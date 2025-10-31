# RAG/Search Architecture Strategy

**Version:** 1.2
**Date:** 2025-10-30
**Status:** Phase 1 Complete ✅ | Phase 2-4 Pending

## Implementation Status

**✅ Phase 1: COMPLETE** (Commit: e3826e7)
- Framework enhancements (base.py, module_generator.py, module_loader.py)
- RAG field analyzer (search_strategy_generator.py)
- UI with tabbed query display (app.py)
- Comprehensive test suite (test_query_architecture.py - 6/6 passing)
- All three query types generated: Scripted, Parameterized, RAG

**⏳ Phase 2: Pending** - LLM-powered query refinement and iteration
**⏳ Phase 3: Pending** - Enhanced search strategy detection
**⏳ Phase 4: Pending** - Advanced Agent Builder integration

## Overview

This document outlines the dual-track query architecture for the Demo Builder platform, enabling both **scripted demonstrations** (non-parameterized queries) and **Agent Builder tool definitions** (parameterized RAG queries).

**IMPORTANT CLARIFICATIONS:**
- Parameterized queries (`?syntax`) are NOT for REST API use
- They are designed for Agent Builder ES|QL tools: https://www.elastic.co/docs/solutions/search/agent-builder/tools/esql-tools
- This phase focuses on GENERATING tool-ready queries, not executing them
- Agent Builder integration (v2) will handle execution

## The Problem

**Current State:**
- Demos generate only pre-scripted ES|QL queries
- Limited to scenarios we anticipate at generation time
- No way to explore "what if?" questions during demos
- Cannot showcase real-time AI-powered analysis

**Desired State:**
- Maintain high-quality scripted queries for known scenarios
- Add parameterized queries for open-ended exploration
- Enable Agent Builder tool calls for interactive demos
- Showcase MATCH → RERANK → COMPLETION pipeline

## Architecture

### Dual-Track Query System

```
Demo Generation
    │
    ├─► Track 1: SCRIPTED QUERIES (existing, enhanced)
    │   │
    │   ├─── Non-parameterized ES|QL queries
    │   ├─── Solve specific customer pain points
    │   ├─── Tested and validated
    │   └─── Serve as base for parameterized versions
    │
    └─► Track 2: PARAMETERIZED QUERIES (new)
        │
        ├─── Auto-generated from Track 1 queries
        ├─── Use ?parameter syntax for user input
        ├─── Enable Agent Builder tool calls
        └─── Support open-ended exploration
```

### Three-Tier RAG Pipeline

```
User Question (via Agent Builder)
    ↓
1. MATCH/MATCH_PHRASE
   - Semantic text search
   - Initial retrieval (100+ documents)
   - Fast, broad coverage
   - Can query multiple indices: FROM index1,index2,index-*
    ↓
2. RERANK (optional, use at least once per demo)
   - ML-based relevance scoring
   - Refine to top 5-10 documents
   - Cross-encoder models
    ↓
3. INLINE STATS (not STATS - preserves fields!)
   - Aggregate context without destroying fields
   - STATS is destructive (removes non-aggregated fields)
   - Use INLINE STATS to keep all needed fields
    ↓
4. COMPLETION
   - LLM generates natural language answer
   - Context from reranked documents
   - Personalized to user's question
    ↓
Result: AI-generated answer with sources
```

**CRITICAL: STATS vs INLINE STATS**
- `STATS` removes all fields not in the aggregation → breaks downstream COMPLETION
- `INLINE STATS` preserves original fields → safe to use before COMPLETION
- Example: `INLINE STATS context = MV_CONCAT(description, "\n")` keeps all fields

## Query Types

### Type 1: Scripted Queries (Non-Parameterized)

**Purpose:** Demonstrate specific, known scenarios with validated results

**Example:**
```python
{
    "query_type": "scripted",
    "name": "high_severity_incidents_last_week",
    "description": "Show all P1/P2 incidents from the past 7 days",
    "esql": """
        FROM support_tickets
        | WHERE severity IN ("P1", "P2")
            AND @timestamp >= NOW() - 7 days
        | STATS
            count = COUNT(*),
            avg_resolution = AVG(resolution_time)
          BY priority, region
        | SORT count DESC
    """,
    "tested": True,
    "expected_results": "~50 rows, avg_resolution ~4.2 hours"
}
```

**Characteristics:**
- Hard-coded values
- Fully tested and validated
- Predictable results
- Used in scripted demo flow

### Type 2: Parameterized Queries (User Input)

**Purpose:** Enable exploration and Agent Builder tool calls

**Example:**
```python
{
    "query_type": "parameterized",
    "name": "search_incidents_by_criteria",
    "description": "Search incidents by severity, date range, or region",
    "esql": """
        FROM support_tickets
        | WHERE severity IN ?severities
            AND @timestamp >= ?start_date
            AND @timestamp < ?end_date
            AND region == ?region
        | STATS
            count = COUNT(*),
            avg_resolution = AVG(resolution_time)
          BY priority, region
        | SORT count DESC
    """,
    "parameters": {
        "severities": {
            "type": "keyword[]",
            "description": "Severity levels to include",
            "default": ["P1", "P2"],
            "required": True
        },
        "start_date": {
            "type": "date",
            "description": "Start of date range",
            "default": "NOW() - 7 days",
            "required": True
        },
        "end_date": {
            "type": "date",
            "description": "End of date range",
            "default": "NOW()",
            "required": True
        },
        "region": {
            "type": "keyword",
            "description": "Geographic region",
            "default": "US-WEST",
            "required": False
        }
    },
    "base_query": "high_severity_incidents_last_week",
    "tested_via_base": True
}
```

**Characteristics:**
- Uses `?parameter` syntax
- Derived from tested scripted queries
- Enables user input
- Maps to Agent Builder tools

### Type 3: RAG Queries (Semantic Search + LLM)

**Purpose:** Answer open-ended questions with AI-generated responses

**Example:**
```python
{
    "query_type": "rag",
    "name": "semantic_incident_search",
    "description": "Ask questions about incidents and get AI-powered answers",
    "esql": """
        FROM support_tickets METADATA _score
        | WHERE MATCH(description, ?user_question)
            OR MATCH(customer_feedback, ?user_question)
        | WHERE @timestamp >= NOW() - 120 days
        | SORT _score DESC
        | LIMIT 100
        | RERANK ?user_question ON description, customer_feedback, resolution_notes
            WITH {{"inference_id": "{rerank_endpoint}"}}
        | LIMIT 5
        | EVAL context = CONCAT(
            "Ticket #", ticket_id, " (", severity, "): ",
            description, " | Resolution: ", resolution_notes
          )
        | STATS all_context = MV_CONCAT(context, "\\n\\n")
        | EVAL prompt = CONCAT(
            "Based on these support tickets:\\n\\n",
            all_context,
            "\\n\\nQuestion: ", ?user_question,
            "\\n\\nProvide a detailed answer with specific examples:"
          )
        | COMPLETION answer = prompt
            WITH {{"inference_id": "{completion_endpoint}"}}
        | KEEP answer, all_context
    """,
    "parameters": {
        "user_question": {
            "type": "string",
            "description": "The question to answer about incidents",
            "required": True,
            "example": "What are customers saying about performance issues?"
        }
    },
    "search_fields": ["description", "customer_feedback", "resolution_notes"],
    "rerank_fields": ["description", "customer_feedback", "resolution_notes"],
    "time_boundary": "120 days",
    "agent_builder_tool": {
        "tool_name": "search_support_incidents",
        "tool_description": "Search support incidents and get AI-powered answers to questions about customer issues, trends, and resolutions"
    }
}
```

**Characteristics:**
- Combines MATCH + RERANK + COMPLETION
- Semantic search on text fields
- LLM-generated natural language answers
- Perfect for Agent Builder integration
- Answers questions not anticipated at demo creation time

## Implementation Strategy

### Phase 1: Query Module Enhancement

**Update `src/framework/base.py`:**

```python
class QueryGeneratorModule(ABC):
    """Base class for query generation"""

    @abstractmethod
    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate scripted (non-parameterized) queries"""
        pass

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized versions of scripted queries

        Default: Auto-convert scripted queries to parameterized versions
        Can be overridden for custom parameter mappings
        """
        scripted_queries = self.generate_queries()
        return self._auto_parameterize_queries(scripted_queries)

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries for semantic search + LLM completion

        Analyzes dataset schema to identify:
        - Text fields for MATCH
        - Fields for RERANK
        - Temporal boundaries
        - Context fields for COMPLETION
        """
        return self._generate_rag_templates()

    def _auto_parameterize_queries(self, queries: List[Dict]) -> List[Dict]:
        """Convert scripted queries to parameterized versions"""
        # Implementation: Extract hard-coded values and replace with ?params
        pass

    def _generate_rag_templates(self) -> List[Dict]:
        """Generate MATCH → RERANK → COMPLETION templates"""
        # Implementation: Analyze schema and create RAG query templates
        pass
```

### Phase 2: LLM-Powered Module Generation

**Update `src/framework/module_generator.py`:**

Add to query generator prompt:

```python
prompt = f"""Generate a Python module that implements QueryGeneratorModule.

IMPORTANT: Generate THREE types of queries:

1. SCRIPTED QUERIES (generate_queries method):
   - Specific, tested ES|QL queries solving known problems
   - Hard-coded values (no parameters)
   - Address customer pain points: {', '.join(config['pain_points'])}
   - Example: "high_priority_incidents" with fixed time range

2. PARAMETERIZED QUERIES (generate_parameterized_queries method):
   - Derived from scripted queries
   - Use ?parameter syntax for user input
   - Enable interactive exploration
   - Example: Same query but with ?start_date, ?end_date, ?severity params

3. RAG QUERIES (generate_rag_queries method):
   - MATCH for semantic text search
   - RERANK for ML-based relevance (optional)
   - COMPLETION for LLM-generated answers
   - Parameterized with ?user_question
   - Map to Agent Builder tool calls

ES|QL REFERENCE DOCS:
{include_esql_docs([
    'docs/esql/search-match.md',      # MATCH/MATCH_PHRASE
    'docs/esql/rerank.md',             # RERANK command
    'docs/esql/completion.md',         # COMPLETION command
    'docs/esql/metadata-fields.md'     # METADATA _score
])}

PARAMETERIZATION SYNTAX:
- Use ?param_name for user-provided values
- Provide params via REST API: {{"params": [{{"param_name": "value"}}]}}
- Example: WHERE field == ?value
- Example: BUCKET(date, ?timespan)

QUERY VALIDATION:
- Test scripted queries with generate_queries()
- Parameterized queries inherit trust from their base scripted query
- RAG queries are templates - validation happens at runtime

Generate the complete implementation with all three query types.
"""
```

### Phase 3: Search Strategy Detection

**Create `src/services/search_strategy_generator.py`:**

```python
class SearchStrategyGenerator:
    """Analyzes dataset schema to determine optimal search strategy"""

    def __init__(self, dataset_schema: Dict[str, Any]):
        self.schema = dataset_schema

    def identify_text_fields(self) -> List[str]:
        """Find text/keyword fields suitable for MATCH"""
        # Look for: description, summary, content, message, feedback, etc.
        pass

    def identify_rerank_fields(self) -> List[str]:
        """Find fields for RERANK (usually subset of text fields)"""
        # Select most important text fields (2-4 fields max)
        pass

    def identify_context_fields(self) -> List[str]:
        """Find fields to include in LLM context"""
        # All relevant fields: ID, status, priority, text, etc.
        pass

    def determine_time_boundary(self) -> str:
        """Determine appropriate time range (30/90/120 days)"""
        # Based on data volume and use case
        pass

    def generate_rag_template(self) -> Dict[str, Any]:
        """Create complete RAG query template"""
        text_fields = self.identify_text_fields()
        rerank_fields = self.identify_rerank_fields()
        context_fields = self.identify_context_fields()
        time_boundary = self.determine_time_boundary()

        return {
            "query_type": "rag",
            "search_fields": text_fields,
            "rerank_fields": rerank_fields,
            "context_fields": context_fields,
            "time_boundary": time_boundary,
            "template": self._build_rag_query(...)
        }
```

### Phase 4: UI Enhancement

**Update `app.py` - Demo Details View:**

Current structure:
```
Demo Details
├── Config
├── Data
├── Queries  ← ENHANCE THIS
└── Guide
```

New structure:
```
Demo Details
├── Config
├── Data
├── Queries
│   ├── Scripted Queries (non-parameterized)
│   └── Parameterized Queries
├── Tools  ← NEW
│   └── RAG Query Templates for Agent Builder
├── Agents  ← NEW
│   └── Agent Builder Tool Definitions (JSON export)
└── Guide
```

**Queries Tab Layout:**

```python
# In app.py demo details view

queries_tab, tools_tab, agents_tab = st.tabs([
    "📊 Queries",
    "🔧 Tools",
    "🤖 Agents"
])

with queries_tab:
    scripted_tab, param_tab = st.tabs([
        "Scripted (Non-Parameterized)",
        "Parameterized"
    ])

    with scripted_tab:
        st.markdown("**Tested queries for scripted demos**")
        for query in scripted_queries:
            with st.expander(f"🎯 {query['name']}"):
                st.code(query['esql'], language='sql')
                st.caption(query['description'])
                if query.get('tested'):
                    st.success("✓ Tested and validated")

    with param_tab:
        st.markdown("**Parameterized queries for interactive exploration**")
        for query in parameterized_queries:
            with st.expander(f"🔍 {query['name']}"):
                st.code(query['esql'], language='sql')
                st.caption(query['description'])

                # Show parameter definitions
                st.markdown("**Parameters:**")
                for param_name, param_def in query['parameters'].items():
                    st.markdown(f"- `?{param_name}` ({param_def['type']}): {param_def['description']}")

                # Link to base query
                if query.get('base_query'):
                    st.info(f"📎 Based on: `{query['base_query']}`")

with tools_tab:
    st.markdown("**RAG query templates for Agent Builder**")

    for rag_query in rag_queries:
        with st.expander(f"🤖 {rag_query['name']}"):
            st.code(rag_query['esql'], language='sql')

            # Show search strategy
            st.markdown("**Search Strategy:**")
            st.markdown(f"- **Text fields:** {', '.join(rag_query['search_fields'])}")
            st.markdown(f"- **Rerank fields:** {', '.join(rag_query['rerank_fields'])}")
            st.markdown(f"- **Time window:** {rag_query['time_boundary']}")

            # Show parameters
            st.markdown("**Parameters:**")
            for param_name, param_def in rag_query['parameters'].items():
                st.markdown(f"- `?{param_name}`: {param_def['description']}")
                if param_def.get('example'):
                    st.code(param_def['example'])

with agents_tab:
    st.markdown("**Agent Builder tool definitions (ready to import)**")

    # Generate Agent Builder JSON
    agent_tools = generate_agent_builder_tools(rag_queries)

    for tool in agent_tools:
        with st.expander(f"🛠️ {tool['name']}"):
            st.json(tool)

            # Copy button
            if st.button("📋 Copy to clipboard", key=tool['name']):
                st.code(json.dumps(tool, indent=2))

    # Export all tools
    if st.button("💾 Download All Tools (JSON)"):
        download_json(agent_tools, f"{demo_name}_agent_tools.json")
```

## Parameter Limitations & Constraints

**IMPORTANT:** ES|QL parameterization has known limitations:

### What Works with Parameters:
- ✅ Simple value comparisons: `WHERE field == ?value`
- ✅ Date ranges: `WHERE @timestamp >= ?start_date`
- ✅ MATCH queries: `WHERE MATCH(field, ?search_term)`
- ✅ BUCKET functions: `BUCKET(date_field, ?timespan)`
- ✅ Numeric comparisons: `WHERE price > ?min_price`

### What DOESN'T Work with Parameters:
- ❌ **LIKE operator**: `WHERE field LIKE ?pattern` (NOT SUPPORTED)
- ❌ **RLIKE operator**: `WHERE field RLIKE ?regex` (NOT SUPPORTED)
- ❌ Field names as parameters: `WHERE ?field_name == value` (NOT SUPPORTED)
- ❌ Index names as parameters: `FROM ?index_name` (NOT SUPPORTED)

**Source:** ES|QL tools are subject to current ES|QL language limitations. Named parameters do not currently work with LIKE and RLIKE operators.

### Multi-Index Queries (SUPPORTED):
ES|QL allows querying multiple indices in a single query:
```sql
-- Query multiple specific indices
FROM employees-00001, contractors-00002, vendors-*

-- Use wildcards for index patterns
FROM logs-*, metrics-*, traces-*
```

This is powerful for RAG queries that need to search across related datasets!

## Query Conversion Strategy

### LLM-Based Parameterization (NOT Auto-Conversion)

**Strategy:** Have LLM generate BOTH versions during the query-fixing iteration process.

**Why LLM-Based Instead of Auto-Conversion:**
- Parameterization is non-trivial (temporal expressions, nested JSON, etc.)
- LLM understands semantic meaning of values
- Avoids parameter limitations (LIKE, RLIKE not supported)
- Can generate meaningful parameter names and descriptions
- Leverages existing query-fixing iteration workflow

**How It Works:**

1. **Step 1:** LLM generates and tests scripted query
2. **Step 2:** After validation, LLM generates parameterized version
3. **Step 3:** Both versions saved, linked by `base_query` field

**Example Workflow:**
```python
# Iteration 1: Generate scripted query
scripted_query = {
    "name": "high_severity_incidents",
    "esql": """
        FROM support_tickets
        | WHERE severity IN ("P1", "P2")
        | WHERE @timestamp >= NOW() - 7 days
        | STATS count BY region
    """
}

# Validate → Test → Fix if needed

# Iteration 2: Generate parameterized version (AFTER validation)
parameterized_query = {
    "name": "search_incidents_by_severity",
    "esql": """
        FROM support_tickets
        | WHERE severity IN ?severities
        | WHERE @timestamp >= ?start_date
        | STATS count BY region
    """,
    "parameters": {
        "severities": {
            "type": "string[]",
            "description": "List of severity levels (P1, P2, P3, P4)",
            "default": ["P1", "P2"]
        },
        "start_date": {
            "type": "date",
            "description": "Start of time range",
            "default": "NOW() - 7 days"
        }
    },
    "base_query": "high_severity_incidents",  # Links to validated query
    "agent_builder_ready": True
}
```

**Key Benefits:**
- ✅ Trust inherited from validated scripted query
- ✅ LLM generates semantically meaningful parameters
- ✅ Avoids parameter limitations (no LIKE/RLIKE in parameterized version)
- ✅ No need to test parameterized queries separately
- ✅ Works with query-fixing iteration process

### Example Conversion

**Scripted Query:**
```sql
FROM support_tickets
| WHERE severity IN ("P1", "P2")
    AND @timestamp >= "2024-10-01"
    AND @timestamp < "2024-11-01"
    AND region == "US-WEST"
| STATS count = COUNT(*) BY priority
```

**Auto-Parameterized:**
```sql
FROM support_tickets
| WHERE severity IN ?severities
    AND @timestamp >= ?start_date
    AND @timestamp < ?end_date
    AND region == ?region
| STATS count = COUNT(*) BY priority
```

**Parameters:**
```json
{
  "severities": {
    "type": "keyword[]",
    "default": ["P1", "P2"],
    "required": true
  },
  "start_date": {
    "type": "date",
    "default": "2024-10-01",
    "required": true
  },
  "end_date": {
    "type": "date",
    "default": "2024-11-01",
    "required": true
  },
  "region": {
    "type": "keyword",
    "default": "US-WEST",
    "required": false
  }
}
```

## Agent Builder Integration

### Tool Definition Export

Generate Agent Builder tool definitions from RAG queries:

```json
{
  "tool_name": "search_support_incidents",
  "tool_description": "Search support incidents and get AI-powered answers about customer issues, trends, and resolutions",
  "tool_type": "esql_rag",
  "parameters": {
    "user_question": {
      "type": "string",
      "description": "Question to answer about support incidents",
      "required": true,
      "examples": [
        "What are customers saying about performance issues?",
        "Which regions have the most P1 incidents?",
        "What are common themes in customer complaints?"
      ]
    }
  },
  "query_template": "...",
  "expected_output": {
    "type": "completion",
    "fields": ["answer", "context"]
  },
  "search_strategy": {
    "retrieval": "MATCH on description, customer_feedback",
    "reranking": "ML-based on description, customer_feedback, resolution_notes",
    "generation": "LLM completion with context from top 5 results"
  }
}
```

### Demo → Agent Builder Workflow

1. **Generate demo** with scripted + RAG queries
2. **Review Tools tab** to see RAG templates
3. **Export to JSON** via Agents tab
4. **Import to Agent Builder** as tool definitions
5. **Use in conversations** - Agent calls tools with user questions

## Benefits

### For Demo Creators
- ✅ **No extra work** - Parameterized queries auto-generated
- ✅ **Trusted queries** - Inherit validation from scripted queries
- ✅ **RAG queries** - LLM generates based on schema analysis

### For Demo Presenters
- ✅ **Scripted flow** - Use non-parameterized queries for known scenarios
- ✅ **Handle questions** - Use parameterized queries for "what about...?"
- ✅ **Interactive exploration** - Use RAG queries for open-ended questions

### For Customers
- ✅ **See real capabilities** - MATCH + RERANK + COMPLETION in action
- ✅ **Ask their questions** - Not limited to pre-scripted scenarios
- ✅ **Experience Agent Builder** - See tools in action

### For Agent Builder
- ✅ **Ready-to-use tools** - Export and import tool definitions
- ✅ **Realistic data** - Tools work with actual demo datasets
- ✅ **Complete examples** - Show full RAG pipeline

## Implementation Checklist

### Framework Updates
- [ ] Update `src/framework/base.py` with new methods
- [ ] Update `src/framework/module_generator.py` with enhanced prompts
- [ ] Create `src/services/search_strategy_generator.py`
- [ ] Update `src/framework/module_loader.py` to load all query types

### Documentation
- [ ] Include `docs/esql/search-match.md` in LLM context
- [ ] Include `docs/esql/rerank.md` in LLM context
- [ ] Include `docs/esql/completion.md` in LLM context
- [ ] Include `docs/esql/metadata-fields.md` in LLM context

### UI Updates
- [ ] Add Queries/Tools/Agents tab structure
- [ ] Add scripted vs parameterized query views
- [ ] Add RAG query template display
- [ ] Add Agent Builder tool export
- [ ] Add JSON download functionality

### Testing
- [ ] Test scripted query generation
- [ ] Test auto-parameterization
- [ ] Test RAG query template generation
- [ ] Test Agent Builder export
- [ ] Integration test: Demo → Agent Builder workflow

### Examples
- [ ] Create example demo with all three query types
- [ ] Document query conversion patterns
- [ ] Show Agent Builder tool import process

## Success Metrics

- **Query coverage:** Every scripted query has a parameterized version
- **RAG queries:** At least 1-2 RAG queries per demo
- **Agent Builder:** Tool definitions export successfully
- **User adoption:** Demo presenters use parameterized/RAG queries in 50%+ of demos
- **Customer engagement:** "What if?" questions answered interactively

## Future Enhancements

### Phase 5: Query Templates
- Template library for common patterns
- Industry-specific query templates
- Best practices catalog

### Phase 6: Agent Builder Bi-Directional Sync
- Import existing Agent Builder tools
- Sync tool definitions back to Demo Builder
- Version control for tool definitions

### Phase 7: Query Performance Optimization
- Automatic LIMIT recommendations
- Cache frequently-used COMPLETION results
- Batch similar queries

### Phase 8: Advanced RAG Techniques
- Hybrid search (vector + text)
- Multi-hop reasoning
- Citation/source tracking

## References

- **ES|QL MATCH:** `/docs/esql/search-match.md`
- **ES|QL RERANK:** `/docs/esql/rerank.md`
- **ES|QL COMPLETION:** `/docs/esql/completion.md`
- **ES|QL Parameterization:** `/docs/esql/time_spans.md` (examples)
- **Agent Builder:** Elastic Agent Builder documentation

## Appendix A: Complete RAG Query Example

```sql
-- Full example: Support ticket semantic search with AI-powered answers

FROM support_tickets METADATA _score
-- Step 1: MATCH - Semantic text search (broad retrieval)
| WHERE MATCH(description, ?user_question)
    OR MATCH(customer_feedback, ?user_question)
-- Time boundary: Last 120 days (configurable)
| WHERE @timestamp >= NOW() - 120 days
-- Sort by relevance
| SORT _score DESC
-- Get top 100 candidates for reranking
| LIMIT 100

-- Step 2: RERANK - ML-based relevance scoring (precision)
| RERANK ?user_question
    ON description, customer_feedback, resolution_notes
    WITH {"inference_id": "my_rerank_endpoint"}
-- Keep top 5 most relevant
| LIMIT 5

-- Step 3: Build context for LLM
| EVAL context = CONCAT(
    "Ticket #", ticket_id,
    " | Severity: ", severity,
    " | Customer: ", customer_name,
    " | Issue: ", description,
    " | Feedback: ", customer_feedback,
    " | Resolution: ", resolution_notes
  )

-- Step 4: Aggregate context (INLINE STATS preserves all fields!)
-- CRITICAL: Use INLINE STATS not STATS to preserve fields for COMPLETION
| INLINE STATS all_context = MV_CONCAT(context, "\n\n")

-- Step 5: COMPLETION - Generate AI answer
| EVAL prompt = CONCAT(
    "You are a support analytics assistant. ",
    "Based on these relevant support tickets:\n\n",
    all_context,
    "\n\nQuestion: ", ?user_question,
    "\n\nProvide a detailed answer with specific examples from the tickets. ",
    "Include ticket numbers and key patterns you observe."
  )
| COMPLETION answer = prompt
    WITH {"inference_id": "my_completion_endpoint"}

-- Return answer and context
| KEEP answer, all_context

-- NOTE: If STATS was used instead of INLINE STATS, all fields except
-- all_context would be destroyed, breaking the COMPLETION command!
```

## Appendix B: Query Type Comparison

| Aspect | Scripted | Parameterized | RAG |
|--------|----------|---------------|-----|
| **Purpose** | Known scenarios | Interactive exploration | Open-ended questions |
| **Parameters** | None | Multiple (?param) | Single (?user_question) |
| **Testing** | Fully tested | Trusted via base | Runtime validation |
| **Results** | Predictable | Variable | Generated by LLM |
| **Use Case** | Scripted demos | "What if?" scenarios | Ad-hoc analysis |
| **Agent Builder** | No | Yes (tool with params) | Yes (primary use case) |
| **User Input** | None | Structured inputs | Natural language |
| **LLM Required** | No | No | Yes (COMPLETION) |

---

## Summary of Key Decisions

### ✅ Confirmed Approach:
1. **LLM generates BOTH query versions** (scripted + parameterized) - NO auto-conversion
2. **Use INLINE STATS** not STATS to preserve fields before COMPLETION
3. **Parameters are for Agent Builder tools** - NOT direct REST API use (v2 feature)
4. **Include RERANK at least once** per demo, but make it optional
5. **Avoid LIKE/RLIKE** in parameterized queries (not supported)
6. **Multi-index queries supported** - leverage `FROM index1,index2,index-*`
7. **Search field selection** - ES|QL skill will evolve to help identify best fields
8. **No backward compatibility needed** - framework updates won't break old modules

### ⏸️ Deferred to V2:
- Executing parameterized queries (requires Agent Builder integration)
- Testing parameterized queries with default values
- Bi-directional sync with Agent Builder

### 🎯 Implementation Priority:
**Phase 1:** Framework updates (base.py, module_generator.py)
**Phase 2:** UI enhancements (Queries/Tools/Agents tabs)
**Phase 3:** Search strategy service
**Phase 4:** Documentation and examples

---

**Document Status:** Updated with Implementation Clarifications (v1.1)
**Next Steps:** Review and approve, then proceed with Phase 1 implementation
