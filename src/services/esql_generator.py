"""
ES|QL Query Generator Service
Generates ES|QL queries for demo scenarios
"""

import logging
from typing import Dict, List
import json

logger = logging.getLogger(__name__)


class ESQLGenerator:
    """Generate ES|QL queries for demo scenarios"""

    def __init__(self):
        self.query_templates = {
            "simple_aggregation": """FROM {index}
| STATS count = COUNT(*),
        avg_value = AVG(value),
        max_value = MAX(value)
| SORT count DESC""",

            "time_series_aggregation": """FROM {index}
| EVAL time_bucket = DATE_TRUNC(1 hour, timestamp)
| STATS count = COUNT(*),
        avg_value = AVG(value)
  BY time_bucket
| SORT time_bucket ASC""",

            "top_entities": """FROM {index}
| STATS total = SUM(value),
        count = COUNT(*)
  BY {group_field}
| SORT total DESC
| LIMIT 10""",

            "filtering_with_calc": """FROM {index}
| WHERE status == "Active"
| EVAL efficiency = TO_DOUBLE(success_count) / total_count * 100
| STATS avg_efficiency = AVG(efficiency),
        total_events = COUNT(*)
  BY type
| WHERE avg_efficiency > 50
| SORT avg_efficiency DESC""",

            "join_pattern": """FROM {index1}
| LOOKUP JOIN {index2} ON entity_id
| STATS combined_value = SUM(value),
        entity_count = COUNT_DISTINCT(entity_id)
  BY type, status
| SORT combined_value DESC""",

            "trend_analysis": """FROM {index}
| EVAL month = DATE_TRUNC(1 month, timestamp)
| STATS monthly_total = SUM(value),
        monthly_avg = AVG(value),
        event_count = COUNT(*)
  BY month
| SORT month ASC""",

            "percentile_analysis": """FROM {index}
| STATS p50 = PERCENTILE(value, 50),
        p95 = PERCENTILE(value, 95),
        p99 = PERCENTILE(value, 99),
        max_value = MAX(value)
| EVAL p95_to_p50_ratio = TO_DOUBLE(p95) / p50""",

            "complex_filtering": """FROM {index}
| WHERE timestamp >= NOW() - 7 days
| EVAL day_of_week = DATE_FORMAT(timestamp, "EEEE")
| STATS daily_avg = AVG(value),
        daily_max = MAX(value),
        event_count = COUNT(*)
  BY day_of_week
| SORT daily_avg DESC"""
        }

    def generate_queries(self, scenario: Dict, datasets: Dict) -> List[Dict]:
        """
        Generate ES|QL queries for a scenario

        Args:
            scenario: Scenario configuration
            datasets: Dictionary of dataset configurations

        Returns:
            List of query configurations
        """
        logger.info(f"Generating queries for scenario: {scenario.get('name', 'Unknown')}")

        queries = []
        dataset_names = list(datasets.keys())

        # Generate queries based on dataset types
        for i, dataset_name in enumerate(dataset_names):
            dataset = datasets[dataset_name]

            # Simple aggregation for all datasets
            queries.append(self._create_query(
                name=f"Summary Statistics for {dataset_name}",
                description=f"Basic statistics and counts for {dataset_name}",
                esql=self._fill_template("simple_aggregation", {"index": dataset_name}),
                complexity="simple"
            ))

            # Time-based queries for datasets with timestamps
            if self._has_timestamp_field(dataset):
                queries.append(self._create_query(
                    name=f"Trend Analysis for {dataset_name}",
                    description=f"Analyze trends over time in {dataset_name}",
                    esql=self._fill_template("trend_analysis", {"index": dataset_name}),
                    complexity="medium"
                ))

            # Top entities query if there's a grouping field
            if self._has_grouping_field(dataset):
                group_field = self._get_grouping_field(dataset)
                queries.append(self._create_query(
                    name=f"Top {group_field} in {dataset_name}",
                    description=f"Find top performing {group_field}",
                    esql=self._fill_template("top_entities", {
                        "index": dataset_name,
                        "group_field": group_field
                    }),
                    complexity="simple"
                ))

        # Add join queries if there are relationships
        relationships = scenario.get("relationships", [])
        for relationship in relationships[:2]:  # Limit to 2 join queries
            if "->" in relationship:
                source, target = relationship.split("->")
                source = source.strip()
                target = target.strip()

                if source in dataset_names and target in dataset_names:
                    queries.append(self._create_query(
                        name=f"Join Analysis: {source} with {target}",
                        description=f"Analyze relationships between {source} and {target}",
                        esql=f"""FROM {target}
| LOOKUP JOIN {source} ON {source}_id
| STATS combined_count = COUNT(*),
        unique_{source} = COUNT_DISTINCT({source}_id)
| SORT combined_count DESC""",
                        complexity="complex"
                    ))

        # Add percentile analysis for metrics
        for dataset_name in dataset_names:
            if "metric" in dataset_name.lower() or "performance" in dataset_name.lower():
                queries.append(self._create_query(
                    name=f"Percentile Analysis for {dataset_name}",
                    description=f"Statistical distribution analysis",
                    esql=self._fill_template("percentile_analysis", {"index": dataset_name}),
                    complexity="medium"
                ))

        # Limit to 8 queries total
        queries = queries[:8]

        logger.info(f"Generated {len(queries)} queries")
        return queries

    def _create_query(self, name: str, description: str, esql: str, complexity: str = "medium") -> Dict:
        """Create a query configuration"""
        return {
            "id": name.lower().replace(" ", "_"),
            "name": name,
            "description": description,
            "esql": esql,
            "complexity": complexity,
            "parameters": self._extract_parameters(esql)
        }

    def _fill_template(self, template_name: str, values: Dict) -> str:
        """Fill a query template with values"""
        template = self.query_templates.get(template_name, "")
        try:
            return template.format(**values)
        except KeyError as e:
            logger.error(f"Missing template value: {e}")
            return template

    def _extract_parameters(self, esql: str) -> List[Dict]:
        """Extract parameters from ES|QL query"""
        parameters = []

        # Look for parameter placeholders (simplified)
        if "?" in esql:
            # Count question marks as parameters
            param_count = esql.count("?")
            for i in range(param_count):
                parameters.append({
                    "name": f"param{i+1}",
                    "type": "string",
                    "required": False
                })

        return parameters

    def _has_timestamp_field(self, dataset) -> bool:
        """Check if dataset has timestamp field"""
        if hasattr(dataset, 'columns'):
            return any('time' in col.lower() or 'date' in col.lower() for col in dataset.columns)
        return True  # Assume it has timestamp for now

    def _has_grouping_field(self, dataset) -> bool:
        """Check if dataset has fields suitable for grouping"""
        if hasattr(dataset, 'columns'):
            return any(col in ['type', 'status', 'category', 'region'] for col in dataset.columns)
        return True

    def _get_grouping_field(self, dataset) -> str:
        """Get the best grouping field from dataset"""
        if hasattr(dataset, 'columns'):
            for field in ['type', 'status', 'category', 'region']:
                if field in dataset.columns:
                    return field
        return "type"  # Default

    def validate_query(self, esql: str) -> bool:
        """
        Basic validation of ES|QL query syntax

        Args:
            esql: ES|QL query string

        Returns:
            True if query appears valid
        """
        # Basic syntax checks
        required_keywords = ["FROM"]
        esql_upper = esql.upper()

        for keyword in required_keywords:
            if keyword not in esql_upper:
                logger.error(f"Missing required keyword: {keyword}")
                return False

        # Check for common issues
        if "STATS" in esql_upper and "BY" not in esql_upper:
            logger.warning("STATS without BY clause - will return single row")

        # Check for division without TO_DOUBLE
        if "/" in esql and "TO_DOUBLE" not in esql_upper:
            logger.warning("Division without TO_DOUBLE may cause integer division issues")

        return True

    def optimize_query(self, esql: str) -> str:
        """
        Apply optimizations to ES|QL query

        Args:
            esql: Original query

        Returns:
            Optimized query
        """
        # Add LIMIT if not present and query might return many rows
        if "LIMIT" not in esql.upper() and "STATS" not in esql.upper():
            esql += "\n| LIMIT 1000"

        # Ensure TO_DOUBLE for division operations
        if "/" in esql and "TO_DOUBLE" not in esql.upper():
            # Simple replacement (in production, would parse properly)
            esql = esql.replace("/", ") / TO_DOUBLE(")
            esql = esql.replace("TO_DOUBLE(TO_DOUBLE(", "TO_DOUBLE(")  # Clean up doubles

        return esql