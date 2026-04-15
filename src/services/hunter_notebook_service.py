"""
Hunter WorkBench — Notebook Generator Service

Generates real Jupyter (.ipynb) notebooks with pre-built ES|QL cells,
pandas DataFrames, and Plotly visualisations.  Each notebook is fully
self-contained: the user only needs to set two environment variables
(ELASTIC_ENDPOINT and ELASTICSEARCH_API_KEY) and run all cells.

Available templates
───────────────────
1. service_health       — deep-dive service health (error rate, latency, throughput)
2. log_pattern_analysis — top error patterns, log-level breakdown, timeline
3. slo_burn_rate        — rolling 30-day error budget burn, breach forecast
4. trace_analysis       — distributed trace waterfall, slowest endpoints, p-latencies
5. capacity_planning    — data volume trends, retention cost projection
6. incident_postmortem  — timeline reconstruction, blast radius, contributing factors
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ── notebook cell builders ────────────────────────────────────────────────────

def _md(lines: str) -> Dict:
    """Markdown cell."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [l + "\n" for l in lines.strip().splitlines()],
    }


def _code(lines: str, outputs: Optional[List] = None) -> Dict:
    """Code cell."""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": outputs or [],
        "source": [l + "\n" for l in lines.strip().splitlines()],
    }


# ── shared setup cells ────────────────────────────────────────────────────────

def _setup_cells(tenant_id: str, region: str) -> List[Dict]:
    return [
        _md(f"""# 🔭 Elastic Demo Generator · Hunter WorkBench
**Tenant:** `{tenant_id}` | **Region:** `{region}` | **Generated:** {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}

---
> Run all cells top-to-bottom.
> Set `ELASTIC_ENDPOINT` and `ELASTICSEARCH_API_KEY` in your environment (or edit the cell below).
"""),
        _code(f"""# ── Configuration ──────────────────────────────────────────────────
import os
import warnings
warnings.filterwarnings("ignore")

ELASTIC_ENDPOINT = os.getenv("ELASTIC_ENDPOINT", "https://your-cluster.es.io:9243")
ELASTICSEARCH_API_KEY = os.getenv("ELASTICSEARCH_API_KEY", "YOUR_API_KEY")

TENANT_ID = "{tenant_id}"
REGION    = "{region}"

# ── Elastic client ──────────────────────────────────────────────────
from elasticsearch import Elasticsearch

es = Elasticsearch(
    ELASTIC_ENDPOINT,
    api_key=ELASTICSEARCH_API_KEY,
    request_timeout=30,
)
info = es.info()
print(f"Connected to Elastic {{info['version']['number']}} — cluster: {{info['cluster_name']}}")
"""),
        _code("""# ── Helper: run ES|QL and return a DataFrame ────────────────────────
import pandas as pd

def esql(query: str, **kwargs) -> pd.DataFrame:
    resp = es.esql.query(body={"query": query, **kwargs}, format="json")
    cols = [c["name"] for c in resp.get("columns", [])]
    rows = resp.get("values", [])
    return pd.DataFrame(rows, columns=cols)

print("esql() helper ready")
"""),
    ]


# ── Template 1: Service Health ────────────────────────────────────────────────

def _nb_service_health(tenant_id: str, region: str) -> List[Dict]:
    return _setup_cells(tenant_id, region) + [
        _md("## 1. Error Rate by Service (last 15 min)"),
        _code(f"""df_errors = esql(\"\"\"
FROM traces-*
| WHERE @timestamp >= NOW() - 15 minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    total  = COUNT(*),
    errors = COUNT_CASE(transaction.result LIKE "HTTP 5*"),
    avg_ms = AVG(transaction.duration.us) / 1000
  BY service.name
| EVAL error_pct = ROUND(errors * 100.0 / GREATEST(total, 1), 1)
| SORT error_pct DESC
\"\"\")

df_errors.style.background_gradient(subset=["error_pct"], cmap="RdYlGn_r")
"""),
        _md("## 2. Latency Percentiles (p50 / p95 / p99)"),
        _code(f"""import plotly.graph_objects as go

df_lat = esql(\"\"\"
FROM traces-*
| WHERE @timestamp >= NOW() - 15 minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    p50 = PERCENTILE(transaction.duration.us, 50)  / 1000,
    p95 = PERCENTILE(transaction.duration.us, 95)  / 1000,
    p99 = PERCENTILE(transaction.duration.us, 99)  / 1000
  BY service.name
| SORT p99 DESC
\"\"\")

fig = go.Figure()
for pct, color in [("p50", "#2ecc71"), ("p95", "#f39c12"), ("p99", "#e74c3c")]:
    fig.add_trace(go.Bar(name=pct, x=df_lat["service.name"], y=df_lat[pct], marker_color=color))
fig.update_layout(barmode="group", title="Latency Percentiles (ms)", height=380)
fig.show()
"""),
        _md("## 3. Request Throughput (per minute, last 30 min)"),
        _code(f"""df_tpm = esql(\"\"\"
FROM traces-*
| WHERE @timestamp >= NOW() - 30 minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS calls = COUNT(*) BY DATE_TRUNC(1 minute, @timestamp), service.name
| SORT @timestamp ASC
\"\"\")

import plotly.express as px
fig = px.line(df_tpm, x="DATE_TRUNC(1 minute, @timestamp)", y="calls",
              color="service.name", title="Requests per Minute")
fig.show()
"""),
        _md("## 4. Health Summary"),
        _code(f"""df_summary = esql(\"\"\"
FROM traces-*
| WHERE @timestamp >= NOW() - 15 minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    total  = COUNT(*),
    errors = COUNT_CASE(transaction.result LIKE "HTTP 5*"),
    p95_ms = PERCENTILE(transaction.duration.us, 95) / 1000
  BY service.name
| EVAL error_pct = ROUND(errors * 100.0 / GREATEST(total, 1), 1)
| EVAL health = CASE(error_pct > 20, "CRITICAL", error_pct > 5, "DEGRADED", "HEALTHY")
| SORT error_pct DESC
\"\"\")

for _, row in df_summary.iterrows():
    icon = "🔴" if row["health"] == "CRITICAL" else ("🟡" if row["health"] == "DEGRADED" else "🟢")
    print(f"{{icon}} {{row['service.name']:30s}} error={{row['error_pct']}}%  p95={{row['p95_ms']:.0f}}ms")
"""),
    ]


# ── Template 2: Log Pattern Analysis ─────────────────────────────────────────

def _nb_log_patterns(tenant_id: str, region: str) -> List[Dict]:
    return _setup_cells(tenant_id, region) + [
        _md("## 1. Log Volume by Level (last 1 hour)"),
        _code(f"""import plotly.express as px

df_levels = esql(\"\"\"
FROM logs-*
| WHERE @timestamp >= NOW() - 1 hour
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS count = COUNT(*) BY log.level
| SORT count DESC
\"\"\")

fig = px.pie(df_levels, names="log.level", values="count",
             title="Log Volume by Level", color="log.level",
             color_discrete_map={{"ERROR":"#e74c3c","WARN":"#f39c12","INFO":"#3498db","DEBUG":"#95a5a6"}})
fig.show()
"""),
        _md("## 2. Top Error Messages"),
        _code(f"""df_errors = esql(\"\"\"
FROM logs-*
| WHERE @timestamp >= NOW() - 1 hour
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
  AND log.level IN ("ERROR", "FATAL", "CRITICAL")
| STATS count = COUNT(*) BY log.message, service.name
| SORT count DESC
| LIMIT 20
\"\"\")

df_errors
"""),
        _md("## 3. Error Spike Detection (5-min buckets)"),
        _code(f"""df_timeline = esql(\"\"\"
FROM logs-*
| WHERE @timestamp >= NOW() - 3 hours
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    total  = COUNT(*),
    errors = COUNT_CASE(log.level IN ("ERROR","FATAL"))
  BY DATE_TRUNC(5 minutes, @timestamp)
| EVAL error_pct = ROUND(errors * 100.0 / GREATEST(total, 1), 1)
| SORT @timestamp ASC
\"\"\")

import plotly.graph_objects as go
fig = go.Figure()
fig.add_trace(go.Bar(x=df_timeline.iloc[:,2], y=df_timeline["total"],  name="Total",  marker_color="#3498db", opacity=0.5))
fig.add_trace(go.Bar(x=df_timeline.iloc[:,2], y=df_timeline["errors"], name="Errors", marker_color="#e74c3c"))
fig.update_layout(barmode="overlay", title="Log Timeline (5-min buckets)", height=320)
fig.show()
"""),
        _md("## 4. Error Rate by Service"),
        _code(f"""df_svc = esql(\"\"\"
FROM logs-*
| WHERE @timestamp >= NOW() - 1 hour
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    total  = COUNT(*),
    errors = COUNT_CASE(log.level IN ("ERROR","FATAL"))
  BY service.name
| EVAL error_pct = ROUND(errors * 100.0 / GREATEST(total, 1), 1)
| SORT error_pct DESC
\"\"\")

df_svc.style.bar(subset=["error_pct"], color="#e74c3c")
"""),
    ]


# ── Template 3: SLO Burn Rate ─────────────────────────────────────────────────

def _nb_slo_burn(tenant_id: str, region: str) -> List[Dict]:
    return _setup_cells(tenant_id, region) + [
        _md("## 1. Availability SLOs — Current Status"),
        _code(f"""df_avail = esql(\"\"\"
FROM traces-*
| WHERE @timestamp >= NOW() - 30 days
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    total  = COUNT(*),
    errors = COUNT_CASE(transaction.result LIKE "HTTP 5*")
  BY service.name
| EVAL availability   = ROUND((total - errors) * 100.0 / GREATEST(total, 1), 4)
| EVAL budget_used    = ROUND((100 - availability) / (100 - 99.9) * 100, 1)
| EVAL slo_status     = CASE(availability < 99.9, "BREACHED", budget_used > 50, "AT RISK", "OK")
| SORT budget_used DESC
\"\"\")

df_avail.style.applymap(
    lambda v: "background: #fde8e8" if v == "BREACHED" else ("background: #fff8e1" if v == "AT RISK" else ""),
    subset=["slo_status"]
)
"""),
        _md("## 2. Daily Error Budget Burn (last 30 days)"),
        _code(f"""df_daily = esql(\"\"\"
FROM traces-*
| WHERE @timestamp >= NOW() - 30 days
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    total  = COUNT(*),
    errors = COUNT_CASE(transaction.result LIKE "HTTP 5*")
  BY DATE_TRUNC(1 day, @timestamp), service.name
| EVAL availability = (total - errors) * 100.0 / GREATEST(total, 1)
| EVAL daily_burn   = ROUND((100 - availability) / (100 - 99.9) * 100 / 30, 2)
| SORT @timestamp ASC
\"\"\")

import plotly.express as px
fig = px.line(df_daily, x=df_daily.columns[2], y="daily_burn",
              color="service.name", title="Daily Error Budget Burn Rate (%)")
fig.add_hline(y=100/30, line_dash="dash", line_color="red",
              annotation_text="Allowed burn (even pace)")
fig.show()
"""),
        _md("## 3. Breach Forecast — Days Until Budget Exhausted"),
        _code(f"""import numpy as np

df_budget = esql(\"\"\"
FROM traces-*
| WHERE @timestamp >= NOW() - 7 days
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    total  = COUNT(*),
    errors = COUNT_CASE(transaction.result LIKE "HTTP 5*")
  BY service.name
| EVAL error_rate_7d = errors * 1.0 / GREATEST(total, 1)
| EVAL projected_availability_30d = ROUND((1 - error_rate_7d) * 100, 4)
| EVAL budget_remaining = ROUND((projected_availability_30d - 99.9) / (100 - 99.9) * 100, 1)
| SORT budget_remaining ASC
\"\"\")

print("Projected 30-day budget (based on 7-day error rate):")
for _, row in df_budget.iterrows():
    remaining = row.get("budget_remaining", 0)
    bar_len   = max(0, min(int(remaining / 2), 50))
    bar_color = "🟢" if remaining > 50 else ("🟡" if remaining > 0 else "🔴")
    print(f"  {{bar_color}} {{row['service.name']:28s}} {{remaining:>6.1f}}% remaining  {{'█' * bar_len}}")
"""),
    ]


# ── Template 4: Trace Analysis ────────────────────────────────────────────────

def _nb_trace_analysis(tenant_id: str, region: str) -> List[Dict]:
    return _setup_cells(tenant_id, region) + [
        _md("## 1. Slowest Endpoints (last 30 min)"),
        _code(f"""df_endpoints = esql(\"\"\"
FROM traces-*
| WHERE @timestamp >= NOW() - 30 minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    calls  = COUNT(*),
    p50_ms = PERCENTILE(transaction.duration.us, 50)  / 1000,
    p95_ms = PERCENTILE(transaction.duration.us, 95)  / 1000,
    p99_ms = PERCENTILE(transaction.duration.us, 99)  / 1000,
    errors = COUNT_CASE(transaction.result LIKE "HTTP 5*")
  BY transaction.name, service.name
| SORT p99_ms DESC
| LIMIT 15
\"\"\")

import plotly.express as px
fig = px.bar(df_endpoints.head(10), x="transaction.name", y="p99_ms",
             color="service.name", title="Top 10 Slowest Endpoints — p99 (ms)")
fig.show()
"""),
        _md("## 2. Latency Distribution Heatmap"),
        _code(f"""df_heatmap = esql(\"\"\"
FROM traces-*
| WHERE @timestamp >= NOW() - 1 hour
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    p50 = PERCENTILE(transaction.duration.us, 50)  / 1000,
    p75 = PERCENTILE(transaction.duration.us, 75)  / 1000,
    p90 = PERCENTILE(transaction.duration.us, 90)  / 1000,
    p95 = PERCENTILE(transaction.duration.us, 95)  / 1000,
    p99 = PERCENTILE(transaction.duration.us, 99)  / 1000
  BY service.name
\"\"\")

import plotly.graph_objects as go
import numpy as np

pct_cols = ["p50","p75","p90","p95","p99"]
z_data   = df_heatmap[pct_cols].values.tolist()
fig = go.Figure(data=go.Heatmap(
    z=z_data, x=pct_cols, y=df_heatmap["service.name"].tolist(),
    colorscale="RdYlGn_r", text=z_data, texttemplate="%{{text:.0f}}",
))
fig.update_layout(title="Latency Heatmap (ms)", height=380)
fig.show()
"""),
        _md("## 3. Error Trace Deep Dive — Sample Failed Transactions"),
        _code(f"""df_failed = esql(\"\"\"
FROM traces-*
| WHERE @timestamp >= NOW() - 30 minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
  AND transaction.result LIKE "HTTP 5*"
| KEEP @timestamp, service.name, transaction.name, transaction.id,
       transaction.duration.us, transaction.result, trace.id
| SORT @timestamp DESC
| LIMIT 20
\"\"\")

df_failed["duration_ms"] = (df_failed["transaction.duration.us"] / 1000).round(1)
df_failed[["@timestamp","service.name","transaction.name","duration_ms","transaction.result","trace.id"]]
"""),
        _md("## 4. Throughput vs. Error Rate Correlation"),
        _code(f"""df_corr = esql(\"\"\"
FROM traces-*
| WHERE @timestamp >= NOW() - 2 hours
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    tpm    = COUNT(*),
    errors = COUNT_CASE(transaction.result LIKE "HTTP 5*")
  BY DATE_TRUNC(5 minutes, @timestamp)
| EVAL error_pct = errors * 100.0 / GREATEST(tpm, 1)
| SORT @timestamp ASC
\"\"\")

import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(specs=[[{{"secondary_y": True}}]])
fig.add_trace(go.Bar(x=df_corr.iloc[:,2], y=df_corr["tpm"], name="TPM", opacity=0.5), secondary_y=False)
fig.add_trace(go.Scatter(x=df_corr.iloc[:,2], y=df_corr["error_pct"], name="Error %",
                         line=dict(color="red", width=2)), secondary_y=True)
fig.update_layout(title="Throughput vs Error Rate (5-min buckets)", height=340)
fig.show()
"""),
    ]


# ── Template 5: Capacity Planning ────────────────────────────────────────────

def _nb_capacity(tenant_id: str, region: str) -> List[Dict]:
    return _setup_cells(tenant_id, region) + [
        _md("## 1. Data Volume by Type (last 30 days)"),
        _code(f"""df_vol = esql(\"\"\"
FROM logs-*, metrics-*, traces-*
| WHERE @timestamp >= NOW() - 30 days
  AND tenant_id == "{tenant_id}"
| STATS doc_count = COUNT(*) BY data_stream.type, DATE_TRUNC(1 day, @timestamp)
| SORT @timestamp ASC
\"\"\")

import plotly.express as px
fig = px.area(df_vol, x=df_vol.columns[2], y="doc_count",
              color="data_stream.type", title="Daily Document Volume by Signal Type")
fig.show()
"""),
        _md("## 2. Growth Rate & 90-Day Forecast"),
        _code(f"""import numpy as np
import plotly.graph_objects as go

df_growth = esql(\"\"\"
FROM logs-*
| WHERE @timestamp >= NOW() - 30 days
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS docs = COUNT(*) BY DATE_TRUNC(1 day, @timestamp)
| SORT @timestamp ASC
\"\"\")

# Simple linear regression for forecast
y  = df_growth["docs"].values
x  = np.arange(len(y))
m, b = np.polyfit(x, y, 1)
x_fut = np.arange(len(y), len(y) + 90)
y_fut = m * x_fut + b

fig = go.Figure()
fig.add_trace(go.Scatter(x=list(x), y=list(y), name="Actual", line=dict(color="#3498db")))
fig.add_trace(go.Scatter(x=list(x_fut), y=list(y_fut), name="Forecast (90d)",
                         line=dict(color="#e74c3c", dash="dash")))
fig.update_layout(title="Log Volume Forecast (90 days)", height=340)
fig.show()

growth_pct = round((m * 30 / max(y[0], 1)) * 100, 1)
print(f"Projected 90-day growth: {{growth_pct}}%")
print(f"Estimated daily volume in 90 days: {{int(y_fut[-1]):,}} docs")
"""),
        _md("## 3. Retention Cost Estimate"),
        _code(f"""# Elastic pricing estimate (adjust COST_PER_GB for your contract)
COST_PER_GB = 0.027   # USD per GB / month

df_retention = esql(\"\"\"
FROM logs-*, metrics-*, traces-*
| WHERE @timestamp >= NOW() - 7 days
  AND tenant_id == "{tenant_id}"
| STATS doc_count = COUNT(*) BY data_stream.type
\"\"\")

# Rough size estimate: 1k docs ≈ 1 MB
for _, row in df_retention.iterrows():
    sig_type = row["data_stream.type"]
    docs     = row["doc_count"]
    gb_week  = docs / 1_000_000
    gb_month = gb_week * 4.3
    cost     = gb_month * COST_PER_GB
    print(f"  {{sig_type:10s}}  {{docs:>12,}} docs/week  "
          f"~{{gb_month:>6.1f}} GB/month  ~${{cost:>6.2f}}/month")
"""),
        _md("## 4. Top Data-Producing Services"),
        _code(f"""df_top = esql(\"\"\"
FROM logs-*, traces-*
| WHERE @timestamp >= NOW() - 7 days
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS doc_count = COUNT(*) BY service.name, data_stream.type
| SORT doc_count DESC
| LIMIT 20
\"\"\")

import plotly.express as px
fig = px.bar(df_top, x="service.name", y="doc_count", color="data_stream.type",
             title="Top Data-Producing Services (7 days)", barmode="stack")
fig.update_xaxes(tickangle=-30)
fig.show()
"""),
    ]


# ── Template 6: Incident Post-Mortem ─────────────────────────────────────────

def _nb_postmortem(tenant_id: str, region: str) -> List[Dict]:
    return _setup_cells(tenant_id, region) + [
        _md("""## Incident Post-Mortem Notebook

Fill in the variables in the cell below before running.

**Sections:**
1. Incident timeline reconstruction
2. Blast radius — affected services + users
3. Error pattern identification
4. Contributing factors
5. Remediation effectiveness
"""),
        _code(f"""# ── Incident parameters — fill these in ──────────────────────────
INCIDENT_SERVICE  = "api-gateway"          # Primary affected service
INCIDENT_START    = "NOW() - 4 hours"       # ES|QL time expression
INCIDENT_END      = "NOW() - 2 hours"       # ES|QL time expression
TENANT_ID         = "{tenant_id}"
REGION            = "{region}"
"""),
        _md("## 1. Error Timeline (1-minute buckets)"),
        _code("""df_timeline = esql(f\"\"\"
FROM traces-*, logs-*
| WHERE @timestamp >= {INCIDENT_START}
  AND @timestamp <= {INCIDENT_END}
  AND tenant_id == "{TENANT_ID}"
  AND region == "{REGION}"
| STATS
    total  = COUNT(*),
    errors = COUNT_CASE(transaction.result LIKE "HTTP 5*" OR log.level == "ERROR")
  BY DATE_TRUNC(1 minute, @timestamp)
| EVAL error_pct = ROUND(errors * 100.0 / GREATEST(total, 1), 1)
| SORT @timestamp ASC
\"\"\")

import plotly.graph_objects as go
fig = go.Figure()
fig.add_trace(go.Bar(x=df_timeline.iloc[:,2], y=df_timeline["total"],
                     name="Total events", opacity=0.4, marker_color="#3498db"))
fig.add_trace(go.Scatter(x=df_timeline.iloc[:,2], y=df_timeline["error_pct"],
                         name="Error %", line=dict(color="red", width=2),
                         yaxis="y2"))
fig.update_layout(title="Incident Timeline", height=360,
                  yaxis2=dict(overlaying="y", side="right", title="Error %"))
fig.show()
"""),
        _md("## 2. Blast Radius — Affected Services"),
        _code("""df_blast = esql(f\"\"\"
FROM traces-*
| WHERE @timestamp >= {INCIDENT_START}
  AND @timestamp <= {INCIDENT_END}
  AND tenant_id == "{TENANT_ID}"
  AND region == "{REGION}"
  AND transaction.result LIKE "HTTP 5*"
| STATS
    error_calls  = COUNT(*),
    unique_traces = COUNT_DISTINCT(trace.id)
  BY service.name
| SORT error_calls DESC
\"\"\")

print("Services affected during incident:")
for _, row in df_blast.iterrows():
    print(f"  ⚡ {row['service.name']:30s}  {int(row['error_calls']):>6,} errors  "
          f"{int(row['unique_traces']):>5,} traces")
"""),
        _md("## 3. Top Error Patterns During Incident"),
        _code("""df_patterns = esql(f\"\"\"
FROM logs-*
| WHERE @timestamp >= {INCIDENT_START}
  AND @timestamp <= {INCIDENT_END}
  AND tenant_id == "{TENANT_ID}"
  AND region == "{REGION}"
  AND service.name == "{INCIDENT_SERVICE}"
  AND log.level IN ("ERROR","FATAL")
| STATS count = COUNT(*) BY log.message
| SORT count DESC
| LIMIT 10
\"\"\")

df_patterns
"""),
        _md("## 4. Latency Comparison: Before vs. During Incident"),
        _code(f"""df_before = esql(\"\"\"
FROM traces-*
| WHERE @timestamp >= NOW() - 6 hours
  AND @timestamp < NOW() - 4 hours
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    p95_ms = PERCENTILE(transaction.duration.us, 95) / 1000
  BY service.name
\"\"\")

df_before["period"] = "Before"

df_during = esql(\"\"\"
FROM traces-*
| WHERE @timestamp >= NOW() - 4 hours
  AND @timestamp < NOW() - 2 hours
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    p95_ms = PERCENTILE(transaction.duration.us, 95) / 1000
  BY service.name
\"\"\")
df_during["period"] = "During"

import pandas as pd, plotly.express as px
df_cmp = pd.concat([df_before, df_during])
fig = px.bar(df_cmp, x="service.name", y="p95_ms", color="period", barmode="group",
             title="P95 Latency — Before vs. During Incident")
fig.show()
"""),
        _md("## 5. Remediation Effectiveness"),
        _code(f"""df_after = esql(\"\"\"
FROM traces-*
| WHERE @timestamp >= NOW() - 2 hours
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    total  = COUNT(*),
    errors = COUNT_CASE(transaction.result LIKE "HTTP 5*"),
    p95_ms = PERCENTILE(transaction.duration.us, 95) / 1000
  BY service.name
| EVAL error_pct = ROUND(errors * 100.0 / GREATEST(total, 1), 1)
| SORT error_pct DESC
\"\"\")

print("Post-remediation status:")
for _, row in df_after.iterrows():
    icon = "🔴" if row["error_pct"] > 5 else "🟢"
    print(f"  {{icon}} {{row['service.name']:30s}}  error={{row['error_pct']}}%  p95={{row['p95_ms']:.0f}}ms")
"""),
    ]


# ── Notebook metadata + format ────────────────────────────────────────────────

_METADATA = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11.0"},
}


def _build_notebook(cells: List[Dict]) -> Dict:
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": _METADATA,
        "cells": cells,
    }


# ── Public API ────────────────────────────────────────────────────────────────

TEMPLATES = {
    "service_health": {
        "title":       "Service Health Deep Dive",
        "icon":        "🩺",
        "description": "Error rate, latency percentiles, and throughput per service. Identifies degraded services at a glance.",
        "persona":     "SRE",
        "builder":     _nb_service_health,
    },
    "log_pattern_analysis": {
        "title":       "Log Pattern Analysis",
        "icon":        "📋",
        "description": "Top error messages, log-level breakdown, error spike detection, and per-service error rate.",
        "persona":     "SRE",
        "builder":     _nb_log_patterns,
    },
    "slo_burn_rate": {
        "title":       "SLO Burn Rate Investigation",
        "icon":        "💰",
        "description": "30-day error budget burn, daily consumption, and 90-day breach forecast per service.",
        "persona":     "SRE / Leadership",
        "builder":     _nb_slo_burn,
    },
    "trace_analysis": {
        "title":       "Distributed Trace Analysis",
        "icon":        "🕸️",
        "description": "Slowest endpoints, latency heatmap, failed trace samples, and throughput/error correlation.",
        "persona":     "Developer / SRE",
        "builder":     _nb_trace_analysis,
    },
    "capacity_planning": {
        "title":       "Capacity Planning",
        "icon":        "📈",
        "description": "Data volume trends, 90-day forecast, retention cost estimate, top data-producing services.",
        "persona":     "DevOps / Leadership",
        "builder":     _nb_capacity,
    },
    "incident_postmortem": {
        "title":       "Incident Post-Mortem",
        "icon":        "🔍",
        "description": "Timeline reconstruction, blast radius, error patterns, latency comparison, and remediation effectiveness.",
        "persona":     "SRE / DevOps",
        "builder":     _nb_postmortem,
    },
}


class HunterNotebookService:

    def generate(
        self,
        template_key: str,
        tenant_id: str = "default",
        region: str    = "us-east-1",
        output_dir: Optional[str] = None,
    ) -> Path:
        """
        Generate a .ipynb notebook for the given template.

        Returns the path to the written file.
        """
        if template_key not in TEMPLATES:
            raise ValueError(f"Unknown template: {template_key}. Choose from: {list(TEMPLATES)}")

        tpl   = TEMPLATES[template_key]
        cells = tpl["builder"](tenant_id, region)
        nb    = _build_notebook(cells)

        out_dir  = Path(output_dir) if output_dir else Path("hunter_notebooks")
        out_dir.mkdir(parents=True, exist_ok=True)

        ts   = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        slug = template_key.replace("_", "-")
        fname = out_dir / f"{slug}_{tenant_id}_{ts}.ipynb"

        fname.write_text(json.dumps(nb, indent=2), encoding="utf-8")
        return fname

    def generate_bytes(
        self,
        template_key: str,
        tenant_id: str = "default",
        region: str    = "us-east-1",
    ) -> bytes:
        """Return the notebook as bytes (for Streamlit download_button)."""
        tpl   = TEMPLATES[template_key]
        cells = tpl["builder"](tenant_id, region)
        nb    = _build_notebook(cells)
        return json.dumps(nb, indent=2).encode("utf-8")

    def list_templates(self) -> List[Dict[str, str]]:
        return [
            {"key": k, **{f: v for f, v in t.items() if f != "builder"}}
            for k, t in TEMPLATES.items()
        ]
