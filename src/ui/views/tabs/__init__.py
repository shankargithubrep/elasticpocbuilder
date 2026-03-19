"""
Tab components for Browse Demos view.

Each tab is implemented as a separate module for better organization and maintainability.
"""

from .config_tab import render_config_tab
from .data_tab import render_data_tab
from .queries_tab import render_queries_tab
from .guide_tab import render_guide_tab
from .conversation_tab import render_conversation_tab
from .tools_tab import render_tools_tab
from .agents_tab import render_agents_tab
from .detection_rules_tab import render_detection_rules_tab
from .service_map_tab import render_service_map_tab

__all__ = [
    'render_config_tab',
    'render_data_tab',
    'render_queries_tab',
    'render_guide_tab',
    'render_conversation_tab',
    'render_tools_tab',
    'render_agents_tab',
    'render_detection_rules_tab',
    'render_service_map_tab',
]