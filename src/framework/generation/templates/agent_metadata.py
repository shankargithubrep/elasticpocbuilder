"""
Agent metadata templates for Elastic Agent Builder integration.

This module provides templates and prompts for generating agent metadata
that enables deployment to the Agent Builder platform.
"""

from typing import Dict, Any, List


def get_agent_instructions_prompt(config: Dict[str, Any],
                                 query_descriptions: List[str],
                                 datasets_info: List[str]) -> str:
    """Generate prompt for creating agent instructions

    Args:
        config: Demo configuration with company context
        query_descriptions: List of query descriptions to inform capabilities
        datasets_info: List of available datasets

    Returns:
        Prompt for LLM to generate comprehensive agent instructions
    """

    company = config.get('company_name', 'Unknown Company')
    department = config.get('department', 'Analytics')
    industry = config.get('industry', 'general')
    pain_points = config.get('pain_points', [])
    use_cases = config.get('use_cases', [])

    # Build the prompt for generating agent instructions
    # This will be extracted from the _generate_agent_instructions method
    return f"""# TODO: Extract agent instructions prompt generation"""
