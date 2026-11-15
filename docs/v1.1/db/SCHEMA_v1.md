# Schema v1 — versioned documentation (2026-11-15)

Precedence: frozen files and their producing code define each representation; `main.tex` §Feature / Label separation governs T4 admissibility. This dictionary documents coexistence, not a single interchangeable format. `docs/DATA_SCHEMA.md` remains the legacy reference. No legacy five-file export can be losslessly relabeled as the official 40-seller board: it lacks listed-round Q histories and the complete method grid. Decision A has different cells/rounds/audit settings; do not concatenate it as another v1.0 method. T4 is a windowed seller aggregation, not an episode board.

CSV types below are logical types: parse booleans from True/False, numbers explicitly, and JSON-valued cells with `json.loads`. Empty CSV cells denote missing/undefined values, not zero. JSONL uses JSON null. Nullability combines observed nulls and code-defined conditional cases; “none observed” does not assert a universal validator. Units are synthetic unless explicitly time/tokens. Each section fixes row granularity, primary key and joins; these apply to every field in its table.

Source implementations: `tokenmarket/benchmark_export.py` (legacy field lists/builders), `scripts/run_v1.py`, `tokenmarket/v1_metrics.py` and `tokenmarket/metrics.py` (board), `tokenmarket/decision_a.py`, `scripts/v1.1/analyze_decision_a.py` (readouts), `tokenmarket/t4_export.py` (T4). Statistical JSON estimates have number-or-null `mean`, `lo`, `hi`; contrast endpoints are paired differences. Rates refer to their named denominator; see METRICS_INTERPRETATION.md.

## Legacy sellers

Frozen example: `exports/production/sellers.jsonl`. One catalog seller per run; key (run_id, seller_id); join orders on those fields.

| Field | Logical type | Unit / meaning | Nullability | Visibility |
|---|---|---|---|---|
| `seller_id` | string | identifier / category | conditional; no null in this file | key/metadata; exclude T4 predictor IDs |
| `jurisdiction` | string | category / text | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `claimed_model` | string | category / text | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `actual_model` | string | category / text | none observed; not a general validator | evaluation/private; not a T4 predictor |
| `listed_quality` | object/list | difficulty → configured accuracy map | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `latent_q_swap` | number | dimensionless fraction/probability | none observed; not a general validator | evaluation/private; not a T4 predictor |
| `latent_q_theft` | number | dimensionless fraction/probability | none observed; not a general validator | evaluation/private; not a T4 predictor |
| `list_price` | number | synthetic currency / 1K billed tokens | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `capacity` | integer | purchases / round | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `stake` | number | synthetic currency | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `stake_remaining` | number | synthetic currency | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `banned_until_round` | integer | round watermark | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `run_id` | string | identifier / category | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `seed` | integer | seed identifier | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |

Tiny example: first frozen row projected to these fields; CSV strings retained verbatim.

```json
{"seller_id": "seller_cn", "jurisdiction": "CN", "claimed_model": "Qwen/Qwen2.5-1.5B-Instruct", "actual_model": "Qwen/Qwen2.5-1.5B-Instruct"}
```

## Legacy buyers

Frozen example: `exports/production/buyers.jsonl`. One buyer per run; key (run_id, buyer_id); join orders on those fields.

| Field | Logical type | Unit / meaning | Nullability | Visibility |
|---|---|---|---|---|
| `buyer_id` | string | identifier / category | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `jurisdiction` | string | category / text | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `budget_total` | number | synthetic currency | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `budget_remaining` | number | synthetic currency | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `strategy_id` | string | identifier / category | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `compliance_profile` | object/list | scenario-control JSON object | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `run_id` | string | identifier / category | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `seed` | integer | seed identifier | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |

Tiny example: first frozen row projected to these fields; CSV strings retained verbatim.

```json
{"buyer_id": "buyer_cn_1", "jurisdiction": "CN", "budget_total": 5.0, "budget_remaining": 2.214392599999999}
```

## Legacy orders

Frozen example: `exports/production/orders.jsonl`. One purchase attempt or unfilled task line; key order_id (retain run_id when combining files); seller_id nullable for unfilled. portfolio_id = task_id groups task purchases.

| Field | Logical type | Unit / meaning | Nullability | Visibility |
|---|---|---|---|---|
| `order_id` | string | identifier / category | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `round` | integer | zero-based round | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `t_submit` | number | Unix seconds; shared simulated log timestamp | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `t_deliver` | number | Unix seconds; not independent observed delivery | yes (empty/null observed) | legacy observable/config; not automatically T4-whitelisted |
| `t_settle` | number | Unix seconds; not independent observed settlement | yes (empty/null observed) | legacy observable/config; not automatically T4-whitelisted |
| `buyer_id` | string | identifier / category | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `seller_id` | string | identifier / category | yes (empty/null observed) | key/metadata; exclude T4 predictor IDs |
| `task_id` | string | identifier / category | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `portfolio_id` | string | identifier / category | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `tokens_billed` | integer | tokens | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `tokens_actual` | integer | tokens | none observed; not a general validator | evaluation/private; not a T4 predictor |
| `price` | number | synthetic currency / 1K billed tokens | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `amount_escrow` | number | synthetic currency | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `amount_paid` | number | synthetic currency, includes corridor fee | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `state` | string | category / text | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `attack_mode` | string | category / text | none observed; not a general validator | evaluation/private; not a T4 predictor |
| `correct` | boolean | boolean indicator | yes (empty/null observed) | evaluation/private; not a T4 predictor |
| `jurisdiction_path` | string | category / text | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `route_policy` | string | category / text | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `run_id` | string | identifier / category | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `seed` | integer | seed identifier | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `config_hash` | string | first 16 SHA256 hex characters of per-run config JSON | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |

Tiny example: first frozen row projected to these fields; CSV strings retained verbatim.

```json
{"order_id": "posted_price__audited_compliance_cascade__seed0|t0000_p059|0|seller_br", "round": 0, "t_submit": 1794140171.8250268, "t_deliver": 1794140171.8250268, "config_hash": "7b60ac28061d2907"}
```

## Legacy audits

Frozen example: `exports/production/audits.jsonl`. One row per allowed purchase, including unsampled audits; key audit_id; order_id joins orders one-to-one on the served subset.

| Field | Logical type | Unit / meaning | Nullability | Visibility |
|---|---|---|---|---|
| `audit_id` | string | identifier / category | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `order_id` | string | identifier / category | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `round` | integer | zero-based round | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `mode` | string | category / text | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `sampled` | integer 0/1 | boolean indicator | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `identity_check` | integer 0/1 | boolean indicator | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `length_check` | integer 0/1 | boolean indicator | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `hit` | integer 0/1 | boolean indicator | none observed; not a general validator | evaluation/private; not a T4 predictor |
| `miss` | integer 0/1 | boolean indicator | none observed; not a general validator | evaluation/private; not a T4 predictor |
| `slash_amount` | number | synthetic currency | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `delist_rounds` | integer | rounds | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `auditor_cost` | number | synthetic currency | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `label_revealed` | integer 0/1 | boolean indicator | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `label_delay_L` | integer or null | task-step delay; null = never | conditional; no null in this file | legacy observable/config; not automatically T4-whitelisted |
| `reveal_pi` | number | dimensionless fraction/probability | none observed; not a general validator | legacy observable/config; not automatically T4-whitelisted |
| `label_correct` | boolean | boolean indicator | conditional; no null in this file | evaluation/private; not a T4 predictor |
| `fraud_realized` | integer 0/1 | boolean indicator | none observed; not a general validator | evaluation/private; not a T4 predictor |
| `run_id` | string | identifier / category | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `seed` | integer | seed identifier | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |

Tiny example: first frozen row projected to these fields; CSV strings retained verbatim.

```json
{"audit_id": "audit|posted_price__audited_compliance_cascade__seed0|t0000_p059|0|seller_br", "order_id": "posted_price__audited_compliance_cascade__seed0|t0000_p059|0|seller_br", "round": 0, "mode": "fixed"}
```

## Legacy episodes

Frozen example: `exports/production/episodes.jsonl`. One run summary; key (run_id, seed); joins other layers on run_id, seed.

| Field | Logical type | Unit / meaning | Nullability | Visibility |
|---|---|---|---|---|
| `run_id` | string | identifier / category | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `seed` | integer | seed identifier | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `a` | number | dimensionless fraction/probability | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `pi` | number | dimensionless fraction/probability | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `L` | integer or null | task-step delay; null = never | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `reputation_rounds` | integer | rounds | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `active_attack_rate` | number | legacy realized attacked / allowed purchases; not Q | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `learned_q_swap` | number | dimensionless fraction/probability | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `learned_q_theft` | number | dimensionless fraction/probability | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `fraud_share` | number | same per-purchase exposure as E | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `J` | number | dimensionless joint objective | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `n_audits` | integer | allowed audited purchases | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `config_hash` | string | first 16 SHA256 hex characters of per-run config JSON | none observed; not a general validator | evaluation/config metadata; not T4 input |

Tiny example: first frozen row projected to these fields; CSV strings retained verbatim.

```json
{"run_id": "posted_price__audited_compliance_cascade__seed0", "seed": 0, "a": 0.1, "pi": 1.0, "config_hash": "7b60ac28061d2907"}
```

## Official 40-seller board

Frozen example: `results/v1.0/main/per_seed.csv`. One method × π × seed run; key (method, pi, seed) within one learner/config directory. No run_id or a column. Keep source directory/learner when combining boards.

| Field | Logical type | Unit / meaning | Nullability | Visibility |
|---|---|---|---|---|
| `method` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `label` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `policy` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `pi` | number | dimensionless fraction/probability | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `seed` | integer | seed identifier | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `E` | number | attacked allowed purchases / allowed purchases | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `E_tok` | number | attacked billed tokens / all billed tokens | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `fraud_share` | number | same per-purchase exposure as E | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `fraud_share_swap` | number | dimensionless fraction/probability | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `fraud_share_theft` | number | dimensionless fraction/probability | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `fraud_share_downgrade` | number | dimensionless fraction/probability | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `Q` | number | unweighted average of available per-mode intent | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `Q_swap` | number | dimensionless fraction/probability | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `Q_theft` | number | dimensionless fraction/probability | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `Q_downgrade` | number | dimensionless fraction/probability | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `tail_trade` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `tail_trade_sellers` | integer | sellers | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `tail_sales` | integer | allowed purchases | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `n_strategic` | integer | sellers | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `Q_present_rounds` | integer | seller-rounds | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `delisted_rounds_tail` | integer | seller-rounds | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `q_delisted_mean` | number | dimensionless fraction/probability | yes (empty/null observed) | evaluation/config metadata; not T4 input |
| `J` | number | dimensionless joint objective | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `quality` | number | correct final tasks / all tasks | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `cost` | number | synthetic currency total, excludes audit | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `cost_per_task` | number | synthetic currency / task | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `audit_cost` | number | synthetic currency total | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `n_audits` | integer | allowed audited purchases | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `audit_rate_realised` | number | audits / allowed purchases | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `violation_rate` | number | violating allowed purchases / all tasks | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `fill_rate` | number | tasks with service / all tasks | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `n_served` | integer | allowed purchases | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `seller_learner` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `audit_rule` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `compliance_filter` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `roster_seed` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `config_hash` | string | first 16 SHA256 hex characters of per-run config JSON | none observed; not a general validator | evaluation/config metadata; not T4 input |

Tiny example: first frozen row projected to these fields; CSV strings retained verbatim.

```json
{"method": "pilot", "label": "PILOT (Panda et al. 2025), faithful reimpl.", "policy": "pilot_v1_compliant", "pi": "0.0", "E": "0.42138364779874216", "Q": "0.8009259259259259", "config_hash": "8480f34cea55114e"}
```

## Decision A raw board

Frozen example: `results/v1.1/v1.2_decision_a/factorial/per_seed.csv`. One cell × learner × seed run; key (cell_id, learner, seed). Join readout cells on (cell_id, learner).

| Field | Logical type | Unit / meaning | Nullability | Visibility |
|---|---|---|---|---|
| `router` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `audit` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `penalty` | number | synthetic currency | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `pi` | number | dimensionless fraction/probability | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `cell_id` | string | identifier / category | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `arm` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `policy` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `trust_feedback` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `penalty_label` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `audit_efficacy_evidence_allowed` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `seed` | integer | seed identifier | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `E_tok` | number | attacked billed tokens / all billed tokens | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `fraud_share` | number | same per-purchase exposure as E | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `n_served` | integer | allowed purchases | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `billed_tokens_total` | integer | tokens | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `fraud_share_swap` | number | dimensionless fraction/probability | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `fraud_share_theft` | number | dimensionless fraction/probability | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `fraud_share_downgrade` | number | dimensionless fraction/probability | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `E` | number | attacked allowed purchases / allowed purchases | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `Q` | number | unweighted average of available per-mode intent | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `Q_swap` | number | dimensionless fraction/probability | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `Q_theft` | number | dimensionless fraction/probability | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `Q_downgrade` | number | dimensionless fraction/probability | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `tail_trade` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `tail_trade_sellers` | integer | sellers | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `tail_sales` | integer | allowed purchases | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `n_strategic` | integer | sellers | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `Q_present_rounds` | integer | seller-rounds | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `delisted_rounds_tail` | integer | seller-rounds | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `q_delisted_mean` | number | dimensionless fraction/probability | yes (empty/null observed) | evaluation/config metadata; not T4 input |
| `q_delisted_swap` | number | dimensionless fraction/probability | yes (empty/null observed) | evaluation/config metadata; not T4 input |
| `q_delisted_theft` | number | dimensionless fraction/probability | yes (empty/null observed) | evaluation/config metadata; not T4 input |
| `q_delisted_downgrade` | number | dimensionless fraction/probability | yes (empty/null observed) | evaluation/config metadata; not T4 input |
| `q_swap` | number | dimensionless fraction/probability | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `q_theft` | number | dimensionless fraction/probability | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `q_downgrade` | number | dimensionless fraction/probability | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `accuracy` | number | correct final tasks / all tasks | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `cost_per_task` | number | synthetic currency / task | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `cost` | number | synthetic currency total, excludes audit | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `audit_cost` | number | synthetic currency total | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `n_audits` | integer | allowed audited purchases | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `audit_rate_realised` | number | audits / allowed purchases | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `fill_rate` | number | tasks with service / all tasks | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `n_tasks` | integer | task instances | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `n_rounds` | integer | rounds | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `tail_rounds` | integer | rounds in Q tail | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `strategic_tail_counts` | JSON string → object/list | JSON object: seller ID → allowed tail purchases | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `learner` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `budget_multiplier` | number | dimensionless budget scaling factor | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `audit_checks` | JSON string → object/list | JSON list of check categories | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `audit_rule` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `config_hash` | string | first 16 SHA256 hex characters of per-run config JSON | none observed; not a general validator | evaluation/config metadata; not T4 input |

Tiny example: first frozen row projected to these fields; CSV strings retained verbatim.

```json
{"router": "pilot", "audit": "a0", "penalty": "0.25", "pi": "1.0", "E": "0.0968000802487712", "Q": "0.9445333333333332", "config_hash": "4a65fe8ae672d4710e5904dcb107fd619704c0d5a474fc00986a33fab7db3223"}
```

## Decision A cells

Frozen example: `results/v1.1/v1.2_decision_a_eval/cells.csv`. One cell × learner summary; key (cell_id, learner). Nested JSON estimates are marginal mean/lo/hi.

| Field | Logical type | Unit / meaning | Nullability | Visibility |
|---|---|---|---|---|
| `router` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `audit` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `penalty` | number | synthetic currency | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `pi` | number | dimensionless fraction/probability | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `cell_id` | string | identifier / category | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `arm` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `policy` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `trust_feedback` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `penalty_label` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `audit_efficacy_evidence_allowed` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `learner` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `n_runs` | integer | runs | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `tail_trade_runs` | integer | runs | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `tail_trade_rate` | number | dimensionless fraction/probability | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `Q_identifiable` | boolean | boolean indicator | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `audit_rate_realised_mean` | number | mean audits / allowed purchases over runs | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `per_run_strategic_tail_counts` | JSON string → object/list | JSON list: seed, tail_sales, by_seller counts | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `astar_relation` | JSON string → object/list | JSON object: relation and frozen break-even bounds | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `E` | JSON string → object/list | attacked allowed purchases / allowed purchases | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `E_tok` | JSON string → object/list | attacked billed tokens / all billed tokens | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `Q` | JSON string → object/list | unweighted average of available per-mode intent | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `q_swap` | JSON string → object/list | dimensionless fraction/probability | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `q_theft` | JSON string → object/list | dimensionless fraction/probability | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `q_downgrade` | JSON string → object/list | dimensionless fraction/probability | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `accuracy` | JSON string → object/list | correct final tasks / all tasks | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `cost_per_task` | JSON string → object/list | synthetic currency / task | none observed; not a general validator | evaluation/config metadata; not T4 input |

Tiny example: first frozen row projected to these fields; CSV strings retained verbatim.

```json
{"router": "pilot", "audit": "a0", "penalty": "0.25", "pi": "1.0", "E": "{\"hi\": 0.11279711717183813, \"lo\": 0.10727107221326278, \"mean\": 0.11008804261883494}", "Q": "{\"hi\": 0.9506133333333333, \"lo\": 0.9471176666666666, \"mean\": 0.9488355555555558}"}
```

## Decision A contrasts

Frozen example: `results/v1.1/v1.2_decision_a_eval/contrasts.csv`. One nonreference cell × learner × metric; key (cell_id, learner, metric); join baseline_cell_id, learner to cells.

| Field | Logical type | Unit / meaning | Nullability | Visibility |
|---|---|---|---|---|
| `router` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `audit` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `penalty` | number | synthetic currency | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `pi` | number | dimensionless fraction/probability | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `cell_id` | string | identifier / category | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `arm` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `policy` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `trust_feedback` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `penalty_label` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `audit_efficacy_evidence_allowed` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `learner` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `metric` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `baseline_cell_id` | string | identifier / category | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `delta_mean` | number | same units as metric; audit minus baseline | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `delta_lo` | number | same units as metric; audit minus baseline | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `delta_hi` | number | same units as metric; audit minus baseline | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `p_raw` | number | adjusted/unadjusted probability as named | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `testable` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `skip_reason` | string | category / text | yes (empty/null observed) | evaluation/config metadata; not T4 input |
| `Q_identifiable` | boolean | boolean indicator | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `baseline_Q_identifiable` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `astar_relation` | JSON string → object/list | JSON object: relation and frozen break-even bounds | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `report_family` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `p_holm_report` | number | adjusted/unadjusted probability as named | conditional; no null in this file | evaluation/config metadata; not T4 input |
| `significant_report` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `decision_a_family` | string | category / text | yes (empty/null observed) | evaluation/config metadata; not T4 input |
| `p_holm_decision_a` | number | adjusted/unadjusted probability as named | yes (empty/null observed) | evaluation/config metadata; not T4 input |
| `significant_decision_a` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |

Tiny example: first frozen row projected to these fields; CSV strings retained verbatim.

```json
{"router": "pilot", "audit": "a0.01", "penalty": "0.25", "pi": "1.0"}
```

## Decision A direction votes

Frozen example: `results/v1.1/v1.2_decision_a_eval/direction_consistency.csv`. One router × audit × penalty × metric vote summary; key those four fields. Nested objects list participating learners and break-even relations.

| Field | Logical type | Unit / meaning | Nullability | Visibility |
|---|---|---|---|---|
| `router` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `audit` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `penalty` | number | synthetic currency | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `metric` | string | category / text | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `audit_efficacy_evidence_allowed` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `report` | JSON string → object/list | JSON direction-consistency object | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `decision_a` | JSON string → object/list | JSON direction-consistency object | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `result1_hit` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `report_hit` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `astar_by_learner` | JSON string → object/list | JSON object keyed by learner | none observed; not a general validator | evaluation/config metadata; not T4 input |
| `all_supporting_learners_at_or_above_astar` | boolean | boolean indicator | none observed; not a general validator | evaluation/config metadata; not T4 input |

Tiny example: first frozen row projected to these fields; CSV strings retained verbatim.

```json
{"router": "pilot", "audit": "a0.01", "penalty": "0.25", "metric": "E"}
```

## T4 features

Frozen example: `results/v1.0/t4_eval/export/features_train.csv`. One run × seller feature window; key (run_id, seller_key); seed is split metadata. Same fields in test/PILOT exports.

| Field | Logical type | Unit / meaning | Nullability | Visibility |
|---|---|---|---|---|
| `run_id` | string | identifier / category | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `seed` | integer | seed identifier | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `seller_key` | string | first 12 SHA256 hex characters of run_id|seller_id | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `quoted_price_mean` | number | synthetic currency / 1K billed tokens | none observed; not a general validator | buyer feature whitelist |
| `quoted_price_std` | number | same price units | none observed; not a general validator | buyer feature whitelist |
| `declared_model` | string | category / text | none observed; not a general validator | buyer feature whitelist |
| `listed_quality_mean` | number | mean configured accuracy | none observed; not a general validator | buyer feature whitelist |
| `latency_mean` | number | milliseconds | conditional; no null in this file | buyer feature whitelist |
| `latency_std` | number | milliseconds | conditional; no null in this file | buyer feature whitelist |
| `latency_p50` | number | milliseconds | conditional; no null in this file | buyer feature whitelist |
| `latency_p90` | number | milliseconds | conditional; no null in this file | buyer feature whitelist |
| `billed_tokens_mean` | number | tokens | none observed; not a general validator | buyer feature whitelist |
| `billed_tokens_std` | number | tokens | none observed; not a general validator | buyer feature whitelist |
| `billed_tokens_sum` | number | tokens | none observed; not a general validator | buyer feature whitelist |
| `seller_jurisdiction` | string | category / text | none observed; not a general validator | buyer feature whitelist |
| `cross_border_share` | number | dimensionless fraction/probability | none observed; not a general validator | buyer feature whitelist |
| `blocked_share` | number | dimensionless fraction/probability | none observed; not a general validator | buyer feature whitelist |
| `violation_share` | number | dimensionless fraction/probability | none observed; not a general validator | buyer feature whitelist |
| `n_attempts` | integer | feature-window attempts | none observed; not a general validator | buyer feature whitelist |
| `n_served` | integer | allowed purchases | none observed; not a general validator | buyer feature whitelist |
| `n_buyers` | integer | distinct served buyers | none observed; not a general validator | buyer feature whitelist |
| `served_share_of_run` | number | seller served purchases / run served purchases in feature window | none observed; not a general validator | buyer feature whitelist |

Tiny example: first frozen row projected to these fields; CSV strings retained verbatim.

```json
{"run_id": "posted_price__audited_compliance_cascade__seed0", "seed": "0", "seller_key": "85f5208eef56", "quoted_price_mean": "0.0609"}
```

## T4 labels

Frozen example: `results/v1.0/t4_eval/export/labels_train.csv`. One run × seller target window and private references; key (run_id, seller_key). Join features on both fields. Same fields in test/PILOT exports.

| Field | Logical type | Unit / meaning | Nullability | Visibility |
|---|---|---|---|---|
| `run_id` | string | identifier / category | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `seed` | integer | seed identifier | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `seller_key` | string | first 12 SHA256 hex characters of run_id|seller_id | none observed; not a general validator | key/metadata; exclude T4 predictor IDs |
| `seller_id` | string | identifier / category | conditional; no null in this file | key/metadata; exclude T4 predictor IDs |
| `fraud_future` | integer 0/1 | boolean indicator | yes (empty/null observed) | evaluation/private; not a predictor |
| `fraud_future_swap` | integer 0/1 | boolean indicator | yes (empty/null observed) | evaluation/private; not a predictor |
| `fraud_future_theft` | integer 0/1 | boolean indicator | yes (empty/null observed) | evaluation/private; not a predictor |
| `fraud_future_downgrade` | integer 0/1 | boolean indicator | yes (empty/null observed) | evaluation/private; not a predictor |
| `n_target_served` | integer | target-window served purchases | none observed; not a general validator | evaluation/private; not a predictor |
| `fraud_order_share_target` | number | attacked / allowed target purchases | yes (empty/null observed) | evaluation/private; not a predictor |
| `fraud_billed_token_share_target` | number | attacked billed / all billed target tokens | yes (empty/null observed) | evaluation/private; not a predictor |
| `leakref_tokens_actual_mean` | number | tokens | conditional; no null in this file | evaluation/private; not a predictor |
| `leakref_billed_minus_actual_mean` | number | tokens | conditional; no null in this file | evaluation/private; not a predictor |

Tiny example: first frozen row projected to these fields; CSV strings retained verbatim.

```json
{"run_id": "posted_price__audited_compliance_cascade__seed0", "seed": "0", "seller_key": "85f5208eef56", "seller_id": "s00", "fraud_future": "0"}
```

## Conversion and joins

Legacy `orders.order_id` follows the raw `purchase_id` where present, else an exporter fallback. Audit rows cover served purchases only. Use run_id with seller/buyer IDs; seller catalog values are not chronological seller-state histories. `t_submit/t_deliver/t_settle` reuse log timestamps and are not independent measured events. `episodes.active_attack_rate` describes realized purchase attacks, while `learned_q_*` are separate legacy values; neither is a substitute for official Q.

Official CSV `config_hash` is a per-run config JSON SHA256 prefix, not the YAML file hash. The method encodes the audit setting; there is no standalone a or L column. `seller_learner` and input directory disambiguate equivalent method/π/seed keys across learners. Official board has no seller-level join; to recover it use raw transaction logs with matching run metadata, not an invented run_id.

Decision A cells join raw run rows on cell_id + learner. Contrasts join twice (cell_id and baseline_cell_id) with learner. Direction votes aggregate learners and join by router, audit, penalty, metric. `decision_a_eval.json` contains the same cell/contrast/vote records plus protocol hashes, input checks, RNG/bootstrap/family metadata and classification; it is not a per-purchase table. JSON-valued CSVs preserve nested data; flattening requires explicit field paths.

T4 keys are run_id + seller_key, never seller_key alone. `seller_id` appears in private labels to map back to raw logs. The manifest records run/seed membership, feature/target windows, whitelist and counts. Target labels are empty if no target-window purchase was served. Private `leakref_*` fields summarize feature-window actual tokens for the leakage checker and are not predictors. `n_target_served` distinguishes missing targets from true negatives. Feature activity/window statistics are not full-run board metrics. See T4_FEATURES.md.

Raw transaction logs, where retained, use `tokenmarket/logging_schema.py:SCHEMA`: one allowed/blocked attempt or unfilled-task row; `(run_id, task_id, portfolio_step)` locates a line and `purchase_id` supports audit joins. Last task row carries final outcome. Cache joins use `(model_name,prompt_sha256,max_new_tokens)`, not transaction task_id. Long task source IDs and revisions are documented in TASKS_AND_CACHE.md.
