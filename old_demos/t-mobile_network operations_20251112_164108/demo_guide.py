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

### **Dataset 1: mme_signaling_failures**
- **Type:** Timeseries
- **Record Count:** 100,000+ records
- **Primary Key:** Composite (timestamp + mme_host + cell_id)
- **Update Frequency:** Real-time streaming
- **Purpose:** Tracks signaling failures, authentication issues, and handoff problems across the mobile core network

**Key Fields:**
- `@timestamp` - Event occurrence time
- `mme_host` - MME hostname (e.g., mme-dal-01, mme-nyc-02)
- `cell_id` - Cell tower identifier
- `failure_type` - Type of failure (handoff_failure, auth_timeout, signaling_storm, split_brain_condition)
- `imsi` - International Mobile Subscriber Identity
- `failure_count` - Number of failures in time window
- `response_time_ms` - Response time in milliseconds
- `error_code` - Specific error identifier
- `severity` - Critical, High, Medium, Low

**Relationships:**
- Links to `mme_host_inventory` via `mme_host`
- Links to `cell_tower_reference` via `cell_id`

---

### **Dataset 2: cell_tower_reference**
- **Type:** Reference data (lookup mode)
- **Record Count:** 5,000+ records
- **Primary Key:** `cell_id`
- **Update Frequency:** Weekly
- **Purpose:** Provides geographic and technical details for cell tower infrastructure

**Key Fields:**
- `cell_id` - Unique cell tower identifier
- `tower_name` - Human-readable tower name
- `region` - Geographic region (Northeast, Southeast, West, Midwest, Southwest)
- `city` - City location
- `state` - State code
- `latitude` - GPS coordinate
- `longitude` - GPS coordinate
- `technology` - 4G_LTE, 5G_NSA, 5G_SA
- `capacity` - Maximum subscriber capacity
- `vendor` - Equipment vendor (Ericsson, Nokia, Samsung)
- `installation_date` - Tower activation date

**Relationships:**
- Referenced by `mme_signaling_failures` via `cell_id`

---

### **Dataset 3: mme_host_inventory**
- **Type:** Reference data (lookup mode)
- **Record Count:** 50+ records
- **Primary Key:** `mme_host`
- **Update Frequency:** Monthly
- **Purpose:** Inventory of Mobility Management Entity servers with capacity and configuration details

**Key Fields:**
- `mme_host` - MME hostname
- `datacenter` - Physical datacenter location
- `cluster_name` - Logical cluster grouping
- `max_subscribers` - Maximum subscriber capacity
- `current_load_pct` - Current load percentage
- `software_version` - MME software version
- `hss_primary` - Primary Home Subscriber Server
- `hss_backup` - Backup HSS
- `status` - active, maintenance, degraded

**Relationships:**
- Referenced by `mme_signaling_failures` via `mme_host`
- Referenced by `subscriber_authentication_events` via `mme_host`

---

### **Dataset 4: subscriber_authentication_events**
- **Type:** Timeseries
- **Record Count:** 500,000+ records
- **Primary Key:** Composite (timestamp + imsi + mme_host)
- **Update Frequency:** Real-time streaming
- **Purpose:** Tracks all subscriber authentication attempts, successes, and failures for security monitoring

**Key Fields:**
- `@timestamp` - Authentication attempt time
- `imsi` - International Mobile Subscriber Identity
- `mme_host` - MME processing the authentication
- `auth_result` - success, failure, timeout
- `auth_type` - initial_attach, handoff, periodic_update
- `failure_reason` - HSS_timeout, invalid_credentials, network_error, roaming_not_allowed
- `response_time_ms` - Authentication response time
- `roaming` - true/false
- `home_network` - Home network operator code
- `visiting_network` - Visited network code (for roaming)
- `device_type` - phone, tablet, iot_device, hotspot

**Relationships:**
- Links to `mme_host_inventory` via `mme_host`

---

## **🚀 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

**CRITICAL: All indexes need "index.mode": "lookup" for joins to work**

#### **Upload mme_signaling_failures (timeseries)**

1. Navigate to **Kibana → Management → Dev Tools**
2. Create the index with timeseries settings:

```json
PUT /mme_signaling_failures
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "mme_host": { "type": "keyword" },
      "cell_id": { "type": "keyword" },
      "failure_type": { "type": "keyword" },
      "imsi": { "type": "keyword" },
      "failure_count": { "type": "integer" },
      "response_time_ms": { "type": "integer" },
      "error_code": { "type": "keyword" },
      "severity": { "type": "keyword" }
    }
  }
}
```

3. Navigate to **Kibana → Management → Data Views**
4. Create a data view for `mme_signaling_failures` with time field `@timestamp`
5. Go to **Kibana → Management → Stack Management → Index Management → Data**
6. Use the file upload feature to upload your CSV

---

#### **Upload cell_tower_reference (lookup mode)**

1. In Dev Tools, create the index with **lookup mode**:

```json
PUT /cell_tower_reference
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "cell_id": { "type": "keyword" },
      "tower_name": { "type": "text" },
      "region": { "type": "keyword" },
      "city": { "type": "keyword" },
      "state": { "type": "keyword" },
      "latitude": { "type": "float" },
      "longitude": { "type": "float" },
      "technology": { "type": "keyword" },
      "capacity": { "type": "integer" },
      "vendor": { "type": "keyword" },
      "installation_date": { "type": "date" }
    }
  }
}
```

2. Upload the CSV file using the file upload feature

---

#### **Upload mme_host_inventory (lookup mode)**

1. In Dev Tools:

```json
PUT /mme_host_inventory
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "mme_host": { "type": "keyword" },
      "datacenter": { "type": "keyword" },
      "cluster_name": { "type": "keyword" },
      "max_subscribers": { "type": "integer" },
      "current_load_pct": { "type": "float" },
      "software_version": { "type": "keyword" },
      "hss_primary": { "type": "keyword" },
      "hss_backup": { "type": "keyword" },
      "status": { "type": "keyword" }
    }
  }
}
```

2. Upload the CSV file

---

#### **Upload subscriber_authentication_events (timeseries)**

1. In Dev Tools:

```json
PUT /subscriber_authentication_events
{
  "mappings": {
    "properties": {
      "@timestamp": { "type": "date" },
      "imsi": { "type": "keyword" },
      "mme_host": { "type": "keyword" },
      "auth_result": { "type": "keyword" },
      "auth_type": { "type": "keyword" },
      "failure_reason": { "type": "keyword" },
      "response_time_ms": { "type": "integer" },
      "roaming": { "type": "boolean" },
      "home_network": { "type": "keyword" },
      "visiting_network": { "type": "keyword" },
      "device_type": { "type": "keyword" }
    }
  }
}
```

2. Create data view with time field `@timestamp`
3. Upload the CSV file

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to your AI Agent chat interface
- Have the agent already configured with all tools

### **Demo Script**

**Presenter:** "Before we dive into how this works, let me show you the end result. I'm going to ask our AI agent a complex business question about T-Mobile's network operations."

**Sample questions to demonstrate:**

1. **ROI/Business Impact Question:**
   - "What's the estimated customer churn risk from the top 5 cell towers with the highest failure rates this week? Calculate potential revenue impact assuming $65 average monthly ARPU."

2. **Cross-Dataset Security Analysis:**
   - "Show me any MME hosts experiencing unusual IMSI influx patterns in the last 24 hours. Are these correlated with authentication failures that might indicate an SS7 attack?"

3. **Predictive Cascade Failure Detection:**
   - "Which cell towers are showing early warning signs of cascade failures based on z-score analysis of handoff failure spikes? Include the tower location and vendor information."

4. **HSS Health Monitoring:**
   - "Analyze authentication failure patterns across all MME hosts. Are we seeing mass authentication failures that indicate HSS problems? Which HSS servers are affected?"

5. **Split-Brain Detection:**
   - "Identify any potential split-brain conditions by finding MME hosts with simultaneous high error rates and correlated failure patterns in the last hour."

6. **Roaming Configuration Analysis:**
   - "What percentage of roaming authentication failures are due to configuration errors versus actual security threats? Break it down by visiting network."

7. **Capacity Planning Question:**
   - "Which MME hosts are operating above 80% capacity while also experiencing elevated signaling failures? What's the correlation between load and failure rate?"

**Pick 2-3 questions and run them live. Let the agent work through the analysis.**

**Transition:** "So how does this actually work? Let's go under the hood and build these queries from scratch using ES|QL."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open Kibana Dev Tools Console
- Have the indices already created and populated

---

### **Query 1: Simple Aggregation (2 minutes)**

**Presenter:** "T-Mobile's Network Operations team wants to know: What are the top cell towers experiencing the most signaling failures today?"

**Copy/paste into console:**

```esql
FROM mme_signaling_failures
| WHERE @timestamp >= NOW() - 24 hours
| STATS total_failures = SUM(failure_count) BY cell_id
| SORT total_failures DESC
| LIMIT 10
```

**Run and narrate results:** "This is basic ES|QL:
- FROM: Source our signaling failure data
- WHERE: Filter to last 24 hours
- STATS: Aggregate failures by cell tower
- SORT and LIMIT: Top 10 problem towers

The syntax is intuitive - it reads like English. Already we can see which towers need immediate attention."

---

### **Query 2: Add Calculations with EVAL (3 minutes)**

**Presenter:** "Let's add calculations to understand the severity and patterns of these failures."

**Copy/paste:**

```esql
FROM mme_signaling_failures
| WHERE @timestamp >= NOW() - 24 hours
| STATS 
    total_failures = SUM(failure_count),
    avg_response_time = AVG(response_time_ms),
    unique_imsi_count = COUNT_DISTINCT(imsi),
    critical_failures = SUM(CASE(severity == "Critical", failure_count, 0))
  BY cell_id
| EVAL critical_pct = TO_DOUBLE(critical_failures) / TO_DOUBLE(total_failures) * 100
| EVAL avg_response_time = ROUND(avg_response_time, 2)
| WHERE total_failures > 100
| SORT critical_pct DESC
| LIMIT 15
```

**Run and highlight:** "Key additions:
- EVAL: Creates calculated fields on-the-fly like critical failure percentage
- TO_DOUBLE: Critical for decimal division - prevents integer math
- Multiple STATS: Aggregating failures, response times, affected subscribers
- CASE statement: Conditional aggregation for critical failures only
- Business-relevant calculations that help prioritize remediation

Now we can see not just volume, but severity and subscriber impact."

---

### **Query 3: Join Datasets with LOOKUP JOIN (3 minutes)**

**Presenter:** "Now let's combine data from multiple sources using ES|QL's JOIN capability to add geographic and vendor context."

**Copy/paste:**

```esql
FROM mme_signaling_failures
| WHERE @timestamp >= NOW() - 24 hours
| STATS 
    total_failures = SUM(failure_count),
    critical_failures = SUM(CASE(severity == "Critical", failure_count, 0)),
    affected_subscribers = COUNT_DISTINCT(imsi)
  BY cell_id
| EVAL critical_pct = TO_DOUBLE(critical_failures) / TO_DOUBLE(total_failures) * 100
| LOOKUP JOIN cell_tower_reference ON cell_id
| WHERE total_failures > 50
| EVAL impact_score = total_failures * critical_pct * affected_subscribers / 1000
| SORT impact_score DESC
| KEEP cell_id, tower_name, city, state, region, vendor, technology, total_failures, critical_pct, affected_subscribers, impact_score
| LIMIT 20
```

**Run and explain:** "Magic happening here:
- LOOKUP JOIN: Combines signaling data with cell tower reference data using cell_id
- Now we have tower names, locations, vendors, and technology types
- This is a LEFT JOIN: All failure records kept, enriched with tower details
- For LOOKUP JOIN to work, cell_tower_reference must have 'index.mode: lookup'
- Impact score calculation combines volume, severity, and subscriber count
- We can now see if certain vendors or technologies have systemic issues

This single query gives Network Operations actionable intelligence with full context."

---

### **Query 4: Complex Multi-Dataset Analytics (2 minutes)**

**Presenter:** "For the grand finale - a sophisticated analytical query showing cell tower cascade failure detection using z-score statistical analysis. This is the kind of query that would traditionally require a data scientist."

**Copy/paste:**

```esql
FROM mme_signaling_failures
| WHERE @timestamp >= NOW() - 2 hours AND failure_type == "handoff_failure"
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS failure_rate = SUM(failure_count) BY cell_id, time_bucket
| STATS 
    avg_failure_rate = AVG(failure_rate),
    stddev_failure_rate = STDEV(failure_rate),
    max_failure_rate = MAX(failure_rate),
    recent_failure_rate = MAX(CASE(time_bucket >= NOW() - 15 minutes, failure_rate, 0))
  BY cell_id
| EVAL z_score = (recent_failure_rate - avg_failure_rate) / stddev_failure_rate
| WHERE z_score > 2.5 AND stddev_failure_rate > 0
| LOOKUP JOIN cell_tower_reference ON cell_id
| EVAL alert_level = CASE(
    z_score > 4, "CRITICAL",
    z_score > 3, "HIGH",
    "MEDIUM"
  )
| EVAL cascade_risk = CASE(
    recent_failure_rate > avg_failure_rate * 5, "Imminent Cascade",
    recent_failure_rate > avg_failure_rate * 3, "High Risk",
    "Elevated Risk"
  )
| SORT z_score DESC
| KEEP cell_id, tower_name, city, state, region, vendor, technology, 
       z_score, alert_level, cascade_risk, recent_failure_rate, avg_failure_rate, max_failure_rate
| LIMIT 25
```

**Run and break down:** 

"This query demonstrates advanced analytical capabilities:

**Statistical Analysis:**
- Z-score calculation identifies towers with abnormal failure spikes (>2.5 standard deviations)
- Compares recent 15-minute window against 2-hour baseline behavior
- Filters out noise by requiring meaningful standard deviation

**Time-Series Processing:**
- DATE_TRUNC creates 5-minute buckets for granular analysis
- Window functions track both historical averages and recent spikes
- CASE statements for temporal comparisons

**Multi-Dataset Enrichment:**
- LOOKUP JOIN adds geographic and vendor context
- Helps identify if cascade failures are region-specific or vendor-specific

**Business Logic:**
- Alert levels (CRITICAL/HIGH/MEDIUM) for prioritization
- Cascade risk assessment based on rate-of-change
- Actionable intelligence for Network Operations

This single query replaces what would traditionally require:
- Data extraction to a data lake
- Python/R statistical analysis
- Manual correlation with reference data
- Dashboard creation

Instead, it runs in milliseconds directly on operational data. This is the power of ES|QL for real-time network analytics."

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

**Agent Configuration:**

**Agent ID:** `tmobile-network-ops-agent`

**Display Name:** `T-Mobile Network Operations AI Assistant`

**Custom Instructions:** 

```
You are an AI assistant specialized in T-Mobile's mobile core network operations and telecommunications analytics. You help Network Operations teams detect, diagnose, and prevent network issues.

Your expertise includes:
- MME (Mobility Management Entity) signaling analysis
- Cell tower performance and cascade failure detection
- HSS (Home Subscriber Server) authentication patterns
- Security threat detection (SS7 attacks, IMSI influx anomalies)
- Split-brain conditions and signaling storms
- Roaming configuration and international connectivity
- Customer churn risk analysis related to network quality

When analyzing data:
1. Always consider the business impact (customer churn, revenue, subscriber experience)
2. Prioritize critical and high-severity issues
3. Look for correlated patterns across multiple MME hosts or cell towers
4. Provide actionable recommendations with specific tower IDs, MME hosts, or regions
5. Calculate statistical measures (z-scores, percentiles) for anomaly detection
6. Consider geographic and vendor patterns in failure analysis

When asked about revenue impact:
- Use $65 as average monthly ARPU (Average Revenue Per User)
- Estimate churn probability based on outage duration and severity
- Consider subscriber count in impact calculations

Always provide context by joining with reference data (cell tower details, MME inventory) when relevant.
```

---

### **Creating Tools**

#### **Tool 1: Cell Tower Cascade Failure Detection**

**Tool Name:** `detect_cell_tower_cascade_failures`

**Description:** 
```
Detects cell towers showing abnormal handoff failure spikes using z-score statistical analysis. Identifies potential cascade failures before they escalate by comparing recent failure rates against historical baselines. Returns towers with z-score > 2.5, enriched with location and vendor information. Use this for proactive alerting and preventing widespread outages.
```

**ES|QL Query:**
```esql
FROM mme_signaling_failures
| WHERE @timestamp >= NOW() - 2 hours AND failure_type == "handoff_failure"
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS failure_rate = SUM(failure_count) BY cell_id, time_bucket
| STATS 
    avg_failure_rate = AVG(failure_rate),
    stddev_failure_rate = STDEV(failure_rate),
    max_failure_rate = MAX(failure_rate),
    recent_failure_rate = MAX(CASE(time_bucket >= NOW() - 15 minutes, failure_rate, 0))
  BY cell_id
| EVAL z_score = (recent_failure_rate - avg_failure_rate) / stddev_failure_rate
| WHERE z_score > 2.5 AND stddev_failure_rate > 0
| LOOKUP JOIN cell_tower_reference ON cell_id
| EVAL alert_level = CASE(z_score > 4, "CRITICAL", z_score > 3, "HIGH", "MEDIUM")
| SORT z_score DESC
| LIMIT 25
```

---

#### **Tool 2: IMSI Influx Anomaly Detection**

**Tool Name:** `detect_imsi_influx_anomalies`

**Description:**
```
Identifies unusual subscriber (IMSI) influx patterns by detecting statistical anomalies in unique IMSI counts per MME host. Helps catch security attacks (SS7 attacks, rogue network attempts) early by flagging MME hosts with abnormal subscriber activity. Compares recent 30-minute window against 4-hour baseline.
```

**ES|QL Query:**
```esql
FROM subscriber_authentication_events
| WHERE @timestamp >= NOW() - 4 hours
| EVAL time_bucket = DATE_TRUNC(30 minutes, @timestamp)
| STATS unique_imsi = COUNT_DISTINCT(imsi) BY mme_host, time_bucket
| STATS 
    avg_imsi_count = AVG(unique_imsi),
    stddev_imsi = STDEV(unique_imsi),
    recent_imsi_count = MAX(CASE(time_bucket >= NOW() - 30 minutes, unique_imsi, 0))
  BY mme_host
| EVAL z_score = (recent_imsi_count - avg_imsi_count) / stddev_imsi
| WHERE z_score > 3 AND stddev_imsi > 0
| LOOKUP JOIN mme_host_inventory ON mme_host
| EVAL threat_level = CASE(z_score > 5, "CRITICAL", z_score > 4, "HIGH", "MEDIUM")
| SORT z_score DESC
| LIMIT 20
```

---

#### **Tool 3: HSS Mass Authentication Failure Detection**

**Tool Name:** `detect_hss_authentication_failures`

**Description:**
```
Detects mass authentication failures indicating HSS (Home Subscriber Server) problems by analyzing failure rates and response time anomalies across MME hosts. Identifies which HSS servers are affected and the scope of impact. Critical for preventing help desk overload and proactive incident management.
```

**ES|QL Query:**
```esql
FROM subscriber_authentication_events
| WHERE @timestamp >= NOW() - 1 hour
| STATS 
    total_attempts = COUNT(*),
    failures = SUM(CASE(auth_result == "failure", 1, 0)),
    timeouts = SUM(CASE(auth_result == "timeout", 1, 0)),
    avg_response_ms = AVG(response_time_ms),
    hss_timeout_failures = SUM(CASE(failure_reason == "HSS_timeout", 1, 0))
  BY mme_host
| EVAL failure_rate = TO_DOUBLE(failures) / TO_DOUBLE(total_attempts) * 100
| EVAL timeout_rate = TO_DOUBLE(timeouts) / TO_DOUBLE(total_attempts) * 100
| WHERE failure_rate > 10 OR timeout_rate > 5
| LOOKUP JOIN mme_host_inventory ON mme_host
| EVAL hss_issue_indicator = CASE(
    hss_timeout_failures > 100, "HSS Outage Likely",
    timeout_rate > 15, "HSS Performance Degraded",
    "Network Issue"
  )
| SORT failure_rate DESC
| LIMIT 30
```

---

#### **Tool 4: MME Split-Brain Detection**

**Tool Name:** `detect_mme_split_brain_conditions`

**Description:**
```
Multi-dimensional analysis detecting split-brain scenarios by identifying simultaneous high error rates across multiple MME hosts with correlated failure patterns. Detects signaling storms and cluster-wide issues. Essential for identifying core network architectural problems.
```

**ES|QL Query:**
```esql
FROM mme_signaling_failures
| WHERE @timestamp >= NOW() - 30 minutes
| STATS 
    total_failures = SUM(failure_count),
    split_brain_events = SUM(CASE(failure_type == "split_brain_condition", failure_count, 0)),
    signaling_storms = SUM(CASE(failure_type == "signaling_storm", failure_count, 0)),
    distinct_error_codes = COUNT_DISTINCT(error_code),
    affected_cells = COUNT_DISTINCT(cell_id)
  BY mme_host
| WHERE total_failures > 200
| LOOKUP JOIN mme_host_inventory ON mme_host
| EVAL split_brain_risk = CASE(
    split_brain_events > 50, "Active Split-Brain",
    signaling_storms > 100, "Signaling Storm",
    distinct_error_codes > 10 AND affected_cells > 50, "Cluster Issue",
    "Elevated Errors"
  )
| EVAL severity_score = (split_brain_events * 5) + (signaling_storms * 3) + (total_failures / 10)
| SORT severity_score DESC
| LIMIT 25
```

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

#### **Warm-up Questions (Start Easy):**

1. "What are the top 5 cell towers with the most failures in the last 24 hours? Include the city and state."

2. "Show me all MME hosts currently operating above 75% capacity."

3. "How many authentication failures occurred in the last hour?"

4. "Which vendors have cell towers in the Northeast region?"

---

#### **Business-Focused Questions:**

5. "Calculate the estimated revenue at risk from the top 10 worst-performing cell towers this week. Assume $65 monthly ARPU and 15% churn probability for affected subscribers."

6. "Which MME hosts are experiencing both high load (>80%) and elevated failure rates? What's the correlation and what's the business impact?"

7. "Show me roaming authentication failures broken down by visiting network. Which international carriers have configuration issues that might be impacting roaming revenue?"

8. "What percentage of our critical severity failures are concentrated in the top 5 cell towers? Should we prioritize these for emergency maintenance?"

---

#### **Trend Analysis Questions:**

9. "Are we seeing an increasing trend in handoff failures over the past 6 hours? Which regions are most affected?"

10. "Compare authentication failure rates between roaming and non-roaming subscribers. Is there a significant difference that indicates roaming-specific issues?"

11. "Show me the correlation between MME response times and authentication failure rates. Is there a performance threshold where failures spike?"

---

#### **Advanced Security & Operations:**

12. "Detect any MME hosts with unusual IMSI influx patterns that might indicate an SS7 attack or security threat. What's the anomaly score?"

13. "Are there any cell towers showing early warning signs of cascade failures based on z-score analysis? Which ones need immediate attention?"

14. "Identify potential split-brain conditions by finding MME hosts with simultaneous high error rates in the last 30 minutes. Are these in the same cluster?"

15. "Which HSS servers are showing signs of degradation based on mass authentication failures and timeout patterns?"

---

#### **Optimization Questions:**

16. "Which 5G cell towers have the highest failure rates compared to 4G towers? Is there a technology-specific issue?"

17. "Show me cell towers from vendor 'Ericsson' that have significantly higher failure rates than the vendor average. Do we have a firmware or configuration issue?"

18. "What's the average response time for each MME host? Which ones are outliers that might need performance tuning?"

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "Modern query language, built for analytics and operational intelligence"
- "Piped syntax is intuitive and readable - even non-technical stakeholders can understand the logic"
- "Operates on blocks, not rows - extremely performant even on hundreds of millions of telemetry records"
- "Supports complex operations: joins, window functions, time-series analysis, statistical functions"
- "No need to move data to a separate analytics platform - query operational data in real-time"

### **On Agent Builder:**
- "Bridges AI and enterprise data without custom development"
- "No coding required - configure, don't code. Tools are just ES|QL queries with descriptions"
- "Works with existing Elasticsearch indices - no data duplication or ETL pipelines"
- "Agent automatically selects the right tools based on natural language questions"
- "Democratizes access to complex analytics - Network Operations engineers don't need to be data scientists"

### **On Business Value for T-Mobile:**
- "Reduces Mean Time to Detect (MTTD) for network issues from hours to seconds"
- "Proactive alerting prevents cascade failures that could impact millions of subscribers"
- "Estimated 30-40% reduction in customer churn from network quality issues"
- "Help desk call volume reduction through early detection and remediation"
- "Faster decision-making - executives can ask questions in natural language and get instant answers"
- "Reduces dependency on centralized data teams - empowers Network Operations with self-service analytics"
- "Security threat detection (SS7 attacks, roaming fraud) happens in real-time, not post-incident"

### **On Telecommunications-Specific Value:**
- "Core network visibility that was previously impossible without extensive custom development"
- "Statistical anomaly detection (z-scores, standard deviations) built into queries - no separate ML pipeline needed"
- "Multi-dimensional correlation across MME hosts, cell towers, HSS servers, and subscriber behavior"
- "Roaming analytics that identify configuration errors before they impact international partnerships"
- "Capacity planning insights by correlating load with failure patterns"

---

## **🔧 Troubleshooting**

**If a query fails:**
- Check index names match exactly (case-sensitive): `mme_signaling_failures`, `cell_tower_reference`, `mme_host_inventory`, `subscriber_authentication_events`
- Verify field names are case-sensitive correct: `@timestamp`, `mme_host`, `cell_id`, `failure_type`
- Ensure joined indices (`cell_tower_reference`, `mme_host_inventory`) are in lookup mode
- Check that date ranges have data - use `NOW() - 24 hours` syntax for relative times

**If agent gives wrong answer:**
- Check tool descriptions - are they clear about what data they return?
- Review custom instructions - does the agent understand telecommunications terminology?
- Verify the agent has access to all 4 tools
- Test the underlying ES|QL query independently in Dev Tools

**If join returns no results:**
- Verify join key format is consistent across datasets (e.g., `cell_id` format matches)
- Check that lookup index has data: `FROM cell_tower_reference | LIMIT 10`
- Ensure lookup index was created with `"index.mode": "lookup"` setting
- Verify the join key exists in both datasets

**If statistical calculations seem off:**
- Ensure using `TO_DOUBLE()` for division operations to prevent integer math
- Check that `STDEV()` has enough data points (at least 2 records per group)
- Verify time ranges are appropriate for the analysis (z-scores need baseline data)

**If agent is slow:**
- Check if queries are scanning too much data - add more restrictive time filters
- Verify indices are properly time-based and using data streams if appropriate
- Consider adding `LIMIT` clauses to tools that might return large result sets

---

## **🎬 Closing**

"What we've shown today for T-Mobile Network Operations:

✅ **Complex telecommunications analytics** on interconnected datasets - MME signaling, cell towers, authentication events, and inventory data

✅ **Natural language interface** for Network Operations engineers - no SQL or programming knowledge required

✅ **Real-time insights** without custom development - queries run on live operational data in milliseconds

✅ **Statistical anomaly detection** that would traditionally require data scientists - z-scores, standard deviations, correlation analysis

✅ **Proactive alerting** for cascade failures, split-brain conditions, HSS issues, and security threats - detect problems before customers are impacted

✅ **Business impact analysis** - revenue at risk, churn probability, subscriber impact - not just technical metrics

✅ **Multi-dimensional correlation** - identify patterns across geography, vendors, technology types, and time

**Time to Value:**
- Agent Builder can be deployed in **days, not months**
- No custom application development required
- Leverages existing Elasticsearch infrastructure
- Tools are just ES|QL queries - your team can create new ones as needs evolve

**ROI for T-Mobile:**
- Reduce customer churn from network quality issues
- Prevent revenue loss from extended outages
- Decrease help desk call volume through proactive remediation
- Faster incident response and root cause analysis
- Security threat detection in real-time

This isn't just a demo - this is production-ready technology that can transform how T-Mobile's Network Operations team monitors, analyzes, and optimizes the mobile core network.

**Questions?**"'''

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
