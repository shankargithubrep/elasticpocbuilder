"""
Browse Demos view - view and manage generated demo modules
"""

import streamlit as st
import logging

from src.framework import DemoModuleManager
from ..data_loaders import (
    load_demo_datasets,
    load_demo_queries,
    load_demo_guide
)
from .tabs import (
    render_config_tab,
    render_data_tab,
    render_queries_tab,
    render_guide_tab,
    render_tools_tab,
    render_agents_tab
)
from ..components.progress_tracker import render_progress_header

logger = logging.getLogger(__name__)


def render_browse_demos_view():
    """Render the demo browsing interface - demo details only (list is in sidebar)"""
    # Show details if a module is selected
    if st.session_state.current_demo_module:
        st.markdown(f"#### 📊 {st.session_state.current_demo_module}")

        # Progress tracking header
        render_progress_header(st.session_state.current_demo_module)

        manager = DemoModuleManager()
        loader = manager.get_module(st.session_state.current_demo_module)

        if loader:
            # Create tabs FIRST to prevent resets
            # New order: Config, Data, Queries, Tools, Agents, Guide
            tabs = st.tabs(["📋 Config", "🗂️ Data", "🔍 Queries", "🔧 Tools", "🤖 Agents", "📝 Guide"])

            # Auto-load assets when demo is selected (after tabs are created)
            # Use a session state key specific to this demo to track if we've loaded
            assets_key = f"assets_loaded_{st.session_state.current_demo_module}"

            if not st.session_state.get(assets_key, False):
                with st.spinner("Loading demo assets..."):
                    try:
                        # Load all assets
                        datasets = load_demo_datasets(st.session_state.current_demo_module)
                        queries = load_demo_queries(st.session_state.current_demo_module)
                        guide = load_demo_guide(st.session_state.current_demo_module)

                        # Mark assets as loaded for this specific demo
                        st.session_state[assets_key] = True
                        st.session_state.assets_generated = True  # Keep for backwards compatibility
                    except Exception as e:
                        logger.error(f"Error auto-loading assets: {e}")
                        st.error(f"Error loading assets: {e}")

            # Render each tab using extracted modules
            with tabs[0]:
                render_config_tab(loader, assets_key)

            with tabs[1]:
                render_data_tab()

            with tabs[2]:
                render_queries_tab(loader)

            with tabs[3]:
                render_tools_tab(loader)

            with tabs[4]:
                # Initialize Agent Builder service for agents tab
                from src.services.agent_builder_service import AgentBuilderService

                try:
                    agent_builder = AgentBuilderService()
                    render_agents_tab(agent_builder)
                except Exception as e:
                    st.error(f"❌ Agent Builder Service not configured: {e}")
                    st.info("Please set ELASTICSEARCH_KIBANA_URL and ELASTICSEARCH_API_KEY in your .env file")

            with tabs[5]:
                render_guide_tab()
        else:
            st.info("👈 Select a demo from the sidebar to view details")
