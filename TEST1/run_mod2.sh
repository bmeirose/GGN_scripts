#!/usr/bin/env bash
# run_pipeline.sh - Minimal conda-only version

TOY_SCRIPT="toy_data_generation.py"
HIBEAM_SCRIPT="HIBEAM_GNN_v1.py"
GPU_ID="${GPU_ID:-}"
ENV_NAME="hibeam_env"

log() { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
error() { printf "\033[1;31m[ERROR]\033[0m %s\n" "$*" >&2; }

# Load Anaconda module and setup
module load Anaconda3/2024.02-1
source $(conda info --base)/etc/profile.d/conda.sh

# Activate conda environment (assumes it already exists)
conda activate $ENV_NAME

# Install just matplotlib (since other packages were working)
conda install -c conda-forge matplotlib -y

# Check files exist
if [[ ! -f "$TOY_SCRIPT" ]]; then
    error "Toy data script not found: $TOY_SCRIPT"
    exit 1
fi

if [[ ! -f "$HIBEAM_SCRIPT" ]]; then
    error "HIBEAM script not found: $HIBEAM_SCRIPT"
    exit 1
fi

# GPU setup
if [[ -n "$GPU_ID" ]]; then
    export CUDA_VISIBLE_DEVICES="$GPU_ID"
    log "Using GPU: $GPU_ID"
fi

# Run pipeline
log "Running toy data generation..."
python "$TOY_SCRIPT"

log "Running HIBEAM GNN..."
python "$HIBEAM_SCRIPT"

log "Pipeline finished successfully!"
