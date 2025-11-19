"""
Static file generation for demo modules.

This module handles generation of static JSON files that are used
for quick loading in the UI without needing to execute Python code.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class StaticFileGenerator:
    """Generates static JSON files for demo modules"""

    @staticmethod
    def generate_static_files(module_path: Path) -> None:
        """Generate all static files for a module.

        Creates CSV files for datasets, all_queries.json with all query types,
        and demo_guide.md for the guide text. This enables quick loading in
        the Browse mode UI without executing Python code.

        The method:
        1. Loads the generated data_generator module to create CSV files
        2. Loads the query_generator module to create all_queries.json
        3. Loads the demo_guide module to create demo_guide.md

        Args:
            module_path: Path to the demo module directory

        Returns:
            None (generates files in module_path/data/, module_path/, etc.)

        Notes:
            - Errors in static file generation don't fail the entire process
            - The dynamic Python modules will still work even if static files fail
            - CSV files contain string conversions of all data types
        """
        try:
            # Dynamically load the generated modules
            from src.framework.module_loader import ModuleLoader

            loader = ModuleLoader(str(module_path))

            # Generate and save datasets as CSV
            logger.info("Generating static dataset files...")
            data_gen = loader.load_data_generator()
            datasets = data_gen.generate_datasets()

            # Create data/ subdirectory
            data_dir = module_path / 'data'
            data_dir.mkdir(exist_ok=True)

            for name, df in datasets.items():
                csv_path = data_dir / f"{name}.csv"
                # Convert numpy string types to regular strings to avoid formatting errors
                df_copy = df.copy()
                for col in df_copy.select_dtypes(include=['object']).columns:
                    df_copy[col] = df_copy[col].astype(str)
                df_copy.to_csv(csv_path, index=False)
                logger.info(f"  Saved {name}.csv ({len(df)} rows)")

            # Generate and save ALL queries as structured JSON
            # (Skip if already created by _generate_query_module_with_strategy)
            all_queries_file = module_path / 'all_queries.json'

            if not all_queries_file.exists():
                logger.info("Generating all_queries.json with all query types...")
                query_gen = loader.load_query_generator(datasets)

                # Load all three query types
                scripted_queries = query_gen.generate_queries()
                parameterized_queries = query_gen.generate_parameterized_queries()
                rag_queries = query_gen.generate_rag_queries()

                # Remove @timestamp parameters (LLM often ignores guidance)
                parameterized_queries = StaticFileGenerator._remove_timestamp_parameters(parameterized_queries)

                # Create structured format
                all_queries = {
                    'scripted': scripted_queries,
                    'parameterized': parameterized_queries,
                    'rag': rag_queries,
                    'all': scripted_queries + parameterized_queries + rag_queries
                }

                all_queries_file.write_text(json.dumps(all_queries, indent=2))
                logger.info(f"  Saved all_queries.json ({len(scripted_queries)} scripted, "
                           f"{len(parameterized_queries)} parameterized, {len(rag_queries)} rag)")
            else:
                logger.info("  all_queries.json already exists, loading it...")
                # Load existing all_queries.json
                with open(all_queries_file, 'r') as f:
                    all_queries = json.load(f)
                scripted_queries = all_queries.get('scripted', [])
                parameterized_queries = all_queries.get('parameterized', [])
                rag_queries = all_queries.get('rag', [])

            # Generate and save demo guide as Markdown (using all queries)
            logger.info("Generating static guide file...")
            all_queries_combined = scripted_queries + parameterized_queries + rag_queries
            guide_gen = loader.load_demo_guide(datasets, all_queries_combined)
            guide = guide_gen.generate_guide()

            guide_file = module_path / 'demo_guide.md'
            guide_file.write_text(guide)
            logger.info(f"  Saved demo_guide.md")

            logger.info("Static file generation complete!")

        except Exception as e:
            logger.error(f"Error generating static files: {e}")
            # Don't fail the entire generation if static files fail
            # The dynamic modules will still work
            import traceback
            logger.debug(traceback.format_exc())

    @staticmethod
    def generate_all_queries_file(module_path: Path) -> None:
        """Generate all_queries.json combining all query types.

        Creates a JSON file that contains all queries organized by type
        (scripted, parameterized, rag) for quick access without loading
        the Python module.

        Args:
            module_path: Path to the demo module directory

        Raises:
            ImportError: If the query_generator module cannot be loaded
            Exception: If query generation fails
        """
        try:
            from src.framework.module_loader import ModuleLoader

            loader = ModuleLoader(str(module_path))

            # First, load datasets (needed for query generation)
            data_gen = loader.load_data_generator()
            datasets = data_gen.generate_datasets()

            # Load query generator
            query_gen = loader.load_query_generator(datasets)

            # Generate all three query types
            scripted_queries = query_gen.generate_queries()
            parameterized_queries = query_gen.generate_parameterized_queries()
            rag_queries = query_gen.generate_rag_queries()

            # Remove timestamp parameters (post-generation cleanup)
            parameterized_queries = StaticFileGenerator._remove_timestamp_parameters(parameterized_queries)

            # Create structured format
            all_queries = {
                'scripted': scripted_queries,
                'parameterized': parameterized_queries,
                'rag': rag_queries,
                'all': scripted_queries + parameterized_queries + rag_queries
            }

            # Write to file
            all_queries_file = module_path / 'all_queries.json'
            all_queries_file.write_text(json.dumps(all_queries, indent=2))

            logger.info(f"Generated all_queries.json at {all_queries_file}")
            logger.info(f"  - Scripted queries: {len(scripted_queries)}")
            logger.info(f"  - Parameterized queries: {len(parameterized_queries)}")
            logger.info(f"  - RAG queries: {len(rag_queries)}")

        except Exception as e:
            logger.error(f"Error generating all_queries.json: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            raise

    @staticmethod
    def _remove_timestamp_parameters(parameterized_queries: List[Dict]) -> List[Dict]:
        """Remove @timestamp-related parameters from parameterized queries.

        Despite LLM guidance, timestamp parameters (start_date, end_date, etc.)
        still get generated. This method removes them post-generation.

        Args:
            parameterized_queries: List of parameterized query dicts

        Returns:
            List of queries with timestamp parameters removed

        Example:
            >>> query = {
            ...     'name': 'Test',
            ...     'parameters': {
            ...         'name': {'type': 'string'},
            ...         'start_date': {'type': 'date'},
            ...         'end_date': {'type': 'date'}
            ...     }
            ... }
            >>> result = StaticFileGenerator._remove_timestamp_parameters([query])
            >>> 'start_date' in result[0].get('parameters', {})
            False
            >>> 'name' in result[0].get('parameters', {})
            True
        """
        import re

        # Parameter names that should be removed
        timestamp_param_names = {
            'start_date', 'end_date', 'start_time', 'end_time',
            'timestamp', 'from_date', 'to_date', 'date_from', 'date_to',
            'time_from', 'time_to', 'start_timestamp', 'end_timestamp'
        }

        def normalize_param_name(name: str) -> str:
            """Convert camelCase/PascalCase to snake_case for comparison"""
            # Convert camelCase to snake_case
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        cleaned_queries = []
        removed_count = 0

        for query in parameterized_queries:
            # Get parameters (could be dict or list format)
            parameters = query.get('parameters', {})

            if not parameters:
                cleaned_queries.append(query)
                continue

            # Make a copy to avoid modifying original
            query_copy = query.copy()

            # Handle dict format: {"param_name": {"type": "date", ...}}
            if isinstance(parameters, dict):
                original_param_count = len(parameters)
                cleaned_params = {
                    name: spec for name, spec in parameters.items()
                    if normalize_param_name(name) not in timestamp_param_names
                }

                if len(cleaned_params) < original_param_count:
                    removed_count += original_param_count - len(cleaned_params)
                    query_copy['parameters'] = cleaned_params

            # Handle list format: [{"name": "...", "type": "date", ...}]
            elif isinstance(parameters, list):
                original_param_count = len(parameters)
                cleaned_params = [
                    p for p in parameters
                    if normalize_param_name(p.get('name', '')) not in timestamp_param_names
                ]

                if len(cleaned_params) < original_param_count:
                    removed_count += original_param_count - len(cleaned_params)
                    query_copy['parameters'] = cleaned_params

            cleaned_queries.append(query_copy)

        if removed_count > 0:
            logger.info(f"Removed {removed_count} timestamp parameters from parameterized queries")

        return cleaned_queries
