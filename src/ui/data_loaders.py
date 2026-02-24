"""
Cached data loading functions for demo modules

This module provides cached data loaders for demo datasets, queries, guides,
and data profiles. All functions use Streamlit's caching to avoid expensive
regeneration on every UI interaction.
"""

import streamlit as st
from pathlib import Path
import json
from typing import Dict, List, Any, Optional
import logging

from src.framework import DemoModuleManager

logger = logging.getLogger(__name__)


@st.cache_data(ttl=3600)
def load_data_generator_module(module_name: str):
    """Load the data generator class from a demo module

    Returns:
        DataGenerator class (not instance) or None
    """
    manager = DemoModuleManager()
    loader = manager.get_module(module_name)
    if loader:
        # Return the class itself, not an instance
        return loader.load_data_generator().__class__
    return None

@st.cache_data(ttl=3600)
def load_demo_datasets(module_name: str):
    """Cache dataset generation for faster loading"""
    manager = DemoModuleManager()
    loader = manager.get_module(module_name)
    if loader:
        data_gen = loader.load_data_generator()
        return data_gen.generate_datasets()
    return {}

@st.cache_data(ttl=3600)
def load_demo_queries(module_name: str):
    """Cache query generation for faster loading

    Returns dict with three query types:
    {
        'scripted': [...],
        'parameterized': [...],
        'rag': [...]
    }

    Automatically merges in auto-fixed queries from query_testing_results.json if available.
    """
    manager = DemoModuleManager()
    loader = manager.get_module(module_name)
    if loader:
        datasets = load_demo_datasets(module_name)
        query_gen = loader.load_query_generator(datasets)

        # Always call all three methods - modern modules implement all three
        scripted = query_gen.generate_queries()
        parameterized = query_gen.generate_parameterized_queries()
        rag = query_gen.generate_rag_queries()

        # Merge in auto-fixed queries from test results if available
        try:
            test_results_path = Path('demos') / module_name / 'query_testing_results.json'
            if test_results_path.exists():
                with open(test_results_path, 'r') as f:
                    test_results = json.load(f)

                # Create a map of query names to fixed queries
                fixed_queries = {}
                for result in test_results.get('queries', []):
                    if result.get('was_fixed') and result.get('final_esql'):
                        fixed_queries[result['name']] = result['final_esql']

                # Replace original queries with fixed versions
                for i, query in enumerate(scripted):
                    if query['name'] in fixed_queries:
                        scripted[i] = query.copy()
                        scripted[i]['query'] = fixed_queries[query['name']]
                        scripted[i]['_auto_fixed'] = True  # Mark as auto-fixed
        except Exception as e:
            # Silently fail - just use original queries
            pass

        return {
            'scripted': scripted,
            'parameterized': parameterized,
            'rag': rag,
            'all': scripted + parameterized + rag  # For backward compatibility
        }
    return {'scripted': [], 'parameterized': [], 'rag': [], 'all': []}

@st.cache_data(ttl=3600)
def load_demo_guide(module_name: str):
    """Cache guide generation for faster loading"""
    manager = DemoModuleManager()
    loader = manager.get_module(module_name)
    if loader:
        datasets = load_demo_datasets(module_name)
        queries_dict = load_demo_queries(module_name)
        # Pass all queries to guide generator
        guide_gen = loader.load_demo_guide(datasets, queries_dict['all'])
        return guide_gen.generate_guide()
    return ""

@st.cache_data(ttl=3600)
def load_demo_data_profile(module_name: str):
    """Load data profile from demo module

    Returns:
        dict: Data profile with field statistics and sample values
    """
    try:
        profile_path = Path("demos") / module_name / "data_profile.json"
        if profile_path.exists():
            with open(profile_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load data profile for {module_name}: {e}")
    return None

def get_sample_values_for_parameters(data_profile: dict, parameters: List[Dict]) -> Dict[str, List[str]]:
    """Extract sample values from data profile for query parameters

    Args:
        data_profile: Data profile dictionary with field statistics
        parameters: List of parameter definitions from query

    Returns:
        dict: Parameter name to list of sample values
    """
    if not data_profile or 'datasets' not in data_profile:
        return {}

    sample_values = {}

    # Common parameter name patterns to field name mappings
    field_mapping_patterns = {
        'search_terms': ['title', 'description', 'name', 'content', 'text'],
        'search_query': ['title', 'description', 'name', 'content', 'text'],
        'query': ['title', 'description', 'name', 'content'],
        'brand_filter': ['brand', 'brand_name'],
        'brand_name': ['brand', 'brand_name'],
        'min_engagement': ['engagement_score', 'engagement', 'score'],
        'min_downloads': ['download_count', 'downloads'],
        'campaign_name': ['campaign_name', 'campaign', 'campaign_theme'],
        'asset_type': ['asset_type', 'type', 'content_type'],
        'file_format': ['file_format', 'format', 'extension']
    }

    for param in parameters:
        param_name = param.get('name', '')
        param_type = param.get('type', 'string')
        param_desc = param.get('description', '').lower()

        # Search across all datasets for matching fields
        matches = []
        for dataset_name, dataset_info in data_profile['datasets'].items():
            fields = dataset_info.get('fields', {})

            # Strategy 1: Exact match
            if param_name in fields:
                field_data = fields[param_name]
                unique_vals = field_data.get('unique_values', [])
                if unique_vals:
                    matches.extend(unique_vals[:10])
                    continue  # Found exact match, move to next parameter

            # Strategy 2: Check predefined mapping patterns
            if param_name in field_mapping_patterns:
                for candidate_field in field_mapping_patterns[param_name]:
                    if candidate_field in fields:
                        field_data = fields[candidate_field]
                        unique_vals = field_data.get('unique_values', [])
                        if unique_vals:
                            matches.extend(unique_vals[:10])
                            break  # Found via pattern, continue to next dataset
                if matches:
                    continue  # Found via pattern, move to next parameter

            # Strategy 3: Partial substring match
            for field_name, field_data in fields.items():
                if param_name in field_name or field_name in param_name:
                    unique_vals = field_data.get('unique_values', [])
                    if unique_vals:
                        matches.extend(unique_vals[:10])

            # Strategy 4: For text search parameters, grab values from text fields
            if not matches and param_type == 'string' and any(keyword in param_desc for keyword in ['search', 'query', 'terms', 'text']):
                # Look for likely text search fields
                for field_name in ['title', 'description', 'name', 'content', 'text']:
                    if field_name in fields:
                        field_data = fields[field_name]
                        unique_vals = field_data.get('unique_values', [])
                        if unique_vals:
                            # For text fields, generate sample search queries from unique values
                            matches.extend(unique_vals[:5])
                            break

        # Deduplicate and limit to first 5-7 unique values
        if matches:
            unique_matches = list(dict.fromkeys(matches))[:7]
            sample_values[param_name] = unique_matches

    return sample_values

def generate_sample_question(query: Dict, param: Dict, data_profile: dict) -> str:
    """Use LLM to generate a contextual sample question for semantic search parameters

    Args:
        query: Query definition with name, description, query text
        param: Parameter definition with name, description, example
        data_profile: Data profile with available fields and values

    Returns:
        str: Generated sample question
    """
    from src.services.llm_proxy_service import UnifiedLLMClient
    import os

    try:
        llm_client = UnifiedLLMClient()

        # Build context about available data
        data_context = ""
        if data_profile and 'datasets' in data_profile:
            data_context = "Available datasets and fields:\n"
            for dataset_name, dataset_info in data_profile['datasets'].items():
                fields = dataset_info.get('fields', {})
                field_names = list(fields.keys())[:10]  # First 10 fields
                data_context += f"- {dataset_name}: {', '.join(field_names)}\n"

        prompt = f"""Generate a realistic sample question for testing this ES|QL semantic search query.

Query Name: {query.get('name', 'Unknown')}
Query Description: {query.get('description', 'No description')}

Parameter: {param.get('name', 'unknown')}
Parameter Description: {param.get('description', 'Natural language question')}
Parameter Example: {param.get('example', 'N/A')}

{data_context}

Generate a single, specific natural language question that:
1. Matches the query's purpose
2. Would return relevant results from the available data
3. Is something a real user might ask

Return ONLY the question text, no explanation or formatting."""

        response = llm_client.messages.create(
            model="claude-3-5-haiku-20241022",  # Fast, cheap model for suggestions
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        suggested_question = response.content[0].text.strip()
        return suggested_question

    except Exception as e:
        logger.error(f"Failed to generate sample question: {e}")
        # Fallback to example if LLM fails
        return param.get('example', 'What is the most common issue?')
