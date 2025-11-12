# ES|QL Patterns and Anti-Patterns Guide

## Overview
This guide documents proven patterns and common pitfalls when generating ES|QL queries for Elastic Agent Builder demos. Following these patterns ensures queries execute successfully and provide meaningful insights.

## ✅ Recommended Patterns

### 🎯 CRITICAL: KEEP Field Prioritization for Agent Tool Calls

**⚠️ AGENT BUILDER LIMITATION**: When ES|QL queries are used as agent tools, **ONLY THE FIRST 5 FIELDS** in the KEEP statement are guaranteed to be included in the tool response.

#### The Problem
```esql
// BAD: Critical fields are buried after position 5
| KEEP timestamp, event_id, session_id, trace_id, span_id, error_message, customer_id, severity
//     ↑ field 1   ↑ field 2  ↑ field 3   ↑ field 4  ↑ field 5  ↑ NOT VISIBLE  ↑ NOT VISIBLE ↑ NOT VISIBLE
```
When an agent calls this query, `error_message`, `customer_id`, and `severity` will be **MISSING** from the tool response!

#### The Solution
```esql
// GOOD: Most critical fields are in positions 1-5
| KEEP customer_id, severity, error_message, timestamp, event_id, session_id, trace_id, span_id
//     ↑ field 1    ↑ field 2  ↑ field 3      ↑ field 4   ↑ field 5  ↑ optional  ↑ optional ↑ optional
```

#### KEEP Field Prioritization Rules

1. **Position 1-2**: **Primary Keys/Identifiers** that agents need for actions
   - `customer_id`, `user_id`, `account_id`, `ticket_id`, `incident_id`

2. **Position 3-4**: **Critical Business Values** for decision-making
   - `severity`, `priority`, `score`, `risk_level`, `amount`, `status`

3. **Position 5**: **Human-Readable Context** for agent responses
   - `error_message`, `description`, `title`, `summary`, `reason`

4. **Position 6+**: **Supporting Data** (nice-to-have but not critical)
   - `timestamp`, `session_id`, `trace_id`, metadata fields

#### Examples by Use Case

**🔍 Search/RAG Query**:
```esql
| KEEP article_id, relevance_score, title, content_snippet, category, author, created_date, tags
//     ↑ ID for retrieval ↑ ranking  ↑ display  ↑ preview    ↑ context  ↑ optional...
```

**🚨 Anomaly Detection Query**:
```esql
| KEEP entity_id, anomaly_severity, metric_name, z_score, current_value, baseline, timestamp
//     ↑ what     ↑ how bad         ↑ which metric ↑ deviation ↑ actual   ↑ optional...
```

**📊 Analytics Query**:
```esql
| KEEP dimension, metric_value, percentage_of_total, trend, rank, period, details
//     ↑ grouping ↑ main value  ↑ context           ↑ direction ↑ position ↑ optional...
```

#### Why This Matters
- **Agents make decisions** based on the first 5 fields
- **Tool responses are truncated** after field 5
- **Users see incomplete data** if critical fields are beyond position 5
- **Actions may fail** if required IDs are not in the visible fields

### 1. Statistical Z-Score Anomaly Detection
**Use Case**: Detect anomalies, outliers, and significant deviations from normal behavior

```esql
FROM <index>
| EVAL time_bucket = DATE_TRUNC(<interval>, @timestamp)
| STATS
    <metric> = <aggregation>
  BY time_bucket, <dimension>
| INLINESTATS
    avg_<metric> = AVG(<metric>),
    stddev_<metric> = STD_DEV(<metric>),
    p95_<metric> = PERCENTILE(<metric>, 95)
  BY <dimension>
| EVAL
    z_score = (<metric> - avg_<metric>) / COALESCE(stddev_<metric>, 1)
| WHERE z_score > <threshold>
| EVAL severity = CASE(
    z_score > 4, "CRITICAL",
    z_score > 3, "HIGH",
    z_score > 2.5, "MEDIUM",
    "LOW"
  )
```

**Pattern Benefits**:
1. **Statistical Rigor**: Z-scores are standardized and well-understood
2. **Adaptive Thresholds**: Automatically adjusts to each dimension's normal behavior
3. **Severity Gradients**: Continuous scoring allows fine-grained alerting
4. **Handles Variance**: Accounts for noisy vs stable metrics
5. **COALESCE Protection**: Prevents division by zero for constant metrics

### 2. Time-Series Aggregation with Enrichment
**Use Case**: Aggregate metrics over time and enrich with reference data

```esql
FROM timeseries_data
| WHERE @timestamp >= NOW() - 24 hours
| EVAL hour = DATE_TRUNC(1 hour, @timestamp)
| STATS
    total_events = COUNT(*),
    avg_response = AVG(response_time)
  BY hour, category_id
| LOOKUP JOIN categories ON category_id
| SORT hour ASC
```

### 3. Multi-Level Aggregation Pattern
**Use Case**: Calculate metrics at different granularities in a single query

```esql
FROM events
| STATS event_count = COUNT(*) BY host, service
| INLINESTATS
    total_by_host = SUM(event_count) BY host
| EVAL percentage = (event_count / total_by_host) * 100
| WHERE percentage > 10
```

## ❌ Anti-Patterns to Avoid

### Window Functions Are NOT Supported

❌ **Anti-Pattern: Attempting LAG/LEAD with OVER**
```esql
// THIS WILL NOT WORK - SYNTAX ERROR
| INLINESTATS
    prev_value = LAG(metric, 1) OVER (PARTITION BY host ORDER BY time)
    BY host
```
**Why it fails**: INLINESTATS doesn't support window functions or OVER clauses. These are SQL windowing concepts not implemented in ES|QL.

✅ **Correct Alternative**:
```esql
// Use statistical deviation instead
| INLINESTATS
    avg_metric = AVG(metric),
    stddev_metric = STD_DEV(metric)
  BY host
| EVAL z_score = (metric - avg_metric) / COALESCE(stddev_metric, 1)
| WHERE z_score > 3  // Detect significant changes
```

### Row References Are NOT Supported

❌ **Anti-Pattern: Trying to Access Previous Rows**
```esql
// THIS WILL NOT WORK - CANNOT REFERENCE OTHER ROWS
| INLINESTATS
    change = metric - metric[-1]
    BY host
```
**Why it fails**: INLINESTATS can only aggregate across rows, not reference specific row positions.

✅ **Correct Alternative**:
```esql
// Use percentage deviation from average
| INLINESTATS
    avg_metric = AVG(metric)
  BY host
| EVAL pct_deviation = ((metric - avg_metric) / avg_metric) * 100
| WHERE ABS(pct_deviation) > 50
```

### Ranking Functions Are NOT Supported

❌ **Anti-Pattern: Attempting Row Numbers or Ranking**
```esql
// THIS WILL NOT WORK - NO RANKING FUNCTIONS
| INLINESTATS
    row_num = ROW_NUMBER() OVER (ORDER BY timestamp)
    rank = RANK() OVER (PARTITION BY host ORDER BY metric DESC)
```
**Why it fails**: ES|QL has no ranking or row numbering functions.

✅ **Correct Alternative**:
```esql
// Use SORT and LIMIT for top N
| STATS max_metric = MAX(metric) BY host
| SORT max_metric DESC
| LIMIT 10
```

## 📋 Quick Reference: Invalid vs Valid Syntax

| ❌ Invalid (Will Error) | ✅ Valid Alternative | Use Case |
|------------------------|---------------------|----------|
| `LAG(value, 1) OVER(...)` | `AVG(value)` with z-score | Detect changes from baseline |
| `LEAD(value, 1) OVER(...)` | `PERCENTILE(value, 95)` | Identify future anomalies |
| `ROW_NUMBER() OVER(...)` | Use `SORT` + `LIMIT` | Get top N results |
| `RANK() OVER(...)` | Use `TOP()` aggregation | Ranking within groups |
| `SUM(value) OVER(ORDER BY...)` | `SUM(value) BY dimension` | Running totals |
| `value - LAG(value)` | Statistical deviation | Period-over-period change |

## ✅ What INLINESTATS CAN Do

### Supported Aggregation Functions
- **Statistical**: `AVG()`, `STD_DEV()`, `VARIANCE()`
- **Counting**: `COUNT()`, `COUNT_DISTINCT()`
- **Min/Max**: `MIN()`, `MAX()`
- **Percentiles**: `PERCENTILE(field, n)`, `MEDIAN()`
- **Sums**: `SUM()`

### Example: Proper INLINESTATS Usage
```esql
// THIS WORKS - PROPER AGGREGATION FUNCTIONS
| INLINESTATS
    avg_metric = AVG(metric),
    stddev_metric = STD_DEV(metric),
    p95_metric = PERCENTILE(metric, 95),
    total = SUM(metric),
    count = COUNT(*)
  BY host, region
```

## 🎯 Key Rules to Remember

### INLINESTATS = Aggregations Only
- ✅ **Can calculate**: AVG, SUM, COUNT, MIN, MAX, PERCENTILE, STD_DEV
- ❌ **Cannot do**: LAG, LEAD, OVER, PARTITION BY (in window context), ROW_NUMBER, RANK
- ❌ **Cannot reference**: Other rows, previous values, or positions

### LOOKUP JOIN = Simple Foreign Key Joins
- ✅ **Can do**: Enrich with reference data based on matching keys
- ❌ **Cannot do**: Complex join conditions, multiple join keys with OR conditions

### DATE Functions
- ✅ **Use**: `DATE_TRUNC()`, `DATE_FORMAT()`, `DATE_EXTRACT()`
- ❌ **Avoid**: Complex date arithmetic without proper functions

## 💡 Common Patterns for Real-World Use Cases

### Pattern 1: Anomaly Detection (Replace LAG/LEAD)
```esql
FROM metrics
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS current_value = AVG(cpu_usage) BY time_bucket, host
| INLINESTATS
    baseline = AVG(current_value),
    stddev = STD_DEV(current_value),
    p99 = PERCENTILE(current_value, 99)
  BY host
| EVAL
    z_score = (current_value - baseline) / COALESCE(stddev, 1),
    is_anomaly = z_score > 3 OR current_value > p99
| WHERE is_anomaly == true
```

### Pattern 2: Period-over-Period Comparison (Replace Window Functions)
```esql
FROM sales
| EVAL
    day_of_week = DATE_EXTRACT("day_of_week", @timestamp),
    hour_of_day = DATE_EXTRACT("hour", @timestamp)
| STATS current_sales = SUM(amount) BY day_of_week, hour_of_day, store_id
| INLINESTATS
    avg_for_timeslot = AVG(current_sales)
  BY day_of_week, hour_of_day
| EVAL
    pct_vs_normal = ((current_sales - avg_for_timeslot) / avg_for_timeslot) * 100
| WHERE ABS(pct_vs_normal) > 25
```

### Pattern 3: Top N with Context (Replace ROW_NUMBER)
```esql
FROM events
| STATS error_count = COUNT(*) BY service, host
| INLINESTATS total_errors = SUM(error_count)
| EVAL error_percentage = (error_count / total_errors) * 100
| WHERE error_percentage > 1
| SORT error_count DESC
| LIMIT 20
```

## 🚀 Best Practices for Query Generation

1. **Start Simple**: Begin with basic aggregations, then add complexity
2. **Test Incrementally**: Validate each stage of the query pipeline
3. **Use COALESCE**: Protect against null values and division by zero
4. **Prefer Statistics**: Use statistical methods over row-by-row comparisons
5. **Leverage BY Clauses**: Group data appropriately for meaningful insights
6. **Consider Scale**: Design queries that work with both small and large datasets

## 📚 Additional Resources

- [ES|QL Language Reference](https://www.elastic.co/guide/en/elasticsearch/reference/current/esql.html)
- [ES|QL Functions](https://www.elastic.co/guide/en/elasticsearch/reference/current/esql-functions.html)
- [ES|QL Aggregation Functions](https://www.elastic.co/guide/en/elasticsearch/reference/current/esql-agg-functions.html)

---

**Last Updated**: November 2024
**Version**: 1.0
**Maintained By**: Elastic Solutions Architecture Team