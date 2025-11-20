"""
Sidebar rendering for the Demo Builder app
"""

import streamlit as st

from src.framework import DemoModuleManager
from .context_display import display_context_summary


def render_sidebar():
    """Render the sidebar with mode toggle and context display"""

    # Vulcan header with tooltip
    st.markdown("### Vulcan", help="Vulcan helps create custom demo modules containing sample data, queries, and agentic tools.")

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
        st.markdown("---")
        st.markdown("#### Generation Options")

        # Initialize dataset_size_preference if not exists
        if "dataset_size_preference" not in st.session_state:
            st.session_state.dataset_size_preference = "medium"  # Default to medium (best for enhanced mode)

        # Dataset Size Slider
        size_options = ["small", "medium", "large"]
        size_index = size_options.index(st.session_state.dataset_size_preference)

        selected_index = st.select_slider(
            "Dataset Size",
            options=range(len(size_options)),
            value=size_index,
            format_func=lambda x: size_options[x].capitalize(),
            key="dataset_size_slider"
        )

        st.session_state.dataset_size_preference = size_options[selected_index]

        # Display legend based on selection
        size_legends = {
            "small": "**Small:** < 5,000 records per dataset",
            "medium": "**Medium:** 5,000-15,000 records per dataset",
            "large": "**Large:** 15,000-50,000 records per dataset"
        }

        st.caption(size_legends[st.session_state.dataset_size_preference])

        # Initialize use_enhanced_generation if not exists
        if "use_enhanced_generation" not in st.session_state:
            st.session_state.use_enhanced_generation = False

        # Data Generation Mode Radio
        generation_mode = st.radio(
            "Data Generation Mode",
            options=["Standard", "Advanced"],
            index=1 if st.session_state.use_enhanced_generation else 0,
            key="generation_mode_radio",
            help="Advanced mode uses realistic clustering and percentile-based query thresholds. Experimental feature - best for analytics demos with aggregations."
        )

        st.session_state.use_enhanced_generation = (generation_mode == "Advanced")

        if generation_mode == "Advanced":
            # Show helpful guidance based on dataset size
            current_size = st.session_state.dataset_size_preference
            if current_size == "small":
                st.info("💡 **Tip:** Advanced mode works best with **Medium** or **Large** dataset sizes for more stable percentile calculations.", icon="ℹ️")
            elif current_size == "medium":
                st.success("✅ **Optimal:** Medium size is perfect for advanced mode!", icon="✅")
            else:  # large
                st.success("✅ **Excellent:** Large datasets provide the most stable percentile-based queries!", icon="✅")

        # Initialize ai_expansion_enabled if not exists
        if "ai_expansion_enabled" not in st.session_state:
            st.session_state.ai_expansion_enabled = False
        if "ai_expansion_used" not in st.session_state:
            st.session_state.ai_expansion_used = False

        # Demo Complexity Radio (only show if conversation hasn't started yet)
        if not st.session_state.messages:
            demo_complexity = st.radio(
                "Demo Complexity",
                options=["Simple", "Expanded"],
                index=1 if st.session_state.ai_expansion_enabled else 0,
                disabled=st.session_state.ai_expansion_used,
                key="demo_complexity_radio",
                help="Expanded mode automatically enhances brief prompts into detailed customer contexts using AI. Works on first message only."
            )
            st.session_state.ai_expansion_enabled = (demo_complexity == "Expanded")

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
