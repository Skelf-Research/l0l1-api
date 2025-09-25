# l0l1 - SQL Analysis and Validation Library

> **🚀 Major Refactor Complete - v0.2.0**
>
> l0l1 has been completely redesigned as a comprehensive SQL validation library with CLI, API, IDE integration, and Jupyter notebook support!

**l0l1** is a modern SQL analysis and validation library that provides:

- 🤖 **AI-Powered Analysis**: Multi-provider support (OpenAI, Anthropic) for query validation, explanation, and completion
- 🔒 **PII Detection**: Automatic detection and anonymization of personally identifiable information
- 🧠 **Continuous Learning**: Learn from successful queries to provide better suggestions over time
- 🛠️ **Multiple Interfaces**: CLI, REST API, Jupyter notebook integration, and IDE plugins
- 🏢 **Multi-Tenant**: Support for multiple tenants without authentication complexity
- 📊 **Easy Model Switching**: Abstract model layer for easy provider switching

## Architecture Overview

```
┌─────────────────┬─────────────────┬─────────────────┐
│   Interfaces    │    Services     │     Models      │
├─────────────────┼─────────────────┼─────────────────┤
│ • CLI           │ • PII Detection │ • OpenAI        │
│ • REST API      │ • Learning      │ • Anthropic     │
│ • Jupyter       │ • Workspace     │ • (Extensible)  │
│ • IDE (LSP)     │ • Vector DB     │                 │
└─────────────────┴─────────────────┴─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation) for package management

### Installation

```bash
# Clone the repository
git clone https://github.com/dipankar/l0l1-api.git
cd l0l1-api

# Install with Poetry (recommended)
poetry install

# Or install everything including optional dependencies
make install-all

# Or traditional pip install
pip install -e .
```

### Configuration

```bash
# Set up environment variables
export L0L1_OPENAI_API_KEY="your_openai_key"
export L0L1_ANTHROPIC_API_KEY="your_anthropic_key"  # Optional
export L0L1_AI_PROVIDER="openai"  # or "anthropic"
```

### Poetry Development Workflow

This project uses [Poetry](https://python-poetry.org/) for dependency management. Here are the most common commands:

```bash
# Install dependencies
make install          # Core dependencies only
make install-all      # All dependencies including optional groups
make setup           # Complete development setup

# Development commands
make dev-server      # Start development server with demo data
make demo-ecommerce  # Create e-commerce demo environment
make test           # Run tests
make lint           # Run linting
make format         # Format code

# Quick validation
make validate SQL="SELECT * FROM users WHERE active = true"
make explain SQL="SELECT COUNT(*) FROM orders"

# See all available commands
make help
```

For detailed Poetry usage, see [POETRY_SETUP.md](POETRY_SETUP.md).

### Usage Examples

#### Command Line Interface

```bash
# Validate a SQL query
l0l1 validate "SELECT * FROM users WHERE id = 1"

# Check for PII and anonymize
l0l1 check-pii "SELECT * FROM users WHERE email = 'john@example.com'" --anonymize

# Explain a query with schema context
l0l1 explain "SELECT COUNT(*) FROM orders" --schema schema.sql

# Complete a partial query
l0l1 complete "SELECT name FROM users WHERE" --workspace myproject

# Start the API server
l0l1 serve --host 0.0.0.0 --port 8000
```

#### Jupyter Notebook Integration

```python
# Load the extension
%load_ext l0l1.integrations.jupyter

# Configure workspace
%l0l1_config --workspace data_analysis --provider openai

# Analyze SQL with magic commands
%%l0l1_sql --validate --explain --check-pii
SELECT u.name, u.email, COUNT(o.id) as orders
FROM users u LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id;

# Use interactive widget
from l0l1.integrations.jupyter.widgets import create_sql_validator
validator = create_sql_validator()
validator.display()
```

#### FastAPI REST API

```python
import aiohttp
import asyncio

async def validate_sql():
    async with aiohttp.ClientSession() as session:
        data = {
            "query": "SELECT * FROM users WHERE active = true",
            "schema_context": "CREATE TABLE users (id INT, active BOOLEAN);"
        }
        async with session.post('http://localhost:8000/sql/validate', json=data) as resp:
            result = await resp.json()
            print(result)

asyncio.run(validate_sql())
```

## Features

### 🤖 AI-Powered Analysis
- **Multi-Provider Support**: Switch between OpenAI and Anthropic models
- **Query Validation**: Detect syntax errors, logical issues, and best practice violations
- **Query Explanation**: Get human-readable explanations of complex SQL
- **Query Completion**: AI-assisted completion with context awareness
- **Query Correction**: Automatic fixing of common SQL mistakes

### 🔒 PII Detection & Anonymization
- **Comprehensive Detection**: Email addresses, phone numbers, SSNs, credit cards, etc.
- **SQL-Aware**: Understands SQL context for better accuracy
- **Anonymization**: Replace PII with safe placeholder values
- **Configurable**: Customize PII entities and detection rules

### 🧠 Continuous Learning
- **Success Tracking**: Learn from queries that execute successfully
- **PII Stripping**: Automatically anonymize queries before learning
- **Similarity Search**: Find similar successful queries using embeddings
- **Workspace Isolation**: Separate learning contexts per workspace/tenant

### 🛠️ Multiple Interfaces

#### Command Line Interface (CLI)
- Rich terminal output with syntax highlighting
- Batch processing support
- Configuration management
- Integration with shell scripts

#### REST API (FastAPI)
- OpenAPI documentation
- Async processing
- CORS support
- Multi-tenant workspace management

#### Jupyter Notebook Integration
- Magic commands for cell-based analysis
- Interactive widgets
- Rich HTML output
- Schema context management

#### IDE Integration (Language Server Protocol)
- Real-time validation
- Code completion
- Hover information
- Quick fixes
- PII warnings

## Configuration

Create a `.env` file or set environment variables:

```bash
# AI Configuration
L0L1_AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
L0L1_COMPLETION_MODEL=gpt-4o-mini
L0L1_EMBEDDING_MODEL=text-embedding-3-small

# Database
DATABASE_URL=sqlite:///./l0l1.db

# Features
L0L1_ENABLE_PII_DETECTION=true
L0L1_ENABLE_LEARNING=true
L0L1_LEARNING_THRESHOLD=0.8

# Directories
L0L1_WORKSPACE_DIR=./workspaces
L0L1_VECTOR_DB_PATH=./data/vector
L0L1_KNOWLEDGE_GRAPH_PATH=./data/kg

# API Server
L0L1_API_HOST=0.0.0.0
L0L1_API_PORT=8000

# Background Tasks
REDIS_URL=redis://localhost:6379/0
```

## Development Setup

```bash
# Clone and install dependencies
git clone https://github.com/yourusername/l0l1-api.git
cd l0l1-api
poetry install --with dev,jupyter

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
black l0l1/
isort l0l1/
flake8 l0l1/
mypy l0l1/

# Start development server
poetry run l0l1 serve --reload
```

## Examples

Check the `examples/` directory for:
- CLI usage examples
- Jupyter notebook demonstrations
- REST API client examples
- VS Code extension configuration

## Roadmap

- [ ] **Enhanced IDE Support**: VS Code, IntelliJ, Vim plugins
- [ ] **Database Connectivity**: Direct connection validation
- [ ] **Advanced Learning**: Query performance optimization
- [ ] **Schema Management**: Version control for database schemas
- [ ] **Collaboration Features**: Query sharing and commenting
- [ ] **Enterprise Features**: SSO, advanced permissions, audit logs

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 **Documentation**: [Coming Soon]
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/l0l1-api/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/l0l1-api/discussions)