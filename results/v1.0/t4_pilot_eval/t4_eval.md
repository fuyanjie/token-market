# T4 seller risk ranking (protocol §5)

Export: `results/v1.0/t4_pilot_eval/export`. Bootstrap: official = mean of per-test-run scores; CI resamples test runs, percentile 95%. pooled_* averages sellers across test runs and is not protocol., B = 2000. Official numbers are the mean of per-test-run scores (runs where the metric is defined). `n scored` is how many test runs entered that average. Rule = low quoted price + billed-tokens anomaly within (run, declared model) peers; it uses no latency, so its full/no-latency difference is 0 by construction.

| attack type | model | metric | n test (pos) | n scored / runs | 7 items | 6 items (no latency) | Δ (7 − 6) | 95% CI |
|---|---|---|---|---|---|---|---|---|
| swap | logreg | auroc | 215 (18) | 6 / 6 | 0.976 | 0.912 | +0.065 | [-0.019, +0.158] |
| swap | logreg | ap | 215 (18) | 6 / 6 | 0.896 | 0.711 | +0.185 | [+0.018, +0.409] |
| swap | logreg | p_at_10 | 215 (18) | 6 / 6 | 0.283 | 0.267 | +0.017 | [-0.033, +0.067] |
| swap | gbdt | auroc | 215 (18) | 6 / 6 | 0.978 | 0.928 | +0.050 | [+0.006, +0.104] |
| swap | gbdt | ap | 215 (18) | 6 / 6 | 0.867 | 0.732 | +0.134 | [+0.051, +0.210] |
| swap | gbdt | p_at_10 | 215 (18) | 6 / 6 | 0.300 | 0.267 | +0.033 | [+0.000, +0.067] |
| swap | rule | auroc | 215 (18) | 6 / 6 | 0.706 | 0.706 | +0.000 | [+0.000, +0.000] |
| swap | rule | ap | 215 (18) | 6 / 6 | 0.393 | 0.393 | +0.000 | [+0.000, +0.000] |
| swap | rule | p_at_10 | 215 (18) | 6 / 6 | 0.167 | 0.167 | +0.000 | [+0.000, +0.000] |
| theft | logreg | auroc | 215 (18) | 6 / 6 | 0.995 | 0.974 | +0.021 | [+0.005, +0.041] |
| theft | logreg | ap | 215 (18) | 6 / 6 | 0.972 | 0.881 | +0.091 | [+0.026, +0.161] |
| theft | logreg | p_at_10 | 215 (18) | 6 / 6 | 0.300 | 0.300 | +0.000 | [+0.000, +0.000] |
| theft | gbdt | auroc | 215 (18) | 6 / 6 | 1.000 | 0.949 | +0.051 | [+0.003, +0.132] |
| theft | gbdt | ap | 215 (18) | 6 / 6 | 1.000 | 0.891 | +0.109 | [+0.028, +0.193] |
| theft | gbdt | p_at_10 | 215 (18) | 6 / 6 | 0.300 | 0.283 | +0.017 | [+0.000, +0.050] |
| theft | rule | auroc | 215 (18) | 6 / 6 | 0.616 | 0.616 | +0.000 | [+0.000, +0.000] |
| theft | rule | ap | 215 (18) | 6 / 6 | 0.208 | 0.208 | +0.000 | [+0.000, +0.000] |
| theft | rule | p_at_10 | 215 (18) | 6 / 6 | 0.117 | 0.117 | +0.000 | [+0.000, +0.000] |
| downgrade | logreg | auroc | 215 (13) | 6 / 6 | 0.826 | 0.682 | +0.144 | [-0.024, +0.301] |
| downgrade | logreg | ap | 215 (13) | 6 / 6 | 0.458 | 0.271 | +0.187 | [+0.001, +0.383] |
| downgrade | logreg | p_at_10 | 215 (13) | 6 / 6 | 0.167 | 0.117 | +0.050 | [-0.033, +0.133] |
| downgrade | gbdt | auroc | 215 (13) | 6 / 6 | 0.861 | 0.670 | +0.191 | [+0.035, +0.338] |
| downgrade | gbdt | ap | 215 (13) | 6 / 6 | 0.518 | 0.232 | +0.286 | [+0.104, +0.500] |
| downgrade | gbdt | p_at_10 | 215 (13) | 6 / 6 | 0.200 | 0.100 | +0.100 | [+0.067, +0.150] |
| downgrade | rule | auroc | 215 (13) | 6 / 6 | 0.713 | 0.713 | +0.000 | [+0.000, +0.000] |
| downgrade | rule | ap | 215 (13) | 6 / 6 | 0.227 | 0.227 | +0.000 | [+0.000, +0.000] |
| downgrade | rule | p_at_10 | 215 (13) | 6 / 6 | 0.117 | 0.117 | +0.000 | [+0.000, +0.000] |
| any | logreg | auroc | 215 (49) | 6 / 6 | 0.970 | 0.895 | +0.074 | [+0.039, +0.108] |
| any | logreg | ap | 215 (49) | 6 / 6 | 0.931 | 0.772 | +0.159 | [+0.075, +0.236] |
| any | logreg | p_at_10 | 215 (49) | 6 / 6 | 0.750 | 0.583 | +0.167 | [+0.083, +0.233] |
| any | gbdt | auroc | 215 (49) | 6 / 6 | 0.976 | 0.941 | +0.035 | [+0.017, +0.051] |
| any | gbdt | ap | 215 (49) | 6 / 6 | 0.946 | 0.859 | +0.087 | [+0.036, +0.136] |
| any | gbdt | p_at_10 | 215 (49) | 6 / 6 | 0.783 | 0.650 | +0.133 | [+0.100, +0.167] |
| any | rule | auroc | 215 (49) | 6 / 6 | 0.703 | 0.703 | +0.000 | [+0.000, +0.000] |
| any | rule | ap | 215 (49) | 6 / 6 | 0.493 | 0.493 | +0.000 | [+0.000, +0.000] |
| any | rule | p_at_10 | 215 (49) | 6 / 6 | 0.400 | 0.400 | +0.000 | [+0.000, +0.000] |

## Pooled-over-sellers (not protocol, appendix only)

These figures rank sellers from all test runs together. They are not the official numbers.

| attack type | model | metric | pooled 7 items | pooled 6 items | pooled Δ |
|---|---|---|---|---|---|
| swap | logreg | auroc | 0.984 | 0.908 | +0.077 |
| swap | logreg | ap | 0.933 | 0.643 | +0.290 |
| swap | logreg | p_at_10 | 1.000 | 0.700 | +0.300 |
| swap | gbdt | auroc | 0.980 | 0.926 | +0.054 |
| swap | gbdt | ap | 0.888 | 0.663 | +0.225 |
| swap | gbdt | p_at_10 | 1.000 | 0.900 | +0.100 |
| swap | rule | auroc | 0.708 | 0.708 | +0.000 |
| swap | rule | ap | 0.283 | 0.283 | +0.000 |
| swap | rule | p_at_10 | 0.400 | 0.400 | +0.000 |
| theft | logreg | auroc | 0.996 | 0.974 | +0.022 |
| theft | logreg | ap | 0.977 | 0.883 | +0.093 |
| theft | logreg | p_at_10 | 1.000 | 1.000 | +0.000 |
| theft | gbdt | auroc | 0.999 | 0.949 | +0.050 |
| theft | gbdt | ap | 0.991 | 0.885 | +0.106 |
| theft | gbdt | p_at_10 | 1.000 | 1.000 | +0.000 |
| theft | rule | auroc | 0.629 | 0.629 | +0.000 |
| theft | rule | ap | 0.143 | 0.143 | +0.000 |
| theft | rule | p_at_10 | 0.100 | 0.100 | +0.000 |
| downgrade | logreg | auroc | 0.848 | 0.707 | +0.141 |
| downgrade | logreg | ap | 0.429 | 0.154 | +0.276 |
| downgrade | logreg | p_at_10 | 0.500 | 0.200 | +0.300 |
| downgrade | gbdt | auroc | 0.887 | 0.704 | +0.182 |
| downgrade | gbdt | ap | 0.464 | 0.153 | +0.311 |
| downgrade | gbdt | p_at_10 | 0.500 | 0.300 | +0.200 |
| downgrade | rule | auroc | 0.677 | 0.677 | +0.000 |
| downgrade | rule | ap | 0.106 | 0.106 | +0.000 |
| downgrade | rule | p_at_10 | 0.000 | 0.000 | +0.000 |
| any | logreg | auroc | 0.973 | 0.895 | +0.078 |
| any | logreg | ap | 0.924 | 0.735 | +0.189 |
| any | logreg | p_at_10 | 1.000 | 1.000 | +0.000 |
| any | gbdt | auroc | 0.980 | 0.949 | +0.031 |
| any | gbdt | ap | 0.949 | 0.855 | +0.094 |
| any | gbdt | p_at_10 | 1.000 | 1.000 | +0.000 |
| any | rule | auroc | 0.704 | 0.704 | +0.000 |
| any | rule | ap | 0.431 | 0.431 | +0.000 |
| any | rule | p_at_10 | 0.500 | 0.500 | +0.000 |
