"""
Create Demo view - conversational demo generation interface
"""

import streamlit as st
import logging

from src.framework import ModularDemoOrchestrator
from ..message_processor import process_smart_message, expand_brief_prompt
from ..guided_expansion_flow import run_guided_expansion

logger = logging.getLogger(__name__)


def render_create_demo_view():
    """Render the demo creation interface"""

    # Initialize state for complexity selection (default: expanded)
    if "ai_expansion_enabled" not in st.session_state:
        st.session_state.ai_expansion_enabled = True
    if "ai_expansion_used" not in st.session_state:
        st.session_state.ai_expansion_used = False
    if "complexity_selection_required" not in st.session_state:
        st.session_state.complexity_selection_required = False

    # Display messages
    if not st.session_state.messages:
        st.markdown("### ⚡ Generate a Custom Demo")

        st.info("Elastic Demo Builder will automatically create a **Search/RAG** or **Analytics** demo module "
                "based on your prompt. To see examples of each type, click **Browse** in the sidebar.")

        st.markdown("""
        Describe your customer scenario below. Include as much as you can:

        - **Company & Department** — who is the customer?
        - **Industry** — what vertical are they in?
        - **Pain Points** — what problems are they facing?
        - **Use Cases** — what do they want to accomplish?
        - **Key Metrics** — what do they measure?

        Don't worry if you're missing some details — just say so in your prompt and Elastic Demo Builder will fill in the gaps. The more context you provide, the better the output.
        """)
        st.caption("Module generation is LLM-assisted — some variance is expected. "
                   "If generation fails, try again or use a smarter model.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Render expandable content (e.g., technical plan) if stored
            if "expanded_content" in message:
                with st.expander("View comprehensive technical plan", expanded=False):
                    st.markdown(message["expanded_content"])

    # Show "View Demo Details" button if a demo was just generated in this conversation
    if (st.session_state.current_demo_module and
        st.session_state.view_mode == "create" and
        st.session_state.get("demo_just_generated", False)):
        if st.button("📂 View Demo Details", key="view_demo_btn", type="primary"):
            st.session_state.view_mode = "browse"
            st.session_state.demo_just_generated = False  # Clear the flag
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

    # Check if guided expansion is in progress (BEFORE chat input)
    # This allows validation UI to render even after reruns
    if 'guided_expansion' in st.session_state and st.session_state.guided_expansion['stage'] in ['extracting', 'validating', 'expanding']:
        # Guided expansion in progress - get stored prompt
        stored_prompt = st.session_state.guided_expansion.get('original_prompt', '')

        # Run guided expansion flow (continues from current stage)
        expanded_content = run_guided_expansion(stored_prompt)

        if expanded_content:
            # Expansion complete - add messages and store result
            st.session_state.messages.append({"role": "user", "content": stored_prompt})

            # STEP 1: Extract basic context from ORIGINAL prompt
            with st.chat_message("user"):
                st.markdown(stored_prompt)

            with st.chat_message("assistant"):
                with st.spinner("📊 Extracting basic context..."):
                    response = process_smart_message(stored_prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

            # STEP 2: Show validation summary (what user reviewed/edited)
            ge_state = st.session_state.get('guided_expansion', {})
            validation_summary = ge_state.get('validation_summary', '')

            if validation_summary:
                with st.chat_message("assistant"):
                    st.markdown(validation_summary)
                    st.session_state.messages.append({"role": "assistant", "content": validation_summary})

            # STEP 3: Show expanded content with generate instructions
            with st.chat_message("assistant"):
                generate_instruction = "Type **generate** and press Enter to create your demo."
                st.markdown(f"### 📝 Expanded Technical Context\n\n{generate_instruction}")
                with st.expander("View comprehensive technical plan", expanded=False):
                    st.markdown(expanded_content)
                st.markdown(f"\n{generate_instruction}")

                # Store summary + expandable content in chat history
                # The message replay loop renders expanded_content via st.expander()
                content_lines = len(expanded_content.splitlines())
                stored_msg = (
                    f"### 📝 Expanded Technical Context\n\n"
                    f"{generate_instruction}\n\n"
                    f"*Comprehensive technical plan generated ({len(expanded_content):,} characters, {content_lines} lines). "
                    f"Expand below to review.*\n\n"
                    f"{generate_instruction}"
                )
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": stored_msg,
                    "expanded_content": expanded_content
                })
                st.session_state.ai_expansion_used = True  # Lock the feature

                # STEP 4: Store expanded content as full_technical_context
                st.session_state.demo_context['full_technical_context'] = expanded_content

                # Mark as rich document for high-fidelity generation
                completion_msg = f"✅ **Rich technical context preserved** ({len(expanded_content):,} characters)"
                st.caption(completion_msg)

            st.rerun()
        else:
            # Still in validation or extraction - validation UI is showing
            # Don't process chat input, just let the UI persist
            st.stop()

    # Chat input
    if prompt := st.chat_input("Paste your customer description or type your response..."):
        # Handle AI expansion if enabled (only for first message)
        # Store prompt and initialize guided expansion state
        if (st.session_state.ai_expansion_enabled and
            not st.session_state.ai_expansion_used and
            len(st.session_state.messages) == 0):  # First message only (before adding to messages)

            # Initialize guided expansion with original prompt
            st.session_state.guided_expansion = {
                'stage': 'extracting',
                'original_prompt': prompt,  # Store prompt for reruns
                'extraction': None,
                'validated_extraction': None,
                'expanded_content': None
            }

            # Trigger rerun to start guided expansion flow
            st.rerun()

        # Add user message (if not in guided expansion flow)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        # Check if this is a generate command
        if prompt.lower().strip() == "generate" and st.session_state.conversation_phase == "ready_to_generate":
            # Guard against duplicate generation (user typing 'generate' again kills in-flight work)
            if st.session_state.get("generation_in_progress"):
                st.warning("Generation is already in progress. Please wait for it to complete.")
                st.stop()
            st.session_state.generation_in_progress = True

            with st.chat_message("assistant"):
                with st.spinner("🌋 Generating custom demo module..."):
                    try:
                        # Create config from context
                        context = st.session_state.demo_context

                        # Resolve pillar + demo_type from sidebar pillar selector
                        selected_pillar = st.session_state.get("selected_pillar", "search")
                        selected_sub = st.session_state.get("selected_sub_category", "")
                        pillar_to_demo_type = {
                            "search": "search",
                            "observability": "observability",
                            "security": "security",
                        }
                        resolved_demo_type = pillar_to_demo_type.get(
                            selected_pillar,
                            context.get("demo_type", "analytics")
                        )

                        config = {
                            "company_name": context.get("company_name", "Demo Company"),
                            "department": context.get("department", "Operations"),
                            "industry": context.get("industry", "Enterprise"),
                            "pain_points": context.get("pain_points", []),
                            "use_cases": context.get("use_cases", []),
                            "metrics": context.get("metrics", []),
                            "demo_type": resolved_demo_type,
                            # Three-pillar fields
                            "pillar": selected_pillar,
                            "sub_category": selected_sub,
                            "compliance_frameworks": context.get("compliance_frameworks", []),
                            "mitre_tactics": context.get("mitre_tactics", []),
                            "data_sources": context.get("data_sources", []),
                            "tech_stack": context.get("tech_stack", {}),
                            "environment_scale": context.get("environment_scale", {}),
                            # Generation settings
                            "dataset_size_preference": st.session_state.get("dataset_size_preference", "medium"),
                            "use_enhanced_generation": True,
                            "full_technical_context": context.get("full_technical_context"),
                            "llm_model": st.session_state.get("llm_model")
                        }

                        # Create enhanced progress display with phase tracking using empty placeholders
                        st.markdown(f"### 🚀 Demo Generation Progress")

                        # Define all 8 pipeline phases
                        # Progress ranges aligned to orchestrator callbacks:
                        #   Strategy:    0.00-0.14  (strategy + data specs)
                        #   Data Module: 0.15-0.29  (LLM code gen, per-dataset for split)
                        #   Datasets:    0.30-0.44  (execute generated code)
                        #   Indexing:    0.45-0.59  (index in ES, per-dataset sub-progress)
                        #   Profiling:   0.60-0.64  (profile indexed data)
                        #   Queries:     0.65-0.74  (generate ES|QL queries)
                        #   Testing:     0.75-0.84  (test and fix queries)
                        #   Finalizing:  0.85-1.00  (cleanup + save)
                        phases = [
                            {"name": "Strategy", "icon": "🎯", "desc": "Planning query strategy and data specifications"},
                            {"name": "Data Module", "icon": "🤖", "desc": "Generating data module code"},
                            {"name": "Datasets", "icon": "📦", "desc": "Creating datasets"},
                            {"name": "Indexing", "icon": "🔍", "desc": "Indexing in Elasticsearch"},
                            {"name": "Profiling", "icon": "📊", "desc": "Profiling indexed data"},
                            {"name": "Queries", "icon": "🔧", "desc": "Generating ES|QL queries"},
                            {"name": "Testing", "icon": "🧪", "desc": "Testing and fixing queries"},
                            {"name": "Finalizing", "icon": "✨", "desc": "Finalizing demo"}
                        ]

                        # Create placeholders for dynamic updates
                        progress_bar_placeholder = st.empty()
                        phases_placeholder = st.empty()
                        current_status_placeholder = st.empty()

                        phase_status = {phase["name"]: "pending" for phase in phases}
                        phase_start_times = {}  # Track when each phase started
                        phase_durations = {}    # Track completed phase durations
                        import time as _time
                        gen_start_time = _time.monotonic()
                        last_update_state = {"progress": 0.0, "phase": None}

                        # Phase boundary thresholds - aligned to orchestrator progress values
                        PHASE_BOUNDARIES = [
                            (0.15, "Strategy", 1),      # 0.00-0.14: strategy + data specs
                            (0.30, "Data Module", 2),    # 0.15-0.29: LLM code gen
                            (0.45, "Datasets", 3),       # 0.30-0.44: execute data gen
                            (0.60, "Indexing", 4),        # 0.45-0.59: index in ES
                            (0.65, "Profiling", 5),       # 0.60-0.64: profile data
                            (0.75, "Queries", 6),         # 0.65-0.74: generate queries
                            (0.85, "Testing", 7),         # 0.75-0.84: test queries
                            (1.01, "Finalizing", 8),      # 0.85-1.00: cleanup + save
                        ]

                        def update_progress(progress: float, message: str):
                            """Update progress with enhanced phase tracking (only updates changed elements)"""
                            # Determine current phase from boundaries
                            current_phase = "Strategy"
                            current_phase_num = 1
                            for threshold, phase_name, phase_num in PHASE_BOUNDARIES:
                                if progress < threshold:
                                    current_phase = phase_name
                                    current_phase_num = phase_num
                                    break

                            # Mark all prior phases as complete
                            for _, phase_name, phase_num in PHASE_BOUNDARIES:
                                if phase_num < current_phase_num:
                                    phase_status[phase_name] = "complete"

                            phase_status[current_phase] = "in_progress"

                            # Track phase start/end times
                            phase_changed = last_update_state["phase"] != current_phase
                            if phase_changed:
                                now = _time.monotonic()
                                # Record duration of previous phase
                                prev_phase = last_update_state["phase"]
                                if prev_phase and prev_phase in phase_start_times:
                                    phase_durations[prev_phase] = round(now - phase_start_times[prev_phase], 1)
                                # Start timing new phase
                                phase_start_times[current_phase] = now

                            # Only update UI if phase changed OR progress increased by at least 3%
                            progress_jump = progress - last_update_state["progress"] >= 0.03

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
                                        pname = phase["name"]
                                        status = phase_status.get(pname, "pending")
                                        dur = phase_durations.get(pname)
                                        dur_str = f" ({dur}s)" if dur is not None else ""
                                        if status == "complete":
                                            st.markdown(f"**{idx}.** ✅ {phase['icon']} {pname}{dur_str}")
                                        elif status == "in_progress":
                                            st.markdown(f"**{idx}.** 🔄 {phase['icon']} **{pname}** - _{phase['desc']}_")
                                        else:
                                            st.markdown(f"**{idx}.** ⏸️ {phase['icon']} {pname}")

                            # Always update current status with timestamp and elapsed time
                            from datetime import datetime
                            ts = datetime.now().strftime("%H:%M:%S")
                            elapsed_total = int(_time.monotonic() - gen_start_time)
                            elapsed_min, elapsed_sec = divmod(elapsed_total, 60)
                            elapsed_str = f"{elapsed_min}m {elapsed_sec}s" if elapsed_min else f"{elapsed_sec}s"
                            current_status_placeholder.info(f"**Current:** {message}  \n_Updated {ts} | Elapsed: {elapsed_str}_")


                        st.caption("⏳ The full generation pipeline takes 15–30 minutes depending on the LLM selected. Please do not type or click anything until generation completes.")

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

                        st.session_state.generation_in_progress = False
                        st.session_state.current_demo_module = results['module_name']
                        st.session_state.demo_just_generated = True  # Set flag to show "View Demo Details" button

                        st.balloons()

                        # Build timing summary for display
                        timing = results.get('timing', {})
                        total_secs = timing.get('total_seconds', int(_time.monotonic() - gen_start_time))
                        total_min, total_sec = divmod(int(total_secs), 60)
                        total_str = f"{total_min}m {total_sec}s" if total_min else f"{total_sec}s"

                        timing_lines = ""
                        for p in timing.get('phases', []):
                            secs = p['seconds']
                            m, s = divmod(int(secs), 60)
                            t = f"{m}m {s}s" if m else f"{s}s"
                            timing_lines += f"  - {p['phase']}: {t}\n"

                        st.success(f"✅ Demo module created: **{results['module_name']}** in {total_str}")

                        response = f"""Your custom demo module is ready!

**Module:** `{results['module_name']}`

**Generated:**
- ✅ Custom data generator ({len(results['datasets'])} datasets)
- ✅ ES|QL queries ({len(results['queries'])} queries)
- ✅ Demo guide and talk track

**Generation Time:** {total_str}
{timing_lines}
**Next Steps:**
1. Click "Browse Demos" in the sidebar to view all details
2. Download the demo guide and queries
3. The module is saved in `demos/{results['module_name']}/` for customization

You can now refine the generated modules or start a new demo!"""

                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})

                    except Exception as e:
                        # Use error display utility for consistent error formatting
                        from src.ui.error_display import display_error
                        from src.exceptions import VulcanException
                        
                        # Display the error in a user-friendly way
                        display_error(e, title="Demo Generation Failed")
                        
                        # Get user message for chat history
                        if isinstance(e, VulcanException):
                            error_msg = e.user_message
                        else:
                            error_msg = f"Error generating demo: {str(e)}"
                        
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        st.session_state.generation_in_progress = False

                        # Save conversation even on failure (orchestrator may not have reached save point)
                        try:
                            module_name = config.get('module_name') or st.session_state.get('current_demo_module')
                            if module_name:
                                from pathlib import Path
                                conv_path = Path("demos") / module_name / "conversation.json"
                                if conv_path.parent.exists() and not conv_path.exists():
                                    import json as _json
                                    from datetime import datetime as _dt
                                    conv_data = {
                                        'messages': st.session_state.messages,
                                        'context': config,
                                        'timestamp': _dt.now().isoformat(),
                                        'note': 'Saved from UI after generation error'
                                    }
                                    conv_path.write_text(_json.dumps(conv_data, indent=2))
                        except Exception:
                            pass  # Best effort

        else:
            # Normal conversation
            with st.chat_message("assistant"):
                try:
                    with st.spinner("Analyzing..."):
                        response = process_smart_message(prompt)
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    # Force rerun to update sidebar with new context
                    st.rerun()
                except Exception as e:
                    # Handle errors in conversation processing
                    from src.ui.error_display import display_error
                    from src.exceptions import VulcanException
                    
                    # Display the error
                    display_error(e, title="Message Processing Failed")
                    
                    # Add error message to chat history
                    if isinstance(e, VulcanException):
                        error_msg = e.user_message
                    else:
                        error_msg = f"Error processing message: {str(e)}"
                    
                    st.session_state.messages.append({"role": "assistant", "content": f"❌ {error_msg}"})
                    
                    # Show helpful message
                    st.info("💡 **You can:**\n- Fix the issue and try again\n- Type 'skip' to use defaults\n- Continue the conversation once the issue is resolved")
