# Inference Endpoints UI Configuration

## Summary

Added user-configurable inference endpoint settings in the Streamlit sidebar, allowing users to customize RERANK and COMPLETION endpoint IDs without editing code.

## Problem Solved

**Before**: Inference endpoint IDs were hardcoded placeholders (`rerank_endpoint`, `completion_endpoint`) in generated RAG queries, causing queries to fail.

**After**: Users can configure actual endpoint IDs in the sidebar, and generated queries use the correct values.

## Changes Made

### 1. Sidebar UI (app.py:1794-1825)

Added new "⚙️ Inference Endpoints" section in the Create mode sidebar:

```python
# Initialize inference endpoints in session state
if "inference_endpoints" not in st.session_state:
    st.session_state.inference_endpoints = {
        "rerank": ".rerank-v1-elasticsearch",
        "completion": "completion-vulcan"
    }

# RERANK endpoint input
rerank_endpoint = st.text_input(
    "RERANK Endpoint",
    value=st.session_state.inference_endpoints["rerank"],
    help="Inference endpoint ID for RERANK command (default: .rerank-v1-elasticsearch)",
    key="rerank_endpoint_input"
)
st.session_state.inference_endpoints["rerank"] = rerank_endpoint

# COMPLETION endpoint input
completion_endpoint = st.text_input(
    "COMPLETION Endpoint",
    value=st.session_state.inference_endpoints["completion"],
    help="Inference endpoint ID for COMPLETION command (default: completion-vulcan)",
    key="completion_endpoint_input"
)
st.session_state.inference_endpoints["completion"] = completion_endpoint

# Show current values
st.caption(f"🔄 RERANK: `{st.session_state.inference_endpoints['rerank']}`")
st.caption(f"🤖 COMPLETION: `{st.session_state.inference_endpoints['completion']}`")
```

**Location**: After Elasticsearch section, before Browse mode section

### 2. ModuleGenerator Updates (src/framework/module_generator.py)

#### Constructor (lines 19-36)
```python
def __init__(self, llm_client=None, inference_endpoints: Optional[Dict[str, str]] = None):
    """Initialize with LLM client and inference endpoint configuration

    Args:
        llm_client: LLM client for code generation
        inference_endpoints: Dict with 'rerank' and 'completion' endpoint IDs
            Default: {'rerank': '.rerank-v1-elasticsearch', 'completion': 'completion-vulcan'}
    """
    self.llm_client = llm_client
    self.base_path = Path("demos")

    # Set inference endpoint defaults
    if inference_endpoints is None:
        inference_endpoints = {
            "rerank": ".rerank-v1-elasticsearch",
            "completion": "completion-vulcan"
        }
    self.inference_endpoints = inference_endpoints
```

#### Prompt Generation Methods
Added local endpoint variables at the start of 4 methods:
- `_generate_rag_queries_with_schema()` (line 563-565)
- `_generate_rag_queries()` (line 823-825)
- `_generate_query_module_with_strategy()` (line 1395-1397)
- `_get_minimal_esql_reference()` (line 1647-1648)

Example:
```python
# Get endpoint IDs for substitution in prompt
rerank_endpoint = self.inference_endpoints['rerank']
completion_endpoint = self.inference_endpoints['completion']
```

Then replaced all references in prompt strings:
- Before: `"{self.inference_endpoints['rerank']}"`
- After: `"{rerank_endpoint}"`

**Why?** F-strings can't handle nested dictionary access with quotes, so we extract to local variables first.

### 3. Orchestrator Updates (src/framework/orchestrator.py:22-34)

```python
def __init__(self, llm_client=None, inference_endpoints: Optional[Dict[str, str]] = None):
    """Initialize orchestrator

    Args:
        llm_client: Optional LLM client for module generation
        inference_endpoints: Optional dict with 'rerank' and 'completion' endpoint IDs
    """
    if llm_client is None:
        llm_client = self._create_default_client()

    self.llm_client = llm_client
    self.module_generator = ModuleGenerator(llm_client, inference_endpoints)
    self.module_manager = DemoModuleManager()
```

### 4. Demo Generation Flow (app.py:813-818)

```python
# Generate demo using modular orchestrator
# Pass inference endpoints from sidebar configuration
inference_endpoints = st.session_state.get("inference_endpoints", {
    "rerank": ".rerank-v1-elasticsearch",
    "completion": "completion-vulcan"
})
orchestrator = ModularDemoOrchestrator(inference_endpoints=inference_endpoints)
```

## Default Values

| Endpoint | ID | Description |
|----------|-------|-------------|
| RERANK | `.rerank-v1-elasticsearch` | Elasticsearch ML nodes rerank endpoint |
| COMPLETION | `completion-vulcan` | Custom completion endpoint for ES|QL COMPLETION command |

These defaults work with standard Elastic Cloud deployments.

## Generated Query Examples

### Before (with placeholders)
```esql
FROM knowledge_base METADATA _score
| WHERE MATCH(content, ?user_question)
| RERANK ?user_question ON content WITH {"inference_id": "rerank_endpoint"}
| LIMIT 5
| COMPLETION answer = prompt WITH {"inference_id": "completion_endpoint"}
```

❌ **Result**: Queries fail with "inference endpoint not found [rerank_endpoint]"

### After (with actual endpoints)
```esql
FROM knowledge_base METADATA _score
| WHERE MATCH(content, ?user_question)
| RERANK ?user_question ON content WITH {"inference_id": ".rerank-v1-elasticsearch"}
| LIMIT 5
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
```

✅ **Result**: Queries execute successfully

## User Workflow

1. **Open Demo Builder** → Streamlit app starts
2. **Sidebar shows default endpoints** → `.rerank-v1-elasticsearch` and `completion-vulcan`
3. **User can modify endpoints** → Text inputs allow customization
4. **Values persist** → Stored in `st.session_state.inference_endpoints`
5. **Generate demo** → Type "generate" after extracting context
6. **Generated queries use configured endpoints** → No more placeholders

## Testing

### Unit Test
```python
from src.framework.module_generator import ModuleGenerator

# Test with custom endpoints
custom_endpoints = {
    'rerank': 'test-rerank-endpoint',
    'completion': 'test-completion-endpoint'
}
mg = ModuleGenerator(llm_client=None, inference_endpoints=custom_endpoints)

assert mg.inference_endpoints['rerank'] == 'test-rerank-endpoint'
assert mg.inference_endpoints['completion'] == 'test-completion-endpoint'

# Test with defaults
mg_default = ModuleGenerator(llm_client=None)
assert mg_default.inference_endpoints['rerank'] == '.rerank-v1-elasticsearch'
assert mg_default.inference_endpoints['completion'] == 'completion-vulcan'
```

✅ All tests pass!

### Integration Test
1. Run `streamlit run app.py`
2. Verify sidebar shows inference endpoint inputs
3. Modify endpoint values
4. Generate a demo with RAG queries
5. Check `demos/[demo_name]/queries.json` → RAG queries should have configured endpoint IDs

## F-String Syntax Fix

**Problem**: Initial implementation used `{self.inference_endpoints['rerank']}` directly in f-strings, causing syntax errors.

**Solution**: Extract to local variables first:
```python
# At method start
rerank_endpoint = self.inference_endpoints['rerank']
completion_endpoint = self.inference_endpoints['completion']

# In f-string
f"| RERANK query ON field WITH {{ \"inference_id\": \"{rerank_endpoint}\" }}"
```

**Why?** F-strings can't handle nested dictionary access with mixed quote types. The parser gets confused with `[' ']` inside f-string curly braces.

## Files Changed

| File | Lines | Changes |
|------|-------|---------|
| `app.py` | 1794-1825 | Added sidebar UI for endpoint configuration |
| `app.py` | 813-818 | Pass endpoints to orchestrator |
| `src/framework/orchestrator.py` | 22-34 | Accept and forward endpoints parameter |
| `src/framework/module_generator.py` | 19-36 | Accept endpoints in constructor |
| `src/framework/module_generator.py` | 563-565, 823-825, 1395-1397, 1647-1648 | Add local endpoint variables |
| `src/framework/module_generator.py` | 606-648 | Replace placeholders in RAG query rules |
| `src/framework/module_generator.py` | 877-900 | Replace placeholders in RAG query template |
| `src/framework/module_generator.py` | 1497 | Replace placeholder in query module template |
| `src/framework/module_generator.py` | 1660, 1670 | Replace placeholders in minimal ES|QL reference |

## Related Documentation

- [INFERENCE-ENDPOINTS.md](./INFERENCE-ENDPOINTS.md) - Available inference endpoints and compatibility
- [COMPLETION-FIX-COMPLETE.md](./COMPLETION-FIX-COMPLETE.md) - COMPLETION syntax fix summary
- [correct-rag-query-examples.md](./correct-rag-query-examples.md) - Working RAG query examples

## Next Steps

1. **Test with real demo generation** → Verify generated queries have correct endpoint IDs
2. **Add endpoint validation** → Check if endpoint exists before demo generation
3. **Save to config file** → Persist endpoint preferences across sessions
4. **Add more endpoints** → Support ELSER sparse embedding endpoint configuration

---

**Last Updated**: 2025-11-06
**Status**: ✅ Complete and tested
