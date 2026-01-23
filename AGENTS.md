# AGENTS.md: AI Agent Instructions

This document provides instructions for AI agents working on the **AI-Based Stock Investment System (ASX Version)**. All agents MUST follow these guidelines to ensure consistency, safety, and code quality.

## 1. Project Overview

The goal is to build a Python-based trading strategy system for the Australian Securities Exchange (ASX). The system uses AI models trained on historical Yahoo Finance data (`yfinance`) to backtest and generate recommendations.

### Core Modules
- `config.py`: Configuration management (tickers, capital, thresholds).
- `buildmodel.py`: AI model training and persistence.
- `backtest.py`: Backtesting engine with performance logging.
- `ui.py`: Streamlit dashboard for configuration and results.
- `shareinvestment_AImodel.py`: Main application entry point.

## 2. Core Mandates

1. **Documentation-First Development**: Always update `asx_ai_trading_system_requirements.md` or relevant documentation before implementing major changes.
2. **Security Priorities**: Never commit API keys or sensitive financial data. Use environment variables for any secrets.
3. **Data Integrity**: Strictly follow the `.AX` ticker suffix convention for all ASX stocks (e.g., `BHP.AX`).
4. **Logic Constraints**: 
   - Enforce strict stop-loss rules.
   - Handle price gaps (selling at actual market price when stop-loss is triggered).
   - Use `yfinance` exclusively for historical data.

## 3. Development Environment

This project uses Python 3.x. 

### Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Key Libraries
- **Data**: `yfinance`, `pandas`, `numpy`
- **AI/ML**: `scikit-learn`, `tensorflow` or `pytorch`
- **UI**: `streamlit` (required)
- **Quality**: `ruff`, `black`, `mypy`, `pytest`

## 4. Build, Lint, and Test Commands

### 4.1. Formatting and Linting
We use `black` for formatting and `ruff` for linting.
```bash
# Format code
black .

# Run linter
ruff check .

# Fix linting errors automatically
ruff check . --fix
```

### 4.2. Type Checking
```bash
# Run static type analysis
mypy .
```

### 4.3. Testing
We use `pytest` for all tests.
```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_backtest.py

# Run a specific test function
pytest tests/test_backtest.py::test_stop_loss_execution

# Run tests with coverage
pytest --cov=.
```

## 5. Code Style Guidelines

### 5.1. Imports
- Use `isort`-style ordering (enforced by `ruff`).
- Grouping: Standard library, Third-party, Local modules.
```python
import os
from datetime import datetime

import pandas as pd
import yfinance as yf

from config import AppConfig
```

### 5.2. Formatting
- Max line length: **88 characters** (Black default).
- Indentation: 4 spaces.

### 5.3. Typing
- **Mandatory** type hints for all function signatures and public variables.
- Use `typing` module for complex types (e.g., `List`, `Dict`, `Optional`).

### 5.4. Naming Conventions
- **Modules/Files**: `snake_case.py` (e.g., `build_model.py`)
- **Functions/Variables**: `snake_case` (e.g., `calculate_roi`)
- **Classes**: `PascalCase` (e.g., `BacktestEngine`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_STOP_LOSS`)

### 5.5. Error Handling
- Use `try...except` blocks with **specific** exceptions.
- Log errors using the `logging` module; do not use `print()` for errors.
```python
import logging

try:
    data = yf.download(ticker)
except Exception as e:
    logging.error(f"Failed to fetch data for {ticker}: {e}")
    raise
```

### 5.6. Docstrings
- Use **Google-style** docstrings for all modules, classes, and functions.
```python
def calculate_roi(initial: float, final: float) -> float:
    """Calculates the Return on Investment.

    Args:
        initial: Starting capital.
        final: Ending capital.

    Returns:
        ROI as a decimal percentage.
    """
    return (final - initial) / initial
```

## 6. Git Workflow

- **Branching**: `feat/`, `fix/`, `docs/` prefixes for branches.
- **Commits**: Concise, present-tense messages (e.g., "Add stop-loss logic to backtester").
- **PRs**: Ensure all linting and tests pass before requesting a review.

---
*Last Updated: 2026-01-23*
*Note: This is a living document. Update it as project conventions evolve.*
