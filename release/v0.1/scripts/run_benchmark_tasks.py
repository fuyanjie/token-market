#!/usr/bin/env python3
"""Standard benchmark tasks T1–T3 with FIXED seeds (mock backend).

  T1 fixed-audit deterrence (press q*)
  T2 sparse-label regime (sweep π, report π* crossover vs StageRoute/PILOT)
  T3 same-budget adaptive audit (NOT primary board)

  /workspace/tmvenv/bin/python scripts/run_benchmark_tasks.py --smoke
  /workspace/tmvenv/bin/python scripts/run_benchmark_tasks.py --tasks T1 T2 T3
  /workspace/tmvenv/bin/python scripts/run_benchmark_tasks.py --full --use-cache --tasks T1 T2 T3
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket.benchmark_export import config_hash, export_knobs, write_jsonl  # noqa: E402
from tokenmarket.config import deep_merge, load_config  # noqa: E402
from tokenmarket.experiments import Context, fraud_seller_id  # noqa: E402
from tokenmarket.sim import run_single  # noqa: E402
from tokenmarket.backends import MockLLM  # noqa: E402
from tokenmarket.sellers import Reputation  # noqa: E402
from tokenmarket.tasks import build_task_pool  # noqa: E402
from tokenmarket.logging_schema import validate_record  # noqa: E402


class _Log:
    def __init__(self):
        self.records = []

    def write(self, rec):
        errs = validate_record(rec)
        if errs:
            raise ValueError(errs)
        self.records.append(rec)


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def _run(cfg, policy, seed, n_tasks):
    rep = Reputation(cfg["models"], {})
    lg = _Log()
    pool = build_task_pool(cfg)
    m = run_single(cfg, "posted_price", policy, seed,
                   {"mock": MockLLM(cfg["market"].get("mock_confidence"))},
                   rep, lg, pool, n_tasks, "mock")
    return m, lg.records


def _episode(m, cfg, policy, seed, chash, records=None):
    # active_attack_rate = served attack share; learned_q_* are separate (Idea lock).
    if records:
        served = [r for r in records if r.get("status") == "allowed"]
        if served:
            attacked = [r for r in served if (r.get("attack_mode") or "none") not in ("none", None)]
            active = len(attacked) / len(served)
        else:
            active = float(m.get("fraud_share", 0.0))
    else:
        active = float(m.get("fraud_share", 0.0))
    fb = cfg["market"].get("feedback", {})
    L = fb.get("delay_L", 0)
    L_out = None if L is None or L == float("inf") else int(L)
    sid = fraud_seller_id(cfg)
    return {
        "run_id": f"posted_price__{policy}__seed{seed}",
        "seed": seed,
        "a": float(m.get("audit_rate", 0.0)),
        "pi": float(fb.get("reveal_prob", 1.0)),
        "L": L_out,
        "reputation_rounds": int(m.get("reputation_rounds", 0)),
        "active_attack_rate": float(active),
        "learned_q_swap": (m.get("learned_swap_q") or {}).get(sid),
        "learned_q_theft": (m.get("learned_theft_q") or {}).get(sid),
        "fraud_share": float(m.get("fraud_share", 0.0)),
        "J": float(m.get("joint_objective", 0.0)),
        "n_audits": int(m.get("n_audits", 0)),
        "config_hash": chash,
        "policy": policy,
    }


def task_t1(cfg, seeds, n_tasks, out_dir, log):
    """Fixed a deterrence on D3."""
    a = float(cfg.get("benchmark", {}).get("tasks", {}).get("T1", {}).get("a", 0.1))
    policy = "audited_compliance_cascade"
    over = {"fraud": {"strategy": "learning", "attack_modes_enabled": ["swap", "theft"]},
            "market": {"audited": {"audit_rate": a, "adaptive_audit": False, "escrow": False,
                                   "reputation_rounds": 0},
                       "feedback": {"mode": "immediate", "delay_L": 0, "reveal_prob": 1.0},
                       "budget_multiplier": 2.0}}
    c = deep_merge(cfg, over)
    chash = config_hash(c)
    rows = []
    for seed in seeds:
        m, recs = _run(c, policy, seed, n_tasks)
        ep = _episode(m, c, policy, seed, chash, records=recs)
        ep["task"] = "T1"
        rows.append(ep)
        log(f"[T1] seed={seed} q*={ep['active_attack_rate']:.3f} fraud={ep['fraud_share']:.3f} J={ep['J']:.3f}")
    path = os.path.join(out_dir, "T1_episodes.jsonl")
    write_jsonl(path, rows)
    return {"task": "T1", "path": path, "rows": rows,
            "summary": {"active_attack_rate": _mean(r["active_attack_rate"] for r in rows),
                        "fraud_share": _mean(r["fraud_share"] for r in rows),
                        "J": _mean(r["J"] for r in rows)}}


def task_t2(cfg, seeds, n_tasks, out_dir, log):
    """Sparse π sweep; report π* where D3 overtakes StageRoute on fraud (primary) / notes J crossover."""
    grid = list(cfg.get("benchmark", {}).get("tasks", {}).get("T2", {}).get("pi_grid",
                                                                           [1.0, 0.2, 0.1, 0.05, 0.0]))
    policies = ["audited_compliance_cascade", "stageroute_compliant", "pilot_compliant"]
    rows = []
    for pi in grid:
        over = {"fraud": {"strategy": "learning", "attack_modes_enabled": ["swap", "theft"]},
                "market": {"budget_multiplier": 2.0,
                           "feedback": {"mode": "sparse" if pi < 1.0 else "immediate",
                                        "delay_L": 0, "reveal_prob": float(pi)},
                           "audited": {"adaptive_audit": False, "escrow": False, "reputation_rounds": 0}}}
        c = deep_merge(cfg, over)
        chash = config_hash(c)
        for policy in policies:
            for seed in seeds:
                m, recs = _run(c, policy, seed, n_tasks)
                ep = _episode(m, c, policy, seed, chash, records=recs)
                ep["task"] = "T2"
                ep["pi"] = float(pi)
                rows.append(ep)
            avg_f = _mean(r["fraud_share"] for r in rows if r["policy"] == policy and r["pi"] == float(pi))
            avg_a = _mean(r["active_attack_rate"] for r in rows if r["policy"] == policy and r["pi"] == float(pi))
            log(f"[T2] pi={pi} {policy}: attack={avg_a:.3f} fraud={avg_f:.3f}")
    # π* on secondary J: densest grid points where ΔJ = D3 - best(bandit) flips sign (pi_dense style).
    # Primary board remains active_attack_rate + fraud_share; J crossover is protocol narrative only.
    bandits = ("stageroute_compliant", "pilot_compliant")
    grid_sorted = sorted({float(p) for p in grid}, reverse=True)
    delta_rows = []
    cross = None
    prev = None  # (pi, deltaJ) at previous (higher) pi
    for pi in grid_sorted:
        d3j = _mean(r["J"] for r in rows if r["policy"] == "audited_compliance_cascade" and r["pi"] == float(pi))
        best_b = max(
            _mean(r["J"] for r in rows if r["policy"] == b and r["pi"] == float(pi))
            for b in bandits
        )
        dJ = d3j - best_b
        delta_rows.append({"pi": pi, "D3_J": d3j, "best_bandit_J": best_b, "delta_J": dJ})
        if prev is not None and prev["delta_J"] < 0 <= dJ:
            cross = {
                "pi_star_J_interval": [float(pi), float(prev["pi"])],  # (lo, hi) where sign flips
                "pi_star_J": float(pi),
                "delta_J_at_lo": dJ,
                "delta_J_at_hi": prev["delta_J"],
                "note": "D3 J overtakes best compliant bandit between these π; primary board remains attack/fraud",
            }
            break
        prev = {"pi": pi, "delta_J": dJ}
    if cross is None:
        # fallback: first (highest) π where D3 already wins, or none
        wins = [d for d in delta_rows if d["delta_J"] >= 0]
        if wins:
            p = max(d["pi"] for d in wins)
            cross = {"pi_star_J": p, "pi_star_J_interval": None,
                     "note": "D3 J >= best bandit at/below this π on grid; no sign-flip bracket (coarse or all-win)"}
        else:
            cross = {"pi_star_J": None, "pi_star_J_interval": None,
                     "note": "D3 J never overtakes bandits on this grid"}
    path = os.path.join(out_dir, "T2_episodes.jsonl")
    write_jsonl(path, rows)
    meta = {"pi_grid": grid, "crossover": cross, "delta_J_by_pi": delta_rows}
    with open(os.path.join(out_dir, "T2_crossover.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    return {"task": "T2", "path": path, "rows": rows, "meta": meta}


def task_t3(cfg, seeds, n_tasks, out_dir, log):
    """Same expected audit budget: fixed vs adaptive. NOT primary board."""
    a = float(cfg.get("benchmark", {}).get("tasks", {}).get("T3", {}).get("a", 0.1))
    policy = "audited_compliance_cascade"
    rows = []
    for arm, adaptive in (("fixed", False), ("adaptive", True)):
        over = {"fraud": {"strategy": "learning", "attack_modes_enabled": ["swap", "theft"]},
                "market": {"budget_multiplier": 2.0,
                           "audited": {"audit_rate": a, "adaptive_audit": adaptive,
                                       "escrow": False, "reputation_rounds": 0},
                           "feedback": {"mode": "immediate", "delay_L": 0, "reveal_prob": 1.0}}}
        c = deep_merge(cfg, over)
        chash = config_hash(c)
        for seed in seeds:
            m, recs = _run(c, policy, seed, n_tasks)
            ep = _episode(m, c, policy, seed, chash, records=recs)
            ep["task"] = "T3"
            ep["arm"] = arm
            ep["primary_board"] = False
            rows.append(ep)
            log(f"[T3] {arm} seed={seed} fraud={ep['fraud_share']:.3f} audits={ep['n_audits']} J={ep['J']:.3f}")
    path = os.path.join(out_dir, "T3_episodes.jsonl")
    write_jsonl(path, rows)
    return {"task": "T3", "path": path, "rows": rows,
            "note": "T3 is appendix / cost-reduction; NOT primary leaderboard"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None,
                    help="default: configs/benchmark/default.yaml; with --full: configs/benchmark/production.yaml")
    ap.add_argument("--tasks", nargs="+", default=["T1", "T2", "T3"], choices=["T1", "T2", "T3"])
    ap.add_argument("--seeds", type=int, nargs="+", default=None)
    ap.add_argument("--n-tasks", type=int, default=None)
    ap.add_argument("--out", default=None,
                    help="default: results/benchmark; with --full: results/benchmark/production")
    ap.add_argument("--smoke", action="store_true", help="seed=[0], n_tasks=24, T1 only unless --tasks set")
    ap.add_argument("--full", action="store_true",
                    help="production scale (n_tasks/n_rounds/pi_grid match pi_dense/experiments); "
                         "writes to results/benchmark/production by default")
    ap.add_argument("--use-cache", action="store_true",
                    help="use per-seller backends + llm_outputs cache (closer to pi_dense/v6 numbers)")
    args = ap.parse_args(argv)

    if args.full and args.smoke:
        raise SystemExit("choose either --smoke or --full, not both")

    if args.config is None:
        args.config = os.path.join(
            ROOT, "configs", "benchmark",
            "production.yaml" if args.full else "default.yaml")
    if args.out is None:
        args.out = os.path.join(
            ROOT, "results", "benchmark",
            *(["production"] if args.full else []))

    cfg = load_config(args.config)
    seeds = args.seeds or cfg.get("benchmark", {}).get("seeds", [0, 1, 2])
    n_tasks = args.n_tasks or cfg.get("run", {}).get("n_tasks", 120)
    tasks = args.tasks
    if args.smoke:
        seeds = args.seeds or [0]
        n_tasks = args.n_tasks or 24
        if args.tasks == ["T1", "T2", "T3"]:
            tasks = ["T1"]
    if args.full:
        # production floors (config should already set these; CLI can still override)
        seeds = args.seeds or cfg.get("benchmark", {}).get("seeds", [0, 1, 2])
        n_tasks = args.n_tasks or cfg.get("run", {}).get("n_tasks", 480)

    # optional: wire cache backends into _run via monkeypatch of module-level helper
    global _run  # noqa: PLW0603
    if args.use_cache:
        from tokenmarket.sim import prepare, build_backends
        from tokenmarket.sellers import Reputation as _Rep

        def _run_cached(cfg, policy, seed, n_tasks):  # noqa: ANN001
            def _log(*a):
                pass
            pool, cache, stats, _ = prepare(cfg, None, cfg["run"].get("cache_file"), None, _log)
            sb = {s.get("backend", "mock") for s in cfg["sellers"]}
            backends = build_backends(cfg, sb, cache)
            lg = _Log()
            rep = _Rep(cfg["models"], stats if isinstance(stats, dict) else {})
            m = run_single(cfg, "posted_price", policy, seed, backends, rep, lg, pool, n_tasks, None)
            return m, lg.records
        _run = _run_cached  # type: ignore

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "knobs.yaml"), "w", encoding="utf-8") as fh:
        import yaml
        yaml.safe_dump(export_knobs(cfg), fh, sort_keys=False)

    log = lambda *a: print(*a, flush=True)  # noqa: E731
    results = {}
    if "T1" in tasks:
        results["T1"] = task_t1(cfg, seeds, n_tasks, args.out, log)
    if "T2" in tasks:
        results["T2"] = task_t2(cfg, seeds, n_tasks, args.out, log)
    if "T3" in tasks:
        results["T3"] = task_t3(cfg, seeds, n_tasks, args.out, log)

    summary = {k: {kk: vv for kk, vv in v.items() if kk != "rows"} for k, v in results.items()}
    with open(os.path.join(args.out, "tasks_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)
    log(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
