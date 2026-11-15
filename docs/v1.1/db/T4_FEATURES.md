# T4 construction — documentation version 1 (2026-11-15)

Implementation: `tokenmarket/t4_export.py:build_unit_rows`, `split_runs`, `tokenmarket/t4_models.py`, `scripts/run_t4_eval.py`. This documents implementation and local records; it does not revise the paper's label-access wording or official D3 verdict.

Row unit is `(run_id, seller_key)`, for a seller with at least one purchase attempt in the feature window. Features use log round <32 (paper rounds 1–32), targets log rounds 32–47 (paper rounds 33–48). Sellers appearing only in the target window have no exported feature row. `seller_key` is the first 12 SHA256 hex characters of `run_id|seller_id`; raw seller_id is confined to the label export. Default sorted seed split is 0–13 train, 14–19 test; explicit train runs override train seeds. All rows of each run stay together. T4 rosters are resampled, but task pool and cached Qwen outputs are shared across train/test. This is not a holdout of tasks or model generations.

| Feature group | Aggregation over feature window |
|---|---|
| Quote | Price mean and population std over all attempts |
| Declared model; jurisdiction | First attempted row's claimed model and seller jurisdiction |
| Listed quality | Mean configured accuracy across listed difficulties for the claimed model; absent without config |
| Latency | Mean, population std, p50, p90 over allowed purchases; quantile is sorted `ceil(q*n)-1` |
| Billing | Mean/std/sum of billed tokens over allowed purchases |
| Flow | Cross-border and blocked shares over attempts; violation share over served purchases |
| Activity | Attempts, served purchases, distinct served buyers, seller's served share of the run |

Empty means/std/quantiles become empty CSV cells; empty billed sum and no-served-run share are zero. All four latency columns are dropped together for the six-item ablation. Seven protocol items expand into multiple columns; they are not seven scalar predictors. Every non-key column must pass the whitelist and blacklist. `run_id`, `seed`, `seller_key` are join/group keys and excluded from learned predictor inputs. Peer rule scores group by run_id and declared_model; they do not learn a run-ID predictor.

Numeric encoder fitting uses **only the training rows with a nonempty label for the attack being scored**: median imputation (zero when wholly absent), train filled-column mean and population std; std ≤1e-12 becomes 1. Test values use those fitted statistics. Declared model and jurisdiction use train-vocabulary one-hot encoding. Unknown categories yield all-zero indicators for that category. No test-fitted normalization is used by learned models. The rule baseline uses test-run, same-declared-model peers, imputes missing values with that peer median, and sums z(-quote mean)+z(billed-token mean); singleton/constant groups contribute zero. It uses no latency.

Logistic regression: L2=1, unpenalized intercept, Newton/IRLS, 50 iterations maximum, stop at maximum absolute step <1e-8. GBDT: logistic loss, 100 trees, learning rate 0.1, depth 3, minimum leaf 5, leaf L2=1, 16 candidate quantile thresholds; deterministic, no row/column subsampling. These are code defaults. A hyperparameter search, validation-set choice or tuning history for T4 is **not recorded**; no such selection is claimed.

Targets: any realized attack / swap / theft / downgrade on an allowed target-window purchase; target-window no service yields empty labels rather than negatives. Training requires both classes; otherwise an attack type is skipped. Official scores average the defined metric per test run. AUROC requires both classes, with average ranks for equal scores; AP requires a positive and uses stable input order to break score ties. Precision@10 selects the first min(10,n) descending-score candidates and divides by the selected count, so for n<10 it is the positive fraction among all available candidates. Empty runs are undefined. Macro averaging gives each defined run equal weight; pooled seller metrics are explicitly nonprotocol diagnostics.

CIs resample test runs with replacement, pairing the full-minus-no-latency difference on runs where both scores exist. `boot_mean_ci` uses only defined per-run scores. Seed is 20261110; default B=2000, the stored D3 per-run recompute uses B=10000. See [STATISTICS](STATISTICS.md). `t4_manifest.json` records actual seeds and rows, not an immutable task-disjoint split.

Frozen examples: `results/v1.0/t4_eval/export/` has 259 train / 104 test feature units; `t4_pilot_eval/export/` has 551 / 224. These include units with missing target labels; they are not the paper's counts restricted to sellers trading in the target window. [SCHEMA_v1](SCHEMA_v1.md) defines the joins and null rules. [REPRODUCE_v1](REPRODUCE_v1.md) supplies export, leakage-check and evaluation commands.
