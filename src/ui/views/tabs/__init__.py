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
from .replay_tab import render_replay_tab
from .search_stack_tab import render_search_stack_tab
from .revenue_engine_tab import render_revenue_engine_tab
from .obs_intelligence_tab import render_obs_intelligence_tab
from .devworkbench_tab import render_devworkbench_tab
from .persona_dashboards_tab import render_persona_dashboards_tab
from .hunter_workbench_tab import render_hunter_workbench_tab
from .eval_workbench_tab import render_eval_workbench_tab
from .ai_endpoint_security_tab import render_ai_endpoint_security_tab
from .genesys_qa_tab import render_genesys_qa_tab
from .esrally_tab import render_esrally_tab

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
    'render_replay_tab',
    'render_search_stack_tab',
    'render_revenue_engine_tab',
    'render_obs_intelligence_tab',
    'render_devworkbench_tab',
    'render_persona_dashboards_tab',
    'render_hunter_workbench_tab',
    'render_eval_workbench_tab',
    'render_ai_endpoint_security_tab',
    'render_genesys_qa_tab',
    'render_esrally_tab',
]