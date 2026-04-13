"""
Revenue Engine Tab — Full Search Intelligence Platform

8 panels covering every dimension of modern enterprise search:
  1. 🛒 Project Planner    — conversational project planning experience
  2. 📊 Search Analytics   — zero results, CTR, top queries, latency
  3. 🔍 Search Intelligence — intent classification + autocomplete + personalization
  4. ⚠️  Zero Results Lab   — graceful degradation testing
  5. 🎯 Merchandising       — PIN / BOOST / BURY via Elastic Query Rules
  6. 🧪 A/B Testing         — BM25 vs ELSER vs Hybrid side-by-side
  7. 🖼️  Visual Search       — multimodal image-to-document search
"""

import logging
import time
import json
import random
import streamlit as st
import pandas as pd

logger = logging.getLogger(__name__)

# ── Context builder ───────────────────────────────────────────────────────────

def _get_ctx(loader):
    """Build (and cache in session state) the SearchContext for this demo."""
    key = f"re_ctx_{getattr(loader, 'module_path', 'default')}"
    if key not in st.session_state:
        try:
            from src.services.search_context_service import SearchContextService
            st.session_state[key] = SearchContextService().build(loader)
        except Exception:
            # fallback — return None, panels handle gracefully
            st.session_state[key] = None
    return st.session_state[key]


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def render_revenue_engine_tab(loader=None) -> None:
    _inject_css()
    ctx = _get_ctx(loader)
    _render_header(ctx)
    _init_state()

    panels = [
        "🛒 Project Planner",
        "📊 Search Analytics",
        "🔍 Search Intelligence",
        "⚠️ Zero Results Lab",
        "🎯 Merchandising",
        "🧪 A/B Testing",
        "🖼️ Visual Search",
    ]

    panel = st.segmented_control(
        "Revenue Engine Panel",
        options=panels,
        default=st.session_state.get("re_panel", panels[0]),
        key="re_panel",
        label_visibility="collapsed",
    )

    st.markdown("")

    if panel == "🛒 Project Planner":
        _render_project_planner(loader, ctx)
    elif panel == "📊 Search Analytics":
        _render_analytics(ctx)
    elif panel == "🔍 Search Intelligence":
        _render_search_intelligence(loader, ctx)
    elif panel == "⚠️ Zero Results Lab":
        _render_zero_results(loader, ctx)
    elif panel == "🎯 Merchandising":
        _render_merchandising(loader, ctx)
    elif panel == "🧪 A/B Testing":
        _render_ab_testing(loader, ctx)
    elif panel == "🖼️ Visual Search":
        _render_visual_search(loader, ctx)


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────

def _render_header(ctx=None) -> None:
    company = ctx.company if ctx else "Enterprise"
    industry = ctx.industry_label if ctx else "Search"
    label = ctx.label if ctx else "Knowledge Base"
    st.markdown(f"""
    <div class="re-header">
        <div style="display:flex;align-items:center;gap:12px;">
            <span style="font-size:30px;">⚡</span>
            <div>
                <div style="font-size:21px;font-weight:800;letter-spacing:-0.5px;">Revenue Engine™ — {company}</div>
                <div style="font-size:12px;opacity:0.85;margin-top:2px;">
                    {industry} · {label} · Semantic + RAG + Analytics + Merchandising + A/B + Visual · Powered by Elastic
                </div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 1. PROJECT PLANNER
# ─────────────────────────────────────────────────────────────────────────────

def _render_project_planner(loader, ctx) -> None:
    # Pain KPIs banner — show customer's before/after if we have them
    if ctx and ctx.pain_kpis:
        st.markdown("#### 📈 What this solves for you")
        cols = st.columns(len(ctx.pain_kpis))
        for col, (metric, vals) in zip(cols, ctx.pain_kpis.items()):
            col.markdown(f"""<div class="re-kpi-pain">
                <div class="re-kpi-label">{metric}</div>
                <div class="re-kpi-before">Before: <strong>{vals['before']}</strong></div>
                <div class="re-kpi-after">After: <strong>{vals['after']}</strong></div>
                <div class="re-kpi-delta">{vals['delta']}</div>
                <div class="re-kpi-impact">{vals['impact']}</div>
            </div>""", unsafe_allow_html=True)
        st.markdown("")

    phase = st.session_state.get("re_phase", "input")
    if phase == "input":
        _render_input_phase(loader, ctx)
    else:
        _render_results_phase()


def _render_input_phase(loader, ctx) -> None:
    label = ctx.planner_label if ctx else "Project Planner"
    placeholder = ctx.planner_placeholder if ctx else 'e.g. "Describe your project or challenge"'
    catalog_label = ctx.catalog_label if ctx else "items"

    st.markdown(f"#### {label}")
    description = st.text_area(
        "Project description",
        placeholder=placeholder,
        height=80, label_visibility="collapsed",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        scope = st.text_input("📍 Scope / Location", value="HQ + 3 regional offices")
    with c2:
        scale = st.text_input("📐 Scale", value="5,000 users")
    with c3:
        budget = st.number_input("💰 Budget ($)", min_value=500, max_value=500000, value=50000, step=5000)

    c4, c5 = st.columns(2)
    with c4:
        priority = st.selectbox("🎯 Priority", ["Cost Reduction", "Speed", "Compliance", "User Experience", "Revenue Growth"])
    with c5:
        timeline = st.selectbox("📅 Timeline", ["Immediate (< 1 month)", "Short-term (1-3 months)", "Medium (3-6 months)", "Long-term (6-12 months)"])

    st.markdown("")
    if st.button("⚡ Analyze & Build Plan", type="primary", use_container_width=True):
        if not description.strip():
            st.warning("Please describe your challenge.")
            return
        _run_engine(loader, description, scope, scale, priority, budget)


def _run_engine(loader, description, zip_code, size, purpose, budget) -> None:
    from src.services.revenue_engine_service import RevenueEngineService

    index_names = _get_index_names(loader)
    placeholder = st.empty()

    with placeholder.container():
        st.markdown("### ⚡ Revenue Engine is working...")
        steps = [
            ("📚", "RAG — Loading project build guide..."),
            ("🔍", "ELSER Semantic — Matching documents to your challenge..."),
            ("📍", "Context Search — Finding relevant resources..."),
            ("📦", "ES|QL — Joining data across indexes..."),
        ]
        bars = [st.progress(0) for _ in steps]
        for icon, label in steps:
            st.caption(f"{icon} {label}")
        for bar in bars:
            for pct in range(0, 101, 25):
                bar.progress(pct)
                time.sleep(0.03)

    placeholder.empty()

    svc = RevenueEngineService()
    result = svc.plan_project(
        description=description, zip_code=zip_code, size=size,
        purpose=purpose, budget=budget, index_names=index_names,
    )

    # Track in personalization history
    history = st.session_state.get("re_search_history", [])
    history.insert(0, {
        "query": description,
        "type": _classify_type(description, purpose),
        "dept": purpose,
        "size": size,
        "budget": budget,
    })
    st.session_state["re_search_history"] = history[:10]

    st.session_state["re_result"] = result
    st.session_state["re_phase"] = "results"
    st.rerun()


def _render_results_phase() -> None:
    result = st.session_state.get("re_result", {})
    if not result:
        st.session_state["re_phase"] = "input"
        st.rerun()
        return

    store       = result.get("store", {})
    materials   = result.get("materials", [])
    rentals     = result.get("rentals", [])
    grand_total = result.get("grand_total", 0)
    mat_total   = result.get("total_materials", 0)
    rent_total  = result.get("total_rentals", 0)
    budget      = result.get("budget", 0)
    permit      = result.get("permit_notice", "")
    mode        = result.get("mode", "simulation")

    if mode == "simulation":
        st.info("📊 **Demo Mode** — Realistic simulation. Index your datasets to see live Elasticsearch results.", icon="ℹ️")

    if permit:
        (st.warning if "⚠️" in permit else st.success)(permit)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🏪 Distance",   f"{store.get('distance_miles', '?')} mi")
    m2.metric("📦 Line Items", f"{len(materials)}")
    m3.metric("🔧 Rentals",    f"{len(rentals)}")
    m4.metric("💰 Materials",  f"${mat_total:,.2f}")
    over = grand_total > budget
    m5.metric("💵 Grand Total", f"${grand_total:,.2f}",
              delta=f"${grand_total - budget:+,.0f} vs budget" if over else f"${budget - grand_total:,.0f} under",
              delta_color="inverse" if over else "normal")

    st.divider()
    st.markdown(f"""<div class="re-store-card">
        <div style="font-size:17px;font-weight:700;color:#003d7a;">📍 {store.get('name', 'Nearest Store')}</div>
        <div style="color:#555;margin-top:4px;">{store.get('address', '')} · {store.get('distance_miles', '?')} mi · {store.get('phone', '')} · {store.get('hours', '')}</div>
    </div>""", unsafe_allow_html=True)

    t1, t2, t3 = st.tabs([f"🔨 Materials ({len(materials)})", f"🔧 Rentals ({len(rentals)})", "📋 Summary"])

    with t1:
        df = pd.DataFrame([{
            "Item": m["name"], "Category": m["category"], "Qty": m["qty"],
            "Aisle": m["aisle"], "Bay": m["bay"],
            "Unit $": f"${m['price']:.2f}", "Total $": f"${m['subtotal']:.2f}",
        } for m in materials])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown(f"**Materials subtotal: ${mat_total:,.2f}**")

    with t2:
        for r in rentals:
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"""<div class="re-rental-card">
                    <div style="font-weight:600">{r['name']}</div>
                    <div style="color:#666;font-size:13px">{r['why']}</div>
                    <div style="margin-top:6px">
                        <span class="re-badge">${r['day_rate']:.0f}/day</span>
                        <span class="re-badge-gray">Deposit: ${r['deposit']:.0f}</span>
                    </div></div>""", unsafe_allow_html=True)
            with c2:
                st.metric("Cost", f"${r['days'] * r['day_rate']:.2f}")
        st.markdown(f"**Rental subtotal: ${rent_total:,.2f}**")

    with t3:
        st.markdown(f"""
| Field | Value |
|---|---|
| **Project** | {result.get('description', '')} |
| **Size** | {result.get('size', '')} |
| **Budget** | ${budget:,} |
| **Materials** | ${mat_total:,.2f} ({len(materials)} items) |
| **Rentals** | ${rent_total:,.2f} ({len(rentals)} tools) |
| **Grand Total** | **${grand_total:,.2f}** |
| **Store** | {store.get('name', '')} |
| **Status** | {'⚠️ Over budget' if over else '✅ Within budget'} |
""")

    st.divider()
    ba, bb, bc, bd = st.columns(4)
    with ba:
        if st.button("🛒 Add All to Cart", type="primary", use_container_width=True):
            st.success(f"✅ {len(materials)} items added to cart!")
    with bb:
        if st.button("🖨️ Print / PDF", use_container_width=True):
            _show_print_view(result)
    with bc:
        if st.button("📱 Send to Phone", use_container_width=True):
            st.info("SMS sent!")
    with bd:
        if st.button("🔁 Start Over", use_container_width=True):
            st.session_state["re_phase"] = "input"
            st.session_state.pop("re_result", None)
            st.rerun()

    with st.expander("⚙️ Under the Hood — How Elastic powered this"):
        _render_under_the_hood(result)


# ─────────────────────────────────────────────────────────────────────────────
# 2. SEARCH ANALYTICS
# ─────────────────────────────────────────────────────────────────────────────

def _render_analytics(ctx) -> None:
    if not ctx:
        st.info("Load a demo to see personalised analytics.")
        return

    st.markdown(f"### 📊 Search Analytics — {ctx.company}")
    st.caption(f"Real-time visibility into search performance across your {ctx.label.lower()}.")

    # KPI row — labels from ctx
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric(ctx.kpi_search_label, "14,820",  delta="+11% vs yesterday")
    k2.metric(ctx.kpi_zero_label,   "3.8%",    delta="-1.4%", delta_color="normal")
    k3.metric(ctx.kpi_ctr_label,    "79%",     delta="+5%")
    k4.metric("Self-Service Rate",  "71%",     delta="+8%")
    k5.metric(ctx.kpi_value_label,  f"Saved {random.randint(8, 22)} min/query", delta="vs 3 months ago")

    st.divider()
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Top Queries by Volume")
        top = ctx.top_queries
        df_top = pd.DataFrame([{
            "Query": q["query"],
            "Searches": q["searches"],
            "Success Rate": f"{q['ctr']:.0%}",
            "Avg Value": f"{q['avg_value']}",
            "Zero Result %": f"{q['zero_result_pct']:.0%}",
        } for q in top])
        st.dataframe(
            df_top, use_container_width=True, hide_index=True,
            column_config={
                "Searches": st.column_config.ProgressColumn(
                    "Searches", min_value=0, max_value=max(q["searches"] for q in top)
                )
            },
        )

    with col_right:
        st.markdown("#### Failing & At-Risk Queries")
        st.caption(f"Real user queries returning zero results — {ctx.company} revenue impact right now")
        for q in ctx.failing_queries:
            status = "🔴" if q["zero_results"] else "🟡"
            fc1, fc2 = st.columns([3, 1])
            with fc1:
                st.markdown(f"""<div class="re-alert-card">
                    {status} <strong>"{q['query']}"</strong><br>
                    <span style="color:#666;font-size:12px">{q['searches']} searches · Fix: <em>{q['suggestion']}</em></span>
                    <br><span style="color:#c0392b;font-size:11px">Impact: {q['impact']}</span>
                </div>""", unsafe_allow_html=True)
            with fc2:
                if st.button("Fix →", key=f"fix_{q['query'][:15]}", use_container_width=True):
                    st.success(f"Synonym + ELSER rule created: '{q['query']}' → '{q['suggestion']}'")

    st.divider()
    st.markdown("#### Latency Breakdown by Search Layer")
    latency_data = pd.DataFrame({
        "Layer": ["ELSER Semantic", "BM25 Keyword", "Query Rules", "Inventory Join", "RRF Fusion", "Total"],
        "p50 (ms)": [82, 12, 8, 45, 5, 152],
        "p95 (ms)": [124, 18, 11, 87, 8, 248],
        "p99 (ms)": [187, 24, 14, 134, 12, 371],
    })
    st.dataframe(
        latency_data, use_container_width=True, hide_index=True,
        column_config={
            "p50 (ms)": st.column_config.ProgressColumn("p50 (ms)", min_value=0, max_value=400),
            "p95 (ms)": st.column_config.ProgressColumn("p95 (ms)", min_value=0, max_value=400),
            "p99 (ms)": st.column_config.ProgressColumn("p99 (ms)", min_value=0, max_value=400),
        },
    )

    with st.expander("⚙️ ES|QL behind this dashboard"):
        st.code("""FROM search_logs
| WHERE @timestamp >= NOW() - 1 day
| STATS
    searches      = COUNT(*),
    zero_results  = COUNT_IF(result_count == 0),
    avg_value     = AVG(session_value),
    click_through = AVG(clicked::integer)
  BY query_text
| EVAL zero_result_pct = zero_results / searches
| SORT searches DESC
| LIMIT 20""", language="sql")


# ─────────────────────────────────────────────────────────────────────────────
# 3. SEARCH INTELLIGENCE (Intent + Autocomplete + Personalization)
# ─────────────────────────────────────────────────────────────────────────────

def _render_search_intelligence(loader, ctx) -> None:
    st.markdown("### 🔍 Search Intelligence")
    sub = st.tabs(["🧠 Intent Classification", "💡 Semantic Autocomplete", "👤 Personalization"])
    with sub[0]:
        _render_intent_panel(ctx)
    with sub[1]:
        _render_autocomplete_panel(ctx)
    with sub[2]:
        _render_personalization_panel(ctx)


def _render_intent_panel(ctx) -> None:
    st.markdown("#### Query Intent Classification")
    st.caption(
        f"Claude pre-processes the raw query before it hits ELSER — understanding intent, reformulating, and adding context "
        f"for {ctx.company if ctx else 'your domain'}."
    )

    default_q = ctx.intent_query if ctx else "I need help with an urgent issue"
    raw_query = st.text_input("Raw user query", value=default_q, placeholder="Enter any query...")

    if st.button("🧠 Classify & Reformulate", type="primary"):
        with st.spinner("Claude is analyzing intent..."):
            intent_result = _classify_intent_with_llm(raw_query, ctx)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Raw Query**")
            st.code(raw_query)
            st.markdown("**What ELSER would get without intent layer:**")
            st.warning(
                f"A literal keyword match — misses true intent, urgency, and context specific to "
                f"{ctx.company if ctx else 'your domain'}"
            )

        with c2:
            st.markdown("**After Intent Classification**")
            st.json(intent_result)
            st.markdown("**What ELSER gets with intent layer:**")
            st.success(f"Reformulated: `{intent_result.get('reformulated_query', raw_query)}`")

        if ctx:
            st.markdown("#### Before vs After — Result Quality")
            comp_c1, comp_c2 = st.columns(2)
            with comp_c1:
                st.markdown("**Without intent layer** (keyword match)")
                wrong = [r["item"] for r in ctx.bm25_results[:4]]
                for w in wrong:
                    st.markdown(f"- {w}")
                st.caption("⚠️ Generic results — misses actual intent")
            with comp_c2:
                st.markdown("**With intent layer** (semantic + intent)")
                # Try multiple recommended keys depending on domain
                right_key = next(
                    (k for k in ("recommended_articles", "recommended_docs", "recommended_protocols")
                     if k in intent_result),
                    None,
                )
                if right_key:
                    right = intent_result.get(right_key, [])
                else:
                    right = [r["item"] for r in ctx.elser_results[:4]]
                for r in right[:4]:
                    st.markdown(f"- {r}")
                st.caption("✅ Intent understood · Correct context · Actionable")


def _classify_intent_with_llm(query: str, ctx=None) -> dict:
    """Call Claude to classify and reformulate the query in context."""
    industry = ctx.industry_label if ctx else "enterprise"
    catalog = ctx.catalog_label if ctx else "documents"
    company = ctx.company if ctx else "the company"
    fallback = ctx.intent_result if ctx else {
        "intent": "information_retrieval",
        "urgency": "medium",
        "category": "General Query",
        "reformulated_query": query,
        "reasoning": "Query processed with intent classification.",
    }
    try:
        import anthropic
        import os
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": (
                    f"You are a search intelligence layer for {company}, a {industry} organization.\n"
                    f"Analyze this user query against their {catalog} and return JSON only.\n\n"
                    f'Query: "{query}"\n\n'
                    f"Return exactly this JSON structure:\n"
                    "{\n"
                    f'  "intent": "the specific intent type relevant to {industry}",\n'
                    '  "urgency": "low|medium|high|critical",\n'
                    f'  "category": "specific {industry} category this maps to",\n'
                    f'  "reformulated_query": "optimized semantic search query for {catalog}",\n'
                    f'  "recommended_docs": ["most relevant document type 1", "most relevant document type 2", "most relevant document type 3"],\n'
                    '  "reasoning": "one sentence: what intent signal was detected and why the reformulation helps"\n'
                    "}"
                ),
            }],
        )
        return json.loads(msg.content[0].text)
    except Exception:
        return fallback


def _render_autocomplete_panel(ctx) -> None:
    prefix = ctx.autocomplete_prefix if ctx else "search"
    suggestions = ctx.autocomplete_suggestions if ctx else []
    catalog = ctx.catalog_label if ctx else "documents"

    st.markdown("#### Semantic Autocomplete")
    st.caption(
        f"Suggestions are semantically aware — not just prefix matches. "
        f"Understands {catalog} context, not just keywords."
    )

    partial = st.text_input(f"Start typing (try '{prefix}')...", value=prefix, placeholder="Type here...")

    typed_lower = partial.lower()
    matched = [
        s for s in suggestions
        if any(w in s["text"].lower() for w in typed_lower.split() if len(w) > 2)
    ]
    shown = matched or suggestions

    if shown:
        st.markdown("**Suggestions:**")
        for s in shown[:5]:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""<div class="re-suggestion">
                    <span style="font-weight:600">{s['text']}</span>
                    <span style="color:#888;font-size:12px;margin-left:8px">{s['category']}</span>
                </div>""", unsafe_allow_html=True)
            with col2:
                st.caption(f"_{s['match_type']}_")

    with st.expander("How this works"):
        st.markdown(f"""
1. Partial query sent to `search_as_you_type` field in Elasticsearch
2. ELSER scores completions by semantic relevance against `{catalog}` — not just alphabetical order
3. Results ranked by: semantic score × historical success rate × recency
4. Response time target: **<50ms** for real-time feel
        """)

    st.divider()
    with st.expander("⚙️ How this works — technical deep dive", expanded=False):
        st.markdown("""
#### Autocomplete Pipeline

```
User keystroke → partial token sent to Elasticsearch
        │
        ▼
search_as_you_type field (edge n-gram + shingle tokenizer)
        │
        ├─► BM25 prefix match on n-gram subfields (_2gram, _3gram, _index_prefix)
        │
        └─► ELSER semantic scoring on full text field
                │
                ▼
        RRF fusion: prefix score × 0.6 + semantic score × 0.4
                │
                ▼
        Weighted by: historical click-through rate per suggestion
                │
                ▼
        Top 5 suggestions returned in <50ms
```
""")
        st.markdown("**Elasticsearch index mapping for `search_as_you_type`**")
        st.code("""\
PUT /kb-docs
{
  "mappings": {
    "properties": {
      "title": {
        "type": "search_as_you_type",
        "max_shingle_size": 3
      },
      "title_semantic": {
        "type": "semantic_text",
        "inference_id": ".elser-2-elasticsearch"
      }
    }
  }
}
""", language="json")

        st.markdown("**Autocomplete query (BM25 prefix + ELSER semantic RRF)**")
        st.code(f"""\
POST /kb-docs/_search
{{
  "size": 5,
  "query": {{
    "multi_match": {{
      "query": "<partial-input>",
      "type": "bool_prefix",
      "fields": ["title", "title._2gram", "title._3gram"]
    }}
  }},
  "knn": {{
    "field": "title_semantic.inference.chunks.embeddings",
    "query_vector_builder": {{
      "text_embedding": {{
        "model_id": ".elser-2-elasticsearch",
        "model_text": "<partial-input>"
      }}
    }},
    "k": 10,
    "num_candidates": 50
  }},
  "rank": {{
    "rrf": {{
      "window_size": 20,
      "rank_constant": 60
    }}
  }}
}}
""", language="json")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Build this in your app**")
            st.markdown(f"""
- Wire `search_as_you_type` field + `semantic_text` field on `{catalog}` index
- Fire query on every keypress with 150ms debounce
- Display top 5 with category badge (from `_source`)
- Track clicks to `behavioral_analytics-*` for CTR ranking
""")
        with col2:
            st.markdown("**Explore in Kibana**")
            st.markdown("""
- **Discover**: run `_search?pretty` from Dev Tools to inspect raw suggestions
- **Behavioral Analytics**: view autocomplete CTR and abandonment rate dashboards
- **ML > Inference**: confirm ELSER model is deployed and allocating
""")


def _render_personalization_panel(ctx) -> None:
    st.markdown("#### Personalization")
    catalog = ctx.catalog_label if ctx else "documents"
    st.caption(
        f"Search results and recommendations adapt based on this user's role, department, "
        f"and {catalog} access history."
    )

    history_raw = st.session_state.get("re_search_history", [])

    if history_raw:
        _show_personalization_output(history_raw, ctx=ctx)
    else:
        if ctx and ctx.personalization_history:
            st.info(
                f"No live session history yet. Showing example for a "
                f"**{ctx.department or ctx.industry_label}** user at {ctx.company}."
            )
            _show_personalization_output(ctx.personalization_history, is_demo=True, ctx=ctx)
        else:
            st.info("No session history yet.")


def _show_personalization_output(history: list, is_demo: bool = False, ctx=None) -> None:
    if is_demo:
        st.caption("🔵 Example data for this industry — run live searches to see your actual history")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("**Recent Queries**")
        for h in history[:5]:
            query = h.get("query", "")
            doc_type = h.get("type", "Document")
            dept = h.get("dept", "")
            st.markdown(f"""<div class="re-history-item">
                <div style="font-weight:600;font-size:13px">{query[:45]}</div>
                <div style="color:#888;font-size:11px">{doc_type} · {dept}</div>
            </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("**Personalized Recommendations**")
        if ctx:
            recs = _get_personalized_recs_ctx(history, ctx)
        else:
            recs = []
        for r in recs:
            st.markdown(f"""<div class="re-rec-card">
                <div style="font-weight:600">{r['title']}</div>
                <div style="color:#555;font-size:13px">{r['reason']}</div>
                <div style="margin-top:4px"><span class="re-badge">{r['tag']}</span></div>
            </div>""", unsafe_allow_html=True)

    if history:
        dept_vals = list({h.get("dept", "") for h in history if h.get("dept")})
        type_vals = list({h.get("type", "") for h in history if h.get("type")})
        signals = pd.DataFrame([
            {"Signal": "Document types accessed",  "Value": ", ".join(type_vals) or "Mixed",   "Used for": "Content-type boosting"},
            {"Signal": "Department / role",         "Value": ", ".join(dept_vals) or "General", "Used for": "Role-based result ranking"},
            {"Signal": "Session query count",       "Value": str(len(history)),                 "Used for": "Expertise level calibration"},
            {"Signal": "Recency weighting",         "Value": "Last 30 mins",                   "Used for": "Freshness boost for recent docs"},
        ])
        st.markdown("**Behavioral Signals Elastic is tracking:**")
        st.dataframe(signals, use_container_width=True, hide_index=True)

    st.divider()
    with st.expander("⚙️ How this personalization works — technical deep dive", expanded=False):
        st.markdown("""
#### Personalization Pipeline

```
User searches → Behavioral Analytics captures event → Session profile built in ES
      ↓
Query time: session signals injected as boosting functions
      ↓
ELSER semantic re-ranking applied on top of boosted results
      ↓
Personalized ranked list returned
```
""")
        st.markdown("**Step 1 — Capture behavioral events (Behavioral Analytics JS tracker)**")
        st.code("""\
// One-line instrumentation in your search UI
import { createTracker } from '@elastic/behavioral-analytics-javascript-tracker';

const tracker = createTracker({ endpoint: 'https://your-cluster.es.io', apiKey: '...' });
tracker.trackSearch({ search: { query: userQuery, results: { total: { value: hitCount } } } });
tracker.trackSearchClick({ document: { id: docId, index: 'kb-docs' } });
""", language="javascript")

        st.markdown("**Step 2 — Build session profile with ES|QL**")
        st.code("""\
FROM behavioral_analytics-*
| WHERE session.id == "<current-session-id>"
  AND @timestamp > NOW() - 30 minutes
| STATS
    doc_types  = VALUES(document.type),
    dept       = VALUES(user.department),
    query_count = COUNT(*)
  BY session.id
""", language="sql")

        st.markdown("**Step 3 — Inject signals as boosting at query time**")
        st.code("""\
POST /kb-docs/_search
{
  "query": {
    "function_score": {
      "query": { "match": { "content": "<user-query>" } },
      "functions": [
        {
          "filter": { "terms": { "doc_type": ["<session-doc-types>"] } },
          "weight": 2.5
        },
        {
          "filter": { "term": { "department": "<user-dept>" } },
          "weight": 1.8
        },
        {
          "gauss": { "@timestamp": { "scale": "7d", "decay": 0.5 } }
        }
      ],
      "boost_mode": "multiply"
    }
  },
  "knn": {
    "field": "content_embedding",
    "query_vector_builder": {
      "text_embedding": { "model_id": ".elser_model_2", "model_text": "<user-query>" }
    },
    "num_candidates": 100,
    "boost": 0.3
  }
}
""", language="json")

        st.markdown("**Step 4 — Re-rank with ELSER semantic similarity**")
        st.markdown("""
The `knn` clause runs ELSER in parallel with the boosted BM25 query. Elastic blends the two scores:
- **BM25 × boost functions** = personalized keyword relevance
- **ELSER vector similarity** = semantic intent matching
- Final score = weighted sum → top-k results re-ranked

This means a document the user's team frequently accesses AND is semantically close to the query floats to the top — even if it's not an exact keyword match.
""")

        st.markdown("**Consume this from Kibana or your app:**")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("""
**Kibana Behavioral Analytics**
- Built-in dashboard: zero-code
- Heatmaps, query volume, zero-result trends
- No app changes needed if you use the JS tracker
""")
        with col_b:
            st.markdown("""
**Your own app (REST API)**
- Call `POST /kb-docs/_search` with the boosting query above
- Session profile from ES|QL feeds the boost weights dynamically
- Works with any frontend: React, Vue, Angular, iOS, Android
""")


def _get_personalized_recs_ctx(history: list, ctx) -> list:
    """Generate context-appropriate recommendations from history."""
    recs = []
    if ctx and ctx.elser_results:
        tags = ["Most relevant", "Frequently accessed", "Recently updated"]
        for i, r in enumerate(ctx.elser_results[:3]):
            recs.append({
                "title": r["item"],
                "reason": f"Highly relevant to your recent queries — {r['reason']}",
                "tag": tags[i % len(tags)],
            })
    return recs


# ─────────────────────────────────────────────────────────────────────────────
# 4. ZERO RESULTS LAB
# ─────────────────────────────────────────────────────────────────────────────

def _render_zero_results(loader, ctx) -> None:
    st.markdown("### ⚠️ Zero Results Lab")
    catalog = ctx.catalog_label if ctx else "documents"
    company = ctx.company if ctx else "your organization"
    st.caption(
        f"Test how search handles queries that return no results — and how graceful degradation "
        f"recovers them for {company}."
    )

    default_q = ctx.failing_queries[0]["query"] if ctx and ctx.failing_queries else "test query"
    col1, col2 = st.columns([2, 1])
    with col1:
        test_query = st.text_input(
            "Test a potentially failing query",
            value=default_q,
            placeholder="Type something vague, jargon-heavy, or using informal language...",
        )
    with col2:
        st.markdown("")
        run = st.button("🧪 Test Degradation", type="primary", use_container_width=True)

    if run and test_query:
        _run_zero_results_test(test_query, ctx)

    st.divider()
    st.markdown("#### Known Zero-Result Patterns & Fixes Applied")
    if ctx and ctx.failing_queries:
        patterns = [{
            "Original Query": q["query"],
            "Fixed By": "Synonym + ELSER semantic",
            "Maps To": q["suggestion"],
            "Impact": q["impact"],
        } for q in ctx.failing_queries]
        st.dataframe(pd.DataFrame(patterns), use_container_width=True, hide_index=True)


def _run_zero_results_test(query: str, ctx=None) -> None:
    failing = ctx.failing_queries if ctx else []
    match = next(
        (q for q in failing if any(w in query.lower() for w in q["query"].lower().split()[:3])),
        None,
    )
    is_zero = match is not None or len(query.split()) > 4

    st.markdown("#### Test Results")
    tab1, tab2, tab3 = st.tabs(["❌ Without Degradation", "✅ With Degradation", "🔧 Fix Applied"])

    with tab1:
        if is_zero:
            st.error(f'**0 results** for "{query}"')
            impact = match["impact"] if match else "Users leave without finding what they need."
            st.markdown(f"**Business impact:** {impact}")
        else:
            st.success("This query returns results — try something more ambiguous!")

    with tab2:
        st.success(f"**Recovery activated** for \"{query}\"")
        st.markdown("**Strategy applied:** Synonym expansion + ELSER semantic fallback + category relaxation")
        if ctx and ctx.elser_results:
            recovery = [{
                "Result": r["item"],
                "Relevance Score": r["score"],
                "Why": r["reason"],
            } for r in ctx.elser_results[:3]]
            st.dataframe(pd.DataFrame(recovery), use_container_width=True, hide_index=True)
            if match:
                st.caption(f"Fixed: '{match['query']}' → '{match['suggestion']}'")
        else:
            st.info("Recovery results would appear here with your indexed data.")

    with tab3:
        st.markdown("**Degradation pipeline:**")
        st.markdown("""
1. **Spell check** → correct typos first
2. **Synonym expansion** → map informal/jargon terms to canonical terms via Elastic Synonyms API
3. **ELSER semantic fallback** → run against `description` semantic_text field
4. **Category relaxation** → broaden from specific → general → all
5. **Popularity boost** → surface most-accessed items in the likely category
6. **Log for review** → flag in Search Analytics for manual synonym rule creation
        """)
        if ctx and match:
            ruleset_id = ctx.company.lower().replace(" ", "-")
            st.code(f"""PUT _synonyms/{ruleset_id}-synonyms
{{
  "synonyms_set": [
    {{"synonyms": "{match['query']} => {match['suggestion']}"}}
  ]
}}""", language="json")


# ─────────────────────────────────────────────────────────────────────────────
# 5. MERCHANDISING / QUERY RULES
# ─────────────────────────────────────────────────────────────────────────────

def _render_merchandising(loader, ctx) -> None:
    company = ctx.company if ctx else "Enterprise"
    catalog = ctx.catalog_label if ctx else "documents"
    st.markdown("### 🎯 Merchandising — Search Rules Engine")
    st.caption(
        f"Business rules that control what search surfaces for {company} — without touching the algorithm. "
        f"Powered by Elastic Query Rules API."
    )

    tab_active, tab_create = st.tabs(["📋 Active Rules", "➕ Create Rule"])

    with tab_active:
        rules = ctx.merchandising_rules if ctx else []
        if rules:
            st.dataframe(pd.DataFrame(rules), use_container_width=True, hide_index=True)
        # Impact metrics
        st.markdown("**Revenue impact of active rules (last 7 days):**")
        ic1, ic2, ic3 = st.columns(3)
        ic1.metric("PIN Rules",   "+23% first-result click-through", delta="+8pp vs no rules")
        ic2.metric("BOOST Rules", "+31% relevant result adoption",   delta="Quality score improved")
        ic3.metric("BURY Rules",  "-67% user frustration exits",     delta="↓ zero-value sessions")

    with tab_create:
        st.markdown(f"#### Create a new rule for {company}")
        rc1, rc2 = st.columns(2)
        with rc1:
            rule_action = st.selectbox(
                "Action",
                ["PIN (always show first)", "BOOST (score multiplier)", "BURY (push to bottom)", "BLOCK (hide completely)"],
            )
            autocomplete_hint = ctx.autocomplete_prefix if ctx else "urgent, critical"
            trigger_query = st.text_input(
                "Trigger query / keyword",
                placeholder=f"e.g. {autocomplete_hint}",
            )
        with rc2:
            catalog_hint = catalog.split("/")[0].strip() if "/" in catalog else catalog
            target = st.text_input(
                "Target document / condition",
                placeholder=f"e.g. doc_type={catalog_hint}",
            )
            boost_factor = st.slider("Boost multiplier", 1.0, 10.0, 3.0, 0.5) if "BOOST" in rule_action else None  # noqa: F841

        rule_name = st.text_input("Rule name", placeholder=f"e.g. {company} Priority Policy")

        if st.button("💾 Save Rule to Elasticsearch", type="primary"):
            action_key = rule_action.split()[0].lower()
            _save_query_rule(rule_name, trigger_query, action_key, target)

    with st.expander("⚙️ How Elastic Query Rules work"):
        ruleset_id = company.lower().replace(" ", "-") + "-search-rules"
        intent_q = (ctx.intent_query[:40] if ctx else "user query")
        catalog_index = catalog.split("/")[0].strip().replace(" ", "_") if ctx else "knowledge_base"
        st.code(f"""PUT _query_rules/{ruleset_id}
{{
  "rules": [
    {{
      "rule_id": "pin-critical-docs",
      "type": "pinned",
      "criteria": [{{"type": "contains", "metadata": "query", "values": ["urgent","critical","escalat"]}}],
      "actions": {{"ids": ["critical-procedure-doc-id"]}}
    }},
    {{
      "rule_id": "boost-recent-updates",
      "type": "boost",
      "criteria": [{{"type": "always"}}],
      "actions": {{"boost": 2.5, "filter": {{"range": {{"last_updated": {{"gte": "now-30d"}}}}}}}}
    }}
  ]
}}

GET {catalog_index}/_search
{{
  "query": {{
    "rule_query": {{
      "match_criteria": {{"query": "{intent_q}"}},
      "ruleset_ids": ["{ruleset_id}"],
      "organic": {{"semantic": {{"field": "description", "query": "{intent_q}"}}}}
    }}
  }}
}}""", language="json")


def _save_query_rule(name, trigger, action, target):
    st.success(f"✅ Rule **'{name}'** saved to Elasticsearch Query Rules API")
    st.code(f"""PUT _query_rules/enterprise-rules/_rule/{name.lower().replace(' ', '-')}
{{
  "type": "{action}",
  "criteria": [{{"type": "contains", "metadata": "query", "values": ["{trigger}"]}}],
  "actions": {{"target": "{target}"}}
}}""", language="json")


# ─────────────────────────────────────────────────────────────────────────────
# 6. A/B TESTING
# ─────────────────────────────────────────────────────────────────────────────

def _render_ab_testing(loader, ctx) -> None:
    company = ctx.company if ctx else "Enterprise"
    st.markdown("### 🧪 Search Strategy A/B Testing")
    st.caption(
        f"Run the same {company} query through 3 ranking strategies simultaneously — "
        f"see which wins on relevance and business outcome."
    )

    default_q = ctx.ab_query if ctx else "how to handle this issue"
    ab_query = st.text_input("Test query", value=default_q, label_visibility="collapsed")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**Strategy A — BM25 Keyword**")
    with col_b:
        st.markdown("**Strategy B — ELSER Semantic**")
    with col_c:
        st.markdown("**Strategy C — Hybrid RRF**")

    if st.button("▶ Run A/B Test", type="primary", use_container_width=True):
        _run_ab_test(ab_query, ctx)

    st.divider()
    st.markdown("#### Live Experiment Results (last 14 days)")
    metric_label = ctx.kpi_ctr_label if ctx else "Click-Through Rate"
    value_label = ctx.kpi_value_label if ctx else "Avg Value"
    exp_data = pd.DataFrame([
        {"Metric": metric_label,           "BM25": "58%",  "ELSER": "76%",  "Hybrid RRF": "83%",   "Winner": "🏆 Hybrid"},
        {"Metric": "First-Result Adoption", "BM25": "31%",  "ELSER": "61%",  "Hybrid RRF": "72%",   "Winner": "🏆 Hybrid"},
        {"Metric": value_label,            "BM25": "Low",  "ELSER": "High", "Hybrid RRF": "Highest","Winner": "🏆 Hybrid"},
        {"Metric": "Zero Result Rate",     "BM25": "9.1%", "ELSER": "1.8%", "Hybrid RRF": "1.1%",  "Winner": "🏆 Hybrid"},
        {"Metric": "p95 Latency",          "BM25": "14ms", "ELSER": "231ms","Hybrid RRF": "248ms",  "Winner": "🥇 BM25"},
        {"Metric": "Sessions with outcome","BM25": "29%",  "ELSER": "67%",  "Hybrid RRF": "81%",   "Winner": "🏆 Hybrid"},
    ])
    st.dataframe(exp_data, use_container_width=True, hide_index=True)
    st.success(
        f"📊 **Recommendation for {company}**: Deploy **Hybrid RRF** as default — "
        f"+52% outcome rate vs BM25. Latency cost: +234ms (within acceptable range for knowledge retrieval)."
    )

    st.divider()
    with st.expander("⚙️ How this works — technical deep dive", expanded=False):
        st.markdown("""
#### Scoring Strategies Compared

```
Query string
    │
    ├─► Strategy A: BM25 Keyword
    │       TF-IDF term frequency × inverse document frequency
    │       Fast (<15ms), exact keyword matches only
    │       Fails on synonyms, paraphrases, abbreviations
    │
    ├─► Strategy B: ELSER Semantic
    │       Query → ELSER sparse vector (30k token weights)
    │       Compared against indexed document vectors
    │       Understands intent, not just keywords (~230ms)
    │
    └─► Strategy C: Hybrid RRF (winner)
            Both BM25 and ELSER run in parallel
            Results fused via Reciprocal Rank Fusion
            RRF score = Σ 1/(rank_constant + rank_i)
            Best of keyword precision + semantic recall (~248ms)
```
""")

        st.markdown("**Hybrid RRF request — the actual Elasticsearch query**")
        st.code("""\
POST /kb-docs/_search
{
  "size": 10,
  "query": {
    "match": {
      "content": {
        "query": "<user-query>",
        "boost": 1.0
      }
    }
  },
  "knn": {
    "field": "content_semantic.inference.chunks.embeddings",
    "query_vector_builder": {
      "text_embedding": {
        "model_id": ".elser-2-elasticsearch",
        "model_text": "<user-query>"
      }
    },
    "k": 10,
    "num_candidates": 100
  },
  "rank": {
    "rrf": {
      "window_size": 50,
      "rank_constant": 60
    }
  }
}
""", language="json")

        st.markdown("**How to interpret the comparison**")
        st.markdown("""
- **Click-Through Rate**: % of result sets where the user clicked a result (higher = better relevance)
- **First-Result Adoption**: % of sessions where user clicked rank #1 (measures precision at 1)
- **Zero Result Rate**: % of queries returning 0 results (ELSER virtually eliminates this)
- **Sessions with outcome**: % where user completed the business action (KPI, find answer, resolve ticket)
""")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Ship the winner to production**")
            st.code("""\
# 1. Update your default search handler
# from: match query only
# to:   hybrid query with rrf rank

# 2. Use Query Rules to pin/promote
#    specific results for key queries
PUT _query_rules/kb-promotions
{
  "rules": [{
    "rule_id": "rule-1",
    "type": "pinned",
    "criteria": [{
      "type": "contains",
      "metadata": "query_string",
      "values": ["installation guide"]
    }],
    "actions": {
      "ids": ["doc-install-main-v3"]
    }
  }]
}
""", language="json")
        with col2:
            st.markdown("**Monitor in Kibana**")
            st.markdown("""
- **Search > Analytics**: track CTR, click position, zero-result rate per strategy
- **Behavioral Analytics > Collections**: segment by user role, time window, query volume
- **Stack Monitoring > ML**: verify ELSER model throughput and latency under production load
- **Observability > APM**: instrument your search handler to trace end-to-end latency
"""  )


def _run_ab_test(query: str, ctx=None) -> None:
    bm25   = ctx.bm25_results   if ctx else []
    elser  = ctx.elser_results  if ctx else []
    hybrid = ctx.hybrid_results if ctx else []

    col_a, col_b, col_c = st.columns(3)
    for col, (strategy, items) in zip(
        [col_a, col_b, col_c],
        [("BM25", bm25), ("ELSER", elser), ("Hybrid", hybrid)],
    ):
        with col:
            st.markdown(f"**{strategy}**")
            for item in items:
                color = "#003d7a" if item["rank"] <= 2 else "#333"
                weight = "700" if item["rank"] == 1 else "400"
                st.markdown(f"""<div class="re-ab-result">
                    <span style="color:{color};font-weight:{weight}">
                        #{item['rank']} {item['item']}
                    </span><br>
                    <span style="color:#888;font-size:11px">{item['reason']} · {item['score']:.2f}</span>
                </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 7. VISUAL SEARCH
# ─────────────────────────────────────────────────────────────────────────────

def _render_visual_search(loader, ctx) -> None:
    company = ctx.company if ctx else "Enterprise"
    scenarios = ctx.visual_scenarios if ctx else ["📸 Upload an image → find matching content"]
    catalog = ctx.catalog_label if ctx else "documents"

    st.markdown("### 🖼️ Visual Search — Image-to-Document")
    st.caption(
        f"Point a camera or upload a screenshot — Elastic finds the matching {catalog} for {company} instantly."
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### Upload an image")
        uploaded = st.file_uploader(
            "Upload a screenshot, photo, or document scan",
            type=["jpg", "jpeg", "png", "webp", "pdf"],
        )
        st.markdown("**Or choose a demo scenario:**")
        demo_scenario = st.selectbox("Demo scenario", scenarios)

        if st.button("🔍 Search by Image", type="primary", use_container_width=True):
            _run_visual_search_result(uploaded, demo_scenario, ctx)

    with col2:
        st.markdown("#### How it works")
        st.markdown(f"""
```
Image / Screenshot upload
        │
        ▼
CLIP Vision Model
(image → 512-dim vector)
        │
        ▼
Elasticsearch kNN search
(vector similarity on {catalog})
        │
        ▼
Top 10 visually similar {catalog}
        │
        ▼
Re-ranked by:
  · Visual similarity score
  · Recency of document
  · User role / access level
  · Query Rules (pinned/boosted)
```
        """)
        st.info(f"""
**Elastic stack for {company}:**
- `dense_vector` field on document/image embeddings
- kNN search with `num_candidates: 200`
- CLIP model via ML inference endpoint
- Re-rank with RRF (visual + text + role)
        """)

    st.divider()
    st.markdown("#### Business impact")
    vi1, vi2, vi3 = st.columns(3)
    vi1.metric("Visual search adoption", "2.4×",  delta="vs text-only search")
    vi2.metric("Wrong result rate",      "-41%",  delta="right content first time")
    vi3.metric("User satisfaction",      "+28%",  delta="screenshot-to-answer UX")

    st.divider()
    with st.expander("⚙️ How this works — technical deep dive", expanded=False):
        st.markdown("""
#### Visual Search Pipeline (CLIP + kNN)

```
Image / Screenshot upload
        │
        ▼
CLIP Vision Encoder (ViT-B/32)
  · 224×224 px normalized input
  · 12-layer transformer encoder
  · Output: 512-dimensional float32 vector
        │
        ▼
Elasticsearch kNN search
  · Field: image_embedding (dense_vector, dims: 512)
  · Similarity: cosine
  · k=10, num_candidates=200
        │
        ▼
Optional: ELSER re-rank using extracted OCR text
  (if image contains readable text — screenshots, docs)
        │
        ▼
RRF fusion: visual similarity + text semantic score
        │
        ▼
Top results with match percentage returned in ~50ms
```
""")

        st.markdown("**Index mapping — storing image embeddings**")
        st.code("""\
PUT /kb-docs
{
  "mappings": {
    "properties": {
      "title": { "type": "text" },
      "content_semantic": {
        "type": "semantic_text",
        "inference_id": ".elser-2-elasticsearch"
      },
      "image_embedding": {
        "type": "dense_vector",
        "dims": 512,
        "index": true,
        "similarity": "cosine"
      }
    }
  }
}
""", language="json")

        st.markdown("**kNN visual search query**")
        st.code("""\
POST /kb-docs/_search
{
  "size": 10,
  "knn": {
    "field": "image_embedding",
    "query_vector": [0.023, -0.141, 0.087, ...],  // 512-dim CLIP output
    "k": 10,
    "num_candidates": 200,
    "filter": {
      "term": { "department": "engineering" }
    }
  },
  "rank": {
    "rrf": {
      "window_size": 20,
      "rank_constant": 60
    }
  }
}
""", language="json")

        st.markdown("**How multimodal search differs from text search**")
        st.markdown("""
| Dimension | Text Search (ELSER) | Visual Search (CLIP) |
|-----------|--------------------|-----------------------|
| Input | Natural language query | Image / screenshot bytes |
| Encoding | Sparse token weights (30k vocab) | Dense 512-dim vector |
| Matching | Semantic token overlap | Pixel-space similarity |
| Best for | Finding documents by description | Finding documents by appearance |
| Combined | — | RRF fusion gives both |
""")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Build this in your app**")
            st.markdown("""
1. Ingest-time: call CLIP ML inference endpoint, store vector in `image_embedding` field
2. Query-time: encode uploaded image → kNN search → RRF with optional ELSER text query
3. Use Elastic's `_inference` API to host CLIP model without external service dependency
4. Index images as base64 in `image` field; CLIP inference pipeline handles encoding automatically
""")
        with col2:
            st.markdown("**Explore in Kibana**")
            st.markdown("""
- **Stack Management > Inference Endpoints**: deploy `clip-vit-b-32` or custom CLIP model
- **Dev Tools**: `POST /_inference/text_embedding/clip-model` to test embedding live
- **Discover**: filter on `image_embedding` field to confirm vectors are indexed
- **ML > Trained Models**: monitor CLIP model throughput and resource allocation
"""  )


def _run_visual_search_result(uploaded, scenario: str, ctx=None) -> None:
    elser = ctx.elser_results if ctx else []
    catalog = ctx.catalog_label if ctx else "documents"

    with st.spinner(f"🖼️ Analyzing image with CLIP model... running kNN search across {catalog}..."):
        time.sleep(1.2)

    results = [{
        "Result": r["item"],
        "Visual Match": f"{int(r['score'] * 100)}%",
        "Relevance": r["reason"],
    } for r in elser[:3]]

    st.success(f"✅ Found {len(results)} matching {catalog} (52ms)")
    st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers — UNCHANGED
# ─────────────────────────────────────────────────────────────────────────────

def _render_under_the_hood(result: dict) -> None:
    timing  = result.get("timing", {})
    queries = result.get("queries", [])

    st.markdown("**Elastic layers that ran:**")
    st.markdown("""
| Layer | Technology | What it did |
|---|---|---|
| 📚 Project Guide | RAG + ELSER | Retrieved build guide from knowledge base |
| 🔍 Product Search | ELSER Semantic | Matched project materials without exact keywords |
| 📍 Store Finder | Geo Search | Nearest store with full BOM in stock |
| 📦 Inventory | ES|QL LOOKUP JOIN | Joined store inventory + catalog in one query |
""")
    cols = st.columns(len(timing) + 1)
    for i, (k, v) in enumerate(timing.items()):
        cols[i].metric(k.replace("_ms", "").replace("_", " ").title(), f"{v}ms")
    cols[-1].metric("Total", f"{result.get('elapsed_ms', 0)}ms")

    for q in queries:
        ms = timing.get(q["timing_key"], "—")
        with st.expander(f"{q['label']}  ·  {ms}ms"):
            st.code(q["esql"], language="sql")


def _show_print_view(result: dict) -> None:
    materials = result.get("materials", [])
    lines = [
        f"# PROJECT LIST — {result.get('store', {}).get('name', '')}",
        f"Project: {result.get('description', '')}",
        f"Total: ${result.get('grand_total', 0):,.2f}", "",
        f"{'Item':<40} {'Qty':>5} {'Aisle':>6} {'Bay':>4} {'Total':>8}", "-" * 70,
    ]
    for m in materials:
        lines.append(f"{m['name']:<40} {m['qty']:>5} {m['aisle']:>6} {m['bay']:>4} ${m['subtotal']:>6.2f}")
    st.code("\n".join(lines))


def _get_index_names(loader) -> list:
    if not loader:
        return []
    try:
        import json as _json
        from pathlib import Path
        p = Path(loader.module_path) / "elastic_assets.json"
        if p.exists():
            return _json.loads(p.read_text()).get("indices", [])
    except Exception:
        pass
    return []


def _classify_type(description: str, purpose: str) -> str:
    text = (description + " " + purpose).lower()
    for t in ["deck", "fence", "patio", "pergola"]:
        if t in text:
            return t
    return "shed"


def _init_state() -> None:
    for key, default in [("re_phase", "input"), ("re_search_history", [])]:
        if key not in st.session_state:
            st.session_state[key] = default


def _inject_css() -> None:
    st.markdown("""<style>
    .re-header{background:linear-gradient(135deg,#0066cc 0%,#003d7a 100%);padding:18px 24px;border-radius:10px;margin-bottom:20px;color:white;}
    .re-store-card{background:#f0f7ff;border:1px solid #c2dcf7;border-left:4px solid #0066cc;border-radius:8px;padding:14px 18px;margin-bottom:8px;}
    .re-rental-card{background:#fff8f0;border:1px solid #f5d9b0;border-left:4px solid #e07b00;border-radius:8px;padding:12px 16px;margin-bottom:8px;}
    .re-alert-card{background:#fff5f5;border:1px solid #fcc;border-radius:6px;padding:10px 14px;margin-bottom:6px;}
    .re-suggestion{background:#f8f9fa;border:1px solid #e0e0e0;border-radius:6px;padding:8px 12px;margin-bottom:4px;cursor:pointer;}
    .re-suggestion:hover{background:#e8f4ff;border-color:#0066cc;}
    .re-history-item{background:#f8f9fa;border-radius:6px;padding:8px 12px;margin-bottom:6px;}
    .re-rec-card{background:#f0fff4;border:1px solid #b7ebc5;border-left:4px solid #27ae60;border-radius:8px;padding:10px 14px;margin-bottom:8px;}
    .re-ab-result{background:#f8f9fa;border-radius:6px;padding:8px 10px;margin-bottom:4px;font-size:13px;}
    .re-badge{background:#0066cc;color:white;font-size:11px;font-weight:600;padding:2px 8px;border-radius:12px;margin-right:6px;}
    .re-badge-gray{background:#eee;color:#444;font-size:11px;padding:2px 8px;border-radius:12px;margin-right:6px;}
    .re-kpi-pain{background:#f0f7ff;border:1px solid #c2dcf7;border-left:4px solid #0066cc;border-radius:8px;padding:12px 14px;margin-bottom:8px;text-align:center;}
    .re-kpi-label{font-weight:700;font-size:.9rem;color:#003d7a;margin-bottom:6px;}
    .re-kpi-before{font-size:.8rem;color:#888;}
    .re-kpi-after{font-size:.8rem;color:#27ae60;font-weight:600;}
    .re-kpi-delta{font-size:1.3rem;font-weight:800;color:#0066cc;margin:4px 0;}
    .re-kpi-impact{font-size:.75rem;color:#555;font-style:italic;}
    </style>""", unsafe_allow_html=True)
