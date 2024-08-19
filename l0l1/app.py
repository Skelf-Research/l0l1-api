# app/__init__.py
from flask import Flask
from flask_smorest import Api
from extensions import db
from views.api import blp
import openai
import dramatiq
from dramatiq.brokers.redis import RedisBroker
import os

def create_app(config_object="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    api = Api(app)

    api.register_blueprint(blp)

    openai.api_key = app.config['OPENAI_API_KEY']

    broker = RedisBroker(url=app.config['DRAMATIQ_BROKER_URL'])
    dramatiq.set_broker(broker)

    # Ensure CogDB root directory exists
    os.makedirs(app.config['COGDB_ROOT_DIR'], exist_ok=True)
    os.makedirs(app.config['WORKSPACE_DATA_DIR'], exist_ok=True)

    return app