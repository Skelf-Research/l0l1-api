from typing import Optional
from ..core.config import settings
from .base import BaseModel
from .providers import ModelProvider


class ModelFactory:
    """Factory for creating model instances."""

    _instance: Optional[BaseModel] = None

    @classmethod
    def create_model(
        cls,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs
    ) -> BaseModel:
        """Create a model instance."""
        provider = provider or settings.default_provider

        if provider == "openai":
            api_key = api_key or settings.openai_api_key
            kwargs.update({
                "embedding_model": settings.embedding_model,
                "completion_model": settings.completion_model
            })
        elif provider == "anthropic":
            api_key = api_key or settings.anthropic_api_key
            kwargs.update({
                "completion_model": settings.completion_model
            })

        return ModelProvider.create(provider, api_key=api_key, **kwargs)

    @classmethod
    def get_default_model(cls) -> BaseModel:
        """Get the default model instance (singleton)."""
        if cls._instance is None:
            cls._instance = cls.create_model()
        return cls._instance

    @classmethod
    def reset_default_model(cls):
        """Reset the default model instance."""
        cls._instance = None