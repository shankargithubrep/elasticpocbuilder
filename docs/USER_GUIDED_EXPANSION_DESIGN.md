# User-Guided Expansion - Quality-First Design

## Philosophy

**Goal**: Maximize precision and quality through user validation and guidance
**Non-Goal**: Cost optimization (use best models, multiple passes as needed)
**Approach**: Interactive, iterative expansion with user checkpoints

---

## User Experience Flow

### Current Experience (No Validation)

```
User submits prompt
    ↓
[8 seconds of waiting...]
    ↓
61K character document appears
    ↓
User hopes it's correct 🤞
    ↓
Generate demo (no way to refine)
```

**Problems**:
- No way to correct misunderstandings
- All-or-nothing (accept or start over)
- User can't guide the expansion
- Errors compound through entire generation

---

### Proposed Experience (User-Guided)

```
┌─────────────────────────────────────────────────────────┐
│ STEP 1: Initial Understanding                           │
│ User submits brief prompt                               │
│ System extracts key concepts                            │
│ Time: 3-5 seconds                                       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ VALIDATION CHECKPOINT 1: Domain & Key Terms            │
│                                                         │
│ 🤖 I understand you're building a SEARCH demo for:     │
│                                                         │
│ **Domain**: Marketing Asset Management                 │
│ **Industry**: Marketing Technology / SaaS              │
│                                                         │
│ **Key Entities I'll Use**:                             │
│ • Italian food ✏️ [edit]                               │
│ • product photos ✏️ [edit]                             │
│ • email templates ✏️ [edit]                            │
│ • social media graphics ✏️ [edit]                      │
│ • restaurant marketing ✏️ [edit]                       │
│ • ➕ Add more...                                        │
│                                                         │
│ **Search Scenarios I Identified**:                     │
│ 1. Restaurant owner searches for Italian food content  │
│    ✏️ [edit] ❌ [remove]                                │
│ 2. Marketing manager finds social media templates      │
│    ✏️ [edit] ❌ [remove]                                │
│ 3. Small business discovers email campaign assets      │
│    ✏️ [edit] ❌ [remove]                                │
│ ➕ Add scenario...                                      │
│                                                         │
│ [✅ Looks Good - Continue] [✏️ Edit] [🔄 Re-analyze]   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ STEP 2: Targeted Expansion                             │
│ Using your validated terms...                          │
│ Time: 8-10 seconds                                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ VALIDATION CHECKPOINT 2: Document Collections          │
│                                                         │
│ 📚 I've defined these document collections:            │
│                                                         │
│ **1. Marketing Assets Collection**                     │
│ - Contains: product photos, social media graphics      │
│ - Searches: "Italian food", "restaurant marketing"     │
│ - Size: ~500K-5M documents                             │
│ ✏️ [refine] ✅ [approve]                                │
│                                                         │
│ **2. Template Library**                                │
│ - Contains: email templates, social post designs       │
│ - Searches: by campaign type, visual style             │
│ - Size: ~5K-15K templates                              │
│ ✏️ [refine] ✅ [approve]                                │
│                                                         │
│ ➕ Add collection...                                    │
│                                                         │
│ [✅ Approve All] [✏️ Refine Individually] [🔄 Regen]   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ STEP 3: Use Case Generation                            │
│ Using your approved collections...                     │
│ Time: 6-8 seconds                                      │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ VALIDATION CHECKPOINT 3: Use Cases Preview             │
│                                                         │
│ 🎯 I've created these search use cases:                │
│                                                         │
│ **1. Natural Language Content Discovery**              │
│ - Searches: "Italian food" → pasta photos, menus      │
│ - Strategy: Hybrid search (BM25 + semantic)           │
│ ✅ ❌                                                    │
│                                                         │
│ **2. Typo-Tolerant Fuzzy Matching**                   │
│ - Searches: "promtional grafics" → finds promotions   │
│ - Strategy: Fuzzy matching with edit distance         │
│ ✅ ❌                                                    │
│                                                         │
│ **3. Campaign Asset Discovery**                        │
│ - Searches: coordinated assets for campaigns          │
│ - Strategy: Multi-faceted filtering                   │
│ ✅ ❌                                                    │
│                                                         │
│ [✅ Accept All] [✏️ Customize] [➕ Add Use Case]       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ FINAL STEP: Complete Document Assembly                 │
│ Assembling final technical document...                 │
│ Time: 5 seconds                                        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│ ✅ READY TO GENERATE                                    │
│                                                         │
│ Expanded Context:                                      │
│ • Domain: Marketing Asset Management                   │
│ • Collections: 2 defined                               │
│ • Use Cases: 6 search scenarios                        │
│ • Document Size: 18,543 characters                     │
│                                                         │
│ [📋 Review Full Document] [Generate Demo] [Save Draft] │
└─────────────────────────────────────────────────────────┘
```

**Benefits**:
- User validates understanding at each stage
- Can edit/refine terms before they propagate
- Catches errors early
- User feels in control
- Higher confidence in output quality

---

## Technical Architecture

### Component Structure

```
src/services/
├── guided_expansion/
│   ├── __init__.py
│   ├── domain_extractor.py         # Step 1: Extract key concepts
│   ├── collection_generator.py     # Step 2: Generate doc collections
│   ├── usecase_generator.py        # Step 3: Generate use cases
│   └── document_assembler.py       # Final: Assemble complete doc
│
src/ui/
├── components/
│   ├── validation_ui.py            # Interactive validation widgets
│   ├── term_editor.py              # Edit key terms/entities
│   └── checkpoint_review.py        # Checkpoint review interface
```

### Session State Structure

```python
st.session_state.guided_expansion = {
    "stage": "domain_extraction",  # domain_extraction | collections | use_cases | final

    # Stage 1: Domain Extraction
    "domain": {
        "name": "Marketing Asset Management",
        "industry": "Marketing Technology / SaaS",
        "validated": False,
        "user_edits": []
    },

    # Stage 1: Key Terms
    "key_terms": {
        "entities": ["Italian food", "product photos", ...],
        "scenarios": ["Restaurant owner searches...", ...],
        "document_types": ["product photos", "email templates", ...],
        "validated": False,
        "user_edits": []
    },

    # Stage 2: Collections
    "collections": [
        {
            "name": "Marketing Assets Collection",
            "purpose": "...",
            "fields": [...],
            "validated": False,
            "user_notes": ""
        }
    ],

    # Stage 3: Use Cases
    "use_cases": [
        {
            "title": "Natural Language Content Discovery",
            "description": "...",
            "validated": True,
            "user_selected": True
        }
    ],

    # Feedback Loop
    "refinement_history": [
        {"stage": "domain_extraction", "user_feedback": "Add 'seasonal campaigns'"},
        {"stage": "collections", "user_feedback": "Reduce to 500K docs"}
    ]
}
```

---

## Implementation Details

### Step 1: Domain Extraction Service

**File**: `src/services/guided_expansion/domain_extractor.py`

```python
"""
Domain Extraction for User-Guided Expansion

Extracts key concepts from user input for validation before full expansion.
Uses best available model for quality (Opus 4.5 if available, else Sonnet).
"""

import logging
from typing import Dict, List, Any
import json

logger = logging.getLogger(__name__)


class DomainExtractor:
    """Extracts domain concepts from brief user input"""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def extract(self, user_input: str, demo_type: str) -> Dict[str, Any]:
        """
        Extract key concepts for user validation.

        Args:
            user_input: Brief user prompt (JSON or text)
            demo_type: 'search' or 'observability'

        Returns:
            {
                "domain": {
                    "name": "Marketing Asset Management",
                    "industry": "Marketing Technology",
                    "primary_focus": "Content discovery and search"
                },
                "key_terms": {
                    "entities": ["Italian food", "product photos", ...],
                    "scenarios": ["Restaurant owner searches...", ...],
                    "document_types": ["product photos", "email templates", ...],
                    "search_patterns": ["natural language", "typo-tolerant", ...]
                },
                "pain_points_summary": "3 pain points identified",
                "use_cases_summary": "8 use cases mentioned"
            }
        """
        logger.info(f"Extracting domain concepts for {demo_type} demo")

        prompt = self._build_extraction_prompt(user_input, demo_type)

        try:
            # Use best model for quality (Opus > Sonnet > Haiku)
            model = self._select_best_model()

            response = self.llm_client.messages.create(
                model=model,
                max_tokens=4000,
                temperature=0.3,  # Lower temp for precise extraction
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text
            extraction = self._parse_json(response_text)

            logger.info(f"Extracted {len(extraction['key_terms']['entities'])} entities")
            return extraction

        except Exception as e:
            logger.error(f"Domain extraction failed: {e}", exc_info=True)
            return self._get_fallback_extraction(user_input)

    def _build_extraction_prompt(self, user_input: str, demo_type: str) -> str:
        """Build extraction prompt tailored to demo type"""

        if demo_type == 'search':
            focus_instructions = """
**SEARCH DEMO FOCUS**:
Extract terms related to:
- Documents/content being searched (e.g., "patient records", "product photos")
- Search queries users perform (e.g., "Italian food", "promotion graphics")
- Types of searches (semantic, fuzzy, exact, geographic)
"""
        else:
            focus_instructions = """
**OBSERVABILITY DEMO FOCUS**:
Extract terms related to:
- Systems being monitored (e.g., "Kubernetes cluster", "payment API")
- Metrics being tracked (e.g., "CPU usage", "response time")
- Data sources (e.g., "Metricbeat", "APM agents")
"""

        prompt = f"""Extract key concepts from this customer input for validation.

{focus_instructions}

**Customer Input**:
```
{user_input}
```

**CRITICAL INSTRUCTIONS**:
1. Extract ONLY terms present in the user's input
2. Use the user's EXACT wording (don't paraphrase)
3. Identify 5-10 most important entities/concepts
4. Capture 3-5 realistic scenarios using user's language
5. Return precise JSON structure

**Output Format** (return ONLY this JSON):
```json
{{
  "domain": {{
    "name": "Concise domain name using user's terminology",
    "industry": "Industry vertical from user's context",
    "primary_focus": "One sentence: what they're trying to accomplish"
  }},
  "key_terms": {{
    "entities": ["List of 5-10 specific entities the user mentioned"],
    "scenarios": [
      "Scenario 1 in user's words",
      "Scenario 2 in user's words",
      "Scenario 3 in user's words"
    ],
    "document_types": ["Types of content/data mentioned"],
    "search_patterns": ["Search approaches implied or stated"]
  }},
  "pain_points_summary": "X pain points identified: [brief list]",
  "use_cases_summary": "Y use cases mentioned: [brief list]"
}}
```

Extract now. Use user's exact terminology.
"""
        return prompt

    def _select_best_model(self) -> str:
        """Select best available model for quality"""
        # Priority: Opus 4.5 > Sonnet 4.5 > Sonnet 3.5
        # For quality-focused extraction, always use Opus if available

        try:
            # Try Opus 4.5 first
            test_response = self.llm_client.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            logger.info("Using Claude Opus 4.5 for extraction (highest quality)")
            return "claude-opus-4-5-20251101"
        except:
            logger.info("Using Claude Sonnet 4.5 for extraction")
            return "claude-sonnet-4-5-20250929"

    def _parse_json(self, text: str) -> Dict:
        """Parse JSON from LLM response"""
        import re

        # Remove markdown code blocks
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        return json.loads(text)

    def _get_fallback_extraction(self, user_input: str) -> Dict:
        """Fallback extraction if LLM fails"""
        logger.warning("Using fallback extraction")
        return {
            "domain": {
                "name": "Enterprise Demo",
                "industry": "Technology",
                "primary_focus": "Data analysis and search"
            },
            "key_terms": {
                "entities": ["data", "search", "analytics"],
                "scenarios": ["User searches for information"],
                "document_types": ["documents", "records"],
                "search_patterns": ["keyword search"]
            },
            "pain_points_summary": "Multiple pain points identified",
            "use_cases_summary": "Several use cases mentioned"
        }
```

---

### Step 2: Interactive Validation UI

**File**: `src/ui/components/validation_ui.py`

```python
"""
Interactive Validation UI Components

Provides editable, user-friendly interfaces for validating extracted concepts.
"""

import streamlit as st
from typing import List, Dict


def show_domain_validation(extraction: Dict) -> Dict:
    """
    Display domain extraction for user validation with edit capability.

    Returns:
        Updated extraction with user modifications
    """
    st.markdown("### 🤖 Domain Understanding Checkpoint")
    st.markdown("I've analyzed your input. Please review and refine:")

    # Domain Section
    st.markdown("#### Domain & Industry")
    col1, col2 = st.columns(2)

    with col1:
        domain_name = st.text_input(
            "Domain Name",
            value=extraction["domain"]["name"],
            key="domain_name",
            help="Concise name for what you're building"
        )

    with col2:
        industry = st.text_input(
            "Industry",
            value=extraction["domain"]["industry"],
            key="industry",
            help="Your industry vertical"
        )

    primary_focus = st.text_area(
        "Primary Focus",
        value=extraction["domain"]["primary_focus"],
        key="primary_focus",
        help="What you're trying to accomplish",
        height=60
    )

    # Key Entities Section
    st.markdown("#### Key Entities & Terms")
    st.caption("These terms will be used throughout the expansion:")

    entities = extraction["key_terms"]["entities"]

    # Editable entity list
    edited_entities = []
    for i, entity in enumerate(entities):
        col1, col2 = st.columns([4, 1])
        with col1:
            edited = st.text_input(
                f"Entity {i+1}",
                value=entity,
                key=f"entity_{i}",
                label_visibility="collapsed"
            )
            edited_entities.append(edited)
        with col2:
            if st.button("❌", key=f"remove_entity_{i}"):
                entities.pop(i)
                st.rerun()

    # Add new entity
    if st.button("➕ Add Entity"):
        st.session_state.new_entity_input = True

    if st.session_state.get("new_entity_input"):
        new_entity = st.text_input("New entity:", key="new_entity")
        if st.button("Add"):
            edited_entities.append(new_entity)
            st.session_state.new_entity_input = False
            st.rerun()

    # Scenarios Section
    st.markdown("#### Search Scenarios")
    st.caption("Realistic scenarios using these terms:")

    scenarios = extraction["key_terms"]["scenarios"]
    edited_scenarios = []

    for i, scenario in enumerate(scenarios):
        col1, col2 = st.columns([4, 1])
        with col1:
            edited = st.text_area(
                f"Scenario {i+1}",
                value=scenario,
                key=f"scenario_{i}",
                height=60,
                label_visibility="collapsed"
            )
            edited_scenarios.append(edited)
        with col2:
            if st.button("❌", key=f"remove_scenario_{i}"):
                scenarios.pop(i)
                st.rerun()

    # Add new scenario
    if st.button("➕ Add Scenario"):
        st.session_state.new_scenario_input = True

    if st.session_state.get("new_scenario_input"):
        new_scenario = st.text_area("New scenario:", key="new_scenario")
        if st.button("Add"):
            edited_scenarios.append(new_scenario)
            st.session_state.new_scenario_input = False
            st.rerun()

    # Action Buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Looks Good - Continue", type="primary"):
            # Update extraction with edits
            extraction["domain"]["name"] = domain_name
            extraction["domain"]["industry"] = industry
            extraction["domain"]["primary_focus"] = primary_focus
            extraction["key_terms"]["entities"] = edited_entities
            extraction["key_terms"]["scenarios"] = edited_scenarios
            extraction["validated"] = True
            return extraction

    with col2:
        if st.button("🔄 Re-analyze Input"):
            st.session_state.reanalyze_requested = True
            return None

    with col3:
        if st.button("❌ Start Over"):
            st.session_state.clear()
            st.rerun()

    return None  # Still editing


def show_collections_validation(collections: List[Dict]) -> List[Dict]:
    """Display generated collections for validation"""

    st.markdown("### 📚 Document Collections Checkpoint")
    st.markdown("Review the collections I've defined:")

    validated_collections = []

    for i, collection in enumerate(collections):
        with st.expander(f"**{collection['name']}**", expanded=(i==0)):
            # Show collection details
            st.markdown(f"**Purpose**: {collection['purpose']}")
            st.markdown(f"**Document Type**: {collection['document_type']}")
            st.markdown(f"**Volume**: {collection['volume']}")

            # Show sample fields
            st.markdown("**Key Search Fields**:")
            for field in collection['fields'][:5]:  # Show first 5
                st.code(f"{field['name']} ({field['type']}): {field['description']}")

            # Validation controls
            col1, col2, col3 = st.columns(3)
            with col1:
                approve = st.checkbox("✅ Approve", key=f"approve_coll_{i}")
            with col2:
                refine = st.button("✏️ Refine", key=f"refine_coll_{i}")
            with col3:
                remove = st.button("❌ Remove", key=f"remove_coll_{i}")

            if approve:
                collection['validated'] = True
                validated_collections.append(collection)
            elif refine:
                # Show refinement UI (to be implemented)
                pass

    # Action buttons
    st.markdown("---")
    all_validated = all(c.get('validated') for c in validated_collections)

    if all_validated and len(validated_collections) > 0:
        if st.button("✅ Approve All - Continue", type="primary"):
            return validated_collections

    return None  # Still validating


def show_progress_indicator(current_stage: str):
    """Show progress through guided expansion stages"""

    stages = {
        "domain_extraction": ("🔍 Domain Analysis", 0),
        "collections": ("📚 Collections", 1),
        "use_cases": ("🎯 Use Cases", 2),
        "final": ("✅ Complete", 3)
    }

    current_idx = stages.get(current_stage, ("", 0))[1]

    # Progress bar
    progress = (current_idx + 1) / len(stages)
    st.progress(progress)

    # Stage indicators
    cols = st.columns(len(stages))
    for i, (stage_name, (label, idx)) in enumerate(stages.items()):
        with cols[i]:
            if idx < current_idx:
                st.success(f"✅ {label}")
            elif idx == current_idx:
                st.info(f"⏳ {label}")
            else:
                st.text(f"⏸️ {label}")
```

---

## Integration Plan

### Phase 1: Core Extraction & Validation (Today - 3-4 hours)

1. Create `domain_extractor.py` ✅
2. Create `validation_ui.py` ✅
3. Update `create_demo.py` to use guided flow
4. Test with Adobe Project Beacon example

### Phase 2: Collection & Use Case Stages (Tomorrow - 4-5 hours)

1. Create `collection_generator.py`
2. Create `usecase_generator.py`
3. Add validation UIs for each stage
4. Implement refinement loops

### Phase 3: Final Assembly & Polish (Day 3 - 2-3 hours)

1. Create `document_assembler.py`
2. Add "Review Full Document" viewer
3. Add save/load draft capability
4. End-to-end testing

---

## Success Metrics

Track these to validate quality improvements:

| Metric | Target |
|--------|--------|
| User confidence in expansion | >4.5/5 |
| Corrections needed per expansion | <2 |
| Domain term precision | >98% |
| Time to validated expansion | <5 minutes |
| User satisfaction with control | >4.7/5 |
| Successful demo generations | >95% |

**Quality is the priority** - we'll use best models and take the time needed for validation.
