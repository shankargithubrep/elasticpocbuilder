from src.framework.base import DemoGuideModule, DemoConfig
from typing import Dict, List, Any, Optional
import pandas as pd

class TMobileUSAIncDemoGuide(DemoGuideModule):
    """Demo guide for T-Mobile USA, Inc. - Network Operations Center (NOC) / Radio Access Network Engineering"""

    def __init__(self, config: DemoConfig, datasets: Dict[str, pd.DataFrame],
                 queries: List[Dict], aha_moment: Optional[Dict] = None):
        """Initialize with demo context"""
        super().__init__(config, datasets, queries, aha_moment)

    def generate_guide(self) -> str:
        """Generate customized demo guide"""
        return '''# **Elastic Agent Builder Demo for T-Mobile USA, Inc.**

## **Internal Demo Script & Reference Guide**

---

## **📋 Demo Overview**

**Total Time:** 25-30 minutes
**Audience:** Network Operations Center (NOC) / Radio Access Network Engineering technical/business stakeholders
**Goal:** Show how Agent Builder enables AI-powered analytics on T-Mobile USA, Inc. mobile network telemetry and signaling data

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## **🗂️ Dataset Architecture**

### **mme_signaling_events** (Timeseries Index)
**Record Count:** 500,000 records
**Purpose:** Real-time MME (Mobility Management Entity) signaling events capturing NAS messages, handoff attempts, authentication requests, and attach/detach procedures

**Primary Key:** `event_id` (unique event identifier)

**Key Fields:**
- `@timestamp` - Event timestamp (ISO 8601)
- `event_id` - Unique event identifier
- `mme_host` - MME hostname processing the event
- `imsi` - International Mobile Subscriber Identity (subscriber identifier)
- `event_type` - Type of signaling event (ATTACH_REQUEST, HANDOFF_REQUEST, TAU_REQUEST, DETACH_REQUEST, etc.)
- `result_code` - Event outcome (SUCCESS, TIMEOUT, REJECTED, NETWORK_FAILURE)
- `cell_id` - Serving cell identifier
- `target_cell_id` - Target cell for handoff events
- `processing_latency_ms` - NAS message processing time in milliseconds
- `mme_cpu_percent` - CPU utilization at event time
- `mme_memory_percent` - Memory utilization at event time
- `sctp_association_id` - SCTP association identifier

**Relationships:**
- `mme_host` → joins to `mme_hosts.hostname`
- `cell_id` → joins to `cell_sites.cell_id`
- `imsi` → joins to `subscriber_profiles.imsi`

---

### **mme_hosts** (Reference/Lookup Index)
**Record Count:** 50 records
**Purpose:** MME infrastructure metadata including cluster assignments, capacity ratings, and geographic locations

**Primary Key:** `hostname`

**Key Fields:**
- `hostname` - MME server hostname (e.g., mme-west-01.tmobile.net)
- `cluster_name` - MME cluster identifier (e.g., WEST_CLUSTER_1)
- `datacenter` - Geographic datacenter location (e.g., Seattle, Dallas, Atlanta)
- `max_subscriber_capacity` - Maximum concurrent subscriber capacity
- `software_version` - MME software version
- `deployment_date` - Date deployed to production
- `redundancy_pair` - Paired MME for failover

**Index Mode:** `lookup` (required for LOOKUP JOIN operations)

---

### **cell_sites** (Reference/Lookup Index)
**Record Count:** 500 records
**Purpose:** Cell tower and site metadata including geographic coordinates, technology types, and adjacent cell relationships

**Primary Key:** `cell_id`

**Key Fields:**
- `cell_id` - Unique cell identifier
- `site_name` - Human-readable site name
- `latitude` - Geographic latitude
- `longitude` - Geographic longitude
- `technology` - Radio technology (LTE, 5G_NSA, 5G_SA)
- `frequency_band` - Operating frequency band (e.g., Band_71, n41)
- `azimuth` - Antenna azimuth direction
- `neighbor_cell_ids` - Comma-separated list of adjacent cells
- `market` - Market/region identifier
- `site_type` - Site classification (MACRO, SMALL_CELL, INDOOR)

**Index Mode:** `lookup` (required for LOOKUP JOIN operations)

---

### **subscriber_profiles** (Reference/Lookup Index)
**Record Count:** 10,000 records
**Purpose:** Subscriber account information including plan types, device information, and account status

**Primary Key:** `imsi`

**Key Fields:**
- `imsi` - International Mobile Subscriber Identity
- `msisdn` - Phone number
- `account_type` - Account classification (POSTPAID, PREPAID, ENTERPRISE)
- `plan_name` - Service plan name
- `device_model` - Current device model
- `account_status` - Active, Suspended, Terminated
- `home_market` - Primary market/region
- `roaming_enabled` - Boolean flag for roaming capability
- `data_plan_gb` - Data plan allowance in GB

**Index Mode:** `lookup` (required for LOOKUP JOIN operations)

---

### **ss7_diameter_events** (Timeseries Index)
**Record Count:** 200,000 records
**Purpose:** SS7 and Diameter signaling protocol events for security monitoring and roaming fraud detection

**Primary Key:** `event_id`

**Key Fields:**
- `@timestamp` - Event timestamp
- `event_id` - Unique event identifier
- `protocol` - Protocol type (SS7_MAP, DIAMETER)
- `message_type` - Specific message type (SEND_ROUTING_INFO, UPDATE_LOCATION, INSERT_SUBSCRIBER_DATA)
- `imsi` - Subscriber IMSI
- `originating_gt` - Originating Global Title (network identifier)
- `destination_gt` - Destination Global Title
- `result_code` - Message result code
- `roaming_country` - Country code for roaming events
- `message_sequence_id` - Sequence identifier for correlation
- `suspicious_flag` - Boolean flag for anomaly detection
- `risk_score` - Calculated risk score (0-100)

**Relationships:**
- `imsi` → joins to `subscriber_profiles.imsi`

---

## **🚀 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

**CRITICAL: All reference indexes need "index.mode": "lookup" for joins to work**

---

#### **Upload mme_signaling_events (Timeseries)**

1. Navigate to **Kibana → Management → Dev Tools**
2. Create the index with timeseries mapping:

```json
PUT mme_signaling_events
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "event_id": { "type": "keyword" },
      "mme_host": { "type": "keyword" },
      "imsi": { "type": "keyword" },
      "event_type": { "type": "keyword" },
      "result_code": { "type": "keyword" },
      "cell_id": { "type": "keyword" },
      "target_cell_id": { "type": "keyword" },
      "processing_latency_ms": { "type": "float" },
      "mme_cpu_percent": { "type": "float" },
      "mme_memory_percent": { "type": "float" },
      "sctp_association_id": { "type": "keyword" }
    }
  }
}
```

3. Navigate to **Kibana → Management → Integrations → Upload a file**
4. Upload `mme_signaling_events.csv`
5. Map fields to match the schema above
6. Import into `mme_signaling_events` index

---

#### **Upload mme_hosts (Lookup Index)**

1. In Dev Tools, create lookup index:

```json
PUT mme_hosts
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "hostname": { "type": "keyword" },
      "cluster_name": { "type": "keyword" },
      "datacenter": { "type": "keyword" },
      "max_subscriber_capacity": { "type": "integer" },
      "software_version": { "type": "keyword" },
      "deployment_date": { "type": "date" },
      "redundancy_pair": { "type": "keyword" }
    }
  }
}
```

2. Upload `mme_hosts.csv` via file upload
3. Import into `mme_hosts` index

---

#### **Upload cell_sites (Lookup Index)**

1. Create lookup index:

```json
PUT cell_sites
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "cell_id": { "type": "keyword" },
      "site_name": { "type": "text" },
      "latitude": { "type": "float" },
      "longitude": { "type": "float" },
      "technology": { "type": "keyword" },
      "frequency_band": { "type": "keyword" },
      "azimuth": { "type": "integer" },
      "neighbor_cell_ids": { "type": "keyword" },
      "market": { "type": "keyword" },
      "site_type": { "type": "keyword" }
    }
  }
}
```

2. Upload `cell_sites.csv` and import

---

#### **Upload subscriber_profiles (Lookup Index)**

1. Create lookup index:

```json
PUT subscriber_profiles
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "imsi": { "type": "keyword" },
      "msisdn": { "type": "keyword" },
      "account_type": { "type": "keyword" },
      "plan_name": { "type": "keyword" },
      "device_model": { "type": "keyword" },
      "account_status": { "type": "keyword" },
      "home_market": { "type": "keyword" },
      "roaming_enabled": { "type": "boolean" },
      "data_plan_gb": { "type": "integer" }
    }
  }
}
```

2. Upload `subscriber_profiles.csv` and import

---

#### **Upload ss7_diameter_events (Timeseries)**

1. Create timeseries index:

```json
PUT ss7_diameter_events
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "event_id": { "type": "keyword" },
      "protocol": { "type": "keyword" },
      "message_type": { "type": "keyword" },
      "imsi": { "type": "keyword" },
      "originating_gt": { "type": "keyword" },
      "destination_gt": { "type": "keyword" },
      "result_code": { "type": "keyword" },
      "roaming_country": { "type": "keyword" },
      "message_sequence_id": { "type": "keyword" },
      "suspicious_flag": { "type": "boolean" },
      "risk_score": { "type": "float" }
    }
  }
}
```

2. Upload `ss7_diameter_events.csv` and import

---

### **Step 2: Verify Data Load**

Run quick verification queries in Dev Tools:

```esql
FROM mme_signaling_events
| STATS event_count = COUNT(*) BY event_type
| SORT event_count DESC
| LIMIT 5
```

```esql
FROM mme_hosts
| STATS host_count = COUNT(*) BY datacenter
```

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to your AI Agent chat interface
- Have the agent already configured with all tools

### **Demo Script**

**Presenter:** "Before we dive into how this works, let me show you the end result. I'm going to ask our AI agent complex network operations questions that would normally require a data analyst to write SQL queries and join multiple systems."

**Sample questions to demonstrate:**

---

**Question 1: ROI / Business Impact**
> "Show me the top 5 cell sites with the highest handoff failure rates in the last 24 hours, and estimate how many subscribers were impacted. Include the estimated revenue impact if each failed session costs us $0.15 in customer satisfaction."

**What this shows:** Multi-dataset join (events + cell sites + subscriber profiles), business calculations, revenue impact analysis

---

**Question 2: Proactive Issue Detection**
> "Which MME hosts are showing signs of resource exhaustion? Look for hosts where CPU or memory utilization is above 85% AND processing latency has increased by more than 50% compared to their 7-day average."

**What this shows:** Statistical analysis, time-based comparisons, threshold detection, predictive alerting

---

**Question 3: Security / Fraud Detection**
> "Identify any SS7 signaling patterns that look like location tracking attacks. Show me IMSIs that received more than 10 SEND_ROUTING_INFO requests from different originating networks within a 1-hour window."

**What this shows:** Security analytics, pattern detection, behavioral analysis, cross-protocol correlation

---

**Question 4: Cascade Failure Analysis**
> "Analyze handoff failures between adjacent cells in the Seattle market. Show me cell pairs where handoff failures increased by more than 200% in the last 4 hours, and identify if failures are propagating through neighbor cell chains."

**What this shows:** Graph-style analysis, geographic filtering, propagation detection, neighbor relationship traversal

---

**Question 5: Subscriber Experience Correlation**
> "How many enterprise account subscribers experienced authentication failures in the last hour? Break it down by MME cluster and show me if there's a correlation with specific software versions."

**What this shows:** Multi-dimensional grouping, subscriber segmentation, infrastructure correlation

---

**Question 6: Capacity Planning**
> "Which MME clusters are operating above 80% of their maximum subscriber capacity? Show current load, capacity headroom, and predict when they'll hit 95% capacity if growth continues at the current 7-day trend."

**What this shows:** Capacity analysis, trend projection, infrastructure planning

---

**Question 7: Split-Brain Detection**
> "Are there any subscribers being processed by multiple MME hosts in the same cluster simultaneously? This could indicate a split-brain scenario. Show me the IMSI, both MME hosts, and the SCTP association IDs."

**What this shows:** Distributed systems failure detection, conflict identification, real-time anomaly detection

---

**Transition:** "Pretty powerful, right? These answers came back in seconds, pulling data from five different datasets, doing complex joins, statistical analysis, and business calculations. So how does this actually work? Let's go under the hood and build these queries from scratch using ES|QL."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open Kibana Dev Tools Console
- Have the indices already created and populated

---

### **Query 1: Simple Aggregation (2 minutes)**

**Presenter:** "T-Mobile's NOC wants to know: What are the most common types of signaling failures happening right now, and which MME hosts are generating them?"

**Copy/paste into console:**

```esql
FROM mme_signaling_events
| WHERE result_code != "SUCCESS" AND @timestamp > NOW() - 1 hour
| STATS failure_count = COUNT(*) BY event_type, mme_host
| SORT failure_count DESC
| LIMIT 20
```

**Run and narrate results:** "This is basic ES|QL:
- FROM: Source our MME signaling events
- WHERE: Filter to failures in the last hour
- STATS: Aggregate failure counts, grouped by event type and MME host
- SORT and LIMIT: Top 20 failure combinations

The syntax is intuitive - it reads like English. Already we can see which MME hosts and event types are problematic."

---

### **Query 2: Add Calculations with EVAL (3 minutes)**

**Presenter:** "Let's add calculations to understand the severity. We'll calculate failure rates and identify MME hosts with degraded performance."

**Copy/paste:**

```esql
FROM mme_signaling_events
| WHERE @timestamp > NOW() - 1 hour
| STATS 
    total_events = COUNT(*),
    failed_events = COUNT(*) WHERE result_code != "SUCCESS",
    avg_latency = AVG(processing_latency_ms),
    avg_cpu = AVG(mme_cpu_percent),
    avg_memory = AVG(mme_memory_percent)
  BY mme_host
| EVAL failure_rate = TO_DOUBLE(failed_events) / TO_DOUBLE(total_events) * 100
| EVAL health_score = 100 - (failure_rate + (avg_cpu / 10) + (avg_memory / 10))
| WHERE failure_rate > 5 OR avg_cpu > 80 OR avg_memory > 80
| SORT health_score ASC
| LIMIT 15
```

**Run and highlight:** "Key additions:
- EVAL: Creates calculated fields on-the-fly (failure_rate, health_score)
- TO_DOUBLE: Critical for decimal division - avoids integer rounding
- Multiple STATS: Aggregating multiple metrics simultaneously
- Conditional filtering: WHERE clause after aggregation
- Business-relevant calculations: health_score combines multiple factors

Now we can see which MME hosts are truly unhealthy, not just busy."

---

### **Query 3: Join Datasets with LOOKUP JOIN (3 minutes)**

**Presenter:** "Now let's combine data from multiple sources. We'll enrich signaling events with MME infrastructure metadata to understand which datacenters and clusters are having issues."

**Copy/paste:**

```esql
FROM mme_signaling_events
| WHERE result_code != "SUCCESS" AND @timestamp > NOW() - 2 hours
| STATS 
    failure_count = COUNT(*),
    unique_subscribers = COUNT_DISTINCT(imsi),
    avg_latency = AVG(processing_latency_ms)
  BY mme_host
| LOOKUP JOIN mme_hosts ON mme_host = hostname
| EVAL capacity_utilization = TO_DOUBLE(unique_subscribers) / TO_DOUBLE(max_subscriber_capacity) * 100
| EVAL failures_per_subscriber = TO_DOUBLE(failure_count) / TO_DOUBLE(unique_subscribers)
| SORT failure_count DESC
| LIMIT 20
```

**Run and explain:** "Magic happening here:
- LOOKUP JOIN: Combines mme_signaling_events with mme_hosts using hostname as the join key
- Now we have access to datacenter, cluster_name, max_subscriber_capacity from the mme_hosts dataset
- This is a LEFT JOIN: All MME hosts kept, enriched with infrastructure metadata
- For LOOKUP JOIN to work, mme_hosts must have 'index.mode: lookup' (which we set during setup)
- We can now calculate capacity_utilization because we have max_subscriber_capacity

This gives us infrastructure context for every failure - essential for root cause analysis."

---

### **Query 4: Complex Multi-Dataset Analytics (2 minutes)**

**Presenter:** "For the grand finale - a sophisticated analytical query showing handoff cascade failure analysis. This identifies when handoff failures are propagating through adjacent cells, a critical pattern that can indicate cell tower misconfigurations or RF interference."

**Copy/paste:**

```esql
FROM mme_signaling_events
| WHERE event_type == "HANDOFF_REQUEST" 
    AND result_code != "SUCCESS" 
    AND @timestamp > NOW() - 4 hours
| STATS 
    handoff_failures = COUNT(*),
    unique_subscribers = COUNT_DISTINCT(imsi),
    avg_latency = AVG(processing_latency_ms)
  BY cell_id, target_cell_id
| WHERE handoff_failures > 10
| LOOKUP JOIN cell_sites AS source_cell ON cell_id = source_cell.cell_id
| LOOKUP JOIN cell_sites AS target_cell ON target_cell_id = target_cell.cell_id
| EVAL same_market = CASE(source_cell.market == target_cell.market, "YES", "NO")
| EVAL technology_mismatch = CASE(
    source_cell.technology != target_cell.technology, 
    CONCAT(source_cell.technology, "->", target_cell.technology),
    "SAME"
  )
| EVAL failure_severity = CASE(
    handoff_failures > 100, "CRITICAL",
    handoff_failures > 50, "HIGH",
    handoff_failures > 20, "MEDIUM",
    "LOW"
  )
| WHERE same_market == "YES"
| STATS 
    total_failures = SUM(handoff_failures),
    affected_subscribers = SUM(unique_subscribers),
    cell_pair_count = COUNT(*)
  BY source_cell.market, technology_mismatch, failure_severity
| SORT total_failures DESC
| LIMIT 25
```

**Run and break down:** 

"This query demonstrates enterprise-grade analytics:

**Multi-dataset joins:** We're joining mme_signaling_events with cell_sites TWICE - once for source cell, once for target cell. This gives us full metadata for both ends of the handoff.

**Advanced EVAL logic:** 
- same_market: Identifies if handoffs are staying within the same geographic market
- technology_mismatch: Detects LTE-to-5G or 5G-to-LTE handoffs which have higher failure rates
- failure_severity: Categorizes severity based on failure volume

**Hierarchical aggregation:** We first aggregate at the cell-pair level, then re-aggregate by market and technology to see patterns.

**Real-world insights:** This query answers: 'Where are handoff cascade failures happening? Is it technology transitions? Is it cross-market handoffs? How many subscribers are affected?'

This is the kind of analysis that would take hours in traditional SQL with multiple CTEs. In ES|QL, it's 25 lines and runs in seconds."

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

**Presenter:** "Now let's wire this up to an AI agent. In Agent Builder, we define tools - each tool is essentially an ES|QL query template that the agent can invoke."

---

**Agent Configuration:**

**Agent ID:** `tmobile-noc-network-analyst`

**Display Name:** `T-Mobile NOC Network Analyst`

**Custom Instructions:** 
```
You are an expert network operations analyst for T-Mobile's Radio Access Network and Core Network infrastructure. You have access to real-time signaling data from MME hosts, cell tower telemetry, subscriber profiles, and SS7/Diameter security events.

When analyzing network issues:
1. Always consider subscriber impact - quantify affected IMSIs when possible
2. Correlate infrastructure health (CPU, memory, latency) with service failures
3. Look for patterns across adjacent cells for cascade failures
4. Consider time-based trends - compare current metrics to historical baselines
5. Flag security anomalies in SS7/Diameter signaling patterns
6. Provide actionable recommendations with specific MME hosts, cell IDs, or clusters

For capacity questions, use max_subscriber_capacity from mme_hosts dataset.
For geographic analysis, use latitude/longitude and market fields from cell_sites.
For subscriber segmentation, use account_type and plan_name from subscriber_profiles.

Always format results in clear tables with relevant metrics. When showing failure rates, include both counts and percentages.
```

---

### **Creating Tools**

**Tool 1: MME Resource Exhaustion Detector**

**Tool Name:** `detect_mme_resource_exhaustion`

**Description:** 
```
Identifies MME hosts showing signs of resource exhaustion by analyzing CPU/memory utilization combined with NAS message processing latency degradation. Detects memory leaks and CPU exhaustion before they trigger failover events. Use this when asked about MME health, performance degradation, or proactive failure detection.
```

**ES|QL Query:**
```esql
FROM mme_signaling_events
| WHERE @timestamp > NOW() - {time_window}
| STATS 
    event_count = COUNT(*),
    avg_cpu = AVG(mme_cpu_percent),
    p95_cpu = PERCENTILE(mme_cpu_percent, 95),
    avg_memory = AVG(mme_memory_percent),
    p95_memory = PERCENTILE(mme_memory_percent, 95),
    avg_latency = AVG(processing_latency_ms),
    p95_latency = PERCENTILE(processing_latency_ms, 95),
    failure_rate = COUNT(*) WHERE result_code != "SUCCESS" / COUNT(*) * 100
  BY mme_host
| LOOKUP JOIN mme_hosts ON mme_host = hostname
| EVAL health_score = 100 - (avg_cpu + avg_memory) / 2
| EVAL latency_degraded = CASE(p95_latency > 500, "YES", "NO")
| WHERE p95_cpu > 85 OR p95_memory > 85 OR p95_latency > 500
| SORT health_score ASC
```

**Parameters:**
- `time_window` (default: "1h") - Time range to analyze

---

**Tool 2: Handoff Cascade Failure Analyzer**

**Tool Name:** `analyze_handoff_cascade_failures`

**Description:**
```
Identifies handoff cascade failures by analyzing failure patterns across adjacent cell pairs. Detects when failures propagate through neighbor cells and categorizes root causes to pinpoint problematic cell tower configurations. Use this for investigating dropped calls, mobility issues, or cell tower problems.
```

**ES|QL Query:**
```esql
FROM mme_signaling_events
| WHERE event_type == "HANDOFF_REQUEST" 
    AND result_code != "SUCCESS"
    AND @timestamp > NOW() - {time_window}
| STATS 
    failure_count = COUNT(*),
    unique_imsis = COUNT_DISTINCT(imsi)
  BY cell_id, target_cell_id
| WHERE failure_count > {min_failures}
| LOOKUP JOIN cell_sites AS source ON cell_id = source.cell_id
| LOOKUP JOIN cell_sites AS target ON target_cell_id = target.cell_id
| EVAL tech_transition = CONCAT(source.technology, " -> ", target.technology)
| EVAL same_market = CASE(source.market == target.market, "YES", "NO")
| SORT failure_count DESC
| LIMIT {result_limit}
```

**Parameters:**
- `time_window` (default: "4h")
- `min_failures` (default: 10)
- `result_limit` (default: 50)

---

**Tool 3: SS7 Security Attack Detector**

**Tool Name:** `detect_ss7_signaling_attacks`

**Description:**
```
Detects SS7/Diameter signaling attacks through semantic pattern matching of suspicious message sequences combined with subscriber behavioral analysis. Identifies location tracking attempts, SMS interception, and fraudulent roaming before financial impact. Use for security investigations or fraud detection.
```

**ES|QL Query:**
```esql
FROM ss7_diameter_events
| WHERE @timestamp > NOW() - {time_window}
    AND (suspicious_flag == true OR risk_score > {risk_threshold})
| STATS 
    event_count = COUNT(*),
    unique_originators = COUNT_DISTINCT(originating_gt),
    avg_risk_score = AVG(risk_score),
    max_risk_score = MAX(risk_score)
  BY imsi, message_type, protocol
| WHERE event_count > {min_events}
| LOOKUP JOIN subscriber_profiles ON imsi = imsi
| EVAL attack_pattern = CASE(
    message_type == "SEND_ROUTING_INFO" AND event_count > 10, "LOCATION_TRACKING",
    message_type == "INSERT_SUBSCRIBER_DATA" AND unique_originators > 3, "SUBSCRIBER_MANIPULATION",
    roaming_country != home_market AND event_count > 20, "ROAMING_FRAUD",
    "SUSPICIOUS_ACTIVITY"
  )
| SORT max_risk_score DESC
| LIMIT {result_limit}
```

**Parameters:**
- `time_window` (default: "1h")
- `risk_threshold` (default: 70)
- `min_events` (default: 5)
- `result_limit` (default: 100)

---

**Tool 4: Subscriber Impact Correlator**

**Tool Name:** `correlate_subscriber_impact`

**Description:**
```
Detects subscriber-impacting incidents 5-15 minutes before help desk call spikes by identifying clusters with 500+ unique IMSIs experiencing service failures within time windows. Uses adaptive percentile-based thresholds for proactive alerting. Use when asked about subscriber impact, service outages, or proactive incident detection.
```

**ES|QL Query:**
```esql
FROM mme_signaling_events
| WHERE @timestamp > NOW() - {time_window}
    AND result_code != "SUCCESS"
| STATS 
    failure_count = COUNT(*),
    unique_subscribers = COUNT_DISTINCT(imsi),
    failure_types = COUNT_DISTINCT(event_type)
  BY mme_host, BUCKET(@timestamp, {bucket_interval})
| LOOKUP JOIN mme_hosts ON mme_host = hostname
| WHERE unique_subscribers > {subscriber_threshold}
| EVAL incident_severity = CASE(
    unique_subscribers > 1000, "CRITICAL",
    unique_subscribers > 500, "HIGH",
    "MEDIUM"
  )
| EVAL estimated_revenue_impact = unique_subscribers * {revenue_per_failure}
| SORT unique_subscribers DESC
| LIMIT {result_limit}
```

**Parameters:**
- `time_window` (default: "15m")
- `bucket_interval` (default: "5m")
- `subscriber_threshold` (default: 500)
- `revenue_per_failure` (default: 0.15)
- `result_limit` (default: 50)

---

**Presenter:** "Notice how each tool is purpose-built for a specific analytical question. The agent reads the tool descriptions and automatically selects the right tool based on the user's question. The parameters allow flexibility - users can ask for different time ranges or thresholds, and the agent fills them in."

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

**Presenter:** "Now for the fun part. Let's interact with the agent using natural language. I'll ask progressively more complex questions."

---

### **Warm-up Questions**

**Q1:** "How many signaling events have we processed in the last hour?"

**What this tests:** Basic aggregation, single dataset query

---

**Q2:** "Which MME host has the highest CPU utilization right now?"

**What this tests:** Filtering, sorting, real-time metrics

---

**Q3:** "Show me the top 10 cell sites by handoff failure count in the last 4 hours."

**What this tests:** Event type filtering, cell site aggregation

---

### **Business-Focused Questions**

**Q4:** "How many enterprise account subscribers experienced authentication failures in the last 2 hours? What's the estimated revenue impact if each failure costs us $0.25?"

**What this tests:** Multi-dataset join (events + subscriber_profiles), subscriber segmentation, business calculations

**Expected behavior:** Agent should use subscriber_profiles to filter account_type == "ENTERPRISE", count failures, multiply by revenue factor

---

**Q5:** "Which MME clusters are operating above 75% of their maximum subscriber capacity right now? Show me current load, capacity headroom in subscribers, and the datacenter location."

**What this tests:** Capacity analysis, infrastructure joins, threshold detection

**Expected behavior:** Join events to mme_hosts, calculate current unique IMSIs vs max_subscriber_capacity, filter by threshold

---

**Q6:** "Are there any cell sites in the Seattle market where handoff failures increased by more than 100% compared to yesterday? Show me the cell IDs, site names, and technology types."

**What this tests:** Time-based comparison, geographic filtering, percentage change calculation

**Expected behavior:** Compare current period to 24h ago, filter by market, calculate percentage increase

---

### **Trend Analysis Questions**

**Q7:** "Show me the hourly trend of authentication failures for the last 24 hours, broken down by MME cluster. Highlight any clusters with unusual spikes."

**What this tests:** Time bucketing, trend visualization, anomaly detection

**Expected behavior:** BUCKET(@timestamp, 1h), group by cluster_name, identify spikes above baseline

---

**Q8:** "Which MME hosts show increasing processing latency over the last 6 hours? Calculate the rate of latency increase per hour."

**What this tests:** Time-series analysis, rate of change calculation, degradation detection

**Expected behavior:** Time-bucketed latency averages, linear trend calculation

---

### **Advanced Correlation Questions**

**Q9:** "Find subscribers who experienced both handoff failures AND authentication failures in the last hour. Show me their account types and device models."

**What this tests:** Multi-event correlation by IMSI, complex filtering, subscriber enrichment

**Expected behavior:** Self-join or multiple aggregations on mme_signaling_events filtered by event_type, join to subscriber_profiles

---

**Q10:** "Are there any SS7 signaling attacks targeting our enterprise subscribers? Look for suspicious patterns like excessive SEND_ROUTING_INFO requests."

**What this tests:** Security analytics, cross-dataset correlation (ss7_diameter_events + subscriber_profiles), pattern detection

**Expected behavior:** Filter ss7_diameter_events for suspicious patterns, join to subscriber_profiles, identify enterprise accounts

---

**Q11:** "Identify any potential split-brain scenarios where the same subscriber is being processed by multiple MME hosts in the same cluster within a 5-minute window."

**What this tests:** Distributed systems failure detection, temporal correlation, cluster-aware analysis

**Expected behavior:** Group events by IMSI and time bucket, count distinct mme_hosts, filter where count > 1, verify same cluster

---

**Q12:** "Which cell tower pairs have the worst handoff success rates, and are they neighbors according to the neighbor_cell_ids field? This could indicate RF interference or misconfiguration."

**What this tests:** Graph-style relationship analysis, neighbor validation, root cause hypothesis

**Expected behavior:** Aggregate handoff failures by cell pair, join to cell_sites, check if target_cell_id appears in source cell's neighbor_cell_ids

---

### **Optimization Questions**

**Q13:** "If we wanted to reduce handoff failures by 20%, which 5 cell sites should we prioritize for optimization based on subscriber impact?"

**What this tests:** Impact-based prioritization, subscriber correlation, optimization recommendations

**Expected behavior:** Calculate failures per cell, multiply by unique IMSIs affected, rank by total subscriber-impact score

---

**Q14:** "Show me MME hosts that are underutilized (below 40% capacity) and could potentially take load from overloaded hosts in the same datacenter."

**What this tests:** Capacity balancing, datacenter-aware analysis, load distribution recommendations

**Expected behavior:** Calculate utilization per MME, filter by datacenter, identify underutilized hosts near overloaded ones

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "Modern query language designed specifically for analytics - not an afterthought"
- "Piped syntax is intuitive and readable - business users can understand these queries"
- "Operates on blocks, not rows - extremely performant even on 500k+ record datasets"
- "Supports complex operations out of the box: joins, window functions, time-series bucketing, statistical functions"
- "LOOKUP JOIN enables true data enrichment without expensive index-time joins"

### **On Agent Builder:**
- "Bridges the gap between AI and enterprise data - no custom API development required"
- "Configure, don't code - tools are ES|QL queries with descriptions, not Python scripts"
- "Works with existing Elasticsearch indices - no data movement or ETL pipelines"
- "Agent automatically selects the right tool based on natural language intent"
- "Parameters allow flexibility - users can specify time ranges, thresholds without knowing query syntax"
- "Built on Elastic's security model - respects index permissions and field-level security"

### **On Business Value for T-Mobile:**
- "Democratizes network analytics - NOC engineers don't need to wait for data team to write queries"
- "Real-time insights on live data - always up-to-date, no stale reports"
- "Proactive issue detection - identify problems 5-15 minutes before subscriber impact"
- "Reduces MTTR (Mean Time To Resolution) - analysts can explore data conversationally during incidents"
- "Cross-domain correlation - connects signaling events, infrastructure health, subscriber data, and security events in one query"
- "Scales with T-Mobile's data volume - ES|QL performance doesn't degrade with dataset size"

### **Specific T-Mobile Use Case Value:**
- "Handoff cascade failure detection prevents widespread service degradation - catching one misconfigured cell before it impacts thousands"
- "MME resource exhaustion prediction prevents failover events - proactive intervention saves customer experience"
- "SS7 attack detection protects subscriber privacy and prevents roaming fraud - measurable cost savings"
- "Subscriber impact correlation enables targeted customer outreach - 'We're aware of the issue in your area' instead of reactive support"

---

## **🔧 Troubleshooting**

### **If a query fails:**

**Error: "Unknown index [mme_hosts]"**
- Check index names match exactly (case-sensitive)
- Verify indices were created successfully with `GET _cat/indices?v`

**Error: "Field [hostname] not found"**
- Verify field names are case-sensitive correct
- Check mapping with `GET mme_hosts/_mapping`

**Error: "LOOKUP JOIN requires lookup index mode"**
- Ensure reference indices (mme_hosts, cell_sites, subscriber_profiles) have `"index.mode": "lookup"` in settings
- Check with `GET mme_hosts/_settings`
- If missing, recreate index with correct settings

**Error: "Cannot join on field [mme_host] - type mismatch"**
- Verify join key fields have same data type in both indices (both should be `keyword`)
- Check with `GET mme_signaling_events/_mapping` and `GET mme_hosts/_mapping`

---

### **If agent gives wrong answer:**

**Agent selects wrong tool:**
- Review tool descriptions - are they clear about when to use each tool?
- Check if tool descriptions overlap - make them more distinct
- Add explicit keywords to tool descriptions that match user question patterns

**Agent doesn't fill parameters correctly:**
- Verify parameter descriptions in tool configuration
- Check if default values are reasonable
- Test tool manually with expected parameter values

**Agent returns incomplete results:**
- Check LIMIT clauses in queries - may be too restrictive
- Verify WHERE filters aren't excluding relevant data
- Test underlying ES|QL query directly in Dev Tools

---

### **If join returns no results:**

**LOOKUP JOIN produces empty results:**
- Verify join key format is consistent across datasets (e.g., both use "mme-west-01" not "mme-west-01.tmobile.net")
- Check that lookup index actually has data: `FROM mme_hosts | LIMIT 10`
- Verify join key values exist in both datasets - sample a few keys from each side
- Ensure no leading/trailing whitespace in join keys

**Performance issues with large joins:**
- Lookup indices should be relatively small (< 100k records)
- Consider filtering before joining to reduce dataset size
- Check if indices are properly sharded for your cluster size

---

### **Data quality issues:**

**Unexpected null values:**
- Check CSV import mapping - ensure fields weren't skipped
- Verify data types match expectations (dates as dates, numbers as numbers)
- Use `| WHERE field IS NOT NULL` to filter incomplete records

**Timestamp parsing errors:**
- Ensure @timestamp field is in ISO 8601 format (YYYY-MM-DDTHH:mm:ss.sssZ)
- Check timezone handling - all timestamps should be UTC
- Verify date math expressions like `NOW() - 1h` work correctly

---

## **🎬 Closing**

**Presenter:** "So let's recap what we've demonstrated today:

✅ **Complex analytics on interconnected datasets** - We joined MME signaling events, infrastructure metadata, cell tower information, subscriber profiles, and security events seamlessly

✅ **Natural language interface for non-technical users** - NOC engineers can ask business questions without knowing ES|QL syntax

✅ **Real-time insights without custom development** - No APIs to build, no ETL pipelines to maintain, no dashboards to update manually

✅ **Queries that would take hours, answered in seconds** - Multi-dataset joins with statistical analysis executing in sub-second response times

✅ **Proactive issue detection** - Identify MME resource exhaustion, handoff cascade failures, and security attacks before subscriber impact

✅ **Scalable to T-Mobile's data volumes** - ES|QL performance on 500k+ event datasets with sub-second query times

**For T-Mobile specifically**, Agent Builder solves critical operational challenges:
- Reduces Mean Time To Detection (MTTD) for network incidents from 15+ minutes to under 5 minutes
- Enables proactive intervention before subscriber-impacting failures occur
- Correlates infrastructure health with service quality in real-time
- Democratizes network analytics across NOC, RAN engineering, and security teams

**Deployment timeline:** Agent Builder can be configured and deployed in days, not months. No custom development required - just define your tools using ES|QL queries you've already written.

**Next steps:**
1. Identify 3-5 high-priority analytical questions your teams ask regularly
2. Work with us to create sample datasets representative of your production data
3. Build and test tools in a development environment
4. Pilot with a small group of NOC analysts
5. Roll out to broader teams based on feedback

**Questions?**"

---

## **📊 Appendix: Sample Data Patterns**

### **Realistic MME Event Distribution**

For demo data generation, use these approximate distributions:

**Event Types:**
- ATTACH_REQUEST: 35%
- TAU_REQUEST (Tracking Area Update): 25%
- HANDOFF_REQUEST: 20%
- DETACH_REQUEST: 10%
- SERVICE_REQUEST: 10%

**Result Codes:**
- SUCCESS: 92%
- TIMEOUT: 3%
- NETWORK_FAILURE: 2.5%
- REJECTED: 1.5%
- AUTHENTICATION_FAILED: 1%

**Processing Latency (ms):**
- Normal: 50-200ms (80% of events)
- Degraded: 200-500ms (15% of events)
- Critical: 500-2000ms (5% of events)

**MME Resource Utilization:**
- CPU: Normal 40-70%, Stressed 70-90%, Critical 90-99%
- Memory: Normal 50-75%, Stressed 75-88%, Critical 88-97%

### **Cell Site Patterns**

**Technology Distribution:**
- LTE: 60%
- 5G_NSA (Non-Standalone): 30%
- 5G_SA (Standalone): 10%

**Site Types:**
- MACRO: 70%
- SMALL_CELL: 25%
- INDOOR: 5%

**Neighbor Cell Relationships:**
- Each cell should have 3-8 neighbor cells
- Neighbor relationships should be bidirectional (if A neighbors B, B neighbors A)

### **Subscriber Profile Patterns**

**Account Types:**
- POSTPAID: 70%
- PREPAID: 20%
- ENTERPRISE: 10%

**Device Models (sample):**
- iPhone 14 Pro, iPhone 13, iPhone 12
- Samsung Galaxy S23, S22, S21
- Google Pixel 7, Pixel 6
- OnePlus 11, OnePlus 10

### **SS7 Attack Patterns**

**Suspicious Message Patterns:**
- Location Tracking: 10+ SEND_ROUTING_INFO requests in 1 hour from different originators
- SMS Interception: Multiple FORWARD_SHORT_MESSAGE requests with unusual routing
- Roaming Fraud: INSERT_SUBSCRIBER_DATA from non-partner networks
- Subscriber Manipulation: Rapid UPDATE_LOCATION requests from geographically distant locations

**Risk Score Calculation:**
```
risk_score = (message_frequency * 20) + 
             (unique_originators * 15) + 
             (non_partner_network_flag * 30) +
             (geographic_anomaly * 25) +
             (time_anomaly * 10)
```

---

**End of Demo Guide**'''

    def get_talk_track(self) -> Dict[str, str]:
        """Talk track for each query"""
        # Can be customized per demo as needed
        return {}

    def get_objection_handling(self) -> Dict[str, str]:
        """Common objections and responses"""
        return {
            "complexity": "ES|QL syntax is SQL-like and easier than complex aggregations",
            "performance": "Queries run on indexed data with millisecond response times",
            "learning_curve": "Most teams productive within days, not weeks"
        }
