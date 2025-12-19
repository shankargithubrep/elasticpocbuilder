"""
Data Tab - Displays demo datasets with download, indexing, and profiling capabilities.
"""

import streamlit as st
import logging
from pathlib import Path
import json

from src.framework import DemoModuleManager
from src.ui.data_loaders import (
    load_demo_datasets,
    load_demo_data_profile
)
from src.ui.components.progress_tracker import get_progress_service

logger = logging.getLogger(__name__)


def render_data_tab():
    """Render the Data tab content."""
    # Section guidance
    st.info("📊 **Index your datasets** to Elasticsearch so queries can run against real data. Click 'Index All Datasets' to complete this step. *Need help? Use the Help feature in the sidebar.*")

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

            # Load index_mode mapping and text_fields from query_strategy.json
            index_mode_map = {}
            text_fields_map = {}  # Fields needing 'text' type for MATCH queries
            try:
                strategy_path = Path('demos') / st.session_state.current_demo_module / 'query_strategy.json'
                if strategy_path.exists():
                    with open(strategy_path, 'r') as f:
                        query_strategy = json.load(f)

                        # Load text_fields (extracted from MATCH queries)
                        text_fields_map = query_strategy.get('text_fields', {})
                        if text_fields_map:
                            logger.info(f"Loaded text fields for MATCH queries: {text_fields_map}")

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
                logging.warning(f"Could not load index_mode mapping: {e}")

            if datasets:
                # Index All button at the top
                if st.button("📤 Index All Datasets", use_container_width=True, type="primary"):
                    from src.services.elasticsearch_indexer import ElasticsearchIndexer

                    st.info(f"Starting batch indexing for {len(datasets)} datasets...")

                    indexer = ElasticsearchIndexer()
                    batch_results = {}  # Track success/failure per dataset
                    for idx, (name, df) in enumerate(datasets.items(), 1):
                        st.markdown(f"**[{idx}/{len(datasets)}] Indexing {name}...**")

                        # Get semantic fields for this dataset
                        semantic_fields = semantic_fields_spec.get(name, [])

                        # Get text fields for this dataset (for MATCH queries)
                        text_fields = text_fields_map.get(name, [])

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
                                text_fields=text_fields,
                                index_mode=index_mode,
                                progress_callback=progress_callback
                            )

                            if result.success:
                                st.success(f"✅ {name}: {result.documents_indexed:,} docs indexed in {result.duration_seconds}s")
                                batch_results[name] = {"success": True}
                            else:
                                st.error(f"❌ {name}: Indexing failed")
                                batch_results[name] = {"success": False, "error": "Indexing failed"}
                        except Exception as e:
                            st.error(f"❌ {name}: {str(e)}")
                            batch_results[name] = {"success": False, "error": str(e)}

                    # Update progress tracking with per-dataset status
                    try:
                        progress_service = get_progress_service(st.session_state.current_demo_module)
                        all_success = True
                        for name, result in batch_results.items():
                            progress_service.mark_dataset_indexed(
                                name,
                                success=result["success"],
                                error=result.get("error")
                            )
                            if not result["success"]:
                                all_success = False

                        # Only mark data_indexed if ALL datasets succeeded
                        if all_success and len(batch_results) == len(datasets):
                            progress_service.mark_data_indexed()
                            st.success("🎉 Batch indexing complete!")
                        else:
                            failed_count = sum(1 for r in batch_results.values() if not r["success"])
                            st.warning(f"⚠️ Batch indexing finished with {failed_count} failure(s)")
                    except Exception as e:
                        logger.warning(f"Could not update progress tracking: {e}")

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

                            # Get text fields for this dataset (for MATCH queries)
                            text_fields = text_fields_map.get(name, [])

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
                                    text_fields=text_fields,
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
                                # Track successful indexing
                                try:
                                    progress_service = get_progress_service(st.session_state.current_demo_module)
                                    progress_service.mark_dataset_indexed(name, success=True)
                                except Exception as e:
                                    logger.warning(f"Could not update progress tracking: {e}")
                        else:
                            st.error(f"❌ Indexing failed:\n{chr(10).join(result_data['errors'])}")
                            # Track failed indexing
                            try:
                                progress_service = get_progress_service(st.session_state.current_demo_module)
                                progress_service.mark_dataset_indexed(name, success=False, error=chr(10).join(result_data['errors']))
                            except Exception as e:
                                logger.warning(f"Could not update progress tracking: {e}")

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
