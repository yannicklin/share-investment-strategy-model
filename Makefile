.PHONY: setup run test lint clean scan

# Default: setup and run
all: setup run

setup:
	@bash setup.sh

# Architecture Detection for macOS
IS_APPLE_SILICON := $(shell sysctl -n machdep.cpu.brand_string 2>/dev/null | grep -q "Apple" && echo "true" || echo "false")

run:
ifeq ($(IS_APPLE_SILICON),true)
	@lsof -ti:8502 | xargs kill -9 2>/dev/null || true
	@arch -arm64 .venv/bin/python3 -m streamlit run ASX_AImodel.py
else
	@lsof -ti:8502 | xargs kill -9 2>/dev/null || true
	@.venv/bin/python3 -m streamlit run ASX_AImodel.py
endif

test:
ifeq ($(IS_APPLE_SILICON),true)
	@arch -arm64 .venv/bin/python3 -m pytest tests/
else
	@.venv/bin/python3 -m pytest tests/
endif

lint:
ifeq ($(IS_APPLE_SILICON),true)
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
	find . -type d -name "__pycache__" -exec rm -rf {} +
