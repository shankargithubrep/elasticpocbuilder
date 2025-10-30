# Elasticsearch Indexing Strategy for Demo Builder

## Overview

This document outlines the strategy for indexing generated demo datasets into Elasticsearch serverless environments, with proper handling of data streams, lookup indices, and semantic text embeddings.

## Architecture Components

### 1. Data Classification

**Timeseries Data (Events/Activity)**
- High-volume, append-only data with timestamps
- Examples: player_events, player_activity, transactions, battlepass_events
- **Storage**: Elasticsearch Data Streams
- **Requirements**: Must have `@timestamp` field

**Lookup/Contextual Data (Dimension Tables)**
- Lower-volume, reference data
- Examples: player_profiles, geo_segments, platform_metadata
- **Storage**: Lookup Indices with `index.mode: lookup`
- **Purpose**: Enrichment via ES|QL LOOKUP JOIN operations

### 2. Semantic Text Fields

**Identification Criteria**
- Text fields used in SEMANTIC() queries
- Rich descriptive content (50+ characters)
- Examples:
  - `player_behavior_profile` (player_profiles)
  - `event_description` (player_activity)
  - `feedback_text` (player_feedback)

**Configuration**
- Field type: `semantic_text`
- Inference endpoint: `.elser-2-elasticsearch` (always available on EIS)
- Auto-generates embeddings using ELSER v2

## Implementation Strategy

### Phase 1: Environment Setup

1. **Elasticsearch Client Initialization**
   - Read credentials from `.env` (ELASTIC_ENDPOINT, ELASTIC_API_KEY)
   - Configure for serverless environment
   - Verify connectivity

2. **Index Template Creation**
   - Create component templates for common fields
   - Create index templates for data streams (with `data_stream: {}`)
   - Configure mappings with semantic_text fields

### Phase 2: Lookup Index Creation

```json
PUT /player_profiles_lookup
{
  "settings": {
    "index.mode": "lookup"
  },
  "mappings": {
    "properties": {
      "player_id": {"type": "keyword"},
      "player_segment": {"type": "keyword"},
      "primary_platform": {"type": "keyword"},
      "region": {"type": "keyword"},
      "account_tier": {"type": "keyword"},
      "total_lifetime_spend": {"type": "float"},
      "battle_pass_owned": {"type": "boolean"},
      "account_age_days": {"type": "integer"},
      "player_behavior_profile": {
        "type": "semantic_text",
        "inference_id": ".elser-2-elasticsearch"
      }
    }
  }
}
```

**Characteristics**:
- Standard index with `index.mode: lookup`
- Optimized for LOOKUP JOIN operations
- No timestamp requirement
- Suitable for slowly-changing dimension data

### Phase 3: Data Stream Creation

```json
PUT /_index_template/player_activity_template
{
  "index_patterns": ["player_activity-*"],
  "data_stream": {},
  "template": {
    "mappings": {
      "properties": {
        "@timestamp": {"type": "date"},
        "event_id": {"type": "keyword"},
        "player_id": {"type": "keyword"},
        "event_type": {"type": "keyword"},
        "platform_used": {"type": "keyword"},
        "session_duration_minutes": {"type": "float"},
        "vbucks_spent": {"type": "integer"},
        "match_result": {"type": "keyword"},
        "event_description": {
          "type": "semantic_text",
          "inference_id": ".elser-2-elasticsearch"
        }
      }
    }
  }
}

PUT /_data_stream/player_activity
```

**Characteristics**:
- Requires matching index template with `data_stream: {}`
- Auto-creates backing indices (`.ds-player_activity-*`)
- Write to stream name, reads across all backing indices
- Automatic `@timestamp` field requirement

### Phase 4: Data Ingestion

**Bulk Indexing Strategy**:
1. Batch documents (1000-5000 per request)
2. Use `_bulk` API for efficiency
3. For data streams: use `create` action (append-only)
4. For lookup indices: use `index` action (upsert)
5. Handle timestamp conversion (pandas → ISO8601)

**Error Handling**:
- Retry on network errors (exponential backoff)
- Log partial failures from bulk responses
- Track indexing progress and statistics

## Field Mapping Strategy

### Automatic Field Detection

Analyze pandas DataFrame to determine:
1. **Timeseries vs Lookup**: Presence of `timestamp` or `@timestamp` column
2. **Semantic Text Candidates**: String columns with mean length > 50 chars
3. **Keyword vs Text**: Cardinality analysis (low cardinality → keyword)
4. **Numeric Types**: int64 → long, float64 → double

### Manual Override Mechanism

Allow demo generators to specify:
```python
def get_field_mappings(self) -> Dict[str, Dict[str, str]]:
    return {
        "player_behavior_profile": {
            "type": "semantic_text",
            "inference_id": ".elser-2-elasticsearch"
        },
        "player_id": {"type": "keyword"}
    }
```

## Naming Conventions

### Data Streams
- Pattern: `{dataset_name}` (lowercase, no special chars)
- Example: `player_activity`, `battlepass_events`
- Backing indices: `.ds-{dataset_name}-{yyyy.MM.dd}-{generation}`

### Lookup Indices
- Pattern: `{dataset_name}_lookup`
- Example: `player_profiles_lookup`, `platform_metadata_lookup`

### Index Templates
- Pattern: `{dataset_name}_template`
- Index pattern: `{dataset_name}-*`

## UI Integration

### Browse Demos → Data Tab

For each dataset, display:
```
Dataset: player_profiles (500 rows)
[Preview] [Download CSV] [Index in Elasticsearch]

Status: Not indexed
```

After clicking "Index in Elasticsearch":
```
Status: Indexing... 500/500 documents
✓ Indexed as: player_profiles_lookup (lookup index)
✓ Semantic text: player_behavior_profile → .elser-2-elasticsearch
```

### Progress Tracking

Show real-time progress:
- Documents indexed / Total
- Current batch
- Errors (if any)
- Index name and type
- Semantic fields configured

## Error Scenarios and Handling

1. **Missing @timestamp in timeseries data**
   - Auto-add `@timestamp` from `timestamp` column
   - Validate ISO8601 format

2. **Inference endpoint unavailable**
   - Fall back to regular `text` field
   - Warn user about missing semantic capabilities

3. **Index already exists**
   - Prompt: "Index exists. Delete and recreate? [Yes/No]"
   - Or: "Append to existing index? [Yes/No]"

4. **Connection failures**
   - Retry with exponential backoff (3 attempts)
   - Display clear error message
   - Suggest checking `.env` credentials

## Security Considerations

- API key from `.env` (never hardcoded)
- Validate serverless endpoint format
- Use HTTPS only
- No sensitive data logging

## Performance Optimization

1. **Batch Size**: 1000-5000 docs per bulk request
2. **Parallelization**: Single-threaded for safety (avoid serverless rate limits)
3. **Memory**: Stream large datasets (don't load all in memory)
4. **Index Refresh**: Let Elasticsearch handle (no forced refresh)

## Testing Strategy

1. **Unit Tests**: Mock Elasticsearch client
2. **Integration Tests**: Use test Elasticsearch instance
3. **Validation**:
   - Verify document count matches DataFrame rows
   - Confirm semantic_text fields exist
   - Test LOOKUP JOIN compatibility

## Future Enhancements

1. **Index Lifecycle Management**: Auto-rollover for data streams
2. **Alias Management**: Create readable aliases
3. **Reindexing**: Support for schema changes
4. **Monitoring**: Track indexing metrics over time
5. **Multi-environment**: Dev/Staging/Prod Elasticsearch clusters

## Implementation Files

- `src/services/elasticsearch_indexer.py` - Core indexing logic
- `src/services/field_mapper.py` - Field type detection and mapping
- `src/ui/components/index_button.py` - Streamlit UI component
- `tests/test_elasticsearch_indexer.py` - Unit tests

## Success Criteria

✅ Timeseries data indexed as data streams with @timestamp
✅ Lookup data indexed with `index.mode: lookup`
✅ Semantic text fields use `.elser-2-elasticsearch`
✅ Bulk indexing completes without errors
✅ UI shows clear progress and status
✅ Generated queries work against indexed data
