# Data-Query Alignment Strategy

## Problem Statement
Generated queries return 0 results because data generation creates sparse distributions when aggregated by time buckets and high-cardinality dimensions, while queries use unrealistic thresholds.

## Root Causes

### 1. Sparse Data Distribution
- **Total events too low**: 2500 failures over 90 days across 100 cells
- **High cardinality splits**: When grouped by (5min bucket × 100 cells), each bucket gets ~1-2 events
- **Random distribution**: Events spread evenly instead of realistic clustering

### 2. Unrealistic Query Thresholds
- Queries expect hundreds of failures per bucket
- WHERE clauses filter for counts that can't exist in the data
- Z-score calculations meaningless with such low variance

## Solution Strategy

### Phase 1: Intelligent Data Generation

#### 1.1 Event Clustering Strategy
Instead of random distribution, create realistic patterns:

```python
def generate_failure_events(self):
    """Generate failures with realistic clustering patterns"""

    # Create "incident periods" - times when failures spike
    incident_periods = self.generate_incident_periods(
        num_incidents=10,  # Major incidents over 90 days
        duration_hours=[1, 4, 12, 24],  # Various incident durations
        severity=['minor', 'major', 'critical']
    )

    # Generate baseline failures (steady state)
    baseline_failures = self.generate_baseline_traffic(
        rate_per_hour=5,  # Low steady-state failure rate
        cells=all_cells
    )

    # Generate incident failures (spikes)
    incident_failures = []
    for incident in incident_periods:
        if incident.severity == 'critical':
            # Critical: Affects multiple cells in a region
            affected_cells = self.get_region_cells(incident.region)
            failure_rate = 500  # per hour
        elif incident.severity == 'major':
            # Major: Affects specific cell tower and neighbors
            affected_cells = [incident.primary_cell] + incident.neighbor_cells[:3]
            failure_rate = 200  # per hour
        else:
            # Minor: Single cell affected
            affected_cells = [incident.primary_cell]
            failure_rate = 50  # per hour

        incident_failures.extend(
            self.generate_clustered_failures(
                cells=affected_cells,
                start_time=incident.start,
                duration=incident.duration,
                rate_per_hour=failure_rate
            )
        )
```

#### 1.2 Correlated Failure Generation
Create realistic correlations between dimensions:

```python
def generate_correlated_failures(self):
    """Generate failures with realistic correlations"""

    # MME overload cascades to multiple cells
    if failure_type == 'mme_overload':
        mme_host = self.pick_overloaded_mme()
        # All cells served by this MME see failures
        affected_cells = self.get_mme_cells(mme_host)

    # Cell handoff failures affect neighbor cells
    elif failure_type == 'handoff_cascade':
        primary_cell = self.pick_problem_cell()
        # Neighbors see correlated failures
        affected_cells = self.get_neighbor_cells(primary_cell)

    # Roaming surge affects specific MMEs
    elif failure_type == 'roaming_surge':
        # Border region MMEs see IMSI influx
        affected_mmes = self.get_border_mmes()
        imsi_multiplier = 10  # More unique IMSIs
```

#### 1.3 Scale Configuration
Add scale parameters to control data density:

```python
class DataGeneratorModule:
    def __init__(self, config):
        # Extract scale from config
        self.scale_factor = config.get('scale_factor', 1.0)

        # Adjust counts based on scale
        self.n_failures = int(2500 * self.scale_factor)
        self.n_auth_events = int(3000 * self.scale_factor)
        self.incident_frequency = max(1, int(10 * self.scale_factor))
```

### Phase 2: Query Validation & Adjustment

#### 2.1 Data-Aware Threshold Calculation
Calculate realistic thresholds based on actual data:

```python
def calculate_realistic_thresholds(self, datasets, aggregation_config):
    """Calculate thresholds that will actually return results"""

    # Simulate the aggregation
    df = datasets[aggregation_config['table']]
    time_bucket = aggregation_config['time_bucket']  # e.g., '5 minutes'
    group_by = aggregation_config['group_by']  # e.g., ['cell_id']

    # Group and calculate statistics
    grouped = df.set_index('@timestamp').resample(time_bucket).groupby(group_by).count()

    # Use percentiles for realistic thresholds
    thresholds = {
        'high': grouped.quantile(0.95),  # Top 5% of buckets
        'medium': grouped.quantile(0.75),  # Top 25%
        'low': grouped.quantile(0.50)  # Median
    }

    return thresholds
```

#### 2.2 Query Generation with Validation
Validate queries return results before finalizing:

```python
def generate_validated_query(self, query_template, datasets):
    """Generate query and validate it returns results"""

    # Generate initial query
    query = self.fill_template(query_template, initial_thresholds)

    # Test query on sample data
    result_count = self.simulate_query(query, datasets)

    # Adjust thresholds if no results
    if result_count == 0:
        # Progressively lower thresholds
        for threshold_multiplier in [0.5, 0.25, 0.1, 0.05]:
            adjusted_query = self.adjust_thresholds(query, threshold_multiplier)
            result_count = self.simulate_query(adjusted_query, datasets)
            if result_count > 0:
                break

    return adjusted_query
```

#### 2.3 Dynamic WHERE Clause Generation
Generate WHERE clauses based on data distribution:

```python
def generate_where_clause(self, stats):
    """Generate WHERE clause that matches data distribution"""

    if stats['max'] < 10:
        # Very sparse data - use low thresholds
        return f"WHERE failure_count >= {max(1, stats['p75'])}"
    elif stats['max'] < 100:
        # Moderate density - use percentile-based
        return f"WHERE failure_count >= {stats['p90']}"
    else:
        # Dense data - can use higher thresholds
        return f"WHERE failure_count >= {stats['p95']}"
```

### Phase 3: Framework Integration

#### 3.1 Update ModuleGenerator Prompts
Include data distribution awareness in LLM prompts:

```python
QUERY_GENERATOR_PROMPT = """
Generate ES|QL queries for the demo. CRITICAL requirements:

1. ANALYZE the data scale first:
   - Total records: {total_records}
   - Time range: {time_range_days} days
   - Cardinality: {unique_cells} cells, {unique_mmes} MMEs

2. CALCULATE realistic thresholds:
   - For {total_records} records over {time_range_days} days
   - Split by {unique_cells} dimensions
   - Maximum events per bucket ≈ {estimated_max_per_bucket}

3. USE adaptive thresholds:
   - If max_per_bucket < 10: Use thresholds like >= 2
   - If max_per_bucket < 100: Use thresholds like >= 10
   - If max_per_bucket < 1000: Use thresholds like >= 50

4. PREFER percentile-based filtering:
   - Instead of: WHERE count > 1000
   - Use: WHERE count > PERCENTILE(count, 95)
"""
```

#### 3.2 Add Query Testing to Orchestrator
Test queries during generation:

```python
class ModularDemoOrchestrator:
    def generate_demo(self, config):
        # ... existing code ...

        # Generate queries
        query_gen = loader.load_query_generator(datasets)
        queries = query_gen.generate_queries()

        # Validate queries return results
        for query in queries:
            if query['query_type'] == 'scripted':
                # Simulate query execution
                results = self.simulate_esql_query(query['query'], datasets)
                if len(results) == 0:
                    logger.warning(f"Query '{query['name']}' returns 0 results")
                    # Attempt to fix
                    query['query'] = self.auto_adjust_query(query['query'], datasets)
```

### Phase 4: Immediate Fixes

For the existing T-Mobile demo, apply these quick fixes:

```python
# Quick fix for query_generator.py
def generate_queries(self):
    queries = []

    # Adjusted Query 1: Lower thresholds
    queries.append({
        'query': '''FROM mme_signaling_failures
| EVAL time_bucket = DATE_TRUNC(30 minutes, @timestamp)  # Wider buckets
| STATS
    failure_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi)
  BY time_bucket, current_cell_id
| WHERE failure_count >= 2  # Realistic threshold
| LOOKUP JOIN cell_tower_reference ON current_cell_id == cell_id
| KEEP current_cell_id, failure_count, time_bucket, cell_name
| SORT failure_count DESC
| LIMIT 50'''
    })
```

## Implementation Priority

1. **Immediate**: Fix existing demos with adjusted thresholds
2. **Short-term**: Add data clustering to data generation
3. **Medium-term**: Implement query validation in orchestrator
4. **Long-term**: Full framework update with adaptive generation

## Success Metrics

- **Query Success Rate**: >95% of generated queries return results
- **Result Quality**: Queries return 5-50 results (not 0, not thousands)
- **Realistic Patterns**: Data shows believable incident clusters
- **Performance**: Query execution time <5 seconds