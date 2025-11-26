# Getting Started

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- OpenAI or Anthropic API key

## Installation

### Using uv (Recommended)

```bash
git clone https://github.com/dipankar/l0l1-api.git
cd l0l1-api
uv sync
```

### Using pip

```bash
git clone https://github.com/dipankar/l0l1-api.git
cd l0l1-api
pip install -e .
```

### Optional Dependencies

```bash
# Development tools
uv sync --extra dev

# Jupyter integration
uv sync --extra jupyter

# All extras
uv sync --all-extras
```

## Configuration

Set your AI provider API key:

```bash
# OpenAI (default)
export OPENAI_API_KEY="sk-..."

# Or Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
export L0L1_AI_PROVIDER="anthropic"
```

See [Configuration](configuration.md) for all options.

## First Steps

### 1. Validate a Query

```bash
uv run l0l1 validate "SELECT * FROM users WHERE id = 1"
```

### 2. Explain a Query

```bash
uv run l0l1 explain "SELECT u.name, COUNT(o.id) FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.id"
```

### 3. Check for PII

```bash
uv run l0l1 check-pii "SELECT * FROM users WHERE email = 'john@example.com'"
```

### 4. Start the API Server

```bash
uv run l0l1-serve
# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 5. Try the Demo

```bash
# Create demo environment with sample data
uv run l0l1-demo ecommerce

# Validate against demo schema
uv run l0l1 validate --workspace demo_ecommerce "SELECT * FROM products"
```

## Using the Makefile

The project includes a Makefile for common tasks:

```bash
make help           # Show all commands
make install        # Install dependencies
make setup          # Full development setup
make serve          # Start API server
make test           # Run tests
make demo-ecommerce # Create demo environment
```

## Next Steps

- [CLI Reference](cli.md) - All CLI commands
- [REST API](api.md) - API endpoints
- [Configuration](configuration.md) - All settings
- [Jupyter Integration](guides/jupyter.md) - Notebook usage
