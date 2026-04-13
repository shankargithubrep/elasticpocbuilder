# Genesys — Elasticsearch Search API Examples

**Prepared**: 2026-04-01
**Purpose**: Demo-ready `_search` API calls for the 3 live scenarios. Paste directly into Kibana Dev Tools.

**Tenant naming used throughout this document:**
- **Eurobank AG** → `tenant-EUROBANK-EU-014` — Frankfurt, eu-central-1, de-DE, Financial Services
- **FINSERV EU** → `tenant-FINSERV-EU-009` — Dublin, eu-west-1, en-GB, Financial Services

These are the same tenant IDs in the indexed data. All examples use one or both consistently.

**Demo context note**: In these examples, tenant context is simulated via an explicit `term` filter. In production, the retrieval adapter injects this filter from the authenticated session — the application never passes `tenant_id` as a query parameter.

---

## Live Example 1 — Multi-Tenant Retrieval Scoping

**The point**: Same shared index. Same query string. Different tenant filter. Different results. The boundary between tenants is enforced at the retrieval layer, not in application code.

**Run 1 — Eurobank agent query:**
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

**Run 2 — same query, FINSERV tenant scope:**
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

**Presenter note**
- **What to run**: Run 1, then Run 2, back-to-back without changing the query string.
- **What to point at**: Run 1 returns Eurobank chunks with `tenant_id: tenant-EUROBANK-EU-014`. Run 2 returns zero hits — FINSERV has no documents in this index.
- **Single conclusion**: The tenant boundary is enforced by the retrieval engine. A FINSERV-scoped query cannot return Eurobank content regardless of what the query says. In production this filter comes from the authenticated identity — for this demo it is simulated. The mechanism is identical either way.

---

## Live Example 2 — Metadata-Aware Retrieval

**The point**: A Eurobank Frankfurt agent queries for GDPR deletion policy. The retrieval adapter constrains results to German-locale documents from the compliance domain, sourced from SharePoint, marked confidential. The LLM receives a clean, scoped result set — not a mixed pile of en-US, draft, and archived content.

**Run 1 — with full metadata constraints (what the retrieval adapter sends):**
```
POST enterprise_pdf_chunks/_search
{
  "query": {
    "bool": {
      "must": {
        "match": { "content": "GDPR article 17 deletion right to erasure" }
      },
      "filter": [
        { "term": { "tenant_id": "tenant-EUROBANK-EU-014" } },
        { "term": { "locale": "de-DE" } },
        { "term": { "knowledge_domain": "Compliance & Privacy" } },
        { "term": { "source": "sharepoint" } }
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

**Run 2 — same query, no locale or domain filter (what a naive retrieval layer sends):**
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

**Presenter note**
- **What to run**: Run 2 first, then Run 1.
- **What to point at**: Run 2 returns chunks across en-US, de-DE, and fr-FR — the English summary, the German SLA appendix, and the French DPA addendum all mixed together. Run 1 returns only the German-locale compliance chunks. Point to the `locale` field in each hit.
- **Single conclusion**: Metadata constraints are the difference between "here are all the relevant chunks" and "here is the right chunk for this agent, in this language, from this source." The LLM gets a cleaner input in Run 1. The answer it generates is correspondingly more precise.

---

## Live Example 3 — Enterprise PDF Chunk Retrieval

**The point**: A Eurobank Frankfurt agent is on a call. The customer cites contract SLA-ENT-2024-001 and asks about penalty clauses. The retrieval layer finds the exact right chunk — page 21 of the German SLA appendix — with page number, section title, and SharePoint URL attached.

**Run 1 — structured identifier in the query (BM25 wins):**
```
POST enterprise_pdf_chunks/_search
{
  "query": {
    "bool": {
      "must": {
        "multi_match": {
          "query": "SLA-ENT-2024-001 penalty clause service credit",
          "fields": ["content", "section_title", "structured_ids"],
          "type": "best_fields"
        }
      },
      "filter": [
        { "term": { "tenant_id": "tenant-EUROBANK-EU-014" } },
        { "term": { "locale": "de-DE" } }
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

**Run 2 — natural language paraphrase of the same intent (semantic wins, lexical struggles):**
```
POST enterprise_pdf_chunks/_search
{
  "query": {
    "bool": {
      "must": {
        "multi_match": {
          "query": "what happens if Genesys misses the response time target",
          "fields": ["content^2", "section_title"],
          "type": "most_fields"
        }
      },
      "filter": [
        { "term": { "tenant_id": "tenant-EUROBANK-EU-014" } },
        { "term": { "locale": "de-DE" } }
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

**Presenter note**
- **What to run**: Run 1, then Run 2.
- **What to point at**: Run 1 — top hit is chunk `c010`, page 21, `Servicegutschriften und Vertragsstrafen bei SLA-Verstoß`. `SLA-ENT-2024-001` appears in `structured_ids` — BM25 matched it exactly. Point to `source_url` and `last_synced_at` — the agent knows where this came from and that it is current. Run 2 — same contract, paraphrased. Lexical search may return a weaker match or rank the wrong chunk first. This is where hybrid RRF (Optional Example 4) closes the gap.
- **Single conclusion**: The retrieval layer returns the right chunk with full provenance. The agent does not get the 34-page document — they get page 21, section title, SharePoint URL. That is the difference between document retrieval and retrieval-layer replacement.

---

## Optional Example 4 — Hybrid Retrieval with RRF

**Only run this if** `enterprise_pdf_chunks` has `content` mapped as `semantic_text`. Verify first:

```
GET enterprise_pdf_chunks/_mapping/field/content
```

If the response shows `"type": "semantic_text"` — run it live. If it shows `"type": "text"` or `"keyword"` — use this as a whiteboard or architecture explanation only. Do not attempt to run it.

**When to use it**: After Run 2 of Example 3, if the paraphrase query returned a weaker result. This is the "why hybrid matters" moment.

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
                  "multi_match": {
                    "query": "what happens if Genesys misses the response time target",
                    "fields": ["content", "section_title", "structured_ids"]
                  }
                },
                "filter": [
                  { "term": { "tenant_id": "tenant-EUROBANK-EU-014" } },
                  { "term": { "locale": "de-DE" } }
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
  "_source": [
    "chunk_id", "section_title", "page_number",
    "locale", "source_url", "last_synced_at"
  ],
  "size": 3
}
```

**Presenter note**
- **What to point at**: Same paraphrase query as Example 3 Run 2. BM25 catches German terminology. Jina v5 bridges "response time target" → "Reaktionszeiten". RRF fuses both. Top result is the correct chunk regardless of which retriever scored it higher. Both filters apply to both retrievers in the same call — no extra code for tenant scoping.
- **Single conclusion**: This is why BM25 alone cannot replace Titan, and Titan alone cannot replace BM25. You need both fused. That is what this single API call delivers.

---

## Example 5 — What Answer Gen Receives

**When to use this**: As an objection-handling backup. If Genesys asks "what changes for Answer Gen?", show this. It is not a live query — it is a side-by-side of the ES call and the transformed response the retrieval adapter returns.

**The ES `_search` call the adapter makes:**
```
POST enterprise_pdf_chunks/_search
{
  "query": {
    "bool": {
      "must": {
        "multi_match": {
          "query": "SLA-ENT-2024-001 penalty clause service credit",
          "fields": ["content", "section_title", "structured_ids"],
          "type": "best_fields"
        }
      },
      "filter": [
        { "term": { "tenant_id": "tenant-EUROBANK-EU-014" } },
        { "term": { "locale": "de-DE" } }
      ]
    }
  },
  "_source": [
    "chunk_id", "parent_doc_id", "doc_title", "section_title",
    "page_number", "locale", "source_url", "source_file",
    "content", "structured_ids", "last_synced_at", "sensitivity"
  ],
  "size": 3
}
```

**What Answer Gen receives — Bedrock KB response shape:**

The retrieval adapter transforms the ES hits into this shape. Answer Gen sends the same request it sends today and receives the same response contract. It does not know it is talking to Elasticsearch.

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
        "parent_doc_id":  "DOC-ENT-2024-001",
        "section_title":  "Servicegutschriften und Vertragsstrafen bei SLA-Verstoß",
        "page_number":    "21",
        "locale":         "de-DE",
        "source_file":    "GEN-ENT-SVC-2024.docx",
        "structured_ids": "SLA-ENT-2024-001,SLA-CLAIM-DE",
        "last_synced_at": "2026-03-28T06:00:00Z",
        "sensitivity":    "confidential"
      }
    },
    {
      "content": {
        "text": "Bei einem P1-Vorfall (kritischer Ausfall gemäß Abschnitt 3.1 des Rahmenvertrags SLA-ENT-2024-001) gelten folgende Eskalationsstufen: Stufe 1 (0–15 Minuten): Automatische Alarmierung des Genesys Bereitschaftsteams Frankfurt über PagerDuty..."
      },
      "location": {
        "type": "SHAREPOINT",
        "sharePointLocation": {
          "url": "https://sharepoint.eurobank.internal/sites/legal/Docs/GEN-ENT-SVC-2024.docx"
        }
      },
      "score": 0.87,
      "metadata": {
        "chunk_id":       "DOC-ENT-2024-001_c008",
        "parent_doc_id":  "DOC-ENT-2024-001",
        "section_title":  "P1-Eskalationsverfahren (Kritische Vorfälle)",
        "page_number":    "19",
        "locale":         "de-DE",
        "source_file":    "GEN-ENT-SVC-2024.docx",
        "structured_ids": "SLA-ENT-2024-001",
        "last_synced_at": "2026-03-28T06:00:00Z",
        "sensitivity":    "confidential"
      }
    }
  ]
}
```

**Presenter note**
- **What to point at**: The shape — `retrievalResults`, `content.text`, `location`, `score`, `metadata`. This is the Bedrock KB retrieval response contract. Answer Gen's prompt builder reads `content.text` and passes it to the LLM. The `location` field is what it uses for citations. Neither changes.
- **Single conclusion**: The retrieval adapter is a translation layer between two API shapes. Answer Gen sends the same request. It receives the same response. The only thing that changed is what is behind the adapter — Elasticsearch instead of OpenSearch + Bedrock KB. That is minimal disruption.

---

## Quick reference

| Example | Live today | Index | Tenant(s) |
|---|---|---|---|
| 1 — Multi-tenant scoping | Yes | `enterprise_pdf_chunks` | Eurobank EU-014 vs FINSERV EU-009 |
| 2 — Metadata-aware retrieval | Yes | `enterprise_pdf_chunks` | Eurobank EU-014 |
| 3 — PDF chunk retrieval | Yes | `enterprise_pdf_chunks` | Eurobank EU-014 |
| 4 — Hybrid RRF | Only if `semantic_text` provisioned | `enterprise_pdf_chunks` | Eurobank EU-014 |
| 5 — Answer Gen payload | Static — no cluster needed | — | Eurobank EU-014 |
