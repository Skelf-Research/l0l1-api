from marshmallow import Schema, fields

class CustomerSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    email = fields.Email(required=True)

class WorkspaceSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    customer_id = fields.Int(required=True)

class SchemaSchema(Schema):
    id = fields.Int(dump_only=True)
    workspace_id = fields.Int(required=True)
    content = fields.Str(required=True)
    explanation = fields.Str()

class QuerySchema(Schema):
    id = fields.Int(dump_only=True)
    workspace_id = fields.Int(required=True)
    content = fields.Str(required=True)
    explanation = fields.Str()

class InsightSchema(Schema):
    id = fields.Int(dump_only=True)
    workspace_id = fields.Int(required=True)
    user_id = fields.Int(required=True)
    content = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)

class CommentSchema(Schema):
    id = fields.Int(dump_only=True)
    insight_id = fields.Int(required=True)
    user_id = fields.Int(required=True)
    content = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)