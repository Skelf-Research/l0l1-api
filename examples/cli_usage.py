#!/usr/bin/env python3
"""
Example usage of l0l1 CLI interface.

This demonstrates how to use the l0l1 command-line tool for SQL analysis.
"""

import subprocess
import os

# Example SQL queries
QUERIES = {
    "valid_query": """
    SELECT u.name, u.email, COUNT(o.id) as order_count
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    WHERE u.created_at > '2023-01-01'
    GROUP BY u.id, u.name, u.email
    ORDER BY order_count DESC;
    """,

    "query_with_pii": """
    SELECT name, email, phone
    FROM customers
    WHERE email = 'john.doe@example.com'
    AND phone = '555-123-4567';
    """,

    "partial_query": """
    SELECT name, email FROM users WHERE
    """,

    "invalid_query": """
    SELECT * FROM non_existent_table
    JOIN another_table ON invalid_column = other_invalid
    WHERE some_column = 'value' AND;
    """
}

# Example schema
SCHEMA = """
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

def run_cli_command(command: str) -> str:
    """Run a CLI command and return the output."""
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            check=False
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error running command: {e}"

def main():
    """Demonstrate CLI usage examples."""
    print("🚀 l0l1 CLI Usage Examples\n" + "="*50)

    # Save schema to a temporary file
    with open("example_schema.sql", "w") as f:
        f.write(SCHEMA)

    try:
        # 1. Show configuration
        print("\n📋 Current Configuration:")
        print(run_cli_command("l0l1 config-show"))

        # 2. Validate queries
        print("\n✅ Validating Valid Query:")
        with open("valid_query.sql", "w") as f:
            f.write(QUERIES["valid_query"])
        print(run_cli_command("l0l1 validate 'SELECT * FROM users' --schema example_schema.sql"))

        # 3. Check for PII
        print("\n🔒 Checking for PII:")
        print(run_cli_command(f"l0l1 check-pii \"{QUERIES['query_with_pii']}\" --anonymize"))

        # 4. Explain a query
        print("\n📝 Explaining Query:")
        print(run_cli_command(f"l0l1 explain \"{QUERIES['valid_query']}\" --schema example_schema.sql"))

        # 5. Complete partial query
        print("\n💡 Completing Partial Query:")
        print(run_cli_command(f"l0l1 complete \"{QUERIES['partial_query']}\" --schema example_schema.sql"))

        # 6. Correct invalid query
        print("\n🔧 Correcting Invalid Query:")
        print(run_cli_command(f"l0l1 correct \"{QUERIES['invalid_query']}\" --schema example_schema.sql"))

        # 7. Show learning stats
        print("\n🧠 Learning Statistics:")
        print(run_cli_command("l0l1 learning-stats --workspace example"))

    finally:
        # Clean up temporary files
        for file in ["example_schema.sql", "valid_query.sql"]:
            if os.path.exists(file):
                os.remove(file)

if __name__ == "__main__":
    main()