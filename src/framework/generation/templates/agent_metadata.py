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

    Creates professional agent instructions that define the agent's role,
    expertise, and capabilities based on the customer context.

    Args:
        config: Demo configuration with company context
        query_descriptions: List of query descriptions to inform capabilities
        datasets_info: List of available datasets

    Returns:
        Prompt for LLM to generate comprehensive agent instructions
    """
    query_context = "\n".join([f"- {desc}" for desc in query_descriptions[:10]]) if query_descriptions else "No queries available yet"
    dataset_context = ", ".join(datasets_info) if datasets_info else "No datasets available yet"

    return f"""Generate professional agent instructions for an Elastic Agent Builder agent.

**Company Context:**
- Company: {config['company_name']}
- Department: {config.get('department', 'General')}
- Industry: {config.get('industry', 'General')}
- Pain Points: {', '.join(config.get('pain_points', []))}
- Use Cases: {', '.join(config.get('use_cases', []))}

**Available Capabilities:**
Query Capabilities:
{query_context}

Available Datasets:
{dataset_context}

**Task:** Generate clear, professional instructions that:
1. Define the agent's role and expertise
2. Explain what types of questions it can answer
3. Reference the specific pain points and use cases
4. Set appropriate tone and communication style
5. Include any industry-specific considerations

The instructions should be 150-250 words, professional but approachable, and specific to this customer's context.

Generate ONLY the instructions text, no additional formatting or explanation."""


def get_agent_metadata_template(config: Dict[str, Any],
                               agent_id: str,
                               avatar_symbol: str,
                               avatar_color: str,
                               instructions: str) -> Dict[str, Any]:
    """Generate complete agent metadata structure for Elastic Agent Builder

    Creates the JSON structure required for deploying an agent to the
    Elastic Agent Builder platform.

    Args:
        config: Demo configuration with company context
        agent_id: Unique identifier for the agent
        avatar_symbol: 2-character symbol for agent avatar
        avatar_color: Hex color code for avatar (#3B82F6 for analytics, #10B981 for search)
        instructions: Professional instructions for agent behavior

    Returns:
        Dictionary with complete agent metadata structure ready for JSON serialization
    """
    company_slug = config['company_name'].lower().replace(' ', '_')[:20]
    dept_slug = config.get('department', 'general').lower().replace(' ', '_')[:15]
    demo_type = config.get('demo_type', 'analytics')

    return {
        "id": agent_id,
        "name": f"{config['company_name']} {generate_concise_department_name(config.get('department', 'Analytics'))} Assistant",
        "description": f"AI assistant specialized in {config.get('department', 'data analysis')} for {config['company_name']}. I can help analyze your data, answer questions, and provide insights based on your specific use cases.",
        "labels": [
            company_slug,
            dept_slug,
            demo_type,
            "demo-builder",
            config.get('industry', 'general').lower()
        ],
        "avatar_color": avatar_color,
        "avatar_symbol": avatar_symbol,
        "configuration": {
            "instructions": instructions,
            "tools": []  # Initially empty, tools will be added separately
        }
    }


def get_fallback_agent_instructions(config: Dict[str, Any]) -> str:
    """Generate fallback agent instructions when LLM is unavailable

    Provides a reasonable default set of instructions based on customer context.

    Args:
        config: Demo configuration with company context

    Returns:
        Fallback agent instructions text
    """
    pain_points = config.get('pain_points', ['Data analysis', 'Reporting', 'Insights'])[:3]
    use_cases = config.get('use_cases', ['Analyzing trends', 'Finding patterns', 'Generating reports'])[:3]
    pain_points_list = "\n".join([f"- {pp}" for pp in pain_points])
    use_cases_list = "\n".join([f"- {uc}" for uc in use_cases])

    return f"""You are an AI assistant specialized in {config.get('department', 'data analysis')} for {config['company_name']}.

I help analyze data and provide insights specific to your {config.get('industry', 'business')} operations.

Key areas of focus:
{pain_points_list}

I can assist with:
{use_cases_list}

Feel free to ask questions about your data, request specific analyses, or explore insights that can help optimize your operations."""


def get_agent_avatar_color_by_type(demo_type: str) -> str:
    """Get the appropriate avatar color based on demo type

    Args:
        demo_type: Type of demo ('analytics' or 'search')

    Returns:
        Hex color code (#3B82F6 for analytics, #10B981 for search)
    """
    if demo_type == 'search':
        return "#10B981"  # Green
    else:
        return "#3B82F6"  # Blue (default for analytics)


def generate_agent_id(company_name: str, department: str) -> str:
    """Generate a unique agent ID from company and department

    Args:
        company_name: Name of the company
        department: Department name

    Returns:
        Formatted agent ID (lowercase, underscores, max 50 chars)
    """
    company_slug = company_name.lower().replace(' ', '_')[:20]
    dept_slug = department.lower().replace(' ', '_')[:15]
    return f"{company_slug}_{dept_slug}_agent"


def generate_avatar_symbol(company_name: str) -> str:
    """Generate avatar symbol from company name initials

    Args:
        company_name: Name of the company

    Returns:
        2-character symbol representing the company
    """
    company_words = company_name.split()
    if len(company_words) >= 2:
        return (company_words[0][0] + company_words[1][0]).upper()[:2]
    else:
        return company_name[:2].upper()


def generate_concise_department_name(department: str) -> str:
    """Generate a concise department name for agent display

    Takes a potentially long department name and creates a shorter version
    suitable for agent names.

    Args:
        department: Full department name

    Returns:
        Concise department name (max ~30 chars)

    Examples:
        "Data team with product marketing and product management" → "Product Data & Marketing"
        "Network Operations Center (NOC) / Radio Access Network Engineering" → "Network Operations"
        "Platform Infrastructure & Engineering" → "Platform Infrastructure"
    """
    # Remove common noise words and parentheticals
    dept = department.lower()

    # Remove parentheticals
    import re
    dept = re.sub(r'\([^)]*\)', '', dept).strip()

    # Common words to remove (articles, conjunctions, etc.)
    noise_words = {'the', 'a', 'an', 'and', 'or', 'of', 'with', 'for', 'in', 'on', 'at', 'to', 'from'}

    # Split on common delimiters
    parts = re.split(r'[/,;]', dept)

    # Take the first meaningful part if multiple parts exist
    if len(parts) > 1:
        dept = parts[0].strip()

    # Extract key words (non-noise words)
    words = dept.split()
    key_words = []

    for word in words:
        if word not in noise_words or len(key_words) == 0:  # Keep at least one word
            # Capitalize first letter
            key_words.append(word.capitalize())

        # Stop if we have a good concise name
        if len(' '.join(key_words)) >= 20:
            break

    # If still too long, take first 3-4 key words
    if len(' '.join(key_words)) > 35:
        key_words = key_words[:3]

    result = ' '.join(key_words)

    # Fallback if result is empty
    if not result:
        result = department[:30]

    return result
