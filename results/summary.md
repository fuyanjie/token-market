# token-market v1 — simulation summary

> Simplified simulation of data-transfer rules; NOT legal advice.

backend=`mock`, seeds=[0, 1, 2], tasks/run=300, auction=`second_price`, log lines=5400, elapsed=0.19s. Values are mean ± std over seeds.

## Mechanism × policy

| mechanism | policy | fill rate | accuracy | total cost | fees | mean lat (ms) | p95 lat (ms) | blocked | violations through | cross-border share | fraud exposure | fraud acc gap | buyer surplus | seller profit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| posted_price | cheapest | 0.794 ± 0.017 | 0.755 ± 0.019 | 2.294 ± 0.055 | 0.0602 ± 0.0017 | 1015 ± 3 | 1704 ± 22 | 61.0 ± 5.3 | 0 ± 0 | 0.631 ± 0.010 | 0.475 ± 0.005 | 0.278 ± 0.048 | 10.889 ± 0.162 | 1.107 ± 0.023 |
| posted_price | quality_per_cost | 0.819 ± 0.002 | 0.737 ± 0.024 | 2.416 ± 0.024 | 0.0597 ± 0.0028 | 988 ± 2 | 1677 ± 61 | 53.7 ± 0.6 | 0 ± 0 | 0.598 ± 0.005 | 0.488 ± 0.001 | 0.267 ± 0.039 | 10.967 ± 0.551 | 1.160 ± 0.012 |
| posted_price | compliance_aware | 0.987 ± 0.009 | 0.779 ± 0.019 | 3.995 ± 0.198 | 0.0610 ± 0.0006 | 979 ± 13 | 1638 ± 15 | 0.0 ± 0.0 | 0 ± 0 | 0.500 ± 0.002 | 0.405 ± 0.004 | 0.298 ± 0.047 | 13.837 ± 0.444 | 1.793 ± 0.081 |
| sealed_bid | cheapest | 0.757 ± 0.015 | 0.714 ± 0.030 | 3.069 ± 0.106 | 0.0768 ± 0.0026 | 966 ± 10 | 1642 ± 67 | 54.0 ± 0.0 | 0 ± 0 | 0.597 ± 0.032 | 0.529 ± 0.010 | 0.304 ± 0.034 | 9.081 ± 0.465 | 1.980 ± 0.069 |
| sealed_bid | quality_per_cost | 0.753 ± 0.013 | 0.713 ± 0.053 | 2.996 ± 0.045 | 0.0754 ± 0.0056 | 964 ± 7 | 1643 ± 52 | 52.7 ± 0.6 | 0 ± 0 | 0.598 ± 0.025 | 0.531 ± 0.009 | 0.302 ± 0.066 | 9.145 ± 1.066 | 1.908 ± 0.019 |
| sealed_bid | compliance_aware | 0.928 ± 0.008 | 0.753 ± 0.024 | 5.802 ± 0.191 | 0.0857 ± 0.0029 | 960 ± 8 | 1637 ± 26 | 0.0 ± 0.0 | 0 ± 0 | 0.491 ± 0.011 | 0.431 ± 0.004 | 0.332 ± 0.040 | 10.552 ± 0.254 | 3.745 ± 0.110 |

## Buyer surplus per buyer

| combo | buyer_br_1 | buyer_br_2 | buyer_cn_1 | buyer_cn_2 | buyer_sg_1 | buyer_sg_2 |
|---|---|---|---|---|---|---|
| posted_price/cheapest | 2.129 ± 0.139 | 2.112 ± 0.032 | 1.268 ± 0.421 | 1.451 ± 0.224 | 2.151 ± 0.125 | 1.778 ± 0.249 |
| posted_price/quality_per_cost | 2.045 ± 0.165 | 1.872 ± 0.066 | 1.452 ± 0.313 | 1.657 ± 0.453 | 2.322 ± 0.240 | 1.619 ± 0.178 |
| posted_price/compliance_aware | 2.224 ± 0.339 | 1.941 ± 0.099 | 2.440 ± 0.382 | 3.286 ± 0.223 | 2.385 ± 0.453 | 1.562 ± 0.108 |
| sealed_bid/cheapest | 1.618 ± 0.243 | 1.801 ± 0.163 | 1.299 ± 0.215 | 1.451 ± 0.312 | 2.346 ± 0.150 | 0.567 ± 0.284 |
| sealed_bid/quality_per_cost | 1.781 ± 0.304 | 1.663 ± 0.048 | 1.441 ± 0.175 | 1.535 ± 0.388 | 2.219 ± 0.256 | 0.506 ± 0.343 |
| sealed_bid/compliance_aware | 1.856 ± 0.318 | 1.602 ± 0.157 | 2.002 ± 0.127 | 2.526 ± 0.081 | 1.900 ± 0.317 | 0.666 ± 0.157 |

## Seller profit per seller

| combo | seller_br | seller_cn | seller_sg |
|---|---|---|---|
| posted_price/cheapest | 0.538 ± 0.007 | 0.060 ± 0.017 | 0.509 ± 0.004 |
| posted_price/quality_per_cost | 0.548 ± 0.003 | 0.092 ± 0.008 | 0.520 ± 0.008 |
| posted_price/compliance_aware | 0.532 ± 0.006 | 0.736 ± 0.071 | 0.525 ± 0.009 |
| sealed_bid/cheapest | 1.484 ± 0.093 | 0.140 ± 0.025 | 0.356 ± 0.018 |
| sealed_bid/quality_per_cost | 1.330 ± 0.040 | 0.142 ± 0.023 | 0.436 ± 0.005 |
| sealed_bid/compliance_aware | 1.649 ± 0.025 | 1.584 ± 0.138 | 0.512 ± 0.012 |

## Blocked attempts by rule

| combo | BR-LGPD-33-VIII | CN-DSL-31 | CN-PIPL-38 | CN-PIPL-40 |
|---|---|---|---|---|
| posted_price/cheapest | 7.667 ± 3.786 | 25.000 ± 4.583 | 15.667 ± 2.517 | 12.667 ± 2.082 |
| posted_price/quality_per_cost | 6.333 ± 3.215 | 25.000 ± 4.583 | 9.667 ± 2.887 | 12.667 ± 2.082 |
| posted_price/compliance_aware | 0 | 0 | 0 | 0 |
| sealed_bid/cheapest | 7.000 ± 3.606 | 25.000 ± 4.583 | 9.333 ± 1.528 | 12.667 ± 2.082 |
| sealed_bid/quality_per_cost | 6.667 ± 3.055 | 25.000 ± 4.583 | 8.333 ± 0.577 | 12.667 ± 2.082 |
| sealed_bid/compliance_aware | 0 | 0 | 0 | 0 |

## Notes

- fraud exposure = share of allowed tx served by a seller whose actual_model != claimed_model (seller_sg: sim-strong-r1 -> sim-weak-r1).
- fraud acc gap = expected accuracy of the claimed model on those tasks minus realised accuracy.
- blocked = attempts stopped by the gateway's compliance rules; violations through = allowed flows that fail an independent re-audit (should be 0).
- buyer surplus = value_per_correct * correct - cost - fee; seller profit = revenue - actual serving cost.
