"""Continuous learning service for SQL query improvement with persistent storage."""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.factory import ModelFactory
from ..core.config import settings
from .pii_detector import PIIDetector
from .pattern_store import PatternStore


class LearningService:
    """Continuous learning service for SQL query improvement."""

    def __init__(self, db_path: str = None):
        self.model = ModelFactory.get_default_model()
        self.pii_detector = PIIDetector()
        self.store = PatternStore(db_path or "./data/learning_patterns.db")

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
            query = self.pii_detector.sanitize_for_learning(query)

        # Generate embedding for similarity matching
        embedding = None
        try:
            embedding_response = await self.model.generate_embedding(query)
            embedding = embedding_response.embedding
        except Exception as e:
            print(f"Warning: Could not generate embedding: {e}")
            # Continue without embedding - pattern will still be saved

        # Save to persistent store
        self.store.save_pattern(
            query=query,
            workspace_id=workspace_id,
            embedding=embedding,
            execution_time=execution_time,
            result_count=result_count,
            schema_context=schema_context
        )

        return True

    async def get_similar_successful_queries(
        self,
        query: str,
        workspace_id: str,
        limit: int = 5,
        similarity_threshold: float = None
    ) -> List[Dict[str, Any]]:
        """Get similar successful queries for learning."""
        if not settings.enable_learning:
            return []

        similarity_threshold = similarity_threshold or settings.learning_threshold

        try:
            # Generate embedding for the input query
            embedding_response = await self.model.generate_embedding(query)
            query_embedding = embedding_response.embedding

            # Get all patterns with embeddings from store
            patterns = self.store.get_patterns_with_embeddings(workspace_id)

            if not patterns:
                return []

            # Calculate similarities
            similarities = []
            for pattern in patterns:
                if not pattern.get("embedding"):
                    continue

                similarity = self._cosine_similarity(query_embedding, pattern["embedding"])
                if similarity >= similarity_threshold:
                    pattern["similarity"] = similarity
                    similarities.append(pattern)

            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:limit]

        except Exception as e:
            print(f"Warning: Could not search similar queries: {e}")
            return []

    async def get_query_suggestions(
        self,
        partial_query: str,
        workspace_id: str,
        schema_context: Optional[str] = None
    ) -> List[str]:
        """Get query completion suggestions based on learned patterns."""
        suggestions = []

        # Get similar successful queries
        similar_queries = await self.get_similar_successful_queries(
            partial_query,
            workspace_id,
            limit=3,
            similarity_threshold=0.6
        )

        # Use AI model to complete the query
        try:
            ai_completion = await self.model.complete_sql_query(
                partial_query,
                schema_context
            )
            suggestions.append(ai_completion)
        except Exception as e:
            print(f"Warning: AI completion failed: {e}")

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
        except Exception as e:
            print(f"Warning: AI correction failed: {e}")
            if similar_queries:
                result["improved_query"] = similar_queries[0]["query"]
                result["confidence"] = similar_queries[0].get("similarity", 0.5)

        return result

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def get_learning_stats(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Get learning statistics."""
        return self.store.get_stats(workspace_id)

    def list_patterns(
        self,
        workspace_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "last_used",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """List learned patterns with pagination."""
        return self.store.list_patterns(workspace_id, limit, offset, sort_by, sort_order)

    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific pattern by ID."""
        pattern = self.store.get_pattern(pattern_id)
        if pattern:
            pattern.pop("embedding", None)  # Don't return embedding in API
        return pattern

    def update_pattern(self, pattern_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a pattern's metadata."""
        pattern = self.store.update_pattern(pattern_id, updates)
        if pattern:
            pattern.pop("embedding", None)
        return pattern

    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a learned pattern."""
        return self.store.delete_pattern(pattern_id)

    def bulk_delete_patterns(
        self,
        pattern_ids: List[str] = None,
        workspace_id: str = None,
        older_than_days: int = None
    ) -> int:
        """Bulk delete patterns based on criteria."""
        return self.store.bulk_delete(pattern_ids, workspace_id, older_than_days)

    def adjust_confidence(self, pattern_id: str, adjustment: float) -> Optional[Dict[str, Any]]:
        """Adjust a pattern's success count (affects confidence)."""
        pattern = self.store.adjust_confidence(pattern_id, adjustment)
        if pattern:
            pattern.pop("embedding", None)
        return pattern

    def export_patterns(self, workspace_id: Optional[str] = None, format: str = "json") -> str:
        """Export patterns for backup or transfer."""
        patterns = self.store.export_patterns(workspace_id)

        if format == "json":
            return json.dumps({
                "patterns": patterns,
                "exported_at": datetime.utcnow().isoformat()
            }, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    async def import_patterns(
        self,
        data: Dict[str, Any],
        workspace_id: str,
        overwrite: bool = False
    ) -> Dict[str, Any]:
        """Import patterns from backup."""
        patterns = data.get("patterns", [])
        result = self.store.import_patterns(patterns, workspace_id, overwrite)

        # Optionally regenerate embeddings for imported patterns
        # This is expensive so we skip it by default
        # for pattern in patterns:
        #     try:
        #         embedding_response = await self.model.generate_embedding(pattern["query"])
        #         self.store.update_pattern(pattern["query_hash"], {"embedding": embedding_response.embedding})
        #     except:
        #         pass

        return result
