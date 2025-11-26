# CLI Reference

The l0l1 CLI provides commands for SQL validation, PII detection, and server management.

## Installation

After installing l0l1, the CLI is available as `l0l1`:

```bash
uv run l0l1 --help
```

## Commands

### validate

Validate a SQL query for syntax and best practices.

```bash
l0l1 validate "SELECT * FROM users WHERE id = 1"
l0l1 validate --workspace myproject "SELECT * FROM orders"
l0l1 validate --schema schema.sql "SELECT * FROM products"
l0l1 validate --strict "SELECT * FROM users"  # Fail on warnings
```

**Options:**
- `--workspace, -w` - Workspace context
- `--schema, -s` - Schema file for context
- `--strict` - Treat warnings as errors
- `--format` - Output format: `text`, `json`

### explain

Get a human-readable explanation of a SQL query.

```bash
l0l1 explain "SELECT u.name, COUNT(o.id) FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.id"
l0l1 explain --detailed "SELECT * FROM users WHERE created_at > NOW() - INTERVAL '7 days'"
```

**Options:**
- `--workspace, -w` - Workspace context
- `--detailed` - Include execution plan details
- `--format` - Output format: `text`, `json`

### complete

Get AI-powered completions for partial SQL.

```bash
l0l1 complete "SELECT * FROM users WHERE"
l0l1 complete --workspace myproject "SELECT name FROM"
```

**Options:**
- `--workspace, -w` - Workspace context (uses learned patterns)
- `--limit, -n` - Number of suggestions (default: 5)

### check-pii

Detect personally identifiable information in SQL.

```bash
l0l1 check-pii "SELECT * FROM users WHERE email = 'john@example.com'"
l0l1 check-pii --anonymize "SELECT ssn FROM employees"
```

**Options:**
- `--anonymize, -a` - Return anonymized query
- `--entities` - Specific PII types to detect
- `--format` - Output format: `text`, `json`

### serve

Start the REST API server.

```bash
l0l1 serve
l0l1 serve --host 0.0.0.0 --port 8000
l0l1 serve --reload  # Development mode
```

**Options:**
- `--host, -h` - Server host (default: 0.0.0.0)
- `--port, -p` - Server port (default: 8000)
- `--reload` - Auto-reload on code changes
- `--workers` - Number of worker processes

### workspace

Manage workspaces.

```bash
l0l1 workspace list
l0l1 workspace create myproject
l0l1 workspace delete myproject
l0l1 workspace info myproject
```

### config

Manage configuration.

```bash
l0l1 config show
l0l1 config set L0L1_AI_PROVIDER anthropic
l0l1 config get L0L1_AI_PROVIDER
```

## Entry Points

l0l1 also provides these direct entry points:

```bash
# Start API server
l0l1-serve

# Initialize demo environment
l0l1-demo ecommerce
l0l1-demo saas
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Validation error |
| 2 | Configuration error |
| 3 | Connection error |

## Examples

### Batch Validation

```bash
# Validate multiple queries from file
cat queries.sql | while read query; do
  l0l1 validate "$query" --format json
done
```

### CI/CD Integration

```bash
# Fail build on invalid SQL
l0l1 validate --strict --format json "$(cat migration.sql)" || exit 1
```

### PII Audit

```bash
# Check all queries in a file for PII
l0l1 check-pii --format json < queries.sql > pii-report.json
```
