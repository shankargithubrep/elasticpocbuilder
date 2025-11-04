"""Prompts package for Demo Builder"""

# Re-export key functions from esql_strict_rules
from .esql_strict_rules import (
    get_esql_rules,
    get_advanced_patterns,
    get_query_patterns,
    get_error_fixes,
    get_llm_guidelines,
    get_fixer_rules,
    get_complete_reference,
    get_rules_for_module_generation,
    get_rules_for_query_fixing,
)

__all__ = [
    'get_esql_rules',
    'get_advanced_patterns',
    'get_query_patterns',
    'get_error_fixes',
    'get_llm_guidelines',
    'get_fixer_rules',
    'get_complete_reference',
    'get_rules_for_module_generation',
    'get_rules_for_query_fixing',
]