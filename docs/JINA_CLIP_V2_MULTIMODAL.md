# Jina Clip v2 — Multimodal Search (9.4+)

Jina Clip v2 is a multimodal embedding model available as a built-in EIS endpoint in
Elastic 9.4. It embeds **text and images into the same vector space**, so a text query
can retrieve images and vice versa — without any API key or ML node deployment.

## When to use it

Use `.jina-clip-v2` in a demo when the customer scenario involves:

- **Product catalog search** by photo or natural-language description
- **Insurance claim triage** using damage photos + text descriptions
- **E-commerce visual search** ("find shoes that look like this")
- **Brand compliance / asset management** — search a media library by description
- **Manufacturing defect retrieval** — match a photo to known defect records
- **Real estate listing search** — "modern kitchen with white cabinets"

## When NOT to use it

- Text-only RAG demos (use `.jina-embeddings-v5-text-small` — larger context window, better for long documents)
- Documents where images are incidental (logos, icons) rather than central to the query
- Demos where the text corpus is not in the languages Clip v2 supports well

## Endpoint details

| Property | Value |
|---|---|
| Inference ID | `.jina-clip-v2` |
| Output dimensions | 1024 |
| Inputs | text OR image (base64, data URI, or URL) |
| Infrastructure | EIS built-in (no ML nodes, no API key) |
| Shared vector space | Yes — text ↔ image cross-retrieval works |

## Index mapping pattern

Use `semantic_text` with an explicit `inference_id`:

```json
{
  "mappings": {
    "properties": {
      "product_name":    { "type": "text" },
      "description":     { "type": "text" },
      "visual_content":  {
        "type": "semantic_text",
        "inference_id": ".jina-clip-v2"
      }
    }
  }
}
```

`visual_content` can accept either text descriptions or image payloads — Elasticsearch
routes them through Clip v2 and stores vectors in the same semantic field.

## Query pattern

Text query retrieving across text-and-image corpus:

```esql
FROM products METADATA _score
| WHERE MATCH(visual_content, "red leather ankle boots with low heel")
| SORT _score DESC
| LIMIT 10
```

Image query (the application passes the image to the endpoint and supplies the
resulting vector or a `semantic_text` match over the stored image field).

## Demo narrative hooks

- **"One index, two modalities"** — single index serves both text and image queries
- **"No ML nodes, no GPU"** — EIS handles all inference
- **"Cross-modal retrieval"** — text query finds images, image query finds text descriptions
- **Pairs well with RERANK** — use `.jina-reranker-v3` to refine hybrid multimodal results

## Guardrails

- Clip v2 is optimized for shorter content than text-v5. For PDF / long-document demos, prefer `.jina-embeddings-v5-text-small`.
- Don't mix Clip v2 and text-v5 vectors in the same field — different vector spaces.
- If the demo needs both deep document search AND image search, use two separate
  `semantic_text` fields each pointing at the appropriate inference endpoint.
