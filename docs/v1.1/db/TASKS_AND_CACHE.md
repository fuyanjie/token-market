# Tasks and cache — documentation version 1 (2026-11-15)

Sources: `tokenmarket/tasks.py`, `tokenmarket/backends.py`, `tokenmarket/cache.py`, `tokenmarket/precompute.py`, `tokenmarket/sim.py`, inherited configuration and recorded `run_meta.json`. Counts below were read from frozen files or constructed in memory, without model generation. Rebuild the inventory with `PYTHONDONTWRITEBYTECODE=1 python scripts/pass17_inventory.py`; see [TASK_COUNTS.json](TASK_COUNTS.json) for hashes.

| Asset | Rows / IDs | Distinct question text or prompt hashes | Scope |
|---|---:|---:|---|
| `data/raw/gsm8k_test.jsonl` | 1319 | 1319 | GSM8K test source |
| `data/raw/math500_test.jsonl` | 500 | 500 | MATH-500 test source |
| `data/long_tasks.jsonl` | 48 / 48 IDs | 48 | 28 GSM8K, 20 MATH-500 |
| In-memory synthetic pool, default/production/scale | 80 / 80 IDs | 77 | Same task seed 1234 |
| `cache/llm_outputs.jsonl` | 250 unique cache keys | 125 | 125 records per Qwen checkpoint; 77 short + 48 long each |

Pool entries and unique question text are different units. Three repeated synthetic questions explain why 80 IDs need only 77 prompt hashes per model; this is a documentation distinction, not a correction to the paper's 80-task pool. Cache `pool_task_id` has 125 distinct stored values because identical rendered prompts share a key. It cannot be used alone as an exhaustive list of the 80 synthetic IDs.

## Selection and provenance

`build_synthetic_pool` cycles configured task types (arithmetic, word_problem, sequence, logic) and difficulty 1–3, using `random.Random('task-pool-1234')`. It generates integer answers from templates. `build_long_subset` ranks GSM8K rows by reference-solution nonempty line count and then reference length, with source index as tie breaker; it draws 28 from the top 84 with `random.Random('long-subset-2024')`. Gold is parsed after `####`, commas removed. MATH-500 selection requires an integer answer matching `^-?\d+$` and level ≥3; the same RNG draws up to 20, and output preserves source index, unique_id and subject where present. Long-task difficulty is 4 for GSM8K, 5 for MATH-500. CLI: `python scripts/build_long_tasks.py --gsm8k data/raw/gsm8k_test.jsonl --math500 data/raw/math500_test.jsonl --n-gsm8k 28 --n-math 20 --seed 2024 --out /tmp/pass17-long-tasks.jsonl` (reconstructed, not executed).

Recorded source IDs: `openai/grade-school-math`, `HuggingFaceH4/MATH-500` via `openai/prm800k`, and `Qwen/Qwen2.5-0.5B-Instruct` / `Qwen/Qwen2.5-1.5B-Instruct`. Dataset and model commit revisions, tokenizer revisions and download argv: **not recorded**. File hashes pin local bytes, not upstream revisions. Source licensing questions are in the component matrix.

## Decode, parse and reuse

Synthetic prompts use `PROMPT_V2`; long prompts use `PROMPT_LONG`, rendered before SHA256 hashing. Cache key is `(model_name, prompt_sha256, max_new_tokens)`, not task ID or run seed. Cached limits are 256 short / 512 long. `LocalHFRunner` uses a user chat template with a generation prompt, left padding, model eval/inference mode, greedy `do_sample=False`, and no temperature/top-p/top-k sampling. Its default CPU dtype is float32; the configured long path uses bfloat16 with its own batch settings. `reasoning_tokens` counts generated tokens before EOS/pad, excluding the input prompt. `gen_time_s` is an amortized token-proportional share of batch wall time, not a measured market service latency.

`parse_answer` uses the last explicit `Answer:` numeric marker (decorations permitted), else the last number in the text; commas are stripped. Values must be within 1e-9 of an integer or become null. Correctness compares parsed answer with gold. Confidence is a deterministic answer-format/self-consistency proxy, not a probability learned from real sellers. Cached truncation cuts output and reparses; mock truncation has its own simulated correctness rule.

`sample_run_tasks` concatenates independently shuffled pool permutations using `random.Random('tasks-<seed>')`, truncates to the requested instance count, assigns buyers cyclically and draws sensitivity/consent. IDs are `t<instance>_<pool_id>`. Pool and cached generations are shared across run seeds and conditions. Shared question/cache resources also cross T4's train/test run split; it is not a task-disjoint or model-disjoint split.

`MockLLM` samples correctness from the configured model/difficulty accuracy and returns gold or a perturbed integer; tokens are Gaussian around the configured difficulty/effort mean with a floor, and confidence is noisy and clipped. Its truncated answer survives with probability proportional to retained tokens. These are synthetic outcomes, not local Qwen inference. `CachedLocalBackend` reads the actual serving model's cached generation; a missing key raises an error. `prepare` may precompute missing keys and append to cache, so full rerun recipes require a scratch cache copy.

## Which assets feed which results

| Experiment/readout | Tasks and outputs used |
|---|---|
| Legacy five-file export, production T1–T3 and dense π | `configs/benchmark/production.yaml` inherits the fixed synthetic pool and cache; long assets are separate |
| v1.0 official main / main_fp / main_exp3 / filter-off | `configs/v1.0/scale.yaml`, inherited synthetic pool; two cached Qwen backends and mock roster |
| Decision A | `results/v1.1/v1.2_decision_a/run_meta.json:base_config`, same synthetic pool; more task instances do not create more unique tasks |
| WP1 cascade diagnostic | `results/v1.1/wp1/run_meta.json`, inherited synthetic pool |
| Official D3 and supplemental PILOT T4 | `t4_runs` / `t4_pilot` metadata, same synthetic pool/cache, resampled rosters; 32-round feature / 16-round target windows |
| Long-task assets | `data/long_tasks.jsonl`, long cache rows, `results/long_math*/`; existence alone is not main-experiment task coverage |

Exact per-run task sequence can be reconstructed from seed and sampling code; main CSVs contain no complete task-ID list. T4 raw transaction logs carry pool/instance IDs. This pass did not infer a different workload from cache contents.
