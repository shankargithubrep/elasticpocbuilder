"""
Sidebar rendering for the Demo Builder app
"""

import streamlit as st

from src.framework import DemoModuleManager
from .context_display import display_context_summary


def render_sidebar():
    """Render the sidebar with mode toggle and context display"""

    # Vulcan header
    st.markdown("### Vulcan")

    # Prominent mode toggle buttons with custom styling
    col1, col2 = st.columns(2)

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

    if st.session_state.view_mode == "create":
        display_context_summary()

        # Dataset size preference (only in create mode)
        st.markdown("---")
        st.markdown("#### Dataset Size")

        # Initialize dataset_size_preference if not exists
        if "dataset_size_preference" not in st.session_state:
            st.session_state.dataset_size_preference = "small"

        # Slider with options
        size_options = ["small", "medium", "large"]
        size_index = size_options.index(st.session_state.dataset_size_preference)

        selected_index = st.select_slider(
            "Size",
            options=range(len(size_options)),
            value=size_index,
            format_func=lambda x: size_options[x].capitalize(),
            key="dataset_size_slider",
            label_visibility="collapsed"
        )

        st.session_state.dataset_size_preference = size_options[selected_index]

        # Display legend based on selection
        size_legends = {
            "small": "**Small:** < 5,000 records per dataset",
            "medium": "**Medium:** 5,000-15,000 records per dataset",
            "large": "**Large:** 15,000-50,000 records per dataset"
        }

        st.caption(size_legends[st.session_state.dataset_size_preference])

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
                "scale": None,
            }
            st.session_state.conversation_phase = "initial"
            st.rerun()

        if st.button("📋 Use Test Prompt", use_container_width=True):
            test_prompt = """Salesforce's Customer Success team wants to prevent churn in their enterprise accounts. They manage 5,000+ accounts worth $10B in ARR but can only do quarterly business reviews. They need real-time health scores, usage analytics, and early warning signals. The CCO wants agents that can answer 'Which accounts are at risk this month and why?'"""
            st.session_state.messages.append({"role": "user", "content": test_prompt})
            st.session_state.needs_processing = True
            st.rerun()

        st.markdown("---")
        st.markdown("### 🔗 Elasticsearch")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Test Connection", use_container_width=True):
                from src.services.elasticsearch_indexer import ElasticsearchIndexer
                try:
                    indexer = ElasticsearchIndexer()
                    success, message = indexer.verify_connection()

                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
                except Exception as e:
                    st.error(f"❌ Connection failed: {e}")

        with col2:
            if st.button("Check ELSER", use_container_width=True):
                from src.services.elasticsearch_indexer import ElasticsearchIndexer
                try:
                    indexer = ElasticsearchIndexer()
                    is_ready, message = indexer.check_elser_deployment()

                    if is_ready:
                        st.success(f"✅ {message}")
                    else:
                        st.warning(f"⚠️ {message}")

                        # Offer to deploy
                        if "not deployed" in message.lower():
                            if st.button("Deploy ELSER", use_container_width=True):
                                with st.spinner("Deploying ELSER..."):
                                    deploy_success, deploy_msg = indexer.deploy_elser()
                                    if deploy_success:
                                        st.success(f"✅ {deploy_msg}")
                                    else:
                                        st.error(f"❌ {deploy_msg}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

        # Inference Endpoints Configuration
        st.markdown("---")
        st.markdown("### ⚙️ Inference Endpoints")

        # Initialize inference endpoints in session state if not exists
        if "inference_endpoints" not in st.session_state:
            st.session_state.inference_endpoints = {
                "rerank": ".rerank-v1-elasticsearch",
                "completion": "completion-vulcan"
            }

        # RERANK endpoint input
        rerank_endpoint = st.text_input(
            "RERANK Endpoint",
            value=st.session_state.inference_endpoints["rerank"],
            help="Inference endpoint ID for RERANK command (default: .rerank-v1-elasticsearch)",
            key="rerank_endpoint_input"
        )
        st.session_state.inference_endpoints["rerank"] = rerank_endpoint

        # COMPLETION endpoint input
        completion_endpoint = st.text_input(
            "COMPLETION Endpoint",
            value=st.session_state.inference_endpoints["completion"],
            help="Inference endpoint ID for COMPLETION command (default: completion-vulcan)",
            key="completion_endpoint_input"
        )
        st.session_state.inference_endpoints["completion"] = completion_endpoint

        # Show current values
        st.caption(f"🔄 RERANK: `{st.session_state.inference_endpoints['rerank']}`")
        st.caption(f"🤖 COMPLETION: `{st.session_state.inference_endpoints['completion']}`")

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
