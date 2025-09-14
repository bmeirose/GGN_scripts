#!/usr/bin/env bash
# Fully safe run_pipeline for HIBEAM

TOY_SCRIPT="toy_data_generation.py"
HIBEAM_SCRIPT="HIBEAM_GNN_v1.py"
GPU_ID="${GPU_ID:-}"
ENV_NAME="hibeam_env"
ENV_PATH="$HOME/.conda/envs/$ENV_NAME"
PIP_CACHE="$HOME/pip_cache"

log() { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
error() { printf "\033[1;31m[ERROR]\033[0m %s\n" "$*" >&2; }

# --- 1. Load Anaconda module ---
log "Loading Anaconda module..."
module load Anaconda3/2024.02-1
source $(conda info --base)/etc/profile.d/conda.sh

# --- 2. Prepare pip cache ---
mkdir -p "$PIP_CACHE"
export PIP_CACHE_DIR="$PIP_CACHE"

# --- 3. Activate or create environment ---
if conda env list | grep -q "$ENV_NAME"; then
    log "Reusing existing environment $ENV_NAME..."
    conda activate "$ENV_NAME"
else
    log "Creating environment $ENV_NAME..."
    conda create -n "$ENV_NAME" python=3.9 -y
    conda activate "$ENV_NAME"
fi

# --- 4. Install or upgrade core packages ---
log "Installing/updating core packages..."
conda install -y -c conda-forge pyarrow pandas matplotlib pytorch-lightning
# PyTorch core installation (CPU version)
if ! python -c "import torch" &>/dev/null; then
    log "Installing PyTorch CPU version..."
    pip install --user torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# --- 5. Install PyTorch Geometric if missing ---
if ! python -c "import torch_geometric" &>/dev/null; then
    log "Installing PyTorch Geometric CPU wheels..."
    pip install --user torch-scatter torch-sparse torch-cluster torch-spline-conv torch-geometric --extra-index-url https://data.pyg.org/whl/torch-2.1.0+cpu.html
fi

# --- 6. Install GraphNet if missing ---
if ! python -c "from graphnet.data import GraphNeTDataModule" &>/dev/null; then
    log "Installing GraphNet..."
    pip install --user git+https://github.com/graphnet-team/graphnet.git
fi

# --- 7. Test critical imports ---
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

# --- 8. Check scripts ---
[[ -f "$TOY_SCRIPT" ]] || { error "Toy data script not found"; exit 1; }
[[ -f "$HIBEAM_SCRIPT" ]] || { error "HIBEAM GNN script not found"; exit 1; }

# --- 9. GPU visibility ---
[[ -n "$GPU_ID" ]] && export CUDA_VISIBLE_DEVICES="$GPU_ID" && log "Set CUDA_VISIBLE_DEVICES=$GPU_ID"

# --- 10. Run toy data generation ---
log "Running toy data generation..."
python "$TOY_SCRIPT" || { error "Toy data generation failed"; exit 1; }

# --- 11. Run HIBEAM GNN ---
log "Running HIBEAM GNN..."
python "$HIBEAM_SCRIPT" || { error "HIBEAM GNN failed"; exit 1; }

log "Pipeline finished successfully!"

