"""
Persona Dashboards Tab

Three role-based dashboards for the Observability pillar:

  🚨 SRE          — Incident triage, MTTR trend, error budget burn, runbook assistant
  🚀 DevOps       — DORA metrics, deployment timeline, change failure rate, pipeline health
  📊 Leadership   — SLO scorecard, cost-per-region, business impact, exec summary

All views are tenant + region scoped and show the underlying ES|QL query.
"""

import streamlit as st

# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """
<style>
.pd-header {
  background: linear-gradient(135deg, #0d1b2a 0%, #1b2838 50%, #1a3a5c 100%);
  color: white; padding: 20px 24px; border-radius: 10px; margin-bottom: 16px;
}
.pd-header h2 { margin: 0; font-size: 1.5rem; }
.pd-header p  { margin: 4px 0 0; opacity: .75; font-size: .85rem; }

.kpi-grid { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.kpi-card {
  flex: 1 1 140px; background: white; border-radius: 8px;
  border: 1px solid #e0e0e0; padding: 14px 16px; text-align: center;
}
.kpi-card .kpi-val { font-size: 1.8rem; font-weight: 700; line-height: 1.1; }
.kpi-card .kpi-lbl { font-size: .75rem; color: #666; margin-top: 4px; }
.kpi-card .kpi-trend { font-size: .8rem; margin-top: 2px; }

.inc-card {
  border-left: 4px solid #e74c3c; background: #fff8f7;
  padding: 10px 14px; border-radius: 0 6px 6px 0; margin-bottom: 8px;
}
.inc-card.p2 { border-color: #f39c12; background: #fffdf0; }
.inc-card.p3 { border-color: #3498db; background: #f0f8ff; }

.runbook {
  background: #f0f7ff; border-left: 4px solid #1565c0;
  padding: 12px 16px; border-radius: 0 6px 6px 0;
  font-family: monospace; font-size: .85rem; white-space: pre-wrap;
}

.dora-elite { color: #2ecc71; font-weight: 700; }
.dora-high  { color: #3498db; font-weight: 700; }
.dora-med   { color: #f39c12; font-weight: 700; }
.dora-low   { color: #e74c3c; font-weight: 700; }

.slo-row { padding: 6px 0; border-bottom: 1px solid #f0f0f0; }
.budget-bar { height: 8px; border-radius: 4px; background: #e0e0e0; }
.budget-fill { height: 8px; border-radius: 4px; }

.exec-stat {
  background: white; border-radius: 8px; border: 1px solid #e0e0e0;
  padding: 16px; text-align: center;
}
.exec-stat .val { font-size: 2rem; font-weight: 700; }
.exec-stat .lbl { font-size: .75rem; color: #666; }
</style>
"""


def _tenant_bar() -> tuple:
    c1, c2 = st.columns([2, 2])
    with c1:
        tenant = st.selectbox("Tenant", ["acme-corp", "default", "genesys-demo", "enterprise-1"], key="pd_tenant")
    with c2:
        region = st.selectbox("Region", ["us-east-1", "eu-west-1", "ap-southeast-1", "us-central1"], key="pd_region")
    return tenant, region


def _esql_expander(query: str, key: str):
    with st.expander("🔍 ES|QL query (under the hood)", expanded=False):
        st.code(query, language="sql")


# ── SRE Dashboard ─────────────────────────────────────────────────────────────

def _render_sre(tenant, region):
    from src.services.persona_dashboard_service import PersonaDashboardService
    svc = PersonaDashboardService(tenant, region)

    # ── Incident summary
    st.markdown("#### 🚨 Active Incidents")
    data = svc.get_sre_incident_summary()

    col1, col2, col3 = st.columns(3)
    col1.metric("🔴 P1 Open",    data["open_p1"])
    col2.metric("🟡 P2 Open",    data["open_p2"])
    col3.metric("📋 Total Open", len([i for i in data["incidents"] if i["status"] != "resolved"]))

    for inc in data["incidents"]:
        sev_class = "p2" if inc["severity"] == "P2" else ("p3" if inc["severity"] == "P3" else "")
        age_label = f"{inc['age_min']}m ago" if inc["age_min"] < 60 else f"{inc['age_min']//60}h ago"
        st.markdown(f"""
<div class="inc-card {sev_class}">
  <strong>{inc['icon'] if 'icon' not in inc else ''}{inc['severity']} — {inc['service']}</strong>
  &nbsp;&nbsp;<span style="color:#666;font-size:.8rem">{inc['status'].upper()} · {age_label} · {inc['owner']}</span><br/>
  <span style="font-size:.85rem">{inc['title']}</span>
</div>""", unsafe_allow_html=True)

    _esql_expander(data["esql"], "sre_inc")

    st.divider()

    # ── MTTR trend
    st.markdown("#### ⏱️ MTTR Trend (14 days)")
    mttr_data = svc.get_sre_mttr_trend()
    import pandas as pd
    import plotly.graph_objects as go

    df = pd.DataFrame(mttr_data["trend"])
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["date"], y=df["mttr_min"], name="MTTR (min)",
                         marker_color="#3498db", opacity=0.7))
    fig.add_hline(y=mttr_data["target_mttr"], line_dash="dash", line_color="#e74c3c",
                  annotation_text=f"Target {mttr_data['target_mttr']}m")
    fig.update_layout(height=260, margin=dict(l=0, r=0, t=20, b=0),
                      yaxis_title="Minutes", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"14-day avg MTTR: **{mttr_data['avg_mttr']} min** (target: {mttr_data['target_mttr']} min)")
    _esql_expander(mttr_data["esql"], "sre_mttr")

    st.divider()

    # ── Error budget
    st.markdown("#### 💰 Error Budget Burn (30 days)")
    budget_data = svc.get_sre_error_budget()

    for b in budget_data["budgets"]:
        pct   = min(b["budget_used"], 100)
        color = "#e74c3c" if pct > 100 else ("#f39c12" if pct > 50 else "#2ecc71")
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            st.markdown(f"**{b['service']}**")
            st.markdown(
                f'<div class="budget-bar"><div class="budget-fill" style="width:{pct}%;background:{color}"></div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.metric("Avail", f"{b['availability']}%", label_visibility="collapsed")
        with c3:
            st.markdown(b["status"])

    _esql_expander(budget_data["esql"], "sre_budget")

    st.divider()

    # ── Runbook assistant
    st.markdown("#### 📖 Runbook Assistant")
    alert_types = list(["High error rate", "Memory OOM", "Latency spike", "Data stream lag", "Certificate expiry"])
    chosen_alert = st.selectbox("Select alert type", alert_types, key="sre_runbook_select")
    runbook = svc.get_sre_runbook(chosen_alert)
    st.markdown(f'<div class="runbook">{runbook["runbook"]}</div>', unsafe_allow_html=True)
    _esql_expander(runbook["esql"], "sre_runbook")


# ── DevOps Dashboard ──────────────────────────────────────────────────────────

def _dora_color(status: str) -> str:
    return {"elite": "#2ecc71", "high": "#3498db", "medium": "#f39c12", "low": "#e74c3c"}.get(status, "#666")


def _render_devops(tenant, region):
    from src.services.persona_dashboard_service import PersonaDashboardService
    svc = PersonaDashboardService(tenant, region)

    # ── DORA metrics
    st.markdown("#### 📐 DORA Four Key Metrics")
    dora = svc.get_devops_dora()

    cols = st.columns(4)
    labels = {
        "deployment_frequency": ("🚀 Deploy Freq", ""),
        "lead_time_hours":      ("⏳ Lead Time", ""),
        "change_failure_rate":  ("💥 Change Fail Rate", ""),
        "mttr_hours":           ("🔧 MTTR", ""),
    }
    for col, (key, (lbl, _)) in zip(cols, labels.items()):
        m = dora[key]
        color = _dora_color(m["status"])
        col.markdown(f"""
<div class="exec-stat">
  <div class="val" style="color:{color}">{m['value']}<span style="font-size:1rem"> {m['unit']}</span></div>
  <div class="lbl">{lbl}</div>
  <div style="font-size:.75rem;color:#888">Trend {m['trend']} · Target {m['target']}</div>
</div>""", unsafe_allow_html=True)

    _esql_expander(dora["esql"], "devops_dora")

    st.divider()

    # ── Deployment timeline
    st.markdown("#### 🗓️ Recent Deployments")
    deploys = svc.get_devops_deployment_timeline()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total (last 2w)", deploys["total"])
    c2.metric("✅ Success",      deploys["success"])
    c3.metric("⏪ Rollbacks",   deploys["rollbacks"])

    import pandas as pd
    df = pd.DataFrame(deploys["deployments"])
    df = df[["icon", "service", "version", "status", "deployed_at", "deployed_by", "duration_s"]]
    df.columns = ["", "Service", "Version", "Status", "Deployed At", "By", "Duration (s)"]
    st.dataframe(df, use_container_width=True, hide_index=True)
    _esql_expander(deploys["esql"], "devops_deploys")

    st.divider()

    # ── Pipeline health
    st.markdown("#### 🔧 CI/CD Pipeline Health")
    pipes = svc.get_devops_pipeline_health()
    import plotly.graph_objects as go

    df_p = pd.DataFrame(pipes["pipelines"])
    fig = go.Figure(go.Bar(
        x=df_p["service"],
        y=df_p["pass_rate"],
        marker_color=[
            "#e74c3c" if r < 80 else ("#f39c12" if r < 92 else "#2ecc71")
            for r in df_p["pass_rate"]
        ],
        text=[f"{r}%" for r in df_p["pass_rate"]],
        textposition="outside",
    ))
    fig.add_hline(y=92, line_dash="dash", line_color="#f39c12", annotation_text="Target 92%")
    fig.update_layout(height=280, margin=dict(l=0, r=0, t=20, b=60),
                      yaxis=dict(title="Pass Rate %", range=[0, 110]), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    flaky = [(p["service"], p["flaky_tests"]) for p in pipes["pipelines"] if p["flaky_tests"] > 0]
    if flaky:
        st.caption("⚠️ Flaky tests: " + " · ".join(f"**{s}** ({n})" for s, n in sorted(flaky, key=lambda x: -x[1])))
    _esql_expander(pipes["esql"], "devops_pipes")


# ── Leadership Dashboard ──────────────────────────────────────────────────────

def _render_leadership(tenant, region):
    from src.services.persona_dashboard_service import PersonaDashboardService
    svc = PersonaDashboardService(tenant, region)

    # ── Exec summary
    st.markdown("#### 🏆 Executive Summary")
    ex = svc.get_leadership_exec_summary()

    cols = st.columns(4)
    cols[0].markdown(f"""<div class="exec-stat">
      <div class="val" style="color:{'#2ecc71' if ex['slo_compliance_pct'] >= 95 else '#e74c3c'}">{ex['slo_compliance_pct']}%</div>
      <div class="lbl">SLO Compliance</div></div>""", unsafe_allow_html=True)
    cols[1].markdown(f"""<div class="exec-stat">
      <div class="val" style="color:{'#e74c3c' if ex['open_p1_incidents'] > 0 else '#2ecc71'}">{ex['open_p1_incidents']}</div>
      <div class="lbl">Open P1 Incidents</div></div>""", unsafe_allow_html=True)
    cols[2].markdown(f"""<div class="exec-stat">
      <div class="val">${ex['monthly_cost_usd']:,.0f}</div>
      <div class="lbl">Monthly Obs Cost</div>
      <div style="font-size:.75rem;color:{'#e74c3c' if ex['cost_trend_pct'] > 0 else '#2ecc71'}">
        {'↑' if ex['cost_trend_pct'] > 0 else '↓'} {abs(ex['cost_trend_pct'])}% MoM</div>
      </div>""", unsafe_allow_html=True)
    cols[3].markdown(f"""<div class="exec-stat">
      <div class="val">{ex['regions_healthy']}/{ex['regions_total']}</div>
      <div class="lbl">Regions Healthy</div>
      <div style="font-size:.75rem;color:#2ecc71">{'✅ Data residency OK' if ex['data_residency_ok'] else '⚠️ Check residency'}</div>
      </div>""", unsafe_allow_html=True)

    st.divider()

    # ── SLO scorecard
    st.markdown("#### 📋 SLO Scorecard")
    scorecard = svc.get_leadership_slo_scorecard()

    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Total SLOs",     scorecard["total"])
    cc2.metric("✅ Compliant",   scorecard["compliant"])
    cc3.metric("Compliance",     f"{scorecard['compliance_pct']}%")

    import pandas as pd
    for slo in scorecard["slos"]:
        pct   = min(slo["budget_used"], 100)
        color = "#e74c3c" if slo["budget_used"] > 100 else ("#f39c12" if slo["budget_used"] > 50 else "#2ecc71")
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        with c1:
            st.markdown(f"**{slo['name']}**")
            st.markdown(
                f'<div class="budget-bar"><div class="budget-fill" style="width:{pct}%;background:{color}"></div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.caption(f"Target: {slo['target']}%")
        with c3:
            st.caption(f"Actual: {slo['actual']}%")
        with c4:
            st.markdown(slo["status"])

    _esql_expander(scorecard["esql"], "lead_slo")

    st.divider()

    # ── Cost per region
    st.markdown("#### 💵 Observability Cost by Region")
    cost_data = svc.get_leadership_cost_per_region()

    import plotly.graph_objects as go
    df_c = pd.DataFrame(cost_data["regions"])
    fig = go.Figure(data=[
        go.Bar(name="Logs",    x=df_c["region"], y=df_c["logs_gb"],    marker_color="#3498db"),
        go.Bar(name="Metrics", x=df_c["region"], y=df_c["metrics_gb"], marker_color="#2ecc71"),
        go.Bar(name="Traces",  x=df_c["region"], y=df_c["traces_gb"],  marker_color="#e67e22"),
    ])
    fig.update_layout(barmode="stack", height=280,
                      margin=dict(l=0, r=0, t=20, b=60),
                      yaxis_title="GB / month", legend=dict(orientation="h", y=-0.3))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"**Total: {cost_data['total_gb']:,.0f} GB / ${cost_data['total_cost']:,.2f} — {cost_data['month']}**")
    st.dataframe(
        pd.DataFrame(cost_data["regions"])[["region", "cloud", "logs_gb", "metrics_gb", "traces_gb", "total_gb", "cost_usd"]],
        use_container_width=True, hide_index=True,
    )
    _esql_expander(cost_data["esql"], "lead_cost")

    st.divider()

    # ── Business impact
    st.markdown("#### ⚠️ Business Impact — Incident Revenue Risk")
    impact = svc.get_leadership_business_impact()

    c1, c2 = st.columns(2)
    c1.metric("Revenue at Risk", f"${impact['total_risk']:,.2f}", delta=f"{impact['month']}")
    c2.metric("Users Affected",  f"{impact['total_users']:,}")

    df_i = pd.DataFrame(impact["incidents"])
    df_i["revenue_risk"] = df_i["revenue_risk"].apply(lambda x: f"${x:,.2f}")
    df_i["affected_users"] = df_i["affected_users"].apply(lambda x: f"{x:,}")
    df_i["resolved"] = df_i["resolved"].apply(lambda x: "✅" if x else "🔴 Open")
    df_i = df_i[["service", "incident", "duration_min", "affected_users", "revenue_risk", "resolved"]]
    df_i.columns = ["Service", "Incident", "Duration (min)", "Users Affected", "Revenue Risk", "Status"]
    st.dataframe(df_i, use_container_width=True, hide_index=True)
    _esql_expander(impact["esql"], "lead_impact")


# ── Main entry point ──────────────────────────────────────────────────────────

def render_persona_dashboards_tab(loader):
    """Render the Persona Dashboards tab for observability demos."""
    st.markdown(_CSS, unsafe_allow_html=True)

    st.markdown("""
<div class="pd-header">
  <h2>👤 Persona Dashboards</h2>
  <p>Role-based views for SRE · DevOps · Leadership — all tenant-scoped, all backed by live ES|QL</p>
</div>
""", unsafe_allow_html=True)

    tenant, region = _tenant_bar()

    persona = st.segmented_control(
        "Persona",
        options=["🚨 SRE", "🚀 DevOps", "📊 Leadership"],
        default="🚨 SRE",
        key="pd_persona",
    )

    st.divider()

    if persona == "🚨 SRE":
        _render_sre(tenant, region)
    elif persona == "🚀 DevOps":
        _render_devops(tenant, region)
    elif persona == "📊 Leadership":
        _render_leadership(tenant, region)
