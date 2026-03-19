"""
Context display components for sidebar

Renders the extracted demo context in the sidebar with progress tracking
and visual indicators for completion status.
"""

import streamlit as st


def display_context_summary():
    """Display extracted context in sidebar with progress tracking"""
    from src.services.context_tracker import ContextTracker

    tracker = ContextTracker()
    context = st.session_state.demo_context

    # Calculate progress
    progress, missing = tracker.calculate_progress(context)
    status = tracker.get_completion_status(context)

    st.caption(
        "**Extracted Context**",
        help="Context extracted from your prompt. Elastic POC Builder uses this to generate realistic data, queries, and demo guides tailored to your customer scenario. All fields should be filled before generation — it will prompt you for any missing details."
    )

    # Show demo type if detected
    demo_type = context.get('demo_type')
    if demo_type:
        type_emoji = "🔍" if demo_type == "search" else "📊"
        type_label = "Search/RAG" if demo_type == "search" else "Analytics"
        st.caption(f"{type_emoji} {type_label} Demo")

    # Display fields as simple list with emoji indicators
    for field_key, field_status in status.items():
        name = field_status['display_name']
        value = field_status['display_value']

        if field_status['is_complete']:
            st.markdown(f"✅ **{name}:** {value}")
        else:
            st.markdown(f"⬜ **{name}**")

    # Ready message directly after context (no divider)
    if tracker.is_ready_to_generate(context):
        st.success("Type **'generate'** to create your demo.")
