"""
Guide Tab - Displays the demo guide narrative.
"""

import streamlit as st
from src.ui.data_loaders import load_demo_guide


def render_guide_tab():
    """Render the Guide tab content."""
    # Only load if assets have been generated
    if st.session_state.get("assets_generated", False):
        try:
            guide = load_demo_guide(st.session_state.current_demo_module)
            if guide:
                st.markdown(guide)
            else:
                st.info("No demo guide found. Try regenerating assets from the Config tab.")
        except Exception as e:
            st.error(f"Error loading guide: {e}")
            st.info("Try clicking 'Generate Assets' in the Config tab.")
    else:
        st.info("📋 Click 'Generate Assets' in the Config tab to view the demo guide")