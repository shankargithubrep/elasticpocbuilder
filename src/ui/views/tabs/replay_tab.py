"""
Live Replay Tab — streams demo data into Elasticsearch with current timestamps
so Kibana Alerts, Detection Rules, and Cases fire in real time.
"""

import os
import time
import logging
import json
import threading
from pathlib import Path
from typing import Optional

import streamlit as st
import pandas as pd

logger = logging.getLogger(__name__)

# Severity colour map
SEV_COLORS = {
    "low":      ("🟢", "#27ae60"),
    "medium":   ("🟡", "#f39c12"),
    "high":     ("🟠", "#e67e22"),
    "critical": ("🔴", "#e74c3c"),
}

ANOMALY_LABELS = {
    "normal":          "✅ Normal",
    "latency_spike":   "🐢 Latency Spike",
    "error_surge":     "💥 Error Storm",
    "slo_breach":      "📉 SLO Breach",
    "attack":          "🔴 Attack",
    "db_slowdown":     "🐌 DB Slowdown",
    "cascade_failure": "⛓️ Cascade Failure",
}


def _get_kibana_url() -> str:
    url = os.getenv("ELASTICSEARCH_KIBANA_URL", "")
    return url.rstrip("/") if url else ""


def _load_scenarios(module_name: str):
    from src.services.replay_engine import load_scenarios, Scenario
    path = Path("demos") / module_name / "scenarios.json"
    return load_scenarios(path)


def _load_demo_dataframes(module_name: str) -> dict:
    """Load all CSVs from demos/<module>/data/ into DataFrames."""
    data_dir = Path("demos") / module_name / "data"
    dfs = {}
    if data_dir.exists():
        for csv_file in data_dir.glob("*.csv"):
            try:
                dfs[csv_file.stem] = pd.read_csv(csv_file)
            except Exception as e:
                logger.warning(f"Could not load {csv_file}: {e}")
    return dfs


def _get_engine_key(module_name: str) -> str:
    return f"replay_engine_{module_name}"


def _get_engine(module_name: str):
    return st.session_state.get(_get_engine_key(module_name))


def _set_engine(module_name: str, engine):
    st.session_state[_get_engine_key(module_name)] = engine


def render_replay_tab(loader):
    """Render the Live Replay tab."""
    module_name = st.session_state.current_demo_module
    pillar = loader.config.get("pillar", "observability")
    kibana_url = _get_kibana_url()

    st.info(
        "▶ **Live Replay** streams your generated demo data into Elasticsearch with **current timestamps**, "
        "so Kibana Alerts, Detection Rules, and Cases fire in real time during your demo."
    )

    # Load scenarios
    scenarios = _load_scenarios(module_name)

    if not scenarios:
        st.warning(
            "⚠️ No scenarios found for this demo. "
            "Scenarios are generated automatically for new demos. "
            "You can regenerate this demo or create a `scenarios.json` manually."
        )
        _render_generate_scenarios_button(loader, module_name)
        return

    # Layout: controls left, status right
    col_ctrl, col_status = st.columns([3, 2])

    with col_ctrl:
        _render_controls(module_name, scenarios, pillar, kibana_url)

    with col_status:
        _render_status(module_name)

    st.divider()
    _render_scenario_details(scenarios)


# ---------------------------------------------------------------------------
# Controls panel
# ---------------------------------------------------------------------------

def _render_controls(module_name: str, scenarios, pillar: str, kibana_url: str):
    st.markdown("#### ⚙️ Replay Controls")

    engine = _get_engine(module_name)
    state = engine.state if engine else "idle"

    # Scenario selector
    scenario_names = [s.name for s in scenarios]
    selected_name = st.selectbox(
        "Scenario",
        options=scenario_names,
        key=f"replay_scenario_{module_name}",
        help="Choose a scenario to replay. Switch scenarios while running to inject anomalies live.",
    )
    selected_scenario = next((s for s in scenarios if s.name == selected_name), scenarios[0])

    # Speed control
    eps = st.slider(
        "Events per second",
        min_value=1, max_value=50, value=5,
        key=f"replay_eps_{module_name}",
        help="How fast events are streamed into Elasticsearch. Higher = alerts fire faster.",
    )

    # Dataset selector (if multiple)
    dfs = _load_demo_dataframes(module_name)
    if not dfs:
        st.error("No data files found. Index data first via the Data tab.")
        return

    dataset_name = list(dfs.keys())[0]
    if len(dfs) > 1:
        dataset_name = st.selectbox(
            "Dataset to replay",
            options=list(dfs.keys()),
            key=f"replay_dataset_{module_name}",
        )

    df = dfs[dataset_name]
    st.caption(f"Dataset: **{dataset_name}** · {len(df):,} rows · replaying in loop")

    # Index name
    index_name = st.text_input(
        "Target index",
        value=f"{module_name.replace('_', '-')}-live",
        key=f"replay_index_{module_name}",
        help="Elasticsearch index to stream events into. Must match your Kibana alert index pattern.",
    )

    st.divider()

    # Start / Pause / Stop buttons
    btn_col1, btn_col2, btn_col3 = st.columns(3)

    with btn_col1:
        if st.button(
            "▶ Start" if state != "running" else "▶ Running",
            key=f"replay_start_{module_name}",
            type="primary",
            use_container_width=True,
            disabled=(state == "running"),
        ):
            _start_replay(module_name, df, index_name, eps, selected_scenario)
            st.rerun()

    with btn_col2:
        if state == "paused":
            if st.button("▶ Resume", key=f"replay_resume_{module_name}", use_container_width=True):
                engine.resume()
                st.rerun()
        else:
            if st.button(
                "⏸ Pause",
                key=f"replay_pause_{module_name}",
                use_container_width=True,
                disabled=(state != "running"),
            ):
                if engine:
                    engine.pause()
                st.rerun()

    with btn_col3:
        if st.button(
            "⏹ Stop",
            key=f"replay_stop_{module_name}",
            use_container_width=True,
            disabled=(state == "idle"),
        ):
            if engine:
                engine.stop()
                _set_engine(module_name, None)
            st.rerun()

    # Apply scenario change while running
    if state == "running" and engine:
        if st.button(
            f"⚡ Inject: {selected_name}",
            key=f"replay_inject_{module_name}",
            use_container_width=True,
            help="Switch to this scenario immediately while replay is running",
        ):
            engine.set_scenario(selected_scenario if selected_scenario.anomaly_type != "normal" else None)
            st.success(f"Injected: **{selected_name}**")

    # Kibana links
    if kibana_url:
        st.divider()
        st.markdown("**Open in Kibana:**")
        lc1, lc2 = st.columns(2)
        with lc1:
            st.link_button("🔔 Alerts", url=f"{kibana_url}/app/observability/alerts",
                           use_container_width=True)
        with lc2:
            st.link_button("📋 Cases", url=f"{kibana_url}/app/cases",
                           use_container_width=True)
        lc3, lc4 = st.columns(2)
        with lc3:
            st.link_button("🛡️ Detection Rules", url=f"{kibana_url}/app/security/rules",
                           use_container_width=True)
        with lc4:
            st.link_button("🔍 Discover", url=f"{kibana_url}/app/discover",
                           use_container_width=True)


# ---------------------------------------------------------------------------
# Status panel
# ---------------------------------------------------------------------------

def _render_status(module_name: str):
    st.markdown("#### 📊 Live Status")

    engine = _get_engine(module_name)
    if not engine or engine.state == "idle":
        st.markdown(
            "<div style='text-align:center;padding:40px;color:#888;border:1px dashed #444;border-radius:8px'>"
            "⏸ Not running<br><small>Press Start to begin streaming</small></div>",
            unsafe_allow_html=True,
        )
        return

    state = engine.state
    stats = engine.stats

    # State badge
    state_colors = {"running": "#27ae60", "paused": "#f39c12", "stopped": "#e74c3c"}
    state_icons  = {"running": "●", "paused": "⏸", "stopped": "⏹"}
    color = state_colors.get(state, "#888")
    icon  = state_icons.get(state, "?")

    st.markdown(
        f"<div style='text-align:center;padding:8px;background:{color}22;"
        f"border:1px solid {color};border-radius:6px;margin-bottom:12px'>"
        f"<span style='color:{color};font-size:1.2rem;font-weight:bold'>"
        f"{icon} {state.upper()}</span></div>",
        unsafe_allow_html=True,
    )

    # Metrics
    m1, m2 = st.columns(2)
    with m1:
        st.metric("Events Indexed", f"{stats['total_indexed']:,}")
    with m2:
        st.metric("Events/sec", stats.get("events_per_second", 0))

    m3, m4 = st.columns(2)
    with m3:
        elapsed = int(time.time() - (
            time.mktime(time.strptime(stats["start_time"][:19], "%Y-%m-%dT%H:%M:%S"))
            if stats.get("start_time") else time.time()
        ))
        mins, secs = divmod(elapsed, 60)
        st.metric("Elapsed", f"{mins:02d}:{secs:02d}")
    with m4:
        st.metric("Errors", stats.get("total_errors", 0))

    # Active scenario
    current_sc = stats.get("current_scenario")
    if current_sc:
        st.caption(f"**Active scenario:** {current_sc}")

    # Auto-refresh while running
    if state == "running":
        st.caption("🔄 Auto-refreshing every 3s")
        time.sleep(3)
        st.rerun()


# ---------------------------------------------------------------------------
# Scenario detail cards
# ---------------------------------------------------------------------------

def _render_scenario_details(scenarios):
    st.markdown("#### 📋 Available Scenarios")
    st.caption("Each scenario injects specific field overrides to trigger corresponding Kibana alerts.")

    for sc in scenarios:
        sev = sc.severity
        emoji, color = SEV_COLORS.get(sev, ("⚪", "#888"))
        atype_label = ANOMALY_LABELS.get(sc.anomaly_type, sc.anomaly_type)

        with st.expander(
            f"{emoji} {sc.name}  ·  {atype_label}  ·  {sc.duration_seconds}s",
            expanded=(sc.anomaly_type == "normal"),
        ):
            st.markdown(sc.description)

            dc1, dc2, dc3 = st.columns(3)
            with dc1:
                st.metric("Trigger after", f"{sc.trigger_after_seconds}s")
            with dc2:
                st.metric("Duration", f"{sc.duration_seconds}s")
            with dc3:
                st.metric("Severity", sev.upper())

            if sc.affected_service and sc.affected_service != "all":
                st.caption(f"**Affected service:** `{sc.affected_service}`")

            if sc.field_overrides:
                st.markdown("**Field overrides injected during anomaly:**")
                st.code(json.dumps(sc.field_overrides, indent=2), language="json")

            if sc.expected_alerts:
                st.markdown("**Expected Kibana alerts:**")
                for alert in sc.expected_alerts:
                    st.markdown(f"  🔔 {alert}")


# ---------------------------------------------------------------------------
# Engine lifecycle
# ---------------------------------------------------------------------------

def _start_replay(module_name: str, df: pd.DataFrame, index_name: str,
                  eps: int, scenario):
    """Create and start a ReplayEngine, storing it in session state."""
    from src.services.replay_engine import ReplayEngine
    from src.services.elasticsearch_indexer import ElasticsearchIndexer

    try:
        indexer = ElasticsearchIndexer()
    except Exception as e:
        st.error(f"❌ Cannot connect to Elasticsearch: {e}")
        return

    engine = ReplayEngine(
        df=df,
        index_name=index_name,
        indexer=indexer,
        events_per_second=eps,
        window_seconds=30,
    )

    # Set initial scenario
    if scenario and scenario.anomaly_type != "normal":
        engine.set_scenario(scenario)

    engine.start()
    _set_engine(module_name, engine)
    logger.info(f"Replay started for {module_name} → {index_name}")


# ---------------------------------------------------------------------------
# Generate scenarios button (for demos without scenarios.json)
# ---------------------------------------------------------------------------

def _render_generate_scenarios_button(loader, module_name: str):
    st.divider()
    st.markdown("#### Generate Scenarios")
    st.markdown(
        "Click below to generate replay scenarios for this demo using AI. "
        "This reads your demo's data fields and creates realistic anomaly scenarios."
    )

    if st.button("🤖 Generate Scenarios", type="primary", key=f"gen_scenarios_{module_name}"):
        with st.spinner("Generating scenarios..."):
            try:
                from src.services.scenario_generator import ScenarioGenerator
                from src.services.llm_proxy_service import UnifiedLLMClient

                config = {**loader.config.get("customer_context", {}), **loader.config}
                strategy = {}
                strategy_path = Path("demos") / module_name / "query_strategy.json"
                if strategy_path.exists():
                    import json as _json
                    strategy = _json.loads(strategy_path.read_text())

                config["datasets"] = strategy.get("datasets", [])

                gen = ScenarioGenerator(UnifiedLLMClient())
                scenarios = gen.generate(config)

                out_path = Path("demos") / module_name / "scenarios.json"
                import json as _json
                out_path.write_text(_json.dumps(scenarios, indent=2))

                st.success(f"✅ Generated {len(scenarios)} scenarios — reload the tab to see them.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Scenario generation failed: {e}")
