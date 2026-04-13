# Genesys Demo Script — 2026-04-02, 8:30–9:00 AM Pacific
## Audience: Amanda Halpin (PM), Balazs Szekely, Balazs Kazmer, Benedek Tanacs, Ram, Nick King
## Duration: 30 minutes hard stop
## Format: Dev Tools (Kibana) — show raw queries and results

---

## Opening (1 min)

> "Everything you're about to see runs against a live Elasticsearch cluster with data
> shaped to your Knowledge Fabric use case — SharePoint, Salesforce, Confluence sources,
> two tenants, real KB articles.
>
> The retrieval adapter is the only thing that changes in your stack.
> Bedrock or your in-house model for generation — untouched. Your API contract — untouched.
>
> I'll show you four things in 30 minutes: keyword search, semantic search, hybrid, and
> multi-tenancy. Let's go."

---

## Beat 1 — BM25: The Baseline (5 min)

**Talk track:**
> "This is what you have today with OpenSearch — BM25 keyword search. Works great when
> the rep types exactly what's in the document."

**Query 1a — exact match (wins):**
```
GET kb_content/_search
{
  "query": {
    "match": { "content": "invoice dispute escalation" }
  },
  "_source": ["title", "source", "tenant_id"],
  "size": 3
}
```
> "Three relevant results — the rep finds the right policy."

**Query 1b — paraphrase (fails):**
```
GET kb_content/_search
{
  "query": {
    "match": { "content": "bill disagreement process" }
  },
  "_source": ["title", "source", "tenant_id"],
  "size": 3
}
```
> "Same intent, different words — zero or low-quality results. This is the Titan problem.
> The rep is on a live voice call. They can't rephrase three times."

**Pause for effect. Don't move on until they nod.**

---

## Beat 2 — Semantic Search: Jina v5 (7 min)

**Talk track:**
> "Now we switch to the semantic_text field — same index, same document, powered by
> Jina Embeddings v5. This is the model Florian's team built. #1 on public benchmarks.
> 119 languages. 32,000 token context — that's a 25-page PDF in one chunk."

**Query 2a — same paraphrase, now semantic:**
```
GET kb_content/_search
{
  "knn": {
    "field": "embedding",
    "query_vector_builder": {
      "text_embedding": {
        "model_id": ".jina-embeddings-v5-text-small",
        "model_text": "bill disagreement process"
      }
    },
    "k": 3,
    "num_candidates": 50
  },
  "_source": ["title", "source", "tenant_id"]
}
```
> "The same query that returned nothing now returns the billing dispute policy.
> Jina understands what the rep means, not just what they typed."

**Query 2b — multilingual (if time allows):**
> "One more — same query in Spanish. No separate Spanish index, no translation layer."
```
GET kb_content/_search
{
  "knn": {
    "field": "embedding",
    "query_vector_builder": {
      "text_embedding": {
        "model_id": ".jina-embeddings-v5-text-small",
        "model_text": "proceso de disputa de factura"
      }
    },
    "k": 3,
    "num_candidates": 50
  },
  "_source": ["title", "source", "tenant_id"]
}
```
> "English documents, Spanish query. Correct result. One model. No configuration."

**Jina future-proofing line (for Amanda):**
> "One more thing on Jina — I know acquisition risk came up yesterday.
> Florian confirmed: from now on, every Jina release is available in Elastic
> on the same day it ships to Hugging Face. No lag, no replatform risk."

---

## Beat 3 — Hybrid + RRF: Best of Both (8 min)

**Talk track:**
> "Semantic is great for intent. BM25 is great for exact references —
> invoice numbers, ticket IDs, product codes. Your reps need both.
> Hybrid with RRF gives you the best result regardless of query type.
> You don't have to choose."

**Query 3a — exact reference number (BM25 wins):**
```
GET kb_content/_search
{
  "query": {
    "match": { "content": "INV-2024-8821" }
  },
  "_source": ["title", "source"],
  "size": 3
}
```
> "Invoice number — BM25 finds it instantly. Semantic would miss this."

**Query 3b — hybrid RRF:**
```
GET kb_content/_search
{
  "retriever": {
    "rrf": {
      "retrievers": [
        {
          "standard": {
            "query": {
              "match": { "content": "invoice dispute escalation procedure" }
            }
          }
        },
        {
          "knn": {
            "field": "embedding",
            "query_vector_builder": {
              "text_embedding": {
                "model_id": ".jina-embeddings-v5-text-small",
                "model_text": "invoice dispute escalation procedure"
              }
            },
            "k": 10,
            "num_candidates": 50
          }
        }
      ],
      "rank_window_size": 20,
      "rank_constant": 60
    }
  },
  "_source": ["title", "source", "tenant_id"],
  "size": 3
}
```
> "RRF runs both in parallel, fuses the scores. The top result is always
> the best from either signal. This is what we want as the default retrieval
> pattern in your Knowledge Fabric."

---

## Beat 4 — Multi-Tenancy (Tenant Isolation) (7 min)

**Talk track:**
> "Your biggest risk today is cross-tenant data exposure.
> Let me show you how Elasticsearch guarantees isolation at the query engine —
> not in application code.
>
> Same query. Same index. Two different reps from two different customers."

**Open two Dev Tools tabs (or switch users)**

**Query 4a — as acme-support / pass01:**
> *(authenticate as acme-support)*
```
GET kb_content/_search
{
  "query": { "match_all": {} },
  "_source": ["title", "tenant_id"],
  "size": 5
}
```
> "ACME support rep — sees only ACME documents."

**Query 4b — as globalnet-support / pass01:**
> *(authenticate as globalnet-support)*
```
GET kb_content/_search
{
  "query": { "match_all": {} },
  "_source": ["title", "tenant_id"],
  "size": 5
}
```
> "GlobalNet rep — same query, same index, completely different result set.
> Zero ACME documents visible. This is enforced by the query engine.
> There is no application code that can accidentally skip this filter.
> No race condition, no misconfiguration, no cross-tenant bleed."

**Closing line:**
> "That's your retrieval layer. Connector to index to hybrid search to tenant isolation.
> You plug your generation on top — Bedrock, your in-house model, unchanged.
> We can set up your POC environment and let your team run their own test queries
> against this exact stack."

---

## If Asked About Chunking (likely)

> "Hard chunking is what breaks on your large PDFs with tables and visual layouts.
> Jina uses semantic chunking — it finds natural content boundaries,
> not character counts. A table stays together. A procedure stays together.
> And in about a month, Jina v5 multimodal ships — same embedding space,
> no re-indexing, and it handles PDFs with images natively."

## If Asked About Connectors Running on Docker/K8s

> "Connectors run as a standalone Python process — they can run on any VM or AMI.
> No containers required. One connector service per region handles all tenants
> in that region via the connector API."

## If Asked About Cost / Sizing

> "For the POC: 2 data nodes + 1 ML node + 1 Kibana node, Enterprise license.
> For production sizing — 200 QPS per region, 21 regions, avg 5K docs per tenant —
> I'll send you a per-region architecture doc this week with the node counts and specs."

---

## Timing Guide

| Section | Target time | Cumulative |
|---------|-------------|------------|
| Opening | 1 min | 1 min |
| Beat 1: BM25 | 5 min | 6 min |
| Beat 2: Semantic | 7 min | 13 min |
| Beat 3: Hybrid | 8 min | 21 min |
| Beat 4: Multi-tenancy | 7 min | 28 min |
| Buffer / Q&A | 2 min | 30 min |

**Hard stop at 30 min — Shankar has school run at 9:00 AM.**
