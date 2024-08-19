# app/blueprints/workspace.py
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import db, Workspace, User, Schema, Query, Insight
from schemas import WorkspaceSchema, SchemaSchema, QuerySchema, InsightSchema
from modules.openai_service import OpenAIService
from marshmallow import Schema, fields

blp = Blueprint("workspace", __name__, description="Workspace operations")

@blp.route("/workspace")
class WorkspaceResource(MethodView):
    @jwt_required()
    @blp.arguments(WorkspaceSchema)
    @blp.response(201, WorkspaceSchema)
    def post(self, workspace_data):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        workspace = Workspace(name=workspace_data["name"], customer_id=user.customer_id)
        db.session.add(workspace)
        db.session.commit()
        return workspace

    @jwt_required()
    @blp.response(200, WorkspaceSchema(many=True))
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        return Workspace.query.filter_by(customer_id=user.customer_id).all()

@blp.route("/workspace/<int:workspace_id>")
class WorkspaceDetailResource(MethodView):
    @jwt_required()
    @blp.response(200, WorkspaceSchema)
    def get(self, workspace_id):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        workspace = Workspace.query.get_or_404(workspace_id)
        if workspace.customer_id != user.customer_id:
            abort(403, message="You don't have access to this workspace.")
        return workspace

    @jwt_required()
    @blp.response(204)
    def delete(self, workspace_id):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        workspace = Workspace.query.get_or_404(workspace_id)
        if workspace.customer_id != user.customer_id:
            abort(403, message="You don't have access to this workspace.")
        db.session.delete(workspace)
        db.session.commit()
        return "", 204

@blp.route("/workspace/<int:workspace_id>/schema")
class WorkspaceSchemaResource(MethodView):
    @jwt_required()
    @blp.response(200, SchemaSchema(many=True))
    def get(self, workspace_id):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        workspace = Workspace.query.get_or_404(workspace_id)
        if workspace.customer_id != user.customer_id:
            abort(403, message="You don't have access to this workspace.")
        return Schema.query.filter_by(workspace_id=workspace_id).all()

@blp.route("/workspace/<int:workspace_id>/query")
class WorkspaceQueryResource(MethodView):
    @jwt_required()
    @blp.response(200, QuerySchema(many=True))
    def get(self, workspace_id):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        workspace = Workspace.query.get_or_404(workspace_id)
        if workspace.customer_id != user.customer_id:
            abort(403, message="You don't have access to this workspace.")
        return Query.query.filter_by(workspace_id=workspace_id).all()

@blp.route("/workspace/<int:workspace_id>/insight")
class WorkspaceInsightResource(MethodView):
    @jwt_required()
    @blp.arguments(InsightSchema)
    @blp.response(201, InsightSchema)
    def post(self, insight_data, workspace_id):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        workspace = Workspace.query.get_or_404(workspace_id)
        if workspace.customer_id != user.customer_id:
            abort(403, message="You don't have access to this workspace.")
        insight = Insight(workspace_id=workspace_id, user_id=user_id, content=insight_data["content"])
        db.session.add(insight)
        db.session.commit()
        return insight

    @jwt_required()
    @blp.response(200, InsightSchema(many=True))
    def get(self, workspace_id):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        workspace = Workspace.query.get_or_404(workspace_id)
        if workspace.customer_id != user.customer_id:
            abort(403, message="You don't have access to this workspace.")
        return Insight.query.filter_by(workspace_id=workspace_id).all()

class QueryInputSchema(Schema):
    query = fields.Str(required=True)

class PartialQuerySchema(Schema):
    partial_query = fields.Str(required=True)

class QueryOutputSchema(Schema):
    query = fields.Str()

class ExplanationSchema(Schema):
    explanation = fields.Str()

class GraphDataSchema(Schema):
    graph_data = fields.List(fields.List(fields.Str()))

@blp.route("/workspace/<int:workspace_id>/similar_queries")
class WorkspaceSimilarQueriesResource(MethodView):
    @jwt_required()
    @blp.arguments(QueryInputSchema)
    @blp.response(200, QuerySchema(many=True))
    def post(self, query_data, workspace_id):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        workspace = Workspace.query.get_or_404(workspace_id)
        if workspace.customer_id != user.customer_id:
            abort(403, message="You don't have access to this workspace.")
        
        vector_db = workspace.get_vector_db()
        query_embedding = OpenAIService.generate_embedding(query_data["query"])
        similar_query_ids = vector_db.search(query_embedding, k=5)
        similar_queries = Query.query.filter(Query.id.in_(similar_query_ids)).all()
        return similar_queries

@blp.route("/workspace/<int:workspace_id>/autocomplete")
class WorkspaceAutocompleteResource(MethodView):
    @jwt_required()
    @blp.arguments(PartialQuerySchema)
    @blp.response(200, QueryOutputSchema)
    def post(self, query_data, workspace_id):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        workspace = Workspace.query.get_or_404(workspace_id)
        if workspace.customer_id != user.customer_id:
            abort(403, message="You don't have access to this workspace.")
        
        kg = workspace.get_knowledge_graph()
        suggested_tables = kg.get_relations('query', 'uses_table')
        completion = OpenAIService.complete_query(query_data["partial_query"], suggested_tables)
        return {"query": completion}

@blp.route("/workspace/<int:workspace_id>/explain_query")
class WorkspaceExplainQueryResource(MethodView):
    @jwt_required()
    @blp.arguments(QueryInputSchema)
    @blp.response(200, ExplanationSchema)
    def post(self, query_data, workspace_id):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        workspace = Workspace.query.get_or_404(workspace_id)
        if workspace.customer_id != user.customer_id:
            abort(403, message="You don't have access to this workspace.")
        
        explanation = OpenAIService.explain_query(query_data["query"])
        return {"explanation": explanation}

@blp.route("/workspace/<int:workspace_id>/visualize")
class WorkspaceVisualizationResource(MethodView):
    @jwt_required()
    @blp.response(200, GraphDataSchema)
    def get(self, workspace_id):
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        workspace = Workspace.query.get_or_404(workspace_id)
        if workspace.customer_id != user.customer_id:
            abort(403, message="You don't have access to this workspace.")
        
        kg = workspace.get_knowledge_graph()
        graph_data = kg.get_all_relations()
        return {"graph_data": graph_data}