"""
Under the Hood - Technical deep dive into Vulcan architecture.

This view showcases the sophisticated query generation, data profiling,
and modular architecture that powers Vulcan.
"""

import streamlit as st


def render_under_the_hood():
    """Render the Under the Hood technical documentation page."""

    st.title("💡 About Vulcan")
    st.caption("What Vulcan is, how it works, and what it generates")

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
    """Render the Overview tab — story-driven narrative aid for demos."""

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown("## What is Vulcan?")
    st.markdown("""
The best demos feel like they live in the customer's world — their industry, their KPIs,
their terminology. But building that from scratch for every prospect takes hours you don't
have, and generic demos just don't land the same way.

**Vulcan solves that.** Describe the customer in plain language — their company, department,
and pain points — and Vulcan generates a complete, custom Elastic Agent Builder demo
end-to-end: synthetic datasets shaped to the domain, sophisticated ES|QL queries grounded
in real indexed data, Agent Builder tool definitions, and a full talk track with a demo guide.

The whole pipeline takes 10–20 minutes. What comes out is a demo that uses the customer's
vocabulary, reflects realistic patterns in their domain, and is ready to run live in Agent Builder.
    """)

    st.divider()

    # ── Section 1: The problem — generic vs bespoke ───────────────────────────
    st.markdown("## The Problem with Generic Demos")
    st.markdown(
        "An LLM can write ES|QL queries — but that doesn't mean they'll produce results "
        "compelling enough to showcase Elastic's capabilities. The difference is context."
    )

    col_bad, col_good = st.columns(2, gap="large")

    with col_bad:
        st.error("#### ❌ Generic (no customer context)")
        st.markdown("**Data fields**")
        st.code(
            "user_id, event_type, value,\ntimestamp, status, category",
            language="text"
        )
        st.markdown("**Sample query**")
        st.code(
            "FROM logs\n| STATS count(*) BY status\n| LIMIT 10",
            language="text"
        )
        st.markdown("**Talk track**")
        st.markdown(
            "_\"Here you can see how many events occurred by status type...\"_"
        )
        st.caption("No industry vocabulary. No realistic patterns. Hard to relate to.")

    with col_good:
        st.success("#### ✅ Vulcan-generated (Telco Network Ops)")
        st.markdown("**Data fields**")
        st.code(
            "tower_id, network_segment, error_code,\nimsi, mme_host, affected_subscribers,\nevent_type, cascade_severity",
            language="text"
        )
        st.markdown("**Sample query**")
        st.code(
            'FROM network_events\n'
            '| WHERE event_type == "handoff_failure"\n'
            '| EVAL time_bucket = DATE_TRUNC(10 minutes, @timestamp)\n'
            '| STATS\n'
            '    failure_count        = COUNT(*),\n'
            '    affected_subscribers = SUM(TO_LONG(affected_subscribers)),\n'
            '    unique_towers        = COUNT_DISTINCT(tower_id),\n'
            '    error_types          = VALUES(error_code)\n'
            '    BY time_bucket, network_segment\n'
            '| INLINESTATS\n'
            '    avg_failures    = AVG(failure_count),\n'
            '    stddev_failures = STD_DEV(failure_count)\n'
            '    BY network_segment\n'
            '| EVAL z_score = (failure_count - avg_failures)\n'
            '               / COALESCE(stddev_failures, 1)\n'
            '| EVAL cascade_severity = CASE(\n'
            '    unique_towers >= 5 AND z_score > 3, "Critical Cascade",\n'
            '    unique_towers >= 3 AND z_score > 2, "Moderate Cascade",\n'
            '    unique_towers >= 2,                 "Localized Issue"\n'
            '  )\n'
            '| WHERE unique_towers >= 2\n'
            '| SORT z_score DESC, unique_towers DESC\n'
            '| LIMIT 100',
            language="esql"
        )
        st.markdown("**Talk track**")
        st.markdown(
            "_\"See these cascade events? When three or more adjacent towers start failing "
            "handoffs simultaneously, that's not random — it's a configuration drift or hardware "
            "fault propagating across the radio network. This query catches it in real time.\"_"
        )
        st.caption("Domain vocabulary. Realistic distributions. Ready to present.")

    st.divider()

    # ── Section 2: The pipeline ───────────────────────────────────────────────
    st.markdown("## How It Works — The Pipeline")
    st.markdown(
        "Vulcan doesn't fill in a template. It runs a multi-stage pipeline where each "
        "phase informs the next — and critically, **queries are planned before data is generated**, "
        "so the data is shaped to make the queries compelling."
    )

    st.markdown("")

    p1, p2, p3, p4, p5 = st.columns(5, gap="small")
    for col, num, label in [
        (p1, "1", "Understand\nthe Customer"),
        (p2, "2", "Plan the\nQuery Strategy"),
        (p3, "3", "Generate &\nIndex Data"),
        (p4, "4", "Profile &\nWrite Queries"),
        (p5, "5", "Deploy to\nAgent Builder"),
    ]:
        with col:
            st.markdown(
                f"<div style='text-align:center; padding:10px; background:#1e3a5f; "
                f"border-radius:8px; height:90px; display:flex; flex-direction:column; "
                f"justify-content:center;'>"
                f"<div style='font-size:1.4em; font-weight:bold; color:#4fa8e8;'>{num}</div>"
                f"<div style='font-size:0.8em; color:#ccc; white-space:pre-line;'>{label}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

    st.markdown("")

    with st.expander("**Stage 1 — Understand the Customer** (context extraction + alignment)", expanded=True):
        col_a, col_b = st.columns(2, gap="large")
        with col_a:
            st.markdown("**You provide (plain language):**")
            st.info(
                "_\"Telco Network Operations team. They're dealing with HSS database sync "
                "failures causing authentication outages. They want proactive anomaly detection "
                "on MME nodes and cell tower failure pattern analysis across datacenters.\"_"
            )
        with col_b:
            st.markdown("**Vulcan extracts:**")
            st.code(
                'company:      "Telco"\n'
                'department:   "Network Operations"\n'
                'industry:     "Telecommunications"\n'
                'pain_points:  ["HSS sync failures",\n'
                '               "auth outages"]\n'
                'use_cases:    ["MME anomaly detection",\n'
                '               "cell tower analysis"]\n'
                'demo_type:    "analytics"  ← auto-detected',
                language="yaml"
            )
        st.caption(
            "The extracted context is surfaced back to you for review and editing before anything is built."
        )

    with st.expander("**Stage 2 — Plan the Query Strategy** (queries first, data second)"):
        st.markdown(
            "Before a single row of data is generated, Vulcan plans the query strategy — "
            "deciding what business questions the demo will answer and what fields and "
            "distributions the data must have to make those queries return interesting results."
        )
        col_a, col_b = st.columns(2, gap="large")
        with col_a:
            st.markdown("**Planned queries (examples):**")
            st.markdown(
                "- MME nodes with failure rates > fleet average *(INLINESTATS)*\n"
                "- HSS sync failures correlated by datacenter *(LOOKUP JOIN)*\n"
                "- Signaling storm detection via IMSI spike analysis *(STATS + CHANGE_POINT)*\n"
                "- Cell tower failure rate trends over 24h *(DATE_TRUNC + STATS)*"
            )
        with col_b:
            st.markdown("**Data requirements derived from queries:**")
            st.markdown(
                "- `failure_count` must be lognormal (so percentile queries are interesting)\n"
                "- `mme_host` cardinality: 12–20 distinct nodes\n"
                "- `hss_node_id` must be a join-able reference dataset\n"
                "- `@timestamp` must span 30 days for trend analysis"
            )

        with st.expander("📋 See the prompts Vulcan uses to expand your brief input"):
            st.markdown(
                "When 'Prompt expansion' is enabled in Settings, Vulcan feeds your brief "
                "description through one of two templates before generation begins — one for "
                "**Observability & Analytics** demos, one for **Search & Retrieval** demos. "
                "The result is a rich, domain-specific context document that drives all "
                "downstream pipeline stages.\n\n"
                "📄 [View the full expansion prompts on GitHub]"
                "(https://github.com/elastic/vulcan/blob/main/docs/EXPANSION_PROMPTS.md)"
            )

    with st.expander("**Stage 3 — Generate & Index Data** (shaped to the strategy)"):
        col_a, col_b = st.columns(2, gap="large")
        with col_a:
            st.markdown("**Custom Python generated per demo:**")
            st.code(
                "# Generates realistic Telco network events\n"
                "# with distributions tuned to make queries land\n"
                "failure_count = np.random.lognormal(\n"
                "    mean=2.1, sigma=1.4, size=n\n"
                ")  # skewed: most nodes healthy, few anomalous\n\n"
                "mme_host = np.random.choice(\n"
                "    ['mme-sea-01', 'mme-sea-02', ..., 'mme-atl-04'],\n"
                "    size=n, p=weights  # weighted: some hosts hotter\n"
                ")",
                language="python"
            )
            st.caption(
                "Generated using **pandas** (DataFrames), **NumPy** (distributions: "
                "lognormal, Poisson, normal, choice with weights), **random** (sampling, "
                "shuffling), and Python's **datetime/timedelta** (time-series generation). "
                "Each demo gets its own custom `data_generator.py` — no shared templates."
            )
        with col_b:
            st.markdown("**Indexed to Elasticsearch:**")
            st.metric("Datasets", "3")
            st.metric("Total records", "~47,500")
            st.metric("Semantic text fields", "2")
            st.caption(
                "Data streams for time-series events; lookup indices for "
                "reference data used in LOOKUP JOIN."
            )

    with st.expander("**Stage 4 — Profile & Write Queries** (grounded in real data)"):
        st.markdown(
            "After indexing, Vulcan profiles the actual data — inspecting field cardinality, "
            "value distributions, and date ranges. **Queries are then written against what's "
            "actually in Elasticsearch**, not against assumptions. This is what makes them work."
        )

        col_prof, col_rules = st.columns(2, gap="large")
        with col_prof:
            st.markdown("**What profiling captures (example):**")
            st.code(
                "index: telco_network_events\n"
                "  total_docs:   47,312\n"
                "  date_range:   2025-02-04 → 2026-03-06\n"
                "  fields:\n"
                "    mme_host:         14 distinct values\n"
                "    network_segment:  ['RAN', 'Core', 'Edge']\n"
                "    failure_count:    min=0, max=312, p95=89\n"
                "    error_code:       23 distinct values\n"
                "    hss_node_id:      join key → hss_nodes index",
                language="yaml"
            )
            st.caption(
                "Cardinality, value samples, and date ranges are fed directly into "
                "the query generation prompt — so field names, filter values, and "
                "JOIN keys are always real, not guessed."
            )
        with col_rules:
            st.markdown("**Query generation is governed by strict rules:**")
            st.markdown(
                "Vulcan's LLM is constrained by a detailed ES|QL ruleset covering "
                "correct syntax, proven patterns, and explicit anti-patterns. "
                "Key rules enforced:"
            )
            st.markdown(
                "- `LOOKUP JOIN`: field must exist in **both** indices; no table prefix after join\n"
                "- `INLINESTATS`: compute baselines inline — no pre-aggregated tables needed\n"
                "- `FORK` + `FUSE LINEAR`: parallel branches, no named branches, no comments inside\n"
                "- `COMPLETION`: must follow `MATCH`/`QSTR`; `inference_id` required\n"
                "- `@timestamp`: never parameterize — use `NOW()` for recency\n"
                "- Parameters: `?name` syntax only; no NULL checks; string literals only"
            )
            st.markdown(
                "📄 [ES|QL patterns & rules](https://github.com/elastic/vulcan/blob/main/src/prompts/esql_strict_rules.py) · "
                "[Command reference docs](https://github.com/elastic/vulcan/tree/main/docs/esql)",
                unsafe_allow_html=False
            )

        st.markdown("**Example — Cell Tower Handoff Cascade Failure Analysis:**")
        st.code(
            "FROM network_events\n"
            "| WHERE event_type == \"handoff_failure\"\n"
            "| EVAL time_bucket = DATE_TRUNC(10 minutes, @timestamp)\n"
            "| STATS\n"
            "    failure_count    = COUNT(*),\n"
            "    affected_subscribers = SUM(TO_LONG(affected_subscribers)),\n"
            "    unique_towers    = COUNT_DISTINCT(tower_id),\n"
            "    error_types      = VALUES(error_code)\n"
            "    BY time_bucket, network_segment\n"
            "| INLINESTATS\n"
            "    avg_failures    = AVG(failure_count),\n"
            "    stddev_failures = STD_DEV(failure_count)\n"
            "    BY network_segment\n"
            "| EVAL z_score = (failure_count - avg_failures) / COALESCE(stddev_failures, 1)\n"
            "| EVAL cascade_severity = CASE(\n"
            "    unique_towers >= 5 AND z_score > 3, \"Critical Cascade\",\n"
            "    unique_towers >= 3 AND z_score > 2, \"Moderate Cascade\",\n"
            "    unique_towers >= 2,                 \"Localized Issue\"\n"
            "  )\n"
            "| WHERE unique_towers >= 2\n"
            "| EVAL towers_per_minute = ROUND(TO_DOUBLE(unique_towers) / 10.0, 1)\n"
            "| SORT z_score DESC, unique_towers DESC, failure_count DESC\n"
            "| LIMIT 100",
            language="esql"
        )
        st.caption(
            "Uses INLINESTATS to compute per-segment baselines inline, then z-scores each "
            "time bucket to classify cascade severity. No pre-aggregated table needed. "
            "Queries are validated against the live index and refined iteratively — "
            "parameterized variants become Agent Builder tools."
        )

    with st.expander("**Stage 5 — You take control** (validate, deploy, deliver)"):
        st.markdown(
            "Generation produces the raw materials. **This stage is yours** — Vulcan gives you "
            "a structured workflow to validate, deploy, and then deliver the demo."
        )

        col_a, col_b = st.columns(2, gap="large")
        with col_a:
            st.markdown("**Your workflow in the Queries tab:**")
            st.markdown(
                "1. **Run each query** against the live index — see real results\n"
                "2. **Mark as validated** — promotes the query to a tool candidate\n"
                "3. **Edit tool metadata** — review the auto-generated `tool_id`, "
                "description, and tags; adjust before saving\n"
                "4. **Deploy tools** — pushes each validated query to Agent Builder "
                "as a callable tool\n"
            )
            st.markdown("**Then in the Agents tab:**")
            st.markdown(
                "5. **Review agent config** — name, instructions, avatar auto-generated\n"
                "6. **Deploy the agent** — creates the agent in Agent Builder\n"
                "7. **Link tools → agent** — assigns all deployed tools to the agent\n"
            )
            st.markdown("**Finally, the Script tab:**")
            st.markdown(
                "8. **Use the auto-generated demo guide** — talk track, key insights, "
                "suggested questions, and 'aha moment' prompts — to run the live demo "
                "in Agent Builder with confidence\n"
            )
        with col_b:
            st.markdown("**Example tool definitions (auto-generated):**")
            st.code(
                '{\n'
                '  "tool_id": "telco_network_ops_tower_handoff_cascade_failures",\n'
                '  "description": "Identifies cell tower handoff cascade failures\n'
                '    where multiple adjacent towers fail simultaneously —\n'
                '    indicating potential radio equipment failure or network\n'
                '    configuration problems.",\n'
                '  "tags": ["network", "cell-tower", "cascade", "anomaly"]\n'
                '}',
                language="json"
            )
            st.markdown("**Demo guide excerpt (auto-generated):**")
            st.info(
                "_\"Start with the cascade failure scan — no parameters needed, it runs "
                "fleet-wide. Point out the z-score column: this isn't just a count, it's "
                "statistically anomalous relative to that segment's own baseline. When the "
                "RAN Segment incident from Mar 6 surfaces with z-score 7.19, ask: 'How long "
                "would it take your team to find this today?' Then pivot to the parameterized "
                "auth failure tool — type LAC-1001 and show how the agent drills into a "
                "specific location area across all HSS nodes instantly.\"_"
            )

    st.divider()

    # ── Section 3: Search vs Analytics ───────────────────────────────────────
    st.markdown("## Two Demo Paths, One Pipeline")
    st.markdown(
        "Vulcan auto-detects whether a use case calls for a **search & retrieval** demo "
        "or an **observability & analytics** demo. The pipeline is the same — the query "
        "strategies, data shapes, and output artifacts are different."
    )

    col_search, col_analytics = st.columns(2, gap="large")

    with col_search:
        st.markdown("### 🔍 Search & Retrieval")
        st.markdown("*Triggered by: find, retrieve, lookup, knowledge base, semantic search*")
        st.markdown("**Elastic capabilities showcased:**")
        st.markdown(
            "- `FORK` + `FUSE LINEAR` for weighted hybrid BM25 + semantic search\n"
            "- `semantic_text` fields with ELSER for vector-based retrieval\n"
            "- Weighted score fusion with minmax normalization\n"
            "- RAG pipeline: `MATCH` → failed-session retrieval → `COMPLETION`\n"
            "- Content gap analysis from abandoned search sessions"
        )
        st.markdown("**Example use cases:**")
        st.markdown(
            "- Brand asset discovery (Brand Asset Platform)\n"
            "- Healthcare provider lookup (in-network search)\n"
            "- Policy & knowledge base retrieval\n"
            "- Support ticket semantic search"
        )

        st.markdown("**Query 1 — Campaign Theme Search** *(scripted hybrid)*:")
        st.code(
            "FROM marketing_asset_catalog\n"
            "    METADATA _id, _index, _score\n"
            "| FORK\n"
            "    (\n"
            "        WHERE MATCH(asset_title, \"E-commerce\")\n"
            "        | EVAL search_type = \"bm25\"\n"
            "        | SORT _score DESC | LIMIT 50\n"
            "    )\n"
            "    (\n"
            "        WHERE MATCH(\n"
            "            asset_description,\n"
            "            \"summer promotion warm weather outdoor seasonal\")\n"
            "        | EVAL search_type = \"semantic\"\n"
            "        | SORT _score DESC | LIMIT 50\n"
            "    )\n"
            "| FUSE LINEAR\n"
            "    WITH {\"weights\": {\"fork1\": 0.3, \"fork2\": 0.7},\n"
            "          \"normalizer\": \"minmax\"}\n"
            "| SORT _score DESC\n"
            "| LIMIT 20\n"
            "| KEEP asset_id, _score, asset_title, asset_description,\n"
            "       asset_type, campaign_theme, industry_tag,\n"
            "       popularity_score, search_type",
            language="esql"
        )

        with st.expander("▶ See it in Agent Builder — summer campaign results"):
            st.image(
                "src/ui/assets/screenshots/tmobile/agent_builder_chat_beacon_summer_assets_query.png",
                caption="Agent Builder reasoning + FORK/FUSE hybrid query execution"
            )
            st.image(
                "src/ui/assets/screenshots/tmobile/agent_builder_chat_beacon_summer_assets_response.png",
                caption="AI-synthesized asset recommendations with scoring rationale"
            )

        st.markdown("**Query 2 — Search Gap RAG Summary** *(parameterized RAG)*:")
        st.code(
            "FROM content_search_logs\n"
            "    METADATA _score\n"
            "| WHERE\n"
            "    MATCH(query_intent, ?industry) AND\n"
            "    (session_outcome == \"Abandoned\" OR\n"
            "     session_outcome == \"No Results Found\")\n"
            "| SORT _score DESC\n"
            "| LIMIT 10\n"
            "| EVAL prompt = CONCAT(\n"
            "    \"You are a content strategy analyst. Analyse these \",\n"
            "    \"failed search sessions and identify content gaps...\",\n"
            "    \"Query Text: \", query_text,\n"
            "    \"User Intent: \", query_intent,\n"
            "    \"Industry: \", industry_vertical,\n"
            "    \"Result Count: \", TO_STRING(result_count),\n"
            "    \"Identify: 1) Missing asset type, \",\n"
            "    \"2) Underserved vertical, \",\n"
            "    \"3) One concrete asset to create.\"\n"
            "  )\n"
            "| COMPLETION gap_analysis = prompt\n"
            "    WITH {\"inference_id\": \"completion-vulcan\"}\n"
            "| KEEP session_outcome, industry_vertical,\n"
            "       filters_applied, result_count,\n"
            "       gap_analysis, _score",
            language="esql"
        )

        with st.expander("▶ See it in Agent Builder — fitness gap analysis (industry=fitness businesses)"):
            st.image(
                "src/ui/assets/screenshots/tmobile/agent_builder_chat_beacon_gap_analysis_query.png",
                caption="Agent Builder reasoning + RAG pipeline execution (MATCH → COMPLETION)"
            )
            st.image(
                "src/ui/assets/screenshots/tmobile/agent_builder_chat_beacon_gap_analysis_response.png",
                caption="AI-synthesized content gap analysis grounded in real abandoned search sessions"
            )

    with col_analytics:
        st.markdown("### 📊 Observability & Analytics")
        st.markdown("*Triggered by: analyze, trend, metric, aggregate, monitor, dashboard*")
        st.markdown("**Elastic capabilities showcased:**")
        st.markdown(
            "- `INLINESTATS` for inline per-segment baselines + z-score anomaly detection\n"
            "- `LOOKUP JOIN` for cross-dataset enrichment (e.g. HSS node metadata)\n"
            "- `DATE_TRUNC` time-series bucketing\n"
            "- `VALUES()` to collect error codes per time window\n"
            "- `STD_DEV` + `COALESCE` for robust statistical scoring\n"
            "- `CASE` for severity classification"
        )
        st.markdown("**Example use cases:**")
        st.markdown(
            "- Network operations cascade failure detection (Telco)\n"
            "- Infrastructure cost & migration analysis (JPMC)\n"
            "- Campaign ROI & performance trends (Brand Asset Platform)\n"
            "- Multi-tenant SLA monitoring"
        )

        st.markdown("**Query 1 — Cell Tower Handoff Cascade Failure Analysis:**")
        st.code(
            "FROM network_events\n"
            "| WHERE event_type == \"handoff_failure\"\n"
            "| EVAL time_bucket = DATE_TRUNC(10 minutes, @timestamp)\n"
            "| STATS\n"
            "    failure_count        = COUNT(*),\n"
            "    affected_subscribers = SUM(TO_LONG(affected_subscribers)),\n"
            "    unique_towers        = COUNT_DISTINCT(tower_id),\n"
            "    error_types          = VALUES(error_code)\n"
            "    BY time_bucket, network_segment\n"
            "| INLINESTATS\n"
            "    avg_failures    = AVG(failure_count),\n"
            "    stddev_failures = STD_DEV(failure_count)\n"
            "    BY network_segment\n"
            "| EVAL z_score = (failure_count - avg_failures)\n"
            "               / COALESCE(stddev_failures, 1)\n"
            "| EVAL cascade_severity = CASE(\n"
            "    unique_towers >= 5 AND z_score > 3, \"Critical Cascade\",\n"
            "    unique_towers >= 3 AND z_score > 2, \"Moderate Cascade\",\n"
            "    unique_towers >= 2,                 \"Localized Issue\"\n"
            "  )\n"
            "| WHERE unique_towers >= 2\n"
            "| SORT z_score DESC, unique_towers DESC\n"
            "| LIMIT 100",
            language="esql"
        )

        with st.expander("▶ See it in Agent Builder — cascade results"):
            st.image("src/ui/assets/screenshots/tmobile/agent_builder_chat_handoff_query.png",
                     caption="Agent Builder reasoning + ES|QL query execution")
            st.image("src/ui/assets/screenshots/tmobile/agent_builder_chat_handoff_response.png",
                     caption="AI-synthesized response with cascade severity classification")

        st.markdown("**Query 2 — Auth Failure Search by Subscriber** *(parameterized)*:")
        st.code(
            "FROM authentication_logs\n"
            "| WHERE\n"
            "    imsi            == ?subscriber_id OR\n"
            "    location_area   == ?subscriber_id OR\n"
            "    subscriber_id   == ?subscriber_id\n"
            "| LOOKUP JOIN hss_nodes ON hss_node_id\n"
            "| EVAL is_failure  = CASE(failure_reason != \"success\", 1, 0)\n"
            "| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)\n"
            "| STATS\n"
            "    total_attempts = COUNT(*),\n"
            "    failures       = SUM(is_failure),\n"
            "    failure_types  = VALUES(failure_reason),\n"
            "    error_codes    = VALUES(error_code),\n"
            "    networks_used  = VALUES(network_type),\n"
            "    locations      = VALUES(location_area),\n"
            "    hss_nodes      = VALUES(hss_name)\n"
            "    BY time_bucket, imsi, subscriber_id\n"
            "| EVAL failure_rate =\n"
            "    ROUND(TO_DOUBLE(failures) / TO_DOUBLE(total_attempts) * 100, 2)\n"
            "| SORT time_bucket DESC\n"
            "| LIMIT 100",
            language="esql"
        )

        with st.expander("▶ See it in Agent Builder — LAC-1001 results"):
            st.image("src/ui/assets/screenshots/tmobile/agent_builder_chat_authfail_query.png",
                     caption="Agent Builder reasoning + parameterized ES|QL execution (subscriber_id=LAC-1001)")
            st.image("src/ui/assets/screenshots/tmobile/agent_builder_chat_authfail_response.png",
                     caption="AI-synthesized diagnostic report for LAC-1001")


def render_data_generation_tab():
    """Render the Data Generation tab."""
    st.markdown("## Data Generation")

    st.markdown("""
    Vulcan uses a **query-first approach**: the query strategy is planned first, then data is generated
    to satisfy those query requirements. This ensures generated data exhibits the patterns that make
    queries produce meaningful, realistic results.
    """)

    st.markdown("### Index Types")

    st.markdown("""
    | Type | Use Case | Example |
    |------|----------|---------|
    | `data_stream` | Time-series events with `@timestamp` | Logs, metrics, network events |
    | `lookup` | Reference/dimension data for LOOKUP JOIN | Providers, products, regions |
    """)

    st.markdown("### Semantic Text Detection")

    st.markdown("""
    For search demos, the query strategy identifies fields used in MATCH/RERANK/COMPLETION
    commands and marks them as `semantic_text`. The data generator then produces rich text
    content for those fields, and indexing applies ELSER inference endpoints automatically.
    """)

    st.markdown("### Scale")

    st.markdown("""
    Dataset size is controlled internally (currently defaults to **large** for analytics demos).
    The LLM receives strict per-dataset and total document limits:

    | Size | Per Dataset | Time-Series | Reference/Lookup | Total Max |
    |------|------------|-------------|------------------|-----------|
    | Small | 200-500 | 1,000-2,000 | 50-200 | 5,000 |
    | Medium | 500-1,500 | 3,000-6,000 | 200-1,000 | 15,000 |
    | **Large** (default) | **2,000-5,000** | **10,000-20,000** | **500-2,000** | **50,000** |

    Search demos use fixed sizes (500-1,000 documents, 200-500 reference) regardless of this setting.
    """)



def render_data_generation_tab():
    """Render the Data Generation tab."""
    st.markdown("## Data Generation")

    st.markdown("""
    Vulcan uses a **query-first approach**: the query strategy is planned first, then data is generated
    to satisfy those query requirements. This ensures generated data exhibits the patterns that make
    queries produce meaningful, realistic results.
    """)

    st.markdown("### Statistical Distributions")

    st.markdown("""
    Each demo gets a custom `data_generator.py` — no shared templates. The LLM selects from
    statistical distributions to create realistic domain-specific data:
    """)

    with st.expander("**NumPy distributions used in generated code**", expanded=True):
        st.markdown("""
        | Distribution | Use Case | Example |
        |---|---|---|
        | `np.random.beta(a, b)` | Rates, percentages, utilization | `beta(2, 5)` → skewed low for baseline CPU; `beta(5, 2)` → skewed high during incidents |
        | `np.random.lognormal(mean, sigma)` | Durations, byte counts, reuse counts | `lognormal(4, 1)` → call durations with realistic long tail |
        | `np.random.normal(mu, sigma)` | Geographic coordinates, continuous values | `normal(0, 0.5)` → lat/lon jitter around tower locations |
        | `np.random.choice(a, p=weights)` | Weighted categoricals | Protocol distribution: S1AP 25%, NAS 25%, DIAMETER 20%, GTP-C 15% |
        | `np.random.poisson(lam)` | Event counts per interval | Failure counts per time bucket |
        | `np.random.randint(low, high)` | ID generation, counts | Unique asset IDs across range |

        **Why this matters**: A `beta(2, 8)` distribution for failure rates means most nodes are healthy
        (rate near 0) with a few anomalous outliers — making INLINESTATS z-score queries produce
        genuinely interesting results instead of flat noise.
        """)

    with st.expander("**Weighted categorical choices**"):
        st.code("""
# Real example from generated telco data_generator.py

vendors = {'Ericsson': 35, 'Nokia': 30, 'Huawei': 20, 'Samsung': 10, 'ZTE': 5}
tower_vendor = self.safe_choice(
    list(vendors.keys()),
    weights=list(vendors.values())
)

protocols = {'S1AP': 25, 'NAS': 25, 'DIAMETER': 20, 'GTP-C': 15, 'SS7': 10, 'SIP': 5}
proto = self.safe_choice(
    list(protocols.keys()),
    weights=list(protocols.values())
)
        """, language="python")

        st.markdown("""
        The `safe_choice()` helper normalizes weights to probabilities automatically and
        handles complex types (lists, dicts) by falling back from NumPy to Python's
        `random.choices` when needed.
        """)

    with st.expander("**Pandas DataFrame construction**"):
        st.markdown("""
        Generated code uses two patterns depending on whether rows have dependencies:

        **Vectorized** (independent rows — faster):
        ```python
        return pd.DataFrame({
            '@timestamp': timestamps,
            'session_id': session_ids,
            'session_duration_seconds': [str(d) for d in durations],
            'bytes_transferred': [str(b) for b in bytes_xfer],
        })
        ```

        **Row-wise** (when fields depend on each other):
        ```python
        rows = []
        for i in range(n):
            is_incident = timestamps[i] in incident_windows
            rows.append({
                'cpu': round(np.random.beta(5, 2) * 100, 1) if is_incident
                       else round(np.random.beta(2, 5) * 100, 1),
                ...
            })
        return pd.DataFrame(rows)
        ```
        """)

    st.markdown("### Index Types")

    st.markdown("""
    | Type | Use Case | Example |
    |------|----------|---------|
    | `data_stream` | Time-series events with `@timestamp` | Logs, metrics, network events |
    | `lookup` | Reference/dimension data for LOOKUP JOIN | Providers, products, regions |
    """)

    st.markdown("### Semantic Text Detection")

    st.markdown("""
    For search demos, the query strategy identifies fields used in MATCH/RERANK/COMPLETION
    commands and marks them as `semantic_text`. The data generator then produces rich text
    content for those fields, and indexing applies ELSER inference endpoints automatically.

    Fields can also be **auto-detected**: any string field with an average length > 50
    characters is automatically mapped as `semantic_text` with the `.elser-2-elasticsearch`
    inference endpoint.
    """)

    with st.expander("**Explicit vs auto-detected semantic fields**"):
        st.markdown("""
        **Explicit** — declared by the data generator:
        ```python
        def get_semantic_fields(self) -> Dict[str, List[str]]:
            return {
                'core_network_events': ['event_description', 'alert_message'],
                'mme_bug_signatures': ['bug_title', 'bug_description'],
            }
        ```

        **Auto-detected** — during mapping generation:
        ```python
        if pd.api.types.is_string_dtype(df[col]):
            avg_length = df[col].astype(str).str.len().mean()
            if avg_length > 50:
                mappings["properties"][col] = {
                    "type": "semantic_text",
                    "inference_id": ".elser-2-elasticsearch"
                }
        ```
        """)

    st.markdown("### Scale")

    st.markdown("""
    Dataset size is controlled internally (currently defaults to **large** for analytics demos).
    The LLM receives strict per-dataset and total document limits:

    | Size | Per Dataset | Time-Series | Reference/Lookup | Total Max |
    |------|------------|-------------|------------------|-----------|
    | Small | 200-500 | 1,000-2,000 | 50-200 | 5,000 |
    | Medium | 500-1,500 | 3,000-6,000 | 200-1,000 | 15,000 |
    | **Large** (default) | **2,000-5,000** | **10,000-20,000** | **500-2,000** | **50,000** |

    Search demos use fixed sizes (500-1,000 documents, 200-500 reference) regardless of this setting.
    """)


def render_query_generation_tab():
    """Render the Query Generation tab."""
    st.markdown("## Query Generation")

    st.markdown("""
    Vulcan generates three types of ES|QL queries, routed by demo type (analytics vs search).
    Each query is tested against real indexed data and iteratively refined until it returns results.
    """)

    st.markdown("### Three Query Types")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **Scripted**
        - No parameters, fixed logic
        - Directly testable
        - Uses `NOW() - X days` for time
        - Best for fleet-wide scans
        """)

    with col2:
        st.markdown("""
        **Parameterized**
        - `?param` syntax for user input
        - Values from data profiling
        - Business dates only (not `@timestamp`)
        - Best for drill-down queries
        """)

    with col3:
        st.markdown("""
        **Completion**
        - MATCH → RERANK → COMPLETION
        - Semantic search pipeline
        - LLM-generated answers from data
        - Best for search/RAG demos
        """)

    st.markdown("### Iterative Testing & Refinement")

    st.markdown("""
    Generated queries are tested against the live Elasticsearch cluster. If a query fails
    or returns zero results, the system automatically attempts to fix it (up to 3 attempts):
    """)

    with st.expander("**How query refinement works**", expanded=True):
        st.markdown("""
        1. **Syntax errors** → LLM rewrites the query with the error message as context
        2. **Zero results** → Constraint relaxation: expand time ranges, lower thresholds, remove restrictive filters
        3. **Parameterized queries** → Temporarily converted to scripted queries for testing by
           substituting real values from Elasticsearch via sample queries

        The `fix_query()` function receives the current ES|QL, the error message, and the full
        data profile, then asks the LLM to produce a corrected version. Each fix attempt is logged
        in `query_testing_results.json` for debugging.
        """)

    st.markdown("### Anti-Pattern Detection")

    st.markdown("""
    The query generator prevents common ES|QL mistakes through prompt-level warnings
    and **two post-generation scanners** that catch silent failures:

    | Anti-Pattern | Problem | Fix | Detection |
    |---|---|---|---|
    | Integer division | `95/100` truncates to `0` | `TO_DOUBLE()` | Post-gen scanner |
    | Missing NULL check | `!= "success"` drops NULLs | `OR field IS NULL` | Post-gen scanner |
    | Window functions | `LAG`, `LEAD`, `OVER` don't exist | `INLINESTATS` | Syntax error |
    | `@timestamp` params | System field, can't parameterize | `NOW() - X days` | Strategy validation |
    | `DATE_EXTRACT` | Wrong command for bucketing | `DATE_TRUNC` | Syntax error |
    | `COUNT_DISTINCT` | Doesn't exist in ES|QL | `COUNT(DISTINCT field)` | Syntax error |
    """)

    with st.expander("**Integer division scanner (silent wrong results)**"):
        st.markdown("""
        This is the most dangerous anti-pattern because the query **succeeds** but returns
        wrong numbers. The scanner examines every EVAL statement with division:

        ```sql
        -- ❌ Returns 0 (integer division truncates the decimal)
        | EVAL success_rate = ((total - failures) / total) * 100

        -- ✅ Returns 95.0 (correct)
        | EVAL success_rate = ((total - failures) / TO_DOUBLE(total)) * 100
        ```

        The scanner checks for missing `TO_DOUBLE()`, float literals, or multiply-by-float-first
        patterns. Percentage calculations (field names containing 'rate' or 'pct') get extra
        flagging. Results are saved to `query_testing_results.json` with suggested fixes.
        """)

    with st.expander("**NULL handling scanner (silent data loss)**"):
        st.markdown("""
        ES|QL silently excludes NULL values from negative filters. For security queries,
        this means **missing data = missed threats**:

        ```sql
        -- ❌ Silently excludes docs where status is NULL
        | WHERE status != "success"

        -- ✅ Includes all non-success rows (including NULL)
        | WHERE status != "success" OR status IS NULL
        ```

        The scanner detects `!=`, `NOT(...)`, and `NOT LIKE` patterns, checks for missing
        `OR field IS NULL` clauses, and flags security-related queries (keywords: `security`,
        `auth`, `threat`, `compliance`, `audit`, `siem`) with CRITICAL warnings.
        """)

    st.markdown("### ES|QL Rules Reference")

    st.markdown("""
    All 20 syntax rules are maintained in `src/prompts/esql_strict_rules.py` and injected
    into every query generation prompt. Key rules include:
    - **LOOKUP JOIN**: no `_lookup` suffix, no table prefix on joined fields
    - **MATCH**: function syntax inside WHERE, not a pipe command
    - **FORK**: unnamed branches, no comments inside
    - **COMPLETION**: requires `inference_id`, must follow retrieval
    - **EVAL variable reuse**: can't reference new variables in same EVAL
    - **Date arithmetic**: wrap in `TO_LONG()` before subtracting
    """)


def render_data_indexing_tab():
    """Render the Data Indexing tab."""
    st.markdown("## Data Indexing")

    st.markdown("""
    Data indexing happens **automatically during generation** — Vulcan creates indices,
    applies mappings, bulk-indexes documents, and profiles the results without manual intervention.
    """)

    st.markdown("### Index Modes & Mapping")

    st.markdown("""
    | Mode | Created As | Mapping Includes |
    |------|-----------|-----------------|
    | `data_stream` | Data stream with `@timestamp` | Date, keyword, numeric fields |
    | `lookup` | Standard index with `index.mode: lookup` | Join keys, keyword/text fields |

    Fields identified as `semantic_text` get an ELSER inference endpoint attached —
    documents are automatically vectorized on indexing.
    """)

    with st.expander("**Mapping type inference from pandas**"):
        st.markdown("""
        The indexer inspects each pandas column to determine the Elasticsearch mapping:

        | Pandas dtype | ES Mapping | Additional Logic |
        |---|---|---|
        | `int64` | `long` | — |
        | `float64` | `double` | — |
        | `bool` | `boolean` | — |
        | `datetime64` | `date` | — |
        | String, low cardinality (<50% unique) | `keyword` | Best for STATS BY, filters |
        | String, high cardinality (≥50% unique) | `text` | Gets `.keyword` sub-field |
        | String, avg length > 50 chars | `semantic_text` | Auto-detected, ELSER applied |

        Text fields used in STATS BY aggregations get a dual mapping with a `.keyword`
        sub-field to support both full-text search and exact-match grouping.
        """)

    st.markdown("### Bulk Indexing")

    with st.expander("**ELSER batch size limits**"):
        st.markdown("""
        When semantic_text fields are present, the ELSER inference endpoint processes
        each document during indexing. To avoid overloading the model:

        | Semantic Fields? | Batch Size | Reason |
        |---|---|---|
        | No | 1,000 docs/batch | Standard bulk performance |
        | Yes | 16 docs/batch | ELSER inference throughput limit |

        The indexer also handles document preparation: converting NumPy int64/float64 to
        native Python types, dropping NaN values, mapping `timestamp` → `@timestamp` for
        data streams, and expanding array fields.
        """)

    with st.expander("**ELSER readiness check**"):
        st.markdown("""
        Before indexing with semantic_text fields, Vulcan verifies the ELSER model is
        deployed and ready:

        1. Check inference endpoint (`.elser-2-elasticsearch`)
        2. Check model deployment state (`started` / `starting` / `downloading`)
        3. If not ready → clear error with instructions to deploy via Kibana ML

        This prevents cryptic indexing failures when the inference endpoint isn't available.
        """)

    st.markdown("### Data Profiling")

    st.markdown("""
    After indexing, Vulcan profiles each index using ES|QL queries. The profile is fed
    directly into the query generation prompt so field names, filter values, and JOIN keys
    are always grounded in real data.
    """)

    with st.expander("**Profiling techniques**", expanded=True):
        st.markdown("""
        | What | ES|QL Query Pattern | Output |
        |---|---|---|
        | Unique values | `STATS unique_values = VALUES(field)` | Full list (up to 100), truncated flag |
        | Numeric stats | `STATS MIN, MAX, AVG, PERCENTILE(field, 50/75/90/95/99)` | Distribution shape |
        | Date ranges | `STATS MIN(@timestamp), MAX(@timestamp)` | Time span of data |
        | Multi-field combos | `STATS COUNT(*) BY field1, field2 \\| SORT COUNT DESC` | Real filter combinations that return results |
        | Relationships | Field value overlap analysis (>10% threshold) | JOIN key candidates between indices |

        **Relationship detection** is especially important for LOOKUP JOIN queries.
        The profiler compares unique values across datasets, checks name patterns
        (e.g., `product_id` vs `product_refs`), detects cardinality (one-to-one vs
        many-to-one), and identifies sample join values that produce actual results.
        """)


def render_queries_tab():
    """Render the Queries tab."""
    st.markdown("## Queries")

    st.markdown("""
    The Queries tab organizes generated queries into three subtabs — **Scripted**,
    **Parameterized**, and **Completion** — each with tools for testing and validation.
    """)

    st.markdown("### Working with Queries")

    st.markdown("""
    For each query you can:
    - **View** the ES|QL with syntax highlighting
    - **Edit** the query text directly in the code editor
    - **Fill parameters** — the "Fill with Sample Values" button auto-populates from data profiling
    - **Use suggested values** — each parameter shows realistic examples from indexed data
    - **Run** against Elasticsearch and see results with row count and execution time
    - **Validate** — marks the query as ready for tool deployment
    """)

    st.markdown("### Suggested Values")

    with st.expander("**How parameter suggestions work**", expanded=True):
        st.markdown("""
        Every parameterized query includes `suggested_values` — realistic sample values that
        help users test queries quickly and understand what each parameter expects.

        **Generation**: The LLM is instructed to include 2-3 realistic values per parameter:
        ```json
        "parameters": {
            "subscriber_id": {
                "type": "string",
                "description": "IMSI, location area code, or subscriber ID",
                "suggested_values": ["LAC-1001", "IMSI-310260", "SUB-7742"]
            }
        }
        ```

        **Enrichment from data profile**: At display time, the system also extracts live values
        from indexed data using 4 matching strategies:
        1. **Exact match** — parameter name matches a field name directly
        2. **Pattern match** — `brand_filter` maps to fields like `brand`, `brand_name`
        3. **Substring match** — partial name overlap
        4. **Text extraction** — for search parameters, pulls sample text content

        **UI display**: Suggested values appear as placeholder text in parameter inputs
        and as a hint bar below the query: `💡 Try: **region**: us-east, us-west | **threshold**: 50, 100`

        The "Fill with Sample Values" button uses the first suggested value for each parameter,
        allowing one-click query testing.
        """)

    st.markdown("### Constraint Relaxation")

    st.markdown("""
    If a query returns zero results, the system can automatically relax constraints:
    expanding time ranges, lowering numeric thresholds, or removing restrictive filters.
    This is applied iteratively during generation and is also available manually in the UI.
    """)


def render_tools_tab():
    """Render the Tools tab."""
    st.markdown("## Tools")

    st.markdown("""
    A **tool** is a validated ES|QL query packaged for Elastic Agent Builder.
    When an agent receives a user question, it selects and invokes the appropriate tool
    to retrieve data from Elasticsearch.
    """)

    st.markdown("### Tool Metadata")

    st.markdown("""
    Each tool includes auto-generated metadata that controls how Agent Builder uses it:
    """)

    with st.expander("**Tool metadata structure**", expanded=True):
        st.code("""
{
  "tool_id": "telco_network_ops_spike_detection",
  "description": "Detects authentication failure spike events using
    INLINESTATS z-score analysis. Use when investigating sudden
    increases in failures or potential security incidents.",
  "tags": ["network", "security", "anomaly-detection"],
  "query": "FROM events-data* | WHERE ...",
  "params": {
    "region": {
      "type": "string",
      "description": "Geographic region to analyze",
      "suggested_values": ["us-east", "us-west", "eu-central"]
    }
  }
}
        """, language="json")

        st.markdown("""
        **Naming convention**: `{company}_{department}_{purpose}` — only lowercase letters,
        numbers, dots, and underscores (no hyphens). This ensures uniqueness and enables
        filtering tools by module prefix.

        **Description best practices**: The first ~50 characters appear in the tool list.
        Start with an action verb ("Analyzes...", "Detects...", "Compares...") and explain
        when an agent should choose this tool over others.

        **Parameter types**: Converted to Agent Builder API format automatically
        (`keyword` → `string`, `long` → `integer`, `double` → `float`).
        """)

    st.markdown("### Deployment Workflow")

    st.markdown("""
    1. **Validate query** in the Queries tab (must return results)
    2. **Review tool metadata** — auto-generated from the query and context
    3. **Deploy** — pushes the tool to Agent Builder via Kibana API (`POST /api/agent_builder/tools`)
    4. **Assign to agent** — link the tool to one or more agents
    """)

    st.markdown("### Module-Specific vs Platform Tools")

    st.markdown("""
    | Type | Prefix | Source | Examples |
    |------|--------|--------|----------|
    | Module-specific | `{company}_{dept}_*` | Generated for this demo | `telco_network_ops_spike_detection` |
    | Platform | `platform.*` | Shared across all agents | `platform.core.search`, `platform.core.generate_esql` |

    Both types can be assigned to any agent. Module-specific tools provide domain expertise;
    platform tools provide general-purpose capabilities like ad-hoc ES|QL execution.
    """)


def render_agents_tab():
    """Render the Agents tab."""
    st.markdown("## Agents")

    st.markdown("""
    An **agent** is an AI assistant in Elastic Agent Builder that uses tools to answer
    user questions. Vulcan generates a complete agent configuration for each demo.
    """)

    st.markdown("### Agent Components")

    st.markdown("""
    | Component | Description |
    |-----------|-------------|
    | **Identity** | ID (`{company}_{dept}_agent`), display name, description |
    | **Avatar** | Symbol (1-2 letters, e.g., "TM") + color (blue for analytics, green for search) |
    | **Instructions** | System prompt: expertise areas, pain points addressed, communication style, available data |
    | **Tools** | List of tool IDs the agent can invoke during conversations |
    | **Labels** | Tags for filtering (e.g., `telco`, `network_operations`, `analytics`) |
    """)

    st.markdown("### Instruction Generation")

    with st.expander("**What goes into agent instructions**"):
        st.markdown("""
        The LLM generates instructions from the customer context, query descriptions,
        and dataset metadata. A well-generated instruction includes:

        1. **Expertise summary** — what the agent specializes in
        2. **Specific capabilities** — tied to actual tool descriptions
        3. **Pain points** — from the original customer context
        4. **Available data** — what metrics and fields the tools expose
        5. **Communication style** — urgent for NOC, consultative for analytics, etc.
        6. **Conversation starters** — example questions users can ask

        Instructions reference the actual tools the agent has access to, so the LLM
        knows when to invoke each one.
        """)

    st.markdown("### Example Configuration")

    st.code("""
{
  "id": "telco_network_operations_agent",
  "name": "Telco Network Ops Assistant",
  "description": "Detects network anomalies and troubleshoots failures",
  "labels": ["telco", "network_operations", "analytics"],
  "avatar_symbol": "TM",
  "avatar_color": "#3B82F6",
  "configuration": {
    "instructions": "You are an AI assistant specialized in ...",
    "tools": [
      {
        "tool_ids": [
          "telco_network_ops_spike_detection",
          "telco_network_ops_handoff_analysis",
          "platform.core.search"
        ]
      }
    ]
  }
}
    """, language="json")

    st.markdown("### Deployment")

    st.markdown("""
    1. **Review** the auto-generated agent config (name, instructions, avatar)
    2. **Deploy** to Agent Builder via Kibana API (`POST /api/agent_builder/agents`)
    3. **Assign tools** — select which deployed tools the agent can invoke
    4. **Test** in Agent Builder — ask questions and watch the agent select tools
    """)


def render_guide_tab():
    """Render the Guide tab."""
    st.markdown("## Demo Guide")

    st.markdown("""
    The demo guide is an auto-generated presenter aid that helps you deliver the demo
    with confidence. It's tailored to the specific customer context and generated queries.
    """)

    st.markdown("### What It Contains")

    st.markdown("""
    | Section | Purpose | Timing |
    |---------|---------|--------|
    | **Demo Overview** | Audience, goal, total time estimate | — |
    | **AI Agent Chat Teaser** | Open with a live agent conversation to hook the audience | 5 min |
    | **ES|QL Query Building** | Walk through queries from simple to sophisticated | 10 min |
    | **Agent & Tool Creation** | Show how queries become tools and agents | 5 min |
    | **AI Agent Q&A Session** | Free-form conversation with the deployed agent | 5-10 min |

    The guide includes **suggested questions** for each tool, **transition phrases** between
    sections, and **key insights** to call out ("Notice how INLINESTATS computes the baseline
    inline — no pre-aggregated table needed").
    """)

    st.markdown("### How It's Generated")

    st.markdown("""
    The guide is the final pipeline stage. It receives the full context — customer details,
    generated datasets, validated queries, tool definitions, and agent metadata — and produces
    a cohesive narrative. The output is saved as `demo_guide.md` in the module directory
    and displayed in the Guide tab.
    """)

    st.markdown("### Claude Code Skills")

    st.markdown("""
    Beyond the generated guide, Vulcan includes **Claude Code skills** — specialized
    slash commands that extend the demo workflow:
    """)

    with st.expander("**Available skills**", expanded=True):
        st.markdown("""
        | Skill | Command | What It Does |
        |-------|---------|-------------|
        | **Agent Builder** | `/agent-builder-new` | Design complete Agent Builder demos: queries, data, tools, agents |
        | **ES|QL Validator** | `/esql-validator-new` | Validate and auto-fix ES|QL queries via MCP tools |
        | **ES|QL Search Patterns** | `/esql-search-patterns-new` | Generate MATCH, QSTR, semantic search, and hybrid queries |
        | **ES|QL Advanced Commands** | `/esql-advanced-commands-new` | Generate LOOKUP JOIN, INLINESTATS, FORK/FUSE, CHANGE_POINT queries |
        | **Content Manager** | `/elastic-content-manager` | Deploy and manage agents/tools via Kibana API |
        | **Google Slides** | `/google-slides-generator` | Create presentation decks from demo artifacts |
        | **Google Docs** | `/google-docs-generator` | Generate demo scripts with talk tracks and timing |

        **How they work**: Each skill is a self-contained prompt in `.claude/skills/` that gives
        Claude Code domain expertise for a specific task. Skills can be chained — for example,
        generate a demo with `/agent-builder-new`, validate queries with `/esql-validator-new`,
        then create a slide deck with `/google-slides-generator`.

        **ES|QL auto-fix patterns** (from the validator skill):
        - Integer division → adds `TO_DOUBLE()`
        - JOIN after STATS → reorders pipeline
        - `DATE_EXTRACT` → converts to `DATE_TRUNC`
        - `ENRICH` → converts to `LOOKUP JOIN`
        - Non-existent functions → removes or replaces
        """)
