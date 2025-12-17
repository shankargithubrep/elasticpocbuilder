"""
Help Chat Widget - Contextual assistant for Vulcan.

Renders as a sidebar mode (alongside Create and Browse).
"""

import streamlit as st
import logging

from .chips import get_chips_for_context
from .context_provider import get_current_context
from src.services.help_chat_service import get_help_service

logger = logging.getLogger(__name__)


def _get_ai_status():
    """
    Check AI Assistant status by checking for index existence.

    Returns:
        tuple: (is_available, is_enabled, doc_count)
            - is_available: Whether ES connection works
            - is_enabled: Whether the doc index exists with documents
            - doc_count: Number of indexed documents (0 if not enabled)
    """
    try:
        from src.services.doc_indexer_service import get_doc_indexer
        doc_indexer = get_doc_indexer()

        if not doc_indexer.is_available():
            return (False, False, 0)

        if doc_indexer.check_index_exists():
            stats = doc_indexer.get_index_stats()
            return (True, True, stats.get('count', 0))

        return (True, False, 0)
    except Exception as e:
        logger.warning(f"Error checking AI status: {e}")
        return (False, False, 0)


def _enable_ai_assistant():
    """Enable AI Assistant by indexing documentation."""
    try:
        from src.services.doc_indexer_service import get_doc_indexer
        doc_indexer = get_doc_indexer()

        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(pct, msg):
            progress_bar.progress(pct / 100)
            status_text.caption(msg)

        result = doc_indexer.index_documentation(progress_callback=update_progress)

        progress_bar.empty()
        status_text.empty()

        return result.success, result.documents_indexed, result.errors
    except Exception as e:
        logger.error(f"Error enabling AI: {e}")
        return False, 0, [str(e)]


def _disable_ai_assistant():
    """Disable AI Assistant by deleting the documentation index."""
    try:
        from src.services.doc_indexer_service import get_doc_indexer
        doc_indexer = get_doc_indexer()
        return doc_indexer.delete_index()
    except Exception as e:
        logger.error(f"Error disabling AI: {e}")
        return False


def _is_ai_enabled() -> bool:
    """Check if AI-powered doc search is enabled."""
    _, is_enabled, _ = _get_ai_status()
    return is_enabled


def _process_message(message: str) -> str:
    """Process a user message and get response. Returns the response."""
    if not message or not message.strip():
        return ""

    context = get_current_context()
    help_service = get_help_service()

    try:
        response = help_service.get_response(
            user_message=message,
            context=context,
            chat_history=[]
        )
        return response
    except Exception as e:
        logger.error(f"Help chat error: {e}")
        return "I encountered an error. Please try again."


def render_chat_sidebar():
    """Render the chat interface in sidebar (called when view_mode == 'chat')."""
    # Initialize state
    if "help_messages" not in st.session_state:
        st.session_state.help_messages = []

    context = get_current_context()
    chips = get_chips_for_context(context)

    # Check AI status
    is_available, is_enabled, doc_count = _get_ai_status()

    # Header
    if is_enabled:
        st.markdown("### 🤖 AI Help")
        st.caption(f"Semantic search enabled ({doc_count} docs)")
    else:
        st.markdown("### 💬 Help Chat")

    # AI Assistant controls at top
    if is_available:
        if is_enabled:
            # Show disable button
            st.caption("Deletes indexed docs from Elasticsearch")
            if st.button("🔴 Disable AI Assistant", use_container_width=True, key="disable_ai_btn"):
                with st.spinner("Removing index..."):
                    if _disable_ai_assistant():
                        st.success("AI Assistant disabled")
                        st.rerun()
                    else:
                        st.error("Failed to disable")
        else:
            # Show enable button
            st.caption("Indexes docs to ES Serverless (requires .env)")
            if st.button("🟢 Enable AI Assistant", use_container_width=True, key="enable_ai_btn"):
                success, count, errors = _enable_ai_assistant()
                if success:
                    st.success(f"Indexed {count} docs!")
                    st.rerun()
                else:
                    st.error(f"Failed: {', '.join(errors[:2])}")
    else:
        st.info("AI requires ES Serverless connection")

    st.markdown("---")

    # Chat history
    if st.session_state.help_messages:
        for msg in st.session_state.help_messages:
            if msg["role"] == "user":
                st.markdown(f"**You:** {msg['content']}")
            else:
                st.markdown(msg["content"])
            st.divider()

        # Clear button
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.help_messages = []
            st.rerun()
    else:
        st.info("👋 Ask a question or click a topic below!")

    st.markdown("---")

    # Quick questions
    st.markdown("**Quick questions:**")
    for i, chip in enumerate(chips[:4]):
        if st.button(chip, key=f"chat_chip_{i}", use_container_width=True):
            # Add user message
            st.session_state.help_messages.append({
                "role": "user",
                "content": chip
            })
            # Get response
            response = _process_message(chip)
            st.session_state.help_messages.append({
                "role": "assistant",
                "content": response
            })
            st.rerun()

    st.markdown("---")

    # Custom question input
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Your question",
            placeholder="Type your question here...",
            height=80,
            label_visibility="collapsed"
        )
        if st.form_submit_button("Ask", use_container_width=True, type="primary"):
            if user_input and user_input.strip():
                st.session_state.help_messages.append({
                    "role": "user",
                    "content": user_input.strip()
                })
                response = _process_message(user_input.strip())
                st.session_state.help_messages.append({
                    "role": "assistant",
                    "content": response
                })
                st.rerun()


# Legacy functions - no longer used
def render_help_header():
    """Deprecated - use render_chat_sidebar() instead."""
    pass

def render_help_button():
    """Deprecated."""
    pass

def render_help_panel():
    """Deprecated."""
    pass

def render_help_widget():
    """Deprecated."""
    pass
