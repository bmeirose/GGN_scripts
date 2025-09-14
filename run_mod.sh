# TO RUN IN DEBUG MODE: bash -x ./run_mod.sh 2>&1 | tee debug.log

#!/usr/bin/env bash
# run_pipeline.sh - With graphnet installation

TOY_SCRIPT="toy_data_generation.py"
HIBEAM_SCRIPT="HIBEAM_GNN_v1.py"
GPU_ID="${GPU_ID:-}"
ENV_NAME="hibeam_env"
ENV_FILE="environment.yml"

log() { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
error() { printf "\033[1;31m[ERROR]\033[0m %s\n" "$*" >&2; }

# Load Anaconda module and setup
log "Loading Anaconda module..."
module load Anaconda3/2024.02-1
source $(conda info --base)/etc/profile.d/conda.sh

# Create environment from file if it doesn't exist
if ! conda env list | grep -q "^$ENV_NAME "; then
    if [[ -f "$ENV_FILE" ]]; then
        log "Creating environment from $ENV_FILE"
        conda env create -f $ENV_FILE
    else
        log "Environment file $ENV_FILE not found, creating basic environment"
        conda create -n $ENV_NAME python=3.9 -y
    fi
fi

# Activate conda environment
log "Activating conda environment: $ENV_NAME"
conda activate $ENV_NAME

# Install required packages if not already installed
log "Checking/installing required packages..."
if ! python -c "import pyarrow" 2>/dev/null; then
    log "Installing pyarrow..."
    conda install -c conda-forge pyarrow -y
fi

if ! python -c "import pandas" 2>/dev/null; then
    log "Installing pandas..."
    conda install pandas -y
fi

if ! python -c "import torch" 2>/dev/null; then
    log "Installing pytorch..."
    conda install pytorch torchvision torchaudio -c pytorch -y
fi

if ! python -c "import matplotlib" 2>/dev/null; then
    log "Installing matplotlib..."
    conda install -c conda-forge matplotlib -y
fi

# === ADD GRAPHNET INSTALLATION ===
if ! python -c "import graphnet" 2>/dev/null; then
    log "Installing graphnet..."
    pip install graphnet
fi

# Check files exist
if [[ ! -f "$TOY_SCRIPT" ]]; then
    error "Toy data generation script not found: $TOY_SCRIPT"
    exit 1
fi

if [[ ! -f "$HIBEAM_SCRIPT" ]]; then
    error "HIBEAM GNN script not found: $HIBEAM_SCRIPT"
    exit 1
fi

# GPU visibility
if [[ -n "$GPU_ID" ]]; then
    export CUDA_VISIBLE_DEVICES="$GPU_ID"
    log "Set CUDA_VISIBLE_DEVICES=$GPU_ID"
fi

# Step 1: Toy data generation
log "Running toy data generation..."
if python "$TOY_SCRIPT"; then
    log "Toy data generation completed successfully"
else
    error "Toy data generation failed with exit code $?"
    exit 1
fi

# Step 2: Run HIBEAM GNN
log "Running HIBEAM GNN..."
if python "$HIBEAM_SCRIPT"; then
    log "HIBEAM GNN completed successfully"
else
    error "HIBEAM GNN failed with exit code $?"
    exit 1
fi

log "Pipeline finished successfully!"
