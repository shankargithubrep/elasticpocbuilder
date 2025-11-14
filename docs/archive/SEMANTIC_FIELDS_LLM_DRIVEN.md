# LLM-Driven Semantic Field Identification

## Overview

Instead of using simple heuristics (like character count > 50), the system now allows the LLM to intelligently identify which fields should use `semantic_text` with ELSER embeddings. The LLM understands the semantic intent of each field and can make better decisions about which fields would benefit from vector-based semantic search.

## Rationale

**Problem with Heuristics:**
- Character count doesn't capture semantic meaning
- A 30-character field might have rich contextual value
- A 200-character field might just be a long ID or URL

**LLM Understanding:**
- The LLM generates the data and understands its purpose
- It knows which fields contain:
  - Rich narratives (semantic search valuable)
  - Short categorical values (keyword search better)
  - Structured identifiers (exact match only)

## Implementation

### 1. Base Module Interface

**File**: `src/framework/base.py`

Added optional method to `DataGeneratorModule`:

```python
def get_semantic_fields(self) -> Dict[str, List[str]]:
    """Specify which fields should use semantic_text with ELSER embeddings

    Returns:
        Dictionary mapping dataset names to lists of semantic field names

    Example:
        {
            'player_profiles': ['player_behavior_profile', 'player_notes'],
            'player_activity': ['event_description', 'match_summary']
        }
    """
    return {}  # Default: no semantic fields (backward compatible)
```

### 2. Module Generator Prompts

**File**: `src/framework/module_generator.py`

Updated prompt to instruct LLM:

```python
def get_semantic_fields(self) -> Dict[str, List[str]]:
    \"\"\"Specify fields that should use semantic_text for vector search\"\"\"
    return {{
        # 'dataset_name': ['field1', 'field2']
        # Fields with rich contextual meaning suitable for semantic search
        # Examples: descriptions, narratives, feedback, notes, summaries
        # NOT: IDs, keywords, short labels, categorical values
    }}

CRITICAL: Implement get_semantic_fields() to identify text fields with meaningful
contextual information that would benefit from semantic (vector) search vs literal matching.
Think about which fields a human would want to search semantically - rich descriptions,
narratives, behavior profiles, feedback text, etc.
```

### 3. Field Mapper Updates

**File**: `src/services/elasticsearch_indexer.py`

#### Updated `analyze_dataframe()`:
```python
def analyze_dataframe(
    df: pd.DataFrame,
    semantic_fields: Optional[List[str]] = None  # NEW: LLM-specified fields
) -> Dict[str, Any]:
    """
    Args:
        semantic_fields: Optional list of fields to configure as semantic_text.
                       If provided, these fields are used instead of auto-detection.
    """
    semantic_field_set = set(semantic_fields) if semantic_fields else set()

    for column in df.columns:
        is_semantic = column in semantic_field_set
        field_mapping = FieldMapper._map_column(df[column], column, force_semantic=is_semantic)
```

#### Updated `_map_column()`:
```python
def _map_column(
    series: pd.Series,
    column_name: str,
    force_semantic: bool = False  # NEW: LLM override
) -> Dict[str, Any]:
    """
    If force_semantic=True, uses semantic_text regardless of heuristics
    """
    if pd.api.types.is_string_dtype(dtype) or pd.api.types.is_object_dtype(dtype):
        if force_semantic:  # LLM says this should be semantic
            return {
                "type": "semantic_text",
                "inference_id": ".elser-2-elasticsearch"
            }
        # Otherwise fall back to heuristics...
```

#### Updated `index_dataset()`:
```python
def index_dataset(
    self,
    df: pd.DataFrame,
    dataset_name: str,
    semantic_fields: Optional[List[str]] = None,  # NEW parameter
    progress_callback: Optional[callable] = None
) -> IndexingResult:
    """
    Args:
        semantic_fields: Optional list of fields to use semantic_text (from LLM)
    """
    mapping_info = FieldMapper.analyze_dataframe(df, semantic_fields)
```

## Usage Example

### LLM-Generated Module

```python
class EpicGamesDataGenerator(DataGeneratorModule):
    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        # ... generate data ...
        return {
            'player_profiles': player_profiles_df,
            'player_activity': player_activity_df
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        """LLM identifies fields with rich contextual meaning"""
        return {
            'player_profiles': [
                'player_behavior_profile'  # Rich behavioral narratives
            ],
            'player_activity': [
                'event_description'  # Detailed event descriptions
            ]
        }
```

### Indexing with LLM Specifications

```python
from src.services.elasticsearch_indexer import ElasticsearchIndexer

# Load the generated module
data_gen = loader.load_data_generator()
datasets = data_gen.generate_datasets()
semantic_field_spec = data_gen.get_semantic_fields()

# Index each dataset with LLM-specified semantic fields
indexer = ElasticsearchIndexer()

for dataset_name, df in datasets.items():
    # Get semantic fields for this dataset from LLM spec
    semantic_fields = semantic_field_spec.get(dataset_name, [])

    result = indexer.index_dataset(
        df=df,
        dataset_name=dataset_name,
        semantic_fields=semantic_fields  # LLM specification
    )

    print(f"Indexed {dataset_name}")
    print(f"  Semantic fields: {result.semantic_fields}")
```

## Decision Criteria for Semantic Fields

The LLM should identify fields as semantic_text when they contain:

✅ **Good Candidates:**
- Player behavior profiles/narratives
- Event descriptions and summaries
- User feedback and comments
- Product descriptions and reviews
- Incident reports and notes
- Match summaries and recaps
- Character descriptions
- Campaign messaging

❌ **Not Good Candidates:**
- Player IDs, transaction IDs
- Email addresses, URLs
- Short status labels ("active", "pending")
- Categorical values ("tier_1", "premium")
- Structured codes ("US-CA-SF")
- Names (better as keyword)
- Short titles (better as text with keyword subfield)

## Benefits

1. **Semantic Precision**: LLM understands which fields have semantic value
2. **No Arbitrary Thresholds**: No "character count > 50" heuristics
3. **Context-Aware**: LLM knows the purpose of each field
4. **Query Alignment**: Fields match the SEMANTIC() queries in generated queries
5. **Backward Compatible**: Defaults to empty dict if not implemented

## Impact on Generated Queries

When the LLM generates ES|QL queries with SEMANTIC(), it already knows which fields are semantic:

```python
# Query generator knows these fields are semantic
queries.append({
    "name": "Churn Signal Detection",
    "esql": """
        FROM player_feedback-*
        | WHERE SEMANTIC(feedback_text, "frustrated, want to quit")
        | LOOKUP JOIN player_profiles ON player_id
        | WHERE SEMANTIC(player_behavior_profile, "high value at-risk player")
    """
})

# Data generator specifies the same fields
def get_semantic_fields(self):
    return {
        'player_feedback': ['feedback_text'],
        'player_profiles': ['player_behavior_profile']
    }
```

**Consistency**: The semantic fields specified in data generation match the fields used in SEMANTIC() queries!

## Testing

### Unit Test Example

```python
def test_llm_semantic_field_specification():
    """Test that LLM-specified semantic fields override heuristics"""
    df = pd.DataFrame({
        'short_rich_field': ['Great!', 'Bad!', 'OK'],  # Short but semantic
        'long_id_field': ['x' * 100] * 3  # Long but not semantic
    })

    # Without LLM spec: heuristic would pick long_id_field
    result_auto = FieldMapper.analyze_dataframe(df)
    assert result_auto['semantic_fields'] == ['long_id_field']  # Wrong!

    # With LLM spec: uses LLM decision
    result_llm = FieldMapper.analyze_dataframe(df, semantic_fields=['short_rich_field'])
    assert result_llm['semantic_fields'] == ['short_rich_field']  # Correct!
```

## Future Enhancements

1. **Confidence Scores**: LLM could rate semantic suitability (0-100%)
2. **Field Purpose Metadata**: LLM explains why each field is semantic
3. **Query Validation**: Cross-check semantic fields against SEMANTIC() queries
4. **Auto-Generation**: Suggest semantic fields during review

## Migration Path

Existing modules without `get_semantic_fields()`:
- ✅ Continue to work (backward compatible)
- ✅ Fall back to heuristic detection
- ✅ Can be manually updated to add the method

New modules from LLM:
- ✅ Automatically include `get_semantic_fields()`
- ✅ LLM decides based on semantic understanding
- ✅ More accurate than heuristics

## Summary

By letting the LLM specify semantic fields, we get:
- **Better accuracy**: LLM understands semantic value
- **Consistency**: Semantic fields match SEMANTIC() queries
- **Flexibility**: Can override heuristics when needed
- **Intelligence**: Contextual decisions vs arbitrary rules
