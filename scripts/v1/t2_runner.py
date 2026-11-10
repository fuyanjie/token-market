#!/usr/bin/env python3
"""v1.0 (v0.1-scale) T2 / A2 runner — Experiment wrapper. Does NOT modify core code.

Reproduces scripts/run_benchmark_tasks.py `--full --use-cache` T2 settings exactly (same overrides,
same _run_cached path, same _episode row), and additionally returns per-round q histories and
per-round strategic-seller tokens so §1 Q can be computed. Writes only under results/v1.0/.
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import run_benchmark_tasks as rbt  # noqa: E402
from tokenmarket.config import deep_merge, load_config  # noqa: E402
from tokenmarket.benchmark_export import config_hash  # noqa: E402
from tokenmarket.experiments import fraud_seller_id  # noqa: E402
from tokenmarket.sim import run_single, prepare, build_backends  # noqa: E402
from tokenmarket.sellers import Reputation  # noqa: E402

PROD_CFG = os.path.join(ROOT, "configs", "benchmark", "production.yaml")
_CACHE = {}


def base_cfg():
    if "cfg" not in _CACHE:
        _CACHE["cfg"] = load_config(PROD_CFG)
    return _CACHE["cfg"]


def t2_cfg(pi, learner=None):
    """Identical override to run_benchmark_tasks.task_t2 (learner=None keeps the v0.1 default egreedy)."""
    over = {"fraud": {"strategy": "learning", "attack_modes_enabled": ["swap", "theft"]},
            "market": {"budget_multiplier": 2.0,
                       "feedback": {"mode": "sparse" if pi < 1.0 else "immediate",
                                    "delay_L": 0, "reveal_prob": float(pi)},
                       "audited": {"adaptive_audit": False, "escrow": False, "reputation_rounds": 0}}}
    if learner is not None:  # §1 Q-robustness: alternative seller learning rule (e.g. hedge)
        over["fraud"]["learning"] = {"learner": learner}
    return deep_merge(base_cfg(), over)


def run_cached(cfg, policy, seed, n_tasks):
    """Same as run_benchmark_tasks._run_cached (inline closure there)."""
    pool, cache, stats, _ = prepare(cfg, None, cfg["run"].get("cache_file"), None, lambda *a: None)
    sb = {s.get("backend", "mock") for s in cfg["sellers"]}
    backends = build_backends(cfg, sb, cache)
    lg = rbt._Log()
    rep = Reputation(cfg["models"], stats if isinstance(stats, dict) else {})
    m = run_single(cfg, "posted_price", policy, seed, backends, rep, lg, pool, n_tasks, None)
    return m, lg.records


def q_stats(m, recs, cfg, sid):
    """§1 Q: last quarter of rounds, seller-present rounds only."""
    n_rounds = int(cfg["run"]["n_rounds"])
    hs = list(m["swap_q_history"][sid])
    ht = list(m["theft_q_history"][sid])
    assert len(hs) == n_rounds == len(ht), (len(hs), n_rounds)
    # delisted rounds: from audit trail ban_until (rep_rounds=0 in T2 -> none expected)
    banned = set()
    for r in recs:  # transaction rows carry both `round` and `ban_until` (set when caught & delisted)
        if r.get("seller_id") == sid and r.get("ban_until") is not None:
            banned.update(range(int(r["round"]) + 1, min(int(r["ban_until"]), n_rounds)))
    k = max(1, n_rounds // 4)
    tail = list(range(n_rounds - k, n_rounds))
    present = [r for r in tail if r not in banned]
    delisted = [r for r in tail if r in banned]
    tok = defaultdict(int)
    for r in recs:
        if r.get("seller_id") == sid and r.get("status") == "allowed":
            tok[int(r["round"])] += int(r.get("billed_tokens") or 0)
    mean = lambda xs: sum(xs) / len(xs) if xs else None  # noqa: E731
    qs = mean([hs[r] for r in present])
    qt = mean([ht[r] for r in present])
    W = sum(tok[r] for r in present)
    # Protocol 口径补正 (2026-11-10): Q = unweighted mean over present rounds, main = (Q_swap+Q_theft)/2
    q_main = None if qs is None else (qs + qt) / 2
    return {"Q_swap": qs, "Q_theft": qt, "Q": q_main, "Q_unweighted": q_main,
            "tail_trade": W > 0,
            "Q_tail_rounds": k, "Q_present_rounds": len(present),
            "delisted_rounds_tail": len(delisted), "delisted_rounds_total": len(banned),
            "q_swap_delisted": mean([hs[r] for r in delisted]), "q_theft_delisted": mean([ht[r] for r in delisted]),
            "sid_tokens_tail": W}


def t2_job(args):
    pi, policy, seed = args[:3]
    learner = args[3] if len(args) > 3 else None
    cfg = t2_cfg(pi, learner)
    n_tasks = cfg["run"]["n_tasks"]
    chash = config_hash(cfg)
    m, recs = run_cached(cfg, policy, seed, n_tasks)
    ep = rbt._episode(m, cfg, policy, seed, chash, records=recs)
    ep["task"] = "T2"
    ep["pi"] = float(pi)
    sid = fraud_seller_id(cfg)
    ep.update(q_stats(m, recs, cfg, sid))
    ep["strategic_seller"] = sid
    ep["seller_learner"] = cfg["fraud"].get("learning", {}).get("learner", "egreedy")
    ep["n_strategic_sellers"] = sum(1 for s in cfg["sellers"] if s.get("strategy"))
    return ep


A2_POLICIES = {  # filter ON  -> filter OFF control (existing policy ids, no core change)
    "stageroute_compliant": "stageroute",
    "pilot_compliant": "pilot",
    "single_cheapest_compliant": "compliance_unaware_cheapest",
}


def a2_job(args):
    policy, seed = args
    cfg = t2_cfg(1.0)
    n_tasks = cfg["run"]["n_tasks"]
    m, recs = run_cached(cfg, policy, seed, n_tasks)
    n_attempt = sum(1 for r in recs if r.get("status") in ("allowed", "blocked"))
    return {"policy": policy, "seed": seed,
            "violation_rate": m["compliance_violation_rate"], "compliance_violations": m["compliance_violations"],
            "fill_rate": m["fill_rate"], "blocked_at_gateway": m["blocked_at_gateway"],
            "filtered_candidates": m["filtered_candidates"], "blocked_or_filtered": m["blocked_or_filtered"],
            "n_attempts": n_attempt, "n_tasks": n_tasks,
            "blocked_or_filtered_per_task": m["blocked_or_filtered"] / n_tasks,
            "task_accuracy": m["task_accuracy"], "fraud_share": m["fraud_share"],
            "J": m["joint_objective"], "violations_by_rule": m.get("violations_by_rule"),
            "filtered_by_rule": m.get("filtered_by_rule")}
