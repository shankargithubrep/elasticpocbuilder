from src.framework.base import DemoGuideModule, DemoConfig
from typing import Dict, List, Any, Optional
import pandas as pd

class TMobileDemoGuide(DemoGuideModule):
    """Demo guide for T-Mobile - Network Operations"""

    def __init__(self, config: DemoConfig, datasets: Dict[str, pd.DataFrame],
                 queries: List[Dict], aha_moment: Optional[Dict] = None):
        """Initialize with demo context"""
        super().__init__(config, datasets, queries, aha_moment)

    def generate_guide(self) -> str:
        """Generate customized demo guide"""
        return '''# **Elastic Agent Builder Demo for T-Mobile**

## **Internal Demo Script & Reference Guide**

---

## **📋 Demo Overview**

**Total Time:** 25-30 minutes
**Audience:** Network Operations technical/business stakeholders
**Goal:** Show how Agent Builder enables AI-powered analytics on T-Mobile network telemetry and operations data

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## **🗂️ Dataset Architecture**

### **Timeseries Datasets**

#### **network_procedures** (500,000 records)
Primary telemetry dataset capturing every network procedure execution across T-Mobile's LTE core network.

**Primary Key:** `procedure_id` (unique identifier per procedure execution)

**Key Fields:**
- `@timestamp` - Procedure execution timestamp
- `procedure_type` - Type of procedure (e.g., "SERVICE_REQUEST", "ATTACH", "HANDOFF", "TAU")
- `imsi` - International Mobile Subscriber Identity (subscriber identifier)
- `mme_id` - MME node handling the procedure
- `hss_id` - HSS node used for authentication
- `source_cell_id` - Originating cell tower
- `target_cell_id` - Destination cell tower (for handoffs)
- `success` - Boolean indicating procedure success/failure
- `failure_reason` - Error code when success=false (e.g., "CONTEXT_NOT_FOUND", "AUTH_FAILURE", "TIMEOUT")
- `duration_ms` - Procedure execution time in milliseconds
- `ue_context_id` - User Equipment context identifier

**Relationships:**
- Links to `mme_nodes` via `mme_id`
- Links to `hss_nodes` via `hss_id`
- Links to `cell_sites` via `source_cell_id` and `target_cell_id`

---

#### **mme_metrics** (100,000 records)
Resource utilization and operational metrics for Mobility Management Entity nodes.

**Primary Key:** `metric_id`

**Key Fields:**
- `@timestamp` - Metric collection timestamp
- `mme_id` - MME node identifier
- `cpu_percent` - CPU utilization percentage
- `memory_percent` - Memory utilization percentage
- `active_contexts` - Number of active UE contexts
- `context_not_found_errors` - Count of context lookup failures
- `database_connections` - Active database connection count
- `avg_response_time_ms` - Average procedure response time

**Relationships:**
- Links to `mme_nodes` via `mme_id`

---

#### **hss_metrics** (50,000 records)
Home Subscriber Server database performance and replication health metrics.

**Primary Key:** `metric_id`

**Key Fields:**
- `@timestamp` - Metric collection timestamp
- `hss_id` - HSS node identifier
- `replication_lag_ms` - Database replication lag in milliseconds
- `query_latency_ms` - Average query response time
- `active_connections` - Active database connections
- `lock_wait_time_ms` - Database lock contention time
- `subscriber_cache_hit_rate` - Cache hit percentage

**Relationships:**
- Links to `hss_nodes` via `hss_id`

---

#### **cell_metrics** (200,000 records)
Radio access network metrics from cell towers.

**Primary Key:** `metric_id`

**Key Fields:**
- `@timestamp` - Metric collection timestamp
- `cell_id` - Cell site identifier
- `active_ues` - Number of connected user devices
- `signal_strength_avg` - Average RSRP in dBm
- `interference_level` - Uplink interference level
- `handoff_success_rate` - Percentage of successful handoffs
- `rrc_connection_failures` - Radio Resource Control connection failures

**Relationships:**
- Links to `cell_sites` via `cell_id`

---

#### **security_events** (50,000 records)
Security monitoring events for SS7 attacks and rogue network detection.

**Primary Key:** `event_id`

**Key Fields:**
- `@timestamp` - Event detection timestamp
- `event_type` - Type of security event (e.g., "SS7_ATTACK", "ROGUE_NETWORK", "IMSI_CATCHER")
- `severity` - Event severity (LOW, MEDIUM, HIGH, CRITICAL)
- `source_ip` - Source IP address of suspicious activity
- `imsi` - Affected subscriber (if applicable)
- `mme_id` - MME that detected the event
- `attack_signature` - Signature pattern matched

**Relationships:**
- Links to `mme_nodes` via `mme_id`

---

### **Reference Datasets (Lookup Mode)**

#### **mme_nodes** (50 records)
Master data for MME infrastructure nodes.

**Primary Key:** `mme_id`

**Key Fields:**
- `mme_id` - Unique MME identifier (e.g., "MME-CHI-01")
- `hostname` - Server hostname
- `datacenter` - Geographic location (e.g., "Chicago", "Dallas", "Seattle")
- `pool_id` - MME pool identifier for load balancing
- `capacity` - Maximum concurrent UE contexts
- `software_version` - MME software version
- `vendor` - Equipment vendor (Ericsson, Nokia, etc.)

---

#### **hss_nodes** (10 records)
Master data for HSS database instances.

**Primary Key:** `hss_id`

**Key Fields:**
- `hss_id` - Unique HSS identifier (e.g., "HSS-WEST-01")
- `hostname` - Database server hostname
- `datacenter` - Geographic location
- `is_primary` - Boolean indicating primary/replica status
- `subscriber_capacity` - Maximum subscriber profiles
- `database_version` - Database software version

---

#### **cell_sites** (5,000 records)
Master data for cell tower locations and configurations.

**Primary Key:** `cell_id`

**Key Fields:**
- `cell_id` - Unique cell identifier
- `site_name` - Human-readable site name
- `latitude` - GPS latitude
- `longitude` - GPS longitude
- `city` - City location
- `state` - State location
- `frequency_band` - LTE frequency band (e.g., "Band 12", "Band 71")
- `sector` - Antenna sector (1, 2, or 3)
- `technology` - Network technology (LTE, 5G NSA)

---

## **🚀 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

**CRITICAL: All indexes need "index.mode": "lookup" for joins to work**

---

#### **Upload network_procedures (timeseries)**

1. Navigate to **Management > Dev Tools**
2. Create the index with standard mode:

```json
PUT /network_procedures
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "procedure_id": { "type": "keyword" },
      "procedure_type": { "type": "keyword" },
      "imsi": { "type": "keyword" },
      "mme_id": { "type": "keyword" },
      "hss_id": { "type": "keyword" },
      "source_cell_id": { "type": "keyword" },
      "target_cell_id": { "type": "keyword" },
      "success": { "type": "boolean" },
      "failure_reason": { "type": "keyword" },
      "duration_ms": { "type": "long" },
      "ue_context_id": { "type": "keyword" }
    }
  }
}
```

3. Upload CSV via **Management > Stack Management > Index Management > Data > Upload File**
4. Map columns to fields and import

---

#### **Upload mme_nodes (reference - LOOKUP MODE)**

1. Create the index with **lookup mode**:

```json
PUT /mme_nodes
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "mme_id": { "type": "keyword" },
      "hostname": { "type": "keyword" },
      "datacenter": { "type": "keyword" },
      "pool_id": { "type": "keyword" },
      "capacity": { "type": "long" },
      "software_version": { "type": "keyword" },
      "vendor": { "type": "keyword" }
    }
  }
}
```

2. Upload CSV and import

---

#### **Upload mme_metrics (timeseries)**

```json
PUT /mme_metrics
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "metric_id": { "type": "keyword" },
      "mme_id": { "type": "keyword" },
      "cpu_percent": { "type": "float" },
      "memory_percent": { "type": "float" },
      "active_contexts": { "type": "long" },
      "context_not_found_errors": { "type": "long" },
      "database_connections": { "type": "long" },
      "avg_response_time_ms": { "type": "float" }
    }
  }
}
```

---

#### **Upload hss_nodes (reference - LOOKUP MODE)**

```json
PUT /hss_nodes
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "hss_id": { "type": "keyword" },
      "hostname": { "type": "keyword" },
      "datacenter": { "type": "keyword" },
      "is_primary": { "type": "boolean" },
      "subscriber_capacity": { "type": "long" },
      "database_version": { "type": "keyword" }
    }
  }
}
```

---

#### **Upload hss_metrics (timeseries)**

```json
PUT /hss_metrics
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "metric_id": { "type": "keyword" },
      "hss_id": { "type": "keyword" },
      "replication_lag_ms": { "type": "long" },
      "query_latency_ms": { "type": "float" },
      "active_connections": { "type": "long" },
      "lock_wait_time_ms": { "type": "float" },
      "subscriber_cache_hit_rate": { "type": "float" }
    }
  }
}
```

---

#### **Upload cell_sites (reference - LOOKUP MODE)**

```json
PUT /cell_sites
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "cell_id": { "type": "keyword" },
      "site_name": { "type": "keyword" },
      "latitude": { "type": "float" },
      "longitude": { "type": "float" },
      "city": { "type": "keyword" },
      "state": { "type": "keyword" },
      "frequency_band": { "type": "keyword" },
      "sector": { "type": "integer" },
      "technology": { "type": "keyword" }
    }
  }
}
```

---

#### **Upload cell_metrics (timeseries)**

```json
PUT /cell_metrics
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "metric_id": { "type": "keyword" },
      "cell_id": { "type": "keyword" },
      "active_ues": { "type": "long" },
      "signal_strength_avg": { "type": "float" },
      "interference_level": { "type": "float" },
      "handoff_success_rate": { "type": "float" },
      "rrc_connection_failures": { "type": "long" }
    }
  }
}
```

---

#### **Upload security_events (timeseries)**

```json
PUT /security_events
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "event_id": { "type": "keyword" },
      "event_type": { "type": "keyword" },
      "severity": { "type": "keyword" },
      "source_ip": { "type": "ip" },
      "imsi": { "type": "keyword" },
      "mme_id": { "type": "keyword" },
      "attack_signature": { "type": "keyword" }
    }
  }
}
```

---

### **Step 2: Verify Lookup Mode Indices**

Run this query to confirm lookup mode is enabled:

```json
GET /mme_nodes,hss_nodes,cell_sites/_settings
```

You should see `"index.mode": "lookup"` in the settings for each reference index.

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to your AI Agent chat interface
- Have the agent already configured with all tools

### **Demo Script**

**Presenter:** "Before we dive into how this works, let me show you the end result. I'm going to ask our AI agent complex network operations questions that would normally require a data engineer to write custom queries."

**Sample questions to demonstrate:**

---

**Question 1 (ROI/Business Impact):**
> "Calculate the revenue impact of HSS authentication failures in the last 24 hours. Assume each failed authentication results in $2 lost revenue per subscriber and show me the total financial impact."

**What this showcases:** Multi-step reasoning, cross-dataset joins, business calculations

---

**Question 2 (Root Cause Analysis):**
> "Show me MME nodes with high service request failure rates correlated with memory exhaustion. Include the MME datacenter location and current memory utilization percentage."

**What this showcases:** Correlation analysis, enrichment with reference data, filtering

---

**Question 3 (Trend Detection):**
> "Are there any cell tower pairs experiencing cascade handoff failures? Show me the top 5 problematic cell pairs with failure rates over 10% and their geographic locations."

**What this showcases:** Pattern detection, percentage calculations, geographic enrichment

---

**Question 4 (Security Monitoring):**
> "Identify any SS7 security attack patterns in the last hour and tell me which subscribers were affected and which MME pool detected the attacks."

**What this showcases:** Security event analysis, time-based filtering, multi-dataset joins

---

**Question 5 (Capacity Planning):**
> "Which MME pools are experiencing split-brain conditions based on divergent UE context counts? Calculate the standard deviation of active contexts per pool."

**What this showcases:** Statistical analysis, grouping, anomaly detection

---

**Question 6 (Subscriber Impact):**
> "How many unique subscribers were impacted by authentication failures in the last 5 minutes? Classify the severity as minor, moderate, or critical based on subscriber count thresholds."

**What this showcases:** Distinct counts, time windows, classification logic

---

**Question 7 (Operational Health):**
> "Give me a health score for each HSS database by combining replication lag, query latency, and authentication failure rates. Flag any HSS instances that need immediate attention."

**What this showcases:** Composite scoring, multi-metric analysis, alerting logic

---

**Transition:** "So how does this actually work? Let's go under the hood and build these queries from scratch using ES|QL."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open Kibana Dev Tools Console
- Have the indices already created and populated

---

### **Query 1: Simple Aggregation (2 minutes)**

**Presenter:** "T-Mobile's Network Operations team wants to know: What are the top failure reasons for service requests in the last hour?"

**Copy/paste into console:**

```esql
FROM network_procedures
| WHERE procedure_type == "SERVICE_REQUEST" AND success == false AND @timestamp > NOW() - 1 hour
| STATS failure_count = COUNT(*) BY failure_reason
| SORT failure_count DESC
| LIMIT 10
```

**Run and narrate results:** "This is basic ES|QL:
- FROM: Source our network procedures data
- WHERE: Filter to failed service requests in the last hour
- STATS: Aggregate failure counts by reason
- SORT and LIMIT: Top 10 failure reasons

The syntax is intuitive - it reads like English. We can see immediately if we have a pattern like CONTEXT_NOT_FOUND dominating, which indicates MME memory issues."

---

### **Query 2: Add Calculations with EVAL (3 minutes)**

**Presenter:** "Let's add calculations to get the failure rate percentage and identify critical thresholds."

**Copy/paste:**

```esql
FROM network_procedures
| WHERE procedure_type == "SERVICE_REQUEST" AND @timestamp > NOW() - 1 hour
| STATS 
    total_procedures = COUNT(*),
    failed_procedures = COUNT(*) WHERE success == false
  BY mme_id
| EVAL failure_rate = TO_DOUBLE(failed_procedures) / TO_DOUBLE(total_procedures) * 100
| EVAL status = CASE(
    failure_rate > 10, "CRITICAL",
    failure_rate > 5, "WARNING",
    "NORMAL"
  )
| WHERE failure_rate > 5
| SORT failure_rate DESC
```

**Run and highlight:** "Key additions:
- EVAL: Creates calculated fields on-the-fly
- TO_DOUBLE: Critical for decimal division in failure rate calculation
- Multiple STATS: Aggregating both total and failed counts
- CASE statement: Business logic to classify severity
- Business-relevant thresholds: >10% is critical, >5% is warning

This gives us actionable intelligence - we can see which MME nodes need immediate attention."

---

### **Query 3: Join Datasets with LOOKUP JOIN (3 minutes)**

**Presenter:** "Now let's enrich this data with MME metadata to know which datacenters and pools are affected."

**Copy/paste:**

```esql
FROM network_procedures
| WHERE procedure_type == "SERVICE_REQUEST" AND @timestamp > NOW() - 1 hour
| STATS 
    total_procedures = COUNT(*),
    failed_procedures = COUNT(*) WHERE success == false
  BY mme_id
| EVAL failure_rate = TO_DOUBLE(failed_procedures) / TO_DOUBLE(total_procedures) * 100
| WHERE failure_rate > 5
| LOOKUP JOIN mme_nodes ON mme_id
| EVAL status = CASE(
    failure_rate > 10, "CRITICAL",
    failure_rate > 5, "WARNING",
    "NORMAL"
  )
| KEEP mme_id, datacenter, pool_id, vendor, failure_rate, status, failed_procedures, total_procedures
| SORT failure_rate DESC
```

**Run and explain:** "Magic happening here:
- LOOKUP JOIN: Combines network_procedures with mme_nodes using mme_id as the join key
- Now we have access to datacenter, pool_id, and vendor from the reference data
- This is a LEFT JOIN: All MME records kept, enriched with metadata
- KEEP: Selects only the columns we want in the output
- For LOOKUP JOIN to work, mme_nodes must have 'index.mode: lookup'

This is crucial for operations - now we know if the Chicago datacenter has issues or if it's an Ericsson software bug affecting multiple nodes."

---

### **Query 4: Complex Multi-Dataset Analytics (2 minutes)**

**Presenter:** "For the grand finale - a sophisticated query that detects MME resource exhaustion correlated with service failures. This combines procedure failures, MME resource metrics, and context errors to identify nodes experiencing memory corruption or software bugs."

**Copy/paste:**

```esql
FROM network_procedures
| WHERE procedure_type == "SERVICE_REQUEST" AND @timestamp > NOW() - 15 minutes
| STATS 
    total_requests = COUNT(*),
    failed_requests = COUNT(*) WHERE success == false,
    context_not_found = COUNT(*) WHERE failure_reason == "CONTEXT_NOT_FOUND"
  BY mme_id
| EVAL failure_rate = TO_DOUBLE(failed_requests) / TO_DOUBLE(total_requests) * 100
| WHERE failure_rate > 3
| LOOKUP JOIN mme_nodes ON mme_id
| LOOKUP JOIN (
    FROM mme_metrics
    | WHERE @timestamp > NOW() - 15 minutes
    | STATS 
        avg_memory = AVG(memory_percent),
        max_memory = MAX(memory_percent),
        avg_contexts = AVG(active_contexts),
        total_context_errors = SUM(context_not_found_errors)
      BY mme_id
  ) ON mme_id
| EVAL memory_pressure = CASE(
    max_memory > 90, "CRITICAL",
    max_memory > 80, "HIGH",
    max_memory > 70, "ELEVATED",
    "NORMAL"
  )
| EVAL context_error_rate = TO_DOUBLE(context_not_found) / TO_DOUBLE(total_requests) * 100
| WHERE max_memory > 70 OR context_error_rate > 2
| EVAL diagnosis = CASE(
    max_memory > 85 AND context_error_rate > 5, "Memory exhaustion causing context loss",
    context_error_rate > 10, "Possible split-brain or database sync issue",
    max_memory > 90, "Memory pressure - preemptive failover recommended",
    "Performance degradation detected"
  )
| KEEP mme_id, datacenter, pool_id, failure_rate, avg_memory, max_memory, 
       memory_pressure, context_error_rate, diagnosis, total_requests, failed_requests
| SORT max_memory DESC, failure_rate DESC
| LIMIT 20
```

**Run and break down:** 

"This query is doing enterprise-grade analytics:

**Step 1 - Procedure Analysis:** Calculate failure rates for service requests in the last 15 minutes, specifically tracking CONTEXT_NOT_FOUND errors which indicate memory issues.

**Step 2 - First Enrichment:** Join with mme_nodes to get datacenter and pool information.

**Step 3 - Subquery Join:** The nested FROM creates a subquery that calculates memory metrics from mme_metrics, then joins those results. This gives us average and max memory utilization correlated with the same time window.

**Step 4 - Classification Logic:** 
- Memory pressure categories based on utilization thresholds
- Context error rate calculation to identify corruption patterns
- Diagnosis field that provides root cause guidance

**Step 5 - Intelligent Filtering:** Only show MMEs with elevated memory (>70%) or high context error rates (>2%)

**The Result:** A prioritized list of MME nodes that need intervention, with clear diagnosis. If we see 'Memory exhaustion causing context loss' - that's an immediate page to the NOC. This query would take a data engineer hours to write in traditional SQL - here it's 25 lines of readable ES|QL."

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

**Agent Configuration:**

**Agent ID:** `tmobile-network-ops-agent`

**Display Name:** `T-Mobile Network Operations AI Assistant`

**Custom Instructions:** 

```
You are an expert AI assistant for T-Mobile Network Operations, specializing in LTE core network analytics, troubleshooting, and performance optimization.

Your knowledge domains include:
- MME (Mobility Management Entity) operations and failure analysis
- HSS (Home Subscriber Server) authentication and database health
- Cell tower handoff patterns and radio access network optimization
- Security event detection (SS7 attacks, rogue networks)
- Subscriber impact analysis and SLA monitoring

When analyzing issues:
1. Always correlate failures with resource utilization metrics
2. Enrich data with datacenter and pool information for geographic context
3. Calculate failure rates as percentages for threshold-based alerting
4. Identify affected subscriber counts for business impact assessment
5. Provide actionable diagnoses with specific remediation guidance

For time-based queries, default to the last 1 hour unless specified otherwise.

For severity classification:
- CRITICAL: >10% failure rate or >10,000 affected subscribers
- WARNING: >5% failure rate or >2,000 affected subscribers  
- ELEVATED: >2% failure rate or >500 affected subscribers

Always include relevant context like datacenter location, MME pool, and vendor information in your responses.
```

---

### **Creating Tools**

#### **Tool 1: MME Service Request Failure Analysis**

**Tool Name:** `analyze_mme_service_failures`

**Description:** 
```
Analyzes service request procedure failures across MME nodes with resource correlation. 
Detects memory exhaustion, context corruption, and software bugs by correlating failure 
rates with CPU/memory utilization and context_not_found errors. Enriches results with 
MME datacenter, pool, and vendor information. Use this when investigating MME performance 
issues, high failure rates, or subscriber impact from core network problems.
```

**ES|QL Query:**
```esql
FROM network_procedures
| WHERE procedure_type == "SERVICE_REQUEST" AND @timestamp > NOW() - {{time_window}}
| STATS 
    total_requests = COUNT(*),
    failed_requests = COUNT(*) WHERE success == false,
    context_errors = COUNT(*) WHERE failure_reason == "CONTEXT_NOT_FOUND"
  BY mme_id
| EVAL failure_rate = TO_DOUBLE(failed_requests) / TO_DOUBLE(total_requests) * 100
| WHERE failure_rate > {{threshold}}
| LOOKUP JOIN mme_nodes ON mme_id
| LOOKUP JOIN (
    FROM mme_metrics
    | WHERE @timestamp > NOW() - {{time_window}}
    | STATS avg_memory = AVG(memory_percent), max_memory = MAX(memory_percent) BY mme_id
  ) ON mme_id
| EVAL diagnosis = CASE(
    max_memory > 85 AND failure_rate > 5, "Memory exhaustion",
    context_errors > 100, "Context corruption detected",
    "Performance degradation"
  )
| KEEP mme_id, datacenter, pool_id, vendor, failure_rate, max_memory, diagnosis
| SORT failure_rate DESC
```

**Parameters:**
- `time_window` (default: "1 hour")
- `threshold` (default: 3)

---

#### **Tool 2: HSS Authentication Failure Detection**

**Tool Name:** `detect_hss_authentication_failures`

**Description:**
```
Detects mass authentication failure events by calculating failure rates per HSS database 
instance. Correlates authentication failures with HSS replication lag and query latency 
to identify database synchronization issues. Use this when investigating subscriber 
authentication problems, HSS database corruption, or sudden spikes in attach/TAU failures. 
Alerts when failure rate exceeds 5% threshold.
```

**ES|QL Query:**
```esql
FROM network_procedures
| WHERE procedure_type IN ("ATTACH", "TAU") AND @timestamp > NOW() - {{time_window}}
| STATS 
    total_auth = COUNT(*),
    failed_auth = COUNT(*) WHERE failure_reason == "AUTH_FAILURE"
  BY hss_id
| EVAL auth_failure_rate = TO_DOUBLE(failed_auth) / TO_DOUBLE(total_auth) * 100
| WHERE auth_failure_rate > 5
| LOOKUP JOIN hss_nodes ON hss_id
| LOOKUP JOIN (
    FROM hss_metrics
    | WHERE @timestamp > NOW() - {{time_window}}
    | STATS 
        avg_replication_lag = AVG(replication_lag_ms),
        max_query_latency = MAX(query_latency_ms)
      BY hss_id
  ) ON hss_id
| EVAL issue_type = CASE(
    avg_replication_lag > 5000, "Database replication lag",
    max_query_latency > 1000, "Query performance degradation",
    "Authentication logic failure"
  )
| KEEP hss_id, datacenter, is_primary, auth_failure_rate, avg_replication_lag, issue_type
| SORT auth_failure_rate DESC
```

**Parameters:**
- `time_window` (default: "1 hour")

---

#### **Tool 3: Cell Tower Handoff Failure Analysis**

**Tool Name:** `analyze_cell_handoff_failures`

**Description:**
```
Identifies problematic cell tower pairs experiencing handoff cascade failures. Calculates 
failure rates for source-target cell combinations and enriches with geographic location 
data. Use this for RF optimization, identifying coverage gaps, or investigating subscriber 
mobility issues. Flags cell pairs with failure rates exceeding 10%.
```

**ES|QL Query:**
```esql
FROM network_procedures
| WHERE procedure_type == "HANDOFF" AND @timestamp > NOW() - {{time_window}}
| STATS 
    total_handoffs = COUNT(*),
    failed_handoffs = COUNT(*) WHERE success == false
  BY source_cell_id, target_cell_id
| EVAL handoff_failure_rate = TO_DOUBLE(failed_handoffs) / TO_DOUBLE(total_handoffs) * 100
| WHERE handoff_failure_rate > {{threshold}}
| LOOKUP JOIN cell_sites AS source ON source_cell_id = source.cell_id
| LOOKUP JOIN cell_sites AS target ON target_cell_id = target.cell_id
| KEEP source_cell_id, target_cell_id, source.city, source.state, target.city, 
       target.state, handoff_failure_rate, failed_handoffs, total_handoffs
| SORT handoff_failure_rate DESC
| LIMIT 20
```

**Parameters:**
- `time_window` (default: "15 minutes")
- `threshold` (default: 10)

---

#### **Tool 4: Subscriber Impact and Severity Classification**

**Tool Name:** `calculate_subscriber_impact`

**Description:**
```
Calculates affected subscriber counts across all procedure failure types and classifies 
incident severity for proactive help desk escalation. Counts unique IMSIs experiencing 
failures and applies tiered severity thresholds (500/2000/10000 subscribers). Use this 
to assess business impact, predict ticket volume, and trigger proactive customer 
notifications before complaints surge.
```

**ES|QL Query:**
```esql
FROM network_procedures
| WHERE success == false AND @timestamp > NOW() - {{time_window}}
| STATS 
    affected_subscribers = COUNT_DISTINCT(imsi),
    total_failures = COUNT(*),
    service_request_failures = COUNT(*) WHERE procedure_type == "SERVICE_REQUEST",
    auth_failures = COUNT(*) WHERE procedure_type IN ("ATTACH", "TAU"),
    handoff_failures = COUNT(*) WHERE procedure_type == "HANDOFF"
| EVAL severity = CASE(
    affected_subscribers > 10000, "CRITICAL - Mass Outage",
    affected_subscribers > 2000, "MAJOR - Significant Impact",
    affected_subscribers > 500, "MODERATE - Elevated Impact",
    "MINOR - Limited Impact"
  )
| EVAL estimated_ticket_volume = affected_subscribers * 0.15
| KEEP severity, affected_subscribers, total_failures, service_request_failures, 
       auth_failures, handoff_failures, estimated_ticket_volume
```

**Parameters:**
- `time_window` (default: "5 minutes")

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

#### **Warm-up Questions (Start Easy)**

**Q1:** "How many service request failures occurred in the last hour?"

**Expected behavior:** Agent uses `analyze_mme_service_failures` tool, returns total count with breakdown by MME.

---

**Q2:** "Which MME node has the highest failure rate right now?"

**Expected behavior:** Agent identifies the top MME with percentage, includes datacenter location.

---

**Q3:** "Show me all CRITICAL severity MME nodes."

**Expected behavior:** Agent filters for failure_rate > 10%, lists nodes with diagnosis.

---

#### **Business-Focused Questions**

**Q4:** "Calculate the financial impact of authentication failures in the last 24 hours. Assume $2 revenue loss per failed authentication."

**Expected behavior:** Agent counts failed authentications, multiplies by $2, presents dollar amount with subscriber count.

---

**Q5:** "How many unique subscribers were impacted by failures in the last 5 minutes? What's the severity classification?"

**Expected behavior:** Agent uses `calculate_subscriber_impact` tool, returns distinct IMSI count and severity tier (MINOR/MODERATE/MAJOR/CRITICAL).

---

**Q6:** "Are we at risk of SLA violations? Show me any MME pools with sustained failure rates above 5% for more than 10 minutes."

**Expected behavior:** Agent analyzes time-series patterns, identifies pools with persistent issues.

---

#### **Trend Analysis Questions**

**Q7:** "Show me the trend of service request failures over the last 4 hours, grouped by hour."

**Expected behavior:** Agent uses time bucketing, shows hourly failure counts to identify if issue is worsening or improving.

---

**Q8:** "Compare authentication failure rates between primary and replica HSS databases."

**Expected behavior:** Agent joins with hss_nodes, groups by is_primary field, calculates comparative rates.

---

**Q9:** "Which datacenters have the most network issues right now?"

**Expected behavior:** Agent aggregates failures across all procedure types by datacenter, ranks locations.

---

#### **Root Cause and Optimization Questions**

**Q10:** "Are there any MME nodes showing signs of memory exhaustion?"

**Expected behavior:** Agent correlates high memory_percent with context_not_found errors, flags nodes with memory_pressure = "CRITICAL".

---

**Q11:** "Identify cell tower pairs with handoff failure rates above 15% and show me their geographic locations."

**Expected behavior:** Agent uses `analyze_cell_handoff_failures` with threshold=15, includes city/state for both source and target cells.

---

**Q12:** "Which vendor's MME equipment is performing worst in terms of failure rates?"

**Expected behavior:** Agent groups by vendor field from mme_nodes, calculates average failure rates, ranks vendors.

---

**Q13:** "Show me any HSS databases with replication lag over 5 seconds that are also experiencing authentication failures."

**Expected behavior:** Agent correlates hss_metrics replication_lag_ms with authentication failures, identifies sync issues.

---

**Q14:** "Detect any potential split-brain conditions in MME pools based on context count divergence."

**Expected behavior:** Agent calculates standard deviation of active_contexts within each pool_id, flags pools with high variance.

---

**Q15:** "Are there any SS7 security attacks detected in the last hour? Which subscribers and MME pools were affected?"

**Expected behavior:** Agent queries security_events for event_type="SS7_ATTACK", joins with mme_nodes for pool information, lists affected IMSIs.

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "Modern query language built specifically for analytics on time-series data"
- "Piped syntax is intuitive and readable - technical and business users can understand queries"
- "Operates on columnar blocks, not individual rows - extremely performant even on millions of records"
- "Supports complex operations out of the box: LOOKUP JOINs, window functions, statistical aggregations, time-series bucketing"
- "No need to pre-define schemas for calculated fields - EVAL creates them on the fly"

### **On Agent Builder:**
- "Bridges the gap between AI and enterprise operational data"
- "No custom development required - configure tools, don't write code"
- "Works directly with existing Elasticsearch indices - no ETL, no data movement"
- "Agent automatically selects the right tool based on question intent"
- "Natural language interface democratizes access to complex analytics"
- "Built-in security - respects Elasticsearch RBAC and field-level security"

### **On Business Value for T-Mobile:**
- "Reduces Mean Time to Detection (MTTD) for network issues from hours to seconds"
- "Democratizes network analytics - NOC engineers don't need to wait for data team"
- "Real-time insights enable proactive remediation before subscribers are impacted"
- "Correlates data across multiple systems automatically - no manual data wrangling"
- "Faster root cause identification reduces MTTR and prevents SLA violations"
- "Predictive capabilities - identify issues before they cascade"
- "Reduces operational costs - fewer escalations, less manual analysis"

### **On Telecommunications-Specific Value:**
- "Handles the scale of telecom data - millions of procedures per hour, no problem"
- "Purpose-built for time-series correlation - critical for network event analysis"
- "Enrichment with reference data (cell sites, MME pools) provides operational context"
- "Supports complex network topology analysis - handoff patterns, pool behavior"
- "Security monitoring integrated with operational data for holistic visibility"

---

## **🔧 Troubleshooting**

**If a query fails:**
- Check index names match exactly (case-sensitive): `network_procedures`, `mme_nodes`, etc.
- Verify field names are correct: `mme_id`, `procedure_type`, `@timestamp`
- Ensure time filters use proper syntax: `NOW() - 1 hour` not `NOW()-1h`
- Confirm joined indices (mme_nodes, hss_nodes, cell_sites) are in lookup mode

**If LOOKUP JOIN returns no results:**
- Verify join key format is consistent: `mme_id` in both datasets should be identical strings
- Check that lookup index has data: `FROM mme_nodes | LIMIT 10`
- Confirm lookup index has `"index.mode": "lookup"` in settings
- Verify join key exists in both datasets - use `STATS COUNT(*) BY mme_id` to check

**If agent gives wrong answer:**
- Check tool descriptions - are they clear about when to use each tool?
- Review custom instructions - is the guidance specific enough?
- Verify query parameters have sensible defaults
- Test the underlying ES|QL query directly in Dev Tools to ensure it works

**If calculations are wrong:**
- Ensure TO_DOUBLE() is used before division for percentage calculations
- Check for division by zero scenarios - add WHERE clauses to filter zero denominators
- Verify aggregation functions match intent: COUNT(*) vs COUNT_DISTINCT() vs SUM()

**If performance is slow:**
- Add time filters to limit data scanned: `WHERE @timestamp > NOW() - 1 hour`
- Use LIMIT clauses to cap result sets
- Consider adding index patterns to FROM clause for partition pruning
- Check if indices have appropriate date-based sharding

---

## **🎬 Closing**

"What we've shown today:

✅ **Complex network analytics** on interconnected datasets - procedures, metrics, reference data - all correlated in real-time

✅ **Natural language interface** for Network Operations engineers - no SQL expertise required to investigate issues

✅ **Real-time root cause detection** - correlating failures with resource utilization, database health, and geographic context automatically

✅ **Proactive alerting capabilities** - identifying issues before they cascade into mass outages

✅ **Business impact quantification** - from technical metrics to subscriber impact to revenue loss in seconds

✅ **No custom development** - Agent Builder deployed on existing Elasticsearch infrastructure in days, not months

**For T-Mobile specifically:**
- Reduce MTTD for MME resource exhaustion from hours to minutes
- Detect HSS split-brain and replication issues before authentication storms
- Identify cell tower handoff problems for targeted RF optimization
- Quantify subscriber impact for proactive help desk scaling
- Correlate security events with operational data for faster threat response

**Next Steps:**
1. Pilot with Network Operations team on production data
2. Expand tool library for additional use cases (TAU failures, RRC issues, capacity planning)
3. Integrate with incident management for automated ticket creation
4. Build custom dashboards for NOC visualization

Questions?"'''

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
