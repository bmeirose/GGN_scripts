#!/usr/bin/env bash
# cleanup_conda_project.sh - safely remove heavy conda environments inside project

module load Anaconda3/2024.02-1

echo "[INFO] Starting cleanup of project conda environments..."

PROJECT_ENVS_DIR="$PWD/conda_envs"
mkdir -p "$PROJECT_ENVS_DIR"

# List environments in project
echo "[INFO] Project conda environments:"
ls -d "$PROJECT_ENVS_DIR"/* 2>/dev/null || echo "None found"

# Remove environments
for env_path in "$PROJECT_ENVS_DIR"/*; do
    if [ -d "$env_path" ]; then
        echo "[INFO] Removing environment: $env_path"
        rm -rf "$env_path"
    fi
done

# Optional: clean conda caches (shared, but safe)
echo "[INFO] Cleaning conda caches..."
conda clean -a -y

# Optional: remove temporary caches (adjust if needed)
echo "[INFO] Cleaning user cache directories..."
rm -rf ~/.cache/*
rm -rf ~/tmp/* 2>/dev/null || true

echo "[INFO] Cleanup finished. Check your disk quota:"
quota -v

