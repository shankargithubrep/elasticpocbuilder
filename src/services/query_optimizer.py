"""
Query Optimizer Service
Optimizes ES|QL queries that return zero results by intelligently relaxing constraints
"""

import logging
from typing import Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def relax_query_constraints(
    query: Dict,
    current_esql: str,
    data_profile: Optional[Dict],
    llm_client
) -> Tuple[str, str]:
    """Relax query constraints when zero results are returned

    Uses LLM with data profile context to intelligently relax:
    - Time windows: 180d → 90d → 60d → 30d
    - Numeric thresholds: >= 100 → >= 50 → >= 10
    - Multi-condition AND: Remove least critical filters

    Args:
        query: Query dictionary with name, description
        current_esql: Current ES|QL query that returned 0 results
        data_profile: Data profile with date ranges and statistics
        llm_client: Anthropic client for LLM calls

    Returns:
        Tuple of (optimized_esql, explanation)
        If optimization fails, returns (current_esql, error_message)
    """

    # Format data profile for LLM
    data_profile_text = ""
    if data_profile:
        try:
            from src.services.data_profiler import DataProfiler
            data_profile_text = DataProfiler.format_profile_for_llm(data_profile, compact=True)
        except Exception as e:
            logger.warning(f"Could not format data profile: {e}")
            data_profile_text = "Data profile not available"

    # Build LLM prompt
    prompt = f"""This ES|QL query executed successfully but returned ZERO results.
Your task is to relax the constraints to make it return results while maintaining its purpose.

**Query Name:** {query['name']}
**Description:** {query.get('description', 'N/A')}

**Current Query (returned 0 results):**
```esql
{current_esql}
```

**Data Profile:**
{data_profile_text}

**Constraint Relaxation Strategies:**

1. **Time-based constraints**: Reduce time windows
   - 365 days → 180 days → 90 days → 30 days → 7 days
   - Use data profile date ranges to pick realistic values

2. **Numeric thresholds**: Lower minimums, raise maximums
   - usage_count >= 100 → >= 50 → >= 10 → >= 5
   - rating >= 4.5 → >= 4.0 → >= 3.5

3. **Multi-condition AND**: Remove least critical conditions
   - Keep core business logic, drop peripheral filters

4. **Strict equality**: Convert to ranges or patterns
   - status == "critical" → status IN ("critical", "high")
   - MATCH with too many terms → fewer terms

5. **Multiple relaxations**: You may need to relax 2-3 constraints

**Your Task:**
1. Identify which constraint(s) are too restrictive (use data profile)
2. Relax them systematically
3. Explain what you changed and why

Format your response as:

EXPLANATION:
[Brief explanation of what you changed and why, in one sentence]

RELAXED QUERY:
```esql
[The relaxed query]
```

Provide ONLY the format above."""

    try:
        response = llm_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()

        # Extract explanation
        explanation = "Constraints relaxed"
        if "EXPLANATION:" in response_text:
            parts = response_text.split("RELAXED QUERY:")
            if parts:
                exp_text = parts[0].replace("EXPLANATION:", "").strip()
                if exp_text:
                    explanation = exp_text

        # Extract relaxed query
        if "```" in response_text:
            code_blocks = response_text.split("```")
            for i, block in enumerate(code_blocks):
                if i % 2 == 1:  # Odd indices are code blocks
                    lines = block.strip().split('\n')
                    # Skip language identifier if present
                    if lines[0].lower() in ['esql', 'sql', '']:
                        relaxed_query = '\n'.join(lines[1:]) if len(lines) > 1 else block.strip()
                    else:
                        relaxed_query = block.strip()

                    logger.info(f"Relaxed query for '{query['name']}': {explanation}")
                    return relaxed_query.strip(), explanation

        # If we can't extract, return original
        logger.warning("Could not extract relaxed query from LLM response")
        return current_esql, "Failed to optimize query"

    except Exception as e:
        logger.error(f"LLM relaxation failed: {e}", exc_info=True)
        return current_esql, f"Optimization error: {str(e)}"


def load_data_profile(module_name: str) -> Optional[Dict]:
    """Load data profile for a demo module

    Args:
        module_name: Name of the demo module

    Returns:
        Data profile dictionary or None if not found
    """
    try:
        from src.services.data_profiler import DataProfiler
        module_path = Path("demos") / module_name
        return DataProfiler.load_profile(module_path)
    except Exception as e:
        logger.warning(f"Could not load data profile for {module_name}: {e}")
        return None
