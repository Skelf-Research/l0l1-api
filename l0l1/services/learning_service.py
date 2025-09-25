import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import json

from ..models.factory import ModelFactory
from ..core.config import settings
from .pii_detector import PIIDetector


class LearningService:
    """Continuous learning service for SQL query improvement."""

    def __init__(self):
        self.model = ModelFactory.get_default_model()
        self.pii_detector = PIIDetector()
        self.learning_data = {}  # In-memory storage for demo, replace with persistent storage

    async def record_successful_query(
        self,
        workspace_id: str,
        query: str,
        execution_time: float,
        result_count: int,
        schema_context: Optional[str] = None
    ) -> bool:
        """Record a successful query for learning."""
        if not settings.enable_learning:
            return False

        # Check if query is safe for learning (no PII)
        if not self.pii_detector.is_safe_for_learning(query):
            # Sanitize the query
            sanitized_query = self.pii_detector.sanitize_for_learning(query)
            query = sanitized_query

        # Generate embedding for similarity matching
        try:
            embedding_response = await self.model.generate_embedding(query)
            embedding = embedding_response.embedding
        except Exception:
            return False

        # Create learning record
        query_hash = hashlib.sha256(query.encode()).hexdigest()
        learning_record = {
            "query_hash": query_hash,
            "query": query,
            "workspace_id": workspace_id,
            "embedding": embedding,
            "execution_time": execution_time,
            "result_count": result_count,
            "schema_context": schema_context,
            "success_count": 1,
            "last_used": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }

        # Store or update learning record
        if query_hash in self.learning_data:
            existing = self.learning_data[query_hash]
            existing["success_count"] += 1
            existing["last_used"] = datetime.utcnow().isoformat()
            existing["execution_time"] = (existing["execution_time"] + execution_time) / 2
        else:
            self.learning_data[query_hash] = learning_record

        return True

    async def get_similar_successful_queries(
        self,
        query: str,
        workspace_id: str,
        limit: int = 5,
        similarity_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """Get similar successful queries for learning."""
        if not settings.enable_learning or not self.learning_data:
            return []

        similarity_threshold = similarity_threshold or settings.learning_threshold

        try:
            # Generate embedding for the input query
            embedding_response = await self.model.generate_embedding(query)
            query_embedding = embedding_response.embedding

            # Calculate similarities with learned queries
            similarities = []
            for record in self.learning_data.values():
                # Filter by workspace if specified
                if workspace_id and record["workspace_id"] != workspace_id:
                    continue

                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, record["embedding"])
                if similarity >= similarity_threshold:
                    similarities.append({
                        **record,
                        "similarity": similarity
                    })

            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:limit]

        except Exception:
            return []

    async def get_query_suggestions(
        self,
        partial_query: str,
        workspace_id: str,
        schema_context: Optional[str] = None
    ) -> List[str]:
        """Get query completion suggestions based on learned patterns."""
        # Get similar successful queries
        similar_queries = await self.get_similar_successful_queries(
            partial_query,
            workspace_id,
            limit=3,
            similarity_threshold=0.6
        )

        suggestions = []

        # Use AI model to complete the query
        try:
            ai_completion = await self.model.complete_sql_query(
                partial_query,
                schema_context
            )
            suggestions.append(ai_completion)
        except Exception:
            pass

        # Add suggestions from learned queries
        for similar in similar_queries:
            if similar["query"] not in suggestions:
                suggestions.append(similar["query"])

        return suggestions[:5]

    async def improve_query_with_learning(
        self,
        original_query: str,
        workspace_id: str,
        error_message: Optional[str] = None,
        schema_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Improve query using learned patterns and AI."""
        result = {
            "improved_query": original_query,
            "confidence": 0.0,
            "learning_applied": False,
            "suggestions": []
        }

        # Get similar successful queries
        similar_queries = await self.get_similar_successful_queries(
            original_query,
            workspace_id,
            limit=3
        )

        if similar_queries:
            result["learning_applied"] = True
            result["suggestions"] = [q["query"] for q in similar_queries[:3]]

        # Use AI to correct the query
        try:
            corrected_query = await self.model.correct_sql_query(
                original_query,
                error_message,
                schema_context
            )
            result["improved_query"] = corrected_query
            result["confidence"] = 0.8 if similar_queries else 0.6
        except Exception:
            if similar_queries:
                result["improved_query"] = similar_queries[0]["query"]
                result["confidence"] = similar_queries[0]["similarity"]

        return result

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def get_learning_stats(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Get learning statistics."""
        if workspace_id:
            workspace_data = [
                record for record in self.learning_data.values()
                if record["workspace_id"] == workspace_id
            ]
        else:
            workspace_data = list(self.learning_data.values())

        if not workspace_data:
            return {
                "total_queries": 0,
                "avg_execution_time": 0.0,
                "most_successful": None,
                "recent_activity": []
            }

        total_queries = len(workspace_data)
        avg_execution_time = sum(q["execution_time"] for q in workspace_data) / total_queries

        # Most successful query
        most_successful = max(workspace_data, key=lambda x: x["success_count"])

        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_activity = [
            q for q in workspace_data
            if datetime.fromisoformat(q["last_used"]) > week_ago
        ]

        return {
            "total_queries": total_queries,
            "avg_execution_time": avg_execution_time,
            "most_successful": {
                "query": most_successful["query"][:100] + "..." if len(most_successful["query"]) > 100 else most_successful["query"],
                "success_count": most_successful["success_count"]
            },
            "recent_activity": len(recent_activity)
        }