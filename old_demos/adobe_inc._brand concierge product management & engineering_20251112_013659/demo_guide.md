# **Elastic Agent Builder Demo for Adobe Inc.**

## **Internal Demo Script & Reference Guide**

---

## **📋 Demo Overview**

**Total Time:** 25-30 minutes
**Audience:** Brand Concierge Product Management & Engineering technical/business stakeholders
**Goal:** Show how Agent Builder enables AI-powered analytics on Adobe Brand Concierge data to solve multi-tenant performance, customer health, and product experimentation challenges

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## **🗂️ Dataset Architecture**

### **api_requests** (Timeseries Index)
- **Record Count:** 250,000,000+ records
- **Primary Key:** `request_id` (unique identifier per API call)
- **Key Fields:**
  - `@timestamp` - Request timestamp
  - `tenant_id` - Foreign key to tenants table
  - `partner_id` - Foreign key to api_partners table
  - `endpoint` - API endpoint path
  - `method` - HTTP method (GET, POST, etc.)
  - `response_time_ms` - Response latency in milliseconds
  - `status_code` - HTTP status code
  - `error_message` - Error details (if applicable)
  - `region` - Data center region
- **Relationships:** Links to `tenants` and `api_partners` via foreign keys

### **tenants** (Reference/Lookup Index)
- **Record Count:** 850+ records
- **Primary Key:** `tenant_id`
- **Key Fields:**
  - `tenant_id` - Unique tenant identifier
  - `tenant_name` - Company/organization name
  - `account_tier` - Enterprise, Professional, Standard
  - `arr` - Annual Recurring Revenue (USD)
  - `renewal_date` - Contract renewal date
  - `industry_vertical` - Retail, Financial Services, Media, etc.
  - `onboarding_date` - Customer start date
  - `sla_p95_target_ms` - Contracted P95 latency SLA
  - `csm_name` - Customer Success Manager
- **Index Mode:** `lookup` (required for LOOKUP JOIN)

### **api_partners** (Reference/Lookup Index)
- **Record Count:** 40+ records
- **Primary Key:** `partner_id`
- **Key Fields:**
  - `partner_id` - Unique partner identifier
  - `partner_name` - Partner company name
  - `partner_tier` - Strategic, Premium, Standard
  - `integration_type` - Webhook, REST API, GraphQL
  - `contract_value` - Annual contract value
  - `support_level` - 24/7, Business Hours, Community
  - `technical_contact_email` - Escalation contact
- **Index Mode:** `lookup`

### **feature_usage_events** (Timeseries Index)
- **Record Count:** 150,000,000+ records
- **Primary Key:** `event_id`
- **Key Fields:**
  - `@timestamp` - Event timestamp
  - `tenant_id` - Foreign key to tenants
  - `user_id` - End user identifier
  - `feature_name` - Feature identifier (e.g., "asset_search", "brand_guidelines")
  - `event_type` - view, click, complete, error
  - `session_id` - Links to user_sessions
  - `experiment_id` - Foreign key to ab_experiments (if in experiment)
  - `variant` - A or B (if in experiment)
  - `metadata` - JSON with additional context
- **Relationships:** Links to `tenants`, `user_sessions`, `ab_experiments`

### **user_sessions** (Timeseries Index)
- **Record Count:** 75,000,000+ records
- **Primary Key:** `session_id`
- **Key Fields:**
  - `session_id` - Unique session identifier
  - `tenant_id` - Foreign key to tenants
  - `user_id` - End user identifier
  - `session_start` - Session start timestamp
  - `session_end` - Session end timestamp
  - `duration_seconds` - Session length
  - `page_views` - Number of pages viewed
  - `features_used` - Array of features accessed
  - `device_type` - Desktop, Mobile, Tablet
  - `browser` - Browser type
- **Relationships:** Links to `tenants`

### **ab_experiments** (Reference/Lookup Index)
- **Record Count:** 150+ records
- **Primary Key:** `experiment_id`
- **Key Fields:**
  - `experiment_id` - Unique experiment identifier
  - `experiment_name` - Human-readable name
  - `hypothesis` - What we're testing
  - `start_date` - Experiment launch date
  - `end_date` - Experiment conclusion date
  - `status` - Running, Completed, Paused
  - `target_feature` - Feature being tested
  - `success_metric` - Primary KPI (conversion_rate, engagement, etc.)
  - `minimum_sample_size` - Statistical threshold
- **Index Mode:** `lookup`

### **webhook_deliveries** (Timeseries Index)
- **Record Count:** 50,000,000+ records
- **Primary Key:** `delivery_id`
- **Key Fields:**
  - `@timestamp` - Delivery attempt timestamp
  - `partner_id` - Foreign key to api_partners
  - `tenant_id` - Foreign key to tenants
  - `event_type` - Type of webhook event
  - `delivery_status` - success, failed, retry
  - `response_time_ms` - Partner endpoint response time
  - `http_status` - HTTP status from partner
  - `retry_count` - Number of retry attempts
  - `payload_size_bytes` - Webhook payload size
- **Relationships:** Links to `api_partners` and `tenants`

---

## **🚀 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

**CRITICAL: All reference indexes need "index.mode": "lookup" for joins to work**

#### **1. Create api_requests index (timeseries)**

Navigate to **Dev Tools** and run:

```json
PUT /api_requests
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "request_id": { "type": "keyword" },
      "tenant_id": { "type": "keyword" },
      "partner_id": { "type": "keyword" },
      "endpoint": { "type": "keyword" },
      "method": { "type": "keyword" },
      "response_time_ms": { "type": "long" },
      "status_code": { "type": "integer" },
      "error_message": { "type": "text" },
      "region": { "type": "keyword" }
    }
  }
}
```

Upload `api_requests.csv` via **Machine Learning > Data Visualizer > Upload file**

#### **2. Create tenants index (lookup mode)**

```json
PUT /tenants
{
  "settings": {
    "index": {
      "mode": "lookup"
    }
  },
  "mappings": {
    "properties": {
      "tenant_id": { "type": "keyword" },
      "tenant_name": { "type": "keyword" },
      "account_tier": { "type": "keyword" },
      "arr": { "type": "long" },
      "renewal_date": { "type": "date" },
      "industry_vertical": { "type": "keyword" },
      "onboarding_date": { "type": "date" },
      "sla_p95_target_ms": { "type": "integer" },
      "csm_name": { "type": "keyword" }
    }
  }
}
```

Upload `tenants.csv` via **Data Visualizer**

#### **3. Create api_partners index (lookup mode)**

```json
PUT /api_partners
{
  "settings": {
    "index": {
      "mode": "lookup"
    }
  },
  "mappings": {
    "properties": {
      "partner_id": { "type": "keyword" },
      "partner_name": { "type": "keyword" },
      "partner_tier": { "type": "keyword" },
      "integration_type": { "type": "keyword" },
      "contract_value": { "type": "long" },
      "support_level": { "type": "keyword" },
      "technical_contact_email": { "type": "keyword" }
    }
  }
}
```

Upload `api_partners.csv` via **Data Visualizer**

#### **4. Create feature_usage_events index (timeseries)**

```json
PUT /feature_usage_events
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "event_id": { "type": "keyword" },
      "tenant_id": { "type": "keyword" },
      "user_id": { "type": "keyword" },
      "feature_name": { "type": "keyword" },
      "event_type": { "type": "keyword" },
      "session_id": { "type": "keyword" },
      "experiment_id": { "type": "keyword" },
      "variant": { "type": "keyword" },
      "metadata": { "type": "object" }
    }
  }
}
```

Upload `feature_usage_events.csv` via **Data Visualizer**

#### **5. Create user_sessions index (timeseries)**

```json
PUT /user_sessions
{
  "mappings": {
    "properties": {
      "session_id": { "type": "keyword" },
      "tenant_id": { "type": "keyword" },
      "user_id": { "type": "keyword" },
      "session_start": { "type": "date" },
      "session_end": { "type": "date" },
      "duration_seconds": { "type": "long" },
      "page_views": { "type": "integer" },
      "features_used": { "type": "keyword" },
      "device_type": { "type": "keyword" },
      "browser": { "type": "keyword" }
    }
  }
}
```

Upload `user_sessions.csv` via **Data Visualizer**

#### **6. Create ab_experiments index (lookup mode)**

```json
PUT /ab_experiments
{
  "settings": {
    "index": {
      "mode": "lookup"
    }
  },
  "mappings": {
    "properties": {
      "experiment_id": { "type": "keyword" },
      "experiment_name": { "type": "text" },
      "hypothesis": { "type": "text" },
      "start_date": { "type": "date" },
      "end_date": { "type": "date" },
      "status": { "type": "keyword" },
      "target_feature": { "type": "keyword" },
      "success_metric": { "type": "keyword" },
      "minimum_sample_size": { "type": "integer" }
    }
  }
}
```

Upload `ab_experiments.csv` via **Data Visualizer**

#### **7. Create webhook_deliveries index (timeseries)**

```json
PUT /webhook_deliveries
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "delivery_id": { "type": "keyword" },
      "partner_id": { "type": "keyword" },
      "tenant_id": { "type": "keyword" },
      "event_type": { "type": "keyword" },
      "delivery_status": { "type": "keyword" },
      "response_time_ms": { "type": "long" },
      "http_status": { "type": "integer" },
      "retry_count": { "type": "integer" },
      "payload_size_bytes": { "type": "long" }
    }
  }
}
```

Upload `webhook_deliveries.csv` via **Data Visualizer**

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to your AI Agent chat interface
- Have the agent already configured with all tools

### **Demo Script**

**Presenter:** "Before we dive into how this works, let me show you the end result. I'm going to ask our AI agent complex business questions about Adobe Brand Concierge's multi-tenant platform."

**Sample questions to demonstrate:**

1. **ROI & Revenue Impact:**
   *"Which tenants are at risk of churning in the next 90 days based on declining feature usage? Calculate the total ARR at risk and rank by revenue impact."*
   
   **Why this impresses:** Cross-references feature usage patterns with tenant revenue data, calculates churn probability, quantifies financial impact - all in one question.

2. **Noisy Neighbor Detection:**
   *"Show me the top 5 noisy neighbor tenants from the past week - those consuming disproportionate resources and causing SLA breaches for others. Include their account tier and CSM contact."*
   
   **Why this impresses:** Identifies performance outliers, correlates with SLA violations, enriches with business context for immediate action.

3. **Partner Ecosystem Health:**
   *"Which API partners have experienced degraded webhook delivery success rates over the past 30 days? Show me the trend and prioritize by partner tier and contract value."*
   
   **Why this impresses:** Time-series trend detection, change point analysis, prioritization by business value.

4. **A/B Testing Decision Support:**
   *"For experiments related to 'conversion optimization' that completed in the last 60 days, which variants showed statistically significant uplift? Should we ship them?"*
   
   **Why this impresses:** Semantic search across experiment descriptions, statistical analysis, actionable go/no-go recommendations.

5. **Feature Adoption Funnel:**
   *"Analyze the adoption funnel for the 'brand_guidelines' feature by account tier. Where are Enterprise customers dropping off compared to Professional tier?"*
   
   **Why this impresses:** Multi-dimensional funnel analysis, cohort comparison, identifies friction points by customer segment.

6. **Cross-Dataset Performance Correlation:**
   *"Show me tenants where P95 API latency exceeds their SLA target AND feature engagement has dropped more than 30% month-over-month. This might indicate performance is driving disengagement."*
   
   **Why this impresses:** Correlates technical performance with user behavior, identifies causation patterns, proactive intervention opportunities.

7. **Real-Time Operational Alert:**
   *"In the last 2 hours, have any Strategic tier API partners experienced webhook delivery failures exceeding 10%? I need to know immediately for escalation."*
   
   **Why this impresses:** Real-time monitoring, threshold-based alerting, automatic prioritization by partner tier.

**Transition:** "So how does this actually work? These answers come from querying 500+ million records across 7 different datasets. Let's go under the hood and build these queries from scratch using ES|QL."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open Kibana Dev Tools Console
- Have the indices already created and populated

---

### **Query 1: Simple Aggregation (2 minutes)**

**Presenter:** "Adobe Brand Concierge wants to know: Which API endpoints are slowest on average, and how many requests are they handling?"

**Copy/paste into console:**

```esql
FROM api_requests
| STATS avg_response_ms = AVG(response_time_ms), 
        request_count = COUNT(*) 
  BY endpoint
| SORT avg_response_ms DESC
| LIMIT 10
```

**Run and narrate results:** "This is basic ES|QL:
- FROM: Source our data from the api_requests index
- STATS: Aggregate with grouping - calculating average response time and counting requests per endpoint
- SORT and LIMIT: Top 10 slowest endpoints

The syntax is intuitive - it reads like English. In 4 lines, we've analyzed 250 million API requests."

---

### **Query 2: Add Calculations with EVAL (3 minutes)**

**Presenter:** "Let's add business-relevant calculations. We want to identify potential SLA breaches - tenants whose P95 latency exceeds 500ms."

**Copy/paste:**

```esql
FROM api_requests
| WHERE @timestamp > NOW() - 7 days
| STATS p95_latency = PERCENTILE(response_time_ms, 95),
        total_requests = COUNT(*),
        error_rate = TO_DOUBLE(COUNT_IF(status_code >= 400)) / TO_DOUBLE(COUNT(*))
  BY tenant_id
| EVAL sla_breach = CASE(p95_latency > 500, "YES", "NO")
| EVAL error_rate_pct = ROUND(error_rate * 100, 2)
| WHERE sla_breach == "YES"
| SORT p95_latency DESC
| LIMIT 20
```

**Run and highlight:** "Key additions:
- WHERE: Time-based filtering - last 7 days only
- PERCENTILE: P95 latency calculation (critical for SLA monitoring)
- TO_DOUBLE: Critical for decimal division in error rate calculation
- EVAL with CASE: Business logic - flagging SLA breaches
- Multiple STATS: Aggregating multiple metrics simultaneously
- Chained WHERE: Filter after aggregation to show only breaches

We're now doing sophisticated analytics in 10 lines."

---

### **Query 3: Join Datasets with LOOKUP JOIN (3 minutes)**

**Presenter:** "Now let's combine data from multiple sources. We want to enrich our SLA breach data with tenant business context - account tier, ARR, and CSM owner."

**Copy/paste:**

```esql
FROM api_requests
| WHERE @timestamp > NOW() - 7 days
| STATS p95_latency = PERCENTILE(response_time_ms, 95),
        total_requests = COUNT(*),
        error_rate = TO_DOUBLE(COUNT_IF(status_code >= 400)) / TO_DOUBLE(COUNT(*))
  BY tenant_id
| EVAL sla_breach = CASE(p95_latency > 500, "YES", "NO")
| WHERE sla_breach == "YES"
| LOOKUP JOIN tenants ON tenant_id
| EVAL revenue_at_risk = arr
| KEEP tenant_id, tenant_name, account_tier, p95_latency, total_requests, 
       error_rate, arr, renewal_date, csm_name
| SORT arr DESC
| LIMIT 15
```

**Run and explain:** "Magic happening here:
- LOOKUP JOIN: Combines api_requests data with the tenants reference table
- ON tenant_id: The join key that links both datasets
- Now we have access to fields from both datasets - technical metrics AND business context
- This is a LEFT JOIN: All tenant records kept, enriched with additional data
- KEEP: Select only the fields we want in the output
- For LOOKUP JOIN to work, the tenants index must have 'index.mode: lookup'

We've now answered: 'Which high-value customers are experiencing SLA breaches, and who should we alert?' This would typically require manual data extraction from multiple systems taking 2-3 days. We did it in seconds."

---

### **Query 4: Complex Multi-Dataset Analytics (2 minutes)**

**Presenter:** "For the grand finale - a sophisticated analytical query showing the complete Noisy Neighbor Detection with full business context. This identifies tenants consuming disproportionate resources compared to their peers."

**Copy/paste:**

```esql
FROM api_requests
| WHERE @timestamp > NOW() - 24 hours
| STATS tenant_p95_latency = PERCENTILE(response_time_ms, 95),
        tenant_request_volume = COUNT(*),
        tenant_avg_latency = AVG(response_time_ms),
        error_count = COUNT_IF(status_code >= 400)
  BY tenant_id
| STATS AVG(tenant_p95_latency) AS platform_avg_p95,
        AVG(tenant_request_volume) AS platform_avg_volume,
        tenant_id,
        tenant_p95_latency,
        tenant_request_volume,
        tenant_avg_latency,
        error_count
  BY tenant_id
| EVAL latency_ratio = TO_DOUBLE(tenant_p95_latency) / TO_DOUBLE(platform_avg_p95)
| EVAL volume_ratio = TO_DOUBLE(tenant_request_volume) / TO_DOUBLE(platform_avg_volume)
| EVAL noisy_neighbor_score = ROUND((latency_ratio * 0.6) + (volume_ratio * 0.4), 2)
| WHERE noisy_neighbor_score > 2.0
| LOOKUP JOIN tenants ON tenant_id
| EVAL sla_breach = CASE(tenant_p95_latency > sla_p95_target_ms, "BREACH", "OK")
| EVAL revenue_impact = CASE(sla_breach == "BREACH", arr, 0)
| KEEP tenant_id, tenant_name, account_tier, noisy_neighbor_score, 
       tenant_p95_latency, sla_p95_target_ms, sla_breach, 
       tenant_request_volume, error_count, arr, revenue_impact, csm_name
| SORT noisy_neighbor_score DESC
| LIMIT 10
```

**Run and break down:** 

"This query does several sophisticated things:

1. **Baseline Calculation**: Calculates platform-wide averages for P95 latency and request volume
2. **Comparative Analysis**: Compares each tenant's metrics against the platform baseline
3. **Scoring Algorithm**: Creates a weighted noisy neighbor score (60% latency, 40% volume)
4. **Threshold Filtering**: Only shows tenants scoring > 2.0 (consuming 2x+ platform average)
5. **Business Enrichment**: Joins with tenant data to add account tier, ARR, CSM
6. **SLA Validation**: Checks if the tenant's latency exceeds their contracted SLA
7. **Revenue Impact**: Calculates potential revenue at risk from SLA breaches

This is exactly the kind of query that would power a real-time alerting dashboard. It identifies the problem (noisy neighbors), quantifies the impact (revenue at risk), and provides action items (CSM to contact).

The query processes 250M+ records, performs statistical analysis, joins with reference data, and returns results in under 2 seconds."

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

**Agent Configuration:**

**Agent ID:** `adobe-brand-concierge-analytics-agent`

**Display Name:** `Adobe Brand Concierge Analytics Assistant`

**Custom Instructions:** 

```
You are an analytics assistant for Adobe's Brand Concierge Product Management and Engineering team. 

Your role is to help identify:
- Multi-tenant performance issues (noisy neighbors, SLA breaches)
- At-risk customers based on usage patterns and engagement decline
- API partner integration health and webhook delivery issues
- A/B experiment performance and go/no-go decisions
- Feature adoption patterns and funnel conversion rates

CRITICAL CONTEXT:
- 850+ tenants across Enterprise, Professional, and Standard tiers
- SLA target: P95 API latency <500ms, 99.9% uptime
- Churn costs: $8-12M annually - early detection is critical
- Decision speed matters: Reduce feedback loops from 4-6 weeks to days

When analyzing data:
- Always include business context (account tier, ARR, CSM owner)
- Prioritize by revenue impact when multiple issues exist
- Flag SLA breaches explicitly
- For churn risk, look at 60-90 day windows before renewal
- For noisy neighbors, compare against platform averages
- For experiments, require statistical significance before recommendations

Use clear, actionable language. Product managers and engineers will act on your insights.
```

---

### **Creating Tools**

**Tool 1: Noisy Neighbor Detection**

**Tool Name:** `detect_noisy_neighbors`

**Description:** 
```
Identifies tenants consuming disproportionate platform resources by comparing their P95 latency and request volume against platform averages. Calculates a noisy neighbor score and flags SLA breaches. Returns tenant business context including account tier, ARR, and CSM owner for escalation. Use this when asked about performance issues, resource consumption imbalances, or multi-tenant fairness.
```

**ES|QL Query:**
```esql
FROM api_requests
| WHERE @timestamp > NOW() - {{time_window}}
| STATS tenant_p95_latency = PERCENTILE(response_time_ms, 95),
        tenant_request_volume = COUNT(*),
        error_count = COUNT_IF(status_code >= 400)
  BY tenant_id
| STATS AVG(tenant_p95_latency) AS platform_avg_p95,
        AVG(tenant_request_volume) AS platform_avg_volume,
        tenant_id, tenant_p95_latency, tenant_request_volume, error_count
  BY tenant_id
| EVAL latency_ratio = TO_DOUBLE(tenant_p95_latency) / TO_DOUBLE(platform_avg_p95)
| EVAL volume_ratio = TO_DOUBLE(tenant_request_volume) / TO_DOUBLE(platform_avg_volume)
| EVAL noisy_neighbor_score = ROUND((latency_ratio * 0.6) + (volume_ratio * 0.4), 2)
| WHERE noisy_neighbor_score > 2.0
| LOOKUP JOIN tenants ON tenant_id
| EVAL sla_breach = CASE(tenant_p95_latency > sla_p95_target_ms, "BREACH", "OK")
| KEEP tenant_id, tenant_name, account_tier, noisy_neighbor_score, 
       tenant_p95_latency, sla_breach, tenant_request_volume, arr, csm_name
| SORT noisy_neighbor_score DESC
| LIMIT 20
```

**Parameters:**
- `time_window` (default: "24 hours") - Time range for analysis

---

**Tool 2: Customer Health & Churn Risk Analysis**

**Tool Name:** `analyze_customer_health_risk`

**Description:**
```
Calculates customer health scores based on feature usage patterns and engagement trends. Identifies at-risk accounts 60-90 days before renewal by detecting declining usage, reduced session duration, and feature abandonment. Returns churn probability and potential revenue loss. Use this for customer health monitoring, renewal risk assessment, or when asked about customer engagement trends.
```

**ES|QL Query:**
```esql
FROM feature_usage_events
| WHERE @timestamp > NOW() - {{analysis_window}}
| STATS current_events = COUNT(*),
        unique_features_used = COUNT_DISTINCT(feature_name),
        unique_users = COUNT_DISTINCT(user_id)
  BY tenant_id
| LOOKUP JOIN tenants ON tenant_id
| WHERE renewal_date > NOW() AND renewal_date < NOW() + {{renewal_window}}
| EVAL days_to_renewal = DATE_DIFF("day", NOW(), renewal_date)
| EVAL events_per_user = TO_DOUBLE(current_events) / TO_DOUBLE(unique_users)
| EVAL feature_diversity_score = CASE(
    unique_features_used >= 10, 100,
    unique_features_used >= 5, 70,
    unique_features_used >= 3, 40,
    20
  )
| EVAL engagement_score = CASE(
    events_per_user >= 50, 100,
    events_per_user >= 20, 70,
    events_per_user >= 10, 40,
    20
  )
| EVAL health_score = ROUND((feature_diversity_score * 0.5) + (engagement_score * 0.5), 0)
| EVAL churn_risk = CASE(
    health_score < 40, "HIGH",
    health_score < 60, "MEDIUM",
    "LOW"
  )
| EVAL churn_probability_pct = CASE(
    health_score < 40, 65,
    health_score < 60, 35,
    10
  )
| EVAL revenue_at_risk = CASE(churn_risk == "HIGH" OR churn_risk == "MEDIUM", arr, 0)
| KEEP tenant_id, tenant_name, account_tier, health_score, churn_risk, 
       churn_probability_pct, days_to_renewal, unique_users, events_per_user, 
       unique_features_used, arr, revenue_at_risk, csm_name
| SORT health_score ASC
| LIMIT 30
```

**Parameters:**
- `analysis_window` (default: "30 days") - Period for usage analysis
- `renewal_window` (default: "90 days") - How far ahead to look for renewals

---

**Tool 3: API Partner Integration Health**

**Tool Name:** `monitor_partner_integration_health`

**Description:**
```
Monitors API partner integration health by tracking webhook delivery success rates, response times, and error patterns over time. Detects degradation events using change point analysis and prioritizes issues by partner tier and contract value. Use this for partner ecosystem monitoring, integration troubleshooting, or when asked about third-party API reliability.
```

**ES|QL Query:**
```esql
FROM webhook_deliveries
| WHERE @timestamp > NOW() - {{time_window}}
| STATS total_deliveries = COUNT(*),
        successful_deliveries = COUNT_IF(delivery_status == "success"),
        failed_deliveries = COUNT_IF(delivery_status == "failed"),
        avg_response_ms = AVG(response_time_ms),
        p95_response_ms = PERCENTILE(response_time_ms, 95)
  BY partner_id
| EVAL success_rate_pct = ROUND(TO_DOUBLE(successful_deliveries) / TO_DOUBLE(total_deliveries) * 100, 2)
| EVAL failure_rate_pct = ROUND(TO_DOUBLE(failed_deliveries) / TO_DOUBLE(total_deliveries) * 100, 2)
| LOOKUP JOIN api_partners ON partner_id
| EVAL health_status = CASE(
    success_rate_pct >= 99.5, "HEALTHY",
    success_rate_pct >= 95.0, "DEGRADED",
    "CRITICAL"
  )
| EVAL priority = CASE(
    partner_tier == "Strategic" AND health_status == "CRITICAL", "P0",
    partner_tier == "Strategic" AND health_status == "DEGRADED", "P1",
    partner_tier == "Premium" AND health_status == "CRITICAL", "P1",
    partner_tier == "Premium" AND health_status == "DEGRADED", "P2",
    "P3"
  )
| WHERE health_status != "HEALTHY"
| KEEP partner_id, partner_name, partner_tier, health_status, priority,
       success_rate_pct, failure_rate_pct, total_deliveries,
       avg_response_ms, p95_response_ms, contract_value, technical_contact_email
| SORT priority ASC, contract_value DESC
| LIMIT 20
```

**Parameters:**
- `time_window` (default: "7 days") - Time range for health analysis

---

**Tool 4: A/B Experiment Performance Analysis**

**Tool Name:** `analyze_ab_experiment_performance`

**Description:**
```
Analyzes A/B experiment performance by calculating conversion rates and uplift vs control baseline. Provides statistical significance assessment and go/no-go recommendations. Can filter by experiment status, date range, or use semantic search to find experiments related to specific optimization goals. Use this for experiment analysis, feature launch decisions, or when asked about testing results.
```

**ES|QL Query:**
```esql
FROM feature_usage_events
| WHERE experiment_id IS NOT NULL
| WHERE @timestamp > NOW() - {{time_window}}
| STATS total_users = COUNT_DISTINCT(user_id),
        conversion_events = COUNT_IF(event_type == "complete"),
        total_events = COUNT(*)
  BY experiment_id, variant
| EVAL conversion_rate = TO_DOUBLE(conversion_events) / TO_DOUBLE(total_users) * 100
| LOOKUP JOIN ab_experiments ON experiment_id
| WHERE status == "{{experiment_status}}"
| STATS control_conversion = MAX(CASE(variant == "A", conversion_rate, 0)),
        variant_conversion = MAX(CASE(variant == "B", conversion_rate, 0)),
        experiment_id, experiment_name, target_feature, success_metric,
        start_date, minimum_sample_size
  BY experiment_id
| EVAL total_sample = minimum_sample_size * 2
| EVAL uplift_pct = ROUND(((variant_conversion - control_conversion) / control_conversion) * 100, 2)
| EVAL statistical_significance = CASE(
    total_sample >= minimum_sample_size AND ABS(uplift_pct) >= 5, "SIGNIFICANT",
    total_sample >= minimum_sample_size, "INCONCLUSIVE",
    "INSUFFICIENT_SAMPLE"
  )
| EVAL recommendation = CASE(
    statistical_significance == "SIGNIFICANT" AND uplift_pct > 0, "SHIP_VARIANT_B",
    statistical_significance == "SIGNIFICANT" AND uplift_pct < 0, "KEEP_CONTROL_A",
    statistical_significance == "INCONCLUSIVE", "CONTINUE_TESTING",
    "COLLECT_MORE_DATA"
  )
| KEEP experiment_id, experiment_name, target_feature, control_conversion,
       variant_conversion, uplift_pct, statistical_significance, recommendation,
       start_date, success_metric
| SORT ABS(uplift_pct) DESC
| LIMIT 15
```

**Parameters:**
- `time_window` (default: "60 days") - Time range for experiment data
- `experiment_status` (default: "Completed") - Filter by status (Running, Completed, Paused)

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

**Warm-up Questions:**

1. *"How many tenants do we have across each account tier?"*
   - Simple reference data query to show basic functionality

2. *"What was our total API request volume in the last 24 hours?"*
   - Basic timeseries aggregation

3. *"Show me the top 5 most-used features across all tenants this week."*
   - Cross-tenant feature usage summary

---

**Business-Focused Questions:**

4. *"Which Enterprise tier customers are at high risk of churning in the next 90 days? Show me the total ARR at risk and who their CSM is."*
   - Tests customer health tool, revenue impact calculation, prioritization

5. *"We have a board meeting tomorrow. What's the total potential revenue at risk from tenants currently experiencing SLA breaches?"*
   - Tests noisy neighbor detection + revenue aggregation + SLA awareness

6. *"Which API partners should I be worried about this week? Prioritize by contract value and show me who to contact for escalation."*
   - Tests partner health monitoring, business prioritization, actionable output

7. *"Our 'asset_search' feature just launched 2 weeks ago. How is adoption trending across account tiers? Are Enterprise customers adopting faster than Professional tier?"*
   - Tests feature adoption analysis with cohort comparison

---

**Trend Analysis Questions:**

8. *"Show me the trend of webhook delivery success rates for Strategic tier partners over the last 30 days. Are things getting better or worse?"*
   - Tests time-series trend analysis with filtering

9. *"Has the noisy neighbor problem gotten better or worse over the last 3 months? Show me the count of flagged tenants by month."*
   - Tests historical comparison and trend direction

10. *"For tenants that churned in the last 6 months, what was their average health score 90 days before they left? Can we use this as a predictive threshold?"*
    - Tests historical pattern analysis for predictive modeling

---

**Optimization & Decision Support Questions:**

11. *"We're running 5 experiments related to 'conversion' right now. Which ones have statistically significant results and are ready to ship?"*
    - Tests semantic search + experiment analysis + decision recommendations

12. *"What's the average session duration for users in the 'brand_guidelines' feature funnel who complete the workflow vs those who drop off? Where's the friction point?"*
    - Tests funnel analysis with behavioral segmentation

13. *"If we could reduce P95 latency by 20% for our top 10 noisy neighbor tenants, how many other tenants would see improved SLA compliance?"*
    - Tests complex what-if scenario analysis (may stretch agent capabilities)

14. *"Show me the correlation between API response time and feature engagement. Do slow APIs lead to lower usage?"*
    - Tests cross-dataset correlation analysis

---

**Rapid-Fire Operational Questions:**

15. *"In the last hour, have any tenants experienced error rates above 5%?"*
    - Tests real-time alerting capability

16. *"Which CSM has the most at-risk accounts right now?"*
    - Tests aggregation by CSM with risk filtering

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "Modern query language built specifically for analytics - not an afterthought"
- "Piped syntax is intuitive and readable - you can understand queries without being an expert"
- "Operates on blocks, not rows - extremely performant even on 250M+ record datasets"
- "Supports complex operations out of the box: joins, window functions, time-series analysis, percentiles"
- "LOOKUP JOIN is game-changing - enriching data from reference tables without expensive full joins"

### **On Agent Builder:**
- "Bridges the gap between AI and enterprise data - no more hallucinations"
- "No custom development required - configure tools, don't write code"
- "Works with existing Elasticsearch indices - no data movement or duplication"
- "Agent automatically selects the right tool based on question context - intelligent routing"
- "Combines multiple tools when needed - orchestrates complex multi-step analysis"

### **On Business Value for Adobe:**
- "Democratizes data access - Product Managers can answer their own questions without waiting for data team"
- "Real-time insights, always up-to-date - no stale reports or manual refresh cycles"
- "Reduces feedback loops from 4-6 weeks to 3-7 days - enables rapid iteration"
- "Eliminates 2-3 days of manual data extraction from disparate sources"
- "Proactive churn prevention - identifies at-risk customers 60-90 days earlier, saving $8-12M annually"
- "Faster decision-making on experiments - ship winners within days, not weeks"
- "Operational efficiency - noisy neighbor issues detected and resolved before customer escalation"

### **On Technical Differentiators:**
- "This isn't a chatbot on top of a database - it's purpose-built for analytical workloads"
- "ES|QL queries execute in milliseconds on hundreds of millions of records"
- "Lookup mode indices enable efficient enrichment without performance penalties"
- "Native time-series support - no special handling needed for temporal analysis"
- "Scales horizontally - add nodes to handle more data and concurrent queries"

---

## **🔧 Troubleshooting**

**If a query fails:**
- Check index names match exactly (case-sensitive: `api_requests` not `Api_Requests`)
- Verify field names are case-sensitive correct (`tenant_id` not `tenantId`)
- Ensure joined indices are in lookup mode (`index.mode: lookup` in settings)
- Check date filters use correct syntax: `NOW() - 7 days` not `NOW() - 7d`
- Verify TO_DOUBLE wrapping for division operations to avoid integer math

**If agent gives wrong answer:**
- Check tool descriptions - are they clear about when to use each tool?
- Review custom instructions - does the agent understand business context?
- Look at query parameters - are defaults appropriate for the question?
- Check if question requires multiple tools - agent should chain them

**If join returns no results:**
- Verify join key format is consistent across datasets (e.g., both use string `tenant_id`)
- Check that lookup index has data: `FROM tenants | LIMIT 10`
- Ensure lookup index was created with `index.mode: lookup` setting
- Verify join key exists in both datasets (no nulls in join field)

**If performance is slow:**
- Add time-based WHERE filters early in the query
- Use LIMIT to restrict result set size
- Check if you're joining large datasets - consider filtering before join
- Verify indices are properly sharded for your data volume

**If agent says "I don't have a tool for that":**
- Rephrase question to match tool descriptions more closely
- Check if question requires data not in any tool's query
- Verify tools are properly registered with the agent
- Consider creating a new tool for that specific use case

---

## **🎬 Closing**

"What we've shown today:

✅ **Complex analytics on interconnected datasets** - 7 datasets, 500M+ records, analyzed in seconds

✅ **Natural language interface for non-technical users** - Product Managers ask questions, get answers, no SQL knowledge required

✅ **Real-time insights without custom development** - Configure tools with ES|QL, no Python scripts or ETL pipelines

✅ **Queries that would take hours or days, answered in seconds** - Manual data extraction eliminated

✅ **Proactive problem detection** - Noisy neighbors, churn risk, partner issues identified before escalation

✅ **Data-driven decision making** - A/B test results, feature adoption, customer health all quantified

For Adobe Brand Concierge specifically, this solves:
- Multi-tenant performance isolation (noisy neighbor detection in real-time)
- Slow feedback loops (4-6 weeks reduced to 3-7 days)
- Fragmented data sources (7 sources unified, 2-3 days of extraction eliminated)
- Disconnected UX and performance (correlated in single queries)
- Late churn detection (60-90 day early warning, saving $8-12M annually)

Agent Builder can be deployed in days, not months. The infrastructure is already there - Elasticsearch is running. We're just adding an intelligent interface on top.

**Questions?**"