# token-market v3 — experiment summary

config `configs/experiments.yaml`, seeds=[0, 1, 2], backend override=None, reputation source: Qwen/Qwen2.5-1.5B-Instruct: measured, sim-fast-mock: config_prior

## C — strategic model-swap seller vs buyer audits (fraud / audit threshold)

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

## D — baselines vs the STRATEGIC model-swap seller

All policies face the same learning swap seller (seller_sg; penalty P=0.25, d=0.9). Only D3 audits (rate 0.1, audit cost 0.004 per audit charged to the buyer budget), so for every other policy the seller faces a = 0. Mean ± std over seeds [0, 1, 2].

| policy | task accuracy | total cost incl. audit | of which audit | cost/task | budget violations | compliance violations | fraud-seller share (swapped purchases) | sg learned q | swaps detected / served | stake slashed | buyer surplus |
|---|---|---|---|---|---|---|---|---|---|---|---|
| single_cheapest_compliant | 0.665 ± 0.019 | 5.562 ± 0.292 | 0.000 | 0.0116 ± 0.0006 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.061 ± 0.019 | 0.922 ± 0.081 | 0.0 / 29.3 | 0.00 | 19.221 ± 0.441 |
| single_best_compliant | 0.634 ± 0.008 | 11.606 ± 0.227 | 0.000 | 0.0242 ± 0.0005 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.766 ± 0.016 | 0.950 ± 0.044 | 0.0 / 335.7 | 0.00 | 12.431 ± 0.333 |
| cascade_compliant | 0.768 ± 0.011 | 13.940 ± 0.054 | 0.000 | 0.0290 ± 0.0001 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.302 ± 0.014 | 0.950 ± 0.044 | 0.0 / 222.7 | 0.00 | 14.897 ± 0.476 |
| vote_k_compliant | 0.690 ± 0.014 | 20.669 ± 0.161 | 0.000 | 0.0431 ± 0.0003 | 0.7 ± 0.6 | 0.0 ± 0.0 | 0.323 ± 0.004 | 0.950 ± 0.044 | 0.0 / 311.7 | 0.00 | 5.555 ± 0.581 |
| compliance_unaware_cheapest | 0.627 ± 0.044 | 3.486 ± 0.028 | 0.000 | 0.0073 ± 0.0001 | 0.0 ± 0.0 | 103.3 ± 6.4 | 0.000 ± 0.000 | 0.539 ± 0.028 | 0.0 / 0.0 | 0.00 | 19.594 ± 1.671 |
| PILOT-style (our simplified reimpl. of Panda et al. 2025), no compliance filter | 0.883 ± 0.019 | 11.433 ± 0.093 | 0.000 | 0.0238 ± 0.0002 | 0.0 ± 0.0 | 77.7 ± 9.3 | 0.235 ± 0.066 | 0.950 ± 0.044 | 0.0 / 112.7 | 0.00 | 21.420 ± 0.660 |
| PILOT-style + compliance filter | 0.856 ± 0.013 | 11.183 ± 0.319 | 0.000 | 0.0233 ± 0.0007 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.215 ± 0.049 | 0.950 ± 0.044 | 0.0 / 103.0 | 0.00 | 20.667 ± 0.634 |
| StageRoute-style (our simplified reimpl. of Li & Li 2025), no compliance filter | 0.837 ± 0.037 | 12.551 ± 0.154 | 0.000 | 0.0261 ± 0.0003 | 0.0 ± 0.0 | 61.3 ± 8.0 | 0.085 ± 0.038 | 0.950 ± 0.044 | 0.0 / 37.7 | 0.00 | 18.819 ± 1.071 |
| StageRoute-style + compliance filter | 0.797 ± 0.030 | 11.507 ± 0.565 | 0.000 | 0.0240 ± 0.0012 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.116 ± 0.086 | 0.950 ± 0.044 | 0.0 / 51.7 | 0.00 | 18.453 ± 1.455 |
| **D3 audited_compliance_cascade (ours)** | 0.811 ± 0.010 | 11.979 ± 0.364 | 0.233 | 0.0250 ± 0.0008 | 0.3 ± 0.6 | 0.0 ± 0.0 | 0.042 ± 0.017 | 0.131 ± 0.108 | 3.3 / 28.0 | 0.83 | 18.418 ± 0.687 |

## Accuracy at equal cost (from the A curves)

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

Differences from the papers (all baselines are OUR SIMPLIFIED REIMPLEMENTATIONS):
- PILOT: hand-made task features instead of query embeddings; the preference prior is the CLAIMED model's public reputation (so a swap seller inherits a good prior); reward = observed correctness; ON-MCKP ZCL threshold with budget bins + spillover and the B_left/Q_left fallback; one LinUCB shared by all buyers, budgets per buyer.
- StageRoute: only the per-query routing LP with UCB rewards / LCB costs and throughput caps (alpha = capacity share); the stage-wise deployment MIP is skipped (3 fixed sellers); LP solved exactly by vertex enumeration.
- Neither baseline accounts for audit cost, models a strategic seller, or filters on compliance (the `_compliant` variants add the hard compliance filter); non-filtered variants run through the audit_only gateway so their breaches are counted.
- D3 routes on audit-adjusted quality: once an audit reveals the served model, the seller's quality is (1 − q̂)·rep(claimed) + q̂·rep(revealed), q̂ = detected / (audits·d) (smoothed).

## A — accuracy vs cost curves

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


## B — long reasoning tasks (GSM8K-hard + MATH-500, real Qwen outputs)

## Measured model accuracy on the long subset

| model | n | acc overall | acc GSM8K-hard (d4) | acc MATH-500 L3+ (d5) | tokens mean ± std | p95 | max | truncation rate (= hit max_new_tokens) | explicit 'Answer:' rate |
|---|---|---|---|---|---|---|---|---|---|
| Qwen/Qwen2.5-0.5B-Instruct | 48 | 0.146 | 0.214 (n=28) | 0.050 (n=20) | 425.3 ± 90.7 | 512 | 512 | 0.417 | 0.000 |
| Qwen/Qwen2.5-1.5B-Instruct | 48 | 0.438 | 0.536 (n=28) | 0.300 (n=20) | 414.3 ± 90.4 | 512 | 512 | 0.292 | 0.312 |

Long tasks: max_new_tokens=512, bf16 on CPU (AMX), greedy, prompt 'solve step by step … Answer: <integer>'.

## Market: normal budget (budget multiplier ×3.0; full summary: `results/long_math/summary.md`)

| policy | task accuracy | Σ expected cost | Σ actual cost | gap (rel) | purchases with overrun | rel. overrun mean / p95 / max | budget violations (purchases) | buyers over budget | max overshoot | budget-exhausted tasks |
|---|---|---|---|---|---|---|---|---|---|---|
| single_cheapest_compliant | 0.289 ± 0.051 | 3.263 | 3.999 | +0.736 (+22.7%) | 394/432 | +72.1% / +152.3% / +219.0% | 0 | 0.0 | 0.0000 | 0.0 |
| single_best_compliant | 0.192 ± 0.011 | 10.220 | 10.525 | +0.305 (+3.0%) | 245/416 | +7.2% / +23.6% / +173.0% | 0 | 0.0 | 0.0000 | 5.3 |
| cascade_compliant | 0.363 ± 0.058 | 14.889 | 15.748 | +0.859 (+5.8%) | 626/866 | +36.4% / +134.0% / +219.0% | 0 | 0.0 | 0.0000 | 0.3 |
| vote_k_compliant | 0.220 ± 0.011 | 17.456 | 18.244 | +0.788 (+4.5%) | 660/950 | +31.8% / +131.5% / +199.0% | 1 | 0.3 | 0.0045 | 4.7 |
| compliance_unaware_cheapest | 0.269 ± 0.021 | 0.890 | 1.707 | +0.817 (+91.8%) | 429/432 | +91.9% / +152.0% / +205.0% | 0 | 0.0 | 0.0000 | 0.0 |
| pilot_compliant | 0.377 ± 0.036 | 8.787 | 9.055 | +0.267 (+3.0%) | 294/432 | +25.9% / +122.4% / +178.0% | 0 | 0.0 | 0.0000 | 0.0 |
| stageroute_compliant | 0.380 ± 0.039 | 8.374 | 8.639 | +0.265 (+3.2%) | 300/432 | +29.4% / +123.4% / +192.0% | 0 | 0.0 | 0.0000 | 0.0 |
| audited_compliance_cascade | 0.366 ± 0.057 | 11.260 | 11.885 | +0.625 (+5.6%) | 533/724 | +42.4% / +137.0% / +219.0% | 0 | 0.0 | 0.0000 | 0.0 |

## Market: tight budget (budget multiplier ×0.5; full summary: `results/long_math_tight/summary.md`)

| policy | task accuracy | Σ expected cost | Σ actual cost | gap (rel) | purchases with overrun | rel. overrun mean / p95 / max | budget violations (purchases) | buyers over budget | max overshoot | budget-exhausted tasks |
|---|---|---|---|---|---|---|---|---|---|---|
| single_cheapest_compliant | 0.269 ± 0.056 | 2.809 | 3.499 | +0.689 (+24.6%) | 373/406 | +74.4% / +153.2% / +219.0% | 3 | 1.0 | 0.0020 | 8.7 |
| single_best_compliant | 0.113 ± 0.017 | 5.655 | 5.854 | +0.198 (+3.5%) | 143/234 | +9.4% / +70.3% / +173.0% | 5 | 1.7 | 0.0182 | 66.0 |
| cascade_compliant | 0.157 ± 0.053 | 5.551 | 5.989 | +0.438 (+7.9%) | 290/375 | +46.4% / +138.6% / +182.0% | 9 | 3.0 | 0.0179 | 71.7 |
| vote_k_compliant | 0.118 ± 0.007 | 5.609 | 5.979 | +0.370 (+6.6%) | 276/367 | +43.5% / +137.7% / +205.0% | 8 | 2.7 | 0.0101 | 76.3 |
| compliance_unaware_cheapest | 0.262 ± 0.022 | 0.871 | 1.669 | +0.798 (+91.6%) | 420/423 | +91.6% / +152.0% / +205.0% | 3 | 1.0 | 0.0050 | 3.0 |
| pilot_compliant | 0.241 ± 0.011 | 5.055 | 5.509 | +0.454 (+9.0%) | 285/359 | +48.0% / +136.1% / +175.0% | 2 | 0.7 | 0.0032 | 24.3 |
| stageroute_compliant | 0.250 ± 0.032 | 5.345 | 5.620 | +0.275 (+5.2%) | 221/299 | +35.9% / +123.1% / +162.0% | 3 | 1.0 | 0.0089 | 44.3 |
| audited_compliance_cascade | 0.157 ± 0.024 | 5.554 | 5.960 | +0.406 (+7.3%) | 294/382 | +46.8% / +139.9% / +205.0% | 10 | 3.3 | 0.0180 | 66.7 |

Overrun counts are summed over seeds; other columns are means over seeds. A purchase is only made if its EXPECTED cost (claimed model's mean tokens) fits the remaining budget, so a budget violation needs a buyer whose remaining budget is below the purchase's ACTUAL cost but above its expected cost — at most a few purchases per buyer at the moment its budget runs out.

## What is real vs simulated

- **Real**: Qwen2.5-1.5B / 0.5B-Instruct outputs (local CPU inference, cached), their correctness against gold, reasoning-token counts and measured generation times on CPU; the GSM8K / MATH-500 long-task problems and golds.
- **Simulated**: prices, serving costs (and the swap cost gap), latency noise and corridor penalties/fees, jurisdictions and the (simplified, NOT legal advice) compliance rules, buyers / budgets / sensitivities / consent, audits and swap detection (identity check succeeding with prob d), penalties / stake slashing / delisting, the strategic seller's learning rule, the mock seller (seller_br, MockLLM) and its confidence.

_total experiment time 26.0s_
