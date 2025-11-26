# l0l1 SQL - VS Code Extension

AI-powered SQL validation, PII detection, and intelligent completions for VS Code.

## Features

- **Real-time Validation** - Syntax checking and best practice analysis
- **PII Detection** - Automatically detect sensitive data in queries
- **AI Explanations** - Get human-readable explanations of complex SQL
- **Smart Completions** - Context-aware SQL suggestions powered by AI
- **Quick Fixes** - One-click fixes for common issues

## Requirements

- VS Code 1.80.0 or higher
- l0l1 API server running (default: http://localhost:8000)

### Starting the l0l1 Server

```bash
# From the l0l1-api directory
uv run l0l1-serve
```

## Installation

### From VSIX (Local)

1. Build the extension:
   ```bash
   cd vscode-extension
   npm install
   npm run compile
   npx vsce package
   ```

2. Install in VS Code:
   - Open VS Code
   - Press `Ctrl+Shift+P` / `Cmd+Shift+P`
   - Run "Extensions: Install from VSIX..."
   - Select the generated `.vsix` file

### From Marketplace (Coming Soon)

Search for "l0l1 SQL" in the VS Code Extensions marketplace.

## Usage

### Commands

| Command | Keybinding | Description |
|---------|------------|-------------|
| `l0l1: Validate SQL Document` | `Ctrl+Shift+V` | Validate the current SQL file |
| `l0l1: Explain SQL Query` | `Ctrl+Shift+E` | Get AI explanation of query |
| `l0l1: Check for PII` | `Ctrl+Shift+P` | Detect PII in query |
| `l0l1: Anonymize PII in Query` | - | Replace PII with placeholders |
| `l0l1: Set Schema Context` | - | Select schema file for context |

### Context Menu

Right-click in any SQL file to access l0l1 commands.

### Status Bar

The status bar shows connection status:
- `$(check) l0l1` - Connected
- `$(warning) l0l1` - Disconnected

Click the status bar item to view the output channel.

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `l0l1.enable` | `true` | Enable/disable the extension |
| `l0l1.serverMode` | `api` | Connection mode: `api`, `tcp`, or `embedded` |
| `l0l1.apiUrl` | `http://localhost:8000` | l0l1 API server URL |
| `l0l1.workspace` | `vscode` | Default workspace name |
| `l0l1.validateOnSave` | `true` | Validate on file save |
| `l0l1.validateOnType` | `false` | Validate while typing |
| `l0l1.validateDelay` | `500` | Debounce delay (ms) for typing validation |
| `l0l1.enablePiiDetection` | `true` | Enable PII detection |
| `l0l1.enableCompletions` | `true` | Enable AI completions |
| `l0l1.schemaFile` | `""` | Path to schema file for context |
| `l0l1.showStatusBar` | `true` | Show status bar item |

### Server Modes

#### API Mode (Default)
Connects to the l0l1 REST API. Best for most users.

```json
{
  "l0l1.serverMode": "api",
  "l0l1.apiUrl": "http://localhost:8000"
}
```

#### TCP Mode
Connects to l0l1 LSP server over TCP. For advanced setups.

```json
{
  "l0l1.serverMode": "tcp",
  "l0l1.tcpHost": "localhost",
  "l0l1.tcpPort": 9257
}
```

Start LSP server:
```bash
uv run python -m l0l1.integrations.ide.server --tcp --port 9257
```

#### Embedded Mode
Starts l0l1 LSP server automatically. Requires Python and l0l1 installed.

```json
{
  "l0l1.serverMode": "embedded",
  "l0l1.pythonPath": "/path/to/python"
}
```

## Features in Detail

### Validation

SQL files are automatically validated on save. Errors and warnings appear in:
- The Problems panel
- Inline squiggles in the editor
- The status bar

### PII Detection

Detects common PII types:
- Email addresses
- Phone numbers
- Social Security Numbers
- Credit card numbers
- IP addresses
- Names and addresses

PII findings appear as warnings with quick fix suggestions.

### Explanations

Select a query and run "Explain SQL Query" to get:
- Plain English explanation
- Complexity assessment
- Tables accessed
- Performance suggestions

### Schema Context

Set a schema file for better validation:

1. Run `l0l1: Set Schema Context`
2. Select your schema SQL file
3. Validation will now consider table/column definitions

## Development

### Building

```bash
cd vscode-extension
npm install
npm run compile
```

### Watching

```bash
npm run watch
```

### Packaging

```bash
npm run package
```

### Debugging

1. Open the extension folder in VS Code
2. Press F5 to launch Extension Development Host
3. Open a SQL file to test

## Troubleshooting

### Extension not activating

- Ensure you have a `.sql` file open
- Check that l0l1 is enabled in settings

### Cannot connect to server

1. Verify the l0l1 server is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. Check the server URL in settings

3. View the l0l1 output channel for errors

### Validation not working

- Check the Problems panel for errors
- Ensure `l0l1.enable` is `true`
- Try restarting the server: `l0l1: Restart Server`

## License

MIT License - see [LICENSE](../LICENSE)

## Links

- [l0l1 Documentation](../docs/)
- [GitHub Repository](https://github.com/dipankar/l0l1-api)
- [Report Issues](https://github.com/dipankar/l0l1-api/issues)
