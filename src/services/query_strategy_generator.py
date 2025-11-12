"""
Query Strategy Generator
Generates query-first strategy BEFORE data generation to ensure alignment
"""

from typing import Dict, List, Any, Optional
import json
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class DatasetRequirement:
    """Requirements for a single dataset"""
    name: str
    type: str  # 'timeseries' or 'reference'
    row_count: str
    required_fields: Dict[str, str]  # field_name: field_type
    relationships: List[str]
    semantic_fields: List[str]


@dataclass
class QueryRequirement:
    """Requirements for a single query"""
    name: str
    pain_point: str
    esql_features: List[str]
    required_datasets: List[str]
    required_fields: Dict[str, List[str]]  # dataset: [field_names]
    join_chain: List[str]
    description: str
    complexity: str


class QueryStrategyGenerator:
    """Generates query strategy BEFORE data generation"""

    def __init__(self, llm_client):
        """Initialize with LLM client

        Args:
            llm_client: Anthropic Claude client
        """
        self.llm_client = llm_client

    def generate_strategy(self, context: Dict) -> Dict:
        """Generate complete query strategy from customer context

        Args:
            context: Customer context with pain_points, use_cases, etc.

        Returns:
            Strategy dict with datasets, queries, relationships, field_mappings
        """
        logger.info(f"Generating query strategy for {context.get('company_name')}")

        # Read ES|QL skill for reference
        esql_skill = self._read_esql_skill()

        prompt = self._build_strategy_prompt(context, esql_skill)

        # Call LLM to generate strategy
        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=8000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            strategy_text = response.content[0].text
            strategy_json = self._extract_json(strategy_text)

            logger.info(f"Generated strategy with {len(strategy_json.get('queries', []))} queries")
            return strategy_json

        except Exception as e:
            logger.error(f"Failed to generate query strategy: {e}", exc_info=True)
            raise

    def _build_strategy_prompt(self, context: Dict, esql_skill: str) -> str:
        """Build the LLM prompt for query strategy generation"""

        prompt = f"""You are an ES|QL expert designing a demo for Elastic Agent Builder.

**Customer Context:**
- Company: {context.get('company_name')}
- Department: {context.get('department')}
- Industry: {context.get('industry')}
- Pain Points: {json.dumps(context.get('pain_points', []), indent=2)}
- Use Cases: {json.dumps(context.get('use_cases', []), indent=2)}
- Scale: {context.get('scale')}
- Metrics: {json.dumps(context.get('metrics', []), indent=2)}

**Your Task:**
Design 5-7 ES|QL queries that directly address their pain points and use cases.
For each query, specify the EXACT data structure needed to make it work.

**ES|QL Capabilities Reference:**
{esql_skill}

**Critical Requirements:**
1. Queries must SOLVE specific pain points (not generic)
2. Use advanced ES|QL features (LOOKUP JOIN, INLINESTATS, EVAL, etc.)
3. Specify EXACT field names needed (be specific, not generic)
4. Choose correct index_mode based on LOOKUP JOIN usage:
   - **index_mode: "lookup"** - If dataset will be used in ANY LOOKUP JOIN clause OR is reference data
   - **index_mode: "data_stream"** - If dataset is ONLY used in FROM clauses AND has a timestamp field
5. Define relationships between datasets (foreign keys)
6. Mark fields that should use semantic_text for vector search

**CRITICAL Index Mode Decision Rule:**
For each dataset, determine index_mode based on how it will be used:
1. **Will this dataset appear in LOOKUP JOIN?** → index_mode: "lookup"
2. **Used ONLY in FROM + has @timestamp?** → index_mode: "data_stream"
3. **Used ONLY in FROM + NO timestamp?** → index_mode: "lookup"

Examples:
- products (used in "LOOKUP JOIN products") → index_mode: "lookup"
- sales_transactions (FROM only, has @timestamp) → index_mode: "data_stream"
- knowledge_base (FROM only, no timestamp) → index_mode: "lookup"

**Output Format (MUST be valid JSON):**
```json
{{
  "datasets": [
    {{
      "name": "sales_transactions",
      "type": "timeseries",
      "index_mode": "data_stream",
      "row_count": "100000+",
      "required_fields": {{
        "transaction_id": "keyword",
        "@timestamp": "date",
        "product_id": "keyword",
        "customer_segment": "keyword",
        "amount": "float",
        "region": "keyword",
        "transaction_notes": "text"
      }},
      "relationships": ["products", "customer_segments"],
      "semantic_fields": ["transaction_notes"]
    }},
    {{
      "name": "products",
      "type": "reference",
      "index_mode": "lookup",
      "row_count": "10000+",
      "required_fields": {{
        "product_id": "keyword",
        "product_name": "text",
        "category": "keyword",
        "price": "float",
        "product_description": "text"
      }},
      "relationships": ["sales_transactions"],
      "semantic_fields": ["product_description"]
    }}
  ],
  "queries": [
    {{
      "name": "Sales Spike Detection with Product Enrichment",
      "pain_point": "Cannot quickly correlate sales spikes with product categories",
      "esql_features": ["STATS", "DATE_TRUNC", "LOOKUP JOIN", "EVAL"],
      "required_datasets": ["sales_transactions", "products"],
      "required_fields": {{
        "sales_transactions": ["@timestamp", "product_id", "amount", "region"],
        "products": ["product_id", "category", "product_name"]
      }},
      "join_chain": ["sales_transactions -> products"],
      "description": "Detect revenue spikes by hour, enrich with product details to identify which categories are driving growth",
      "complexity": "medium"
    }}
  ],
  "relationships": [
    {{
      "from": "sales_transactions",
      "to": "products",
      "type": "many-to-one",
      "join_field": "product_id"
    }}
  ],
  "field_mappings": {{
    "sales_transactions.product_id": "products.product_id",
    "sales_transactions.customer_segment": "customer_segments.segment_id"
  }}
}}
```

**Important Guidelines:**
- Use SPECIFIC field names relevant to their business (not generic "field1")
- Include @timestamp for timeseries datasets (not just "timestamp")
- Reference datasets should be small lookup tables
- Every query should directly address a pain point
- Use LOOKUP JOIN syntax: "FROM timeseries | LOOKUP JOIN reference ON key"
- Use the actual dataset name in LOOKUP JOIN (no suffix needed)

**CRITICAL JSON FORMATTING RULES:**
1. Return ONLY valid JSON - no markdown, no commentary, no explanations
2. Ensure all strings are properly escaped (use \\" for quotes inside strings)
3. Do NOT include newlines inside JSON string values - use \\n instead
4. Do NOT include unescaped special characters in string values
5. Enclose the entire JSON in a ```json code block

Generate the complete strategy as valid JSON now:"""

        return prompt

    def _read_esql_skill(self) -> str:
        """Read ES|QL skill documentation for reference"""
        try:
            from pathlib import Path
            skill_path = Path('.claude/skills/esql-advanced-commands.md')
            if skill_path.exists():
                return skill_path.read_text()
            else:
                logger.warning("ES|QL skill file not found, using minimal reference")
                return """
ES|QL Key Features:
- LOOKUP JOIN: Enrich timeseries with reference data
- INLINESTATS: Calculate aggregates while keeping all rows
- EVAL: Create calculated fields
- STATS: Aggregate with GROUP BY
- DATE_TRUNC: Bucket timestamps
- WHERE: Filter rows
- SORT: Order results
- LIMIT: Limit result count
"""
        except Exception as e:
            logger.warning(f"Could not read ES|QL skill: {e}")
            return "ES|QL advanced commands"

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
            logger.debug(f"JSON text preview: {json_text[:1000]}")

            # Save the problematic JSON for debugging
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(json_text)
                logger.error(f"Saved problematic JSON to: {f.name}")

            # Try to provide helpful error message
            error_msg = f"Invalid JSON in LLM response: {e}\n"
            error_msg += f"This usually means the LLM generated malformed JSON with unescaped quotes or newlines.\n"
            error_msg += f"Check the saved file at the path above for details."
            raise ValueError(error_msg)

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

    def validate_strategy(self, strategy: Dict) -> bool:
        """Validate that strategy has required structure

        Args:
            strategy: Query strategy dictionary

        Returns:
            True if valid, raises ValueError if invalid
        """
        required_keys = ['datasets', 'queries', 'relationships']

        for key in required_keys:
            if key not in strategy:
                raise ValueError(f"Strategy missing required key: {key}")

        if not strategy['datasets']:
            raise ValueError("Strategy must have at least one dataset")

        if not strategy['queries']:
            raise ValueError("Strategy must have at least one query")

        # Validate dataset structure
        for dataset in strategy['datasets']:
            required_dataset_keys = ['name', 'type', 'required_fields']
            for key in required_dataset_keys:
                if key not in dataset:
                    raise ValueError(f"Dataset missing required key: {key}")

            if dataset['type'] not in ['timeseries', 'reference']:
                raise ValueError(f"Dataset type must be 'timeseries' or 'reference', got: {dataset['type']}")

        # Validate query structure
        for query in strategy['queries']:
            required_query_keys = ['name', 'required_datasets', 'required_fields']
            for key in required_query_keys:
                if key not in query:
                    raise ValueError(f"Query missing required key: {key}")

        logger.info("Strategy validation passed")
        return True

    def get_field_info_for_prompts(self, data_requirements: Dict) -> str:
        """Format data requirements for inclusion in code generation prompts

        Args:
            data_requirements: Extracted data requirements

        Returns:
            Formatted string for LLM prompt
        """
        formatted = "**Data Requirements (from Query Strategy):**\n\n"

        for dataset_name, reqs in data_requirements.items():
            formatted += f"**Dataset: {dataset_name}** ({reqs['type']})\n"
            formatted += f"  Type: {reqs['type']}\n"
            formatted += f"  Rows: {reqs['row_count']}\n"
            formatted += "  Required Fields:\n"

            for field_name, field_type in reqs['fields'].items():
                formatted += f"    - {field_name}: {field_type}\n"

            if reqs.get('semantic_fields'):
                formatted += f"  Semantic Fields: {', '.join(reqs['semantic_fields'])}\n"

            if reqs.get('relationships'):
                formatted += f"  Relationships: {', '.join(reqs['relationships'])}\n"

            formatted += "\n"

        return formatted
