from flask.views import MethodView
from flask_smorest import Blueprint, abort
from .models import db, Customer, Workspace, Schema, Query
from .schemas import CustomerSchema, WorkspaceSchema, SchemaSchema, QuerySchema
from flask_jwt_extended import jwt_required

blp = Blueprint("l0l1", __name__, description="l0l1 API")

@blp.route("/customer")
class CustomerResource(MethodView):
    @blp.arguments(CustomerSchema)
    @blp.response(201, CustomerSchema)
    def post(self, customer_data):
        customer = Customer(**customer_data)
        db.session.add(customer)
        db.session.commit()
        return customer

    @blp.response(200, CustomerSchema(many=True))
    def get(self):
        return Customer.query.all()

@blp.route("/workspace")
class WorkspaceResource(MethodView):
    @blp.arguments(WorkspaceSchema)
    @blp.response(201, WorkspaceSchema)
    def post(self, workspace_data):
        workspace = Workspace(**workspace_data)
        db.session.add(workspace)
        db.session.commit()
        return workspace

    @blp.response(200, WorkspaceSchema(many=True))
    def get(self):
        return Workspace.query.all()

# Add similar endpoints for Schema and Query resources

from .tasks import process_schema, process_query

@blp.route("/schema")
class SchemaResource(MethodView):
    @blp.arguments(SchemaSchema)
    @blp.response(201, SchemaSchema)
    def post(self, schema_data):
        schema = Schema(**schema_data)
        db.session.add(schema)
        db.session.commit()
        process_schema.send(schema.id)
        return schema

@blp.route("/query")
class QueryResource(MethodView):
    @blp.arguments(QuerySchema)
    @blp.response(201, QuerySchema)
    def post(self, query_data):
        query = Query(**query_data)
        db.session.add(query)
        db.session.commit()
        process_query.send(query.id)
        return query
    
@blp.route("/workspace/<int:workspace_id>/visualize")
class WorkspaceVisualizationResource(MethodView):
    def get(self, workspace_id):
        workspace = Workspace.query.get_or_404(workspace_id)
        kg = workspace.get_knowledge_graph()
        schemas = Schema.query.filter_by(workspace_id=workspace_id).all()
        queries = Query.query.filter_by(workspace_id=workspace_id).all()
        
        graph_data = kg.get_all_relations()
        
        return render_template('workspace_visualization.html',
                               workspace=workspace,
                               schemas=schemas,
                               queries=queries,
                               graph_data=graph_data)
    

@blp.route("/workspace/<int:workspace_id>/insight")
class InsightResource(MethodView):
    @jwt_required()
    @blp.arguments(InsightSchema)
    @blp.response(201, InsightSchema)
    def post(self, insight_data, workspace_id):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if not user:
            abort(403, message="Unauthorized")
        workspace = Workspace.query.get(workspace_id)
        if not workspace or workspace.customer_id != user.customer_id:
            abort(404, message="Workspace not found")
        insight = Insight(workspace_id=workspace_id, user_id=user.id, **insight_data)
        db.session.add(insight)
        db.session.commit()
        return insight

    @jwt_required()
    @blp.response(200, InsightSchema(many=True))
    def get(self, workspace_id):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if not user:
            abort(403, message="Unauthorized")
        workspace = Workspace.query.get(workspace_id)
        if not workspace or workspace.customer_id != user.customer_id:
            abort(404, message="Workspace not found")
        return Insight.query.filter_by(workspace_id=workspace_id).all()

@blp.route("/insight/<int:insight_id>/comment")
class CommentResource(MethodView):
    @jwt_required()
    @blp.arguments(CommentSchema)
    @blp.response(201, CommentSchema)
    def post(self, comment_data, insight_id):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if not user:
            abort(403, message="Unauthorized")
        insight = Insight.query.get(insight_id)
        if not insight or insight.workspace.customer_id != user.customer_id:
            abort(404, message="Insight not found")
        comment = Comment(insight_id=insight_id, user_id=user.id, **comment_data)
        db.session.add(comment)
        db.session.commit()
        return comment

    @jwt_required()
    @blp.response(200, CommentSchema(many=True))
    def get(self, insight_id):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if not user:
            abort(403, message="Unauthorized")
        insight = Insight.query.get(insight_id)
        if not insight or insight.workspace.customer_id != user.customer_id:
            abort(404, message="Insight not found")
        return Comment.query.filter_by(insight_id=insight_id).all()