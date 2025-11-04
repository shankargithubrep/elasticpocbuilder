"""
Lightweight Query Planner for Path 1 (Data-First with Schema Coordination)

This planner is lighter than QueryStrategyGenerator - it only plans:
1. Query type distribution (how many scripted/parameterized/RAG queries)
2. Field requirements for each query type
3. Dataset relationships for joins

The actual query generation is delegated to specialized 3-call generation.
"""

from typing import Dict, List, Any, Optional
import json
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class QueryPlan:
    """Lightweight query plan with field requirements"""
    name: str
    query_type: str  # 'scripted', 'parameterized', or 'rag'
    pain_point: str
    required_datasets: List[str]
    required_fields: Dict[str, List[str]]  # dataset: [field_names]
    description: str


@dataclass
class DatasetPlan:
    """Lightweight dataset plan"""
    name: str
    type: str  # 'timeseries' or 'reference'
    required_fields: Dict[str, str]  # field_name: field_type
    relationships: List[str]
    semantic_fields: List[str]


class LightweightQueryPlanner:
    """Generates query plans BEFORE data generation (lighter than QueryStrategyGenerator)"""

    def __init__(self, llm_client):
        """Initialize with LLM client

        Args:
            llm_client: Anthropic Claude client
        """
        self.llm_client = llm_client

    def plan_queries(self, context: Dict) -> Dict:
        """Generate lightweight query plan from customer context

        Args:
            context: Customer context with pain_points, use_cases, etc.

        Returns:
            Plan dict with:
            - datasets: List of DatasetPlan
            - query_plans: List of QueryPlan
            - field_requirements: Dict mapping dataset -> fields
        """
        logger.info(f"Planning queries for {context.get('company_name')}")

        # Read ES|QL reference
        esql_reference = self._read_esql_reference()

        prompt = self._build_planning_prompt(context, esql_reference)

        # Call LLM to generate plan
        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=6000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            plan_text = response.content[0].text
            plan_json = self._extract_json(plan_text)

            # Validate and log
            self._validate_plan(plan_json)
            logger.info(
                f"Generated plan with {len(plan_json.get('query_plans', []))} queries: "
                f"{self._count_query_types(plan_json)}"
            )

            return plan_json

        except Exception as e:
            logger.error(f"Failed to generate query plan: {e}", exc_info=True)
            raise

    def _build_planning_prompt(self, context: Dict, esql_reference: str) -> str:
        """Build the LLM prompt for query planning"""

        prompt = f"""You are an ES|QL expert planning queries for an Elastic Agent Builder demo.

**Customer Context:**
- Company: {context.get('company_name')}
- Department: {context.get('department')}
- Industry: {context.get('industry')}
- Pain Points: {json.dumps(context.get('pain_points', []), indent=2)}
- Use Cases: {json.dumps(context.get('use_cases', []), indent=2)}
- Scale: {context.get('scale')}
- Metrics: {json.dumps(context.get('metrics', []), indent=2)}

**Your Task:**
Plan 5-7 queries that showcase ES|QL sophistication and address their pain points.

**Query Types to Include:**
1. **Scripted Queries** (2-3 queries): Fixed, testable queries with specific values
   - Purpose: Demonstrate specific analytics and insights
   - Example: "Show all high-value transactions in the last 30 days"

2. **Parameterized Queries** (2-3 queries): Use `?field` syntax for Agent Builder tool calls
   - Purpose: Create interactive tools that users can customize
   - Example: "Find customers by ?segment and ?region"

3. **RAG Queries** (1-2 queries): MATCH → RERANK → COMPLETION for semantic search
   - Purpose: Show vector search and AI-powered summarization
   - Example: "Search knowledge base for ?user_question, rerank by relevance, generate summary"

**ES|QL Capabilities:**
{esql_reference}

**Critical Planning Requirements:**
1. Specify EXACT field names needed (not generic "field1")
2. Include @timestamp for timeseries datasets
3. Define relationships between datasets (for LOOKUP JOIN)
4. Mark text fields that need semantic_text for RAG queries
5. Each query must solve a specific pain point

**Output Format (MUST be valid JSON):**
```json
{{
  "datasets": [
    {{
      "name": "support_tickets",
      "type": "timeseries",
      "required_fields": {{
        "ticket_id": "keyword",
        "@timestamp": "date",
        "customer_id": "keyword",
        "status": "keyword",
        "priority": "keyword",
        "description": "text",
        "resolution_notes": "text"
      }},
      "relationships": ["customers", "knowledge_base"],
      "semantic_fields": ["description", "resolution_notes"]
    }},
    {{
      "name": "customers",
      "type": "reference",
      "required_fields": {{
        "customer_id": "keyword",
        "customer_name": "text",
        "segment": "keyword",
        "region": "keyword"
      }},
      "relationships": ["support_tickets"],
      "semantic_fields": []
    }}
  ],
  "query_plans": [
    {{
      "name": "High Priority Ticket Trends",
      "query_type": "scripted",
      "pain_point": "Cannot quickly identify priority ticket patterns",
      "required_datasets": ["support_tickets"],
      "required_fields": {{
        "support_tickets": ["@timestamp", "priority", "status", "ticket_id"]
      }},
      "description": "Analyze high priority tickets by hour to identify peak support times"
    }},
    {{
      "name": "Find Customers by Segment and Region",
      "query_type": "parameterized",
      "pain_point": "Manual customer filtering is slow",
      "required_datasets": ["customers", "support_tickets"],
      "required_fields": {{
        "customers": ["customer_id", "customer_name", "segment", "region"],
        "support_tickets": ["customer_id", "ticket_id", "status"]
      }},
      "description": "Interactive tool to find customers by ?segment and ?region with their ticket counts"
    }},
    {{
      "name": "Search Knowledge Base for Solutions",
      "query_type": "rag",
      "pain_point": "Support agents waste time searching for solutions",
      "required_datasets": ["knowledge_base"],
      "required_fields": {{
        "knowledge_base": ["article_id", "title", "content", "category"]
      }},
      "description": "Semantic search knowledge base using ?user_question, rerank results, generate summary"
    }}
  ]
}}
```

**Important Guidelines:**
- Use SPECIFIC field names relevant to their business (not generic)
- Include @timestamp for all timeseries datasets
- Reference datasets are lookup tables (small, enrichment data)
- EVERY query should directly address a stated pain point
- Mix query types: aim for 2-3 scripted, 2-3 parameterized, 1-2 RAG
- Semantic fields are for RAG MATCH operations (text fields only)

Generate the query plan as valid JSON:"""

        return prompt

    def _read_esql_reference(self) -> str:
        """Read ES|QL skill documentation for reference"""
        try:
            from pathlib import Path
            skill_path = Path('.claude/skills/esql-advanced-commands.md')
            if skill_path.exists():
                content = skill_path.read_text()
                # Truncate to keep prompt smaller
                return content[:3000] + "\n\n[... see full docs for more details ...]"
            else:
                logger.warning("ES|QL skill file not found, using minimal reference")
                return self._get_minimal_esql_reference()
        except Exception as e:
            logger.warning(f"Could not read ES|QL skill: {e}")
            return self._get_minimal_esql_reference()

    def _get_minimal_esql_reference(self) -> str:
        """Minimal ES|QL reference when skill file not available"""
        return """
ES|QL Key Features:
- **LOOKUP JOIN**: Enrich timeseries with reference data
  FROM timeseries | LOOKUP JOIN reference_lookup ON key
- **INLINESTATS**: Calculate aggregates while keeping all rows
  INLINESTATS avg_amount = AVG(amount) BY region
- **EVAL**: Create calculated fields
  EVAL revenue = quantity * price
- **STATS**: Aggregate with GROUP BY
  STATS total = SUM(amount) BY DATE_TRUNC(1 hour, @timestamp)
- **MATCH**: Semantic search with boost and fuzziness
  WHERE MATCH(field, ?query, {"boost": 2.0, "fuzziness": "AUTO"})
- **RERANK**: Re-order results by relevance
  | RERANK inference_endpoint field=text query=?user_question
- **DATE_TRUNC**: Bucket timestamps for time series analysis
"""

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response

        Args:
            text: LLM response text

        Returns:
            Parsed JSON dictionary
        """
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
            # Assume entire response is JSON
            json_text = text.strip()

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"JSON text: {json_text[:500]}")
            raise ValueError(f"Invalid JSON in LLM response: {e}")

    def _validate_plan(self, plan: Dict) -> bool:
        """Validate that plan has required structure

        Args:
            plan: Query plan dictionary

        Returns:
            True if valid, raises ValueError if invalid
        """
        if 'datasets' not in plan:
            raise ValueError("Plan missing 'datasets' key")

        if 'query_plans' not in plan:
            raise ValueError("Plan missing 'query_plans' key")

        if not plan['datasets']:
            raise ValueError("Plan must have at least one dataset")

        if not plan['query_plans']:
            raise ValueError("Plan must have at least one query plan")

        # Validate datasets
        for dataset in plan['datasets']:
            if 'name' not in dataset or 'required_fields' not in dataset:
                raise ValueError(f"Dataset missing required fields: {dataset}")

        # Validate query plans
        for query in plan['query_plans']:
            if 'name' not in query or 'query_type' not in query:
                raise ValueError(f"Query plan missing required fields: {query}")

            if query['query_type'] not in ['scripted', 'parameterized', 'rag']:
                raise ValueError(f"Invalid query_type: {query['query_type']}")

        logger.info("Plan validation passed")
        return True

    def _count_query_types(self, plan: Dict) -> str:
        """Count query types for logging

        Args:
            plan: Query plan dictionary

        Returns:
            Summary string like "3 scripted, 2 parameterized, 2 RAG"
        """
        counts = {'scripted': 0, 'parameterized': 0, 'rag': 0}

        for query in plan.get('query_plans', []):
            query_type = query.get('query_type', 'unknown')
            if query_type in counts:
                counts[query_type] += 1

        return f"{counts['scripted']} scripted, {counts['parameterized']} parameterized, {counts['rag']} RAG"

    def extract_field_requirements(self, plan: Dict) -> Dict[str, Dict]:
        """Extract field requirements for data generation

        Args:
            plan: Query plan dictionary

        Returns:
            Dict mapping dataset names to their field requirements
        """
        field_requirements = {}

        for dataset in plan.get('datasets', []):
            field_requirements[dataset['name']] = {
                'fields': dataset['required_fields'],
                'relationships': dataset.get('relationships', []),
                'semantic_fields': dataset.get('semantic_fields', []),
                'type': dataset['type'],
                'row_count': 'moderate'  # Default row count
            }

        return field_requirements

    def format_requirements_for_data_prompt(self, plan: Dict) -> str:
        """Format field requirements for data generator prompt

        Args:
            plan: Query plan dictionary

        Returns:
            Formatted string for LLM prompt
        """
        formatted = "**Field Requirements (from Query Planning):**\n\n"
        formatted += "You MUST use these EXACT field names and types:\n\n"

        for dataset in plan.get('datasets', []):
            formatted += f"**Dataset: {dataset['name']}** ({dataset['type']})\n"
            formatted += "  Required Fields:\n"

            for field_name, field_type in dataset['required_fields'].items():
                formatted += f"    - {field_name}: {field_type}\n"

            if dataset.get('semantic_fields'):
                formatted += f"  Semantic Fields (for RAG): {', '.join(dataset['semantic_fields'])}\n"

            if dataset.get('relationships'):
                formatted += f"  Relationships: {', '.join(dataset['relationships'])}\n"

            formatted += "\n"

        formatted += "**CRITICAL**: Do NOT invent new field names. Use ONLY the fields listed above.\n"

        return formatted

    def format_schema_for_query_prompts(self, datasets: Dict) -> str:
        """Format actual dataset schema for query generation prompts

        Args:
            datasets: Generated datasets from data generator

        Returns:
            Formatted schema string for LLM prompt
        """
        formatted = "**Available Data Schema:**\n\n"

        for dataset_name, data in datasets.items():
            if isinstance(data, list) and len(data) > 0:
                # Extract field names from first record
                sample = data[0]
                formatted += f"**{dataset_name}**:\n"

                for field_name in sample.keys():
                    field_type = type(sample[field_name]).__name__
                    formatted += f"  - {field_name} ({field_type})\n"

                formatted += f"  Rows: {len(data)}\n\n"

        formatted += "**CRITICAL**: Use ONLY these exact field names in your queries.\n"

        return formatted
