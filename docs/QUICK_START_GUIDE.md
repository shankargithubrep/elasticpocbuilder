# Elastic Demo Builder — Quick Start Guide

> For the outcome-based demo script and Kibana navigation reference, see
> [OUTCOME_BASED_DEMO_GUIDE.md](OUTCOME_BASED_DEMO_GUIDE.md)

---

## Launch the App

```bash
source venv/bin/activate
streamlit run app.py
# → http://localhost:8501
```

---

## Environment Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

### Required `.env` keys

```bash
# LLM (choose one)
ANTHROPIC_API_KEY=sk-ant-...

# Elasticsearch
ELASTICSEARCH_CLOUD_ID=...
ELASTICSEARCH_API_KEY=...

# Kibana (required for Agent Builder + dashboards + alerting)
ELASTICSEARCH_KIBANA_URL=https://your-cluster.kb.us-central1.gcp.cloud.es.io

# Slack (optional — enables Slack alerts)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_CHANNEL=#elastic-demos
```

---

## Two Modes

### Create Mode
Generate a new demo from a customer description.

1. Click **Create** in the sidebar
2. Select a **Pillar**: Search / Observability / Security
3. Paste your customer description
4. Click **Generate Demo**
5. Watch real-time progress: Data → Queries → Guide → Stack Provisioning

### Browse Mode
View, manage, and present generated demos.

1. Click **Browse** in the sidebar
2. Select a demo from the list
3. Navigate the tabs:

| Tab | What it does |
|---|---|
| 📋 Config | Customer context, generation settings |
| 🗂️ Data | Index datasets into Elasticsearch |
| 🔍 Queries | Validate and run ES\|QL queries |
| 🔍 Search Stack | *(Search only)* Full stack: dashboard, alerts, Search App, health check |
| 🛡️ Detection Rules | *(Security only)* SIEM detection rules |
| 📡 Service Map | *(Observability only)* APM service dependency map |
| 🔧 Tools | Agent Builder tool definitions |
| 🤖 Agents | Deploy AI Agent to Kibana Agent Builder |
| ▶ Live Replay | Stream live data to trigger Kibana Alerts in real time |
| 📝 Guide | Presenter talk track and demo narrative |

---

## What Gets Auto-Created for Search Demos

When you generate a **Search** demo, the following are automatically provisioned in your Elastic cluster:

| Asset | Description |
|---|---|
| ELSER ingest pipeline | ML inference on semantic fields |
| ILM policy | Hot 7d → Warm → Delete 90d |
| Index template | Component templates with proper mappings |
| Search Application | RRF hybrid search (BM25 + ELSER) |
| Synonyms set | Industry-specific vocabulary |
| Kibana dashboard | P50/P95/P99 latency, query volume, error rate, top terms |
| Slack connector | Wired to alert rules |
| P95 latency alert | Fires when response time exceeds threshold |
| Error rate alert | Fires when error count spikes |
| Cases configuration | Alert → auto-create Kibana Case |
| Discover saved view | Pre-filtered view of the demo data |
| Scoped API key | Read-only key for customer self-testing (30-day expiry) |
| elastic_assets.json | Full manifest of everything created |

All provisioning is **idempotent** — safe to re-run via the Re-provision button.

---

## Pillar Sub-Categories

### Search
- **Search / RAG** — document retrieval, semantic search, knowledge base, RAG applications

### Observability
- **APM** — application performance, traces, service maps
- **Infrastructure** — host metrics, Kubernetes, cloud
- **SLO** — service level objectives and error budgets
- **MOTLP (Managed OTLP)** — native OpenTelemetry ingestion, no collector required

### Security
- **SIEM** — threat detection, investigation, response
- Generates detection rules, realistic attack scenarios, case management

---

## Live Replay

The Live Replay engine streams demo data with current timestamps into Elasticsearch, making Kibana Alerts and Detection Rules fire in real time.

1. Browse → **▶ Live Replay** tab
2. Select dataset and index name
3. Choose a scenario:
   - **Normal Operations** — baseline (establish "before" state)
   - **Latency Spike** — P95 jumps → latency alert fires
   - **Error Storm** — error rate spikes → error alert fires → Case created
   - **SLO Breach** — burn rate consumed → SLO alert fires
   - **Attack** — brute force / lateral movement → detection rule fires
4. Set events per second (5–20 recommended for demos)
5. Click **▶ Start** — alerts fire in Kibana within 5 minutes

---

## Writing a Good Customer Description

Include all of the following for the best demo output:

```
Company: Acme Insurance
Department: Claims Processing
Industry: Health Insurance

Pain Points:
- Adjusters spend 3 hours/day searching for policy documents across 5 systems
- Denial decisions are inconsistent because staff can't quickly find precedent cases
- No visibility into which policies are searched most — or which return zero results

Use Cases:
- Semantic search across policies, claims, and medical guidelines
- AI assistant for adjusters to get instant answers from policy documents
- Search analytics to identify knowledge gaps and content quality issues

Scale: 2,000 adjusters, 5 million policy documents, 50,000 searches/day

Key Metrics: search response time, zero-result rate, adjuster handle time, denial accuracy
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| ELSER inference fails | Machine Learning → Trained Models → start `.elser-2-elasticsearch` |
| Dashboard not showing | Search Stack → Re-provision |
| Agent deploy fails | Check `ELASTICSEARCH_KIBANA_URL` in `.env` — must include `:443` |
| Queries return 0 results | Data tab → re-index datasets |
| Slack alerts not firing | Check `SLACK_WEBHOOK_URL` in `.env`, run Health Check |
| Live Replay not indexing | Verify index name matches what's in Elasticsearch |

---

## File Structure

```
demos/{company}_{dept}_{timestamp}/
├── config.json              # Customer context + generation settings
├── data_generator.py        # LLM-generated data generation code
├── query_generator.py       # LLM-generated ES|QL queries
├── demo_guide.py            # LLM-generated talk track
├── all_queries.json         # All generated queries with metadata
├── query_strategy.json      # Full query strategy from LLM
├── elastic_assets.json      # Provisioned asset manifest (Search demos)
├── scenarios.json           # Live Replay scenarios
└── agent_metadata.json      # Agent Builder configuration
```

---

*Elastic Demo Builder — Built by the Elastic Solutions Architecture Team*
