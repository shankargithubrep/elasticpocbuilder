"""
Elastic Agent Builder Demo Generator
Modular architecture with LLM-generated custom demos
"""

# Load environment variables from .env file FIRST
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
import sys
import pandas as pd

# Add project modules to path
sys.path.insert(0, str(Path(__file__).parent))

# Import modular framework
from src.framework import (
    ModularDemoOrchestrator,
    DemoModuleManager,
    list_demos
)

# Import UI components
from src.ui import (
    render_sidebar,
    render_create_demo_view,
    render_browse_demos_view
)
# Help chat is now part of sidebar modes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Vulcan",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Automated demo generation for Elastic Agent Builder",
    },
)

# Custom CSS
st.markdown("""
<style>
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    /* Blue assistant avatar instead of default red */
    [data-testid="stChatMessageAvatarAssistant"] {
        background-color: #2563EB !important;
    }
    .context-badge {
        background-color: rgba(0, 123, 255, 0.2);
        border: 1px solid #007BFF;
        border-radius: 15px;
        padding: 5px 10px;
        margin: 2px;
        display: inline-block;
        font-size: 0.9em;
    }
    .success-badge {
        background-color: rgba(0, 255, 0, 0.2);
        border: 1px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "demo_context" not in st.session_state:
    st.session_state.demo_context = {
        "company_name": None,
        "department": None,
        "industry": None,
        "pain_points": [],
        "use_cases": [],
        "metrics": [],
        "scale": None,
        "urgency": None,
    }

if "conversation_phase" not in st.session_state:
    st.session_state.conversation_phase = "initial"

if "needs_processing" not in st.session_state:
    st.session_state.needs_processing = False

if "current_demo_module" not in st.session_state:
    st.session_state.current_demo_module = None

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "create"  # "create" or "browse"

if "show_under_the_hood" not in st.session_state:
    st.session_state.show_under_the_hood = False

if "ai_expansion_enabled" not in st.session_state:
    st.session_state.ai_expansion_enabled = False

if "ai_expansion_used" not in st.session_state:
    st.session_state.ai_expansion_used = False

if "llm_model" not in st.session_state:
    st.session_state.llm_model = None


def main():
    """Main application entry point"""

    # Render sidebar
    with st.sidebar:
        render_sidebar()

    # Check if showing "Under the hood" view
    if st.session_state.get("show_under_the_hood", False):
        from src.ui.views.under_the_hood import render_under_the_hood

        # Add a back button
        if st.button("← Back to Create Demo", key="back_from_under_hood"):
            st.session_state.show_under_the_hood = False
            st.rerun()

        render_under_the_hood()
    else:
        # Render main content based on mode (Create or Browse only)
        if st.session_state.view_mode == "create":
            render_create_demo_view()
        else:
            render_browse_demos_view()


if __name__ == "__main__":
    main()
