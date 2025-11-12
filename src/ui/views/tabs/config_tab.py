"""
Config Tab - Displays demo configuration and allows asset regeneration.
"""

import streamlit as st
import logging
import os
import anthropic

from src.ui.data_loaders import (
    load_demo_datasets,
    load_demo_queries,
    load_demo_guide
)

logger = logging.getLogger(__name__)


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
        llm_client = None
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            llm_client = anthropic.Anthropic(api_key=api_key)

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