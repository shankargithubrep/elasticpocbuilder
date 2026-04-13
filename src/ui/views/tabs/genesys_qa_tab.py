"""
Genesys Knowledge AI — Live Q&A Demo Tab

Split-screen interface showing:
  LEFT  (chat panel)   — ChatGPT-style Q&A powered by Anthropic Claude
  RIGHT (hood panel)   — Elasticsearch query, retrieved chunks with scores & metadata

Features:
  • Scenario presets   — one-click combos that guarantee working tenant+index pairs
  • Contextual toggle  — standard chunk vs chunk-with-context (answers Balaji's question)
  • CSV fallback       — works without Elasticsearch; loads real data from genesys_faq_sop.csv
  • Suggested prompts  — click-to-ask for a fluid demo

Bug-fix notes:
  • _csv_search() provides real retrieval when the ES index is not yet populated
  • Preset sync writes to session_state BEFORE rendering disabled selectboxes
  • st.chat_input is at the top level (not inside a column)
"""

import os
import json
import time
import datetime
import logging
import streamlit as st
from pathlib import Path
from typing import Any

from src.services import llamaindex_rag_service

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

TENANTS = {
    "Eurobank AG (Frankfurt)":  "tenant-EUROBANK-EU-014",
    "FINSERV EU (Dublin)":      "tenant-FINSERV-EU-009",
    "ACME Corp":                "tenant-ACME-EU-001",
    "Globocom LATAM":           "tenant-GLOBOCOM-LATAM-007",
}

INDEX_OPTIONS = {
    "FAQ / SOP Articles":      ["genesys_faq_sop"],
    "Enterprise PDF Chunks":   ["enterprise_pdf_chunks"],
    "Both (FAQ + PDF Chunks)": ["genesys_faq_sop", "enterprise_pdf_chunks"],
}

# Curated combos — tenant + index guaranteed to have data.
# Value: (tenant_label, index_label) — sets both dropdowns at once.
SCENARIO_PRESETS = {
    "— Custom (pick manually) —":                        None,
    "🏦 Eurobank · GDPR & Compliance (FAQ/SOP)":        ("Eurobank AG (Frankfurt)", "FAQ / SOP Articles"),
    "🏦 Eurobank · SLA Penalty Clauses (PDFs)":         ("Eurobank AG (Frankfurt)", "Enterprise PDF Chunks"),
    "🏦 Eurobank · Full Knowledge Base (FAQ + PDFs)":   ("Eurobank AG (Frankfurt)", "Both (FAQ + PDF Chunks)"),
    "🏢 FINSERV EU · FAQ / SOP Articles":               ("FINSERV EU (Dublin)",     "FAQ / SOP Articles"),
    "🏢 FINSERV EU · Full Knowledge Base":              ("FINSERV EU (Dublin)",     "Both (FAQ + PDF Chunks)"),
    "🏭 ACME Corp · FAQ / SOP Articles":                ("ACME Corp",               "FAQ / SOP Articles"),
    "🌐 Globocom LATAM · FAQ / SOP (Spanish)":          ("Globocom LATAM",          "FAQ / SOP Articles"),
}

# Default prompts (Custom / PDF-only scenarios)
SUGGESTED_PROMPTS = [
    "What is the P1 escalation procedure?",
    "How are SLA penalty credits calculated?",
    "What are the GDPR article 17 deletion steps?",
    "What happens if Genesys misses the response time target?",
    "What is in the SLA-ENT-2024-001 service agreement?",
    "What are the network topology details for EU deployment?",
]

# Scenario-specific prompts — matched to actual data in each tenant/index combo
SCENARIO_PROMPTS: dict[str, list[str]] = {
    "🏦 Eurobank · GDPR & Compliance (FAQ/SOP)": [
        "What is the P1 escalation procedure?",
        "What are the GDPR article 17 deletion steps?",
        "How do I handle a GDPR Article 15 access request?",
        "What is the full P1 war-room and post-incident review process?",
        "What is the compliance recording policy?",
        "How do I onboard a new agent to the platform?",
    ],
    "🏦 Eurobank · SLA Penalty Clauses (PDFs)": [
        "What is the P1 escalation procedure?",
        "How are SLA penalty credits calculated?",
        "What happens if Genesys misses the response time target?",
        "What are the GDPR article 17 deletion steps?",
        "What is in the SLA-ENT-2024-001 agreement?",
        "What are the EU network topology details?",
    ],
    "🏦 Eurobank · Full Knowledge Base (FAQ + PDFs)": [
        "What is the full P1 incident response procedure including war-room steps?",
        "How are SLA availability breaches detected and credits calculated?",
        "What are the GDPR Article 17 deletion steps?",
        "What happens if Genesys misses the response time target?",
        "How do I configure voice queue routing for a new product line?",
        "What is the monthly SLA reporting cycle?",
    ],
    "🏢 FINSERV EU · FAQ / SOP Articles": [
        "How do I configure a new IVR menu?",
        "How do I set up email routing rules with priority tiers?",
        "What do I do if customer data is exposed in a breach?",
        "How do I set up omnichannel routing with voice, email, chat and WhatsApp?",
        "How do I configure the WhatsApp Business channel for FINSERV?",
        "What are the FCA compliance requirements for email recording?",
    ],
    "🏢 FINSERV EU · Full Knowledge Base": [
        "How do I configure a new IVR menu?",
        "How do I set up omnichannel routing with voice, email and WhatsApp?",
        "What do I do if customer data is exposed in a breach?",
        "What are the SLA penalty credits?",
        "What is the tier 2 escalation procedure?",
        "What is the P1 escalation procedure?",
    ],
    "🏭 ACME Corp · FAQ / SOP Articles": [
        "How do I set up the email channel in Genesys Cloud CX?",
        "How do I configure advanced email routing rules?",
        "How do I troubleshoot emails landing in spam folders?",
        "What is the QA review process for contact centre interactions?",
        "What are the different agent licence types?",
        "How do I configure DKIM and SPF for outbound email deliverability?",
    ],
    "🌐 Globocom LATAM · FAQ / SOP (Spanish)": [
        "How do I configure the Spanish IVR?",
        "How do I set up WhatsApp Business for Mexico and Colombia?",
        "What are the LATAM digital channel compliance rules?",
        "¿Cómo configuro el IVR en español?",
        "What are the P1 escalation steps for the voice platform?",
        "How do I handle LGPD deletion requests in Brazil?",
    ],
}

_CSS = """
<style>
.qa-header {
    background: linear-gradient(135deg, #005571 0%, #00bfb3 100%);
    color: white; border-radius: 10px; padding: 18px 24px; margin-bottom: 16px;
}
.qa-header h3 { margin: 0; font-size: 1.3rem; }
.qa-header p  { margin: 4px 0 0; opacity: .85; font-size: .82rem; }
.hood-section { font-size: .78rem; color: #555; margin-bottom: 4px; font-weight: 600;
                text-transform: uppercase; letter-spacing: .05em; }
.chunk-card {
    border-left: 3px solid #00bfb3; background: #f8fdfd;
    border-radius: 6px; padding: 10px 12px; margin-bottom: 8px;
    font-size: .82rem;
}
.chunk-card .chunk-title { font-weight: 600; color: #005571; }
.chunk-card .chunk-meta  { color: #777; font-size: .75rem; margin: 2px 0 6px; }
.chunk-card .chunk-body  { color: #333; line-height: 1.45; }
.score-pill {
    display: inline-block; background: #e6f7f6; color: #007a73;
    border-radius: 12px; padding: 1px 8px; font-size: .72rem;
    font-weight: 700; margin-left: 6px;
}
.user-msg  { background: #f0f4ff; border-radius: 8px; padding: 10px 14px;
             margin: 6px 0; font-size: .88rem; }
.asst-msg  { background: #f8f8f8; border-radius: 8px; padding: 10px 14px;
             margin: 6px 0; font-size: .88rem; line-height: 1.55; }
.source-chip {
    display: inline-block; background: #eef6f5; color: #005571;
    border: 1px solid #c0dedd; border-radius: 10px;
    padding: 2px 9px; font-size: .72rem; margin: 2px 3px 0 0;
}
.ctx-badge-on  { background:#d4f5f3; color:#006b66; border-radius:10px;
                 padding:2px 8px; font-size:.75rem; font-weight:600; }
.ctx-badge-off { background:#f0f0f0; color:#888; border-radius:10px;
                 padding:2px 8px; font-size:.75rem; font-weight:600; }
.fallback-note { background:#fff8e6; border-left:3px solid #f0a500;
                 border-radius:6px; padding:6px 10px; font-size:.75rem;
                 color:#7a5500; margin-bottom:6px; }
.metrics-panel { background:#f4fbfa; border:1px solid #c8ece9;
                 border-radius:8px; padding:10px 14px; margin-bottom:10px; }
.metrics-panel .mp-title { font-size:.70rem; font-weight:700; color:#005571;
                            text-transform:uppercase; letter-spacing:.05em;
                            margin-bottom:8px; }
/* 3-column breakdown grid */
.bd-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; }
.bd-section { background:#fff; border:1px solid #d6eeed; border-radius:7px;
              padding:8px 10px; }
.bd-section-label { font-size:.65rem; font-weight:700; color:#888;
                    text-transform:uppercase; letter-spacing:.06em; margin-bottom:3px; }
.bd-total { font-size:1.05rem; font-weight:800; margin-bottom:6px; line-height:1; }
.bd-total.fast { color:#009e97; }
.bd-total.warn { color:#c87600; }
.bd-total.slow { color:#c03030; }
.bd-row { display:flex; justify-content:space-between; align-items:baseline;
          font-size:.72rem; margin-bottom:2px; }
.bd-row-label { color:#777; }
.bd-row-val   { font-weight:600; color:#333; }
.bd-row-val.fast { color:#009e97; }
.bd-row-val.warn { color:#c87600; }
/* bar showing ES vs network proportion inside retrieval section */
.bd-bar-wrap { margin-top:5px; height:6px; background:#eee; border-radius:3px; overflow:hidden; }
.bd-bar-es   { height:100%; background:#00bfb3; float:left; }
.bd-bar-net  { height:100%; background:#f0a500; float:left; }
/* p95 session row */
.metric-row { display:flex; gap:6px; margin-bottom:4px; flex-wrap:wrap; }
.metric-chip { background:#fff; border:1px solid #b8e2df; border-radius:8px;
               padding:4px 10px; font-size:.76rem; color:#333; flex:1;
               min-width:70px; text-align:center; }
.metric-chip .mc-label { font-size:.65rem; color:#888; display:block; }
.metric-chip .mc-val   { font-weight:700; color:#005571; font-size:.88rem; }
.metric-chip.mc-fast   { border-color:#00bfb3; background:#e6faf9; }
.metric-chip.mc-warn   { border-color:#f0a500; background:#fff8e6; }
.metric-chip.mc-slow   { border-color:#e06060; background:#fff0f0; }
.p95-row { margin-top:6px; padding-top:6px; border-top:1px dashed #d0ecea; }
</style>
"""


# ── CSV-backed retrieval (works with or without Elasticsearch) ─────────────────

def _find_csv() -> Path | None:
    """Locate genesys_faq_sop.csv by searching all genesys demo folders."""
    base = Path(__file__).resolve().parent.parent.parent.parent / "demos"
    candidates = sorted(base.glob("genesys_*/data/genesys_faq_sop.csv"), reverse=True)
    return candidates[0] if candidates else None


def _csv_search(query_text: str, tenant_id: str,
                use_context: bool, size: int = 5) -> list[dict]:
    """
    Keyword-based retrieval from genesys_faq_sop.csv.
    Used as fallback when the ES index is empty or not yet created.
    """
    csv_path = _find_csv()
    if csv_path is None:
        return []

    try:
        import pandas as pd
        df = pd.read_csv(csv_path)
    except Exception as e:
        logger.warning(f"CSV load failed: {e}")
        return []

    # Tenant filter
    df = df[df["tenant_id"] == tenant_id]
    if df.empty:
        return []

    # Simple BM25-style keyword scoring
    # Keep all words ≥ 2 chars — short terms like "P1", "IVR", "SLA" are important
    stopwords = {"do", "to", "is", "in", "of", "the", "how", "what", "are",
                 "for", "and", "if", "an", "a", "i", "it", "at", "on"}
    words = [w.strip("?.,") for w in query_text.lower().split()
             if w.strip("?.,") not in stopwords and len(w.strip("?.,")) >= 2]
    content_col = (
        "content_with_context"
        if (use_context and "content_with_context" in df.columns)
        else "content"
    )

    def _score(row) -> float:
        haystack = (
            str(row.get("title", "")).lower() + " " +
            str(row.get(content_col, "")).lower()
        )
        return sum(1 for w in words if w in haystack)

    df = df.copy()
    df["_score"] = df.apply(_score, axis=1)
    df = df[df["_score"] > 0].sort_values("_score", ascending=False).head(size)

    hits = []
    max_score = df["_score"].max() if not df.empty else 1
    for _, row in df.iterrows():
        hits.append({
            "index":       "genesys_faq_sop",
            "score":       round(float(row["_score"]) / max(max_score, 1), 3),
            "id":          str(row.get("doc_id", "—")),
            "title":       str(row.get("title", "—")),
            "locale":      str(row.get("locale", "—")),
            "domain":      str(row.get("knowledge_domain", "—")),
            "doc_type":    str(row.get("doc_type", "faq")),
            "page":        None,
            "source_url":  str(row.get("source", "")) or None,
            "sensitivity": str(row.get("sensitivity", "internal")),
            "updated":     str(row.get("last_updated", "—")),
            "content":     str(row.get(content_col, "")),
            "_from_csv":   True,
        })
    return hits


# ── Elasticsearch helpers ──────────────────────────────────────────────────────

def _build_es_client():
    """Build Elasticsearch client from environment variables."""
    try:
        from elasticsearch import Elasticsearch
        api_key  = os.getenv("ELASTICSEARCH_API_KEY", "")
        cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
        if cloud_id:
            return Elasticsearch(cloud_id=cloud_id, api_key=api_key)
        endpoint = os.getenv("ELASTIC_ENDPOINT", "")
        if not endpoint:
            return None
        return Elasticsearch(endpoint, api_key=api_key)
    except Exception as e:
        logger.warning(f"Could not build ES client: {e}")
        return None


def _search_index(es, index: str, query_text: str, tenant_id: str,
                  use_context: bool, size: int = 5) -> tuple[list[dict], float]:
    """
    Run a match query against one ES index.
    Returns (hits, es_took_ms) where es_took_ms is the cluster-side execution
    time reported in the response `took` field (pure ES time, no network).
    """
    content_field = (
        "content_with_context"
        if (use_context and index == "genesys_faq_sop")
        else "content"
    )

    source_fields = [
        "doc_id", "chunk_id", "doc_type", "title", "section_title",
        "locale", "knowledge_domain", "page_number", "source_url",
        "sensitivity", "last_updated", "last_synced_at", content_field,
    ]

    body = {
        "query": {
            "bool": {
                "must":   {"match": {content_field: query_text}},
                "filter": [{"term": {"tenant_id": tenant_id}}],
            }
        },
        "_source": source_fields,
        "size": size,
    }

    try:
        resp = es.search(index=index, body=body)
    except Exception as e:
        logger.warning(f"ES search failed on {index}: {e}")
        return [], 0.0

    # `took` is the cluster-side execution time in milliseconds (excludes network)
    es_took_ms = float(resp.get("took", 0))

    hits = []
    for h in resp.get("hits", {}).get("hits", []):
        src = h.get("_source", {})
        hits.append({
            "index":       index,
            "score":       round(h.get("_score", 0), 3),
            "id":          src.get("doc_id") or src.get("chunk_id") or h["_id"],
            "title":       src.get("title") or src.get("section_title", "—"),
            "locale":      src.get("locale", "—"),
            "domain":      src.get("knowledge_domain", "—"),
            "doc_type":    src.get("doc_type", "chunk"),
            "page":        src.get("page_number"),
            "source_url":  src.get("source_url"),
            "sensitivity": src.get("sensitivity", "internal"),
            "updated":     src.get("last_updated") or src.get("last_synced_at"),
            "content":     src.get(content_field, ""),
            "_from_csv":   False,
        })
    return hits, es_took_ms


# Real _source fields per index — exactly what Kibana will return
_SOURCE_FIELDS = {
    "genesys_faq_sop": [
        "doc_id", "doc_type", "title", "locale",
        "knowledge_domain", "sensitivity", "source", "last_updated",
    ],
    "enterprise_pdf_chunks": [
        "chunk_id", "parent_doc_id", "section_title", "page_number",
        "locale", "knowledge_domain", "source_url", "last_synced_at",
        "structured_ids", "sensitivity",
    ],
}
_SOURCE_FIELDS_DEFAULT = [
    "doc_id", "chunk_id", "title", "section_title", "locale",
    "knowledge_domain", "sensitivity", "last_updated", "last_synced_at",
]


def _build_kibana_snippet(query_text: str, tenant_id: str,
                          indices: list[str], use_context: bool,
                          is_csv_fallback: bool = False) -> str:
    """
    Build a complete, copy-pasteable Kibana Dev Tools snippet.
    Format:  POST {index}/_search\n{ ... }
    For multiple indices: POST idx1,idx2/_search
    """
    index_str = ",".join(indices)

    # Determine content field per index (only faq_sop gets content_with_context)
    # For display we show the field used for the primary/first index
    primary_idx = indices[0]
    content_field = (
        "content_with_context"
        if (use_context and primary_idx == "genesys_faq_sop")
        else "content"
    )

    # Merge _source fields from all queried indices, add content field
    source_fields = []
    for idx in indices:
        for f in _SOURCE_FIELDS.get(idx, _SOURCE_FIELDS_DEFAULT):
            if f not in source_fields:
                source_fields.append(f)
    if content_field not in source_fields:
        source_fields.append(content_field)

    body = {
        "query": {
            "bool": {
                "must":   {"match": {content_field: query_text}},
                "filter": [{"term": {"tenant_id": tenant_id}}],
            }
        },
        "_source": source_fields,
        "size": 5,
    }

    fallback_comment = (
        "\n// NOTE: genesys_faq_sop not yet indexed — results below from CSV fallback.\n"
        "// Go to Data tab → Index All Datasets to activate live retrieval.\n"
        if is_csv_fallback else ""
    )

    return f"POST {index_str}/_search\n{fallback_comment}{json.dumps(body, indent=2)}"


def _build_esql_snippet(query_text: str, tenant_id: str,
                        indices: list[str], use_context: bool) -> str:
    """
    ES|QL equivalent of the retrieval query — runnable in Kibana Console (ES|QL tab).
    Uses MATCH() for full-text search + WHERE for tenant scoping.
    """
    content_field = (
        "content_with_context"
        if (use_context and "genesys_faq_sop" in indices)
        else "content"
    )
    # ES|QL doesn't support comma-separated multi-index in FROM with MATCH the same way;
    # show the primary index and note the secondary if both are selected.
    primary = indices[0]
    note = (
        f"\n// Also run against: {indices[1]} (replace FROM index above)"
        if len(indices) > 1 else ""
    )
    keep_fields = {
        "genesys_faq_sop": f"doc_id, doc_type, title, locale, knowledge_domain, {content_field}",
        "enterprise_pdf_chunks": f"chunk_id, section_title, page_number, locale, knowledge_domain, {content_field}",
    }.get(primary, f"_id, {content_field}")

    return (
        f'FROM {primary}{note}\n'
        f'| WHERE tenant_id == "{tenant_id}"\n'
        f'| WHERE MATCH({content_field}, "{query_text}")\n'
        f'| KEEP {keep_fields}\n'
        f'| LIMIT 5'
    )


def _retrieve(query_text: str, tenant_id: str,
              indices: list[str], use_context: bool) -> tuple[list[dict], str, dict]:
    """
    Run retrieval. ES first; CSV fallback if ES is unavailable or index is empty.
    Returns (hits, kibana_snippet, timing) where timing contains:
      - es_took_ms: sum of `took` fields from all ES responses (pure cluster time)
      - is_csv_fallback: bool
    """
    es = _build_es_client()
    all_hits: list[dict] = []
    total_es_took_ms = 0.0

    if es is not None:
        for idx in indices:
            idx_hits, idx_took = _search_index(es, idx, query_text, tenant_id, use_context)
            all_hits.extend(idx_hits)
            total_es_took_ms += idx_took

    # ── Fallback: CSV-based retrieval when ES index is empty or not created ───
    faq_in_indices = "genesys_faq_sop" in indices
    faq_hits_from_es = [h for h in all_hits if h["index"] == "genesys_faq_sop"]
    is_csv_fallback = False

    if faq_in_indices and not faq_hits_from_es:
        csv_hits = _csv_search(query_text, tenant_id, use_context)
        all_hits.extend(csv_hits)
        is_csv_fallback = bool(csv_hits)

    all_hits.sort(key=lambda h: h["score"], reverse=True)
    snippet = _build_kibana_snippet(
        query_text, tenant_id, indices, use_context, is_csv_fallback
    )
    timing = {
        "es_took_ms":    round(total_es_took_ms, 1),
        "is_csv_fallback": is_csv_fallback,
    }
    return all_hits[:5], snippet, timing


# ── Claude answer generation ───────────────────────────────────────────────────

def _build_system_prompt(use_context: bool) -> str:
    mode = (
        "contextual (each chunk includes document origin and domain metadata)"
        if use_context
        else "standard (raw chunk text only, no document metadata)"
    )
    return (
        "You are a helpful assistant for a Genesys Knowledge AI platform. "
        "You answer agent questions using ONLY the knowledge base chunks provided. "
        f"Retrieval mode is: {mode}. "
        "Always cite the source document ID and title. "
        "If the answer is not in the provided chunks, say clearly: "
        "'I could not find an answer for this tenant in the indexed knowledge base.' "
        "Be concise and professional. Format lists with dashes."
    )


def _build_user_prompt(question: str, hits: list[dict]) -> str:
    context_blocks = []
    for i, h in enumerate(hits, 1):
        page_note = f", page {h['page']}" if h.get("page") else ""
        context_blocks.append(
            f"[Chunk {i} | ID: {h['id']} | \"{h['title']}\"{page_note} | "
            f"Locale: {h['locale']} | Domain: {h['domain']} | Score: {h['score']}]\n"
            f"{h['content']}"
        )
    context_str = (
        "\n\n---\n\n".join(context_blocks)
        if context_blocks
        else "No relevant chunks found for this tenant."
    )
    return f"Context chunks:\n\n{context_str}\n\n---\n\nQuestion: {question}"


def _generate_answer(question: str, hits: list[dict],
                     use_context: bool) -> tuple[str, dict]:
    """
    Call Anthropic Claude and return (answer_text, usage).
    usage = {input_tokens, output_tokens} — taken directly from the API response.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return (
            "_Anthropic API key not configured. Set `ANTHROPIC_API_KEY` in your .env to enable "
            "live answer generation._\n\n"
            "**Demo note**: Claude receives the retrieved chunks above as context and generates "
            "a grounded, cited answer. The retrieval adapter returns the same Bedrock KB response "
            "shape — Answer Gen never knows the backend changed.",
            {},
        )

    try:
        from anthropic import Anthropic
        client  = Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=_build_system_prompt(use_context),
            messages=[{"role": "user", "content": _build_user_prompt(question, hits)}],
        )
        usage = {
            "input_tokens":  message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens,
        }
        return message.content[0].text, usage
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        return f"_Error generating answer: {e}_", {}


# ── UI helpers ─────────────────────────────────────────────────────────────────

def _render_chunk_card(h: dict, idx: int) -> None:
    page_note   = f" · p.{h['page']}" if h.get("page") else ""
    source_note = f" · {h['index']}"
    csv_badge   = " · <em>CSV fallback</em>" if h.get("_from_csv") else ""
    st.markdown(
        f"""<div class="chunk-card">
            <span class="chunk-title">{idx}. {h['title']}</span>
            <span class="score-pill">score {h['score']}</span>
            <div class="chunk-meta">
                {h['id']}{page_note}{source_note} · {h['locale']} · {h['domain']}{csv_badge}
            </div>
            <div class="chunk-body">{h['content'][:300]}{'…' if len(h['content']) > 300 else ''}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def _render_sources(hits: list[dict]) -> None:
    if not hits:
        return
    chips = "".join(
        f'<span class="source-chip">{h["id"]} — {h["title"][:35]}</span>'
        for h in hits
    )
    st.markdown(f"**Sources:** {chips}", unsafe_allow_html=True)


def _render_message(msg: dict) -> None:
    if msg["role"] == "user":
        st.markdown(
            f'<div class="user-msg">👤 {msg["content"]}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="asst-msg">{msg["content"]}</div>',
            unsafe_allow_html=True,
        )
        if msg.get("hits"):
            _render_sources(msg["hits"])


# ── Metrics helpers ────────────────────────────────────────────────────────────

def _percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    sv = sorted(values)
    idx = max(0, int(len(sv) * p / 100) - 1)
    return sv[min(idx, len(sv) - 1)]


def _speed_class(ms: float) -> str:
    """CSS class for colouring a latency chip: fast <500ms, warn <1500ms, slow ≥1500ms."""
    if ms < 500:
        return "mc-fast"
    if ms < 1500:
        return "mc-warn"
    return "mc-slow"


def _render_metrics_panel() -> None:
    """Render the detailed latency breakdown panel inside the hood column."""
    log: list[dict] = st.session_state.get("qa_latency_log", [])
    last: dict      = st.session_state.get("qa_last_metrics", {})

    if not last:
        return

    r_ms      = last.get("retrieval_ms", 0)
    es_took   = last.get("es_took_ms", 0)
    net_ms    = last.get("network_ms", 0)
    g_ms      = last.get("gen_ms", 0)
    in_tok    = last.get("input_tokens", 0)
    out_tok   = last.get("output_tokens", 0)
    tok_s     = last.get("tokens_per_sec", 0)
    tot_ms    = last.get("total_ms", 0)
    hits      = last.get("hits", 0)
    avg_sc    = last.get("avg_score", 0.0)
    source    = last.get("source", "ES")
    q_num     = last.get("query_num", "?")
    at_time   = last.get("wall_clock", "")
    ts_note   = f"Query #{q_num}" + (f" &nbsp;·&nbsp; {at_time}" if at_time else "")

    # Proportional bar for ES vs network (retrieval section)
    if r_ms > 0:
        es_pct  = min(100, round(es_took  / r_ms * 100))
        net_pct = 100 - es_pct
    else:
        es_pct = net_pct = 50

    # ── Retrieval section ────────────────────────────────────────────────────
    ret_class = _speed_class(r_ms)
    ret_html  = (
        f'<div class="bd-section">'
        f'  <div class="bd-section-label">📡 Retrieval</div>'
        f'  <div class="bd-total {ret_class}">{r_ms:.0f} ms</div>'
        f'  <div class="bd-row">'
        f'    <span class="bd-row-label">ES cluster (took)</span>'
        f'    <span class="bd-row-val fast">{es_took:.0f} ms</span>'
        f'  </div>'
        f'  <div class="bd-row">'
        f'    <span class="bd-row-label">Network + overhead</span>'
        f'    <span class="bd-row-val warn">{net_ms:.0f} ms</span>'
        f'  </div>'
        f'  <div class="bd-bar-wrap">'
        f'    <div class="bd-bar-es"  style="width:{es_pct}%"></div>'
        f'    <div class="bd-bar-net" style="width:{net_pct}%"></div>'
        f'  </div>'
        f'  <div class="bd-row" style="margin-top:3px;font-size:.62rem;color:#aaa;">'
        f'    <span>■ ES {es_pct}%</span><span>■ net {net_pct}%</span>'
        f'  </div>'
        f'</div>'
    )

    # ── Generation section ───────────────────────────────────────────────────
    gen_class = _speed_class(g_ms)
    tok_note  = f"~{tok_s:.0f} tok/s" if tok_s else "—"
    gen_html  = (
        f'<div class="bd-section">'
        f'  <div class="bd-section-label">🤖 Generation</div>'
        f'  <div class="bd-total {gen_class}">{g_ms:.0f} ms</div>'
        f'  <div class="bd-row">'
        f'    <span class="bd-row-label">Input tokens</span>'
        f'    <span class="bd-row-val">{in_tok:,}</span>'
        f'  </div>'
        f'  <div class="bd-row">'
        f'    <span class="bd-row-label">Output tokens</span>'
        f'    <span class="bd-row-val">{out_tok:,}</span>'
        f'  </div>'
        f'  <div class="bd-row">'
        f'    <span class="bd-row-label">Throughput</span>'
        f'    <span class="bd-row-val">{tok_note}</span>'
        f'  </div>'
        f'</div>'
    )

    # ── End-to-end section ───────────────────────────────────────────────────
    e2e_class = _speed_class(tot_ms)
    e2e_html  = (
        f'<div class="bd-section">'
        f'  <div class="bd-section-label">⏱ End-to-End</div>'
        f'  <div class="bd-total {e2e_class}">{tot_ms:.0f} ms</div>'
        f'  <div class="bd-row">'
        f'    <span class="bd-row-label">Chunks</span>'
        f'    <span class="bd-row-val">{hits}</span>'
        f'  </div>'
        f'  <div class="bd-row">'
        f'    <span class="bd-row-label">Avg score</span>'
        f'    <span class="bd-row-val">{avg_sc:.3f}</span>'
        f'  </div>'
        f'  <div class="bd-row">'
        f'    <span class="bd-row-label">Source</span>'
        f'    <span class="bd-row-val">{source}</span>'
        f'  </div>'
        f'</div>'
    )

    # ── Session p50/p95 (shown once ≥3 queries) ──────────────────────────────
    pct_html = ""
    if len(log) >= 3:
        totals = [e["total_ms"]    for e in log]
        rets   = [e["retrieval_ms"] for e in log]
        nets   = [e.get("network_ms", 0) for e in log]
        es_ts  = [e.get("es_took_ms", 0) for e in log]
        gens   = [e["gen_ms"]      for e in log]
        n      = len(log)
        pct_html = (
            f'<div class="p95-row">'
            f'<div class="mp-title">Session Percentiles (n={n})</div>'
            f'<div class="metric-row">'
            f'  <div class="metric-chip"><span class="mc-label">p50 Total</span>'
            f'    <span class="mc-val">{_percentile(totals,50):.0f} ms</span></div>'
            f'  <div class="metric-chip {_speed_class(_percentile(totals,95))}"><span class="mc-label">p95 Total</span>'
            f'    <span class="mc-val">{_percentile(totals,95):.0f} ms</span></div>'
            f'  <div class="metric-chip"><span class="mc-label">p50 ES took</span>'
            f'    <span class="mc-val">{_percentile(es_ts,50):.0f} ms</span></div>'
            f'  <div class="metric-chip {_speed_class(_percentile(es_ts,95))}"><span class="mc-label">p95 ES took</span>'
            f'    <span class="mc-val">{_percentile(es_ts,95):.0f} ms</span></div>'
            f'  <div class="metric-chip"><span class="mc-label">p50 Network</span>'
            f'    <span class="mc-val">{_percentile(nets,50):.0f} ms</span></div>'
            f'  <div class="metric-chip {_speed_class(_percentile(nets,95))}"><span class="mc-label">p95 Network</span>'
            f'    <span class="mc-val">{_percentile(nets,95):.0f} ms</span></div>'
            f'  <div class="metric-chip {_speed_class(_percentile(gens,95))}"><span class="mc-label">p95 Generation</span>'
            f'    <span class="mc-val">{_percentile(gens,95):.0f} ms</span></div>'
            f'</div>'
            f'</div>'
        )

    st.markdown(
        f'<div class="metrics-panel">'
        f'  <div class="mp-title">Latency Breakdown &nbsp;·&nbsp; {ts_note}</div>'
        f'  <div class="bd-grid">{ret_html}{gen_html}{e2e_html}</div>'
        f'  {pct_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Main render ────────────────────────────────────────────────────────────────

def render_genesys_qa_tab(loader: Any = None) -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    # Header
    st.markdown(
        '<div class="qa-header">'
        "<h3>Genesys Knowledge AI — Live Q&A</h3>"
        "<p>Retrieval powered by Elasticsearch · Answer generation powered by Anthropic Claude · "
        "Tenant-scoped · Multilingual</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Session state init ────────────────────────────────────────────────────
    for key, default in [
        ("qa_messages",        []),
        ("qa_last_hits",       []),
        ("qa_last_kibana_snippet", ""),
        ("qa_rag_engine",      "Direct (Elastic)"),
        ("qa_scenario",        list(SCENARIO_PRESETS.keys())[0]),
        ("qa_tenant",          list(TENANTS.keys())[0]),
        ("qa_index",           list(INDEX_OPTIONS.keys())[0]),
        ("qa_context_mode",    False),
        ("qa_latency_log",      []),   # list of {retrieval_ms, gen_ms, total_ms, hits, avg_score}
        ("qa_last_metrics",    {}),
        ("qa_last_gen_details", {}),  # {model, max_tokens, context_chars, num_chunks, question}
        ("qa_last_esql",        ""),  # ES|QL version of the last retrieval query
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # ── Row 1: Scenario preset + contextual toggle + RAG engine + clear ─────────
    r1c1, r1c2, r1c3, r1c4 = st.columns([4, 2, 2, 1])

    with r1c1:
        scenario_label = st.selectbox(
            "Demo Scenario",
            options=list(SCENARIO_PRESETS.keys()),
            key="qa_scenario",
            help=(
                "Pick a curated scenario — auto-sets tenant and index to a combo that "
                "has data. Choose '— Custom —' to configure them independently."
            ),
        )

    preset = SCENARIO_PRESETS[scenario_label]

    # ── FIX: sync session_state BEFORE rendering the disabled selectboxes ──────
    if preset is not None:
        st.session_state["qa_tenant"] = preset[0]
        st.session_state["qa_index"]  = preset[1]

    with r1c2:
        use_context = st.toggle(
            "Contextual Retrieval",
            key="qa_context_mode",
            help=(
                "OFF — raw chunk text sent to Claude.\n\n"
                "ON — each chunk includes a context prefix (parent document, domain, "
                "tenant, source). Claude's citations become more precise — directly "
                "answers the 'chunk-with-context' question."
            ),
        )
        badge = (
            '<span class="ctx-badge-on">With Context</span>'
            if use_context
            else '<span class="ctx-badge-off">Standard Chunks</span>'
        )
        st.markdown(badge, unsafe_allow_html=True)

    with r1c3:
        _li_available = llamaindex_rag_service.is_available()
        rag_engine = st.selectbox(
            "RAG Engine",
            options=["Direct (Elastic)", "LlamaIndex"],
            key="qa_rag_engine",
            disabled=not _li_available,
            help=(
                "Direct — manual retrieval + Claude call (existing pipeline).\n\n"
                "LlamaIndex — LlamaIndex response synthesizer orchestrates prompt "
                "assembly and Claude call on top of the same Elasticsearch hits.\n\n"
                + ("" if _li_available
                   else "⚠️ LlamaIndex not installed. Run: "
                        "pip install llama-index-core llama-index-llms-anthropic")
            ),
        )

    with r1c4:
        st.write("")
        if st.button("Clear chat", use_container_width=True, key="qa_clear"):
            st.session_state.qa_messages            = []
            st.session_state.qa_last_hits           = []
            st.session_state.qa_last_kibana_snippet = ""
            st.session_state.qa_latency_log         = []
            st.session_state.qa_last_metrics        = {}
            st.session_state.qa_last_gen_details    = {}
            st.session_state.qa_last_esql           = ""
            st.rerun()

    # ── Row 2: Tenant + Index dropdowns (read-only when preset active) ─────────
    c1, c2, c3 = st.columns([2, 2, 3])

    with c1:
        st.selectbox(
            "Tenant",
            options=list(TENANTS.keys()),
            key="qa_tenant",
            disabled=preset is not None,
            help="All retrieval is scoped to this tenant — demonstrates DLS in action.",
        )

    with c2:
        st.selectbox(
            "Index",
            options=list(INDEX_OPTIONS.keys()),
            key="qa_index",
            disabled=preset is not None,
            help="Choose which Elasticsearch index(es) to retrieve from.",
        )

    with c3:
        if preset is not None:
            st.markdown(
                '<div style="font-size:.78rem;color:#888;margin-top:24px;">'
                "🔒 Locked by scenario — choose '— Custom —' to unlock</div>",
                unsafe_allow_html=True,
            )

    # Resolve effective tenant + index from session state (already synced above)
    tenant_id = TENANTS[st.session_state["qa_tenant"]]
    indices   = INDEX_OPTIONS[st.session_state["qa_index"]]

    # ── Suggested prompts — scenario-aware ────────────────────────────────────
    active_prompts = SCENARIO_PROMPTS.get(scenario_label, SUGGESTED_PROMPTS)
    st.markdown("**Try a question:**")
    prompt_cols = st.columns(len(active_prompts))
    clicked_prompt = None
    for col, prompt in zip(prompt_cols, active_prompts):
        with col:
            if st.button(prompt, use_container_width=True, key=f"sp_{hash(prompt) % 99999}"):
                clicked_prompt = prompt

    st.divider()

    # ── Main split layout ─────────────────────────────────────────────────────
    chat_col, hood_col = st.columns([3, 2], gap="medium")

    with chat_col:
        st.markdown("#### Answer")
        for msg in st.session_state.qa_messages:
            _render_message(msg)

    with hood_col:
        st.markdown("#### Under the Hood")

        snippet = st.session_state.get("qa_last_kibana_snippet", "")

        # If hits exist but snippet is stale/empty (e.g. after a code deploy),
        # rebuild it live from the last question in message history.
        if st.session_state.qa_last_hits and not snippet:
            last_q = next(
                (m["content"] for m in reversed(st.session_state.qa_messages) if m["role"] == "user"),
                None,
            )
            if last_q:
                snippet = _build_kibana_snippet(last_q, tenant_id, indices, use_context)
                st.session_state.qa_last_kibana_snippet = snippet

        if not st.session_state.qa_last_hits and not snippet:
            st.info(
                "Ask a question to see the Elasticsearch query and retrieved chunks here.\n\n"
                "This panel shows exactly what the retrieval adapter sends to Claude — "
                "before any answer is generated."
            )
        else:
            # ── Metrics panel — latency + quality ─────────────────────────────
            _render_metrics_panel()

            # ── Query drilldowns — collapsible, directly under the numbers ────
            esql    = st.session_state.get("qa_last_esql", "")
            gd      = st.session_state.get("qa_last_gen_details", {})

            with st.expander("📡 Retrieval Query — Kibana Console & ES|QL", expanded=False):
                tab_kibana, tab_esql = st.tabs(["Kibana Dev Tools (_search)", "ES|QL (Console)"])
                with tab_kibana:
                    st.caption(
                        "Paste into **Kibana → Dev Tools → Console** "
                        "(make sure you're connected to the correct deployment)."
                    )
                    st.code(snippet, language="json")
                with tab_esql:
                    st.caption(
                        "Paste into **Kibana → Dev Tools → ES|QL** tab. "
                        "`MATCH()` triggers the same Jina dense-vector retrieval as the `_search` call above."
                    )
                    st.code(esql if esql else "# Ask a question first", language="sql")

            if gd:
                ctx_chars = gd.get("context_chars", 0)
                est_tok   = gd.get("est_tokens", 0)
                gen_ms    = gd.get("gen_ms", 0)
                model     = gd.get("model", "—")
                n_chunks  = gd.get("num_chunks", 0)
                with st.expander("🤖 Generation Call — Claude API parameters", expanded=False):
                    st.caption(
                        f"**What caused the {gen_ms:.0f} ms?** "
                        f"Claude received {n_chunks} chunks → ~{ctx_chars:,} chars "
                        f"(~{est_tok:,} tokens) of context. "
                        f"Sonnet 4.6 processes & generates at 80–120 tokens/s — "
                        f"so {gen_ms/1000:.1f}s for a detailed response is expected. "
                        f"Larger chunks = richer answers = longer generation time."
                    )
                    call_summary = {
                        "model":       model,
                        "max_tokens":  1024,
                        "context": {
                            "chunks":         n_chunks,
                            "context_chars":  ctx_chars,
                            "input_tokens":   gd.get("input_tokens", "—"),
                            "output_tokens":  gd.get("output_tokens", "—"),
                        },
                        "system": _build_system_prompt(use_context),
                        "user_message": f"Context chunks:\n\n[{n_chunks} chunks — see Retrieved Chunks panel]\n\n---\n\nQuestion: {gd.get('question','')}",
                    }
                    st.code(json.dumps(call_summary, indent=2), language="json")

            # ── Retrieved Chunks — shown FIRST so always visible ──────────────
            hit_count = len(st.session_state.qa_last_hits)
            ctx_label = "contextual" if use_context else "standard"
            st.markdown(
                f'<div class="hood-section">Retrieved Chunks ({hit_count} · {ctx_label})</div>',
                unsafe_allow_html=True,
            )

            if st.session_state.qa_last_hits:
                for i, h in enumerate(st.session_state.qa_last_hits, 1):
                    _render_chunk_card(h, i)
            else:
                st.warning(
                    f"No chunks found for tenant `{tenant_id}` in `{', '.join(indices)}`. "
                    "Check that the index is populated (Data tab → Index All Datasets)."
                )

            if use_context:
                st.caption(
                    "Contextual mode ON — each chunk includes a context prefix. "
                    "Claude's citations are more precise."
                )
            else:
                st.caption(
                    "Standard mode — raw chunk text only. "
                    "Toggle Contextual Retrieval above to see the difference."
                )

            # CSV fallback notice (shown inline, no duplicate snippet)
            is_csv = snippet and "CSV fallback" in snippet
            if is_csv:
                st.markdown(
                    '<div class="fallback-note">⚠️ <strong>genesys_faq_sop</strong> not yet '
                    "indexed — results come from CSV fallback. "
                    "Go to <strong>Data</strong> tab → <strong>Index All Datasets</strong> "
                    "to activate live retrieval.</div>",
                    unsafe_allow_html=True,
                )

    # ── FIX: chat_input at top-level (not inside a column) ────────────────────
    user_input = st.chat_input(
        "Ask a question about this tenant's knowledge base…",
        key="qa_input",
    )

    question = clicked_prompt or user_input

    if question:
        st.session_state.qa_messages.append({"role": "user", "content": question})

        t0 = time.perf_counter()
        with st.spinner("Retrieving from Elasticsearch…"):
            hits, kibana_snippet, ret_timing = _retrieve(question, tenant_id, indices, use_context)
        retrieval_ms = (time.perf_counter() - t0) * 1000

        st.session_state.qa_last_hits           = hits
        st.session_state.qa_last_kibana_snippet = kibana_snippet

        t1 = time.perf_counter()
        rag_engine = st.session_state.get("qa_rag_engine", "Direct (Elastic)")
        if rag_engine == "LlamaIndex":
            with st.spinner("Generating answer with LlamaIndex + Claude…"):
                answer, gen_usage = llamaindex_rag_service.run_query(
                    question, hits, use_context, os.getenv("ANTHROPIC_API_KEY"),
                )
            gen_model_label = "llamaindex · claude-sonnet-4-6"
        else:
            with st.spinner("Generating answer with Claude…"):
                answer, gen_usage = _generate_answer(question, hits, use_context)
            gen_model_label = "claude-sonnet-4-6"
        gen_ms = (time.perf_counter() - t1) * 1000

        # ── Detailed breakdown ────────────────────────────────────────────────
        es_took_ms    = ret_timing["es_took_ms"]
        # network_ms = total retrieval round-trip minus what ES spent inside the cluster
        network_ms    = round(max(retrieval_ms - es_took_ms, 0), 1)
        input_tokens  = gen_usage.get("input_tokens", 0)
        output_tokens = gen_usage.get("output_tokens", 0)
        tokens_per_sec = round(output_tokens / (gen_ms / 1000), 1) if gen_ms > 0 and output_tokens else 0.0

        total_ms      = retrieval_ms + gen_ms
        avg_score     = round(sum(h["score"] for h in hits) / len(hits), 3) if hits else 0.0
        source        = "CSV" if ret_timing["is_csv_fallback"] else "ES"
        context_chars = sum(len(h.get("content", "")) for h in hits)
        wall_clock    = datetime.datetime.now().strftime("%H:%M:%S")
        query_num     = len(st.session_state.qa_latency_log) + 1

        metrics_entry = {
            "retrieval_ms":  round(retrieval_ms, 1),
            "es_took_ms":    es_took_ms,
            "network_ms":    network_ms,
            "gen_ms":        round(gen_ms, 1),
            "input_tokens":  input_tokens,
            "output_tokens": output_tokens,
            "tokens_per_sec": tokens_per_sec,
            "total_ms":      round(total_ms, 1),
            "hits":          len(hits),
            "avg_score":     avg_score,
            "source":        source,
            "wall_clock":    wall_clock,
            "query_num":     query_num,
        }
        st.session_state.qa_last_metrics = metrics_entry
        st.session_state.qa_latency_log.append(metrics_entry)

        # Gen-call details for the drilldown expander
        st.session_state.qa_last_gen_details = {
            "model":          gen_model_label,
            "max_tokens":     1024,
            "context_chars":  context_chars,
            "input_tokens":   input_tokens,
            "output_tokens":  output_tokens,
            "num_chunks":     len(hits),
            "question":       question,
            "gen_ms":         round(gen_ms, 1),
        }
        # Store ES|QL for retrieval drilldown
        st.session_state.qa_last_esql = _build_esql_snippet(
            question, tenant_id, indices, use_context
        )

        st.session_state.qa_messages.append({
            "role":    "assistant",
            "content": answer,
            "hits":    hits,
        })
        st.rerun()
