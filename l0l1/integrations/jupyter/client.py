"""HTTP client for l0l1 API integration in Jupyter."""

from typing import Optional, Dict, Any, List
import httpx


class L0l1JupyterClient:
    """Client for communicating with l0l1 API from Jupyter notebooks."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        timeout: float = 30.0
    ):
        self.api_url = api_url
        self.timeout = timeout
        self.provider = "openai"
        self._client: Optional[httpx.AsyncClient] = None

    def set_api_url(self, url: str) -> None:
        """Set the API server URL."""
        self.api_url = url.rstrip('/')
        self._client = None  # Reset client

    def set_provider(self, provider: str) -> None:
        """Set the AI provider."""
        self.provider = provider

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.api_url,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
        return self._client

    async def get_status(self) -> Dict[str, Any]:
        """Get server status."""
        try:
            client = await self._get_client()
            response = await client.get("/health")
            data = response.json()
            return {
                "connected": True,
                "provider": data.get("ai_provider", self.provider),
                "version": data.get("version", "unknown"),
                "features": data.get("features", {})
            }
        except Exception:
            return {
                "connected": False,
                "provider": self.provider,
                "version": "unknown",
                "features": {}
            }

    async def validate(
        self,
        query: str,
        workspace_id: str = "default",
        schema_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate a SQL query."""
        try:
            client = await self._get_client()
            response = await client.post("/sql/validate", json={
                "query": query,
                "workspace_id": workspace_id,
                "schema_context": schema_context
            })
            data = response.json()
            return {
                "valid": data.get("valid", True),
                "errors": self._normalize_issues(data.get("errors", [])),
                "warnings": self._normalize_issues(data.get("warnings", [])),
                "suggestions": data.get("suggestions", [])
            }
        except httpx.ConnectError:
            return {
                "valid": False,
                "errors": ["Cannot connect to l0l1 server. Is it running?"],
                "warnings": [],
                "suggestions": ["Start the server with: uv run l0l1-serve"]
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "suggestions": []
            }

    async def explain(
        self,
        query: str,
        workspace_id: str = "default"
    ) -> Dict[str, Any]:
        """Get explanation for a SQL query."""
        try:
            client = await self._get_client()
            response = await client.post("/sql/explain", json={
                "query": query,
                "workspace_id": workspace_id
            })
            data = response.json()
            return {
                "explanation": data.get("explanation", "No explanation available"),
                "complexity": data.get("complexity", "unknown"),
                "tables": data.get("tables_accessed", [])
            }
        except httpx.ConnectError:
            return {
                "explanation": "Cannot connect to l0l1 server",
                "complexity": "unknown",
                "tables": []
            }
        except Exception as e:
            return {
                "explanation": f"Error: {str(e)}",
                "complexity": "unknown",
                "tables": []
            }

    async def check_pii(self, query: str) -> Dict[str, Any]:
        """Check for PII in a SQL query."""
        try:
            client = await self._get_client()
            response = await client.post("/pii/detect", json={
                "query": query
            })
            data = response.json()
            return {
                "has_pii": data.get("has_pii", False),
                "detections": [
                    {
                        "entity_type": d.get("entity_type"),
                        "value": d.get("value"),
                        "start": d.get("start"),
                        "end": d.get("end"),
                        "score": d.get("score", 0)
                    }
                    for d in data.get("detections", [])
                ]
            }
        except httpx.ConnectError:
            return {"has_pii": False, "detections": []}
        except Exception:
            return {"has_pii": False, "detections": []}

    async def anonymize(self, query: str) -> Dict[str, Any]:
        """Anonymize PII in a SQL query."""
        try:
            client = await self._get_client()
            response = await client.post("/pii/anonymize", json={
                "query": query
            })
            data = response.json()
            return {
                "anonymized_query": data.get("anonymized_query", query),
                "has_pii": bool(data.get("replacements")),
                "detections": [
                    {
                        "entity_type": r.get("entity_type"),
                        "value": r.get("original"),
                        "score": 1.0
                    }
                    for r in data.get("replacements", [])
                ]
            }
        except Exception:
            return {
                "anonymized_query": query,
                "has_pii": False,
                "detections": []
            }

    async def complete(
        self,
        partial_query: str,
        workspace_id: str = "default",
        limit: int = 5
    ) -> Dict[str, Any]:
        """Get completions for a partial SQL query."""
        try:
            client = await self._get_client()
            response = await client.post("/sql/complete", json={
                "partial_query": partial_query,
                "workspace_id": workspace_id,
                "limit": limit
            })
            data = response.json()
            return {
                "completions": data.get("completions", [])
            }
        except Exception:
            return {"completions": []}

    async def record_query(
        self,
        query: str,
        workspace_id: str = "default",
        execution_time_ms: float = 0,
        success: bool = True
    ) -> bool:
        """Record a successful query for learning."""
        try:
            client = await self._get_client()
            await client.post("/learning/record", json={
                "query": query,
                "workspace_id": workspace_id,
                "execution_time_ms": execution_time_ms,
                "success": success
            })
            return True
        except Exception:
            return False

    async def get_similar_queries(
        self,
        query: str,
        workspace_id: str = "default",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar queries from learning history."""
        try:
            client = await self._get_client()
            response = await client.get("/learning/similar", params={
                "query": query,
                "workspace_id": workspace_id,
                "limit": limit
            })
            data = response.json()
            return data.get("similar_queries", [])
        except Exception:
            return []

    def _normalize_issues(self, issues: List) -> List[str]:
        """Normalize issues to string list."""
        result = []
        for issue in issues:
            if isinstance(issue, str):
                result.append(issue)
            elif isinstance(issue, dict):
                result.append(issue.get("message", str(issue)))
            else:
                result.append(str(issue))
        return result

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
