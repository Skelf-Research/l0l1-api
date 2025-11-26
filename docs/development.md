# Development Guide

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Git

### Installing uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Homebrew
brew install uv

# pip
pip install uv
```

## Setup

```bash
# Clone repository
git clone https://github.com/dipankar/l0l1-api.git
cd l0l1-api

# Install all dependencies
uv sync --extra dev --extra jupyter --extra demo --extra docs

# Install pre-commit hooks
uv run pre-commit install

# Create demo environment
uv run l0l1-demo ecommerce
```

Or use the Makefile:

```bash
make setup
```

## Project Structure

```
l0l1-api/
├── l0l1/                  # Main package
│   ├── api/               # FastAPI REST API
│   ├── cli/               # CLI commands
│   ├── services/          # Core services
│   ├── models/            # AI model integrations
│   └── integrations/      # Jupyter, IDE integrations
├── tests/                 # Test suite
├── docs/                  # Documentation
├── examples/              # Example code
├── frontend/              # Web frontend
└── pyproject.toml         # Project configuration
```

## Common Tasks

### Running Tests

```bash
uv run pytest                           # All tests
uv run pytest --cov=l0l1               # With coverage
uv run pytest -m "not slow"            # Fast tests only
uv run pytest -m integration           # Integration tests
uv run pytest tests/test_specific.py   # Specific file
```

### Code Quality

```bash
# Format code
uv run black l0l1/ tests/
uv run isort l0l1/ tests/

# Lint
uv run flake8 l0l1/
uv run ruff check l0l1/
uv run mypy l0l1/

# All checks
make lint
```

### Running Services

```bash
# API server (development)
uv run uvicorn l0l1.api.main:app --reload --port 8000

# API server (production)
uv run uvicorn l0l1.api.main:app --host 0.0.0.0 --port 8000

# Background workers
uv run dramatiq l0l1.tasks

# Jupyter
uv run jupyter lab
```

## Dependency Management

### Adding Dependencies

```bash
# Add runtime dependency
# Edit pyproject.toml [project.dependencies]

# Add dev dependency
# Edit pyproject.toml [project.optional-dependencies.dev]

# Regenerate lock file
uv lock
uv sync
```

### Updating Dependencies

```bash
uv lock --upgrade        # Upgrade all
uv lock --upgrade-package fastapi  # Upgrade specific
```

### Optional Dependency Groups

| Group | Install | Contents |
|-------|---------|----------|
| `dev` | `uv sync --extra dev` | Testing, linting, formatting |
| `jupyter` | `uv sync --extra jupyter` | JupyterLab, IPython |
| `demo` | `uv sync --extra demo` | Demo data generation |
| `docs` | `uv sync --extra docs` | MkDocs, documentation |
| `postgres` | `uv sync --extra postgres` | PostgreSQL drivers |
| `mysql` | `uv sync --extra mysql` | MySQL drivers |

## Building

```bash
# Build package
uv build

# Outputs to dist/
# - l0l1-0.2.0-py3-none-any.whl
# - l0l1-0.2.0.tar.gz
```

## Publishing

```bash
# Publish to PyPI
uv publish

# Publish to Test PyPI
uv publish --index testpypi
```

## Makefile Reference

```bash
make help          # Show all commands

# Installation
make install       # Core dependencies
make install-all   # All dependencies
make install-prod  # Production only
make dev           # Dev environment setup

# Testing
make test          # Run tests
make test-cov      # Tests with coverage
make test-fast     # Fast tests only

# Code quality
make lint          # Run all linters
make format        # Format code
make format-check  # Check formatting

# Services
make serve         # Start API server
make jupyter       # Start JupyterLab
make workers       # Start background workers

# Demo
make demo-ecommerce  # Create demo
make demo-clean      # Clean demos

# Documentation
make docs          # Build docs
make docs-serve    # Serve docs locally

# Build
make build         # Build package
make publish       # Publish to PyPI

# Utilities
make clean         # Clean cache files
make update        # Update dependencies
make security      # Security audit
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run checks: `make lint && make test`
5. Commit: `git commit -m "Add my feature"`
6. Push: `git push origin feature/my-feature`
7. Create a Pull Request

### Commit Messages

Follow conventional commits:
- `feat: Add new validation rule`
- `fix: Handle null values in PII detection`
- `docs: Update API documentation`
- `test: Add tests for workspace service`
- `refactor: Simplify query parser`

### Code Style

- Black for formatting (line length 88)
- isort for import sorting
- Type hints required for public APIs
- Docstrings for public functions

## Troubleshooting

### Lock file issues

```bash
uv lock --upgrade
uv sync
```

### Clean rebuild

```bash
rm -rf .venv
uv sync
```

### Cache issues

```bash
uv cache clean
```
