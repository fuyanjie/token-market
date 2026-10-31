"""v3 experiments (run_experiments.py):

  C  fraud_audit_threshold : strategic (learning) model-swap seller vs buyer audit rate x penalty
  D  baselines             : PILOT-style / StageRoute-style (with & without compliance filter), v2 policies and
                             OUR audited_compliance_cascade against the strategic seller
  A  cost_curves           : accuracy vs cost (incl. audit cost) for all policies over budget / knob sweeps,
                             accuracy at equal cost, Pareto frontier
  B  long_math             : market on the long GSM8K / MATH-500 subset (normal + tight budget)

All runs reuse the precomputed output cache; nothing here loads a model.
"""
from __future__ import annotations

import copy
import json
import os
import statistics
import time
from typing import Dict, List, Optional, Tuple

from .config import deep_merge, load_config
from .logging_schema import TransactionLogger, read_log, validate_record
from .metrics import aggregate, p95
from .sellers import Reputation
from .sim import REAL_VS_SIM, build_backends, prepare, run_all, run_single  # noqa: F401
from .strategic import analytic_threshold, best_response, make_strategy

class NullLogger:
    """Validates records like TransactionLogger but keeps nothing (large sweeps)."""

    def __init__(self, keep: bool = False):
        self.count, self.keep, self.records = 0, keep, []

    def write(self, rec: Dict) -> None:
        errs = validate_record(rec)
        if errs:
            raise ValueError(f"invalid transaction record: {errs}")
        self.count += 1
        if self.keep:
            self.records.append(dict(rec))


class Context:
    def __init__(self, cfg: Dict, backend_override: Optional[str], cache_path: Optional[str], log):
        self.cfg = cfg
        self.backend_override = backend_override
        self.pool, self.cache, self.stats, _ = prepare(cfg, backend_override, cache_path, None, log)
        self.rep = Reputation(cfg["models"], self.stats)
        sb = {backend_override} if backend_override else {s.get("backend", "mock") for s in cfg["sellers"]}
        self.backends = build_backends(cfg, sb, self.cache)


def run_point(ctx: Context, over: Dict, policy: str, seeds: List[int], logger=None) -> Dict:
    cfg = deep_merge(ctx.cfg, over)
    logger = logger or NullLogger()
    per_seed = []
    for seed in seeds:
        m = run_single(cfg, "posted_price", policy, seed, ctx.backends, ctx.rep, logger, ctx.pool,
                       None, ctx.backend_override)
        m.pop("gateway", None)
        per_seed.append(m)
    return {"policy": policy, "over": over, "per_seed": per_seed, "aggregate": aggregate(per_seed)}


def _ms(xs):
    xs = list(xs)
    return (statistics.fmean(xs) if xs else 0.0, statistics.stdev(xs) if len(xs) > 1 else 0.0)


def _pm(a: Dict, k: str, fmt="{:.3f}") -> str:
    return f"{fmt.format(a[k]['mean'])} ± {fmt.format(a[k]['std'])}"


def fraud_seller_id(cfg: Dict) -> str:
    return next(s["id"] for s in cfg["sellers"] if s["claimed_model"] != s["actual_model"])


# --------------------------------------------------------------------------- C
def experiment_C(ctx: Context, seeds: List[int], log_dir: str, log=print) -> Dict:
    ec = ctx.cfg["experiments"]["C"]
    sid = fraud_seller_id(ctx.cfg)
    scfg = next(s for s in ctx.cfg["sellers"] if s["id"] == sid)
    f = ctx.cfg["fraud"]
    d = float(f["detect_prob"])
    saving = make_strategy(scfg, ctx.cfg, 0.0, ctx.rep).cost_saving
    thr = float(ec.get("q_threshold", 0.1))
    rows, table = [], {}
    os.makedirs(log_dir, exist_ok=True)
    with TransactionLogger(os.path.join(log_dir, "transactions_C.jsonl"), mode="w") as lg:
        for P in ec["penalties"]:
            for a in ec["audit_rates"]:
                over = {"fraud": {"penalty": P}, "run": dict(ec.get("run", {})),
                        "market": {"audit": {"rate": a}, "budget_multiplier": ec.get("budget_multiplier", 1.0)}}
                r = run_point(ctx, over, ec["policy"], seeds, lg)
                ps = r["per_seed"]
                q = _ms(m["learned_swap_q"][sid] for m in ps)
                served = _ms(m["seller_swap_rate"][sid] for m in ps)
                # empirical realised per-purchase saving of swapped vs honest (pre-penalty) is reported by the
                # seller's own estimates: mean profit swapped - mean profit honest (+ penalty paid per swap)
                row = {"penalty": P, "audit_rate": a, "learned_q_mean": q[0], "learned_q_std": q[1],
                       "served_swap_rate_mean": served[0], "served_swap_rate_std": served[1],
                       "analytic_q": best_response(saving, a, d, P), "analytic_gain": saving - a * d * P,
                       "swaps_detected": _ms(m["swaps_detected"] for m in ps)[0],
                       "n_audits": _ms(m["n_audits"] for m in ps)[0],
                       "stake_slashed": _ms(m["total_stake_slashed"] for m in ps)[0],
                       "seller_profit": _ms(m["seller_profit"][sid] for m in ps)[0],
                       "fraud_seller_purchases": _ms(m["seller_purchases"][sid] for m in ps)[0],
                       "task_accuracy": _ms(m["task_accuracy"] for m in ps)[0],
                       "audit_cost": _ms(m["total_audit_cost"] for m in ps)[0],
                       "q_history_seed0": ps[0]["swap_q_history"][sid]}
                rows.append(row)
                log(f"[C] P={P} a={a}: learned q={q[0]:.3f}±{q[1]:.3f} (analytic q*={row['analytic_q']:.0f})")
    for P in ec["penalties"]:
        rs = sorted((r for r in rows if r["penalty"] == P), key=lambda r: r["audit_rate"])
        emp = None
        for i, r in enumerate(rs):
            if all(x["learned_q_mean"] < thr for x in rs[i:]):
                emp = r["audit_rate"]
                break
        table[str(P)] = {"penalty": P, "analytic_threshold": analytic_threshold(saving, d, P),
                         "empirical_threshold": emp,
                         "grid_bracket_analytic": next((r["audit_rate"] for r in rs
                                                        if r["audit_rate"] > analytic_threshold(saving, d, P)), None)}
    return {"cost_saving_per_purchase": saving, "detect_prob": d, "cost_gap_per_1k": f["cost_gap_per_1k"],
            "claimed_tokens_mean": ctx.rep.tokens_mean(scfg["claimed_model"]), "q_threshold": thr,
            "policy": ec["policy"], "seeds": seeds, "rows": rows, "thresholds": table,
            "n_tasks": ec.get("run", {}).get("n_tasks", ctx.cfg["run"]["n_tasks"]),
            "n_rounds": ec.get("run", {}).get("n_rounds", ctx.cfg["run"]["n_rounds"]),
            "learning": f.get("learning", {})}


def render_C(res: Dict) -> str:
    L = ["# C — strategic model-swap seller vs buyer audits (fraud / audit threshold)", "",
         f"Buyer policy `{res['policy']}` (routes on CLAIMED quality, so it sends most demand to the swap seller); "
         f"{res['n_tasks']} tasks/run in {res['n_rounds']} rounds (= seller epochs); seeds={res['seeds']}. "
         f"The seller (seller_sg, claims Qwen2.5-1.5B, can serve 0.5B) LEARNS its swap rate q per epoch with "
         f"Hedge over q ∈ {{0, 0.1, …, 1}} on its own realised profit (incl. stake actually slashed), "
         f"ε-exploration {res['learning'].get('epsilon', 0.1)}; learned q = mean q played over the last half of "
         "the epochs (mean ± std over seeds).", "",
         f"Per-purchase cost saving of swapping = cost_gap {res['cost_gap_per_1k']}/1K × claimed-model mean "
         f"tokens {res['claimed_tokens_mean']:.1f} / 1000 = **{res['cost_saving_per_purchase']:.5f}**; "
         f"detect_prob d = {res['detect_prob']}; audits are SIMULATED identity checks.", "",
         "## Threshold: analytic a* = saving / (d·P) vs empirical", "",
         f"Empirical threshold = smallest audit rate in the grid from which on the learned q stays < "
         f"{res['q_threshold']}.", "",
         "| penalty P | analytic a* | first grid a > a* | empirical a (learned q < thr) | same grid point? |",
         "|---|---|---|---|---|"]
    for t in res["thresholds"].values():
        a_star = t["analytic_threshold"]
        ok = t["empirical_threshold"] == t["grid_bracket_analytic"]
        L.append(f"| {t['penalty']} | {a_star:.4f} | {t['grid_bracket_analytic'] if t['grid_bracket_analytic'] is not None else '> grid'} "
                 f"| {t['empirical_threshold'] if t['empirical_threshold'] is not None else 'not reached'} "
                 f"| {'yes' if ok else 'no (learning lags near the threshold, where the gain is ~0)'} |")
    L += ["", "## Sweep", "",
          "| P | audit rate a | analytic gain = saving − a·d·P | analytic q* | learned q | served swap rate "
          "| swaps detected | stake slashed | seller_sg profit | sg purchases | buyer audit cost | task accuracy |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["rows"]:
        L.append(f"| {r['penalty']} | {r['audit_rate']} | {r['analytic_gain']:+.5f} | {r['analytic_q']:.0f} "
                 f"| {r['learned_q_mean']:.3f} ± {r['learned_q_std']:.3f} | {r['served_swap_rate_mean']:.3f} "
                 f"| {r['swaps_detected']:.1f} | {r['stake_slashed']:.2f} | {r['seller_profit']:+.3f} "
                 f"| {r['fraud_seller_purchases']:.0f} | {r['audit_cost']:.3f} | {r['task_accuracy']:.3f} |")
    L += ["", "Notes: the learning seller never sees a, d or P — only its realised profits. Because of ε-exploration "
          "the q actually played never drops to exactly 0 (floor ≈ ε/2). Realised savings differ slightly from the "
          "analytic one because swapped (0.5B) and honest (1.5B) answers have different real token counts (revenue "
          "is per token). Values per seed: results/fraud_audit_threshold.json.", ""]
    return "\n".join(L)


# --------------------------------------------------------------------------- A
def interp_at(points: List[Tuple[float, float]], c: float) -> Optional[float]:
    """Best accuracy attainable at cost <= c along a policy's curve, linearly interpolated between the points of
    its monotone (Pareto) envelope; None if c is below the cheapest point."""
    env = pareto(points)
    if not env or c < env[0][0] - 1e-12:
        return None
    for (c0, a0), (c1, a1) in zip(env, env[1:]):
        if c0 <= c <= c1:
            return a0 + (a1 - a0) * (c - c0) / (c1 - c0) if c1 > c0 else max(a0, a1)
    return env[-1][1]


def pareto(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Non-dominated (cost ascending, accuracy strictly increasing) subset."""
    out = []
    for c, a in sorted(points, key=lambda p: (p[0], -p[1])):
        if not out or a > out[-1][1] + 1e-12:
            out.append((c, a))
    return out


def experiment_A(ctx: Context, seeds: List[int], log=print) -> Dict:
    ea = ctx.cfg["experiments"]["A"]
    pts = []

    def add(family, policy, over, knob):
        r = run_point(ctx, over, policy, seeds)
        a = r["aggregate"]
        pts.append({"family": family, "policy": policy, "knob": knob,
                    "cost_per_task": a["mean_cost_per_task_incl_audit"]["mean"],
                    "cost_per_task_std": a["mean_cost_per_task_incl_audit"]["std"],
                    "accuracy": a["task_accuracy"]["mean"], "accuracy_std": a["task_accuracy"]["std"],
                    "budget_violations": a["budget_violations"]["mean"],
                    "compliance_violations": a["compliance_violations"]["mean"],
                    "fraud_seller_share": a["fraud_seller_share"]["mean"]})

    for pol in ea["budget_policies"]:
        for bm in ea["budget_multipliers"]:
            add(pol, pol, {"market": {"budget_multiplier": bm}}, f"budget×{bm}")
    kb = ea["knob_budget_multiplier"]
    for thr in ea["cascade_thresholds"]:
        add("cascade_compliant (threshold)", "cascade_compliant",
            {"market": {"budget_multiplier": kb, "cascade": {"confidence_threshold": thr}}}, f"thr={thr}")
    for k in ea["vote_k"]:
        add("vote_k_compliant (k)", "vote_k_compliant", {"market": {"budget_multiplier": kb, "vote": {"k": k}}},
            f"k={k}")
        for bm in ea["budget_multipliers"]:
            add(f"vote_k_compliant k={k}", "vote_k_compliant",
                {"market": {"budget_multiplier": bm, "vote": {"k": k}}}, f"budget×{bm}")
    for ar in ea["d3_audit_rates"]:
        add("audited_compliance_cascade (audit rate)", "audited_compliance_cascade",
            {"market": {"budget_multiplier": kb, "audited": {"audit_rate": ar}}}, f"audit={ar}")
    log(f"[A] {len(pts)} curve points x {len(seeds)} seeds")

    fams = sorted({p["family"] for p in pts})
    allc = sorted(p["cost_per_task"] for p in pts)
    levels = sorted({round(allc[int(q * (len(allc) - 1))], 4) for q in (0.2, 0.4, 0.6, 0.8)})
    eq = {f: {str(c): interp_at([(p["cost_per_task"], p["accuracy"]) for p in pts if p["family"] == f], c)
              for c in levels} for f in fams}
    front = pareto([(p["cost_per_task"], p["accuracy"]) for p in pts])
    front_pts = [next(p for p in pts if p["cost_per_task"] == c and p["accuracy"] == a) for c, a in front]
    return {"seeds": seeds, "points": pts, "cost_levels": levels, "accuracy_at_equal_cost": eq,
            "pareto_frontier": [{k: p[k] for k in ("family", "knob", "cost_per_task", "accuracy")} for p in front_pts]}


def render_A(res: Dict) -> str:
    L = ["# A — accuracy vs cost curves", "",
         "Market with the STRATEGIC (learning) swap seller; cost = mean cost per task INCLUDING audit cost "
         f"(mean ± std over seeds {res['seeds']}). Each family is one policy swept over its knob or over the "
         "per-buyer budget multiplier (StageRoute's per-query budget b = B/T moves with the multiplier).", "",
         "## Accuracy at equal cost (best accuracy at cost/task ≤ c on each family's interpolated Pareto envelope;"
         " – = family cannot reach that cost level)", "",
         "| family | " + " | ".join(f"c={c:.4f}" for c in res["cost_levels"]) + " |",
         "|---|" + "---|" * len(res["cost_levels"])]
    for f, d in res["accuracy_at_equal_cost"].items():
        L.append(f"| {f} | " + " | ".join("–" if d[str(c)] is None else f"{d[str(c)]:.3f}"
                                          for c in res["cost_levels"]) + " |")
    L += ["", "## Pareto frontier (all points)", "", "| family | knob | cost/task | accuracy |", "|---|---|---|---|"]
    for p in res["pareto_frontier"]:
        L.append(f"| {p['family']} | {p['knob']} | {p['cost_per_task']:.4f} | {p['accuracy']:.3f} |")
    L += ["", "## All points", "", "| family | knob | cost/task (incl. audit) | accuracy | budget viol. | compliance viol. "
          "| fraud-seller share |", "|---|---|---|---|---|---|---|"]
    for p in res["points"]:
        L.append(f"| {p['family']} | {p['knob']} | {p['cost_per_task']:.4f} ± {p['cost_per_task_std']:.4f} "
                 f"| {p['accuracy']:.3f} ± {p['accuracy_std']:.3f} | {p['budget_violations']:.1f} "
                 f"| {p['compliance_violations']:.1f} | {p['fraud_seller_share']:.3f} |")
    L.append("")
    return "\n".join(L)


def plot_A(res: Dict, path: str) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    fig, ax = plt.subplots(figsize=(10, 6.5))
    cmap = plt.get_cmap("tab20")
    for i, f in enumerate(sorted({p["family"] for p in res["points"]})):
        ps = sorted((p for p in res["points"] if p["family"] == f), key=lambda p: p["cost_per_task"])
        ax.errorbar([p["cost_per_task"] for p in ps], [p["accuracy"] for p in ps],
                    yerr=[p["accuracy_std"] for p in ps], marker="osD^v<>ph*"[i % 10], ms=4, lw=1.2, capsize=2,
                    color=cmap(i % 20), ls="-" if i < 10 else "--", label=f)
    fr = res["pareto_frontier"]
    ax.plot([p["cost_per_task"] for p in fr], [p["accuracy"] for p in fr], "k--", lw=1.5, label="Pareto frontier")
    ax.set_xlabel("mean cost per task incl. audit cost (USD, synthetic)")
    ax.set_ylabel("task accuracy")
    ax.set_title("token-market v3: accuracy vs cost (strategic swap seller)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return True


def plot_C(res: Dict, path: str) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for P, t in res["thresholds"].items():
        rs = sorted((r for r in res["rows"] if str(r["penalty"]) == P), key=lambda r: r["audit_rate"])
        line, = ax.plot([r["audit_rate"] for r in rs], [r["learned_q_mean"] for r in rs], marker="o", label=f"P={P}")
        if t["analytic_threshold"] <= max(r["audit_rate"] for r in rs):
            ax.axvline(t["analytic_threshold"], color=line.get_color(), ls=":", lw=1)
    ax.axhline(res["q_threshold"], color="grey", ls="--", lw=1)
    ax.set_xlabel("buyer audit rate a")
    ax.set_ylabel("learned swap rate q")
    ax.set_title("learned swap rate vs audit rate (dotted: analytic a* = saving/(d·P))")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return True


# --------------------------------------------------------------------------- D
def experiment_D(ctx: Context, seeds: List[int], log_dir: str, curves: Optional[Dict], log=print) -> Dict:
    ed = ctx.cfg["experiments"]["D"]
    sid = fraud_seller_id(ctx.cfg)
    rows = []
    os.makedirs(log_dir, exist_ok=True)
    with TransactionLogger(os.path.join(log_dir, "transactions_D.jsonl"), mode="w") as lg:
        for pol in ed["policies"]:
            r = run_point(ctx, {"market": {"budget_multiplier": ed.get("budget_multiplier", 1.0)}}, pol, seeds, lg)
            a, ps = r["aggregate"], r["per_seed"]
            rows.append({"policy": pol, "aggregate": {k: a[k] for k in (
                "task_accuracy", "total_cost", "total_audit_cost", "total_cost_incl_audit",
                "mean_cost_per_task_incl_audit", "budget_violations", "compliance_violations",
                "fraud_seller_share", "n_audits", "swaps_detected", "swaps_served", "total_stake_slashed",
                "total_buyer_surplus", "total_cost_gap", "budget_exhausted_tasks")},
                "learned_q": _ms(m["learned_swap_q"][sid] for m in ps),
                "sg_swap_rate": _ms(m["seller_swap_rate"][sid] for m in ps)})
            log(f"[D] {pol}: acc={a['task_accuracy']['mean']:.3f} cost={a['total_cost_incl_audit']['mean']:.3f}")
    eq = None
    if curves:
        eq = {"cost_levels": curves["cost_levels"], "by_family": curves["accuracy_at_equal_cost"]}
    return {"seeds": seeds, "rows": rows, "equal_cost": eq, "fraud_seller": sid,
            "penalty": ctx.cfg["fraud"]["penalty"], "detect_prob": ctx.cfg["fraud"]["detect_prob"],
            "d3_audit_rate": ctx.cfg["market"]["audited"]["audit_rate"],
            "audit_cost": ctx.cfg["market"]["audit"]["cost"]}


LABEL = {
    "pilot": "PILOT-style (our simplified reimpl. of Panda et al. 2025), no compliance filter",
    "pilot_compliant": "PILOT-style + compliance filter",
    "stageroute": "StageRoute-style (our simplified reimpl. of Li & Li 2025), no compliance filter",
    "stageroute_compliant": "StageRoute-style + compliance filter",
    "audited_compliance_cascade": "**D3 audited_compliance_cascade (ours)**",
}


def render_D(res: Dict) -> str:
    L = ["# D — baselines vs the STRATEGIC model-swap seller", "",
         f"All policies face the same learning swap seller ({res['fraud_seller']}; penalty P={res['penalty']}, "
         f"d={res['detect_prob']}). Only D3 audits (rate {res['d3_audit_rate']}, audit cost {res['audit_cost']} "
         f"per audit charged to the buyer budget), so for every other policy the seller faces a = 0. "
         f"Mean ± std over seeds {res['seeds']}.", "",
         "| policy | task accuracy | total cost incl. audit | of which audit | cost/task | budget violations "
         "| compliance violations | fraud-seller share (swapped purchases) | sg learned q | swaps detected / served "
         "| stake slashed | buyer surplus |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["rows"]:
        a = r["aggregate"]
        L.append(f"| {LABEL.get(r['policy'], r['policy'])} | {_pm(a, 'task_accuracy')} "
                 f"| {_pm(a, 'total_cost_incl_audit')} | {a['total_audit_cost']['mean']:.3f} "
                 f"| {_pm(a, 'mean_cost_per_task_incl_audit', '{:.4f}')} | {_pm(a, 'budget_violations', '{:.1f}')} "
                 f"| {_pm(a, 'compliance_violations', '{:.1f}')} | {_pm(a, 'fraud_seller_share')} "
                 f"| {r['learned_q'][0]:.3f} ± {r['learned_q'][1]:.3f} "
                 f"| {a['swaps_detected']['mean']:.1f} / {a['swaps_served']['mean']:.1f} "
                 f"| {a['total_stake_slashed']['mean']:.2f} | {_pm(a, 'total_buyer_surplus')} |")
    if res.get("equal_cost"):
        e = res["equal_cost"]
        L += ["", "## Accuracy at equal cost (from the A curves)", "",
              "| family | " + " | ".join(f"c={c:.4f}" for c in e["cost_levels"]) + " |",
              "|---|" + "---|" * len(e["cost_levels"])]
        for f, d in e["by_family"].items():
            L.append(f"| {f} | " + " | ".join("–" if d[str(c)] is None else f"{d[str(c)]:.3f}"
                                              for c in e["cost_levels"]) + " |")
    L += ["", "Differences from the papers (all baselines are OUR SIMPLIFIED REIMPLEMENTATIONS):",
          "- PILOT: hand-made task features instead of query embeddings; the preference prior is the CLAIMED model's "
          "public reputation (so a swap seller inherits a good prior); reward = observed correctness; ON-MCKP ZCL "
          "threshold with budget bins + spillover and the B_left/Q_left fallback; one LinUCB shared by all buyers, "
          "budgets per buyer.",
          "- StageRoute: only the per-query routing LP with UCB rewards / LCB costs and throughput caps "
          "(alpha = capacity share); the stage-wise deployment MIP is skipped (3 fixed sellers); LP solved exactly by "
          "vertex enumeration.",
          "- Neither baseline accounts for audit cost, models a strategic seller, or filters on compliance (the "
          "`_compliant` variants add the hard compliance filter); non-filtered variants run through the audit_only "
          "gateway so their breaches are counted.",
          "- D3 routes on audit-adjusted quality: once an audit reveals the served model, the seller's quality is "
          "(1 − q̂)·rep(claimed) + q̂·rep(revealed), q̂ = detected / (audits·d) (smoothed).", ""]
    return "\n".join(L)


# --------------------------------------------------------------------------- B
def _overrun_stats(recs: List[Dict]) -> Dict:
    served = [r for r in recs if r["status"] == "allowed"]
    rel = [r["actual_cost"] / r["expected_cost"] - 1 for r in served if r["expected_cost"] > 0]
    return {"purchases": len(served), "overrun_purchases": sum(1 for r in served if r["cost_overrun"] > 1e-12),
            "rel_overrun_mean": _ms(rel)[0], "rel_overrun_p95": p95(rel), "rel_overrun_max": max(rel, default=0.0),
            "budget_violations": sum(1 for r in served if r["budget_overrun"]),
            "max_budget_overshoot": max((-r["budget_remaining"] for r in served if r["budget_overrun"]), default=0.0)}


def experiment_B(base_cfg_path: str, seeds: List[int], tight_mult: float, backend_override: Optional[str],
                 cache_path: Optional[str], log=print) -> Optional[Dict]:
    cfg = load_config(base_cfg_path)
    from .tasks import build_task_pool
    from .precompute import local_models, model_stats, local_cfg
    from .cache import OutputCache
    if not backend_override:
        cache = OutputCache(cache_path or cfg["run"].get("cache_file", "cache/llm_outputs.jsonl"))
        pool = build_task_pool(cfg)
        lc = local_cfg(cfg)
        ok = all(model_stats(cache, pool, m, int(lc["max_new_tokens"]), int(lc["long_max_new_tokens"]))
                 for m in local_models(cfg))
        if not ok:
            log("[B] long-math cache incomplete: run `python run_sim.py --config configs/long_math.yaml "
                "--precompute-only` first; skipping B")
            return None
    out = {"seeds": seeds, "variants": {}}
    base_mult = float(cfg["market"].get("budget_multiplier", 1.0))
    for name, mult in (("normal", base_mult), ("tight", tight_mult)):
        c = deep_merge(cfg, {"market": {"budget_multiplier": mult}})
        rd = cfg["run"]["results_dir"] + ("" if name == "normal" else "_tight")
        s = run_all(c, seeds=seeds, backend_name=backend_override, results_dir=rd, cache_path=cache_path,
                    log=lambda *a: None)
        recs = read_log(s["log_file"])
        pols = {}
        for key, combo in s["combos"].items():
            if combo["mechanism"] != "posted_price":
                continue
            a = combo["aggregate"]
            pols[combo["policy"]] = {
                "task_accuracy": a["task_accuracy"], "total_cost": a["total_cost"],
                "total_expected_cost": a["total_expected_cost"], "total_cost_gap": a["total_cost_gap"],
                "cost_gap_rel": a["cost_gap_rel"], "budget_violations": a["budget_violations"],
                "buyers_over_budget": a["buyers_over_budget"], "budget_exhausted_tasks": a["budget_exhausted_tasks"],
                "overruns": _overrun_stats([r for r in recs if r["policy"] == combo["policy"]
                                            and r["mechanism"] == "posted_price"])}
        out["variants"][name] = {"budget_multiplier": mult, "results_dir": rd, "policies": pols}
        out["model_stats"] = s["model_stats"]
        log(f"[B] {name} (budget×{mult}): wrote {rd}/summary.md")
    return out


def render_B(res: Dict) -> str:
    L = ["# B — long reasoning tasks (GSM8K-hard + MATH-500, real Qwen outputs)", ""]
    ms = res["model_stats"]
    L += ["## Measured model accuracy on the long subset", "",
          "| model | n | acc overall | acc GSM8K-hard (d4) | acc MATH-500 L3+ (d5) | tokens mean ± std | p95 | max "
          "| truncation rate (= hit max_new_tokens) | explicit 'Answer:' rate |", "|---|---|---|---|---|---|---|---|---|---|"]
    for m, s in ms.items():
        bd = s["by_difficulty"]
        g = lambda d: f"{bd[d]['accuracy']:.3f} (n={bd[d]['n']})" if d in bd else "–"  # noqa: E731
        L.append(f"| {m} | {s['n']} | {s['accuracy']:.3f} | {g(4)} | {g(5)} | {s['tokens_mean']:.1f} ± "
                 f"{s['tokens_std']:.1f} | {s['tokens_p95']:.0f} | {s['tokens_max']} | {s['truncated_rate']:.3f} "
                 f"| {s['explicit_answer_rate']:.3f} |")
    mnt = next(iter(ms.values()))["long_max_new_tokens"] if ms else "?"
    L += ["", f"Long tasks: max_new_tokens={mnt}, bf16 on CPU (AMX), greedy, prompt 'solve step by step … "
          "Answer: <integer>'.", ""]
    for name, v in res["variants"].items():
        L += [f"## Market: {name} budget (budget multiplier ×{v['budget_multiplier']}; full summary: "
              f"`{v['results_dir']}/summary.md`)", "",
              "| policy | task accuracy | Σ expected cost | Σ actual cost | gap (rel) | purchases with overrun "
              "| rel. overrun mean / p95 / max | budget violations (purchases) | buyers over budget | max overshoot "
              "| budget-exhausted tasks |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for p, a in v["policies"].items():
            o = a["overruns"]
            L.append(f"| {p} | {_pm(a, 'task_accuracy')} | {a['total_expected_cost']['mean']:.3f} "
                     f"| {a['total_cost']['mean']:.3f} | {a['total_cost_gap']['mean']:+.3f} "
                     f"({a['cost_gap_rel']['mean']:+.1%}) | {o['overrun_purchases']}/{o['purchases']} "
                     f"| {o['rel_overrun_mean']:+.1%} / {o['rel_overrun_p95']:+.1%} / {o['rel_overrun_max']:+.1%} "
                     f"| {o['budget_violations']} | {a['buyers_over_budget']['mean']:.1f} "
                     f"| {o['max_budget_overshoot']:.4f} | {a['budget_exhausted_tasks']['mean']:.1f} |")
        L.append("")
    L += ["Overrun counts are summed over seeds; other columns are means over seeds. A purchase is only made if its "
          "EXPECTED cost (claimed model's mean tokens) fits the remaining budget, so a budget violation needs a buyer "
          "whose remaining budget is below the purchase's ACTUAL cost but above its expected cost — at most a few "
          "purchases per buyer at the moment its budget runs out.", ""]
    return "\n".join(L)
