"""
Dev WorkBench Tab

VS Code / IDE integration for Elastic Demo Generator observability:
  - MCP server config generator (copy-ready JSON for VS Code settings)
  - Inline Root Cause Analyzer — run structured RCA from the browser
  - Live ES|QL Console — ad-hoc query playground
  - Claude prompt templates for IDE troubleshooting
"""

import json
import os
import urllib.parse
import streamlit as st
import streamlit.components.v1 as _st_components


# ── helpers ───────────────────────────────────────────────────────────────────

def _copy_button(content: str, key: str, label: str = "📋 Copy"):
    encoded = urllib.parse.quote(content, safe="")
    _st_components.html(
        f"""
        <button
          style="background:#1f77b4;color:white;border:none;border-radius:4px;
                 padding:6px 14px;cursor:pointer;font-size:13px;font-family:monospace;"
          onclick="navigator.clipboard.writeText(decodeURIComponent('{encoded}'))
                   .then(()=>{{this.innerHTML='✅ Copied!';setTimeout(()=>this.innerHTML='{label}',2000)}})
                   .catch(()=>this.innerHTML='❌ Failed')">
          {label}
        </button>
        """,
        height=44,
    )


def _get_obs_service(loader) -> str:
    """Best-effort extract of a service name from the demo config."""
    ctx = loader.config.get("customer_context") or loader.config
    company = ctx.get("company_name", "demo")
    return company.lower().replace(" ", "-")[:20]


def _get_es():
    """Return live ES client or None."""
    try:
        from elasticsearch import Elasticsearch
        api_key  = os.getenv("ELASTICSEARCH_API_KEY", "")
        endpoint = os.getenv("ELASTIC_ENDPOINT", "") or os.getenv("ES_URL", "")
        cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
        if not (api_key and (endpoint or cloud_id)):
            return None
        kwargs = {"request_timeout": 20, "api_key": api_key}
        if cloud_id:
            return Elasticsearch(cloud_id=cloud_id, **kwargs)
        return Elasticsearch(endpoint, **kwargs)
    except Exception:
        return None


# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """
<style>
.wb-header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: white; padding: 20px 24px; border-radius: 10px; margin-bottom: 16px;
}
.wb-header h2 { margin: 0; font-size: 1.5rem; }
.wb-header p  { margin: 4px 0 0; opacity: .75; font-size: .85rem; }
.wb-section {
  border: 1px solid #e0e0e0; border-radius: 8px;
  padding: 16px; margin-bottom: 16px; background: #fafafa;
}
.wb-section h4 { margin: 0 0 12px; color: #1f4e79; }
.tool-badge {
  display:inline-block; background:#e8f4f8; color:#1565c0;
  border-radius:4px; padding:2px 8px; font-size:.8rem;
  font-family:monospace; margin:2px;
}
.rca-section {
  background: #fff8e1; border-left: 4px solid #ffc107;
  padding: 12px 16px; border-radius: 0 6px 6px 0; margin: 8px 0;
}
</style>
"""

# ── MCP config builder ────────────────────────────────────────────────────────

def _render_mcp_setup(loader):
    """Section 1 — VS Code MCP config."""
    import sys
    from pathlib import Path

    st.markdown('<div class="wb-section"><h4>⚙️ 1. Connect VS Code to Your Elastic Cluster</h4>', unsafe_allow_html=True)

    cwd = str(Path.cwd())
    endpoint = os.getenv("ELASTIC_ENDPOINT", "") or os.getenv("ES_URL", "https://your-cluster.es.io:9243")
    api_key  = os.getenv("ELASTICSEARCH_API_KEY", "YOUR_API_KEY_HERE")

    mcp_config = {
        "mcp": {
            "servers": {
                "elastic-demo-generator": {
                    "type": "stdio",
                    "command": sys.executable,
                    "args": ["-m", "src.mcp.mcp_server"],
                    "cwd": cwd,
                    "env": {
                        "ELASTIC_ENDPOINT": endpoint,
                        "ELASTICSEARCH_API_KEY": api_key,
                    }
                }
            }
        }
    }
    config_str = json.dumps(mcp_config, indent=2)

    st.markdown("""
Add this to your **VS Code `settings.json`** (`Cmd+Shift+P` → *Preferences: Open User Settings (JSON)*):
""")
    st.code(config_str, language="json")
    _copy_button(config_str, "copy_mcp_cfg", "📋 Copy MCP Config")

    st.markdown("""
**What this unlocks in VS Code (with Claude):**
- Ask *"What's wrong with auth-service?"* → Claude queries your live Elastic cluster
- Ask *"Show me errors in the last 30 minutes"* → Live log search
- Ask *"What's my SLO burn rate?"* → Real-time SLO compliance
- Run any ES|QL query with *"Run this ES|QL: FROM logs-* | ..."*
""")

    st.markdown("---")
    st.markdown("### ⚙️ How MCP + Elastic works — technical deep dive")

    st.markdown("#### 1. MCP stdio transport: VS Code spawns the Python process")
    st.markdown("""
The MCP configuration above uses `"type": "stdio"`. When you open VS Code with Claude:

1. VS Code's Claude extension reads the `mcp.servers` config from `settings.json`
2. It **spawns** `python -m src.mcp.mcp_server` as a child process in the `cwd` you specified
3. All communication happens over **stdin / stdout** using [JSON-RPC 2.0](https://www.jsonrpc.org/specification) messages — no network port, no firewall rules needed
4. VS Code sends a `tools/list` request; the MCP server responds with the tool schema (name, description, input JSON Schema)
5. When Claude decides to call a tool, VS Code sends a `tools/call` JSON-RPC request; the server runs the ES|QL query and returns the result as a JSON-RPC response
""")
    st.code("""\
# What VS Code sends when Claude calls get_service_health:
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_service_health",
    "arguments": {
      "tenant_id": "acme",
      "region": "us-east-1"
    }
  }
}

# What the MCP server returns:
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"services\": [{\"name\": \"auth-service\", \"error_rate\": 4.2, ...}]}"
    }]
  }
}
""", language="json")

    st.markdown("#### 2. How each tool call maps to an ES|QL query against the live cluster")
    st.markdown("""
Each MCP tool is a thin wrapper that:
1. Validates the input arguments (tenant_id, region, time window)
2. Constructs a parameterised ES|QL query (tenant filter baked in — no cross-tenant data leakage)
3. Sends it to Elastic via the Python `elasticsearch` client
4. Serialises the result rows as JSON and returns them to Claude via the JSON-RPC response
""")
    st.code("""\
# Example: search_logs tool internals
def search_logs(tenant_id: str, region: str, query: str, window_minutes: int = 30) -> dict:
    esql = f\"\"\"
FROM logs-*
| WHERE @timestamp >= NOW() - {window_minutes} minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
  AND MATCH(log.message, "{query}")
| STATS count = COUNT(*) BY log.message, service.name
| SORT count DESC
| LIMIT 20
\"\"\"
    resp = es_client.esql.query(body={"query": esql}, format="json")
    return {
        "columns": resp["columns"],
        "rows": resp["values"],
        "total": len(resp["values"]),
    }
""", language="python")

    st.markdown("#### 3. Security model: API key scoped to read-only on specific indices")
    st.markdown("""
The `ELASTICSEARCH_API_KEY` in the MCP config should be a **restricted API key** — not a superuser key. Create it with the minimum privileges needed:
""")
    st.code("""\
POST /_security/api_key
{
  "name": "edg-mcp-readonly",
  "role_descriptors": {
    "mcp_reader": {
      "cluster": ["monitor"],
      "indices": [
        {
          "names": [
            "traces-apm-*",
            "logs-*",
            "metrics-apm-*",
            ".ml-anomalies-*"
          ],
          "privileges": ["read", "view_index_metadata"],
          "field_security": {
            "grant": ["*"],
            "except": ["_source._private"]
          },
          "query": {
            "term": { "tenant_id": "<tenant-specific-filter>" }
          }
        }
      ]
    }
  },
  "expiration": "90d",
  "metadata": { "purpose": "edg-mcp-server", "owner": "sre-team" }
}
""", language="json")
    st.markdown("""
Key security properties:
- **Read-only**: `read` and `view_index_metadata` privileges only — no write, no delete, no index management
- **Index-scoped**: only the observability indices (`traces-apm-*`, `logs-*`, `metrics-apm-*`) — not `security-*`, not `.kibana*`
- **Document-level security**: the optional `query` filter ensures the API key can only see data for a specific tenant — critical for multi-tenant deployments
- **Expiration**: 90-day expiry forces rotation, reducing blast radius if the key is leaked
- **No cluster-wide privileges**: `monitor` only — cannot see user accounts, API keys, or cluster configuration
""")

    st.markdown('</div>', unsafe_allow_html=True)


# ── Available tools reference ─────────────────────────────────────────────────

def _render_tools_reference():
    """Section 2 — tool quick reference."""
    st.markdown('<div class="wb-section"><h4>🔧 2. Available MCP Tools</h4>', unsafe_allow_html=True)

    tools = [
        ("get_service_health",  "Health status for all services — error rate, latency, throughput"),
        ("search_logs",         "Full-text log search with service + time window filters"),
        ("get_apm_metrics",     "APM latency (p50/p95/p99), error rate, slowest endpoints"),
        ("get_active_alerts",   "Currently firing Kibana alerting rules"),
        ("get_slo_status",      "SLO burn rate, error budget consumed, compliance status"),
        ("run_esql_query",      "Execute any ES|QL query directly"),
        ("analyze_root_cause",  "Structured RCA — combines logs + APM + alerts + blast radius"),
    ]

    for name, desc in tools:
        st.markdown(
            f'<span class="tool-badge">{name}</span> — {desc}',
            unsafe_allow_html=True,
        )

    with st.expander("📋 Example Claude prompts for VS Code", expanded=False):
        prompts = [
            ('Service health',       'What is the current health of the auth-service for tenant "acme" in us-east-1?'),
            ('Root cause',           'Analyze the root cause of the auth-service degradation for tenant "acme" over the last 30 minutes.'),
            ('Log investigation',    'Search for "NullPointerException" errors in the contact-routing service in the last hour.'),
            ('SLO check',            'What is the SLO burn rate for tenant "acme" in eu-west-1?'),
            ('Ad-hoc ES|QL',         'Run this ES|QL: FROM traces-* | WHERE tenant_id == "acme" | STATS COUNT(*) BY service.name'),
            ('Blast radius',         'Which services have the highest error rates right now for tenant "acme"?'),
            ('Incident investigation', 'We got a page that api-gateway is returning 5xx. Analyze the root cause and give me remediation steps.'),
        ]
        for title, prompt in prompts:
            st.markdown(f"**{title}**")
            st.code(prompt, language=None)
            _copy_button(prompt, f"copy_prompt_{title.replace(' ', '_')}", "📋 Copy prompt")

    st.markdown('</div>', unsafe_allow_html=True)


# ── Inline RCA runner ─────────────────────────────────────────────────────────

def _render_rca_runner(loader):
    """Section 3 — run RCA from the browser without VS Code."""
    st.markdown('<div class="wb-section"><h4>🔍 3. Root Cause Analyzer</h4>', unsafe_allow_html=True)
    st.caption("Run a structured RCA directly from this browser — no VS Code required.")

    default_service = _get_obs_service(loader)

    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        service = st.text_input("Service name", value=default_service, key="rca_service")
    with c2:
        tenant_id = st.text_input("Tenant ID", value="default", key="rca_tenant")
    with c3:
        window = st.selectbox("Window", [15, 30, 60, 120], index=1, key="rca_window")

    region = st.text_input("Region", value="us-east-1", key="rca_region")
    incident = st.text_area(
        "Describe the symptom (optional)",
        placeholder="e.g. Users are getting 504 errors on login, latency spiked to 30s",
        key="rca_incident",
        height=80,
    )

    es = _get_es()

    if st.button("🔍 Run Root Cause Analysis", type="primary", key="rca_run"):
        if not es:
            st.warning("No live Elastic connection. Showing simulated RCA based on demo data.")
            _render_simulated_rca(service, tenant_id, region, window, incident)
        else:
            with st.spinner(f"Analysing `{service}` across logs, traces, and alerts…"):
                _render_live_rca(es, service, tenant_id, region, window, incident)

    st.markdown('</div>', unsafe_allow_html=True)


def _render_simulated_rca(service, tenant_id, region, window, incident):
    """Show a demo RCA when no live ES is configured."""
    import random
    patterns = [
        f"Connection pool exhausted after 100 concurrent requests to downstream-db",
        f"JWT token validation failed: signature mismatch (clock skew > 5s)",
        f"Redis cache miss rate spiked to 94% — fallback to DB causing N+1 queries",
        f"OOM kill observed in container — heap grew from 512MB to 2.1GB in 8 minutes",
    ]
    top_error = random.choice(patterns)

    st.markdown(f"""
### Root Cause Analysis — `{service}` *(simulated)*

**Tenant:** `{tenant_id}` | **Region:** `{region}` | **Window:** last {window}m
{f"> **Reported symptom:** {incident}" if incident else ""}

---

#### 1. Top Error Pattern
> `{top_error}`

**Frequency:** {random.randint(42, 847)} occurrences in the last {window} minutes

#### 2. APM Timeline
| Time | Requests | Errors | P99 (ms) |
|------|----------|--------|----------|
| -{window}m | 120 | 2 | 145 |
| -{window//2}m | 118 | 41 | 3,240 |
| -5m | 97 | 89 | 12,800 |
| now | 103 | 91 | 14,200 |

*Error rate climbed from ~1.7% → ~88% over {window//2} minutes.*

#### 3. Blast Radius
| Service | Errors |
|---------|--------|
| `{service}` | 91 |
| `api-gateway` | 67 |
| `contact-routing` | 23 |

---
<div class="rca-section">

#### 🛠️ Recommended Actions

1. **Immediate**: Check downstream connection pool config (`max_connections`, `pool_timeout`)
2. **Correlate**: Was there a deployment or config change ~{window//2} minutes ago?
3. **Trace**: Pull a failing `transaction.id` and follow the distributed trace
4. **Scale**: If load-related — trigger HPA or pre-warm cache
5. **Notify**: SLA breach if error rate > 5% for >5 minutes

</div>

> *Connect a live Elastic cluster to see real data from your cluster.*
""", unsafe_allow_html=True)


def _render_live_rca(es, service, tenant_id, region, window, incident):
    """Run real ES|QL queries for RCA."""
    from datetime import datetime, timezone

    def esql(q):
        try:
            resp = es.esql.query(body={"query": q}, format="json")
            return resp.get("columns", []), resp.get("values", [])
        except Exception as exc:
            return [], [["error", str(exc)]]

    # Error patterns
    cols1, rows1 = esql(f"""
FROM logs-*
| WHERE @timestamp >= NOW() - {window} minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
  AND service.name == "{service}"
  AND log.level IN ("ERROR", "FATAL")
| STATS count = COUNT(*) BY log.message
| SORT count DESC
| LIMIT 8
""")

    # APM timeline
    cols2, rows2 = esql(f"""
FROM traces-*
| WHERE @timestamp >= NOW() - {window} minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
  AND service.name == "{service}"
| STATS
    calls  = COUNT(*),
    errors = COUNT_CASE(transaction.result LIKE "HTTP 5*"),
    p99_ms = PERCENTILE(transaction.duration.us, 99) / 1000
  BY DATE_TRUNC(5 minutes, @timestamp)
| SORT @timestamp ASC
""")

    # Blast radius
    cols3, rows3 = esql(f"""
FROM traces-*
| WHERE @timestamp >= NOW() - {window} minutes
  AND tenant_id == "{tenant_id}"
  AND region == "{region}"
  AND transaction.result LIKE "HTTP 5*"
| STATS errors = COUNT(*) BY service.name
| SORT errors DESC
| LIMIT 8
""")

    top_error = rows1[0][1] if rows1 and len(rows1[0]) > 1 else "No errors found"
    incident_ctx = f"\n> **Reported symptom:** {incident}" if incident else ""

    st.markdown(f"""
### Root Cause Analysis — `{service}`

**Tenant:** `{tenant_id}` | **Region:** `{region}` | **Window:** last {window}m
{incident_ctx}
""")

    st.markdown("#### 1. Top Error Patterns")
    if rows1:
        st.dataframe({"Message": [r[1] for r in rows1], "Count": [r[0] for r in rows1]})
    else:
        st.success("No ERROR/FATAL logs found — service logs appear healthy.")

    st.markdown("#### 2. APM Error Timeline (5-min buckets)")
    if rows2:
        import pandas as pd
        df = pd.DataFrame(rows2, columns=[c["name"] for c in cols2] if cols2 else ["ts", "calls", "errors", "p99_ms"])
        st.dataframe(df)
    else:
        st.info("No trace data found for this service in the selected window.")

    st.markdown("#### 3. Services with Errors (Blast Radius)")
    if rows3:
        import pandas as pd
        df3 = pd.DataFrame(rows3, columns=[c["name"] for c in cols3] if cols3 else ["service", "errors"])
        st.dataframe(df3)

    st.markdown(f"""
---
<div class="rca-section">

#### 🛠️ Recommended Actions

1. **Review top error**: `{str(top_error)[:120]}`
2. **Correlate** the APM timeline above with any deployment or config change at the onset of the spike.
3. **Trace** a failing `transaction.id` through the distributed trace to find the originating call.
4. **Check upstream** services listed in the Blast Radius section.
5. **Run in VS Code**: Connect the Elastic Demo Generator MCP server and ask Claude for a deeper analysis with full context.

</div>

> *Generated by Elastic Demo Generator · Dev WorkBench • {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}*
""", unsafe_allow_html=True)


# ── ES|QL Console ─────────────────────────────────────────────────────────────

def _render_esql_console(loader):
    """Section 4 — live ES|QL playground."""
    st.markdown('<div class="wb-section"><h4>⌨️ 4. Live ES|QL Console</h4>', unsafe_allow_html=True)
    st.caption("Run any ES|QL query against your cluster directly from the browser.")

    default_ns = _get_obs_service(loader)
    default_query = f'FROM logs-*\n| WHERE tenant_id == "default" AND region == "us-east-1"\n| STATS count = COUNT(*) BY service.name\n| SORT count DESC\n| LIMIT 10'

    query = st.text_area("ES|QL Query", value=default_query, height=140, key="esql_console_query")

    es = _get_es()

    col_run, col_clear = st.columns([1, 4])
    with col_run:
        run = st.button("▶ Run", type="primary", key="esql_run")

    if run:
        if not es:
            st.warning("No live Elastic connection configured. Set `ELASTIC_ENDPOINT` and `ELASTICSEARCH_API_KEY` in your `.env` file.")
        else:
            with st.spinner("Running query…"):
                try:
                    resp = es.esql.query(body={"query": query}, format="json")
                    cols = [c["name"] for c in resp.get("columns", [])]
                    rows = resp.get("values", [])
                    if cols:
                        import pandas as pd
                        df = pd.DataFrame(rows, columns=cols)
                        st.dataframe(df, use_container_width=True)
                        st.caption(f"{len(rows)} rows returned")
                    else:
                        st.info("Query returned no results.")
                except Exception as exc:
                    st.error(f"Query error: {exc}")

    # Quick ES|QL snippets
    with st.expander("📚 ES|QL quick snippets", expanded=False):
        snippets = [
            ("Error rate by service (15m)",
             'FROM traces-*\n| WHERE @timestamp >= NOW() - 15 minutes\n| STATS errors = COUNT_CASE(transaction.result LIKE "HTTP 5*"), total = COUNT(*) BY service.name\n| EVAL error_pct = ROUND(errors * 100.0 / GREATEST(total, 1), 1)\n| SORT error_pct DESC'),
            ("Top error messages",
             'FROM logs-*\n| WHERE @timestamp >= NOW() - 1 hour AND log.level == "ERROR"\n| STATS count = COUNT(*) BY log.message\n| SORT count DESC\n| LIMIT 10'),
            ("P95 latency per endpoint",
             'FROM traces-*\n| WHERE @timestamp >= NOW() - 30 minutes\n| STATS p95_ms = PERCENTILE(transaction.duration.us, 95) / 1000 BY transaction.name\n| SORT p95_ms DESC\n| LIMIT 10'),
            ("SLO availability (7 days)",
             'FROM traces-*\n| WHERE @timestamp >= NOW() - 7 days\n| STATS total = COUNT(*), errors = COUNT_CASE(transaction.result LIKE "HTTP 5*") BY service.name\n| EVAL availability = ROUND((total - errors) * 100.0 / GREATEST(total, 1), 3)\n| SORT availability ASC'),
        ]
        for title, snip in snippets:
            st.markdown(f"**{title}**")
            st.code(snip, language="sql")
            if st.button(f"Load into console", key=f"load_snip_{title.replace(' ', '_')}"):
                st.session_state["esql_console_query"] = snip
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# ── main entry point ──────────────────────────────────────────────────────────

def render_devworkbench_tab(loader):
    """Render the Dev WorkBench tab for observability demos."""
    st.markdown(_CSS, unsafe_allow_html=True)

    # Header
    st.markdown("""
<div class="wb-header">
  <h2>🖥️ Dev WorkBench</h2>
  <p>Connect Claude in VS Code to your live Elastic cluster · Root cause analysis · ES|QL console</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
> **How it works**: Elastic Demo Generator ships an [MCP server](https://modelcontextprotocol.io) that connects VS Code's Claude
> directly to your Elastic cluster. SREs and developers can ask Claude questions about live telemetry,
> run root cause analysis, and investigate incidents — without leaving the IDE.
""")

    _render_mcp_setup(loader)
    _render_tools_reference()
    _render_rca_runner(loader)
    _render_esql_console(loader)
