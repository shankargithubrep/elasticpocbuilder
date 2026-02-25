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

# Fixed dataset sizes for search/RAG demos
# Search demos need smaller datasets (500-1000) vs analytics (5000-50000)
# because they only display top 10-20 results by relevance score
SIZE_RANGES = {
    'documents': '500-1000',
    'reference': '200-500'
}


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

        # STEP 1: Generate search narrative FIRST (new)
        # This defines the key search scenarios and target phrases
        from src.services.search_narrative_generator import SearchNarrativeGenerator

        narrative_gen = SearchNarrativeGenerator(self.llm_client)
        search_narrative = narrative_gen.generate_narrative({
            "industry": context.get("industry"),
            "business_category": context.get("business_category", context.get("department")),
            "pain_points": context.get("pain_points", []),
            "use_cases": context.get("use_cases", [])
        })

        logger.info(f"Generated search narrative with {len(search_narrative['search_scenarios'])} scenarios")

        # Add narrative to context for use in prompts
        context["search_narrative"] = search_narrative

        # STEP 2: Generate CUSTOM domain library from narrative and context
        # This creates domain-specific keywords extracted from the search scenarios
        from src.services.custom_domain_library_generator import CustomDomainLibraryGenerator

        library_gen = CustomDomainLibraryGenerator(self.llm_client)
        custom_library = library_gen.generate_library(
            customer_context=context,
            search_narrative=search_narrative
        )

        logger.info(f"Generated custom domain library with {len(custom_library)} categories, "
                   f"{sum(len(v) for v in custom_library.values())} total keywords")

        # Add custom library to context for use in data generation
        context["custom_domain_library"] = custom_library

        # Extract dataset size preference (default to 'medium' if not specified)
        size_preference = context.get('dataset_size_preference', 'medium')
        logger.info(f"Using dataset size preference: {size_preference}")

        # Read ES|QL search skill for reference
        esql_skill = self._read_search_skill()

        prompt = self._build_strategy_prompt(context, esql_skill, size_preference)

        # Call LLM to generate strategy
        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=16000,  # Increased from 8000 to accommodate search narrative + full strategy
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            strategy_text = response.content[0].text

            # Debug logging (only to logger, not console)
            logger.debug(f"Search strategy LLM response length: {len(strategy_text)}")
            logger.debug(f"Search strategy preview: {strategy_text[:500]}")

            strategy_json = self._extract_json(strategy_text)

            # Add search narrative and custom library to strategy
            strategy_json["search_narrative"] = search_narrative
            strategy_json["custom_domain_library"] = custom_library

            logger.info(f"Generated SEARCH strategy with {len(strategy_json.get('queries', []))} queries")
            return strategy_json

        except Exception as e:
            logger.error(f"Failed to generate search strategy: {e}", exc_info=True)
            logger.error(f"Raw response preview: {strategy_text[:1000] if 'strategy_text' in locals() else 'N/A'}")
            raise

    def _build_strategy_prompt(self, context: Dict, esql_skill: str, size_preference: str = 'medium') -> str:
        """Build the LLM prompt for search strategy generation

        Args:
            context: Customer context
            esql_skill: ES|QL skill documentation
            size_preference: Dataset size preference - 'small', 'medium', or 'large' (default 'medium')

        Returns:
            Prompt string
        """
        # Fixed size ranges for search demos (size_preference ignored)
        documents_range = SIZE_RANGES['documents']
        reference_range = SIZE_RANGES['reference']

        # Check if we have rich technical context for high-fidelity generation
        full_context = context.get('full_technical_context')

        if full_context:
            # Use rich technical document for detailed field names and implementation guidance
            context_section = f"""**Customer Context (Full Technical Document):**

{full_context}

**Summary Fields (for tracking):**
- Company: {context.get('company_name')}
- Department: {context.get('department')}
- Industry: {context.get('industry')}
- Demo Type: search/RAG"""
        else:
            # Fallback to basic fields
            context_section = f"""**Customer Context:**
- Company: {context.get('company_name')}
- Department: {context.get('department')}
- Industry: {context.get('industry')}
- Pain Points: {json.dumps(context.get('pain_points', []), indent=2)}
- Use Cases: {json.dumps(context.get('use_cases', []), indent=2)}"""

        prompt = f"""You are an ES|QL search expert designing a SEARCH/RAG demo for Elastic Agent Builder.

{context_section}

**Your Task:**
Design 5-7 ES|QL SEARCH queries that help users FIND and RETRIEVE relevant information.
This is a SEARCH/RAG demo, NOT analytics. Focus on document retrieval, not aggregations.

**CRITICAL - If Full Technical Document Provided:**
- Extract EXACT field names from the technical document for semantic_text fields
- Reference specific document types and search use cases mentioned
- Design document collections that match the described content types

**CRITICAL - Always Demonstrate Advanced Capabilities:**
While addressing the customer's pain points, ALWAYS include sophisticated queries that showcase Elasticsearch's advanced search features.

**MANDATORY: Include at least 1-2 queries using these ADVANCED HYBRID SEARCH commands:**

1. **FORK + FUSE Pipeline** - Multi-branch parallel search with score fusion

   **Simple FUSE (RRF - recommended for hybrid queries):**
   ```esql
   FROM index METADATA _id, _index, _score
   | FORK (WHERE MATCH(title, "exact term") | EVAL search_type = "bm25" | SORT _score DESC | LIMIT 50)
          (WHERE MATCH(content_semantic, "natural language query") | EVAL search_type = "semantic" | SORT _score DESC | LIMIT 50)
   | FUSE
   | SORT _score DESC
   | LIMIT 20
   | KEEP doc_id, title, content, _score, search_type
   ```
   Use `EVAL search_type = "..."` to label which branch each result came from. Include `search_type` in KEEP.

   **⚠️ CRITICAL: SORT _score DESC MUST come AFTER FUSE and BEFORE the first LIMIT!**

   **Key insight: FIELD TYPE determines search behavior:**
   - MATCH on `text` field → BM25 (lexical/keyword search)
   - MATCH on `semantic_text` field → semantic (vector similarity)
   - True hybrid REQUIRES both a `text` field AND a `semantic_text` field in the dataset!

   **Weighted LINEAR FUSE (for expert/sophisticated queries):**
   ```esql
   FROM index METADATA _id, _index, _score
   | FORK (WHERE MATCH(title, "term") | EVAL search_type = "bm25" | SORT _score DESC | LIMIT 50)
          (WHERE MATCH(content_semantic, "query") | EVAL search_type = "semantic" | SORT _score DESC | LIMIT 50)
   | FUSE LINEAR WITH {{ "weights": {{ "fork1": 0.3, "fork2": 0.7 }}, "normalizer": "minmax" }}
   | SORT _score DESC
   | LIMIT 20
   | KEEP doc_id, title, content, _score, search_type
   ```

   **FUSE Variety Guidelines:**
   - `FUSE` (default RRF) - Use for "hybrid" complexity, position-based fusion
   - `FUSE LINEAR WITH {{...}}` - Use for "sophisticated" complexity, explicit weight control

2. **RERANK** - ML-based relevance reranking for precision
   ```esql
   | RERANK "query text" ON content_field WITH {{ "inference_id": ".rerank-v1-elasticsearch" }}
   ```
   Add RERANK after initial retrieval to improve result quality with ML models.

3. **COMPLETION** - LLM text generation for RAG answers/summaries
   ```esql
   | EVAL prompt = CONCAT("Summarize: ", content)
   | COMPLETION summary = prompt WITH {{ "inference_id": "completion-vulcan" }}
   ```
   Use after retrieval to generate answers, summaries, or insights.

**Search Type Definitions (for query classification):**
| Search Type | Description | Pattern |
|------------|-------------|---------|
| `bm25` | BM25/keyword search on `text` field | `MATCH(text_field, "term")` |
| `semantic` | Semantic search on `semantic_text` field | `MATCH(semantic_field, "query")` |
| `fuzzy` | BM25 with typo tolerance | `MATCH(field, "term", {{"fuzziness": "AUTO"}})` |
| `hybrid` | FORK+FUSE combining BM25 + semantic (simple RRF) | `FORK (...) (...) | FUSE | SORT _score DESC` |
| `hybrid_weighted` | FORK+FUSE LINEAR with explicit weights | `FORK (...) (...) | FUSE LINEAR WITH {{...}} | SORT _score DESC` |
| `rerank` | Pipeline with ML reranking | `MATCH | SORT | LIMIT | RERANK | LIMIT` |
| `rag_completion` | Pipeline with LLM generation | `MATCH | LIMIT | EVAL prompt | COMPLETION` |

**Also include these standard advanced features:**

4. **Fuzzy Search** - Use `{{"fuzziness": "AUTO"}}` to handle typos and misspellings
   Example: `MATCH(product_name, "wireles headfones", {{"fuzziness": "AUTO"}})`

5. **Precision Control** - Use `{{"minimum_should_match": N}}` for multi-term queries
   Example: `MATCH(content, "configure email notification settings", {{"operator": "OR", "minimum_should_match": 3}})`

6. **Multi-field BM25 with Boost** - Weight multiple text fields (NOT hybrid - both are BM25)
   Example: `MATCH(title, "term", {{"boost": 0.7}}) OR MATCH(summary, "term", {{"boost": 0.3}})`
   Note: This is weighted multi-field BM25, NOT hybrid (no semantic search involved)

**Query Complexity Targets (MANDATORY):**
- At least 1-2 queries MUST use FORK + FUSE for true hybrid search (BM25 + semantic)
- At least 1 query SHOULD use RERANK for ML reranking
- At least 1 query SHOULD use COMPLETION for RAG/summarization
- All queries should feel natural to the use case, not forced

**ES|QL Search Capabilities:**
{esql_skill}

**CRITICAL - ES|QL Syntax Rules (NOT Elasticsearch Query DSL):**
❌ NEVER use colon syntax: `field:"value"` (this is Query DSL, NOT ES|QL!)
✅ Use MATCH for full-text search: `WHERE MATCH(field, "search terms")`
✅ Use LIKE for pattern matching: `WHERE field LIKE "*value*"`
✅ Use == for exact keyword match: `WHERE field == "exact value"`

Example of WRONG vs CORRECT:
- WRONG: `WHERE provider_name:"Dr Smith"` ← Query DSL syntax, will fail!
- CORRECT: `WHERE MATCH(provider_name, "Dr Smith")` ← ES|QL syntax
- CORRECT: `WHERE provider_name LIKE "*Smith*"` ← Pattern matching

**CRITICAL - This is a SEARCH Demo:**
1. Queries should RETRIEVE specific documents/records (not aggregate)
2. Use MATCH for full-text search on `text` fields (NOT keyword fields!)
3. Use LIKE for pattern matching on any string field
4. Use == for exact matches on `keyword` fields
5. Focus on RELEVANCE (use _score), not metrics
6. Include semantic_text fields for vector search
7. Limit results (5-50 documents)
8. NO STATS, NO GROUP BY, NO aggregations (that's analytics, not search)
9. Choose correct index_mode based on LOOKUP JOIN usage:
   - **index_mode: "lookup"** - If dataset will be used in ANY LOOKUP JOIN clause OR is reference data
   - **index_mode: "data_stream"** - If dataset is ONLY used in FROM clauses AND has a timestamp field

**CRITICAL - semantic_text Field Requirements for Hybrid Search:**

**⚠️ MANDATORY: Each searchable dataset MUST include:**
- At least one `text` field for BM25 search (names, titles, short text)
- At least one `semantic_text` field for semantic search (descriptions, content, bios, summaries)

**Without a semantic_text field, true hybrid search is IMPOSSIBLE!**

Example dataset fields:
```json
{{
  "provider_name": "text",              // For BM25 search
  "provider_bio": "semantic_text"       // For semantic search - REQUIRED for hybrid!
}}
```

**semantic_text Field Pattern:**
- **CORRECT**: Use the main descriptive field as semantic_text directly
  Example: "description": "semantic_text", "title": "text"
- **WRONG**: Do NOT create BOTH a text description AND a separate semantic_text description
  Example: "description": "text" + "semantic_description": "semantic_text" ← ANTIPATTERN!
  Example: "content": "text" + "content_summary": "semantic_text" ← ANTIPATTERN!
- Each dataset should have EXACTLY TWO searchable text fields:
  1. A short text field for BM25 (title, name, headline) — type: "text"
  2. A long descriptive field for semantic search — type: "semantic_text"
- Do NOT prefix or suffix field names with "semantic_" — just use the natural field name
- Elasticsearch automatically handles BOTH text storage AND embedding generation for semantic_text fields
- The data generator will create ONE column with text data
- Elasticsearch will auto-generate embeddings using ELSER v2 (.elser-2-elasticsearch)
- Reference: https://www.elastic.co/search-labs/blog/semantic-search-simplified-semantic-text

**Good candidates for semantic_text:**
- Descriptions, summaries, bios, overviews
- Content, body, notes, details
- Explanations, reasons, feedback
- Any field with natural language that benefits from meaning-based search

**🎯 CRITICAL: Content Diversity for Score Differentiation**

For search demos to show meaningful score differences, data MUST have **tiered relevance**:

**Tier 1 - Highly Relevant (~20% of docs):**
- Exact keyword matches in titles/names
- Dense topic coverage with specific terminology
- Multiple mentions of key search terms

**Tier 2 - Moderately Relevant (~40% of docs):**
- Related but not exact terms (synonyms, related concepts)
- Partial topic coverage
- Some relevant keywords but not dominant

**Tier 3 - Low Relevance (~40% of docs):**
- Different topics entirely
- Generic or unrelated content
- No keyword overlap with common searches

**Example tiering structure (adapt to customer's domain):**
- Tier 1: [Profile with ALL key attributes - exact match for common queries]
- Tier 2: [Profile with SOME key attributes - partial match]
- Tier 3: [Profile with DIFFERENT attributes - low/no relevance]

⚠️ Use terminology from the customer's actual use case, not these placeholders.

Without tiered content, all documents score similarly and the demo fails to show relevance ranking!

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

**⚠️ CRITICAL ES|QL ANTI-PATTERNS TO AVOID:**
❌ NEVER use window functions: LAG(), LEAD(), OVER, PARTITION BY (in window context)
❌ NEVER use ranking functions: ROW_NUMBER(), RANK(), DENSE_RANK()
❌ NEVER try to reference other rows: metric[-1], previous values, or row positions
❌ NEVER use unsupported syntax like: OVER (ORDER BY...), OVER (PARTITION BY...)

**✅ For Search Queries, Remember:**
- Search queries focus on RETRIEVAL, not complex analytics
- Use SORT and LIMIT for ranking, not ROW_NUMBER()
- Use _score for relevance ranking (automatically calculated by MATCH)
- INLINESTATS is rarely needed in search (it's for analytics)

**⚠️ IMPORTANT: _score is a COMPUTED field, not source data**
- _score is calculated at query time by Elasticsearch for MATCH queries
- DO NOT include _score in "required_fields" - it's not part of the indexed data
- You access _score using METADATA _score clause in FROM statement
- Only use _score in KEEP, SORT, and EVAL - it doesn't exist in the source documents

**Example of CORRECT search ranking:**
```esql
FROM knowledge_base
| MATCH(content, "user query")
| SORT _score DESC
| LIMIT 10
```

**🎯 CRITICAL: KEEP Field Prioritization for Agent Tool Calls**
⚠️ **ONLY THE FIRST 5 FIELDS in KEEP are visible to agents!** Fields 6+ are truncated in tool responses.

**For SEARCH queries, prioritize fields like this:**
1. **Position 1**: Document/entity ID (for retrieval)
2. **Position 2**: Relevance score or rank
3. **Position 3**: Title or name (for display)
4. **Position 4**: Content snippet or summary
5. **Position 5**: Category or type
6. **Positions 6+**: Metadata (author, date, tags) - NOT visible to agents

**Example KEEP for search:**
```esql
// GOOD: Most relevant fields first
| KEEP article_id, _score, title, content_snippet, category, author, created_date

// BAD: ID and title buried
| KEEP created_date, author, tags, status, article_id, title, content
```

**⚠️ CRITICAL: NEVER Parameterize @timestamp**
❌ **DO NOT parameterize @timestamp or system timestamp fields!**

**For search queries, use relative time:**
```esql
// ✅ GOOD: Relative time with NOW()
FROM documents
| WHERE @timestamp >= NOW() - 30 days
| MATCH(content, "search term")

// ❌ BAD: Parameterized @timestamp
FROM documents
| WHERE @timestamp >= ?start_date  ❌ DON'T DO THIS!
```

**Date Parameterization Rules:**
- ❌ `@timestamp` → IF filtering on it, use `NOW() - X days/hours` (NEVER parameterize - it's an Elasticsearch system field)
- ⚠️ Only add time filters when part of the use case (e.g., "recent documents", "published this month")
- ⚠️ Don't add @timestamp filters to every query - data is static, so time-based filters become stale
- ✅ Other date fields (e.g., `created_at`, `published_date`, `effective_date`) → Can parameterize based on query purpose

**🎯 CRITICAL: Dataset Size Requirements ({size_preference.upper()} preference)**

You MUST use these EXACT row_count ranges in your output:
- Document collections (e.g., policies, articles, FAQs, knowledge base): "{documents_range}"
- Reference datasets (e.g., categories, users, metadata): "{reference_range}"

**IMPORTANT:**
- Use cardinality appropriate for the industry (realistic distribution)
- DO NOT calculate row counts based on business size (e.g., "10k documents × 5 categories")
- ALWAYS use the template ranges above for row_count fields
- Use cardinality_notes to explain data distribution, NOT to justify larger row counts

**Example (CORRECT):**
```json
{{
  "name": "policy_documents",
  "row_count": "{documents_range}",  // ✅ Use this exact template value
  "cardinality_notes": "Distributed across 50 categories and 10 regions for dense search results"
}}
```

**Example (WRONG):**
```json
{{
  "name": "policy_documents",
  "row_count": "25000",  // ❌ DO NOT calculate your own row count
  "cardinality_notes": "5k documents × 5 categories = 25k total documents"
}}
```

**Output Format (MUST be valid JSON):**
```json
{{
  "datasets": [
    {{
      "name": "knowledge_base_articles",
      "type": "documents",
      "index_mode": "lookup",
      "row_count": "{documents_range}",
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
      "semantic_fields": ["content"],
      "text_fields": ["title"]
    }},
    {{
      "name": "authors",
      "type": "reference",
      "index_mode": "lookup",
      "row_count": "{reference_range}",
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
      "name": "article_search_bm25",
      "pain_point": "Agents can't quickly find answers to customer questions",
      "search_type": "keyword",
      "required_datasets": ["knowledge_base_articles"],
      "required_fields": {{
        "knowledge_base_articles": ["article_id", "title", "content", "category"]
      }},
      "description": "BM25 keyword search - fast but requires exact term matches",
      "complexity": "simple",
      "variant_group": "article_search",
      "example_esql": "FROM knowledge_base_articles METADATA _score | WHERE MATCH(title, \"password reset\") | KEEP article_id, _score, title, content, category | SORT _score DESC | LIMIT 10"
    }},
    {{
      "name": "article_search_semantic",
      "pain_point": "Agents can't quickly find answers to customer questions",
      "search_type": "semantic",
      "required_datasets": ["knowledge_base_articles"],
      "required_fields": {{
        "knowledge_base_articles": ["article_id", "title", "content", "category"]
      }},
      "description": "Semantic search - understands meaning, handles synonyms and related concepts",
      "complexity": "medium",
      "variant_group": "article_search",
      "example_esql": "FROM knowledge_base_articles METADATA _score | WHERE MATCH(content, 'how to reset my password forgot login') | KEEP article_id, _score, title, content, category | SORT _score DESC | LIMIT 10"
    }},
    {{
      "name": "article_search_hybrid",
      "pain_point": "Agents can't quickly find answers to customer questions",
      "search_type": "hybrid",
      "required_datasets": ["knowledge_base_articles"],
      "required_fields": {{
        "knowledge_base_articles": ["article_id", "title", "content", "category", "search_type"]
      }},
      "description": "True hybrid search - FORK/FUSE combining BM25 on text field with semantic on semantic_text field",
      "complexity": "advanced",
      "variant_group": "article_search",
      "example_esql": "FROM knowledge_base_articles METADATA _id, _index, _score | FORK (WHERE MATCH(title, 'password reset') | EVAL search_type = 'bm25' | SORT _score DESC | LIMIT 50) (WHERE MATCH(content, 'forgot login help password') | EVAL search_type = 'semantic' | SORT _score DESC | LIMIT 50) | FUSE | SORT _score DESC | LIMIT 10 | KEEP article_id, _score, title, content, category, search_type"
    }},
    {{
      "name": "article_search_sophisticated",
      "pain_point": "Agents can't quickly find answers to customer questions",
      "search_type": "hybrid_weighted",
      "required_datasets": ["knowledge_base_articles"],
      "required_fields": {{
        "knowledge_base_articles": ["article_id", "title", "content", "category", "search_type"]
      }},
      "description": "Sophisticated hybrid - FORK/FUSE LINEAR with explicit weights for tuned BM25/semantic balance",
      "complexity": "expert",
      "variant_group": "article_search",
      "example_esql": "FROM knowledge_base_articles METADATA _id, _index, _score | FORK (WHERE MATCH(title, 'password reset') | EVAL search_type = 'bm25' | SORT _score DESC | LIMIT 50) (WHERE MATCH(content, 'forgot login help password') | EVAL search_type = 'semantic' | SORT _score DESC | LIMIT 50) | FUSE LINEAR WITH {{ 'weights': {{ 'fork1': 0.4, 'fork2': 0.6 }}, 'normalizer': 'minmax' }} | SORT _score DESC | LIMIT 10 | KEEP article_id, _score, title, content, category, search_type"
    }},
    {{
      "name": "Multi-Strategy Hybrid Search with FORK + FUSE",
      "pain_point": "Need to combine exact matching with semantic understanding",
      "search_type": "hybrid",
      "required_datasets": ["knowledge_base_articles"],
      "required_fields": {{
        "knowledge_base_articles": ["article_id", "title", "content", "search_type"]
      }},
      "description": "Use FORK to run BM25 and semantic searches in parallel with search_type labels, then FUSE (RRF) to combine results",
      "complexity": "advanced",
      "example_esql": "FROM knowledge_base_articles METADATA _id, _index, _score | FORK (WHERE MATCH(title, 'authentication') | EVAL search_type = 'bm25' | SORT _score DESC | LIMIT 50) (WHERE MATCH(content, 'authentication login error') | EVAL search_type = 'semantic' | SORT _score DESC | LIMIT 50) | FUSE | SORT _score DESC | LIMIT 20 | KEEP article_id, _score, title, content, search_type"
    }},
    {{
      "name": "Precision Search with ML Reranking",
      "pain_point": "Initial search results need better relevance ranking",
      "search_type": "rerank",
      "required_datasets": ["knowledge_base_articles"],
      "required_fields": {{
        "knowledge_base_articles": ["article_id", "title", "content", "_score"]
      }},
      "description": "Retrieve candidates with semantic search, then use ML reranking for precision",
      "complexity": "expert",
      "example_esql": "FROM knowledge_base_articles METADATA _score | WHERE MATCH(content, 'configure SSO single sign-on') | SORT _score DESC | LIMIT 50 | RERANK \\"how to configure SSO\\" ON content, title WITH {{ \\"inference_id\\": \\".rerank-v1-elasticsearch\\" }} | LIMIT 10 | KEEP article_id, _score, title, content, category"
    }},
    {{
      "name": "RAG Answer Generation with COMPLETION",
      "pain_point": "Users need synthesized answers, not just document lists",
      "search_type": "rag_completion",
      "required_datasets": ["knowledge_base_articles"],
      "required_fields": {{
        "knowledge_base_articles": ["title", "content"]
      }},
      "description": "Retrieve relevant documents and generate a synthesized answer using LLM",
      "complexity": "expert",
      "example_esql": "FROM knowledge_base_articles METADATA _score | WHERE MATCH(content, 'password reset procedure') | SORT _score DESC | LIMIT 5 | EVAL prompt = CONCAT(\\"Based on this article, summarize the password reset steps:\\\\n\\\\nTitle: \\", title, \\"\\\\nContent: \\", content) | COMPLETION summary = prompt WITH {{ \\"inference_id\\": \\"completion-vulcan\\" }} | KEEP title, summary, _score"
    }},
    {{
      "name": "Fuzzy Search for Typo Tolerance",
      "pain_point": "Handle user typos and misspellings",
      "search_type": "fuzzy",
      "required_datasets": ["knowledge_base_articles"],
      "required_fields": {{
        "knowledge_base_articles": ["article_id", "title", "content"]
      }},
      "description": "Find results even when search terms contain typos",
      "complexity": "advanced",
      "example_esql": "FROM knowledge_base_articles METADATA _score | WHERE MATCH(title, 'authentacation eror', {{'fuzziness': 'AUTO'}}) | KEEP article_id, _score, title, content, category | SORT _score DESC | LIMIT 20"
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

**🎯 CRITICAL: Data-Query Alignment for Meaningful Results:**

Your queries will search for specific terms. The data generator MUST create content that:
1. **Contains exact matches** for your search terms (for high scores)
2. **Contains related content** (for medium scores)
3. **Contains unrelated content** (for low scores - demonstrates contrast)

When designing queries, consider:
- What search terms will users type?
- Does the dataset contain documents that will match those terms?
- Will there be score diversity (some docs score 15, others score 3)?

**Example of Good Data-Query Alignment:**
- Query searches for "[specific topic from customer context]"
- Dataset MUST contain:
  - Documents directly about [that topic] (high relevance)
  - Documents about [related/broader topic] (medium relevance)
  - Documents about [tangentially related topic] (low relevance)

**Example of BAD Alignment (will fail):**
- Query searches for "[specific topic]"
- Dataset only contains documents about unrelated topics
- Result: No relevant documents found, demo fails!

⚠️ **CRITICAL**: Use topics from the customer's actual domain/context. DO NOT copy these placeholder examples.

When generating the query strategy, ensure the queries align with realistic content that the data generator can create.

**🎯 CRITICAL: Multi-Strategy Query Variants (Required for 2-3 key queries)**

For 2-3 of your most important queries, generate FOUR variants demonstrating the progression of search sophistication.
This showcases Elastic's relevancy capabilities and helps SAs demonstrate "here's basic search vs sophisticated search."

**Variant Naming Convention (Encouraged):**
Use a suffix to indicate the search strategy:
- `{{query_name}}_bm25` - Simple keyword/BM25 search on text field (baseline)
- `{{query_name}}_semantic` - Semantic search on semantic_text field
- `{{query_name}}_fuzzy` - BM25 with fuzziness for typo tolerance
- `{{query_name}}_hybrid` - **FORK+FUSE (simple RRF)** combining BM25 + semantic
- `{{query_name}}_sophisticated` - **FORK+FUSE LINEAR** with explicit weights
- `{{query_name}}_rerank` - Pipeline with RERANK for ML reranking
- `{{query_name}}_rag` or `{{query_name}}_completion` - Pipeline with COMPLETION for LLM generation

**Example Variant Set:**
For a "Provider Search" query, generate these variants:

1. **provider_search_bm25** (complexity: "simple")
   - Uses BM25 on text field: `WHERE MATCH(provider_name, "Dr Smith")`
   - Shows baseline keyword scoring

2. **provider_search_semantic** (complexity: "medium")
   - Uses semantic on semantic_text field: `WHERE MATCH(provider_bio, "heart specialist")`
   - Shows meaning understanding

3. **provider_search_hybrid** (complexity: "advanced")
   - Uses FORK+FUSE (simple RRF): `FORK (BM25) (semantic) | FUSE | SORT _score DESC`
   - Shows true hybrid combining both approaches

4. **provider_search_sophisticated** (complexity: "expert")
   - Uses FORK+FUSE LINEAR with weights: `FORK (...) (...) | FUSE LINEAR WITH {{...}} | SORT _score DESC`
   - Shows tunable weighting between BM25 and semantic

5. **provider_search_rerank** (complexity: "expert")
   - Pipeline with RERANK: `MATCH | SORT | LIMIT | RERANK | LIMIT`
   - Shows ML-based relevance reranking

6. **provider_search_rag** (complexity: "expert")
   - Pipeline with COMPLETION: `MATCH | LIMIT | EVAL prompt | COMPLETION`
   - Shows LLM-generated summaries/answers

**Guidelines for Variant Selection:**
- Choose 2-3 queries that best represent the customer's core search needs
- Make the progression meaningful (each step adds value)
- Keep the base query name consistent, only change the suffix
- All variants should address the SAME pain point
- Add `"variant_group": "base_query_name"` to link variants together

**Example Search Queries (NOT analytics):**
✅ GOOD: "Find all policies related to parental leave"
✅ GOOD: "Retrieve patient X's medical history"
✅ GOOD: "Search for support tickets similar to this issue"
❌ BAD: "Count how many tickets per category" (that's analytics)
❌ BAD: "Average response time by department" (that's analytics)

**MANDATORY - Include Advanced Queries:**
Of the 5-7 queries you design:

**REQUIRED (must have these query types):**
- At least 1 `_hybrid` query using FORK+FUSE (simple RRF) - complexity: "advanced"
- At least 1 "expert" query from: `_sophisticated` (LINEAR), `_rerank`, OR `_rag`/`_completion`

**ALSO INCLUDE (at least 1-2):**
- Fuzzy search with `{{"fuzziness": "AUTO"}}` - complexity: "advanced"
- Multi-field BM25 with boost parameters (NOT hybrid) - complexity: "medium"
- Phrase matching with MATCH_PHRASE - complexity: "medium"

**Complexity Labeling:**
- "simple": Basic BM25 or semantic search
- "medium": Fuzzy, phrase matching, multi-field BM25
- "advanced": True hybrid (FORK+FUSE RRF)
- "expert": Sophisticated (LINEAR), RERANK, or COMPLETION

**Important:** RERANK and COMPLETION are separate query types - don't force them together.

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
        """Extract JSON from LLM response with robust error handling"""
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

        # First attempt: Parse as-is
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parse failed: {e}")
            logger.debug(f"Attempting to fix common JSON issues...")

            # Second attempt: Fix common issues
            try:
                fixed_json = self._fix_json_issues(json_text)
                return json.loads(fixed_json)
            except json.JSONDecodeError as e2:
                logger.error(f"JSON fix attempt failed: {e2}")

                # Save the problematic JSON for debugging
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(json_text)
                    logger.error(f"Saved problematic JSON to: {f.name}")

                # Try to provide helpful error message
                error_msg = f"Invalid JSON in LLM response: {e}\n"
                error_msg += f"This usually means the LLM generated malformed JSON with unescaped quotes or newlines.\n"
                error_msg += f"Check the saved file at the path above for details."
                raise ValueError(error_msg)

    def _fix_json_issues(self, json_text: str) -> str:
        """Attempt to fix common JSON formatting issues from LLM responses

        Args:
            json_text: Raw JSON text that failed to parse

        Returns:
            Fixed JSON text
        """
        import re

        # Step 1: Check if JSON appears truncated and attempt to complete it
        json_text = self._complete_truncated_json(json_text)

        # Step 2: Replace actual newlines within string values with \n
        # This regex finds strings and replaces newlines within them
        def fix_newlines_in_strings(match):
            # The matched string content (without quotes)
            content = match.group(1)
            # Replace actual newlines with escaped newlines
            fixed_content = content.replace('\n', '\\n').replace('\r', '\\r')
            # Replace tabs with escaped tabs
            fixed_content = fixed_content.replace('\t', '\\t')
            # Return the fixed string with quotes
            return f'"{fixed_content}"'

        # Match string values (handling escaped quotes)
        # This pattern matches: "..." where ... can contain \" but not unescaped "
        json_text = re.sub(r'"((?:[^"\\]|\\.)*)(?<!\\)"', fix_newlines_in_strings, json_text)

        # Step 3: Fix unescaped quotes within string values more aggressively
        # Look for patterns where we have quotes inside a string value
        # This is a more aggressive approach for fixing nested quotes
        def fix_quotes_in_value(text):
            # Find string values that might have unescaped quotes
            # This looks for patterns like: "value": "text with "quote" inside"
            pattern = r'("(?:query|description|name|pain_point|esql)":\s*")(.*?)("(?:\s*,|\s*\}))'

            def escape_internal_quotes(match):
                prefix = match.group(1)
                content = match.group(2)
                suffix = match.group(3)
                # Escape any unescaped quotes in the content
                fixed_content = re.sub(r'(?<!\\)"', r'\"', content)
                return prefix + fixed_content + suffix

            return re.sub(pattern, escape_internal_quotes, text, flags=re.DOTALL)

        json_text = fix_quotes_in_value(json_text)

        # Step 4: Fix malformed required_fields structure
        # Pattern: "required_fields": { "field1": "value", "field2", "field3" }
        # Should be: "required_fields": { "dataset_name": ["field1", "field2", "field3"] }
        def fix_required_fields(text):
            # Find required_fields blocks that don't have a dataset wrapper
            # These have fields listed directly instead of inside a dataset key
            pattern = r'"required_datasets":\s*\[(.*?)\].*?"required_fields":\s*\{([^}]+)\}'

            def repair_fields(match):
                datasets_str = match.group(1)
                fields_str = match.group(2)

                # Extract first dataset name (remove quotes)
                dataset_match = re.search(r'"([^"]+)"', datasets_str)
                if not dataset_match:
                    return match.group(0)  # Can't fix without dataset name

                dataset_name = dataset_match.group(1)

                # Check if fields are already properly formatted with dataset wrapper
                if f'"{dataset_name}"' in fields_str and '[' in fields_str:
                    return match.group(0)  # Already correct

                # Extract field names from malformed structure
                # Pattern: "field1": "type", "field2", "field3"
                field_names = []
                for field_match in re.finditer(r'"([^"]+)"', fields_str):
                    field_name = field_match.group(1)
                    # Skip values like "keyword", "text", "_score" which are types/metadata
                    if field_name not in ['keyword', 'text', 'long', 'date', 'semantic_text', '_score', 'double', 'integer', 'boolean']:
                        field_names.append(field_name)

                if not field_names:
                    return match.group(0)  # No fields found

                # Rebuild with proper structure
                fields_array = ', '.join(f'"{f}"' for f in field_names)
                fixed = f'"required_datasets": [{datasets_str}], "required_fields": {{"{dataset_name}": [{fields_array}]}}'
                return fixed

            return re.sub(pattern, repair_fields, text, flags=re.DOTALL)

        json_text = fix_required_fields(json_text)

        # Step 5: Remove trailing commas before closing brackets/braces
        json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)

        # Step 6: Ensure consistent quote usage (replace single quotes around keys/values)
        # But be careful not to replace single quotes within string values
        json_text = re.sub(r"'([^']*)'(\s*:)", r'"\1"\2', json_text)  # Fix keys
        json_text = re.sub(r":\s*'([^']*)'", r': "\1"', json_text)    # Fix simple string values

        # Step 7: Remove any BOM or zero-width spaces
        json_text = json_text.replace('\ufeff', '').replace('\u200b', '')

        # Step 8: Handle common encoding issues
        json_text = json_text.encode('utf-8', errors='ignore').decode('utf-8')

        logger.debug("Applied JSON fixes: truncation, newlines, quotes, required_fields, trailing commas, encoding")
        return json_text

    def _complete_truncated_json(self, json_text: str) -> str:
        """Attempt to complete truncated JSON by closing open structures

        Args:
            json_text: Potentially truncated JSON text

        Returns:
            Completed JSON text
        """
        import re

        # Count open brackets and braces
        open_braces = json_text.count('{') - json_text.count('}')
        open_brackets = json_text.count('[') - json_text.count(']')

        # Check if we're in the middle of a string value
        # Look for the last quote and determine if we're inside a string
        in_string = False
        escape_next = False
        quote_count = 0

        for char in json_text:
            if escape_next:
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                continue
            if char == '"':
                quote_count += 1
                in_string = not in_string

        # If we're in a string, close it
        if in_string:
            json_text += '"'
            logger.debug("Closed incomplete string value")

        # Now check if we need to close the current object/array context
        # Look at the last few characters to understand the context
        trimmed = json_text.rstrip()

        # If the last character is a quote, we just closed a string
        # Check what comes before the string to see if we need a closing brace/bracket
        if trimmed.endswith('"'):
            # Look backwards to find the context
            # Find the last opening that would contain this string
            # Simple heuristic: if we just closed a string after "query": "...",
            # we likely need to close the object containing this query
            last_100_chars = trimmed[-100:] if len(trimmed) > 100 else trimmed

            # Check if this looks like the end of a query field
            if '"query"' in last_100_chars or '"esql"' in last_100_chars:
                # This is likely a truncated query field, need to close the parent object
                # But first check if there are more fields expected
                # Simple approach: assume query is the last field in queries array item
                pass  # Will be handled by structure closing below

        # Now close structures based on count
        closing = ''

        # We need to be smart about closing - check the context
        # If we just ended with a string value, we might need to close the containing object first
        if open_braces > 0 or open_brackets > 0:
            # Analyze the last part to understand nesting
            # Simple approach: close in LIFO order (close brackets before braces)

            # First close any arrays
            closing += ']' * open_brackets

            # Then close any objects
            closing += '}' * open_braces

        if closing:
            logger.debug(f"Completing truncated JSON with: {closing}")
            json_text += closing

        return json_text

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

            # variant_group is optional but should be a string if present
            if 'variant_group' in query and not isinstance(query['variant_group'], str):
                raise ValueError(f"Query variant_group must be a string")

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
