# l0l1 Makefile - Poetry-based development workflow
.PHONY: help install dev test lint format clean demo serve docs

# Default target
help: ## Show this help message
	@echo "l0l1 - AI-Powered SQL Analysis and Validation Library"
	@echo "======================================================"
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation
install: ## Install dependencies
	poetry install

install-all: ## Install all dependencies including optional groups
	poetry install --with dev,jupyter,demo,docs,ide

install-prod: ## Install only production dependencies
	poetry install --only main

# Development
dev: ## Setup development environment
	poetry install --with dev,jupyter,demo
	poetry run pre-commit install

shell: ## Activate Poetry shell
	poetry shell

# Testing
test: ## Run tests
	poetry run pytest

test-cov: ## Run tests with coverage
	poetry run pytest --cov=l0l1 --cov-report=term-missing --cov-report=html

test-fast: ## Run only fast tests
	poetry run pytest -m "not slow"

test-integration: ## Run integration tests
	poetry run pytest -m integration

# Code Quality
lint: ## Run linting
	poetry run flake8 l0l1/
	poetry run ruff l0l1/
	poetry run mypy l0l1/

format: ## Format code
	poetry run black l0l1/ tests/ examples/
	poetry run isort l0l1/ tests/ examples/

format-check: ## Check code formatting
	poetry run black --check l0l1/ tests/ examples/
	poetry run isort --check-only l0l1/ tests/ examples/

# Demo and Development
demo-ecommerce: ## Create e-commerce demo environment
	poetry run python -m l0l1.demo.demo_init ecommerce

demo-saas: ## Create SaaS demo environment
	poetry run python -m l0l1.demo.demo_init saas

demo-clean: ## Clean demo environments
	rm -rf ~/.l0l1/workspaces/demo_*

# Services
serve: ## Start API server
	poetry run uvicorn l0l1.api.main:app --reload --host 0.0.0.0 --port 8000

serve-prod: ## Start API server for production
	poetry run uvicorn l0l1.api.main:app --host 0.0.0.0 --port 8000

workers: ## Start background workers
	poetry run dramatiq l0l1.tasks

# Jupyter
jupyter: ## Start Jupyter Lab
	poetry run jupyter lab

jupyter-notebook: ## Start Jupyter Notebook
	poetry run jupyter notebook

# Documentation
docs: ## Build documentation
	poetry run mkdocs build

docs-serve: ## Serve documentation locally
	poetry run mkdocs serve

docs-deploy: ## Deploy documentation
	poetry run mkdocs gh-deploy

# Build and Release
build: ## Build package
	poetry build

publish: ## Publish to PyPI (requires authentication)
	poetry publish

publish-test: ## Publish to Test PyPI
	poetry publish --repository testpypi

# Database and Migration
db-upgrade: ## Run database migrations
	poetry run alembic upgrade head

db-downgrade: ## Rollback database migrations
	poetry run alembic downgrade -1

db-migration: ## Create new database migration
	@read -p "Migration name: " name; \
	poetry run alembic revision --autogenerate -m "$$name"

# Utilities
clean: ## Clean up cache and temporary files
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	poetry cache clear pypi --all

update: ## Update dependencies
	poetry update

security: ## Run security checks
	poetry run pip-audit
	poetry export -f requirements.txt | poetry run safety check --stdin

pre-commit: ## Run pre-commit hooks on all files
	poetry run pre-commit run --all-files

# Quick development workflow
check: format-check lint test-fast ## Run quick checks (format, lint, fast tests)

ci: format-check lint test ## Run CI checks (format, lint, all tests)

# Environment info
info: ## Show environment information
	@echo "=== System Information ==="
	@python --version
	@poetry --version
	@echo ""
	@echo "=== Poetry Configuration ==="
	@poetry config --list
	@echo ""
	@echo "=== Virtual Environment ==="
	@poetry env info
	@echo ""
	@echo "=== Installed Packages ==="
	@poetry show --tree

# CLI shortcuts
validate: ## Validate SQL (usage: make validate SQL="SELECT * FROM table")
	poetry run l0l1 validate "$(SQL)"

explain: ## Explain SQL (usage: make explain SQL="SELECT * FROM table")
	poetry run l0l1 explain "$(SQL)"

complete: ## Complete SQL (usage: make complete SQL="SELECT * FROM")
	poetry run l0l1 complete "$(SQL)"

# Development server with auto-reload
dev-server: ## Start development server with auto-reload and demo data
	@echo "Starting l0l1 development server..."
	@echo "Creating demo environment..."
	@make demo-ecommerce > /dev/null 2>&1 || true
	@echo "Starting API server at http://localhost:8000"
	@poetry run uvicorn l0l1.api.main:app --reload --host 0.0.0.0 --port 8000

# Full setup for new developers
setup: ## Complete setup for new developers
	@echo "Setting up l0l1 development environment..."
	poetry install --with dev,jupyter,demo,docs
	poetry run pre-commit install
	@make demo-ecommerce
	@echo ""
	@echo "✅ Setup complete! Try these commands:"
	@echo "  make serve        # Start API server"
	@echo "  make jupyter      # Start Jupyter Lab"
	@echo "  make test         # Run tests"
	@echo "  make help         # Show all commands"