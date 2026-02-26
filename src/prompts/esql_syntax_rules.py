"""
ES|QL Syntax Rules and Best Practices
======================================

This module contains critical ES|QL syntax rules extracted from failure analysis.
These rules should be incorporated into query generation prompts to improve success rates.
"""

ESQL_CRITICAL_RULES = """
## CRITICAL ES|QL SYNTAX RULES - MUST FOLLOW

### 1. FORK Syntax
✅ CORRECT: `| FORK (WHERE emp_no == 10001) (WHERE emp_no == 10002)`
❌ WRONG: `| FORK (...), (...)` - NO COMMAS between branches!
❌ WRONG: `FORK` alone - Must be piped with `|`

### 2. MATCH Syntax (ALWAYS within WHERE)
✅ CORRECT: `WHERE MATCH(field, "search term")`
✅ CORRECT: `WHERE MATCH(field, ?parameter, {"fuzziness": "AUTO"})`
❌ WRONG: `| MATCH field "term"` - MATCH is NOT a pipe operation
❌ WRONG: `MATCH(field, term)` without WHERE - MUST be inside WHERE clause

### 3. RERANK Syntax (Pipe operation with inference endpoint)
✅ CORRECT: `| RERANK "query" ON field WITH { "inference_id" : "rerank_endpoint" }`
✅ CORRECT: `| RERANK ?question ON title, content WITH { "inference_id" : "my_reranker" }`
✅ CORRECT: `| RERANK score = "search term" ON content WITH { "inference_id" : "endpoint" }`
❌ WRONG: `| RERANK field "query"` - Missing ON keyword
❌ WRONG: `| RERANK "query" ON field MODEL "model"` - Use WITH, not MODEL
❌ WRONG: `WHERE RERANK(...)` - RERANK is a pipe operation, not a WHERE clause

### 4. LOOKUP JOIN Syntax
✅ CORRECT: `| LOOKUP JOIN table ON field`
✅ CORRECT: `| LOOKUP JOIN table ON field1 == field2 AND field3 == field4` - Complete binary expressions
❌ WRONG: `| LOOKUP table ON field` - Missing JOIN keyword
❌ WRONG: `| LOOKUP JOIN table_lookup ON field` - No _lookup suffix needed
❌ WRONG: `| LOOKUP JOIN table ON field1 == field2 AND field3` - Incomplete condition (missing right side)
❌ WRONG: Using same field name in both datasets (causes ambiguous reference error)

**CRITICAL - Complete Binary Expressions:**
Every JOIN ON condition must be complete: `field == field`, not just `field`

**CRITICAL - Unique Field Names:**
Ensure field names are UNIQUE between main and lookup datasets to avoid ambiguous references.
Use different names: `order_status` vs `status_name` (not both `status`)

### 5. Index Modes
- **data_stream**: Regular timeseries data (default mode)
- **lookup**: Small reference tables for enrichment
- When using LOOKUP JOIN, the target table must be in lookup mode

### 6. Query Parameters (Agent Builder)
✅ CORRECT: `WHERE field == ?parameter`
✅ CORRECT: `WHERE MATCH(field, ?search_term)`
❌ WRONG: `WHERE ?parameter IS NULL` - Cannot check NULL on parameters
❌ WRONG: `WHERE field == ?parameter OR ?parameter IS NULL` - No optional parameters

### 7. Field Names
- Use `@timestamp` for time fields, not `timestamp`
- Use exact field names from schema - no invented fields
- Text fields for MATCH must be text or semantic_text type

### 8. STATS vs INLINESTATS
- `STATS`: Aggregates and removes individual rows (like GROUP BY)
- `INLINESTATS`: Adds aggregate columns while keeping all rows
- For RAG queries, use INLINESTATS to preserve context

### 9. Common Command Order
1. FROM index_name
2. WHERE filters
3. EVAL calculations
4. STATS/INLINESTATS aggregations
5. KEEP/DROP fields
6. SORT ordering
7. LIMIT rows

### 10. DATE Functions
✅ CORRECT: `DATE_TRUNC(1 hour, @timestamp)`
✅ CORRECT: `DATE_EXTRACT("month", @timestamp)`
❌ WRONG: `DATE_TRUNC(@timestamp, 1 hour)` - Wrong parameter order

### 11. COMPLETION Syntax (LLM text generation)
✅ CORRECT (9.2.0+): `| COMPLETION prompt WITH { "inference_id" : "completion_endpoint" }`
✅ CORRECT (9.2.0+): `| COMPLETION answer = prompt WITH { "inference_id" : "gpt4_endpoint" }`
✅ CORRECT (9.1.x): `| COMPLETION prompt WITH completion_endpoint`
❌ WRONG: `| COMPLETION "prompt" MODEL "gpt-4"` - Use WITH, not MODEL
❌ WRONG: `| COMPLETION prompt` - Must specify inference endpoint
❌ WRONG: Template syntax like `{{#results}}` - Not supported in ES|QL
⚠️ WARNING: Every row generates 1 LLM API call - always use LIMIT!

**Building Prompts from Row Data:**
- Use EVAL + CONCAT() to build prompts from field values
- Example: `| EVAL prompt = CONCAT("Summarize: ", title, " - ", content)`
- Cannot use template/loop syntax - ES|QL processes row by row

**Best Practices:**
1. Filter with WHERE before COMPLETION to reduce API calls
2. Always use LIMIT (start small, like 5-10 rows)
3. Build prompts with EVAL before COMPLETION
4. Use MATCH → RERANK → LIMIT → COMPLETION pipeline for relevance

### 12. String Literals (No Newlines or Escape Sequences)
ES|QL string literals use double quotes and do NOT support escape sequences.
Any newline character (literal or escaped) inside a string causes a parsing_exception.

✅ CORRECT: `"Hello World"` — simple single-line string
✅ CORRECT: `CONCAT("Part one. ", "Part two. ", "Field: ", field_name)` — separate args
❌ WRONG: `"Line one\nLine two"` — \\n escape not supported
❌ WRONG: `"Line one\\nLine two"` — \\\\n escape not supported
❌ WRONG: String literals that span multiple lines in the query text
❌ WRONG: `'single quotes'` — only double quotes are valid

**For CONCAT prompts (used with COMPLETION):**
Break long text into separate CONCAT arguments, each on one line:
```esql
| EVAL prompt = CONCAT(
    "You are an expert assistant. ",
    "Based on this document, provide a summary. ",
    "Title: ", title, " ",
    "Content: ", content)
```
Use spaces or periods to separate sections — NEVER use \\n or newline characters.
"""

ESQL_QUERY_EXAMPLES = """
## Example Queries by Type

### Scripted Query (Fixed values)
```esql
FROM support_tickets
| WHERE @timestamp >= NOW() - 7 days
  AND priority == "High"
| STATS ticket_count = COUNT(*),
        avg_resolution = AVG(resolution_time)
  BY category
| SORT ticket_count DESC
| LIMIT 10
```

### Parameterized Query (Agent Builder tool)
```esql
FROM customers
| WHERE segment == ?customer_segment
  AND region == ?selected_region
| LOOKUP JOIN orders ON customer_id
| STATS total_revenue = SUM(orders.amount),
        order_count = COUNT(orders.order_id)
  BY customer_name
| SORT total_revenue DESC
```

### RAG Query (Semantic search with MATCH → RERANK → COMPLETION)
```esql
FROM knowledge_base
| WHERE MATCH(content, ?user_question, {"fuzziness": "AUTO"})
| SORT _score DESC
| LIMIT 100
| RERANK ?user_question ON title, content WITH { "inference_id" : "rerank_endpoint" }
| LIMIT 5
| EVAL prompt = CONCAT(
    "Answer this question based on the article: ",
    ?user_question, " ",
    "Article Title: ", title, " ",
    "Content: ", content
  )
| COMPLETION answer = prompt WITH { "inference_id" : "completion_endpoint" }
| KEEP title, content, answer, _score
```

### RAG Query (Simple MATCH only, no COMPLETION)
```esql
FROM knowledge_base
| WHERE MATCH(content, ?user_question)
| SORT _score DESC
| LIMIT 10
| KEEP article_id, title, content, category, _score
```

### FORK Query (Multiple branches)
```esql
FROM transactions
| FORK
  (WHERE amount > 1000 | STATS high_value = COUNT(*))
  (WHERE amount <= 1000 | STATS low_value = COUNT(*))
  (STATS total = COUNT(*))
```
"""

def get_esql_rules_for_prompt():
    """Get ES|QL rules formatted for LLM prompts"""
    return ESQL_CRITICAL_RULES

def get_esql_examples_for_prompt():
    """Get ES|QL example queries for LLM prompts"""
    return ESQL_QUERY_EXAMPLES

def get_common_error_fixes():
    """Get common ES|QL error patterns and their fixes"""
    return """
## Common ES|QL Errors and Fixes

| Error Message | Likely Cause | Fix |
|--------------|--------------|-----|
| "Unknown column [agents_lookup]" | Using _lookup suffix | Remove _lookup suffix |
| "line X:Y: mismatched input ',' expecting '('" | FORK with commas | Remove commas between branches |
| "JOIN ON clause only supports fields or AND of Binary Expressions" | Incomplete JOIN condition | Complete binary expression: `field1 == field2 AND field3 == field4` |
| "Found ambiguous reference to [field]" | Same field in both datasets | Rename fields during data generation to be unique |
| "Unknown function [MATCH]" | MATCH outside WHERE | Move MATCH inside WHERE clause |
| "mismatched input 'MATCH' expecting" | MATCH used as pipe command | Use WHERE MATCH(field, "query") |
| "Lookup Join requires a single lookup mode index" | Target not in lookup mode | Ensure target index is lookup mode |
| "Unknown column [?param]" | Parameter in wrong context | Parameters only in WHERE/MATCH |
| "cannot use [==] on unsupported" | Type mismatch | Check field types match values |
| "Unknown command [MODEL]" | Using MODEL keyword | Use WITH { "inference_id" : "..." } |
| "token recognition error at: '{{'" | Template syntax in query | Use EVAL + CONCAT() to build prompts |
| "token recognition error at: '\"...\\n'" | Newline in string literal | Break into separate CONCAT args, no \\n |
| "RERANK requires inference_id" | Missing WITH clause | Add WITH { "inference_id" : "..." } |
| "COMPLETION requires inference_id" | Missing WITH clause | Add WITH { "inference_id" : "..." } |
"""