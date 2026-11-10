#!/usr/bin/env python3
"""Render results/v1.0 markdown + figures from the JSON written by run_v1_t2_a2.py / run_q_gate.py."""
import json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_v1_t2_a2 import OUT, D3, SR, PI_, POLICIES, PI_GRID

NAME = {D3: "D3 (fixed-rate audit reference baseline, a=0.1)", SR: "StageRoute+compliance", PI_: "PILOT+compliance"}
SHORT = {D3: "D3-ref", SR: "StageRoute", PI_: "PILOT"}
d = json.load(open(os.path.join(OUT, "T2_v01scale_20seed.json")))
a2 = json.load(open(os.path.join(OUT, "A2_compliance_control.json")))
qg = json.load(open(os.path.join(OUT, "Q_gate_v01scale.json")))
c = lambda x: f"{x['mean']:.3f} [{x['lo']:.3f}, {x['hi']:.3f}]"  # noqa: E731
cv = {(r["pi"], r["policy"]): r for r in d["curves"]}

# ---------------- figures
for key, lab, fn in (("fraud_share", "E = fraud_share (buyer exposure)", "T2_v01scale_E_vs_pi.png"),
                     ("Q", "Q (seller attack prob, last 1/4 rounds)", "T2_v01scale_Q_vs_pi.png")):
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for pol, st in ((SR, "o-"), (PI_, "s-"), (D3, "k--")):
        xs = sorted(PI_GRID)
        m = [cv[(p, pol)][key]["mean"] for p in xs]
        lo = [cv[(p, pol)][key]["lo"] for p in xs]
        hi = [cv[(p, pol)][key]["hi"] for p in xs]
        ax.plot(xs, m, st, label=SHORT[pol], ms=4, lw=1.2 if pol != D3 else 1.0)
        ax.fill_between(xs, lo, hi, alpha=0.2 if pol != D3 else 0.08)
    if key == "Q":
        for pol, mk in ((SR, "o"), (PI_, "s")):
            for p in xs:
                r = cv[(p, pol)]
                if r["tail_trade_frac"] <= 0.5:
                    ax.plot([p], [r["Q"]["mean"]], mk, ms=8, mfc="white", mec="C0" if pol == SR else "C1", zorder=5)
        ax.text(0.02, 0.02, "hollow = majority of runs have no tail trade:\nQ not identifiable as deterrence when the seller is avoided",
                transform=ax.transAxes, fontsize=7, va="bottom")
    ax.set_xscale("symlog", linthresh=0.05)
    ax.set_xticks([0, 0.05, 0.1, 0.2, 1.0]); ax.set_xticklabels(["0", ".05", ".1", ".2", "1"])
    ax.set_xlabel("π (label reveal probability)"); ax.set_ylabel(lab)
    ax.set_title(f"T2 v0.1-scale, 20 seeds, 95% bootstrap CI ({key})", fontsize=9)
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, fn), dpi=160); plt.close(fig)
# zoom of E without pi=0 PILOT blow-up
fig, ax = plt.subplots(figsize=(6.4, 4.2))
xs = [p for p in sorted(PI_GRID) if p > 0]
for pol, st in ((SR, "o-"), (PI_, "s-"), (D3, "k--")):
    ax.plot(xs, [cv[(p, pol)]["fraud_share"]["mean"] for p in xs], st, label=SHORT[pol], ms=4)
    ax.fill_between(xs, [cv[(p, pol)]["fraud_share"]["lo"] for p in xs],
                    [cv[(p, pol)]["fraud_share"]["hi"] for p in xs], alpha=0.2)
ax.set_xscale("log"); ax.set_xlabel("π (log, π>0)"); ax.set_ylabel("E = fraud_share")
ax.set_title("T2 v0.1-scale E vs π (π>0 zoom), 20 seeds, 95% CI", fontsize=9); ax.legend(fontsize=8); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "T2_v01scale_E_vs_pi_zoom.png"), dpi=160); plt.close(fig)
# Pareto (E,Q) at pi=1 and 0.1
fig, axs = plt.subplots(1, 2, figsize=(9, 4))
for ax, pi in zip(axs, (1.0, 0.1)):
    for pol, mk in ((D3, "k^"), (SR, "o"), (PI_, "s")):
        r = cv[(pi, pol)]
        e, q = r["fraud_share"], r["Q"]
        hollow = r["tail_trade_frac"] <= 0.5
        col = {D3: "k", SR: "C0", PI_: "C1"}[pol]
        ax.errorbar(e["mean"], q["mean"], xerr=[[e["mean"] - e["lo"]], [e["hi"] - e["mean"]]],
                    yerr=[[q["mean"] - q["lo"]], [q["hi"] - q["mean"]]], fmt=mk[-1], color=col, ms=8,
                    mfc="white" if hollow else col, mec=col, capsize=3,
                    label=f"{SHORT[pol]} (tail-trade runs {r['tail_trade_frac']:.0%})")
    ax.set_xlabel("E (lower better)"); ax.set_ylabel("Q (lower better)"); ax.set_title(f"(E,Q) at π={pi}", fontsize=9)
    ax.grid(alpha=0.3); ax.legend(fontsize=7, loc="center right")
    ax.text(0.02, 0.02, "hollow: most runs have no tail trade —\nQ not identifiable as deterrence when the seller is avoided",
            transform=ax.transAxes, fontsize=7, va="bottom")
fig.suptitle("v0.1 scale (3 sellers), to be replaced by the 40-seller main table — (E,Q) with 95% CI, no winner", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "T2_v01scale_pareto_EQ.png"), dpi=160); plt.close(fig)

# ---------------- T2 md
g = d["regression_gate"]; rule = d["pi_star_rule"]
L = ["# T2 sparse-label regime — v1.0 protocol, **v0.1-scale** (20 seeds)", "",
     "Scale label: **v0.1-scale** (3 sellers, 1 strategic seller `seller_sg`, 2 attack modes swap/theft, n_tasks=480, "
     "n_rounds=48, LLM cache, `configs/benchmark/production.yaml`). NOT the §2 40-seller scale — that sim is not ready yet; "
     "all numbers here must be re-run when it is.", "",
     f"Seeds 0–19; π grid {sorted(PI_GRID, reverse=True)} (frozen grid + 0.11). Policies: {', '.join(NAME[p] for p in POLICIES)}.",
     "Stats: same-seed paired bootstrap, 10,000 resamples, 95% percentile CI; Holm over the 3 policy pairs per (π, metric). "
     "Runner: `scripts/v1/run_v1_t2_a2.py` (wraps the existing simulator; no core code changed).", "",
     "## §0 Regression gate", "",
     f"Seeds 0–2 rerun with the v0.1 T2 config vs `results/benchmark/production/T2_episodes.jsonl`: {g['n_rows']} rows × 15 fields "
     f"= {g['n_fields_compared']} values, max |Δ| = {g['max_abs_diff']}, mismatches = {g['n_mismatches']} → **{'PASS' if g['pass'] else 'FAIL'}**. "
     f"The seed 0–2 rows inside the 20-seed run are also identical to frozen (`{d['seed0_2_subset_equals_frozen']}`).", "",
     "## Metric definitions used (and approximations)", "",
     "- **E** = `fraud_share` (fraudulent served tokens / served tokens).",
     "- **Q** (§1, fixed by protocol 口径补正 2026-11-10): the simulator logs the q the strategic seller *played* each round "
     "(`swap_q_history`, `theft_q_history`). Q_swap, Q_theft = **unweighted** mean over the last 12 of 48 rounds, restricted to rounds the seller is listed; "
     "**Q (main column) = simple average of Q_swap and Q_theft. No token weighting.** Recomputed from the existing raw runs (`scripts/v1/recompute_q_v1.py`); no simulation rerun.",
     "- **Tail-trade runs** = fraction of the 20 runs in which the strategic seller served ≥1 trade in those tail rounds. "
     "Without tail trades, attacking and not attacking pay the same, so q is not driven by feedback and **is not identifiable as deterrence**; "
     "such (policy, π) cells (tail-trade runs ≤ 50%) are hollow markers in the figures and their Q gets no deterrence reading.",
     "- Delisting: T2 uses `reputation_rounds=0`, so no seller is ever delisted — delisted tail rounds = 0 in all 660 runs. The exclusion rule is implemented and applies in settings with delisting.",
     "- D3's E and Q are identical across π by construction (D3 does not use outcome labels) — not a finding.", "",
     "## Headline (§4)", "",
     "**Bandits lower E by avoiding attackers; as labels get sparse, avoidance fails and E rises. When the seller is avoided and has no trades, "
     "its intent Q is not identifiable, so this setting does not support any conclusion about deterrence.**", "",
     "- E: PILOT 0.046 (π=1) → 0.123 (π=0.05) → 0.684 (π=0); StageRoute 0.014 → 0.063 → 0.083. Paired E(π)−E(1) is significant after Holm for PILOT at every π≤0.2 and for StageRoute at every π≤0.12 (not at 0.2–0.15).",
     "- Q: PILOT shows no significant change vs π=1 at any π. StageRoute's Q is significantly higher than at π=1 (Holm) at π=0.06, 0.05 and 0; "
     "at 0.06 and 0.05 only 10% of StageRoute runs have tail trades, so that change is not identifiable as a change in deterrence. At π=0 every run trades, "
     "and that cell coincides with E rising. StageRoute has tail trades in ≤15% of runs at every π>0 (hollow markers).",
     "- D3-ref E and Q are constant in π by construction (labels not used) — not a finding.", "",
     "Mean [95% CI] over 20 seeds. Table note: **v0.1 scale (3 sellers), to be replaced by the 40-seller main table.** "
     "Tail-trade runs = share of runs with ≥1 strategic-seller trade in the last quarter of rounds (≤50% → Q not identifiable).", "",
     "| π | E StageRoute | E PILOT | E D3-ref | Q StageRoute | Q PILOT | Q D3-ref | tail-trade runs SR / PILOT / D3 |",
     "|---|---|---|---|---|---|---|---|"]
for pi in sorted(PI_GRID, reverse=True):
    L.append(f"| {pi} | {c(cv[(pi, SR)]['fraud_share'])} | {c(cv[(pi, PI_)]['fraud_share'])} | {c(cv[(pi, D3)]['fraud_share'])} "
             f"| {c(cv[(pi, SR)]['Q'])} | {c(cv[(pi, PI_)]['Q'])} | {c(cv[(pi, D3)]['Q'])} "
             f"| {cv[(pi, SR)]['tail_trade_frac']:.0%} / {cv[(pi, PI_)]['tail_trade_frac']:.0%} / {cv[(pi, D3)]['tail_trade_frac']:.0%} |")
L += ["", "Figures: `T2_v01scale_E_vs_pi.png`, `T2_v01scale_E_vs_pi_zoom.png` (π>0), `T2_v01scale_Q_vs_pi.png`, `T2_v01scale_pareto_EQ.png`.", "",
      "### Q split by attack mode (mean [95% CI]; v0.1 scale (3 sellers), to be replaced by the 40-seller main table)", "", "| π | Q_swap SR | Q_theft SR | Q_swap PILOT | Q_theft PILOT | Q_swap D3 | Q_theft D3 |", "|---|---|---|---|---|---|---|"]
for pi in sorted(PI_GRID, reverse=True):
    L.append("| " + " | ".join([str(pi)] + [c(cv[(pi, p)][k]) for p in (SR, PI_, D3) for k in ("Q_swap", "Q_theft")]) + " |")
L += ["", "### Bandit degradation vs π=1 (same-seed paired E(π)−E(1); Holm over π within each bandit×metric)", "",
      "| π | ΔE StageRoute [CI] p_Holm | ΔE PILOT [CI] p_Holm | ΔQ StageRoute [CI] p_Holm | ΔQ PILOT [CI] p_Holm |", "|---|---|---|---|---|"]
dg = {(r["pi"], r["policy"], r["metric"]): r for r in d["bandit_degradation_vs_pi1"]}
f2 = lambda r: f"{r['diff_vs_pi1']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}] {r['p_holm']:.3g}"  # noqa: E731
for pi in sorted([p for p in PI_GRID if p != 1.0], reverse=True):
    L.append(f"| {pi} | {f2(dg[(pi, SR, 'fraud_share')])} | {f2(dg[(pi, PI_, 'fraud_share')])} | {f2(dg[(pi, SR, 'Q')])} | {f2(dg[(pi, PI_, 'Q')])} |")
L += ["", "### Pairwise policy differences (paired, Holm over 3 pairs per π×metric)", "",
      "| π | metric | pair | diff [95% CI] | p_Holm |", "|---|---|---|---|---|"]
for r in d["pairwise_holm"]:
    a, b = r["pair"].split(" - ")
    L.append(f"| {r['pi']} | {'E' if r['metric']=='fraud_share' else 'Q'} | {SHORT[a]} − {SHORT[b]} | {r['diff']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}] | {r['p_holm']:.3g} |")
L += ["", "## Appendix note: hedge-learner Q-ranking check (NOT the formal §1 gate)", "",
      "Per protocol 口径补正 items 3 and 5, this check does not count toward promoting Q. The formal gate runs later with EXP3 or fictitious play, "
      "per π (all π must pass), at the 40-seller scale with the full baselines. For reference only: rerunning the same grid/seeds with the seller "
      "learner set to `hedge` (`Q_gate_v01scale.json`) gives Kendall τ = 1.0 for the 3-policy Q ordering at all 11 π and the same (E,Q) front "
      "{D3-ref, StageRoute}. With 3 policies τ≥0.6 just means identical order, and StageRoute's Q is mostly non-identifiable (see tail-trade column).", "",
      "| π | τ | front (egreedy) | front (hedge) | Q hedge SR / PILOT / D3 |", "|---|---|---|---|---|"]
for o in qg["per_pi"]:
    L.append(f"| {o['pi']} | {o['kendall_tau']:.2f} | {', '.join(SHORT[p] for p in o['front_egreedy'])} | {', '.join(SHORT[p] for p in o['front_hedge'])} "
             f"| {o['Q_hedge'][SR]:.3f} / {o['Q_hedge'][PI_]:.3f} / {o['Q_hedge'][D3]:.3f} |")
L += ["",
      "## Appendix (§4): paired ΔJ and π* rule", "",
      "ΔJ = J(D3-ref) − max(J StageRoute, J PILOT), best bandit taken **per seed** (same definition as `T2_per_seed_seed0-2.md`), paired over seeds. "
      "`ΔJ of means` = the frozen-paper definition (difference of seed means), shown for reference only.", "",
      "| π | mean ΔJ [95% CI] | seeds with ΔJ>0 (of 20) | ΔJ of means |", "|---|---|---|---|"]
for r in d["appendix_dJ"]:
    L.append(f"| {r['pi']} | {r['dJ_mean']:+.4f} [{r['lo']:+.4f}, {r['hi']:+.4f}] | {r['n_seeds_positive']} | {r['dJ_of_means']:+.4f} |")
L += ["", "### Pre-registered rule (applied as written, not changed after results)", "",
      f"Rule: {rule['rule']}.", "",
      f"- π=0.12: ΔJ = {rule['dJ_0.12']['dJ_mean']:+.4f} [{rule['dJ_0.12']['lo']:+.4f}, {rule['dJ_0.12']['hi']:+.4f}] → entirely <0: **{rule['dJ_0.12']['hi'] < 0}**",
      f"- π=0.10: ΔJ = {rule['dJ_0.10']['dJ_mean']:+.4f} [{rule['dJ_0.10']['lo']:+.4f}, {rule['dJ_0.10']['hi']:+.4f}] → entirely >0: **{rule['dJ_0.10']['lo'] > 0}**",
      f"- **Outcome: (0.10, 0.12) is NOT kept → report as conditional interval + per-seed distribution.**", "",
      "Sensitivity (reported, does not alter the rule outcome): pairing D3 against each bandit separately, no CI at 0.12 is entirely <0 "
      "and none at 0.10 is entirely >0 either (D3−SR at 0.10: −0.006 [−0.031, +0.021]; D3−PILOT at 0.10: +0.018 [−0.006, +0.042]). "
      "With the per-seed-best definition the paired ΔJ CI excludes 0 on the negative side for all π ≥ 0.10, includes 0 at 0.08/0.06/0.05, and is >0 only at π=0.", "",
      "### Per-seed crossover distribution", "",
      "First sign flip of ΔJ scanning π downward (ΔJ<0 at the higher π, ≥0 at the lower π); `flips` = number of sign changes on the grid (>1 = non-monotone).", "",
      "| seed | crossover interval | flips |", "|---|---|---|"]
from collections import Counter
cnt = Counter()
for r in d["per_seed_crossover"]:
    iv = r["first_crossover_interval"]
    key = "none" if iv is None else f"({iv[0]}, {iv[1]})"
    cnt[key] += 1
    L.append(f"| {r['seed']} | {key} | {r['n_sign_changes']} |")
L += ["", "Distribution: " + "; ".join(f"{k}: {v}" for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])) + ".",
      f"Seeds whose crossover lies in (0.10, 0.12) or its 0.11 split: {sum(1 for r in d['per_seed_crossover'] if r['first_crossover_interval'] and 0.10 <= r['first_crossover_interval'][0] < 0.12)} of 20.", ""]
open(os.path.join(OUT, "T2_v01scale_20seed.md"), "w").write("\n".join(L))

# ---------------- A2 md
A = ["# A2 compliance — filter OFF control (§6), **v0.1-scale**", "",
     "Setting: T2 v0.1 config at π=1.0 (immediate feedback), seeds 0–19, n_tasks=480. Filter ON = `*_compliant` policies "
     "(hard pre-filter + gateway `enforce`). Filter OFF = the same router without the filter (`stageroute`, `pilot`, "
     "`compliance_unaware_cheapest`), gateway in `audit_only` mode: violating flows go through and are counted. These policy ids "
     "already exist in `portfolio.py`; no core code changed. Runner: `scripts/v1/run_v1_t2_a2.py`.", "",
     "Columns: violation rate = served purchases breaching a rule / tasks; fill rate = tasks with ≥1 served purchase / tasks; "
     "blocked/filtered per task = (candidates removed by the hard filter + gateway blocks) / tasks. Mean [95% bootstrap CI] over 20 seeds.", "",
     "| policy | filter | violation rate | fill rate | blocked/filtered per task | accuracy | E (fraud_share) | J |", "|---|---|---|---|---|---|---|---|"]
for r in a2["summary"]:
    A.append(f"| {r['policy']} | {r['filter']} | {c(r['violation_rate'])} | {c(r['fill_rate'])} | {c(r['blocked_or_filtered_per_task'])} "
             f"| {c(r['task_accuracy'])} | {c(r['fraud_share'])} | {c(r['J'])} |")
A += ["", "Paired OFF − ON (same seed):", "", "| pair | metric | diff [95% CI] |", "|---|---|---|"]
for r in a2["paired_off_minus_on"]:
    A.append(f"| {r['off']} − {r['on']} | {r['metric']} | {r['diff_off_minus_on']:+.4f} [{r['lo']:+.4f}, {r['hi']:+.4f}] |")
A += ["", "Reading (plain): with the filter on, violations are 0 in all runs; removing it from the same router yields violation rates of "
      "≈0.13 (StageRoute, PILOT) and ≈0.22 (cheapest), with fill rate essentially unchanged (≤0.8 pp drop for StageRoute OFF, CI touches 0). "
      "So the zero in the ON rows is produced by the filter, not by an absence of violating buyer–seller pairs in this market. "
      "Violations by rule are in `A2_compliance_control.json` / `raw/A2_episodes.jsonl` (mainly SG-PDPA-26 and BR-LGPD-33-VIII).", "",
      "**Not covered:** D3 (`audited_compliance_cascade`) has no filter-OFF variant — `is_hard()` keys on the policy id, and there is no "
      "non-hard audited policy id. Minimal change needed (not made): add an `audited_cascade` id to `BASELINE_POLICIES` in "
      "`tokenmarket/portfolio.py` and to `AUDITED_POLICIES`, dispatched to the same code path as `audited_compliance_cascade` "
      "(≈3 lines, Coding's area). D3 ON row is reported for reference.",
      "", "Caveat: v0.1-scale has 3 sellers / 6 buyers and a basic rule set; violation rates will change at §2 scale."]
open(os.path.join(OUT, "A2_compliance_control.md"), "w").write("\n".join(A))
print("ok")
