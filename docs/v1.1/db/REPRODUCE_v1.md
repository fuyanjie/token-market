# Three-level reproduction — documentation version 1 (2026-11-15)

Run from repository root after the portable setup in [ENVIRONMENT](ENVIRONMENT.md). `python` below means the activated environment's interpreter. This guide distinguishes historical argv (recorded in run metadata), reconstructed commands (derived from argparse/code and frozen input paths; original argv not recorded), and commands executed in Pass 17. [ARTIFACT_MAP](ARTIFACT_MAP.md) supplies one row for every table/figure, including manual tables and producer gaps. No simulator grid, cache regeneration or full experiment was run in Pass 17.

## L1 — smoke and tests

Executed 2026-11-15 in the existing environment:

```bash
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/pass17-mpl python -m pytest -q -p no:cacheprovider --basetemp=/tmp/pass17-pytest -k 'not test_v01_numbers_unchanged'
```

Expected evidence: [pytest_2026-11-15.log](pytest_2026-11-15.log), 256 passed, five deselected, 35.14 seconds. The selected suite includes temporary-output smoke runs and mock inference. The five excluded golden-number parametrizations call cache preparation on the repository cache, potentially writing on a miss. This is an executed selected-suite pass, not a full-suite or historical official Decision A environment claim. Test assertions define their own tolerances; no new global tolerance is imposed.

## L2 — verify frozen outputs and re-render

Checksum verification, after the final manifest is built:

```bash
sha256sum -c release/v1.0/SHA256SUMS
```

Expected output: each repository-relative dependency reports OK; exact byte hashes, no numeric tolerance. The manifest excludes itself and temporary outputs. It describes referenced repository inputs, not a complete staged release.

Executed frozen-board analysis (reconstructed argv; original analysis argv not recorded):

```bash
python scripts/v1/analyze_scale_v1.py --in results/v1.0/main --peer results/v1.0/main_fp --out /tmp/pass17-l2/analysis
```

Expected: `inference.json`, `inference.md`, E/Q/Etok and scatter plots under the output directory. Pass 17 compared parsed `curves` and `q_gate` exactly with `results/v1.0/main/inference.json`: both equal. This is resampling existing per-seed summaries, not running the simulator. Optional analogous EXP3 command (documented, not executed):

```bash
python scripts/v1/analyze_scale_v1.py --in results/v1.0/main_exp3 --out /tmp/pass17-exp3-analysis
```

For hard-coded table/figure renderers, use this scratch mirror; it copies only script files and symlinks read-only inputs. These renderers have **no output flags**. Do not run them directly against protected paper tables in this checkout.

```bash
python - <<'PY'
from pathlib import Path
import shutil
root = Path.cwd()
scratch = Path('/tmp/pass17-l2')
(scratch/'scripts').mkdir(parents=True, exist_ok=True)
(scratch/'docs/latex-sigkdd-v1.0/tables').mkdir(parents=True, exist_ok=True)
(scratch/'docs/latex-sigkdd-v1.0/figures').mkdir(parents=True, exist_ok=True)
for name in ('results', 'configs', '.git'):
    target = scratch/name
    if not target.exists():
        target.symlink_to(root/name, target_is_directory=True)
target = scratch/'docs/v1.1'
if not target.exists():
    target.symlink_to(root/'docs/v1.1', target_is_directory=True)
for name in ('pass12_decision_a_tables.py', 'pass16_price_ratio_tables.py', 'figures_nature.py'):
    shutil.copyfile(root/'scripts'/name, scratch/'scripts'/name)
PY
python /tmp/pass17-l2/scripts/pass12_decision_a_tables.py
python /tmp/pass17-l2/scripts/pass16_price_ratio_tables.py
MPLCONFIGDIR=/tmp/pass17-mpl python /tmp/pass17-l2/scripts/figures_nature.py
```

Executed: all three exited zero. Expected outputs: the six `.tex` files under `/tmp/pass17-l2/docs/latex-sigkdd-v1.0/tables/`, and five paper PDF/PNG plot stems under its `figures/` (40-seller Pareto, E/Q vs π, Etok vs π; first-batch Pareto and E/Q vs π). All six tables are byte-identical to frozen paper files. Plot source values come directly from frozen JSON; a numeric/image/PDF binary tolerance is **not recorded**. The conceptual five-layer PNG/SVG is frozen; original raster-export argv is not recorded. A reconstructed Inkscape export is in the artifact map and was not executed.

T4 local evaluation commands, reconstructed from `run_t4_eval.py` argparse and the stored bootstrap counts, both executed:

```bash
python scripts/run_t4_eval.py --export-dir results/v1.0/t4_eval/export --out /tmp/pass17-l2/t4-d3 --n-boot 10000
python scripts/run_t4_eval.py --export-dir results/v1.0/t4_pilot_eval/export --out /tmp/pass17-l2/t4-pilot --n-boot 2000
```

Expected: `t4_eval.json`, `t4_eval.md`. Parsed result and notes arrays match `t4_eval_per_run/t4_eval.json` for D3 and `t4_pilot_eval/t4_eval.json` for PILOT exactly. Path provenance fields naturally differ. D3's stored missing-class limitations remain unchanged. A reconstructed original-count D3 evaluator uses `--n-boot 2000`; it was not additionally executed. No public scoring service is implied.

T4-E: reconstructed export/diagnostic commands from frozen logs (documented, not executed; they do not generate transactions):

```bash
python -m tokenmarket.t4_export --logs results/v1.0/t4_runs/logs/*.jsonl --config configs/v1.0/scale.yaml --out /tmp/pass17-t4-export --feature-rounds 32 --target-rounds 16 --train-seeds 0 1 2 3 4 5 6 7 8 9 10 11 12 13
python scripts/check_t4_leakage.py --dir /tmp/pass17-t4-export
python -m tokenmarket.t4_export --logs results/v1.0/t4_pilot/logs/*.jsonl --config configs/v1.0/scale.yaml --out /tmp/pass17-t4-pilot-export --feature-rounds 32 --target-rounds 16 --train-seeds 0 1 2 3 4 5 6 7 8 9 10 11 12 13
python scripts/check_t4_leakage.py --dir /tmp/pass17-t4-pilot-export
```

Expected: four CSVs and `t4_manifest.json`; comparator tolerance for re-export **not recorded**. The heuristic checker may flag simulator-correlated features and does not certify absence of all shortcuts. Evaluator supports `--drop-latency`; default evaluates both full/no-latency settings. See T4_FEATURES.md for exact fit and score rules.

Dated documentation checks, executed:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/pass17_inventory.py
PYTHONDONTWRITEBYTECODE=1 python scripts/pass17_schema.py
PYTHONDONTWRITEBYTECODE=1 python scripts/pass17_q_gate_report.py
PYTHONDONTWRITEBYTECODE=1 python scripts/pass17_artifact_map.py
```

These read frozen inputs and write only the specified documentation files under `docs/v1.1/db/`. The Q report checks both predicates at all π and compares with the frozen gate; it does not change a verdict. The first-batch Hedge report is not promoted into that gate.

All executions/statuses, times and equality comparisons are retained in [L2_REPORT.json](L2_REPORT.json) / [l2_2026-11-15.log](l2_2026-11-15.log). Manual tables are compiled from frozen LaTeX, not claimed to have an absent automatic converter. The standalone producer/argv for 40-seller `A2_paired.json` is not recorded; L2 preserves/checksums that readout. Its stored bootstrap settings do not establish the missing RNG call order.

## L3 — full regeneration (documented only; NOT executed)

Use an independent disposable working copy, **not this frozen checkout**. The commands below use historical output names inside that disposable copy. Cache preparation can append and load model weights on a miss; use a scratch cache copy, with complete coverage checked before execution. No network writes are required. Historical configs inherit relative paths; preserve the directory layout. This pass did not create the full working copy or execute any of these commands.

Recorded official v1.0 simulator argv, portable interpreter substituted for a machine path:

```bash
python scripts/run_v1.py --config configs/v1.0/scale.yaml --seeds 0-19 --jobs 8 --out results/v1.0/main
python scripts/run_v1.py --config configs/v1.0/scale.yaml --seeds 0-19 --jobs 8 --learner fictitious_play --out results/v1.0/main_fp
python scripts/run_v1.py --config configs/v1.0/scale.yaml --seeds 0-19 --jobs 8 --learner exp3 --out results/v1.0/main_exp3
python scripts/run_v1.py --config configs/v1.0/scale.yaml --seeds 0-19 --jobs 8 --pi-grid 1.0 --no-compliance-filter --out results/v1.0/a2_filter_off
```

Expected each: `per_seed.csv`, `run_meta.json`, `summary.md`, `tail_trade_rate.csv`. Run L2 analyzer for main/peer/EXP3 afterwards. Existing comparator recipe (reconstructed, not executed) verifies selected regenerated seeds against a frozen reference copied separately; numeric absolute tolerance 1e-9 is recorded in `compare_repro.py`, text/header/key equality exact:

```bash
python scripts/v1.1/compare_repro.py --ref /tmp/frozen-reference/per_seed.csv --new results/v1.0/main/per_seed.csv --seeds 0 1 2 --tol 1e-9 --out /tmp/pass17-compare
```

T4 generation argv recorded in the two run_meta files:

```bash
python scripts/run_v1.py --config configs/v1.0/scale.yaml --seeds 0-19 --pi-grid 1.0 --methods fixed_audit_a0.10 --resample-roster --out results/v1.0/t4_runs --log-dir results/v1.0/t4_runs/logs
python scripts/run_v1.py --config configs/v1.0/scale.yaml --seeds 0-19 --pi-grid 1.0 --methods pilot --resample-roster --out results/v1.0/t4_pilot --log-dir results/v1.0/t4_pilot/logs
```

Expected per-run raw transaction JSONL plus board files. Then apply T4-E and local evaluator commands above. No output tolerance is recorded for full T4 transaction regeneration.

Decision A recorded grid argv (absolute local paths made portable); reconstructed analyzer argv from argparse, official protocol hash and frozen paths:

```bash
python scripts/v1.1/run_wp1.py --mode decision_a --protocol docs/v1.1/PROTOCOL_v1.2.md --protocol-sha256 daddac6c0dddb22b08701caff5715e77215ae13a588512af176ff4933430b102 --n-rounds 1000 --out results/v1.1/v1.2_decision_a --jobs 8
python scripts/v1.1/analyze_decision_a.py --run results/v1.1/v1.2_decision_a --out results/v1.1/v1.2_decision_a_eval --protocol docs/v1.1/PROTOCOL_v1.2.md --protocol-sha256 daddac6c0dddb22b08701caff5715e77215ae13a588512af176ff4933430b102
```

Expected grid: manifest/run_meta/completion/completed_runs plus factorial cells/CSV. Expected analyzer: cells, contrasts, direction-consistency CSVs, readout JSON/MD and checksum sidecars. It requires a completed official grid and the recorded WP2 fact at `results/v1.1/v1.2_wp2_eval_r1000/wp2_eval.json`. That fact is a frozen prerequisite, not recomputed here. The analyzer guards fresh output paths under results/v1.1; `/tmp` cannot simply replace `--out` in this command. A disposable copy is necessary. Full Decision A comparison tolerance: **not recorded**; stored flags, classification and frozen statistical rules are authoritative.

Separate WP1 diagnostic analysis entry point, reconstructed and not executed (no flags; hard-coded paths, disposable copy only):

```bash
python scripts/v1.1/analyze_wp1.py
```

Expected `results/v1.1/wp1_eval/wp1_eval.{json,md}` and `contrasts.csv`; the script has no argparse interface and `--help` does not provide a safe dry run. This is a 48-round diagnostic, not Decision A. Its separate protocol is PROTOCOL_v1.1.md. No separate v1.2 WP1 eval exists; do not silently replace the diagnostic with the rerun.

Older recipes (separate scale; documented only):

```bash
python scripts/export_benchmark_layers.py --full --use-cache --out /tmp/pass17-legacy-export
python scripts/run_benchmark_tasks.py --full --use-cache --tasks T1 T2 T3 --out /tmp/pass17-legacy-tasks
python run_experiments.py --config configs/pi_dense.yaml --only F --seeds 0 1 2 --cache-file cache/llm_outputs.jsonl --results-dir /tmp/pass17-pi-dense
```

Expected five-file export plus optional private labels; T1/T2/T3 episodes/crossover/summary; F feedback_ablation JSON/MD/PNG. These do not regenerate the official main or Decision A tables. First-batch historical scripts `scripts/v1/run_v1_t2_a2.py`, `run_q_gate.py`, `recompute_q_v1.py`, `make_report_v1.py` have no output flags and hard-code result/cache paths: use only in a disposable copy and preserve their historical sequence (grid → Hedge diagnostic → present-round Q recompute → report). Full first-batch tolerance is only the comparator checks embedded in those scripts; other tolerances **not recorded**.

Fresh model/cache generation needs upstream models, source revision decisions and optional dependencies; historical revisions and complete installation records are not recorded. This is an acknowledged boundary, not a claim of clean-room regeneration. The paper's title/abstract/contributions, target scenario and all locked results remain unchanged.
