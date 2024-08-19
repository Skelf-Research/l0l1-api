# app/__init__.py
from flask import Flask
from flask_smorest import Api
from extensions import db
from views.auth import blp as auth_blp
from views.workspace import blp as workspace_blp
from views.schema import blp as schema_blp
from views.query import blp as query_blp
import openai
import dramatiq
from dramatiq.brokers.redis import RedisBroker
import os


def create_app(config_object="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    api = Api(app)

    api.register_blueprint(auth_blp)
    api.register_blueprint(workspace_blp)
    api.register_blueprint(schema_blp)
    api.register_blueprint(query_blp)

    openai.api_key = app.config['OPENAI_API_KEY']

    broker = RedisBroker(url=app.config['DRAMATIQ_BROKER_URL'])
    dramatiq.set_broker(broker)

    # Ensure CogDB root directory exists
    os.makedirs(app.config['COGDB_ROOT_DIR'], exist_ok=True)
    os.makedirs(app.config['WORKSPACE_DATA_DIR'], exist_ok=True)

    return app