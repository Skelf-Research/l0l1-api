from typing import Optional, List
from pydantic import BaseSettings, Field
import os


class Settings(BaseSettings):
    # Database
    database_url: str = Field(default="sqlite:///./l0l1.db", env="DATABASE_URL")

    # AI Model Configuration
    default_provider: str = Field(default="openai", env="L0L1_AI_PROVIDER")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")

    # Model Settings
    embedding_model: str = Field(default="text-embedding-3-small", env="L0L1_EMBEDDING_MODEL")
    completion_model: str = Field(default="gpt-4o-mini", env="L0L1_COMPLETION_MODEL")

    # Vector Database
    vector_db_path: str = Field(default="./data/vector", env="L0L1_VECTOR_DB_PATH")

    # Knowledge Graph
    knowledge_graph_path: str = Field(default="./data/kg", env="L0L1_KNOWLEDGE_GRAPH_PATH")

    # Background Tasks
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Workspace Settings
    workspace_data_dir: str = Field(default="./workspaces", env="L0L1_WORKSPACE_DIR")

    # PII Detection
    enable_pii_detection: bool = Field(default=True, env="L0L1_ENABLE_PII_DETECTION")
    pii_entities: List[str] = Field(
        default=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "SSN", "CREDIT_CARD", "IP_ADDRESS"],
        env="L0L1_PII_ENTITIES"
    )

    # Continuous Learning
    enable_learning: bool = Field(default=True, env="L0L1_ENABLE_LEARNING")
    learning_threshold: float = Field(default=0.8, env="L0L1_LEARNING_THRESHOLD")

    # API Settings
    api_host: str = Field(default="0.0.0.0", env="L0L1_API_HOST")
    api_port: int = Field(default=8000, env="L0L1_API_PORT")

    # Logging
    log_level: str = Field(default="INFO", env="L0L1_LOG_LEVEL")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()