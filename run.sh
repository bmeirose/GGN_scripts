#!/usr/bin/env bash
# run_pipeline.sh
# Run toy data generation first, then HIBEAM GNN.

set -euo pipefail

TOY_SCRIPT="toy_data_generation.py"
HIBEAM_SCRIPT="HIBEAM_GNN_v1.py"

# Optional GPU selection (set GPU_ID before running, e.g. GPU_ID=0 ./run_pipeline.sh)
GPU_ID="${GPU_ID:-}"

log() { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }

# Check files exist
if [[ ! -f "$TOY_SCRIPT" ]]; then
  echo "[ERR] Toy data generation script not found: $TOY_SCRIPT" >&2
  exit 1
fi

if [[ ! -f "$HIBEAM_SCRIPT" ]]; then
  echo "[ERR] HIBEAM GNN script not found: $HIBEAM_SCRIPT" >&2
  exit 1
fi

# GPU visibility
if [[ -n "$GPU_ID" ]]; then
  export CUDA_VISIBLE_DEVICES="$GPU_ID"
  log "Set CUDA_VISIBLE_DEVICES=$GPU_ID"
fi

# Step 1: Toy data generation
log "Running toy data generation..."
python "$TOY_SCRIPT"

# Step 2: Run HIBEAM GNN
log "Running HIBEAM GNN..."
python "$HIBEAM_SCRIPT"

log "Pipeline finished successfully!"
