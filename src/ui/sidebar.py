"""
Sidebar rendering for the Demo Builder app
"""

import streamlit as st
from pathlib import Path

from src.framework import DemoModuleManager
from .context_display import display_context_summary
from .components.help_chat import render_chat_sidebar

# Defaults for inference endpoints
_RERANK_DEFAULT = ".rerank-v1-elasticsearch"
_COMPLETION_DEFAULT = "completion-vulcan"


def _get_default_llm_model() -> str:
    """Get the default LLM model name, with fallback."""
    try:
        from src.services.llm_proxy_service import LLMProxyClient
        return LLMProxyClient().get_model_name("default")
    except Exception:
        return "claude-sonnet-4-6"


def _render_status_lines():
    """Render compact status lines directly in the sidebar (always visible)."""
    from src.services.status_service import get_app_status

    if "app_status" not in st.session_state:
        st.session_state.app_status = get_app_status()

    status = st.session_state.app_status

    llm_emoji = "✅" if status.llm.is_ok else "❌"
    es_emoji = "✅" if status.elasticsearch.is_ok else "❌"
    st.caption(f"{llm_emoji} LLM: {status.llm.detail}  \n{es_emoji} ES: {status.elasticsearch.detail}")


def _render_settings_expander():
    """Render the collapsible Settings expander."""
    from src.services.status_service import get_app_status

    if "app_status" not in st.session_state:
        st.session_state.app_status = get_app_status()

    status = st.session_state.app_status

    with st.expander("🌋 Vulcan · Settings", expanded=False):
        st.caption("Vulcan helps create custom demo modules containing sample data, queries, and agentic tools.")

        # ES test buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Test ES", key="test_es_btn", use_container_width=True):
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

        with col3:
            if st.button("Refresh", key="refresh_status_btn", use_container_width=True):
                if "app_status" in st.session_state:
                    del st.session_state.app_status
                st.rerun()

        ai_emoji = "✅" if status.ai_assistant.is_ok else "❌"
        st.caption(f"{ai_emoji} **AI Assistant:** {status.ai_assistant.detail} (toggle in Help panel)")

        st.divider()

        # --- Settings ---

        # Prompt Expansion toggle (default ON)
        # Initialize the widget key directly so Streamlit's keyed state defaults to True
        if "expansion_toggle" not in st.session_state:
            st.session_state.expansion_toggle = True

        expansion_enabled = st.checkbox(
            "Prompt expansion", key="expansion_toggle",
            help="When enabled, Vulcan uses an LLM to expand your brief prompt into a detailed "
                 "technical context before generating the demo. Produces higher-quality modules. "
                 "Disable for direct processing of already-detailed prompts."
        )
        st.session_state.ai_expansion_enabled = expansion_enabled

        # Embedding Type
        st.caption("**Embedding Type**")
        embedding_options = ["sparse", "dense", "custom"]
        current = st.session_state.inference_endpoints.get("embedding_type", "sparse")
        current_index = embedding_options.index(current) if current in embedding_options else 0

        embedding_type = st.radio(
            "Embedding Type",
            options=embedding_options,
            index=current_index,
            help="Sparse (ELSER) for English keyword-aware search; Dense (Jina) for multilingual semantic search; Custom for your own endpoint",
            key="embedding_type_radio",
            horizontal=True,
            label_visibility="collapsed"
        )
        st.session_state.inference_endpoints["embedding_type"] = embedding_type

        if embedding_type == "custom":
            custom_endpoint = st.text_input(
                "Custom embedding endpoint",
                value=st.session_state.inference_endpoints.get("custom_embedding", ""),
                help="Your custom inference endpoint ID. You must also select the vector type below.",
                key="custom_embedding_endpoint_input",
                label_visibility="collapsed",
                placeholder="my-custom-embedding-endpoint"
            )
            st.session_state.inference_endpoints["custom_embedding"] = custom_endpoint

            custom_vector_type = st.radio(
                "Vector type",
                options=["sparse", "dense"],
                index=0,
                help="Does your custom endpoint produce sparse or dense vectors?",
                key="custom_vector_type_radio",
                horizontal=True,
                label_visibility="collapsed"
            )
            st.session_state.inference_endpoints["custom_vector_type"] = custom_vector_type

        # Custom LLM Model
        default_model = _get_default_llm_model()
        custom_model = st.checkbox(
            "Custom LLM model", key="custom_model_checkbox",
            help="Override the default LLM model used for demo generation"
        )
        if custom_model:
            llm_model_input = st.text_input(
                "LLM Model",
                value=st.session_state.get("llm_model", "") or "",
                key="llm_model_input",
                label_visibility="collapsed",
                placeholder=f"e.g. {default_model}"
            )
            st.session_state.llm_model = llm_model_input if llm_model_input else None
        else:
            st.session_state.llm_model = None

        # Custom Rerank Endpoint
        custom_rerank = st.checkbox(
            "Custom rerank endpoint", key="custom_rerank_checkbox",
            help="Re-ranks search results by semantic relevance. Used by the ES|QL RERANK command."
        )
        if custom_rerank:
            rerank_input = st.text_input(
                "Rerank Endpoint",
                value=st.session_state.inference_endpoints.get("rerank", _RERANK_DEFAULT),
                key="rerank_endpoint_input",
                label_visibility="collapsed",
                placeholder=f"e.g. {_RERANK_DEFAULT}"
            )
            st.session_state.inference_endpoints["rerank"] = rerank_input if rerank_input else _RERANK_DEFAULT
        else:
            st.session_state.inference_endpoints["rerank"] = _RERANK_DEFAULT

        # Custom Completion Endpoint
        custom_completion = st.checkbox(
            "Custom completion endpoint", key="custom_completion_checkbox",
            help="Generates natural-language answers from search results (RAG). Used by the ES|QL COMPLETION command."
        )
        if custom_completion:
            completion_input = st.text_input(
                "Completion Endpoint",
                value=st.session_state.inference_endpoints.get("completion", _COMPLETION_DEFAULT),
                key="completion_endpoint_input",
                label_visibility="collapsed",
                placeholder=f"e.g. {_COMPLETION_DEFAULT}"
            )
            st.session_state.inference_endpoints["completion"] = completion_input if completion_input else _COMPLETION_DEFAULT
        else:
            st.session_state.inference_endpoints["completion"] = _COMPLETION_DEFAULT

        st.divider()

        # API Credentials override
        st.markdown("**API Credentials**")
        st.caption("Configured in your `.env` file. Override below for this session only.  \n"
                   "[Generate a temporary LLM Proxy key](https://sa-workshops.prod-3.eden.elastic.dev/LLM_Key_Generator)")

        import os
        override_creds = st.checkbox(
            "Override credentials",
            key="override_creds_checkbox",
            help="Temporarily override .env credentials for this session"
        )
        if override_creds:
            proxy_url = st.text_input(
                "LLM Proxy URL",
                value=st.session_state.get("llm_proxy_url_override", "") or "",
                key="llm_proxy_url_input",
                label_visibility="collapsed",
                placeholder="LLM Proxy URL"
            )
            proxy_key = st.text_input(
                "LLM Proxy API Key",
                value=st.session_state.get("llm_proxy_key_override", "") or "",
                key="llm_proxy_key_input",
                label_visibility="collapsed",
                placeholder="LLM Proxy API Key",
                type="password"
            )
            if proxy_url:
                os.environ["LLM_PROXY_URL"] = proxy_url
                st.session_state.llm_proxy_url_override = proxy_url
            if proxy_key:
                os.environ["LLM_PROXY_API_KEY"] = proxy_key
                st.session_state.llm_proxy_key_override = proxy_key

            es_url = st.text_input(
                "Elasticsearch URL",
                value=st.session_state.get("es_url_override", "") or "",
                key="es_url_input",
                label_visibility="collapsed",
                placeholder="Elasticsearch URL"
            )
            es_key = st.text_input(
                "Elasticsearch API Key",
                value=st.session_state.get("es_key_override", "") or "",
                key="es_key_input",
                label_visibility="collapsed",
                placeholder="Elasticsearch API Key",
                type="password"
            )
            if es_url:
                os.environ["ELASTICSEARCH_URL"] = es_url
                st.session_state.es_url_override = es_url
            if es_key:
                os.environ["ELASTICSEARCH_API_KEY"] = es_key
                st.session_state.es_key_override = es_key

            st.caption("Overrides apply to this session only and are not saved to disk.")


def render_sidebar():
    """Render the sidebar with mode toggle and context display"""

    # Initialize inference endpoints early (needed by both settings and create mode)
    if "inference_endpoints" not in st.session_state:
        st.session_state.inference_endpoints = {
            "rerank": _RERANK_DEFAULT,
            "completion": _COMPLETION_DEFAULT,
            "embedding_type": "sparse"
        }

    # Settings expander (collapsible)
    _render_settings_expander()

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

    # Status lines (always visible, below mode buttons)
    _render_status_lines()

    # Compact active-settings display (always visible)
    EMBEDDING_DEFAULTS = {
        "sparse": ".elser-2-elasticsearch",
        "dense": ".jina-embeddings-v5-text-small",
    }
    active_embedding_type = st.session_state.inference_endpoints.get("embedding_type", "sparse")
    if active_embedding_type == "custom":
        active_embedding = st.session_state.inference_endpoints.get("custom_embedding", "custom")
    else:
        active_embedding = EMBEDDING_DEFAULTS.get(active_embedding_type, active_embedding_type)
    active_model = st.session_state.get("llm_model") or _get_default_llm_model()
    active_rerank = st.session_state.inference_endpoints.get("rerank", _RERANK_DEFAULT)
    active_completion = st.session_state.inference_endpoints.get("completion", _COMPLETION_DEFAULT)

    active_expansion = "Enabled" if st.session_state.get("ai_expansion_enabled", True) else "Disabled"
    st.caption(
        f"**Expansion:** `{active_expansion}`",
        help="Prompt expansion uses an LLM to enrich your brief prompt into a detailed technical context before generation. Change in Settings above."
    )
    st.caption(
        f"**Embedding:** `{active_embedding}`",
        help="Vector embedding model for semantic search. Change in Settings above."
    )
    st.caption(
        f"**LLM Model:** `{active_model}`",
        help="The LLM used for generating demo modules. Override in Settings above."
    )
    st.caption(
        f"**Rerank:** `{active_rerank}`",
        help="ES|QL RERANK re-ranks search results by semantic relevance. Override in Settings above."
    )
    st.caption(
        f"**Completion:** `{active_completion}`",
        help="ES|QL COMPLETION generates natural-language answers from search results (RAG). Override in Settings above."
    )

    # Always render mode-specific content below
    if st.session_state.view_mode == "create":

        # Initialize state
        # TODO: Expose size control in sidebar UI (see GitHub issue).
        # Analytics defaults to "large" for realistic distributions (5K-20K rows/dataset).
        # Search path ignores this setting — hardcoded at 500-1000 docs in search_strategy_generator.py.
        st.session_state.dataset_size_preference = "large"
        st.session_state.use_enhanced_generation = True

        # Demo Context Section
        display_context_summary()

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
            st.session_state.ai_expansion_used = False  # Re-enable expansion
            st.rerun()

        # About Vulcan button
        if st.button("💡 About Vulcan", use_container_width=True, key="under_the_hood_btn"):
            st.session_state.show_under_the_hood = True
            st.rerun()

    else:  # Browse mode
        st.markdown("### 📚 Demo Modules")

        manager = DemoModuleManager()
        demos = manager.list_modules()

        # CSS for cards
        st.markdown(
            """<style>
            div[data-testid="stVerticalBlock"] .selected-demo-card {
                border-left: 3px solid #4A90D9 !important;
                background-color: rgba(74, 144, 217, 0.08);
                border-radius: 0.5rem;
                padding: 0.25rem 0.5rem;
                margin-bottom: 0.25rem;
            }
            /* Fixed-width sidebar cards */
            [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
                min-width: 0;
                overflow: hidden;
            }
            </style>""",
            unsafe_allow_html=True,
        )

        # Import button + hidden file input
        if st.button("📂 Import Module", key="import_module_btn", use_container_width=True):
            st.session_state.show_import_uploader = True
            st.rerun()

        if st.session_state.get("show_import_uploader"):
            uploaded = st.file_uploader(
                "Select a .zip module", type=["zip"], key="import_module_zip",
                label_visibility="collapsed"
            )
            if uploaded is not None:
                import io, zipfile
                with zipfile.ZipFile(io.BytesIO(uploaded.read())) as zf:
                    top_dirs = {name.split("/")[0] for name in zf.namelist() if "/" in name}
                    if top_dirs:
                        dest = Path("demos")
                        dest.mkdir(exist_ok=True)
                        zf.extractall(dest)
                        st.session_state.show_import_uploader = False
                        st.success(f"Imported: {', '.join(top_dirs)}")
                        st.rerun()
                    else:
                        st.error("Zip must contain a module folder.")

        if not demos:
            st.info("No demos yet. Switch to Create mode to make one!")
        else:
            st.caption(f"{len(demos)} modules")

            # List demos as card containers
            for demo in demos:
                is_selected = st.session_state.current_demo_module == demo['name']

                # Format date from ISO string
                date_label = ""
                raw_date = demo.get('created_at', '')
                if raw_date:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(raw_date)
                        date_label = dt.strftime("%b %d, %Y")
                    except (ValueError, TypeError):
                        date_label = raw_date[:10] if len(raw_date) >= 10 else raw_date

                # Type emoji + label
                demo_type = demo.get('demo_type', 'analytics')
                type_label = "🔍 Search" if demo_type == "search" else "📊 Analytics"

                with st.container(border=True):
                    # Highlight selected card
                    if is_selected:
                        st.markdown(
                            '<div class="selected-demo-card"></div>',
                            unsafe_allow_html=True,
                        )

                    if st.button(
                        f"{demo.get('customer', 'Unknown')} - {demo.get('department', 'N/A')}",
                        key=f"select_{demo['name']}",
                        use_container_width=True,
                        type="primary" if is_selected else "secondary"
                    ):
                        if st.session_state.current_demo_module != demo['name']:
                            st.session_state.current_demo_module = demo['name']
                            st.rerun()

                    # Metadata line + actions popover
                    meta_parts = [type_label]
                    if date_label:
                        meta_parts.append(date_label)
                    meta_text = " · ".join(meta_parts)

                    meta_col, menu_col = st.columns([6, 1])
                    with meta_col:
                        st.caption(meta_text)
                    with menu_col:
                        with st.popover("⋯"):
                            import io, zipfile
                            zip_buf = io.BytesIO()
                            module_path = Path(demo['path'])
                            with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                                for f in module_path.iterdir():
                                    if f.is_file():
                                        zf.write(f, f"{module_path.name}/{f.name}")
                            zip_buf.seek(0)
                            st.download_button(
                                "📥 Download", zip_buf,
                                file_name=f"{demo['name']}.zip",
                                mime="application/zip",
                                key=f"download_{demo['name']}",
                                use_container_width=True
                            )
                            if st.button("🗑️ Delete", key=f"delete_{demo['name']}", use_container_width=True):
                                st.session_state.confirm_delete = demo['name']
                                st.rerun()

                    # Confirmation row
                    if st.session_state.get("confirm_delete") == demo['name']:
                        st.warning(f"Delete **{demo.get('customer', 'Unknown')}**?", icon="⚠️")
                        yes_col, no_col = st.columns(2)
                        with yes_col:
                            if st.button("Yes, delete", key=f"confirm_yes_{demo['name']}", type="primary", use_container_width=True):
                                manager.delete_module(demo['name'])
                                if st.session_state.current_demo_module == demo['name']:
                                    st.session_state.current_demo_module = None
                                st.session_state.confirm_delete = None
                                st.rerun()
                        with no_col:
                            if st.button("Cancel", key=f"confirm_no_{demo['name']}", use_container_width=True):
                                st.session_state.confirm_delete = None
                                st.rerun()
