"""
Context-specific suggestion chips for the Help Chat widget.

Provides quick-access questions that change based on current UI context.
"""

from typing import List, Dict, Any


# Chip configurations by context
CONTEXT_CHIPS: Dict[str, List[str]] = {
    # Create mode chips
    "create": [
        "How should I format my prompt?",
        "Search vs Analytics demos?",
        "What makes a good description?",
        "What is expanded mode?",
    ],

    # Browse mode - Config tab
    "browse_config": [
        "What does this config control?",
        "How do I regenerate assets?",
        "Can I edit the config?",
    ],

    # Browse mode - Data tab
    "browse_data": [
        "How do I index this data?",
        "What do these fields mean?",
        "Can I modify the data?",
    ],

    # Browse mode - Queries tab
    "browse_queries": [
        "How do I test a query?",
        "What does validation mean?",
        "How to edit and re-run?",
    ],

    # Browse mode - Tools tab
    "browse_tools": [
        "How do I deploy a tool?",
        "What is tool metadata?",
        "Why can't I deploy this tool?",
    ],

    # Browse mode - Agents tab
    "browse_agents": [
        "How do I create an agent?",
        "How do I assign tools?",
        "What are agent instructions?",
    ],

    # Browse mode - Guide tab
    "browse_guide": [
        "How do I use this guide?",
        "Can I customize the guide?",
        "What's the talk track?",
    ],

    # Generic browse (no specific tab or unknown tab)
    "browse": [
        "How do I navigate this module?",
        "What should I do first?",
        "How do I deploy to Agent Builder?",
    ],

    # Fallback for unknown context
    "default": [
        "What is Vulcan?",
        "How do I get started?",
        "What can I build with this?",
    ],
}


def get_chips_for_context(context: Dict[str, Any]) -> List[str]:
    """
    Get appropriate suggestion chips based on current UI context.

    Args:
        context: Dictionary with:
            - mode: "create" | "browse"
            - tab: (optional) Current tab name in browse mode
            - module_name: (optional) Currently selected module

    Returns:
        List of chip question strings
    """
    mode = context.get("mode", "").lower()
    tab = context.get("tab", "").lower()

    # Create mode
    if mode == "create":
        return CONTEXT_CHIPS["create"]

    # Browse mode with specific tab
    if mode == "browse":
        # Map tab names to chip keys
        tab_key_map = {
            "config": "browse_config",
            "data": "browse_data",
            "queries": "browse_queries",
            "tools": "browse_tools",
            "agents": "browse_agents",
            "guide": "browse_guide",
        }

        chip_key = tab_key_map.get(tab, "browse")
        return CONTEXT_CHIPS.get(chip_key, CONTEXT_CHIPS["browse"])

    # Fallback
    return CONTEXT_CHIPS["default"]


def get_all_chip_questions() -> List[str]:
    """
    Get all unique chip questions across all contexts.

    Useful for pre-building FAQ responses.

    Returns:
        Deduplicated list of all chip questions
    """
    all_questions = []
    seen = set()

    for questions in CONTEXT_CHIPS.values():
        for q in questions:
            if q not in seen:
                all_questions.append(q)
                seen.add(q)

    return all_questions
