"""
Under the Hood - Technical deep dive into Demo Builder architecture.

This view showcases the sophisticated query generation, data profiling,
and modular architecture that powers the Demo Builder.
"""

import streamlit as st


def render_under_the_hood():
    """Render the Under the Hood technical documentation page."""

    st.title("🔧 Under the Hood")
    st.caption("Technical deep dive into Demo Builder's architecture and sophisticated query generation")

    # Create tabs for each major component
    tabs = st.tabs([
        "Overview",
        "Data Generation",
        "Query Generation",
        "Data Indexing",
        "Queries",
        "Tools",
        "Agents",
        "Guide"
    ])

    # Tab 1: Overview
    with tabs[0]:
        render_overview_tab()

    # Tab 2: Data Generation
    with tabs[1]:
        render_data_generation_tab()

    # Tab 3: Query Generation
    with tabs[2]:
        render_query_generation_tab()

    # Tab 4: Data Indexing
    with tabs[3]:
        render_data_indexing_tab()

    # Tab 5: Queries
    with tabs[4]:
        render_queries_tab()

    # Tab 6: Tools
    with tabs[5]:
        render_tools_tab()

    # Tab 7: Agents
    with tabs[6]:
        render_agents_tab()

    # Tab 8: Guide
    with tabs[7]:
        render_guide_tab()


def render_overview_tab():
    """Render the Overview tab."""
    st.markdown("## Module Generation Strategy")

    st.markdown("""
    Demo Builder uses a sophisticated **LLM-powered modular architecture** to generate
    custom Elasticsearch demonstrations. Each demo is a self-contained Python module
    with data generation, query strategies, and deployment configurations.
    """)

    # Architecture diagram
    st.markdown("### High-Level Architecture")
    st.code("""
    User Input (Natural Language)
            ↓
    ┌─────────────────────────────┐
    │ SmartContextExtractor       │  → Extract company, department, pain points, metrics
    └─────────────────────────────┘
            ↓
    ┌─────────────────────────────┐
    │ ModularDemoOrchestrator     │  → Coordinate module generation
    └─────────────────────────────┘
            ↓
    ┌─────────────────────────────┐
    │ Query Strategy Selection    │  → Analytics vs Search/RAG
    └─────────────────────────────┘
            ↓
    ┌─────────────────────────────┐
    │ LLM Code Generation         │  → Generate Python modules
    │  - data_generator.py        │
    │  - queries.json             │
    │  - static/                  │
    │  - agent_metadata.json      │
    └─────────────────────────────┘
            ↓
    ┌─────────────────────────────┐
    │ Dynamic Module Loading      │  → Import and execute generated code
    └─────────────────────────────┘
            ↓
    ┌─────────────────────────────┐
    │ Data Indexing & Profiling   │  → Index to Elasticsearch, profile for parameters
    └─────────────────────────────┘
            ↓
    ┌─────────────────────────────┐
    │ Query Validation & Testing  │  → Iterative refinement, constraint relaxation
    └─────────────────────────────┘
            ↓
    ┌─────────────────────────────┐
    │ Tool & Agent Deployment     │  → Deploy to Elastic Agent Builder
    └─────────────────────────────┘
    """, language="text")

    # Key steps
    st.markdown("### Key Generation Steps")

    with st.expander("**1. Context Extraction**", expanded=True):
        st.markdown("""
        - **Natural Language Processing**: Parses user descriptions to extract structured context
        - **Pattern Matching**: Identifies company name, department, industry, pain points, use cases
        - **Completeness Tracking**: Monitors context completeness (need ≥50% to generate)
        - **Interactive Refinement**: Asks clarifying questions to fill gaps
        """)
        st.code("""
# Example: SmartContextExtractor
context = {
    "company_name": "T-Mobile",
    "department": "Network Operations",
    "industry": "Telecommunications",
    "pain_points": ["HSS database failures", "Signaling storms"],
    "use_cases": ["Proactive anomaly detection", "Cell tower analysis"],
    "metrics": ["IMSI spike detection", "Cell ID cardinality"]
}
        """, language="python")

    with st.expander("**2. Demo Type Detection**"):
        st.markdown("""
        - **Analytics Demos**: Aggregations, trends, time-series, metrics
        - **Search/RAG Demos**: Document retrieval, semantic search, knowledge bases
        - **Auto-Detection**: Based on use case keywords and pain points
        - **Strategy Routing**: Different code generation strategies per type
        """)
        st.code("""
# Analytics keywords: analyze, trend, metric, aggregate, dashboard
# Search keywords: find, retrieve, lookup, documents, semantic search

if demo_type == "analytics":
    strategy_generator = QueryStrategyGenerator()  # STATS, INLINESTATS, LOOKUP JOIN
elif demo_type == "search":
    strategy_generator = SearchQueryStrategyGenerator()  # MATCH, RERANK, COMPLETION
        """, language="python")

    with st.expander("**3. Query Strategy Generation**"):
        st.markdown("""
        - **LLM-Powered Planning**: Generates query plan before data generation
        - **Use Case Mapping**: Maps each pain point to specific ES|QL patterns
        - **Parameter Identification**: Determines which queries need user parameters
        - **Semantic Text Detection**: Identifies fields needing vector search
        - **Output**: Structured query plan with data requirements
        """)

    with st.expander("**4. Data Generation (Query-Informed)**"):
        st.markdown("""
        - **Query-First Approach**: Data is generated to satisfy query requirements
        - **Semantic Text Fields**: Automatically identified and indexed with proper mappings
        - **Index Type Selection**: data_stream vs lookup based on use case
        - **Realistic Data**: Uses Faker + LLM for domain-specific realism
        - **Scale Aware**: Generates appropriate volume based on context
        """)

    with st.expander("**5. Query Generation & Validation**"):
        st.markdown("""
        - **Sophisticated ES|QL**: Leverages advanced commands (LOOKUP JOIN, INLINESTATS, RERANK)
        - **Anti-Pattern Avoidance**: Follows query guides to avoid common errors
        - **Iterative Refinement**: Tests queries, refines on errors
        - **Constraint Relaxation**: Can adjust thresholds if no results found
        - **Parameter Extraction**: Profiles data to detect valid parameter values
        """)

    with st.expander("**6. Data Indexing & Profiling**"):
        st.markdown("""
        - **Bulk Indexing**: Efficient batch indexing to Elasticsearch
        - **Mapping Generation**: Automatic mapping creation for semantic_text fields
        - **Data Profiling**: Analyzes indexed data to extract parameter values
        - **Cardinality Analysis**: Identifies fields suitable for parameters
        - **Business Date Detection**: Recognizes date fields for time-based filtering
        """)

    with st.expander("**7. Tool & Agent Deployment**"):
        st.markdown("""
        - **Elastic Agent Builder Integration**: Deploys validated queries as tools
        - **Parameter Configuration**: Maps query parameters to tool inputs
        - **Agent Configuration**: Creates AI assistants with tool access
        - **Tool Assignment**: Associates tools with appropriate agents
        """)

    with st.expander("**8. Demo Guide Generation**"):
        st.markdown("""
        - **Narrative Structure**: Creates compelling demo flow
        - **Talk Track**: Provides presenter guidance
        - **A-ha Moments**: Identifies key insights to highlight
        - **Technical Details**: Explains query sophistication
        """)

    st.divider()

    st.markdown("### Key Architectural Principles")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Modular Plugin Architecture**
        - Framework defines interfaces
        - LLM generates implementations
        - Modules are version-controlled
        - Manual editing supported

        **Query-First Design**
        - Queries drive data generation
        - Not data → query (backwards)
        - Ensures realistic demo scenarios
        """)

    with col2:
        st.markdown("""
        **Sophisticated Query Generation**
        - Multi-stage LLM reasoning
        - Data profiling integration
        - Anti-pattern awareness
        - Iterative refinement

        **Production-Ready**
        - Real Elasticsearch indexing
        - Actual ES|QL validation
        - Elastic Agent Builder deployment
        """)


def render_data_generation_tab():
    """Render the Data Generation tab."""
    st.markdown("## Data Generation Strategy")

    st.markdown("""
    Unlike traditional demo builders that start with data and then create queries,
    Demo Builder uses a **query-first approach** where data is generated to satisfy
    sophisticated query requirements.
    """)

    # Key concepts
    st.markdown("### Query-Informed Data Generation")

    with st.expander("**Why Query-First?**", expanded=True):
        st.markdown("""
        **Traditional Approach (Problematic):**
        ```
        1. Generate generic data
        2. Try to write queries
        3. Queries limited by data structure
        4. Unrealistic demo scenarios
        ```

        **Demo Builder Approach (Better):**
        ```
        1. Define query requirements (e.g., "detect spike patterns")
        2. Generate data that exhibits those patterns
        3. Queries showcase sophisticated ES|QL
        4. Realistic, compelling demos
        ```

        **Example**: For "detect authentication failure spikes", we generate:
        - Normal baseline traffic (100-200 events/min)
        - Spike periods (500+ events/min)
        - Multiple failure types (timeouts, wrong password, HSS unavailable)
        - Temporal patterns that make INLINESTATS interesting
        """)

    st.markdown("### Semantic Text Field Identification")

    with st.expander("**Automatic semantic_text Detection**"):
        st.markdown("""
        The system automatically identifies fields that should use Elasticsearch's
        `semantic_text` type for vector-based semantic search.
        """)

        st.code("""
# From query_strategy_generator.py
def _identify_semantic_text_fields(self, query_plan: Dict) -> List[str]:
    '''
    Analyzes query plan to identify fields requiring semantic search.

    Returns fields that need semantic_text mapping for:
    - MATCH queries (fuzzy matching)
    - RERANK operations (relevance scoring)
    - Completion/RAG use cases
    '''
    semantic_fields = []

    for query in query_plan.get('queries', []):
        # Check for MATCH, QSTR, or RERANK usage
        if any(cmd in query.get('esql_commands', [])
               for cmd in ['MATCH', 'QSTR', 'RERANK']):
            semantic_fields.extend(query.get('searchable_fields', []))

    return list(set(semantic_fields))
        """, language="python")

        st.markdown("""
        **How It Works:**
        1. Query strategy identifies fields used in MATCH/RERANK
        2. Data generator receives semantic_fields list
        3. Mappings include proper semantic_text configuration
        4. Generated data includes rich text content
        5. Indexing applies inference endpoints
        """)

    st.markdown("### Index Type Selection")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **data_stream (Time-Series)**
        - Events with @timestamp
        - Append-only workloads
        - Automatic lifecycle management
        - Examples: logs, metrics, events

        ```python
        {
            "index_type": "data_stream",
            "timestamp_field": "@timestamp",
            "lifecycle": "30d"
        }
        ```
        """)

    with col2:
        st.markdown("""
        **lookup (Reference Data)**
        - Documents without time dimension
        - Update/replace patterns
        - Used in LOOKUP JOIN
        - Examples: users, products, policies

        ```python
        {
            "index_type": "lookup",
            "id_field": "provider_id",
            "update_strategy": "upsert"
        }
        ```
        """)

    st.markdown("### Data Profiling for Parameters")

    with st.expander("**Sophisticated Parameter Extraction**"):
        st.markdown("""
        After indexing, the system profiles the data to extract valid parameter values.
        This enables intelligent parameter suggestions and validation.
        """)

        st.code("""
# From agent_builder_service.py
def extract_esql_parameters(self, query: str, data_profile: Dict) -> Dict:
    '''
    Analyzes ES|QL query to extract parameters with business-aware detection.

    Capabilities:
    - Field cardinality analysis (low cardinality = good for parameters)
    - Business date detection (order_date, created_at, etc.)
    - Type inference (keyword, date, numeric)
    - Description generation from field names
    - Optional vs required determination
    '''

    # Example output:
    {
        "region": {
            "type": "keyword",
            "description": "Geographic region filter",
            "values": ["us-east", "us-west", "eu-central"],
            "cardinality": 3,
            "optional": False
        },
        "start_date": {
            "type": "date",
            "description": "Start date for analysis period",
            "business_date": True,
            "optional": False
        }
    }
        """, language="python")

        st.markdown("""
        **Business Date Detection:**
        - Recognizes date-related field names (created_at, order_date, timestamp)
        - Identifies date fields used in WHERE clauses
        - Provides date parameters for time-based filtering
        - Suggests reasonable date ranges based on data
        """)

    st.markdown("### Data Generation Implementation")

    with st.expander("**Code Structure**"):
        st.code("""
# Generated data_generator.py structure

class DataGenerator:
    def __init__(self):
        self.faker = Faker()

    def generate_datasets(self) -> Dict[str, Any]:
        '''
        Generate all datasets for this demo.

        Returns dict with:
        - datasets: List of dataset configs
        - semantic_text_fields: Fields needing inference
        - index_mappings: Custom mappings for each index
        '''
        return {
            "datasets": [
                self._generate_events_dataset(),
                self._generate_lookup_dataset()
            ],
            "semantic_text_fields": {
                "events-index": ["description", "notes"],
                "lookup-index": ["bio", "summary"]
            }
        }

    def _generate_events_dataset(self):
        '''Query-informed generation with realistic patterns.'''
        events = []

        # Generate baseline traffic
        for _ in range(1000):
            events.append({
                "@timestamp": self._random_timestamp(),
                "event_type": random.choice(["success", "failure"]),
                # ... other fields
            })

        # Generate spike patterns (for INLINESTATS detection)
        spike_time = datetime.now()
        for _ in range(500):
            events.append({
                "@timestamp": spike_time,
                "event_type": "failure",
                "failure_reason": "hss_unavailable"
            })

        return {
            "index_name": "events-index",
            "index_type": "data_stream",
            "documents": events
        }
        """, language="python")

    st.markdown("### Scale-Aware Generation")

    st.markdown("""
    The system generates data volume based on the extracted context:

    | Scale | Events Generated | Use Case |
    |-------|-----------------|----------|
    | Small (< 1K) | 500-1,000 | Quick demos, testing |
    | Medium (1K-10K) | 5,000-10,000 | Standard demos |
    | Large (10K-100K) | 50,000-100,000 | Performance testing |
    | Enterprise (> 100K) | 500,000+ | Scale demonstrations |

    The scale is specified via the "Size" dropdown in the sidebar (Small/Medium/Large).
    """)


def render_query_generation_tab():
    """Render the Query Generation tab."""
    st.markdown("## Query Generation Strategy")

    st.markdown("""
    Demo Builder's query generation is the most sophisticated component, using
    multi-stage LLM reasoning with data profiling, anti-pattern awareness, and
    iterative refinement.
    """)

    # Demo type routing
    st.markdown("### Demo Type Routing")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Analytics Demos**
        - Uses `QueryStrategyGenerator`
        - ES|QL Commands: STATS, INLINESTATS, LOOKUP JOIN, EVAL, DATE_TRUNC
        - Focus: Aggregations, trends, metrics
        - Pattern: FROM → WHERE → STATS BY → SORT
        """)

        st.code("""
// Example Analytics Query
FROM events-data*
| WHERE @timestamp > NOW() - 30 days
| EVAL hour = DATE_TRUNC(1 hour, @timestamp)
| STATS
    total_events = COUNT(*),
    failure_rate = AVG(CASE(status == "failure", 1, 0))
  BY hour, region
| SORT hour DESC
        """, language="sql")

    with col2:
        st.markdown("""
        **Search/RAG Demos**
        - Uses `SearchQueryStrategyGenerator`
        - ES|QL Commands: MATCH, QSTR, RERANK, COMPLETION
        - Focus: Document retrieval, semantic search
        - Pattern: FROM → MATCH → RERANK → COMPLETION
        """)

        st.code("""
// Example Search Query
FROM providers-lookup
| MATCH provider_name WITH "cardiologist"
        AND bio WITH "heart disease"
| RERANK top = 10
| COMPLETION
    context = CONCAT(provider_name, " - ", bio)
    question = "Find specialists..."
        """, language="sql")

    st.markdown("### Query Strategy Generation (Stage 1)")

    with st.expander("**Initial Query Planning**", expanded=True):
        st.markdown("""
        Before generating any data or queries, the system creates a comprehensive query strategy.
        """)

        st.code("""
# From module_generator.py - generate_query_strategy()

QUERY_STRATEGY_PROMPT = '''
You are an expert ES|QL query architect. Given this customer context:

Company: {company}
Department: {department}
Pain Points: {pain_points}
Use Cases: {use_cases}

Generate a sophisticated query strategy that:

1. Maps each pain point to specific ES|QL patterns
2. Identifies which queries need parameters
3. Determines data requirements (fields, patterns, scale)
4. Specifies semantic_text fields for vector search
5. Plans query complexity progression (simple → advanced)

Focus on these ES|QL capabilities:
- INLINESTATS for anomaly detection
- LOOKUP JOIN for data enrichment
- DATE_TRUNC + STATS for time-series
- MATCH + RERANK for semantic search
- Multi-lag analysis for trend detection

Output JSON with:
{{
  "demo_type": "analytics" | "search",
  "queries": [
    {{
      "name": "...",
      "use_case": "...",
      "esql_commands": ["STATS", "INLINESTATS"],
      "parameters": ["region", "threshold"],
      "searchable_fields": ["description"],
      "data_requirements": {{
        "fields": [...],
        "patterns": ["spike_detection", "baseline_traffic"]
      }}
    }}
  ],
  "semantic_text_fields": ["description", "notes"],
  "index_requirements": [...]
}}
'''
        """, language="python")

        st.markdown("""
        **Key Outputs:**
        - List of queries to generate
        - Parameter requirements
        - Data generation instructions
        - Semantic text field identification
        - Index structure requirements
        """)

    st.markdown("### Query Generation (Stage 2)")

    with st.expander("**Sophisticated ES|QL Generation**"):
        st.markdown("""
        After data is generated and indexed, the system generates actual ES|QL queries
        with anti-pattern awareness and best practices.
        """)

        st.code("""
# From module_generator.py - generate_queries()

QUERY_GENERATION_PROMPT = '''
Generate ES|QL queries following this query strategy:
{query_strategy}

Available Data Profile:
{data_profile}

CRITICAL GUIDELINES:

✅ DO:
- Use INLINESTATS for rolling averages and anomaly detection
- Use LOOKUP JOIN to enrich main dataset with reference data
- Use DATE_TRUNC for time-series bucketing
- Use EVAL before OR after STATS (just don't reference aggregated-away fields)
- Use CASE() for conditional logic and zero-division protection
- Use MATCH for text search, RERANK for relevance
- Use time filters ONLY when relevant to the use case (e.g., "recent activity", "last month's performance")

❌ DO NOT:
- Use window functions (LAG, LEAD, OVER, ROW_NUMBER, RANK)
- Reference fields not in BY clause after STATS (they're aggregated away)
- Divide without checking for zero (causes errors)
- Use fields not present in data profile
- Add @timestamp filters to every query (data is static; use only when use-case requires it)
- Parameterize @timestamp (use NOW() - X days when needed, or parameterize business dates)

SEMANTIC SEARCH PATTERN:
FROM index
| MATCH field WITH "search terms"
| RERANK top = 10
| COMPLETION context = CONCAT(...)

ANALYTICS PATTERN:
FROM data-stream*
| WHERE @timestamp > NOW() - 7 days
| INLINESTATS baseline = AVG(count) BY category
| EVAL deviation = (count - baseline) / baseline
| WHERE deviation > 0.5
| STATS anomalies = COUNT(*) BY category
'''
        """, language="python")

    st.markdown("### Data Profiling Integration")

    with st.expander("**Using Profiled Data for Query Generation**"):
        st.markdown("""
        The system profiles indexed data and provides this context to query generation.
        """)

        st.code("""
# Example Data Profile

{
  "indices": {
    "events-data-stream": {
      "doc_count": 50000,
      "fields": {
        "@timestamp": {
          "type": "date",
          "min": "2024-10-01T00:00:00Z",
          "max": "2024-11-12T00:00:00Z"
        },
        "region": {
          "type": "keyword",
          "cardinality": 5,
          "top_values": ["us-east", "us-west", "eu-central", "ap-south", "ap-east"]
        },
        "event_type": {
          "type": "keyword",
          "cardinality": 3,
          "top_values": ["success", "failure", "timeout"]
        },
        "failure_count": {
          "type": "long",
          "min": 0,
          "max": 523,
          "avg": 87.3
        }
      }
    }
  }
}

# Query generation uses this to:
# 1. Know which fields exist
# 2. Use realistic values in WHERE clauses
# 3. Choose appropriate aggregation fields
# 4. Set reasonable thresholds
        """, language="python")

    st.markdown("### Iterative Query Testing")

    with st.expander("**Validation & Refinement Loop**"):
        st.markdown("""
        Generated queries are tested against the actual Elasticsearch cluster and
        refined if errors occur.
        """)

        st.code("""
# From query_validation_service.py

def validate_query(self, query_text: str) -> Dict:
    '''
    Tests query against Elasticsearch and refines if needed.

    Process:
    1. Execute query via ES|QL API
    2. Check for syntax errors
    3. Check for zero results
    4. If errors: refine query (up to 3 attempts)
    5. If no results: relax constraints
    6. Mark as validated on success
    '''

    for attempt in range(3):
        result = self.execute_esql(query_text)

        if result['error']:
            # Common fixes:
            # - Remove EVAL after STATS
            # - Add zero-division checks
            # - Fix DATE_EXTRACT syntax → DATE_TRUNC
            # - Correct field names
            refined = self.refine_query(query_text, result['error'])
            query_text = refined
            continue

        if result['row_count'] == 0:
            # Relax constraints:
            # - Expand time range
            # - Lower thresholds
            # - Remove restrictive filters
            relaxed = self.relax_constraints(query_text)
            query_text = relaxed
            continue

        # Success!
        return {'valid': True, 'query': query_text, 'row_count': result['row_count']}

    return {'valid': False, 'error': 'Could not refine query'}
        """, language="python")

    st.markdown("### Semantic Search Strategy")

    with st.expander("**MATCH → RERANK → COMPLETION Pipeline**"):
        st.markdown("""
        For search/RAG demos, Demo Builder implements the full semantic search pipeline.
        """)

        st.markdown("""
        **Stage 1: MATCH (Initial Retrieval)**
        ```sql
        FROM providers-lookup
        | MATCH provider_name WITH "cardiologist"
                AND bio WITH "heart disease specialist"
        ```
        - Uses semantic_text fields
        - Fuzzy matching with vector embeddings
        - Retrieves candidate documents

        **Stage 2: RERANK (Relevance Scoring)**
        ```sql
        | RERANK top = 10
        ```
        - Re-scores results using cross-encoder
        - More accurate than initial retrieval
        - Returns top-k most relevant

        **Stage 3: COMPLETION (RAG)**
        ```sql
        | COMPLETION
            context = CONCAT(provider_name, " | ", specialty, " | ", bio)
            question = "Find me a cardiologist specializing in heart disease"
        ```
        - Passes retrieved context to LLM
        - Generates natural language answer
        - Cites sources from results

        **Full Pipeline:**
        ```sql
        FROM providers-lookup
        | MATCH provider_name WITH "cardiologist"
                AND bio WITH "heart disease"
        | RERANK top = 10
        | COMPLETION
            context = CONCAT(provider_name, " - ", bio, " - ", office_location)
            question = $question
        ```
        """)

    st.markdown("### Anti-Pattern Detection & Prevention")

    with st.expander("**Common ES|QL Anti-Patterns**", expanded=True):
        st.markdown("""
        The query generator uses aggressive warnings and post-generation detection to prevent common ES|QL errors:

        | Anti-Pattern | Why It Fails | Correct Approach | Detection |
        |--------------|--------------|------------------|-----------|
        | Window functions (`LAG`, `LEAD`, `OVER`) | ES\|QL doesn't support SQL window functions | Use `INLINESTATS` with statistical methods | Syntax error |
        | Referencing aggregated-away fields | Can't use fields not in `BY` clause after `STATS` | Include in `BY` clause or use `INLINESTATS` | Syntax error |
        | Division without zero check | Crashes on zero denominator | Use `CASE(denom != 0, num/denom, 0)` | Runtime error |
        | **Integer division** | Truncates to 0, produces wrong results | Wrap denominator in `TO_DOUBLE()` | **Post-gen scanner** ⚡ |
        | Parameterizing `@timestamp` | System field should use relative time | Use `NOW() - 7 days`; parameterize business dates | Strategy validation |
        | **Missing NULL checks** | Silently excludes NULL values in negative filters | Append `OR field IS NULL` to `!=`, `NOT` filters | **Post-gen scanner** ⚡ |
        | `DATE_EXTRACT` for bucketing | Wrong command for time-series grouping | Use `DATE_TRUNC(1 hour, @timestamp)` | Syntax error |
        """)

        st.markdown("""
        **⚡ Automated Detection** - Two anti-patterns are detected even when queries succeed:

        **1. Integer Division** (Silent Wrong Results)
        ```sql
        -- ❌ WRONG: Returns 0 or 100 only
        | EVAL success_rate = ((total - failures) / total) * 100
        -- Result: (95 / 100) = 0 (integer division truncates)

        -- ✅ CORRECT: Returns accurate percentages
        | EVAL success_rate = ((total - failures) / TO_DOUBLE(total)) * 100
        -- Result: (95 / 100.0) = 0.95, then 0.95 * 100 = 95.0
        ```

        **Why Critical**: Produces plausible but wrong results (0 or 100 for percentages)
        - No error thrown
        - Affects ALL division of aggregated fields
        - Detected by scanning EVAL statements

        **2. NULL Handling** (Silent Data Loss)
        ```sql
        -- ❌ WRONG: Silently excludes docs where status is NULL
        | WHERE status != "success"

        -- ✅ CORRECT: Includes ALL non-success (including NULL)
        | WHERE status != "success" OR status IS NULL
        ```

        **Why Critical**: Missing data = missed threats in security queries
        - No error thrown
        - Documents with NULL values silently excluded
        - Especially dangerous for security/SIEM use cases
        - Detected by scanning negative filters (`!=`, `NOT`, `NOT LIKE`)

        Both patterns are automatically detected during query testing and flagged with warnings + suggested fixes.
        """)

    with st.expander("**Query Strategy Validation**"):
        st.markdown("""
        Before data/query generation, the system creates a `query_strategy.json` file that's
        validated for anti-patterns:

        **Saved to**: `demos/[demo_name]/query_strategy.json`

        **Purpose**:
        - Captures PLANNED query strategy before execution
        - Enables debugging (compare planned vs generated)
        - Allows early detection of anti-patterns
        - Provides triaging capability

        **Validation Checks**:
        - ✅ @timestamp parameterization hints (detects queries planning to use `?start_date`)
        - ✅ Reference dataset usage (array length validation reminders)
        - ✅ Field consistency (across datasets, queries, relationships)
        - ✅ Query complexity progression (simple → advanced)

        **Example Warning**:
        ```
        ⚠️ Query 'Revenue Analysis' may parameterize @timestamp
           (mentions: start_date, end_date).
           Remember: @timestamp should NEVER be parameterized - use NOW() instead!
        ```

        See `docs/QUERY_STRATEGY_INTROSPECTION.md` for details.
        """)

    with st.expander("**Query Testing with Pattern Detection**"):
        st.markdown("""
        During the query testing phase (after generation), all queries are automatically
        scanned for patterns that don't produce errors but may cause issues:

        **Automated Scans**:

        1. **Integer Division Scanner**
           - Detects EVAL statements with division (`/`)
           - Checks for missing `TO_DOUBLE()` wrappers
           - Special flagging for percentage calculations
           - Provides specific fix suggestions

        2. **NULL Handling Scanner**
           - Detects negative filters (`!=`, `NOT`, `NOT LIKE`)
           - Checks for missing `OR field IS NULL` clauses
           - **Security query flagging**: Warns if query contains security keywords
           - Keywords: `security`, `auth`, `threat`, `compliance`, `audit`, `siem`

        **Warning Output** (saved to `query_testing_results.json`):
        ```json
        {
          "warnings": [
            {
              "type": "integer_division",
              "field": "success_rate_pct",
              "message": "Potential integer division (will truncate to 0)",
              "suggested_fix": "| EVAL success_rate_pct = ... / TO_DOUBLE(total)"
            },
            {
              "type": "missing_null_check",
              "field": "auth_result",
              "message": "Missing NULL check - CRITICAL for security queries",
              "is_security_query": true,
              "suggested_fix": "| WHERE auth_result != 'success' OR auth_result IS NULL"
            }
          ]
        }
        ```

        **Docs**:
        - `docs/INTEGER_DIVISION_ANTI_PATTERN.md`
        - `docs/NULL_HANDLING_ANTI_PATTERN.md`
        """)

    st.divider()

    st.markdown("### Complete ES|QL Guidance Inventory")

    st.markdown("""
    To demonstrate to the ES|QL team the breadth of guidance needed for agentic LLM tools,
    below is a comprehensive inventory of all ES|QL rules, patterns, and anti-patterns provided
    to the query generation system.
    """)

    with st.expander("**📚 Critical Syntax Rules (20 Rules)**"):
        st.markdown("""
        These rules are enforced through `src/prompts/esql_strict_rules.py` and prevent
        common syntax errors and anti-patterns:

        **1. LOOKUP JOIN - NO SUFFIX, NO PREFIX** ⚠️⚠️ CRITICAL
        - Never use `_lookup` suffix on index names
        - Reference joined fields WITHOUT prefix after JOIN
        - Example: `FROM events | LOOKUP JOIN providers ON id` → use `provider_name` not `providers.provider_name`

        **2. MATCH Syntax - ALWAYS WITHIN WHERE** ⚠️
        - MATCH is a function called within WHERE clause
        - Pattern: `WHERE MATCH(field, "term")` or `WHERE MATCH(field, ?param)`

        **3. FORK Syntax - NO NAMED BRANCHES** ⚠️
        - FORK branches are unnamed
        - Cannot assign branches to variables

        **4. Query Parameters - CANNOT CHECK NULL** ⚠️
        - Cannot check if parameter is NULL
        - Parameters are ALWAYS required when used

        **5. RERANK Syntax - Pipe Operation** ⚠️
        - Syntax: `| RERANK "query" ON field`
        - Not a function: `WHERE RERANK(...)` is invalid

        **6. COUNT_DISTINCT Syntax** ⚠️⚠️ VERY COMMON ERROR
        - Function doesn't exist in ES|QL
        - Use `STATS unique_count = COUNT(DISTINCT field)`

        **7. INLINESTATS Syntax - Single BY Clause** ⚠️⚠️ VERY COMMON ERROR
        - ONE BY clause at end applies to ALL aggregations
        - Not per-aggregation BY clauses

        **8. STATS Conditional Aggregation** ⚠️
        - Use `COUNT(*) WHERE condition` syntax
        - Example: `failures = COUNT(*) WHERE status == "failed"`

        **9. DATE Functions - Parameter Order** ⚠️
        - DATE_TRUNC: `DATE_TRUNC(interval, field)` not `DATE_TRUNC(field, interval)`
        - Interval first, field second

        **10. Index Modes for LOOKUP JOIN** ⚠️ CRITICAL
        - Lookup tables must be created in `lookup` mode
        - Cannot use standard indices in LOOKUP JOIN

        **11. Field Names - Case Sensitive** ⚠️
        - ES|QL is case-sensitive for field names
        - `Region` ≠ `region`

        **12. Date Arithmetic - ALWAYS Use TO_LONG()** ⚠️⚠️ CRITICAL
        - Cannot subtract datetime values directly
        - Must wrap both in TO_LONG() first

        **13. Division and Type Casting** ⚠️
        - Use TO_DOUBLE() for precision
        - Pattern: `TO_DOUBLE(numerator) / denominator`

        **14. LOOKUP JOIN Schema Validation** ⚠️⚠️⚠️ CRITICAL
        - Join key MUST exist in both datasets
        - Cannot be auto-fixed if missing

        **15. COMPLETION Syntax (RAG Queries)** ⚠️
        - Syntax: `| COMPLETION context = CONCAT(...) question = $question`
        - Requires context and question parameters

        **16. Time Filtering - Different Patterns** ⚠️⚠️ CRITICAL
        - Scripted: `@timestamp > NOW() - 7 days`
        - Parameterized: `business_date >= ?start_date` (NOT @timestamp)

        **17. EVAL Variable Reuse** ⚠️⚠️ CRITICAL
        - Cannot use newly defined variables in same EVAL command
        - Must use separate EVAL commands

        **18. @timestamp Parameterization** ⚠️⚠️ CRITICAL
        - NEVER parameterize @timestamp with `?start_date`
        - Use `NOW() - X days` for relative time
        - Parameterize business dates only (order_date, created_at)

        **19. Experimental Features** ⚠️
        - CHANGE_POINT, LAG/LEAD may not be supported
        - Use INLINESTATS with z-score calculation instead

        **20. NULL Handling with Negative Filters** ⚠️⚠️ CRITICAL
        - ES|QL EXCLUDES NULL values from `!=`, `NOT`, `NOT LIKE`
        - Always append `OR field IS NULL` unless intentional
        - ESPECIALLY critical for security/SIEM queries
        """)

    with st.expander("**✨ Advanced ES|QL Patterns (6 Patterns)**"):
        st.markdown("""
        Sophisticated query patterns taught to the generation system:

        **1. LOOKUP JOIN for Data Enrichment**
        - Enrich streaming data with dimensional data
        - Pattern: `FROM events | LOOKUP JOIN dimension ON key | WHERE enriched_field ...`

        **2. INLINESTATS for Anomaly Detection**
        - Keep all rows while adding aggregate calculations
        - Pattern: `| INLINESTATS avg = AVG(value) BY category | EVAL deviation = value - avg`

        **3. FORK for Parallel Analysis**
        - Split pipeline for multiple analyses
        - Pattern: `| FORK (WHERE type == "A" | STATS ...) (WHERE type == "B" | STATS ...)`

        **4. Multi-Field Search Pattern**
        - Search across multiple fields with different boosts
        - Pattern: `WHERE MATCH(title, ?query, {"boost": 2.0}) OR MATCH(content, ?query)`

        **5. Time Series Anomaly Detection**
        - Detect anomalies using z-scores
        - Pattern: `| INLINESTATS mean = AVG(value), stddev = STDDEV(value) | EVAL z_score = (value - mean) / stddev | WHERE z_score > 3`

        **6. Semantic Search Pipeline (MATCH → RERANK → COMPLETION)**
        - Full RAG pipeline
        - Pattern: `FROM index | MATCH field WITH "term" | RERANK top = 10 | COMPLETION context = CONCAT(...)`
        """)

    with st.expander("**🚨 Aggressive Anti-Pattern Warnings (4 Warnings)**"):
        st.markdown("""
        Warnings placed at END of ALL query generation prompts (recency bias strategy):

        **1. @timestamp Parameterization Warning**
        - Location: All 4 query generation methods
        - Visual: 🚨🚨🚨 CRITICAL with emoji and CAPS
        - Shows exact wrong pattern vs correct pattern
        - Repeated in both parameterized and scripted query methods

        **2. Integer Division Warning** (NEW)
        - Location: All 4 query generation methods
        - Shows `(total - failures) / total` → returns 0
        - Correct: `(total - failures) / TO_DOUBLE(total)` → returns 0.95
        - Includes WHY explanation and multiple valid patterns

        **3. NULL Handling Warning** (NEW)
        - Location: All 4 query generation methods
        - Shows `WHERE status != "success"` → silently excludes NULL
        - Correct: `WHERE status != "success" OR status IS NULL`
        - Emphasizes security impact: "missing data = missed threats"

        **4. Array Length Anti-Pattern Warning**
        - Location: Data generation prompts
        - Prevents slicing pre-defined pools beyond their length
        - Shows wrong: `pool[:n]` when pool has fewer than n items
        - Correct: Generate exact count or use `np.random.choice` with replacement
        """)

    with st.expander("**🔍 Post-Generation Detection (2 Scanners)**"):
        st.markdown("""
        Automated pattern detection during query testing phase:

        **1. Integer Division Scanner**
        - Scans: All EVAL statements with division (`/`)
        - Checks: Missing TO_DOUBLE(), float literals, multiply-by-float-first
        - Flags: Percentage calculations specifically (field names with 'rate' or 'pct')
        - Output: Warning with suggested fix in `query_testing_results.json`

        **2. NULL Handling Scanner**
        - Scans: All WHERE clauses with `!=`, `NOT(...)`, `NOT LIKE`
        - Checks: Missing `OR field IS NULL` clauses
        - Flags: Security queries (keywords: security, auth, threat, compliance, audit, siem)
        - Output: CRITICAL warning for security queries
        """)

    with st.expander("**📋 Safe Query Patterns by Type (4 Templates)**"):
        st.markdown("""
        Template patterns provided for different query types:

        **1. Scripted Query (No Parameters, Testable)**
        - Fixed logic, hard-coded values
        - Pattern: `FROM index | WHERE field == "value" | STATS agg BY group | SORT field`

        **2. Parameterized Query (Required Parameters Only)**
        - User-provided parameters using `?param` syntax
        - Pattern: `FROM index | WHERE field == ?param | STATS agg BY group`
        - NO optional parameters or NULL checks

        **3. RAG Query (Semantic Search + LLM)**
        - Full pipeline: MATCH → RERANK → COMPLETION
        - Pattern: `FROM index | MATCH field WITH ?query | RERANK top = 10 | COMPLETION ...`

        **4. Complex Aggregation with Enrichment (Scripted)**
        - Combines LOOKUP JOIN + INLINESTATS + time-series
        - Multi-stage query with data enrichment and anomaly detection
        """)

    with st.expander("**✅ DO's and ❌ DON'Ts (30+ Guidelines)**"):
        st.markdown("""
        Comprehensive list of best practices and anti-patterns:

        **DO's:**
        - Use INLINESTATS for rolling averages and anomaly detection
        - Use LOOKUP JOIN to enrich main dataset with reference data
        - Use DATE_TRUNC for time-series bucketing
        - Use EVAL before OR after STATS (just don't reference aggregated-away fields)
        - Use CASE() for conditional logic and zero-division protection
        - Use MATCH for text search, RERANK for relevance
        - Use TO_DOUBLE() when dividing aggregated fields
        - Include `OR field IS NULL` with negative filters
        - Use time filters ONLY when relevant to use case

        **DON'Ts:**
        - Use window functions (LAG, LEAD, OVER, ROW_NUMBER, RANK)
        - Reference fields not in BY clause after STATS
        - Divide without checking for zero or using TO_DOUBLE()
        - Use fields not present in data profile
        - Add @timestamp filters to every query (data is static)
        - Parameterize @timestamp (use NOW() - X days or parameterize business dates)
        - Use COUNT_DISTINCT (doesn't exist)
        - Use DATE_EXTRACT for bucketing (use DATE_TRUNC instead)
        - Forget NULL handling in negative filters
        """)

    with st.expander("**📊 Example-Based Learning (10+ Examples)**"):
        st.markdown("""
        Concrete examples provided in prompts:

        **1. INLINESTATS for Anomaly Detection Example**
        - Complete working query with z-score calculation
        - Shows baseline calculation, deviation, and filtering

        **2. LOOKUP JOIN Enrichment Example**
        - Shows joining events with reference data
        - Demonstrates field usage after JOIN

        **3. Multi-Lag Analysis Example**
        - Detects sustained patterns vs transient spikes
        - Uses LAG with INLINESTATS

        **4. Semantic Search Pipeline Example**
        - Full MATCH → RERANK → COMPLETION flow
        - Shows parameter substitution

        **5. Zero Division Protection Example**
        - Shows CASE() pattern for safe division
        - Alternative using COALESCE

        **6. Time Bucketing Example**
        - DATE_TRUNC with STATS BY pattern
        - Shows hourly/daily aggregation

        **7. Conditional Aggregation Example**
        - COUNT(*) WHERE pattern
        - Shows multiple conditions

        **8. Integer Division Fix Example**
        - Wrong: `(total - failures) / total`
        - Correct: `(total - failures) / TO_DOUBLE(total)`

        **9. NULL Handling Example**
        - Wrong: `WHERE status != "success"`
        - Correct: `WHERE status != "success" OR status IS NULL`

        **10. Business Date Parameterization Example**
        - Shows parameterizing order_date, created_at
        - Contrasts with @timestamp (use NOW() instead)
        """)

    with st.expander("**🎯 Query Strategy Generation Guidance**"):
        st.markdown("""
        Guidance specific to the query strategy generation phase:

        **Pain Point Mapping**
        - Maps customer pain points to specific ES|QL patterns
        - Identifies which commands solve which problems
        - Example: "proactive detection" → INLINESTATS for anomaly detection

        **Parameter Identification**
        - Determines which queries need user parameters
        - Distinguishes required vs optional (optional not supported)
        - Identifies business date fields for parameterization

        **Semantic Text Detection**
        - Identifies fields needing vector search
        - Maps to MATCH, RERANK, COMPLETION usage
        - Determines semantic_text mapping requirements

        **Index Type Selection**
        - data_stream for time-series with @timestamp
        - lookup for reference data in LOOKUP JOIN
        - Based on use case and query patterns

        **Complexity Progression**
        - Simple queries first (basic STATS)
        - Progressive sophistication (INLINESTATS, LOOKUP JOIN)
        - Culminates in advanced patterns (multi-lag, anomaly detection)
        """)

    with st.expander("**📖 Documentation & Debugging Resources**"):
        st.markdown("""
        Comprehensive documentation for debugging and understanding:

        **Anti-Pattern Docs:**
        - `docs/INTEGER_DIVISION_ANTI_PATTERN.md` - Why integer division fails, detection logic
        - `docs/NULL_HANDLING_ANTI_PATTERN.md` - Silent data loss, security impact
        - `docs/TIMESTAMP_PARAMETER_ANTI_PATTERN_FIX.md` - Why @timestamp params fail
        - `docs/ARRAY_LENGTH_ANTI_PATTERN_FIX.md` - Data generation slicing errors

        **Strategy & Introspection:**
        - `docs/QUERY_STRATEGY_INTROSPECTION.md` - Using query_strategy.json for debugging
        - Explains validation, anti-pattern detection, and triaging workflow

        **Architecture:**
        - `docs/RAG_SEARCH_ARCHITECTURE.md` - Search vs analytics demo types
        - `docs/MODULAR_ARCHITECTURE.md` - Framework design principles
        """)

    st.markdown("""
    ---
    **Summary Statistics:**
    - **20** Critical syntax rules
    - **6** Advanced query patterns
    - **4** Aggressive end-of-prompt warnings (recency bias strategy)
    - **2** Post-generation pattern scanners (integer division, NULL handling)
    - **4** Safe query templates
    - **30+** DO's and DON'Ts
    - **10+** Concrete examples
    - **Multi-stage** guidance (strategy → generation → validation)
    - **Comprehensive** documentation for debugging

    **Key Innovation**: Not just preventing errors, but detecting silent failures (integer division,
    NULL exclusion) that produce plausible but wrong results.
    """)


def render_data_indexing_tab():
    """Render the Data Indexing tab."""
    st.markdown("## Data Indexing & Profiling")

    st.markdown("""
    The Data tab provides functionality to index generated data to Elasticsearch
    and profile it for parameter extraction.
    """)

    st.markdown("### Indexing Workflow")

    st.code("""
    User Flow:
    1. View Generated Data → Preview documents before indexing
    2. Configure Index Settings → Index names, shard counts, replicas
    3. Bulk Index → Efficient batch indexing with progress tracking
    4. Data Profiling → Analyze indexed data for query parameters
    5. Semantic Text Setup → Apply inference endpoints for vector search
    """, language="text")

    with st.expander("**Index Configuration**"):
        st.markdown("""
        Users can configure index settings before indexing:

        **Index Types:**
        - **data_stream**: For time-series data with @timestamp
        - **standard**: For regular indices
        - **lookup**: For reference data used in LOOKUP JOIN

        **Settings:**
        - Number of shards (default: 1)
        - Number of replicas (default: 1)
        - Refresh interval (default: 1s)
        - Custom mappings for semantic_text fields
        """)

        st.code("""
# Example Index Request

PUT /events-data-stream
{
  "mappings": {
    "properties": {
      "@timestamp": {"type": "date"},
      "event_type": {"type": "keyword"},
      "description": {"type": "semantic_text"},  // Vector search field
      "count": {"type": "long"},
      "region": {"type": "keyword"}
    }
  },
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 1,
    "refresh_interval": "1s"
  }
}
        """, language="json")

    with st.expander("**Bulk Indexing**"):
        st.markdown("""
        Efficient batch indexing with error handling:
        """)

        st.code("""
# From elasticsearch_service.py

def bulk_index_documents(self, index_name: str, documents: List[Dict]) -> Dict:
    '''
    Bulk index documents with progress tracking.

    Features:
    - Batch size: 500 documents per request
    - Progress callbacks for UI updates
    - Error aggregation and reporting
    - Automatic retry on transient failures
    - Refresh after completion
    '''

    batch_size = 500
    total_docs = len(documents)
    indexed = 0
    errors = []

    for i in range(0, total_docs, batch_size):
        batch = documents[i:i + batch_size]

        # Prepare bulk request
        actions = [
            {
                "_index": index_name,
                "_source": doc
            }
            for doc in batch
        ]

        # Execute bulk
        response = bulk(self.client, actions, stats_only=False)

        indexed += len(batch)
        progress = (indexed / total_docs) * 100

        # Report progress to UI
        if progress_callback:
            progress_callback(progress)

    # Refresh index
    self.client.indices.refresh(index=index_name)

    return {
        'success': True,
        'indexed': indexed,
        'errors': errors
    }
        """, language="python")

    with st.expander("**Data Profiling**"):
        st.markdown("""
        After indexing, the system profiles data to extract metadata useful for
        query generation and parameter extraction.
        """)

        st.code("""
# From elasticsearch_service.py

def profile_index(self, index_name: str) -> Dict:
    '''
    Profile indexed data to extract parameter metadata.

    Returns:
    - Document count
    - Field types and statistics
    - Cardinality for keyword fields
    - Value ranges for numeric fields
    - Top values for low-cardinality fields
    - Date ranges for date fields
    '''

    profile = {
        "doc_count": 0,
        "fields": {}
    }

    # Get document count
    count_result = self.client.count(index=index_name)
    profile["doc_count"] = count_result['count']

    # Get field mappings
    mapping = self.client.indices.get_mapping(index=index_name)

    # Analyze each field
    for field_name, field_info in mappings['properties'].items():
        field_type = field_info.get('type', 'unknown')

        if field_type == 'keyword':
            # Get cardinality and top values
            agg_result = self.client.search(
                index=index_name,
                size=0,
                aggs={
                    "cardinality": {"cardinality": {"field": field_name}},
                    "top_values": {"terms": {"field": field_name, "size": 10}}
                }
            )

            profile["fields"][field_name] = {
                "type": "keyword",
                "cardinality": agg_result['aggregations']['cardinality']['value'],
                "top_values": [
                    bucket['key']
                    for bucket in agg_result['aggregations']['top_values']['buckets']
                ]
            }

        elif field_type in ['long', 'integer', 'double', 'float']:
            # Get numeric statistics
            stats_result = self.client.search(
                index=index_name,
                size=0,
                aggs={
                    "stats": {"stats": {"field": field_name}}
                }
            )

            profile["fields"][field_name] = {
                "type": field_type,
                "min": stats_result['aggregations']['stats']['min'],
                "max": stats_result['aggregations']['stats']['max'],
                "avg": stats_result['aggregations']['stats']['avg']
            }

        elif field_type == 'date':
            # Get date range
            date_range = self.client.search(
                index=index_name,
                size=0,
                aggs={
                    "min_date": {"min": {"field": field_name}},
                    "max_date": {"max": {"field": field_name}}
                }
            )

            profile["fields"][field_name] = {
                "type": "date",
                "min": date_range['aggregations']['min_date']['value_as_string'],
                "max": date_range['aggregations']['max_date']['value_as_string']
            }

    return profile
        """, language="python")

        st.markdown("""
        **Profile Usage:**
        - Query generation uses field statistics to create realistic queries
        - Parameter extraction identifies low-cardinality fields as good candidates
        - Date ranges inform time-based filtering
        - Numeric ranges help set appropriate thresholds
        """)

    with st.expander("**Semantic Text Inference**"):
        st.markdown("""
        For fields marked as `semantic_text`, the system applies inference endpoints
        for vector embedding generation.
        """)

        st.code("""
# Semantic text field configuration

PUT _inference/text_embedding/my-elser-endpoint
{
  "service": "elasticsearch",
  "service_settings": {
    "model_id": ".elser_model_2",
    "deployment_id": "elser_deployment"
  }
}

PUT /events-data-stream
{
  "mappings": {
    "properties": {
      "description": {
        "type": "semantic_text",
        "inference_id": "my-elser-endpoint"
      }
    }
  }
}

# Documents are automatically vectorized on indexing
POST /events-data-stream/_doc
{
  "description": "Authentication failure due to HSS database timeout"
  // Vector embeddings generated automatically
}
        """, language="json")

    st.markdown("### Data Tab UI")

    st.markdown("""
    The Data tab provides:

    1. **Dataset Preview**: View generated documents before indexing
    2. **Index Configuration**: Set index names, shards, replicas
    3. **Bulk Indexing**: Index with progress tracking
    4. **Index Status**: View indexed document counts
    5. **Data Profile**: View field statistics and metadata
    6. **Delete Indices**: Clean up test data
    """)


def render_queries_tab():
    """Render the Queries tab."""
    st.markdown("## Query Testing & Validation")

    st.markdown("""
    The Queries tab provides sophisticated query testing, editing, validation,
    and constraint relaxation capabilities.
    """)

    st.markdown("### Query Categories")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Scripted Queries**
        - No parameters
        - Fixed logic
        - Direct execution
        - Example: "Show total events by region"
        """)

    with col2:
        st.markdown("""
        **Parameterized Queries**
        - User-provided parameters
        - Dynamic filtering
        - Reusable templates
        - Example: "Show events for $region since $date"
        """)

    with col3:
        st.markdown("""
        **RAG Queries**
        - Semantic search
        - MATCH + RERANK + COMPLETION
        - Natural language questions
        - Example: "Find providers matching $question"
        """)

    st.markdown("### Query Testing Interface")

    with st.expander("**Testing Workflow**"):
        st.markdown("""
        Users can test queries before validation:

        1. **Select Query**: Choose from generated queries
        2. **View Query**: See ES|QL with syntax highlighting
        3. **Edit Query**: Make changes in code editor
        4. **Provide Parameters**: Fill in required parameters
        5. **Execute**: Run against Elasticsearch
        6. **View Results**: See returned rows and execution time
        7. **Validate**: Mark as validated if working correctly
        """)

        st.code("""
# Query Testing UI Flow

┌─────────────────────────────┐
│ Query: "Detect Spike Events"│
│ Type: Parameterized         │
└─────────────────────────────┘
        ↓
┌─────────────────────────────┐
│ ES|QL Code Editor           │
│ - Syntax highlighting       │
│ - Line numbers              │
│ - Error indicators          │
└─────────────────────────────┘
        ↓
┌─────────────────────────────┐
│ Parameter Input             │
│ region: us-east             │
│ threshold: 100              │
└─────────────────────────────┘
        ↓
┌─────────────────────────────┐
│ Execute Query               │
│ ⚡ Run Test                  │
└─────────────────────────────┘
        ↓
┌─────────────────────────────┐
│ Results Display             │
│ - Rows returned: 15         │
│ - Execution time: 45ms      │
│ - Column preview            │
└─────────────────────────────┘
        ↓
┌─────────────────────────────┐
│ ✅ Validate Query           │
└─────────────────────────────┘
        """, language="text")

    with st.expander("**Query Editing**"):
        st.markdown("""
        Users can edit queries directly in the UI:
        """)

        st.code("""
// Original generated query
FROM events-data*
| WHERE @timestamp > NOW() - 7 days
| WHERE region == "us-east"
| STATS count = COUNT(*) BY event_type
| SORT count DESC

// User can edit to:
// - Change time range
// - Add/remove filters
// - Modify aggregations
// - Adjust sorting
// - Add EVAL calculations

// Edited query
FROM events-data*
| WHERE @timestamp > NOW() - 30 days  // Extended range
| WHERE region == "us-east" OR region == "us-west"  // Multiple regions
| EVAL is_failure = CASE(event_type == "failure", 1, 0)
| STATS
    total = COUNT(*),
    failures = SUM(is_failure),
    failure_rate = AVG(is_failure)
  BY DATE_TRUNC(1 day, @timestamp)
| SORT @timestamp DESC
        """, language="sql")

    with st.expander("**Constraint Relaxation**"):
        st.markdown("""
        If a query returns zero results, the system can automatically relax constraints.
        """)

        st.code("""
# From query_validation_service.py

def relax_query_constraints(self, query_text: str) -> str:
    '''
    Relax constraints in a query that returns no results.

    Strategies:
    1. Expand time range (7 days → 30 days → 90 days)
    2. Lower numeric thresholds (> 100 → > 50 → > 10)
    3. Remove optional filters (AND region == ... → removed)
    4. Broaden MATCH terms (exact phrase → individual words)
    5. Increase TOP/LIMIT values
    '''

    # Example: Time range expansion
    if 'NOW() - 7 days' in query_text:
        return query_text.replace('NOW() - 7 days', 'NOW() - 30 days')

    # Example: Threshold lowering
    if 'WHERE count > 100' in query_text:
        return query_text.replace('WHERE count > 100', 'WHERE count > 50')

    # Example: Remove restrictive filter
    if 'AND region ==' in query_text:
        # Remove entire AND clause
        return re.sub(r'AND region == "[^"]*"', '', query_text)

    return query_text
        """, language="python")

        st.markdown("""
        **User Control:**
        - Users can trigger constraint relaxation manually
        - System suggests which constraints to relax
        - Users can accept/reject suggestions
        - Multiple relaxation iterations supported
        """)

    with st.expander("**Query Validation**"):
        st.markdown("""
        Validation marks a query as production-ready and enables tool deployment.
        """)

        st.code("""
# Validation Process

def validate_query(query_id: str, query_text: str) -> Dict:
    '''
    Validate a query for production use.

    Checks:
    1. Syntax validation (ES|QL parser)
    2. Execution test (returns results)
    3. Performance check (< 5 second response)
    4. Result structure (has expected columns)
    5. Parameter safety (no injection risks)
    '''

    # Execute query
    result = execute_esql(query_text)

    if result['error']:
        return {'valid': False, 'error': result['error']}

    if result['row_count'] == 0:
        return {'valid': False, 'error': 'Query returns no results'}

    if result['execution_time_ms'] > 5000:
        return {'valid': False, 'error': 'Query too slow'}

    # Mark as validated
    save_validation_status(query_id, {
        'validated': True,
        'validated_at': datetime.now(),
        'row_count': result['row_count'],
        'execution_time_ms': result['execution_time_ms']
    })

    return {'valid': True}
        """, language="python")

        st.markdown("""
        **Validation Benefits:**
        - Only validated queries can be deployed as tools
        - Validation status tracked in tool_metadata.json
        - Validation timestamp and metrics recorded
        - Re-validation required after editing
        """)

    st.markdown("### Query Result Display")

    with st.expander("**Result Visualization**"):
        st.markdown("""
        Query results are displayed with rich visualizations:

        **Tabular Display:**
        - Paginated results (50 rows per page)
        - Sortable columns
        - Formatted values (dates, numbers)
        - Export to CSV

        **Charts:**
        - Time-series line charts for date fields
        - Bar charts for aggregations
        - Pie charts for distributions
        - Automatic chart selection based on result structure

        **Metadata:**
        - Row count
        - Execution time
        - Columns returned
        - Query explanation
        """)

        st.code("""
# Example Result Display

Query: "Detect Authentication Spike Events"
Executed in: 87ms
Rows returned: 23

┌─────────────────────┬──────────┬───────────┬────────────┐
│ timestamp           │ region   │ failures  │ deviation  │
├─────────────────────┼──────────┼───────────┼────────────┤
│ 2024-11-12 10:00:00 │ us-east  │ 523       │ +412%      │
│ 2024-11-12 09:00:00 │ us-west  │ 387       │ +298%      │
│ 2024-11-12 08:00:00 │ us-east  │ 156       │ +127%      │
│ ...                 │ ...      │ ...       │ ...        │
└─────────────────────┴──────────┴───────────┴────────────┘

[Line Chart: Failures over Time by Region]

💡 Insight: Spike detected in us-east region at 10:00 AM
        """, language="text")


def render_tools_tab():
    """Render the Tools tab."""
    st.markdown("## Tool Deployment & Management")

    st.markdown("""
    The Tools tab enables deployment of validated queries to Elastic Agent Builder as tools
    that AI agents can invoke.
    """)

    st.markdown("### Tool Deployment Workflow")

    st.code("""
    Flow:
    1. Validate Query → Must pass validation in Queries tab
    2. Configure Tool Metadata → ID, description, tags, sample question
    3. Configure Parameters → Mark optional/required, set types
    4. Preview API Payload → See exact API call before deployment
    5. Deploy Tool → Create tool in Elastic Agent Builder
    6. Assign to Agent → Associate tool with appropriate agent(s)
    """, language="text")

    with st.expander("**Tool Metadata Configuration**"):
        st.markdown("""
        Each tool requires metadata for Agent Builder:
        """)

        st.code("""
Tool Metadata Structure:

{
  "tool_id": "company_department_purpose",  // Unique identifier
  "description": "Brief description of what the tool does and when to use it",
  "tags": ["category1", "category2"],  // For organization
  "sample_question": "Example user question that would trigger this tool",
  "query": "FROM ... | WHERE ... | STATS ...",  // ES|QL query
  "params": {
    "region": {
      "type": "keyword",
      "description": "Geographic region to filter by",
      "optional": false,
      "values": ["us-east", "us-west", "eu-central"]
    },
    "threshold": {
      "type": "integer",
      "description": "Minimum event count threshold",
      "optional": true,
      "default": 100
    }
  }
}
        """, language="json")

        st.markdown("""
        **Tool ID Convention:**
        - Format: `{company}_{department}_{purpose}`
        - Example: `tmobile_network_spike_detection`
        - Ensures uniqueness across demos
        - Makes filtering by module possible

        **Description Best Practices:**
        - First ~50 characters appear in tool list
        - Start with brief summary
        - Explain when to use the tool
        - Mention key parameters

        **Sample Questions:**
        - Realistic user questions
        - Help agents understand tool applicability
        - Examples:
          - "Are there any authentication spike events in us-east?"
          - "Show me the top failing services in the last hour"
          - "Find providers specializing in cardiology near Seattle"
        """)

    with st.expander("**Parameter Configuration**"):
        st.markdown("""
        Parameters are automatically extracted from queries and can be configured:
        """)

        st.code("""
# From agent_builder_service.py

def extract_esql_parameters(self, query: str, data_profile: Dict) -> Dict:
    '''
    Sophisticated parameter extraction with business awareness.

    Detects:
    1. WHERE clause filters: WHERE region == ?
    2. Time-based filters: WHERE @timestamp > ?
    3. Numeric thresholds: WHERE count > ?
    4. MATCH terms: MATCH field WITH ?

    Enriches with data profile:
    - Type inference from field mappings
    - Valid values from cardinality analysis
    - Business date detection (order_date, created_at, etc.)
    - Optional vs required determination
    '''

    parameters = {}

    # Extract from WHERE clauses
    where_patterns = re.findall(r'WHERE\s+(\w+)\s*==\s*\?', query)
    for field in where_patterns:
        param_info = {
            "type": self._infer_type(field, data_profile),
            "description": self._generate_description(field),
            "optional": False
        }

        # Add valid values if low cardinality
        if field in data_profile.get('fields', {}):
            field_info = data_profile['fields'][field]
            if field_info.get('cardinality', 999) < 20:
                param_info['values'] = field_info.get('top_values', [])

        parameters[field] = param_info

    # Detect business date fields
    date_fields = self._detect_business_dates(query, data_profile)
    for field in date_fields:
        parameters[field] = {
            "type": "date",
            "description": f"Filter by {field.replace('_', ' ')}",
            "business_date": True,
            "optional": False
        }

    return parameters
        """, language="python")

        st.markdown("""
        **Parameter Types:**
        - `keyword`: String values (region, status, category)
        - `date`: Date/time values with business date awareness
        - `integer`/`long`: Numeric thresholds
        - `text`: Full-text search terms

        **Optional vs Required:**
        - Users can mark parameters as optional
        - Optional parameters have default values
        - Required parameters must be provided by agent
        """)

    with st.expander("**API Payload Preview**"):
        st.markdown("""
        Before deployment, users can preview the exact API call:
        """)

        st.code("""
POST https://kibana.elastic.co/api/agent_builder/tools
Headers:
  Authorization: ApiKey xxxxx
  Content-Type: application/json
  kbn-xsrf: true

Body:
{
  "id": "tmobile_network_spike_detection",
  "type": "esql",
  "description": "Detects authentication failure spike events using INLINESTATS to compare current rates against baseline. Use when investigating sudden increases in authentication failures or potential security incidents.",
  "tags": ["network", "security", "anomaly-detection"],
  "configuration": {
    "query": "FROM events-data* | WHERE @timestamp > NOW() - 1 hour | WHERE region == $region | INLINESTATS baseline = AVG(failure_count) BY region | EVAL deviation = (failure_count - baseline) / baseline | WHERE deviation > $threshold | STATS spike_events = COUNT(*), max_failures = MAX(failure_count), avg_deviation = AVG(deviation) BY region | SORT spike_events DESC",
    "params": {
      "region": {
        "type": "keyword",
        "description": "Geographic region to analyze",
        "optional": false,
        "values": ["us-east", "us-west", "eu-central", "ap-south", "ap-east"]
      },
      "threshold": {
        "type": "integer",
        "description": "Deviation threshold percentage (e.g., 50 for 50%)",
        "optional": true,
        "default": 50
      }
    }
  }
}
        """, language="http")

        st.markdown("""
        **Preview Benefits:**
        - See exact API payload before deployment
        - Verify parameter configuration
        - Review query syntax
        - Copy curl command for manual testing
        """)

    with st.expander("**Tool Deployment**"):
        st.markdown("""
        Deployment creates the tool in Elastic Agent Builder:
        """)

        st.code("""
# From agent_builder_service.py

def create_tool(self, tool_config: Dict) -> Dict:
    '''
    Deploy tool to Elastic Agent Builder.

    Process:
    1. Validate tool configuration
    2. POST to /api/agent_builder/tools
    3. Handle errors (duplicate ID, invalid query, etc.)
    4. Mark as deployed in local metadata
    5. Return deployment status
    '''

    response = requests.post(
        f"{self.kibana_url}/api/agent_builder/tools",
        headers={
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json",
            "kbn-xsrf": "true"
        },
        json={
            "id": tool_config['id'],
            "type": "esql",
            "description": tool_config['description'],
            "tags": tool_config.get('tags', []),
            "configuration": {
                "query": tool_config['query'],
                "params": tool_config.get('params', {})
            }
        }
    )

    if response.status_code == 200:
        return {'success': True, 'tool_id': tool_config['id']}
    else:
        return {'success': False, 'error': response.json().get('message')}
        """, language="python")

    st.markdown("### Deployed Tools Management")

    with st.expander("**Viewing Deployed Tools**"):
        st.markdown("""
        The Tools tab shows all tools deployed for the current demo:

        **Filtering:**
        - Matches module prefix (e.g., `tmobile_network*`)
        - Handles both hyphens and underscores
        - Shows count of deployed tools

        **Tool Details:**
        - Tool ID and description
        - Full tool definition (JSON)
        - Associated agents
        - Deployment timestamp

        **Actions:**
        - View full definition
        - Delete from deployment (preserves local config)
        - Re-deploy with updated configuration
        """)

    with st.expander("**Tool Testing**"):
        st.markdown("""
        After deployment, tools can be tested:

        **Via Agent Builder UI:**
        - Navigate to Agent Builder
        - Select an agent with the tool assigned
        - Ask questions that trigger the tool
        - View tool invocations and results

        **Via API:**
        ```bash
        POST /api/agent_builder/tools/{tool_id}/test
        {
          "parameters": {
            "region": "us-east",
            "threshold": 100
          }
        }
        ```

        **Via Demo App:**
        - Testing interface coming soon
        - Will allow direct tool invocation
        - Preview parameters and results
        """)


def render_agents_tab():
    """Render the Agents tab."""
    st.markdown("## Agent Configuration & Deployment")

    st.markdown("""
    The Agents tab manages AI agent configuration and deployment to Elastic Agent Builder.
    Agents are AI assistants that can invoke tools to answer user questions.
    """)

    st.markdown("### Agent Architecture")

    st.code("""
    Agent Components:

    1. Identity
       - ID: Unique identifier (company_department_agent)
       - Name: Display name shown to users
       - Description: Brief summary of capabilities
       - Avatar: Symbol and color for visual identity

    2. Instructions
       - System prompt defining behavior
       - Expertise areas and capabilities
       - Communication style guidelines
       - Use case explanations

    3. Tools
       - Assigned tool IDs
       - Agent can invoke these during conversations
       - Tools provide data access

    4. Labels
       - Tags for organization and filtering
       - Example: ["network", "security", "analytics"]
    """, language="text")

    with st.expander("**Agent Metadata Structure**"):
        st.markdown("""
        Each demo module includes pre-generated agent metadata:
        """)

        st.code("""
# agent_metadata.json

{
  "id": "tmobile_network_operations_agent",
  "name": "T-Mobile Network Operations Assistant",
  "description": "AI assistant specialized in Network Operations for T-Mobile. I can help detect network issues proactively, analyze signaling storms, and troubleshoot authentication failures.",
  "labels": [
    "t-mobile",
    "network_operations",
    "analytics",
    "telecommunications"
  ],
  "avatar_color": "#3B82F6",
  "avatar_symbol": "TM",
  "configuration": {
    "instructions": "You are an AI assistant specialized in Network Operations for T-Mobile...\\n\\n**Your Expertise:**\\n- Proactive Network Anomaly Detection\\n- Cell Tower Handoff Analysis\\n- Core Network Troubleshooting\\n- Security & Authentication\\n\\n**Key Pain Points I Address:**\\n- HSS database failures\\n- MME software bugs\\n- Signaling storms\\n- Security attacks\\n\\n**Communication Style:**\\nI communicate clearly and urgently, understanding that network operations require rapid response...",
    "tools": []
  }
}
        """, language="json")

        st.markdown("""
        **ID Convention:**
        - Format: `{company}_{department}_agent`
        - Example: `tmobile_network_operations_agent`
        - Ensures uniqueness and module filtering

        **Avatar Colors:**
        - Analytics demos: `#3B82F6` (blue)
        - Search demos: `#10B981` (green)
        - Custom colors supported

        **Avatar Symbols:**
        - 1-2 letter abbreviation
        - Usually company initials
        - Examples: "TM", "AB", "JP"
        """)

    with st.expander("**Agent Instructions**"):
        st.markdown("""
        Instructions define agent behavior and capabilities:
        """)

        st.code("""
You are an AI assistant specialized in Network Operations for T-Mobile,
one of the leading mobile network operators in the United States.

**Your Expertise:**
You help Network Operations teams monitor and troubleshoot critical network
infrastructure including MME hosts, HSS databases, cell towers, and core
network components across 4G LTE and 5G networks.

**What You Can Help With:**
- **Proactive Network Anomaly Detection**: Detect network issues before they
  impact subscribers by tracking IMSI and cell ID cardinality changes
- **Cell Tower Handoff Analysis**: Identify cell tower handoff cascade
  failures and mobility issues that cause dropped calls
- **Core Network Troubleshooting**: Detect core network split-brain scenarios,
  signaling storms, and MME software bugs
- **Security & Authentication**: Identify rogue network attempts, SS7 security
  attacks, and mass authentication failure events

**Key Pain Points I Address:**
- Reactive troubleshooting that waits for help desk to be overwhelmed
- HSS database corruption or synchronization issues
- Radio equipment failure and cell tower handoff failures
- MME software bugs and resource exhaustion
- Rogue network attempts and SS7 security attacks

**Available Data & Metrics:**
I have access to network telemetry including:
- Unique IMSI and cell ID cardinality tracking over time windows
- Procedure failure counts (>200 failures per 5-minute interval threshold)
- IMSI spike detection across lag periods with percent change calculations
- Cell ID spike detection with threshold alerting
- MME host monitoring (2-5 hosts tracked)

**Communication Style:**
I communicate clearly and urgently, understanding that network operations
require rapid response to prevent subscriber impact. I provide actionable
insights with specific thresholds and patterns that indicate problems.

How can I assist you with your network operations today?
        """, language="text")

        st.markdown("""
        **Instruction Components:**
        1. **Expertise Summary**: High-level capabilities
        2. **Detailed Capabilities**: Specific use cases with explanations
        3. **Pain Points**: Problems the agent helps solve
        4. **Available Data**: What metrics/data the tools provide
        5. **Communication Style**: How the agent should respond

        **Best Practices:**
        - Be specific about capabilities
        - Reference actual pain points from context
        - Mention available tools/data
        - Set appropriate tone (urgent, technical, friendly, etc.)
        - Provide conversation starters
        """)

    with st.expander("**Tool Assignment**"):
        st.markdown("""
        Agents are assigned tools that provide data access:
        """)

        st.code("""
# Tool Assignment Process

1. Deploy Tools
   - Tools must be deployed before assignment
   - Tools validated and working

2. View Agent
   - See currently assigned tools
   - Check tool availability

3. Select Tools
   - Module-specific tools (company_department_*)
   - Platform tools (platform.*)
   - Check/uncheck to assign/remove

4. Update Agent
   - Click "Set Active Tools for this Agent"
   - Tools immediately available to agent

5. Test Agent
   - Ask questions in Agent Builder UI
   - Agent invokes tools as needed
   - View tool invocation logs
        """, language="text")

        st.markdown("""
        **Tool Categories:**

        **Module-Specific Tools:**
        - Generated for this demo
        - Prefix matches module (e.g., `tmobile_network_*`)
        - Specific to use cases and pain points
        - Example: `tmobile_network_spike_detection`

        **Platform Tools:**
        - Shared across all demos
        - Prefix: `platform.*`
        - Generic capabilities
        - Examples:
          - `platform.core.search`: General search
          - `platform.core.generate_esql`: Generate queries
          - `platform.core.execute_esql`: Run custom queries
        """)

        st.code("""
# Agent with Tools Configuration

{
  "id": "tmobile_network_operations_agent",
  "name": "T-Mobile Network Operations Assistant",
  "configuration": {
    "instructions": "...",
    "tools": [
      {
        "tool_ids": [
          "tmobile_network_spike_detection",
          "tmobile_network_handoff_analysis",
          "tmobile_network_authentication_failures",
          "platform.core.search",
          "platform.core.generate_esql"
        ]
      }
    ]
  }
}
        """, language="json")

    st.markdown("### Agent Deployment")

    with st.expander("**Deployment Workflow**"):
        st.markdown("""
        Deploying an agent to Elastic Agent Builder:
        """)

        st.code("""
# From agent_builder_service.py

def create_agent(self, agent_config: Dict) -> Dict:
    '''
    Deploy agent to Elastic Agent Builder.

    Process:
    1. Validate agent configuration
    2. POST to /api/agent_builder/agents
    3. Handle errors (duplicate ID, invalid config)
    4. Return deployment status
    '''

    response = requests.post(
        f"{self.kibana_url}/api/agent_builder/agents",
        headers={
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json",
            "kbn-xsrf": "true"
        },
        json={
            "id": agent_config['id'],
            "name": agent_config['name'],
            "description": agent_config['description'],
            "labels": agent_config.get('labels', []),
            "avatar_color": agent_config.get('avatar_color', '#3B82F6'),
            "avatar_symbol": agent_config.get('avatar_symbol', 'AI'),
            "configuration": {
                "instructions": agent_config['instructions'],
                "tools": [
                    {
                        "tool_ids": agent_config.get('tool_ids', [])
                    }
                ]
            }
        }
    )

    if response.status_code == 200:
        return {'success': True, 'agent_id': agent_config['id']}
    else:
        return {'success': False, 'error': response.json().get('message')}
        """, language="python")

        st.markdown("""
        **Deployment States:**
        - **Not Deployed**: Agent only exists locally
        - **Deployed**: Agent live in Agent Builder
        - **Modified**: Local changes not yet deployed
        - **Update Available**: Can re-deploy with changes

        **Deployment Options:**
        - **Create New**: Deploy agent for first time
        - **Update Existing**: Modify deployed agent
        - **Save Locally**: Update metadata without deploying
        """)

    with st.expander("**Agent Management**"):
        st.markdown("""
        The Agents tab provides management capabilities:

        **View Deployed Agents:**
        - List all agents for current demo
        - Filter by module prefix
        - Show currently assigned tools
        - Display agent configuration

        **Agent Actions:**
        - View raw JSON configuration
        - Update tool assignments
        - Modify instructions and metadata
        - Delete from deployment
        - Re-deploy with changes

        **Tool Assignment:**
        - See available tools (deployed + platform)
        - Check/uncheck tools to assign/remove
        - Update agent with new tool set
        - Changes take effect immediately
        """)

    st.markdown("### Agent Testing")

    with st.expander("**Testing in Agent Builder**"):
        st.markdown("""
        After deployment, test agents in the Agent Builder UI:

        **Access Agent Builder:**
        1. Navigate to Kibana
        2. Go to Search → Agent Builder
        3. Select your deployed agent
        4. Start a conversation

        **Example Conversation:**
        ```
        User: Are there any authentication spike events in the us-east region?

        Agent: Let me check the authentication events for the us-east region...
        [Invokes: tmobile_network_spike_detection with region=us-east]

        I found 3 spike events in us-east region in the last hour:

        1. 10:15 AM - 523 failures (412% above baseline)
           - Primary cause: HSS database timeout
           - Affected IMSIs: 1,247

        2. 09:45 AM - 387 failures (298% above baseline)
           - Primary cause: MME resource exhaustion
           - Affected IMSIs: 892

        3. 09:20 AM - 256 failures (187% above baseline)
           - Primary cause: Signaling storm
           - Affected IMSIs: 634

        These spikes indicate a potential HSS database issue. I recommend:
        1. Check HSS database health and synchronization status
        2. Review MME resource utilization (CPU, memory)
        3. Investigate signaling storm root cause

        Would you like me to analyze cell tower handoff patterns during these events?
        ```

        **Observability:**
        - View tool invocation logs
        - See parameters passed to tools
        - Review tool results
        - Monitor response times
        - Track error rates
        """)


def render_guide_tab():
    """Render the Guide tab."""
    st.markdown("## Demo Guide Generation")

    st.markdown("""
    The demo guide provides a narrative structure, talk track, and presenter guidance
    for delivering compelling demonstrations.
    """)

    st.markdown("### Guide Structure")

    st.code("""
    Demo Guide Components:

    1. Executive Summary
       - Who is the customer?
       - What are their pain points?
       - Why Elasticsearch?

    2. Demo Narrative
       - Story arc
       - Problem → Solution → Value
       - Key insights to highlight

    3. Talk Track
       - What to say at each step
       - How to position features
       - Objection handling

    4. Technical Details
       - Query explanations
       - Architecture highlights
       - Sophisticated features to call out

    5. A-ha Moments
       - Key insights that resonate
       - "I didn't know Elasticsearch could do that!"
       - Value realization points
    """, language="text")

    with st.expander("**Guide Generation Process**"):
        st.markdown("""
        The guide is generated using LLM with context from the demo:
        """)

        st.code("""
# From module_generator.py

DEMO_GUIDE_PROMPT = '''
Generate a comprehensive demo guide for this Elasticsearch demonstration.

Customer Context:
- Company: {company}
- Department: {department}
- Industry: {industry}
- Pain Points: {pain_points}
- Use Cases: {use_cases}

Demo Assets:
- Datasets: {dataset_summary}
- Queries: {query_summary}
- Tools: {tool_summary}

Create a guide with:

1. **Executive Summary** (2-3 paragraphs)
   - Customer background and challenges
   - Why Elasticsearch is uniquely positioned to help
   - Expected outcomes from the demo

2. **Demo Narrative** (Story arc)
   - Opening: Establish pain point
   - Rising action: Show problem in data
   - Climax: Reveal solution with sophisticated query
   - Resolution: Show business value

3. **Talk Track** (Step-by-step presenter guidance)
   For each query:
   - Setup: "We're going to look at..."
   - Execution: "Notice how this query..."
   - Insight: "What this tells us is..."
   - Value: "This helps you..."

4. **Technical Highlights** (Sophistication showcase)
   - Advanced ES|QL commands used
   - Architecture decisions
   - Performance optimizations
   - Integration patterns

5. **A-ha Moments** (Key insights)
   - Moments that make prospects go "wow"
   - Capabilities they didn't know existed
   - Concrete ROI examples

6. **Objection Handling**
   - Common concerns
   - Prepared responses
   - Competitive positioning

7. **Next Steps** (After demo)
   - Trial setup
   - POC planning
   - Technical deep dives
'''
        """, language="python")

    with st.expander("**Executive Summary**"):
        st.markdown("""
        Example executive summary:
        """)

        st.markdown("""
        **T-Mobile Network Operations Demo**

        **Customer Profile:**
        T-Mobile is one of the leading mobile network operators in the United States,
        serving millions of subscribers across 4G LTE and 5G networks. Their Network
        Operations team is responsible for monitoring and maintaining critical infrastructure
        including MME hosts, HSS databases, cell towers, and core network components.

        **Key Challenges:**
        - **Reactive Troubleshooting**: Currently, issues are only detected after help desk
          is overwhelmed with subscriber complaints
        - **HSS Database Failures**: Database corruption and synchronization issues cause
          mass authentication failures
        - **Signaling Storms**: MME software bugs and resource exhaustion lead to network instability
        - **Security Threats**: Rogue network attempts and SS7 attacks are difficult to detect

        **Why Elasticsearch:**
        Elasticsearch's ES|QL query language with advanced commands like INLINESTATS and
        LOOKUP JOIN enables proactive anomaly detection by comparing real-time metrics against
        baseline patterns. This shifts operations from reactive to proactive, detecting issues
        before they impact subscribers.

        **Expected Outcomes:**
        - Detect authentication spikes within minutes (vs. hours currently)
        - Identify root causes faster (database vs. equipment vs. attack)
        - Reduce mean time to resolution (MTTR) by 70%
        - Prevent subscriber impact through early warning alerts
        """)

    with st.expander("**Demo Narrative**"):
        st.markdown("""
        The narrative creates a compelling story arc:
        """)

        st.markdown("""
        **Act 1: Establish the Problem**

        "Let me show you a typical day in T-Mobile's Network Operations Center.
        It's 10:15 AM, and suddenly the help desk starts getting flooded with calls -
        subscribers can't authenticate to the network. By the time you realize there's
        a problem, you're already in crisis mode."

        **Act 2: Show the Problem in Data**

        "Let's look at what's happening in the data. This query tracks unique IMSI counts
        over time - these are your subscribers trying to authenticate. Notice anything unusual?"

        [Run Query 1: Baseline IMSI counts]

        "Everything looks normal for the past 24 hours. But let's use INLINESTATS to compare
        current activity against the baseline..."

        [Run Query 2: INLINESTATS spike detection]

        "There it is - at 10:15 AM, we see a 412% spike in authentication failures. But more
        importantly, Elasticsearch detected this pattern within 5 minutes of it starting."

        **Act 3: Reveal the Solution**

        "Now let's use LOOKUP JOIN to enrich this data with HSS database health metrics..."

        [Run Query 3: LOOKUP JOIN with database metrics]

        "And there's your root cause - the HSS database in us-east went into a split-brain
        scenario at 10:13 AM, two minutes before the subscriber impact. With Elasticsearch,
        you would have been alerted before the first help desk call."

        **Act 4: Show Business Value**

        "Let's quantify the impact. Your help desk gets $50 per call, and you received 1,247
        calls about this incident. That's $62,350 in support costs - not counting the
        subscriber churn and SLA violations."

        [Run Query 4: Cost analysis]

        "With proactive detection, you prevent 90% of those calls. That's $56,000 saved on
        this incident alone. And you're seeing 3-4 incidents per week..."
        """)

    with st.expander("**Talk Track**"):
        st.markdown("""
        Detailed presenter guidance for each query:
        """)

        st.code("""
Query 1: "Baseline IMSI Count Tracking"

**Setup:**
"Let's start by looking at your normal authentication patterns. This query
tracks the number of unique subscribers (IMSIs) attempting authentication
over time."

**Execution:**
"Notice how I'm using DATE_TRUNC to bucket by hour, and STATS to count
unique IMSIs. This gives us a baseline of what 'normal' looks like for
your network."

[Run query, show results]

**Insight:**
"You can see the typical pattern - around 100-200 unique IMSIs per hour
during normal operations. There's a slight uptick during morning hours
when people start their commute."

**Value:**
"This baseline is critical because it lets us detect anomalies. Without
this context, a spike of 500 IMSIs might not seem unusual - but compared
to your baseline of 150, it's a 233% increase."

**Technical Highlight:**
"One sophisticated aspect here is that we're using INLINESTATS in the next
query to calculate this baseline automatically. Elasticsearch computes the
rolling average within the same query - no need for separate baseline queries."

**Transition:**
"Now let's use that baseline to detect anomalies in real-time..."
        """, language="text")

    with st.expander("**Technical Highlights**"):
        st.markdown("""
        Showcase the sophisticated features:
        """)

        st.markdown("""
        **Advanced ES|QL Commands**

        1. **INLINESTATS for Anomaly Detection**
           ```sql
           | INLINESTATS baseline = AVG(failure_count) BY region
           | EVAL deviation = (failure_count - baseline) / baseline
           | WHERE deviation > 0.5
           ```
           - Calculates rolling baseline within the same query
           - No need for separate aggregation passes
           - Real-time comparison of current vs. baseline
           - Detects spikes, drops, and anomalies instantly

        2. **LOOKUP JOIN for Data Enrichment**
           ```sql
           FROM events-data*
           | LOOKUP JOIN database-status ON region_id
           | WHERE database_status == "degraded"
           ```
           - Enriches event stream with reference data
           - Correlates failures with infrastructure health
           - Joins happen at query time, not indexing
           - Multiple lookup tables supported

        3. **Multi-Lag Analysis for Trend Detection**
           ```sql
           | INLINESTATS
               lag1 = LAG(count, 1),
               lag2 = LAG(count, 2),
               lag3 = LAG(count, 3)
           | EVAL sustained_spike =
               (count > lag1 * 1.5) AND
               (lag1 > lag2 * 1.5) AND
               (lag2 > lag3 * 1.5)
           ```
           - Detects sustained patterns vs. transient blips
           - Three consecutive periods of increase = real problem
           - Reduces false positive alerts

        4. **Semantic Search Pipeline**
           ```sql
           FROM providers-lookup
           | MATCH provider_name WITH "cardiologist"
                   AND bio WITH "heart disease"
           | RERANK top = 10
           | COMPLETION context = CONCAT(...)
           ```
           - Three-stage semantic search
           - Vector-based initial retrieval
           - Cross-encoder reranking
           - LLM-powered natural language responses

        **Architecture Decisions**

        - **data_stream for Time-Series**: Automatic lifecycle management
        - **lookup Indices for Reference Data**: Optimized for LOOKUP JOIN
        - **semantic_text Fields**: Automatic vector embedding
        - **Query-First Data Generation**: Data exhibits patterns queries need

        **Performance Optimizations**

        - Bulk indexing with 500 doc batches
        - Filtered time ranges (only last 7-30 days)
        - Low-cardinality fields for grouping (region, status)
        - INLINESTATS instead of separate baseline queries
        """)

    with st.expander("**A-ha Moments**"):
        st.markdown("""
        Key moments that create impact:
        """)

        st.markdown("""
        **1. "INLINESTATS lets you detect anomalies in a single query"**

        Most prospects think they need:
        - Separate query to calculate baseline
        - Store baseline somewhere
        - Another query to compare against baseline
        - Complex alerting logic

        A-ha: "INLINESTATS does all of this in one query, in real-time"

        ---

        **2. "You can join event streams with reference data at query time"**

        Most prospects think they need:
        - Enrich events at ingest time
        - Duplicate reference data in every event
        - Complex pipelines to keep data in sync

        A-ha: "LOOKUP JOIN enriches at query time - update the lookup table and
        all queries instantly see the new data, no reindexing needed"

        ---

        **3. "Semantic search isn't just keyword matching"**

        Most prospects think semantic search is:
        - Fancier keyword search
        - Synonym handling
        - Maybe fuzzy matching

        A-ha: "MATCH uses vector embeddings to understand meaning. Search for
        'heart doctor' and find 'cardiologist' - no synonyms needed, the model
        understands they're semantically similar"

        ---

        **4. "The query language can do statistical analysis"**

        Most prospects think:
        - ES|QL is just for filtering and aggregation
        - Statistical analysis requires external tools
        - Need to export data for trend detection

        A-ha: "ES|QL has INLINESTATS for rolling averages, LAG for time-series
        analysis, CASE for conditional logic - full statistical capabilities
        built into the query language"

        ---

        **5. "This demo was generated from a natural language description"**

        Most prospects think:
        - Demos take weeks to build
        - Require deep Elasticsearch expertise
        - Hard to customize for their specific use case

        A-ha: "I described your pain points in plain English, and the system
        generated realistic data, sophisticated queries, and this entire demo
        in under 2 minutes. We can rebuild it for your exact scenario right now."
        """)

    st.markdown("### Guide Usage")

    with st.expander("**Before the Demo**"):
        st.markdown("""
        Preparation using the guide:

        1. **Read Executive Summary** (5 min)
           - Understand customer background
           - Memorize key pain points
           - Internalize positioning

        2. **Review Demo Narrative** (10 min)
           - Understand the story arc
           - Identify key moments
           - Plan transitions between queries

        3. **Practice Talk Track** (20 min)
           - Rehearse query explanations
           - Practice value positioning
           - Time the demo flow

        4. **Study Technical Highlights** (15 min)
           - Understand sophisticated features
           - Prepare for technical questions
           - Review architecture decisions

        5. **Prepare A-ha Moments** (10 min)
           - Identify 2-3 key insights
           - Plan how to reveal them
           - Prepare impact statements
        """)

    with st.expander("**During the Demo**"):
        st.markdown("""
        Using the guide during presentation:

        - **Follow the narrative structure** for compelling flow
        - **Use talk track verbatim** for first few demos (then adapt)
        - **Call out technical highlights** to showcase sophistication
        - **Pause at a-ha moments** to let insights land
        - **Reference pain points** frequently to maintain relevance
        """)

    with st.expander("**After the Demo**"):
        st.markdown("""
        Post-demo follow-up:

        - **Share the guide** with prospect for reference
        - **Highlight objection handling** section if concerns raised
        - **Review next steps** section for clear path forward
        - **Customize guide** based on feedback for future demos
        """)
