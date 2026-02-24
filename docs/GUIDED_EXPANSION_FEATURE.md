# User-Guided Expansion Feature

## What Was Built

A **precision-focused prompt expansion feature** that allows users to validate and refine key concepts before full expansion. This addresses the problem of expanded prompts introducing generic terms or missing user-specific terminology.

### The Problem We Solved

**Before:** User submits brief prompt → System expands to 61K character document → Sometimes introduces generic terms or misses specific terminology → User gets demo with wrong terms

**After:** User submits brief prompt → System extracts key concepts → **User validates/edits concepts** → System expands using validated terms → User gets precise demo

### Key Benefits

1. **Precision**: User controls exactly which terms are used in the expansion
2. **Quality**: Prevents generic terms from leaking into demos
3. **Transparency**: User sees what the system understood before committing
4. **Flexibility**: Can add missing entities, remove irrelevant ones, refine scenarios

## How It Works

### Three-Stage Flow

**Stage 1: Domain Extraction (10 seconds)**
- System analyzes your brief input
- Extracts key entities, scenarios, domain, and industry
- Uses Claude Sonnet 4.5 for high-quality extraction
- Progress indicator: "🔍 Domain Analysis"

**Stage 2: User Validation (user-paced)**
- Shows extracted concepts in editable form
- You can:
  - Edit any entity or scenario
  - Add new ones you want included
  - Remove ones that don't fit
  - Adjust domain name and industry
- Progress indicator: "🔍 Domain Analysis" (validation checkpoint)

**Stage 3: Guided Expansion (30-60 seconds)**
- System builds enriched prompt with YOUR validated terms
- Expands to full technical document
- Uses your exact terminology throughout
- Progress indicator: "📝 Expansion"

### Visual Flow

```
📝 You submit: "I want a search demo for Italian restaurant menu photos"
    ↓
🔍 System extracts:
    Entities: ["Italian restaurant", "menu photos", "promotional graphics"]
    Scenarios: ["Restaurant owner searches for menu templates", ...]
    ↓
✏️  You validate/edit:
    ✓ Keep: "Italian restaurant", "menu photos"
    ✏️  Edit: "promotional graphics" → "marketing materials"
    ➕ Add: "seasonal campaigns"
    ↓
📝 System expands with YOUR terms:
    "...Italian restaurant menu photos...marketing materials...seasonal campaigns..."
    All data, queries, and scenarios use these exact terms
```

## How to Use It

### Quick Start

1. **Start the app** (already running at http://localhost:8501)
2. **Select "Expanded" complexity** in sidebar under Demo Generation Options
3. **Paste your prompt** - can be brief (1-2 sentences)
4. **Click "Generate Demo"**
5. **Wait for extraction** (~10 seconds)
6. **Review and edit** the extracted concepts:
   - Check entities match your terminology
   - Edit scenarios to be more specific
   - Add any missing terms
7. **Click "✅ Looks Good - Continue"**
8. **Wait for expansion** (~30-60 seconds)
9. **Review expanded document** and proceed with demo generation

### Example Prompts to Try

**Search Demo:**
```
I want a search demo for Adobe's marketing asset management.
Users search for content like "Italian food photos" and
"holiday promotional graphics". Need fuzzy matching and
semantic search for brand-consistent assets.
```

**Healthcare Search:**
```
Provider directory search. Doctors search for specialists
like "cardiologist in Boston accepting new patients".
Handle misspellings of provider names.
```

**Observability Demo:**
```
Monitor Kubernetes cluster performance. Track pod CPU usage,
memory consumption, identify microservices causing latency
in payment API. Alert on anomalies.
```

### Tips for Best Results

1. **Be specific in your prompt**: Mention exact terms you want in the demo
2. **Include examples**: "like X" or "such as Y" helps extraction
3. **During validation**:
   - Use your exact terminology (don't generalize)
   - Add domain-specific jargon you need
   - Remove any terms that feel generic
4. **Trust but verify**: The extraction is good, but you know your domain best

## Validation UI Features

### Editable Sections

**Domain & Industry:**
- Domain Name: Short name for what you're building
- Industry: Your vertical (Healthcare, Marketing, Finance, etc.)
- Primary Focus: One-sentence description of goals

**Key Entities:**
- List of specific terms/concepts from your input
- Click text box to edit any entity
- ➕ Add button to include new entities
- ❌ Remove button to delete irrelevant ones

**Scenarios:**
- Realistic use cases using your terminology
- Text areas for editing scenario descriptions
- ➕ Add button for new scenarios
- ❌ Remove button to delete scenarios

**Summary:**
- Entity count and scenario count
- Pain points summary
- Use cases summary

### Action Buttons

- **✅ Looks Good - Continue** (primary): Proceed with validated terms
- **🔄 Re-analyze**: Start over with extraction (if extraction was way off)
- **❌ Cancel**: Cancel expansion, return to normal flow

## Technical Details

### Architecture

**Service Layer:**
- `DomainExtractor` (uses Sonnet 4.5, temp=0.3 for precision)
- Extracts: domain, industry, entities, scenarios, document types, search patterns

**UI Layer:**
- `show_domain_validation()` - Interactive validation component
- `show_progress_indicator()` - Stage progress tracking
- `run_guided_expansion()` - Flow orchestration

**Integration:**
- Hooks into `create_demo.py` when "Expanded" complexity selected
- Falls back to standard expansion on errors
- Preserves all existing functionality

### Session State

```python
guided_expansion = {
    'stage': 'extracting' | 'validating' | 'expanding' | 'complete',
    'extraction': {...},  # Raw LLM output
    'validated_extraction': {...},  # User-edited version
    'expanded_content': str,  # Final document
    'demo_type': 'search' | 'analytics'
}
```

### Cost & Performance

- **Extraction**: ~$0.02, ~10 seconds
- **Expansion**: ~$0.30-0.60, ~30-60 seconds (unchanged)
- **Total**: ~$0.32-0.62 per demo
- **User validation**: No additional cost (user-paced)

**ROI**: Prevents wasted expansions with wrong terms (saves regenerations)

## Troubleshooting

### Extraction seems generic
- Your prompt might be too vague - add specific examples
- Click "Re-analyze" and try with more detail
- Or just edit the entities directly in the validation UI

### Extraction taking too long (>30 seconds)
- Network issue or API slowness
- Wait for timeout, system will fall back to standard expansion
- Check your API connectivity

### Can't add new entity/scenario
- Make sure text box has content before clicking ➕
- Click ➕ button, don't just press Enter
- Check browser console for any JavaScript errors

### Validation UI doesn't update after edit
- Streamlit should auto-rerun on button clicks
- If stuck, refresh browser page (may lose edits)
- File bug report if reproducible

### Expansion doesn't use my validated terms
- File bug - this is the core feature promise
- Check expanded document for your exact terms
- Provide feedback for prompt engineering improvements

## Success Metrics

After using this feature, you should observe:

- ✅ Expanded documents use YOUR terminology (not generic terms)
- ✅ Data descriptions contain keywords from YOUR scenarios
- ✅ Search queries reference YOUR entities
- ✅ Demo feels tailored to YOUR use case
- ✅ Less time spent editing generated content afterward

## Feedback

As you test this feature, please note:

1. **Extraction accuracy**: Did it capture your key terms?
2. **Validation UX**: Was editing easy and intuitive?
3. **Expansion quality**: Did it honor your validated terms?
4. **Performance**: Were timings acceptable?
5. **Overall value**: Does this improve your workflow?

## What's Next

Based on your testing and feedback, we can:

1. **Refine extraction prompts** for better accuracy
2. **Enhance validation UI** with additional features (reorder, bulk edit, etc.)
3. **Improve expansion prompts** to better honor validated terms
4. **Add templates** for common domains (healthcare, legal, finance)
5. **Track metrics** on extraction accuracy and edit frequency

---

**Status:** ✅ Ready for testing
**Model:** Claude Sonnet 4.5 (as requested)
**Philosophy:** Precision and quality over cost
**Location:** http://localhost:8501

## Quick Test

Try this now:

1. Go to http://localhost:8501
2. Set complexity to "Expanded"
3. Paste: "I want a search demo for finding Italian restaurant promotional photos and menu templates"
4. Click "Generate Demo"
5. Watch extraction, validate terms, continue
6. Observe how YOUR terms appear throughout the expanded document

**Expected result:** Expansion contains "Italian restaurant", "promotional photos", "menu templates" - not generic "food" or "images"
