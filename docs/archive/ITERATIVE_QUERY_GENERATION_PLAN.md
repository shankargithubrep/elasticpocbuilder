# Iterative Query Generation with LLM Testing

## Philosophy

Instead of preventing errors with rigid schemas, we **embrace the LLM's debugging ability** by letting it test queries against real data and iterate based on actual error messages.

## Core Concept

```
Generate → Test → Fix → Repeat
```

The LLM generates queries, tests them against indexed data, sees any errors, and fixes them. This natural feedback loop plays to LLM strengths.

## Implementation Phases

### Phase 1: Lightweight Field Discovery (Immediate Fix)

**Problem**: Query generator doesn't know actual field names
**Solution**: Pass DataFrame columns directly to query generator

```python
# In module_loader.py
def load_query_generator(self, datasets: Dict[str, pd.DataFrame]) -> QueryGeneratorModule:
    """Load query generator with dataset information"""

    # Extract field information from actual DataFrames
    field_info = {}
    for name, df in datasets.items():
        field_info[name] = {
            'columns': list(df.columns),
            'dtypes': {col: str(df[col].dtype) for col in df.columns},
            'sample': df.head(2).to_dict()  # Include sample data
        }

    # Pass to query generator
    module = self._import_module('query_generator')
    generator = module.QueryGenerator(self.config)
    generator.datasets = datasets
    generator.field_info = field_info  # NEW: Actual field information

    return generator
```

**In generated query_generator.py:**
```python
def generate_queries(self):
    # Access actual field names
    for dataset_name, info in self.field_info.items():
        print(f"Dataset {dataset_name} has fields: {info['columns']}")

    # Use actual field names instead of guessing
    timeseries_fields = self.field_info['listening_events']['columns']
    if 'listen_duration_min' in timeseries_fields:  # Actual field name!
        duration_field = 'listen_duration_min'
```

### Phase 2: Query Testing Integration

**Add testing capability to module generator:**

```python
# In module_generator.py
def _generate_and_test_queries(self, config, datasets):
    """Generate queries and test them against real data"""

    # 1. Index sample data to temporary index
    test_index = f"test_{config['company']}_{int(time.time())}"
    self._index_test_data(datasets, test_index)

    # 2. Generate initial queries
    queries = self._generate_initial_queries(config, datasets)

    # 3. Test each query
    tested_queries = []
    for query in queries:
        test_result = self._test_query(query['esql'], test_index)

        if test_result['success']:
            tested_queries.append(query)
        else:
            # 4. Use LLM to fix failed query
            fixed_query = self._fix_query_with_llm(
                query=query,
                error=test_result['error'],
                field_info=self._get_field_info(datasets),
                test_index=test_index
            )
            tested_queries.append(fixed_query)

    # 5. Clean up test index
    self._delete_test_index(test_index)

    return tested_queries
```

### Phase 3: LLM-Driven Query Fixing

```python
def _fix_query_with_llm(self, query, error, field_info, test_index):
    """Use LLM to fix a failed query based on actual error"""

    fix_prompt = f"""
    The following ES|QL query failed:

    Query: {query['esql']}

    Error: {error}

    Available fields in index '{test_index}':
    {json.dumps(field_info, indent=2)}

    Common fixes:
    - Field name mismatches (use exact field names from above)
    - Division by zero (use COALESCE or conditional logic)
    - JOIN order issues (largest dataset first)
    - Syntax errors (check ES|QL documentation)

    Please provide a fixed version of the query that will work with the actual data.
    Return ONLY the corrected ES|QL query, no explanation.
    """

    response = self.llm_client.generate(fix_prompt)
    query['esql'] = response.strip()
    query['was_fixed'] = True
    query['original_error'] = error

    # Test the fixed query
    retry_result = self._test_query(query['esql'], test_index)
    if not retry_result['success']:
        # Log but continue - at least we tried
        query['fix_failed'] = True
        query['retry_error'] = retry_result['error']

    return query
```

### Phase 4: Progressive Enhancement

Once basic test-and-fix works, enhance with:

1. **Multi-round iteration**: Keep fixing until it works (max 3 attempts)
2. **Learning from patterns**: Track common fixes and apply preemptively
3. **Performance feedback**: Show query execution time, optimize slow queries
4. **Result validation**: Check if results make business sense

```python
def _iterate_until_working(self, query, test_index, max_attempts=3):
    """Keep trying to fix query until it works"""

    for attempt in range(max_attempts):
        result = self._test_query(query['esql'], test_index)

        if result['success']:
            # Also check if results are reasonable
            if self._validate_results(result['data']):
                return query
            else:
                query = self._improve_query(query, result['data'])
        else:
            query = self._fix_query_with_llm(query, result['error'])

    return query  # Return best effort
```

## Benefits Over Rigid Schema

| Aspect | Rigid Schema | Iterative Testing |
|--------|--------------|-------------------|
| Field name accuracy | Requires perfect prediction | Self-corrects from errors |
| Flexibility | Constrained by schema | Natural LLM creativity |
| Error handling | Tries to prevent all errors | Fixes errors as they occur |
| Maintenance | Schema must be updated | Self-adapting |
| LLM usage | Fighting against LLM nature | Playing to LLM strengths |

## Implementation Timeline

1. **Hour 1**: Add field discovery (Phase 1) ✅ Immediate fix
2. **Hour 2-3**: Add query testing capability (Phase 2)
3. **Hour 4-5**: Add LLM fixing logic (Phase 3)
4. **Hour 6+**: Progressive enhancements (Phase 4)

## Success Metrics

- ✅ 0% field name mismatch errors (self-corrected)
- ✅ 95%+ queries working on first generation
- ✅ 100% queries working after iteration
- ✅ Average fix time < 5 seconds per query
- ✅ No manual intervention required

## Next Steps

1. Implement Phase 1 (field discovery) - Quick win
2. Test with Spotify demo to verify field name issue is fixed
3. Add Phase 2 (query testing) in module generator
4. Implement Phase 3 (LLM fixing)
5. Deploy and monitor success rate

## Example: Fixing the Spotify Issue

**Current Problem:**
```esql
-- Query looks for 'listen_duration_seconds'
-- But data has 'listen_duration_min'
AVG(listen_duration_seconds)  -- FAILS
```

**With Iterative Testing:**
```
1. LLM generates: AVG(listen_duration_seconds)
2. Test returns: "Field 'listen_duration_seconds' not found. Available fields: [listen_duration_min, ...]"
3. LLM fixes: AVG(listen_duration_min)
4. Test passes ✅
5. Save working query
```

## Conclusion

This approach transforms query generation from a **prediction problem** (guessing field names) to a **debugging problem** (fixing based on errors), which LLMs handle brilliantly.

The system becomes self-healing, adaptive, and maintains the creative freedom that makes LLMs powerful.