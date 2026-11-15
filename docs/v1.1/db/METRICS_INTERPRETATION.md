# Metrics interpretation — documentation version 1 (2026-11-15)

Implementation sources: `tokenmarket/v1_metrics.py:exposure,intent`, `tokenmarket/audit_v1.py:present_rounds`, `tokenmarket/metrics.py:run_metrics`, and `scripts/run_v1.py`. Definitions below describe those sources, leaving all official values and paper verdicts intact.

For one run, served purchases are log rows with status `allowed`. A task can have multiple purchases in a cascade/portfolio. E (`fraud_share`) = attacked allowed purchases / allowed purchases. Any non-`none` realized attack counts, including swap, theft, downgrade and combined modes; the per-mode shares can overlap for combined attacks. E_tok is the billed-token total of attacked purchases / billed-token total of all allowed purchases. It uses billed, not actual generated tokens. If no purchases are served, E=0; if billed-token total is zero, E_tok=0. These zeros are denominator conventions, not evidence that the method learned honest seller behavior.

Q is separate from exposure. For each strategic seller and enabled mode, average its played attack probability over present (nonsuspended) rounds in the last quarter. Average eligible sellers within each mode, then take the unweighted mean of available mode values. Missing available modes produce null rather than invented zeros; no available mode yields null Q. `Q_present_rounds`, `delisted_rounds_tail` and `q_delisted_mean` describe support and excluded rounds. `tail_trade` records at least one served purchase from a strategic seller in the last 12 rounds (bounded by run length); this support window differs from the last-quarter Q window when run length changes. `tail_trade_rate` is the fraction of runs with such trades. Q is not weighted by purchases, tokens or realized attacks.

Aggregation is a mean across seed-level run summaries within method × π (or Decision A cell × learner), not a ratio obtained by pooling every seed's transactions. For statistical and missing-value behavior see [STATISTICS](STATISTICS.md). A task-level fill rate counts task IDs with any allowed purchase / final task rows. Accuracy is the fraction of final task outcomes correct, including no-answer outcomes as false. Served purchase count is not the same as served task count. Total cost sums buyer `actual_cost` (payment plus corridor fee) over allowed purchases, excluding audit cost; `cost_per_task` divides by all task instances. Audit cost is recorded separately. Violation rate is violations per task in `metrics.py`, so do not silently relabel it as per-purchase probability.

Low exposure can reflect avoidance: the cheapest router has zero recorded exposure in the relevant frozen board while its lack of strategic tail trades supplies no evidence of reduced seller intent. Read E alongside Q support, served volume, fill rate, accuracy and cost. Low served volume or zero buying can reduce exposure without providing useful procurement; no new dominance or deterrence conclusion follows from this documentation.

| Secondary frozen evidence | Location / columns |
|---|---|
| Fill, final task accuracy, cost, audit cost, served purchases | `results/v1.0/main/per_seed.csv`: `fill_rate`, `quality`, `cost`, `cost_per_task`, `audit_cost`, `n_served`; corresponding `main_fp`, `main_exp3`, `a2_filter_off` CSVs |
| E/Q and selected secondary inference | `results/v1.0/main/inference.json` / `.md`; not every secondary CSV field has a published CI |
| A2 OFF−ON summaries | `results/v1.0/a2_filter_off/A2_paired.json` / `.md` |
| Decision A accuracy and cost intervals | `results/v1.1/v1.2_decision_a_eval/cells.csv`: JSON-valued `accuracy`, `cost_per_task`; raw fields in `v1.2_decision_a/factorial/per_seed.csv` |
| T4 feature/target activity | `features_*.csv`: `n_attempts`, `n_served`, `served_share_of_run`; `labels_*.csv`: `n_target_served` |
| Legacy task/purchase accuracy and spend | `results/benchmark/production/*_episodes.jsonl`; names and available fields differ from official board |

Existing secondary summaries are indexed for interpretation, not promoted into new paper findings. Units and versioned joins are in [SCHEMA_v1](SCHEMA_v1.md).
