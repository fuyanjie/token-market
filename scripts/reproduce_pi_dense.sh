#!/usr/bin/env bash
# Reproduce the dense-π experiment (experiment F / pi_dense) and the T1–T3
# protocol boards from the on-disk LLM cache. Does not load model weights when
# the cache is complete. Never writes into results/pi_dense/ or release/v0.1/.
#
# Usage (from repository root):
#   scripts/reproduce_pi_dense.sh              # tiny smoke (default)
#   scripts/reproduce_pi_dense.sh --smoke
#   scripts/reproduce_pi_dense.sh --full-F     # seeds 0-2, full π grid (experiment F)
#   scripts/reproduce_pi_dense.sh --full-T123  # production T1–T3 with --use-cache
#   scripts/reproduce_pi_dense.sh --full       # both --full-F and --full-T123
#
# Optional:
#   PYTHON=/path/to/python CACHE=cache/llm_outputs.jsonl OUT=results/_repro \
#     scripts/reproduce_pi_dense.sh --smoke
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-}"
if [[ -z "$PYTHON" ]]; then
  if [[ -x /workspace/tmvenv/bin/python ]]; then
    PYTHON=/workspace/tmvenv/bin/python
  else
    PYTHON="$(command -v python3)"
  fi
fi
CACHE="${CACHE:-$ROOT/cache/llm_outputs.jsonl}"
# Prefer the staged supplement cache if the default path is missing.
if [[ ! -f "$CACHE" && -f "$ROOT/release/v0.1.1-supplement/cache/llm_outputs.jsonl" ]]; then
  CACHE="$ROOT/release/v0.1.1-supplement/cache/llm_outputs.jsonl"
fi

MODE="smoke"
OUT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --smoke) MODE="smoke"; shift ;;
    --full-F) MODE="full-F"; shift ;;
    --full-T123) MODE="full-T123"; shift ;;
    --full) MODE="full"; shift ;;
    --out) OUT="$2"; shift 2 ;;
    --cache) CACHE="$2"; shift 2 ;;
    --python) PYTHON="$2"; shift 2 ;;
    -h|--help) sed -n '2,22p' "$0"; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ ! -f "$CACHE" ]]; then
  echo "LLM cache not found: $CACHE" >&2
  echo "Expected cache/llm_outputs.jsonl or release/v0.1.1-supplement/cache/llm_outputs.jsonl" >&2
  exit 1
fi
if [[ ! -x "$PYTHON" ]] && ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "python not found: $PYTHON" >&2
  exit 1
fi

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"
export MPLBACKEND="${MPLBACKEND:-Agg}"

echo "python: $PYTHON"
echo "cache:  $CACHE"
"$PYTHON" -c "import sys; print('version:', sys.version.splitlines()[0])"

write_rel_extends() {
  # $1 = yaml path, $2 = parent yaml; YAML body is read from this function's stdin.
  # Do not feed the body to `python - <<`, which would consume stdin for the program.
  local dest="$1" parent="$2"
  local bodyfile
  bodyfile="$(mktemp)"
  cat > "$bodyfile"
  "$PYTHON" - "$dest" "$parent" "$bodyfile" << 'PY'
import os, sys
dest, parent, bodyfile = sys.argv[1], sys.argv[2], sys.argv[3]
body = open(bodyfile, encoding="utf-8").read()
os.remove(bodyfile)
rel = os.path.relpath(parent, os.path.dirname(os.path.abspath(dest)))
os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
with open(dest, "w", encoding="utf-8") as fh:
    fh.write("extends: " + rel + "\n")
    fh.write(body)
print("wrote", dest, "extends", rel)
PY
}

run_smoke() {
  local dest="${OUT:-$ROOT/results/_smoke_repro}"
  mkdir -p "$dest"
  local cfg="$dest/pi_dense_smoke.yaml"
  write_rel_extends "$cfg" "$ROOT/configs/pi_dense.yaml" << 'YAML'
# Tiny smoke overlay for experiment F. Lists replace parent lists
# (see tokenmarket.config.deep_merge).
run:
  n_tasks: 24
  n_rounds: 4
experiments:
  seeds: [0]
  F:
    policies: [audited_compliance_cascade]
    reveal_probs: [1.0]
    delays: [0]
    combined: []
YAML
  echo "==> smoke experiment F (1 seed, 1 pi, 24 tasks, 4 rounds)"
  "$PYTHON" "$ROOT/run_experiments.py" \
    --config "$cfg" --only F --seeds 0 \
    --cache-file "$CACHE" --results-dir "$dest/pi_dense"
  echo "==> smoke T2 (1 seed, 1 pi, 24 tasks) via run_benchmark_tasks.py --use-cache"
  local t2cfg="$dest/t2_smoke.yaml"
  write_rel_extends "$t2cfg" "$ROOT/configs/benchmark/production.yaml" << 'YAML'
run:
  n_tasks: 24
  n_rounds: 4
  seeds: [0]
benchmark:
  seeds: [0]
  tasks:
    T2:
      pi_grid: [1.0]
YAML
  "$PYTHON" "$ROOT/scripts/run_benchmark_tasks.py" \
    --config "$t2cfg" --use-cache --tasks T2 --seeds 0 --n-tasks 24 \
    --out "$dest/t2"
  echo "smoke outputs under $dest"
  ls -la "$dest/pi_dense/feedback_ablation.json" "$dest/t2/T2_episodes.jsonl"
}

run_full_F() {
  local dest="${OUT:-$ROOT/results/_repro}/pi_dense"
  mkdir -p "$dest"
  echo "==> full experiment F (seeds 0 1 2, dense pi grid, n_tasks=480, n_rounds=48)"
  echo "    writing to $dest  (does not overwrite results/pi_dense/)"
  "$PYTHON" "$ROOT/run_experiments.py" \
    --config "$ROOT/configs/pi_dense.yaml" --only F --seeds 0 1 2 \
    --cache-file "$CACHE" --results-dir "$dest"
  echo "full F outputs under $dest"
}

run_full_T123() {
  local dest="${OUT:-$ROOT/results/_repro}/t123"
  mkdir -p "$dest"
  echo "==> full T1-T3 production boards with --use-cache"
  echo "    writing to $dest  (does not overwrite results/benchmark/production/)"
  "$PYTHON" "$ROOT/scripts/run_benchmark_tasks.py" \
    --full --use-cache --tasks T1 T2 T3 --out "$dest"
  echo "full T1-T3 outputs under $dest"
}

case "$MODE" in
  smoke) run_smoke ;;
  full-F) run_full_F ;;
  full-T123) run_full_T123 ;;
  full) run_full_F; run_full_T123 ;;
esac
