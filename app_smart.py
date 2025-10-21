"""
Elastic Agent Builder Demo Generator - Smart Version
Enhanced with better context extraction and response generation
"""

import streamlit as st
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
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
    page_title="Elastic Demo Builder - Smart",
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
        "data_types": [],
        "metrics": [],
        "scale": None,
        "urgency": None,
        "audience": None
    }

if "conversation_phase" not in st.session_state:
    st.session_state.conversation_phase = "initial"


class SmartContextExtractor:
    """Intelligent context extraction from user messages"""

    def __init__(self):
        # Expanded patterns for better extraction
        self.company_patterns = [
            r"(?:for|with|at|meeting with)\s+([A-Z][A-Za-z0-9\s&'.-]+?)(?:'s|'s|team|division|department|\s+wants|\s+needs|\s+is|\s+has|,|\.|\s+[a-z])",
            r"^([A-Z][A-Za-z0-9\s&'.-]+?)(?:'s|'s|team|division|department|\s+wants|\s+needs)",
            r"(?:customer|client|prospect)\s+is\s+([A-Z][A-Za-z0-9\s&'.-]+)",
        ]

        self.department_keywords = {
            "customer success": ["customer success", "cs team", "account management", "customer experience"],
            "sales": ["sales", "revenue", "account executive", "sales ops", "sales operations"],
            "marketing": ["marketing", "campaign", "brand", "demand gen", "marketing ops"],
            "engineering": ["engineering", "development", "devops", "platform", "infrastructure"],
            "operations": ["operations", "ops team", "supply chain", "logistics", "operational"],
            "finance": ["finance", "accounting", "treasury", "audit", "compliance", "risk"],
            "it": ["it ", "information technology", "it department", "technology team"],
            "hr": ["hr", "human resources", "people team", "talent", "recruiting"],
            "analytics": ["analytics", "data team", "business intelligence", "bi team", "insights"],
            "support": ["support", "help desk", "service desk", "customer service"],
            "clinical": ["clinical", "medical", "patient care", "healthcare"],
        }

        self.pain_point_patterns = {
            "visibility": ["can't see", "no visibility", "lack of visibility", "can't get.*visibility", "blind to"],
            "performance": ["slow", "performance", "takes hours", "takes too long", "inefficient"],
            "integration": ["don't talk", "different systems", "silos", "disconnected", "fragmented"],
            "scale": ["billion", "million", "thousands", "hundreds of", "massive", "growing"],
            "real_time": ["real-time", "real time", "instant", "immediate", "live", "streaming"],
            "prediction": ["predict", "forecast", "anticipate", "prevent", "proactive"],
            "cost": ["expensive", "cost", "budget", "spending", "waste", "loss", "lost"],
            "manual": ["manual", "by hand", "spreadsheet", "repetitive", "tedious"],
            "compliance": ["compliance", "regulatory", "audit", "governance", "sox", "gdpr", "sec"],
            "accuracy": ["false positive", "inaccurate", "errors", "mistakes", "wrong"],
        }

    def extract_context(self, message: str) -> Dict:
        """Extract all possible context from the message"""
        context = {}

        # Extract company
        company = self.extract_company(message)
        if company:
            context["company_name"] = company
            context["industry"] = self.infer_industry(company)

        # Extract department
        department = self.extract_department(message)
        if department:
            context["department"] = department

        # Extract pain points
        pain_points = self.extract_pain_points(message)
        if pain_points:
            context["pain_points"] = pain_points

        # Extract metrics
        metrics = self.extract_metrics(message)
        if metrics:
            context["metrics"] = metrics

        # Extract scale
        scale = self.extract_scale(message)
        if scale:
            context["scale"] = scale

        # Extract audience
        audience = self.extract_audience(message)
        if audience:
            context["audience"] = audience

        # Extract urgency
        urgency = self.extract_urgency(message)
        if urgency:
            context["urgency"] = urgency

        return context

    def extract_company(self, message: str) -> Optional[str]:
        """Extract company name from message"""
        for pattern in self.company_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                # Clean up common suffixes
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
                        pain_points.append("Performance and efficiency issues")
                    elif category == "integration":
                        pain_points.append("System integration challenges")
                    elif category == "scale":
                        pain_points.append("Scaling challenges")
                    elif category == "real_time":
                        pain_points.append("Need for real-time insights")
                    elif category == "prediction":
                        pain_points.append("Lack of predictive capabilities")
                    elif category == "cost":
                        pain_points.append("High costs and inefficiencies")
                    elif category == "manual":
                        pain_points.append("Manual and repetitive processes")
                    elif category == "compliance":
                        pain_points.append("Compliance and regulatory requirements")
                    elif category == "accuracy":
                        pain_points.append("Data accuracy and quality issues")
                    break

        return list(set(pain_points))  # Remove duplicates

    def extract_metrics(self, message: str) -> List[str]:
        """Extract mentioned metrics from message"""
        metrics = []
        message_lower = message.lower()

        metric_keywords = {
            "ROI": ["roi", "return on investment"],
            "Revenue": ["revenue", "arr", "mrr"],
            "Churn": ["churn", "retention", "attrition"],
            "Performance": ["performance", "efficiency", "speed"],
            "Utilization": ["utilization", "usage", "adoption"],
            "Satisfaction": ["satisfaction", "nps", "csat"],
            "Risk": ["risk", "exposure", "vulnerability"],
            "Compliance": ["compliance", "violations", "audit"],
        }

        for metric_name, keywords in metric_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    metrics.append(metric_name)
                    break

        return list(set(metrics))

    def extract_scale(self, message: str) -> Optional[str]:
        """Extract scale information from message"""
        # Look for numbers with context
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

    def extract_audience(self, message: str) -> Optional[str]:
        """Extract audience information from message"""
        audience_patterns = [
            r"(?:meeting with|presenting to|audience is)\s+(?:the\s+)?([A-Z][A-Za-z\s,]+)",
            r"(VP|CEO|CFO|CTO|CCO|Director|Manager|team lead|analyst)[^.]*(?:will be|is|are)",
        ]

        for pattern in audience_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    def extract_urgency(self, message: str) -> Optional[str]:
        """Extract urgency/timeline from message"""
        urgency_patterns = [
            r"next\s+(week|monday|tuesday|wednesday|thursday|friday)",
            r"(tomorrow|today|this week|urgent|asap)",
            r"meeting\s+(?:is\s+)?(?:on\s+)?([A-Za-z]+\s+\d+|\d+/\d+)",
        ]

        for pattern in urgency_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    def infer_industry(self, company: str) -> str:
        """Infer industry from company name"""
        company_lower = company.lower()

        industry_indicators = {
            "Technology": ["tech", "software", "cloud", "salesforce", "microsoft", "google", "oracle", "adobe", "sap"],
            "Retail": ["walmart", "target", "costco", "home depot", "amazon", "retail", "store"],
            "Healthcare": ["clinic", "hospital", "health", "medical", "pharma", "kaiser", "mayo"],
            "Financial": ["bank", "capital", "financial", "morgan", "chase", "goldman", "citi", "wells"],
            "Manufacturing": ["motors", "electric", "ford", "boeing", "general", "industries"],
        }

        for industry, indicators in industry_indicators.items():
            for indicator in indicators:
                if indicator in company_lower:
                    return industry

        return "Enterprise"


def process_smart_message(message: str) -> str:
    """Process message with intelligent context extraction"""

    # Initialize extractor
    extractor = SmartContextExtractor()

    # Extract all context from the message
    extracted = extractor.extract_context(message)

    # Update session state with extracted context
    context = st.session_state.demo_context

    for key, value in extracted.items():
        if value:
            if isinstance(value, list):
                context[key] = list(set(context.get(key, []) + value))
            else:
                context[key] = value

    # Determine conversation phase based on what we have
    has_company = bool(context.get("company_name"))
    has_department = bool(context.get("department"))
    has_pain_points = bool(context.get("pain_points"))

    # Generate intelligent response based on extracted context
    if has_company and has_department and has_pain_points:
        # We have enough context to suggest use cases
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

        if context.get("urgency"):
            response += f"\n**Timeline:** {context['urgency']}\n"

        response += """
Here are the most relevant Agent Builder use cases for this scenario:

**1. 🎯 Intelligent Account Health Monitoring**
- Real-time health scores calculated from usage patterns
- Automated alerts for at-risk accounts
- Natural language queries about account status

**2. 📊 Predictive Churn Analytics**
- Early warning signals based on behavior patterns
- Cohort analysis to identify risk factors
- Proactive intervention recommendations

**3. 🤖 Customer Success Intelligence Agent**
- Answers questions like "Which accounts need attention this week?"
- Provides instant insights on usage trends
- Suggests personalized engagement strategies

**Ready to build this demo?** I'll create:
- Account and usage datasets (5,000+ accounts as mentioned)
- Health score calculations and churn predictions
- ES|QL queries for all key metrics
- A configured agent that can answer natural language questions

Type **"Generate demo"** to proceed, or let me know if you'd like to adjust the focus!
"""
        st.session_state.conversation_phase = "ready_to_generate"
        return response

    elif has_company and has_department:
        # We have company and department but need more on pain points
        return f"""Great! I see you're working with **{context['company_name']}'s {context['department']}** team.

To create the most impactful demo, could you tell me more about:

1. **Specific challenges** they're facing?
2. **Current pain points** with their existing solution?
3. **What success looks like** for them?

I noticed you mentioned some scale ({context.get('scale', 'large volume')}) - what specific problems does this create for them?"""

    elif has_company:
        # We have company but need department
        return f"""Excellent, **{context['company_name']}** is a great opportunity for Agent Builder!

I can see this is about {context.get('pain_points', ['analytics'])[0] if context.get('pain_points') else 'improving their operations'}.

Which specific team or department will be the primary users?
- Is this for a technical team (Engineering, Data, IT)?
- Or business users (Sales, Marketing, Operations)?
- Or executives needing strategic insights?

Understanding the audience will help me tailor the complexity and focus of the demo."""

    else:
        # Need more basic information
        return """I'd love to help you create a compelling Agent Builder demo!

From your message, I can see you have a specific use case in mind. Could you provide a bit more detail about:

1. **The company name** and their industry?
2. **Which team** will be using Agent Builder?
3. **The main challenge** they're trying to solve?

Feel free to paste in meeting notes or requirements - I'll extract all the relevant details!"""


def display_context_summary():
    """Display extracted context in sidebar"""
    if any(st.session_state.demo_context.values()):
        with st.sidebar:
            st.markdown("### 📋 Extracted Context")

            context = st.session_state.demo_context

            # Display with visual badges
            if context.get("company_name"):
                st.markdown(f"🏢 **Company:** {context['company_name']}")

            if context.get("industry"):
                st.markdown(f"🏭 **Industry:** {context['industry']}")

            if context.get("department"):
                st.markdown(f"👥 **Department:** {context['department']}")

            if context.get("scale"):
                st.markdown(f"📊 **Scale:** {context['scale']}")

            if context.get("urgency"):
                st.markdown(f"⏰ **Timeline:** {context['urgency']}")

            if context.get("pain_points"):
                st.markdown("**🎯 Pain Points:**")
                for point in context["pain_points"]:
                    st.markdown(f"  • {point}")

            if context.get("metrics"):
                st.markdown("**📈 Key Metrics:**")
                st.markdown(f"  {', '.join(context['metrics'])}")

            # Progress indicator
            filled_fields = sum(1 for k, v in context.items() if v and k != "use_cases")
            total_fields = 7  # Key fields we want
            progress = filled_fields / total_fields

            st.progress(progress, text=f"Context: {int(progress*100)}% complete")

            if progress >= 0.5:
                st.success("✅ Sufficient context to generate demo!")
            else:
                st.info("📝 Gathering more details...")


def main():
    st.title("🚀 Elastic Agent Builder Demo Generator")
    st.markdown("*Smart context extraction for instant demo creation*")

    # Display context in sidebar
    display_context_summary()

    # Main chat interface
    if not st.session_state.messages:
        st.info("""
        👋 **Welcome!** Paste your complete customer description and I'll extract all the context automatically.

        Try this example: *"Salesforce's Customer Success team wants to prevent churn in their enterprise accounts.
        They manage 5,000+ accounts worth $10B in ARR but can only do quarterly business reviews..."*
        """)

    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Paste your customer description or requirements..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate smart response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing context..."):
                response = process_smart_message(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

                # If ready to generate
                if "Generate demo" in prompt and st.session_state.conversation_phase == "ready_to_generate":
                    with st.spinner("🚀 Generating your demo..."):
                        try:
                            # Import orchestrator
                            from src.services.demo_orchestrator import DemoOrchestrator
                            from src.services.llm_service import ConversationContext

                            # Create context from session state
                            demo_context = st.session_state.demo_context
                            conv_context = ConversationContext(
                                company_name=demo_context.get("company_name"),
                                department=demo_context.get("department"),
                                industry=demo_context.get("industry"),
                                pain_points=demo_context.get("pain_points", []),
                                use_cases=demo_context.get("use_cases", []),
                                scale=demo_context.get("scale"),
                                metrics=demo_context.get("metrics", []),
                                conversation_phase="ready"
                            )

                            # Create progress placeholder
                            progress_placeholder = st.empty()

                            # Define progress callback
                            def update_progress(progress: float, message: str):
                                progress_placeholder.progress(progress, text=message)

                            # Generate demo
                            orchestrator = DemoOrchestrator()
                            demo_package = orchestrator.generate_demo(
                                conv_context,
                                progress_callback=update_progress
                            )

                            st.balloons()
                            st.success("✅ Demo package created successfully!")

                            # Display download options
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.download_button(
                                    "📝 Demo Guide",
                                    data=demo_package.demo_guide,
                                    file_name=f"demo_guide_{demo_package.demo_id}.md",
                                    mime="text/markdown",
                                    key="download_guide"
                                )

                            with col2:
                                # Export queries to file
                                queries_content = "-- ES|QL Queries for Demo\n\n"
                                for i, query in enumerate(demo_package.queries, 1):
                                    queries_content += f"-- Query {i}: {query.get('name', 'Query')}\n"
                                    queries_content += f"{query.get('esql', '')}\n\n"

                                st.download_button(
                                    "🔍 ES|QL Queries",
                                    data=queries_content,
                                    file_name=f"queries_{demo_package.demo_id}.es",
                                    mime="text/plain",
                                    key="download_queries"
                                )

                            with col3:
                                # Export sample data (first dataset)
                                if demo_package.datasets:
                                    first_dataset = list(demo_package.datasets.values())[0]
                                    csv_data = first_dataset.to_csv(index=False)

                                    st.download_button(
                                        "📊 Sample Data",
                                        data=csv_data,
                                        file_name=f"sample_data_{demo_package.demo_id}.csv",
                                        mime="text/csv",
                                        key="download_data"
                                    )

                            # Show demo statistics
                            with st.expander("📈 Demo Statistics", expanded=True):
                                stats_col1, stats_col2, stats_col3 = st.columns(3)

                                with stats_col1:
                                    st.metric("Datasets Created", len(demo_package.datasets))

                                with stats_col2:
                                    total_records = sum(len(df) for df in demo_package.datasets.values())
                                    st.metric("Total Records", f"{total_records:,}")

                                with stats_col3:
                                    st.metric("Queries Generated", len(demo_package.queries))

                                st.info(f"Demo ID: {demo_package.demo_id}")

                        except Exception as e:
                            st.error(f"Error generating demo: {str(e)}")
                            logger.error(f"Demo generation failed: {e}")

    # Quick actions in sidebar
    with st.sidebar:
        st.markdown("---")
        if st.button("🔄 Start Fresh", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        if st.button("📋 Use Test Prompt", use_container_width=True):
            test_prompt = """Salesforce's Customer Success team wants to prevent churn in their enterprise accounts.
            They manage 5,000+ accounts worth $10B in ARR but can only do quarterly business reviews.
            They need real-time health scores, usage analytics, and early warning signals.
            The CCO wants agents that can answer 'Which accounts are at risk this month and why?'"""
            st.session_state.messages.append({"role": "user", "content": test_prompt})
            st.rerun()

        st.markdown("---")
        st.markdown("### ✨ Special Features")

        # A-ha moment button (placeholder)
        if st.button("💡 Generate A-ha Moment", use_container_width=True, disabled=True):
            pass

        st.caption("🚧 **Coming Soon:** Generate a powerful 'A-ha moment' that will wow your customer by showing exactly how Agent Builder solves their biggest pain point!")


if __name__ == "__main__":
    main()