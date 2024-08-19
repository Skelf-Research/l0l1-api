from marshmallow import Schema, fields

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    customer_name = fields.Str(required=True, load_only=True)

class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)

class CustomerSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)

class WorkspaceSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    customer_id = fields.Int(dump_only=True)

class SchemaSchema(Schema):
    id = fields.Int(dump_only=True)
    workspace_id = fields.Int(required=True)
    content = fields.Str(required=True)
    explanation = fields.Str(dump_only=True)

class QuerySchema(Schema):
    id = fields.Int(dump_only=True)
    workspace_id = fields.Int(required=True)
    content = fields.Str(required=True)
    explanation = fields.Str(dump_only=True)

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