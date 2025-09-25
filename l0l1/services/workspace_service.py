import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from ..core.config import settings
from ..api.models import Workspace, WorkspaceCreate, WorkspaceUpdate


class WorkspaceService:
    """Service for managing workspaces without authentication."""

    def __init__(self):
        self.workspaces = {}  # In-memory storage for demo
        self._ensure_workspace_directory()

    def _ensure_workspace_directory(self):
        """Ensure workspace data directory exists."""
        Path(settings.workspace_data_dir).mkdir(parents=True, exist_ok=True)

    async def list_workspaces(self, tenant_id: str) -> List[Workspace]:
        """List all workspaces for a tenant."""
        workspaces = [
            workspace for workspace in self.workspaces.values()
            if workspace.tenant_id == tenant_id
        ]
        return workspaces

    async def create_workspace(self, workspace_create: WorkspaceCreate) -> Workspace:
        """Create a new workspace."""
        workspace_id = str(uuid.uuid4())
        now = datetime.utcnow()

        workspace = Workspace(
            id=workspace_id,
            name=workspace_create.name,
            description=workspace_create.description,
            tenant_id=workspace_create.tenant_id,
            created_at=now,
            updated_at=now
        )

        self.workspaces[workspace_id] = workspace

        # Create workspace data directory
        workspace_dir = Path(settings.workspace_data_dir) / workspace_id
        workspace_dir.mkdir(exist_ok=True)

        return workspace

    async def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get workspace by ID."""
        return self.workspaces.get(workspace_id)

    async def update_workspace(
        self,
        workspace_id: str,
        workspace_update: WorkspaceUpdate
    ) -> Optional[Workspace]:
        """Update workspace."""
        workspace = self.workspaces.get(workspace_id)
        if not workspace:
            return None

        update_data = workspace_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workspace, field, value)

        workspace.updated_at = datetime.utcnow()
        return workspace

    async def delete_workspace(self, workspace_id: str) -> bool:
        """Delete workspace."""
        if workspace_id not in self.workspaces:
            return False

        del self.workspaces[workspace_id]

        # Clean up workspace data directory
        workspace_dir = Path(settings.workspace_data_dir) / workspace_id
        if workspace_dir.exists():
            import shutil
            shutil.rmtree(workspace_dir)

        return True

    def get_workspace_data_path(self, workspace_id: str) -> Path:
        """Get the data directory path for a workspace."""
        return Path(settings.workspace_data_dir) / workspace_id