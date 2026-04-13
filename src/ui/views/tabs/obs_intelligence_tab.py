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

    with st.expander("⚙️ How this works — technical deep dive", expanded=False):
        st.markdown("""
#### APM Data Model: Traces → Spans → Transactions

```
EDOT Agent (SDK)  ──instrumentation──►  your service code
        │
        │  HTTP/gRPC  (OTLP protocol)
        ▼
APM Server / OTLP Endpoint (Elastic Cloud managed)
        │
        ├─► traces-apm-*       (transactions + spans)
        ├─► logs-apm.*         (application logs with trace correlation)
        └─► metrics-apm.*      (runtime metrics: JVM heap, GC, CPU)
```

- **Transaction**: a single top-level request (e.g. `GET /api/users`)
- **Span**: a unit of work within a transaction (e.g. DB query, HTTP call to downstream)
- **Trace**: the full tree of spans across all services, linked by `trace.id`

Health scores are derived by aggregating `transaction.result`, `transaction.duration.us`, and `event.outcome` per service over a rolling 5-minute window.
""")
        st.markdown("**How to set up APM Server (Elastic Cloud)**")
        st.code("""\
# 1. Elastic Cloud: APM Server is provisioned automatically.
#    Find your APM endpoint in: Cloud console > Integrations > APM

# 2. Set EDOT (Elastic Distribution of OpenTelemetry) env vars:
OTEL_SERVICE_NAME=auth-service
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-apm-server.apm.us-east-1.aws.elastic.cloud
OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer <secret-token>"

# 3. Add EDOT SDK to your app (Python example):
pip install opentelemetry-distro elastic-opentelemetry
opentelemetry-bootstrap -a install
""", language="bash")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Build service health in your app**")
            st.markdown("""
- Query `metrics-apm.*` for error rate and throughput per service
- Query `traces-apm-*` for P95 latency using `PERCENTILE(transaction.duration.us, 95)`
- Set thresholds: error rate > 2% = degraded, > 5% = critical
- Expose `/health` endpoint in your portal that calls this ES|QL in real-time
""")
        with col2:
            st.markdown("**Explore in Kibana APM**")
            st.markdown("""
- **Observability > Services**: pre-built service health dashboard, no query needed
- **Observability > Alerts**: create threshold rules on error rate and latency
- **Stack Management > Index Management**: inspect `traces-apm-*` mappings and data retention
- **APM > Service Map**: auto-generated topology from span `destination.service.resource`
""")


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

    with st.expander("⚙️ How this works — technical deep dive", expanded=False):
        st.markdown("""
#### Latency Percentiles in ES|QL

Percentile aggregations (`P50`, `P95`, `P99`) answer different questions:
- **P50** (median): the typical user experience — half of requests are faster than this
- **P95**: 95% of users are faster; the threshold for "acceptable" in most SLOs
- **P99**: tail latency — what your slowest 1% of users experience; critical for SLA compliance

`event.duration` in OpenTelemetry/EDOT is stored in **nanoseconds**. Divide by `1,000,000` to get milliseconds.
""")
        st.markdown("**ES|QL `PERCENTILE()` aggregation explained**")
        st.code("""\
FROM traces-apm-*
| WHERE @timestamp >= NOW() - 1 hour
  AND tenant_id == "genesys-us"
  AND service.name == "auth-service"
| STATS
    p50_ms = PERCENTILE(transaction.duration.us, 50) / 1000,
    p95_ms = PERCENTILE(transaction.duration.us, 95) / 1000,
    p99_ms = PERCENTILE(transaction.duration.us, 99) / 1000,
    throughput = COUNT(*),
    error_rate = COUNT_CASE(event.outcome == "failure") * 100.0 / COUNT(*)
  BY DATE_TRUNC(5 minutes, @timestamp)
| SORT @timestamp ASC
""", language="sql")

        st.markdown("**Create a Kibana SLO from this latency data**")
        st.code("""\
POST kbn:/api/slos
{
  "name": "auth-service P95 latency < 500ms",
  "description": "95th percentile response time SLO",
  "indicator": {
    "type": "sli.apm.transactionDuration",
    "params": {
      "service": "auth-service",
      "environment": "production",
      "transactionType": "request",
      "transactionName": "*",
      "threshold": 500,
      "index": "traces-apm-*"
    }
  },
  "timeWindow": { "duration": "30d", "type": "rolling" },
  "budgetingMethod": "occurrences",
  "objective": { "target": 0.99 }
}
""", language="json")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Build this in your app**")
            st.markdown("""
- Run the ES|QL query above on page load with a configurable time window
- Plot P50/P95/P99 as a line chart — spikes in P99 but not P50 = tail latency problem
- Alert when P95 crosses your SLA threshold using Kibana Alerting
- Link each data point to Kibana APM traces for drill-down
""")
        with col2:
            st.markdown("**Explore in Kibana**")
            st.markdown("""
- **APM > Services > [service] > Transactions**: pre-built latency distribution histogram
- **APM > Services > [service] > Throughput**: requests per minute over time
- **Observability > SLOs**: manage SLO targets, burn rate, and error budget in one place
- **Dashboards**: clone the built-in APM dashboard and add your tenant filter
""")


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

    with st.expander("⚙️ How this works — technical deep dive", expanded=False):
        st.markdown("""
#### Log Pipeline: EDOT → Elastic

```
Your application (any language)
        │
        │  OTLP / Filebeat / Logstash agent
        ▼
EDOT Collector  (OpenTelemetry collector, Elastic-managed distribution)
        │
        ├─► Enrichment: adds host.name, container.id, k8s.pod.name, trace.id
        ├─► Parsing:    ingest pipelines extract structured fields from message
        └─► Routing:    data stream routing by service.name + environment
        │
        ▼
logs-{service}.{environment}-{namespace}   (data stream, hot-warm-cold ILM)
        │
        ├─► @timestamp, log.level, log.message (ECS fields)
        ├─► trace.id, transaction.id           (APM correlation)
        ├─► service.name, host.name, container.id
        └─► labels.*  (custom tags from your app)
```
""")
        st.markdown("**Full-text search on logs with ES|QL `MATCH`**")
        st.code("""\
FROM logs-*
| WHERE @timestamp >= NOW() - 1 hour
  AND tenant_id == "genesys-us"
  AND log.level IN ("ERROR", "FATAL")
  AND MATCH(log.message, "connection timeout OR pool exhausted")
| STATS count = COUNT(*) BY log.message, service.name
| SORT count DESC
| LIMIT 20
""", language="sql")

        st.markdown("**Semantic log search with ELSER (finds similar errors, not just keywords)**")
        st.code("""\
POST /logs-*/_search
{
  "query": {
    "semantic": {
      "field": "log_message_semantic",
      "query": "database connection failure"
    }
  },
  "filter": [
    { "range": { "@timestamp": { "gte": "now-1h" } } },
    { "term": { "tenant_id": "genesys-us" } }
  ]
}
""", language="json")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Build this in your app**")
            st.markdown("""
- Use `MATCH` for fast full-text keyword searches on `log.message`
- Use `semantic_text` + ELSER for fuzzy concept matching (e.g. "auth failure" finds "token rejected")
- Correlate logs to traces: join `logs-*` on `trace.id` to see the full request context
- Feed error patterns to Claude for AI root cause summaries via Anthropic API
""")
        with col2:
            st.markdown("**Explore in Kibana**")
            st.markdown("""
- **Observability > Logs Explorer**: stream live logs with KQL / ES|QL filter bar
- **Observability > Logs > Anomalies**: ML-based unusual log rate detection per service
- **APM > Services > [service] > Logs**: correlated logs for a specific trace
- **Stack Management > Ingest Pipelines**: inspect the parsing pipeline for your log format
""")


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

    with st.expander("⚙️ How this works — technical deep dive", expanded=False):
        st.markdown("""
#### How Elastic Correlations Works

Elastic Correlations (`_field_caps` + statistical analysis) scans all field values across failing vs successful requests and surfaces fields that appear disproportionately in failures. This is how "version 2.3.1 was deployed 10 minutes before error rate spiked" gets detected automatically.

```
Failing transactions sample (event.outcome == "failure")
        │
        ├─► Elastic computes field-value frequency distribution
        │
        └─► Compares against baseline (successful transactions)
                │
                ▼
        Fields with high "impact score" (KS test statistic) surfaced
        Example: { "field": "labels.version", "value": "2.3.1", "impact": 0.94 }
```
""")
        st.markdown("**ES|QL query to find correlated fields during an incident**")
        st.code("""\
FROM traces-apm-*
| WHERE @timestamp >= NOW() - 30 minutes
  AND tenant_id == "genesys-us"
  AND service.name == "auth-service"
| EVAL is_failing = event.outcome == "failure"
| STATS
    fail_count = COUNT_CASE(is_failing == true),
    total      = COUNT(*),
    fail_rate  = COUNT_CASE(is_failing == true) * 100.0 / COUNT(*)
  BY labels.version, labels.region, labels.deploy_id
| WHERE fail_count > 5
| SORT fail_rate DESC
| LIMIT 20
""", language="sql")

        st.markdown("**Create a Kibana Alert to auto-detect incidents**")
        st.code("""\
POST kbn:/api/alerting/rule
{
  "name": "auth-service error rate > 5%",
  "rule_type_id": "apm.error_rate",
  "schedule": { "interval": "2m" },
  "params": {
    "serviceName": "auth-service",
    "transactionType": "request",
    "windowSize": 5,
    "windowUnit": "m",
    "threshold": 5,
    "environment": "production"
  },
  "actions": [{
    "id": "<slack-connector-id>",
    "group": "threshold_met",
    "params": {
      "message": "auth-service error rate exceeded 5% for tenant genesys-us"
    }
  }]
}
""", language="json")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Build this in your app**")
            st.markdown("""
- Wire alert webhooks to your incident portal to create tickets automatically
- Use the ES|QL query above to surface correlated labels (version, deploy_id, region)
- Implement "Blast Radius" by querying all services with failing transactions in the same `trace.id` tree
- Store incident timelines in a dedicated `incidents-*` index for post-mortem analysis
""")
        with col2:
            st.markdown("**Explore in Kibana**")
            st.markdown("""
- **APM > Services > [service] > Correlations**: interactive correlation explorer (no ES|QL needed)
- **Observability > Alerts**: manage all alerting rules across APM, logs, metrics, SLOs
- **Stack Management > Connectors**: configure Slack, PagerDuty, Jira integrations for alert actions
- **Cases**: Kibana built-in incident management, linked to alerts and investigations
""")


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

    with st.expander("⚙️ How this works — technical deep dive", expanded=False):
        st.markdown("""
#### Trace Context Propagation (W3C TraceContext)

Every request carries two HTTP headers that link spans across services:

```
Client → api-gateway → auth-service → postgres

Headers injected by EDOT agent automatically:
  traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
               │  │                                │                │
               │  └─ trace.id (128-bit hex)        │                └─ sampled flag
               └─ version                          └─ span.id (64-bit hex)
  tracestate:  vendor-specific key-value pairs

Every span stores:
  trace.id       = "4bf92f3577b34da6a3ce929d0e0e4736"  ← links ALL spans in this request
  span.id        = "00f067aa0ba902b7"                   ← this span's unique ID
  parent.span.id = "<caller span.id>"                   ← builds the call tree
```

This is how Elastic builds the waterfall view — by querying all spans with the same `trace.id` and ordering by `@timestamp`.
""")
        st.markdown("**ES|QL query to reconstruct a trace waterfall**")
        st.code("""\
FROM traces-apm-*
| WHERE trace.id == "4bf92f3577b34da6a3ce929d0e0e4736"
| EVAL duration_ms = transaction.duration.us / 1000
| KEEP service.name, transaction.name, span.id, parent.id,
       @timestamp, duration_ms, event.outcome
| SORT @timestamp ASC
""", language="sql")

        st.markdown("**Query to find the dependency graph from span destination metadata**")
        st.code("""\
FROM traces-apm-*
| WHERE @timestamp >= NOW() - 1 hour
  AND tenant_id == "genesys-us"
  AND span.destination.service.resource IS NOT NULL
| STATS
    call_count = COUNT(*),
    p95_ms     = PERCENTILE(span.duration.us, 95) / 1000,
    error_pct  = COUNT_CASE(event.outcome == "failure") * 100.0 / COUNT(*)
  BY service.name, span.destination.service.resource
| SORT call_count DESC
| LIMIT 50
""", language="sql")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Build this in your app**")
            st.markdown("""
- Pass `traceparent` header through all HTTP calls — EDOT handles this automatically
- Store `trace.id` in your application logs to correlate log lines to specific traces
- Build the waterfall by querying spans with the same `trace.id`, sorted by `@timestamp`
- Highlight the critical path: the chain of spans that sum to the total transaction duration
""")
        with col2:
            st.markdown("**Explore in Kibana APM**")
            st.markdown("""
- **APM > Traces**: search traces by `trace.id`, latency, error status, user ID
- **APM > Services > [service] > Service Map**: visualize inter-service dependencies
- **APM > Transactions > [transaction] > Trace sample**: full waterfall with span detail
- **Discover**: filter `traces-apm-*` by `trace.id` to see raw span documents
""")


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

    with st.expander("⚙️ How this works — technical deep dive", expanded=False):
        st.markdown("""
#### SLO / SLI / Error Budget Math

```
SLO (Service Level Objective)  — the target: "99.9% of requests succeed"
SLI (Service Level Indicator)  — the measurement: good_requests / total_requests
Error Budget                   — allowed failures: 100% - 99.9% = 0.1%
                                  Over 30 days: 0.1% × 30d × 24h × 60m = 43.2 minutes
Burn Rate                      — how fast you're consuming the budget:
                                  burn_rate = error_rate_now / (1 - SLO_target)
                                  burn_rate = 1.0 → consuming at exactly budget pace
                                  burn_rate = 2.0 → will exhaust budget in 15 days
```

A **burn rate alert at 2× over 1 hour** gives you enough warning to fix the issue before the error budget is exhausted within the SLO window.
""")
        st.markdown("**ES|QL SLI calculation**")
        st.code("""\
FROM traces-apm-*
| WHERE @timestamp >= NOW() - 30 days
  AND tenant_id == "genesys-us"
  AND service.name == "auth-service"
| STATS
    good   = COUNT_CASE(event.outcome == "success"),
    total  = COUNT(*)
| EVAL
    sli_pct       = ROUND(good * 100.0 / total, 4),
    error_budget  = ROUND(100.0 - sli_pct, 4),
    budget_spent  = ROUND((100.0 - sli_pct) / 0.1 * 100, 1)
""", language="sql")

        st.markdown("**Create an SLO via Kibana API**")
        st.code("""\
POST kbn:/api/slos
{
  "name": "auth-service availability 99.9%",
  "description": "Monthly rolling 30-day SLO for authentication service",
  "indicator": {
    "type": "sli.apm.transactionErrorRate",
    "params": {
      "service":          "auth-service",
      "environment":      "production",
      "transactionType":  "request",
      "transactionName":  "*",
      "index":            "traces-apm-*",
      "filter":           "tenant_id: \"genesys-us\""
    }
  },
  "timeWindow":      { "duration": "30d", "type": "rolling" },
  "budgetingMethod": "occurrences",
  "objective":       { "target": 0.999 }
}
""", language="json")

        st.markdown("**Burn rate alert (fires when budget will be exhausted in < 2 hours)**")
        st.code("""\
POST kbn:/api/alerting/rule
{
  "name": "auth-service SLO burn rate critical",
  "rule_type_id": "slo.rules.burnRate",
  "params": {
    "sloId": "<slo-id-from-above>",
    "windows": [
      { "id": "short",  "burnRateThreshold": 14.4, "maxBurnRateThreshold": 720, "longWindow": "1h",  "shortWindow": "5m",  "actionGroup": "slo.burnRate.alert" },
      { "id": "medium", "burnRateThreshold": 6.0,  "maxBurnRateThreshold": 720, "longWindow": "6h",  "shortWindow": "30m", "actionGroup": "slo.burnRate.alert" }
    ]
  }
}
""", language="json")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Build this in your app**")
            st.markdown("""
- Surface the SLO compliance percentage and remaining error budget per tenant on a status page
- Calculate burn rate in real-time: `burn_rate = current_error_rate / (1 - target)`
- Trigger escalations when burn rate > 2× for > 5 minutes (means error budget gone in < 2.5 days)
- Store SLO history in `slos-*` index for trend analysis and quarterly reviews
""")
        with col2:
            st.markdown("**Explore in Kibana**")
            st.markdown("""
- **Observability > SLOs**: create, manage, and monitor all SLOs with burn rate charts
- **Observability > Alerts**: burn rate alerts with configurable multi-window detection
- **Dashboards > [SLO] Overview**: clone the built-in SLO dashboard and filter by tenant
- **Stack Management > Rules**: view all SLO-related alerting rules and connector actions
""")


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

    with st.expander("⚙️ How this works — technical deep dive", expanded=False):
        st.markdown("""
#### How Elastic ML Anomaly Detection Jobs Work

Elastic ML uses a **time-series modelling approach** (not neural networks):

```
Historical data (≥ 2× the bucket span)
        │
        ▼
Bucket span (e.g. 15 minutes)
  Model learns: typical value for this metric at this time-of-day / day-of-week
        │
        ▼
Real-time scoring
  anomaly_score = f(actual_value, expected_value, confidence_interval)
  Range: 0–100   (> 75 = critical, 50–75 = major, 25–50 = minor)
        │
        ▼
Influencers
  Fields that correlate with the anomaly (e.g. service.name, host.name)
  Useful for blast-radius: "which services drove the spike?"
        │
        ▼
Results stored in: .ml-anomalies-* indices
```

Key configuration parameters:
- **Bucket span**: granularity of analysis (15m = balance of sensitivity vs noise)
- **Detectors**: which metric function to analyse (e.g. `mean(transaction.duration.us)`, `count`)
- **Influencers**: fields that partition the model (e.g. `service.name`, `tenant_id`)
""")
        st.markdown("**Create an ML anomaly detection job via API**")
        st.code("""\
PUT _ml/anomaly_detectors/apm-latency-anomaly
{
  "description": "Detect unusual latency spikes per service per tenant",
  "analysis_config": {
    "bucket_span": "15m",
    "detectors": [{
      "function": "mean",
      "field_name": "transaction.duration.us",
      "by_field_name": "service.name",
      "partition_field_name": "tenant_id"
    }],
    "influencers": ["service.name", "tenant_id", "host.name"]
  },
  "data_description": {
    "time_field": "@timestamp",
    "time_format": "epoch_ms"
  },
  "datafeed_config": {
    "indices": ["traces-apm-*"],
    "query": {
      "bool": {
        "filter": [{ "term": { "processor.event": "transaction" } }]
      }
    }
  }
}
""", language="json")

        st.markdown("**Query anomaly results with ES|QL**")
        st.code("""\
FROM .ml-anomalies-*
| WHERE @timestamp >= NOW() - 24 hours
  AND job_id == "apm-latency-anomaly"
  AND record_score >= 50
| KEEP timestamp, record_score, actual, typical, influencers,
       by_field_value, partition_field_value
| SORT record_score DESC
| LIMIT 20
""", language="sql")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Build this in your app**")
            st.markdown("""
- Create one ML job per key metric (latency, error rate, throughput, log rate)
- Use `partition_field_name: "tenant_id"` to get per-tenant anomaly baselines — critical for multi-tenant SaaS
- Map anomaly scores to alert severity: > 75 → PagerDuty, 50–75 → Slack, < 50 → dashboard only
- Link anomaly records to APM traces via the influencer `service.name` for fast drill-down
""")
        with col2:
            st.markdown("**Explore in Kibana**")
            st.markdown("""
- **Machine Learning > Anomaly Detection**: create and manage jobs with a wizard UI
- **Machine Learning > Anomaly Explorer**: interactive anomaly swimlane per service
- **Machine Learning > Single Metric Viewer**: deep-dive into one detector's model and anomalies
- **Observability > Logs > Anomalies**: ML job automatically created for log rate per service
""")


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
