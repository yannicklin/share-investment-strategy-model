#!/bin/bash

# ASX AI Trading System - Robust Setup Script
# This script ensures the correct environment is created for your architecture (Intel/ARM).

set -e

echo "🔍 Detecting hardware..."
# Detect physical hardware (handles macOS Rosetta and Linux)
OS=$(uname -s)
ARCH=$(uname -m)

if [ "$OS" == "Darwin" ]; then
    # macOS-specific detection
    IS_APPLE_SILICON=$(sysctl -n machdep.cpu.brand_string 2>/dev/null | grep -q "Apple" && echo "true" || echo "false")
else
    # Linux/Codespace - no Apple Silicon
    IS_APPLE_SILICON="false"
fi

echo "💻 OS: $OS, Shell Arch: $ARCH, Apple Silicon: $IS_APPLE_SILICON"

# 1. Clean up existing environment if it's incorrect
if [ -d ".venv" ]; then
    echo "♻️ Existing .venv found. Checking compatibility..."
    VENV_ARCH=$(.venv/bin/python3 -c "import platform; print(platform.machine())" 2>/dev/null || echo "unknown")
    
    if [ "$IS_APPLE_SILICON" == "true" ] && [ "$VENV_ARCH" == "x86_64" ]; then
        echo "⚠️  CRITICAL: You are on Apple Silicon but your .venv is Intel (x86_64)."
        echo "🗑️  Removing incompatible .venv to fix AVX/TensorFlow crashes..."
        rm -rf .venv
    fi
fi

# 2. Create the environment
if [ ! -d ".venv" ]; then
    echo "🛠️  Creating new virtual environment..."
    
    # Prefer Python 3.10+ if available
    if command -v python3.12 >/dev/null 2>&1; then
        PYTHON_EXEC=$(command -v python3.12)
    elif command -v python3.11 >/dev/null 2>&1; then
        PYTHON_EXEC=$(command -v python3.11)
    elif command -v python3.10 >/dev/null 2>&1; then
        PYTHON_EXEC=$(command -v python3.10)
    else
        PYTHON_EXEC="/usr/bin/python3"
    fi
    
    echo "🐍 Using Python: $PYTHON_EXEC"

    if [ "$IS_APPLE_SILICON" == "true" ]; then
        echo "🍎 SUPER FORCE: Creating native arm64 environment..."
        # Create it using the selected python
        $PYTHON_EXEC -m venv .venv
        
        # Verify using the arm64 slice explicitly
        VENV_TYPE=$(/usr/bin/arch -arm64 .venv/bin/python3 -c "import platform; print(platform.machine())" 2>/dev/null || echo "unknown")
        echo "🧪 Verification (forced arm64): $VENV_TYPE"
        
        if [ "$VENV_TYPE" != "arm64" ] && [ "$VENV_TYPE" != "arm64e" ]; then
            echo "❌ ERROR: Could not verify arm64 support in venv."
            exit 1
        fi
    else
        $PYTHON_EXEC -m venv .venv
    fi
fi

# 3. Activate and Install
echo "📦 Installing/Updating dependencies..."
PYTHON_VENV=".venv/bin/python3"

# Define INSTALL_CMD before usage
if [ "$IS_APPLE_SILICON" == "true" ]; then
    INSTALL_CMD="/usr/bin/arch -arm64 $PYTHON_VENV"
else
    INSTALL_CMD="$PYTHON_VENV"
fi

# Detect if UV is available (Codespace/Linux) or use pip (macOS)
if command -v uv >/dev/null 2>&1; then
    echo "🚀 Using UV for fast dependency installation..."
    # UV sync reads from pyproject.toml and handles everything
    uv sync --no-dev || {
        echo "⚠️  UV sync failed, trying with dev dependencies..."
        uv sync
    }
else
    # Use pip directly from the venv (reads from pyproject.toml)
    echo "🐍 Using venv pip for reliable installation..."
    $INSTALL_CMD -m pip install --upgrade pip
    # Non-editable install (avoids -e issues in some environments)
    $INSTALL_CMD -m pip install .
fi

echo "✅ Setup complete!"
FINAL_ARCH=$($INSTALL_CMD -c "import platform; print(platform.machine())")
echo "🎯 Final Python Architecture: $FINAL_ARCH"
