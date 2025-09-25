#!/usr/bin/env python3
"""
Demo Initialization Script for l0l1 Analytics

This script sets up a complete demo environment with:
- DuckDB database with realistic data
- Pre-populated learning patterns
- Graph-based relationships
- Query history for different teams
- Performance insights

Usage:
    python -m l0l1.demo.demo_init [ecommerce|saas]
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

from .duckdb_generator import create_demo_workspace
from ..services.learning_service import LearningService
from ..services.graph_learning_service import GraphLearningService
from ..core.config import settings


class DemoInitializer:
    """Initialize a complete demo environment for l0l1."""

    def __init__(self, company_type: str = "ecommerce"):
        self.company_type = company_type
        self.workspace_id = f"demo_{company_type}"

    async def initialize_complete_demo(self) -> Dict[str, Any]:
        """Set up a complete demo environment with all l0l1 features."""

        print(f"🚀 Initializing l0l1 demo environment: {self.company_type}")

        # Step 1: Create database and basic data
        print("📊 Creating demo database with realistic data...")
        workspace_data = create_demo_workspace(self.company_type)

        # Step 2: Initialize learning services
        print("🧠 Setting up AI learning services...")
        learning_service = LearningService(self.workspace_id)
        graph_service = GraphLearningService(self.workspace_id)

        # Step 3: Populate learning data from query history
        print("📈 Populating learning patterns...")
        await self._populate_learning_data(
            learning_service,
            graph_service,
            workspace_data['query_history']
        )

        # Step 4: Generate graph-based insights
        print("🕸️  Generating graph-based relationships...")
        graph_insights = self._generate_graph_insights(
            graph_service,
            workspace_data['learning_patterns']
        )

        # Step 5: Create workspace configuration
        print("⚙️  Creating workspace configuration...")
        workspace_config = self._create_workspace_config(workspace_data)

        # Step 6: Generate demo API responses
        print("🌐 Pre-generating API response cache...")
        api_cache = await self._generate_api_cache(workspace_data)

        # Step 7: Create demo documentation
        print("📚 Generating demo documentation...")
        demo_docs = self._create_demo_docs(workspace_data, graph_insights)

        demo_info = {
            "workspace_id": self.workspace_id,
            "company_type": self.company_type,
            "database_path": workspace_data['database_path'],
            "workspace_config": workspace_config,
            "graph_insights": graph_insights,
            "api_cache": api_cache,
            "demo_docs": demo_docs,
            "setup_complete": True
        }

        # Save complete demo info
        demo_file = Path(settings.workspace_data_dir) / "demo" / f"{self.workspace_id}_complete.json"
        with open(demo_file, 'w') as f:
            json.dump(demo_info, f, indent=2, default=str)

        print("✅ Demo environment initialized successfully!")
        print(f"📁 Demo files saved to: {demo_file.parent}")
        print(f"🗄️  Database: {workspace_data['database_path']}")

        return demo_info

    async def _populate_learning_data(
        self,
        learning_service: LearningService,
        graph_service: GraphLearningService,
        query_history: List[Dict[str, Any]]
    ):
        """Populate learning services with historical query data."""

        for query_record in query_history:
            # Add to vector-based learning
            if query_record.get('success', True):
                await learning_service.record_successful_query(
                    self.workspace_id,
                    query_record['sql'],
                    query_record.get('execution_time', 150),
                    query_record.get('result_count', 10)
                )

            # Add to graph-based learning
            user_context = {
                'user_id': query_record.get('user', 'demo_user'),
                'department': query_record.get('team', 'analytics')
            }

            await graph_service.analyze_and_store_query(
                query_record['sql'],
                query_record.get('execution_time', 150),
                query_record.get('result_count', 10),
                query_record.get('success', True),
                user_context
            )

    def _generate_graph_insights(
        self,
        graph_service: GraphLearningService,
        learning_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive graph-based insights."""

        # Get workspace insights
        workspace_insights = graph_service.get_workspace_insights()

        # Enhanced insights for demo
        enhanced_insights = {
            "workspace_insights": workspace_insights,

            "table_relationships": [
                {
                    "id": 1,
                    "from_table": "users",
                    "to_table": "orders",
                    "join_pattern": "users.id = orders.user_id",
                    "confidence": 0.95,
                    "frequency": learning_patterns['table_relationships'].get('users_orders', {}).get('frequency', 156),
                    "avg_performance": "180ms"
                },
                {
                    "id": 2,
                    "from_table": "orders",
                    "to_table": "order_items",
                    "join_pattern": "orders.id = order_items.order_id",
                    "confidence": 0.98,
                    "frequency": learning_patterns['table_relationships'].get('orders_order_items', {}).get('frequency', 142),
                    "avg_performance": "145ms"
                }
            ],

            "recommended_joins": [
                {
                    "id": 1,
                    "sql": "JOIN orders ON users.id = orders.user_id",
                    "reason": "Commonly used with users table (95% confidence)",
                    "frequency": 156
                },
                {
                    "id": 2,
                    "sql": "JOIN order_items ON orders.id = order_items.order_id",
                    "reason": "Standard pattern for order details",
                    "frequency": 142
                }
            ],

            "performance_insights": [
                {
                    "id": 1,
                    "type": "slow_table",
                    "title": "Large table scan detected",
                    "description": f"Queries on orders table average {learning_patterns['performance_patterns']['slow_patterns'][0]['avg_time'] if learning_patterns['performance_patterns']['slow_patterns'] else '1200ms'}",
                    "suggestion": "WHERE orders.created_at >= CURRENT_DATE - INTERVAL '30 days'",
                    "suggestion_text": "Add date filter to reduce scan"
                },
                {
                    "id": 2,
                    "type": "missing_index",
                    "title": "Index opportunity detected",
                    "description": "created_at column frequently used in WHERE clauses",
                    "suggestion_text": "Consider adding index on created_at"
                },
                {
                    "id": 3,
                    "type": "optimization",
                    "title": "JOIN performance",
                    "description": "User-order joins perform well with user_id filters",
                    "suggestion": "WHERE users.id IN (SELECT DISTINCT user_id FROM orders WHERE created_at >= '2024-01-01')",
                    "suggestion_text": "Filter users before joining for better performance"
                }
            ],

            "optimization_opportunities": [
                {
                    "id": 1,
                    "title": "Add LIMIT clauses",
                    "description": "Large result sets detected in similar queries",
                    "impact": "60% faster execution",
                    "affected_queries": 12
                },
                {
                    "id": 2,
                    "title": "Use indexed columns for filtering",
                    "description": "Non-indexed columns used in WHERE clauses",
                    "impact": "75% faster execution",
                    "affected_queries": 8
                }
            ],

            "team_patterns": learning_patterns.get('team_preferences', {}),

            "popular_templates": [
                {
                    "id": 1,
                    "name": "Monthly Revenue Analysis",
                    "sql": "SELECT DATE_TRUNC('month', created_at) as month, SUM(total_amount) as revenue FROM orders WHERE status = 'delivered' GROUP BY 1 ORDER BY 1 DESC",
                    "usage_count": 47,
                    "team": "sales",
                    "avg_execution_time": "156ms"
                },
                {
                    "id": 2,
                    "name": "Customer Order Summary",
                    "sql": "SELECT u.name, COUNT(o.id) as total_orders, SUM(o.total_amount) as total_spent FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id, u.name ORDER BY total_spent DESC",
                    "usage_count": 32,
                    "team": "sales",
                    "avg_execution_time": "234ms"
                },
                {
                    "id": 3,
                    "name": "Product Performance",
                    "sql": "SELECT p.name, SUM(oi.quantity) as units_sold, SUM(oi.total_price) as revenue FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id, p.name ORDER BY revenue DESC",
                    "usage_count": 28,
                    "team": "sales",
                    "avg_execution_time": "298ms"
                }
            ]
        }

        return enhanced_insights

    def _create_workspace_config(self, workspace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create workspace configuration for the demo."""

        return {
            "workspace_id": self.workspace_id,
            "name": workspace_data['company']['name'],
            "description": workspace_data['company']['description'],
            "company_type": self.company_type,
            "database_type": "duckdb",
            "database_path": workspace_data['database_path'],
            "tables": [table['name'] for table in workspace_data['schema_info']['tables']],
            "team_structure": workspace_data['company']['team_focus'],

            # Demo-specific settings
            "demo_mode": True,
            "learning_enabled": True,
            "pii_detection_enabled": True,
            "graph_learning_enabled": True,

            # Sample users for demo
            "demo_users": [
                {"name": "Sarah Johnson", "team": "sales", "role": "analyst"},
                {"name": "Mike Chen", "team": "sales", "role": "manager"},
                {"name": "Jessica Liu", "team": "marketing", "role": "analyst"},
                {"name": "David Rodriguez", "team": "marketing", "role": "manager"},
                {"name": "Robert Kim", "team": "finance", "role": "analyst"},
                {"name": "Alex Thompson", "team": "product", "role": "manager"}
            ]
        }

    async def _generate_api_cache(self, workspace_data: Dict[str, Any]) -> Dict[str, Any]:
        """Pre-generate API responses for demo performance."""

        # This would normally call the actual API endpoints
        # For demo, we'll create realistic mock responses

        return {
            "schema_endpoint": {
                "tables": workspace_data['schema_info']['tables'],
                "relationships": workspace_data['learning_patterns']['common_joins']
            },

            "learning_stats": {
                "total_queries": len(workspace_data['query_history']),
                "avg_execution_time": sum(q.get('execution_time', 0) for q in workspace_data['query_history']) / len(workspace_data['query_history']),
                "success_rate": len([q for q in workspace_data['query_history'] if q.get('success', True)]) / len(workspace_data['query_history']),
                "most_active_team": max(workspace_data['company']['team_focus'].keys()),
                "query_complexity_trend": "increasing"
            },

            "recent_queries": workspace_data['query_history'][-10:],  # Last 10 queries

            "performance_metrics": {
                "fast_queries": len([q for q in workspace_data['query_history'] if q.get('execution_time', 0) < 100]),
                "medium_queries": len([q for q in workspace_data['query_history'] if 100 <= q.get('execution_time', 0) < 1000]),
                "slow_queries": len([q for q in workspace_data['query_history'] if q.get('execution_time', 0) >= 1000])
            }
        }

    def _create_demo_docs(self, workspace_data: Dict[str, Any], graph_insights: Dict[str, Any]) -> Dict[str, Any]:
        """Create documentation for the demo."""

        return {
            "getting_started": {
                "title": f"Getting Started with {workspace_data['company']['name']}",
                "description": workspace_data['company']['description'],
                "sample_queries": [
                    {
                        "title": "Basic Revenue Query",
                        "sql": "SELECT SUM(total_amount) as total_revenue FROM orders WHERE status = 'delivered'",
                        "description": "Get total revenue from delivered orders"
                    },
                    {
                        "title": "Customer Analysis",
                        "sql": "SELECT COUNT(DISTINCT user_id) as total_customers FROM orders WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'",
                        "description": "Count active customers in last 30 days"
                    }
                ]
            },

            "schema_guide": {
                "title": "Database Schema Guide",
                "tables": workspace_data['schema_info']['tables'],
                "relationships": graph_insights['table_relationships']
            },

            "team_guides": {
                team: {
                    "title": f"{team.title()} Team Guide",
                    "common_patterns": patterns,
                    "sample_queries": [q for q in workspace_data['query_history'] if q.get('team') == team][:3]
                }
                for team, patterns in workspace_data['company']['team_focus'].items()
            }
        }


async def main():
    """Main entry point for demo initialization."""

    company_type = sys.argv[1] if len(sys.argv) > 1 else "ecommerce"

    if company_type not in ["ecommerce", "saas"]:
        print("❌ Error: company_type must be 'ecommerce' or 'saas'")
        sys.exit(1)

    # Ensure required directories exist
    demo_dir = Path(settings.workspace_data_dir) / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)

    # Initialize demo
    initializer = DemoInitializer(company_type)
    demo_info = await initializer.initialize_complete_demo()

    # Print summary
    print("\n" + "="*60)
    print("🎉 DEMO INITIALIZATION COMPLETE!")
    print("="*60)
    print(f"Company Type: {company_type}")
    print(f"Workspace ID: {demo_info['workspace_id']}")
    print(f"Database: {demo_info['database_path']}")
    print(f"Tables: {len(demo_info['workspace_config']['tables'])}")
    print(f"Sample Queries: {len(demo_info['api_cache']['recent_queries'])}")
    print("\n🚀 You can now start the l0l1 server and explore the demo!")
    print("\nTo start the demo server:")
    print(f"  l0l1 serve --demo --workspace {demo_info['workspace_id']}")
    print("\nTo explore with CLI:")
    print(f"  l0l1 validate --workspace {demo_info['workspace_id']} \"SELECT * FROM users LIMIT 10\"")


if __name__ == "__main__":
    asyncio.run(main())