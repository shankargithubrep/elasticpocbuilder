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
    if not st.session_state.current_demo_module:
        st.markdown("### Browse Demos")
        st.info(
            "**Select a demo** from the list on the left to view its details, "
            "or switch to **Create** mode to generate a new one.\n\n"
            "Generated demos are stored in the `demos/` directory and persist across sessions."
        )
        return

    if st.session_state.current_demo_module:
        st.markdown(f"#### 📊 {st.session_state.current_demo_module}")

        # Progress tracking header
        render_progress_header(st.session_state.current_demo_module)

        st.caption("Step through each tab to bring your demo to life: "
                   "**Data** — index generated datasets into Elasticsearch. "
                   "**Queries** — test and validate ES|QL queries against your data. "
                   "**Tools** — deploy validated queries as Agent Builder tools. "
                   "**Agents** — configure and deploy your agent. "
                   "**Guide** — review the presenter script and talk track.")

        manager = DemoModuleManager()
        loader = manager.get_module(st.session_state.current_demo_module)

        if loader:
            # Tab labels and icons — use a session-state-backed selector so
            # the active tab survives Streamlit reruns (st.tabs resets on every
            # rerun because it's a layout element, not a stateful widget).
            TAB_OPTIONS = [
                "📋 Config",
                "🗂️ Data",
                "🔍 Queries",
                "🔧 Tools",
                "🤖 Agents",
                "📝 Guide",
            ]

            if "browse_active_tab" not in st.session_state:
                st.session_state["browse_active_tab"] = TAB_OPTIONS[0]

            active_tab = st.segmented_control(
                "Tab",
                options=TAB_OPTIONS,
                default=st.session_state["browse_active_tab"],
                key="browse_active_tab",
                label_visibility="collapsed",
            )

            # Auto-load assets when demo is selected
            assets_key = f"assets_loaded_{st.session_state.current_demo_module}"

            if not st.session_state.get(assets_key, False):
                with st.spinner("Loading demo assets..."):
                    try:
                        datasets = load_demo_datasets(st.session_state.current_demo_module)
                        queries = load_demo_queries(st.session_state.current_demo_module)
                        guide = load_demo_guide(st.session_state.current_demo_module)

                        st.session_state[assets_key] = True
                        st.session_state.assets_generated = True
                    except Exception as e:
                        logger.error(f"Error auto-loading assets: {e}")
                        st.error(f"Error loading assets: {e}")

            # Render the selected tab
            if active_tab == "📋 Config":
                render_config_tab(loader, assets_key)

            elif active_tab == "🗂️ Data":
                render_data_tab()

            elif active_tab == "🔍 Queries":
                render_queries_tab(loader)

            elif active_tab == "🔧 Tools":
                render_tools_tab(loader)

            elif active_tab == "🤖 Agents":
                from src.services.agent_builder_service import AgentBuilderService

                try:
                    agent_builder = AgentBuilderService()
                    render_agents_tab(agent_builder)
                except Exception as e:
                    st.error(f"❌ Agent Builder Service not configured: {e}")
                    st.info("Please set ELASTICSEARCH_KIBANA_URL and ELASTICSEARCH_API_KEY in your .env file")

            elif active_tab == "📝 Guide":
                render_guide_tab()
        else:
            st.info("👈 Select a demo from the sidebar to view details")
