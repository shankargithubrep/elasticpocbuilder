"""
Elastic Agent Builder API Client
Implements official Kibana APIs for managing agents, tools, and conversations
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class ToolType(Enum):
    """Tool types supported by Agent Builder"""
    ESQL = "esql"
    INDEX_SEARCH = "index_search"
    BUILTIN = "builtin"


class ParameterType(Enum):
    """Parameter types for tool configuration"""
    STRING = "string"
    KEYWORD = "keyword"
    LONG = "long"
    INTEGER = "integer"
    DOUBLE = "double"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    OBJECT = "object"
    NESTED = "nested"


@dataclass
class ToolParameter:
    """Tool parameter definition"""
    name: str
    type: ParameterType
    description: str
    required: bool = False
    default_value: Optional[Any] = None


@dataclass
class ESQLTool:
    """ES|QL tool configuration"""
    id: str
    name: str
    description: str
    query: str
    parameters: List[ToolParameter]
    labels: Optional[List[str]] = None


@dataclass
class IndexSearchTool:
    """Index search tool configuration"""
    id: str
    name: str
    description: str
    pattern: str  # e.g., "logs-*", "brand-assets"
    labels: Optional[List[str]] = None


@dataclass
class Agent:
    """Agent configuration"""
    id: str
    display_name: str
    description: str
    instructions: str
    tool_ids: List[str]
    labels: Optional[List[str]] = None
    avatar_color: str = "blue"
    avatar_symbol: str = "sparkle"


class ElasticAgentBuilderClient:
    """Client for interacting with Elastic Agent Builder APIs"""

    def __init__(self, kibana_url: str, api_key: str):
        """
        Initialize the client

        Args:
            kibana_url: Base URL for Kibana instance
            api_key: API key for authentication
        """
        self.kibana_url = kibana_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"ApiKey {api_key}",
            "Content-Type": "application/json",
            "kbn-xsrf": "true"  # Required for state-changing operations
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    # ==================== Tool Management ====================

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def create_esql_tool(self, tool: ESQLTool) -> Dict:
        """
        Create an ES|QL tool

        Args:
            tool: ES|QL tool configuration

        Returns:
            Created tool response
        """
        payload = {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "type": "esql",
            "esql": {
                "query": tool.query,
                "parameters": [
                    {
                        "name": param.name,
                        "type": param.type.value,
                        "description": param.description,
                        "required": param.required,
                        "default": param.default_value
                    }
                    for param in tool.parameters
                ]
            }
        }

        if tool.labels:
            payload["labels"] = tool.labels

        response = self.session.post(
            f"{self.kibana_url}/api/agent_builder/tools",
            json=payload
        )

        response.raise_for_status()
        logger.info(f"Created ES|QL tool: {tool.id}")
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def create_index_search_tool(self, tool: IndexSearchTool) -> Dict:
        """
        Create an index search tool

        Args:
            tool: Index search tool configuration

        Returns:
            Created tool response
        """
        payload = {
            "id": tool.id,
            "name": tool.name,
            "description": tool.description,
            "type": "index_search",
            "pattern": tool.pattern
        }

        if tool.labels:
            payload["labels"] = tool.labels

        response = self.session.post(
            f"{self.kibana_url}/api/agent_builder/tools",
            json=payload
        )

        response.raise_for_status()
        logger.info(f"Created index search tool: {tool.id}")
        return response.json()

    def list_tools(self, include_builtin: bool = False) -> List[Dict]:
        """
        List all available tools

        Args:
            include_builtin: Whether to include built-in tools

        Returns:
            List of tools
        """
        response = self.session.get(f"{self.kibana_url}/api/agent_builder/tools")
        response.raise_for_status()

        tools = response.json()

        if not include_builtin:
            tools = [t for t in tools if t.get("type") != "builtin"]

        return tools

    def get_tool(self, tool_id: str) -> Dict:
        """
        Get a specific tool by ID

        Args:
            tool_id: Tool identifier

        Returns:
            Tool configuration
        """
        response = self.session.get(f"{self.kibana_url}/api/agent_builder/tools/{tool_id}")
        response.raise_for_status()
        return response.json()

    def update_tool(self, tool_id: str, updates: Dict) -> Dict:
        """
        Update an existing tool

        Args:
            tool_id: Tool identifier
            updates: Updated configuration

        Returns:
            Updated tool response
        """
        response = self.session.put(
            f"{self.kibana_url}/api/agent_builder/tools/{tool_id}",
            json=updates
        )
        response.raise_for_status()
        logger.info(f"Updated tool: {tool_id}")
        return response.json()

    def delete_tool(self, tool_id: str) -> bool:
        """
        Delete a tool

        Args:
            tool_id: Tool identifier

        Returns:
            True if successful
        """
        response = self.session.delete(f"{self.kibana_url}/api/agent_builder/tools/{tool_id}")
        response.raise_for_status()
        logger.info(f"Deleted tool: {tool_id}")
        return True

    def execute_tool(self, tool_id: str, parameters: Optional[Dict] = None) -> Dict:
        """
        Execute a tool for testing

        Args:
            tool_id: Tool identifier
            parameters: Tool parameters

        Returns:
            Execution results
        """
        payload = {
            "tool_id": tool_id,
            "parameters": parameters or {}
        }

        response = self.session.post(
            f"{self.kibana_url}/api/agent_builder/tools/_execute",
            json=payload
        )

        response.raise_for_status()
        return response.json()

    # ==================== Agent Management ====================

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def create_agent(self, agent: Agent) -> Dict:
        """
        Create a new agent

        Args:
            agent: Agent configuration

        Returns:
            Created agent response
        """
        payload = {
            "id": agent.id,
            "display_name": agent.display_name,
            "description": agent.description,
            "instructions": agent.instructions,
            "tools": agent.tool_ids,
            "avatar": {
                "color": agent.avatar_color,
                "symbol": agent.avatar_symbol
            }
        }

        if agent.labels:
            payload["labels"] = agent.labels

        response = self.session.post(
            f"{self.kibana_url}/api/agent_builder/agents",
            json=payload
        )

        response.raise_for_status()
        logger.info(f"Created agent: {agent.id}")
        return response.json()

    def list_agents(self) -> List[Dict]:
        """
        List all available agents

        Returns:
            List of agents
        """
        response = self.session.get(f"{self.kibana_url}/api/agent_builder/agents")
        response.raise_for_status()
        return response.json()

    def get_agent(self, agent_id: str) -> Dict:
        """
        Get a specific agent by ID

        Args:
            agent_id: Agent identifier

        Returns:
            Agent configuration
        """
        response = self.session.get(f"{self.kibana_url}/api/agent_builder/agents/{agent_id}")
        response.raise_for_status()
        return response.json()

    def update_agent(self, agent_id: str, updates: Dict) -> Dict:
        """
        Update an existing agent

        Args:
            agent_id: Agent identifier
            updates: Updated configuration

        Returns:
            Updated agent response
        """
        response = self.session.put(
            f"{self.kibana_url}/api/agent_builder/agents/{agent_id}",
            json=updates
        )
        response.raise_for_status()
        logger.info(f"Updated agent: {agent_id}")
        return response.json()

    def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent

        Args:
            agent_id: Agent identifier

        Returns:
            True if successful
        """
        response = self.session.delete(f"{self.kibana_url}/api/agent_builder/agents/{agent_id}")
        response.raise_for_status()
        logger.info(f"Deleted agent: {agent_id}")
        return True

    # ==================== Conversations ====================

    def converse(self, agent_id: str, message: str, conversation_id: Optional[str] = None) -> Dict:
        """
        Send a message to an agent

        Args:
            agent_id: Agent to converse with
            message: User message
            conversation_id: Optional existing conversation ID

        Returns:
            Agent response
        """
        payload = {
            "agent_id": agent_id,
            "message": message
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        response = self.session.post(
            f"{self.kibana_url}/api/agent_builder/converse",
            json=payload
        )

        response.raise_for_status()
        return response.json()

    def converse_async(self, agent_id: str, message: str, conversation_id: Optional[str] = None):
        """
        Send a message to an agent with streaming response

        Args:
            agent_id: Agent to converse with
            message: User message
            conversation_id: Optional existing conversation ID

        Yields:
            Streamed response chunks
        """
        payload = {
            "agent_id": agent_id,
            "message": message
        }

        if conversation_id:
            payload["conversation_id"] = conversation_id

        response = self.session.post(
            f"{self.kibana_url}/api/agent_builder/converse/async",
            json=payload,
            stream=True
        )

        response.raise_for_status()

        for line in response.iter_lines():
            if line:
                yield json.loads(line)

    def list_conversations(self) -> List[Dict]:
        """
        List all conversations

        Returns:
            List of conversations
        """
        response = self.session.get(f"{self.kibana_url}/api/agent_builder/conversations")
        response.raise_for_status()
        return response.json()

    def get_conversation(self, conversation_id: str) -> Dict:
        """
        Get a specific conversation

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation details
        """
        response = self.session.get(
            f"{self.kibana_url}/api/agent_builder/conversations/{conversation_id}"
        )
        response.raise_for_status()
        return response.json()

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation

        Args:
            conversation_id: Conversation identifier

        Returns:
            True if successful
        """
        response = self.session.delete(
            f"{self.kibana_url}/api/agent_builder/conversations/{conversation_id}"
        )
        response.raise_for_status()
        logger.info(f"Deleted conversation: {conversation_id}")
        return True

    # ==================== MCP Server ====================

    def get_mcp_server_url(self) -> str:
        """
        Get the MCP server URL for external client configuration

        Returns:
            MCP server URL
        """
        return f"{self.kibana_url}/api/agent_builder/mcp"

    def generate_mcp_config(self, name: str = "elastic-agent-builder") -> Dict:
        """
        Generate MCP client configuration

        Args:
            name: Server name for client config

        Returns:
            MCP client configuration
        """
        return {
            "mcpServers": {
                name: {
                    "command": "npx",
                    "args": [
                        "mcp-remote",
                        self.get_mcp_server_url(),
                        "--header",
                        f"Authorization:ApiKey {self.api_key}"
                    ]
                }
            }
        }

    # ==================== Validation & Testing ====================

    def validate_agent_with_queries(self, agent_id: str, test_queries: List[str]) -> List[Dict]:
        """
        Validate an agent with test queries

        Args:
            agent_id: Agent to test
            test_queries: List of test questions

        Returns:
            Validation results
        """
        results = []

        for query in test_queries:
            try:
                response = self.converse(agent_id, query)

                validation = {
                    "query": query,
                    "success": True,
                    "response_length": len(response.get("response", "")),
                    "tools_used": response.get("tools_used", []),
                    "execution_time_ms": response.get("execution_time_ms")
                }

            except Exception as e:
                validation = {
                    "query": query,
                    "success": False,
                    "error": str(e)
                }

            results.append(validation)

        return results

    def health_check(self) -> bool:
        """
        Check if the API is accessible

        Returns:
            True if API is healthy
        """
        try:
            response = self.session.get(f"{self.kibana_url}/api/agent_builder/agents")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False