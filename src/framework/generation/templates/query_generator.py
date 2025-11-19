"""
Query generator templates for demo module generation.

This module provides templates for generating query generator modules
with scripted, parameterized, and RAG query types.
"""

from typing import Dict, Any


def get_scripted_queries_prompt(config: Dict[str, Any], esql_docs: str) -> str:
    """Get prompt for generating scripted queries

    Generates SCRIPTED (non-parameterized) ES|QL queries that address pain points.

    Args:
        config: Demo configuration with company context
        esql_docs: ES|QL documentation reference

    Returns:
        LLM prompt for generating scripted queries method
    """
    tool_metadata_prompt = _get_tool_metadata_instructions(config)
    company_slug = config['company_name'].lower().replace(' ', '_')[:15]
    dept_slug = config.get('department', 'analytics').lower().replace(' ', '_')[:10]

    return f"""Generate the `generate_queries()` method for a QueryGeneratorModule.

**Customer Context:**
Company: {config["company_name"]}
Department: {config["department"]}
Pain Points: {", ".join(config["pain_points"])}
Use Cases: {", ".join(config["use_cases"])}

{tool_metadata_prompt}

**Task**: Generate 5-7 SCRIPTED (non-parameterized) ES|QL queries that address their pain points.

**Requirements:**
- All queries must use hard-coded values (no ?parameters)
- Start simple, progress to complex
- Each query should address a specific pain point
- All will be tested against indexed data

**ES|QL Reference (Basics):**
{esql_docs[:1500]}

**Method Template:**
```python
def generate_queries(self) -> List[Dict[str, Any]]:
    \"\"\"Generate SCRIPTED (non-parameterized) ES|QL queries

    These are fully tested queries with hard-coded values.
    Address pain points: {", ".join(config["pain_points"])}
    \"\"\"
    queries = []

    # Query 1: [Simple aggregation]
    queries.append({{
        "query_type": "scripted",
        "name": "descriptive_name",
        "description": "What it demonstrates",
        "tool_metadata": {{  # REQUIRED for Agent Builder
            "tool_id": "{company_slug}_{dept_slug}_purpose",
            "description": "Short action summary. Details about when to use and insights provided.",
            "tags": ["domain", "function", "esql"]
        }},
        "esql": \"\"\"
            FROM index_name
            | WHERE condition
            | STATS aggregation
            | SORT field DESC
            | LIMIT 10
        \"\"\",
        "expected_insight": "What customer learns",
        "tested": True
    }})

    # Add 4-6 more queries of increasing complexity...

    return queries
```

🚨🚨🚨 CRITICAL - INTEGER DIVISION ANTI-PATTERN 🚨🚨🚨
ALWAYS use TO_DOUBLE() when dividing aggregated fields! Integer division truncates to 0!

❌ WRONG (produces 0 or 100 only):
```esql
| EVAL success_rate = ((total - failures) / total) * 100
```

✅ CORRECT (produces accurate percentages like 95.7):
```esql
| EVAL success_rate = ((total - failures) / TO_DOUBLE(total)) * 100
```

**WHY**: In ES|QL, dividing two integers performs integer division and truncates the result.
- (95 / 100) = 0 (WRONG - integer division)
- (95 / TO_DOUBLE(100)) = 0.95 (CORRECT - float division)

**RULE**: If you see division (/) in an EVAL, wrap the denominator in TO_DOUBLE() UNLESS:
- You already use TO_DOUBLE(): ✓ `field / TO_DOUBLE(total)`
- You multiply by float first: ✓ `field * 100.0 / total`
- You divide by float literal: ✓ `milliseconds / 1000.0`

🚨🚨🚨 CRITICAL - NULL HANDLING ANTI-PATTERN 🚨🚨🚨
ALWAYS include NULL checks with negative filters! ES|QL silently excludes NULL values!

❌ WRONG (silently excludes docs where field is NULL - DATA LOSS):
```esql
| WHERE status != "success"
| WHERE NOT(error_type LIKE "*timeout*")
```

✅ CORRECT (includes NULL values - complete data):
```esql
| WHERE status != "success" OR status IS NULL
| WHERE NOT(error_type LIKE "*timeout*") OR error_type IS NULL
```

**WHY**: ES|QL excludes NULL/missing fields from negative filters (!=, NOT, NOT LIKE).
- Documents where the field is NULL are SILENTLY EXCLUDED even though they match "not X"
- ESPECIALLY CRITICAL for security queries - missing data = missed threats!

**RULE**: When using negative filters (!=, NOT, NOT LIKE, NOT IN), append `OR field IS NULL` UNLESS:
- Field is guaranteed to exist (e.g., @timestamp)
- You explicitly want to exclude nulls (rare - document this in description)

Generate ONLY the method implementation (including the def line and all queries). Do NOT include class definition or imports."""


def get_parameterized_queries_prompt(config: Dict[str, Any], esql_docs: str) -> str:
    """Get prompt for generating parameterized queries

    Generates PARAMETERIZED queries for Agent Builder ES|QL tools with ?parameter syntax.

    Args:
        config: Demo configuration with company context
        esql_docs: ES|QL documentation reference

    Returns:
        LLM prompt for generating parameterized queries method
    """
    tool_metadata_prompt = _get_tool_metadata_instructions(config)
    company_slug = config['company_name'].lower().replace(' ', '_')[:15]
    dept_slug = config.get('department', 'analytics').lower().replace(' ', '_')[:10]

    return f"""Generate the `generate_parameterized_queries()` method for a QueryGeneratorModule.

**Customer Context:**
Company: {config["company_name"]}
Department: {config["department"]}
Pain Points: {", ".join(config["pain_points"])}

{tool_metadata_prompt}

**Task**: Generate 3-5 PARAMETERIZED queries for Agent Builder ES|QL tools.

**Requirements:**
- Based on typical analytics queries for their use case
- Use ?parameter syntax for user-configurable values
- NO LIKE or RLIKE operators (not supported with parameters!)
- Include parameter definitions with types and defaults
- Link to conceptual base query for trust

**CRITICAL - Smart Parameter Selection:**

✅ **CREATE parameters for BUSINESS-SPECIFIC logic:**
- Domain fields: `WHERE category == ?category`, `WHERE status == ?status`
- Business date fields: `WHERE deployment_date >= ?deploy_start`, `WHERE hire_date BETWEEN ?from AND ?to`
- Schema-specific: `WHERE provider_id == ?provider`, `WHERE priority_level >= ?min_priority`

❌ **AVOID parameters for CROSS-CUTTING concerns:**
- `@timestamp` filtering (agents handle dynamically via platform.core.execute_esql)
- Event timestamps: created_at, updated_at, indexed_at
- Generic operations: LIMIT, SORT direction

**Business Date Fields - GOOD Examples:**
```
WHERE deployment_date >= ?deploy_start  # ✓ Business date field
WHERE expiration_date < ?expiry_cutoff  # ✓ Domain-specific date
WHERE hire_date BETWEEN ?from AND ?to   # ✓ Business temporal logic
```

**@timestamp Filtering - AVOID:**
```
WHERE @timestamp >= ?start_date  # ✗ Agent handles this via execute_esql
WHERE @timestamp <= ?end_date    # ✗ Cross-cutting concern
```

**ES|QL Parameter Syntax:**
```
WHERE category == ?category
WHERE deployment_date >= ?deploy_start  # Use business dates, not @timestamp
LIMIT ?limit  # Optional - consider if necessary
```

**Method Template:**
```python
def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
    \"\"\"Generate PARAMETERIZED versions for Agent Builder

    Use ?parameter syntax. NO LIKE/RLIKE operators!
    \"\"\"
    param_queries = []

    param_queries.append({{
        "query_type": "parameterized",
        "name": "parameterized_query_name",
        "description": "Configurable version of X",
        "tool_metadata": {{  # REQUIRED for Agent Builder
            "tool_id": "{company_slug}_{dept_slug}_configurable",
            "description": "Analyzes data with business-specific filters. Focus on domain logic, not time ranges (agents handle those).",
            "tags": ["analytics", "configurable", "esql"]
        }},
        "esql": \"\"\"
            FROM index_name
            | WHERE category == ?category
            | WHERE status == ?status
            | STATS aggregation BY field
            | SORT _count DESC
            | LIMIT 100
        \"\"\",
        "parameters": {{
            "category": {{
                "type": "keyword",
                "description": "Business category filter",
                "default": "example_category",
                "required": True
            }},
            "status": {{
                "type": "keyword",
                "description": "Status filter (active, pending, completed)",
                "default": "active",
                "required": False
            }}
        }},
        "base_query": "related_scripted_query_name",
        "agent_builder_ready": True
    }})

    # Add 2-4 more parameterized queries...

    return param_queries
```

🚨🚨🚨 CRITICAL - @timestamp ANTI-PATTERN 🚨🚨🚨
NEVER EVER parameterize @timestamp! This is the #1 most common mistake!

❌ WRONG (DO NOT GENERATE THIS):
```esql
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
```

✅ CORRECT (USE THIS INSTEAD):
```esql
| WHERE @timestamp >= NOW() - 7 days  # Relative time with NOW()
```

The ONLY time-based parameters allowed are for BUSINESS date fields (order_date, created_at, etc.) - NEVER @timestamp!

🚨🚨🚨 CRITICAL - INTEGER DIVISION ANTI-PATTERN 🚨🚨🚨
ALWAYS use TO_DOUBLE() when dividing aggregated fields! Integer division truncates to 0!

❌ WRONG (produces 0 or 100 only):
```esql
| EVAL success_rate = ((total - failures) / total) * 100
```

✅ CORRECT (produces accurate percentages like 95.7):
```esql
| EVAL success_rate = ((total - failures) / TO_DOUBLE(total)) * 100
```

**WHY**: In ES|QL, dividing two integers performs integer division and truncates the result.
- (95 / 100) = 0 (WRONG - integer division)
- (95 / TO_DOUBLE(100)) = 0.95 (CORRECT - float division)

**RULE**: If you see division (/) in an EVAL, wrap the denominator in TO_DOUBLE() UNLESS:
- You already use TO_DOUBLE(): ✓ `field / TO_DOUBLE(total)`
- You multiply by float first: ✓ `field * 100.0 / total`
- You divide by float literal: ✓ `milliseconds / 1000.0`

🚨🚨🚨 CRITICAL - NULL HANDLING ANTI-PATTERN 🚨🚨🚨
ALWAYS include NULL checks with negative filters! ES|QL silently excludes NULL values!

❌ WRONG (silently excludes docs where field is NULL - DATA LOSS):
```esql
| WHERE status != "success"
| WHERE NOT(error_type LIKE "*timeout*")
```

✅ CORRECT (includes NULL values - complete data):
```esql
| WHERE status != "success" OR status IS NULL
| WHERE NOT(error_type LIKE "*timeout*") OR error_type IS NULL
```

**WHY**: ES|QL excludes NULL/missing fields from negative filters (!=, NOT, NOT LIKE).
- Documents where the field is NULL are SILENTLY EXCLUDED even though they match "not X"
- ESPECIALLY CRITICAL for security queries - missing data = missed threats!

**RULE**: When using negative filters (!=, NOT, NOT LIKE, NOT IN), append `OR field IS NULL` UNLESS:
- Field is guaranteed to exist (e.g., @timestamp)
- You explicitly want to exclude nulls (rare - document this in description)

Generate ONLY the method implementation. Do NOT include class definition or imports."""


def get_rag_queries_prompt(config: Dict[str, Any], esql_docs: str,
                          rerank_endpoint: str = ".rerank-v1-elasticsearch",
                          completion_endpoint: str = "completion-vulcan") -> str:
    """Get prompt for generating RAG queries

    Generates RAG queries using MATCH -> RERANK -> INLINE STATS -> COMPLETION pipeline.

    Args:
        config: Demo configuration with company context
        esql_docs: ES|QL documentation reference
        rerank_endpoint: Inference endpoint ID for reranking
        completion_endpoint: Inference endpoint ID for LLM completion

    Returns:
        LLM prompt for generating RAG queries method
    """
    tool_metadata_prompt = _get_tool_metadata_instructions(config)
    company_slug = config['company_name'].lower().replace(' ', '_')[:15]
    dept_slug = config.get('department', 'analytics').lower().replace(' ', '_')[:10]

    return f"""Generate the `generate_rag_queries()` method for a QueryGeneratorModule.

**Customer Context:**
Company: {config["company_name"]}
Department: {config["department"]}
Pain Points: {", ".join(config["pain_points"])}

{tool_metadata_prompt}

**Task**: Generate 1-3 RAG queries using MATCH -> RERANK -> INLINE STATS -> COMPLETION pipeline.

**CRITICAL RAG Architecture:**
1. MATCH: Semantic search across text fields with relevance tuning
2. RERANK: ML-based relevance scoring
3. INLINE STATS (NOT STATS!): Aggregate context without losing fields
4. COMPLETION: LLM generates answer from context

**IMPORTANT - Use Relevance Tuning:**
ALWAYS use MATCH with named parameters for relevance tuning:
- `boost`: Increase/decrease field importance (e.g., {{"boost": 2.0}} for titles, {{"boost": 0.5}} for descriptions)
- `fuzziness`: Allow typos/variations (e.g., {{"fuzziness": "AUTO"}} or {{"fuzziness": "1"}})

Example:
```esql
WHERE MATCH(title, ?query, {{"boost": 2.0, "fuzziness": "AUTO"}})
   OR MATCH(description, ?query, {{"boost": 1.0, "fuzziness": "1"}})
   OR MATCH(content, ?query, {{"boost": 0.5}})
```

**ES|QL Reference (RAG Commands):**
{esql_docs}

**CRITICAL - INLINE STATS vs STATS:**
- WRONG: `| STATS context = MV_CONCAT(field, "\\n")`  <- Loses all fields except context!
- CORRECT: `| INLINE STATS all_context = MV_CONCAT(context, "\\n\\n")`  <- Preserves fields!

**Method Template:**
```python
def generate_rag_queries(self) -> List[Dict[str, Any]]:
    \"\"\"Generate RAG queries (MATCH -> RERANK -> COMPLETION)

    For semantic search + AI-powered answers via Agent Builder.
    CRITICAL: Use INLINE STATS not STATS!
    \"\"\"
    rag_queries = []

    rag_queries.append({{
        "query_type": "rag",
        "name": "semantic_search_rag",
        "description": "Ask questions about [data type]",
        "tool_metadata": {{  # REQUIRED for Agent Builder
            "tool_id": "{company_slug}_{dept_slug}_ai_search",
            "description": "Searches knowledge base with AI answers. Provides contextual responses using semantic search and completion.",
            "tags": ["search", "ai", "rag", "esql"]
        }},
        "esql": \"\"\"
            FROM index_name METADATA _score
            | WHERE MATCH(text_field1, ?user_question, {{"boost": 2.0, "fuzziness": "AUTO"}})
                OR MATCH(text_field2, ?user_question, {{"boost": 1.5, "fuzziness": "1"}})
                OR MATCH(text_field3, ?user_question, {{"boost": 1.0}})
            | WHERE @timestamp >= NOW() - 120 days
            | SORT _score DESC
            | LIMIT 100
            | RERANK ?user_question
                ON text_field1, text_field2, text_field3
                WITH {{"inference_id": "{rerank_endpoint}"}}
            | LIMIT 5
            | EVAL context = CONCAT(
                "Record: ", id_field, " | ",
                "Field1: ", text_field1, " | ",
                "Field2: ", text_field2
              )
            | INLINE STATS all_context = MV_CONCAT(context, "\\\\n\\\\n")
            | EVAL prompt = CONCAT(
                "Based on these records:\\\\n\\\\n",
                all_context,
                "\\\\n\\\\nQuestion: ", ?user_question,
                "\\\\n\\\\nProvide a detailed answer:"
              )
            | COMPLETION answer = prompt
                WITH {{"inference_id": "{completion_endpoint}"}}
            | KEEP answer, all_context
        \"\"\",
        "parameters": {{
            "user_question": {{
                "type": "string",
                "description": "Question to answer",
                "required": True,
                "example": "What are the main issues with...?"
            }}
        }},
        "search_fields": ["text_field1", "text_field2"],
        "rerank_fields": ["text_field1", "text_field2", "text_field3"],
        "context_fields": ["id_field", "text_field1", "text_field2", "status"],
        "time_boundary": "120 days"
    }})

    # Optionally add 1-2 more RAG queries for different use cases...

    return rag_queries
```

**IMPORTANT**:
- **ALWAYS use boost and fuzziness parameters** in MATCH for relevance tuning
- Identify 3-5 text fields for MATCH (description, content, feedback, notes, comments, etc.)
- Use DIFFERENT boost values to prioritize fields (2.0 for important, 1.5 for medium, 1.0 or 0.5 for less important)
- Add fuzziness ("AUTO" or "1") to handle typos and variations
- Select 2-4 most important fields for RERANK
- Use INLINE STATS to aggregate context
- Set appropriate time boundary (30/90/120 days)

Generate ONLY the method implementation. Do NOT include class definition or imports."""


def _get_tool_metadata_instructions(config: Dict[str, Any]) -> str:
    """Get tool metadata instructions embedded in prompts

    Used in all three query generation prompts to ensure consistent tool metadata formatting.
    """
    company_slug = config['company_name'].lower().replace(' ', '_')[:15]
    dept_slug = config.get('department', 'analytics').lower().replace(' ', '_')[:10]

    return f"""
**IMPORTANT: Agent Builder Tool Metadata**

Each query MUST include 'tool_metadata' for deployment to Elastic Agent Builder.
This metadata allows queries to become reusable tools that AI agents can invoke.

For EACH query you generate, include a 'tool_metadata' field with:

1. 'tool_id': Unique identifier following pattern: <customer>_<dept>_<purpose>
   - MUST start and end with a letter or number
   - ONLY lowercase letters, numbers, dots, underscores
   - Maximum 50 characters
   - Use company prefix: {company_slug}
   - Department: {dept_slug}
   - Examples:
     * "{company_slug}_{dept_slug}_performance" OK
     * "{company_slug}_{dept_slug}_inventory_alerts" OK
     * "Query-1-{config['company_name']}" NOT OK (no uppercase/hyphens)

2. 'description': Tool description for Agent Builder (NOT the same as query description)
   - First ~50 characters appear in tool list - make them count!
   - Start with WHAT it does (verb): "Analyzes...", "Compares...", "Identifies..."
   - Then explain WHEN to use it and what insights it provides
   - Focus on business value, not technical implementation
   - Bad: "ES|QL query for metrics analysis"
   - Good: "Analyzes performance metrics across regions. Identifies underperforming areas and trends for optimization."

3. 'tags': Array of 3-5 lowercase tags for categorization
   - Include domain tags based on use case
   - Include functional tags (performance, cost, analytics)
   - Include "esql" for all ES|QL queries
   - Keep single words, no spaces

Example query structure with tool_metadata:
{{
    'name': 'Regional Performance Analysis',
    'description': 'Analyze performance metrics across different regions',  # Original query description
    'tool_metadata': {{
        'tool_id': '{company_slug}_{dept_slug}_regional_performance',
        'description': 'Analyzes regional performance metrics. Identifies underperforming regions and trends for strategic planning.',
        'tags': ['analytics', 'performance', 'regional', 'esql']
    }},
    'esql': 'FROM metrics | STATS avg_performance = AVG(score) BY region',
    'pain_point': 'Lack of visibility into regional performance'
}}

Tool metadata is REQUIRED - every query must have valid tool_metadata for Agent Builder deployment.
"""


def get_query_module_wrapper(config: Dict[str, Any], scripted_code: str,
                            parameterized_code: str, rag_code: str) -> str:
    """Create complete query generator module from three method implementations

    Combines scripted, parameterized, and RAG method code into a full Python module.

    Args:
        config: Demo configuration
        scripted_code: generate_queries() method code
        parameterized_code: generate_parameterized_queries() method code
        rag_code: generate_rag_queries() method code

    Returns:
        Complete Python module with class definition and all three methods
    """
    company_class = config["company_name"].replace(" ", "")

    def indent_method(code: str) -> str:
        """Add 4-space indentation to each line of method code"""
        lines = code.strip().split('\n')
        indented_lines = ['    ' + line for line in lines]
        return '\n'.join(indented_lines)

    scripted_indented = indent_method(scripted_code)
    parameterized_indented = indent_method(parameterized_code)
    rag_indented = indent_method(rag_code)

    full_module = f"""from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class {company_class}QueryGenerator(QueryGeneratorModule):
    \"\"\"Query generator for {config["company_name"]} - {config["department"]}

    Generates three types of queries:
    1. Scripted (tested, non-parameterized)
    2. Parameterized (Agent Builder tools)
    3. RAG (semantic search + LLM completion)
    \"\"\"

{scripted_indented}

{parameterized_indented}

{rag_indented}

    def get_query_progression(self) -> List[str]:
        \"\"\"Order to present SCRIPTED queries (for demos)\"\"\"
        # Extract query names from scripted queries
        queries = self.generate_queries()
        return [q.get('name', f'query_{{i}}') for i, q in enumerate(queries)]
"""

    return full_module
