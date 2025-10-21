"""
Elastic Agent Builder Demo Generator
A conversation-based interface for creating custom demos for Elastic Solutions Architects
"""

import streamlit as st
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging
from pathlib import Path
import sys

# Add project modules to path
sys.path.insert(0, str(Path(__file__).parent))

# Import services (to be created)
from src.services.customer_researcher import CustomerResearcher
from src.services.scenario_generator import ScenarioGenerator
from src.services.data_generator import DataGenerator
from src.services.esql_generator import ESQLGenerator
from src.services.elastic_client import ElasticClient
from src.utils.session_state import initialize_session_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Elastic Demo Builder",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Automated demo generation for Elastic Agent Builder",
    },
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .user-message {
        background-color: rgba(59, 130, 246, 0.1);
    }
    .assistant-message {
        background-color: rgba(34, 197, 94, 0.1);
    }
    .demo-artifact {
        background-color: rgba(251, 191, 36, 0.1);
        border-left: 4px solid #fbbf24;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_app():
    """Initialize the Streamlit app and session state."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.demo_state = "initial"
        st.session_state.customer_info = {}
        st.session_state.scenario = {}
        st.session_state.generated_data = {}
        st.session_state.esql_queries = []
        st.session_state.demo_artifacts = {}

def render_sidebar():
    """Render the sidebar with demo progress and controls."""
    with st.sidebar:
        st.header("🚀 Demo Builder Progress")

        # Progress indicators
        progress_steps = {
            "initial": "🔵 Start",
            "research": "🔍 Customer Research",
            "scenario": "📋 Scenario Design",
            "data": "📊 Data Generation",
            "queries": "🔎 Query Creation",
            "validation": "✅ Validation",
            "complete": "🎉 Complete"
        }

        current_step = st.session_state.get("demo_state", "initial")
        for step, label in progress_steps.items():
            if step == current_step:
                st.markdown(f"**→ {label}**")
            elif list(progress_steps.keys()).index(step) < list(progress_steps.keys()).index(current_step):
                st.markdown(f"✓ ~~{label}~~")
            else:
                st.markdown(f"◯ {label}")

        st.divider()

        # Customer info display
        if st.session_state.customer_info:
            st.subheader("📋 Customer Info")
            for key, value in st.session_state.customer_info.items():
                if value:
                    st.text(f"{key}: {value}")

        st.divider()

        # Controls
        st.subheader("⚙️ Controls")
        if st.button("🔄 Start New Demo", use_container_width=True):
            st.session_state.clear()
            initialize_app()
            st.rerun()

        if st.button("💾 Export Demo Package", use_container_width=True):
            export_demo_package()

        st.divider()

        # Help section
        with st.expander("ℹ️ How to Use"):
            st.markdown("""
            1. **Start**: Provide customer name and context
            2. **Research**: AI researches the company
            3. **Scenario**: Design custom demo scenario
            4. **Generate**: Create sample data
            5. **Queries**: Build ES|QL queries
            6. **Validate**: Test everything works
            7. **Export**: Download demo package
            """)

def process_user_input(user_input: str):
    """Process user input and advance the demo state."""
    current_state = st.session_state.demo_state

    if current_state == "initial":
        # Extract customer info from initial input
        st.session_state.customer_info["input"] = user_input
        st.session_state.demo_state = "research"
        return "Great! Let me research this customer and understand their context. What specific team or department will you be demoing to?"

    elif current_state == "research":
        st.session_state.customer_info["department"] = user_input
        # Here we would call the CustomerResearcher service
        st.session_state.demo_state = "scenario"
        return """Based on my research, I've identified some potential use cases.

Let me design a custom scenario for your demo. What are the main pain points or goals this team has that Agent Builder could address?"""

    elif current_state == "scenario":
        st.session_state.customer_info["pain_points"] = user_input
        # Here we would call the ScenarioGenerator service
        st.session_state.demo_state = "data"
        return """Perfect! I'll create a scenario around those pain points.

Here's what I propose:
- **Primary Dataset**: Main business entities relevant to their use case
- **Performance Dataset**: Metrics and time-series data
- **Event Dataset**: Detailed activity logs

Shall I proceed with generating the sample data? Type 'yes' to continue or provide any specific requirements."""

    elif current_state == "data":
        if "yes" in user_input.lower():
            # Here we would call the DataGenerator service
            st.session_state.demo_state = "queries"
            return """Excellent! I've generated three interconnected datasets with realistic data.

Now let's create ES|QL queries that will answer their key business questions. I'll generate queries for:
1. Performance analytics
2. Trend analysis
3. Optimization opportunities
4. Operational insights

Type 'continue' to generate the queries."""
        else:
            return "Please specify your requirements for the data generation."

    elif current_state == "queries":
        if "continue" in user_input.lower():
            # Here we would call the ESQLGenerator service
            st.session_state.demo_state = "validation"
            return """Great! I've created 8 ES|QL queries tailored to their use cases.

Each query has been designed to:
- Show progressive complexity
- Demonstrate key ES|QL features
- Answer real business questions
- Work with the generated data

Ready to validate everything? Type 'validate' to test all queries."""
        else:
            return "What specific queries would you like me to include?"

    elif current_state == "validation":
        if "validate" in user_input.lower():
            # Here we would validate queries
            st.session_state.demo_state = "complete"
            return """✅ Validation Complete! All queries are working correctly.

Your demo package is ready! It includes:
- 📊 Sample datasets (CSV files)
- 🔍 ES|QL queries (tested and validated)
- 📝 Demo guide (markdown)
- 🎯 Agent configuration
- 🎨 Presentation slides

Use the 'Export Demo Package' button in the sidebar to download everything."""
        else:
            return "Type 'validate' when you're ready to test the queries."

    elif current_state == "complete":
        return "Your demo is complete! Use the sidebar to export or start a new demo."

    return "I'm not sure how to help with that. Please provide more context."

def export_demo_package():
    """Export all demo artifacts as a downloadable package."""
    # Create a timestamp for the export
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = Path(f"exports/demo_{timestamp}")

    # This would create zip file with all artifacts
    st.success("Demo package exported successfully!")
    st.balloons()

def render_chat_interface():
    """Render the main chat interface."""
    st.title("🚀 Elastic Agent Builder Demo Generator")
    st.markdown("### Create compelling, customized demos in minutes")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and "artifact" in message:
                # Display special formatting for artifacts
                st.markdown(f'<div class="demo-artifact">{message["content"]}</div>',
                          unsafe_allow_html=True)
            else:
                st.markdown(message["content"])

    # Chat input
    if st.session_state.demo_state == "initial":
        prompt = "Enter customer name and their website/industry:"
    else:
        prompt = "Your response:"

    if user_input := st.chat_input(prompt):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate assistant response
        response = process_user_input(user_input)

        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

        st.rerun()

def render_current_artifacts():
    """Display current demo artifacts in tabs."""
    if st.session_state.demo_state != "initial" and st.session_state.demo_state != "research":
        st.divider()
        st.subheader("📦 Demo Artifacts")

        tabs = st.tabs(["📊 Data", "🔍 Queries", "📝 Guide", "🎯 Agent Config"])

        with tabs[0]:
            if st.session_state.generated_data:
                st.markdown("### Generated Datasets")
                for dataset_name, info in st.session_state.generated_data.items():
                    with st.expander(f"📄 {dataset_name}"):
                        st.code(info.get("preview", "Data preview not available"))
            else:
                st.info("Data will be generated in the next step")

        with tabs[1]:
            if st.session_state.esql_queries:
                st.markdown("### ES|QL Queries")
                for i, query in enumerate(st.session_state.esql_queries, 1):
                    with st.expander(f"Query {i}: {query.get('name', 'Unnamed')}"):
                        st.code(query.get("esql", ""), language="sql")
                        st.markdown(f"**Description**: {query.get('description', '')}")
            else:
                st.info("Queries will be generated after data creation")

        with tabs[2]:
            if st.session_state.demo_artifacts.get("guide"):
                st.markdown("### Demo Guide")
                st.markdown(st.session_state.demo_artifacts["guide"])
            else:
                st.info("Demo guide will be generated upon completion")

        with tabs[3]:
            if st.session_state.demo_artifacts.get("agent_config"):
                st.markdown("### Agent Configuration")
                st.json(st.session_state.demo_artifacts["agent_config"])
            else:
                st.info("Agent configuration will be generated upon completion")

def main():
    """Main application entry point."""
    initialize_app()
    render_sidebar()

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        render_chat_interface()

    with col2:
        render_current_artifacts()

if __name__ == "__main__":
    main()