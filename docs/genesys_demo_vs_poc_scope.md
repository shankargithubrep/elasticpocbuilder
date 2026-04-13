# Genesys — What the Demo Shows vs What the POC Delivers

**Prepared**: 2026-04-01
**Purpose**: Pre-presentation reference — what can be run live today, what requires POC provisioning, and why each boundary exists.

---

## Reading this document

Three tiers are defined below:

| Tier | Meaning |
|---|---|
| **Show in demo** | Data is loaded, ES\|QL query is written and tested, can be run live right now |
| **Not in demo — possible in POC** | Architecturally complete and in-scope, but requires ES infrastructure provisioning that has not been done yet |
| **Out of scope** | Deferred to production by design; not promised for the POC |

---

## Tier 1 — Can Show in the Demo Today

These are backed by real data files (300 rows each), written ES|QL queries in `all_queries.json`, and scenarios in `scenarios.json`.

---

### 1.1 — Retrieval failure diagnostics: exact-match miss rate by structured ID type

**Requirement mapped**: R7 (hybrid retrieval), R9 (quality measurement)
**Data**: `search_query_logs`
**What it shows**: ES|QL query buckets retrieval attempts by hour and ID type (`invoice_number`, `product_code`, `sla_id`), computes miss rate, applies INLINESTATS z-score to flag anomalous windows where dense-only retrieval fails. Escalation count tied to each window.

**Why it works in the demo**: `search_query_logs` has `query_type`, `structured_id_type`, `retrieval_method`, `query_matched`, `result_count`, `escalated_to_human` — all required fields are present.

**What it proves to Genesys**: The Titan dense-only retrieval gap is quantified with data, not just claimed. The miss rate is visible by ID type. The escalation cost is attached to each failure window.

---

### 1.2 — Multilingual retrieval failure rate by locale

**Requirement mapped**: R7 (multilingual recall)
**Data**: `knowledge_retrieval_events` + `locale_metadata_lookup` (LOOKUP JOIN)
**What it shows**: Failure rates per locale sorted descending. Non-English locales (es-419, pt-BR, fr-FR, de-DE) are visible against their `multilingual_indexing_enabled` flag. Average confidence score and latency included per locale.

**Why it works in the demo**: LOOKUP JOIN on `locale_code` is supported. Both datasets have the join key. The `is_failure` flag is derived from `retrieval_status` values (`no_match`, `error`, `low_confidence`).

**What it proves to Genesys**: LATAM and EU tenant failure rates are localized to specific languages. Indexing gaps (where `multilingual_indexing_enabled = false`) are directly correlated with failure spikes.

---

### 1.3 — GDPR Article 17 deletion propagation audit trail

**Requirement mapped**: R10 (RTBF audit trail)
**Data**: `gdpr_deletion_events` + `kb_replica_registry` (LOOKUP JOIN)
**What it shows**: Per-deletion-request propagation status across replicas and shards — confirmed count, pending count, SLA breach flag, days elapsed, audit status (`COMPLIANT`, `IN_PROGRESS`, `NON_COMPLIANT_OVERDUE`, `REQUIRES_REMEDIATION`). Filters to non-compliant requests.

**Why it works in the demo**: `gdpr_deletion_events` has `deletion_request_id`, `deletion_status`, `deletion_confirmed_at`, `article17_deadline_at`, `replica_id`, `shard_id`. `kb_replica_registry` has `expected_propagation_sla_hours` joinable on `replica_id`.

**What it proves to Genesys**: Regulators can query propagation proof in one ES|QL statement. The audit is not a manual process. SLA breach detection is automatic. This directly addresses the "no RTBF proof" gap they named as a core problem.

---

### 1.4 — Tenant locale search quality trending over time

**Requirement mapped**: R9 (retrieval quality measurement)
**Data**: `knowledge_retrieval_events` + `locale_reference` (LOOKUP JOIN)
**What it shows**: Hourly quality score trend for `fr-FR`, `de-DE`, `es-419` locales — average relevance score, retrieval success rate, zero-result rate per tenant and locale over time. Surfaces systemic regressions that are invisible in aggregate metrics.

**Why it works in the demo**: `knowledge_retrieval_events` has `@timestamp`, `tenant_id`, `locale`, `retrieval_score`, `result_count`, `top_result_confidence`, `is_zero_result`. `locale_reference` joins on `locale_code`.

**What it proves to Genesys**: Retrieval quality is measurable and monitorable by locale, not just globally. This is the operational foundation for an SLA on multilingual quality.

---

### 1.5 — Multi-tenant regional distribution and replica health

**Requirement mapped**: R3 (multi-tenant isolation), R5 (connector runtime — regional)
**Data**: `kb_replica_registry` + `tenant_region_reference`
**What it shows**: Tenants distributed across us-east-1, eu-west-1, eu-central-1, ap-southeast-1, sa-east-1 with data residency zones (EU-GDPR, LATAM-LGPD), replica tier (primary/secondary), and SLA per region. Regulatory framework visible per tenant.

**Why it works in the demo**: Both datasets exist with 300 rows each. The regional distribution is realistic — tenants include FINSERV-EU, RETAILCO-LATAM, HEALTHNET-NA, LOGISTIC-EU.

**What it proves to Genesys**: The architecture is multi-region and data-residency-aware. A new tenant's region assignment is metadata — not infrastructure change.

---

### 1.6 — Translation coverage gaps by article

**Requirement mapped**: R7 (multilingual)
**Data**: `locale_coverage_reference`
**What it shows**: Per-article translation completeness percentage. Articles with zero LATAM or EU locales are visible. Missing locales listed per article (e.g., `es-419`, `fr-FR`, `de-DE` absent from a given article).

**Why it works in the demo**: `locale_coverage_reference` has `article_id`, `available_locales`, `latam_locale_count`, `eu_locale_count`, `translation_completeness_pct`, `missing_latam_locales`, `missing_eu_locales`.

**What it proves to Genesys**: Content gaps that cause retrieval failures are identifiable before tenants notice. This is a proactive quality layer, not a reactive one.

---

### 1.7 — Structured ID pattern catalog

**Requirement mapped**: R7 (hybrid retrieval design)
**Data**: `structured_query_pattern_lookup`
**What it shows**: Which ID patterns (e.g. `INV-[A-Z]+-\d{4}`, `SLA-TKT-\d+`, `DPA-[A-Z]+-\d{4}`) require lexical match vs semantic, with match confidence and usage frequency. Directly supports the BM25-vs-semantic routing argument.

**Why it works in the demo**: Static lookup dataset. Each row has `pattern_key`, `requires_lexical_match`, `pattern_category`, `match_confidence_score`, `pattern_description`.

**What it proves to Genesys**: The hybrid retrieval routing is not arbitrary — there is a catalog of ID patterns that maps to retrieval strategy. This is the engineering basis for why BM25 is necessary alongside semantic search.

---

## Tier 2 — Not in Demo Today, Possible in POC

These capabilities are architecturally complete in the requirements document and technically sound, but they require Elasticsearch infrastructure to be provisioned — indexes created with specific mappings, users and roles configured, or endpoints deployed. They are not blocked by data or by design, only by setup time.

---

### 2.1 — DLS live demonstration: same query, different results

**Requirement mapped**: R3 (multi-tenant isolation), R4 (IdP/ACL)
**Why it is not in the demo**: Requires `kb_content` index to be provisioned in Elasticsearch with the R6 metadata schema (`tenant_id`, `acl.principals`, `chunk_id`, `semantic_text`). Also requires three ES native users (`acme-support`, `globalnet-support`, `acme-tier2`) and ES roles with DLS filters mapping to each tenant. None of this is in the data files — `knowledge_articles.csv` exists but has neither `acl.principals` nor `tenant_id` at the document level.

**What is needed to unlock it**:
1. Create `kb_content` index with the R6 mapping (DLS-ready schema)
2. Load representative documents with `tenant_id` and `acl.principals` populated
3. Create ES roles: `acme-role` (DLS: `tenant_id = acme`), `globalnet-role` (DLS: `tenant_id = globalnet`), `acme-tier2-role` (DLS: `tenant_id = acme AND acl.principals: acme-tier2`)
4. Create ES native users bound to those roles

**Why it is achievable in the POC**: This is standard ES security — no external dependency. DLS is a documented ES feature available on any cluster. Estimated setup: 2–3 hours once a cluster is available.

**Demo moment it unlocks**: Act 2 in the demo guide — log in as `acme-support`, run a query, see ACME docs only. Log out, log in as `globalnet-support`, same query, see GlobalNet docs only. Zero overlap. This is the most important 30 seconds of the demo.

---

### 2.2 — Hybrid RRF retrieval: live query comparison

**Requirement mapped**: R7 (hybrid retrieval with RRF), R2 (BYOV)
**Why it is not in the demo**: The `knowledge_articles` index needs to exist in Elasticsearch with a `semantic_text` field mapped to an EIS inference endpoint (Jina v5). Without the `semantic_text` field type, the `"retriever": { "semantic": {...} }` syntax in the queries cannot execute. Running on flat CSV data or a standard text field would only produce BM25 results, not hybrid.

**What is needed to unlock it**:
1. Create `kb_content` (or `knowledge_articles`) index with `semantic_text` field mapped to Jina v5 EIS endpoint (`.jina-embeddings-v5-text-small`)
2. Load content documents — the `knowledge_articles.csv` data is a valid starting point but needs `content` field populated (currently sparse)
3. Run the three-step comparison in the demo guide: dense-only (0 results for `INV-2026-84732`) → BM25 only → hybrid RRF

**Why it is achievable in the POC**: Jina v5 is the confirmed default from Serverless / ES 9.4 (Mar 30). EIS configuration is a single API call. Index mapping with `semantic_text` is defined in R6. No external model deployment required.

**Demo moment it unlocks**: Act 3 in the demo guide — invoice number query, side-by-side comparison of dense vs hybrid. The most direct proof that Elastic beats Titan on exact-match retrieval.

---

### 2.3 — Connector sync event trail with ACL capture

**Requirement mapped**: R5 (connector runtime), R6 (metadata schema)
**Why it is not in the demo**: `kb_sync_events` index does not exist in the data files. The demo guide references it in Act 4 for RTBF (to prove the deleted document is absent post-sync) and in Act 5 for connector health. Without this index, the connector-side of the story is entirely absent — Act 5 currently shows query latency from `search_query_logs`, which is retrieval analytics, not connector operational data.

**What is needed to unlock it**:
1. Create `kb_sync_events` index with fields: `connector_id`, `source_type`, `doc_id`, `tenant_id`, `acl.principals`, `sync_status`, `last_synced_at`, `propagation_confirmed`, `gdpr_article17`
2. Load representative sync events for SharePoint, Salesforce, and Confluence sources
3. Optionally show one RTBF event: `gdpr_article17: true` + `propagation_confirmed: false` → deletion → `propagation_confirmed: true`

**Why it is achievable in the POC**: Synthetic data generation is already proven in this demo — adding a `kb_sync_events` dataset with 200–300 rows is the same pattern used for all existing datasets.

**Demo moment it unlocks**: Connector realism in Act 5. Ability to show that the RTBF audit trail connects source system deletion → connector detection → ES document deletion → `propagation_confirmed: true`. This is the end-to-end proof Genesys's compliance team needs.

---

### 2.4 — Retrieval quality comparison table (NDCG / Recall baseline)

**Requirement mapped**: R9 (retrieval quality measurement)
**Why it is not in the demo**: The `_rank_eval` API requires documents and queries to be loaded in Elasticsearch with a defined judgment set (known relevant doc IDs per query). The eval harness exists as a requirement but has not been provisioned. Without live indices, the comparison between dense-only and hybrid + rerank cannot be computed numerically.

**What is needed to unlock it**:
1. Load `kb_content` with real content (depends on 2.2 above)
2. Define a judgment set: 20+ questions with known relevant `doc_id` values per tenant
3. Run `_rank_eval` against three strategies: dense-only, hybrid RRF, hybrid RRF + rerank
4. Produce the score comparison table (NDCG@3, NDCG@5, Recall@10, MRR)

**Why it is achievable in the POC**: `_rank_eval` is a built-in ES API — no external tooling. The judgment set can be synthetic for the POC (fabricated known-relevant pairs). The POC scope document in the requirements already lists this as a deliverable.

**Demo moment it unlocks**: The "proof, not claim" moment in R9. A comparison table with actual numbers showing the lift from dense-only to hybrid. This is what turns a demo into a proof of concept.

---

### 2.5 — R11 Retrieval adapter: unchanged API contract demonstration

**Requirement mapped**: R11 (same API contract)
**Why it is not in the demo**: No adapter code exists. The retrieval adapter (Bedrock KB API → ES `_search` API → Bedrock KB response shape) is defined in the requirements but has not been implemented or shown.

**What is needed to unlock it**:
1. Write a thin Python adapter (a few dozen lines) that accepts a Bedrock KB-shaped request, executes the ES hybrid RRF query, and returns a Bedrock KB-shaped response
2. Show it in the demo: call the adapter with a Bedrock KB format request → adapter calls Elasticsearch → response back in Bedrock KB shape → Answer Gen receives it unchanged

**Why it is achievable in the POC**: The adapter is a translation layer, not a new product. The ES query shape is already defined (Act 3 queries). The Bedrock KB response schema is documented. This is a 1–2 day engineering task.

**Demo moment it unlocks**: The single most important proof for the "low-disruption migration" story. Without it, the claim that "Answer Gen won't notice the switch" remains unproven. With it, the migration path is concrete.

---

## Tier 3 — Out of POC Scope (Production Path)

These are real requirements that Genesys will ask about. The right answer is not "we can't do it" but "here is when and how."

| Capability | Requirement | Why Deferred | Production Path |
|---|---|---|---|
| Okta SAML / OIDC integration | R4 | Requires Genesys to bring an Okta sandbox or Elastic to set up a simulated IdP. Not a one-day task, and D3 (Okta for POC) is an open decision. | Standard ES SAML/OIDC realm config. Elastic has done this with Okta before. 1–2 week engagement once Okta sandbox is available. |
| Custom API connector | R5 | Custom connector requires Genesys eng team access and a working source API to connect to. SDK is available (Python, `BaseConnector` subclass). | Elastic PS engagement: ~1–2 weeks per connector type. Or Genesys self-serves using Connector Framework SDK. |
| Fargate connector deployment | R5 | Infrastructure config. Requires Genesys AWS environment access. | Connector workers are standard Docker containers. Fargate task definition is straightforward once containers are validated. |
| Full BYOM embedding | R2 | PyTorch upload via Eland requires ML node configuration and model validation. EIS (Jina v5) covers the POC. | BYOM path is documented — Eland model upload, ML node sizing, inference endpoint config. |
| Group mapping table ownership | D5 (open decision) | Genesys has not decided who owns the Okta group ↔ source system group mapping table. | Once decided: a `tenant_registry` index with group mappings, maintained by connector runtime or Genesys IdP team. |

---

## Quick reference for the presentation

**If asked: "Can you show us DLS working right now?"**
> Not in this environment — the `kb_content` index and role configuration need to be provisioned on a live cluster. The query and role definitions are written. The data schema is defined. This is 2–3 hours of setup, not a design question.

**If asked: "Can you show us hybrid search working right now?"**
> The queries are written and the architecture is defined. The `semantic_text` field needs to be mapped against an EIS endpoint on a live cluster. The demo today shows where hybrid retrieval is needed — the quantified failure data from dense-only — and the query that replaces it.

**If asked: "What changes for Answer Gen?"**
> Nothing. The retrieval adapter (R11) translates between the Bedrock KB API shape and Elasticsearch. Answer Gen sends the same request it sends today and receives the same response shape. The switch is invisible to it.

**If asked: "How do we migrate 8,000 tenants?"**
> Each tenant is an ES role and a user. No index schema change. No pipeline change. Onboarding a new tenant is creating one role with a DLS filter and one user. Existing tenants migrate by running their content through the connector runtime into `kb_content`.
