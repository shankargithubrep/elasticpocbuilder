"""
Interactive Help & Documentation — Swagger/OpenAPI-style

Renders outcome-based, interactive documentation with:
- Collapsible outcome cards (like Swagger endpoints)
- YAML workflow examples with copy-to-clipboard
- Live "Try it" buttons where applicable
- Workflow diagrams
"""

import streamlit as st
import os

KIBANA_URL = os.getenv("ELASTICSEARCH_KIBANA_URL", "").rstrip("/")


def render_help_docs():
    """Main entry point — renders the full interactive docs page."""

    st.markdown("## ⚡ Elastic Demo Builder — Interactive Docs")
    st.caption(
        "Outcome-based reference. Every feature maps to a customer business outcome. "
        "Expand any card to see the YAML workflow, Kibana navigation, and talk track."
    )

    # Top-level filter
    pillar = st.segmented_control(
        "Pillar",
        ["All", "🔍 Search", "📡 Observability", "🛡️ Security", "⚙️ Platform"],
        default="All",
        key="help_pillar_filter",
        label_visibility="collapsed",
    )

    st.divider()

    if pillar in ("All", "🔍 Search"):
        _render_pillar_header("Search", "🔍", "#0077CC",
            "Find anything, instantly — across every system, every document, every knowledge base.")
        _render_outcome_card(**OUTCOMES["search_semantic"])
        _render_outcome_card(**OUTCOMES["search_dashboard"])
        _render_outcome_card(**OUTCOMES["search_alerting"])
        _render_outcome_card(**OUTCOMES["search_app"])
        _render_outcome_card(**OUTCOMES["search_agent"])
        _render_outcome_card(**OUTCOMES["search_api_key"])

    if pillar in ("All", "📡 Observability"):
        _render_pillar_header("Observability", "📡", "#00BFB3",
            "Detect, investigate, and resolve incidents before customers are impacted.")
        _render_outcome_card(**OUTCOMES["obs_apm"])
        _render_outcome_card(**OUTCOMES["obs_slo"])
        _render_outcome_card(**OUTCOMES["obs_motlp"])

    if pillar in ("All", "🛡️ Security"):
        _render_pillar_header("Security", "🛡️", "#F04E98",
            "Detect threats faster, respond with confidence, meet every audit.")
        _render_outcome_card(**OUTCOMES["sec_detection"])
        _render_outcome_card(**OUTCOMES["sec_cases"])
        _render_outcome_card(**OUTCOMES["sec_agent"])

    if pillar in ("All", "⚙️ Platform"):
        _render_pillar_header("Platform", "⚙️", "#FEC514",
            "Infrastructure that makes every demo work — pipelines, templates, lifecycle, live replay.")
        _render_outcome_card(**OUTCOMES["platform_pipeline"])
        _render_outcome_card(**OUTCOMES["platform_ilm"])
        _render_outcome_card(**OUTCOMES["platform_replay"])
        _render_outcome_card(**OUTCOMES["platform_health"])


# =============================================================================
# Outcome card renderer
# =============================================================================

def _render_outcome_card(
    id: str,
    method_badge: str,
    method_color: str,
    title: str,
    outcome: str,
    kibana_path: str,
    talk_track: str,
    yaml_label: str,
    yaml_body: str,
    try_it=None,
):
    """Render a single Swagger-style outcome card."""

    badge_html = (
        f'<span style="background:{method_color};color:white;'
        f'padding:3px 10px;border-radius:4px;font-weight:bold;'
        f'font-size:0.8em;font-family:monospace;">{method_badge}</span>'
    )
    header_html = (
        f'{badge_html} &nbsp; <strong style="font-size:1.05em">{title}</strong>'
    )

    with st.expander(f"{method_badge}  {title}", expanded=False):
        st.markdown(badge_html + f"&nbsp;&nbsp;**{title}**", unsafe_allow_html=True)

        # Outcome statement
        st.markdown(f"#### 🎯 Customer Outcome")
        st.info(outcome)

        col1, col2 = st.columns([1, 1])

        with col1:
            # Kibana path
            st.markdown("#### 📍 Where in Kibana")
            st.markdown(kibana_path)

            # Talk track
            st.markdown("#### 💬 Talk Track")
            st.markdown(f"*{talk_track}*")

        with col2:
            # YAML workflow example
            st.markdown(f"#### 📄 {yaml_label}")
            st.code(yaml_body, language="yaml")

        # Try it button (optional)
        if try_it:
            st.divider()
            try_it()


def _render_pillar_header(label: str, icon: str, color: str, tagline: str):
    st.markdown(
        f"""<div style="border-left:4px solid {color};padding:8px 16px;
        margin:16px 0 8px 0;background:rgba(0,0,0,0.03);border-radius:4px;">
        <span style="font-size:1.3em;font-weight:700">{icon} {label}</span><br/>
        <span style="color:#666;font-size:0.95em">{tagline}</span>
        </div>""",
        unsafe_allow_html=True,
    )


# =============================================================================
# Outcome definitions
# =============================================================================

OUTCOMES = {

    # ── Search ──────────────────────────────────────────────────────────────

    "search_semantic": dict(
        id="search_semantic",
        method_badge="SEARCH",
        method_color="#0077CC",
        title="Semantic Search — Find What Users Mean, Not Just What They Type",
        outcome=(
            "Your staff finds the right policy, case, or document in seconds — even when "
            "they don't know the exact terminology. Zero-result rates drop. "
            "Satisfaction scores go up."
        ),
        kibana_path=(
            "**Enterprise Search → Search Applications → `{demo}-search-app` → Preview**\n\n"
            "Type a domain query. Toggle Semantic ON/OFF to show the difference.\n\n"
            "**Dev Tools** → run same query with `match` vs `semantic` side by side."
        ),
        talk_track=(
            "What's a search your team does every day? Type it in here. "
            "Now watch — Elastic understands what you mean, not just what you typed. "
            "A search for 'heart failure' returns results about 'myocardial infarction'. "
            "That's ELSER — our purpose-built semantic search model running entirely inside your cluster."
        ),
        yaml_label="ELSER Ingest Pipeline",
        yaml_body="""# Auto-generated ELSER ingest pipeline
# Created by: Search Stack provisioning
# Purpose: ML inference on semantic fields at index time

PUT _ingest/pipeline/{demo_slug}-elser-pipeline
{
  "description": "ELSER semantic search pipeline",
  "processors": [
    {
      "inference": {
        "model_id": ".elser-2-elasticsearch",
        "input_output": [
          {
            "input_field": "content",
            "output_field": "ml.inference.content_expanded_terms"
          },
          {
            "input_field": "title",
            "output_field": "ml.inference.title_expanded_terms"
          }
        ],
        "on_failure": [
          {
            "append": {
              "field": "_source._ingest_errors",
              "value": "ELSER inference failed",
              "ignore_failure": true
            }
          }
        ]
      }
    }
  ]
}

# Search Application with RRF hybrid search
PUT _application/search_application/{demo_slug}-search-app
{
  "indices": ["{demo_slug}-knowledge-base"],
  "template": {
    "script": {
      "source": {
        "retriever": {
          "rrf": {
            "retrievers": [
              {
                "standard": {
                  "query": {
                    "multi_match": {
                      "query": "{{query}}",
                      "fields": ["title", "content"],
                      "boost": 1.0
                    }
                  }
                }
              },
              {
                "knn": {
                  "field": "content",
                  "query_vector_builder": {
                    "text_embedding": {
                      "model_id": ".elser-2-elasticsearch",
                      "model_text": "{{query}}"
                    }
                  },
                  "k": 10,
                  "num_candidates": 100,
                  "boost": 1.0
                }
              }
            ],
            "rank_constant": 60,
            "rank_window_size": 100
          }
        },
        "size": "{{size}}"
      },
      "params": {
        "query": "",
        "size": 10
      }
    }
  }
}

# Synonyms for domain vocabulary
PUT _synonyms/{demo_slug}-synonyms
{
  "synonyms_set": [
    { "id": "rule-0", "synonyms": "heart attack, myocardial infarction, MI, cardiac arrest" },
    { "id": "rule-1", "synonyms": "prior authorization, PA, pre-auth, pre-authorization" },
    { "id": "rule-2", "synonyms": "claim, request, application, submission" }
  ]
}""",
    ),

    "search_dashboard": dict(
        id="search_dashboard",
        method_badge="MONITOR",
        method_color="#00BFB3",
        title="Search Performance Dashboard — P50 / P95 / P99 Latency",
        outcome=(
            "You know the moment search performance degrades — before a customer complains. "
            "P95 latency, error rates, query patterns — all in one dashboard, "
            "refreshing every 30 seconds."
        ),
        kibana_path=(
            "**Dashboards → `{Company} — Search Performance Dashboard`**\n\n"
            "- Panel 1: Query volume over time (bar chart)\n"
            "- Panel 2: P50 / P95 / P99 latency (line chart) ← **point to this first**\n"
            "- Panel 3: Top search terms (table)\n"
            "- Panel 4: Error rate over time (area chart)\n\n"
            "Set time range to `last 7 days`. Use Live Replay to make it update in real time."
        ),
        talk_track=(
            "This dashboard is auto-generated from your data. "
            "The P95 line is your SLA indicator — if it crosses your threshold, "
            "your on-call team gets a Slack message within 5 minutes. "
            "No one is watching a dashboard. The system watches itself."
        ),
        yaml_label="Kibana Dashboard API",
        yaml_body="""# Auto-created dashboard (Kibana Saved Objects API)
# 4 panels using Lens visualization engine

POST /api/saved_objects/dashboard/{dashboard_uuid}
{
  "attributes": {
    "title": "{Company} — Search Performance Dashboard",
    "timeFrom": "now-7d",
    "timeTo": "now",
    "refreshInterval": { "pause": false, "value": 30000 },
    "panelsJSON": "[
      {
        # Panel 1: Query Volume
        'type': 'lens',
        'gridData': { 'x': 0, 'y': 0, 'w': 24, 'h': 15 },
        'visualization': 'bar_stacked',
        'metric': 'count()',
        'breakdown': '@timestamp (date_histogram)'
      },
      {
        # Panel 2: P50/P95/P99 Latency — KEY PANEL
        'type': 'lens',
        'gridData': { 'x': 24, 'y': 0, 'w': 24, 'h': 15 },
        'visualization': 'line',
        'metrics': [
          'percentile(response_time_ms, 50)  → P50',
          'percentile(response_time_ms, 95)  → P95 ← SLA indicator',
          'percentile(response_time_ms, 99)  → P99'
        ]
      },
      {
        # Panel 3: Top Search Terms
        'type': 'lens',
        'gridData': { 'x': 0, 'y': 15, 'w': 24, 'h': 15 },
        'visualization': 'datatable',
        'breakdown': 'terms(query.keyword, size=15)'
      },
      {
        # Panel 4: Error Rate
        'type': 'lens',
        'gridData': { 'x': 24, 'y': 15, 'w': 24, 'h': 15 },
        'visualization': 'area',
        'metric': 'count() where status_code != 200'
      }
    ]"
  }
}""",
    ),

    "search_alerting": dict(
        id="search_alerting",
        method_badge="ALERT",
        method_color="#F04E98",
        title="Alerting + Slack — Right Person, Right Alert, Right Time",
        outcome=(
            "The right person gets alerted within 5 minutes of a search degradation — "
            "in Slack, before a customer complains. "
            "Alert fires → Kibana Case auto-created → on-call engineer assigned."
        ),
        kibana_path=(
            "**Observability → Alerts → Rules** — two rules:\n"
            "1. `{Company} — High P95 Search Latency` — fires when P95 > 2000ms\n"
            "2. `{Company} — High Search Error Rate` — fires when errors > 10 in 5min\n\n"
            "**Stack Management → Connectors** — Slack connector wired to both rules\n\n"
            "**Live demo**: Browse → Live Replay → inject **Error Storm** → watch Slack fire"
        ),
        talk_track=(
            "When this alert fires, your Slack channel gets a message within 5 minutes. "
            "A Kibana Case is automatically created and assigned. "
            "Your engineer has the full context — index, query pattern, error rate — "
            "in one click from Slack to Kibana."
        ),
        yaml_label="Alerting Rule + Slack Workflow",
        yaml_body="""# Alert Rule 1: High P95 Latency
POST /api/alerting/rule
{
  "name": "{Company} — High P95 Search Latency",
  "rule_type_id": ".es-query",
  "schedule": { "interval": "5m" },
  "params": {
    "index": ["{demo_slug}-knowledge-base"],
    "timeField": "@timestamp",
    "timeWindowSize": 5,
    "timeWindowUnit": "m",
    "thresholdComparator": ">",
    "threshold": [2000],
    "esQuery": "{\"aggs\":{\"p95\":{\"percentiles\":{\"field\":\"response_time_ms\",\"percents\":[95]}}}}"
  },
  "actions": [
    {
      "id": "{slack_connector_id}",
      "group": "threshold met",
      "params": {
        "message": "🚨 *{Company} Alert* — P95 latency exceeded 2000ms\\nCheck dashboard: {kibana_url}/app/dashboards"
      }
    }
  ],
  "tags": ["{demo_slug}", "search", "latency"]
}

---

# Alert Rule 2: High Error Rate
POST /api/alerting/rule
{
  "name": "{Company} — High Search Error Rate",
  "rule_type_id": ".es-query",
  "schedule": { "interval": "5m" },
  "params": {
    "index": ["{demo_slug}-knowledge-base"],
    "timeField": "@timestamp",
    "timeWindowSize": 5,
    "timeWindowUnit": "m",
    "thresholdComparator": ">",
    "threshold": [10],
    "esQuery": "{\"query\":{\"bool\":{\"must_not\":[{\"term\":{\"status_code\":200}}]}}}"
  },
  "actions": [
    {
      "id": "{slack_connector_id}",
      "group": "threshold met",
      "params": {
        "message": "🚨 *{Company} Alert* — High error rate detected\\nErrors in last 5 min: {{context.value}}"
      }
    }
  ]
}

---

# Slack Connector
POST /api/actions/connector
{
  "name": "Elastic Demo Builder — Slack",
  "connector_type_id": ".slack",
  "secrets": {
    "webhookUrl": "https://hooks.slack.com/services/T.../B.../...."
  }
}

---

# Case Management Configuration (alert → auto-case)
PATCH /api/cases/configure
{
  "connector": {
    "id": "{slack_connector_id}",
    "name": "Elastic Demo Builder — Slack",
    "type": ".slack",
    "fields": null
  },
  "closure_type": "close-by-user"
}""",
    ),

    "search_app": dict(
        id="search_app",
        method_badge="SEARCH APP",
        method_color="#0077CC",
        title="Elastic Search Application — One API Endpoint for Hybrid Search",
        outcome=(
            "One clean API endpoint wraps ELSER semantic search, BM25 keyword search, "
            "RRF fusion, query rules, and synonyms. Your developers integrate in hours, "
            "not weeks."
        ),
        kibana_path=(
            "**Enterprise Search → Search Applications → `{demo}-search-app`**\n\n"
            "Click **Preview** to show live search\n\n"
            "Click **API** tab to show the single endpoint your developers use:\n"
            "`POST /_application/search_application/{demo}-search-app/_search`\n\n"
            "Browse → Search Stack → Search Preview — live in the demo builder"
        ),
        talk_track=(
            "Your developers get one endpoint. They send a query, they get ranked results. "
            "The ELSER model, the BM25, the RRF fusion, the query rules — all invisible. "
            "It just works. And when you want to tune relevance, "
            "you change a slider here — no code deployment required."
        ),
        yaml_label="Search Application Query",
        yaml_body="""# Query the Search Application (what your app calls)
POST /_application/search_application/{demo_slug}-search-app/_search
{
  "params": {
    "query": "prior authorization denied diabetes",
    "size": 10
  }
}

# Response — RRF-fused results ranked by relevance
{
  "hits": {
    "total": { "value": 342 },
    "hits": [
      {
        "_score": 0.97,
        "_index": "{demo_slug}-knowledge-base",
        "_source": {
          "title": "Prior Authorization Policy — Endocrine Disorders",
          "content": "Type 2 diabetes medications require PA when...",
          "category": "policy",
          "last_updated": "2026-01-15"
        }
      }
      # ... more results
    ]
  }
}

---

# Query Rules — pin specific results for key queries
PUT _query_rules/{demo_slug}-query-rules
{
  "rules": [
    {
      "rule_id": "pin-0",
      "type": "pinned",
      "criteria": [
        {
          "type": "fuzzy",
          "metadata": "query",
          "values": ["prior authorization", "PA request", "pre-auth"]
        }
      ],
      "actions": {
        "ids": ["policy-doc-pa-001"]
      }
    }
  ]
}""",
    ),

    "search_agent": dict(
        id="search_agent",
        method_badge="AI AGENT",
        method_color="#7B2FBE",
        title="AI Agent — Domain-Aware Assistant Over Your Data",
        outcome=(
            "Your customers and staff get an AI assistant that knows your data, "
            "your policies, and your domain — not a generic chatbot. "
            "Questions answered in seconds instead of hours of manual search."
        ),
        kibana_path=(
            "**Stack Management → Agent Builder → select deployed agent → Test**\n\n"
            "Ask: *'What are the top denial reasons this month?'*\n"
            "Ask: *'Show me all claims over $10,000 denied in Q1'*\n"
            "Ask: *'Which policy covers cardiac rehabilitation?'*\n\n"
            "The agent runs ES|QL queries against your indexed data and returns grounded answers."
        ),
        talk_track=(
            "This agent knows your data. Ask it a question your team asks every day. "
            "It doesn't hallucinate — every answer is grounded in your Elasticsearch data. "
            "You can see exactly which documents it used, what query it ran, "
            "and how it arrived at the answer."
        ),
        yaml_label="Agent Builder Configuration",
        yaml_body="""# Agent deployed via Kibana Agent Builder API
POST /api/agent_builder/agents
{
  "agent_id": "{demo_slug}_agent",
  "name": "{Company} {Department} Assistant",
  "description": "AI assistant for {Department} — powered by your Elasticsearch data",
  "system_prompt": "You are an expert {domain} assistant for {Company}...",
  "tools": [
    {
      "tool_id": "{demo_slug}_top_queries",
      "name": "Top Search Queries",
      "description": "Returns the most frequent search queries in the last 7 days",
      "query": "FROM {demo_slug}-knowledge-base | STATS count = COUNT() BY query | SORT count DESC | LIMIT 10"
    },
    {
      "tool_id": "{demo_slug}_error_analysis",
      "name": "Error Rate Analysis",
      "description": "Returns error rate breakdown by category",
      "query": "FROM {demo_slug}-knowledge-base | WHERE status_code != 200 | STATS errors = COUNT() BY category | SORT errors DESC"
    },
    {
      "tool_id": "{demo_slug}_latency_p95",
      "name": "P95 Latency by Service",
      "description": "Returns P95 latency percentile per service",
      "query": "FROM {demo_slug}-knowledge-base | STATS p95 = PERCENTILE(response_time_ms, 95) BY service_name | SORT p95 DESC"
    }
  ],
  "avatar_symbol": "{initials}",
  "labels": ["{demo_slug}", "demo-builder"]
}""",
    ),

    "search_api_key": dict(
        id="search_api_key",
        method_badge="SECURITY",
        method_color="#3DAE2B",
        title="Scoped API Key — Customer Takes It Away and Tests Themselves",
        outcome=(
            "Every customer gets a read-only, index-scoped API key at the end of the demo. "
            "They can query your Elastic environment with their own tools — "
            "Postman, curl, their app — before signing. "
            "Confidence accelerates the deal."
        ),
        kibana_path=(
            "**Browse → Search Stack → Infrastructure** — key shown with copy button\n\n"
            "**Stack Management → API Keys** — shows the scoped key with permissions\n\n"
            "Share with the customer: *'Here's a 30-day read-only key to your demo environment. "
            "Query it from Postman, from your app, from anywhere.'"
        ),
        talk_track=(
            "Take this API key. Point it at your Elasticsearch cluster from your own application. "
            "It's scoped to this demo's index only — read-only, 30-day expiry. "
            "This is exactly how your developers would integrate. "
            "You don't need to trust our demo — test it yourself."
        ),
        yaml_label="Scoped API Key + Role",
        yaml_body="""# Scoped read-only API key
# Auto-created by Search Stack provisioning

POST /_security/api_key
{
  "name": "{demo_slug}-demo-readonly",
  "expiration": "30d",
  "role_descriptors": {
    "{demo_slug}-search-role": {
      "indices": [
        {
          "names": ["{demo_slug}-knowledge-base", "{demo_slug}-events"],
          "privileges": ["read", "view_index_metadata"]
        }
      ],
      "cluster": ["monitor"]
    }
  }
}

# Response — give this to the customer
{
  "id": "abc123...",
  "name": "{demo_slug}-demo-readonly",
  "expiration": 1748390400000,
  "api_key": "...",
  "encoded": "YWJjMTIz..."   # ← base64(id:api_key) — use this in Authorization header
}

# Customer uses it like this:
curl -X GET "{elastic_endpoint}/{demo_slug}-knowledge-base/_search" \
  -H "Authorization: ApiKey YWJjMTIz..." \
  -H "Content-Type: application/json" \
  -d '{"query": {"match": {"content": "prior authorization"}}}'""",
    ),

    # ── Observability ────────────────────────────────────────────────────────

    "obs_apm": dict(
        id="obs_apm",
        method_badge="APM",
        method_color="#00BFB3",
        title="APM — Root Cause in 60 Seconds, Not 6 Hours",
        outcome=(
            "MTTR goes from hours to minutes. Engineers stop guessing and start knowing. "
            "From a spike on the service map to the offending span in under 60 seconds."
        ),
        kibana_path=(
            "**Observability → Service Map** — shows dependency graph, click a degraded service\n\n"
            "**Observability → Services → {service name} → Transactions** — drill into slow spans\n\n"
            "**Discover** — correlate trace ID with the error log line\n\n"
            "Browse → Service Map tab — auto-generated from APM demo data"
        ),
        talk_track=(
            "A customer reports slow checkout. Your on-call engineer opens the service map. "
            "Checkout is red. They click it — see it depends on the payment service. "
            "Payment service P95 is 8 seconds. They click the slowest trace — "
            "it's a database query that's missing an index. "
            "60 seconds from symptom to root cause."
        ),
        yaml_label="APM Data Stream + ES|QL Correlation",
        yaml_body="""# APM uses data streams — auto-created by Elastic APM Server
# Index pattern: traces-apm-*, logs-apm-*, metrics-apm-*

# ES|QL: Correlate slow traces with error logs
FROM traces-apm-*
| WHERE @timestamp >= NOW() - 1 HOUR
| WHERE transaction.duration.us > 5000000   // > 5 seconds
| EVAL service = service.name,
         trace = trace.id,
         duration_s = ROUND(transaction.duration.us / 1000000, 2)
| KEEP service, trace, duration_s, transaction.name
| SORT duration_s DESC
| LIMIT 20

---

# Cross-signal: find logs for a slow trace
FROM logs-apm-*
| WHERE trace.id == "abc123def456..."
| WHERE log.level == "error"
| KEEP @timestamp, service.name, message, error.message
| SORT @timestamp DESC

---

# SLO definition (auto-generated for APM demos)
POST /api/observability/slos
{
  "name": "{service_name} — Availability SLO",
  "description": "99.9% of requests succeed within 2 seconds",
  "indicator": {
    "type": "sli.apm.transactionDuration",
    "params": {
      "service": "{service_name}",
      "environment": "production",
      "transactionType": "request",
      "threshold": 2000,
      "index": "metrics-apm.*"
    }
  },
  "timeWindow": { "duration": "30d", "type": "rolling" },
  "budgetingMethod": "occurrences",
  "objective": { "target": 0.999 }
}""",
    ),

    "obs_slo": dict(
        id="obs_slo",
        method_badge="SLO",
        method_color="#FEC514",
        title="SLOs — Know About a Breach 30 Minutes Before It Happens",
        outcome=(
            "You know about an SLO breach while you still have budget to fix it. "
            "Burn rate alerts fire before the SLO is actually breached. "
            "Error budget consumed? Alert fires. Team investigates. SLO saved."
        ),
        kibana_path=(
            "**Observability → SLOs** — shows all SLOs with burn rate and remaining budget\n\n"
            "Click an SLO → shows burn rate chart, error budget history\n\n"
            "**Observability → Alerts** → filter by SLO — burn rate alert fires before breach"
        ),
        talk_track=(
            "Your SLO says 99.9% of requests succeed in under 2 seconds. "
            "Your error budget is 43 minutes of downtime per month. "
            "Right now you're burning it at 14x the normal rate — "
            "you'll breach in 3 minutes, not 43. "
            "Your team gets that alert now, not after the breach."
        ),
        yaml_label="SLO + Burn Rate Alert",
        yaml_body="""# SLO Definition
POST /api/observability/slos
{
  "name": "{service} — Latency SLO",
  "indicator": {
    "type": "sli.apm.transactionDuration",
    "params": {
      "service": "{service_name}",
      "environment": "production",
      "transactionType": "request",
      "threshold": 2000,
      "index": "metrics-apm.*,metrics-*.otel-*"
    }
  },
  "timeWindow": { "duration": "30d", "type": "rolling" },
  "budgetingMethod": "occurrences",
  "objective": { "target": 0.999 },
  "settings": {
    "syncDelay": "1m",
    "frequency": "1m"
  }
}

---

# Burn Rate Alert (auto-created with SLO)
# Fires when burning budget 14x faster than sustainable rate
POST /api/alerting/rule
{
  "name": "{service} SLO Breach — Burn Rate Alert",
  "rule_type_id": "slo.rules.burnRate",
  "schedule": { "interval": "1m" },
  "params": {
    "sloId": "{slo_uuid}",
    "windows": [
      {
        "id": "critical",
        "burnRateThreshold": 14.4,
        "maxBurnRateThreshold": 720,
        "longWindow": { "value": 1, "unit": "h" },
        "shortWindow": { "value": 5, "unit": "m" },
        "actionGroup": "slo.burnRate.alert"
      }
    ]
  }
}""",
    ),

    "obs_motlp": dict(
        id="obs_motlp",
        method_badge="MOTLP",
        method_color="#00BFB3",
        title="Managed OTLP — Native OpenTelemetry, Zero Infrastructure",
        outcome=(
            "Point your existing OpenTelemetry SDK at Elastic Cloud. "
            "No collector, no agents, no ECS mapping. "
            "Your telemetry, your field names, full fidelity."
        ),
        kibana_path=(
            "**Discover → index: `traces-generic.otel-default`**\n\n"
            "Show fields: `TraceId`, `SpanId`, `Duration`, `resource.attributes.service.name`\n\n"
            "These are **native OTLP field names** — no transformation, no ECS mapping.\n\n"
            "**Stack Management → Index Management → Data Streams** → filter `generic.otel`"
        ),
        talk_track=(
            "You're already using OpenTelemetry. "
            "Set one environment variable — OTEL_EXPORTER_OTLP_ENDPOINT — "
            "point it at Elastic Cloud, add your API key header. "
            "Done. Your traces, metrics, and logs appear here in their native OTLP format. "
            "No collector to run, no ECS mapping to maintain."
        ),
        yaml_label="MOTLP SDK Configuration",
        yaml_body="""# SDK Configuration — any OpenTelemetry-compatible SDK
# Just set these environment variables:

OTEL_EXPORTER_OTLP_ENDPOINT=https://{cluster_id}.apm.us-central1.gcp.cloud.es.io
OTEL_EXPORTER_OTLP_HEADERS=Authorization=ApiKey {base64_api_key}
OTEL_SERVICE_NAME=checkout-service
OTEL_RESOURCE_ATTRIBUTES=data_stream.dataset=checkout,deployment.environment=production

# That's it. Data appears at:
# traces-generic.otel-default
# metrics-generic.otel-default
# logs-generic.otel-default

---

# Verify ingestion via ES|QL
FROM traces-generic.otel-default
| WHERE resource.attributes.service.name == "checkout-service"
| WHERE @timestamp >= NOW() - 1 HOUR
| STATS
    avg_duration = AVG(Duration),
    p95_duration = PERCENTILE(Duration, 95),
    error_rate   = COUNT(CASE WHEN StatusCode == "STATUS_CODE_ERROR" THEN 1 END) / COUNT(*) * 100
  BY SpanName
| SORT p95_duration DESC
| LIMIT 20

---

# Native OTLP document structure (no ECS translation)
{
  "TraceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "SpanId": "00f067aa0ba902b7",
  "ParentSpanId": "00f067aa0ba902b7",
  "SpanName": "POST /api/checkout",
  "Duration": 245000000,       # nanoseconds
  "StatusCode": "STATUS_CODE_OK",
  "resource.attributes.service.name": "checkout-service",
  "resource.attributes.deployment.environment": "production",
  "data_stream.dataset": "checkout",
  "data_stream.namespace": "default",
  "data_stream.type": "traces"
}""",
    ),

    # ── Security ─────────────────────────────────────────────────────────────

    "sec_detection": dict(
        id="sec_detection",
        method_badge="DETECT",
        method_color="#F04E98",
        title="Detection Rules — Find Real Threats, Filter the Noise",
        outcome=(
            "Mean time to detect goes from days to minutes. "
            "Your analysts focus on real threats — the noise is ML-filtered. "
            "Every alert has full context: host, user, process tree, network."
        ),
        kibana_path=(
            "**Security → Rules → Detection Rules** — show generated rules\n\n"
            "**Security → Alerts** — filter by severity: Critical / High\n\n"
            "Click an alert → **Analyzer** → show process tree\n\n"
            "Browse → Live Replay → inject **Attack** scenario → watch alerts fire live"
        ),
        talk_track=(
            "This detection rule fires when it sees 5 failed logins followed by a success "
            "from a new IP — that's a credential stuffing attack. "
            "Your analysts get the alert with the full context: "
            "who the user is, what host, what process, what they did after login. "
            "No pivoting across 6 tools. Everything in one timeline."
        ),
        yaml_label="Detection Rule (SIEM)",
        yaml_body="""# Detection Rule — Brute Force Followed by Success
# Auto-generated for Security demos

POST /api/detection_engine/rules
{
  "name": "{Company} — Credential Stuffing: Brute Force then Success",
  "description": "Multiple failed logins followed by a successful login from a new IP",
  "risk_score": 73,
  "severity": "high",
  "type": "eql",
  "language": "eql",
  "query": "
    sequence by user.name with maxspan=10m
      [authentication where event.outcome == 'failure'] with runs=5
      [authentication where event.outcome == 'success' and
       not source.ip in (known_good_ips)]
  ",
  "index": ["logs-*", "filebeat-*", "winlogbeat-*"],
  "tags": ["{demo_slug}", "brute-force", "credential-access", "T1110"],
  "references": ["https://attack.mitre.org/techniques/T1110/"],
  "threat": [
    {
      "framework": "MITRE ATT&CK",
      "tactic": { "id": "TA0006", "name": "Credential Access" },
      "technique": [{ "id": "T1110", "name": "Brute Force" }]
    }
  ],
  "actions": [
    {
      "id": "{connector_id}",
      "action_type_id": ".slack",
      "params": {
        "message": "🚨 *{Company} Security Alert*\\nCredential stuffing detected: {{context.rule.name}}\\nUser: {{context.user.name}} | IP: {{context.source.ip}}"
      }
    }
  ]
}

---

# Lateral Movement Detection
POST /api/detection_engine/rules
{
  "name": "{Company} — Lateral Movement: Unusual Internal Connection",
  "type": "threshold",
  "query": "event.category: network and event.type: connection and network.direction: internal",
  "threshold": { "field": ["destination.ip"], "value": 20 },
  "risk_score": 47,
  "severity": "medium"
}""",
    ),

    "sec_cases": dict(
        id="sec_cases",
        method_badge="CASES",
        method_color="#F04E98",
        title="Cases — Every Alert Becomes an Investigation with Full Audit Trail",
        outcome=(
            "Your next SOC 2 or ISO 27001 audit is a 10-minute exercise, not a 3-week scramble. "
            "Every alert, investigation step, and resolution is recorded automatically."
        ),
        kibana_path=(
            "**Security → Cases** — show auto-created case from a fired detection rule\n\n"
            "Click a case → show: linked alerts, timeline, comments, assignee, status\n\n"
            "**Stack Management → Audit Logs** — show the full action trail\n\n"
            "Filter cases by `tags: demo-builder` to show only demo cases"
        ),
        talk_track=(
            "When this detection rule fired, a Case was automatically created. "
            "The analyst's investigation steps are recorded here. "
            "The alert that triggered it is linked. "
            "The resolution is documented. "
            "When your auditor asks 'show me how you handled this incident', "
            "this is your answer — one click."
        ),
        yaml_label="Case + Timeline Workflow",
        yaml_body="""# Case auto-created when detection rule fires
# Kibana Cases API

POST /api/cases
{
  "title": "Credential Stuffing Attempt — {user.name} from {source.ip}",
  "description": "Detection rule fired: 5 failed logins followed by success from new IP.\\nUser: {user.name} | Source IP: {source.ip} | Host: {host.name}",
  "severity": "high",
  "status": "open",
  "tags": ["{demo_slug}", "brute-force", "T1110"],
  "connector": {
    "id": "{connector_id}",
    "name": "Slack",
    "type": ".slack",
    "fields": null
  },
  "settings": { "syncAlerts": true }
}

# Link alert to case
POST /api/cases/{case_id}/alerts
{
  "alert_id": "{alert_id}",
  "index": ".internal.alerts-security.alerts-default-000001",
  "rule": {
    "id": "{rule_id}",
    "name": "Credential Stuffing: Brute Force then Success"
  }
}

# Add investigation comment
POST /api/cases/{case_id}/comments
{
  "type": "user",
  "comment": "Confirmed source IP {source.ip} is not in any approved VPN range.\\nBlocking at firewall and resetting {user.name} credentials.\\nEscalating to Tier 2."
}

# Audit log entry (automatic — every action recorded)
GET /api/security/audit/events?type=case_create,case_update,alert_linked
{
  "events": [
    {
      "timestamp": "2026-03-21T07:45:23Z",
      "user": "analyst@company.com",
      "action": "case_create",
      "outcome": "success",
      "case_id": "{case_id}"
    }
  ]
}""",
    ),

    "sec_agent": dict(
        id="sec_agent",
        method_badge="AI SOC",
        method_color="#7B2FBE",
        title="AI Security Analyst — Tier 1 Does the Work of Tier 2",
        outcome=(
            "Tier 1 analysts answer questions that used to require Tier 2. "
            "Your senior analysts focus on threat hunting, not triage. "
            "Every answer is grounded in your SIEM data — no hallucination."
        ),
        kibana_path=(
            "**Stack Management → Agent Builder → {Company} Security Assistant → Test**\n\n"
            "Ask: *'Show me all brute force attempts in the last 4 hours'*\n"
            "Ask: *'Which hosts have unusual outbound traffic?'*\n"
            "Ask: *'Summarize the open critical alerts'*"
        ),
        talk_track=(
            "Your Tier 1 analyst asks: 'Show me all critical alerts from the last hour'. "
            "The agent runs the ES|QL query, returns the answer with context. "
            "They ask: 'Is this IP known malicious?' — it checks threat intel. "
            "They ask: 'What else did this user do?' — it correlates across logs. "
            "They resolve in 10 minutes what used to take 2 hours."
        ),
        yaml_label="Security Agent Tools",
        yaml_body="""# Security Agent — ES|QL tools grounded in real SIEM data

POST /api/agent_builder/agents
{
  "agent_id": "{demo_slug}_security_agent",
  "name": "{Company} Security Operations Assistant",
  "system_prompt": "You are an expert security analyst for {Company}. Use the provided tools to investigate alerts, correlate events, and support incident response. Always cite the data source for every finding.",
  "tools": [
    {
      "tool_id": "critical_alerts",
      "name": "Critical Alerts — Last Hour",
      "query": "FROM .alerts-security.alerts-default-* | WHERE @timestamp >= NOW() - 1 HOUR | WHERE kibana.alert.severity == 'critical' | KEEP @timestamp, kibana.alert.rule.name, host.name, user.name, source.ip | SORT @timestamp DESC | LIMIT 20"
    },
    {
      "tool_id": "brute_force_summary",
      "name": "Brute Force Attempts — Last 4 Hours",
      "query": "FROM logs-* | WHERE @timestamp >= NOW() - 4 HOURS | WHERE event.category == 'authentication' AND event.outcome == 'failure' | STATS attempts = COUNT(), unique_users = COUNT_DISTINCT(user.name) BY source.ip | WHERE attempts > 10 | SORT attempts DESC"
    },
    {
      "tool_id": "unusual_outbound",
      "name": "Unusual Outbound Traffic",
      "query": "FROM logs-* | WHERE event.category == 'network' AND network.direction == 'outbound' | WHERE destination.ip NOT IN ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16') | STATS bytes = SUM(network.bytes), connections = COUNT() BY source.ip, destination.ip | WHERE connections > 100 | SORT bytes DESC"
    },
    {
      "tool_id": "user_activity",
      "name": "User Activity Timeline",
      "query": "FROM logs-* | WHERE user.name == '{{user_name}}' | WHERE @timestamp >= NOW() - 24 HOURS | KEEP @timestamp, event.category, event.action, host.name, source.ip | SORT @timestamp DESC | LIMIT 50"
    }
  ]
}""",
    ),

    # ── Platform ─────────────────────────────────────────────────────────────

    "platform_pipeline": dict(
        id="platform_pipeline",
        method_badge="PIPELINE",
        method_color="#3DAE2B",
        title="Ingest Pipeline — Data Enriched and AI-Ready at Index Time",
        outcome=(
            "Every document is ML-enriched, geo-located, PII-redacted, and timestamped "
            "before it hits the index. Zero post-processing. "
            "Search quality is built in, not bolted on."
        ),
        kibana_path=(
            "**Stack Management → Ingest Pipelines → `{demo_slug}-elser-pipeline`**\n\n"
            "Show the processors: ELSER inference → PII redaction → timestamp\n\n"
            "**Dev Tools**: `GET _ingest/pipeline/{demo_slug}-elser-pipeline`"
        ),
        talk_track=(
            "Every document runs through this pipeline on the way in. "
            "ELSER generates the semantic tokens — you never see them, "
            "they're stored alongside your content. "
            "PII is redacted before storage. "
            "No batch job, no nightly re-index, no Lambda function. "
            "It happens at ingestion time, every time."
        ),
        yaml_label="Full Ingest Pipeline",
        yaml_body="""# Full ingest pipeline — ELSER + enrichment + PII redaction

PUT _ingest/pipeline/{demo_slug}-elser-pipeline
{
  "description": "ELSER semantic search + PII redaction pipeline",
  "processors": [
    # 1. ELSER ML inference for semantic fields
    {
      "inference": {
        "model_id": ".elser-2-elasticsearch",
        "input_output": [
          { "input_field": "content", "output_field": "ml.inference.content_expanded_terms" },
          { "input_field": "title",   "output_field": "ml.inference.title_expanded_terms"   }
        ],
        "on_failure": [
          { "append": { "field": "_source._ingest_errors", "value": "ELSER failed", "ignore_failure": true } }
        ]
      }
    },
    # 2. PII redaction (email, IP, phone, card numbers)
    {
      "redact": {
        "field": "content",
        "patterns": [
          "%{EMAILADDRESS:email}",
          "%{IP:ip_address}",
          "\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b",
          "\\b\\d{4}[- ]?\\d{4}[- ]?\\d{4}[- ]?\\d{4}\\b"
        ],
        "ignore_missing": true,
        "ignore_failure": true
      }
    },
    # 3. Geo-IP enrichment for IP fields
    {
      "geoip": {
        "field": "source.ip",
        "target_field": "geo.source",
        "ignore_missing": true,
        "ignore_failure": true
      }
    },
    # 4. Ingestion timestamp
    {
      "set": {
        "field": "_source.ingested_at",
        "value": "{{_ingest.timestamp}}",
        "ignore_failure": true
      }
    }
  ],
  "on_failure": [
    { "set": { "field": "event.kind", "value": "pipeline_error" } },
    { "append": { "field": "error.message", "value": "{{ _ingest.on_failure_message }}" } }
  ]
}""",
    ),

    "platform_ilm": dict(
        id="platform_ilm",
        method_badge="ILM",
        method_color="#3DAE2B",
        title="Index Lifecycle Management — Data Retention Without Manual Work",
        outcome=(
            "Hot data is fast and searchable. "
            "Warm data is compressed and cost-optimised. "
            "Cold data is archived to object storage — still searchable, pennies per GB. "
            "Deleted after 90 days, automatically. "
            "Your storage bill is controlled. Your auditors are happy."
        ),
        kibana_path=(
            "**Stack Management → Index Lifecycle Policies → `{demo_slug}-search-ilm`**\n\n"
            "Show the phases: Hot → Warm → Cold → Delete\n\n"
            "**Stack Management → Index Management** → show index age and phase"
        ),
        talk_track=(
            "You don't need to think about data retention. "
            "Hot for 7 days — full speed, full replicas. "
            "Warm after that — forcemerged, single shard, reduced cost. "
            "Cold after 30 days — searchable snapshot on object storage, "
            "1/10th the cost of hot. "
            "Deleted at 90 days — automatic, policy-driven, audit-ready."
        ),
        yaml_label="ILM Policy",
        yaml_body="""# ILM Policy — auto-created by Search Stack provisioning

PUT _ilm/policy/{demo_slug}-search-ilm
{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_age": "7d",
            "max_primary_shard_size": "10gb"
          },
          "set_priority": { "priority": 100 }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "forcemerge": { "max_num_segments": 1 },
          "shrink": { "number_of_shards": 1 },
          "set_priority": { "priority": 50 }
        }
      },
      "cold": {
        "min_age": "30d",
        "actions": {
          "searchable_snapshot": {
            "snapshot_repository": "found-snapshots"   # Elastic Cloud managed
          },
          "set_priority": { "priority": 0 }
        }
      },
      "delete": {
        "min_age": "90d",
        "actions": { "delete": {} }
      }
    }
  }
}

# Index template binding the ILM policy
PUT _index_template/{demo_slug}-search-template
{
  "index_patterns": ["{demo_slug}-*"],
  "composed_of": ["{demo_slug}-mappings", "{demo_slug}-settings"],
  "priority": 200
}

# Settings component template
PUT _component_template/{demo_slug}-settings
{
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "index.lifecycle.name": "{demo_slug}-search-ilm",
      "index.default_pipeline": "{demo_slug}-elser-pipeline"
    }
  }
}""",
    ),

    "platform_replay": dict(
        id="platform_replay",
        method_badge="LIVE",
        method_color="#FF6600",
        title="Live Replay Engine — Make Kibana Alerts Fire During Your Demo",
        outcome=(
            "Generated demo data is historical. Kibana Alerts check 'now-5m to now'. "
            "The Replay Engine bridges that gap — streaming your demo data with current timestamps "
            "so Alerts, Detection Rules, and Cases fire live in front of the customer."
        ),
        kibana_path=(
            "**Browse → ▶ Live Replay tab**\n\n"
            "1. Select dataset and index\n"
            "2. Choose scenario: Normal → Latency Spike → Error Storm → Attack\n"
            "3. Set events per second (5–20)\n"
            "4. Click ▶ Start\n"
            "5. Open Kibana Alerts in another tab — alerts fire within 5 minutes"
        ),
        talk_track=(
            "Let me show you what happens when something goes wrong. "
            "I'm going to inject an error storm scenario. "
            "Watch the dashboard — the error rate is climbing. "
            "In about 3 minutes, your on-call engineer gets a Slack message. "
            "Watch."
        ),
        yaml_label="Scenario Configuration",
        yaml_body="""# scenarios.json — auto-generated per demo
# Controls Live Replay scenario injection

[
  {
    "name": "Normal Operations",
    "description": "Baseline traffic — establishes healthy 'before' state",
    "trigger_after_seconds": 0,
    "duration_seconds": 0,
    "anomaly_type": "none",
    "severity": "info",
    "field_overrides": {},
    "expected_alerts": []
  },
  {
    "name": "Latency Spike",
    "description": "P95 latency jumps 3-5x for 10 minutes",
    "trigger_after_seconds": 60,
    "duration_seconds": 600,
    "anomaly_type": "latency_spike",
    "affected_service": "checkout-api",
    "severity": "high",
    "field_overrides": {
      "response_time_ms": { "multiply": 4.5 },
      "status_code": { "set": 504, "probability": 0.15 }
    },
    "expected_alerts": [
      "{Company} — High P95 Search Latency (fires in ~5 min)"
    ]
  },
  {
    "name": "Error Storm",
    "description": "Error rate spikes to 40%+ — alert fires, Case auto-created",
    "trigger_after_seconds": 30,
    "duration_seconds": 300,
    "anomaly_type": "error_surge",
    "severity": "critical",
    "field_overrides": {
      "status_code": { "set": 500, "probability": 0.45 },
      "error_message": { "set": "Internal server error — upstream timeout" }
    },
    "expected_alerts": [
      "{Company} — High Search Error Rate (fires in ~5 min)",
      "Kibana Case auto-created and assigned"
    ]
  },
  {
    "name": "Attack — Brute Force",
    "description": "Credential stuffing from new IP range",
    "trigger_after_seconds": 45,
    "duration_seconds": 480,
    "anomaly_type": "brute_force",
    "severity": "critical",
    "field_overrides": {
      "source.ip": { "set": "185.220.101.{random:1-254}" },
      "event.outcome": { "set": "failure", "probability": 0.85 },
      "event.category": { "set": "authentication" }
    },
    "expected_alerts": [
      "Credential Stuffing detection rule fires",
      "Security Alert created",
      "Slack notification sent"
    ]
  }
]

# Replay Engine — key settings
events_per_second: 10        # 10 docs/s = ~864k docs/day — realistic load
window_seconds: 30           # timestamps spread over last 30s
loop: true                   # loops forever until stopped
retimestamp_field: "@timestamp"   # field to overwrite with current time""",
    ),

    "platform_health": dict(
        id="platform_health",
        method_badge="HEALTH",
        method_color="#3DAE2B",
        title="Pre-Demo Health Check — 8-Point Checklist Before Every Demo",
        outcome=(
            "Nothing fails during a customer demo. "
            "30 minutes before showtime, run the health check. "
            "8 green checks — you're ready. "
            "Any red — fix it before the customer sees it."
        ),
        kibana_path=(
            "**Browse → Search Stack → Infrastructure → Run Health Check**\n\n"
            "8 checks run automatically:\n"
            "1. Index exists + has documents\n"
            "2. ELSER pipeline exists\n"
            "3. ELSER model started\n"
            "4. Search Application exists\n"
            "5. Kibana dashboard accessible\n"
            "6. Alert rules enabled\n"
            "7. Slack connector responding\n"
            "8. Scoped API key valid"
        ),
        talk_track="(Internal tool — use before the demo, not during)",
        yaml_label="Health Check Results",
        yaml_body="""# Health check results — saved to elastic_assets.json

{
  "overall": "ok",
  "checked_at": "2026-03-21T07:45:00Z",
  "items": [
    { "name": "{demo_slug}-knowledge-base", "status": "ok",      "message": "12,450 documents indexed" },
    { "name": "Pipeline: {demo_slug}-elser-pipeline", "status": "ok",   "message": "Pipeline exists" },
    { "name": "ELSER model",         "status": "ok",      "message": "Started on 2 node(s)" },
    { "name": "Search App: {demo_slug}-search-app", "status": "ok", "message": "Search Application exists" },
    { "name": "Dashboard: {title}",  "status": "ok",      "message": "Exists in Kibana" },
    { "name": "Alert: High P95 Latency", "status": "ok",  "message": "Active" },
    { "name": "Alert: High Error Rate",  "status": "ok",  "message": "Active" },
    { "name": "Slack connector",     "status": "ok",      "message": "Connector configured" },
    { "name": "Scoped API key",      "status": "ok",      "message": "Valid — expires: 2026-04-20" }
  ]
}

# If any item is "warning" or "error":
# - ELSER not started → ML → Trained Models → start .elser-2-elasticsearch
# - Index empty       → Data tab → re-index datasets
# - Dashboard missing → Search Stack → Re-provision
# - Alert disabled    → Observability → Alerts → Rules → enable
# - Slack failing     → check SLACK_WEBHOOK_URL in .env""",
    ),
}
