"""
Context extraction for demo generation

Provides intelligent context extraction from natural language user input
using LLM-based processing or fallback to regex-based extraction.
"""

import streamlit as st
import re
import json
from typing import Dict


class SmartContextExtractor:
    """Intelligent context extraction from user messages using LLM"""

    def __init__(self):
        self.llm_client = None
        try:
            import anthropic
            import os

            # Try to get API key from environment or Streamlit secrets
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key and hasattr(st, 'secrets') and 'ANTHROPIC_API_KEY' in st.secrets:
                api_key = st.secrets["ANTHROPIC_API_KEY"]

            if api_key:
                self.llm_client = anthropic.Anthropic(api_key=api_key)
            else:
                # Don't show warning in __init__, will show if extraction fails
                pass
        except Exception as e:
            # Silently fail, will fallback to basic extraction
            pass

    def extract_context(self, message: str) -> Dict:
        """Extract all possible context from the message using LLM"""

        if not self.llm_client:
            # Fallback to basic extraction if LLM not available
            st.info("💡 Using basic extraction. For better results, set ANTHROPIC_API_KEY environment variable.")
            return self._basic_extract(message)

        try:
            # Use LLM to extract context
            extraction_prompt = f"""Extract the following information from this customer description. Return ONLY valid JSON.

Customer Message:
{message}

Extract:
- company_name: The company name (string or null)
- department: The department/team (string or null)
- industry: The industry (string or null)
- pain_points: List of specific pain points or challenges (array of strings, extract as many as mentioned)
- use_cases: List of use cases or goals (array of strings)
- metrics: List of metrics they care about (array of strings)
- scale: Data scale mentioned (string or null, e.g., "5000+ accounts", "millions of transactions")

Return ONLY a JSON object with these keys. If a field is not found, use null or empty array.

JSON:"""

            response = self.llm_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": extraction_prompt}]
            )

            # Parse JSON response
            content = response.content[0].text.strip()

            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            context = json.loads(content)

            # Clean up nulls
            result = {}
            for key, value in context.items():
                if value is not None and value != [] and value != "":
                    result[key] = value

            return result

        except Exception as e:
            st.error(f"LLM extraction failed: {e}")
            return self._basic_extract(message)

    def _basic_extract(self, message: str) -> Dict:
        """Fallback basic extraction using regex"""
        context = {}

        # Basic company extraction
        company_match = re.search(r"(?:Customer is|for|with|at)\s+([A-Z][A-Za-z0-9\s&'.-]+?)(?:\.|,|Department|\s+is)", message, re.IGNORECASE)
        if company_match:
            context["company_name"] = company_match.group(1).strip()

        # Basic department extraction
        dept_keywords = ["Call Center", "Customer Success", "Sales", "Marketing", "Operations", "Supply Chain", "Finance"]
        for dept in dept_keywords:
            if dept.lower() in message.lower():
                context["department"] = dept
                break

        return context
