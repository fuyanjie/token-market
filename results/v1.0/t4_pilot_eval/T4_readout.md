# T4 supplement readout: PILOT, π=1

This is the pre-registered supplement, not a replacement of the official T4 condition (`fixed_audit_a0.10`, π=1). Official numbers are the mean of per-test-run scores (`t4_eval.md`). Pooled-over-sellers figures in that file are not protocol and belong in an appendix note only.

Setting: `pilot`, π=1, seeds 0–19, `--resample-roster`. Features: rounds 1–32. Labels: rounds 33–48. Train seeds 0–13, test 14–19. The ranking unit is a seller with at least one served purchase in the target window (test: 215 scored sellers, not 40 per run). Bootstrap: resample test runs, B=2000, 95% percentile CI on the 7-minus-6 difference.

This batch: E=0.158, tail_trade 20/20 (resampled roster).

## Label counts

| split | scored sellers | any | swap | theft | downgrade |
|---|---:|---:|---:|---:|---:|
| train (14 runs) | 524 | 105 | 40 | 34 | 31 |
| test (6 runs) | 215 | 49 | 18 | 18 | 13 |

All 6 test runs have both classes for every attack type (and for `any`). Defined runs = 6/6, which meets the ≥4/6 rule, so detection performance may be reported for this supplement.

Per test run, `any` positives are 9, 8, 7, 9, 8, 8 (seeds 14–19). The 49 `any` positives partition as 18+18+13 by type (no overlap in this batch).

## Official per-run means (6/6 scored)

`any` (49 positives):

| model | AUROC 7 / 6 | Δ AUROC (95% CI) | AP 7 / 6 | Δ AP | p@10 7 / 6 | Δ p@10 |
|---|---|---|---|---|---|---|
| logreg | 0.970 / 0.895 | +0.074 [+0.039, +0.108] | 0.931 / 0.772 | +0.159 [+0.075, +0.236] | 0.750 / 0.583 | +0.167 [+0.083, +0.233] |
| GBDT | 0.976 / 0.941 | +0.035 [+0.017, +0.051] | 0.946 / 0.859 | +0.087 [+0.036, +0.136] | 0.783 / 0.650 | +0.133 [+0.100, +0.167] |
| rule | 0.703 / 0.703 | 0 (no latency) | 0.493 / 0.493 | 0 | 0.400 / 0.400 | 0 |

By attack type, the 7-vs-6 AUROC CI includes 0 for swap + logreg (`+0.065 [−0.019, +0.158]`) and downgrade + logreg (`+0.144 [−0.024, +0.301]`). It excludes 0 for theft (both models) and for swap/downgrade + GBDT. The rule baseline is weaker than logreg and GBDT on `any`.

Do not replace this condition with strongest or any other method after seeing these numbers. The official D3 T4 condition still does not report detection performance.
