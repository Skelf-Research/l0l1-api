# app/models.py
from flask_sqlalchemy import SQLAlchemy
from .vector_db import VectorDB
from .knowledge_graph import KnowledgeGraph

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class Workspace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    customer = db.relationship('Customer', backref=db.backref('workspaces', lazy=True))
    vector_db_path = db.Column(db.String(255), nullable=True)
    cogdb_path = db.Column(db.String(255), nullable=True)

    def get_vector_db(self):
        if not hasattr(self, '_vector_db'):
            self._vector_db = VectorDB(ndim=768)
            if self.vector_db_path and os.path.exists(self.vector_db_path):
                self._vector_db.load(self.vector_db_path)
        return self._vector_db

    def save_vector_db(self):
        if hasattr(self, '_vector_db'):
            if not self.vector_db_path:
                self.vector_db_path = os.path.join(current_app.config['WORKSPACE_DATA_DIR'], f"vector_db_{self.id}.usearch")
            self._vector_db.save(self.vector_db_path)
            db.session.commit()

    def get_knowledge_graph(self):
        if not hasattr(self, '_knowledge_graph'):
            if not self.cogdb_path:
                self.cogdb_path = os.path.join(current_app.config['WORKSPACE_DATA_DIR'], f"cogdb_{self.id}")
                db.session.commit()
            self._knowledge_graph = KnowledgeGraph(self.cogdb_path)
        return self._knowledge_graph

    def delete(self):
        # Clean up associated files
        if self.vector_db_path and os.path.exists(self.vector_db_path):
            os.remove(self.vector_db_path)
        if self.cogdb_path and os.path.exists(self.cogdb_path):
            import shutil
            shutil.rmtree(self.cogdb_path)
        db.session.delete(self)
        db.session.commit()

class Schema(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)
    embedding = db.Column(db.PickleType, nullable=True)
    workspace = db.relationship('Workspace', backref=db.backref('schemas', lazy=True))

    def generate_explanation_and_embedding(self):
        from .openai_service import OpenAIService
        self.explanation = OpenAIService.explain_schema(self.content)
        self.embedding = OpenAIService.generate_embedding(self.content)
        db.session.commit()

class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)
    embedding = db.Column(db.PickleType, nullable=True)
    workspace = db.relationship('Workspace', backref=db.backref('queries', lazy=True))

    def generate_explanation_and_embedding(self):
        from .openai_service import OpenAIService
        self.explanation = OpenAIService.explain_query(self.content)
        self.embedding = OpenAIService.generate_embedding(self.content)
        db.session.commit()

class Insight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspace.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    workspace = db.relationship('Workspace', backref=db.backref('insights', lazy=True))
    user = db.relationship('User', backref=db.backref('insights', lazy=True))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    insight_id = db.Column(db.Integer, db.ForeignKey('insight.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    insight = db.relationship('Insight', backref=db.backref('comments', lazy=True))
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
