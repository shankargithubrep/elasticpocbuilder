"""
Search Stack Tab

Renders the full Elastic Search stack provisioning UI for Search demos.
Three sub-tabs:
  1. Infrastructure — asset manifest, health check, re-provision, teardown
  2. Monitoring — embedded Kibana dashboard + alert rule status
  3. Search Preview — live in-app search widget against the Search Application
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

import streamlit as st

logger = logging.getLogger(__name__)

KIBANA_URL = os.getenv("ELASTICSEARCH_KIBANA_URL", "").rstrip("/")
SPACE_ID = os.getenv("KIBANA_SPACE_ID", "default")


def render_search_stack_tab(loader) -> None:
    """Main entry point — renders the Search Stack tab."""
    module_path = loader.module_path if hasattr(loader, "module_path") else str(loader)
    assets = _load_assets(module_path)

    st.markdown("### 🔍 Search Stack")
    st.caption(
        "Auto-provisioned Elastic assets: index templates, ELSER pipeline, "
        "Search Application, Kibana dashboards, alerting rules, and Slack connector."
    )

    if not assets:
        _render_not_provisioned(module_path, loader)
        return

    sub_tabs = st.tabs(["🏗️ Infrastructure", "📊 Monitoring", "🔎 Search Preview"])

    with sub_tabs[0]:
        _render_infrastructure(module_path, assets, loader)

    with sub_tabs[1]:
        _render_monitoring(assets)

    with sub_tabs[2]:
        _render_search_preview(assets)


# =============================================================================
# Infrastructure sub-tab
# =============================================================================

def _render_infrastructure(module_path: str, assets: Dict, loader) -> None:
    provisioned_at = assets.get("provisioned_at", "unknown")
    errors = assets.get("provisioning_errors", [])

    # Overall status banner
    if errors:
        st.warning(f"⚠️ Provisioned with **{len(errors)} warning(s)** — {provisioned_at}")
        with st.expander("View provisioning warnings"):
            for e in errors:
                st.code(e)
    else:
        st.success(f"✅ Fully provisioned — {provisioned_at}")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Run Health Check", use_container_width=True):
            _run_health_check(module_path)

    with col2:
        if st.button("🔧 Re-provision", use_container_width=True):
            _reprovision(module_path, loader)

    # Health check results (if available)
    health = assets.get("health_check", {})
    if health and health.get("items"):
        st.markdown("#### Pre-Demo Checklist")
        overall = health.get("overall", "unknown")
        icons = {"ok": "✅", "warning": "⚠️", "error": "❌"}
        st.markdown(f"**Overall: {icons.get(overall, '❓')} {overall.upper()}** — checked at {health.get('checked_at', '')}")
        for item in health["items"]:
            icon = icons.get(item["status"], "❓")
            detail = f" — *{item['detail']}*" if item.get("detail") else ""
            st.markdown(f"{icon} **{item['name']}**: {item['message']}{detail}")

    st.divider()

    # Asset cards
    st.markdown("#### Provisioned Assets")
    _render_asset_cards(assets)

    st.divider()

    # Teardown
    with st.expander("🗑️ Teardown (remove all provisioned assets)"):
        st.warning(
            "This will delete the ELSER pipeline, index templates, Search Application, "
            "Kibana dashboards, alerting rules, and the scoped API key. "
            "**Indexed data is not deleted.**"
        )
        if st.button("⚠️ Teardown All Assets", type="secondary"):
            _teardown(module_path)


def _render_asset_cards(assets: Dict) -> None:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Elasticsearch**")
        indices = assets.get("indices", [])
        st.metric("Indices", len(indices))
        for idx in indices:
            st.code(idx)

        if pipeline := assets.get("ingest_pipeline"):
            st.markdown(f"**Ingest Pipeline**")
            st.code(pipeline)

        if ilm := assets.get("ilm_policy"):
            st.markdown(f"**ILM Policy**")
            st.code(ilm)

        if template := assets.get("index_template"):
            st.markdown(f"**Index Template**")
            st.code(template)

        if app := assets.get("search_application"):
            st.markdown(f"**Search Application**")
            st.code(app)
            if KIBANA_URL:
                st.markdown(
                    f"[Open in Kibana]({KIBANA_URL}/app/enterprise_search/applications/{app})"
                )

        if synonyms := assets.get("synonyms_id"):
            st.markdown(f"**Synonyms Set**")
            st.code(synonyms)

    with col2:
        st.markdown("**Kibana**")

        dashboards = assets.get("kibana_dashboard_ids", [])
        st.metric("Dashboards", len(dashboards))
        for did in dashboards:
            base = f"{KIBANA_URL}/app/dashboards#/view/{did}" if KIBANA_URL else "#"
            st.markdown(f"[Open Dashboard →]({base})")

        rules = assets.get("alerting_rule_ids", [])
        st.metric("Alert Rules", len(rules))
        if rules and KIBANA_URL:
            st.markdown(f"[View in Alerts →]({KIBANA_URL}/app/observability/alerts)")

        if assets.get("slack_connector_id"):
            st.markdown("**Slack Connector** ✅")
        if assets.get("case_connector_configured"):
            st.markdown("**Case Management** ✅")

        views = assets.get("discover_view_ids", [])
        if views and KIBANA_URL:
            st.markdown(f"**Discover Views** ({len(views)})")
            for vid in views:
                st.markdown(f"[Open in Discover →]({KIBANA_URL}/app/discover#/view/{vid})")

        key_info = assets.get("scoped_api_key")
        if key_info and isinstance(key_info, dict):
            st.markdown("**Scoped API Key (read-only)**")
            st.code(key_info.get("encoded", "hidden"), language=None)
            st.caption("30-day expiry — share with customer for their own testing")


# =============================================================================
# Monitoring sub-tab
# =============================================================================

def _render_monitoring(assets: Dict) -> None:
    dashboard_ids = assets.get("kibana_dashboard_ids", [])

    if dashboard_ids and KIBANA_URL:
        st.markdown("#### 📊 Kibana Dashboard")
        st.caption("P50 / P95 / P99 latency · Query volume · Top terms · Error rate")

        dash_id = dashboard_ids[0]
        dash_url = f"{KIBANA_URL}/app/dashboards#/view/{dash_id}?embed=true&_g=(refreshInterval:(pause:!f,value:30000),time:(from:now-7d,to:now))"

        st.components.v1.iframe(dash_url, height=700, scrolling=True)
        st.markdown(f"[Open in full Kibana →]({KIBANA_URL}/app/dashboards#/view/{dash_id})")
    else:
        st.info("Dashboard not provisioned yet — run provisioning first or check Kibana URL in .env")

    st.divider()

    # Alert rules summary
    rule_ids = assets.get("alerting_rule_ids", [])
    if rule_ids:
        st.markdown("#### 🔔 Alert Rules")
        st.markdown(f"{len(rule_ids)} rule(s) configured:")
        for i, rule_id in enumerate(rule_ids):
            label = "P95 Latency Rule" if i == 0 else "Error Rate Rule"
            if KIBANA_URL:
                st.markdown(f"- [{label}]({KIBANA_URL}/app/observability/alerts) `{rule_id}`")
            else:
                st.code(rule_id)

    # Slack
    if assets.get("slack_connector_id"):
        st.markdown("#### 💬 Slack Alerts")
        st.success("Slack connector active — alerts fire to your configured channel")
    else:
        st.info("Slack not configured — add SLACK_WEBHOOK_URL to .env to enable Slack alerts")


# =============================================================================
# Search Preview sub-tab
# =============================================================================

def _render_search_preview(assets: Dict) -> None:
    app_name = assets.get("search_application")
    key_info = assets.get("scoped_api_key")
    indices = assets.get("indices", [])

    st.markdown("#### 🔎 Live Search Preview")
    st.caption(
        "Test your Search Application live — uses ELSER semantic search + RRF hybrid ranking. "
        "Results come directly from Elasticsearch."
    )

    if not app_name:
        st.info("Search Application not provisioned. Run provisioning to enable live search.")
        return

    # Search input
    query = st.text_input(
        "Search query",
        placeholder="e.g. 'claims denied for diabetes', 'refund policy'",
        key="search_preview_query",
    )
    col1, col2 = st.columns([1, 3])
    with col1:
        result_size = st.selectbox("Results", [5, 10, 20], index=1, key="search_preview_size")
    with col2:
        use_semantic = st.toggle("Semantic (ELSER)", value=True, key="search_preview_semantic")

    if st.button("🔍 Search", type="primary", use_container_width=False):
        _run_search_preview(
            app_name=app_name,
            query=query,
            size=result_size,
            use_semantic=use_semantic,
            key_info=key_info,
            indices=indices,
        )

    # Hybrid weight tuner
    with st.expander("⚖️ Hybrid Search Weight Tuning"):
        st.caption("Adjust balance between BM25 (keyword) and ELSER (semantic) search")
        col_bm25, col_sem = st.columns(2)
        with col_bm25:
            bm25_boost = st.slider("BM25 boost", 0.1, 3.0, 1.0, 0.1, key="bm25_boost")
        with col_sem:
            sem_boost = st.slider("Semantic boost", 0.1, 3.0, 1.0, 0.1, key="sem_boost")
        rrf_k = st.slider("RRF rank constant", 10, 200, 60, 10, key="rrf_k")

        if st.button("Apply Weights", key="apply_weights"):
            _update_hybrid_weights(assets, bm25_boost, sem_boost, rrf_k)


def _run_search_preview(
    app_name: str,
    query: str,
    size: int,
    use_semantic: bool,
    key_info: Optional[Dict],
    indices: list,
) -> None:
    if not query.strip():
        st.warning("Enter a search query")
        return

    try:
        from elasticsearch import Elasticsearch
        api_key = (key_info or {}).get("encoded") or os.getenv("ELASTICSEARCH_API_KEY", "")
        cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
        if cloud_id:
            es = Elasticsearch(cloud_id=cloud_id, api_key=api_key)
        else:
            es = Elasticsearch(os.getenv("ELASTIC_ENDPOINT", ""), api_key=api_key)

        if use_semantic:
            # Use the Search Application endpoint
            resp = es.search_application.search(
                name=app_name,
                body={"params": {"query": query, "size": size}},
            )
        else:
            # Fall back to plain multi-match BM25
            resp = es.search(
                index=",".join(indices) if indices else "_all",
                body={
                    "query": {"multi_match": {"query": query, "fields": ["*"]}},
                    "size": size,
                },
            )

        hits = resp.get("hits", {})
        total = hits.get("total", {}).get("value", 0)
        took_ms = resp.get("took", 0)

        st.markdown(f"**{total:,} results** in {took_ms}ms")

        for hit in hits.get("hits", []):
            score = round(hit.get("_score", 0) or 0, 3)
            source = hit.get("_source", {})
            index = hit.get("_index", "")

            with st.expander(f"Score: {score} — `{index}`", expanded=False):
                # Show up to 5 fields
                display = {k: v for k, v in list(source.items())[:10] if not k.startswith("ml.")}
                st.json(display)

    except Exception as e:
        st.error(f"Search failed: {e}")


def _update_hybrid_weights(assets: Dict, bm25: float, semantic: float, rrf_k: int) -> None:
    try:
        from src.services.search_application_service import SearchApplicationService
        from elasticsearch import Elasticsearch
        api_key = os.getenv("ELASTICSEARCH_API_KEY", "")
        cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
        es = Elasticsearch(cloud_id=cloud_id, api_key=api_key) if cloud_id else Elasticsearch(
            os.getenv("ELASTIC_ENDPOINT", ""), api_key=api_key
        )
        svc = SearchApplicationService(es)
        demo_slug = assets.get("demo_name", "")
        svc.update_hybrid_weights(
            demo_slug=demo_slug,
            index_names=assets.get("indices", []),
            semantic_fields=[],
            text_fields=[],
            bm25_boost=bm25,
            semantic_boost=semantic,
            rrf_rank_constant=rrf_k,
        )
        st.success(f"Updated weights: BM25={bm25} · Semantic={semantic} · RRF k={rrf_k}")
    except Exception as e:
        st.error(f"Failed to update weights: {e}")


# =============================================================================
# Actions
# =============================================================================

def _run_health_check(module_path: str) -> None:
    with st.spinner("Running health check..."):
        try:
            from src.services.search_health_check import SearchHealthCheckService
            svc = SearchHealthCheckService()
            report = svc.run(module_path)
            icons = {"ok": "✅", "warning": "⚠️", "error": "❌"}
            overall_icon = icons.get(report.overall, "❓")
            st.success(f"{overall_icon} Health check complete — overall: **{report.overall.upper()}**")
            st.rerun()
        except Exception as e:
            st.error(f"Health check failed: {e}")


def _reprovision(module_path: str, loader) -> None:
    with st.spinner("Re-provisioning Search stack..."):
        try:
            from src.services.search_provisioner import SearchProvisioner
            config_path = Path(module_path) / "config.json"
            query_strategy_path = Path(module_path) / "query_strategy.json"

            query_strategy = {}
            if query_strategy_path.exists():
                query_strategy = json.loads(query_strategy_path.read_text())

            demo_slug = Path(module_path).name
            provisioner = SearchProvisioner()
            provisioner.provision_all(
                demo_slug=demo_slug,
                query_strategy=query_strategy,
                datasets={},
                module_path=module_path,
            )
            st.success("Re-provisioning complete!")
            st.rerun()
        except Exception as e:
            st.error(f"Re-provisioning failed: {e}")


def _teardown(module_path: str) -> None:
    with st.spinner("Tearing down assets..."):
        try:
            from src.services.search_provisioner import SearchProvisioner
            provisioner = SearchProvisioner()
            provisioner.teardown_all(module_path)
            st.success("All assets removed. Reload the page to see updated state.")
            st.rerun()
        except Exception as e:
            st.error(f"Teardown failed: {e}")


# =============================================================================
# Not-provisioned state
# =============================================================================

def _render_not_provisioned(module_path: str, loader) -> None:
    st.info(
        "This demo has not been provisioned yet. "
        "Provisioning creates the full Elastic Search stack: "
        "ELSER pipeline, index templates, Search Application, "
        "Kibana dashboards, alerting rules, and Slack connector."
    )
    if st.button("🚀 Provision Now", type="primary"):
        _reprovision(module_path, loader)


# =============================================================================
# Helpers
# =============================================================================

def _load_assets(module_path: str) -> Optional[Dict]:
    path = Path(module_path) / "elastic_assets.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return None
