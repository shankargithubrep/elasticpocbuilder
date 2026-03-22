# Elastic Demo Builder — Outcome-Based Demo Guide

> **Philosophy**: Every demo we run should answer one customer question:
> *"What business outcome does Elastic deliver for me?"*
>
> This guide maps every feature of the Elastic Demo Builder to a specific
> customer outcome, and shows exactly where in Kibana to point during the demo.

---

## Table of Contents

1. [What This Tool Does](#1-what-this-tool-does)
2. [The Three Pillars](#2-the-three-pillars)
3. [Outcome Map — Search](#3-outcome-map--search)
4. [Outcome Map — Observability](#4-outcome-map--observability)
5. [Outcome Map — Security](#5-outcome-map--security)
6. [Running a Demo — Step by Step](#6-running-a-demo--step-by-step)
7. [Kibana Navigation Reference](#7-kibana-navigation-reference)
8. [Live Replay — Making Alerts Fire During Demos](#8-live-replay--making-alerts-fire-during-demos)
9. [Pre-Demo Checklist](#9-pre-demo-checklist)
10. [Talk Track Tips](#10-talk-track-tips)

---

## 1. What This Tool Does

The Elastic Demo Builder generates a **complete, customer-specific Elastic environment** from a single description of your customer's business problem. In under 20 minutes you go from a blank Elastic cluster to:

- Realistic data modelled on the customer's domain
- A working Search Application with ELSER semantic search
- Live Kibana dashboards showing P95 latency, query volume, and error rates
- Alerting rules wired to Slack
- A deployed AI Agent in Agent Builder pre-loaded with the customer's data
- A Live Replay engine that makes Kibana Alerts, Detection Rules, and Cases fire in real time during your demo

**What it is NOT**: a static slide deck or a scripted recording. Everything runs live against real Elasticsearch, so the customer sees their own domain reflected in the data.

---

## 2. The Three Pillars

| Pillar | Primary Buyer | Core Outcome |
|---|---|---|
| **Search** | CTO, Head of Product, VP Engineering | Find anything, instantly — across every system, every document, every knowledge base |
| **Observability** | VP Engineering, SRE Lead, Platform Engineering | Detect, investigate, and resolve incidents before customers are impacted |
| **Security** | CISO, SOC Manager, Head of Compliance | Detect threats faster, respond with confidence, meet every audit |

Choose the pillar that matches your customer's primary pain point. You can run all three in a single Elastic cluster.

---

## 3. Outcome Map — Search

### Outcome 1: "Find anything across all our systems — instantly"

**What we show**: A Search Application that searches across structured and unstructured data simultaneously, using both keyword and semantic (AI) search.

**How it works in the Demo Builder**:
- Select **Search** pillar → choose sub-type (Search/RAG)
- Generate demo → ELSER pipeline and Search Application auto-provisioned
- Open **Browse → Search Stack → Search Preview** tab
- Type a domain-specific query — e.g. *"claims denied for type 2 diabetes"*

**Where to show in Kibana**:
> Kibana → Enterprise Search → Search Applications → `{demo}-search-app`
> Click **Preview** → type queries → show semantic vs keyword toggle

**Customer outcome statement**:
> *"Your staff finds the right policy, case, or document in seconds instead of navigating five different systems. That's hours saved per employee per week."*

---

### Outcome 2: "Our search doesn't understand what our customers actually mean"

**What we show**: ELSER semantic search understands intent, not just keywords. A query for *"heart attack"* returns results about *"myocardial infarction"*. A query for *"refund"* returns results about *"returns and chargebacks"*.

**How it works in the Demo Builder**:
- Synonyms API set auto-created with industry-specific vocabulary
- ELSER inference pipeline auto-attached to the index
- Hybrid RRF search (BM25 + ELSER) weights tunable in the Search Preview tab

**Where to show in Kibana**:
> Kibana → Dev Tools → run the same query twice: once with `match`, once with `semantic`. Show the difference in results.
>
> Or: Search Stack → Search Preview → toggle **Semantic (ELSER)** on/off

**Customer outcome statement**:
> *"Elastic understands what your customers mean, not just what they type. Zero-result rates drop. Satisfaction scores go up."*

---

### Outcome 3: "We need to know if search is working — right now"

**What we show**: A live Kibana dashboard with P50/P95/P99 latency, query volume trends, top search terms, and error rate — all updating in real time.

**How it works in the Demo Builder**:
- Dashboard auto-created during provisioning
- Four panels: latency percentiles, query volume, top terms, error rate

**Where to show in Kibana**:
> Kibana → Dashboards → `{Company} — Search Performance Dashboard`
>
> Point to the **P95 latency panel** and say: *"If this line crosses your SLA threshold, your team gets a Slack alert within 5 minutes."*

**Customer outcome statement**:
> *"You know the moment search performance degrades — before a customer complains. P95 latency, error rates, query patterns — all in one place."*

---

### Outcome 4: "We need alerts when search breaks"

**What we show**: Two alerting rules fire automatically — one for high P95 latency, one for high error rate. Both trigger a Slack notification.

**How it works in the Demo Builder**:
- Alert rules auto-created (ES|QL threshold rules)
- Slack connector auto-wired
- Cases auto-created when an alert fires

**Where to show in Kibana**:
> Kibana → Observability → Alerts → show the two rules
>
> Kibana → Stack Management → Connectors → show Slack connector
>
> Use **Live Replay → Inject Scenario → Error Storm** to make the alert fire live

**Customer outcome statement**:
> *"The right person gets the right alert at the right time — in Slack, in PagerDuty, in Jira — without anyone manually watching a dashboard."*

---

### Outcome 5: "We want to give our customers an AI assistant over our content"

**What we show**: The deployed AI Agent in Elastic Agent Builder — pre-loaded with the customer's indexed data and ES|QL queries as tools.

**How it works in the Demo Builder**:
- Agent Builder tools auto-generated from the ES|QL queries
- Agent deployed directly from the **Agents** tab
- Agent has a custom persona, instructions, and domain knowledge

**Where to show in Kibana**:
> Kibana → Stack Management → Agent Builder → select the deployed agent → click **Test**
>
> Ask it a domain question — e.g. *"What are our top denial reasons this month?"*

**Customer outcome statement**:
> *"Your customers and staff get an AI assistant that knows your data, your policies, and your domain — not a generic chatbot."*

---

### Outcome 6: "We need to control who sees what"

**What we show**: A scoped, read-only API key generated for the demo — restricted to only the demo's indices, with optional document-level security.

**How it works in the Demo Builder**:
- Scoped API key auto-created with `read` privileges on demo indices only
- Key shown in Search Stack → Infrastructure tab
- Key has 30-day expiry

**Where to show in Kibana**:
> Kibana → Stack Management → API Keys → show the scoped key
>
> Kibana → Stack Management → Roles → show the search-only role definition

**Customer outcome statement**:
> *"Every user sees only what they're permitted to see. Compliance, governance, and data residency are built in — not bolted on."*

---

## 4. Outcome Map — Observability

### Outcome 1: "We can't find the root cause before the customer feels it"

**What we show**: APM traces, metrics, and logs correlated in a single view. From a spike on the service map to the offending span in under 60 seconds.

**How it works in the Demo Builder**:
- Select **Observability** pillar → APM or Infrastructure sub-category
- Service Map tab auto-generated with dependency graph
- Queries show cross-signal correlation (traces + logs + metrics)

**Where to show in Kibana**:
> Kibana → Observability → Service Map → click a degraded service
>
> Kibana → Observability → Traces → drill into the slowest transaction
>
> Kibana → Discover → correlate the trace ID with the error log

**Customer outcome statement**:
> *"MTTR goes from hours to minutes. You stop guessing, start knowing."*

---

### Outcome 2: "Our SLOs keep breaching and we don't know why"

**What we show**: SLO definitions with error budgets, burn rate alerts, and the ML anomaly that preceded the breach.

**How it works in the Demo Builder**:
- SLO scenario auto-generated in the observability strategy
- Live Replay → SLO Breach scenario streams anomalous data in real time

**Where to show in Kibana**:
> Kibana → Observability → SLOs → show burn rate
>
> Kibana → Observability → Alerts → show the SLO breach alert fired

**Customer outcome statement**:
> *"You know about an SLO breach 30 minutes before it happens — while you still have burn rate budget to fix it."*

---

### Outcome 3: "We want OpenTelemetry but don't want to manage the infrastructure"

**What we show**: Managed OTLP (MOTLP) — native OpenTelemetry ingestion into Elastic Cloud. No collector to manage, no ECS translation, native OTLP field names preserved.

**How it works in the Demo Builder**:
- Select **Observability → MOTLP (Managed OTLP)**
- Data generated with native OTLP fields: `TraceId`, `Duration`, `resource.attributes.*`
- Indexed to `traces-generic.otel-default`

**Where to show in Kibana**:
> Kibana → Discover → index: `traces-generic.otel-default`
>
> Show `TraceId`, `SpanId`, `resource.attributes.service.name` — native OTLP, zero transformation

**Customer outcome statement**:
> *"Point your existing OpenTelemetry SDK at Elastic Cloud. No collector, no agents, no ECS mapping. Your telemetry, your field names, full fidelity."*

---

## 5. Outcome Map — Security

### Outcome 1: "We're drowning in alerts and missing real threats"

**What we show**: Detection rules firing on realistic attack data — brute force, lateral movement, data exfiltration — with ML-based anomaly scoring to separate signal from noise.

**How it works in the Demo Builder**:
- Select **Security** pillar
- Detection rules auto-generated and deployed
- Live Replay → Attack scenario streams realistic threat data in real time

**Where to show in Kibana**:
> Kibana → Security → Alerts → filter by severity
>
> Kibana → Security → Rules → show the detection rule logic
>
> Click an alert → show the investigation timeline

**Customer outcome statement**:
> *"Your analysts focus on real threats. The noise is filtered. Mean time to detect goes from days to minutes."*

---

### Outcome 2: "We need to prove compliance — on demand"

**What we show**: Audit logs, case history, and automated evidence collection tied to every alert and investigation.

**How it works in the Demo Builder**:
- Cases auto-created when detection rules fire
- Every alert linked to the triggering data and rule

**Where to show in Kibana**:
> Kibana → Security → Cases → show an auto-created case with full timeline
>
> Kibana → Stack Management → Audit Logs → show the complete action trail

**Customer outcome statement**:
> *"Your next SOC 2 or ISO 27001 audit is a 10-minute exercise, not a 3-week scramble."*

---

### Outcome 3: "Our security team can't keep up with the volume"

**What we show**: The AI Agent deployed with security context — analysts ask it questions in plain English, it queries the data and surfaces findings.

**How it works in the Demo Builder**:
- Agent deployed with security-specific system prompt
- Tools based on ES|QL queries against security indices
- Agent knows the customer's environment

**Where to show in Kibana**:
> Kibana → Agent Builder → test the security agent
>
> Ask: *"Show me all brute force attempts in the last 4 hours"* or *"Which hosts have unusual outbound traffic?"*

**Customer outcome statement**:
> *"Tier 1 analysts do the work of Tier 2. Your senior analysts focus on hunting, not triage."*

---

## 6. Running a Demo — Step by Step

### Step 1: Generate the Demo (5 minutes)

1. Open the app: `streamlit run app.py` → `http://localhost:8501`
2. Click **Create**
3. Select the **Pillar** (Search / Observability / Security)
4. Paste a detailed customer description including:
   - Company name and industry
   - Department and team
   - Top 3 pain points
   - What they measure (KPIs/metrics)
   - Scale (number of users, records, events/day)
5. Click **Generate Demo**
6. Watch the progress: Data → Queries → Guide → Stack Provisioning

> **Pro tip**: The richer your description, the more relevant the data and queries. Include real field names, real metrics, real pain points from your discovery call.

---

### Step 2: Index Data and Provision the Stack (auto for Search)

**For Search demos** — this happens automatically during generation. The full stack is provisioned: ELSER pipeline, index templates, Search Application, dashboards, alerting rules.

**For Observability and Security demos** — click the **Data** tab → Index all datasets. Then come back to this guide for the remaining steps.

---

### Step 3: Run the Health Check

1. Browse → select your demo → **Search Stack** tab
2. Click **Run Health Check**
3. Verify all items are ✅ green before your demo

If anything is ⚠️ or ❌:
- ELSER not started → go to Kibana → Machine Learning → Trained Models → start `.elser-2-elasticsearch`
- Index empty → go to the **Data** tab and re-index
- Dashboard missing → click **Re-provision**

---

### Step 4: Validate Queries

1. Browse → **Queries** tab
2. Click **Run All Queries**
3. All queries should return results
4. Note the first 2-3 queries — these are your demo "aha moments"

---

### Step 5: Deploy the Agent

1. Browse → **Agents** tab
2. Review the agent name, description, and instructions
3. Click **Deploy Agent**
4. Go to Kibana → Agent Builder → test it with a domain question

---

### Step 6 (Optional): Start Live Replay

For demos where you want Kibana Alerts, Cases, and Detection Rules to fire live:

1. Browse → **Live Replay** tab
2. Select a dataset and index name
3. Choose a scenario: Normal → Latency Spike → Error Storm → SLO Breach → Attack
4. Set events per second (5–20 recommended)
5. Click **▶ Start Live Replay**
6. Open Kibana Alerts in another tab — alerts will fire within 5 minutes

---

### Step 7: Present

Follow the **Guide** tab for the full talk track. It's structured as:
- **Opening** — customer's pain point (personalized)
- **Discovery** — what the data shows
- **Aha moments** — the queries that prove the value
- **Call to action** — next steps

---

## 7. Kibana Navigation Reference

| What to Show | Kibana Path |
|---|---|
| Search Application (live search) | Enterprise Search → Search Applications |
| Search preview / test | Enterprise Search → Search Applications → Preview |
| Performance dashboard | Dashboards → `{Company} — Search Performance Dashboard` |
| P95/P99 latency | Dashboards → Latency Percentiles panel |
| Top search terms | Dashboards → Top Search Terms panel |
| Error rate | Dashboards → Error Rate Over Time panel |
| Alert rules | Observability → Alerts → Rules |
| Active alerts | Observability → Alerts |
| Slack connector | Stack Management → Connectors |
| Cases | Security → Cases (Security) or Observability → Cases |
| AI Agent | Stack Management → Agent Builder |
| ELSER model status | Machine Learning → Trained Models |
| Index data | Stack Management → Index Management |
| Data streams | Stack Management → Index Management → Data Streams |
| ILM policies | Stack Management → Index Lifecycle Policies |
| API Keys | Stack Management → API Keys |
| Audit logs | Stack Management → Audit Logs |
| Discover (raw data) | Discover → select index pattern |
| APM Service Map | Observability → Service Map |
| SLOs | Observability → SLOs |
| Detection Rules | Security → Rules |
| Security Alerts | Security → Alerts |
| MOTLP data | Discover → `traces-generic.otel-default` |

---

## 8. Live Replay — Making Alerts Fire During Demos

The Live Replay engine re-timestamps your generated demo data to `now` and streams it continuously into Elasticsearch. This makes Kibana Alerts, Detection Rules, and Cases fire in real time during your demo — not against 90-day-old historical data.

### Scenarios

| Scenario | What Happens | Alert That Fires |
|---|---|---|
| **Normal Operations** | Baseline traffic, healthy metrics | None — establishes the "before" state |
| **Latency Spike** | P95 latency jumps 3–5x for 10 minutes | High P95 Latency alert → Slack |
| **Error Storm** | Error rate spikes to 40%+ | High Error Rate alert → Slack → Case created |
| **SLO Breach** | Error budget consumed in minutes | SLO Burn Rate alert |
| **Attack / Brute Force** | Authentication failures from new IP range | Detection Rule fires → Security Alert |
| **DB Slowdown** | Database query latency cascades to API | Downstream latency alert |
| **Cascade Failure** | Multiple services degraded simultaneously | Multiple correlated alerts |

### Demo Script with Live Replay

1. Start with **Normal Operations** — show the healthy dashboard
2. Say: *"Now let me show you what happens when something goes wrong"*
3. Inject **Latency Spike** scenario
4. Watch the P95 panel climb in the dashboard (30s refresh)
5. Within 5 minutes — Slack alert fires
6. Show the Case auto-created in Kibana
7. Say: *"Your on-call engineer got a Slack message 4 minutes after the problem started. With Elastic, they would have been paged before a customer complained."*

---

## 9. Pre-Demo Checklist

Run this 30 minutes before every demo:

**App**
- [ ] App running: `streamlit run app.py`
- [ ] Demo selected in Browse mode
- [ ] Health Check all green ✅

**Elasticsearch**
- [ ] ELSER model started (Machine Learning → Trained Models)
- [ ] Rerank model started
- [ ] Index has documents (check Data tab)
- [ ] Queries return results (run all in Queries tab)

**Kibana**
- [ ] Dashboard loads and shows data
- [ ] Agent deployed and responding in Agent Builder
- [ ] Alert rules enabled (Observability → Alerts → Rules)
- [ ] Slack connector working (test it in Stack Management → Connectors)

**Live Replay (if using)**
- [ ] Index name matches the indexed data
- [ ] Normal scenario streaming (verify Events counter incrementing)
- [ ] Alert rules set to check `now-5m to now` (default for ES|QL rules)

---

## 10. Talk Track Tips

### Opening (30 seconds)
Don't open with Elasticsearch. Open with their problem.

> *"You mentioned in discovery that your support team spends 2 hours a day searching for policy documents across SharePoint, Confluence, and the ticketing system. That's 10 hours a week per analyst. Today I'm going to show you how that becomes a 30-second search."*

### The Aha Moment
Let the customer type a query. Don't type it yourself. When they see their domain's terminology surface the right result, they own the insight.

> *"What's a search your team does every day? Type it in here."*

### The Data Question
Customers always ask: *"Is this fake data?"*

> *"The structure and relationships in this data are modelled on your industry — the same field names, the same query patterns. The values are synthetic, but the demo shows you exactly what Elastic would do with your real data. And because this is code-generated, we can have your real data indexed here in the same time it took to set this up."*

### The Outcome Close
Every demo should end with a specific, measurable outcome.

> *"Based on what we've seen today: 30-second document retrieval instead of 2-hour searches. P95 latency monitoring with 5-minute alert response. An AI assistant that knows your policies and can answer your staff's questions. Which of these three would have the most impact for your team right now?"*

---

*Built by the Elastic Solutions Architecture Team — Elastic Demo Builder v2.0*
