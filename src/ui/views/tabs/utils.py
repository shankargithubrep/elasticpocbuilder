"""
Utility functions shared across tab modules.
"""

import json
import os
import logging
import streamlit as st
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def get_module_prefix(module_name: str) -> str:
    """Extract company_department prefix from module name or metadata.

    For example: 'jp_morgan_chase_(jpmc)_cto group - infrastructure...' -> 'jpmc_cto'
    """
    try:
        # Try to load agent metadata to get the proper prefix
        agent_metadata_path = os.path.join("demos", module_name, "agent_metadata.json")
        if os.path.exists(agent_metadata_path):
            with open(agent_metadata_path, 'r') as f:
                metadata = json.load(f)
                agent_id = metadata.get('id', '')
                # Agent ID format: company_department_agent
                # We want: company_department
                if agent_id and agent_id.endswith('_agent'):
                    return agent_id[:-6]  # Remove '_agent' suffix

        # Fallback: Try to load tool metadata to get prefix pattern
        tool_metadata_path = os.path.join("demos", module_name, "tool_metadata.json")
        if os.path.exists(tool_metadata_path):
            with open(tool_metadata_path, 'r') as f:
                metadata = json.load(f)
                # Look at any tool ID to extract the prefix
                for key, value in metadata.items():
                    if isinstance(value, dict) and 'tool_id' in value:
                        tool_id = value['tool_id']
                        # Tool ID format: company_department_purpose
                        # We want: company_department
                        parts = tool_id.split('_')
                        if len(parts) >= 3:
                            return '_'.join(parts[:2])

        # Fallback: Try to extract from module name itself
        # This is less reliable but better than nothing
        parts = module_name.lower().replace(' ', '_').replace('-', '_').split('_')
        if len(parts) >= 2:
            # Take first two meaningful parts
            return f"{parts[0]}_{parts[1]}"

        return module_name.lower()[:30]  # Last resort fallback
    except Exception as e:
        logger.warning(f"Error extracting module prefix: {e}")
        return module_name.lower()[:30]


def load_demo_queries(module_name: str) -> Dict[str, Any]:
    """Load queries from a demo module.

    Args:
        module_name: Name of the demo module

    Returns:
        Dictionary with query types as keys
    """
    from src.framework import DemoModuleManager

    manager = DemoModuleManager()
    loader = manager.get_module(module_name)

    if not loader:
        return {}

    try:
        if 'queries' not in st.session_state:
            loader.load_assets()

        queries_dict = st.session_state.get('queries', {})

        # Extract scripted, parameterized, and RAG queries
        if isinstance(queries_dict, dict):
            return {
                'scripted': queries_dict.get('scripted', []),
                'parameterized': queries_dict.get('parameterized', []),
                'rag': queries_dict.get('rag', [])
            }
        elif isinstance(queries_dict, list):
            # Legacy format - categorize queries
            scripted = []
            parameterized = []
            rag = []

            for query in queries_dict:
                if query.get('parameters'):
                    if any('rag' in str(p).lower() for p in query.get('parameters', [])):
                        rag.append(query)
                    else:
                        parameterized.append(query)
                else:
                    scripted.append(query)

            return {
                'scripted': scripted,
                'parameterized': parameterized,
                'rag': rag
            }
        else:
            return {}
    except Exception as e:
        logger.error(f"Error loading queries: {e}")
        return {}