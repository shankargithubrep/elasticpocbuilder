"""
Data Specification Expander Service

Generates domain-specific value specifications for search/RAG demo data generation.
This prevents domain contamination and ensures query-data alignment.
"""

import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class DataSpecificationExpander:
    """Generates domain-specific data value specifications for search demos

    This service adds a dynamic LLM expansion step between query strategy generation
    and data generation to ensure:
    - Domain-specific value examples (not hardcoded templates)
    - Appropriate cardinality for categorical fields
    - Content patterns for semantic_text fields
    - Query-data alignment (data contains searchable terms)
    """

    def __init__(self, llm_client):
        """Initialize with LLM client

        Args:
            llm_client: Anthropic Claude client
        """
        self.llm_client = llm_client

    def expand_data_specifications(
        self,
        query_strategy: Dict,
        customer_context: Dict
    ) -> Dict:
        """Generate domain-specific value specifications

        Args:
            query_strategy: The query strategy with field requirements
            customer_context: Customer info (company, industry, pain_points, etc.)

        Returns:
            data_specifications dict with field-level guidance:
            {
              "datasets": {
                "dataset_name": {
                  "fields": {
                    "field_name": {
                      "type": "keyword",
                      "cardinality": 20,
                      "examples": ["value1", "value2", ...],
                      "description": "What this field represents",
                      "diversity_guidance": "How to ensure variety"
                    }
                  }
                }
              }
            }
        """
        logger.info(f"Expanding data specifications for {customer_context.get('company_name')}")

        # Build the expansion prompt
        prompt = self._build_expansion_prompt(query_strategy, customer_context)

        # Call LLM to generate specifications
        # Increased max_tokens to handle complex nested JSON structures
        max_tokens = 24000

        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=max_tokens,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text

            logger.debug(f"Data specification LLM response length: {len(response_text)}")

            # Extract JSON from response
            specifications = self._extract_json(response_text)

            # Validate that we got something useful
            if not specifications or 'datasets' not in specifications:
                raise ValueError("Invalid specifications structure: missing 'datasets' key")

            logger.info(f"Generated data specifications for {len(specifications.get('datasets', {}))} datasets")

            return specifications

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Response may have been truncated. Length: {len(response_text)} chars")
            raise ValueError(f"Invalid JSON in LLM response: {e}")
        except Exception as e:
            logger.error(f"Failed to expand data specifications: {e}", exc_info=True)
            raise

    def _build_expansion_prompt(
        self,
        query_strategy: Dict,
        customer_context: Dict
    ) -> str:
        """Build the LLM prompt for data specification expansion

        Args:
            query_strategy: The query strategy with datasets and queries
            customer_context: Customer context with company, industry, pain points

        Returns:
            Formatted prompt string
        """
        company_name = customer_context.get('company_name', 'Unknown Company')
        department = customer_context.get('department', 'Unknown Department')
        industry = customer_context.get('industry', 'Unknown Industry')
        pain_points = customer_context.get('pain_points', [])
        use_cases = customer_context.get('use_cases', [])

        # Extract datasets from query strategy
        datasets = query_strategy.get('datasets', [])
        queries = query_strategy.get('queries', [])

        # Build dataset requirements summary
        dataset_summary = []
        for dataset in datasets:
            name = dataset.get('name', 'unknown')
            fields = dataset.get('fields', {})
            dataset_summary.append(f"\n### {name}")
            dataset_summary.append(f"Fields:")
            for field_name, field_type in fields.items():
                dataset_summary.append(f"  - {field_name}: {field_type}")

        dataset_info = "\n".join(dataset_summary)

        # Extract search terms from queries to guide content alignment
        search_terms = []
        for query in queries[:5]:  # Sample first 5 queries
            example_esql = query.get('example_esql', '')
            if 'MATCH(' in example_esql:
                # Extract search terms from MATCH clauses
                import re
                matches = re.findall(r'MATCH\([^,]+,\s*["\']([^"\']+)["\']', example_esql)
                search_terms.extend(matches)

        search_terms_summary = ", ".join(set(search_terms[:10])) if search_terms else "Not specified"

        prompt = f"""You are generating domain-specific data value specifications for a search/RAG demo.

**Customer Context:**
- Company: {company_name}
- Department: {department}
- Industry: {industry}
- Pain Points: {', '.join(pain_points)}
- Use Cases: {', '.join(use_cases)}

**Datasets to Generate:**
{dataset_info}

**Example Search Terms from Queries:**
{search_terms_summary}

**Your Task:**
Generate domain-specific value specifications for each field in each dataset. These specifications will guide an LLM data generator to create realistic, query-aligned data.

**CRITICAL - Domain Specificity:**
- Use terminology from the customer's ACTUAL industry/domain
- DO NOT use generic placeholders or examples from other domains
- Extract domain terms from pain points, use cases, and company name
- Ensure values make sense for {industry} industry and {department} department

**Output Format:**
Return a JSON object with this structure:

```json
{{
  "datasets": {{
    "dataset_name": {{
      "fields": {{
        "field_name": {{
          "type": "keyword",  // Copy from input
          "cardinality": 20,  // How many distinct values (10-50 for keyword, 3-10 for status)
          "examples": ["Value 1", "Value 2", "Value 3", ...],  // 5-10 domain-specific examples
          "description": "Brief description of what this field represents",
          "diversity_guidance": "How to ensure variety across records"
        }},
        "another_field": {{
          "type": "text",
          "content_pattern": "1-2 sentences describing [topic]",
          "diversity_guidance": "Vary vocabulary and phrasing",
          "query_alignment": "Should contain terms like 'X', 'Y' that queries will search for"
        }},
        "semantic_field": {{
          "type": "semantic_text",
          "content_pattern": "3-5 sentences describing expertise/details about {{other_field}}",
          "diversity_guidance": "Vary sentence structure, length, and terminology",
          "query_alignment": "Include searchable terms: {search_terms_summary[:100]}...",
          "tiering_guidance": "20% highly relevant (dense keywords), 40% moderately relevant, 40% low relevance"
        }}
      }}
    }}
  }}
}}
```

**Field Type Guidelines:**

**For `keyword` fields** (categories, statuses, types):
- Provide 5-10 domain-specific examples
- Specify cardinality (10-50 typical)
- Description of what values represent
- Diversity guidance (mix common and specialized)

**For `text` fields** (names, titles, short descriptions):
- Content pattern (how to structure the text)
- Diversity guidance (vary phrasing)
- Query alignment if searchable

**For `semantic_text` fields** (bios, descriptions, content, summaries):
- Content pattern with reference to other fields (e.g., "expertise in {{specialty}}")
- Diversity guidance (vary vocabulary, length, structure)
- **Query alignment** - CRITICAL: List specific terms that queries will search for
- **Tiering guidance** - Ensure 3-tier relevance distribution for score differentiation

**For `geo_point` fields** (locations, addresses with coordinates):
- Geographic region specification (e.g., "Los Angeles area (33.7-34.3°N, -118.7 to -118.0°W)")
- Clustering guidance (e.g., "Create 5-8 clusters around major cities with random jitter")
- Coordinate precision (typically 6 decimal places for ~0.1m accuracy)
- CRITICAL: Must be generated as dict format with 'lat' and 'lon' keys for proper ES mapping

**For other types** (date, boolean, integer, float):
- Provide appropriate value ranges or examples

**Example Output for Healthcare Domain:**

```json
{{
  "datasets": {{
    "provider_directory": {{
      "fields": {{
        "specialty": {{
          "type": "keyword",
          "cardinality": 20,
          "examples": ["Cardiology", "Family Medicine", "Pediatrics", "Orthopedics", "Dermatology", "Neurology", "Psychiatry", "Endocrinology"],
          "description": "Medical specialties and practice areas",
          "diversity_guidance": "Mix 60% common specialties (Cardiology, Family Medicine) with 40% specialized fields (Endocrinology, Rheumatology)"
        }},
        "provider_name": {{
          "type": "text",
          "content_pattern": "Dr. [Last Name], [Credentials]",
          "diversity_guidance": "Use diverse last names, vary credentials (MD, DO, PhD, etc.)"
        }},
        "provider_bio": {{
          "type": "semantic_text",
          "content_pattern": "3-5 sentences describing medical expertise in {{specialty}}, years of experience, and approach to patient care",
          "diversity_guidance": "Vary vocabulary (specialist, physician, doctor), sentence structure, and content length (150-400 words)",
          "query_alignment": "Include searchable terms: 'heart specialist', 'primary care', 'pediatric care', 'orthopedic surgery', etc.",
          "tiering_guidance": "Tier 1 (20%): Dense specialty-specific terminology. Tier 2 (40%): General medical terms. Tier 3 (40%): Generic provider descriptions."
        }}
      }}
    }}
  }}
}}
```

**Now generate specifications for the customer's actual domain:**
- Company: {company_name}
- Industry: {industry}
- Datasets: {', '.join([d.get('name', 'unknown') for d in datasets])}

Generate realistic, domain-appropriate value specifications that will create high-quality demo data.
"""

        return prompt

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response text with multiple fallback strategies

        Args:
            text: LLM response text potentially containing JSON

        Returns:
            Parsed JSON dict

        Raises:
            ValueError: If JSON cannot be extracted or parsed
        """
        import re

        # Strategy 1: Try to find JSON in code blocks first (most reliable)
        json_blocks = re.findall(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)

        if json_blocks:
            for i, block in enumerate(json_blocks):
                try:
                    parsed = json.loads(block)
                    logger.debug(f"Successfully parsed JSON from code block {i+1}")
                    return parsed
                except json.JSONDecodeError as e:
                    logger.warning(f"Code block {i+1} is not valid JSON: {e}")
                    continue

        # Strategy 2: Try to find outermost JSON object
        # Look for { ... } pattern, being greedy to get the full object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                logger.debug("Successfully parsed JSON from outermost braces")
                return parsed
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from outermost braces: {e}")
                # Show preview of where error occurred
                error_pos = getattr(e, 'pos', 0)
                start = max(0, error_pos - 100)
                end = min(len(json_match.group(0)), error_pos + 100)
                context = json_match.group(0)[start:end]
                logger.error(f"Error context: ...{context}...")

        # Strategy 3: Try to find JSON starting with { "datasets"
        datasets_match = re.search(r'\{\s*"datasets"\s*:.*\}', text, re.DOTALL)
        if datasets_match:
            try:
                parsed = json.loads(datasets_match.group(0))
                logger.debug("Successfully parsed JSON starting with 'datasets' key")
                return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse datasets-first JSON: {e}")

        # If all strategies failed, provide helpful error
        logger.error(f"Unable to extract valid JSON from response")
        logger.error(f"Response length: {len(text)} characters")
        logger.error(f"Response preview (first 500 chars): {text[:500]}")
        logger.error(f"Response preview (last 500 chars): {text[-500:]}")

        raise ValueError("No valid JSON found in LLM response after trying multiple extraction strategies")
