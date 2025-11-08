"""
Create Demo view - conversational demo generation interface
"""

import streamlit as st
import logging

from src.framework import ModularDemoOrchestrator
from ..message_processor import process_smart_message

logger = logging.getLogger(__name__)


def render_create_demo_view():
    """Render the demo creation interface"""
    st.title("🚀 Elastic Agent Builder Demo Generator")
    st.markdown("*Create custom demos with LLM-generated modules*")

    # Display messages
    if not st.session_state.messages:
        st.info("""
        👋 **Welcome!** Paste your customer description and I'll extract context automatically.

        **Example:** *"Salesforce's Customer Success team wants to prevent churn in their 5,000+
        enterprise accounts worth $10B in ARR..."*
        """)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Show "View Demo Details" button if a demo was just generated
    if st.session_state.current_demo_module and st.session_state.view_mode == "create":
        if st.button("📂 View Demo Details", key="view_demo_btn", type="primary"):
            st.session_state.view_mode = "browse"
            st.rerun()

    # Process programmatically added messages
    if st.session_state.needs_processing and st.session_state.messages:
        last_message = st.session_state.messages[-1]
        if last_message["role"] == "user":
            st.session_state.needs_processing = False

            with st.chat_message("assistant"):
                with st.spinner("Analyzing context..."):
                    response = process_smart_message(last_message["content"])
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()

    # Chat input
    if prompt := st.chat_input("Paste your customer description or type your response..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Check if this is a generate command
        if prompt.lower().strip() == "generate" and st.session_state.conversation_phase == "ready_to_generate":
            with st.chat_message("assistant"):
                with st.spinner("🚀 Generating custom demo module..."):
                    try:
                        # Create config from context
                        context = st.session_state.demo_context
                        config = {
                            "company_name": context.get("company_name", "Demo Company"),
                            "department": context.get("department", "Operations"),
                            "industry": context.get("industry", "Enterprise"),
                            "pain_points": context.get("pain_points", []),
                            "use_cases": context.get("use_cases", []),
                            "scale": context.get("scale", "10000 records"),
                            "metrics": context.get("metrics", []),
                            "demo_type": context.get("demo_type", "analytics"),
                            "dataset_size_preference": st.session_state.get("dataset_size_preference", "medium")
                        }

                        # Create enhanced progress display with phase tracking using empty placeholders
                        st.markdown(f"### 🚀 Demo Generation Progress")

                        # Define all 8 phases
                        phases = [
                            {"name": "Strategy", "icon": "🎯", "desc": "Planning query strategy"},
                            {"name": "Data Module", "icon": "🤖", "desc": "Generating data module"},
                            {"name": "Datasets", "icon": "📦", "desc": "Creating datasets"},
                            {"name": "Indexing", "icon": "🔍", "desc": "Indexing in Elasticsearch"},
                            {"name": "Profiling", "icon": "📊", "desc": "Profiling indexed data"},
                            {"name": "Queries", "icon": "🔧", "desc": "Generating ES|QL queries"},
                            {"name": "Testing", "icon": "🧪", "desc": "Testing queries"},
                            {"name": "Cleanup", "icon": "✨", "desc": "Finalizing demo"}
                        ]

                        # Create placeholders for dynamic updates
                        progress_bar_placeholder = st.empty()
                        phases_placeholder = st.empty()
                        current_status_placeholder = st.empty()

                        phase_status = {phase["name"]: "pending" for phase in phases}
                        last_update_state = {"progress": 0.0, "phase": None}

                        def update_progress(progress: float, message: str):
                            """Update progress with enhanced phase tracking (only updates changed elements)"""
                            # Determine current phase based on progress and message
                            if progress <= 0.05:
                                current_phase = "Strategy"
                                current_phase_num = 1
                            elif progress <= 0.15:
                                phase_status["Strategy"] = "complete"
                                current_phase = "Data Module"
                                current_phase_num = 2
                            elif progress <= 0.3:
                                phase_status["Data Module"] = "complete"
                                current_phase = "Datasets"
                                current_phase_num = 3
                            elif progress <= 0.5:
                                phase_status["Datasets"] = "complete"
                                current_phase = "Indexing"
                                current_phase_num = 4
                            elif progress <= 0.6:
                                phase_status["Indexing"] = "complete"
                                current_phase = "Profiling"
                                current_phase_num = 5
                            elif progress <= 0.65:
                                phase_status["Profiling"] = "complete"
                                current_phase = "Queries"
                                current_phase_num = 6
                            elif progress <= 0.85:
                                phase_status["Queries"] = "complete"
                                current_phase = "Testing"
                                current_phase_num = 7
                            else:
                                phase_status["Testing"] = "complete"
                                current_phase = "Cleanup"
                                current_phase_num = 8

                            if current_phase in phase_status:
                                phase_status[current_phase] = "in_progress"

                            # Only update UI if phase changed OR progress increased by at least 5%
                            phase_changed = last_update_state["phase"] != current_phase
                            progress_jump = progress - last_update_state["progress"] >= 0.05

                            if not (phase_changed or progress_jump):
                                return  # Skip update to reduce UI churn

                            last_update_state["progress"] = progress
                            last_update_state["phase"] = current_phase

                            # Update progress bar with phase name
                            progress_bar_placeholder.progress(
                                progress,
                                text=f"{int(progress * 100)}% - Step {current_phase_num}/8: {current_phase}"
                            )

                            # Update phase checklist (only if phase changed)
                            if phase_changed:
                                with phases_placeholder.container():
                                    st.markdown("#### Pipeline Steps:")
                                    for idx, phase in enumerate(phases, 1):
                                        status = phase_status.get(phase["name"], "pending")
                                        if status == "complete":
                                            st.markdown(f"**{idx}.** ✅ {phase['icon']} {phase['name']}")
                                        elif status == "in_progress":
                                            st.markdown(f"**{idx}.** 🔄 {phase['icon']} **{phase['name']}** - _{phase['desc']}_")
                                        else:
                                            st.markdown(f"**{idx}.** ⏸️ {phase['icon']} {phase['name']}")

                            # Always update current status (this is the only line that changes frequently)
                            current_status_placeholder.info(f"**Current:** {message}")


                        # Generate demo using modular orchestrator
                        # Pass inference endpoints from sidebar configuration
                        inference_endpoints = st.session_state.get("inference_endpoints", {
                            "rerank": ".rerank-v1-elasticsearch",
                            "completion": "completion-vulcan"
                        })
                        orchestrator = ModularDemoOrchestrator(inference_endpoints=inference_endpoints)

                        # Use Path 2: Query-first strategy with LOOKUP JOIN support
                        # Generates all three query types: scripted, parameterized, and RAG
                        results = orchestrator.generate_new_demo_with_strategy(
                            config,
                            update_progress,
                            conversation=st.session_state.messages
                        )

                        st.session_state.current_demo_module = results['module_name']

                        st.balloons()
                        st.success(f"✅ Demo module created: **{results['module_name']}**")

                        response = f"""Your custom demo module is ready! 🎉

**Module:** `{results['module_name']}`

**Generated:**
- ✅ Custom data generator ({len(results['datasets'])} datasets)
- ✅ ES|QL queries ({len(results['queries'])} queries)
- ✅ Demo guide and talk track

**Next Steps:**
1. Click "Browse Demos" in the sidebar to view all details
2. Download the demo guide and queries
3. The module is saved in `demos/{results['module_name']}/` for customization

You can now refine the generated modules or start a new demo!"""

                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})

                    except Exception as e:
                        error_msg = f"Error generating demo: {str(e)}"
                        st.error(error_msg)
                        logger.error(f"Demo generation failed: {e}", exc_info=True)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})

        else:
            # Normal conversation
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    response = process_smart_message(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
            # Force rerun to update sidebar with new context
            st.rerun()
