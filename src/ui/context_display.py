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

    st.markdown("### 📋 Demo Context")

    # Show demo type if detected
    demo_type = context.get('demo_type')
    if demo_type:
        type_emoji = "🔍" if demo_type == "search" else "📊"
        type_label = "Search/RAG" if demo_type == "search" else "Analytics"
        st.info(f"{type_emoji} **Demo Type:** {type_label}")

    # Progress bar at top
    st.progress(progress, text=f"{int(progress * 100)}% complete")

    # Display fields as simple list with emoji indicators
    st.markdown("#### Extracted Context")

    for field_key, field_status in status.items():
        name = field_status['display_name']
        value = field_status['display_value']

        if field_status['is_complete']:
            # Complete: show green checkmark
            st.markdown(f"✅ **{name}:** {value}")
        else:
            # Incomplete: show red X
            st.markdown(f"❌ **{name}:** *(not set)*")

    # Status message
    st.markdown("---")

    if tracker.is_ready_to_generate(context):
        st.success("✅ Ready to generate!\n\nType **'generate'** to create your demo.")
    else:
        missing_count = len(missing)
        st.warning(f"⚠️ Need more info ({missing_count} fields)")
