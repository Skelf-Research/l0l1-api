# Configuration

l0l1 can be configured via environment variables or a `.env` file.

## AI Provider Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `L0L1_AI_PROVIDER` | `openai` | AI provider: `openai` or `anthropic` |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | - | Anthropic API key |
| `L0L1_COMPLETION_MODEL` | `gpt-4o-mini` | Model for completions |
| `L0L1_EMBEDDING_MODEL` | `text-embedding-3-small` | Model for embeddings |

## Database Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./l0l1.db` | Main database URL |
| `L0L1_VECTOR_DB_PATH` | `./data/vector` | Vector database path |
| `L0L1_KNOWLEDGE_GRAPH_PATH` | `./data/kg` | Knowledge graph path |

## Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `L0L1_ENABLE_PII_DETECTION` | `true` | Enable PII detection |
| `L0L1_ENABLE_LEARNING` | `true` | Enable continuous learning |
| `L0L1_LEARNING_THRESHOLD` | `0.8` | Similarity threshold for learning |

## Server Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `L0L1_API_HOST` | `0.0.0.0` | API server host |
| `L0L1_API_PORT` | `8000` | API server port |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for background tasks |

## Workspace Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `L0L1_WORKSPACE_DIR` | `./workspaces` | Workspace storage directory |
| `L0L1_DEFAULT_WORKSPACE` | `default` | Default workspace name |

## Example .env File

```bash
# AI Configuration
L0L1_AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
L0L1_COMPLETION_MODEL=gpt-4o-mini
L0L1_EMBEDDING_MODEL=text-embedding-3-small

# Database
DATABASE_URL=sqlite:///./l0l1.db
L0L1_VECTOR_DB_PATH=./data/vector

# Features
L0L1_ENABLE_PII_DETECTION=true
L0L1_ENABLE_LEARNING=true
L0L1_LEARNING_THRESHOLD=0.8

# Server
L0L1_API_HOST=0.0.0.0
L0L1_API_PORT=8000

# Background Tasks
REDIS_URL=redis://localhost:6379/0
```

## Per-Workspace Configuration

Workspaces can have their own configuration:

```python
from l0l1 import WorkspaceConfig

config = WorkspaceConfig(
    workspace_id="my-project",
    ai_provider="anthropic",
    enable_pii_detection=True,
    schema_path="./schemas/my-project.sql"
)
```

## Database Backend Configuration

### PostgreSQL
```bash
uv sync --extra postgres
DATABASE_URL=postgresql://user:pass@localhost:5432/l0l1
```

### MySQL
```bash
uv sync --extra mysql
DATABASE_URL=mysql://user:pass@localhost:3306/l0l1
```

### SQLite (Default)
```bash
DATABASE_URL=sqlite:///./l0l1.db
```
