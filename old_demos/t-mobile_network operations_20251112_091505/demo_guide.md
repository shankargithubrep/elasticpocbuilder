# **Elastic Agent Builder Demo for T-Mobile**

## **Internal Demo Script & Reference Guide**

---

## **📋 Demo Overview**

**Total Time:** 25-30 minutes
**Audience:** Network Operations technical/business stakeholders
**Goal:** Show how Agent Builder enables AI-powered analytics on T-Mobile telecommunications data

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## **🗂️ Dataset Architecture**

### **Timeseries Event Datasets**

#### **lte_s1ap_events** (1,000,000+ records)
Primary timeseries dataset capturing LTE S1 Application Protocol events between eNodeB and MME.

**Primary Key:** `event_id` (unique per event)

**Key Fields:**
- `@timestamp` - Event timestamp (ISO 8601)
- `imsi` - International Mobile Subscriber Identity (15 digits)
- `procedure_type` - S1AP procedure (ATTACH, HANDOVER, SERVICE_REQUEST, DETACH, etc.)
- `cell_id` - Cell tower identifier (links to cell_tower_reference)
- `mme_host` - MME hostname (links to mme_host_reference)
- `cause_code` - Failure cause code (links to cause_code_reference)
- `status` - SUCCESS or FAILURE
- `handover_type` - X2, S1, INTRA_CELL (for handover procedures)
- `target_cell_id` - Destination cell for handovers

**Relationships:**
- → `cell_tower_reference` (via cell_id)
- → `mme_host_reference` (via mme_host)
- → `cause_code_reference` (via cause_code)

---

#### **hss_authentication_events** (500,000+ records)
HSS (Home Subscriber Server) authentication and authorization events.

**Primary Key:** `auth_event_id`

**Key Fields:**
- `@timestamp` - Authentication timestamp
- `imsi` - Subscriber identity
- `hss_node` - HSS node identifier (links to hss_node_reference)
- `auth_result` - SUCCESS, FAILURE, TIMEOUT
- `failure_reason` - Detailed failure code
- `database_response_time_ms` - Database query latency
- `vector_generation_time_ms` - Authentication vector generation time

**Relationships:**
- → `hss_node_reference` (via hss_node)

---

#### **signaling_link_metrics** (200,000+ records)
SCTP signaling link performance metrics between network elements.

**Primary Key:** `metric_id`

**Key Fields:**
- `@timestamp` - Measurement timestamp
- `mme_host` - MME endpoint (links to mme_host_reference)
- `messages_per_second` - Message rate
- `error_rate` - Percentage of errors
- `sctp_retransmissions` - SCTP retransmission count
- `active_associations` - Number of active SCTP associations
- `cpu_utilization_percent` - MME CPU usage
- `memory_utilization_percent` - MME memory usage
- `active_subscribers` - Current subscriber count

**Relationships:**
- → `mme_host_reference` (via mme_host)

---

#### **ss7_security_events** (50,000+ records)
SS7 signaling security events and potential attack indicators.

**Primary Key:** `security_event_id`

**Key Fields:**
- `@timestamp` - Detection timestamp
- `originating_network` - Source network code
- `destination_imsi` - Target subscriber
- `message_type` - SS7 message type (MAP, CAMEL, etc.)
- `attack_signature` - Detected signature ID (links to threat_signature_reference)
- `severity` - CRITICAL, HIGH, MEDIUM, LOW
- `blocked` - true/false (was it blocked)

**Relationships:**
- → `threat_signature_reference` (via attack_signature)

---

### **Reference Datasets**

#### **cell_tower_reference** (5,000+ records)
Cell tower and site configuration data.

**Primary Key:** `cell_id`

**Key Fields:**
- `cell_id` - Unique cell identifier
- `site_name` - Physical site name
- `latitude` - Geographic coordinate
- `longitude` - Geographic coordinate
- `region` - Network region (WEST, EAST, CENTRAL, etc.)
- `technology` - LTE, 5G_NSA, 5G_SA
- `neighbor_cells` - Array of adjacent cell_ids
- `capacity` - Maximum subscribers
- `status` - ACTIVE, MAINTENANCE, DEGRADED

---

#### **mme_host_reference** (50+ records)
MME (Mobility Management Entity) host configuration.

**Primary Key:** `mme_host`

**Key Fields:**
- `mme_host` - Hostname
- `datacenter` - Physical datacenter location
- `mme_pool` - Pool identifier for load balancing
- `role` - PRIMARY, BACKUP, STANDBY
- `software_version` - MME software release
- `capacity_tier` - SMALL, MEDIUM, LARGE (subscriber capacity)
- `max_subscribers` - Maximum subscriber capacity

---

#### **cause_code_reference** (500+ records)
S1AP and LTE cause code definitions.

**Primary Key:** `cause_code`

**Key Fields:**
- `cause_code` - Numeric cause code
- `cause_description` - Human-readable description
- `category` - RADIO, TRANSPORT, NAS, PROTOCOL, MISC
- `severity` - CRITICAL, MAJOR, MINOR, INFO
- `recommended_action` - Troubleshooting guidance
- `user_impacting` - true/false

---

#### **hss_node_reference** (20+ records)
HSS node configuration and cluster information.

**Primary Key:** `hss_node`

**Key Fields:**
- `hss_node` - HSS node identifier
- `datacenter` - Physical location
- `cluster_id` - HSS cluster for replication
- `database_type` - ORACLE, CASSANDRA, etc.
- `replication_status` - HEALTHY, DEGRADED, FAILED
- `subscriber_capacity` - Maximum subscribers

---

#### **threat_signature_reference** (1,000+ records)
SS7 security threat signatures and attack patterns.

**Primary Key:** `attack_signature`

**Key Fields:**
- `attack_signature` - Signature identifier
- `threat_name` - Attack name
- `threat_category` - LOCATION_TRACKING, INTERCEPTION, FRAUD, DOS
- `threat_description` - Detailed description
- `mitigation_strategy` - Recommended countermeasures
- `cve_references` - Related CVE identifiers

---

## **🚀 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

**CRITICAL: All indexes need "index.mode": "lookup" for joins to work**

Navigate to **Kibana → Dev Tools** and execute these commands:

#### **1. Create lte_s1ap_events index**

```json
PUT lte_s1ap_events
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "event_id": { "type": "keyword" },
      "imsi": { "type": "keyword" },
      "procedure_type": { "type": "keyword" },
      "cell_id": { "type": "keyword" },
      "mme_host": { "type": "keyword" },
      "cause_code": { "type": "keyword" },
      "status": { "type": "keyword" },
      "handover_type": { "type": "keyword" },
      "target_cell_id": { "type": "keyword" }
    }
  }
}
```

Upload CSV via **Kibana → Machine Learning → Data Visualizer → Upload File** → Select `lte_s1ap_events.csv` → Import to `lte_s1ap_events` index.

---

#### **2. Create hss_authentication_events index**

```json
PUT hss_authentication_events
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "auth_event_id": { "type": "keyword" },
      "imsi": { "type": "keyword" },
      "hss_node": { "type": "keyword" },
      "auth_result": { "type": "keyword" },
      "failure_reason": { "type": "keyword" },
      "database_response_time_ms": { "type": "integer" },
      "vector_generation_time_ms": { "type": "integer" }
    }
  }
}
```

Upload `hss_authentication_events.csv` to this index.

---

#### **3. Create signaling_link_metrics index**

```json
PUT signaling_link_metrics
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "metric_id": { "type": "keyword" },
      "mme_host": { "type": "keyword" },
      "messages_per_second": { "type": "integer" },
      "error_rate": { "type": "float" },
      "sctp_retransmissions": { "type": "integer" },
      "active_associations": { "type": "integer" },
      "cpu_utilization_percent": { "type": "float" },
      "memory_utilization_percent": { "type": "float" },
      "active_subscribers": { "type": "integer" }
    }
  }
}
```

Upload `signaling_link_metrics.csv` to this index.

---

#### **4. Create ss7_security_events index**

```json
PUT ss7_security_events
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "security_event_id": { "type": "keyword" },
      "originating_network": { "type": "keyword" },
      "destination_imsi": { "type": "keyword" },
      "message_type": { "type": "keyword" },
      "attack_signature": { "type": "keyword" },
      "severity": { "type": "keyword" },
      "blocked": { "type": "boolean" }
    }
  }
}
```

Upload `ss7_security_events.csv` to this index.

---

#### **5. Create cell_tower_reference index (LOOKUP MODE)**

```json
PUT cell_tower_reference
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
      "region": { "type": "keyword" },
      "technology": { "type": "keyword" },
      "neighbor_cells": { "type": "keyword" },
      "capacity": { "type": "integer" },
      "status": { "type": "keyword" }
    }
  }
}
```

Upload `cell_tower_reference.csv` to this index.

---

#### **6. Create mme_host_reference index (LOOKUP MODE)**

```json
PUT mme_host_reference
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "mme_host": { "type": "keyword" },
      "datacenter": { "type": "keyword" },
      "mme_pool": { "type": "keyword" },
      "role": { "type": "keyword" },
      "software_version": { "type": "keyword" },
      "capacity_tier": { "type": "keyword" },
      "max_subscribers": { "type": "integer" }
    }
  }
}
```

Upload `mme_host_reference.csv` to this index.

---

#### **7. Create cause_code_reference index (LOOKUP MODE)**

```json
PUT cause_code_reference
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "cause_code": { "type": "keyword" },
      "cause_description": { "type": "text" },
      "category": { "type": "keyword" },
      "severity": { "type": "keyword" },
      "recommended_action": { "type": "text" },
      "user_impacting": { "type": "boolean" }
    }
  }
}
```

Upload `cause_code_reference.csv` to this index.

---

#### **8. Create hss_node_reference index (LOOKUP MODE)**

```json
PUT hss_node_reference
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "hss_node": { "type": "keyword" },
      "datacenter": { "type": "keyword" },
      "cluster_id": { "type": "keyword" },
      "database_type": { "type": "keyword" },
      "replication_status": { "type": "keyword" },
      "subscriber_capacity": { "type": "integer" }
    }
  }
}
```

Upload `hss_node_reference.csv` to this index.

---

#### **9. Create threat_signature_reference index (LOOKUP MODE)**

```json
PUT threat_signature_reference
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "attack_signature": { "type": "keyword" },
      "threat_name": { "type": "keyword" },
      "threat_category": { "type": "keyword" },
      "threat_description": { "type": "text" },
      "mitigation_strategy": { "type": "text" },
      "cve_references": { "type": "keyword" }
    }
  }
}
```

Upload `threat_signature_reference.csv` to this index.

---

### **Step 2: Verify Data Upload**

Run these quick checks in Dev Tools:

```esql
FROM lte_s1ap_events
| LIMIT 1
```

```esql
FROM cell_tower_reference
| LIMIT 1
```

Verify you get results from both timeseries and reference datasets.

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to your AI Agent chat interface
- Have the agent already configured with all tools

### **Demo Script**

**Presenter:** "Before we dive into how this works, let me show you the end result. I'm going to ask our AI agent complex network operations questions that would normally require deep technical expertise and hours of manual analysis."

**Sample questions to demonstrate:**

1. **ROI/Business Impact Question:**
   - *"What is the financial impact of the top 3 cell tower failure patterns over the last 24 hours? Calculate based on average revenue per subscriber of $50/month and estimated outage duration."*
   
   **Why this is impressive:** Agent performs multi-dataset joins, calculates business metrics, and provides executive-ready answers.

2. **Trend Detection Question:**
   - *"Show me any unusual spikes in unique IMSI counts or cell ID cardinality over the past 6 hours. Compare against historical patterns and flag anomalies."*
   
   **Why this is impressive:** Agent understands time-series analysis, lag calculations, and anomaly detection without explicit instructions.

3. **Root Cause Analysis:**
   - *"We're seeing authentication failures spike on HSS cluster WEST-02. What's the root cause and which specific database nodes are affected?"*
   
   **Why this is impressive:** Agent correlates across multiple datasets (HSS events + node reference), identifies patterns, and provides enriched context.

4. **Security Threat Detection:**
   - *"Are there any SS7 security attacks targeting our subscribers in the last hour? Include threat category, severity, and recommended mitigation actions."*
   
   **Why this is impressive:** Agent joins security events with threat intelligence, prioritizes by severity, and provides actionable guidance.

5. **Predictive/Proactive Question:**
   - *"Which MME hosts are showing early signs of resource exhaustion? Include CPU, memory, active subscriber counts, and capacity tier."*
   
   **Why this is impressive:** Agent analyzes resource metrics against capacity baselines to predict issues before they impact customers.

6. **Complex Cascade Failure Analysis:**
   - *"Detect any cell tower handoff cascade failures where neighbor cells are experiencing coordinated failures affecting 500+ subscribers."*
   
   **Why this is impressive:** Agent performs graph-like analysis across neighbor relationships, identifies cascade patterns, and quantifies subscriber impact.

7. **Network Split-Brain Detection:**
   - *"Are there any signs of core network split-brain or signaling storms? Look for message rate spikes, elevated error rates, and SCTP retransmission patterns across MME pools."*
   
   **Why this is impressive:** Agent correlates multiple signal types (message rates, errors, retransmissions) across distributed systems to identify complex failure modes.

**After demonstrating 2-3 questions:**

**Presenter:** "Notice how the agent:
- Understood natural language questions
- Automatically selected the right datasets
- Performed complex joins and calculations
- Provided business-relevant context
- Gave actionable recommendations

**Transition:** "So how does this actually work? Let's go under the hood and build these queries from scratch using ES|QL."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open Kibana Dev Tools Console
- Have the indices already created and populated

---

### **Query 1: Simple Aggregation (2 minutes)**

**Presenter:** "T-Mobile Network Operations wants to know: What are the top failure procedures in the last hour, and how many subscribers are affected?"

**Copy/paste into console:**

```esql
FROM lte_s1ap_events
| WHERE @timestamp > NOW() - 1 hour AND status == "FAILURE"
| STATS failure_count = COUNT(*), unique_subscribers = COUNT_DISTINCT(imsi) BY procedure_type
| SORT failure_count DESC
| LIMIT 10
```

**Run and narrate results:** "This is basic ES|QL:
- **FROM**: Source our LTE S1AP events
- **WHERE**: Filter to failures in the last hour
- **STATS**: Aggregate failure counts and unique subscriber counts by procedure type
- **SORT and LIMIT**: Show top 10 procedures by failure volume

The syntax is intuitive - it reads like English. We can immediately see which procedures are causing the most problems and how many subscribers are impacted."

---

### **Query 2: Add Calculations with EVAL (3 minutes)**

**Presenter:** "Let's add calculations to detect sustained spike patterns - comparing current activity against previous time periods to identify anomalies."

**Copy/paste:**

```esql
FROM lte_s1ap_events
| WHERE @timestamp > NOW() - 30 minutes
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    unique_imsi = COUNT_DISTINCT(imsi),
    unique_cells = COUNT_DISTINCT(cell_id),
    total_events = COUNT(*)
  BY time_bucket
| SORT time_bucket ASC
| EVAL 
    imsi_change_1 = TO_DOUBLE(unique_imsi) - LAG(unique_imsi, 1),
    imsi_change_2 = TO_DOUBLE(unique_imsi) - LAG(unique_imsi, 2),
    cell_change_1 = TO_DOUBLE(unique_cells) - LAG(unique_cells, 1),
    cell_change_2 = TO_DOUBLE(unique_cells) - LAG(unique_cells, 2)
| WHERE imsi_change_1 > 400 OR imsi_change_2 > 280 OR cell_change_1 > 50 OR cell_change_2 > 25
```

**Run and highlight:** "Key additions:
- **DATE_TRUNC**: Bucket events into 5-minute intervals
- **EVAL with LAG**: Compare current counts against 1-lag and 2-lag periods
- **TO_DOUBLE**: Critical for decimal math operations
- **Multi-condition WHERE**: Flag anomalies based on spike thresholds

This detects sustained spike patterns that indicate mass events, network issues, or potential attacks. The lag analysis ensures we're not just seeing normal variance."

---

### **Query 3: Join Datasets with LOOKUP JOIN (3 minutes)**

**Presenter:** "Now let's combine data from multiple sources to get enriched context. We'll analyze HSS authentication failures and enrich them with HSS node configuration details."

**Copy/paste:**

```esql
FROM hss_authentication_events
| WHERE @timestamp > NOW() - 30 minutes AND auth_result == "FAILURE"
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*),
    unique_subscribers = COUNT_DISTINCT(imsi),
    avg_db_response_ms = AVG(database_response_time_ms)
  BY time_bucket, hss_node
| WHERE failure_count > 200
| LOOKUP JOIN hss_node_reference ON hss_node
| EVAL health_status = CASE(
    replication_status == "FAILED", "CRITICAL",
    replication_status == "DEGRADED", "WARNING",
    "HEALTHY"
  )
| SORT failure_count DESC
| KEEP time_bucket, hss_node, datacenter, cluster_id, database_type, replication_status, 
       failure_count, unique_subscribers, avg_db_response_ms, health_status
```

**Run and explain:** "Magic happening here:
- **LOOKUP JOIN**: Combines authentication events with HSS node reference data
- We now have access to datacenter, cluster_id, database_type, and replication_status
- **CASE statement**: Creates a health_status field based on replication status
- This is a **LEFT JOIN**: All failure records kept, enriched with node configuration details
- **CRITICAL**: For LOOKUP JOIN to work, hss_node_reference must have 'index.mode: lookup'

This tells us not just THAT authentication is failing, but WHY - we can see database replication issues, specific clusters affected, and datacenter locations for immediate remediation."

---

### **Query 4: Complex Multi-Dataset Analytics (2 minutes)**

**Presenter:** "For the grand finale - a sophisticated analytical query showing cell tower handoff cascade failure detection with geographic enrichment and neighbor cell analysis."

**Copy/paste:**

```esql
FROM lte_s1ap_events
| WHERE @timestamp > NOW() - 30 minutes 
  AND procedure_type == "HANDOVER" 
  AND status == "FAILURE"
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    handover_failures = COUNT(*),
    unique_subscribers = COUNT_DISTINCT(imsi),
    unique_source_cells = COUNT_DISTINCT(cell_id),
    unique_target_cells = COUNT_DISTINCT(target_cell_id)
  BY time_bucket, cell_id
| WHERE handover_failures > 50 AND unique_subscribers > 100
| LOOKUP JOIN cell_tower_reference ON cell_id
| RENAME site_name AS source_site, region AS source_region, 
         latitude AS source_lat, longitude AS source_lon,
         status AS source_status
| EVAL cascade_risk = CASE(
    unique_target_cells > 5, "HIGH",
    unique_target_cells > 3, "MEDIUM",
    "LOW"
  )
| EVAL geographic_key = CONCAT(source_region, "-", TO_STRING(ROUND(source_lat, 1)))
| STATS 
    total_failures = SUM(handover_failures),
    total_affected_subscribers = SUM(unique_subscribers),
    affected_source_cells = COUNT_DISTINCT(cell_id),
    cells_in_cascade = VALUES(source_site)
  BY time_bucket, geographic_key, source_region, cascade_risk
| WHERE affected_source_cells >= 3
| SORT total_failures DESC
| LIMIT 20
```

**Run and break down:** 

"This query is doing sophisticated network failure analysis:

**Step 1 - Filter & Bucket:**
- Focus on handover failures in last 30 minutes
- Group into 5-minute time windows

**Step 2 - Initial Aggregation:**
- Count failures per source cell
- Track unique subscribers and target cells affected
- Filter to significant events (50+ failures, 100+ subscribers)

**Step 3 - Geographic Enrichment:**
- JOIN with cell tower reference to get site names, coordinates, regions
- Rename fields to distinguish source cell attributes

**Step 4 - Risk Scoring:**
- Calculate cascade_risk based on how many target cells are affected
- Create geographic_key to cluster nearby cells

**Step 5 - Cascade Detection:**
- Re-aggregate by geographic area and time
- Identify patterns where 3+ cells in the same region are failing simultaneously
- This indicates radio equipment failure or coverage gap cascades

**Business Value:**
This single query replaces hours of manual investigation. Network Operations can immediately see:
- WHERE cascade failures are happening (geographic clustering)
- WHEN they started (time buckets)
- IMPACT (subscriber counts)
- SEVERITY (cascade risk scoring)

This enables proactive response before help desk is overwhelmed with customer complaints."

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

**Agent Configuration:**

**Agent ID:** `tmobile-network-ops-agent`

**Display Name:** `T-Mobile Network Operations AI Agent`

**Custom Instructions:** 

```
You are an expert telecommunications network operations analyst for T-Mobile. You have deep knowledge of LTE/5G core network architecture, S1AP signaling, HSS authentication systems, MME operations, and SS7 security.

When analyzing network issues:
1. Always consider subscriber impact first
2. Correlate events across multiple network layers (radio, core, signaling)
3. Provide root cause analysis with specific node/cell identifiers
4. Include severity assessment and recommended actions
5. Calculate business impact when relevant (revenue, subscriber counts)

When detecting anomalies:
- Use multi-lag analysis to identify sustained patterns, not just single spikes
- Consider geographic clustering of failures
- Correlate resource utilization with failure patterns
- Flag security threats with appropriate urgency

Always enrich technical data with business context from reference datasets (cell tower locations, MME capacity, cause code descriptions, threat intelligence).

Format responses with clear sections: Summary, Root Cause, Impact, Recommended Actions.
```

---

### **Creating Tools**

#### **Tool 1: IMSI and Cell ID Spike Detection**

**Tool Name:** `detect_imsi_cell_spikes`

**Description:** 
```
Detects sustained spike patterns in unique IMSI and cell ID cardinality over time. 
Calculates counts per 5-minute interval and compares against 1-lag and 2-lag periods 
to identify anomalies indicating network issues, mass events, or security attacks.

Triggers alerts when:
- imsi_change_1 > 400 OR imsi_change_2 > 280
- cell_id_change_1 > 50 OR cell_id_change_2 > 25

Use this tool to detect early warning signs before help desk is overwhelmed.
```

**ES|QL Query:** (Use Query 2 from Part 2)

---

#### **Tool 2: HSS Authentication Failure Analysis**

**Tool Name:** `analyze_hss_auth_failures`

**Description:**
```
Identifies mass authentication failure events by aggregating failed authentication 
attempts per 5-minute interval (minimum 200 failures threshold). Enriches results 
with HSS node details including datacenter, cluster_id, database_type, and 
replication_status to pinpoint database corruption, synchronization issues, or 
replication failures affecting subscriber authentication.

Returns health status assessment and specific HSS nodes requiring attention.
```

**ES|QL Query:** (Use Query 3 from Part 2)

---

#### **Tool 3: Cell Tower Handoff Cascade Failure Detection**

**Tool Name:** `detect_handoff_cascade_failures`

**Description:**
```
Detects cell tower handoff cascade failures by analyzing handover failure patterns 
across neighbor cells within 5-minute windows. Enriches with cell tower geography, 
site names, and neighbor relationships to identify radio equipment failures or 
coverage gaps affecting 50+ unique cell IDs and 500+ subscribers.

Provides geographic clustering analysis and cascade risk scoring (HIGH/MEDIUM/LOW) 
based on number of affected target cells. Critical for identifying infrastructure 
failures before widespread service degradation.
```

**ES|QL Query:** (Use Query 4 from Part 2)

---

#### **Tool 4: MME Resource Exhaustion Detection**

**Tool Name:** `detect_mme_resource_exhaustion`

**Description:**
```
Identifies MME software bugs or resource exhaustion by correlating service request 
procedure failures (minimum 200 failures per 5-minute interval) with MME resource 
utilization metrics (CPU, memory, active subscribers). Enriches with MME software 
version, capacity tier, and datacenter location to pinpoint specific hosts 
experiencing issues.

Flags MME hosts approaching capacity limits or exhibiting abnormal resource patterns 
across 2-5 MME hosts. Enables proactive capacity management and software bug detection.
```

**ES|QL Query:**
```esql
FROM lte_s1ap_events
| WHERE @timestamp > NOW() - 30 minutes 
  AND procedure_type == "SERVICE_REQUEST" 
  AND status == "FAILURE"
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS failure_count = COUNT(*), unique_imsi = COUNT_DISTINCT(imsi) 
  BY time_bucket, mme_host
| WHERE failure_count > 200
| LOOKUP JOIN signaling_link_metrics ON mme_host
| LOOKUP JOIN mme_host_reference ON mme_host
| EVAL capacity_utilization = TO_DOUBLE(active_subscribers) / TO_DOUBLE(max_subscribers) * 100
| EVAL resource_health = CASE(
    cpu_utilization_percent > 85 OR memory_utilization_percent > 90, "CRITICAL",
    cpu_utilization_percent > 70 OR memory_utilization_percent > 75, "WARNING",
    "HEALTHY"
  )
| WHERE resource_health != "HEALTHY"
| STATS 
    total_failures = SUM(failure_count),
    avg_cpu = AVG(cpu_utilization_percent),
    avg_memory = AVG(memory_utilization_percent),
    avg_capacity_util = AVG(capacity_utilization),
    affected_hosts = VALUES(mme_host)
  BY software_version, capacity_tier, datacenter, resource_health
| SORT total_failures DESC
```

---

#### **Tool 5: SS7 Security Attack Detection**

**Tool Name:** `detect_ss7_security_attacks`

**Description:**
```
Detects SS7 security attacks or roaming misconfigurations by identifying attack 
signature patterns per originating network. Enriches with threat intelligence 
including threat category (LOCATION_TRACKING, INTERCEPTION, FRAUD, DOS), 
threat description, and mitigation strategies.

Enables proactive security response and network protection. Prioritizes by severity 
and provides actionable mitigation guidance. Critical for protecting subscriber 
privacy and preventing fraud.
```

**ES|QL Query:**
```esql
FROM ss7_security_events
| WHERE @timestamp > NOW() - 1 hour
| STATS 
    attack_count = COUNT(*),
    unique_targets = COUNT_DISTINCT(destination_imsi),
    blocked_count = COUNT(*) WHERE blocked == true,
    unblocked_count = COUNT(*) WHERE blocked == false
  BY originating_network, attack_signature, severity
| LOOKUP JOIN threat_signature_reference ON attack_signature
| EVAL block_rate = TO_DOUBLE(blocked_count) / TO_DOUBLE(attack_count) * 100
| EVAL risk_level = CASE(
    severity == "CRITICAL" AND unblocked_count > 0, "IMMEDIATE_ACTION",
    severity == "HIGH" AND unblocked_count > 10, "URGENT",
    severity == "MEDIUM", "MONITOR",
    "LOW_PRIORITY"
  )
| SORT attack_count DESC, severity DESC
| KEEP originating_network, threat_name, threat_category, severity, attack_count, 
       unique_targets, block_rate, risk_level, threat_description, mitigation_strategy
```

---

#### **Tool 6: Core Network Signaling Storm Detection**

**Tool Name:** `detect_signaling_storms`

**Description:**
```
Identifies core network split-brain scenarios or signaling storms by detecting 
abnormal message rate spikes, elevated error rates, and SCTP retransmission patterns 
across MME pools. Enriches with MME primary/backup status and datacenter location 
to detect network partitioning or signaling overload conditions.

Detects when message_per_second exceeds thresholds, error_rate is elevated, and 
SCTP retransmissions indicate transport issues. Critical for maintaining core 
network stability.
```

**ES|QL Query:**
```esql
FROM signaling_link_metrics
| WHERE @timestamp > NOW() - 15 minutes
| EVAL time_bucket = DATE_TRUNC(1 minute, @timestamp)
| STATS 
    avg_msg_rate = AVG(messages_per_second),
    max_msg_rate = MAX(messages_per_second),
    avg_error_rate = AVG(error_rate),
    total_retransmissions = SUM(sctp_retransmissions),
    avg_cpu = AVG(cpu_utilization_percent)
  BY time_bucket, mme_host
| LOOKUP JOIN mme_host_reference ON mme_host
| EVAL storm_indicator = CASE(
    max_msg_rate > 5000 AND avg_error_rate > 2.0, "STORM_DETECTED",
    max_msg_rate > 3000 AND total_retransmissions > 100, "WARNING",
    "NORMAL"
  )
| WHERE storm_indicator != "NORMAL"
| STATS 
    affected_mmes = COUNT_DISTINCT(mme_host),
    total_retrans = SUM(total_retransmissions),
    peak_msg_rate = MAX(max_msg_rate),
    mme_list = VALUES(mme_host)
  BY time_bucket, mme_pool, datacenter, storm_indicator
| SORT time_bucket DESC, peak_msg_rate DESC
```

---

#### **Tool 7: Procedure Failure Root Cause Analysis**

**Tool Name:** `analyze_procedure_failure_root_cause`

**Description:**
```
Performs comprehensive procedure failure root cause analysis by aggregating failures 
per cause code. Enriches with human-readable cause descriptions, severity levels, 
and recommended actions. Correlates with cell tower geography to prioritize 
remediation efforts and minimize service downtime affecting 500+ subscribers.

Provides actionable troubleshooting guidance and identifies user-impacting failures 
for prioritization. Essential for rapid incident response.
```

**ES|QL Query:**
```esql
FROM lte_s1ap_events
| WHERE @timestamp > NOW() - 1 hour AND status == "FAILURE"
| STATS 
    failure_count = COUNT(*),
    unique_subscribers = COUNT_DISTINCT(imsi),
    unique_cells = COUNT_DISTINCT(cell_id),
    procedures_affected = VALUES(procedure_type)
  BY cause_code
| WHERE failure_count > 100
| LOOKUP JOIN cause_code_reference ON cause_code
| EVAL priority = CASE(
    user_impacting == true AND severity == "CRITICAL", "P1",
    user_impacting == true AND severity == "MAJOR", "P2",
    severity == "CRITICAL", "P2",
    "P3"
  )
| EVAL subscriber_impact = CASE(
    unique_subscribers > 1000, "HIGH",
    unique_subscribers > 500, "MEDIUM",
    "LOW"
  )
| SORT failure_count DESC
| KEEP cause_code, cause_description, category, severity, priority, failure_count, 
       unique_subscribers, unique_cells, subscriber_impact, recommended_action, 
       procedures_affected
| LIMIT 20
```

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

#### **Warm-up Questions (Start Here)**

1. **"What are the top 5 procedure types with the most failures in the last hour?"**
   - *Tests basic aggregation and sorting*
   - *Expected: Quick list with counts*

2. **"How many unique subscribers experienced authentication failures in the last 30 minutes?"**
   - *Tests simple filtering and distinct counting*
   - *Expected: Single number with context*

3. **"Show me all cell towers in the WEST region that are currently in DEGRADED status."**
   - *Tests reference data lookup*
   - *Expected: List of cell_ids and site names*

---

#### **Business-Focused Questions (Show ROI)**

4. **"What is the estimated revenue impact of handover failures in the last 6 hours? Assume $50 ARPU and 30-minute average outage per affected subscriber."**
   - *Tests business calculation capabilities*
   - *Expected: Dollar amount with methodology explanation*

5. **"Which MME hosts are at risk of capacity exhaustion within the next hour based on current subscriber growth rate?"**
   - *Tests predictive analysis*
   - *Expected: List of hosts with capacity utilization percentages*

6. **"Prioritize the top 3 network issues by subscriber impact right now. Include failure counts and recommended actions."**
   - *Tests multi-dataset correlation and prioritization*
   - *Expected: Ranked list with action items*

---

#### **Trend Analysis Questions (Show Intelligence)**

7. **"Are there any abnormal spikes in unique IMSI counts over the last 2 hours compared to historical patterns?"**
   - *Tests spike detection tool with lag analysis*
   - *Expected: Time periods with spike indicators and magnitude*

8. **"Show me the trend of authentication failures per HSS cluster over the last 24 hours. Are any clusters showing degradation?"**
   - *Tests time-series aggregation and pattern recognition*
   - *Expected: Cluster-level trends with health assessment*

9. **"Has the handover failure rate increased in any specific geographic region in the last 4 hours?"**
   - *Tests geographic correlation and trend detection*
   - *Expected: Region-level failure rate comparison*

---

#### **Security & Threat Detection (Show Criticality)**

10. **"Are there any active SS7 security attacks targeting our subscribers right now? What's the threat category and severity?"**
    - *Tests security event detection with enrichment*
    - *Expected: List of active attacks with threat intelligence*

11. **"Which originating networks have the highest volume of blocked SS7 attacks in the last week? Should we implement additional filtering?"**
    - *Tests security trend analysis and recommendation generation*
    - *Expected: Network rankings with mitigation recommendations*

---

#### **Root Cause & Troubleshooting (Show Depth)**

12. **"We're seeing a spike in SERVICE_REQUEST failures on MME pool EAST-01. What's the root cause and which specific hosts are affected?"**
    - *Tests multi-dataset correlation and root cause analysis*
    - *Expected: Specific MME hosts, resource metrics, and probable cause*

13. **"Cell tower site 'Downtown-Seattle-01' is experiencing handoff failures. Which neighbor cells are affected and what's the cascade risk?"**
    - *Tests cascade failure detection with neighbor analysis*
    - *Expected: Neighbor cell list, failure counts, risk assessment*

14. **"What are the top 3 cause codes for ATTACH procedure failures, and what are the recommended troubleshooting actions?"**
    - *Tests cause code enrichment and actionable guidance*
    - *Expected: Cause codes with descriptions and remediation steps*

---

#### **Operational Optimization (Show Proactive Value)**

15. **"Which cell towers are operating above 90% capacity and should be prioritized for expansion?"**
    - *Tests capacity planning analysis*
    - *Expected: Cell tower list with utilization metrics*

16. **"Are there any signaling storms or split-brain conditions detected in the core network right now?"**
    - *Tests complex pattern detection across distributed systems*
    - *Expected: MME pool status with storm indicators*

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "Modern query language, built for analytics - designed for the way humans think about data"
- "Piped syntax is intuitive and readable - anyone can understand what a query does"
- "Operates on blocks, not rows - extremely performant even on massive datasets"
- "Supports complex operations: joins, window functions, time-series, lag analysis"
- "No need to pre-define schemas - query the data you have, right now"

### **On Agent Builder:**
- "Bridges AI and enterprise data - your proprietary data stays in your environment"
- "No custom development - configure, don't code. Build agents in hours, not months"
- "Works with existing Elasticsearch indices - no data migration required"
- "Agent automatically selects right tools based on question context"
- "Built-in governance and access controls - enterprise-ready security"

### **On Business Value for T-Mobile:**
- "Democratizes network operations data - anyone can ask questions, not just ES|QL experts"
- "Real-time insights, always up-to-date - no stale reports or manual queries"
- "Reduces dependency on data teams - Network Operations becomes self-sufficient"
- "Faster decision-making during incidents - minutes instead of hours"
- "Proactive issue detection - catch problems before customers are impacted"
- "Reduces mean time to resolution (MTTR) - faster root cause identification"

### **On Technical Differentiation:**
- "ES|QL is Elasticsearch's native query language - optimized for the underlying architecture"
- "LOOKUP JOIN enables real-time enrichment without data duplication"
- "Time-series functions (LAG, DATE_TRUNC) purpose-built for operational analytics"
- "Agent Builder uses RAG (Retrieval-Augmented Generation) - AI answers grounded in your real data"

---

## **🔧 Troubleshooting**

**If a query fails:**
- Check index names match exactly (case-sensitive)
- Verify field names are correct (use `FROM <index> | LIMIT 1` to inspect fields)
- Ensure joined indices are in lookup mode (`GET <index>/_settings` to verify)
- Check time range filters - ensure data exists in that time window

**If agent gives wrong answer:**
- Check tool descriptions - are they clear and specific about what the tool does?
- Review custom instructions - does the agent have the right context?
- Verify query results in Dev Tools first - is the underlying query correct?
- Check if the agent selected the right tool (review agent logs)

**If join returns no results:**
- Verify join key format is consistent across datasets (e.g., both are keywords, not text)
- Check that lookup index has data (`FROM <lookup_index> | LIMIT 1`)
- Ensure join key values actually match (case-sensitive)
- Verify lookup index has `"index.mode": "lookup"` setting

**If agent is slow:**
- Check if queries have appropriate time range filters
- Verify indexes are not overly large without time-based filtering
- Consider adding LIMIT clauses to tools for faster responses
- Review agent logs for which tools are being called

**If data upload fails:**
- Ensure CSV format is correct (headers match field names)
- Check for special characters or encoding issues
- Verify date fields are in ISO 8601 format
- Try uploading a smaller sample first to test

---

## **🎬 Closing**

"What we've shown today:

✅ **Complex analytics** on interconnected telecommunications datasets - LTE events, HSS authentication, signaling metrics, security events - all correlated in real-time

✅ **Natural language interface** for non-technical users - Network Operations teams can ask questions without knowing ES|QL syntax

✅ **Real-time insights** without custom development - queries that would take hours to write and debug, answered in seconds

✅ **Proactive issue detection** - catch network problems before help desk is overwhelmed with customer complaints

✅ **Root cause analysis** with enriched context - not just WHAT is failing, but WHY, with specific nodes, cells, and actionable remediation steps

**For T-Mobile specifically:**
- Detect authentication failures before subscriber impact
- Identify cascade failures across cell tower neighbors
- Catch resource exhaustion before MME failures
- Block SS7 security attacks with threat intelligence
- Reduce MTTR from hours to minutes

**Deployment Timeline:**
Agent Builder can be deployed in **days, not months**:
- Day 1-2: Index setup and data ingestion
- Day 3-4: ES|QL query development and testing
- Day 5-7: Agent configuration and tool creation
- Week 2: User testing and refinement
- Week 3: Production rollout

**Next Steps:**
1. Identify 2-3 high-priority use cases for pilot
2. Schedule data access and index setup session
3. Build initial agent with core tools
4. Conduct user acceptance testing with Network Operations team
5. Iterate based on feedback
6. Scale to additional use cases

Questions?"

---

## **📎 Appendix: Quick Reference**

### **ES|QL Command Cheat Sheet**

| Command | Purpose | Example |
|---------|---------|---------|
| `FROM` | Source data | `FROM lte_s1ap_events` |
| `WHERE` | Filter rows | `WHERE status == "FAILURE"` |
| `STATS` | Aggregate | `STATS count = COUNT(*) BY field` |
| `EVAL` | Calculate fields | `EVAL rate = TO_DOUBLE(a) / TO_DOUBLE(b)` |
| `LOOKUP JOIN` | Join datasets | `LOOKUP JOIN ref_index ON key_field` |
| `SORT` | Order results | `SORT count DESC` |
| `LIMIT` | Restrict rows | `LIMIT 10` |
| `KEEP` | Select columns | `KEEP field1, field2` |
| `DROP` | Remove columns | `DROP unwanted_field` |
| `RENAME` | Rename fields | `RENAME old AS new` |

### **Common ES|QL Functions**

| Function | Purpose | Example |
|----------|---------|---------|
| `COUNT(*)` | Count rows | `STATS total = COUNT(*)` |
| `COUNT_DISTINCT()` | Unique count | `STATS unique = COUNT_DISTINCT(imsi)` |
| `AVG()` | Average | `STATS avg_val = AVG(field)` |
| `SUM()` | Sum | `STATS total = SUM(field)` |
| `MAX()` / `MIN()` | Extremes | `STATS max_val = MAX(field)` |
| `DATE_TRUNC()` | Time bucketing | `EVAL bucket = DATE_TRUNC(5 minutes, @timestamp)` |
| `LAG()` | Previous value | `EVAL prev = LAG(field, 1)` |
| `CASE()` | Conditional | `EVAL status = CASE(val > 10, "HIGH", "LOW")` |
| `CONCAT()` | String join | `EVAL key = CONCAT(a, "-", b)` |
| `TO_DOUBLE()` | Type conversion | `EVAL rate = TO_DOUBLE(count)` |

### **Index Mode Settings**

**For LOOKUP JOIN to work:**
```json
{
  "settings": {
    "index.mode": "lookup"
  }
}
```

**Apply to all reference datasets:**
- cell_tower_reference
- mme_host_reference
- cause_code_reference
- hss_node_reference
- threat_signature_reference

---

**End of Demo Guide**