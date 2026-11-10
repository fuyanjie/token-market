"""Frozen v1.1 WP1 cells and safe WP2 horizon configuration (no inference)."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json

from .config import deep_merge
from .roster import materialize
from .sellers import Reputation
from .sim import build_backends, prepare, run_single
from .v1_metrics import exposure, intent

AUDIT_RATES = (0.0, 0.01, 0.02, 0.03, 0.05, 0.10, 0.20)
PENALTIES = (0.25, 0.0625, 0.015625)
PIS = (1.0, 0.1, 0.0)
POLICIES = {
    "cascade": "audited_compliance_cascade",
    "pilot": "pilot_v1_compliant",
    "stageroute": "stageroute_v1_compliant",
    "strongest": "single_best_compliant",
    "cheapest": "single_cheapest_compliant",
    "cascade+trust": "audited_compliance_cascade",
}
PROTOCOL_SHA256 = "e9c84494a7031d7023d4861c02a5786a59fbc74541007978a13b9882f209c179"
_PREPARED = {}


@dataclass(frozen=True)
class Cell:
    router: str
    audit: str
    penalty: float
    pi: float

    @property
    def arm(self):
        return "control" if self.router == "cascade+trust" else "factorial"

    @property
    def policy(self):
        return POLICIES[self.router]

    @property
    def cell_id(self):
        return f"{self.router}__{self.audit}__P{self.penalty:g}__pi{self.pi:g}"

    def metadata(self):
        return dict(asdict(self), cell_id=self.cell_id, arm=self.arm, policy=self.policy,
                    trust_feedback=self.arm == "control",
                    penalty_label={0.25: "P", 0.0625: "P/4", 0.015625: "P/16"}[self.penalty],
                    audit_efficacy_evidence_allowed=self.penalty != PENALTIES[-1])


def enumerate_wp1():
    """All frozen cells, with controls explicitly separated, never post-hoc dropped."""
    audits = tuple(f"a{rate:g}" for rate in AUDIT_RATES) + ("risk_adaptive",)
    return [Cell(router, audit, penalty, pi)
            for router in POLICIES
            for audit in audits for penalty in PENALTIES
            for pi in (PIS if router in ("pilot", "stageroute") else (1.0,))]


def scale_horizon(base, n_rounds):
    """Return a copy; budgets scale from the reference multiplier, never cumulatively."""
    if isinstance(n_rounds, bool) or not isinstance(n_rounds, int) or n_rounds < 1:
        raise ValueError("n_rounds must be a positive integer")
    market = base.get("market", {})
    reference = market.get("budget_multiplier_at_480", market.get("budget_multiplier", 1.0))
    n_tasks = 10 * n_rounds
    return deep_merge(base, {"run": {"n_rounds": n_rounds, "n_tasks": n_tasks},
                             "market": {"budget_multiplier_at_480": float(reference),
                                        "budget_multiplier": float(reference) * n_tasks / 480}})


def cell_config(base, cell, seed, n_rounds=48, learner="egreedy"):
    if cell not in enumerate_wp1():
        raise ValueError("cell is outside the frozen WP1 grid")
    if learner not in ("egreedy", "fictitious_play", "exp3"):
        raise ValueError("unsupported protocol learner")
    risk = base.get("market", {}).get("audited", {}).get("risk_adaptive", {})
    block = {"enabled": True, "rate": 0.1 if cell.audit == "risk_adaptive" else float(cell.audit[1:]),
             "audit_rule": "risk_adaptive" if cell.audit == "risk_adaptive" else "fixed",
             "types": ["identity", "length"], "trust_feedback": cell.arm == "control",
             "risk_adaptive": risk}
    cfg = deep_merge(scale_horizon(base, n_rounds), {
        "market": {"policies": [cell.policy], "mechanisms": ["posted_price"], "compliance_filter": True,
                   "audit_v11": block,
                   "audited": {"reputation_rounds": 0, "adaptive_audit": False, "escrow": False},
                   "feedback": {"mode": "immediate" if cell.pi == 1 else "sparse",
                                "delay_L": 0, "reveal_prob": cell.pi}},
        "fraud": {"strategy": "learning", "penalty": cell.penalty, "reputation_rounds": 0,
                  "learning": {"learner": learner}},
    })
    return materialize(cfg, seed)


class MemoryLog:
    def __init__(self):
        self.records = []

    def write(self, record):
        self.records.append(record)


def run_cell(job):
    cell, seed = job["cell"], job["seed"]
    cfg = cell_config(job["base"], cell, seed, job["n_rounds"], job["learner"])
    backend, cache_file = job.get("backend"), job["cache_file"]
    # Same task pool and model/cache preparation across audit cells in each worker.
    key = (backend, cache_file, json.dumps(cfg.get("task_pool", {}), sort_keys=True),
           json.dumps(cfg["models"], sort_keys=True),
           json.dumps(cfg.get("backends", {}), sort_keys=True),
           tuple(sorted((s["claimed_model"], s["actual_model"], s["backend"]) for s in cfg["sellers"])))
    if key not in _PREPARED:
        _PREPARED[key] = prepare(cfg, backend, cache_file, log=lambda *a: None)[:3]
    pool, cache, stats = _PREPARED[key]
    backends = build_backends(cfg, {backend} if backend else {s["backend"] for s in cfg["sellers"]}, cache)
    logger = MemoryLog()
    m = run_single(cfg, "posted_price", cell.policy, seed, backends, Reputation(cfg["models"], stats),
                   logger, pool, backend_override=backend)
    tail_rounds = max(1, cfg["run"]["n_rounds"] // 4)
    q = intent(m, logger.records, cfg["run"]["n_rounds"], tail_trade_rounds=tail_rounds)
    tail_from = cfg["run"]["n_rounds"] - tail_rounds
    counts = {sid: 0 for sid in m["strategic_modes"]}
    for rec in logger.records:
        if rec["status"] == "allowed" and rec["seller_id"] in counts and rec["round"] >= tail_from:
            counts[rec["seller_id"]] += 1
    row = dict(cell.metadata(), seed=seed, **exposure(logger.records), **q,
               q_swap=q["Q_swap"], q_theft=q["Q_theft"], q_downgrade=q["Q_downgrade"],
               accuracy=m["task_accuracy"], cost_per_task=m["mean_cost_per_task_incl_audit"],
               cost=m["total_cost_incl_audit"], audit_cost=m["total_audit_cost"],
               n_audits=m["n_audits"], audit_rate_realised=m["n_audits"] / max(1, m["n_purchases"]),
               fill_rate=m["fill_rate"], n_tasks=cfg["run"]["n_tasks"], n_rounds=cfg["run"]["n_rounds"],
               tail_rounds=tail_rounds, strategic_tail_counts=counts, learner=job["learner"],
               budget_multiplier=cfg["market"]["budget_multiplier"], audit_checks=m["audit_checks"],
               audit_rule=m["audit_rule"],
               config_hash=hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest())
    if job.get("log_dir"):
        path = job["log_dir"] / f"{cell.cell_id}__seed{seed}.jsonl"
        with path.open("x", encoding="utf-8") as fh:
            for rec in logger.records:
                fh.write(json.dumps(rec) + "\n")
    return row


def summarize_cells(rows):
    groups = {}
    for row in rows:
        groups.setdefault(row["cell_id"], []).append(row)
    summaries = []
    for cell_id, runs in groups.items():
        n_tail = sum(r["tail_trade"] for r in runs)
        summary = {k: runs[0][k] for k in Cell(runs[0]["router"], runs[0]["audit"],
                                             runs[0]["penalty"], runs[0]["pi"]).metadata()}
        summary.update(n_runs=len(runs), tail_trade_runs=n_tail, tail_trade_rate=n_tail / len(runs),
                       Q_identifiable=n_tail / len(runs) > 0.5,
                       per_run_strategic_tail_counts=[
                           {"seed": r["seed"], "tail_sales": r["tail_sales"],
                            "by_seller": r["strategic_tail_counts"]} for r in runs])
        for metric in ("E", "E_tok", "Q", "q_swap", "q_theft", "q_downgrade", "accuracy", "cost_per_task"):
            values = [r[metric] for r in runs if r[metric] is not None]
            summary[metric] = sum(values) / len(values) if values else None
        summaries.append(summary)
    return summaries
