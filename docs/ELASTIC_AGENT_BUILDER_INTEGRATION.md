# Elastic Agent Builder Integration Guide
## Official APIs and Implementation Strategy

---

## 📚 Overview

This document integrates official Elastic Agent Builder documentation with our Demo Builder platform, providing a complete blueprint for creating, managing, and deploying AI-powered analytics agents programmatically.

---

## 🔑 Key API Endpoints

### Authentication Setup
```bash
export KIBANA_URL="your-kibana-url"
export API_KEY="your-api-key"
```

All API requests require:
- `Authorization: ApiKey ${API_KEY}` header
- `kbn-xsrf: true` header for state-changing operations

### Core Endpoints We'll Use

#### Tools Management
```
POST   /api/agent_builder/tools           # Create new tool
GET    /api/agent_builder/tools           # List all tools
PUT    /api/agent_builder/tools/{toolId}  # Update tool
POST   /api/agent_builder/tools/_execute  # Test tool execution
DELETE /api/agent_builder/tools/{id}      # Delete tool
```

#### Agents Management
```
POST   /api/agent_builder/agents          # Create agent
GET    /api/agent_builder/agents          # List agents
PUT    /api/agent_builder/agents/{id}     # Update agent
DELETE /api/agent_builder/agents/{id}     # Delete agent
```

#### Conversations
```
POST   /api/agent_builder/converse        # Start chat
POST   /api/agent_builder/converse/async  # Stream chat
GET    /api/agent_builder/conversations   # List conversations
```

---

## 🛠️ Tool Types & Creation Strategy

### 1. ES|QL Tools (For Precise Analytics)

**When to Use**: Structured queries with predictable output, complex aggregations, time-series analysis

**Creation Pattern**:
```python
def create_esql_tool(kibana_url, api_key, tool_config):
    """Create an ES|QL tool via Kibana API"""

    tool_payload = {
        "id": tool_config["id"],
        "name": tool_config["name"],
        "description": tool_config["description"],
        "type": "esql",
        "esql": {
            "query": tool_config["query"],  # Uses ?parameter_name syntax
            "parameters": tool_config["parameters"]
        },
        "labels": tool_config.get("labels", [])
    }

    response = requests.post(
        f"{kibana_url}/api/agent_builder/tools",
        headers={
            "Authorization": f"ApiKey {api_key}",
            "kbn-xsrf": "true"
        },
        json=tool_payload
    )
    return response.json()
```

**Parameter Syntax in ES|QL**:
```sql
FROM campaign_performance
| WHERE Date >= ?start_date AND Date <= ?end_date
| STATS revenue = SUM(Revenue) BY ?group_by_field
| LIMIT ?limit
```

### 2. Index Search Tools (For Flexible Exploration)

**When to Use**: Natural language queries, exploratory searches, varied search intent

**Creation Pattern**:
```python
def create_index_search_tool(kibana_url, api_key, tool_config):
    """Create an index search tool"""

    tool_payload = {
        "id": tool_config["id"],
        "name": tool_config["name"],
        "description": tool_config["description"],
        "type": "index_search",
        "pattern": tool_config["pattern"],  # e.g., "logs-*", "brand-assets"
        "labels": tool_config.get("labels", [])
    }

    response = requests.post(
        f"{kibana_url}/api/agent_builder/tools",
        headers={
            "Authorization": f"ApiKey {api_key}",
            "kbn-xsrf": "true"
        },
        json=tool_payload
    )
    return response.json()
```

---

## 🤖 Agent Creation & Configuration

### Agent Creation via API

```python
def create_agent(kibana_url, api_key, agent_config):
    """Create a fully configured agent"""

    agent_payload = {
        "id": agent_config["id"],
        "display_name": agent_config["display_name"],
        "description": agent_config["description"],
        "instructions": agent_config["instructions"],
        "tools": agent_config["tool_ids"],  # List of tool IDs
        "labels": agent_config.get("labels", []),
        "avatar": {
            "color": agent_config.get("color", "blue"),
            "symbol": agent_config.get("symbol", "sparkle")
        }
    }

    response = requests.post(
        f"{kibana_url}/api/agent_builder/agents",
        headers={
            "Authorization": f"ApiKey {api_key}",
            "kbn-xsrf": "true"
        },
        json=agent_payload
    )
    return response.json()
```

### Best Practices for Agent Instructions

```python
AGENT_INSTRUCTION_TEMPLATE = """
You are a {domain} analytics expert for {customer_name}.

Your specialization includes:
{specializations}

Available datasets:
{datasets}

Key metrics to focus on:
{metrics}

Response guidelines:
- Provide actionable insights with specific numbers
- Highlight trends and anomalies
- Suggest optimization opportunities
- Format responses with clear headers and bullet points

When using tools:
- Prefer {preferred_tools} for {use_cases}
- Always validate data quality before reporting
- Include confidence levels when appropriate
"""
```

---

## 🔄 MCP Server Integration

### Enabling External AI Clients

The MCP server endpoint allows integration with Claude Desktop, Cursor, VS Code:

```
{KIBANA_URL}/api/agent_builder/mcp
```

**Client Configuration Example (Claude Desktop)**:
```json
{
  "mcpServers": {
    "elastic-demo-builder": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "${KIBANA_URL}/api/agent_builder/mcp",
        "--header",
        "Authorization:ApiKey ${API_KEY}"
      ]
    }
  }
}
```

---

## 📊 Demo Builder Integration Architecture

### Phase 1: Tool Generation Pipeline

```python
class ElasticToolGenerator:
    def __init__(self, kibana_url, api_key):
        self.kibana_url = kibana_url
        self.api_key = api_key
        self.headers = {
            "Authorization": f"ApiKey {api_key}",
            "kbn-xsrf": "true"
        }

    def generate_tools_for_demo(self, demo_config):
        """Generate and deploy all tools for a demo"""

        tools = []

        # Create ES|QL tools for structured queries
        for query in demo_config["esql_queries"]:
            tool = self.create_esql_tool(query)
            tools.append(tool)

        # Create index search tools for exploration
        for index in demo_config["indices"]:
            tool = self.create_index_search_tool(index)
            tools.append(tool)

        # Validate all tools
        for tool in tools:
            self.validate_tool(tool["id"])

        return tools

    def validate_tool(self, tool_id):
        """Test tool execution"""

        response = requests.post(
            f"{self.kibana_url}/api/agent_builder/tools/_execute",
            headers=self.headers,
            json={
                "tool_id": tool_id,
                "parameters": {}  # Test with default params
            }
        )
        return response.json()
```

### Phase 2: Agent Deployment

```python
class AgentDeployer:
    def __init__(self, kibana_url, api_key):
        self.kibana_url = kibana_url
        self.api_key = api_key

    def deploy_demo_agent(self, demo_config, tool_ids):
        """Deploy a complete agent with all tools"""

        # Generate custom instructions based on demo
        instructions = self.generate_instructions(demo_config)

        # Create the agent
        agent = self.create_agent({
            "id": f"demo_{demo_config['customer']}_{demo_config['id']}",
            "display_name": f"{demo_config['customer']} Analytics Expert",
            "description": demo_config["description"],
            "instructions": instructions,
            "tool_ids": tool_ids,
            "labels": ["demo", demo_config["industry"]]
        })

        # Test the agent with sample queries
        self.test_agent(agent["id"], demo_config["test_queries"])

        return agent
```

### Phase 3: Validation & Testing

```python
class DemoValidator:
    def __init__(self, kibana_url, api_key):
        self.kibana_url = kibana_url
        self.api_key = api_key

    def validate_demo(self, agent_id, test_queries):
        """End-to-end demo validation"""

        results = []

        for query in test_queries:
            # Start conversation
            response = requests.post(
                f"{self.kibana_url}/api/agent_builder/converse",
                headers={
                    "Authorization": f"ApiKey {self.api_key}",
                    "kbn-xsrf": "true"
                },
                json={
                    "agent_id": agent_id,
                    "message": query["question"],
                    "conversation_id": None  # New conversation
                }
            )

            result = response.json()

            # Validate response
            validation = {
                "query": query["question"],
                "success": response.status_code == 200,
                "has_data": len(result.get("data", [])) > 0,
                "execution_time": result.get("execution_time_ms"),
                "tools_used": result.get("tools_used", [])
            }

            results.append(validation)

        return results
```

---

## 🚀 Implementation Workflow

### Complete Demo Creation Flow

```python
async def create_complete_demo(customer_info):
    """Full demo creation pipeline"""

    # Step 1: Generate demo configuration
    demo_config = await generate_demo_config(customer_info)

    # Step 2: Create and upload data
    data_uploader = DataUploader(KIBANA_URL, API_KEY)
    indices = await data_uploader.upload_demo_data(demo_config["datasets"])

    # Step 3: Generate and create tools
    tool_generator = ElasticToolGenerator(KIBANA_URL, API_KEY)
    tools = await tool_generator.generate_tools_for_demo(demo_config)

    # Step 4: Create and configure agent
    agent_deployer = AgentDeployer(KIBANA_URL, API_KEY)
    agent = await agent_deployer.deploy_demo_agent(
        demo_config,
        [tool["id"] for tool in tools]
    )

    # Step 5: Validate everything works
    validator = DemoValidator(KIBANA_URL, API_KEY)
    validation_results = await validator.validate_demo(
        agent["id"],
        demo_config["test_queries"]
    )

    # Step 6: Generate documentation
    docs = generate_demo_documentation(
        demo_config,
        agent,
        tools,
        validation_results
    )

    return {
        "agent": agent,
        "tools": tools,
        "validation": validation_results,
        "documentation": docs
    }
```

---

## 📈 Self-Improving Integration

### Using Existing Agents to Help Create New Demos

```python
class AgentAssistedDemoBuilder:
    def __init__(self, kibana_url, api_key):
        self.kibana_url = kibana_url
        self.api_key = api_key

    async def query_existing_agent(self, agent_id, question):
        """Query an existing agent for insights"""

        response = await self.converse_with_agent(
            agent_id,
            question
        )

        return response["answer"]

    async def generate_demo_with_agent_help(self, customer_info):
        """Use existing agents to help create new demo"""

        # Query industry expert agent
        industry_insights = await self.query_existing_agent(
            f"industry_expert_{customer_info['industry']}",
            f"What are the key metrics and KPIs for {customer_info['company']}?"
        )

        # Query query optimization agent
        optimized_queries = await self.query_existing_agent(
            "query_optimizer",
            f"Optimize these ES|QL queries: {draft_queries}"
        )

        # Query data relationship analyzer
        data_model = await self.query_existing_agent(
            "data_relationship_analyzer",
            f"Design data model for {customer_info['use_case']}"
        )

        # Combine insights to create demo
        demo_config = self.synthesize_demo_config(
            industry_insights,
            optimized_queries,
            data_model
        )

        return demo_config
```

---

## 🔒 Security Considerations

### API Key Management

```python
class SecureAPIManager:
    def __init__(self):
        # Store API keys securely
        self.api_key = os.environ.get("ELASTIC_API_KEY")

        # Validate permissions
        self.validate_permissions()

    def validate_permissions(self):
        """Ensure API key has required permissions"""

        required_permissions = [
            "agent_builder:tools:*",
            "agent_builder:agents:*",
            "indices:data/write/*"
        ]

        # Test permissions with minimal operation
        response = requests.get(
            f"{KIBANA_URL}/api/agent_builder/tools",
            headers={"Authorization": f"ApiKey {self.api_key}"}
        )

        if response.status_code == 403:
            raise PermissionError("API key lacks required permissions")
```

---

## 📋 Next Steps for Implementation

1. **Create API client wrapper** with all endpoints
2. **Build tool generation templates** for common patterns
3. **Implement agent instruction generator** based on industry
4. **Create validation suite** for end-to-end testing
5. **Build MCP server integration** for Claude Desktop
6. **Deploy seed demos** with working agents

---

## 🎯 Success Metrics

- **Tool Creation Success Rate**: >95% on first attempt
- **Agent Response Accuracy**: >90% relevant answers
- **Query Execution Time**: <500ms average
- **Demo Creation Time**: <15 minutes end-to-end
- **Validation Pass Rate**: 100% before deployment

---

*This integration guide combines official Elastic Agent Builder capabilities with our automated demo generation platform for maximum impact.*