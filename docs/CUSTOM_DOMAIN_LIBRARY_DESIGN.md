# Custom Domain Library Generation - Architecture Design

## Concept

Generate a **custom keyword library** tailored to each demo using a single LLM call. This library is then used by all data generation to create rich, domain-appropriate descriptions.

## Why This Is Better Than Static Library

**Current Problem**:
- Static library has only 9 predefined domains
- Healthcare demo gets generic "primary care" keywords
- Legal demo falls back to "retail" → bizarre descriptions

**Solution**:
- Generate custom library from customer context + search scenarios
- One LLM call per demo (~$0.05-0.10)
- Library contains 50-100 domain-specific keywords perfect for THIS customer
- Reused for all 500-1000 descriptions in the demo

**Cost Comparison**:
- Static library: $0 but limited quality
- LLM per description: $10-20 per demo (too expensive!)
- **Custom library: $0.05-0.10 per demo** ✅ **Sweet spot!**

---

## Pipeline Integration

### Current Flow
```
1. Context Extraction (user prompt → structured context)
2. Search Narrative Generation (8-10 scenarios with exact_phrases)
3. Query Strategy Generation (16+ queries)
4. Data Specification Expansion (often fails, JSON errors)
5. Data Generation (uses static library)
   └─ seed_description_with_keywords() → DOMAIN_LIBRARIES["healthcare"]
6. Indexing
7. Query Generation
```

### New Flow (With Custom Library)
```
1. Context Extraction
2. Search Narrative Generation (8-10 scenarios)
   └─ Example scenarios:
       - "radiology_imaging_search": ["MRI scan", "CT scan", "X-ray"]
       - "patient_records_lookup": ["medical chart", "EHR", "clinical notes"]
3. 🆕 Custom Domain Library Generation
   Input: customer context + search scenarios
   Output: {
     "imaging_terms": ["radiology", "diagnostic imaging", "PACS", "DICOM"],
     "record_types": ["patient chart", "medical records", "clinical documentation"],
     "contexts": ["imaging center", "radiology department", "hospital"],
     "descriptors": ["diagnostic-quality", "high-resolution", "HIPAA-compliant"],
     "specialties": ["radiology", "nuclear medicine", "interventional imaging"]
   }
   Cost: ~$0.05-0.10 (one call)
4. Query Strategy Generation
5. Data Specification Expansion (optional, can fail)
6. Data Generation (uses CUSTOM library)
   └─ seed_description_with_keywords() → custom_library["imaging_terms"]
7. Indexing
8. Query Generation
```

**Key Insight**: The custom library is generated AFTER search narrative so it can extract keywords from ALL scenarios!

---

## Implementation Design

### Step 1: Create CustomDomainLibraryGenerator

**File**: `src/services/custom_domain_library_generator.py`

```python
"""
Custom Domain Library Generator

Generates a custom keyword library tailored to the specific demo
based on customer context and search scenarios.
"""

import logging
import json
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class CustomDomainLibraryGenerator:
    """Generates custom domain keyword libraries for each demo"""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def generate_library(
        self,
        customer_context: Dict[str, Any],
        search_narrative: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Generate custom keyword library from customer context and search scenarios.

        Args:
            customer_context: Company, industry, pain points, use cases
            search_narrative: Search scenarios with exact_phrases, semantic_phrases

        Returns:
            Custom keyword library with 5-8 categories, 10-20 keywords each
            {
              "category_1": ["keyword1", "keyword2", ...],
              "category_2": ["keyword1", "keyword2", ...],
              ...
            }
        """
        logger.info("Generating custom domain library from context and scenarios")

        # Build prompt
        prompt = self._build_library_prompt(customer_context, search_narrative)

        # Call LLM
        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text
            library = self._extract_json(response_text)

            # Validate library structure
            self._validate_library(library)

            logger.info(f"Generated custom library with {len(library)} categories")
            return library

        except Exception as e:
            logger.error(f"Failed to generate custom library: {e}")
            # Return fallback generic library
            return self._get_fallback_library()

    def _build_library_prompt(
        self,
        customer_context: Dict[str, Any],
        search_narrative: Dict[str, Any]
    ) -> str:
        """Build the LLM prompt for custom library generation"""

        company = customer_context.get("company_name", "Unknown")
        industry = customer_context.get("industry", "Unknown")
        department = customer_context.get("department", "Unknown")

        # Extract all search scenarios
        scenarios = search_narrative.get("search_scenarios", [])

        # Collect all unique phrases across scenarios
        all_exact_phrases = []
        all_semantic_phrases = []
        all_domains = set()

        for scenario in scenarios:
            all_exact_phrases.extend(scenario.get("exact_phrases", []))
            all_semantic_phrases.extend(scenario.get("semantic_phrases", []))
            all_domains.add(scenario.get("domain", "unknown"))

        # Format scenario summaries
        scenario_summaries = []
        for i, scenario in enumerate(scenarios[:10], 1):  # Limit to 10
            desc = scenario.get("description", "Unknown")
            exact = ", ".join(scenario.get("exact_phrases", [])[:3])
            scenario_summaries.append(f"{i}. {desc}\n   Key terms: {exact}")

        prompt = f"""You are generating a custom keyword library for a search demo.

## Customer Context
- Company: {company}
- Industry: {industry}
- Department: {department}

## Search Scenarios ({len(scenarios)} total)
{chr(10).join(scenario_summaries)}

## Collected Search Terms
**Exact phrases across all scenarios** ({len(set(all_exact_phrases))} unique):
{', '.join(list(set(all_exact_phrases))[:30])}

**Semantic concepts** ({len(set(all_semantic_phrases))} unique):
{', '.join(list(set(all_semantic_phrases))[:30])}

## Your Task

Generate a custom keyword library with 5-8 categories of domain-specific keywords. These will be used to create rich, realistic descriptions for {industry} industry content.

**Output 5-8 categories**, each with **10-20 keywords**. Categories should be relevant to the search scenarios above.

**Suggested category types** (adapt to the domain):
- **primary_terms**: Core subject matter terms (e.g., for healthcare imaging: "radiology", "diagnostic imaging", "medical scans")
- **item_types**: Specific items/documents (e.g., "MRI scan", "CT scan", "X-ray", "ultrasound")
- **contexts**: Where this occurs (e.g., "imaging center", "radiology department", "hospital")
- **descriptors**: Adjectives and qualifiers (e.g., "diagnostic-quality", "high-resolution", "HIPAA-compliant")
- **processes**: Actions and workflows (e.g., "image acquisition", "scan interpretation", "results reporting")
- **specialties**: Sub-domains or specializations (e.g., "interventional radiology", "nuclear medicine")
- **related_concepts**: Broader related terms (e.g., "patient care", "clinical workflow", "medical technology")

**Important Guidelines**:
- Extract keywords FROM the search scenarios above (use exact_phrases and semantic_phrases as primary source)
- Add complementary terms that fit the domain
- Use terminology that professionals in this industry would actually use
- Make keywords specific enough to be meaningful but general enough to reuse
- Each category should have 10-20 keywords (not too few, not too many)
- Keywords should sound natural in descriptions like "Professional image showcasing {{keyword}}"

**Example Output** (Healthcare Imaging):

```json
{{
  "imaging_modalities": [
    "MRI scan", "CT scan", "X-ray imaging", "ultrasound", "PET scan",
    "mammography", "fluoroscopy", "nuclear medicine scan", "DEXA scan",
    "angiography", "cardiac imaging", "brain imaging", "body imaging"
  ],
  "clinical_contexts": [
    "radiology department", "imaging center", "diagnostic facility",
    "hospital radiology", "outpatient imaging", "emergency imaging",
    "interventional suite", "mobile imaging unit", "teleradiology"
  ],
  "quality_descriptors": [
    "diagnostic-quality", "high-resolution", "contrast-enhanced",
    "multiplanar", "3D reconstructed", "DICOM-compliant", "HIPAA-secure",
    "AI-assisted", "real-time", "detailed visualization", "anatomically precise"
  ],
  "clinical_applications": [
    "disease diagnosis", "treatment planning", "surgical guidance",
    "follow-up monitoring", "screening studies", "trauma assessment",
    "oncology imaging", "cardiac evaluation", "neurological assessment"
  ],
  "workflow_terms": [
    "image acquisition", "scan protocol", "radiologist review",
    "results reporting", "PACS integration", "image archiving",
    "study comparison", "multi-modality correlation", "clinical correlation"
  ],
  "medical_specialties": [
    "radiology", "nuclear medicine", "interventional radiology",
    "neuroradiology", "musculoskeletal imaging", "cardiac imaging",
    "breast imaging", "pediatric radiology", "emergency radiology"
  ]
}}
```

Generate the custom keyword library now for **{industry} - {department}**. Return ONLY valid JSON.
"""

        return prompt

    def _extract_json(self, text: str) -> Dict[str, List[str]]:
        """Extract JSON from LLM response"""
        import re

        # Remove markdown code blocks
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]

        # Parse JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Response text: {text[:500]}")
            raise

    def _validate_library(self, library: Dict[str, List[str]]):
        """Validate library structure"""
        if not isinstance(library, dict):
            raise ValueError("Library must be a dictionary")

        if len(library) < 3:
            raise ValueError(f"Library must have at least 3 categories, got {len(library)}")

        for category, keywords in library.items():
            if not isinstance(keywords, list):
                raise ValueError(f"Category '{category}' must have a list of keywords")
            if len(keywords) < 5:
                raise ValueError(f"Category '{category}' must have at least 5 keywords, got {len(keywords)}")

    def _get_fallback_library(self) -> Dict[str, List[str]]:
        """Return generic fallback library if generation fails"""
        logger.warning("Using fallback generic library")
        return {
            "primary_terms": ["content", "materials", "resources", "assets", "documents"],
            "contexts": ["organization", "business", "facility", "department", "enterprise"],
            "descriptors": ["professional", "quality", "comprehensive", "effective", "detailed"],
            "processes": ["operations", "workflows", "procedures", "activities", "services"],
            "applications": ["business use", "organizational needs", "operational requirements"]
        }
```

---

### Step 2: Update Search Strategy Generator

**File**: `src/services/search_strategy_generator.py`

Add custom library generation after search narrative:

```python
def generate_strategy(self, context: Dict) -> Dict:
    """Generate search strategy with custom domain library"""

    # STEP 1: Generate search narrative (existing)
    from src.services.search_narrative_generator import SearchNarrativeGenerator
    narrative_gen = SearchNarrativeGenerator(self.llm_client)
    search_narrative = narrative_gen.generate_narrative({...})

    # STEP 2: Generate CUSTOM domain library (NEW!)
    from src.services.custom_domain_library_generator import CustomDomainLibraryGenerator
    library_gen = CustomDomainLibraryGenerator(self.llm_client)
    custom_library = library_gen.generate_library(
        customer_context=context,
        search_narrative=search_narrative
    )

    logger.info(f"Generated custom library with {len(custom_library)} categories")

    # Store custom library in strategy for use during data generation
    strategy_json["search_narrative"] = search_narrative
    strategy_json["custom_domain_library"] = custom_library  # NEW!

    # ... rest of method
```

---

### Step 3: Update Domain Keyword Library to Use Custom Library

**File**: `src/services/domain_keyword_library.py`

Add function to merge custom library with static fallback:

```python
def get_keywords_for_domain(
    domain: str,
    custom_library: Dict[str, List[str]] = None
) -> Dict[str, List[str]]:
    """
    Get keyword library for specific domain.

    Args:
        domain: Domain name (e.g., 'food_beverage', 'healthcare')
        custom_library: Optional custom library generated for this demo

    Returns:
        Dictionary of keyword categories
    """
    # Priority 1: Use custom library if available (best quality)
    if custom_library and len(custom_library) > 0:
        logger.info(f"Using custom library with {len(custom_library)} categories")
        return custom_library

    # Priority 2: Use static library if domain exists
    if domain in DOMAIN_LIBRARIES:
        logger.info(f"Using static library for domain: {domain}")
        return DOMAIN_LIBRARIES[domain]

    # Priority 3: Generic fallback (better than "retail")
    logger.warning(f"Domain '{domain}' not in library, using generic keywords")
    return GENERIC_KEYWORDS


def seed_description_with_keywords(
    scenario: Dict[str, Any],
    use_exact: bool = True,
    asset_type: str = "image",
    index: int = 0,
    custom_library: Dict[str, List[str]] = None  # NEW parameter!
) -> str:
    """Generate description with keywords from custom or static library"""

    domain = scenario.get("domain", "retail")
    keywords = get_keywords_for_domain(domain, custom_library)  # Pass custom library!

    # ... rest of function unchanged
```

---

### Step 4: Update Module Generator to Pass Custom Library

**File**: `src/framework/generation/module_generator.py`

Update data generation prompt to include custom library:

```python
def _build_search_demo_prompt(self, config, query_strategy, data_specifications):
    """Build prompt for search demo data generation"""

    # Extract custom library from query_strategy
    custom_library = query_strategy.get("custom_domain_library", {})
    search_narrative = query_strategy.get("search_narrative", {})

    # Build Section 0: SEARCH NARRATIVE (existing)
    narrative_section = f"""
    ## 🔍 SEARCH NARRATIVE
    {json.dumps(search_narrative, indent=2)}

    ## 📚 CUSTOM DOMAIN LIBRARY (NEW!)
    You have access to a custom keyword library generated specifically for this demo:
    {json.dumps(custom_library, indent=2)}

    **CRITICAL - Use this custom library for keyword seeding:**
    ```python
    from src.services.domain_keyword_library import seed_description_with_keywords

    # Pass the custom library!
    custom_library = {json.dumps(custom_library)}

    description = seed_description_with_keywords(
        scenario=scenario,
        use_exact=True,
        asset_type=asset_type,
        index=i,
        custom_library=custom_library  # Use custom library!
    )
    ```
    """

    # ... rest of prompt
```

---

## Cost Analysis

### Per Demo Costs

**Search Demo Generation**:
1. Context expansion (if used): ~$0.10
2. Search narrative (8-10 scenarios): ~$0.15
3. **Custom library generation**: ~$0.05-0.10 ← NEW
4. Query strategy: ~$0.20
5. Data specification expansion: ~$0.15
6. Data generation: ~$0.25
7. Demo guide: ~$0.20

**Total**: ~$1.10-1.30 per demo (was ~$1.05 before)

**Cost increase**: **$0.05-0.10 per demo** (4.5% increase)

**Value gained**: Domain-specific keywords for ANY industry without manual library maintenance!

---

## Benefits Summary

### Compared to Static Library

✅ **Works for ANY domain** (legal, energy, manufacturing, finance, etc.)
✅ **Customer-specific keywords** (extracts from their actual pain points and use cases)
✅ **Scenario-aware** (uses exact_phrases from ALL scenarios)
✅ **No manual maintenance** (auto-adapts to new industries)
✅ **Better quality** (healthcare imaging gets "radiology", "DICOM", not just "primary care")

### Compared to LLM-per-Description

✅ **Much cheaper** ($0.10 vs $10-20 per demo)
✅ **Faster** (1 call vs 1000 calls)
✅ **Consistent** (same library used for all descriptions in a demo)
✅ **Cacheable** (could cache libraries for similar demos)

---

## Implementation Plan

### Phase 1: Core Implementation (2-3 hours)

1. Create `custom_domain_library_generator.py`
2. Update `search_strategy_generator.py` to call library generator
3. Update `domain_keyword_library.py` to accept custom_library parameter
4. Update `module_generator.py` to pass custom library in prompt

### Phase 2: Testing (1 hour)

1. Test with healthcare imaging demo
2. Test with legal document search demo
3. Test with energy infrastructure demo
4. Verify keyword quality and relevance

### Phase 3: Optimization (optional, 2 hours)

1. Add library caching for similar demos
2. Add library validation and quality checks
3. Add fallback strategies if library generation fails
4. Monitor cost and adjust token limits

---

## Example Output

### Healthcare Medical Imaging Demo

**Search Narrative** (existing):
```json
{
  "search_scenarios": [
    {
      "scenario_id": "radiology_imaging_search",
      "exact_phrases": ["MRI scan", "CT scan", "radiology report"]
    }
  ]
}
```

**Custom Library** (NEW!):
```json
{
  "imaging_modalities": [
    "MRI scan", "CT scan", "X-ray imaging", "ultrasound", "PET scan",
    "DICOM imaging", "nuclear medicine", "interventional radiology"
  ],
  "clinical_contexts": [
    "radiology department", "imaging center", "diagnostic facility",
    "hospital radiology", "PACS workstation", "teleradiology network"
  ],
  "quality_descriptors": [
    "diagnostic-quality", "high-resolution", "contrast-enhanced",
    "multiplanar", "3D reconstructed", "HIPAA-compliant", "AI-assisted"
  ],
  "workflow_terms": [
    "image acquisition", "scan protocol", "radiologist review",
    "PACS integration", "study comparison", "results reporting"
  ]
}
```

**Generated Description** (using custom library):
```
"Diagnostic-quality MRI brain scan from radiology department imaging center.
High-resolution multiplanar imaging with 3D reconstructed views perfect for
radiologist review and clinical correlation. HIPAA-compliant DICOM imaging
optimized for PACS integration and study comparison workflows."
```

**Search Result**:
- Query: "MRI scan radiology report imaging"
- Score: **32.5** (was 16.2 with static library)
- Match quality: Excellent - ALL keywords present and contextually appropriate!

---

## Decision Points

### Should We Implement This?

**Pros**:
- ✅ Solves the domain coverage problem completely
- ✅ Minimal cost increase ($0.05-0.10 per demo, 4.5%)
- ✅ Works for ANY industry (legal, energy, manufacturing, etc.)
- ✅ Better quality even for covered domains (more specific)
- ✅ No manual maintenance required
- ✅ Natural fit in existing pipeline

**Cons**:
- ⚠️ Additional LLM call (potential failure point)
- ⚠️ Slight complexity increase
- ⚠️ Need to test across many domains

**Recommendation**: **YES - Implement this!**

The benefits far outweigh the costs. This is the "right" solution architecturally.

---

## Alternative: Quick Fix First, Then Custom Library

**Option 1: Full implementation now** (2-3 hours)
- Implement custom library generation
- Deploy and test
- Ready for ANY domain immediately

**Option 2: Quick fix + gradual rollout** (30 min now, 3 hours later)
- **Now**: Change fallback from "retail" to "generic" (prevents worst cases)
- **Later**: Implement custom library generation (when you have time)
- **Benefit**: Immediate fix, full solution when ready

**Recommendation**: Option 2 if time-constrained, Option 1 if you want the full solution now.
