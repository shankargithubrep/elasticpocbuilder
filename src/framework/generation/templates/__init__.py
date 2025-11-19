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
    get_scripted_queries_prompt,
    get_parameterized_queries_prompt,
    get_rag_queries_prompt,
    get_query_module_wrapper
)

from .guide_generator import (
    get_demo_guide_prompt,
    get_demo_guide_module_template,
    get_fallback_demo_guide
)

from .agent_metadata import (
    get_agent_instructions_prompt,
    get_agent_metadata_template,
    get_fallback_agent_instructions,
    generate_agent_id,
    generate_avatar_symbol,
    get_agent_avatar_color_by_type
)

__all__ = [
    # Data generators
    'get_analytics_data_generator_template',
    'get_search_data_generator_template',
    'get_simple_data_generator_template',

    # Query generators
    'get_scripted_queries_prompt',
    'get_parameterized_queries_prompt',
    'get_rag_queries_prompt',
    'get_query_module_wrapper',

    # Guide generators
    'get_demo_guide_prompt',
    'get_demo_guide_module_template',
    'get_fallback_demo_guide',

    # Agent metadata
    'get_agent_instructions_prompt',
    'get_agent_metadata_template',
    'get_fallback_agent_instructions',
    'generate_agent_id',
    'generate_avatar_symbol',
    'get_agent_avatar_color_by_type'
]