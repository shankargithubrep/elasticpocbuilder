"""
Module Visualizer - Enhanced Config Tab Display
Provides comprehensive visualization of demo module structure, relationships, and business value
"""

import streamlit as st
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from collections import defaultdict

logger = logging.getLogger(__name__)


class ModuleVisualizer:
    """Visualize demo module structure, relationships, and query strategy"""

    def __init__(self, module_path: Path, llm_client=None):
        """Initialize with module path and optional LLM client for summaries

        Args:
            module_path: Path to the demo module directory
            llm_client: Optional Anthropic client for generating summaries
        """
        self.module_path = module_path
        self.llm_client = llm_client
        self.module_name = module_path.name

        # Load all module data
        self.config = self._load_json('config.json')
        self.query_strategy = self._load_json('query_strategy.json')
        self.data_profile = self._load_json('data_profile.json')
        self.test_results = self._load_json('query_testing_results.json')

        # Parse loaded data
        self._parse_module_data()

    def _load_json(self, filename: str) -> Dict:
        """Load JSON file from module directory"""
        file_path = self.module_path / filename
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load {filename}: {e}")
        return {}

    def _parse_module_data(self):
        """Parse and structure module data for visualization"""
        # Extract datasets from query strategy (reload trigger)
        self.datasets = self.query_strategy.get('datasets', [])
        self.dataset_map = {d['name']: d for d in self.datasets}

        # Build relationships map from data generator module's get_relationships() method
        self.relationships = []
        try:
            # Load the data generator instance directly
            from src.framework import DemoModuleManager
            manager = DemoModuleManager()
            loader = manager.get_module(self.module_name)
            if loader:
                data_gen = loader.load_data_generator()
                if hasattr(data_gen, 'get_relationships'):
                    relationships = data_gen.get_relationships()
                    # Parse tuples: (source_table, foreign_key, target_table) -> (source_table, target_table)
                    for rel in relationships:
                        if len(rel) >= 3:
                            source_table, foreign_key, target_table = rel[0], rel[1], rel[2]
                            self.relationships.append((source_table, target_table))
                        elif len(rel) == 2:
                            # Handle simple (source, target) format
                            self.relationships.append((rel[0], rel[1]))
                    logger.info(f"Loaded {len(self.relationships)} relationships from data generator")
                else:
                    logger.warning(f"Data generator has no get_relationships method")
        except Exception as e:
            logger.warning(f"Could not load relationships from data generator: {e}", exc_info=True)

        # Fallback: if no relationships found, try data_profile.json (detected by data profiler)
        if not self.relationships and self.data_profile.get('relationships'):
            for rel in self.data_profile['relationships']:
                source = rel.get('source_dataset')
                target = rel.get('lookup_dataset')
                if source and target:
                    self.relationships.append((source, target))
            if self.relationships:
                logger.info(f"Loaded {len(self.relationships)} relationships from data profile")

        # Fallback: try query_strategy.json dataset relationships
        if not self.relationships:
            for dataset in self.datasets:
                source_name = dataset['name']
                for target_name in dataset.get('relationships', []):
                    self.relationships.append((source_name, target_name))

        # Load actual queries from the module using the same method as the UI
        try:
            from .data_loaders import load_demo_queries
            # Clear cache to ensure we get fresh data
            load_demo_queries.clear()
            queries_dict = load_demo_queries(self.module_name)
            self.scripted_queries = queries_dict.get('scripted', [])
            self.parameterized_queries = queries_dict.get('parameterized', [])
            self.rag_queries = queries_dict.get('rag', [])
            self.queries = queries_dict.get('all', [])

            # Debug logging
            logger.info(f"Loaded queries for {self.module_name}:")
            logger.info(f"  Scripted: {len(self.scripted_queries)}")
            logger.info(f"  Parameterized: {len(self.parameterized_queries)}")
            logger.info(f"  RAG: {len(self.rag_queries)}")
        except Exception as e:
            logger.warning(f"Could not load queries from module {self.module_name}: {e}")
            # Fallback to empty lists
            self.scripted_queries = []
            self.parameterized_queries = []
            self.rag_queries = []
            self.queries = []

        # Count query types
        self.query_counts = {
            'scripted': len(self.scripted_queries),
            'parameterized': len(self.parameterized_queries),
            'rag': len(self.rag_queries)
        }

        # Calculate total records from ACTUAL data (not query_strategy estimates)
        self.total_records = self._get_actual_record_count()

        # Also store actual row counts per dataset for display
        self.actual_row_counts = self._get_actual_row_counts_by_dataset()

    def _parse_row_count(self, count_str: str) -> int:
        """Parse row count string to integer"""
        if isinstance(count_str, int):
            return count_str
        # Handle strings like "500000+", "1000-5000", etc.
        count_str = str(count_str).strip()

        # Remove suffixes like '+', '~'
        count_str = count_str.replace('+', '').replace('~', '')

        # Handle ranges - take the first number
        if '-' in count_str:
            count_str = count_str.split('-')[0].strip()

        # Try to parse as integer
        try:
            # Clean the string to only keep digits
            cleaned = ''.join(c for c in count_str if c.isdigit())
            if cleaned:
                return int(cleaned)
            return 0
        except:
            return 0

    def generate_executive_summary(self) -> str:
        """Generate executive summary using LLM or fallback template"""
        if self.llm_client:
            try:
                # Prepare context for LLM
                context = self.config.get('customer_context', {})

                prompt = f"""Generate a 2-3 sentence executive summary for this demo module:

Company: {context.get('company_name', 'Unknown')}
Industry: {context.get('industry', 'Unknown')}
Department: {context.get('department', 'Unknown')}
Demo Type: {self.config.get('demo_type', 'observability')}

Datasets: {len(self.datasets)} datasets with {self.total_records:,}+ records
- Types: {', '.join(set(d.get('type', 'unknown') for d in self.datasets))}

Queries: {len(self.queries)} total
- {self.query_counts['scripted']} scripted (direct execution)
- {self.query_counts['parameterized']} parameterized (user input)
- {self.query_counts['rag']} RAG (semantic search)

Pain Points Addressed: {', '.join(context.get('pain_points', [])[:3])}

Key Use Cases: {', '.join(context.get('use_cases', [])[:3])}

Write a business-focused summary highlighting the demo's purpose and value. Focus on what business problems it solves."""

                response = self.llm_client.messages.create(
                    model="claude-3-5-haiku-20241022",
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompt}]
                )

                return response.content[0].text.strip()

            except Exception as e:
                logger.warning(f"LLM summary generation failed: {e}")

        # Fallback template-based summary
        context = self.config.get('customer_context', {})
        demo_type = "search and retrieval" if self.config.get('demo_type') == 'search' else "observability"

        return f"""This {demo_type} demo for {context.get('company_name', 'the organization')} addresses {len(context.get('pain_points', []))} critical pain points across {context.get('department', 'the department')}.
        It analyzes {len(self.datasets)} interconnected datasets containing {self.total_records:,}+ records with {len(self.queries)} queries covering key business scenarios."""

    def create_relationship_diagram(self) -> go.Figure:
        """Create interactive dataset relationship diagram using Plotly"""
        # Create nodes for datasets
        node_labels = []
        node_colors = []
        node_sizes = []
        node_hover = []

        # Color mapping by dataset type
        type_colors = {
            'timeseries': '#3498db',  # Blue
            'reference': '#2ecc71',   # Green
            'documents': '#f39c12',   # Orange
            'events': '#9b59b6'       # Purple
        }

        # Create node positions using circular layout
        import math
        n_nodes = len(self.datasets)
        positions = {}

        for i, dataset in enumerate(self.datasets):
            angle = 2 * math.pi * i / n_nodes
            x = math.cos(angle)
            y = math.sin(angle)
            positions[dataset['name']] = (x, y)

            # Node properties
            node_labels.append(dataset['name'])
            node_colors.append(type_colors.get(dataset.get('type', 'reference'), '#95a5a6'))

            # Size based on actual row count (log scale)
            dataset_name = dataset['name']
            actual_count = self.actual_row_counts.get(dataset_name)
            if actual_count is not None:
                row_count = actual_count
                count_display = f"{actual_count:,}"
            else:
                # Fallback to estimated count if actual data not available
                row_count = self._parse_row_count(dataset.get('row_count', '1000'))
                count_display = f"{dataset.get('row_count', 'unknown')} (est)"

            node_sizes.append(20 + math.log10(max(row_count, 1)) * 5)

            # Hover text with actual row count
            hover_text = f"""<b>{dataset_name}</b><br>
Type: {dataset.get('type', 'unknown')}<br>
Rows: {count_display}<br>
Index Mode: {dataset.get('index_mode', 'standard')}<br>
Fields: {len(dataset.get('required_fields', {}))}"""
            node_hover.append(hover_text)

        # Create edges for relationships
        edge_x = []
        edge_y = []
        edge_text = []

        # Create edges from relationships list
        for source_dataset, target_dataset in self.relationships:
            if source_dataset in positions and target_dataset in positions:
                x0, y0 = positions[source_dataset]
                x1, y1 = positions[target_dataset]

                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                edge_text.append(f"{source_dataset} → {target_dataset}")

        # Create Plotly figure
        fig = go.Figure()

        # Add edges
        if edge_x:
            fig.add_trace(go.Scatter(
                x=edge_x, y=edge_y,
                mode='lines',
                line=dict(width=1, color='#bdc3c7'),
                hoverinfo='text',
                text=edge_text,
                showlegend=False
            ))

        # Add nodes
        fig.add_trace(go.Scatter(
            x=[pos[0] for pos in positions.values()],
            y=[pos[1] for pos in positions.values()],
            mode='markers+text',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white')
            ),
            text=node_labels,
            textposition="top center",
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=node_hover,
            showlegend=False
        ))

        # Update layout
        fig.update_layout(
            title="Dataset Relationships",
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            height=400,
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )

        return fig

    def render_module_overview(self):
        """Main rendering function for enhanced Config tab"""

        # Executive Summary
        st.markdown("### 📊 Module Overview")

        summary = self.generate_executive_summary()
        st.info(summary)

        # Quick Stats
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            demo_type = self.config.get('demo_type', 'observability')
            if demo_type == 'analytics':
                demo_type = 'observability'  # Backward compatibility
            type_emoji = "🔍" if demo_type == "search" else "📊"
            st.metric("Demo Type", f"{type_emoji} {demo_type.title()}")

        with col2:
            st.metric("Datasets", len(self.datasets), f"{self.total_records:,}+ records")

        with col3:
            total_queries = sum(self.query_counts.values())
            st.metric("Queries", total_queries, f"{self.query_counts['scripted']}/{self.query_counts['parameterized']}/{self.query_counts['rag']}")

        with col4:
            relationship_count = len(self.relationships)
            st.metric("Relationships", relationship_count, "connections")

        # Relationship Diagram
        if self.datasets:
            st.markdown("### 🔗 Dataset Relationships")
            try:
                fig = self.create_relationship_diagram()
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                logger.warning(f"Could not create relationship diagram: {e}")
                # Fallback to text display
                if self.relationships:
                    st.markdown("**Relationships:**")
                    for source, target in self.relationships:
                        st.text(f"  • {source} → {target}")

        # Dataset Details
        st.markdown("### 📁 Datasets")

        for dataset in self.datasets:
            dataset_name = dataset['name']

            # Get actual row count if available, otherwise use estimated
            actual_count = self.actual_row_counts.get(dataset_name)
            if actual_count is not None:
                count_display = f"{actual_count:,} records"
            else:
                count_display = f"{dataset.get('row_count', 'unknown')} records (estimated)"

            with st.expander(f"**{dataset_name}** ({dataset.get('type', 'unknown')} - {count_display})"):

                # Purpose (if we can derive it)
                purpose = self._derive_dataset_purpose(dataset)
                if purpose:
                    st.markdown(f"**Purpose:** {purpose}")

                # Key fields
                fields = dataset.get('required_fields', {})
                if fields:
                    field_list = list(fields.keys())[:10]  # Show first 10
                    if len(fields) > 10:
                        field_list.append(f"... and {len(fields) - 10} more")
                    st.markdown(f"**Key Fields:** {', '.join(field_list)}")

                # Join relationships
                relationships = self._find_dataset_relationships(dataset_name)
                if relationships:
                    st.markdown("**Relationships:**")
                    for rel in relationships:
                        st.text(f"  {rel}")

                # Query usage
                query_usage = self._count_query_usage(dataset_name)
                st.markdown(f"**Used in:** {query_usage} queries")

        # Query Strategy
        st.markdown("### 🎯 Query Strategy")

        tab1, tab2, tab3 = st.tabs(["Scripted", "Parameterized", "RAG"])

        with tab1:
            if self.scripted_queries:
                self._render_query_list(self.scripted_queries)
            else:
                st.info("No scripted queries in this module")

        with tab2:
            if self.parameterized_queries:
                self._render_query_list(self.parameterized_queries)
            else:
                st.info("No parameterized queries in this module")

        with tab3:
            if self.rag_queries:
                self._render_query_list(self.rag_queries)
            else:
                st.info("No RAG queries in this module")

        # Business Context
        with st.expander("💼 Business Context"):
            context = self.config.get('customer_context', {})

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Pain Points:**")
                for pain in context.get('pain_points', [])[:5]:
                    st.text(f"• {pain}")

            with col2:
                st.markdown("**Use Cases:**")
                for use_case in context.get('use_cases', [])[:5]:
                    st.text(f"• {use_case}")

            st.markdown("**Key Metrics:**")
            metrics = context.get('metrics', [])[:10]
            if metrics:
                st.text(', '.join(metrics))

    def _derive_dataset_purpose(self, dataset: Dict) -> str:
        """Derive dataset purpose from its structure and relationships"""
        name = dataset['name'].lower()
        dataset_type = dataset.get('type', '')

        # Common patterns
        if 'user' in name or 'session' in name:
            return "User behavior and session tracking"
        elif 'product' in name or 'catalog' in name:
            return "Product/service catalog and metadata"
        elif 'transaction' in name or 'sales' in name:
            return "Transaction and sales data"
        elif 'metric' in name or 'performance' in name:
            return "Performance metrics and KPIs"
        elif dataset_type == 'reference':
            return "Reference data for enrichment"
        elif dataset_type == 'timeseries':
            return "Time-series event data"

        return ""

    def _find_dataset_relationships(self, dataset_name: str) -> List[str]:
        """Find all relationships for a dataset"""
        relationships = []

        for source, target in self.relationships:
            if source == dataset_name:
                # Outgoing relationship
                relationships.append(f"→ {target}")
            elif target == dataset_name:
                # Incoming relationship
                relationships.append(f"← from {source}")

        return relationships

    def _get_actual_record_count(self) -> int:
        """Get actual record count from generated data files"""
        try:
            from .data_loaders import load_demo_datasets
            # Load actual datasets
            datasets = load_demo_datasets(self.module_name)
            # Sum the row counts
            return sum(len(df) for df in datasets.values())
        except Exception as e:
            logger.warning(f"Could not load actual datasets to count records: {e}")
            # Fallback to zero
            return 0

    def _get_actual_row_counts_by_dataset(self) -> Dict[str, int]:
        """Get actual row count for each dataset from generated data"""
        try:
            from .data_loaders import load_demo_datasets
            datasets = load_demo_datasets(self.module_name)
            return {name: len(df) for name, df in datasets.items()}
        except Exception as e:
            logger.warning(f"Could not load actual datasets for row counts: {e}")
            return {}

    def _count_query_usage(self, dataset_name: str) -> int:
        """Count how many queries use this dataset by parsing query text"""
        count = 0
        for query in self.queries:
            # Get the query text from the query dict
            query_text = query.get('query', '')

            # Check if dataset name appears in the query text
            # Look for patterns like "FROM dataset_name" or "LOOKUP JOIN dataset_name"
            if dataset_name in query_text:
                count += 1
        return count

    def _render_query_list(self, queries: List[Dict]):
        """Render a list of queries with their details"""
        for i, query in enumerate(queries):
            with st.container():
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**{query.get('name', 'Unnamed Query')}**")

                    # Description
                    desc = query.get('description', '')
                    if desc:
                        st.text(desc[:200] + ('...' if len(desc) > 200 else ''))

                    # Show pain point if available
                    pain_point = query.get('pain_point', '')
                    if pain_point:
                        st.caption(f"Addresses: {pain_point}")

                with col2:
                    # Query type
                    query_type = query.get('query_type', 'unknown')
                    st.caption(f"Type: {query_type}")

                    # Parameters for parameterized queries
                    params = query.get('parameters', [])
                    if params:
                        st.caption(f"Parameters: {len(params)}")
                        for p in params[:2]:
                            st.text(f"• {p.get('name', 'param')}")

            if i < len(queries) - 1:
                st.divider()