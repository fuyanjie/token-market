# C — strategic model-swap seller vs buyer audits (fraud / audit threshold)

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
