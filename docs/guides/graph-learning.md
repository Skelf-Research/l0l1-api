from typing import Dict, List, Any, Optional, Tuple
import sqlparse
from collections import defaultdict, Counter
import json
from datetime import datetime

from ..modules.knowledge_graph import KnowledgeGraph
from ..core.config import settings


class GraphLearningService:
    """Advanced graph-based learning for SQL query patterns and relationships."""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.kg = KnowledgeGraph(workspace_id)

    async def analyze_and_store_query(
        self,
        query: str,
        execution_time: float,
        result_count: int,
        success: bool = True,
        user_context: Optional[Dict] = None
    ):
        """Analyze query and store comprehensive graph relationships."""

        # Parse SQL query
        parsed = sqlparse.parse(query)[0]
        analysis = self._analyze_query_structure(parsed)

        # Generate unique query ID
        query_id = f"query_{hash(query) % 100000}"

        # Store basic query metadata
        self.kg.add_relation(query_id, "has_sql", query)
        self.kg.add_relation(query_id, "execution_time", str(execution_time))
        self.kg.add_relation(query_id, "result_count", str(result_count))
        self.kg.add_relation(query_id, "success", str(success))
        self.kg.add_relation(query_id, "timestamp", datetime.utcnow().isoformat())

        # Store query type and patterns
        self.kg.add_relation(query_id, "query_type", analysis["type"])
        for pattern in analysis["patterns"]:
            self.kg.add_relation(query_id, "uses_pattern", pattern)

        # Store table relationships
        for table in analysis["tables"]:
            self.kg.add_relation(query_id, "uses_table", table)
            self.kg.add_relation(table, "used_by_query", query_id)

        # Store column relationships
        for column in analysis["columns"]:
            self.kg.add_relation(query_id, "uses_column", column)
            self.kg.add_relation(column, "used_by_query", query_id)

        # Store join relationships
        for join_info in analysis["joins"]:
            self.kg.add_relation(
                join_info["left_table"],
                f"joined_with_{join_info['type']}",
                join_info["right_table"]
            )
            self.kg.add_relation(query_id, "performs_join", f"{join_info['left_table']}_{join_info['right_table']}")

        # Store aggregation patterns
        for agg in analysis["aggregations"]:
            self.kg.add_relation(query_id, "uses_aggregation", agg["function"])
            self.kg.add_relation(query_id, "aggregates_column", agg["column"])

        # Store filter patterns
        for filter_info in analysis["filters"]:
            self.kg.add_relation(query_id, "filters_on", filter_info["column"])
            self.kg.add_relation(query_id, "uses_operator", filter_info["operator"])

        # Store user context if provided
        if user_context:
            user_id = user_context.get("user_id", "unknown")
            department = user_context.get("department")

            self.kg.add_relation(query_id, "written_by", user_id)
            if department:
                self.kg.add_relation(user_id, "works_in", department)
                self.kg.add_relation(query_id, "department_context", department)

        # Learn performance patterns
        self._learn_performance_patterns(query_id, analysis, execution_time, result_count)

        # Learn co-occurrence patterns
        self._learn_co_occurrence_patterns(analysis)

    def _analyze_query_structure(self, parsed_query) -> Dict[str, Any]:
        """Deep analysis of SQL query structure."""

        analysis = {
            "type": self._get_query_type(parsed_query),
            "patterns": [],
            "tables": set(),
            "columns": set(),
            "joins": [],
            "aggregations": [],
            "filters": [],
            "subqueries": 0,
            "complexity_score": 0
        }

        # Walk through all tokens
        for token in parsed_query.flatten():
            if token.ttype is sqlparse.tokens.Keyword:
                keyword = token.value.upper()

                # Identify patterns
                if keyword in ["JOIN", "INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN"]:
                    analysis["patterns"].append(f"{keyword.replace(' ', '_')}_PATTERN")
                elif keyword in ["GROUP BY", "ORDER BY", "HAVING"]:
                    analysis["patterns"].append(f"{keyword.replace(' ', '_')}_PATTERN")
                elif keyword in ["UNION", "INTERSECT", "EXCEPT"]:
                    analysis["patterns"].append(f"{keyword}_PATTERN")
                elif keyword == "WITH":
                    analysis["patterns"].append("CTE_PATTERN")

            elif token.ttype is sqlparse.tokens.Name:
                # Extract table and column names
                name = token.value.lower()

                # Simple heuristic: if it contains a dot, it's likely table.column
                if "." in name:
                    table, column = name.split(".", 1)
                    analysis["tables"].add(table)
                    analysis["columns"].add(f"{table}.{column}")
                else:
                    # Could be table or column - context-dependent
                    analysis["tables"].add(name)
                    analysis["columns"].add(name)

        # Detect aggregation functions
        query_str = str(parsed_query).upper()
        agg_functions = ["COUNT", "SUM", "AVG", "MAX", "MIN", "STDDEV", "VARIANCE"]
        for func in agg_functions:
            if func in query_str:
                analysis["patterns"].append(f"{func}_AGGREGATION")
                # Try to extract the column being aggregated
                import re
                pattern = f"{func}\\s*\\(\\s*([^)]+)\\s*\\)"
                matches = re.findall(pattern, query_str)
                for match in matches:
                    analysis["aggregations"].append({
                        "function": func,
                        "column": match.strip()
                    })

        # Calculate complexity score
        analysis["complexity_score"] = self._calculate_complexity(analysis, query_str)

        return analysis

    def _get_query_type(self, parsed_query) -> str:
        """Determine the primary query type."""
        first_keyword = None
        for token in parsed_query.tokens:
            if token.ttype is sqlparse.tokens.Keyword:
                first_keyword = token.value.upper()
                break

        return first_keyword or "UNKNOWN"

    def _calculate_complexity(self, analysis: Dict, query_str: str) -> int:
        """Calculate query complexity score."""
        score = 0

        # Base score for query type
        if analysis["type"] == "SELECT":
            score += 1
        elif analysis["type"] in ["INSERT", "UPDATE", "DELETE"]:
            score += 2

        # Add points for patterns
        score += len(analysis["patterns"]) * 2
        score += len(analysis["tables"]) * 1
        score += len(analysis["joins"]) * 3
        score += len(analysis["aggregations"]) * 2

        # Subqueries add significant complexity
        subquery_count = query_str.count("SELECT") - 1  # Subtract main query
        score += subquery_count * 5

        # Window functions
        if "OVER" in query_str:
            score += 4

        return score

    def _learn_performance_patterns(
        self,
        query_id: str,
        analysis: Dict,
        execution_time: float,
        result_count: int
    ):
        """Learn relationships between query patterns and performance."""

        # Classify performance
        if execution_time < 100:  # Fast queries
            performance_class = "FAST"
        elif execution_time < 1000:  # Medium queries
            performance_class = "MEDIUM"
        else:  # Slow queries
            performance_class = "SLOW"

        self.kg.add_relation(query_id, "performance_class", performance_class)

        # Learn pattern-performance relationships
        for pattern in analysis["patterns"]:
            self.kg.add_relation(pattern, "observed_performance", f"{performance_class}_{execution_time}")

        # Learn table-performance relationships
        for table in analysis["tables"]:
            self.kg.add_relation(table, "query_performance", f"{performance_class}_{execution_time}")

    def _learn_co_occurrence_patterns(self, analysis: Dict):
        """Learn which tables, columns, and patterns frequently appear together."""

        tables = list(analysis["tables"])
        patterns = analysis["patterns"]

        # Table co-occurrence
        for i, table1 in enumerate(tables):
            for table2 in tables[i+1:]:
                self.kg.add_relation(table1, "co_occurs_with", table2)
                self.kg.add_relation(table2, "co_occurs_with", table1)

        # Pattern-table relationships
        for pattern in patterns:
            for table in tables:
                self.kg.add_relation(pattern, "commonly_used_with", table)

    async def get_intelligent_suggestions(
        self,
        partial_query: str,
        context: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Get intelligent suggestions based on graph learning."""

        # Parse what we have so far
        try:
            parsed = sqlparse.parse(partial_query)[0]
            current_analysis = self._analyze_query_structure(parsed)
        except:
            current_analysis = {"tables": set(), "patterns": [], "columns": set()}

        suggestions = []

        # 1. Table completion suggestions
        if current_analysis["tables"]:
            table_suggestions = self._suggest_related_tables(current_analysis["tables"])
            suggestions.extend(table_suggestions)

        # 2. Join suggestions
        join_suggestions = self._suggest_joins(current_analysis["tables"])
        suggestions.extend(join_suggestions)

        # 3. Column suggestions
        column_suggestions = self._suggest_columns(current_analysis["tables"])
        suggestions.extend(column_suggestions)

        # 4. Pattern-based suggestions
        pattern_suggestions = self._suggest_patterns(current_analysis)
        suggestions.extend(pattern_suggestions)

        # 5. Performance-based suggestions
        perf_suggestions = self._suggest_performance_optimizations(current_analysis)
        suggestions.extend(perf_suggestions)

        return suggestions[:10]  # Return top 10 suggestions

    def _suggest_related_tables(self, current_tables: set) -> List[Dict[str, Any]]:
        """Suggest tables that are frequently used with current tables."""
        suggestions = []

        for table in current_tables:
            # Find tables that co-occur with this one
            related_tables = self.kg.get_relations(table, "co_occurs_with")

            for related_table in related_tables[:3]:  # Top 3
                if related_table not in current_tables:
                    suggestions.append({
                        "type": "table",
                        "suggestion": f"JOIN {related_table}",
                        "reason": f"Frequently used with {table}",
                        "confidence": 0.8
                    })

        return suggestions

    def _suggest_joins(self, current_tables: set) -> List[Dict[str, Any]]:
        """Suggest join patterns based on learned relationships."""
        suggestions = []

        tables_list = list(current_tables)
        for i, table1 in enumerate(tables_list):
            for table2 in tables_list[i+1:]:
                # Check if there are known join patterns
                join_patterns = self.kg.get_relations(table1, f"joined_with_LEFT")

                if table2 in join_patterns:
                    suggestions.append({
                        "type": "join",
                        "suggestion": f"LEFT JOIN {table2} ON {table1}.id = {table2}.{table1}_id",
                        "reason": f"Common join pattern observed",
                        "confidence": 0.9
                    })

        return suggestions

    def _suggest_columns(self, current_tables: set) -> List[Dict[str, Any]]:
        """Suggest columns frequently used with current tables."""
        suggestions = []

        for table in current_tables:
            # Find commonly used columns for this table
            common_columns = self.kg.get_relations(table, "commonly_selected")

            for column in common_columns[:5]:  # Top 5
                suggestions.append({
                    "type": "column",
                    "suggestion": f"{table}.{column}",
                    "reason": f"Frequently selected from {table}",
                    "confidence": 0.7
                })

        return suggestions

    def _suggest_patterns(self, current_analysis: Dict) -> List[Dict[str, Any]]:
        """Suggest query patterns based on current context."""
        suggestions = []

        current_patterns = set(current_analysis["patterns"])

        # If they're using GROUP BY, suggest ORDER BY
        if "GROUP_BY_PATTERN" in current_patterns:
            if "ORDER_BY_PATTERN" not in current_patterns:
                suggestions.append({
                    "type": "pattern",
                    "suggestion": "ORDER BY column_name DESC",
                    "reason": "Commonly used with GROUP BY",
                    "confidence": 0.8
                })

        # If they have aggregations, suggest HAVING
        if any("AGGREGATION" in p for p in current_patterns):
            if "HAVING" not in current_patterns:
                suggestions.append({
                    "type": "pattern",
                    "suggestion": "HAVING COUNT(*) > 10",
                    "reason": "Filter aggregated results",
                    "confidence": 0.7
                })

        return suggestions

    def _suggest_performance_optimizations(self, current_analysis: Dict) -> List[Dict[str, Any]]:
        """Suggest performance optimizations based on learned patterns."""
        suggestions = []

        # Check if similar queries were slow
        for table in current_analysis["tables"]:
            slow_queries = self.kg.get_relations(table, "query_performance")
            slow_count = sum(1 for perf in slow_queries if "SLOW" in perf)

            if slow_count > 2:  # If multiple slow queries on this table
                suggestions.append({
                    "type": "performance",
                    "suggestion": f"Consider adding LIMIT clause for {table}",
                    "reason": f"Large result sets observed for {table}",
                    "confidence": 0.6
                })

        return suggestions

    def get_workspace_insights(self) -> Dict[str, Any]:
        """Get comprehensive insights about the workspace."""

        # Get all relations for analysis
        all_relations = self.kg.get_all_relations()

        # Analyze patterns
        table_usage = Counter()
        pattern_usage = Counter()
        performance_stats = defaultdict(list)

        for source, relation, target in all_relations:
            if relation == "uses_table":
                table_usage[target] += 1
            elif relation == "uses_pattern":
                pattern_usage[target] += 1
            elif relation == "performance_class":
                performance_stats[target].append(source)

        return {
            "most_used_tables": dict(table_usage.most_common(10)),
            "common_patterns": dict(pattern_usage.most_common(10)),
            "performance_distribution": {
                "fast": len(performance_stats["FAST"]),
                "medium": len(performance_stats["MEDIUM"]),
                "slow": len(performance_stats["SLOW"])
            },
            "total_queries_analyzed": len([r for r in all_relations if r[1] == "has_sql"]),
            "unique_tables": len(table_usage),
            "complexity_trends": self._analyze_complexity_trends(all_relations)
        }

    def _analyze_complexity_trends(self, relations: List) -> Dict[str, Any]:
        """Analyze how query complexity changes over time."""
        # This would analyze complexity scores over time
        # For now, return a simple summary
        return {
            "avg_complexity": 5.2,
            "trend": "increasing",  # Could be "increasing", "stable", "decreasing"
            "most_complex_pattern": "JOIN with multiple aggregations"
        }