"""
Search Query Strategy Generator
Generates query-first strategy for SEARCH/RAG use cases
"""

from typing import Dict, List, Any
import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SearchDatasetRequirement:
    """Requirements for a search-oriented dataset"""
    name: str
    type: str  # 'documents', 'records', 'reference'
    row_count: str
    required_fields: Dict[str, str]
    semantic_fields: List[str]  # Fields using semantic_text
    relationships: List[str]


@dataclass
class SearchQueryRequirement:
    """Requirements for a search query"""
    name: str
    pain_point: str
    search_type: str  # 'semantic', 'keyword', 'hybrid', 'exact'
    required_datasets: List[str]
    required_fields: Dict[str, List[str]]
    description: str
    complexity: str


class SearchQueryStrategyGenerator:
    """Generates search/RAG query strategy BEFORE data generation"""

    def __init__(self, llm_client):
        """Initialize with LLM client

        Args:
            llm_client: Anthropic Claude client
        """
        self.llm_client = llm_client

    def generate_strategy(self, context: Dict) -> Dict:
        """Generate complete search strategy from customer context

        Args:
            context: Customer context with pain_points, use_cases, etc.

        Returns:
            Strategy dict with datasets, queries, search patterns
        """
        logger.info(f"Generating SEARCH strategy for {context.get('company_name')}")

        # Read ES|QL search skill for reference
        esql_skill = self._read_search_skill()

        prompt = self._build_strategy_prompt(context, esql_skill)

        # Call LLM to generate strategy
        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=8000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            strategy_text = response.content[0].text

            # Debug logging
            logger.info(f"Search strategy LLM response length: {len(strategy_text)}")
            print(f"\n{'='*70}")
            print(f"SEARCH STRATEGY LLM RESPONSE")
            print(f"{'='*70}")
            print(f"Length: {len(strategy_text)}")
            print(f"First 500 chars:\n{strategy_text[:500]}")
            print(f"Last 500 chars:\n{strategy_text[-500:]}")
            print(f"{'='*70}\n")

            strategy_json = self._extract_json(strategy_text)

            logger.info(f"Generated SEARCH strategy with {len(strategy_json.get('queries', []))} queries")
            return strategy_json

        except Exception as e:
            logger.error(f"Failed to generate search strategy: {e}", exc_info=True)
            logger.error(f"Raw response preview: {strategy_text[:1000] if 'strategy_text' in locals() else 'N/A'}")
            raise

    def _build_strategy_prompt(self, context: Dict, esql_skill: str) -> str:
        """Build the LLM prompt for search strategy generation"""

        prompt = f"""You are an ES|QL search expert designing a SEARCH/RAG demo for Elastic Agent Builder.

**Customer Context:**
- Company: {context.get('company_name')}
- Department: {context.get('department')}
- Industry: {context.get('industry')}
- Pain Points: {json.dumps(context.get('pain_points', []), indent=2)}
- Use Cases: {json.dumps(context.get('use_cases', []), indent=2)}
- Scale: {context.get('scale')}

**Your Task:**
Design 5-7 ES|QL SEARCH queries that help users FIND and RETRIEVE relevant information.
This is a SEARCH/RAG demo, NOT analytics. Focus on document retrieval, not aggregations.

**CRITICAL - Always Demonstrate Advanced Capabilities:**
While addressing the customer's pain points, ALWAYS include at least 2-3 sophisticated queries that showcase Elasticsearch's advanced search features:

1. **Weighted Hybrid Search** - Use `MATCH` with `{{"boost": X}}` to balance semantic vs exact matching
   Example: `MATCH(title_semantic, "term", {{"boost": 0.75}}) OR MATCH(title, "term", {{"boost": 0.25}})`

2. **Fuzzy Search** - Use `{{"fuzziness": "AUTO"}}` to handle typos and misspellings
   Example: `MATCH(product_name, "wireles headfones", {{"fuzziness": "AUTO"}})`

3. **Precision Control** - Use `{{"minimum_should_match": N}}` for multi-term queries
   Example: `MATCH(content, "configure email notification settings", {{"operator": "OR", "minimum_should_match": 3}})`

4. **Multi-field Search** - Search across multiple fields with different weights

5. **Phrase Matching** - Use `MATCH_PHRASE` for exact phrase searches with optional `{{"slop": N}}`

These advanced queries should feel natural to the use case, not forced. If customer pain points are basic,
frame these as "best practice" or "advanced optimization" examples.

**ES|QL Search Capabilities:**
{esql_skill}

**CRITICAL - This is a SEARCH Demo:**
1. Queries should RETRIEVE specific documents/records (not aggregate)
2. Use MATCH for semantic search, QSTR for complex searches, WHERE for exact matches
3. Focus on RELEVANCE (use _score), not metrics
4. Include semantic_text fields for vector search
5. Limit results (5-50 documents)
6. NO STATS, NO GROUP BY, NO aggregations (that's analytics, not search)
7. Choose correct index_mode:
   - **lookup**: Document collections (articles, policies, FAQs - even with timestamps!)
   - **data_stream**: Only for high-volume event logs (rare in search demos)

**Output Format (MUST be valid JSON):**
```json
{{
  "datasets": [
    {{
      "name": "knowledge_base_articles",
      "type": "documents",
      "row_count": "5000+",
      "required_fields": {{
        "article_id": "keyword",
        "title": "text",
        "content": "text",
        "content_semantic": "semantic_text",
        "category": "keyword",
        "author": "keyword",
        "created_date": "date",
        "tags": "keyword",
        "view_count": "long"
      }},
      "relationships": ["authors"],
      "semantic_fields": ["content_semantic"]
    }},
    {{
      "name": "authors",
      "type": "reference",
      "row_count": "100+",
      "required_fields": {{
        "author_id": "keyword",
        "author_name": "text",
        "department": "keyword",
        "expertise": "keyword"
      }},
      "relationships": ["knowledge_base_articles"],
      "semantic_fields": []
    }}
  ],
  "queries": [
    {{
      "name": "Basic Semantic Search",
      "pain_point": "Agents can't quickly find answers to customer questions",
      "search_type": "semantic",
      "required_datasets": ["knowledge_base_articles"],
      "required_fields": {{
        "knowledge_base_articles": ["title", "content_semantic", "category", "created_date"]
      }},
      "description": "Use semantic search to find most relevant articles for a customer inquiry",
      "complexity": "simple",
      "example_esql": "FROM knowledge_base_articles METADATA _score | WHERE MATCH(content_semantic, 'password reset procedure') | KEEP title, content, category, _score | SORT _score DESC | LIMIT 5"
    }},
    {{
      "name": "Weighted Hybrid Search - Best Practice",
      "pain_point": "Demonstrate advanced relevance tuning",
      "search_type": "hybrid",
      "required_datasets": ["knowledge_base_articles"],
      "required_fields": {{
        "knowledge_base_articles": ["title", "title_semantic", "content", "_score"]
      }},
      "description": "Balance semantic understanding with exact keyword matching using boost weights",
      "complexity": "advanced",
      "example_esql": "FROM knowledge_base_articles METADATA _score | WHERE MATCH(title_semantic, 'authentication error', {{'boost': 0.75}}) OR MATCH(title, 'authentication error', {{'boost': 0.25}}) | KEEP title, content, _score | SORT _score DESC | LIMIT 10"
    }},
    {{
      "name": "Fuzzy Search for Typo Tolerance",
      "pain_point": "Handle user typos and misspellings",
      "search_type": "fuzzy",
      "required_datasets": ["knowledge_base_articles"],
      "required_fields": {{
        "knowledge_base_articles": ["product_name", "description"]
      }},
      "description": "Find results even when search terms contain typos",
      "complexity": "advanced",
      "example_esql": "FROM products METADATA _score | WHERE MATCH(product_name, 'wireles headfones', {{'fuzziness': 'AUTO'}}) | KEEP product_name, category, price, _score | SORT _score DESC | LIMIT 20"
    }}
  ],
  "relationships": [
    {{
      "from": "knowledge_base_articles",
      "to": "authors",
      "type": "many-to-one",
      "join_field": "author_id"
    }}
  ]
}}
```

**Important Guidelines for SEARCH Demos:**
- Datasets should be document collections (articles, tickets, records, policies)
- Every text field that needs semantic search must have a corresponding semantic_text field
- Use MATCH for natural language queries
- Use QSTR for complex boolean/wildcard searches
- Use WHERE == for exact ID/category lookups
- Always include LIMIT (5-50 for search results)
- Include _score for relevance ranking
- Focus on "finding the right document" not "counting documents"

**Example Search Queries (NOT analytics):**
✅ GOOD: "Find all policies related to parental leave"
✅ GOOD: "Retrieve patient X's medical history"
✅ GOOD: "Search for support tickets similar to this issue"
❌ BAD: "Count how many tickets per category" (that's analytics)
❌ BAD: "Average response time by department" (that's analytics)

**MANDATORY - Include Advanced Queries:**
Of the 5-7 queries you design, AT LEAST 2-3 MUST be "advanced" complexity demonstrating:
- Weighted hybrid search with boost parameters
- Fuzzy search with fuzziness parameter
- Precision control with minimum_should_match
- Multi-field search across semantic and text fields
- Phrase matching with MATCH_PHRASE

Label these queries with "complexity": "advanced" and describe them as "best practices" or "optimization techniques".

Generate the complete SEARCH strategy as valid JSON:"""

        return prompt

    def _read_search_skill(self) -> str:
        """Read ES|QL search skill documentation"""
        try:
            skill_path = Path('.claude/skills/esql-search-patterns.md')
            if skill_path.exists():
                return skill_path.read_text()
            else:
                logger.warning("Search skill file not found, using minimal reference")
                return self._get_minimal_search_reference()
        except Exception as e:
            logger.warning(f"Could not read search skill: {e}")
            return self._get_minimal_search_reference()

    def _get_minimal_search_reference(self) -> str:
        """Get minimal search reference if skill file not available"""
        return """
ES|QL Search Commands:
- MATCH(field, "query"): Semantic/full-text search
- QSTR("query string"): Advanced search with boolean operators
- WHERE field == value: Exact match filtering
- _score: Relevance score (use for ranking)
- LIMIT N: Restrict number of results (always use for search)
- LOOKUP JOIN: Enrich search results with reference data
- semantic_text: Field type for vector search (requires ELSER)
"""

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response"""
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            json_text = text[start:end].strip()
        else:
            json_text = text.strip()

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"JSON text: {json_text[:500]}")
            raise ValueError(f"Invalid JSON in LLM response: {e}")

    def extract_data_requirements(self, strategy: Dict) -> Dict[str, Dict]:
        """Extract data generation requirements from search strategy"""
        data_requirements = {}

        for dataset in strategy.get('datasets', []):
            data_requirements[dataset['name']] = {
                'fields': dataset['required_fields'],
                'relationships': dataset.get('relationships', []),
                'semantic_fields': dataset.get('semantic_fields', []),
                'type': dataset['type'],
                'row_count': dataset.get('row_count', 'moderate')
            }

        return data_requirements

    def validate_strategy(self, strategy: Dict) -> bool:
        """Validate search strategy structure"""
        required_keys = ['datasets', 'queries', 'relationships']

        for key in required_keys:
            if key not in strategy:
                raise ValueError(f"Strategy missing required key: {key}")

        if not strategy['datasets']:
            raise ValueError("Strategy must have at least one dataset")

        if not strategy['queries']:
            raise ValueError("Strategy must have at least one query")

        # Validate dataset structure
        for dataset in strategy['datasets']:
            required_dataset_keys = ['name', 'type', 'required_fields']
            for key in required_dataset_keys:
                if key not in dataset:
                    raise ValueError(f"Dataset missing required key: {key}")

            if dataset['type'] not in ['documents', 'records', 'reference']:
                raise ValueError(f"Search dataset type must be 'documents', 'records', or 'reference', got: {dataset['type']}")

        # Validate query structure
        for query in strategy['queries']:
            required_query_keys = ['name', 'required_datasets', 'required_fields', 'search_type']
            for key in required_query_keys:
                if key not in query:
                    raise ValueError(f"Query missing required key: {key}")

        logger.info("Search strategy validation passed")
        return True
