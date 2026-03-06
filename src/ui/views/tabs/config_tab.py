"""
Config Tab - Displays demo configuration and allows asset regeneration.
"""

import streamlit as st
import logging
import os
import json
import anthropic
from pathlib import Path
from typing import List, Dict, Any

from src.ui.data_loaders import (
    load_demo_datasets,
    load_demo_queries,
    load_demo_guide
)
from src.ui.components.progress_tracker import get_progress_service

logger = logging.getLogger(__name__)


def _get_deployed_resources(module_name: str, loader) -> Dict[str, Any]:
    """Get list of deployed resources for this module."""
    resources = {
        "datasets": [],  # List of index names
        "tools": [],     # List of tool IDs
        "agents": []     # List of agent IDs
    }

    module_path = Path("demos") / module_name

    # Get datasets from data_profile.json
    data_profile_path = module_path / "data_profile.json"
    if data_profile_path.exists():
        try:
            with open(data_profile_path, 'r') as f:
                data = json.load(f)
                resources["datasets"] = list(data.get('datasets', {}).keys())
        except Exception as e:
            logger.warning(f"Could not load datasets: {e}")

    # Get tools from tool_metadata.json
    tool_metadata_path = module_path / "tool_metadata.json"
    if tool_metadata_path.exists():
        try:
            with open(tool_metadata_path, 'r') as f:
                data = json.load(f)
                for tool_id, meta in data.items():
                    if isinstance(meta, dict) and meta.get('deployed', False):
                        resources["tools"].append({
                            "id": tool_id,
                            "deployed_tool_id": meta.get('deployed_tool_id', tool_id),
                            "name": meta.get('name', tool_id)
                        })
        except Exception as e:
            logger.warning(f"Could not load tools: {e}")

    # Get agent from agent_metadata.json
    agent_metadata_path = module_path / "agent_metadata.json"
    if agent_metadata_path.exists():
        try:
            with open(agent_metadata_path, 'r') as f:
                data = json.load(f)
                if data.get('deployed', False) or data.get('deployed_at'):
                    resources["agents"].append({
                        "id": data.get('id', 'unknown'),
                        "name": data.get('name', 'Unknown Agent')
                    })
                elif data.get('id'):
                    # Agent exists but might have been deployed without tracking
                    resources["agents"].append({
                        "id": data.get('id', 'unknown'),
                        "name": data.get('name', 'Unknown Agent'),
                        "unknown_status": True  # Flag to indicate we're not sure if deployed
                    })
        except Exception as e:
            logger.warning(f"Could not load agent: {e}")

    return resources


def _render_deployed_resources_section(module_name: str, loader):
    """Render the deployed resources management section."""
    with st.expander("🗑️ Manage Deployed Resources", expanded=False):
        st.caption("Remove resources deployed to Elasticsearch and Agent Builder")

        resources = _get_deployed_resources(module_name, loader)

        # Initialize selection state
        if "delete_selections" not in st.session_state:
            st.session_state.delete_selections = {
                "datasets": True,
                "tools": True,
                "agents": True
            }

        # Select all / deselect all
        col_all, col_none, col_spacer = st.columns([1, 1, 3])
        with col_all:
            if st.button("Select All", key="select_all_resources"):
                st.session_state.delete_selections = {"datasets": True, "tools": True, "agents": True}
                st.rerun()
        with col_none:
            if st.button("Select None", key="select_none_resources"):
                st.session_state.delete_selections = {"datasets": False, "tools": False, "agents": False}
                st.rerun()

        st.divider()

        # Resource checkboxes
        datasets_count = len(resources["datasets"])
        tools_count = len(resources["tools"])
        agents_count = len(resources["agents"])

        col1, col2, col3 = st.columns(3)

        with col1:
            datasets_selected = st.checkbox(
                f"📊 Datasets ({datasets_count})",
                value=st.session_state.delete_selections.get("datasets", True),
                key="delete_datasets_check",
                help=f"Delete indices: {', '.join(resources['datasets'][:3])}{'...' if datasets_count > 3 else ''}" if datasets_count > 0 else "No datasets found"
            )
            st.session_state.delete_selections["datasets"] = datasets_selected

        with col2:
            tools_selected = st.checkbox(
                f"🔧 Tools ({tools_count})",
                value=st.session_state.delete_selections.get("tools", True),
                key="delete_tools_check",
                help=f"Delete tools from Agent Builder" if tools_count > 0 else "No tools deployed"
            )
            st.session_state.delete_selections["tools"] = tools_selected

        with col3:
            agents_selected = st.checkbox(
                f"🤖 Agents ({agents_count})",
                value=st.session_state.delete_selections.get("agents", True),
                key="delete_agents_check",
                help=f"Delete agent from Agent Builder" if agents_count > 0 else "No agent deployed"
            )
            st.session_state.delete_selections["agents"] = agents_selected

        st.divider()

        # Delete button with confirmation
        any_selected = datasets_selected or tools_selected or agents_selected
        total_to_delete = (
            (datasets_count if datasets_selected else 0) +
            (tools_count if tools_selected else 0) +
            (agents_count if agents_selected else 0)
        )

        if any_selected:
            st.warning(f"⚠️ This will permanently delete {total_to_delete} resource(s) from Elasticsearch/Agent Builder.")

            if st.button("🗑️ Delete Selected Resources", type="primary", key="delete_resources_btn"):
                _execute_resource_deletion(module_name, resources, st.session_state.delete_selections)
        else:
            st.info("Select at least one resource type to delete.")


def _execute_resource_deletion(module_name: str, resources: Dict[str, Any], selections: Dict[str, bool]):
    """Execute the deletion of selected resources."""
    results = {"success": [], "failed": []}

    # Delete datasets (ES indices)
    if selections.get("datasets", False) and resources["datasets"]:
        with st.spinner("Deleting indices from Elasticsearch..."):
            try:
                from src.services.elasticsearch_indexer import ElasticsearchIndexer
                indexer = ElasticsearchIndexer()

                for index_name in resources["datasets"]:
                    try:
                        success, msg = indexer.delete_index(index_name)
                        if success:
                            results["success"].append(f"Index: {index_name}")
                        else:
                            results["failed"].append(f"Index {index_name}: {msg}")
                    except Exception as e:
                        results["failed"].append(f"Index {index_name}: {str(e)}")

            except Exception as e:
                results["failed"].append(f"ES connection: {str(e)}")

    # Delete tools from Agent Builder
    if selections.get("tools", False) and resources["tools"]:
        with st.spinner("Deleting tools from Agent Builder..."):
            try:
                from src.services.agent_builder_service import AgentBuilderService
                client = AgentBuilderService()

                for tool in resources["tools"]:
                    tool_id = tool.get("deployed_tool_id") or tool.get("id")
                    try:
                        result = client.delete_tool(tool_id)
                        if result.get('success'):
                            results["success"].append(f"Tool: {tool.get('name', tool_id)}")
                        else:
                            results["failed"].append(f"Tool {tool_id}: {result.get('error', 'Delete returned false')}")
                    except Exception as e:
                        if "404" in str(e) or "not found" in str(e).lower():
                            results["success"].append(f"Tool: {tool_id} (already removed)")
                        else:
                            results["failed"].append(f"Tool {tool_id}: {str(e)}")

                # Update tool_metadata.json to mark as not deployed
                _update_tool_metadata_after_delete(module_name)

            except Exception as e:
                results["failed"].append(f"Agent Builder connection: {str(e)}")

    # Delete agents from Agent Builder
    if selections.get("agents", False) and resources["agents"]:
        with st.spinner("Deleting agents from Agent Builder..."):
            try:
                from src.services.agent_builder_service import AgentBuilderService
                client = AgentBuilderService()

                for agent in resources["agents"]:
                    agent_id = agent.get("id")
                    try:
                        result = client.delete_agent(agent_id)
                        if result.get('success'):
                            results["success"].append(f"Agent: {agent.get('name', agent_id)}")
                        else:
                            results["failed"].append(f"Agent {agent_id}: {result.get('error', 'Delete returned false')}")
                    except Exception as e:
                        if "404" in str(e) or "not found" in str(e).lower():
                            results["success"].append(f"Agent: {agent_id} (already removed)")
                        else:
                            results["failed"].append(f"Agent {agent_id}: {str(e)}")

                # Update agent_metadata.json to mark as not deployed
                _update_agent_metadata_after_delete(module_name)

            except Exception as e:
                results["failed"].append(f"Agent Builder connection: {str(e)}")

    # Update progress tracking
    try:
        progress_service = get_progress_service(module_name)
        if selections.get("datasets", False):
            progress_service.mark_data_not_indexed()
        if selections.get("agents", False):
            progress_service.mark_agent_not_deployed()
    except Exception as e:
        logger.warning(f"Could not update progress: {e}")

    # Show results
    if results["success"]:
        st.success(f"✅ Successfully deleted: {', '.join(results['success'])}")
    if results["failed"]:
        st.error(f"❌ Failed to delete: {', '.join(results['failed'])}")

    if results["success"]:
        st.rerun()


def _update_tool_metadata_after_delete(module_name: str):
    """Update tool_metadata.json to mark tools as not deployed."""
    tool_metadata_path = Path("demos") / module_name / "tool_metadata.json"
    if tool_metadata_path.exists():
        try:
            with open(tool_metadata_path, 'r') as f:
                data = json.load(f)

            for tool_id in data:
                if isinstance(data[tool_id], dict):
                    data[tool_id]['deployed'] = False
                    data[tool_id]['deployed_at'] = None
                    data[tool_id]['deployed_tool_id'] = None

            with open(tool_metadata_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.warning(f"Could not update tool metadata: {e}")


def _update_agent_metadata_after_delete(module_name: str):
    """Update agent_metadata.json to mark agent as not deployed."""
    agent_metadata_path = Path("demos") / module_name / "agent_metadata.json"
    if agent_metadata_path.exists():
        try:
            with open(agent_metadata_path, 'r') as f:
                data = json.load(f)

            data['deployed'] = False
            data['deployed_at'] = None

            with open(agent_metadata_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.warning(f"Could not update agent metadata: {e}")


def render_config_tab(loader, assets_key: str):
    """Render the Config tab content.

    Args:
        loader: The demo module loader instance
        assets_key: Session state key for tracking assets
    """
    # Use the new ModuleVisualizer for enhanced Config display
    try:
        from src.ui.module_visualizer import ModuleVisualizer

        # Get LLM client if available
        from src.services.llm_proxy_service import UnifiedLLMClient
        
        llm_client = UnifiedLLMClient()
        if not llm_client._proxy_client.is_available():
            llm_client = None

        # Create and render visualizer
        visualizer = ModuleVisualizer(loader.module_path, llm_client)
        visualizer.render_module_overview()

    except ImportError:
        # Fallback to simple JSON display if visualizer not available
        st.markdown("### Demo Configuration")
        st.json(loader.config)
    except Exception as e:
        logger.warning(f"Could not render module visualization: {e}")
        # Fallback to simple JSON display
        st.markdown("### Demo Configuration")
        st.json(loader.config)

    st.divider()
    st.markdown("### Regenerate Assets")
    st.caption("Force regeneration of datasets, queries, and guide")

    if st.button("🔄 Regenerate Assets", use_container_width=True):
        with st.spinner("Regenerating demo assets..."):
            try:
                # Force regeneration by clearing cache and loading
                load_demo_datasets.clear()
                load_demo_queries.clear()
                load_demo_guide.clear()

                # Generate all assets
                datasets = load_demo_datasets(st.session_state.current_demo_module)
                queries = load_demo_queries(st.session_state.current_demo_module)
                guide = load_demo_guide(st.session_state.current_demo_module)

                # Mark assets as regenerated
                st.session_state[assets_key] = True
                st.session_state.assets_generated = True

                st.success(f"✅ Regenerated {len(datasets)} datasets, {len(queries)} queries, and demo guide!")
                st.rerun()
            except Exception as e:
                st.error(f"Error regenerating assets: {e}")
                import traceback
                st.code(traceback.format_exc())

    # Original Conversation Section
    st.divider()
    st.markdown("### Original Conversation")
    st.caption("The conversation that led to the creation of this demo")

    import json
    conversation_file = loader.module_path / 'conversation.json'
    if conversation_file.exists():
        try:
            with open(conversation_file, 'r') as f:
                conversation_data = json.load(f)

            messages = conversation_data.get('messages', [])

            if messages:
                st.markdown(f"**Generated:** {conversation_data.get('timestamp', 'Unknown')}")
                st.divider()

                # Display messages in chat format
                for msg in messages:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')

                    if role == 'user':
                        with st.chat_message("user"):
                            st.markdown(content)
                    elif role == 'assistant':
                        with st.chat_message("assistant"):
                            st.markdown(content)
            else:
                st.info("No conversation messages found.")
        except Exception as e:
            st.error(f"Error loading conversation: {e}")
            st.code(str(e))
    else:
        st.info("💬 No conversation history found for this demo. This feature was added in a recent update.")