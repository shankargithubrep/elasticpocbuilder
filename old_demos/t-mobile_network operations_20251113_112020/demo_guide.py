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
**Goal:** Show how Agent Builder enables AI-powered analytics on T-Mobile network infrastructure data

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## **🗂️ Dataset Architecture**

### **mme_failure_events** (Timeseries Index)
- **Record Count:** 500,000+
- **Primary Key:** `event_id`
- **Time Field:** `@timestamp`
- **Key Fields:**
  - `mme_host_id` - Links to mme_hosts
  - `subscriber_id` - Links to subscriber_profiles
  - `cell_tower_id` - Links to cell_towers
  - `failure_type` - Authentication, Handoff, Attach, Detach, etc.
  - `failure_code` - Numeric error code
  - `plmn_id` - Public Land Mobile Network identifier
  - `severity` - Critical, Major, Minor, Warning
  - `session_id` - Unique session identifier
- **Purpose:** Core telemetry for all MME (Mobility Management Entity) failure events
- **Relationships:** Central fact table linking to all reference datasets

### **mme_hosts** (Reference Index - Lookup Mode)
- **Record Count:** 50+
- **Primary Key:** `mme_host_id`
- **Key Fields:**
  - `hostname` - MME server hostname
  - `cluster_name` - Logical cluster grouping
  - `datacenter` - Physical location
  - `capacity_rating` - Max subscribers supported
  - `software_version` - Current MME software version
  - `deployment_date` - When host was deployed
- **Purpose:** MME infrastructure metadata for enrichment
- **Index Mode:** `lookup` (required for LOOKUP JOIN operations)

### **cell_towers** (Reference Index - Lookup Mode)
- **Record Count:** 5,000+
- **Primary Key:** `cell_tower_id`
- **Key Fields:**
  - `tower_name` - Human-readable tower identifier
  - `location.lat` / `location.lon` - Geographic coordinates
  - `region` - Geographic region (Northeast, Southwest, etc.)
  - `equipment_type` - Radio equipment model
  - `power_source` - Grid, Battery, Solar, Hybrid
  - `commissioning_date` - When tower went live
  - `neighbor_towers` - Array of adjacent tower IDs
- **Purpose:** Cell tower infrastructure and topology data
- **Index Mode:** `lookup` (required for LOOKUP JOIN operations)

### **subscriber_profiles** (Reference Index - Lookup Mode)
- **Record Count:** 100,000+
- **Primary Key:** `subscriber_id`
- **Key Fields:**
  - `account_type` - Consumer, Enterprise, Government, Wholesale
  - `service_tier` - Premium, Standard, Basic
  - `contract_sla` - SLA percentage (99.9%, 99.99%, etc.)
  - `enterprise_name` - Company name for enterprise accounts
  - `activation_date` - When subscriber joined
  - `home_region` - Primary coverage area
- **Purpose:** Subscriber segmentation and SLA tracking
- **Index Mode:** `lookup` (required for LOOKUP JOIN operations)

### **hss_sync_events** (Timeseries Index)
- **Record Count:** 200,000+
- **Primary Key:** `sync_event_id`
- **Time Field:** `@timestamp`
- **Key Fields:**
  - `hss_node_id` - HSS (Home Subscriber Server) node identifier
  - `sync_type` - Full, Incremental, Emergency
  - `records_synced` - Number of subscriber records synchronized
  - `sync_duration_ms` - Time taken for sync operation
  - `sync_status` - Success, Partial, Failed
  - `corruption_detected` - Boolean flag
  - `affected_subscribers` - Array of impacted subscriber IDs
- **Purpose:** HSS database synchronization health monitoring
- **Relationships:** Links to subscriber_profiles via affected_subscribers

---

## **🚀 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

**CRITICAL: All indexes need "index.mode": "lookup" for joins to work**

#### **1. Upload mme_failure_events (Timeseries)**

```
POST mme_failure_events/_doc
{
  "event_id": "evt_001",
  "@timestamp": "2024-01-15T10:23:45Z",
  "mme_host_id": "mme_host_12",
  "subscriber_id": "sub_45678",
  "cell_tower_id": "tower_2341",
  "failure_type": "Authentication",
  "failure_code": 401,
  "plmn_id": "310260",
  "severity": "Critical",
  "session_id": "sess_998877"
}
```

**Repeat for ~500K records with varied timestamps, failure types, and IDs**

#### **2. Create mme_hosts (Lookup Mode)**

```
PUT mme_hosts
{
  "settings": {
    "index": {
      "mode": "lookup"
    }
  },
  "mappings": {
    "properties": {
      "mme_host_id": { "type": "keyword" },
      "hostname": { "type": "keyword" },
      "cluster_name": { "type": "keyword" },
      "datacenter": { "type": "keyword" },
      "capacity_rating": { "type": "integer" },
      "software_version": { "type": "keyword" },
      "deployment_date": { "type": "date" }
    }
  }
}

POST mme_hosts/_doc/mme_host_12
{
  "mme_host_id": "mme_host_12",
  "hostname": "mme-dal-prod-12",
  "cluster_name": "Dallas-Cluster-A",
  "datacenter": "Dallas-DC1",
  "capacity_rating": 500000,
  "software_version": "v8.2.1",
  "deployment_date": "2023-06-15"
}
```

**Repeat for ~50 MME hosts across different clusters and datacenters**

#### **3. Create cell_towers (Lookup Mode)**

```
PUT cell_towers
{
  "settings": {
    "index": {
      "mode": "lookup"
    }
  },
  "mappings": {
    "properties": {
      "cell_tower_id": { "type": "keyword" },
      "tower_name": { "type": "keyword" },
      "location": { "type": "geo_point" },
      "region": { "type": "keyword" },
      "equipment_type": { "type": "keyword" },
      "power_source": { "type": "keyword" },
      "commissioning_date": { "type": "date" },
      "neighbor_towers": { "type": "keyword" }
    }
  }
}

POST cell_towers/_doc/tower_2341
{
  "cell_tower_id": "tower_2341",
  "tower_name": "DAL-Downtown-23",
  "location": { "lat": 32.7767, "lon": -96.7970 },
  "region": "Southwest",
  "equipment_type": "Ericsson-5G-AIR6488",
  "power_source": "Grid",
  "commissioning_date": "2022-03-10",
  "neighbor_towers": ["tower_2340", "tower_2342", "tower_2355"]
}
```

**Repeat for ~5,000 cell towers across all regions**

#### **4. Create subscriber_profiles (Lookup Mode)**

```
PUT subscriber_profiles
{
  "settings": {
    "index": {
      "mode": "lookup"
    }
  },
  "mappings": {
    "properties": {
      "subscriber_id": { "type": "keyword" },
      "account_type": { "type": "keyword" },
      "service_tier": { "type": "keyword" },
      "contract_sla": { "type": "keyword" },
      "enterprise_name": { "type": "keyword" },
      "activation_date": { "type": "date" },
      "home_region": { "type": "keyword" }
    }
  }
}

POST subscriber_profiles/_doc/sub_45678
{
  "subscriber_id": "sub_45678",
  "account_type": "Enterprise",
  "service_tier": "Premium",
  "contract_sla": "99.99%",
  "enterprise_name": "American Airlines",
  "activation_date": "2021-08-20",
  "home_region": "Southwest"
}
```

**Repeat for ~100K subscribers with mix of Consumer (70%), Enterprise (25%), Government (5%)**

#### **5. Upload hss_sync_events (Timeseries)**

```
POST hss_sync_events/_doc
{
  "sync_event_id": "sync_5001",
  "@timestamp": "2024-01-15T10:15:00Z",
  "hss_node_id": "hss_node_03",
  "sync_type": "Incremental",
  "records_synced": 15420,
  "sync_duration_ms": 3450,
  "sync_status": "Success",
  "corruption_detected": false,
  "affected_subscribers": []
}
```

**Repeat for ~200K sync events with occasional corruption_detected: true events**

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to your AI Agent chat interface
- Have the agent already configured with all tools

### **Demo Script**

**Presenter:** "Before we dive into how this works, let me show you the end result. I'm going to ask our AI agent a complex business question that would normally require a data engineer, multiple queries, and hours of work."

**Sample questions to demonstrate:**

1. **ROI / Business Impact Question:**
   "Which enterprise customers are at highest risk of SLA violations in the last 24 hours based on authentication failure rates? Calculate the potential financial penalty for each."

   *Why this impresses:* Joins subscriber profiles, calculates SLA risk, filters to enterprise accounts, and estimates business impact - all in natural language.

2. **Trend Detection:**
   "Show me cell towers that have experienced a 3x increase in handoff failures compared to their 7-day baseline. Are these towers geographically clustered?"

   *Why this impresses:* Statistical baseline comparison, geographic analysis, pattern detection across time windows.

3. **Root Cause Analysis:**
   "Are there any MME hosts in the same cluster showing synchronized failure spikes in the last hour? This could indicate a split-brain condition."

   *Why this impresses:* Multi-dimensional correlation, cluster-aware analysis, identifies systemic infrastructure issues.

4. **Security / Anomaly Detection:**
   "Identify any unusual PLMN patterns in authentication failures that might indicate SS7 attacks or rogue network attempts."

   *Why this impresses:* Security-focused analysis, pattern recognition, threat detection without predefined rules.

5. **Capacity Planning:**
   "Which MME hosts are handling subscriber loads above 80% of their capacity rating, and how many authentication failures are they generating?"

   *Why this impresses:* Joins infrastructure metadata with operational telemetry, resource exhaustion prediction.

6. **Cascade Failure Detection:**
   "Find cell towers where more than 50 neighboring towers are also experiencing failures. Show me the equipment type and power source distribution."

   *Why this impresses:* Graph-like topology analysis, infrastructure correlation, multi-attribute enrichment.

7. **Operational Efficiency:**
   "What percentage of HSS sync events are failing or showing corruption? Break it down by HSS node and show which subscriber segments are most affected."

   *Why this impresses:* Multi-dataset join, percentage calculations, segmentation analysis, database health monitoring.

**Transition:** "So how does this actually work? These answers come from real queries against your network operations data. Let's go under the hood and build these queries from scratch using ES|QL."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open Kibana Dev Tools Console
- Have the indices already created and populated

---

### **Query 1: Simple Aggregation (2 minutes)**

**Presenter:** "T-Mobile's Network Operations team wants to know: What are the top failure types impacting the network right now, and how severe are they?"

**Copy/paste into console:**

```esql
FROM mme_failure_events
| STATS failure_count = COUNT(*) BY failure_type, severity
| SORT failure_count DESC
| LIMIT 10
```

**Run and narrate results:** "This is basic ES|QL:
- FROM: Source our MME failure events data
- STATS: Aggregate failure counts, grouped by type and severity
- SORT and LIMIT: Show top 10 problem areas

The syntax is intuitive - it reads like English. You can see immediately if Authentication failures or Handoff issues are dominating, and whether they're Critical or just Warnings."

---

### **Query 2: Add Calculations with EVAL (3 minutes)**

**Presenter:** "Let's add calculations to detect abnormal authentication failure rates that might indicate an HSS database issue or mass outage."

**Copy/paste:**

```esql
FROM mme_failure_events
| WHERE @timestamp > NOW() - 5 minutes
| STATS 
    total_events = COUNT(*),
    auth_failures = COUNT(*) WHERE failure_type == "Authentication"
  BY BUCKET(@timestamp, 1 minute)
| EVAL auth_failure_rate = TO_DOUBLE(auth_failures) / TO_DOUBLE(total_events) * 100
| EVAL z_score = (auth_failure_rate - 2.5) / 1.2
| WHERE z_score > 3
| SORT @timestamp DESC
```

**Run and highlight:** "Key additions:
- EVAL: Creates calculated fields on-the-fly (failure rate, statistical z-score)
- TO_DOUBLE: Critical for decimal division - prevents integer math errors
- Multiple STATS: Aggregating total events and filtered auth failures
- WHERE after EVAL: Filter to only show statistical anomalies (z-score > 3)
- Business-relevant calculations: This query implements the 'Mass Subscriber Authentication Failure Detection' use case

When z-score exceeds 3, we're seeing authentication failures 3 standard deviations above normal - a clear indicator that HSS database sync issues or corruption are occurring."

---

### **Query 3: Join Datasets with LOOKUP JOIN (3 minutes)**

**Presenter:** "Now let's combine data from multiple sources to identify which enterprise customers are being impacted - critical for SLA management."

**Copy/paste:**

```esql
FROM mme_failure_events
| WHERE @timestamp > NOW() - 1 hour AND failure_type == "Authentication"
| STATS failure_count = COUNT(*) BY subscriber_id
| LOOKUP JOIN subscriber_profiles ON subscriber_id
| WHERE account_type == "Enterprise"
| EVAL sla_risk_score = CASE(
    failure_count > 10, "Critical",
    failure_count > 5, "High",
    failure_count > 2, "Medium",
    "Low"
  )
| SORT failure_count DESC
| KEEP subscriber_id, enterprise_name, service_tier, contract_sla, failure_count, sla_risk_score
| LIMIT 20
```

**Run and explain:** "Magic happening here:
- LOOKUP JOIN: Combines failure events with subscriber profile data using subscriber_id as the join key
- Now we have access to fields from both datasets - account_type, enterprise_name, contract_sla
- This is a LEFT JOIN: All failure records kept, enriched with subscriber metadata
- For LOOKUP JOIN to work, the subscriber_profiles index must have 'index.mode: lookup'
- CASE statement: Creates business-relevant risk scores based on failure thresholds
- KEEP: Explicitly selects only the fields we want in final output

This directly addresses T-Mobile's pain point: 'SLA violations with enterprise customers' - we can now proactively alert account managers before American Airlines or other enterprise customers experience outages."

---

### **Query 4: Complex Multi-Dataset Analytics (2 minutes)**

**Presenter:** "For the grand finale - a sophisticated analytical query showing cascade failure detection across cell tower infrastructure, enriched with equipment and power source data to identify systematic infrastructure problems."

**Copy/paste:**

```esql
FROM mme_failure_events
| WHERE @timestamp > NOW() - 2 hours AND failure_type == "Handoff"
| STATS 
    handoff_failures = COUNT(*),
    unique_subscribers = COUNT_DISTINCT(subscriber_id),
    unique_mme_hosts = COUNT_DISTINCT(mme_host_id)
  BY cell_tower_id
| WHERE handoff_failures > 100
| LOOKUP JOIN cell_towers ON cell_tower_id
| EVAL neighbor_count = MV_COUNT(neighbor_towers)
| STATS 
    affected_towers = COUNT(*),
    total_handoff_failures = SUM(handoff_failures),
    total_subscribers_impacted = SUM(unique_subscribers),
    avg_neighbor_count = AVG(neighbor_count)
  BY region, equipment_type, power_source
| EVAL failure_severity = CASE(
    affected_towers > 50, "Cascade Failure - Infrastructure Issue",
    affected_towers > 20, "Regional Degradation",
    affected_towers > 10, "Localized Problem",
    "Normal Operations"
  )
| WHERE affected_towers > 10
| EVAL avg_failures_per_tower = ROUND(TO_DOUBLE(total_handoff_failures) / TO_DOUBLE(affected_towers), 2)
| SORT total_handoff_failures DESC
| KEEP region, equipment_type, power_source, affected_towers, total_handoff_failures, 
       total_subscribers_impacted, avg_failures_per_tower, failure_severity
```

**Run and break down:** 

"This query implements the 'Cell Tower Handoff Cascade Failure Analysis' use case. Let's break down what's happening:

**Stage 1 - Failure Aggregation:**
- Filter to handoff failures in last 2 hours
- Count failures per tower, track unique subscribers and MME hosts
- Filter to towers with >100 failures (noise reduction)

**Stage 2 - Infrastructure Enrichment:**
- LOOKUP JOIN brings in tower metadata: region, equipment type, power source, neighbor topology
- MV_COUNT calculates how many neighbor towers each tower has

**Stage 3 - Pattern Detection:**
- Second STATS groups by infrastructure attributes (region, equipment, power)
- Identifies if 50+ towers with same equipment type are failing - indicates vendor equipment issue
- Or if towers in same region with 'Battery' power source are failing - indicates power infrastructure problem

**Stage 4 - Business Logic:**
- CASE statement categorizes severity: 50+ towers = 'Cascade Failure'
- Calculates average failures per tower to distinguish widespread vs. concentrated issues
- Filters to only show significant problems (>10 towers affected)

**The Result:** 
Instead of drowning in individual tower alerts, this query surfaces systematic infrastructure failures. If you see 75 towers in the Southwest region with 'Ericsson-5G-AIR6488' equipment all failing, you know it's a vendor equipment bug, not 75 separate incidents. This directly addresses the pain point: 'Radio equipment failure and cell site power failures affecting handoffs' - we can now identify and escalate infrastructure-wide issues in minutes, not hours."

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

**Agent Configuration:**

**Agent ID:** `tmobile-network-ops-agent`

**Display Name:** `T-Mobile Network Operations AI Assistant`

**Custom Instructions:** 

"You are an AI assistant specialized in T-Mobile's network operations data analysis. You have access to MME failure events, cell tower infrastructure, subscriber profiles, MME host metadata, and HSS synchronization events.

**Your primary objectives:**
1. Detect systematic infrastructure failures and cascade events affecting multiple cell towers or MME hosts
2. Identify enterprise customer SLA violation risks before help desk is overwhelmed
3. Surface HSS database corruption and synchronization issues affecting subscriber authentication
4. Detect security threats including SS7 attacks and rogue network attempts
5. Filter noise and only alert on multi-dimensional problems with business impact

**Analysis approach:**
- Use statistical methods (z-scores, baseline comparisons) to detect anomalies, not just raw counts
- Always enrich failure data with subscriber, tower, and infrastructure context
- Prioritize enterprise customers and SLA risk in your analysis
- Look for correlated failures across multiple dimensions (time, geography, infrastructure)
- Explain the business impact and recommended actions in your responses

**When analyzing failures:**
- Authentication failures: Check HSS sync status, calculate z-scores, identify enterprise impact
- Handoff failures: Look for geographic clustering, equipment type patterns, cascade effects
- MME issues: Check for split-brain conditions (synchronized failures across cluster), resource exhaustion
- Security: Identify unusual PLMN patterns, unauthorized roaming attempts, suspicious failure signatures

Always provide actionable insights, not just data dumps."

---

### **Creating Tools**

#### **Tool 1: Mass Authentication Failure Detector**

**Tool Name:** `detect_mass_auth_failures`

**Description:** "Detects mass subscriber authentication failures using statistical z-score analysis across 5-minute intervals. Enriches results with subscriber context to identify enterprise customer impact and HSS database issues. Use this when asked about authentication problems, HSS issues, subscriber login failures, or SLA risks."

**ES|QL Query:**
```esql
FROM mme_failure_events
| WHERE @timestamp > NOW() - 30 minutes
| STATS 
    total_events = COUNT(*),
    auth_failures = COUNT(*) WHERE failure_type == "Authentication",
    unique_subscribers = COUNT_DISTINCT(subscriber_id),
    unique_mme_hosts = COUNT_DISTINCT(mme_host_id)
  BY BUCKET(@timestamp, 5 minutes)
| EVAL auth_failure_rate = TO_DOUBLE(auth_failures) / TO_DOUBLE(total_events) * 100
| EVAL z_score = (auth_failure_rate - 2.5) / 1.2
| WHERE z_score > 2
| SORT @timestamp DESC
| LIMIT 20
```

#### **Tool 2: Cell Tower Cascade Failure Analyzer**

**Tool Name:** `analyze_tower_cascade_failures`

**Description:** "Identifies systematic cell tower handoff failures using multi-dimensional cardinality analysis. Detects infrastructure cascade failures from power or equipment issues affecting 50+ cells. Enriches with tower metadata including equipment type, power source, and region. Use this for handoff problems, cell site outages, or geographic failure patterns."

**ES|QL Query:**
```esql
FROM mme_failure_events
| WHERE @timestamp > NOW() - 2 hours AND failure_type == "Handoff"
| STATS handoff_failures = COUNT(*), unique_subscribers = COUNT_DISTINCT(subscriber_id) BY cell_tower_id
| WHERE handoff_failures > 50
| LOOKUP JOIN cell_towers ON cell_tower_id
| STATS 
    affected_towers = COUNT(*),
    total_failures = SUM(handoff_failures),
    total_subscribers = SUM(unique_subscribers)
  BY region, equipment_type, power_source
| WHERE affected_towers > 10
| SORT total_failures DESC
```

#### **Tool 3: MME Split-Brain and Signaling Storm Detector**

**Tool Name:** `detect_mme_split_brain`

**Description:** "Detects split-brain conditions and signaling storms by analyzing failure patterns across multiple MME hosts in the same cluster. Uses statistical deviation to identify synchronized cyclical failures indicating core network issues. Use this for MME outages, core network problems, or when multiple MME hosts are showing issues simultaneously."

**ES|QL Query:**
```esql
FROM mme_failure_events
| WHERE @timestamp > NOW() - 1 hour
| STATS 
    failure_count = COUNT(*),
    unique_failure_types = COUNT_DISTINCT(failure_type),
    failure_spike = COUNT(*) WHERE severity == "Critical"
  BY mme_host_id, BUCKET(@timestamp, 5 minutes)
| LOOKUP JOIN mme_hosts ON mme_host_id
| STATS 
    hosts_affected = COUNT_DISTINCT(mme_host_id),
    total_failures = SUM(failure_count),
    critical_spikes = SUM(failure_spike),
    avg_failures_per_host = AVG(failure_count)
  BY cluster_name, BUCKET(@timestamp, 5 minutes)
| WHERE hosts_affected > 2 AND critical_spikes > 100
| EVAL split_brain_risk = CASE(
    hosts_affected > 4 AND critical_spikes > 500, "Critical - Likely Split-Brain",
    hosts_affected > 3 AND critical_spikes > 300, "High - Signaling Storm",
    "Medium - Cluster Degradation"
  )
| SORT @timestamp DESC
```

#### **Tool 4: Enterprise SLA Violation Risk Calculator**

**Tool Name:** `calculate_enterprise_sla_risk`

**Description:** "Proactively identifies service degradation affecting enterprise customers by analyzing failure patterns for enterprise subscribers. Calculates SLA risk scores before violations occur and help desk is overwhelmed. Use this for enterprise customer questions, SLA monitoring, or account management priorities."

**ES|QL Query:**
```esql
FROM mme_failure_events
| WHERE @timestamp > NOW() - 24 hours
| STATS 
    total_failures = COUNT(*),
    auth_failures = COUNT(*) WHERE failure_type == "Authentication",
    handoff_failures = COUNT(*) WHERE failure_type == "Handoff"
  BY subscriber_id
| LOOKUP JOIN subscriber_profiles ON subscriber_id
| WHERE account_type == "Enterprise"
| EVAL failure_rate_score = CASE(
    total_failures > 20, 100,
    total_failures > 10, 75,
    total_failures > 5, 50,
    25
  )
| EVAL sla_violation_risk = CASE(
    contract_sla == "99.99%" AND total_failures > 5, "Critical",
    contract_sla == "99.9%" AND total_failures > 10, "High",
    total_failures > 15, "Medium",
    "Low"
  )
| SORT total_failures DESC
| KEEP enterprise_name, service_tier, contract_sla, total_failures, auth_failures, 
       handoff_failures, failure_rate_score, sla_violation_risk
| LIMIT 50
```

**Summary:** These four tools cover T-Mobile's critical use cases: authentication failures (HSS issues), cascade failures (infrastructure), split-brain detection (core network), and enterprise SLA risk (business impact). The agent will automatically select the appropriate tool based on the user's question.

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

**Warm-up Questions:**

1. "How many authentication failures occurred in the last hour?"
   - *Purpose: Simple query to show basic functionality*

2. "Which cell tower has the most handoff failures today?"
   - *Purpose: Single dataset aggregation with sorting*

3. "Show me the top 5 MME hosts by total failure count in the last 6 hours."
   - *Purpose: Demonstrates host-level analysis*

---

**Business-Focused Questions:**

4. "Which enterprise customers are currently at risk of SLA violations? Show me the top 10 by failure count and their contract SLA levels."
   - *Purpose: Multi-dataset join, business impact focus, SLA awareness*

5. "Calculate the potential financial penalty if American Airlines experiences an SLA violation this month based on current failure rates."
   - *Purpose: ROI calculation, predictive analysis, specific customer focus*

6. "Are there any MME clusters showing signs of split-brain conditions right now? Which clusters should we investigate immediately?"
   - *Purpose: Infrastructure correlation, cluster-aware analysis, urgency prioritization*

7. "Show me all cell towers in the Southwest region experiencing handoff failures. Are there more than 50 towers affected, indicating a cascade failure?"
   - *Purpose: Geographic filtering, cascade detection threshold, infrastructure impact*

---

**Trend Analysis Questions:**

8. "Compare authentication failure rates between the last hour and the previous 24-hour baseline. Are we seeing a statistical anomaly?"
   - *Purpose: Time-based comparison, statistical analysis, anomaly detection*

9. "Which equipment types are showing the highest failure rates? Is there a pattern suggesting a vendor-specific issue?"
   - *Purpose: Equipment analysis, vendor correlation, pattern recognition*

10. "Show me the trend of HSS sync failures over the last 7 days. Are we seeing increasing corruption events?"
    - *Purpose: Multi-day trend, database health monitoring, escalation detection*

---

**Root Cause and Security Questions:**

11. "Are there any unusual PLMN patterns in authentication failures that might indicate an SS7 security attack or rogue network attempt?"
    - *Purpose: Security analysis, threat detection, pattern anomaly identification*

12. "Find cell towers where both the tower and more than 3 of its neighbor towers are experiencing failures. Show me their power sources and equipment types."
    - *Purpose: Topology-aware analysis, multi-dimensional correlation, infrastructure root cause*

---

**Optimization and Capacity Questions:**

13. "Which MME hosts are handling subscriber loads above 80% of their rated capacity? How many failures are they generating compared to less-loaded hosts?"
    - *Purpose: Capacity analysis, resource exhaustion detection, performance correlation*

14. "Show me the distribution of failures by severity level. What percentage are Critical vs. Warning? Has this distribution changed in the last 6 hours?"
    - *Purpose: Severity analysis, noise filtering, trend comparison*

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "Modern query language, built for analytics at scale"
- "Piped syntax is intuitive and readable - data teams and network engineers can both understand it"
- "Operates on blocks, not rows - extremely performant even with 500K+ failure events"
- "Supports complex operations: LOOKUP JOINs across datasets, window functions for time-series, statistical calculations"
- "EVAL enables on-the-fly calculations - z-scores, risk scores, business metrics - without pre-processing"
- "Purpose-built for Elasticsearch - leverages inverted indices and columnar storage"

### **On Agent Builder:**
- "Bridges AI and enterprise data - no more exporting to CSV or building custom APIs"
- "No custom development - configure, don't code. We built this demo in under an hour"
- "Works with existing Elasticsearch indices - no data migration required"
- "Agent automatically selects right tools based on question context - users don't need to know what data exists where"
- "Natural language to ES|QL translation happens automatically - democratizes access to network operations data"
- "Grounded in your actual data - not hallucinated, every answer is backed by a real query"

### **On Business Value for T-Mobile:**
- "Democratizes network operations data access - NOC engineers, account managers, executives can all ask questions"
- "Real-time insights, always up-to-date - no waiting for daily reports or data warehouse refreshes"
- "Reduces dependency on data teams - network ops can self-serve for 80% of questions"
- "Faster decision-making - identify enterprise SLA risks in seconds, not hours"
- "Proactive vs. reactive - detect cascade failures and split-brain conditions before total outage"
- "Noise reduction - statistical thresholds and multi-dimensional analysis filter out false positives"
- "Cost avoidance - prevent enterprise SLA penalties by identifying at-risk customers early"
- "Reduced MTTR (Mean Time To Resolution) - root cause analysis across multiple datasets in one query"

### **On T-Mobile-Specific Pain Points Addressed:**

**Extended Outages / Customer Churn:**
- "Mass authentication failure detection with z-score analysis catches HSS issues in 5-minute windows, not after customers start calling"
- "Enterprise SLA risk scoring lets account managers proactively reach out before violations occur"

**Radio Equipment Failures:**
- "Cascade failure detection identifies when 50+ towers with same equipment type fail - vendor bug escalation in minutes"
- "Equipment type correlation shows patterns invisible to single-tower monitoring"

**Core Network Split-Brain:**
- "Cluster-aware MME analysis detects synchronized failures across hosts - split-brain signature"
- "Signaling storm detection based on critical spike thresholds and multi-host correlation"

**HSS Database Issues:**
- "Statistical anomaly detection on authentication rates - 3 standard deviations triggers alert"
- "HSS sync event correlation with authentication failures - proves database root cause"

**SLA Violations:**
- "Enterprise customer prioritization in all failure analysis - never miss a high-value account issue"
- "Contract SLA-aware risk scoring - 99.99% SLA customers flagged at lower failure thresholds"

---

## **🔧 Troubleshooting**

**If a query fails:**
- Check index names match exactly: `mme_failure_events`, `mme_hosts`, `cell_towers`, `subscriber_profiles`, `hss_sync_events`
- Verify field names are case-sensitive correct: `subscriber_id` not `Subscriber_ID`
- Ensure joined indices are in lookup mode: Run `GET mme_hosts/_settings` and verify `"index.mode": "lookup"`
- Check time range: If using `NOW() - 1 hour`, ensure you have recent data with `@timestamp` in that window

**If LOOKUP JOIN returns no results:**
- Verify join key format is consistent: Both indices must have exact matching values (e.g., "mme_host_12")
- Check that lookup index has data: Run `GET mme_hosts/_count` to verify records exist
- Confirm lookup index mode: `GET mme_hosts/_settings` should show `"mode": "lookup"`
- Test join key existence: Run simple query on both indices to verify join key values overlap

**If agent gives wrong answer:**
- Check tool descriptions - are they clear about when to use each tool?
- Review custom instructions - does the agent understand T-Mobile's priorities (enterprise customers, SLA risk)?
- Verify tool queries return expected results - run them manually in Dev Tools
- Check if question is ambiguous - try rephrasing with more specifics (time range, customer type, failure type)

**If statistical calculations seem off:**
- Verify TO_DOUBLE() is used in division operations - integer division will truncate decimals
- Check z-score parameters (mean: 2.5, std dev: 1.2) - adjust based on your actual baseline data
- Ensure sufficient data volume - statistical methods need meaningful sample sizes

**If performance is slow:**
- Add time range filters: `WHERE @timestamp > NOW() - 24 hours` dramatically reduces data scanned
- Use LIMIT on large result sets: Especially after STATS operations
- Check index shard count: 500K records should be on 1-2 shards max for lookup indices
- Consider data stream for timeseries indices: Improves query performance on time-range filters

---

## **🎬 Closing**

"What we've shown today with T-Mobile's network operations data:

✅ **Complex analytics on interconnected datasets** - MME failures, cell towers, subscribers, HSS sync - all joined and analyzed together

✅ **Natural language interface for non-technical users** - Account managers can check enterprise SLA risk without knowing ES|QL

✅ **Real-time insights without custom development** - No Spark jobs, no data pipelines, no months of engineering

✅ **Queries that would take hours, answered in seconds** - Cascade failure detection across 5,000 towers, enterprise impact analysis, split-brain detection

✅ **Proactive vs. reactive operations** - Detect HSS corruption before authentication fails, identify SLA risk before violations, catch split-brain before total outage

✅ **Noise reduction through multi-dimensional analysis** - Statistical thresholds, cluster correlation, infrastructure context - only alert on real problems

✅ **Business impact focus** - Enterprise customer prioritization, SLA-aware risk scoring, financial penalty calculations

**Deployment Timeline:**
- Data ingestion: 1-2 days (if not already in Elasticsearch)
- Agent Builder configuration: 2-4 hours
- Tool creation and testing: 1 day
- User training: 2 hours
- Total: Can be deployed in **1 week**, not months

**Next Steps:**
1. Identify additional datasets to enrich analysis (vendor ticketing, customer complaints, billing)
2. Define custom thresholds and baselines for your specific network (z-score parameters, cascade thresholds)
3. Integrate with alerting workflows (PagerDuty, ServiceNow)
4. Expand to additional use cases (capacity planning, predictive maintenance, fraud detection)

**Questions?**"

---

## **📚 Appendix: Additional Query Examples**

### **HSS Corruption Impact Analysis**

```esql
FROM hss_sync_events
| WHERE @timestamp > NOW() - 24 hours AND corruption_detected == true
| MV_EXPAND affected_subscribers
| LOOKUP JOIN subscriber_profiles ON subscriber_id = affected_subscribers
| WHERE account_type == "Enterprise"
| STATS 
    corruption_events = COUNT(*),
    unique_enterprises = COUNT_DISTINCT(enterprise_name)
  BY enterprise_name, contract_sla
| SORT corruption_events DESC
| LIMIT 20
```

**Use Case:** Identify which enterprise customers were affected by HSS database corruption events, prioritized by contract SLA.

---

### **Geographic Heat Map of Failures**

```esql
FROM mme_failure_events
| WHERE @timestamp > NOW() - 4 hours
| STATS failure_count = COUNT(*) BY cell_tower_id
| LOOKUP JOIN cell_towers ON cell_tower_id
| KEEP tower_name, region, location, equipment_type, failure_count
| WHERE failure_count > 50
| SORT failure_count DESC
```

**Use Case:** Create geographic visualization of failure hot spots, enriched with tower metadata for infrastructure correlation.

---

### **MME Software Version Correlation**

```esql
FROM mme_failure_events
| WHERE @timestamp > NOW() - 7 days
| STATS failure_count = COUNT(*), unique_subscribers = COUNT_DISTINCT(subscriber_id) BY mme_host_id
| LOOKUP JOIN mme_hosts ON mme_host_id
| STATS 
    hosts_with_version = COUNT(*),
    total_failures = SUM(failure_count),
    total_subscribers_impacted = SUM(unique_subscribers),
    avg_failures_per_host = AVG(failure_count)
  BY software_version
| EVAL failure_rate_per_host = ROUND(TO_DOUBLE(total_failures) / TO_DOUBLE(hosts_with_version), 2)
| SORT total_failures DESC
```

**Use Case:** Identify if specific MME software versions correlate with higher failure rates - detect software bugs before widespread deployment.

---

### **Power Source Failure Correlation**

```esql
FROM mme_failure_events
| WHERE @timestamp > NOW() - 12 hours AND failure_type == "Handoff"
| STATS handoff_failures = COUNT(*) BY cell_tower_id
| LOOKUP JOIN cell_towers ON cell_tower_id
| STATS 
    towers_affected = COUNT(*),
    total_handoff_failures = SUM(handoff_failures)
  BY power_source, region
| EVAL avg_failures_per_tower = ROUND(TO_DOUBLE(total_handoff_failures) / TO_DOUBLE(towers_affected), 2)
| SORT total_handoff_failures DESC
```

**Use Case:** Detect if cell site power failures (battery backup, solar) are causing handoff issues - infrastructure root cause analysis.

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
