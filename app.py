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
    page_title="Elastic Demo Builder",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Automated demo generation for Elastic Agent Builder",
    },
)

# ── Elastic Brand Theme ────────────────────────────────────────────────────────
# Palette:
#   Primary blue  #005571   Teal accent  #00BFB3   Dark navy   #1D1E24
#   Body text     #343741   Muted        #69707D   Border      #D3DAE6
#   BG light      #F5F7FA   Pink         #F04E98   Yellow      #FEC514
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>

/* ── Global ──────────────────────────────────────────────────────────────── */
.stApp {
    background-color: #F5F7FA;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1D1E24 0%, #25262E 100%) !important;
    border-right: 1px solid #343741;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div {
    color: #DFE5EF !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #00BFB3 !important;
}
[data-testid="stSidebar"] hr {
    border-color: #343741 !important;
    opacity: 0.5;
}
[data-testid="stSidebar"] .stButton button {
    background-color: #2A2B33 !important;
    border: 1px solid #4A4B55 !important;
    color: #DFE5EF !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background-color: #005571 !important;
    border-color: #00BFB3 !important;
    color: white !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background-color: #2A2B33 !important;
    border: 1px solid #343741 !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    color: #00BFB3 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #2A2B33 !important;
    border: 1px solid #4A4B55 !important;
    color: #DFE5EF !important;
}
[data-testid="stSidebar"] input {
    background-color: #2A2B33 !important;
    border: 1px solid #4A4B55 !important;
    color: #DFE5EF !important;
    border-radius: 6px !important;
}
[data-testid="stSidebar"] .stAlert {
    background-color: #1a3a3a !important;
    border-left: 3px solid #00BFB3 !important;
    border-radius: 6px !important;
}

/* ── Top header bar ──────────────────────────────────────────────────────── */
[data-testid="stHeader"] {
    background-color: #005571 !important;
    border-bottom: 2px solid #00BFB3 !important;
}

/* ── Main headings ───────────────────────────────────────────────────────── */
.stMainBlockContainer h1,
.stMainBlockContainer h2,
.stMainBlockContainer h3 {
    color: #005571 !important;
    font-weight: 700 !important;
}
.stMainBlockContainer h4 {
    color: #343741 !important;
    font-weight: 600 !important;
}

/* ── Primary buttons ─────────────────────────────────────────────────────── */
.stButton > button[kind="primary"] {
    background-color: #00BFB3 !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    transition: background-color 0.15s ease !important;
}
.stButton > button[kind="primary"]:hover {
    background-color: #009e97 !important;
}
.stButton > button[kind="primary"]:disabled {
    background-color: #D3DAE6 !important;
    color: #69707D !important;
}

/* ── Secondary buttons ───────────────────────────────────────────────────── */
.stButton > button[kind="secondary"] {
    background-color: white !important;
    border: 1px solid #D3DAE6 !important;
    color: #343741 !important;
    border-radius: 6px !important;
    transition: all 0.15s ease !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #00BFB3 !important;
    color: #005571 !important;
}

/* ── Input fields ────────────────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    border: 1px solid #D3DAE6 !important;
    border-radius: 6px !important;
    background-color: white !important;
    color: #343741 !important;
    transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #00BFB3 !important;
    box-shadow: 0 0 0 2px rgba(0, 191, 179, 0.15) !important;
    outline: none !important;
}

/* ── Select boxes ────────────────────────────────────────────────────────── */
[data-baseweb="select"] > div {
    border: 1px solid #D3DAE6 !important;
    border-radius: 6px !important;
    background-color: white !important;
    transition: border-color 0.15s ease !important;
}
[data-baseweb="select"] > div:focus-within {
    border-color: #00BFB3 !important;
    box-shadow: 0 0 0 2px rgba(0, 191, 179, 0.15) !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background-color: white !important;
    border-radius: 8px 8px 0 0 !important;
    border-bottom: 2px solid #D3DAE6 !important;
    gap: 2px !important;
    padding: 0 4px !important;
}
.stTabs [data-baseweb="tab"] {
    color: #69707D !important;
    font-weight: 500 !important;
    border-radius: 6px 6px 0 0 !important;
    padding: 8px 14px !important;
    transition: color 0.15s ease !important;
    font-size: 0.85rem !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #005571 !important;
    background-color: #F5F7FA !important;
}
.stTabs [aria-selected="true"] {
    color: #005571 !important;
    font-weight: 700 !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #00BFB3 !important;
    height: 3px !important;
    border-radius: 3px 3px 0 0 !important;
}

/* ── Segmented control ───────────────────────────────────────────────────── */
[data-testid="stSegmentedControl"] {
    background-color: #F5F7FA !important;
    border: 1px solid #D3DAE6 !important;
    border-radius: 6px !important;
    padding: 2px !important;
}
[data-testid="stSegmentedControl"] button[aria-checked="true"] {
    background-color: #005571 !important;
    color: white !important;
    border-radius: 5px !important;
}
[data-testid="stSegmentedControl"] button[aria-checked="false"] {
    color: #69707D !important;
}

/* ── Metrics ─────────────────────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background-color: white !important;
    border: 1px solid #D3DAE6 !important;
    border-left: 3px solid #00BFB3 !important;
    border-radius: 6px !important;
    padding: 12px 16px !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05) !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    color: #69707D !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    font-weight: 600 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #005571 !important;
    font-weight: 700 !important;
}

/* ── Expanders ───────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border: 1px solid #D3DAE6 !important;
    border-radius: 8px !important;
    background-color: white !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
    margin-bottom: 6px !important;
}
[data-testid="stExpander"] summary {
    color: #005571 !important;
    font-weight: 600 !important;
    padding: 10px 14px !important;
}
[data-testid="stExpander"] summary:hover {
    background-color: #F5F7FA !important;
    border-radius: 7px !important;
}

/* ── Alert boxes ─────────────────────────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 6px !important;
}
div[data-testid="stAlert"] > div[role="alert"] {
    border-radius: 6px !important;
}

/* ── Dataframes ──────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #D3DAE6 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

/* ── Dividers ────────────────────────────────────────────────────────────── */
hr {
    border-color: #D3DAE6 !important;
    opacity: 0.8 !important;
}

/* ── Progress bar ────────────────────────────────────────────────────────── */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #005571 0%, #00BFB3 100%) !important;
    border-radius: 4px !important;
}

/* ── Spinner ─────────────────────────────────────────────────────────────── */
.stSpinner > div {
    border-top-color: #00BFB3 !important;
}

/* ── Toggle ──────────────────────────────────────────────────────────────── */
[data-testid="stToggle"] [data-checked="true"],
input[type="checkbox"]:checked + div {
    background-color: #00BFB3 !important;
}

/* ── Checkbox ────────────────────────────────────────────────────────────── */
[data-baseweb="checkbox"] [data-checked="true"] {
    background-color: #00BFB3 !important;
    border-color: #00BFB3 !important;
}

/* ── Chat messages ───────────────────────────────────────────────────────── */
.stChatMessage {
    background-color: white !important;
    border: 1px solid #D3DAE6 !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    margin-bottom: 8px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
}
[data-testid="stChatMessageAvatarAssistant"] {
    background-color: #005571 !important;
}
[data-testid="stChatMessageAvatarUser"] {
    background-color: #00BFB3 !important;
}

/* ── Chat input ──────────────────────────────────────────────────────────── */
[data-testid="stChatInput"] {
    border: 1px solid #D3DAE6 !important;
    border-radius: 8px !important;
    background-color: white !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #00BFB3 !important;
    box-shadow: 0 0 0 2px rgba(0, 191, 179, 0.15) !important;
}
[data-testid="stChatInput"] button {
    background-color: #005571 !important;
    border-radius: 6px !important;
}
[data-testid="stChatInput"] button:hover {
    background-color: #00BFB3 !important;
}

/* ── Code blocks ─────────────────────────────────────────────────────────── */
[data-testid="stCodeBlock"] {
    border-radius: 6px !important;
    border: 1px solid #D3DAE6 !important;
}

/* ── Info/Success/Warning/Error boxes ────────────────────────────────────── */
div[data-testid="stAlert"][kind="info"] {
    background-color: #EBF5F9 !important;
    border-left: 4px solid #005571 !important;
}
div[data-testid="stAlert"][kind="success"] {
    background-color: #E6FAF9 !important;
    border-left: 4px solid #00BFB3 !important;
}
div[data-testid="stAlert"][kind="warning"] {
    background-color: #FFF8E6 !important;
    border-left: 4px solid #FEC514 !important;
}
div[data-testid="stAlert"][kind="error"] {
    background-color: #FFF0F0 !important;
    border-left: 4px solid #BD271E !important;
}

/* ── Badges (preserved from original) ───────────────────────────────────── */
.context-badge {
    background-color: rgba(0, 191, 179, 0.12);
    border: 1px solid #00BFB3;
    border-radius: 15px;
    padding: 4px 10px;
    margin: 2px;
    display: inline-block;
    font-size: 0.85em;
    color: #005571;
    font-weight: 500;
}
.success-badge {
    background-color: rgba(0, 191, 179, 0.12);
    border: 1px solid #00BFB3;
    border-radius: 15px;
    padding: 4px 10px;
    color: #007a73;
    font-weight: 500;
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
        # Render main content based on mode
        if st.session_state.view_mode == "create":
            render_create_demo_view()
        elif st.session_state.view_mode == "help":
            from src.ui.views.help_docs import render_help_docs
            render_help_docs()
        elif st.session_state.view_mode == "whats_new":
            from src.ui.views.whats_new_view import render_whats_new_view
            render_whats_new_view()
        elif st.session_state.view_mode == "prompt_builder":
            from src.ui.views.prompt_builder_view import render_prompt_builder_view
            render_prompt_builder_view()
        else:
            render_browse_demos_view()


if __name__ == "__main__":
    main()
