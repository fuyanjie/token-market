# B — long reasoning tasks (GSM8K-hard + MATH-500, real Qwen outputs)

_v4: infrastructure / negative finding, NOT a contribution claim — per-purchase cost overruns are large on long outputs, but budget violations are ≈ 0 under normal budgets and only bind under tight budgets._

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
