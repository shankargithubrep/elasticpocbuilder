"""
Guided Expansion Flow Orchestration

Coordinates the multi-stage expansion with user validation checkpoints.
"""

import streamlit as st
import logging
from typing import Optional, Dict

from .components.guided_expansion import show_domain_validation, show_progress_indicator
from ..services.guided_expansion import DomainExtractor
from .message_processor import expand_brief_prompt
from .prompt_templates import detect_demo_type

logger = logging.getLogger(__name__)


def run_guided_expansion(user_prompt: str) -> Optional[str]:
    """
    Run guided expansion flow with user validation checkpoints.

    This is an enhanced version of expand_brief_prompt that adds:
    - Domain extraction and validation
    - User editing of key terms
    - Iterative refinement

    Args:
        user_prompt: Brief user input to expand

    Returns:
        Expanded technical document if complete, None if still in progress
    """

    # Initialize guided expansion state if not exists
    if 'guided_expansion' not in st.session_state:
        st.session_state.guided_expansion = {
            'stage': 'extracting',  # extracting | validating | expanding | complete
            'original_prompt': user_prompt,  # Store for reruns
            'extraction': None,
            'validated_extraction': None,
            'expanded_content': None
        }

    ge_state = st.session_state.guided_expansion

    # Stage 1: Extract domain concepts
    if ge_state['stage'] == 'extracting':
        show_progress_indicator('domain_extraction')

        with st.spinner("🔍 Analyzing your input..."):
            try:
                # Detect demo type
                demo_type = detect_demo_type(user_prompt)
                logger.info(f"Detected demo type: {demo_type}")

                # Get LLM client
                from src.services.llm_proxy_service import UnifiedLLMClient
                llm_client = UnifiedLLMClient()

                # Extract domain concepts
                extractor = DomainExtractor(llm_client)
                extraction = extractor.extract(user_prompt, demo_type)

                # Store extraction
                ge_state['extraction'] = extraction
                ge_state['demo_type'] = demo_type
                ge_state['stage'] = 'validating'

                st.rerun()

            except Exception as e:
                logger.error(f"Extraction failed: {e}", exc_info=True)
                st.error(f"❌ Failed to analyze input: {e}")
                st.error("Falling back to standard expansion...")

                # Fallback to standard expansion
                expanded = expand_brief_prompt(user_prompt)
                return expanded

    # Stage 2: User validates and edits
    elif ge_state['stage'] == 'validating':
        show_progress_indicator('domain_extraction')

        st.markdown("---")

        # Show validation UI
        logger.info("Showing validation UI for user review")
        result = show_domain_validation(ge_state['extraction'])

        if result:
            # Check if user requested action
            if isinstance(result, dict) and 'action' in result:
                if result['action'] == 'cancel':
                    # User cancelled - clear state
                    del st.session_state.guided_expansion
                    st.info("Expansion cancelled. You can submit your prompt again.")
                    return None
            else:
                # User validated - store and move to expansion
                ge_state['validated_extraction'] = result
                ge_state['stage'] = 'expanding'

                # Create a summary of what was validated for chat history
                validated = result
                summary = f"""### 🔍 Domain Analysis & Validation

**Domain:** {validated['domain']['name']}
**Industry:** {validated['domain']['industry']}
**Focus:** {validated['domain']['primary_focus']}

**Key Entities Validated ({len(validated['key_terms']['entities'])}):**
{chr(10).join(f'- {entity}' for entity in validated['key_terms']['entities'][:8])}
{f"- ...and {len(validated['key_terms']['entities']) - 8} more" if len(validated['key_terms']['entities']) > 8 else ""}

**Scenarios Identified ({len(validated['key_terms']['scenarios'])}):**
{chr(10).join(f'{i+1}. {scenario[:100]}{"..." if len(scenario) > 100 else ""}' for i, scenario in enumerate(validated['key_terms']['scenarios'][:3]))}
{f"...and {len(validated['key_terms']['scenarios']) - 3} more scenarios" if len(validated['key_terms']['scenarios']) > 3 else ""}

✅ **User validated and approved** - Proceeding to expansion with these terms.
"""
                ge_state['validation_summary'] = summary
                st.rerun()

        return None  # Still validating

    # Stage 3: Expand using validated terms
    elif ge_state['stage'] == 'expanding':
        show_progress_indicator('expansion')

        with st.spinner("📝 Generating detailed technical document..."):
            try:
                validated = ge_state['validated_extraction']
                demo_type = ge_state['demo_type']

                # Build enriched prompt with validated terms
                enriched_prompt = _build_enriched_prompt(user_prompt, validated)

                # Use standard expansion with validated terms
                # skip_size_check=True because enriched prompt is intentionally large
                expanded = expand_brief_prompt(enriched_prompt, force_demo_type=demo_type, skip_size_check=True)

                # Store result
                ge_state['expanded_content'] = expanded
                ge_state['stage'] = 'complete'

                # Clean up state after completion
                del st.session_state.guided_expansion

                return expanded

            except Exception as e:
                logger.error(f"Expansion failed: {e}", exc_info=True)
                st.error(f"❌ Expansion failed: {e}")
                return None

    elif ge_state['stage'] == 'complete':
        # Already complete - return stored content
        content = ge_state['expanded_content']
        del st.session_state.guided_expansion
        return content

    return None


def _build_enriched_prompt(original_prompt: str, validated_extraction: Dict) -> str:
    """
    Build enriched prompt incorporating validated user edits.

    This ensures the expansion uses the exact terms the user validated.
    """

    domain = validated_extraction['domain']
    key_terms = validated_extraction['key_terms']

    enriched = f"""
**VALIDATED CUSTOMER CONTEXT** (use these exact terms):

**Domain**: {domain['name']}
**Industry**: {domain['industry']}
**Primary Focus**: {domain['primary_focus']}

**Key Entities to Use** (exact phrases validated by user):
{chr(10).join(f'- {entity}' for entity in key_terms['entities'])}

**User-Validated Scenarios**:
{chr(10).join(f'{i+1}. {scenario}' for i, scenario in enumerate(key_terms['scenarios']))}

**Original User Input**:
```
{original_prompt}
```

**CRITICAL INSTRUCTIONS FOR EXPANSION**:
1. Use ONLY the validated entities listed above in all examples
2. Reference the validated scenarios when creating use cases
3. Do NOT introduce new entities or generic terms
4. Use the user's exact phrasing from the validated terms

Expand this into a detailed technical use case document now.
"""

    return enriched
