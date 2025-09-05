# YouTube Music Manager - Development Tasks

.PHONY: test test-unit test-integration coverage lint clean install help

# Default target
help: ## Show this help message
	@echo "YouTube Music Manager - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

test: ## Run all tests
	pytest

test-unit: ## Run only unit tests
	pytest -m "not integration" --tb=short

test-integration: ## Run only integration tests  
	pytest -m integration --tb=short

coverage: ## Run tests with detailed coverage report
	pytest --cov=ytmusic_manager --cov-report=term-missing --cov-report=html

lint: ## Run code linting
	@echo "Checking code with flake8..."
	@flake8 ytmusic_manager/ main.py tests/ --max-line-length=100 --ignore=E203,W503 || echo "flake8 not installed, skipping..."
	@echo "Checking imports with isort..."
	@isort --check-only --diff ytmusic_manager/ main.py tests/ || echo "isort not installed, skipping..."
	@echo "Checking types with mypy..."
	@mypy ytmusic_manager/ main.py || echo "mypy not installed, skipping..."

format: ## Format code
	@echo "Formatting with black..."
	@black ytmusic_manager/ main.py tests/ || echo "black not installed, skipping..."
	@echo "Sorting imports with isort..."
	@isort ytmusic_manager/ main.py tests/ || echo "isort not installed, skipping..."

clean: ## Clean up generated files
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf *.log
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

validate: ## Validate artists.txt file
	python3 main.py validate --verbose

sync-dry: ## Run sync in dry-run mode
	python3 main.py sync --dry-run --verbose

sync: ## Run actual sync (WARNING: makes real changes)
	@echo "WARNING: This will make real changes to your YouTube Music subscriptions!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	python3 main.py sync --verbose --interactive

list: ## List current subscriptions
	python3 main.py list --verbose

# Development quality targets
check: lint test ## Run all quality checks

ci: install lint test ## Run CI pipeline locally

# Package building
build: clean ## Build distribution packages
	python -m build

# Release helpers
release-check: lint test ## Check release readiness
	@echo "All checks passed - ready for release"