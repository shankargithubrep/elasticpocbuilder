"""
Agents Tab - Manages agent configuration and deployment to Elastic Agent Builder.
"""

import streamlit as st
import logging
import os
import json

from .utils import get_module_prefix

logger = logging.getLogger(__name__)


def render_agents_tab(agent_builder):
    """Render the Agents tab content.

    Args:
        agent_builder: The AgentBuilderService instance
    """
    st.markdown("### Agent Management")

    # Load agent metadata from module if it exists
    agent_metadata_path = os.path.join(
        "demos",
        st.session_state.current_demo_module,
        "agent_metadata.json"
    )

    agent_metadata = None
    if os.path.exists(agent_metadata_path):
        try:
            with open(agent_metadata_path, 'r') as f:
                agent_metadata = json.load(f)
        except Exception as e:
            st.error(f"Error loading agent metadata: {e}")

    if not agent_metadata:
        st.warning("No agent metadata found for this demo. Agent metadata is generated automatically for new demos.")
        st.info("To add agent metadata to older demos, regenerate the demo module.")
    else:
        # Section 1: Deployed Agents
        st.markdown("#### 🤖 Deployed Agents")

        # Check connection
        if not agent_builder.validate_connection()['success']:
            st.error("❌ Cannot connect to Elastic Agent Builder. Please check your environment variables.")
        else:
            # List all agents
            all_agents_response = agent_builder.list_agents()
            if 'error' in all_agents_response:
                st.error(f"Error listing agents: {all_agents_response['error']}")
                deployed_agents = []
            else:
                all_agents = all_agents_response.get('agents', [])
                # Filter for agents matching this demo
                # Use both exact match (for the main agent) and prefix match
                agent_id = agent_metadata.get('id', 'unknown')
                module_prefix = get_module_prefix(st.session_state.current_demo_module)
                st.caption(f"Filtering agents matching: `{agent_id}` or prefix: `{module_prefix}*`")
                deployed_agents = [a for a in all_agents
                    if a.get('id', '') == agent_id or
                        a.get('id', '').startswith(module_prefix)]

                # Get all tools for tool assignment
                deployed_response = agent_builder.list_tools()
                all_tools = deployed_response.get('tools', []) if 'error' not in deployed_response else []

                if deployed_agents:
                    for agent in deployed_agents:
                        with st.expander(f"🤖 {agent.get('name', agent.get('id', 'Unknown'))}"):
                            # Get current tools assigned to this agent
                            agent_tools = agent.get('configuration', {}).get('tools', [])
                            current_tool_ids = []
                            if agent_tools and isinstance(agent_tools, list) and len(agent_tools) > 0:
                                if isinstance(agent_tools[0], dict):
                                    current_tool_ids = agent_tools[0].get('tool_ids', [])

                            # Show current tools
                            st.markdown("##### 🛠️ Currently Assigned Tools")
                            if current_tool_ids:
                                for tool_id in current_tool_ids:
                                    st.text(f"• {tool_id}")
                            else:
                                st.info("No tools currently assigned")

                            st.divider()

                            # Tool assignment section
                            st.markdown("##### ➕ Manage Tool Assignment")

                            # Get available tools
                            # 1. Module-specific tools
                            module_tools = [t for t in all_tools if t.get('id', '').startswith(module_prefix)]
                            module_tool_ids = [t['id'] for t in module_tools]

                            # 2. Platform tools
                            platform_tools = [t for t in all_tools if t.get('id', '').startswith('platform.')]
                            platform_tool_ids = [t['id'] for t in platform_tools]

                            # Combine all available tools
                            all_available_ids = []
                            if module_tool_ids:
                                all_available_ids.extend(module_tool_ids)
                            if platform_tool_ids:
                                all_available_ids.extend(platform_tool_ids)

                            if all_available_ids:
                                with st.form(f"tool_assignment_{agent['id']}"):
                                    st.markdown("**Select tools to assign:**")

                                    # Multi-select with sections
                                    selected_tools = []

                                    # Module tools section
                                    if module_tool_ids:
                                        st.caption("📦 Module-specific tools:")
                                        for tool_id in module_tool_ids:
                                            checked = st.checkbox(
                                                tool_id,
                                                value=tool_id in current_tool_ids,
                                                key=f"check_{agent['id']}_{tool_id}"
                                            )
                                            if checked:
                                                selected_tools.append(tool_id)

                                    # Platform tools section
                                    if platform_tool_ids:
                                        st.caption("🌐 Platform tools:")
                                        for tool_id in platform_tool_ids:
                                            checked = st.checkbox(
                                                tool_id,
                                                value=tool_id in current_tool_ids,
                                                key=f"check_{agent['id']}_{tool_id}"
                                            )
                                            if checked:
                                                selected_tools.append(tool_id)

                                    # Update button
                                    if st.form_submit_button("🔧 Set Active Tools for this Agent", use_container_width=True):
                                        with st.spinner("Updating agent tools..."):
                                            # Update agent with new tools
                                            update_config = {
                                                'name': agent.get('name'),
                                                'description': agent.get('description'),
                                                'labels': agent.get('labels', []),
                                                'avatar_color': agent.get('avatar_color'),
                                                'avatar_symbol': agent.get('avatar_symbol'),
                                                'instructions': agent.get('configuration', {}).get('instructions', ''),
                                                'configuration': {
                                                    'instructions': agent.get('configuration', {}).get('instructions', ''),
                                                    'tools': [{'tool_ids': selected_tools}] if selected_tools else []
                                                }
                                            }

                                            result = agent_builder.update_agent(agent['id'], update_config)
                                            if result.get('success'):
                                                st.success(f"✅ Tools updated for agent: {agent['id']}")
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Failed to update tools: {result.get('error')}")
                            else:
                                st.warning("No tools available to assign. Deploy some tools first!")

                            st.divider()

                            # Actions
                            col1, col2 = st.columns(2)
                            with col1:
                                # View details button
                                if st.button("👁️ View Raw JSON", key=f"view_agent_{agent['id']}", use_container_width=True):
                                    st.session_state[f"show_json_{agent['id']}"] = not st.session_state.get(f"show_json_{agent['id']}", False)

                            with col2:
                                # Delete button
                                if st.button("🗑️ Delete Agent", key=f"delete_agent_{agent['id']}", use_container_width=True):
                                    result = agent_builder.delete_agent(agent['id'])
                                    if result.get('success'):
                                        st.success(f"Deleted agent: {agent['id']}")
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to delete: {result.get('error')}")

                            # Show JSON if toggled
                            if st.session_state.get(f"show_json_{agent['id']}"):
                                st.markdown("##### Raw Agent JSON")
                                st.json(agent)
                else:
                    st.info("No agents deployed for this demo yet.")

        st.divider()

        # Section 2: Agent Configuration
        st.markdown("#### 🎯 Agent Configuration")
        st.caption("Configure and deploy your agent to Elastic Agent Builder")

        # Agent configuration form
        with st.form("agent_config_form"):
            # Pre-fill with metadata from module
            agent_id = st.text_input(
                "Agent ID",
                value=agent_metadata.get('id', ''),
                help="Unique identifier for the agent (lowercase, no spaces)"
            )

            agent_name = st.text_input(
                "Agent Name",
                value=agent_metadata.get('name', ''),
                help="Display name for the agent"
            )

            agent_description = st.text_area(
                "Agent Description",
                value=agent_metadata.get('description', ''),
                height=100,
                help="Brief description shown to users"
            )

            # Avatar customization
            col1, col2 = st.columns(2)
            with col1:
                avatar_symbol = st.text_input(
                    "Avatar Symbol",
                    value=agent_metadata.get('avatar_symbol', 'AI'),
                    max_chars=2,
                    help="1-2 letter symbol for the avatar"
                )

            with col2:
                avatar_color = st.color_picker(
                    "Avatar Color",
                    value=agent_metadata.get('avatar_color', '#3B82F6')
                )

            # Labels
            labels_str = st.text_input(
                "Labels (comma-separated)",
                value=", ".join(agent_metadata.get('labels', [])),
                help="Tags for categorizing the agent"
            )
            agent_labels = [l.strip() for l in labels_str.split(',') if l.strip()]

            # Instructions
            agent_instructions = st.text_area(
                "Agent Instructions",
                value=agent_metadata.get('configuration', {}).get('instructions', ''),
                height=200,
                help="System prompt/instructions for the agent"
            )

            # Form actions
            col_save, col_deploy = st.columns(2)

            with col_save:
                if st.form_submit_button("💾 Save Configuration", use_container_width=True):
                    # Update agent metadata in the file
                    updated_metadata = {
                        "id": agent_id,
                        "name": agent_name,
                        "description": agent_description,
                        "labels": agent_labels,
                        "avatar_color": avatar_color,
                        "avatar_symbol": avatar_symbol,
                        "configuration": {
                            "instructions": agent_instructions,
                            "tools": []  # Tools will be managed separately
                        }
                    }

                    try:
                        with open(agent_metadata_path, 'w') as f:
                            json.dump(updated_metadata, f, indent=2)
                        st.success("✅ Agent configuration saved locally!")
                    except Exception as e:
                        st.error(f"Failed to save configuration: {e}")

            with col_deploy:
                if st.form_submit_button("🚀 Deploy Agent", use_container_width=True, type="primary"):
                    if not all([agent_id, agent_name, agent_description, agent_instructions]):
                        st.error("Please fill in all required fields")
                    else:
                        with st.spinner("Deploying agent to Elastic Agent Builder..."):
                            # Check if agent exists
                            existing = [a for a in deployed_agents if a.get('id') == agent_id]

                            if existing:
                                # Update existing agent
                                result = agent_builder.update_agent(agent_id, {
                                    'name': agent_name,
                                    'description': agent_description,
                                    'labels': agent_labels,
                                    'avatar_color': avatar_color,
                                    'avatar_symbol': avatar_symbol,
                                    'instructions': agent_instructions
                                })
                                if result.get('success'):
                                    st.success(f"✅ Agent updated successfully: {agent_id}")
                                else:
                                    st.error(f"❌ Update failed: {result.get('error')}")
                            else:
                                # Create new agent
                                result = agent_builder.create_agent({
                                    'id': agent_id,
                                    'name': agent_name,
                                    'description': agent_description,
                                    'labels': agent_labels,
                                    'avatar_color': avatar_color,
                                    'avatar_symbol': avatar_symbol,
                                    'instructions': agent_instructions,
                                    'tool_ids': []  # Start with no tools
                                })
                                if result.get('success'):
                                    st.success(f"✅ Agent deployed successfully: {agent_id}")
                                    st.balloons()
                                else:
                                    st.error(f"❌ Deployment failed: {result.get('error')}")

                            # Refresh to show new status
                            if result.get('success'):
                                st.rerun()
