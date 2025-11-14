# MCP Configuration Guide for Elastic Agent Builder

This guide shows how to configure Claude Code (and other MCP clients) to connect to Elastic's built-in MCP server for real-time ES|QL query validation and execution.

## What is Elastic's MCP Server?

Elastic Agent Builder includes a **built-in MCP (Model Context Protocol) server** accessible via Kibana's API. This allows AI assistants like Claude Code to:

- Execute ES|QL queries in real-time
- Validate query syntax before demos
- List and manage Agent Builder tools
- Test integrations programmatically

**Important**: There is NO separate npm package to install. The MCP server is built into Kibana at version 8.17.0+.

## Prerequisites

Before configuring MCP, you need:

1. **Elastic Deployment** (Cloud or self-managed)
   - Kibana 8.17.0 or later
   - Agent Builder enabled

2. **API Key** with appropriate permissions
   - Generate via Kibana UI: Search "API keys" in global search
   - Requires permissions for indices you want to query

3. **MCP Client** (one of):
   - Claude Code (recommended for this project)
   - Claude Desktop
   - Cursor
   - VS Code with MCP extension

## Configuration Steps

### Step 1: Generate Elastic API Key

1. Open Kibana
2. Search for "API keys" in the global search bar
3. Click "Create API key"
4. Configure permissions:
   - Name: `agent-builder-mcp`
   - Indices: Grant read access to your demo indices
   - Agent Builder: Enable tool execution permissions
5. Copy the API key (you won't see it again!)

### Step 2: Configure MCP Client

#### For Claude Code

Add this configuration to your project's `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "elastic-agent-builder": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "${KIBANA_URL}/api/agent_builder/mcp",
        "--header",
        "Authorization:${AUTH_HEADER}"
      ],
      "env": {
        "KIBANA_URL": "https://your-deployment.kb.us-central1.gcp.cloud.es.io:9243",
        "AUTH_HEADER": "ApiKey YOUR_API_KEY_HERE"
      }
    }
  }
}
```

**Configuration Notes**:
- Replace `KIBANA_URL` with your actual Kibana URL
- Replace `YOUR_API_KEY_HERE` with the API key from Step 1
- Do NOT include a trailing slash on the Kibana URL
- The `ApiKey` prefix is required in the `AUTH_HEADER`

#### For Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "elastic-agent-builder": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://your-deployment.kb.us-central1.gcp.cloud.es.io:9243/api/agent_builder/mcp",
        "--header",
        "Authorization:ApiKey YOUR_API_KEY_HERE"
      ]
    }
  }
}
```

### Step 3: Verify Connection

Test the connection using Claude Code:

```bash
# Start a Claude Code session
# Ask Claude: "Can you list the available Elasticsearch MCP tools?"
```

Expected response should include tools like:
- `esql_query` - Execute ES|QL queries
- `list_tools` - List Agent Builder tools
- `execute_tool` - Execute a specific tool

## Security Best Practices

### Environment Variables (Recommended)

Instead of hardcoding credentials, use environment variables:

1. Create `.env` file in your project root:

```bash
ELASTIC_KIBANA_URL=https://your-deployment.kb.us-central1.gcp.cloud.es.io:9243
ELASTIC_API_KEY=your_api_key_here
```

2. Add `.env` to `.gitignore`:

```bash
echo ".env" >> .gitignore
```

3. Reference in `settings.local.json`:

```json
{
  "mcpServers": {
    "elastic-agent-builder": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "${ELASTIC_KIBANA_URL}/api/agent_builder/mcp",
        "--header",
        "Authorization:ApiKey ${ELASTIC_API_KEY}"
      ],
      "env": {
        "ELASTIC_KIBANA_URL": "${ELASTIC_KIBANA_URL}",
        "ELASTIC_API_KEY": "${ELASTIC_API_KEY}"
      }
    }
  }
}
```

### API Key Permissions

Grant minimum required permissions:

```json
{
  "cluster": ["monitor"],
  "indices": [
    {
      "names": ["your-demo-indices-*"],
      "privileges": ["read", "view_index_metadata"]
    }
  ],
  "applications": [
    {
      "application": "kibana-.kibana",
      "privileges": ["feature_agent_builder.read"],
      "resources": ["*"]
    }
  ]
}
```

## Available MCP Tools

Once configured, Claude Code can access these tools:

### `esql_query`
Execute ES|QL queries and return results.

**Example**:
```
Ask Claude: "Execute this ES|QL query: FROM accounts | LIMIT 5"
```

### `list_tools`
List all Agent Builder tools configured in your Kibana instance.

**Example**:
```
Ask Claude: "List all available Agent Builder tools"
```

### `execute_tool`
Execute a specific Agent Builder tool by ID.

**Example**:
```
Ask Claude: "Execute tool 'customer-lookup' with customer_id=12345"
```

### `get_mapping`
Retrieve index mappings to understand data structure.

**Example**:
```
Ask Claude: "Get the mapping for the 'accounts' index"
```

## Troubleshooting

### Connection Fails

**Error**: "Cannot connect to MCP server"

**Solutions**:
1. Verify Kibana URL is correct (no trailing slash)
2. Check API key is valid: `curl -H "Authorization: ApiKey YOUR_KEY" https://YOUR_KIBANA_URL/api/status`
3. Ensure Kibana version is 8.17.0+
4. Check network connectivity to Kibana

### API Key Permissions Error

**Error**: "Unauthorized" or "Insufficient permissions"

**Solutions**:
1. Verify API key has `feature_agent_builder.read` permission
2. Check index permissions include your demo indices
3. Regenerate API key with correct permissions

### MCP Remote Not Found

**Error**: "npx: command not found: mcp-remote"

**Solutions**:
1. Ensure Node.js is installed: `node --version`
2. Install mcp-remote globally: `npm install -g mcp-remote`
3. Or let npx download it on first use (requires internet)

### Query Execution Timeout

**Error**: "Query execution timed out"

**Solutions**:
1. Reduce dataset size for testing
2. Add timeout parameter to query
3. Optimize query with proper filters
4. Check Elasticsearch cluster health

## Integration with Demo Builder

### Using MCP in Skills

The `esql-validator` Skill uses MCP to validate queries:

```python
# In your demo generation workflow
from src.framework import ModularDemoOrchestrator

orchestrator = ModularDemoOrchestrator()
results = orchestrator.generate_new_demo(config)

# Now ask Claude Code to validate queries:
# "Validate all ES|QL queries in the generated demo module"
```

### Automated Testing

Use MCP in your test suite:

```python
# tests/test_query_validation.py
def test_generated_queries_execute():
    """Test that generated queries execute successfully via MCP"""

    # Generate demo
    results = generate_demo(test_config)

    # Ask Claude Code via MCP to execute each query
    for query in results['queries']:
        # Claude Code will use MCP to execute
        validation = validate_query_via_mcp(query['esql'])
        assert validation['success'], f"Query failed: {query['name']}"
```

## Claude Code Skills Using MCP

### ES|QL Validator Skill

Location: `.claude/skills/esql-validator.md`

This Skill uses MCP to:
- Validate ES|QL syntax
- Execute queries against live data
- Auto-fix common errors
- Analyze query performance

**Usage**:
```
Ask Claude: "Validate the queries in demos/acme_sales_20241023_140512/"
```

Claude will automatically:
1. Read the query_generator.py module
2. Extract ES|QL queries
3. Use MCP to execute each query
4. Report results and suggest fixes

## Example Workflows

### Workflow 1: Generate and Validate Demo

```
You: "Create a demo for Acme Corp's sales team tracking deal pipeline"

Claude: [Generates demo module]

You: "Validate all queries using Elasticsearch"

Claude: [Uses MCP to execute queries, reports results]
```

### Workflow 2: Debug Failing Query

```
You: "This query is failing: FROM accounts | STATS churn_rate = churned / total BY segment"

Claude: [Analyzes query]
"I see the issue - integer division. Let me test the fix via MCP..."

Claude: [Uses MCP to execute corrected query]
"Fixed! Use: STATS churn_rate = TO_DOUBLE(churned) / total"
```

### Workflow 3: Performance Testing

```
You: "Test the performance of all queries in this demo"

Claude: [Uses MCP to execute queries with timing]
"Results:
- Query 1: 45ms ✅
- Query 2: 230ms ⚠️  (could be optimized)
- Query 3: 12ms ✅"
```

## Advanced Configuration

### Multiple Elastic Deployments

Configure multiple MCP servers for different environments:

```json
{
  "mcpServers": {
    "elastic-dev": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "${DEV_KIBANA_URL}/api/agent_builder/mcp",
        "--header",
        "Authorization:ApiKey ${DEV_API_KEY}"
      ]
    },
    "elastic-prod": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "${PROD_KIBANA_URL}/api/agent_builder/mcp",
        "--header",
        "Authorization:ApiKey ${PROD_API_KEY}"
      ]
    }
  }
}
```

### Custom Headers

Add additional headers if needed:

```json
{
  "command": "npx",
  "args": [
    "mcp-remote",
    "${KIBANA_URL}/api/agent_builder/mcp",
    "--header",
    "Authorization:ApiKey ${API_KEY}",
    "--header",
    "kbn-xsrf:true"
  ]
}
```

### Timeout Configuration

Adjust timeouts for slow queries:

```json
{
  "command": "npx",
  "args": [
    "mcp-remote",
    "${KIBANA_URL}/api/agent_builder/mcp",
    "--header",
    "Authorization:ApiKey ${API_KEY}",
    "--timeout",
    "30000"
  ]
}
```

## Resources

### Official Documentation
- [Elastic Agent Builder MCP Server](https://www.elastic.co/docs/solutions/search/agent-builder/mcp-server)
- [Kibana API Reference](https://www.elastic.co/docs/solutions/search/agent-builder/kibana-api)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)

### Claude Code Documentation
- [Claude Code MCP Integration](https://docs.claude.com/en/docs/claude-code/mcp)
- [Claude Code Skills](https://docs.claude.com/en/docs/claude-code/skills)

### Demo Builder Resources
- [CLAUDE.md](../CLAUDE.md) - Project instructions
- [MODULAR_ARCHITECTURE.md](./MODULAR_ARCHITECTURE.md) - Architecture guide
- [ES|QL Validator Skill](../.claude/skills/esql-validator.md)

## Support

For issues with:
- **MCP Configuration**: Check this guide's troubleshooting section
- **Elastic API Keys**: Consult Kibana documentation
- **Claude Code**: Visit [Claude Code GitHub](https://github.com/anthropics/claude-code)
- **Demo Builder**: Open an issue in this repository

---

**Last Updated**: 2025-10-23
**Elastic Version**: 8.17.0+
**Claude Code Version**: Latest
