#!/bin/bash

# ASX Bot Trading System - Setup Script (asx-bot branch)
# Prepares environment for Flask automation (no Streamlit, no M1 Mac-specific handling)

set -e

echo "🤖 ASX Bot Trading System - Environment Setup"
echo "=============================================="

echo "🤖 ASX Bot Trading System - Environment Setup"
echo "=============================================="

# 1. Check Python version
echo "🐍 Checking Python version..."
PYTHON_EXEC=$(command -v python3 || echo "")
if [ -z "$PYTHON_EXEC" ]; then
    echo "❌ Python 3 not found. Please install Python 3.10+."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_EXEC --version | awk '{print $2}')
echo "✅ Using Python $PYTHON_VERSION"

# 2. Create virtual environment
if [ -d ".venv" ]; then
    echo "♻️  Existing .venv found. Skipping creation."
else
    echo "🛠️  Creating new virtual environment..."
    $PYTHON_EXEC -m venv .venv
    echo "✅ Virtual environment created"
fi

# 3. Activate and install dependencies
echo "📦 Installing dependencies from requirements.txt..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"

# 4. Setup environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit .env file with your actual secrets:"
    echo "   - DATABASE_URL (PostgreSQL connection string)"
    echo "   - CRON_TOKEN (secure random string)"
    echo "   - BACKUP_ENCRYPTION_KEY (32-byte base64 key)"
    echo "   - Notification API keys (SendGrid, Telnyx, Telegram)"
else
    echo "✅ .env file already exists"
fi

# 5. Verify core imports
echo "🧪 Verifying core imports..."
python -c "import flask, sqlalchemy, yfinance, sklearn, catboost, prophet, tensorflow" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ All core modules imported successfully"
else
    echo "❌ Import verification failed. Check requirements installation."
    exit 1
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your actual secrets"
echo "  2. Start PostgreSQL database (local or Supabase)"
echo "  3. Run: make db-init (initialize database schema)"
echo "  4. Run: make test (verify tests pass)"
echo "  5. Run: make run (start Flask app locally)"
echo ""
    fi
fi

# 3. Activate and Install
echo "📦 Installing/Updating dependencies..."
PYTHON_VENV=".venv/bin/python3"

# Force arm64 for installation if on Apple Silicon to ensure correct wheels
if [ "$IS_APPLE_SILICON" == "true" ]; then
    INSTALL_CMD="/usr/bin/arch -arm64 $PYTHON_VENV"
else
    INSTALL_CMD="$PYTHON_VENV"
fi

# Use pip directly from the venv to avoid architecture mismatches with global tools like uv
echo "🐍 Using venv pip for reliable installation..."
$INSTALL_CMD -m pip install --upgrade pip
$INSTALL_CMD -m pip install -e "."

echo "✅ Setup complete!"
FINAL_ARCH=$($INSTALL_CMD -c "import platform; print(platform.machine())")
echo "🎯 Final Python Architecture: $FINAL_ARCH"
