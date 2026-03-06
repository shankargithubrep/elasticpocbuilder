"""
Module Generator using LLM
Generates demo-specific modules that implement the base framework
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ModuleGenerator:
    """Generates demo modules using LLM"""

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

    def _resolve_vector_type(self) -> str:
        """Resolve the vector type (sparse/dense) accounting for custom endpoints"""
        embedding_type = self.inference_endpoints.get("embedding_type", "sparse")
        if embedding_type == "custom":
            return self.inference_endpoints.get("custom_vector_type", "sparse")
        return embedding_type

    def _resolve_embedding_endpoint(self) -> str:
        """Resolve the embedding endpoint ID accounting for custom endpoints"""
        embedding_type = self.inference_endpoints.get("embedding_type", "sparse")
        if embedding_type == "custom":
            return self.inference_endpoints.get("custom_embedding", ".elser-2-elasticsearch")
        if embedding_type == "dense":
            return ".jina-embeddings-v5-text-small"
        return ".elser-2-elasticsearch"

    def generate_demo_module(self, config: Dict[str, Any], query_plan: Optional[Dict[str, Any]] = None) -> str:
        """Generate a complete demo module for a customer

        Args:
            config: Demo configuration with customer context
            query_plan: Optional query plan with field requirements (from LightweightQueryPlanner)

        Returns:
            Path to the generated module directory
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
            self._generate_config_file(config, module_path)
        else:
            logger.info("Using original data-first generation (no query plan)")
            # Generate each component (Python modules) - original flow
            self._generate_data_module(config, module_path)
            self._generate_query_module(config, module_path)
            self._generate_guide_module(config, module_path)
            self._generate_config_file(config, module_path)

        # Generate static files for quick loading (must happen before agent metadata)
        self._generate_static_files(module_path)

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

        # Save query strategy
        strategy_file = module_path / 'query_strategy.json'
        strategy_file.write_text(json.dumps(query_strategy, indent=2))
        logger.info("Saved query_strategy.json")

        # Extract data requirements from strategy (inline pure dict transformation)
        data_requirements = {}
        for dataset in query_strategy.get('datasets', []):
            data_requirements[dataset['name']] = {
                'fields': dataset.get('required_fields', dataset.get('fields', {})),
                'relationships': dataset.get('relationships', []),
                'semantic_fields': dataset.get('semantic_fields', []),
                'type': dataset['type'],
                'row_count': dataset.get('row_count', 'moderate')
            }

        # Generate each component with strategy
        self._generate_data_module_with_requirements(config, module_path, data_requirements)
        self._generate_query_module_with_strategy(config, module_path, query_strategy)
        self._generate_guide_module(config, module_path)
        self._generate_config_file(config, module_path)

        # Generate static files for quick loading (must happen before agent metadata)
        self._generate_static_files(module_path)

        # Generate agent metadata AFTER static files (needs queries.json)
        logger.info(">>> About to call _generate_agent_metadata() from generate_demo_module_with_strategy()")
        self._generate_agent_metadata(config, module_path)
        logger.info(">>> Returned from _generate_agent_metadata()")

        logger.info(f"Generated demo module with strategy at: {module_path}")
        return str(module_path)

    def generate_data_and_infrastructure_only(
        self,
        config: Dict[str, Any],
        query_strategy: Dict[str, Any],
        data_specifications: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Generate module infrastructure and data generator only (NO QUERIES YET)

        This is Phase 1 of the split generation workflow. Query generation happens later
        after data is indexed and profiled.

        Args:
            config: Demo configuration with customer context
            query_strategy: Pre-generated query strategy with data requirements
            data_specifications: Optional domain-specific value specifications (for search demos)
            progress_callback: Optional progress callback for per-dataset reporting

        Returns:
            Path to the generated module directory (ready for data generation)
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

        # Save query strategy
        strategy_file = module_path / 'query_strategy.json'
        strategy_file.write_text(json.dumps(query_strategy, indent=2))
        logger.info("Saved query_strategy.json")

        # Save data specifications if provided (for search demos)
        if data_specifications:
            specs_file = module_path / 'data_specifications.json'
            specs_file.write_text(json.dumps(data_specifications, indent=2))
            logger.info("Saved data_specifications.json")

        # Extract data requirements from strategy (inline pure dict transformation)
        data_requirements = {}
        for dataset in query_strategy.get('datasets', []):
            data_requirements[dataset['name']] = {
                'fields': dataset.get('required_fields', dataset.get('fields', {})),
                'relationships': dataset.get('relationships', []),
                'semantic_fields': dataset.get('semantic_fields', []),
                'type': dataset['type'],
                'row_count': dataset.get('row_count', 'moderate')
            }

        # Generate ONLY data module and config (NO QUERIES)
        # NOTE: Guide generation is handled separately by the orchestrator
        # so it can run in parallel with data execution + indexing
        self._generate_data_module_with_requirements(
            config,
            module_path,
            data_requirements,
            data_specifications=data_specifications,
            progress_callback=progress_callback
        )
        self._generate_config_file(config, module_path)

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
        self._generate_static_files(module_path_obj)

        # Generate agent metadata AFTER all static files (needs all_queries.json)
        logger.info(">>> About to call _generate_agent_metadata() from generate_query_module_with_profile()")
        self._generate_agent_metadata(config, module_path_obj)
        logger.info(">>> Returned from _generate_agent_metadata()")

    def _generate_data_module(self, config: Dict[str, Any], module_path: Path):
        """Generate the data generation module"""

        # Get dataset size preference and calculate ranges
        size_preference = config.get('dataset_size_preference', 'medium')
        size_ranges = {
            'small': {
                'total_max': 5000,
                'per_dataset_max': 1000,
                'per_dataset_typical': '200-500',
                'timeseries_max': 3000,
                'timeseries_typical': '1000-2000',
                'reference_max': 500,
                'reference_typical': '50-200'
            },
            'medium': {
                'total_max': 15000,
                'per_dataset_max': 3000,
                'per_dataset_typical': '500-1500',
                'timeseries_max': 10000,
                'timeseries_typical': '3000-6000',
                'reference_max': 2000,
                'reference_typical': '200-1000'
            },
            'large': {
                'total_max': 50000,
                'per_dataset_max': 10000,
                'per_dataset_typical': '2000-5000',
                'timeseries_max': 30000,
                'timeseries_typical': '10000-20000',
                'reference_max': 5000,
                'reference_typical': '500-2000'
            }
        }

        ranges = size_ranges[size_preference]

        prompt = f"""Generate a Python module that implements DataGeneratorModule for this customer:

Company: {config["company_name"]}
Department: {config["department"]}
Industry: {config["industry"]}
Pain Points: {", ".join(config["pain_points"])}
Use Cases: {", ".join(config["use_cases"])}
Dataset Size Preference: {size_preference.upper()}

The module should:
1. Import necessary libraries and the base class
2. Implement a class that inherits from DataGeneratorModule
3. Generate realistic, industry-specific data
4. Define relationships between datasets
5. Be specific to their business, not generic

CRITICAL - TIMESTAMP REQUIREMENTS:
- All timestamp/datetime columns MUST use datetime.now() as the END date
- Generate data going BACKWARDS from today, maximum 120 days old
- NEVER hardcode dates like '2023-01-01' or generate future dates
- NEVER generate data older than 120 days from today
- Use pd.date_range(end=datetime.now(), periods=N, freq='h') for timeseries data
- Example: For 90 days of hourly data use periods=90*24 (2,160 rows)
- This ensures ES|QL queries with "NOW() - X days" will return results (stay within 120-day window)

CRITICAL - DATASET SIZES ({size_preference.upper()} preference):
***** STRICT TOTAL LIMIT: {ranges['total_max']:,} documents MAXIMUM across ALL datasets combined *****
- Each individual dataset: {ranges['per_dataset_typical']} rows (NEVER exceed {ranges['per_dataset_max']:,} per dataset)
- For demos with 5-6 datasets, aim for {ranges['per_dataset_max'] // 3:,}-{ranges['per_dataset_max'] // 2:,} rows each to stay under total
- Reference/lookup tables: {ranges['reference_typical']} rows (MAX {ranges['reference_max']:,})
- DO NOT generate thousands of records per dataset - keep datasets SMALL for demo purposes
- Example for {size_preference.upper()}: 6 datasets x 1000 rows = 6000 total (GOOD)
- WRONG for {size_preference.upper()}: 6 datasets x 6000 rows = 36000 total (EXCEEDS LIMIT!)

CRITICAL - STRING TEMPLATE FORMATTING:
When using string templates with .format(), ensure placeholder names EXACTLY match the keyword arguments:
- WRONG: template = "{{treatments}}" with .format(treatment="value")  ← Plural vs singular mismatch!
- CORRECT: template = "{{treatment}}" with .format(treatment="value")  ← Names match exactly
- WRONG: template = "{{user_name}}" with .format(username="value")  ← Underscore mismatch!
- CORRECT: template = "{{username}}" with .format(username="value")  ← Names match exactly
Check ALL template placeholders match their .format() keyword arguments EXACTLY (case and plurality matter!)

CRITICAL - AVOID EMPTY LIST ERRORS:
List comprehensions with filters can produce empty lists causing "'a' cannot be empty" errors in np.random.choice().
ALWAYS provide a fallback when filtering lists:
- WRONG: choice([s for s in systems if condition])  ← Can be empty!
- CORRECT: filtered = [s for s in systems if condition]; choice(filtered if filtered else systems)
- BETTER: choice(systems)  ← Avoid complex filtering when simple random choice works
When you MUST filter, check the result before passing to safe_choice() or np.random.choice()

CRITICAL - F-STRING ESCAPE RESTRICTIONS:
Python f-strings CANNOT contain backslash escapes inside the expression parts (the {{}} braces).
This will cause a SyntaxError: "f-string expression part cannot include a backslash"
- WRONG: f'{{random.choice(["item\'s", "another"])}}' ← Backslash escape inside {{}}!
- CORRECT: f'{{random.choice(["item" + chr(39) + "s", "another"])}}' ← Use chr(39) for apostrophe
- BETTER: f'{{random.choice(["items", "another"])}}' ← Avoid apostrophes in lists
- ALSO GOOD: random.choice(["item's", "another"]) ← No f-string at all
When building strings with apostrophes/quotes, use concatenation, chr(), or avoid f-strings entirely.

Template:
```python
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List

class {config["company_name"].replace(" ", "")}DataGenerator(DataGeneratorModule):
    \"\"\"Data generator for {config["company_name"]} - {config["department"]}\"\"\"

    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        \"\"\"Generate datasets specific to {config["company_name"]}'s needs\"\"\"
        datasets = {{}}

        # Generate main dataset with columns specific to their business
        # Include patterns that demonstrate their pain points

        # EXAMPLE: Generate timestamps ending at NOW (critical for ES|QL queries)
        # Max 120 days of data - this example shows ~42 days (1000 hours)
        # events_df = pd.DataFrame({{
        #     'timestamp': pd.date_range(end=datetime.now(), periods=1000, freq='h'),
        #     'event_type': np.random.choice(['click', 'purchase'], 1000),
        #     'amount': np.random.uniform(10, 1000, 1000)
        # }})
        # datasets['events'] = events_df

        # IMPORTANT: Size preference is {size_preference.upper()}
        # - Primary datasets: {ranges['timeseries_typical']} rows (MAX {ranges['timeseries_max']:,})
        # - Reference/lookup tables: {ranges['reference_typical']} rows (MAX {ranges['reference_max']:,})

        return datasets

    def get_relationships(self) -> List[tuple]:
        \"\"\"Define foreign key relationships\"\"\"
        return [
            # (source_table, foreign_key_column, target_table)
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        \"\"\"Describe each dataset\"\"\"
        return {{
            # 'dataset_name': 'Description of what this data represents'
        }}
```

Generate the complete implementation:"""

        if self.llm_client:
            code = self._call_llm(prompt, max_tokens=32000)
        else:
            code = self._generate_mock_data_module(config)

        # Validate syntax before saving (with auto-fix on failure)
        code = self._validate_python_syntax(code, 'data_generator.py')

        # Save the module
        module_file = module_path / 'data_generator.py'
        module_file.write_text(code)

    def _generate_query_module(self, config: Dict[str, Any], module_path: Path):
        """Generate the query generation module with THREE query types via 3 separate LLM calls.

        This method orchestrates three separate LLM calls for cost efficiency and resilience:
        1. _generate_scripted_queries() - ~5K tokens
        2. _generate_parameterized_queries() - ~4K tokens
        3. _generate_rag_queries() - ~6K tokens

        Total ~15K tokens vs single 16K call, but only pay for what's used.
        """
        logger.info("🏗️  Generating query module via 3-call approach...")

        # Read ES|QL documentation once (shared across all calls)
        esql_docs = self._read_esql_docs()

        # Generate each query type separately
        logger.info("📤 Call 1/3: Generating scripted queries...")
        scripted_code = self._generate_scripted_queries(config, esql_docs)

        logger.info("📤 Call 2/3: Generating parameterized queries...")
        parameterized_code = self._generate_parameterized_queries(config, esql_docs)

        logger.info("📤 Call 3/3: Generating RAG queries...")
        rag_code = self._generate_rag_queries(config, esql_docs)

        # Combine all three methods into single module
        logger.info("🔧 Combining query methods into single module...")
        full_code = self._combine_query_methods(config, scripted_code, parameterized_code, rag_code)

        # Validate syntax before saving (with auto-fix on failure)
        full_code = self._validate_python_syntax(full_code, 'query_generator.py')

        # Validate that all required methods are present
        methods_present = self._validate_query_module_methods(full_code)
        missing_methods = [method for method, present in methods_present.items() if not present]

        if missing_methods:
            logger.warning(f"⚠️  Query module is missing methods: {', '.join(missing_methods)}")
            logger.warning("⚠️  Framework will use default implementations (return empty lists)")

        # Save the module
        module_file = module_path / 'query_generator.py'
        module_file.write_text(full_code)
        logger.info("✅ Generated complete query_generator.py with all 3 query types")

    def _generate_query_module_with_plan(self, config: Dict[str, Any], module_path: Path, query_plan: Dict):
        """Generate query module using query plan for schema coordination

        This ensures generated queries use EXACT field names from the data.
        Similar to 3-call approach but with schema context from query plan.
        """
        logger.info("🏗️  Generating query module with query plan schema...")

        # Read ES|QL documentation
        esql_docs = self._read_esql_docs()

        # Format schema context from query plan
        from src.services.query_planner import LightweightQueryPlanner
        planner = LightweightQueryPlanner(self.llm_client)
        schema_context = planner.format_requirements_for_data_prompt(query_plan)

        # Generate each query type with schema context
        logger.info("📤 Call 1/3: Generating scripted queries (with schema)...")
        scripted_code = self._generate_scripted_queries_with_schema(config, esql_docs, schema_context, query_plan)

        logger.info("📤 Call 2/3: Generating parameterized queries (with schema)...")
        parameterized_code = self._generate_parameterized_queries_with_schema(config, esql_docs, schema_context, query_plan)

        logger.info("📤 Call 3/3: Generating RAG queries (with schema)...")
        rag_code = self._generate_rag_queries_with_schema(config, esql_docs, schema_context, query_plan)

        # Combine all three methods into single module
        logger.info("🔧 Combining query methods into single module...")
        full_code = self._combine_query_methods(config, scripted_code, parameterized_code, rag_code)

        # Validate syntax (with auto-fix on failure)
        full_code = self._validate_python_syntax(full_code, 'query_generator.py')

        # Validate methods
        methods_present = self._validate_query_module_methods(full_code)
        missing_methods = [method for method, present in methods_present.items() if not present]

        if missing_methods:
            logger.warning(f"⚠️  Query module is missing methods: {', '.join(missing_methods)}")
            logger.warning("⚠️  Framework will use default implementations (return empty lists)")

        # Save the module
        module_file = module_path / 'query_generator.py'
        module_file.write_text(full_code)
        logger.info("✅ Generated query_generator.py with schema-coordinated queries")

    def _generate_scripted_queries_with_schema(self, config: Dict, esql_docs: str, schema_context: str, query_plan: Dict) -> str:
        """Generate scripted queries using schema from query plan"""
        # Get query plans for this type
        scripted_plans = [q for q in query_plan.get('query_plans', []) if q.get('query_type') == 'scripted']

        # Get centralized ES|QL rules
        esql_rules = self._get_esql_strict_rules()

        # Get tool metadata instructions
        tool_metadata_prompt = self._get_tool_metadata_instructions(config)

        # Call existing method with enhanced prompt including schema
        base_prompt = f"""Generate the `generate_queries()` method for a QueryGeneratorModule.

**Customer Context:**
Company: {config["company_name"]}
Department: {config["department"]}
Pain Points: {", ".join(config["pain_points"])}

{schema_context}

**Planned Scripted Queries:**
{json.dumps(scripted_plans, indent=2)}

{tool_metadata_prompt}

**CRITICAL - Method Signature:**
```python
def generate_queries(self) -> List[Dict[str, Any]]:
    \"\"\"Generate scripted (non-parameterized) ES|QL queries

    Access datasets via self.datasets
    \"\"\"
    queries = []
    # ... implementation using self.datasets ...
    return queries
```

**CRITICAL - Query Dictionary Format:**
Each query MUST include a "type" field with the EXACT value "scripted":
```python
queries.append({{
    "type": "scripted",  # REQUIRED - MUST be exactly "scripted" for non-parameterized queries
    "name": "Query Name",
    "description": "What it does",
    "esql": \"\"\"FROM index | WHERE condition | STATS aggregation\"\"\",
    # ... other fields ...
}})
```

{esql_rules}

🚨🚨🚨 CRITICAL - INTEGER DIVISION ANTI-PATTERN 🚨🚨🚨
ALWAYS use TO_DOUBLE() when dividing aggregated fields! Integer division truncates to 0!

❌ WRONG (produces 0 or 100 only):
```esql
| EVAL success_rate = ((total - failures) / total) * 100
```

✅ CORRECT (produces accurate percentages like 95.7):
```esql
| EVAL success_rate = ((total - failures) / TO_DOUBLE(total)) * 100
```

**WHY**: In ES|QL, dividing two integers performs integer division and truncates the result.
- (95 / 100) = 0 (WRONG - integer division)
- (95 / TO_DOUBLE(100)) = 0.95 (CORRECT - float division)

**RULE**: If you see division (/) in an EVAL, wrap the denominator in TO_DOUBLE() UNLESS:
- You already use TO_DOUBLE(): ✓ `field / TO_DOUBLE(total)`
- You multiply by float first: ✓ `field * 100.0 / total`
- You divide by float literal: ✓ `milliseconds / 1000.0`

🚨🚨🚨 CRITICAL - NULL HANDLING ANTI-PATTERN 🚨🚨🚨
ALWAYS include NULL checks with negative filters! ES|QL silently excludes NULL values!

❌ WRONG (silently excludes docs where field is NULL - DATA LOSS):
```esql
| WHERE status != "success"
| WHERE NOT(error_type LIKE "*timeout*")
```

✅ CORRECT (includes NULL values - complete data):
```esql
| WHERE status != "success" OR status IS NULL
| WHERE NOT(error_type LIKE "*timeout*") OR error_type IS NULL
```

**WHY**: ES|QL excludes NULL/missing fields from negative filters (!=, NOT, NOT LIKE).
- Documents where the field is NULL are SILENTLY EXCLUDED even though they match "not X"
- ESPECIALLY CRITICAL for security queries - missing data = missed threats!

**RULE**: When using negative filters (!=, NOT, NOT LIKE, NOT IN), append `OR field IS NULL` UNLESS:
- Field is guaranteed to exist (e.g., @timestamp)
- You explicitly want to exclude nulls (rare - document this in description)

Generate ONLY the generate_queries() method with the EXACT signature above (no datasets parameter!).
Access data via self.datasets. Use EXACT field names from the schema. ALWAYS use "type": "scripted" for ALL queries."""

        # Call LLM
        return self._call_llm(base_prompt + "\n\n" + esql_docs[:1000])

    def _generate_parameterized_queries_with_schema(self, config: Dict, esql_docs: str, schema_context: str, query_plan: Dict) -> str:
        """Generate parameterized queries using schema from query plan"""
        # Get query plans for this type
        param_plans = [q for q in query_plan.get('query_plans', []) if q.get('query_type') == 'parameterized']

        # Get centralized ES|QL rules
        esql_rules = self._get_esql_strict_rules()

        # Get tool metadata instructions
        tool_metadata_prompt = self._get_tool_metadata_instructions(config)

        base_prompt = f"""Generate the `generate_parameterized_queries()` method for a QueryGeneratorModule.

**Customer Context:**
Company: {config["company_name"]}
Department: {config["department"]}
Pain Points: {", ".join(config["pain_points"])}

{schema_context}

**Planned Parameterized Queries:**
{json.dumps(param_plans, indent=2)}

{tool_metadata_prompt}

**CRITICAL - Method Signature:**
```python
def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
    \"\"\"Generate parameterized ES|QL queries with ?parameter syntax for Agent Builder

    Access datasets via self.datasets
    \"\"\"
    queries = []
    # ... implementation using self.datasets ...
    return queries
```

**CRITICAL - Query Dictionary Format:**
Each query MUST include a "type" field with the EXACT value "parameterized":
```python
queries.append({{
    "type": "parameterized",  # REQUIRED - MUST be exactly "parameterized" for Agent Builder queries
    "name": "Query Name",
    "description": "What it does",
    "esql": \"\"\"FROM index | WHERE field == ?param_name\"\"\",
    "parameters": {{"param_name": "example_value"}},
    # ... other fields ...
}})
```

{esql_rules}

🚨🚨🚨 CRITICAL - @timestamp ANTI-PATTERN 🚨🚨🚨
NEVER EVER parameterize @timestamp! This is the #1 most common mistake!

❌ WRONG (DO NOT GENERATE THIS):
```esql
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
```

✅ CORRECT (USE THIS INSTEAD):
```esql
| WHERE @timestamp >= NOW() - 7 days  # Relative time with NOW()
```

If you see @timestamp in the query plan, IGNORE any parameter suggestions and use NOW() instead!
The ONLY time-based parameters allowed are for BUSINESS date fields (order_date, created_at, etc.) - NEVER @timestamp!

🚨🚨🚨 CRITICAL - INTEGER DIVISION ANTI-PATTERN 🚨🚨🚨
ALWAYS use TO_DOUBLE() when dividing aggregated fields! Integer division truncates to 0!

❌ WRONG (produces 0 or 100 only):
```esql
| EVAL success_rate = ((total - failures) / total) * 100
```

✅ CORRECT (produces accurate percentages like 95.7):
```esql
| EVAL success_rate = ((total - failures) / TO_DOUBLE(total)) * 100
```

**WHY**: In ES|QL, dividing two integers performs integer division and truncates the result.
- (95 / 100) = 0 (WRONG - integer division)
- (95 / TO_DOUBLE(100)) = 0.95 (CORRECT - float division)

**RULE**: If you see division (/) in an EVAL, wrap the denominator in TO_DOUBLE() UNLESS:
- You already use TO_DOUBLE(): ✓ `field / TO_DOUBLE(total)`
- You multiply by float first: ✓ `field * 100.0 / total`
- You divide by float literal: ✓ `milliseconds / 1000.0`

🚨🚨🚨 CRITICAL - NULL HANDLING ANTI-PATTERN 🚨🚨🚨
ALWAYS include NULL checks with negative filters! ES|QL silently excludes NULL values!

❌ WRONG (silently excludes docs where field is NULL - DATA LOSS):
```esql
| WHERE status != "success"
| WHERE NOT(error_type LIKE "*timeout*")
```

✅ CORRECT (includes NULL values - complete data):
```esql
| WHERE status != "success" OR status IS NULL
| WHERE NOT(error_type LIKE "*timeout*") OR error_type IS NULL
```

**WHY**: ES|QL excludes NULL/missing fields from negative filters (!=, NOT, NOT LIKE).
- Documents where the field is NULL are SILENTLY EXCLUDED even though they match "not X"
- ESPECIALLY CRITICAL for security queries - missing data = missed threats!

**RULE**: When using negative filters (!=, NOT, NOT LIKE, NOT IN), append `OR field IS NULL` UNLESS:
- Field is guaranteed to exist (e.g., @timestamp)
- You explicitly want to exclude nulls (rare - document this in description)

Generate ONLY the generate_parameterized_queries() method with the EXACT signature above (no datasets parameter!).
Access data via self.datasets. Use ?parameter syntax for Agent Builder tools. Use EXACT field names from schema. ALWAYS use "type": "parameterized" for ALL queries."""

        return self._call_llm(base_prompt + "\n\n" + esql_docs[:1000])

    def _generate_rag_queries_with_schema(self, config: Dict, esql_docs: str, schema_context: str, query_plan: Dict) -> str:
        """Generate RAG queries using schema from query plan"""
        # Get query plans for this type
        rag_plans = [q for q in query_plan.get('query_plans', []) if q.get('query_type') == 'rag']

        # Get endpoint IDs for substitution in prompt
        rerank_endpoint = self.inference_endpoints['rerank']
        completion_endpoint = self.inference_endpoints['completion']

        # Get centralized ES|QL rules
        esql_rules = self._get_esql_strict_rules()

        # Get tool metadata instructions
        tool_metadata_prompt = self._get_tool_metadata_instructions(config)

        base_prompt = f"""Generate the `generate_rag_queries()` method for a QueryGeneratorModule.

**Customer Context:**
Company: {config["company_name"]}
Department: {config["department"]}
Pain Points: {", ".join(config["pain_points"])}

{schema_context}

**Planned RAG Queries:**
{json.dumps(rag_plans, indent=2)}

{tool_metadata_prompt}

**CRITICAL - Method Signature:**
```python
def generate_rag_queries(self) -> List[Dict[str, Any]]:
    \"\"\"Generate RAG queries with MATCH -> RERANK -> COMPLETION pipeline

    Access datasets via self.datasets
    \"\"\"
    queries = []
    # ... implementation using self.datasets ...
    return queries
```

**CRITICAL - Query Dictionary Format:**
Each query MUST include a "type" field with the EXACT value "rag":
```python
queries.append({{
    "type": "rag",  # REQUIRED - MUST be exactly "rag" for semantic search queries
    "name": "Query Name",
    "description": "What it does",
    "esql": \"\"\"FROM knowledge_base | WHERE MATCH(content, ?question)\"\"\",
    # ... other fields ...
}})
```

{esql_rules}

**CRITICAL ES|QL Syntax Rules for RAG Queries:**
1. **MATCH (always in WHERE clause)**:
   ✅ CORRECT: `WHERE MATCH(field, ?parameter)`
   ✅ CORRECT: `WHERE MATCH(field, ?param, {{"fuzziness": "AUTO"}})`
   ❌ WRONG: `| MATCH field ?parameter` (MATCH is NOT a pipe operation)

2. **RERANK (pipe operation with ON and WITH)**:
   ✅ CORRECT: `| RERANK ?query ON field WITH {{ "inference_id": """ + f'"{rerank_endpoint}"' + """ }}`
   ✅ CORRECT: `| RERANK ?query ON field1, field2 WITH {{ "inference_id": """ + f'"{rerank_endpoint}"' + """ }}`
   ❌ WRONG: `| RERANK field ?query` (missing ON keyword)
   ❌ WRONG: `| RERANK ?query ON field MODEL "model"` (use WITH, not MODEL)

3. **COMPLETION (pipe operation with WITH - optional for RAG)**:
   ✅ CORRECT: `| COMPLETION answer = prompt WITH {{ "inference_id": """ + f'"{completion_endpoint}"' + """ }}`
   ✅ CORRECT: Build prompts with EVAL: `| EVAL prompt = CONCAT("Q: ", ?query, " A: ", content)`
   ❌ WRONG: `| COMPLETION "text" MODEL "gpt-4"` (use WITH, not MODEL)
   ❌ WRONG: Using template syntax like `{{{{#results}}}}` (not supported)
   ⚠️ WARNING: Every row generates 1 LLM API call - use LIMIT before COMPLETION!

   **CRITICAL CONCAT STRING RULE - ES|QL does NOT support newlines or escape sequences in string literals!**
   ❌ WRONG: `CONCAT("Line one\\nLine two")` — causes parsing_exception
   ❌ WRONG: `CONCAT("Multi-line\nstring")` — causes parsing_exception
   ❌ WRONG: String literals that span multiple lines
   ✅ CORRECT: `CONCAT("Line one. ", "Line two. ", "Title: ", title, " Content: ", content)`
   Each piece of text must be a separate CONCAT argument on a single line. Use spaces or periods to separate sections, NOT newline characters.

4. **METADATA _score**: Add after FROM to access relevance scores
   Example: `FROM index METADATA _score`

5. **LOOKUP JOIN**: Use `LOOKUP JOIN table ON field` (JOIN keyword is required)
   Example: `| LOOKUP JOIN agents ON agent_id`

6. **Standard RAG Pipeline Pattern**:
   ```
   FROM index METADATA _score
   | WHERE MATCH(semantic_field, ?user_question)
   | SORT _score DESC
   | LIMIT 100
   | RERANK ?user_question ON field WITH {{ "inference_id": """ + f'"{rerank_endpoint}"' + """ }}
   | LIMIT 10
   | KEEP fields...
   ```

7. **Optional COMPLETION** (add cost warning if used):
   ```
   | LIMIT 5  # CRITICAL: Limit before COMPLETION to reduce API calls
   | EVAL prompt = CONCAT("Question: ", ?user_question, " Content: ", content)
   | COMPLETION answer = prompt WITH {{ "inference_id": """ + f'"{completion_endpoint}"' + """ }}
   ```

**Inference Endpoints (ALWAYS use these exact IDs)**:
- RERANK: `{rerank_endpoint}`
- COMPLETION: `{completion_endpoint}`
- SPARSE EMBEDDING: `.elser-2-elastic` (for semantic_text fields)

8. **Semantic Text Fields**: Fields used in MATCH must be text or semantic_text type

**Important**: For most RAG use cases, MATCH → RERANK → LIMIT is sufficient.
Only add COMPLETION if the use case explicitly requires LLM-generated summaries/answers.
If using COMPLETION, ALWAYS include cost warning in description.

Generate ONLY the generate_rag_queries() method with the EXACT signature above (no datasets parameter!).
Access data via self.datasets. Use correct MATCH/RERANK syntax. Use EXACT field names from schema. ALWAYS use "type": "rag" for ALL queries."""

        return self._call_llm(base_prompt + "\n\n" + esql_docs[:1000])

    def _get_tool_metadata_instructions(self, config: Dict[str, Any]) -> str:
        """Get instructions for generating tool metadata for Agent Builder"""

        # Extract company and department for tool ID generation
        company_slug = config['company_name'].lower().replace(' ', '_')[:15]
        dept_slug = config.get('department', 'analytics').lower().replace(' ', '_')[:10]

        return f"""
**IMPORTANT: Agent Builder Tool Metadata**

Each query MUST include 'tool_metadata' for deployment to Elastic Agent Builder.
This metadata allows queries to become reusable tools that AI agents can invoke.

For EACH query you generate, include a 'tool_metadata' field with:

1. 'tool_id': Unique identifier following pattern: <customer>_<dept>_<purpose>
   - MUST start and end with a letter or number
   - ONLY lowercase letters, numbers, dots, underscores
   - Maximum 50 characters
   - Use company prefix: {company_slug}
   - Department: {dept_slug}
   - Examples:
     * "{company_slug}_{dept_slug}_performance" ✓
     * "{company_slug}_{dept_slug}_inventory_alerts" ✓
     * "Query-1-{config['company_name']}" ✗ (no uppercase/hyphens)

2. 'description': Tool description for Agent Builder (NOT the same as query description)
   - First ~50 characters appear in tool list - make them count!
   - Start with WHAT it does (verb): "Analyzes...", "Compares...", "Identifies..."
   - Then explain WHEN to use it and what insights it provides
   - Focus on business value, not technical implementation
   - Bad: "ES|QL query for metrics analysis"
   - Good: "Analyzes performance metrics across regions. Identifies underperforming areas and trends for optimization."

3. 'tags': Array of 3-5 lowercase tags for categorization
   - Include domain tags based on use case
   - Include functional tags (performance, cost, analytics)
   - Include "esql" for all ES|QL queries
   - Keep single words, no spaces

Example query structure with tool_metadata:
{{
    'name': 'Regional Performance Analysis',
    'description': 'Analyze performance metrics across different regions',  # Original query description
    'tool_metadata': {{
        'tool_id': '{company_slug}_{dept_slug}_regional_performance',
        'description': 'Analyzes regional performance metrics. Identifies underperforming regions and trends for strategic planning.',
        'tags': ['analytics', 'performance', 'regional', 'esql']
    }},
    'esql': 'FROM metrics | STATS avg_performance = AVG(score) BY region',
    'pain_point': 'Lack of visibility into regional performance'
}}

Tool metadata is REQUIRED - every query must have valid tool_metadata for Agent Builder deployment.
"""

    def _generate_scripted_queries(self, config: Dict[str, Any], esql_docs: str) -> str:
        """Generate ONLY the generate_queries() method (scripted queries)

        Target: ~5K tokens
        Returns: Just the method code, not the full class
        """
        # Get tool metadata instructions
        tool_metadata_prompt = self._get_tool_metadata_instructions(config)

        # Get company and department slugs for the template
        company_slug = config['company_name'].lower().replace(' ', '_')[:15]
        dept_slug = config.get('department', 'analytics').lower().replace(' ', '_')[:10]

        prompt = f"""Generate the `generate_queries()` method for a QueryGeneratorModule.

**Customer Context:**
Company: {config["company_name"]}
Department: {config["department"]}
Pain Points: {", ".join(config["pain_points"])}
Use Cases: {", ".join(config["use_cases"])}

{tool_metadata_prompt}

**Task**: Generate 5-7 SCRIPTED (non-parameterized) ES|QL queries that address their pain points.

**Requirements:**
- All queries must use hard-coded values (no ?parameters)
- Start simple, progress to complex
- Each query should address a specific pain point
- All will be tested against indexed data

**ES|QL Reference (Basics):**
{esql_docs[:1500]}

**Method Template:**
```python
def generate_queries(self) -> List[Dict[str, Any]]:
    \"\"\"Generate SCRIPTED (non-parameterized) ES|QL queries

    These are fully tested queries with hard-coded values.
    Address pain points: {", ".join(config["pain_points"])}
    \"\"\"
    queries = []

    # Query 1: [Simple aggregation]
    queries.append({{
        "query_type": "scripted",
        "name": "descriptive_name",
        "description": "What it demonstrates",
        "tool_metadata": {{  # REQUIRED for Agent Builder
            "tool_id": "{company_slug}_{dept_slug}_purpose",
            "description": "Short action summary. Details about when to use and insights provided.",
            "tags": ["domain", "function", "esql"]
        }},
        "esql": \"\"\"
            FROM index_name
            | WHERE condition
            | STATS aggregation
            | SORT field DESC
            | LIMIT 10
        \"\"\",
        "expected_insight": "What customer learns",
        "tested": True
    }})

    # Add 4-6 more queries of increasing complexity...

    return queries
```

🚨🚨🚨 CRITICAL - INTEGER DIVISION ANTI-PATTERN 🚨🚨🚨
ALWAYS use TO_DOUBLE() when dividing aggregated fields! Integer division truncates to 0!

❌ WRONG (produces 0 or 100 only):
```esql
| EVAL success_rate = ((total - failures) / total) * 100
```

✅ CORRECT (produces accurate percentages like 95.7):
```esql
| EVAL success_rate = ((total - failures) / TO_DOUBLE(total)) * 100
```

**WHY**: In ES|QL, dividing two integers performs integer division and truncates the result.
- (95 / 100) = 0 (WRONG - integer division)
- (95 / TO_DOUBLE(100)) = 0.95 (CORRECT - float division)

**RULE**: If you see division (/) in an EVAL, wrap the denominator in TO_DOUBLE() UNLESS:
- You already use TO_DOUBLE(): ✓ `field / TO_DOUBLE(total)`
- You multiply by float first: ✓ `field * 100.0 / total`
- You divide by float literal: ✓ `milliseconds / 1000.0`

🚨🚨🚨 CRITICAL - NULL HANDLING ANTI-PATTERN 🚨🚨🚨
ALWAYS include NULL checks with negative filters! ES|QL silently excludes NULL values!

❌ WRONG (silently excludes docs where field is NULL - DATA LOSS):
```esql
| WHERE status != "success"
| WHERE NOT(error_type LIKE "*timeout*")
```

✅ CORRECT (includes NULL values - complete data):
```esql
| WHERE status != "success" OR status IS NULL
| WHERE NOT(error_type LIKE "*timeout*") OR error_type IS NULL
```

**WHY**: ES|QL excludes NULL/missing fields from negative filters (!=, NOT, NOT LIKE).
- Documents where the field is NULL are SILENTLY EXCLUDED even though they match "not X"
- ESPECIALLY CRITICAL for security queries - missing data = missed threats!

**RULE**: When using negative filters (!=, NOT, NOT LIKE, NOT IN), append `OR field IS NULL` UNLESS:
- Field is guaranteed to exist (e.g., @timestamp)
- You explicitly want to exclude nulls (rare - document this in description)

Generate ONLY the method implementation (including the def line and all queries). Do NOT include class definition or imports."""

        if self.llm_client:
            code = self._call_llm_for_method(prompt, max_tokens=6000)
        else:
            code = """    def generate_queries(self) -> List[Dict[str, Any]]:
        return []"""

        return code

    def _generate_parameterized_queries(self, config: Dict[str, Any], esql_docs: str) -> str:
        """Generate ONLY the generate_parameterized_queries() method

        Target: ~4K tokens
        Returns: Just the method code, not the full class
        """
        # Get tool metadata instructions
        tool_metadata_prompt = self._get_tool_metadata_instructions(config)

        # Get company and department slugs for the template
        company_slug = config['company_name'].lower().replace(' ', '_')[:15]
        dept_slug = config.get('department', 'analytics').lower().replace(' ', '_')[:10]

        prompt = f"""Generate the `generate_parameterized_queries()` method for a QueryGeneratorModule.

**Customer Context:**
Company: {config["company_name"]}
Department: {config["department"]}
Pain Points: {", ".join(config["pain_points"])}

{tool_metadata_prompt}

**Task**: Generate 3-5 PARAMETERIZED queries for Agent Builder ES|QL tools.

**Requirements:**
- Based on typical analytics queries for their use case
- Use ?parameter syntax for user-configurable values
- NO LIKE or RLIKE operators (not supported with parameters!)
- Include parameter definitions with types and defaults
- Link to conceptual base query for trust

**CRITICAL - Smart Parameter Selection:**

✅ **CREATE parameters for BUSINESS-SPECIFIC logic:**
- Domain fields: `WHERE category == ?category`, `WHERE status == ?status`
- Business date fields: `WHERE deployment_date >= ?deploy_start`, `WHERE hire_date BETWEEN ?from AND ?to`
- Schema-specific: `WHERE provider_id == ?provider`, `WHERE priority_level >= ?min_priority`

❌ **AVOID parameters for CROSS-CUTTING concerns:**
- `@timestamp` filtering (agents handle dynamically via platform.core.execute_esql)
- Event timestamps: created_at, updated_at, indexed_at
- Generic operations: LIMIT, SORT direction

**Business Date Fields - GOOD Examples:**
```
WHERE deployment_date >= ?deploy_start  # ✓ Business date field
WHERE expiration_date < ?expiry_cutoff  # ✓ Domain-specific date
WHERE hire_date BETWEEN ?from AND ?to   # ✓ Business temporal logic
```

**@timestamp Filtering - AVOID:**
```
WHERE @timestamp >= ?start_date  # ✗ Agent handles this via execute_esql
WHERE @timestamp <= ?end_date    # ✗ Cross-cutting concern
```

**ES|QL Parameter Syntax:**
```
WHERE category == ?category
WHERE deployment_date >= ?deploy_start  # Use business dates, not @timestamp
LIMIT ?limit  # Optional - consider if necessary
```

**Method Template:**
```python
def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
    \"\"\"Generate PARAMETERIZED versions for Agent Builder

    Use ?parameter syntax. NO LIKE/RLIKE operators!
    \"\"\"
    param_queries = []

    param_queries.append({{
        "query_type": "parameterized",
        "name": "parameterized_query_name",
        "description": "Configurable version of X",
        "tool_metadata": {{  # REQUIRED for Agent Builder
            "tool_id": "{company_slug}_{dept_slug}_configurable",
            "description": "Analyzes data with business-specific filters. Focus on domain logic, not time ranges (agents handle those).",
            "tags": ["analytics", "configurable", "esql"]
        }},
        "esql": \"\"\"
            FROM index_name
            | WHERE category == ?category
            | WHERE status == ?status
            | STATS aggregation BY field
            | SORT _count DESC
            | LIMIT 100
        \"\"\",
        "parameters": {{
            "category": {{
                "type": "keyword",
                "description": "Business category filter",
                "default": "example_category",
                "required": True
            }},
            "status": {{
                "type": "keyword",
                "description": "Status filter (active, pending, completed)",
                "default": "active",
                "required": False
            }}
        }},
        "base_query": "related_scripted_query_name",
        "agent_builder_ready": True
    }})

    # Add 2-4 more parameterized queries...

    return param_queries
```

🚨🚨🚨 CRITICAL - @timestamp ANTI-PATTERN 🚨🚨🚨
NEVER EVER parameterize @timestamp! This is the #1 most common mistake!

❌ WRONG (DO NOT GENERATE THIS):
```esql
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
```

✅ CORRECT (USE THIS INSTEAD):
```esql
| WHERE @timestamp >= NOW() - 7 days  # Relative time with NOW()
```

The ONLY time-based parameters allowed are for BUSINESS date fields (order_date, created_at, etc.) - NEVER @timestamp!

🚨🚨🚨 CRITICAL - INTEGER DIVISION ANTI-PATTERN 🚨🚨🚨
ALWAYS use TO_DOUBLE() when dividing aggregated fields! Integer division truncates to 0!

❌ WRONG (produces 0 or 100 only):
```esql
| EVAL success_rate = ((total - failures) / total) * 100
```

✅ CORRECT (produces accurate percentages like 95.7):
```esql
| EVAL success_rate = ((total - failures) / TO_DOUBLE(total)) * 100
```

**WHY**: In ES|QL, dividing two integers performs integer division and truncates the result.
- (95 / 100) = 0 (WRONG - integer division)
- (95 / TO_DOUBLE(100)) = 0.95 (CORRECT - float division)

**RULE**: If you see division (/) in an EVAL, wrap the denominator in TO_DOUBLE() UNLESS:
- You already use TO_DOUBLE(): ✓ `field / TO_DOUBLE(total)`
- You multiply by float first: ✓ `field * 100.0 / total`
- You divide by float literal: ✓ `milliseconds / 1000.0`

🚨🚨🚨 CRITICAL - NULL HANDLING ANTI-PATTERN 🚨🚨🚨
ALWAYS include NULL checks with negative filters! ES|QL silently excludes NULL values!

❌ WRONG (silently excludes docs where field is NULL - DATA LOSS):
```esql
| WHERE status != "success"
| WHERE NOT(error_type LIKE "*timeout*")
```

✅ CORRECT (includes NULL values - complete data):
```esql
| WHERE status != "success" OR status IS NULL
| WHERE NOT(error_type LIKE "*timeout*") OR error_type IS NULL
```

**WHY**: ES|QL excludes NULL/missing fields from negative filters (!=, NOT, NOT LIKE).
- Documents where the field is NULL are SILENTLY EXCLUDED even though they match "not X"
- ESPECIALLY CRITICAL for security queries - missing data = missed threats!

**RULE**: When using negative filters (!=, NOT, NOT LIKE, NOT IN), append `OR field IS NULL` UNLESS:
- Field is guaranteed to exist (e.g., @timestamp)
- You explicitly want to exclude nulls (rare - document this in description)

Generate ONLY the method implementation. Do NOT include class definition or imports."""

        if self.llm_client:
            code = self._call_llm_for_method(prompt, max_tokens=5000)
        else:
            code = """    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        return []"""

        return code

    def _generate_rag_queries(self, config: Dict[str, Any], esql_docs: str) -> str:
        """Generate ONLY the generate_rag_queries() method

        Target: ~6K tokens
        Returns: Just the method code, not the full class
        """
        # Get tool metadata instructions
        tool_metadata_prompt = self._get_tool_metadata_instructions(config)

        # Get company and department slugs for the template
        company_slug = config['company_name'].lower().replace(' ', '_')[:15]
        dept_slug = config.get('department', 'analytics').lower().replace(' ', '_')[:10]

        # Get endpoint IDs for substitution in prompt
        rerank_endpoint = self.inference_endpoints['rerank']
        completion_endpoint = self.inference_endpoints['completion']

        prompt = f"""Generate the `generate_rag_queries()` method for a QueryGeneratorModule.

**Customer Context:**
Company: {config["company_name"]}
Department: {config["department"]}
Pain Points: {", ".join(config["pain_points"])}

{tool_metadata_prompt}

**Task**: Generate 1-3 RAG queries using MATCH -> RERANK -> INLINE STATS -> COMPLETION pipeline.

**CRITICAL RAG Architecture:**
1. MATCH: Semantic search across text fields with relevance tuning
2. RERANK: ML-based relevance scoring
3. INLINE STATS (NOT STATS!): Aggregate context without losing fields
4. COMPLETION: LLM generates answer from context

**IMPORTANT - Use Relevance Tuning:**
ALWAYS use MATCH with named parameters for relevance tuning:
- `boost`: Increase/decrease field importance (e.g., {"boost": 2.0} for titles, {"boost": 0.5} for descriptions)
- `fuzziness`: Allow typos/variations (e.g., {"fuzziness": "AUTO"} or {"fuzziness": "1"})

Example:
```esql
WHERE MATCH(title, ?query, {"boost": 2.0, "fuzziness": "AUTO"})
   OR MATCH(description, ?query, {"boost": 1.0, "fuzziness": "1"})
   OR MATCH(content, ?query, {"boost": 0.5})
```

**ES|QL Reference (RAG Commands):**
{esql_docs}

**CRITICAL - INLINE STATS vs STATS:**
- WRONG: `| STATS context = MV_CONCAT(field, " --- ")`  ← Loses all fields except context!
- CORRECT: `| INLINE STATS all_context = MV_CONCAT(context, " --- ")`  ← Preserves fields!
- NEVER use "\\n" as MV_CONCAT separator — ES|QL does NOT support newlines in string literals

**Method Template:**
```python
def generate_rag_queries(self) -> List[Dict[str, Any]]:
    \"\"\"Generate RAG queries (MATCH -> RERANK -> COMPLETION)

    For semantic search + AI-powered answers via Agent Builder.
    CRITICAL: Use INLINE STATS not STATS!
    \"\"\"
    rag_queries = []

    rag_queries.append({{
        "query_type": "rag",
        "name": "semantic_search_rag",
        "description": "Ask questions about [data type]",
        "tool_metadata": {{  # REQUIRED for Agent Builder
            "tool_id": "{company_slug}_{dept_slug}_ai_search",
            "description": "Searches knowledge base with AI answers. Provides contextual responses using semantic search and completion.",
            "tags": ["search", "ai", "rag", "esql"]
        }},
        "esql": \"\"\"
            FROM index_name METADATA _score
            | WHERE MATCH(text_field1, ?user_question, {"boost": 2.0, "fuzziness": "AUTO"})
                OR MATCH(text_field2, ?user_question, {"boost": 1.5, "fuzziness": "1"})
                OR MATCH(text_field3, ?user_question, {"boost": 1.0})
            | WHERE @timestamp >= NOW() - 120 days
            | SORT _score DESC
            | LIMIT 100
            | RERANK ?user_question
                ON text_field1, text_field2, text_field3
                WITH {{"inference_id": """ + f'"{rerank_endpoint}"' + """}}
            | LIMIT 5
            | EVAL context = CONCAT(
                "Record: ", id_field, " | ",
                "Field1: ", text_field1, " | ",
                "Field2: ", text_field2
              )
            | INLINE STATS all_context = MV_CONCAT(context, " --- ")
            | EVAL prompt = CONCAT(
                "Based on these records: ",
                all_context,
                " Question: ", ?user_question,
                " Provide a detailed answer:"
              )
            | COMPLETION answer = prompt
                WITH {{"inference_id": """ + f'"{completion_endpoint}"' + """}}
            | KEEP answer, all_context
        \"\"\",
        "parameters": {{
            "user_question": {{
                "type": "string",
                "description": "Question to answer",
                "required": True,
                "example": "What are the main issues with...?"
            }}
        }},
        "search_fields": ["text_field1", "text_field2"],
        "rerank_fields": ["text_field1", "text_field2", "text_field3"],
        "context_fields": ["id_field", "text_field1", "text_field2", "status"],
        "time_boundary": "120 days"
    }})

    # Optionally add 1-2 more RAG queries for different use cases...

    return rag_queries
```

**IMPORTANT**:
- **ALWAYS use boost and fuzziness parameters** in MATCH for relevance tuning
- Identify 3-5 text fields for MATCH (description, content, feedback, notes, comments, etc.)
- Use DIFFERENT boost values to prioritize fields (2.0 for important, 1.5 for medium, 1.0 or 0.5 for less important)
- Add fuzziness ("AUTO" or "1") to handle typos and variations
- Select 2-4 most important fields for RERANK
- Use INLINE STATS to aggregate context
- Set appropriate time boundary (30/90/120 days)

Generate ONLY the method implementation. Do NOT include class definition or imports."""

        if self.llm_client:
            code = self._call_llm_for_method(prompt, max_tokens=7000)
        else:
            code = """    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        return []"""

        return code

    def _combine_query_methods(self, config: Dict[str, Any], scripted: str, parameterized: str, rag: str) -> str:
        """Combine three method implementations into a complete QueryGeneratorModule

        Args:
            config: Demo configuration
            scripted: generate_queries() method code
            parameterized: generate_parameterized_queries() method code
            rag: generate_rag_queries() method code

        Returns:
            Complete Python module with class definition and all three methods
        """
        company_class = config["company_name"].replace(" ", "")

        # Indent each method to be part of the class (4 spaces)
        def indent_method(code: str) -> str:
            """Add 4-space indentation to each line of method code"""
            lines = code.strip().split('\n')
            indented_lines = ['    ' + line for line in lines]
            return '\n'.join(indented_lines)

        scripted_indented = indent_method(scripted)
        parameterized_indented = indent_method(parameterized)
        rag_indented = indent_method(rag)

        # Build complete module with all three methods
        full_module = f"""from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class {company_class}QueryGenerator(QueryGeneratorModule):
    \"\"\"Query generator for {config["company_name"]} - {config["department"]}

    Generates three types of queries:
    1. Scripted (tested, non-parameterized)
    2. Parameterized (Agent Builder tools)
    3. RAG (semantic search + LLM completion)
    \"\"\"

{scripted_indented}

{parameterized_indented}

{rag_indented}

    def get_query_progression(self) -> List[str]:
        \"\"\"Order to present SCRIPTED queries (for demos)\"\"\"
        # Extract query names from scripted queries
        queries = self.generate_queries()
        return [q.get('name', f'query_{{i}}') for i, q in enumerate(queries)]
"""

        return full_module

    def _call_llm_for_method(self, prompt: str, max_tokens: int = 6000) -> str:
        """Call LLM to generate a single method implementation

        Args:
            prompt: LLM prompt requesting specific method
            max_tokens: Maximum tokens for response

        Returns:
            Method code (including def line and body)
        """
        logger.info(f"📤 Calling LLM with prompt length: {len(prompt)} characters, max_tokens: {max_tokens}")

        stop_reason = None
        if hasattr(self.llm_client, 'messages'):  # Anthropic
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            code = response.content[0].text
            stop_reason = getattr(response, 'stop_reason', None)
            logger.info(f"📥 LLM response length: {len(code)} characters, stop_reason: {stop_reason}")
        elif hasattr(self.llm_client, 'chat'):  # OpenAI
            response = self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            code = response.choices[0].message.content
            stop_reason = getattr(response.choices[0], 'finish_reason', None)
            logger.info(f"📥 LLM response length: {len(code)} characters, stop_reason: {stop_reason}")
        else:
            return ""

        # Detect truncated output
        if stop_reason in ('max_tokens', 'length'):
            logger.warning(f"⚠️ Method output truncated (stop_reason={stop_reason}, max_tokens={max_tokens}). Code will likely have syntax errors.")

        # Extract Python code if wrapped in markdown
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
            logger.info(f"✂️  Extracted Python code: {len(code)} characters")

        return code.strip()

    def _generate_guide_module(self, config: Dict[str, Any], module_path: Path):
        """Generate the demo guide module

        Uses fixed template since structure is always the same - only content varies.
        Content is dynamically generated from config/datasets/queries at runtime.
        """
        # Sanitize company name for use as Python class name
        # Remove parentheses, brackets, and other special characters that would break syntax
        import re
        company_class = re.sub(r'[^a-zA-Z0-9_]', '', config['company_name'].replace(' ', ''))

        # Generate comprehensive demo guide content using LLM
        guide_content = self._generate_demo_guide_content(config, module_path)

        # Fixed template - structure doesn't change, only runtime content
        code = f"""from src.framework.base import DemoGuideModule, DemoConfig
from typing import Dict, List, Any, Optional
import pandas as pd

class {company_class}DemoGuide(DemoGuideModule):
    \"\"\"Demo guide for {config['company_name']} - {config['department']}\"\"\"

    def __init__(self, config: DemoConfig, datasets: Dict[str, pd.DataFrame],
                 queries: List[Dict], aha_moment: Optional[Dict] = None):
        \"\"\"Initialize with demo context\"\"\"
        super().__init__(config, datasets, queries, aha_moment)

    def generate_guide(self) -> str:
        \"\"\"Generate customized demo guide\"\"\"
        return '''{guide_content}'''

    def get_talk_track(self) -> Dict[str, str]:
        \"\"\"Talk track for each query\"\"\"
        # Can be customized per demo as needed
        return {{}}

    def get_objection_handling(self) -> Dict[str, str]:
        \"\"\"Common objections and responses\"\"\"
        return {{
            "complexity": "ES|QL syntax is SQL-like and easier than complex aggregations",
            "performance": "Queries run on indexed data with millisecond response times",
            "learning_curve": "Most teams productive within days, not weeks"
        }}
"""

        # Validate syntax before saving (with auto-fix on failure)
        code = self._validate_python_syntax(code, 'demo_guide.py')

        # Save the module
        module_file = module_path / 'demo_guide.py'
        module_file.write_text(code)

    def _format_single_dataset_spec(self, dataset_name: str, dataset_spec: Dict[str, Any]) -> str:
        """Format a single dataset's field specifications into prompt guidance

        Args:
            dataset_name: Name of the dataset
            dataset_spec: Dataset specification with fields dict

        Returns:
            Formatted string with field guidance for this dataset
        """
        sections = []
        sections.append(f"\n## Dataset: {dataset_name}")

        fields_spec = dataset_spec.get('fields', {})

        if not fields_spec:
            sections.append("  (No field specifications provided)")
            return "\n".join(sections)

        sections.append("\n**Field Specifications:**\n")

        for field_name, field_spec in fields_spec.items():
            field_type = field_spec.get('type', 'unknown')

            # Start with field name and type
            sections.append(f"- **{field_name}** ({field_type}):")

            # Add description if available
            if 'description' in field_spec:
                sections.append(f"  - Description: {field_spec['description']}")

            # Type-specific formatting
            if field_type == 'keyword':
                # Cardinality
                if 'cardinality' in field_spec:
                    sections.append(f"  - Cardinality: {field_spec['cardinality']} distinct values")

                # Examples
                if 'examples' in field_spec:
                    examples = field_spec['examples']
                    examples_str = ", ".join([f'"{ex}"' for ex in examples[:8]])
                    if len(examples) > 8:
                        examples_str += f", ... ({len(examples)} total)"
                    sections.append(f"  - Example Values: {examples_str}")

                # Diversity guidance
                if 'diversity_guidance' in field_spec:
                    sections.append(f"  - Diversity: {field_spec['diversity_guidance']}")

            elif field_type in ('text', 'semantic_text'):
                # Content pattern
                if 'content_pattern' in field_spec:
                    sections.append(f"  - Content Pattern: {field_spec['content_pattern']}")

                # Query alignment (CRITICAL for semantic search)
                if 'query_alignment' in field_spec:
                    sections.append(f"  - Query Alignment: {field_spec['query_alignment']}")

                # Diversity guidance
                if 'diversity_guidance' in field_spec:
                    sections.append(f"  - Diversity: {field_spec['diversity_guidance']}")

                # Tiering guidance (for semantic_text)
                if field_type == 'semantic_text' and 'tiering_guidance' in field_spec:
                    sections.append(f"  - Tiering: {field_spec['tiering_guidance']}")

                # Coherence rules (for semantic_text)
                if 'coherence_rules' in field_spec:
                    rules = field_spec['coherence_rules']
                    if 'must_reference' in rules:
                        sections.append(f"  - Coherence: Content MUST reference values from fields: {rules['must_reference']}")
                    if rules.get('uniqueness') == 'each row unique':
                        sections.append(f"  - Uniqueness: Every value MUST be unique across all rows")

            elif field_type == 'geo_point':
                # Geographic region
                if 'geographic_region' in field_spec:
                    sections.append(f"  - Region: {field_spec['geographic_region']}")

                # Clustering guidance
                if 'clustering_guidance' in field_spec:
                    sections.append(f"  - Clustering: {field_spec['clustering_guidance']}")

                # Coordinate precision
                if 'coordinate_precision' in field_spec:
                    sections.append(f"  - Precision: {field_spec['coordinate_precision']}")

                # Format requirement
                sections.append(f"  - Format: Dict with 'lat' and 'lon' keys (REQUIRED for geo_point mapping)")

            else:
                # For other types (date, boolean, integer, float, etc.)
                if 'examples' in field_spec:
                    examples_str = ", ".join([str(ex) for ex in field_spec['examples'][:5]])
                    sections.append(f"  - Examples: {examples_str}")

                if 'value_range' in field_spec:
                    sections.append(f"  - Range: {field_spec['value_range']}")

            sections.append("")  # Blank line between fields

        return "\n".join(sections)

    def _format_field_specifications_for_prompt(self, data_specifications: Dict[str, Any]) -> str:
        """Format data specifications into rich prompt guidance for LLM

        Transforms data_specifications.json structure into detailed field requirements
        with examples, cardinality, content patterns, and diversity guidance.

        Args:
            data_specifications: Domain-specific value specifications from expander

        Returns:
            Formatted string with rich field guidance for data generation prompt
        """
        sections = []

        datasets = data_specifications.get('datasets', {})

        for dataset_name, dataset_spec in datasets.items():
            sections.append(self._format_single_dataset_spec(dataset_name, dataset_spec))

        result = "\n".join(sections)
        logger.debug(f"Formatted field specifications: {len(result)} characters")
        return result

    def _generate_single_dataset_method(
        self,
        dataset_name: str,
        dataset_spec: Dict[str, Any],
        config: Dict[str, Any],
        data_requirements: Dict,
        size_preference: str,
        ranges: Dict[str, Any],
        use_enhanced: bool = False
    ) -> str:
        """Generate a single _generate_<dataset_name>() method via LLM

        Args:
            dataset_name: Name of the dataset (e.g. 'provider_directory')
            dataset_spec: Field specifications for this dataset (from data_specifications)
            config: Demo configuration
            data_requirements: Full data requirements dict (for relationship context)
            size_preference: 'small', 'medium', or 'large'
            ranges: Size range limits for this preference
            use_enhanced: Whether to include enhanced clustering guidance

        Returns:
            Method code string (def _generate_<name>(self): ...)
        """
        # Format field specs for just this dataset
        field_guidance = self._format_single_dataset_spec(dataset_name, dataset_spec)

        # Build relationship context for this dataset
        relationship_lines = []
        ds_req = data_requirements.get(dataset_name, {})
        ds_relationships = ds_req.get('relationships', [])
        if ds_relationships:
            relationship_lines.append(f"\nRelationships for {dataset_name}:")
            for rel in ds_relationships:
                relationship_lines.append(f"  - {rel}")
        relationship_context = "\n".join(relationship_lines)

        # Determine row count guidance
        ds_type = ds_req.get('type', 'lookup')
        if ds_type == 'data_stream':
            row_guidance = f"timeseries data: {ranges['timeseries_typical']} rows (MAX {ranges['timeseries_max']:,})"
        elif ds_type == 'lookup':
            row_guidance = f"reference/lookup data: {ranges['reference_typical']} rows (MAX {ranges['reference_max']:,})"
        else:
            row_guidance = f"{ranges['per_dataset_typical']} rows (MAX {ranges['per_dataset_max']:,})"

        # Build the per-dataset prompt
        prompt = f"""Generate a single Python method that creates the '{dataset_name}' dataset.

Company: {config["company_name"]}
Industry: {config["industry"]}
Department: {config["department"]}

{field_guidance}
{relationship_context}

Dataset size: {row_guidance} ({size_preference.upper()} preference)

CRITICAL RULES:
- ALL arrays in pd.DataFrame() MUST have EXACTLY the same length
- @timestamp columns MUST use datetime.now() as END date, go BACKWARDS max 120 days
- NEVER hardcode dates like '2023-01-01'
- For geo_point fields: use dict with 'lat' and 'lon' keys
- For semantic_text fields: generate ONLY that field (no separate text duplicate)
- Generate rows as COMPLETE ENTITIES - all fields logically consistent
- Every text/semantic_text value MUST be unique across all rows
- When using .format(), ensure placeholder names EXACTLY match keyword arguments
- Avoid empty list errors: always provide fallback for filtered lists
- F-strings CANNOT contain backslash escapes inside {{}} expression parts
- ALL string literals MUST fit on a SINGLE LINE - never let a string wrap across lines
- Keep description strings concise (under 200 chars) to avoid line-length issues
- Use self.safe_choice() instead of np.random.choice() - NEVER call np.random.choice directly
- Use self.random_timedelta() for timestamps - NEVER construct timestamps manually

These helper methods are ALREADY DEFINED on the class. Use them exactly as shown:

```python
# safe_choice(choices, size=None, weights=None, replace=True)
# - size=None returns a SINGLE SCALAR value (string, int, etc.)
# - size=N returns a numpy ARRAY of N values
# - Handles complex elements (lists, tuples, dicts) automatically
# - Automatically normalizes probability weights
# Examples:
tag = self.safe_choice(["A", "B", "C"])  # returns ONE string like "B"
tags = self.safe_choice(["A", "B", "C"], size=100)  # returns array of 100
tags = self.safe_choice(["A", "B", "C"], size=100, weights=[0.5, 0.3, 0.2])

# random_timedelta(start_date, end_date=None, days=None, hours=None, minutes=None, max_days=None)
# Examples:
self.random_timedelta(start, end)  # random datetime between start and end
self.random_timedelta(datetime.now(), max_days=120)  # random within last 120 days
self.random_timedelta(base, days=5, hours=3)  # base + exact offset
```

Generate ONLY the method implementation. Do NOT include class definition, imports, or safe_choice/random_timedelta definitions.

Method signature:
```python
def _generate_{dataset_name}(self):
    \"\"\"Generate {dataset_name} dataset\"\"\"
    # ... generate data ...
    return pd.DataFrame({{...}})
```

Generate the complete method:"""

        if use_enhanced:
            prompt += """

ENHANCED DATA: Use skewed distributions (beta, lognormal, poisson) for numeric fields.
Use weighted choices for categorical fields. Create realistic clustering patterns."""

        if self.llm_client:
            code = self._call_llm_for_method(prompt, max_tokens=16000)

            # Validate method syntax early (before combining with other methods)
            # Much cheaper to retry one method than fix a 900+ line combined module
            syntax_error = self._check_method_syntax(code, dataset_name)
            if syntax_error:
                logger.warning(f"⚠️ Method _generate_{dataset_name}() has syntax error: {syntax_error}")
                logger.info(f"🔄 Retrying _generate_{dataset_name}() with stricter prompt...")

                # Retry with extra guidance about the specific error
                retry_prompt = prompt + f"""

IMPORTANT: Your previous attempt had a syntax error: {syntax_error}
Common causes:
- Unterminated string literals (strings that span multiple lines without triple quotes)
- Keep ALL string values on a SINGLE LINE, even if long
- Use triple quotes (\"\"\"...\"\"\") for multi-line strings
- Ensure all parentheses, brackets, and braces are properly closed

Generate the corrected method:"""

                code = self._call_llm_for_method(retry_prompt, max_tokens=16000)

                # Check again - if still broken, try a quick fix
                syntax_error_2 = self._check_method_syntax(code, dataset_name)
                if syntax_error_2:
                    logger.warning(f"⚠️ Retry also has syntax error: {syntax_error_2}. Attempting quick fix...")
                    code = self._fix_unterminated_strings(code)
        else:
            # Mock fallback for testing
            code = f"""def _generate_{dataset_name}(self):
    \"\"\"Generate {dataset_name} dataset\"\"\"
    n = 100
    return pd.DataFrame({{
        'id': [f'{dataset_name}_{{i}}' for i in range(n)]
    }})"""

        return code

    def _check_method_syntax(self, code: str, dataset_name: str) -> Optional[str]:
        """Check if a generated method has valid Python syntax.

        Wraps the method in a minimal class shell and tries to compile it.

        Args:
            code: Method code string (def _generate_xxx(self): ...)
            dataset_name: Name for error messages

        Returns:
            Error message string if syntax error, None if valid
        """
        # Wrap method in a minimal compilable shell
        lines = code.split('\n')
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        # Find def line's indent to normalize
        base_indent = 0
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith('def '):
                base_indent = len(line) - len(stripped)
                break

        # Build test module with method inside a class
        test_lines = ["class _Test:"]
        for line in lines:
            if not line.strip():
                test_lines.append("")
            elif len(line) >= base_indent and line[:base_indent].strip() == '':
                test_lines.append("    " + line[base_indent:])
            else:
                test_lines.append("    " + line.lstrip())
        test_code = "\n".join(test_lines)

        try:
            compile(test_code, f'_generate_{dataset_name}', 'exec')
            return None  # Valid
        except SyntaxError as e:
            return f"{e.msg} (line {e.lineno})"

    @staticmethod
    def _fix_unterminated_strings(code: str) -> str:
        """Best-effort fix for unterminated string literals in generated code.

        Scans each line for unmatched quotes and closes them.
        """
        fixed_lines = []
        for line in code.split('\n'):
            stripped = line.rstrip()
            # Skip empty lines and comments
            if not stripped or stripped.lstrip().startswith('#'):
                fixed_lines.append(line)
                continue

            # Count unescaped quotes
            in_string = None
            i = 0
            while i < len(stripped):
                char = stripped[i]
                if char == '\\' and in_string:
                    i += 2  # Skip escaped character
                    continue
                if char in ('"', "'"):
                    # Check for triple quotes
                    triple = stripped[i:i+3]
                    if triple in ('"""', "'''"):
                        if in_string == triple:
                            in_string = None
                            i += 3
                            continue
                        elif in_string is None:
                            in_string = triple
                            i += 3
                            continue
                    # Single quotes
                    if in_string == char:
                        in_string = None
                    elif in_string is None:
                        in_string = char
                i += 1

            # If we're still in a string at end of line, close it
            if in_string and in_string in ('"', "'"):
                fixed_lines.append(stripped + in_string + ',')
                logger.warning(f"Fixed unterminated string: {stripped[:80]}...")
            else:
                fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def _combine_data_methods(
        self,
        config: Dict[str, Any],
        dataset_methods: Dict[str, str],
        data_requirements: Dict,
        data_specifications: Optional[Dict[str, Any]] = None
    ) -> str:
        """Combine per-dataset method strings into a complete DataGeneratorModule

        Follows the same pattern as _combine_query_methods(): assembles individual
        method implementations into a complete Python module with boilerplate.

        Args:
            config: Demo configuration
            dataset_methods: Dict mapping dataset_name -> method code string
            data_requirements: Data requirements dict (for relationships, semantic fields, descriptions)
            data_specifications: Optional data specifications (for richer metadata)

        Returns:
            Complete Python module string
        """
        company_class = config["company_name"].replace(" ", "")

        # Indent each method to be part of the class (4 spaces)
        def indent_method(code: str) -> str:
            """Ensure method code has exactly 4-space class-level indentation.

            Detects the def line's current indentation as the base level,
            strips that base from all lines, then adds 4-space class prefix.
            This handles LLM output regardless of its original indentation.
            """
            lines = code.split('\n')
            # Remove leading/trailing empty lines only (NOT strip which
            # destroys the first line's indentation context)
            while lines and not lines[0].strip():
                lines.pop(0)
            while lines and not lines[-1].strip():
                lines.pop()

            # Find the base indentation from the def line
            base_indent = 0
            for line in lines:
                stripped = line.lstrip()
                if stripped.startswith('def '):
                    base_indent = len(line) - len(stripped)
                    break

            indented_lines = []
            for line in lines:
                if not line.strip():
                    indented_lines.append('')
                else:
                    # Strip base indentation, then add 4-space class level
                    if len(line) >= base_indent and line[:base_indent].strip() == '':
                        indented_lines.append('    ' + line[base_indent:])
                    else:
                        # Safety: line has less indent than base, just strip all and add 4
                        indented_lines.append('    ' + line.lstrip())
            return '\n'.join(indented_lines)

        # Build generate_datasets() method that calls each sub-method
        dataset_calls = []
        for ds_name in dataset_methods:
            dataset_calls.append(f"        datasets['{ds_name}'] = self._generate_{ds_name}()")
        generate_datasets_body = "\n".join(dataset_calls)

        # Auto-generate get_semantic_fields() from data requirements
        semantic_fields_dict = {}
        for ds_name, ds_req in data_requirements.items():
            sem_fields = ds_req.get('semantic_fields', [])
            if sem_fields:
                semantic_fields_dict[ds_name] = sem_fields

        semantic_fields_code = "{\n"
        for ds_name, fields in semantic_fields_dict.items():
            semantic_fields_code += f"            '{ds_name}': {fields},\n"
        semantic_fields_code += "        }"

        # Auto-generate get_data_descriptions() from dataset names/types
        descriptions_code = "{\n"
        for ds_name, ds_req in data_requirements.items():
            ds_type = ds_req.get('type', 'lookup')
            ds_label = ds_name.replace("_", " ").title()
            descriptions_code += f"            '{ds_name}': '{ds_label} ({ds_type})',\n"
        descriptions_code += "        }"

        # Auto-generate get_relationships() from data requirements
        relationships = []
        for ds_name, ds_req in data_requirements.items():
            for rel in ds_req.get('relationships', []):
                # Relationships can be strings like "joins to X on field_name"
                # or structured data - include as comments for clarity
                relationships.append(f"            # {ds_name}: {rel}")

        relationships_code = "[\n"
        if relationships:
            relationships_code += "\n".join(relationships) + "\n"
        relationships_code += "        ]"

        # Indent all dataset methods
        indented_methods = []
        for ds_name, method_code in dataset_methods.items():
            indented_methods.append(indent_method(method_code))

        methods_combined = "\n\n".join(indented_methods)

        # Build the complete module
        full_module = f'''from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List


class {company_class}DataGenerator(DataGeneratorModule):
    """Data generator for {config["company_name"]} - {config["department"]}"""

    @staticmethod
    def safe_choice(choices, size=None, weights=None, replace=True):
        """Safer alternative to np.random.choice with automatic probability normalization.

        Automatically handles complex elements (lists, tuples, dicts) by falling back
        to Python's random.choices when numpy would fail with shape errors.
        """
        use_python_random = False
        if len(choices) > 0:
            first_type = type(choices[0])
            if first_type in (list, tuple, dict):
                use_python_random = True

        if use_python_random:
            if size is None:
                if weights is not None:
                    return random.choices(choices, weights=weights, k=1)[0]
                else:
                    return random.choice(choices)
            if weights is not None:
                return random.choices(choices, weights=weights, k=size)
            else:
                return random.choices(choices, k=size)

        if weights is not None:
            weights = np.array(weights, dtype=float)
            if len(weights) > len(choices):
                import logging
                logging.warning(f"Truncating {{len(weights) - len(choices)}} excess weights")
                weights = weights[:len(choices)]
            elif len(weights) < len(choices):
                raise ValueError(
                    f"Not enough weights for choices!\\n"
                    f"  Choices ({{len(choices)}}): {{choices}}\\n"
                    f"  Weights ({{len(weights)}}): {{weights.tolist()}}"
                )
            probabilities = weights / weights.sum()
            if size is None:
                return np.random.choice(choices, p=probabilities, replace=replace)
            return np.random.choice(choices, size=size, p=probabilities, replace=replace)
        else:
            if size is None:
                return np.random.choice(choices)
            return np.random.choice(choices, size=size, replace=replace)

    @staticmethod
    def random_timedelta(start_date, end_date=None, days=None, hours=None, minutes=None, max_days=None):
        """Generate random timedelta-adjusted datetime, handling numpy int64 conversion.

        Usage patterns:
            random_timedelta(start, end)  # random datetime between start and end
            random_timedelta(datetime.now(), max_days=120)  # random datetime within last 120 days
            random_timedelta(base, days=5, hours=3)  # base + 5 days + 3 hours
        """
        if max_days is not None:
            # Random timestamp within last max_days days from start_date
            random_seconds = int(np.random.random() * int(max_days) * 86400)
            return start_date - timedelta(seconds=random_seconds)

        if end_date is not None:
            delta = end_date - start_date
            random_seconds = int(np.random.random() * delta.total_seconds())
            return start_date + timedelta(seconds=random_seconds)

        delta_kwargs = {{}}
        if days is not None:
            delta_kwargs['days'] = int(days)
        if hours is not None:
            delta_kwargs['hours'] = int(hours)
        if minutes is not None:
            delta_kwargs['minutes'] = int(minutes)

        return start_date + timedelta(**delta_kwargs)

    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        """Generate datasets with EXACT fields from requirements"""
        datasets = {{}}

{generate_datasets_body}

        return datasets

{methods_combined}

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships from requirements"""
        return {relationships_code}

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {descriptions_code}

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        """Return fields that should use semantic_text mapping"""
        return {semantic_fields_code}
'''

        return full_module

    def _build_search_field_guidance(
        self,
        query_strategy: Dict[str, Any],
        data_profile: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build explicit field mapping guidance for search query generation.

        Produces a SEARCH FIELD MAPPING section that tells the LLM exactly which
        fields to use for BM25 vs semantic search. Only called for search demos.

        Args:
            query_strategy: Strategy with datasets and required_fields
            data_profile: Optional profiled data with sample values

        Returns:
            Formatted guidance string for the query generation prompt
        """
        lines = ["", "**SEARCH FIELD MAPPING (use these exact fields):**"]

        for dataset in query_strategy.get('datasets', []):
            ds_name = dataset.get('name', 'unknown')
            fields = dataset.get('required_fields', dataset.get('fields', {}))
            if not isinstance(fields, dict):
                continue

            bm25_fields = []
            semantic_fields = []
            keyword_fields = []

            for field_name, field_type in fields.items():
                if field_type == 'text':
                    bm25_fields.append(field_name)
                elif field_type == 'semantic_text':
                    semantic_fields.append(field_name)
                elif field_type == 'keyword':
                    keyword_fields.append(field_name)

            lines.append(f"\n  Dataset: {ds_name}")
            if bm25_fields:
                lines.append(f"    BM25 fields (text): {bm25_fields}")
            if semantic_fields:
                lines.append(f"    Semantic fields (semantic_text): {semantic_fields}")
            if keyword_fields:
                lines.append(f"    Filter fields (keyword): {keyword_fields}")

            if bm25_fields and semantic_fields:
                lines.append(
                    f"    FORK/FUSE: Use BM25 MATCH on {bm25_fields} and semantic search on {semantic_fields}"
                )

            # Include sample content from data profile if available
            if data_profile and 'datasets' in data_profile:
                profile_ds = data_profile.get('datasets', {}).get(ds_name, {})
                profile_fields = profile_ds.get('fields', {})

                for field_name in bm25_fields + semantic_fields:
                    if field_name in profile_fields:
                        field_info = profile_fields[field_name]
                        sample_values = field_info.get('sample_values', field_info.get('top_values', []))
                        if sample_values:
                            # Show first 3 samples, truncated
                            samples = []
                            for v in sample_values[:3]:
                                v_str = str(v)
                                if len(v_str) > 100:
                                    v_str = v_str[:100] + "..."
                                samples.append(v_str)
                            lines.append(f"    Sample {field_name} values: {samples}")

        lines.append("")
        lines.append("  IMPORTANT: Use MATCH() only on 'text' fields, not on 'keyword' or 'semantic_text' fields.")
        lines.append("  For semantic search, reference 'semantic_text' fields in RERANK and COMPLETION commands.")
        lines.append("")

        return "\n".join(lines)

    def _generate_data_module_with_requirements(self, config: Dict[str, Any],
                                                 module_path: Path,
                                                 data_requirements: Dict,
                                                 data_specifications: Optional[Dict[str, Any]] = None,
                                                 progress_callback: Optional[callable] = None):
        """Generate data module based on query strategy requirements

        Args:
            config: Demo configuration
            module_path: Path to module directory
            data_requirements: Data requirements extracted from query strategy
            data_specifications: Optional domain-specific value specifications (for search demos)
            progress_callback: Optional progress callback for per-dataset reporting
        """
        from src.services.query_strategy_generator import QueryStrategyGenerator
        strategy_gen = QueryStrategyGenerator(self.llm_client)

        # Use rich specifications if available, otherwise fall back to basic formatting
        if data_specifications:
            logger.info("Using rich data specifications for field guidance")
            formatted_requirements = self._format_field_specifications_for_prompt(data_specifications)
        else:
            logger.info("Using basic field requirements (no specifications provided)")
            formatted_requirements = strategy_gen.get_field_info_for_prompts(data_requirements)

        # Get dataset size preference and calculate ranges
        size_preference = config.get('dataset_size_preference', 'medium')
        size_ranges = {
            'small': {
                'total_max': 5000,
                'per_dataset_max': 1000,
                'per_dataset_typical': '200-500',
                'timeseries_max': 3000,
                'timeseries_typical': '1000-2000',
                'reference_max': 500,
                'reference_typical': '50-200'
            },
            'medium': {
                'total_max': 15000,
                'per_dataset_max': 3000,
                'per_dataset_typical': '500-1500',
                'timeseries_max': 10000,
                'timeseries_typical': '3000-6000',
                'reference_max': 2000,
                'reference_typical': '200-1000'
            },
            'large': {
                'total_max': 50000,
                'per_dataset_max': 10000,
                'per_dataset_typical': '2000-5000',
                'timeseries_max': 30000,
                'timeseries_typical': '10000-20000',
                'reference_max': 5000,
                'reference_typical': '500-2000'
            }
        }

        ranges = size_ranges[size_preference]

        # Determine if we should use per-dataset split approach
        # Split when: 2+ datasets AND data_specifications available (rich field specs per dataset)
        num_datasets = len(data_requirements)
        use_split = num_datasets >= 2 and data_specifications is not None
        use_enhanced = config.get('use_enhanced_generation', False)

        if use_split:
            # === PER-DATASET SPLIT APPROACH ===
            # Generates each dataset method separately to avoid token limit truncation
            logger.info(f"Using per-dataset split approach for {num_datasets} datasets")

            datasets_spec = data_specifications.get('datasets', {})
            dataset_methods = {}

            for i, (ds_name, ds_spec) in enumerate(datasets_spec.items(), 1):
                # Report per-dataset progress within data module phase (0.16-0.28)
                if progress_callback:
                    sub_progress = 0.16 + ((i - 1) / num_datasets) * 0.12
                    progress_callback(sub_progress, f"🤖 Generating data module ({i}/{num_datasets}): {ds_name}...")

                logger.info(f"📤 Data Call {i}/{num_datasets}: Generating _generate_{ds_name}()...")
                method_code = self._generate_single_dataset_method(
                    dataset_name=ds_name,
                    dataset_spec=ds_spec,
                    config=config,
                    data_requirements=data_requirements,
                    size_preference=size_preference,
                    ranges=ranges,
                    use_enhanced=use_enhanced
                )
                dataset_methods[ds_name] = method_code
                logger.info(f"📥 Generated _generate_{ds_name}(): {len(method_code)} chars")

            # Combine all methods into complete module
            logger.info("🔧 Combining data methods into single module...")
            code = self._combine_data_methods(
                config=config,
                dataset_methods=dataset_methods,
                data_requirements=data_requirements,
                data_specifications=data_specifications
            )
        else:
            # === SINGLE-CALL APPROACH (1 dataset or no data_specifications) ===
            logger.info(f"Using single-call approach for {num_datasets} dataset(s)")

            prompt = f"""Generate a Python module that implements DataGeneratorModule for this customer:

Company: {config["company_name"]}
Department: {config["department"]}
Industry: {config["industry"]}
Pain Points: {", ".join(config["pain_points"])}
Use Cases: {", ".join(config["use_cases"])}
Dataset Size Preference: {size_preference.upper()}

{formatted_requirements}

CRITICAL - YOU MUST GENERATE DATA THAT EXACTLY MATCHES THE REQUIREMENTS ABOVE.

The module should:
1. Import necessary libraries and the base class
2. Implement a class that inherits from DataGeneratorModule
3. Generate datasets with the EXACT field names specified in requirements
4. Use the EXACT data types specified (keyword, date, float, text, etc.)
5. Create proper foreign key relationships as specified
6. Include semantic_text fields where specified
7. For fields with type "semantic_text" in the requirements, generate ONLY that field (do NOT create a separate "description" text field alongside a "semantic_description" semantic_text field — the semantic_text field IS the description)

CRITICAL - SEARCH DATA QUALITY (if generating search/document data):
- Generate rows as COMPLETE ENTITIES - all fields in a row must be logically consistent
  - If category="Security", the description MUST discuss security topics
  - NEVER generate random field combinations like category="Security" + description about "cooking tips"
- Avoid template-based generation patterns like "Dr. {{name}} specializes in {{specialty}}"
  - Instead, write unique natural-language text for each row
- Every text and semantic_text value MUST be unique across all rows
  - If you have 400 rows, you need 400 distinct descriptions
  - Use varied vocabulary, sentence structures, and detail levels
- For coherence_rules in field specs: content MUST reference the specified related fields

CRITICAL - TIMESTAMP REQUIREMENTS:
- All @timestamp or timestamp columns MUST use datetime.now() as the END date
- Generate data going BACKWARDS from today, maximum 120 days old
- NEVER hardcode dates like '2023-01-01' or generate future dates
- Use pd.date_range(end=datetime.now(), periods=N, freq='h') for timeseries data
- This ensures ES|QL queries with "NOW() - X days" will return results

CRITICAL - FIELD NAMING:
- Use EXACT field names from requirements (case-sensitive!)
- For timeseries datasets, use '@timestamp' not 'timestamp'
- Match field types exactly (keyword, date, float, text, geo_point)

CRITICAL - GEO_POINT FIELDS:
For fields with type 'geo_point', generate as DICT with 'lat' and 'lon' keys:
- ✅ CORRECT: {{'lat': 34.0522, 'lon': -118.2437}}
- ❌ WRONG: "34.0522,-118.2437" (will be detected as keyword, ST_DISTANCE queries will fail!)
- ❌ WRONG: [-118.2437, 34.0522] (GeoJSON format not reliably detected)

Example generation:
```python
locations = []
for i in range(n):
    lat = base_lat + np.random.normal(0, 0.05)  # Add jitter
    lon = base_lon + np.random.normal(0, 0.05)
    locations.append({{'lat': round(lat, 6), 'lon': round(lon, 6)}})

df = pd.DataFrame({{
    'location_field': locations,  # Dict format ensures geo_point mapping
    ...
}})
```

CRITICAL - DATASET SIZES ({size_preference.upper()} preference):
***** STRICT TOTAL LIMIT: {ranges['total_max']:,} documents MAXIMUM across ALL datasets combined *****
- Each individual dataset: {ranges['per_dataset_typical']} rows (NEVER exceed {ranges['per_dataset_max']:,} per dataset)
- For demos with 5-6 datasets, aim for {ranges['per_dataset_max'] // 3:,}-{ranges['per_dataset_max'] // 2:,} rows each to stay under total
- Reference/lookup tables: {ranges['reference_typical']} rows (MAX {ranges['reference_max']:,})
- DO NOT generate thousands of records per dataset - keep datasets SMALL for demo purposes
- Example for {size_preference.upper()}: 6 datasets x 1000 rows = 6000 total (GOOD)
- WRONG for {size_preference.upper()}: 6 datasets x 6000 rows = 36000 total (EXCEEDS LIMIT!)

CRITICAL - STRING TEMPLATE FORMATTING:
When using string templates with .format(), ensure placeholder names EXACTLY match the keyword arguments:
- WRONG: template = "{{treatments}}" with .format(treatment="value")  ← Plural vs singular mismatch!
- CORRECT: template = "{{treatment}}" with .format(treatment="value")  ← Names match exactly
- WRONG: template = "{{user_name}}" with .format(username="value")  ← Underscore mismatch!
- CORRECT: template = "{{username}}" with .format(username="value")  ← Names match exactly
Check ALL template placeholders match their .format() keyword arguments EXACTLY (case and plurality matter!)

CRITICAL - AVOID EMPTY LIST ERRORS:
List comprehensions with filters can produce empty lists causing "'a' cannot be empty" errors in np.random.choice().
ALWAYS provide a fallback when filtering lists:
- WRONG: choice([s for s in systems if condition])  ← Can be empty!
- CORRECT: filtered = [s for s in systems if condition]; choice(filtered if filtered else systems)
- BETTER: choice(systems)  ← Avoid complex filtering when simple random choice works
When you MUST filter, check the result before passing to safe_choice() or np.random.choice()

CRITICAL - F-STRING ESCAPE RESTRICTIONS:
Python f-strings CANNOT contain backslash escapes inside the expression parts (the {{}} braces).
This will cause a SyntaxError: "f-string expression part cannot include a backslash"
- WRONG: f'{{random.choice(["item\'s", "another"])}}' ← Backslash escape inside {{}}!
- CORRECT: f'{{random.choice(["item" + chr(39) + "s", "another"])}}' ← Use chr(39) for apostrophe
- BETTER: f'{{random.choice(["items", "another"])}}' ← Avoid apostrophes in lists
- ALSO GOOD: random.choice(["item's", "another"]) ← No f-string at all
When building strings with apostrophes/quotes, use concatenation, chr(), or avoid f-strings entirely.

Template:
```python
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List

class {config["company_name"].replace(" ", "")}DataGenerator(DataGeneratorModule):
    \"\"\"Data generator for {config["company_name"]} - {config["department"]}\"\"\"

    @staticmethod
    def safe_choice(choices, size=None, weights=None, replace=True):
        \"\"\"Safer alternative to np.random.choice with automatic probability normalization.

        Automatically handles complex elements (lists, tuples, dicts) by falling back
        to Python's random.choices when numpy would fail with shape errors.
        \"\"\"
        # Check if choices contains complex elements that numpy can't handle
        # numpy requires 1D arrays of simple types (strings, numbers)
        use_python_random = False
        if len(choices) > 0:
            first_type = type(choices[0])
            # Any list, tuple, or dict elements require Python's random.choices
            if first_type in (list, tuple, dict):
                use_python_random = True

        # Use Python's random.choices for complex elements
        if use_python_random:
            if size is None:
                if weights is not None:
                    return random.choices(choices, weights=weights, k=1)[0]
                else:
                    return random.choice(choices)
            if weights is not None:
                return random.choices(choices, weights=weights, k=size)
            else:
                return random.choices(choices, k=size)

        # Use numpy for simple 1D arrays (faster)
        # When size is None: return a scalar (matches np.random.choice default behavior)
        # When size is given: return an array
        if weights is not None:
            weights = np.array(weights, dtype=float)

            # Handle weight count mismatch
            if len(weights) > len(choices):
                import logging
                logging.warning(f"Truncating {{len(weights) - len(choices)}} excess weights (had {{len(weights)}}, need {{len(choices)}})")
                weights = weights[:len(choices)]
            elif len(weights) < len(choices):
                raise ValueError(
                    f"Not enough weights for choices!\\n"
                    f"  Choices ({{len(choices)}}): {{choices}}\\n"
                    f"  Weights ({{len(weights)}}): {{weights.tolist()}}\\n"
                    f"  Missing {{len(choices) - len(weights)}} weight(s)"
                )

            probabilities = weights / weights.sum()
            if size is None:
                return np.random.choice(choices, p=probabilities, replace=replace)
            return np.random.choice(choices, size=size, p=probabilities, replace=replace)
        else:
            if size is None:
                return np.random.choice(choices)
            return np.random.choice(choices, size=size, replace=replace)

    @staticmethod
    def random_timedelta(start_date, end_date=None, days=None, hours=None, minutes=None, max_days=None):
        \"\"\"Generate random timedelta-adjusted datetime, handling numpy int64 conversion.

        Usage patterns:
            random_timedelta(start, end)  # random datetime between start and end
            random_timedelta(datetime.now(), max_days=120)  # random datetime within last 120 days
            random_timedelta(base, days=5, hours=3)  # base + 5 days + 3 hours
        \"\"\"
        if max_days is not None:
            random_seconds = int(np.random.random() * int(max_days) * 86400)
            return start_date - timedelta(seconds=random_seconds)

        if end_date is not None:
            delta = end_date - start_date
            random_seconds = int(np.random.random() * delta.total_seconds())
            return start_date + timedelta(seconds=random_seconds)

        delta_kwargs = {{}}
        if days is not None:
            delta_kwargs['days'] = int(days)
        if hours is not None:
            delta_kwargs['hours'] = int(hours)
        if minutes is not None:
            delta_kwargs['minutes'] = int(minutes)

        return start_date + timedelta(**delta_kwargs)

    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        \"\"\"Generate datasets with EXACT fields from requirements\"\"\"
        datasets = {{}}

        # Generate each dataset according to requirements
        # Use EXACT field names, types, and relationships specified above

        return datasets

    def get_relationships(self) -> List[tuple]:
        \"\"\"Define foreign key relationships from requirements\"\"\"
        return [
            # Format: (source_table, foreign_key_column, target_table)
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        \"\"\"Describe each dataset\"\"\"
        return {{}}

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        \"\"\"Return fields that should use semantic_text mapping\"\"\"
        return {{
            # From requirements above
        }}
```

**⚠️⚠️ CRITICAL: DataFrame Array Length Validation ⚠️⚠️**

**RULE**: ALL arrays in a pd.DataFrame() constructor MUST have EXACTLY the same length!

**❌ WRONG - Mismatched lengths (WILL CRASH):**
```python
# n = 1000, but some arrays are shorter
df = pd.DataFrame({{
    'id': [f'ID-{{i}}' for i in range(n)],           # 1000 elements ✓
    'name': [f'Name {{i}}' for i in range(n)],       # 1000 elements ✓
    'status': ['active', 'pending', 'failed'],       # 3 elements ❌ WRONG!
    'category': np.random.choice(categories, 100)    # 100 elements ❌ WRONG!
}})
# ERROR: All arrays must be of the same length
```

**✅ CORRECT - All arrays same length:**
```python
# ALL arrays must be length n
df = pd.DataFrame({{
    'id': [f'ID-{{i}}' for i in range(n)],                    # n elements ✓
    'name': [f'Name {{i}}' for i in range(n)],                # n elements ✓
    'status': np.random.choice(statuses, n),                  # n elements ✓
    'category': np.random.choice(categories, n),              # n elements ✓
    'amount': np.random.lognormal(5, 1, n),                   # n elements ✓
    'timestamp': pd.date_range(end=datetime.now(), periods=n) # n elements ✓
}})
```

**Common Mistakes to Avoid:**
1. ❌ Using static list without size parameter: `['a', 'b', 'c']` → Use `np.random.choice(['a', 'b', 'c'], n)`
2. ❌ Wrong size parameter: `np.random.choice(items, 100)` when n=1000
3. ❌ List comprehension with wrong range: `[x for x in range(100)]` when n=1000
4. ❌ Reusing array from different dataset: `df1['id']` when df1 has different length
5. ❌ **SLICING PRE-DEFINED REFERENCE POOLS** (MOST COMMON ERROR):
   ```python
   # WRONG: Define small pool, then slice more items than exist
   hss_nodes = ['hss-01', 'hss-02', 'hss-03']  # Only 3 items
   n_hss = 10
   df = pd.DataFrame({{'node_id': hss_nodes[:n_hss]}})  # ❌ CRASH! Slices only return 3, need 10

   # CORRECT Option 1: Generate exact count inline
   n_hss = 10
   df = pd.DataFrame({{'node_id': [f'hss-{{i:02d}}' for i in range(1, n_hss+1)]}})  # ✓ 10 items

   # CORRECT Option 2: Use np.random.choice with replacement to sample from pool
   hss_pool = ['hss-east-01', 'hss-east-02', 'hss-west-01']  # Pool of 3
   n_hss = 10
   df = pd.DataFrame({{'node_id': np.random.choice(hss_pool, n_hss)}})  # ✓ Samples 10 with replacement
   ```
   **NEVER slice a reference pool expecting more items than it contains!**

6. ❌ **CONCATENATED SUB-LIST POOL THAT DOESN'T SUM TO N** (SILENT TRUNCATION):
   ```python
   # WRONG: Build pool from sub-lists that sum to less than n, then slice [:n]
   n = 1000
   sequential_ids = [f'ID-{{i}}' for i in range(200)]   # 200 items
   prefixed_ids   = [f'PRE-{{i}}' for i in range(200)]  # 200 items
   uuid_ids       = [str(uuid.uuid4()) for _ in range(200)]  # 200 items
   all_ids = sequential_ids + prefixed_ids + uuid_ids    # 600 items total — NOT 1000!
   asset_ids = all_ids[:n]   # ❌ silently returns 600, no error here
   # ... other arrays all have 1000 items
   df = pd.DataFrame({{'id': asset_ids, 'val': np.random.choice([...], n)}})  # ❌ CRASH!

   # CORRECT: Generate UUIDs to pad the pool to exactly n
   n = 1000
   sequential_ids = [f'ID-{{i}}' for i in range(200)]
   prefixed_ids   = [f'PRE-{{i}}' for i in range(200)]
   uuid_ids       = [str(uuid.uuid4())[:12].upper() for _ in range(n - len(sequential_ids) - len(prefixed_ids))]
   all_ids = sequential_ids + prefixed_ids + uuid_ids  # exactly n items ✓
   np.random.shuffle(all_ids)
   asset_ids = all_ids  # no slice needed ✓
   ```
   **Always verify that concatenated sub-list pools sum to AT LEAST n before slicing!**

**Validation Pattern:**
```python
# Before creating DataFrame, ensure all arrays have same length
n = 5000  # Number of records

# Create all arrays with size n
ids = [f'ID-{{i:06d}}' for i in range(n)]        # n elements
names = [f'Name {{i}}' for i in range(n)]        # n elements
statuses = np.random.choice(['a', 'b'], n)       # n elements
amounts = np.random.lognormal(5, 1, n)           # n elements

# NOW safe to create DataFrame
df = pd.DataFrame({{'id': ids, 'name': names, 'status': statuses, 'amount': amounts}})
```

**NEVER VIOLATE THIS RULE - IT WILL CRASH THE ENTIRE DEMO GENERATION!**

**WEIGHT MANAGEMENT BEST PRACTICES:**

**RECOMMENDED: Use dictionaries to define weighted choices (prevents count mismatches):**
```python
# Define weights as dictionary - impossible to mismatch!
protocol_weights = {{
    'http': 15,
    'https': 40,
    'ssh': 8,
    'dns': 10
}}
protocols = list(protocol_weights.keys())
weights = list(protocol_weights.values())
df['protocol'] = safe_choice(protocols, size=n, weights=weights)
```

**Alternative: Parallel arrays (must count carefully):**
```python
# If using parallel arrays, ensure counts match EXACTLY!
protocols = ['http', 'https', 'ssh', 'dns']  # 4 items
weights = [15, 40, 8, 10]  # 4 weights - MUST MATCH!
df['protocol'] = safe_choice(protocols, size=n, weights=weights)
```

**Why dictionaries are better:**
- ✅ Impossible to mismatch counts (keys and values always paired)
- ✅ More readable and maintainable
- ✅ Self-documenting (can see weight for each choice)
- ✅ safe_choice will truncate excess weights or error on insufficient weights

**CODE EFFICIENCY GUIDELINES:**
- Keep inline lists SHORT (max 10-15 items), use variables for long lists
- Minimize comments - let code be self-documenting
- Use loops and list comprehensions instead of repetitive code
- Avoid overly verbose variable names
- Focus on correctness and brevity
"""

            # Add enhanced data generation guidance if enabled
            if use_enhanced:
                prompt += """
🔥 ENHANCED DATA GENERATION MODE ENABLED 🔥

CRITICAL: Generate data with REALISTIC CLUSTERING for meaningful analytics queries!

1. **NUMERIC FIELDS** - Use SKEWED distributions (NOT uniform random):
   ```python
   # Risk scores (0-1): concentrate low, few high
   risk_score = np.random.beta(2, 5, size=n)  # p90 ≈ 0.82, p95 ≈ 0.90

   # Amounts: realistic right-skew
   amount = np.random.lognormal(mean=4, sigma=1, size=n)

   # Counts: realistic clustering
   count = np.random.poisson(lam=3, size=n)
   ```

2. **CATEGORICAL FIELDS** - CONCENTRATE values (NOT equal distribution):

   **RECOMMENDED: Use dictionaries for weights (prevents count mismatches):**
   ```python
   # Dictionary approach - impossible to mismatch counts!
   status_weights = {{
       'active': 80,
       'pending': 15,
       'failed': 5
   }}
   statuses = list(status_weights.keys())
   weights = list(status_weights.values())
   status = safe_choice(statuses, size=n, weights=weights)
   ```

   **Alternative (parallel arrays - must count carefully):**
   ```python
   # 80% active, 15% pending, 5% failed
   # WARNING: Ensure weights list has SAME length as choices!
   status = safe_choice(['active', 'pending', 'failed'], size=n, weights=[80, 15, 5])
   ```

3. **TIME-SERIES CLUSTERING** - Create incident periods:
   ```python
   # 30% baseline (random), 70% clustered in incidents
   baseline_count = int(total_failures * 0.3)
   incident_count = total_failures - baseline_count

   # Create 10-15 incident periods
   for incident in range(10):
       incident_start = random_timedelta(start_time, end_time)
       affected_resources = random.sample(all_resources, k=15)  # SAME resources
       for _ in range(incident_count // 10):
           timestamp = random_timedelta(incident_start, incident_start + timedelta(hours=2))
           resource = random.choice(affected_resources)  # Cluster by resource
           # Add failure event...
   ```

4. **MULTI-DIMENSIONAL CLUSTERING** - For COUNT_DISTINCT aggregations:

   When queries use COUNT_DISTINCT(field) with GROUP BY multiple dimensions, ensure variety WITHIN group boundaries!

   **CRITICAL Anti-Pattern (WILL FAIL):**
   ```python
   # 1:1 mapping - each host in unique datacenter
   mme_hosts = [
       ('mme-01', 'cluster-1', 'DC-Seattle'),   # unique combination
       ('mme-02', 'cluster-2', 'DC-Dallas'),    # unique combination
       ('mme-03', 'cluster-1', 'DC-Atlanta'),   # unique combination
   ]
   # Query: GROUP BY cluster_id, datacenter → Each group has max 1 host!
   # Query: WHERE unique_hosts >= 2 → RETURNS 0 RESULTS ❌
   ```

   **CORRECT Pattern (MANY:1 relationships):**
   ```python
   # Multiple hosts share the same (cluster, datacenter) combination
   mme_hosts = [
       ('mme-01', 'cluster-1', 'DC-Seattle'),
       ('mme-02', 'cluster-1', 'DC-Seattle'),   # SAME cluster AND datacenter
       ('mme-03', 'cluster-1', 'DC-Seattle'),   # SAME cluster AND datacenter
       ('mme-04', 'cluster-2', 'DC-Dallas'),
       ('mme-05', 'cluster-2', 'DC-Dallas'),    # SAME cluster AND datacenter
   ]
   # Query: GROUP BY cluster_id, datacenter → Each group has multiple hosts ✅
   # Query: WHERE unique_hosts >= 2 → RETURNS RESULTS ✅
   ```

   **Implementation Strategy:**
   ```python
   # Step 1: Define dimension hierarchies
   datacenters = ['DC-Seattle', 'DC-Dallas', 'DC-Atlanta']
   clusters = ['cluster-1', 'cluster-2']

   # Step 2: Create combinations (NOT 1:1, use repetition for MANY:1)
   cluster_dc_combos = [
       ('cluster-1', 'DC-Seattle'),   # Will have multiple hosts
       ('cluster-1', 'DC-Dallas'),    # Will have multiple hosts
       ('cluster-2', 'DC-Dallas'),    # Will have multiple hosts
       ('cluster-2', 'DC-Atlanta'),   # Will have multiple hosts
   ]

   # Step 3: Assign multiple resources per combination
   for i, (cluster, dc) in enumerate(cluster_dc_combos):
       # Create 2-4 hosts per (cluster, datacenter) combination
       num_hosts = random.randint(2, 4)
       for j in range(num_hosts):
           mme_hosts.append({{
               'mme_host': f'mme-{{cluster[-1]}}{{dc[-7:]}}-{{j:02d}}',
               'cluster_id': cluster,
               'datacenter': dc,
               'region': get_region_for_dc(dc)
           }})

   # Step 4: During incidents, assign failures to SAME (cluster, datacenter)
   for incident in incidents:
       # Pick a specific (cluster, datacenter) combination
       target_cluster, target_dc = random.choice(cluster_dc_combos)

       # Get ALL hosts in that combination
       affected_hosts = [
           h for h in mme_hosts
           if h['cluster_id'] == target_cluster and h['datacenter'] == target_dc
       ]

       # Assign failures across these hosts during incident
       for _ in range(failures_per_incident):
           host = random.choice(affected_hosts)
           # This ensures COUNT_DISTINCT(mme_host) BY cluster_id, datacenter >= 2
   ```

Goal: Percentile-based thresholds (p75, p90, p95) return meaningful result counts (not 0, not all).
"""

            prompt += """
Generate the complete implementation with ALL required fields:"""

            if self.llm_client:
                code = self._call_llm(prompt, max_tokens=16000)
            else:
                code = self._generate_mock_data_module(config)

        # Validate syntax before saving (with auto-fix on failure)
        code = self._validate_python_syntax(code, 'data_generator.py')

        # Save the module
        module_file = module_path / 'data_generator.py'
        module_file.write_text(code)
        logger.info("Generated data_generator.py with strategy requirements")

        # Runtime validation: test-execute generate_datasets() to catch runtime errors
        # (e.g. "All arrays must be of the same length") before they surface during demo run
        if self.llm_client:
            exec_error = self._test_execute_data_generator(module_path, config)
            if exec_error:
                logger.warning(f"Data generator execution failed, retrying with error context:\n{exec_error[:400]}")
                retry_prompt = prompt + f"""

**⚠️ EXECUTION ERROR — YOUR PREVIOUS CODE CRASHED. FIX IT AND REGENERATE.**

The code you generated raised an exception when executed:
```
{exec_error}
```

Common causes of this error:
- Arrays passed to pd.DataFrame() have different lengths — ALL must be exactly `n`
- Building an ID/value pool by concatenating sub-lists whose TOTAL is less than `n`, then slicing `pool[:n]` — this silently returns fewer items than `n` with no error at the slice
- Weights list length doesn't match choices list length

Fix the error and regenerate the COMPLETE data_generator.py from scratch:"""
                retry_code = self._call_llm(retry_prompt, max_tokens=16000)
                retry_code = self._validate_python_syntax(retry_code, 'data_generator.py')
                module_file.write_text(retry_code)
                logger.info("Saved retried data_generator.py")

                exec_error2 = self._test_execute_data_generator(module_path, config)
                if exec_error2:
                    raise RuntimeError(
                        f"Data generator failed after one retry.\nError:\n{exec_error2}"
                    )
                logger.info("Retried data_generator.py executed successfully")

    def _test_execute_data_generator(self, module_path: Path, config: Dict[str, Any]) -> Optional[str]:
        """Test-execute generate_datasets() on a freshly generated data_generator.py.

        Returns None on success, or a traceback string on failure.
        Used to catch runtime errors (e.g. mismatched array lengths) before they
        surface during the actual demo run.
        """
        import importlib.util
        import traceback as tb

        module_file = module_path / 'data_generator.py'
        try:
            # Unique spec name avoids import cache collisions between retries
            spec_name = f"_validation_{module_path.name}_{id(module_file)}"
            spec = importlib.util.spec_from_file_location(spec_name, module_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the DataGeneratorModule subclass
            from src.framework.base import DataGeneratorModule, DemoConfig
            generator_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type) and obj is not DataGeneratorModule
                        and issubclass(obj, DataGeneratorModule)):
                    generator_class = obj
                    break

            if generator_class is None:
                return "No DataGeneratorModule subclass found in generated code."

            demo_config = DemoConfig(
                company_name=config.get('company_name', 'Test'),
                department=config.get('department', 'General'),
                industry=config.get('industry', 'Technology'),
                pain_points=config.get('pain_points', []),
                use_cases=config.get('use_cases', []),
                scale=config.get('scale', '1000'),
                metrics=config.get('metrics', []),
            )

            generator = generator_class(demo_config)
            datasets = generator.generate_datasets()
            logger.info(f"Validation: generate_datasets() succeeded — {len(datasets)} datasets")
            return None  # Success

        except Exception:
            return tb.format_exc()

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

        # Categorize by query_type OR search_type (handle both naming conventions)
        def get_type(q):
            """Get query type - handles both query_type and search_type fields"""
            return q.get('query_type') or q.get('search_type', '')

        # Parameterized: explicitly marked as parameterized
        parameterized_queries = [q for q in all_queries if get_type(q) == 'parameterized']

        # RAG: marked as 'rag' or search_type contains 'rag' or 'completion'
        rag_queries = [q for q in all_queries if get_type(q) in ['rag', 'rag_completion', 'rag_rerank']]

        # Scripted: everything else (bm25, semantic, hybrid, fuzzy, rerank, etc.)
        scripted_queries = [q for q in all_queries if q not in parameterized_queries and q not in rag_queries]

        logger.info(f"  Categorized: {len(scripted_queries)} scripted, "
                   f"{len(parameterized_queries)} parameterized, {len(rag_queries)} rag")

        # Save all queries to all_queries.json (reference copy before LLM enhancement)
        all_queries_data = {
            'scripted': scripted_queries,
            'parameterized': parameterized_queries,
            'rag': rag_queries,
            'all': all_queries
        }

        all_queries_file = module_path / 'all_queries.json'
        all_queries_file.write_text(json.dumps(all_queries_data, indent=2))
        logger.info(f"  Saved all_queries.json")

        # Generate JSON loader as fallback (will be overwritten by LLM-generated module on success)
        self._generate_json_loader_query_module(config, module_path)

        # Format data profile for prompt if available
        data_profile_section = ""
        join_guidance = ""

        if data_profile and 'datasets' in data_profile:
            from src.services.data_profiler import DataProfiler
            data_profile_section = f"""

**ACTUAL INDEXED DATA PROFILE:**
The following data has been generated, indexed in Elasticsearch, and profiled.
USE THESE EXACT FIELD NAMES AND VALUE EXAMPLES IN YOUR QUERIES.

{DataProfiler.format_profile_for_llm(data_profile, compact=True)}

CRITICAL - FILTER VALUE REQUIREMENTS:
1. ⚡ **USE SUGGESTED FILTERS FIRST**: The data profile shows "Suggested Filters (Guaranteed Results)" for each dataset
   - These filters are pre-validated and guaranteed to return results
   - Copy filter clauses EXACTLY as shown (e.g., `WHERE status == 'active'`)
   - You can combine suggested filters with AND/OR operators

2. ❌ **DO NOT INVENT filter values** - use ONLY values shown in data profile
   - ✅ GOOD: `WHERE status == 'active'` (value from profile)
   - ❌ BAD: `WHERE status == 'pending'` (invented value not in profile)

3. **Field name accuracy**:
   - Use ONLY field names that appear in the data profile above
   - Check spelling carefully (common errors: timestamp vs @timestamp, userId vs user_id)
   - Verify field types match operations (text for MATCH, numeric for math)

⚠️  WARNING: Queries with invented filter values will return 0 results and fail testing!
"""

            # Add enhanced mode numeric threshold guidance
            if config.get('use_enhanced_generation', False):
                data_profile_section += """
**🔥 ENHANCED MODE - NUMERIC THRESHOLD REQUIREMENTS:**

The data has been generated with realistic clustering. Use percentile-based thresholds from profile above.

CRITICAL - FOR WHERE CLAUSES WITH NUMERIC COMPARISONS (>, <, >=, <=):
1. ⚡ **USE THRESHOLD SUGGESTIONS**: The profile shows "NUMERIC THRESHOLD SUGGESTIONS" for each numeric field
   - These are percentile-based thresholds (p75, p90, p95, p99)
   - Each suggestion shows expected result count
   - Example: `WHERE risk_score > 0.82` → 1000 results (Top 10%)

2. **DO NOT use arbitrary thresholds** - They will likely return 0 results!
   - ❌ BAD: `WHERE failure_count >= 200` (arbitrary number)
   - ✅ GOOD: `WHERE failure_count >= {p90_value}` (from threshold suggestions)

3. **For aggregations with WHERE filters**:
   - Check data profile for actual value distributions
   - Use threshold suggestions for meaningful result counts
   - Aim for 5-25% of data (not 0%, not 100%)

4. **Example using profile data**:
   ```
   If profile shows:
   - risk_score: p90 = 0.82 (returns ~1000 results)
   - risk_score: p95 = 0.90 (returns ~500 results)

   Then use:
   WHERE risk_score > 0.82  # High risk (top 10%)
   WHERE risk_score > 0.90  # Critical risk (top 5%)
   ```

REMEMBER: Enhanced mode data has clustering - percentile thresholds are your friend!

**🔥 ENHANCED MODE - ADAPTIVE TIME BUCKETING AND THRESHOLDS:**

When using DATE_TRUNC with GROUP BY and WHERE clause thresholds, you MUST ensure alignment:

CRITICAL - TIME BUCKETING LOGIC:
1. **Check data volume and time range** from the data profile:
   - Total records in dataset
   - Time range (earliest to latest @timestamp)

2. **Calculate expected events per bucket**:
   - Formula: expected_per_bucket = total_records / (num_days × intervals_per_day)
   - Example: 10,000 records / (90 days × 288 five-minute intervals) = 0.38 events/bucket

3. **Choose appropriate bucket size** based on expected density:
   - **5-minute buckets**: Only for LARGE datasets (>100K records) with high-frequency events
   - **15-minute buckets**: Medium datasets (10K-100K records)
   - **30-minute buckets**: Small-medium datasets (5K-50K records)
   - **1-hour buckets**: Small datasets (<10K records)
   - **Daily/weekly buckets**: For long-term trend analysis or very sparse data

4. **Align thresholds with bucket size**:

   ❌ **ANTI-PATTERN (WILL FAIL)**:
   ```esql
   | EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
   | STATS failure_count = COUNT(*) BY time_bucket, cluster_id, datacenter
   | WHERE failure_count > 50  ← IMPOSSIBLE! Max 2-3 per 5-min bucket
   ```

   ✅ **CORRECT - Wider buckets OR lower thresholds**:
   ```esql
   Option A: Wider time buckets
   | EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
   | STATS failure_count = COUNT(*) BY time_bucket, cluster_id, datacenter
   | WHERE failure_count > 50  ← Now achievable with hourly aggregation

   Option B: Percentile-based thresholds
   | EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
   | STATS failure_count = COUNT(*) BY time_bucket, cluster_id, datacenter
   | WHERE failure_count > {p90_value}  ← Use actual p90 from profile (e.g., 3)
   ```

5. **Multi-dimensional aggregations reduce density further**:
   - GROUP BY (time_bucket, dim1, dim2, dim3) splits data N ways
   - Each additional dimension divides expected_per_bucket by cardinality
   - Example: GROUP BY (time_bucket, 100 cells, 3 datacenters) = 300 groups per time bucket
   - If you have 1000 events/hour → only 3.3 events per (time_bucket, cell, datacenter) group

6. **Use data profile to inform decisions**:
   - Check "Total Records" in dataset profile
   - Check numeric field percentiles (p50, p75, p90, p95, p99)
   - Use threshold suggestions that show expected result counts
   - Don't guess thresholds - use profile data!

REMEMBER: More dimensions in GROUP BY = fewer events per group = need wider time buckets OR lower thresholds!
"""

            # Add JOIN-specific guidance if relationships detected
            if data_profile.get('relationships'):
                relationships = data_profile['relationships']
                join_guidance = f"""

**CRITICAL - LOOKUP JOIN GUIDANCE:**
The data profiler detected {len(relationships)} relationship(s) between datasets. These are pre-validated
and ready for use in LOOKUP JOIN queries.

**How to use detected relationships:**
1. The data profile above shows exact JOIN syntax for each relationship
2. Use the provided syntax examples - they use correct field names and operators
3. For array fields (comma-separated values), use MV_EXPAND before JOIN
4. Both indices must be indexed in 'lookup' mode (already configured)

**LOOKUP JOIN Syntax Rules:**
✅ CORRECT: `FROM source | LOOKUP JOIN lookup_table ON field`
✅ CORRECT: `FROM source | LOOKUP JOIN lookup_table ON source_field == lookup_field`
✅ CORRECT (array): `FROM source | MV_EXPAND array_field | LOOKUP JOIN lookup ON array_field == lookup_field`

❌ WRONG: `FROM source | LOOKUP JOIN lookup_table ON field = field` (use == not =)
❌ WRONG: `FROM source | LOOKUP JOIN lookup_table_lookup ON field` (no _lookup suffix)
❌ WRONG: `FROM source | LOOKUP lookup_table ON field` (missing JOIN keyword)

**When to use LOOKUP JOIN:**
- Use DETECTED relationships from data profile (they have matching values)
- JOIN adds enrichment fields from lookup table to results
- Good for demos: shows advanced ES|QL capabilities
- Don't overuse: not every query needs a JOIN

**Validation:**
- All detected relationships have been validated for:
  * Field name matching (ID fields vs reference fields)
  * Value overlap (≥10% of values match between datasets)
  * Correct cardinality (1:1, 1:many, or many:1)
"""
        else:
            data_profile_section = """

**WARNING - NO DATA PROFILE AVAILABLE:**
Data profile was not available during query generation. Field names must be inferred from strategy.
This may result in field name mismatches or typos. Use extreme care with field naming.
"""
            join_guidance = ""

        # Build search field mapping guidance (search demos only)
        search_field_guidance = ""
        demo_type = config.get('demo_type', 'analytics')
        if demo_type == 'search':
            search_field_guidance = self._build_search_field_guidance(
                query_strategy, data_profile
            )

        # Build prompt using string concatenation to avoid f-string issues with curly braces
        # in data_profile_section and join_guidance (which contain ES|QL/JSON syntax)

        # Get ES|QL rules (might also contain curly braces)
        esql_rules = self._get_esql_strict_rules()

        # Get tool metadata instructions
        tool_metadata_prompt = self._get_tool_metadata_instructions(config)

        # Get endpoint IDs for substitution in prompts
        rerank_endpoint = self.inference_endpoints['rerank']
        completion_endpoint = self.inference_endpoints['completion']

        # Build template with company name
        company_class_name = config['company_name'].replace(" ", "")

        prompt_parts = [
            "Generate a Python module that implements QueryGeneratorModule for this customer:",
            "",
            f"Company: {config['company_name']}",
            f"Department: {config['department']}",
            f"Pain Points: {', '.join(config['pain_points'])}",
            f"Use Cases: {', '.join(config['use_cases'])}",
            "",
            "**Pre-Planned Query Strategy:**",
            json.dumps(query_strategy, indent=2),
            data_profile_section,  # Contains ES|QL/JSON with curly braces
            join_guidance,         # Contains ES|QL/JSON with curly braces
            search_field_guidance, # Search field mapping (empty for analytics)
            "",
            "CRITICAL - IMPLEMENT THE QUERIES FROM THE STRATEGY ABOVE.",
            "",
            tool_metadata_prompt,  # Tool metadata instructions for Agent Builder
            "",
            "The module should:",
            "1. Implement QueryGeneratorModule base class",
            "2. Generate the EXACT queries from the strategy with proper ES|QL syntax",
            "3. Use field names that MATCH the generated data",
            "4. Include query descriptions that explain the business value",
            "5. Include tool_metadata for each query for Agent Builder deployment",
            "6. Return queries in the order that builds a compelling narrative",
            "",
            "**ES|QL STRICT SYNTAX RULES - MUST FOLLOW:**",
            esql_rules,  # Might contain curly braces too
            "",
            "CRITICAL - ESCAPING ES|QL QUERIES IN PYTHON:",
            "- ALWAYS use SINGLE-QUOTE triple strings (''') for query values, NEVER double-quote triple strings (\"\"\")",
            "  ✅ CORRECT: 'query': '''FROM index | WHERE MATCH(field, \"term\")'''",
            "  ❌ WRONG:  'query': \"\"\"FROM index | WHERE MATCH(field, \"term\")\"\"\"  ← breaks on inner quotes!",
            "- ES|QL queries with JSON parameters use SINGLE curly braces: MATCH(field, \"term\", {\"boost\": 0.75})",
            "- Inside ''' strings, use double quotes freely: {\"inference_id\": \"completion-vulcan\"}",
            "- Do NOT use f-strings for queries — no variable interpolation needed",
            "- IMPORTANT: The final ES|QL syntax must always have SINGLE braces {} in the query string",
            "",
            "CRITICAL - METHOD SEPARATION RULES:",
            "1. generate_queries() → ONLY scripted queries with HARDCODED values (no ?parameters)",
            "2. generate_parameterized_queries() → ONLY queries with ?parameter syntax",
            "3. generate_rag_queries() → ONLY RAG queries with MATCH/RERANK/COMPLETION",
            "4. DO NOT mix these - each query goes in EXACTLY ONE method based on its type",
            "",
            "Template - MUST IMPLEMENT ALL THREE METHODS:",
            "```python",
            "from src.framework.base import QueryGeneratorModule, DemoConfig",
            "from typing import Dict, List, Any",
            "import pandas as pd",
            "",
            f"class {company_class_name}QueryGenerator(QueryGeneratorModule):",
            f"    \"\"\"Query generator for {config['company_name']} - {config['department']}\"\"\"",
            "",
            "    # DO NOT define __init__ - inherited from base class provides:",
            "    # self.config, self.datasets",
            "",
            "    def generate_queries(self) -> List[Dict[str, Any]]:",
            "        \"\"\"Generate SCRIPTED ES|QL queries with hardcoded values (no user parameters)",
            "",
            "        CRITICAL RULES FOR THIS METHOD:",
            "        - ONLY include queries with HARDCODED values (e.g., WHERE status == \"active\")",
            "        - DO NOT include queries with ?parameter syntax - those go in generate_parameterized_queries()",
            "        - DO NOT include RAG/COMPLETION queries - those go in generate_rag_queries()",
            "        - Each query MUST have query_type=\"scripted\"",
            "        - These queries can be run immediately without user input",
            "        \"\"\"",
            "        queries = []",
            "",
            "        # SCRIPTED QUERIES - Ready to run with hardcoded filter values",
            "        # Example: WHERE campaign_theme == \"summer_promotion\" (NOT ?campaign_theme)",
            "        # Each query: name, description, tool_metadata, query, query_type=\"scripted\"",
            "",
            "        return queries",
            "",
            "    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:",
            "        \"\"\"Generate parameterized queries with ?parameter syntax for user customization",
            "",
            "        CRITICAL RULES FOR THIS METHOD:",
            "        - MUST use ?parameter syntax in ES|QL queries (e.g., WHERE brand == ?brand_name)",
            "        - Each query MUST have query_type=\"parameterized\"",
            "        - Each query MUST have 'parameters' list defining each ?parameter",
            "        - Parameters define: name, type (string/long/double/boolean), description, required",
            "        - These become Agent Builder tools that accept user input",
            "",
            "        Example:",
            "        {",
            "            'name': 'search_by_brand',",
            "            'query_type': 'parameterized',",
            "            'parameters': [{'name': 'brand_name', 'type': 'string', 'required': True}],",
            "            'query': \"FROM assets | WHERE brand == ?brand_name | LIMIT 10\"",
            "        }",
            "        \"\"\"",
            "        queries = []",
            "",
            "        # PARAMETERIZED QUERIES - Use ?parameter syntax, define parameters list",
            "        # Each query: name, description, tool_metadata, query_type=\"parameterized\", parameters, query with ?params",
            "",
            "        return queries",
            "",
            "    def generate_rag_queries(self) -> List[Dict[str, Any]]:",
            "        \"\"\"Generate RAG queries using COMPLETION command",
            "",
            "        CRITICAL - RAG Pipeline Requirements:",
            "        1. MUST use MATCH to find semantically similar documents",
            "        2. OPTIONALLY use RERANK to improve relevance",
            "        3. MUST use COMPLETION to generate LLM-powered answers",
            "        4. Target semantic_text fields from the strategy",
            "",
            "        Example RAG query structure:",
            "        FROM index METADATA _id",
            "        | WHERE MATCH(semantic_field, ?user_question)",
            "        | RERANK ?user_question ON semantic_field",
            "        | LIMIT 5",
            "        | EVAL prompt = CONCAT(\"Answer this question: \", ?user_question)",
            '        | COMPLETION answer = prompt WITH {{"inference_id": "' + completion_endpoint + '"}}',
            "        \"\"\"",
            "        queries = []",
            "",
            "        # Extract semantic_text fields from strategy datasets",
            "        # For each semantic_text field, generate a RAG query",
            "",
            "        return queries",
            "",
            "    def get_query_progression(self) -> List[str]:",
            "        \"\"\"Define the order to present queries for maximum impact\"\"\"",
            "        return [",
            "            # Query names in presentation order from strategy",
            "        ]",
            "```",
            "",
            "CRITICAL REQUIREMENTS:",
            "1. ALL THREE methods must be implemented (generate_queries, generate_parameterized_queries, generate_rag_queries)",
            "2. RAG queries MUST use the COMPLETION command with semantic_text fields from the strategy",
            "3. Each query must have proper query_type metadata (\"scripted\", \"parameterized\", or \"rag\")",
            "4. Each query MUST include tool_metadata with tool_id, description, and tags for Agent Builder",
            "5. Extract semantic_text fields from the strategy datasets to guide RAG generation",
            "",
            "Generate the complete implementation with ALL queries from the strategy:"
        ]

        prompt = "\n".join(prompt_parts)
        logger.info("→ Calling LLM to generate query code...")
        logger.info(f"  Prompt length: {len(prompt)} characters")

        try:
            if self.llm_client:
                code = self._call_llm(prompt, max_tokens=32000)
                logger.info(f"✓ LLM returned {len(code)} characters of code")
            else:
                logger.warning("No LLM client, using mock generator")
                code = self._generate_mock_query_module(config)
        except Exception as e:
            logger.error(f"✗ LLM call failed: {e}", exc_info=True)
            raise

        # Validate syntax before saving (with auto-fix on failure)
        logger.info("→ Validating Python syntax...")
        try:
            code = self._validate_python_syntax(code, 'query_generator.py')
            logger.info("✓ Syntax validation passed")
        except Exception as e:
            logger.error(f"✗ Syntax validation failed: {e}", exc_info=True)
            raise

        # Save the module
        logger.info(f"→ Writing query_generator.py to {module_path}")
        try:
            module_file = module_path / 'query_generator.py'
            module_file.write_text(code)
            logger.info(f"✓ Successfully wrote query_generator.py ({len(code)} bytes)")
        except Exception as e:
            logger.error(f"✗ Failed to write file: {e}", exc_info=True)
            raise

        logger.info("Generated query_generator.py with strategy")

    def _generate_json_loader_query_module(self, config: Dict[str, Any], module_path: Path):
        """Generate simple query_generator.py that loads from all_queries.json

        This replaces the complex LLM-generated code with a simple loader template.
        The queries are already in all_queries.json, so we just need methods to read them.
        """
        logger.info("Generating JSON loader query module...")

        company_class_name = config['company_name'].replace(" ", "").replace("-", "")
        company_name = config['company_name']
        department = config['department']

        code = f'''
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import json
from pathlib import Path

class {company_class_name}QueryGenerator(QueryGeneratorModule):
    """Query generator for {company_name} - {department}

    Loads queries from all_queries.json instead of hardcoding them.
    This makes queries easier to edit and maintain.
    """

    def __init__(self, config: DemoConfig, datasets: Dict[str, Any]):
        super().__init__(config, datasets)
        self._queries_cache = None

    def _load_queries(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load all queries from all_queries.json (cached)"""
        if self._queries_cache is None:
            queries_file = Path(__file__).parent / 'all_queries.json'
            with open(queries_file, 'r') as f:
                self._queries_cache = json.load(f)
        return self._queries_cache

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate scripted queries (no user parameters)

        Returns queries that can be run immediately without customization.
        """
        return self._load_queries().get('scripted', [])

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries that accept user input

        Returns queries with parameters that users can customize.
        These become Agent Builder tools that accept input.
        """
        return self._load_queries().get('parameterized', [])

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using COMPLETION command

        Returns queries that use the MATCH -> RERANK -> COMPLETION pipeline
        for semantic search and generative AI responses.
        """
        return self._load_queries().get('rag', [])
'''

        # Write the generated code
        module_file = module_path / 'query_generator.py'
        module_file.write_text(code)
        logger.info(f"  Generated query_generator.py ({len(code)} bytes) - JSON loader approach")

    def _generate_config_file(self, config: Dict[str, Any], module_path: Path):
        """Generate module configuration file"""
        # Extract demo_type to top level for visibility
        demo_type = config.get('demo_type', 'analytics')

        config_data = {
            "_comment": "demo_type: 'search' (document retrieval/RAG) or 'analytics' (metrics/trends)",
            "demo_type": demo_type,
            "module_version": "1.0.0",
            "generated_at": datetime.now().isoformat(),
            "customer_context": config,
            "module_components": {
                "data_generator": "data_generator.py",
                "query_generator": "query_generator.py",
                "demo_guide": "demo_guide.py"
            },
            "inference_endpoints": {
                "embedding_type": self._resolve_vector_type(),
                "embedding_endpoint": self._resolve_embedding_endpoint(),
                "rerank": self.inference_endpoints.get("rerank", ".rerank-v1-elasticsearch"),
                "completion": self.inference_endpoints.get("completion", "completion-vulcan"),
            }
        }

        config_file = module_path / 'config.json'
        config_file.write_text(json.dumps(config_data, indent=2))

    def _generate_agent_metadata(self, config: Dict[str, Any], module_path: Path):
        """Generate agent metadata for Elastic Agent Builder deployment

        Creates agent_metadata.json with all required fields for the Kibana API.
        """
        logger.info("=" * 60)
        logger.info("AGENT METADATA GENERATION START")
        logger.info(f"Module path: {module_path}")
        logger.info(f"Module path exists: {module_path.exists()}")
        logger.info(f"Config: company_name={config.get('company_name')}, department={config.get('department')}")
        logger.info("=" * 60)

        # Generate agent ID and basic info
        company_slug = config['company_name'].lower().replace(' ', '_')[:20]
        dept_slug = config.get('department', 'general').lower().replace(' ', '_')[:15]
        agent_id = f"{company_slug}_{dept_slug}_agent"
        logger.info(f"Generated agent_id: {agent_id}")

        # Generate avatar symbol from company initials
        company_words = config['company_name'].split()
        if len(company_words) >= 2:
            avatar_symbol = (company_words[0][0] + company_words[1][0]).upper()[:2]
        else:
            avatar_symbol = config['company_name'][:2].upper()
        logger.info(f"Generated avatar_symbol: {avatar_symbol}")

        # Select color based on demo type
        demo_type = config.get('demo_type', 'analytics')
        avatar_color = "#3B82F6" if demo_type == 'analytics' else "#10B981"  # Blue for analytics, green for search
        logger.info(f"Demo type: {demo_type}, Avatar color: {avatar_color}")

        # Prepare context for LLM to generate instructions
        try:
            # Load ALL queries to understand what the agent can do
            all_queries_file = module_path / 'all_queries.json'
            logger.info(f"Looking for queries at: {all_queries_file}")
            logger.info(f"all_queries.json exists: {all_queries_file.exists()}")

            if all_queries_file.exists():
                logger.info("Loading all_queries.json...")
                with open(all_queries_file, 'r') as f:
                    all_queries_data = json.load(f)
                # Get all queries (scripted + parameterized + rag)
                all_queries = all_queries_data.get('all', [])
                query_descriptions = [q.get('description', q.get('name', '')) for q in all_queries[:10]]  # First 10 queries
                logger.info(f"Successfully loaded {len(all_queries)} queries, extracted {len(query_descriptions)} descriptions")
            else:
                logger.warning("all_queries.json NOT FOUND - using empty query descriptions")
                query_descriptions = []

            # Load datasets to understand what data is available
            datasets_info = []
            data_dir = module_path / 'data'
            logger.info(f"Looking for data directory at: {data_dir}")
            logger.info(f"Data directory exists: {data_dir.exists()}")

            if data_dir.exists():
                csv_files = list(data_dir.glob('*.csv'))
                logger.info(f"Found {len(csv_files)} CSV files in data directory")
                for csv_file in csv_files:
                    dataset_name = csv_file.stem
                    datasets_info.append(dataset_name)
                    logger.info(f"  - Dataset: {dataset_name}")
            else:
                logger.warning("Data directory NOT FOUND - using empty dataset info")

        except Exception as e:
            logger.error(f"ERROR loading context for agent instructions: {e}", exc_info=True)
            query_descriptions = []
            datasets_info = []

        # Generate agent instructions using LLM
        logger.info("Calling _generate_agent_instructions()...")
        logger.info(f"  - {len(query_descriptions)} query descriptions")
        logger.info(f"  - {len(datasets_info)} datasets")
        instructions = self._generate_agent_instructions(config, query_descriptions, datasets_info)
        logger.info(f"Generated instructions ({len(instructions)} chars)")

        # Create agent metadata structure
        logger.info("Building agent metadata structure...")
        agent_metadata = {
            "id": agent_id,
            "name": f"{config['company_name']} {config.get('department', 'Analytics')} Assistant",
            "description": f"AI assistant specialized in {config.get('department', 'data analysis')} for {config['company_name']}. I can help analyze your data, answer questions, and provide insights based on your specific use cases.",
            "labels": [
                company_slug,
                dept_slug,
                demo_type,
                "demo-builder",
                config.get('industry', 'general').lower()
            ],
            "avatar_color": avatar_color,
            "avatar_symbol": avatar_symbol,
            "configuration": {
                "instructions": instructions,
                "tools": []  # Initially empty, tools will be added separately
            }
        }
        logger.info("Agent metadata structure created successfully")

        # Save agent metadata
        agent_file = module_path / 'agent_metadata.json'
        logger.info(f"Writing agent metadata to: {agent_file}")
        try:
            agent_file.write_text(json.dumps(agent_metadata, indent=2))
            logger.info(f"✓ Successfully wrote agent_metadata.json")
            logger.info(f"✓ File size: {agent_file.stat().st_size} bytes")
        except Exception as e:
            logger.error(f"✗ FAILED to write agent_metadata.json: {e}", exc_info=True)
            raise

        logger.info("=" * 60)
        logger.info(f"AGENT METADATA GENERATION COMPLETE - ID: {agent_id}")
        logger.info("=" * 60)

    def _generate_demo_guide_content(self, config: Dict[str, Any], module_path: Path) -> str:
        """Generate comprehensive demo guide content using LLM

        Args:
            config: Demo configuration
            module_path: Path to module directory

        Returns:
            Formatted markdown demo guide content
        """
        # Load query strategy, data profile, and tested queries for context
        try:
            import json
            query_strategy_file = module_path / 'query_strategy.json'
            data_profile_file = module_path / 'data_profile.json'
            all_queries_file = module_path / 'all_queries.json'

            query_strategy = {}
            data_profile = {}
            all_queries = {}

            if query_strategy_file.exists():
                with open(query_strategy_file, 'r') as f:
                    query_strategy = json.load(f)

            if data_profile_file.exists():
                with open(data_profile_file, 'r') as f:
                    data_profile = json.load(f)

            if all_queries_file.exists():
                with open(all_queries_file, 'r') as f:
                    all_queries = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load strategy/profile/queries for guide generation: {e}")
            query_strategy = {}
            data_profile = {}
            all_queries = {}

        # Fallback if no LLM available
        if not self.llm_client:
            return self._generate_fallback_demo_guide(config, query_strategy, data_profile)

        # Build comprehensive context for LLM
        datasets_info = []
        for dataset in query_strategy.get('datasets', []):
            dataset_desc = f"**{dataset['name']}** ({dataset.get('type', 'unknown')} - {dataset.get('row_count', 'unknown')} records)"
            datasets_info.append(dataset_desc)

        # Build data profile summary with actual field names
        profile_info = []
        for ds_name, ds_profile in data_profile.get('datasets', {}).items():
            fields = list(ds_profile.get('fields', {}).keys())
            profile_info.append(f"**{ds_name}** fields: {', '.join(fields)}")

        # Use ACTUAL tested queries from all_queries.json (not strategy plans)
        tested_queries_info = []
        tested_rag_queries_info = []
        if isinstance(all_queries, dict):
            scripted = all_queries.get('scripted', [])
            parameterized = all_queries.get('parameterized', [])
            rag = all_queries.get('rag', [])
        else:
            scripted = all_queries
            parameterized = []
            rag = []

        for query in scripted + parameterized:
            esql = query.get('esql') or query.get('query') or query.get('example_esql', '')
            name = query.get('name', 'unnamed')
            desc = query.get('description', '')
            tested_queries_info.append(f"**{name}**: {desc}\n```esql\n{esql}\n```")

        for query in rag:
            esql = query.get('esql') or query.get('query') or query.get('example_esql', '')
            name = query.get('name', 'unnamed')
            desc = query.get('description', '')
            search_type = query.get('search_type', 'rag')
            tested_rag_queries_info.append(f"**{name}** (type: {search_type}): {desc}\n```esql\n{esql}\n```")

        # Create template guide structure to show LLM the desired format
        template_guide = """# **Elastic Agent Builder Demo for {COMPANY}**

## **Internal Demo Script & Reference Guide**

---

## **📋 Demo Overview**

**Total Time:** 25-30 minutes
**Audience:** {DEPARTMENT} technical/business stakeholders
**Goal:** Show how Agent Builder enables AI-powered {DEMO_TYPE} on {COMPANY} data

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## **🗂️ Dataset Architecture**

{DATASETS_SECTION}

---

## **🌋 Demo Setup Instructions**

### **Step 1: Upload Sample Datasets in Kibana**

**CRITICAL: All indexes need "index.mode": "lookup" for joins to work**

{DATASET_UPLOAD_INSTRUCTIONS}

---

## **Part 1: AI Agent Chat Teaser (5 minutes)**

### **Setup**
- Navigate to your AI Agent chat interface
- Have the agent already configured with all tools

### **Demo Script**

**Presenter:** "Before we dive into how this works, let me show you the end result. I'm going to ask our AI agent a complex business question."

**Sample questions to demonstrate:**

{TEASER_QUESTIONS}

**Transition:** "So how does this actually work? Let's go under the hood and build these queries from scratch."

---

## **Part 2: ES|QL Query Building (10 minutes)**

### **Setup**
- Open Kibana Dev Tools Console
- Have the indices already created and populated

---

### **Query 1: Simple Aggregation (2 minutes)**

**Presenter:** "{COMPANY} wants to know: {SIMPLE_QUERY_QUESTION}"

**Copy/paste into console:**

```
{SIMPLE_QUERY}
```

**Run and narrate results:** "This is basic ES|QL:
- FROM: Source our data
- STATS: Aggregate with grouping
- SORT and LIMIT: Top results

The syntax is intuitive - it reads like English."

---

### **Query 2: Add Calculations with EVAL (3 minutes)**

**Presenter:** "Let's add calculations to get deeper insights."

**Copy/paste:**

```
{EVAL_QUERY}
```

**Run and highlight:** "Key additions:
- EVAL: Creates calculated fields on-the-fly
- TO_DOUBLE: Critical for decimal division
- Multiple STATS: Aggregating multiple metrics
- Business-relevant calculations

---

### **Query 3: Join Datasets with LOOKUP JOIN (3 minutes)**

**Presenter:** "Now let's combine data from multiple sources using ES|QL's JOIN capability."

**Copy/paste:**

```
{JOIN_QUERY}
```

**Run and explain:** "Magic happening here:
- LOOKUP JOIN: Combines datasets using a join key
- Now we have access to fields from both datasets
- This is a LEFT JOIN: All records kept, enriched with additional data
- For LOOKUP JOIN to work, the joined index must have 'index.mode: lookup'"

---

### **Query 4: Complex Multi-Dataset Analytics (2 minutes)**

**Presenter:** "For the grand finale - a sophisticated analytical query showing {COMPLEX_QUERY_PURPOSE}"

**Copy/paste:**

```
{COMPLEX_QUERY}
```

**Run and break down:** {COMPLEX_QUERY_EXPLANATION}

---

### **Query 5: RAG — AI-Generated Answers from Search Results (3 minutes)**

**Presenter:** "Now here is where it gets exciting. What if instead of just returning raw search results, the system could read the results and generate a natural language answer? That's RAG — Retrieval Augmented Generation — and ES|QL supports it natively."

**Copy/paste:**

```
{RAG_QUERY}
```

**Run and explain:** "Let me break down this pipeline:
- **MATCH**: Semantic search finds the most relevant documents
- **RERANK** (optional): An AI model re-scores results for better precision
- **EVAL + CONCAT**: Builds a prompt from the actual document data
- **COMPLETION**: Sends that prompt to an LLM and returns the generated answer

This is the full RAG pipeline running entirely inside Elasticsearch — no external orchestration, no LangChain, no custom code. The data never leaves the cluster."

**Key Value Points:**
- "RAG queries run as Agent Builder tools — the agent decides WHEN to use retrieval vs analytics"
- "The LLM answer is grounded in actual indexed data, reducing hallucination"
- "Every COMPLETION row is one LLM call — we use LIMIT to control cost"
- "This transforms Elasticsearch from a search engine into an AI-powered knowledge system"

---

## **Part 3: Agent & Tool Creation (5 minutes)**

### **Creating the Agent**

**Agent Configuration:**

**Agent ID:** `{AGENT_ID}`

**Display Name:** `{AGENT_NAME}`

**Custom Instructions:** {AGENT_INSTRUCTIONS_SUMMARY}

---

### **Creating Tools**

{TOOLS_SUMMARY}

---

## **Part 4: AI Agent Q&A Session (5-10 minutes)**

### **Demo Question Set**

**Warm-up:**
{WARMUP_QUESTIONS}

**Business-focused:**
{BUSINESS_QUESTIONS}

**Trend analysis:**
{TREND_QUESTIONS}

---

## **🎯 Key Talking Points**

### **On ES|QL:**
- "Modern query language, built for analytics"
- "Piped syntax is intuitive and readable"
- "Operates on blocks, not rows - extremely performant"
- "Supports complex operations: joins, window functions, time-series"

### **On Agent Builder:**
- "Bridges AI and enterprise data"
- "No custom development - configure, don't code"
- "Works with existing Elasticsearch indices"
- "Agent automatically selects right tools"

### **On RAG & COMPLETION:**
- "Full RAG pipeline runs natively inside Elasticsearch — no external orchestration needed"
- "LLM answers are grounded in actual indexed data, not hallucinated"
- "MATCH finds relevant documents, RERANK improves precision, COMPLETION generates answers"
- "Every query is also an Agent Builder tool — the agent decides when to search vs analyze"
- "Cost-controlled: LIMIT before COMPLETION means you control exactly how many LLM calls"

### **On Business Value:**
- "Democratizes data access - anyone can ask questions"
- "Real-time insights, always up-to-date"
- "Reduces dependency on data teams"
- "Faster decision-making"
- "AI answers grounded in your actual data - not generic responses"

---

## **🔧 Troubleshooting**

**If a query fails:**
- Check index names match exactly
- Verify field names are case-sensitive correct
- Ensure joined indices are in lookup mode

**If agent gives wrong answer:**
- Check tool descriptions - are they clear?
- Review custom instructions

**If join returns no results:**
- Verify join key format is consistent across datasets
- Check that lookup index has data

---

## **🎬 Closing**

"What we've shown today:
✅ Complex analytics on interconnected datasets
✅ Natural language interface for non-technical users
✅ Real-time insights without custom development
✅ Queries that would take hours, answered in seconds
✅ RAG pipeline — AI-generated answers grounded in your actual data, running natively in Elasticsearch

Agent Builder can be deployed in days, not months.

Questions?"
"""

        prompt = f"""Generate a comprehensive, detailed demo guide for an Elastic Agent Builder demonstration.

**Customer Context:**
- Company: {config['company_name']}
- Department: {config['department']}
- Industry: {config['industry']}
- Demo Type: {config.get('demo_type', 'analytics')}

**Pain Points:**
{chr(10).join('- ' + p for p in config.get('pain_points', [])[:5])}

**Use Cases:**
{chr(10).join('- ' + uc for uc in config.get('use_cases', [])[:5])}

**Available Datasets (with actual field names from indexed data):**
{chr(10).join(datasets_info)}

{chr(10).join(profile_info) if profile_info else '(No data profile available)'}

**ACTUAL TESTED ES|QL QUERIES — Scripted & Parameterized (use these EXACTLY — do NOT invent new queries):**
{chr(10).join(tested_queries_info) if tested_queries_info else chr(10).join(f'**{q.get("name", "?")}**: {q.get("description", "")}' for q in query_strategy.get("queries", [])[:8])}

**ACTUAL TESTED RAG/COMPLETION QUERIES (use at least one in the RAG section of the guide):**
{chr(10).join(tested_rag_queries_info) if tested_rag_queries_info else '(No RAG queries available — skip the RAG section)'}

**Your Task:**
Using the template structure provided below, generate a COMPLETE, DETAILED demo guide with:

1. **Real content** - Not placeholders. Use the actual company name, datasets, and query information provided above.

2. **Dataset Architecture section** - Describe each dataset with record counts, primary keys, and the ACTUAL fields listed above (from indexed data profile). Do NOT invent field names.

3. **Demo Setup Instructions** - Specific steps for uploading CSVs and creating lookup mode indices for each dataset.

4. **Part 1: AI Agent Teaser** - 5-7 example questions that showcase different capabilities.

5. **Part 2: ES|QL Query Building** - Select queries from the ACTUAL TESTED QUERIES above that show a progression:
   - Query 1: Simple query (BM25 keyword search or basic aggregation)
   - Query 2: Add EVAL calculations or semantic search
   - Query 3: Hybrid search or LOOKUP JOIN enrichment
   - Query 4: Complex analytics (multi-dataset, INLINESTATS, etc.)
   - **Query 5: RAG/COMPLETION query** — Pick the best RAG query from the tested RAG queries above.
     This is the demo climax: show the full MATCH → RERANK → COMPLETION pipeline.
     If no RAG queries are available, skip this section.

   **CRITICAL: Copy the actual ES|QL from the tested queries above. Do NOT write new queries or modify field names.
   These queries have been validated against the actual indexed data.**

6. **Part 3: Agent & Tool Creation** - Summarize agent configuration with 3-4 key tool examples

7. **Part 4: Q&A Questions** - 10-12 diverse questions organized by category (warmup, business, trends, optimization)

8. **Talking Points** - Keep the standard ES|QL/Agent Builder/Business Value points from template

**CRITICAL FORMATTING RULES:**
- Output ONLY the markdown content (no code fences around the entire guide)
- Use proper markdown syntax
- Keep the emoji section headers (📋, 🗂️, 🌋, 🎯, etc.)
- Queries should be in ```esql``` code blocks
- Make it feel like a real internal demo script with specific, actionable content
- NEVER invent field names — only use fields from the data profile and tested queries above

**Template Structure to Follow:**
{template_guide}

Generate the complete guide now:"""

        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=16000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            guide_content = response.content[0].text.strip()

            # Clean up any potential code fence wrapping
            if guide_content.startswith('```markdown'):
                guide_content = guide_content[len('```markdown'):].strip()
            if guide_content.startswith('```'):
                guide_content = guide_content[3:].strip()
            if guide_content.endswith('```'):
                guide_content = guide_content[:-3].strip()

            logger.info(f"Generated comprehensive demo guide ({len(guide_content)} characters)")
            return guide_content

        except Exception as e:
            logger.error(f"Failed to generate demo guide with LLM: {e}", exc_info=True)
            return self._generate_fallback_demo_guide(config, query_strategy, data_profile)

    def _generate_fallback_demo_guide(self, config: Dict[str, Any],
                                      query_strategy: Dict, data_profile: Dict) -> str:
        """Generate basic fallback demo guide if LLM fails"""
        pain_points = ', '.join(config.get('pain_points', [])[:2]) if config.get('pain_points') else 'operational challenges'

        datasets = query_strategy.get('datasets', [])
        queries = query_strategy.get('queries', [])

        dataset_list = '\n'.join([f"- **{d['name']}** ({d.get('type', 'unknown')} - {d.get('row_count', 'unknown')} records)"
                                  for d in datasets[:5]])

        query_list = '\n'.join([f"{i+1}. **{q['name']}**" for i, q in enumerate(queries[:8])])

        return f"""# Demo Guide: {config['company_name']} - {config['department']}

## 📋 Demo Overview

**Industry:** {config['industry']}
**Focus Areas:** {pain_points}
**Total Time:** 25-30 minutes

**Demo Flow:**
1. AI Agent Chat Teaser (5 min)
2. ES|QL Query Building (10 min)
3. Agent & Tool Creation (5 min)
4. AI Agent Q&A Session (5-10 min)

---

## 🗂️ Datasets

{dataset_list}

---

## 🌋 Key Queries

{query_list}

---

## 🎯 Value Proposition

- **Speed:** Insights in seconds vs hours/days
- **Scalability:** Handles growing data volumes
- **Self-Service:** Empowers teams with intuitive query language

---

## Closing Points

- ES|QL provides SQL-like simplicity with Elasticsearch power
- Queries run directly on indexed data (millisecond response times)
- Agent Builder enables natural language access to data
- Most teams productive within days, not weeks
"""

    def _generate_agent_instructions(self, config: Dict[str, Any], query_descriptions: List[str], datasets_info: List[str]) -> str:
        """Generate agent instructions using LLM based on demo context"""

        if not self.llm_client:
            # Fallback instructions if no LLM available
            return f"""You are an AI assistant specialized in {config.get('department', 'data analysis')} for {config['company_name']}.

Your role is to help users analyze data, answer questions, and provide insights specific to their use cases.

Key responsibilities:
- Analyze data patterns and trends
- Answer questions about the available datasets
- Provide actionable insights and recommendations
- Help users understand their data better

Always be helpful, accurate, and focused on providing value through data-driven insights."""

        # Build context for LLM
        query_context = "\n".join([f"- {desc}" for desc in query_descriptions[:10]]) if query_descriptions else "No queries available yet"
        dataset_context = ", ".join(datasets_info) if datasets_info else "No datasets available yet"

        prompt = f"""Generate professional agent instructions for an Elastic Agent Builder agent.

**Company Context:**
- Company: {config['company_name']}
- Department: {config.get('department', 'General')}
- Industry: {config.get('industry', 'General')}
- Pain Points: {', '.join(config.get('pain_points', []))}
- Use Cases: {', '.join(config.get('use_cases', []))}

**Available Capabilities:**
Query Capabilities:
{query_context}

Available Datasets:
{dataset_context}

**Task:** Generate clear, professional instructions that:
1. Define the agent's role and expertise
2. Explain what types of questions it can answer
3. Reference the specific pain points and use cases
4. Set appropriate tone and communication style
5. Include any industry-specific considerations

The instructions should be 150-250 words, professional but approachable, and specific to this customer's context.

Generate ONLY the instructions text, no additional formatting or explanation."""

        try:
            instructions = self._call_llm(prompt)
            # Clean up any potential formatting
            instructions = instructions.strip()
            if instructions.startswith('"') and instructions.endswith('"'):
                instructions = instructions[1:-1]
            return instructions
        except Exception as e:
            logger.error(f"Failed to generate agent instructions via LLM: {e}")
            # Return fallback instructions
            return f"""You are an AI assistant specialized in {config.get('department', 'data analysis')} for {config['company_name']}.

I help analyze data and provide insights specific to your {config.get('industry', 'business')} operations.

Key areas of focus:
{chr(10).join(['- ' + pp for pp in config.get('pain_points', ['Data analysis', 'Reporting', 'Insights'])[:3]])}

I can assist with:
{chr(10).join(['- ' + uc for uc in config.get('use_cases', ['Analyzing trends', 'Finding patterns', 'Generating reports'])[:3]])}

Feel free to ask questions about your data, request specific analyses, or explore insights that can help optimize your operations."""

    def _get_esql_strict_rules(self) -> str:
        """Get strict ES|QL rules from the centralized rules module"""
        try:
            from src.prompts.esql_strict_rules import get_rules_for_module_generation
            return get_rules_for_module_generation()
        except ImportError:
            logger.warning("Could not import ES|QL strict rules, using fallback")
            # Fallback to minimal rules if import fails
            return self._get_minimal_esql_reference()

    def _get_minimal_esql_reference(self) -> str:
        """Get minimal ES|QL reference as fallback"""
        return """
## CRITICAL ES|QL SYNTAX RULES

### LOOKUP JOIN - NO SUFFIX CONVENTION ⚠️
✅ CORRECT: `| LOOKUP JOIN products ON product_id`
❌ WRONG: `| LOOKUP JOIN products_lookup ON product_id`
NEVER add _lookup suffix to index names.

### MATCH Syntax - ALWAYS WITHIN WHERE ⚠️
✅ CORRECT: `| WHERE MATCH(field, "search term")`
❌ WRONG: `| MATCH field "term"` - MATCH is NOT a pipe operation

### Query Parameters - CANNOT CHECK NULL ⚠️
❌ WRONG: `WHERE ?param IS NULL` - Cannot check if parameter is NULL
Parameters are ALWAYS required when used.

### DATE Functions - Parameter Order ⚠️
✅ CORRECT: `DATE_TRUNC(1 hour, @timestamp)`
❌ WRONG: `DATE_TRUNC(@timestamp, 1 hour)` - Wrong order
"""

    def _read_esql_docs(self) -> str:
        """Read ES|QL documentation for RAG query generation

        Reads key ES|QL docs needed for generating RAG queries:
        - search-match.md (MATCH/MATCH_PHRASE)
        - rerank.md (RERANK command)
        - completion.md (COMPLETION command)
        - metadata-fields.md (METADATA _score)
        """
        try:
            from pathlib import Path
            docs_path = Path('docs/esql')

            docs = []
            doc_files = [
                'search-match.md',
                'rerank.md',
                'completion.md',
                'metadata-fields.md'
            ]

            for doc_file in doc_files:
                doc_path = docs_path / doc_file
                if doc_path.exists():
                    content = doc_path.read_text()
                    # Include first 2000 chars of each doc (enough for syntax/examples)
                    docs.append(f"### {doc_file}\n{content[:2000]}")

            if docs:
                return "\n\n---\n\n".join(docs)
            else:
                logger.warning("ES|QL docs not found, using minimal reference")
                return self._get_minimal_esql_reference()

        except Exception as e:
            logger.warning(f"Could not read ES|QL docs: {e}")
            return self._get_minimal_esql_reference()

    def _get_minimal_esql_reference(self) -> str:
        """Minimal ES|QL reference if docs unavailable"""
        rerank_endpoint = self.inference_endpoints['rerank']
        completion_endpoint = self.inference_endpoints['completion']

        return f"""
### ES|QL Commands for RAG Queries

**MATCH (Semantic Search):**
```
WHERE MATCH(field, "query", {{"boost": 0.75}})
```

**RERANK (ML Relevance):**
```
| RERANK query_text ON field1, field2 WITH {{"inference_id": """ + f'"{rerank_endpoint}"' + """}}
```

**INLINE STATS (Preserve Fields):**
```
| INLINE STATS context = MV_CONCAT(field, " --- ")
```

**COMPLETION (LLM Generation):**
```
| EVAL prompt = CONCAT("Summarize these results. ", "Title: ", title, " Content: ", content)
| COMPLETION answer = prompt WITH {{"inference_id": """ + f'"{completion_endpoint}"' + """}}
```

**CRITICAL CONCAT STRING RULE:** ES|QL does NOT support newlines or escape sequences in string literals!
❌ WRONG: `CONCAT("Line one\\nLine two")` — causes parsing_exception
✅ CORRECT: `CONCAT("Line one. ", "Line two. ", "Title: ", title)` — separate args, no newlines

**METADATA (Score):**
```
FROM index METADATA _score
```

**Parameter Syntax:**
```
?param_name  (for Agent Builder tools)
```

**CRITICAL:** Use INLINE STATS not STATS before COMPLETION!
"""

    def _call_llm(self, prompt: str, max_tokens: int = 16000) -> str:
        """Call LLM to generate code

        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum output tokens (default 16000, use higher for large data generators)
        """
        logger.info(f"📤 Calling LLM with prompt length: {len(prompt)} characters, max_tokens: {max_tokens}")

        stop_reason = None
        if hasattr(self.llm_client, 'messages'):  # Anthropic
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            code = response.content[0].text
            stop_reason = getattr(response, 'stop_reason', None)
            logger.info(f"📥 LLM response length: {len(code)} characters, stop_reason: {stop_reason}")
        elif hasattr(self.llm_client, 'chat'):  # OpenAI
            response = self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            code = response.choices[0].message.content
            stop_reason = getattr(response.choices[0], 'finish_reason', None)
            logger.info(f"📥 LLM response length: {len(code)} characters, stop_reason: {stop_reason}")
        else:
            return ""

        # Detect truncated output
        if stop_reason in ('max_tokens', 'length'):
            logger.warning(f"⚠️ LLM output was truncated (stop_reason={stop_reason}, max_tokens={max_tokens})")

        # Extract Python code
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
            logger.info(f"✂️  Extracted Python code: {len(code)} characters")

        return code

    def _validate_python_syntax(self, code: str, module_name: str, auto_fix: bool = True) -> str:
        """Validate Python syntax, optionally auto-fixing via LLM retry

        Args:
            code: Python code to validate
            module_name: Name of module being validated (for error messages)
            auto_fix: If True and LLM client is available, attempt to fix syntax errors

        Returns:
            The validated (and possibly fixed) code

        Raises:
            SyntaxError: If code has syntax errors and cannot be fixed
        """
        try:
            compile(code, module_name, 'exec')
            logger.info(f"✅ Syntax validation passed for {module_name}")
            return code
        except SyntaxError as e:
            logger.error(f"❌ Syntax error in generated {module_name}: {e}")
            logger.error(f"Error at line {e.lineno}: {e.text}")

            if not auto_fix or not self.llm_client:
                raise SyntaxError(f"Generated code has syntax error at line {e.lineno}: {e.msg}")

            # Attempt LLM-assisted fix
            logger.info(f"🔧 Attempting auto-fix of syntax error in {module_name}...")
            error_context = self._get_error_context(code, e.lineno)
            fix_prompt = f"""The following Python code has a syntax error at line {e.lineno}: {e.msg}

Error context (lines around the error):
```
{error_context}
```

The problematic line text: {e.text}

Common causes of "unterminated string literal":
- A string opened with a quote but not closed on the same line (use triple quotes for multi-line)
- An apostrophe inside a single-quoted string (use double quotes or escape)
- A backslash at the end of a string that escapes the closing quote

Return the COMPLETE fixed Python code. Do not omit any functions or classes.
The full original code is below — fix ONLY the syntax error, do not change logic:

```python
{code}
```"""
            try:
                fixed_code = self._call_llm(fix_prompt)
                compile(fixed_code, module_name, 'exec')
                logger.info(f"✅ Auto-fix succeeded for {module_name}")
                return fixed_code
            except SyntaxError as e2:
                logger.error(f"❌ Auto-fix failed for {module_name}: {e2}")
                raise SyntaxError(f"Generated code has syntax error at line {e.lineno}: {e.msg} (auto-fix also failed)")

    @staticmethod
    def _get_error_context(code: str, error_line: int, context_lines: int = 5) -> str:
        """Extract lines around an error for context"""
        lines = code.split('\n')
        start = max(0, error_line - context_lines - 1)
        end = min(len(lines), error_line + context_lines)
        context = []
        for i in range(start, end):
            marker = " >>> " if i == error_line - 1 else "     "
            context.append(f"{marker}{i + 1}: {lines[i]}")
        return '\n'.join(context)

    def _validate_query_module_methods(self, code: str) -> Dict[str, bool]:
        """Validate that query module has all required methods using AST parsing

        Args:
            code: Python code to validate

        Returns:
            Dict mapping method names to boolean (True if present)
        """
        import ast

        required_methods = {
            'generate_queries': False,
            'generate_parameterized_queries': False,
            'generate_rag_queries': False
        }

        try:
            tree = ast.parse(code)

            # Find all method definitions in classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if item.name in required_methods:
                                required_methods[item.name] = True

            # Log results
            logger.info("🔍 Query module method validation:")
            for method, present in required_methods.items():
                status = "✅" if present else "❌"
                logger.info(f"  {status} {method}: {'FOUND' if present else 'MISSING'}")

            return required_methods

        except Exception as e:
            logger.error(f"❌ Failed to parse code for method validation: {e}")
            return required_methods

    def _generate_mock_data_module(self, config: Dict[str, Any]) -> str:
        """Generate mock data module for testing"""
        company = config['company_name'].replace(' ', '')
        return f"""from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

class {company}DataGenerator(DataGeneratorModule):
    \"\"\"Data generator for {config['company_name']} - {config['department']}\"\"\"

    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        \"\"\"Generate datasets specific to {config['company_name']}'s needs\"\"\"
        datasets = {{}}

        # Customers dataset
        customers = pd.DataFrame({{
            'customer_id': [f'CUST-{{i:06d}}' for i in range(1000)],
            'company_name': [f'Customer {{i}}' for i in range(1000)],
            'segment': np.random.choice(['Enterprise', 'SMB', 'Startup'], 1000),
            'industry': np.random.choice(['{config["industry"]}', 'Other'], 1000),
            'lifetime_value': np.random.lognormal(10, 2, 1000)
        }})
        datasets['customers'] = customers

        # Transactions dataset
        # IMPORTANT: Use datetime.now() as end date so ES|QL queries with NOW() work
        transactions = pd.DataFrame({{
            'transaction_id': [f'TXN-{{i:08d}}' for i in range(10000)],
            'customer_id': np.random.choice(customers['customer_id'], 10000),
            'amount': np.random.lognormal(5, 1.5, 10000),
            'timestamp': pd.date_range(end=datetime.now(), periods=10000, freq='h')
        }})
        datasets['transactions'] = transactions

        return datasets

    def get_relationships(self) -> List[tuple]:
        \"\"\"Define foreign key relationships\"\"\"
        return [
            ('transactions', 'customer_id', 'customers')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        \"\"\"Describe each dataset\"\"\"
        return {{
            'customers': 'Customer master data with segmentation',
            'transactions': 'Transaction history with amounts and timestamps'
        }}
"""

    def _generate_mock_query_module(self, config: Dict[str, Any]) -> str:
        """Generate mock query module for testing"""
        company = config['company_name'].replace(' ', '')
        return f"""from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class {company}QueryGenerator(QueryGeneratorModule):
    \"\"\"Query generator for {config['company_name']} - {config['department']}\"\"\"

    def generate_queries(self) -> List[Dict[str, Any]]:
        \"\"\"Generate ES|QL queries specific to {config['company_name']}'s use cases\"\"\"

        queries = [
            {{
                'name': 'Customer Overview',
                'description': 'High-level customer metrics',
                'esql': 'FROM customers | STATS total = COUNT(*), avg_value = AVG(lifetime_value) BY segment',
                'expected_insight': 'Customer distribution and value by segment'
            }},
            {{
                'name': 'Transaction Analysis',
                'description': 'Transaction patterns over time',
                'esql': 'FROM transactions | EVAL day = DATE_TRUNC(1 day, timestamp) | STATS daily_total = SUM(amount) BY day',
                'expected_insight': 'Daily transaction volumes and trends'
            }}
        ]

        return queries

    def get_query_progression(self) -> List[str]:
        \"\"\"Define the order to present queries for maximum impact\"\"\"
        return ['Customer Overview', 'Transaction Analysis']
"""

    def _generate_mock_guide_module(self, config: Dict[str, Any]) -> str:
        """Generate mock guide module for testing"""
        company = config['company_name'].replace(' ', '')
        return f"""from src.framework.base import DemoGuideModule, DemoConfig
from typing import Dict, List, Any, Optional
import pandas as pd

class {company}DemoGuide(DemoGuideModule):
    \"\"\"Demo guide for {config['company_name']} - {config['department']}\"\"\"

    def generate_guide(self) -> str:
        \"\"\"Generate customized demo guide\"\"\"
        guide = \"\"\"# Demo Guide: {config['company_name']} - {config['department']}

## Opening Hook
"I understand you're facing {', '.join(config['pain_points'])}. Let me show you how Agent Builder solves this..."

## Demo Flow
1. Start with overview metrics
2. Drill down into specific pain points
3. Show real-time analysis capabilities
4. Demonstrate natural language queries
        \"\"\"
        return guide

    def get_talk_track(self) -> Dict[str, str]:
        \"\"\"Generate talk track for each query\"\"\"
        return {{
            'Customer Overview': 'Notice how quickly we can segment your customer base...',
            'Transaction Analysis': 'This shows real-time transaction patterns...'
        }}

    def get_objection_handling(self) -> Dict[str, str]:
        \"\"\"Industry-specific objection handling\"\"\"
        return {{
            'How is this different from our BI tool?': 'Agent Builder provides real-time, conversational analytics...',
            'What about data security?': 'Enterprise-grade security with full encryption and RBAC...'
        }}
"""
    def _remove_timestamp_parameters(self, parameterized_queries: List[Dict]) -> List[Dict]:
        """Remove @timestamp-related parameters from parameterized queries

        Despite LLM guidance, timestamp parameters (start_date, end_date, etc.) still get generated.
        This scanner removes them post-generation.

        Args:
            parameterized_queries: List of parameterized query dicts

        Returns:
            List of queries with timestamp parameters removed
        """
        # Parameter names that should be removed
        timestamp_param_names = {
            'start_date', 'end_date', 'start_time', 'end_time',
            'timestamp', 'from_date', 'to_date', 'date_from', 'date_to',
            'time_from', 'time_to', 'start_timestamp', 'end_timestamp'
        }

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
                    if name.lower() not in timestamp_param_names
                }

                if len(cleaned_params) < original_param_count:
                    removed_params = set(parameters.keys()) - set(cleaned_params.keys())
                    removed_count += len(removed_params)
                    logger.info(f"Removed timestamp parameters from '{query.get('name', 'unknown')}': {removed_params}")
                    query_copy['parameters'] = cleaned_params

            # Handle list format: [{"name": "start_date", "type": "date", ...}, ...]
            elif isinstance(parameters, list):
                original_param_count = len(parameters)
                cleaned_params = [
                    param for param in parameters
                    if param.get('name', '').lower() not in timestamp_param_names
                ]

                if len(cleaned_params) < original_param_count:
                    removed_params = [p.get('name') for p in parameters if p.get('name', '').lower() in timestamp_param_names]
                    removed_count += len(removed_params)
                    logger.info(f"Removed timestamp parameters from '{query.get('name', 'unknown')}': {removed_params}")
                    query_copy['parameters'] = cleaned_params

            cleaned_queries.append(query_copy)

        if removed_count > 0:
            logger.warning(f"⚠️ Removed {removed_count} timestamp parameters from parameterized queries "
                          f"(LLM ignored guidance). Agents should handle time ranges via platform.core.execute_esql.")

        return cleaned_queries

    def _generate_static_files(self, module_path: Path):
        """Generate static files for quick loading in Browse mode

        Creates:
        - CSV files for each dataset
        - all_queries.json for all query types (scripted, parameterized, rag)
        - demo_guide.md for guide text
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
                parameterized_queries = self._remove_timestamp_parameters(parameterized_queries)

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
