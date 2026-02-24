# Search Narrative Implementation Plan

## Executive Summary

**Problem**: Search demos generate queries looking for "Italian food" but data contains generic text with no relevant keywords, resulting in poor relevancy scores (2-4) and unconvincing demos.

**Solution**: Generate a "Search Narrative" defining 3-5 key search scenarios, then use keyword seeding to create data that naturally contains those search terms.

**Expected Impact**: 5-7x improvement in relevancy scores (from 2-4 to 12-18) with no additional cost or latency.

---

## Implementation Approach: Hybrid Strategy

### Phase 1: Search Narrative Generation (1 LLM call per demo)

**New Service**: `src/services/search_narrative_generator.py`

```python
class SearchNarrativeGenerator:
    """
    Generates a search narrative defining key search scenarios for the demo.

    Input: Customer context (industry, pain points, business category)
    Output: 3-5 search scenarios with exact phrases, semantic phrases, and distribution targets
    Cost: 1 LLM call (~$0.10)
    Time: ~5 seconds
    """

    def generate_narrative(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate search narrative with 3-5 scenarios.

        Returns:
        {
            "search_scenarios": [
                {
                    "scenario_id": "italian_restaurant_promotion",
                    "description": "...",
                    "domain": "food_beverage",
                    "exact_phrases": ["Italian food", "pasta", "pizza"],
                    "semantic_phrases": ["Mediterranean", "cuisine"],
                    "target_distribution": {
                        "exact_matches": 15,
                        "semantic_matches": 25,
                        "noise": 60
                    }
                },
                ...
            ]
        }
        """
```

**Integration Point**: Called by `SearchStrategyGenerator` after analyzing customer context, before generating query strategy.

**Prompt Template**:
```
Given this customer context:
- Industry: {industry}
- Business: {business_category}
- Pain Points: {pain_points}
- Use Cases: {use_cases}

Generate a search narrative defining 3-5 realistic search scenarios for this customer.

For each scenario, provide:
1. scenario_id: snake_case identifier
2. description: What the user is looking for
3. domain: Category (food_beverage, fitness, retail, real_estate, etc.)
4. exact_phrases: 3-5 phrases that should appear verbatim in documents
5. semantic_phrases: 3-5 related concepts that are semantically similar
6. target_distribution: How many documents should match (exact/semantic/noise)

Example output:
{
  "search_scenarios": [
    {
      "scenario_id": "italian_restaurant_promotion",
      "description": "Small Italian restaurant owner searching for summer promotion assets",
      "domain": "food_beverage",
      "exact_phrases": ["Italian food", "pasta dishes", "pizza menu", "Italian restaurant"],
      "semantic_phrases": ["Mediterranean cuisine", "authentic Italian", "family dining", "Italian flavors"],
      "target_distribution": {
        "exact_matches": 15,
        "semantic_matches": 25,
        "noise": 60
      }
    }
  ]
}

Return ONLY the JSON, no explanation.
```

---

### Phase 2: Keyword Library Creation

**New File**: `src/services/domain_keyword_library.py`

```python
"""
Domain-specific keyword libraries for search content generation.
Used to seed realistic keywords into generated data based on search narrative.
"""

DOMAIN_LIBRARIES = {
    "food_beverage": {
        "cuisines": [
            "Italian", "Mexican", "Chinese", "Thai", "French", "Japanese",
            "Mediterranean", "American", "Korean", "Vietnamese", "Greek", "Indian"
        ],
        "dishes": [
            "pasta", "pizza", "sushi", "tacos", "curry", "steak", "salad",
            "burgers", "sandwiches", "seafood", "noodles", "rice bowls"
        ],
        "contexts": [
            "restaurant", "catering", "food truck", "cafe", "bistro", "diner",
            "eatery", "kitchen", "bakery", "bar", "grill", "tavern"
        ],
        "descriptors": [
            "authentic", "fresh", "homemade", "gourmet", "artisan",
            "traditional", "handcrafted", "organic", "locally-sourced"
        ],
        "occasions": [
            "dinner service", "lunch special", "brunch menu", "takeout",
            "delivery", "catering event", "dining experience"
        ]
    },

    "fitness": {
        "activities": [
            "yoga", "running", "cycling", "weightlifting", "CrossFit",
            "pilates", "HIIT", "spinning", "boxing", "swimming"
        ],
        "products": [
            "activewear", "gym apparel", "workout clothes", "athletic wear",
            "sports gear", "fitness equipment", "training accessories"
        ],
        "contexts": [
            "fitness center", "gym", "sports club", "wellness studio",
            "training facility", "health club", "yoga studio", "CrossFit box"
        ],
        "descriptors": [
            "performance", "breathable", "flexible", "durable",
            "moisture-wicking", "comfortable", "supportive", "lightweight"
        ],
        "benefits": [
            "muscle building", "weight loss", "cardio health", "flexibility",
            "strength training", "endurance", "recovery", "wellness"
        ]
    },

    "retail": {
        "products": [
            "clothing", "accessories", "footwear", "jewelry", "home decor",
            "electronics", "gadgets", "furniture", "cosmetics", "bags"
        ],
        "styles": [
            "modern", "vintage", "minimalist", "luxury", "casual", "formal",
            "bohemian", "contemporary", "classic", "trendy", "elegant"
        ],
        "contexts": [
            "boutique", "department store", "online shop", "showroom",
            "outlet", "mall", "marketplace", "retail store", "shop"
        ],
        "descriptors": [
            "trendy", "affordable", "premium", "exclusive", "versatile",
            "handmade", "designer", "limited-edition", "curated"
        ],
        "occasions": [
            "everyday wear", "special occasion", "work attire", "weekend casual",
            "formal event", "seasonal collection", "holiday gift"
        ]
    },

    "real_estate": {
        "property_types": [
            "single-family home", "condo", "townhouse", "apartment",
            "luxury estate", "commercial space", "office building", "land"
        ],
        "features": [
            "open floor plan", "modern kitchen", "master suite", "backyard",
            "pool", "garage", "hardwood floors", "updated bathrooms"
        ],
        "locations": [
            "downtown", "suburban", "waterfront", "historic district",
            "gated community", "school district", "walkable neighborhood"
        ],
        "descriptors": [
            "spacious", "renovated", "move-in ready", "charming", "contemporary",
            "pristine", "well-maintained", "upgraded", "stunning"
        ],
        "contexts": [
            "listing", "open house", "property showcase", "virtual tour",
            "market analysis", "neighborhood guide", "property brochure"
        ]
    },

    "healthcare": {
        "services": [
            "primary care", "urgent care", "specialty clinic", "diagnostic imaging",
            "laboratory services", "physical therapy", "mental health", "wellness"
        ],
        "specialties": [
            "cardiology", "orthopedics", "pediatrics", "dermatology",
            "neurology", "oncology", "women's health", "dentistry"
        ],
        "contexts": [
            "hospital", "clinic", "medical center", "health system",
            "physician practice", "urgent care center", "outpatient facility"
        ],
        "descriptors": [
            "comprehensive", "patient-centered", "evidence-based", "compassionate",
            "advanced", "preventive", "personalized", "accessible"
        ],
        "benefits": [
            "improved outcomes", "faster recovery", "better quality of life",
            "preventive care", "chronic disease management", "wellness support"
        ]
    }
}


def get_keywords_for_domain(domain: str) -> Dict[str, List[str]]:
    """Get keyword library for specific domain"""
    return DOMAIN_LIBRARIES.get(domain, DOMAIN_LIBRARIES["retail"])


def seed_description_with_keywords(
    scenario: Dict[str, Any],
    use_exact: bool = True,
    asset_type: str = "image"
) -> str:
    """
    Generate a description with keywords seeded from the scenario.

    Args:
        scenario: Search scenario from narrative
        use_exact: If True, use exact phrases; if False, use semantic phrases
        asset_type: Type of asset (image, video, graphic, etc.)

    Returns:
        Rich description with natural keyword integration
    """
    domain = scenario["domain"]
    keywords = get_keywords_for_domain(domain)

    if use_exact:
        # Use exact target phrase
        exact_phrase = random.choice(scenario["exact_phrases"])

        # Get supporting keywords from library
        category_keys = list(keywords.keys())
        supporting1 = random.choice(keywords[category_keys[0]])
        supporting2 = random.choice(keywords[category_keys[1]])
        context = random.choice(keywords.get("contexts", ["business"]))
        descriptor = random.choice(keywords.get("descriptors", ["professional"]))

        # Template variations for natural language
        templates = [
            f"Professional {asset_type} showcasing {exact_phrase} with emphasis on {supporting1}. "
            f"{descriptor.title()} content ideal for {context} marketing campaigns featuring {supporting2}.",

            f"{descriptor.title()} {asset_type} highlighting {exact_phrase} in authentic presentation. "
            f"Perfect for {context} promotions, capturing the essence of {supporting1} and {supporting2}.",

            f"High-quality {asset_type} featuring {exact_phrase} designed for {context} advertising. "
            f"Showcases {supporting1} with {descriptor} attention to detail and {supporting2} appeal.",
        ]

        return random.choice(templates)

    else:
        # Use semantic phrase
        semantic_phrase = random.choice(scenario["semantic_phrases"])

        # Get supporting keywords
        category_keys = list(keywords.keys())
        supporting1 = random.choice(keywords[category_keys[0]])
        supporting2 = random.choice(keywords[category_keys[1]])
        context = random.choice(keywords.get("contexts", ["business"]))

        templates = [
            f"Creative {asset_type} emphasizing {semantic_phrase} through {supporting1}. "
            f"Designed for {context} campaigns with focus on {supporting2} and authentic presentation.",

            f"{asset_type.title()} content highlighting {semantic_phrase} in professional setting. "
            f"Features {supporting1} and {supporting2} perfect for {context} promotional materials.",

            f"Engaging {asset_type} that captures {semantic_phrase} with {supporting1}. "
            f"Ideal for {context} marketing, emphasizing quality {supporting2} and compelling visuals.",
        ]

        return random.choice(templates)
```

---

### Phase 3: Integration with Data Generation

**Modified File**: `src/framework/generation/module_generator.py`

Update the data generation prompt to include narrative context:

```python
def _generate_data_module_with_requirements(self, ...):
    """Modified to include search narrative"""

    # NEW: Check if this is a search demo with narrative
    search_narrative = self.config.get("search_narrative")
    narrative_context = ""

    if search_narrative:
        narrative_context = f"""
## SEARCH NARRATIVE CONTEXT

This demo has specific search scenarios that the data must support.
Your generated data MUST include content that matches these search terms:

{json.dumps(search_narrative, indent=2)}

CRITICAL REQUIREMENTS for search demos:
1. Distribute documents across scenarios as specified in target_distribution
2. For "exact_matches" documents: Include exact phrases verbatim in descriptions
3. For "semantic_matches" documents: Include semantic_phrases naturally
4. For "noise" documents: Include unrelated content for contrast

IMPLEMENTATION:
- Use the keyword seeding approach from domain_keyword_library.py
- Call seed_description_with_keywords() for scenario-aligned documents
- Ensure realistic distribution: {search_narrative['search_scenarios'][0]['target_distribution']}

Example for Italian restaurant scenario:
✅ GOOD: "Professional food photography featuring Italian food and pasta dishes,
          ideal for restaurant summer menu promotions with authentic Mediterranean cuisine."
❌ BAD:  "High-quality Image asset for Holiday Sale campaign targeting Food Beverage businesses."
"""

    data_gen_prompt = f"""
{self._get_data_generation_system_prompt()}

{narrative_context}

... (rest of existing prompt)
"""
```

---

### Phase 4: Update SearchStrategyGenerator

**Modified File**: `src/services/search_strategy_generator.py`

```python
class SearchQueryStrategyGenerator:
    """Modified to generate narrative first"""

    def generate_strategy(self, config: DemoConfig) -> Dict[str, Any]:
        """Generate complete search strategy including narrative"""

        # NEW STEP 1: Generate search narrative
        from src.services.search_narrative_generator import SearchNarrativeGenerator

        narrative_gen = SearchNarrativeGenerator(self.llm_client)
        search_narrative = narrative_gen.generate_narrative({
            "industry": config.industry,
            "business_category": config.get("business_category"),
            "pain_points": config.pain_points,
            "use_cases": config.use_cases
        })

        logger.info(f"Generated search narrative with {len(search_narrative['search_scenarios'])} scenarios")

        # STEP 2: Generate query strategy (existing code, now narrative-aware)
        strategy = self._generate_query_strategy(config, search_narrative)

        # Include narrative in strategy
        strategy["search_narrative"] = search_narrative

        return strategy
```

---

## Testing Plan

### Test 1: Generate Single Demo with Narrative

```bash
# Create test demo with narrative approach
python -c "
from src.framework import ModularDemoOrchestrator
from src.framework.base import DemoConfig

config = DemoConfig(
    company_name='Adobe',
    department='Project Beacon',
    industry='Technology',
    pain_points=['content discovery', 'manual search'],
    use_cases=['search marketing assets'],
    demo_type='search'
)

orchestrator = ModularDemoOrchestrator()
result = orchestrator.generate_demo(config)
print(f'Demo generated: {result}')
"
```

**Expected**:
- `search_narrative.json` exists in demo folder
- Data contains "Italian food", "pasta", "restaurant" in realistic frequencies
- Query results have scores 10-18 (vs 2-4 before)

### Test 2: Compare Relevancy Scores

```python
# In demos/PROJECT_NAME/test_queries.py
from elasticsearch import Elasticsearch

es = Elasticsearch(...)

# Test query
query = {
    "query": {
        "match": {
            "asset_description": "Italian food restaurant"
        }
    }
}

results = es.search(index="marketing_assets", body=query)

# Measure scores
scores = [hit["_score"] for hit in results["hits"]["hits"]]
avg_score = sum(scores) / len(scores)

print(f"Average relevancy score: {avg_score}")
print(f"Top 5 scores: {scores[:5]}")

# BEFORE: avg_score ≈ 2.5, top scores: [3.2, 2.8, 2.5, 2.1, 1.9]
# AFTER:  avg_score ≈ 12.3, top scores: [18.5, 15.2, 13.8, 12.1, 10.9]
```

---

## Rollout Plan

### Week 1: Foundation
- [ ] Create `SearchNarrativeGenerator` service
- [ ] Create `domain_keyword_library.py` with 5 domains
- [ ] Add unit tests for narrative generation

### Week 2: Integration
- [ ] Update `SearchStrategyGenerator` to call narrative generator
- [ ] Update `ModuleGenerator` data prompts with narrative context
- [ ] Test with single demo (Adobe Project Beacon)

### Week 3: Validation
- [ ] Generate 3 test demos (food, fitness, retail)
- [ ] Measure relevancy score improvements
- [ ] Collect feedback on search quality

### Week 4: Production
- [ ] Enable for all new search demos
- [ ] Document in user guide
- [ ] Add narrative visualization in UI

---

## Success Metrics

### Immediate (Week 2)
- [ ] Narrative generation successful (< 10 seconds)
- [ ] Data contains exact phrases (> 10% of documents)
- [ ] Queries return results with scores > 10

### Short-term (Week 4)
- [ ] Average relevancy score > 12.0 (vs 2.5 baseline)
- [ ] Top 5 results all relevant to query
- [ ] Customer feedback: "Search results look realistic"

### Long-term (Month 2)
- [ ] 100% of search demos use narrative approach
- [ ] Zero customer complaints about "generic data"
- [ ] Search demos used in production customer meetings

---

## Cost Analysis

**Current Approach**: Free, but poor quality

**Narrative Approach**:
- 1 LLM call for narrative: ~$0.10
- 0 additional calls for data: $0
- **Total per demo: $0.10**

**ROI**: Massive improvement in demo quality for negligible cost

---

## Next Steps

1. ✅ Review strategy document
2. ✅ Run test comparison script
3. 📋 Get approval for implementation approach
4. 🚀 Begin Week 1 development

