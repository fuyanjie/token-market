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
| 5 | PILOT+compliance | 0.785 ± 0.009 | 0.807 ± 0.014 | 0.000 | 0.044 ± 0.012 | 0.92 / 0.62 | 0.052 | 0.0231 | 0.99 |
| 5 | StageRoute+compliance | 0.814 ± 0.027 | 0.822 ± 0.021 | 0.000 | 0.017 ± 0.017 | 0.70 / 0.64 | 0.022 | 0.0226 | 0.99 |
| 5 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.99 |
| 20 | PILOT+compliance | 0.782 ± 0.017 | 0.803 ± 0.014 | 0.000 | 0.042 ± 0.010 | 0.94 / 0.88 | 0.054 | 0.0223 | 0.96 |
| 20 | StageRoute+compliance | 0.797 ± 0.021 | 0.806 ± 0.014 | 0.000 | 0.019 ± 0.015 | 0.80 / 0.46 | 0.026 | 0.0221 | 0.96 |
| 20 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.96 |
| 50 | PILOT+compliance | 0.748 ± 0.022 | 0.785 ± 0.020 | 0.000 | 0.076 ± 0.006 | 0.95 / 0.94 | 0.090 | 0.0225 | 0.90 |
| 50 | StageRoute+compliance | 0.788 ± 0.012 | 0.800 ± 0.006 | 0.000 | 0.024 ± 0.016 | 0.70 / 0.64 | 0.033 | 0.0214 | 0.90 |
| 50 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.91 |
| ∞ (never) | PILOT+compliance | -0.030 ± 0.063 | 0.309 ± 0.046 | 0.000 | 0.678 ± 0.035 | 0.95 / 0.94 | 0.707 | 0.0233 | 0.00 |
| ∞ (never) | StageRoute+compliance | 0.585 ± 0.021 | 0.623 ± 0.019 | 0.000 | 0.075 ± 0.010 | 0.95 / 0.94 | 0.083 | 0.0116 | 0.00 |
| ∞ (never) | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.00 |

## Sparsity sweep (L = 0)

| π | policy | J | accuracy | violation rate | fraud share | sg q_swap / q_theft | share of purchases from sg | cost/task incl. audit | feedback coverage |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PILOT+compliance | 0.789 ± 0.010 | 0.811 ± 0.007 | 0.000 | 0.045 ± 0.011 | 0.95 / 0.93 | 0.048 | 0.0231 | 1.00 |
| 1 | StageRoute+compliance | 0.811 ± 0.026 | 0.822 ± 0.015 | 0.000 | 0.023 ± 0.022 | 0.80 / 0.77 | 0.034 | 0.0230 | 1.00 |
| 1 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 1.00 |
| 0.2 | PILOT+compliance | 0.780 ± 0.015 | 0.808 ± 0.011 | 0.000 | 0.058 ± 0.008 | 0.95 / 0.94 | 0.065 | 0.0220 | 0.21 |
| 0.2 | StageRoute+compliance | 0.803 ± 0.007 | 0.812 ± 0.007 | 0.000 | 0.018 ± 0.017 | 0.64 / 0.61 | 0.021 | 0.0220 | 0.21 |
| 0.2 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.20 |
| 0.05 | PILOT+compliance | 0.673 ± 0.039 | 0.740 ± 0.024 | 0.000 | 0.135 ± 0.032 | 0.95 / 0.94 | 0.149 | 0.0227 | 0.06 |
| 0.05 | StageRoute+compliance | 0.681 ± 0.115 | 0.729 ± 0.064 | 0.000 | 0.097 ± 0.106 | 0.95 / 0.94 | 0.107 | 0.0217 | 0.05 |
| 0.05 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.05 |
| 0 | PILOT+compliance | -0.030 ± 0.063 | 0.309 ± 0.046 | 0.000 | 0.678 ± 0.035 | 0.95 / 0.94 | 0.707 | 0.0233 | 0.00 |
| 0 | StageRoute+compliance | 0.585 ± 0.021 | 0.623 ± 0.019 | 0.000 | 0.075 ± 0.010 | 0.95 / 0.94 | 0.083 | 0.0116 | 0.00 |
| 0 | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.00 |

## Combined points

| (L, π) | policy | J | accuracy | violation rate | fraud share | sg q_swap / q_theft | share of purchases from sg | cost/task incl. audit | feedback coverage |
|---|---|---|---|---|---|---|---|---|---|
| (20, 0.2) | PILOT+compliance | 0.747 ± 0.033 | 0.782 ± 0.024 | 0.000 | 0.070 ± 0.021 | 0.95 / 0.94 | 0.083 | 0.0221 | 0.20 |
| (20, 0.2) | StageRoute+compliance | 0.752 ± 0.037 | 0.776 ± 0.021 | 0.000 | 0.048 ± 0.031 | 0.79 / 0.79 | 0.058 | 0.0215 | 0.20 |
| (20, 0.2) | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.19 |
| (50, 0.05) | PILOT+compliance | 0.634 ± 0.018 | 0.717 ± 0.009 | 0.000 | 0.166 ± 0.019 | 0.95 / 0.94 | 0.183 | 0.0234 | 0.05 |
| (50, 0.05) | StageRoute+compliance | 0.672 ± 0.043 | 0.714 ± 0.019 | 0.000 | 0.084 ± 0.062 | 0.95 / 0.94 | 0.093 | 0.0184 | 0.05 |
| (50, 0.05) | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.05 |

## D3 advantage over the best compliant bandit

ΔJ = J(D3) − max J(bandits); Δfraud = min fraud share(bandits) − fraud share(D3); Δq = min learned q over bandits − D3's (positive = D3 better).

| (L, π) | best bandit | ΔJ | Δfraud share | Δq_swap | Δq_theft |
|---|---|---|---|---|---|
| (0, 1) | stageroute_compliant | -0.045 | -0.078 | +0.72 | +0.68 |
| (5, 1) | stageroute_compliant | -0.047 | -0.084 | +0.62 | +0.54 |
| (20, 1) | stageroute_compliant | -0.030 | -0.082 | +0.72 | +0.38 |
| (50, 1) | stageroute_compliant | -0.022 | -0.077 | +0.62 | +0.56 |
| (∞ (never), 1) | stageroute_compliant | +0.181 | -0.026 | +0.87 | +0.86 |
| (0, 0.2) | stageroute_compliant | -0.037 | -0.083 | +0.56 | +0.53 |
| (0, 0.05) | stageroute_compliant | +0.085 | -0.004 | +0.87 | +0.86 |
| (0, 0) | stageroute_compliant | +0.181 | -0.026 | +0.87 | +0.86 |
| (20, 0.2) | stageroute_compliant | +0.014 | -0.053 | +0.71 | +0.71 |
| (50, 0.05) | stageroute_compliant | +0.094 | -0.017 | +0.87 | +0.86 |

## Hypothesis verdict

Hypothesis: D3's advantage (J and fraud suppression) over the compliant bandits GROWS as outcome feedback becomes delayed or sparse.

- grows from immediate to L = ∞: **yes** (ΔJ non-decreasing along the L sweep within 0.01: yes)
- grows from immediate to π = 0: **yes** (ΔJ non-decreasing along the π sweep within 0.01: yes)
- regimes where D3 beats BOTH compliant bandits on J: (L=∞ (never), π=1), (L=0, π=0.05), (L=0, π=0), (L=20, π=0.2), (L=50, π=0.05)
- regimes where D3 has a lower fraud share than BOTH bandits: none
- seller attack rates: the bandits never lower q (they avoid the attacker instead of deterring it), D3's audits keep q low in every regime because audits do not depend on outcome feedback.
- **verdict: hypothesis HELD in direction only** — D3's advantage grows as labels get delayed / sparse, but D3 overtakes the bandits on J only in the regimes listed above.
