from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class SQLCellRenderer:
    """Renders SQL analysis results for UI integration."""

    @staticmethod
    def render_to_vue_component(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Render analysis results as Vue component data."""
        query = analysis_results["query"]
        results = analysis_results["results"]

        component_data = {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "components": []
        }

        # Query display component
        component_data["components"].append({
            "type": "query-display",
            "props": {
                "query": query,
                "language": "sql"
            }
        })

        # PII detection component
        if "pii" in results:
            pii_data = results["pii"]
            component_data["components"].append({
                "type": "pii-detection",
                "props": {
                    "detected": pii_data["detected"],
                    "entities": pii_data.get("entities", []),
                    "anonymized_query": pii_data.get("anonymized_query"),
                    "severity": "warning" if pii_data["detected"] else "success"
                }
            })

        # Validation component
        if "validation" in results:
            validation = results["validation"]
            component_data["components"].append({
                "type": "validation-result",
                "props": {
                    "is_valid": validation.get("is_valid", True),
                    "issues": validation.get("issues", []),
                    "suggestions": validation.get("suggestions", []),
                    "severity": validation.get("severity", "medium")
                }
            })

        # Explanation component
        if "explanation" in results and "error" not in results["explanation"]:
            component_data["components"].append({
                "type": "query-explanation",
                "props": {
                    "explanation": results["explanation"]["text"]
                }
            })

        # Suggestions component
        if "suggestions" in results and results["suggestions"].get("completions"):
            component_data["components"].append({
                "type": "query-suggestions",
                "props": {
                    "suggestions": results["suggestions"]["completions"][:3],
                    "learning_applied": results["suggestions"].get("learning_applied", False)
                }
            })

        # Learning stats component
        if "learning_stats" in results and results["learning_stats"]["total_queries"] > 0:
            component_data["components"].append({
                "type": "learning-stats",
                "props": {
                    "stats": results["learning_stats"]
                }
            })

        return component_data

    @staticmethod
    def render_to_skeleton_ui(analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Render analysis results optimized for SkeletonUI components."""
        query = analysis_results["query"]
        results = analysis_results["results"]

        skeleton_data = {
            "query": query,
            "cards": []
        }

        # Query card
        skeleton_data["cards"].append({
            "type": "code-block",
            "header": "SQL Query",
            "content": query,
            "language": "sql",
            "variant": "ghost"
        })

        # PII card
        if "pii" in results:
            pii_data = results["pii"]
            if pii_data["detected"]:
                skeleton_data["cards"].append({
                    "type": "alert",
                    "variant": "warning",
                    "header": "⚠️ PII Detected",
                    "content": {
                        "entities": pii_data["entities"],
                        "anonymized": pii_data.get("anonymized_query")
                    }
                })
            else:
                skeleton_data["cards"].append({
                    "type": "alert",
                    "variant": "success",
                    "header": "✅ No PII Detected",
                    "content": "Query is safe from PII perspective"
                })

        # Validation card
        if "validation" in results:
            validation = results["validation"]
            variant = "success" if validation.get("is_valid", True) else "error"

            skeleton_data["cards"].append({
                "type": "alert",
                "variant": variant,
                "header": "✅ Valid Query" if validation.get("is_valid", True) else "❌ Query Issues",
                "content": {
                    "issues": validation.get("issues", []),
                    "suggestions": validation.get("suggestions", []),
                    "severity": validation.get("severity", "medium")
                }
            })

        # Explanation card
        if "explanation" in results and "error" not in results["explanation"]:
            skeleton_data["cards"].append({
                "type": "card",
                "header": "📝 Query Explanation",
                "content": results["explanation"]["text"],
                "variant": "ghost"
            })

        # Suggestions card
        if "suggestions" in results and results["suggestions"].get("completions"):
            skeleton_data["cards"].append({
                "type": "accordion",
                "header": "💡 Query Suggestions",
                "items": [
                    {
                        "title": f"Option {i+1}",
                        "content": suggestion,
                        "type": "code"
                    }
                    for i, suggestion in enumerate(results["suggestions"]["completions"][:3])
                ]
            })

        return skeleton_data

    @staticmethod
    def generate_tailwind_classes(component_type: str, variant: str = "default") -> Dict[str, str]:
        """Generate Tailwind CSS classes for different component types."""
        class_maps = {
            "query-display": {
                "container": "bg-gray-50 rounded-lg p-4 mb-4",
                "header": "text-sm font-semibold text-gray-700 mb-3",
                "code": "bg-gray-900 text-gray-100 p-3 rounded-md overflow-x-auto text-sm font-mono"
            },
            "pii-detection": {
                "warning": "bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4",
                "success": "bg-green-50 border border-green-200 rounded-lg p-4 mb-4",
                "header": "text-sm font-semibold mb-3",
                "entity": "inline-block bg-yellow-100 text-yellow-800 px-2 py-1 rounded text-xs mr-2 mb-2"
            },
            "validation-result": {
                "success": "bg-green-50 border border-green-200 rounded-lg p-4 mb-4",
                "error": "bg-red-50 border border-red-200 rounded-lg p-4 mb-4",
                "header": "text-sm font-semibold mb-3",
                "issue": "text-sm mb-2",
                "suggestion": "text-sm mb-2 text-blue-600"
            },
            "explanation": {
                "container": "bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4",
                "header": "text-sm font-semibold text-blue-800 mb-3",
                "content": "text-sm text-blue-700 leading-relaxed"
            },
            "suggestions": {
                "container": "bg-green-50 border border-green-200 rounded-lg p-4 mb-4",
                "header": "text-sm font-semibold text-green-800 mb-3",
                "suggestion": "mb-3 last:mb-0",
                "code": "bg-gray-900 text-gray-100 p-3 rounded-md overflow-x-auto text-sm font-mono mt-2"
            }
        }

        return class_maps.get(component_type, {})


class NotebookRenderer:
    """Renders notebook-like interface components."""

    @staticmethod
    def create_cell_template(cell_type: str = "sql") -> Dict[str, Any]:
        """Create a template for notebook cells."""
        templates = {
            "sql": {
                "cell_type": "sql",
                "source": "",
                "metadata": {
                    "l0l1": {
                        "options": {
                            "validate": True,
                            "explain": False,
                            "check_pii": True,
                            "complete": False,
                            "anonymize": False
                        }
                    }
                },
                "outputs": [],
                "execution_count": None
            },
            "markdown": {
                "cell_type": "markdown",
                "source": "",
                "metadata": {},
                "outputs": [],
                "execution_count": None
            }
        }

        return templates.get(cell_type, templates["sql"])

    @staticmethod
    def create_notebook_template(workspace_id: str, title: str = "New Notebook") -> Dict[str, Any]:
        """Create a template for a complete notebook."""
        return {
            "metadata": {
                "l0l1": {
                    "workspace_id": workspace_id,
                    "title": title,
                    "created_at": datetime.utcnow().isoformat(),
                    "kernel_info": {
                        "name": "l0l1-sql",
                        "version": "0.2.0"
                    }
                }
            },
            "cells": [
                {
                    "cell_type": "markdown",
                    "source": f"# {title}\n\nThis notebook uses l0l1 for SQL analysis and validation.",
                    "metadata": {},
                    "outputs": [],
                    "execution_count": None
                }
            ]
        }

    @staticmethod
    def render_notebook_toolbar() -> Dict[str, Any]:
        """Render toolbar options for notebook interface."""
        return {
            "cell_types": [
                {"value": "sql", "label": "SQL", "icon": "database"},
                {"value": "markdown", "label": "Markdown", "icon": "document-text"}
            ],
            "execution_options": [
                {"key": "validate", "label": "Validate", "default": True},
                {"key": "explain", "label": "Explain", "default": False},
                {"key": "check_pii", "label": "Check PII", "default": True},
                {"key": "complete", "label": "Complete", "default": False},
                {"key": "anonymize", "label": "Anonymize", "default": False}
            ],
            "actions": [
                {"key": "run", "label": "Run", "shortcut": "Shift+Enter", "icon": "play"},
                {"key": "run_all", "label": "Run All", "shortcut": "Ctrl+Shift+Enter", "icon": "play-circle"},
                {"key": "clear", "label": "Clear Outputs", "shortcut": "Ctrl+Alt+O", "icon": "trash"},
                {"key": "export", "label": "Export", "icon": "download"}
            ]
        }