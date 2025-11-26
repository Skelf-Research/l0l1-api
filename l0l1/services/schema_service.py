"""Schema management service for versioning and schema operations."""

import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class SchemaChangeType(str, Enum):
    """Types of schema changes."""
    CREATE_TABLE = "create_table"
    DROP_TABLE = "drop_table"
    ADD_COLUMN = "add_column"
    DROP_COLUMN = "drop_column"
    MODIFY_COLUMN = "modify_column"
    ADD_INDEX = "add_index"
    DROP_INDEX = "drop_index"
    ADD_CONSTRAINT = "add_constraint"
    DROP_CONSTRAINT = "drop_constraint"
    RENAME = "rename"


class SchemaVersion:
    """Represents a schema version."""

    def __init__(
        self,
        id: str,
        version: str,
        workspace_id: str,
        schema_data: Dict[str, Any],
        description: str = "",
        created_at: Optional[datetime] = None,
        created_by: Optional[str] = None,
        parent_version: Optional[str] = None
    ):
        self.id = id
        self.version = version
        self.workspace_id = workspace_id
        self.schema_data = schema_data
        self.description = description
        self.created_at = created_at or datetime.utcnow()
        self.created_by = created_by
        self.parent_version = parent_version
        self.is_active = False
        self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """Calculate schema checksum for change detection."""
        schema_str = json.dumps(self.schema_data, sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "version": self.version,
            "workspace_id": self.workspace_id,
            "schema_data": self.schema_data,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
            "parent_version": self.parent_version,
            "is_active": self.is_active,
            "checksum": self.checksum
        }


class SchemaChange:
    """Represents a schema change/migration."""

    def __init__(
        self,
        id: str,
        change_type: SchemaChangeType,
        target: str,
        details: Dict[str, Any],
        sql_up: str,
        sql_down: str,
        version_from: Optional[str] = None,
        version_to: Optional[str] = None
    ):
        self.id = id
        self.change_type = change_type
        self.target = target
        self.details = details
        self.sql_up = sql_up
        self.sql_down = sql_down
        self.version_from = version_from
        self.version_to = version_to
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "change_type": self.change_type.value,
            "target": self.target,
            "details": self.details,
            "sql_up": self.sql_up,
            "sql_down": self.sql_down,
            "version_from": self.version_from,
            "version_to": self.version_to,
            "created_at": self.created_at.isoformat()
        }


class SchemaService:
    """Service for managing database schemas and versions."""

    def __init__(self):
        self.versions: Dict[str, SchemaVersion] = {}
        self.changes: Dict[str, SchemaChange] = {}
        self.active_versions: Dict[str, str] = {}  # workspace_id -> version_id

    def _generate_id(self, prefix: str = "sv") -> str:
        """Generate a unique ID."""
        timestamp = datetime.utcnow().isoformat()
        return f"{prefix}_{hashlib.md5(timestamp.encode()).hexdigest()[:10]}"

    def _generate_version_number(self, workspace_id: str) -> str:
        """Generate next version number for a workspace."""
        workspace_versions = [
            v for v in self.versions.values()
            if v.workspace_id == workspace_id
        ]
        if not workspace_versions:
            return "1.0.0"

        # Find latest version and increment
        latest = max(workspace_versions, key=lambda v: v.created_at)
        parts = latest.version.split(".")
        parts[-1] = str(int(parts[-1]) + 1)
        return ".".join(parts)

    async def create_schema_version(
        self,
        workspace_id: str,
        schema_data: Dict[str, Any],
        description: str = "",
        created_by: Optional[str] = None,
        set_active: bool = True
    ) -> SchemaVersion:
        """Create a new schema version."""
        version_id = self._generate_id("sv")
        version_number = self._generate_version_number(workspace_id)

        # Get parent version
        parent_version = self.active_versions.get(workspace_id)

        version = SchemaVersion(
            id=version_id,
            version=version_number,
            workspace_id=workspace_id,
            schema_data=schema_data,
            description=description,
            created_by=created_by,
            parent_version=parent_version
        )

        self.versions[version_id] = version

        if set_active:
            await self.set_active_version(workspace_id, version_id)

        return version

    async def get_schema_version(self, version_id: str) -> Optional[SchemaVersion]:
        """Get a schema version by ID."""
        return self.versions.get(version_id)

    async def get_active_version(self, workspace_id: str) -> Optional[SchemaVersion]:
        """Get the active schema version for a workspace."""
        version_id = self.active_versions.get(workspace_id)
        if version_id:
            return self.versions.get(version_id)
        return None

    async def set_active_version(self, workspace_id: str, version_id: str) -> bool:
        """Set the active schema version for a workspace."""
        if version_id not in self.versions:
            return False

        version = self.versions[version_id]
        if version.workspace_id != workspace_id:
            return False

        # Deactivate previous version
        prev_version_id = self.active_versions.get(workspace_id)
        if prev_version_id and prev_version_id in self.versions:
            self.versions[prev_version_id].is_active = False

        # Activate new version
        version.is_active = True
        self.active_versions[workspace_id] = version_id
        return True

    async def list_versions(
        self,
        workspace_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[SchemaVersion]:
        """List schema versions for a workspace."""
        versions = [
            v for v in self.versions.values()
            if v.workspace_id == workspace_id
        ]
        versions.sort(key=lambda v: v.created_at, reverse=True)
        return versions[offset:offset + limit]

    async def compare_versions(
        self,
        version_id_1: str,
        version_id_2: str
    ) -> Dict[str, Any]:
        """Compare two schema versions and return differences."""
        v1 = self.versions.get(version_id_1)
        v2 = self.versions.get(version_id_2)

        if not v1 or not v2:
            raise ValueError("One or both versions not found")

        differences = {
            "version_1": {"id": v1.id, "version": v1.version},
            "version_2": {"id": v2.id, "version": v2.version},
            "tables_added": [],
            "tables_removed": [],
            "tables_modified": [],
            "columns_added": [],
            "columns_removed": [],
            "columns_modified": [],
            "indexes_added": [],
            "indexes_removed": []
        }

        # Get tables from both versions
        tables_1 = {t["name"]: t for t in v1.schema_data.get("tables", [])}
        tables_2 = {t["name"]: t for t in v2.schema_data.get("tables", [])}

        # Find added/removed tables
        differences["tables_added"] = [
            t for name, t in tables_2.items() if name not in tables_1
        ]
        differences["tables_removed"] = [
            t for name, t in tables_1.items() if name not in tables_2
        ]

        # Find modified tables
        for name in set(tables_1.keys()) & set(tables_2.keys()):
            t1, t2 = tables_1[name], tables_2[name]

            # Compare columns
            cols_1 = {c["name"]: c for c in t1.get("columns", [])}
            cols_2 = {c["name"]: c for c in t2.get("columns", [])}

            for col_name, col in cols_2.items():
                if col_name not in cols_1:
                    differences["columns_added"].append({
                        "table": name,
                        "column": col
                    })
                elif cols_1[col_name] != col:
                    differences["columns_modified"].append({
                        "table": name,
                        "old": cols_1[col_name],
                        "new": col
                    })

            for col_name, col in cols_1.items():
                if col_name not in cols_2:
                    differences["columns_removed"].append({
                        "table": name,
                        "column": col
                    })

        return differences

    async def generate_migration(
        self,
        from_version_id: str,
        to_version_id: str
    ) -> List[SchemaChange]:
        """Generate migration SQL between two versions."""
        diff = await self.compare_versions(from_version_id, to_version_id)
        migrations = []

        # Generate CREATE TABLE statements
        for table in diff["tables_added"]:
            change_id = self._generate_id("sc")
            columns_sql = ", ".join([
                f"{c['name']} {c['type']}" +
                (" NOT NULL" if not c.get('nullable', True) else "") +
                (" PRIMARY KEY" if c.get('primary_key') else "")
                for c in table.get("columns", [])
            ])

            migrations.append(SchemaChange(
                id=change_id,
                change_type=SchemaChangeType.CREATE_TABLE,
                target=table["name"],
                details=table,
                sql_up=f"CREATE TABLE {table['name']} ({columns_sql});",
                sql_down=f"DROP TABLE {table['name']};",
                version_from=from_version_id,
                version_to=to_version_id
            ))

        # Generate DROP TABLE statements
        for table in diff["tables_removed"]:
            change_id = self._generate_id("sc")
            migrations.append(SchemaChange(
                id=change_id,
                change_type=SchemaChangeType.DROP_TABLE,
                target=table["name"],
                details=table,
                sql_up=f"DROP TABLE {table['name']};",
                sql_down="-- Restore table manually",
                version_from=from_version_id,
                version_to=to_version_id
            ))

        # Generate ADD COLUMN statements
        for col_info in diff["columns_added"]:
            change_id = self._generate_id("sc")
            col = col_info["column"]
            col_sql = f"{col['name']} {col['type']}"
            if not col.get('nullable', True):
                col_sql += " NOT NULL"

            migrations.append(SchemaChange(
                id=change_id,
                change_type=SchemaChangeType.ADD_COLUMN,
                target=f"{col_info['table']}.{col['name']}",
                details=col_info,
                sql_up=f"ALTER TABLE {col_info['table']} ADD COLUMN {col_sql};",
                sql_down=f"ALTER TABLE {col_info['table']} DROP COLUMN {col['name']};",
                version_from=from_version_id,
                version_to=to_version_id
            ))

        # Generate DROP COLUMN statements
        for col_info in diff["columns_removed"]:
            change_id = self._generate_id("sc")
            col = col_info["column"]

            migrations.append(SchemaChange(
                id=change_id,
                change_type=SchemaChangeType.DROP_COLUMN,
                target=f"{col_info['table']}.{col['name']}",
                details=col_info,
                sql_up=f"ALTER TABLE {col_info['table']} DROP COLUMN {col['name']};",
                sql_down="-- Restore column manually",
                version_from=from_version_id,
                version_to=to_version_id
            ))

        # Store migrations
        for migration in migrations:
            self.changes[migration.id] = migration

        return migrations

    async def validate_schema(self, schema_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a schema definition."""
        errors = []
        warnings = []

        tables = schema_data.get("tables", [])

        if not tables:
            warnings.append("Schema has no tables defined")

        table_names = set()
        for table in tables:
            # Check for duplicate table names
            if table["name"] in table_names:
                errors.append(f"Duplicate table name: {table['name']}")
            table_names.add(table["name"])

            # Check for primary key
            columns = table.get("columns", [])
            has_pk = any(c.get("primary_key") for c in columns)
            if not has_pk:
                warnings.append(f"Table '{table['name']}' has no primary key")

            # Check for column definitions
            if not columns:
                errors.append(f"Table '{table['name']}' has no columns")

            # Check column names
            col_names = set()
            for col in columns:
                if col["name"] in col_names:
                    errors.append(f"Duplicate column name in '{table['name']}': {col['name']}")
                col_names.add(col["name"])

            # Validate foreign keys
            for fk in table.get("foreign_keys", []):
                ref_table = fk.get("references", {}).get("table")
                if ref_table and ref_table not in table_names and ref_table != table["name"]:
                    # Table might be defined later, just warn
                    warnings.append(
                        f"Foreign key in '{table['name']}' references unknown table '{ref_table}'"
                    )

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "table_count": len(tables),
            "total_columns": sum(len(t.get("columns", [])) for t in tables)
        }

    async def export_schema(
        self,
        version_id: str,
        format: str = "json"
    ) -> str:
        """Export schema in various formats."""
        version = self.versions.get(version_id)
        if not version:
            raise ValueError(f"Version not found: {version_id}")

        if format == "json":
            return json.dumps(version.schema_data, indent=2)

        elif format == "sql":
            # Generate CREATE TABLE statements
            sql_lines = []
            sql_lines.append(f"-- Schema Version: {version.version}")
            sql_lines.append(f"-- Generated: {datetime.utcnow().isoformat()}")
            sql_lines.append("")

            for table in version.schema_data.get("tables", []):
                sql_lines.append(f"CREATE TABLE {table['name']} (")

                col_defs = []
                for col in table.get("columns", []):
                    col_def = f"  {col['name']} {col['type']}"
                    if not col.get('nullable', True):
                        col_def += " NOT NULL"
                    if col.get('primary_key'):
                        col_def += " PRIMARY KEY"
                    if col.get('unique'):
                        col_def += " UNIQUE"
                    if col.get('default') is not None:
                        col_def += f" DEFAULT {col['default']}"
                    col_defs.append(col_def)

                sql_lines.append(",\n".join(col_defs))
                sql_lines.append(");")
                sql_lines.append("")

            return "\n".join(sql_lines)

        else:
            raise ValueError(f"Unsupported format: {format}")

    async def import_schema_from_sql(
        self,
        sql: str,
        workspace_id: str
    ) -> Dict[str, Any]:
        """Parse SQL and create schema (basic implementation)."""
        import re

        tables = []
        # Basic CREATE TABLE parser
        create_pattern = r"CREATE\s+TABLE\s+(\w+)\s*\((.*?)\);"
        matches = re.findall(create_pattern, sql, re.IGNORECASE | re.DOTALL)

        for table_name, columns_str in matches:
            columns = []
            for col_def in columns_str.split(","):
                col_def = col_def.strip()
                if not col_def:
                    continue

                parts = col_def.split()
                if len(parts) >= 2:
                    columns.append({
                        "name": parts[0],
                        "type": parts[1],
                        "nullable": "NOT NULL" not in col_def.upper(),
                        "primary_key": "PRIMARY KEY" in col_def.upper()
                    })

            tables.append({
                "name": table_name,
                "schema": "public",
                "columns": columns,
                "indexes": [],
                "foreign_keys": []
            })

        schema_data = {"tables": tables}

        return {
            "schema_data": schema_data,
            "tables_parsed": len(tables),
            "total_columns": sum(len(t["columns"]) for t in tables)
        }
