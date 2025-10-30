# Elasticsearch Integration - UI Implementation

## Overview

The Streamlit UI now includes full Elasticsearch indexing capabilities with LLM-driven semantic field identification. Users can index demo datasets directly from the Browse Demos view with a single click.

## Features Implemented

### 1. Elasticsearch Connection Test (Sidebar)

**Location**: `app.py:722-736`

Added a connection test section in the sidebar that's visible in both Create and Browse modes:

```python
st.markdown("### 🔗 Elasticsearch")

if st.button("Test Connection", use_container_width=True):
    from src.services.elasticsearch_indexer import ElasticsearchIndexer
    indexer = ElasticsearchIndexer()
    success, message = indexer.verify_connection()

    if success:
        st.success(f"✅ {message}")
    else:
        st.error(f"❌ {message}")
```

**What it does**:
- Tests connection to Elasticsearch using credentials from `.env`
- Shows cluster name and version on success
- Shows error message on failure

### 2. Index Dataset Button (Data Tab)

**Location**: `app.py:618-657`

Added "📤 Index" button for each dataset in the Data tab:

```python
with col3:
    # Index in Elasticsearch button
    if st.button("📤 Index", key=f"index_{name}"):
        from src.services.elasticsearch_indexer import ElasticsearchIndexer

        # Get semantic fields from LLM specification
        semantic_fields = semantic_fields_spec.get(name, [])

        # Index the dataset
        indexer = ElasticsearchIndexer()
        result = indexer.index_dataset(
            df,
            name,
            semantic_fields=semantic_fields,
            progress_callback=progress_callback
        )
```

**What it does**:
- Indexes dataset into Elasticsearch
- Uses LLM-specified semantic fields from `get_semantic_fields()`
- Shows progress bar during indexing
- Displays results: index name, type, semantic fields, duration
- Shows detailed error messages if indexing fails

### 3. Semantic Fields Display

**Location**: `app.py:662-664`

Shows which fields are using semantic_text:

```python
# Show semantic fields info if specified by LLM
if name in semantic_fields_spec:
    st.info(f"🧠 **Semantic fields:** {', '.join(semantic_fields_spec[name])}")
```

**What it shows**:
- Info box below the data preview
- Lists all fields that will use semantic_text with ELSER embeddings

## User Workflow

### Testing Connection

1. Open the app
2. Look at sidebar
3. Click "Test Connection" button
4. See connection status

### Indexing a Dataset

1. Switch to "Browse Demos" mode
2. Click on a demo module
3. Click "View Details"
4. Go to "Data" tab
5. For each dataset:
   - See preview of data
   - See semantic fields indicator (if any)
   - Click "📤 Index" button
6. Watch progress bar
7. See success message with details

## Example Success Message

```
✅ Indexed 10,000 documents

Index: player_activity (data_stream)

Semantic fields: event_description

Duration: 12.34s
```

## Example Semantic Fields Info

```
🧠 Semantic fields: player_behavior_profile
```

This appears below the data preview for `player_profiles` dataset.

## Technical Details

### LLM-Driven Semantic Fields

The UI automatically retrieves semantic field specifications from the data generator module:

```python
data_gen = loader.load_data_generator()
datasets = data_gen.generate_datasets()
semantic_fields_spec = data_gen.get_semantic_fields()  # LLM specification

# For each dataset:
semantic_fields = semantic_fields_spec.get(name, [])  # Get fields for this dataset
```

### Index Creation

The indexer automatically:
- Detects if data is timeseries (has timestamp) → creates data stream
- Detects if data is lookup (no timestamp) → creates lookup index with `index.mode: lookup`
- Configures semantic_text fields with `.elser-2-elasticsearch` endpoint
- Handles `@timestamp` mapping for timeseries data
- Bulk indexes documents in batches of 1000

### Progress Tracking

Progress callback shows real-time status:
- 10%: Analyzed dataset
- 30%: Created index/data stream
- 40%: Prepared documents
- 40-95%: Indexing batches
- 95%: Complete

### Error Handling

UI shows:
- Full error messages
- Python traceback for debugging
- Specific field mapping errors
- Bulk indexing failures

## Example Demo Module

Added `get_semantic_fields()` to Epic Games demo:

```python
def get_semantic_fields(self) -> Dict[str, List[str]]:
    """Specify fields that should use semantic_text for vector search"""
    return {
        'player_profiles': [
            'player_behavior_profile'  # Rich behavioral narratives
        ],
        'player_activity': [
            'event_description'  # Detailed event descriptions
        ]
    }
```

## Backward Compatibility

Modules without `get_semantic_fields()`:
- ✅ Still work normally
- ✅ Fall back to empty dict
- ✅ No semantic fields configured (uses heuristics)
- ✅ Can be manually updated

## Environment Configuration

Required in `.env` (choose one option):

**Option 1: Elastic Cloud (Recommended)**
```bash
ELASTICSEARCH_CLOUD_ID=your-cloud-id-here
ELASTICSEARCH_API_KEY=your-api-key-here
```

**Option 2: Custom Endpoint**
```bash
ELASTIC_ENDPOINT=https://my-deployment.es.us-central1.gcp.cloud.es.io:443
ELASTIC_API_KEY=your-api-key-here
```

The indexer supports multiple naming conventions for flexibility:
- `ELASTICSEARCH_CLOUD_ID` or `ELASTIC_CLOUD_ID`
- `ELASTICSEARCH_API_KEY` or `ELASTIC_API_KEY`
- `ELASTIC_ENDPOINT` or `ELASTIC_CLOUD_ENDPOINT`

## UI Layout

```
Browse Demos View
│
├─ Demo Card (expandable)
│   ├─ View Details Button
│   └─ Delete Button
│
└─ Details View (tabs)
    ├─ Config Tab
    ├─ Data Tab
    │   ├─ Dataset 1
    │   │   ├─ Dataset Name
    │   │   ├─ [📥 CSV] [📤 Index] buttons
    │   │   ├─ Data Preview (10 rows)
    │   │   ├─ Total rows count
    │   │   └─ 🧠 Semantic fields info (if any)
    │   └─ Dataset 2
    │       └─ ... same structure
    ├─ Queries Tab
    └─ Guide Tab
```

## Next Steps

Future enhancements:
1. Index management view (list all indexed datasets)
2. Delete index button
3. View index mappings
4. Index statistics (doc count, size)
5. Re-index button for updates
6. Index settings configuration
7. Multi-environment support (dev/prod)

## Testing

To test the integration:

1. **Test Connection**:
```bash
# Start app
streamlit run app.py

# In sidebar: Click "Test Connection"
# Should show: "Connected to [cluster-name] (version 8.x.x)"
```

2. **Test Indexing**:
```bash
# In Browse Demos: Open epic_games_product_20251023_135523
# Data tab: Click "📤 Index" for player_profiles
# Should show progress bar
# Should complete with success message
# Check semantic fields: "player_behavior_profile"
```

3. **Verify in Elasticsearch**:
```bash
GET player_profiles_lookup/_mapping
# Should show semantic_text field for player_behavior_profile

GET player_profiles_lookup/_count
# Should show 500 documents
```

## Benefits

- ✅ **One-click indexing**: No manual ES commands needed
- ✅ **LLM-driven semantics**: Smart field type detection
- ✅ **Real-time feedback**: Progress and status updates
- ✅ **Error visibility**: Clear error messages
- ✅ **Automatic configuration**: Data streams vs lookup indices
- ✅ **Demo-ready data**: Instantly available for Agent Builder

## Summary

The UI integration is complete and functional. Users can now:
1. Test Elasticsearch connection from sidebar
2. Index datasets with a single button click
3. See LLM-specified semantic fields
4. Track indexing progress in real-time
5. View detailed success/error messages

All future demo modules generated by the LLM will automatically include `get_semantic_fields()` method with intelligent semantic field identification.
