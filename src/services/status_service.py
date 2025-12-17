"""
Status Service - Provides connection status for all app components.

Checks:
- LLM Configuration (Proxy, Anthropic, OpenAI)
- Elasticsearch Environment
- AI Assistant (doc index)
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ComponentStatus:
    """Status of a single component."""
    is_ok: bool
    label: str
    detail: str


@dataclass
class AppStatus:
    """Overall app status."""
    all_ok: bool
    llm: ComponentStatus
    elasticsearch: ComponentStatus
    ai_assistant: ComponentStatus


def get_llm_status() -> ComponentStatus:
    """
    Check LLM configuration status.

    Returns:
        ComponentStatus with provider info
    """
    try:
        # Check for LLM Proxy first
        if os.getenv("LLM_PROXY_URL") and os.getenv("LLM_PROXY_API_KEY"):
            # Try to get model info from proxy
            from src.services.llm_proxy_service import LLMProxyClient
            client = LLMProxyClient(provider="proxy")
            if client.is_available():
                model = client.get_model_name("default")
                # Extract model name for display
                model_short = model.split("/")[-1] if "/" in model else model
                return ComponentStatus(
                    is_ok=True,
                    label="LLM Config",
                    detail=f"Proxy - {model_short}"
                )

        # Check for direct Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            return ComponentStatus(
                is_ok=True,
                label="LLM Config",
                detail="Direct - Anthropic"
            )

        # Check for direct OpenAI
        if os.getenv("OPENAI_API_KEY"):
            return ComponentStatus(
                is_ok=True,
                label="LLM Config",
                detail="Direct - OpenAI"
            )

        # No LLM configured
        return ComponentStatus(
            is_ok=False,
            label="LLM Config",
            detail="Not configured"
        )

    except Exception as e:
        logger.warning(f"Error checking LLM status: {e}")
        return ComponentStatus(
            is_ok=False,
            label="LLM Config",
            detail=f"Error: {str(e)[:30]}"
        )


def get_elasticsearch_status() -> ComponentStatus:
    """
    Check Elasticsearch connection status.

    Returns:
        ComponentStatus with connection info
    """
    try:
        from src.services.elasticsearch_indexer import ElasticsearchIndexer

        # Check if credentials are configured
        cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID") or os.getenv("ELASTIC_CLOUD_ID")
        api_key = os.getenv("ELASTICSEARCH_API_KEY") or os.getenv("ELASTIC_API_KEY")

        if not cloud_id or not api_key:
            return ComponentStatus(
                is_ok=False,
                label="Elasticsearch",
                detail="Not configured in .env"
            )

        # Try to connect
        indexer = ElasticsearchIndexer()
        success, message = indexer.verify_connection()

        if success:
            # Extract cluster info from message if available
            return ComponentStatus(
                is_ok=True,
                label="Elasticsearch",
                detail="Connected"
            )
        else:
            return ComponentStatus(
                is_ok=False,
                label="Elasticsearch",
                detail=message[:30] if message else "Connection failed"
            )

    except Exception as e:
        logger.warning(f"Error checking ES status: {e}")
        return ComponentStatus(
            is_ok=False,
            label="Elasticsearch",
            detail=f"Error: {str(e)[:25]}"
        )


def get_ai_assistant_status() -> ComponentStatus:
    """
    Check AI Assistant status (doc index existence).

    Returns:
        ComponentStatus with index info
    """
    try:
        from src.services.doc_indexer_service import get_doc_indexer

        doc_indexer = get_doc_indexer()

        if not doc_indexer.is_available():
            return ComponentStatus(
                is_ok=False,
                label="AI Assistant",
                detail="Requires ES connection"
            )

        if doc_indexer.check_index_exists():
            stats = doc_indexer.get_index_stats()
            count = stats.get('count', 0)
            return ComponentStatus(
                is_ok=True,
                label="AI Assistant",
                detail=f"Enabled ({count} docs)"
            )
        else:
            return ComponentStatus(
                is_ok=False,
                label="AI Assistant",
                detail="Not enabled"
            )

    except Exception as e:
        logger.warning(f"Error checking AI status: {e}")
        return ComponentStatus(
            is_ok=False,
            label="AI Assistant",
            detail=f"Error: {str(e)[:25]}"
        )


def get_app_status() -> AppStatus:
    """
    Get overall app status including all components.

    Returns:
        AppStatus with all component statuses
    """
    llm = get_llm_status()
    es = get_elasticsearch_status()
    ai = get_ai_assistant_status()

    # All OK if LLM and ES are working (AI Assistant is optional)
    all_ok = llm.is_ok and es.is_ok

    return AppStatus(
        all_ok=all_ok,
        llm=llm,
        elasticsearch=es,
        ai_assistant=ai
    )


def get_elser_status() -> Tuple[bool, str]:
    """
    Check ELSER deployment status.

    Returns:
        Tuple of (is_ready, message)
    """
    try:
        from src.services.elasticsearch_indexer import ElasticsearchIndexer
        indexer = ElasticsearchIndexer()
        return indexer.check_elser_deployment()
    except Exception as e:
        return False, f"Error: {str(e)}"
