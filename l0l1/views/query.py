# app/blueprints/query.py
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import Query, Workspace, User
from schemas import QuerySchema
from actors import process_query

blp = Blueprint("query", __name__, description="Query operations")

@blp.route("/workspace/<int:workspace_id>/query")
class QueryResource(MethodView):
    @jwt_required()
    @blp.arguments(QuerySchema)
    @blp.response(201, QuerySchema)
    def post(self, query_data, workspace_id):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        workspace = Workspace.query.get_or_404(workspace_id)
        if workspace.customer_id != user.customer_id:
            abort(403, message="You don't have access to this workspace.")
        query = Query(workspace_id=workspace_id, content=query_data["content"])
        db.session.add(query)
        db.session.commit()
        process_query.send(query.id)
        return query

    @jwt_required()
    @blp.response(200, QuerySchema(many=True))
    def get(self, workspace_id):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        workspace = Workspace.query.get_or_404(workspace_id)
        if workspace.customer_id != user.customer_id:
            abort(403, message="You don't have access to this workspace.")
        return Query.query.filter_by(workspace_id=workspace_id).all()