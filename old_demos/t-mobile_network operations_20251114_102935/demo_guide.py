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
**Goal:** Show how Agent Builder enables AI-powered analytics on T-Mobile network telemetry data

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## **🗂️ Dataset Architecture**

### **Timeseries Datasets (Event Streams)**

#### **mme_signaling_events** (150,000 records)
Core network signaling events from Mobility Management Entity nodes.

**Primary Key:** `event_id` (unique per signaling event)

**Key Fields:**
- `@timestamp` - Event occurrence time
- `imsi` - International Mobile Subscriber Identity (subscriber identifier)
- `mme_host` - MME server processing the event
- `cell_id` - Cell tower identifier
- `procedure_type` - Signaling procedure (attach, service_request, tracking_area_update, detach)
- `result` - Success or failure indicator
- `reject_cause` - Failure reason code when result = failure
- `latency_ms` - Procedure processing time in milliseconds
- `nas_message_type` - Non-Access Stratum message type

**Relationships:**
- `mme_host` → joins to `mme_hosts.hostname`
- `cell_id` → joins to `cells.cell_id`
- `imsi` → links to `subscriber_sessions.imsi`

---

#### **diameter_transactions** (200,000 records)
Diameter protocol transactions between MME and HSS for authentication and subscriber data.

**Primary Key:** `transaction_id`

**Key Fields:**
- `@timestamp` - Transaction timestamp
- `command_code` - Diameter command (AIR=authentication, ULR=update_location, IDR=insert_data)
- `result_code` - Success (2001) or error codes
- `hss_node` - HSS database node processing request
- `mme_host` - Originating MME
- `imsi` - Subscriber identifier
- `response_time_ms` - Round-trip transaction time
- `application_id` - Diameter application (S6a interface)

**Relationships:**
- `hss_node` → joins to `hss_nodes.node_id`
- `mme_host` → joins to `mme_hosts.hostname`
- `imsi` → links to `subscriber_sessions.imsi`

---

#### **handoff_events** (80,000 records)
Cell handoff attempts and outcomes as subscribers move between cell towers.

**Primary Key:** `handoff_id`

**Key Fields:**
- `@timestamp` - Handoff attempt time
- `imsi` - Subscriber performing handoff
- `source_cell_id` - Originating cell
- `target_cell_id` - Destination cell
- `handoff_result` - Success, failure, or timeout
- `failure_reason` - Root cause (radio_link_failure, target_cell_congestion, missing_neighbor)
- `rsrp_source` - Reference Signal Received Power at source (dBm)
- `rsrp_target` - RSRP at target cell
- `handoff_duration_ms` - Time to complete handoff

**Relationships:**
- `source_cell_id` → joins to `cells.cell_id`
- `target_cell_id` → joins to `cells.cell_id`
- `imsi` → links to `subscriber_sessions.imsi`

---

#### **security_events** (25,000 records)
Detected security threats including SS7 attacks and rogue network attempts.

**Primary Key:** `security_event_id`

**Key Fields:**
- `@timestamp` - Detection timestamp
- `attack_type` - Category (ss7_map_exploit, fake_base_station, roaming_fraud, imsi_catcher)
- `source_network` - Originating network/PLMN
- `affected_imsi` - Targeted subscriber(s)
- `severity` - Critical, high, medium, low
- `blocked` - Whether attack was successfully blocked (true/false)
- `attack_description` - Semantic description of attack vector
- `detection_method` - How threat was identified

**Relationships:**
- `affected_imsi` → links to `subscriber_sessions.imsi`

---

#### **subscriber_sessions** (120,000 records)
Active and completed subscriber data sessions with service quality metrics.

**Primary Key:** `session_id`

**Key Fields:**
- `@timestamp` - Session start time
- `imsi` - Subscriber identifier
- `session_duration_seconds` - Length of data session
- `data_volume_mb` - Total data transferred
- `session_result` - Completed, dropped, or failed
- `drop_reason` - Cause of session termination if abnormal
- `cell_id` - Serving cell during session
- `customer_segment_id` - Business customer tier
- `apn` - Access Point Name (service type)

**Relationships:**
- `cell_id` → joins to `cells.cell_id`
- `customer_segment_id` → joins to `customer_segments.segment_id`
- `imsi` → common key across all timeseries datasets

---

### **Reference Datasets (Lookup Tables)**

#### **mme_hosts** (50 records)
Mobility Management Entity server inventory.

**Primary Key:** `hostname`

**Key Fields:**
- `hostname` - MME server identifier (e.g., mme-dal-01)
- `datacenter` - Physical location
- `software_version` - MME software release
- `capacity_max_subscribers` - Maximum subscriber capacity
- `vendor` - Equipment manufacturer

---

#### **cells** (500 records)
Cell tower/sector inventory with geographic and technical attributes.

**Primary Key:** `cell_id`

**Key Fields:**
- `cell_id` - Unique cell identifier
- `site_name` - Tower location name
- `latitude` - Geographic coordinate
- `longitude` - Geographic coordinate
- `technology` - LTE, 5G_NSA, 5G_SA
- `frequency_band` - Spectrum band (e.g., n41, n71)
- `max_capacity_users` - Engineered capacity limit
- `region` - Geographic market region

---

#### **hss_nodes** (20 records)
Home Subscriber Server database node inventory.

**Primary Key:** `node_id`

**Key Fields:**
- `node_id` - HSS node identifier
- `datacenter` - Physical location
- `database_type` - Database technology
- `replication_group` - Database replication cluster
- `active_subscribers` - Subscriber records hosted

---

#### **customer_segments** (10 records)
Customer tier definitions with business value metrics.

**Primary Key:** `segment_id`

**Key Fields:**
- `segment_id` - Segment identifier
- `segment_name` - Business tier (Enterprise, Premium, Standard, Prepaid)
- `arpu` - Average Revenue Per User (monthly)
- `sla_uptime_percent` - Contracted service level
- `sla_penalty_rate` - Financial penalty per hour of downtime

---

## **🚀 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

**CRITICAL: All indexes need "index.mode": "lookup" for joins to work**

Navigate to **Kibana → Management → Dev Tools**

---

#### **1. Create mme_signaling_events index**

```json
PUT /mme_signaling_events
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "event_id": { "type": "keyword" },
      "imsi": { "type": "keyword" },
      "mme_host": { "type": "keyword" },
      "cell_id": { "type": "keyword" },
      "procedure_type": { "type": "keyword" },
      "result": { "type": "keyword" },
      "reject_cause": { "type": "keyword" },
      "latency_ms": { "type": "integer" },
      "nas_message_type": { "type": "keyword" }
    }
  }
}
```

**Upload CSV:** Use Kibana's **Upload File** feature (Machine Learning → Data Visualizer → Upload file) and map to this index.

---

#### **2. Create diameter_transactions index**

```json
PUT /diameter_transactions
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "transaction_id": { "type": "keyword" },
      "command_code": { "type": "keyword" },
      "result_code": { "type": "integer" },
      "hss_node": { "type": "keyword" },
      "mme_host": { "type": "keyword" },
      "imsi": { "type": "keyword" },
      "response_time_ms": { "type": "integer" },
      "application_id": { "type": "keyword" }
    }
  }
}
```

---

#### **3. Create handoff_events index**

```json
PUT /handoff_events
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "handoff_id": { "type": "keyword" },
      "imsi": { "type": "keyword" },
      "source_cell_id": { "type": "keyword" },
      "target_cell_id": { "type": "keyword" },
      "handoff_result": { "type": "keyword" },
      "failure_reason": { "type": "keyword" },
      "rsrp_source": { "type": "integer" },
      "rsrp_target": { "type": "integer" },
      "handoff_duration_ms": { "type": "integer" }
    }
  }
}
```

---

#### **4. Create security_events index**

```json
PUT /security_events
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "security_event_id": { "type": "keyword" },
      "attack_type": { "type": "keyword" },
      "source_network": { "type": "keyword" },
      "affected_imsi": { "type": "keyword" },
      "severity": { "type": "keyword" },
      "blocked": { "type": "boolean" },
      "attack_description": { "type": "text" },
      "detection_method": { "type": "keyword" }
    }
  }
}
```

---

#### **5. Create subscriber_sessions index**

```json
PUT /subscriber_sessions
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "session_id": { "type": "keyword" },
      "imsi": { "type": "keyword" },
      "session_duration_seconds": { "type": "integer" },
      "data_volume_mb": { "type": "float" },
      "session_result": { "type": "keyword" },
      "drop_reason": { "type": "keyword" },
      "cell_id": { "type": "keyword" },
      "customer_segment_id": { "type": "keyword" },
      "apn": { "type": "keyword" }
    }
  }
}
```

---

#### **6. Create mme_hosts index (LOOKUP MODE)**

```json
PUT /mme_hosts
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "hostname": { "type": "keyword" },
      "datacenter": { "type": "keyword" },
      "software_version": { "type": "keyword" },
      "capacity_max_subscribers": { "type": "integer" },
      "vendor": { "type": "keyword" }
    }
  }
}
```

---

#### **7. Create cells index (LOOKUP MODE)**

```json
PUT /cells
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
      "technology": { "type": "keyword" },
      "frequency_band": { "type": "keyword" },
      "max_capacity_users": { "type": "integer" },
      "region": { "type": "keyword" }
    }
  }
}
```

---

#### **8. Create hss_nodes index (LOOKUP MODE)**

```json
PUT /hss_nodes
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "node_id": { "type": "keyword" },
      "datacenter": { "type": "keyword" },
      "database_type": { "type": "keyword" },
      "replication_group": { "type": "keyword" },
      "active_subscribers": { "type": "integer" }
    }
  }
}
```

---

#### **9. Create customer_segments index (LOOKUP MODE)**

```json
PUT /customer_segments
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "segment_id": { "type": "keyword" },
      "segment_name": { "type": "keyword" },
      "arpu": { "type": "float" },
      "sla_uptime_percent": { "type": "float" },
      "sla_penalty_rate": { "type": "float" }
    }
  }
}
```

---

### **Step 2: Verify Data Load**

Run quick verification queries:

```esql
FROM mme_signaling_events
| STATS event_count = COUNT(*)
```

```esql
FROM cells
| STATS cell_count = COUNT(*)
```

All indices should return record counts matching the architecture section.

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to your AI Agent chat interface
- Have the agent already configured with all tools

### **Demo Script**

**Presenter:** "Before we dive into how this works, let me show you the end result. I'm going to ask our AI agent complex network operations questions that would normally require a data analyst hours to answer."

---

### **Sample questions to demonstrate:**

#### **Question 1: Revenue Impact Analysis (ROI Focus)**

**Ask the agent:**
> "What is the estimated revenue impact from dropped subscriber sessions in the last 24 hours? Break it down by customer segment and calculate SLA penalty exposure."

**What this shows:**
- Multi-dataset joins (subscriber_sessions → customer_segments)
- Business metric calculations (ARPU × session counts)
- Financial impact quantification
- Executive-level insights

**Expected output:** Revenue loss figures by segment, total SLA penalties, affected subscriber counts.

---

#### **Question 2: Security Threat Detection (Cross-Dataset)**

**Ask the agent:**
> "Show me SS7 security attacks detected in the last 7 days. Which source networks are most aggressive? How many subscribers were affected and what percentage were successfully blocked?"

**What this shows:**
- Security event aggregation
- Pattern detection across attack types
- Effectiveness metrics (blocked vs. not blocked)
- Threat prioritization

**Expected output:** Attack counts by source network, affected IMSI counts, blocking success rates.

---

#### **Question 3: Network Performance Root Cause (Complex Analytics)**

**Ask the agent:**
> "Which cells are experiencing the highest handoff failure rates? For the top 5 problematic cells, identify if they're source or target problems and show me the neighboring cells involved."

**What this shows:**
- Handoff cascade failure detection
- Geographic clustering analysis
- Directional problem identification (source vs. target)
- Actionable insights for field ops

**Expected output:** Ranked list of cells with failure rates, neighbor relationships, failure patterns.

---

#### **Question 4: Database Performance Correlation**

**Ask the agent:**
> "Analyze HSS authentication transaction performance. Which HSS nodes are showing response time degradation? Correlate with MME hosts to identify if specific MME-HSS pairs have issues."

**What this shows:**
- Diameter protocol analysis
- Database node performance tracking
- Multi-dimensional correlation (MME × HSS)
- Proactive degradation detection

**Expected output:** HSS nodes with elevated response times, affected MME hosts, statistical anomalies.

---

#### **Question 5: Subscriber Context Split-Brain Detection**

**Ask the agent:**
> "Detect potential split-brain conditions where the same IMSI is being processed by multiple MME hosts simultaneously within 5-minute windows. Show me the IMSIs and involved MME hosts."

**What this shows:**
- Advanced temporal window analysis
- Multi-MME context conflict detection
- Distributed system failure modes
- Signaling storm prevention

**Expected output:** IMSIs with multiple concurrent MME processors, time windows, affected hosts.

---

#### **Question 6: Capacity Planning & Trending**

**Ask the agent:**
> "Show me the trend of attach procedure failures by MME host over the last 30 days. Identify which MMEs are showing increasing failure rates that might indicate resource exhaustion."

**What this shows:**
- Time-series trend analysis
- Proactive capacity monitoring
- Resource exhaustion prediction
- Infrastructure scaling insights

**Expected output:** MME hosts with trending failure rate increases, statistical trends, capacity alerts.

---

#### **Question 7: Technology Migration Analysis**

**Ask the agent:**
> "Compare service request failure rates between LTE and 5G cells. Which technology is performing better and what are the dominant failure causes for each?"

**What this shows:**
- Technology comparison analytics
- Migration readiness assessment
- Failure cause distribution
- Strategic technology insights

**Expected output:** Failure rate comparison, technology-specific failure causes, performance deltas.

---

**Transition:** "Pretty powerful, right? These answers came back in seconds. Now let me show you how this actually works under the hood. We're going to build these queries from scratch using ES|QL."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open Kibana Dev Tools Console
- Have the indices already created and populated
- Switch to ES|QL mode in the console

---

### **Query 1: Simple Aggregation (2 minutes)**

**Presenter:** "T-Mobile Network Operations wants to know: Which MME hosts are experiencing the highest attach procedure failure rates?"

**Copy/paste into console:**

```esql
FROM mme_signaling_events
| WHERE procedure_type == "attach"
| STATS total_attempts = COUNT(*), 
        failures = COUNT(*) WHERE result == "failure"
  BY mme_host
| EVAL failure_rate = TO_DOUBLE(failures) / TO_DOUBLE(total_attempts) * 100
| SORT failure_rate DESC
| LIMIT 10
```

**Run and narrate results:** "This is basic ES|QL:
- FROM: Source our signaling events
- WHERE: Filter to attach procedures only
- STATS: Aggregate total attempts and failures by MME host
- EVAL: Calculate failure rate percentage
- SORT and LIMIT: Top 10 problematic MMEs

The syntax is intuitive - it reads like English. Notice how we use TO_DOUBLE for accurate percentage calculations."

---

### **Query 2: Add Calculations with EVAL (3 minutes)**

**Presenter:** "Let's add more sophisticated calculations to detect abnormal authentication response times that indicate HSS database degradation."

**Copy/paste:**

```esql
FROM diameter_transactions
| WHERE command_code == "AIR"
| STATS avg_response = AVG(response_time_ms),
        stddev_response = STDDEV(response_time_ms),
        total_transactions = COUNT(*),
        failures = COUNT(*) WHERE result_code != 2001
  BY hss_node
| EVAL failure_rate = TO_DOUBLE(failures) / TO_DOUBLE(total_transactions) * 100
| EVAL z_score_threshold = avg_response + (2 * stddev_response)
| EVAL performance_status = CASE(
    avg_response > z_score_threshold, "DEGRADED",
    failure_rate > 5.0, "HIGH_FAILURE_RATE",
    "NORMAL"
  )
| SORT avg_response DESC
| LIMIT 20
```

**Run and highlight:** "Key additions:
- EVAL: Creates calculated fields on-the-fly
- STDDEV: Statistical standard deviation for anomaly detection
- CASE: Conditional logic to classify node health status
- Z-score analysis: Identifies nodes with response times 2+ standard deviations above mean
- Multiple business-relevant calculations in a single query

This is the kind of analysis that would take hours in traditional SQL - here it's real-time."

---

### **Query 3: Join Datasets with LOOKUP JOIN (3 minutes)**

**Presenter:** "Now let's combine handoff events with cell tower metadata to identify cascade failure patterns where one problematic cell causes failures to multiple neighbors."

**Copy/paste:**

```esql
FROM handoff_events
| WHERE handoff_result == "failure"
| STATS failure_count = COUNT(*),
        unique_targets = COUNT_DISTINCT(target_cell_id)
  BY source_cell_id
| WHERE unique_targets >= 3
| LOOKUP JOIN cells ON cells.cell_id = source_cell_id
| EVAL cascade_severity = CASE(
    unique_targets >= 5, "CRITICAL",
    unique_targets >= 4, "HIGH",
    "MEDIUM"
  )
| KEEP source_cell_id, site_name, technology, region, failure_count, unique_targets, cascade_severity
| SORT failure_count DESC
| LIMIT 15
```

**Run and explain:** "Magic happening here:
- LOOKUP JOIN: Combines handoff events with cell metadata using cell_id as the join key
- Now we have access to site_name, technology, region from the cells reference table
- WHERE unique_targets >= 3: Identifies cascade patterns (one source failing to 3+ targets)
- This is a LEFT JOIN: All handoff records kept, enriched with cell tower details
- For LOOKUP JOIN to work, the cells index must have 'index.mode: lookup'

This query identifies the exact cell towers causing cascade failures - field ops can dispatch teams immediately."

---

### **Query 4: Complex Multi-Dataset Analytics (2 minutes)**

**Presenter:** "For the grand finale - a sophisticated analytical query showing real-time revenue impact calculation for network incidents with customer segment analysis."

**Copy/paste:**

```esql
FROM subscriber_sessions
| WHERE session_result == "dropped" AND @timestamp > NOW() - 24 hours
| LOOKUP JOIN customer_segments ON customer_segments.segment_id = customer_segment_id
| LOOKUP JOIN cells ON cells.cell_id = cell_id
| STATS dropped_sessions = COUNT(*),
        unique_subscribers = COUNT_DISTINCT(imsi),
        total_data_loss_mb = SUM(data_volume_mb)
  BY segment_name, region, technology
| EVAL revenue_loss = TO_DOUBLE(dropped_sessions) * arpu / 30.0
| EVAL sla_penalty_exposure = CASE(
    TO_DOUBLE(dropped_sessions) / TO_DOUBLE(unique_subscribers) > 0.05,
    TO_DOUBLE(unique_subscribers) * arpu * sla_penalty_rate,
    0.0
  )
| EVAL total_financial_impact = revenue_loss + sla_penalty_exposure
| EVAL avg_data_loss_per_session = total_data_loss_mb / TO_DOUBLE(dropped_sessions)
| KEEP segment_name, region, technology, dropped_sessions, unique_subscribers, 
       revenue_loss, sla_penalty_exposure, total_financial_impact, avg_data_loss_per_session
| SORT total_financial_impact DESC
| LIMIT 20
```

**Run and break down:** 

"This is executive-level business intelligence:

**Data Integration:**
- Joins subscriber sessions with customer segments (for ARPU data)
- Joins with cells (for geographic and technology context)
- Three datasets combined in one query

**Business Calculations:**
- Revenue loss: Daily ARPU impact (monthly ARPU / 30 days)
- SLA penalty exposure: Triggered when drop rate exceeds 5% of subscribers
- Total financial impact: Revenue + penalties

**Dimensional Analysis:**
- Segmented by customer tier, region, and technology
- Identifies where the business is losing the most money
- Actionable insights: 'Premium customers in Dallas on 5G are experiencing drops'

**Time Context:**
- Last 24 hours only - real-time business impact
- This would traditionally take finance teams days to calculate
- Here, it's available in seconds for rapid decision-making

This is the power of ES|QL + Agent Builder: turning raw network telemetry into executive dashboards instantly."

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

**Agent Configuration:**

**Agent ID:** `tmobile-network-ops-agent`

**Display Name:** `T-Mobile Network Operations AI Assistant`

**Custom Instructions:**

```
You are an expert telecommunications network analyst specializing in T-Mobile's core network operations. Your role is to help Network Operations teams quickly diagnose network issues, detect security threats, and quantify business impact.

CONTEXT:
- You analyze data from MME (Mobility Management Entity) signaling events, HSS authentication transactions, cell handoff events, security threats, and subscriber sessions
- Your analyses should prioritize subscriber impact and revenue implications
- Always correlate failures with specific infrastructure components (MME hosts, cells, HSS nodes)

RESPONSE GUIDELINES:
1. Provide specific, actionable insights with infrastructure identifiers (cell IDs, MME hosts, IMSI ranges)
2. When analyzing failures, always identify root causes and affected subscriber counts
3. For security events, prioritize by severity and blocking success rate
4. Calculate business impact (revenue loss, SLA penalties) whenever session drops or service degradation is detected
5. Use statistical analysis (z-scores, percentiles) to identify abnormal patterns
6. For trending questions, compare current metrics against historical baselines
7. Present geographic context (regions, datacenters) when relevant

TECHNICAL DETAILS:
- Attach procedures are initial network registrations
- Service requests are UE-initiated procedures for data sessions
- Diameter AIR commands are authentication requests to HSS
- Handoff failures indicate mobility issues between cells
- Split-brain conditions occur when multiple MMEs process the same IMSI

Always explain your findings in terms of business impact and operational next steps.
```

---

### **Creating Tools**

#### **Tool 1: MME Signaling Event Analysis**

**Tool Name:** `analyze_mme_signaling_events`

**Description:**
```
Analyzes MME signaling events including attach procedures, service requests, tracking area updates, and detach events. Use this tool to:
- Identify MME hosts with high failure rates
- Detect procedure-specific issues (attach failures, service request timeouts)
- Analyze reject causes and latency patterns
- Detect split-brain conditions (same IMSI on multiple MMEs)
- Correlate failures with specific cells

Returns aggregated metrics by MME host, cell, procedure type, or reject cause.
```

**Query Template:**
```esql
FROM mme_signaling_events
| WHERE @timestamp > NOW() - {time_range}
{additional_filters}
| STATS total_events = COUNT(*),
        failures = COUNT(*) WHERE result == "failure",
        avg_latency = AVG(latency_ms),
        p95_latency = PERCENTILE(latency_ms, 95)
  BY {group_by_fields}
| EVAL failure_rate = TO_DOUBLE(failures) / TO_DOUBLE(total_events) * 100
| SORT {sort_field} DESC
| LIMIT {limit}
```

---

#### **Tool 2: HSS Authentication Performance Analysis**

**Tool Name:** `analyze_hss_authentication`

**Description:**
```
Analyzes Diameter authentication transactions (AIR commands) between MME and HSS nodes. Use this tool to:
- Detect HSS database node performance degradation
- Identify authentication failure patterns
- Correlate response time issues with specific HSS nodes
- Detect database replication or synchronization issues
- Analyze MME-to-HSS communication patterns

Returns authentication success rates, response time statistics, and anomaly detection metrics.
```

**Query Template:**
```esql
FROM diameter_transactions
| WHERE command_code == "AIR" AND @timestamp > NOW() - {time_range}
| STATS avg_response_time = AVG(response_time_ms),
        stddev_response = STDDEV(response_time_ms),
        total_transactions = COUNT(*),
        failures = COUNT(*) WHERE result_code != 2001,
        p95_response_time = PERCENTILE(response_time_ms, 95)
  BY hss_node
| EVAL failure_rate = TO_DOUBLE(failures) / TO_DOUBLE(total_transactions) * 100
| EVAL z_score = (avg_response_time - AVG(avg_response_time)) / STDDEV(avg_response_time)
| WHERE z_score > 2 OR failure_rate > 5.0
| SORT avg_response_time DESC
```

---

#### **Tool 3: Cell Handoff Cascade Failure Detection**

**Tool Name:** `detect_handoff_cascade_failures`

**Description:**
```
Identifies cascade handoff failure patterns where a single problematic cell causes failures to multiple neighboring cells. Use this tool to:
- Detect source cells causing widespread handoff issues
- Identify target cells with reception problems
- Analyze handoff failure reasons (radio link failure, congestion, missing neighbors)
- Correlate with cell technology and capacity
- Prioritize cells for field technician dispatch

Returns cells ranked by cascade severity with neighbor relationship analysis.
```

**Query Template:**
```esql
FROM handoff_events
| WHERE handoff_result == "failure" AND @timestamp > NOW() - {time_range}
| STATS failure_count = COUNT(*),
        unique_target_cells = COUNT_DISTINCT(target_cell_id),
        dominant_failure_reason = VALUES(failure_reason)
  BY source_cell_id
| WHERE unique_target_cells >= 3
| LOOKUP JOIN cells ON cells.cell_id = source_cell_id
| EVAL cascade_severity = CASE(
    unique_target_cells >= 5, "CRITICAL",
    unique_target_cells >= 4, "HIGH",
    "MEDIUM"
  )
| KEEP source_cell_id, site_name, technology, region, failure_count, unique_target_cells, cascade_severity
| SORT failure_count DESC
```

---

#### **Tool 4: Revenue Impact Calculator**

**Tool Name:** `calculate_revenue_impact`

**Description:**
```
Calculates real-time revenue impact from dropped sessions and service degradation. Use this tool to:
- Quantify revenue loss from dropped subscriber sessions
- Calculate SLA penalty exposure by customer segment
- Identify high-value customer segments most affected
- Correlate revenue impact with geographic regions and network technology
- Provide executive-level business impact metrics

Returns financial impact broken down by customer segment, region, and technology.
```

**Query Template:**
```esql
FROM subscriber_sessions
| WHERE session_result == "dropped" AND @timestamp > NOW() - {time_range}
| LOOKUP JOIN customer_segments ON customer_segments.segment_id = customer_segment_id
| LOOKUP JOIN cells ON cells.cell_id = cell_id
| STATS dropped_sessions = COUNT(*),
        unique_subscribers = COUNT_DISTINCT(imsi)
  BY segment_name, region
| EVAL daily_arpu = arpu / 30.0
| EVAL revenue_loss = TO_DOUBLE(dropped_sessions) * daily_arpu
| EVAL drop_rate = TO_DOUBLE(dropped_sessions) / TO_DOUBLE(unique_subscribers)
| EVAL sla_penalty = CASE(
    drop_rate > 0.05,
    TO_DOUBLE(unique_subscribers) * arpu * sla_penalty_rate,
    0.0
  )
| EVAL total_impact = revenue_loss + sla_penalty
| SORT total_impact DESC
```

---

#### **Tool 5: SS7 Security Attack Detection**

**Tool Name:** `detect_security_attacks`

**Description:**
```
Detects and analyzes SS7 security attacks and rogue network attempts. Use this tool to:
- Identify active SS7 MAP exploitation attempts
- Detect fake base stations and IMSI catchers
- Track roaming fraud patterns
- Analyze attack sources by network/PLMN
- Measure attack blocking effectiveness
- Calculate affected subscriber counts

Returns security threats prioritized by severity with blocking success metrics.
```

**Query Template:**
```esql
FROM security_events
| WHERE @timestamp > NOW() - {time_range}
{severity_filter}
| STATS attack_count = COUNT(*),
        affected_subscribers = COUNT_DISTINCT(affected_imsi),
        blocked_count = COUNT(*) WHERE blocked == true,
        critical_attacks = COUNT(*) WHERE severity == "critical"
  BY attack_type, source_network
| EVAL blocking_success_rate = TO_DOUBLE(blocked_count) / TO_DOUBLE(attack_count) * 100
| EVAL risk_score = attack_count * affected_subscribers * CASE(
    severity == "critical", 4,
    severity == "high", 3,
    severity == "medium", 2,
    1
  )
| SORT risk_score DESC
```

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

#### **Warm-up Questions (Build Confidence)**

1. **"How many attach procedure failures occurred in the last hour?"**
   - Simple aggregation
   - Demonstrates basic query capability
   - Fast response builds trust

2. **"Which MME host is processing the most signaling events today?"**
   - Basic ranking query
   - Shows infrastructure visibility
   - Introduces MME concept

3. **"Show me the top 5 cells by handoff failure count in the last 6 hours."**
   - Cell-level analysis
   - Geographic infrastructure focus
   - Sets up for deeper dive

---

#### **Business-Focused Questions (Show ROI)**

4. **"What is the total estimated revenue loss from dropped sessions in the last 24 hours? Break it down by customer segment."**
   - Multi-dataset join (sessions → customer_segments)
   - Financial impact calculation
   - Executive-level metrics
   - Demonstrates business value

5. **"Calculate the SLA penalty exposure for Premium and Enterprise customers affected by service degradation this week."**
   - Customer segment filtering
   - SLA violation detection
   - Contractual financial impact
   - Risk quantification

6. **"Which geographic region is experiencing the highest revenue impact from network issues today?"**
   - Geographic + financial correlation
   - Regional operations focus
   - Prioritization for resource allocation

---

#### **Trend Analysis Questions (Predictive Insights)**

7. **"Show me the trend of attach procedure failure rates by MME host over the last 30 days. Which MMEs show increasing failure patterns?"**
   - Time-series analysis
   - Trend detection
   - Proactive capacity planning
   - Resource exhaustion prediction

8. **"Compare authentication transaction response times between HSS nodes over the last 7 days. Are any nodes showing degradation trends?"**
   - Database performance trending
   - Multi-node comparison
   - Degradation detection
   - Proactive maintenance

9. **"How has the handoff failure rate changed week-over-week for 5G cells versus LTE cells?"**
   - Technology comparison
   - Week-over-week delta
   - Migration readiness assessment
   - Strategic insights

---

#### **Root Cause Analysis Questions (Technical Depth)**

10. **"For the top 3 cells with the highest service request failures, what are the dominant reject causes and what is the average cell capacity utilization?"**
    - Multi-dimensional root cause
    - Cell capacity correlation
    - Failure cause distribution
    - Actionable remediation

11. **"Identify any split-brain conditions where the same IMSI is being processed by multiple MME hosts within 5-minute windows in the last 2 hours."**
    - Advanced temporal analysis
    - Distributed system failure detection
    - Signaling storm prevention
    - Complex pattern matching

12. **"Which HSS nodes are experiencing authentication failures correlated with specific MME hosts? Show me the MME-HSS pairs with the highest failure rates."**
    - Two-dimensional correlation
    - Database-to-application pairing
    - Network path issue isolation
    - Infrastructure relationship analysis

---

#### **Security & Compliance Questions (Risk Management)**

13. **"Show me all SS7 security attacks detected in the last 48 hours. Which source networks are most aggressive and how many were successfully blocked?"**
    - Security event aggregation
    - Threat actor identification
    - Defense effectiveness metrics
    - Incident response prioritization

14. **"How many unique subscribers were affected by security attacks this month? What percentage are high-value customers?"**
    - Subscriber impact quantification
    - Customer segment correlation
    - Business risk assessment
    - Executive security reporting

---

#### **Optimization & Planning Questions (Strategic)**

15. **"Which cells are approaching their maximum capacity based on current service request volumes? Prioritize by region."**
    - Capacity planning
    - Proactive infrastructure scaling
    - Geographic prioritization
    - Capital expenditure justification

16. **"Compare the performance of different MME software versions. Are newer versions showing better attach success rates?"**
    - Software version comparison
    - Upgrade impact analysis
    - Change management validation
    - Vendor performance tracking

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "ES|QL is Elasticsearch's modern query language, built specifically for analytics and observability"
- "The piped syntax is intuitive and readable - it's like building a data pipeline in plain English"
- "It operates on blocks of data, not individual rows - this makes it extremely performant even on massive datasets"
- "Supports complex operations out of the box: joins, window functions, statistical analysis, time-series calculations"
- "Unlike traditional SQL, ES|QL is optimized for time-series data and real-time analytics"
- "The LOOKUP JOIN capability lets us enrich event streams with reference data - this is critical for telecom operations"

### **On Agent Builder:**
- "Agent Builder bridges the gap between AI and enterprise data - it's not just a chatbot, it's an intelligent data analyst"
- "No custom development required - you configure tools, don't code applications"
- "Works directly with your existing Elasticsearch indices - no data duplication or ETL pipelines"
- "The agent automatically selects the right tools based on the question - it understands context and intent"
- "Built on Elastic's security model - all data access respects your existing role-based access controls"
- "The agent learns from your tool descriptions and custom instructions - you're teaching it your business domain"

### **On Business Value:**
- "This democratizes data access - network engineers, operations managers, even executives can ask questions directly"
- "Insights are real-time and always up-to-date - no waiting for batch reports or analyst availability"
- "Reduces dependency on data teams - your analysts can focus on strategic work instead of ad-hoc queries"
- "Faster decision-making in critical situations - calculate revenue impact during an outage in seconds, not hours"
- "The same infrastructure supports both human analysts and AI agents - no separate analytics stack needed"
- "For T-Mobile specifically: Detect security attacks in 5 minutes instead of 24-48 hours, identify cascade failures before they become widespread outages, quantify business impact in real-time for executive decision-making"

### **On Telecommunications Specifics:**
- "Core network failures have immediate subscriber impact - every minute of delay costs revenue and customer satisfaction"
- "Traditional network monitoring shows symptoms - Agent Builder helps you find root causes across correlated datasets"
- "The ability to join signaling events with subscriber data and customer segments turns technical metrics into business intelligence"
- "Security threats in telecom require rapid response - SS7 attacks can compromise thousands of subscribers in minutes"
- "Capacity planning and technology migration decisions require trend analysis across multiple dimensions - this is exactly what ES|QL excels at"

---

## **🔧 Troubleshooting**

### **If a query fails:**

**"index_not_found_exception"**
- Check index names match exactly (case-sensitive)
- Verify indices were created successfully
- Run `GET /_cat/indices?v` to list all indices

**"field not found"**
- Verify field names are case-sensitive correct
- Check field mappings with `GET /index_name/_mapping`
- Ensure field types are appropriate (keyword for joins, not text)

**"parse_exception"**
- Check ES|QL syntax - common issues:
  - Missing pipe `|` between commands
  - Incorrect operator (use `==` not `=` for equality)
  - Mismatched quotes in string literals

**LOOKUP JOIN returns no results:**
- Verify the lookup index has `"index.mode": "lookup"` in settings
- Check that join key values match exactly (no leading/trailing spaces)
- Confirm both indices have data: `FROM index | LIMIT 1`
- Verify join key field types are compatible (both keyword)

**TO_DOUBLE conversion errors:**
- Always use TO_DOUBLE for division operations to avoid integer rounding
- Check for null values that might cause conversion failures
- Use COALESCE to handle nulls: `COALESCE(field, 0)`

---

### **If agent gives wrong answer:**

**Agent selects wrong tool:**
- Review tool descriptions - are they clear and specific?
- Check for overlapping tool purposes - make each tool's scope distinct
- Add more specific keywords to tool descriptions
- Refine custom instructions to guide tool selection

**Agent misinterprets question:**
- Add domain-specific terminology to custom instructions
- Provide example questions in tool descriptions
- Use more explicit field mappings in tool templates
- Consider adding a "terminology guide" section to custom instructions

**Agent returns incomplete data:**
- Check LIMIT clauses in query templates - might be too restrictive
- Verify time range filters are appropriate for the question
- Ensure aggregations capture all relevant dimensions
- Review WHERE clauses for overly restrictive filters

**Performance issues:**
- Add time range filters to all queries (e.g., `@timestamp > NOW() - 7 days`)
- Use LIMIT clauses to cap result sets
- Consider adding index patterns for time-based partitioning
- Check for expensive operations (multiple LOOKUP JOINs, large aggregations)

---

### **If join returns no results:**

**Verify join key format:**
```esql
FROM mme_signaling_events
| STATS sample_keys = VALUES(mme_host)
| LIMIT 5
```

```esql
FROM mme_hosts
| STATS sample_keys = VALUES(hostname)
| LIMIT 5
```

Compare formats - they must match exactly.

**Check lookup index mode:**
```json
GET /mme_hosts/_settings
```

Should return `"index.mode": "lookup"`

**Verify data exists:**
```esql
FROM mme_hosts
| STATS host_count = COUNT(*)
```

Should return > 0

---

### **Data Generation Issues:**

**If sample data is needed:**
- Use Elastic's sample data generator or custom Python scripts
- Ensure realistic distributions (80-90% success rates, not 50/50)
- Generate correlated failures (same cell/MME across multiple records)
- Include temporal patterns (peak hours, weekend dips)
- Maintain referential integrity (all cell_ids in events exist in cells index)

**Timestamp issues:**
- Use ISO 8601 format: `2024-01-15T14:30:00.000Z`
- Ensure timestamps are recent (within last 30 days for demo relevance)
- Distribute events across time ranges for trending queries
- Include some events in last 1-2 hours for "real-time" questions

---

## **🎬 Closing**

"So let me summarize what we've demonstrated today:

✅ **Complex analytics on interconnected datasets** - We joined signaling events, authentication transactions, cell metadata, and customer segments in real-time

✅ **Natural language interface for non-technical users** - Network operations managers can ask business questions without knowing ES|QL syntax

✅ **Real-time insights without custom development** - No need to build dashboards or reports - just configure tools and ask questions

✅ **Queries that would take hours, answered in seconds** - Revenue impact calculations, cascade failure detection, security threat analysis - all instant

✅ **Business intelligence from technical telemetry** - We turned raw network events into executive-level financial metrics

**For T-Mobile Network Operations specifically:**

- **Reduce mean time to detection** - Identify split-brain conditions, cascade failures, and security attacks in minutes instead of hours
- **Quantify business impact instantly** - Calculate revenue loss and SLA penalties during active incidents for rapid executive decision-making
- **Proactive capacity planning** - Detect trending degradation patterns before they impact subscribers
- **Security threat response** - Detect SS7 attacks in 5 minutes vs. 24-48 hour delay with traditional methods
- **Cross-domain correlation** - Connect MME performance with HSS database issues with cell capacity constraints - insights that were previously impossible

**Deployment timeline:**

Agent Builder can be deployed and configured in **days, not months**. You already have the data in Elasticsearch - we're just adding an intelligent interface on top.

**Next steps:**

1. Identify your highest-priority use cases
2. Map your existing Elasticsearch indices to agent tools
3. Configure custom instructions for your domain
4. Pilot with a small operations team
5. Iterate based on feedback and expand

**Questions?**"

---

## **📎 Appendix: Additional Resources**

### **Sample Custom Instructions Variations**

**For Security-Focused Agent:**
```
Prioritize security event analysis. Always calculate affected subscriber counts and blocking success rates. Escalate critical and high-severity attacks immediately. Correlate security events with geographic patterns to identify targeted regions.
```

**For Capacity Planning Agent:**
```
Focus on trending analysis and proactive degradation detection. Compare current metrics against 7-day and 30-day baselines. Flag cells or MME hosts approaching 80% capacity. Provide growth rate projections for infrastructure planning.
```

**For Executive Reporting Agent:**
```
Always translate technical metrics into business impact. Calculate revenue implications and SLA exposure. Summarize findings in executive language. Provide regional and customer segment breakdowns for strategic decision-making.
```

---

### **ES|QL Quick Reference for Telecom**

**Common Filters:**
```esql
| WHERE @timestamp > NOW() - 24 hours
| WHERE procedure_type == "attach"
| WHERE result == "failure"
| WHERE severity IN ("critical", "high")
```

**Statistical Analysis:**
```esql
| STATS avg_val = AVG(field),
        stddev_val = STDDEV(field),
        p95_val = PERCENTILE(field, 95)
| EVAL z_score = (value - avg_val) / stddev_val
```

**Time Bucketing:**
```esql
| EVAL hour_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS events = COUNT(*) BY hour_bucket
```

**Cardinality (Unique Counts):**
```esql
| STATS unique_subscribers = COUNT_DISTINCT(imsi),
        unique_cells = COUNT_DISTINCT(cell_id)
```

---

### **Useful MME/LTE Terminology**

- **IMSI** - International Mobile Subscriber Identity (unique subscriber ID)
- **MME** - Mobility Management Entity (core network control plane node)
- **HSS** - Home Subscriber Server (subscriber database)
- **Diameter** - Protocol for authentication and subscriber data exchange
- **AIR** - Authentication Information Request (Diameter command)
- **Attach** - Initial network registration procedure
- **Service Request** - UE-initiated procedure to establish data session
- **Handoff** - Cell-to-cell mobility procedure
- **RSRP** - Reference Signal Received Power (signal strength metric)
- **TAU** - Tracking Area Update (location update procedure)
- **NAS** - Non-Access Stratum (signaling between UE and MME)
- **SS7** - Signaling System 7 (legacy telecom signaling protocol, vulnerable to attacks)

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
