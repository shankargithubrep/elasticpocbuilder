"""
Conversation Tab - Displays the original conversation that created the demo.
"""

import streamlit as st
import json
import logging

logger = logging.getLogger(__name__)


def render_conversation_tab(loader):
    """Render the Conversation tab content.

    Args:
        loader: The demo module loader instance
    """
    # Load and display conversation history
    st.markdown("### Original Conversation")
    st.markdown("This is the conversation that led to the creation of this demo.")

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