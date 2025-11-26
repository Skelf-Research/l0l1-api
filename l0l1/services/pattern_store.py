"""Persistent storage for learned SQL patterns using SQLite."""

import sqlite3
import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import threading


class PatternStore:
    """SQLite-based persistent storage for learned patterns."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = None):
        """Singleton pattern to ensure single database connection."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = None):
        if self._initialized:
            return

        self.db_path = db_path or "./data/learning_patterns.db"
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()
        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema."""
        conn = self._get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    query_hash TEXT UNIQUE NOT NULL,
                    workspace_id TEXT NOT NULL,
                    embedding TEXT,
                    success_count INTEGER DEFAULT 1,
                    execution_time REAL DEFAULT 0.0,
                    result_count INTEGER DEFAULT 0,
                    schema_context TEXT,
                    created_at TEXT NOT NULL,
                    last_used TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_patterns_workspace ON patterns(workspace_id);
                CREATE INDEX IF NOT EXISTS idx_patterns_last_used ON patterns(last_used);
                CREATE INDEX IF NOT EXISTS idx_patterns_success ON patterns(success_count);
                CREATE INDEX IF NOT EXISTS idx_patterns_hash ON patterns(query_hash);
            """)
            conn.commit()
        finally:
            conn.close()

    def _generate_id(self, query: str) -> str:
        """Generate a unique pattern ID from query hash."""
        return hashlib.sha256(query.encode()).hexdigest()

    def save_pattern(
        self,
        query: str,
        workspace_id: str,
        embedding: List[float] = None,
        execution_time: float = 0.0,
        result_count: int = 0,
        schema_context: str = None
    ) -> Dict[str, Any]:
        """Save or update a learned pattern."""
        query_hash = self._generate_id(query)
        now = datetime.utcnow().isoformat()

        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Check if pattern exists
            cursor.execute(
                "SELECT id, success_count, execution_time FROM patterns WHERE query_hash = ?",
                (query_hash,)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing pattern
                new_success_count = existing["success_count"] + 1
                avg_execution_time = (existing["execution_time"] + execution_time) / 2

                cursor.execute("""
                    UPDATE patterns
                    SET success_count = ?,
                        execution_time = ?,
                        last_used = ?,
                        embedding = COALESCE(?, embedding)
                    WHERE query_hash = ?
                """, (
                    new_success_count,
                    avg_execution_time,
                    now,
                    json.dumps(embedding) if embedding else None,
                    query_hash
                ))
                conn.commit()

                return self.get_pattern(query_hash)
            else:
                # Insert new pattern
                cursor.execute("""
                    INSERT INTO patterns (id, query, query_hash, workspace_id, embedding,
                                         success_count, execution_time, result_count,
                                         schema_context, created_at, last_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    query_hash,
                    query,
                    query_hash,
                    workspace_id,
                    json.dumps(embedding) if embedding else None,
                    1,
                    execution_time,
                    result_count,
                    schema_context,
                    now,
                    now
                ))
                conn.commit()

                return self.get_pattern(query_hash)
        finally:
            conn.close()

    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get a pattern by ID."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patterns WHERE id = ? OR query_hash = ?", (pattern_id, pattern_id))
            row = cursor.fetchone()

            if not row:
                return None

            return self._row_to_dict(row)
        finally:
            conn.close()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to a dictionary."""
        return {
            "id": row["id"],
            "query": row["query"],
            "query_hash": row["query_hash"],
            "workspace_id": row["workspace_id"],
            "embedding": json.loads(row["embedding"]) if row["embedding"] else None,
            "success_count": row["success_count"],
            "execution_time": row["execution_time"],
            "result_count": row["result_count"],
            "schema_context": row["schema_context"],
            "created_at": row["created_at"],
            "last_used": row["last_used"],
            "confidence": min(1.0, row["success_count"] / 10)
        }

    def list_patterns(
        self,
        workspace_id: str = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "last_used",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """List patterns with pagination and sorting."""
        valid_sort_fields = ["last_used", "success_count", "execution_time", "created_at"]
        if sort_by not in valid_sort_fields:
            sort_by = "last_used"

        order = "DESC" if sort_order == "desc" else "ASC"

        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Get total count
            if workspace_id:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM patterns WHERE workspace_id = ?",
                    (workspace_id,)
                )
            else:
                cursor.execute("SELECT COUNT(*) as count FROM patterns")

            total = cursor.fetchone()["count"]

            # Get patterns
            if workspace_id:
                cursor.execute(f"""
                    SELECT * FROM patterns
                    WHERE workspace_id = ?
                    ORDER BY {sort_by} {order}
                    LIMIT ? OFFSET ?
                """, (workspace_id, limit, offset))
            else:
                cursor.execute(f"""
                    SELECT * FROM patterns
                    ORDER BY {sort_by} {order}
                    LIMIT ? OFFSET ?
                """, (limit, offset))

            rows = cursor.fetchall()
            patterns = [self._row_to_dict(row) for row in rows]

            # Remove embeddings from list response (too large)
            for p in patterns:
                p.pop("embedding", None)

            return {
                "patterns": patterns,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        finally:
            conn.close()

    def get_patterns_with_embeddings(self, workspace_id: str = None) -> List[Dict[str, Any]]:
        """Get all patterns with embeddings for similarity search."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            if workspace_id:
                cursor.execute(
                    "SELECT * FROM patterns WHERE workspace_id = ? AND embedding IS NOT NULL",
                    (workspace_id,)
                )
            else:
                cursor.execute("SELECT * FROM patterns WHERE embedding IS NOT NULL")

            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
        finally:
            conn.close()

    def update_pattern(self, pattern_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a pattern."""
        allowed_fields = ["query", "success_count", "execution_time", "schema_context"]
        update_fields = {k: v for k, v in updates.items() if k in allowed_fields and v is not None}

        if not update_fields:
            return self.get_pattern(pattern_id)

        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            set_clause = ", ".join([f"{k} = ?" for k in update_fields.keys()])
            values = list(update_fields.values()) + [datetime.utcnow().isoformat(), pattern_id]

            cursor.execute(f"""
                UPDATE patterns
                SET {set_clause}, last_used = ?
                WHERE id = ? OR query_hash = ?
            """, values + [pattern_id])

            conn.commit()

            if cursor.rowcount == 0:
                return None

            return self.get_pattern(pattern_id)
        finally:
            conn.close()

    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM patterns WHERE id = ? OR query_hash = ?", (pattern_id, pattern_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def bulk_delete(
        self,
        pattern_ids: List[str] = None,
        workspace_id: str = None,
        older_than_days: int = None
    ) -> int:
        """Bulk delete patterns based on criteria."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            deleted = 0

            if pattern_ids:
                placeholders = ",".join(["?" for _ in pattern_ids])
                cursor.execute(f"DELETE FROM patterns WHERE id IN ({placeholders})", pattern_ids)
                deleted += cursor.rowcount

            if workspace_id and not pattern_ids:
                cursor.execute("DELETE FROM patterns WHERE workspace_id = ?", (workspace_id,))
                deleted += cursor.rowcount

            if older_than_days:
                cutoff = (datetime.utcnow() - timedelta(days=older_than_days)).isoformat()
                cursor.execute("DELETE FROM patterns WHERE created_at < ?", (cutoff,))
                deleted += cursor.rowcount

            conn.commit()
            return deleted
        finally:
            conn.close()

    def adjust_confidence(self, pattern_id: str, adjustment: float) -> Optional[Dict[str, Any]]:
        """Adjust pattern confidence by modifying success count."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Get current success count
            cursor.execute("SELECT success_count FROM patterns WHERE id = ? OR query_hash = ?", (pattern_id, pattern_id))
            row = cursor.fetchone()

            if not row:
                return None

            new_count = max(1, row["success_count"] + int(adjustment * 10))

            cursor.execute("""
                UPDATE patterns
                SET success_count = ?, last_used = ?
                WHERE id = ? OR query_hash = ?
            """, (new_count, datetime.utcnow().isoformat(), pattern_id, pattern_id))

            conn.commit()
            return self.get_pattern(pattern_id)
        finally:
            conn.close()

    def get_stats(self, workspace_id: str = None) -> Dict[str, Any]:
        """Get learning statistics."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            if workspace_id:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_queries,
                        AVG(execution_time) as avg_execution_time,
                        MAX(success_count) as max_success
                    FROM patterns WHERE workspace_id = ?
                """, (workspace_id,))
            else:
                cursor.execute("""
                    SELECT
                        COUNT(*) as total_queries,
                        AVG(execution_time) as avg_execution_time,
                        MAX(success_count) as max_success
                    FROM patterns
                """)

            stats_row = cursor.fetchone()

            # Get most successful pattern
            if workspace_id:
                cursor.execute("""
                    SELECT query, success_count FROM patterns
                    WHERE workspace_id = ?
                    ORDER BY success_count DESC LIMIT 1
                """, (workspace_id,))
            else:
                cursor.execute("""
                    SELECT query, success_count FROM patterns
                    ORDER BY success_count DESC LIMIT 1
                """)

            most_successful = cursor.fetchone()

            # Recent activity (last 7 days)
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            if workspace_id:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM patterns WHERE workspace_id = ? AND last_used > ?",
                    (workspace_id, week_ago)
                )
            else:
                cursor.execute("SELECT COUNT(*) as count FROM patterns WHERE last_used > ?", (week_ago,))

            recent = cursor.fetchone()["count"]

            return {
                "total_queries": stats_row["total_queries"] or 0,
                "avg_execution_time": stats_row["avg_execution_time"] or 0.0,
                "most_successful": {
                    "query": most_successful["query"][:100] + "..." if most_successful and len(most_successful["query"]) > 100 else (most_successful["query"] if most_successful else None),
                    "success_count": most_successful["success_count"] if most_successful else 0
                } if most_successful else None,
                "recent_activity": recent
            }
        finally:
            conn.close()

    def export_patterns(self, workspace_id: str = None) -> List[Dict[str, Any]]:
        """Export patterns for backup."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            if workspace_id:
                cursor.execute("SELECT * FROM patterns WHERE workspace_id = ?", (workspace_id,))
            else:
                cursor.execute("SELECT * FROM patterns")

            rows = cursor.fetchall()
            patterns = []
            for row in rows:
                p = self._row_to_dict(row)
                p.pop("embedding", None)  # Don't export embeddings
                patterns.append(p)

            return patterns
        finally:
            conn.close()

    def import_patterns(
        self,
        patterns: List[Dict[str, Any]],
        workspace_id: str,
        overwrite: bool = False
    ) -> Dict[str, int]:
        """Import patterns from backup."""
        imported = 0
        skipped = 0

        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            for pattern in patterns:
                query_hash = self._generate_id(pattern["query"])

                # Check if exists
                cursor.execute("SELECT id FROM patterns WHERE query_hash = ?", (query_hash,))
                exists = cursor.fetchone()

                if exists and not overwrite:
                    skipped += 1
                    continue

                now = datetime.utcnow().isoformat()

                if exists and overwrite:
                    cursor.execute("""
                        UPDATE patterns
                        SET query = ?, workspace_id = ?, success_count = ?,
                            execution_time = ?, result_count = ?, schema_context = ?,
                            last_used = ?
                        WHERE query_hash = ?
                    """, (
                        pattern["query"],
                        workspace_id,
                        pattern.get("success_count", 1),
                        pattern.get("execution_time", 0.0),
                        pattern.get("result_count", 0),
                        pattern.get("schema_context"),
                        now,
                        query_hash
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO patterns (id, query, query_hash, workspace_id,
                                             success_count, execution_time, result_count,
                                             schema_context, created_at, last_used)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        query_hash,
                        pattern["query"],
                        query_hash,
                        workspace_id,
                        pattern.get("success_count", 1),
                        pattern.get("execution_time", 0.0),
                        pattern.get("result_count", 0),
                        pattern.get("schema_context"),
                        pattern.get("created_at", now),
                        now
                    ))

                imported += 1

            conn.commit()
            return {"imported": imported, "skipped": skipped, "total": len(patterns)}
        finally:
            conn.close()
