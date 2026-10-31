# token-market v2 — C2 compliance-constrained portfolio purchasing

> Simplified simulation of data-transfer rules; NOT legal advice.

seller backends={'seller_cn': 'local_hf', 'seller_sg': 'local_hf', 'seller_br': 'mock'}, seeds=[0, 1, 2], tasks/run=240 (drawn from fixed pool of 80, task_seed=1234), auction=`second_price`, log lines=7031, precompute=0.0s, market sim=0.535s. Values are mean ± std over seeds.

## C2 baseline comparison (posted price)

| policy | task accuracy | total cost | mean cost/task | purchases/task | expected→actual cost gap | budget violations | compliance violations | blocked/filtered | cross-border share | fraud-seller share | buyer surplus | mean task latency (ms) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single_cheapest_compliant | 0.665 ± 0.010 | 2.812 ± 0.074 | 0.0117 ± 0.0003 | 1.00 ± 0.00 | +0.146 ± +0.033 (+5.5% ± +1.1%) | 0.0 ± 0.0 (0.0% ± 0.0%) | 0.0 ± 0.0 | 123.3 ± 10.1 | 0.560 ± 0.032 | 0.121 ± 0.018 | 9.545 ± 0.302 | 1136 ± 84 |
| single_best_compliant | 0.639 ± 0.013 | 5.843 ± 0.043 | 0.0243 ± 0.0002 | 0.92 ± 0.01 | +0.230 ± +0.065 (+4.1% ± +1.2%) | 0.3 ± 0.6 (0.2% ± 0.3%) | 0.0 ± 0.0 | 123.0 ± 9.5 | 0.561 ± 0.021 | 0.814 ± 0.020 | 6.210 ± 0.333 | 4456 ± 203 |
| cascade_compliant | 0.778 ± 0.028 | 7.362 ± 0.371 | 0.0307 ± 0.0015 | 1.58 ± 0.06 | +0.575 ± +0.119 (+8.5% ± +1.7%) | 0.0 ± 0.0 (0.0% ± 0.0%) | 0.0 ± 0.0 | 123.3 ± 10.1 | 0.554 ± 0.023 | 0.331 ± 0.016 | 7.248 ± 0.613 | 4609 ± 417 |
| vote_k_compliant | 0.689 ± 0.005 | 10.407 ± 0.309 | 0.0434 ± 0.0013 | 1.98 ± 0.05 | +0.521 ± +0.122 (+5.3% ± +1.2%) | 1.0 ± 0.0 (0.2% ± 0.0%) | 0.0 ± 0.0 | 123.3 ± 10.1 | 0.569 ± 0.010 | 0.351 ± 0.003 | 2.659 ± 0.334 | 5160 ± 348 |
| compliance_unaware_cheapest | 0.653 ± 0.028 | 2.540 ± 0.033 | 0.0106 ± 0.0001 | 1.00 ± 0.00 | +0.273 ± +0.056 (+12.1% ± +2.6%) | 0.0 ± 0.0 (0.0% ± 0.0%) | 56.7 ± 3.5 | 0.0 ± 0.0 | 0.669 ± 0.003 | 0.164 ± 0.004 | 9.570 ± 0.519 | 1321 ± 118 |

## v4 joint objective J = accuracy − 1.0·violation rate (/task) − 0.5·fraud share (/purchase)

| policy | J | task accuracy | compliance violation rate | fraud share (swap or theft) |
|---|---|---|---|---|
| cascade_compliant | 0.612 ± 0.027 | 0.778 ± 0.028 | 0.000 ± 0.000 | 0.331 ± 0.016 |
| single_cheapest_compliant | 0.605 ± 0.003 | 0.665 ± 0.010 | 0.000 ± 0.000 | 0.121 ± 0.018 |
| vote_k_compliant | 0.513 ± 0.006 | 0.689 ± 0.005 | 0.000 ± 0.000 | 0.351 ± 0.003 |
| compliance_unaware_cheapest | 0.335 ± 0.016 | 0.653 ± 0.028 | 0.236 ± 0.015 | 0.164 ± 0.004 |
| single_best_compliant | 0.232 ± 0.017 | 0.639 ± 0.013 | 0.000 ± 0.000 | 0.814 ± 0.020 |

## Mechanism comparison (single-seller policies: posted price vs sealed-bid second_price auction)

| mechanism | policy | task accuracy | fill rate | total cost | mean price/1K | compliance violations | budget violations | cross-border share | fraud-seller share | buyer surplus | seller profit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| posted_price | compliance_unaware_cheapest | 0.653 ± 0.028 | 0.997 ± 0.005 | 2.540 ± 0.033 | 0.0797 ± 0.0005 | 56.7 ± 3.5 | 0.0 ± 0.0 | 0.669 ± 0.003 | 0.164 ± 0.004 | 9.570 ± 0.519 | 1.476 ± 0.021 |
| sealed_bid | compliance_unaware_cheapest | 0.633 ± 0.014 | 0.967 ± 0.015 | 2.713 ± 0.037 | 0.0901 ± 0.0016 | 56.3 ± 3.1 | 0.0 ± 0.0 | 0.667 ± 0.008 | 0.138 ± 0.013 | 9.070 ± 0.283 | 1.705 ± 0.019 |
| posted_price | single_best_compliant | 0.639 ± 0.013 | 0.917 ± 0.008 | 5.843 ± 0.043 | 0.1769 ± 0.0008 | 0.0 ± 0.0 | 0.3 ± 0.6 | 0.561 ± 0.021 | 0.814 ± 0.020 | 6.210 ± 0.333 | 3.866 ± 0.076 |
| sealed_bid | single_best_compliant | 0.665 ± 0.027 | 1.000 ± 0.000 | 3.961 ± 0.194 | 0.1176 ± 0.0053 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.539 ± 0.002 | 0.433 ± 0.015 | 8.392 ± 0.281 | 2.241 ± 0.098 |
| posted_price | single_cheapest_compliant | 0.665 ± 0.010 | 1.000 ± 0.000 | 2.812 ± 0.074 | 0.0904 ± 0.0012 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.560 ± 0.032 | 0.121 ± 0.018 | 9.545 ± 0.302 | 1.470 ± 0.014 |
| sealed_bid | single_cheapest_compliant | 0.665 ± 0.010 | 1.000 ± 0.000 | 3.684 ± 0.186 | 0.1202 ± 0.0033 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.560 ± 0.032 | 0.121 ± 0.018 | 8.673 ± 0.414 | 2.335 ± 0.110 |

## Accuracy by seller (purchases) and fraud gap

| combo | seller_cn | seller_sg | seller_br | fraud acc gap (claimed rep − realised) |
|---|---|---|---|---|
| posted_price/single_cheapest_compliant | 0.898 | 0.714 | 0.624 | 0.218 ± 0.112 |
| posted_price/single_best_compliant | 0.909 | 0.658 | 0.782 | 0.265 ± 0.014 |
| posted_price/cascade_compliant | 0.910 | 0.650 | 0.617 | 0.267 ± 0.017 |
| posted_price/vote_k_compliant | 0.909 | 0.657 | 0.638 | 0.264 ± 0.022 |
| posted_price/compliance_unaware_cheapest | – | 0.670 | 0.652 | 0.250 ± 0.042 |
| sealed_bid/single_cheapest_compliant | 0.898 | 0.714 | 0.624 | 0.218 ± 0.112 |
| sealed_bid/single_best_compliant | 0.898 | 0.570 | 0.700 | 0.334 ± 0.037 |
| sealed_bid/compliance_unaware_cheapest | – | 0.671 | 0.653 | 0.245 ± 0.081 |

## Buyer surplus per buyer

| combo | buyer_br_1 | buyer_br_2 | buyer_cn_1 | buyer_cn_2 | buyer_sg_1 | buyer_sg_2 |
|---|---|---|---|---|---|---|
| posted_price/single_cheapest_compliant | 1.518 ± 0.048 | 1.462 ± 0.114 | 1.547 ± 0.143 | 2.011 ± 0.249 | 1.814 ± 0.186 | 1.192 ± 0.099 |
| posted_price/single_best_compliant | 1.191 ± 0.057 | 0.648 ± 0.085 | 1.230 ± 0.216 | 1.959 ± 0.145 | 0.853 ± 0.161 | 0.329 ± 0.143 |
| posted_price/cascade_compliant | 1.182 ± 0.178 | 0.766 ± 0.190 | 1.466 ± 0.253 | 2.014 ± 0.165 | 1.237 ± 0.453 | 0.583 ± 0.060 |
| posted_price/vote_k_compliant | 0.412 ± 0.154 | -0.296 ± 0.110 | 0.507 ± 0.114 | 1.462 ± 0.207 | 0.434 ± 0.162 | 0.142 ± 0.120 |
| posted_price/compliance_unaware_cheapest | 1.401 ± 0.054 | 1.196 ± 0.176 | 1.771 ± 0.269 | 2.612 ± 0.369 | 1.608 ± 0.237 | 0.982 ± 0.128 |
| sealed_bid/single_cheapest_compliant | 1.248 ± 0.065 | 1.367 ± 0.124 | 1.420 ± 0.162 | 1.755 ± 0.316 | 1.752 ± 0.181 | 1.131 ± 0.104 |
| sealed_bid/single_best_compliant | 1.281 ± 0.252 | 1.336 ± 0.067 | 1.330 ± 0.193 | 1.806 ± 0.101 | 1.559 ± 0.188 | 1.080 ± 0.291 |
| sealed_bid/compliance_unaware_cheapest | 1.401 ± 0.148 | 1.205 ± 0.174 | 1.767 ± 0.229 | 2.421 ± 0.312 | 1.554 ± 0.287 | 0.723 ± 0.091 |

## Seller profit per seller

| combo | seller_br | seller_cn | seller_sg |
|---|---|---|---|
| posted_price/single_cheapest_compliant | 0.649 ± 0.006 | 0.296 ± 0.075 | 0.524 ± 0.082 |
| posted_price/single_best_compliant | 0.037 ± 0.003 | 0.325 ± 0.066 | 3.504 ± 0.140 |
| posted_price/cascade_compliant | 0.594 ± 0.010 | 1.018 ± 0.011 | 2.516 ± 0.281 |
| posted_price/vote_k_compliant | 0.540 ± 0.026 | 1.821 ± 0.038 | 3.293 ± 0.151 |
| posted_price/compliance_unaware_cheapest | 0.698 ± 0.007 | 0.000 ± 0.000 | 0.778 ± 0.017 |
| sealed_bid/single_cheapest_compliant | 1.166 ± 0.034 | 0.667 ± 0.168 | 0.503 ± 0.071 |
| sealed_bid/single_best_compliant | 0.577 ± 0.082 | 0.667 ± 0.168 | 0.997 ± 0.011 |
| sealed_bid/compliance_unaware_cheapest | 0.977 ± 0.012 | 0.000 ± 0.000 | 0.728 ± 0.013 |

## Realised spend / budget per buyer

| combo | buyer_br_1 | buyer_br_2 | buyer_cn_1 | buyer_cn_2 | buyer_sg_1 | buyer_sg_2 |
|---|---|---|---|---|---|---|
| posted_price/single_cheapest_compliant | 0.139 ± 0.005 | 0.155 ± 0.017 | 0.288 ± 0.012 | 0.369 ± 0.042 | 0.117 ± 0.004 | 0.576 ± 0.029 |
| posted_price/single_best_compliant | 0.466 ± 0.022 | 0.551 ± 0.029 | 0.425 ± 0.022 | 0.443 ± 0.022 | 0.459 ± 0.044 | 0.982 ± 0.026 |
| posted_price/cascade_compliant | 0.587 ± 0.053 | 0.737 ± 0.106 | 0.565 ± 0.025 | 0.581 ± 0.058 | 0.540 ± 0.138 | 0.994 ± 0.006 |
| posted_price/vote_k_compliant | 0.996 ± 0.005 | 1.000 ± 0.002 | 0.842 ± 0.041 | 0.695 ± 0.083 | 0.829 ± 0.056 | 0.997 ± 0.009 |
| posted_price/compliance_unaware_cheapest | 0.244 ± 0.030 | 0.266 ± 0.004 | 0.113 ± 0.005 | 0.115 ± 0.005 | 0.189 ± 0.015 | 0.955 ± 0.031 |
| sealed_bid/single_cheapest_compliant | 0.274 ± 0.026 | 0.203 ± 0.023 | 0.339 ± 0.016 | 0.471 ± 0.072 | 0.142 ± 0.006 | 0.699 ± 0.036 |
| sealed_bid/single_best_compliant | 0.316 ± 0.015 | 0.218 ± 0.026 | 0.353 ± 0.013 | 0.478 ± 0.065 | 0.166 ± 0.010 | 0.800 ± 0.042 |
| sealed_bid/compliance_unaware_cheapest | 0.256 ± 0.029 | 0.272 ± 0.006 | 0.136 ± 0.006 | 0.138 ± 0.006 | 0.189 ± 0.017 | 0.995 ± 0.003 |

## Compliance violations by rule (audit-only baseline)

| combo | BR-LGPD-33-VIII | CN-DSL-31 | CN-PIPL-38 | CN-PIPL-40 |
|---|---|---|---|---|
| posted_price/compliance_unaware_cheapest | 2.000 ± 0.000 | 17.667 ± 6.658 | 27.333 ± 3.055 | 9.667 ± 1.155 |
| sealed_bid/compliance_unaware_cheapest | 1.667 ± 0.577 | 17.667 ± 6.658 | 27.333 ± 3.055 | 9.667 ± 1.155 |

## Hard-filtered seller candidates by rule

| combo | BR-LGPD-33-VIII | CN-DSL-31 | CN-PIPL-38 | CN-PIPL-40 | SG-PDPA-26 |
|---|---|---|---|---|---|
| posted_price/single_cheapest_compliant | 20.000 ± 2.000 | 35.333 ± 13.317 | 27.333 ± 3.055 | 19.333 ± 2.309 | 21.333 ± 2.309 |
| posted_price/single_best_compliant | 19.667 ± 2.517 | 35.333 ± 13.317 | 27.333 ± 3.055 | 19.333 ± 2.309 | 21.333 ± 2.309 |
| posted_price/cascade_compliant | 20.000 ± 2.000 | 35.333 ± 13.317 | 27.333 ± 3.055 | 19.333 ± 2.309 | 21.333 ± 2.309 |
| posted_price/vote_k_compliant | 20.000 ± 2.000 | 35.333 ± 13.317 | 27.333 ± 3.055 | 19.333 ± 2.309 | 21.333 ± 2.309 |
| sealed_bid/single_cheapest_compliant | 20.000 ± 2.000 | 35.333 ± 13.317 | 27.333 ± 3.055 | 19.333 ± 2.309 | 21.333 ± 2.309 |
| sealed_bid/single_best_compliant | 20.000 ± 2.000 | 35.333 ± 13.317 | 27.333 ± 3.055 | 19.333 ± 2.309 | 21.333 ± 2.309 |

## Cascade / vote stop reasons

| combo | budget | confident | exhausted | vote |
|---|---|---|---|---|
| posted_price/cascade_compliant | 18.000 ± 2.646 | 190.000 ± 4.000 | 32.000 ± 1.732 | 0 |
| posted_price/vote_k_compliant | 36.000 ± 3.606 | 0 | 0 | 204.000 ± 3.606 |

## Model reputation used for routing (by CLAIMED model)

| claimed model | source | advertised tokens | acc d1 | acc d2 | acc d3 |
|---|---|---|---|---|---|
| Qwen/Qwen2.5-1.5B-Instruct | measured | 142.3 | 0.929 | 1.000 | 0.833 |
| sim-fast-mock | config_prior | 100.0 | 0.820 | 0.620 | 0.400 |

## Measured local model accuracy

| model | n | acc overall | acc d1 (n) | acc d2 (n) | acc d3 (n) | reasoning tokens mean ± std | gen time/item (s) mean ± std | total gen time (s) | explicit 'Answer:' rate | truncated rate |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen/Qwen2.5-0.5B-Instruct | 80 | 0.662 | 0.786 (28) | 0.750 (28) | 0.417 (24) | 149.4 ± 63.7 | 4.40 ± 7.08 | 352.2 | 0.512 | 0.075 |
| Qwen/Qwen2.5-1.5B-Instruct | 80 | 0.925 | 0.929 (28) | 1.000 (28) | 0.833 (24) | 142.3 ± 47.2 | 2.53 ± 0.77 | 202.5 | 0.900 | 0.037 |

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
