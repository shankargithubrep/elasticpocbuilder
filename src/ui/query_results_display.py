"""
Query Results Display Module
Handles visualization of actual ES|QL query results from Elasticsearch
"""

from typing import Dict, List, Any, Optional
import streamlit as st
import pandas as pd
import logging

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
        show_pipeline_view: bool = False
    ):
        """Render a query with optional results display

        Args:
            query: Query dictionary with 'name', 'esql_query', etc.
            results: Optional results from Elasticsearch execution
            show_pipeline_view: If True, show educational data pipeline view
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
        with tab_clean:
            query_text = self._get_query_text(query)
            st.code(query_text, language='sql')

            # Show parameters if they exist
            if query.get('parameters'):
                self._render_parameters(query['parameters'])

        # Query results view (if available)
        if results and tab_results:
            with tab_results:
                self._render_query_results(results)

        # Educational pipeline view (if requested and available)
        if show_pipeline_view and tab_pipeline:
            with tab_pipeline:
                self._render_pipeline_view(query, results)

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

    def _render_parameters(self, parameters):
        """Render query parameters in an expandable section"""
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

    def _render_query_results(self, results: Dict[str, Any]):
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
            self._render_esql_results(results)
        elif 'hits' in results:
            # Traditional Elasticsearch format
            self._render_traditional_results(results)
        else:
            # Unknown format - display as JSON
            st.json(results)

    def _render_esql_results(self, results: Dict):
        """Render ES|QL format results (columns + values)"""
        columns = [col['name'] for col in results['columns']]
        values = results['values']

        # Create DataFrame
        df = pd.DataFrame(values, columns=columns)

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

        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name="query_results.csv",
            mime="text/csv"
        )

    def _render_traditional_results(self, results: Dict):
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

            # Render the query with results
            display.render_query_with_results(
                query,
                results=results,
                show_pipeline_view=show_pipeline_view
            )

            st.divider()