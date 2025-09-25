import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class UISession:
    """Manages UI session state for notebook-like interfaces."""

    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str = "default"
    tenant_id: str = "default"
    created_at: datetime = field(default_factory=datetime.utcnow)
    cells: List[Dict[str, Any]] = field(default_factory=list)
    execution_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    schema_context: Optional[str] = None

    def add_cell(self, cell_type: str = "sql", source: str = "") -> str:
        """Add a new cell to the session."""
        cell_id = str(uuid.uuid4())
        cell = {
            "id": cell_id,
            "cell_type": cell_type,
            "source": source,
            "outputs": [],
            "execution_count": None,
            "metadata": {
                "created_at": datetime.utcnow().isoformat()
            }
        }

        if cell_type == "sql":
            cell["metadata"]["l0l1"] = {
                "options": {
                    "validate": True,
                    "explain": False,
                    "check_pii": True,
                    "complete": False,
                    "anonymize": False
                }
            }

        self.cells.append(cell)
        return cell_id

    def update_cell(self, cell_id: str, source: str, options: Optional[Dict[str, Any]] = None) -> bool:
        """Update cell content and options."""
        for cell in self.cells:
            if cell["id"] == cell_id:
                cell["source"] = source
                cell["metadata"]["updated_at"] = datetime.utcnow().isoformat()

                if options and cell["cell_type"] == "sql":
                    cell["metadata"]["l0l1"]["options"].update(options)

                # Clear previous outputs when source changes
                cell["outputs"] = []
                cell["execution_count"] = None
                return True

        return False

    def execute_cell(self, cell_id: str, outputs: List[Dict[str, Any]]) -> bool:
        """Record cell execution results."""
        for cell in self.cells:
            if cell["id"] == cell_id:
                self.execution_count += 1
                cell["execution_count"] = self.execution_count
                cell["outputs"] = outputs
                cell["metadata"]["executed_at"] = datetime.utcnow().isoformat()
                return True

        return False

    def delete_cell(self, cell_id: str) -> bool:
        """Delete a cell from the session."""
        original_length = len(self.cells)
        self.cells = [cell for cell in self.cells if cell["id"] != cell_id]
        return len(self.cells) < original_length

    def move_cell(self, cell_id: str, new_index: int) -> bool:
        """Move a cell to a new position."""
        cell_to_move = None
        old_index = -1

        for i, cell in enumerate(self.cells):
            if cell["id"] == cell_id:
                cell_to_move = cell
                old_index = i
                break

        if cell_to_move is None or new_index < 0 or new_index >= len(self.cells):
            return False

        # Remove from old position and insert at new position
        self.cells.pop(old_index)
        self.cells.insert(new_index, cell_to_move)
        return True

    def clear_all_outputs(self):
        """Clear outputs from all cells."""
        for cell in self.cells:
            cell["outputs"] = []
            cell["execution_count"] = None

    def get_cell(self, cell_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific cell by ID."""
        for cell in self.cells:
            if cell["id"] == cell_id:
                return cell
        return None

    def get_cells_by_type(self, cell_type: str) -> List[Dict[str, Any]]:
        """Get all cells of a specific type."""
        return [cell for cell in self.cells if cell["cell_type"] == cell_type]

    def export_notebook(self) -> Dict[str, Any]:
        """Export session as a notebook format."""
        return {
            "metadata": {
                "l0l1": {
                    "session_id": self.session_id,
                    "workspace_id": self.workspace_id,
                    "tenant_id": self.tenant_id,
                    "created_at": self.created_at.isoformat(),
                    "execution_count": self.execution_count,
                    "schema_context": self.schema_context,
                    **self.metadata
                }
            },
            "cells": self.cells.copy()
        }

    def import_notebook(self, notebook_data: Dict[str, Any]) -> bool:
        """Import notebook data into session."""
        try:
            if "cells" in notebook_data:
                self.cells = notebook_data["cells"]

            if "metadata" in notebook_data and "l0l1" in notebook_data["metadata"]:
                l0l1_meta = notebook_data["metadata"]["l0l1"]
                self.workspace_id = l0l1_meta.get("workspace_id", self.workspace_id)
                self.tenant_id = l0l1_meta.get("tenant_id", self.tenant_id)
                self.execution_count = l0l1_meta.get("execution_count", 0)
                self.schema_context = l0l1_meta.get("schema_context")

                # Update metadata but preserve session_id and created_at
                preserved = {
                    "session_id": self.session_id,
                    "created_at": self.created_at.isoformat()
                }
                self.metadata = {**l0l1_meta, **preserved}

            return True

        except Exception:
            return False

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        total_cells = len(self.cells)
        sql_cells = len([c for c in self.cells if c["cell_type"] == "sql"])
        executed_cells = len([c for c in self.cells if c["execution_count"] is not None])

        return {
            "session_id": self.session_id,
            "workspace_id": self.workspace_id,
            "tenant_id": self.tenant_id,
            "created_at": self.created_at.isoformat(),
            "total_cells": total_cells,
            "sql_cells": sql_cells,
            "executed_cells": executed_cells,
            "execution_count": self.execution_count,
            "has_schema_context": self.schema_context is not None
        }