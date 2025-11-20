"""Helper functions for the Demo Builder UI"""

import streamlit as st
from typing import Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)


def display_context_summary(demo_context: Optional[Dict] = None):
    """Display the extracted context in the sidebar"""
    if demo_context is None:
        demo_context = st.session_state.get('demo_context', {})

    st.markdown("### 📊 Extracted Context")

    # Calculate context completeness
    required_fields = ['company_name', 'department', 'pain_points']
    total_fields = ['company_name', 'department', 'industry', 'pain_points', 'use_cases', 'metrics', 'scale']

    required_filled = sum(1 for field in required_fields if demo_context.get(field))
    total_filled = sum(1 for field in total_fields if demo_context.get(field))

    progress = total_filled / len(total_fields)

    # Company & Department
    col1, col2 = st.columns(2)
    with col1:
        company = demo_context.get('company_name', '')
        st.metric("Company", company or "❓")
    with col2:
        dept = demo_context.get('department', '')
        st.metric("Department", dept or "❓")

    # Industry & Scale
    col3, col4 = st.columns(2)
    with col3:
        industry = demo_context.get('industry', '')
        st.metric("Industry", industry or "❓")
    with col4:
        scale = demo_context.get('scale', '')
        st.metric("Scale", scale or "❓")

    # Pain Points
    pain_points = demo_context.get('pain_points', [])
    if pain_points:
        st.markdown("**🎯 Pain Points:**")
        for pp in pain_points[:3]:
            st.caption(f"• {pp}")
    else:
        st.caption("🎯 Pain Points: *Not yet identified*")

    # Metrics
    metrics = demo_context.get('metrics', [])
    if metrics:
        st.markdown("**📈 Metrics:**")
        for metric in metrics[:3]:
            st.caption(f"• {metric}")
    else:
        st.caption("📈 Metrics: *Not yet identified*")

    # Progress indicator
    st.markdown("---")
    st.progress(progress)
    st.caption(f"Context: {int(progress*100)}% complete")

    total_required = len(required_fields)
    if progress >= 0.8:
        st.success("✅ **Ready to generate!**")
        # Add prominent Generate Demo button
        if st.button("🌋 Generate Demo", type="primary", use_container_width=True):
            st.session_state.trigger_demo_generation = True
            st.rerun()
    elif progress >= 0.66:
        st.info("🟡 Almost there! Add more details to improve the demo.")
    else:
        st.warning(f"⏳ Need {total_required - required_filled} more required field(s)")


def create_demo_config(context: Dict) -> Dict:
    """Create demo configuration from context"""
    return {
        "company_name": context.get("company_name", "Demo Company"),
        "department": context.get("department", "Operations"),
        "industry": context.get("industry", "Enterprise"),
        "pain_points": context.get("pain_points", []),
        "use_cases": context.get("use_cases", []),
        "scale": context.get("scale", "10000 records"),
        "metrics": context.get("metrics", [])
    }


def display_demo_generation_progress(progress_placeholder, status_placeholder, progress: float, message: str):
    """Update progress display during demo generation"""
    progress_placeholder.progress(progress, text=message)
    status_placeholder.info(f"💡 {message}")


def format_demo_results(results: Dict) -> str:
    """Format demo generation results for display"""
    return f"""Your custom demo module is ready! 🎉

**Module:** `{results['module_name']}`

**Generated:**
- ✅ Custom data generator ({len(results.get('datasets', []))} datasets)
- ✅ ES|QL queries ({len(results.get('queries', []))} queries)
- ✅ Demo guide and talk track

**Next steps:**
- Switch to "Browse Demos" to view details
- Run indexing and query execution
- Customize the generated modules if needed
"""


def get_test_prompt() -> str:
    """Get a test prompt for demo generation"""
    return """Salesforce's Customer Success team wants to prevent churn in their enterprise accounts. They manage 5,000+ accounts worth $10B in ARR but can only do quarterly business reviews. They need real-time health scores, usage analytics, and early warning signals. The CCO wants agents that can answer 'Which accounts are at risk this month and why?'"""


def should_generate_demo(prompt: str, conversation_phase: str, demo_context: Dict) -> bool:
    """Determine if a demo should be generated based on user input"""
    generate_triggers = ["generate demo", "generate", "yes", "proceed", "ok", "let's do it", "go ahead"]

    # Check if we have enough context
    has_minimum_context = (
        demo_context.get("company_name") and
        demo_context.get("department") and
        demo_context.get("pain_points")
    )

    return (
        any(trigger in prompt.lower() for trigger in generate_triggers) and
        (conversation_phase == "ready_to_generate" or has_minimum_context) and
        len(prompt.split()) <= 10  # Short affirmative responses
    )