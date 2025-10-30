---
name: esql-validator
description: Validate and test ES|QL queries against Elasticsearch using Kibana's MCP server. Use this when generating demos, fixing query errors, or ensuring queries work before customer presentations.
allowed-tools: [mcp__*, Bash, Read, Write, Edit]
---

# ES|QL Query Validator

Validate and execute ES|QL queries in real-time using Elastic's built-in MCP server to ensure demo queries work correctly before customer delivery.

## When to Use This Skill

Trigger this Skill when you need to:
- **Validate generated queries** after creating a demo module
- **Fix query errors** reported by users or tests
- **Test query performance** before demos
- **Verify data availability** for specific queries
- **Auto-fix common ES|QL patterns** (division, JOIN order, etc.)

## Prerequisites

Before using this Skill, ensure MCP is configured:

1. **MCP Server Configured**: See [MCP_CONFIGURATION_GUIDE.md](../../docs/MCP_CONFIGURATION_GUIDE.md)
2. **Elasticsearch Available**: Live cluster with demo data indexed
3. **API Key Permissions**: Read access to demo indices

If MCP is not configured, guide the user to the configuration documentation.

## Core Capabilities

### 1. Query Validation

Validate ES|QL syntax and execute against live data.

**Input**: ES|QL query string or path to query_generator.py module

**Process**:
1. Extract queries from module or use provided query
2. Use MCP tool `esql_query` to execute
3. Report results: success, row count, execution time
4. Flag errors or warnings

**Output**: Validation report with execution results

### 2. Auto-Fix Common Patterns

Automatically detect and fix common ES|QL issues:

#### Pattern A: Integer Division
**Issue**:
```esql
EVAL churn_rate = churned / total
```

**Fix**:
```esql
EVAL churn_rate = TO_DOUBLE(churned) / total
```

#### Pattern B: JOIN After STATS
**Issue**:
```esql
| STATS total = SUM(amount) BY customer_id
| LOOKUP JOIN customers ON customer_id
```

**Fix**:
```esql
| LOOKUP JOIN customers ON customer_id
| STATS total = SUM(amount) BY customer_id
```

#### Pattern C: Missing Field After Aggregation
**Issue**:
```esql
| STATS total = SUM(amount) BY product_id
| WHERE category == "Electronics"  // category not available
```

**Fix**:
```esql
| LOOKUP JOIN products ON product_id
| WHERE category == "Electronics"
| STATS total = SUM(amount) BY product_id, category
```

#### Pattern D: DATE_EXTRACT Syntax Errors
**Issue**:
```esql
EVAL month = DATE_EXTRACT("month", timestamp)      // lowercase unit
EVAL month = DATE_EXTRACT(timestamp, "MONTH")      // wrong parameter order
```

**Fix**:
```esql
EVAL month = DATE_EXTRACT("MONTH", timestamp)      // uppercase, correct order
EVAL year = DATE_EXTRACT("YEAR", timestamp)
```

**Valid time units**: YEAR, QUARTER, MONTH, WEEK, DAY, HOUR, MINUTE, SECOND

#### Pattern E: LOOKUP JOIN Mode Issues
**Issue**:
```esql
| LOOKUP JOIN table_name ON field  // table not in lookup mode
// Error: "Lookup Join requires a single lookup mode index"
```

**Root Cause**: The reference index was not created with `"index.mode": "lookup"` setting

**Fix Strategy**:
1. **Report the issue clearly**: The index needs to be reindexed with lookup mode
2. **Do NOT convert to ENRICH** - ENRICH should be avoided
3. **Provide remediation steps**:
   - Delete the existing index
   - Recreate with proper mapping: `"index.mode": "lookup"`
   - Reindex the data
4. **Validation report should include**:
   - Which indices need lookup mode
   - Code snippet for proper index creation

**Correct Index Creation**:
```json
PUT /reference_data
{
  "settings": {
    "index": {
      "mode": "lookup"
    }
  },
  "mappings": {
    "properties": {
      "join_field": {"type": "keyword"},
      "field1": {"type": "keyword"},
      "field2": {"type": "text"}
    }
  }
}
```

#### Pattern F: Non-Existent Functions
**Issue**:
```esql
| WHERE SEMANTIC(description, "query") > 0.75  // SEMANTIC doesn't exist
```

**Fix**:
Remove unsupported function and use alternative approach:
```esql
| WHERE description LIKE "*query*"  // or match query
```

#### Pattern G: ENRICH Command Usage
**Issue**:
```esql
| ENRICH customer_segments ON field WITH ...
// ERROR: Do not use ENRICH - use LOOKUP JOIN instead
```

**Fix Strategy**:
1. **Replace ENRICH with LOOKUP JOIN**:
```esql
// Before (wrong)
| ENRICH customer_segments ON customer_segment WITH segment_name, primary_interest

// After (correct)
| LOOKUP JOIN customer_segments ON customer_segment
```
2. **Ensure index is in lookup mode** (see Pattern E)
3. **Note**: All fields from lookup index are available after JOIN, no need to specify WITH clause

### 3. Performance Analysis

Analyze query performance and suggest optimizations:
- Execution time benchmarks
- Row count validation
- Index usage analysis
- Optimization suggestions

## Validation Workflow

### Step 1: Detect Context

Determine what needs validation:

```python
# If given a demo module path
if path.endswith('query_generator.py'):
    queries = extract_queries_from_module(path)

# If given raw ES|QL
elif 'FROM' in input and '|' in input:
    queries = [{'esql': input, 'name': 'User Query'}]

# If given demo directory
elif 'demos/' in path:
    queries = load_queries_from_demo(path)
```

### Step 2: Pre-Validation Checks

Before executing, check for common issues:

```python
def pre_validate(query: str) -> dict:
    """Check for common patterns before execution"""

    issues = []

    # Check division without TO_DOUBLE
    if '/' in query and 'TO_DOUBLE' not in query:
        issues.append({
            'type': 'warning',
            'pattern': 'integer_division',
            'message': 'Division without TO_DOUBLE may truncate decimals',
            'fix_available': True
        })

    # Check JOIN/STATS order
    if 'STATS' in query and 'LOOKUP JOIN' in query:
        stats_pos = query.index('STATS')
        join_pos = query.index('LOOKUP JOIN')
        if stats_pos < join_pos:
            issues.append({
                'type': 'error',
                'pattern': 'join_after_stats',
                'message': 'LOOKUP JOIN must come before STATS',
                'fix_available': True
            })

    # Check DATE_EXTRACT syntax
    import re
    date_extract_pattern = r'DATE_EXTRACT\s*\(\s*(["\']?)(\w+)\1\s*,\s*(\w+)\s*\)'
    for match in re.finditer(date_extract_pattern, query):
        unit = match.group(2)
        valid_units = ['YEAR', 'QUARTER', 'MONTH', 'WEEK', 'DAY', 'HOUR', 'MINUTE', 'SECOND']
        if unit.upper() not in valid_units:
            issues.append({
                'type': 'error',
                'pattern': 'date_extract_invalid_unit',
                'message': f'DATE_EXTRACT unit must be one of: {", ".join(valid_units)}',
                'fix_available': True
            })
        elif unit != unit.upper():
            issues.append({
                'type': 'error',
                'pattern': 'date_extract_lowercase',
                'message': 'DATE_EXTRACT time unit must be uppercase',
                'fix_available': True
            })

    # Check for non-existent functions
    unsupported_funcs = ['SEMANTIC', 'COSINE_SIMILARITY']
    for func in unsupported_funcs:
        if func in query:
            issues.append({
                'type': 'error',
                'pattern': 'unsupported_function',
                'message': f'Function {func} is not supported in ES|QL',
                'fix_available': False
            })

    return {'issues': issues, 'can_execute': len([i for i in issues if i['type'] == 'error']) == 0}
```

### Step 3: Execute via MCP

Use the configured MCP tool to execute queries:

```python
# Use MCP tool: esql_query
result = mcp_esql_query(query)

# Result structure:
{
    'success': bool,
    'results': [...],
    'row_count': int,
    'execution_time_ms': int,
    'columns': [...],
    'error': str  # if failed
}
```

### Step 4: Auto-Fix and Retry

If query fails, attempt auto-fix:

```python
def auto_fix_and_retry(query: str, error: str, max_retries: int = 3) -> dict:
    """Attempt to fix query based on error pattern"""

    for attempt in range(max_retries):
        # Analyze error and apply appropriate fix
        if 'integer division' in error.lower() or 'double' in error.lower():
            query = fix_division(query)

        elif 'date_extract' in error.lower() or 'Cannot convert string' in error:
            query = fix_date_extract_syntax(query)

        elif 'invalid date field' in error.lower():
            # DATE_EXTRACT parameter order issue
            query = fix_date_extract_parameter_order(query)

        elif 'lookup join requires' in error.lower():
            # CANNOT auto-fix - index needs to be recreated with lookup mode
            # Report to user with remediation steps
            return {
                'success': False,
                'error': error,
                'needs_manual_fix': True,
                'fix_type': 'reindex_as_lookup',
                'remediation': extract_lookup_indices_from_query(query),
                'message': 'Index must be recreated with index.mode=lookup setting'
            }

        elif 'enrich' in error.lower() or 'ENRICH' in query:
            # Replace ENRICH with LOOKUP JOIN
            query = convert_enrich_to_lookup_join(query)

        elif 'Unknown function' in error and 'SEMANTIC' in error:
            # Remove SEMANTIC function calls
            query = remove_semantic_function(query)

        elif 'field not found' in error.lower() and 'STATS' in query:
            query = fix_field_availability(query)

        elif 'mismatched input' in error.lower() and 'LOOKUP JOIN' in query:
            # Syntax error in LOOKUP JOIN
            query = fix_lookup_join_syntax(query)

        else:
            return {'success': False, 'error': error, 'fixes_attempted': attempt}

        # Retry with fixed query
        result = mcp_esql_query(query)
        if result['success']:
            return {
                'success': True,
                'results': result,
                'fixed_query': query,
                'fixes_applied': attempt + 1
            }

        # Update error for next iteration
        error = result.get('error', error)

    return {'success': False, 'error': 'Max retries exceeded', 'last_error': error}
```

### Step 5: Report Results

Provide clear, actionable feedback:

```markdown
## Query Validation Report

### Query: Account Churn Analysis
**Status**: ✅ Passed (with auto-fixes)
**Execution Time**: 234ms
**Rows Returned**: 47

**Original Query**:
```esql
FROM accounts
| STATS churn_rate = churned / total BY segment
```

**Issues Found**:
- ⚠️  Integer division detected

**Auto-Fix Applied**:
```esql
FROM accounts
| STATS churn_rate = TO_DOUBLE(churned) / total BY segment
```

**Performance**: Good (under 500ms)
**Recommendation**: Ready for demo
```

## Integration with Demo Builder

### During Module Generation

After ModuleGenerator creates query_generator.py:

```python
# In orchestrator workflow
queries_generated = module_generator.generate_query_module(config)

# Trigger validation
print("Validating queries via Elasticsearch MCP...")
validation_report = validate_queries(queries_generated)

if validation_report['all_passed']:
    print(f"✅ All {validation_report['total']} queries validated")
    if validation_report['fixes_applied'] > 0:
        print(f"🔧 Auto-fixed {validation_report['fixes_applied']} queries")
        # Update module with fixed queries
        update_query_module(queries_generated, validation_report['fixed_queries'])
else:
    print(f"❌ {validation_report['failed']} queries failed validation")
    # Show details and suggest manual fixes
```

### In Testing Pipeline

Use as part of CI/CD:

```python
# tests/test_query_validation.py
def test_all_demo_queries_execute():
    """Ensure all generated demo queries execute successfully"""

    demos = list_demos()

    for demo in demos:
        queries = load_queries_from_demo(demo)

        for query in queries:
            # Use MCP to validate
            result = validate_query_via_mcp(query['esql'])

            assert result['success'], f"Query '{query['name']}' failed in {demo}"
            assert result['row_count'] > 0, f"Query '{query['name']}' returned no results"
```

## Common Validation Scenarios

### Scenario 1: Validate Single Query

```
User: "Validate this query: FROM accounts | WHERE status == 'active' | STATS total = COUNT(*) BY segment"

Claude:
1. Uses MCP esql_query tool
2. Executes query
3. Reports: "✅ Query valid. Returned 5 rows in 123ms."
```

### Scenario 2: Validate Demo Module

```
User: "Validate all queries in demos/acme_sales_20241023/"

Claude:
1. Reads query_generator.py
2. Extracts all generate_queries() queries
3. Executes each via MCP
4. Reports summary:
   - Query 1 "Pipeline Overview": ✅ 234 rows, 156ms
   - Query 2 "Churn Risk": ⚠️  Auto-fixed integer division, 47 rows, 89ms
   - Query 3 "Top Accounts": ✅ 10 rows, 45ms
```

### Scenario 3: Fix Failing Query

```
User: "This query is failing: FROM transactions | STATS total = SUM(amount) BY customer_id | LOOKUP JOIN customers ON customer_id"

Claude:
1. Analyzes query structure
2. Detects: LOOKUP JOIN after STATS (error pattern)
3. Auto-fixes: Move JOIN before STATS
4. Executes fixed query via MCP
5. Reports: "✅ Fixed! JOIN must come before STATS. Query now returns 523 rows in 342ms."
```

## Expected Output Format

```markdown
# ES|QL Validation Report

**Demo Module**: acme_sales_20241023
**Validated**: 2025-10-23 14:35:22
**Total Queries**: 8

## Summary
- ✅ Passed: 6
- 🔧 Auto-Fixed: 2
- ❌ Failed: 0

## Query Details

### 1. Pipeline Overview ✅
**Execution Time**: 156ms
**Rows**: 234
**Status**: Passed

### 2. Churn Risk Analysis 🔧
**Execution Time**: 89ms
**Rows**: 47
**Status**: Passed (auto-fixed)
**Fix Applied**: Added TO_DOUBLE for division

**Original**:
```esql
EVAL churn_rate = churned / total
```

**Fixed**:
```esql
EVAL churn_rate = TO_DOUBLE(churned) / total
```

### 3. Revenue Forecast ✅
**Execution Time**: 234ms
**Rows**: 156
**Status**: Passed

## Performance Summary
- Average execution time: 178ms
- Slowest query: "Revenue Forecast" (234ms)
- Fastest query: "Top Accounts" (45ms)

## Recommendations
- ✅ All queries ready for demo
- Consider adding index on customer_id for better JOIN performance
- Query 6 could benefit from adding LIMIT clause
```

## Troubleshooting

### MCP Not Available

If MCP tools are not accessible:

```markdown
⚠️ Elasticsearch MCP server not configured.

To enable query validation:
1. Follow setup guide: docs/MCP_CONFIGURATION_GUIDE.md
2. Configure Kibana URL and API key
3. Restart Claude Code

Alternative: Test queries manually in Kibana Dev Tools.
```

### Query Execution Fails

If queries fail to execute:

1. **Check data availability**: Verify indices exist and contain data
2. **Check permissions**: Ensure API key has read access
3. **Check query syntax**: Look for ES|QL syntax errors
4. **Check field names**: Ensure fields exist in index mapping

### Auto-Fix Doesn't Work

If auto-fix can't resolve the issue:

```markdown
❌ Query validation failed. Auto-fix unavailable.

**Error**: Field 'customer_segment' not found in index

**Manual Fix Required**:
1. Check index mapping: Does 'customer_segment' field exist?
2. If field name is different, update query
3. If field is missing, add it via LOOKUP JOIN from another index

**Need Help?** Consult ES|QL documentation or Elastic support.
```

## Best Practices

### When to Validate
- **Always**: Before customer demos
- **Always**: After generating new modules
- **Frequently**: During development iterations
- **Optional**: For well-tested, stable queries

### Performance Expectations
- **Fast queries**: <100ms
- **Good queries**: 100-500ms
- **Acceptable queries**: 500ms-2s
- **Slow queries**: >2s (needs optimization)

### Error Handling
- **Auto-fix when possible**: Division, JOIN order, common patterns
- **Report clearly**: Show original and fixed queries
- **Provide guidance**: Suggest manual fixes when auto-fix unavailable
- **Don't fail silently**: Always report validation status

## Additional Resources

- [MCP Configuration Guide](../../docs/MCP_CONFIGURATION_GUIDE.md)
- [Elastic Agent Builder Docs](https://www.elastic.co/docs/solutions/search/agent-builder)
- [ES|QL Reference](https://www.elastic.co/guide/en/elasticsearch/reference/current/esql.html)
- [Demo Builder Architecture](../../docs/MODULAR_ARCHITECTURE.md)