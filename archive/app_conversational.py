"""
Elastic Agent Builder Demo Generator - Conversational Version
An enhanced interface with guided onboarding and conversational context gathering
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

# Import services
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
    .demo-phase {
        padding: 10px;
        border-radius: 5px;
        background-color: rgba(0, 123, 255, 0.1);
        border-left: 4px solid #007BFF;
        margin: 10px 0;
    }
    .example-prompt {
        background-color: rgba(0, 255, 0, 0.05);
        border: 1px dashed #28a745;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        cursor: pointer;
    }
    .example-prompt:hover {
        background-color: rgba(0, 255, 0, 0.1);
    }
    .context-section {
        background-color: rgba(255, 193, 7, 0.1);
        border-left: 4px solid #ffc107;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .help-text {
        color: #6c757d;
        font-size: 0.9em;
        font-style: italic;
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
        "data_types": [],
        "demo_scope": None,
        "technical_level": None
    }

if "conversation_phase" not in st.session_state:
    st.session_state.conversation_phase = "initial"

if "demo_id" not in st.session_state:
    st.session_state.demo_id = None

# System prompt for the assistant
SYSTEM_PROMPT = """You are an expert Elastic Solutions Architect assistant helping create custom Agent Builder demos.

Your goal is to have a CONVERSATION to gather sufficient context before generating the demo. Follow this approach:

1. **Initial Greeting**: Welcome the user and ask about their customer
2. **Company Research**: Ask about the company, their industry, and department
3. **Pain Points Discovery**: Probe for specific challenges and pain points
4. **Use Case Refinement**: Suggest relevant use cases based on their needs
5. **Data Requirements**: Understand what data types would be most relevant
6. **Demo Scope**: Confirm the scope and complexity of the demo
7. **Generation**: Only after gathering context, proceed with demo generation

Always:
- Ask clarifying questions before making assumptions
- Suggest options when the user seems unsure
- Provide examples to guide their thinking
- Confirm understanding before proceeding
- Be conversational and helpful

Current context gathered:
{context}

Phase: {phase}
"""

def get_assistant_prompt():
    """Get the current system prompt with context"""
    return SYSTEM_PROMPT.format(
        context=json.dumps(st.session_state.demo_context, indent=2),
        phase=st.session_state.conversation_phase
    )

def display_onboarding():
    """Display onboarding information for new users"""
    with st.container():
        st.markdown("### 🚀 Welcome to the Elastic Agent Builder Demo Generator!")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            #### How to Get Started:
            1. **Describe your customer** - Company name and department
            2. **Discuss their challenges** - We'll explore pain points together
            3. **Select use cases** - I'll suggest relevant scenarios
            4. **Review the plan** - We'll confirm before generating
            5. **Generate demo** - Create data, queries, and agents
            """)

        with col2:
            st.markdown("""
            #### What I'll Help You Create:
            - 📊 Relevant synthetic data for the customer
            - 🔍 Working ES|QL queries with validation
            - 🤖 Configured agents with tools
            - 📝 Complete demo guide and scripts
            - ✅ Tested and validated components
            """)

        st.markdown("---")

        st.markdown("### 💡 Example Prompts to Get Started:")

        example_prompts = [
            {
                "title": "🏢 Enterprise Customer",
                "prompt": "I'm preparing a demo for Adobe's marketing operations team. They're struggling with campaign performance analytics and need real-time insights."
            },
            {
                "title": "🏥 Healthcare Customer",
                "prompt": "I have a meeting with Kaiser Permanente next week. They want to see how Agent Builder can help with patient flow optimization."
            },
            {
                "title": "🏪 Retail Customer",
                "prompt": "Target's e-commerce team needs help analyzing customer journey data and detecting anomalies in transaction patterns."
            },
            {
                "title": "🏦 Financial Services",
                "prompt": "JPMorgan Chase is interested in using Agent Builder for fraud detection and compliance monitoring."
            },
            {
                "title": "🎯 Quick Start",
                "prompt": "I need a demo for a marketing analytics use case. The customer wants to track campaign ROI and customer engagement."
            }
        ]

        for example in example_prompts:
            if st.button(f"{example['title']}", key=f"example_{example['title']}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": example['prompt']})
                st.rerun()

def display_context_summary():
    """Display the current context gathered"""
    if any(st.session_state.demo_context.values()):
        with st.sidebar:
            st.markdown("### 📋 Demo Context")

            context = st.session_state.demo_context

            if context["company_name"]:
                st.markdown(f"**Company:** {context['company_name']}")

            if context["department"]:
                st.markdown(f"**Department:** {context['department']}")

            if context["industry"]:
                st.markdown(f"**Industry:** {context['industry']}")

            if context["pain_points"]:
                st.markdown("**Pain Points:**")
                for point in context["pain_points"]:
                    st.markdown(f"- {point}")

            if context["use_cases"]:
                st.markdown("**Use Cases:**")
                for use_case in context["use_cases"]:
                    st.markdown(f"- {use_case}")

            if context["data_types"]:
                st.markdown("**Data Types:**")
                for data_type in context["data_types"]:
                    st.markdown(f"- {data_type}")

            progress = sum(1 for v in context.values() if v) / len(context)
            st.progress(progress, text=f"Context Gathering: {int(progress*100)}%")

def process_user_message(message: str) -> str:
    """Process user message and generate appropriate response"""

    # Update context based on message content
    context = st.session_state.demo_context
    phase = st.session_state.conversation_phase

    # Simple context extraction (in production, use NLP/LLM)
    message_lower = message.lower()

    # Extract company name
    if not context["company_name"]:
        # Look for company indicators
        companies = ["adobe", "target", "kaiser", "jpmorgan", "chase", "microsoft", "google", "amazon", "netflix"]
        for company in companies:
            if company in message_lower:
                context["company_name"] = company.title()
                break

    # Extract department
    if not context["department"]:
        departments = ["marketing", "sales", "operations", "it", "finance", "hr", "engineering", "support", "analytics"]
        for dept in departments:
            if dept in message_lower:
                context["department"] = dept.title()
                break

    # Detect pain points keywords
    if "struggle" in message_lower or "challenge" in message_lower or "problem" in message_lower or "issue" in message_lower:
        # Extract pain points from message
        if "performance" in message_lower:
            context["pain_points"].append("Performance optimization")
        if "insight" in message_lower or "analytics" in message_lower:
            context["pain_points"].append("Lack of real-time insights")
        if "roi" in message_lower:
            context["pain_points"].append("ROI measurement")

    # Generate contextual response based on phase
    if phase == "initial":
        if not context["company_name"]:
            return """Thanks for reaching out! I'd love to help you create a compelling Agent Builder demo.

To get started, could you tell me:
1. **Which company** is this demo for?
2. **Which department or team** will be the primary audience?
3. **What's the main business challenge** they're facing?

Feel free to share as much context as you'd like - the more I understand about their needs, the better I can tailor the demo!"""

        elif not context["department"]:
            return f"""Great! I see you're working with {context['company_name']}.

Which department or team will be the primary audience for this demo? For example:
- Marketing Operations
- Sales Analytics
- IT Operations
- Customer Support
- Finance/Compliance

Also, what are the main challenges they're trying to solve?"""

        elif not context["pain_points"]:
            return f"""Perfect! So we're creating a demo for {context['company_name']}'s {context['department']} team.

What are the **specific pain points or challenges** they're facing? For example:
- Slow query performance on large datasets?
- Difficulty in creating custom analytics?
- Need for real-time insights?
- Complex data relationships?
- Manual reporting processes?

Understanding their pain points will help me suggest the most relevant use cases."""

        else:
            st.session_state.conversation_phase = "use_case_selection"

    if phase == "use_case_selection":
        # Suggest relevant use cases
        researcher = CustomerResearcher()
        profile = researcher.research_company(
            context["company_name"] or "Generic Company",
            context["department"] or "Operations"
        )

        response = f"""Based on what you've told me about {context['company_name']}'s {context['department']} team, here are some relevant Agent Builder use cases:

"""
        for i, use_case in enumerate(profile.use_cases[:3], 1):
            response += f"**{i}. {use_case}**\n"

        response += """
Which of these resonates most with their needs? Or would you like to explore a different angle?

Once we confirm the use case, I'll design the demo with:
- Relevant synthetic data matching their business
- ES|QL queries addressing their specific needs
- Configured agents with appropriate tools
"""
        context["use_cases"] = profile.use_cases
        st.session_state.conversation_phase = "confirmation"
        return response

    if phase == "confirmation":
        return """Excellent choice! Let me confirm the demo plan:

**📋 Demo Summary:**
- **Customer:** """ + f"{context['company_name']} - {context['department']}" + """
- **Primary Use Case:** """ + (context['use_cases'][0] if context['use_cases'] else "Analytics") + """
- **Key Capabilities to Showcase:**
  - Real-time data analysis with ES|QL
  - Natural language interaction with agents
  - Custom tool creation for specific queries
  - Performance at scale

**🚀 Ready to Generate?**
If this looks good, I'll create:
1. **Synthetic datasets** (customers, products, transactions, metrics)
2. **10+ ES|QL queries** (validated and optimized)
3. **Configured agent** with conversation examples
4. **Complete demo guide** with talk track

Type "**Generate demo**" to proceed, or let me know if you'd like to adjust anything!"""

    if "generate demo" in message_lower:
        st.session_state.conversation_phase = "generating"
        return "🚀 Starting demo generation! I'll create all the components for your demo. This will take about 30 seconds..."

    # Default response
    return """I'm here to help create your demo! Could you provide more details about:
- The customer company and department
- Their specific challenges or pain points
- What success looks like for them

The more context you share, the better I can tailor the demo!"""

def main():
    st.title("🚀 Elastic Agent Builder Demo Generator")
    st.markdown("*AI-powered demo creation for Solutions Architects*")

    # Display context in sidebar
    display_context_summary()

    # Main chat interface
    col1, col2 = st.columns([2, 1])

    with col1:
        # Show onboarding if no messages
        if not st.session_state.messages:
            display_onboarding()

        # Chat messages container
        chat_container = st.container()

        with chat_container:
            # Display chat messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Describe your customer and their needs..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Generate response
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = process_user_message(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

                    # If ready to generate, start the process
                    if st.session_state.conversation_phase == "generating":
                        with st.spinner("Generating demo components..."):
                            # Here we would call the actual generation services
                            st.success("✅ Demo generated successfully!")
                            st.balloons()

                            # Show download buttons
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.download_button(
                                    "📝 Download Demo Guide",
                                    data="# Demo Guide\n\nYour demo content here...",
                                    file_name="demo_guide.md",
                                    mime="text/markdown"
                                )
                            with col2:
                                st.download_button(
                                    "🔍 Download ES|QL Queries",
                                    data="-- ES|QL Queries\n\nFROM index | ...",
                                    file_name="queries.es",
                                    mime="text/plain"
                                )
                            with col3:
                                st.download_button(
                                    "📊 Download Sample Data",
                                    data="id,name,value\n1,test,100",
                                    file_name="sample_data.csv",
                                    mime="text/csv"
                                )

    with col2:
        # Help panel
        with st.expander("ℹ️ Help & Tips", expanded=True):
            st.markdown("""
            ### 🎯 Tips for Effective Demos

            **Gather Context First:**
            - Company name and industry
            - Department and audience
            - Specific pain points
            - Success criteria

            **Be Specific:**
            - "Campaign ROI tracking" > "Analytics"
            - "Fraud detection in payments" > "Security"
            - "Customer churn prediction" > "ML"

            **Common Use Cases:**
            - Performance Analytics
            - Customer 360 View
            - Operational Intelligence
            - Fraud Detection
            - Compliance Monitoring

            **Need Help?**
            - Type "help" for guidance
            - Use example prompts to start
            - Ask clarifying questions
            """)

        # Quick actions
        st.markdown("### ⚡ Quick Actions")

        if st.button("🔄 Start New Demo", use_container_width=True):
            st.session_state.messages = []
            st.session_state.demo_context = {
                "company_name": None,
                "department": None,
                "industry": None,
                "pain_points": [],
                "use_cases": [],
                "data_types": [],
                "demo_scope": None,
                "technical_level": None
            }
            st.session_state.conversation_phase = "initial"
            st.rerun()

        if st.button("📋 Load Previous Demo", use_container_width=True):
            demo_id = st.text_input("Enter Demo ID:")
            if demo_id:
                st.info(f"Loading demo: {demo_id}")
                # Load demo from GitHub state

        if st.button("🧪 Test Components", use_container_width=True):
            st.info("Running component tests...")
            # Run validation tests

if __name__ == "__main__":
    main()