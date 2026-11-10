# T4 seller risk ranking (protocol §5)

Export: `/workspace/token-market/results/v1.0/t4_eval/export`. Bootstrap: official = mean of per-test-run scores; CI resamples test runs, percentile 95%. pooled_* averages sellers across test runs and is not protocol., B = 10000. Official numbers are the mean of per-test-run scores (runs where the metric is defined). `n scored` is how many test runs entered that average. Rule = low quoted price + billed-tokens anomaly within (run, declared model) peers; it uses no latency, so its full/no-latency difference is 0 by construction.

| attack type | model | metric | n test (pos) | n scored / runs | 7 items | 6 items (no latency) | Δ (7 − 6) | 95% CI |
|---|---|---|---|---|---|---|---|---|
| swap | logreg | auroc | 89 (1) | 1 / 6 | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] |
| swap | logreg | ap | 89 (1) | 1 / 6 | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] |
| swap | logreg | p_at_10 | 89 (1) | 6 / 6 | 0.017 | 0.017 | +0.000 | [+0.000, +0.000] |
| swap | gbdt | auroc | 89 (1) | 1 / 6 | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] |
| swap | gbdt | ap | 89 (1) | 1 / 6 | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] |
| swap | gbdt | p_at_10 | 89 (1) | 6 / 6 | 0.017 | 0.017 | +0.000 | [+0.000, +0.000] |
| swap | rule | auroc | 89 (1) | 1 / 6 | 0.462 | 0.462 | +0.000 | [+0.000, +0.000] |
| swap | rule | ap | 89 (1) | 1 / 6 | 0.125 | 0.125 | +0.000 | [+0.000, +0.000] |
| swap | rule | p_at_10 | 89 (1) | 6 / 6 | 0.017 | 0.017 | +0.000 | [+0.000, +0.000] |
| theft | logreg | auroc | 89 (1) | 1 / 6 | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] |
| theft | logreg | ap | 89 (1) | 1 / 6 | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] |
| theft | logreg | p_at_10 | 89 (1) | 6 / 6 | 0.017 | 0.017 | +0.000 | [+0.000, +0.000] |
| theft | gbdt | auroc | 89 (1) | 1 / 6 | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] |
| theft | gbdt | ap | 89 (1) | 1 / 6 | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] |
| theft | gbdt | p_at_10 | 89 (1) | 6 / 6 | 0.017 | 0.017 | +0.000 | [+0.000, +0.000] |
| theft | rule | auroc | 89 (1) | 1 / 6 | 0.923 | 0.923 | +0.000 | [+0.000, +0.000] |
| theft | rule | ap | 89 (1) | 1 / 6 | 0.500 | 0.500 | +0.000 | [+0.000, +0.000] |
| theft | rule | p_at_10 | 89 (1) | 6 / 6 | 0.017 | 0.017 | +0.000 | [+0.000, +0.000] |
| any | logreg | auroc | 89 (2) | 2 / 6 | 1.000 | 0.962 | +0.038 | [+0.000, +0.077] |
| any | logreg | ap | 89 (2) | 2 / 6 | 1.000 | 0.750 | +0.250 | [+0.000, +0.500] |
| any | logreg | p_at_10 | 89 (2) | 6 / 6 | 0.033 | 0.033 | +0.000 | [+0.000, +0.000] |
| any | gbdt | auroc | 89 (2) | 2 / 6 | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] |
| any | gbdt | ap | 89 (2) | 2 / 6 | 1.000 | 1.000 | +0.000 | [+0.000, +0.000] |
| any | gbdt | p_at_10 | 89 (2) | 6 / 6 | 0.033 | 0.033 | +0.000 | [+0.000, +0.000] |
| any | rule | auroc | 89 (2) | 2 / 6 | 0.692 | 0.692 | +0.000 | [+0.000, +0.000] |
| any | rule | ap | 89 (2) | 2 / 6 | 0.312 | 0.312 | +0.000 | [+0.000, +0.000] |
| any | rule | p_at_10 | 89 (2) | 6 / 6 | 0.033 | 0.033 | +0.000 | [+0.000, +0.000] |

## Pooled-over-sellers (not protocol, appendix only)

These figures rank sellers from all test runs together. They are not the official numbers.

| attack type | model | metric | pooled 7 items | pooled 6 items | pooled Δ |
|---|---|---|---|---|---|
| swap | logreg | auroc | 1.000 | 1.000 | +0.000 |
| swap | logreg | ap | 1.000 | 1.000 | +0.000 |
| swap | logreg | p_at_10 | 0.100 | 0.100 | +0.000 |
| swap | gbdt | auroc | 0.989 | 0.977 | +0.011 |
| swap | gbdt | ap | 0.500 | 0.333 | +0.167 |
| swap | gbdt | p_at_10 | 0.100 | 0.100 | +0.000 |
| swap | rule | auroc | 0.443 | 0.443 | +0.000 |
| swap | rule | ap | 0.020 | 0.020 | +0.000 |
| swap | rule | p_at_10 | 0.000 | 0.000 | +0.000 |
| theft | logreg | auroc | 0.977 | 0.955 | +0.023 |
| theft | logreg | ap | 0.333 | 0.200 | +0.133 |
| theft | logreg | p_at_10 | 0.100 | 0.100 | +0.000 |
| theft | gbdt | auroc | 0.977 | 0.989 | -0.011 |
| theft | gbdt | ap | 0.333 | 0.500 | -0.167 |
| theft | gbdt | p_at_10 | 0.100 | 0.100 | +0.000 |
| theft | rule | auroc | 0.955 | 0.955 | +0.000 |
| theft | rule | ap | 0.200 | 0.200 | +0.000 |
| theft | rule | p_at_10 | 0.100 | 0.100 | +0.000 |
| any | logreg | auroc | 0.977 | 0.937 | +0.040 |
| any | logreg | ap | 0.417 | 0.211 | +0.206 |
| any | logreg | p_at_10 | 0.200 | 0.200 | +0.000 |
| any | gbdt | auroc | 0.989 | 0.966 | +0.023 |
| any | gbdt | ap | 0.583 | 0.393 | +0.190 |
| any | gbdt | p_at_10 | 0.200 | 0.200 | +0.000 |
| any | rule | auroc | 0.701 | 0.701 | +0.000 |
| any | rule | ap | 0.120 | 0.120 | +0.000 |
| any | rule | p_at_10 | 0.100 | 0.100 | +0.000 |

Notes:
- downgrade: skipped (train needs both classes and a non-empty test set): {'attack_type': 'downgrade', 'n_train': 208, 'n_train_pos': 0, 'n_test': 89, 'n_test_pos': 0, 'n_test_runs': 6}
