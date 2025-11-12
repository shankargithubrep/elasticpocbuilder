"""
Elastic Agent Builder API Service

This service handles all interactions with the Elastic Agent Builder API,
including tools and agents management.
"""

import json
import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime


class AgentBuilderService:
    """Service for interacting with Elastic Agent Builder API."""

    def __init__(self, kibana_url: str = None, api_key: str = None):
        """
        Initialize the Agent Builder Service.

        Args:
            kibana_url: The Kibana URL (defaults to env var ELASTICSEARCH_KIBANA_URL or KIBANA_URL)
            api_key: The API key (defaults to env var ELASTICSEARCH_API_KEY or KIBANA_API_KEY)
        """
        # Try multiple environment variable names for compatibility
        self.kibana_url = kibana_url or os.getenv('ELASTICSEARCH_KIBANA_URL') or os.getenv('KIBANA_URL', '')
        self.api_key = api_key or os.getenv('ELASTICSEARCH_API_KEY') or os.getenv('KIBANA_API_KEY', '')

        if not self.kibana_url:
            raise ValueError("ELASTICSEARCH_KIBANA_URL not provided or not in environment variables")
        if not self.api_key:
            raise ValueError("ELASTICSEARCH_API_KEY not provided or not in environment variables")

        # Remove trailing slash from kibana_url if present
        self.kibana_url = self.kibana_url.rstrip('/')

        # Set up headers
        self.headers = {
            'Authorization': f'ApiKey {self.api_key}',
            'Content-Type': 'application/json'
        }

        # Headers for state-changing operations
        self.write_headers = {
            **self.headers,
            'kbn-xsrf': 'true'
        }

    def list_tools(self) -> Dict[str, Any]:
        """
        List all tools from Agent Builder.

        Returns:
            Dict containing the list of tools and metadata
        """
        try:
            response = requests.get(
                f"{self.kibana_url}/api/agent_builder/tools",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            # Normalize the response - API returns 'results' but UI expects 'tools'
            return {
                'tools': data.get('results', [])
            }
        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'tools': []
            }

    def get_tool(self, tool_id: str) -> Dict[str, Any]:
        """
        Get details of a specific tool.

        Args:
            tool_id: The ID of the tool to retrieve

        Returns:
            Dict containing tool details
        """
        try:
            response = requests.get(
                f"{self.kibana_url}/api/agent_builder/tools/{tool_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'tool': None
            }

    def create_tool(self, tool_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new tool in Agent Builder.

        Args:
            tool_config: Configuration for the tool including:
                - id: Tool ID
                - type: Tool type (esql or index_search)
                - description: Tool description
                - configuration: Tool-specific configuration
                - tags: Optional tags

        Returns:
            Dict containing creation result
        """
        try:
            # Construct the payload based on tool type
            if tool_config.get('type') == 'esql':
                payload = {
                    'id': tool_config['id'],
                    'type': 'esql',
                    'description': tool_config['description'],
                    'tags': tool_config.get('tags', []),
                    'configuration': {
                        'query': tool_config['query'],
                        'params': tool_config.get('params', {})
                    }
                }
            elif tool_config.get('type') == 'index_search':
                payload = {
                    'id': tool_config['id'],
                    'type': 'index_search',
                    'description': tool_config['description'],
                    'tags': tool_config.get('tags', []),
                    'pattern': tool_config.get('pattern', '*')
                }
            else:
                return {
                    'error': f"Unsupported tool type: {tool_config.get('type')}",
                    'success': False
                }

            response = requests.post(
                f"{self.kibana_url}/api/agent_builder/tools",
                headers=self.write_headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return {
                'success': True,
                'tool': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'success': False
            }

    def delete_tool(self, tool_id: str) -> Dict[str, Any]:
        """
        Delete a tool from Agent Builder.

        Args:
            tool_id: The ID of the tool to delete

        Returns:
            Dict containing deletion result
        """
        try:
            response = requests.delete(
                f"{self.kibana_url}/api/agent_builder/tools/{tool_id}",
                headers=self.write_headers,
                timeout=30
            )
            response.raise_for_status()
            return {
                'success': True,
                'message': f'Tool {tool_id} deleted successfully'
            }
        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'success': False
            }

    def execute_tool(self, tool_id: str, tool_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool to test it.

        Args:
            tool_id: The ID of the tool to execute
            tool_params: Parameters to pass to the tool

        Returns:
            Dict containing execution result
        """
        try:
            payload = {
                'tool_id': tool_id,
                'tool_params': tool_params
            }

            response = requests.post(
                f"{self.kibana_url}/api/agent_builder/tools/_execute",
                headers=self.write_headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'success': False
            }

    def list_agents(self) -> Dict[str, Any]:
        """
        List all agents from Agent Builder.

        Returns:
            Dict containing the list of agents
        """
        try:
            response = requests.get(
                f"{self.kibana_url}/api/agent_builder/agents",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            # Normalize the response - API returns 'results' but UI expects 'agents'
            return {
                'agents': data.get('results', [])
            }
        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'agents': []
            }

    def create_agent(self, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new agent in Agent Builder.

        Args:
            agent_config: Configuration for the agent including:
                - id: Agent ID
                - name: Agent name
                - description: Agent description
                - instructions: Agent instructions
                - tool_ids: List of tool IDs to include
                - labels: Optional labels
                - avatar_color: Optional avatar color
                - avatar_symbol: Optional avatar symbol

        Returns:
            Dict containing creation result
        """
        try:
            payload = {
                'id': agent_config['id'],
                'name': agent_config['name'],
                'description': agent_config['description'],
                'labels': agent_config.get('labels', []),
                'avatar_color': agent_config.get('avatar_color', '#007AFF'),
                'avatar_symbol': agent_config.get('avatar_symbol', agent_config['name'][:2].upper()),
                'configuration': {
                    'instructions': agent_config['instructions'],
                    'tools': [
                        {
                            'tool_ids': agent_config.get('tool_ids', [])
                        }
                    ]
                }
            }

            response = requests.post(
                f"{self.kibana_url}/api/agent_builder/agents",
                headers=self.write_headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return {
                'success': True,
                'agent': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'success': False
            }

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Get a specific agent by ID from Agent Builder.

        Args:
            agent_id: The ID of the agent to retrieve

        Returns:
            Dict containing the agent details
        """
        try:
            response = requests.get(
                f"{self.kibana_url}/api/agent_builder/agents/{agent_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'agent': None
            }

    def update_agent(self, agent_id: str, agent_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing agent in Agent Builder.

        Args:
            agent_id: The ID of the agent to update
            agent_config: Configuration updates for the agent

        Returns:
            Dict containing update result
        """
        try:
            payload = {
                'name': agent_config['name'],
                'description': agent_config['description'],
                'labels': agent_config.get('labels', []),
                'avatar_color': agent_config.get('avatar_color', '#007AFF'),
                'avatar_symbol': agent_config.get('avatar_symbol', agent_config['name'][:2].upper()),
                'configuration': {
                    'instructions': agent_config['instructions'],
                    'tools': agent_config.get('configuration', {}).get('tools', [])
                }
            }

            response = requests.put(
                f"{self.kibana_url}/api/agent_builder/agents/{agent_id}",
                headers=self.write_headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return {
                'success': True,
                'agent': response.json()
            }
        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'success': False
            }

    def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Delete an agent from Agent Builder.

        Args:
            agent_id: The ID of the agent to delete

        Returns:
            Dict containing deletion result
        """
        try:
            response = requests.delete(
                f"{self.kibana_url}/api/agent_builder/agents/{agent_id}",
                headers=self.write_headers,
                timeout=30
            )
            response.raise_for_status()
            return {
                'success': True,
                'message': f'Agent {agent_id} deleted successfully'
            }
        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'success': False
            }

    def _extract_field_from_parameter(self, query: str, param: str) -> str:
        """
        Extract the field name that a parameter is filtering.

        Args:
            query: ES|QL query string
            param: Parameter name

        Returns:
            Field name being filtered, or empty string if not found
        """
        import re

        # Pattern: field_name OPERATOR ?param
        # Handles: WHERE field >= ?param, WHERE field == ?param, etc.
        pattern = rf'(\w+)\s*[><=!]+\s*\?{param}\b'
        match = re.search(pattern, query, re.IGNORECASE)

        return match.group(1) if match else ""

    def _is_timestamp_parameter(self, query: str, param: str) -> bool:
        """
        Detect if parameter filters @timestamp or event time field.
        These should NOT be created as parameters (agents handle via execute_esql).

        Args:
            query: ES|QL query string
            param: Parameter name

        Returns:
            True if this is an @timestamp or event timestamp parameter
        """
        import re

        # Check if parameter is used with @timestamp
        pattern = rf'@timestamp\s*[><=!]+\s*\?{param}\b'
        if re.search(pattern, query, re.IGNORECASE):
            return True

        # Check parameter name patterns that suggest event timestamps
        timestamp_patterns = ['timestamp', 'created_at', 'updated_at', 'event_time', 'indexed_at']
        field_name = self._extract_field_from_parameter(query, param)

        return any(p in field_name.lower() for p in timestamp_patterns)

    def _is_business_date_parameter(
        self,
        query: str,
        param: str,
        data_profile: Optional[Dict] = None
    ) -> bool:
        """
        Detect if parameter filters a business date field.
        These SHOULD be created as parameters.

        Args:
            query: ES|QL query string
            param: Parameter name
            data_profile: Optional data profile to validate field types

        Returns:
            True if this is a business date field parameter
        """
        # Extract the field name being filtered
        field_name = self._extract_field_from_parameter(query, param)

        if not field_name:
            return False

        # Rule 1: Not @timestamp
        if field_name == '@timestamp':
            return False

        # Rule 2: Check if field exists in data profile as datetime
        if data_profile:
            for dataset in data_profile.get('datasets', {}).values():
                fields = dataset.get('fields', {})
                if field_name in fields:
                    field_type = fields[field_name].get('type', '')
                    # Check for datetime type indicators
                    if 'datetime' in field_type.lower():
                        return True

        # Rule 3: Name matches business date pattern
        business_patterns = [
            'deployment', 'deploy', 'hire', 'hired', 'expiration', 'expires',
            'launch', 'launched', 'renewal', 'renew', 'completion', 'completed',
            'due', 'purchase', 'purchased', 'start', 'end', 'begin', 'finish',
            'activation', 'deactivation', 'termination', 'effective'
        ]

        # Check both parameter name and field name
        param_lower = param.lower()
        field_lower = field_name.lower()

        for pattern in business_patterns:
            if pattern in param_lower or pattern in field_lower:
                # Additional check: not an event timestamp
                if not self._is_timestamp_parameter(query, param):
                    return True

        return False

    def extract_esql_parameters(
        self,
        query: str,
        data_profile: Optional[Dict] = None
    ) -> Dict[str, Dict[str, str]]:
        """
        Extract parameters from an ES|QL query with sophisticated detection
        to distinguish business date fields from @timestamp filtering.

        Business date fields (deployment_date, hire_date, etc.) get parameters.
        @timestamp filtering does NOT get parameters (agents handle via execute_esql).

        Args:
            query: The ES|QL query string
            data_profile: Optional data profile to validate field types

        Returns:
            Dict of parameters with their types
        """
        import re

        # Find all parameters in the query
        param_pattern = r'\?(\w+)'
        params = re.findall(param_pattern, query)

        # Create parameter definitions with inferred types
        param_definitions = {}
        for param in params:
            # CRITICAL: Skip @timestamp parameters (agents handle via execute_esql)
            if self._is_timestamp_parameter(query, param):
                # Don't create parameter - agents will handle temporal filtering
                continue

            param_lower = param.lower()

            # Check if this is a business date parameter
            is_business_date = self._is_business_date_parameter(query, param, data_profile)

            # Infer type based on parameter name
            if is_business_date or 'date' in param_lower or 'time' in param_lower:
                param_type = 'date'
                if is_business_date:
                    field_name = self._extract_field_from_parameter(query, param)
                    description = f"Business date filter for {field_name}"
                else:
                    description = f"Date/time parameter for {param}"
            elif 'count' in param_lower or 'limit' in param_lower or 'size' in param_lower:
                param_type = 'integer'
                description = f"Number parameter for {param}"
            elif 'id' in param_lower:
                param_type = 'keyword'
                description = f"ID parameter for {param}"
            elif 'price' in param_lower or 'amount' in param_lower or 'value' in param_lower:
                param_type = 'double'
                description = f"Numeric value for {param}"
            else:
                param_type = 'text'
                description = f"Text parameter for {param}"

            param_definitions[param] = {
                'type': param_type,
                'description': description,
                'optional': False  # All extracted params default to required
            }

        return param_definitions

    def validate_connection(self) -> Dict[str, Any]:
        """
        Validate the connection to Kibana and Agent Builder API.

        Returns:
            Dict containing validation result
        """
        try:
            # Try to list tools as a connection test
            response = requests.get(
                f"{self.kibana_url}/api/agent_builder/tools",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return {
                'success': True,
                'message': 'Successfully connected to Agent Builder API'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e)
            }