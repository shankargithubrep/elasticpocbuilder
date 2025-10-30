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


@st.cache_data(ttl=3600)
def load_demo_datasets(module_name: str):
    """Cache dataset generation for faster loading"""
    manager = DemoModuleManager()
    loader = manager.get_module(module_name)
    if loader:
        data_gen = loader.load_data_generator()
        return data_gen.generate_datasets()
    return {}

@st.cache_data(ttl=3600)
def load_demo_queries(module_name: str):
    """Cache query generation for faster loading"""
    manager = DemoModuleManager()
    loader = manager.get_module(module_name)
    if loader:
        datasets = load_demo_datasets(module_name)
        query_gen = loader.load_query_generator(datasets)
        return query_gen.generate_queries()
    return []

@st.cache_data(ttl=3600)
def load_demo_guide(module_name: str):
    """Cache guide generation for faster loading"""
    manager = DemoModuleManager()
    loader = manager.get_module(module_name)
    if loader:
        datasets = load_demo_datasets(module_name)
        queries = load_demo_queries(module_name)
        guide_gen = loader.load_demo_guide(datasets, queries)
        return guide_gen.generate_guide()
    return ""

def render_browse_demos_view():
    """Render the demo browsing interface - demo details only (list is in sidebar)"""
    # Show details if a module is selected
    if st.session_state.current_demo_module:
        st.title(f"📊 {st.session_state.current_demo_module}")

        manager = DemoModuleManager()
        loader = manager.get_module(st.session_state.current_demo_module)

        if loader:
            tabs = st.tabs(["📋 Config", "🗂️ Data", "🔍 Queries", "📝 Guide"])

            with tabs[0]:
                st.markdown("### Generate Demo Assets")
                st.warning("""
                ⚠️ **Generation Time: 5-20 minutes**

                Large datasets (10,000+ rows) can take significant time to generate.
                The page will appear frozen but is actively processing. Please be patient!

                **Progress:**
                - Data generation: 80-90% of time (slowest)
                - Query generation: 5-10% of time
                - Guide generation: 5-10% of time
                """)

                if st.button("🚀 Generate Assets", use_container_width=True):
                    with st.spinner("Generating demo assets..."):
                        try:
                            # Force regeneration by clearing cache and loading
                            load_demo_datasets.clear()
                            load_demo_queries.clear()
                            load_demo_guide.clear()

                            # Generate all assets
                            datasets = load_demo_datasets(st.session_state.current_demo_module)
                            queries = load_demo_queries(st.session_state.current_demo_module)
                            guide = load_demo_guide(st.session_state.current_demo_module)

                            # Mark assets as generated
                            st.session_state.assets_generated = True

                            st.success(f"✅ Generated {len(datasets)} datasets, {len(queries)} queries, and demo guide!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error generating assets: {e}")
                            import traceback
                            st.code(traceback.format_exc())

                st.divider()
                st.markdown("### Demo Configuration")
                st.json(loader.config)

            with tabs[1]:
                # Only load if assets have been generated
                if st.session_state.get("assets_generated", False):
                    try:
                        datasets = load_demo_datasets(st.session_state.current_demo_module)

                        # Get semantic fields specification from data generator
                        manager = DemoModuleManager()
                        loader = manager.get_module(st.session_state.current_demo_module)
                        data_gen = loader.load_data_generator()

                        # Try to get semantic fields (may not exist in older modules)
                        try:
                            semantic_fields_spec = data_gen.get_semantic_fields()
                        except AttributeError:
                            semantic_fields_spec = {}

                        if datasets:
                            for name, df in datasets.items():
                                st.markdown(f"### {name}")

                                # Action buttons
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    # Download CSV
                                    csv = df.to_csv(index=False)
                                    st.download_button(
                                        "📥 CSV",
                                        csv,
                                        f"{name}.csv",
                                        "text/csv",
                                        key=f"download_{name}",
                                        use_container_width=True
                                    )

                                with col2:
                                    # View data
                                    if st.button("👁️ View", key=f"view_{name}", use_container_width=True):
                                        st.session_state[f"show_data_{name}"] = not st.session_state.get(f"show_data_{name}", False)

                                with col3:
                                    # Index in Elasticsearch button
                                    if st.button("📤 Index", key=f"index_{name}", use_container_width=True):
                                        from src.services.elasticsearch_indexer import ElasticsearchIndexer

                                        # Get semantic fields for this dataset
                                        semantic_fields = semantic_fields_spec.get(name, [])

                                        # Show progress and stop button
                                        progress_bar = st.progress(0)
                                        status_text = st.empty()
                                        stop_button_container = st.empty()

                                        # Track stop request in session state
                                        stop_key = f"stop_indexing_{name}"
                                        st.session_state[stop_key] = False

                                        def progress_callback(pct, msg):
                                            progress_bar.progress(pct)
                                            status_text.text(msg)

                                        def stop_callback():
                                            return st.session_state.get(stop_key, False)

                                        # Show stop button
                                        if stop_button_container.button("⏸️ Stop Indexing", key=f"stop_{name}"):
                                            st.session_state[stop_key] = True

                                        try:
                                            # Index the dataset
                                            indexer = ElasticsearchIndexer()
                                            result = indexer.index_dataset(
                                                df,
                                                name,
                                                semantic_fields=semantic_fields,
                                                progress_callback=progress_callback,
                                                stop_callback=stop_callback
                                            )

                                            # Clear stop button
                                            stop_button_container.empty()

                                            if result.success:
                                                was_stopped = result.documents_indexed < len(df)
                                                if was_stopped:
                                                    st.warning(
                                                        f"⏸️ Indexing stopped by user\n\n"
                                                        f"**Indexed:** {result.documents_indexed:,} / {len(df):,} documents\n\n"
                                                        f"**Index:** {result.index_name} ({result.index_type})\n\n"
                                                        f"**Semantic fields:** {', '.join(result.semantic_fields) if result.semantic_fields else 'None'}\n\n"
                                                        f"**Duration:** {result.duration_seconds}s"
                                                    )
                                                else:
                                                    st.success(
                                                        f"✅ Indexed {result.documents_indexed:,} documents\n\n"
                                                        f"**Index:** {result.index_name} ({result.index_type})\n\n"
                                                        f"**Semantic fields:** {', '.join(result.semantic_fields) if result.semantic_fields else 'None'}\n\n"
                                                        f"**Duration:** {result.duration_seconds}s"
                                                    )
                                            else:
                                                st.error(f"❌ Indexing failed:\n{chr(10).join(result.errors)}")

                                        except Exception as e:
                                            stop_button_container.empty()
                                            st.error(f"❌ Indexing error: {e}")
                                            import traceback
                                            st.code(traceback.format_exc())

                                # Show semantic fields info if specified
                                if name in semantic_fields_spec and semantic_fields_spec[name]:
                                    st.info(f"🧠 **Semantic fields:** {', '.join(semantic_fields_spec[name])}")

                                # Show data if view button was clicked
                                if st.session_state.get(f"show_data_{name}", False):
                                    st.dataframe(df.head(100), use_container_width=True)
                                    st.caption(f"Showing first 100 of {len(df)} rows")
                                else:
                                    st.caption(f"Total rows: {len(df)} | Columns: {len(df.columns)}")

                                st.divider()
                        else:
                            st.info("No datasets found. Try regenerating assets from the Config tab.")
                    except Exception as e:
                        st.error(f"Error loading data: {e}")
                        st.info("Try clicking 'Generate Assets' in the Config tab.")
                else:
                    st.info("📋 Click 'Generate Assets' in the Config tab to view datasets")

            with tabs[2]:
                # Only load if assets have been generated
                if st.session_state.get("assets_generated", False):
                    try:
                        queries = load_demo_queries(st.session_state.current_demo_module)
                        if queries:
                            for i, query in enumerate(queries, 1):
                                query_name = query.get('name', f'Query {i}')
                                st.markdown(f"### {i}. {query_name}")

                                # Description
                                if query.get('description'):
                                    st.caption(query['description'])

                                # Query code with copy button
                                query_text = query.get('esql', '')
                                st.code(query_text, language='sql')

                                # Action buttons
                                col1, col2 = st.columns([1, 3])

                                with col1:
                                    # Test query button
                                    if st.button("▶️ Test Query", key=f"test_query_{i}", use_container_width=True):
                                        from src.services.elasticsearch_indexer import ElasticsearchIndexer

                                        with st.spinner(f"Executing {query_name}..."):
                                            try:
                                                indexer = ElasticsearchIndexer()
                                                success, result, error = indexer.execute_esql(query_text)

                                                if success:
                                                    st.success(f"✅ Query executed successfully!")

                                                    # Display results
                                                    if result:
                                                        # Try to convert to DataFrame for better display
                                                        try:
                                                            if 'columns' in result and 'values' in result:
                                                                # ES|QL response format
                                                                columns = [col['name'] for col in result['columns']]
                                                                values = result['values']
                                                                result_df = pd.DataFrame(values, columns=columns)
                                                                st.dataframe(result_df, use_container_width=True)
                                                                st.caption(f"Returned {len(result_df)} rows")
                                                            else:
                                                                # Fallback to JSON display
                                                                st.json(result)
                                                        except Exception as display_error:
                                                            # If conversion fails, show raw JSON
                                                            st.json(result)
                                                else:
                                                    st.error(f"❌ Query failed:\n\n{error}")

                                            except Exception as e:
                                                st.error(f"❌ Error executing query: {e}")
                                                import traceback
                                                with st.expander("Show traceback"):
                                                    st.code(traceback.format_exc())

                                with col2:
                                    # Copy to clipboard button (visual only, actual copy handled by st.code)
                                    st.caption(f"💾 Use the copy button in the code block above")

                                st.divider()
                        else:
                            st.info("No queries found. Try regenerating assets from the Config tab.")
                    except Exception as e:
                        st.error(f"Error loading queries: {e}")
                        st.info("Try clicking 'Generate Assets' in the Config tab.")
                else:
                    st.info("📋 Click 'Generate Assets' in the Config tab to view queries")

            with tabs[3]:
                # Only load if assets have been generated
                if st.session_state.get("assets_generated", False):
                    try:
                        guide = load_demo_guide(st.session_state.current_demo_module)
                        if guide:
                            st.markdown(guide)
                        else:
                            st.info("No demo guide found. Try regenerating assets from the Config tab.")
                    except Exception as e:
                        st.error(f"Error loading guide: {e}")
                        st.info("Try clicking 'Generate Assets' in the Config tab.")
                else:
                    st.info("📋 Click 'Generate Assets' in the Config tab to view the demo guide")
    else:
        st.info("👈 Select a demo from the sidebar to view details")


def main():
    """Main application entry point"""

    # Sidebar
    with st.sidebar:
        # Demo Builder header
        st.markdown("### Demo Builder")

        # Prominent mode toggle buttons with custom styling
        col1, col2 = st.columns(2)

        with col1:
            create_selected = st.session_state.view_mode == "create"
            if st.button(
                "Create",
                use_container_width=True,
                type="primary" if create_selected else "secondary",
                key="create_mode_btn"
            ):
                st.session_state.view_mode = "create"
                st.rerun()

        with col2:
            browse_selected = st.session_state.view_mode == "browse"
            if st.button(
                "Browse",
                use_container_width=True,
                type="primary" if browse_selected else "secondary",
                key="browse_mode_btn"
            ):
                st.session_state.view_mode = "browse"
                st.rerun()

        if st.session_state.view_mode == "create":
            display_context_summary()

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
            st.markdown("### 🔗 Elasticsearch")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Test Connection", use_container_width=True):
                    from src.services.elasticsearch_indexer import ElasticsearchIndexer
                    try:
                        indexer = ElasticsearchIndexer()
                        success, message = indexer.verify_connection()

                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {e}")

            with col2:
                if st.button("Check ELSER", use_container_width=True):
                    from src.services.elasticsearch_indexer import ElasticsearchIndexer
                    try:
                        indexer = ElasticsearchIndexer()
                        is_ready, message = indexer.check_elser_deployment()

                        if is_ready:
                            st.success(f"✅ {message}")
                        else:
                            st.warning(f"⚠️ {message}")

                            # Offer to deploy
                            if "not deployed" in message.lower():
                                if st.button("Deploy ELSER", use_container_width=True):
                                    with st.spinner("Deploying ELSER..."):
                                        deploy_success, deploy_msg = indexer.deploy_elser()
                                        if deploy_success:
                                            st.success(f"✅ {deploy_msg}")
                                        else:
                                            st.error(f"❌ {deploy_msg}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

            st.markdown("---")
            st.markdown("### ✨ Special Features")

            if st.button("💡 Generate A-ha Moment", use_container_width=True, disabled=True):
                pass

            st.caption("🚧 **Coming Soon:** Generate powerful 'A-ha moments' that wow customers!")

        else:  # Browse mode
            st.markdown("### 📚 Demo Modules")

            manager = DemoModuleManager()
            demos = manager.list_modules()

            if not demos:
                st.info("No demos yet. Switch to Create mode to make one!")
            else:
                # Show count
                st.caption(f"{len(demos)} modules")

                # List demos as clickable buttons
                for demo in demos:
                    # Make button show selected state
                    is_selected = st.session_state.current_demo_module == demo['name']
                    button_type = "primary" if is_selected else "secondary"

                    if st.button(
                        f"{demo.get('customer', 'Unknown')} - {demo.get('department', 'N/A')}",
                        key=f"select_{demo['name']}",
                        use_container_width=True,
                        type=button_type
                    ):
                        # Only rerun if selection changed
                        if st.session_state.current_demo_module != demo['name']:
                            st.session_state.current_demo_module = demo['name']
                            st.rerun()

    # Main content area
    if st.session_state.view_mode == "create":
        render_create_demo_view()
    else:
        render_browse_demos_view()


if __name__ == "__main__":
    main()
