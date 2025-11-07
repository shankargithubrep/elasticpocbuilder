# Parameterized ES|QL Query Testing

## Overview

This document describes the test suite for parameterized ES|QL queries that can be executed via the Elastic Agent Builder API.

## Test File

**Location:** `tests/test_parameterized_esql.py`

**Test Results:** ✅ 19 passed, 1 skipped (integration test)

## What Are Parameterized ES|QL Queries?

Parameterized ES|QL queries allow you to create reusable query templates with dynamic parameters. This is documented in `docs/esql/esql-tools.md`.

### Syntax

```esql
FROM provider_directory
| WHERE specialty == ?specialty
  AND state == ?state
| LIMIT 25
```

Parameters use the `?parameter_name` syntax and must be defined with:
- **name**: Parameter identifier
- **type**: Data type (string, integer, date, etc.)
- **description**: User-facing explanation
- **required**: Whether the parameter is mandatory
- **default_value**: Optional default if not required

### Supported Parameter Types

- `string`, `keyword`
- `long`, `integer`, `double`, `float`
- `boolean`, `date`
- `object`, `nested`

## Test Suite Structure

### 1. TestParameterizedESQLQueries
Core functionality tests for parameterized queries.

**Tests:**
- `test_parameter_syntax_validation` - Validates `?param` syntax in queries
- `test_parameter_type_validation` - Ensures parameter types are valid
- `test_create_esql_tool_with_parameters` - Tests tool creation with parameters
- `test_execute_tool_with_parameters` - Tests executing tools with parameter values
- `test_date_parameter_handling` - Validates date parameter handling
- `test_multiple_parameter_types` - Tests queries with mixed parameter types
- `test_load_queries_from_demo` - Loads real parameterized queries from generated demos
- `test_parameter_descriptions` - Validates parameter documentation quality
- `test_required_vs_optional_parameters` - Tests optional parameters with defaults
- `test_parameter_naming_conventions` - Validates parameter naming best practices
- `test_query_with_lookup_join_and_parameters` - Tests parameters with LOOKUP JOIN

### 2. TestParameterValidation
Parameter validation logic tests.

**Tests:**
- `test_missing_parameter_detection` - Detects params in query but not defined
- `test_unused_parameter_detection` - Detects defined params not used in query
- `test_invalid_parameter_type` - Rejects invalid parameter types

### 3. TestMCPIntegration
Tests for MCP tool integration.

**Tests:**
- `test_execute_esql_via_mcp` - Demonstrates MCP tool execution pattern
- `test_generate_esql_with_context` - Tests natural language to parameterized query

### 4. TestRealWorldScenarios
Real-world use case tests.

**Tests:**
- `test_provider_search_scenario` - Healthcare provider lookup workflow
- `test_member_history_scenario` - Member authorization history lookup
- `test_time_range_analysis_scenario` - Time-based analytics with date parameters

## Running the Tests

### Run All Tests
```bash
source venv/bin/activate
python -m pytest tests/test_parameterized_esql.py -v
```

### Run Specific Test Class
```bash
python -m pytest tests/test_parameterized_esql.py::TestParameterizedESQLQueries -v
```

### Run Single Test
```bash
python -m pytest tests/test_parameterized_esql.py::TestParameterizedESQLQueries::test_parameter_syntax_validation -v
```

### Run with Coverage
```bash
python -m pytest tests/test_parameterized_esql.py --cov=src.services.elastic_agent_builder_client --cov-report=html
```

## Integration Testing

The test suite includes an integration test that validates against a live Elasticsearch cluster:

```bash
# Credentials loaded from .env file
python -m pytest tests/test_parameterized_esql.py::TestParameterizedESQLQueries::test_real_parameterized_query_execution -v
```

**Note:** This test is currently skipped because the Agent Builder API endpoint may not be available in all deployments.

## Real Demo Examples

The test suite validates parameterized queries from the UnitedHealth call center demo:

**Demo Path:**
```
demos/unitedhealth_group_call center operations_20251104_143942/queries.json
```

**Example Parameterized Queries:**
1. **Provider Network Lookup** - Search by specialty, state, and plan network
2. **Member Prior Authorization History** - Lookup by member ID
3. **Claims Denial Analysis** - Filter by provider and date range
4. **Call Performance by Agent** - Analyze by agent ID and time range

## Key Findings

### ✅ No RANK Syntax Issues
- Searched entire codebase for RANK queries
- Found RERANK command in `docs/esql/rerank.md` (semantic reranking with inference)
- No RANK or RERANK queries found in any `queries.json` files
- All queries use standard ES|QL commands (FROM, WHERE, STATS, LOOKUP JOIN)

### ✅ Parameterized Query Pattern Validated
- All parameterized queries in demo follow correct `?parameter_name` syntax
- Parameter definitions match usage in queries
- Parameter types are valid ES|QL types
- Descriptions include helpful examples

## Best Practices

### Parameter Naming
- Use `snake_case` for parameter names
- Make names descriptive (min 3 characters)
- Don't start with underscore
- Example: `start_date`, `provider_id`, `specialty`

### Parameter Descriptions
- Include examples in descriptions
- Example: "Two-letter state code (e.g., IL, CA, TX)"
- Minimum 10 characters
- Explain the expected format

### Query Structure
- Use parameters in WHERE clauses
- Parameters work with LOOKUP JOIN
- Always include LIMIT clause
- Filter data before applying parameters for performance

### Parameter Types
- Use `string` for text matching
- Use `date` for timestamp comparisons
- Use `integer` or `long` for numeric filters
- Use `boolean` for true/false conditions

## API Client Usage

```python
from src.services.elastic_agent_builder_client import (
    ElasticAgentBuilderClient,
    ESQLTool,
    ToolParameter,
    ParameterType
)

# Create client
client = ElasticAgentBuilderClient(
    kibana_url=os.getenv("ELASTICSEARCH_KIBANA_URL"),
    api_key=os.getenv("ELASTICSEARCH_API_KEY")
)

# Define parameters
parameters = [
    ToolParameter(
        name="specialty",
        type=ParameterType.STRING,
        description="Provider specialty (e.g., Cardiology)",
        required=True
    )
]

# Create tool
tool = ESQLTool(
    id="provider-search",
    name="Provider Network Search",
    description="Search providers by specialty and location",
    query="FROM provider_directory | WHERE specialty == ?specialty | LIMIT 25",
    parameters=parameters
)

# Execute tool with parameters
result = client.execute_tool(
    tool_id="provider-search",
    parameters={"specialty": "Cardiology"}
)
```

## MCP Tool Usage

When using MCP tools (available in Claude Desktop with MCP server configured):

```python
# Execute ES|QL query
result = mcp__elastic_agent_builder__platform_core_execute_esql(
    query="FROM provider_directory | WHERE specialty == 'Cardiology' | LIMIT 5"
)

# Generate ES|QL from natural language
result = mcp__elastic_agent_builder__platform_core_generate_esql(
    query="Find cardiologists in Illinois",
    context="Healthcare provider directory"
)
```

## Related Documentation

- **ES|QL Tools:** `docs/esql/esql-tools.md`
- **ES|QL Completion:** `docs/esql/completion.md`
- **RERANK Command:** `docs/esql/rerank.md`
- **Client Implementation:** `src/services/elastic_agent_builder_client.py`

## Contributing

When adding new parameterized query tests:

1. Add test to appropriate test class
2. Use fixtures for sample queries
3. Test both valid and invalid scenarios
4. Include real-world use case examples
5. Document expected behavior in docstrings

## Future Enhancements

- [ ] Add actual API integration test when endpoint is available
- [ ] Test query validation with Elasticsearch
- [ ] Add performance benchmarks for parameterized queries
- [ ] Test error handling for invalid parameter values
- [ ] Add tests for nested/object parameter types
