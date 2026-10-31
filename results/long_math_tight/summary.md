# token-market v2 — C2 compliance-constrained portfolio purchasing

> Simplified simulation of data-transfer rules; NOT legal advice.

seller backends={'seller_cn': 'local_hf', 'seller_sg': 'local_hf', 'seller_br': 'mock'}, seeds=[0, 1, 2], tasks/run=144 (drawn from fixed pool of 48, task_seed=1234), auction=`second_price`, log lines=5224, precompute=0.0s, market sim=0.51s. Values are mean ± std over seeds.

## C2 baseline comparison (posted price)

| policy | task accuracy | total cost | mean cost/task | purchases/task | expected→actual cost gap | budget violations | compliance violations | blocked/filtered | cross-border share | fraud-seller share | buyer surplus | mean task latency (ms) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single_cheapest_compliant | 0.269 ± 0.056 | 3.499 ± 0.029 | 0.0243 ± 0.0002 | 0.94 ± 0.04 | +0.689 ± +0.029 (+24.6% ± +1.5%) | 1.0 ± 0.0 (0.7% ± 0.0%) | 0.0 ± 0.0 | 79.0 ± 6.6 | 0.522 ± 0.015 | 0.074 ± 0.015 | -0.509 ± 0.606 | 2378 ± 66 |
| single_best_compliant | 0.113 ± 0.017 | 5.854 ± 0.072 | 0.0406 ± 0.0005 | 0.54 ± 0.01 | +0.198 ± +0.083 (+3.5% ± +1.5%) | 1.7 ± 1.2 (2.1% ± 1.4%) | 0.0 ± 0.0 | 79.0 ± 6.6 | 0.526 ± 0.017 | 0.765 ± 0.018 | -4.517 ± 0.232 | 4761 ± 373 |
| cascade_compliant | 0.157 ± 0.053 | 5.989 ± 0.047 | 0.0416 ± 0.0003 | 0.87 ± 0.04 | +0.438 ± +0.082 (+7.9% ± +1.5%) | 3.0 ± 1.7 (2.4% ± 1.2%) | 0.0 ± 0.0 | 79.0 ± 6.6 | 0.560 ± 0.020 | 0.264 ± 0.009 | -4.196 ± 0.520 | 8705 ± 807 |
| vote_k_compliant | 0.118 ± 0.007 | 5.979 ± 0.031 | 0.0415 ± 0.0002 | 0.85 ± 0.03 | +0.370 ± +0.044 (+6.6% ± +0.9%) | 2.7 ± 1.2 (2.2% ± 0.9%) | 0.0 ± 0.0 | 79.0 ± 6.6 | 0.570 ± 0.010 | 0.275 ± 0.007 | -4.612 ± 0.079 | 7803 ± 28 |
| compliance_unaware_cheapest | 0.262 ± 0.022 | 1.669 ± 0.010 | 0.0116 ± 0.0001 | 0.98 ± 0.00 | +0.798 ± +0.010 (+91.6% ± +1.1%) | 1.0 ± 0.0 (0.7% ± 0.0%) | 32.0 ± 5.0 | 0.0 ± 0.0 | 0.660 ± 0.000 | 0.000 ± 0.000 | 1.218 ± 0.258 | 599 ± 8 |
| pilot_compliant | 0.241 ± 0.011 | 5.509 ± 0.172 | 0.0383 ± 0.0012 | 0.83 ± 0.03 | +0.454 ± +0.108 (+9.0% ± +2.0%) | 0.7 ± 0.6 (0.5% ± 0.5%) | 0.0 ± 0.0 | 79.0 ± 6.6 | 0.498 ± 0.027 | 0.090 ± 0.041 | -2.815 ± 0.232 | 5910 ± 182 |
| stageroute_compliant | 0.250 ± 0.032 | 5.620 ± 0.219 | 0.0390 ± 0.0015 | 0.69 ± 0.09 | +0.275 ± +0.119 (+5.2% ± +2.5%) | 1.0 ± 1.0 (1.0% ± 1.1%) | 0.0 ± 0.0 | 79.0 ± 6.6 | 0.584 ± 0.056 | 0.031 ± 0.013 | -2.800 ± 0.532 | 8724 ± 1824 |
| audited_compliance_cascade | 0.157 ± 0.024 | 5.960 ± 0.034 | 0.0414 ± 0.0002 | 0.88 ± 0.09 | +0.406 ± +0.075 (+7.3% ± +1.5%) | 3.3 ± 1.2 (2.7% ± 1.1%) | 0.0 ± 0.0 | 79.0 ± 6.6 | 0.563 ± 0.012 | 0.203 ± 0.075 | -4.238 ± 0.291 | 9259 ± 1465 |

## v4 joint objective J = accuracy − 1.0·violation rate (/task) − 0.5·fraud share (/purchase)

| policy | J | task accuracy | compliance violation rate | fraud share (swap or theft) |
|---|---|---|---|---|
| stageroute_compliant | 0.234 ± 0.038 | 0.250 ± 0.032 | 0.000 ± 0.000 | 0.031 ± 0.013 |
| single_cheapest_compliant | 0.231 ± 0.061 | 0.269 ± 0.056 | 0.000 ± 0.000 | 0.074 ± 0.015 |
| pilot_compliant | 0.196 ± 0.024 | 0.241 ± 0.011 | 0.000 ± 0.000 | 0.090 ± 0.041 |
| audited_compliance_cascade | 0.056 ± 0.047 | 0.157 ± 0.024 | 0.000 ± 0.000 | 0.203 ± 0.075 |
| compliance_unaware_cheapest | 0.039 ± 0.016 | 0.262 ± 0.022 | 0.222 ± 0.035 | 0.000 ± 0.000 |
| cascade_compliant | 0.025 ± 0.057 | 0.157 ± 0.053 | 0.000 ± 0.000 | 0.264 ± 0.009 |
| vote_k_compliant | -0.020 ± 0.006 | 0.118 ± 0.007 | 0.000 ± 0.000 | 0.275 ± 0.007 |
| single_best_compliant | -0.269 ± 0.016 | 0.113 ± 0.017 | 0.000 ± 0.000 | 0.765 ± 0.018 |

## Mechanism comparison (single-seller policies: posted price vs sealed-bid second_price auction)

| mechanism | policy | task accuracy | fill rate | total cost | mean price/1K | compliance violations | budget violations | cross-border share | fraud-seller share | buyer surplus | seller profit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| posted_price | compliance_unaware_cheapest | 0.262 ± 0.022 | 0.979 ± 0.000 | 1.669 ± 0.010 | 0.0600 ± 0.0000 | 32.0 ± 5.0 | 1.0 ± 0.0 | 0.660 ± 0.000 | 0.000 ± 0.000 | 1.218 ± 0.258 | 0.810 ± 0.004 |
| sealed_bid | compliance_unaware_cheapest | 0.266 ± 0.017 | 0.956 ± 0.004 | 1.964 ± 0.025 | 0.0728 ± 0.0006 | 32.0 ± 5.0 | 1.0 ± 0.0 | 0.651 ± 0.001 | 0.000 ± 0.000 | 0.986 ± 0.302 | 1.121 ± 0.020 |
| posted_price | single_best_compliant | 0.113 ± 0.017 | 0.542 ± 0.007 | 5.854 ± 0.072 | 0.1752 ± 0.0036 | 0.0 ± 0.0 | 1.7 ± 1.2 | 0.526 ± 0.017 | 0.765 ± 0.018 | -4.517 ± 0.232 | 3.791 ± 0.032 |
| sealed_bid | single_best_compliant | 0.192 ± 0.045 | 0.810 ± 0.028 | 4.483 ± 0.119 | 0.1104 ± 0.0030 | 0.0 ± 0.0 | 2.0 ± 1.0 | 0.485 ± 0.030 | 0.428 ± 0.026 | -2.327 ± 0.528 | 2.425 ± 0.018 |
| posted_price | single_cheapest_compliant | 0.269 ± 0.056 | 0.940 ± 0.036 | 3.499 ± 0.029 | 0.0862 ± 0.0018 | 0.0 ± 0.0 | 1.0 ± 0.0 | 0.522 ± 0.015 | 0.074 ± 0.015 | -0.509 ± 0.606 | 1.764 ± 0.050 |
| sealed_bid | single_cheapest_compliant | 0.222 ± 0.024 | 0.866 ± 0.031 | 4.049 ± 0.035 | 0.1154 ± 0.0029 | 0.0 ± 0.0 | 1.7 ± 1.5 | 0.510 ± 0.022 | 0.061 ± 0.012 | -1.605 ± 0.294 | 2.567 ± 0.035 |

## Accuracy by seller (purchases) and fraud gap

| combo | seller_cn | seller_sg | seller_br | fraud acc gap (claimed rep − realised) |
|---|---|---|---|---|
| posted_price/single_cheapest_compliant | 0.480 | 0.139 | 0.268 | 0.281 ± 0.063 |
| posted_price/single_best_compliant | 0.483 | 0.134 | 0.492 | 0.307 ± 0.009 |
| posted_price/cascade_compliant | 0.400 | 0.162 | 0.269 | 0.274 ± 0.033 |
| posted_price/vote_k_compliant | 0.406 | 0.158 | 0.259 | 0.284 ± 0.027 |
| posted_price/compliance_unaware_cheapest | – | – | 0.267 | 0.000 ± 0.000 |
| posted_price/pilot_compliant | 0.416 | 0.062 | 0.232 | 0.365 ± 0.117 |
| posted_price/stageroute_compliant | 0.437 | 0.000 | 0.248 | 0.392 ± 0.082 |
| posted_price/audited_compliance_cascade | 0.399 | 0.195 | 0.256 | 0.285 ± 0.037 |
| sealed_bid/single_cheapest_compliant | 0.436 | 0.116 | 0.243 | 0.297 ± 0.108 |
| sealed_bid/single_best_compliant | 0.436 | 0.185 | 0.235 | 0.285 ± 0.055 |
| sealed_bid/compliance_unaware_cheapest | – | – | 0.278 | 0.000 ± 0.000 |

## Buyer surplus per buyer

| combo | buyer_br_1 | buyer_br_2 | buyer_cn_1 | buyer_cn_2 | buyer_sg_1 | buyer_sg_2 |
|---|---|---|---|---|---|---|
| posted_price/single_cheapest_compliant | 0.214 ± 0.010 | 0.146 ± 0.130 | -0.755 ± 0.147 | -0.497 ± 0.227 | 0.273 ± 0.276 | 0.111 ± 0.180 |
| posted_price/single_best_compliant | -0.773 ± 0.084 | -0.840 ± 0.094 | -0.830 ± 0.114 | -0.826 ± 0.123 | -1.038 ± 0.058 | -0.210 ± 0.034 |
| posted_price/cascade_compliant | -0.743 ± 0.280 | -0.749 ± 0.051 | -0.862 ± 0.080 | -0.809 ± 0.057 | -0.879 ± 0.234 | -0.154 ± 0.037 |
| posted_price/vote_k_compliant | -0.835 ± 0.110 | -0.837 ± 0.043 | -0.940 ± 0.123 | -0.879 ± 0.066 | -0.928 ± 0.158 | -0.194 ± 0.002 |
| posted_price/compliance_unaware_cheapest | 0.139 ± 0.192 | 0.148 ± 0.139 | 0.216 ± 0.109 | 0.373 ± 0.255 | 0.174 ± 0.155 | 0.167 ± 0.062 |
| posted_price/pilot_compliant | -0.461 ± 0.050 | -0.335 ± 0.275 | -0.731 ± 0.158 | -0.691 ± 0.105 | -0.447 ± 0.096 | -0.150 ± 0.087 |
| posted_price/stageroute_compliant | -0.709 ± 0.036 | -0.471 ± 0.098 | -0.538 ± 0.081 | -0.623 ± 0.184 | -0.430 ± 0.342 | -0.029 ± 0.243 |
| posted_price/audited_compliance_cascade | -0.658 ± 0.218 | -0.742 ± 0.041 | -0.927 ± 0.064 | -0.881 ± 0.115 | -0.879 ± 0.046 | -0.150 ± 0.031 |
| sealed_bid/single_cheapest_compliant | -0.135 ± 0.114 | 0.090 ± 0.016 | -0.905 ± 0.129 | -0.742 ± 0.104 | 0.080 ± 0.090 | 0.008 ± 0.072 |
| sealed_bid/single_best_compliant | -0.254 ± 0.166 | -0.135 ± 0.240 | -0.821 ± 0.172 | -0.783 ± 0.151 | -0.179 ± 0.068 | -0.155 ± 0.071 |
| sealed_bid/compliance_unaware_cheapest | 0.199 ± 0.046 | 0.143 ± 0.079 | 0.102 ± 0.124 | 0.349 ± 0.291 | 0.108 ± 0.032 | 0.085 ± 0.036 |

## Seller profit per seller

| combo | seller_br | seller_cn | seller_sg |
|---|---|---|---|
| posted_price/single_cheapest_compliant | 0.625 ± 0.040 | 0.561 ± 0.035 | 0.577 ± 0.095 |
| posted_price/single_best_compliant | 0.031 ± 0.011 | 0.434 ± 0.089 | 3.325 ± 0.104 |
| posted_price/cascade_compliant | 0.351 ± 0.043 | 1.056 ± 0.059 | 1.829 ± 0.091 |
| posted_price/vote_k_compliant | 0.328 ± 0.031 | 1.065 ± 0.034 | 1.839 ± 0.039 |
| posted_price/compliance_unaware_cheapest | 0.810 ± 0.004 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| posted_price/pilot_compliant | 0.358 ± 0.027 | 1.540 ± 0.183 | 0.607 ± 0.225 |
| posted_price/stageroute_compliant | 0.222 ± 0.095 | 1.920 ± 0.131 | 0.189 ± 0.069 |
| posted_price/audited_compliance_cascade | 0.368 ± 0.085 | 1.283 ± 0.240 | 0.872 ± 0.723 |
| sealed_bid/single_cheapest_compliant | 1.147 ± 0.017 | 0.991 ± 0.126 | 0.429 ± 0.138 |
| sealed_bid/single_best_compliant | 0.514 ± 0.005 | 0.991 ± 0.126 | 0.919 ± 0.113 |
| sealed_bid/compliance_unaware_cheapest | 1.121 ± 0.020 | 0.000 ± 0.000 | 0.000 ± 0.000 |

## Realised spend / budget per buyer

| combo | buyer_br_1 | buyer_br_2 | buyer_cn_1 | buyer_cn_2 | buyer_sg_1 | buyer_sg_2 |
|---|---|---|---|---|---|---|
| posted_price/single_cheapest_compliant | 0.277 ± 0.010 | 0.274 ± 0.013 | 0.945 ± 0.025 | 0.984 ± 0.016 | 0.230 ± 0.012 | 0.997 ± 0.017 |
| posted_price/single_best_compliant | 0.983 ± 0.038 | 0.980 ± 0.041 | 1.005 ± 0.009 | 0.981 ± 0.023 | 0.958 ± 0.023 | 0.840 ± 0.137 |
| posted_price/cascade_compliant | 1.000 ± 0.004 | 1.006 ± 0.012 | 0.988 ± 0.010 | 0.994 ± 0.010 | 1.002 ± 0.009 | 1.014 ± 0.010 |
| posted_price/vote_k_compliant | 0.998 ± 0.003 | 1.000 ± 0.003 | 0.986 ± 0.010 | 0.997 ± 0.015 | 0.998 ± 0.002 | 1.014 ± 0.010 |
| posted_price/compliance_unaware_cheapest | 0.281 ± 0.008 | 0.272 ± 0.003 | 0.232 ± 0.011 | 0.235 ± 0.003 | 0.223 ± 0.010 | 1.014 ± 0.008 |
| posted_price/pilot_compliant | 0.928 ± 0.060 | 0.895 ± 0.090 | 0.990 ± 0.009 | 0.953 ± 0.016 | 0.806 ± 0.068 | 1.000 ± 0.019 |
| posted_price/stageroute_compliant | 0.965 ± 0.031 | 0.961 ± 0.029 | 0.964 ± 0.037 | 0.978 ± 0.013 | 0.814 ± 0.192 | 0.996 ± 0.014 |
| posted_price/audited_compliance_cascade | 1.008 ± 0.008 | 0.999 ± 0.001 | 0.998 ± 0.020 | 0.998 ± 0.001 | 1.002 ± 0.002 | 1.002 ± 0.015 |
| sealed_bid/single_cheapest_compliant | 0.579 ± 0.069 | 0.377 ± 0.053 | 1.002 ± 0.007 | 0.993 ± 0.011 | 0.277 ± 0.020 | 1.009 ± 0.028 |
| sealed_bid/single_best_compliant | 0.674 ± 0.072 | 0.532 ± 0.091 | 0.998 ± 0.014 | 1.000 ± 0.001 | 0.420 ± 0.032 | 1.022 ± 0.006 |
| sealed_bid/compliance_unaware_cheapest | 0.337 ± 0.009 | 0.323 ± 0.028 | 0.281 ± 0.010 | 0.281 ± 0.007 | 0.277 ± 0.014 | 1.021 ± 0.007 |

## Compliance violations by rule (audit-only baseline)

| combo | CN-DSL-31 | CN-PIPL-38 | CN-PIPL-40 |
|---|---|---|---|
| posted_price/compliance_unaware_cheapest | 14.667 ± 1.155 | 11.333 ± 3.215 | 6.000 ± 2.000 |
| sealed_bid/compliance_unaware_cheapest | 14.667 ± 1.155 | 11.333 ± 3.215 | 6.000 ± 2.000 |

## Hard-filtered seller candidates by rule

| combo | BR-LGPD-33-VIII | CN-DSL-31 | CN-PIPL-38 | CN-PIPL-40 | SG-PDPA-26 |
|---|---|---|---|---|---|
| posted_price/single_cheapest_compliant | 13.333 ± 1.155 | 29.333 ± 2.309 | 11.333 ± 3.215 | 12.000 ± 4.000 | 13.000 ± 1.732 |
| posted_price/single_best_compliant | 13.333 ± 1.155 | 29.333 ± 2.309 | 11.333 ± 3.215 | 12.000 ± 4.000 | 13.000 ± 1.732 |
| posted_price/cascade_compliant | 13.333 ± 1.155 | 29.333 ± 2.309 | 11.333 ± 3.215 | 12.000 ± 4.000 | 13.000 ± 1.732 |
| posted_price/vote_k_compliant | 13.333 ± 1.155 | 29.333 ± 2.309 | 11.333 ± 3.215 | 12.000 ± 4.000 | 13.000 ± 1.732 |
| posted_price/pilot_compliant | 13.333 ± 1.155 | 29.333 ± 2.309 | 11.333 ± 3.215 | 12.000 ± 4.000 | 13.000 ± 1.732 |
| posted_price/stageroute_compliant | 13.333 ± 1.155 | 29.333 ± 2.309 | 11.333 ± 3.215 | 12.000 ± 4.000 | 13.000 ± 1.732 |
| posted_price/audited_compliance_cascade | 13.333 ± 1.155 | 29.333 ± 2.309 | 11.333 ± 3.215 | 12.000 ± 4.000 | 13.000 ± 1.732 |
| sealed_bid/single_cheapest_compliant | 13.333 ± 1.155 | 29.333 ± 2.309 | 11.333 ± 3.215 | 12.000 ± 4.000 | 13.000 ± 1.732 |
| sealed_bid/single_best_compliant | 13.333 ± 1.155 | 29.333 ± 2.309 | 11.333 ± 3.215 | 12.000 ± 4.000 | 13.000 ± 1.732 |

## Cascade / vote stop reasons

| combo | budget | confident | exhausted | vote |
|---|---|---|---|---|
| posted_price/cascade_compliant | 88.000 ± 8.888 | 20.333 ± 4.933 | 35.667 ± 4.041 | 0 |
| posted_price/vote_k_compliant | 100.333 ± 3.215 | 0 | 0 | 43.667 ± 3.215 |
| posted_price/audited_compliance_cascade | 79.667 ± 11.676 | 23.000 ± 5.568 | 41.333 ± 6.658 | 0 |

## Model reputation used for routing (by CLAIMED model)

| claimed model | source | advertised tokens | acc d4 | acc d5 |
|---|---|---|---|---|
| Qwen/Qwen2.5-1.5B-Instruct | measured | 414.3 | 0.536 | 0.300 |
| sim-fast-mock | config_prior | 100.0 | 0.300 | 0.200 |

## Measured local model accuracy

| model | n | acc overall | acc d4 (n) | acc d5 (n) | reasoning tokens mean ± std | gen time/item (s) mean ± std | total gen time (s) | explicit 'Answer:' rate | truncated rate |
|---|---|---|---|---|---|---|---|---|---|
| Qwen/Qwen2.5-0.5B-Instruct | 48 | 0.146 | 0.214 (28) | 0.050 (20) | 425.3 ± 90.7 | 3.02 ± 0.61 | 145.0 | 0.000 | 0.417 |
| Qwen/Qwen2.5-1.5B-Instruct | 48 | 0.438 | 0.536 (28) | 0.300 (20) | 414.3 ± 90.4 | 13.90 ± 9.86 | 667.0 | 0.312 | 0.292 |

Greedy decoding, chat template, max_new_tokens=256, batched (left padding). reasoning tokens = generated tokens excluding EOS/padding; gen time/item = amortised share of batch wall time proportional to generated tokens (8 CPU threads). Correct = parsed answer (last 'Answer:' number, else last number) == gold.

## What is real vs simulated

- **Real**: Qwen2.5-1.5B / 0.5B-Instruct outputs (local CPU inference, cached), their correctness against gold, reasoning-token counts and measured generation times on CPU; the GSM8K / MATH-500 long-task problems and golds. v4 token theft truncates these REAL cached outputs (character-proportional cut, answer re-parsed) - no new generation is run; the optional length-audit reference cross-check compares against the REAL cached greedy generation of the claimed model.
- **Simulated**: prices, serving costs (and the swap cost gap), latency noise and corridor penalties/fees, jurisdictions and the (simplified, NOT legal advice) compliance rules, buyers / budgets / sensitivities / consent, audits and BOTH detectors (identity check succeeding with prob d, length audit with prob d_length; miss / false-negative rates 1 - d, false positives 0), penalties / stake slashing / delisting, the strategic seller's learning rule and attack choice, the mock seller (seller_br, MockLLM), its confidence and its truncation model.

## Metric definitions

- task accuracy = share of tasks whose FINAL portfolio answer equals gold (tasks with no answer count as wrong).
- total cost = Σ actual_cost over purchases (actual_cost = price × actual reasoning tokens / 1000 × (1 + corridor fee rate)); mean cost/task = total cost / tasks.
- expected→actual cost gap = Σ(actual_cost − expected_cost) over served purchases (relative to Σ expected); expected_cost uses the CLAIMED model's advertised mean tokens.
- budget violations = purchases after which the buyer's realised spend exceeds its budget (budget_overrun=true); rate = / purchases. Purchases are only made if expected cost ≤ remaining budget, so overruns come only from token-length uncertainty.
- compliance violations = purchases whose data flow breached a rule but went through (violation=true). Hard-constraint policies filter infeasible sellers before purchase and go through an enforcing gateway (must be 0); the compliance_unaware_cheapest baseline goes through the gateway in audit_only mode, so its breaches are counted rather than blocked.
- blocked/filtered = seller candidates removed by the hard compliance filter + attempts blocked at the gateway.
- cross-border share / fraud-seller share = share of purchases that are cross-border / served by a model-swap seller (seller_sg: claims Qwen/Qwen2.5-1.5B-Instruct, serves Qwen/Qwen2.5-0.5B-Instruct).
- buyer surplus = Σ value_per_correct × final_correct − Σ actual_cost; seller profit = revenue − serving cost of the ACTUAL model.
- task latency: single = purchase latency; cascade = sum (sequential); vote = max (parallel).
