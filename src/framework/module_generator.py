"""
Module Generator using LLM
Generates demo-specific modules that implement the base framework
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ModuleGenerator:
    """Generates demo modules using LLM"""

    def __init__(self, llm_client=None):
        """Initialize with LLM client"""
        self.llm_client = llm_client
        self.base_path = Path("demos")  # Where demo modules are stored

    def generate_demo_module(self, config: Dict[str, Any]) -> str:
        """Generate a complete demo module for a customer

        Args:
            config: Demo configuration with customer context

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

        # Generate each component (Python modules)
        self._generate_data_module(config, module_path)
        self._generate_query_module(config, module_path)
        self._generate_guide_module(config, module_path)
        self._generate_config_file(config, module_path)

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

        # Generate static files for quick loading
        self._generate_static_files(module_path)

        logger.info(f"Generated demo module with strategy at: {module_path}")
        return str(module_path)

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

Company: {config['company_name']}
Department: {config['department']}
Industry: {config['industry']}
Pain Points: {', '.join(config['pain_points'])}
Use Cases: {', '.join(config['use_cases'])}
Scale: {config['scale']}
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
- Scale mentioned ({config['scale']}) is for REALISM only, don't generate that many!

Template:
```python
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

class {config['company_name'].replace(' ', '')}DataGenerator(DataGeneratorModule):
    \"\"\"Data generator for {config['company_name']} - {config['department']}\"\"\"

    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        \"\"\"Generate datasets specific to {config['company_name']}'s needs\"\"\"
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
        # Scale mentioned: {config['scale']} (for context only, don't generate that many rows!)

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
        """Generate the query generation module with THREE query types:
        1. Scripted queries (tested, non-parameterized)
        2. Parameterized queries (Agent Builder tools)
        3. RAG queries (MATCH → RERANK → COMPLETION)
        """

        # Read ES|QL documentation for reference
        esql_docs = self._read_esql_docs()

        prompt = f"""Generate a Python module that implements QueryGeneratorModule with THREE types of queries.

**Customer Context:**
Company: {config['company_name']}
Department: {config['department']}
Pain Points: {', '.join(config['pain_points'])}
Use Cases: {', '.join(config['use_cases'])}

**CRITICAL - Generate ALL THREE Query Types:**

1. **SCRIPTED QUERIES** (generate_queries method):
   - Non-parameterized, fully tested ES|QL queries
   - Hard-coded values addressing specific pain points
   - These serve as the foundation for parameterized versions

2. **PARAMETERIZED QUERIES** (generate_parameterized_queries method):
   - Based on validated scripted queries
   - Use ?parameter syntax for Agent Builder ES|QL tools
   - NOT executed in this app - tool definitions only
   - AVOID LIKE/RLIKE operators (not supported with parameters!)

3. **RAG QUERIES** (generate_rag_queries method):
   - MATCH → RERANK → COMPLETION pipeline
   - For open-ended question answering
   - Use INLINE STATS (NOT STATS) to preserve fields!

**ES|QL Reference Documentation:**
{esql_docs}

**CRITICAL - ESCAPING ES|QL QUERIES IN PYTHON:**
- ES|QL queries with JSON parameters use curly braces: MATCH(field, "term", {{"boost": 0.75}})
- ALWAYS use double curly braces {{{{ }}}} to escape JSON in queries when using f-strings
- Example CORRECT: query = f\"\"\"FROM index | WHERE MATCH(field, "term", {{"boost": 1.5}})\"\"\"
- Example WRONG: query = f\"\"\"FROM index | WHERE MATCH(field, "term", {"boost": 1.5})\"\"\"

**Template Structure:**
```python
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class {config['company_name'].replace(' ', '')}QueryGenerator(QueryGeneratorModule):
    \"\"\"Query generator for {config['company_name']} - {config['department']}

    Generates three types of queries:
    1. Scripted (tested, non-parameterized)
    2. Parameterized (Agent Builder tools)
    3. RAG (semantic search + LLM completion)
    \"\"\"

    def generate_queries(self) -> List[Dict[str, Any]]:
        \"\"\"Generate SCRIPTED (non-parameterized) ES|QL queries

        These are fully tested queries with hard-coded values.
        Address pain points: {', '.join(config['pain_points'])}
        \"\"\"
        queries = []

        # Query 1: [Simple query addressing first pain point]
        queries.append({{
            "query_type": "scripted",
            "name": "query_name_here",
            "description": "What it demonstrates",
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

        # Add 4-6 more scripted queries...

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        \"\"\"Generate PARAMETERIZED versions for Agent Builder

        Based on validated scripted queries above.
        Use ?parameter syntax. NO LIKE/RLIKE operators!
        \"\"\"
        param_queries = []

        # Parameterized version of Query 1
        param_queries.append({{
            "query_type": "parameterized",
            "name": "parameterized_query_name",
            "description": "Configurable version of X",
            "esql": \"\"\"
                FROM index_name
                | WHERE field == ?value
                | WHERE @timestamp >= ?start_date
                | STATS aggregation
                | SORT field DESC
                | LIMIT ?limit
            \"\"\",
            "parameters": {{
                "value": {{
                    "type": "keyword",
                    "description": "Filter value",
                    "default": "original_value",
                    "required": True
                }},
                "start_date": {{
                    "type": "date",
                    "description": "Start of date range",
                    "default": "NOW() - 7 days",
                    "required": True
                }},
                "limit": {{
                    "type": "integer",
                    "description": "Max results",
                    "default": "10",
                    "required": False
                }}
            }},
            "base_query": "query_name_here",
            "agent_builder_ready": True
        }})

        # Add parameterized versions for 2-3 more scripted queries...

        return param_queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        \"\"\"Generate RAG queries (MATCH → RERANK → COMPLETION)

        For semantic search + AI-powered answers via Agent Builder.
        CRITICAL: Use INLINE STATS not STATS!
        \"\"\"
        rag_queries = []

        # Identify text fields from datasets
        # Example: description, content, feedback, notes, etc.

        rag_queries.append({{
            "query_type": "rag",
            "name": "semantic_search_rag",
            "description": "Ask questions about [data type]",
            "esql": \"\"\"
                FROM index_name METADATA _score
                | WHERE MATCH(text_field1, ?user_question)
                    OR MATCH(text_field2, ?user_question)
                | WHERE @timestamp >= NOW() - 120 days
                | SORT _score DESC
                | LIMIT 100
                | RERANK ?user_question
                    ON text_field1, text_field2, text_field3
                    WITH {{"inference_id": "rerank_endpoint"}}
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
                    WITH {{"inference_id": "completion_endpoint"}}
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
            "time_boundary": "120 days",
            "agent_builder_tool": {{
                "tool_name": "search_dataset_name",
                "tool_description": "Search and analyze [data type] with AI-powered answers"
            }}
        }})

        # Optionally add 1-2 more RAG queries for different use cases...

        return rag_queries

    def get_query_progression(self) -> List[str]:
        \"\"\"Order to present SCRIPTED queries (for demos)\"\"\"
        return [
            # List scripted query names in presentation order
        ]
```

**IMPORTANT GUIDELINES:**

1. **Scripted Queries** (5-7 queries):
   - Start simple, progress to complex
   - Hard-coded dates, values, filters
   - Each solves a specific pain point
   - All fully tested and validated

2. **Parameterized Queries** (3-5 queries):
   - Select 3-5 most useful scripted queries
   - Replace hard-coded values with ?parameters
   - Provide meaningful parameter descriptions
   - Link to base_query for trust/validation
   - NEVER use LIKE or RLIKE (not supported!)

3. **RAG Queries** (1-3 queries):
   - Identify 3-5 text fields for MATCH
   - Select 2-4 most important for RERANK
   - Use INLINE STATS to aggregate context
   - Include all relevant fields in context
   - Set appropriate time boundary (30/90/120 days)

4. **Field Selection for RAG:**
   - Text fields: description, content, message, feedback, notes, comments
   - Context: Include IDs, status, categories, timestamps
   - Rerank: Prioritize primary content fields

5. **Multi-Index Support:**
   - Can query multiple indices: FROM index1,index2,index-*
   - Useful for RAG across related datasets

Generate the COMPLETE implementation with ALL THREE methods populated:"""

        if self.llm_client:
            code = self._call_llm(prompt)
        else:
            code = self._generate_mock_query_module(config)

        # Validate syntax before saving
        self._validate_python_syntax(code, 'query_generator.py')

        # Save the module
        module_file = module_path / 'query_generator.py'
        module_file.write_text(code)

    def _generate_guide_module(self, config: Dict[str, Any], module_path: Path):
        """Generate the demo guide module

        Uses fixed template since structure is always the same - only content varies.
        Content is dynamically generated from config/datasets/queries at runtime.
        """
        company_class = config['company_name'].replace(' ', '')

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
        # Extract pain points
        pain_points = ', '.join(self.config.pain_points[:2]) if self.config.pain_points else 'operational challenges'

        # Extract query names
        query_names = [q.get('name', f'Query {{i+1}}') for i, q in enumerate(self.queries[:5])]
        query_list = '\\n'.join([f'{{i+1}}. {{name}}' for i, name in enumerate(query_names)])

        return f\"\"\"# Demo Guide: {{self.config.company_name}} - {{self.config.department}}

## Overview
**Industry:** {{self.config.industry}}
**Focus Areas:** {{pain_points}}

## Demo Flow
1. **Introduction** - Establish context around their key challenges
2. **Data Exploration** - Show {{len(self.queries)}} targeted queries addressing pain points
3. **Business Impact** - Highlight speed, accuracy, and insights gained

## Key Queries
{{query_list}}

## Value Proposition
- **Speed:** Insights in seconds vs hours/days
- **Scalability:** Handles growing data volumes
- **Self-Service:** Empowers teams with intuitive query language

## Closing Points
- ES|QL provides SQL-like simplicity with Elasticsearch power
- Queries run directly on indexed data (millisecond response times)
- Most teams productive within days, not weeks
\"\"\"

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

Company: {config['company_name']}
Department: {config['department']}
Industry: {config['industry']}
Pain Points: {', '.join(config['pain_points'])}
Use Cases: {', '.join(config['use_cases'])}
Scale: {config['scale']}
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
- Scale mentioned ({config['scale']}) is for REALISM only, don't generate that many!

Template:
```python
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

class {config['company_name'].replace(' ', '')}DataGenerator(DataGeneratorModule):
    \"\"\"Data generator for {config['company_name']} - {config['department']}\"\"\"

    @staticmethod
    def safe_choice(choices, size=None, weights=None, replace=True):
        \"\"\"Safer alternative to np.random.choice with automatic probability normalization.\"\"\"
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
                                             query_strategy: Dict):
        """Generate query module using pre-planned query strategy

        Args:
            config: Demo configuration
            module_path: Path to module directory
            query_strategy: Complete query strategy with planned queries
        """
        prompt = f"""Generate a Python module that implements QueryGeneratorModule for this customer:

Company: {config['company_name']}
Department: {config['department']}
Pain Points: {', '.join(config['pain_points'])}
Use Cases: {', '.join(config['use_cases'])}

**Pre-Planned Query Strategy:**
{json.dumps(query_strategy, indent=2)}

CRITICAL - IMPLEMENT THE QUERIES FROM THE STRATEGY ABOVE.

The module should:
1. Implement QueryGeneratorModule base class
2. Generate the EXACT queries from the strategy with proper ES|QL syntax
3. Use field names that MATCH the generated data
4. Include query descriptions that explain the business value
5. Return queries in the order that builds a compelling narrative

IMPORTANT - ES|QL SYNTAX:
- For lookup joins: "FROM timeseries | LOOKUP JOIN reference_lookup ON key"
- Append "_lookup" to reference dataset names in LOOKUP JOIN
- Use @timestamp not timestamp for indexed data
- DATE_EXTRACT syntax: DATE_EXTRACT("month", @timestamp)
- Include proper error handling for edge cases

CRITICAL - ESCAPING ES|QL QUERIES IN PYTHON:
- ES|QL queries with JSON parameters use curly braces: MATCH(field, "term", {{"boost": 0.75}})
- ALWAYS use double curly braces {{{{ }}}} to escape JSON in queries when using f-strings
- OR use regular strings with .format() instead of f-strings for queries
- Example CORRECT: query = f\"\"\"FROM index | WHERE MATCH(field, "term", {{"boost": 1.5}})\"\"\"
- Example WRONG: query = f\"\"\"FROM index | WHERE MATCH(field, "term", {"boost": 1.5})\"\"\"

Template:
```python
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class {config['company_name'].replace(' ', '')}QueryGenerator(QueryGeneratorModule):
    \"\"\"Query generator for {config['company_name']} - {config['department']}\"\"\"

    # DO NOT define __init__ - inherited from base class provides:
    # self.config, self.datasets

    def generate_queries(self) -> List[Dict[str, Any]]:
        \"\"\"Generate ES|QL queries from pre-planned strategy\"\"\"

        queries = []

        # Implement each query from the strategy above
        # Make sure to use EXACT field names that exist in the datasets

        return queries

    def get_query_progression(self) -> List[str]:
        \"\"\"Define the order to present queries for maximum impact\"\"\"
        return [
            # Query names in presentation order from strategy
        ]
```

Generate the complete implementation with ALL queries from the strategy:"""

        if self.llm_client:
            code = self._call_llm(prompt)
        else:
            code = self._generate_mock_query_module(config)

        # Validate syntax before saving
        self._validate_python_syntax(code, 'query_generator.py')

        # Save the module
        module_file = module_path / 'query_generator.py'
        module_file.write_text(code)
        logger.info("Generated query_generator.py with strategy")

    def _generate_config_file(self, config: Dict[str, Any], module_path: Path):
        """Generate module configuration file"""
        config_data = {
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
        return """
### ES|QL Commands for RAG Queries

**MATCH (Semantic Search):**
```
WHERE MATCH(field, "query", {"boost": 0.75})
```

**RERANK (ML Relevance):**
```
| RERANK query_text ON field1, field2 WITH {"inference_id": "rerank_endpoint"}
```

**INLINE STATS (Preserve Fields):**
```
| INLINE STATS context = MV_CONCAT(field, "\\n")
```

**COMPLETION (LLM Generation):**
```
| COMPLETION answer = prompt WITH {"inference_id": "completion_endpoint"}
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
        if hasattr(self.llm_client, 'messages'):  # Anthropic
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=8000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            code = response.content[0].text
        elif hasattr(self.llm_client, 'chat'):  # OpenAI
            response = self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=8000
            )
            code = response.choices[0].message.content
        else:
            return ""

        # Extract Python code
        if "```python" in code:
            code = code.split("```python")[1].split("```")[0]

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
                df.to_csv(csv_path, index=False)
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
