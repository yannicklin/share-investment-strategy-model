#!/bin/bash

# setup_multimarket_server.sh
# Sets up the multi-branch environment for Oracle Cloud deployment.

set -e

echo "🚀 Starting Multi-Market Server Setup..."

# 1. Verify Git Installation
if ! command -v git &> /dev/null; then
    echo "❌ Git could not be found. Please install git."
    exit 1
fi

# 2. Verify Docker Installation
if ! command -v docker &> /dev/null; then
    echo "❌ Docker could not be found. Please install docker."
    exit 1
fi

# 2.5 Verify .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "⚠️  .env file not found. Creating from .env.example..."
        cp .env.example .env
        echo "✅ Created .env. Please edit it with your OCI credentials before running docker-compose up."
    else
        echo "❌ .env file missing! Please create one with your OCI secrets."
        exit 1
    fi
fi

# 2.6 Configure Swap for Low-Memory Instance (6GB RAM)
# Essential for preventing OOM kills during ML model training
SWAP_FILE="/swapfile"
if [ -f "$SWAP_FILE" ]; then
    echo "✅ Swap file already exists."
else
    echo "⚠️  No swap file found. Creating 4GB swap for stability (requires sudo)..."
    # Use dd instead of fallocate for better compatibility
    sudo dd if=/dev/zero of=$SWAP_FILE bs=1M count=4096 status=progress
    sudo chmod 600 $SWAP_FILE
    sudo mkswap $SWAP_FILE
    sudo swapon $SWAP_FILE
    # Add to fstab for persistence across reboots
    echo "$SWAP_FILE none swap sw 0 0" | sudo tee -a /etc/fstab
    echo "✅ Swap created successfully."
fi

# 3. Create Worktrees for Each Branch
echo "📂 Setting up branch worktrees..."

create_worktree() {
    local branch=$1
    local dir=$2
    
    if [ -d "$dir" ]; then
        echo "   ✅ Directory '$dir' already exists."
    else
        echo "   Creating worktree for branch '$branch' in '$dir'..."
        # Fetch latest changes first
        git fetch origin $branch:$branch || git fetch origin $branch
        git worktree add ./$dir $branch
    fi
}

create_worktree "asx" "asx"
create_worktree "usa" "usa"
create_worktree "twn" "twn"

# 4. Ensure Directories for Persistence exist (optional, Docker creates them, but good for permissions)
echo "📁 Ensuring persistence directories..."
mkdir -p asx/models asx/logs asx/data
mkdir -p usa/models usa/logs usa/data
mkdir -p twn/models twn/logs twn/data

# 5. Launch Docker Compose
echo "🐳 Launching Docker containers..."
docker compose up -d --build

echo "✅ Deployment Complete!"
echo "   - ASX Lab:        asx.twoudia.top"
echo "   - USA Lab:        usa.twoudia.top"
echo "   - Taiwan Lab:     twn.twoudia.top"
