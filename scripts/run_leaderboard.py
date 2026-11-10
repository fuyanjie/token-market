#!/usr/bin/env python3
"""Benchmark leaderboard: three tables (active attack rate, realized fraud, J).

Primary board = active_attack_rate + fraud_share.
J is secondary. Immediate-feedback J is NOT the primary ranking.

Baselines: StageRoute, PILOT (immediate feedback), fixed-a audit, random audit, v6 D3.

  /workspace/tmvenv/bin/python scripts/run_leaderboard.py --smoke
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tokenmarket.backends import MockLLM  # noqa: E402
from tokenmarket.benchmark_export import config_hash, write_jsonl  # noqa: E402
from tokenmarket.config import deep_merge, load_config  # noqa: E402
from tokenmarket.experiments import fraud_seller_id  # noqa: E402
from tokenmarket.logging_schema import validate_record  # noqa: E402
from tokenmarket.sellers import Reputation  # noqa: E402
from tokenmarket.sim import run_single  # noqa: E402
from tokenmarket.tasks import build_task_pool  # noqa: E402


class _Log:
    def __init__(self):
        self.records = []

    def write(self, rec):
        assert validate_record(rec) == []
        self.records.append(rec)


def _mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs):
    xs = list(xs)
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return (sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5


BASELINES = [
    # name, policy, overrides
    ("D3_v6", "audited_compliance_cascade",
     {"market": {"audited": {"audit_rate": 0.1, "adaptive_audit": False, "escrow": False, "reputation_rounds": 0},
                 "feedback": {"mode": "immediate", "delay_L": 0, "reveal_prob": 1.0}}}),
    ("fixed_a_audit", "audited_compliance_cascade",
     {"market": {"audited": {"audit_rate": 0.1, "adaptive_audit": False, "escrow": False, "reputation_rounds": 0},
                 "feedback": {"mode": "immediate", "delay_L": 0, "reveal_prob": 1.0}}}),
    ("random_audit", "single_best_compliant",
     {"market": {"audit": {"rate": 0.1, "types": ["identity", "length"]},
                 "feedback": {"mode": "immediate", "delay_L": 0, "reveal_prob": 1.0}}}),
    ("StageRoute", "stageroute_compliant",
     {"market": {"audit": {"rate": 0.0},
                 "feedback": {"mode": "immediate", "delay_L": 0, "reveal_prob": 1.0}}}),
    ("PILOT", "pilot_compliant",
     {"market": {"audit": {"rate": 0.0},
                 "feedback": {"mode": "immediate", "delay_L": 0, "reveal_prob": 1.0}}}),
]


def run_baseline(cfg, name, policy, over, seeds, n_tasks):
    c = deep_merge(cfg, deep_merge(
        {"fraud": {"strategy": "learning", "attack_modes_enabled": ["swap", "theft"]},
         "market": {"budget_multiplier": 2.0}}, over))
    chash = config_hash(c)
    sid = fraud_seller_id(c)
    eps = []
    for seed in seeds:
        rep = Reputation(c["models"], {})
        lg = _Log()
        m = run_single(c, "posted_price", policy, seed,
                       {"mock": MockLLM(c["market"].get("mock_confidence"))},
                       rep, lg, build_task_pool(c), n_tasks, "mock")
        qmap = m.get("learned_swap_q") or {}
        active = _mean(qmap.values()) if qmap else float(m.get("fraud_share", 0.0))
        eps.append({
            "baseline": name,
            "policy": policy,
            "run_id": f"posted_price__{policy}__seed{seed}",
            "seed": seed,
            "active_attack_rate": active,
            "fraud_share": float(m["fraud_share"]),
            "J": float(m["joint_objective"]),
            "n_audits": int(m["n_audits"]),
            "learned_q_swap": (m.get("learned_swap_q") or {}).get(sid),
            "config_hash": chash,
        })
    return {
        "baseline": name,
        "policy": policy,
        "active_attack_rate": _mean(e["active_attack_rate"] for e in eps),
        "active_attack_rate_std": _std(e["active_attack_rate"] for e in eps),
        "fraud_share": _mean(e["fraud_share"] for e in eps),
        "fraud_share_std": _std(e["fraud_share"] for e in eps),
        "J": _mean(e["J"] for e in eps),
        "J_std": _std(e["J"] for e in eps),
        "n_audits": _mean(e["n_audits"] for e in eps),
        "episodes": eps,
    }


def render_tables(rows):
    note = ("Primary board = active_attack_rate + fraud_share. "
            "J is secondary. Immediate-feedback J is NOT the primary ranking.")
    L = ["# Benchmark leaderboard", "", note, "",
         "## Table 1 — active attack rate (primary; learned q* mean)", "",
         "| rank | baseline | active_attack_rate |",
         "|---|---|---|"]
    for i, r in enumerate(sorted(rows, key=lambda x: x["active_attack_rate"]), 1):
        L.append(f"| {i} | {r['baseline']} | {r['active_attack_rate']:.3f} ± {r['active_attack_rate_std']:.3f} |")
    L += ["", "## Table 2 — realized fraud_share (primary)", "",
          "| rank | baseline | fraud_share |",
          "|---|---|---|"]
    for i, r in enumerate(sorted(rows, key=lambda x: x["fraud_share"]), 1):
        L.append(f"| {i} | {r['baseline']} | {r['fraud_share']:.3f} ± {r['fraud_share_std']:.3f} |")
    L += ["", "## Table 3 — J (secondary; NOT primary board)", "",
          "| rank | baseline | J |",
          "|---|---|---|"]
    for i, r in enumerate(sorted(rows, key=lambda x: -x["J"]), 1):
        L.append(f"| {i} | {r['baseline']} | {r['J']:.3f} ± {r['J_std']:.3f} |")
    L += ["", "Baselines: StageRoute / PILOT (immediate feedback, no audit), fixed-a D3 audit, "
          "random audit on single_best_compliant, v6 D3 (audited_compliance_cascade). "
          "D3_v6 and fixed_a_audit share the same arm in v1 (appendix may split adaptive).", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(ROOT, "configs", "benchmark", "default.yaml"))
    ap.add_argument("--seeds", type=int, nargs="+", default=None)
    ap.add_argument("--n-tasks", type=int, default=None)
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "benchmark"))
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    seeds = args.seeds or cfg.get("benchmark", {}).get("seeds", [0, 1, 2])
    n_tasks = args.n_tasks or 80
    if args.smoke:
        seeds = args.seeds or [0]
        n_tasks = args.n_tasks or 24

    os.makedirs(args.out, exist_ok=True)
    rows = []
    seen = set()
    for name, policy, over in BASELINES:
        if name in seen:
            continue
        seen.add(name)
        print(f"[leaderboard] {name} ...", flush=True)
        rows.append(run_baseline(cfg, name, policy, over, seeds, n_tasks))

    # dedupe identical D3_v6 / fixed_a in display: keep both labels but same numbers is OK per brief
    md = render_tables(rows)
    with open(os.path.join(args.out, "leaderboard.md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    with open(os.path.join(args.out, "leaderboard.json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, default=str)
    # also dump episode lines for analysis joins
    eps = [e for r in rows for e in r["episodes"]]
    write_jsonl(os.path.join(args.out, "leaderboard_episodes.jsonl"), eps)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
