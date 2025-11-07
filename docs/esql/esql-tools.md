---
title: ES|QL tools
description: ES|QL query tools enable you to create parameterized queries that execute directly against your Elasticsearch data. These custom tools provide precise...
url: https://www.elastic.co/docs/solutions/search/agent-builder/tools/esql-tools
---

# ES|QL tools

ES|QL query tools enable you to create parameterized queries that execute directly against your Elasticsearch data. These custom tools provide precise control over data retrieval through templated [ES|QL](https://www.elastic.co/docs/reference/query-languages/esql) statements.

## When to use ES|QL tools

Use custom **ES|QL tools** when:
- You need precise control over the query logic
- Your use case involves repeatable analytical patterns
- You want to expose specific, parameterized queries to agents
- Results should be in a predictable tabular format
- You have well-defined data retrieval requirements


## Key characteristics

- Execute pre-defined ES|QL queries with dynamic parameters
- Support typed parameters
- Return results in tabular format for structured data analysis
- Ideal for repeatable analytical queries with variable inputs


## Parameter types

ES|QL tools support the following parameter types:
- **String types**: `text`, `keyword`
- **Numeric types**: `long`, `integer`, `double`, `float`
- **Other types**: `boolean`, `date`, `object`, `nested`


## Parameter options

Parameters can be configured as:
- **Required**: Must be provided by the agent when calling the tool
- **Optional**: Can be omitted; uses `null` if no default is specified


## Query syntax

In your ES|QL query, reference parameters using the `?parameter_name` syntax. The agent will automatically interpolate parameter values when executing the query.

### Example

Here's an example ES|QL tool that searches for books using full-text search. `?search_terms` is a named parameter that the agent will provide when executing the query.
```esql
FROM books
| WHERE MATCH(title, ?search_terms)
| KEEP title, author, year
| LIMIT 10
```

You can ask the LLM to infer the parameters for the query or add them manually.
![Creating an ES|QL tool with a parameterized query](https://www.elastic.co/docs/solutions/search/agent-builder/images/create-esql-tool-query.png)


## Best practices

- **Include [`LIMIT`](https://www.elastic.co/docs/reference/query-languages/esql/commands/limit) clauses**: Prevent returning excessive results by setting reasonable limits
- **Use meaningful parameter names**: Choose names that clearly indicate what the parameter represents (e.g., `start_date` instead of `date1`)
- **Define parameter types**: Ensure parameters have the correct type to avoid runtime errors
- **Provide clear descriptions**: Help agents understand when and how to use each parameter


## Limitations

ES|QL tools are subject to the current limitations of the ES|QL language itself. For more information, refer to [ES|QL tool limitations](/docs/solutions/search/agent-builder/limitations-known-issues#esql-limitations).

## ES|QL documentation

To learn more about the language, refer to the [ES|QL docs](https://www.elastic.co/docs/reference/query-languages/esql).
