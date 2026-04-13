"""
Eval Workbench Tab — Dynamic Customer Evaluation Query Pack

Generates and displays structured ES|QL evaluation scenarios for any demo
module. Scenarios are LLM-generated based on the demo's real index schema
and customer context, then cached in eval_scenarios.json alongside the demo.
"""

import streamlit as st
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Category colour palette — LLM may produce any category names
# ---------------------------------------------------------------------------

_PALETTE = [
    "#0077CC", "#B22222", "#D4730A", "#1A7A4A",
    "#6B21A8", "#444444", "#1E6F9F", "#8B5500",
]

_KNOWN_COLORS = {
    "document search":            "#006B6B",
    "agent kb search":            "#006B6B",
    "kb search":                  "#006B6B",
    "search":                     "#006B6B",
    "retrieval quality":          "#0077CC",
    "tenant isolation":           "#B22222",
    "tenant isolation & acl":     "#B22222",
    "acl":                        "#B22222",
    "performance":                "#D4730A",
    "performance & latency":      "#D4730A",
    "ingestion":                  "#1A7A4A",
    "ingestion & data freshness": "#1A7A4A",
    "data freshness":             "#1A7A4A",
    "content freshness":          "#1A7A4A",
    "containment analytics":      "#6B21A8",
    "compliance":                 "#444444",
    "compliance & audit":         "#444444",
    "access anomaly detection":   "#B22222",
    "business analytics":         "#1E6F9F",
    "data quality":               "#1A7A4A",
}


def _category_color(category: str, index: int = 0) -> str:
    key = category.lower()
    for k, v in _KNOWN_COLORS.items():
        if k in key:
            return v
    return _PALETTE[index % len(_PALETTE)]


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render_eval_workbench_tab(loader):
    """Render the Eval Workbench tab for the currently selected demo."""
    module_name = st.session_state.get("current_demo_module", "")
    module_path = Path("demos") / module_name

    from src.services.eval_scenario_generator import EvalScenarioGenerator
    gen = EvalScenarioGenerator(str(module_path))

    stored = gen.load_scenarios()

    if stored is None:
        _render_generate_prompt(gen, module_name)
    else:
        _render_workbench(stored, gen, module_name)


# ---------------------------------------------------------------------------
# State: no scenarios yet
# ---------------------------------------------------------------------------

def _render_generate_prompt(gen, module_name: str):
    st.markdown("### 🧪 Eval Workbench")
    st.info(
        "**No evaluation scenarios generated yet for this demo.**\n\n"
        "Click the button below to generate a customer evaluation query pack tailored "
        "to this demo's actual index schema and customer context. "
        "Scenarios are cached to `eval_scenarios.json` and available instantly on subsequent visits."
    )

    col1, col2 = st.columns([2, 5])
    with col1:
        generate_clicked = st.button(
            "🔨 Generate Eval Pack",
            use_container_width=True,
            type="primary",
            key="eval_generate_btn",
        )

    if generate_clicked or st.session_state.get("eval_generating"):
        st.session_state.eval_generating = True
        _run_generation(gen)


def _run_generation(gen):
    """Execute generation with live progress messages."""
    progress_placeholder = st.empty()
    messages = []

    def cb(msg):
        messages.append(msg)
        progress_placeholder.markdown("\n\n".join(messages))

    try:
        gen.generate(progress_callback=cb)
        st.session_state.eval_generating = False
        st.rerun()
    except Exception as e:
        st.session_state.eval_generating = False
        st.error(f"❌ Generation failed: {e}")
        with st.expander("Details"):
            import traceback
            st.code(traceback.format_exc())


# ---------------------------------------------------------------------------
# State: scenarios loaded
# ---------------------------------------------------------------------------

def _render_workbench(stored: dict, gen, module_name: str):
    scenarios = stored.get("scenarios", [])
    generated_at = stored.get("generated_at", "")
    company = stored.get("company", module_name)

    # Header row
    col_title, col_regen = st.columns([7, 2])
    with col_title:
        st.info(
            f"🧪 **{company} — Evaluation Query Pack** — "
            f"{len(scenarios)} scenarios across "
            f"{len(set(s['category'] for s in scenarios))} categories. "
            "Run them live, export as markdown, or share with the customer."
        )
    with col_regen:
        st.caption(f"Generated: {generated_at[:10] if generated_at else 'unknown'}")
        if st.button("🔄 Regenerate", key="eval_regen_btn", use_container_width=True):
            gen._scenarios_path.unlink(missing_ok=True)
            st.rerun()

    if not scenarios:
        st.warning("Scenario file exists but contains no scenarios. Try regenerating.")
        return

    # Build ordered category list — pin Document Search first
    _DOC_SEARCH_NAMES = {"document search", "agent kb search", "kb search", "search"}
    raw_order = list(dict.fromkeys(s["category"] for s in scenarios))
    doc_cats  = [c for c in raw_order if c.lower() in _DOC_SEARCH_NAMES]
    other_cats = [c for c in raw_order if c.lower() not in _DOC_SEARCH_NAMES]
    ordered_cats = doc_cats + other_cats

    cat_icon_map = {s["category"]: s.get("category_icon", "📋") for s in scenarios}
    cat_color_map = {
        cat: _category_color(cat, i) for i, cat in enumerate(ordered_cats)
    }

    # Category filter
    all_label = "🗂️ All"
    cat_options = [all_label] + [
        f"{cat_icon_map[c]} {c}" for c in ordered_cats
    ]
    selected = st.segmented_control(
        "Category",
        options=cat_options,
        default=all_label,
        key="eval_cat_filter",
        label_visibility="collapsed",
    )

    # Filter
    if not selected or selected == all_label:
        visible = scenarios
    else:
        # Strip leading "icon " to recover the category name
        raw_cat = selected.split(" ", 1)[1] if " " in selected else selected
        visible = [s for s in scenarios if s["category"] == raw_cat]

    st.caption(f"Showing **{len(visible)}** of **{len(scenarios)}** scenarios")

    # Init session state buckets
    for key in ("eval_results", "eval_errors"):
        if key not in st.session_state:
            st.session_state[key] = {}

    # Render scenarios
    _DOC_SEARCH_NAMES = {"document search", "agent kb search", "kb search", "search"}
    current_cat = None
    for scenario in visible:
        cat = scenario["category"]
        if cat != current_cat:
            current_cat = cat
            color = cat_color_map.get(cat, "#555")
            icon  = cat_icon_map.get(cat, "📋")
            st.markdown(
                f"<h3 style='color:{color};margin-top:1.5em;margin-bottom:0.3em'>"
                f"{icon} {cat}</h3>",
                unsafe_allow_html=True,
            )
            # Special banner for document search category
            if cat.lower() in _DOC_SEARCH_NAMES:
                st.markdown(
                    "<div style='background:#e6f7f7;border:1px solid #006B6B;border-radius:6px;"
                    "padding:8px 14px;margin-bottom:12px;font-size:0.88em'>"
                    "🧑‍💼 <strong>Agent / End-User Perspective</strong> — These queries simulate what a "
                    "customer care agent or knowledge worker would type into the search box. "
                    "Each one returns actual documents (not aggregations). "
                    "Use these to demo <strong>retrieval quality</strong> and "
                    "<strong>relevance ranking</strong> to the business audience."
                    "</div>",
                    unsafe_allow_html=True,
                )
        _render_card(scenario, cat_color_map)

    # Export
    st.divider()
    _render_export(stored)


# ---------------------------------------------------------------------------
# Scenario card
# ---------------------------------------------------------------------------

def _render_card(scenario: dict, cat_color_map: dict):
    sid = scenario.get("id", "?")
    cat = scenario.get("category", "")
    color = cat_color_map.get(cat, "#555")
    result_key = f"eval_result_{sid}"
    error_key  = f"eval_error_{sid}"

    with st.container(border=True):
        # Header
        col_id, col_title, col_aud = st.columns([1, 7, 3])
        with col_id:
            st.markdown(
                f"<span style='background:{color};color:white;padding:3px 8px;"
                f"border-radius:4px;font-weight:bold;font-size:0.85em'>{sid}</span>",
                unsafe_allow_html=True,
            )
        with col_title:
            st.markdown(f"**{scenario.get('title', '')}**")
        with col_aud:
            aud_tags = " ".join(
                f"`{a.capitalize()}`" for a in scenario.get("audience", [])
            )
            st.markdown(aud_tags)

        # Description
        if scenario.get("description"):
            st.caption(scenario["description"])

        # "Proves" callout
        proves = scenario.get("proves", "")
        if proves:
            st.markdown(
                f"<div style='border-left:3px solid {color};padding:4px 10px;"
                f"background:#f8f9fa;margin:4px 0 8px;border-radius:0 4px 4px 0;"
                f"font-size:0.85em'>✅ <em>{proves}</em></div>",
                unsafe_allow_html=True,
            )

        # Index badges
        indices = scenario.get("indices", [])
        if indices:
            st.caption("📑 Indices: " + " ".join(f"`{i}`" for i in indices))

        # ES|QL — native copy icon appears top-right on hover
        esql = scenario.get("esql", "")
        st.code(esql, language="sql")

        # Presenter note
        note = scenario.get("note", "")
        if note:
            st.markdown(
                f"<div style='font-size:0.82em;color:#555;background:#fffbe6;"
                f"border:1px solid #ffe58f;padding:5px 10px;border-radius:4px;margin-top:4px'>"
                f"🗣️ <strong>Presenter note:</strong> {note}</div>",
                unsafe_allow_html=True,
            )

        # Action buttons
        col_run, col_space = st.columns([2, 8])
        with col_run:
            if st.button(
                "▶️ Run Query",
                key=f"eval_run_{sid}",
                use_container_width=True,
                type="primary",
            ):
                _execute(sid, esql, scenario)

        # Results
        if result_key in st.session_state.eval_results:
            result = st.session_state.eval_results[result_key]
            row_count = len(result.get("values", []))
            col_ok, col_clr = st.columns([7, 1])
            with col_ok:
                st.success(f"✅ {row_count} row{'s' if row_count != 1 else ''} returned")
            with col_clr:
                if st.button("✖", key=f"eval_clr_{sid}", use_container_width=True):
                    del st.session_state.eval_results[result_key]
                    st.session_state.eval_errors.pop(error_key, None)
                    st.rerun()
            with st.expander("📊 Results", expanded=True):
                _render_table(result, sid)

        if error_key in st.session_state.eval_errors:
            st.error(f"❌ {st.session_state.eval_errors[error_key]}")


def _execute(sid: str, esql: str, scenario: dict = None):
    result_key = f"eval_result_{sid}"
    error_key  = f"eval_error_{sid}"
    st.session_state.eval_results.pop(result_key, None)
    st.session_state.eval_errors.pop(error_key, None)
    try:
        from src.services.elasticsearch_indexer import ElasticsearchIndexer
        indexer = ElasticsearchIndexer()
        success, result, error = indexer.execute_esql(esql)
        if success:
            st.session_state.eval_results[result_key] = result
            # Record successful queries (>0 rows) to the cache for future few-shot examples
            row_count = len(result.get("values", []))
            if row_count > 0 and scenario:
                try:
                    from src.services.esql_query_cache import EsqlQueryCache
                    module = st.session_state.get("current_demo_module", "unknown")
                    EsqlQueryCache().record(
                        query=esql,
                        category=scenario.get("category", ""),
                        title=scenario.get("title", sid),
                        demo_module=module,
                        row_count=row_count,
                        schema_indices=scenario.get("indices", []),
                    )
                except Exception:
                    pass  # Cache errors never block the UI
        else:
            st.session_state.eval_errors[error_key] = error or "Unknown error"
    except Exception as e:
        st.session_state.eval_errors[error_key] = str(e)


def _render_table(result: dict, unique_key: str):
    import pandas as pd
    columns = [c.get("name", f"col_{i}") for i, c in enumerate(result.get("columns", []))]
    values  = result.get("values", [])
    if not values:
        st.info("Query returned 0 rows.")
        return
    try:
        df = pd.DataFrame(values, columns=columns)
        st.dataframe(df, use_container_width=True, key=f"df_{unique_key}")
    except Exception as e:
        st.warning(f"Could not render table: {e}")
        st.json(result)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def _render_export(stored: dict):
    st.markdown("### 📤 Export Query Pack")
    st.caption("Download all scenarios as a shareable markdown file.")
    md = _build_markdown(stored)
    module = stored.get("demo_module", "demo")
    st.download_button(
        label="⬇️ Download eval_query_pack.md",
        data=md,
        file_name=f"{module}_eval_query_pack.md",
        mime="text/markdown",
        key="eval_export_btn",
    )


def _build_markdown(stored: dict) -> str:
    company   = stored.get("company", "Demo")
    gen_at    = stored.get("generated_at", "")[:10]
    scenarios = stored.get("scenarios", [])

    lines = [
        f"# {company} — Elastic Evaluation Query Pack",
        f"Generated: {gen_at}",
        "",
        "---",
        "",
    ]
    current_cat = None
    for s in scenarios:
        if s["category"] != current_cat:
            current_cat = s["category"]
            lines += [f"## {s.get('category_icon','📋')} {current_cat}", ""]
        lines += [
            f"### {s['id']} — {s['title']}",
            "",
            f"**Audience:** {', '.join(s.get('audience', []))}",
            "",
            s.get("description", ""),
            "",
            f"> ✅ **Proves:** {s.get('proves', '')}",
            "",
            f"**Indices:** `{'`, `'.join(s.get('indices', []))}`",
            "",
            "```sql",
            s.get("esql", ""),
            "```",
            "",
        ]
        if s.get("note"):
            lines += [f"> 🗣️ **Presenter note:** {s['note']}", ""]
        lines += ["---", ""]
    return "\n".join(lines)
