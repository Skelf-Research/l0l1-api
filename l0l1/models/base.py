from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel as PydanticBaseModel


class EmbeddingResponse(PydanticBaseModel):
    embedding: List[float]
    model: str
    usage: Optional[Dict[str, Any]] = None


class CompletionResponse(PydanticBaseModel):
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None


class BaseModel(ABC):
    """Abstract base class for AI model providers."""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def generate_embedding(self, text: str, model: Optional[str] = None) -> EmbeddingResponse:
        """Generate embeddings for the given text."""
        pass

    @abstractmethod
    async def complete_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.0,
        **kwargs
    ) -> CompletionResponse:
        """Generate text completion."""
        pass

    @abstractmethod
    async def explain_sql_query(self, query: str, schema_context: Optional[str] = None) -> str:
        """Generate explanation for SQL query."""
        pass

    @abstractmethod
    async def complete_sql_query(
        self,
        partial_query: str,
        schema_context: Optional[str] = None,
        table_suggestions: Optional[List[str]] = None
    ) -> str:
        """Complete partial SQL query."""
        pass

    @abstractmethod
    async def validate_sql_query(
        self,
        query: str,
        schema_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate SQL query and return suggestions."""
        pass

    @abstractmethod
    async def correct_sql_query(
        self,
        query: str,
        error_message: Optional[str] = None,
        schema_context: Optional[str] = None
    ) -> str:
        """Correct SQL query based on error."""
        pass