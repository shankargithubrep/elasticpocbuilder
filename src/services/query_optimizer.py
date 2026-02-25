"""
Query Optimizer Service
Fixes ES|QL queries with errors or zero results by applying syntax rules and relaxing constraints
"""

import logging
import re
from typing import Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def fix_query(
    query: Dict,
    current_esql: str,
    data_profile: Optional[Dict],
    llm_client,
    error_message: Optional[str] = None,
    indexed_datasets: Optional[Dict] = None
) -> Tuple[str, str]:
    """Fix ES|QL query issues including syntax errors, anti-patterns, and zero results

    Uses LLM with ES|QL strict rules, data profile context, and error information to fix:
    - Syntax errors (LOOKUP JOIN anti-patterns, etc.)
    - Anti-patterns (redundant JOIN conditions like `ON field == field`)
    - Zero results (overly restrictive constraints)

    Args:
        query: Query dictionary with name, description
        current_esql: Current ES|QL query that failed or returned 0 results
        data_profile: Data profile with date ranges and statistics
        llm_client: Anthropic client for LLM calls
        error_message: Optional error message from query execution
        indexed_datasets: Optional dict of dataset name -> index name mappings

    Returns:
        Tuple of (fixed_esql, explanation)
        If fixing fails, returns (current_esql, error_message)
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

    # Load ES|QL strict rules
    try:
        from src.prompts.esql_strict_rules import get_rules_for_query_fixing
        esql_rules = get_rules_for_query_fixing()
    except Exception as e:
        logger.warning(f"Could not load ES|QL rules: {e}")
        esql_rules = ""

    # Determine the issue type
    issue_description = ""
    if error_message:
        issue_description = f"**Error Message:**\n{error_message}\n\nThe query has a syntax error or validation issue."
    else:
        issue_description = "The query executed successfully but returned **ZERO results**. Constraints may be too restrictive."

    # Format indexed datasets if provided
    indexed_datasets_text = ""
    if indexed_datasets:
        import json
        indexed_datasets_text = f"\n**Available Indices:**\n```json\n{json.dumps(indexed_datasets, indent=2)}\n```\n"

    # Build LLM prompt with ES|QL rules
    prompt = f"""Fix this ES|QL query that has issues.

**Query Name:** {query['name']}
**Description:** {query.get('description', 'N/A')}

**Issue:**
{issue_description}

**Current Query:**
```esql
{current_esql}
```

**Data Profile:**
{data_profile_text}
{indexed_datasets_text}
{esql_rules}

**CRITICAL ANTI-PATTERNS TO FIX:**

1. **Redundant JOIN Conditions** - MOST COMMON ERROR
   ❌ WRONG: `| LOOKUP JOIN products ON product_id == product_id`
   ❌ WRONG: `| LOOKUP JOIN user_profiles ON user.name == user.name`
   ❌ WRONG: `| LOOKUP JOIN network_assets ON labels.asset_id == labels.asset_id`
   ✅ CORRECT: `| LOOKUP JOIN products ON product_id`
   ✅ CORRECT: `| LOOKUP JOIN user_profiles ON user.name`
   ✅ CORRECT: `| LOOKUP JOIN network_assets ON labels.asset_id`

   When both sides of the == are identical, remove the `== field` part entirely.
   This applies to BOTH simple field names (product_id) AND dotted field names (user.name, labels.asset_id).
   This is ALWAYS wrong and will cause "ambiguous reference" errors.

2. **Table Prefixes After JOIN**
   ❌ WRONG: `| LOOKUP JOIN members ON member_id | STATS COUNT(*) BY members.tier`
   ✅ CORRECT: `| LOOKUP JOIN members ON member_id | STATS COUNT(*) BY tier`

3. **_lookup Suffix**
   ❌ WRONG: `| LOOKUP JOIN products_lookup ON product_id`
   ✅ CORRECT: `| LOOKUP JOIN products ON product_id`

4. **MV_EXPAND for Array Fields**
   If JOIN field contains arrays/comma-separated values, use MV_EXPAND first:
   ```esql
   FROM pages
   | MV_EXPAND product_refs
   | LOOKUP JOIN products ON product_refs == product_id
   ```

**Constraint Relaxation Strategies (if zero results):**

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

5. **Invalid JOIN keys**: If join key doesn't exist in both datasets
   - Remove the JOIN entirely or use a different field
   - Check data profile for actual available fields

**Your Task:**
1. First, check for and fix ANY anti-patterns (especially redundant JOIN conditions!)
2. If there's an error message, fix the syntax/validation issue
3. If zero results, relax constraints systematically
4. Explain what you changed and why in ONE sentence

Format your response as:

EXPLANATION:
[Brief one-sentence explanation of what you fixed]

FIXED QUERY:
```esql
[The fixed query]
```

Provide ONLY the format above."""

    try:
        response = llm_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text.strip()

        # Extract explanation
        explanation = "Query fixed"
        if "EXPLANATION:" in response_text:
            parts = response_text.split("FIXED QUERY:")
            if parts:
                exp_text = parts[0].replace("EXPLANATION:", "").strip()
                if exp_text:
                    explanation = exp_text

        # Extract fixed query
        if "```" in response_text:
            code_blocks = response_text.split("```")
            for i, block in enumerate(code_blocks):
                if i % 2 == 1:  # Odd indices are code blocks
                    lines = block.strip().split('\n')
                    # Skip language identifier if present
                    if lines[0].lower() in ['esql', 'sql', '']:
                        fixed_query = '\n'.join(lines[1:]) if len(lines) > 1 else block.strip()
                    else:
                        fixed_query = block.strip()

                    # Apply deterministic anti-pattern fixes
                    fixed_query = apply_deterministic_fixes(fixed_query)

                    logger.info(f"Fixed query '{query['name']}': {explanation}")
                    return fixed_query.strip(), explanation

        # If we can't extract, return original
        logger.warning("Could not extract fixed query from LLM response")
        return current_esql, "Failed to fix query"

    except Exception as e:
        logger.error(f"LLM fix failed: {e}", exc_info=True)
        return current_esql, f"Fix error: {str(e)}"


def apply_deterministic_fixes(esql: str) -> str:
    """Apply deterministic regex-based fixes for common anti-patterns

    This catches issues the LLM might miss, especially the redundant JOIN condition.

    Args:
        esql: ES|QL query string

    Returns:
        Fixed ES|QL query string
    """
    # Fix redundant JOIN conditions like: ON field == field
    # Pattern: LOOKUP JOIN <table> ON <field> == <same_field>
    # Handles both simple fields (product_id) and dotted fields (user.name)
    esql = re.sub(
        r'(LOOKUP\s+JOIN\s+\w+\s+ON\s+)([\w.]+)\s+==\s+\2\b',
        r'\1\2',
        esql,
        flags=re.IGNORECASE
    )

    # Remove _lookup suffix from index names
    esql = re.sub(
        r'(LOOKUP\s+JOIN\s+)(\w+)_lookup\b',
        r'\1\2',
        esql,
        flags=re.IGNORECASE
    )

    return esql


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


# Backward compatibility alias
relax_query_constraints = fix_query
