# Domain Keyword Library - Limitations & Recommendations

## Current Limitation

The domain keyword library (`src/services/domain_keyword_library.py`) has **predefined keyword sets** for only 9 domains:
- food_beverage
- fitness
- retail
- real_estate
- healthcare
- technology
- professional_services
- hospitality
- fashion

**Problem**: If you generate a search demo for a domain NOT in this list, or for a specialized subdomain, the keyword seeding may not be optimal.

---

## Example Scenarios

### Scenario 1: Healthcare Medical Imaging (⚠️ Partial Coverage)

**What User Wants**: Search demo for radiologists finding patient imaging (MRI, CT scans, X-rays)

**What Happens**:
1. ✅ Search narrative generates correctly:
   - domain: "healthcare"
   - exact_phrases: ["MRI scan", "CT scan", "radiology report"]

2. ⚠️ Data generation uses library:
   - Library has: "primary care", "cardiology", "hospital"
   - Library MISSING: "radiology", "imaging", "DICOM", "patient records"

3. ⚠️ Result:
   - "Professional image showcasing **MRI brain scan** with emphasis on **primary care**"
   - The exact phrase is there (good!) but supporting keywords are off-topic

**Impact**: Moderate - exact phrases work, but supporting content feels generic

---

### Scenario 2: Legal Document Search (❌ No Coverage)

**What User Wants**: Law firm searching case files, legal briefs, court documents

**What Happens**:
1. ✅ Search narrative generates correctly:
   - domain: "professional_services" (or "legal" if LLM chooses)
   - exact_phrases: ["legal brief", "court filing", "case law"]

2. ❌ Data generation:
   - If domain="legal" → NOT in library → **Fallback to "retail"**!
   - Library uses: "clothing", "boutique", "trendy", "affordable"

3. ❌ Result:
   - "Trendy image showcasing **legal brief** designed for boutique marketing"
   - NONSENSICAL combination!

**Impact**: Severe - descriptions are bizarre and unusable

---

### Scenario 3: Energy/Utilities Infrastructure (❌ No Coverage)

**What User Wants**: Utility company searching maintenance records, power grid documentation

**What Happens**:
1. ✅ Narrative: exact_phrases = ["power transformer", "grid maintenance", "electrical repair"]
2. ❌ Fallback to "retail" keywords
3. ❌ Result: "Luxury image showcasing **power transformer** with premium quality..."

**Impact**: Severe - completely inappropriate

---

## Root Cause Analysis

### Where the Limitation Comes From

```python
# src/services/domain_keyword_library.py
def get_keywords_for_domain(domain: str) -> Dict[str, List[str]]:
    return DOMAIN_LIBRARIES.get(domain, DOMAIN_LIBRARIES["retail"])
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                        Fallback to retail!
```

**The Issue**:
- If domain not found → uses "retail" keywords
- "retail" keywords (trendy, boutique, fashion) are inappropriate for most domains

---

## Why It Mostly Works (But Has Gaps)

### The Saving Grace: Exact Phrases Come From Narrative

The **most important keywords** (exact search terms) come from the **search narrative**, NOT the library:

```python
exact_phrase = scenario.get("exact_phrases", [])[0]  # "MRI scan" - FROM NARRATIVE ✅
supporting1 = random.choice(keywords["services"])     # "primary care" - FROM LIBRARY ⚠️
```

**Result**:
- Searches for "MRI scan" WILL find documents (exact phrase is seeded)
- But surrounding context might be generic ("primary care") instead of specific ("radiology")

**This is why it's not catastrophically broken - but it's not optimal either.**

---

## Recommendations

### Option 1: Expand the Library (Manual, Limited Scalability)

Add more domains and richer keywords:

```python
"healthcare": {
    "imaging": ["MRI scan", "CT scan", "X-ray", "ultrasound", "DICOM", "radiology"],
    "records": ["patient chart", "medical record", "clinical notes", "EHR", "EMR"],
    "lab": ["lab results", "pathology report", "blood work", "diagnostic test"],
    ...
},

"legal": {
    "documents": ["legal brief", "court filing", "motion", "deposition", "discovery"],
    "research": ["case law", "statute", "precedent", "legal opinion"],
    ...
},

"energy": {
    "infrastructure": ["power grid", "transformer", "substation", "transmission line"],
    "maintenance": ["equipment repair", "preventive maintenance", "outage"],
    ...
}
```

**Pros**:
- Immediate improvement for covered domains
- Full control over keywords

**Cons**:
- Manual maintenance required
- Can't cover every possible domain
- Still requires updates for new industries

---

### Option 2: Make Supporting Keywords Optional (Quick Fix)

Change the fallback behavior:

```python
def get_keywords_for_domain(domain: str) -> Dict[str, List[str]]:
    # Instead of falling back to retail, return generic/neutral keywords
    if domain not in DOMAIN_LIBRARIES:
        return {
            "contexts": ["organization", "business", "enterprise"],
            "descriptors": ["professional", "quality", "effective", "comprehensive"],
            "products": ["content", "materials", "resources", "documents"],
            "services": ["services", "solutions", "support", "operations"]
        }
    return DOMAIN_LIBRARIES[domain]
```

**Pros**:
- Generic keywords work for ANY domain
- No more "trendy boutique" for legal briefs!
- Minimal code change

**Cons**:
- Less rich/specific than domain-tailored keywords
- Descriptions feel more generic

---

### Option 3: LLM-Generated Supporting Keywords (Best, More Complex)

Instead of static library, generate supporting keywords dynamically:

```python
def get_keywords_for_scenario(scenario: Dict, llm_client) -> Dict[str, List[str]]:
    """Generate domain-appropriate keywords using LLM"""

    prompt = f"""Given this search scenario:
    - Domain: {scenario['domain']}
    - Description: {scenario['description']}
    - Exact phrases: {scenario['exact_phrases']}

    Generate 15-20 supporting keywords in these categories:
    - contexts: Where this occurs (e.g., "radiology department", "imaging center")
    - descriptors: Adjectives (e.g., "diagnostic", "high-resolution")
    - related_terms: Related concepts (e.g., "patient care", "clinical workflow")

    Return as JSON.
    """

    response = llm_client.messages.create(...)
    return parse_json(response)
```

**Pros**:
- Works for ANY domain automatically
- Keywords are scenario-specific
- No manual maintenance
- Rich, contextually appropriate vocabulary

**Cons**:
- Additional LLM call per scenario (~$0.01-0.05)
- Slight performance impact
- Need error handling for LLM failures

---

### Option 4: Hybrid Approach (Recommended)

Combine static library + LLM generation:

```python
def get_keywords_for_domain(domain: str, scenario: Dict = None, llm_client = None) -> Dict:
    # Try static library first (fast, free)
    if domain in DOMAIN_LIBRARIES:
        return DOMAIN_LIBRARIES[domain]

    # If not in library and LLM available, generate dynamically
    if llm_client and scenario:
        try:
            return generate_keywords_with_llm(scenario, llm_client)
        except Exception as e:
            logger.warning(f"LLM keyword generation failed: {e}")

    # Fallback to generic (better than "retail")
    return get_generic_keywords()
```

**Pros**:
- Best of both worlds
- Fast for common domains (uses library)
- Flexible for uncommon domains (uses LLM)
- Graceful degradation if LLM fails

**Cons**:
- More complex implementation
- Cost variability depending on domain

---

## Current State Assessment

### Domains That Work Well (Library Coverage)

✅ **food_beverage**: Comprehensive (cuisines, dishes, contexts)
✅ **fitness**: Good coverage (activities, products, benefits)
✅ **retail**: Comprehensive (products, styles, occasions)
✅ **real_estate**: Good (property types, features, locations)
⚠️ **healthcare**: Partial (generic services, missing specialized terms)
✅ **technology**: Decent (products, services, descriptors)
⚠️ **professional_services**: Generic (lacks specificity)
✅ **hospitality**: Good (hotels, tourism, restaurants overlap)
✅ **fashion**: Strong (styles, occasions, products)

### Domains That Need Work

❌ **Legal**: Not covered (falls back to retail)
❌ **Energy/Utilities**: Not covered
❌ **Manufacturing**: Not covered
❌ **Logistics/Supply Chain**: Not covered
❌ **Finance/Banking**: Not covered (would use professional_services, too generic)
❌ **Government/Public Sector**: Not covered
❌ **Education**: Mentioned in narrative prompt but not in library
❌ **Agriculture**: Not covered
❌ **Construction**: Not covered

### Healthcare Subdomains That Need Work

⚠️ **Medical Imaging/Radiology**: Partially covered ("diagnostic imaging" exists but no imaging-specific keywords)
❌ **Medical Records/Documentation**: Not covered
❌ **Laboratory/Pathology**: Not covered
❌ **Pharmacy**: Not covered
❌ **Medical Devices**: Not covered
⚠️ **Clinical Trials**: Not covered (would default to "research" which isn't in library)

---

## Immediate Action Items

### Quick Fix (1 hour)

**Change the fallback** from "retail" to generic:

```python
# In src/services/domain_keyword_library.py

GENERIC_KEYWORDS = {
    "contexts": ["organization", "business", "facility", "enterprise", "department"],
    "descriptors": ["professional", "quality", "comprehensive", "effective", "detailed"],
    "products": ["content", "materials", "resources", "assets", "documents"],
    "services": ["services", "solutions", "operations", "processes", "systems"],
    "benefits": ["efficiency", "quality", "performance", "effectiveness", "results"]
}

def get_keywords_for_domain(domain: str) -> Dict[str, List[str]]:
    return DOMAIN_LIBRARIES.get(domain, GENERIC_KEYWORDS)  # ← Use GENERIC instead of retail
```

**Impact**: Prevents bizarre combinations like "trendy legal brief"

---

### Medium-Term Enhancement (3-4 hours)

**Expand library for high-priority domains**:

Add specialized keywords for:
1. Legal (case law, filings, contracts)
2. Financial (transactions, accounts, investments)
3. Manufacturing (production, quality, equipment)
4. Healthcare subdomains (imaging, records, lab)

---

### Long-Term Solution (1-2 days)

**Implement hybrid LLM + static approach** (Option 4 above):

1. Keep static library for common domains (fast, free)
2. Add LLM generation for uncommon domains
3. Cache LLM-generated keywords per scenario
4. Monitor cost and performance

---

## Testing Strategy

### How to Test Domain Coverage

For each demo generation, log:
```
Domain: {scenario_domain}
Library status: [FOUND | NOT_FOUND → fallback]
Sample supporting keywords: {keywords_used[:5]}
```

**Red flags**:
- "trendy", "boutique", "fashion" appearing in non-retail demos
- Generic words ("business", "organization") when specific terms expected

### Validation Checklist

Before deploying, test with:
- [ ] Healthcare medical imaging demo
- [ ] Legal document search demo
- [ ] Financial transaction search demo
- [ ] Manufacturing quality records demo
- [ ] Energy infrastructure demo

For each, verify:
- Descriptions make sense for the domain
- Supporting keywords are appropriate
- No "retail" keywords leak into other domains

---

## Bottom Line

**Current State**:
- ✅ Works well for: food, fitness, retail, real estate, fashion, hospitality
- ⚠️ Works okay for: healthcare (generic), technology, professional services
- ❌ Breaks down for: legal, energy, manufacturing, finance, logistics, etc.

**Risk Level**:
- **Low risk** if generating demos for covered domains
- **Medium risk** for healthcare (exact phrases work, context is generic)
- **High risk** for uncovered domains (falls back to retail → bizarre descriptions)

**Recommended Immediate Action**:
Implement Quick Fix (change fallback to generic keywords) - takes 15 minutes, prevents worst-case scenarios

**Decision Points**:
1. How many different industries will use this tool?
   - Few → Expand library manually (Option 1)
   - Many → Hybrid LLM approach (Option 4)

2. Is slight cost increase acceptable?
   - Yes → LLM-generated keywords ($0.01-0.05 per scenario)
   - No → Expand static library

3. How important is demo quality for edge cases?
   - Critical → Implement hybrid approach
   - Moderate → Generic fallback is fine
