# VS Code Extension

l0l1 provides a VS Code extension for SQL validation, PII detection, and AI-powered completions directly in your editor.

## Installation

### Prerequisites

1. VS Code 1.80.0 or higher
2. l0l1 API server running

### Install from VSIX

```bash
cd vscode-extension
npm install
npm run compile
npx vsce package
```

Then in VS Code: `Extensions: Install from VSIX...`

## Quick Start

1. Start the l0l1 server:
   ```bash
   uv run l0l1-serve
   ```

2. Open a `.sql` file in VS Code

3. The extension activates automatically and validates your SQL

## Features

### Real-time Validation

SQL files are validated on save. Issues appear in:
- Problems panel
- Editor squiggles
- Status bar

### PII Detection

Automatically detects sensitive data:
- Email addresses
- Phone numbers
- SSNs, credit cards
- IP addresses

### AI Explanations

Select SQL and run `l0l1: Explain SQL Query` (`Ctrl+Shift+E`) to get:
- Plain English explanation
- Complexity assessment
- Tables accessed

### Smart Completions

AI-powered suggestions based on:
- Your schema context
- Previously successful queries
- SQL best practices

## Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| Validate Document | `Ctrl+Shift+V` | Validate current file |
| Explain Query | `Ctrl+Shift+E` | AI explanation |
| Check for PII | `Ctrl+Shift+P` | Detect PII |
| Anonymize PII | - | Replace PII with placeholders |
| Set Schema | - | Select schema file |

## Configuration

```json
{
  "l0l1.enable": true,
  "l0l1.serverMode": "api",
  "l0l1.apiUrl": "http://localhost:8000",
  "l0l1.workspace": "vscode",
  "l0l1.validateOnSave": true,
  "l0l1.validateOnType": false,
  "l0l1.enablePiiDetection": true,
  "l0l1.schemaFile": "./schema.sql"
}
```

### Server Modes

**API Mode** (default) - Connect to REST API:
```json
{
  "l0l1.serverMode": "api",
  "l0l1.apiUrl": "http://localhost:8000"
}
```

**TCP Mode** - Connect to LSP server:
```json
{
  "l0l1.serverMode": "tcp",
  "l0l1.tcpHost": "localhost",
  "l0l1.tcpPort": 9257
}
```

Start LSP server:
```bash
uv run l0l1-lsp --tcp --port 9257
```

**Embedded Mode** - Auto-start LSP:
```json
{
  "l0l1.serverMode": "embedded",
  "l0l1.pythonPath": "python"
}
```

## Schema Context

For better validation, set a schema file:

1. Run `l0l1: Set Schema Context`
2. Select your schema SQL file
3. Validation now considers your tables/columns

## Troubleshooting

### Extension not working

1. Check l0l1 server is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check VS Code output panel (l0l1 SQL)

3. Verify settings in VS Code

### No diagnostics appearing

- Ensure file is `.sql` extension
- Check `l0l1.enable` is `true`
- Try `l0l1: Restart Server`

## Development

See [vscode-extension/README.md](../../vscode-extension/README.md) for development instructions.
