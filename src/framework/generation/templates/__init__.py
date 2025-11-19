"""
Template management for demo module generation.

This module provides templates for generating demo modules:
- Data generator templates (analytics and search modes)
- Query generator templates (scripted, parameterized, RAG)
- Demo guide templates
- Agent metadata templates
"""

from .data_generator import (
    get_analytics_data_generator_template,
    get_search_data_generator_template,
    get_simple_data_generator_template
)

from .query_generator import (
    get_analytics_query_generator_template,
    get_search_query_generator_template,
    get_simple_query_generator_template,
    get_query_generator_with_strategy_template
)

from .guide_generator import (
    get_demo_guide_template,
    get_simple_demo_guide_template
)

from .agent_metadata import (
    get_agent_instructions_prompt
)

__all__ = [
    # Data generators
    'get_analytics_data_generator_template',
    'get_search_data_generator_template',
    'get_simple_data_generator_template',

    # Query generators
    'get_analytics_query_generator_template',
    'get_search_query_generator_template',
    'get_simple_query_generator_template',
    'get_query_generator_with_strategy_template',

    # Guide generators
    'get_demo_guide_template',
    'get_simple_demo_guide_template',

    # Agent metadata
    'get_agent_instructions_prompt'
]