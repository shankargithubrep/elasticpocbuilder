from src.framework.base import DemoGuideModule, DemoConfig
from typing import Dict, List, Any, Optional
import pandas as pd

class TelcoDemoGuide(DemoGuideModule):
    """Demo guide for Telco - Network Operations"""

    def __init__(self, config: DemoConfig, datasets: Dict[str, pd.DataFrame],
                 queries: List[Dict], aha_moment: Optional[Dict] = None):
        """Initialize with demo context"""
        super().__init__(config, datasets, queries, aha_moment)

    def generate_guide(self) -> str:
        """Generate customized demo guide"""
        return '''# **Elastic Agent Builder Demo for Telco**

## **Internal Demo Script & Reference Guide**

---

## **📋 Demo Overview**

**Total Time:** 25-30 minutes
**Audience:** Network Operations technical and business stakeholders
**Goal:** Show how Agent Builder enables AI-powered observability on Telco network data — from dropped calls and authentication failures to signaling storms and MME resource exhaustion

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

**The Story We're Telling:**
Network Operations teams are drowning in data — millions of signaling events, MME logs, RAN metrics, and call records flowing in every minute. Finding a split-brain condition, a signaling storm, or an HSS authentication failure before it cascades into a widespread outage requires correlating data across a dozen systems. Today we'll show how Elastic Agent Builder turns that complexity into a conversational interface backed by real-time analytics.

---

## **🗂️ Dataset Architecture**

### **Overview**

This demo uses **11 datasets** spanning timeseries operational data and reference/lookup enrichment tables. The architecture mirrors a real Telco NOC data environment, with core network events, radio access metrics, subscriber session logs, and equipment registries all indexed in Elasticsearch.

---

### **Timeseries Datasets (High Volume — 5,000–10,000 records each)**

These are the operational heartbeat of the network. They arrive continuously and are queried for anomaly detection, trending, and alerting.

---

#### **`data_session_logs`**
Tracks individual subscriber data sessions from attach to termination. Used to detect interrupted sessions, abnormal terminations, and degradation by RAT type.

| Field | Description |
|---|---|
| `@timestamp` | Session event timestamp |
| `session_id` | Unique session identifier |
| `session_status` | Status at time of record (e.g., `interrupted`, `abnormal_termination`, `active`) |
| `termination_cause` | Reason for session end |
| `rat_type` | Radio Access Technology (e.g., `4G`, `5G`, `3G`) |
| `subscriber_id` | Subscriber identifier (maps to IMSI) |
| `apn` | Access Point Name |
| `cell_id` | Cell identifier where session was served |
| `session_duration_seconds` | Duration of the session |
| `bytes_transferred` | Data volume transferred |

**Record Count:** 5,000–10,000 | **Primary Key:** `session_id` | **Join Key:** `cell_id`, `subscriber_id`

---

#### **`core_network_events`**
The central event bus for core network conditions — split-brain alerts, consensus failures, node degradation, and signaling anomalies. This is the primary dataset for detecting split-brain and storm conditions.

| Field | Description |
|---|---|
| `@timestamp` | Event timestamp |
| `event_id` | Unique event identifier |
| `event_title` | Short title of the event |
| `event_description` | Full narrative description of the event |
| `alert_message` | Machine-generated alert string |
| `node_id` | Network node that generated the event |
| `node_role` | Role of the node (e.g., MME, HSS, SGW) |
| `cluster_id` | Cluster the node belongs to |
| `network_region` | Geographic region |
| `severity` | Severity level (critical, major, minor, info) |
| `event_type` | Classification of event type |
| `consensus_state` | Cluster consensus status (e.g., `split`, `degraded`, `healthy`) |
| `affected_peers` | Number of peer nodes impacted |
| `score` | Relevance/anomaly score |

**Record Count:** 5,000–10,000 | **Primary Key:** `event_id` | **Join Key:** `node_id`, `cluster_id`

---

### **Reference / Lookup Datasets (200–1,000 records each)**

These are enrichment tables — relatively static, used in LOOKUP JOIN operations to annotate operational data with context. **All must be indexed with `"index.mode": "lookup"`.**

---

#### **`call_detail_records`**
Per-call records capturing drop events, handoff attempts, signal quality, and subscriber identity. Used for dropped call rate analytics by tower and mobility zone.

| Field | Description |
|---|---|
| `@timestamp` | Call event timestamp |
| `cell_tower_id` | Tower serving the call (join key to `cell_tower_reference`) |
| `call_dropped` | Boolean — whether the call was dropped |
| `call_attempt` | Boolean — whether this was a call attempt |
| `handoff_event` | Whether a handoff occurred during the call |
| `subscriber_id` | Subscriber identifier |
| `call_duration_seconds` | Duration of the call |
| `signal_strength_dbm` | Signal strength at time of event |
| `network_type` | Network type (4G/5G/3G) |

**Record Count:** 200–1,000 | **Primary Key:** `session_id` | **Join Key:** `cell_tower_id`

---

#### **`cell_tower_reference`**
Static reference table describing each cell tower's physical and operational characteristics. Used to enrich call records with mobility zone and geographic context.

| Field | Description |
|---|---|
| `cell_tower_id` | Unique tower identifier (join key) |
| `mobility_zone` | Zone classification (e.g., highway, urban, transit hub) |
| `handoff_zone_type` | Type of handoff zone |
| `geographic_region` | Geographic region of the tower |
| `tower_vendor` | Equipment vendor |
| `latitude` | Tower latitude |
| `longitude` | Tower longitude |

**Record Count:** 200–1,000 | **Index Mode:** `lookup` | **Join Key:** `cell_tower_id`

---

#### **`mme_system_logs`**
Detailed operational logs from Mobility Management Entity nodes — the most critical dataset for detecting MME resource exhaustion, software bugs, and subscriber attach failures.

| Field | Description |
|---|---|
| `@timestamp` | Log timestamp |
| `mme_node_id` | MME node identifier |
| `mme_pool_id` | Pool the MME belongs to |
| `cpu_utilization_pct` | CPU utilization percentage |
| `memory_utilization_pct` | Memory utilization percentage |
| `active_ue_sessions` | Active UE session count |
| `attach_request_rate` | Rate of attach requests per minute |
| `attach_failure_rate` | Rate of attach failures per minute |
| `software_version` | MME software version |
| `process_name` | Process generating the log |
| `log_severity` | Log severity level |
| `error_code` | Error code |
| `fault_code` | Fault code (join key to bug signature tables) |
| `fault_category` | Category of fault |
| `fault_severity` | Severity of the fault |
| `affected_subscribers` | Count of affected subscribers |
| `attach_failures` | Attach failure count |
| `detach_events` | Detach event count |
| `s1ap_errors` | S1AP error count |
| `nas_procedure_failures` | NAS procedure failure count |
| `core_dump_generated` | Whether a core dump was generated |
| `log_level` | Log level |
| `s1ap_error_count` | S1AP error count (numeric) |
| `nas_signaling_error_count` | NAS signaling error count |

**Record Count:** 200–1,000 | **Primary Key:** `mme_node_id` + `@timestamp` | **Join Key:** `fault_code`, `software_version`

---

#### **`mme_bug_signature_lookup`**
Maps software versions to known bug IDs and descriptions. Used in LOOKUP JOIN to correlate MME faults with known defects.

| Field | Description |
|---|---|
| `software_version` | MME software version (join key) |
| `bug_id` | Known bug identifier |
| `bug_description` | Description of the bug |
| `affected_component` | Component affected by the bug |
| `patch_available` | Whether a patch exists |
| `severity_rating` | Severity rating of the bug |

**Record Count:** 200–1,000 | **Index Mode:** `lookup` | **Join Key:** `software_version`

---

#### **`mme_bug_signatures`**
Extended bug signature reference with CVE references, patch versions, and workaround availability. Used for deep fault enrichment.

| Field | Description |
|---|---|
| `fault_code` | Fault code (join key) |
| `bug_id` | Bug identifier |
| `bug_title` | Human-readable bug title |
| `bug_severity` | Severity classification |
| `affected_software_versions` | List of affected software versions |
| `bug_category` | Bug category |
| `patch_available` | Patch availability flag |
| `patch_version` | Version that resolves the bug |
| `cve_reference` | CVE reference if applicable |
| `workaround_available` | Whether a workaround exists |

**Record Count:** 200–1,000 | **Index Mode:** `lookup` | **Join Key:** `fault_code`

---

#### **`signaling_logs`**
Per-message signaling records across core network elements. Used for signaling storm detection by measuring message volume burst per node.

| Field | Description |
|---|---|
| `@timestamp` | Message timestamp |
| `network_element_id` | Network element that processed the message (join key) |
| `signaling_protocol` | Protocol (e.g., Diameter, S1AP, GTP) |
| `message_type` | Type of signaling message |
| `source_node` | Originating node |
| `destination_node` | Destination node |
| `message_direction` | Inbound or outbound |
| `session_id` | Associated session |
| `cause_code` | Cause code for the message |

**Record Count:** 200–1,000 | **Join Key:** `network_element_id`

---

#### **`network_element_registry`**
Master registry of all network elements — MMEs, HSSs, SGWs, eNodeBs — with capacity thresholds and criticality tiers. Used to enrich signaling storm detection with operational context.

| Field | Description |
|---|---|
| `network_element_id` | Unique element identifier (join key) |
| `element_name` | Human-readable element name |
| `element_type` | Type (MME, HSS, SGW, eNodeB, etc.) |
| `region` | Operational region |
| `vendor` | Equipment vendor |
| `capacity_threshold_msg_per_min` | Rated capacity in messages per minute |
| `criticality_tier` | Tier 1/2/3 criticality classification |

**Record Count:** 200–1,000 | **Index Mode:** `lookup` | **Join Key:** `network_element_id`

---

#### **`ran_performance_metrics`**
Per-cell RAN performance data including handover attempts, failures, and UE counts. Primary dataset for handover failure analytics.

| Field | Description |
|---|---|
| `@timestamp` | Metric timestamp |
| `ran_node_id` | RAN node identifier (join key to `ran_site_reference`) |
| `cell_id` | Cell identifier |
| `handover_attempts` | Total handover attempts |
| `handover_failures` | Total handover failures |
| `handover_type` | Type of handover (intra-frequency, inter-frequency, inter-RAT) |
| `source_rat` | Source radio access technology |
| `target_rat` | Target radio access technology |
| `ue_count` | Active UE count at time of measurement |

**Record Count:** 200–1,000 | **Join Key:** `ran_node_id`

---

#### **`ran_site_reference`**
Static reference for RAN sites — maps node IDs to site names, regions, vendors, and technology generation. Used to enrich handover analytics with geographic context.

| Field | Description |
|---|---|
| `ran_node_id` | RAN node identifier (join key) |
| `site_name` | Human-readable site name |
| `region` | Geographic region |
| `sub_region` | Sub-region classification |
| `vendor` | Equipment vendor |
| `technology_generation` | Technology generation (4G, 5G, etc.) |

**Record Count:** 200–1,000 | **Index Mode:** `lookup` | **Join Key:** `ran_node_id`

---

### **Dataset Relationship Map**

```
data_session_logs ──────────────────────────────────── (standalone timeseries)
core_network_events ─────────────────────────────────── (standalone timeseries)

call_detail_records ──[cell_tower_id]──► cell_tower_reference (lookup)
signaling_logs ────────[network_element_id]──► network_element_registry (lookup)
ran_performance_metrics ──[ran_node_id]──► ran_site_reference (lookup)
mme_system_logs ──[software_version]──► mme_bug_signature_lookup (lookup)
mme_system_logs ──[fault_code]──────► mme_bug_signatures (lookup)
```

---

## **🌋 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

> **CRITICAL: All reference/lookup indexes MUST be created with `"index.mode": "lookup"` for LOOKUP JOIN operations to work. Timeseries indexes use standard mode.**

---

#### **Timeseries Indexes (Standard Mode)**

Navigate to **Kibana → Stack Management → Index Management → Create Index** or use Dev Tools.

**Create `data_session_logs`:**
```json
PUT data_session_logs
{
  "settings": {
    "number_of_shards": 1
  },
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "session_id": { "type": "keyword" },
      "session_status": { "type": "keyword" },
      "termination_cause": { "type": "keyword" },
      "rat_type": { "type": "keyword" },
      "subscriber_id": { "type": "keyword" },
      "apn": { "type": "keyword" },
      "cell_id": { "type": "keyword" },
      "session_duration_seconds": { "type": "long" },
      "bytes_transferred": { "type": "long" }
    }
  }
}
```

**Create `core_network_events`:**
```json
PUT core_network_events
{
  "settings": {
    "number_of_shards": 1
  },
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "event_id": { "type": "keyword" },
      "event_title": { "type": "text" },
      "event_description": { "type": "text" },
      "alert_message": { "type": "text" },
      "node_id": { "type": "keyword" },
      "node_role": { "type": "keyword" },
      "cluster_id": { "type": "keyword" },
      "network_region": { "type": "keyword" },
      "severity": { "type": "keyword" },
      "event_type": { "type": "keyword" },
      "consensus_state": { "type": "keyword" },
      "affected_peers": { "type": "integer" },
      "score": { "type": "float" }
    }
  }
}
```

---

#### **Lookup Indexes (Must use `index.mode: lookup`)**

**Create `cell_tower_reference`:**
```json
PUT cell_tower_reference
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "cell_tower_id": { "type": "keyword" },
      "mobility_zone": { "type": "keyword" },
      "handoff_zone_type": { "type": "keyword" },
      "geographic_region": { "type": "keyword" },
      "tower_vendor": { "type": "keyword" },
      "latitude": { "type": "float" },
      "longitude": { "type": "float" }
    }
  }
}
```

**Create `network_element_registry`:**
```json
PUT network_element_registry
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "network_element_id": { "type": "keyword" },
      "element_name": { "type": "keyword" },
      "element_type": { "type": "keyword" },
      "region": { "type": "keyword" },
      "vendor": { "type": "keyword" },
      "capacity_threshold_msg_per_min": { "type": "long" },
      "criticality_tier": { "type": "keyword" }
    }
  }
}
```

**Create `ran_site_reference`:**
```json
PUT ran_site_reference
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "ran_node_id": { "type": "keyword" },
      "site_name": { "type": "keyword" },
      "region": { "type": "keyword" },
      "sub_region": { "type": "keyword" },
      "vendor": { "type": "keyword" },
      "technology_generation": { "type": "keyword" }
    }
  }
}
```

**Create `mme_bug_signature_lookup`:**
```json
PUT mme_bug_signature_lookup
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "software_version": { "type": "keyword" },
      "bug_id": { "type": "keyword" },
      "bug_description": { "type": "text" },
      "affected_component": { "type": "keyword" },
      "patch_available": { "type": "boolean" },
      "severity_rating": { "type": "keyword" }
    }
  }
}
```

**Create `mme_bug_signatures`:**
```json
PUT mme_bug_signatures
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "fault_code": { "type": "keyword" },
      "bug_id": { "type": "keyword" },
      "bug_title": { "type": "keyword" },
      "bug_severity": { "type": "keyword" },
      "affected_software_versions": { "type": "keyword" },
      "bug_category": { "type": "keyword" },
      "patch_available": { "type": "boolean" },
      "patch_version": { "type": "keyword" },
      "cve_reference": { "type": "keyword" },
      "workaround_available": { "type": "boolean" }
    }
  }
}
```

---

### **Step 2: Load CSV Data via Kibana File Upload**

1. Navigate to **Kibana → Machine Learning → Data Visualizer → File**
2. Upload each CSV file
3. On the **Import** step, set the index name to match exactly (e.g., `data_session_logs`)
4. For lookup indexes: after upload, use Dev Tools to verify `index.mode` is set correctly — Kibana File Upload may not preserve lookup mode, so re-create with the mappings above and use `_bulk` to reload if needed

> **Pro Tip for Demo Prep:** Load the timeseries datasets (`data_session_logs`, `core_network_events`) last so timestamps are fresh. Use a time range of "Last 7 days" in Kibana to ensure data appears in visualizations.

---

### **Step 3: Verify Data in Dev Tools**

Run these quick validation checks before the demo:

```esql
// Verify data_session_logs
FROM data_session_logs
| STATS total = COUNT(*), interrupted = COUNT_IF(session_status == "interrupted")
| LIMIT 1
```

```esql
// Verify core_network_events
FROM core_network_events
| STATS event_count = COUNT(*) BY severity
| SORT event_count DESC
```

```esql
// Verify lookup join works
FROM mme_system_logs
| LOOKUP JOIN mme_bug_signatures ON fault_code
| WHERE bug_id IS NOT NULL
| LIMIT 5
```

---

### **Step 4: Configure AI Agent**

1. Navigate to **Kibana → Elastic AI Assistant → Agent Builder**
2. Create a new agent using the configuration in Part 3 of this guide
3. Add all tools (ES|QL queries) as described
4. Test with a warm-up question before the live demo

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to the Elastic AI Assistant / Agent Builder chat interface
- Agent should already be configured with all tools active
- Use a split screen if possible: chat on one side, Kibana dashboards on the other

### **Demo Script**

**Presenter:** "Before we go under the hood, let me show you what we're building toward. This is the AI agent that Network Operations engineers will use day-to-day. I'm going to ask it some questions that would normally require a senior engineer, three different monitoring tools, and a lot of time."

---

**Sample Questions to Demonstrate:**

> 💬 **Question 1 (Dropped Calls — Warm-up):**
> *"Which cell towers have the highest dropped call rates right now, and are any of them in high-mobility zones like highways or transit hubs?"*

**Why this works:** Combines `call_detail_records` with `cell_tower_reference` enrichment. Shows the agent can correlate operational metrics with geographic context in one question.

---

> 💬 **Question 2 (MME Health — Business Impact):**
> *"Are any MME nodes showing signs of resource exhaustion, and do we know if the issue is tied to a known software bug with a patch available?"*

**Why this works:** Pulls from `mme_system_logs`, enriches with `mme_bug_signatures`. Demonstrates the agent's ability to cross-reference operational telemetry with a known defect database — something that would normally require an engineer to manually look up a bug tracker.

---

> 💬 **Question 3 (Signaling Storm — Urgency):**
> *"Is there a signaling storm in progress? Which network elements are showing abnormal message burst activity, and what's their criticality tier?"*

**Why this works:** Analyzes `signaling_logs` with statistical anomaly detection and enriches with `network_element_registry`. The criticality tier answer immediately tells the NOC whether this is a Tier 1 emergency.

---

> 💬 **Question 4 (Split-Brain — Incident Triage):**
> *"Search for any split-brain or consensus failure events in the core network over the last 24 hours. Give me the most critical ones first."*

**Why this works:** Full-text search across `core_network_events` using BM25 relevance scoring. Mimics how a NOC engineer would search during an active incident — natural language, not a query language.

---

> 💬 **Question 5 (Handover Failures — RAN Health):**
> *"Which RAN sites are experiencing the worst handover failure rates, and which regions are most affected? Break it down by technology generation."*

**Why this works:** Analyzes `ran_performance_metrics` and enriches with `ran_site_reference`. Gives RAN engineers an immediate geographic and technology-specific view of mobility failures.

---

> 💬 **Question 6 (Session Interruptions — Trending):**
> *"Show me the trend of interrupted data sessions over the last 6 hours, broken down by 4G versus 5G. Is it getting worse?"*

**Why this works:** Time-bucketed trend analysis on `data_session_logs` segmented by `rat_type`. The "is it getting worse?" part is where the agent interprets the trend, not just returns raw data.

---

> 💬 **Question 7 (Composite — Executive Summary):**
> *"Give me a network health summary. What are the top three issues I should be focused on right now across the core network, RAN, and subscriber sessions?"*

**Why this works:** Forces the agent to invoke multiple tools, synthesize results, and produce a prioritized summary. This is the "wow" moment — one question, full network situational awareness.

---

**Transition:**

**Presenter:** "Every one of those answers came from real indexed data — `mme_system_logs`, `signaling_logs`, `core_network_events`, `ran_performance_metrics` — all the datasets your team already has. The agent is not guessing. It's running ES|QL queries, joining datasets, and using statistical anomaly detection under the hood. Let me show you exactly how that works."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open **Kibana → Dev Tools Console**
- All indices are already created and populated
- Walk through queries progressively — each one builds on the last in sophistication

---

### **Query 1: Core Network Split-Brain Event Search (2 minutes)**

**Presenter:** "Let's start with something every NOC engineer needs during an incident: fast, relevant search. The question is — *are there any split-brain events happening in the core network right now?* In the old world, you'd grep through log files or run a filtered query in a monitoring tool. With ES|QL, we do it like this."

**Copy/paste into Dev Tools:**

```esql
FROM core_network_events
| WHERE MATCH(event_description, "split-brain") OR MATCH(alert_message, "split-brain")
| SORT score DESC, @timestamp DESC
| KEEP @timestamp, event_title, event_description, alert_message, node_id, node_role, cluster_id, network_region, severity, consensus_state, affected_peers, score
| LIMIT 20
```

**Run and narrate results:**

"Let's break down what ES|QL is doing here:

- **FROM**: We're sourcing from `core_network_events` — our core network event bus
- **WHERE MATCH**: This is BM25 full-text search — the same relevance engine that powers Google-style search. It's not a keyword filter, it's a *relevance score*. Documents that talk about split-brain more prominently score higher
- **SORT score DESC**: We get the most relevant results first — critical for incident triage when you have thousands of events
- **KEEP**: We're projecting only the fields we care about — `consensus_state` and `affected_peers` are especially valuable here
- **LIMIT 20**: Controlled result set

Notice `consensus_state` in the results — you can immediately see which nodes are in a `split` state versus `degraded` or `healthy`. This is the kind of triage that used to take 10 minutes of log searching, now done in under a second."

**Pause for effect:** "And this exact query becomes a tool in our AI agent. When an engineer asks 'are there any split-brain events?', the agent runs this query and summarizes the results."

---

### **Query 2: Data Session Interruption Trending Over Time (3 minutes)**

**Presenter:** "Now let's add analytical depth. Keyword search tells us *what* is happening. Time-series analysis tells us *how bad it's getting and in which direction*. Let's look at interrupted data sessions trending over time, broken out by radio access technology."

**Copy/paste:**

```esql
FROM data_session_logs
| WHERE session_status IN ("interrupted", "abnormal_termination")
| EVAL hour_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS session_count = COUNT(*) BY hour_bucket, rat_type
| EVAL interruption_rate = TO_DOUBLE(session_count) / TO_DOUBLE(SUM(session_count))
| SORT hour_bucket ASC, session_count DESC
```

**Run and highlight:**

"This is where ES|QL starts to feel like a real analytics language. Let me walk through the additions:

- **WHERE with IN**: Filters for both `interrupted` and `abnormal_termination` statuses — two different ways a session can fail in the telco data model
- **EVAL DATE_TRUNC**: Creates hourly time buckets. This is how we build a time series — group by truncated timestamp. You can change `1 hour` to `15 minutes` or `1 day` depending on your analysis window
- **STATS COUNT BY hour_bucket, rat_type**: Two-dimensional aggregation — we get counts per hour *and* per RAT type. So we see 4G, 5G, and 3G trends independently
- **EVAL interruption_rate**: Calculates what fraction of sessions in each bucket were interrupted. `TO_DOUBLE` is critical here — without it, integer division would give us zeros
- **SORT ASC**: Chronological order so you can read the trend left to right

Look at the results — if you see the 5G `session_count` climbing steadily across buckets while 4G remains flat, that's a 5G-specific degradation event. If all RATs are rising simultaneously, it points to a core network issue rather than a radio problem. *That* distinction is what separates a 30-minute resolution from a 3-hour war room."

---

### **Query 3: Dropped Call Rate by Cell Tower and Mobility Zone — LOOKUP JOIN (3 minutes)**

**Presenter:** "Now let's bring in our first LOOKUP JOIN. We know which towers are dropping calls — but *where* are those towers? Are they on a highway corridor? A transit hub? Knowing the mobility zone context changes the entire remediation strategy."

**Copy/paste:**

```esql
FROM call_detail_records
| STATS dropped_calls = SUM(TO_LONG(call_dropped)), total_attempts = SUM(TO_LONG(call_attempt)) BY cell_tower_id, BUCKET(@timestamp, 15 minutes)
| EVAL dropped_call_rate = TO_DOUBLE(dropped_calls) / TO_DOUBLE(total_attempts)
| INLINESTATS mean_rate = AVG(dropped_call_rate), std_rate = STD_DEV(dropped_call_rate) BY cell_tower_id
| EVAL z_score = (dropped_call_rate - mean_rate) / std_rate
| WHERE z_score > 3
| LOOKUP JOIN cell_tower_reference ON cell_tower_id
| KEEP cell_tower_id, mobility_zone, handoff_zone_type, geographic_region, tower_vendor, dropped_call_rate, z_score, dropped_calls, total_attempts
| SORT z_score DESC
```

**Run and explain:**

"This query has a lot going on — let me highlight the key concepts:

- **STATS with BUCKET**: We're aggregating per tower per 15-minute window. `BUCKET(@timestamp, 15 minutes)` is ES|QL's time bucketing function — it automatically aligns to clean 15-minute intervals
- **EVAL dropped_call_rate**: Per-tower drop rate as a decimal (0.0 to 1.0)
- **INLINESTATS**: This is powerful and unique to ES|QL. It computes the mean and standard deviation of `dropped_call_rate` *across all time buckets for each tower* — without a subquery or window function. It's like a running statistical context that gets added as new columns to every row
- **Z-score > 3**: We're flagging towers that are more than 3 standard deviations above their own historical mean. This is statistically rigorous anomaly detection — not a fixed threshold that generates false positives
- **LOOKUP JOIN cell_tower_reference ON cell_tower_id**: Here's the magic. We join against our lookup index using `cell_tower_id` as the key. Now every anomalous tower row is enriched with `mobility_zone`, `handoff_zone_type`, `geographic_region`, and `tower_vendor`

Look at the results — a tower with a Z-score of 4.7 in a `highway` mobility zone tells a completely different story than one in a `suburban_residential` zone. Highway towers have constant handoff pressure from fast-moving UEs. That context changes whether you escalate to the RAN team or the transport team.

**Critical technical note for the audience:** LOOKUP JOIN only works when the joined index has `index.mode: lookup` set. This is a special index mode in Elasticsearch that optimizes the index for join operations. We set this up during demo prep."

---

### **Query 4: Signaling Storm Detection with INLINESTATS and Network Element Enrichment (2 minutes)**

**Presenter:** "For the analytical grand finale — let's detect a signaling storm in progress. This is one of the most dangerous conditions in a telco core network. A signaling storm can cascade from one overloaded element to the entire signaling fabric within minutes. Here's how we catch it statistically before it reaches critical mass."

**Copy/paste:**

```esql
FROM signaling_logs
| STATS msg_count = COUNT(*) BY network_element_id, signaling_protocol, BUCKET(@timestamp, 5 minutes)
| INLINESTATS mean_msg = AVG(msg_count), std_msg = STD_DEV(msg_count) BY network_element_id
| EVAL z_score = (msg_count - mean_msg) / std_msg
| WHERE z_score > 3
| LOOKUP JOIN network_element_registry ON network_element_id
| KEEP network_element_id, element_name, element_type, region, vendor, capacity_threshold_msg_per_min, criticality_tier, signaling_protocol, msg_count, mean_msg, std_msg, z_score
| SORT z_score DESC, criticality_tier ASC
```

**Run and break down:**

"Let me walk through the full analytical pipeline:

- **STATS COUNT BY network_element_id, signaling_protocol, BUCKET**: Three-dimensional aggregation — per element, per protocol, per 5-minute window. We're building a message volume time series for every element in the network
- **INLINESTATS AVG + STD_DEV BY network_element_id**: Computes each element's *own* statistical baseline. An HSS naturally handles more Diameter messages than an eNodeB handles S1AP messages — so we need per-element baselines, not a global threshold
- **Z-score > 3**: Same statistical rigor as Query 3. We're finding elements that are *statistically anomalous relative to their own behavior* — not just busy
- **LOOKUP JOIN network_element_registry**: Enriches each storm candidate with `element_type`, `region`, `capacity_threshold_msg_per_min`, and — critically — `criticality_tier`
- **SORT z_score DESC, criticality_tier ASC**: Sorts by severity of anomaly first, then by criticality tier (Tier 1 sorts before Tier 3 alphabetically — adjust if your data uses numeric tiers)

The `capacity_threshold_msg_per_min` field from the registry is especially valuable here. If `msg_count` is approaching or exceeding that threshold, you have not just a statistical anomaly but a *capacity breach*. That's your page-the-on-call trigger.

What you're looking at right now is a query that would have taken a senior network engineer 20-30 minutes to build in a traditional monitoring tool — running in under a second, ready to be turned into an agent tool."

---

> **📝 Presenter Note — No RAG Section:**
> The RAG/COMPLETION query section is not included in this demo guide as no validated RAG queries are available for this dataset configuration. The demo climax is Query 4's multi-dataset INLINESTATS + LOOKUP JOIN pipeline. If semantic search or COMPLETION capabilities are added to the environment in future, the `core_network_events` dataset (with `event_description` and `alert_message` text fields) is the ideal candidate for a MATCH → RERANK → COMPLETION pipeline for incident root cause summarization.

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

Navigate to **Kibana → Elastic AI Assistant → Agent Builder → Create New Agent**

---

**Agent Configuration:**

| Setting | Value |
|---|---|
| **Agent ID** | `telco-noc-observability-agent` |
| **Display Name** | `Network Operations AI Assistant` |
| **Model** | GPT-4o or Claude 3.5 Sonnet (recommended for complex multi-tool reasoning) |
| **Temperature** | 0.1 (low — we want deterministic, factual answers for NOC use cases) |

**Custom Instructions:**

```
You are an AI assistant for a Telco Network Operations Center (NOC). 
Your role is to help network engineers monitor 4G and 5G network health, 
detect anomalies, and triage incidents in real time.

You have access to tools that query live network data including:
- Data session logs (interrupted sessions, RAT type, cell ID)
- Core network events (split-brain, consensus failures, node alerts)
- MME system logs (CPU/memory utilization, attach failures, fault codes)
- Signaling logs (message volume per network element and protocol)
- Call detail records (dropped calls, handoff events, signal strength)
- RAN performance metrics (handover attempts and failures per node)
- Reference data: cell tower locations, RAN site metadata, MME bug signatures, 
  network element registry

Always cite the data source and time range when answering. 
If you detect a critical condition (Z-score > 3, Tier 1 element affected, 
consensus_state = 'split'), clearly flag it as HIGH PRIORITY.
When a known software bug is identified via fault code enrichment, 
always include patch availability status in your response.
Prioritize actionable insights over raw data dumps.
```

---

### **Creating Tools**

Each tool is an ES|QL query exposed to the agent with a natural language description. The agent uses these descriptions to decide *which tool to invoke* for a given question.

---

#### **Tool 1: Session Interruption Trend Analyzer**

| Setting | Value |
|---|---|
| **Tool Name** | `session_interruption_trend` |
| **Description** | "Use this tool when asked about interrupted data sessions, session failures, abnormal terminations, or data session degradation trends over time. Returns hourly session interruption counts broken down by radio access technology (4G, 5G, 3G). Use this to identify rising failure trends and correlate with network events or maintenance windows." |
| **Dataset** | `data_session_logs` |
| **Query** | Data Session Interruption Trending Over Time (Query 2 above) |
| **Parameters** | `time_window` (default: last 24 hours) |

**Presenter talking point:** "The description is the most important part of a tool. The agent reads this description and decides whether to use this tool for a given question. If the description is vague, the agent will either use the wrong tool or not use it at all. Be specific about *what question this tool answers*."

---

#### **Tool 2: Signaling Storm Detector**

| Setting | Value |
|---|---|
| **Tool Name** | `signaling_storm_detector` |
| **Description** | "Use this tool when asked about signaling storms, abnormal signaling activity, message burst conditions, or overloaded network elements. Analyzes signaling message volume per network element and protocol using statistical Z-score anomaly detection. Enriches results with element type, region, capacity thresholds, and criticality tier. Flag any Tier 1 elements with Z-score > 3 as HIGH PRIORITY." |
| **Dataset** | `signaling_logs` + `network_element_registry` (LOOKUP JOIN) |
| **Query** | Signaling Storm Detection Across Network Elements (Query 4 above) |
| **Parameters** | `time_window` (default: last 1 hour for storm detection — storms are fast-moving) |

---

#### **Tool 3: Core Network Event Search**

| Setting | Value |
|---|---|
| **Tool Name** | `core_network_event_search` |
| **Description** | "Use this tool when asked about specific core network events, split-brain conditions, consensus failures, node alerts, or when the user wants to search for a specific event type by keyword. Performs full-text relevance search across event descriptions and alert messages. Returns results sorted by relevance score and severity. Best used for incident triage and searching for specific condition types like 'split-brain', 'consensus failure', or 'node isolation'." |
| **Dataset** | `core_network_events` |
| **Query** | Core Network Split-Brain Event Search (Query 1 above) |
| **Parameters** | `search_term` (dynamic — passed from user question), `time_window` |

---

#### **Tool 4: MME Bug Enrichment and Impact Analyzer**

| Setting | Value |
|---|---|
| **Tool Name** | `mme_bug_impact_analyzer` |
| **Description** | "Use this tool when asked about MME software bugs, known defects, fault codes, patch availability, or when correlating MME failures with specific software versions. Enriches MME fault events with known bug signatures including bug ID, severity, CVE reference, patch version, and workaround availability. Returns aggregated impact by affected subscriber count and fault frequency. Use this to answer questions like 'which MME bugs are causing the most subscriber impact?' or 'do we have a patch for the faults we're seeing?'" |
| **Dataset** | `mme_system_logs` + `mme_bug_signatures` (LOOKUP JOIN) |
| **Query** | MME Software Bug Enrichment and Impact Correlation |
| **Parameters** | `time_window`, `min_severity` (optional filter) |

---

#### **Tool 5: Dropped Call Anomaly Detector**

| Setting | Value |
|---|---|
| **Tool Name** | `dropped_call_anomaly_detector` |
| **Description** | "Use this tool when asked about dropped calls, call quality issues, towers with high drop rates, or mobility zone problems. Uses statistical Z-score analysis to identify cell towers with statistically anomalous dropped call rates (beyond 3 standard deviations from their own baseline). Enriches results with tower mobility zone, handoff zone type, geographic region, and vendor. Useful for identifying problematic towers on highway corridors, transit hubs, or high-mobility areas." |
| **Dataset** | `call_detail_records` + `cell_tower_reference` (LOOKUP JOIN) |
| **Query** | Dropped Call Rate by Cell Tower and Mobility Zone (Query 3 above) |
| **Parameters** | `time_window`, `z_score_threshold` (default: 3) |

---

#### **Tool 6: Handover Failure Analytics**

| Setting | Value |
|---|---|
| **Tool Name** | `handover_failure_analytics` |
| **Description** | "Use this tool when asked about handover failures, mobility failures, inter-RAT handovers, RAN performance, or cell site reliability. Calculates handover attempt and failure rates per RAN node and enriches with site name, region, sub-region, vendor, and technology generation. Highlights nodes and regions with the worst handover success rates. Use for questions about 4G-to-5G handover performance, regional RAN health, or specific vendor performance comparisons." |
| **Dataset** | `ran_performance_metrics` + `ran_site_reference` (LOOKUP JOIN) |
| **Query** | Handover Failure Analytics by RAN and Region |
| **Parameters** | `time_window`, `technology_generation` (optional filter: 4G, 5G) |

---

### **Agent Tool Summary**

| Tool | Primary Dataset | Join Dataset | Key Capability |
|---|---|---|---|
| `session_interruption_trend` | `data_session_logs` | — | Time-series trending by RAT |
| `signaling_storm_detector` | `signaling_logs` | `network_element_registry` | Z-score anomaly + capacity context |
| `core_network_event_search` | `core_network_events` | — | BM25 full-text incident search |
| `mme_bug_impact_analyzer` | `mme_system_logs` | `mme_bug_signatures` | Fault-to-bug enrichment |
| `dropped_call_anomaly_detector` | `call_detail_records` | `cell_tower_reference` | Statistical drop rate anomaly |
| `handover_failure_analytics` | `ran_performance_metrics` | `ran_site_reference` | RAN mobility performance |

**Presenter talking point:** "Six tools cover the entire NOC observability surface — sessions, signaling, core network events, MME health, call quality, and RAN performance. The agent selects the right tool automatically based on the question. A single agent replaces six separate monitoring dashboards."

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

Use these questions in sequence. They are ordered to build from simple to complex and to demonstrate progressively more impressive agent behavior.

---

#### **🔥 Warm-Up Questions (Get the audience engaged)**

> **"What's the current status of our data sessions? Are there more interruptions on 4G or 5G right now?"**

*Expected agent behavior:* Invokes `session_interruption_trend`, returns hourly breakdown by `rat_type`, identifies which technology has higher interruption counts. Should note whether the trend is increasing or stable.

*Talking point:* "Notice the agent didn't just return raw numbers — it interpreted the trend and told us which RAT is worse. That's the LLM layer working on top of the ES|QL results."

---

> **"Search for any node isolation events in the last 24 hours."**

*Expected agent behavior:* Invokes `core_network_event_search` with search term "node isolation", returns relevant events sorted by score and severity.

*Talking point:* "This is BM25 full-text search. The agent understood that 'node isolation' is a keyword to search for in event descriptions — it didn't try to run an aggregation. Tool selection is working correctly."

---

#### **💼 Business-Focused Questions**

> **"Which MME nodes are at risk of resource exhaustion, and is there a known software bug behind it? Do we have a patch?"**

*Expected agent behavior:* Invokes `mme_bug_impact_analyzer`, returns enriched fault events with `bug_id`, `bug_severity`, `patch_available`, and `patch_version`. Should highlight any faults where `patch_available = false`.

*Talking point:* "This question would normally require an engineer to pull MME logs, look up the fault code in a bug tracker, check the patch management system, and cross-reference the software version. The agent did all of that in one query. And crucially — it's telling us whether we *can* patch it, not just that there's a problem."

---

> **"Which cell towers are dropping the most calls, and are any of them in high-mobility zones like highways?"**

*Expected agent behavior:* Invokes `dropped_call_anomaly_detector`, returns statistically anomalous towers enriched with `mobility_zone` and `handoff_zone_type`. Should call out any `highway` or `transit_hub` zones specifically.

*Talking point:* "The mobility zone context is the difference between a routine tower maintenance ticket and an urgent escalation to the transport team about a highway corridor serving 50,000 commuters."

---

> **"Give me a summary of handover failures by region. Which regions are performing worst and what vendor equipment is involved?"**

*Expected agent behavior:* Invokes `handover_failure_analytics`, returns per-node failure rates enriched with `region`, `sub_region`, and `vendor`. Should identify the worst-performing region and note vendor patterns if present.

*Talking point:* "Vendor patterns in handover failures are gold for procurement and SLA conversations. If one vendor's equipment is consistently underperforming in a specific region, that's a data-driven contract discussion."

---

#### **📈 Trend Analysis Questions**

> **"Show me the trend of interrupted data sessions over the last 6 hours. Is it getting worse?"**

*Expected agent behavior:* Invokes `session_interruption_trend` with a 6-hour window, returns hourly counts, and interprets whether the trend is ascending, stable, or recovering. Should note the most recent bucket compared to the earliest.

*Talking point:* "The 'is it getting worse?' part is the LLM interpreting the time series — not just returning numbers. This is what separates an AI assistant from a dashboard."

---

> **"Are there any signaling storms developing right now? Which elements should I be worried about?"**

*Expected agent behavior:* Invokes `signaling_storm_detector`, identifies elements with Z-score > 3, enriches with `criticality_tier` and `capacity_threshold_msg_per_min`, and prioritizes Tier 1 elements in its response.

*Talking point:* "The phrase 'should I be worried about' is the agent's cue to apply prioritization logic. It's not just listing anomalies — it's triaging them by criticality tier. That's the custom instruction we wrote earlier doing its job."

---

> **"Have there been any split-brain events in the core network this week, and which clusters were affected?"**

*Expected agent behavior:* Invokes `core_network_event_search` with "split-brain" as the search term, filters to the past 7 days, returns events with `cluster_id`, `consensus_state`, and `affected_peers`.

*Talking point:* "Split-brain events are often transient — they appear and resolve quickly. Full-text search with a week-long lookback window is exactly the right tool for this retrospective question."

---

#### **🔧 Optimization and Escalation Questions**

> **"Which RAN sites have the worst 5G handover success rates? I want to prioritize them for parameter tuning next week."**

*Expected agent behavior:* Invokes `handover_failure_analytics` filtered to `technology_generation = 5G`, returns failure rates sorted descending, enriched with `site_name`, `sub_region`, and `vendor`. Should return a prioritized list suitable for a work order.

*Talking point:* "This is a planning question, not an incident question. The agent is being used for proactive optimization, not just reactive firefighting. That's the shift from monitoring to observability."

---

> **"Are there any MME faults with no patch available that are affecting a large number of subscribers?"**

*Expected agent behavior:* Invokes `mme_bug_impact_analyzer`, filters for `patch_available = false`, sorts by `affected_subscribers` descending. Should highlight the highest-impact unpatched bugs.

*Talking point:* "Unpatched bugs with high subscriber impact are your top escalation items for the vendor SLA call. The agent just built your agenda."

---

> **"We had a major incident last Tuesday. Can you search for any core network events around that time that might explain what happened?"**

*Expected agent behavior:* Invokes `core_network_event_search` with a time-bounded query around last Tuesday, returns high-severity events with `event_description` and `alert_message` for root cause analysis.

*Talking point:* "Post-incident analysis is one of the highest-value use cases. Instead of a 2-hour log review, the NOC team gets a structured summary of what the network was telling us during the incident window."

---

> **"Which network elements are closest to their capacity thresholds based on current signaling volume?"**

*Expected agent behavior:* Invokes `signaling_storm_detector`, compares `msg_count` against `capacity_threshold_msg_per_min` from the registry enrichment, returns elements approaching or exceeding threshold.

*Talking point:* "This is proactive capacity management. The agent is not waiting for a storm — it's identifying elements that are trending toward their rated capacity limit before the alarm fires."

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "Modern query language built for analytics — not a bolt-on to a legacy query engine"
- "Piped syntax reads like English: FROM → WHERE → STATS → EVAL → SORT → LIMIT"
- "Operates on columnar data blocks, not row-by-row — extremely performant at scale"
- "INLINESTATS is unique to ES|QL — computes statistical context inline without subqueries or window functions"
- "LOOKUP JOIN enables multi-dataset enrichment without ETL pipelines or data warehouses"
- "DATE_TRUNC and BUCKET make time-series analysis first-class — not an afterthought"

### **On Agent Builder:**
- "Bridges AI reasoning and enterprise operational data — no custom orchestration layer"
- "Configure, don't code — tools are ES|QL queries with natural language descriptions"
- "Works against existing Elasticsearch indices — no data migration required"
- "The agent automatically selects the right tool based on the question — tool descriptions are the key"
- "Custom instructions shape the agent's persona, prioritization logic, and output format"
- "Multi-tool reasoning: the agent can invoke multiple tools in sequence to answer a compound question"

### **On Statistical Anomaly Detection:**
- "Z-score based detection adapts to each element's own baseline — no manual threshold tuning per node"
- "INLINESTATS computes mean and standard deviation inline — the statistical context travels with the data"
- "3 standard deviations is a principled threshold — statistically significant, not arbitrary"
- "This approach scales to thousands of network elements without per-element configuration"

### **On Business Value for Network Operations:**
- "Reduces mean time to detect (MTTD) — statistical anomaly detection catches storms before they cascade"
- "Reduces mean time to understand (MTTU) — LOOKUP JOIN enrichment provides context at query time, not after"
- "Democratizes NOC expertise — a junior engineer can ask the same questions a senior engineer would"
- "Shifts from reactive monitoring to proactive observability — trending and capacity analysis built in"
- "Vendor accountability — handover failure analytics by vendor provides SLA evidence"
- "Patch prioritization — bug enrichment with subscriber impact quantifies the cost of unresolved defects"
- "One agent, six tools, full network coverage — replaces multiple siloed dashboards"

### **On Data Architecture:**
- "Lookup indexes are a purpose-built join optimization in Elasticsearch — not a workaround"
- "Reference data (tower locations, bug signatures, element registry) stays current without rebuilding pipelines"
- "Timeseries indexes hold the operational heartbeat; lookup indexes hold the context — clean separation"
- "LOOKUP JOIN is a left join — all operational records are preserved, enriched where a match exists"

---

## **🔧 Troubleshooting**

### **If a query fails:**

| Symptom | Likely Cause | Fix |
|---|---|---|
| `Unknown index` error | Index name mismatch | Check exact index name — ES|QL is case-sensitive |
| `Unknown column` error | Field name typo | Verify against the dataset field list in this guide |
| LOOKUP JOIN returns nulls for all enriched fields | Joined index not in lookup mode | Re-create the index with `"index.mode": "lookup"` |
| LOOKUP JOIN returns no rows | Join key format mismatch | Verify `cell_tower_id` / `network_element_id` formats match exactly across datasets |
| INLINESTATS returns null Z-scores | Insufficient data points for std dev calculation | Widen the time window or check that the dataset has sufficient records |
| `TO_DOUBLE` division returns 0 | Missing `TO_DOUBLE` cast | Ensure both numerator and denominator are cast with `TO_DOUBLE()` before division |
| Date aggregation returns unexpected buckets | Timezone offset | Add `| EVAL @timestamp = DATE_FORMAT("yyyy-MM-dd'T'HH:mm:ss", @timestamp)` to debug |

### **If the agent gives wrong answers:**

| Symptom | Likely Cause | Fix |
|---|---|---|
| Agent uses wrong tool | Tool description too vague | Make descriptions more specific about which questions each tool answers |
| Agent doesn't invoke any tool | Question phrasing doesn't match tool descriptions | Add synonyms to tool descriptions (e.g., "signaling storm OR message burst OR overload") |
| Agent returns raw data instead of insight | Custom instructions too permissive | Add explicit instruction: "Always interpret results and provide a recommendation, not just raw data" |
| Agent hallucinates field names | LLM is generating ES|QL on the fly | Ensure tools use pre-built parameterized queries, not LLM-generated ES|QL |

### **If join returns no results:**
1. Run `FROM cell_tower_reference | LIMIT 5` to verify the lookup index has data
2. Run `FROM call_detail_records | STATS count = COUNT(*) BY cell_tower_id | LIMIT 5` to check join key values
3. Compare the `cell_tower_id` format between datasets — a mismatch of `TOWER_001` vs `tower_001` will silently return nulls

### **Demo environment checklist (run before audience arrives):**
- [ ] All 11 indices exist and have data (`FROM <index> | LIMIT 1`)
- [ ] All 6 lookup indices have `index.mode: lookup`
- [ ] At least one LOOKUP JOIN query returns enriched results
- [ ] Agent is configured with all 6 tools
- [ ] Agent responds to "what tools do you have?" with a coherent summary
- [ ] Kibana time picker is set to "Last 7 days" for timeseries datasets

---

## **🎬 Closing**

**Presenter:**

"Let's recap what we've demonstrated today across your Network Operations environment:

✅ **Full-text incident search** — BM25 relevance search across core network events for rapid split-brain and consensus failure triage

✅ **Time-series interruption trending** — Hourly session failure analysis by RAT type, showing 4G vs 5G degradation independently

✅ **Statistical anomaly detection** — Z-score based dropped call and signaling storm detection that adapts to each element's own baseline — no manual threshold management

✅ **Multi-dataset enrichment via LOOKUP JOIN** — Cell tower mobility zones, network element capacity thresholds, MME bug signatures, and RAN site metadata all joined at query time

✅ **Natural language interface** — A single AI agent with six tools covering the entire NOC observability surface, answering questions that would previously require multiple tools and senior engineering expertise

✅ **Proactive observability** — Not just alerting on what's broken, but trending what's degrading and identifying what's approaching capacity before it becomes an incident

The queries we built today are running against your actual data model — `data_session_logs`, `core_network_events`, `mme_system_logs`, `signaling_logs`, `call_detail_records`, `ran_performance_metrics` — with enrichment from your reference datasets. This is not a proof of concept built on synthetic data. It's your data, your field names, your network.

**Agent Builder can be deployed in days, not months.** The queries are already written and tested. The agent configuration is straightforward. The lookup indexes are a one-time setup.

What questions do you have?"

---

*Internal guide prepared for Telco Network Operations — Elastic Agent Builder Observability Demo*
*Queries validated against indexed datasets — do not modify field names without re-validation*'''

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
