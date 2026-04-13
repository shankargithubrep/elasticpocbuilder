# Genesys POC — Requirements Document

**Captured**: 2026-03-26
**Source**: Genesys technical discussion (10:30 session)
**Status**: Draft — pending Genesys review

---

## Context

Genesys is replacing **OpenSearch + Bedrock Knowledge Base** with Elasticsearch as the retrieval layer for their Knowledge AI platform. Bedrock LLM stays for generation and orchestration. The API contract to Genesys Answer Gen must remain unchanged.

**Core problems being solved:**
- ACL drift — cross-tenant document exposure
- Dense-only Titan recall gaps on complex/multilingual queries
- Connector sprawl — no standardized sync runtime
- Multilingual failure on non-English tenants
- No GDPR Article 17 (RTBF) proof

---

## Requirements

### R1 — Retrieval Layer Replacement
Elasticsearch becomes the retrieval layer behind the existing Genesys Answer Gen API contract.
- Bedrock LLM: unchanged (generation and orchestration)
- OpenSearch + Bedrock KB: removed (retrieval only)
- Elastic: connectors + ACL trimming + hybrid retrieval
- API contract to Genesys Answer Gen: identical request/response shape

---

### R2 — Vector Tool Flexibility (BYOV)
Genesys may bring their own embedding model. The architecture must be model-agnostic.

- Support pre-computed vectors stored as `dense_vector` — Elastic handles kNN
- Support custom inference endpoints via `_inference` API (OpenAI-compatible)
- Support Bring Your Own Model (BYOM) via Eland / PyTorch upload
- DLS, RRF fusion, and connector runtime must function regardless of embedding model
- Default for POC: Jina v5 via EIS (`.jina-embeddings-v5-text-small`)

---

### R3 — Multi-Tenant Isolation
Strict tenant isolation — one Genesys customer must never see another's data at query time.

- Query-time enforcement via Document Level Security (`acl.principals` keyword field)
- `tenant_id` keyword field on every document
- Shared index + DLS preferred pattern (scales to thousands of tenants, no index proliferation)
- New tenant onboarded by creating ES role + user — no index schema changes required
- DLS filter baked into ES role definition — cannot be bypassed by the querying user

---

### R4 — IdP / Okta as ACL Authority
Okta (or enterprise IdP) is the single source of truth for identity and group membership. Elasticsearch must not own ACL decisions.

**Authentication flow (query time):**
- User authenticates via Okta → JWT/SAML token issued with group claims
- Elastic SAML/OIDC realm trusts Okta as IdP
- Role mapping rules: Okta group claim → ES role → DLS query filter applied automatically

**ACL sync flow (index time):**
- Connector syncs document from source system
- Connector resolves source system permissions → calls Okta Groups API
- Normalized Okta group IDs written to `acl.principals`
- At query time, user's Okta JWT groups match `acl.principals` → access granted

**Requirements:**
- Elastic configured with SAML or OIDC realm pointing to Okta
- Role mapping rules defined per tenant group pattern
- `acl.principals` must use Okta-normalized group IDs (canonical format TBD — see Open Decisions)
- Group mapping table (Okta group ↔ source system group) stored in `tenant_registry` index
- ACL drift elimination: both index-time and query-time resolve from same Okta source

---

### R5 — Connector Runtime
7 source types in scope. Connector workers deployed on AWS Fargate (Genesys-managed).

**Native connectors (no build required):**
| Source | ACL capture |
|---|---|
| SharePoint | Native — group memberships included |
| Salesforce | Partial native — custom field mapping needed |
| ServiceNow | Partial native — custom field mapping needed |
| Confluence | Native — space permissions included |
| S3 (Customer Buckets) | Native — IAM policy mapping needed |
| Web Content (Crawler) | Built-in crawler — no ACL |

**Custom build required:**
| Source | Approach |
|---|---|
| Custom API | Elastic Connector Framework SDK (Python) — subclass `BaseConnector`, implement `get_docs()` |

**Connector runtime requirements:**
- Incremental sync + delete propagation (target freshness: < 5 min including deletes)
- Rate-limit handling + retries built-in
- Canonical schema normalization (source field names → `kb_content` schema)
- ACL capture at sync time — Okta group IDs written to `acl.principals`
- Deploy per region, route by tenant
- N connectors = shared runtime + standard behavior

**Custom API connector delivery options:**
1. Self-serve: Genesys eng team uses Elastic Connector Framework SDK
2. Elastic PS engagement: scoped per connector type (~1–2 weeks each)
3. Direct indexing: if Genesys already has a sync pipeline, POST directly to ES `_bulk` API

---

### R6 — Metadata Tagging Schema
Every `kb_content` document must carry a rich, standardized metadata set. An ES ingest pipeline enforces defaults at index time regardless of connector.

```json
{
  "tenant_id":              "acme",
  "source":                 "sharepoint",
  "connector_id":           "sharepoint-acme-prod",
  "doc_id":                 "sp-12345",
  "chunk_id":               "sp-12345_chunk_002",
  "chunk_index":            2,
  "total_chunks":           5,
  "parent_doc_id":          "sp-12345",

  "title":                  "Billing Dispute Resolution Policy",
  "content":                "...",
  "doc_type":               "policy",
  "content_category":       "billing",
  "intent_tags":            ["billing", "dispute", "refund"],
  "agent_skill":            "billing-support",

  "locale":                 "en-US",
  "sensitivity":            "internal",
  "contains_pii":           false,
  "gdpr_article17":         false,
  "propagation_confirmed":  false,

  "doc_status":             "active",
  "version":                "2.1",
  "expires_at":             null,
  "review_due":             "2026-09-01",

  "source_url":             "https://sharepoint...",
  "source_file":            "Billing_Policy_v2.1.docx",
  "source_section":         "Section 3",
  "page_number":            7,

  "last_modified_at":       "2026-01-10T00:00:00Z",
  "last_synced_at":         "2026-03-26T08:30:00Z",
  "@timestamp":             "2026-03-26T08:30:00Z",

  "acl": {
    "principals": ["okta-group:acme-billing-agents", "tenant:acme"]
  }
}
```

---

### R7 — Hybrid Retrieval with RRF
Replace dense-only Titan retrieval with full hybrid stack.

- BM25 (keyword) + Jina v5 semantic (`semantic_text` field via EIS)
- RRF fusion executed in a single `_search` API call (multi-retriever)
- Optional Jina v3 reranker post-RRF for precision lift on Top-K
- Multilingual: Jina v5 supports 93 languages; locale-aware analyzers per tenant
- All sub-queries in multi-retriever call respect DLS automatically — no extra code

**Why this beats Bedrock KB:**
| Scenario | Bedrock KB (Titan dense-only) | Elastic hybrid |
|---|---|---|
| Exact term match (P1, SLA, invoice #) | Weak | BM25 catches it |
| Semantic/paraphrase match | OK | Jina v5 catches it |
| Multi-intent query | One retrieval, misses intents | RRF merges decomposed sub-queries |
| Non-English content | Poor (Titan) | Jina v5 93 languages |
| Stale document returned | No control | `doc_status` filter eliminates it |

---

### R8 — Query Decomposition
Complex multi-intent queries must be handled without changing the Genesys Answer Gen API contract.

**Architecture:**
- Decomposition sits at **app layer** (retrieval adapter) — not inside Elasticsearch
- LLM (small model call) splits complex question into N focused sub-queries
- Sub-queries packaged into ES multi-retriever RRF payload — single ES call
- ES executes sub-queries in parallel, merges via RRF, applies DLS to all
- Answer Gen receives one ranked Top-K result set — decomposition invisible to it

**Decomposition patterns required:**
- Intent splitting: "refund AND upgrade question" → two sub-queries
- Entity extraction: "premium customer Germany 2+ years" → filters + semantic query
- Step-back: specific question → abstract policy question
- HyDE: generate hypothetical answer → embed → search for matching documents

---

### R9 — Retrieval Quality Measurement
Quality must be measurable and provable — not just claimed.

**Methodology:**
- Eval set: 20+ curated questions with known relevant doc IDs per tenant
- Run against: dense-only baseline (Titan equivalent) vs Elastic hybrid + rerank
- Metrics: NDCG@3, NDCG@5, Recall@10, MRR, freshness % (`doc_status: active`)
- Tool: Elastic `_rank_eval` API (built-in, no external tooling needed)

**POC deliverable:** comparison table showing score delta across retrieval strategies

**Live demo format:** same query run as:
1. Dense-only → shows wrong/incomplete result
2. Hybrid RRF → shows correct result
3. Hybrid RRF + rerank → shows most precise result

---

### R10 — RTBF / Delete Propagation Audit Trail
GDPR Article 17 compliance — proof that deleted content is removed from the retrieval layer.

- `propagation_confirmed: false` written to `kb_content` at index time
- `gdpr_article17: true` flag on sensitive documents
- Delete event in source system → connector detects → ES document deleted
- `kb_sync_events` record written with `propagation_confirmed: true` + timestamp
- Audit trail queryable: regulators can query "prove document X was removed and when"
- Target: delete propagation confirmed within < 5 min of source deletion

---

### R11 — Same API Contract (Retrieval Adapter)
Genesys Answer Gen API contract must not change.

**Retrieval adapter responsibilities:**
- Protocol translation: Bedrock KB API shape → ES `_search` API shape → Bedrock KB response shape
- DLS injection: user's Okta token → `acl.principals` filter added to every query
- Query decomposition: multi-intent handling (R8)
- Metadata filtering: `doc_status: active`, `expires_at` null-or-future, tenant scope
- Response formatting: Top-K + citations in Bedrock KB contract shape

---

## Open Decisions — Needs Genesys Input

| # | Decision | Options | Impact |
|---|---|---|---|
| D1 | Canonical `acl.principals` format | `okta-group:{id}` (portable) vs `okta-group:{name}` (readable, fragile) | Every connector + role mapping depends on this |
| D2 | Custom API connector delivery | Self-build (SDK) vs Elastic PS vs direct indexing | Timeline and ownership |
| D3 | Okta for POC | Bring Okta sandbox vs simulate with static role mappings | POC fidelity for auth flow |
| D4 | On-prem embedding | Cloud Connect + Jina EIS vs BYOM on ML nodes | Infrastructure decision |
| D5 | Group mapping table ownership | Okta group ↔ source system group mapping | Connector ACL accuracy |

---

## POC Scope (Next Week)

**Show in demo (built):**
- 4 indices provisioned: `kb_content`, `kb_sync_events`, `tenant_registry`, `connector_registry`
- DLS with 3 users: alice_acme (acme only), bob_globalnet (globalnet only), admin_genesys (all)
- Hybrid RRF queries against `kb_content` with semantic + BM25
- RTBF audit trail in `kb_sync_events`
- 3 connector sources: SharePoint, Salesforce, Confluence

**Defer to production scope:**
- Okta SAML/OIDC integration (D3)
- Custom API connector build (D2)
- Full metadata schema with ingest pipeline (R6)
- Eval harness with NDCG scores (R9)
- Fargate deployment config (R5)
