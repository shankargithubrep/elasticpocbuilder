# Search Content Specificity Analysis

## Executive Summary

The latest demo (adobe,_inc._project_beacon_team_20260122_111205) shows **significant improvement** over previous versions, with relevancy scores in the **12-18 range** (up from 2-4). However, there's still a gap between query specificity and data content richness.

**Key Finding**: The search narrative generated successfully with 5 scenarios, BUT the data specification expansion **failed** due to JSON parsing error, causing the data generator to fall back to generic templates instead of keyword-seeded content.

---

## What Happened

### Timeline

1. ✅ **11:08:49** - Search narrative generated successfully (5 scenarios)
2. ✅ **11:10:58** - Query strategy generated with 16 queries
3. ❌ **11:12:05** - **Data specification expansion FAILED** (JSON parse error)
4. ⚠️  **11:12:05** - Fallback to basic specifications (no narrative context)
5. ⚠️  **11:13:48** - Data generator created WITHOUT keyword seeding

### The Gap

**Query searches for:**
```
"Italian restaurant food menu photos pasta pizza"
```

**Top matching description (score ~16):**
```
"High-quality image asset designed for restaurant businesses.
Features rustic aesthetic with monochrome color scheme. Perfect
for brand awareness campaigns targeting professionals. Optimized
for web platform with professional appeal."
```

**Why it matched:**
- ✅ Contains "restaurant" (exact keyword match)
- ~ "rustic" has semantic similarity to Italian/traditional
- ~ "monochrome" might relate to classic Italian design
- ❌ Missing: "Italian", "food", "menu", "pasta", "pizza"

**Search Narrative DID generate the right keywords:**
```json
{
  "scenario_id": "summer_coffee_shop_promotion",
  "exact_phrases": [
    "cold brew coffee",
    "iced drinks",
    "summer beverages",
    "coffee shop promotion"
  ]
}
```

But these never made it into the data because expansion failed!

---

## Root Cause Analysis

### Why Data Spec Expansion Failed

From logs (line 39):
```
Failed to parse JSON: Expecting ',' delimiter: line 197 column 10 (char 14830)
```

This is the same JSON truncation/malformation issue we saw before. Possible causes:

1. **Token limit**: Even though we increased to 16000, the LLM response might still be cut off
2. **Complex nested structure**: Data specifications are deeply nested JSON
3. **LLM syntax error**: Model generated invalid JSON mid-response

### Cascading Impact

```
Data Spec Expansion Fails
    ↓
Orchestrator uses "basic specifications"
    ↓
Module generator gets NO search narrative context in data prompt
    ↓
Data generator uses generic template strings
    ↓
Descriptions lack specific keywords from search scenarios
```

---

## Current State Assessment

### What's Working ✅

1. **Search narrative generation** - Created 5 diverse, realistic scenarios
2. **Query generation** - 16 queries with appropriate search terms
3. **Relevancy scores improved** - From 2-4 to 12-18 (3-4x better!)
4. **Semantic matching** - "restaurant" + "rustic" DO match "Italian restaurant"
5. **Architecture** - All components are properly integrated

### What Needs Improvement ⚠️

1. **Data spec expansion reliability** - JSON parsing failures
2. **Keyword specificity** - Need more exact phrase matches in descriptions
3. **Cuisine/topic diversity** - Should have multiple restaurant types (Italian, Mexican, Chinese, etc.)
4. **Narrative-to-data pipeline** - Broken when expansion fails

---

## Test Strategies for Improvement

### Strategy 1: Fix Data Spec Expansion Reliability

**Approach**: Debug and fix JSON parsing in data specification expander

**Changes needed**:
```python
# In src/services/data_specification_expander.py

1. Add more robust JSON extraction (try multiple patterns)
2. Increase max_tokens further (16000 → 24000?)
3. Add JSON schema validation before parsing
4. Implement retry logic with simpler prompts
5. Add fallback: if expansion fails, still pass search narrative to module generator
```

**Expected improvement**:
- Data spec expansion succeeds 95%+ of time
- Even when it fails, narrative still reaches data generator

**Risk**: Low - this is a bug fix, not architecture change

---

### Strategy 2: Direct Narrative Injection (Bypass Expansion)

**Approach**: Pass search narrative DIRECTLY to module generator, independent of data spec expansion

**Changes needed**:
```python
# In src/framework/orchestrator.py

def _generate_demo_module(self, context, query_strategy):
    # ALWAYS pass narrative, even if expansion fails
    narrative = query_strategy.get("search_narrative", {})

    # Try expansion, but don't let it block narrative
    try:
        expanded_specs = self.expander.expand_data_specifications(...)
    except Exception as e:
        logger.warning(f"Expansion failed, using narrative anyway: {e}")
        expanded_specs = None

    # Pass BOTH to module generator
    module_path = self.module_generator.generate_demo_module(
        config=config,
        query_strategy=query_strategy,  # includes narrative
        expanded_specs=expanded_specs    # might be None
    )
```

**Expected improvement**:
- Keyword seeding works even when expansion fails
- Descriptions contain "Italian", "pasta", "pizza" for Italian searches

**Risk**: Low - makes system more resilient

---

### Strategy 3: Multi-Cuisine/Topic Data Generation

**Approach**: Generate diverse, topic-specific descriptions using domain library

**Current (generic)**:
```python
desc = f"High-quality {asset_type} designed for {industry} businesses..."
```

**Proposed (topic-specific)**:
```python
from src.services.domain_keyword_library import seed_description_with_keywords

# For each search scenario in narrative
if scenario["domain"] == "food_beverage":
    for phrase in scenario["exact_phrases"]:
        # Generate descriptions WITH these keywords
        desc = seed_description_with_keywords(
            scenario=scenario,
            use_exact=True,
            asset_type=asset_type,
            index=i
        )
        # Returns: "Appetizing Italian restaurant menu featuring
        #           fresh pasta dishes and authentic Neapolitan pizza..."
```

**Target distribution** (from search narrative):
- 14 descriptions with "Italian food" exact matches
- 24 descriptions with "Mediterranean cuisine" semantic matches
- 52 noise descriptions with other topics

**Expected improvement**:
- Exact match relevancy: 18-24 (up from 12-18)
- Semantic match relevancy: 10-14 (up from 8-10)
- Noise relevancy: 2-6 (stays low - important for contrast!)

**Risk**: Medium - requires careful distribution management

---

### Strategy 4: Post-Generation Content Enrichment

**Approach**: After generic data is generated, enrich descriptions with scenario keywords

**Pseudocode**:
```python
def enrich_descriptions(df, search_narrative):
    """Add scenario-specific keywords to existing descriptions"""

    scenarios = search_narrative["search_scenarios"]

    for scenario in scenarios:
        # Calculate how many rows to enrich for this scenario
        n_exact = scenario["target_distribution"]["exact_matches"]
        n_semantic = scenario["target_distribution"]["semantic_matches"]

        # Select random rows to enrich
        exact_rows = random.sample(range(len(df)), n_exact)
        semantic_rows = random.sample(range(len(df)), n_semantic)

        # Inject exact phrases
        for row_idx in exact_rows:
            original = df.loc[row_idx, 'asset_description']
            phrases = random.sample(scenario["exact_phrases"], 2)
            df.loc[row_idx, 'asset_description'] = inject_keywords(original, phrases)

        # Inject semantic phrases (more subtle)
        for row_idx in semantic_rows:
            original = df.loc[row_idx, 'asset_description']
            phrases = random.sample(scenario["semantic_phrases"], 2)
            df.loc[row_idx, 'asset_description'] = inject_keywords(original, phrases, mode='semantic')

    return df
```

**Expected improvement**:
- Works with current generic generation
- Can fix descriptions after the fact
- Precise control over distribution

**Risk**: Low - doesn't change generation, only enriches

---

## Recommended Approach

### Phase 1: Quick Win (Strategy 2 + Strategy 4)

1. **Make narrative injection resilient** (Strategy 2)
   - Pass narrative even when expansion fails
   - Estimated dev time: 30 minutes
   - Risk: Low

2. **Add post-enrichment** (Strategy 4)
   - Enrich after generation with scenario keywords
   - Estimated dev time: 1-2 hours
   - Risk: Low

**Total time**: 2-3 hours
**Expected result**: Descriptions contain exact keywords from queries

### Phase 2: Robust Fix (Strategy 1 + Strategy 3)

1. **Fix data spec expansion** (Strategy 1)
   - Debug JSON parsing
   - Add retry logic and better error handling
   - Estimated dev time: 2-3 hours
   - Risk: Low

2. **Implement domain-aware generation** (Strategy 3)
   - Use keyword seeding during generation (not after)
   - Estimated dev time: 3-4 hours
   - Risk: Medium

**Total time**: 5-7 hours
**Expected result**: Reliable, high-quality keyword-rich content from the start

---

## Example: Italian Restaurant Search

### Current State

**Query**: `MATCH(asset_description, "Italian restaurant food menu photos pasta pizza")`

**Top Result (score: 16.2)**:
```
Title: "Rustic Social Media for Restaurant"
Description: "High-quality image asset designed for restaurant businesses.
              Features rustic aesthetic with monochrome color scheme..."
Type: image
Category: social_media
```

**Analysis**:
- ✅ BM25 matched on "restaurant"
- ~ Semantic matched "rustic" → Italian traditional
- ❌ Missing all food-specific keywords

### With Strategy 2 + 4 (Post-Enrichment)

**Same Document, Enriched**:
```
Title: "Rustic Italian Restaurant Social Media"
Description: "High-quality image asset designed for Italian restaurant
              businesses featuring authentic pasta dishes and artisan pizza.
              Rustic aesthetic with warm earth-tone color scheme perfect
              for showcasing your menu items..."
Type: image
Category: social_media
```

**Expected score**: 22-26 (up from 16)
**Why**: Exact matches on "Italian", "restaurant", "pasta", "pizza", "menu"

### With Strategy 1 + 3 (Keyword Seeding from Start)

**Generated from Narrative**:
```
Title: "Authentic Italian Cuisine Photo Collection"
Description: "Mouthwatering photography of traditional Italian restaurant
              menu favorites - handmade pasta tossed in rich marinara,
              wood-fired Neapolitan pizza with fresh mozzarella, classic
              antipasti platters. Perfect for restaurant menu boards, food
              delivery apps, and social media promotion of your Italian
              dining experience..."
Type: image
Category: product_photo
```

**Expected score**: 28-35 (keyword-dense, semantically coherent)
**Why**: Natural integration of ALL search terms in contextually appropriate way

---

## Questions for Discussion

### Q1: Should we generate descriptions with MULTIPLE cuisines/topics?

**Current**: Generic "restaurant" without cuisine type

**Option A**: Diverse cuisine-specific content
- 15% Italian (pasta, pizza, risotto)
- 15% Mexican (tacos, burritos, salsa)
- 10% Chinese (dumplings, noodles, stir-fry)
- 10% Japanese (sushi, ramen, teriyaki)
- 50% generic or other

**Option B**: Scenario-driven distribution
- Generate based on 5 search scenarios from narrative
- Each scenario gets its target_distribution allocation
- Remaining rows are noise

**Recommendation**: Option B - follows the narrative architecture we built

### Q2: How specific should keyword matching be?

**Option A - Exact phrase matching**:
- Query: "Italian restaurant food"
- Description: "Italian restaurant food menu with pasta and pizza"
- Score: 30-35 (very high)
- Demo impact: Might look "too perfect"

**Option B - Natural keyword integration**:
- Query: "Italian restaurant food"
- Description: "Authentic trattoria menu featuring fresh pasta, wood-fired pizza, and classic Italian appetizers"
- Score: 22-28 (excellent but natural)
- Demo impact: Looks realistic and impressive

**Option C - Semantic-only** (current state):
- Query: "Italian restaurant food"
- Description: "Rustic restaurant aesthetic with professional appeal"
- Score: 12-18 (decent but missing specifics)
- Demo impact: Works but not compelling

**Recommendation**: Option B - natural integration feels realistic while delivering strong relevancy

### Q3: Is this level of complexity worth it?

**Consider**:
- Current scores (12-18) are already 3-4x better than before (2-4)
- Semantic search IS finding relevant results ("restaurant" + "rustic")
- Real-world searches don't always have perfect keyword matches

**But**:
- Demo is meant to be impressive and show "wow" moments
- Competitors might have better sample data
- We already built the infrastructure (search narrative, keyword library)
- It's mainly a reliability fix, not a feature

**Recommendation**: Yes - finish what we started. The architecture is solid, we just need to fix the data spec expansion bug and ensure narrative reaches data generator.

---

## Next Steps

1. **Immediate**: Run diagnosis on data spec expansion JSON error
2. **Quick win**: Implement Strategy 2 (resilient narrative injection)
3. **Testing**: Generate new demo and compare relevancy scores
4. **If needed**: Implement Strategy 4 (post-enrichment) as backup
5. **Long-term**: Fix expansion reliability (Strategy 1)

---

## Metrics to Track

| Metric | Current | Target (Phase 1) | Target (Phase 2) |
|--------|---------|------------------|------------------|
| Exact match score | 16.2 | 22-26 | 28-35 |
| Semantic match score | 12.8 | 14-18 | 18-24 |
| Noise score | 3.2 | 2-6 | 2-4 |
| Keyword coverage | 30% | 70% | 95% |
| Data spec success rate | 50% | 95% | 99% |

