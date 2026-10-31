# token-market v2 — C2 compliance-constrained portfolio purchasing

> Simplified simulation of data-transfer rules; NOT legal advice.

seller backends={'seller_cn': 'local_hf', 'seller_sg': 'local_hf', 'seller_br': 'mock'}, seeds=[0, 1, 2], tasks/run=144 (drawn from fixed pool of 48, task_seed=1234), auction=`second_price`, log lines=6011, precompute=0.0s, market sim=0.652s. Values are mean ± std over seeds.

## C2 baseline comparison (posted price)

| policy | task accuracy | total cost | mean cost/task | purchases/task | expected→actual cost gap | budget violations | compliance violations | blocked/filtered | cross-border share | fraud-seller share | buyer surplus | mean task latency (ms) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single_cheapest_compliant | 0.289 ± 0.051 | 3.999 ± 0.393 | 0.0278 ± 0.0027 | 1.00 ± 0.00 | +0.736 ± +0.044 (+22.7% ± +1.8%) | 0.0 ± 0.0 (0.0% ± 0.0%) | 0.0 ± 0.0 | 79.0 ± 6.6 | 0.523 ± 0.016 | 0.079 ± 0.022 | -0.775 ± 0.890 | 2718 ± 178 |
| single_best_compliant | 0.192 ± 0.011 | 10.525 ± 0.070 | 0.0731 ± 0.0005 | 0.96 ± 0.00 | +0.305 ± +0.069 (+3.0% ± +0.7%) | 0.0 ± 0.0 (0.0% ± 0.0%) | 0.0 ± 0.0 | 79.0 ± 6.6 | 0.495 ± 0.020 | 0.803 ± 0.021 | -8.278 ± 0.229 | 4725 ± 93 |
| cascade_compliant | 0.363 ± 0.058 | 15.748 ± 0.738 | 0.1094 ± 0.0051 | 2.00 ± 0.03 | +0.859 ± +0.027 (+5.8% ± +0.2%) | 0.0 ± 0.0 (0.0% ± 0.0%) | 0.0 ± 0.0 | 79.0 ± 6.6 | 0.564 ± 0.003 | 0.314 ± 0.005 | -11.701 ± 1.355 | 10902 ± 830 |
| vote_k_compliant | 0.220 ± 0.011 | 18.244 ± 0.194 | 0.1267 ± 0.0013 | 2.20 ± 0.04 | +0.788 ± +0.072 (+4.5% ± +0.4%) | 0.3 ± 0.6 (0.1% ± 0.2%) | 0.0 ± 0.0 | 79.0 ± 6.6 | 0.569 ± 0.007 | 0.344 ± 0.007 | -15.691 ± 0.187 | 11045 ± 397 |
| compliance_unaware_cheapest | 0.269 ± 0.021 | 1.707 ± 0.003 | 0.0119 ± 0.0000 | 1.00 ± 0.00 | +0.817 ± +0.003 (+91.8% ± +0.4%) | 0.0 ± 0.0 (0.0% ± 0.0%) | 32.0 ± 5.0 | 0.0 ± 0.0 | 0.667 ± 0.000 | 0.000 ± 0.000 | 1.246 ± 0.294 | 599 ± 9 |
| pilot_compliant | 0.377 ± 0.036 | 9.055 ± 0.822 | 0.0629 ± 0.0057 | 1.00 ± 0.00 | +0.267 ± +0.114 (+3.0% ± +1.2%) | 0.0 ± 0.0 (0.0% ± 0.0%) | 0.0 ± 0.0 | 79.0 ± 6.6 | 0.546 ± 0.036 | 0.079 ± 0.017 | -4.808 ± 0.855 | 9409 ± 999 |
| stageroute_compliant | 0.380 ± 0.039 | 8.639 ± 0.914 | 0.0600 ± 0.0063 | 1.00 ± 0.00 | +0.265 ± +0.140 (+3.2% ± +1.8%) | 0.0 ± 0.0 (0.0% ± 0.0%) | 0.0 ± 0.0 | 79.0 ± 6.6 | 0.602 ± 0.014 | 0.023 ± 0.011 | -4.346 ± 1.069 | 9321 ± 1145 |
| audited_compliance_cascade | 0.366 ± 0.057 | 11.885 ± 0.864 | 0.0825 ± 0.0060 | 1.68 ± 0.04 | +0.625 ± +0.078 (+5.6% ± +0.7%) | 0.0 ± 0.0 (0.0% ± 0.0%) | 0.0 ± 0.0 | 79.0 ± 6.6 | 0.553 ± 0.004 | 0.178 ± 0.018 | -7.896 ± 1.363 | 9781 ± 854 |

## v4 joint objective J = accuracy − 1.0·violation rate (/task) − 0.5·fraud share (/purchase)

| policy | J | task accuracy | compliance violation rate | fraud share (swap or theft) |
|---|---|---|---|---|
| stageroute_compliant | 0.368 ± 0.042 | 0.380 ± 0.039 | 0.000 ± 0.000 | 0.023 ± 0.011 |
| pilot_compliant | 0.338 ± 0.035 | 0.377 ± 0.036 | 0.000 ± 0.000 | 0.079 ± 0.017 |
| audited_compliance_cascade | 0.277 ± 0.058 | 0.366 ± 0.057 | 0.000 ± 0.000 | 0.178 ± 0.018 |
| single_cheapest_compliant | 0.250 ± 0.057 | 0.289 ± 0.051 | 0.000 ± 0.000 | 0.079 ± 0.022 |
| cascade_compliant | 0.206 ± 0.060 | 0.363 ± 0.058 | 0.000 ± 0.000 | 0.314 ± 0.005 |
| vote_k_compliant | 0.048 ± 0.007 | 0.220 ± 0.011 | 0.000 ± 0.000 | 0.344 ± 0.007 |
| compliance_unaware_cheapest | 0.046 ± 0.014 | 0.269 ± 0.021 | 0.222 ± 0.035 | 0.000 ± 0.000 |
| single_best_compliant | -0.209 ± 0.014 | 0.192 ± 0.011 | 0.000 ± 0.000 | 0.803 ± 0.021 |

## Mechanism comparison (single-seller policies: posted price vs sealed-bid second_price auction)

| mechanism | policy | task accuracy | fill rate | total cost | mean price/1K | compliance violations | budget violations | cross-border share | fraud-seller share | buyer surplus | seller profit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| posted_price | compliance_unaware_cheapest | 0.269 ± 0.021 | 1.000 ± 0.000 | 1.707 ± 0.003 | 0.0600 ± 0.0000 | 32.0 ± 5.0 | 0.0 ± 0.0 | 0.667 ± 0.000 | 0.000 ± 0.000 | 1.246 ± 0.294 | 0.829 ± 0.002 |
| sealed_bid | compliance_unaware_cheapest | 0.269 ± 0.021 | 1.000 ± 0.000 | 2.073 ± 0.021 | 0.0729 ± 0.0007 | 32.0 ± 5.0 | 0.0 ± 0.0 | 0.667 ± 0.000 | 0.000 ± 0.000 | 0.881 ± 0.302 | 1.183 ± 0.019 |
| posted_price | single_best_compliant | 0.192 ± 0.011 | 0.963 ± 0.004 | 10.525 ± 0.070 | 0.1772 ± 0.0002 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.495 ± 0.020 | 0.803 ± 0.021 | -8.278 ± 0.229 | 6.902 ± 0.085 |
| sealed_bid | single_best_compliant | 0.250 ± 0.049 | 1.000 ± 0.000 | 6.059 ± 0.514 | 0.1165 ± 0.0064 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.502 ± 0.021 | 0.414 ± 0.026 | -3.222 ± 1.025 | 3.338 ± 0.329 |
| posted_price | single_cheapest_compliant | 0.289 ± 0.051 | 1.000 ± 0.000 | 3.999 ± 0.393 | 0.0895 ± 0.0044 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.523 ± 0.016 | 0.079 ± 0.022 | -0.775 ± 0.890 | 2.005 ± 0.226 |
| sealed_bid | single_cheapest_compliant | 0.289 ± 0.051 | 1.000 ± 0.000 | 5.403 ± 0.504 | 0.1240 ± 0.0058 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.523 ± 0.016 | 0.079 ± 0.022 | -2.180 ± 1.004 | 3.404 ± 0.334 |

## Accuracy by seller (purchases) and fraud gap

| combo | seller_cn | seller_sg | seller_br | fraud acc gap (claimed rep − realised) |
|---|---|---|---|---|
| posted_price/single_cheapest_compliant | 0.455 | 0.130 | 0.276 | 0.290 ± 0.072 |
| posted_price/single_best_compliant | 0.455 | 0.141 | 0.397 | 0.298 ± 0.013 |
| posted_price/cascade_compliant | 0.451 | 0.155 | 0.273 | 0.279 ± 0.025 |
| posted_price/vote_k_compliant | 0.439 | 0.140 | 0.251 | 0.297 ± 0.014 |
| posted_price/compliance_unaware_cheapest | – | – | 0.269 | 0.000 ± 0.000 |
| posted_price/pilot_compliant | 0.447 | 0.048 | 0.305 | 0.337 ± 0.085 |
| posted_price/stageroute_compliant | 0.442 | 0.000 | 0.274 | 0.381 ± 0.035 |
| posted_price/audited_compliance_cascade | 0.451 | 0.210 | 0.276 | 0.278 ± 0.017 |
| sealed_bid/single_cheapest_compliant | 0.455 | 0.130 | 0.276 | 0.290 ± 0.072 |
| sealed_bid/single_best_compliant | 0.455 | 0.174 | 0.253 | 0.294 ± 0.041 |
| sealed_bid/compliance_unaware_cheapest | – | – | 0.269 | 0.000 ± 0.000 |

## Buyer surplus per buyer

| combo | buyer_br_1 | buyer_br_2 | buyer_cn_1 | buyer_cn_2 | buyer_sg_1 | buyer_sg_2 |
|---|---|---|---|---|---|---|
| posted_price/single_cheapest_compliant | 0.189 ± 0.046 | 0.216 ± 0.071 | -0.942 ± 0.326 | -0.649 ± 0.323 | 0.273 ± 0.265 | 0.138 ± 0.186 |
| posted_price/single_best_compliant | -1.172 ± 0.316 | -1.538 ± 0.280 | -1.455 ± 0.116 | -1.176 ± 0.303 | -1.605 ± 0.049 | -1.331 ± 0.059 |
| posted_price/cascade_compliant | -1.973 ± 0.551 | -2.638 ± 0.380 | -2.564 ± 0.177 | -1.741 ± 0.471 | -1.714 ± 0.781 | -1.072 ± 0.166 |
| posted_price/vote_k_compliant | -2.889 ± 0.464 | -3.578 ± 0.353 | -2.920 ± 0.075 | -2.109 ± 0.151 | -2.815 ± 0.193 | -1.379 ± 0.065 |
| posted_price/compliance_unaware_cheapest | 0.139 ± 0.129 | 0.236 ± 0.034 | 0.165 ± 0.080 | 0.407 ± 0.300 | 0.145 ± 0.174 | 0.153 ± 0.094 |
| posted_price/pilot_compliant | -0.857 ± 0.104 | -0.989 ± 0.361 | -1.103 ± 0.089 | -0.959 ± 0.421 | -0.627 ± 0.145 | -0.273 ± 0.272 |
| posted_price/stageroute_compliant | -1.029 ± 0.115 | -0.970 ± 0.289 | -0.984 ± 0.093 | -0.950 ± 0.473 | -0.280 ± 0.380 | -0.133 ± 0.246 |
| posted_price/audited_compliance_cascade | -1.110 ± 0.508 | -1.814 ± 0.291 | -2.196 ± 0.175 | -1.488 ± 0.513 | -0.929 ± 0.624 | -0.358 ± 0.083 |
| sealed_bid/single_cheapest_compliant | -0.114 ± 0.099 | 0.106 ± 0.082 | -1.231 ± 0.366 | -1.226 ± 0.336 | 0.206 ± 0.264 | 0.079 ± 0.174 |
| sealed_bid/single_best_compliant | -0.364 ± 0.104 | -0.091 ± 0.330 | -1.210 ± 0.287 | -1.251 ± 0.446 | -0.125 ± 0.070 | -0.180 ± 0.158 |
| sealed_bid/compliance_unaware_cheapest | 0.076 ± 0.129 | 0.189 ± 0.036 | 0.104 ± 0.079 | 0.348 ± 0.294 | 0.071 ± 0.169 | 0.094 ± 0.092 |

## Seller profit per seller

| combo | seller_br | seller_cn | seller_sg |
|---|---|---|---|
| posted_price/single_cheapest_compliant | 0.643 ± 0.037 | 0.697 ± 0.114 | 0.665 ± 0.189 |
| posted_price/single_best_compliant | 0.039 ± 0.003 | 0.697 ± 0.114 | 6.166 ± 0.193 |
| posted_price/cascade_compliant | 0.641 ± 0.039 | 2.864 ± 0.249 | 5.048 ± 0.131 |
| posted_price/vote_k_compliant | 0.617 ± 0.031 | 3.310 ± 0.075 | 6.034 ± 0.218 |
| posted_price/compliance_unaware_cheapest | 0.829 ± 0.002 | 0.000 ± 0.000 | 0.000 ± 0.000 |
| posted_price/pilot_compliant | 0.236 ± 0.046 | 2.990 ± 0.414 | 0.672 ± 0.128 |
| posted_price/stageroute_compliant | 0.272 ± 0.069 | 3.048 ± 0.365 | 0.208 ± 0.102 |
| posted_price/audited_compliance_cascade | 0.643 ± 0.037 | 2.864 ± 0.249 | 1.312 ± 0.326 |
| sealed_bid/single_cheapest_compliant | 1.219 ± 0.019 | 1.568 ± 0.256 | 0.617 ± 0.183 |
| sealed_bid/single_best_compliant | 0.566 ± 0.036 | 1.568 ± 0.256 | 1.204 ± 0.093 |
| sealed_bid/compliance_unaware_cheapest | 1.183 ± 0.019 | 0.000 ± 0.000 | 0.000 ± 0.000 |

## Realised spend / budget per buyer

| combo | buyer_br_1 | buyer_br_2 | buyer_cn_1 | buyer_cn_2 | buyer_sg_1 | buyer_sg_2 |
|---|---|---|---|---|---|---|
| posted_price/single_cheapest_compliant | 0.046 ± 0.001 | 0.046 ± 0.002 | 0.186 ± 0.032 | 0.198 ± 0.023 | 0.038 ± 0.002 | 0.188 ± 0.005 |
| posted_price/single_best_compliant | 0.250 ± 0.028 | 0.303 ± 0.026 | 0.258 ± 0.011 | 0.263 ± 0.014 | 0.246 ± 0.007 | 0.967 ± 0.003 |
| posted_price/cascade_compliant | 0.434 ± 0.064 | 0.560 ± 0.062 | 0.445 ± 0.018 | 0.361 ± 0.032 | 0.300 ± 0.072 | 0.994 ± 0.006 |
| posted_price/vote_k_compliant | 0.544 ± 0.060 | 0.666 ± 0.049 | 0.457 ± 0.024 | 0.397 ± 0.001 | 0.411 ± 0.020 | 0.999 ± 0.003 |
| posted_price/compliance_unaware_cheapest | 0.047 ± 0.001 | 0.046 ± 0.001 | 0.038 ± 0.002 | 0.039 ± 0.001 | 0.038 ± 0.002 | 0.191 ± 0.002 |
| posted_price/pilot_compliant | 0.236 ± 0.047 | 0.297 ± 0.058 | 0.264 ± 0.004 | 0.266 ± 0.020 | 0.169 ± 0.019 | 0.409 ± 0.105 |
| posted_price/stageroute_compliant | 0.257 ± 0.033 | 0.302 ± 0.046 | 0.252 ± 0.006 | 0.264 ± 0.022 | 0.133 ± 0.044 | 0.275 ± 0.084 |
| posted_price/audited_compliance_cascade | 0.290 ± 0.056 | 0.423 ± 0.042 | 0.396 ± 0.004 | 0.327 ± 0.041 | 0.195 ± 0.055 | 0.532 ± 0.060 |
| sealed_bid/single_cheapest_compliant | 0.097 ± 0.013 | 0.064 ± 0.009 | 0.225 ± 0.038 | 0.275 ± 0.032 | 0.047 ± 0.004 | 0.228 ± 0.005 |
| sealed_bid/single_best_compliant | 0.115 ± 0.014 | 0.089 ± 0.015 | 0.232 ± 0.032 | 0.278 ± 0.034 | 0.070 ± 0.005 | 0.320 ± 0.037 |
| sealed_bid/compliance_unaware_cheapest | 0.057 ± 0.001 | 0.054 ± 0.003 | 0.047 ± 0.003 | 0.047 ± 0.002 | 0.047 ± 0.003 | 0.231 ± 0.001 |

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
| posted_price/cascade_compliant | 5.000 ± 1.000 | 49.667 ± 3.055 | 89.333 ± 3.786 | 0 |
| posted_price/vote_k_compliant | 7.667 ± 0.577 | 0 | 0 | 136.333 ± 0.577 |
| posted_price/audited_compliance_cascade | 0 | 49.667 ± 3.055 | 94.333 ± 3.055 | 0 |

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
