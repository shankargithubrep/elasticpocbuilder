"""
Custom Domain Library Generator

Generates a custom keyword library tailored to each specific demo
based on customer context and search scenarios.
"""

import logging
import json
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class CustomDomainLibraryGenerator:
    """Generates custom domain keyword libraries for each demo"""

    def __init__(self, llm_client):
        """Initialize with LLM client"""
        self.llm_client = llm_client

    def generate_library(
        self,
        customer_context: Dict[str, Any],
        search_narrative: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Generate custom keyword library from customer context and search scenarios.

        This creates a domain-specific keyword library extracted from the search
        scenarios and customer context. The library is reused for all data generation
        in the demo, ensuring consistent, domain-appropriate vocabulary.

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

            logger.info(f"Generated custom library with {len(library)} categories, "
                       f"{sum(len(v) for v in library.values())} total keywords")

            # Log sample for debugging
            first_category = list(library.keys())[0]
            sample_keywords = library[first_category][:5]
            logger.debug(f"Sample keywords from '{first_category}': {sample_keywords}")

            return library

        except Exception as e:
            logger.error(f"Failed to generate custom library: {e}", exc_info=True)
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
            exact = ", ".join(scenario.get("exact_phrases", [])[:4])
            scenario_summaries.append(f"{i}. {desc}\n   Key terms: {exact}")

        # Get unique phrases for display
        unique_exact = list(set(all_exact_phrases))
        unique_semantic = list(set(all_semantic_phrases))

        prompt = f"""You are generating a custom keyword library for a search demo.

## Customer Context
- Company: {company}
- Industry: {industry}
- Department: {department}

## Search Scenarios ({len(scenarios)} total)
{chr(10).join(scenario_summaries)}

## Collected Search Terms
**Exact phrases across all scenarios** ({len(unique_exact)} unique):
{', '.join(unique_exact[:30])}

**Semantic concepts** ({len(unique_semantic)} unique):
{', '.join(unique_semantic[:30])}

## Your Task

Generate a custom keyword library with 5-8 categories of domain-specific keywords. These will be used to create rich, realistic descriptions for {industry} industry content.

**CRITICAL**: Extract keywords primarily from the search scenarios above. The exact_phrases and semantic_phrases are the most important source material.

**Output 5-8 categories**, each with **10-20 keywords**. Categories should be relevant to the search scenarios.

**Suggested category types** (adapt to the domain):
- **primary_terms**: Core subject matter terms extracted from exact_phrases
- **item_types**: Specific items/documents/products mentioned in scenarios
- **contexts**: Where this occurs (locations, departments, settings)
- **descriptors**: Adjectives and qualifiers that fit the domain
- **processes**: Actions, workflows, activities
- **specialties**: Sub-domains or specializations (if applicable)
- **related_concepts**: Broader related terms from semantic_phrases

**Important Guidelines**:
1. PRIMARY SOURCE: Extract keywords FROM the exact_phrases and semantic_phrases listed above
2. Add complementary terms that naturally fit the domain
3. Use terminology that professionals in {industry} would actually use
4. Make keywords specific enough to be meaningful but general enough to reuse
5. Each category should have 10-20 keywords
6. Keywords should sound natural in phrases like "Professional content showcasing {{keyword}}"
7. Avoid generic business jargon - use domain-specific terminology

**Example Output Format** (Healthcare Imaging):

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

Now generate the custom keyword library for **{company} - {industry} - {department}**.

Remember to:
- Extract keywords from the search scenarios above
- Create 5-8 categories
- Put 10-20 keywords per category
- Use domain-specific professional terminology

Return ONLY valid JSON, no explanation or markdown formatting.
"""

        return prompt

    def _extract_json(self, text: str) -> Dict[str, List[str]]:
        """Extract JSON from LLM response"""

        # Remove markdown code blocks
        text = text.strip()
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
                logger.warning(f"Category '{category}' has only {len(keywords)} keywords (recommended: 10-20)")

    def _get_fallback_library(self) -> Dict[str, List[str]]:
        """Return generic fallback library if generation fails"""
        logger.warning("Using fallback generic library due to generation failure")
        return {
            "primary_terms": [
                "content", "materials", "resources", "assets", "documents",
                "information", "data", "records", "files", "items"
            ],
            "contexts": [
                "organization", "business", "facility", "department", "enterprise",
                "office", "workplace", "center", "location", "site"
            ],
            "descriptors": [
                "professional", "quality", "comprehensive", "effective", "detailed",
                "accurate", "reliable", "thorough", "complete", "organized"
            ],
            "processes": [
                "operations", "workflows", "procedures", "activities", "services",
                "tasks", "functions", "processes", "management", "administration"
            ],
            "applications": [
                "business use", "organizational needs", "operational requirements",
                "professional purposes", "enterprise applications", "workflow support"
            ]
        }
