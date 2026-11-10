"""A2 add-on: D3 filter ON (audited_compliance_cascade) vs OFF (audited_cascade_unfiltered), pi=1, seeds 0-19."""
import json, os, sys
from multiprocessing import Pool
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import t2_runner as T
ON, OFF = "audited_compliance_cascade", "audited_cascade_unfiltered"
SEEDS = list(range(20)); B = 10000
rng = np.random.default_rng(20261110)
def boot(x):
    x = np.asarray(x, float); idx = rng.integers(0, len(x), (B, len(x))); m = x[idx].mean(1)
    lo, hi = np.percentile(m, [2.5, 97.5]); p = min(1.0, 2*min((m <= 0).mean(), (m >= 0).mean()))
    return float(x.mean()), float(lo), float(hi), float(p)
if __name__ == "__main__":
    with Pool(8) as pool:
        rows = pool.map(T.a2_job, [(p, s) for p in (ON, OFF) for s in SEEDS])
    idx = {(r["policy"], r["seed"]): r for r in rows}
    K = ("violation_rate", "fill_rate", "blocked_or_filtered_per_task", "task_accuracy", "fraud_share", "J")
    summ = {p: {k: boot([idx[(p, s)][k] for s in SEEDS])[:3] for k in K} for p in (ON, OFF)}
    diff = {k: boot([idx[(OFF, s)][k] - idx[(ON, s)][k] for s in SEEDS]) for k in K}
    out = "results/v1.0/A2_d3_unfiltered"
    json.dump({"pi": 1.0, "seeds": SEEDS, "summary": summ, "paired_off_minus_on": diff, "rows": rows},
              open(out + ".json", "w"), indent=2, default=str)
    L = ["# A2 add-on: D3 过滤 ON vs OFF（v0.1 规模，π=1，seed 0–19，同 seed 配对 bootstrap 10k）", "",
         "| 指标 | D3 ON | D3 OFF | OFF−ON [95% CI] | p |", "|---|---|---|---|---|"]
    for k in K:
        a, b, d = summ[ON][k], summ[OFF][k], diff[k]
        L.append(f"| {k} | {a[0]:.3f} | {b[0]:.3f} | {d[0]:+.3f} [{d[1]:+.3f}, {d[2]:+.3f}] | {d[3]:.4f} |")
    open(out + ".md", "w").write("\n".join(L) + "\n"); print("\n".join(L))
