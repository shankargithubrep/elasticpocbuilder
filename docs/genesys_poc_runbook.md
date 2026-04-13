# Genesys POC Runbook — Elastic Knowledge Base with DLS & Hybrid Retrieval

**Audience:** Solutions Architects, Pre-Sales Engineers
**Cluster:** Elastic Cloud (ES 8.14+ / 9.x) with Jina Embeddings v5 enabled via Elastic Inference Service
**Demo Time:** ~5 minutes for the scripted flow; full exploration can take 20-30 minutes

---

## Section 1 — Setup

### Prerequisites

- Python 3.10+ with virtual environment activated
- `elasticsearch` and `python-dotenv` packages installed
- A running Elastic cluster with:
  - Security enabled (X-Pack)
  - The `.jina-embeddings-v5-text-small` inference endpoint deployed
    (Elastic Inference Service — no separate ML node required on Elastic Cloud Enterprise 9.3+)

### Environment Variables

Create or update your `.env` file in the project root:

```bash
# Option A: Elastic Cloud (recommended)
ELASTICSEARCH_CLOUD_ID=your-cloud-id:dXMtZWFzdC0x...
ELASTICSEARCH_API_KEY=your-api-key-here

# Option B: Self-managed / on-prem
ELASTIC_ENDPOINT=https://your-cluster:9200
ELASTICSEARCH_API_KEY=your-api-key-here
```

The API key must have cluster-level privileges to manage indices, roles, and users.
A superuser key works for POC purposes.

### Run the Provisioner

```bash
# From the project root, with venv active:
python -m src.services.genesys_poc_provisioner
```

Expected output:

```
Creating index: kb_content ...
Creating index: kb_sync_events ...
Creating DLS roles ...
Creating demo users ...
Indexing kb_content documents ...
Indexing kb_sync_events ...
Provisioning complete.

Provisioning summary:
{
  "kb_content": "created",
  "kb_sync_events": "created",
  "roles": {
    "genesys_acme_agent": "ok",
    "genesys_globalnet_agent": "ok",
    "genesys_admin": "ok"
  },
  "users": {
    "alice_acme": "ok",
    "bob_globalnet": "ok",
    "admin_genesys": "ok"
  },
  "kb_content_docs": 60,
  "kb_sync_events_docs": 30
}
```

### Smoke-Test DLS After Provisioning

```bash
python -m src.services.genesys_poc_provisioner --verify-dls
```

Expected: Alice sees only `acme` documents; Bob sees only `globalnet` documents; admin sees both.

### Teardown

```bash
python -m src.services.genesys_poc_provisioner --teardown
```

This deletes `kb_content`, `kb_sync_events`, all three roles, and all three users.

---

## Section 2 — DLS Demo (The Money Moment)

This is the core differentiator: the **same query** against the **same index** returns **different documents** per user — enforced entirely at query time in Elasticsearch. Zero application-layer ACL drift.

Open Kibana → Dev Tools and run the blocks below in sequence.

### Demo Users Reference

| User | Username | Password | Tenant | Role |
|------|----------|----------|--------|------|
| Alice | `alice_acme` | `demo-acme-2026` | acme | `genesys_acme_agent` |
| Bob | `bob_globalnet` | `demo-globalnet-2026` | globalnet | `genesys_globalnet_agent` |
| Admin | `admin_genesys` | `demo-admin-2026` | all tenants | `genesys_admin` |

### Query 1 — "escalation procedure"

```
# As Alice (acme tenant only)
# Basic YWxpY2VfYWNtZTpkZW1vLWFjbWUtMjAyNg== = alice_acme:demo-acme-2026
GET kb_content/_search?pretty
Authorization: Basic YWxpY2VfYWNtZTpkZW1vLWFjbWUtMjAyNg==

{
  "query": {
    "match": {
      "content": "escalation procedure"
    }
  },
  "_source": ["tenant_id", "title", "source", "acl.principals"],
  "size": 5
}
```

Expected result: All hits have `tenant_id: "acme"`. Alice cannot see GlobalNet documents.

```
# As Bob (globalnet tenant only)
# Basic Ym9iX2dsb2JhbG5ldDpkZW1vLWdsb2JhbG5ldC0yMDI2 = bob_globalnet:demo-globalnet-2026
GET kb_content/_search?pretty
Authorization: Basic Ym9iX2dsb2JhbG5ldDpkZW1vLWdsb2JhbG5ldC0yMDI2

{
  "query": {
    "match": {
      "content": "escalation procedure"
    }
  },
  "_source": ["tenant_id", "title", "source", "acl.principals"],
  "size": 5
}
```

Expected result: All hits have `tenant_id: "globalnet"`. Bob cannot see Acme documents.

```
# As Admin (all tenants)
# Basic YWRtaW5fZ2VuZXN5czpkZW1vLWFkbWluLTIwMjY= = admin_genesys:demo-admin-2026
GET kb_content/_search?pretty
Authorization: Basic YWRtaW5fZ2VuZXN5czpkZW1vLWFkbWluLTIwMjY=

{
  "query": {
    "match": {
      "content": "escalation procedure"
    }
  },
  "_source": ["tenant_id", "title", "source"],
  "size": 10
}
```

Expected result: Mix of `acme` and `globalnet` documents — admin has no DLS restriction.

---

### Query 2 — "billing dispute resolution"

```
# Alice (acme only)
GET kb_content/_search?pretty
Authorization: Basic YWxpY2VfYWNtZTpkZW1vLWFjbWUtMjAyNg==

{
  "query": {
    "match": {
      "content": "billing dispute resolution"
    }
  },
  "_source": ["tenant_id", "title", "source"],
  "size": 5
}
```

```
# Bob (globalnet only)
GET kb_content/_search?pretty
Authorization: Basic Ym9iX2dsb2JhbG5ldDpkZW1vLWdsb2JhbG5ldC0yMDI2

{
  "query": {
    "match": {
      "content": "billing dispute resolution"
    }
  },
  "_source": ["tenant_id", "title", "source"],
  "size": 5
}
```

**Key talking point:** The index is identical. The role's DLS query wraps every search with a `bool` filter — `tenant_id == acme AND acl.principals ∩ user's principals`. The application never touches ACL logic.

---

### Query 3 — "API authentication"

```
# Alice (acme only — will see Acme engineering docs)
GET kb_content/_search?pretty
Authorization: Basic YWxpY2VfYWNtZTpkZW1vLWFjbWUtMjAyNg==

{
  "query": {
    "match": {
      "content": "API authentication"
    }
  },
  "_source": ["tenant_id", "title", "source", "acl.principals"],
  "size": 5
}
```

```
# Bob (globalnet only — will see GlobalNet developer portal docs)
GET kb_content/_search?pretty
Authorization: Basic Ym9iX2dsb2JhbG5ldDpkZW1vLWdsb2JhbG5ldC0yMDI2

{
  "query": {
    "match": {
      "content": "API authentication"
    }
  },
  "_source": ["tenant_id", "title", "source", "acl.principals"],
  "size": 5
}
```

**Show:** Alice sees `CONF-A-001` (Acme Platform API auth guide); Bob sees `CONF-GN-001` (GlobalNet developer portal auth). Same query, different knowledge bases — pure DLS.

---

## Section 3 — Hybrid Retrieval Queries

All queries below use the **admin** key so tenant filtering does not obscure the retrieval comparison.
Run as the default cluster superuser or use:

```
Authorization: Basic YWRtaW5fZ2VuZXN5czpkZW1vLWFkbWluLTIwMjY=
```

### 3a — BM25 Keyword Search (traditional full-text)

```
POST kb_content/_search?pretty
{
  "query": {
    "match": {
      "content": "escalation procedure"
    }
  },
  "_source": ["title", "tenant_id", "source"],
  "size": 5
}
```

Scores are based on TF-IDF / BM25. Exact keyword matches rank highest.
**Weakness:** Misses documents that describe the same concept with different vocabulary (e.g., "tier escalation runbook").

---

### 3b — Semantic Search (Jina EIS vector)

Uses the `semantic_text` field — Elasticsearch handles embedding generation automatically via the configured inference endpoint.

```
POST kb_content/_search?pretty
{
  "query": {
    "semantic": {
      "field": "content",
      "query": "escalation procedure"
    }
  },
  "_source": ["title", "tenant_id", "source"],
  "size": 5
}
```

Scores are cosine similarity in Jina's 512-dim embedding space.
**Strength:** Finds conceptually related documents even without keyword overlap.
**Weakness:** Can drift toward semantically adjacent but contextually wrong results.

---

### 3c — RRF Hybrid (BM25 + Semantic, fused with Reciprocal Rank Fusion)

Best of both worlds. RRF fuses rank positions rather than raw scores, so BM25 and vector scores are naturally normalized.

```
POST kb_content/_search?pretty
{
  "retriever": {
    "rrf": {
      "retrievers": [
        {
          "standard": {
            "query": {
              "match": {
                "content": "escalation procedure"
              }
            }
          }
        },
        {
          "standard": {
            "query": {
              "semantic": {
                "field": "content",
                "query": "escalation procedure"
              }
            }
          }
        }
      ],
      "rank_window_size": 20,
      "rank_constant": 60
    }
  },
  "_source": ["title", "tenant_id", "source"],
  "size": 5
}
```

**Show the audience:** The top result is typically more relevant than either BM25 or semantic alone. The `_rank` field in the response shows the final fused position.

---

### 3d — RRF + Jina Reranker (post-retrieval cross-encoder)

After RRF produces a candidate set, the Jina reranker re-scores each result using a cross-encoder model that reads both query and document together — much more accurate than bi-encoder similarity.

**Step 1:** Get the top-20 RRF results (reuse query 3c with `size: 20`).

**Step 2:** Rerank via the Inference API:

```
POST _inference/rerank/.jina-reranker-v2-base-multilingual
{
  "input": [
    "Acme Employee Escalation Policy — When a customer complaint cannot be resolved at Tier 1...",
    "Agent Escalation Runbook — GlobalNet agents follow a three-tier escalation model...",
    "Incident Management Runbook — Incident severity is classified P1 through P4..."
  ],
  "query": "escalation procedure for billing complaints"
}
```

The reranker returns a `relevance_score` per document. The highest scores float to the top regardless of original retrieval order.

**Why this matters:** Jina Reranker v2 is multilingual — it handles `en-US`, `es-419`, and `fr-FR` documents in the same index without separate language models.

---

## Section 4 — Connector Runtime Queries

Run these in Kibana Dev Tools to narrate the sync event story.

### 4a — Event counts by type

```
GET kb_sync_events/_search?pretty
{
  "size": 0,
  "aggs": {
    "by_event_type": {
      "terms": {
        "field": "event_type",
        "size": 10
      }
    }
  }
}
```

Expected buckets: `upsert` (15), `audit` (6), `delete` (3), `retry` (2), `rate_limit` (1).

---

### 4b — Failed syncs with retry events

```
GET kb_sync_events/_search?pretty
{
  "query": {
    "terms": {
      "event_type": ["retry", "rate_limit"]
    }
  },
  "_source": ["@timestamp", "tenant_id", "source", "event_type", "doc_id", "error_message", "retry_count"],
  "sort": [{"@timestamp": {"order": "desc"}}],
  "size": 10
}
```

**Talking point:** The connector runtime captures every failure with its error message and retry count. Ops teams get immediate visibility without tailing logs.

---

### 4c — Delete propagation audit trail

```
GET kb_sync_events/_search?pretty
{
  "query": {
    "term": {
      "event_type": "delete"
    }
  },
  "_source": ["@timestamp", "tenant_id", "source", "doc_id", "connector_id", "region"],
  "sort": [{"@timestamp": {"order": "desc"}}]
}
```

**Talking point:** When a document is removed from SharePoint or Salesforce, the connector writes a `delete` event here AND removes the document from `kb_content`. Audit trail proves propagation for compliance reviews.

---

### 4d — RTBF compliance query (Right to be Forgotten)

After a customer submits a RTBF request, the privacy team needs proof that all documents for a given tenant have been processed:

```
GET kb_sync_events/_search?pretty
{
  "query": {
    "bool": {
      "filter": [
        {"term": {"tenant_id": "acme"}},
        {"term": {"event_type": "delete"}}
      ]
    }
  },
  "_source": ["@timestamp", "doc_id", "source", "connector_id", "status"],
  "sort": [{"@timestamp": {"order": "asc"}}]
}
```

Pair with a count of remaining `acme` documents in `kb_content` to show completeness:

```
GET kb_content/_count
{
  "query": {
    "term": {"tenant_id": "acme"}
  }
}
```

---

### 4e — Sync health by region and source

```
GET kb_sync_events/_search?pretty
{
  "size": 0,
  "aggs": {
    "by_region": {
      "terms": {"field": "region", "size": 5},
      "aggs": {
        "by_source": {
          "terms": {"field": "source", "size": 5},
          "aggs": {
            "by_status": {
              "terms": {"field": "status", "size": 5}
            }
          }
        }
      }
    }
  }
}
```

---

## Section 5 — Scripted Demo Flow (5-Minute Script)

### 0:00 — Opening (15 seconds)

> "Today I'm going to show you three things Elastic does for Genesys knowledge management that OpenSearch cannot: query-time ACL enforcement with no drift, native hybrid retrieval without ML infrastructure, and a full connector audit trail — all in one index."

Open Kibana Dev Tools.

---

### 0:15 — (30 seconds) Index health check

Run:

```
GET kb_content/_stats/docs,store?pretty
GET kb_sync_events/_count
```

> "We have 60 knowledge base documents chunked from SharePoint, Salesforce, and Confluence — two tenants, three sources. Thirty sync events track every upsert, delete, retry, and rate-limit. The `content` field is `semantic_text`, so Jina embeddings are generated automatically at ingest. No ML pipeline to manage."

---

### 1:00 — (60 seconds) DLS demo — same query, different users

Run **Query 2a** (Alice — escalation procedure). Point at results: `"tenant_id": "acme"` only.

> "Alice is a Genesys agent for the Acme tenant. Her role has a DLS query baked in that filters to `tenant_id == acme` AND her ACL principals. Watch the source documents — all Acme."

Run **Query 2b** (Bob — same search body). Point at results: `"tenant_id": "globalnet"` only.

> "Bob is a GlobalNet agent. Same index. Same query. Completely different result set. There is no application code enforcing this. Elasticsearch's DLS wraps every request server-side. If someone calls the API directly with Bob's credentials, they still only see GlobalNet data."

Run **Query 2a** again as Admin. Show both tenants.

> "Admin sees everything. This is your platform ops view — useful for debugging and compliance audits. One index, three security postures."

**Pause for reaction.** This is the money moment.

---

### 2:00 — (60 seconds) Hybrid retrieval — BM25 vs semantic vs RRF

Run **Query 3a** (BM25). Note `_score` values and top result.

> "BM25 is classic full-text — TF-IDF. Fast and accurate for exact keyword matches."

Run **Query 3b** (semantic). Note different ranking order.

> "Jina EIS generates a 512-dim embedding at query time and finds semantically similar chunks. Notice the ranking is different — it caught 'tier escalation runbook' even though those exact words weren't in the query."

Run **Query 3c** (RRF hybrid). Show `_rank` field.

> "RRF fuses both ranked lists. The result at position 1 was ranked 3rd in BM25 and 2nd in semantic — but RRF's harmonic fusion puts it on top. No ML nodes. No separate pipeline. Jina EIS runs in Elastic's inference tier."

---

### 3:00 — (60 seconds) Connector sync events

Run **Query 4a** (event counts by type).

> "This is your connector observability layer. Every sync operation — upsert, delete, retry, rate-limit — is captured as a structured event. You can alert on retry spikes, audit delete propagation, and prove RTBF compliance."

Run **Query 4c** (delete events).

> "These three delete events show documents removed from the source systems. The connector propagated the deletion to `kb_content` and wrote this audit record. If a regulator asks 'when did you delete customer data?', this is your answer."

Run **Query 4b** (retries and rate-limits).

> "Two retries — one Confluence timeout, one Salesforce API rate-limit with 60-second backoff. Both eventually succeeded. The connector handled it automatically; the ops team was never paged."

---

### 4:00 — (30 seconds) Closing

> "What you just saw is what replaces the OpenSearch-based knowledge base: query-time ACL enforcement with zero drift, native Jina EIS hybrid retrieval with no ML infrastructure, and a structured sync audit trail — all on a single Elastic index. The DLS roles are five lines of JSON. The hybrid retrieval is one API call. This is production-ready today on Elastic Cloud."

---

## Section 6 — Talking Points

### On DLS vs Application-Layer ACL

**Prospect question:** "We already filter by tenant in our application layer. Why does this matter?"

**Answer:** "Application-layer filtering means every query path — your API, your admin UI, your background jobs, your analytics pipeline — must each correctly enforce the ACL. One missed code path and tenant A sees tenant B's data. With DLS, the enforcement is in Elasticsearch itself. The role's `query` parameter is injected as a mandatory filter on every request that comes in with that user's credentials. You cannot bypass it, because it happens before your application code runs. ACLs captured at sync time into `acl.principals` — DLS enforces at query time, not app layer. Zero drift."

---

### On Hybrid Retrieval vs Pure Vector Search

**Prospect question:** "We're evaluating Pinecone for vector search. What does Elastic add?"

**Answer:** "BM25 finds exact keyword matches that vector search misses — product codes, error codes, proper nouns. Vector search finds semantic matches that BM25 misses. RRF fuses both ranked lists using harmonic mean of positions, so you don't need to tune a blending weight. Jina EIS means Elastic handles embedding generation — you don't maintain a separate vector database or embedding service. And because everything is in one index, your DLS security layer covers both retrieval modes automatically."

---

### On Jina EIS vs ELSER vs On-Premises ML Nodes

**Prospect question:** "We're on-prem. Do we need ML nodes to run this?"

**Answer:** "No. ES 9.3+ Enterprise with Cloud Connect gives you access to Elastic Inference Service endpoints — including Jina Embeddings v5 and Jina Reranker v2 — without running ML nodes on-prem. Jina v5 supports 119+ languages in a single model, handles 32K token contexts, and outperforms ELSER on multilingual benchmarks. For Genesys's global deployments with Spanish, French, and English content, that's a single model replacing three. The inference call is a standard HTTP request to the `_inference` API — no model management, no GPU provisioning."

---

### On Connector Runtime vs ETL Pipelines

**Prospect question:** "We have a nightly ETL that pushes documents to our search index. What's wrong with that?"

**Answer:** "A nightly ETL means your search index is up to 24 hours stale. If an agent updates a resolution procedure in Confluence at 9am, your contact center agents are searching an outdated version until the next night's run. The Genesys connector runtime is event-driven — it watches for changes in SharePoint, Salesforce, and Confluence and syncs incrementally within minutes. Deletes propagate in near real-time. And every event is captured in `kb_sync_events`, giving you a full audit trail for compliance and debugging."

---

## Appendix A — Index Mapping Reference

### kb_content

| Field | Type | Notes |
|-------|------|-------|
| `tenant_id` | keyword | Mandatory — DLS filter target |
| `source` | keyword | sharepoint / salesforce / confluence |
| `doc_id` | keyword | Source system document ID |
| `chunk_id` | keyword | doc_id + "-chunk-N" — document _id |
| `title` | text + keyword | Full-text searchable; keyword for exact match / aggregation |
| `content` | semantic_text | Jina v5 embeddings auto-generated; BM25 + kNN both work |
| `locale` | keyword | en-US / es-419 / fr-FR |
| `acl.principals` | keyword (array) | ["user:alice@acme.com", "group:acme-agents", "tenant:acme"] |
| `source_url` | keyword | Deep-link back to source document |
| `last_synced_at` | date | Last successful sync timestamp |
| `@timestamp` | date | Document creation / update timestamp |

### kb_sync_events

| Field | Type | Values |
|-------|------|--------|
| `@timestamp` | date | Event time |
| `tenant_id` | keyword | acme / globalnet |
| `source` | keyword | sharepoint / salesforce / confluence |
| `event_type` | keyword | upsert / delete / retry / rate_limit / audit |
| `doc_id` | keyword | Affected document |
| `status` | keyword | success / deferred / logged |
| `error_message` | text | Human-readable error (nullable) |
| `retry_count` | integer | Number of retries attempted |
| `connector_id` | keyword | Connector instance identifier |
| `region` | keyword | us-east-1 / eu-west-1 |

---

## Appendix B — DLS Role Definitions

### genesys_acme_agent

```json
{
  "indices": [{
    "names": ["kb_content"],
    "privileges": ["read", "view_index_metadata"],
    "query": "{\"bool\":{\"filter\":[{\"term\":{\"tenant_id\":\"acme\"}},{\"terms\":{\"acl.principals\":[\"user:alice@acme.com\",\"group:acme-agents\",\"tenant:acme\"]}}]}}"
  }]
}
```

### genesys_globalnet_agent

```json
{
  "indices": [{
    "names": ["kb_content"],
    "privileges": ["read", "view_index_metadata"],
    "query": "{\"bool\":{\"filter\":[{\"term\":{\"tenant_id\":\"globalnet\"}},{\"terms\":{\"acl.principals\":[\"user:bob@globalnet.com\",\"group:globalnet-agents\",\"tenant:globalnet\"]}}]}}"
  }]
}
```

### genesys_admin

```json
{
  "indices": [{
    "names": ["kb_content"],
    "privileges": ["read", "view_index_metadata"]
  }]
}
```

Note: `genesys_admin` has no `query` parameter — no DLS restriction. This is intentional for the demo contrast.

---

## Appendix C — Base64 Auth Reference

| User | Credentials | Base64 Token |
|------|-------------|--------------|
| alice_acme | `alice_acme:demo-acme-2026` | `YWxpY2VfYWNtZTpkZW1vLWFjbWUtMjAyNg==` |
| bob_globalnet | `bob_globalnet:demo-globalnet-2026` | `Ym9iX2dsb2JhbG5ldDpkZW1vLWdsb2JhbG5ldC0yMDI2` |
| admin_genesys | `admin_genesys:demo-admin-2026` | `YWRtaW5fZ2VuZXN5czpkZW1vLWFkbWluLTIwMjY=` |

Usage in Kibana Dev Tools:

```
GET kb_content/_search
Authorization: Basic <token>
```

Usage with curl:

```bash
curl -X GET "https://your-cluster:9200/kb_content/_search" \
  -H "Authorization: Basic YWxpY2VfYWNtZTpkZW1vLWFjbWUtMjAyNg==" \
  -H "Content-Type: application/json" \
  -d '{"query": {"match": {"content": "escalation procedure"}}, "size": 5}'
```
