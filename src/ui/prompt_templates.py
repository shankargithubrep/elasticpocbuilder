"""
Prompt templates for AI expansion and context generation

Two templates exist for different demo types:
- OBSERVABILITY_EXPANSION_TEMPLATE: For APM, logs, metrics, infrastructure monitoring demos
- SEARCH_EXPANSION_TEMPLATE: For search relevancy, RAG, document retrieval demos
"""

import re
from typing import Literal

# Keywords for early demo type detection
SEARCH_KEYWORDS = [
    'search', 'find', 'retrieve', 'lookup', 'look up', 'discovery', 'discover',
    'knowledge base', 'documents', 'document', 'rag', 'retrieval', 'semantic',
    'provider directory', 'policy search', 'content', 'catalog', 'inventory lookup',
    'fuzzy', 'matching', 'relevance', 'relevancy', 'ranking', 'recommendations',
    'question answering', 'qa', 'chatbot', 'assistant', 'help desk', 'support search',
    'product search', 'site search', 'ecommerce search', 'e-commerce'
]

OBSERVABILITY_KEYWORDS = [
    'monitor', 'monitoring', 'apm', 'traces', 'tracing', 'logs', 'logging',
    'metrics', 'infrastructure', 'performance', 'latency', 'throughput',
    'cpu', 'memory', 'disk', 'network', 'kubernetes', 'k8s', 'containers',
    'observability', 'sre', 'devops', 'incident', 'alert', 'dashboard',
    'trend', 'analytics', 'aggregate', 'statistics', 'time-series', 'timeseries',
    'metricbeat', 'filebeat', 'heartbeat', 'opentelemetry', 'otel'
]


def detect_demo_type(text: str) -> Literal['search', 'observability']:
    """
    Detect demo type from user input BEFORE expansion.
    Returns 'search' or 'observability' based on keyword analysis.
    """
    text_lower = text.lower()

    search_score = sum(1 for kw in SEARCH_KEYWORDS if kw in text_lower)
    observability_score = sum(1 for kw in OBSERVABILITY_KEYWORDS if kw in text_lower)

    # Default to observability if no clear signal (maintains backward compatibility)
    if search_score > observability_score:
        return 'search'
    return 'observability'


# =============================================================================
# OBSERVABILITY EXPANSION TEMPLATE
# For: APM, logs, metrics, infrastructure monitoring, time-series analytics
# =============================================================================

OBSERVABILITY_EXPANSION_TEMPLATE = """You are an Elastic Solutions Architect creating a detailed technical use case document. You will receive sparse customer context including company name, department, pain points, and basic use cases. Your task is to transform this into a comprehensive, realistic document that aligns with actual enterprise data sources and Elastic Observability capabilities.

**Input Format**

You'll receive JSON or text containing:
- Customer name, department, industry
- Brief pain points (1-2 sentences each)
- High-level use cases (simple descriptions)
- Basic metrics mentioned (optional)

**Output Requirements**

**1. Customer Profile Section**

Expand the basic customer info to include:
- Full company name and department
- Industry vertical
- **Use Case Category**: Choose from Infrastructure, Security, Application Performance, Business Analytics, Cost Management, Customer Experience, DevOps/SRE
- **Primary Interest**: The main Elastic solution area (APM, Infrastructure Monitoring, Logs, Security, etc.)

**2. Pain Points Section (3-6 detailed pain points)**

Transform each basic pain point into a detailed, technical description that:
- Explains the business impact (cost, risk, efficiency, customer experience)
- Describes the technical root cause (tooling gaps, data silos, visibility issues, scale challenges)
- Includes realistic specifics: mention actual tools/systems enterprises use (Kafka, Splunk, Prometheus, cloud providers, databases, etc.)
- Uses 2-4 sentences per pain point
- Groups related pain points under subheadings if >4 total (e.g., "Infrastructure Challenges", "Data Platform Issues")

Example transformation:
- **Input**: "No unified framework for data collection"
- **Output**: "No standardized performance benchmarking framework: Each team runs ad-hoc performance tests with different tools, metrics, and methodologies, making it impossible to compare results across applications or hardware platforms objectively. Critical decisions about infrastructure investments lack data-driven justification."

**3. Key Metrics & Data Sources Section**

This is the most critical section. For each category of metrics:

Structure each category as:
```
### [Category Name] (via [Data Collection Method])
* **[Specific Metric Name]**:
  - Field names: `field.name.notation` following Elastic Common Schema or OpenTelemetry conventions
  - Description of what's measured
  - Source system (if data exists elsewhere like Kafka, databases, APIs)
  - Optional: breakdown dimensions (by host, service, region, etc.)
```

**Data Collection Methods to Reference:**
- Metricbeat modules (System, Kafka, Redis, MySQL, Kubernetes, etc.)
- APM Agents (Java, Node.js, Python, .NET, Go, RUM)
- Filebeat modules (Nginx, Apache, System logs, application logs)
- Custom Beats or API integrations
- OpenTelemetry SDKs and collectors
- Elastic integrations (AWS, Azure, GCP, Kubernetes)
- Data pipelines (Kafka → Logstash → Elasticsearch)

**Field Naming Guidelines:**
- Use ECS (Elastic Common Schema) field conventions: `host.name`, `service.name`, `event.outcome`
- For APM: `transaction.duration.us`, `span.type`, `trace.id`
- For infrastructure: `system.cpu.total.pct`, `system.memory.used.bytes`
- For custom metrics: `labels.custom_field` or logical namespace patterns
- Always use actual field names, never placeholder brackets like `[field_name]`

Identify 4-8 metric categories relevant to the use case:
- Application Performance Metrics (APM)
- Infrastructure/System Metrics (CPU, memory, disk, network)
- Business/Custom Metrics (transactions, conversions, user actions)
- Cost/Financial Metrics (if relevant)
- Data Platform Metrics (Kafka, databases, queues)
- Error & Availability Metrics
- Security Metrics (if relevant)
- User Experience Metrics (RUM, if relevant)

**4. Use Cases Section (4-6 detailed use cases)**

Expand each basic use case into a comprehensive description with:

```
### [Number]. [Descriptive Use Case Title]

**Objective**: One sentence clearly stating the business or technical goal.

**Key Metrics**:
- List 3-6 specific metrics tracked for this use case
- Reference field names from section 3
- Include thresholds or targets where appropriate

**Output/Benefits**:
- What insights or actions result
- Specific example: "Output: 'AMD processors handle 35% more requests at same latency SLA'"
- Business value delivered
```

**Use Case Guidelines:**
- Each use case should be realistic and achievable through ES|QL queries and data analysis
- Focus on what insights can be derived from the data (not how to build dashboards or ML jobs)
- Progress from foundational (monitoring, visibility) to advanced (optimization, prediction) use cases
- Include at least one use case about data consolidation if pain points mention disparate systems
- Include at least one use case about cost analysis if financial concerns are mentioned
- End with an executive reporting or business validation use case if appropriate

**5. Optional Sections (include if relevant to use case)**

**Data Model & Index Strategy:**
- Recommended index patterns
- Critical field mappings (10-15 key fields with descriptions)
- Data retention considerations

**Tone & Style Guidelines**

- **Be specific and technical**: Use real product names, actual field names, concrete numbers
- **Be realistic**: Only reference data sources that enterprises actually have or can realistically collect
- **Avoid vagueness**: Replace "various metrics" with specific named metrics
- **Use industry terminology**: Match the customer's industry (financial services, healthcare, retail, etc.)
- **No query language examples**: Do not include ESQL, KQL, or any query syntax
- **No placeholder text**: Replace all [placeholders] with realistic examples

**Validation Checklist**

Before finalizing, ensure:
- ✓ Every metric has realistic field names in dot.notation
- ✓ Data collection methods are specified (Metricbeat, APM, Filebeat, etc.)
- ✓ Pain points include technical root causes, not just symptoms
- ✓ Use cases have clear objectives and expected outputs/benefits
- ✓ No ESQL, KQL, or query syntax appears anywhere
- ✓ No mentions of dashboards, ML jobs, alerting rules, or other unimplemented features
- ✓ Industry-specific terminology is used appropriately
- ✓ All systems/tools mentioned are real products enterprises use

---

**Now, please expand the following customer context:**

{user_prompt}
"""


# =============================================================================
# SEARCH EXPANSION TEMPLATE
# For: Search relevancy, RAG, document retrieval, knowledge bases, semantic search
# =============================================================================

SEARCH_EXPANSION_TEMPLATE = """You are an Elastic Solutions Architect creating a detailed technical use case document for a **Search & Retrieval** solution. You will receive sparse customer context and transform it into a comprehensive document focused on **search relevancy, document retrieval, and knowledge discovery**.

**IMPORTANT**: This is a SEARCH demo, not an observability demo. Focus ONLY on:
- Document collections and their structure
- Search patterns (exact, fuzzy, semantic, hybrid)
- Relevancy requirements and ranking needs
- Field types for search (text, keyword, semantic_text, geo_point)

Do NOT include APM, Metricbeat, infrastructure monitoring, or time-series metrics.

**Input Format**

You'll receive JSON or text containing:
- Customer name, department, industry
- Brief pain points about search/retrieval challenges
- High-level use cases involving finding/retrieving information
- Types of documents or content to search (optional)

**Output Requirements**

**1. Customer Profile Section**

Expand the basic customer info to include:
- Full company name and department
- Industry vertical
- **Use Case Category**: Choose from Knowledge Management, Customer Support, E-commerce Search, Content Discovery, Document Retrieval, RAG/AI Assistant, Compliance Search
- **Primary Interest**: Elasticsearch Search (Full-text, Semantic, Hybrid, Vector)

**2. Pain Points Section (3-5 detailed pain points)**

Transform each pain point into a search-focused technical description that:
- Explains the search/retrieval challenge (missed results, irrelevant results, slow lookups)
- Describes why current search fails (exact match only, no synonym handling, no fuzzy matching, no semantic understanding)
- Quantifies impact (time wasted, escalations, customer complaints, compliance risk)
- Uses 2-3 sentences per pain point

🚨 **CRITICAL**: Extract and use ACTUAL terminology from the user's input. Do NOT invent new domain terms or use generic examples from this template.

**3. Document Collections Section**

This is the most critical section. Define the document collections that will be searched:

Structure each collection as:
```
### [Collection Name]
* **Purpose**: What information this collection contains and who searches it
* **Document Type**: The kind of content (policies, profiles, products, articles, etc.)
* **Key Search Fields**:
  - `field_name` (field_type): Description and search behavior
  - Use types: `text` (full-text), `keyword` (exact), `semantic_text` (vector), `geo_point` (location)
* **Search Patterns**: How users typically search this collection
  - Exact lookup (by ID, code, or exact term)
  - Fuzzy search (handling typos and variations)
  - Semantic search (meaning-based, natural language)
  - Geographic search (location-based with radius)
* **Volume**: Approximate document count (hundreds, thousands, millions)
* **Value Diversity Requirements**: For each `keyword` field, describe the variety needed (see guidance below)
```

**Field Type Guidelines:**
- `text`: For full-text BM25 search (short fields: names, titles, headlines)
- `keyword`: For exact matching and filtering (IDs, codes, categories, status)
- `semantic_text`: For vector embeddings AND text storage — enables BOTH meaning-based search AND full-text search on the same field
- `geo_point`: For location-based searches (provider locations, store locations)
- `date`: For temporal filtering (effective dates, last updated)
- `boolean`: For binary filters (active/inactive, available/unavailable)
- `float`/`integer`: For numeric filtering and sorting (ratings, scores, prices)

**🚨 CRITICAL: semantic_text Field Rules**
- `semantic_text` fields store the original text AND auto-generate vector embeddings — you get BOTH BM25 and semantic search from ONE field
- Each dataset should have exactly TWO searchable text fields:
  1. A SHORT `text` field for BM25 keyword search (title, name, headline)
  2. A LONGER `semantic_text` field for semantic search (description, bio, content)
- **WRONG**: Creating BOTH `description` (text) AND `description_semantic` (semantic_text) ← ANTIPATTERN!
- **WRONG**: Creating BOTH `visual_caption` (text) AND `visual_caption_semantic` (semantic_text) ← ANTIPATTERN!
- **CORRECT**: Use the natural field name directly as semantic_text: `description` (semantic_text), `bio` (semantic_text)
- Do NOT prefix or suffix field names with "semantic_" — just use the natural field name with type `semantic_text`

**🚨 CRITICAL: Field Value Diversity Guidance**

For each `keyword` field in your document collections, provide guidance on the VARIETY of values needed.

**DO NOT provide specific hardcoded example values**. Instead, describe the VALUE SPACE:

**Format**:
```
* **Value Diversity Requirements**:
  - `field_name`: Need [number] distinct values representing [description of variety]
    Actual values should be: [instructions for deriving realistic values from user's domain]
```

**Instructions**:

1. **Extract from user input FIRST**: If user mentions specific entities, reference those explicitly
2. **Describe VALUE SPACE, not specific values**:
   - ✅ GOOD: "Need 8-10 distinct categories relevant to the user's mentioned domain"
   - ❌ BAD: Listing specific values (these contaminate all demos)
3. **Reference user context**: "Include user's mentioned [X] plus 4-6 related options"
4. **Specify diversity needs**: How many values, what dimension they cover, any constraints

**Example of GOOD guidance** (this shows format only - adapt to user's actual domain):
```
- `category_field`: Need 8-10 values representing the breadth of the user's product/service domain. Include the user's explicitly mentioned categories plus logically related options for variety.
```

**🚨 CRITICAL: Common Filter Combinations**

Describe 2-3 **realistic search scenarios** where users combine multiple filters. Extract these from the user's pain points and use cases - do NOT invent generic scenarios.

**Format**:
```
**Common Search Scenarios**:
1. "[Describe realistic user search behavior derived from their input]"
   - Combines: [list 3-4 field names that logically filter together in this domain]
   - Why realistic: [explain based on user's described workflows or pain points]
   - Guidance for data: Ensure adequate combinations of these fields are populated together
```

**4. Use Cases Section (4-6 search-focused use cases)**

Each use case should demonstrate a specific search capability:

```
### [Number]. [Descriptive Use Case Title]

**Search Challenge**: The specific retrieval problem being solved

**Search Strategy**: The Elasticsearch capability being demonstrated
- Choose from: Fuzzy matching, Semantic search, Hybrid search, Geographic search, Faceted search, Autocomplete, RAG/Question Answering

**Document Collection**: Which collection(s) are searched

**Example Query Pattern**: A query description using DOMAIN TERMS FROM USER INPUT

🚨 **CRITICAL - USE USER'S TERMINOLOGY**:
- Extract entities and terms from the user's actual input
- Format: "[Action verb] [entity from user's domain] [with criteria from user's context]"
- DO NOT use generic placeholders or examples from this template
- VARY terms across different use cases (don't repeat the same entity in every example)

**Success Criteria**: What makes search results "good"
- Top result should be...
- Results should include...
- Search should complete in...

**Business Value**: Quantified improvement over current state
```

**Use Case Guidelines:**
- Demonstrate PROGRESSION of search sophistication:
  1. Basic keyword/BM25 search
  2. Fuzzy matching for typos and variations
  3. Semantic search for meaning understanding
  4. Hybrid search combining keyword + semantic
  5. Advanced: RERANK for precision, COMPLETION for RAG
- Each use case should map to a real user workflow FROM THEIR INPUT
- Include at least one fuzzy/typo-tolerant search use case
- Include at least one semantic/natural language use case
- Include at least one multi-criteria filtering use case (combining 3+ filters)
- VARY the entities/terms across use cases (don't repeat the same terms)

**5. Search Relevancy Requirements**

Describe what "good" search results mean for this customer:
- **Precision requirements**: How important is it that top results are highly relevant?
- **Recall requirements**: How important is finding ALL relevant documents?
- **Ranking factors**: What should influence result ordering? (recency, popularity, location, etc.)
- **Personalization needs**: Should results vary by user role, location, or history?

**Tone & Style Guidelines**

- **Focus on SEARCH**: Every section should relate to finding/retrieving documents
- **Extract from USER INPUT**: Use terminology, entities, and context from the user's prompt
- **Be DESCRIPTIVE, not PRESCRIPTIVE**: Describe what kind of values to create, don't specify exact values
- **Use search terminology**: relevancy, ranking, recall, precision, fuzzy, semantic
- **No observability content**: Do NOT mention APM, Metricbeat, traces, infrastructure
- **No query syntax**: Do not include ES|QL, KQL, or DSL examples
- **Industry-specific but user-derived**: Match the user's industry with terms from their input

**Validation Checklist**

Before finalizing, ensure:
- ✓ All content is search/retrieval focused (no APM, metrics, monitoring)
- ✓ Document collections have realistic field types
- ✓ 🆕 Value diversity guidance describes TYPES of values, not specific hardcoded examples
- ✓ 🆕 Common filter combinations are derived from user's pain points/use cases
- ✓ Use cases demonstrate different search strategies
- ✓ 🆕 Example query patterns use terminology from USER'S INPUT (not template examples)
- ✓ Pain points describe search/retrieval failures
- ✓ No ES|QL, KQL, or query syntax appears anywhere
- ✓ Field names use appropriate types (text, keyword, semantic_text, geo_point)
- ✓ 🆕 No redundant field pairs — NEVER both `field` (text) and `field_semantic` (semantic_text) for the same concept
- ✓ 🆕 Each dataset has exactly ONE `text` field (short) and ONE `semantic_text` field (long) — not two versions of the same field
- ✓ 🆕 Variety across use case examples (don't repeat same entity in every use case)
- ✓ 🆕 No hardcoded domain values that could leak into every demo

---

**Now, please expand the following customer context into a search-focused use case document:**

{user_prompt}
"""


# Backward compatibility alias
GUIDED_HELP_TEMPLATE = OBSERVABILITY_EXPANSION_TEMPLATE
