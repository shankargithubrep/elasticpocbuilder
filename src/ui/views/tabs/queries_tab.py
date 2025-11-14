"""
Queries Tab - Displays and manages demo queries with execution, editing, and validation.
"""

import streamlit as st
import logging

from src.framework import DemoModuleManager
from src.ui.data_loaders import (
    load_demo_queries,
    load_demo_data_profile,
    get_sample_values_for_parameters,
    generate_sample_question
)
from src.ui.query_results_display import QueryResultsDisplay

logger = logging.getLogger(__name__)


def render_queries_tab(loader):
    """Render the Queries tab content.

    Args:
        loader: The demo module loader instance
    """
    # Only load if assets have been generated
    if st.session_state.get("assets_generated", False):
        try:
            queries_dict = load_demo_queries(st.session_state.current_demo_module)

            # Create sub-tabs for query types
            query_tabs = st.tabs([
                f"📝 Scripted ({len(queries_dict['scripted'])})",
                f"🔧 Parameterized ({len(queries_dict['parameterized'])})",
                f"🤖 RAG ({len(queries_dict['rag'])})"
            ])

            # Initialize QueryResultsDisplay for clean rendering
            display = QueryResultsDisplay()

            # Initialize edit mode state
            if "query_edit_mode" not in st.session_state:
                st.session_state.query_edit_mode = {}

            # Import validation service
            from src.services.query_validation_service import QueryValidationService
            validation_service = QueryValidationService(loader.module_path)

            # Helper function to render queries using the new display module
            def render_query_list(queries, query_type, can_execute=True):
                if queries:
                    for i, query in enumerate(queries, 1):
                        query_key = f"{query_type}_query_{i}"
                        original_query = display._get_query_text(query)

                        # Add anchor for scroll position
                        st.markdown(f'<div id="{query_key}"></div>', unsafe_allow_html=True)

                        # Check if query is validated
                        is_validated = validation_service.is_query_validated(query_key)

                        # Show validation status in header
                        col_header, col_status = st.columns([10, 1])
                        with col_header:
                            # Always show query metadata/title first
                            display.render_query_with_results(
                                query,
                                results=None,
                                show_pipeline_view=False,
                                unique_key=query_key,
                                allow_editing=False
                            )
                        with col_status:
                            if is_validated:
                                st.success("✅")

                        # Check if query has temp edits
                        temp_editor_key = f"temp_editor_{query_key}"
                        current_query = st.session_state.get(temp_editor_key, original_query)

                        # Check edit mode state - read from widget key in session_state
                        edit_toggle_key = f"edit_toggle_{query_key}"

                        # CRITICAL: Check if we just tested this query - preserve edit mode
                        just_tested_key = f"{query_key}_just_tested"
                        if just_tested_key in st.session_state:
                            # We just executed a test, ensure checkbox stays checked
                            st.session_state[edit_toggle_key] = True
                            del st.session_state[just_tested_key]

                        is_editing = st.session_state.get(edit_toggle_key, False)

                        # Debug: show edit state
                        st.caption(f"🔍 DEBUG: is_editing={is_editing}, toggle_key={edit_toggle_key}")

                        if is_editing:
                            # Show editor mode with text_area
                            st.markdown("---")
                            st.markdown("**✏️ Edit Mode**")

                            # Add JavaScript to scroll to this query
                            st.markdown(f"""
                            <script>
                            setTimeout(function() {{
                                var element = document.getElementById('{query_key}');
                                if (element) {{
                                    element.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                                }}
                            }}, 100);
                            </script>
                            """, unsafe_allow_html=True)

                            # Add custom CSS for larger monospace font in text_area
                            st.markdown("""
                            <style>
                            textarea {
                                font-family: 'Courier New', Courier, monospace !important;
                                font-size: 16px !important;
                                line-height: 1.5 !important;
                            }
                            </style>
                            """, unsafe_allow_html=True)

                            # Use text_area for editing
                            edited_query = st.text_area(
                                "Edit your ES|QL query:",
                                value=current_query,
                                height=300,
                                key=f"editor_{query_key}",
                                label_visibility="collapsed"
                            )

                            # Show status
                            if edited_query != original_query:
                                st.info(f"✏️ Query modified ({len(edited_query)} characters)")
                            else:
                                st.caption(f"Original query ({len(edited_query)} characters)")

                            # Store the edited query content to preserve it across reruns
                            if edited_query != current_query:
                                st.session_state[temp_editor_key] = edited_query

                            # Button for edit mode
                            if st.button("▶️ Test This Query", key=f"test_edit_{query_key}", use_container_width=True):
                                # Use the edited_query directly from text_area
                                if edited_query and edited_query.strip():
                                    from src.services.elasticsearch_indexer import ElasticsearchIndexer
                                    try:
                                        # Store the query being tested
                                        st.session_state[temp_editor_key] = edited_query

                                        # CRITICAL: Set flag to preserve edit mode on next render
                                        st.session_state[just_tested_key] = True

                                        indexer = ElasticsearchIndexer()
                                        success, result, error = indexer.execute_esql(edited_query)

                                        if success:
                                            st.session_state[f"{query_key}_results"] = result
                                            st.session_state[f"{query_key}_test_success"] = True
                                            # Don't call st.rerun() to avoid checkbox reset
                                        else:
                                            st.session_state[f"{query_key}_test_error"] = error
                                    except Exception as e:
                                        st.session_state[f"{query_key}_test_error"] = str(e)
                                else:
                                    st.session_state[f"{query_key}_test_error"] = "No query content in editor"

                            # Display success/error messages (keep them in session state)
                            if f"{query_key}_test_success" in st.session_state:
                                results = st.session_state.get(f"{query_key}_results", {})
                                st.success(f"✅ Query executed! {len(results.get('values', []))} rows returned")
                                # Don't delete - let it persist

                            if f"{query_key}_test_error" in st.session_state:
                                st.error(f"❌ {st.session_state[f'{query_key}_test_error']}")
                                # Don't delete - let it persist

                            # Display results if available (in edit mode)
                            if f"{query_key}_results" in st.session_state:
                                st.divider()
                                st.markdown("### 📊 Query Results")
                                display._render_query_results(st.session_state[f"{query_key}_results"], unique_key=f"edit_{query_key}")

                        # Add execution capability for scripted, parameterized, and RAG queries
                        # Only show these buttons when NOT in edit mode
                        if not is_editing and can_execute and query_type in ['scripted', 'parameterized', 'rag']:
                            query_key = f"{query_type}_query_{i}"

                            # For parameterized and RAG queries, show parameter inputs
                            if query_type in ['parameterized', 'rag'] and query.get('parameters'):
                                with st.expander("⚙️ Test with Parameters", expanded=False):
                                    # Load data profile for sample values
                                    data_profile = load_demo_data_profile(st.session_state.current_demo_module)

                                    # Show sample values from data profile if available
                                    if data_profile:
                                        sample_values_dict = get_sample_values_for_parameters(
                                            data_profile,
                                            query['parameters']
                                        )

                                        # Show sample values if found
                                        if sample_values_dict:
                                            with st.expander("💡 Sample Values from Data Profile", expanded=False):
                                                st.caption("Copy these sample values to test the query with real data")
                                                for param_name, values in sample_values_dict.items():
                                                    if values:
                                                        st.markdown(f"**{param_name}:**")
                                                        # Display as copyable code blocks
                                                        for val in values:
                                                            st.code(val, language=None)
                                                st.divider()

                                        # For parameters without sample values, offer "Suggest Question"
                                        params_without_values = [
                                            p for p in query['parameters']
                                            if p.get('name') not in sample_values_dict
                                        ]

                                        if params_without_values:
                                            with st.expander("💭 Generate Sample Questions (LLM)", expanded=False):
                                                st.caption("Use AI to generate contextual sample questions based on query purpose and available data")
                                                for param in params_without_values:
                                                    param_name = param.get('name', 'unknown')
                                                    col1, col2 = st.columns([3, 1])
                                                    with col1:
                                                        st.markdown(f"**{param_name}:** {param.get('description', 'No description')}")
                                                    with col2:
                                                        suggest_key = f"suggest_{query_key}_{param_name}"
                                                        if st.button("✨ Suggest", key=suggest_key, use_container_width=True):
                                                            with st.spinner("Generating suggestion..."):
                                                                suggested = generate_sample_question(query, param, data_profile)
                                                                st.session_state[f"{suggest_key}_value"] = suggested
                                                                # Note: Not calling st.rerun() to avoid tab reset

                                                    # Show generated suggestion
                                                    if f"{suggest_key}_value" in st.session_state:
                                                        st.code(st.session_state[f"{suggest_key}_value"], language=None)
                                                st.divider()

                                    param_values = display._render_parameter_inputs(
                                        query['parameters'],
                                        unique_key=query_key
                                    )

                                    # Test and Edit buttons
                                    col1, col2 = st.columns([1, 1])
                                    with col1:
                                        if st.button("▶️ Test with These Parameters", key=f"test_{query_key}", use_container_width=True):
                                            from src.services.elasticsearch_indexer import ElasticsearchIndexer
                                            query_name = query.get('name', f'Query {i}')

                                            with st.spinner(f"Executing {query_name}..."):
                                                try:
                                                    # Check if we're in edit mode and have temp editor content
                                                    temp_editor_key = f"temp_editor_{query_key}"
                                                    if temp_editor_key in st.session_state:
                                                        # Use current editor content
                                                        query_text = st.session_state[temp_editor_key]
                                                    else:
                                                        # Use original query
                                                        query_text = display._get_query_text(query)

                                                    # Substitute parameters into query
                                                    substituted_query = display.substitute_parameters(query_text, param_values)

                                                    # Execute
                                                    indexer = ElasticsearchIndexer()
                                                    success, result, error = indexer.execute_esql(substituted_query)

                                                    if success:
                                                        st.success("✅ Query executed successfully!")
                                                        # Store results and substituted query
                                                        st.session_state[f"{query_key}_results"] = result
                                                        st.session_state[f"{query_key}_substituted"] = substituted_query
                                                        # Note: Not calling st.rerun() to avoid tab reset
                                                    else:
                                                        st.error(f"❌ Query failed: {error}")
                                                except Exception as e:
                                                    st.error(f"❌ Error: {e}")

                                    with col2:
                                        # Edit mode checkbox - let Streamlit manage state via key
                                        st.checkbox(
                                            "✏️ Edit Query",
                                            key=f"edit_toggle_{query_key}"
                                        )

                            # For scripted queries, simple test button
                            elif query_type == 'scripted':
                                col1, col2, col3 = st.columns([1, 1, 2])
                                with col1:
                                    if st.button("▶️ Test Query", key=f"test_{query_key}", use_container_width=True):
                                        from src.services.elasticsearch_indexer import ElasticsearchIndexer
                                        query_name = query.get('name', f'Query {i}')

                                        with st.spinner(f"Executing {query_name}..."):
                                            try:
                                                indexer = ElasticsearchIndexer()

                                                # Check if we're in edit mode and have temp editor content
                                                temp_editor_key = f"temp_editor_{query_key}"
                                                if temp_editor_key in st.session_state and st.session_state[temp_editor_key]:
                                                    # Use current editor content
                                                    query_text = st.session_state[temp_editor_key]
                                                    st.info(f"Using edited query ({len(query_text)} chars)")
                                                else:
                                                    # Use original query
                                                    query_text = display._get_query_text(query)
                                                    st.info(f"Using original query ({len(query_text)} chars)")

                                                if not query_text or not query_text.strip():
                                                    st.error("❌ Query is empty!")
                                                    st.stop()

                                                success, result, error = indexer.execute_esql(query_text)

                                                if success:
                                                    st.success("✅ Query executed successfully!")
                                                    # Store results in session state for display
                                                    st.session_state[f"{query_key}_results"] = result
                                                    # Note: Not calling st.rerun() to avoid tab reset
                                                    # Results will display below automatically
                                                else:
                                                    st.error(f"❌ Query failed: {error}")
                                            except Exception as e:
                                                st.error(f"❌ Error: {e}")

                                with col2:
                                    # Edit mode checkbox - let Streamlit manage state via key
                                    st.checkbox(
                                        "✏️ Edit Query",
                                        key=f"edit_toggle_{query_key}"
                                    )

                            # Display substituted query if available (for parameterized)
                            if f"{query_key}_substituted" in st.session_state:
                                with st.expander("📝 Executed Query (with parameters)", expanded=False):
                                    st.code(st.session_state[f"{query_key}_substituted"], language='sql')

                            # Display results if available in session state
                            if f"{query_key}_results" in st.session_state:
                                with st.expander("📊 Query Results", expanded=True):
                                    display._render_query_results(st.session_state[f"{query_key}_results"], unique_key=query_key)

                                    # Add validation button after successful test
                                    col_val1, col_val2, col_val3 = st.columns([2, 2, 6])
                                    with col_val1:
                                        if is_validated:
                                            if st.button("❌ Mark as Unvalidated", key=f"unvalidate_{query_key}", use_container_width=True):
                                                validation_service.mark_query_unvalidated(query_key)
                                                st.rerun()
                                        else:
                                            if st.button("✅ Mark as Validated", key=f"validate_{query_key}", use_container_width=True, type="primary"):
                                                validation_service.mark_query_validated(query_key)
                                                st.rerun()
                                    with col_val2:
                                        if is_validated:
                                            st.success("Query is validated ✅")

                                # Check if query returned zero results - offer optimization
                                results = st.session_state[f"{query_key}_results"]
                                if (query_type == 'scripted' and results and
                                    'columns' in results and 'values' in results and
                                    len(results['values']) == 0):

                                    # Show optimize button for zero-results queries
                                    optimize_key = f"{query_key}_optimize"
                                    if st.button("🔧 Fix Query", key=optimize_key, help="Use LLM to relax constraints and improve results"):
                                        with st.spinner("Analyzing constraints..."):
                                            try:
                                                # Import optimizer
                                                from src.services.query_optimizer import relax_query_constraints
                                                import os
                                                import json
                                                from pathlib import Path
                                                from src.services.llm_proxy_service import UnifiedLLMClient

                                                # Get LLM client
                                                llm_client = UnifiedLLMClient()

                                                # Load data profile from demo directory if available
                                                data_profile = None
                                                demo_module_name = st.session_state.current_demo_module
                                                profile_path = Path("demos") / demo_module_name / "data_profile.json"
                                                if profile_path.exists():
                                                    try:
                                                        with open(profile_path, 'r') as f:
                                                            data_profile = json.load(f)
                                                    except Exception as e:
                                                        st.warning(f"Could not load data profile: {e}")

                                                # Get current query
                                                current_esql = display._get_query_text(query)

                                                # Optimize
                                                optimized_esql, explanation = relax_query_constraints(
                                                    query=query,
                                                    current_esql=current_esql,
                                                    data_profile=data_profile,
                                                    llm_client=llm_client
                                                )

                                                # Show optimized query
                                                st.success(f"✅ {explanation}")
                                                st.code(optimized_esql, language='sql')

                                                # Offer to test the optimized query
                                                if st.button("▶️ Test Optimized Query", key=f"{optimize_key}_test"):
                                                    from src.services.elasticsearch_indexer import ElasticsearchIndexer
                                                    try:
                                                        indexer = ElasticsearchIndexer()
                                                        success, test_results, error = indexer.execute_esql(optimized_esql)
                                                        if success:
                                                            st.session_state[f"{query_key}_results"] = test_results
                                                            st.success(f"Found {len(test_results.get('values', []))} results!")
                                                            st.rerun()
                                                        else:
                                                            st.error(f"Test failed: {error}")
                                                    except Exception as e:
                                                        st.error(f"Test failed: {e}")
                                            except Exception as e:
                                                st.error(f"Optimization failed: {e}")

                        # Pain point and dataset info
                        if query.get('pain_point'):
                            st.caption(f"📌 **Addresses:** {query['pain_point']}")
                        if query.get('datasets'):
                            st.caption(f"📊 **Uses datasets:** {', '.join(query['datasets'])}")

                        st.divider()
                else:
                    st.info(f"No {query_type} queries found.")

            # Render each query type in its tab
            with query_tabs[0]:
                st.markdown("### Scripted Queries")
                st.caption("Non-parameterized, fully tested ES|QL queries. These can be executed directly.")
                render_query_list(queries_dict['scripted'], 'scripted', can_execute=True)

            with query_tabs[1]:
                st.markdown("### Parameterized Queries")
                st.caption("Agent Builder ES|QL tool definitions with `?parameter` syntax. You can test these by providing parameter values!")
                render_query_list(queries_dict['parameterized'], 'parameterized', can_execute=True)

            with query_tabs[2]:
                st.markdown("### RAG Queries")
                st.caption("Semantic search queries using MATCH → RERANK → COMPLETION pipeline for open-ended Q&A.")
                render_query_list(queries_dict['rag'], 'rag', can_execute=True)

        except Exception as e:
            st.error(f"Error loading queries: {e}")
            st.info("Try clicking 'Generate Assets' in the Config tab.")
            import traceback
            with st.expander("Show traceback"):
                st.code(traceback.format_exc())
    else:
        st.info("📋 Click 'Generate Assets' in the Config tab to view queries")
