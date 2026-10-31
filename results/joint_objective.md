# Joint objective — main comparison (v4 headline)

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

## Appendix — raw-accuracy table (secondary; same runs)

| policy | task accuracy | total cost incl. audit | of which audit | compliance violations | swapped share | theft share | swaps / thefts detected | buyer overpayment | buyer surplus | budget violations |
|---|---|---|---|---|---|---|---|---|---|---|
| stageroute | 0.868 | 12.313 | 0.000 | 61.3 | 0.006 | 0.010 | 0.0 / 0.0 | 0.079 | 19.980 | 0.0 |
| pilot | 0.853 | 12.003 | 0.000 | 65.7 | 0.037 | 0.025 | 0.0 / 0.0 | 0.205 | 19.797 | 0.0 |
| stageroute_compliant | 0.822 | 11.031 | 0.000 | 0.0 | 0.018 | 0.018 | 0.0 / 0.0 | 0.148 | 19.622 | 0.0 |
| audited_compliance_cascade | 0.817 | 12.748 | 0.241 | 0.0 | 0.061 | 0.090 | 3.0 / 4.3 | 1.062 | 17.842 | 0.0 |
| pilot_compliant | 0.811 | 11.074 | 0.000 | 0.0 | 0.038 | 0.031 | 0.0 / 0.0 | 0.249 | 19.182 | 0.0 |
| cascade_compliant | 0.783 | 15.406 | 0.000 | 0.0 | 0.269 | 0.259 | 0.0 / 0.0 | 3.549 | 14.081 | 0.7 |
| compliance_unaware_cheapest | 0.627 | 3.486 | 0.000 | 103.3 | 0.000 | 0.000 | 0.0 / 0.0 | 0.000 | 19.594 | 0.0 |
| single_cheapest_compliant | 0.623 | 5.544 | 0.000 | 0.0 | 0.067 | 0.067 | 0.0 / 0.0 | 0.556 | 17.499 | 0.0 |
| vote_k_compliant | 0.482 | 20.360 | 0.000 | 0.0 | 0.312 | 0.315 | 0.0 / 0.0 | 5.223 | -1.766 | 0.0 |
| single_best_compliant | 0.222 | 11.175 | 0.000 | 0.0 | 0.742 | 0.754 | 0.0 / 0.0 | 5.668 | -2.162 | 0.0 |

The v3 swap-only comparison (raw accuracy, now also with a J column) is kept in results/baselines.md; the v3 accuracy-vs-cost curves in results/cost_curves.md.
