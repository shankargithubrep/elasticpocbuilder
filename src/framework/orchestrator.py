"""
Modular Demo Orchestrator
Orchestrates demo generation using the modular framework
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import json
from datetime import datetime

from .module_generator import ModuleGenerator
from .module_loader import ModuleLoader, DemoModuleManager
from .base import DemoConfig

logger = logging.getLogger(__name__)


class ModularDemoOrchestrator:
    """Orchestrates demo generation using modular architecture"""

    def __init__(self, llm_client=None, inference_endpoints: Optional[Dict[str, str]] = None):
        """Initialize orchestrator

        Args:
            llm_client: Optional LLM client for module generation
            inference_endpoints: Optional dict with 'rerank' and 'completion' endpoint IDs
        """
        # Create default client if not provided
        if llm_client is None:
            llm_client = self._create_default_client()

        self.llm_client = llm_client
        self.module_generator = ModuleGenerator(llm_client, inference_endpoints)
        self.module_manager = DemoModuleManager()

    def _create_default_client(self):
        """Create default LLM client"""
        import os
        from anthropic import Anthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            return Anthropic(api_key=api_key)
        else:
            logger.warning("No ANTHROPIC_API_KEY found, using None")
            return None

    def generate_new_demo(
        self,
        config: Dict[str, Any],
        progress_callback: Optional[callable] = None,
        conversation: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Generate a new demo module and execute it (Path 1: Query Planning + Specialized Generation)

        DEPRECATED: This method uses the older lightweight query planning approach
        and does not include LOOKUP JOIN index mode mapping.

        Use generate_new_demo_with_strategy() instead for:
        - Proper LOOKUP JOIN support (reference datasets as lookup indices)
        - Query-first strategy with comprehensive planning
        - All three query types (scripted, parameterized, RAG)

        Args:
            config: Demo configuration
            progress_callback: Optional progress callback
            conversation: Optional conversation history to save

        Returns:
            Demo results including module path
        """
        logger.warning(
            "DEPRECATED: generate_new_demo() (Path 1) is deprecated. "
            "Use generate_new_demo_with_strategy() (Path 2) instead for LOOKUP JOIN support."
        )
        # Step 0: Plan Queries (lightweight query planning)
        if progress_callback:
            progress_callback(0.05, "🎯 Planning queries and data structure...")

        query_plan = None
        try:
            from src.services.query_planner import LightweightQueryPlanner

            planner = LightweightQueryPlanner(self.llm_client)
            query_plan = planner.plan_queries(config)

            logger.info(f"Query plan created with {len(query_plan.get('query_plans', []))} queries")

        except Exception as e:
            logger.error(f"Query planning failed: {e}", exc_info=True)
            # Continue without query plan if planning fails
            query_plan = None

        # Step 1: Generate the module WITH query plan
        if progress_callback:
            progress_callback(0.1, "🤖 Generating custom demo module...")

        module_path = self.module_generator.generate_demo_module(config, query_plan=query_plan)

        # Step 2: Load and execute the module
        if progress_callback:
            progress_callback(0.3, "📦 Loading demo module...")

        loader = ModuleLoader(module_path)
        results = loader.execute_demo(progress_callback)

        # Add module information to results
        results['module_path'] = module_path
        results['module_name'] = Path(module_path).name

        # Step 3: Index Data in Elasticsearch
        if progress_callback:
            progress_callback(0.5, "🔍 Indexing data in Elasticsearch...")

        indexing_results = None
        try:
            from src.services.indexing_orchestrator import IndexingOrchestrator
            from src.services.elasticsearch_indexer import ElasticsearchIndexer

            indexer = ElasticsearchIndexer()
            indexing_orch = IndexingOrchestrator(indexer)

            # Get semantic fields from data generator
            data_gen = loader.load_data_generator()
            semantic_fields = {}
            if hasattr(data_gen, 'get_semantic_fields'):
                semantic_fields = data_gen.get_semantic_fields()

            indexing_results = indexing_orch.index_all_datasets(
                results['datasets'],
                semantic_fields,
                {},  # No index_modes from strategy in Path 1
                progress_callback
            )

            logger.info(f"Indexed {len(indexing_results)} datasets")

        except Exception as e:
            logger.error(f"Indexing failed: {e}", exc_info=True)

        # Step 4: Test and Fix Queries
        if indexing_results and progress_callback:
            progress_callback(0.7, "🧪 Testing and fixing queries...")

        query_test_results = None
        try:
            from src.services.query_test_runner import QueryTestRunner

            # Only test if indexing succeeded
            successful_indices = {
                name: result['index_name']
                for name, result in indexing_results.items()
                if result.get('status') == 'success'
            }

            if successful_indices:
                test_runner = QueryTestRunner(indexer, self.llm_client)
                query_test_results = test_runner.test_all_queries(
                    results.get('all_queries', results.get('queries', [])),
                    successful_indices,
                    max_attempts=3
                )

                logger.info(f"Query testing complete: {query_test_results['successfully_fixed']} fixed, {query_test_results['needs_manual_fix']} need manual fix")

                # Save test results to module
                self._save_query_test_results(module_path, query_test_results)
            else:
                logger.warning("No successful indices, skipping query testing")

        except Exception as e:
            logger.error(f"Query testing failed: {e}", exc_info=True)

        # Step 5: Cleanup Test Indices
        if indexing_results and progress_callback:
            progress_callback(0.85, "🧹 Cleaning up test indices...")

        try:
            if indexing_results:
                cleanup_count = 0
                for dataset_name, result in indexing_results.items():
                    if result.get('status') == 'success':
                        index_name = result['index_name']
                        try:
                            indexer.delete_index(index_name)
                            cleanup_count += 1
                            logger.info(f"Deleted test index: {index_name}")
                        except Exception as e:
                            logger.warning(f"Failed to delete test index {index_name}: {e}")

                logger.info(f"Cleaned up {cleanup_count}/{len(indexing_results)} test indices")
        except Exception as e:
            logger.error(f"Index cleanup failed: {e}", exc_info=True)
            # Don't fail the entire generation if cleanup fails

        # Step 6: Save conversation history if provided
        if conversation:
            if progress_callback:
                progress_callback(0.95, "💾 Saving conversation history...")
            self.save_conversation(module_path, conversation, config)

        logger.info(f"Demo generated and executed: {module_path}")

        return results

    def generate_new_demo_with_strategy(
        self,
        config: Dict[str, Any],
        progress_callback: Optional[callable] = None,
        conversation: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Generate demo using query-first strategy with validation

        Args:
            config: Demo configuration
            progress_callback: Optional progress callback
            conversation: Optional conversation history to save

        Returns:
            Demo results including module path and test results
        """
        results = {'phases': {}}

        # Phase 1: Generate Query Strategy (branch by demo_type)
        if progress_callback:
            progress_callback(0.05, "🎯 Planning query strategy...")

        demo_type = config.get('demo_type', 'analytics')  # Default to analytics
        logger.info(f"Generating demo with type: {demo_type}")

        if demo_type == 'search':
            from src.services.search_strategy_generator import SearchQueryStrategyGenerator
            strategy_generator = SearchQueryStrategyGenerator(self.llm_client)
        else:  # analytics
            from src.services.query_strategy_generator import QueryStrategyGenerator
            strategy_generator = QueryStrategyGenerator(self.llm_client)

        try:
            query_strategy = strategy_generator.generate_strategy(config)
            strategy_generator.validate_strategy(query_strategy)
            results['phases']['strategy'] = {
                'status': 'completed',
                'queries_planned': len(query_strategy.get('queries', [])),
                'datasets_planned': len(query_strategy.get('datasets', []))
            }
            logger.info(f"Query strategy generated: {len(query_strategy.get('queries', []))} queries")
        except Exception as e:
            logger.error(f"Strategy generation failed: {e}", exc_info=True)
            raise ValueError(f"Failed to generate query strategy: {e}")

        # Phase 2: Generate Data Module ONLY (queries will be generated AFTER profiling)
        if progress_callback:
            progress_callback(0.15, "🤖 Generating data module...")

        module_path = self.module_generator.generate_data_and_infrastructure_only(config, query_strategy)

        # Phase 3: Load and Execute Data Generation ONLY (queries come later in Phase 5!)
        if progress_callback:
            progress_callback(0.3, "📦 Generating datasets...")

        loader = ModuleLoader(module_path)

        # Only generate datasets, NOT queries yet
        data_generator = loader.load_data_generator()
        datasets = data_generator.generate_datasets()
        relationships = data_generator.get_relationships()
        data_descriptions = data_generator.get_data_descriptions()

        # Store dataset results
        results['datasets'] = datasets
        results['relationships'] = relationships
        results['data_descriptions'] = data_descriptions
        results['module_path'] = module_path
        results['module_name'] = Path(module_path).name
        results['query_strategy'] = query_strategy

        logger.info(f"Generated {len(datasets)} datasets (queries will be generated after profiling)")

        # Phase 4: Index Data in Elasticsearch (NEW)
        if progress_callback:
            progress_callback(0.5, "🔍 Indexing data in Elasticsearch...")

        indexing_results = None
        try:
            from src.services.indexing_orchestrator import IndexingOrchestrator
            from src.services.elasticsearch_indexer import ElasticsearchIndexer

            indexer = ElasticsearchIndexer()
            indexing_orch = IndexingOrchestrator(indexer)

            # Get semantic fields from data generator
            data_gen = loader.load_data_generator()
            semantic_fields = {}
            if hasattr(data_gen, 'get_semantic_fields'):
                semantic_fields = data_gen.get_semantic_fields()

            # PHASE 1: Detect datasets used in LOOKUP JOIN (must be lookup mode)
            lookup_join_datasets = self._detect_lookup_join_datasets(query_strategy)
            if lookup_join_datasets:
                logger.info(f"Detected {len(lookup_join_datasets)} datasets used in LOOKUP JOIN: {lookup_join_datasets}")

            # Extract index_mode mapping from query strategy
            # Prefer explicit index_mode field, fallback to type-based mapping
            index_modes = {}
            for dataset in query_strategy.get('datasets', []):
                dataset_name = dataset.get('name')

                # Check for explicit index_mode field (preferred)
                if 'index_mode' in dataset:
                    index_mode = dataset.get('index_mode')
                    logger.info(f"Dataset {dataset_name}: Using explicit index_mode={index_mode}")
                else:
                    # Fallback: Convert type to index_mode
                    dataset_type = dataset.get('type')

                    # Analytics demo types
                    if dataset_type == 'reference':
                        index_mode = 'lookup'
                    elif dataset_type == 'timeseries':
                        index_mode = 'data_stream'
                    # Search demo types
                    elif dataset_type in ['documents', 'records']:
                        index_mode = 'lookup'  # Search demos typically use lookup
                    else:
                        # Default to lookup (safer than data_stream)
                        index_mode = 'lookup'
                        logger.warning(f"Dataset {dataset_name}: Unknown type '{dataset_type}', defaulting to index_mode=lookup")

                    logger.info(f"Dataset {dataset_name} (type={dataset_type}) -> index_mode={index_mode}")

                # PHASE 1: Override if dataset is used in LOOKUP JOIN
                if dataset_name in lookup_join_datasets:
                    if index_mode != 'lookup':
                        logger.warning(
                            f"Dataset {dataset_name} is used in LOOKUP JOIN but has index_mode={index_mode}. "
                            f"Forcing to index_mode=lookup to prevent indexing failure."
                        )
                        index_mode = 'lookup'
                    else:
                        logger.info(f"Dataset {dataset_name}: Confirmed as lookup (used in LOOKUP JOIN)")

                if dataset_name:
                    index_modes[dataset_name] = index_mode

            indexing_results = indexing_orch.index_all_datasets(
                datasets,  # ← Changed from exec_results['datasets']
                semantic_fields,
                index_modes,
                progress_callback
            )

            results['phases']['indexing'] = indexing_results
            logger.info(f"Indexed {len(indexing_results)} datasets")

        except Exception as e:
            logger.error(f"Indexing failed: {e}", exc_info=True)
            results['phases']['indexing'] = {'status': 'failed', 'error': str(e)}

        # Phase 4.5: Profile Indexed Data (NEW)
        if indexing_results and progress_callback:
            progress_callback(0.6, "🔍 Profiling indexed data...")

        data_profile = None
        try:
            from src.services.data_profiler import profile_indexed_data
            from src.services.elasticsearch_indexer import ElasticsearchIndexer

            # Only profile if indexing succeeded
            successful_indices = {
                name: result['index_name']
                for name, result in indexing_results.items()
                if result.get('status') == 'success'
            }

            if successful_indices:
                es_client = ElasticsearchIndexer()
                demo_path_obj = Path(module_path)

                # Profile the indexed datasets
                data_profile = profile_indexed_data(
                    es_client,
                    datasets,  # ← Changed from exec_results['datasets']
                    demo_path_obj,
                    index_name_map=successful_indices,  # Pass the actual index names
                    progress_callback=None  # Don't need sub-progress for this
                )

                results['phases']['profiling'] = {
                    'status': 'completed',
                    'datasets_profiled': len(data_profile.get('datasets', {}))
                }
                logger.info(f"Data profiling complete: {len(data_profile.get('datasets', {}))} datasets profiled")
            else:
                logger.warning("No successful indices, skipping data profiling")
                results['phases']['profiling'] = {'status': 'skipped', 'reason': 'no_indexed_data'}

        except Exception as e:
            logger.error(f"Data profiling failed: {e}", exc_info=True)
            results['phases']['profiling'] = {'status': 'failed', 'error': str(e)}
            # Don't fail the entire generation if profiling fails

        # Phase 5: Generate Query Module (NOW with data profile!)
        if progress_callback:
            progress_callback(0.65, "🔧 Generating queries with data profile...")

        try:
            self.module_generator.generate_query_module_with_profile(
                module_path,
                config,
                query_strategy,
                data_profile=data_profile
            )
            results['phases']['query_generation'] = {'status': 'completed'}
            logger.info(f"Query module generated with data profile")

            # Reload module to get the new queries
            loader = ModuleLoader(module_path)
            query_gen = loader.load_query_generator(datasets)  # ← Changed from exec_results['datasets']

            # Load all three query types
            scripted_queries = query_gen.generate_queries()
            parameterized_queries = query_gen.generate_parameterized_queries()
            rag_queries = query_gen.generate_rag_queries()

            # Combine all queries
            all_queries = scripted_queries + parameterized_queries + rag_queries

            # Store queries with type breakdown
            results['all_queries'] = all_queries
            results['queries'] = all_queries  # For backward compatibility
            results['scripted_queries'] = scripted_queries  # Only these get tested
            results['parameterized_queries'] = parameterized_queries
            results['rag_queries'] = rag_queries

            logger.info(f"Loaded {len(all_queries)} total queries: "
                       f"{len(scripted_queries)} scripted, "
                       f"{len(parameterized_queries)} parameterized, "
                       f"{len(rag_queries)} RAG")

        except Exception as e:
            logger.error(f"Query module generation failed: {e}", exc_info=True)
            results['phases']['query_generation'] = {'status': 'failed', 'error': str(e)}
            # Don't fail the entire generation if query generation fails
            all_queries = []
            scripted_queries = []
            parameterized_queries = []
            rag_queries = []
            # Initialize results keys even when query generation fails
            results['queries'] = []
            results['scripted_queries'] = []
            results['parameterized_queries'] = []
            results['rag_queries'] = []

        # Phase 6: Test and Fix Queries
        if indexing_results and progress_callback:
            progress_callback(0.75, "🧪 Testing and fixing queries...")

        query_test_results = None
        try:
            from src.services.query_test_runner import QueryTestRunner

            # Only test if indexing succeeded
            successful_indices = {
                name: result['index_name']
                for name, result in indexing_results.items()
                if result.get('status') == 'success'
            }

            # Only test scripted queries (parameterized/RAG queries have parameters)
            if successful_indices and scripted_queries:
                test_runner = QueryTestRunner(indexer, self.llm_client, data_profile=data_profile)
                query_test_results = test_runner.test_all_queries(
                    scripted_queries,
                    successful_indices,
                    max_attempts=3
                )

                results['phases']['query_testing'] = query_test_results
                logger.info(f"Query testing complete: {query_test_results['successfully_fixed']} fixed, {query_test_results['needs_manual_fix']} need manual fix")

                # Save test results to module
                self._save_query_test_results(module_path, query_test_results)
            else:
                logger.warning("No successful indices, skipping query testing")
                results['phases']['query_testing'] = {'status': 'skipped', 'reason': 'no_indexed_data'}

        except Exception as e:
            logger.error(f"Query testing failed: {e}", exc_info=True)
            results['phases']['query_testing'] = {'status': 'failed', 'error': str(e)}

        # Phase 7: Cleanup Test Indices
        if indexing_results and progress_callback:
            progress_callback(0.85, "🧹 Cleaning up test indices...")

        try:
            if indexing_results:
                cleanup_count = 0
                for dataset_name, result in indexing_results.items():
                    if result.get('status') == 'success':
                        index_name = result['index_name']
                        try:
                            indexer.delete_index(index_name)
                            cleanup_count += 1
                            logger.info(f"Deleted test index: {index_name}")
                        except Exception as e:
                            logger.warning(f"Failed to delete test index {index_name}: {e}")

                logger.info(f"Cleaned up {cleanup_count}/{len(indexing_results)} test indices")
                results['phases']['cleanup'] = {'status': 'completed', 'indices_deleted': cleanup_count}
        except Exception as e:
            logger.error(f"Index cleanup failed: {e}", exc_info=True)
            results['phases']['cleanup'] = {'status': 'failed', 'error': str(e)}
            # Don't fail the entire generation if cleanup fails

        # Phase 8: Save conversation history if provided
        if conversation:
            if progress_callback:
                progress_callback(0.95, "💾 Saving conversation history...")
            self.save_conversation(module_path, conversation, config)

        logger.info(f"Demo with strategy generated and executed: {module_path}")

        return results

    def _save_query_test_results(self, module_path: str, test_results: Dict) -> None:
        """Save query test results to module folder

        Args:
            module_path: Path to the demo module
            test_results: Query test results dictionary
        """
        try:
            test_results_file = Path(module_path) / 'query_testing_results.json'
            test_results_file.write_text(json.dumps(test_results, indent=2))
            logger.info(f"Saved query test results to {test_results_file}")

            # Also update config.json with summary
            config_file = Path(module_path) / 'config.json'
            if config_file.exists():
                config_data = json.loads(config_file.read_text())
                config_data['query_testing'] = {
                    'enabled': True,
                    'queries_fixed': test_results.get('successfully_fixed', 0),
                    'queries_need_manual_fix': test_results.get('needs_manual_fix', 0),
                    'total_tested': test_results.get('total_queries', 0),
                    'tested_at': test_results.get('tested_at')
                }
                config_file.write_text(json.dumps(config_data, indent=2))
                logger.info("Updated config.json with test summary")

        except Exception as e:
            logger.error(f"Failed to save query test results: {e}", exc_info=True)
            # Don't fail the entire generation if save fails

    def _detect_lookup_join_datasets(self, query_strategy: Dict[str, Any]) -> set:
        """Detect datasets used in LOOKUP JOIN operations

        Args:
            query_strategy: Query strategy dictionary containing queries

        Returns:
            Set of dataset names used in LOOKUP JOIN operations
        """
        import re

        lookup_datasets = set()

        # Parse all queries in the strategy
        for query in query_strategy.get('queries', []):
            esql_query = query.get('esql') or query.get('esql_query') or query.get('query') or ''
            esql_upper = esql_query.upper()

            # Check if this query contains LOOKUP JOIN
            if 'LOOKUP JOIN' in esql_upper or 'LOOKUP  JOIN' in esql_upper:
                # Extract dataset name after LOOKUP JOIN
                # Pattern: ... LOOKUP JOIN dataset_name ON ...
                # Handle single or double spaces between LOOKUP and JOIN
                matches = re.findall(r'LOOKUP\s+JOIN\s+(\w+)', esql_upper)
                for match in matches:
                    dataset_name = match.lower()
                    lookup_datasets.add(dataset_name)
                    logger.debug(f"Found LOOKUP JOIN on dataset: {dataset_name}")

        return lookup_datasets

    def save_conversation(
        self,
        module_path: str,
        conversation: List[Dict],
        config: Dict[str, Any]
    ) -> None:
        """Save conversation history to demo module folder

        Args:
            module_path: Path to the demo module
            conversation: List of conversation messages
            config: Demo configuration context
        """
        try:
            conversation_file = Path(module_path) / 'conversation.json'
            conversation_data = {
                'messages': conversation,
                'context': config,
                'created_at': datetime.now().isoformat()
            }
            conversation_file.write_text(json.dumps(conversation_data, indent=2))
            logger.info(f"Saved conversation history to {conversation_file}")
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}", exc_info=True)
            # Don't fail the entire generation if conversation save fails

    def execute_existing_demo(
        self,
        module_name: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Execute an existing demo module

        Args:
            module_name: Name of the module to execute
            progress_callback: Optional progress callback

        Returns:
            Demo results
        """
        loader = self.module_manager.get_module(module_name)

        if loader is None:
            raise ValueError(f"Module '{module_name}' not found")

        results = loader.execute_demo(progress_callback)
        results['module_name'] = module_name

        return results

    def list_available_demos(self) -> list:
        """List all available demo modules

        Returns:
            List of available demos
        """
        return self.module_manager.list_modules()

    def regenerate_module_component(
        self,
        module_name: str,
        component: str,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Regenerate a specific component of an existing module

        Args:
            module_name: Name of the module
            component: Component to regenerate ('data', 'queries', 'guide')
            config: Optional updated configuration

        Returns:
            True if successful
        """
        loader = self.module_manager.get_module(module_name)

        if loader is None:
            raise ValueError(f"Module '{module_name}' not found")

        # Load existing config if not provided
        if config is None:
            config = loader.config.get('customer_context', {})

        module_path = Path(loader.module_path)

        # Regenerate the specific component
        if component == 'data':
            self.module_generator._generate_data_module(config, module_path)
        elif component == 'queries':
            self.module_generator._generate_query_module(config, module_path)
        elif component == 'guide':
            self.module_generator._generate_guide_module(config, module_path)
        else:
            raise ValueError(f"Unknown component: {component}")

        logger.info(f"Regenerated {component} for module {module_name}")
        return True

    def export_module(self, module_name: str, export_path: str) -> str:
        """Export a demo module as a standalone package

        Args:
            module_name: Name of the module to export
            export_path: Path where to export

        Returns:
            Path to exported package
        """
        import shutil
        import json

        loader = self.module_manager.get_module(module_name)

        if loader is None:
            raise ValueError(f"Module '{module_name}' not found")

        # Create export directory
        export_dir = Path(export_path) / module_name
        export_dir.mkdir(parents=True, exist_ok=True)

        # Copy module files
        shutil.copytree(loader.module_path, export_dir, dirs_exist_ok=True)

        # Add README
        readme_content = f"""# Demo Module: {module_name}

## Customer Context
{json.dumps(loader.config.get('customer_context', {}), indent=2)}

## Components
- `data_generator.py`: Generates demo datasets
- `query_generator.py`: Creates ES|QL queries
- `demo_guide.py`: Produces demo guide and talk track
- `config.json`: Module configuration

## Usage
```python
from src.framework.module_loader import ModuleLoader

loader = ModuleLoader('{module_name}')
results = loader.execute_demo()
```

## Customization
Each component can be edited independently to refine the demo.
"""

        (export_dir / 'README.md').write_text(readme_content)

        logger.info(f"Exported module to {export_dir}")
        return str(export_dir)


# Convenience functions for common operations

def create_demo(config: Dict[str, Any], llm_client=None) -> Dict[str, Any]:
    """Create a new demo module

    Args:
        config: Demo configuration
        llm_client: Optional LLM client

    Returns:
        Demo results
    """
    orchestrator = ModularDemoOrchestrator(llm_client)
    return orchestrator.generate_new_demo(config)


def run_demo(module_name: str) -> Dict[str, Any]:
    """Run an existing demo module

    Args:
        module_name: Name of the demo module

    Returns:
        Demo results
    """
    orchestrator = ModularDemoOrchestrator()
    return orchestrator.execute_existing_demo(module_name)


def list_demos() -> list:
    """List all available demos

    Returns:
        List of demo modules
    """
    orchestrator = ModularDemoOrchestrator()
    return orchestrator.list_available_demos()