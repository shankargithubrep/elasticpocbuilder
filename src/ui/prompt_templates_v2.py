"""
ENHANCED Search Expansion Template (v2)
Addresses query refinement challenges by emphasizing realistic values and combinations
"""

SEARCH_EXPANSION_TEMPLATE_V2 = """You are an Elastic Solutions Architect creating a detailed technical use case document for a **Search & Retrieval** solution. You will receive sparse customer context and transform it into a comprehensive document focused on **search relevancy, document retrieval, and knowledge discovery**.

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
- **Output**: "Benefits policies exist as unstructured PDF and Word documents with no semantic search capability. Agents cannot ask natural language questions like 'Is bariatric surgery covered for BMI over 40?' and must manually navigate table-of-contents structures, spending 3-5 minutes per policy lookup."

🚨 **CRITICAL**: Use ACTUAL terminology from the customer's domain, NEVER generic placeholders like [item], [condition], [resource].

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
  - **Multi-criteria filtering**: Describe common combinations users need (see below)
* **Volume**: Approximate document count (hundreds, thousands, millions)
* **Value Examples**: 🆕 List 3-5 REAL example values for each categorical field (see guidelines below)
```

**Field Type Guidelines:**
- `text`: For full-text search with analyzers (names, descriptions, content)
- `keyword`: For exact matching and filtering (IDs, codes, categories, status)
- `semantic_text`: For vector embeddings enabling meaning-based search
- `geo_point`: For location-based searches (provider locations, store locations)
- `date`: For temporal filtering (effective dates, last updated)
- `boolean`: For binary filters (active, accepting_new_patients)
- `float`/`integer`: For numeric filtering and sorting (ratings, scores)

**🆕 CRITICAL: Realistic Field Values**

For each `keyword` field in your document collections, provide 3-5 REALISTIC example values:

**DO** ✅:
- `specialty_description`: "Cardiology", "Orthopedic Surgery", "Pediatrics", "Family Medicine", "Dermatology"
- `network_plans`: "UnitedHealthcare Choice Plus", "Aetna PPO", "Blue Cross Blue Shield", "Cigna Open Access"
- `state`: "CA", "NY", "TX", "FL", "IL"
- `product_category`: "Fishing Rods", "Hiking Boots", "Camping Tents", "Kayaks", "Backpacks"

**DON'T** ❌:
- `specialty`: "Specialty A", "Specialty B", "Specialty C"
- `network`: "Network 1", "Network 2"
- `category`: "[category name]", "Example Category"

**Why This Matters**: These example values will inform the demo generation system about realistic data to create. Generic placeholders result in search queries that return 0 results.

**🆕 Common Filter Combinations**

For each document collection, describe 2-3 **realistic search scenarios** where users combine multiple filters:

Example format:
```
**Common Search Scenarios**:
1. "Find cardiologists in California accepting new patients on UnitedHealthcare Choice Plus"
   - Combines: specialty_description, state, accepting_new_patients, network_plans
   - Why realistic: Callers often have specific insurance and location requirements

2. "Locate orthopedic surgeons near ZIP 90210 with ratings above 4.0"
   - Combines: specialty_description, geo_location (near 90210), patient_rating
   - Why realistic: Members want quality providers nearby

3. "Search for family medicine doctors in New York who speak Spanish"
   - Combines: specialty_description, state, languages_spoken
   - Why realistic: Language access is critical for diverse patient populations
```

**Why This Matters**: Multi-criteria queries are common in search applications. Describing realistic combinations ensures the generated data will contain co-occurring values that actually exist together in documents (e.g., "Cardiology" + "CA" + "accepting_new_patients=true" + "UnitedHealthcare Choice Plus" appearing in the same provider record).

**4. Use Cases Section (4-6 search-focused use cases)**

Each use case should demonstrate a specific search capability:

```
### [Number]. [Descriptive Use Case Title]

**Search Challenge**: The specific retrieval problem being solved

**Search Strategy**: The Elasticsearch capability being demonstrated
- Choose from: Fuzzy matching, Semantic search, Hybrid search, Geographic search, Faceted search, Autocomplete, RAG/Question Answering

**Document Collection**: Which collection(s) are searched

**Example Query Pattern**: A CONCRETE, REALISTIC example query (NO PLACEHOLDERS)

🚨 **USE ACTUAL EXAMPLES FROM YOUR DOMAIN**:
✅ GOOD: "Find cardiologists near ZIP code 90210 accepting new patients on UnitedHealthcare Choice Plus"
✅ GOOD: "Is bariatric surgery covered for patients with BMI over 40 and diabetes?"
✅ GOOD: "Search knowledge base for 'how to reset password after account lockout'"

❌ BAD: "Find [resource type] near [location] with [attributes]"
❌ BAD: "Is [specific item] covered/available for [conditions]?"
❌ BAD: "Search for [entity] with [criteria]"

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
- Include at least one **multi-criteria filtering** use case (combining 3+ filters)
- 🆕 Use CONCRETE examples with actual values from your domain (no placeholders!)

**5. Search Relevancy Requirements**

Describe what "good" search results mean for this customer:
- **Precision requirements**: How important is it that top results are highly relevant?
- **Recall requirements**: How important is finding ALL relevant documents?
- **Ranking factors**: What should influence result ordering? (recency, popularity, location, distance, ratings, etc.)
- **Personalization needs**: Should results vary by user role, location, or history?

**Tone & Style Guidelines**

- **Focus on SEARCH**: Every section should relate to finding/retrieving documents
- **Be CONCRETE and SPECIFIC**: Use realistic values from the domain, never placeholders
- **Use search terminology**: relevancy, ranking, recall, precision, fuzzy, semantic
- **No observability content**: Do NOT mention APM, Metricbeat, traces, infrastructure
- **No query syntax**: Do not include ES|QL, KQL, or DSL examples
- **Industry-specific examples**: Use realistic document types for the industry
- **Real-world values**: Provider names, product names, categories, locations should be realistic for the industry

**Validation Checklist**

Before finalizing, ensure:
- ✓ All content is search/retrieval focused (no APM, metrics, monitoring)
- ✓ Document collections have realistic field types
- ✓ 🆕 Each keyword field has 3-5 REALISTIC example values listed
- ✓ 🆕 Common filter combinations are described with concrete examples
- ✓ Use cases demonstrate different search strategies
- ✓ 🆕 Example query patterns use ACTUAL domain terms (no [placeholders])
- ✓ Pain points describe search/retrieval failures
- ✓ No ES|QL, KQL, or query syntax appears anywhere
- ✓ Field names use appropriate types (text, keyword, semantic_text, geo_point)
- ✓ Industry-specific document types are realistic
- ✓ 🆕 At least one multi-criteria filtering use case (3+ combined filters)

---

**Now, please expand the following customer context into a search-focused use case document:**

{user_prompt}
"""
