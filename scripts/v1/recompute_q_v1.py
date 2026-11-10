#!/usr/bin/env python3
"""Recompute T2 v0.1-scale analysis from results/v1.0/raw/ under the fixed Q definition
(PROTOCOL_v1.0.md 口径补正 2026-11-10): Q = unweighted mean of played q over seller-present tail rounds,
Q_swap / Q_theft separately, main = simple average; no token weighting. Adds tail-trade run fraction.
No simulation is rerun: all needed quantities (Q_swap, Q_theft, sid_tokens_tail) are in the raw rows.
Bootstrap call order is identical to run_v1_t2_a2.py, so E / J CIs are bit-identical to the first run."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_v1_t2_a2 import (OUT, RAW, D3, SR, PI_, POLICIES, BANDITS, PI_GRID, SEEDS, boot_mean_ci, holm)
from run_q_gate import kendall, front


def load(fn):
    rows = [json.loads(l) for l in open(os.path.join(RAW, fn))]
    for r in rows:  # fixed definition
        r["Q"] = (r["Q_swap"] + r["Q_theft"]) / 2
        r["Q_unweighted"] = r["Q"]
        r["tail_trade"] = r["sid_tokens_tail"] > 0
        r.pop("Q_tw_fallback_unweighted", None)
        r["Q_definition"] = "unweighted mean over present tail rounds; main=(Q_swap+Q_theft)/2 (protocol 口径补正 2026-11-10)"
    with open(os.path.join(RAW, fn), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    return rows


def main():
    old = json.load(open(os.path.join(OUT, "T2_v01scale_20seed.json")))
    rows = load("T2_v01scale_20seed_episodes.jsonl")
    idx = {(r["pi"], r["policy"], r["seed"]): r for r in rows}
    rng = np.random.default_rng(20261110)
    get = lambda pi, pol, k: np.array([idx[(pi, pol, s)][k] for s in SEEDS], float)  # noqa: E731
    curves, pairs_tab, degr = [], [], []
    for pi in PI_GRID:
        for pol in POLICIES:
            row = {"pi": pi, "policy": pol}
            for k in ("fraud_share", "Q", "Q_swap", "Q_theft", "Q_unweighted", "J", "learned_q_swap", "learned_q_theft"):
                mu, lo, hi, _ = boot_mean_ci(get(pi, pol, k), rng)
                row[k] = {"mean": mu, "lo": lo, "hi": hi}
            row.pop("Q_unweighted")
            row["tail_trade_frac"] = float(np.mean([idx[(pi, pol, s)]["tail_trade"] for s in SEEDS]))
            row["Q_identifiable_majority"] = row["tail_trade_frac"] > 0.5
            row["delisted_rounds_tail_total"] = int(sum(idx[(pi, pol, s)]["delisted_rounds_tail"] for s in SEEDS))
            curves.append(row)
            if pol in BANDITS and pi != 1.0:
                for k in ("fraud_share", "Q"):
                    mu, lo, hi, p = boot_mean_ci(get(pi, pol, k) - get(1.0, pol, k), rng)
                    degr.append({"pi": pi, "policy": pol, "metric": k, "diff_vs_pi1": mu, "lo": lo, "hi": hi, "p": p})
        for k in ("fraud_share", "Q"):
            res = []
            for a, b in [(D3, SR), (D3, PI_), (SR, PI_)]:
                mu, lo, hi, p = boot_mean_ci(get(pi, a, k) - get(pi, b, k), rng)
                res.append({"pi": pi, "metric": k, "pair": f"{a} - {b}", "diff": mu, "lo": lo, "hi": hi, "p": p})
            for r, pa in zip(res, holm([r["p"] for r in res])):
                r["p_holm"] = pa
            pairs_tab.extend(res)
    for pol in BANDITS:
        for k in ("fraud_share", "Q"):
            fam = [d for d in degr if d["policy"] == pol and d["metric"] == k]
            for d, pa in zip(fam, holm([d["p"] for d in fam])):
                d["p_holm"] = pa
    # sanity: E entries must be bit-identical to the first analysis
    oc = {(r["pi"], r["policy"]): r for r in old["curves"]}
    assert all(oc[(r["pi"], r["policy"])]["fraud_share"] == r["fraud_share"] for r in curves)
    # hedge appendix (not the formal gate)
    hrows = load("T2_v01scale_20seed_hedge_episodes.jsonl")
    hq = []
    for pi in PI_GRID:
        m = lambda rs, pol, k: float(np.mean([r[k] for r in rs if r["pi"] == pi and r["policy"] == pol]))  # noqa: E731
        Qe = [m(rows, p, "Q") for p in POLICIES]; Ee = [m(rows, p, "fraud_share") for p in POLICIES]
        Qh = [m(hrows, p, "Q") for p in POLICIES]; Eh = [m(hrows, p, "fraud_share") for p in POLICIES]
        hq.append({"pi": pi, "Q_egreedy": dict(zip(POLICIES, Qe)), "Q_hedge": dict(zip(POLICIES, Qh)),
                   "kendall_tau": kendall(Qe, Qh), "front_egreedy": [POLICIES[i] for i in front(Ee, Qe)],
                   "front_hedge": [POLICIES[i] for i in front(Eh, Qh)],
                   "tail_trade_frac_hedge": {p: float(np.mean([r["tail_trade"] for r in hrows if r["pi"] == pi and r["policy"] == p])) for p in POLICIES}})
    qg = {"label": "v0.1-scale", "status": "APPENDIX ONLY — not the formal §1 Q-promotion gate (protocol 口径补正 item 3/5). "
          "Formal gate: EXP3 or fictitious play, per π, all π must pass, at 40-seller scale with full baselines.",
          "learners": ["egreedy (v0.1 default)", "hedge"], "per_pi": hq}
    json.dump(qg, open(os.path.join(OUT, "Q_gate_v01scale.json"), "w"), indent=2)
    old.update({"curves": curves, "pairwise_holm": pairs_tab, "bandit_degradation_vs_pi1": degr,
                "Q_definition": "Q = unweighted mean of the played (mixed-strategy) q over seller-present rounds in the last "
                                "quarter (12/48); Q_swap, Q_theft separate; main column = simple average. No token weighting. "
                                "tail_trade_frac = share of runs with >=1 served trade by the strategic seller in those rounds. "
                                "T2 has reputation_rounds=0, so no delisting occurs; exclusion rule is implemented but inactive.",
                "hedge_check": "appendix only, see Q_gate_v01scale.json (not the formal gate)",
                "table_note": "v0.1 scale (3 sellers), to be replaced by the 40-seller main table"})
    json.dump(old, open(os.path.join(OUT, "T2_v01scale_20seed.json"), "w"), indent=2)
    print("ok")


if __name__ == "__main__":
    main()
