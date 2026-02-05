.PHONY: help setup venv shell install install-dev serve test lint clean clean-venv

help:
	@echo "Sniffly Development Commands"
	@echo ""
	@echo "  make setup        - Complete setup with venv + pyenv (recommended)"
	@echo "  make venv         - Create virtual environment (.venv)"
	@echo "  make shell        - Activate virtual environment in new shell"
	@echo "  make install      - Install package in development mode"
	@echo "  make install-dev  - Install package + dev dependencies"
	@echo "  make serve        - Start the Sniffly dashboard server"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run linter (ruff + mypy)"
	@echo "  make clean        - Remove build artifacts and cache"
	@echo "  make clean-venv   - Remove virtual environment (.venv)"
	@echo ""

venv:
	@echo "Setting up Python environment with pyenv..."
	@if [ ! -d ".venv" ]; then \
		PYTHON_VERSION=$$(cat .python-version) && \
		pyenv local $$PYTHON_VERSION && \
		$$(pyenv which python) -m venv .venv && \
		echo "Virtual environment created in .venv/ with Python $$PYTHON_VERSION"; \
	else \
		echo "Virtual environment already exists in .venv/"; \
	fi
	@echo ""
	@echo "Activate with: source .venv/bin/activate"

setup: venv install-dev
	@echo ""
	@echo "Setup complete! Virtual environment created in .venv/"
	@echo "Activate with: source .venv/bin/activate"
	@echo "Or run: make shell"
	@echo "Then run: make serve"

shell:
	@if [ ! -d ".venv" ]; then \
		echo "Virtual environment not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@VENV_PYTHON=$$(.venv/bin/python --version 2>&1 | cut -d' ' -f2); \
	echo "Activating virtual environment (Python $$VENV_PYTHON)..."; \
	echo "Type 'exit' or press Ctrl+D to leave the virtual environment."; \
	echo ""; \
	VIRTUAL_ENV="$$(pwd)/.venv" \
	PATH="$$(pwd)/.venv/bin:$$PATH" \
	PS1="(.venv) $${PS1}" \
	$${SHELL:-/bin/bash}

install:
	@if [ -d ".venv" ]; then \
		.venv/bin/pip install -e .; \
	else \
		pip install -e .; \
	fi

install-dev: install
	@if [ -d ".venv" ]; then \
		.venv/bin/pip install -r requirements-dev.txt; \
	else \
		pip install -r requirements-dev.txt; \
	fi

serve:
	@if [ -d ".venv" ]; then \
		.venv/bin/sniffly init; \
	else \
		sniffly init; \
	fi

test:
	@if [ -d ".venv" ]; then \
		.venv/bin/python run_tests.py; \
	else \
		python run_tests.py; \
	fi

lint:
	@if [ -d ".venv" ]; then \
		PATH=".venv/bin:$$PATH" ./lint.sh; \
	else \
		./lint.sh; \
	fi

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete

clean-venv:
	@echo "Removing virtual environment..."
	rm -rf .venv
	@echo "Virtual environment removed. Run 'make setup' to recreate."
