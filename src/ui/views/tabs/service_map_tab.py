"""
Service Map Tab — Observability Pillar

Displays APM service topology and SLO definitions for Observability demos:
- Service dependency map rendered as a visual diagram
- SLO definitions with target percentages and ES|QL queries
- APM index patterns and data overview
"""

import streamlit as st
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


def _load_observability_strategy(module_name: str) -> dict:
    """Load query_strategy.json for a demo module."""
    path = Path("demos") / module_name / "query_strategy.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception as e:
            logger.warning(f"Could not load query_strategy.json: {e}")
    return {}


def _render_service_map(service_map: dict):
    """Render service topology as a visual Mermaid-style diagram using st.graphviz_chart."""

    services = service_map.get("services", [])
    dependencies = service_map.get("dependencies", [])
    entry_points = service_map.get("entry_points", [])

    if not services:
        st.info("No services defined in the service map.")
        return

    # Language colour map
    lang_colors = {
        "python": "#3776ab",
        "java": "#ed8b00",
        "go": "#00acd7",
        "nodejs": "#339933",
        "dotnet": "#512bd4",
        "ruby": "#cc342d",
    }

    # --- Text-based service map ---
    st.markdown("#### Service Topology")

    # Entry points with arrow chain
    if entry_points:
        st.caption(f"**Entry points:** {', '.join(f'`{s}`' for s in entry_points)}")

    # Build adjacency for display
    downstream: dict = {}
    for dep in dependencies:
        if len(dep) >= 2:
            upstream, downstream_svc = dep[0], dep[1]
            downstream.setdefault(upstream, []).append(downstream_svc)

    # Service cards
    service_lookup = {s.get("name", ""): s for s in services}
    visited = set()

    def render_service_node(name: str, depth: int = 0):
        if name in visited:
            return
        visited.add(name)
        svc = service_lookup.get(name, {})
        lang = svc.get("language", "unknown")
        version = svc.get("version", "")
        color = lang_colors.get(lang.lower(), "#888")
        indent = "&nbsp;" * (depth * 8)
        arrow = "└→ " if depth > 0 else ""
        st.markdown(
            f"{indent}{arrow}<span style='background:{color};color:white;padding:2px 8px;"
            f"border-radius:4px;font-size:0.8rem;font-family:monospace'>{name}</span>"
            f"&nbsp;<span style='color:#888;font-size:0.75rem'>{lang} {version}</span>",
            unsafe_allow_html=True
        )
        for child in downstream.get(name, []):
            render_service_node(child, depth + 1)

    # Render from entry points first, then any orphans
    for ep in entry_points:
        render_service_node(ep, 0)
    for svc in services:
        render_service_node(svc.get("name", ""), 0)

    # Stats row
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Services", len(services))
    with col2:
        st.metric("Dependencies", len(dependencies))
    with col3:
        langs = list({s.get("language", "unknown") for s in services})
        st.metric("Languages", len(langs), help=", ".join(langs))

    # Service detail table
    st.markdown("**Service Details**")
    for svc in services:
        name = svc.get("name", "unknown")
        lang = svc.get("language", "unknown")
        version = svc.get("version", "")
        deps = downstream.get(name, [])
        dep_str = f"→ {', '.join(deps)}" if deps else "leaf service"
        st.caption(f"**{name}** · {lang} {version} · {dep_str}")


def _render_slo_queries(slo_queries: list):
    """Render SLO definitions with targets and ES|QL queries."""

    if not slo_queries:
        st.info("No SLO queries were generated for this demo.")
        return

    st.markdown(f"#### Service Level Objectives ({len(slo_queries)} defined)")

    for i, slo in enumerate(slo_queries, 1):
        slo_name = slo.get("slo_name", f"SLO {i}")
        service = slo.get("service", "")
        target = slo.get("target_percentage", 99.9)
        window = slo.get("window_days", 30)
        sli_query = slo.get("sli_query", "")
        burn_rate_query = slo.get("burn_rate_query", "")
        error_budget_query = slo.get("error_budget_query", "")

        # Target colour
        if target >= 99.9:
            target_color = "🟢"
        elif target >= 99.0:
            target_color = "🟡"
        else:
            target_color = "🔴"

        with st.expander(
            f"{target_color} {slo_name}  ·  {target}%  ·  {window}-day window",
            expanded=(i == 1),
        ):
            meta_col1, meta_col2, meta_col3 = st.columns(3)
            with meta_col1:
                st.metric("Target", f"{target}%")
            with meta_col2:
                st.metric("Window", f"{window}d")
            with meta_col3:
                error_budget = round(100 - target, 3)
                st.metric("Error Budget", f"{error_budget}%", help="Allowed failure rate within the window")

            if service:
                st.caption(f"**Service:** `{service}`")

            if sli_query:
                st.markdown("**SLI Query** *(measures the indicator)*")
                st.code(sli_query, language="sql")

            if burn_rate_query:
                st.markdown("**Burn Rate Query** *(detect SLO violations early)*")
                st.code(burn_rate_query, language="sql")

            if error_budget_query:
                st.markdown("**Error Budget Remaining**")
                st.code(error_budget_query, language="sql")


def render_service_map_tab(loader):
    """Render the Service Map tab for Observability demos."""

    strategy = _load_observability_strategy(st.session_state.current_demo_module)
    service_map = strategy.get("service_map", {})
    slo_queries = strategy.get("slo_queries", [])
    sub_category = strategy.get("sub_category", loader.config.get("sub_category", "apm"))
    index_patterns = strategy.get("index_patterns", [])

    has_service_map = bool(service_map.get("services"))
    has_slos = bool(slo_queries)

    if not has_service_map and not has_slos:
        st.info(
            "No service map or SLO data found for this demo. "
            "This tab is available for Observability pillar demos (APM, SLO). "
            "Generate an Observability demo to see service topology here."
        )
        return

    services_count = len(service_map.get("services", []))
    slo_count = len(slo_queries)

    st.info(
        f"📡 **Observability Demo** — {sub_category.upper()} · "
        f"{services_count} services · {slo_count} SLOs defined. "
        "Queries use OpenTelemetry / EDOT field conventions."
    )

    # Index patterns reference
    if index_patterns:
        st.caption(
            f"**Index patterns:** `{'`, `'.join(index_patterns)}`  "
            f"· `event.duration` is in **nanoseconds** (divide by 1,000,000 for ms)"
        )

    st.divider()

    # Sub-tabs: Service Map | SLOs
    sub_tabs = st.tabs([
        f"🗺️ Service Map ({services_count} services)",
        f"📊 SLOs ({slo_count} defined)",
    ])

    with sub_tabs[0]:
        if has_service_map:
            _render_service_map(service_map)

            # Export service map JSON
            st.divider()
            st.download_button(
                "📥 Download Service Map (JSON)",
                data=json.dumps(service_map, indent=2),
                file_name=f"{st.session_state.current_demo_module}_service_map.json",
                mime="application/json",
                use_container_width=True,
            )
        else:
            st.info("No service map was generated for this demo.")

    with sub_tabs[1]:
        if has_slos:
            _render_slo_queries(slo_queries)

            # Export SLO definitions
            st.divider()
            st.download_button(
                "📥 Download SLO Definitions (JSON)",
                data=json.dumps(slo_queries, indent=2),
                file_name=f"{st.session_state.current_demo_module}_slos.json",
                mime="application/json",
                use_container_width=True,
            )
        else:
            st.info("No SLO queries were generated for this demo.")
