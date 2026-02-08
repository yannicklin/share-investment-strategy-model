#!/bin/bash

# AI Trading System (USA) - Setup Script
# Handles Python environment creation, Apple Silicon compatibility, and dependency installation.

set -e

# Detect Architecture
ARCH=$(uname -m)
OS=$(uname -s)
IS_APPLE_SILICON="false"

if [[ "$OS" == "Darwin" && "$ARCH" == "arm64" ]]; then
    IS_APPLE_SILICON="true"
fi

echo "🔍 Detected System: $OS ($ARCH)"
if [ "$IS_APPLE_SILICON" == "true" ]; then
    echo "🍎 Apple Silicon Mode Active"
fi

# Python Version Selection
PYTHON_EXEC="python3"
if command -v python3.12 >/dev/null 2>&1; then PYTHON_EXEC="python3.12";
elif command -v python3.11 >/dev/null 2>&1; then PYTHON_EXEC="python3.11";
elif command -v python3.10 >/dev/null 2>&1; then PYTHON_EXEC="python3.10";
fi

echo "🐍 Using Python: $PYTHON_EXEC"

# Create Virtual Environment if missing
if [ ! -d ".venv" ]; then
    echo "🛠️  Creating virtual environment (.venv)..."
    $PYTHON_EXEC -m venv .venv
fi

# Install Dependencies
echo "📦 Installing dependencies..."
source .venv/bin/activate

# Use uv if available for speed, otherwise pip
if command -v uv >/dev/null 2>&1; then
    echo "🚀 Using uv for fast installation..."
    uv pip install -r requirements.txt
else
    echo "🐢 Using pip..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

echo "✅ Setup Complete! Run 'make run' to start."
