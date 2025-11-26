# Jupyter Integration

l0l1 provides deep Jupyter notebook integration with magic commands and interactive widgets for SQL analysis.

## Installation

```bash
uv sync --extra jupyter
uv run jupyter lab
```

## Quick Start

### Load the Extension

```python
%load_ext l0l1.integrations.jupyter
```

This displays a welcome message with available commands.

### Configure Settings

```python
# Set workspace
%l0l1_config --workspace myproject

# Set AI provider
%l0l1_config --provider anthropic

# Set API URL (if server is on different host)
%l0l1_config --api-url http://localhost:8000

# Load schema context
%l0l1_config --schema ./schema.sql
```

### Analyze SQL

```python
%%l0l1_sql --validate --explain
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id
ORDER BY order_count DESC
LIMIT 10
```

## Magic Commands

### %l0l1_config

Configure l0l1 settings for the session.

```python
%l0l1_config --workspace name    # Set workspace
%l0l1_config --provider openai   # Set AI provider
%l0l1_config --api-url URL       # Set server URL
%l0l1_config --schema file.sql   # Load schema file
```

### %l0l1_status

Display current status and configuration.

```python
%l0l1_status
```

Shows:
- Current workspace
- Server connection status
- AI provider
- Schema loaded status

### %l0l1_schema

Manage schema context.

```python
%l0l1_schema                     # Show current schema
%l0l1_schema ./schema.sql        # Load schema from file
%l0l1_schema --clear             # Clear schema context
```

### %%l0l1_sql

Analyze SQL queries (cell magic).

```python
%%l0l1_sql [options]
SELECT * FROM users
```

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--validate` | `-v` | Validate query syntax and logic |
| `--explain` | `-e` | Get AI explanation of query |
| `--check-pii` | `-p` | Detect PII in query |
| `--anonymize` | `-a` | Show anonymized version |
| `--complete` | `-c` | Get completion suggestions |
| `--schema` | `-s` | Inline schema context |

**Examples:**

```python
# Validate and explain
%%l0l1_sql --validate --explain
SELECT * FROM users WHERE id = 1

# Check for PII and anonymize
%%l0l1_sql --check-pii --anonymize
SELECT email, ssn FROM customers WHERE id = 123

# Get completions
%%l0l1_sql --complete
SELECT name FROM users WHERE created_at >
```

## Interactive Widgets

### SQL Validator Widget

Full-featured SQL analysis widget.

```python
from l0l1.integrations.jupyter.widgets import create_sql_validator

validator = create_sql_validator(workspace="myproject")
validator.display()
```

Features:
- SQL input area
- Validation, explanation, PII detection checkboxes
- Schema context input (collapsible)
- Rich formatted results

### Query History Widget

Search and explore similar queries from learning history.

```python
from l0l1.integrations.jupyter.widgets import create_query_history

history = create_query_history(workspace="myproject")
history.display()
```

Features:
- Search for similar queries
- View similarity scores
- Reuse past queries

### Schema Explorer Widget

Parse and explore database schema.

```python
from l0l1.integrations.jupyter.widgets import create_schema_explorer

explorer = create_schema_explorer()
explorer.display()
```

Features:
- Paste schema SQL
- Extract table and column names
- Visual schema overview

## Programmatic Usage

Use l0l1 directly in Python code:

```python
from l0l1.integrations.jupyter import L0l1JupyterClient
import asyncio

client = L0l1JupyterClient(api_url="http://localhost:8000")

# Validate
result = await client.validate(
    "SELECT * FROM users",
    workspace_id="myproject"
)
print(f"Valid: {result['valid']}")

# Check PII
pii = await client.check_pii("SELECT email FROM users")
print(f"Has PII: {pii['has_pii']}")

# Explain
explanation = await client.explain("SELECT COUNT(*) FROM orders")
print(explanation['explanation'])

# Get completions
completions = await client.complete("SELECT name FROM users WHERE")
for c in completions['completions']:
    print(c)
```

## Schema Context

Provide schema context for better validation:

### From File

```python
%l0l1_schema ./database/schema.sql
```

### Inline

```python
%%l0l1_sql --validate --schema "CREATE TABLE users (id INT, name VARCHAR(100))"
SELECT * FROM users
```

### In Widget

Use the collapsible "Schema Context" section in the SQL Validator widget.

## Integration with pandas

Validate queries before execution:

```python
import pandas as pd
from l0l1.integrations.jupyter import L0l1JupyterClient

client = L0l1JupyterClient()

query = "SELECT * FROM sales WHERE date > '2024-01-01'"

# Validate first
result = await client.validate(query)
if result['valid']:
    df = pd.read_sql(query, connection)
else:
    print("Fix query before running:")
    for error in result['errors']:
        print(f"  - {error}")
```

## Configuration Reference

### API Server

By default, the extension connects to `http://localhost:8000`. Change with:

```python
%l0l1_config --api-url http://your-server:8000
```

### Workspaces

Workspaces isolate learning data. Use different workspaces for different projects:

```python
%l0l1_config --workspace production
%l0l1_config --workspace development
```

## Troubleshooting

### Extension not loading

```python
# Check if installed
!pip list | grep l0l1

# Reinstall
!pip install -e ".[jupyter]"
```

### Server connection errors

1. Verify server is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check API URL:
   ```python
   %l0l1_config --api-url http://localhost:8000
   %l0l1_status
   ```

### Async errors

Install nest_asyncio (should be automatic with jupyter extra):

```python
!pip install nest-asyncio
```

## Example Notebook

```python
# Cell 1: Load extension
%load_ext l0l1.integrations.jupyter

# Cell 2: Configure
%l0l1_config --workspace analytics --provider openai

# Cell 3: Check status
%l0l1_status

# Cell 4: Define schema
schema = """
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255),
    created_at TIMESTAMP
);
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    total DECIMAL(10,2)
);
"""

# Cell 5: Analyze query with schema
%%l0l1_sql --validate --explain --schema "$schema"
SELECT u.name, SUM(o.total) as total_spent
FROM users u
JOIN orders o ON u.id = o.user_id
GROUP BY u.id
HAVING SUM(o.total) > 1000
ORDER BY total_spent DESC

# Cell 6: Check for PII
%%l0l1_sql --check-pii --anonymize
SELECT name, email, phone
FROM customers
WHERE email = 'john@example.com'

# Cell 7: Interactive widget
from l0l1.integrations.jupyter.widgets import create_sql_validator
validator = create_sql_validator()
validator.display()
```
