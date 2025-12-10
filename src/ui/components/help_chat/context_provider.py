"""
Context Provider for Help Chat widget.

Gathers current UI state to provide contextual assistance.
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class HelpChatContextProvider:
    """
    Gathers current application context for LLM assistance.

    Provides information about:
    - Current mode (create/browse)
    - Current tab (in browse mode)
    - Selected module and its contents
    - Conversation state (in create mode)
    """

    def get_current_context(self) -> Dict[str, Any]:
        """
        Get comprehensive context about the current UI state.

        Returns:
            Dictionary with context information including:
            - mode: Current view mode ("create" | "browse")
            - tab: Current tab name (if browse mode)
            - module_name: Selected module (if browse mode)
            - module_summary: Brief description of module contents
            - datasets: List of dataset summaries
            - query_count: Number of queries
            - conversation_phase: Current conversation phase (if create mode)
            - demo_context: Extracted demo context (if create mode)
        """
        context = {}

        # Get current mode
        mode = st.session_state.get("view_mode", "create")
        context["mode"] = mode

        if mode == "create":
            context.update(self._get_create_context())
        elif mode == "browse":
            context.update(self._get_browse_context())

        return context

    def _get_create_context(self) -> Dict[str, Any]:
        """Get context specific to Create mode."""
        context = {}

        # Conversation phase
        context["conversation_phase"] = st.session_state.get(
            "conversation_phase", "initial"
        )

        # Extracted demo context
        demo_context = st.session_state.get("demo_context", {})
        if demo_context:
            context["demo_context"] = {
                "company": demo_context.get("company_name"),
                "department": demo_context.get("department"),
                "industry": demo_context.get("industry"),
                "has_pain_points": bool(demo_context.get("pain_points")),
                "has_use_cases": bool(demo_context.get("use_cases")),
                "demo_type": demo_context.get("demo_type"),
            }

        # Generation options
        context["ai_expansion_enabled"] = st.session_state.get(
            "ai_expansion_enabled", False
        )

        return context

    def _get_browse_context(self) -> Dict[str, Any]:
        """Get context specific to Browse mode."""
        context = {}

        # Current module
        module_name = st.session_state.get("current_demo_module")
        if module_name:
            context["module_name"] = module_name
            context.update(self._get_module_context(module_name))

        # Try to detect current tab
        context["tab"] = self._detect_current_tab()

        return context

    def _get_module_context(self, module_name: str) -> Dict[str, Any]:
        """Get context about the currently selected module."""
        context = {}

        try:
            # Get module path
            module_path = Path("demos") / module_name

            # Load config if available
            config_path = module_path / "config.json"
            if config_path.exists():
                import json
                with open(config_path) as f:
                    config = json.load(f)

                context["module_summary"] = self._summarize_config(config)
                context["demo_type"] = config.get("demo_type", "unknown")

            # Get dataset information from session state
            datasets = self._get_datasets_from_session(module_name)
            if datasets:
                context["datasets"] = datasets
                context["dataset_count"] = len(datasets)

            # Get query count from session state
            query_count = self._get_query_count_from_session(module_name)
            if query_count:
                context["query_count"] = query_count

        except Exception as e:
            logger.warning(f"Error getting module context: {e}")

        return context

    def _summarize_config(self, config: Dict[str, Any]) -> str:
        """Create a brief summary of module config."""
        parts = []

        if config.get("company_name"):
            parts.append(f"Company: {config['company_name']}")

        if config.get("department"):
            parts.append(f"Dept: {config['department']}")

        if config.get("industry"):
            parts.append(f"Industry: {config['industry']}")

        if config.get("demo_type"):
            parts.append(f"Type: {config['demo_type']}")

        return " | ".join(parts) if parts else "No summary available"

    def _get_datasets_from_session(self, module_name: str) -> List[Dict[str, Any]]:
        """Get dataset information from session state."""
        datasets = []

        # Check for loaded datasets in session state
        assets_key = f"assets_loaded_{module_name}"
        if not st.session_state.get(assets_key):
            return datasets

        # Try to find datasets in session state
        # The actual key depends on how data_loaders stores them
        for key in st.session_state:
            if "datasets" in key.lower() and module_name in key:
                stored = st.session_state[key]
                if isinstance(stored, dict):
                    for name, data in stored.items():
                        dataset_info = {
                            "name": name,
                            "record_count": len(data) if hasattr(data, '__len__') else "?",
                        }
                        datasets.append(dataset_info)
                break

        return datasets

    def _get_query_count_from_session(self, module_name: str) -> Optional[int]:
        """Get query count from session state."""
        # Try to find queries in session state
        for key in st.session_state:
            if "queries" in key.lower() and module_name in key:
                stored = st.session_state[key]
                if isinstance(stored, dict):
                    # Count all query types
                    count = 0
                    for category in stored.values():
                        if isinstance(category, list):
                            count += len(category)
                        elif isinstance(category, dict):
                            count += len(category)
                    return count
        return None

    def _detect_current_tab(self) -> str:
        """
        Attempt to detect which tab is currently active.

        Note: Streamlit's st.tabs() doesn't expose selection state directly.
        We use heuristics based on session state keys.
        """
        # Check for tab-specific session state markers

        # Data tab markers
        for key in st.session_state:
            if key.startswith("show_data_") or key.startswith("show_profile_"):
                if st.session_state.get(key):
                    return "data"

        # Query edit mode markers
        if st.session_state.get("query_editor_states"):
            for key, value in st.session_state.get("query_editor_states", {}).items():
                if value:
                    return "queries"

        if st.session_state.get("query_edit_mode"):
            return "queries"

        # Default to config (first tab)
        return "config"


# Singleton instance
_context_provider: Optional[HelpChatContextProvider] = None


def get_context_provider() -> HelpChatContextProvider:
    """Get or create the context provider singleton."""
    global _context_provider
    if _context_provider is None:
        _context_provider = HelpChatContextProvider()
    return _context_provider


def get_current_context() -> Dict[str, Any]:
    """Convenience function to get current context."""
    return get_context_provider().get_current_context()
