"""
Search Query Strategy Generator
Generates query-first strategy for SEARCH/RAG use cases
Includes RAG query field analysis for MATCH → RERANK → COMPLETION pipeline
"""

from typing import Dict, List, Any, Optional
import json
import logging
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

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
7. Choose correct index_mode based on LOOKUP JOIN usage:
   - **index_mode: "lookup"** - If dataset will be used in ANY LOOKUP JOIN clause OR is reference data
   - **index_mode: "data_stream"** - If dataset is ONLY used in FROM clauses AND has a timestamp field

**CRITICAL - semantic_text Field Pattern:**
For fields that need semantic search (vector embeddings):
- **CORRECT**: Define ONLY ONE field as "semantic_text" type
  Example: "content": "semantic_text"
- **WRONG**: Do NOT create both a text field AND a semantic_text field
  Example: "content": "text" + "content_semantic": "semantic_text" ← ANTIPATTERN!
- Elasticsearch automatically handles BOTH text storage AND embedding generation for semantic_text fields
- The data generator will create ONE column with text data
- Elasticsearch will auto-generate embeddings using ELSER v2 (.elser-2-elasticsearch)
- Reference: https://www.elastic.co/search-labs/blog/semantic-search-simplified-semantic-text

**CRITICAL Index Mode Decision Rule:**
For each dataset, determine index_mode based on how it will be used:
1. **Will this dataset appear in LOOKUP JOIN?** → index_mode: "lookup"
2. **Used ONLY in FROM + has @timestamp?** → index_mode: "data_stream"
3. **Used ONLY in FROM + NO timestamp?** → index_mode: "lookup"

Examples:
- knowledge_base (FROM only, no @timestamp) → index_mode: "lookup"
- providers (used in "LOOKUP JOIN providers") → index_mode: "lookup"
- call_logs (FROM only, has @timestamp) → index_mode: "data_stream"

**NOTE**: Most search demos use lookup mode for ALL datasets (document collections).
Only use data_stream for high-volume event logs with timestamps.

**Output Format (MUST be valid JSON):**
```json
{{
  "datasets": [
    {{
      "name": "knowledge_base_articles",
      "type": "documents",
      "index_mode": "lookup",
      "row_count": "5000+",
      "required_fields": {{
        "article_id": "keyword",
        "title": "text",
        "content": "semantic_text",
        "category": "keyword",
        "author": "keyword",
        "created_date": "date",
        "tags": "keyword",
        "view_count": "long"
      }},
      "relationships": ["authors"],
      "semantic_fields": ["content"]
    }},
    {{
      "name": "authors",
      "type": "reference",
      "index_mode": "lookup",
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

            if dataset['type'] not in ['documents', 'records', 'reference', 'events']:
                raise ValueError(f"Search dataset type must be 'documents', 'records', 'reference', or 'events', got: {dataset['type']}")

        # Validate query structure
        for query in strategy['queries']:
            required_query_keys = ['name', 'required_datasets', 'required_fields', 'search_type']
            for key in required_query_keys:
                if key not in query:
                    raise ValueError(f"Query missing required key: {key}")

        logger.info("Search strategy validation passed")
        return True


class RAGFieldAnalyzer:
    """Analyzes dataset schema to identify optimal fields for RAG queries

    Supports the MATCH → RERANK → COMPLETION pipeline by identifying:
    - Text fields suitable for MATCH
    - Fields for RERANK (important text content)
    - Fields for LLM context
    - Temporal boundaries
    """

    def __init__(self, dataset_schema: Dict[str, str]):
        """Initialize with dataset schema

        Args:
            dataset_schema: Dict mapping field names to types
                Example: {"title": "text", "content": "text", "@timestamp": "date"}
        """
        self.schema = dataset_schema

    def identify_text_fields(self) -> List[str]:
        """Find text/keyword fields suitable for MATCH

        Looks for common text field patterns:
        - description, summary, content, message, feedback
        - title, subject, headline
        - notes, comments, details
        - Any field with 'text' or 'keyword' type

        Returns:
            List of field names suitable for semantic search
        """
        text_fields = []
        text_keywords = [
            'description', 'summary', 'content', 'message', 'feedback',
            'title', 'subject', 'headline', 'body', 'text',
            'notes', 'comments', 'details', 'explanation', 'reason'
        ]

        for field_name, field_type in self.schema.items():
            # Include if field type is text or keyword
            if field_type in ('text', 'keyword', 'semantic_text'):
                text_fields.append(field_name)
            # Or if field name suggests text content
            elif any(keyword in field_name.lower() for keyword in text_keywords):
                text_fields.append(field_name)

        logger.info(f"Identified {len(text_fields)} text fields for MATCH: {text_fields}")
        return text_fields

    def identify_rerank_fields(self, text_fields: Optional[List[str]] = None) -> List[str]:
        """Find most important text fields for RERANK

        Selects 2-4 most important text fields from text_fields.
        Prioritizes:
        - Primary content fields (description, content, message)
        - User-generated content (feedback, comments)
        - Resolution/outcome fields

        Args:
            text_fields: Optional list of text fields (calls identify_text_fields if not provided)

        Returns:
            List of 2-4 most important text fields for reranking
        """
        if text_fields is None:
            text_fields = self.identify_text_fields()

        # Priority keywords (higher priority = higher score)
        priority_map = {
            'content': 10,
            'description': 9,
            'message': 8,
            'feedback': 7,
            'comments': 6,
            'summary': 5,
            'notes': 4,
            'title': 3,
            'subject': 2
        }

        # Score each field
        scored_fields = []
        for field in text_fields:
            score = 0
            field_lower = field.lower()
            for keyword, priority in priority_map.items():
                if keyword in field_lower:
                    score = max(score, priority)
            scored_fields.append((field, score))

        # Sort by score (descending) and take top 2-4
        scored_fields.sort(key=lambda x: x[1], reverse=True)
        rerank_fields = [field for field, score in scored_fields[:4]]

        # Ensure we have at least 2 fields
        if len(rerank_fields) < 2 and text_fields:
            rerank_fields = text_fields[:min(4, len(text_fields))]

        logger.info(f"Identified {len(rerank_fields)} fields for RERANK: {rerank_fields}")
        return rerank_fields

    def identify_context_fields(self) -> List[str]:
        """Find fields to include in LLM context

        Includes ID fields, status fields, metadata, and all text fields.
        Excludes internal/system fields.

        Returns:
            List of field names to include in COMPLETION prompt
        """
        context_fields = []
        exclude_patterns = ['_', 'internal', 'system', 'meta']

        for field_name, field_type in self.schema.items():
            # Exclude fields with underscore prefix (internal fields)
            if field_name.startswith('_'):
                continue
            # Exclude if matches exclude patterns
            if any(pattern in field_name.lower() for pattern in exclude_patterns[1:]):
                continue
            # Include all other fields
            context_fields.append(field_name)

        logger.info(f"Identified {len(context_fields)} fields for context: {context_fields}")
        return context_fields

    def determine_time_boundary(self, row_count_estimate: str = "moderate") -> str:
        """Determine appropriate time range for temporal queries

        Based on data volume, suggests time boundary:
        - Small/Few: 30 days
        - Moderate: 90 days
        - Large/Many: 120 days

        Args:
            row_count_estimate: Estimated data volume ("small", "moderate", "large")

        Returns:
            Time boundary string (e.g., "90 days")
        """
        # Check if schema has timestamp field
        has_timestamp = any(
            '@timestamp' in field or 'timestamp' in field.lower() or 'date' in field.lower()
            for field in self.schema.keys()
        )

        if not has_timestamp:
            logger.warning("No timestamp field found, time boundary may not be applicable")
            return "120 days"  # Default fallback

        # Determine boundary based on volume
        if 'small' in row_count_estimate.lower() or 'few' in row_count_estimate.lower():
            boundary = "30 days"
        elif 'large' in row_count_estimate.lower() or 'many' in row_count_estimate.lower():
            boundary = "120 days"
        else:  # moderate or unknown
            boundary = "90 days"

        logger.info(f"Determined time boundary: {boundary} (volume: {row_count_estimate})")
        return boundary

    def generate_rag_template_config(self, dataset_name: str, row_count: str = "moderate") -> Dict[str, Any]:
        """Generate complete RAG query configuration

        Analyzes schema and returns all necessary information for
        generating a RAG query template.

        Args:
            dataset_name: Name of the dataset/index
            row_count: Estimated row count

        Returns:
            Dict with:
            - search_fields: Fields for MATCH
            - rerank_fields: Fields for RERANK
            - context_fields: Fields for COMPLETION context
            - time_boundary: Time range string
            - index_name: Dataset name
        """
        text_fields = self.identify_text_fields()
        rerank_fields = self.identify_rerank_fields(text_fields)
        context_fields = self.identify_context_fields()
        time_boundary = self.determine_time_boundary(row_count)

        config = {
            "index_name": dataset_name,
            "search_fields": text_fields,
            "rerank_fields": rerank_fields,
            "context_fields": context_fields,
            "time_boundary": time_boundary,
            "has_timestamp": any('@timestamp' in f or 'timestamp' in f.lower() for f in self.schema.keys())
        }

        logger.info(f"Generated RAG template config for {dataset_name}")
        logger.debug(f"Config: {json.dumps(config, indent=2)}")

        return config
