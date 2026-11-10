# T4 seller risk ranking (protocol §5)

Export: `results/v1.0/t4_eval/export`. Bootstrap: cluster by test run, percentile 95%, B = 2000. Rule = low quoted price + billed-tokens anomaly within (run, declared model) peers; it uses no latency, so its full/no-latency difference is 0 by construction.

| attack type | model | metric | n test (pos) | 7 items | 6 items (no latency) | Δ (7 − 6) | 95% CI |
|---|---|---|---|---|---|---|---|
| swap | logreg | auroc | 89 (1) | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] |
| swap | logreg | ap | 89 (1) | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] |
| swap | logreg | p_at_10 | 89 (1) | 0.100 | 0.100 | +0.000 | [+0.000, +0.000] |
| swap | gbdt | auroc | 89 (1) | 0.989 | 0.977 | +0.011 | [+0.000, +0.035] |
| swap | gbdt | ap | 89 (1) | 0.500 | 0.333 | +0.167 | [+0.000, +0.167] |
| swap | gbdt | p_at_10 | 89 (1) | 0.100 | 0.100 | +0.000 | [+0.000, +0.000] |
| swap | rule | auroc | 89 (1) | 0.443 | 0.443 | +0.000 | [+0.000, +0.000] |
| swap | rule | ap | 89 (1) | 0.020 | 0.020 | +0.000 | [+0.000, +0.000] |
| swap | rule | p_at_10 | 89 (1) | 0.000 | 0.000 | +0.000 | [+0.000, +0.000] |
| theft | logreg | auroc | 89 (1) | 0.977 | 0.955 | +0.023 | [+0.000, +0.045] |
| theft | logreg | ap | 89 (1) | 0.333 | 0.200 | +0.133 | [+0.000, +0.667] |
| theft | logreg | p_at_10 | 89 (1) | 0.100 | 0.100 | +0.000 | [+0.000, +0.000] |
| theft | gbdt | auroc | 89 (1) | 0.977 | 0.989 | -0.011 | [-0.034, +0.000] |
| theft | gbdt | ap | 89 (1) | 0.333 | 0.500 | -0.167 | [-0.675, +0.000] |
| theft | gbdt | p_at_10 | 89 (1) | 0.100 | 0.100 | +0.000 | [+0.000, +0.000] |
| theft | rule | auroc | 89 (1) | 0.955 | 0.955 | +0.000 | [+0.000, +0.000] |
| theft | rule | ap | 89 (1) | 0.200 | 0.200 | +0.000 | [+0.000, +0.000] |
| theft | rule | p_at_10 | 89 (1) | 0.100 | 0.100 | +0.000 | [+0.000, +0.000] |
| any | logreg | auroc | 89 (2) | 0.977 | 0.937 | +0.040 | [+0.011, +0.076] |
| any | logreg | ap | 89 (2) | 0.417 | 0.211 | +0.206 | [+0.075, +0.583] |
| any | logreg | p_at_10 | 89 (2) | 0.200 | 0.200 | +0.000 | [+0.000, +0.100] |
| any | gbdt | auroc | 89 (2) | 0.989 | 0.966 | +0.023 | [+0.000, +0.067] |
| any | gbdt | ap | 89 (2) | 0.583 | 0.393 | +0.190 | [+0.000, +0.804] |
| any | gbdt | p_at_10 | 89 (2) | 0.200 | 0.200 | +0.000 | [+0.000, +0.000] |
| any | rule | auroc | 89 (2) | 0.701 | 0.701 | +0.000 | [+0.000, +0.000] |
| any | rule | ap | 89 (2) | 0.120 | 0.120 | +0.000 | [+0.000, +0.000] |
| any | rule | p_at_10 | 89 (2) | 0.100 | 0.100 | +0.000 | [+0.000, +0.000] |

Notes:
- downgrade: skipped (train needs both classes and a non-empty test set): {'attack_type': 'downgrade', 'n_train': 208, 'n_train_pos': 0, 'n_test': 89, 'n_test_pos': 0}
