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


def render_browse_demos_view():
    """Render the demo browsing interface - demo details only (list is in sidebar)"""
    # Show details if a module is selected
    if st.session_state.current_demo_module:
        st.title(f"📊 {st.session_state.current_demo_module}")

        manager = DemoModuleManager()
        loader = manager.get_module(st.session_state.current_demo_module)

        if loader:
            tabs = st.tabs(["📋 Config", "🗂️ Data", "🔍 Queries", "📝 Guide", "💬 Conversation"])

            with tabs[0]:
                st.markdown("### Generate Demo Assets")
                st.info("⚠️ **Generation may take 5-20 minutes** — Page will appear frozen. Data: 80-90% | Queries: 5-10% | Guide: 5-10%")

                if st.button("🚀 Generate Assets", use_container_width=True):
                    with st.spinner("Generating demo assets..."):
                        try:
                            # Force regeneration by clearing cache and loading
                            load_demo_datasets.clear()
                            load_demo_queries.clear()
                            load_demo_guide.clear()

                            # Generate all assets
                            datasets = load_demo_datasets(st.session_state.current_demo_module)
                            queries = load_demo_queries(st.session_state.current_demo_module)
                            guide = load_demo_guide(st.session_state.current_demo_module)

                            # Mark assets as generated
                            st.session_state.assets_generated = True

                            st.success(f"✅ Generated {len(datasets)} datasets, {len(queries)} queries, and demo guide!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error generating assets: {e}")
                            import traceback
                            st.code(traceback.format_exc())

                st.divider()
                st.markdown("### Demo Configuration")
                st.json(loader.config)

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
                                col1, col2, col3 = st.columns(3)

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

                        # Helper function to render queries using the new display module
                        def render_query_list(queries, query_type, can_execute=True):
                            if queries:
                                for i, query in enumerate(queries, 1):
                                    # Use the new QueryResultsDisplay for clean rendering
                                    display.render_query_with_results(
                                        query,
                                        results=None,  # No results by default - clean queries only
                                        show_pipeline_view=False  # Don't show educational view by default
                                    )

                                    # Add execution capability for scripted, parameterized, and RAG queries
                                    if can_execute and query_type in ['scripted', 'parameterized', 'rag']:
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
                                                                            st.rerun()

                                                                # Show generated suggestion
                                                                if f"{suggest_key}_value" in st.session_state:
                                                                    st.code(st.session_state[f"{suggest_key}_value"], language=None)
                                                            st.divider()

                                                param_values = display._render_parameter_inputs(
                                                    query['parameters'],
                                                    unique_key=query_key
                                                )

                                                # Test button
                                                if st.button("▶️ Test with These Parameters", key=f"test_{query_key}", use_container_width=True):
                                                    from src.services.elasticsearch_indexer import ElasticsearchIndexer
                                                    query_name = query.get('name', f'Query {i}')

                                                    with st.spinner(f"Executing {query_name}..."):
                                                        try:
                                                            # Substitute parameters into query
                                                            query_text = display._get_query_text(query)
                                                            substituted_query = display.substitute_parameters(query_text, param_values)

                                                            # Execute
                                                            indexer = ElasticsearchIndexer()
                                                            success, result, error = indexer.execute_esql(substituted_query)

                                                            if success:
                                                                st.success("✅ Query executed successfully!")
                                                                # Store results and substituted query
                                                                st.session_state[f"{query_key}_results"] = result
                                                                st.session_state[f"{query_key}_substituted"] = substituted_query
                                                                st.rerun()
                                                            else:
                                                                st.error(f"❌ Query failed: {error}")
                                                        except Exception as e:
                                                            st.error(f"❌ Error: {e}")

                                        # For scripted queries, simple test button
                                        elif query_type == 'scripted':
                                            col1, col2 = st.columns([1, 3])
                                            with col1:
                                                if st.button("▶️ Test Query", key=f"test_{query_key}", use_container_width=True):
                                                    from src.services.elasticsearch_indexer import ElasticsearchIndexer
                                                    query_name = query.get('name', f'Query {i}')

                                                    with st.spinner(f"Executing {query_name}..."):
                                                        try:
                                                            indexer = ElasticsearchIndexer()
                                                            query_text = display._get_query_text(query)
                                                            success, result, error = indexer.execute_esql(query_text)

                                                            if success:
                                                                st.success("✅ Query executed successfully!")
                                                                # Store results in session state for display
                                                                st.session_state[f"{query_key}_results"] = result
                                                                st.rerun()
                                                            else:
                                                                st.error(f"❌ Query failed: {error}")
                                                        except Exception as e:
                                                            st.error(f"❌ Error: {e}")

                                        # Display substituted query if available (for parameterized)
                                        if f"{query_key}_substituted" in st.session_state:
                                            with st.expander("📝 Executed Query (with parameters)", expanded=False):
                                                st.code(st.session_state[f"{query_key}_substituted"], language='sql')

                                        # Display results if available in session state
                                        if f"{query_key}_results" in st.session_state:
                                            with st.expander("📊 Query Results", expanded=True):
                                                display._render_query_results(st.session_state[f"{query_key}_results"], unique_key=query_key)

                                            # Check if query returned zero results - offer optimization
                                            results = st.session_state[f"{query_key}_results"]
                                            if (query_type == 'scripted' and results and
                                                'columns' in results and 'values' in results and
                                                len(results['values']) == 0):

                                                # Show optimize button for zero-results queries
                                                optimize_key = f"{query_key}_optimize"
                                                if st.button("🔧 Optimize Constraints", key=optimize_key, help="Use LLM to relax constraints and improve results"):
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

    else:
        st.info("👈 Select a demo from the sidebar to view details")

