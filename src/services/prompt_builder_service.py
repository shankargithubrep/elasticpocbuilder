"""
Prompt Builder Service — generates and refines Create Demo prompts
for Elastic Search use cases using LLM assistance.

Users fill in a guided form; this service converts their inputs into a
well-structured, detailed prompt ready to paste into the Create Demo flow.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Starter templates ──────────────────────────────────────────────────────────

TEMPLATES = {
    "— Start from scratch —": None,
    "🏦 Financial Services · Customer Service KB": {
        "industry":       "Financial Services",
        "department":     "Customer Service",
        "persona":        "Call center agents answering customer queries",
        "data_sources":   ["Salesforce KB", "SharePoint", "PDF Documents"],
        "content_types":  ["FAQs", "SOPs / Procedures", "Policies"],
        "doc_count":      "1K – 10K",
        "languages":      "Multilingual (European)",
        "search_type":    "Hybrid (BM25 + Semantic)",
        "features":       ["Multilingual", "RAG / Q&A answers", "Multi-tenant"],
        "latency":        "< 100ms",
        "pain_point":     "Agents spend too long searching multiple systems for answers during live calls",
        "success_metric": "Reduce average handle time by 30%, improve first-call resolution",
        "compliance":     ["GDPR"],
    },
    "🏥 Healthcare · Clinical Knowledge Search": {
        "industry":       "Healthcare",
        "department":     "Clinical Operations",
        "persona":        "Clinicians and care coordinators looking up protocols",
        "data_sources":   ["SharePoint", "PDF Documents", "Confluence"],
        "content_types":  ["SOPs / Procedures", "Policies", "Technical Manuals"],
        "doc_count":      "1K – 10K",
        "languages":      "English only",
        "search_type":    "Hybrid (BM25 + Semantic)",
        "features":       ["Re-ranking", "RAG / Q&A answers", "Filters / Facets"],
        "latency":        "< 500ms",
        "pain_point":     "Clinicians cannot quickly locate the right protocol version during patient care",
        "success_metric": "90% of queries answered within 3 seconds with correct protocol version",
        "compliance":     ["HIPAA"],
    },
    "🛒 Retail · Product & Catalogue Search": {
        "industry":       "Retail / E-commerce",
        "department":     "Digital Commerce",
        "persona":        "Customers searching for products on the website",
        "data_sources":   ["Custom / Internal", "PDF Documents"],
        "content_types":  ["Product Docs", "FAQs"],
        "doc_count":      "10K – 100K",
        "languages":      "Multilingual (Global)",
        "search_type":    "Hybrid (BM25 + Semantic)",
        "features":       ["Multilingual", "Re-ranking", "Filters / Facets"],
        "latency":        "< 100ms",
        "pain_point":     "Low search relevance causes customers to abandon without finding products",
        "success_metric": "Increase search-to-purchase conversion rate by 20%",
        "compliance":     [],
    },
    "⚖️ Legal · Contract & Policy Retrieval": {
        "industry":       "Legal / Professional Services",
        "department":     "Legal",
        "persona":        "Lawyers and paralegals searching contract clauses and precedents",
        "data_sources":   ["PDF Documents", "SharePoint"],
        "content_types":  ["Contracts / Legal", "Policies"],
        "doc_count":      "1K – 10K",
        "languages":      "English only",
        "search_type":    "Semantic",
        "features":       ["Re-ranking", "RAG / Q&A answers", "Filters / Facets"],
        "latency":        "< 500ms",
        "pain_point":     "Manual contract review takes days; teams cannot find relevant precedent clauses quickly",
        "success_metric": "Reduce contract review time by 50%, surface relevant clauses in under 10 seconds",
        "compliance":     ["GDPR", "SOC 2"],
    },
    "📞 Telecom · Agent Assist & Troubleshooting": {
        "industry":       "Telecommunications",
        "department":     "Customer Service",
        "persona":        "Support agents handling technical troubleshooting calls",
        "data_sources":   ["Salesforce KB", "ServiceNow", "PDF Documents"],
        "content_types":  ["FAQs", "SOPs / Procedures", "Technical Manuals"],
        "doc_count":      "1K – 10K",
        "languages":      "Multilingual (Global)",
        "search_type":    "Hybrid (BM25 + Semantic)",
        "features":       ["Multilingual", "RAG / Q&A answers", "Multi-tenant", "Re-ranking"],
        "latency":        "< 100ms",
        "pain_point":     "Agents cannot resolve complex technical issues quickly, leading to escalations and repeat calls",
        "success_metric": "Reduce escalation rate by 25%, cut average handle time to under 4 minutes",
        "compliance":     [],
    },
}

# ── Form option lists ──────────────────────────────────────────────────────────

INDUSTRIES = [
    "Financial Services", "Healthcare", "Retail / E-commerce",
    "Telecommunications", "Manufacturing", "Government / Public Sector",
    "Legal / Professional Services", "Technology / SaaS", "Insurance",
    "Energy & Utilities", "Education", "Other",
]

DEPARTMENTS = [
    "Customer Service", "IT / Technology", "Legal", "HR / People",
    "Sales", "Marketing", "Operations", "Clinical Operations",
    "Digital Commerce", "Compliance", "Finance", "Other",
]

DATA_SOURCES = [
    "Salesforce KB", "ServiceNow", "SharePoint", "Confluence",
    "PDF Documents", "Web / Intranet", "Custom / Internal",
]

CONTENT_TYPES = [
    "FAQs", "SOPs / Procedures", "Policies", "Contracts / Legal",
    "Product Docs", "Technical Manuals", "Training Materials",
]

DOC_COUNTS = ["< 1K", "1K – 10K", "10K – 100K", "100K+"]

LANGUAGE_OPTIONS = [
    "English only",
    "Multilingual (European)",
    "Multilingual (Global)",
]

SEARCH_TYPES = [
    "Hybrid (BM25 + Semantic)",
    "Semantic only",
    "BM25 / Keyword only",
]

FEATURES = [
    "Multilingual",
    "Re-ranking",
    "RAG / Q&A answers",
    "Filters / Facets",
    "Multi-tenant",
    "Personalisation",
]

LATENCY_OPTIONS = ["< 100ms", "< 500ms", "< 1s", "Best effort"]

COMPLIANCE_OPTIONS = ["GDPR", "HIPAA", "SOC 2", "PCI-DSS", "FedRAMP", "None / Other"]


# ── LLM calls ─────────────────────────────────────────────────────────────────

def _get_llm_client():
    """Return an Anthropic client using available credentials."""
    try:
        import os
        from anthropic import Anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            return None
        return Anthropic(api_key=api_key)
    except Exception:
        return None


def generate_prompt(inputs: dict[str, Any]) -> tuple[str, str]:
    """
    Generate a detailed Create Demo prompt from guided form inputs.

    Parameters
    ----------
    inputs : dict with keys matching the form fields

    Returns
    -------
    (prompt_text, error_message)  — error_message is empty string on success.
    """
    client = _get_llm_client()
    if not client:
        return "", "Anthropic API key not configured. Set ANTHROPIC_API_KEY in your .env file."

    features_str    = ", ".join(inputs.get("features", [])) or "standard search"
    sources_str     = ", ".join(inputs.get("data_sources", [])) or "internal documents"
    content_str     = ", ".join(inputs.get("content_types", [])) or "mixed documents"
    compliance_str  = ", ".join(inputs.get("compliance", [])) or "no specific compliance requirements"

    system = """\
You are a senior Elastic Solutions Architect writing a technical demo brief for the Elastic Demo Builder.

The output will be pasted directly into the Demo Builder and must give the generator everything it needs to \
produce realistic data, specific ES|QL queries, and a credible demo narrative for an engineering audience.

Follow this exact structure. Use markdown headings. Be specific and technical — avoid marketing language.

## Output structure

### Core message
One or two sentences that anchor the entire demo to a single business outcome.

### Primary audience
Who will watch this demo and what they care about technically.

### Architecture framing
A short Before/After that shows what changes (retrieval layer, search tier, data pipeline, etc.) \
and what stays the same. Keep it honest and low-disruption.

### Demo scenarios (exactly 3)
For each scenario:
- **Scenario N: [Title]** — what it proves and why it matters
- **Story**: the specific business situation being illustrated
- **What to build**: datasets, document types, metadata fields, realistic content
- **Live interaction**: exact example queries or actions the presenter runs
- **What the UI should show**: result cards, filters, metadata visible, highlight behaviour
- **Talk track note**: one sentence the presenter says to frame this scenario

### Data model
Key metadata fields the indexed documents must carry (realistic field names, not generic).

### Success criteria
3 bullet points. The demo is successful if the audience concludes X, Y, Z.

### Technical preferences
Search approach, features to use (hybrid, reranking, RAG, facets, multi-tenant, etc.), \
latency target, compliance considerations.

Do NOT include a generic intro paragraph. Start immediately with ## Core message."""

    user = f"""\
Generate a structured technical demo brief for the Elastic Demo Builder using the context below.

Industry: {inputs.get('industry', 'Technology')}
Department: {inputs.get('department', 'IT')}
User persona: {inputs.get('persona', 'employees')}

Data sources: {sources_str}
Content types: {content_str}
Document volume: {inputs.get('doc_count', '1K–10K')} documents
Languages: {inputs.get('languages', 'English only')}

Search approach: {inputs.get('search_type', 'Hybrid (BM25 + Semantic)')}
Key features required: {features_str}
Latency target: {inputs.get('latency', '< 500ms')}

Primary pain point: {inputs.get('pain_point', '')}
Success metric: {inputs.get('success_metric', '')}
Compliance requirements: {compliance_str}

Produce the full structured brief. Make every scenario concrete — include specific example queries \
the presenter will run live, realistic document types, and exact metadata fields. \
Write for an engineering audience, not a marketing audience."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text.strip(), ""
    except Exception as e:
        logger.error(f"Prompt generation error: {e}")
        return "", f"Generation failed: {e}"


def refine_prompt(existing_prompt: str, refinement_instruction: str) -> tuple[str, str]:
    """
    Refine an existing prompt with additional instructions.

    Parameters
    ----------
    existing_prompt          : The current generated prompt text.
    refinement_instruction   : User's instruction e.g. "make it more technical".

    Returns
    -------
    (refined_prompt_text, error_message)
    """
    client = _get_llm_client()
    if not client:
        return "", "Anthropic API key not configured."

    system = (
        "You are an Elastic Solutions Architect refining a demo brief. "
        "Apply the user's instruction to improve the existing prompt. "
        "Preserve all the core context — only change what the instruction asks for. "
        "Output only the refined prompt text, no preamble, no explanation."
    )

    user = f"""Existing prompt:
{existing_prompt}

Refinement instruction: {refinement_instruction}

Output the refined prompt:"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text.strip(), ""
    except Exception as e:
        logger.error(f"Prompt refinement error: {e}")
        return "", f"Refinement failed: {e}"
