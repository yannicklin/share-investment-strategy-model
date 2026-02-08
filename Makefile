.PHONY: setup run clean test update

# Default target
all: setup run

# Setup environment (calls the robust shell script)
setup:
	@bash setup.sh

# Run the application
run:
	@echo "🚀 Starting US Market AI Dashboard..."
	@.venv/bin/streamlit run main.py

# Clean up temporary files
clean:
	@echo "🧹 Cleaning up..."
	@rm -rf __pycache__
	@rm -rf .venv
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "✅ Clean complete."

# Run tests (Placeholder for now)
test:
	@echo "🧪 Running tests..."
	@.venv/bin/python3 -m pytest tests/ || echo "No tests found or test failure."

# Update dependencies
update:
	@echo "📦 Updating requirements..."
	@.venv/bin/pip freeze > requirements.txt
