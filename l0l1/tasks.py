# app/tasks.py
import dramatiq
from dramatiq.brokers.redis import RedisBroker
import sqlparse

redis_broker = RedisBroker(host="localhost", port=6379)
dramatiq.set_broker(redis_broker)

@dramatiq.actor
def process_schema(schema_id):
    from .models import Schema, db
    schema = Schema.query.get(schema_id)
    if schema:
        schema.generate_explanation_and_embedding()
        workspace = schema.workspace
        vector_db = workspace.get_vector_db()
        vector_db.add(f"schema_{schema.id}", schema.embedding)
        workspace.save_vector_db()
        
        kg = workspace.get_knowledge_graph()
        parsed = sqlparse.parse(schema.content)
        for statement in parsed:
            if statement.get_type() == 'CREATE':
                table_name = statement.token_next_by(i=sqlparse.tokens.Keyword, m=['TABLE', 'VIEW']).parent.get_name()
                kg.add_relation('schema', 'has_table', table_name)
                for token in statement.tokens:
                    if isinstance(token, sqlparse.sql.Identifier):
                        column_name = token.get_name()
                        kg.add_relation(table_name, 'has_column', column_name)
        
        db.session.commit()

@dramatiq.actor
def process_query(query_id):
    from .models import Query, db
    query = Query.query.get(query_id)
    if query:
        query.generate_explanation_and_embedding()
        workspace = query.workspace
        vector_db = workspace.get_vector_db()
        vector_db.add(f"query_{query.id}", query.embedding)
        workspace.save_vector_db()
        
        kg = workspace.get_knowledge_graph()
        parsed = sqlparse.parse(query.content)[0]
        tables = set()
        columns = set()
        
        for token in parsed.flatten():
            if token.ttype is sqlparse.tokens.Name:
                if token.is_group:
                    if token.get_parent_name():
                        tables.add(token.get_parent_name())
                    columns.add(token.get_name())
                else:
                    tables.add(token.value)
        
        for table in tables:
            kg.add_relation('query', 'uses_table', table)
        for column in columns:
            kg.add_relation('query', 'uses_column', column)
        
        db.session.commit()