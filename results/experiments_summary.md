# token-market v5 — experiment summary

Novelty framing: compliance-constrained portfolio purchasing + strategic fraud (model swap AND token theft) under IMPERFECT audits, compared with PILOT-style / StageRoute-style baselines on the JOINT objective J = accuracy − λ·violation rate − μ·fraud share (headline: section J). v5 (section F): the setting where audits matter is DELAYED / SPARSE outcome feedback - audits are a separate, immediate signal, while the bandits' correctness labels are delayed by L steps or revealed w.p. π. Reasoning-token length uncertainty is NOT claimed as a contribution: the expected-vs-actual cost logging is infrastructure and its finding is negative (overruns ≈ 0 under normal budgets, they only bind under tight budgets; section B).

config `configs/experiments.yaml`, seeds=[0, 1, 2], backend override=None, reputation source: Qwen/Qwen2.5-1.5B-Instruct: measured, sim-fast-mock: config_prior

## J — Joint objective — main comparison (v4 headline)

**J = accuracy − λ · compliance_violation_rate − μ · fraud_share**, with

- accuracy = task accuracy (final portfolio answer == gold; tasks without an answer count as wrong);
- compliance_violation_rate = compliance violations / **tasks** (purchases whose data flow breached a rule and went through; only the compliance-unaware policies can have them);
- fraud_share = attacked purchases / **purchases**, attacked = model swap (actual_model ≠ claimed_model) OR token theft (billed_tokens > actual_tokens, i.e. attack_mode ∈ {swap, theft, both}).

Default weights λ = 1.0, μ = 0.5. Market: the strategic (learning) seller_sg with attack modes ['swap', 'theft'] (it learns q_swap and q_theft against each policy's audit regime); only D3 audits (rate 0.1, checks ['identity', 'length'], d_identity = 0.9, d_length = 0.9, P = 0.25); budget × 2.0. Mean ± std over seeds [0, 1, 2]. **Main baseline to beat on J: `pilot_compliant` (PILOT + compliance filter).**

## Ranking by J

| rank | policy | J | Δ J vs pilot_compliant | accuracy | violation rate (/task) | fraud share (/purchase) | cost/task incl. audit | sg learned q_swap / q_theft |
|---|---|---|---|---|---|---|---|---|
| 1 | StageRoute-style + compliance filter | 0.811 ± 0.026 | +0.022 | 0.822 ± 0.015 | 0.000 | 0.023 | 0.0230 | 0.80 / 0.77 |
| 2 | PILOT-style + compliance filter | 0.789 ± 0.010 | +0.000 | 0.811 ± 0.007 | 0.000 | 0.045 | 0.0231 | 0.95 / 0.93 |
| 3 | **D3 audited_compliance_cascade (ours)** | 0.766 ± 0.037 | -0.022 | 0.817 ± 0.025 | 0.000 | 0.101 | 0.0266 | 0.08 / 0.08 |
| 4 | StageRoute-style (our simplified reimpl. of Li & Li 2025), no compliance filter | 0.735 ± 0.004 | -0.054 | 0.868 ± 0.005 | 0.128 | 0.011 | 0.0257 | 0.64 / 0.31 |
| 5 | PILOT-style (our simplified reimpl. of Panda et al. 2025), no compliance filter | 0.697 ± 0.006 | -0.092 | 0.853 ± 0.009 | 0.137 | 0.040 | 0.0250 | 0.95 / 0.86 |
| 6 | cascade_compliant | 0.644 ± 0.010 | -0.144 | 0.783 ± 0.010 | 0.000 | 0.277 | 0.0321 | 0.96 / 0.96 |
| 7 | single_cheapest_compliant | 0.585 ± 0.021 | -0.203 | 0.623 ± 0.019 | 0.000 | 0.075 | 0.0116 | 0.95 / 0.94 |
| 8 | compliance_unaware_cheapest | 0.412 ± 0.035 | -0.377 | 0.627 ± 0.044 | 0.215 | 0.000 | 0.0073 | 0.54 / 0.49 |
| 9 | vote_k_compliant | 0.318 ± 0.021 | -0.471 | 0.482 ± 0.018 | 0.000 | 0.328 | 0.0424 | 0.95 / 0.93 |
| 10 | single_best_compliant | -0.166 ± 0.043 | -0.955 | 0.222 ± 0.031 | 0.000 | 0.777 | 0.0233 | 0.95 / 0.94 |

## Sensitivity to (λ, μ)

| policy | λ=1.0, μ=0.5 | λ=0.5, μ=0.25 | λ=2.0, μ=1.0 | λ=1.0, μ=0.0 |
|---|---|---|---|---|
| stageroute_compliant | 0.811 (#1) | 0.816 (#1) | 0.799 (#1) | 0.822 (#1) |
| pilot_compliant | 0.789 (#2) | 0.800 (#3) | 0.766 (#2) | 0.811 (#3) |
| audited_compliance_cascade | 0.766 (#3) | 0.791 (#4) | 0.716 (#3) | 0.817 (#2) |
| stageroute | 0.735 (#4) | 0.801 (#2) | 0.601 (#4) | 0.740 (#5) |
| pilot | 0.697 (#5) | 0.775 (#5) | 0.540 (#6) | 0.717 (#6) |
| cascade_compliant | 0.644 (#6) | 0.713 (#6) | 0.506 (#7) | 0.783 (#4) |
| single_cheapest_compliant | 0.585 (#7) | 0.604 (#7) | 0.548 (#5) | 0.623 (#7) |
| compliance_unaware_cheapest | 0.412 (#8) | 0.519 (#8) | 0.197 (#8) | 0.412 (#9) |
| vote_k_compliant | 0.318 (#9) | 0.400 (#9) | 0.154 (#9) | 0.482 (#8) |
| single_best_compliant | -0.166 (#10) | 0.028 (#10) | -0.555 (#10) | 0.222 (#10) |

## Equal-cost view (each policy's budget sweep, metrics linearly interpolated at cost/task = c incl. audit; – = policy cannot get this cheap; * = saturated: the policy spends less than c even with the largest budget, its most expensive point is shown)

### cost/task = 0.0050

| policy | J | accuracy | violation rate | fraud share |
|---|---|---|---|---|
| single_cheapest_compliant | 0.309 | 0.326 | 0.000 | 0.035 |
| compliance_unaware_cheapest | 0.243 | 0.427 | 0.184 | 0.000 |
| pilot_compliant | 0.231 | 0.257 | 0.000 | 0.051 |
| pilot | 0.187 | 0.306 | 0.113 | 0.012 |
| stageroute_compliant | 0.154 | 0.182 | 0.000 | 0.056 |
| cascade_compliant | 0.019 | 0.135 | 0.000 | 0.232 |
| vote_k_compliant | -0.060 | 0.075 | 0.000 | 0.270 |
| single_best_compliant | -0.284 | 0.061 | 0.000 | 0.691 |
| audited_compliance_cascade | – | – | – | – |

### cost/task = 0.0100

| policy | J | accuracy | violation rate | fraud share |
|---|---|---|---|---|
| single_cheapest_compliant | 0.511 | 0.548 | 0.000 | 0.075 |
| pilot_compliant | 0.432 | 0.455 | 0.000 | 0.046 |
| compliance_unaware_cheapest | 0.412* | 0.627* | 0.215* | 0.000* |
| stageroute_compliant | 0.348 | 0.365 | 0.000 | 0.033 |
| pilot | 0.346 | 0.522 | 0.171 | 0.007 |
| audited_compliance_cascade | 0.197 | 0.285 | 0.000 | 0.177 |
| cascade_compliant | 0.131 | 0.258 | 0.000 | 0.254 |
| vote_k_compliant | -0.019 | 0.129 | 0.000 | 0.295 |
| single_best_compliant | -0.248 | 0.112 | 0.000 | 0.720 |

### cost/task = 0.0150

| policy | J | accuracy | violation rate | fraud share |
|---|---|---|---|---|
| pilot_compliant | 0.614 | 0.632 | 0.000 | 0.037 |
| single_cheapest_compliant | 0.585* | 0.623* | 0.000* | 0.075* |
| stageroute_compliant | 0.529 | 0.541 | 0.000 | 0.025 |
| pilot | 0.507 | 0.676 | 0.163 | 0.011 |
| compliance_unaware_cheapest | 0.412* | 0.627* | 0.215* | 0.000* |
| audited_compliance_cascade | 0.341 | 0.422 | 0.000 | 0.162 |
| cascade_compliant | 0.232 | 0.367 | 0.000 | 0.269 |
| vote_k_compliant | 0.036 | 0.189 | 0.000 | 0.305 |
| single_best_compliant | -0.209 | 0.159 | 0.000 | 0.734 |

### cost/task = 0.0200

| policy | J | accuracy | violation rate | fraud share |
|---|---|---|---|---|
| pilot_compliant | 0.723 | 0.742 | 0.000 | 0.039 |
| stageroute_compliant | 0.690 | 0.703 | 0.000 | 0.027 |
| pilot | 0.636 | 0.784 | 0.139 | 0.017 |
| single_cheapest_compliant | 0.585* | 0.623* | 0.000* | 0.075* |
| audited_compliance_cascade | 0.519 | 0.585 | 0.000 | 0.133 |
| compliance_unaware_cheapest | 0.412* | 0.627* | 0.215* | 0.000* |
| cascade_compliant | 0.358 | 0.493 | 0.000 | 0.269 |
| vote_k_compliant | 0.085 | 0.241 | 0.000 | 0.311 |
| single_best_compliant | -0.177 | 0.201 | 0.000 | 0.756 |

### cost/task = 0.0235

| policy | J | accuracy | violation rate | fraud share |
|---|---|---|---|---|
| stageroute_compliant | 0.811* | 0.822* | 0.000* | 0.023* |
| pilot_compliant | 0.772 | 0.807 | 0.000 | 0.070 |
| pilot | 0.684 | 0.839 | 0.141 | 0.028 |
| audited_compliance_cascade | 0.643 | 0.699 | 0.000 | 0.112 |
| single_cheapest_compliant | 0.585* | 0.623* | 0.000* | 0.075* |
| cascade_compliant | 0.446 | 0.581 | 0.000 | 0.269 |
| compliance_unaware_cheapest | 0.412* | 0.627* | 0.215* | 0.000* |
| vote_k_compliant | 0.120 | 0.277 | 0.000 | 0.314 |
| single_best_compliant | -0.166 | 0.223 | 0.000 | 0.779 |

### cost/task = 0.0275

| policy | J | accuracy | violation rate | fraud share |
|---|---|---|---|---|
| stageroute_compliant | 0.811* | 0.822* | 0.000* | 0.023* |
| audited_compliance_cascade | 0.806 | 0.857 | 0.000 | 0.102 |
| pilot_compliant | 0.772* | 0.807* | 0.000* | 0.071* |
| pilot | 0.697* | 0.853* | 0.137* | 0.040* |
| single_cheapest_compliant | 0.585* | 0.623* | 0.000* | 0.075* |
| cascade_compliant | 0.537 | 0.673 | 0.000 | 0.272 |
| compliance_unaware_cheapest | 0.412* | 0.627* | 0.215* | 0.000* |
| vote_k_compliant | 0.161 | 0.320 | 0.000 | 0.318 |
| single_best_compliant | -0.165* | 0.231* | 0.000* | 0.793* |


## F — Delayed / sparse outcome feedback (v5 ablation)

**Setting.** Outcome feedback = whether a purchased answer was correct (the bandit reward). A purchase at step t (task index) has its label revealed with probability π and, if revealed, delivered to the router at step t + L (FIFO by due step, before that step's routing decision); labels still pending at the end of the episode are flushed if L is finite, never delivered if L = ∞. Only the LABEL is delayed: the realised cost is on the buyer's own bill and stays immediate (PILOT budget bins, StageRoute cost estimate).

**Audits are a separate signal.** D3's audits (rate 0.1, checks ['identity', 'length'], d_identity = 0.9, d_length = 0.9, P = 0.25) run, slash/delist the seller and update D3's TrustModel IMMEDIATELY in every regime; D3's routing never uses correctness labels, so the feedback channel only changes its logging. PILOT+compliance and StageRoute+compliance do NOT audit (audit rate 0).

Market: strategic learning seller seller_sg with attack modes ['swap', 'theft'] (same as section J), budget × 2.0, J = acc − 1.0·violation rate − 0.5·fraud share. Mean ± std over seeds [0, 1, 2]. q = seller's learned attack rate (mean over the last half of epochs). coverage = labels delivered during the episode / purchases.

Real vs simulated: the correctness labels come from the REAL cached Qwen outputs (no new generation); the feedback channel (delay L, reveal probability π, flush rule), audits, the seller's learning rule, prices and budgets are SIMULATED.

### Delay sweep (π = 1)

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

### Sparsity sweep (L = 0)

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

### Combined points

| (L, π) | policy | J | accuracy | violation rate | fraud share | sg q_swap / q_theft | share of purchases from sg | cost/task incl. audit | feedback coverage |
|---|---|---|---|---|---|---|---|---|---|
| (20, 0.2) | PILOT+compliance | 0.747 ± 0.033 | 0.782 ± 0.024 | 0.000 | 0.070 ± 0.021 | 0.95 / 0.94 | 0.083 | 0.0221 | 0.20 |
| (20, 0.2) | StageRoute+compliance | 0.752 ± 0.037 | 0.776 ± 0.021 | 0.000 | 0.048 ± 0.031 | 0.79 / 0.79 | 0.058 | 0.0215 | 0.20 |
| (20, 0.2) | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.19 |
| (50, 0.05) | PILOT+compliance | 0.634 ± 0.018 | 0.717 ± 0.009 | 0.000 | 0.166 ± 0.019 | 0.95 / 0.94 | 0.183 | 0.0234 | 0.05 |
| (50, 0.05) | StageRoute+compliance | 0.672 ± 0.043 | 0.714 ± 0.019 | 0.000 | 0.084 ± 0.062 | 0.95 / 0.94 | 0.093 | 0.0184 | 0.05 |
| (50, 0.05) | **D3 (ours)** | 0.766 ± 0.037 | 0.817 ± 0.025 | 0.000 | 0.101 ± 0.023 | 0.08 / 0.08 | 0.260 | 0.0266 | 0.05 |

### D3 advantage over the best compliant bandit

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

### Hypothesis verdict

Hypothesis: D3's advantage (J and fraud suppression) over the compliant bandits GROWS as outcome feedback becomes delayed or sparse.

- grows from immediate to L = ∞: **yes** (ΔJ non-decreasing along the L sweep within 0.01: yes)
- grows from immediate to π = 0: **yes** (ΔJ non-decreasing along the π sweep within 0.01: yes)
- regimes where D3 beats BOTH compliant bandits on J: (L=∞ (never), π=1), (L=0, π=0.05), (L=0, π=0), (L=20, π=0.2), (L=50, π=0.05)
- regimes where D3 has a lower fraud share than BOTH bandits: none
- seller attack rates: the bandits never lower q (they avoid the attacker instead of deterring it), D3's audits keep q low in every regime because audits do not depend on outcome feedback.
- **verdict: hypothesis HELD in direction only** — D3's advantage grows as labels get delayed / sparse, but D3 overtakes the bandits on J only in the regimes listed above.

## C — strategic model-swap seller vs buyer audits (fraud / audit threshold)

Buyer policy `single_best_compliant` (routes on CLAIMED quality, so it sends most demand to the swap seller); 960 tasks/run in 96 rounds (= seller epochs); seeds=[0, 1, 2]. The seller (seller_sg, claims Qwen2.5-1.5B, can serve 0.5B) LEARNS its swap rate q per epoch with Hedge over q ∈ {0, 0.1, …, 1} on its own realised profit (incl. stake actually slashed), ε-exploration 0.1; learned q = mean q played over the last half of the epochs (mean ± std over seeds).

Per-purchase cost saving of swapping = cost_gap 0.07/1K × claimed-model mean tokens 142.3 / 1000 = **0.00996**; detect_prob d = 0.9; audits are SIMULATED identity checks.

## Threshold: analytic a* = saving / (d·P) vs empirical

Empirical threshold = smallest audit rate in the grid from which on the learned q stays < 0.1.

| penalty P | analytic a* | first grid a > a* | empirical a (learned q < thr) | same grid point? |
|---|---|---|---|---|
| 0.02 | 0.5535 | > grid | not reached | yes |
| 0.1 | 0.1107 | 0.2 | 0.2 | yes |
| 0.5 | 0.0221 | 0.05 | 0.05 | yes |

## Sweep

| P | audit rate a | analytic gain = saving − a·d·P | analytic q* | learned q | served swap rate | swaps detected | stake slashed | seller_sg profit | sg purchases | buyer audit cost | task accuracy |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.02 | 0.0 | +0.00996 | 1 | 0.962 ± 0.014 | 0.958 | 0.0 | 0.00 | +15.276 | 799 | 0.000 | 0.705 |
| 0.02 | 0.02 | +0.00960 | 1 | 0.962 ± 0.014 | 0.958 | 16.3 | 0.33 | +14.950 | 799 | 0.087 | 0.705 |
| 0.02 | 0.05 | +0.00906 | 1 | 0.962 ± 0.014 | 0.958 | 31.0 | 0.62 | +14.656 | 799 | 0.175 | 0.705 |
| 0.02 | 0.1 | +0.00816 | 1 | 0.962 ± 0.014 | 0.958 | 59.7 | 1.19 | +14.083 | 799 | 0.325 | 0.705 |
| 0.02 | 0.2 | +0.00636 | 1 | 0.962 ± 0.014 | 0.958 | 128.7 | 2.57 | +12.703 | 799 | 0.716 | 0.705 |
| 0.02 | 0.3 | +0.00456 | 1 | 0.962 ± 0.014 | 0.958 | 194.0 | 3.88 | +11.396 | 799 | 1.084 | 0.705 |
| 0.02 | 0.5 | +0.00096 | 1 | 0.962 ± 0.014 | 0.936 | 332.0 | 6.64 | +8.473 | 799 | 1.924 | 0.708 |
| 0.1 | 0.0 | +0.00996 | 1 | 0.962 ± 0.014 | 0.958 | 0.0 | 0.00 | +15.276 | 799 | 0.000 | 0.705 |
| 0.1 | 0.02 | +0.00816 | 1 | 0.962 ± 0.014 | 0.958 | 16.3 | 1.63 | +13.643 | 799 | 0.087 | 0.705 |
| 0.1 | 0.05 | +0.00546 | 1 | 0.962 ± 0.014 | 0.958 | 31.0 | 3.10 | +12.176 | 799 | 0.175 | 0.705 |
| 0.1 | 0.1 | +0.00096 | 1 | 0.642 ± 0.546 | 0.670 | 43.7 | 4.37 | +8.416 | 799 | 0.325 | 0.768 |
| 0.1 | 0.2 | -0.00804 | 0 | 0.031 ± 0.019 | 0.069 | 9.3 | 0.93 | +6.568 | 799 | 0.709 | 0.897 |
| 0.1 | 0.3 | -0.01704 | 0 | 0.031 ± 0.019 | 0.060 | 11.7 | 1.17 | +6.261 | 799 | 1.088 | 0.900 |
| 0.1 | 0.5 | -0.03504 | 0 | 0.031 ± 0.019 | 0.044 | 16.0 | 1.60 | +5.679 | 799 | 1.935 | 0.903 |
| 0.5 | 0.0 | +0.00996 | 1 | 0.962 ± 0.014 | 0.958 | 0.0 | 0.00 | +15.276 | 799 | 0.000 | 0.705 |
| 0.5 | 0.02 | +0.00096 | 1 | 0.462 ± 0.475 | 0.613 | 10.3 | 5.17 | +7.043 | 799 | 0.087 | 0.780 |
| 0.5 | 0.05 | -0.01254 | 0 | 0.031 ± 0.019 | 0.226 | 4.3 | 2.17 | +6.666 | 799 | 0.179 | 0.863 |
| 0.5 | 0.1 | -0.03504 | 0 | 0.031 ± 0.019 | 0.052 | 2.0 | 1.00 | +6.349 | 799 | 0.327 | 0.901 |
| 0.5 | 0.2 | -0.08004 | 0 | 0.031 ± 0.019 | 0.052 | 6.3 | 3.17 | +4.182 | 799 | 0.709 | 0.901 |
| 0.5 | 0.3 | -0.12504 | 0 | 0.031 ± 0.019 | 0.052 | 10.0 | 5.00 | +2.349 | 799 | 1.087 | 0.901 |
| 0.5 | 0.5 | -0.21504 | 0 | 0.031 ± 0.019 | 0.044 | 16.0 | 8.00 | -0.721 | 799 | 1.935 | 0.903 |

Notes: the learning seller never sees a, d or P — only its realised profits. Because of ε-exploration the q actually played never drops to exactly 0 (floor ≈ ε/2). Realised savings differ slightly from the analytic one because swapped (0.5B) and honest (1.5B) answers have different real token counts (revenue is per token). Values per seed: results/fraud_audit_threshold.json.

## I — Imperfect detection — audit rate a × detection probability d (miss rate 1 − d) × penalty P

Learning model-swap seller (swap only), buyer policy `single_best_compliant`, 960 tasks / 96 epochs per run, seeds=[0, 1, 2]. Identity check detects a swapped answer with probability d; **miss rate = false-negative rate = 1 − d**; false-positive rate = 0 (honest answers are never flagged). Detection is SIMULATED.

Swap saving per purchase = 0.00996. Analytic threshold **a\*(d) = saving / (d · P)** (decreasing in d: halving d doubles the audit rate needed). Empirical threshold = smallest grid audit rate from which on the learned q stays < 0.1.

### Thresholds a*(d) vs empirical

| P | d | miss rate 1−d | analytic a*(d) | first grid a > a* | empirical a (learned q < thr) | match |
|---|---|---|---|---|---|---|
| 0.1 | 0.3 | 0.7 | 0.3321 | 0.5 | 0.5 | yes |
| 0.1 | 0.5 | 0.5 | 0.1993 | 0.2 | 0.3 | no |
| 0.1 | 0.7 | 0.3 | 0.1423 | 0.2 | 0.2 | yes |
| 0.1 | 0.9 | 0.1 | 0.1107 | 0.2 | 0.2 | yes |
| 0.1 | 1.0 | 0.0 | 0.0996 | 0.1 | 0.2 | no |
| 0.5 | 0.3 | 0.7 | 0.0664 | 0.1 | 0.1 | yes |
| 0.5 | 0.5 | 0.5 | 0.0399 | 0.05 | 0.1 | no |
| 0.5 | 0.7 | 0.3 | 0.0285 | 0.05 | 0.05 | yes |
| 0.5 | 0.9 | 0.1 | 0.0221 | 0.05 | 0.05 | yes |
| 0.5 | 1.0 | 0.0 | 0.0199 | 0.02 | 0.02 | yes |

## T — Token theft — strategic seller chooses (q_swap, q_theft) under identity / length audits

seller_sg can (i) **swap** (serve Qwen2.5-0.5B while claiming 1.5B) and/or (ii) **steal tokens**: bill `claimed_mean` tokens (claimed-model mean 142.3) while actually stopping after `theft_max_new_tokens` = 48 tokens (truncation of the REAL cached Qwen output; the final answer is re-parsed from the truncated text, so it is usually lost). Revenue is charged on BILLED tokens, serving cost on ACTUAL tokens. Per epoch the seller picks (q_swap, q_theft) on {0, 0.1, …, 1}² by ε-greedy on its own realised profit; per purchase swap ~ Bern(q_swap), theft ~ Bern(q_theft) → attack_mode ∈ {none, swap, theft, both}.

Buyer policy `single_best_compliant`, 960 tasks / 96 epochs, seeds=[0, 1, 2]. Analytic per-purchase gains before penalties: swap 0.00996, theft 0.01126 = (price·E[billed − full] + cost·E[full − actual]) / 1000. Length audit flags billed > actual·(1 + 0.1); both detectors are SIMULATED (miss rate 1 − d, no false positives) except the reference cross-check row below.

## Attack × audit regime (a = 0.1, d_identity = 0.9, d_length = 0.9, P = 0.5)

| attack enabled | audit regime | learned q_swap | learned q_theft | served swap / theft rate | swaps det. / served | thefts det. / served | seller_sg profit | buyer overpayment | buyer accuracy | fraud share | J |
|---|---|---|---|---|---|---|---|---|---|---|---|
| honest | no audit | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 / 0.00 | 0.0 / 0 | 0.0 / 0 | +6.87 | 0.00 | 0.914 | 0.000 | 0.914 |
| honest | identity only | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 / 0.00 | 0.0 / 0 | 0.0 / 0 | +6.87 | 0.00 | 0.914 | 0.000 | 0.914 |
| honest | length only | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 / 0.00 | 0.0 / 0 | 0.0 / 0 | +6.87 | 0.00 | 0.914 | 0.000 | 0.914 |
| honest | identity + length | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 / 0.00 | 0.0 / 0 | 0.0 / 0 | +6.87 | 0.00 | 0.914 | 0.000 | 0.914 |
| swap-only | no audit | 0.96 ± 0.01 | 0.00 ± 0.00 | 0.96 / 0.00 | 0.0 / 766 | 0.0 / 0 | +15.28 | 0.00 | 0.705 | 0.798 | 0.306 |
| swap-only | identity only | 0.03 ± 0.02 | 0.00 ± 0.00 | 0.05 / 0.00 | 2.0 / 42 | 0.0 / 0 | +6.35 | 0.00 | 0.901 | 0.043 | 0.880 |
| swap-only | length only | 0.96 ± 0.01 | 0.00 ± 0.00 | 0.96 / 0.00 | 0.0 / 766 | 0.0 / 0 | +15.28 | 0.00 | 0.705 | 0.798 | 0.306 |
| swap-only | identity + length | 0.03 ± 0.02 | 0.00 ± 0.00 | 0.05 / 0.00 | 2.0 / 42 | 0.0 / 0 | +6.35 | 0.00 | 0.901 | 0.043 | 0.880 |
| theft-only | no audit | 0.00 ± 0.00 | 0.96 ± 0.01 | 0.00 / 0.97 | 0.0 / 0 | 0.0 / 772 | +15.53 | 13.06 | 0.170 | 0.804 | -0.232 |
| theft-only | identity only | 0.00 ± 0.00 | 0.96 ± 0.01 | 0.00 / 0.97 | 0.0 / 0 | 0.0 / 772 | +15.53 | 13.06 | 0.170 | 0.804 | -0.232 |
| theft-only | length only | 0.00 ± 0.00 | 0.05 ± 0.01 | 0.00 / 0.07 | 0.0 / 0 | 3.7 / 57 | +5.67 | 0.96 | 0.860 | 0.059 | 0.830 |
| theft-only | identity + length | 0.00 ± 0.00 | 0.05 ± 0.01 | 0.00 / 0.07 | 0.0 / 0 | 3.7 / 57 | +5.67 | 0.96 | 0.860 | 0.059 | 0.830 |
| both | no audit | 0.96 ± 0.02 | 0.97 ± 0.02 | 0.94 / 0.95 | 0.0 / 749 | 0.0 / 757 | +18.07 | 12.97 | 0.226 | 0.811 | -0.179 |
| both | identity only | 0.03 ± 0.02 | 0.97 ± 0.02 | 0.08 / 0.95 | 3.7 / 62 | 0.0 / 759 | +13.89 | 12.85 | 0.183 | 0.811 | -0.223 |
| both | length only | 0.96 ± 0.02 | 0.05 ± 0.03 | 0.93 / 0.09 | 0.0 / 746 | 6.7 / 73 | +12.28 | 1.24 | 0.654 | 0.811 | 0.249 |
| both | identity + length | 0.03 ± 0.02 | 0.05 ± 0.03 | 0.09 / 0.10 | 3.7 / 69 | 7.0 / 78 | +4.16 | 1.32 | 0.834 | 0.108 | 0.780 |

## Which audit is needed to deter which attack (✓ = every enabled attack's learned rate < 0.1)

| attack | no audit | identity only | length only | identity + length |
|---|---|---|---|---|
| swap-only | ✗ | ✓ | ✗ | ✓ |
| theft-only | ✗ | ✗ | ✓ | ✓ |
| both | ✗ | ✗ | ✗ | ✓ |

## Thresholds for the combined attacker (both enabled, identity + length audits)

| P | d_identity | d_length | analytic a*_swap | grid / empirical a_swap | analytic a*_theft | grid / empirical a_theft |
|---|---|---|---|---|---|---|
| 0.1 | 0.9 | 0.9 | 0.1107 | 0.2 / 0.2 | 0.1251 | 0.2 / 0.2 |
| 0.1 | 0.9 | 0.3 | 0.1107 | 0.2 / 0.2 | 0.3753 | > grid / not reached |
| 0.1 | 0.3 | 0.9 | 0.3321 | > grid / not reached | 0.1251 | 0.2 / 0.2 |
| 0.1 | 0.5 | 0.5 | 0.1993 | 0.2 / 0.2 | 0.2252 | 0.3 / 0.3 |
| 0.5 | 0.9 | 0.9 | 0.0221 | 0.05 / 0.05 | 0.0250 | 0.05 / 0.05 |
| 0.5 | 0.9 | 0.3 | 0.0221 | 0.05 / 0.02 | 0.0751 | 0.1 / 0.2 |
| 0.5 | 0.3 | 0.9 | 0.0664 | 0.1 / 0.2 | 0.0250 | 0.05 / 0.05 |
| 0.5 | 0.5 | 0.5 | 0.0399 | 0.05 / 0.05 | 0.0450 | 0.05 / 0.05 |


## D — baselines vs the STRATEGIC model-swap seller

All policies face the same learning swap seller (seller_sg; penalty P=0.25, d=0.9). Only D3 audits (rate 0.1, audit cost 0.004 per audit charged to the buyer budget), so for every other policy the seller faces a = 0. Mean ± std over seeds [0, 1, 2].

v4: the last column is the joint objective J = accuracy − λ·violation rate (/task) − μ·fraud share (/purchase), λ = 1, μ = 0.5 (here fraud = swap only; the v4 headline with swap + theft and the J ranking is results/joint_objective.md). This raw-accuracy table is kept as the v3 appendix.

| policy | task accuracy | total cost incl. audit | of which audit | cost/task | budget violations | compliance violations | fraud-seller share (swapped purchases) | sg learned q | swaps detected / served | stake slashed | buyer surplus | J |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single_cheapest_compliant | 0.665 ± 0.019 | 5.562 ± 0.292 | 0.000 | 0.0116 ± 0.0006 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.061 ± 0.019 | 0.922 ± 0.081 | 0.0 / 29.3 | 0.00 | 19.221 ± 0.441 | 0.635 ± 0.029 |
| single_best_compliant | 0.634 ± 0.008 | 11.606 ± 0.227 | 0.000 | 0.0242 ± 0.0005 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.766 ± 0.016 | 0.950 ± 0.044 | 0.0 / 335.7 | 0.00 | 12.431 ± 0.333 | 0.251 ± 0.015 |
| cascade_compliant | 0.768 ± 0.011 | 13.940 ± 0.054 | 0.000 | 0.0290 ± 0.0001 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.302 ± 0.014 | 0.950 ± 0.044 | 0.0 / 222.7 | 0.00 | 14.897 ± 0.476 | 0.617 ± 0.008 |
| vote_k_compliant | 0.690 ± 0.014 | 20.669 ± 0.161 | 0.000 | 0.0431 ± 0.0003 | 0.7 ± 0.6 | 0.0 ± 0.0 | 0.323 ± 0.004 | 0.950 ± 0.044 | 0.0 / 311.7 | 0.00 | 5.555 ± 0.581 | 0.529 ± 0.012 |
| compliance_unaware_cheapest | 0.627 ± 0.044 | 3.486 ± 0.028 | 0.000 | 0.0073 ± 0.0001 | 0.0 ± 0.0 | 103.3 ± 6.4 | 0.000 ± 0.000 | 0.539 ± 0.028 | 0.0 / 0.0 | 0.00 | 19.594 ± 1.671 | 0.412 ± 0.035 |
| PILOT-style (our simplified reimpl. of Panda et al. 2025), no compliance filter | 0.883 ± 0.019 | 11.433 ± 0.093 | 0.000 | 0.0238 ± 0.0002 | 0.0 ± 0.0 | 77.7 ± 9.3 | 0.235 ± 0.066 | 0.950 ± 0.044 | 0.0 / 112.7 | 0.00 | 21.420 ± 0.660 | 0.603 ± 0.033 |
| PILOT-style + compliance filter | 0.856 ± 0.013 | 11.183 ± 0.319 | 0.000 | 0.0233 ± 0.0007 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.215 ± 0.049 | 0.950 ± 0.044 | 0.0 / 103.0 | 0.00 | 20.667 ± 0.634 | 0.749 ± 0.015 |
| StageRoute-style (our simplified reimpl. of Li & Li 2025), no compliance filter | 0.837 ± 0.037 | 12.551 ± 0.154 | 0.000 | 0.0261 ± 0.0003 | 0.0 ± 0.0 | 61.3 ± 8.0 | 0.085 ± 0.038 | 0.950 ± 0.044 | 0.0 / 37.7 | 0.00 | 18.819 ± 1.071 | 0.667 ± 0.041 |
| StageRoute-style + compliance filter | 0.797 ± 0.030 | 11.507 ± 0.565 | 0.000 | 0.0240 ± 0.0012 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.116 ± 0.086 | 0.950 ± 0.044 | 0.0 / 51.7 | 0.00 | 18.453 ± 1.455 | 0.739 ± 0.073 |
| **D3 audited_compliance_cascade (ours)** | 0.811 ± 0.010 | 11.979 ± 0.364 | 0.233 | 0.0250 ± 0.0008 | 0.3 ± 0.6 | 0.0 ± 0.0 | 0.042 ± 0.017 | 0.131 ± 0.108 | 3.3 / 28.0 | 0.83 | 18.418 ± 0.687 | 0.790 ± 0.014 |

## Accuracy at equal cost (from the A curves)

| family | c=0.0100 | c=0.0203 | c=0.0246 | c=0.0272 |
|---|---|---|---|---|
| audited_compliance_cascade | 0.317 | 0.646 | 0.786 | 0.877 |
| audited_compliance_cascade (audit rate) | – | – | – | 0.880 |
| cascade_compliant | 0.265 | 0.537 | 0.646 | 0.710 |
| cascade_compliant (threshold) | – | 0.769 | 0.798 | 0.808 |
| pilot | 0.546 | 0.788 | 0.890 | 0.896 |
| pilot_compliant | 0.465 | 0.761 | 0.875 | 0.876 |
| single_best_compliant | 0.275 | 0.538 | 0.644 | 0.693 |
| single_cheapest_compliant | 0.588 | 0.665 | 0.665 | 0.665 |
| stageroute | 0.305 | 0.644 | 0.786 | 0.865 |
| stageroute_compliant | 0.342 | 0.681 | 0.819 | 0.832 |
| vote_k_compliant (k) | – | – | – | 0.693 |
| vote_k_compliant k=1 | 0.275 | 0.538 | 0.644 | 0.693 |
| vote_k_compliant k=2 | 0.173 | 0.335 | 0.401 | 0.440 |
| vote_k_compliant k=3 | 0.174 | 0.340 | 0.405 | 0.447 |

Differences from the papers (all baselines are OUR SIMPLIFIED REIMPLEMENTATIONS):
- PILOT: hand-made task features instead of query embeddings; the preference prior is the CLAIMED model's public reputation (so a swap seller inherits a good prior); reward = observed correctness; ON-MCKP ZCL threshold with budget bins + spillover and the B_left/Q_left fallback; one LinUCB shared by all buyers, budgets per buyer.
- StageRoute: only the per-query routing LP with UCB rewards / LCB costs and throughput caps (alpha = capacity share); the stage-wise deployment MIP is skipped (3 fixed sellers); LP solved exactly by vertex enumeration.
- Neither baseline accounts for audit cost, models a strategic seller, or filters on compliance (the `_compliant` variants add the hard compliance filter); non-filtered variants run through the audit_only gateway so their breaches are counted.
- D3 routes on audit-adjusted quality: once an audit reveals the served model, the seller's quality is (1 − q̂)·rep(claimed) + q̂·rep(revealed), q̂ = detected / (audits·d) (smoothed).

## A — accuracy vs cost curves

Market with the STRATEGIC (learning) swap seller; cost = mean cost per task INCLUDING audit cost (mean ± std over seeds [0, 1, 2]). Each family is one policy swept over its knob or over the per-buyer budget multiplier (StageRoute's per-query budget b = B/T moves with the multiplier).

## Accuracy at equal cost (best accuracy at cost/task ≤ c on each family's interpolated Pareto envelope; – = family cannot reach that cost level)

| family | c=0.0100 | c=0.0203 | c=0.0246 | c=0.0272 |
|---|---|---|---|---|
| audited_compliance_cascade | 0.317 | 0.646 | 0.786 | 0.877 |
| audited_compliance_cascade (audit rate) | – | – | – | 0.880 |
| cascade_compliant | 0.265 | 0.537 | 0.646 | 0.710 |
| cascade_compliant (threshold) | – | 0.769 | 0.798 | 0.808 |
| pilot | 0.546 | 0.788 | 0.890 | 0.896 |
| pilot_compliant | 0.465 | 0.761 | 0.875 | 0.876 |
| single_best_compliant | 0.275 | 0.538 | 0.644 | 0.693 |
| single_cheapest_compliant | 0.588 | 0.665 | 0.665 | 0.665 |
| stageroute | 0.305 | 0.644 | 0.786 | 0.865 |
| stageroute_compliant | 0.342 | 0.681 | 0.819 | 0.832 |
| vote_k_compliant (k) | – | – | – | 0.693 |
| vote_k_compliant k=1 | 0.275 | 0.538 | 0.644 | 0.693 |
| vote_k_compliant k=2 | 0.173 | 0.335 | 0.401 | 0.440 |
| vote_k_compliant k=3 | 0.174 | 0.340 | 0.405 | 0.447 |

## Pareto frontier (all points)

| family | knob | cost/task | accuracy |
|---|---|---|---|
| stageroute | budget×0.2 | 0.0049 | 0.154 |
| stageroute_compliant | budget×0.2 | 0.0049 | 0.169 |
| pilot | budget×0.2 | 0.0049 | 0.307 |
| single_cheapest_compliant | budget×0.2 | 0.0050 | 0.337 |
| single_cheapest_compliant | budget×0.4 | 0.0082 | 0.503 |
| pilot | budget×0.4 | 0.0099 | 0.544 |
| single_cheapest_compliant | budget×0.6 | 0.0104 | 0.604 |
| single_cheapest_compliant | budget×1.0 | 0.0114 | 0.651 |
| single_cheapest_compliant | budget×1.5 | 0.0116 | 0.665 |
| cascade_compliant (threshold) | thr=0.1 | 0.0117 | 0.667 |
| cascade_compliant (threshold) | thr=0.3 | 0.0151 | 0.709 |
| pilot | budget×1.0 | 0.0203 | 0.788 |
| pilot_compliant | budget×1.5 | 0.0228 | 0.831 |
| pilot_compliant | budget×2.0 | 0.0233 | 0.856 |
| pilot | budget×2.0 | 0.0238 | 0.883 |
| pilot | budget×3.0 | 0.0252 | 0.896 |


## B — long reasoning tasks (GSM8K-hard + MATH-500, real Qwen outputs)

_v4: infrastructure / negative finding, NOT a contribution claim — per-purchase cost overruns are large on long outputs, but budget violations are ≈ 0 under normal budgets and only bind under tight budgets._

## Measured model accuracy on the long subset

| model | n | acc overall | acc GSM8K-hard (d4) | acc MATH-500 L3+ (d5) | tokens mean ± std | p95 | max | truncation rate (= hit max_new_tokens) | explicit 'Answer:' rate |
|---|---|---|---|---|---|---|---|---|---|
| Qwen/Qwen2.5-0.5B-Instruct | 48 | 0.146 | 0.214 (n=28) | 0.050 (n=20) | 425.3 ± 90.7 | 512 | 512 | 0.417 | 0.000 |
| Qwen/Qwen2.5-1.5B-Instruct | 48 | 0.438 | 0.536 (n=28) | 0.300 (n=20) | 414.3 ± 90.4 | 512 | 512 | 0.292 | 0.312 |

Long tasks: max_new_tokens=512, bf16 on CPU (AMX), greedy, prompt 'solve step by step … Answer: <integer>'.

## Market: normal budget (budget multiplier ×3.0; full summary: `results/long_math/summary.md`)

| policy | task accuracy | Σ expected cost | Σ actual cost | gap (rel) | purchases with overrun | rel. overrun mean / p95 / max | budget violations (purchases) | buyers over budget | max overshoot | budget-exhausted tasks |
|---|---|---|---|---|---|---|---|---|---|---|
| single_cheapest_compliant | 0.289 ± 0.051 | 3.263 | 3.999 | +0.736 (+22.7%) | 394/432 | +72.1% / +152.3% / +219.0% | 0 | 0.0 | 0.0000 | 0.0 |
| single_best_compliant | 0.192 ± 0.011 | 10.220 | 10.525 | +0.305 (+3.0%) | 245/416 | +7.2% / +23.6% / +173.0% | 0 | 0.0 | 0.0000 | 5.3 |
| cascade_compliant | 0.363 ± 0.058 | 14.889 | 15.748 | +0.859 (+5.8%) | 626/866 | +36.4% / +134.0% / +219.0% | 0 | 0.0 | 0.0000 | 0.3 |
| vote_k_compliant | 0.220 ± 0.011 | 17.456 | 18.244 | +0.788 (+4.5%) | 660/950 | +31.8% / +131.5% / +199.0% | 1 | 0.3 | 0.0045 | 4.7 |
| compliance_unaware_cheapest | 0.269 ± 0.021 | 0.890 | 1.707 | +0.817 (+91.8%) | 429/432 | +91.9% / +152.0% / +205.0% | 0 | 0.0 | 0.0000 | 0.0 |
| pilot_compliant | 0.377 ± 0.036 | 8.787 | 9.055 | +0.267 (+3.0%) | 294/432 | +25.9% / +122.4% / +178.0% | 0 | 0.0 | 0.0000 | 0.0 |
| stageroute_compliant | 0.380 ± 0.039 | 8.374 | 8.639 | +0.265 (+3.2%) | 300/432 | +29.4% / +123.4% / +192.0% | 0 | 0.0 | 0.0000 | 0.0 |
| audited_compliance_cascade | 0.366 ± 0.057 | 11.260 | 11.885 | +0.625 (+5.6%) | 533/724 | +42.4% / +137.0% / +219.0% | 0 | 0.0 | 0.0000 | 0.0 |

## Market: tight budget (budget multiplier ×0.5; full summary: `results/long_math_tight/summary.md`)

| policy | task accuracy | Σ expected cost | Σ actual cost | gap (rel) | purchases with overrun | rel. overrun mean / p95 / max | budget violations (purchases) | buyers over budget | max overshoot | budget-exhausted tasks |
|---|---|---|---|---|---|---|---|---|---|---|
| single_cheapest_compliant | 0.269 ± 0.056 | 2.809 | 3.499 | +0.689 (+24.6%) | 373/406 | +74.4% / +153.2% / +219.0% | 3 | 1.0 | 0.0020 | 8.7 |
| single_best_compliant | 0.113 ± 0.017 | 5.655 | 5.854 | +0.198 (+3.5%) | 143/234 | +9.4% / +70.3% / +173.0% | 5 | 1.7 | 0.0182 | 66.0 |
| cascade_compliant | 0.157 ± 0.053 | 5.551 | 5.989 | +0.438 (+7.9%) | 290/375 | +46.4% / +138.6% / +182.0% | 9 | 3.0 | 0.0179 | 71.7 |
| vote_k_compliant | 0.118 ± 0.007 | 5.609 | 5.979 | +0.370 (+6.6%) | 276/367 | +43.5% / +137.7% / +205.0% | 8 | 2.7 | 0.0101 | 76.3 |
| compliance_unaware_cheapest | 0.262 ± 0.022 | 0.871 | 1.669 | +0.798 (+91.6%) | 420/423 | +91.6% / +152.0% / +205.0% | 3 | 1.0 | 0.0050 | 3.0 |
| pilot_compliant | 0.241 ± 0.011 | 5.055 | 5.509 | +0.454 (+9.0%) | 285/359 | +48.0% / +136.1% / +175.0% | 2 | 0.7 | 0.0032 | 24.3 |
| stageroute_compliant | 0.250 ± 0.032 | 5.345 | 5.620 | +0.275 (+5.2%) | 221/299 | +35.9% / +123.1% / +162.0% | 3 | 1.0 | 0.0089 | 44.3 |
| audited_compliance_cascade | 0.157 ± 0.024 | 5.554 | 5.960 | +0.406 (+7.3%) | 294/382 | +46.8% / +139.9% / +205.0% | 10 | 3.3 | 0.0180 | 66.7 |

Overrun counts are summed over seeds; other columns are means over seeds. A purchase is only made if its EXPECTED cost (claimed model's mean tokens) fits the remaining budget, so a budget violation needs a buyer whose remaining budget is below the purchase's ACTUAL cost but above its expected cost — at most a few purchases per buyer at the moment its budget runs out.

## What is real vs simulated

- **Real**: Qwen2.5-1.5B / 0.5B-Instruct outputs (local CPU inference, cached), their correctness against gold, reasoning-token counts and measured generation times on CPU; the GSM8K / MATH-500 long-task problems and golds. v4 token theft truncates these REAL cached outputs (character-proportional cut, answer re-parsed) - no new generation is run; the optional length-audit reference cross-check compares against the REAL cached greedy generation of the claimed model.
- **Simulated**: prices, serving costs (and the swap cost gap), latency noise and corridor penalties/fees, jurisdictions and the (simplified, NOT legal advice) compliance rules, buyers / budgets / sensitivities / consent, audits and BOTH detectors (identity check succeeding with prob d, length audit with prob d_length; miss / false-negative rates 1 - d, false positives 0), penalties / stake slashing / delisting, the strategic seller's learning rule and attack choice, the mock seller (seller_br, MockLLM), its confidence and its truncation model.

_total experiment time 80.4s_
