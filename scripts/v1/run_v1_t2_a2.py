#!/usr/bin/env python3
"""v1.0 v0.1-scale: §0 regression gate, §4 T2 (20 seeds), §6 A2 filter-OFF control.
Outputs only under results/v1.0/. Usage: /workspace/tmvenv/bin/python scripts/v1/run_v1_t2_a2.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t2_runner as T  # noqa: E402

ROOT = T.ROOT
OUT = os.path.join(ROOT, "results", "v1.0")
RAW = os.path.join(OUT, "raw")
FROZEN = os.path.join(ROOT, "results", "benchmark", "production", "T2_episodes.jsonl")
D3, SR, PI_ = "audited_compliance_cascade", "stageroute_compliant", "pilot_compliant"
POLICIES = [D3, SR, PI_]
BANDITS = [SR, PI_]
PI_GRID = [1.0, 0.2, 0.18, 0.15, 0.12, 0.11, 0.1, 0.08, 0.06, 0.05, 0.0]
SEEDS = list(range(20))
B = 10_000
ALPHA = 0.05
FROZEN_FIELDS = ["run_id", "seed", "a", "pi", "L", "reputation_rounds", "active_attack_rate", "learned_q_swap",
                 "learned_q_theft", "fraud_share", "J", "n_audits", "config_hash", "policy", "task"]


def boot_mean_ci(x, rng):
    x = np.asarray(x, float)
    n = len(x)
    idx = rng.integers(0, n, size=(B, n))
    bm = x[idx].mean(axis=1)
    lo, hi = np.percentile(bm, [2.5, 97.5])
    p = min(1.0, 2 * min((bm <= 0).mean(), (bm >= 0).mean()))
    return float(x.mean()), float(lo), float(hi), float(p)


def holm(ps):
    m = len(ps)
    order = np.argsort(ps)
    adj = [0.0] * m
    run = 0.0
    for k, i in enumerate(order):
        run = max(run, min(1.0, (m - k) * ps[i]))
        adj[i] = run
    return adj


def main():
    t0 = time.time()
    os.makedirs(RAW, exist_ok=True)
    timings = {}
    # ---------------- §0 regression gate
    frozen = [json.loads(l) for l in open(FROZEN)]
    jobs0 = [(r["pi"], r["policy"], r["seed"]) for r in frozen]
    with Pool(8) as pool:
        rerun = pool.map(T.t2_job, jobs0)
    n_cmp, maxdiff, mism = 0, 0.0, []
    for f, r in zip(frozen, rerun):
        for k in FROZEN_FIELDS:
            a, b = f.get(k), r.get(k)
            n_cmp += 1
            if isinstance(a, float) or isinstance(b, float):
                d = abs((a or 0.0) - (b or 0.0)) if (a is not None and b is not None) else (0.0 if a == b else 1.0)
                maxdiff = max(maxdiff, d)
                if d > 1e-9:
                    mism.append((f["run_id"], f["pi"], k, a, b))
            elif a != b:
                mism.append((f["run_id"], f["pi"], k, a, b))
    gate = {"n_rows": len(frozen), "n_fields_compared": n_cmp, "max_abs_diff": maxdiff,
            "n_mismatches": len(mism), "mismatches": mism[:20], "pass": not mism}
    json.dump(gate, open(os.path.join(OUT, "regression_gate_seed0-2.json"), "w"), indent=2)
    print("GATE", json.dumps({k: v for k, v in gate.items() if k != "mismatches"}), flush=True)
    timings["gate_s"] = round(time.time() - t0, 1)
    if not gate["pass"]:
        print("REGRESSION GATE FAILED — stopping", flush=True)
        sys.exit(2)

    # ---------------- §4 T2 20 seeds
    t1 = time.time()
    jobs = [(pi, pol, s) for pi in PI_GRID for pol in POLICIES for s in SEEDS]
    with Pool(8) as pool:
        rows = pool.map(T.t2_job, jobs)
    with open(os.path.join(RAW, "T2_v01scale_20seed_episodes.jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    timings["t2_s"] = round(time.time() - t1, 1)
    # seeds 0-2 subset of 20-seed run must equal frozen (sanity, grid points in frozen)
    idx = {(r["pi"], r["policy"], r["seed"]): r for r in rows}
    sub_ok = all(abs(idx[(f["pi"], f["policy"], f["seed"])]["J"] - f["J"]) <= 1e-12 for f in frozen)

    rng = np.random.default_rng(20261110)
    get = lambda pi, pol, k: np.array([idx[(pi, pol, s)][k] for s in SEEDS], float)  # noqa: E731
    curves, pairs_tab, degr = [], [], []
    for pi in PI_GRID:
        for pol in POLICIES:
            row = {"pi": pi, "policy": pol}
            for k in ("fraud_share", "Q", "Q_swap", "Q_theft", "Q_unweighted", "J", "learned_q_swap",
                      "learned_q_theft"):
                mu, lo, hi, _ = boot_mean_ci(get(pi, pol, k), rng)
                row[k] = {"mean": mu, "lo": lo, "hi": hi}
            row["Q_tw_fallback_runs"] = int(sum(idx[(pi, pol, s)]["Q_tw_fallback_unweighted"] for s in SEEDS))
            row["delisted_rounds_tail_total"] = int(sum(idx[(pi, pol, s)]["delisted_rounds_tail"] for s in SEEDS))
            curves.append(row)
            if pol in BANDITS and pi != 1.0:  # degradation vs pi=1 (same seed, paired)
                for k in ("fraud_share", "Q"):
                    d = get(pi, pol, k) - get(1.0, pol, k)
                    mu, lo, hi, p = boot_mean_ci(d, rng)
                    degr.append({"pi": pi, "policy": pol, "metric": k, "diff_vs_pi1": mu, "lo": lo, "hi": hi,
                                 "p": p})
        for k in ("fraud_share", "Q"):
            prs = [(D3, SR), (D3, PI_), (SR, PI_)]
            res = []
            for a, b in prs:
                mu, lo, hi, p = boot_mean_ci(get(pi, a, k) - get(pi, b, k), rng)
                res.append({"pi": pi, "metric": k, "pair": f"{a} - {b}", "diff": mu, "lo": lo, "hi": hi, "p": p})
            for r, pa in zip(res, holm([r["p"] for r in res])):
                r["p_holm"] = pa
            pairs_tab.extend(res)
    # Holm within each (bandit, metric) family over pi for degradation
    for pol in BANDITS:
        for k in ("fraud_share", "Q"):
            fam = [d for d in degr if d["policy"] == pol and d["metric"] == k]
            for d, pa in zip(fam, holm([d["p"] for d in fam])):
                d["p_holm"] = pa

    # ---------------- appendix: ΔJ (pre-registered: per-seed D3 J − max bandit J; paired bootstrap)
    dj = []
    perseed = {s: {} for s in SEEDS}
    for pi in PI_GRID:
        d = get(pi, D3, "J") - np.maximum(get(pi, SR, "J"), get(pi, PI_, "J"))
        mu, lo, hi, p = boot_mean_ci(d, rng)
        mu_m = float(get(pi, D3, "J").mean() - max(get(pi, SR, "J").mean(), get(pi, PI_, "J").mean()))
        dj.append({"pi": pi, "dJ_mean": mu, "lo": lo, "hi": hi, "p": p, "dJ_of_means": mu_m,
                   "n_seeds_positive": int((d > 0).sum())})
        for s, v in zip(SEEDS, d):
            perseed[s][pi] = float(v)
    grid_desc = sorted(PI_GRID, reverse=True)
    cross = []
    for s in SEEDS:
        v = [perseed[s][p] for p in grid_desc]
        first = None
        for i in range(1, len(grid_desc)):
            if v[i - 1] < 0 <= v[i]:
                first = [grid_desc[i], grid_desc[i - 1]]
                break
        signs = [1 if x >= 0 else -1 for x in v]
        nflip = sum(1 for i in range(1, len(signs)) if signs[i] != signs[i - 1])
        cross.append({"seed": s, "first_crossover_interval": first, "n_sign_changes": nflip,
                      "always_nonneg": all(x >= 0 for x in v), "always_neg": all(x < 0 for x in v),
                      "dJ_by_pi": {str(p): perseed[s][p] for p in grid_desc}})
    at = {r["pi"]: r for r in dj}
    keep = at[0.12]["hi"] < 0 and at[0.10]["lo"] > 0
    rule = {"rule": "keep (0.10,0.12) iff 95% CI of paired ΔJ at π=0.12 entirely <0 AND at π=0.10 entirely >0",
            "dJ_0.12": at[0.12], "dJ_0.10": at[0.10], "keep_interval": bool(keep),
            "outcome": "keep (0.10, 0.12)" if keep else "conditional interval + per-seed distribution"}

    # ---------------- §6 A2
    t2 = time.time()
    a2_pols = list(T.A2_POLICIES.keys()) + list(T.A2_POLICIES.values()) + [D3]
    with Pool(8) as pool:
        a2rows = pool.map(T.a2_job, [(p, s) for p in a2_pols for s in SEEDS])
    with open(os.path.join(RAW, "A2_episodes.jsonl"), "w") as fh:
        for r in a2rows:
            fh.write(json.dumps(r) + "\n")
    a2idx = {(r["policy"], r["seed"]): r for r in a2rows}
    a2sum = []
    for p in a2_pols:
        row = {"policy": p, "filter": "ON" if p in T.A2_POLICIES or p == D3 else "OFF"}
        for k in ("violation_rate", "fill_rate", "blocked_or_filtered_per_task", "task_accuracy", "fraud_share",
                  "J"):
            mu, lo, hi, _ = boot_mean_ci([a2idx[(p, s)][k] for s in SEEDS], rng)
            row[k] = {"mean": mu, "lo": lo, "hi": hi}
        a2sum.append(row)
    a2diff = []
    for on, off in T.A2_POLICIES.items():
        for k in ("violation_rate", "fill_rate", "blocked_or_filtered_per_task"):
            x = np.array([a2idx[(off, s)][k] - a2idx[(on, s)][k] for s in SEEDS])
            mu, lo, hi, p = boot_mean_ci(x, rng)
            a2diff.append({"on": on, "off": off, "metric": k, "diff_off_minus_on": mu, "lo": lo, "hi": hi, "p": p})
    timings["a2_s"] = round(time.time() - t2, 1)
    timings["total_s"] = round(time.time() - t0, 1)

    out = {"label": "v0.1-scale", "protocol": "docs/PROTOCOL_v1.0.md", "seeds": SEEDS, "pi_grid": PI_GRID,
           "bootstrap": {"B": B, "ci": 0.95, "paired": "same-seed", "seed_rng": 20261110},
           "regression_gate": {k: v for k, v in gate.items() if k != "mismatches"},
           "seed0_2_subset_equals_frozen": sub_ok,
           "curves": curves, "pairwise_holm": pairs_tab, "bandit_degradation_vs_pi1": degr,
           "appendix_dJ": dj, "per_seed_crossover": cross, "pi_star_rule": rule, "timings": timings}
    json.dump(out, open(os.path.join(OUT, "T2_v01scale_20seed.json"), "w"), indent=2)
    json.dump({"label": "v0.1-scale", "pi": 1.0, "seeds": SEEDS, "summary": a2sum, "paired_off_minus_on": a2diff,
               "pairs": T.A2_POLICIES, "timings": timings},
              open(os.path.join(OUT, "A2_compliance_control.json"), "w"), indent=2)
    print("DONE", json.dumps(timings), "rule:", rule["outcome"], flush=True)


if __name__ == "__main__":
    main()
