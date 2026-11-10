# Reproduce pi_dense and T1–T3 (staging supplement, not a release)

This directory is a **staging** pack for the missing reproduction inputs that
paper §6.5 lists under `release/v0.1/` but that pack does not actually contain:
the dense-π (`pi_dense`) result files and the LLM output cache. It is **not** a
new public release. Do not upload or publish it. `release/v0.1/` is frozen and
was not modified.

Run all commands from the repository root. Cache-backed runs do not load model
weights when the cache covers the 80-task synthetic pool (it does; see below).

Python: **3.13.5**. Dependencies: see top-level `requirements.txt` (core pins are
enough for this path).

Cache path used by the configs: `cache/llm_outputs.jsonl`
(`run.cache_file` in `configs/default.yaml`). A copy is in
`release/v0.1.1-supplement/cache/llm_outputs.jsonl` (304242 bytes; sha256 in
`MANIFEST`). Point `--cache-file` or `CACHE=` at either copy.

If the cache is incomplete, `prepare()` / `precompute()` will try to load
`Qwen/Qwen2.5-0.5B-Instruct` and `Qwen/Qwen2.5-1.5B-Instruct` via transformers
and write new lines into the cache file. Do not run that path unless you intend
to regenerate outputs.

A wrapper script implements the same commands:

```bash
scripts/reproduce_pi_dense.sh --smoke              # tiny end-to-end check
scripts/reproduce_pi_dense.sh --full-F             # experiment F, seeds 0–2
scripts/reproduce_pi_dense.sh --full-T123          # production T1–T3
scripts/reproduce_pi_dense.sh --full               # both full targets
```

Full modes write under `results/_repro/` by default and **do not overwrite**
`results/pi_dense/` or `results/benchmark/production/`.

## One command per result

### 1. Dense π grid (experiment F / pi_dense)

```bash
python run_experiments.py \
  --config configs/pi_dense.yaml \
  --only F \
  --seeds 0 1 2 \
  --cache-file cache/llm_outputs.jsonl \
  --results-dir results/_repro/pi_dense
```

This is the authoritative π grid in `configs/pi_dense.yaml` (experiment F):
policies `pilot_compliant`, `stageroute_compliant`, `audited_compliance_cascade`;
`π ∈ {1.0, 0.2, 0.18, 0.15, 0.12, 0.10, 0.08, 0.06, 0.05, 0.0}`; `L = 0`;
`n_tasks=480`; `n_rounds=48`. Outputs: `feedback_ablation.{json,md,png}` and
`experiments_summary.md`. Staged copies of the existing run are under
`release/v0.1.1-supplement/results/pi_dense/`.

The saved JSON stores **seed-mean and std only**. See “Per-seed tables” below.

### 2. T1 — fixed audit-rate deterrence

```bash
python scripts/run_benchmark_tasks.py \
  --full --use-cache --tasks T1 \
  --out results/_repro/t123
```

Uses `configs/benchmark/production.yaml` (`--full`), seeds `{0,1,2}`, cache-backed
seller backends. Writes `T1_episodes.jsonl` (one row per seed).

### 3. T2 — sparse-label regime (dense π grid, per seed)

```bash
python scripts/run_benchmark_tasks.py \
  --full --use-cache --tasks T2 \
  --out results/_repro/t123
```

Same production scale and the same π grid as experiment F. Writes
`T2_episodes.jsonl` (one row per seed × policy × π) and `T2_crossover.json`.
A copy of the existing production `T2_episodes.jsonl` is in this supplement
(see “Per-seed tables”).

### 4. T3 — same-budget adaptive audit (appendix)

```bash
python scripts/run_benchmark_tasks.py \
  --full --use-cache --tasks T3 \
  --out results/_repro/t123
```

Or run T1–T3 together: `python scripts/run_benchmark_tasks.py --full --use-cache`.

## Per-seed tables

`results/pi_dense/feedback_ablation.json` (and the copy in this supplement) has
no per-seed rows. `experiment_F` in `tokenmarket/experiments.py` calls
`run_point()`, which does keep a `per_seed` list in memory, but the writer only
records mean and std. **There is no CLI flag** to dump per-seed pi_dense tables
from `run_experiments.py` / experiment F.

The per-seed numbers for the same dense π grid, policies, and seeds `{0,1,2}`
already exist in the T2 production episodes (Experiment reconstructed
per-seed crossovers from this file; this supplement only stages it):

`results/benchmark/production/T2_episodes.jsonl`
(copied to `release/v0.1.1-supplement/results/benchmark/production/T2_episodes.jsonl`)

Each line is one episode with `seed`, `policy`, `pi`, `L`, `J`,
`fraud_share`, `active_attack_rate`, `learned_q_swap`, `learned_q_theft`, and
related fields. To reshape into a per-seed table comparable to the pi_dense
mean/std rows — **without computing a crossover or π\*** — for example:

```python
import json, collections
rows = [json.loads(l) for l in open(
    "release/v0.1.1-supplement/results/benchmark/production/T2_episodes.jsonl")
    if l.strip()]
# one record per (seed, policy, pi); group however you need
by_seed = collections.defaultdict(list)
for r in rows:
    by_seed[r["seed"]].append(r)
# columns of interest: seed, policy, pi, J, fraud_share, active_attack_rate,
# learned_q_swap, learned_q_theft
```

No other per-seed pi_dense dump was found under `results/pi_dense/`.

## Smoke

```bash
scripts/reproduce_pi_dense.sh --smoke
```

Runs experiment F with 1 seed, 1 π (`1.0`), 24 tasks, 4 rounds, and a matching
one-point T2 cache-backed run, writing under `results/_smoke_repro/`.
