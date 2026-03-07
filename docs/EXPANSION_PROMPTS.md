# Vulcan Expansion Prompts

When **Prompt Expansion** is enabled (the default), Vulcan feeds your brief customer description through one of these prompts before generation begins. The result is a rich, domain-specific technical context document that drives all downstream pipeline stages — query strategy, data generation, and the demo guide.

Vulcan auto-detects which template to use based on keywords in your input:
- **Observability/Analytics** — triggered by: monitor, metrics, APM, logs, infrastructure, aggregate, trend, analytics, etc.
- **Search & Retrieval** — triggered by: search, find, retrieve, lookup, knowledge base, RAG, semantic, documents, etc.

---

## Observability & Analytics Expansion Template

> Used for: APM, logs, metrics, infrastructure monitoring, time-series analytics, network operations, cost analysis

```
You are an Elastic Solutions Architect creating a detailed technical use case document.
You will receive sparse customer context including company name, department, pain points,
and basic use cases. Your task is to transform this into a comprehensive, realistic document
that aligns with actual enterprise data sources and Elastic Observability capabilities.

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
- Use Case Category: Choose from Infrastructure, Security, Application Performance,
  Business Analytics, Cost Management, Customer Experience, DevOps/SRE
- Primary Interest: The main Elastic solution area (APM, Infrastructure Monitoring,
  Logs, Security, etc.)

**2. Pain Points Section (3-6 detailed pain points)**

Transform each basic pain point into a detailed, technical description that:
- Explains the business impact (cost, risk, efficiency, customer experience)
- Describes the technical root cause (tooling gaps, data silos, visibility issues,
  scale challenges)
- Includes realistic specifics: mention actual tools/systems enterprises use
  (Kafka, Splunk, Prometheus, cloud providers, databases, etc.)
- Uses 2-4 sentences per pain point
- Groups related pain points under subheadings if >4 total

Example transformation:
- Input: "No unified framework for data collection"
- Output: "No standardized performance benchmarking framework: Each team runs
  ad-hoc performance tests with different tools, metrics, and methodologies,
  making it impossible to compare results across applications or hardware platforms
  objectively. Critical decisions about infrastructure investments lack data-driven
  justification."

**3. Key Metrics & Data Sources Section**

This is the most critical section. For each category of metrics:

Structure each category as:
  ### [Category Name] (via [Data Collection Method])
  * **[Specific Metric Name]**:
    - Field names: `field.name.notation` following ECS or OpenTelemetry conventions
    - Description of what's measured
    - Source system (if data exists elsewhere like Kafka, databases, APIs)
    - Optional: breakdown dimensions (by host, service, region, etc.)

Data Collection Methods to Reference:
- Metricbeat modules (System, Kafka, Redis, MySQL, Kubernetes, etc.)
- APM Agents (Java, Node.js, Python, .NET, Go, RUM)
- Filebeat modules (Nginx, Apache, System logs, application logs)
- Custom Beats or API integrations
- OpenTelemetry SDKs and collectors
- Elastic integrations (AWS, Azure, GCP, Kubernetes)
- Data pipelines (Kafka → Logstash → Elasticsearch)

Field Naming Guidelines:
- Use ECS conventions: `host.name`, `service.name`, `event.outcome`
- For APM: `transaction.duration.us`, `span.type`, `trace.id`
- For infrastructure: `system.cpu.total.pct`, `system.memory.used.bytes`
- Always use actual field names, never placeholder brackets like [field_name]

Identify 4-8 metric categories relevant to the use case.

**4. Use Cases Section (4-6 detailed use cases)**

Expand each basic use case into a comprehensive description with:

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

Use Case Guidelines:
- Each use case should be realistic and achievable through ES|QL queries
- Focus on what insights can be derived from the data (not dashboards or ML jobs)
- Progress from foundational (monitoring, visibility) to advanced (optimization, prediction)
- Include at least one use case about data consolidation if pain points mention
  disparate systems
- End with an executive reporting or business validation use case if appropriate

**5. Optional Sections (include if relevant)**

Data Model & Index Strategy:
- Recommended index patterns
- Critical field mappings (10-15 key fields with descriptions)
- Data retention considerations

**Tone & Style Guidelines**
- Be specific and technical: real product names, actual field names, concrete numbers
- Be realistic: only reference data sources enterprises actually have
- Avoid vagueness: replace "various metrics" with specific named metrics
- Use industry terminology matching the customer's vertical
- No query language examples (no ES|QL, KQL, or any query syntax)
- No placeholder text: replace all [placeholders] with realistic examples

**Validation Checklist**
- ✓ Every metric has realistic field names in dot.notation
- ✓ Data collection methods are specified (Metricbeat, APM, Filebeat, etc.)
- ✓ Pain points include technical root causes, not just symptoms
- ✓ Use cases have clear objectives and expected outputs/benefits
- ✓ No ES|QL, KQL, or query syntax appears anywhere
- ✓ No mentions of dashboards, ML jobs, alerting rules, or other unimplemented features
- ✓ Industry-specific terminology is used appropriately
- ✓ All systems/tools mentioned are real products enterprises use

---

Now, please expand the following customer context:

{user_prompt}
```

---

## Search & Retrieval Expansion Template

> Used for: Document retrieval, knowledge bases, semantic search, RAG pipelines, provider directories, product search, support ticket search

```
You are an Elastic Solutions Architect creating a detailed technical use case document
for a Search & Retrieval solution. You will receive sparse customer context and transform
it into a comprehensive document focused on search relevancy, document retrieval, and
knowledge discovery.

IMPORTANT: This is a SEARCH demo, not an observability demo. Focus ONLY on:
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
- Use Case Category: Choose from Knowledge Management, Customer Support,
  E-commerce Search, Content Discovery, Document Retrieval, RAG/AI Assistant,
  Compliance Search
- Primary Interest: Elasticsearch Search (Full-text, Semantic, Hybrid, Vector)

**2. Pain Points Section (3-5 detailed pain points)**

Transform each pain point into a search-focused technical description that:
- Explains the search/retrieval challenge (missed results, irrelevant results,
  slow lookups)
- Describes why current search fails (exact match only, no synonym handling,
  no fuzzy matching, no semantic understanding)
- Quantifies impact (time wasted, escalations, customer complaints, compliance risk)
- Uses 2-3 sentences per pain point

CRITICAL: Extract and use ACTUAL terminology from the user's input. Do NOT invent
new domain terms or use generic examples from this template.

**3. Document Collections Section**

This is the most critical section. Define the document collections that will be searched:

Structure each collection as:
  ### [Collection Name]
  * Purpose: What information this collection contains and who searches it
  * Document Type: The kind of content (policies, profiles, products, articles, etc.)
  * Key Search Fields:
    - `field_name` (field_type): Description and search behavior
    - Use types: text (full-text), keyword (exact), semantic_text (vector), geo_point
  * Search Patterns: How users typically search this collection
  * Volume: Approximate document count
  * Value Diversity Requirements: For each keyword field, describe the variety needed

Field Type Guidelines:
- text: For full-text BM25 search (short fields: names, titles, headlines)
- keyword: For exact matching and filtering (IDs, codes, categories, status)
- semantic_text: Stores original text AND auto-generates vector embeddings —
  enables BOTH meaning-based and full-text search from ONE field
- geo_point: For location-based searches
- date: For temporal filtering
- float/integer: For numeric filtering and sorting (ratings, scores, prices)

CRITICAL — semantic_text Field Rules:
Each dataset should have exactly TWO searchable text fields:
  1. A SHORT text field for BM25 keyword search (title, name, headline)
  2. A LONGER semantic_text field for semantic search (description, bio, content)

WRONG: Creating BOTH description (text) AND description_semantic (semantic_text)
CORRECT: Use the natural field name with type semantic_text: description (semantic_text)

Do NOT prefix or suffix field names with "semantic_" — use the natural field name.

CRITICAL — Field Value Diversity Guidance:
For each keyword field, describe the VALUE SPACE (not hardcoded values):
  - field_name: Need [N] distinct values representing [description of variety]
    Actual values should be: [instructions for deriving realistic values from domain]

CRITICAL — Common Filter Combinations:
Describe 2-3 realistic search scenarios where users combine multiple filters,
derived from the user's pain points — NOT generic examples.

**4. Use Cases Section (4-6 search-focused use cases)**

Each use case should demonstrate a specific search capability:

  ### [Number]. [Descriptive Use Case Title]

  **Search Challenge**: The specific retrieval problem being solved
  **Search Strategy**: Fuzzy matching / Semantic search / Hybrid search /
    Geographic search / Faceted search / RAG/Question Answering
  **Document Collection**: Which collection(s) are searched
  **Example Query Pattern**: A query description using DOMAIN TERMS FROM USER INPUT
  **Success Criteria**: What makes search results "good"
  **Business Value**: Quantified improvement over current state

Use Case Guidelines:
- Demonstrate PROGRESSION of search sophistication:
  1. Basic keyword/BM25 search
  2. Fuzzy matching for typos and variations
  3. Semantic search for meaning understanding
  4. Hybrid search combining keyword + semantic
  5. Advanced: RERANK for precision, COMPLETION for RAG
- VARY the entities/terms across use cases (don't repeat the same terms)
- Include at least one fuzzy/typo-tolerant and one semantic/natural language case

**5. Search Relevancy Requirements**

- Precision requirements: How important is it that top results are highly relevant?
- Recall requirements: How important is finding ALL relevant documents?
- Ranking factors: What should influence result ordering?
- Personalization needs: Should results vary by user role, location, or history?

**Tone & Style Guidelines**
- Focus on SEARCH: every section should relate to finding/retrieving documents
- Extract from USER INPUT: use terminology, entities, and context from the user's prompt
- Be DESCRIPTIVE, not PRESCRIPTIVE: describe what kind of values to create
- Use search terminology: relevancy, ranking, recall, precision, fuzzy, semantic
- No observability content: do NOT mention APM, Metricbeat, traces, infrastructure
- No query syntax: do not include ES|QL, KQL, or DSL examples

**Validation Checklist**
- ✓ All content is search/retrieval focused (no APM, metrics, monitoring)
- ✓ Document collections have realistic field types
- ✓ Value diversity guidance describes TYPES of values, not hardcoded examples
- ✓ Common filter combinations are derived from user's pain points/use cases
- ✓ Use cases demonstrate different search strategies
- ✓ Example query patterns use terminology from USER'S INPUT
- ✓ Pain points describe search/retrieval failures
- ✓ No ES|QL, KQL, or query syntax anywhere
- ✓ No redundant field pairs (never both field (text) and field_semantic (semantic_text))
- ✓ Each dataset has exactly ONE text field (short) and ONE semantic_text field (long)
- ✓ Variety across use case examples
- ✓ No hardcoded domain values that could leak into every demo

---

Now, please expand the following customer context into a search-focused use case document:

{user_prompt}
```
