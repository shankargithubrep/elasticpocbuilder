"""
LlamaIndex RAG Service — orchestrates answer generation using LlamaIndex.

Uses pre-retrieved Elasticsearch hits as LlamaIndex nodes and routes them
through LlamaIndex's response synthesizer with Claude as the LLM backend.

Architecture:
  Elasticsearch retrieval (unchanged)  →  LlamaIndex nodes  →  Claude answer

This keeps Elastic as the retrieval layer and adds LlamaIndex as the
orchestration + prompt synthesis layer above it.
"""

import os
import logging

logger = logging.getLogger(__name__)


def is_available() -> bool:
    """Check whether LlamaIndex packages are installed."""
    try:
        import llama_index.core           # noqa: F401
        import llama_index.llms.anthropic  # noqa: F401
        return True
    except ImportError:
        return False


def _build_nodes(hits: list[dict]):
    """Convert Elasticsearch hit dicts into LlamaIndex NodeWithScore objects."""
    from llama_index.core.schema import NodeWithScore, TextNode

    nodes = []
    for h in hits:
        page_note = f", page {h['page']}" if h.get("page") else ""
        node = TextNode(
            text=h.get("content", ""),
            metadata={
                "title":    h.get("title", "—"),
                "id":       h.get("id", "—"),
                "locale":   h.get("locale", "—"),
                "domain":   h.get("domain", "—"),
                "index":    h.get("index", "—"),
                "page":     page_note,
                "score":    str(h.get("score", 0)),
            },
            id_=str(h.get("id", "")),
        )
        nodes.append(NodeWithScore(node=node, score=float(h.get("score", 0))))
    return nodes


def _qa_prompt_template():
    """QA prompt template that mirrors the Genesys KB context format."""
    from llama_index.core.prompts import PromptTemplate

    return PromptTemplate(
        "You are a helpful assistant for a Genesys Knowledge AI platform.\n"
        "Answer the question using ONLY the knowledge base chunks provided below.\n"
        "Always cite the source document ID and title in your answer.\n"
        "If the answer is not in the provided chunks, say clearly:\n"
        "'I could not find an answer for this tenant in the indexed knowledge base.'\n"
        "Be concise and professional. Format lists with dashes.\n\n"
        "Knowledge base chunks:\n\n"
        "{context_str}\n\n"
        "---\n\n"
        "Question: {query_str}\n\n"
        "Answer:"
    )


def run_query(
    question: str,
    hits: list[dict],
    use_context: bool,
    api_key: str | None = None,
) -> tuple[str, dict]:
    """
    Generate an answer via LlamaIndex + Claude using pre-retrieved ES hits.

    Parameters
    ----------
    question    : The user's question.
    hits        : Retrieved chunks from Elasticsearch (_retrieve() output).
    use_context : Whether contextual chunk mode is active.
    api_key     : Anthropic API key (falls back to ANTHROPIC_API_KEY env var).

    Returns
    -------
    (answer_text, usage_dict)
    usage_dict keys: input_tokens, output_tokens (if extractable), engine
    """
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")

    if not api_key:
        return (
            "_Anthropic API key not configured. Set `ANTHROPIC_API_KEY` in your .env._",
            {},
        )

    try:
        from llama_index.core.response_synthesizers import get_response_synthesizer
        from llama_index.llms.anthropic import Anthropic as AnthropicLLM
    except ImportError as e:
        return (
            f"_LlamaIndex packages not installed: {e}. "
            "Run: pip install llama-index-core llama-index-llms-anthropic_",
            {},
        )

    try:
        llm = AnthropicLLM(
            model="claude-sonnet-4-6",
            api_key=api_key,
            max_tokens=1024,
            system_prompt=(
                "You are a helpful assistant for a Genesys Knowledge AI platform. "
                "Retrieval mode: "
                + ("contextual (chunks include document metadata)" if use_context
                   else "standard (raw chunk text only)")
                + "."
            ),
        )

        synthesizer = get_response_synthesizer(
            llm=llm,
            response_mode="compact",       # merges all nodes into one prompt pass
            text_qa_template=_qa_prompt_template(),
            verbose=False,
        )

        nodes = _build_nodes(hits)

        if not nodes:
            return "No relevant chunks found to generate an answer.", {"engine": "llamaindex"}

        response = synthesizer.synthesize(question, nodes=nodes)
        answer   = str(response)

        # Attempt to extract token usage from LlamaIndex response metadata
        usage: dict = {"engine": "llamaindex"}
        try:
            meta = getattr(response, "metadata", None) or {}
            # LlamaIndex stores Anthropic usage under various keys depending on version
            for key in ("usage", "token_usage", "llm_output"):
                val = meta.get(key)
                if isinstance(val, dict):
                    usage["input_tokens"]  = val.get("input_tokens", 0)
                    usage["output_tokens"] = val.get("output_tokens", 0)
                    break
        except Exception:
            pass

        return answer, usage

    except Exception as e:
        logger.error(f"LlamaIndex run_query error: {e}")
        return f"_LlamaIndex error: {e}_", {}
