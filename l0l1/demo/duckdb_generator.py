import duckdb
import random
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import json

from ..core.config import settings
from ..services.graph_learning_service import GraphLearningService


class DemoDataGenerator:
    """Generate realistic demo data using DuckDB for l0l1 demonstrations."""

    def __init__(self, db_path: str = "demo_analytics.duckdb"):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)

        # Demo company scenarios
        self.companies = {
            "ecommerce": {
                "name": "TechMart Analytics",
                "description": "E-commerce platform with users, products, orders",
                "tables": ["users", "products", "orders", "order_items", "categories", "reviews"],
                "team_focus": {
                    "sales": ["conversion", "revenue", "customer_segments"],
                    "marketing": ["campaigns", "attribution", "funnel"],
                    "finance": ["costs", "profitability", "forecasting"]
                }
            },
            "saas": {
                "name": "CloudApp Metrics",
                "description": "SaaS platform with subscriptions and usage analytics",
                "tables": ["users", "subscriptions", "usage_events", "billing", "support_tickets"],
                "team_focus": {
                    "product": ["feature_usage", "retention", "churn"],
                    "growth": ["activation", "expansion", "acquisition"],
                    "support": ["tickets", "satisfaction", "resolution_time"]
                }
            }
        }

    def setup_demo_workspace(self, company_type: str = "ecommerce") -> Dict[str, Any]:
        """Set up a complete demo workspace with realistic data."""

        if company_type not in self.companies:
            raise ValueError(f"Company type must be one of: {list(self.companies.keys())}")

        company = self.companies[company_type]

        # Create tables and data
        if company_type == "ecommerce":
            self._create_ecommerce_data()
        elif company_type == "saas":
            self._create_saas_data()

        # Generate demo learning data
        learning_data = self._generate_learning_patterns(company_type)

        # Create demo query history
        query_history = self._generate_query_history(company_type)

        return {
            "company": company,
            "database_path": self.db_path,
            "learning_patterns": learning_data,
            "query_history": query_history,
            "schema_info": self._get_schema_info()
        }

    def _create_ecommerce_data(self):
        """Create realistic e-commerce dataset."""

        # Categories
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100),
                parent_id INTEGER,
                created_at TIMESTAMP
            )
        """)

        categories = [
            (1, 'Electronics', None, '2023-01-01'),
            (2, 'Clothing', None, '2023-01-01'),
            (3, 'Home & Garden', None, '2023-01-01'),
            (4, 'Smartphones', 1, '2023-01-01'),
            (5, 'Laptops', 1, '2023-01-01'),
            (6, "Men's Clothing", 2, '2023-01-01'),
            (7, "Women's Clothing", 2, '2023-01-01'),
        ]

        for cat in categories:
            self.conn.execute(
                "INSERT OR REPLACE INTO categories VALUES (?, ?, ?, ?)", cat
            )

        # Users (realistic distribution)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name VARCHAR(255),
                email VARCHAR(255),
                age INTEGER,
                city VARCHAR(100),
                signup_source VARCHAR(50),
                created_at TIMESTAMP,
                last_login TIMESTAMP,
                total_spent DECIMAL(10,2)
            )
        """)

        # Generate 10,000 users
        cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose']
        sources = ['google', 'facebook', 'direct', 'email', 'referral']

        users_data = []
        for i in range(1, 10001):
            signup_date = self._random_date('2022-01-01', '2024-01-01')
            last_login = self._random_date(signup_date, '2024-12-01')
            total_spent = round(random.uniform(0, 2000), 2)

            users_data.append((
                i,
                f"User {i}",
                f"user{i}@demo.com",
                random.randint(18, 70),
                random.choice(cities),
                random.choice(sources),
                signup_date,
                last_login,
                total_spent
            ))

        self.conn.executemany(
            "INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            users_data
        )

        # Products
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name VARCHAR(255),
                category_id INTEGER,
                price DECIMAL(10,2),
                cost DECIMAL(10,2),
                inventory_count INTEGER,
                rating DECIMAL(3,2),
                created_at TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
            )
        """)

        products_data = []
        for i in range(1, 1001):  # 1000 products
            category_id = random.randint(1, 7)
            price = round(random.uniform(10, 500), 2)
            cost = round(price * random.uniform(0.3, 0.7), 2)  # 30-70% margin

            products_data.append((
                i,
                f"Product {i}",
                category_id,
                price,
                cost,
                random.randint(0, 1000),
                round(random.uniform(3.0, 5.0), 2),
                self._random_date('2022-01-01', '2024-01-01')
            ))

        self.conn.executemany(
            "INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            products_data
        )

        # Orders
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                status VARCHAR(50),
                total_amount DECIMAL(10,2),
                shipping_cost DECIMAL(10,2),
                tax_amount DECIMAL(10,2),
                created_at TIMESTAMP,
                shipped_at TIMESTAMP,
                delivered_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'returned']
        orders_data = []

        for i in range(1, 50001):  # 50,000 orders
            user_id = random.randint(1, 10000)
            status = random.choice(statuses)
            total_amount = round(random.uniform(20, 800), 2)
            shipping_cost = round(random.uniform(5, 25), 2)
            tax_amount = round(total_amount * 0.08, 2)

            created_at = self._random_date('2023-01-01', '2024-12-01')
            shipped_at = None
            delivered_at = None

            if status in ['shipped', 'delivered']:
                shipped_at = self._add_days(created_at, random.randint(1, 3))
                if status == 'delivered':
                    delivered_at = self._add_days(shipped_at, random.randint(1, 7))

            orders_data.append((
                i, user_id, status, total_amount, shipping_cost, tax_amount,
                created_at, shipped_at, delivered_at
            ))

        self.conn.executemany(
            "INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            orders_data
        )

        # Order Items
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY,
                order_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                price_per_item DECIMAL(10,2),
                total_price DECIMAL(10,2),
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        order_items_data = []
        item_id = 1

        for order_id in range(1, 50001):
            # Each order has 1-5 items
            num_items = random.randint(1, 5)

            for _ in range(num_items):
                product_id = random.randint(1, 1000)
                quantity = random.randint(1, 3)
                price_per_item = round(random.uniform(10, 200), 2)
                total_price = price_per_item * quantity

                order_items_data.append((
                    item_id, order_id, product_id, quantity,
                    price_per_item, total_price
                ))
                item_id += 1

        self.conn.executemany(
            "INSERT OR REPLACE INTO order_items VALUES (?, ?, ?, ?, ?, ?)",
            order_items_data
        )

        # Reviews
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                product_id INTEGER,
                rating INTEGER,
                review_text TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_users_city ON users(city)",
            "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)",
            "CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id)"
        ]

        for idx in indexes:
            self.conn.execute(idx)

    def _create_saas_data(self):
        """Create realistic SaaS dataset."""

        # Users
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email VARCHAR(255),
                company_name VARCHAR(255),
                company_size VARCHAR(50),
                role VARCHAR(100),
                plan_type VARCHAR(50),
                created_at TIMESTAMP,
                last_active TIMESTAMP,
                is_active BOOLEAN
            )
        """)

        # Generate 5,000 SaaS users
        companies = ['TechCorp', 'StartupInc', 'BigCorp', 'MediumCo', 'SmallBiz']
        company_sizes = ['startup', 'small', 'medium', 'large', 'enterprise']
        roles = ['admin', 'user', 'manager', 'developer', 'analyst']
        plans = ['free', 'basic', 'pro', 'enterprise']

        users_data = []
        for i in range(1, 5001):
            created_at = self._random_date('2022-01-01', '2024-01-01')
            last_active = self._random_date(created_at, '2024-12-01')

            users_data.append((
                i,
                f"user{i}@{random.choice(companies).lower()}.com",
                f"{random.choice(companies)} {random.randint(1, 999)}",
                random.choice(company_sizes),
                random.choice(roles),
                random.choice(plans),
                created_at,
                last_active,
                random.choice([True, True, True, False])  # 75% active
            ))

        self.conn.executemany(
            "INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            users_data
        )

        # Subscriptions
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                plan_name VARCHAR(100),
                mrr DECIMAL(10,2),
                status VARCHAR(50),
                started_at TIMESTAMP,
                cancelled_at TIMESTAMP,
                trial_end TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        plan_pricing = {
            'free': 0,
            'basic': 29,
            'pro': 99,
            'enterprise': 299
        }

        statuses = ['active', 'active', 'active', 'cancelled', 'trialing']
        subscriptions_data = []

        for i in range(1, 4001):  # Not all users have paid subscriptions
            user_id = random.randint(1, 5000)
            plan = random.choice(['basic', 'pro', 'enterprise'])
            mrr = plan_pricing[plan]
            status = random.choice(statuses)

            started_at = self._random_date('2022-01-01', '2024-01-01')
            cancelled_at = None
            trial_end = None

            if status == 'cancelled':
                cancelled_at = self._add_days(started_at, random.randint(30, 365))
            elif status == 'trialing':
                trial_end = self._add_days(started_at, 14)

            subscriptions_data.append((
                i, user_id, plan, mrr, status, started_at, cancelled_at, trial_end
            ))

        self.conn.executemany(
            "INSERT OR REPLACE INTO subscriptions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            subscriptions_data
        )

        # Usage Events
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_events (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                event_type VARCHAR(100),
                feature_name VARCHAR(100),
                session_id VARCHAR(255),
                created_at TIMESTAMP,
                properties JSON,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Generate usage events
        event_types = ['login', 'feature_used', 'file_uploaded', 'report_generated', 'settings_changed']
        features = ['dashboard', 'reports', 'analytics', 'exports', 'integrations', 'api', 'collaboration']

        events_data = []
        for i in range(1, 100001):  # 100k events
            user_id = random.randint(1, 5000)
            event_type = random.choice(event_types)
            feature = random.choice(features)
            session_id = f"session_{random.randint(1000000, 9999999)}"
            created_at = self._random_date('2023-01-01', '2024-12-01')

            properties = json.dumps({
                'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge']),
                'platform': random.choice(['Web', 'Mobile', 'Desktop']),
                'duration_seconds': random.randint(10, 3600)
            })

            events_data.append((
                i, user_id, event_type, feature, session_id, created_at, properties
            ))

        self.conn.executemany(
            "INSERT OR REPLACE INTO usage_events VALUES (?, ?, ?, ?, ?, ?, ?)",
            events_data
        )

        # Billing
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS billing (
                id INTEGER PRIMARY KEY,
                subscription_id INTEGER,
                amount DECIMAL(10,2),
                status VARCHAR(50),
                billing_date TIMESTAMP,
                paid_date TIMESTAMP,
                invoice_number VARCHAR(100),
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
            )
        """)

        # Support Tickets
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                subject VARCHAR(255),
                status VARCHAR(50),
                priority VARCHAR(50),
                category VARCHAR(100),
                created_at TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create indexes
        saas_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_company_size ON users(company_size)",
            "CREATE INDEX IF NOT EXISTS idx_users_plan_type ON users(plan_type)",
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status)",
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_started_at ON subscriptions(started_at)",
            "CREATE INDEX IF NOT EXISTS idx_usage_events_user_id ON usage_events(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_usage_events_created_at ON usage_events(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_usage_events_feature_name ON usage_events(feature_name)"
        ]

        for idx in saas_indexes:
            self.conn.execute(idx)

    def _generate_learning_patterns(self, company_type: str) -> Dict[str, Any]:
        """Generate realistic learning patterns for the demo."""

        patterns = {
            "table_relationships": {},
            "performance_patterns": {},
            "team_preferences": {},
            "common_joins": [],
            "optimization_hints": []
        }

        if company_type == "ecommerce":
            patterns.update({
                "table_relationships": {
                    "users_orders": {"frequency": 156, "confidence": 0.95},
                    "orders_order_items": {"frequency": 142, "confidence": 0.98},
                    "products_order_items": {"frequency": 134, "confidence": 0.92},
                    "users_reviews": {"frequency": 67, "confidence": 0.85}
                },
                "performance_patterns": {
                    "fast_patterns": [
                        {"pattern": "user_id = ?", "avg_time": "45ms", "frequency": 89},
                        {"pattern": "status = 'delivered'", "avg_time": "67ms", "frequency": 76},
                        {"pattern": "created_at >= CURRENT_DATE - 7", "avg_time": "123ms", "frequency": 54}
                    ],
                    "slow_patterns": [
                        {"pattern": "SELECT * FROM orders WHERE created_at < '2022-01-01'", "avg_time": "2300ms", "frequency": 23},
                        {"pattern": "JOIN without user_id filter", "avg_time": "1800ms", "frequency": 15}
                    ]
                },
                "team_preferences": {
                    "sales": {
                        "favorite_tables": ["orders", "users", "order_items"],
                        "common_metrics": ["revenue", "conversion_rate", "avg_order_value"],
                        "time_periods": ["monthly", "quarterly"],
                        "typical_filters": ["status = 'delivered'", "created_at >= DATE_TRUNC('month', CURRENT_DATE)"]
                    },
                    "marketing": {
                        "favorite_tables": ["users", "orders", "reviews"],
                        "common_metrics": ["acquisition", "retention", "ltv"],
                        "time_periods": ["daily", "weekly"],
                        "typical_filters": ["signup_source", "city", "age BETWEEN ? AND ?"]
                    },
                    "finance": {
                        "favorite_tables": ["orders", "products", "order_items"],
                        "common_metrics": ["profit_margin", "cost_analysis", "forecasting"],
                        "time_periods": ["monthly", "quarterly"],
                        "typical_filters": ["status IN ('delivered', 'shipped')", "total_amount > 100"]
                    }
                },
                "common_joins": [
                    {
                        "tables": ["users", "orders"],
                        "join_condition": "users.id = orders.user_id",
                        "frequency": 156,
                        "avg_performance": "180ms"
                    },
                    {
                        "tables": ["orders", "order_items"],
                        "join_condition": "orders.id = order_items.order_id",
                        "frequency": 142,
                        "avg_performance": "145ms"
                    },
                    {
                        "tables": ["products", "order_items"],
                        "join_condition": "products.id = order_items.product_id",
                        "frequency": 134,
                        "avg_performance": "167ms"
                    }
                ]
            })

        elif company_type == "saas":
            patterns.update({
                "table_relationships": {
                    "users_subscriptions": {"frequency": 134, "confidence": 0.92},
                    "users_usage_events": {"frequency": 189, "confidence": 0.96},
                    "subscriptions_billing": {"frequency": 67, "confidence": 0.89},
                    "users_support_tickets": {"frequency": 43, "confidence": 0.78}
                },
                "performance_patterns": {
                    "fast_patterns": [
                        {"pattern": "user_id = ?", "avg_time": "35ms", "frequency": 123},
                        {"pattern": "status = 'active'", "avg_time": "56ms", "frequency": 98},
                        {"pattern": "plan_name = 'pro'", "avg_time": "42ms", "frequency": 67}
                    ],
                    "slow_patterns": [
                        {"pattern": "SELECT * FROM usage_events WHERE created_at < '2023-01-01'", "avg_time": "3400ms", "frequency": 12},
                        {"pattern": "Complex aggregations without user_id filter", "avg_time": "2100ms", "frequency": 8}
                    ]
                },
                "team_preferences": {
                    "product": {
                        "favorite_tables": ["usage_events", "users", "subscriptions"],
                        "common_metrics": ["dau", "retention", "feature_adoption"],
                        "time_periods": ["daily", "weekly"],
                        "typical_filters": ["event_type = 'feature_used'", "is_active = true"]
                    },
                    "growth": {
                        "favorite_tables": ["users", "subscriptions", "billing"],
                        "common_metrics": ["mrr", "churn_rate", "expansion_revenue"],
                        "time_periods": ["monthly", "quarterly"],
                        "typical_filters": ["plan_name != 'free'", "status = 'active'"]
                    },
                    "support": {
                        "favorite_tables": ["support_tickets", "users", "subscriptions"],
                        "common_metrics": ["resolution_time", "satisfaction", "ticket_volume"],
                        "time_periods": ["daily", "weekly"],
                        "typical_filters": ["status IN ('open', 'in_progress')", "priority = 'high'"]
                    }
                },
                "common_joins": [
                    {
                        "tables": ["users", "subscriptions"],
                        "join_condition": "users.id = subscriptions.user_id",
                        "frequency": 134,
                        "avg_performance": "156ms"
                    },
                    {
                        "tables": ["users", "usage_events"],
                        "join_condition": "users.id = usage_events.user_id",
                        "frequency": 189,
                        "avg_performance": "234ms"
                    }
                ]
            })

        return patterns

    def _generate_query_history(self, company_type: str) -> List[Dict[str, Any]]:
        """Generate realistic query history for demo."""

        history = []

        if company_type == "ecommerce":
            # Sales team queries
            history.extend([
                {
                    "id": 1,
                    "sql": "SELECT DATE_TRUNC('month', created_at) as month, SUM(total_amount) as revenue FROM orders WHERE status = 'delivered' GROUP BY 1 ORDER BY 1 DESC",
                    "team": "sales",
                    "user": "Sarah Johnson",
                    "execution_time": 156,
                    "result_count": 24,
                    "timestamp": "2024-01-15 14:30:00",
                    "success": True,
                    "description": "Monthly revenue analysis"
                },
                {
                    "id": 2,
                    "sql": "SELECT u.city, COUNT(DISTINCT u.id) as customers, AVG(o.total_amount) as avg_order FROM users u JOIN orders o ON u.id = o.user_id WHERE o.created_at >= '2024-01-01' GROUP BY u.city ORDER BY customers DESC LIMIT 10",
                    "team": "sales",
                    "user": "Mike Chen",
                    "execution_time": 234,
                    "result_count": 10,
                    "timestamp": "2024-01-15 10:15:00",
                    "success": True,
                    "description": "Customer distribution by city"
                },
                {
                    "id": 3,
                    "sql": "SELECT p.name, SUM(oi.quantity) as units_sold, SUM(oi.total_price) as revenue FROM products p JOIN order_items oi ON p.id = oi.product_id JOIN orders o ON oi.order_id = o.id WHERE o.status = 'delivered' AND o.created_at >= CURRENT_DATE - INTERVAL '30 days' GROUP BY p.id, p.name ORDER BY revenue DESC LIMIT 20",
                    "team": "sales",
                    "user": "Sarah Johnson",
                    "execution_time": 298,
                    "result_count": 20,
                    "timestamp": "2024-01-14 16:45:00",
                    "success": True,
                    "description": "Top selling products last 30 days"
                }
            ])

            # Marketing team queries
            history.extend([
                {
                    "id": 4,
                    "sql": "SELECT signup_source, COUNT(*) as new_users, AVG(total_spent) as avg_ltv FROM users WHERE created_at >= CURRENT_DATE - INTERVAL '90 days' GROUP BY signup_source ORDER BY new_users DESC",
                    "team": "marketing",
                    "user": "Jessica Liu",
                    "execution_time": 145,
                    "result_count": 5,
                    "timestamp": "2024-01-15 09:20:00",
                    "success": True,
                    "description": "Acquisition channel performance"
                },
                {
                    "id": 5,
                    "sql": "SELECT DATE_TRUNC('week', u.created_at) as week, u.signup_source, COUNT(*) as signups FROM users u WHERE u.created_at >= CURRENT_DATE - INTERVAL '12 weeks' GROUP BY 1, 2 ORDER BY 1 DESC, 3 DESC",
                    "team": "marketing",
                    "user": "David Rodriguez",
                    "execution_time": 178,
                    "result_count": 60,
                    "timestamp": "2024-01-14 14:10:00",
                    "success": True,
                    "description": "Weekly signup trends by source"
                }
            ])

            # Finance team queries
            history.extend([
                {
                    "id": 6,
                    "sql": "SELECT p.name, SUM(oi.total_price) as revenue, SUM(p.cost * oi.quantity) as cost, SUM(oi.total_price - p.cost * oi.quantity) as profit FROM products p JOIN order_items oi ON p.id = oi.product_id JOIN orders o ON oi.order_id = o.id WHERE o.status = 'delivered' GROUP BY p.id, p.name ORDER BY profit DESC LIMIT 25",
                    "team": "finance",
                    "user": "Robert Kim",
                    "execution_time": 456,
                    "result_count": 25,
                    "timestamp": "2024-01-15 11:30:00",
                    "success": True,
                    "description": "Product profitability analysis"
                }
            ])

            # Some failed queries for learning
            history.extend([
                {
                    "id": 7,
                    "sql": "SELECT * FROM orders WHERE created_at < '2020-01-01'",
                    "team": "sales",
                    "user": "New Analyst",
                    "execution_time": 15000,
                    "result_count": 0,
                    "timestamp": "2024-01-13 15:20:00",
                    "success": False,
                    "error": "Query timeout - too many rows scanned",
                    "description": "Failed query - no date limit"
                }
            ])

        elif company_type == "saas":
            # Product team queries
            history.extend([
                {
                    "id": 1,
                    "sql": "SELECT DATE_TRUNC('day', created_at) as day, COUNT(DISTINCT user_id) as dau FROM usage_events WHERE created_at >= CURRENT_DATE - INTERVAL '30 days' GROUP BY 1 ORDER BY 1",
                    "team": "product",
                    "user": "Alex Thompson",
                    "execution_time": 189,
                    "result_count": 30,
                    "timestamp": "2024-01-15 11:20:00",
                    "success": True,
                    "description": "Daily active users trend"
                },
                {
                    "id": 2,
                    "sql": "SELECT feature_name, COUNT(*) as usage_count, COUNT(DISTINCT user_id) as unique_users FROM usage_events WHERE event_type = 'feature_used' AND created_at >= CURRENT_DATE - INTERVAL '7 days' GROUP BY feature_name ORDER BY usage_count DESC",
                    "team": "product",
                    "user": "Sarah Kim",
                    "execution_time": 234,
                    "result_count": 7,
                    "timestamp": "2024-01-15 14:45:00",
                    "success": True,
                    "description": "Feature adoption analysis"
                }
            ])

            # Growth team queries
            history.extend([
                {
                    "id": 3,
                    "sql": "SELECT DATE_TRUNC('month', started_at) as month, plan_name, SUM(mrr) as total_mrr, COUNT(*) as new_subscriptions FROM subscriptions WHERE status = 'active' GROUP BY 1, 2 ORDER BY 1 DESC, 3 DESC",
                    "team": "growth",
                    "user": "Jennifer Walsh",
                    "execution_time": 145,
                    "result_count": 48,
                    "timestamp": "2024-01-15 09:30:00",
                    "success": True,
                    "description": "Monthly MRR by plan"
                },
                {
                    "id": 4,
                    "sql": "WITH cohorts AS (SELECT user_id, DATE_TRUNC('month', created_at) as cohort_month FROM users), retention AS (SELECT c.cohort_month, COUNT(DISTINCT ue.user_id) as retained_users FROM cohorts c JOIN usage_events ue ON c.user_id = ue.user_id WHERE ue.created_at >= c.cohort_month + INTERVAL '1 month' AND ue.created_at < c.cohort_month + INTERVAL '2 months' GROUP BY c.cohort_month) SELECT * FROM retention ORDER BY cohort_month DESC",
                    "team": "growth",
                    "user": "Mark Johnson",
                    "execution_time": 567,
                    "result_count": 24,
                    "timestamp": "2024-01-14 16:15:00",
                    "success": True,
                    "description": "User retention cohort analysis"
                }
            ])

        return history

    def _get_schema_info(self) -> Dict[str, Any]:
        """Get comprehensive schema information."""

        schema_info = {"tables": []}

        # Get all tables
        tables_result = self.conn.execute("SHOW TABLES").fetchall()

        for (table_name,) in tables_result:
            # Get column information
            columns_result = self.conn.execute(f"DESCRIBE {table_name}").fetchall()

            # Get row count
            count_result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            row_count = count_result[0] if count_result else 0

            columns = []
            for col_info in columns_result:
                columns.append({
                    "name": col_info[0],
                    "type": col_info[1],
                    "nullable": col_info[2] == "YES",
                    "primary_key": False  # DuckDB DESCRIBE doesn't show this easily
                })

            schema_info["tables"].append({
                "name": table_name,
                "type": "table",
                "row_count": row_count,
                "columns": columns
            })

        return schema_info

    def _random_date(self, start_date: str, end_date: str) -> str:
        """Generate random date between start and end."""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        time_between = end - start
        days_between = time_between.days
        random_days = random.randrange(days_between)

        random_date = start + timedelta(days=random_days)
        return random_date.isoformat()

    def _add_days(self, date_str: str, days: int) -> str:
        """Add days to a date string."""
        date_obj = datetime.fromisoformat(date_str)
        new_date = date_obj + timedelta(days=days)
        return new_date.isoformat()

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute query and return results."""
        try:
            start_time = datetime.now()
            result = self.conn.execute(query).fetchall()
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # Get column names
            columns = [desc[0] for desc in self.conn.description] if self.conn.description else []

            # Convert to list of dictionaries
            data = []
            for row in result:
                row_dict = {}
                for i, col in enumerate(columns):
                    row_dict[col] = row[i]
                data.append(row_dict)

            return {
                "success": True,
                "data": data,
                "columns": columns,
                "row_count": len(result),
                "execution_time": execution_time
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "columns": [],
                "row_count": 0,
                "execution_time": 0
            }

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()


def create_demo_workspace(company_type: str = "ecommerce") -> Dict[str, Any]:
    """Create a complete demo workspace."""

    # Ensure demo directory exists
    demo_dir = Path(settings.workspace_data_dir) / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)

    # Create database
    db_path = demo_dir / f"demo_{company_type}.duckdb"
    generator = DemoDataGenerator(str(db_path))

    # Set up workspace
    workspace_info = generator.setup_demo_workspace(company_type)

    # Save workspace info
    info_path = demo_dir / f"demo_{company_type}_info.json"
    with open(info_path, 'w') as f:
        json.dump(workspace_info, f, indent=2, default=str)

    return {
        **workspace_info,
        "info_file": str(info_path),
        "generator": generator
    }


if __name__ == "__main__":
    # CLI for creating demo workspaces
    import sys

    company_type = sys.argv[1] if len(sys.argv) > 1 else "ecommerce"

    print(f"Creating demo workspace for {company_type}...")
    workspace = create_demo_workspace(company_type)

    print(f"Demo workspace created successfully!")
    print(f"Database: {workspace['database_path']}")
    print(f"Info file: {workspace['info_file']}")
    print(f"Tables created: {len(workspace['schema_info']['tables'])}")

    # Show sample queries
    print("\nSample queries you can try:")
    for query in workspace['query_history'][:3]:
        print(f"- {query['description']}:")
        print(f"  {query['sql'][:80]}...")
        print()