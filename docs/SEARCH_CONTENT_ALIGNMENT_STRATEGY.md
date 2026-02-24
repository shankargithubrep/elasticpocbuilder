# Search Demo Content Alignment Strategy

## Problem Statement

**Current Issue**: Search demos generate queries that look for specific phrases (e.g., "Italian food", "holiday sale", "fitness apparel") but the data generation creates generic templated content that doesn't contain these phrases. This results in:
- Low relevancy scores
- Poor search results that don't demonstrate search quality
- Unconvincing demos where queries return irrelevant results
- Inability to showcase BM25 vs semantic search differences

**Example from Project Beacon Demo**:
- Query searches: `MATCH(asset_description, "Italian food restaurant")`
- Generated descriptions: "High-quality Image asset for Holiday Sale campaign targeting Food Beverage businesses. Features professional design with strong visual appeal."
- Result: No actual mentions of "Italian food" or "restaurant" → poor relevance

## Root Cause Analysis

### Current Generation Flow
```
1. Generate query strategy → defines WHAT queries will run
2. Generate data independently → creates generic content
3. Queries don't match data → poor results
```

### The Disconnect
- **Query Generator**: Creates sophisticated search scenarios with specific search terms
- **Data Generator**: Creates templated descriptions with random combinations of generic terms
- **No Bridge**: No mechanism ensures query terms appear in realistic distributions in the data

## Proposed Solutions

### Strategy 1: Query Narrative First (RECOMMENDED)

**Concept**: Generate a "search narrative" that defines key search scenarios, then generate data to support those scenarios.

**Flow**:
```
1. Define Search Narrative
   └─ Key search scenarios (e.g., "Italian restaurant promotion", "fitness apparel sale")
   └─ Target phrases for each scenario
   └─ Expected result distribution (highly relevant, partially relevant, not relevant)

2. Generate Query Strategy (as we do now)
   └─ Uses search narrative to create realistic queries

3. Generate Data WITH narrative context
   └─ X% of documents highly relevant to scenario 1
   └─ Y% of documents highly relevant to scenario 2
   └─ Z% of documents are "noise" (not relevant to any scenario)
```

**Example Search Narrative**:
```json
{
  "search_scenarios": [
    {
      "scenario_id": "italian_restaurant_promotion",
      "description": "Small Italian restaurant looking for assets for summer promotion",
      "key_phrases": [
        "Italian food",
        "pasta",
        "pizza",
        "restaurant",
        "dining",
        "cuisine"
      ],
      "semantic_concepts": [
        "Mediterranean flavors",
        "family dining",
        "authentic Italian"
      ],
      "target_distribution": {
        "exact_matches": 15,  // 15 documents contain exact phrases
        "semantic_matches": 25,  // 25 contain related concepts
        "partial_matches": 20,  // 20 have some relevance
        "noise": 40  // 40 are unrelated
      }
    },
    {
      "scenario_id": "fitness_apparel_sale",
      "description": "Gym owner promoting new activewear line",
      "key_phrases": [
        "fitness",
        "workout",
        "athletic wear",
        "gym apparel",
        "activewear"
      ],
      "semantic_concepts": [
        "performance clothing",
        "sports fashion",
        "exercise gear"
      ],
      "target_distribution": {
        "exact_matches": 12,
        "semantic_matches": 20,
        "partial_matches": 18,
        "noise": 50
      }
    }
  ]
}
```

**Advantages**:
- ✅ Queries and data are inherently aligned
- ✅ Can demonstrate BM25 vs semantic differences (exact vs concept matching)
- ✅ Realistic relevancy score distributions
- ✅ Compelling demo narratives

**Challenges**:
- Requires LLM call to generate narrative first
- Adds complexity to data generation
- Need to balance multiple scenarios in one dataset

---

### Strategy 2: LLM-Generated Rich Content

**Concept**: Use LLM to generate realistic descriptions instead of templates.

**Current Approach** (Template-Based):
```python
desc = f'High-quality {atype} asset for {theme} campaign targeting {category} businesses.'
# Result: Generic, no specific keywords
```

**Proposed Approach** (LLM-Generated):
```python
# Pass context to LLM
context = {
    "asset_type": "image",
    "business_category": "food_beverage",
    "campaign_theme": "summer_promotion",
    "target_keywords": ["Italian food", "pasta", "restaurant"]
}

prompt = f"""Generate a realistic marketing asset description for:
- Asset Type: {context['asset_type']}
- Business: {context['business_category']}
- Campaign: {context['campaign_theme']}
- Should naturally include: {', '.join(context['target_keywords'])}

Generate 1-2 sentences that sound like a real marketing asset description."""

desc = llm.generate(prompt)
# Result: "Vibrant food photography showcasing authentic Italian pasta dishes,
#          perfect for restaurant summer menu promotions featuring fresh Mediterranean cuisine."
```

**Advantages**:
- ✅ Rich, realistic content
- ✅ Natural inclusion of search terms
- ✅ Semantic variation (not just exact matches)
- ✅ Can generate at scale

**Challenges**:
- 💰 Cost: 1000 descriptions × $0.01/call = $10 per demo
- ⏱️ Time: Slower generation (though can batch)
- 🎲 Consistency: Need to ensure distribution of topics

---

### Strategy 3: Keyword Seeding with Domain Libraries

**Concept**: Pre-define domain-specific content libraries and seed keywords into templated descriptions.

**Implementation**:
```python
# Define domain-specific libraries
FOOD_KEYWORDS = {
    "cuisines": ["Italian", "Mexican", "Chinese", "Thai", "French", "Japanese"],
    "dishes": ["pasta", "pizza", "sushi", "tacos", "curry", "steak"],
    "contexts": ["restaurant", "catering", "food truck", "cafe", "bistro"]
}

FITNESS_KEYWORDS = {
    "activities": ["yoga", "running", "cycling", "weightlifting", "CrossFit"],
    "products": ["activewear", "gym apparel", "workout clothes", "athletic wear"],
    "contexts": ["fitness center", "gym", "sports club", "wellness studio"]
}

# Seeded description generation
def generate_description(category, theme):
    # Pick relevant keyword library
    if category == "food_beverage":
        keywords = FOOD_KEYWORDS
        cuisine = random.choice(keywords["cuisines"])
        dish = random.choice(keywords["dishes"])
        context = random.choice(keywords["contexts"])

        return f"Professional food photography featuring {cuisine} {dish}, " \
               f"ideal for {context} menu promotions. High-resolution image " \
               f"showcasing authentic cuisine in appetizing presentation."

    # Similar for other categories...
```

**Advantages**:
- ✅ Fast (no LLM calls needed)
- ✅ Controlled keyword distribution
- ✅ Predictable, testable
- ✅ Can tune exact vs semantic balance

**Challenges**:
- Requires manual curation of keyword libraries
- Less natural-sounding than LLM-generated
- Need libraries for many domains

---

### Strategy 4: Hybrid Approach (PRACTICAL)

**Concept**: Combine narrative planning with keyword seeding.

**Flow**:
```
1. Generate Search Narrative (LLM - 1 call per demo)
   └─ Defines 3-5 key search scenarios
   └─ Extracts key phrases for each

2. Create Keyword Distribution Plan
   └─ Assign documents to scenarios
   └─ Define exact vs semantic vs noise split

3. Generate Data with Keyword Seeding
   └─ Use templates with keyword libraries
   └─ Seed exact phrases for exact matches
   └─ Use related terms for semantic matches
   └─ Use unrelated content for noise

4. Generate Queries (as we do now)
   └─ Queries naturally align with narrative
```

**Example**:
```python
# After narrative generation
narrative = {
    "scenario_1": {
        "name": "Italian restaurant promotion",
        "exact_phrases": ["Italian food", "pasta", "pizza"],
        "semantic_phrases": ["Mediterranean", "cuisine", "dining"],
        "target_docs": 20
    },
    "scenario_2": {
        "name": "Fitness apparel sale",
        "exact_phrases": ["activewear", "gym apparel", "workout clothes"],
        "semantic_phrases": ["athletic", "performance wear", "sports fashion"],
        "target_docs": 15
    },
    "noise": {
        "target_docs": 65  # Rest are unrelated
    }
}

# During data generation
for i in range(100):
    if i < 20:  # First 20 docs for scenario 1
        desc = generate_description_with_keywords(
            scenario=narrative["scenario_1"],
            use_exact=i < 10  # Half exact, half semantic
        )
    elif i < 35:  # Next 15 for scenario 2
        desc = generate_description_with_keywords(
            scenario=narrative["scenario_2"],
            use_exact=i < 25
        )
    else:  # Rest are noise
        desc = generate_generic_description()
```

**Advantages**:
- ✅ Best of both worlds: aligned + fast
- ✅ One LLM call for narrative, rest is templated
- ✅ Predictable distributions
- ✅ Cost-effective

---

## Recommended Implementation Plan

### Phase 1: Add Search Narrative Generation (High Priority)

**Changes Needed**:
1. New service: `SearchNarrativeGenerator`
   - Input: Customer context, pain points, industry
   - Output: 3-5 search scenarios with key phrases
   - One LLM call per demo (~5 seconds)

2. Update `SearchStrategyGenerator`
   - Include narrative in strategy JSON
   - Pass to query generator

3. Update `DataGenerator` base prompt
   - Include narrative context
   - Provide scenario assignments for each document

**Expected Result**: Data naturally contains search terms at realistic frequencies

---

### Phase 2: Add Keyword Seeding Library (Medium Priority)

**Changes Needed**:
1. Create `src/services/domain_keywords.py`
   - Libraries for: retail, food service, healthcare, fitness, real estate, etc.
   - Organized by: exact terms, semantic terms, context words

2. Update data generation templates
   - Check narrative scenarios
   - Seed appropriate keywords from libraries

**Expected Result**: Even better alignment without additional LLM cost

---

### Phase 3: Optional LLM-Enhanced Content (Low Priority)

**For high-value demos only**:
- Add flag: `use_llm_content_generation: true`
- Batch LLM calls (20 descriptions at a time)
- Use for semantic_text fields only (most important for search)

---

## Testing Plan

### Test 1: Baseline Current Approach
```bash
# Generate demo with current approach
# Measure: Average relevancy scores for search queries
# Expected: Low scores (< 5.0)
```

### Test 2: With Search Narrative
```bash
# Add narrative generation
# Measure: Average relevancy scores
# Expected: Significant improvement (> 10.0)
```

### Test 3: With Keyword Seeding
```bash
# Add keyword libraries
# Measure: Exact match percentages
# Expected: 10-15% of results are exact matches
```

### Test 4: Query Result Quality
```bash
# Run scripted queries
# Measure: % of queries returning compelling results
# Expected: > 80% have good results
```

---

## Sample Output Comparison

### Current Approach
**Query**: `MATCH(asset_description, "Italian food restaurant")`

**Top Result** (Score: 2.3):
> "High-quality Image asset for Holiday Sale campaign targeting Food Beverage businesses. Features professional design with strong visual appeal."

❌ No mention of Italian, food, or restaurant despite being food industry

---

### With Search Narrative + Keyword Seeding
**Query**: `MATCH(asset_description, "Italian food restaurant")`

**Top Result** (Score: 15.7):
> "Professional food photography showcasing authentic Italian pasta and pizza dishes. Perfect for restaurant menu promotions, featuring rustic presentation and Mediterranean ingredients. High-resolution images ideal for Italian cuisine marketing."

✅ Contains exact phrases: "Italian", "restaurant", "food"
✅ Contains semantic concepts: "pasta", "pizza", "cuisine", "dishes"
✅ Natural, realistic description
✅ High relevancy score

**Result 2** (Score: 12.3):
> "Vibrant dining scene imagery for casual restaurant marketing. Features family-style Mediterranean cuisine in warm, inviting atmosphere. Ideal for food service industry promotional campaigns."

✅ Semantic match: "dining", "cuisine", "food service"
✅ Related concepts: "Mediterranean" (related to Italian)
✅ Good score but not exact match (demonstrates BM25 vs semantic!)

**Result 8** (Score: 3.1):
> "Modern minimalist template for technology startup presentations. Clean design with bold typography and tech-focused imagery."

✅ Low score for unrelated content (good contrast!)

---

## Success Metrics

### Immediate Goals
- [ ] Average query relevancy score > 10.0
- [ ] Top 3 results for each query are relevant
- [ ] At least 10% exact phrase matches in dataset
- [ ] Clear difference between BM25 and semantic results

### Long-term Goals
- [ ] Demo-ready without manual data editing
- [ ] Customer can run any reasonable search query
- [ ] Search quality comparable to production systems
- [ ] Showcase advanced ES|QL search capabilities

---

## Next Steps

1. **Review this strategy** - Does the approach make sense?
2. **Choose implementation path** - Hybrid approach recommended
3. **Create POC** - Test narrative generation with one demo
4. **Measure improvement** - Compare before/after scores
5. **Roll out** - Apply to all search demos

---

**Document Status**: Draft for Review
**Created**: 2026-01-22
**Author**: Claude Code Analysis
