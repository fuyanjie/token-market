# T4 readout (agreed setting; not a new condition)

Setting: `fixed_audit_a0.10`, π=1, seeds 0–19, `--resample-roster`, official command then `scripts/run_t4_eval.py`. Features: rounds 1–32. Labels: rounds 33–48 (attack on a served purchase in the target window). Train seeds 0–13, test 14–19. Official table: `t4_eval.md` (script default: metrics pooled over test sellers; cluster bootstrap B=2000 on Δ of 7 vs 6 items).

## Label counts

| split | scored sellers | any pos | swap | theft | downgrade |
|---|---:|---:|---:|---:|---:|
| train (14 runs) | 208 | 7 | 3 | 4 | 0 |
| test (6 runs) | 89 | 2 | 1 | 1 | 0 |

Downgrade has no positives in train or test and was skipped. Of 6 test runs, both classes are present in 2 runs for `any` (seeds 16 and 18, 1 positive each) and in 1 run each for swap (seed 16) and theft (seed 18). The other test runs have zero positives, so per-run AUROC is undefined there.

This sparsity matches the main-table fact that D3 rarely trades with strategic sellers (this T4 batch: E=0.0066, tail_trade 16/20 under a resampled roster).

## How to read the official numbers

Do not write AUROC 0.98–1.00 as evidence that detection works. With 1–2 test positives, a high AUROC only means those few sellers were ranked ahead of the negatives. precision@10 = 0.10 (swap/theft) or 0.20 (`any`) is 1 or 2 hits in the top 10 of the pooled 89 sellers.

The official point estimates pool all test sellers. Protocol §5 asked for per-run metrics then an average over test runs, with no cross-seed pooling. Because 4/6 test runs have no positive, that average is mostly undefined. On the runs where it is defined, logreg and GBDT still have AUROC/AP = 1.0, again with a single positive per run.

7 vs 6 items (drop latency): in the official pooled table, `any` + logreg ΔAUROC = +0.040 [0.011, 0.076] and ΔAP = +0.206 [0.075, 0.583]. Other 7-vs-6 CIs usually include 0. Do not claim that latency helps; n_pos is 2. The rule baseline (low quoted price + billed-token anomaly) is weaker (pooled `any` AUROC 0.701, AP 0.120) and does not use latency.

A higher-prevalence condition would be a new protocol decision, not a rerun of this setting.
