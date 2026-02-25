"""
Interactive Validation UI Components

Provides editable, user-friendly interfaces for validating extracted concepts
during guided prompt expansion.
"""

import streamlit as st
from typing import Dict, Optional, List


def show_progress_indicator(current_stage: str):
    """
    Show progress through guided expansion stages.

    Args:
        current_stage: One of 'domain_extraction', 'expansion', 'review'
    """
    stages = {
        "domain_extraction": ("🔍 Domain Analysis", 0),
        "expansion": ("📝 Expansion", 1),
        "review": ("✅ Review", 2)
    }

    if current_stage not in stages:
        return

    current_idx = stages[current_stage][1]

    # Progress bar
    progress = (current_idx + 1) / len(stages)
    st.progress(progress)

    # Stage indicators
    cols = st.columns(len(stages))
    for i, (stage_key, (label, idx)) in enumerate(stages.items()):
        with cols[i]:
            if idx < current_idx:
                st.success(f"✅ {label}")
            elif idx == current_idx:
                st.info(f"⏳ {label}")
            else:
                st.text(f"⏸️ {label}")


def show_domain_validation(extraction: Dict) -> Optional[Dict]:
    """
    Display domain extraction for user validation with full edit capability.

    Args:
        extraction: Extracted domain concepts from DomainExtractor

    Returns:
        Updated extraction dict if validated, None if still editing
    """
    st.markdown("### 🤖 Domain Understanding Checkpoint")
    st.markdown("I've analyzed your input. **Review and refine the entities and scenarios below, then click Continue.**")

    # Initialize session state for tracking edits
    if 'validation_edits' not in st.session_state:
        st.session_state.validation_edits = {
            'entities': extraction["key_terms"]["entities"].copy(),
            'scenarios': extraction["key_terms"]["scenarios"].copy()
        }

    # Action Buttons at the TOP (visible without scrolling)
    col1, col2 = st.columns(2)
    button_clicked = False
    cancel_clicked = False

    with col1:
        if st.button("✅ Looks Good - Continue", type="primary", key="validation_continue_top", use_container_width=True):
            button_clicked = True

    with col2:
        if st.button("❌ Cancel", key="validation_cancel_top", use_container_width=True):
            cancel_clicked = True

    st.markdown("---")

    # Domain Section (compact)
    st.markdown("#### 🏢 Domain & Industry")

    col1, col2 = st.columns(2)

    with col1:
        domain_name = st.text_input(
            "Domain Name",
            value=extraction["domain"]["name"],
            key="validation_domain_name",
            help="Concise name for what you're building"
        )

    with col2:
        industry = st.text_input(
            "Industry",
            value=extraction["domain"]["industry"],
            key="validation_industry",
            help="Your industry vertical"
        )

    primary_focus = st.text_area(
        "Primary Focus",
        value=extraction["domain"]["primary_focus"],
        key="validation_primary_focus",
        help="What you're trying to accomplish",
        height=80
    )

    # Entities & Scenarios in a collapsible section
    with st.expander(f"🔑 Key Entities ({len(st.session_state.validation_edits['entities'])}) & 📋 Scenarios ({len(st.session_state.validation_edits['scenarios'])})", expanded=True):
        # Key Entities Section
        st.markdown("**Key Entities & Terms**")
        st.caption("These specific terms will be used throughout the expansion:")

        # Use session state for entity list to handle adds/removes
        entities = st.session_state.validation_edits['entities']

        edited_entities = []
        entities_to_remove = []

        for i, entity in enumerate(entities):
            col1, col2 = st.columns([5, 1])
            with col1:
                edited = st.text_input(
                    f"Entity {i+1}",
                    value=entity,
                    key=f"validation_entity_{i}",
                    label_visibility="collapsed"
                )
                edited_entities.append(edited)
            with col2:
                if st.button("❌", key=f"validation_remove_entity_{i}"):
                    entities_to_remove.append(i)

        # Remove entities marked for deletion
        if entities_to_remove:
            st.session_state.validation_edits['entities'] = [
                e for i, e in enumerate(edited_entities) if i not in entities_to_remove
            ]
            st.rerun()
        else:
            st.session_state.validation_edits['entities'] = edited_entities

        # Add new entity button
        col1, col2 = st.columns([3, 1])
        with col1:
            new_entity = st.text_input(
                "Add new entity:",
                key="validation_new_entity",
                placeholder="Type a new entity and press Enter"
            )
        with col2:
            if st.button("➕ Add", key="validation_add_entity_btn"):
                if new_entity and new_entity.strip():
                    st.session_state.validation_edits['entities'].append(new_entity.strip())
                    st.rerun()

        st.markdown("---")

        # Scenarios Section
        st.markdown("**Search Scenarios**")
        st.caption("Realistic scenarios using your terminology:")

        scenarios = st.session_state.validation_edits['scenarios']
        edited_scenarios = []
        scenarios_to_remove = []

        for i, scenario in enumerate(scenarios):
            col1, col2 = st.columns([5, 1])
            with col1:
                edited = st.text_area(
                    f"Scenario {i+1}",
                    value=scenario,
                    key=f"validation_scenario_{i}",
                    height=80,
                    label_visibility="collapsed"
                )
                edited_scenarios.append(edited)
            with col2:
                st.write("")  # Spacing
                st.write("")  # Spacing
                if st.button("❌", key=f"validation_remove_scenario_{i}"):
                    scenarios_to_remove.append(i)

        # Remove scenarios marked for deletion
        if scenarios_to_remove:
            st.session_state.validation_edits['scenarios'] = [
                s for i, s in enumerate(edited_scenarios) if i not in scenarios_to_remove
            ]
            st.rerun()
        else:
            st.session_state.validation_edits['scenarios'] = edited_scenarios

        # Add new scenario
        st.text_area(
            "Add new scenario:",
            key="validation_new_scenario",
            placeholder="Describe a realistic scenario using your terminology",
            height=80
        )

        if st.button("➕ Add Scenario", key="validation_add_scenario_btn"):
            new_scenario = st.session_state.get("validation_new_scenario", "").strip()
            if new_scenario:
                st.session_state.validation_edits['scenarios'].append(new_scenario)
                st.rerun()

    # Summary
    st.markdown("#### 📊 Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Entities", len(st.session_state.validation_edits['entities']))
        st.caption(extraction["pain_points_summary"])
    with col2:
        st.metric("Scenarios", len(st.session_state.validation_edits['scenarios']))
        st.caption(extraction["use_cases_summary"])

    # Handle button clicks from the top buttons (deferred so form edits are captured)
    if button_clicked:
        # Build updated extraction with user edits
        updated_extraction = {
            "domain": {
                "name": domain_name,
                "industry": industry,
                "primary_focus": primary_focus
            },
            "key_terms": {
                "entities": st.session_state.validation_edits['entities'],
                "scenarios": st.session_state.validation_edits['scenarios'],
                "document_types": extraction["key_terms"].get("document_types", []),
                "search_patterns": extraction["key_terms"].get("search_patterns", [])
            },
            "pain_points_summary": extraction["pain_points_summary"],
            "use_cases_summary": extraction["use_cases_summary"],
            "validated": True
        }

        # Clear validation session state
        if 'validation_edits' in st.session_state:
            del st.session_state.validation_edits

        return updated_extraction

    if cancel_clicked:
        st.session_state.expansion_cancelled = True
        if 'validation_edits' in st.session_state:
            del st.session_state.validation_edits
        return {"action": "cancel"}

    return None  # Still editing


def show_validation_help():
    """Show help information for validation UI"""
    with st.expander("ℹ️ How to use validation"):
        st.markdown("""
**Why validate?**
The terms you confirm here will be used throughout the entire expanded document.
This ensures precision and prevents generic terms from leaking in.

**What to check:**
- **Entities**: Specific things mentioned (products, documents, systems)
- **Scenarios**: Realistic use cases in your own words

**Tips:**
- Use your exact terminology (don't generalize)
- Add entities if I missed important ones
- Edit scenarios to match your actual workflows
- Remove anything that doesn't apply

**What happens next:**
Your validated terms will be used to generate the full technical document
with document collections, search patterns, and use cases.
        """)
