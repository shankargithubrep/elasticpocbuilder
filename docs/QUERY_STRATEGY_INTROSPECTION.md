# Query Strategy Introspection & Validation

## Overview

Every generated demo includes a `query_strategy.json` file that captures the **planned** query strategy BEFORE data and query generation occurs. This is invaluable for:

1. **Debugging** - See what was planned vs. what was generated
2. **Triaging** - Identify if bugs came from bad strategy or bad execution
3. **Validation** - Check for anti-patterns early in the process

## File Location

```
demos/<demo_module_name>/
├── query_strategy.json  ← Generated FIRST (Phase 1)
├── data_generator.py    ← Generated SECOND (Phase 2)
├── query_generator.py   ← Generated LAST (Phase 6)
└── ...
```

**Timeline:**
- ⏱️ **Phase 1 (Strategy)**: Create `query_strategy.json`
- ⏱️ **Phase 2 (Data Module)**: Use strategy to generate `data_generator.py`
- ⏱️ **Phase 3-5 (Indexing & Profiling)**: Execute data generation, index, profile
- ⏱️ **Phase 6 (Query Module)**: Use strategy + profiled data to generate `query_generator.py`

## Structure

### Datasets Section

```json
{
  "datasets": [
    {
      "name": "mme_signaling_events",
      "type": "timeseries",
      "index_mode": "data_stream",
      "row_count": "150000",
      "description": "MME signaling events including attach procedures...",
      "required_fields": {
        "@timestamp": "date",
        "event_id": "keyword",
        "mme_host": "keyword",
        "procedure_type": "keyword",
        ...
      },
      "relationships": ["mme_hosts", "cells"],
      "semantic_fields": [],
      "cardinality_notes": "Multiple mme_host values (2-5) share the same (cluster_id, datacenter) combination..."
    }
  ]
}
```

**Key Fields:**
- `name`: Dataset identifier
- `type`: "timeseries" or "reference"
- `index_mode`: "data_stream" or "lookup"
- `required_fields`: Exact field names and types planned
- `relationships`: Which other datasets this joins to
- `cardinality_notes`: Special data distribution requirements

### Queries Section

```json
{
  "queries": [
    {
      "name": "Core Network Split-Brain Detection",
      "pain_point": "Split-brain conditions where multiple MMEs...",
      "esql_features": ["LOOKUP JOIN", "STATS", "INLINESTATS", "EVAL"],
      "required_datasets": ["mme_signaling_events", "mme_hosts"],
      "required_fields": {
        "mme_signaling_events": ["@timestamp", "mme_host", "cluster_id", ...],
        "mme_hosts": ["mme_host", "cluster_id", "datacenter", ...]
      },
      "join_chain": ["mme_signaling_events -> mme_hosts"],
      "description": "Detects split-brain scenarios by analyzing duplicate...",
      "complexity": "complex"
    }
  ]
}
```

**Key Fields:**
- `name`: Query name
- `pain_point`: Which customer pain point this addresses
- `esql_features`: Which ES|QL commands will be used
- `required_datasets`: Which datasets are needed
- `required_fields`: Exact fields needed from each dataset
- `join_chain`: How datasets relate (for LOOKUP JOIN)

### Relationships Section

```json
{
  "relationships": [
    {
      "source": "mme_signaling_events",
      "join_key": "mme_host",
      "target": "mme_hosts",
      "type": "many_to_one"
    }
  ]
}
```

## Using for Debugging

### Scenario 1: "Generated query doesn't work"

**Steps:**
1. Open `query_strategy.json`
2. Find the query by name in the `queries` array
3. Check `required_fields` - Are these the fields you expected?
4. Check `esql_features` - Are the right commands planned?
5. Compare `required_fields` to actual fields in `data_generator.py`
6. Check if `query_generator.py` uses the same field names

**Example:**
```bash
# Check if strategy field names match generated data
grep "mme_host" query_strategy.json
grep "mme_host" data_generator.py
grep "mme_host" query_generator.py
```

### Scenario 2: "@timestamp parameterization bug"

**Steps:**
1. Open `query_strategy.json`
2. Search for queries using `@timestamp` in `required_fields`
3. Check if `description` or `pain_point` mentions "date range", "start_date", "end_date"
4. **RED FLAG**: If a query plans to use @timestamp AND mentions date parameters → Anti-pattern likely!

**Example Detection:**
```json
{
  "required_fields": {
    "events": ["@timestamp", "status", ...]  // Uses @timestamp
  },
  "description": "Analyzes events within specified date range..."  // ❌ Mentions "date range"!
}
```

This indicates the strategy PLANNED to parameterize @timestamp, which means the query generator will likely generate the anti-pattern.

### Scenario 3: "Array length mismatch error"

**Steps:**
1. Check the error message for dataset name (e.g., `hss_nodes`)
2. Open `query_strategy.json`
3. Find that dataset in the `datasets` array
4. Check `row_count` - Is it a reasonable number?
5. Check `cardinality_notes` - Does it describe special requirements?
6. Open `data_generator.py` and find where that dataset is created
7. Compare planned fields vs generated fields

**Example:**
```json
// In strategy
{
  "name": "hss_nodes",
  "row_count": "10",
  "required_fields": {
    "node_id": "keyword",
    "datacenter": "keyword",
    "role": "keyword"
  }
}

// Then check data_generator.py for:
// hss_nodes = [...list of 6 items...]  ❌ Only 6, but strategy says 10!
```

### Scenario 4: "Query uses wrong fields"

**Root Cause Analysis:**
1. Check `query_strategy.json` for planned field names
2. Check `data_generator.py` for actual generated field names
3. Check `query_generator.py` for field names used in queries

**Mismatch Types:**
- **Strategy vs Data**: Strategy planned `mme_host`, data generated `mme_hostname`
- **Data vs Query**: Data has `procedure_type`, query uses `procedure_name`

## Anti-Pattern Validation

### Automated Checks (Added in This Update)

The `validate_strategy()` function now checks for:

#### 1. @timestamp Parameterization Hints

**Detection Logic:**
- Query uses `@timestamp` in `required_fields`
- AND description/pain_point mentions: `start_date`, `end_date`, `date range`, `time range parameter`, `parameterized time`, `user-specified date`

**Warning Output:**
```
🚨 QUERY STRATEGY VALIDATION WARNINGS:
  ⚠️ Query 'Revenue Impact Analysis' may parameterize @timestamp (mentions: start_date, end_date).
     Remember: @timestamp should NEVER be parameterized - use NOW() instead!
```

**Action:** Review the query plan and ensure downstream generation won't create `?start_date` / `?end_date` parameters.

#### 2. Reference Dataset Usage

**Detection Logic:**
- Query uses reference datasets
- Logs debug reminder about array length requirements

**Why:** Reference datasets (lookup tables) are often sliced incorrectly in data generation.

### Manual Review Checklist

Before generation proceeds, manually review `query_strategy.json`:

- [ ] **Field Names**: Are they realistic and consistent? (e.g., `mobile.procedure.type` not `procedure`)
- [ ] **Row Counts**: Are they reasonable for the dataset size preference?
- [ ] **Cardinality**: Do queries expecting multi-dimensional cardinality have appropriate `cardinality_notes`?
- [ ] **Relationships**: Are join keys present in both source and target datasets?
- [ ] **@timestamp Usage**: If used, is it for relative time filtering (NOW()) not parameters?

## Future Enhancements

### Possible Additions

1. **Pre-Generation Review Step**
   - After strategy generation, pause and show user the plan
   - User can approve/reject/modify before proceeding
   - Useful for expensive generation runs

2. **Strategy Diff Tool**
   - Compare `query_strategy.json` between different demo versions
   - Identify why one version worked and another didn't

3. **Strategy Templates**
   - Save working strategies as templates
   - Reuse proven patterns for similar use cases

4. **Automated Strategy Fixes**
   - Detect anti-patterns
   - Automatically rewrite strategy to fix them
   - Re-generate without LLM call

5. **Strategy Scoring**
   - Rate strategy quality before execution
   - Predict likelihood of success based on patterns

## Examples from T-Mobile Demo

### Good Strategy Example

```json
{
  "name": "MME Resource Exhaustion Prediction",
  "required_fields": {
    "mme_signaling_events": [
      "@timestamp",
      "mme_host",
      "procedure_latency_ms",
      "procedure_result"
    ]
  },
  "esql_features": ["STATS", "INLINESTATS", "EVAL", "WHERE"],
  "description": "Detects MME resource exhaustion by calculating z-scores for latency..."
}
```

**✅ Good because:**
- Uses `@timestamp` for time-series analysis (not parameters)
- Field names are specific and realistic
- ES|QL features are appropriate for the use case
- No hints of date parameterization

### Bad Strategy Example (Hypothetical)

```json
{
  "name": "Session Analysis by Date Range",
  "required_fields": {
    "sessions": [
      "@timestamp",
      "session_id",
      "status"
    ]
  },
  "description": "Analyzes sessions within user-specified start and end dates..."
}
```

**❌ Bad because:**
- Mentions "user-specified start and end dates" with `@timestamp` usage
- Will likely generate `?start_date` and `?end_date` parameters
- Should use `NOW() - X days` instead

## Best Practices

1. **Always Check the Strategy First** when debugging query issues
2. **Compare Strategy → Data → Queries** for field name consistency
3. **Look for Warning Signs** early (date range mentions, parameterization hints)
4. **Save Working Strategies** for reuse in similar demos
5. **Treat Strategy as Source of Truth** for what SHOULD have been generated

## Related Files

- `src/services/query_strategy_generator.py` - Generates analytics strategies
- `src/services/search_strategy_generator.py` - Generates search/RAG strategies
- `src/framework/orchestrator.py` - Saves `query_strategy.json` at line 256
- `src/framework/module_generator.py` - Uses strategy to generate modules

---

**Last Updated**: 2024-11-14
**Feature**: Query strategy introspection and validation
**Purpose**: Enable early detection of anti-patterns and easier debugging
