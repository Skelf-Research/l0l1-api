# app/blueprints/schema.py
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Schema, Workspace, User
from schemas import SchemaSchema
from actors import process_schema

blp = Blueprint("schema", __name__, description="Schema operations")

@blp.route("/workspace/<int:workspace_id>/schema")
class SchemaResource(MethodView):
    @jwt_required()
    @blp.arguments(SchemaSchema)
    @blp.response(201, SchemaSchema)
    def post(self, schema_data, workspace_id):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        workspace = Workspace.query.get_or_404(workspace_id)
        if workspace.customer_id != user.customer_id:
            abort(403, message="You don't have access to this workspace.")
        schema = Schema(workspace_id=workspace_id, content=schema_data["content"])
        db.session.add(schema)
        db.session.commit()
        process_schema.send(schema.id)
        return schema

    @jwt_required()
    @blp.response(200, SchemaSchema(many=True))
    def get(self, workspace_id):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        workspace = Workspace.query.get_or_404(workspace_id)
        if workspace.customer_id != user.customer_id:
            abort(403, message="You don't have access to this workspace.")
        return Schema.query.filter_by(workspace_id=workspace_id).all()