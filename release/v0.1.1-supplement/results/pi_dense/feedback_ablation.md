# F — Delayed / sparse outcome feedback (v5 ablation)

**Setting.** Outcome feedback = whether a purchased answer was correct (the bandit reward). A purchase at step t (task index) has its label revealed with probability π and, if revealed, delivered to the router at step t + L (FIFO by due step, before that step's routing decision); labels still pending at the end of the episode are flushed if L is finite, never delivered if L = ∞. Only the LABEL is delayed: the realised cost is on the buyer's own bill and stays immediate (PILOT budget bins, StageRoute cost estimate).

**Audits are a separate signal.** D3's audits (rate 0.1, checks ['identity', 'length'], d_identity = 0.9, d_length = 0.9, P = 0.25) run, slash/delist the seller and update D3's TrustModel IMMEDIATELY in every regime; D3's routing never uses correctness labels, so the feedback channel only changes its logging. PILOT+compliance and StageRoute+compliance do NOT audit (audit rate 0).

Market: strategic learning seller seller_sg with attack modes ['swap', 'theft'] (same as section J), budget × 2.0, J = acc − 1.0·violation rate − 0.5·fraud share. Mean ± std over seeds [0, 1, 2]. q = seller's learned attack rate (mean over the last half of epochs). coverage = labels delivered during the episode / purchases.

Real vs simulated: the correctness labels come from the REAL cached Qwen outputs (no new generation); the feedback channel (delay L, reveal probability π, flush rule), audits, the seller's learning rule, prices and budgets are SIMULATED.

## Delay sweep (π = 1)

| L | policy | J | accuracy | violation rate | fraud share | sg q_swap / q_theft | share of purchases from sg | cost/task incl. audit | feedback coverage |
|---|---|---|---|---|---|---|---|---|---|
| 0 | PILOT+compliance | 0.789 ± 0.010 | 0.811 ± 0.007 | 0.000 | 0.045 ± 0.011 | 0.95 / 0.93 | 0.048 | 0.0231 | 1.00 |
| 0 | StageRoute+compliance | 0.811 ± 0.026 | 0.822 ± 0.015 | 0.000 | 0.023 ± 0.022 | 0.80 / 0.77 | 0.034 | 0.0230 | 1.00 |
| 0 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 1.00 |

## Sparsity sweep (L = 0)

| π | policy | J | accuracy | violation rate | fraud share | sg q_swap / q_theft | share of purchases from sg | cost/task incl. audit | feedback coverage |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PILOT+compliance | 0.789 ± 0.010 | 0.811 ± 0.007 | 0.000 | 0.045 ± 0.011 | 0.95 / 0.93 | 0.048 | 0.0231 | 1.00 |
| 1 | StageRoute+compliance | 0.811 ± 0.026 | 0.822 ± 0.015 | 0.000 | 0.023 ± 0.022 | 0.80 / 0.77 | 0.034 | 0.0230 | 1.00 |
| 1 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 1.00 |
| 0.2 | PILOT+compliance | 0.780 ± 0.015 | 0.808 ± 0.011 | 0.000 | 0.058 ± 0.008 | 0.95 / 0.94 | 0.065 | 0.0220 | 0.21 |
| 0.2 | StageRoute+compliance | 0.803 ± 0.007 | 0.812 ± 0.007 | 0.000 | 0.018 ± 0.017 | 0.64 / 0.61 | 0.021 | 0.0220 | 0.21 |
| 0.2 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.20 |
| 0.18 | PILOT+compliance | 0.763 ± 0.022 | 0.798 ± 0.016 | 0.000 | 0.069 ± 0.013 | 0.95 / 0.91 | 0.077 | 0.0228 | 0.18 |
| 0.18 | StageRoute+compliance | 0.799 ± 0.011 | 0.810 ± 0.006 | 0.000 | 0.022 ± 0.017 | 0.64 / 0.61 | 0.026 | 0.0223 | 0.18 |
| 0.18 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.18 |
| 0.15 | PILOT+compliance | 0.772 ± 0.024 | 0.801 ± 0.015 | 0.000 | 0.057 ± 0.019 | 0.95 / 0.94 | 0.062 | 0.0218 | 0.16 |
| 0.15 | StageRoute+compliance | 0.798 ± 0.012 | 0.808 ± 0.011 | 0.000 | 0.020 ± 0.019 | 0.64 / 0.61 | 0.023 | 0.0220 | 0.16 |
| 0.15 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.15 |
| 0.12 | PILOT+compliance | 0.729 ± 0.055 | 0.776 ± 0.035 | 0.000 | 0.094 ± 0.040 | 0.92 / 0.83 | 0.106 | 0.0221 | 0.13 |
| 0.12 | StageRoute+compliance | 0.789 ± 0.023 | 0.805 ± 0.015 | 0.000 | 0.032 ± 0.019 | 0.80 / 0.77 | 0.036 | 0.0224 | 0.13 |
| 0.12 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.12 |
| 0.1 | PILOT+compliance | 0.726 ± 0.064 | 0.774 ± 0.035 | 0.000 | 0.097 ± 0.058 | 0.83 / 0.78 | 0.108 | 0.0230 | 0.10 |
| 0.1 | StageRoute+compliance | 0.747 ± 0.049 | 0.780 ± 0.034 | 0.000 | 0.066 ± 0.032 | 0.95 / 0.94 | 0.075 | 0.0226 | 0.10 |
| 0.1 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.10 |
| 0.08 | PILOT+compliance | 0.699 ± 0.059 | 0.760 ± 0.033 | 0.000 | 0.123 ± 0.054 | 0.95 / 0.94 | 0.140 | 0.0224 | 0.08 |
| 0.08 | StageRoute+compliance | 0.737 ± 0.071 | 0.774 ± 0.047 | 0.000 | 0.075 ± 0.049 | 0.95 / 0.94 | 0.085 | 0.0227 | 0.08 |
| 0.08 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.08 |
| 0.06 | PILOT+compliance | 0.652 ± 0.039 | 0.731 ± 0.024 | 0.000 | 0.158 ± 0.030 | 0.95 / 0.94 | 0.174 | 0.0223 | 0.07 |
| 0.06 | StageRoute+compliance | 0.714 ± 0.035 | 0.751 ± 0.019 | 0.000 | 0.075 ± 0.038 | 0.95 / 0.94 | 0.083 | 0.0216 | 0.07 |
| 0.06 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.06 |
| 0.05 | PILOT+compliance | 0.673 ± 0.039 | 0.740 ± 0.024 | 0.000 | 0.135 ± 0.032 | 0.95 / 0.94 | 0.149 | 0.0227 | 0.06 |
| 0.05 | StageRoute+compliance | 0.681 ± 0.115 | 0.729 ± 0.064 | 0.000 | 0.097 ± 0.106 | 0.95 / 0.94 | 0.107 | 0.0217 | 0.05 |
| 0.05 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.05 |
| 0 | PILOT+compliance | -0.030 ± 0.063 | 0.309 ± 0.046 | 0.000 | 0.678 ± 0.035 | 0.95 / 0.94 | 0.707 | 0.0233 | 0.00 |
| 0 | StageRoute+compliance | 0.585 ± 0.021 | 0.623 ± 0.019 | 0.000 | 0.075 ± 0.010 | 0.95 / 0.94 | 0.083 | 0.0116 | 0.00 |
| 0 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.00 |

## D3 advantage over the best compliant bandit

ΔJ = J(D3) − max J(bandits); Δfraud = min fraud share(bandits) − fraud share(D3); Δq = min learned q over bandits − D3's (positive = D3 better).

| (L, π) | best bandit | ΔJ | Δfraud share | Δq_swap | Δq_theft |
|---|---|---|---|---|---|
| (0, 1) | stageroute_compliant | -0.045 | -0.078 | +0.72 | +0.68 |
| (0, 0.2) | stageroute_compliant | -0.037 | -0.083 | +0.56 | +0.53 |
| (0, 0.18) | stageroute_compliant | -0.033 | -0.079 | +0.56 | +0.53 |
| (0, 0.15) | stageroute_compliant | -0.031 | -0.081 | +0.56 | +0.53 |
| (0, 0.12) | stageroute_compliant | -0.023 | -0.069 | +0.72 | +0.68 |
| (0, 0.1) | stageroute_compliant | +0.019 | -0.035 | +0.74 | +0.70 |
| (0, 0.08) | stageroute_compliant | +0.029 | -0.026 | +0.87 | +0.86 |
| (0, 0.06) | stageroute_compliant | +0.052 | -0.026 | +0.87 | +0.86 |
| (0, 0.05) | stageroute_compliant | +0.085 | -0.004 | +0.87 | +0.86 |
| (0, 0) | stageroute_compliant | +0.181 | -0.026 | +0.87 | +0.86 |

## Hypothesis verdict

Hypothesis: D3's advantage (J and fraud suppression) over the compliant bandits GROWS as outcome feedback becomes delayed or sparse.

- grows from immediate to L = ∞: **no** (ΔJ non-decreasing along the L sweep within 0.01: yes)
- grows from immediate to π = 0: **yes** (ΔJ non-decreasing along the π sweep within 0.01: yes)
- regimes where D3 beats BOTH compliant bandits on J: (L=0, π=0.1), (L=0, π=0.08), (L=0, π=0.06), (L=0, π=0.05), (L=0, π=0)
- regimes where D3 has a lower fraud share than BOTH bandits: none
- seller attack rates: the bandits never lower q (they avoid the attacker instead of deterring it), D3's audits keep q low in every regime because audits do not depend on outcome feedback.
- **verdict: hypothesis NOT supported**
