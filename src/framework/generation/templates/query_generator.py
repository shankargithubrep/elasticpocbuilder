"""
Query generator templates for demo module generation.

This module provides templates for generating query generator modules
with scripted, parameterized, and RAG query types.
"""

from typing import Dict, Any


def get_analytics_query_generator_template() -> str:
    """Get the query generator template for analytics mode

    Generates queries focused on:
    - Aggregations with STATS
    - Time-series analysis with DATE_TRUNC
    - LOOKUP JOIN operations
    - Metrics and dashboards
    """
    # Template from lines 1329-1410
    return """# TODO: Extract analytics query generator template"""


def get_search_query_generator_template() -> str:
    """Get the query generator template for search/RAG mode

    Generates queries focused on:
    - MATCH operations for text search
    - RERANK for relevance optimization
    - COMPLETION for LLM-based answers
    - Semantic search patterns
    """
    # Template from lines 2229-?
    return """# TODO: Extract search query generator template"""


def get_simple_query_generator_template() -> str:
    """Get the simple query generator template (fallback)"""
    # Template from lines 3147-3180
    return """# TODO: Extract simple query generator template"""


def get_query_generator_with_strategy_template(query_strategy: Dict[str, Any]) -> str:
    """Get template for generating queries from a query strategy

    This is used in the two-phase generation approach where:
    1. Query strategy is generated first
    2. Data is generated and indexed
    3. Queries are generated with actual schema knowledge
    """
    # Template logic for strategy-based generation
    return """# TODO: Extract strategy-based query generator template"""
