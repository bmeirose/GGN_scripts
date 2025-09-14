#!/usr/bin/env bash
# run_pipeline_safe.sh - Stable pipeline runner for HIBEAM GNN
# To debug: bash -x ./run_pipeline.sh 2>&1 | tee debug.log

TOY_SCRIPT="toy_data_generation.py"
HIBEAM_SCRIPT="HIBEAM_GNN_v1.py"
GPU_ID="${GPU_ID:-}"     # optional, set externally
ENV_NAME="hibeam_env"

log() { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
error() { printf "\033[1;31m[ERROR]\033[0m %s\n" "$*" >&2; }

# --- 1. Load Anaconda module and setup ---
log "Loading Anaconda module..."
module load Anaconda3/2024.02-1
source "$(conda info --base)/etc/profile.d/conda.sh"

# --- 2. Create environment if missing ---
if ! conda env list | grep -qE "^${ENV_NAME}\s"; then
    log "Creating conda environment: $ENV_NAME"
    conda create -n "$ENV_NAME" python=3.9 -y
fi

# --- 3. Activate environment ---
log "Activating environment: $ENV_NAME"
conda deactivate 2>/dev/null || true
conda activate "$ENV_NAME"

# --- 4. Install/update core packages ---
log "Installing/updating core packages..."
conda install -y -c conda-forge pyarrow pandas matplotlib pytorch-lightning
# PyTorch + Torchvision (CPU by default, GPU if available)
conda install -y -c pytorch pytorch torchvision torchaudio
# IPython and extras (pexpect, prompt_toolkit, etc.)
pip install --user "ipython[all]"

# --- 5. Install PyTorch Geometric safely ---
log "Installing PyTorch Geometric..."
pip install torch-geometric -f https://data.pyg.org/whl/torch-$(python -c "import torch; print(torch.__version__.split('+')[0])").html

# --- 6. Install GraphNeT ---
log "Installing GraphNeT..."
pip install --user git+https://github.com/graphnet-team/graphnet.git

# --- 7. Check required scripts ---
if [[ ! -f "$TOY_SCRIPT" ]]; then
    error "Toy data generation script not found: $TOY_SCRIPT"
    exit 1
fi
if [[ ! -f "$HIBEAM_SCRIPT" ]]; then
    error "HIBEAM GNN script not found: $HIBEAM_SCRIPT"
    exit 1
fi

# --- 8. GPU setup (optional) ---
if [[ -n "$GPU_ID" ]]; then
    export CUDA_VISIBLE_DEVICES="$GPU_ID"
    log "Set CUDA_VISIBLE_DEVICES=$GPU_ID"
fi

# --- 9. Run toy data generation ---
log "Running toy data generation..."
if python "$TOY_SCRIPT"; then
    log "Toy data generation completed successfully"
else
    error "Toy data generation failed with exit code $?"
    exit 1
fi

# --- 10. Run HIBEAM GNN ---
log "Running HIBEAM GNN..."
if python "$HIBEAM_SCRIPT"; then
    log "HIBEAM GNN completed successfully"
else
    error "HIBEAM GNN failed with exit code $?"
    exit 1
fi

log "Pipeline finished successfully!"

