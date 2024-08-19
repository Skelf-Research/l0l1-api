from extensions import db
from models import Workspace, Schema, Query

class WorkspaceManager:
    @staticmethod
    def create_workspace(name, customer_id):
        workspace = Workspace(name=name, customer_id=customer_id)
        db.session.add(workspace)
        db.session.commit()
        return workspace

    @staticmethod
    def delete_workspace(workspace_id):
        workspace = Workspace.query.get(workspace_id)
        if workspace:
            workspace.delete()
        else:
            raise ValueError(f"Workspace with id {workspace_id} not found")

    @staticmethod
    def get_workspace_summary(workspace_id):
        workspace = Workspace.query.get(workspace_id)
        if workspace:
            return {
                'id': workspace.id,
                'name': workspace.name,
                'customer_id': workspace.customer_id,
                'schema_count': Schema.query.filter_by(workspace_id=workspace_id).count(),
                'query_count': Query.query.filter_by(workspace_id=workspace_id).count(),
            }
        else:
            raise ValueError(f"Workspace with id {workspace_id} not found")