"""
Browse Demos view - view and manage generated demo modules
"""

import streamlit as st
import logging

from src.framework import DemoModuleManager
from ..data_loaders import (
    load_demo_datasets,
    load_demo_queries,
    load_demo_guide,
    load_demo_data_profile,
    get_sample_values_for_parameters,
    generate_sample_question
)
from ..query_results_display import QueryResultsDisplay

logger = logging.getLogger(__name__)


def get_module_prefix(module_name: str) -> str:
    """Extract company_department prefix from module name or metadata.

    For example: 'jp_morgan_chase_(jpmc)_cto group - infrastructure...' -> 'jpmc_cto'
    """
    import json
    import os

    try:
        # Try to load agent metadata to get the proper prefix
        agent_metadata_path = os.path.join("demos", module_name, "agent_metadata.json")
        if os.path.exists(agent_metadata_path):
            with open(agent_metadata_path, 'r') as f:
                metadata = json.load(f)
                agent_id = metadata.get('id', '')
                # Agent ID format: company_department_agent
                # We want: company_department
                if agent_id and agent_id.endswith('_agent'):
                    return agent_id[:-6]  # Remove '_agent' suffix

        # Fallback: Try to load tool metadata to get prefix pattern
        tool_metadata_path = os.path.join("demos", module_name, "tool_metadata.json")
        if os.path.exists(tool_metadata_path):
            with open(tool_metadata_path, 'r') as f:
                metadata = json.load(f)
                # Look at any tool ID to extract the prefix
                for key, value in metadata.items():
                    if isinstance(value, dict) and 'tool_id' in value:
                        tool_id = value['tool_id']
                        # Tool ID format: company_department_purpose
                        # We want: company_department
                        parts = tool_id.split('_')
                        if len(parts) >= 3:
                            return '_'.join(parts[:2])

        # Fallback: Try to extract from module name itself
        # This is less reliable but better than nothing
        parts = module_name.lower().replace(' ', '_').replace('-', '_').split('_')
        if len(parts) >= 2:
            # Take first two meaningful parts
            return f"{parts[0]}_{parts[1]}"

        return module_name.lower()[:30]  # Last resort fallback
    except Exception as e:
        logger.warning(f"Error extracting module prefix: {e}")
        return module_name.lower()[:30]


def render_browse_demos_view():
    """Render the demo browsing interface - demo details only (list is in sidebar)"""
    # Show details if a module is selected
    if st.session_state.current_demo_module:
        st.title(f"📊 {st.session_state.current_demo_module}")

        manager = DemoModuleManager()
        loader = manager.get_module(st.session_state.current_demo_module)

        if loader:
            # Create tabs FIRST to prevent resets
            tabs = st.tabs(["📋 Config", "🗂️ Data", "🔍 Queries", "📝 Guide", "💬 Conversation", "🤖 Agents & Tools"])

            # Auto-load assets when demo is selected (after tabs are created)
            # Use a session state key specific to this demo to track if we've loaded
            assets_key = f"assets_loaded_{st.session_state.current_demo_module}"

            if not st.session_state.get(assets_key, False):
                with st.spinner("Loading demo assets..."):
                    try:
                        # Load all assets
                        datasets = load_demo_datasets(st.session_state.current_demo_module)
                        queries = load_demo_queries(st.session_state.current_demo_module)
                        guide = load_demo_guide(st.session_state.current_demo_module)

                        # Mark assets as loaded for this specific demo
                        st.session_state[assets_key] = True
                        st.session_state.assets_generated = True  # Keep for backwards compatibility
                    except Exception as e:
                        logger.error(f"Error auto-loading assets: {e}")
                        st.error(f"Error loading assets: {e}")

            with tabs[0]:
                # Use the new ModuleVisualizer for enhanced Config display
                try:
                    from ..module_visualizer import ModuleVisualizer
                    import anthropic
                    import os

                    # Get LLM client if available
                    llm_client = None
                    api_key = os.getenv("ANTHROPIC_API_KEY")
                    if api_key:
                        llm_client = anthropic.Anthropic(api_key=api_key)

                    # Create and render visualizer
                    visualizer = ModuleVisualizer(loader.module_path, llm_client)
                    visualizer.render_module_overview()

                except ImportError:
                    # Fallback to simple JSON display if visualizer not available
                    st.markdown("### Demo Configuration")
                    st.json(loader.config)
                except Exception as e:
                    logger.warning(f"Could not render module visualization: {e}")
                    # Fallback to simple JSON display
                    st.markdown("### Demo Configuration")
                    st.json(loader.config)

                st.divider()
                st.markdown("### Regenerate Assets")
                st.caption("Force regeneration of datasets, queries, and guide")

                if st.button("🔄 Regenerate Assets", use_container_width=True):
                    with st.spinner("Regenerating demo assets..."):
                        try:
                            # Force regeneration by clearing cache and loading
                            load_demo_datasets.clear()
                            load_demo_queries.clear()
                            load_demo_guide.clear()

                            # Generate all assets
                            datasets = load_demo_datasets(st.session_state.current_demo_module)
                            queries = load_demo_queries(st.session_state.current_demo_module)
                            guide = load_demo_guide(st.session_state.current_demo_module)

                            # Mark assets as regenerated
                            st.session_state[assets_key] = True
                            st.session_state.assets_generated = True

                            st.success(f"✅ Regenerated {len(datasets)} datasets, {len(queries)} queries, and demo guide!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error regenerating assets: {e}")
                            import traceback
                            st.code(traceback.format_exc())

            with tabs[1]:
                # Only load if assets have been generated
                if st.session_state.get("assets_generated", False):
                    try:
                        datasets = load_demo_datasets(st.session_state.current_demo_module)

                        # Get semantic fields specification from data generator
                        manager = DemoModuleManager()
                        loader = manager.get_module(st.session_state.current_demo_module)
                        data_gen = loader.load_data_generator()

                        # Try to get semantic fields (may not exist in older modules)
                        try:
                            semantic_fields_spec = data_gen.get_semantic_fields()
                        except AttributeError:
                            semantic_fields_spec = {}

                        # Load index_mode mapping from query_strategy.json
                        index_mode_map = {}
                        try:
                            from pathlib import Path
                            import json
                            strategy_path = Path('demos') / st.session_state.current_demo_module / 'query_strategy.json'
                            if strategy_path.exists():
                                with open(strategy_path, 'r') as f:
                                    query_strategy = json.load(f)
                                    for dataset in query_strategy.get('datasets', []):
                                        dataset_name = dataset.get('name')
                                        if dataset_name:
                                            # Prefer explicit index_mode, fallback to type-based mapping
                                            if 'index_mode' in dataset:
                                                index_mode_map[dataset_name] = dataset['index_mode']
                                            else:
                                                # Fallback logic
                                                dataset_type = dataset.get('type')
                                                if dataset_type == 'reference':
                                                    index_mode_map[dataset_name] = 'lookup'
                                                elif dataset_type == 'timeseries':
                                                    index_mode_map[dataset_name] = 'data_stream'
                                                elif dataset_type in ['documents', 'records']:
                                                    index_mode_map[dataset_name] = 'lookup'
                                                else:
                                                    index_mode_map[dataset_name] = 'lookup'  # Safe default
                        except Exception as e:
                            import logging
                            logging.warning(f"Could not load index_mode mapping: {e}")

                        if datasets:
                            # Index All button at the top
                            if st.button("📤 Index All Datasets", use_container_width=True, type="primary"):
                                from src.services.elasticsearch_indexer import ElasticsearchIndexer

                                st.info(f"Starting batch indexing for {len(datasets)} datasets...")

                                indexer = ElasticsearchIndexer()
                                for idx, (name, df) in enumerate(datasets.items(), 1):
                                    st.markdown(f"**[{idx}/{len(datasets)}] Indexing {name}...**")

                                    # Get semantic fields for this dataset
                                    semantic_fields = semantic_fields_spec.get(name, [])

                                    # Get index_mode for this dataset
                                    index_mode = index_mode_map.get(name, 'lookup')  # Default to lookup

                                    progress_bar = st.progress(0)
                                    status_text = st.empty()

                                    def progress_callback(pct, msg):
                                        progress_bar.progress(pct)
                                        status_text.text(msg)

                                    try:
                                        result = indexer.index_dataset(
                                            df,
                                            name,
                                            semantic_fields=semantic_fields,
                                            index_mode=index_mode,
                                            progress_callback=progress_callback
                                        )

                                        if result.success:
                                            st.success(f"✅ {name}: {result.documents_indexed:,} docs indexed in {result.duration_seconds}s")
                                        else:
                                            st.error(f"❌ {name}: Indexing failed")
                                    except Exception as e:
                                        st.error(f"❌ {name}: {str(e)}")

                                st.success("🎉 Batch indexing complete!")

                            st.divider()

                            for name, df in datasets.items():
                                st.markdown(f"### {name}")

                                # Action buttons
                                col1, col2, col3, col4 = st.columns(4)

                                with col1:
                                    # Download CSV
                                    csv = df.to_csv(index=False)
                                    st.download_button(
                                        "📥 CSV",
                                        csv,
                                        f"{name}.csv",
                                        "text/csv",
                                        key=f"download_data_{st.session_state.current_demo_module}_{name}",
                                        use_container_width=True
                                    )

                                with col2:
                                    # View data
                                    if st.button("👁️ View", key=f"view_{name}", use_container_width=True):
                                        st.session_state[f"show_data_{name}"] = not st.session_state.get(f"show_data_{name}", False)

                                with col3:
                                    # Data Profile Summary button
                                    if st.button("📊 Profile", key=f"profile_{name}", use_container_width=True):
                                        st.session_state[f"show_profile_{name}"] = not st.session_state.get(f"show_profile_{name}", False)

                                with col4:
                                    # Index in Elasticsearch button
                                    if st.button("📤 Index", key=f"index_{name}", use_container_width=True):
                                        from src.services.elasticsearch_indexer import ElasticsearchIndexer

                                        # Get semantic fields for this dataset
                                        semantic_fields = semantic_fields_spec.get(name, [])

                                        # Get index_mode for this dataset
                                        index_mode = index_mode_map.get(name, 'lookup')  # Default to lookup

                                        # Show progress and stop button
                                        progress_bar = st.progress(0)
                                        status_text = st.empty()
                                        stop_button_container = st.empty()

                                        # Track stop request in session state
                                        stop_key = f"stop_indexing_{name}"
                                        st.session_state[stop_key] = False

                                        def progress_callback(pct, msg):
                                            progress_bar.progress(pct)
                                            status_text.text(msg)

                                        def stop_callback():
                                            return st.session_state.get(stop_key, False)

                                        # Show stop button
                                        if stop_button_container.button("⏸️ Stop Indexing", key=f"stop_{name}"):
                                            st.session_state[stop_key] = True

                                        try:
                                            # Index the dataset
                                            indexer = ElasticsearchIndexer()
                                            result = indexer.index_dataset(
                                                df,
                                                name,
                                                semantic_fields=semantic_fields,
                                                index_mode=index_mode,
                                                progress_callback=progress_callback,
                                                stop_callback=stop_callback
                                            )

                                            # Clear stop button
                                            stop_button_container.empty()

                                            # Store result in session state to display outside column
                                            st.session_state[f"index_result_{name}"] = {
                                                'success': result.success,
                                                'documents_indexed': result.documents_indexed,
                                                'total_docs': len(df),
                                                'index_name': result.index_name,
                                                'index_type': result.index_type,
                                                'semantic_fields': result.semantic_fields,
                                                'duration_seconds': result.duration_seconds,
                                                'errors': result.errors if not result.success else [],
                                                'was_stopped': st.session_state.get(stop_key, False)
                                            }

                                        except Exception as e:
                                            stop_button_container.empty()
                                            st.session_state[f"index_result_{name}"] = {
                                                'success': False,
                                                'error': str(e),
                                                'traceback': __import__('traceback').format_exc()
                                            }

                                # Display indexing result outside columns (full width)
                                if f"index_result_{name}" in st.session_state:
                                    result_data = st.session_state[f"index_result_{name}"]

                                    if 'error' in result_data:
                                        # Exception occurred
                                        st.error(f"❌ Indexing error: {result_data['error']}")
                                        st.code(result_data['traceback'])
                                    elif result_data['success']:
                                        # Check if actually stopped by user
                                        was_stopped_by_user = result_data['was_stopped']
                                        incomplete_indexing = result_data['documents_indexed'] < result_data['total_docs']

                                        if was_stopped_by_user and incomplete_indexing:
                                            st.warning(
                                                f"⏸️ Indexing stopped by user\n\n"
                                                f"**Indexed:** {result_data['documents_indexed']:,} / {result_data['total_docs']:,} documents\n\n"
                                                f"**Index:** {result_data['index_name']} ({result_data['index_type']})\n\n"
                                                f"**Semantic fields:** {', '.join(result_data['semantic_fields']) if result_data['semantic_fields'] else 'None'}\n\n"
                                                f"**Duration:** {result_data['duration_seconds']}s"
                                            )
                                        elif incomplete_indexing and result_data['documents_indexed'] == 0:
                                            st.error(
                                                f"❌ Indexing failed: No documents were indexed\n\n"
                                                f"This usually indicates a connection issue or mapping error. "
                                                f"Check your Elasticsearch connection and try again."
                                            )
                                        elif incomplete_indexing:
                                            st.warning(
                                                f"⚠️ Partial indexing\n\n"
                                                f"**Indexed:** {result_data['documents_indexed']:,} / {result_data['total_docs']:,} documents\n\n"
                                                f"**Index:** {result_data['index_name']} ({result_data['index_type']})\n\n"
                                                f"**Semantic fields:** {', '.join(result_data['semantic_fields']) if result_data['semantic_fields'] else 'None'}\n\n"
                                                f"**Duration:** {result_data['duration_seconds']}s"
                                            )
                                        else:
                                            st.success(
                                                f"✅ Indexed {result_data['documents_indexed']:,} documents\n\n"
                                                f"**Index:** {result_data['index_name']} ({result_data['index_type']})\n\n"
                                                f"**Semantic fields:** {', '.join(result_data['semantic_fields']) if result_data['semantic_fields'] else 'None'}\n\n"
                                                f"**Duration:** {result_data['duration_seconds']}s"
                                            )
                                    else:
                                        st.error(f"❌ Indexing failed:\n{chr(10).join(result_data['errors'])}")

                                # Show semantic fields info if specified
                                if name in semantic_fields_spec and semantic_fields_spec[name]:
                                    st.info(f"🧠 **Semantic fields:** {', '.join(semantic_fields_spec[name])}")

                                # Show data profile summary if profile button was clicked
                                if st.session_state.get(f"show_profile_{name}", False):
                                    data_profile = load_demo_data_profile(st.session_state.current_demo_module)
                                    if data_profile and name in data_profile.get('datasets', {}):
                                        dataset_profile = data_profile['datasets'][name]

                                        st.markdown("#### 📊 Data Profile Summary")

                                        # Overview metrics
                                        col_a, col_b, col_c = st.columns(3)
                                        with col_a:
                                            st.metric("Total Records", f"{dataset_profile.get('total_records', 0):,}")
                                        with col_b:
                                            st.metric("Total Fields", len(dataset_profile.get('fields', {})))
                                        with col_c:
                                            # Count numeric vs text fields
                                            fields = dataset_profile.get('fields', {})
                                            numeric_count = sum(1 for f in fields.values() if f.get('type') in ['int64', 'float64', 'number'])
                                            st.metric("Numeric Fields", numeric_count)

                                        st.markdown("**Field Details:**")

                                        # Display field information in a clean format
                                        for field_name, field_info in dataset_profile.get('fields', {}).items():
                                            field_type = field_info.get('type', 'unknown')

                                            with st.expander(f"🔹 {field_name} ({field_type})"):
                                                # Show unique value count or range
                                                if 'unique_values' in field_info:
                                                    unique_vals = field_info['unique_values']
                                                    if field_info.get('truncated', False):
                                                        st.caption(f"📝 Sample values (showing {len(unique_vals)} of many):")
                                                    else:
                                                        st.caption(f"📝 All unique values ({len(unique_vals)}):")

                                                    # Show first 10 values in columns
                                                    display_vals = unique_vals[:10]
                                                    if len(display_vals) <= 5:
                                                        for val in display_vals:
                                                            st.code(str(val), language=None)
                                                    else:
                                                        col_left, col_right = st.columns(2)
                                                        mid = len(display_vals) // 2
                                                        with col_left:
                                                            for val in display_vals[:mid]:
                                                                st.code(str(val), language=None)
                                                        with col_right:
                                                            for val in display_vals[mid:]:
                                                                st.code(str(val), language=None)

                                                    if len(unique_vals) > 10:
                                                        st.caption(f"... and {len(unique_vals) - 10} more values")

                                                elif 'range' in field_info:
                                                    range_info = field_info['range']
                                                    st.caption(f"📊 Range: {range_info.get('min', 'N/A')} to {range_info.get('max', 'N/A')}")
                                                    if 'mean' in range_info:
                                                        st.caption(f"📈 Mean: {range_info['mean']:.2f}")
                                    else:
                                        st.warning(f"No data profile found for dataset '{name}'")

                                # Show data if view button was clicked
                                if st.session_state.get(f"show_data_{name}", False):
                                    st.dataframe(df.head(100), use_container_width=True)
                                    st.caption(f"Showing first 100 of {len(df)} rows")
                                else:
                                    st.caption(f"Total rows: {len(df)} | Columns: {len(df.columns)}")

                                st.divider()
                        else:
                            st.info("No datasets found. Try regenerating assets from the Config tab.")
                    except Exception as e:
                        st.error(f"Error loading data: {e}")
                        st.info("Try clicking 'Generate Assets' in the Config tab.")
                else:
                    st.info("📋 Click 'Generate Assets' in the Config tab to view datasets")

            with tabs[2]:
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
                                                            import anthropic
                                                            import os
                                                            import json
                                                            from pathlib import Path

                                                            # Get LLM client
                                                            llm_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

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

            with tabs[3]:
                # Only load if assets have been generated
                if st.session_state.get("assets_generated", False):
                    try:
                        guide = load_demo_guide(st.session_state.current_demo_module)
                        if guide:
                            st.markdown(guide)
                        else:
                            st.info("No demo guide found. Try regenerating assets from the Config tab.")
                    except Exception as e:
                        st.error(f"Error loading guide: {e}")
                        st.info("Try clicking 'Generate Assets' in the Config tab.")
                else:
                    st.info("📋 Click 'Generate Assets' in the Config tab to view the demo guide")

            with tabs[4]:
                # Load and display conversation history
                st.markdown("### Original Conversation")
                st.markdown("This is the conversation that led to the creation of this demo.")

                conversation_file = loader.module_path / 'conversation.json'
                if conversation_file.exists():
                    try:
                        import json
                        with open(conversation_file, 'r') as f:
                            conversation_data = json.load(f)

                        messages = conversation_data.get('messages', [])

                        if messages:
                            st.markdown(f"**Generated:** {conversation_data.get('timestamp', 'Unknown')}")
                            st.divider()

                            # Display messages in chat format
                            for msg in messages:
                                role = msg.get('role', 'unknown')
                                content = msg.get('content', '')

                                if role == 'user':
                                    with st.chat_message("user"):
                                        st.markdown(content)
                                elif role == 'assistant':
                                    with st.chat_message("assistant"):
                                        st.markdown(content)
                        else:
                            st.info("No conversation messages found.")
                    except Exception as e:
                        st.error(f"Error loading conversation: {e}")
                        st.code(str(e))
                else:
                    st.info("💬 No conversation history found for this demo. This feature was added in a recent update.")

            with tabs[5]:  # Agents & Tools tab
                # Import necessary services
                from src.services.agent_builder_service import AgentBuilderService
                from src.services.query_validation_service import QueryValidationService

                # Initialize services
                validation_service = QueryValidationService(loader.module_path)

                # Create sub-tabs for Tools and Agents
                agent_tabs = st.tabs(["🔧 Tools", "🤖 Agents"])

                with agent_tabs[0]:  # Tools tab
                    st.markdown("### Tool Management")

                    # Initialize Agent Builder service
                    try:
                        agent_builder = AgentBuilderService()
                        connection_valid = agent_builder.validate_connection()

                        if not connection_valid['success']:
                            st.error(f"❌ Cannot connect to Agent Builder API: {connection_valid.get('error', 'Unknown error')}")
                            st.info("Please check your ELASTICSEARCH_KIBANA_URL and ELASTICSEARCH_API_KEY environment variables.")
                            st.stop()
                    except Exception as e:
                        st.error(f"❌ Agent Builder Service not configured: {e}")
                        st.info("Please set ELASTICSEARCH_KIBANA_URL and ELASTICSEARCH_API_KEY in your .env file")
                        st.stop()

                    # Section 1: Deployed Tools
                    st.markdown("#### 📤 Deployed Tools")

                    # Get list of deployed tools from API
                    deployed_response = agent_builder.list_tools()

                    if 'error' in deployed_response:
                        st.warning(f"Could not fetch deployed tools: {deployed_response['error']}")
                        deployed_tools = []
                    else:
                        # Get tools that belong to this demo
                        all_tools = deployed_response.get('tools', [])
                        # Extract the company_department prefix for filtering
                        module_prefix = get_module_prefix(st.session_state.current_demo_module)
                        st.caption(f"Filtering tools with prefix: `{module_prefix}*`")
                        deployed_tools = [t for t in all_tools if t.get('id', '').startswith(module_prefix)]

                    if deployed_tools:
                        for tool in deployed_tools:
                            with st.expander(f"🔧 {tool.get('name', tool.get('id', 'Unknown'))}"):
                                col1, col2 = st.columns([3, 1])

                                with col1:
                                    st.json(tool)

                                with col2:
                                    # View details button
                                    if st.button("👁️ View", key=f"view_tool_{tool['id']}", use_container_width=True):
                                        details = agent_builder.get_tool(tool['id'])
                                        if 'error' not in details:
                                            st.session_state[f"tool_details_{tool['id']}"] = details

                                    # Delete button
                                    if st.button("🗑️ Delete", key=f"delete_tool_{tool['id']}", use_container_width=True):
                                        result = agent_builder.delete_tool(tool['id'])
                                        if result.get('success'):
                                            st.success(f"Deleted tool: {tool['id']}")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to delete: {result.get('error')}")

                                # Show details if fetched
                                if f"tool_details_{tool['id']}" in st.session_state:
                                    st.markdown("##### Tool Details")
                                    st.json(st.session_state[f"tool_details_{tool['id']}"])
                    else:
                        st.info("No tools deployed for this demo yet.")

                    st.divider()

                    # Section 2: Tool Candidates
                    st.markdown("#### 🎯 Tool Candidates")
                    st.caption("Validated queries from this module ready for deployment as Agent Builder tools")

                    # Load queries for this specific module
                    try:
                        queries_dict = load_demo_queries(st.session_state.current_demo_module)
                        all_queries = []

                        # Combine all query types with their metadata
                        for query_type in ['scripted', 'parameterized', 'rag']:
                            for i, query in enumerate(queries_dict.get(query_type, []), 1):
                                query_id = f"{query_type}_query_{i}"
                                # Only check if validated in this module's validation service
                                if validation_service.is_query_validated(query_id):
                                    all_queries.append({
                                        'query_id': query_id,
                                        'query': query,
                                        'type': query_type,
                                        'is_deployed': validation_service.is_tool_deployed(query_id),
                                        'metadata': validation_service.get_tool_metadata(query_id) or query.get('tool_metadata')
                                    })

                        # Separate deployed and undeployed
                        undeployed_queries = [q for q in all_queries if not q['is_deployed']]
                        already_deployed = [q for q in all_queries if q['is_deployed']]

                        if undeployed_queries:
                            st.success(f"Found {len(undeployed_queries)} validated queries ready for deployment")

                            for candidate in undeployed_queries:
                                query_id = candidate['query_id']
                                query = candidate['query']
                                metadata = candidate['metadata']

                                # Create badge for query type
                                type_badge = {
                                    'scripted': '📊 SCRIPTED',
                                    'parameterized': '🔧 PARAMETERIZED',
                                    'rag': '🤖 RAG'
                                }.get(candidate['type'], '❓ ' + candidate['type'].upper())

                                # Use query name or fallback to query_id
                                query_name = query.get('name', query_id)

                                with st.expander(f"{type_badge} | {query_name}", expanded=False):
                                    # Show query type and description
                                    col1, col2 = st.columns([1, 3])
                                    with col1:
                                        # Display query type as a colored badge
                                        if candidate['type'] == 'scripted':
                                            st.info(f"**Type:** SCRIPTED")
                                        elif candidate['type'] == 'parameterized':
                                            st.warning(f"**Type:** PARAMETERIZED")
                                        elif candidate['type'] == 'rag':
                                            st.success(f"**Type:** RAG")
                                        else:
                                            st.markdown(f"**Type:** {candidate['type'].upper()}")

                                    with col2:
                                        if query.get('description'):
                                            st.markdown(f"**Description:** {query['description']}")

                                    # Tool metadata form
                                    st.markdown("##### Tool Configuration")

                                    # Check if metadata already exists (from saved or pre-generated)
                                    # Priority: 1) Saved metadata, 2) Pre-generated from query, 3) Defaults
                                    if metadata:
                                        tool_id = metadata.get('tool_id', f"{st.session_state.current_demo_module}_{query_id}")
                                        tool_description = metadata.get('description', query.get('description', ''))
                                        tool_tags = metadata.get('tags', [])
                                    elif query.get('tool_metadata'):
                                        # Use pre-generated tool metadata from query module
                                        pre_gen = query['tool_metadata']
                                        tool_id = pre_gen.get('tool_id', f"{st.session_state.current_demo_module}_{query_id}")
                                        tool_description = pre_gen.get('description', query.get('description', ''))
                                        tool_tags = pre_gen.get('tags', [])
                                    else:
                                        # Fallback defaults
                                        tool_id = f"{st.session_state.current_demo_module}_{query_id}"
                                        tool_description = query.get('description', '')
                                        tool_tags = []

                                    # Input fields for tool metadata (removed name field)
                                    new_tool_id = st.text_input(
                                        "Tool ID",
                                        value=tool_id,
                                        key=f"tool_id_{query_id}",
                                        help="Unique identifier for the tool in Agent Builder (e.g., company_dept_purpose)"
                                    )

                                    new_tool_description = st.text_area(
                                        "Tool Description",
                                        value=tool_description,
                                        key=f"tool_desc_{query_id}",
                                        height=100,
                                        help="First ~50 chars appear in tool list. Start with a brief summary, then explain when to use it."
                                    )

                                    # Tags input
                                    tags_str = st.text_input(
                                        "Tags (comma-separated)",
                                        value=", ".join(tool_tags) if tool_tags else "",
                                        key=f"tool_tags_{query_id}",
                                        help="Tags to categorize the tool"
                                    )
                                    new_tool_tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []

                                    # Info message if using pre-generated metadata
                                    if query.get('tool_metadata') and not metadata:
                                        st.info("ℹ️ Using pre-generated tool metadata from query module. You can edit these values before saving.")

                                    # API Call Preview Section
                                    with st.expander("🔍 Preview API Call", expanded=False):
                                        st.markdown("##### API Payload Preview")
                                        st.caption("This is what will be sent to the Kibana Agent Builder API")

                                        # Build the API payload based on current form values
                                        api_payload = {
                                            "id": new_tool_id,
                                            "type": "esql",
                                            "description": new_tool_description,
                                            "tags": new_tool_tags,
                                            "configuration": {
                                                "query": display._get_query_text(query)
                                            }
                                        }

                                        # Add parameters if this is a parameterized or RAG query
                                        if candidate['type'] in ['parameterized', 'rag'] and query.get('parameters'):
                                            # Extract parameter definitions from query
                                            params = {}
                                            for param in query['parameters']:
                                                if isinstance(param, dict):
                                                    param_name = param.get('name', '')
                                                    if param_name:
                                                        params[param_name] = {
                                                            "type": param.get('type', 'text'),
                                                            "description": param.get('description', ''),
                                                            "required": param.get('required', True)
                                                        }
                                                        if 'default' in param:
                                                            params[param_name]['default'] = param['default']
                                                        if 'example' in param:
                                                            params[param_name]['example'] = param['example']
                                            if params:
                                                api_payload['configuration']['params'] = params

                                        # Display the payload as JSON
                                        st.json(api_payload)

                                        # Show the API endpoint
                                        st.markdown("##### API Endpoint")
                                        st.code(f"POST {os.getenv('ELASTICSEARCH_KIBANA_URL', '<KIBANA_URL>')}/api/agent_builder/tools", language="bash")

                                        # Show curl command
                                        st.markdown("##### Example cURL Command")
                                        curl_command = f"""curl -X POST \\
  "{os.getenv('ELASTICSEARCH_KIBANA_URL', '<KIBANA_URL>')}/api/agent_builder/tools" \\
  -H "Authorization: ApiKey ${{API_KEY}}" \\
  -H "Content-Type: application/json" \\
  -H "kbn-xsrf: true" \\
  -d '{json.dumps(api_payload, indent=2)}'"""
                                        st.code(curl_command, language="bash")

                                    # Save metadata button
                                    col_save, col_deploy = st.columns(2)

                                    with col_save:
                                        if st.button("💾 Save Metadata", key=f"save_{query_id}", use_container_width=True):
                                            # Save the metadata (removed name field)
                                            new_metadata = {
                                                'tool_id': new_tool_id,
                                                'description': new_tool_description,
                                                'tags': new_tool_tags,
                                                'query': display._get_query_text(query),
                                                'query_type': candidate['type']
                                            }

                                            # Extract parameters if present
                                            if query.get('parameters'):
                                                new_metadata['parameters'] = query['parameters']

                                            validation_service.save_tool_metadata(query_id, new_metadata)
                                            st.success("Metadata saved!")
                                            st.rerun()

                                    with col_deploy:
                                        # Check if ready for deployment
                                        is_ready = validation_service.is_tool_ready_for_deployment(query_id)

                                        if is_ready:
                                            if st.button("🚀 Deploy Tool", key=f"deploy_{query_id}",
                                                        use_container_width=True, type="primary"):
                                                with st.spinner("Deploying tool to Agent Builder..."):
                                                    try:
                                                        # Get the full metadata
                                                        deploy_metadata = validation_service.get_tool_metadata(query_id)

                                                        # Create tool configuration
                                                        tool_config = {
                                                            'id': deploy_metadata['tool_id'],
                                                            'type': 'esql',
                                                            'description': deploy_metadata['description'],
                                                            'tags': deploy_metadata.get('tags', []),
                                                            'query': deploy_metadata['query']
                                                        }

                                                        # Extract parameters from query
                                                        params = agent_builder.extract_esql_parameters(deploy_metadata['query'])
                                                        if params:
                                                            tool_config['params'] = params

                                                        # Deploy the tool
                                                        result = agent_builder.create_tool(tool_config)

                                                        if result.get('success'):
                                                            validation_service.mark_tool_deployed(query_id, deploy_metadata['tool_id'])
                                                            st.success(f"✅ Tool deployed successfully: {deploy_metadata['tool_id']}")
                                                            st.balloons()
                                                            st.rerun()
                                                        else:
                                                            st.error(f"❌ Deployment failed: {result.get('error')}")

                                                    except Exception as e:
                                                        st.error(f"❌ Error during deployment: {e}")
                                        else:
                                            st.warning("Please fill in all required fields before deploying")

                        # Show already deployed queries at the bottom
                        if already_deployed:
                            with st.expander(f"✅ Already Deployed ({len(already_deployed)})", expanded=False):
                                for deployed in already_deployed:
                                    deployed_tool_id = validation_service.get_deployed_tool_id(deployed['query_id'])
                                    st.success(f"• {deployed['query'].get('name', deployed['query_id'])} → {deployed_tool_id}")

                        if not undeployed_queries and not already_deployed:
                            st.info("No validated queries found. Go to the Queries tab and validate queries after testing them.")

                    except Exception as e:
                        st.error(f"Error loading queries: {e}")
                        import traceback
                        st.code(traceback.format_exc())

                with agent_tabs[1]:  # Agents tab
                    st.markdown("### Agent Management")

                    # Load agent metadata from module if it exists
                    agent_metadata_path = os.path.join(
                        "demos",
                        st.session_state.current_demo_module,
                        "agent_metadata.json"
                    )

                    agent_metadata = None
                    if os.path.exists(agent_metadata_path):
                        try:
                            with open(agent_metadata_path, 'r') as f:
                                agent_metadata = json.load(f)
                        except Exception as e:
                            st.error(f"Error loading agent metadata: {e}")

                    if not agent_metadata:
                        st.warning("No agent metadata found for this demo. Agent metadata is generated automatically for new demos.")
                        st.info("To add agent metadata to older demos, regenerate the demo module.")
                        return

                    # Section 1: Deployed Agents
                    st.markdown("#### 🤖 Deployed Agents")

                    # Check connection
                    if not agent_builder.validate_connection():
                        st.error("❌ Cannot connect to Elastic Agent Builder. Please check your environment variables.")
                        return

                    # List all agents
                    all_agents_response = agent_builder.list_agents()
                    if 'error' in all_agents_response:
                        st.error(f"Error listing agents: {all_agents_response['error']}")
                        deployed_agents = []
                    else:
                        all_agents = all_agents_response.get('agents', [])
                        # Filter for agents matching this demo
                        # Use both exact match (for the main agent) and prefix match
                        agent_id = agent_metadata.get('id', 'unknown')
                        module_prefix = get_module_prefix(st.session_state.current_demo_module)
                        st.caption(f"Filtering agents matching: `{agent_id}` or prefix: `{module_prefix}*`")
                        deployed_agents = [a for a in all_agents
                                         if a.get('id', '') == agent_id or
                                         a.get('id', '').startswith(module_prefix)]

                    if deployed_agents:
                        for agent in deployed_agents:
                            with st.expander(f"🤖 {agent.get('name', agent.get('id', 'Unknown'))}"):
                                # Get current tools assigned to this agent
                                agent_tools = agent.get('configuration', {}).get('tools', [])
                                current_tool_ids = []
                                if agent_tools and isinstance(agent_tools, list) and len(agent_tools) > 0:
                                    if isinstance(agent_tools[0], dict):
                                        current_tool_ids = agent_tools[0].get('tool_ids', [])

                                # Show current tools
                                st.markdown("##### 🛠️ Currently Assigned Tools")
                                if current_tool_ids:
                                    for tool_id in current_tool_ids:
                                        st.text(f"• {tool_id}")
                                else:
                                    st.info("No tools currently assigned")

                                st.divider()

                                # Tool assignment section
                                st.markdown("##### ➕ Manage Tool Assignment")

                                # Get available tools
                                # 1. Module-specific tools
                                module_tools = [t for t in all_tools if t.get('id', '').startswith(module_prefix)]
                                module_tool_ids = [t['id'] for t in module_tools]

                                # 2. Platform tools
                                platform_tools = [t for t in all_tools if t.get('id', '').startswith('platform.')]
                                platform_tool_ids = [t['id'] for t in platform_tools]

                                # Combine all available tools
                                all_available_ids = []
                                if module_tool_ids:
                                    all_available_ids.extend(module_tool_ids)
                                if platform_tool_ids:
                                    all_available_ids.extend(platform_tool_ids)

                                if all_available_ids:
                                    with st.form(f"tool_assignment_{agent['id']}"):
                                        st.markdown("**Select tools to assign:**")

                                        # Multi-select with sections
                                        selected_tools = []

                                        # Module tools section
                                        if module_tool_ids:
                                            st.caption("📦 Module-specific tools:")
                                            for tool_id in module_tool_ids:
                                                checked = st.checkbox(
                                                    tool_id,
                                                    value=tool_id in current_tool_ids,
                                                    key=f"check_{agent['id']}_{tool_id}"
                                                )
                                                if checked:
                                                    selected_tools.append(tool_id)

                                        # Platform tools section
                                        if platform_tool_ids:
                                            st.caption("🌐 Platform tools:")
                                            for tool_id in platform_tool_ids:
                                                checked = st.checkbox(
                                                    tool_id,
                                                    value=tool_id in current_tool_ids,
                                                    key=f"check_{agent['id']}_{tool_id}"
                                                )
                                                if checked:
                                                    selected_tools.append(tool_id)

                                        # Update button
                                        if st.form_submit_button("🔄 Update Tools", use_container_width=True):
                                            with st.spinner("Updating agent tools..."):
                                                # Update agent with new tools
                                                update_config = {
                                                    'name': agent.get('name'),
                                                    'description': agent.get('description'),
                                                    'labels': agent.get('labels', []),
                                                    'avatar_color': agent.get('avatar_color'),
                                                    'avatar_symbol': agent.get('avatar_symbol'),
                                                    'instructions': agent.get('configuration', {}).get('instructions', ''),
                                                    'configuration': {
                                                        'instructions': agent.get('configuration', {}).get('instructions', ''),
                                                        'tools': [{'tool_ids': selected_tools}] if selected_tools else []
                                                    }
                                                }

                                                result = agent_builder.update_agent(agent['id'], update_config)
                                                if result.get('success'):
                                                    st.success(f"✅ Tools updated for agent: {agent['id']}")
                                                    st.rerun()
                                                else:
                                                    st.error(f"❌ Failed to update tools: {result.get('error')}")
                                else:
                                    st.warning("No tools available to assign. Deploy some tools first!")

                                st.divider()

                                # Actions
                                col1, col2 = st.columns(2)
                                with col1:
                                    # View details button
                                    if st.button("👁️ View Raw JSON", key=f"view_agent_{agent['id']}", use_container_width=True):
                                        st.session_state[f"show_json_{agent['id']}"] = not st.session_state.get(f"show_json_{agent['id']}", False)

                                with col2:
                                    # Delete button
                                    if st.button("🗑️ Delete Agent", key=f"delete_agent_{agent['id']}", use_container_width=True):
                                        result = agent_builder.delete_agent(agent['id'])
                                        if result.get('success'):
                                            st.success(f"Deleted agent: {agent['id']}")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to delete: {result.get('error')}")

                                # Show JSON if toggled
                                if st.session_state.get(f"show_json_{agent['id']}"):
                                    st.markdown("##### Raw Agent JSON")
                                    st.json(agent)
                    else:
                        st.info("No agents deployed for this demo yet.")

                    st.divider()

                    # Section 2: Agent Configuration
                    st.markdown("#### 🎯 Agent Configuration")
                    st.caption("Configure and deploy your agent to Elastic Agent Builder")

                    # Agent configuration form
                    with st.form("agent_config_form"):
                        # Pre-fill with metadata from module
                        agent_id = st.text_input(
                            "Agent ID",
                            value=agent_metadata.get('id', ''),
                            help="Unique identifier for the agent (lowercase, no spaces)"
                        )

                        agent_name = st.text_input(
                            "Agent Name",
                            value=agent_metadata.get('name', ''),
                            help="Display name for the agent"
                        )

                        agent_description = st.text_area(
                            "Agent Description",
                            value=agent_metadata.get('description', ''),
                            height=100,
                            help="Brief description shown to users"
                        )

                        # Avatar customization
                        col1, col2 = st.columns(2)
                        with col1:
                            avatar_symbol = st.text_input(
                                "Avatar Symbol",
                                value=agent_metadata.get('avatar_symbol', 'AI'),
                                max_chars=2,
                                help="1-2 letter symbol for the avatar"
                            )

                        with col2:
                            avatar_color = st.color_picker(
                                "Avatar Color",
                                value=agent_metadata.get('avatar_color', '#3B82F6')
                            )

                        # Labels
                        labels_str = st.text_input(
                            "Labels (comma-separated)",
                            value=", ".join(agent_metadata.get('labels', [])),
                            help="Tags for categorizing the agent"
                        )
                        agent_labels = [l.strip() for l in labels_str.split(',') if l.strip()]

                        # Instructions
                        agent_instructions = st.text_area(
                            "Agent Instructions",
                            value=agent_metadata.get('configuration', {}).get('instructions', ''),
                            height=200,
                            help="System prompt/instructions for the agent"
                        )

                        # Form actions
                        col_save, col_deploy = st.columns(2)

                        with col_save:
                            if st.form_submit_button("💾 Save Configuration", use_container_width=True):
                                # Update agent metadata in the file
                                updated_metadata = {
                                    "id": agent_id,
                                    "name": agent_name,
                                    "description": agent_description,
                                    "labels": agent_labels,
                                    "avatar_color": avatar_color,
                                    "avatar_symbol": avatar_symbol,
                                    "configuration": {
                                        "instructions": agent_instructions,
                                        "tools": []  # Tools will be managed separately
                                    }
                                }

                                try:
                                    with open(agent_metadata_path, 'w') as f:
                                        json.dump(updated_metadata, f, indent=2)
                                    st.success("✅ Agent configuration saved locally!")
                                except Exception as e:
                                    st.error(f"Failed to save configuration: {e}")

                        with col_deploy:
                            if st.form_submit_button("🚀 Deploy Agent", use_container_width=True, type="primary"):
                                if not all([agent_id, agent_name, agent_description, agent_instructions]):
                                    st.error("Please fill in all required fields")
                                else:
                                    with st.spinner("Deploying agent to Elastic Agent Builder..."):
                                        # Check if agent exists
                                        existing = [a for a in deployed_agents if a.get('id') == agent_id]

                                        if existing:
                                            # Update existing agent
                                            result = agent_builder.update_agent(agent_id, {
                                                'name': agent_name,
                                                'description': agent_description,
                                                'labels': agent_labels,
                                                'avatar_color': avatar_color,
                                                'avatar_symbol': avatar_symbol,
                                                'instructions': agent_instructions
                                            })
                                            if result.get('success'):
                                                st.success(f"✅ Agent updated successfully: {agent_id}")
                                            else:
                                                st.error(f"❌ Update failed: {result.get('error')}")
                                        else:
                                            # Create new agent
                                            result = agent_builder.create_agent({
                                                'id': agent_id,
                                                'name': agent_name,
                                                'description': agent_description,
                                                'labels': agent_labels,
                                                'avatar_color': avatar_color,
                                                'avatar_symbol': avatar_symbol,
                                                'instructions': agent_instructions,
                                                'tool_ids': []  # Start with no tools
                                            })
                                            if result.get('success'):
                                                st.success(f"✅ Agent deployed successfully: {agent_id}")
                                                st.balloons()
                                            else:
                                                st.error(f"❌ Deployment failed: {result.get('error')}")

                                        # Refresh to show new status
                                        if result.get('success'):
                                            st.rerun()


    else:
        st.info("👈 Select a demo from the sidebar to view details")

