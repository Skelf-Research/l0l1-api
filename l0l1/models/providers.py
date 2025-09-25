from typing import List, Optional, Dict, Any
import asyncio
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from langchain_openai import OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic

from .base import BaseModel, EmbeddingResponse, CompletionResponse


class ModelProvider:
    """Registry for different AI model providers."""

    providers = {}

    @classmethod
    def register(cls, name: str, provider_class):
        cls.providers[name] = provider_class

    @classmethod
    def create(cls, name: str, **kwargs) -> BaseModel:
        if name not in cls.providers:
            raise ValueError(f"Unknown provider: {name}")
        return cls.providers[name](**kwargs)


class OpenAIProvider(BaseModel):
    """OpenAI model provider."""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.client = AsyncOpenAI(api_key=api_key)
        self.embedding_model = kwargs.get("embedding_model", "text-embedding-3-small")
        self.completion_model = kwargs.get("completion_model", "gpt-4o-mini")

    async def generate_embedding(self, text: str, model: Optional[str] = None) -> EmbeddingResponse:
        model = model or self.embedding_model
        response = await self.client.embeddings.create(
            input=text,
            model=model
        )
        return EmbeddingResponse(
            embedding=response.data[0].embedding,
            model=model,
            usage=response.usage.model_dump() if response.usage else None
        )

    async def complete_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.0,
        **kwargs
    ) -> CompletionResponse:
        model = model or self.completion_model
        response = await self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )

        return CompletionResponse(
            content=response.choices[0].message.content,
            model=model,
            usage=response.usage.model_dump() if response.usage else None,
            finish_reason=response.choices[0].finish_reason
        )

    async def explain_sql_query(self, query: str, schema_context: Optional[str] = None) -> str:
        context = f"\n\nSchema context:\n{schema_context}" if schema_context else ""
        prompt = f"""Explain the following SQL query in clear, concise language:

SQL Query:
{query}{context}

Please provide:
1. What the query does
2. Which tables/columns it uses
3. Any joins or complex operations
4. The expected result format"""

        response = await self.complete_text(prompt)
        return response.content

    async def complete_sql_query(
        self,
        partial_query: str,
        schema_context: Optional[str] = None,
        table_suggestions: Optional[List[str]] = None
    ) -> str:
        context = f"\n\nSchema context:\n{schema_context}" if schema_context else ""
        tables = f"\n\nAvailable tables: {', '.join(table_suggestions)}" if table_suggestions else ""

        prompt = f"""Complete the following partial SQL query:

Partial Query:
{partial_query}{context}{tables}

Please provide only the completed SQL query without explanations."""

        response = await self.complete_text(prompt, max_tokens=200)
        return response.content.strip()

    async def validate_sql_query(
        self,
        query: str,
        schema_context: Optional[str] = None
    ) -> Dict[str, Any]:
        context = f"\n\nSchema context:\n{schema_context}" if schema_context else ""
        prompt = f"""Analyze the following SQL query for potential issues:

SQL Query:
{query}{context}

Please respond in JSON format with:
{{
  "is_valid": boolean,
  "issues": ["list of issues found"],
  "suggestions": ["list of improvement suggestions"],
  "severity": "low|medium|high"
}}"""

        response = await self.complete_text(prompt, max_tokens=300)
        try:
            import json
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "is_valid": False,
                "issues": ["Could not parse validation response"],
                "suggestions": [],
                "severity": "medium"
            }

    async def correct_sql_query(
        self,
        query: str,
        error_message: Optional[str] = None,
        schema_context: Optional[str] = None
    ) -> str:
        context = f"\n\nSchema context:\n{schema_context}" if schema_context else ""
        error = f"\n\nError message:\n{error_message}" if error_message else ""

        prompt = f"""Correct the following SQL query:

SQL Query:
{query}{context}{error}

Please provide only the corrected SQL query without explanations."""

        response = await self.complete_text(prompt, max_tokens=300)
        return response.content.strip()


class AnthropicProvider(BaseModel):
    """Anthropic Claude model provider."""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.client = AsyncAnthropic(api_key=api_key)
        self.completion_model = kwargs.get("completion_model", "claude-3-haiku-20240307")

    async def generate_embedding(self, text: str, model: Optional[str] = None) -> EmbeddingResponse:
        # Anthropic doesn't provide embeddings, fallback to OpenAI
        from ..core.config import settings
        if settings.openai_api_key:
            openai_provider = OpenAIProvider(api_key=settings.openai_api_key)
            return await openai_provider.generate_embedding(text, model)
        raise NotImplementedError("Anthropic doesn't provide embeddings. Configure OpenAI as fallback.")

    async def complete_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.0,
        **kwargs
    ) -> CompletionResponse:
        model = model or self.completion_model
        max_tokens = max_tokens or 1000

        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )

        return CompletionResponse(
            content=response.content[0].text,
            model=model,
            usage=response.usage.__dict__ if hasattr(response, 'usage') else None,
            finish_reason=response.stop_reason
        )

    async def explain_sql_query(self, query: str, schema_context: Optional[str] = None) -> str:
        context = f"\n\nSchema context:\n{schema_context}" if schema_context else ""
        prompt = f"""Explain the following SQL query in clear, concise language:

SQL Query:
{query}{context}

Please provide:
1. What the query does
2. Which tables/columns it uses
3. Any joins or complex operations
4. The expected result format"""

        response = await self.complete_text(prompt)
        return response.content

    async def complete_sql_query(
        self,
        partial_query: str,
        schema_context: Optional[str] = None,
        table_suggestions: Optional[List[str]] = None
    ) -> str:
        context = f"\n\nSchema context:\n{schema_context}" if schema_context else ""
        tables = f"\n\nAvailable tables: {', '.join(table_suggestions)}" if table_suggestions else ""

        prompt = f"""Complete the following partial SQL query:

Partial Query:
{partial_query}{context}{tables}

Please provide only the completed SQL query without explanations."""

        response = await self.complete_text(prompt, max_tokens=200)
        return response.content.strip()

    async def validate_sql_query(
        self,
        query: str,
        schema_context: Optional[str] = None
    ) -> Dict[str, Any]:
        context = f"\n\nSchema context:\n{schema_context}" if schema_context else ""
        prompt = f"""Analyze the following SQL query for potential issues:

SQL Query:
{query}{context}

Please respond in JSON format with:
{{
  "is_valid": boolean,
  "issues": ["list of issues found"],
  "suggestions": ["list of improvement suggestions"],
  "severity": "low|medium|high"
}}"""

        response = await self.complete_text(prompt, max_tokens=300)
        try:
            import json
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "is_valid": False,
                "issues": ["Could not parse validation response"],
                "suggestions": [],
                "severity": "medium"
            }

    async def correct_sql_query(
        self,
        query: str,
        error_message: Optional[str] = None,
        schema_context: Optional[str] = None
    ) -> str:
        context = f"\n\nSchema context:\n{schema_context}" if schema_context else ""
        error = f"\n\nError message:\n{error_message}" if error_message else ""

        prompt = f"""Correct the following SQL query:

SQL Query:
{query}{context}{error}

Please provide only the corrected SQL query without explanations."""

        response = await self.complete_text(prompt, max_tokens=300)
        return response.content.strip()


# Register providers
ModelProvider.register("openai", OpenAIProvider)
ModelProvider.register("anthropic", AnthropicProvider)