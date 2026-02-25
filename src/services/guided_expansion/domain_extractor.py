"""
Domain Extraction for User-Guided Expansion

Extracts key concepts from user input for validation before full expansion.
Uses Claude Sonnet 4.5 for high-quality extraction.
"""

import logging
from typing import Dict, List, Any
import json
import re

logger = logging.getLogger(__name__)


class DomainExtractor:
    """Extracts domain concepts from brief user input for user validation"""

    def __init__(self, llm_client):
        """Initialize with LLM client"""
        self.llm_client = llm_client

    def extract(self, user_input: str, demo_type: str) -> Dict[str, Any]:
        """
        Extract key concepts for user validation.

        Args:
            user_input: Brief user prompt (JSON or text)
            demo_type: 'search' or 'observability'

        Returns:
            {
                "domain": {
                    "name": "Marketing Asset Management",
                    "industry": "Marketing Technology",
                    "primary_focus": "Content discovery and search"
                },
                "key_terms": {
                    "entities": ["Italian food", "product photos", ...],
                    "scenarios": ["Restaurant owner searches...", ...],
                    "document_types": ["product photos", "email templates", ...],
                    "search_patterns": ["natural language", "typo-tolerant", ...]
                },
                "pain_points_summary": "3 pain points identified",
                "use_cases_summary": "8 use cases mentioned"
            }
        """
        logger.info(f"Extracting domain concepts for {demo_type} demo")

        prompt = self._build_extraction_prompt(user_input, demo_type)

        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4000,
                temperature=0.3,  # Lower temp for precise extraction
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text
            extraction = self._parse_json(response_text)

            logger.info(f"Extracted {len(extraction['key_terms']['entities'])} entities, "
                       f"{len(extraction['key_terms']['scenarios'])} scenarios")

            return extraction

        except Exception as e:
            logger.error(f"Domain extraction failed: {e}", exc_info=True)
            return self._get_fallback_extraction(user_input)

    def _build_extraction_prompt(self, user_input: str, demo_type: str) -> str:
        """Build extraction prompt tailored to demo type"""

        if demo_type == 'search':
            focus_instructions = """
**SEARCH DEMO FOCUS**:
Extract terms related to:
- Documents/content being searched (e.g., "patient records", "product photos", "legal briefs")
- Search queries users perform (e.g., "Italian food", "promotion graphics", "case law")
- Types of searches mentioned (semantic, fuzzy, exact, geographic, RAG)
- Industries or domains (healthcare, legal, retail, etc.)
"""
        else:
            focus_instructions = """
**OBSERVABILITY DEMO FOCUS**:
Extract terms related to:
- Systems being monitored (e.g., "Kubernetes cluster", "payment API", "microservices")
- Metrics being tracked (e.g., "CPU usage", "response time", "error rates")
- Data sources mentioned (e.g., "Metricbeat", "APM agents", "logs")
- Technologies or platforms (AWS, Docker, Node.js, etc.)
"""

        prompt = f"""Extract key concepts from this customer input for validation before full expansion.

{focus_instructions}

**Customer Input**:
```
{user_input}
```

**CRITICAL INSTRUCTIONS**:
1. Extract ONLY terms actually present in the user's input
2. Use the user's EXACT wording - don't paraphrase or generalize
3. Identify 5-10 most important entities/concepts the user mentioned
4. Capture 3-5 realistic scenarios using the user's exact language
5. Be precise - if user says "Italian food", use that exact phrase, not "food" or "cuisine"

**Output Format** (return ONLY this JSON, no markdown formatting):
{{
  "domain": {{
    "name": "Concise domain name using user's terminology (e.g., 'Marketing Asset Management', 'Healthcare Patient Records')",
    "industry": "Industry vertical from user's context (e.g., 'Marketing Technology', 'Healthcare')",
    "primary_focus": "One clear sentence describing what they're trying to accomplish"
  }},
  "key_terms": {{
    "entities": [
      "Entity 1 (exact phrase from user input)",
      "Entity 2 (exact phrase from user input)",
      "Entity 3 (exact phrase from user input)"
    ],
    "scenarios": [
      "Scenario 1 description in user's words",
      "Scenario 2 description in user's words",
      "Scenario 3 description in user's words"
    ],
    "document_types": ["Content type 1", "Content type 2"],
    "search_patterns": ["Pattern 1 from input", "Pattern 2 from input"]
  }},
  "pain_points_summary": "X pain points identified: [one-line summary]",
  "use_cases_summary": "Y use cases mentioned: [one-line summary]"
}}

**Quality Check Before Returning**:
- Are all entities exact phrases from the input? (Not generalized?)
- Do scenarios use the user's specific examples? (Not generic?)
- Is the domain name specific to their use case? (Not "Enterprise Search"?)

Extract now. Return ONLY the JSON structure.
"""
        return prompt

    def _parse_json(self, text: str) -> Dict:
        """Parse JSON from LLM response with multiple strategies"""

        # Remove markdown code blocks
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            # Find JSON between any code blocks
            parts = text.split("```")
            for part in parts:
                if part.strip().startswith("{"):
                    text = part
                    break

        # Try to find JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Text preview: {text[:500]}")
            raise

    def _get_fallback_extraction(self, user_input: str) -> Dict:
        """Fallback extraction if LLM fails"""
        logger.warning("Using fallback extraction due to LLM failure")

        # Try to extract basic info from input
        input_lower = user_input.lower()

        # Detect domain
        if "search" in input_lower or "find" in input_lower:
            domain_name = "Search and Retrieval"
        elif "monitor" in input_lower or "metrics" in input_lower:
            domain_name = "Observability and Monitoring"
        else:
            domain_name = "Enterprise Demo"

        return {
            "domain": {
                "name": domain_name,
                "industry": "Technology",
                "primary_focus": "Data analysis and retrieval"
            },
            "key_terms": {
                "entities": ["data", "search", "information"],
                "scenarios": ["User searches for relevant information"],
                "document_types": ["documents", "records"],
                "search_patterns": ["keyword search"]
            },
            "pain_points_summary": "Multiple pain points identified in input",
            "use_cases_summary": "Several use cases mentioned"
        }
