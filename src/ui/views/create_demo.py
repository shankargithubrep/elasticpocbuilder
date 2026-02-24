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

    # Initialize state for complexity selection
    if "ai_expansion_enabled" not in st.session_state:
        st.session_state.ai_expansion_enabled = None  # Force user to choose
    if "ai_expansion_used" not in st.session_state:
        st.session_state.ai_expansion_used = False
    if "complexity_selection_required" not in st.session_state:
        st.session_state.complexity_selection_required = True

    # Display messages
    if not st.session_state.messages:
        st.markdown("""
        ### 👋 Get Started

        Review the Demo Generation Options in the sidebar, then choose your Demo Complexity mode below before entering your customer description.

        **Note:** Since module generation is LLM-assisted, some variance is expected even with identical inputs. This is still an experimental utility, so if generation fails you may need to try again (and consider using a smarter model).
        """)

        # Demo Complexity Control (REQUIRED before input)
        st.markdown("**Demo Complexity** *(required)*")

        complexity_options = ["Simple", "Expanded"]

        # Determine current index based on session state
        if st.session_state.ai_expansion_enabled is None:
            current_index = None
        else:
            current_index = 1 if st.session_state.ai_expansion_enabled else 0

        selected_complexity = st.radio(
            "Choose how the LLM should process your input:",
            options=complexity_options,
            index=current_index,
            disabled=st.session_state.ai_expansion_used,
            key="complexity_radio",
            help="**Simple**: Direct processing of your prompt\n\n**Expanded**: LLM enhances brief prompts into detailed technical contexts",
            horizontal=True
        )

        # Update session state based on selection
        if selected_complexity == "Simple":
            st.session_state.ai_expansion_enabled = False
            st.session_state.complexity_selection_required = False
        elif selected_complexity == "Expanded":
            st.session_state.ai_expansion_enabled = True
            st.session_state.complexity_selection_required = False

        # Show description of selected mode
        if st.session_state.ai_expansion_enabled is True:
            st.info("💡 **Expanded mode**: Your brief prompt will be enhanced into a detailed technical context")
        elif st.session_state.ai_expansion_enabled is False:
            st.info("💡 **Simple mode**: Your prompt will be processed directly without expansion")

        st.markdown("")  # Spacing

        # Expandable section for detailed prompt guidance
        with st.expander("🔍 View Demo Complexity Expansion Prompt"):
            st.info("ℹ️ This shows the LLM instructions used when the **Expanded** option is selected for Demo Complexity in the sidebar. The LLM uses this template to transform brief prompts into detailed customer contexts.")
            st.markdown("""
            ### Step 1: Create a Customer Context JSON

            Start by creating a simple JSON structure with basic customer information:

            ```json
            {
              "customer_context": {
                "company_name": "Customer-ABC",
                "department": "CTO Group",
                "industry": "Financial Services",
                "pain_points": [
                  "High infrastructure costs on Intel hardware",
                  "No unified framework for data collection and analysis",
                  "Data scattered across disparate systems (Kafka queues, Hive)"
                ],
                "use_cases": [
                  "Run baseline and stress test benchmarks to compare hardware performance",
                  "Demonstrate application performance migration from Intel to AMD hardware",
                  "Consolidate data from Kafka queues and Hive into unified observability platform"
                ],
                "metrics": [
                  "user engagement",
                  "response time",
                  "delta of cost between Intel chipset & AMD chipset architecture",
                  "task completion rate"
                ],
                "demo_type": "analytics"
              }
            }
            ```

            ### Step 2: Expand with an LLM (Recommended: Claude Sonnet)

            Submit the JSON above **plus** the following prompt to your LLM of choice. Then paste the LLM response into the chat input below.

            ---

            #### Prompt: Use Case Expansion & Data Source Mapping

            You are an Elastic Solutions Architect creating a detailed technical use case document. You will receive sparse customer context including company name, department, pain points, and basic use cases. Your task is to transform this into a comprehensive, realistic document that aligns with actual enterprise data sources and Elastic Observability capabilities.

            **Input Format**

            You'll receive JSON or text containing:
            - Customer name, department, industry
            - Brief pain points (1-2 sentences each)
            - High-level use cases (simple descriptions)
            - Basic metrics mentioned (optional)

            **Output Requirements**

            **1. Customer Profile Section**

            Expand the basic customer info to include:
            - Full company name and department
            - Industry vertical
            - **Use Case Category**: Choose from Infrastructure, Security, Application Performance, Business Analytics, Cost Management, Customer Experience, DevOps/SRE
            - **Primary Interest**: The main Elastic solution area (APM, Infrastructure Monitoring, Logs, Security, etc.)

            **2. Pain Points Section (3-6 detailed pain points)**

            Transform each basic pain point into a detailed, technical description that:
            - Explains the business impact (cost, risk, efficiency, customer experience)
            - Describes the technical root cause (tooling gaps, data silos, visibility issues, scale challenges)
            - Includes realistic specifics: mention actual tools/systems enterprises use (Kafka, Splunk, Prometheus, cloud providers, databases, etc.)
            - Uses 2-4 sentences per pain point
            - Groups related pain points under subheadings if >4 total (e.g., "Infrastructure Challenges", "Data Platform Issues")

            Example transformation:
            - **Input**: "No unified framework for data collection"
            - **Output**: "No standardized performance benchmarking framework: Each team runs ad-hoc performance tests with different tools, metrics, and methodologies, making it impossible to compare results across applications or hardware platforms objectively. Critical decisions about infrastructure investments lack data-driven justification."

            **3. Key Metrics & Data Sources Section**

            This is the most critical section. For each category of metrics:

            Structure each category as:
            ```
            ### [Category Name] (via [Data Collection Method])
            * **[Specific Metric Name]**:
              - Field names: `field.name.notation` following Elastic Common Schema or OpenTelemetry conventions
              - Description of what's measured
              - Source system (if data exists elsewhere like Kafka, databases, APIs)
              - Optional: breakdown dimensions (by host, service, region, etc.)
            ```

            **Data Collection Methods to Reference:**
            - Metricbeat modules (System, Kafka, Redis, MySQL, Kubernetes, etc.)
            - APM Agents (Java, Node.js, Python, .NET, Go, RUM)
            - Filebeat modules (Nginx, Apache, System logs, application logs)
            - Custom Beats or API integrations
            - OpenTelemetry SDKs and collectors
            - Elastic integrations (AWS, Azure, GCP, Kubernetes)
            - Data pipelines (Kafka → Logstash → Elasticsearch)

            **Field Naming Guidelines:**
            - Use ECS (Elastic Common Schema) field conventions: `host.name`, `service.name`, `event.outcome`
            - For APM: `transaction.duration.us`, `span.type`, `trace.id`
            - For infrastructure: `system.cpu.total.pct`, `system.memory.used.bytes`
            - For custom metrics: `labels.custom_field` or logical namespace patterns
            - Always use actual field names, never placeholder brackets like `[field_name]`

            Identify 4-8 metric categories relevant to the use case:
            - Application Performance Metrics (APM)
            - Infrastructure/System Metrics (CPU, memory, disk, network)
            - Business/Custom Metrics (transactions, conversions, user actions)
            - Cost/Financial Metrics (if relevant)
            - Data Platform Metrics (Kafka, databases, queues)
            - Error & Availability Metrics
            - Security Metrics (if relevant)
            - User Experience Metrics (RUM, if relevant)

            **4. Use Cases Section (5-8 detailed use cases)**

            Expand each basic use case into a comprehensive description with:

            ```
            ### [Number]. [Descriptive Use Case Title]

            **Objective**: One sentence clearly stating the business or technical goal.

            **Implementation**:
            - Bullet points describing HOW this would be implemented
            - Reference specific Elastic features (dashboards, Lens visualizations, Canvas, Anomaly Detection, Alerting)
            - Mention data collection approaches from section 3
            - Include technical details: what gets instrumented, monitored, or integrated

            **Key Metrics**:
            - List 3-6 specific metrics tracked for this use case
            - Reference field names from section 3
            - Include thresholds or targets where appropriate

            **Output/Benefits**:
            - What insights or actions result
            - Specific example: "Output: 'AMD processors handle 35% more requests at same latency SLA'"
            - Business value delivered
            ```

            **Use Case Guidelines:**
            - Each use case should be realistic and implementable
            - Reference actual Elastic capabilities (not hypothetical features)
            - Progress from foundational (monitoring, visibility) to advanced (optimization, prediction) use cases
            - Include at least one use case about data consolidation if pain points mention disparate systems
            - Include at least one use case about cost analysis if financial concerns are mentioned
            - End with an executive reporting or business validation use case if appropriate

            **5. Optional Sections (include if relevant to use case)**

            **Data Model & Index Strategy:**
            - Recommended index patterns
            - Critical field mappings (10-15 key fields with descriptions)
            - Data retention considerations

            **Implementation Timeline:**
            - 4-6 phase breakdown with week ranges
            - What gets deployed/configured in each phase
            - Milestones and deliverables

            **Tone & Style Guidelines**

            - **Be specific and technical**: Use real product names, actual field names, concrete numbers
            - **Be realistic**: Only reference data sources that enterprises actually have or can realistically collect
            - **Avoid vagueness**: Replace "various metrics" with specific named metrics
            - **Use industry terminology**: Match the customer's industry (financial services, healthcare, retail, etc.)
            - **No query language examples**: Do not include ESQL, KQL, or any query syntax
            - **No placeholder text**: Replace all [placeholders] with realistic examples

            **Validation Checklist**

            Before finalizing, ensure:
            - ✓ Every metric has realistic field names in dot.notation
            - ✓ Data collection methods are specified (Metricbeat, APM, Filebeat, etc.)
            - ✓ Pain points include technical root causes, not just symptoms
            - ✓ Use cases have clear objectives and implementation steps
            - ✓ No ESQL, KQL, or query syntax appears anywhere
            - ✓ Industry-specific terminology is used appropriately
            - ✓ All systems/tools mentioned are real products enterprises use

            ---

            ### Step 3: Paste the LLM Response

            Once you have the expanded description from your LLM, paste it into the chat input below to generate your demo!
            """)

        st.divider()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

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

            # STEP 3: Show expanded content
            with st.chat_message("assistant"):
                st.markdown("### 📝 Expanded Technical Context")
                with st.expander("View full expanded context", expanded=False):
                    st.markdown(expanded_content)

                st.session_state.messages.append({"role": "assistant", "content": f"### 📝 Expanded Technical Context\n\n{expanded_content}"})
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

    # Chat input with validation
    if prompt := st.chat_input("Paste your customer description or type your response..."):
        # Validate that complexity has been selected (only for first message)
        if (len(st.session_state.messages) == 0 and
            st.session_state.ai_expansion_enabled is None):
            # Show error and don't process input
            st.error("⚠️ **Please select a Demo Complexity mode** (Simple or Expanded) above before submitting your customer description.")
            st.stop()

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
            with st.chat_message("assistant"):
                with st.spinner("🌋 Generating custom demo module..."):
                    try:
                        # Create config from context
                        context = st.session_state.demo_context
                        config = {
                            "company_name": context.get("company_name", "Demo Company"),
                            "department": context.get("department", "Operations"),
                            "industry": context.get("industry", "Enterprise"),
                            "pain_points": context.get("pain_points", []),
                            "use_cases": context.get("use_cases", []),
                            "metrics": context.get("metrics", []),
                            "demo_type": context.get("demo_type", "analytics"),
                            "dataset_size_preference": st.session_state.get("dataset_size_preference", "medium"),
                            "use_enhanced_generation": True,  # Always use enhanced generation
                            "full_technical_context": context.get("full_technical_context")  # Pass rich context for high-fidelity generation
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
                        st.session_state.demo_just_generated = True  # Set flag to show "View Demo Details" button

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
