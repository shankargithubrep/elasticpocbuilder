"""
Progress Header Bar component for Browse mode.

Displays visual progress tracking:
Progress: [████░░░░] 50% | Data ✓ | Queries 3/8 | Tools 0/4 | Agent ✗ | [Reset]
"""

import streamlit as st
import logging
from typing import Optional

from .service import get_progress_service

logger = logging.getLogger(__name__)


# CSS for progress header styling
PROGRESS_HEADER_CSS = """
<style>
.progress-header {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}

.progress-bar-container {
    flex: 0 0 150px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.progress-bar-bg {
    flex: 1;
    height: 8px;
    background: #e0e0e0;
    border-radius: 4px;
    overflow: hidden;
}

.progress-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #0077CC 0%, #00a3cc 100%);
    border-radius: 4px;
    transition: width 0.3s ease;
}

.progress-percentage {
    font-weight: 600;
    color: #333;
    min-width: 40px;
}

.progress-item {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 13px;
}

.progress-item-done {
    background: #d4edda;
    color: #155724;
}

.progress-item-partial {
    background: #fff3cd;
    color: #856404;
}

.progress-item-pending {
    background: #f8d7da;
    color: #721c24;
}

.progress-divider {
    color: #adb5bd;
    font-weight: 300;
}
</style>
"""


def _get_query_count(module_name: str) -> int:
    """Get total query count using the same loader as the Queries tab.

    Uses load_demo_queries() to ensure consistency with what the Queries tab displays.
    Counts queries from: scripted, parameterized, rag categories.
    """
    try:
        from src.ui.data_loaders import load_demo_queries
        queries = load_demo_queries(module_name)

        # Count from scripted, parameterized, rag categories
        count = 0
        for category in ['scripted', 'parameterized', 'rag']:
            items = queries.get(category, [])
            if isinstance(items, list):
                count += len(items)

        return count
    except Exception as e:
        logger.warning(f"Error loading queries for count: {e}")
        return 0


def _get_tool_count(module_name: str) -> int:
    """Get total tool count (tool candidates = validated queries).

    The denominator for tools is the number of validated queries,
    since only validated queries become tool candidates.
    """
    from pathlib import Path
    import json

    validated_queries_path = Path("demos") / module_name / "validated_queries.json"

    try:
        if validated_queries_path.exists():
            with open(validated_queries_path, 'r') as f:
                data = json.load(f)
                validated = data.get('validated_queries', [])
                return len(validated)
    except Exception:
        pass

    return 0


def _get_dataset_names(module_name: str) -> list:
    """Get dataset names from the module's data_profile.json."""
    from pathlib import Path
    import json

    try:
        data_profile_path = Path("demos") / module_name / "data_profile.json"
        if data_profile_path.exists():
            with open(data_profile_path, 'r') as f:
                data = json.load(f)
                return list(data.get('datasets', {}).keys())
    except Exception:
        pass

    return []


def render_progress_header(module_name: str):
    """
    Render the progress tracking header bar.

    Args:
        module_name: Name of the current demo module
    """
    if not module_name:
        return

    # Inject CSS
    st.markdown(PROGRESS_HEADER_CSS, unsafe_allow_html=True)

    # Get progress service and calculate progress
    try:
        service = get_progress_service(module_name)

        # Auto-sync progress from external services (ES, Agent Builder)
        # This detects data/agents deployed before progress tracking was added
        # Uses cooldown to avoid repeated API calls
        dataset_names = _get_dataset_names(module_name)
        service.auto_sync_progress(dataset_names=dataset_names, timeout_seconds=3.0)

        total_queries = _get_query_count(module_name)
        total_tools = _get_tool_count(module_name)
        progress = service.calculate_progress(total_queries, total_tools)
    except Exception as e:
        logger.error(f"Error calculating progress: {e}")
        return

    # Initialize reset confirmation state
    if "show_reset_confirmation" not in st.session_state:
        st.session_state.show_reset_confirmation = False

    # Render header with columns
    col_progress, col_data, col_queries, col_tools, col_agent, col_reset = st.columns([2, 1, 1.2, 1.2, 1, 0.8])

    with col_progress:
        # Progress bar
        pct = progress["percentage"]
        bar_html = f"""
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-weight: 500; color: #666; font-size: 13px;">Progress</span>
            <div style="flex: 1; height: 8px; background: #e0e0e0; border-radius: 4px; overflow: hidden; min-width: 80px;">
                <div style="height: 100%; width: {pct}%; background: linear-gradient(90deg, #0077CC, #00a3cc); border-radius: 4px;"></div>
            </div>
            <span style="font-weight: 600; color: #333; font-size: 13px;">{pct}%</span>
        </div>
        """
        st.markdown(bar_html, unsafe_allow_html=True)

    with col_data:
        # Data status - tooltip explains data indexing
        data_tooltip = "✓ = All datasets indexed. Shows successful/total datasets attempted."
        d_success = progress["data"].get("datasets_success", 0)
        d_failed = progress["data"].get("datasets_failed", 0)
        d_total = progress["data"].get("datasets_total", 0)

        if progress["data"]["done"]:
            # All datasets indexed successfully
            st.markdown(f'<span title="{data_tooltip}" style="cursor: help;">✅ <strong>Data</strong></span>', unsafe_allow_html=True)
        elif d_failed > 0:
            # Some datasets failed
            st.markdown(f'<span title="{data_tooltip}" style="cursor: help;">❌ <strong>Data</strong> {d_success}/{d_total}</span>', unsafe_allow_html=True)
        elif d_success > 0:
            # Some indexed, none failed (partial progress)
            st.markdown(f'<span title="{data_tooltip}" style="cursor: help;">🔶 <strong>Data</strong> {d_success}/{d_total}</span>', unsafe_allow_html=True)
        else:
            # Nothing indexed yet
            st.markdown(f'<span title="{data_tooltip}" style="cursor: help;">⬜ <strong>Data</strong></span>', unsafe_allow_html=True)

    with col_queries:
        # Queries status - tooltip explains validation
        q_validated = progress["queries"]["validated"]
        q_total = progress["queries"]["total"]
        queries_tooltip = "✓ = At least 1 query validated. Shows validated/total queries. You don't need to validate all queries."
        if q_total == 0:
            st.markdown(f'<span title="{queries_tooltip}" style="cursor: help;">➖ <strong>Queries</strong></span>', unsafe_allow_html=True)
        elif q_validated > 0:
            st.markdown(f'<span title="{queries_tooltip}" style="cursor: help;">✅ <strong>Queries</strong> {q_validated}/{q_total}</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span title="{queries_tooltip}" style="cursor: help;">⬜ <strong>Queries</strong> 0/{q_total}</span>', unsafe_allow_html=True)

    with col_tools:
        # Tools status - tooltip explains deployment
        t_deployed = progress["tools"]["deployed"]
        t_total = progress["tools"]["total"]
        tools_tooltip = "✓ = At least 1 tool deployed. Shows deployed/validated queries (tool candidates)."
        if t_total == 0:
            st.markdown(f'<span title="{tools_tooltip}" style="cursor: help;">➖ <strong>Tools</strong></span>', unsafe_allow_html=True)
        elif t_deployed == t_total and t_total > 0:
            st.markdown(f'<span title="{tools_tooltip}" style="cursor: help;">✅ <strong>Tools</strong> {t_deployed}/{t_total}</span>', unsafe_allow_html=True)
        elif t_deployed > 0:
            st.markdown(f'<span title="{tools_tooltip}" style="cursor: help;">🔶 <strong>Tools</strong> {t_deployed}/{t_total}</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span title="{tools_tooltip}" style="cursor: help;">⬜ <strong>Tools</strong> 0/{t_total}</span>', unsafe_allow_html=True)

    with col_agent:
        # Agent status - tooltip explains agent deployment
        agent_tooltip = "✓ = Agent has been deployed to Agent Builder"
        if progress["agent"]["done"]:
            st.markdown(f'<span title="{agent_tooltip}" style="cursor: help;">✅ <strong>Agent</strong></span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span title="{agent_tooltip}" style="cursor: help;">⬜ <strong>Agent</strong></span>', unsafe_allow_html=True)

    with col_reset:
        # Reset button
        if st.button("🔄", key="progress_reset_btn", help="Reset progress"):
            st.session_state.show_reset_confirmation = True
            st.rerun()

    # Show reset confirmation dialog
    if st.session_state.show_reset_confirmation:
        _render_reset_confirmation(module_name, service)


def _render_reset_confirmation(module_name: str, service):
    """Render reset confirmation dialog."""
    st.warning("⚠️ **Reset Progress?**")
    st.markdown("""
    This will:
    - Mark all queries as unvalidated
    - Mark all tools as not deployed
    - Reset data indexing and agent deployment status

    **Note:** This does NOT delete data from Elasticsearch or remove deployed tools from Agent Builder.
    """)

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("Yes, Reset", type="primary", key="confirm_reset"):
            service.reset_progress()
            st.session_state.show_reset_confirmation = False
            st.success("Progress reset successfully!")
            st.rerun()

    with col2:
        if st.button("Cancel", key="cancel_reset"):
            st.session_state.show_reset_confirmation = False
            st.rerun()
