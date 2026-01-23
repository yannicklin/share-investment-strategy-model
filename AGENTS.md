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

1. **Documentation-First Development**: Always update `asx_ai_trading_system_requirements.md` or relevant documentation before implementing major architectural changes.
2. **Security Priorities**: NEVER commit API keys or sensitive financial data. Use environment variables or local `.env` files (ensure they are in `.gitignore`).
3. **Data Integrity**: Strictly follow the `.AX` ticker suffix convention for all ASX stocks (e.g., `BHP.AX`, `CBA.AX`).
4. **Logic Constraints**: 
   - Enforce strict stop-loss rules.
   - Handle price gaps (selling at actual market price when stop-loss is triggered).
   - Use `yfinance` exclusively for historical data.

## 3. Development Environment

This project uses Python 3.12+ and `uv` for package management.

### Setup
```bash
# Create virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### Key Libraries
- **Data**: `yfinance`, `pandas`, `numpy`
- **AI/ML**: `scikit-learn`, `xgboost`, `tensorflow` or `pytorch`
- **UI**: `streamlit`, `plotly`
- **Quality**: `ruff`, `black`, `mypy`, `pytest`

## 4. Build, Lint, and Test Commands

### 4.1. Formatting and Linting
We use `black` for formatting and `ruff` for linting and import sorting.
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
- Use `ruff`-style ordering (enforced by `ruff`'s `I` rules).
- Grouping: Standard library, Third-party, Local modules.
- Absolute imports are preferred.

### 5.2. Formatting
- Max line length: **88 characters** (Black default).
- Indentation: 4 spaces.
- Double quotes for strings unless the string contains double quotes.

### 5.3. Typing
- **Mandatory** type hints for all function signatures and public variables.
- Use `typing` module for complex types (e.g., `List`, `Dict`, `Optional`) or pipe syntax for Python 3.10+ (e.g., `int | None`).

### 5.4. Naming Conventions
- **Modules/Files**: `snake_case.py` (e.g., `build_model.py`)
- **Functions/Variables**: `snake_case` (e.g., `calculate_roi`)
- **Classes**: `PascalCase` (e.g., `BacktestEngine`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_STOP_LOSS`)

### 5.5. Error Handling
- Use `try...except` blocks with **specific** exceptions. Avoid `except Exception:`.
- Log errors using the `logging` module; do not use `print()` for errors.
- Ensure resources (files, connections) are closed using `with` statements.

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

## 6. Documentation and Requirements

- **Requirements File**: The `asx_ai_trading_system_requirements.md` is the source of truth for business logic. Refer to it for specific thresholds, module responsibilities, and data source requirements.
- **In-code Documentation**:
    - Use clear variable names that reflect financial or technical concepts (e.g., `adj_close` instead of `ac`).
    - Explain the "why" for complex financial logic or AI model choices.
- **Module-level Docstrings**: Each major module (`config.py`, `backtest.py`, etc.) should have a high-level summary of its purpose at the top of the file.

## 7. Git Workflow

- **Branching**: Use descriptive names like `feat/ai-model`, `fix/stop-loss`, `docs/update-agents`.
- **Commits**: Concise, present-tense messages (e.g., "Add stop-loss logic to backtester").
- **PRs**: Ensure all linting and tests pass before requesting a review.
- **Review**: When creating PRs, summarize the changes and how they align with the requirements.

## 8. Troubleshooting and Support

- **LSP Errors**: If you encounter "Import could not be resolved" errors, verify that the package is in `requirements.txt` and installed in the `.venv`.
- **Data Issues**: `yfinance` can sometimes fail or return empty data. Implement robust error handling and retries where appropriate.
- **Model Convergence**: If the AI model fails to converge or produces poor results, check feature scaling and data preprocessing steps.

---
*Last Updated: 2026-01-23*
*Note: This is a living document. Update it as project conventions evolve.*
