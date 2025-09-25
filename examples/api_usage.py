#!/usr/bin/env python3
"""
Example usage of l0l1 FastAPI endpoints.

This demonstrates how to use the l0l1 REST API for SQL analysis.
"""

import asyncio
import aiohttp
import json

# API base URL
BASE_URL = "http://localhost:8000"

# Example data
TENANT_ID = "example_tenant"
WORKSPACE_NAME = "data_analysis"

EXAMPLE_QUERIES = {
    "valid": """
    SELECT u.name, u.email, COUNT(o.id) as order_count
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    WHERE u.created_at > '2023-01-01'
    GROUP BY u.id, u.name, u.email
    ORDER BY order_count DESC;
    """,

    "with_pii": """
    SELECT name, email, phone, ssn
    FROM customers
    WHERE email = 'john.doe@example.com';
    """,

    "invalid": """
    SELECT * FROM non_existent_table
    WHERE invalid_column = 'value';
    """
}

SCHEMA_CONTEXT = """
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
"""

class L0L1APIClient:
    """Simple client for l0l1 API."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
        self.workspace_id = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def health_check(self):
        """Check API health."""
        async with self.session.get(f"{self.base_url}/health") as response:
            return await response.json()

    async def create_workspace(self, name: str, tenant_id: str):
        """Create a new workspace."""
        data = {
            "name": name,
            "tenant_id": tenant_id,
            "description": f"Workspace for {name}"
        }
        async with self.session.post(f"{self.base_url}/workspaces", json=data) as response:
            result = await response.json()
            self.workspace_id = result["id"]
            return result

    async def validate_query(self, query: str, schema_context: str = None):
        """Validate a SQL query."""
        data = {
            "query": query,
            "schema_context": schema_context,
            "workspace_id": self.workspace_id
        }
        async with self.session.post(f"{self.base_url}/sql/validate", json=data) as response:
            return await response.json()

    async def explain_query(self, query: str, schema_context: str = None):
        """Explain a SQL query."""
        data = {
            "query": query,
            "schema_context": schema_context
        }
        async with self.session.post(f"{self.base_url}/sql/explain", json=data) as response:
            return await response.json()

    async def complete_query(self, partial_query: str, schema_context: str = None):
        """Complete a partial SQL query."""
        data = {
            "partial_query": partial_query,
            "schema_context": schema_context,
            "workspace_id": self.workspace_id,
            "max_suggestions": 3
        }
        async with self.session.post(f"{self.base_url}/sql/complete", json=data) as response:
            return await response.json()

    async def correct_query(self, query: str, error_message: str = None, schema_context: str = None):
        """Correct a SQL query."""
        data = {
            "query": query,
            "error_message": error_message,
            "schema_context": schema_context,
            "workspace_id": self.workspace_id
        }
        async with self.session.post(f"{self.base_url}/sql/correct", json=data) as response:
            return await response.json()

    async def check_pii(self, query: str):
        """Check query for PII."""
        data = {"query": query}
        async with self.session.post(f"{self.base_url}/sql/check-pii", json=data) as response:
            return await response.json()

    async def record_successful_query(self, query: str, execution_time: float, result_count: int):
        """Record a successful query for learning."""
        data = {
            "query": query,
            "workspace_id": self.workspace_id,
            "execution_time": execution_time,
            "result_count": result_count,
            "schema_context": SCHEMA_CONTEXT
        }
        async with self.session.post(f"{self.base_url}/learning/record", json=data) as response:
            return response.status == 201

    async def get_learning_stats(self):
        """Get learning statistics."""
        params = {"workspace_id": self.workspace_id}
        async with self.session.get(f"{self.base_url}/learning/stats", params=params) as response:
            return await response.json()

def print_json(data, title=""):
    """Pretty print JSON data."""
    if title:
        print(f"\n{title}")
        print("=" * len(title))
    print(json.dumps(data, indent=2, default=str))

async def main():
    """Demonstrate API usage."""
    print("🚀 l0l1 FastAPI Usage Examples")
    print("=" * 50)

    try:
        async with L0L1APIClient(BASE_URL) as client:
            # 1. Health check
            health = await client.health_check()
            print_json(health, "Health Check")

            # 2. Create workspace
            workspace = await client.create_workspace(WORKSPACE_NAME, TENANT_ID)
            print_json(workspace, "Created Workspace")

            # 3. Validate queries
            print("\n" + "="*50)
            print("QUERY VALIDATION")
            print("="*50)

            # Valid query
            result = await client.validate_query(EXAMPLE_QUERIES["valid"], SCHEMA_CONTEXT)
            print_json(result, "Valid Query Validation")

            # Invalid query
            result = await client.validate_query(EXAMPLE_QUERIES["invalid"], SCHEMA_CONTEXT)
            print_json(result, "Invalid Query Validation")

            # 4. PII Detection
            print("\n" + "="*50)
            print("PII DETECTION")
            print("="*50)

            pii_result = await client.check_pii(EXAMPLE_QUERIES["with_pii"])
            print_json(pii_result, "PII Detection Result")

            # 5. Query Explanation
            print("\n" + "="*50)
            print("QUERY EXPLANATION")
            print("="*50)

            explanation = await client.explain_query(EXAMPLE_QUERIES["valid"], SCHEMA_CONTEXT)
            print_json(explanation, "Query Explanation")

            # 6. Query Completion
            print("\n" + "="*50)
            print("QUERY COMPLETION")
            print("="*50)

            partial_query = "SELECT name, email FROM users WHERE created_at >"
            completion = await client.complete_query(partial_query, SCHEMA_CONTEXT)
            print_json(completion, "Query Completion")

            # 7. Query Correction
            print("\n" + "="*50)
            print("QUERY CORRECTION")
            print("="*50)

            error_msg = "Table 'non_existent_table' doesn't exist"
            correction = await client.correct_query(
                EXAMPLE_QUERIES["invalid"],
                error_msg,
                SCHEMA_CONTEXT
            )
            print_json(correction, "Query Correction")

            # 8. Record successful queries for learning
            print("\n" + "="*50)
            print("LEARNING SYSTEM")
            print("="*50)

            success = await client.record_successful_query(
                EXAMPLE_QUERIES["valid"],
                0.042,  # 42ms execution time
                150     # 150 rows returned
            )
            print(f"Query recorded for learning: {success}")

            # Get learning stats
            stats = await client.get_learning_stats()
            print_json(stats, "Learning Statistics")

    except aiohttp.ClientConnectorError:
        print("❌ Error: Could not connect to l0l1 API server.")
        print("Make sure the server is running with: l0l1 serve")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())