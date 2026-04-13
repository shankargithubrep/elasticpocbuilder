"""
Vulcan MCP Server — Dev WorkBench

Exposes Elastic observability data as MCP tools so Claude in VS Code
can query telemetry, run root cause analysis, and troubleshoot services
directly from the IDE.

Tools exposed:
  - get_service_health      : Overall health of all services for a tenant
  - search_logs             : Full-text search across log data streams
  - get_apm_metrics         : APM latency / error rate / throughput for a service
  - get_active_alerts       : Current firing alerting rules
  - get_slo_status          : SLO burn rates and error budget remaining
  - run_esql_query          : Execute arbitrary ES|QL (read-only, SELECT-like)
  - analyze_root_cause      : Structured RCA — combines logs + APM + alerts

Usage (stdio transport, recommended for VS Code):
  python -m src.mcp.vulcan_mcp_server

VS Code settings.json:
  {
    "mcp": {
      "servers": {
        "vulcan-elastic": {
          "type": "stdio",
          "command": "python",
          "args": ["-m", "src.mcp.vulcan_mcp_server"],
          "cwd": "<path-to-vulcan>",
          "env": {
            "ELASTIC_ENDPOINT": "...",
            "ELASTICSEARCH_API_KEY": "..."
          }
        }
      }
    }
  }
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()
logger = logging.getLogger(__name__)

mcp = FastMCP("vulcan-elastic")

# ── Elasticsearch client ──────────────────────────────────────────────────────

def _get_es():
    from elasticsearch import Elasticsearch
    api_key  = os.getenv("ELASTICSEARCH_API_KEY", "")
    cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
    endpoint = os.getenv("ELASTIC_ENDPOINT", "") or os.getenv("ES_URL", "")
    kwargs   = {"request_timeout": 30}
    if api_key:
        kwargs["api_key"] = api_key
    if cloud_id:
        return Elasticsearch(cloud_id=cloud_id, **kwargs)
    if endpoint:
        return Elasticsearch(endpoint, **kwargs)
    raise RuntimeError(
        "No Elasticsearch connection configured. "
        "Set ELASTIC_ENDPOINT and ELASTICSEARCH_API_KEY env vars."
    )


# ── helpers ───────────────────────────────────────────────────────────────────

def _run_esql(query: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Execute an ES|QL query and return {columns, rows, count, error}."""
    es = _get_es()
    try:
        resp = es.esql.query(
            body={"query": query, **({"params": params} if params else {})},
            format="json",
        )
        columns = [c["name"] for c in resp.get("columns", [])]
        rows    = resp.get("values", [])
        return {"columns": columns, "rows": rows, "count": len(rows), "error": None}
    except Exception as exc:
        return {"columns": [], "rows": [], "count": 0, "error": str(exc)}


def _fmt_table(result: Dict[str, Any], max_rows: int = 20) -> str:
    """Render ES|QL result as a markdown table string."""
    if result.get("error"):
        return f"❌ ES|QL error: {result['error']}"
    cols = result["columns"]
    rows = result["rows"][:max_rows]
    if not cols:
        return "No results."
    header = "| " + " | ".join(cols) + " |"
    sep    = "| " + " | ".join(["---"] * len(cols)) + " |"
    lines  = [header, sep]
    for row in rows:
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    extra = f"\n*(showing {len(rows)} of {result['count']})*" if result["count"] > max_rows else ""
    return "\n".join(lines) + extra


# ── Tool 1: Service Health ────────────────────────────────────────────────────

@mcp.tool()
def get_service_health(
    tenant_id: str = "default",
    region: str = "us-east-1",
    window_minutes: int = 15,
) -> str:
    """
    Get a health summary for all services belonging to a tenant.

    Returns error rate, p95 latency, throughput, and an overall health status
    (healthy / degraded / critical) per service.

    Args:
        tenant_id: Tenant identifier (multi-tenant isolation)
        region: Elastic region / data residency zone
        window_minutes: Look-back window in minutes (default 15)
    """
    query = f"""
FROM traces-*
| WHERE @timestamp >= NOW() - {window_minutes} minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    total      = COUNT(*),
    errors     = COUNT_CASE(transaction.result LIKE "HTTP 5*"),
    avg_dur_ms = AVG(transaction.duration.us) / 1000
  BY service.name
| EVAL error_pct = ROUND(errors * 100.0 / GREATEST(total, 1), 1)
| EVAL health = CASE(
    error_pct > 20, "🔴 critical",
    error_pct > 5,  "🟡 degraded",
    "🟢 healthy"
  )
| SORT error_pct DESC
"""
    result = _run_esql(query)
    table  = _fmt_table(result)

    return f"""## Service Health — tenant: `{tenant_id}` / region: `{region}` (last {window_minutes}m)

{table}

> Query: `FROM traces-* | WHERE tenant_id == "{tenant_id}" AND region == "{region}"…`
"""


# ── Tool 2: Search Logs ───────────────────────────────────────────────────────

@mcp.tool()
def search_logs(
    query_text: str,
    service: str = "",
    tenant_id: str = "default",
    region: str = "us-east-1",
    window_minutes: int = 60,
    max_results: int = 20,
) -> str:
    """
    Search recent log messages for a keyword, error pattern, or exception.

    Args:
        query_text: Text to search in log.message (supports wildcards)
        service: Filter to a specific service name (optional, empty = all)
        tenant_id: Tenant identifier
        region: Elastic region
        window_minutes: Look-back window in minutes (default 60)
        max_results: Maximum log lines to return (default 20)
    """
    service_filter = f'\n  AND service.name == "{service}"' if service else ""
    query = f"""
FROM logs-*
| WHERE @timestamp >= NOW() - {window_minutes} minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"{service_filter}
  AND log.message LIKE "*{query_text}*"
| KEEP @timestamp, service.name, log.level, log.message
| SORT @timestamp DESC
| LIMIT {max_results}
"""
    result = _run_esql(query)
    table  = _fmt_table(result, max_rows=max_results)
    hit_count = result["count"]

    return f"""## Log Search — `{query_text}` (last {window_minutes}m)

**Tenant:** `{tenant_id}` | **Region:** `{region}`{f' | **Service:** `{service}`' if service else ''}
**Matches:** {hit_count}

{table}
"""


# ── Tool 3: APM Metrics ───────────────────────────────────────────────────────

@mcp.tool()
def get_apm_metrics(
    service: str,
    tenant_id: str = "default",
    region: str = "us-east-1",
    window_minutes: int = 30,
) -> str:
    """
    Get APM performance metrics for a specific service: latency, error rate,
    throughput, and slowest endpoints.

    Args:
        service: Service name (e.g. "auth-service", "api-gateway")
        tenant_id: Tenant identifier
        region: Elastic region
        window_minutes: Look-back window in minutes (default 30)
    """
    # Overall stats
    overall_q = f"""
FROM traces-*
| WHERE @timestamp >= NOW() - {window_minutes} minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
  AND service.name == "{service}"
| STATS
    requests   = COUNT(*),
    errors     = COUNT_CASE(transaction.result LIKE "HTTP 5*"),
    p50_ms     = PERCENTILE(transaction.duration.us, 50) / 1000,
    p95_ms     = PERCENTILE(transaction.duration.us, 95) / 1000,
    p99_ms     = PERCENTILE(transaction.duration.us, 99) / 1000
| EVAL error_rate = ROUND(errors * 100.0 / GREATEST(requests, 1), 2)
| EVAL tpm = ROUND(requests / {window_minutes}.0, 1)
"""
    overall = _run_esql(overall_q)

    # Slowest endpoints
    endpoints_q = f"""
FROM traces-*
| WHERE @timestamp >= NOW() - {window_minutes} minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
  AND service.name == "{service}"
| STATS
    calls   = COUNT(*),
    p95_ms  = PERCENTILE(transaction.duration.us, 95) / 1000,
    errors  = COUNT_CASE(transaction.result LIKE "HTTP 5*")
  BY transaction.name
| SORT p95_ms DESC
| LIMIT 10
"""
    endpoints = _run_esql(endpoints_q)

    return f"""## APM Metrics — `{service}` (last {window_minutes}m)

**Tenant:** `{tenant_id}` | **Region:** `{region}`

### Overall

{_fmt_table(overall)}

### Slowest Endpoints

{_fmt_table(endpoints)}
"""


# ── Tool 4: Active Alerts ─────────────────────────────────────────────────────

@mcp.tool()
def get_active_alerts(
    tenant_id: str = "default",
    region: str = "us-east-1",
    window_minutes: int = 60,
) -> str:
    """
    List active and recently fired alerting rules for a tenant.

    Args:
        tenant_id: Tenant identifier
        region: Elastic region
        window_minutes: Look-back window for recent alerts
    """
    query = f"""
FROM .alerts-*
| WHERE @timestamp >= NOW() - {window_minutes} minutes
  AND kibana.alert.status == "active"
| KEEP @timestamp, kibana.alert.rule.name, kibana.alert.severity,
       kibana.alert.status, kibana.alert.reason
| SORT @timestamp DESC
| LIMIT 25
"""
    result = _run_esql(query)

    # Fallback: if .alerts-* not accessible, return helpful message
    if result.get("error"):
        return f"""## Active Alerts — tenant: `{tenant_id}` / region: `{region}`

⚠️ Could not query alert index: `{result['error']}`

*Tip: The `.alerts-*` index requires appropriate Kibana alerting permissions.*
"""

    return f"""## Active Alerts — tenant: `{tenant_id}` / region: `{region}` (last {window_minutes}m)

{_fmt_table(result)}
"""


# ── Tool 5: SLO Status ────────────────────────────────────────────────────────

@mcp.tool()
def get_slo_status(
    tenant_id: str = "default",
    region: str = "us-east-1",
) -> str:
    """
    Get current SLO burn rates, error budgets, and compliance status for a tenant.

    Args:
        tenant_id: Tenant identifier
        region: Elastic region
    """
    # SLO summary from traces — availability and latency SLOs
    avail_q = f"""
FROM traces-*
| WHERE @timestamp >= NOW() - 7 days
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
| STATS
    total  = COUNT(*),
    errors = COUNT_CASE(transaction.result LIKE "HTTP 5*")
  BY service.name
| EVAL availability = ROUND((total - errors) * 100.0 / GREATEST(total, 1), 3)
| EVAL slo_target   = 99.9
| EVAL budget_used  = ROUND((100 - availability) / (100 - slo_target) * 100, 1)
| EVAL status = CASE(
    availability < 99.0, "🔴 BREACHED",
    availability < 99.9, "🟡 AT RISK",
    "🟢 OK"
  )
| SORT availability ASC
"""
    result = _run_esql(avail_q)

    return f"""## SLO Status — tenant: `{tenant_id}` / region: `{region}` (7-day window)

### Availability SLOs (target: 99.9%)

{_fmt_table(result)}

> **budget_used** — % of error budget consumed. >100% = SLO breached.
"""


# ── Tool 6: Raw ES|QL ─────────────────────────────────────────────────────────

@mcp.tool()
def run_esql_query(
    query: str,
    max_rows: int = 50,
) -> str:
    """
    Execute an arbitrary ES|QL query against the connected Elastic cluster.

    Use this for ad-hoc investigations. ES|QL is a pipe-based query language:
      FROM <index> | WHERE <filter> | STATS ... BY ... | SORT ... | LIMIT n

    Args:
        query: Full ES|QL query string
        max_rows: Maximum rows to return (default 50, max 500)
    """
    max_rows = min(max_rows, 500)
    result   = _run_esql(query)
    table    = _fmt_table(result, max_rows=max_rows)

    return f"""## ES|QL Result

```esql
{query.strip()}
```

{table}
"""


# ── Tool 7: Root Cause Analyzer ───────────────────────────────────────────────

@mcp.tool()
def analyze_root_cause(
    service: str,
    incident_description: str = "",
    tenant_id: str = "default",
    region: str = "us-east-1",
    window_minutes: int = 30,
) -> str:
    """
    Perform automated root cause analysis for a degraded or failing service.

    Combines error logs, APM spike data, trace patterns, and alert state
    into a structured RCA report with recommended remediation steps.

    Args:
        service: Service name to investigate (e.g. "auth-service")
        incident_description: Optional description of the observed symptom
        tenant_id: Tenant identifier
        region: Elastic region
        window_minutes: Investigation window in minutes (default 30)
    """
    # 1. Error log patterns
    errors_q = f"""
FROM logs-*
| WHERE @timestamp >= NOW() - {window_minutes} minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
  AND service.name == "{service}"
  AND log.level IN ("ERROR", "FATAL", "CRITICAL")
| STATS count = COUNT(*) BY log.message
| SORT count DESC
| LIMIT 10
"""
    error_patterns = _run_esql(errors_q)

    # 2. APM error spike
    apm_q = f"""
FROM traces-*
| WHERE @timestamp >= NOW() - {window_minutes} minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
  AND service.name == "{service}"
| STATS
    calls      = COUNT(*),
    errors     = COUNT_CASE(transaction.result LIKE "HTTP 5*"),
    p99_ms     = PERCENTILE(transaction.duration.us, 99) / 1000
  BY DATE_TRUNC(1 minute, @timestamp)
| SORT @timestamp ASC
"""
    apm_timeline = _run_esql(apm_q)

    # 3. Upstream/downstream services with errors
    upstream_q = f"""
FROM traces-*
| WHERE @timestamp >= NOW() - {window_minutes} minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
  AND transaction.result LIKE "HTTP 5*"
| STATS error_calls = COUNT(*) BY service.name
| SORT error_calls DESC
| LIMIT 10
"""
    upstream = _run_esql(upstream_q)

    # Build RCA narrative
    incident_ctx = f"\n> **Reported symptom:** {incident_description}\n" if incident_description else ""

    error_count = error_patterns.get("count", 0)
    top_error   = (error_patterns["rows"][0][0] if error_patterns["rows"] else "No errors found")

    return f"""# Root Cause Analysis — `{service}`

**Tenant:** `{tenant_id}` | **Region:** `{region}` | **Window:** last {window_minutes}m
{incident_ctx}
---

## 1. Error Log Patterns

{_fmt_table(error_patterns)}

## 2. APM Error Timeline (1-minute buckets)

{_fmt_table(apm_timeline)}

## 3. Services with Errors (cross-service blast radius)

{_fmt_table(upstream)}

---

## Recommended Investigation Steps

1. **Check top error pattern**: `{top_error[:120] if top_error else 'N/A'}`
2. **Correlate** the APM error timeline with any deployment, config change, or external dependency call at the onset of the spike.
3. **Trace** a failing `transaction.id` through the distributed trace to find the originating service.
4. **Check upstream dependencies** — services listed in section 3 may be the root cause or be impacted downstream.
5. **Review recent changes**: run `git log --since="{window_minutes} minutes ago" --oneline` in the affected service repo.

> *Generated by Vulcan Dev WorkBench • {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}*
"""


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    """Run the MCP server with stdio transport (default for VS Code)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
