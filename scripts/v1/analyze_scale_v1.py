#!/usr/bin/env python3
"""Bootstrap + Holm + figures for a scripts/run_v1.py output directory (PROTOCOL_v1.0)."""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import defaultdict
from itertools import combinations

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

B = 10_000
RNG_SEED = 20261110
HOLLOW = 0.5  # Q not identifiable when tail_trade_rate <= this
D3 = "fixed_audit_a0.10"
BANDITS = ("pilot", "stageroute")
SHORT = {
    "pilot": "PILOT",
    "stageroute": "StageRoute",
    "cheapest_fixed": "cheapest",
    "strongest_fixed": "strongest",
    "random_audit": "random-intensity",
    "fixed_audit_a0.05": "fixed a=0.05",
    "fixed_audit_a0.10": "D3-ref (a=0.10)",
    "fixed_audit_a0.20": "fixed a=0.20",
    "risk_adaptive_audit": "risk-adaptive",
}
ORDER = [
    "pilot", "stageroute", "cheapest_fixed", "strongest_fixed",
    "fixed_audit_a0.05", "fixed_audit_a0.10", "fixed_audit_a0.20",
    "random_audit", "risk_adaptive_audit",
]
STY = {
    "pilot": dict(fmt="o-", color="C0"),
    "stageroute": dict(fmt="s-", color="C1"),
    "cheapest_fixed": dict(fmt="v--", color="C2"),
    "strongest_fixed": dict(fmt="^--", color="C3"),
    "random_audit": dict(fmt="D-.", color="C4"),
    "fixed_audit_a0.05": dict(fmt="P--", color="0.45"),
    "fixed_audit_a0.10": dict(fmt="k--", color="k"),
    "fixed_audit_a0.20": dict(fmt="X--", color="0.3"),
    "risk_adaptive_audit": dict(fmt="p-.", color="C5"),
}
KEY_PI = (1.0, 0.5, 0.30, 0.20, 0.12, 0.10, 0.08, 0.06, 0.02, 0.0)
METRICS = ("E", "E_tok", "Q", "Q_swap", "Q_theft", "Q_downgrade", "J")
SCALE_SHA256 = "780e9b961d89bad6fd520c9cbfd5710055ff2d5d3e0ff3bcfbd745709eb0da6c"


def parse_bool(x):
    if isinstance(x, bool):
        return x
    s = str(x).strip().lower()
    if s in ("1", "true", "yes"):
        return True
    if s in ("0", "false", "no", ""):
        return False
    raise ValueError(x)


def parse_float(x, default=np.nan):
    if x is None or str(x).strip() == "":
        return default
    return float(x)


def boot_mean_ci(x, rng):
    x = np.asarray(x, float)
    n = len(x)
    idx = rng.integers(0, n, size=(B, n))
    bm = x[idx].mean(axis=1)
    lo, hi = np.percentile(bm, [2.5, 97.5])
    p = min(1.0, 2 * min((bm <= 0).mean(), (bm >= 0).mean()))
    return float(np.nanmean(x)), float(lo), float(hi), float(p)


def holm(ps):
    m = len(ps)
    order = np.argsort(ps)
    adj = [0.0] * m
    run = 0.0
    for k, i in enumerate(order):
        run = max(run, min(1.0, (m - k) * ps[i]))
        adj[i] = run
    return adj


def kendall_tau(rank_a, rank_b):
    # rank_* : dict method -> rank (0 best). τ = (C-D)/(C+D) over pairs, ties in either ranking ignored in denom? standard tau-a uses n(n-1)/2
    items = list(rank_a)
    n = len(items)
    if n < 2:
        return np.nan, 0, 0, 0
    C = D = T = 0
    for i, j in combinations(items, 2):
        da = rank_a[i] - rank_a[j]
        db = rank_b[i] - rank_b[j]
        if da == 0 or db == 0:
            T += 1
            continue
        if (da > 0) == (db > 0):
            C += 1
        else:
            D += 1
    denom = C + D + T
    tau = (C - D) / denom if denom else np.nan  # tau-b like if ties in denom; also report tau-a
    tau_a = (C - D) / (n * (n - 1) / 2)
    return float(tau_a), C, D, T


def pareto_front(points):
    """points: {method: (E, Q)}, both lower-better. Return set of non-dominated methods."""
    front = set()
    for a, (ea, qa) in points.items():
        dominated = False
        for b, (eb, qb) in points.items():
            if b == a:
                continue
            if eb <= ea and qb <= qa and (eb < ea or qb < qa):
                dominated = True
                break
        if not dominated:
            front.add(a)
    return front


def load_csv(path):
    rows = list(csv.DictReader(open(path)))
    out = []
    for r in rows:
        d = dict(r)
        d["pi"] = float(r["pi"])
        d["seed"] = int(r["seed"])
        for k in METRICS + ("quality", "cost", "fill_rate", "violation_rate"):
            d[k] = parse_float(r.get(k, ""))
        d["tail_trade"] = 1.0 if parse_bool(r["tail_trade"]) else 0.0
        out.append(d)
    return out


def fmt_ci(d, digits=3):
    return f"{d['mean']:.{digits}f} [{d['lo']:.{digits}f}, {d['hi']:.{digits}f}]"


def analyze(indir, outdir, peer=None, title_prefix="40-seller main"):
    os.makedirs(outdir, exist_ok=True)
    meta = json.load(open(os.path.join(indir, "run_meta.json")))
    rows = load_csv(os.path.join(indir, "per_seed.csv"))
    methods = [m for m in ORDER if m in {r["method"] for r in rows}]
    pis = sorted({r["pi"] for r in rows})
    seeds = sorted({r["seed"] for r in rows})
    rng = np.random.default_rng(RNG_SEED)

    def vec(method, pi, key):
        v = {r["seed"]: r[key] for r in rows if r["method"] == method and r["pi"] == pi}
        return np.array([v[s] for s in seeds], float)

    curves = []
    for pi in pis:
        for m in methods:
            row = {"pi": pi, "method": m, "label": SHORT[m]}
            for k in METRICS:
                mu, lo, hi, p = boot_mean_ci(vec(m, pi, k), rng)
                row[k] = {"mean": mu, "lo": lo, "hi": hi}
            mu, lo, hi, p = boot_mean_ci(vec(m, pi, "tail_trade"), rng)
            row["tail_trade_rate"] = {"mean": mu, "lo": lo, "hi": hi, "n": int(vec(m, pi, "tail_trade").sum())}
            row["identifiable"] = bool(mu > HOLLOW)
            curves.append(row)
    cv = {(r["pi"], r["method"]): r for r in curves}

    # pairwise Holm per (pi, metric) for E and Q
    pairs_tab = []
    for pi in pis:
        for k in ("E", "Q"):
            res = []
            for a, b in combinations(methods, 2):
                mu, lo, hi, p = boot_mean_ci(vec(a, pi, k) - vec(b, pi, k), rng)
                res.append({"pi": pi, "metric": k, "pair": f"{a} - {b}", "a": a, "b": b,
                            "diff": mu, "lo": lo, "hi": hi, "p": p})
            for r, pa in zip(res, holm([r["p"] for r in res])):
                r["p_holm"] = pa
            pairs_tab.extend(res)

    # bandit degradation vs pi=1, Holm over pi
    degr = []
    for m in BANDITS:
        if m not in methods:
            continue
        for k in ("E", "Q"):
            fam = []
            for pi in pis:
                if pi == 1.0:
                    continue
                mu, lo, hi, p = boot_mean_ci(vec(m, pi, k) - vec(m, 1.0, k), rng)
                fam.append({"pi": pi, "method": m, "metric": k, "diff_vs_pi1": mu, "lo": lo, "hi": hi, "p": p})
            for d, pa in zip(fam, holm([d["p"] for d in fam])):
                d["p_holm"] = pa
            degr.extend(fam)

    # appendix ΔJ = D3 J − max(StageRoute, PILOT) J
    dj, perseed = [], {s: {} for s in seeds}
    if D3 in methods and all(m in methods for m in BANDITS):
        for pi in pis:
            d = vec(D3, pi, "J") - np.maximum(vec("stageroute", pi, "J"), vec("pilot", pi, "J"))
            mu, lo, hi, p = boot_mean_ci(d, rng)
            mu_m = float(vec(D3, pi, "J").mean() - max(vec("stageroute", pi, "J").mean(), vec("pilot", pi, "J").mean()))
            dj.append({"pi": pi, "dJ_mean": mu, "lo": lo, "hi": hi, "p": p, "dJ_of_means": mu_m,
                       "n_seeds_positive": int((d > 0).sum())})
            for s, v in zip(seeds, d):
                perseed[s][pi] = float(v)
        grid_desc = sorted(pis, reverse=True)
        cross = []
        for s in seeds:
            v = [perseed[s][p] for p in grid_desc]
            first = None
            for i in range(1, len(grid_desc)):
                if v[i - 1] < 0 <= v[i]:
                    first = [grid_desc[i], grid_desc[i - 1]]
                    break
            signs = [1 if x >= 0 else -1 for x in v]
            nflip = sum(1 for i in range(1, len(signs)) if signs[i] != signs[i - 1])
            cross.append({"seed": s, "first_crossover_interval": first, "n_sign_changes": nflip,
                          "always_nonneg": all(x >= 0 for x in v), "always_neg": all(x < 0 for x in v)})
        at = {r["pi"]: r for r in dj}
        keep = (0.12 in at and 0.10 in at and at[0.12]["hi"] < 0 and at[0.10]["lo"] > 0)
        rule = {
            "rule": "keep (0.10,0.12) iff 95% CI of paired ΔJ=J_D3-max(J_SR,J_PILOT) at π=0.12 entirely <0 AND at π=0.10 entirely >0",
            "dJ_0.12": at.get(0.12), "dJ_0.10": at.get(0.10), "keep_interval": bool(keep),
            "outcome": "keep (0.10, 0.12)" if keep else "conditional interval + per-seed distribution",
        }
    else:
        cross, rule = [], {"outcome": "skipped (missing D3 or bandits)"}

    # Q-gate vs peer learner directory
    gate = None
    if peer:
        pmeta = json.load(open(os.path.join(peer, "run_meta.json")))
        prows = load_csv(os.path.join(peer, "per_seed.csv"))
        def pvec(method, pi, key):
            v = {r["seed"]: r[key] for r in prows if r["method"] == method and r["pi"] == pi}
            return np.array([v[s] for s in seeds], float)
        pcurves = []
        prng = np.random.default_rng(RNG_SEED)
        for pi in pis:
            for m in methods:
                row = {"pi": pi, "method": m}
                for k in ("E", "Q"):
                    mu, lo, hi, p = boot_mean_ci(pvec(m, pi, k), prng)
                    row[k] = {"mean": mu, "lo": lo, "hi": hi}
                mu, lo, hi, p = boot_mean_ci(pvec(m, pi, "tail_trade"), prng)
                row["tail_trade_rate"] = {"mean": mu}
                row["identifiable"] = bool(mu > HOLLOW)
                pcurves.append(row)
        pcv = {(r["pi"], r["method"]): r for r in pcurves}
        per_pi = []
        all_ok = True
        for pi in pis:
            id_main = [m for m in methods if cv[(pi, m)]["identifiable"]]
            id_peer = [m for m in methods if pcv[(pi, m)]["identifiable"]]
            common = [m for m in methods if m in id_main and m in id_peer]
            # ranks by mean Q (lower = better = rank 0)
            def ranks(src, ms):
                qs = {m: src[(pi, m)]["Q"]["mean"] for m in ms}
                ordered = sorted(ms, key=lambda m: qs[m])
                return {m: i for i, m in enumerate(ordered)}, qs
            rm, qm = ranks(cv, common)
            rp, qp = ranks(pcv, common)
            tau_a, C, D, T = kendall_tau(rm, rp)
            fm = pareto_front({m: (cv[(pi, m)]["E"]["mean"], cv[(pi, m)]["Q"]["mean"]) for m in common})
            fp_ = pareto_front({m: (pcv[(pi, m)]["E"]["mean"], pcv[(pi, m)]["Q"]["mean"]) for m in common})
            tau_ok = (tau_a >= 0.6) if not np.isnan(tau_a) else False
            front_ok = fm == fp_
            ok = bool(tau_ok and front_ok)
            if not ok:
                all_ok = False
            per_pi.append({
                "pi": pi, "n_identifiable_main": len(id_main), "n_identifiable_peer": len(id_peer),
                "n_common": len(common), "common": common,
                "kendall_tau_a": tau_a, "concordant_pairs": C, "discordant_pairs": D, "tied_pairs": T,
                "tau_ge_0.6": tau_ok, "front_main": sorted(fm), "front_peer": sorted(fp_),
                "front_unchanged": front_ok, "pass": ok,
            })
        gate = {
            "main_learner": meta.get("learner"),
            "peer_learner": pmeta.get("learner"),
            "identifiability_rule": f"tail_trade_rate > {HOLLOW}",
            "rule": "pass iff at every π, Kendall τ_a of Q ranks (identifiable methods under both learners) ≥ 0.6 AND (E,Q) Pareto front among those methods is unchanged",
            "pass_all_pi": all_ok,
            "outcome": "Q promoted to main column" if all_ok else "Q stays a secondary column; report E as the main column",
            "per_pi": per_pi,
        }

    out = {
        "label": "40-seller",
        "protocol": "docs/PROTOCOL_v1.0.md",
        "config": meta.get("config"),
        "scale_yaml_sha256": SCALE_SHA256,
        "learner": meta.get("learner"),
        "seeds": seeds,
        "pi_grid": pis,
        "methods": methods,
        "n_tasks": meta.get("n_tasks"),
        "n_rounds": meta.get("n_rounds"),
        "compliance_filter": meta.get("compliance_filter"),
        "resample_roster": meta.get("resample_roster"),
        "bootstrap": {"B": B, "ci": 0.95, "paired": "same-seed", "seed_rng": RNG_SEED},
        "hollow_rule": f"Q drawn hollow / not identifiable when tail_trade_rate <= {HOLLOW}",
        "curves": curves,
        "pairwise_holm": pairs_tab,
        "bandit_degradation_vs_pi1": degr,
        "appendix_dJ": dj,
        "per_seed_crossover": cross,
        "pi_star_rule": rule,
        "q_gate": gate,
        "run_meta": meta,
    }
    json.dump(out, open(os.path.join(outdir, "inference.json"), "w"), indent=2)

    # ---------- figures
    def plot_metric(key, ylab, fn, zoom=False):
        fig, ax = plt.subplots(figsize=(7.2, 4.6))
        xs = [p for p in pis if (p > 0 if zoom else True)]
        for m in methods:
            st = STY[m]
            ys = [cv[(p, m)][key]["mean"] for p in xs]
            lo = [cv[(p, m)][key]["lo"] for p in xs]
            hi = [cv[(p, m)][key]["hi"] for p in xs]
            ax.plot(xs, ys, st["fmt"], color=st["color"], label=SHORT[m], ms=4, lw=1.2)
            ax.fill_between(xs, lo, hi, color=st["color"], alpha=0.12)
            if key == "Q":
                for p in xs:
                    r = cv[(p, m)]
                    if not r["identifiable"]:
                        ax.plot([p], [r["Q"]["mean"]], "o", ms=7, mfc="white", mec=st["color"], zorder=5)
        if key == "Q":
            ax.text(0.02, 0.02, "hollow: tail-trade rate ≤ 50% — Q not identifiable",
                    transform=ax.transAxes, fontsize=7, va="bottom")
        if zoom:
            ax.set_xscale("log")
            ax.set_xlabel("π (log, π>0)")
        else:
            ax.set_xscale("symlog", linthresh=0.08)
            ax.set_xticks([0, 0.1, 0.2, 0.3, 0.5, 1.0])
            ax.set_xticklabels(["0", ".1", ".2", ".3", ".5", "1"])
            ax.set_xlabel("π (label reveal probability)")
        ax.set_ylabel(ylab)
        learner = meta.get("learner")
        ax.set_title(f"{title_prefix}, 20 seeds, {learner}, 95% CI", fontsize=9)
        ax.legend(fontsize=6.5, ncol=3, loc="best")
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(outdir, fn), dpi=160)
        plt.close(fig)

    plot_metric("E", "E = fraud_share (per trade, lower better)", "E_vs_pi.png")
    plot_metric("E", "E = fraud_share (per trade, lower better)", "E_vs_pi_zoom.png", zoom=True)
    plot_metric("E_tok", "E_tok (billed-token weighted)", "Etok_vs_pi.png")
    plot_metric("Q", "Q (unweighted mean of attack-mode q; lower better)", "Q_vs_pi.png")

    # (E,Q) at π=1 and 0.10, no front-membership claim
    fig, axs = plt.subplots(1, 2, figsize=(9.2, 4.4))
    for ax, pi in zip(axs, (1.0, 0.10)):
        for m in methods:
            r = cv[(pi, m)]
            e, q = r["E"], r["Q"]
            hollow = not r["identifiable"]
            col = STY[m]["color"]
            ax.errorbar(e["mean"], q["mean"],
                        xerr=[[e["mean"] - e["lo"]], [e["hi"] - e["mean"]]],
                        yerr=[[q["mean"] - q["lo"]], [q["hi"] - q["mean"]]],
                        fmt="o", color=col, ms=6, mfc="white" if hollow else col, mec=col, capsize=2,
                        label=f"{SHORT[m]} ({r['tail_trade_rate']['mean']:.0%})")
        ax.set_xlabel("E (lower better)")
        ax.set_ylabel("Q (lower better)")
        ax.set_title(f"(E, Q) at π={pi}", fontsize=9)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=5.5, loc="best")
    fig.suptitle(f"{title_prefix}, 20 seeds, 95% CI — hollow: Q not identifiable; front membership not concluded", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "EQ_scatter.png"), dpi=160)
    plt.close(fig)

    # ---------- markdown
    L = []
    L.append(f"# {title_prefix} — PROTOCOL v1.0, 20 seeds")
    L.append("")
    L.append(f"- Config: `{meta.get('config')}` (frozen copy `configs/v1.0/frozen/scale.yaml`, sha256 `{SCALE_SHA256}`).")
    L.append(f"- Roster: 40 sellers (31 honest + 9 strategic: 3 swap / 3 theft / 3 downgrade), fixed roster (not resampled), `n_tasks=480`, `n_rounds=48`, `reputation_rounds=0`.")
    L.append(f"- Seller learner (this table): `{meta.get('learner')}`. Compliance filter: {meta.get('compliance_filter')}.")
    L.append("- E = attacked trades / served trades (swap, theft, or downgrade). E_tok = billed-token-weighted share (secondary column).")
    L.append("- Q = unweighted mean of the q the strategic seller played, over tail rounds the seller is listed; main Q is the simple average of Q_swap, Q_theft, Q_downgrade.")
    L.append(f"- Q is treated as not identifiable (hollow point) when the share of runs with a tail trade is ≤ {HOLLOW:.0%}.")
    L.append("- Stats: same-seed paired bootstrap, 10,000 resamples, 95% percentile CI. Holm correction over the 36 method pairs at each (π, metric), and over π for each bandit degradation family.")
    L.append("- Pareto / front membership is not concluded in the text; E is read on its own, and Q only at identifiable points.")
    L.append("")
    L.append("## Lead table (selected π)")
    L.append("")
    L.append("| method | π | E | E_tok | Q | Q_swap | Q_theft | Q_downgrade | tail-trade runs | Q identifiable |")
    L.append("|---|---:|---|---|---|---|---|---|---|---|")
    show_pi = [p for p in KEY_PI if p in set(pis)]
    for m in methods:
        for pi in show_pi:
            r = cv[(pi, m)]
            ident = "yes" if r["identifiable"] else "no"
            tr = r["tail_trade_rate"]
            L.append(
                f"| {SHORT[m]} | {pi:g} | {fmt_ci(r['E'])} | {fmt_ci(r['E_tok'])} | {fmt_ci(r['Q'])} | "
                f"{fmt_ci(r['Q_swap'])} | {fmt_ci(r['Q_theft'])} | {fmt_ci(r['Q_downgrade'])} | "
                f"{tr['mean']:.2f} ({tr['n']}/20) | {ident} |"
            )
    L.append("")
    L.append("## Bandit E / Q vs π=1 (paired, Holm over π)")
    L.append("")
    L.append("| method | metric | π | Δ vs π=1 [95% CI] | p_holm |")
    L.append("|---|---|---:|---|---:|")
    for d in degr:
        sig = " *" if d["p_holm"] < 0.05 else ""
        L.append(
            f"| {SHORT[d['method']]} | {d['metric']} | {d['pi']:g} | "
            f"{d['diff_vs_pi1']:+.3f} [{d['lo']:+.3f}, {d['hi']:+.3f}] | {d['p_holm']:.4f}{sig} |"
        )
    L.append("")
    L.append("## Appendix: π* (ΔJ = J_D3 − max(J_StageRoute, J_PILOT))")
    L.append("")
    L.append(f"Rule outcome: **{rule.get('outcome')}**.")
    if dj:
        L.append("")
        L.append("| π | ΔJ [95% CI] | n_seeds ΔJ>0 |")
        L.append("|---:|---|---:|")
        for r in dj:
            L.append(f"| {r['pi']:g} | {r['dJ_mean']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}] | {r['n_seeds_positive']} |")
        # crossover summary
        from collections import Counter
        buckets = Counter()
        for c in cross:
            buckets[str(c["first_crossover_interval"])] += 1
        L.append("")
        L.append("Per-seed first crossover interval (high π → low π, first sign change of ΔJ from negative to non-negative), counts out of 20:")
        L.append("")
        for k, n in buckets.most_common():
            L.append(f"- {k}: {n}")
        nflip = sum(1 for c in cross if c["n_sign_changes"] > 1)
        L.append(f"- seeds with more than one sign change (non-monotone): {nflip}")
    L.append("")
    if gate:
        L.append("## Q-promotion gate (existing learner vs fictitious play)")
        L.append("")
        L.append(f"Peer learner: `{gate['peer_learner']}`. Identifiability: {gate['identifiability_rule']}.")
        L.append(f"Outcome: **{gate['outcome']}** (all π pass: {gate['pass_all_pi']}).")
        L.append("")
        L.append("| π | n common identifiable | τ_a | τ≥0.6 | front (main) | front (FP) | front unchanged | pass |")
        L.append("|---:|---:|---:|---|---|---|---|---|")
        for r in gate["per_pi"]:
            L.append(
                f"| {r['pi']:g} | {r['n_common']} | {r['kendall_tau_a']:.3f} | "
                f"{'yes' if r['tau_ge_0.6'] else 'no'} | "
                f"{','.join(SHORT[m] for m in r['front_main'])} | "
                f"{','.join(SHORT[m] for m in r['front_peer'])} | "
                f"{'yes' if r['front_unchanged'] else 'no'} | "
                f"{'yes' if r['pass'] else 'no'} |"
            )
        L.append("")
    open(os.path.join(outdir, "inference.md"), "w").write("\n".join(L) + "\n")
    print("wrote", outdir, "learner", meta.get("learner"), "rule", rule.get("outcome"),
          "gate", None if not gate else gate["outcome"])
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--out", dest="outdir", required=True)
    ap.add_argument("--peer", default=None, help="peer learner dir for Q gate (e.g. main_fp)")
    ap.add_argument("--title", default="40-seller main table")
    args = ap.parse_args()
    analyze(args.indir, args.outdir, peer=args.peer, title_prefix=args.title)
