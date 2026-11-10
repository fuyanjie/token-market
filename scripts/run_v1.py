#!/usr/bin/env python3
"""v1.0 runner (docs/PROTOCOL_v1.0.md §1-§3, §6): methods x π x seeds -> per-seed CSV with E, Q, J, cost, quality.

  /workspace/tmvenv/bin/python scripts/run_v1.py --config configs/v1.0/scale.yaml \
      --seeds 0-19 --methods pilot stageroute cheapest_fixed ... --out results/v1.0/main --jobs 8

--pi-grid / --methods default to the config's `v1:` block. π sets the outcome-label feedback regime of the bandit
routers (mode sparse, L=0, reveal prob π; π=1 -> immediate), exactly as the v0.1 T2 task does.
Outputs: <out>/per_seed.csv (one row per method x π x seed), <out>/tail_trade_rate.csv (per method x π),
<out>/summary.md (plain means, no inference - the
Experiment team does bootstrap / Holm), <out>/run_meta.json; with --log-dir also the raw transaction JSONL per run
(input for tokenmarket.t4_export / scripts/run_t4_eval.py).
Writes only under results/v1.0/ or results/_smoke/ inside the repo (or outside results/ entirely, e.g. /tmp).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
from multiprocessing import Pool
from typing import Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket.config import deep_merge, load_config  # noqa: E402
from tokenmarket.registry import DEFAULT_MAIN_TABLE, resolve  # noqa: E402
from tokenmarket.roster import materialize, roster_seed  # noqa: E402
from tokenmarket.sellers import Reputation  # noqa: E402
from tokenmarket.sim import build_backends, prepare, run_single  # noqa: E402
from tokenmarket.v1_metrics import exposure, intent  # noqa: E402

COLUMNS = ["method", "label", "policy", "pi", "seed", "E", "E_tok", "fraud_share",
           "fraud_share_swap", "fraud_share_theft", "fraud_share_downgrade",
           "Q", "Q_swap", "Q_theft", "Q_downgrade", "tail_trade", "tail_trade_sellers", "tail_sales", "n_strategic",
           "Q_present_rounds", "delisted_rounds_tail", "q_delisted_mean",
           "J", "quality", "cost", "cost_per_task", "audit_cost", "n_audits", "audit_rate_realised", "violation_rate",
           "fill_rate", "n_served", "seller_learner", "audit_rule", "compliance_filter", "roster_seed",
           "config_hash"]
_PREP: Dict = {}


class _MemLog:
    def __init__(self):
        self.records = []

    def write(self, r):
        self.records.append(r)


def parse_seeds(xs: List[str]) -> List[int]:
    out = []
    for x in xs:
        if "-" in x:
            a, b = x.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(x))
    return out


def config_hash(cfg: Dict) -> str:
    return hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:16]


def point_config(base: Dict, method: str, pi: float, seed: int, learner=None, filter_off=False,
                 resample=False) -> Dict:
    cfg = deep_merge(base, resolve(method).over)
    over = {"market": {"feedback": {"mode": "sparse" if pi < 1.0 else "immediate", "delay_L": 0,
                                    "reveal_prob": float(pi)}}}
    if learner:
        over["fraud"] = {"learning": {"learner": learner}}
    if filter_off:
        over["market"]["compliance_filter"] = False
    if resample and "roster" in cfg:
        over["roster"] = {"resample_per_seed": True}
    cfg = deep_merge(cfg, over)
    return materialize(cfg, seed)


def _prepared(cfg: Dict, backend: str, cache_file: str):
    key = (backend, cache_file, json.dumps(cfg.get("task_pool", {}), sort_keys=True),
           json.dumps(sorted({s["claimed_model"] for s in cfg["sellers"]} | {s["actual_model"] for s in cfg["sellers"]})))
    if key not in _PREP:
        pool, cache, stats, _ = prepare(cfg, backend, cache_file, None, lambda *a: None)
        _PREP[key] = (pool, cache, stats)
    return _PREP[key]


def run_point(job: Dict) -> Dict:
    cfg = point_config(job["base"], job["method"], job["pi"], job["seed"], job.get("learner"),
                       job.get("filter_off", False), job.get("resample", False))
    backend = job.get("backend")
    pool, cache, stats = _prepared(cfg, backend, job["cache_file"])
    sb = {backend} if backend else {s.get("backend", "mock") for s in cfg["sellers"]}
    backends = build_backends(cfg, sb, cache)
    rep = Reputation(cfg["models"], stats)
    meth = resolve(job["method"])
    lg = _MemLog()
    m = run_single(cfg, "posted_price", meth.policy, job["seed"], backends, rep, lg, pool, None, backend)
    m.pop("gateway", None)
    recs = lg.records
    n_tasks = int(m["n_tasks"]) or 1
    row = {"method": meth.name, "label": meth.label, "policy": meth.policy, "pi": float(job["pi"]),
           "seed": int(job["seed"]), **exposure(recs), **intent(m, recs, int(cfg["run"]["n_rounds"])),
           "E_tok": m["E_tok"], "J": m["joint_objective"], "quality": m["task_accuracy"],
           "cost": m["total_cost_incl_audit"],
           "cost_per_task": m["mean_cost_per_task_incl_audit"], "audit_cost": m["total_audit_cost"],
           "n_audits": m["n_audits"], "audit_rate_realised": m["n_audits"] / max(1, m["n_purchases"]),
           "violation_rate": m["compliance_violation_rate"], "fill_rate": m["fill_rate"],
           "seller_learner": cfg["fraud"].get("learning", {}).get("learner", "egreedy"),
           "audit_rule": m.get("audit_rule"), "compliance_filter": m.get("compliance_filter"),
           "roster_seed": roster_seed(cfg["roster"], job["seed"]) if cfg.get("roster") else None,
           "config_hash": config_hash(cfg)}
    if job.get("log_dir"):
        path = os.path.join(job["log_dir"], f"{meth.name}__pi{job['pi']:g}__seed{job['seed']}.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for r in recs:
                fh.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    row["_n_tasks"] = n_tasks
    return row


def check_out(path: str) -> None:
    ap = os.path.abspath(path)
    res = os.path.join(ROOT, "results") + os.sep
    if ap.startswith(res) and not (ap.startswith(os.path.join(ROOT, "results", "v1.0") + os.sep)
                                   or ap.startswith(os.path.join(ROOT, "results", "_smoke") + os.sep)):
        raise SystemExit(f"refusing to write {path}: only results/v1.0/ or results/_smoke/ inside results/")


def _fmt(v):
    return "" if v is None else (f"{v:.6g}" if isinstance(v, float) else str(v))


def tail_trade_rate(rows: List[Dict]) -> float:
    """口径补正 2: fraction of runs with >=1 sale to a strategic seller in the Q tail window (last 12 of 48 rounds)."""
    return sum(1 for r in rows if r["tail_trade"]) / len(rows) if rows else 0.0


def tail_trade_rates(rows: List[Dict]) -> List[Dict]:
    groups: Dict = {}
    for r in rows:
        groups.setdefault((r["method"], r["pi"]), []).append(r)
    return [{"method": m, "pi": pi, "n_runs": len(rs), "tail_trade_runs": sum(1 for r in rs if r["tail_trade"]),
             "tail_trade_rate": tail_trade_rate(rs)} for (m, pi), rs in sorted(groups.items())]


def write_summary(rows: List[Dict], path: str) -> None:
    keys = ["E", "E_tok", "Q", "Q_swap", "Q_theft", "Q_downgrade", "J", "quality", "cost"]
    groups: Dict = {}
    for r in rows:
        groups.setdefault((r["method"], r["pi"]), []).append(r)
    L = ["# v1.0 run summary (plain means over seeds; inference is done by Experiment)", "",
         "E = fraud_share (per purchase), E_tok = billed-token share; Q = unweighted mean of q over seller-present "
         "tail rounds, simple mean of modes; tail_trade_rate = fraction of runs with >=1 sale to a strategic seller "
         "in the last 12 rounds (Q not identifiable / hollow point when low).", "",
         "| method | π | n | " + " | ".join(keys) + " | tail_trade_rate |", "|---|---|---|" + "---|" * (len(keys) + 1)]
    for (meth, pi), rs in sorted(groups.items(), key=lambda kv: (kv[0][0], -kv[0][1])):
        cells = []
        for k in keys:
            v = [r[k] for r in rs if r.get(k) is not None]
            cells.append(f"{sum(v) / len(v):.4f}" if v else "–")
        L.append(f"| {meth} | {pi:g} | {len(rs)} | " + " | ".join(cells)
                 + f" | {tail_trade_rate(rs):.2f} ({sum(1 for r in rs if r['tail_trade'])}/{len(rs)}) |")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=os.path.join(ROOT, "configs", "v1.0", "scale.yaml"))
    ap.add_argument("--seeds", nargs="+", default=None, help="e.g. 0-19 or 0 1 2 (default: config run.seeds)")
    ap.add_argument("--pi-grid", nargs="+", type=float, default=None)
    ap.add_argument("--methods", nargs="+", default=None)
    ap.add_argument("--out", required=True, help="output directory (results/v1.0/... or results/_smoke/...)")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--backend-override", default=None, help="e.g. mock (smoke / CI without the LLM cache)")
    ap.add_argument("--cache-file", default=os.path.join(ROOT, "cache", "llm_outputs.jsonl"))
    ap.add_argument("--n-tasks", type=int, default=None, help="override run.n_tasks (smoke only)")
    ap.add_argument("--n-rounds", type=int, default=None, help="override run.n_rounds (smoke only)")
    ap.add_argument("--learner", default=None, choices=["egreedy", "hedge", "exp3", "fictitious_play"],
                    help="seller learning rule (Q robustness check, protocol §1)")
    ap.add_argument("--no-compliance-filter", action="store_true", help="A2 control (protocol §6)")
    ap.add_argument("--resample-roster", action="store_true", help="redraw the roster per seed (T4)")
    ap.add_argument("--log-dir", default=None, help="also write raw transaction JSONL per run (T4 input)")
    args = ap.parse_args(argv)

    check_out(os.path.join(args.out, "x"))
    if args.log_dir:
        check_out(os.path.join(args.log_dir, "x"))
        os.makedirs(args.log_dir, exist_ok=True)
    base = load_config(args.config)
    if args.n_tasks:
        base["run"]["n_tasks"] = int(args.n_tasks)
    if args.n_rounds:
        base["run"]["n_rounds"] = int(args.n_rounds)
    v1 = base.get("v1", {})
    seeds = parse_seeds(args.seeds) if args.seeds else list(base["run"]["seeds"])
    pis = args.pi_grid or list(v1.get("pi_grid", [1.0]))
    methods = args.methods or list(v1.get("methods", DEFAULT_MAIN_TABLE))
    for mth in methods:
        resolve(mth)
    os.makedirs(args.out, exist_ok=True)
    jobs = [{"base": base, "method": mth, "pi": float(pi), "seed": int(s), "learner": args.learner,
             "filter_off": args.no_compliance_filter, "resample": args.resample_roster,
             "backend": args.backend_override, "cache_file": args.cache_file, "log_dir": args.log_dir}
            for mth in methods for pi in pis for s in seeds]
    t0 = time.time()
    if args.jobs > 1:
        with Pool(args.jobs) as pool:
            rows = pool.map(run_point, jobs, chunksize=1)
    else:
        rows = [run_point(j) for j in jobs]
    for r in rows:
        r.pop("_n_tasks", None)
    csv_path = os.path.join(args.out, "per_seed.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNS)
        for r in rows:
            w.writerow([_fmt(r.get(c)) if not isinstance(r.get(c), float) else repr(r[c]) for c in COLUMNS])
    write_summary(rows, os.path.join(args.out, "summary.md"))
    with open(os.path.join(args.out, "tail_trade_rate.csv"), "w", encoding="utf-8", newline="") as fh:
        tw = csv.DictWriter(fh, ["method", "pi", "n_runs", "tail_trade_runs", "tail_trade_rate"])
        tw.writeheader()
        tw.writerows(tail_trade_rates(rows))
    meta = {"config": os.path.relpath(args.config, ROOT), "seeds": seeds, "pi_grid": pis, "methods": methods,
            "labels": {m: resolve(m).label for m in methods}, "policies": {m: resolve(m).policy for m in methods},
            "learner": args.learner or base["fraud"].get("learning", {}).get("learner", "egreedy"),
            "compliance_filter": not args.no_compliance_filter, "resample_roster": args.resample_roster,
            "backend_override": args.backend_override, "n_tasks": base["run"]["n_tasks"],
            "n_rounds": base["run"]["n_rounds"], "n_rows": len(rows), "elapsed_s": round(time.time() - t0, 2),
            "argv": sys.argv[1:] if argv is None else list(argv)}
    with open(os.path.join(args.out, "run_meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)
    print(f"wrote {csv_path} ({len(rows)} rows) in {meta['elapsed_s']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
