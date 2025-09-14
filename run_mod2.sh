#!/usr/bin/env bash
# run_pipeline_safe.sh - SAFE version of run_mod2.sh

TOY_SCRIPT="toy_data_generation.py"
HIBEAM_SCRIPT="HIBEAM_GNN_v1.py"
GPU_ID="${GPU_ID:-}"
ENV_NAME="hibeam_env"
ENV_PATH="$HOME/.conda/envs/$ENV_NAME"

log() { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
error() { printf "\033[1;31m[ERROR]\033[0m %s\n" "$*" >&2; }

# Load Anaconda module and setup
log "Loading Anaconda module..."
module load Anaconda3/2024.02-1
source $(conda info --base)/etc/profile.d/conda.sh

# --- 1. Check if environment exists ---
if conda env list | grep -q "$ENV_NAME"; then
    log "Environment $ENV_NAME already exists. Reusing it..."
    conda activate "$ENV_NAME"
    log "Updating packages in environment..."
    conda update -n "$ENV_NAME" --all -y || log "Update failed, continuing anyway..."
else
    log "Environment $ENV_NAME does not exist. Creating fresh environment..."
    conda create -n "$ENV_NAME" python=3.9 -y
    conda activate "$ENV_NAME"

    log "Installing required packages..."
    conda install -c conda-forge -c pytorch \
        pyarrow pandas matplotlib pytorch torchvision torchaudio \
        pytorch-lightning pytorch-geometric -y

    log "Installing graphnet via pip..."
    pip install git+https://github.com/graphnet-team/graphnet.git
fi

# --- 2. Test critical imports ---
log "Testing critical imports..."
python - <<EOF || { error "Critical imports failed"; exit 1; }
import torch
import pyarrow
import pandas
import matplotlib
import pytorch_lightning
import torch_geometric
from graphnet.data import GraphNeTDataModule
EOF
log "All imports successful!"

# --- 3. Check scripts exist ---
[[ -f "$TOY_SCRIPT" ]] || { error "Toy data script not found"; exit 1; }
[[ -f "$HIBEAM_SCRIPT" ]] || { error "HIBEAM GNN script not found"; exit 1; }

# --- 4. GPU visibility ---
[[ -n "$GPU_ID" ]] && export CUDA_VISIBLE_DEVICES="$GPU_ID" && log "Set CUDA_VISIBLE_DEVICES=$GPU_ID"

# --- 5. Run toy data generation ---
log "Running toy data generation..."
python "$TOY_SCRIPT" || { error "Toy data generation failed"; exit 1; }

# --- 6. Run HIBEAM GNN ---
log "Running HIBEAM GNN..."
python "$HIBEAM_SCRIPT" || { error "HIBEAM GNN failed"; exit 1; }

log "Pipeline finished successfully!"

