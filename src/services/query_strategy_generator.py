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

        # Start with requested number of queries
        num_queries = 5  # Reduced from 7 to avoid truncation
        max_retries = 2

        for attempt in range(max_retries):
            try:
                # Adjust prompt based on attempt
                if attempt > 0:
                    logger.info(f"Retry {attempt}: Requesting {num_queries} queries to avoid truncation")

                prompt = self._build_strategy_prompt(context, esql_skill, num_queries=num_queries)

                # Call LLM to generate strategy
                response = self.llm_client.messages.create(
                    model="claude-sonnet-4",
                    max_tokens=8000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )

                strategy_text = response.content[0].text

                # Check if response appears truncated
                if self._is_likely_truncated(strategy_text):
                    logger.warning(f"Response appears truncated (attempt {attempt + 1}/{max_retries})")
                    # Reduce number of queries for next attempt
                    num_queries = max(3, num_queries - 2)
                    if attempt < max_retries - 1:
                        continue

                strategy_json = self._extract_json(strategy_text)

                logger.info(f"Generated strategy with {len(strategy_json.get('queries', []))} queries")
                return strategy_json

            except ValueError as e:
                if "Invalid JSON" in str(e) and attempt < max_retries - 1:
                    # Try with fewer queries on JSON parsing errors
                    logger.warning(f"JSON parsing failed (attempt {attempt + 1}/{max_retries}): {e}")
                    num_queries = max(3, num_queries - 2)
                    continue
                else:
                    logger.error(f"Failed to generate query strategy: {e}", exc_info=True)
                    raise

            except Exception as e:
                logger.error(f"Failed to generate query strategy: {e}", exc_info=True)
                raise

        # If we get here, all retries failed
        raise ValueError("Failed to generate valid query strategy after all retries")

    def _is_likely_truncated(self, text: str) -> bool:
        """Check if the response text appears to be truncated

        Args:
            text: Response text from LLM

        Returns:
            True if text appears truncated
        """
        # Check for common signs of truncation
        text = text.rstrip()

        # If it doesn't end with typical JSON endings, might be truncated
        if not (text.endswith('}') or text.endswith(']') or text.endswith('```')):
            return True

        # If JSON block started but not closed
        if '```json' in text and not text.endswith('```'):
            return True

        # Check for severely imbalanced brackets/braces
        open_braces = text.count('{')
        close_braces = text.count('}')
        open_brackets = text.count('[')
        close_brackets = text.count(']')

        # If there's a large imbalance, likely truncated
        if abs(open_braces - close_braces) > 2 or abs(open_brackets - close_brackets) > 2:
            return True

        return False

    def _build_strategy_prompt(self, context: Dict, esql_skill: str, num_queries: int = 5) -> str:
        """Build the LLM prompt for query strategy generation

        Args:
            context: Customer context
            esql_skill: ES|QL skill documentation
            num_queries: Number of queries to generate (default 5)

        Returns:
            Prompt string
        """

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
Design EXACTLY {num_queries} ES|QL queries that directly address their pain points and use cases.
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

**⚠️ CRITICAL ES|QL ANTI-PATTERNS TO AVOID:**
❌ NEVER use window functions: LAG(), LEAD(), OVER, PARTITION BY (in window context)
❌ NEVER use ranking functions: ROW_NUMBER(), RANK(), DENSE_RANK()
❌ NEVER try to reference other rows: metric[-1], previous values, or row positions
❌ NEVER use unsupported syntax like: OVER (ORDER BY...), OVER (PARTITION BY...)

**✅ RECOMMENDED PATTERNS FOR COMMON USE CASES:**

1. **For Anomaly Detection** (instead of LAG/LEAD):
```esql
| STATS metric_value = AVG(field) BY time_bucket, dimension
| INLINESTATS
    avg_metric = AVG(metric_value),
    stddev_metric = STD_DEV(metric_value)
  BY dimension
| EVAL z_score = (metric_value - avg_metric) / COALESCE(stddev_metric, 1)
| WHERE z_score > 3
```

2. **For Change Detection** (instead of LAG for period-over-period):
```esql
| INLINESTATS
    baseline = AVG(metric),
    threshold = PERCENTILE(metric, 95)
  BY category
| EVAL pct_deviation = ((metric - baseline) / baseline) * 100
| WHERE ABS(pct_deviation) > 25
```

3. **For Top N Results** (instead of ROW_NUMBER):
```esql
| STATS max_value = MAX(metric) BY dimension
| SORT max_value DESC
| LIMIT 10
```

**✅ WHAT INLINESTATS CAN DO:**
- Statistical aggregations: AVG(), STD_DEV(), VARIANCE()
- Counting: COUNT(), COUNT_DISTINCT()
- Min/Max: MIN(), MAX()
- Percentiles: PERCENTILE(field, n), MEDIAN()
- Sums: SUM()

**REMEMBER:** INLINESTATS = Aggregations ONLY. No window functions, no row references!

**🎯 CRITICAL: KEEP Field Prioritization for Agent Tool Calls**
⚠️ **ONLY THE FIRST 5 FIELDS in KEEP are visible to agents!** Fields 6+ are truncated in tool responses.

**KEEP Field Order Requirements:**
1. **Positions 1-2**: Primary identifiers (customer_id, user_id, entity_id)
2. **Positions 3-4**: Critical values (severity, score, amount, status)
3. **Position 5**: Human context (error_message, description, summary)
4. **Positions 6+**: Supporting data (timestamps, metadata) - NOT visible to agents

**Example KEEP statements:**
```esql
// GOOD: Critical fields first
| KEEP customer_id, anomaly_severity, metric_name, z_score, current_value, timestamp, details

// BAD: Critical fields buried
| KEEP timestamp, session_id, trace_id, span_id, details, customer_id, severity
```

**⚠️ CRITICAL: NEVER Parameterize @timestamp**
❌ **DO NOT parameterize @timestamp or system timestamp fields!**

**WRONG - Anti-pattern:**
```esql
FROM purchase_transactions
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date  ❌ BAD!
```

**CORRECT - Use NOW() for @timestamp:**
```esql
FROM purchase_transactions
| WHERE @timestamp >= NOW() - 7 days  ✅ GOOD!
```

**Date Parameterization Rules:**
- ❌ `@timestamp` → IF filtering on it, use `NOW() - X days/hours` (NEVER parameterize - it's an Elasticsearch system field)
- ✅ `created_at` → Can parameterize for specific dates, or use `NOW()` for recency
- ✅ `updated_at` → Can parameterize for specific dates, or use `NOW()` for recency
- ✅ `acquisition_date` → Parameterize as `?start_date` (business date)
- ✅ `order_date` → Parameterize as `?order_date` (business date)
- ✅ `contract_date` → Parameterize as `?contract_start` (business date)

**Critical Rules**:
- `@timestamp` is the ONLY field that should NEVER be parameterized
- Only add time-based filters when they're part of the use case (e.g., "recent activity", "last quarter's sales")
- Don't add @timestamp filters to every query - generated data is static, so "last 7 days" filters become stale
- All other date fields CAN be parameterized based on query purpose:
  - For recency ("last 7 days") → Use `NOW() - X days`
  - For specific ranges ("Q1 2023") → Use `?parameters`

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
      "name": "Sales Anomaly Detection with Statistical Z-Score",
      "pain_point": "Cannot quickly identify abnormal sales patterns across regions",
      "esql_features": ["STATS", "DATE_TRUNC", "INLINESTATS", "EVAL", "STD_DEV"],
      "required_datasets": ["sales_transactions"],
      "required_fields": {{
        "sales_transactions": ["@timestamp", "amount", "region", "store_id"]
      }},
      "description": "Detect statistical anomalies in hourly sales using z-score analysis, identify stores with unusual patterns",
      "complexity": "medium",
      "esql_query": "FROM sales_transactions | EVAL hour = DATE_TRUNC(1 hour, @timestamp) | STATS hourly_sales = SUM(amount) BY hour, store_id, region | INLINESTATS avg_sales = AVG(hourly_sales), stddev_sales = STD_DEV(hourly_sales), p95_sales = PERCENTILE(hourly_sales, 95) BY region | EVAL z_score = (hourly_sales - avg_sales) / COALESCE(stddev_sales, 1) | WHERE z_score > 3 OR z_score < -3 | EVAL anomaly_type = CASE(z_score > 3, 'SPIKE', 'DROP') | SORT ABS(z_score) DESC"
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
        """Extract JSON from LLM response with robust error handling

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

        # First attempt: Parse as-is
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parse failed: {e}")
            logger.debug(f"Attempting to fix common JSON issues...")

            # Second attempt: Fix common issues
            try:
                fixed_json = self._fix_json_issues(json_text)
                return json.loads(fixed_json)
            except json.JSONDecodeError as e2:
                logger.error(f"JSON fix attempt failed: {e2}")

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

    def _fix_json_issues(self, json_text: str) -> str:
        """Attempt to fix common JSON formatting issues from LLM responses

        Args:
            json_text: Raw JSON text that failed to parse

        Returns:
            Fixed JSON text
        """
        import re

        # Step 1: Check if JSON appears truncated and attempt to complete it
        json_text = self._complete_truncated_json(json_text)

        # Step 2: Replace actual newlines within string values with \n
        # This regex finds strings and replaces newlines within them
        def fix_newlines_in_strings(match):
            # The matched string content (without quotes)
            content = match.group(1)
            # Replace actual newlines with escaped newlines
            fixed_content = content.replace('\n', '\\n').replace('\r', '\\r')
            # Replace tabs with escaped tabs
            fixed_content = fixed_content.replace('\t', '\\t')
            # Return the fixed string with quotes
            return f'"{fixed_content}"'

        # Match string values (handling escaped quotes)
        # This pattern matches: "..." where ... can contain \" but not unescaped "
        json_text = re.sub(r'"((?:[^"\\]|\\.)*)(?<!\\)"', fix_newlines_in_strings, json_text)

        # Step 3: Fix unescaped quotes within string values more aggressively
        # Look for patterns where we have quotes inside a string value
        # This is a more aggressive approach for fixing nested quotes
        def fix_quotes_in_value(text):
            # Find string values that might have unescaped quotes
            # This looks for patterns like: "value": "text with "quote" inside"
            pattern = r'("(?:query|description|name|pain_point|esql)":\s*")(.*?)("(?:\s*,|\s*\}))'

            def escape_internal_quotes(match):
                prefix = match.group(1)
                content = match.group(2)
                suffix = match.group(3)
                # Escape any unescaped quotes in the content
                fixed_content = re.sub(r'(?<!\\)"', r'\"', content)
                return prefix + fixed_content + suffix

            return re.sub(pattern, escape_internal_quotes, text, flags=re.DOTALL)

        json_text = fix_quotes_in_value(json_text)

        # Step 4: Remove trailing commas before closing brackets/braces
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)

        # Step 5: Ensure consistent quote usage (replace single quotes around keys/values)
        # But be careful not to replace single quotes within string values
        json_text = re.sub(r"'([^']*)'(\s*:)", r'"\1"\2', json_text)  # Fix keys
        json_text = re.sub(r":\s*'([^']*)'", r': "\1"', json_text)    # Fix simple string values

        # Step 6: Remove any BOM or zero-width spaces
        json_text = json_text.replace('\ufeff', '').replace('\u200b', '')

        # Step 7: Handle common encoding issues
        json_text = json_text.encode('utf-8', errors='ignore').decode('utf-8')

        logger.debug("Applied JSON fixes: truncation, newlines, trailing commas, quotes, encoding")
        return json_text

    def _complete_truncated_json(self, json_text: str) -> str:
        """Attempt to complete truncated JSON by closing open structures

        Args:
            json_text: Potentially truncated JSON text

        Returns:
            Completed JSON text
        """
        import re

        # Count open brackets and braces
        open_braces = json_text.count('{') - json_text.count('}')
        open_brackets = json_text.count('[') - json_text.count(']')

        # Check if we're in the middle of a string value
        # Look for the last quote and determine if we're inside a string
        in_string = False
        escape_next = False
        quote_count = 0

        for char in json_text:
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"':
                quote_count += 1
                in_string = not in_string

        # If we're in a string, close it
        if in_string:
            json_text += '"'
            logger.debug("Closed incomplete string value")

        # Now check if we need to close the current object/array context
        # Look at the last few characters to understand the context
        trimmed = json_text.rstrip()

        # If the last character is a quote, we just closed a string
        # Check what comes before the string to see if we need a closing brace/bracket
        if trimmed.endswith('"'):
            # Look backwards to find the context
            # Find the last opening that would contain this string
            # Simple heuristic: if we just closed a string after "query": "...",
            # we likely need to close the object containing this query
            last_100_chars = trimmed[-100:] if len(trimmed) > 100 else trimmed

            # Check if this looks like the end of a query field
            if '"query"' in last_100_chars or '"esql"' in last_100_chars:
                # This is likely a truncated query field, need to close the parent object
                # But first check if there are more fields expected
                # Simple approach: assume query is the last field in queries array item
                pass  # Will be handled by structure closing below

        # Now close structures based on count
        closing = ''

        # We need to be smart about closing - check the context
        # If we just ended with a string value, we might need to close the containing object first
        if open_braces > 0 or open_brackets > 0:
            # Analyze the last part to understand nesting
            # Simple approach: close in LIFO order (close brackets before braces)

            # First close any arrays
            closing += ']' * open_brackets

            # Then close any objects
            closing += '}' * open_braces

        if closing:
            logger.debug(f"Completing truncated JSON with: {closing}")
            json_text += closing

        return json_text

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
