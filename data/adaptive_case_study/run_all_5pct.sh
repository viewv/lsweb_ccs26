#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TRIALS="${TRIALS:-1000}"
SEED="${SEED:-20260722}"
RESULTS_ROOT="${RESULTS_ROOT:-$SCRIPT_DIR/results_repro}"
FIGURE_DIR="${FIGURE_DIR:-$SCRIPT_DIR/figures_repro}"
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl-case-study-1}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp/case-study-1-cache}"
mkdir -p "$MPLCONFIGDIR" "$XDG_CACHE_HOME/fontconfig"

cd "$SCRIPT_DIR"
if ! "$PYTHON_BIN" -c "import numpy, pandas, matplotlib" >/dev/null 2>&1; then
  echo "Missing Python dependencies for $PYTHON_BIN." >&2
  echo "Create/activate a virtual environment and run:" >&2
  echo "  python3 -m pip install -r $SCRIPT_DIR/requirements.txt" >&2
  exit 1
fi

"$PYTHON_BIN" -m unittest -v test_adaptive_sampling.py
"$PYTHON_BIN" run_tranco_experiment.py \
  --trials "$TRIALS" \
  --seed "$SEED" \
  --tolerance 0.05 \
  --output-dir "$RESULTS_ROOT/tranco"
"$PYTHON_BIN" run_tranco_top100k_impact_experiment.py \
  --trials "$TRIALS" \
  --seed "$SEED" \
  --tolerance 0.05 \
  --output-dir "$RESULTS_ROOT/tranco_top100k_impact"
"$PYTHON_BIN" run_commoncrawl_experiment.py \
  --trials "$TRIALS" \
  --seed "$SEED" \
  --tolerance 0.05 \
  --output-dir "$RESULTS_ROOT/commoncrawl"
"$PYTHON_BIN" plot_results.py \
  --tranco-results "$RESULTS_ROOT/tranco" \
  --tranco-top100k-impact-results "$RESULTS_ROOT/tranco_top100k_impact" \
  --commoncrawl-results "$RESULTS_ROOT/commoncrawl" \
  --figure-dir "$FIGURE_DIR"

echo "5% results written to $RESULTS_ROOT"
echo "5% figures written to $FIGURE_DIR"
