# **Elastic Agent Builder Demo for Adobe Inc.**

## **Internal Demo Script & Reference Guide**

---

## **📋 Demo Overview**

**Total Time:** 25-30 minutes
**Audience:** Brand Concierge AI/ML & Product Engineering technical/business stakeholders
**Goal:** Show how Agent Builder enables AI-powered search on Adobe brand asset and retrieval optimization data

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## **🗂️ Dataset Architecture**

### **brand_assets** (Primary Dataset)
- **Record Count:** 45,000,000 documents
- **Type:** Documents index
- **Primary Key:** `asset_id` (keyword)
- **Key Fields:**
  - `asset_id`: Unique identifier for each brand asset
  - `asset_name`: Name/title of the asset
  - `asset_type`: Type (logo, image, video, template, etc.)
  - `brand_name`: Associated brand name
  - `tags`: Array of descriptive tags
  - `created_date`: Asset creation timestamp
  - `file_size_mb`: Size in megabytes
  - `usage_count`: Number of times asset has been used
  - `quality_score`: Computed quality rating (0-100)
  - `customer_id`: Reference to customer account
  - `embedding_vector`: Dense vector for semantic search
- **Relationships:** Links to `customer_accounts` via `customer_id`

### **ai_assistant_conversations** (Conversational Data)
- **Record Count:** 2,500,000 documents
- **Type:** Documents index
- **Primary Key:** `conversation_id` (keyword)
- **Key Fields:**
  - `conversation_id`: Unique conversation identifier
  - `session_id`: Multi-turn session grouping
  - `turn_number`: Position in conversation sequence
  - `user_query`: Original user question
  - `retrieved_assets`: Array of asset IDs returned
  - `retrieval_method`: Strategy used (semantic, hybrid, fuzzy, etc.)
  - `timestamp`: Query timestamp
  - `response_time_ms`: Retrieval latency
  - `user_satisfaction`: Rating (1-5)
  - `required_clarification`: Boolean indicating if follow-up needed
  - `context_from_previous`: Boolean indicating context usage
- **Relationships:** References `brand_assets` via `retrieved_assets` array

### **retrieval_experiments** (A/B Testing Data)
- **Record Count:** 50,000 documents
- **Type:** Documents index
- **Primary Key:** `experiment_id` (keyword)
- **Key Fields:**
  - `experiment_id`: Unique experiment identifier
  - `experiment_name`: Descriptive name
  - `model_type`: Embedding model tested (e.g., "e5-large", "bge-base")
  - `retrieval_strategy`: Strategy tested (semantic, hybrid, fuzzy, etc.)
  - `semantic_weight`: Weight for semantic matching (0-1)
  - `keyword_weight`: Weight for keyword matching (0-1)
  - `start_date`: Experiment start timestamp
  - `end_date`: Experiment end timestamp
  - `query_count`: Number of queries tested
  - `avg_precision`: Average precision score
  - `avg_recall`: Average recall score
  - `avg_response_time_ms`: Average latency
  - `quality_score`: Overall quality metric (0-100)
  - `status`: Current status (running, completed, failed)
- **Relationships:** Experiments test retrieval strategies used in `ai_assistant_conversations`

### **query_templates** (Template Management)
- **Record Count:** 40 documents
- **Type:** Documents index
- **Primary Key:** `template_id` (keyword)
- **Key Fields:**
  - `template_id`: Unique template identifier
  - `template_name`: Descriptive name
  - `query_dsl`: JSON string of Elasticsearch Query DSL
  - `use_case`: Associated use case
  - `created_date`: Template creation date
  - `last_modified`: Last update timestamp
  - `usage_count`: Times template has been used
  - `maintenance_hours`: Hours spent maintaining template
  - `complexity_score`: Complexity rating (1-10)
  - `requires_update`: Boolean flag for needed updates
- **Relationships:** Templates define retrieval strategies tracked in `retrieval_experiments`

### **customer_accounts** (Reference Data)
- **Record Count:** 850 documents
- **Type:** Lookup index (**MUST have "index.mode": "lookup"**)
- **Primary Key:** `customer_id` (keyword)
- **Key Fields:**
  - `customer_id`: Unique customer identifier
  - `company_name`: Customer company name
  - `industry`: Industry vertical
  - `tier`: Service tier (enterprise, professional, standard)
  - `region`: Geographic region
  - `account_manager`: Assigned account manager name
  - `total_assets`: Total brand assets owned
  - `monthly_queries`: Average monthly query volume
  - `contract_value`: Annual contract value
- **Relationships:** Referenced by `brand_assets` for enrichment

### **retrieval_quality_incidents** (Incident Tracking)
- **Record Count:** 15,000 documents
- **Type:** Documents index
- **Primary Key:** `incident_id` (keyword)
- **Key Fields:**
  - `incident_id`: Unique incident identifier
  - `reported_date`: When incident was reported
  - `query_text`: Original problematic query
  - `expected_results`: What should have been retrieved
  - `actual_results`: What was actually retrieved
  - `root_cause`: Identified cause (embedding issue, query parsing, etc.)
  - `debug_time_minutes`: Time spent debugging
  - `resolution`: How it was fixed
  - `template_id`: Associated query template (if applicable)
  - `severity`: Impact level (critical, high, medium, low)
  - `status`: Current status (open, investigating, resolved)
- **Relationships:** Links to `query_templates` via `template_id`

---

## **🚀 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

**CRITICAL: All indexes need "index.mode": "lookup" for joins to work**

#### **1. Upload brand_assets index**

Navigate to: **Management → Dev Tools**

```json
PUT brand_assets
{
  "mappings": {
    "properties": {
      "asset_id": { "type": "keyword" },
      "asset_name": { "type": "text" },
      "asset_type": { "type": "keyword" },
      "brand_name": { "type": "keyword" },
      "tags": { "type": "keyword" },
      "created_date": { "type": "date" },
      "file_size_mb": { "type": "float" },
      "usage_count": { "type": "long" },
      "quality_score": { "type": "integer" },
      "customer_id": { "type": "keyword" },
      "embedding_vector": { "type": "dense_vector", "dims": 768 }
    }
  }
}
```

Then use **Management → Stack Management → Index Management → Data** to upload CSV with sample data.

#### **2. Upload ai_assistant_conversations index**

```json
PUT ai_assistant_conversations
{
  "mappings": {
    "properties": {
      "conversation_id": { "type": "keyword" },
      "session_id": { "type": "keyword" },
      "turn_number": { "type": "integer" },
      "user_query": { "type": "text" },
      "retrieved_assets": { "type": "keyword" },
      "retrieval_method": { "type": "keyword" },
      "timestamp": { "type": "date" },
      "response_time_ms": { "type": "integer" },
      "user_satisfaction": { "type": "integer" },
      "required_clarification": { "type": "boolean" },
      "context_from_previous": { "type": "boolean" }
    }
  }
}
```

#### **3. Upload retrieval_experiments index**

```json
PUT retrieval_experiments
{
  "mappings": {
    "properties": {
      "experiment_id": { "type": "keyword" },
      "experiment_name": { "type": "text" },
      "model_type": { "type": "keyword" },
      "retrieval_strategy": { "type": "keyword" },
      "semantic_weight": { "type": "float" },
      "keyword_weight": { "type": "float" },
      "start_date": { "type": "date" },
      "end_date": { "type": "date" },
      "query_count": { "type": "long" },
      "avg_precision": { "type": "float" },
      "avg_recall": { "type": "float" },
      "avg_response_time_ms": { "type": "integer" },
      "quality_score": { "type": "integer" },
      "status": { "type": "keyword" }
    }
  }
}
```

#### **4. Upload query_templates index**

```json
PUT query_templates
{
  "mappings": {
    "properties": {
      "template_id": { "type": "keyword" },
      "template_name": { "type": "text" },
      "query_dsl": { "type": "text" },
      "use_case": { "type": "keyword" },
      "created_date": { "type": "date" },
      "last_modified": { "type": "date" },
      "usage_count": { "type": "long" },
      "maintenance_hours": { "type": "float" },
      "complexity_score": { "type": "integer" },
      "requires_update": { "type": "boolean" }
    }
  }
}
```

#### **5. Upload customer_accounts index (LOOKUP MODE)**

**CRITICAL: This must be a lookup index for joins:**

```json
PUT customer_accounts
{
  "settings": {
    "index": {
      "mode": "lookup"
    }
  },
  "mappings": {
    "properties": {
      "customer_id": { "type": "keyword" },
      "company_name": { "type": "keyword" },
      "industry": { "type": "keyword" },
      "tier": { "type": "keyword" },
      "region": { "type": "keyword" },
      "account_manager": { "type": "keyword" },
      "total_assets": { "type": "long" },
      "monthly_queries": { "type": "long" },
      "contract_value": { "type": "long" }
    }
  }
}
```

#### **6. Upload retrieval_quality_incidents index**

```json
PUT retrieval_quality_incidents
{
  "mappings": {
    "properties": {
      "incident_id": { "type": "keyword" },
      "reported_date": { "type": "date" },
      "query_text": { "type": "text" },
      "expected_results": { "type": "text" },
      "actual_results": { "type": "text" },
      "root_cause": { "type": "keyword" },
      "debug_time_minutes": { "type": "integer" },
      "resolution": { "type": "text" },
      "template_id": { "type": "keyword" },
      "severity": { "type": "keyword" },
      "status": { "type": "keyword" }
    }
  }
}
```

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to your AI Agent chat interface
- Have the agent already configured with all tools

### **Demo Script**

**Presenter:** "Before we dive into how this works, let me show you the end result. Adobe's Brand Concierge team was spending 3 weeks just to evaluate a new embedding model, and 30-60 minutes debugging each retrieval quality incident. Let me show you how our AI agent can answer complex questions instantly."

**Sample questions to demonstrate:**

1. **ROI Analysis:**
   *"What's the total maintenance burden across all our query templates? Calculate the total hours spent and identify the top 5 templates requiring the most maintenance effort."*
   
   **Why this matters:** Shows how 40+ templates requiring 1-2 weeks to update can be analyzed instantly.

2. **Retrieval Performance Comparison:**
   *"Compare the performance of semantic vs hybrid retrieval strategies in our experiments. Which approach has better quality scores and what's the response time difference?"*
   
   **Why this matters:** Demonstrates the A/B testing framework eliminating 3-week engineering projects.

3. **Cross-Dataset Incident Analysis:**
   *"Find all critical retrieval quality incidents from the last quarter and show me which query templates were involved. Include the average debug time for each template."*
   
   **Why this matters:** Addresses the 30-60 minute per incident debugging problem with visibility.

4. **Customer Context Enrichment:**
   *"Show me the top 10 enterprise tier customers by monthly query volume, and for each one, tell me how many brand assets they own and their primary industry."*
   
   **Why this matters:** Demonstrates combining multiple specialized data sources automatically.

5. **Conversation Quality Trends:**
   *"What percentage of our AI assistant conversations required clarification questions? Break it down by retrieval method and show me which approach has the best first-turn success rate."*
   
   **Why this matters:** Shows multi-turn conversation analysis for context understanding optimization.

6. **Experiment Success Metrics:**
   *"Which embedding models in our experiments achieved quality scores above 85? For each one, show me the semantic/keyword weight balance and average precision."*
   
   **Why this matters:** Enables rapid experimentation framework for model evaluation.

7. **Asset Usage Intelligence:**
   *"Find the most-used brand assets from the last month and enrich them with customer company names and service tiers. Which customer segments drive the most asset usage?"*
   
   **Why this matters:** Combines retrieval data with customer context for personalized strategies.

**Transition:** "Notice how the agent automatically knew which datasets to query, how to join them together, and how to calculate the business metrics Adobe cares about. So how does this actually work? Let's go under the hood and build these queries from scratch."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open Kibana Dev Tools Console
- Have the indices already created and populated

---

### **Query 1: Simple Aggregation (2 minutes)**

**Presenter:** "Adobe's engineering team wants to understand their query template maintenance burden. Let's start with a simple question: What are the most complex query templates and how much maintenance effort do they require?"

**Copy/paste into console:**

```esql
FROM query_templates
| STATS total_maintenance = SUM(maintenance_hours), template_count = COUNT() BY complexity_score
| SORT complexity_score DESC
| LIMIT 10
```

**Run and narrate results:** "This is basic ES|QL:
- FROM: Source our query templates data
- STATS: Aggregate maintenance hours and count templates by complexity
- SORT and LIMIT: Top 10 complexity levels

The syntax is intuitive - it reads like English. We can see immediately which complexity levels consume the most maintenance time."

---

### **Query 2: Add Calculations with EVAL (3 minutes)**

**Presenter:** "Let's add calculations to understand the ROI of optimizing these templates. We'll calculate average maintenance per template and identify high-impact optimization targets."

**Copy/paste:**

```esql
FROM query_templates
| WHERE requires_update == true
| EVAL avg_maintenance_per_use = TO_DOUBLE(maintenance_hours) / TO_DOUBLE(usage_count)
| EVAL total_cost_estimate = maintenance_hours * 150
| STATS 
    total_templates = COUNT(),
    total_maintenance_hours = SUM(maintenance_hours),
    total_cost = SUM(total_cost_estimate),
    avg_complexity = AVG(complexity_score)
  BY use_case
| EVAL avg_cost_per_template = total_cost / total_templates
| SORT total_cost DESC
| LIMIT 10
```

**Run and highlight:** "Key additions:
- EVAL: Creates calculated fields on-the-fly (cost per use, total cost estimate)
- TO_DOUBLE: Critical for decimal division to avoid integer rounding
- Multiple STATS: Aggregating multiple metrics simultaneously
- Business-relevant calculations: Converting hours to dollar costs at $150/hour
- WHERE filter: Focus only on templates flagged for updates

This shows Adobe exactly where to focus optimization efforts - the use cases with highest total maintenance cost."

---

### **Query 3: Join Datasets with LOOKUP JOIN (3 minutes)**

**Presenter:** "Now let's get sophisticated. Adobe wants to understand which customer segments are experiencing retrieval quality incidents. We'll join incident data with customer account information."

**Copy/paste:**

```esql
FROM retrieval_quality_incidents
| WHERE severity IN ("critical", "high")
| STATS 
    incident_count = COUNT(),
    avg_debug_time = AVG(debug_time_minutes),
    total_debug_hours = SUM(debug_time_minutes) / 60
  BY template_id
| LOOKUP customer_accounts ON template_id
| EVAL debug_cost = total_debug_hours * 150
| WHERE incident_count > 5
| SORT debug_cost DESC
| LIMIT 15
```

**Run and explain:** "Magic happening here:
- LOOKUP JOIN: Combines incident data with customer context using template_id
- Now we have access to fields from both datasets (customer tier, industry, etc.)
- This is a LEFT JOIN: All incidents kept, enriched with customer data where available
- For LOOKUP JOIN to work, the joined index must have 'index.mode: lookup'
- Business insight: We can now see which customer segments experience the most incidents and the associated cost

This visibility was previously impossible - it took 30-60 minutes per incident without pattern recognition."

---

### **Query 4: Complex Multi-Dataset Analytics (2 minutes)**

**Presenter:** "For the grand finale - a sophisticated analytical query showing Adobe's complete retrieval optimization landscape. We'll analyze experiment results, calculate ROI, and identify the best-performing strategies with full customer context."

**Copy/paste:**

```esql
FROM retrieval_experiments
| WHERE status == "completed" AND quality_score >= 80
| EVAL 
    precision_recall_balance = (avg_precision + avg_recall) / 2,
    quality_per_ms = TO_DOUBLE(quality_score) / TO_DOUBLE(avg_response_time_ms),
    weight_ratio = semantic_weight / keyword_weight,
    experiment_duration_days = (end_date - start_date) / (1000 * 60 * 60 * 24)
| STATS
    experiment_count = COUNT(),
    avg_quality = AVG(quality_score),
    avg_precision = AVG(avg_precision),
    avg_recall = AVG(avg_recall),
    avg_response_time = AVG(avg_response_time_ms),
    total_queries_tested = SUM(query_count),
    best_quality = MAX(quality_score),
    median_weight_ratio = PERCENTILE(weight_ratio, 50)
  BY retrieval_strategy, model_type
| EVAL 
    quality_improvement_vs_baseline = ((avg_quality - 70) / 70) * 100,
    queries_per_experiment = total_queries_tested / experiment_count,
    strategy_label = CONCAT(retrieval_strategy, " (", model_type, ")")
| WHERE avg_quality >= 85
| SORT avg_quality DESC, avg_response_time ASC
| LIMIT 20
```

**Run and break down:** 

"This query is doing serious analytical work:

**Data Preparation (Lines 1-7):**
- Filtering to completed experiments with quality threshold
- Calculating composite metrics: precision/recall balance, quality-per-millisecond efficiency
- Computing weight ratios to understand semantic vs keyword balance
- Converting timestamp differences to human-readable days

**Aggregation Layer (Lines 8-17):**
- Multi-dimensional grouping by strategy AND model type
- Computing statistical measures: averages, totals, max values, percentiles
- The percentile function shows us the typical weight ratio (median) per strategy

**Business Intelligence (Lines 18-21):**
- Quality improvement percentage vs baseline (70 is Adobe's current baseline)
- Queries per experiment shows testing thoroughness
- Concatenated labels for readable results
- Final filtering to show only high-performers (85+ quality)

**Results Interpretation:**
Adobe can now see:
- Which combination of retrieval strategy + embedding model performs best
- Whether quality improvements justify any latency increases
- The optimal semantic/keyword weight balance for hybrid search
- How much better than baseline (70) each approach performs

**The Business Impact:**
This single query replaces what used to be a 3-week engineering project. Adobe can now evaluate new embedding models in minutes, not weeks. They can see immediately if a 75/25 semantic/keyword split (from their weighted hybrid search use case) is optimal, or if other ratios perform better."

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

**Agent Configuration:**

**Agent ID:** `adobe-brand-retrieval-optimizer`

**Display Name:** `Adobe Brand Retrieval Intelligence Agent`

**Custom Instructions:** 
```
You are an AI assistant specialized in Adobe's Brand Concierge retrieval optimization and quality analysis. Your role is to help engineers and product managers analyze retrieval experiments, debug quality incidents, understand customer usage patterns, and optimize query templates.

Key Capabilities:
1. Analyze retrieval experiment results and recommend optimal strategies
2. Debug retrieval quality incidents by finding patterns across similar failures
3. Calculate ROI and maintenance burden for query template optimization
4. Provide customer-enriched insights by combining asset usage with account data
5. Evaluate multi-turn conversation quality and context awareness
6. Compare semantic vs hybrid vs fuzzy retrieval performance

When answering questions:
- Always provide quantitative metrics (quality scores, response times, costs)
- Calculate business impact (hours saved, cost reductions, quality improvements)
- Compare against Adobe's baseline (70 quality score, 3-week experiment cycles)
- Highlight patterns across multiple incidents or experiments
- Recommend specific retrieval strategies based on data
- Use customer context (tier, industry) when relevant for personalization insights

Data Context:
- 45M brand assets across 850 customer accounts
- 2.5M AI assistant conversations with multi-turn context
- 50K retrieval experiments testing different strategies
- 40 query templates requiring ongoing maintenance
- 15K quality incidents with debug time tracking

Adobe's Pain Points You're Solving:
- 3-week engineering projects for model evaluation → Minutes with experiments analysis
- 30-60 min per incident debugging → Pattern recognition across incidents
- 1-2 weeks to update 40+ templates → Identify high-impact templates first
- No multi-turn context → Analyze conversation patterns
- 2-3 days writing new Query DSL → Test strategies via experiments

Always be specific, data-driven, and focused on actionable insights.
```

---

### **Creating Tools**

**Tool 1: Brand Asset Analytics**
- **Tool Name:** `analyze_brand_assets`
- **Index:** `brand_assets`
- **Description:** "Analyze Adobe's 45 million brand assets including usage patterns, quality scores, customer ownership, asset types, and file sizes. Use this tool for questions about asset performance, customer asset libraries, most-used assets, quality distributions, or asset type breakdowns. Can filter by customer, brand, date range, or asset type."
- **Sample ES|QL:**
```esql
FROM brand_assets
| STATS 
    total_assets = COUNT(),
    avg_quality = AVG(quality_score),
    total_usage = SUM(usage_count),
    avg_size_mb = AVG(file_size_mb)
  BY asset_type, brand_name
| SORT total_usage DESC
| LIMIT 20
```

**Tool 2: Retrieval Experiment Analysis**
- **Tool Name:** `analyze_retrieval_experiments`
- **Index:** `retrieval_experiments`
- **Description:** "Analyze Adobe's retrieval optimization experiments including A/B tests of different embedding models (e5-large, bge-base, etc.), retrieval strategies (semantic, hybrid, fuzzy), and weight configurations. Use for questions about experiment performance, quality scores, precision/recall metrics, response times, optimal strategies, or model comparisons. Includes semantic_weight and keyword_weight for hybrid search analysis."
- **Sample ES|QL:**
```esql
FROM retrieval_experiments
| WHERE status == "completed" AND quality_score >= 80
| STATS 
    avg_quality = AVG(quality_score),
    avg_precision = AVG(avg_precision),
    avg_recall = AVG(avg_recall),
    experiment_count = COUNT()
  BY retrieval_strategy, model_type
| SORT avg_quality DESC
```

**Tool 3: Conversation Quality Analysis**
- **Tool Name:** `analyze_conversation_quality`
- **Index:** `ai_assistant_conversations`
- **Description:** "Analyze Adobe's 2.5M AI assistant conversations including multi-turn sessions, retrieval methods used, user satisfaction scores, clarification requirements, and context usage. Use for questions about conversation success rates, retrieval method effectiveness, multi-turn context patterns, response times, or user satisfaction trends. Can analyze by retrieval method, time period, or session patterns."
- **Sample ES|QL:**
```esql
FROM ai_assistant_conversations
| STATS 
    total_conversations = COUNT(),
    avg_satisfaction = AVG(user_satisfaction),
    clarification_rate = AVG(CASE(required_clarification == true, 1, 0)),
    context_usage_rate = AVG(CASE(context_from_previous == true, 1, 0)),
    avg_response_time = AVG(response_time_ms)
  BY retrieval_method
| EVAL clarification_pct = clarification_rate * 100
| SORT avg_satisfaction DESC
```

**Tool 4: Quality Incident Debugging**
- **Tool Name:** `debug_quality_incidents`
- **Index:** `retrieval_quality_incidents`
- **Description:** "Debug Adobe's retrieval quality incidents including failed queries, root causes, debug times, severity levels, and resolutions. Use for questions about incident patterns, common failure modes, debug time analysis, template-related issues, or incident trends. Helps identify systematic problems reducing the 30-60 minutes per incident debug time."
- **Sample ES|QL:**
```esql
FROM retrieval_quality_incidents
| WHERE severity IN ("critical", "high")
| STATS 
    incident_count = COUNT(),
    avg_debug_time = AVG(debug_time_minutes),
    total_debug_hours = SUM(debug_time_minutes) / 60
  BY root_cause, severity
| EVAL debug_cost = total_debug_hours * 150
| SORT incident_count DESC
```

**Tool 5: Query Template Management**
- **Tool Name:** `analyze_query_templates`
- **Index:** `query_templates`
- **Description:** "Analyze Adobe's 40 query templates including maintenance burden, complexity scores, usage frequency, and update requirements. Use for questions about template maintenance costs, high-complexity templates, frequently-used templates, or optimization priorities. Helps address the 1-2 weeks required to update templates."
- **Sample ES|QL:**
```esql
FROM query_templates
| WHERE requires_update == true
| STATS 
    template_count = COUNT(),
    total_maintenance_hours = SUM(maintenance_hours),
    avg_complexity = AVG(complexity_score),
    total_usage = SUM(usage_count)
  BY use_case
| EVAL maintenance_cost = total_maintenance_hours * 150
| SORT maintenance_cost DESC
```

**Tool 6: Customer-Enriched Asset Intelligence**
- **Tool Name:** `customer_asset_insights`
- **Index:** `brand_assets` (with LOOKUP to `customer_accounts`)
- **Description:** "Combine brand asset data with customer account context including company names, industry verticals, service tiers, regions, and contract values. Use for questions about customer segment analysis, enterprise vs professional tier usage, industry-specific patterns, or personalized retrieval insights. Requires joining brand_assets with customer_accounts."
- **Sample ES|QL:**
```esql
FROM brand_assets
| STATS 
    asset_count = COUNT(),
    avg_quality = AVG(quality_score),
    total_usage = SUM(usage_count)
  BY customer_id
| LOOKUP customer_accounts ON customer_id
| WHERE tier == "enterprise"
| SORT asset_count DESC
| LIMIT 20
```

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

**Warm-up Questions (Understanding the Data):**

1. *"How many brand assets does Adobe have in total, and what's the average quality score?"*
   - Tests basic aggregation on brand_assets
   - Should return ~45M assets with quality metrics

2. *"What are the different retrieval methods being used in our AI assistant conversations?"*
   - Tests categorical breakdown
   - Should show semantic, hybrid, fuzzy, exact match, etc.

3. *"How many retrieval experiments have we completed, and what's the range of quality scores?"*
   - Tests filtering and statistical functions
   - Shows experiment volume and quality distribution

---

**Business-Focused Questions (ROI & Impact):**

4. *"Calculate the total cost of debugging retrieval quality incidents over the last quarter. Assume $150/hour for engineering time."*
   - Tests time-based filtering, aggregation, and cost calculation
   - Should sum debug_time_minutes and multiply by hourly rate
   - **Expected insight:** Quantifies the 30-60 min per incident problem

5. *"Which query templates require updates and have the highest maintenance burden? Show me the top 5 with total hours spent."*
   - Tests filtering (requires_update == true) and ranking
   - **Expected insight:** Identifies optimization priorities for the 40+ templates

6. *"What's the ROI if we reduce clarification questions by 50%? Calculate based on current conversation volume and average response time savings."*
   - Tests complex calculation with hypothetical scenarios
   - Should analyze clarification rates and time impact
   - **Expected insight:** Quantifies multi-turn context improvement value

---

**Trend Analysis Questions:**

7. *"Compare user satisfaction scores across different retrieval methods. Which approach has the highest satisfaction and lowest clarification rate?"*
   - Tests multi-metric comparison across categories
   - Should join satisfaction with clarification_required
   - **Expected insight:** Validates retrieval strategy effectiveness

8. *"Show me the trend of retrieval quality incidents over time. Are we getting better or worse?"*
   - Tests time-series analysis with date bucketing
   - Should group incidents by month/week
   - **Expected insight:** Shows if quality is improving

9. *"Which embedding models in our experiments achieved quality scores above 85, and how do their response times compare?"*
   - Tests filtering, grouping, and multi-metric comparison
   - **Expected insight:** Identifies best model candidates for the 3-week evaluation problem

---

**Optimization & Strategy Questions:**

10. *"For hybrid retrieval experiments, what's the optimal balance between semantic_weight and keyword_weight? Show me the top 5 weight combinations by quality score."*
   - Tests advanced filtering and ranking on weight configurations
   - **Expected insight:** Validates the 75/25 weighted hybrid approach or suggests alternatives

11. *"Find all critical incidents related to fuzzy search failures. What are the common root causes and how long did they take to debug?"*
   - Tests multi-field filtering and pattern analysis
   - **Expected insight:** Identifies systematic fuzzy search issues

12. *"Which enterprise customers have the most brand assets and the highest monthly query volumes? Enrich with their industry and account manager."*
   - Tests LOOKUP JOIN between brand_assets and customer_accounts
   - **Expected insight:** Shows customer segmentation for personalized retrieval

---

**Advanced Multi-Dataset Questions:**

13. *"Compare the performance of experiments using 'bge-base' vs 'e5-large' embedding models. For each, show average quality, precision, recall, and the number of experiments run."*
   - Tests grouping and multi-metric aggregation
   - **Expected insight:** Direct model comparison for evaluation

14. *"What percentage of our AI assistant conversations use context from previous turns? Break it down by retrieval method to see which strategies benefit most from multi-turn context."*
   - Tests boolean field aggregation and percentage calculation
   - **Expected insight:** Shows context-aware retrieval effectiveness

15. *"Find the query templates with complexity scores above 7 that are also associated with quality incidents. Calculate the total debug time for each template."*
   - Tests multi-dataset correlation (query_templates + retrieval_quality_incidents)
   - **Expected insight:** Links template complexity to operational issues

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "Modern query language, built for analytics - not just search"
- "Piped syntax is intuitive and readable - no nested JSON"
- "Operates on blocks, not rows - extremely performant at scale"
- "Supports complex operations: joins, window functions, time-series, statistical functions"
- "Adobe can now write analytical queries in minutes vs 2-3 days for Query DSL"

### **On Agent Builder:**
- "Bridges AI and enterprise data - no custom development needed"
- "Works with existing Elasticsearch indices - no data migration"
- "Agent automatically selects right tools based on question intent"
- "Reduces dependency on data teams - democratizes data access"
- "Adobe's engineers can focus on building features, not maintaining query templates"

### **On Business Value for Adobe:**
- "**3 weeks → minutes:** Retrieval experiment evaluation goes from engineering project to self-service analysis"
- "**30-60 min → seconds:** Incident debugging with pattern recognition across 15K incidents"
- "**1-2 weeks → hours:** Template optimization prioritized by data-driven ROI analysis"
- "**Stateless → stateful:** Multi-turn conversation analysis enables context-aware retrieval"
- "**40+ templates → intelligent composition:** Agent automatically combines specialized retrieval strategies"
- "**Real-time insights:** Always up-to-date with live Elasticsearch data"
- "**Explainable retrieval:** Complete transparency into why results were returned"

### **Addressing Adobe's Specific Pain Points:**

**Pain Point 1: No framework for retrieval experimentation**
- "Agent Builder provides instant analysis of 50K experiments across models and strategies"
- "Compare quality, precision, recall, and response times in natural language"
- "A/B test results accessible to entire team, not just engineers"

**Pain Point 2: Limited context understanding**
- "Analyze 2.5M conversations to understand multi-turn patterns"
- "Identify which retrieval methods benefit most from contextual awareness"
- "Measure clarification rates to optimize first-turn success"

**Pain Point 3: No ability to combine specialized retrieval strategies**
- "Agent automatically composes multiple tools for complex questions"
- "Single question can analyze assets, experiments, incidents, and customer context"
- "Intelligent tool selection eliminates manual Query DSL composition"

**Pain Point 4: High maintenance burden**
- "Identify which of 40+ templates need updates and their maintenance cost"
- "Prioritize optimization by ROI - total hours × $150/hour"
- "Track template complexity and usage to focus engineering effort"

**Pain Point 5: Difficulty debugging poor retrieval results**
- "Pattern recognition across 15K incidents with root cause analysis"
- "Link incidents to specific templates and customer segments"
- "Calculate total debug cost and identify systematic issues"

---

## **🔧 Troubleshooting**

**If a query fails:**
- Check index names match exactly (case-sensitive: `brand_assets` not `Brand_Assets`)
- Verify field names are correct (e.g., `customer_id` not `customerId`)
- Ensure joined indices are in lookup mode (customer_accounts must have `"index.mode": "lookup"`)
- Check that date fields are properly formatted (ISO 8601)
- Verify numeric fields aren't being treated as strings (use TO_DOUBLE for calculations)

**If agent gives wrong answer:**
- Check tool descriptions - are they clear about what data each tool contains?
- Review custom instructions - does the agent understand Adobe's context?
- Verify the agent has access to all 6 tools
- Check if the question requires a JOIN - ensure lookup indices are configured
- Look at the ES|QL query the agent generated - is it syntactically correct?

**If join returns no results:**
- Verify join key format is consistent across datasets (e.g., both use `customer_id`)
- Check that lookup index (customer_accounts) has data loaded
- Ensure the lookup index has `"index.mode": "lookup"` in settings
- Verify the join key exists in both datasets (use a simple query to check)

**If calculations seem wrong:**
- Check for integer division - always use TO_DOUBLE for decimal results
- Verify aggregation functions are using correct fields
- Look for null values that might affect averages
- Ensure EVAL calculations happen before STATS when needed

**If performance is slow:**
- Add WHERE filters early in the query to reduce data volume
- Use LIMIT to restrict result sets
- Check if indices are properly sized for demo (don't need full 45M records)
- Consider using sampled data for demo purposes

---

## **🎬 Closing**

"What we've shown today addresses Adobe's specific challenges:

✅ **3-week experiment evaluation → minutes** - Analyze 50K experiments across models and strategies instantly

✅ **30-60 min incident debugging → seconds** - Pattern recognition across 15K incidents with root cause analysis

✅ **1-2 weeks template updates → data-driven prioritization** - Calculate ROI for optimizing 40+ templates

✅ **Stateless retrieval → multi-turn context awareness** - Analyze 2.5M conversations to optimize context usage

✅ **Manual Query DSL composition → intelligent tool orchestration** - Agent automatically combines specialized retrieval strategies

✅ **No visibility → complete explainability** - Understand exactly why retrieval decisions were made

**The Adobe Brand Concierge team can now:**
- Evaluate new embedding models in minutes, not weeks
- Debug retrieval failures with pattern recognition, not manual investigation
- Optimize query templates based on data-driven ROI analysis
- Understand multi-turn conversation patterns to improve context awareness
- Make retrieval strategy decisions backed by 50K experiments worth of data

**Deployment Timeline:**
- Agent Builder can be configured and deployed in days, not months
- No custom development required - just configuration
- Works with existing Elasticsearch infrastructure
- Scales to Adobe's 45M assets and 2.5M conversations

**Questions?"**

---

## **📊 Demo Success Metrics**

After the demo, you should be able to answer:

- ✅ Can the audience see how Agent Builder eliminates the 3-week experiment evaluation cycle?
- ✅ Did we demonstrate pattern recognition across incidents reducing debug time?
- ✅ Was the ROI calculation for template optimization clear and compelling?
- ✅ Did we show multi-turn conversation analysis for context awareness?
- ✅ Was the automatic tool composition for complex queries impressive?
- ✅ Can they envision their team using this without engineering support?

**Follow-up Actions:**
1. Share this demo guide with attendees
2. Provide sample CSV datasets for their own testing
3. Schedule technical deep-dive on Agent Builder configuration
4. Discuss integration with Adobe's existing retrieval infrastructure
5. Plan pilot deployment with Brand Concierge team

---

**End of Demo Guide**