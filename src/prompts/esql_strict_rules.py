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

### 6. COUNT_DISTINCT Syntax ⚠️⚠️ VERY COMMON ERROR
✅ CORRECT: `COUNT_DISTINCT(field)` - Single function name
❌ WRONG: `COUNT(DISTINCT field)` - SQL syntax doesn't work in ES|QL

**This is a VERY COMMON mistake**. ES|QL uses `COUNT_DISTINCT()` as a single function, NOT the SQL `COUNT(DISTINCT ...)` pattern.

### 7. INLINESTATS Syntax - Single BY Clause ⚠️⚠️ VERY COMMON ERROR
✅ CORRECT: `INLINESTATS avg_val = AVG(value), max_val = MAX(value) BY category`
❌ WRONG: `INLINESTATS avg_val = AVG(value) BY category, max_val = MAX(value) BY category`

**Rule**: INLINESTATS uses ONE BY clause at the end (just like STATS), NOT one BY clause per aggregation.
This is the SAME syntax pattern as STATS - the BY clause applies to all aggregations together.

### 8. STATS Conditional Aggregation ⚠️
✅ CORRECT: `STATS denied = SUM(CASE(status == "denied", 1, 0))`
✅ CORRECT: `STATS high_risk = COUNT(*) WHERE risk > 0.8` (ES|QL 8.13+)
❌ WRONG: `STATS denied = COUNT(*) WHERE status == "denied"` in older versions
❌ WRONG: `STATS denied = COUNT_IF(status == "denied")` - No COUNT_IF function
❌ WRONG: `COUNT(CASE(...))` - Use SUM(CASE(...)) for conditional counting

### 9. DATE Functions - Parameter Order ⚠️
✅ CORRECT: `DATE_TRUNC(1 hour, @timestamp)`
✅ CORRECT: `DATE_EXTRACT("month", @timestamp)`
❌ WRONG: `DATE_TRUNC(@timestamp, 1 hour)` - Wrong order
❌ WRONG: `DATE_EXTRACT(@timestamp, "month")` - Wrong order

### 10. Index Modes for LOOKUP JOIN ⚠️ CRITICAL
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

### 11. Field Names - Case Sensitive ⚠️
- Use `@timestamp` for time fields (not `timestamp`)
- Field names are CASE SENSITIVE and must match exactly
- Never invent field names - use only fields from the schema
- After STATS, only grouped fields and calculated fields are available

### 12. Date Arithmetic - ALWAYS Use TO_LONG() ⚠️⚠️ CRITICAL
**Common Error**: `[-] has arguments with incompatible types [datetime] and [datetime]`

✅ CORRECT: `EVAL days_diff = (TO_LONG(NOW()) - TO_LONG(last_updated)) / 86400000`
✅ CORRECT: `EVAL hours_diff = (TO_LONG(end_time) - TO_LONG(start_time)) / 3600000`
❌ WRONG: `EVAL days_diff = (NOW() - last_updated) / 86400000` - Datetime subtraction fails
❌ WRONG: `EVAL hours = (end_time - start_time) / 3600000` - Type error

**Rule**: You CANNOT subtract datetime values directly. Always wrap both sides in TO_LONG() first.

### 13. Division and Type Casting ⚠️
✅ CORRECT: `EVAL rate = TO_DOUBLE(numerator) / denominator`
✅ CORRECT: `EVAL pct = numerator * 100.0 / denominator`
❌ WRONG: `EVAL rate = numerator / denominator` - Integer division loses precision

### 14. LOOKUP JOIN Schema Validation ⚠️⚠️⚠️ CRITICAL - CANNOT BE AUTO-FIXED
**Common Error**: `Unknown column [field_name] in right/left side of join`

This is the MOST COMMON failure that CANNOT be automatically fixed. The join key MUST exist in BOTH datasets.

**Example Failure Pattern:**
```esql
FROM aem_pages
| LOOKUP JOIN aem_products ON product_references  -- ❌ FAILS if product_references not in aem_products
```

**Error Messages You'll See:**
- "Unknown column [product_references] in right side of join" → Join key missing in lookup dataset
- "Unknown column [product_id] in left side of join" → Join key missing in source dataset

**PREVENTION STRATEGY:**
Before writing ANY LOOKUP JOIN query, you MUST:
1. ✅ Verify the join key exists in the source dataset schema (FROM dataset)
2. ✅ Verify the join key exists in the lookup dataset schema
3. ✅ Use the EXACT field name (case-sensitive) from both schemas
4. ❌ NEVER invent, assume, or guess join key names

**Correct Pattern:**
```esql
-- FIRST: Verify 'user_id' exists in BOTH events schema AND users schema
FROM events
| LOOKUP JOIN users ON user_id  -- ✅ Only works if user_id is in BOTH
| STATS count = COUNT(*) BY tier  -- Access users fields directly after join
```

**Anti-Pattern (WILL FAIL):**
```esql
FROM pages
| LOOKUP JOIN products ON product_references  -- ❌ Assumes product_references exists - probably doesn't
```

**When You See This Error:**
- It means the schema doesn't support the join you're trying to do
- Auto-fix CANNOT resolve this - it requires data model changes
- You must either: use a different join key that exists in both, or abandon the join

### 15. COMPLETION Syntax (RAG Queries) ⚠️
✅ CORRECT: `| COMPLETION "prompt" WITH ?user_question`
❌ WRONG: `| COMPLETION "prompt" ON field` - Wrong syntax
Note: COMPLETION may not be available in all Elasticsearch versions

### 16. Time Filtering - Different Patterns for Scripted vs Parameterized ⚠️⚠️ CRITICAL
**The Problem**: Demo data is static with fixed timestamps. Using `NOW()` in scripted queries will return NO RESULTS.

**SCRIPTED QUERIES** (no parameters, for exploration):
❌ WRONG: `WHERE @timestamp > NOW() - 7 days` - Will return empty results with static demo data
❌ WRONG: `WHERE @timestamp >= NOW() - 30 days` - Same problem
✅ CORRECT: **OMIT time filters entirely** - Let users control time range via Kibana time picker

**PARAMETERIZED QUERIES** (user-facing tools with parameters):
✅ CORRECT: `WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date`
✅ CORRECT: `WHERE @timestamp >= ?start_date` - For open-ended queries
✅ CORRECT: Use parameters for user-controlled time filtering

**Why This Matters**:
- Demo data has fixed timestamps (e.g., generated for 2024-11-01 to 2024-11-15)
- `NOW() - 7 days` only works if current date happens to overlap with demo data range
- Kibana's time picker lets users select any time range that matches the demo data
- Parameterized queries can accept user input for flexible time filtering

**Rule**:
- Scripted queries: NO `@timestamp` filters (rely on Kibana time picker)
- Parameterized queries: Use `?start_date` and `?end_date` parameters

### 17. Experimental Features ⚠️
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

### INLINESTATS - Keep All Rows While Aggregating ⚠️
**Purpose**: Add aggregate calculations without grouping

✅ CORRECT - Single BY clause for all aggregations:
```esql
FROM transactions
| INLINESTATS
    avg_amount = AVG(amount),
    max_amount = MAX(amount),
    total_count = COUNT(*)
  BY category
| EVAL variance_from_avg = amount - avg_amount
| WHERE variance_from_avg > 1000
```

❌ WRONG - Multiple BY clauses (one per aggregation):
```esql
FROM transactions
| INLINESTATS
    avg_amount = AVG(amount) BY category,
    max_amount = MAX(amount) BY category  -- ❌ Syntax error!
```

**Rule**: INLINESTATS uses the SAME syntax as STATS - ONE BY clause at the end that applies to ALL aggregations.

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
Note: NO `@timestamp` filter - users control time via Kibana time picker

### 2. Parameterized Query (Required Parameters Only)
```esql
FROM customers
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE region == ?region
| WHERE segment == ?segment
| STATS
    customer_count = COUNT(*),
    avg_revenue = AVG(total_revenue)
  BY plan_type
| SORT customer_count DESC
```
Note: ALL parameters are REQUIRED. No NULL checking or optional params.
Time filtering uses ?start_date and ?end_date parameters (NOT NOW())

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

### 4. Complex Aggregation with Enrichment (Scripted)
```esql
FROM call_events
| LOOKUP JOIN agents ON agent_id
| LOOKUP JOIN customers ON customer_id
| STATS
    call_count = COUNT(*),
    avg_duration = AVG(duration_seconds),
    resolved = SUM(CASE(status == "resolved", 1, 0))
  BY team, tier, segment
| EVAL resolution_rate = TO_DOUBLE(resolved) * 100.0 / call_count
| WHERE call_count > 10
| SORT resolution_rate DESC
```
Note: No `@timestamp` filter - Kibana time picker controls the time range
"""

# ============================================================================
# COMMON ERROR FIXES
# ============================================================================

COMMON_ERROR_FIXES = """
## Common ES|QL Errors and Their Fixes

| Error Pattern | Root Cause | Fix |
|--------------|------------|-----|
| "Unknown column [field] in right/left side of join" | Join key doesn't exist in both datasets | **CANNOT AUTO-FIX** - Verify schemas and use field that exists in BOTH |
| "[-] has arguments with incompatible types [datetime]" | Direct datetime subtraction | Wrap both sides in TO_LONG(): `(TO_LONG(NOW()) - TO_LONG(field))` |
| "Unknown function [COUNT]" with DISTINCT | Using SQL `COUNT(DISTINCT field)` | Use `COUNT_DISTINCT(field)` instead |
| INLINESTATS syntax error with multiple BY | Multiple BY clauses per aggregation | Use ONE BY clause: `INLINESTATS a = AVG(x), b = MAX(y) BY category` |
| Query returns no results (scripted query) | Using `NOW() - X days` with static demo data | Remove `@timestamp` filters from scripted queries - use Kibana time picker |
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

**Note**: The first two errors are the MOST COMMON failures from production testing.
"""

# ============================================================================
# PROMPTING BEST PRACTICES
# ============================================================================

LLM_PROMPTING_GUIDELINES = """
## Guidelines for LLM Query Generation

### DO's:
1. ALWAYS validate field names against the actual schema before using them
2. ALWAYS verify LOOKUP JOIN keys exist in BOTH source AND lookup dataset schemas (CRITICAL!)
3. ALWAYS use TO_LONG() when subtracting datetime values
4. ALWAYS use scripted queries for testing before making parameterized versions
5. ALWAYS use TO_DOUBLE() for division operations
6. ALWAYS use @timestamp for time fields
7. ALWAYS put MATCH inside WHERE clause
8. ALWAYS check index mode compatibility for LOOKUP JOIN
9. ALWAYS omit `@timestamp` filters in SCRIPTED queries (let Kibana time picker control range)
10. ALWAYS use `?start_date` and `?end_date` parameters for time filtering in PARAMETERIZED queries
11. PREFER INLINESTATS over window functions
12. PREFER SUM(CASE()) over conditional COUNT

### DON'Ts:
1. NEVER use table prefixes after LOOKUP JOIN (use `specialty` not `providers.specialty`)
2. NEVER add _lookup suffix to index names
3. NEVER invent or assume LOOKUP JOIN keys - verify they exist in BOTH schemas first
4. NEVER subtract datetime values directly - always use TO_LONG() wrapper
5. NEVER check if parameters are NULL
6. NEVER use named branches in FORK
7. NEVER put comments inside FORK branches
8. NEVER use MATCH as a pipe operation
9. NEVER assume fields exist after STATS without including in GROUP BY
10. NEVER use COUNT_IF or other non-existent functions
11. NEVER mix parameter order in DATE functions
12. NEVER use SQL syntax `COUNT(DISTINCT field)` - use `COUNT_DISTINCT(field)` instead
13. NEVER use multiple BY clauses in INLINESTATS - use ONE BY clause for all aggregations
14. NEVER use `NOW() - X days` in SCRIPTED queries - omit time filters entirely
15. NEVER use `NOW()` in any query - use parameters or omit time filters

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

6. **Fix COUNT(DISTINCT ...) pattern**:
   - `COUNT(DISTINCT field)` → `COUNT_DISTINCT(field)`
   - This is SQL syntax, not ES|QL syntax

7. **Fix INLINESTATS multiple BY clauses**:
   - `INLINESTATS a = AVG(x) BY cat, b = MAX(y) BY cat` → `INLINESTATS a = AVG(x), b = MAX(y) BY cat`
   - Move all aggregations before the single BY clause

8. **Remove NOW() time filters from scripted queries**:
   - Delete lines like `WHERE @timestamp >= NOW() - 7 days`
   - Delete lines like `WHERE @timestamp > NOW() - 30 days`
   - Scripted queries should NOT filter by time - users control via Kibana time picker
   - Keep `@timestamp` filters ONLY in parameterized queries with `?start_date` and `?end_date`

9. **Replace invalid aggregates**:
   - `COUNT_IF(condition)` → `SUM(CASE(condition, 1, 0))`
   - `COUNT(*) WHERE condition` → `SUM(CASE(condition, 1, 0))` (if not supported)

10. **Fix division**:
   - `a / b` → `TO_DOUBLE(a) / b` (when precision needed)
   - `a / b` → `a * 1.0 / b` (alternative)

11. **Fix RERANK syntax**:
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