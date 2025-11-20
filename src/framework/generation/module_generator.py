"""
Slim Module Generator - Orchestrator using extracted templates and utilities

This is a refactored version of the original 3,428-line module_generator.py.
It maintains the same public API but delegates to extracted components:
- Templates in src/framework/generation/templates/
- Utilities in src/framework/generation/generators/

The orchestrator focuses on high-level workflow coordination while the
actual prompt generation, code extraction, and file generation is handled
by specialized modules.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# Import extracted template modules
from src.framework.generation.templates import (
    # Data generator templates
    get_analytics_data_generator_template,
    get_search_data_generator_template,
    get_simple_data_generator_template,

    # Query generator templates
    get_scripted_queries_prompt,
    get_parameterized_queries_prompt,
    get_rag_queries_prompt,
    get_query_module_wrapper,

    # Guide templates
    get_demo_guide_prompt,
    get_demo_guide_module_template,
    get_fallback_demo_guide,

    # Agent metadata templates
    get_agent_instructions_prompt,
    get_agent_metadata_template,
    get_fallback_agent_instructions,
    generate_agent_id,
    generate_avatar_symbol,
    get_agent_avatar_color_by_type
)

# Import extracted utility modules
from src.framework.generation.generators import (
    StaticFileGenerator,
    ConfigGenerator,
    CodeExtractor
)

logger = logging.getLogger(__name__)


class ModuleGenerator:
    """Orchestrates demo module generation using LLM and extracted components

    This slim orchestrator coordinates the generation workflow while delegating
    template generation, code extraction, and file I/O to specialized components.

    Public API (maintain backward compatibility):
    - generate_demo_module(config, query_plan)
    - generate_demo_module_with_strategy(config, query_strategy)
    - generate_data_and_infrastructure_only(config, query_strategy)
    - generate_query_module_with_profile(module_path, config, query_strategy, data_profile)
    """

    def __init__(self, llm_client=None, inference_endpoints: Optional[Dict[str, str]] = None):
        """Initialize with LLM client and inference endpoint configuration

        Args:
            llm_client: LLM client for code generation
            inference_endpoints: Dict with 'rerank' and 'completion' endpoint IDs
                Default: {'rerank': '.rerank-v1-elasticsearch', 'completion': 'completion-vulcan'}
        """
        self.llm_client = llm_client
        self.base_path = Path("demos")  # Where demo modules are stored

        # Set inference endpoint defaults
        if inference_endpoints is None:
            inference_endpoints = {
                "rerank": ".rerank-v1-elasticsearch",
                "completion": "completion-vulcan"
            }
        self.inference_endpoints = inference_endpoints

    # ========================================================================
    # PUBLIC API - Main entry points (maintain exact signatures)
    # ========================================================================

    def generate_demo_module(self, config: Dict[str, Any], query_plan: Optional[Dict[str, Any]] = None) -> str:
        """Generate a complete demo module for a customer

        Args:
            config: Demo configuration with customer context
            query_plan: Optional query plan with field requirements (from LightweightQueryPlanner)

        Returns:
            Path to the generated module directory
        """
        # Create unique module name and directory
        module_path = self._create_module_directory(config)

        # If query_plan provided, use requirements-based generation
        if query_plan:
            logger.info("Using query plan for coordinated data/query generation")

            # Save query plan
            plan_file = module_path / 'query_plan.json'
            plan_file.write_text(json.dumps(query_plan, indent=2))
            logger.info("Saved query_plan.json")

            # Extract field requirements from query plan
            from src.services.query_planner import LightweightQueryPlanner
            planner = LightweightQueryPlanner(self.llm_client)
            data_requirements = planner.extract_field_requirements(query_plan)

            # Generate each component with field requirements
            self._generate_data_module_with_requirements(config, module_path, data_requirements)
            self._generate_query_module_with_plan(config, module_path, query_plan)
            self._generate_guide_module(config, module_path)
            ConfigGenerator.generate_config_file(config, module_path)
        else:
            logger.info("Using original data-first generation (no query plan)")
            # Generate each component (Python modules) - original flow
            self._generate_data_module(config, module_path)
            self._generate_query_module(config, module_path)
            self._generate_guide_module(config, module_path)
            ConfigGenerator.generate_config_file(config, module_path)

        # Generate static files for quick loading (must happen before agent metadata)
        StaticFileGenerator.generate_static_files(module_path)

        # Generate agent metadata AFTER static files (needs queries.json)
        logger.info(">>> About to call _generate_agent_metadata() from generate_demo_module()")
        self._generate_agent_metadata(config, module_path)
        logger.info(">>> Returned from _generate_agent_metadata()")

        logger.info(f"Generated demo module at: {module_path}")
        return str(module_path)

    def generate_demo_module_with_strategy(self, config: Dict[str, Any], query_strategy: Dict[str, Any]) -> str:
        """Generate a complete demo module using query-first strategy

        Args:
            config: Demo configuration with customer context
            query_strategy: Pre-generated query strategy with data requirements

        Returns:
            Path to the generated module directory
        """
        # Create unique module name and directory
        module_path = self._create_module_directory(config)

        # Save query strategy
        strategy_file = module_path / 'query_strategy.json'
        strategy_file.write_text(json.dumps(query_strategy, indent=2))
        logger.info("Saved query_strategy.json")

        # Extract data requirements from strategy
        from src.services.query_strategy_generator import QueryStrategyGenerator
        strategy_gen = QueryStrategyGenerator(self.llm_client)
        data_requirements = strategy_gen.extract_data_requirements(query_strategy)

        # Generate each component with strategy
        self._generate_data_module_with_requirements(config, module_path, data_requirements)
        self._generate_query_module_with_strategy(config, module_path, query_strategy)
        self._generate_guide_module(config, module_path)
        ConfigGenerator.generate_config_file(config, module_path)

        # Generate static files for quick loading (must happen before agent metadata)
        StaticFileGenerator.generate_static_files(module_path)

        # Generate agent metadata AFTER static files (needs queries.json)
        logger.info(">>> About to call _generate_agent_metadata() from generate_demo_module_with_strategy()")
        self._generate_agent_metadata(config, module_path)
        logger.info(">>> Returned from _generate_agent_metadata()")

        logger.info(f"Generated demo module with strategy at: {module_path}")
        return str(module_path)

    def generate_data_and_infrastructure_only(self, config: Dict[str, Any], query_strategy: Dict[str, Any]) -> str:
        """Generate module infrastructure and data generator only (NO QUERIES YET)

        This is Phase 1 of the split generation workflow. Query generation happens later
        after data is indexed and profiled.

        Args:
            config: Demo configuration with customer context
            query_strategy: Pre-generated query strategy with data requirements

        Returns:
            Path to the generated module directory (ready for data generation)
        """
        # Create unique module name and directory
        module_path = self._create_module_directory(config)

        # Save query strategy
        strategy_file = module_path / 'query_strategy.json'
        strategy_file.write_text(json.dumps(query_strategy, indent=2))
        logger.info("Saved query_strategy.json")

        # Extract data requirements from strategy
        from src.services.query_strategy_generator import QueryStrategyGenerator
        strategy_gen = QueryStrategyGenerator(self.llm_client)
        data_requirements = strategy_gen.extract_data_requirements(query_strategy)

        # Generate ONLY data module and supporting files (NO QUERIES)
        self._generate_data_module_with_requirements(config, module_path, data_requirements)
        self._generate_guide_module(config, module_path)
        ConfigGenerator.generate_config_file(config, module_path)

        # NOTE: Do NOT generate static files yet - query_generator.py doesn't exist
        # Static files will be generated in Phase 2 after query_generator.py is created

        logger.info(f"Generated module infrastructure and data at: {module_path} (queries will be generated after profiling)")
        return str(module_path)

    def generate_query_module_with_profile(self, module_path: str, config: Dict[str, Any],
                                          query_strategy: Dict[str, Any],
                                          data_profile: Optional[Dict[str, Any]] = None) -> None:
        """Generate query module using actual profiled data (Phase 2 of split workflow)

        This method is called AFTER data is generated, indexed, and profiled.
        It uses the data profile to generate queries with accurate field names and values.

        Args:
            module_path: Path to existing module directory
            config: Demo configuration
            query_strategy: Query strategy (for context)
            data_profile: Profiled data from Elasticsearch (field names, values, combinations)
        """
        logger.info("="*60)
        logger.info("PHASE 5: Starting query module generation with profile")
        logger.info("="*60)

        module_path_obj = Path(module_path)

        if not module_path_obj.exists():
            logger.error(f"Module path does not exist: {module_path}")
            raise ValueError(f"Module path does not exist: {module_path}")

        logger.info(f"Module path: {module_path}")
        logger.info(f"Data profile present: {data_profile is not None}")
        if data_profile:
            logger.info(f"Data profile datasets: {list(data_profile.get('datasets', {}).keys())}")

        try:
            # Generate query module WITH data profile
            logger.info("Calling _generate_query_module_with_strategy...")
            self._generate_query_module_with_strategy(
                config,
                module_path_obj,
                query_strategy,
                data_profile=data_profile
            )
            logger.info("✓ Query module generation completed successfully")
        except Exception as e:
            logger.error(f"✗ Query module generation failed: {e}", exc_info=True)
            raise

        logger.info(f"Generated query module with data profile at: {module_path}")

        # NOW generate static files - all modules are complete (data, guide, AND queries)
        StaticFileGenerator.generate_static_files(module_path_obj)

    # ========================================================================
    # INTERNAL METHODS - Generation workflow coordination
    # ========================================================================

    def _create_module_directory(self, config: Dict[str, Any]) -> Path:
        """Create unique module directory with standard structure

        Args:
            config: Demo configuration

        Returns:
            Path to created module directory
        """
        # Create unique module name with defensive handling for None values
        company_name = config.get('company_name') or 'demo'
        company_slug = company_name.lower().replace(' ', '_')

        department = config.get('department') or 'general'
        department_slug = department.lower().replace(' ', '_')

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        module_name = f"{company_slug}_{department_slug}_{timestamp}"
        module_path = self.base_path / module_name

        # Create module directory structure
        module_path.mkdir(parents=True, exist_ok=True)
        (module_path / '__init__.py').touch()

        logger.info(f"Created module directory: {module_path}")
        return module_path

    def _generate_data_module(self, config: Dict[str, Any], module_path: Path):
        """Generate the data generation module (original flow without requirements)

        Uses LLM to generate custom data generator based on customer context.
        Chooses between analytics and search templates based on demo_type.
        """
        demo_type = config.get('demo_type', 'analytics')

        # Get size preference for prompting
        size_preference = config.get('dataset_size_preference', 'medium')

        logger.info(f"Generating data module for {demo_type} demo (size: {size_preference})")

        # Build context for template
        template_config = {
            **config,
            'size_preference': size_preference
        }

        # Choose template based on demo type
        if demo_type == 'search':
            template = get_search_data_generator_template(template_config)
        else:
            template = get_analytics_data_generator_template(template_config)

        # If LLM available, enhance the template with customer-specific code
        if self.llm_client:
            prompt = self._build_data_generation_prompt(config, template, size_preference)
            code = self._call_llm(prompt)
            code = CodeExtractor.extract_python_code(code)
        else:
            # Use template as-is for mock generation
            logger.warning("No LLM client - using template as-is")
            code = template

        # Validate and save
        CodeExtractor.validate_python_syntax(code, 'data_generator.py')

        output_file = module_path / 'data_generator.py'
        output_file.write_text(code)
        logger.info(f"Generated data_generator.py")

    def _generate_data_module_with_requirements(self, config: Dict[str, Any],
                                                 module_path: Path,
                                                 data_requirements: Dict):
        """Generate data module based on query strategy requirements

        Args:
            config: Demo configuration
            module_path: Path to module directory
            data_requirements: Data requirements extracted from query strategy
        """
        from src.services.query_strategy_generator import QueryStrategyGenerator
        strategy_gen = QueryStrategyGenerator(self.llm_client)
        formatted_requirements = strategy_gen.get_field_info_for_prompts(data_requirements)

        demo_type = config.get('demo_type', 'analytics')
        size_preference = config.get('dataset_size_preference', 'medium')

        logger.info(f"Generating data module with requirements for {demo_type} demo")

        # Get base template
        template_config = {
            **config,
            'size_preference': size_preference
        }

        if demo_type == 'search':
            base_template = get_search_data_generator_template(template_config)
        else:
            base_template = get_analytics_data_generator_template(template_config)

        # Build enhanced prompt with requirements
        prompt = self._build_data_generation_with_requirements_prompt(
            config, base_template, formatted_requirements, size_preference
        )

        # Generate code
        if self.llm_client:
            code = self._call_llm(prompt)
            code = CodeExtractor.extract_python_code(code)
        else:
            logger.warning("No LLM client - using template with placeholder requirements")
            code = base_template

        # Validate and save
        CodeExtractor.validate_python_syntax(code, 'data_generator.py')

        output_file = module_path / 'data_generator.py'
        output_file.write_text(code)
        logger.info(f"Generated data_generator.py with requirements")

    def _generate_query_module(self, config: Dict[str, Any], module_path: Path):
        """Generate query module (original flow without query plan)

        Generates all three query types (scripted, parameterized, RAG) using LLM.
        """
        logger.info("Generating query module (original flow)")

        # Get ES|QL documentation
        esql_docs = self._get_minimal_esql_reference()

        # Generate each query type using template prompts
        scripted_code = self._generate_scripted_queries(config, esql_docs)
        parameterized_code = self._generate_parameterized_queries(config, esql_docs)
        rag_code = self._generate_rag_queries(config, esql_docs)

        # Combine into single module
        query_module = get_query_module_wrapper(
            config=config,
            scripted_method=scripted_code,
            parameterized_method=parameterized_code,
            rag_method=rag_code
        )

        # Validate and save
        CodeExtractor.validate_python_syntax(query_module, 'query_generator.py')
        method_validation = CodeExtractor.validate_query_module_methods(query_module)

        if not all(method_validation.values()):
            logger.warning(f"Some query methods missing: {method_validation}")

        output_file = module_path / 'query_generator.py'
        output_file.write_text(query_module)
        logger.info(f"Generated query_generator.py")

    def _generate_query_module_with_plan(self, config: Dict[str, Any], module_path: Path, query_plan: Dict):
        """Generate query module using pre-planned query requirements

        Args:
            config: Demo configuration
            module_path: Path to module directory
            query_plan: Query plan with field requirements
        """
        logger.info("Generating query module with query plan")

        # Get ES|QL documentation
        esql_docs = self._get_minimal_esql_reference()

        # Get schema context from query plan
        schema_context = self._format_schema_from_plan(query_plan)

        # Generate each query type with schema awareness
        scripted_code = self._generate_scripted_queries_with_schema(
            config, esql_docs, schema_context, query_plan
        )
        parameterized_code = self._generate_parameterized_queries_with_schema(
            config, esql_docs, schema_context, query_plan
        )
        rag_code = self._generate_rag_queries_with_schema(
            config, esql_docs, schema_context, query_plan
        )

        # Combine into single module
        query_module = get_query_module_wrapper(
            config=config,
            scripted_method=scripted_code,
            parameterized_method=parameterized_code,
            rag_method=rag_code
        )

        # Validate and save
        CodeExtractor.validate_python_syntax(query_module, 'query_generator.py')

        output_file = module_path / 'query_generator.py'
        output_file.write_text(query_module)
        logger.info(f"Generated query_generator.py with plan")

    def _generate_query_module_with_strategy(self, config: Dict[str, Any],
                                             module_path: Path,
                                             query_strategy: Dict,
                                             data_profile: Optional[Dict[str, Any]] = None):
        """Generate query module using pre-planned query strategy

        NEW APPROACH: Saves queries to all_queries.json and generates simple loader methods.
        No LLM call needed - uses query_strategy directly.

        Args:
            config: Demo configuration
            module_path: Path to module directory
            query_strategy: Complete query strategy with planned queries
            data_profile: Optional profiled data from Elasticsearch (field names, values, combinations)
        """
        logger.info("→ Generating query module with JSON loader approach")
        logger.info(f"  Config keys: {list(config.keys())}")
        logger.info(f"  Query strategy has {len(query_strategy.get('queries', []))} queries")

        # Extract and categorize queries from strategy
        all_queries = query_strategy.get('queries', [])

        # Categorize by query_type
        scripted_queries = [q for q in all_queries if q.get('query_type') == 'scripted']
        parameterized_queries = [q for q in all_queries if q.get('query_type') == 'parameterized']
        rag_queries = [q for q in all_queries if q.get('query_type') == 'rag']

        logger.info(f"  Categorized: {len(scripted_queries)} scripted, "
                   f"{len(parameterized_queries)} parameterized, {len(rag_queries)} rag")

        # Save all queries to all_queries.json BEFORE generating Python module
        all_queries_data = {
            'scripted': scripted_queries,
            'parameterized': parameterized_queries,
            'rag': rag_queries,
            'all': all_queries
        }

        all_queries_file = module_path / 'all_queries.json'
        all_queries_file.write_text(json.dumps(all_queries_data, indent=2))
        logger.info(f"  Saved all_queries.json")

        # Generate simple query_generator.py with JSON loader methods
        self._generate_json_loader_query_module(config, module_path)

    def _generate_json_loader_query_module(self, config: Dict[str, Any], module_path: Path):
        """Generate a simple query module that loads queries from all_queries.json

        This is used in the strategy-based workflow where queries are pre-generated
        and saved to JSON. The Python module just needs to load and return them.
        """
        import re
        company_class = re.sub(r'[^a-zA-Z0-9_]', '', config['company_name'].replace(' ', ''))

        code = f"""from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd
import json
from pathlib import Path

class {company_class}QueryGenerator(QueryGeneratorModule):
    \"\"\"Query generator for {config['company_name']} - {config['department']}

    Loads pre-generated queries from all_queries.json
    \"\"\"

    def __init__(self, config: DemoConfig, datasets: Dict[str, Any]):
        super().__init__(config, datasets)
        self._queries = self._load_queries()

    def _load_queries(self) -> Dict[str, List[Dict[str, Any]]]:
        \"\"\"Load queries from all_queries.json\"\"\"
        queries_file = Path(__file__).parent / 'all_queries.json'

        if queries_file.exists():
            with open(queries_file, 'r') as f:
                return json.load(f)

        return {{'scripted': [], 'parameterized': [], 'rag': [], 'all': []}}

    def generate_queries(self) -> List[Dict[str, Any]]:
        \"\"\"Return scripted queries\"\"\"
        return self._queries.get('scripted', [])

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        \"\"\"Return parameterized queries\"\"\"
        return self._queries.get('parameterized', [])

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        \"\"\"Return RAG queries\"\"\"
        return self._queries.get('rag', [])

    def get_query_progression(self) -> List[str]:
        \"\"\"Define the order to present queries for maximum impact\"\"\"
        # Use the order from all queries
        all_queries = self._queries.get('all', [])
        return [q.get('name', f'Query {{i+1}}') for i, q in enumerate(all_queries)]
"""

        output_file = module_path / 'query_generator.py'
        output_file.write_text(code)
        logger.info(f"Generated JSON loader query_generator.py")

    def _generate_guide_module(self, config: Dict[str, Any], module_path: Path):
        """Generate the demo guide module

        Uses fixed template since structure is always the same - only content varies.
        Content is dynamically generated from config/datasets/queries at runtime.
        """
        # Sanitize company name for use as Python class name
        import re
        company_class = re.sub(r'[^a-zA-Z0-9_]', '', config['company_name'].replace(' ', ''))

        # Generate comprehensive demo guide content using LLM
        guide_content = self._generate_demo_guide_content(config, module_path)

        # Use template to wrap content
        code = get_demo_guide_module_template(
            company_class=company_class,
            company_name=config['company_name'],
            department=config['department'],
            guide_content=guide_content
        )

        output_file = module_path / 'demo_guide.py'
        output_file.write_text(code)
        logger.info(f"Generated demo_guide.py")

    def _generate_agent_metadata(self, config: Dict[str, Any], module_path: Path):
        """Generate agent metadata for Elastic Assistant integration

        Creates tool_metadata.json with agent configuration, instructions,
        and example queries for the Elastic Assistant.
        """
        logger.info("="*60)
        logger.info("Generating agent metadata")
        logger.info("="*60)

        # Try to load queries from all_queries.json first (new approach)
        all_queries_file = module_path / 'all_queries.json'
        queries_file = module_path / 'queries.json'  # Fallback

        query_descriptions = []

        if all_queries_file.exists():
            logger.info("Loading queries from all_queries.json")
            try:
                with open(all_queries_file, 'r') as f:
                    all_queries_data = json.load(f)
                    queries = all_queries_data.get('all', [])
                    query_descriptions = [
                        f"{q.get('name', 'Query')}: {q.get('description', 'No description')}"
                        for q in queries
                    ]
                    logger.info(f"Found {len(query_descriptions)} queries in all_queries.json")
            except Exception as e:
                logger.warning(f"Failed to load all_queries.json: {e}")

        elif queries_file.exists():
            logger.info("Loading queries from queries.json (fallback)")
            try:
                with open(queries_file, 'r') as f:
                    queries = json.load(f)
                    query_descriptions = [
                        f"{q.get('name', 'Query')}: {q.get('description', 'No description')}"
                        for q in queries
                    ]
                    logger.info(f"Found {len(query_descriptions)} queries in queries.json")
            except Exception as e:
                logger.warning(f"Failed to load queries.json: {e}")
        else:
            logger.warning("No queries file found - using fallback descriptions")

        # Get dataset info from config
        datasets_info = [
            f"{config.get('company_name', 'Company')} data includes relevant business metrics"
        ]

        # Generate agent instructions using LLM
        if self.llm_client and query_descriptions:
            agent_instructions = self._generate_agent_instructions(
                config, query_descriptions, datasets_info
            )
        else:
            logger.warning("Using fallback agent instructions")
            agent_instructions = get_fallback_agent_instructions(config)

        # Generate metadata using template
        metadata = get_agent_metadata_template(
            config=config,
            agent_instructions=agent_instructions,
            query_descriptions=query_descriptions,
            inference_endpoints=self.inference_endpoints
        )

        # Save to tool_metadata.json
        metadata_file = module_path / 'tool_metadata.json'
        metadata_file.write_text(json.dumps(metadata, indent=2))
        logger.info(f"Generated tool_metadata.json")

    # ========================================================================
    # HELPER METHODS - Prompt building and LLM interaction
    # ========================================================================

    def _build_data_generation_prompt(self, config: Dict[str, Any],
                                      template: str,
                                      size_preference: str) -> str:
        """Build prompt for data generation (no requirements)"""
        size_ranges = {
            'small': {
                'timeseries_max': 5000,
                'timeseries_typical': '1000-3000',
                'reference_max': 500,
                'reference_typical': '50-200'
            },
            'medium': {
                'timeseries_max': 15000,
                'timeseries_typical': '5000-10000',
                'reference_max': 2000,
                'reference_typical': '200-1000'
            },
            'large': {
                'timeseries_max': 50000,
                'timeseries_typical': '15000-30000',
                'reference_max': 5000,
                'reference_typical': '500-2000'
            }
        }

        ranges = size_ranges.get(size_preference, size_ranges['medium'])

        prompt = f"""Generate a Python module that implements DataGeneratorModule for this customer:

Company: {config["company_name"]}
Department: {config["department"]}
Industry: {config["industry"]}
Pain Points: {", ".join(config["pain_points"])}
Use Cases: {", ".join(config["use_cases"])}
Scale: {config["scale"]}
Dataset Size Preference: {size_preference.upper()}

The module should:
1. Import necessary libraries and the base class
2. Implement a class that inherits from DataGeneratorModule
3. Generate realistic, industry-specific data
4. Define relationships between datasets
5. Be specific to their business, not generic

CRITICAL - DATASET SIZES ({size_preference.upper()} preference):
- Primary timeseries datasets: {ranges['timeseries_typical']} rows (MAX {ranges['timeseries_max']:,})
- Reference/lookup tables: {ranges['reference_typical']} rows (MAX {ranges['reference_max']:,})
- Scale mentioned ({config["scale"]}) is for REALISM only, don't generate that many!

CRITICAL - TIMESTAMP REQUIREMENTS:
- All timestamp/datetime columns MUST use datetime.now() as the END date
- Generate data going BACKWARDS from today, maximum 120 days old
- NEVER hardcode dates like '2023-01-01' or generate future dates

Template to enhance:
{template}

Generate complete, working Python code.
"""
        return prompt

    def _build_data_generation_with_requirements_prompt(self, config: Dict[str, Any],
                                                        template: str,
                                                        formatted_requirements: str,
                                                        size_preference: str) -> str:
        """Build prompt for data generation with query requirements"""
        size_ranges = {
            'small': {
                'timeseries_max': 5000,
                'timeseries_typical': '1000-3000',
                'reference_max': 500,
                'reference_typical': '50-200'
            },
            'medium': {
                'timeseries_max': 15000,
                'timeseries_typical': '5000-10000',
                'reference_max': 2000,
                'reference_typical': '200-1000'
            },
            'large': {
                'timeseries_max': 50000,
                'timeseries_typical': '15000-30000',
                'reference_max': 5000,
                'reference_typical': '500-2000'
            }
        }

        ranges = size_ranges.get(size_preference, size_ranges['medium'])

        prompt = f"""Generate a Python module that implements DataGeneratorModule for this customer:

Company: {config["company_name"]}
Department: {config["department"]}
Industry: {config["industry"]}
Pain Points: {", ".join(config["pain_points"])}
Use Cases: {", ".join(config["use_cases"])}
Scale: {config["scale"]}
Dataset Size Preference: {size_preference.upper()}

{formatted_requirements}

The module should:
1. Generate data that satisfies the field requirements above
2. Include all required fields with appropriate data types
3. Create realistic relationships between datasets
4. Be specific to their business context

CRITICAL - DATASET SIZES ({size_preference.upper()} preference):
- Primary timeseries datasets: {ranges['timeseries_typical']} rows (MAX {ranges['timeseries_max']:,})
- Reference/lookup tables: {ranges['reference_typical']} rows (MAX {ranges['reference_max']:,})

Template to enhance:
{template}

Generate complete, working Python code that satisfies ALL field requirements.
"""
        return prompt

    def _generate_scripted_queries(self, config: Dict[str, Any], esql_docs: str) -> str:
        """Generate scripted queries method using template"""
        prompt = get_scripted_queries_prompt(config, esql_docs)

        if self.llm_client:
            code = self._call_llm(prompt)
            return CodeExtractor.extract_python_code(code)
        else:
            # Return minimal placeholder
            return """def generate_queries(self) -> List[Dict[str, Any]]:
        \"\"\"Generate ES|QL queries\"\"\"
        return []"""

    def _generate_parameterized_queries(self, config: Dict[str, Any], esql_docs: str) -> str:
        """Generate parameterized queries method using template"""
        prompt = get_parameterized_queries_prompt(config, esql_docs)

        if self.llm_client:
            code = self._call_llm(prompt)
            return CodeExtractor.extract_python_code(code)
        else:
            return """def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        \"\"\"Generate parameterized queries\"\"\"
        return []"""

    def _generate_rag_queries(self, config: Dict[str, Any], esql_docs: str) -> str:
        """Generate RAG queries method using template"""
        prompt = get_rag_queries_prompt(config, esql_docs, self.inference_endpoints)

        if self.llm_client:
            code = self._call_llm(prompt)
            return CodeExtractor.extract_python_code(code)
        else:
            return """def generate_rag_queries(self) -> List[Dict[str, Any]]:
        \"\"\"Generate RAG queries\"\"\"
        return []"""

    def _generate_scripted_queries_with_schema(self, config: Dict, esql_docs: str,
                                               schema_context: str, query_plan: Dict) -> str:
        """Generate scripted queries with schema awareness"""
        prompt = get_scripted_queries_prompt(config, esql_docs, schema_context=schema_context)

        if self.llm_client:
            code = self._call_llm(prompt)
            return CodeExtractor.extract_python_code(code)
        else:
            return """def generate_queries(self) -> List[Dict[str, Any]]:
        return []"""

    def _generate_parameterized_queries_with_schema(self, config: Dict, esql_docs: str,
                                                    schema_context: str, query_plan: Dict) -> str:
        """Generate parameterized queries with schema awareness"""
        prompt = get_parameterized_queries_prompt(config, esql_docs, schema_context=schema_context)

        if self.llm_client:
            code = self._call_llm(prompt)
            return CodeExtractor.extract_python_code(code)
        else:
            return """def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        return []"""

    def _generate_rag_queries_with_schema(self, config: Dict, esql_docs: str,
                                         schema_context: str, query_plan: Dict) -> str:
        """Generate RAG queries with schema awareness"""
        prompt = get_rag_queries_prompt(config, esql_docs, self.inference_endpoints,
                                       schema_context=schema_context)

        if self.llm_client:
            code = self._call_llm(prompt)
            return CodeExtractor.extract_python_code(code)
        else:
            return """def generate_rag_queries(self) -> List[Dict[str, Any]]:
        return []"""

    def _generate_demo_guide_content(self, config: Dict[str, Any], module_path: Path) -> str:
        """Generate demo guide content using LLM

        Args:
            config: Demo configuration
            module_path: Path to module directory (for loading queries/datasets)

        Returns:
            Markdown-formatted demo guide content
        """
        # Try to get query information for context
        query_descriptions = []

        all_queries_file = module_path / 'all_queries.json'
        if all_queries_file.exists():
            try:
                with open(all_queries_file, 'r') as f:
                    all_queries_data = json.load(f)
                    queries = all_queries_data.get('all', [])
                    query_descriptions = [q.get('name', 'Query') for q in queries]
            except:
                pass

        if self.llm_client:
            prompt = get_demo_guide_prompt(config, query_descriptions)
            content = self._call_llm(prompt)
            return content.strip()
        else:
            return get_fallback_demo_guide(config)

    def _generate_agent_instructions(self, config: Dict[str, Any],
                                    query_descriptions: List[str],
                                    datasets_info: List[str]) -> str:
        """Generate agent instructions using LLM

        Args:
            config: Demo configuration
            query_descriptions: List of query descriptions
            datasets_info: List of dataset descriptions

        Returns:
            Agent instructions text
        """
        if self.llm_client:
            prompt = get_agent_instructions_prompt(config, query_descriptions, datasets_info)
            instructions = self._call_llm(prompt, max_tokens=2000)
            return instructions.strip()
        else:
            return get_fallback_agent_instructions(config)

    def _format_schema_from_plan(self, query_plan: Dict) -> str:
        """Format schema context from query plan for prompts"""
        # Extract schema information from query plan
        schema_lines = ["Available Schema:"]

        # This would parse the query_plan structure to extract field info
        # Simplified implementation:
        if 'field_requirements' in query_plan:
            for dataset, fields in query_plan['field_requirements'].items():
                schema_lines.append(f"\n{dataset}:")
                for field in fields:
                    schema_lines.append(f"  - {field}")

        return "\n".join(schema_lines)

    def _get_minimal_esql_reference(self) -> str:
        """Get minimal ES|QL reference for prompts

        Returns condensed ES|QL syntax reference for query generation.
        """
        return """ES|QL Quick Reference:

Basic Commands:
- FROM index_name
- WHERE condition
- STATS aggregation BY field
- EVAL new_field = expression
- SORT field [ASC|DESC]
- LIMIT n

Aggregations:
- COUNT(*), COUNT(field)
- AVG(field), SUM(field), MIN(field), MAX(field)
- PERCENTILE(field, percentile)

Functions:
- DATE_TRUNC(interval, field) - Truncate timestamps
- BUCKET(field, interval) - Create buckets
- TO_STRING(field), TO_DATETIME(field) - Type conversion

Search Commands (for semantic_text fields):
- MATCH "query text"
- QSTR "field:value OR field2:value2"
- MATCH_PHRASE "exact phrase"

Example:
FROM metrics-*
| WHERE @timestamp > NOW() - 7 days
| STATS avg_value = AVG(value) BY category
| SORT avg_value DESC
| LIMIT 10
"""

    def _call_llm(self, prompt: str, max_tokens: int = 6000) -> str:
        """Call LLM with prompt and return response

        Handles both Anthropic and OpenAI clients.
        """
        if not self.llm_client:
            logger.warning("No LLM client available")
            return ""

        try:
            # Try Anthropic format first
            if hasattr(self.llm_client, 'messages'):
                response = self.llm_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text

            # Try OpenAI format
            elif hasattr(self.llm_client, 'chat'):
                response = self.llm_client.chat.completions.create(
                    model="gpt-4",
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content

            else:
                logger.error("Unknown LLM client type")
                return ""

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
