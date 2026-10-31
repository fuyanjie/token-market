# A — accuracy vs cost curves

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

## All points

| family | knob | cost/task (incl. audit) | accuracy | budget viol. | compliance viol. | fraud-seller share |
|---|---|---|---|---|---|---|
| single_cheapest_compliant | budget×0.2 | 0.0050 ± 0.0000 | 0.337 ± 0.009 | 2.0 | 0.0 | 0.025 |
| single_cheapest_compliant | budget×0.4 | 0.0082 ± 0.0001 | 0.503 ± 0.008 | 0.3 | 0.0 | 0.036 |
| single_cheapest_compliant | budget×0.6 | 0.0104 ± 0.0002 | 0.604 ± 0.010 | 1.0 | 0.0 | 0.060 |
| single_cheapest_compliant | budget×1.0 | 0.0114 ± 0.0006 | 0.651 ± 0.019 | 0.3 | 0.0 | 0.063 |
| single_cheapest_compliant | budget×1.5 | 0.0116 ± 0.0006 | 0.665 ± 0.019 | 0.0 | 0.0 | 0.061 |
| single_cheapest_compliant | budget×2.0 | 0.0116 ± 0.0006 | 0.665 ± 0.019 | 0.0 | 0.0 | 0.061 |
| single_cheapest_compliant | budget×3.0 | 0.0116 ± 0.0006 | 0.665 ± 0.019 | 0.0 | 0.0 | 0.061 |
| single_cheapest_compliant | budget×5.0 | 0.0116 ± 0.0006 | 0.665 ± 0.019 | 0.0 | 0.0 | 0.061 |
| single_best_compliant | budget×0.2 | 0.0049 ± 0.0001 | 0.134 ± 0.007 | 1.7 | 0.0 | 0.685 |
| single_best_compliant | budget×0.4 | 0.0099 ± 0.0000 | 0.272 ± 0.014 | 0.7 | 0.0 | 0.713 |
| single_best_compliant | budget×0.6 | 0.0149 ± 0.0000 | 0.396 ± 0.013 | 1.3 | 0.0 | 0.726 |
| single_best_compliant | budget×1.0 | 0.0228 ± 0.0003 | 0.605 ± 0.016 | 0.3 | 0.0 | 0.751 |
| single_best_compliant | budget×1.5 | 0.0237 ± 0.0004 | 0.623 ± 0.010 | 0.0 | 0.0 | 0.762 |
| single_best_compliant | budget×2.0 | 0.0242 ± 0.0005 | 0.634 ± 0.008 | 0.0 | 0.0 | 0.766 |
| single_best_compliant | budget×3.0 | 0.0253 ± 0.0005 | 0.660 ± 0.006 | 0.0 | 0.0 | 0.771 |
| single_best_compliant | budget×5.0 | 0.0265 ± 0.0004 | 0.693 ± 0.006 | 0.0 | 0.0 | 0.781 |
| cascade_compliant | budget×0.2 | 0.0050 ± 0.0000 | 0.143 ± 0.003 | 3.3 | 0.0 | 0.246 |
| cascade_compliant | budget×0.4 | 0.0100 ± 0.0000 | 0.265 ± 0.027 | 1.3 | 0.0 | 0.278 |
| cascade_compliant | budget×0.6 | 0.0150 ± 0.0000 | 0.403 ± 0.011 | 2.0 | 0.0 | 0.280 |
| cascade_compliant | budget×1.0 | 0.0248 ± 0.0002 | 0.651 ± 0.015 | 2.0 | 0.0 | 0.292 |
| cascade_compliant | budget×1.5 | 0.0289 ± 0.0002 | 0.752 ± 0.012 | 0.7 | 0.0 | 0.295 |
| cascade_compliant | budget×2.0 | 0.0290 ± 0.0001 | 0.768 ± 0.011 | 0.0 | 0.0 | 0.302 |
| cascade_compliant | budget×3.0 | 0.0306 ± 0.0009 | 0.799 ± 0.007 | 0.0 | 0.0 | 0.300 |
| cascade_compliant | budget×5.0 | 0.0310 ± 0.0007 | 0.822 ± 0.012 | 0.0 | 0.0 | 0.303 |
| pilot | budget×0.2 | 0.0049 ± 0.0000 | 0.307 ± 0.009 | 1.0 | 54.0 | 0.038 |
| pilot | budget×0.4 | 0.0099 ± 0.0000 | 0.544 ± 0.022 | 1.3 | 84.7 | 0.073 |
| pilot | budget×0.6 | 0.0139 ± 0.0003 | 0.666 ± 0.026 | 0.7 | 86.0 | 0.080 |
| pilot | budget×1.0 | 0.0203 ± 0.0002 | 0.788 ± 0.019 | 0.7 | 69.3 | 0.170 |
| pilot | budget×1.5 | 0.0239 ± 0.0003 | 0.860 ± 0.013 | 0.3 | 71.7 | 0.193 |
| pilot | budget×2.0 | 0.0238 ± 0.0002 | 0.883 ± 0.019 | 0.0 | 77.7 | 0.235 |
| pilot | budget×3.0 | 0.0252 ± 0.0008 | 0.896 ± 0.010 | 0.0 | 73.7 | 0.242 |
| pilot | budget×5.0 | 0.0253 ± 0.0005 | 0.894 ± 0.015 | 0.0 | 77.3 | 0.287 |
| pilot_compliant | budget×0.2 | 0.0049 ± 0.0000 | 0.256 ± 0.014 | 0.3 | 0.0 | 0.089 |
| pilot_compliant | budget×0.4 | 0.0099 ± 0.0000 | 0.462 ± 0.019 | 0.3 | 0.0 | 0.129 |
| pilot_compliant | budget×0.6 | 0.0145 ± 0.0002 | 0.624 ± 0.003 | 0.3 | 0.0 | 0.134 |
| pilot_compliant | budget×1.0 | 0.0208 ± 0.0003 | 0.772 ± 0.012 | 0.7 | 0.0 | 0.203 |
| pilot_compliant | budget×1.5 | 0.0228 ± 0.0004 | 0.831 ± 0.006 | 0.7 | 0.0 | 0.208 |
| pilot_compliant | budget×2.0 | 0.0233 ± 0.0007 | 0.856 ± 0.013 | 0.0 | 0.0 | 0.215 |
| pilot_compliant | budget×3.0 | 0.0246 ± 0.0001 | 0.871 ± 0.008 | 0.0 | 0.0 | 0.257 |
| pilot_compliant | budget×5.0 | 0.0246 ± 0.0008 | 0.876 ± 0.003 | 0.0 | 0.0 | 0.283 |
| stageroute | budget×0.2 | 0.0049 ± 0.0001 | 0.154 ± 0.009 | 1.0 | 9.3 | 0.153 |
| stageroute | budget×0.4 | 0.0099 ± 0.0000 | 0.302 ± 0.008 | 1.0 | 25.3 | 0.135 |
| stageroute | budget×0.6 | 0.0149 ± 0.0001 | 0.469 ± 0.017 | 1.0 | 36.7 | 0.083 |
| stageroute | budget×1.0 | 0.0237 ± 0.0003 | 0.754 ± 0.023 | 0.3 | 59.7 | 0.061 |
| stageroute | budget×1.5 | 0.0258 ± 0.0002 | 0.828 ± 0.044 | 0.0 | 61.3 | 0.070 |
| stageroute | budget×2.0 | 0.0261 ± 0.0003 | 0.837 ± 0.037 | 0.0 | 61.3 | 0.085 |
| stageroute | budget×3.0 | 0.0268 ± 0.0009 | 0.854 ± 0.022 | 0.0 | 61.3 | 0.106 |
| stageroute | budget×5.0 | 0.0275 ± 0.0015 | 0.875 ± 0.004 | 0.0 | 61.3 | 0.126 |
| stageroute_compliant | budget×0.2 | 0.0049 ± 0.0000 | 0.169 ± 0.021 | 0.7 | 0.0 | 0.153 |
| stageroute_compliant | budget×0.4 | 0.0099 ± 0.0000 | 0.340 ± 0.023 | 1.3 | 0.0 | 0.130 |
| stageroute_compliant | budget×0.6 | 0.0149 ± 0.0001 | 0.507 ± 0.048 | 1.0 | 0.0 | 0.107 |
| stageroute_compliant | budget×1.0 | 0.0224 ± 0.0003 | 0.749 ± 0.031 | 1.0 | 0.0 | 0.093 |
| stageroute_compliant | budget×1.5 | 0.0236 ± 0.0009 | 0.786 ± 0.039 | 0.7 | 0.0 | 0.103 |
| stageroute_compliant | budget×2.0 | 0.0240 ± 0.0012 | 0.797 ± 0.030 | 0.0 | 0.0 | 0.116 |
| stageroute_compliant | budget×3.0 | 0.0246 ± 0.0018 | 0.821 ± 0.015 | 0.0 | 0.0 | 0.132 |
| stageroute_compliant | budget×5.0 | 0.0251 ± 0.0023 | 0.832 ± 0.001 | 0.0 | 0.0 | 0.146 |
| audited_compliance_cascade | budget×0.2 | 0.0050 ± 0.0000 | 0.153 ± 0.010 | 2.7 | 0.0 | 0.098 |
| audited_compliance_cascade | budget×0.4 | 0.0100 ± 0.0000 | 0.317 ± 0.019 | 1.7 | 0.0 | 0.040 |
| audited_compliance_cascade | budget×0.6 | 0.0150 ± 0.0000 | 0.481 ± 0.010 | 1.3 | 0.0 | 0.051 |
| audited_compliance_cascade | budget×1.0 | 0.0234 ± 0.0002 | 0.742 ± 0.017 | 0.3 | 0.0 | 0.059 |
| audited_compliance_cascade | budget×1.5 | 0.0247 ± 0.0008 | 0.790 ± 0.008 | 0.0 | 0.0 | 0.036 |
| audited_compliance_cascade | budget×2.0 | 0.0250 ± 0.0008 | 0.811 ± 0.010 | 0.3 | 0.0 | 0.042 |
| audited_compliance_cascade | budget×3.0 | 0.0261 ± 0.0011 | 0.850 ± 0.002 | 0.7 | 0.0 | 0.041 |
| audited_compliance_cascade | budget×5.0 | 0.0268 ± 0.0008 | 0.877 ± 0.011 | 0.0 | 0.0 | 0.040 |
| cascade_compliant (threshold) | thr=0.1 | 0.0117 ± 0.0006 | 0.667 ± 0.018 | 0.0 | 0.0 | 0.064 |
| cascade_compliant (threshold) | thr=0.3 | 0.0151 ± 0.0011 | 0.709 ± 0.014 | 0.0 | 0.0 | 0.111 |
| cascade_compliant (threshold) | thr=0.5 | 0.0218 ± 0.0011 | 0.787 ± 0.013 | 0.0 | 0.0 | 0.208 |
| cascade_compliant (threshold) | thr=0.7 | 0.0310 ± 0.0007 | 0.822 ± 0.012 | 0.0 | 0.0 | 0.303 |
| cascade_compliant (threshold) | thr=0.8 | 0.0358 ± 0.0012 | 0.817 ± 0.010 | 0.0 | 0.0 | 0.343 |
| cascade_compliant (threshold) | thr=0.95 | 0.0469 ± 0.0009 | 0.842 ± 0.002 | 0.3 | 0.0 | 0.329 |
| vote_k_compliant (k) | k=1 | 0.0265 ± 0.0004 | 0.693 ± 0.006 | 0.0 | 0.0 | 0.781 |
| vote_k_compliant k=1 | budget×0.2 | 0.0049 ± 0.0001 | 0.134 ± 0.007 | 1.7 | 0.0 | 0.685 |
| vote_k_compliant k=1 | budget×0.4 | 0.0099 ± 0.0000 | 0.272 ± 0.014 | 0.7 | 0.0 | 0.713 |
| vote_k_compliant k=1 | budget×0.6 | 0.0149 ± 0.0000 | 0.396 ± 0.013 | 1.3 | 0.0 | 0.726 |
| vote_k_compliant k=1 | budget×1.0 | 0.0228 ± 0.0003 | 0.605 ± 0.016 | 0.3 | 0.0 | 0.751 |
| vote_k_compliant k=1 | budget×1.5 | 0.0237 ± 0.0004 | 0.623 ± 0.010 | 0.0 | 0.0 | 0.762 |
| vote_k_compliant k=1 | budget×2.0 | 0.0242 ± 0.0005 | 0.634 ± 0.008 | 0.0 | 0.0 | 0.766 |
| vote_k_compliant k=1 | budget×3.0 | 0.0253 ± 0.0005 | 0.660 ± 0.006 | 0.0 | 0.0 | 0.771 |
| vote_k_compliant k=1 | budget×5.0 | 0.0265 ± 0.0004 | 0.693 ± 0.006 | 0.0 | 0.0 | 0.781 |
| vote_k_compliant (k) | k=2 | 0.0449 ± 0.0007 | 0.703 ± 0.013 | 0.0 | 0.0 | 0.427 |
| vote_k_compliant k=2 | budget×0.2 | 0.0049 ± 0.0000 | 0.089 ± 0.004 | 0.7 | 0.0 | 0.361 |
| vote_k_compliant k=2 | budget×0.4 | 0.0100 ± 0.0001 | 0.172 ± 0.009 | 2.3 | 0.0 | 0.386 |
| vote_k_compliant k=2 | budget×0.6 | 0.0150 ± 0.0000 | 0.253 ± 0.009 | 2.7 | 0.0 | 0.401 |
| vote_k_compliant k=2 | budget×1.0 | 0.0250 ± 0.0000 | 0.407 ± 0.024 | 2.0 | 0.0 | 0.406 |
| vote_k_compliant k=2 | budget×1.5 | 0.0364 ± 0.0003 | 0.576 ± 0.011 | 1.0 | 0.0 | 0.415 |
| vote_k_compliant k=2 | budget×2.0 | 0.0407 ± 0.0004 | 0.633 ± 0.009 | 0.7 | 0.0 | 0.421 |
| vote_k_compliant k=2 | budget×3.0 | 0.0429 ± 0.0007 | 0.662 ± 0.017 | 0.0 | 0.0 | 0.423 |
| vote_k_compliant k=2 | budget×5.0 | 0.0449 ± 0.0007 | 0.703 ± 0.013 | 0.0 | 0.0 | 0.427 |
| vote_k_compliant (k) | k=3 | 0.0485 ± 0.0008 | 0.778 ± 0.012 | 0.0 | 0.0 | 0.336 |
| vote_k_compliant k=3 | budget×0.2 | 0.0050 ± 0.0000 | 0.098 ± 0.004 | 1.7 | 0.0 | 0.265 |
| vote_k_compliant k=3 | budget×0.4 | 0.0100 ± 0.0000 | 0.174 ± 0.011 | 2.0 | 0.0 | 0.302 |
| vote_k_compliant k=3 | budget×0.6 | 0.0150 ± 0.0000 | 0.258 ± 0.007 | 1.0 | 0.0 | 0.307 |
| vote_k_compliant k=3 | budget×1.0 | 0.0250 ± 0.0000 | 0.411 ± 0.009 | 2.7 | 0.0 | 0.317 |
| vote_k_compliant k=3 | budget×1.5 | 0.0369 ± 0.0003 | 0.606 ± 0.005 | 1.7 | 0.0 | 0.317 |
| vote_k_compliant k=3 | budget×2.0 | 0.0431 ± 0.0003 | 0.690 ± 0.014 | 0.7 | 0.0 | 0.323 |
| vote_k_compliant k=3 | budget×3.0 | 0.0465 ± 0.0009 | 0.732 ± 0.013 | 0.0 | 0.0 | 0.328 |
| vote_k_compliant k=3 | budget×5.0 | 0.0485 ± 0.0008 | 0.778 ± 0.012 | 0.0 | 0.0 | 0.336 |
| audited_compliance_cascade (audit rate) | audit=0.02 | 0.0310 ± 0.0005 | 0.815 ± 0.012 | 0.0 | 0.0 | 0.290 |
| audited_compliance_cascade (audit rate) | audit=0.05 | 0.0285 ± 0.0020 | 0.850 ± 0.021 | 0.0 | 0.0 | 0.156 |
| audited_compliance_cascade (audit rate) | audit=0.1 | 0.0268 ± 0.0008 | 0.877 ± 0.011 | 0.0 | 0.0 | 0.040 |
| audited_compliance_cascade (audit rate) | audit=0.2 | 0.0272 ± 0.0006 | 0.880 ± 0.009 | 0.0 | 0.0 | 0.028 |
| audited_compliance_cascade (audit rate) | audit=0.3 | 0.0278 ± 0.0005 | 0.880 ± 0.009 | 0.0 | 0.0 | 0.028 |
