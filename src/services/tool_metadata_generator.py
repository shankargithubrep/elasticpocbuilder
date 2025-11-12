"""
Tool Metadata Generator using LLM

This service generates metadata for Agent Builder tools using an LLM
to create appropriate names, descriptions, and tags based on the query content.
"""

import json
from typing import Dict, Any, List


def generate_tool_metadata(
    query: Dict[str, Any],
    query_id: str,
    module_name: str,
    llm_client: Any
) -> Dict[str, Any]:
    """
    Generate tool metadata using an LLM based on the query content.

    Args:
        query: The query dictionary containing the ES|QL query and metadata
        query_id: The unique identifier for the query
        module_name: The name of the demo module
        llm_client: The Anthropic client instance

    Returns:
        Dict containing generated tool metadata
    """

    # Extract query text - handle different query formats
    if isinstance(query.get('esql'), str):
        query_text = query['esql']
    elif isinstance(query.get('esql'), dict) and 'query' in query['esql']:
        query_text = query['esql']['query']
    elif 'query' in query:
        query_text = query['query']
    else:
        query_text = str(query)

    # Extract company/customer name from module_name
    # Format is typically: company_department_timestamp
    module_parts = module_name.split('_')
    if len(module_parts) >= 2:
        company = module_parts[0].lower()
        department = module_parts[1].lower() if len(module_parts) > 1 else "analytics"
    else:
        company = module_name.lower()[:10]  # Truncate if too long
        department = "analytics"

    # Build context about the query
    context_parts = []

    if query.get('name'):
        context_parts.append(f"Query Name: {query['name']}")

    if query.get('description'):
        context_parts.append(f"Query Description: {query['description']}")

    if query.get('pain_point'):
        context_parts.append(f"Pain Point Addressed: {query['pain_point']}")

    if query.get('datasets'):
        context_parts.append(f"Datasets Used: {', '.join(query['datasets'])}")

    if query.get('parameters'):
        param_list = [f"{p.get('name')} ({p.get('type', 'unknown')})" for p in query['parameters']]
        context_parts.append(f"Parameters: {', '.join(param_list)}")

    context = "\n".join(context_parts)

    # Create the prompt for the LLM
    prompt = f"""You are an expert at creating Elastic Agent Builder tool definitions.

Based on the following ES|QL query and context, generate appropriate metadata for deploying this as an Agent Builder tool.

Query Context:
{context}

ES|QL Query:
```
{query_text}
```

Customer/Company: {company}
Department/Group: {department}

CRITICAL REQUIREMENTS:

1. "tool_id": Create a concise tool ID following this pattern: <customer>_<group>_<purpose>
   - MUST start and end with a letter or number
   - Can ONLY contain lowercase letters, numbers, dots, and underscores
   - Keep it SHORT (max 50 chars) and descriptive
   - Example: "jpmc_infrastructure_performance_baseline"
   - Do NOT include timestamps, dates, or "query" in the ID

2. "description": Start with a short human-friendly summary (first ~50 chars are shown in tool list)
   - First sentence: Brief summary of what the tool does (will be truncated in UI)
   - Following sentences: When to use it, what insights it provides
   - Focus on business value, not technical details
   - Example: "Compares Intel vs AMD server performance metrics. Analyzes performance-per-dollar across workloads to identify cost optimization opportunities. Useful for infrastructure planning and TCO analysis."

3. "tags": An array of 3-5 relevant tags for categorization
   - Include domain tags (e.g., "infrastructure", "performance", "cost")
   - Include technical tags (e.g., "esql", "analytics")
   - Keep tags lowercase and single words

4. "sample_question": A natural, realistic user question that would trigger an agent to call this tool
   - Should sound like a real human asking a business question
   - Should NOT feel too formal or obviously matching the description
   - Should reflect the actual business context and pain points
   - Example (for performance analysis): "I'm trying to decide between Intel and AMD servers for our next batch of hardware. Which ones give us better bang for our buck?"
   - Example (for cost analysis): "Can you show me where we're spending the most on cloud infrastructure this quarter?"
   - Make it conversational and contextual to the specific query purpose

Return ONLY valid JSON with these 4 fields, no other text or markdown formatting."""

    try:
        # Call the LLM
        response = llm_client.messages.create(
            model="claude-3-haiku-20240307",  # Use Haiku for speed and cost
            max_tokens=500,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract the JSON from the response
        response_text = response.content[0].text.strip()

        # Clean up the response if it has markdown code blocks
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # Remove first and last lines if they are code block markers
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = "\n".join(lines)

        # Parse the JSON
        metadata = json.loads(response_text)

        # Validate and clean up the metadata
        if 'tool_id' not in metadata:
            metadata['tool_id'] = f"{company}_{department}_{query_id.replace('-', '_')}"

        # Sanitize tool_id to meet constraints
        import re
        tool_id = metadata['tool_id'].lower()
        # Replace any character that's not alphanumeric, dot, or underscore
        tool_id = re.sub(r'[^a-z0-9._]', '_', tool_id)
        # Remove consecutive underscores
        tool_id = re.sub(r'_+', '_', tool_id)
        # Ensure it starts and ends with alphanumeric
        tool_id = re.sub(r'^[^a-z0-9]+', '', tool_id)
        tool_id = re.sub(r'[^a-z0-9]+$', '', tool_id)
        # Truncate if too long
        if len(tool_id) > 50:
            tool_id = tool_id[:50].rstrip('_.')
        metadata['tool_id'] = tool_id

        if 'description' not in metadata:
            metadata['description'] = query.get('description', 'ES|QL query tool')

        if 'tags' not in metadata:
            metadata['tags'] = []

        # Ensure tags is a list
        if isinstance(metadata.get('tags'), str):
            metadata['tags'] = [metadata['tags']]

        # Add fallback sample_question if not provided
        if 'sample_question' not in metadata:
            # Create a basic sample question from the query name
            query_name = query.get('name', 'this analysis')
            metadata['sample_question'] = f"Can you show me {query_name.lower()}?"

        # Add the query text to metadata
        metadata['query'] = query_text

        # Add parameters if they exist
        if query.get('parameters'):
            metadata['parameters'] = query['parameters']

        return metadata

    except json.JSONDecodeError as e:
        # If JSON parsing fails, create a basic metadata structure
        import re
        # Create a simple tool ID from query name
        query_name = query.get('name', query_id)
        simple_purpose = re.sub(r'[^a-z0-9]+', '_', query_name.lower())[:20]
        tool_id = f"{company}_{department}_{simple_purpose}".rstrip('_')
        tool_id = re.sub(r'_+', '_', tool_id)

        return {
            'tool_id': tool_id,
            'description': query.get('description', 'ES|QL query tool for data analysis'),
            'tags': ['esql', 'analytics', company],
            'sample_question': f"Can you show me {query_name.lower()}?",
            'query': query_text
        }

    except Exception as e:
        # Fallback to basic metadata
        import re
        # Create a simple tool ID
        tool_id = f"{company}_{department}_tool".lower()
        tool_id = re.sub(r'[^a-z0-9._]', '_', tool_id)
        tool_id = re.sub(r'_+', '_', tool_id)

        query_name = query.get('name', 'this analysis')

        return {
            'tool_id': tool_id,
            'description': f"ES|QL query tool: {query.get('description', 'Data analysis query')}",
            'tags': ['esql', 'analytics'],
            'sample_question': f"Can you help me with {query_name.lower()}?",
            'query': query_text,
            'error': str(e)
        }