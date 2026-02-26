# Correct RAG Query Examples (MATCH → RERANK → COMPLETION)

## Overview

This document shows **correct** ES|QL syntax for RAG queries using MATCH, RERANK, and COMPLETION commands for the UnitedHealth call center use case.

## ❌ Common Mistakes to Avoid

1. **Using MATCH as a pipe command** → `| MATCH field query` ❌
   - CORRECT: `WHERE MATCH(field, "query")` ✅

2. **Missing ON keyword in RERANK** → `| RERANK field query` ❌
   - CORRECT: `| RERANK "query" ON field WITH { "inference_id" : "..." }` ✅

3. **Using MODEL keyword** → `| COMPLETION prompt MODEL "gpt-4"` ❌
   - CORRECT: `| COMPLETION prompt WITH { "inference_id" : "..." }` ✅

4. **Using template syntax** → `{{#results}}` ❌
   - CORRECT: Use `EVAL` + `CONCAT()` to build prompts ✅

## Healthcare Call Center RAG Queries

### 1. Knowledge Base Search (MATCH only - No COMPLETION)

**Use Case**: Agent searches for insurance term explanations

**Query**:
```esql
FROM knowledge_base
| WHERE MATCH(content, ?user_question, {"fuzziness": "AUTO"})
| SORT _score DESC
| LIMIT 10
| KEEP article_id, title, content, category, subcategory, _score
```

**Parameters**:
```json
[
  {
    "name": "user_question",
    "type": "string",
    "description": "Customer's question (e.g., 'What is prior authorization?')"
  }
]
```

**Test with**:
- user_question: "prior authorization"
- user_question: "denial codes"

---

### 2. Knowledge Base with AI Summary (MATCH → COMPLETION)

**Use Case**: Agent gets AI-explained answer to customer question

**Query**:
```esql
FROM knowledge_base
| WHERE MATCH(content, ?user_question)
| SORT _score DESC
| LIMIT 5
| EVAL prompt = CONCAT(
    "You are a helpful insurance expert. Based on this article, explain in simple terms: ",
    ?user_question, " ",
    "Article: ", title, " ",
    "Content: ", content, " ",
    "Provide a clear explanation a call center agent can use:"
  )
| COMPLETION answer = prompt WITH { "inference_id" : "openai_gpt4" }
| KEEP title, content, answer, _score
```

**Note**: This generates 5 LLM API calls (one per row). Use LIMIT carefully!

---

### 3. Similar Case Lookup (MATCH → RERANK)

**Use Case**: Find similar resolved cases for agent guidance

**Query**:
```esql
FROM call_center_interactions METADATA _score
| WHERE MATCH(notes, ?issue_description)
  AND resolution_status == "Resolved"
  AND first_call_resolution == true
| SORT _score DESC
| LIMIT 100
| RERANK ?issue_description ON notes WITH { "inference_id" : "cohere_rerank" }
| LIMIT 10
| LOOKUP JOIN agents ON agent_id
| KEEP interaction_id, call_type, issue_category, notes, call_duration_seconds, agent_name, specialization, _score
```

**Parameters**:
```json
[
  {
    "name": "issue_description",
    "type": "string",
    "description": "Description of the customer issue"
  }
]
```

---

### 4. Full RAG Pipeline (MATCH → RERANK → COMPLETION)

**Use Case**: Agent gets AI-generated guidance based on similar cases

**Query**:
```esql
FROM call_center_interactions METADATA _score
| WHERE MATCH(notes, ?issue_description)
  AND resolution_status == "Resolved"
  AND first_call_resolution == true
| SORT _score DESC
| LIMIT 50
| RERANK ?issue_description ON notes WITH { "inference_id" : "cohere_rerank" }
| LIMIT 3
| LOOKUP JOIN agents ON agent_id
| EVAL prompt = CONCAT(
    "You are an experienced call center supervisor. Based on these similar resolved cases, provide guidance for handling: ",
    ?issue_description, " ",
    "Similar Case: ", notes, " ",
    "Agent: ", agent_name, " (", specialization, ") ",
    "Call Duration: ", TO_STRING(call_duration_seconds), " seconds ",
    "Resolution Status: ", resolution_status, " ",
    "Provide specific actionable guidance:"
  )
| COMPLETION guidance = prompt WITH { "inference_id" : "openai_gpt4" }
| KEEP interaction_id, issue_category, notes, agent_name, guidance, _score
```

**Note**: Generates 3 LLM API calls. Pipeline: MATCH (50) → RERANK (3) → COMPLETION (3)

---

### 5. Prior Authorization Guidance (MATCH → COMPLETION)

**Use Case**: Agent gets help explaining denial reasons

**Query**:
```esql
FROM prior_authorizations METADATA _score
| WHERE MATCH(denial_reason, ?denial_query)
  AND status IN ("Denied", "Pending")
| SORT _score DESC
| LIMIT 5
| LOOKUP JOIN members ON member_id
| LOOKUP JOIN providers ON provider_id
| EVAL prompt = CONCAT(
    "You are a prior authorization specialist. Explain this denial to a customer. ",
    "Medication: ", medication_name, " ",
    "Denial Reason: ", denial_reason, " ",
    "Plan Type: ", plan_type, " ",
    "Provider: ", provider_name, " (", specialty, ") ",
    "Urgency: ", urgency_flag, " ",
    "Customer asks: ", ?denial_query, " ",
    "Provide a clear explanation including: ",
    "1. Why it was denied ",
    "2. Next steps for the customer ",
    "3. Alternative options if available ",
    "4. Expected timeline"
  )
| COMPLETION explanation = prompt WITH { "inference_id" : "openai_gpt4" }
| KEEP auth_id, medication_name, denial_reason, plan_type, provider_name, explanation, _score
```

---

### 6. Simple Semantic Search (MATCH only - for testing)

**Use Case**: Basic search without AI, good for testing MATCH syntax

**Query**:
```esql
FROM provider_directory METADATA _score
| WHERE MATCH(provider_profile, ?search_query)
  AND accepting_new_patients == true
| SORT _score DESC
| LIMIT 10
| KEEP provider_id, provider_name, specialty, city, state, phone, _score
```

**Test with**:
- search_query: "cardiologist with hospital affiliation"
- search_query: "pediatrics speaks Spanish"

---

## Key Syntax Rules

### MATCH (Always in WHERE clause)
```esql
✅ WHERE MATCH(field, "query")
✅ WHERE MATCH(field, ?parameter)
✅ WHERE MATCH(field, ?param, {"fuzziness": "AUTO"})
❌ | MATCH field "query"
❌ | MATCH field, query
```

### RERANK (Pipe command with ON and WITH)
```esql
✅ | RERANK "query" ON field WITH { "inference_id" : "endpoint" }
✅ | RERANK ?param ON field1, field2 WITH { "inference_id" : "endpoint" }
✅ | RERANK score = "query" ON field WITH { "inference_id" : "endpoint" }
❌ | RERANK field "query"
❌ | RERANK "query" ON field MODEL "model"
```

### COMPLETION (Pipe command with WITH)
```esql
✅ | COMPLETION prompt WITH { "inference_id" : "endpoint" }
✅ | COMPLETION answer = prompt WITH { "inference_id" : "endpoint" }
✅ | EVAL prompt = CONCAT("text: ", field) | COMPLETION answer = prompt WITH ...
❌ | COMPLETION "text" MODEL "gpt-4"
❌ | COMPLETION prompt (without WITH)
❌ Using {{templates}} syntax
```

### Building Prompts
```esql
✅ | EVAL prompt = CONCAT("Question: ", title, " Answer: ", content)
✅ | EVAL prompt = CONCAT("Explain: ", field1, " Context: ", field2)
❌ | EVAL prompt = CONCAT("Line one\nLine two") — newlines cause parsing_exception
❌ | COMPLETION "{{#results}} {{title}} {{/results}}"
```

### String Literals (CRITICAL)
ES|QL does NOT support newlines or escape sequences in string literals.
```esql
✅ "simple single-line string"
✅ CONCAT("Part one. ", "Part two. ", "Field: ", field)
❌ "Line one\nLine two"  — causes parsing_exception
❌ "Line one\\nLine two" — causes parsing_exception
❌ Strings spanning multiple lines
❌ 'single quotes'        — only double quotes
```

## Cost Optimization Tips

1. **Filter Before COMPLETION**: Use WHERE to reduce rows
2. **Use LIMIT Aggressively**: Start with 3-5 rows
3. **RERANK Before COMPLETION**: Narrow to most relevant docs
4. **Test Without COMPLETION**: Validate MATCH/RERANK first
5. **Consider RERANK-only**: Often sufficient without COMPLETION

## Testing Strategy

### Phase 1: Test MATCH
```esql
FROM index
| WHERE MATCH(field, ?param)
| LIMIT 10
```

### Phase 2: Add RERANK
```esql
FROM index
| WHERE MATCH(field, ?param)
| LIMIT 50
| RERANK ?param ON field WITH { "inference_id" : "rerank" }
| LIMIT 5
```

### Phase 3: Add COMPLETION (Small LIMIT!)
```esql
FROM index
| WHERE MATCH(field, ?param)
| LIMIT 50
| RERANK ?param ON field WITH { "inference_id" : "rerank" }
| LIMIT 3
| EVAL prompt = CONCAT("...", field)
| COMPLETION answer = prompt WITH { "inference_id" : "completion" }
```

## Prerequisites

Before using these queries, ensure:

1. **Inference Endpoints Configured**:
   - Rerank endpoint (e.g., `cohere_rerank`)
   - Completion endpoint (e.g., `openai_gpt4`)

2. **Semantic Text Fields**:
   - Fields used in MATCH should be `text` or `semantic_text` type
   - Example: `content`, `notes`, `provider_profile`

3. **METADATA _score**:
   - Add `METADATA _score` after FROM to access relevance scores
   - Required for sorting by relevance

4. **Lookup Indices**:
   - Reference tables (members, providers, agents) must be in `lookup` mode
   - Use LOOKUP JOIN to enrich results

## References

- **ES|QL MATCH**: `docs/esql/search-and-filter.md`
- **ES|QL RERANK**: `docs/esql/rerank.md`
- **ES|QL COMPLETION**: `docs/esql/completion.md`
- **Syntax Rules**: `src/prompts/esql_syntax_rules.py`
