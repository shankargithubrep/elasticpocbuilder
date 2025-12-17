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

Example transformations:
- **Input**: "Hard to find provider information"
- **Output**: "Provider directory search requires exact name matches, forcing agents to ask members to spell names letter-by-letter. Nicknames ('Dr. Bob' vs 'Robert'), maiden names, and phonetically similar spellings (Smith/Smyth/Smythe) cause 23% of searches to fail, resulting in escalations and extended call times."

- **Input**: "Policy documents are hard to search"
- **Output**: "Benefits policies exist as unstructured PDF and Word documents with no semantic search capability. Agents cannot ask natural language questions like 'Is gastric bypass covered for BMI over 40?' and must manually navigate table-of-contents structures, spending 3-5 minutes per policy lookup."

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
```

**Field Type Guidelines:**
- `text`: For full-text search with analyzers (names, descriptions, content)
- `keyword`: For exact matching and filtering (IDs, codes, categories, status)
- `semantic_text`: For vector embeddings enabling meaning-based search
- `geo_point`: For location-based searches (provider locations, store locations)
- `date`: For temporal filtering (effective dates, last updated)
- `boolean`: For binary filters (active, accepting_new_patients)
- `float`/`integer`: For numeric filtering and sorting (ratings, scores)

**4. Use Cases Section (4-6 search-focused use cases)**

Each use case should demonstrate a specific search capability:

```
### [Number]. [Descriptive Use Case Title]

**Search Challenge**: The specific retrieval problem being solved

**Search Strategy**: The Elasticsearch capability being demonstrated
- Choose from: Fuzzy matching, Semantic search, Hybrid search, Geographic search, Faceted search, Autocomplete, RAG/Question Answering

**Document Collection**: Which collection(s) are searched

**Example Query Pattern**: A natural language description of what users search for
- Example: "Find cardiologists near 90210 accepting new PPO patients"
- Example: "Is bariatric surgery covered for BMI over 40?"

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
- Each use case should map to a real user workflow
- Include at least one fuzzy/typo-tolerant search use case
- Include at least one semantic/natural language use case
- Include at least one use case combining multiple search strategies

**5. Search Relevancy Requirements**

Describe what "good" search results mean for this customer:
- **Precision requirements**: How important is it that top results are highly relevant?
- **Recall requirements**: How important is finding ALL relevant documents?
- **Ranking factors**: What should influence result ordering? (recency, popularity, location, etc.)
- **Personalization needs**: Should results vary by user role, location, or history?

**Tone & Style Guidelines**

- **Focus on SEARCH**: Every section should relate to finding/retrieving documents
- **Be specific about content**: Describe actual document types and fields
- **Use search terminology**: relevancy, ranking, recall, precision, fuzzy, semantic
- **No observability content**: Do NOT mention APM, Metricbeat, traces, infrastructure
- **No query syntax**: Do not include ES|QL, KQL, or DSL examples
- **Industry-specific examples**: Use realistic document types for the industry

**Validation Checklist**

Before finalizing, ensure:
- ✓ All content is search/retrieval focused (no APM, metrics, monitoring)
- ✓ Document collections have realistic field types
- ✓ Use cases demonstrate different search strategies
- ✓ Pain points describe search/retrieval failures
- ✓ No ES|QL, KQL, or query syntax appears anywhere
- ✓ Field names use appropriate types (text, keyword, semantic_text, geo_point)
- ✓ Industry-specific document types are realistic

---

**Now, please expand the following customer context into a search-focused use case document:**

{user_prompt}
"""


# Backward compatibility alias
GUIDED_HELP_TEMPLATE = OBSERVABILITY_EXPANSION_TEMPLATE
