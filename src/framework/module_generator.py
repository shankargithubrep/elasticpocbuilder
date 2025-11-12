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

    def generate_demo_module(self, config: Dict[str, Any], query_plan: Optional[Dict[str, Any]] = None) -> str:
        """Generate a complete demo module for a customer

        Args:
            config: Demo configuration with customer context
            query_plan: Optional query plan with field requirements (from LightweightQueryPlanner)

        Returns:
            Path to the generated module directory
        """
        # Create unique module name
        company_slug = config['company_name'].lower().replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        module_name = f"{company_slug}_{config['department'].lower()}_{timestamp}"
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
            self._generate_agent_metadata(config, module_path)
        else:
            logger.info("Using original data-first generation (no query plan)")
            # Generate each component (Python modules) - original flow
            self._generate_data_module(config, module_path)
            self._generate_query_module(config, module_path)
            self._generate_guide_module(config, module_path)
            self._generate_config_file(config, module_path)
            self._generate_agent_metadata(config, module_path)

        # Generate static files for quick loading
        self._generate_static_files(module_path)

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
        # Create unique module name
        company_slug = config['company_name'].lower().replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        module_name = f"{company_slug}_{config['department'].lower()}_{timestamp}"
        module_path = self.base_path / module_name

        # Create module directory structure
        module_path.mkdir(parents=True, exist_ok=True)
        (module_path / '__init__.py').touch()

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
        self._generate_config_file(config, module_path)
        self._generate_agent_metadata(config, module_path)

        # Generate static files for quick loading
        self._generate_static_files(module_path)

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
        # Create unique module name
        company_slug = config['company_name'].lower().replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        module_name = f"{company_slug}_{config['department'].lower()}_{timestamp}"
        module_path = self.base_path / module_name

        # Create module directory structure
        module_path.mkdir(parents=True, exist_ok=True)
        (module_path / '__init__.py').touch()

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

    def _generate_data_module(self, config: Dict[str, Any], module_path: Path):
        """Generate the data generation module"""

        # Get dataset size preference and calculate ranges
        size_preference = config.get('dataset_size_preference', 'medium')
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

        ranges = size_ranges[size_preference]

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

CRITICAL - TIMESTAMP REQUIREMENTS:
- All timestamp/datetime columns MUST use datetime.now() as the END date
- Generate data going BACKWARDS from today, maximum 120 days old
- NEVER hardcode dates like '2023-01-01' or generate future dates
- NEVER generate data older than 120 days from today
- Use pd.date_range(end=datetime.now(), periods=N, freq='h') for timeseries data
- Example: For 90 days of hourly data use periods=90*24 (2,160 rows)
- This ensures ES|QL queries with "NOW() - X days" will return results (stay within 120-day window)

CRITICAL - DATASET SIZES ({size_preference.upper()} preference):
- Primary timeseries datasets: {ranges['timeseries_typical']} rows (MAX {ranges['timeseries_max']:,})
- Reference/lookup tables: {ranges['reference_typical']} rows (MAX {ranges['reference_max']:,})
- Scale mentioned ({config["scale"]}) is for REALISM only, don't generate that many!

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
        # Scale mentioned: {config["scale"]} (for context only, don't generate that many rows!)

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
            code = self._call_llm(prompt)
        else:
            code = self._generate_mock_data_module(config)

        # Validate syntax before saving
        self._validate_python_syntax(code, 'data_generator.py')

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

        # Validate syntax before saving
        self._validate_python_syntax(full_code, 'query_generator.py')

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

        # Validate syntax
        self._validate_python_syntax(full_code, 'query_generator.py')

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
- WRONG: `| STATS context = MV_CONCAT(field, "\\n")`  ← Loses all fields except context!
- CORRECT: `| INLINE STATS all_context = MV_CONCAT(context, "\\n\\n")`  ← Preserves fields!

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
            | INLINE STATS all_context = MV_CONCAT(context, "\\\\n\\\\n")
            | EVAL prompt = CONCAT(
                "Based on these records:\\\\n\\\\n",
                all_context,
                "\\\\n\\\\nQuestion: ", ?user_question,
                "\\\\n\\\\nProvide a detailed answer:"
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

        if hasattr(self.llm_client, 'messages'):  # Anthropic
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=max_tokens,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            code = response.content[0].text
            logger.info(f"📥 LLM response length: {len(code)} characters")
        elif hasattr(self.llm_client, 'chat'):  # OpenAI
            response = self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            code = response.choices[0].message.content
            logger.info(f"📥 LLM response length: {len(code)} characters")
        else:
            return ""

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
        return '''{{guide_content}}'''

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

        # Validate syntax before saving
        self._validate_python_syntax(code, 'demo_guide.py')

        # Save the module
        module_file = module_path / 'demo_guide.py'
        module_file.write_text(code)

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

        # Get dataset size preference and calculate ranges
        size_preference = config.get('dataset_size_preference', 'medium')
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

        ranges = size_ranges[size_preference]

        prompt = f"""Generate a Python module that implements DataGeneratorModule for this customer:

Company: {config["company_name"]}
Department: {config["department"]}
Industry: {config["industry"]}
Pain Points: {", ".join(config["pain_points"])}
Use Cases: {", ".join(config["use_cases"])}
Scale: {config["scale"]}
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

CRITICAL - TIMESTAMP REQUIREMENTS:
- All @timestamp or timestamp columns MUST use datetime.now() as the END date
- Generate data going BACKWARDS from today, maximum 120 days old
- NEVER hardcode dates like '2023-01-01' or generate future dates
- Use pd.date_range(end=datetime.now(), periods=N, freq='h') for timeseries data
- This ensures ES|QL queries with "NOW() - X days" will return results

CRITICAL - FIELD NAMING:
- Use EXACT field names from requirements (case-sensitive!)
- For timeseries datasets, use '@timestamp' not 'timestamp'
- Match field types exactly (keyword, date, float, text)

CRITICAL - DATASET SIZES ({size_preference.upper()} preference):
- Primary timeseries datasets: {ranges['timeseries_typical']} rows (MAX {ranges['timeseries_max']:,})
- Reference/lookup tables: {ranges['reference_typical']} rows (MAX {ranges['reference_max']:,})
- Scale mentioned ({config["scale"]}) is for REALISM only, don't generate that many!

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

        WARNING: Do NOT use this for lists of lists with varying lengths!
        For example, if you have networks = [['HMO', 'PPO'], ['PPO', 'EPO'], ['HMO']],
        use Python's random.choice() instead:
            import random
            'networks': [','.join(random.choice(networks)) for _ in range(n)]
        \"\"\"
        if weights is not None:
            weights = np.array(weights, dtype=float)
            probabilities = weights / weights.sum()
            return np.random.choice(choices, size=size, p=probabilities, replace=replace)
        else:
            return np.random.choice(choices, size=size, replace=replace)

    @staticmethod
    def random_timedelta(start_date, end_date=None, days=None, hours=None, minutes=None):
        \"\"\"Generate random timedelta-adjusted datetime, handling numpy int64 conversion.\"\"\"
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

**CODE EFFICIENCY GUIDELINES:**
- Keep inline lists SHORT (max 10-15 items), use variables for long lists
- Minimize comments - let code be self-documenting
- Use loops and list comprehensions instead of repetitive code
- Avoid overly verbose variable names
- Focus on correctness and brevity

Generate the complete implementation with ALL required fields:"""

        if self.llm_client:
            code = self._call_llm(prompt)
        else:
            code = self._generate_mock_data_module(config)

        # Validate syntax before saving
        self._validate_python_syntax(code, 'data_generator.py')

        # Save the module
        module_file = module_path / 'data_generator.py'
        module_file.write_text(code)
        logger.info("Generated data_generator.py with strategy requirements")

    def _generate_query_module_with_strategy(self, config: Dict[str, Any],
                                             module_path: Path,
                                             query_strategy: Dict,
                                             data_profile: Optional[Dict[str, Any]] = None):
        """Generate query module using pre-planned query strategy

        Args:
            config: Demo configuration
            module_path: Path to module directory
            query_strategy: Complete query strategy with planned queries
            data_profile: Optional profiled data from Elasticsearch (field names, values, combinations)
        """
        logger.info("→ Entering _generate_query_module_with_strategy")
        logger.info(f"  Config keys: {list(config.keys())}")
        logger.info(f"  Query strategy has {len(query_strategy.get('queries', []))} queries")
        logger.info(f"  Data profile available: {data_profile is not None}")

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
            "- ES|QL queries with JSON parameters use SINGLE curly braces: MATCH(field, \"term\", {\"boost\": 0.75})",
            "- When using triple-quoted strings (recommended): Use single braces directly",
            "  Example: query = \"\"\"FROM index | WHERE MATCH(field, \"term\", {\"boost\": 1.5})\"\"\"",
            "- When using f-strings: Must double the braces to escape them",
            "  Example: query = f\"\"\"FROM index | WHERE MATCH(field, \"term\", {{\"boost\": 1.5}})\"\"\"",
            "- IMPORTANT: The final ES|QL syntax must always have SINGLE braces {} in the query string",
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
            "        \"\"\"Generate ALL ES|QL queries from pre-planned strategy",
            "",
            "        CRITICAL: Categorize each query with query_type field:",
            "        - \"scripted\": Basic queries that don't take user parameters",
            "        - \"parameterized\": Queries that can be customized with user input",
            "        - \"rag\": RAG queries using MATCH -> RERANK -> COMPLETION pipeline",
            "        \"\"\"",
            "        queries = []",
            "",
            "        # Implement SCRIPTED queries (simple, no parameters)",
            "        # Each query should have: name, description, tool_metadata, query, query_type=\"scripted\"",
            "",
            "        # Implement PARAMETERIZED queries (user can customize)",
            "        # Each query should have: name, description, tool_metadata, query, query_type=\"parameterized\", parameters",
            "",
            "        # Implement RAG queries for semantic_text fields",
            "        # Each query should have: name, description, tool_metadata, query, query_type=\"rag\"",
            "        # RAG queries MUST use: MATCH -> RERANK (optional) -> COMPLETION pipeline",
            "",
            "        return queries",
            "",
            "    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:",
            "        \"\"\"Generate parameterized queries that accept user input",
            "",
            "        These are Agent Builder Tool queries that let users customize parameters.",
            "        Include parameter definitions for each query.",
            "        \"\"\"",
            "        queries = []",
            "",
            "        # Implement parameterized queries from strategy",
            "        # Each should define parameters users can customize",
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
                code = self._call_llm(prompt)
                logger.info(f"✓ LLM returned {len(code)} characters of code")
            else:
                logger.warning("No LLM client, using mock generator")
                code = self._generate_mock_query_module(config)
        except Exception as e:
            logger.error(f"✗ LLM call failed: {e}", exc_info=True)
            raise

        # Validate syntax before saving
        logger.info("→ Validating Python syntax...")
        try:
            self._validate_python_syntax(code, 'query_generator.py')
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
            }
        }

        config_file = module_path / 'config.json'
        config_file.write_text(json.dumps(config_data, indent=2))

    def _generate_agent_metadata(self, config: Dict[str, Any], module_path: Path):
        """Generate agent metadata for Elastic Agent Builder deployment

        Creates agent_metadata.json with all required fields for the Kibana API.
        """
        logger.info("Generating agent metadata...")

        # Generate agent ID and basic info
        company_slug = config['company_name'].lower().replace(' ', '_')[:20]
        dept_slug = config.get('department', 'general').lower().replace(' ', '_')[:15]
        agent_id = f"{company_slug}_{dept_slug}_agent"

        # Generate avatar symbol from company initials
        company_words = config['company_name'].split()
        if len(company_words) >= 2:
            avatar_symbol = (company_words[0][0] + company_words[1][0]).upper()[:2]
        else:
            avatar_symbol = config['company_name'][:2].upper()

        # Select color based on demo type
        demo_type = config.get('demo_type', 'analytics')
        avatar_color = "#3B82F6" if demo_type == 'analytics' else "#10B981"  # Blue for analytics, green for search

        # Prepare context for LLM to generate instructions
        try:
            # Load queries to understand what the agent can do
            queries_file = module_path / 'queries.json'
            if queries_file.exists():
                with open(queries_file, 'r') as f:
                    queries = json.load(f)
                query_descriptions = [q.get('description', q.get('name', '')) for q in queries[:10]]  # First 10 queries
            else:
                query_descriptions = []

            # Load datasets to understand what data is available
            datasets_info = []
            data_dir = module_path / 'data'
            if data_dir.exists():
                for csv_file in data_dir.glob('*.csv'):
                    dataset_name = csv_file.stem
                    datasets_info.append(dataset_name)

        except Exception as e:
            logger.warning(f"Could not load context for agent instructions: {e}")
            query_descriptions = []
            datasets_info = []

        # Generate agent instructions using LLM
        instructions = self._generate_agent_instructions(config, query_descriptions, datasets_info)

        # Create agent metadata structure
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

        # Save agent metadata
        agent_file = module_path / 'agent_metadata.json'
        agent_file.write_text(json.dumps(agent_metadata, indent=2))
        logger.info(f"Generated agent_metadata.json with ID: {agent_id}")

    def _generate_demo_guide_content(self, config: Dict[str, Any], module_path: Path) -> str:
        """Generate comprehensive demo guide content using LLM

        Args:
            config: Demo configuration
            module_path: Path to module directory

        Returns:
            Formatted markdown demo guide content
        """
        # Load query strategy and data profile for context
        try:
            import json
            query_strategy_file = module_path / 'query_strategy.json'
            data_profile_file = module_path / 'data_profile.json'

            query_strategy = {}
            data_profile = {}

            if query_strategy_file.exists():
                with open(query_strategy_file, 'r') as f:
                    query_strategy = json.load(f)

            if data_profile_file.exists():
                with open(data_profile_file, 'r') as f:
                    data_profile = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load strategy/profile for guide generation: {e}")
            query_strategy = {}
            data_profile = {}

        # Fallback if no LLM available
        if not self.llm_client:
            return self._generate_fallback_demo_guide(config, query_strategy, data_profile)

        # Build comprehensive context for LLM
        datasets_info = []
        for dataset in query_strategy.get('datasets', []):
            dataset_desc = f"**{dataset['name']}** ({dataset.get('type', 'unknown')} - {dataset.get('row_count', 'unknown')} records)"
            datasets_info.append(dataset_desc)

        queries_info = []
        for query in query_strategy.get('queries', [])[:8]:  # Top 8 queries
            query_desc = f"**{query['name']}**: {query.get('description', '')}"
            queries_info.append(query_desc)

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

## **🚀 Demo Setup Instructions**

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

### **On Business Value:**
- "Democratizes data access - anyone can ask questions"
- "Real-time insights, always up-to-date"
- "Reduces dependency on data teams"
- "Faster decision-making"

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

**Available Datasets:**
{chr(10).join(datasets_info)}

**Key Queries:**
{chr(10).join(queries_info)}

**Your Task:**
Using the template structure provided below, generate a COMPLETE, DETAILED demo guide with:

1. **Real content** - Not placeholders. Use the actual company name, datasets, and query information provided above.

2. **Dataset Architecture section** - Describe each dataset with record counts, primary keys, fields, relationships. Be specific using the dataset info above.

3. **Demo Setup Instructions** - Specific steps for uploading CSVs and creating lookup mode indices for each dataset.

4. **Part 1: AI Agent Teaser** - 5-7 example questions that showcase different capabilities (ROI analysis, trend detection, cross-dataset joins, etc.)

5. **Part 2: ES|QL Query Building** - Create 3-4 progressive queries:
   - Query 1: Simple aggregation (2-3 lines)
   - Query 2: Add EVAL calculations (5-8 lines)
   - Query 3: LOOKUP JOIN enrichment (8-12 lines)
   - Query 4: Complex multi-dataset analytics (15-25 lines)

   Use ACTUAL query concepts from the key queries listed above. Make them realistic and runnable.

6. **Part 3: Agent & Tool Creation** - Summarize agent configuration with 3-4 key tool examples

7. **Part 4: Q&A Questions** - 10-12 diverse questions organized by category (warmup, business, trends, optimization)

8. **Talking Points** - Keep the standard ES|QL/Agent Builder/Business Value points from template

**CRITICAL FORMATTING RULES:**
- Output ONLY the markdown content (no code fences around the entire guide)
- Use proper markdown syntax
- Keep the emoji section headers (📋, 🗂️, 🚀, 🎯, etc.)
- Queries should be in ```esql``` code blocks
- Make it feel like a real internal demo script with specific, actionable content

**Template Structure to Follow:**
{template_guide}

Generate the complete guide now:"""

        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-5-20250929",
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

## 🚀 Key Queries

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
| INLINE STATS context = MV_CONCAT(field, "\\n")
```

**COMPLETION (LLM Generation):**
```
| COMPLETION answer = prompt WITH {{"inference_id": """ + f'"{completion_endpoint}"' + """}}
```

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

    def _call_llm(self, prompt: str) -> str:
        """Call LLM to generate code"""
        logger.info(f"📤 Calling LLM with prompt length: {len(prompt)} characters")

        if hasattr(self.llm_client, 'messages'):  # Anthropic
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=16000,  # Increased from 8000 to fit all 3 query methods
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            code = response.content[0].text
            logger.info(f"📥 LLM response length: {len(code)} characters")
        elif hasattr(self.llm_client, 'chat'):  # OpenAI
            response = self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=16000  # Increased from 8000
            )
            code = response.choices[0].message.content
            logger.info(f"📥 LLM response length: {len(code)} characters")
        else:
            return ""

        # Extract Python code
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]
            logger.info(f"✂️  Extracted Python code: {len(code)} characters")

        return code

    def _validate_python_syntax(self, code: str, module_name: str) -> None:
        """Validate Python syntax and raise error if invalid

        Args:
            code: Python code to validate
            module_name: Name of module being validated (for error messages)

        Raises:
            SyntaxError: If code has syntax errors
        """
        try:
            compile(code, module_name, 'exec')
            logger.info(f"✅ Syntax validation passed for {module_name}")
        except SyntaxError as e:
            logger.error(f"❌ Syntax error in generated {module_name}: {e}")
            logger.error(f"Error at line {e.lineno}: {e.text}")
            raise SyntaxError(f"Generated code has syntax error at line {e.lineno}: {e.msg}")

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
    def _generate_static_files(self, module_path: Path):
        """Generate static files for quick loading in Browse mode

        Creates:
        - CSV files for each dataset
        - queries.json for query list
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

            # Generate and save queries as JSON
            logger.info("Generating static queries file...")
            query_gen = loader.load_query_generator(datasets)
            queries = query_gen.generate_queries()

            queries_file = module_path / 'queries.json'
            queries_file.write_text(json.dumps(queries, indent=2))
            logger.info(f"  Saved queries.json ({len(queries)} queries)")

            # Generate and save demo guide as Markdown
            logger.info("Generating static guide file...")
            guide_gen = loader.load_demo_guide(datasets, queries)
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
