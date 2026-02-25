"""
Search Narrative Generator

Generates a search narrative defining key search scenarios for search demos.
This ensures data contains content that aligns with the queries we'll generate.
"""

import logging
from typing import Dict, Any, List
import json

logger = logging.getLogger(__name__)


class SearchNarrativeGenerator:
    """Generates search narratives that define key search scenarios for demos"""

    def __init__(self, llm_client):
        """Initialize with LLM client"""
        self.llm_client = llm_client

    def generate_narrative(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate search narrative with 8-10 diverse search scenarios.

        Args:
            context: Customer context including industry, pain points, use cases

        Returns:
            Dictionary containing search scenarios with exact phrases, semantic phrases,
            and target distribution for data generation
        """
        logger.info("Generating search narrative from customer context")

        # Build prompt
        prompt = self._build_narrative_prompt(context)

        # Call LLM with increased tokens to handle 8-10 scenarios
        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=8000,  # Increased from 4000 to handle more scenarios
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = response.content[0].text

            # Extract JSON from response
            narrative = self._extract_json(response_text)

            # Validate narrative structure
            self._validate_narrative(narrative)

            logger.info(f"Generated narrative with {len(narrative['search_scenarios'])} scenarios")
            return narrative

        except Exception as e:
            logger.error(f"Failed to generate search narrative: {e}")
            # Return fallback narrative
            return self._get_fallback_narrative(context)

    def _build_narrative_prompt(self, context: Dict[str, Any]) -> str:
        """Build the narrative generation prompt"""

        industry = context.get("industry", "Unknown")
        business_category = context.get("business_category", "Unknown")
        pain_points = context.get("pain_points", [])
        use_cases = context.get("use_cases", [])

        prompt = f"""You are an expert at designing search demos for Elasticsearch. Your task is to generate a "search narrative" that defines realistic search scenarios for a customer demo.

## Customer Context
- Industry: {industry}
- Business Category: {business_category}
- Pain Points: {', '.join(pain_points) if pain_points else 'Not specified'}
- Use Cases: {', '.join(use_cases) if use_cases else 'Not specified'}

## Your Task
Generate 8-10 diverse, realistic search scenarios that this customer would actually perform. Create scenarios across different domains and use cases to showcase variety. For each scenario, you must provide:

1. **scenario_id**: Unique identifier in snake_case (e.g., "italian_restaurant_promotion")
2. **description**: 1-2 sentence description of what the user is searching for
3. **domain**: Category (food_beverage, fitness, retail, real_estate, healthcare, technology, professional_services, hospitality, fashion, education)
4. **exact_phrases**: 4-6 specific phrases that should appear VERBATIM in some documents (these will be used in BM25 queries)
5. **semantic_phrases**: 4-6 related concepts that are semantically similar (these demonstrate semantic search)
6. **target_distribution**: How many documents should match:
   - exact_matches: Documents containing exact phrases (typically 8-16 per scenario)
   - semantic_matches: Documents with related concepts (typically 12-24 per scenario)
   - noise: Unrelated documents for contrast (typically 30-50 per scenario)

## Important Guidelines
- Exact phrases should be SPECIFIC and REALISTIC (e.g., "Italian food", "pasta dishes", "pizza menu")
- Semantic phrases should be RELATED but DIFFERENT (e.g., "Mediterranean cuisine", "authentic Italian")
- Make scenarios DIVERSE across different domains (food, fitness, fashion, real estate, etc.)
- Vary the specificity - some scenarios very specific (Italian restaurant), others broader (restaurant marketing)
- Total documents across all scenarios should be 200-300 (with overlap for noise)
- Each scenario should have a clear, distinct search intent

## Example Output
```json
{{
  "search_scenarios": [
    {{
      "scenario_id": "italian_restaurant_promotion",
      "description": "Small Italian restaurant owner searching for marketing assets to promote their summer menu featuring pasta and pizza",
      "domain": "food_beverage",
      "exact_phrases": [
        "Italian food",
        "pasta dishes",
        "pizza menu",
        "Italian restaurant",
        "Italian cuisine",
        "authentic Italian"
      ],
      "semantic_phrases": [
        "Mediterranean flavors",
        "European dining",
        "family-style meals",
        "rustic cuisine",
        "traditional cooking",
        "artisan recipes"
      ],
      "target_distribution": {{
        "exact_matches": 15,
        "semantic_matches": 25,
        "noise": 60
      }}
    }},
    {{
      "scenario_id": "fitness_apparel_sale",
      "description": "Gym owner promoting new activewear line for their fitness center members",
      "domain": "fitness",
      "exact_phrases": [
        "activewear",
        "gym apparel",
        "workout clothes",
        "athletic wear",
        "fitness clothing",
        "sports apparel"
      ],
      "semantic_phrases": [
        "performance wear",
        "training gear",
        "exercise clothing",
        "athletic fashion",
        "sports fashion",
        "fitness attire"
      ],
      "target_distribution": {{
        "exact_matches": 12,
        "semantic_matches": 20,
        "noise": 60
      }}
    }}
  ]
}}
```

Generate the search narrative now. Return ONLY valid JSON, no explanation or markdown formatting.
"""

        return prompt

    def _extract_json(self, response_text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""

        # Remove markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```"):
            # Remove opening ```json or ```
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            # Remove closing ```
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]

        # Parse JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            logger.debug(f"Response text: {text[:500]}")
            raise

    def _validate_narrative(self, narrative: Dict[str, Any]):
        """Validate narrative structure"""

        if "search_scenarios" not in narrative:
            raise ValueError("Narrative missing 'search_scenarios' key")

        scenarios = narrative["search_scenarios"]

        if not isinstance(scenarios, list) or len(scenarios) < 5:
            raise ValueError(f"Narrative must have at least 5 search scenarios, got {len(scenarios)}")

        for i, scenario in enumerate(scenarios):
            required_keys = [
                "scenario_id", "description", "domain",
                "exact_phrases", "semantic_phrases", "target_distribution"
            ]

            for key in required_keys:
                if key not in scenario:
                    raise ValueError(f"Scenario {i} missing required key: {key}")

            # Validate target_distribution
            dist = scenario["target_distribution"]
            required_dist_keys = ["exact_matches", "semantic_matches", "noise"]
            for key in required_dist_keys:
                if key not in dist:
                    raise ValueError(f"Scenario {i} target_distribution missing key: {key}")

    def _get_fallback_narrative(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Return a generic fallback narrative if LLM generation fails"""

        logger.warning("Using fallback narrative due to generation failure")

        # Generic fallback based on industry
        industry = context.get("industry", "Business").lower()

        if "food" in industry or "restaurant" in industry:
            domain = "food_beverage"
            exact = ["Italian food", "pasta dishes", "restaurant menu"]
            semantic = ["Mediterranean cuisine", "dining experience", "culinary offerings"]
        elif "fitness" in industry or "health" in industry:
            domain = "fitness"
            exact = ["workout programs", "fitness training", "gym services"]
            semantic = ["athletic performance", "wellness programs", "exercise routines"]
        elif "retail" in industry or "ecommerce" in industry:
            domain = "retail"
            exact = ["product catalog", "online shopping", "retail merchandise"]
            semantic = ["shopping experience", "customer purchases", "product offerings"]
        else:
            domain = "professional_services"
            exact = ["business solutions", "professional services", "client support"]
            semantic = ["service offerings", "customer solutions", "business assistance"]

        return {
            "search_scenarios": [
                {
                    "scenario_id": "primary_search_scenario",
                    "description": f"Primary search scenario for {context.get('business_category', 'business')}",
                    "domain": domain,
                    "exact_phrases": exact,
                    "semantic_phrases": semantic,
                    "target_distribution": {
                        "exact_matches": 15,
                        "semantic_matches": 25,
                        "noise": 60
                    }
                }
            ]
        }
