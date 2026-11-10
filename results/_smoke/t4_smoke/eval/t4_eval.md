# T4 seller risk ranking (protocol §5)

Export: `results/_smoke/t4_smoke/eval/export`. Bootstrap: cluster by test run, percentile 95%, B = 200. Rule = low quoted price + billed-tokens anomaly within (run, declared model) peers; it uses no latency, so its full/no-latency difference is 0 by construction.

| attack type | model | metric | n test (pos) | 7 items | 6 items (no latency) | Δ (7 − 6) | 95% CI |
|---|---|---|---|---|---|---|---|
| swap | logreg | auroc | 4 (1) | 0.667 | 1.000 | -0.333 | [-0.333, -0.333] |
| swap | logreg | ap | 4 (1) | 0.500 | 1.000 | -0.500 | [-0.500, -0.500] |
| swap | logreg | p_at_10 | 4 (1) | 0.250 | 0.250 | +0.000 | [+0.000, +0.000] |
| swap | gbdt | auroc | 4 (1) | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |
| swap | gbdt | ap | 4 (1) | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |
| swap | gbdt | p_at_10 | 4 (1) | 0.250 | 0.250 | +0.000 | [+0.000, +0.000] |
| swap | rule | auroc | 4 (1) | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] |
| swap | rule | ap | 4 (1) | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] |
| swap | rule | p_at_10 | 4 (1) | 0.250 | 0.250 | +0.000 | [+0.000, +0.000] |
| any | logreg | auroc | 4 (2) | 0.250 | 1.000 | -0.750 | [-0.750, -0.750] |
| any | logreg | ap | 4 (2) | 0.500 | 1.000 | -0.500 | [-0.500, -0.500] |
| any | logreg | p_at_10 | 4 (2) | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |
| any | gbdt | auroc | 4 (2) | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |
| any | gbdt | ap | 4 (2) | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] |
| any | gbdt | p_at_10 | 4 (2) | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |
| any | rule | auroc | 4 (2) | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |
| any | rule | ap | 4 (2) | 0.750 | 0.750 | +0.000 | [+0.000, +0.000] |
| any | rule | p_at_10 | 4 (2) | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |

Notes:
- theft: skipped (train needs both classes and a non-empty test set): {'attack_type': 'theft', 'n_train': 4, 'n_train_pos': 0, 'n_test': 4, 'n_test_pos': 0}
- downgrade: skipped (train needs both classes and a non-empty test set): {'attack_type': 'downgrade', 'n_train': 4, 'n_train_pos': 0, 'n_test': 4, 'n_test_pos': 1}
