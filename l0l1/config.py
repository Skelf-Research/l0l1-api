# app/config.py
import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///l0l1.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_TITLE = 'l0l1 API'
    API_VERSION = 'v1'
    OPENAPI_VERSION = '3.0.2'
    OPENAPI_JSON_PATH = 'api-spec.json'
    OPENAPI_URL_PREFIX = '/'
    OPENAPI_REDOC_PATH = '/redoc'
    OPENAPI_SWAGGER_UI_PATH = '/swagger-ui'
    OPENAPI_SWAGGER_UI_URL = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    DRAMATIQ_BROKER_URL = 'redis://localhost:6379/0'
    COGDB_ROOT_DIR = os.getenv('COGDB_ROOT_DIR', 'cogdb_data')