# JOIN Compatibility Problem Analysis

## Problem Summary

The current ES|QL query generation has a critical flaw: queries reference fields from datasets that haven't been joined, or join to incorrect lookup tables based on incompatible foreign keys.

## Example from Spotify Demo (spotify_data_science_20251024_141727)

### Query 7: Real-Time A/B Test Impact Analysis

**Problematic Query:**
```esql
FROM podcast_listening_events
| WHERE timestamp > NOW() - 24 hours
| LOOKUP JOIN listener_profiles_lookup ON show_id  -- ❌ WRONG: listener_profiles has listener_id, not show_id
| STATS
    total_listeners = COUNT_DISTINCT(listener_id),
    total_plays = COUNT(*),
    avg_completion = AVG(completion_rate),
    unique_shows = COUNT_DISTINCT(show_id)
  BY ab_test_variant, genre  -- ❌ WRONG: 'genre' field not available after this JOIN
```

### Data Structure

```
Dataset: podcast_listening_events (timeseries)
Fields: event_id, timestamp, listener_id, show_id, episode_duration_sec,
        listen_duration_sec, completion_rate, skip_count, rewind_count,
        playback_speed, is_relisten, device_type, listening_behavior

Dataset: listener_profiles (lookup)
Fields: listener_id, subscription_tier, region, country, account_age_days,
        avg_weekly_hours, engagement_segment, primary_genre_id, shows_followed,
        churn_risk_score, listener_profile
Foreign Key: listener_id

Dataset: podcast_shows (lookup)
Fields: show_id, show_name, genre_id, show_age_days, total_episodes,
        avg_episode_length_min, monthly_listeners, avg_completion_rate,
        growth_trend, mom_growth_pct, binge_score, show_description
Foreign Key: show_id

Dataset: podcast_genres (lookup)
Fields: genre_id, genre_name, parent_category, top_region,
        regional_growth_rate, total_shows_in_genre, avg_engagement_score,
        trending_status
Foreign Key: genre_id
```

### Relationship Graph

```
podcast_listening_events
├─ listener_id → listener_profiles.listener_id
└─ show_id → podcast_shows.show_id
                └─ genre_id → podcast_genres.genre_id
```

## Root Causes

### 1. JOIN Key Mismatch
**Problem:** Joining to a lookup table using a foreign key that doesn't exist in that table.

**Example:**
- `LOOKUP JOIN listener_profiles_lookup ON show_id`
- But `listener_profiles` only has `listener_id` as its foreign key
- The timeseries has both `listener_id` AND `show_id`, so the JOIN key must match one of the lookup table's keys

### 2. Field Availability After JOIN
**Problem:** Using fields that aren't available after the JOIN operation.

**Example:**
- After joining `listener_profiles_lookup`, we get fields from listener_profiles
- But the query tries to group `BY genre`, which is in `podcast_shows` (not joined)
- To access `genre`, we need to join `podcast_shows_lookup ON show_id`

### 3. Missing Multi-Hop JOIN Logic
**Problem:** Accessing fields that require multiple JOINs through intermediate tables.

**Example:**
- To get `genre_name`, we need:
  1. `JOIN podcast_shows_lookup ON show_id` → gets `genre_id`
  2. `JOIN podcast_genres_lookup ON genre_id` → gets `genre_name`
- Current implementation doesn't understand these multi-hop relationships

### 4. Field Name Variations Not Caught
**Problem:** Field validation doesn't catch when a similar field exists in a different dataset.

**Example:**
- Query uses `completion_rate` (exists in timeseries)
- But also references `avg_completion_rate` (exists in podcast_shows lookup)
- Validator should detect this and suggest correct JOIN

## Impact

1. **Invalid ES|QL Queries:** Queries that fail syntax validation or execution
2. **Missing Data:** Queries that execute but return incomplete results
3. **Incorrect JOINs:** Performance issues from unnecessary JOINs
4. **Poor Demo Quality:** Demos that don't showcase Elastic's capabilities properly

## Required Fixes

### 1. Relationship Graph Analysis
Build a graph of dataset relationships to understand:
- Which datasets can be joined from the timeseries
- What foreign keys are available
- Which fields become available after each JOIN
- Multi-hop paths to reach distant datasets

### 2. Enhanced JOIN Validation
Validate that:
- JOIN key exists in both source and target datasets
- JOIN key types are compatible
- All referenced fields are available after JOINs
- Multi-hop JOINs are in correct order

### 3. Improved LLM Prompt Engineering
Provide the LLM with:
- Explicit relationship graph
- Foreign key constraints
- Field availability rules
- Multi-hop JOIN examples
- JOIN order requirements

### 4. Post-Generation Validation and Auto-Correction
After generating queries:
- Parse ESQL to extract JOINs and field references
- Verify field availability at each step
- Detect missing JOINs needed for referenced fields
- Auto-correct JOIN keys and add missing JOINs
- Suggest alternative query structures if needed

## Correct Query Example

**What the query SHOULD be:**
```esql
FROM podcast_listening_events
| WHERE timestamp > NOW() - 24 hours
| WHERE ab_test_variant == "variant_a" OR ab_test_variant == "control"
| LOOKUP JOIN podcast_shows_lookup ON show_id  -- ✓ CORRECT: Join to get genre_id
| LOOKUP JOIN podcast_genres_lookup ON genre_id  -- ✓ CORRECT: Join to get genre_name
| STATS
    total_listeners = COUNT_DISTINCT(listener_id),
    total_plays = COUNT(*),
    completed_plays = SUM(CASE(completion_rate >= 90, 1, 0)),
    avg_completion = AVG(completion_rate),
    unique_shows = COUNT_DISTINCT(show_id)
  BY ab_test_variant, genre_name  -- ✓ CORRECT: genre_name now available
| EVAL completion_rate_pct = ROUND(completed_plays / GREATEST(total_plays, 1) * 100, 1)
| SORT ab_test_variant ASC, total_listeners DESC
```

## Implementation Priority

1. **High Priority:**
   - Relationship graph builder (reads `get_relationships()` from data_generator)
   - JOIN key validation
   - Field availability checker

2. **Medium Priority:**
   - Multi-hop JOIN path detection
   - Auto-correction for incorrect JOINs
   - Enhanced LLM prompt with relationship context

3. **Nice to Have:**
   - Query optimizer (remove redundant JOINs)
   - Performance hints (JOIN order optimization)
   - Visual relationship diagram in UI

## Next Steps

1. Create `RelationshipGraphAnalyzer` class
2. Extend `QueryValidator` to check JOIN compatibility
3. Update `module_generator.py` prompt with relationship context
4. Add post-generation validation loop
5. Test with Spotify and Netflix demos
6. Document best practices for query generation

## Related Files

- `/Users/jesse.miller/demo-builder/src/framework/query_validator.py` - Current validator
- `/Users/jesse.miller/demo-builder/src/framework/module_generator.py` - LLM prompt generation
- `/Users/jesse.miller/demo-builder/src/framework/base.py` - DataGeneratorModule.get_relationships()
- `/Users/jesse.miller/demo-builder/demos/spotify_data_science_20251024_141727/` - Example with issues

## References

- ES|QL LOOKUP JOIN documentation: https://www.elastic.co/guide/en/elasticsearch/reference/current/esql-commands.html#esql-lookup-join
- JOIN ordering best practices
- Foreign key constraint patterns
