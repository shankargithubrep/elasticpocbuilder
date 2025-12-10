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

    st.markdown("### 💬 Help Chat")
    st.caption("Ask questions about using Vulcan")

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
