.PHONY: setup install db-init run test lint clean help

# Default: show help
all: help

help:
	@echo "ASX Bot Trading System - Makefile Commands"
	@echo "==========================================="
	@echo ""
	@echo "Setup:"
	@echo "  make setup      - Run setup.sh (create venv, install deps)"
	@echo "  make install    - Install/upgrade dependencies only"
	@echo "  make db-init    - Initialize database schema"
	@echo ""
	@echo "Development:"
	@echo "  make run        - Start Flask app locally (port 5000)"
	@echo "  make test       - Run pytest test suite"
	@echo "  make lint       - Run code quality checks"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean      - Remove venv and artifacts"
	@echo ""

setup:
	@bash setup.sh

install:
	@echo "📦 Installing dependencies..."
	@.venv/bin/pip install --upgrade pip
	@.venv/bin/pip install -r requirements.txt
	@echo "✅ Dependencies updated"

db-init:
	@echo "🗄️  Initializing database schema..."
	@.venv/bin/python -c "from app.bot import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('✅ Database tables created')"

run:
	@echo "🚀 Starting Flask bot application..."
	@.venv/bin/python run_bot.py

test:
	@echo "🧪 Running test suite..."
	@.venv/bin/pytest tests/bot/ -v --tb=short

lint:
	@echo "🔍 Running code quality checks..."
	@.venv/bin/python -m ruff check . || echo "⚠️  Ruff not installed (optional)"

clean:
	@echo "🧹 Cleaning up..."
	rm -rf .venv
	rm -rf catboost_info
	rm -rf models/*.pkl models/*.h5 models/*.joblib
	rm -rf __pycache__ app/__pycache__ app/bot/__pycache__
	rm -rf .pytest_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"
