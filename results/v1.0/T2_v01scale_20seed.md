# T2 sparse-label regime — v1.0 protocol, **v0.1-scale** (20 seeds)

Scale label: **v0.1-scale** (3 sellers, 1 strategic seller `seller_sg`, 2 attack modes swap/theft, n_tasks=480, n_rounds=48, LLM cache, `configs/benchmark/production.yaml`). NOT the §2 40-seller scale — that sim is not ready yet; all numbers here must be re-run when it is.

Seeds 0–19; π grid [1.0, 0.2, 0.18, 0.15, 0.12, 0.11, 0.1, 0.08, 0.06, 0.05, 0.0] (frozen grid + 0.11). Policies: D3 (fixed-rate audit reference baseline, a=0.1), StageRoute+compliance, PILOT+compliance.
Stats: same-seed paired bootstrap, 10,000 resamples, 95% percentile CI; Holm over the 3 policy pairs per (π, metric). Runner: `scripts/v1/run_v1_t2_a2.py` (wraps the existing simulator; no core code changed).

## §0 Regression gate

Seeds 0–2 rerun with the v0.1 T2 config vs `results/benchmark/production/T2_episodes.jsonl`: 90 rows × 15 fields = 1350 values, max |Δ| = 0.0, mismatches = 0 → **PASS**. The seed 0–2 rows inside the 20-seed run are also identical to frozen (`True`).

## Metric definitions used (and approximations)

- **E** = `fraud_share` (attacked trades / served trades, counted per trade, swap or theft; matches `tokenmarket/metrics.py`). A billed-token-weighted E_tok will be added as a secondary column.
- **Q** (§1, fixed by protocol 口径补正 2026-11-10): the simulator logs the q the strategic seller *played* each round (`swap_q_history`, `theft_q_history`). Q_swap, Q_theft = **unweighted** mean over the last 12 of 48 rounds, restricted to rounds the seller is listed; **Q (main column) = simple average of Q_swap and Q_theft. No token weighting.** Recomputed from the existing raw runs (`scripts/v1/recompute_q_v1.py`); no simulation rerun.
- **Tail-trade runs** = fraction of the 20 runs in which the strategic seller served ≥1 trade in those tail rounds. Without tail trades, attacking and not attacking pay the same, so q is not driven by feedback and **is not identifiable as deterrence**; such (policy, π) cells (tail-trade runs ≤ 50%) are hollow markers in the figures and their Q gets no deterrence reading.
- Delisting: T2 uses `reputation_rounds=0`, so no seller is ever delisted — delisted tail rounds = 0 in all 660 runs. The exclusion rule is implemented and applies in settings with delisting.
- D3's E and Q are identical across π by construction (D3 does not use outcome labels) — not a finding.

## Headline (§4)

**Bandits lower E by avoiding attackers; as labels get sparse, avoidance fails and E rises. When the seller is avoided and has no trades, its intent Q is not identifiable, so this setting does not support any conclusion about deterrence.**

- E: PILOT 0.046 (π=1) → 0.123 (π=0.05) → 0.684 (π=0); StageRoute 0.014 → 0.063 → 0.083. Paired E(π)−E(1) is significant after Holm for PILOT at every π≤0.2 and for StageRoute at every π≤0.12 (not at 0.2–0.15).
- Q: PILOT shows no significant change vs π=1 at any π. StageRoute's Q is significantly higher than at π=1 (Holm) at π=0.06, 0.05 and 0; at 0.06 and 0.05 only 10% of StageRoute runs have tail trades, so that change is not identifiable as a change in deterrence. At π=0 every run trades, and that cell coincides with E rising. StageRoute has tail trades in ≤15% of runs at every π>0 (hollow markers).
- D3-ref E and Q are constant in π by construction (labels not used) — not a finding.

Mean [95% CI] over 20 seeds. Table note: **v0.1 scale (3 sellers), to be replaced by the 40-seller main table.** Tail-trade runs = share of runs with ≥1 strategic-seller trade in the last quarter of rounds (≤50% → Q not identifiable).

| π | E StageRoute | E PILOT | E D3-ref | Q StageRoute | Q PILOT | Q D3-ref | tail-trade runs SR / PILOT / D3 |
|---|---|---|---|---|---|---|---|
| 1.0 | 0.014 [0.008, 0.020] | 0.046 [0.038, 0.054] | 0.106 [0.085, 0.131] | 0.689 [0.602, 0.783] | 0.913 [0.860, 0.953] | 0.118 [0.061, 0.187] | 10% / 75% / 100% |
| 0.2 | 0.030 [0.014, 0.049] | 0.072 [0.063, 0.082] | 0.106 [0.085, 0.131] | 0.671 [0.584, 0.767] | 0.912 [0.857, 0.951] | 0.118 [0.059, 0.187] | 0% / 85% / 100% |
| 0.18 | 0.026 [0.012, 0.044] | 0.090 [0.078, 0.102] | 0.106 [0.086, 0.130] | 0.698 [0.604, 0.795] | 0.911 [0.854, 0.953] | 0.118 [0.060, 0.188] | 0% / 95% / 100% |
| 0.15 | 0.024 [0.012, 0.038] | 0.083 [0.069, 0.099] | 0.106 [0.086, 0.131] | 0.677 [0.592, 0.767] | 0.929 [0.902, 0.954] | 0.118 [0.060, 0.189] | 10% / 100% / 100% |
| 0.12 | 0.036 [0.017, 0.061] | 0.087 [0.072, 0.102] | 0.106 [0.086, 0.131] | 0.746 [0.654, 0.839] | 0.901 [0.839, 0.950] | 0.118 [0.060, 0.188] | 10% / 85% / 100% |
| 0.11 | 0.042 [0.022, 0.067] | 0.087 [0.073, 0.102] | 0.106 [0.085, 0.131] | 0.791 [0.696, 0.884] | 0.881 [0.810, 0.941] | 0.118 [0.059, 0.187] | 5% / 100% / 100% |
| 0.1 | 0.047 [0.030, 0.066] | 0.092 [0.077, 0.106] | 0.106 [0.086, 0.131] | 0.822 [0.726, 0.910] | 0.904 [0.851, 0.947] | 0.118 [0.059, 0.188] | 15% / 95% / 100% |
| 0.08 | 0.041 [0.024, 0.064] | 0.107 [0.089, 0.127] | 0.106 [0.086, 0.130] | 0.805 [0.709, 0.897] | 0.914 [0.856, 0.954] | 0.118 [0.059, 0.188] | 10% / 100% / 100% |
| 0.06 | 0.053 [0.032, 0.077] | 0.118 [0.100, 0.135] | 0.106 [0.086, 0.130] | 0.840 [0.748, 0.923] | 0.911 [0.861, 0.953] | 0.118 [0.059, 0.188] | 10% / 95% / 100% |
| 0.05 | 0.063 [0.035, 0.094] | 0.123 [0.103, 0.144] | 0.106 [0.085, 0.131] | 0.860 [0.775, 0.933] | 0.904 [0.843, 0.951] | 0.118 [0.060, 0.187] | 10% / 95% / 100% |
| 0.0 | 0.083 [0.076, 0.089] | 0.684 [0.675, 0.694] | 0.106 [0.086, 0.130] | 0.934 [0.912, 0.955] | 0.937 [0.912, 0.960] | 0.118 [0.059, 0.188] | 100% / 100% / 100% |

Figures: `T2_v01scale_E_vs_pi.png`, `T2_v01scale_E_vs_pi_zoom.png` (π>0), `T2_v01scale_Q_vs_pi.png`, `T2_v01scale_pareto_EQ.png`.

### Q split by attack mode (mean [95% CI]; v0.1 scale (3 sellers), to be replaced by the 40-seller main table)

| π | Q_swap SR | Q_theft SR | Q_swap PILOT | Q_theft PILOT | Q_swap D3 | Q_theft D3 |
|---|---|---|---|---|---|---|
| 1.0 | 0.695 [0.601, 0.794] | 0.683 [0.595, 0.774] | 0.944 [0.914, 0.970] | 0.883 [0.781, 0.947] | 0.167 [0.073, 0.282] | 0.068 [0.037, 0.103] |
| 0.2 | 0.699 [0.613, 0.789] | 0.644 [0.547, 0.745] | 0.915 [0.848, 0.959] | 0.908 [0.860, 0.945] | 0.167 [0.075, 0.280] | 0.068 [0.038, 0.102] |
| 0.18 | 0.718 [0.628, 0.813] | 0.679 [0.580, 0.778] | 0.917 [0.851, 0.963] | 0.905 [0.854, 0.947] | 0.167 [0.076, 0.280] | 0.068 [0.037, 0.102] |
| 0.15 | 0.689 [0.603, 0.780] | 0.664 [0.575, 0.759] | 0.942 [0.919, 0.964] | 0.915 [0.881, 0.947] | 0.167 [0.075, 0.284] | 0.068 [0.037, 0.102] |
| 0.12 | 0.795 [0.700, 0.885] | 0.697 [0.562, 0.821] | 0.946 [0.923, 0.968] | 0.856 [0.740, 0.941] | 0.167 [0.075, 0.280] | 0.068 [0.037, 0.103] |
| 0.11 | 0.835 [0.741, 0.919] | 0.747 [0.608, 0.868] | 0.926 [0.880, 0.962] | 0.836 [0.720, 0.932] | 0.167 [0.075, 0.283] | 0.068 [0.037, 0.101] |
| 0.1 | 0.864 [0.771, 0.942] | 0.781 [0.640, 0.900] | 0.934 [0.900, 0.963] | 0.873 [0.788, 0.937] | 0.167 [0.074, 0.280] | 0.068 [0.037, 0.103] |
| 0.08 | 0.848 [0.752, 0.932] | 0.763 [0.622, 0.882] | 0.946 [0.923, 0.968] | 0.883 [0.784, 0.948] | 0.167 [0.075, 0.283] | 0.068 [0.038, 0.102] |
| 0.06 | 0.860 [0.767, 0.941] | 0.820 [0.703, 0.913] | 0.946 [0.923, 0.968] | 0.875 [0.786, 0.944] | 0.167 [0.076, 0.283] | 0.068 [0.038, 0.102] |
| 0.05 | 0.860 [0.766, 0.941] | 0.859 [0.782, 0.926] | 0.946 [0.923, 0.969] | 0.863 [0.752, 0.945] | 0.167 [0.074, 0.281] | 0.068 [0.037, 0.102] |
| 0.0 | 0.946 [0.922, 0.969] | 0.922 [0.895, 0.948] | 0.951 [0.930, 0.971] | 0.922 [0.890, 0.952] | 0.167 [0.075, 0.280] | 0.068 [0.037, 0.102] |

### Bandit degradation vs π=1 (same-seed paired E(π)−E(1); Holm over π within each bandit×metric)

| π | ΔE StageRoute [CI] p_Holm | ΔE PILOT [CI] p_Holm | ΔQ StageRoute [CI] p_Holm | ΔQ PILOT [CI] p_Holm |
|---|---|---|---|---|
| 0.2 | +0.016 [+0.002, +0.032] 0.0528 | +0.026 [+0.016, +0.037] 0 | -0.018 [-0.112, +0.073] 1 | -0.002 [-0.057, +0.064] 1 |
| 0.18 | +0.013 [+0.001, +0.028] 0.0532 | +0.044 [+0.031, +0.057] 0 | +0.009 [-0.067, +0.086] 1 | -0.002 [-0.059, +0.063] 1 |
| 0.15 | +0.010 [-0.001, +0.025] 0.0934 | +0.037 [+0.022, +0.053] 0 | -0.013 [-0.090, +0.073] 1 | +0.015 [-0.021, +0.069] 1 |
| 0.12 | +0.023 [+0.004, +0.047] 0.0192 | +0.041 [+0.025, +0.057] 0 | +0.057 [-0.023, +0.147] 0.727 | -0.012 [-0.079, +0.057] 1 |
| 0.11 | +0.028 [+0.009, +0.053] 0.0012 | +0.041 [+0.026, +0.055] 0 | +0.102 [+0.005, +0.205] 0.179 | -0.032 [-0.112, +0.048] 1 |
| 0.1 | +0.034 [+0.016, +0.052] 0 | +0.046 [+0.031, +0.060] 0 | +0.133 [+0.034, +0.235] 0.0588 | -0.010 [-0.068, +0.056] 1 |
| 0.08 | +0.028 [+0.009, +0.050] 0.002 | +0.061 [+0.042, +0.082] 0 | +0.116 [+0.020, +0.218] 0.104 | +0.001 [-0.058, +0.064] 1 |
| 0.06 | +0.039 [+0.018, +0.066] 0 | +0.072 [+0.052, +0.090] 0 | +0.151 [+0.065, +0.244] 0 | -0.003 [-0.062, +0.063] 1 |
| 0.05 | +0.049 [+0.020, +0.082] 0 | +0.077 [+0.056, +0.099] 0 | +0.170 [+0.085, +0.257] 0 | -0.009 [-0.080, +0.060] 1 |
| 0.0 | +0.069 [+0.060, +0.079] 0 | +0.638 [+0.626, +0.650] 0 | +0.245 [+0.157, +0.331] 0 | +0.023 [-0.018, +0.082] 1 |

### Pairwise policy differences (paired, Holm over 3 pairs per π×metric)

| π | metric | pair | diff [95% CI] | p_Holm |
|---|---|---|---|---|
| 1.0 | E | D3-ref − StageRoute | +0.092 [+0.069, +0.119] | 0 |
| 1.0 | E | D3-ref − PILOT | +0.060 [+0.038, +0.084] | 0 |
| 1.0 | E | StageRoute − PILOT | -0.032 [-0.041, -0.023] | 0 |
| 1.0 | Q | D3-ref − StageRoute | -0.571 [-0.693, -0.447] | 0 |
| 1.0 | Q | D3-ref − PILOT | -0.796 [-0.872, -0.713] | 0 |
| 1.0 | Q | StageRoute − PILOT | -0.224 [-0.308, -0.138] | 0 |
| 0.2 | E | D3-ref − StageRoute | +0.076 [+0.044, +0.110] | 0 |
| 0.2 | E | D3-ref − PILOT | +0.034 [+0.012, +0.057] | 0.0004 |
| 0.2 | E | StageRoute − PILOT | -0.043 [-0.061, -0.021] | 0.0004 |
| 0.2 | Q | D3-ref − StageRoute | -0.554 [-0.677, -0.431] | 0 |
| 0.2 | Q | D3-ref − PILOT | -0.794 [-0.880, -0.700] | 0 |
| 0.2 | Q | StageRoute − PILOT | -0.240 [-0.339, -0.135] | 0 |
| 0.18 | E | D3-ref − StageRoute | +0.080 [+0.048, +0.112] | 0 |
| 0.18 | E | D3-ref − PILOT | +0.016 [-0.004, +0.036] | 0.118 |
| 0.18 | E | StageRoute − PILOT | -0.064 [-0.083, -0.042] | 0 |
| 0.18 | Q | D3-ref − StageRoute | -0.581 [-0.711, -0.445] | 0 |
| 0.18 | Q | D3-ref − PILOT | -0.794 [-0.882, -0.698] | 0 |
| 0.18 | Q | StageRoute − PILOT | -0.213 [-0.314, -0.107] | 0 |
| 0.15 | E | D3-ref − StageRoute | +0.082 [+0.060, +0.106] | 0 |
| 0.15 | E | D3-ref − PILOT | +0.023 [-0.003, +0.051] | 0.0818 |
| 0.15 | E | StageRoute − PILOT | -0.059 [-0.079, -0.038] | 0 |
| 0.15 | Q | D3-ref − StageRoute | -0.559 [-0.665, -0.456] | 0 |
| 0.15 | Q | D3-ref − PILOT | -0.811 [-0.886, -0.728] | 0 |
| 0.15 | Q | StageRoute − PILOT | -0.252 [-0.340, -0.160] | 0 |
| 0.12 | E | D3-ref − StageRoute | +0.070 [+0.038, +0.099] | 0 |
| 0.12 | E | D3-ref − PILOT | +0.019 [-0.006, +0.048] | 0.152 |
| 0.12 | E | StageRoute − PILOT | -0.050 [-0.074, -0.022] | 0.002 |
| 0.12 | Q | D3-ref − StageRoute | -0.628 [-0.739, -0.515] | 0 |
| 0.12 | Q | D3-ref − PILOT | -0.783 [-0.873, -0.687] | 0 |
| 0.12 | Q | StageRoute − PILOT | -0.155 [-0.248, -0.068] | 0.0002 |
| 0.11 | E | D3-ref − StageRoute | +0.064 [+0.026, +0.100] | 0.0048 |
| 0.11 | E | D3-ref − PILOT | +0.019 [-0.006, +0.046] | 0.141 |
| 0.11 | E | StageRoute − PILOT | -0.045 [-0.069, -0.018] | 0.0048 |
| 0.11 | Q | D3-ref − StageRoute | -0.673 [-0.786, -0.553] | 0 |
| 0.11 | Q | D3-ref − PILOT | -0.764 [-0.856, -0.665] | 0 |
| 0.11 | Q | StageRoute − PILOT | -0.090 [-0.206, +0.026] | 0.125 |
| 0.1 | E | D3-ref − StageRoute | +0.059 [+0.032, +0.085] | 0 |
| 0.1 | E | D3-ref − PILOT | +0.014 [-0.008, +0.039] | 0.22 |
| 0.1 | E | StageRoute − PILOT | -0.044 [-0.067, -0.018] | 0.002 |
| 0.1 | Q | D3-ref − StageRoute | -0.705 [-0.819, -0.586] | 0 |
| 0.1 | Q | D3-ref − PILOT | -0.786 [-0.866, -0.701] | 0 |
| 0.1 | Q | StageRoute − PILOT | -0.081 [-0.184, +0.020] | 0.114 |
| 0.08 | E | D3-ref − StageRoute | +0.065 [+0.032, +0.097] | 0.0004 |
| 0.08 | E | D3-ref − PILOT | -0.001 [-0.023, +0.021] | 0.888 |
| 0.08 | E | StageRoute − PILOT | -0.066 [-0.093, -0.039] | 0 |
| 0.08 | Q | D3-ref − StageRoute | -0.688 [-0.810, -0.558] | 0 |
| 0.08 | Q | D3-ref − PILOT | -0.797 [-0.878, -0.707] | 0 |
| 0.08 | Q | StageRoute − PILOT | -0.109 [-0.206, -0.008] | 0.0354 |
| 0.06 | E | D3-ref − StageRoute | +0.053 [+0.029, +0.077] | 0 |
| 0.06 | E | D3-ref − PILOT | -0.012 [-0.034, +0.013] | 0.317 |
| 0.06 | E | StageRoute − PILOT | -0.065 [-0.090, -0.037] | 0 |
| 0.06 | Q | D3-ref − StageRoute | -0.722 [-0.824, -0.616] | 0 |
| 0.06 | Q | D3-ref − PILOT | -0.793 [-0.879, -0.697] | 0 |
| 0.06 | Q | StageRoute − PILOT | -0.071 [-0.158, +0.011] | 0.089 |
| 0.05 | E | D3-ref − StageRoute | +0.043 [+0.007, +0.078] | 0.0352 |
| 0.05 | E | D3-ref − PILOT | -0.017 [-0.043, +0.010] | 0.211 |
| 0.05 | E | StageRoute − PILOT | -0.061 [-0.093, -0.027] | 0.0018 |
| 0.05 | Q | D3-ref − StageRoute | -0.742 [-0.841, -0.638] | 0 |
| 0.05 | Q | D3-ref − PILOT | -0.787 [-0.875, -0.684] | 0 |
| 0.05 | Q | StageRoute − PILOT | -0.045 [-0.139, +0.049] | 0.349 |
| 0.0 | E | D3-ref − StageRoute | +0.023 [+0.003, +0.047] | 0.0216 |
| 0.0 | E | D3-ref − PILOT | -0.578 [-0.601, -0.553] | 0 |
| 0.0 | E | StageRoute − PILOT | -0.601 [-0.611, -0.591] | 0 |
| 0.0 | Q | D3-ref − StageRoute | -0.816 [-0.888, -0.734] | 0 |
| 0.0 | Q | D3-ref − PILOT | -0.819 [-0.893, -0.734] | 0 |
| 0.0 | Q | StageRoute − PILOT | -0.002 [-0.021, +0.014] | 0.793 |

## Appendix note: hedge-learner Q-ranking check (NOT the formal §1 gate)

Per protocol 口径补正 items 3 and 5, this check does not count toward promoting Q. The formal gate runs later with EXP3 or fictitious play, per π (all π must pass), at the 40-seller scale with the full baselines. For reference only: rerunning the same grid/seeds with the seller learner set to `hedge` (`Q_gate_v01scale.json`) gives Kendall τ = 1.0 for the 3-policy Q ordering at all 11 π and the same (E,Q) front {D3-ref, StageRoute}. With 3 policies τ≥0.6 just means identical order, and StageRoute's Q is mostly non-identifiable (see tail-trade column).

| π | τ | front (egreedy) | front (hedge) | Q hedge SR / PILOT / D3 |
|---|---|---|---|---|
| 1.0 | 1.00 | D3-ref, StageRoute | D3-ref, StageRoute | 0.551 / 0.660 / 0.328 |
| 0.2 | 1.00 | D3-ref, StageRoute | D3-ref, StageRoute | 0.598 / 0.730 / 0.328 |
| 0.18 | 1.00 | D3-ref, StageRoute | D3-ref, StageRoute | 0.591 / 0.737 / 0.328 |
| 0.15 | 1.00 | D3-ref, StageRoute | D3-ref, StageRoute | 0.566 / 0.710 / 0.328 |
| 0.12 | 1.00 | D3-ref, StageRoute | D3-ref, StageRoute | 0.547 / 0.694 / 0.328 |
| 0.11 | 1.00 | D3-ref, StageRoute | D3-ref, StageRoute | 0.591 / 0.714 / 0.328 |
| 0.1 | 1.00 | D3-ref, StageRoute | D3-ref, StageRoute | 0.616 / 0.746 / 0.328 |
| 0.08 | 1.00 | D3-ref, StageRoute | D3-ref, StageRoute | 0.619 / 0.732 / 0.328 |
| 0.06 | 1.00 | D3-ref, StageRoute | D3-ref, StageRoute | 0.612 / 0.740 / 0.328 |
| 0.05 | 1.00 | D3-ref, StageRoute | D3-ref, StageRoute | 0.623 / 0.763 / 0.328 |
| 0.0 | 1.00 | D3-ref, StageRoute | D3-ref, StageRoute | 0.764 / 0.844 / 0.328 |

## Appendix (§4): paired ΔJ and π* rule

ΔJ = J(D3-ref) − max(J StageRoute, J PILOT), best bandit taken **per seed** (same definition as `T2_per_seed_seed0-2.md`), paired over seeds. `ΔJ of means` = the frozen-paper definition (difference of seed means), shown for reference only.

| π | mean ΔJ [95% CI] | seeds with ΔJ>0 (of 20) | ΔJ of means |
|---|---|---|---|
| 1.0 | -0.0671 [-0.0919, -0.0456] | 0 | -0.0663 |
| 0.2 | -0.0505 [-0.0751, -0.0279] | 2 | -0.0366 |
| 0.18 | -0.0434 [-0.0693, -0.0189] | 3 | -0.0365 |
| 0.15 | -0.0457 [-0.0696, -0.0229] | 3 | -0.0422 |
| 0.12 | -0.0363 [-0.0623, -0.0135] | 4 | -0.0205 |
| 0.11 | -0.0313 [-0.0578, -0.0076] | 6 | -0.0130 |
| 0.1 | -0.0251 [-0.0438, -0.0067] | 6 | -0.0063 |
| 0.08 | -0.0224 [-0.0479, +0.0001] | 6 | -0.0047 |
| 0.06 | +0.0055 [-0.0172, +0.0268] | 11 | +0.0263 |
| 0.05 | +0.0116 [-0.0151, +0.0370] | 13 | +0.0503 |
| 0.0 | +0.1718 [+0.1488, +0.1922] | 20 | +0.1718 |

### Pre-registered rule (applied as written, not changed after results)

Rule: keep (0.10,0.12) iff 95% CI of paired ΔJ at π=0.12 entirely <0 AND at π=0.10 entirely >0.

- π=0.12: ΔJ = -0.0363 [-0.0623, -0.0135] → entirely <0: **True**
- π=0.10: ΔJ = -0.0251 [-0.0438, -0.0067] → entirely >0: **False**
- **Outcome: (0.10, 0.12) is NOT kept → report as conditional interval + per-seed distribution.**

Sensitivity (reported, does not alter the rule outcome): pairing D3 against each bandit separately, no CI at 0.12 is entirely <0 and none at 0.10 is entirely >0 either (D3−SR at 0.10: −0.006 [−0.031, +0.021]; D3−PILOT at 0.10: +0.018 [−0.006, +0.042]). With the per-seed-best definition the paired ΔJ CI excludes 0 on the negative side for all π ≥ 0.10, includes 0 at 0.08/0.06/0.05, and is >0 only at π=0.

### Per-seed crossover distribution

First sign flip of ΔJ scanning π downward (ΔJ<0 at the higher π, ≥0 at the lower π); `flips` = number of sign changes on the grid (>1 = non-monotone).

| seed | crossover interval | flips |
|---|---|---|
| 0 | (0.06, 0.08) | 1 |
| 1 | (0.08, 0.1) | 1 |
| 2 | (0.18, 0.2) | 1 |
| 3 | (0.1, 0.11) | 3 |
| 4 | (0.0, 0.05) | 1 |
| 5 | (0.06, 0.08) | 1 |
| 6 | (0.0, 0.05) | 1 |
| 7 | (0.05, 0.06) | 1 |
| 8 | (0.15, 0.18) | 3 |
| 9 | (0.0, 0.05) | 1 |
| 10 | (0.0, 0.05) | 1 |
| 11 | (0.08, 0.1) | 1 |
| 12 | (0.0, 0.05) | 1 |
| 13 | (0.06, 0.08) | 1 |
| 14 | (0.2, 1.0) | 5 |
| 15 | (0.0, 0.05) | 1 |
| 16 | (0.06, 0.08) | 1 |
| 17 | (0.11, 0.12) | 1 |
| 18 | (0.2, 1.0) | 1 |
| 19 | (0.12, 0.15) | 1 |

Distribution: (0.0, 0.05): 6; (0.06, 0.08): 4; (0.08, 0.1): 2; (0.2, 1.0): 2; (0.18, 0.2): 1; (0.1, 0.11): 1; (0.05, 0.06): 1; (0.15, 0.18): 1; (0.11, 0.12): 1; (0.12, 0.15): 1.
Seeds whose crossover lies in (0.10, 0.12) or its 0.11 split: 2 of 20.
