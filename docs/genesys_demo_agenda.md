# Genesys Knowledge AI — Demo Runbook

**Date**: 2026-04-02 | **Duration**: 30 min | **Tool**: Kibana Dev Tools

**Before you start** — confirm all three indices have data:
```
GET _cat/indices/knowledge_retrieval_events,knowledge_articles,enterprise_pdf_chunks?v&h=index,docs.count
```
All three must show `docs.count > 0`. If any are missing, go to the app Data tab and index them first.

---

## Glossary — abbreviations used in this document

| Term | Full name | One-line meaning |
|---|---|---|
| **ES\|QL** | Elasticsearch Query Language | Elastic's pipe-based query language for analytics — does not exist in OpenSearch |
| **BM25** | Best Match 25 | Elasticsearch's lexical (keyword) ranking algorithm — matches exact tokens, scores by frequency and rarity |
| **RRF** | Reciprocal Rank Fusion | A technique that merges ranked result lists from multiple retrievers (e.g. BM25 + semantic) into a single ranked list |
| **DLS** | Document Level Security | An Elasticsearch feature that bakes a per-user filter into the user's role — enforced by the engine, not application code |
| **PPL** | Piped Processing Language | OpenSearch's query language — similar pipe syntax to ES\|QL but lacks type-casting functions and the `STATS…BY` pattern |
| **FGAC** | Fine-Grained Access Control | OpenSearch's security model for row- and column-level access — requires custom index security policies |
| **LLM** | Large Language Model | The AI model that generates the agent's answer (Bedrock Claude/Titan in Genesys's setup) |
| **KB** | Knowledge Base | Bedrock Knowledge Base — AWS's managed retrieval service wrapping OpenSearch, being replaced in this demo |
| **EIS** | Elastic Inference Service | Elastic's hosted ML inference endpoint — serves Jina v5 embeddings without needing a separate model deployment |
| **AppFlow** | Amazon AppFlow | AWS's managed data pipeline/ETL service — used today to sync content into OpenSearch; replaced by Elastic connectors |
| **ACL** | Access Control List | A list of users/groups permitted to access a document — captured by Elastic connectors at sync time |
| **JWT** | JSON Web Token | A signed token carrying a user's identity and group claims, issued after Okta authentication |
| **SAML** | Security Assertion Markup Language | A standard for federated SSO — used to link Okta identity to Elastic roles |
| **OIDC** | OpenID Connect | A modern identity standard built on OAuth 2.0 — alternative to SAML for the Okta → Elastic trust |
| **POC** | Proof of Concept | The live Elasticsearch cluster that replicates the production retrieval path for evaluation |
| **SLA** | Service Level Agreement | A contract defining uptime, response time, and penalty terms (e.g. SLA-ENT-2024-001 in Scenario 3) |
| **DPA** | Data Processing Agreement | A GDPR-required contract governing how personal data is handled (e.g. DPA-EU-2024-042 in Scenario 3) |
| **S3** | Amazon Simple Storage Service | AWS object storage — where Bedrock KB stores source documents; referenced in KB citations instead of page-level provenance |
| **p95** | 95th percentile latency | The response time that 95% of requests complete within — used for performance benchmarks |

---

## Opening (2 min) — say this before opening Dev Tools

> "Bedrock LLM stays. Answer Gen stays. The API contract stays.
> We are replacing one component — the retrieval layer — with Elasticsearch.
> Three things break in that layer today: tenant scoping lives in application code, metadata constraints are not enforced at retrieval time, and dense-only search fails on complex enterprise content.
> We are going to show all three."

---

## Scenario 1 — Multi-Tenant Retrieval Scoping (8 min)

**The OpenSearch problem this scenario addresses**: In OpenSearch + Bedrock KB, the tenant boundary is a WHERE clause written by a developer in the retrieval adapter. It can be misconfigured, accidentally removed, or bypassed. There is no engine-level enforcement — the guarantee is only as reliable as the application code. Elasticsearch Document Level Security (DLS) moves that guarantee into the retrieval engine itself, where it is a property of the user's authenticated role, not the query.

---

### Step 1.1 — ES|QL: show the shared platform (1 min)

```
POST _query
{
  "query": """
    FROM knowledge_retrieval_events
    | WHERE @timestamp > NOW() - 30 days
    | EVAL is_zero = CASE(retrieval_status == "zero_results", 1, 0)
    | EVAL confidence_num = TO_DOUBLE(retrieval_confidence_score)
    | STATS
        total_queries    = COUNT(*),
        zero_result_rate = ROUND(TO_DOUBLE(SUM(is_zero)) / COUNT(*) * 100.0, 1),
        avg_confidence   = ROUND(AVG(confidence_num), 2)
      BY tenant_id
    | SORT total_queries DESC
    | LIMIT 10
  """
}
```

Expected: 8+ tenant rows. Each with a distinct `tenant_id`. Some showing `zero_result_rate` of 30–50%.

> "Eight enterprise tenants. One shared platform. The question is what enforces the boundary between them."

> **vs OpenSearch**: ES|QL does not exist in OpenSearch. OpenSearch has PPL (Piped Processing Language) with similar pipe syntax, but lacks ES|QL's type-casting functions (`TO_DOUBLE`, `CASE`), multi-index aggregation across data streams, and the `STATS…BY` pattern used here. This cross-tenant quality dashboard is an ES|QL-native capability.

---

### Step 1.2 — ES|QL: Eurobank scoped view (1 min)

```
POST _query
{
  "query": """
    FROM knowledge_retrieval_events
    | WHERE tenant_id == "tenant-EUROBANK-EU-014"
    | KEEP @timestamp, tenant_id, query_text, locale_code, retrieval_status, retrieval_confidence_score, channel_type
    | SORT @timestamp DESC
    | LIMIT 10
  """
}
```

Expected: 10 rows, all `tenant_id: tenant-EUROBANK-EU-014`, mix of `de-DE` locale and `success`/`zero_results` statuses.

> "Eurobank AG agents only. Frankfurt, de-DE, voice and chat. Every row is scoped to this tenant."

> **vs OpenSearch**: Both systems can filter by tenant at query time. The difference is *where* that filter comes from. In OpenSearch + Bedrock KB, it is injected by application code. One developer makes a mistake, one missed condition, and FINSERV queries return Eurobank rows. In ES, the next step shows what happens when that guarantee moves into the engine.

---

### Step 1.3 — ES|QL: FINSERV scoped view (1 min)

```
POST _query
{
  "query": """
    FROM knowledge_retrieval_events
    | WHERE tenant_id == "tenant-FINSERV-EU-009"
    | KEEP @timestamp, tenant_id, query_text, locale_code, retrieval_status, retrieval_confidence_score, channel_type
    | SORT @timestamp DESC
    | LIMIT 10
  """
}
```

Expected: 10 rows, all `tenant_id: tenant-FINSERV-EU-009`. Zero Eurobank rows.

> "FINSERV EU. Same platform, different scope. Zero Eurobank rows. The scoping is working — but right now it lives in the query, not in the engine."

---

### Step 1.4 — `_search`: same query, Eurobank tenant (2 min)

```
POST enterprise_pdf_chunks/_search
{
  "query": {
    "bool": {
      "must": {
        "match": { "content": "escalation procedure P1 incident" }
      },
      "filter": [
        { "term": { "tenant_id": "tenant-EUROBANK-EU-014" } }
      ]
    }
  },
  "_source": ["chunk_id", "tenant_id", "locale", "section_title", "page_number", "source_url"],
  "size": 5
}
```

Expected: hits for chunks `c004`, `c008`, `c011` among others. Every hit shows `tenant_id: tenant-EUROBANK-EU-014`.

> "Eurobank agent submits a query. Five chunks returned. Every hit: `tenant_id: tenant-EUROBANK-EU-014`. Point to that field on every row."

> **vs OpenSearch**: In OpenSearch + Bedrock KB, the retrieval call goes through AppFlow → OpenSearch → Bedrock KB wrapper. The tenant filter is added by the adapter layer — application code your team writes and maintains. There is no OpenSearch-native mechanism that prevents a malformed request from crossing tenant lines. In ES, the next step demonstrates why that is different.

---

### Step 1.5 — `_search`: same query, FINSERV tenant (1 min)

**Do not change the query string. Only change the `tenant_id` value.**

```
POST enterprise_pdf_chunks/_search
{
  "query": {
    "bool": {
      "must": {
        "match": { "content": "escalation procedure P1 incident" }
      },
      "filter": [
        { "term": { "tenant_id": "tenant-FINSERV-EU-009" } }
      ]
    }
  },
  "_source": ["chunk_id", "tenant_id", "locale", "section_title", "page_number", "source_url"],
  "size": 5
}
```

Expected: `"hits": { "total": { "value": 0 } }` — zero results.

> "Same query. FINSERV scope. Zero hits. FINSERV cannot see Eurobank content. The boundary is enforced at the retrieval engine.
> For this demo, tenant context is simulated via an explicit filter. In production, the retrieval adapter injects it from the authenticated session — the mechanism is identical, it just comes from the identity layer instead."

> **vs OpenSearch**: OpenSearch has Fine-Grained Access Control (FGAC) with document-level security, but it requires custom index-level security policies that are configured per-cluster and are difficult to audit across tenants. Elastic DLS is defined in a user role — one role definition per tenant, applied automatically at query time, with full audit logging via Elastic's security event stream. The provisioning is 2–3 hours on a live cluster; the enforcement is permanent and cannot be bypassed by the query author.

**Pause here. Let the zero result land before moving on.**

---

## Scenario 2 — Metadata-Aware Retrieval (8 min)

**The OpenSearch problem this scenario addresses**: Bedrock KB manages chunking and indexing opaquely — you cannot inspect the content model or run quality analysis against it. Retrieval quality problems (wrong locale, stale content, mixed domains) are invisible until an agent gets a wrong answer. Elasticsearch exposes the full metadata model as queryable fields, making coverage gaps and noise measurable before they affect agents.

---

### Step 2.1 — ES|QL: metadata richness across the knowledge base (1 min)

```
POST _query
{
  "query": """
    FROM knowledge_articles
    | WHERE published_status == "published"
    | STATS
        article_count = COUNT(*),
        locales       = COUNT_DISTINCT(source_locale),
        domains       = COUNT_DISTINCT(knowledge_domain)
      BY tenant_region, knowledge_domain
    | SORT article_count DESC
    | LIMIT 12
  """
}
```

Expected: rows across `eu-west-1`, `eu-central-1`, `us-east-1`, `global`. Multiple domains per region.

> "Every article carries structured metadata: locale, domain, status, region. This is what makes retrieval controllable. Let me show what happens when you use it — and what happens when you don't."

> **vs OpenSearch**: You cannot run this query against Bedrock KB. The knowledge base index is managed by AWS — you have no access to the underlying document schema or the ability to aggregate across it. You find out about locale gaps when Frankfurt agents start calling your support line. ES exposes this before the problem reaches agents.

---

### Step 2.2 — ES|QL: locale coverage gaps by domain (2 min)

```
POST _query
{
  "query": """
    FROM knowledge_articles
    | EVAL is_de = CASE(source_locale == "de-DE", 1, 0)
    | EVAL is_fr = CASE(source_locale == "fr-FR", 1, 0)
    | EVAL is_es = CASE(source_locale == "es-419" OR source_locale == "es-MX", 1, 0)
    | STATS
        total_articles     = COUNT(*),
        has_german_locale  = SUM(is_de),
        has_french_locale  = SUM(is_fr),
        has_spanish_locale = SUM(is_es)
      BY knowledge_domain
    | EVAL german_coverage_pct  = ROUND(TO_DOUBLE(has_german_locale)  / total_articles * 100.0, 1)
    | EVAL french_coverage_pct  = ROUND(TO_DOUBLE(has_french_locale)  / total_articles * 100.0, 1)
    | EVAL spanish_coverage_pct = ROUND(TO_DOUBLE(has_spanish_locale) / total_articles * 100.0, 1)
    | KEEP knowledge_domain, total_articles, german_coverage_pct, french_coverage_pct, spanish_coverage_pct
    | SORT german_coverage_pct ASC
  """
}
```

Expected: `SLA Management` and `IVR & Routing` near bottom for `german_coverage_pct`. Some domains at 0%.

> "SLA Management: low German coverage. IVR and Routing: near-zero French. This is why Frankfurt agents get zero results querying in German — the content was never indexed in that locale. Metadata makes the gap visible before tenants notice it."

> **vs OpenSearch**: OpenSearch PPL can do similar aggregations, but the Bedrock KB abstraction layer removes access to the underlying index entirely. Genesys cannot run PPL against a Bedrock KB index — it is AWS-managed. This analysis requires direct index access, which only exists with Elasticsearch as the retrieval store.

---

### Step 2.3 — ES|QL: noise breakdown without status filtering (1 min)

```
POST _query
{
  "query": """
    FROM knowledge_articles
    | WHERE source_locale == "de-DE"
    | EVAL is_published    = CASE(published_status == "published", 1, 0)
    | EVAL is_draft        = CASE(published_status == "draft", 1, 0)
    | EVAL is_archived     = CASE(published_status == "archived", 1, 0)
    | EVAL is_under_review = CASE(published_status == "under_review", 1, 0)
    | STATS
        total        = COUNT(*),
        published    = SUM(is_published),
        drafts       = SUM(is_draft),
        archived     = SUM(is_archived),
        under_review = SUM(is_under_review)
      BY knowledge_domain
    | EVAL noise_pct = ROUND(TO_DOUBLE(total - published) / total * 100.0, 1)
    | SORT noise_pct DESC
  """
}
```

Expected: `noise_pct` of 30–60% across most domains. Only a fraction of German articles are in published state.

> "Without status filtering, 30 to 50 percent of the German-locale result set is noise — drafts, archived versions, articles under review. The LLM gets all of it. This is how stale content enters generated answers."

> **vs OpenSearch**: Bedrock KB does not expose document status as a retrievable or filterable field — it indexes documents as-is from the data source. Elastic connectors capture `published_status` (and equivalent fields from SharePoint, Confluence, ServiceNow) at sync time and write them as typed metadata fields. The ingest pipeline enforces the schema. You can filter on `published_status` at retrieval time. Bedrock KB cannot.

---

### Step 2.4 — `_search`: without metadata constraints — show the noise (1 min)

**Run this first.**

```
POST enterprise_pdf_chunks/_search
{
  "query": {
    "bool": {
      "must": {
        "match": { "content": "GDPR article 17 deletion right to erasure" }
      },
      "filter": [
        { "term": { "tenant_id": "tenant-EUROBANK-EU-014" } }
      ]
    }
  },
  "_source": ["chunk_id", "section_title", "page_number", "locale", "knowledge_domain", "source_url"],
  "size": 10
}
```

Expected: hits in `en-US` (page 1, 3, 13), `de-DE` (pages 18–23), and `fr-FR` (pages 26–31) all mixed together.

> "No metadata constraints. Results in en-US, de-DE, and fr-FR all mixed — English summary, German SLA appendix, French DPA addendum. The LLM has to decide which one is relevant. It often doesn't get it right."

> **vs OpenSearch**: This is exactly what Bedrock KB returns today — a mixed result set across all locales, because the retrieval layer applies no session-context constraints. The LLM receives all of it and must disambiguate. That disambiguation fails silently.

---

### Step 2.5 — `_search`: with metadata constraints — show the precision (1 min)

**Change only the filters. Keep the query string identical.**

```
POST enterprise_pdf_chunks/_search
{
  "query": {
    "bool": {
      "must": {
        "match": { "content": "GDPR article 17 deletion right to erasure" }
      },
      "filter": [
        { "term":  { "tenant_id":         "tenant-EUROBANK-EU-014" } },
        { "term":  { "locale":            "fr-FR"                  } },
        { "match": { "knowledge_domain":  "Compliance & Privacy"   } },
        { "term":  { "source":            "sharepoint"             } }
      ]
    }
  },
  "_source": [
    "chunk_id", "section_title", "page_number", "locale",
    "knowledge_domain", "source", "source_url", "sensitivity", "last_synced_at"
  ],
  "size": 5
}
```

Expected: only `fr-FR` chunks from pages 26–31 — the French DPA addendum. `sensitivity: confidential` on each hit.

> "Same query. Four metadata constraints applied from session context. Only the French DPA addendum chunks return — the ones a compliance agent actually needs. The LLM receives a clean, scoped result set. The answer it generates is correspondingly more precise."

> **vs OpenSearch**: Bedrock KB does not support retrieval-time metadata filtering of this kind. You can set up filters in the KB data source configuration, but they are static — not driven by session context (agent locale, tenant, source system). The Elastic retrieval adapter applies these dynamically from the authenticated session on every query. OpenSearch also lacks a native `source` field that captures where the document came from — that field is written by the Elastic connector at sync time.

---

## Scenario 3 — Enterprise PDF Chunk Retrieval (8 min)

**The OpenSearch problem this scenario addresses**: Bedrock KB uses Amazon Titan as its default embedding model — English-dominant, dense-only, with no BM25 component. Structured identifiers like `SLA-ENT-2024-001` are embedded as vectors and matched semantically — which means Titan finds text that is *about* contracts, not the *specific* contract. Multilingual retrieval across de-DE content from an en-US query fails silently. Elastic combines BM25 (exact token matching) with Jina v5 (93 languages, 8K context) via hybrid RRF — handling both cases in one API call.

---

### Step 3.1 — ES|QL: show the document structure (2 min)

```
POST _query
{
  "query": """
    FROM enterprise_pdf_chunks
    | WHERE parent_doc_id == "DOC-ENT-2024-001"
    | KEEP chunk_id, locale, page_number, section_title, contains_table, contains_visual, structured_ids
    | SORT page_number ASC
  """
}
```

Expected: 15 rows in page order. Locales switch from `en-US` (pages 1–15) → `de-DE` (pages 18–23) → `fr-FR` (pages 26–31).

Point to:
- `contains_table: true` on pages 8, 9, 20, 21, 23, 29 — tables preserved in chunks
- `contains_visual: true` on page 15 — network topology diagram flagged
- `structured_ids` column — `SLA-ENT-2024-001` and `DPA-EU-2024-042` indexed as searchable metadata

> "34-page Eurobank AG service agreement. Three languages. Fifteen chunks. Each carries its own locale, page number, section label, and structured IDs. Not one blob — fifteen addressable pieces."

> **vs OpenSearch**: In Bedrock KB, you cannot run this query. Chunks are internal to the KB — the application receives document-level references (an S3 key), not chunk-level metadata. There is no page number, no section title, no locale per chunk. You have no visibility into how a document was split or what each piece contains. The Elastic ingest pipeline writes this schema at index time, making every chunk independently addressable and inspectable.

---

### Step 3.2 — ES|QL: structured ID lookup (1 min)

```
POST _query
{
  "query": """
    FROM enterprise_pdf_chunks
    | WHERE MATCH(structured_ids, "SLA-ENT-2024-001")
      AND knowledge_domain == "Compliance & Privacy"
    | KEEP chunk_id, locale, page_number, section_title, structured_ids, sensitivity
    | SORT page_number ASC
  """
}
```

Expected: multiple chunks across `en-US`, `de-DE`, and `fr-FR` all carrying `SLA-ENT-2024-001` in `structured_ids`.

> "Every chunk that carries SLA-ENT-2024-001 as a structured identifier. Three locales, different sections, different pages. The metadata schema links them. Watch what happens when an agent queries for this identifier."

> **vs OpenSearch**: `structured_ids` is a first-class indexed field in the Elastic schema — the ingest pipeline extracts it from the document and writes it explicitly. In Bedrock KB, this field does not exist. Contract identifiers are embedded inside the document text and Titan tries to find them semantically. BM25 on a dedicated `structured_ids` field is exact and fast — Titan vector search on embedded identifiers is probabilistic and slow.

---

### Step 3.3 — `_search`: structured identifier query — BM25 wins (2 min)

```
POST enterprise_pdf_chunks/_search
{
  "query": {
    "bool": {
      "should": [
        {
          "match": {
            "content": "penalty clause service credit"
          }
        },
        {
          "match": {
            "structured_ids": "SLA-ENT-2024-001"
          }
        }
      ],
      "minimum_should_match": 1,
      "filter": [
        { "term": { "tenant_id": "tenant-EUROBANK-EU-014" } },
        { "term": { "locale":    "de-DE"                  } }
      ]
    }
  },
  "highlight": {
    "fields": {
      "content": { "fragment_size": 250, "number_of_fragments": 1 }
    }
  },
  "_source": [
    "chunk_id", "parent_doc_id", "section_title",
    "page_number", "locale", "source_url", "structured_ids", "last_synced_at"
  ],
  "size": 3
}
```

Expected: top hit is `c010`, page 21, `Servicegutschriften und Vertragsstrafen bei SLA-Verstoß`. `structured_ids` shows `SLA-ENT-2024-001,SLA-CLAIM-DE`. Highlight shows the penalty clause text.

> "Top result: chunk c010, page 21 — the penalty clause. SLA-ENT-2024-001 matched in `structured_ids`. BM25 caught the exact identifier. Point to `source_url` and `last_synced_at` — the agent knows exactly where this came from and that it is current."

> **vs OpenSearch**: This is the core failure of Titan dense-only retrieval. `SLA-ENT-2024-001` embedded as a vector will find text that is *semantically similar to a contract reference* — it does not find the specific contract. An agent querying for `SLA-ENT-2024-001` in Bedrock KB may get the right document by accident if it appears frequently enough in the content, or may get nothing if Titan's embedding space doesn't score it highly. BM25 on `structured_ids` is deterministic — it either matches or it doesn't, with no ambiguity. For regulated financial services content, deterministic retrieval is not optional.

---

### Step 3.4 — `_search`: natural language paraphrase — BM25 bridges the language gap (1 min)

```
POST enterprise_pdf_chunks/_search
{
  "query": {
    "bool": {
      "must": {
        "match": {
          "content": "what happens if Genesys misses the response time target"
        }
      },
      "filter": [
        { "term": { "tenant_id": "tenant-EUROBANK-EU-014" } },
        { "term": { "locale":    "de-DE"                  } }
      ]
    }
  },
  "_source": [
    "chunk_id", "section_title", "page_number",
    "locale", "source_url", "last_synced_at"
  ],
  "size": 3
}
```

Expected top 3 in order:
- `c010` page 21 — `Servicegutschriften und Vertragsstrafen bei SLA-Verstoß` (score ~0.74)
- `c008` page 19 — `P1-Eskalationsverfahren (Kritische Vorfälle)` (score ~0.73)
- `c009` page 20 — `Reaktionszeiten und Verfügbarkeitsziele` (score ~0.70)

> "English query, German document. The top result is the penalty clause. Second is the P1 escalation procedure. Third is the response time table — exactly the three sections a Frankfurt agent needs on this call. BM25 on analysed text bridges the language gap. With Jina v5 semantic added via hybrid RRF, this works even on queries that share zero terms with the document."

> **vs OpenSearch**: Titan is English-dominant. An English-language query against German content in Bedrock KB will either fail to retrieve the German chunks or rank them lower than English summaries — because Titan's embedding space is weighted toward English. Jina v5 (served via EIS — Elastic Inference Service, Elastic's hosted model endpoint — default from ES 9.4 / March 30 Serverless) is trained across 93 languages with a shared multilingual embedding space. English queries and German documents land close in that space. Genesys has Frankfurt agents, Dublin agents, Buenos Aires agents — Titan cannot serve all of them from the same model.

---

### Step 3.5 — ES|QL: single chunk — what gets passed to the LLM (1 min)

```
POST _query
{
  "query": """
    FROM enterprise_pdf_chunks
    | WHERE chunk_id == "DOC-ENT-2024-001_c008"
    | KEEP chunk_id, parent_doc_id, doc_title, source_url, page_number, section_title, locale, content, last_synced_at
  """
}
```

Expected: one row. Full `content` text of the P1 escalation procedure in German. `source_url` pointing to SharePoint. `page_number: 19`.

> "One chunk. Page 19. The P1 escalation procedure in German — the binding version the contract specifies. A SharePoint URL the agent can open and cite. A sync timestamp. This is what the retrieval adapter passes to Bedrock LLM — not 34 pages, one precisely located piece with full provenance."

> **vs OpenSearch**: Bedrock KB returns an S3 location — a bucket and key pointing to the source document. The agent receives a reference to the 34-page PDF, not page 19. Answer Gen's citation is the document, not the clause. In regulated industries, a citation to page 21, section `Servicegutschriften`, SharePoint URL, synced 2026-03-28, is materially different from a citation to a 34-page PDF in an S3 bucket. Chunk-level provenance is what makes the answer auditable.

---

## Optional — Hybrid RRF (3 min, only if `semantic_text` is provisioned)

**Check first — run this before the session starts:**
```
GET enterprise_pdf_chunks/_mapping/field/content
```

- `"type": "semantic_text"` → run the query below live
- `"type": "text"` → whiteboard only: *"BM25 and Jina v5 run as two parallel retrievers, RRF fuses their ranked lists. Tenant and locale filters apply to both in one call. This is what the POC provisions."*

```
POST enterprise_pdf_chunks/_search
{
  "retriever": {
    "rrf": {
      "retrievers": [
        {
          "standard": {
            "query": {
              "bool": {
                "must": {
                  "match": {
                    "content": "what happens if Genesys misses the response time target"
                  }
                },
                "filter": [
                  { "term": { "tenant_id": "tenant-EUROBANK-EU-014" } },
                  { "term": { "locale":    "de-DE"                  } }
                ]
              }
            }
          }
        },
        {
          "standard": {
            "query": {
              "semantic": {
                "field": "content",
                "query": "what happens if Genesys misses the response time target"
              }
            }
          }
        }
      ],
      "rank_window_size": 15,
      "rank_constant": 60
    }
  },
  "_source": ["chunk_id", "section_title", "page_number", "locale", "source_url"],
  "size": 3
}
```

Expected: same top 3 chunks as step 3.4 but with more robust scoring — Jina v5 bridges the English query to German content even with zero term overlap.

> "Same paraphrase query. BM25 catches German terminology. Jina v5 bridges the English intent to the German content. RRF fuses both ranked lists. The correct chunk surfaces regardless of which retriever scored it higher. Tenant and locale filters apply to both retrievers in one API call — no extra code."

> **vs OpenSearch**: OpenSearch hybrid search exists but requires a separate search pipeline configuration with a normalization processor — it does not have a native RRF retriever. Critically, OpenSearch's hybrid search does not apply a single filter set to both legs simultaneously; you configure each retriever separately. The Elastic `rrf` retriever is a first-class API object — both BM25 and semantic legs share the same `filter` block, tenant and locale scoping applies to both in one call, and the fusion is done natively in the engine without a post-processing step.

---

## Closing — What Answer Gen Receives (2 min)

No query. Show this JSON as a static slide or paste into a text editor.

```json
{
  "retrievalResults": [
    {
      "content": {
        "text": "Unterschreitet Genesys die vereinbarte Verfügbarkeit gemäß SLA-ENT-2024-001 in einem Kalendermonat, gelten folgende Gutschriftenregelungen: Verfügbarkeit 99,5%–99,9%: Gutschrift 10% der monatlichen Grundgebühr (MRC). Verfügbarkeit 99,0%–99,5%: Gutschrift 25% MRC. Verfügbarkeit unter 99,0%: Gutschrift 50% MRC..."
      },
      "location": {
        "type": "SHAREPOINT",
        "sharePointLocation": {
          "url": "https://sharepoint.eurobank.internal/sites/legal/Docs/GEN-ENT-SVC-2024.docx"
        }
      },
      "score": 0.94,
      "metadata": {
        "chunk_id":       "DOC-ENT-2024-001_c010",
        "section_title":  "Servicegutschriften und Vertragsstrafen bei SLA-Verstoß",
        "page_number":    "21",
        "locale":         "de-DE",
        "source_file":    "GEN-ENT-SVC-2024.docx",
        "structured_ids": "SLA-ENT-2024-001,SLA-CLAIM-DE",
        "last_synced_at": "2026-03-28T06:00:00Z"
      }
    }
  ]
}
```

> "This is what crosses the wire to Answer Gen. The shape is the Bedrock KB retrieval contract — `retrievalResults`, `content.text`, `location`, `score`, `metadata`. Answer Gen's prompt builder reads `content.text`. Citations come from `location.sharePointLocation.url`. Neither changes.
>
> The retrieval adapter translates between two API shapes. Answer Gen sends the same request it sends today. It receives the same response it receives today. The only thing that changed is what is behind the adapter."

---

## Q&A — prepared answers

**"This is just filtering, not real DLS."**
> The filter is simulated for the demo. In the provisioned POC, this is Document Level Security baked into the ES role definition — a filter that cannot be bypassed by the query author. The role definitions and user setup are written. Two to three hours to provision on a live cluster.

**"OpenSearch also has document-level security."**
> OpenSearch FGAC has DLS, but it is configured at the index level via security policies that are separate from the application. In practice, Genesys's OpenSearch setup enforces tenant isolation in application code — not in the engine. The question is not whether OpenSearch theoretically supports DLS; it is whether your current deployment enforces it at the engine. It does not. That is the gap this POC closes.

**"What changes for our Okta integration?"**
> At query time: user authenticates via Okta, a JWT (JSON Web Token carrying group claims) is issued, the Elastic SAML/OIDC realm maps the Okta group to an ES role, and the DLS filter is applied automatically. At index time: the connector resolves source permissions, calls the Okta Groups API, and writes Okta group IDs to `acl.principals` (Access Control List field). Open decision: canonical group ID format — `okta-group:{id}` vs `okta-group:{name}`.

**"What about our other connector sources?"**
> SharePoint and Confluence: native ACL capture. Salesforce and ServiceNow: partial native, custom field mapping needed. Custom API: Python subclass of BaseConnector, one to two week PS engagement per connector type. S3: IAM policy maps to `acl.principals`.

**"What does the migration path look like?"**
> Each tenant is an ES role and a user. No index schema change. You can run old and new retrieval paths in parallel, compare result quality per tenant, and cut over when satisfied. The Elastic connector runtime replaces AppFlow (Amazon's managed data pipeline service). The retrieval adapter replaces the Bedrock KB wrapper.

**"What is the performance impact?"**
> ~8ms overhead for tenant filtering at p95 (95th percentile — meaning 95% of requests complete within this time). Total retrieval p95 under 50ms. 92ms headroom against a 100ms SLA.

**"Why not just fix OpenSearch?"**
> Three reasons. First, Bedrock KB is a managed service — Genesys cannot change the chunking strategy, the metadata schema, or the retrieval logic. It is a black box. Second, Titan is English-dominant — you cannot swap the embedding model in Bedrock KB. Third, DLS in your current OpenSearch setup lives in application code, not the engine. All three of those are architectural constraints, not configuration options. Elasticsearch removes all three constraints in one change.

---

## Run order summary

| Step | Type | Index | Time |
|---|---|---|---|
| 1.1 | ES\|QL | `knowledge_retrieval_events` | 1 min |
| 1.2 | ES\|QL | `knowledge_retrieval_events` | 1 min |
| 1.3 | ES\|QL | `knowledge_retrieval_events` | 1 min |
| 1.4 | `_search` | `enterprise_pdf_chunks` | 2 min |
| 1.5 | `_search` | `enterprise_pdf_chunks` | 1 min |
| 2.1 | ES\|QL | `knowledge_articles` | 1 min |
| 2.2 | ES\|QL | `knowledge_articles` | 2 min |
| 2.3 | ES\|QL | `knowledge_articles` | 1 min |
| 2.4 | `_search` | `enterprise_pdf_chunks` | 1 min |
| 2.5 | `_search` | `enterprise_pdf_chunks` | 1 min |
| 3.1 | ES\|QL | `enterprise_pdf_chunks` | 2 min |
| 3.2 | ES\|QL | `enterprise_pdf_chunks` | 1 min |
| 3.3 | `_search` | `enterprise_pdf_chunks` | 2 min |
| 3.4 | `_search` | `enterprise_pdf_chunks` | 1 min |
| 3.5 | ES\|QL | `enterprise_pdf_chunks` | 1 min |
| Optional RRF | `_search` | `enterprise_pdf_chunks` | 3 min |
| Closing | Static JSON | — | 2 min |
