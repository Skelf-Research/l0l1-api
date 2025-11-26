"""Database connectivity service for schema introspection and validation."""

import asyncio
import sqlite3
import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager


class DatabaseConnection:
    """Represents a database connection configuration."""

    def __init__(
        self,
        id: str,
        name: str,
        db_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str = "",
        ssl_enabled: bool = False,
        workspace_id: Optional[str] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.name = name
        self.db_type = db_type
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.ssl_enabled = ssl_enabled
        self.workspace_id = workspace_id
        self.created_at = created_at or datetime.utcnow()
        self.last_connected = None
        self.is_connected = False

    def to_dict(self, include_password: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": self.id,
            "name": self.name,
            "db_type": self.db_type,
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "ssl_enabled": self.ssl_enabled,
            "workspace_id": self.workspace_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_connected": self.last_connected.isoformat() if self.last_connected else None,
            "is_connected": self.is_connected
        }
        if include_password:
            result["password"] = self.password
        return result


class ConnectionStore:
    """SQLite-based persistent storage for database connections."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or "./data/connections.db"
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS connections (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    db_type TEXT NOT NULL,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    database TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT,
                    ssl_enabled INTEGER DEFAULT 0,
                    workspace_id TEXT,
                    created_at TEXT NOT NULL,
                    last_connected TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_connections_workspace ON connections(workspace_id);
            """)
            conn.commit()
        finally:
            conn.close()

    def save(self, connection: DatabaseConnection) -> None:
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT OR REPLACE INTO connections
                (id, name, db_type, host, port, database, username, password,
                 ssl_enabled, workspace_id, created_at, last_connected)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                connection.id,
                connection.name,
                connection.db_type,
                connection.host,
                connection.port,
                connection.database,
                connection.username,
                connection.password,
                1 if connection.ssl_enabled else 0,
                connection.workspace_id,
                connection.created_at.isoformat() if connection.created_at else datetime.utcnow().isoformat(),
                connection.last_connected.isoformat() if connection.last_connected else None
            ))
            conn.commit()
        finally:
            conn.close()

    def get(self, connection_id: str) -> Optional[DatabaseConnection]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM connections WHERE id = ?", (connection_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_connection(row)
            return None
        finally:
            conn.close()

    def list(self, workspace_id: Optional[str] = None) -> List[DatabaseConnection]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if workspace_id:
                cursor.execute("SELECT * FROM connections WHERE workspace_id = ?", (workspace_id,))
            else:
                cursor.execute("SELECT * FROM connections")
            return [self._row_to_connection(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def delete(self, connection_id: str) -> bool:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM connections WHERE id = ?", (connection_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def _row_to_connection(self, row: sqlite3.Row) -> DatabaseConnection:
        return DatabaseConnection(
            id=row["id"],
            name=row["name"],
            db_type=row["db_type"],
            host=row["host"],
            port=row["port"],
            database=row["database"],
            username=row["username"],
            password=row["password"] or "",
            ssl_enabled=bool(row["ssl_enabled"]),
            workspace_id=row["workspace_id"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        )


class DatabaseService:
    """Service for managing database connections and schema introspection."""

    SUPPORTED_DATABASES = {
        "postgresql": {"port": 5432, "driver": "asyncpg"},
        "mysql": {"port": 3306, "driver": "aiomysql"},
        "sqlite": {"port": 0, "driver": "aiosqlite"},
        "duckdb": {"port": 0, "driver": "duckdb"},
    }

    def __init__(self, db_path: str = None):
        self.store = ConnectionStore(db_path or "./data/connections.db")
        self._pool_cache: Dict[str, Any] = {}

    def _generate_id(self, name: str, workspace_id: str) -> str:
        unique_str = f"{name}:{workspace_id}:{datetime.utcnow().isoformat()}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:12]

    async def create_connection(
        self,
        name: str,
        db_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str = "",
        ssl_enabled: bool = False,
        workspace_id: Optional[str] = None
    ) -> DatabaseConnection:
        """Create a new database connection configuration."""
        if db_type not in self.SUPPORTED_DATABASES:
            raise ValueError(f"Unsupported database type: {db_type}. Supported: {list(self.SUPPORTED_DATABASES.keys())}")

        conn_id = self._generate_id(name, workspace_id or "default")

        connection = DatabaseConnection(
            id=conn_id,
            name=name,
            db_type=db_type,
            host=host,
            port=port or self.SUPPORTED_DATABASES[db_type]["port"],
            database=database,
            username=username,
            password=password,
            ssl_enabled=ssl_enabled,
            workspace_id=workspace_id
        )

        self.store.save(connection)
        return connection

    @asynccontextmanager
    async def _get_async_connection(self, conn: DatabaseConnection):
        """Get an async database connection based on type."""
        db_conn = None
        try:
            if conn.db_type == "postgresql":
                import asyncpg
                db_conn = await asyncpg.connect(
                    host=conn.host,
                    port=conn.port,
                    user=conn.username,
                    password=conn.password,
                    database=conn.database,
                    ssl=conn.ssl_enabled if conn.ssl_enabled else None
                )
                yield db_conn
            elif conn.db_type == "mysql":
                import aiomysql
                db_conn = await aiomysql.connect(
                    host=conn.host,
                    port=conn.port,
                    user=conn.username,
                    password=conn.password,
                    db=conn.database,
                    autocommit=True
                )
                yield db_conn
            elif conn.db_type == "sqlite":
                import aiosqlite
                db_conn = await aiosqlite.connect(conn.database)
                db_conn.row_factory = aiosqlite.Row
                yield db_conn
            elif conn.db_type == "duckdb":
                import duckdb
                db_conn = duckdb.connect(conn.database)
                yield db_conn
            else:
                raise ValueError(f"Unsupported database type: {conn.db_type}")
        finally:
            if db_conn:
                if conn.db_type == "postgresql":
                    await db_conn.close()
                elif conn.db_type == "mysql":
                    db_conn.close()
                elif conn.db_type == "sqlite":
                    await db_conn.close()
                elif conn.db_type == "duckdb":
                    db_conn.close()

    async def test_connection(self, connection_id: str) -> Dict[str, Any]:
        """Test a database connection."""
        conn = self.store.get(connection_id)
        if not conn:
            raise ValueError(f"Connection not found: {connection_id}")

        result = {
            "success": False,
            "message": "",
            "latency_ms": 0,
            "server_version": None
        }

        start_time = datetime.utcnow()

        try:
            async with self._get_async_connection(conn) as db_conn:
                if conn.db_type == "postgresql":
                    version = await db_conn.fetchval("SELECT version()")
                    result["server_version"] = version.split(",")[0] if version else "Unknown"
                elif conn.db_type == "mysql":
                    async with db_conn.cursor() as cursor:
                        await cursor.execute("SELECT VERSION()")
                        row = await cursor.fetchone()
                        result["server_version"] = row[0] if row else "Unknown"
                elif conn.db_type == "sqlite":
                    async with db_conn.execute("SELECT sqlite_version()") as cursor:
                        row = await cursor.fetchone()
                        result["server_version"] = f"SQLite {row[0]}" if row else "Unknown"
                elif conn.db_type == "duckdb":
                    version = db_conn.execute("SELECT version()").fetchone()
                    result["server_version"] = version[0] if version else "DuckDB"

                result["success"] = True
                result["message"] = f"Successfully connected to {conn.db_type}"
                conn.last_connected = datetime.utcnow()
                conn.is_connected = True
                self.store.save(conn)

        except ImportError as e:
            result["success"] = False
            result["message"] = f"Database driver not installed: {str(e)}. Run: uv sync"
        except Exception as e:
            result["success"] = False
            result["message"] = f"Connection failed: {str(e)}"
            conn.is_connected = False

        end_time = datetime.utcnow()
        result["latency_ms"] = (end_time - start_time).total_seconds() * 1000

        return result

    async def get_connection(self, connection_id: str) -> Optional[DatabaseConnection]:
        return self.store.get(connection_id)

    async def list_connections(self, workspace_id: Optional[str] = None) -> List[DatabaseConnection]:
        return self.store.list(workspace_id)

    async def update_connection(self, connection_id: str, **kwargs) -> Optional[DatabaseConnection]:
        conn = self.store.get(connection_id)
        if not conn:
            return None

        for key, value in kwargs.items():
            if hasattr(conn, key) and value is not None:
                setattr(conn, key, value)

        self.store.save(conn)
        return conn

    async def delete_connection(self, connection_id: str) -> bool:
        if connection_id in self._pool_cache:
            del self._pool_cache[connection_id]
        return self.store.delete(connection_id)

    async def introspect_schema(self, connection_id: str) -> Dict[str, Any]:
        """Introspect database schema."""
        conn = self.store.get(connection_id)
        if not conn:
            raise ValueError(f"Connection not found: {connection_id}")

        schema = {
            "connection_id": connection_id,
            "database": conn.database,
            "db_type": conn.db_type,
            "introspected_at": datetime.utcnow().isoformat(),
            "tables": [],
            "views": [],
            "functions": []
        }

        try:
            async with self._get_async_connection(conn) as db_conn:
                if conn.db_type == "postgresql":
                    schema["tables"] = await self._introspect_postgresql(db_conn)
                elif conn.db_type == "mysql":
                    schema["tables"] = await self._introspect_mysql(db_conn, conn.database)
                elif conn.db_type == "sqlite":
                    schema["tables"] = await self._introspect_sqlite(db_conn)
                elif conn.db_type == "duckdb":
                    schema["tables"] = self._introspect_duckdb(db_conn)
        except ImportError as e:
            raise ValueError(f"Database driver not installed: {str(e)}")

        return schema

    async def _introspect_postgresql(self, db_conn) -> List[Dict[str, Any]]:
        """Introspect PostgreSQL schema."""
        tables = []

        # Get tables
        table_rows = await db_conn.fetch("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            AND table_type = 'BASE TABLE'
            ORDER BY table_schema, table_name
        """)

        for table_row in table_rows:
            table_schema = table_row["table_schema"]
            table_name = table_row["table_name"]

            # Get columns
            column_rows = await db_conn.fetch("""
                SELECT column_name, data_type, is_nullable, column_default,
                       character_maximum_length, numeric_precision, numeric_scale
                FROM information_schema.columns
                WHERE table_schema = $1 AND table_name = $2
                ORDER BY ordinal_position
            """, table_schema, table_name)

            columns = []
            for col in column_rows:
                col_type = col["data_type"].upper()
                if col["character_maximum_length"]:
                    col_type = f"{col_type}({col['character_maximum_length']})"
                elif col["numeric_precision"]:
                    col_type = f"{col_type}({col['numeric_precision']},{col['numeric_scale'] or 0})"

                columns.append({
                    "name": col["column_name"],
                    "type": col_type,
                    "nullable": col["is_nullable"] == "YES",
                    "default": col["column_default"]
                })

            # Get primary keys
            pk_rows = await db_conn.fetch("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = $1 AND tc.table_name = $2
                AND tc.constraint_type = 'PRIMARY KEY'
            """, table_schema, table_name)
            pk_columns = [row["column_name"] for row in pk_rows]

            for col in columns:
                col["primary_key"] = col["name"] in pk_columns

            # Get indexes
            index_rows = await db_conn.fetch("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = $1 AND tablename = $2
            """, table_schema, table_name)

            indexes = []
            for idx in index_rows:
                indexes.append({
                    "name": idx["indexname"],
                    "definition": idx["indexdef"]
                })

            # Get foreign keys
            fk_rows = await db_conn.fetch("""
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = $1 AND tc.table_name = $2
            """, table_schema, table_name)

            foreign_keys = []
            for fk in fk_rows:
                foreign_keys.append({
                    "columns": [fk["column_name"]],
                    "references": {
                        "table": fk["foreign_table_name"],
                        "columns": [fk["foreign_column_name"]]
                    }
                })

            tables.append({
                "name": table_name,
                "schema": table_schema,
                "columns": columns,
                "indexes": indexes,
                "foreign_keys": foreign_keys
            })

        return tables

    async def _introspect_mysql(self, db_conn, database: str) -> List[Dict[str, Any]]:
        """Introspect MySQL schema."""
        tables = []

        async with db_conn.cursor() as cursor:
            # Get tables
            await cursor.execute("""
                SELECT TABLE_NAME
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
            """, (database,))
            table_rows = await cursor.fetchall()

            for (table_name,) in table_rows:
                # Get columns
                await cursor.execute("""
                    SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (database, table_name))
                column_rows = await cursor.fetchall()

                columns = []
                for col in column_rows:
                    columns.append({
                        "name": col[0],
                        "type": col[1].upper(),
                        "nullable": col[2] == "YES",
                        "default": col[3],
                        "primary_key": col[4] == "PRI"
                    })

                # Get indexes
                await cursor.execute(f"SHOW INDEX FROM `{table_name}`")
                index_rows = await cursor.fetchall()

                indexes = {}
                for idx in index_rows:
                    idx_name = idx[2]
                    if idx_name not in indexes:
                        indexes[idx_name] = {"name": idx_name, "columns": [], "unique": not idx[1]}
                    indexes[idx_name]["columns"].append(idx[4])

                # Get foreign keys
                await cursor.execute("""
                    SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    AND REFERENCED_TABLE_NAME IS NOT NULL
                """, (database, table_name))
                fk_rows = await cursor.fetchall()

                foreign_keys = []
                for fk in fk_rows:
                    foreign_keys.append({
                        "columns": [fk[0]],
                        "references": {"table": fk[1], "columns": [fk[2]]}
                    })

                tables.append({
                    "name": table_name,
                    "schema": database,
                    "columns": columns,
                    "indexes": list(indexes.values()),
                    "foreign_keys": foreign_keys
                })

        return tables

    async def _introspect_sqlite(self, db_conn) -> List[Dict[str, Any]]:
        """Introspect SQLite schema."""
        tables = []

        # Get tables
        async with db_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ) as cursor:
            table_rows = await cursor.fetchall()

        for (table_name,) in table_rows:
            # Get columns using PRAGMA
            async with db_conn.execute(f"PRAGMA table_info('{table_name}')") as cursor:
                column_rows = await cursor.fetchall()

            columns = []
            for col in column_rows:
                columns.append({
                    "name": col[1],
                    "type": col[2] or "TEXT",
                    "nullable": not col[3],
                    "default": col[4],
                    "primary_key": bool(col[5])
                })

            # Get indexes
            async with db_conn.execute(f"PRAGMA index_list('{table_name}')") as cursor:
                index_rows = await cursor.fetchall()

            indexes = []
            for idx in index_rows:
                idx_name = idx[1]
                async with db_conn.execute(f"PRAGMA index_info('{idx_name}')") as idx_cursor:
                    idx_cols = await idx_cursor.fetchall()
                indexes.append({
                    "name": idx_name,
                    "columns": [c[2] for c in idx_cols],
                    "unique": bool(idx[2])
                })

            # Get foreign keys
            async with db_conn.execute(f"PRAGMA foreign_key_list('{table_name}')") as cursor:
                fk_rows = await cursor.fetchall()

            foreign_keys = []
            for fk in fk_rows:
                foreign_keys.append({
                    "columns": [fk[3]],
                    "references": {"table": fk[2], "columns": [fk[4]]}
                })

            tables.append({
                "name": table_name,
                "schema": "main",
                "columns": columns,
                "indexes": indexes,
                "foreign_keys": foreign_keys
            })

        return tables

    def _introspect_duckdb(self, db_conn) -> List[Dict[str, Any]]:
        """Introspect DuckDB schema."""
        tables = []

        # Get tables
        table_rows = db_conn.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'main' AND table_type = 'BASE TABLE'
        """).fetchall()

        for (table_name,) in table_rows:
            # Get columns
            column_rows = db_conn.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'main' AND table_name = ?
                ORDER BY ordinal_position
            """, [table_name]).fetchall()

            columns = []
            for col in column_rows:
                columns.append({
                    "name": col[0],
                    "type": col[1].upper(),
                    "nullable": col[2] == "YES",
                    "default": col[3],
                    "primary_key": False
                })

            tables.append({
                "name": table_name,
                "schema": "main",
                "columns": columns,
                "indexes": [],
                "foreign_keys": []
            })

        return tables

    async def execute_query(
        self,
        connection_id: str,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Execute a query on the database (read-only for safety)."""
        conn = self.store.get(connection_id)
        if not conn:
            raise ValueError(f"Connection not found: {connection_id}")

        # Safety check - only allow SELECT queries
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT") and not query_upper.startswith("WITH"):
            raise ValueError("Only SELECT and WITH (CTE) queries are allowed for safety")

        # Add LIMIT if not present
        if "LIMIT" not in query_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"

        result = {
            "success": False,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "execution_time_ms": 0,
            "truncated": False
        }

        start_time = datetime.utcnow()

        try:
            async with self._get_async_connection(conn) as db_conn:
                if conn.db_type == "postgresql":
                    rows = await db_conn.fetch(query)
                    if rows:
                        result["columns"] = list(rows[0].keys())
                        result["rows"] = [list(row.values()) for row in rows]
                        result["row_count"] = len(rows)

                elif conn.db_type == "mysql":
                    async with db_conn.cursor() as cursor:
                        await cursor.execute(query)
                        rows = await cursor.fetchall()
                        if cursor.description:
                            result["columns"] = [col[0] for col in cursor.description]
                        result["rows"] = [list(row) for row in rows]
                        result["row_count"] = len(rows)

                elif conn.db_type == "sqlite":
                    async with db_conn.execute(query) as cursor:
                        rows = await cursor.fetchall()
                        if cursor.description:
                            result["columns"] = [col[0] for col in cursor.description]
                        result["rows"] = [list(row) for row in rows]
                        result["row_count"] = len(rows)

                elif conn.db_type == "duckdb":
                    cursor_result = db_conn.execute(query)
                    rows = cursor_result.fetchall()
                    result["columns"] = [col[0] for col in cursor_result.description]
                    result["rows"] = [list(row) for row in rows]
                    result["row_count"] = len(rows)

                result["success"] = True
                result["truncated"] = result["row_count"] >= limit

        except ImportError as e:
            result["success"] = False
            result["error"] = f"Database driver not installed: {str(e)}"
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)

        end_time = datetime.utcnow()
        result["execution_time_ms"] = (end_time - start_time).total_seconds() * 1000

        return result

    def get_supported_databases(self) -> Dict[str, Any]:
        """Get list of supported database types."""
        return {
            db_type: {"default_port": info["port"], "driver": info["driver"]}
            for db_type, info in self.SUPPORTED_DATABASES.items()
        }
