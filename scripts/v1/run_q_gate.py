#!/usr/bin/env python3
"""§1 Q-promotion gate at v0.1-scale: rerun T2 grid with seller learner=hedge (full-information Hedge,
'fictitious-play style' per strategic.py) and compare per-π policy ranking on Q vs the egreedy run.
Gate (pre-registered): Kendall τ ≥ 0.6 AND Pareto-front membership in (E,Q) unchanged."""
import json, os, sys, time
from multiprocessing import Pool
from itertools import combinations
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import t2_runner as T
from run_v1_t2_a2 import PI_GRID, POLICIES, SEEDS, OUT, RAW


def kendall(a, b):
    c = d = 0
    for i, j in combinations(range(len(a)), 2):
        s = np.sign(a[i] - a[j]) * np.sign(b[i] - b[j])
        c += s > 0; d += s < 0
    n = len(a) * (len(a) - 1) / 2
    return (c - d) / n


def front(E, Q):
    idx = range(len(E))
    return sorted(i for i in idx if not any((E[j] <= E[i] and Q[j] <= Q[i]) and (E[j] < E[i] or Q[j] < Q[i]) for j in idx))


def main():
    t0 = time.time()
    with Pool(8) as p:
        rows = p.map(T.t2_job, [(pi, pol, s, "hedge") for pi in PI_GRID for pol in POLICIES for s in SEEDS])
    with open(os.path.join(RAW, "T2_v01scale_20seed_hedge_episodes.jsonl"), "w") as fh:
        for r in rows: fh.write(json.dumps(r) + "\n")
    base = [json.loads(l) for l in open(os.path.join(RAW, "T2_v01scale_20seed_episodes.jsonl"))]
    out = []
    for pi in PI_GRID:
        m = lambda rs, pol, k: float(np.mean([r[k] for r in rs if r["pi"] == pi and r["policy"] == pol]))
        Qe = [m(base, p, "Q") for p in POLICIES]; Ee = [m(base, p, "fraud_share") for p in POLICIES]
        Qh = [m(rows, p, "Q") for p in POLICIES]; Eh = [m(rows, p, "fraud_share") for p in POLICIES]
        tau = kendall(Qe, Qh); fe, fh_ = front(Ee, Qe), front(Eh, Qh)
        out.append({"pi": pi, "Q_egreedy": dict(zip(POLICIES, Qe)), "Q_hedge": dict(zip(POLICIES, Qh)),
                    "E_egreedy": dict(zip(POLICIES, Ee)), "E_hedge": dict(zip(POLICIES, Eh)),
                    "kendall_tau": tau, "front_egreedy": [POLICIES[i] for i in fe],
                    "front_hedge": [POLICIES[i] for i in fh_], "pass": bool(tau >= 0.6 and fe == fh_)})
    res = {"label": "v0.1-scale", "learners": ["egreedy (v0.1 default)", "hedge"], "per_pi": out,
           "n_pi_pass": sum(o["pass"] for o in out), "n_pi": len(out),
           "all_pi_pass": all(o["pass"] for o in out), "runtime_s": round(time.time() - t0, 1)}
    json.dump(res, open(os.path.join(OUT, "Q_gate_v01scale.json"), "w"), indent=2)
    for o in out:
        print(o["pi"], round(o["kendall_tau"], 3), o["front_egreedy"], o["front_hedge"], o["pass"],
              {k[:6]: round(v, 3) for k, v in o["Q_hedge"].items()})
    print("all_pi_pass", res["all_pi_pass"], res["n_pi_pass"], "/", res["n_pi"], res["runtime_s"], "s")


if __name__ == "__main__":
    main()
