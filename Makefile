# l0l1 Makefile - uv-based development workflow
.PHONY: help install dev test lint format clean demo serve docs frontend-install frontend-dev frontend-build frontend-preview dev-all setup-all

# Default target
help: ## Show this help message
	@echo "l0l1 - AI-Powered SQL Analysis and Validation Library"
	@echo "======================================================"
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation
install: ## Install dependencies
	uv sync

install-all: ## Install all dependencies including optional groups
	uv sync --all-extras

install-prod: ## Install only production dependencies
	uv sync --no-dev

# Development
dev: ## Setup development environment
	uv sync --extra dev --extra jupyter --extra demo
	uv run pre-commit install

# Testing
test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=l0l1 --cov-report=term-missing --cov-report=html

test-fast: ## Run only fast tests
	uv run pytest -m "not slow"

test-integration: ## Run integration tests
	uv run pytest -m integration

# Code Quality
lint: ## Run linting
	uv run flake8 l0l1/
	uv run ruff check l0l1/
	uv run mypy l0l1/

format: ## Format code
	uv run black l0l1/ tests/ examples/
	uv run isort l0l1/ tests/ examples/

format-check: ## Check code formatting
	uv run black --check l0l1/ tests/ examples/
	uv run isort --check-only l0l1/ tests/ examples/

# Demo and Development
demo-ecommerce: ## Create e-commerce demo environment
	uv run python -m l0l1.demo.demo_init ecommerce

demo-saas: ## Create SaaS demo environment
	uv run python -m l0l1.demo.demo_init saas

demo-clean: ## Clean demo environments
	rm -rf ~/.l0l1/workspaces/demo_*

# Services
serve: ## Start API server
	uv run uvicorn l0l1.api.main:app --reload --host 0.0.0.0 --port 8000

serve-prod: ## Start API server for production
	uv run uvicorn l0l1.api.main:app --host 0.0.0.0 --port 8000

workers: ## Start background workers
	uv run dramatiq l0l1.tasks

# Jupyter
jupyter: ## Start Jupyter Lab
	uv run jupyter lab

jupyter-notebook: ## Start Jupyter Notebook
	uv run jupyter notebook

# Documentation
docs: ## Build documentation
	uv run mkdocs build

docs-serve: ## Serve documentation locally
	uv run mkdocs serve

docs-deploy: ## Deploy documentation
	uv run mkdocs gh-deploy

# Build and Release
build: ## Build package
	uv build

publish: ## Publish to PyPI (requires authentication)
	uv publish

publish-test: ## Publish to Test PyPI
	uv publish --index testpypi

# Database and Migration
db-upgrade: ## Run database migrations
	uv run alembic upgrade head

db-downgrade: ## Rollback database migrations
	uv run alembic downgrade -1

db-migration: ## Create new database migration
	@read -p "Migration name: " name; \
	uv run alembic revision --autogenerate -m "$$name"

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
	uv cache clean

update: ## Update dependencies
	uv lock --upgrade

security: ## Run security checks
	uv run pip-audit

pre-commit: ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files

# Quick development workflow
check: format-check lint test-fast ## Run quick checks (format, lint, fast tests)

ci: format-check lint test ## Run CI checks (format, lint, all tests)

# Environment info
info: ## Show environment information
	@echo "=== System Information ==="
	@python --version
	@uv --version
	@echo ""
	@echo "=== Virtual Environment ==="
	@uv venv --help > /dev/null 2>&1 && echo "uv is configured correctly"
	@echo ""
	@echo "=== Installed Packages ==="
	@uv pip list

# CLI shortcuts
validate: ## Validate SQL (usage: make validate SQL="SELECT * FROM table")
	uv run l0l1 validate "$(SQL)"

explain: ## Explain SQL (usage: make explain SQL="SELECT * FROM table")
	uv run l0l1 explain "$(SQL)"

complete: ## Complete SQL (usage: make complete SQL="SELECT * FROM")
	uv run l0l1 complete "$(SQL)"

# Development server with auto-reload
dev-server: ## Start development server with auto-reload and demo data
	@echo "Starting l0l1 development server..."
	@echo "Creating demo environment..."
	@make demo-ecommerce > /dev/null 2>&1 || true
	@echo "Starting API server at http://localhost:8000"
	@uv run uvicorn l0l1.api.main:app --reload --host 0.0.0.0 --port 8000

# Full setup for new developers
setup: ## Complete setup for new developers
	@echo "Setting up l0l1 development environment..."
	uv sync --extra dev --extra jupyter --extra demo --extra docs
	uv run pre-commit install
	@make demo-ecommerce
	@echo ""
	@echo "Setup complete! Try these commands:"
	@echo "  make serve        # Start API server"
	@echo "  make jupyter      # Start Jupyter Lab"
	@echo "  make test         # Run tests"
	@echo "  make help         # Show all commands"

# Frontend development
frontend-install: ## Install frontend dependencies
	cd frontend && npm install

frontend-dev: ## Start frontend development server
	cd frontend && npm run dev

frontend-build: ## Build frontend for production
	cd frontend && npm run build

frontend-preview: ## Preview frontend production build
	cd frontend && npm run preview

# Full stack development
dev-all: ## Start both API and frontend servers
	@echo "Starting l0l1 full stack development..."
	@echo "API server: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@make serve & make frontend-dev

# Complete setup including frontend
setup-all: setup frontend-install ## Complete setup including frontend
	@echo ""
	@echo "Full stack setup complete! Try these commands:"
	@echo "  make dev-all      # Start API + Frontend"
	@echo "  make serve        # Start API server only"
	@echo "  make frontend-dev # Start frontend only"
