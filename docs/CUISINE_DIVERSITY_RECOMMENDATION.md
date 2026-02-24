# Cuisine Diversity Recommendation

## Your Question

> "I'm wondering if we should have also generated some of the descriptions to have different cuisines? Or is that too complex and too much to expect from this generator?"

## TL;DR: Yes, We Should - And It's Already Designed For It!

**Recommendation**: ✅ **Generate diverse, cuisine-specific descriptions**

**Complexity**: ⚠️ **Low-Medium** - The architecture is already in place (search narrative + domain library), we just need to fix the pipeline break.

---

## Current State Analysis

### What the Search Narrative Generated

Looking at `query_strategy.json` for your latest demo, the search narrative created **5 diverse scenarios**:

1. **Summer Coffee Shop Promotion** (cold brew, iced drinks)
   - Domain: `food_beverage`
   - Exact phrases: "cold brew coffee", "iced drinks", "summer beverages"

2. **Boutique Loyalty Program** (fashion retail)
   - Domain: `fashion`
   - Exact phrases: "loyalty program", "customer rewards"

3. **Real Estate Open House** (property marketing)
   - Domain: `real_estate`
   - Exact phrases: "open house", "property showing"

4. **Yoga Studio Wellness** (fitness/meditation)
   - Domain: `fitness`
   - Exact phrases: "yoga classes", "meditation sessions"

5. **Dental Practice Cleaning** (healthcare)
   - Domain: `healthcare`
   - Exact phrases: "teeth cleaning", "dental checkup"

### What's Missing: Italian Restaurant Scenario

The query searches for **"Italian restaurant food menu photos pasta pizza"** but there's **NO Italian scenario** in the narrative!

This suggests one of two things:
1. The LLM didn't generate a restaurant food scenario (it should have based on Project Beacon's context)
2. OR there was one but it got lost when data spec expansion failed

---

## Why Cuisine Diversity Matters

### Demo Impact

**Without cuisine diversity** (current state):
```
Query: "Italian restaurant food menu photos pasta pizza"

Results:
1. "restaurant businesses... rustic aesthetic" (score: 16)
2. "restaurant businesses... professional appeal" (score: 14)
3. "restaurant businesses... modern style" (score: 12)
```

**Problem**: All results say "restaurant" but lack specificity. Looks generic.

**With cuisine diversity**:
```
Query: "Italian restaurant food menu photos pasta pizza"

Results:
1. "Authentic Italian trattoria featuring handmade pasta, wood-fired pizza..." (score: 32)
2. "Classic Italian bistro menu with risotto, lasagna, tiramisu..." (score: 28)
3. "Traditional pizzeria showcasing Neapolitan-style pizza..." (score: 26)

And noise results:
15. "Mexican restaurant tacos and burritos..." (score: 4)
16. "Chinese dim sum and noodles..." (score: 3)
17. "Japanese sushi and ramen..." (score: 3)
```

**Benefit**:
- ✅ Top results are HIGHLY specific and relevant
- ✅ Score contrast is dramatic (32 vs 3 = 10x difference!)
- ✅ Shows semantic search power (ignores Mexican/Chinese for Italian)
- ✅ Demo feels realistic - like an actual asset library

### Real-World Alignment

Actual DAM/marketing platforms DO have diverse content:
- Restaurant stock photos include Italian, Mexican, Chinese, Japanese, etc.
- Fashion has different styles (bohemian, streetwear, formal, athletic)
- Real estate has various property types (condo, house, commercial, land)

Generic "restaurant photos" without cuisine type is actually **LESS realistic** than diverse cuisine-specific content.

---

## Implementation Complexity

### Option 1: Expand Search Narrative Scenarios (RECOMMENDED)

**What**: Generate 8-10 search scenarios instead of 5, with more domain coverage

**Complexity**: **LOW** ⭐
- Already working: `SearchNarrativeGenerator` creates scenarios
- Just increase scenario count in prompt from 5 to 10
- LLM will naturally create diverse scenarios

**Changes needed**:
```python
# In src/services/search_narrative_generator.py

# Current: "Generate 3-5 search scenarios"
# Change to: "Generate 8-10 diverse search scenarios"

# Expected output for Project Beacon:
scenarios = [
    # Food & Beverage (3 scenarios)
    {"domain": "food_beverage", "exact_phrases": ["Italian restaurant", "pasta", "pizza"]},
    {"domain": "food_beverage", "exact_phrases": ["coffee shop", "cold brew", "espresso"]},
    {"domain": "food_beverage", "exact_phrases": ["Mexican restaurant", "tacos", "burritos"]},

    # Fashion (2 scenarios)
    {"domain": "fashion", "exact_phrases": ["boutique", "loyalty program"]},
    {"domain": "fashion", "exact_phrases": ["seasonal collection", "spring fashion"]},

    # Real Estate (2 scenarios)
    {"domain": "real_estate", "exact_phrases": ["open house", "property listing"]},
    {"domain": "real_estate", "exact_phrases": ["luxury home", "modern condo"]},

    # Fitness (2 scenarios)
    {"domain": "fitness", "exact_phrases": ["yoga studio", "wellness"]},
    {"domain": "fitness", "exact_phrases": ["HIIT training", "gym"]},

    # Other
    {"domain": "healthcare", "exact_phrases": ["dental", "teeth cleaning"]}
]
```

**Estimated effort**: 30 minutes

---

### Option 2: Expand Domain Keyword Library

**What**: Add more cuisine types to domain library

**Complexity**: **LOW** ⭐⭐
- Domain library exists: `src/services/domain_keyword_library.py`
- Currently has: `food_beverage` domain
- Add more specific sub-domains or expand keyword pool

**Changes needed**:
```python
# In src/services/domain_keyword_library.py

DOMAIN_LIBRARIES = {
    "food_beverage": {
        # Add more cuisines
        "cuisines": [
            "Italian", "Mexican", "Chinese", "Japanese", "Thai",
            "Indian", "French", "Mediterranean", "American", "Korean"
        ],
        "italian_dishes": ["pasta", "pizza", "risotto", "lasagna", "tiramisu"],
        "mexican_dishes": ["tacos", "burritos", "enchiladas", "quesadillas"],
        "chinese_dishes": ["dumplings", "noodles", "fried rice", "dim sum"],
        "japanese_dishes": ["sushi", "ramen", "tempura", "teriyaki"],
        # ... etc
    }
}
```

**Estimated effort**: 1 hour

---

### Option 3: Fix Data Spec Expansion Pipeline (CRITICAL)

**What**: Fix the JSON parsing bug that's preventing narrative from reaching data generator

**Complexity**: **MEDIUM** ⭐⭐⭐
- This is the ROOT CAUSE of current problem
- Even with perfect scenarios, if expansion fails, keyword seeding won't work

**Changes needed**:
```python
# In src/services/data_specification_expander.py

1. Increase max_tokens: 16000 → 24000
2. Add retry logic with exponential backoff
3. Improve JSON extraction regex
4. Add validation before parsing
5. CRITICAL: Pass search narrative even if expansion fails

# In src/framework/orchestrator.py

def _generate_demo_module(self, context, query_strategy):
    narrative = query_strategy.get("search_narrative", {})

    try:
        expanded = self.expander.expand_data_specifications(...)
    except Exception as e:
        logger.warning(f"Expansion failed: {e}")
        expanded = None  # Continue with narrative

    # ALWAYS pass narrative
    config["search_narrative"] = narrative
```

**Estimated effort**: 2-3 hours

---

## Recommended Approach

### Phase 1: Quick Reliability Fix (2-3 hours)

**Goal**: Make narrative injection resilient

1. ✅ **Fix expansion bypass** (Option 3)
   - Pass narrative even when expansion fails
   - Ensures keyword seeding always works

2. ✅ **Expand scenario count** (Option 1)
   - Generate 8-10 scenarios instead of 5
   - More domain coverage

**Result**: Cuisine diversity working reliably

---

### Phase 2: Expand Library (optional, 1-2 hours)

**Goal**: Richer keyword pool

1. ✅ **Expand domain library** (Option 2)
   - More cuisines, more specific keywords
   - Better semantic variation

**Result**: Higher quality, more natural descriptions

---

## Expected Results

### With 8-10 Diverse Scenarios

For Project Beacon (DAM for SMBs), expect scenarios like:

**Food & Beverage** (30% of assets, 3 scenarios):
- Italian restaurant (pasta, pizza, risotto)
- Coffee shop (cold brew, espresso, latte)
- Mexican restaurant (tacos, burritos, salsa)

**Fashion/Retail** (25% of assets, 2-3 scenarios):
- Boutique loyalty program
- Seasonal collection launch
- Fashion promotion graphics

**Real Estate** (20% of assets, 2 scenarios):
- Open house events
- Luxury property listings

**Fitness/Wellness** (15% of assets, 2 scenarios):
- Yoga/meditation studio
- HIIT/gym training

**Professional Services** (10% of assets, 1-2 scenarios):
- Healthcare (dental)
- Legal/consulting

### Data Distribution Example

For 1000 assets in `marketing_assets` dataset:

```
Italian restaurant content:    80 assets (8%)
  ├─ Exact matches:           14 assets ("Italian pasta pizza")
  ├─ Semantic matches:        24 assets ("Mediterranean cuisine")
  └─ Noise:                   42 assets (other topics)

Mexican restaurant content:    70 assets (7%)
  ├─ Exact matches:           12 assets ("Mexican tacos burritos")
  ├─ Semantic matches:        22 assets ("Latin food")
  └─ Noise:                   36 assets

Coffee shop content:          90 assets (9%)
  ├─ Exact matches:           16 assets ("cold brew iced coffee")
  ├─ Semantic matches:        26 assets ("artisan beverages")
  └─ Noise:                   48 assets

... (7 more scenarios)

Generic/other content:       400 assets (40%)
```

### Query Results With Diversity

**Query**: "Italian restaurant food menu photos pasta pizza"

**Top 5 Results**:
```
1. Score: 32 - "Authentic Italian trattoria menu featuring fresh pasta dishes and wood-fired Neapolitan pizza..."
2. Score: 28 - "Classic Italian bistro showcasing handmade lasagna, risotto, and tiramisu desserts..."
3. Score: 26 - "Traditional Italian cuisine with spaghetti carbonara, margherita pizza, and antipasti..."
4. Score: 24 - "Italian restaurant menu board displaying pasta varieties and artisan pizza options..."
5. Score: 22 - "Mediterranean dining featuring Italian specialties: bruschetta, caprese salad, pasta..."
```

**Bottom 5 Results** (important for contrast!):
```
96. Score: 4 - "Mexican restaurant tacos and burritos promotional graphics..."
97. Score: 3 - "Chinese dim sum and noodle dish photography for Asian restaurant..."
98. Score: 3 - "Japanese sushi and ramen bowl presentations for restaurant menus..."
99. Score: 2 - "Professional gym equipment and HIIT training session photos..."
100. Score: 2 - "Modern dental clinic teeth cleaning appointment booking graphics..."
```

**Demo Impact**:
- ✅ Score range: 2-32 (16x difference!)
- ✅ Top results are PERFECT matches
- ✅ Low scores show semantic search ISN'T just matching everything
- ✅ Realistic diversity like real DAM platform

---

## Is This Too Complex?

### NO - It's Already Designed For It!

The architecture you built ALREADY supports this:

```
✅ SearchNarrativeGenerator - creates diverse scenarios
✅ Domain Keyword Library - has cuisine keywords
✅ seed_description_with_keywords() - generates content
✅ Target distribution - controls exact vs semantic vs noise
```

**What's broken**: The pipeline (data spec expansion)

**What's needed**: Fix the plumbing, not rebuild the house

---

## Comparison: With vs Without Cuisine Diversity

### Demo Quality Assessment

| Aspect | Without Diversity | With Diversity |
|--------|------------------|----------------|
| **Realism** | ⚠️ Looks artificial (all assets too similar) | ✅ Like real DAM library |
| **Search Demo Impact** | ⚠️ Scores similar (12-18 range) | ✅ Dramatic score range (2-32) |
| **Semantic Search Demo** | ⚠️ Hard to show AI understanding | ✅ Clear: Italian ≠ Mexican ≠ Japanese |
| **Audience Comprehension** | ⚠️ "Why are scores so similar?" | ✅ "Wow, it finds exactly what I want!" |
| **Data Variety** | ⚠️ Generic, templated feel | ✅ Rich, diverse content |
| **Maintenance** | ✅ Simpler | ⚠️ More scenarios to manage |

### Bottom Line

**Without cuisine diversity**: Demo works, but feels generic and doesn't fully showcase semantic search power.

**With cuisine diversity**: Demo feels realistic, shows dramatic relevancy differences, and impresses audiences.

**Is it worth it?**
- ✅ **YES** - if you're already 80% there (you are!)
- ✅ **YES** - if demos are high-stakes (Project Beacon = major customer)
- ⚠️ **MAYBE** - if this is just internal testing

---

## Final Recommendation

### DO IT - For These Reasons

1. **You're 80% there** - Architecture exists, just fix the pipeline
2. **Dramatic demo impact** - 2x vs 32x relevancy shows AI power clearly
3. **More realistic** - Real DAM platforms have diverse content
4. **Better storytelling** - "Watch it find Italian and ignore Mexican"
5. **Competitive advantage** - Other demo builders don't do this

### Implementation Priority

**MUST DO** (2-3 hours):
- Fix data spec expansion reliability
- Pass narrative even when expansion fails
- Increase scenario count to 8-10

**SHOULD DO** (1-2 hours):
- Expand domain keyword library
- Add more cuisine/topic keywords

**NICE TO HAVE** (optional):
- LLM-generated rich descriptions for flagship demos
- A/B testing different keyword density levels

---

## Questions To Decide

### Q1: How many cuisines/topics per domain?

**Option A - Conservative** (2-3 per domain):
- Food: Italian, Coffee shop, Mexican
- Fashion: Boutique, Seasonal
- Real estate: Open house, Luxury

**Option B - Comprehensive** (4-5 per domain):
- Food: Italian, Mexican, Chinese, Japanese, Coffee
- Fashion: Boutique, Athletic, Formal, Seasonal
- Real estate: Residential, Commercial, Luxury, Rentals

**Recommendation**: Start with A, expand to B if needed

### Q2: How specific should exact phrases be?

**Option A - Very Specific**:
- "handmade spaghetti carbonara"
- "wood-fired Neapolitan pizza"
- "authentic tiramisu dessert"

**Option B - Moderately Specific**:
- "pasta dishes"
- "pizza varieties"
- "Italian desserts"

**Option C - Generic**:
- "Italian food"
- "restaurant menu"
- "dining options"

**Recommendation**: Mix of A and B - specific dishes but natural language

### Q3: Should every query have a matching scenario?

**Current**: Query for "Italian restaurant" but NO Italian scenario in narrative

**Option A - Perfect Alignment**:
- Every query gets a matching scenario
- Generate scenarios based on queries

**Option B - Realistic Diversity**:
- Some queries will have perfect matches (Italian)
- Some will have partial matches (Mediterranean → Italian)
- Some will have low matches (for score contrast)

**Recommendation**: Option B - more realistic and better demo

---

## Next Steps

1. Review this analysis
2. Decide on scenario count (5 → 8-10?)
3. Decide on cuisine diversity level (conservative vs comprehensive)
4. Implement Phase 1 (reliability fixes)
5. Test with new demo generation
6. Measure relevancy score improvements
7. Optional: Implement Phase 2 (library expansion)

