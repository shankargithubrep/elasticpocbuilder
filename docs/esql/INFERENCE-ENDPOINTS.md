# Elastic Inference Endpoints - Default Configuration

## Available Endpoints (Preconfigured)

Based on your Elastic Cloud deployment, these endpoints are available by default:

| Endpoint ID | Service | Type | Task Type | Use Case |
|-------------|---------|------|-----------|----------|
| `.elser-2-elastic` | Elastic Inference Service (GPU) | `sparse_embedding` | N/A | Semantic search (ELSER v2) |
| `.elser-2-elasticsearch` | Elasticsearch (ML Nodes) | `sparse_embedding` | N/A | Semantic search (ELSER v2) |
| `.multilingual-e5-small-elasticsearch` | Elasticsearch (ML Nodes) | `text_embedding` | N/A | Dense vector embeddings |
| `.rainbow-sprinkles-elastic` | Elastic Inference Service (GPU) | `chat_completion` | **chat_completion** | ⚠️ Not compatible with COMPLETION |
| `.rerank-v1-elasticsearch` | Elasticsearch (ML Nodes) | `rerank` | rerank | ✅ Use for RERANK command |

## Important: COMPLETION Command Limitation

⚠️ **CRITICAL**: The COMPLETION command requires task type `completion`, **not** `chat_completion`.

**Problem**:
- `.rainbow-sprinkles-elastic` is `chat_completion` (for conversational AI)
- ES|QL COMPLETION requires `completion` (for text generation)

**Error Message**:
```
cannot use inference endpoint [.rainbow-sprinkles-elastic] with task type [chat_completion]
within a Completion command. Only inference endpoints with the task type [completion] are supported.
```

**Solution**:
You need to create a custom inference endpoint with task type `completion`. See [Creating Completion Endpoint](#creating-completion-endpoint) below.

## Working Configurations

### ✅ MATCH (No Inference Needed)

```esql
FROM provider_directory METADATA _score
| WHERE MATCH(provider_profile, ?search_query)
| SORT _score DESC
| LIMIT 10
```

**Status**: Works perfectly - no inference endpoint needed

---

### ✅ RERANK (Use .rerank-v1-elasticsearch)

```esql
FROM provider_directory METADATA _score
| WHERE MATCH(provider_profile, ?search_query)
| SORT _score DESC
| LIMIT 50
| RERANK ?search_query ON provider_profile
  WITH { "inference_id" : ".rerank-v1-elasticsearch" }
| LIMIT 10
```

**Status**: Endpoint available - may timeout on large datasets

**Note**: RERANK can be slow. Use smaller LIMIT before RERANK.

---

### ❌ COMPLETION (No Compatible Endpoint Available)

```esql
FROM provider_directory
| LIMIT 3
| EVAL prompt = CONCAT("Describe: ", provider_name)
| COMPLETION answer = prompt
  WITH { "inference_id" : ".rainbow-sprinkles-elastic" }  -- ❌ Won't work
```

**Status**: Not available - `.rainbow-sprinkles-elastic` is incompatible

**Error**: Endpoint is `chat_completion`, need `completion`

---

## Recommended Query Patterns

### Pattern 1: MATCH Only (No Inference)
**Use Case**: Fast semantic search, no LLM needed

```esql
FROM knowledge_base METADATA _score
| WHERE MATCH(content, ?user_question)
| SORT _score DESC
| LIMIT 10
| KEEP article_id, title, content, _score
```

**Pros**:
- ✅ Fast
- ✅ No inference costs
- ✅ Works out of the box

---

### Pattern 2: MATCH + RERANK (Recommended)
**Use Case**: Higher quality relevance ranking

```esql
FROM knowledge_base METADATA _score
| WHERE MATCH(content, ?user_question)
| SORT _score DESC
| LIMIT 100
| RERANK ?user_question ON title, content
  WITH { "inference_id" : ".rerank-v1-elasticsearch" }
| LIMIT 5
| KEEP article_id, title, content, _score
```

**Pros**:
- ✅ Better relevance than MATCH alone
- ✅ Available endpoint
- ✅ No per-row LLM costs

**Cons**:
- ⚠️ May timeout on large datasets
- ⚠️ Slower than MATCH alone

---

### Pattern 3: MATCH + RERANK + COMPLETION (Not Currently Available)
**Use Case**: LLM-generated summaries/answers

```esql
FROM knowledge_base METADATA _score
| WHERE MATCH(content, ?user_question)
| SORT _score DESC
| LIMIT 100
| RERANK ?user_question ON title, content
  WITH { "inference_id" : ".rerank-v1-elasticsearch" }
| LIMIT 3
| EVAL prompt = CONCAT("Q: ", ?user_question, " A: ", content)
| COMPLETION answer = prompt
  WITH { "inference_id" : "YOUR_COMPLETION_ENDPOINT" }  -- Need to create this
| KEEP title, content, answer
```

**Status**: ❌ Requires custom completion endpoint

---

## Creating Completion Endpoint

To use the COMPLETION command, you need to create an inference endpoint with task type `completion`:

### Option 1: OpenAI/Azure OpenAI

```bash
PUT _inference/completion/my-openai-completion
{
  "service": "openai",
  "service_settings": {
    "api_key": "YOUR_API_KEY",
    "model_id": "gpt-4"
  }
}
```

### Option 2: Azure OpenAI

```bash
PUT _inference/completion/my-azure-completion
{
  "service": "azureopenai",
  "service_settings": {
    "api_key": "YOUR_API_KEY",
    "resource_name": "YOUR_RESOURCE",
    "deployment_id": "YOUR_DEPLOYMENT",
    "api_version": "2024-02-01"
  }
}
```

### Option 3: Elastic Inference (if available)

Check with your Elastic account team if completion endpoints are available on Elastic Inference Service.

---

## Hardcoded Defaults for Demo Builder

Based on current availability, the demo builder should use:

### For RAG Queries (generate_rag_queries):

```python
# Default inference endpoints
RERANK_ENDPOINT = ".rerank-v1-elasticsearch"
COMPLETION_ENDPOINT = None  # Not available - skip COMPLETION in generated queries

# Generate MATCH + RERANK queries (no COMPLETION)
queries.append({
    "type": "rag",
    "name": "Knowledge Base Search",
    "esql": """FROM knowledge_base METADATA _score
| WHERE MATCH(content, ?user_question)
| SORT _score DESC
| LIMIT 100
| RERANK ?user_question ON title, content
  WITH { "inference_id" : ".rerank-v1-elasticsearch" }
| LIMIT 10
| KEEP article_id, title, content, _score""",
    "parameters": [
        {
            "name": "user_question",
            "type": "string",
            "description": "User's question"
        }
    ]
})
```

### For Sparse Embeddings (semantic_text fields):

```python
SPARSE_EMBEDDING_ENDPOINT = ".elser-2-elastic"  # GPU-based, faster
# OR
SPARSE_EMBEDDING_ENDPOINT = ".elser-2-elasticsearch"  # ML nodes
```

---

## Testing Strategy

### Phase 1: Test MATCH ✅
```esql
FROM provider_directory METADATA _score
| WHERE MATCH(provider_profile, "cardiologist")
| LIMIT 5
```
**Result**: Works perfectly

### Phase 2: Test RERANK ⚠️
```esql
FROM provider_directory METADATA _score
| WHERE MATCH(provider_profile, "cardiologist")
| LIMIT 20
| RERANK "cardiologist with hospital experience" ON provider_profile
  WITH { "inference_id" : ".rerank-v1-elasticsearch" }
| LIMIT 5
```
**Result**: May timeout - use smaller datasets

### Phase 3: COMPLETION ❌
**Status**: Cannot test - no compatible endpoint

**Recommendation**: Generate queries without COMPLETION for now

---

## Summary

| Feature | Status | Endpoint | Notes |
|---------|--------|----------|-------|
| MATCH | ✅ Works | N/A | No inference needed |
| RERANK | ⚠️ Available | `.rerank-v1-elasticsearch` | May timeout |
| COMPLETION | ❌ Not Available | N/A | Need `completion` endpoint |
| Sparse Embeddings | ✅ Works | `.elser-2-elastic` | For semantic_text fields |

**Recommendation for Demo Builder**:
- Generate MATCH + RERANK queries only
- Skip COMPLETION until custom endpoint is configured
- Document that COMPLETION requires additional setup

---

## Next Steps

1. **Short-term**: Generate RAG queries with MATCH + RERANK (no COMPLETION)
2. **Medium-term**: Test RERANK performance with actual datasets
3. **Long-term**: Set up completion endpoint for full MATCH → RERANK → COMPLETION pipeline

---

**Last Updated**: Based on inference endpoints available in your Elastic Cloud deployment
