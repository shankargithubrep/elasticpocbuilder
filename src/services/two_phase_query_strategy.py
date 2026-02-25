"""
Two-Phase Query Strategy Generator
Generates query strategies in two phases to avoid truncation issues
"""

from typing import Dict, List, Any, Optional
import json
import logging
from dataclasses import dataclass, asdict
import concurrent.futures
from threading import Lock

logger = logging.getLogger(__name__)

# Dataset size ranges by preference (per-dataset limits)
SIZE_RANGES = {
    'small': {'timeseries': '1000-3000', 'reference': '50-200'},
    'medium': {'timeseries': '5000-10000', 'reference': '200-1000'},
    'large': {'timeseries': '20000-50000', 'reference': '1000-5000'}
}


@dataclass
class QueryOutline:
    """Lightweight query outline for Phase 1"""
    name: str
    query_type: str  # 'scripted' or 'parameterized'
    category: str  # 'analytics', 'anomaly_detection', 'search', etc.
    complexity: str  # 'simple', 'medium', 'complex'
    primary_dataset: str
    uses_lookup_join: bool
    pain_point_summary: str  # Brief 1-line summary


class TwoPhaseQueryStrategyGenerator:
    """Generates query strategies in two phases to avoid truncation"""

    def __init__(self, llm_client, max_concurrent: int = 3):
        """Initialize with LLM client

        Args:
            llm_client: Anthropic Claude client
            max_concurrent: Maximum concurrent Phase 2 enrichments
        """
        self.llm_client = llm_client
        self.max_concurrent = max_concurrent
        self._lock = Lock()

    def generate_strategy(self, context: Dict) -> Dict:
        """Generate complete query strategy using two-phase approach

        Args:
            context: Customer context with pain_points, use_cases, etc.

        Returns:
            Complete strategy dict with datasets, queries, relationships
        """
        logger.info(f"Starting two-phase strategy generation for {context.get('company_name')}")

        # Extract dataset size preference (default to 'medium' if not specified)
        size_preference = context.get('dataset_size_preference', 'medium')
        logger.info(f"Using dataset size preference: {size_preference}")

        # Phase 1: Generate lightweight query outlines
        query_outlines = self._phase1_generate_outlines(context)
        logger.info(f"Phase 1 complete: {len(query_outlines)} query outlines generated")

        # Phase 2: Enrich each query in parallel
        enriched_queries = self._phase2_enrich_queries(context, query_outlines)
        logger.info(f"Phase 2 complete: {len(enriched_queries)} queries enriched")

        # Phase 3: Generate dataset requirements from enriched queries
        datasets = self._generate_dataset_requirements(enriched_queries, size_preference)

        # Phase 4: Generate relationships and field mappings
        relationships, field_mappings = self._generate_relationships(datasets, enriched_queries)

        # Assemble final strategy
        strategy = {
            "datasets": datasets,
            "queries": enriched_queries,
            "relationships": relationships,
            "field_mappings": field_mappings
        }

        return strategy

    def _phase1_generate_outlines(self, context: Dict) -> List[QueryOutline]:
        """Phase 1: Generate lightweight query outlines

        This phase generates ONLY the structure, no detailed ES|QL or descriptions
        """
        prompt = f"""You are an ES|QL expert designing query outlines for {context.get('company_name')}.

**Context:**
- Company: {context.get('company_name')}
- Department: {context.get('department')}
- Industry: {context.get('industry')}
- Pain Points: {json.dumps(context.get('pain_points', [])[:3])}
- Demo Type: {context.get('demo_type', 'analytics')}

**Task**: Generate EXACTLY 7 query outlines (just the structure, not the full queries).

For each query, provide ONLY:
- name: Short descriptive name (max 10 words)
- query_type: "scripted" or "parameterized"
- category: One of: "analytics", "anomaly_detection", "search", "enrichment", "trending"
- complexity: "simple", "medium", or "complex"
- primary_dataset: Main dataset name (e.g., "transactions", "events", "logs")
- uses_lookup_join: true/false
- pain_point_summary: ONE sentence describing the pain point it addresses

**🎯 IMPORTANT: Do NOT specify row counts or dataset sizes in this phase.**

This is just the outline phase. Row counts will be determined automatically in Phase 2 based on the {size_preference} preference. Focus only on query structure and pain points.

**Output Format (JSON only):**
```json
{{
  "queries": [
    {{
      "name": "Revenue Anomaly Detection",
      "query_type": "scripted",
      "category": "anomaly_detection",
      "complexity": "medium",
      "primary_dataset": "sales_transactions",
      "uses_lookup_join": true,
      "pain_point_summary": "Cannot quickly identify abnormal sales patterns"
    }}
  ]
}}
```

Generate ONLY the JSON with 7 query outlines. Keep descriptions brief."""

        response = self.llm_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,  # Much smaller - won't truncate
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        result = self._extract_json(response.content[0].text)

        # Convert to QueryOutline objects
        outlines = []
        for q in result.get('queries', []):
            outlines.append(QueryOutline(
                name=q['name'],
                query_type=q['query_type'],
                category=q['category'],
                complexity=q['complexity'],
                primary_dataset=q['primary_dataset'],
                uses_lookup_join=q['uses_lookup_join'],
                pain_point_summary=q['pain_point_summary']
            ))

        return outlines

    def _phase2_enrich_queries(self, context: Dict, outlines: List[QueryOutline]) -> List[Dict]:
        """Phase 2: Enrich each query outline with full details (parallel)"""
        enriched_queries = []

        # Use ThreadPoolExecutor for concurrent enrichment
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            # Submit all enrichment tasks
            future_to_outline = {}
            for i, outline in enumerate(outlines):
                future = executor.submit(self._enrich_single_query, context, outline, i)
                future_to_outline[future] = outline

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_outline):
                outline = future_to_outline[future]
                try:
                    enriched = future.result(timeout=60)
                    with self._lock:
                        enriched_queries.append(enriched)
                    logger.info(f"Enriched query: {outline.name}")
                except Exception as e:
                    logger.error(f"Failed to enrich query {outline.name}: {e}")
                    # Add a minimal version so we don't lose the query
                    with self._lock:
                        enriched_queries.append({
                            "name": outline.name,
                            "pain_point": outline.pain_point_summary,
                            "description": f"Query to address: {outline.pain_point_summary}",
                            "esql_features": ["STATS", "WHERE"],
                            "required_datasets": [outline.primary_dataset],
                            "required_fields": {outline.primary_dataset: ["@timestamp", "id"]},
                            "complexity": outline.complexity,
                            "esql_query": "FROM data | STATS count = COUNT(*)"
                        })

        return enriched_queries

    def _enrich_single_query(self, context: Dict, outline: QueryOutline, index: int) -> Dict:
        """Enrich a single query outline with full details

        This is called in parallel for each query
        """
        # Read ES|QL skill snippet
        esql_guidance = self._get_esql_guidance_snippet(outline.category)

        prompt = f"""You are enriching a query outline for {context.get('company_name')}.

**Query Outline:**
- Name: {outline.name}
- Type: {outline.query_type}
- Category: {outline.category}
- Complexity: {outline.complexity}
- Primary Dataset: {outline.primary_dataset}
- Uses LOOKUP JOIN: {outline.uses_lookup_join}
- Pain Point: {outline.pain_point_summary}

**Context:**
- Industry: {context.get('industry')}
- Department: {context.get('department')}

**ES|QL Guidance:**
{esql_guidance}

**Task**: Generate the COMPLETE query details including the full ES|QL query.

**Requirements:**
1. ES|QL query must be syntactically correct
2. Use appropriate ES|QL features for the category ({outline.category})
3. If uses_lookup_join=true, include a LOOKUP JOIN
4. Field names should be specific to the industry/use case
5. Include @timestamp for timeseries data

**Output Format (JSON only):**
```json
{{
  "name": "{outline.name}",
  "pain_point": "{outline.pain_point_summary}",
  "description": "Detailed description of what the query does and how it helps",
  "esql_features": ["STATS", "INLINESTATS", "EVAL", etc.],
  "required_datasets": ["{outline.primary_dataset}", "reference_data_if_needed"],
  "required_fields": {{
    "{outline.primary_dataset}": ["@timestamp", "field1", "field2", etc.]
  }},
  "complexity": "{outline.complexity}",
  "esql_query": "Complete ES|QL query here"
}}
```

Generate ONLY the JSON for this single query:"""

        response = self.llm_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,  # Safe size for single query
            temperature=0.6,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse and return
        result = self._extract_json(response.content[0].text)
        return result

    def _generate_dataset_requirements(self, queries: List[Dict], size_preference: str = 'medium') -> List[Dict]:
        """Generate dataset requirements from enriched queries

        Args:
            queries: List of enriched query dicts
            size_preference: Dataset size preference - 'small', 'medium', or 'large' (default 'medium')

        Returns:
            List of dataset requirement dicts
        """
        datasets = {}

        # Get size ranges for the preference
        size_ranges = SIZE_RANGES.get(size_preference, SIZE_RANGES['medium'])
        reference_range = size_ranges['reference']
        timeseries_range = size_ranges['timeseries']

        for query in queries:
            for dataset_name in query.get('required_datasets', []):
                if dataset_name not in datasets:
                    # Determine dataset type based on usage
                    uses_lookup = any(
                        dataset_name in q.get('esql_query', '') and 'LOOKUP JOIN' in q.get('esql_query', '')
                        for q in queries
                    )

                    datasets[dataset_name] = {
                        "name": dataset_name,
                        "type": "reference" if uses_lookup else "timeseries",
                        "index_mode": "lookup" if uses_lookup else "data_stream",
                        "row_count": reference_range if uses_lookup else timeseries_range,
                        "required_fields": {},
                        "relationships": [],
                        "semantic_fields": []
                    }

                # Merge required fields
                if dataset_name in query.get('required_fields', {}):
                    for field in query['required_fields'][dataset_name]:
                        if field not in datasets[dataset_name]['required_fields']:
                            # Infer field type
                            field_type = self._infer_field_type(field)
                            datasets[dataset_name]['required_fields'][field] = field_type

        return list(datasets.values())

    def _generate_relationships(self, datasets: List[Dict], queries: List[Dict]) -> tuple:
        """Generate relationships and field mappings from datasets and queries"""
        relationships = []
        field_mappings = {}

        # Analyze queries for LOOKUP JOIN patterns
        for query in queries:
            esql = query.get('esql_query', '')
            if 'LOOKUP JOIN' in esql:
                # Extract JOIN pattern (simplified - could use regex)
                # Pattern: "LOOKUP JOIN reference_table ON join_field"
                import re
                join_pattern = r'LOOKUP JOIN\s+(\w+)\s+ON\s+(\w+)'
                matches = re.findall(join_pattern, esql)

                for ref_table, join_field in matches:
                    # Find primary dataset (FROM clause)
                    from_pattern = r'FROM\s+(\w+)'
                    from_match = re.search(from_pattern, esql)
                    if from_match:
                        primary_table = from_match.group(1)

                        relationships.append({
                            "from": primary_table,
                            "to": ref_table,
                            "type": "many-to-one",
                            "join_field": join_field
                        })

                        # Add field mapping
                        field_mappings[f"{primary_table}.{join_field}"] = f"{ref_table}.{join_field}"

        return relationships, field_mappings

    def _infer_field_type(self, field_name: str) -> str:
        """Infer field type from name"""
        if field_name == "@timestamp":
            return "date"
        elif "_id" in field_name or field_name.endswith("_id"):
            return "keyword"
        elif "amount" in field_name or "price" in field_name or "cost" in field_name:
            return "float"
        elif "count" in field_name or "quantity" in field_name:
            return "integer"
        elif "description" in field_name or "notes" in field_name or "message" in field_name:
            return "text"
        else:
            return "keyword"

    def _get_esql_guidance_snippet(self, category: str) -> str:
        """Get relevant ES|QL guidance snippet for the category"""
        guidance = {
            "anomaly_detection": """
**Anomaly Detection Pattern:**
| STATS metric_value = AVG(field) BY time_bucket, dimension
| INLINESTATS avg_metric = AVG(metric_value), stddev_metric = STD_DEV(metric_value) BY dimension
| EVAL z_score = (metric_value - avg_metric) / COALESCE(stddev_metric, 1)
| WHERE z_score > 3 OR z_score < -3""",

            "analytics": """
**Analytics Pattern:**
| STATS total = SUM(amount), avg_value = AVG(amount), count = COUNT(*) BY category
| EVAL percentage = (total / SUM(total) OVER ()) * 100
| SORT total DESC""",

            "search": """
**Search Pattern:**
| WHERE MATCH(field, ?query)
| KEEP id, title, description, score
| SORT score DESC
| LIMIT 10""",

            "enrichment": """
**Enrichment Pattern:**
FROM main_data
| LOOKUP JOIN reference_data ON key_field
| STATS aggregation BY enriched_field
| SORT aggregation DESC""",

            "trending": """
**Trending Pattern:**
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS count = COUNT(*) BY time_bucket, category
| SORT time_bucket DESC"""
        }

        return guidance.get(category, "| STATS count = COUNT(*)")

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response"""
        import json

        # Try to find JSON in code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            json_text = text[start:end].strip()
        else:
            json_text = text.strip()

        return json.loads(json_text)

    def extract_data_requirements(self, strategy: Dict) -> Dict[str, Dict]:
        """Extract data generation requirements from query strategy

        Args:
            strategy: Query strategy dictionary

        Returns:
            Dict mapping dataset names to their requirements
        """
        data_requirements = {}

        for dataset in strategy.get('datasets', []):
            data_requirements[dataset['name']] = {
                'fields': dataset['required_fields'],
                'relationships': dataset.get('relationships', []),
                'semantic_fields': dataset.get('semantic_fields', []),
                'type': dataset['type'],
                'row_count': dataset.get('row_count', 'moderate')
            }

        return data_requirements

    def validate_strategy(self, strategy: Dict) -> None:
        """Validate the generated strategy

        Args:
            strategy: Query strategy dictionary

        Raises:
            ValueError: If strategy is invalid
        """
        # Basic validation
        if not strategy.get('datasets'):
            raise ValueError("Strategy must include datasets")
        if not strategy.get('queries'):
            raise ValueError("Strategy must include queries")

        # Ensure all required datasets exist
        dataset_names = {d['name'] for d in strategy['datasets']}
        for query in strategy['queries']:
            for dataset in query.get('required_datasets', []):
                if dataset not in dataset_names:
                    raise ValueError(f"Query references unknown dataset: {dataset}")

        logger.info(f"Strategy validated: {len(strategy['queries'])} queries, {len(strategy['datasets'])} datasets")