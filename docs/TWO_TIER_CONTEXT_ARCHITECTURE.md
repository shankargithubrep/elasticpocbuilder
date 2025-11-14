# Two-Tier Context Architecture

## Overview

Implemented a two-tier context extraction system that preserves rich technical details when available while maintaining simple progress tracking.

## Problem Solved

**Before:** When users provided detailed technical documents with field names, metric categories, and implementation details, only basic fields were extracted (company, department, pain_points[], use_cases[]). All rich detail was lost, resulting in generic demos.

**After:** System now detects and preserves full technical documents while extracting basic fields for progress tracking. Rich context flows through to demo generation for high-fidelity output.

## Architecture

### Tier 1: Basic Context (Progress Tracking)

**Purpose:** Track conversation progress, display in sidebar, determine readiness

**Fields:**
- `company_name`: String
- `department`: String
- `industry`: String
- `pain_points`: List[String]
- `use_cases`: List[String]
- `scale`: String
- `metrics`: List[String]
- `demo_type`: String

### Tier 2: Full Technical Context (Generation Quality)

**Purpose:** Preserve rich technical details for high-fidelity demo generation

**Field:**
- `full_technical_context`: String (verbatim copy of rich technical document)

**Detection Criteria:**
A document is classified as "rich technical document" if it contains:
- Detailed use case sections with "Objective:", "Implementation:", "Key Metrics:", "Output/Benefits:"
- Specific field names in dot.notation (e.g., `mobile.procedure.type`, `system.cpu.pct`)
- Multiple metric categories with data sources (e.g., "via Metricbeat", "via APM")
- Detailed pain point sections with business impact explanations
- Technical documentation structure (headings, subheadings, bullet points)

## Data Flow

```
User Input (Detailed Technical Document)
    ↓
process_smart_message() (src/ui/message_processor.py)
    ↓
LLM extracts BOTH:
  1. Basic fields → demo_context (progress tracking)
  2. Full document → demo_context['full_technical_context'] (generation)
    ↓
st.session_state.demo_context stored with both tiers
    ↓
When user types "generate" → config created with both tiers
    ↓
Orchestrator passes config to strategy generators
    ↓
QueryStrategyGenerator._build_strategy_prompt() checks:
  - If full_technical_context exists → inject full document
  - Else → use basic fields
    ↓
LLM receives rich context → generates high-fidelity queries with:
  - Exact field names from document
  - Specific metric categories
  - Implementation-aware dataset designs
```

## Implementation Details

### 1. Message Processor (src/ui/message_processor.py)

**Lines 230-249:** Updated extraction prompt schema to include:
```json
{
  "is_rich_technical_document": false,
  "full_technical_context": null,
  ...
}
```

**Lines 360-366:** Store full technical context when detected:
```python
if result.get('is_rich_technical_document', False):
    full_context = result.get('full_technical_context')
    if full_context:
        context['full_technical_context'] = full_context
```

### 2. Create Demo View (src/ui/views/create_demo.py)

**Line 304:** Pass full context to orchestrator:
```python
config = {
    ...
    "full_technical_context": context.get("full_technical_context")
}
```

### 3. Query Strategy Generator (src/services/query_strategy_generator.py)

**Lines 159-196:** Conditional context section:
```python
full_context = context.get('full_technical_context')

if full_context:
    # Inject entire technical document
    context_section = f"""**Customer Context (Full Technical Document):**

{full_context}
...
```

### 4. Search Strategy Generator (src/services/search_strategy_generator.py)

**Lines 101-136:** Same conditional context injection for search/RAG demos

## AI Expansion Feature Enhancement

### Auto-Detection of Rich Documents (src/ui/message_processor.py:131-144)

The AI expansion feature now detects if input is already detailed and skips expansion:

```python
is_detailed = (
    len(brief_prompt) > 2000 or
    brief_prompt.count('\n') > 20 or
    'field names:' in brief_prompt.lower() or
    'key metrics' in brief_prompt.lower() or
    ...
)

if is_detailed:
    # Skip expansion, use as-is
    return f"""✅ **Detected comprehensive technical document**

{brief_prompt}"""
```

This prevents:
- Truncation of already-detailed documents
- Wasteful LLM calls to expand rich content
- Loss of formatting and structure

## User Workflows

### Workflow 1: Brief → Expanded → Rich Demo

1. User provides brief description: "T-Mobile Network Operations needs to detect 4G/5G failures"
2. **CHECK** "Generate detailed context with AI"
3. System expands to full technical document
4. System extracts both basic fields + full document
5. Generates high-fidelity demo with field names and metrics

### Workflow 2: Rich Document → Rich Demo

1. User provides full technical document (20+ pages with field names, metrics)
2. **CHECK** "Generate detailed context with AI" (optional - auto-detects)
3. System detects rich document, preserves verbatim
4. System extracts basic fields for progress tracking
5. Generates high-fidelity demo using full context

### Workflow 3: JSON → Basic Demo

1. User provides JSON with basic fields
2. **UNCHECK** "Generate detailed context with AI"
3. System extracts basic fields only
4. Generates standard demo with generic field names

## Benefits

### For Users

✅ **Preserve your work:** Detailed documents you've crafted are used fully, not summarized
✅ **Higher fidelity:** Demos reference exact field names, metrics, and implementations you specified
✅ **Flexible input:** Works with brief descriptions OR full technical documents
✅ **Automatic detection:** System knows when you've provided rich context

### For Developers

✅ **Backward compatible:** Existing demos using basic fields continue to work
✅ **Progressive enhancement:** Basic fields for tracking, full context for quality
✅ **Clean separation:** Progress tracking logic unchanged, generation logic enhanced
✅ **Testable:** Can test with/without rich context independently

## Testing Scenarios

### Test 1: Brief Prompt with AI Expansion
**Input:** "Salesforce Customer Success team preventing churn"
**Expected:** Expansion → Rich document → Both tiers extracted

### Test 2: Full Technical Document
**Input:** 30-page T-Mobile network operations document
**Expected:** Auto-detect rich → No expansion → Both tiers extracted

### Test 3: Basic JSON
**Input:** `{"company_name": "Acme", "department": "Sales"}`
**Expected:** No expansion → Basic tier only extracted

### Test 4: Sidebar Progress Tracking
**Expected:** Uses basic tier only (company, department, progress %)

### Test 5: Demo Generation Quality
**With rich context:** Exact field names (`mobile.procedure.type`)
**Without rich context:** Generic field names (`procedure_type`)

## Future Enhancements

1. **Visual indicator:** Show in sidebar when rich context is detected
2. **Context editor:** Allow users to refine full_technical_context before generation
3. **Template library:** Pre-built rich technical documents for common industries
4. **Diff view:** Compare basic vs rich context extraction results
5. **Quality metrics:** Track correlation between context richness and demo satisfaction

## Related Files

- `src/ui/message_processor.py` - Context extraction and storage
- `src/ui/views/create_demo.py` - Config preparation
- `src/services/query_strategy_generator.py` - Analytics strategy with rich context
- `src/services/search_strategy_generator.py` - Search strategy with rich context
- `src/framework/orchestrator.py` - Receives config with both tiers

## Rollout Notes

- ✅ No breaking changes - existing demos work as before
- ✅ No database migrations needed - session state only
- ✅ No user action required - automatic detection
- ✅ Immediate benefit for users with detailed prompts
