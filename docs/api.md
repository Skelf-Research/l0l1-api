# REST API Reference

The l0l1 REST API provides programmatic access to SQL validation, PII detection, and learning features.

## Starting the Server

```bash
uv run l0l1-serve
# or
uv run l0l1 serve --host 0.0.0.0 --port 8000
```

API documentation available at `http://localhost:8000/docs` (Swagger UI).

## Authentication

By default, the API does not require authentication. For production, configure authentication via environment variables or reverse proxy.

## Endpoints

### SQL Validation

#### POST /sql/validate

Validate a SQL query.

**Request:**
```json
{
  "query": "SELECT * FROM users WHERE id = 1",
  "workspace_id": "default",
  "schema_context": "CREATE TABLE users (id INT, name VARCHAR(255));"
}
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": ["Consider adding LIMIT clause"],
  "suggestions": ["Add index on users.id for better performance"]
}
```

#### POST /sql/explain

Get explanation for a SQL query.

**Request:**
```json
{
  "query": "SELECT u.name, COUNT(o.id) FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.id",
  "workspace_id": "default"
}
```

**Response:**
```json
{
  "explanation": "This query retrieves each user's name along with their order count...",
  "complexity": "medium",
  "tables_accessed": ["users", "orders"]
}
```

#### POST /sql/complete

Get completions for partial SQL.

**Request:**
```json
{
  "partial_query": "SELECT * FROM users WHERE",
  "workspace_id": "default",
  "limit": 5
}
```

**Response:**
```json
{
  "completions": [
    "SELECT * FROM users WHERE id = ?",
    "SELECT * FROM users WHERE active = true",
    "SELECT * FROM users WHERE created_at > ?"
  ]
}
```

### PII Detection

#### POST /pii/detect

Detect PII in a SQL query.

**Request:**
```json
{
  "query": "SELECT * FROM users WHERE email = 'john@example.com'",
  "entities": ["EMAIL", "PHONE", "SSN"]
}
```

**Response:**
```json
{
  "has_pii": true,
  "detections": [
    {
      "entity_type": "EMAIL",
      "value": "john@example.com",
      "start": 42,
      "end": 58,
      "score": 0.95
    }
  ]
}
```

#### POST /pii/anonymize

Anonymize PII in a SQL query.

**Request:**
```json
{
  "query": "SELECT * FROM users WHERE email = 'john@example.com'"
}
```

**Response:**
```json
{
  "original_query": "SELECT * FROM users WHERE email = 'john@example.com'",
  "anonymized_query": "SELECT * FROM users WHERE email = '<EMAIL>'",
  "replacements": [
    {
      "original": "john@example.com",
      "replacement": "<EMAIL>",
      "entity_type": "EMAIL"
    }
  ]
}
```

### Learning

#### POST /learning/record

Record a successful query for learning.

**Request:**
```json
{
  "query": "SELECT * FROM users WHERE active = true ORDER BY created_at DESC",
  "workspace_id": "default",
  "execution_time_ms": 45,
  "success": true
}
```

#### GET /learning/similar

Find similar queries from learning history.

**Request:**
```
GET /learning/similar?query=SELECT * FROM users&workspace_id=default&limit=5
```

**Response:**
```json
{
  "similar_queries": [
    {
      "query": "SELECT * FROM users WHERE active = true",
      "similarity": 0.92,
      "execution_count": 15
    }
  ]
}
```

### Workspaces

#### GET /workspaces

List all workspaces.

#### POST /workspaces

Create a new workspace.

**Request:**
```json
{
  "workspace_id": "my-project",
  "description": "Production database queries",
  "schema_path": "/schemas/production.sql"
}
```

#### GET /workspaces/{workspace_id}

Get workspace details.

#### DELETE /workspaces/{workspace_id}

Delete a workspace.

### Health

#### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "ai_provider": "openai",
  "features": {
    "pii_detection": true,
    "learning": true
  }
}
```

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid SQL syntax",
    "details": {
      "line": 1,
      "column": 15,
      "suggestion": "Check for missing semicolon"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input |
| `NOT_FOUND` | 404 | Resource not found |
| `AI_ERROR` | 502 | AI provider error |
| `INTERNAL_ERROR` | 500 | Server error |

## Rate Limiting

Default rate limits (configurable):
- 100 requests/minute for validation endpoints
- 50 requests/minute for AI-powered endpoints

## SDKs

### Python

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/sql/validate",
        json={"query": "SELECT * FROM users", "workspace_id": "default"}
    )
    result = response.json()
```

### curl

```bash
curl -X POST http://localhost:8000/sql/validate \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM users", "workspace_id": "default"}'
```
