#!/bin/bash

# ====== USER CONFIGURATION ======
GITHUB_USERNAME="bmeirose"
REPO_NAME="$(basename "$(pwd)")" 
BRANCH="main"
PROJECT_DIR="$(pwd)"
REMOTE_URL="git@github.com:$GITHUB_USERNAME/$REPO_NAME.git"  # Use SSH
MAX_SIZE=10485760  # 10 MB in bytes #
# =================================

cd "$PROJECT_DIR" || exit 1

# Initialize repo if not already done
if [ ! -d ".git" ]; then
    echo "Initializing local Git repository..."
    git init -b $BRANCH
    git remote add origin "$REMOTE_URL"
    git add .
    git commit -m "Initial commit"
    git push -u origin $BRANCH
fi

# Find only files under size limit
FILES_TO_ADD=$(find . -type f -size -${MAX_SIZE}c)

if [ -z "$FILES_TO_ADD" ]; then
    echo "No files below size limit ($MAX_SIZE bytes) to add."
else
    # Stage them
    echo "$FILES_TO_ADD" | xargs git add
fi

# Commit with timestamp
commit_message="Auto-backup on $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$commit_message" || echo "No new changes to commit."

# Push
git push origin $BRANCH

echo "Backup completed successfully at $(date '+%Y-%m-%d %H:%M:%S')"

