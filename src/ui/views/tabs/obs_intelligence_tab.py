"""
Reliability Engine™ — Observability Intelligence Tab

Multi-tenant, multi-region in-app observability experience.
No Kibana required for the demo.

7 Panels:
  1. 🏥 Service Health      — live health scores per service, active alerts
  2. 📈 APM Analytics       — latency P50/P95/P99, throughput, error rate trends
  3. 📋 Log Intelligence     — error patterns, Claude-powered root cause
  4. 🚨 Incident Triage      — alert → correlated signals → timeline → fix
  5. 🔗 Distributed Tracing  — service dep map, critical path, span waterfall
  6. 📊 SLO Dashboard        — error budget, burn rate, SLO compliance
  7. 🤖 Anomaly Detection    — ML anomaly scores, contributing factors
"""

import streamlit as st
from typing import Any, Dict, Optional


# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """
<style>
.re-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: white; border-radius: 10px; padding: 20px 24px; margin-bottom: 16px;
}
.re-header h2 { margin: 0; font-size: 1.5rem; }
.re-header p  { margin: 4px 0 0; opacity: .8; font-size: .85rem; }
.health-card {
    border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;
    border-left: 4px solid #ccc; background: #f8f9fa;
}
.health-card.critical { border-left-color: #dc3545; background: #fff5f5; }
.health-card.degraded  { border-left-color: #fd7e14; background: #fff8f0; }
.health-card.healthy   { border-left-color: #28a745; background: #f0fff4; }
.kpi-tile {
    text-align: center; padding: 16px 8px; border-radius: 8px;
    background: #f8f9fa; border: 1px solid #dee2e6;
}
.kpi-tile .value { font-size: 1.8rem; font-weight: 700; }
.kpi-tile .label { font-size: .75rem; color: #666; margin-top: 2px; }
.slo-row { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.slo-bar-bg { background: #e9ecef; border-radius: 4px; height: 8px; flex: 1; }
.slo-bar-fill { border-radius: 4px; height: 8px; }
.alert-card {
    border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;
    border-left: 4px solid #dc3545; background: #fff5f5;
}
.alert-card.high   { border-left-color: #fd7e14; background: #fff8f0; }
.alert-card.medium { border-left-color: #ffc107; background: #fffdf0; }
.timeline-event { display: flex; gap: 12px; margin-bottom: 8px; align-items: flex-start; }
.timeline-dot { width: 10px; height: 10px; border-radius: 50%; margin-top: 4px; flex-shrink: 0; }
.anomaly-bar { border-radius: 4px; height: 10px; margin-top: 4px; }
</style>
"""


# ── Tenant / Region selectors ─────────────────────────────────────────────────

_DEMO_TENANTS = [
    "genesys-us",
    "genesys-eu",
    "genesys-apac",
    "acme-corp",
    "demo-tenant",
]

_DEMO_REGIONS = [
    "us-east-1",
    "eu-west-1",
    "ap-southeast-1",
]


def _tenant_region_bar(key_prefix: str = "obs") -> tuple:
    """Render tenant + region selectors. Returns (tenant_id, region)."""
    col1, col2, col3 = st.columns([2, 2, 4])
    with col1:
        tenant = st.selectbox(
            "Tenant",
            options=_DEMO_TENANTS,
            key=f"{key_prefix}_tenant",
            help="Filter all observability data to this tenant",
        )
    with col2:
        region = st.selectbox(
            "Region",
            options=_DEMO_REGIONS,
            key=f"{key_prefix}_region",
            help="Select regional Elastic cluster (data stays in region)",
        )
    with col3:
        st.caption(
            f"📍 Querying **{region}** cluster · tenant filter: `tenant_id == \"{tenant}\"`  \n"
            "All ES|QL queries are scoped to this tenant + region — data never crosses region boundaries."
        )
    return tenant, region


def _esql_expander(label: str, query: str):
    with st.expander(f"🔍 Under the Hood — {label}", expanded=False):
        st.code(query, language="sql")


# ── Panel 1: Service Health ───────────────────────────────────────────────────

def _render_service_health(svc: Any, tenant: str, region: str):
    st.markdown("## 🏥 Service Health")
    st.caption(f"Real-time health for all services · tenant `{tenant}` · region `{region}`")

    data = svc.get_service_health()
    alerts = svc.get_active_alerts()

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-tile"><div class="value">{data["healthy_pct"]}%</div>'
                    f'<div class="label">Services Healthy</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-tile"><div class="value" style="color:#dc3545">'
                    f'{data["active_alerts"]}</div><div class="label">Active Alerts</div></div>',
                    unsafe_allow_html=True)
    with k3:
        critical = alerts["critical_count"]
        st.markdown(f'<div class="kpi-tile"><div class="value" style="color:#dc3545">'
                    f'{critical}</div><div class="label">Critical Alerts</div></div>',
                    unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-tile"><div class="value">{len(data["services"])}</div>'
                    f'<div class="label">Total Services</div></div>', unsafe_allow_html=True)

    st.markdown("")

    # Active alerts strip
    if alerts["alerts"]:
        st.markdown("**🚨 Active Alerts**")
        for a in alerts["alerts"][:3]:
            sev_class = "" if a["severity"] == "critical" else a["severity"]
            st.markdown(
                f'<div class="alert-card {sev_class}">'
                f'{a["icon"]} <strong>{a["name"]}</strong> · {a["service"]} · '
                f'fired {a["fired_at"]} ({a["duration"]}) · '
                f'<em>{a.get("affected_tenants", 1)} tenant(s) affected</em></div>',
                unsafe_allow_html=True,
            )
        st.markdown("")

    # Services table
    st.markdown("**📋 Service Inventory**")
    col_h, col_e, col_p, col_t, col_s = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    col_h.markdown("**Service**")
    col_e.markdown("**Error Rate**")
    col_p.markdown("**P95 (ms)**")
    col_t.markdown("**TPS**")
    col_s.markdown("**Status**")
    st.divider()
    for s in data["services"]:
        c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])
        c1.markdown(f"`{s['name']}`  \n<small>{s['team']} · {s['language']}</small>",
                    unsafe_allow_html=True)
        c2.markdown(f"{s['error_rate']}%")
        c3.markdown(f"{s['p95_ms']}")
        c4.markdown(f"{s['throughput']:,}")
        c5.markdown(f"{s['health_icon']} {s['health'].capitalize()}")

    _esql_expander("Service Health", data["esql"])


# ── Panel 2: APM Analytics ────────────────────────────────────────────────────

def _render_apm_analytics(svc: Any, tenant: str, region: str):
    st.markdown("## 📈 APM Analytics")
    st.caption("Latency · Throughput · Error Rate across services and time")

    service_names = ["all"] + [s["name"] for s in svc.get_service_health()["services"]]
    sel_service = st.selectbox("Filter by service", service_names, key="obs_apm_service")
    sel_window  = st.select_slider("Time window", ["15m", "1h", "6h", "24h"], value="1h",
                                   key="obs_apm_window")

    data = svc.get_apm_analytics(
        service=None if sel_service == "all" else sel_service,
        window=sel_window,
    )
    s = data["summary"]

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-tile"><div class="value">{s["avg_p95"]}ms</div>'
                    f'<div class="label">Avg P95 Latency</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-tile"><div class="value" style="color:#fd7e14">'
                    f'{s["max_p95"]}ms</div><div class="label">Peak P95</div></div>',
                    unsafe_allow_html=True)
    with k3:
        color = "#dc3545" if s["avg_err"] > 1 else "#28a745"
        st.markdown(f'<div class="kpi-tile"><div class="value" style="color:{color}">'
                    f'{s["avg_err"]}%</div><div class="label">Avg Error Rate</div></div>',
                    unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-tile"><div class="value">{s["peak_tps"]:,}</div>'
                    f'<div class="label">Peak TPS</div></div>', unsafe_allow_html=True)

    st.markdown("")

    # Latency table
    st.markdown("**⏱️ Latency Breakdown (last 24h)**")
    cols = st.columns([2, 1.5, 1.5, 1.5, 1.5, 1.5])
    for h, c in zip(["Time", "P50", "P95", "P99", "Error %", "TPS"], cols):
        c.markdown(f"**{h}**")
    st.divider()
    for b in data["buckets"][-12:]:
        c = st.columns([2, 1.5, 1.5, 1.5, 1.5, 1.5])
        c[0].markdown(b["timestamp"])
        c[1].markdown(f"{b['p50_ms']}ms")
        spike = b["p95_ms"] > 500
        c[2].markdown(f"{'🔴 ' if spike else ''}{b['p95_ms']}ms")
        c[3].markdown(f"{b['p99_ms']}ms")
        err_color = "🔴" if b["error_rate"] > 2 else "🟡" if b["error_rate"] > 0.5 else "🟢"
        c[4].markdown(f"{err_color} {b['error_rate']}%")
        c[5].markdown(f"{b['throughput']:,}")

    _esql_expander("APM Analytics", data["esql"])


# ── Panel 3: Log Intelligence ─────────────────────────────────────────────────

def _render_log_intelligence(svc: Any, tenant: str, region: str):
    st.markdown("## 📋 Log Intelligence")
    st.caption("Error pattern analysis + Claude-powered root cause for this tenant")

    data = svc.get_log_intelligence()

    # Claude insight card
    st.info(f"🤖 **AI Root Cause Analysis**\n\n{data['claude_insight']}")

    k1, k2 = st.columns(2)
    with k1:
        st.metric("Total Errors (1h)", f"{data['total_errors']:,}")
    with k2:
        st.metric("Top Error Service", data["top_service"])

    st.markdown("")
    st.markdown("**🔁 Top Error Patterns**")

    head = st.columns([4, 1.5, 1, 2])
    for h, c in zip(["Pattern", "Count", "Trend", "Service"], head):
        c.markdown(f"**{h}**")
    st.divider()
    for p in data["patterns"]:
        cols = st.columns([4, 1.5, 1, 2])
        cols[0].markdown(f"`{p['pattern'][:60]}`")
        cols[1].markdown(f"{p['count']:,}")
        trend_color = "🔴" if p["trend"] == "↑" else "🟢" if p["trend"] == "↓" else "🟡"
        cols[2].markdown(f"{trend_color} {p['trend']}")
        cols[3].markdown(f"`{p['service']}`")

    _esql_expander("Log Intelligence", data["esql"])


# ── Panel 4: Incident Triage ──────────────────────────────────────────────────

def _render_incident_triage(svc: Any, tenant: str, region: str):
    st.markdown("## 🚨 Incident Triage")
    st.caption("Alert → correlated signals → timeline → root cause → fix")

    alerts = svc.get_active_alerts()

    if not alerts["alerts"]:
        st.success("✅ No active incidents for this tenant and region.")
        return

    alert_names = [a["name"] for a in alerts["alerts"]]
    selected = st.selectbox("Select alert to investigate", alert_names, key="obs_triage_alert")

    incident = svc.get_incident_timeline(selected)

    # Root cause box
    st.error(f"🔍 **Root Cause** (AI-powered)\n\n{incident['root_cause']}")

    # Timeline
    st.markdown("**📅 Incident Timeline**")
    event_colors = {
        "deploy":   "#0d6efd",
        "metric":   "#fd7e14",
        "alert":    "#dc3545",
        "error":    "#6f42c1",
        "current":  "#198754",
    }
    for ev in incident["timeline"]:
        color = event_colors.get(ev["type"], "#aaa")
        icon  = {"deploy": "🚀", "metric": "📈", "alert": "🔔",
                 "error": "❌", "current": "📍"}.get(ev["type"], "•")
        st.markdown(
            f'<div class="timeline-event">'
            f'<div class="timeline-dot" style="background:{color}"></div>'
            f'<div><code>{ev["time"]}</code> {icon} {ev["event"]}</div></div>',
            unsafe_allow_html=True,
        )

    # Recommended actions
    st.markdown("")
    st.markdown("**⚡ Recommended Actions** *(ACT — requires approval + audit trail)*")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("↩ Rollback Deploy", use_container_width=True, key="obs_rollback"):
            st.warning("⚠️ Action requires allowlist approval. Open ticket to trigger via MCP.")
    with col2:
        if st.button("🎫 Create Incident", use_container_width=True, key="obs_ticket"):
            st.success("✅ Incident #INC-4821 created and linked to this alert.")
    with col3:
        if st.button("📟 Page On-Call", use_container_width=True, key="obs_page"):
            st.warning("⚠️ PagerDuty page requires ACT permission. Submit for approval.")

    _esql_expander("Incident Correlation", incident["esql"])


# ── Panel 5: Distributed Tracing ─────────────────────────────────────────────

def _render_distributed_tracing(svc: Any, tenant: str, region: str):
    st.markdown("## 🔗 Distributed Tracing")
    st.caption("Service dependencies · Critical path · Span waterfall")

    data = svc.get_trace_summary()

    # Critical path waterfall
    st.markdown("**🛤️ Critical Path — Slowest Trace**")
    max_ms = max(s["duration_ms"] for s in data["critical_path"])
    for span in data["critical_path"]:
        pct = span["duration_ms"] / max_ms
        color = "#dc3545" if span["status"] == "slow" else "#0d6efd"
        label_icon = "🐌" if span["status"] == "slow" else "✅"
        st.markdown(f"`{span['span']}` — **{span['duration_ms']}ms** {label_icon}")
        st.markdown(
            f'<div style="background:#e9ecef;border-radius:4px;height:10px;margin-bottom:8px">'
            f'<div style="background:{color};width:{pct*100:.0f}%;height:10px;border-radius:4px"></div></div>',
            unsafe_allow_html=True,
        )

    st.metric("Total Trace Duration", f"{data['total_span_ms']}ms")
    st.markdown("")

    # Service dependency table
    st.markdown("**🗺️ Service Dependency Map**")
    cols = st.columns([2.5, 2.5, 1.5, 1.5])
    for h, c in zip(["From", "To", "P95 (ms)", "Error %"], cols):
        c.markdown(f"**{h}**")
    st.divider()
    for dep in data["dependencies"]:
        c = st.columns([2.5, 2.5, 1.5, 1.5])
        c[0].markdown(f"`{dep['from']}`")
        c[1].markdown(f"`{dep['to']}`")
        slow = dep["p95_ms"] > 300
        c[2].markdown(f"{'🔴 ' if slow else ''}{dep['p95_ms']}ms")
        err_icon = "🔴" if dep["err"] > 2 else "🟡" if dep["err"] > 0.5 else "🟢"
        c[3].markdown(f"{err_icon} {dep['err']}%")

    _esql_expander("Distributed Tracing", data["esql"])


# ── Panel 6: SLO Dashboard ────────────────────────────────────────────────────

def _render_slo_dashboard(svc: Any, tenant: str, region: str):
    st.markdown("## 📊 SLO Dashboard")
    st.caption(f"Error budget · Burn rate · Compliance for tenant `{tenant}`")

    data = svc.get_slo_dashboard()

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown(f'<div class="kpi-tile"><div class="value" style="color:#28a745">'
                    f'{data["healthy_count"]}</div><div class="label">Healthy SLOs</div></div>',
                    unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-tile"><div class="value" style="color:#fd7e14">'
                    f'{data["at_risk_count"]}</div><div class="label">At Risk</div></div>',
                    unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-tile"><div class="value" style="color:#dc3545">'
                    f'{data["breached_count"]}</div><div class="label">Breached</div></div>',
                    unsafe_allow_html=True)

    st.markdown("")

    for slo in data["slos"]:
        budget_pct = min(100, max(0, slo["budget_remaining"]))
        bar_color  = "#dc3545" if slo["status"] == "breached" else \
                     "#fd7e14" if slo["status"] == "at_risk" else "#28a745"
        burn_icon  = "🔥" if slo["burn_rate"] > 2 else ""

        with st.container(border=True):
            h1, h2 = st.columns([3, 1])
            with h1:
                st.markdown(f"{slo['status_icon']} **{slo['name']}** — `{slo['service']}`")
            with h2:
                st.markdown(f"Target: **{slo['target']}%** · Window: {slo['window']}")

            m1, m2, m3 = st.columns(3)
            m1.metric("Current SLI", f"{slo['current']}%",
                      delta=f"{round(slo['current']-slo['target'],3)}%")
            m2.metric("Error Budget", f"{budget_pct:.1f}% remaining")
            m3.metric("Burn Rate (1h)", f"{slo['burn_rate']}x {burn_icon}")

            st.markdown(
                f'<div style="background:#e9ecef;border-radius:4px;height:8px;">'
                f'<div style="background:{bar_color};width:{budget_pct:.0f}%;height:8px;border-radius:4px"></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    _esql_expander("SLO Dashboard", data["esql"])


# ── Panel 7: Anomaly Detection ────────────────────────────────────────────────

def _render_anomaly_detection(svc: Any, tenant: str, region: str):
    st.markdown("## 🤖 ML Anomaly Detection")
    st.caption("Proactive issue discovery — finds problems before users report them")

    data = svc.get_anomalies()

    st.info(
        f"**{data['high_confidence']} high-confidence anomaly(ies)** detected in the last 24h "
        f"for tenant `{tenant}` in `{region}`. "
        "ML models baseline normal behaviour per service per tenant."
    )

    for a in data["anomalies"]:
        score_pct = int(a["score"] * 100)
        color = "#dc3545" if score_pct > 85 else "#fd7e14" if score_pct > 70 else "#ffc107"
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1:
                st.markdown(f"**{a['service']}** — `{a['metric']}`")
                st.caption(f"Started: {a['started']}")
            with c2:
                st.markdown(f"**Anomaly Score: {score_pct}%**")
                st.markdown(
                    f'<div style="background:#e9ecef;border-radius:4px;height:10px;">'
                    f'<div style="background:{color};width:{score_pct}%;height:10px;border-radius:4px"></div></div>',
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(f"**Delta:** {a['delta']}")
                if st.button("Investigate", key=f"obs_anomaly_{a['service']}_{a['metric']}",
                             use_container_width=True):
                    st.session_state["obs_triage_panel"] = True
                    st.info("Switch to **Incident Triage** panel to drill down.")

    _esql_expander("ML Anomaly Detection", data["esql"])


# ── Main render function ───────────────────────────────────────────────────────

def render_obs_intelligence_tab(loader=None):
    """Entry point — renders the full Reliability Engine™ tab."""
    st.markdown(_CSS, unsafe_allow_html=True)

    # Header banner
    st.markdown(
        '<div class="re-header">'
        '<h2>🔭 Reliability Engine™</h2>'
        '<p>7-Layer Observability Intelligence · APM + Logs + Traces + SLOs + ML · '
        'Tenant-Aware · Multi-Region · Powered by Elastic</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Tenant + Region selectors (top of every panel)
    tenant, region = _tenant_region_bar("obs_main")

    # Panel navigation
    PANELS = [
        "🏥 Service Health",
        "📈 APM Analytics",
        "📋 Log Intelligence",
        "🚨 Incident Triage",
        "🔗 Distributed Tracing",
        "📊 SLO Dashboard",
        "🤖 Anomaly Detection",
    ]

    active_panel = st.segmented_control(
        "obs_panel",
        options=PANELS,
        default=PANELS[0],
        key="obs_panel_selector",
        label_visibility="collapsed",
    )

    st.markdown("")

    # Build service object (simulation unless live ES client wired)
    from src.services.obs_intelligence_service import ObsIntelligenceService
    svc = ObsIntelligenceService(tenant_id=tenant, region=region)

    # Route to panel
    if active_panel == "🏥 Service Health":
        _render_service_health(svc, tenant, region)
    elif active_panel == "📈 APM Analytics":
        _render_apm_analytics(svc, tenant, region)
    elif active_panel == "📋 Log Intelligence":
        _render_log_intelligence(svc, tenant, region)
    elif active_panel == "🚨 Incident Triage":
        _render_incident_triage(svc, tenant, region)
    elif active_panel == "🔗 Distributed Tracing":
        _render_distributed_tracing(svc, tenant, region)
    elif active_panel == "📊 SLO Dashboard":
        _render_slo_dashboard(svc, tenant, region)
    elif active_panel == "🤖 Anomaly Detection":
        _render_anomaly_detection(svc, tenant, region)
