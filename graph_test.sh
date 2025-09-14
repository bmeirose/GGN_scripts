module load Anaconda3/2024.02-1
source $(conda info --base)/etc/profile.d/conda.sh
conda activate hibeam_env

# Install pytorch_lightning
conda install -c conda-forge pytorch-lightning -y

# Test if it works
python -c "import pytorch_lightning; print('PyTorch Lightning installed successfully!')"
python -c "from graphnet.data import GraphNeTDataModule; print('GraphNet data module imported successfully!')"
