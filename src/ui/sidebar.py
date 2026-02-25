"""
Sidebar rendering for the Demo Builder app
"""

import streamlit as st

from src.framework import DemoModuleManager
from .context_display import display_context_summary
from .components.help_chat import render_chat_sidebar


def _render_status_section():
    """Render the collapsible Status section at top of sidebar."""
    from src.services.status_service import get_app_status

    # Get status (cached for session to avoid repeated calls)
    if "app_status" not in st.session_state:
        st.session_state.app_status = get_app_status()

    status = st.session_state.app_status

    # Status header with overall indicator and Vulcan branding
    status_emoji = "✅" if status.all_ok else "❌"
    status_label = f"🌋 Vulcan · Status {status_emoji}"

    with st.expander(status_label, expanded=False):
        st.caption("Vulcan helps create custom demo modules containing sample data, queries, and agentic tools.")
        st.divider()
        # LLM Config - compact single line
        llm_emoji = "✅" if status.llm.is_ok else "❌"
        st.markdown(f"{llm_emoji} **LLM:** {status.llm.detail}")

        # Elasticsearch - compact single line
        es_emoji = "✅" if status.elasticsearch.is_ok else "❌"
        st.markdown(f"{es_emoji} **ES:** {status.elasticsearch.detail}")

        # ES test buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Test", key="test_es_btn", use_container_width=True):
                from src.services.elasticsearch_indexer import ElasticsearchIndexer
                try:
                    indexer = ElasticsearchIndexer()
                    success, message = indexer.verify_connection()
                    if success:
                        st.success(f"✅ {message}")
                        del st.session_state.app_status
                    else:
                        st.error(f"❌ {message}")
                except Exception as e:
                    st.error(f"❌ {e}")

        with col2:
            if st.button("ELSER", key="test_elser_btn", use_container_width=True):
                from src.services.elasticsearch_indexer import ElasticsearchIndexer
                try:
                    indexer = ElasticsearchIndexer()
                    is_ready, message = indexer.check_elser_deployment()
                    if is_ready:
                        st.success(f"✅ {message}")
                    else:
                        st.warning(f"⚠️ {message}")
                except Exception as e:
                    st.error(f"❌ {e}")

        # AI Assistant - compact single line
        ai_emoji = "✅" if status.ai_assistant.is_ok else "❌"
        st.markdown(f"{ai_emoji} **AI:** {status.ai_assistant.detail}")
        st.caption("Toggle in Help panel")

        st.divider()

        # Inference Endpoints - compact
        st.markdown("**Inference Endpoints**")

        # Initialize inference endpoints in session state if not exists
        if "inference_endpoints" not in st.session_state:
            st.session_state.inference_endpoints = {
                "rerank": ".rerank-v1-elasticsearch",
                "completion": "completion-vulcan",
                "sparse_embedding": ".elser-2-elasticsearch",
                "dense_embedding": ".jina-embeddings-v5-text-small",
                "embedding_type": "sparse"
            }

        # RERANK endpoint input
        rerank_endpoint = st.text_input(
            "RERANK",
            value=st.session_state.inference_endpoints["rerank"],
            help="Inference endpoint ID for RERANK command",
            key="rerank_endpoint_input",
            label_visibility="collapsed",
            placeholder="RERANK endpoint"
        )
        st.session_state.inference_endpoints["rerank"] = rerank_endpoint

        # COMPLETION endpoint input
        completion_endpoint = st.text_input(
            "COMPLETION",
            value=st.session_state.inference_endpoints["completion"],
            help="Inference endpoint ID for COMPLETION command",
            key="completion_endpoint_input",
            label_visibility="collapsed",
            placeholder="COMPLETION endpoint"
        )
        st.session_state.inference_endpoints["completion"] = completion_endpoint

        st.divider()

        # Refresh status button
        if st.button("🔄 Refresh", use_container_width=True, key="refresh_status_btn"):
            if "app_status" in st.session_state:
                del st.session_state.app_status
            st.rerun()


def render_sidebar():
    """Render the sidebar with mode toggle and context display"""

    # Initialize inference endpoints early (needed by both status section and create mode)
    if "inference_endpoints" not in st.session_state:
        st.session_state.inference_endpoints = {
            "rerank": ".rerank-v1-elasticsearch",
            "completion": "completion-vulcan",
            "sparse_embedding": ".elser-2-elasticsearch",
            "dense_embedding": ".jina-embeddings-v5-text-small",
            "embedding_type": "sparse"
        }

    # Status section at top (collapsible) - includes Vulcan branding
    _render_status_section()

    # Initialize help toggle state
    if "help_chat_visible" not in st.session_state:
        st.session_state.help_chat_visible = False

    # Mode toggle buttons + Help toggle
    col1, col2, col3 = st.columns(3)

    with col1:
        create_selected = st.session_state.view_mode == "create"
        if st.button(
            "Create",
            use_container_width=True,
            type="primary" if create_selected else "secondary",
            key="create_mode_btn"
        ):
            st.session_state.view_mode = "create"
            st.rerun()

    with col2:
        browse_selected = st.session_state.view_mode == "browse"
        if st.button(
            "Browse",
            use_container_width=True,
            type="primary" if browse_selected else "secondary",
            key="browse_mode_btn"
        ):
            st.session_state.view_mode = "browse"
            st.rerun()

    with col3:
        # Help toggle button
        help_label = "Help ✓" if st.session_state.help_chat_visible else "Help"
        if st.button(
            help_label,
            use_container_width=True,
            type="primary" if st.session_state.help_chat_visible else "secondary",
            key="help_toggle_btn"
        ):
            st.session_state.help_chat_visible = not st.session_state.help_chat_visible
            st.rerun()

    # If help is visible, show chat at top of sidebar
    if st.session_state.help_chat_visible:
        st.markdown("---")
        render_chat_sidebar()
        st.markdown("---")

    # Always render mode-specific content below
    if st.session_state.view_mode == "create":
        st.markdown("---")

        # Initialize state
        # Dataset size is now auto-determined by demo type (search=smaller, analytics=larger)
        st.session_state.dataset_size_preference = "medium"
        # Always use enhanced generation (no toggle needed)
        st.session_state.use_enhanced_generation = True

        # Embedding type selector (always visible in create mode)
        st.markdown("**Embedding Type**")
        embedding_type = st.radio(
            "Embedding Type",
            options=["sparse", "dense"],
            index=0 if st.session_state.inference_endpoints.get("embedding_type", "sparse") == "sparse" else 1,
            help="Sparse (ELSER) for English keyword-aware search; Dense (Jina) for multilingual semantic search",
            key="embedding_type_radio",
            horizontal=True,
            label_visibility="collapsed"
        )
        st.session_state.inference_endpoints["embedding_type"] = embedding_type

        if embedding_type == "sparse":
            sparse_endpoint = st.text_input(
                "SPARSE EMBEDDING",
                value=st.session_state.inference_endpoints.get("sparse_embedding", ".elser-2-elasticsearch"),
                help="Inference endpoint ID for sparse embeddings (ELSER)",
                key="sparse_embedding_endpoint_input",
                label_visibility="collapsed",
                placeholder="SPARSE EMBEDDING endpoint"
            )
            st.session_state.inference_endpoints["sparse_embedding"] = sparse_endpoint
        else:
            dense_endpoint = st.text_input(
                "DENSE EMBEDDING",
                value=st.session_state.inference_endpoints.get("dense_embedding", ".jina-embeddings-v5-text-small"),
                help="Inference endpoint ID for dense embeddings (e.g. Jina v5)",
                key="dense_embedding_endpoint_input",
                label_visibility="collapsed",
                placeholder="DENSE EMBEDDING endpoint"
            )
            st.session_state.inference_endpoints["dense_embedding"] = dense_endpoint

        # LLM Model override (always visible in create mode)
        st.markdown("**LLM Model**")
        llm_model_input = st.text_input(
            "LLM Model",
            value=st.session_state.get("llm_model", "") or "",
            help="Override the default LLM model for demo generation. Leave empty to use the built-in default.",
            key="llm_model_input",
            label_visibility="collapsed",
            placeholder="e.g. claude-sonnet-4-6"
        )
        st.session_state.llm_model = llm_model_input if llm_model_input else None

        try:
            from src.services.llm_proxy_service import LLMProxyClient
            _client = LLMProxyClient()
            resolved = llm_model_input if llm_model_input else _client.get_model_name("default")
            st.caption(f"Active: `{resolved}`")
        except Exception:
            pass

        st.markdown("---")

        # Demo Context Section
        display_context_summary()

        st.markdown("---")

        if st.button("🔄 Start Fresh", use_container_width=True):
            st.session_state.messages = []
            st.session_state.demo_context = {
                "company_name": None,
                "department": None,
                "industry": None,
                "pain_points": [],
                "use_cases": [],
                "metrics": [],
            }
            st.session_state.conversation_phase = "initial"
            st.session_state.ai_expansion_used = False  # Re-enable complexity dropdown
            st.rerun()

        if st.button("📋 Use Test Prompt", use_container_width=True):
            test_prompt = """Salesforce's Customer Success team wants to prevent churn in their enterprise accounts. They manage 5,000+ accounts worth $10B in ARR but can only do quarterly business reviews. They need real-time health scores, usage analytics, and early warning signals. The CCO wants agents that can answer 'Which accounts are at risk this month and why?'"""
            st.session_state.messages.append({"role": "user", "content": test_prompt})
            st.session_state.needs_processing = True
            st.rerun()

        # Under the Hood button
        st.markdown("---")
        if st.button("🔧 Under the Hood", use_container_width=True, key="under_the_hood_btn"):
            st.session_state.show_under_the_hood = True
            st.rerun()

    else:  # Browse mode
        st.markdown("### 📚 Demo Modules")

        manager = DemoModuleManager()
        demos = manager.list_modules()

        if not demos:
            st.info("No demos yet. Switch to Create mode to make one!")
        else:
            # Show count
            st.caption(f"{len(demos)} modules")

            # List demos as clickable buttons
            for demo in demos:
                # Make button show selected state
                is_selected = st.session_state.current_demo_module == demo['name']
                button_type = "primary" if is_selected else "secondary"

                if st.button(
                    f"{demo.get('customer', 'Unknown')} - {demo.get('department', 'N/A')}",
                    key=f"select_{demo['name']}",
                    use_container_width=True,
                    type=button_type
                ):
                    # Only rerun if selection changed
                    if st.session_state.current_demo_module != demo['name']:
                        st.session_state.current_demo_module = demo['name']
                        st.rerun()
