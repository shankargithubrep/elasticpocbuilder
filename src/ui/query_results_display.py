"""
Query Results Display Module
Handles visualization of actual ES|QL query results from Elasticsearch
"""

from typing import Dict, List, Any, Optional, Tuple
import streamlit as st
import pandas as pd
import logging
from code_editor import code_editor

logger = logging.getLogger(__name__)


class QueryResultsDisplay:
    """Display actual query results from Elasticsearch in a clean tabular format"""

    def __init__(self):
        """Initialize the query results display"""
        self.max_display_rows = 100
        self.max_display_cols = 20

    def render_query_with_results(
        self,
        query: Dict[str, Any],
        results: Optional[Dict[str, Any]] = None,
        show_pipeline_view: bool = False,
        unique_key: str = "",
        allow_editing: bool = False
    ) -> Optional[str]:
        """Render a query with optional results display

        Args:
            query: Query dictionary with 'name', 'esql_query', etc.
            results: Optional results from Elasticsearch execution
            show_pipeline_view: If True, show educational data pipeline view
            unique_key: Unique key for Streamlit widgets
            allow_editing: If True, render query as editable code editor with SQL syntax highlighting

        Returns:
            If allow_editing=True, returns the edited query text. Otherwise returns None.
        """
        # Query name and type
        query_name = query.get('name', 'Untitled Query')
        st.markdown(f"### {query_name}")

        # Query type badge
        query_type = query.get('query_type', 'scripted')
        self._render_query_type_badge(query_type)

        # Description
        if query.get('description'):
            st.caption(query['description'])

        # Create tabs for different views
        if results:
            tab_clean, tab_results, tab_pipeline = st.tabs([
                "📝 ES|QL Query",
                "📊 Results",
                "🔬 Data Pipeline (Educational)"
            ])
        else:
            tab_clean = st.container()
            tab_results = None
            tab_pipeline = None

        # Clean ES|QL query view
        edited_query = None
        with tab_clean:
            query_text = self._get_query_text(query)

            if allow_editing:
                # Use code editor for editable queries with SQL syntax highlighting
                editor_response = code_editor(
                    code=query_text,
                    lang="sql",
                    height=[10, 30],  # Min/max height
                    allow_reset=True,
                    key=f"code_editor_{unique_key}"
                )

                # Extract edited text from response
                if editor_response and 'text' in editor_response:
                    edited_query = editor_response['text']
                else:
                    edited_query = query_text
            else:
                # Use read-only code display
                st.code(query_text, language='sql')

            # Show parameters if they exist
            if query.get('parameters'):
                self._render_parameters(query['parameters'])

        # Query results view (if available)
        if results and tab_results:
            with tab_results:
                self._render_query_results(results, unique_key=unique_key)

        # Educational pipeline view (if requested and available)
        if show_pipeline_view and tab_pipeline:
            with tab_pipeline:
                self._render_pipeline_view(query, results)

        # Return edited query if editing is enabled
        return edited_query if allow_editing else None

    def _render_query_type_badge(self, query_type: str):
        """Render a badge showing the query type"""
        badges = {
            'scripted': ("**Type:** `Scripted` ✅", "*Executable - can be tested against data*"),
            'parameterized': ("**Type:** `Parameterized` ⚙️", "*Agent Builder Tool - requires parameters*"),
            'rag': ("**Type:** `RAG` 🤖", "*Agent Builder Tool - semantic search enabled*")
        }
        badge_text, description = badges.get(query_type, ("**Type:** `Unknown`", ""))
        st.markdown(f"{badge_text} {description}")

    def _get_query_text(self, query: Dict) -> str:
        """Extract query text from various possible field names"""
        # Support multiple field name conventions
        return (
            query.get('esql') or
            query.get('esql_query') or
            query.get('query') or
            query.get('es|ql') or
            ''
        )

    def _render_parameters(self, parameters, allow_input=False, unique_key=""):
        """Render query parameters in an expandable section

        Args:
            parameters: Parameter definitions (list or dict)
            allow_input: If True, render input widgets for parameter values
            unique_key: Unique key for input widgets
        """
        if allow_input:
            # Render parameter inputs for testing
            return self._render_parameter_inputs(parameters, unique_key)
        else:
            # Render parameter definitions (read-only)
            with st.expander("📋 Parameters"):
                # Handle both list and dict formats
                if isinstance(parameters, list):
                    for param_info in parameters:
                        self._render_single_parameter(
                            param_info.get('name', 'unknown'),
                            param_info
                        )
                elif isinstance(parameters, dict):
                    for param_name, param_info in parameters.items():
                        self._render_single_parameter(param_name, param_info)

            return None

    def _render_single_parameter(self, param_name: str, param_info):
        """Render a single parameter

        Handles both formats:
        - Old format: param_info is a string (simple value)
        - New format: param_info is a dict with type, description, default, required
        """
        st.markdown(f"**{param_name}**")

        # Handle old format (string) vs new format (dict)
        if isinstance(param_info, str):
            # Old format: simple string value
            st.write(f"Type: `string`")
            st.write(f"Default: `{param_info}`")
        else:
            # New format: dictionary with metadata
            # Type
            param_type = param_info.get('type', 'string')
            st.write(f"Type: `{param_type}`")

            # Description
            if param_info.get('description'):
                st.write(f"Description: {param_info['description']}")

            # Default value
            if 'default' in param_info:
                st.write(f"Default: `{param_info['default']}`")

            # Required flag
            if param_info.get('required'):
                st.write("**Required**")

        st.divider()

    def _render_parameter_inputs(self, parameters, unique_key=""):
        """Render input widgets for parameter values

        Returns:
            dict: Parameter name to value mapping
        """
        st.markdown("#### 🔧 Test Parameters")
        st.caption("Enter values for each parameter to test the query")

        param_values = {}

        # Handle both list and dict formats
        param_list = parameters if isinstance(parameters, list) else [
            {"name": k, **v} if isinstance(v, dict) else {"name": k, "type": "string", "default": v}
            for k, v in parameters.items()
        ]

        # Check if we have date/timestamp parameters (start_date, end_date, etc.)
        has_date_params = any(
            'date' in param_info.get('name', '').lower() or
            'time' in param_info.get('name', '').lower() or
            param_info.get('type', '').lower() in ['date', 'datetime', 'timestamp']
            for param_info in param_list
        )

        # Show sample date ranges if we have date parameters
        if has_date_params:
            with st.expander("📅 Sample Date Ranges", expanded=False):
                st.caption("Copy these sample values to quickly test different time ranges")

                from datetime import datetime, timedelta
                now = datetime.now()

                # Calculate sample date ranges
                sample_ranges = [
                    {
                        "label": "Last 3 years",
                        "start": (now - timedelta(days=3*365)).strftime('%Y-%m-%d'),
                        "end": now.strftime('%Y-%m-%d')
                    },
                    {
                        "label": "3 months ago to last week",
                        "start": (now - timedelta(days=90)).strftime('%Y-%m-%d'),
                        "end": (now - timedelta(days=7)).strftime('%Y-%m-%d')
                    },
                    {
                        "label": "Last 30 days",
                        "start": (now - timedelta(days=30)).strftime('%Y-%m-%d'),
                        "end": now.strftime('%Y-%m-%d')
                    },
                    {
                        "label": "Last week",
                        "start": (now - timedelta(days=7)).strftime('%Y-%m-%d'),
                        "end": now.strftime('%Y-%m-%d')
                    }
                ]

                for sample in sample_ranges:
                    col1, col2, col3 = st.columns([2, 2, 2])
                    with col1:
                        st.caption(f"**{sample['label']}**")
                    with col2:
                        st.code(sample['start'], language=None)
                    with col3:
                        st.code(sample['end'], language=None)

        # Render parameters in a two-column layout for more compact display
        for i in range(0, len(param_list), 2):
            # Create two columns
            col1, col2 = st.columns(2)

            # Render first parameter in left column
            with col1:
                if i < len(param_list):
                    param_values.update(self._render_single_parameter_input(
                        param_list[i], unique_key
                    ))

            # Render second parameter in right column (if exists)
            with col2:
                if i + 1 < len(param_list):
                    param_values.update(self._render_single_parameter_input(
                        param_list[i + 1], unique_key
                    ))

        return param_values

    def _render_single_parameter_input(self, param_info: Dict, unique_key: str) -> Dict[str, Any]:
        """Render a single parameter input widget

        Args:
            param_info: Parameter information dictionary
            unique_key: Unique key for widget

        Returns:
            Dict with parameter name and value
        """
        param_name = param_info.get('name', 'unknown')
        param_type = param_info.get('type', 'string')
        param_desc = param_info.get('description', '')
        param_default = param_info.get('default', '')
        param_required = param_info.get('required', False)

        # Create input widget based on type
        label = f"**{param_name}**" + (" *" if param_required else "")
        help_text = param_desc if param_desc else f"Enter value for {param_name}"

        if param_type in ['integer', 'long']:
            default_val = int(param_default) if param_default and str(param_default).isdigit() else 0
            value = st.number_input(
                label,
                value=default_val,
                step=1,
                key=f"param_{unique_key}_{param_name}",
                help=help_text
            )
            return {param_name: int(value)}

        elif param_type in ['double', 'float']:
            default_val = float(param_default) if param_default else 0.0
            value = st.number_input(
                label,
                value=default_val,
                step=0.1,
                key=f"param_{unique_key}_{param_name}",
                help=help_text
            )
            return {param_name: float(value)}

        elif param_type == 'boolean':
            default_val = bool(param_default) if param_default else False
            value = st.checkbox(
                label,
                value=default_val,
                key=f"param_{unique_key}_{param_name}",
                help=help_text
            )
            return {param_name: value}

        elif param_type == 'date':
            from datetime import datetime, timedelta
            # Default to 90 days ago if no default
            default_date = datetime.now() - timedelta(days=90)
            value = st.date_input(
                label,
                value=default_date,
                key=f"param_{unique_key}_{param_name}",
                help=help_text
            )
            return {param_name: value.strftime('%Y-%m-%d')}

        else:  # string, keyword, or unknown
            default_val = str(param_default) if param_default else ""
            value = st.text_input(
                label,
                value=default_val,
                key=f"param_{unique_key}_{param_name}",
                help=help_text,
                placeholder=f"e.g., {param_desc.split('(e.g., ')[-1].rstrip(')')}..." if '(e.g.,' in param_desc else f"Enter {param_name}"
            )
            return {param_name: value}

    def substitute_parameters(self, query_text: str, param_values: Dict[str, Any]) -> str:
        """Substitute parameter values into a parameterized query

        Args:
            query_text: ES|QL query with ?parameter placeholders
            param_values: Dict of parameter name to value

        Returns:
            Query with substituted values
        """
        result = query_text

        for param_name, param_value in param_values.items():
            placeholder = f"?{param_name}"

            # Format value based on type
            if isinstance(param_value, str):
                # String values need quotes
                formatted_value = f'"{param_value}"'
            elif isinstance(param_value, bool):
                # Boolean values are lowercase
                formatted_value = str(param_value).lower()
            else:
                # Numbers don't need quotes
                formatted_value = str(param_value)

            result = result.replace(placeholder, formatted_value)

        return result

    def _render_query_results(self, results: Dict[str, Any], unique_key: str = ""):
        """Render actual query results from Elasticsearch"""
        st.markdown("#### Query Execution Results")

        # Check if we have valid results
        if not results:
            st.info("No results available. Execute the query to see results.")
            return

        # Handle different result formats
        if 'error' in results:
            st.error(f"Query execution failed: {results['error']}")
            return

        # Extract data from ES|QL response
        if 'columns' in results and 'values' in results:
            # ES|QL format with columns and values
            self._render_esql_results(results, unique_key=unique_key)
        elif 'hits' in results:
            # Traditional Elasticsearch format
            self._render_traditional_results(results, unique_key=unique_key)
        else:
            # Unknown format - display as JSON
            st.json(results)

    def _normalize_array_values(self, values: List[List[Any]]) -> List[List[Any]]:
        """Convert array-type values to comma-separated strings for DataFrame compatibility

        ES|QL's VALUES() aggregation returns arrays which Pandas can't handle in DataFrames.
        This function converts any list values to comma-separated strings.

        Args:
            values: List of rows from ES|QL query results

        Returns:
            Normalized list with arrays converted to strings
        """
        normalized = []
        for row in values:
            normalized_row = []
            for val in row:
                if isinstance(val, list):
                    # Convert array to comma-separated string
                    normalized_row.append(', '.join(str(v) for v in val))
                else:
                    normalized_row.append(val)
            normalized.append(normalized_row)
        return normalized

    def _render_esql_results(self, results: Dict, unique_key: str = ""):
        """Render ES|QL format results (columns + values)"""
        columns = [col['name'] for col in results['columns']]
        values = results['values']

        # Normalize array values to strings before creating DataFrame
        # This handles ES|QL's VALUES() aggregation which returns arrays
        normalized_values = self._normalize_array_values(values)

        # Create DataFrame
        df = pd.DataFrame(normalized_values, columns=columns)

        # Display metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", len(df))
        with col2:
            st.metric("Columns", len(columns))
        with col3:
            if 'took' in results:
                st.metric("Query Time", f"{results['took']}ms")

        # Display the data
        if len(df) > self.max_display_rows:
            st.warning(f"Showing first {self.max_display_rows} of {len(df)} rows")
            df = df.head(self.max_display_rows)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        # Download button with unique key
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="query_results.csv",
            mime="text/csv",
            key=f"download_csv_{unique_key}" if unique_key else None
        )

    def _render_traditional_results(self, results: Dict, unique_key: str = ""):
        """Render traditional Elasticsearch hits format"""
        hits = results.get('hits', {}).get('hits', [])

        if not hits:
            st.info("Query returned no results")
            return

        # Extract fields from _source
        records = [hit.get('_source', {}) for hit in hits]
        df = pd.DataFrame(records)

        # Display metadata
        total_hits = results.get('hits', {}).get('total', {}).get('value', len(hits))
        st.metric("Total Hits", total_hits)

        # Display the data
        if len(df) > self.max_display_rows:
            st.warning(f"Showing first {self.max_display_rows} of {total_hits} results")

        st.dataframe(
            df.head(self.max_display_rows),
            use_container_width=True,
            hide_index=True
        )

        # Download button with unique key
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="query_results.csv",
            mime="text/csv",
            key=f"download_csv_{unique_key}" if unique_key else None
        )

    def _render_pipeline_view(self, query: Dict, results: Optional[Dict]):
        """Render educational data pipeline view showing transformations"""
        st.markdown("#### Data Pipeline Visualization")
        st.info(
            "This educational view shows how data flows through the ES|QL pipeline. "
            "This is for learning purposes only - actual queries execute directly in Elasticsearch."
        )

        # Parse the query to identify pipeline stages
        query_text = self._get_query_text(query)
        stages = self._parse_pipeline_stages(query_text)

        # Display each stage
        for i, stage in enumerate(stages, 1):
            with st.expander(f"Stage {i}: {stage['operation']}", expanded=(i == 1)):
                st.code(stage['command'], language='sql')

                if stage.get('description'):
                    st.caption(stage['description'])

                # If we have sample data for this stage, show it
                if stage.get('sample_data'):
                    st.markdown("**Sample Output:**")
                    st.dataframe(
                        stage['sample_data'],
                        use_container_width=True,
                        hide_index=True
                    )

    def _parse_pipeline_stages(self, query_text: str) -> List[Dict]:
        """Parse ES|QL query into pipeline stages for visualization"""
        stages = []
        lines = query_text.strip().split('\n')

        current_command = []
        for line in lines:
            line = line.strip()
            if line.startswith('|') and current_command:
                # New pipeline stage
                command_text = '\n'.join(current_command)
                stages.append(self._create_stage_info(command_text))
                current_command = [line]
            else:
                current_command.append(line)

        # Add the last stage
        if current_command:
            command_text = '\n'.join(current_command)
            stages.append(self._create_stage_info(command_text))

        return stages

    def _create_stage_info(self, command: str) -> Dict:
        """Create stage information from a command"""
        # Identify the operation type
        command_upper = command.upper()

        if command_upper.startswith('FROM'):
            operation = "Data Source"
            description = "Load data from the specified index or data stream"
        elif 'WHERE' in command_upper:
            operation = "Filter"
            description = "Filter rows based on conditions"
        elif 'LOOKUP JOIN' in command_upper:
            operation = "Enrich"
            description = "Join with lookup data for enrichment"
        elif 'STATS' in command_upper:
            operation = "Aggregate"
            description = "Calculate statistics and group data"
        elif 'EVAL' in command_upper:
            operation = "Transform"
            description = "Create calculated fields"
        elif 'SORT' in command_upper:
            operation = "Sort"
            description = "Order results"
        elif 'LIMIT' in command_upper:
            operation = "Limit"
            description = "Restrict number of results"
        elif 'INLINESTATS' in command_upper:
            operation = "Inline Statistics"
            description = "Calculate stats while preserving all rows"
        else:
            operation = "Process"
            description = None

        return {
            'operation': operation,
            'command': command,
            'description': description
        }


def render_queries_with_execution(
    queries: List[Dict],
    query_type: str,
    es_client=None,
    show_pipeline_view: bool = False
):
    """Render queries with optional execution capability

    Args:
        queries: List of query dictionaries
        query_type: Type of queries ('scripted', 'parameterized', 'rag')
        es_client: Optional Elasticsearch client for execution
        show_pipeline_view: If True, show educational pipeline view
    """
    display = QueryResultsDisplay()

    if not queries:
        st.info(f"No {query_type} queries available")
        return

    for i, query in enumerate(queries, 1):
        query_name = query.get('name', f'Query {i}')

        # Create a unique key for this query's execution state
        exec_key = f"{query_type}_query_{i}_executed"
        results_key = f"{query_type}_query_{i}_results"

        # Container for this query
        with st.container():
            st.markdown(f"### {i}. {query_name}")

            # Add execution button for scripted queries with ES client
            if query_type == 'scripted' and es_client:
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button(f"▶️ Execute", key=f"exec_{query_type}_{i}"):
                        with st.spinner("Executing query..."):
                            try:
                                # Execute the query
                                query_text = display._get_query_text(query)
                                results = es_client.execute_esql(query_text)

                                # Store results in session state
                                st.session_state[exec_key] = True
                                st.session_state[results_key] = results
                                st.success("Query executed successfully!")
                            except Exception as e:
                                st.error(f"Execution failed: {e}")
                                st.session_state[exec_key] = True
                                st.session_state[results_key] = {'error': str(e)}

            # Get results from session state if available
            results = None
            if st.session_state.get(exec_key):
                results = st.session_state.get(results_key)

            # Keys for storing optimization state (define early so we can check them)
            optimize_key = f"{query_type}_query_{i}_optimize"
            optimized_query_key = f"{query_type}_query_{i}_optimized_query"
            optimized_explanation_key = f"{query_type}_query_{i}_optimized_explanation"

            # Show optimized query if available (persists across reruns, shown for ANY result state)
            if optimized_query_key in st.session_state:
                st.info("💡 Optimized Query Suggestion")
                st.success(f"✅ {st.session_state[optimized_explanation_key]}")
                st.code(st.session_state[optimized_query_key], language='sql')

                # Offer to test the optimized query
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("▶️ Test Query", key=f"{optimize_key}_test"):
                        try:
                            test_results = es_client.execute_esql(st.session_state[optimized_query_key])
                            st.session_state[results_key] = test_results
                            st.session_state[exec_key] = True
                            # Clear optimization state after successful test
                            del st.session_state[optimized_query_key]
                            del st.session_state[optimized_explanation_key]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Test failed: {e}")
                with col2:
                    if st.button("❌ Clear Suggestion", key=f"{optimize_key}_clear"):
                        # Clear optimization state
                        del st.session_state[optimized_query_key]
                        del st.session_state[optimized_explanation_key]
                        st.rerun()

            # Check if query returned zero results - offer optimization
            if (query_type == 'scripted' and results and
                'columns' in results and 'values' in results and
                len(results['values']) == 0 and
                optimized_query_key not in st.session_state):  # Only show button if no suggestion exists

                # Show optimize button for zero-results queries
                if st.button("🔧 Fix Query", key=optimize_key, help="Use LLM to relax constraints and improve results"):
                    with st.spinner("Analyzing constraints..."):
                        try:
                            # Import optimizer
                            from src.services.query_optimizer import relax_query_constraints, load_data_profile
                            from src.services.llm_proxy_service import UnifiedLLMClient
                            import os

                            # Get LLM client
                            llm_client = UnifiedLLMClient()

                            # Get data profile (extract module name from somewhere - for now use first demo)
                            # TODO: Pass module_name as parameter to this function
                            data_profile = None

                            # Get current query
                            current_esql = display._get_query_text(query)

                            # Optimize
                            optimized_esql, explanation = relax_query_constraints(
                                query=query,
                                current_esql=current_esql,
                                data_profile=data_profile,
                                llm_client=llm_client
                            )

                            # Store in session state so it persists across reruns
                            st.session_state[optimized_query_key] = optimized_esql
                            st.session_state[optimized_explanation_key] = explanation
                            st.rerun()
                        except Exception as e:
                            st.error(f"Optimization failed: {e}")

            # Render the query with results
            display.render_query_with_results(
                query,
                results=results,
                show_pipeline_view=show_pipeline_view,
                unique_key=f"{query_type}_{i}"
            )

            st.divider()