# Guided Expansion Testing Guide

## Overview

The **Guided Expansion** feature adds user validation checkpoints to the prompt expansion process. Instead of directly expanding a brief prompt into a 61K character document, the system now:

1. **Extracts** key concepts from the user's input
2. **Validates** with the user - allowing them to edit entities and scenarios
3. **Expands** using the validated terms for maximum precision

## Architecture

### Components

**Service Layer:**
- `src/services/guided_expansion/domain_extractor.py` - Extracts key concepts using Sonnet 4.5
- `src/services/guided_expansion/__init__.py` - Service package exports

**UI Layer:**
- `src/ui/guided_expansion_flow.py` - Orchestrates multi-stage flow with state management
- `src/ui/components/guided_expansion/validation_ui.py` - Interactive validation components
- `src/ui/components/guided_expansion/__init__.py` - UI component exports

**Integration:**
- `src/ui/views/create_demo.py` - Main demo creation view using guided expansion

### Flow Diagram

```
User submits brief prompt
        ↓
[Stage: extracting]
  - Detect demo type (search/analytics)
  - Extract domain concepts with Sonnet
        ↓
[Stage: validating]
  - Show extracted entities/scenarios
  - User can edit, add, remove terms
  - User clicks "Looks Good - Continue"
        ↓
[Stage: expanding]
  - Build enriched prompt with validated terms
  - Call standard expansion with forced demo type
  - Return expanded document
        ↓
[Stage: complete]
  - Clear state and return to normal flow
```

## Testing Scenarios

### Test 1: Basic Search Demo (Adobe Marketing)

**Input Prompt:**
```
I want a search demo for Adobe's marketing asset management system.
Users need to find content like "Italian restaurant food menu photos"
and promotional graphics for seasonal campaigns.
```

**Expected Extraction:**
- **Domain Name**: "Marketing Asset Management" or similar
- **Industry**: "Marketing Technology"
- **Entities**: ["Italian restaurant", "food menu photos", "promotional graphics", "seasonal campaigns"]
- **Scenarios**: At least 2-3 scenarios mentioning the search examples

**Validation Test:**
1. Check entities are from input (not generic)
2. Edit an entity - change "Italian restaurant" to "Italian cuisine restaurants"
3. Add new entity - "brand guidelines"
4. Remove an entity if one seems off
5. Click "Looks Good - Continue"

**Expected Result:**
- Expanded document uses edited terms
- No generic terms leak in
- Search queries reference validated entities

### Test 2: Healthcare Search Demo

**Input Prompt:**
```
Healthcare provider network directory. Doctors want to search for
specialists like "cardiologist in Boston" or "pediatric oncologist
accepting new patients". Handle misspellings and fuzzy matching.
```

**Expected Extraction:**
- **Domain Name**: "Healthcare Provider Network" or "Provider Directory"
- **Industry**: "Healthcare"
- **Entities**: ["specialists", "cardiologist", "pediatric oncologist", "new patients"]
- **Scenarios**: Scenarios about finding doctors with specialties and locations

**Validation Test:**
1. Verify medical terms are preserved exactly
2. Add entity: "insurance networks"
3. Edit scenario to be more specific about location-based search
4. Click "Looks Good - Continue"

**Expected Result:**
- Custom domain library includes medical terminology
- Data descriptions reference validated medical specialties
- Search queries handle fuzzy matching for provider names

### Test 3: Observability Demo

**Input Prompt:**
```
Monitor Kubernetes cluster performance. Track pod CPU usage, memory consumption,
and identify which microservices are causing high latency in our payment API.
```

**Expected Extraction:**
- **Domain Name**: "Kubernetes Observability" or similar
- **Industry**: "Cloud Infrastructure" or "DevOps"
- **Entities**: ["Kubernetes cluster", "pod CPU usage", "memory consumption", "microservices", "payment API"]
- **Scenarios**: Scenarios about tracking metrics and identifying performance issues

**Validation Test:**
1. Verify technical terms preserved (don't generalize "Kubernetes" to "container platform")
2. Add entity: "service mesh latency"
3. Add scenario: "Alert when pod restarts exceed threshold"
4. Click "Looks Good - Continue"

**Expected Result:**
- Expanded document focuses on metrics and aggregations (not search)
- Query strategies include STATS, INLINESTATS
- Uses observability expansion template

### Test 4: Re-analyze Flow

**Input Prompt:**
```
Legal document search for case precedents.
```

**Test Steps:**
1. System extracts concepts
2. User reviews and sees extraction is too generic
3. User clicks "Re-analyze" button
4. System returns to extracting stage
5. User submits again or cancels

**Expected Result:**
- State resets to 'extracting'
- No errors or state corruption
- User can try again

### Test 5: Cancel Flow

**Input Prompt:**
```
Test prompt for cancellation.
```

**Test Steps:**
1. System extracts concepts
2. User reviews validation UI
3. User clicks "Cancel" button
4. System clears guided expansion state

**Expected Result:**
- State cleared from session
- Info message: "Expansion cancelled. You can submit your prompt again."
- User can submit new prompt

### Test 6: Fallback on Error

**Scenario:** Domain extraction fails (network error, API timeout)

**Expected Behavior:**
1. Error logged: "Extraction failed: {error}"
2. Error message shown to user: "❌ Failed to analyze input: {error}"
3. Fallback message: "Falling back to standard expansion..."
4. Standard expansion runs without validation
5. Demo generation continues

## Key Quality Checks

### Extraction Quality
- [ ] Entities are exact phrases from user input (not paraphrased)
- [ ] Scenarios reference user's specific examples
- [ ] Domain name is specific (not generic "Enterprise Search")
- [ ] Industry matches user's context
- [ ] 5-10 entities extracted
- [ ] 3-5 scenarios extracted

### Validation UI Quality
- [ ] All extracted terms are editable
- [ ] Can add new entities/scenarios
- [ ] Can remove entities/scenarios
- [ ] Changes persist between renders
- [ ] "Re-analyze" button works
- [ ] "Cancel" button works
- [ ] "Looks Good - Continue" proceeds to expansion

### Expansion Quality
- [ ] Expanded document uses validated entities exactly
- [ ] No generic terms introduced after validation
- [ ] Demo type detection correct (search vs analytics)
- [ ] Custom domain library generated with validated terms
- [ ] Data descriptions seed validated keywords

## Performance Targets

- **Extraction Time**: < 10 seconds (Sonnet 4.5 call)
- **Validation**: User-paced (no timeout)
- **Expansion Time**: 30-60 seconds (same as standard expansion)
- **Total Time**: 40-70 seconds + user validation time

## Cost Analysis

**Per Demo with Guided Expansion:**
- Domain Extraction: ~$0.02 (4K input, 1K output)
- Expansion: ~$0.30-0.60 (same as before)
- **Total**: ~$0.32-0.62 per demo

**Cost vs Quality Trade-off:**
- User explicitly chose "precision and quality over cost"
- Validation checkpoint prevents $0.60 expansions with wrong terms
- ROI: Prevents wasted generations

## Session State Management

### State Structure
```python
st.session_state.guided_expansion = {
    'stage': 'extracting' | 'validating' | 'expanding' | 'complete',
    'extraction': Dict,  # Raw extraction from LLM
    'validated_extraction': Dict,  # User-validated version
    'expanded_content': str,  # Final expanded document
    'demo_type': str  # 'search' or 'analytics'
}

st.session_state.validation_edits = {
    'entities': List[str],  # User's edited entity list
    'scenarios': List[str]  # User's edited scenario list
}
```

### State Lifecycle
1. **Init**: Create `guided_expansion` state on first prompt submission with expansion
2. **Extracting**: Set stage='extracting', run extraction, move to 'validating'
3. **Validating**: Show UI, track edits in `validation_edits`, wait for user action
4. **Expanding**: Build enriched prompt, run expansion, move to 'complete'
5. **Complete**: Return expanded content, delete `guided_expansion` state
6. **Cleanup**: Delete `validation_edits` on continue/cancel/reanalyze

## Integration Points

### Entry Point
`src/ui/views/create_demo.py` - When user enables "Expanded" complexity:

```python
if st.session_state.demo_complexity == "expanded":
    expanded_content = run_guided_expansion(prompt)
    if expanded_content:
        # Expansion complete - store and continue
        st.session_state.messages.append(...)
        st.session_state.ai_expansion_used = True
        st.session_state.demo_context['full_technical_context'] = expanded_content
        st.rerun()
    else:
        # Still in validation - don't rerun
        pass
```

### Dependency Chain
```
create_demo.py
    ↓
guided_expansion_flow.py
    ↓ (imports)
    ├─ components.guided_expansion.validation_ui
    ├─ services.guided_expansion.DomainExtractor
    ├─ message_processor.expand_brief_prompt
    └─ prompt_templates.detect_demo_type
```

## Troubleshooting

### Issue: "Module not found: guided_expansion"
**Solution:** Restart Streamlit app to pick up new module structure

### Issue: Extraction returns generic terms
**Solution:**
1. Check extraction prompt in `domain_extractor.py`
2. Verify temp=0.3 for precision
3. Add more specific instructions for domain

### Issue: Validation UI doesn't show edits
**Solution:**
1. Check `st.session_state.validation_edits` initialization
2. Verify session state persistence across reruns
3. Add debug logging to track state changes

### Issue: Expansion ignores validated terms
**Solution:**
1. Check `_build_enriched_prompt()` is using validated_extraction
2. Verify enriched prompt includes "use these exact terms" instruction
3. Check expansion prompt template honors validated context

## Next Steps

1. **User Testing**: Run through all test scenarios with real prompts
2. **Iteration**: Based on user feedback, refine:
   - Extraction prompt for better precision
   - Validation UI for easier editing
   - Enriched prompt structure for better guidance
3. **Documentation**: Update QUICK_START_GUIDE.md with guided expansion workflow
4. **Metrics**: Track extraction accuracy, validation edit frequency, expansion quality

## Success Criteria

- [ ] Extraction accuracy: 90%+ entities match user input exactly
- [ ] User validation: < 3 edits per extraction on average
- [ ] Expansion quality: 95%+ terms in expanded doc match validated terms
- [ ] User satisfaction: "This is much more precise than before"
- [ ] Performance: Total flow < 2 minutes including user validation

---

**Status:** ✅ Implementation complete - Ready for testing
**Model:** Claude Sonnet 4.5 for extraction (as requested)
**Focus:** Precision and quality over cost optimization
