"""
STRICT ES|QL Syntax Rules - Single Source of Truth
===================================================

This module contains CRITICAL ES|QL syntax rules that MUST be followed.
These rules supersede any conflicting documentation or examples.
Consolidated from testing failures, skills, and production experience.
"""

# ============================================================================
# CRITICAL SYNTAX RULES - VIOLATIONS CAUSE IMMEDIATE FAILURE
# ============================================================================

ESQL_STRICT_RULES = """
## CRITICAL ES|QL SYNTAX RULES - MUST FOLLOW

### 1. LOOKUP JOIN - NO SUFFIX, NO PREFIX ⚠️⚠️ CRITICAL
✅ CORRECT: `| LOOKUP JOIN products ON product_id`
❌ WRONG: `| LOOKUP JOIN products_lookup ON product_id`
❌ WRONG: Any use of "_lookup" suffix
❌ WRONG: Using ENRICH instead of LOOKUP JOIN

The index name should be used directly without any suffix.
Lookup mode is determined by index settings, not naming convention.

**CRITICAL - Field References After LOOKUP JOIN:**
After a LOOKUP JOIN, fields from the joined dataset are available **DIRECTLY** without any prefix.

✅ CORRECT Pattern:
```esql
FROM claims
| LOOKUP JOIN providers ON provider_id
| STATS count = COUNT(*) BY specialty              -- Just "specialty", no prefix!
| KEEP claim_id, provider_name, specialty          -- Just "provider_name", "specialty"
```

❌ WRONG Pattern:
```esql
FROM claims
| LOOKUP JOIN providers ON provider_id
| STATS count = COUNT(*) BY providers.specialty     -- ❌ ERROR: Unknown column [providers_lookup.specialty]
| KEEP claim_id, providers.provider_name            -- ❌ ERROR: Unknown column [providers_lookup.provider_name]
```

**Why this fails**: Elasticsearch tries to interpret `providers.specialty` as a dataset reference and looks for `providers_lookup.specialty`, which doesn't exist.

**Rule**: Reference ALL fields (from both source and joined datasets) without any table prefix after LOOKUP JOIN.

**IMPORTANT**: Use LOOKUP JOIN for data enrichment, NOT ENRICH.
LOOKUP JOIN is the modern, preferred approach that works with lookup mode indices.

### 2. MATCH Syntax - ALWAYS WITHIN WHERE ⚠️
✅ CORRECT: `| WHERE MATCH(field, "search term")`
✅ CORRECT: `| WHERE MATCH(field, ?parameter)`
✅ CORRECT: `| WHERE MATCH(field, ?query, {"boost": 2.0, "fuzziness": "AUTO"})`
❌ WRONG: `| MATCH field "term"` - MATCH is NOT a pipe operation
❌ WRONG: `| MATCH title, content WITH ?query` - Invalid syntax
❌ WRONG: `| MATCH (field) ?query` - Invalid syntax

MATCH is a function that MUST be called within WHERE clause.
For multiple fields, use OR:
✅ `| WHERE MATCH(title, ?query) OR MATCH(content, ?query)`

### 3. FORK Syntax - NO NAMED BRANCHES ⚠️
✅ CORRECT:
```esql
| FORK
  (WHERE category == "A" | STATS count = COUNT(*))
  (WHERE category == "B" | STATS count = COUNT(*))
```

❌ WRONG:
```esql
| FORK
  branch_a = (...)  // NO NAMED BRANCHES!
  branch_b = (...)
```

❌ WRONG: Comments inside FORK branches can cause parsing errors

FORK branches are unnamed and cannot be assigned to variables.

### 4. Query Parameters - CANNOT CHECK NULL ⚠️
❌ WRONG: `WHERE ?param IS NULL` - Cannot check if parameter is NULL
❌ WRONG: `WHERE field == ?param OR ?param IS NULL` - Invalid pattern
❌ WRONG: `WHERE COALESCE(?param, "default") == field` - Won't work

Parameters are ALWAYS required when used. If optional behavior is needed:
- Create SEPARATE scripted queries (no parameters)
- Create SEPARATE parameterized queries (with required parameters)
- DO NOT attempt conditional parameter logic

### 5. RERANK Syntax - Pipe Operation ⚠️
✅ CORRECT: `| RERANK "query" ON field`
✅ CORRECT: `| RERANK ?question ON content`
❌ WRONG: `| RERANK semantic_text WITH ?query` - Wrong syntax
❌ WRONG: `| RERANK field WITH query` - Wrong syntax
❌ WRONG: `WHERE RERANK(...)` - RERANK is a pipe operation

### 6. STATS Conditional Aggregation ⚠️
✅ CORRECT: `STATS denied = SUM(CASE(status == "denied", 1, 0))`
✅ CORRECT: `STATS high_risk = COUNT(*) WHERE risk > 0.8` (ES|QL 8.13+)
❌ WRONG: `STATS denied = COUNT(*) WHERE status == "denied"` in older versions
❌ WRONG: `STATS denied = COUNT_IF(status == "denied")` - No COUNT_IF function
❌ WRONG: `COUNT(CASE(...))` - Use SUM(CASE(...)) for conditional counting

### 7. DATE Functions - Parameter Order ⚠️
✅ CORRECT: `DATE_TRUNC(1 hour, @timestamp)`
✅ CORRECT: `DATE_EXTRACT("month", @timestamp)`
❌ WRONG: `DATE_TRUNC(@timestamp, 1 hour)` - Wrong order
❌ WRONG: `DATE_EXTRACT(@timestamp, "month")` - Wrong order

### 8. Index Modes for LOOKUP JOIN ⚠️ CRITICAL
When using LOOKUP JOIN, the target index MUST be in lookup mode:

**Index Mode Requirements:**
- **Data Streams** (`.ds-*` prefix) = Standard mode → CANNOT be used with LOOKUP JOIN
- **Lookup Indices** = Lookup mode → REQUIRED for LOOKUP JOIN

**Dataset Type Mapping:**
- `type: "timeseries"` → Create as data_stream (for events, logs, interactions)
- `type: "reference"` → Create as lookup index (for members, providers, products)

**ERROR**: "Lookup Join requires a single lookup mode index; [members] resolves to [.ds-members-2025.11.03-000001] in [standard] mode"
- This means members was incorrectly created as a data stream (note `.ds-` prefix)
- Solution: Reference datasets MUST be created as lookup indices, not data streams
- You CANNOT fix this in the query - the index creation mode must be corrected

### 9. Field Names - Case Sensitive ⚠️
- Use `@timestamp` for time fields (not `timestamp`)
- Field names are CASE SENSITIVE and must match exactly
- Never invent field names - use only fields from the schema
- After STATS, only grouped fields and calculated fields are available

### 10. Division and Type Casting ⚠️
✅ CORRECT: `EVAL rate = TO_DOUBLE(numerator) / denominator`
✅ CORRECT: `EVAL pct = numerator * 100.0 / denominator`
❌ WRONG: `EVAL rate = numerator / denominator` - Integer division loses precision

### 11. COMPLETION Syntax (RAG Queries) ⚠️
✅ CORRECT: `| COMPLETION "prompt" WITH ?user_question`
❌ WRONG: `| COMPLETION "prompt" ON field` - Wrong syntax
Note: COMPLETION may not be available in all Elasticsearch versions

### 12. Experimental Features ⚠️
These may fail depending on ES version:
- CHANGE_POINT - Use INLINESTATS with z-score calculation instead
- LAG/LEAD - Window functions may not be supported
- SEMANTIC - Use MATCH with semantic_text fields instead
"""

# ============================================================================
# ADVANCED COMMANDS AND PATTERNS
# ============================================================================

ESQL_ADVANCED_PATTERNS = """
## Advanced ES|QL Commands for Demos

### LOOKUP JOIN - Data Enrichment
**Purpose**: Enrich streaming data with dimensional data
**CRITICAL**: After LOOKUP JOIN, reference fields WITHOUT any prefix!
```esql
FROM events
| LOOKUP JOIN dimension_table ON join_key
| WHERE tier == "VIP"                              -- ✅ No prefix!
| STATS revenue = SUM(amount) BY segment            -- ✅ No prefix!
```

### INLINESTATS - Keep All Rows While Aggregating
**Purpose**: Add aggregate calculations without grouping
```esql
FROM transactions
| INLINESTATS avg_amount = AVG(amount) BY category
| EVAL variance_from_avg = amount - avg_amount
| WHERE variance_from_avg > 1000
```

### FORK - Parallel Analysis Paths
**Purpose**: Split pipeline for multiple analyses
```esql
FROM events
| FORK
  (WHERE type == "error" | STATS errors = COUNT(*))
  (WHERE type == "warning" | STATS warnings = COUNT(*))
  (STATS total = COUNT(*))
```

### Multi-Field Search Pattern
```esql
FROM knowledge_base
| WHERE MATCH(title, ?query, {"boost": 2.0})
     OR MATCH(content, ?query, {"boost": 1.0})
     OR MATCH(tags, ?query, {"boost": 1.5})
| SORT _score DESC
| LIMIT 10
```

### Time Series Anomaly Detection
```esql
FROM metrics
| EVAL hour = DATE_TRUNC(1 hour, @timestamp)
| STATS value = AVG(metric) BY hour
| INLINESTATS
    mean_value = AVG(value),
    stddev_value = STDDEV(value)
| EVAL z_score = (value - mean_value) / stddev_value
| WHERE z_score > 3 OR z_score < -3
```
"""

# ============================================================================
# SAFE QUERY PATTERNS BY TYPE
# ============================================================================

ESQL_QUERY_PATTERNS = """
## Safe Query Patterns by Type

### 1. Scripted Query (No Parameters, Testable)
```esql
FROM transactions
| WHERE @timestamp >= NOW() - 30 days
| WHERE status == "pending"
| LOOKUP JOIN products ON product_id
| STATS
    total = COUNT(*),
    avg_amount = AVG(amount),
    max_amount = MAX(amount)
  BY category
| SORT total DESC
| LIMIT 20
```

### 2. Parameterized Query (Required Parameters Only)
```esql
FROM customers
| WHERE region == ?region
| WHERE segment == ?segment
| WHERE created_date >= ?start_date
| STATS
    customer_count = COUNT(*),
    avg_revenue = AVG(total_revenue)
  BY plan_type
| SORT customer_count DESC
```
Note: ALL parameters are REQUIRED. No NULL checking or optional params.

### 3. RAG Query (Semantic Search + LLM)
```esql
FROM knowledge_base
| WHERE MATCH(content, ?user_question, {"fuzziness": "AUTO"})
| WHERE category IN ["policy", "procedure", "faq"]
| KEEP article_id, title, content, last_updated, _score
| SORT _score DESC
| LIMIT 5
```
Note: MATCH within WHERE, proper field selection with KEEP

### 4. Complex Aggregation with Enrichment
```esql
FROM call_events
| WHERE @timestamp >= NOW() - 7 days
| LOOKUP JOIN agents ON agent_id
| LOOKUP JOIN customers ON customer_id
| STATS
    call_count = COUNT(*),
    avg_duration = AVG(duration_seconds),
    resolved = SUM(CASE(status == "resolved", 1, 0))
  BY agents.team, agents.tier, customers.segment
| EVAL resolution_rate = TO_DOUBLE(resolved) * 100.0 / call_count
| WHERE call_count > 10
| SORT resolution_rate DESC
```
"""

# ============================================================================
# COMMON ERROR FIXES
# ============================================================================

COMMON_ERROR_FIXES = """
## Common ES|QL Errors and Their Fixes

| Error Pattern | Root Cause | Fix |
|--------------|------------|-----|
| "Unknown index [x_lookup]" | Adding _lookup suffix | Remove _lookup suffix entirely |
| "Unknown column [providers_lookup.field]" | Using table prefix after JOIN | Remove prefix: `providers.field` → `field` |
| "Unknown column [table.field]" after JOIN | Field reference with prefix | Reference fields directly without table prefix |
| "mismatched input 'MATCH'" | MATCH as pipe operation | Use WHERE MATCH(field, query) |
| "Unknown query parameter" | Checking param IS NULL | Remove NULL checks, use required params |
| "token recognition error" in FORK | Named branches or comments | Remove branch names and comments |
| "Lookup Join requires lookup mode" | Index not in lookup mode | Target index must be created in lookup mode |
| "Unknown function [COUNT_IF]" | Function doesn't exist | Use SUM(CASE(...)) pattern |
| "DATE_TRUNC" errors | Wrong parameter order | Use DATE_TRUNC(interval, field) |
| "Division by zero" | Integer division | Use TO_DOUBLE() or multiply by 1.0 |
| "Field not found" after STATS | Field not in GROUP BY | Only grouped/aggregated fields available |
| "Unknown column [agents_lookup]" | Auto-fix adding suffix | Remove the _lookup suffix |
| "RERANK" errors | Wrong syntax | Use RERANK query ON field |
| "MATCH WITH" syntax error | Invalid MATCH syntax | Use WHERE MATCH(field, query) |
"""

# ============================================================================
# PROMPTING BEST PRACTICES
# ============================================================================

LLM_PROMPTING_GUIDELINES = """
## Guidelines for LLM Query Generation

### DO's:
1. ALWAYS validate field names against the actual schema
2. ALWAYS use scripted queries for testing before making parameterized versions
3. ALWAYS use TO_DOUBLE() for division operations
4. ALWAYS use @timestamp for time fields
5. ALWAYS put MATCH inside WHERE clause
6. ALWAYS check index mode compatibility for LOOKUP JOIN
7. PREFER INLINESTATS over window functions
8. PREFER SUM(CASE()) over conditional COUNT

### DON'Ts:
1. NEVER use table prefixes after LOOKUP JOIN (use `specialty` not `providers.specialty`)
2. NEVER add _lookup suffix to index names
3. NEVER check if parameters are NULL
4. NEVER use named branches in FORK
5. NEVER put comments inside FORK branches
6. NEVER use MATCH as a pipe operation
7. NEVER assume fields exist after STATS without including in GROUP BY
8. NEVER use COUNT_IF or other non-existent functions
9. NEVER mix parameter order in DATE functions

### Query Generation Process:
1. Start with scripted query (concrete values)
2. Test and validate the scripted query
3. Only then convert to parameterized (if needed)
4. Ensure all parameters are required (no optional logic)
5. Create separate queries for different optional scenarios
"""

# ============================================================================
# AUTO-FIX RULES FOR QUERY TESTER
# ============================================================================

QUERY_FIXER_RULES = """
## Query Auto-Fix Rules (For query_test_runner.py)

When fixing queries, apply these transformations IN ORDER:

1. **Remove table prefixes after LOOKUP JOIN** - Fields are available DIRECTLY
   - `providers.specialty` → `specialty`
   - `members.first_name` → `first_name`
   - `products.category` → `category`
   - ANY `table.field` reference after LOOKUP JOIN → just `field`

2. **Remove ALL _lookup suffixes** - Never add them, always remove them
   - `agents_lookup` → `agents`
   - `products_lookup` → `products`

3. **Fix MATCH syntax**:
   - `| MATCH field WITH query` → `| WHERE MATCH(field, query)`
   - `| MATCH field "query"` → `| WHERE MATCH(field, "query")`
   - `| MATCH title, content WITH ?q` → `| WHERE MATCH(title, ?q) OR MATCH(content, ?q)`

3. **Fix FORK branches**:
   - Remove any `name = (...)` patterns
   - Remove comments inside branches

4. **Remove parameter NULL checks**:
   - Delete any `?param IS NULL` conditions
   - Remove entire `OR ?param IS NULL` clauses
   - If this breaks logic, note that query needs separate scripted version

5. **Fix DATE functions**:
   - `DATE_TRUNC(@timestamp, 1 hour)` → `DATE_TRUNC(1 hour, @timestamp)`
   - `DATE_EXTRACT(@timestamp, "month")` → `DATE_EXTRACT("month", @timestamp)`

6. **Replace invalid aggregates**:
   - `COUNT_IF(condition)` → `SUM(CASE(condition, 1, 0))`
   - `COUNT(*) WHERE condition` → `SUM(CASE(condition, 1, 0))` (if not supported)

7. **Fix division**:
   - `a / b` → `TO_DOUBLE(a) / b` (when precision needed)
   - `a / b` → `a * 1.0 / b` (alternative)

8. **Fix RERANK syntax**:
   - `RERANK field WITH query` → `RERANK query ON field`
   - `RERANK semantic_text WITH ?q` → `RERANK ?q ON semantic_text`

CRITICAL: NEVER suggest adding _lookup suffix as a fix!
If index not found, it's a data indexing issue, not a query issue.
"""

# ============================================================================
# PYTHON UTILITY FUNCTIONS
# ============================================================================

def get_esql_rules() -> str:
    """Get core ES|QL syntax rules for prompts"""
    return ESQL_STRICT_RULES

def get_advanced_patterns() -> str:
    """Get advanced ES|QL command patterns"""
    return ESQL_ADVANCED_PATTERNS

def get_query_patterns() -> str:
    """Get safe query patterns by type"""
    return ESQL_QUERY_PATTERNS

def get_error_fixes() -> str:
    """Get common error patterns and fixes"""
    return COMMON_ERROR_FIXES

def get_llm_guidelines() -> str:
    """Get LLM prompting guidelines"""
    return LLM_PROMPTING_GUIDELINES

def get_fixer_rules() -> str:
    """Get auto-fixer rules for query_test_runner"""
    return QUERY_FIXER_RULES

def get_complete_reference() -> str:
    """Get complete ES|QL reference for prompts"""
    sections = [
        ESQL_STRICT_RULES,
        ESQL_ADVANCED_PATTERNS,
        ESQL_QUERY_PATTERNS,
        COMMON_ERROR_FIXES,
        LLM_PROMPTING_GUIDELINES
    ]
    return "\n\n".join(sections)

def get_rules_for_module_generation() -> str:
    """Get rules specifically for module generation prompts"""
    sections = [
        ESQL_STRICT_RULES,
        ESQL_QUERY_PATTERNS,
        LLM_PROMPTING_GUIDELINES
    ]
    return "\n\n".join(sections)

def get_rules_for_query_fixing() -> str:
    """Get rules specifically for query auto-fixing"""
    sections = [
        ESQL_STRICT_RULES,
        COMMON_ERROR_FIXES,
        QUERY_FIXER_RULES
    ]
    return "\n\n".join(sections)

# For backward compatibility with existing code
ESQL_CRITICAL_RULES = ESQL_STRICT_RULES
ESQL_QUERY_EXAMPLES = ESQL_QUERY_PATTERNS