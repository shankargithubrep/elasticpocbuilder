from src.framework.base import DemoGuideModule, DemoConfig
from typing import Dict, List, Any, Optional
import pandas as pd

class TMobileUSAIncDemoGuide(DemoGuideModule):
    """Demo guide for T-Mobile USA, Inc. - Network Operations Center (NOC) - Core Network Engineering"""

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
**Audience:** Network Operations Center (NOC) - Core Network Engineering technical/business stakeholders
**Goal:** Show how Agent Builder enables AI-powered analytics on T-Mobile USA, Inc. data

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## **🗂️ Dataset Architecture**

### **mme_signaling_events** (Timeseries Index)
**Record Count:** 500,000 records
**Index Mode:** Standard timeseries
**Primary Key:** event_id
**Purpose:** Core signaling event data from MME infrastructure capturing Diameter, GTP-C, and S1-AP protocol messages

**Key Fields:**
- `@timestamp` - Event occurrence time (ISO 8601)
- `event_id` - Unique event identifier (string)
- `mme_host_id` - MME server identifier (string, FK to mme_infrastructure)
- `cluster_id` - MME cluster identifier (string)
- `imsi` - International Mobile Subscriber Identity (string, FK to subscriber_profiles)
- `plmn_id` - Public Land Mobile Network ID for roaming partner (string, FK to roaming_partners)
- `cell_site_id` - Cell tower identifier (string, FK to cell_site_inventory)
- `message_type` - Protocol message type (authentication_request, attach_request, handoff_request, location_update, etc.)
- `interface` - Signaling interface (S6a_diameter, S11_gtpc, S1AP)
- `result_code` - Message result (success, failure, timeout, retry)
- `response_time_ms` - Message processing time in milliseconds (long)
- `memory_used_mb` - MME memory utilization at event time (long)
- `thread_pool_depth` - Active thread count (long)
- `queue_depth` - Message queue depth (long)
- `retry_count` - Number of message retries (long)
- `tracking_area_code` - TAC for location tracking (string)

**Relationships:**
- Joins to `mme_infrastructure` via `mme_host_id`
- Joins to `subscriber_profiles` via `imsi`
- Joins to `roaming_partners` via `plmn_id`
- Joins to `cell_site_inventory` via `cell_site_id`

---

### **mme_infrastructure** (Reference/Lookup Index)
**Record Count:** 150 records
**Index Mode:** lookup
**Primary Key:** mme_host_id
**Purpose:** MME server infrastructure metadata and capacity specifications

**Key Fields:**
- `mme_host_id` - Unique MME server identifier (string)
- `cluster_id` - Cluster assignment (string)
- `datacenter` - Physical datacenter location (string)
- `hardware_model` - Server hardware model (string)
- `software_version` - MME software version (string)
- `max_capacity_subscribers` - Maximum subscriber capacity (long)
- `memory_total_gb` - Total server memory in GB (long)
- `cpu_cores` - Number of CPU cores (long)
- `deployment_date` - Server deployment date (date)
- `last_restart` - Last restart timestamp (date)
- `cluster_role` - Role in cluster (active, standby, backup)

---

### **subscriber_profiles** (Reference/Lookup Index)
**Record Count:** 5,000 records
**Index Mode:** lookup
**Primary Key:** imsi
**Purpose:** High-value subscriber profiles for churn risk analysis

**Key Fields:**
- `imsi` - International Mobile Subscriber Identity (string)
- `subscriber_tier` - Service tier (platinum, gold, silver, bronze)
- `monthly_revenue` - Monthly recurring revenue (double)
- `account_tenure_months` - Account age in months (long)
- `contract_type` - Contract type (postpaid, prepaid)
- `data_plan_gb` - Monthly data allowance in GB (long)
- `international_roaming_enabled` - Roaming flag (boolean)
- `sla_target_availability` - SLA availability target percentage (double)
- `incident_count_30d` - Service incidents in last 30 days (long)
- `complaint_count_90d` - Customer complaints in last 90 days (long)
- `churn_risk_score` - Calculated churn risk (0-100) (double)

---

### **roaming_partners** (Reference/Lookup Index)
**Record Count:** 200 records
**Index Mode:** lookup
**Primary Key:** plmn_id
**Purpose:** International roaming partner configuration and agreement details

**Key Fields:**
- `plmn_id` - Public Land Mobile Network identifier (string)
- `operator_name` - Roaming partner operator name (string)
- `country_code` - ISO country code (string)
- `region` - Geographic region (EMEA, APAC, Americas, etc.)
- `agreement_type` - Roaming agreement type (bilateral, unilateral, IPX)
- `authentication_method` - Auth method (MAP, Diameter, hybrid)
- `traffic_baseline_daily_auth` - Expected daily authentication volume (long)
- `traffic_baseline_daily_data_mb` - Expected daily data volume in MB (long)
- `sla_max_auth_failures_pct` - Maximum allowed authentication failure rate (double)
- `security_risk_level` - Partner risk level (low, medium, high)
- `agreement_start_date` - Agreement effective date (date)
- `last_config_change` - Last configuration update (date)

---

### **cell_site_inventory** (Reference/Lookup Index)
**Record Count:** 8,000 records
**Index Mode:** lookup
**Primary Key:** cell_site_id
**Purpose:** Cell tower infrastructure and geographic coverage data

**Key Fields:**
- `cell_site_id` - Unique cell site identifier (string)
- `site_name` - Human-readable site name (string)
- `tracking_area_code` - TAC assignment (string)
- `latitude` - Geographic latitude (double)
- `longitude` - Geographic longitude (double)
- `coverage_radius_meters` - Approximate coverage radius (long)
- `technology` - Radio technology (LTE, 5G_NSA, 5G_SA)
- `capacity_max_subscribers` - Maximum concurrent subscribers (long)
- `neighbor_sites` - Comma-separated list of neighbor cell_site_ids (string)
- `commissioning_date` - Site activation date (date)
- `last_maintenance` - Last maintenance date (date)
- `site_priority` - Site importance (critical, high, medium, low)
- `backhaul_type` - Backhaul connection type (fiber, microwave, satellite)

---

## **🚀 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

**CRITICAL: All indexes need "index.mode": "lookup" for joins to work (except the timeseries index)**

---

#### **1. Create mme_signaling_events index (Timeseries)**

**Navigate to:** Dev Tools Console

**Run:**

```json
PUT /mme_signaling_events
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "event_id": { "type": "keyword" },
      "mme_host_id": { "type": "keyword" },
      "cluster_id": { "type": "keyword" },
      "imsi": { "type": "keyword" },
      "plmn_id": { "type": "keyword" },
      "cell_site_id": { "type": "keyword" },
      "message_type": { "type": "keyword" },
      "interface": { "type": "keyword" },
      "result_code": { "type": "keyword" },
      "response_time_ms": { "type": "long" },
      "memory_used_mb": { "type": "long" },
      "thread_pool_depth": { "type": "long" },
      "queue_depth": { "type": "long" },
      "retry_count": { "type": "long" },
      "tracking_area_code": { "type": "keyword" }
    }
  }
}
```

**Upload CSV:** Management → Stack Management → Data → Upload a file → Select `mme_signaling_events.csv` → Import to `mme_signaling_events` index

---

#### **2. Create mme_infrastructure index (Lookup)**

**Run:**

```json
PUT /mme_infrastructure
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "mme_host_id": { "type": "keyword" },
      "cluster_id": { "type": "keyword" },
      "datacenter": { "type": "keyword" },
      "hardware_model": { "type": "keyword" },
      "software_version": { "type": "keyword" },
      "max_capacity_subscribers": { "type": "long" },
      "memory_total_gb": { "type": "long" },
      "cpu_cores": { "type": "long" },
      "deployment_date": { "type": "date" },
      "last_restart": { "type": "date" },
      "cluster_role": { "type": "keyword" }
    }
  }
}
```

**Upload CSV:** Upload `mme_infrastructure.csv` to `mme_infrastructure` index

---

#### **3. Create subscriber_profiles index (Lookup)**

**Run:**

```json
PUT /subscriber_profiles
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "imsi": { "type": "keyword" },
      "subscriber_tier": { "type": "keyword" },
      "monthly_revenue": { "type": "double" },
      "account_tenure_months": { "type": "long" },
      "contract_type": { "type": "keyword" },
      "data_plan_gb": { "type": "long" },
      "international_roaming_enabled": { "type": "boolean" },
      "sla_target_availability": { "type": "double" },
      "incident_count_30d": { "type": "long" },
      "complaint_count_90d": { "type": "long" },
      "churn_risk_score": { "type": "double" }
    }
  }
}
```

**Upload CSV:** Upload `subscriber_profiles.csv` to `subscriber_profiles` index

---

#### **4. Create roaming_partners index (Lookup)**

**Run:**

```json
PUT /roaming_partners
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "plmn_id": { "type": "keyword" },
      "operator_name": { "type": "keyword" },
      "country_code": { "type": "keyword" },
      "region": { "type": "keyword" },
      "agreement_type": { "type": "keyword" },
      "authentication_method": { "type": "keyword" },
      "traffic_baseline_daily_auth": { "type": "long" },
      "traffic_baseline_daily_data_mb": { "type": "long" },
      "sla_max_auth_failures_pct": { "type": "double" },
      "security_risk_level": { "type": "keyword" },
      "agreement_start_date": { "type": "date" },
      "last_config_change": { "type": "date" }
    }
  }
}
```

**Upload CSV:** Upload `roaming_partners.csv` to `roaming_partners` index

---

#### **5. Create cell_site_inventory index (Lookup)**

**Run:**

```json
PUT /cell_site_inventory
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "cell_site_id": { "type": "keyword" },
      "site_name": { "type": "keyword" },
      "tracking_area_code": { "type": "keyword" },
      "latitude": { "type": "double" },
      "longitude": { "type": "double" },
      "coverage_radius_meters": { "type": "long" },
      "technology": { "type": "keyword" },
      "capacity_max_subscribers": { "type": "long" },
      "neighbor_sites": { "type": "keyword" },
      "commissioning_date": { "type": "date" },
      "last_maintenance": { "type": "date" },
      "site_priority": { "type": "keyword" },
      "backhaul_type": { "type": "keyword" }
    }
  }
}
```

**Upload CSV:** Upload `cell_site_inventory.csv` to `cell_site_inventory` index

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to your AI Agent chat interface
- Have the agent already configured with all tools

### **Demo Script**

**Presenter:** "Before we dive into how this works, let me show you the end result. I'm going to ask our AI agent a complex business question that would normally require a data analyst hours to answer."

**Sample questions to demonstrate:**

---

**Question 1 (ROI & Business Impact):**
> "Which MME clusters are showing signs of split-brain conditions in the last 24 hours, and what's the estimated subscriber impact and revenue at risk if we don't address this immediately?"

**What to highlight:** "Notice the agent is correlating signaling anomalies, calculating affected subscriber counts, joining with subscriber revenue data, and providing a business impact assessment—all in seconds."

---

**Question 2 (Proactive Threat Detection):**
> "Are there any roaming partners showing suspicious authentication patterns that deviate from their baseline behavior? Flag any potential SS7 or Diameter security threats."

**What to highlight:** "The agent is comparing current authentication volumes and failure rates against historical baselines per roaming partner, identifying anomalies that could indicate location tracking attacks or other security threats."

---

**Question 3 (Root Cause Analysis):**
> "We're seeing handoff failures spike in the Northeast region. Which cell towers are the root cause, and how many subscribers are being impacted by cascade failures?"

**What to highlight:** "This requires correlating handoff failure events, analyzing neighbor site relationships, identifying the originating tower, and calculating cascade impact—complex spatial and temporal analysis done conversationally."

---

**Question 4 (Predictive Maintenance):**
> "Which MME servers are showing gradual memory growth patterns that could lead to crashes in the next 7-14 days? Give me the top 5 by risk level."

**What to highlight:** "The agent is performing statistical analysis on memory utilization trends over time, calculating z-scores to detect abnormal growth patterns, and prioritizing by potential subscriber impact."

---

**Question 5 (Churn Risk & Customer Experience):**
> "Show me platinum and gold tier subscribers who've experienced 3 or more service disruptions in the last 30 days and are now below their SLA targets. These are churn risks we need to address."

**What to highlight:** "Joining signaling failure data with subscriber profiles, filtering by tier and incident count, calculating SLA compliance—this is the kind of proactive customer retention intelligence that prevents revenue loss."

---

**Question 6 (Trend Analysis):**
> "What's the trend in signaling storm incidents over the last 90 days? Are we getting better or worse at early detection?"

**What to highlight:** "Time-series trend analysis with context about detection latency improvements."

---

**Question 7 (Cross-Dataset Operational Intelligence):**
> "For the MME cluster that had the split-brain incident yesterday, show me the hardware specs, software versions, last restart times, and recent memory utilization trends for all hosts in that cluster."

**What to highlight:** "Seamlessly joining infrastructure metadata with real-time operational metrics to provide complete operational context for incident response."

---

**Transition:** "So how does this actually work? Let's go under the hood and build these queries from scratch using ES|QL, Elasticsearch's modern query language."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open Kibana Dev Tools Console
- Have the indices already created and populated

---

### **Query 1: Simple Aggregation (2 minutes)**

**Presenter:** "T-Mobile wants to know: Which MME clusters are handling the highest signaling load, and what's the average response time per cluster?"

**Copy/paste into console:**

```esql
FROM mme_signaling_events
| STATS total_messages = COUNT(*), avg_response_ms = AVG(response_time_ms) BY cluster_id
| SORT total_messages DESC
| LIMIT 10
```

**Run and narrate results:** "This is basic ES|QL:
- FROM: Source our signaling events data
- STATS: Aggregate message counts and calculate average response time, grouped by cluster
- SORT and LIMIT: Show top 10 busiest clusters

The syntax is intuitive - it reads like English. This gives us a quick operational view of cluster load distribution."

---

### **Query 2: Add Calculations with EVAL (3 minutes)**

**Presenter:** "Let's add calculations to identify signaling storms by detecting abnormal retry rates and queue depths—early warning indicators before cascade failures impact thousands of subscribers."

**Copy/paste:**

```esql
FROM mme_signaling_events
| WHERE @timestamp >= NOW() - 1 hour
| STATS 
    total_messages = COUNT(*),
    retry_messages = COUNT(*) WHERE retry_count > 0,
    avg_queue_depth = AVG(queue_depth),
    max_queue_depth = MAX(queue_depth),
    avg_response_ms = AVG(response_time_ms)
  BY cluster_id, mme_host_id
| EVAL retry_rate_pct = TO_DOUBLE(retry_messages) / TO_DOUBLE(total_messages) * 100
| EVAL queue_depth_variance = max_queue_depth - avg_queue_depth
| WHERE retry_rate_pct > 5 OR avg_queue_depth > 1000
| SORT retry_rate_pct DESC
| LIMIT 20
```

**Run and highlight:** "Key additions:
- EVAL: Creates calculated fields on-the-fly—retry rate percentage and queue depth variance
- TO_DOUBLE: Critical for decimal division to get accurate percentages
- WHERE clause filtering: Focus on hosts showing storm indicators (>5% retry rate or queue depth >1000)
- Multiple STATS: Aggregating multiple metrics simultaneously
- Business-relevant calculations: These thresholds align with T-Mobile's cascade failure detection requirements—catch issues before they impact 2,000+ subscribers

This query would alert on signaling storm precursors within 5 minutes instead of the current 15-30 minute detection delay."

---

### **Query 3: Join Datasets with LOOKUP JOIN (3 minutes)**

**Presenter:** "Now let's combine signaling data with MME infrastructure metadata to identify which specific servers are at risk of resource exhaustion. This is where ES|QL's JOIN capability shines."

**Copy/paste:**

```esql
FROM mme_signaling_events
| WHERE @timestamp >= NOW() - 4 hours
| STATS 
    avg_memory_mb = AVG(memory_used_mb),
    max_memory_mb = MAX(memory_used_mb),
    avg_thread_depth = AVG(thread_pool_depth),
    message_count = COUNT(*)
  BY mme_host_id
| EVAL memory_growth_rate = (max_memory_mb - avg_memory_mb) / avg_memory_mb * 100
| LOOKUP JOIN mme_infrastructure ON mme_host_id
| EVAL memory_utilization_pct = TO_DOUBLE(max_memory_mb) / TO_DOUBLE(memory_total_gb * 1024) * 100
| EVAL capacity_utilization_pct = TO_DOUBLE(message_count) / TO_DOUBLE(max_capacity_subscribers) * 100
| WHERE memory_growth_rate > 15 OR memory_utilization_pct > 85
| SORT memory_utilization_pct DESC
| KEEP mme_host_id, cluster_id, datacenter, software_version, memory_utilization_pct, memory_growth_rate, capacity_utilization_pct, max_memory_mb, memory_total_gb
| LIMIT 15
```

**Run and explain:** "Magic happening here:
- LOOKUP JOIN: Combines signaling events with infrastructure metadata using mme_host_id as the join key
- Now we have access to fields from both datasets—memory_total_gb, max_capacity_subscribers, software_version, datacenter
- This is a LEFT JOIN: All MME hosts are kept, enriched with infrastructure data
- Memory utilization percentage: Comparing actual usage against total capacity
- Memory growth rate: Detecting the gradual degradation pattern that indicates memory leaks
- For LOOKUP JOIN to work, the mme_infrastructure index must have 'index.mode: lookup'

This query identifies MME servers showing memory leak patterns before they crash and impact 50,000-150,000 subscribers. Current 5-minute SNMP polling misses these gradual patterns—this captures them in real-time."

---

### **Query 4: Complex Multi-Dataset Analytics (2 minutes)**

**Presenter:** "For the grand finale - a sophisticated analytical query showing split-brain detection with full business impact analysis. This correlates signaling anomalies, infrastructure state, and subscriber revenue data to answer: 'Which clusters have split-brain conditions right now, and what's the dollar impact?'"

**Copy/paste:**

```esql
FROM mme_signaling_events
| WHERE @timestamp >= NOW() - 60 seconds
| WHERE message_type == "authentication_request" OR message_type == "attach_request"
| STATS 
    unique_active_hosts = COUNT_DISTINCT(mme_host_id),
    total_auth_requests = COUNT(*),
    unique_imsi_count = COUNT_DISTINCT(imsi),
    duplicate_registrations = COUNT(*) - COUNT_DISTINCT(imsi)
  BY cluster_id
| WHERE unique_active_hosts > 1 AND duplicate_registrations > 10
| EVAL split_brain_severity = CASE(
    duplicate_registrations > 100, "CRITICAL",
    duplicate_registrations > 50, "HIGH",
    "MEDIUM"
  )
| LOOKUP JOIN mme_infrastructure ON cluster_id
| EVAL total_cluster_capacity = max_capacity_subscribers * unique_active_hosts
| EVAL affected_subscriber_estimate = duplicate_registrations * 2
| MV_EXPAND imsi
| LOOKUP JOIN subscriber_profiles ON imsi
| STATS 
    total_affected_subscribers = SUM(affected_subscriber_estimate),
    platinum_subscribers_affected = COUNT(*) WHERE subscriber_tier == "platinum",
    gold_subscribers_affected = COUNT(*) WHERE subscriber_tier == "gold",
    avg_monthly_revenue_per_sub = AVG(monthly_revenue),
    total_revenue_at_risk = SUM(monthly_revenue),
    high_churn_risk_subs = COUNT(*) WHERE churn_risk_score > 70
  BY cluster_id, split_brain_severity, datacenter
| EVAL hourly_revenue_impact = total_revenue_at_risk / 730
| EVAL estimated_outage_cost_1hr = hourly_revenue_impact * 1
| WHERE total_affected_subscribers > 500
| SORT total_revenue_at_risk DESC
| KEEP cluster_id, datacenter, split_brain_severity, total_affected_subscribers, platinum_subscribers_affected, gold_subscribers_affected, total_revenue_at_risk, estimated_outage_cost_1hr, high_churn_risk_subs
| LIMIT 10
```

**Run and break down:** 

"This query is doing enterprise-grade analytics:

**Split-Brain Detection Logic:**
- Looking at last 60 seconds of authentication/attach requests
- Counting distinct active MME hosts per cluster
- Detecting duplicate IMSI registrations—the smoking gun of split-brain
- Flagging clusters where multiple hosts are simultaneously active (unique_active_hosts > 1) AND seeing duplicate registrations

**Severity Classification:**
- CASE statement categorizes severity based on duplicate registration count
- CRITICAL: >100 duplicates (major split-brain affecting 200+ subscribers)
- HIGH: >50 duplicates
- MEDIUM: 10-50 duplicates

**Multi-Dataset Enrichment:**
- First LOOKUP JOIN: Gets MME infrastructure data (capacity, datacenter)
- MV_EXPAND: Explodes the IMSI array to join with subscriber profiles
- Second LOOKUP JOIN: Enriches with subscriber tier and revenue data

**Business Impact Calculation:**
- Estimates affected subscribers (duplicate registrations × 2 for cascade effect)
- Segments by subscriber tier (platinum/gold get priority response)
- Calculates total monthly revenue at risk
- Converts to hourly impact (÷ 730 hours/month)
- Identifies high churn-risk subscribers who need proactive outreach

**Operational Intelligence:**
- Filters to significant incidents (>500 subscribers affected)
- Sorts by revenue impact to prioritize response
- Provides datacenter context for rapid incident response

This single query replaces what would normally require:
- A data analyst writing SQL joins across 3 databases
- Manual calculation of business impact in a spreadsheet
- 30-60 minutes of analysis time

Instead, it runs in under 2 seconds and gives NOC engineers immediate, actionable intelligence with business context. This is how you reduce split-brain detection from 15-30 minutes to under 60 seconds while simultaneously quantifying the business impact."

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

**Agent Configuration:**

**Agent ID:** `tmobile-noc-core-network-analyst`

**Display Name:** `T-Mobile Core Network Intelligence Agent`

**Custom Instructions:** 

"You are an expert telecommunications network analyst specializing in T-Mobile's Core Network Operations. Your role is to analyze MME signaling data, detect network anomalies, predict failures, and provide actionable intelligence to prevent subscriber impact.

**Key Responsibilities:**
- Detect split-brain conditions, signaling storms, and resource exhaustion patterns
- Analyze SS7/Diameter security threats and roaming partner anomalies
- Identify cell tower handoff cascade failures and root cause cell sites
- Calculate business impact in terms of affected subscribers and revenue at risk
- Prioritize incidents by subscriber tier (platinum/gold) and churn risk
- Provide proactive recommendations to prevent SLA violations

**Critical Thresholds:**
- Split-brain: Multiple active MME hosts in cluster with duplicate IMSI registrations
- Signaling storm: Retry rate >5% or queue depth >1000 messages
- Resource exhaustion: Memory growth >15% in 4 hours or utilization >85%
- Security threat: Authentication failures >2x baseline or volume spike >3 standard deviations
- Cascade failure: Handoff failures affecting >500 subscribers with neighbor site correlation

**Response Format:**
- Always quantify subscriber impact and revenue at risk
- Segment impact by subscriber tier when relevant
- Include datacenter/cluster/host identifiers for rapid response
- Provide severity classification (CRITICAL/HIGH/MEDIUM/LOW)
- Suggest specific mitigation actions based on incident type

**Data Context:**
- mme_signaling_events: 500K real-time signaling messages from MME infrastructure
- mme_infrastructure: 150 MME servers across clusters and datacenters
- subscriber_profiles: 5K high-value subscriber profiles with revenue and churn risk
- roaming_partners: 200 international roaming partner configurations
- cell_site_inventory: 8K cell tower locations and coverage data

When analyzing trends, use appropriate time windows: 1-hour for real-time detection, 4-hour for resource exhaustion, 24-hour for pattern analysis, 7-14 days for memory leak detection."

---

### **Creating Tools**

#### **Tool 1: Split-Brain Detection & Impact Analysis**

**Tool Name:** `detect_split_brain_conditions`

**Description:** "Detects MME cluster split-brain conditions by identifying multiple simultaneously active hosts with duplicate IMSI registrations in the last 60 seconds. Returns affected clusters with subscriber impact, revenue at risk, and severity classification. Use this for real-time split-brain monitoring and when investigating duplicate registration incidents."

**ES|QL Query:**
```esql
FROM mme_signaling_events
| WHERE @timestamp >= NOW() - 60 seconds
| WHERE message_type == "authentication_request" OR message_type == "attach_request"
| STATS 
    unique_active_hosts = COUNT_DISTINCT(mme_host_id),
    duplicate_registrations = COUNT(*) - COUNT_DISTINCT(imsi),
    unique_imsi_count = COUNT_DISTINCT(imsi)
  BY cluster_id
| WHERE unique_active_hosts > 1 AND duplicate_registrations > 10
| EVAL split_brain_severity = CASE(
    duplicate_registrations > 100, "CRITICAL",
    duplicate_registrations > 50, "HIGH",
    "MEDIUM"
  )
| EVAL affected_subscriber_estimate = duplicate_registrations * 2
| SORT duplicate_registrations DESC
```

---

#### **Tool 2: Proactive MME Resource Exhaustion Detection**

**Tool Name:** `detect_mme_resource_exhaustion`

**Description:** "Identifies MME servers showing gradual resource degradation patterns (memory leaks, thread pool exhaustion) before service-affecting failures. Analyzes 4-hour memory growth trends and current utilization against capacity. Use this for proactive maintenance scheduling and when investigating performance degradation. Returns top at-risk MME hosts with infrastructure context."

**ES|QL Query:**
```esql
FROM mme_signaling_events
| WHERE @timestamp >= NOW() - 4 hours
| STATS 
    avg_memory_mb = AVG(memory_used_mb),
    max_memory_mb = MAX(memory_used_mb),
    min_memory_mb = MIN(memory_used_mb),
    avg_thread_depth = AVG(thread_pool_depth),
    max_queue_depth = MAX(queue_depth)
  BY mme_host_id
| EVAL memory_growth_rate = (max_memory_mb - min_memory_mb) / min_memory_mb * 100
| LOOKUP JOIN mme_infrastructure ON mme_host_id
| EVAL memory_utilization_pct = TO_DOUBLE(max_memory_mb) / TO_DOUBLE(memory_total_gb * 1024) * 100
| WHERE memory_growth_rate > 15 OR memory_utilization_pct > 85
| SORT memory_utilization_pct DESC
| LIMIT 20
```

---

#### **Tool 3: Roaming Partner Security Threat Detection**

**Tool Name:** `detect_roaming_security_threats`

**Description:** "Detects SS7/Diameter security threats by comparing roaming partner authentication patterns against baseline behavior. Identifies location tracking attempts, abnormal authentication failures, and suspicious traffic volume spikes per PLMN. Use this for security monitoring and when investigating roaming partner anomalies. Returns partners with anomaly scores and threat indicators."

**ES|QL Query:**
```esql
FROM mme_signaling_events
| WHERE @timestamp >= NOW() - 24 hours
| WHERE plmn_id IS NOT NULL
| STATS 
    total_auth_requests = COUNT(*),
    failed_auths = COUNT(*) WHERE result_code == "failure",
    timeout_auths = COUNT(*) WHERE result_code == "timeout",
    avg_response_ms = AVG(response_time_ms)
  BY plmn_id
| EVAL failure_rate_pct = TO_DOUBLE(failed_auths) / TO_DOUBLE(total_auth_requests) * 100
| LOOKUP JOIN roaming_partners ON plmn_id
| EVAL traffic_deviation_pct = (TO_DOUBLE(total_auth_requests) - TO_DOUBLE(traffic_baseline_daily_auth)) / TO_DOUBLE(traffic_baseline_daily_auth) * 100
| EVAL baseline_failure_threshold = sla_max_auth_failures_pct * 2
| WHERE failure_rate_pct > baseline_failure_threshold OR traffic_deviation_pct > 300 OR traffic_deviation_pct < -80
| EVAL threat_severity = CASE(
    failure_rate_pct > baseline_failure_threshold * 3, "CRITICAL",
    traffic_deviation_pct > 500, "HIGH",
    "MEDIUM"
  )
| SORT failure_rate_pct DESC
| LIMIT 15
```

---

#### **Tool 4: Subscriber Churn Risk Analysis**

**Tool Name:** `identify_churn_risk_subscribers`

**Description:** "Identifies high-value subscribers at elevated churn risk by correlating recent service failures with incident history and SLA compliance. Flags platinum/gold subscribers with 3+ disruptions in 30 days who are below SLA targets. Use this for proactive customer retention and when analyzing subscriber experience impact. Returns prioritized list with revenue context."

**ES|QL Query:**
```esql
FROM mme_signaling_events
| WHERE @timestamp >= NOW() - 30 days
| WHERE result_code == "failure" OR result_code == "timeout"
| STATS incident_count = COUNT(*) BY imsi
| WHERE incident_count >= 3
| LOOKUP JOIN subscriber_profiles ON imsi
| WHERE subscriber_tier == "platinum" OR subscriber_tier == "gold"
| WHERE incident_count > incident_count_30d OR churn_risk_score > 60
| EVAL sla_compliance_gap = sla_target_availability - 95.0
| EVAL retention_priority = CASE(
    subscriber_tier == "platinum" AND churn_risk_score > 80, "URGENT",
    subscriber_tier == "platinum" OR churn_risk_score > 70, "HIGH",
    "MEDIUM"
  )
| SORT monthly_revenue DESC
| LIMIT 50
```

---

#### **Tool 5: Signaling Storm Early Warning**

**Tool Name:** `detect_signaling_storm_precursors`

**Description:** "Detects signaling storm precursors by identifying abnormal message retry acceleration and duplicate transaction patterns across Diameter S6a and GTP-C S11 interfaces. Uses 5-minute intervals to flag cascade risks before affecting 2,000+ subscribers. Use this for real-time storm prevention and when investigating retry spikes."

**ES|QL Query:**
```esql
FROM mme_signaling_events
| WHERE @timestamp >= NOW() - 1 hour
| WHERE interface == "S6a_diameter" OR interface == "S11_gtpc"
| STATS 
    total_messages = COUNT(*),
    retry_messages = COUNT(*) WHERE retry_count > 0,
    avg_retry_count = AVG(retry_count),
    max_queue_depth = MAX(queue_depth),
    avg_queue_depth = AVG(queue_depth)
  BY cluster_id, mme_host_id, BUCKET(@timestamp, 5 minutes)
| EVAL retry_rate_pct = TO_DOUBLE(retry_messages) / TO_DOUBLE(total_messages) * 100
| WHERE retry_rate_pct > 5 OR max_queue_depth > 1000
| EVAL storm_risk_level = CASE(
    retry_rate_pct > 15 AND max_queue_depth > 2000, "CRITICAL",
    retry_rate_pct > 10 OR max_queue_depth > 1500, "HIGH",
    "MEDIUM"
  )
| SORT @timestamp DESC, retry_rate_pct DESC
```

---

#### **Tool 6: Cell Tower Handoff Cascade Failure Analysis**

**Tool Name:** `analyze_handoff_cascade_failures`

**Description:** "Identifies root cause cell sites triggering cascade handoff failures by analyzing failure concentration patterns and neighbor site relationships. Correlates handoff failures across tracking areas to pinpoint originating tower within 5 minutes. Use this when investigating regional handoff issues and subscriber connectivity problems."

**ES|QL Query:**
```esql
FROM mme_signaling_events
| WHERE @timestamp >= NOW() - 1 hour
| WHERE message_type == "handoff_request" AND result_code == "failure"
| STATS 
    failure_count = COUNT(*),
    affected_subscribers = COUNT_DISTINCT(imsi),
    avg_response_ms = AVG(response_time_ms)
  BY cell_site_id, tracking_area_code
| WHERE failure_count > 50
| LOOKUP JOIN cell_site_inventory ON cell_site_id
| EVAL impact_severity = CASE(
    affected_subscribers > 1500, "CRITICAL - CASCADE",
    affected_subscribers > 500, "HIGH - PRIMARY FAILURE",
    "MEDIUM"
  )
| SORT affected_subscribers DESC
| LIMIT 20
```

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

#### **Warm-up Questions (Start Here):**

1. **"What MME clusters are currently handling the most signaling traffic?"**
   - *Purpose: Simple aggregation to warm up, shows basic data access*

2. **"Show me the top 5 MME servers by current memory utilization percentage."**
   - *Purpose: Demonstrates infrastructure monitoring capability*

3. **"Which roaming partners are we exchanging the most authentication requests with today?"**
   - *Purpose: Shows roaming data access and international traffic visibility*

---

#### **Business-Focused Questions (Core Demo):**

4. **"Are there any MME clusters showing split-brain conditions right now? If so, how many subscribers are affected and what's the estimated revenue at risk?"**
   - *Purpose: PRIMARY USE CASE - Shows real-time anomaly detection with business impact*
   - *Expected: Agent uses split-brain detection tool, calculates subscriber impact, joins with revenue data*

5. **"Which platinum or gold tier subscribers have experienced 3 or more service disruptions in the last 30 days and are now at high churn risk? I need to escalate these for retention."**
   - *Purpose: Customer experience + revenue protection*
   - *Expected: Joins signaling failures with subscriber profiles, filters by tier and incident count*

6. **"Show me any roaming partners with suspicious authentication patterns that could indicate SS7 or Diameter security attacks. Focus on partners deviating significantly from their baseline behavior."**
   - *Purpose: Security threat detection - critical for international roaming*
   - *Expected: Uses security threat detection tool, compares to baselines, flags anomalies*

7. **"We're getting complaints about dropped calls in the Seattle area. Which cell towers are showing handoff failure spikes, and is this a single tower issue or a cascade failure?"**
   - *Purpose: Root cause analysis for customer-facing issues*
   - *Expected: Analyzes handoff failures by geographic area, identifies root cause tower, estimates cascade impact*

8. **"Which MME servers are showing memory leak patterns that could lead to crashes in the next 7-14 days? Give me the top 5 by risk level so we can schedule proactive maintenance."**
   - *Purpose: Predictive maintenance - prevents large-scale outages*
   - *Expected: Uses resource exhaustion detection tool, analyzes memory growth trends, prioritizes by capacity*

---

#### **Trend Analysis Questions:**

9. **"What's the trend in signaling storm incidents over the last 90 days? Are we detecting them faster than we were 3 months ago?"**
   - *Purpose: Operational improvement tracking*
   - *Expected: Time-series analysis of storm incidents, detection latency trends*

10. **"How has our authentication failure rate with international roaming partners changed over the last 60 days? Are there any partners getting worse?"**
    - *Purpose: Service quality trends for roaming agreements*
    - *Expected: Trend analysis per roaming partner, identifies degrading relationships*

11. **"Show me the correlation between MME software version and memory utilization patterns. Are certain versions more prone to memory leaks?"**
    - *Purpose: Software quality analysis for capacity planning*
    - *Expected: Groups by software version, analyzes memory trends, identifies problematic versions*

---

#### **Optimization & Planning Questions:**

12. **"Which MME clusters are approaching capacity based on current signaling load and subscriber count? I need to plan capacity expansion for Q2."**
    - *Purpose: Capacity planning with infrastructure context*
    - *Expected: Calculates utilization vs. max capacity, projects growth, recommends expansion*

13. **"For the MME cluster in the Dallas datacenter that had the split-brain incident yesterday, show me the complete infrastructure profile: hardware specs, software versions, last restart times, and recent memory trends for all hosts."**
    - *Purpose: Incident investigation with full operational context*
    - *Expected: Multi-dataset join providing complete cluster profile for root cause analysis*

14. **"What percentage of our high-value subscribers (platinum/gold) have experienced service disruptions in the last quarter, and how does that compare to our SLA commitments?"**
    - *Purpose: SLA compliance reporting for executive stakeholders*
    - *Expected: Calculates disruption rates by tier, compares to SLA targets, quantifies compliance gap*

---

#### **Advanced/Bonus Questions (If Time Permits):**

15. **"If we lose the primary MME in cluster NYC-CORE-01 right now, how many subscribers would be affected during failover, and what's the estimated revenue impact of a 5-minute outage?"**
    - *Purpose: Disaster recovery planning with business impact*
    - *Expected: Calculates cluster capacity, estimates failover impact, quantifies revenue loss*

16. **"Show me all high-severity incidents (split-brain, signaling storms, cascade failures) in the last 7 days, sorted by total subscriber impact. I need this for our weekly NOC review."**
    - *Purpose: Executive reporting and trend summary*
    - *Expected: Aggregates multiple incident types, ranks by impact, provides weekly summary*

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "Modern query language, built for analytics on massive datasets"
- "Piped syntax is intuitive and readable—anyone with SQL experience can learn it in hours"
- "Operates on blocks, not rows—extremely performant even on 500K+ record datasets"
- "Supports complex operations: LOOKUP JOINs across indices, window functions, time-series bucketing, statistical aggregations"
- "EVAL allows on-the-fly calculations without ETL—calculate business metrics directly in the query"
- "LOOKUP JOIN enables true relational analytics across Elasticsearch indices without denormalization"

### **On Agent Builder:**
- "Bridges AI and enterprise data—your LLM can now query operational data in real-time"
- "No custom development required—configure tools, don't code integrations"
- "Works with existing Elasticsearch indices—no data migration or duplication needed"
- "Agent automatically selects the right tool based on question context—intelligent query routing"
- "Supports multiple tools per agent—one agent can handle diverse analytical questions"
- "Natural language interface democratizes data access—network engineers don't need to learn ES|QL"

### **On Business Value for T-Mobile:**
- "Reduces split-brain detection from 15-30 minutes to under 60 seconds—preventing impact to thousands of subscribers"
- "Proactive memory leak detection prevents MME crashes affecting 50,000-150,000 subscribers per incident"
- "Real-time churn risk identification enables proactive retention for high-value subscribers—protecting millions in annual revenue"
- "Security threat detection catches roaming partner attacks before they escalate—protecting brand reputation and regulatory compliance"
- "Democratizes network intelligence—NOC engineers get instant answers without waiting for data analysts"
- "Faster MTTR through semantic incident search—find similar past incidents in seconds instead of hours"
- "Quantifies business impact automatically—every alert includes subscriber count and revenue at risk"
- "Replaces monthly aggregated reporting with real-time subscriber experience monitoring—proactive SLA violation management"
- "Can be deployed in days, not months—no custom development, just configuration"

### **On Technical Differentiators:**
- "LOOKUP JOIN is the game-changer—true relational analytics across Elasticsearch indices without performance penalty"
- "Lookup mode indices are optimized for joins—fast enrichment even with large reference datasets"
- "ES|QL's statistical functions (AVG, COUNT_DISTINCT, BUCKET) enable sophisticated anomaly detection without external tools"
- "Time-series bucketing with BUCKET() enables trend analysis and time-window comparisons in a single query"
- "CASE statements allow inline severity classification—no post-processing required"
- "Agent Builder's tool abstraction means you can update queries without retraining the AI—operational agility"

---

## **🔧 Troubleshooting**

### **If a query fails:**

**"Error: Unknown index"**
- Check index names match exactly (case-sensitive)
- Verify indices were created successfully: `GET /_cat/indices?v`

**"Error: Unknown column"**
- Verify field names are case-sensitive correct
- Check field mapping: `GET /index_name/_mapping`
- Ensure fields exist in the dataset

**"LOOKUP JOIN returns no results"**
- Verify joined index has `"index.mode": "lookup"` setting: `GET /index_name/_settings`
- Check that join key format is consistent across datasets (e.g., both use string type)
- Verify join key values actually match: Query both indices separately to confirm overlap

**"Query timeout"**
- Reduce time window (e.g., NOW() - 1 hour instead of NOW() - 7 days)
- Add more specific WHERE filters to reduce dataset size
- Check cluster health: `GET /_cluster/health`

---

### **If agent gives wrong answer:**

**Agent doesn't use the right tool:**
- Check tool descriptions—are they clear about when to use each tool?
- Verify tool names are descriptive and contextually relevant
- Review custom instructions—does the agent understand the use case?

**Agent provides incomplete analysis:**
- Tool query may not be returning expected fields—verify with manual ES|QL test
- Check if LOOKUP JOIN is enriching data correctly—test join query separately
- Review agent custom instructions—add more context about expected response format

**Agent calculates wrong business metrics:**
- Verify EVAL calculations in tool queries (e.g., TO_DOUBLE conversions for percentages)
- Check that reference data in lookup indices is accurate (e.g., memory_total_gb, max_capacity_subscribers)
- Test tool queries manually to confirm calculations

---

### **If join returns no results:**

**LOOKUP JOIN produces empty results:**
- Verify lookup index has data: `FROM lookup_index | LIMIT 10`
- Check join key format consistency: Query both indices and compare key values
- Ensure join key field names match exactly (case-sensitive)
- Verify lookup index has `"index.mode": "lookup"`: `GET /lookup_index/_settings`

**Join returns partial results:**
- This is expected behavior for LEFT JOIN—not all records will have matching lookup data
- Add WHERE clause after join to filter out null enrichment fields if needed
- Check for data quality issues in join keys (extra spaces, different formats)

---

### **Performance optimization:**

**Query runs slowly:**
- Add time-based WHERE filters early in the query (before STATS)
- Use COUNT(*) instead of COUNT_DISTINCT when exact uniqueness isn't critical
- Limit result sets with LIMIT clause
- Consider adding index patterns to narrow data scope: `FROM mme_signaling_events-*`

**Agent response is slow:**
- Simplify tool queries—remove unnecessary fields from KEEP clause
- Reduce LIMIT values in tool queries (e.g., LIMIT 20 instead of LIMIT 100)
- Add more specific WHERE filters to tool queries based on common question patterns

---

## **🎬 Closing**

**"Let me summarize what we've demonstrated today:**

✅ **Real-time anomaly detection** - Split-brain conditions detected in under 60 seconds instead of 15-30 minutes

✅ **Proactive failure prevention** - Memory leak detection 7-14 days before service-affecting crashes

✅ **Business impact quantification** - Every alert includes affected subscriber count and revenue at risk

✅ **Security threat detection** - Roaming partner anomalies caught before they escalate to major incidents

✅ **Customer retention intelligence** - Churn risk identification for high-value subscribers with recent service issues

✅ **Natural language access** - NOC engineers get instant answers without learning ES|QL or waiting for analysts

✅ **Complex analytics simplified** - Queries that would take hours to write in SQL, answered conversationally in seconds

✅ **No custom development** - Agent Builder is configuration, not code—deploy in days, not months

**The Technical Foundation:**
- ES|QL provides the analytical power—LOOKUP JOINs enable true relational analytics across your operational data
- Lookup mode indices optimize for enrichment—fast joins even with large reference datasets
- Agent Builder bridges AI and enterprise data—your LLM can now query real-time network telemetry

**The Business Impact for T-Mobile:**
- Prevent revenue loss from SLA violations by detecting transient failures in real-time
- Reduce MTTR for split-brain and signaling storm incidents from 30 minutes to under 5 minutes
- Protect millions in annual revenue through proactive churn risk management
- Catch international roaming configuration errors proactively instead of through customer complaints
- Identify cell tower cascade failures within 5 minutes and pinpoint root cause towers

**This isn't just monitoring—it's intelligent, proactive network operations with built-in business context.**

**Questions?"**

---

## **📎 Appendix: Quick Reference**

### **ES|QL Command Cheat Sheet**

```esql
FROM index_name                          // Source data
| WHERE field == "value"                 // Filter rows
| STATS AGG(field) BY group_field        // Aggregate
| EVAL new_field = calculation           // Calculate new fields
| LOOKUP JOIN lookup_index ON join_key   // Enrich with reference data
| SORT field DESC                        // Order results
| LIMIT n                                // Limit result count
| KEEP field1, field2                    // Select specific fields
| DROP field1, field2                    // Remove fields
```

### **Common Aggregations**
- `COUNT(*)` - Count all rows
- `COUNT_DISTINCT(field)` - Count unique values
- `AVG(field)` - Average
- `SUM(field)` - Sum
- `MIN(field)` / `MAX(field)` - Min/Max values
- `BUCKET(@timestamp, 5 minutes)` - Time-series bucketing

### **Time Filters**
- `NOW()` - Current timestamp
- `NOW() - 1 hour` - One hour ago
- `NOW() - 24 hours` - 24 hours ago
- `NOW() - 7 days` - 7 days ago

### **Index Settings for LOOKUP JOIN**
```json
PUT /lookup_index
{
  "settings": {
    "index.mode": "lookup"
  }
}
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
