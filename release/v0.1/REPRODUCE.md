# Reproduce production board (v0.1)

Run from repository root: `/workspace/token-market` (needs project Python deps + optional LLM cache).

```bash
# 1) Five-layer export → exports/production/
python scripts/export_benchmark_layers.py --full --use-cache --with-labels

# 2) T1–T3 task boards → results/benchmark/production/
python scripts/run_benchmark_tasks.py --full --use-cache

# 3) Optional leaderboard smoke (does not replace production board)
python scripts/run_leaderboard.py --smoke
```

Config: `configs/benchmark/production.yaml`  
Knobs freeze: `adaptive_audit=false`, `reputation_rounds=0`, `escrow=false` (see `exports/production/knobs.yaml`).

This release already ships the frozen outputs under `exports/production/` and `results/benchmark/production/`. Re-running should match `SHA256SUMS` when cache + seeds align; treat mismatches as a regenerate event, not silent board edits.
