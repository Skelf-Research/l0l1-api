# l0l1

**AI-Powered SQL Analysis and Validation Library**

l0l1 provides intelligent SQL validation, PII detection, and continuous learning capabilities through CLI, REST API, Jupyter, and IDE interfaces.

## Features

- **AI Analysis** - Multi-provider (OpenAI, Anthropic) query validation, explanation, and completion
- **PII Detection** - Automatic detection and anonymization of sensitive data
- **Continuous Learning** - Learn from successful queries to improve suggestions
- **Multi-Interface** - CLI, REST API, Jupyter notebooks, IDE plugins (LSP)
- **Multi-Tenant** - Workspace isolation without authentication overhead

## Quick Start

```bash
# Install
git clone https://github.com/dipankar/l0l1-api.git && cd l0l1-api
uv sync

# Configure
export OPENAI_API_KEY="your-key"

# Run
uv run l0l1 validate "SELECT * FROM users WHERE id = 1"
uv run l0l1-serve  # Start API server at :8000
```

## Usage

### CLI
```bash
l0l1 validate "SELECT * FROM users"        # Validate query
l0l1 explain "SELECT COUNT(*) FROM orders" # Explain query
l0l1 check-pii "SELECT email FROM users"   # Detect PII
l0l1 serve --port 8000                     # Start API
```

### REST API
```bash
curl -X POST http://localhost:8000/sql/validate \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM users", "workspace_id": "default"}'
```

### Python
```python
from l0l1 import SQLValidator

validator = SQLValidator(workspace="my-project")
result = validator.validate("SELECT * FROM users WHERE active = true")
```

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/getting-started.md) | Installation, configuration, first steps |
| [Configuration](docs/configuration.md) | Environment variables and settings |
| [CLI Reference](docs/cli.md) | Command line interface documentation |
| [REST API](docs/api.md) | API endpoints and usage |
| [Development](docs/development.md) | Contributing, testing, uv workflow |

### Guides
| Guide | Description |
|-------|-------------|
| [VS Code Extension](docs/guides/vscode-extension.md) | IDE integration for VS Code |
| [PII Detection & Learning](docs/guides/pii-learning.md) | PII detection flow and learning system |
| [Graph-Based Learning](docs/guides/graph-learning.md) | Knowledge graph and continuous learning |
| [Jupyter Integration](docs/guides/jupyter.md) | Notebook magic commands and widgets |
| [UI Integration](docs/guides/ui-integration.md) | Frontend integration patterns |
| [Analytics Workbench](docs/guides/analytics-workbench.md) | Building analytics environments |

## Architecture

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Interfaces  │  │   Services   │  │    Models    │
├──────────────┤  ├──────────────┤  ├──────────────┤
│ CLI          │  │ PII Detection│  │ OpenAI       │
│ REST API     │──│ Learning     │──│ Anthropic    │
│ Jupyter      │  │ Workspace    │  │ (Extensible) │
│ IDE (LSP)    │  │ Vector DB    │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

## Development

```bash
make setup      # Full dev environment setup
make test       # Run tests
make lint       # Run linters
make serve      # Start dev server
make help       # Show all commands
```

## License

MIT License - see [LICENSE](LICENSE)

## Links

- [GitHub Issues](https://github.com/dipankar/l0l1-api/issues)
- [GitHub Discussions](https://github.com/dipankar/l0l1-api/discussions)
