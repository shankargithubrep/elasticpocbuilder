"""
Elastic Agent Builder Demo Generator
Modular architecture with LLM-generated custom demos
"""

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

# Custom CSS
st.markdown("""
<style>
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
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


class SmartContextExtractor:
    """Intelligent context extraction from user messages"""

    def __init__(self):
        self.company_patterns = [
            r"(?:for|with|at|meeting with)\s+([A-Z][A-Za-z0-9\s&'.-]+?)(?:'s|'s|team|division|department|\s+wants|\s+needs|\s+is|\s+has|,|\.|\s+[a-z])",
            r"^([A-Z][A-Za-z0-9\s&'.-]+?)(?:'s|'s|team|division|department|\s+wants|\s+needs)",
            r"(?:customer|client|prospect)\s+is\s+([A-Z][A-Za-z0-9\s&'.-]+)",
        ]

        self.department_keywords = {
            "customer success": ["customer success", "cs team", "account management"],
            "sales": ["sales", "revenue", "account executive"],
            "marketing": ["marketing", "campaign", "brand"],
            "engineering": ["engineering", "development", "devops"],
            "operations": ["operations", "ops team", "supply chain"],
            "finance": ["finance", "accounting", "treasury"],
            "analytics": ["analytics", "data team", "business intelligence"],
        }

        self.pain_point_patterns = {
            "visibility": ["can't see", "no visibility", "lack of visibility"],
            "performance": ["slow", "performance", "takes hours"],
            "prediction": ["predict", "forecast", "anticipate", "prevent"],
            "real_time": ["real-time", "real time", "instant"],
            "manual": ["manual", "by hand", "spreadsheet"],
        }

    def extract_context(self, message: str) -> Dict:
        """Extract all possible context from the message"""
        context = {}

        company = self.extract_company(message)
        if company:
            context["company_name"] = company
            context["industry"] = self.infer_industry(company)

        department = self.extract_department(message)
        if department:
            context["department"] = department

        pain_points = self.extract_pain_points(message)
        if pain_points:
            context["pain_points"] = pain_points

        metrics = self.extract_metrics(message)
        if metrics:
            context["metrics"] = metrics

        scale = self.extract_scale(message)
        if scale:
            context["scale"] = scale

        return context

    def extract_company(self, message: str) -> Optional[str]:
        """Extract company name from message"""
        for pattern in self.company_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                company = re.sub(r"\s+(team|division|department)$", "", company, flags=re.IGNORECASE)
                return company
        return None

    def extract_department(self, message: str) -> Optional[str]:
        """Extract department from message"""
        message_lower = message.lower()
        for dept_name, keywords in self.department_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    return dept_name.title()
        return None

    def extract_pain_points(self, message: str) -> List[str]:
        """Extract pain points from message"""
        pain_points = []
        message_lower = message.lower()

        for category, patterns in self.pain_point_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    if category == "visibility":
                        pain_points.append("Lack of real-time visibility")
                    elif category == "performance":
                        pain_points.append("Performance issues")
                    elif category == "prediction":
                        pain_points.append("Lack of predictive capabilities")
                    elif category == "real_time":
                        pain_points.append("Need for real-time insights")
                    elif category == "manual":
                        pain_points.append("Manual processes")
                    break

        return list(set(pain_points))

    def extract_metrics(self, message: str) -> List[str]:
        """Extract mentioned metrics from message"""
        metrics = []
        message_lower = message.lower()

        metric_keywords = {
            "Revenue": ["revenue", "arr", "mrr"],
            "Churn": ["churn", "retention", "attrition"],
            "Performance": ["performance", "efficiency"],
            "Risk": ["risk", "exposure"],
        }

        for metric_name, keywords in metric_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    metrics.append(metric_name)
                    break

        return list(set(metrics))

    def extract_scale(self, message: str) -> Optional[str]:
        """Extract scale information from message"""
        patterns = [
            r"(\d+[,\d]*)\s*(?:billion|B)\s+(?:in\s+)?(\w+)",
            r"(\d+[,\d]*)\s*(?:million|M)\s+(\w+)",
            r"(\d+[,\d]*[+]?)\s+(\w+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return f"{match.group(1)} {match.group(2)}"

        return None

    def infer_industry(self, company: str) -> str:
        """Infer industry from company name"""
        company_lower = company.lower()

        industry_indicators = {
            "Technology": ["tech", "software", "salesforce", "microsoft", "adobe"],
            "Retail": ["walmart", "target", "retail", "store"],
            "Healthcare": ["clinic", "hospital", "health", "medical"],
            "Financial": ["bank", "capital", "financial", "chase"],
        }

        for industry, indicators in industry_indicators.items():
            for indicator in indicators:
                if indicator in company_lower:
                    return industry

        return "Enterprise"


def process_smart_message(message: str) -> str:
    """Process message with intelligent context extraction"""

    extractor = SmartContextExtractor()
    extracted = extractor.extract_context(message)

    # Update session state with extracted context
    context = st.session_state.demo_context

    for key, value in extracted.items():
        if value:
            if isinstance(value, list):
                context[key] = list(set(context.get(key, []) + value))
            else:
                context[key] = value

    # Determine conversation phase
    has_company = bool(context.get("company_name"))
    has_department = bool(context.get("department"))
    has_pain_points = bool(context.get("pain_points"))

    # Generate intelligent response
    if has_company and has_department and has_pain_points:
        company = context["company_name"]
        dept = context["department"]
        pain_points = context["pain_points"]

        response = f"""Excellent! I understand you're creating a demo for **{company}'s {dept}** team.

Based on the challenges you mentioned:
"""
        for pain_point in pain_points[:3]:
            response += f"- {pain_point}\n"

        if context.get("scale"):
            response += f"\n**Scale:** {context['scale']}\n"

        if context.get("metrics"):
            response += f"\n**Key Metrics:** {', '.join(context['metrics'])}\n"

        response += """
I'll create a custom demo module with:
- Industry-specific datasets tailored to their business
- ES|QL queries that solve their specific problems
- A demo guide and talk track

**Ready to build?** Type **"Generate demo"** to proceed!
"""
        st.session_state.conversation_phase = "ready_to_generate"
        return response

    elif has_company and has_department:
        return f"""Great! I see you're working with **{context['company_name']}'s {context['department']}** team.

To create the most impactful demo, could you tell me more about their specific challenges and pain points?"""

    elif has_company:
        return f"""Excellent, **{context['company_name']}** is a great opportunity!

Which specific team or department will be using Agent Builder?"""

    else:
        return """I'd love to help you create a compelling Agent Builder demo!

Could you provide:
1. **Company name** and industry?
2. **Which team** will use it?
3. **Main challenges** they're facing?

Feel free to paste in meeting notes - I'll extract the details!"""


def display_context_summary():
    """Display extracted context in sidebar"""
    if any(st.session_state.demo_context.values()):
        st.markdown("### 📋 Demo Context")

        context = st.session_state.demo_context

        if context.get("company_name"):
            st.markdown(f"🏢 **Company:** {context['company_name']}")

        if context.get("industry"):
            st.markdown(f"🏭 **Industry:** {context['industry']}")

        if context.get("department"):
            st.markdown(f"👥 **Department:** {context['department']}")

        if context.get("scale"):
            st.markdown(f"📊 **Scale:** {context['scale']}")

        if context.get("pain_points"):
            st.markdown("**🎯 Pain Points:**")
            for point in context["pain_points"]:
                st.markdown(f"  • {point}")

        if context.get("metrics"):
            st.markdown(f"**📈 Metrics:** {', '.join(context['metrics'])}")

        # Progress indicator
        filled_fields = sum(1 for k, v in context.items() if v)
        total_fields = 7
        progress = filled_fields / total_fields

        st.progress(progress, text=f"Context: {int(progress*100)}%")

        if progress >= 0.5:
            st.success("✅ Ready to generate!")


def render_create_demo_view():
    """Render the demo creation interface"""
    st.title("🚀 Elastic Agent Builder Demo Generator")
    st.markdown("*Create custom demos with LLM-generated modules*")

    # Display messages
    if not st.session_state.messages:
        st.info("""
        👋 **Welcome!** Paste your customer description and I'll extract context automatically.

        **Example:** *"Salesforce's Customer Success team wants to prevent churn in their 5,000+
        enterprise accounts worth $10B in ARR..."*
        """)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Process programmatically added messages
    if st.session_state.needs_processing and st.session_state.messages:
        last_message = st.session_state.messages[-1]
        if last_message["role"] == "user":
            st.session_state.needs_processing = False

            with st.chat_message("assistant"):
                with st.spinner("Analyzing context..."):
                    response = process_smart_message(last_message["content"])
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()

    # Chat input
    if prompt := st.chat_input("Paste your customer description or type your response..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Check if this is a generate command
        if "generate demo" in prompt.lower() and st.session_state.conversation_phase == "ready_to_generate":
            with st.chat_message("assistant"):
                with st.spinner("🚀 Generating custom demo module..."):
                    try:
                        # Create config from context
                        context = st.session_state.demo_context
                        config = {
                            "company_name": context.get("company_name", "Demo Company"),
                            "department": context.get("department", "Operations"),
                            "industry": context.get("industry", "Enterprise"),
                            "pain_points": context.get("pain_points", []),
                            "use_cases": context.get("use_cases", []),
                            "scale": context.get("scale", "10000 records"),
                            "metrics": context.get("metrics", [])
                        }

                        # Create progress placeholder
                        progress_placeholder = st.empty()

                        def update_progress(progress: float, message: str):
                            progress_placeholder.progress(progress, text=message)

                        # Generate demo using modular orchestrator
                        orchestrator = ModularDemoOrchestrator()
                        results = orchestrator.generate_new_demo(config, update_progress)

                        st.session_state.current_demo_module = results['module_name']

                        st.balloons()
                        st.success(f"✅ Demo module created: **{results['module_name']}**")

                        response = f"""Your custom demo module is ready! 🎉

**Module:** `{results['module_name']}`

**Generated:**
- ✅ Custom data generator ({len(results['datasets'])} datasets)
- ✅ ES|QL queries ({len(results['queries'])} queries)
- ✅ Demo guide and talk track

**Next Steps:**
1. Click "Browse Demos" in the sidebar to view all details
2. Download the demo guide and queries
3. The module is saved in `demos/{results['module_name']}/` for customization

You can now refine the generated modules or start a new demo!"""

                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})

                    except Exception as e:
                        error_msg = f"Error generating demo: {str(e)}"
                        st.error(error_msg)
                        logger.error(f"Demo generation failed: {e}", exc_info=True)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

        else:
            # Normal conversation
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    response = process_smart_message(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})


def render_browse_demos_view():
    """Render the demo browsing interface"""
    st.title("📚 Demo Modules Library")
    st.markdown("*Browse and manage generated demo modules*")

    # List all demos
    manager = DemoModuleManager()
    demos = manager.list_modules()

    if not demos:
        st.info("No demo modules yet. Create your first demo!")
        return

    st.markdown(f"### {len(demos)} Demo Modules")

    for demo in demos:
        with st.expander(f"🎯 {demo['name']}", expanded=False):
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**Customer:** {demo.get('customer', 'N/A')}")
                st.markdown(f"**Department:** {demo.get('department', 'N/A')}")
                st.markdown(f"**Created:** {demo.get('created_at', 'N/A')}")
                st.markdown(f"**Path:** `{demo['path']}`")

            with col2:
                if st.button("🔍 View Details", key=f"view_{demo['name']}"):
                    st.session_state.current_demo_module = demo['name']

                if st.button("🗑️ Delete", key=f"delete_{demo['name']}"):
                    if manager.delete_module(demo['name']):
                        st.success(f"Deleted {demo['name']}")
                        st.rerun()

    # Show details if a module is selected
    if st.session_state.current_demo_module:
        st.markdown("---")
        st.markdown(f"## 📊 Module: {st.session_state.current_demo_module}")

        loader = manager.get_module(st.session_state.current_demo_module)

        if loader:
            tabs = st.tabs(["📋 Config", "🗂️ Data", "🔍 Queries", "📝 Guide"])

            with tabs[0]:
                st.json(loader.config)

            with tabs[1]:
                try:
                    data_gen = loader.load_data_generator()
                    datasets = data_gen.generate_datasets()

                    for name, df in datasets.items():
                        st.markdown(f"### {name}")
                        st.dataframe(df.head(10))
                        st.caption(f"Total rows: {len(df)}")
                except Exception as e:
                    st.error(f"Error loading data: {e}")

            with tabs[2]:
                try:
                    data_gen = loader.load_data_generator()
                    datasets = data_gen.generate_datasets()
                    query_gen = loader.load_query_generator(datasets)
                    queries = query_gen.generate_queries()

                    for i, query in enumerate(queries, 1):
                        st.markdown(f"### Query {i}: {query.get('name', 'Query')}")
                        st.code(query.get('esql', ''), language='sql')
                        st.caption(query.get('description', ''))
                except Exception as e:
                    st.error(f"Error loading queries: {e}")

            with tabs[3]:
                try:
                    data_gen = loader.load_data_generator()
                    datasets = data_gen.generate_datasets()
                    query_gen = loader.load_query_generator(datasets)
                    queries = query_gen.generate_queries()
                    guide_gen = loader.load_demo_guide(datasets, queries)
                    guide = guide_gen.generate_guide()

                    st.markdown(guide)
                except Exception as e:
                    st.error(f"Error loading guide: {e}")


def main():
    """Main application entry point"""

    # Sidebar
    with st.sidebar:
        st.markdown("## 🎛️ Controls")

        # View mode selector
        view_mode = st.radio(
            "Mode",
            ["Create Demo", "Browse Demos"],
            key="view_selector",
            horizontal=True
        )

        if view_mode == "Create Demo":
            st.session_state.view_mode = "create"
        else:
            st.session_state.view_mode = "browse"

        st.markdown("---")

        if st.session_state.view_mode == "create":
            display_context_summary()

            st.markdown("---")

            if st.button("🔄 Start Fresh", use_container_width=True):
                st.session_state.messages = []
                st.session_state.demo_context = {
                    "company_name": None,
                    "department": None,
                    "industry": None,
                    "pain_points": [],
                    "use_cases": [],
                    "metrics": [],
                    "scale": None,
                }
                st.session_state.conversation_phase = "initial"
                st.rerun()

            if st.button("📋 Use Test Prompt", use_container_width=True):
                test_prompt = """Salesforce's Customer Success team wants to prevent churn in their enterprise accounts. They manage 5,000+ accounts worth $10B in ARR but can only do quarterly business reviews. They need real-time health scores, usage analytics, and early warning signals. The CCO wants agents that can answer 'Which accounts are at risk this month and why?'"""
                st.session_state.messages.append({"role": "user", "content": test_prompt})
                st.session_state.needs_processing = True
                st.rerun()

            st.markdown("---")
            st.markdown("### ✨ Special Features")

            if st.button("💡 Generate A-ha Moment", use_container_width=True, disabled=True):
                pass

            st.caption("🚧 **Coming Soon:** Generate powerful 'A-ha moments' that wow customers!")

    # Main content area
    if st.session_state.view_mode == "create":
        render_create_demo_view()
    else:
        render_browse_demos_view()


if __name__ == "__main__":
    main()
