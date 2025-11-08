# Field Metadata Schema Implementation Plan

## Executive Summary

**Problem**: Query generators use hardcoded field name lists to guess field names, causing mismatches like `listen_duration_seconds` vs `listen_duration_min`.

**Solution**: Implement a field metadata schema where data generators declare field names and purposes, and query generators consume this metadata directly.

**Impact**: Eliminates all field name mismatches, removes hardcoded guessing logic, creates single source of truth.

---

## Current State Analysis

### Root Cause of Field Mismatches

**Example from Spotify Demo** (`spotify_data_science_20251027_103612`):

1. **Data Generator** creates: `listen_duration_min` (data_generator.py:327)
2. **Query Generator** searches for: `['listen_duration_seconds', 'duration_seconds', 'play_duration', 'listen_time']` (query_generator.py:61)
3. **Result**: Field not found → Falls back to `listen_duration_seconds` (doesn't exist) → Query fails

### Why All Three Defense Layers Failed

| Layer | Purpose | Why It Failed |
|-------|---------|---------------|
| Query Generator Auto-Detection | Find fields by searching hardcoded lists | List didn't include `listen_duration_min` |
| QueryValidator Fuzzy Matching | Find similar field names | Only triggered after exact mappings fail |
| QueryValidator Field Mappings | Map known variations | Checks for `listen_duration_minutes` (full word), not `listen_duration_min` (abbreviated) |

### Hardcoded Field Names in Code

**File**: `src/framework/module_generator.py`

**Lines 495-514**: Query generator template with hardcoded lists:
```python
# This template is included in LLM prompt and copied to generated modules
user_field = None
for field in ['listener_id', 'user_id', 'subscriber_id', 'customer_id', 'viewer_id', 'player_id']:
    if field in timeseries_fields:
        user_field = field
        break

timestamp_field = 'timestamp' if 'timestamp' in timeseries_fields else '@timestamp'
```

**Result**: Every generated query module inherits this pattern and creates similar hardcoded lists.

---

## Proposed Solution: Field Metadata Schema

### Architecture Overview

```
┌─────────────────────────┐
│  Data Generator Module  │
│                         │
│  generate_datasets()    │──┐
│  get_relationships()    │  │
│  get_semantic_fields()  │  │  Existing methods
│                         │  │
│  get_field_metadata()   │◄─┘  NEW METHOD
│  (declares all fields) │
└────────────┬────────────┘
             │
             │ Field metadata dict
             │ (field names + roles + types)
             ▼
┌─────────────────────────┐
│ Query Generator Module  │
│                         │
│  Reads metadata         │
│  Uses EXACT field names │
│  No hardcoded lists     │
└─────────────────────────┘
```

### Field Metadata Schema

```python
def get_field_metadata(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Declare metadata for every field in every dataset.

    Returns:
        {
            'dataset_name': {
                'field_name': {
                    'role': str,              # Field purpose
                    'data_type': str,         # ES data type
                    'description': str,       # Human-readable purpose
                    'aggregations': List[str], # Valid aggregation functions
                    'groupable': bool,        # Can use in GROUP BY
                    'filterable': bool,       # Can use in WHERE
                    'unit': str,              # For metrics (minutes/seconds/dollars/count)
                    'links_to': str           # For foreign keys (target dataset)
                }
            }
        }
    """
```

### Field Roles

| Role | Purpose | Examples |
|------|---------|----------|
| `timestamp` | Time-series ordering field | `timestamp`, `event_time`, `created_at` |
| `metric` | Numeric value for aggregation | `listen_duration_min`, `revenue`, `play_count` |
| `dimension` | Categorical field for grouping | `genre`, `region`, `device_type` |
| `foreign_key` | Join key to another dataset | `listener_id`, `show_id`, `user_id` |
| `primary_key` | Unique identifier | `id`, `episode_id` |
| `semantic` | Rich text for semantic search | `episode_description`, `review_text` |

### Example Metadata

```python
def get_field_metadata(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
    return {
        'podcast_listening_events': {
            'timestamp': {
                'role': 'timestamp',
                'data_type': 'date',
                'description': 'Event occurrence time',
                'aggregations': [],
                'groupable': False,
                'filterable': True
            },
            'listener_id': {
                'role': 'foreign_key',
                'data_type': 'keyword',
                'description': 'Unique listener identifier',
                'links_to': 'listener_profiles',
                'aggregations': [],
                'groupable': True,
                'filterable': True
            },
            'listen_duration_min': {
                'role': 'metric',
                'data_type': 'long',
                'description': 'Listening duration in minutes',
                'unit': 'minutes',
                'aggregations': ['sum', 'avg', 'min', 'max', 'percentiles'],
                'groupable': False,
                'filterable': True
            },
            'genre': {
                'role': 'dimension',
                'data_type': 'keyword',
                'description': 'Podcast genre category',
                'aggregations': ['count', 'cardinality'],
                'groupable': True,
                'filterable': True
            },
            'episode_description': {
                'role': 'semantic',
                'data_type': 'semantic_text',
                'description': 'Rich episode description for semantic search',
                'aggregations': [],
                'groupable': False,
                'filterable': False
            }
        }
    }
```

---

## Implementation Plan

### Phase 1: Add Base Class Method ✅ Priority 1

**File**: `src/framework/base.py`

**Location**: After `get_semantic_fields()` method (line 74)

**Action**: Add new abstract method to `DataGeneratorModule`:

```python
def get_field_metadata(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Provide metadata about each field's purpose and usage in queries.

    This enables query generators to use exact field names and understand
    field purposes without hardcoded guessing logic.

    Returns:
        Dictionary mapping dataset names to field metadata:
        {
            'dataset_name': {
                'field_name': {
                    'role': 'timestamp' | 'metric' | 'dimension' | 'foreign_key' | 'primary_key' | 'semantic',
                    'data_type': 'date' | 'long' | 'double' | 'keyword' | 'text' | 'semantic_text',
                    'description': str,
                    'aggregations': List[str],  # For metrics: ['sum', 'avg', 'min', 'max', 'percentiles', 'count']
                    'groupable': bool,
                    'filterable': bool,
                    'unit': str,  # For metrics: 'minutes' | 'seconds' | 'hours' | 'dollars' | 'count' | etc.
                    'links_to': str  # For foreign_key: target dataset name
                }
            }
        }

    Field Roles:
        - timestamp: Time-series ordering field (event_time, created_at)
        - metric: Numeric value for aggregation (revenue, duration, count)
        - dimension: Categorical field for grouping (region, genre, status)
        - foreign_key: Join key to another dataset (user_id, product_id)
        - primary_key: Unique identifier (id, episode_id)
        - semantic: Rich text for semantic search (description, review)

    Example:
        {
            'events': {
                'timestamp': {
                    'role': 'timestamp',
                    'data_type': 'date',
                    'description': 'Event time'
                },
                'listen_duration_min': {
                    'role': 'metric',
                    'data_type': 'long',
                    'unit': 'minutes',
                    'aggregations': ['sum', 'avg', 'min', 'max'],
                    'groupable': False,
                    'filterable': True,
                    'description': 'Listening duration'
                }
            }
        }
    """
    return {}  # Default: empty (backward compatible)
```

**Testing**: No changes needed - default implementation is backward compatible.

---

### Phase 2: Update Data Generator Prompts ✅ Priority 1

**File**: `src/framework/module_generator.py`

**Location**: In `_generate_data_module()` method, after `get_semantic_fields()` prompt section (around line 273-280)

**Action**: Add comprehensive field metadata instructions to LLM prompt:

```python
# Add after the get_semantic_fields() section in the prompt:

CRITICAL: Implement get_field_metadata() to describe EVERY field's purpose.

This metadata enables query generators to use exact field names without guessing.
You MUST provide metadata for EVERY field in EVERY dataset.

Field Metadata Structure:
```python
def get_field_metadata(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
    return {
        'dataset_name': {
            'field_name': {
                'role': 'timestamp' | 'metric' | 'dimension' | 'foreign_key' | 'primary_key' | 'semantic',
                'data_type': 'date' | 'long' | 'double' | 'keyword' | 'text' | 'semantic_text',
                'description': str,  # Human-readable purpose
                'aggregations': List[str],  # Valid aggregation functions
                'groupable': bool,  # Can use in GROUP BY
                'filterable': bool,  # Can use in WHERE
                'unit': str,  # For metrics only
                'links_to': str  # For foreign_key only
            }
        }
    }
```

Field Roles:
- **timestamp**: Time-series ordering (timestamp, event_time, created_at)
- **metric**: Numeric values for aggregation (duration, revenue, count, score)
- **dimension**: Categories for grouping (genre, region, status, device_type)
- **foreign_key**: Join keys (user_id, product_id, account_id)
- **primary_key**: Unique identifiers (id, episode_id)
- **semantic**: Rich text for semantic search (description, notes, review)

Examples:

```python
# Timestamp field
'timestamp': {
    'role': 'timestamp',
    'data_type': 'date',
    'description': 'Event occurrence time',
    'aggregations': [],
    'groupable': False,
    'filterable': True
}

# Metric field (duration)
'listen_duration_min': {
    'role': 'metric',
    'data_type': 'long',
    'unit': 'minutes',
    'aggregations': ['sum', 'avg', 'min', 'max', 'percentiles'],
    'groupable': False,
    'filterable': True,
    'description': 'Time spent listening to content'
}

# Dimension field (category)
'genre': {
    'role': 'dimension',
    'data_type': 'keyword',
    'aggregations': ['count', 'cardinality'],
    'groupable': True,
    'filterable': True,
    'description': 'Content genre category'
}

# Foreign key field
'listener_id': {
    'role': 'foreign_key',
    'data_type': 'keyword',
    'links_to': 'listener_profiles',
    'aggregations': ['count', 'cardinality'],
    'groupable': True,
    'filterable': True,
    'description': 'Links to listener profiles'
}

# Semantic text field
'episode_description': {
    'role': 'semantic',
    'data_type': 'semantic_text',
    'aggregations': [],
    'groupable': False,
    'filterable': False,
    'description': 'Rich episode description for semantic search'
}
```

IMPORTANT Guidelines:
1. Every field must have metadata - no exceptions
2. Use descriptive, clear descriptions
3. For metrics, list all valid aggregations
4. For foreign keys, specify target dataset in 'links_to'
5. Set groupable=True only for dimensions and keys
6. Set filterable=True for fields usable in WHERE clauses
```

**Testing**: Generate new demo and verify `get_field_metadata()` is implemented with all fields.

---

### Phase 3: Update Query Generator Prompts ✅ Priority 1

**File**: `src/framework/module_generator.py`

**Location**: In `_generate_query_module()` method (around line 300-570)

**Changes Required**:

#### 3A: Add Field Metadata to Query Generator Context

**Location**: Top of `_generate_query_module()` method (line 300)

```python
def _generate_query_module(self, config: Dict[str, Any], module_path: Path):
    """Generate the query generation module"""

    # Load the data generator to get field metadata
    sys.path.insert(0, str(module_path))
    try:
        data_module = importlib.import_module('data_generator')
        data_gen_class = [cls for cls in dir(data_module)
                         if 'DataGenerator' in cls and cls != 'DataGeneratorModule'][0]
        data_gen = getattr(data_module, data_gen_class)(DemoConfig(**config))
        datasets = data_gen.generate_datasets()
        field_metadata = data_gen.get_field_metadata()
    finally:
        sys.path.pop(0)

    # Include field metadata in the prompt
    prompt = f"""Generate a Python module that implements QueryGeneratorModule...

    FIELD METADATA (use these exact field names):
    ```json
    {json.dumps(field_metadata, indent=2)}
    ```
    """
```

#### 3B: Remove Hardcoded Field Detection Template

**Location**: Lines 495-514 (the hardcoded template)

**REMOVE** this entire section:
```python
# Extract ACTUAL field names for common concepts
# You MUST adapt these based on what fields actually exist!
timeseries_fields = self.datasets[timeseries_dataset].columns if timeseries_dataset else []

# Find the actual user/listener ID field
user_field = None
for field in ['listener_id', 'user_id', 'subscriber_id', 'customer_id', 'viewer_id', 'player_id']:
    if field in timeseries_fields:
        user_field = field
        break

# Find the actual timestamp field
timestamp_field = 'timestamp' if 'timestamp' in timeseries_fields else '@timestamp'

# Find the actual item/content ID field
item_field = None
for field in timeseries_fields:
    if field.endswith('_id') and field != user_field:
        item_field = field
        break
```

**REPLACE** with metadata-based helper functions:

```python
CRITICAL: Use field metadata to find fields by role, NOT hardcoded lists.

The data generator provides get_field_metadata() which declares all field names and purposes.
You MUST use this metadata to find fields by their role.

Helper Functions Template:
```python
def __init__(self, config: DemoConfig, datasets: Dict[str, pd.DataFrame]):
    super().__init__(config, datasets)

    # Load field metadata from data generator
    # (In actual implementation, this will be passed from orchestrator)
    from data_generator import {CompanyName}DataGenerator
    data_gen = {CompanyName}DataGenerator(config)
    self.field_metadata = data_gen.get_field_metadata()

def _find_field_by_role(self, dataset: str, role: str, **filters) -> Optional[str]:
    """
    Find a field by its role in the metadata.

    Args:
        dataset: Dataset name
        role: Field role ('timestamp', 'metric', 'dimension', 'foreign_key', etc.)
        **filters: Additional filters (e.g., links_to='users', unit='minutes')

    Returns:
        Field name or None

    Example:
        timestamp_field = self._find_field_by_role('events', 'timestamp')
        duration_field = self._find_field_by_role('events', 'metric', unit='minutes')
        user_key = self._find_field_by_role('events', 'foreign_key', links_to='users')
    """
    if dataset not in self.field_metadata:
        return None

    for field_name, metadata in self.field_metadata[dataset].items():
        if metadata.get('role') != role:
            continue

        # Check additional filters
        match = True
        for key, value in filters.items():
            if metadata.get(key) != value:
                match = False
                break

        if match:
            return field_name

    return None

def _find_fields_by_role(self, dataset: str, role: str) -> List[str]:
    """Find all fields with a given role"""
    if dataset not in self.field_metadata:
        return []

    return [
        field_name
        for field_name, metadata in self.field_metadata[dataset].items()
        if metadata.get('role') == role
    ]

def _get_field_info(self, dataset: str, field_name: str) -> Dict[str, Any]:
    """Get full metadata for a specific field"""
    return self.field_metadata.get(dataset, {}).get(field_name, {})
```

Usage Example in generate_queries():
```python
def generate_queries(self) -> List[Dict[str, Any]]:
    # Find fields using metadata - NO hardcoded field names!
    timeseries_dataset = self._find_timeseries_dataset()

    timestamp_field = self._find_field_by_role(timeseries_dataset, 'timestamp')
    duration_field = self._find_field_by_role(timeseries_dataset, 'metric', unit='minutes')
    user_key = self._find_field_by_role(timeseries_dataset, 'foreign_key', links_to='users')

    # Get all dimension fields for grouping
    dimension_fields = self._find_fields_by_role(timeseries_dataset, 'dimension')

    # Get all metric fields for aggregation
    metric_fields = self._find_fields_by_role(timeseries_dataset, 'metric')

    # Now use these EXACT field names in queries
    queries = []
    queries.append({
        'name': 'Total Duration by Genre',
        'esql': f'''
            FROM {timeseries_dataset}
            | STATS total_duration = SUM({duration_field})
              BY {dimension_fields[0]}
            | SORT total_duration DESC
            | LIMIT 10
        '''
    })

    return queries
```

DO NOT use hardcoded field name lists like:
❌ for field in ['listen_duration_seconds', 'duration_seconds']:
❌ timestamp_field = 'timestamp' if 'timestamp' in fields else '@timestamp'
❌ if field.endswith('_id'):

ALWAYS use metadata lookups:
✅ duration_field = self._find_field_by_role('events', 'metric', unit='minutes')
✅ timestamp_field = self._find_field_by_role('events', 'timestamp')
✅ user_key = self._find_field_by_role('events', 'foreign_key', links_to='users')
```

**Testing**: Generate new demo and verify query generator uses `_find_field_by_role()` methods instead of hardcoded lists.

---

### Phase 4: Update Orchestrator ✅ Priority 2

**File**: `src/framework/orchestrator.py`

**Location**: In `generate_new_demo()` method where query generator is loaded

**Current Code** (approximate):
```python
data_gen = loader.load_data_generator()
datasets = data_gen.generate_datasets()
query_gen = loader.load_query_generator(datasets)
```

**Updated Code**:
```python
data_gen = loader.load_data_generator()
datasets = data_gen.generate_datasets()
field_metadata = data_gen.get_field_metadata()  # NEW

# Pass metadata to query generator
query_gen = loader.load_query_generator(datasets)
query_gen.field_metadata = field_metadata  # NEW
```

**Also Update**: `src/framework/module_loader.py` if needed to ensure `field_metadata` is available.

**Testing**: Generate demo and verify field_metadata is accessible in query generator.

---

### Phase 5: Update Module Loader ✅ Priority 2

**File**: `src/framework/module_loader.py`

**Action**: Ensure query generator receives field metadata when loaded.

**Testing**: Load existing demo and verify metadata is available.

---

### Phase 6: Update QueryValidator (Optional) ⚠️ Priority 3

**File**: `src/framework/query_validator.py`

**Purpose**: QueryValidator can use field metadata instead of hardcoded mappings.

**Changes**:
- Accept `field_metadata` parameter in `__init__`
- Use metadata for validation instead of hardcoded mappings
- Keep fuzzy matching as fallback

**Testing**: Run query validation on new demos.

---

## Testing Strategy

### Test 1: Basic Field Detection
1. Generate new demo (any industry)
2. Verify `data_generator.py` has `get_field_metadata()` implemented
3. Verify all fields have metadata
4. Verify metadata has correct roles

**Expected**: Every field in every dataset has complete metadata.

### Test 2: Query Generation Uses Metadata
1. Generate new demo
2. Open `query_generator.py`
3. Search for hardcoded field lists: `for field in ['`
4. Search for metadata usage: `_find_field_by_role`

**Expected**:
- ✅ No hardcoded field name lists
- ✅ Uses `_find_field_by_role()` methods
- ✅ All queries use exact field names from metadata

### Test 3: Field Name Mismatch Prevention
1. Generate Spotify-like demo with duration metrics
2. Check data generator uses: `listen_duration_min`
3. Check query generator uses: same field name (not `listen_duration_seconds`)
4. Run queries via "Test All Queries" button

**Expected**: All queries succeed without field name errors.

### Test 4: Backward Compatibility
1. Load old demo module (before metadata implementation)
2. Verify it still works
3. `get_field_metadata()` returns `{}` (default)

**Expected**: Old modules continue to function.

### Test 5: Complex Query Scenarios
1. Generate demo with multiple metrics and dimensions
2. Verify queries use correct fields for:
   - Aggregations (SUM, AVG on metrics)
   - Grouping (GROUP BY on dimensions)
   - Filtering (WHERE on filterable fields)
   - JOINs (foreign_key fields)

**Expected**: Queries are semantically correct and use appropriate fields.

---

## Migration Path for Existing Demos

### Option 1: Leave As-Is (Recommended)
- Old demos continue to work
- New demos use metadata
- No breaking changes

### Option 2: Regenerate
- Delete old demo
- Re-run demo generation
- New version has metadata

### Option 3: Manual Retrofit
- Add `get_field_metadata()` to old data generators
- Update old query generators to use metadata
- Time-consuming, not recommended

**Recommendation**: Use Option 1 - backward compatibility is maintained.

---

## Success Metrics

### Quantitative
- ✅ 0 hardcoded field name lists in generated query modules
- ✅ 100% of fields have metadata
- ✅ 0 field name mismatch errors in queries
- ✅ All test queries pass on first generation

### Qualitative
- ✅ LLM can generate queries without guessing field names
- ✅ Field purposes are self-documenting
- ✅ Easy to add new field types
- ✅ Query generation is more reliable

---

## Timeline Estimate

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 1: Base class | 30 min | None |
| Phase 2: Data gen prompts | 1 hour | Phase 1 |
| Phase 3: Query gen prompts | 2 hours | Phase 2 |
| Phase 4: Orchestrator | 30 min | Phase 3 |
| Phase 5: Module loader | 30 min | Phase 4 |
| Phase 6: QueryValidator | 1 hour | Optional |
| **Testing** | 2 hours | All phases |
| **TOTAL** | ~7.5 hours | |

---

## Rollback Plan

If implementation causes issues:

1. **Revert Phase 3**: Restore hardcoded field detection template
2. **Keep Phase 1-2**: Data generators will have metadata (harmless)
3. **Query generators**: Will continue using old detection logic
4. **Impact**: No user-facing changes

**Rollback Time**: < 15 minutes

---

## Future Enhancements

### Enhancement 1: Field Metadata Validation
Add validation that metadata matches actual DataFrame fields.

### Enhancement 2: Metadata-Driven UI
Generate UI forms dynamically based on field metadata.

### Enhancement 3: Auto-Generated Documentation
Create field dictionaries automatically from metadata.

### Enhancement 4: Query Suggestions
Suggest optimal queries based on field roles and types.

---

## Appendix A: Complete Example

### Example Data Generator with Metadata

```python
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
from typing import Dict, List, Any

class SpotifyDataGenerator(DataGeneratorModule):

    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        # ... generate datasets ...
        return {
            'podcast_listening_events': events_df,
            'listener_profiles': profiles_df
        }

    def get_field_metadata(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return {
            'podcast_listening_events': {
                'timestamp': {
                    'role': 'timestamp',
                    'data_type': 'date',
                    'description': 'Event occurrence time',
                    'aggregations': [],
                    'groupable': False,
                    'filterable': True
                },
                'listener_id': {
                    'role': 'foreign_key',
                    'data_type': 'keyword',
                    'links_to': 'listener_profiles',
                    'aggregations': ['count', 'cardinality'],
                    'groupable': True,
                    'filterable': True,
                    'description': 'Unique listener identifier'
                },
                'show_id': {
                    'role': 'foreign_key',
                    'data_type': 'keyword',
                    'links_to': 'podcast_shows',
                    'aggregations': ['count', 'cardinality'],
                    'groupable': True,
                    'filterable': True,
                    'description': 'Podcast show identifier'
                },
                'listen_duration_min': {
                    'role': 'metric',
                    'data_type': 'long',
                    'unit': 'minutes',
                    'aggregations': ['sum', 'avg', 'min', 'max', 'percentiles'],
                    'groupable': False,
                    'filterable': True,
                    'description': 'Time spent listening in minutes'
                },
                'completion_rate': {
                    'role': 'metric',
                    'data_type': 'double',
                    'unit': 'percentage',
                    'aggregations': ['avg', 'min', 'max', 'percentiles'],
                    'groupable': False,
                    'filterable': True,
                    'description': 'Percentage of episode completed'
                },
                'genre': {
                    'role': 'dimension',
                    'data_type': 'keyword',
                    'aggregations': ['count', 'cardinality'],
                    'groupable': True,
                    'filterable': True,
                    'description': 'Podcast genre category'
                },
                'region': {
                    'role': 'dimension',
                    'data_type': 'keyword',
                    'aggregations': ['count', 'cardinality'],
                    'groupable': True,
                    'filterable': True,
                    'description': 'Geographic region'
                }
            },
            'listener_profiles': {
                'listener_id': {
                    'role': 'primary_key',
                    'data_type': 'keyword',
                    'aggregations': ['count', 'cardinality'],
                    'groupable': True,
                    'filterable': True,
                    'description': 'Unique listener identifier'
                },
                'subscription_tier': {
                    'role': 'dimension',
                    'data_type': 'keyword',
                    'aggregations': ['count', 'cardinality'],
                    'groupable': True,
                    'filterable': True,
                    'description': 'Subscription level (Free/Premium)'
                }
            }
        }
```

### Example Query Generator Using Metadata

```python
from src.framework.base import QueryGeneratorModule, DemoConfig
import pandas as pd
from typing import Dict, List, Any, Optional

class SpotifyQueryGenerator(QueryGeneratorModule):

    def __init__(self, config: DemoConfig, datasets: Dict[str, pd.DataFrame]):
        super().__init__(config, datasets)

        # Load field metadata
        from data_generator import SpotifyDataGenerator
        data_gen = SpotifyDataGenerator(config)
        self.field_metadata = data_gen.get_field_metadata()

    def _find_field_by_role(self, dataset: str, role: str, **filters) -> Optional[str]:
        """Find a field by its role in the metadata"""
        if dataset not in self.field_metadata:
            return None

        for field_name, metadata in self.field_metadata[dataset].items():
            if metadata.get('role') != role:
                continue

            match = True
            for key, value in filters.items():
                if metadata.get(key) != value:
                    match = False
                    break

            if match:
                return field_name

        return None

    def _find_fields_by_role(self, dataset: str, role: str) -> List[str]:
        """Find all fields with a given role"""
        if dataset not in self.field_metadata:
            return []

        return [
            field_name
            for field_name, metadata in self.field_metadata[dataset].items()
            if metadata.get('role') == role
        ]

    def generate_queries(self) -> List[Dict[str, Any]]:
        # Find fields using metadata
        timeseries = 'podcast_listening_events'

        timestamp_field = self._find_field_by_role(timeseries, 'timestamp')
        duration_field = self._find_field_by_role(timeseries, 'metric', unit='minutes')
        completion_field = self._find_field_by_role(timeseries, 'metric', unit='percentage')
        user_key = self._find_field_by_role(timeseries, 'foreign_key', links_to='listener_profiles')

        dimension_fields = self._find_fields_by_role(timeseries, 'dimension')

        queries = []

        # Query 1: Total listening time by genre
        queries.append({
            'name': 'Total Listening Time by Genre',
            'description': 'Aggregate total listening duration by genre',
            'esql': f'''
                FROM {timeseries}
                | STATS total_minutes = SUM({duration_field}),
                        avg_minutes = AVG({duration_field}),
                        listener_count = COUNT_DISTINCT({user_key})
                  BY {dimension_fields[0]}
                | SORT total_minutes DESC
                | LIMIT 10
            '''
        })

        # Query 2: Average completion rate by region
        queries.append({
            'name': 'Completion Rate by Region',
            'description': 'Calculate average completion rate by geographic region',
            'esql': f'''
                FROM {timeseries}
                | STATS avg_completion = AVG({completion_field})
                  BY {dimension_fields[1]}
                | SORT avg_completion DESC
            '''
        })

        return queries
```

---

## Appendix B: Field Role Reference

| Role | Use Cases | Aggregations | Groupable | Filterable |
|------|-----------|--------------|-----------|------------|
| `timestamp` | Time-series queries, date bucketing | - | No | Yes |
| `metric` | SUM, AVG, MIN, MAX, PERCENTILES | sum, avg, min, max, percentiles | No | Yes |
| `dimension` | GROUP BY, segmentation | count, cardinality | Yes | Yes |
| `foreign_key` | JOINs, relationship queries | count, cardinality | Yes | Yes |
| `primary_key` | Unique identification | count, cardinality | Yes | Yes |
| `semantic` | Semantic search, MATCH queries | - | No | No (use MATCH) |

---

## Appendix C: Common Field Units

### Duration
- `seconds` - Time in seconds
- `minutes` - Time in minutes
- `hours` - Time in hours
- `milliseconds` - Time in milliseconds

### Money
- `dollars` - USD currency
- `cents` - Cents (1/100 dollar)
- `euros` - EUR currency

### Data
- `bytes` - Data size in bytes
- `kilobytes` - Data size in KB
- `megabytes` - Data size in MB
- `gigabytes` - Data size in GB

### Count
- `count` - Simple count/tally
- `items` - Number of items
- `users` - Number of users
- `events` - Number of events

### Rate
- `percentage` - Value 0-100
- `ratio` - Value 0-1
- `rate` - Events per time unit

### Score
- `score` - Numeric score
- `rating` - User rating (1-5, 1-10, etc.)
- `confidence` - Confidence score (0-1)

---

## Document Version

- **Version**: 1.0
- **Date**: 2025-10-27
- **Author**: AI Assistant (Claude)
- **Status**: Ready for Implementation
