.PHONY: setup run test lint clean scan

# Default: setup and run
all: setup run

setup:
	@bash setup.sh

# Architecture Detection for macOS
IS_APPLE_SILICON := $(shell sysctl -n machdep.cpu.brand_string 2>/dev/null | grep -q "Apple" && echo "true" || echo "false")

# Environment Detection (UV in Codespaces vs traditional venv)
HAS_UV := $(shell command -v uv >/dev/null 2>&1 && echo "true" || echo "false")

# Auto-detect entry point file (USA_AImodel.py, TWN_AImodel.py, ASX_AImodel.py)
ENTRY_POINT := $(shell ls *_AImodel.py 2>/dev/null | head -n 1)

run:
ifeq ($(HAS_UV),true)
	@lsof -ti:8502 | xargs kill -9 2>/dev/null || true
	@uv run streamlit run $(ENTRY_POINT)
else ifeq ($(IS_APPLE_SILICON),true)
	@lsof -ti:8502 | xargs kill -9 2>/dev/null || true
	@arch -arm64 .venv/bin/python3 -m streamlit run $(ENTRY_POINT)
else
	@lsof -ti:8502 | xargs kill -9 2>/dev/null || true
	@.venv/bin/python3 -m streamlit run $(ENTRY_POINT)
endif

test:
ifeq ($(HAS_UV),true)
	@uv run pytest tests/
else ifeq ($(IS_APPLE_SILICON),true)
	@arch -arm64 .venv/bin/python3 -m pytest tests/
else
	@.venv/bin/python3 -m pytest tests/
endif

lint:
ifeq ($(HAS_UV),true)
	@uv run ruff check .
else ifeq ($(IS_APPLE_SILICON),true)
	@arch -arm64 .venv/bin/ruff check .
else
	@.venv/bin/ruff check .
endif

scan:
	@echo "Running Trivy filesystem scan..."
	@trivy fs .
	@echo "\nRunning Semgrep security scan..."
	@semgrep scan .

clean:
	rm -rf .venv
	rm -rf catboost_info
	rm -rf data/models/*.joblib
	rm -rf data/models/*.h5
	rm -rf data/models/*.keras
	rm -rf data/models/*.json
	rm -rf data/ledgers/*.*
	find . -type d -name "__pycache__" -exec rm -rf {} +
