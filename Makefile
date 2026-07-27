# ============================================================================
# Makefile — Canadian MURB Geometry Analysis
# ============================================================================
.DEFAULT_GOAL := help

.PHONY: help install dev lint format typecheck test test-cov clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in production mode
	uv pip install -e .

dev: ## Install in development mode with all extras
	uv pip install -e ".[dev]"
	pre-commit install

lint: ## Run linting checks
	ruff check src/ tests/
	ruff format --check src/ tests/

format: ## Auto-format code
	ruff format src/ tests/
	ruff check --fix src/ tests/

typecheck: ## Run static type checking
	mypy src/

test: ## Run tests
	pytest tests/

test-cov: ## Run tests with coverage
	pytest tests/ --cov --cov-report=term-missing --cov-report=html

clean: ## Remove generated artifacts
	rm -rf dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
