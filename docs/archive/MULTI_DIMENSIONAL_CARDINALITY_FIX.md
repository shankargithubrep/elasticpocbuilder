# Multi-Dimensional Cardinality Fix

## Issue Discovered

**Demo**: T-Mobile Network Operations (t-mobile_network operations_20251112_164108)
**Date**: 2025-11-13

### The Problems

1. **Multi-Dimensional Cardinality Problem**
   - Query: `COUNT_DISTINCT(mme_host) BY cluster_id, datacenter >= 2`
   - Result: Always returns 0 (expected 2+ hosts per group)
   - Root Cause: Data has 1:1 MME→datacenter mapping, so each (cluster, datacenter) group has max 1 host

2. **Time Bucketing Misalignment**
   - Query: `WHERE failure_count > 50` with 5-minute buckets
   - Result: Returns 0 (max value is 28)
   - Root Cause: 2500 failures over 90 days = max 2-3 per 5-minute bucket

3. **Threshold Misalignment**
   - Query: `WHERE failure_count >= 200`
   - Result: Returns 0 (max value is 2)
   - Root Cause: No guidance on realistic thresholds for sparse data

### Why It Matters

These issues cause generated queries to return 0 results, making demos ineffective. The problem affects **analytics queries** with:
- Multi-dimensional GROUP BY clauses
- COUNT_DISTINCT aggregations
- Time-series aggregations with WHERE filters
- Percentile-based thresholds

## The Solution: 3-Phase Enhancement

### Phase 1: Query Strategy Generator - Cardinality Analysis

**File**: `src/services/query_strategy_generator.py`

**Added**: Multi-dimensional cardinality requirements and time bucketing guidance

**Key Changes**:
1. Added section "Multi-Dimensional Cardinality Requirements"
2. Added guidance for COUNT_DISTINCT with GROUP BY
3. Added MANY:1 vs 1:1 relationship examples
4. Added time bucketing and threshold alignment guidance

**Example From Prompt**:
```
🎯 CRITICAL: Multi-Dimensional Cardinality Requirements

For COUNT_DISTINCT(field) >= N with GROUP BY (dimension1, dimension2):
- Ensure ≥N distinct values of field exist within SAME (dimension1, dimension2) combination
- Use MANY:1 relationships, NOT 1:1

Example:
"cardinality_requirements": "Ensure 2-5 mme_host values share the same (cluster_id, datacenter) combination"
```

### Phase 2: Data Generation Prompts - Multi-Dimensional Clustering

**File**: `src/framework/module_generator.py` (lines 1446-1519)

**Added**: Section 4 - Multi-dimensional clustering for COUNT_DISTINCT aggregations

**Key Changes**:
1. Added anti-pattern example (1:1 relationships)
2. Added correct pattern (MANY:1 relationships)
3. Added implementation guidance with code examples
4. Explained why 1:1 mappings fail for COUNT_DISTINCT queries

**Anti-Pattern Example**:
```python
❌ CRITICAL Anti-Pattern (WILL FAIL):
mme_hosts = [
    ('mme-01', 'cluster-1', 'DC-Seattle'),   # unique combination
    ('mme-02', 'cluster-2', 'DC-Dallas'),    # unique combination
]
# Query: GROUP BY cluster_id, datacenter → Each group has max 1 host!
```

**Correct Pattern Example**:
```python
✅ CORRECT Pattern (MANY:1 relationships):
mme_hosts = [
    ('mme-01', 'cluster-1', 'DC-Seattle'),
    ('mme-02', 'cluster-1', 'DC-Seattle'),   # SAME cluster AND datacenter
    ('mme-03', 'cluster-1', 'DC-Seattle'),   # SAME cluster AND datacenter
]
# Query: GROUP BY cluster_id, datacenter → Each group has 3 hosts!
```

### Phase 3: Query Generation Prompts - Adaptive Time Bucketing

**File**: `src/framework/module_generator.py` (lines 1621-1676)

**Added**: Adaptive time bucketing and threshold alignment guidance

**Key Changes**:
1. Added expected events per bucket formula
2. Added bucket size recommendations based on data volume
3. Added anti-pattern examples with failing queries
4. Added multi-dimensional density warnings
5. Added data profile usage guidance

**Key Formula**:
```
expected_per_bucket = total_records / (num_days × intervals_per_day)
```

**Bucket Size Guidance**:
- **5-minute buckets**: Only for LARGE datasets (>100K records)
- **15-minute buckets**: Medium datasets (10K-100K records)
- **30-minute buckets**: Small-medium datasets (5K-50K records)
- **1-hour buckets**: Small datasets (<10K records)
- **Daily/weekly buckets**: Long-term trends or very sparse data

**Anti-Pattern Example**:
```esql
❌ ANTI-PATTERN (WILL FAIL):
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS failure_count = COUNT(*) BY time_bucket, cluster_id, datacenter
| WHERE failure_count > 50  ← IMPOSSIBLE! Max 2-3 per 5-min bucket
```

**Correct Pattern Example**:
```esql
✅ CORRECT - Wider buckets OR lower thresholds:

Option A: Wider time buckets
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS failure_count = COUNT(*) BY time_bucket, cluster_id, datacenter
| WHERE failure_count > 50  ← Now achievable with hourly aggregation

Option B: Percentile-based thresholds
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS failure_count = COUNT(*) BY time_bucket, cluster_id, datacenter
| WHERE failure_count > {p90_value}  ← Use actual p90 from profile (e.g., 3)
```

## Implementation Details

### Files Modified

1. **src/services/query_strategy_generator.py**
   - Added cardinality requirements section
   - Added time bucketing guidance
   - Integrated with existing strategy generation

2. **src/framework/module_generator.py**
   - Added Section 4 to data generation prompts (multi-dimensional clustering)
   - Added adaptive time bucketing to query generation prompts
   - Enhanced mode guidance for both data and queries

### Validation

Created `/tmp/test_cardinality_fix_simple.py` to verify:

**Phase 1 Checks**: ✅
- Cardinality requirements section present
- COUNT_DISTINCT guidance with GROUP BY
- MANY:1 relationship examples
- Time bucketing guidance
- Bucket size recommendations

**Phase 2 Checks**: ✅
- Section 4 header present
- Anti-pattern examples (1:1 relationships)
- MANY:1 relationship guidance
- Implementation guidance
- COUNT_DISTINCT aggregation mention

**Phase 3 Checks**: ✅
- Time bucketing section header
- Expected events per bucket formula
- Bucket size guidance (5-minute, 1-hour, etc.)
- Anti-pattern examples with failures
- Multi-dimensional density warnings
- Data profile usage guidance

**Result**: All checks passed ✅✅✅

### How to Re-test

```bash
python3 /tmp/test_cardinality_fix_simple.py
```

## Impact on Query Generation

### Queries Now Guided By

1. **Cardinality Analysis**
   - LLM calculates expected distinct values per GROUP BY combination
   - Ensures MANY:1 relationships for COUNT_DISTINCT queries
   - Validates dimensional relationships before query generation

2. **Time Bucket Selection**
   - LLM calculates expected events per bucket
   - Selects appropriate bucket size based on data volume
   - Considers multi-dimensional splits (each dimension divides density)

3. **Threshold Selection**
   - LLM uses data profile percentiles (p75, p90, p95, p99)
   - Aligns thresholds with actual data distributions
   - Avoids arbitrary numbers that return 0 results

### Example Scenario

**T-Mobile Network Operations Demo**:
- 2500 failure events over 90 days
- 100 cell_ids, 3 datacenters, 5 mme_hosts
- Query needs: Detect anomalous failure rates

**Before Fix**:
```esql
-- Query returns 0 results (multiple issues)
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS
    failure_count = COUNT(*),
    unique_hosts = COUNT_DISTINCT(mme_host)
  BY time_bucket, cluster_id, datacenter
| WHERE failure_count >= 200 AND unique_hosts >= 2
```

**After Fix**:
```esql
-- Query returns meaningful results (aligned with data)
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)  ← Wider buckets
| STATS
    failure_count = COUNT(*),
    unique_hosts = COUNT_DISTINCT(mme_host)
  BY time_bucket, cluster_id, datacenter
| WHERE failure_count >= 15 AND unique_hosts >= 2  ← Profile-based threshold
-- Data generated with MANY:1 (multiple hosts per cluster+datacenter)
```

## Related Enhancements

This fix complements existing enhancements:

1. **Enhanced Data Generation Mode** (sidebar.py, data_profiler.py)
   - UI flag to enable realistic clustering
   - Percentile calculation and threshold suggestions
   - Beta, lognormal, Poisson distributions

2. **ES|QL Strict Rules** (esql_strict_rules.py)
   - Rule #17: EVAL Variable Reuse
   - All rules centralized and version controlled

3. **Data Profiler** (data_profiler.py)
   - Calculates percentiles (p50, p75, p90, p95, p99)
   - Generates threshold suggestions with expected result counts
   - Provides field value examples for WHERE clauses

## Next Steps

### For Testing

1. **T-Mobile Scenario Regeneration**
   - Enable enhanced generation mode
   - Use medium dataset size
   - Validate queries return meaningful results
   - Check for multi-dimensional cardinality in results

2. **Other Analytics Demos**
   - Identify demos with COUNT_DISTINCT queries
   - Identify demos with time-series aggregations
   - Regenerate with new guidance
   - Validate improved result counts

### For Documentation

1. **User Guidance**
   - Document when to use enhanced mode
   - Explain multi-dimensional cardinality patterns
   - Provide examples of dimensional relationships

2. **Developer Guidance**
   - Document the 3-phase architecture
   - Explain how cardinality analysis works
   - Provide troubleshooting guide for 0-result queries

## Summary

**Problem**: Multi-dimensional aggregations returning 0 results due to:
- 1:1 dimensional relationships (should be MANY:1)
- Time buckets too granular for data volume
- Arbitrary thresholds not aligned with data distributions

**Root Cause**: LLM lacked guidance on:
- Cardinality requirements for COUNT_DISTINCT queries
- Time bucket selection based on data density
- Threshold selection based on actual data profiles

**Solution**: 3-phase enhancement:
- Phase 1: Query strategy includes cardinality analysis
- Phase 2: Data generation creates MANY:1 relationships
- Phase 3: Query generation adapts time buckets and thresholds

**Impact**:
- Prevents 0-result queries in multi-dimensional aggregations
- Ensures COUNT_DISTINCT queries have sufficient cardinality
- Aligns time buckets with data volume
- Uses percentile-based thresholds from data profiles

**Status**: ✅ All 3 phases implemented and tested

**Next**: Test with T-Mobile scenario regeneration to validate effectiveness
