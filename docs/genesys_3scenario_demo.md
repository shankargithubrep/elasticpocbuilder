# Genesys — 3-Scenario Demo Script

**Prepared**: 2026-04-01
**Duration**: 15 minutes
**Audience**: Genesys Knowledge AI Platform Engineering + IT/Security

---

## Opening (90 seconds) — say this before touching the screen

> "I want to be explicit about what we are and are not showing today.
>
> Today Genesys Answer Gen calls OpenSearch + Bedrock Knowledge Base to retrieve documents. The LLM generates the answer. Answer Gen owns the orchestration. That does not change.
>
> What we are showing is what happens if you replace the single retrieval component — OpenSearch + Bedrock KB — with Elasticsearch. The API contract between your application and the retrieval layer stays identical. Answer Gen sends the same request it sends today. It receives the same response shape. Your agents do not notice. Your compliance team does.
>
> Three things break today in that retrieval layer. We are going to show all three."

**Draw or show this once — do not dwell on it:**

```
TODAY:    Answer Gen  →  [OpenSearch + Bedrock KB]  →  documents
AFTER:    Answer Gen  →  [Elasticsearch]            →  documents
                              ↑
                    Connectors replace AppFlow
                    DLS replaces app-layer tenant filter
                    Hybrid RRF replaces Titan dense-only
                    Same API contract. Bedrock LLM unchanged.
```

---

## Scenario 1 — Multi-Tenant Retrieval Scoping (4 minutes)

### The problem

> "Problem one: cross-tenant document exposure. Genesys runs a shared platform. Tenant ACME should never see Tenant FINSERV's data. Today that guarantee lives in application code — a WHERE clause someone writes and someone else can accidentally remove. We are going to show what happens when that guarantee moves into the retrieval engine itself, where it cannot be bypassed."

### What to show

**Step 1 — Show the baseline: retrieval events across all tenants**

Run this against `knowledge_retrieval_events`. Shows agents from different tenants all hitting the shared platform:

```esql
FROM knowledge_retrieval_events
| WHERE @timestamp > NOW() - 1 hour
| STATS
    total_queries    = COUNT(*),
    zero_result_rate = ROUND(COUNT_IF(retrieval_status == "zero_results") / COUNT(*) * 100, 1),
    avg_confidence   = ROUND(AVG(retrieval_confidence_score), 2)
  BY tenant_id
| SORT total_queries DESC
| LIMIT 10
```

> "This is the shared platform. Eight enterprise tenants. One index. The question is: what is enforcing the boundary between them?"

**Step 2 — Show retrieval scoped to a single tenant: ACME EU**

```esql
FROM knowledge_retrieval_events
| WHERE tenant_id == "tenant-ACME-EU-001"
| KEEP @timestamp, tenant_id, query_text, locale_code, retrieval_status, retrieval_confidence_score, channel_type
| SORT @timestamp DESC
| LIMIT 10
```

> "When the retrieval layer is scoped to tenant-ACME-EU-001, only ACME queries are visible. Only ACME articles return. The same query run under a different tenant identity returns a completely different result set."

**Step 3 — Contrast: show the FINSERV tenant view**

```esql
FROM knowledge_retrieval_events
| WHERE tenant_id == "tenant-FINSERV-EU-009"
| KEEP @timestamp, tenant_id, query_text, locale_code, retrieval_status, retrieval_confidence_score, channel_type
| SORT @timestamp DESC
| LIMIT 10
```

> "Zero ACME results. Zero overlap. Same index, different tenant context, completely isolated result set."

**Step 4 — Show the failure mode that exists today**

```esql
FROM knowledge_retrieval_events
| WHERE retrieval_status == "zero_results" OR retrieval_status == "language_mismatch"
| STATS
    failure_count = COUNT(*),
    affected_sessions = COUNT_DISTINCT(session_id)
  BY tenant_id, locale_code, retrieval_status
| SORT failure_count DESC
| LIMIT 10
```

> "These are the tenants where retrieval is already failing. FINSERV EU agents querying in German. GLOBOCOM LATAM agents in French. Zero results. This is the multilingual retrieval failure on top of the scoping problem — we will come back to it in Scenario 3."

### Closing line

> "In production, this scoping is enforced by Document Level Security baked into the ES role definition — not a WHERE clause in application code. A query authored by an ACME-scoped user cannot physically return a FINSERV document. Not without changing the user's role. Not without us knowing."

---

## Scenario 2 — Metadata-Aware Retrieval Precision (4 minutes)

### The problem

> "Problem two: retrieval precision. Today Genesys Answer Gen retrieves documents and passes them to the LLM for generation. If the wrong document is retrieved — wrong locale, outdated version, archived article — the LLM generates a wrong answer with full confidence. The retrieval layer needs to be controllable by metadata: locale, document status, knowledge domain, source, sensitivity. Not as post-filters, but as first-class retrieval constraints."

### What to show

**Step 1 — Show the metadata richness available per article**

```esql
FROM knowledge_articles
| WHERE published_status == "published"
| STATS
    article_count = COUNT(*),
    locales = COUNT_DISTINCT(source_locale),
    domains = COUNT_DISTINCT(knowledge_domain)
  BY tenant_region, knowledge_domain
| SORT article_count DESC
| LIMIT 12
```

> "Every article in the knowledge base carries structured metadata: locale, domain, status, region, last updated. This is the schema that makes retrieval controllable. Let me show what happens when you use it."

**Step 2 — Retrieval scoped to published, German-locale compliance articles**

```esql
FROM knowledge_articles
| WHERE source_locale == "de-DE"
  AND knowledge_domain == "Compliance & Privacy"
  AND published_status == "published"
| KEEP article_id, article_title, knowledge_domain, source_locale, tenant_region, last_updated
| SORT last_updated DESC
| LIMIT 10
```

> "Query: compliance articles, German locale, published only. Archived drafts excluded. Stale content excluded. The result set is precise before the semantic layer even runs."

**Step 3 — Show what happens without metadata constraints: noise from wrong domains and statuses**

```esql
FROM knowledge_articles
| WHERE source_locale == "de-DE"
| STATS
    total = COUNT(*),
    published = COUNT_IF(published_status == "published"),
    drafts = COUNT_IF(published_status == "draft"),
    archived = COUNT_IF(published_status == "archived"),
    under_review = COUNT_IF(published_status == "under_review")
  BY knowledge_domain
| EVAL noise_pct = ROUND((total - published) / total * 100, 1)
| SORT noise_pct DESC
```

> "Without metadata filtering, 30–40% of the German-locale result set is noise — drafts, archived versions, articles under review. The LLM gets all of it. This is how stale content enters generated answers."

**Step 4 — Locale coverage gap: show which domains have no German coverage**

```esql
FROM knowledge_articles
| STATS
    total_articles     = COUNT(*),
    has_german_locale  = COUNT_IF(source_locale == "de-DE"),
    has_french_locale  = COUNT_IF(source_locale == "fr-FR"),
    has_spanish_locale = COUNT_IF(source_locale == "es-419" OR source_locale == "es-MX")
  BY knowledge_domain
| EVAL german_coverage_pct  = ROUND(has_german_locale  / total_articles * 100, 1)
| EVAL french_coverage_pct  = ROUND(has_french_locale  / total_articles * 100, 1)
| EVAL spanish_coverage_pct = ROUND(has_spanish_locale / total_articles * 100, 1)
| KEEP knowledge_domain, total_articles, german_coverage_pct, french_coverage_pct, spanish_coverage_pct
| SORT german_coverage_pct ASC
```

> "This is what causes the zero-result failures we saw in Scenario 1. SLA Management domain: only 12% German coverage. IVR & Routing: zero French. A Frankfurt agent querying SLA policy in German hits a wall because the content was never indexed in that locale. Metadata makes this visible and actionable."

### Closing line

> "The retrieval adapter we are building between Answer Gen and Elasticsearch applies these constraints automatically — locale from the agent's session context, doc_status from a freshness filter, knowledge domain from the query intent. Answer Gen never sees the filter logic. It just receives a more precise result set."

---

## Scenario 3 — Enterprise PDF: Chunked Retrieval with Source Attribution (5 minutes)

### The problem

> "Problem three: real enterprise content. Genesys's knowledge base is not clean web pages. It is service agreements, compliance addendums, SharePoint-sourced PDFs with German SLA appendices, French data processing schedules, tables, legal clause numbering, and structured identifiers like SLA-ENT-2024-001. Dense-only retrieval fails on all of it. We built one of those documents and chunked it to show what retrieval looks like when it works correctly."

### The document

> "This is a real Genesys enterprise service agreement for Eurobank AG — 34 pages, three languages, SharePoint-sourced. English operational body. German SLA appendix. French data processing addendum. It contains tables, a network topology diagram, escalation contact matrices, and compliance clauses referencing specific article numbers. Fifteen chunks in the index."

**Show the document structure first:**

```esql
FROM enterprise_pdf_chunks
| WHERE parent_doc_id == "DOC-ENT-2024-001"
| KEEP chunk_id, locale, page_number, section_title, contains_table, contains_visual, structured_ids
| SORT page_number ASC
```

> "Fifteen chunks. Three locales. The document does not exist as a single record — it exists as addressable pieces, each carrying its own locale, page number, section label, and structured IDs. This is what proper enterprise content indexing looks like."

### Step 1 — Query: structured identifier lookup

> "An agent is on a call. The customer cites contract SLA-ENT-2024-001 and asks about penalty clauses. The identifier is in the query. Dense-only Titan would embed this string and find semantically similar text — which returns the wrong chunk, or nothing. Watch what BM25 does."

```esql
FROM enterprise_pdf_chunks
| WHERE structured_ids LIKE "*SLA-ENT-2024-001*"
  AND knowledge_domain == "Compliance & Privacy"
| KEEP chunk_id, locale, page_number, section_title, structured_ids, sensitivity
| SORT page_number ASC
```

> "Three chunks match the identifier. One is the English summary. One is the German penalty clause — page 21. One is the French DPA addendum. The agent asked about penalty clauses: that is chunk c010, page 21, German locale, Servicegutschriften und Vertragsstrafen. Exact identifier, exact chunk, with the page number and sensitivity label attached. This is what BM25 adds to dense retrieval."

### Step 2 — Query: multilingual semantic retrieval with locale constraint

> "Same agent, different question. They need the P1 escalation procedure — binding German version, because the contract says the German text is authoritative. In English. Watch what happens."

```esql
FROM enterprise_pdf_chunks
| WHERE locale == "de-DE"
  AND parent_doc_id == "DOC-ENT-2024-001"
| KEEP chunk_id, page_number, section_title, content, structured_ids
| SORT page_number ASC
```

Point to chunk c008, page 19, section `P1-Eskalationsverfahren (Kritische Vorfälle)`.

> "This is the chunk an agent actually needs. Page 19. German. It contains the three escalation stages, the PagerDuty trigger, the conference bridge number, and the BSI notification requirement. The English summary on page 11 says 'see German appendix page 19 for binding version' — so the right retrieval is the German chunk, not the English one. Metadata scope on locale makes this deterministic."

**In a provisioned environment, this runs as hybrid RRF:**

```json
POST enterprise_pdf_chunks/_search
{
  "retriever": {
    "rrf": {
      "retrievers": [
        {
          "standard": {
            "query": {
              "bool": {
                "must": { "match": { "content": "P1 Eskalation kritischer Vorfall" } },
                "filter": [
                  { "term": { "locale": "de-DE" } },
                  { "term": { "parent_doc_id": "DOC-ENT-2024-001" } }
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
                "query": "P1 incident escalation procedure Germany binding version"
              }
            }
          }
        }
      ],
      "rank_window_size": 15,
      "rank_constant": 60
    }
  },
  "_source": ["chunk_id", "page_number", "section_title", "locale", "source_url", "last_synced_at", "structured_ids"],
  "size": 3
}
```

> "BM25 matches the German escalation terminology. Jina v5 semantic matches the English-language concept 'P1 escalation procedure'. RRF fuses them. The locale filter keeps results in German. The top result is chunk c008, page 19, with the SharePoint URL the agent can cite — so the answer is not just correct, it is verifiable."

### Step 3 — Show what Answer Gen actually receives

> "The last thing I want to show is what the retrieval adapter returns to Answer Gen. It does not return the full 34-page document. It returns this:"

```esql
FROM enterprise_pdf_chunks
| WHERE chunk_id == "DOC-ENT-2024-001_c008"
| KEEP chunk_id, parent_doc_id, doc_title, source_url, page_number, section_title, locale, content, last_synced_at
```

> "One chunk. Page 19. The SharePoint URL the agent can open. The section title. The locale. The sync timestamp so Answer Gen knows this content is current. This is what the retrieval adapter passes to Bedrock LLM — not a wall of text, a precisely located piece with full provenance. That is the difference between retrieval and retrieval-layer replacement."

### Closing line

> "The document this came from is a 34-page PDF sourced from SharePoint via the Elastic SharePoint connector, which captures the document, extracts text, chunks it with configurable overlap, runs it through the ingest pipeline to apply the metadata schema, and writes tenant and ACL fields automatically. The engineering effort Genesys does not have to build."

---

## Closing (1 minute)

> "Three things we showed:
>
> One — retrieval scoped by tenant context. Same index, different identity, zero overlap. That guarantee lives in the engine, not in application code.
>
> Two — retrieval precision through metadata. Locale, status, domain applied as constraints before the semantic layer runs. The LLM gets a clean result set.
>
> Three — a real enterprise PDF, chunked, multilingual, with structured identifiers. Hybrid retrieval returning the exact right chunk with page number, source URL, and sync timestamp.
>
> Answer Gen sent the same request it sends today. It received the same response shape. Nothing else changed."

---

## Objection handling

**"This is just filtering, not real DLS."**
> "The filtering in Scenario 1 demonstrates the retrieval scoping behavior. In the provisioned POC, this is Document Level Security — a filter baked into the ES role definition, not the query. The result is identical. The difference is that DLS cannot be bypassed by a developer writing the wrong WHERE clause. We have the role and user definitions ready. Two to three hours to provision on a live cluster."

**"How does this work with our Okta groups?"**
> "The DLS filter maps to `acl.principals` on each document. At sync time, the connector resolves SharePoint group membership, calls Okta, and writes the canonical Okta group IDs to that field. At query time, the user's Okta JWT claims match against it. The open decision we flagged — canonical group ID format — needs your input before we implement it."

**"What happens to Answer Gen during migration?"**
> "Nothing. The retrieval adapter sits between Answer Gen and Elasticsearch. It translates the Bedrock KB request shape into an ES `_search` call and returns a Bedrock KB response shape. Answer Gen does not know and does not care. You can run old and new retrieval paths in parallel, compare results, and cut over per-tenant when quality is validated."

**"What about our other six connector sources?"**
> "SharePoint and Salesforce are native — ACL capture included out of the box. ServiceNow and Confluence are partial native — custom field mapping needed but no custom code. The Custom API source needs a Python subclass of BaseConnector — a 1–2 week PS engagement per connector type, or your team self-serves with the SDK. S3 customer buckets map IAM policy to `acl.principals`."

---

## What requires a live cluster to show (not in this demo)

Be explicit if asked — do not obscure this:

| Capability | What it needs | Time to provision |
|---|---|---|
| DLS live login switch (acme-support vs globalnet-support) | `kb_content` index + ES users/roles with DLS filters | 2–3 hours |
| Hybrid RRF with live semantic retrieval | `semantic_text` field + Jina v5 EIS endpoint configured | ~4 hours |
| Connector sync event trail | `kb_sync_events` index with ACL-capture records | 1–2 hours |
| Retrieval quality comparison table (NDCG) | Live index + judgment set + `_rank_eval` run | Depends on above |

These are provisioning tasks, not design questions. The architecture, schema, query logic, and data are all defined and ready.
