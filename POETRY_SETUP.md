# Poetry Setup Guide for l0l1

This guide explains how to set up and use l0l1 with Poetry for Python package management.

## 📋 Prerequisites

- Python 3.11 or higher
- Poetry installed on your system

### Installing Poetry

If you don't have Poetry installed, install it using:

```bash
# Using the official installer (recommended)
curl -sSL https://install.python-poetry.org | python3 -

# Or using pip
pip install poetry

# Or using homebrew (macOS)
brew install poetry
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/dipankar/l0l1-api.git
cd l0l1-api

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### 2. Run l0l1

```bash
# Check installation
poetry run l0l1 --help

# Start the API server
poetry run l0l1-serve

# Create a demo environment
poetry run l0l1-demo ecommerce
```

## 📦 Dependency Groups

l0l1 uses Poetry's dependency groups to organize different types of dependencies:

### Core Dependencies
```bash
# Install only core dependencies (default)
poetry install --only main
```

### Development Dependencies
```bash
# Install with development tools
poetry install --with dev

# Run tests
poetry run pytest

# Format code
poetry run black l0l1/
poetry run isort l0l1/

# Type checking
poetry run mypy l0l1/
```

### Optional Feature Groups

#### Jupyter Integration
```bash
# Install Jupyter dependencies
poetry install --with jupyter

# Start JupyterLab with l0l1 integration
poetry run jupyter lab
```

#### Demo Environment
```bash
# Install demo dependencies
poetry install --with demo

# Create demo workspace
poetry run l0l1-demo ecommerce
```

#### Documentation
```bash
# Install documentation dependencies
poetry install --with docs

# Build documentation
poetry run mkdocs build
poetry run mkdocs serve
```

#### IDE Integration
```bash
# Install IDE/LSP dependencies
poetry install --with ide

# This provides Language Server Protocol support for IDEs
```

#### Database-Specific Groups
```bash
# PostgreSQL support
poetry install --with postgres

# MySQL support
poetry install --with mysql

# SQLite support
poetry install --with sqlite
```

## 🛠️ Development Workflow

### Setting Up Development Environment

```bash
# Install all development dependencies
poetry install --with dev,jupyter,demo,docs

# Install pre-commit hooks
poetry run pre-commit install

# Run all checks
poetry run pre-commit run --all-files
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=l0l1

# Run only fast tests
poetry run pytest -m "not slow"

# Run integration tests
poetry run pytest -m integration

# Run demo tests (requires demo data)
poetry run pytest -m demo
```

### Code Quality

```bash
# Format code
poetry run black l0l1/
poetry run isort l0l1/

# Lint code
poetry run flake8 l0l1/
poetry run ruff l0l1/

# Type checking
poetry run mypy l0l1/
```

## 🌐 Production Deployment

### Building for Production

```bash
# Build wheel package
poetry build

# Install in production environment
pip install dist/l0l1-*.whl

# Or install from source
poetry install --only main --no-dev
```

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Core settings
L0L1_OPENAI_API_KEY=your_openai_key
L0L1_ANTHROPIC_API_KEY=your_anthropic_key

# Database settings
L0L1_DATABASE_URL=postgresql://user:pass@host:port/db

# Learning settings
L0L1_ENABLE_LEARNING=true
L0L1_ENABLE_PII_DETECTION=true

# Demo mode
L0L1_DEMO_MODE=false
```

### Running Services

```bash
# Start API server
poetry run uvicorn l0l1.api.main:app --host 0.0.0.0 --port 8000

# Start with auto-reload (development)
poetry run uvicorn l0l1.api.main:app --reload

# Start background workers
poetry run dramatiq l0l1.tasks
```

## 📊 Demo and Examples

### Creating Demo Environments

```bash
# E-commerce demo
poetry run l0l1-demo ecommerce

# SaaS platform demo
poetry run l0l1-demo saas

# Check demo status
poetry run l0l1 validate --workspace demo_ecommerce \"SELECT * FROM users LIMIT 10\"
```

### Jupyter Integration

```bash
# Start Jupyter with l0l1 magic commands
poetry run jupyter lab

# In a notebook cell:
%load_ext l0l1.jupyter
%l0l1_workspace demo_ecommerce
```

## 🔧 Configuration

### Poetry Configuration

View current Poetry configuration:
```bash
poetry config --list
```

Common configurations:
```bash
# Use in-project virtual environments
poetry config virtualenvs.in-project true

# Set custom cache directory
poetry config cache-dir /custom/cache/path

# Configure PyPI token for publishing
poetry config pypi-token.pypi your-token
```

### Adding Dependencies

```bash
# Add runtime dependency
poetry add requests

# Add development dependency
poetry add --group dev pytest-mock

# Add optional dependency
poetry add --group postgres psycopg2-binary

# Add from Git repository
poetry add git+https://github.com/user/repo.git

# Add with version constraints
poetry add \"fastapi>=0.100.0,<0.200.0\"
```

## 🚨 Troubleshooting

### Common Issues

1. **Virtual Environment Issues**
   ```bash
   # Delete and recreate virtual environment
   poetry env remove python
   poetry install
   ```

2. **Dependency Conflicts**
   ```bash
   # Update lock file
   poetry lock --no-update

   # Update dependencies
   poetry update
   ```

3. **Missing Optional Dependencies**
   ```bash
   # Install specific groups
   poetry install --with postgres,mysql

   # Check what's installed
   poetry show --tree
   ```

4. **Demo Data Issues**
   ```bash
   # Regenerate demo data
   rm -rf ~/.l0l1/workspaces/demo_*
   poetry run l0l1-demo ecommerce
   ```

### Performance Tips

1. **Faster Installs**
   ```bash
   # Parallel installation
   poetry config installer.parallel true

   # Skip development dependencies in production
   poetry install --only main
   ```

2. **Caching**
   ```bash
   # Clear Poetry cache
   poetry cache clear pypi --all

   # Use local wheel cache
   poetry config cache-dir ./cache
   ```

## 📚 Additional Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [l0l1 API Documentation](https://l0l1.readthedocs.io)
- [Contributing Guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## 🎯 Next Steps

After setting up with Poetry, you can:

1. **Explore the Demo**: `poetry run l0l1-demo ecommerce`
2. **Start the API**: `poetry run l0l1-serve`
3. **Try Jupyter Integration**: `poetry run jupyter lab`
4. **Read the Documentation**: Visit the docs for detailed API usage
5. **Contribute**: Check out issues and submit PRs!

---

**Happy analyzing with l0l1! 🚀**