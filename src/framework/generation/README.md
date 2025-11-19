# Module Generation Framework

This directory contains the refactored, modular module generation system. The monolithic 3,428-line `module_generator.py` has been split into focused components for better maintainability.

## Architecture

```
generation/
├── module_generator.py          # Slim orchestrator (997 lines, was 3,428)
├── templates/                   # LLM prompt templates
│   ├── data_generator.py       # Data generation templates
│   ├── query_generator.py      # Query generation prompts
│   ├── guide_generator.py      # Demo guide templates
│   ├── agent_metadata.py       # Agent metadata templates
│   └── __init__.py
└── generators/                  # Utility functions
    ├── code_extractor.py       # Code extraction & validation
    ├── config_generator.py     # Config file generation
    ├── static_files.py         # Static file generation
    └── __init__.py
```

## Quick Start

```python
from src.framework.generation.module_generator import ModuleGenerator

# Create orchestrator
mg = ModuleGenerator(llm_client=your_llm_client)

# Generate a complete demo module
module_path = mg.generate_demo_module_with_strategy(
    config={
        'company_name': 'Acme Corp',
        'department': 'Sales',
        'industry': 'Technology',
        # ... more config
    },
    query_strategy={
        'queries': [...],
        # ... query strategy
    }
)

print(f"Demo module created at: {module_path}")
```

## Public API

### Main Generation Methods

#### 1. `generate_demo_module(config, query_plan=None)`

Generate a complete demo module with optional query plan.

**Parameters:**
- `config` (Dict): Customer context configuration
- `query_plan` (Dict, optional): Query plan from LightweightQueryPlanner

**Returns:** `str` - Path to generated module directory

**Use Case:** Original flow with optional query planning

---

#### 2. `generate_demo_module_with_strategy(config, query_strategy)`

Generate a complete demo module using pre-generated query strategy.

**Parameters:**
- `config` (Dict): Customer context configuration
- `query_strategy` (Dict): Pre-generated query strategy

**Returns:** `str` - Path to generated module directory

**Use Case:** Modern query-first workflow (recommended)

---

#### 3. `generate_data_and_infrastructure_only(config, query_strategy)`

Generate module infrastructure and data (Phase 1 of split workflow).

**Parameters:**
- `config` (Dict): Customer context configuration
- `query_strategy` (Dict): Query strategy for data requirements

**Returns:** `str` - Path to generated module directory

**Use Case:** Split workflow - generate data first, queries after indexing

---

#### 4. `generate_query_module_with_profile(module_path, config, query_strategy, data_profile=None)`

Generate query module using profiled data (Phase 2 of split workflow).

**Parameters:**
- `module_path` (str): Path to existing module directory
- `config` (Dict): Customer context configuration
- `query_strategy` (Dict): Query strategy
- `data_profile` (Dict, optional): Profiled data from Elasticsearch

**Returns:** `None` (modifies existing module)

**Use Case:** Split workflow - generate queries after data profiling

## Component Details

### Templates (`templates/`)

#### data_generator.py

Provides data generation templates for different demo types:

- `get_analytics_data_generator_template(config)` - Analytics mode template
- `get_search_data_generator_template(config)` - Search/RAG mode template
- `get_simple_data_generator_template(config)` - Minimal fallback template

**Example:**
```python
from src.framework.generation.templates import get_analytics_data_generator_template

template = get_analytics_data_generator_template({
    'company_name': 'Acme Corp',
    'department': 'Sales',
    'size_preference': 'medium'
})
```

#### query_generator.py

Provides query generation prompts:

- `get_scripted_queries_prompt(config, esql_docs, schema_context=None)` - Scripted query prompt
- `get_parameterized_queries_prompt(config, esql_docs, schema_context=None)` - Parameterized query prompt
- `get_rag_queries_prompt(config, esql_docs, inference_endpoints, schema_context=None)` - RAG query prompt
- `get_query_module_wrapper(config, scripted_method, parameterized_method, rag_method)` - Module wrapper

**Example:**
```python
from src.framework.generation.templates import get_scripted_queries_prompt

prompt = get_scripted_queries_prompt(
    config={'company_name': 'Acme', ...},
    esql_docs="ES|QL reference...",
    schema_context="Available fields: ..."
)
```

#### guide_generator.py

Provides demo guide templates:

- `get_demo_guide_prompt(config, query_descriptions)` - LLM prompt for guide content
- `get_demo_guide_module_template(company_class, company_name, department, guide_content)` - Module wrapper
- `get_fallback_demo_guide(config)` - Fallback guide when LLM unavailable

#### agent_metadata.py

Provides agent metadata generation:

- `get_agent_instructions_prompt(config, query_descriptions, datasets_info)` - LLM prompt
- `get_agent_metadata_template(config, agent_instructions, query_descriptions, inference_endpoints)` - Metadata template
- `get_fallback_agent_instructions(config)` - Fallback instructions
- `generate_agent_id(company_name, department)` - Generate unique agent ID
- `generate_avatar_symbol(company_name)` - Generate avatar symbol
- `get_agent_avatar_color_by_type(demo_type)` - Get avatar color

### Generators (`generators/`)

#### code_extractor.py

Code extraction and validation utilities:

**Methods:**
- `CodeExtractor.extract_python_code(response)` - Extract Python from markdown
- `CodeExtractor.validate_python_syntax(code, module_name)` - Syntax validation
- `CodeExtractor.validate_query_module_methods(code)` - Method presence validation

**Example:**
```python
from src.framework.generation.generators import CodeExtractor

# Extract code from LLM response
response = "```python\ndef hello(): pass\n```"
code = CodeExtractor.extract_python_code(response)

# Validate syntax
CodeExtractor.validate_python_syntax(code, 'test.py')  # Raises if invalid
```

#### config_generator.py

Configuration file generation:

**Methods:**
- `ConfigGenerator.generate_config_file(config, module_path)` - Generate config.json

**Example:**
```python
from src.framework.generation.generators import ConfigGenerator
from pathlib import Path

ConfigGenerator.generate_config_file(
    config={'company_name': 'Acme', ...},
    module_path=Path('demos/acme_sales_20241118')
)
```

#### static_files.py

Static file generation for UI:

**Methods:**
- `StaticFileGenerator.generate_static_files(module_path)` - Generate all static files

**Example:**
```python
from src.framework.generation.generators import StaticFileGenerator
from pathlib import Path

# Generates CSV files, all_queries.json, demo_guide.md
StaticFileGenerator.generate_static_files(
    module_path=Path('demos/acme_sales_20241118')
)
```

## Internal Workflow

### Standard Demo Generation Flow

```
1. _create_module_directory(config)
   └─> Creates demos/company_dept_timestamp/

2. _generate_data_module_with_requirements(config, module_path, requirements)
   └─> Creates data_generator.py using templates

3. _generate_query_module_with_strategy(config, module_path, query_strategy)
   └─> Creates query_generator.py (JSON loader approach)

4. _generate_guide_module(config, module_path)
   └─> Creates demo_guide.py using templates

5. ConfigGenerator.generate_config_file(config, module_path)
   └─> Creates config.json

6. StaticFileGenerator.generate_static_files(module_path)
   └─> Creates data/*.csv, all_queries.json, demo_guide.md

7. _generate_agent_metadata(config, module_path)
   └─> Creates tool_metadata.json
```

### Split Workflow (Data First, Queries Later)

**Phase 1: Data & Infrastructure**
```python
module_path = mg.generate_data_and_infrastructure_only(config, query_strategy)
# → Creates module with data_generator.py, demo_guide.py, config.json
# → NO query_generator.py yet
```

**Phase 2: Index Data & Profile**
```python
# (External code indexes data and profiles it)
data_profile = index_and_profile_data(module_path)
```

**Phase 3: Generate Queries with Profile**
```python
mg.generate_query_module_with_profile(
    module_path=module_path,
    config=config,
    query_strategy=query_strategy,
    data_profile=data_profile
)
# → Creates query_generator.py using actual field values
# → Generates static files now that all modules complete
```

## Configuration Schema

### Demo Config

```python
config = {
    'company_name': str,              # Company name
    'department': str,                # Department
    'industry': str,                  # Industry
    'pain_points': List[str],         # Pain points
    'use_cases': List[str],           # Use cases
    'scale': str,                     # Scale description
    'metrics': List[str],             # Metrics to track
    'demo_type': str,                 # 'analytics' or 'search'
    'dataset_size_preference': str,   # 'small', 'medium', 'large'
}
```

### Query Strategy

```python
query_strategy = {
    'queries': [
        {
            'name': str,              # Query name
            'description': str,       # Query description
            'query_type': str,        # 'scripted', 'parameterized', 'rag'
            'esql': str,              # ES|QL query string
            'parameters': Dict,       # For parameterized queries
            'expected_insight': str,  # Expected insight
            'data_requirements': Dict # Required fields
        },
        # ... more queries
    ]
}
```

## Backward Compatibility

The new slim orchestrator is **100% backward compatible** with the original:

- ✅ All public method signatures preserved exactly
- ✅ Same return types and behaviors
- ✅ Same file outputs and structure
- ✅ Can be used as drop-in replacement

## Migration Guide

### Option 1: Use New Location (Recommended)

```python
# Old import (still works)
from src.framework.module_generator import ModuleGenerator

# New import (preferred)
from src.framework.generation.module_generator import ModuleGenerator
```

### Option 2: Import Components Directly

```python
# Use templates directly in your code
from src.framework.generation.templates import (
    get_analytics_data_generator_template,
    get_scripted_queries_prompt
)

# Use utilities directly
from src.framework.generation.generators import (
    CodeExtractor,
    ConfigGenerator
)
```

## Testing

Run tests for the generation framework:

```bash
# Test imports
python -c "from src.framework.generation.module_generator import ModuleGenerator; print('✓')"

# Test instantiation
python -c "from src.framework.generation.module_generator import ModuleGenerator; mg = ModuleGenerator(); print('✓')"

# Run integration tests
python -m pytest tests/test_integration.py -v -k module_generator
```

## Benefits of Refactoring

1. **71% Size Reduction**: 3,428 → 997 lines
2. **Better Maintainability**: Changes isolated to specific files
3. **Improved Testability**: Each component can be unit tested
4. **Enhanced Reusability**: Templates can be used elsewhere
5. **Clearer Separation**: Orchestration vs implementation
6. **Easier Debugging**: Smaller, focused files

## Future Improvements

- [ ] Add caching for frequently used templates
- [ ] Add template versioning for backward compatibility
- [ ] Add validation schemas for config and query_strategy
- [ ] Add metrics/telemetry for generation performance
- [ ] Add template marketplace for community contributions

## Related Documentation

- [REFACTORING_COMPARISON.md](/Users/jesse.miller/demo-builder/REFACTORING_COMPARISON.md) - Detailed comparison
- [REFACTORING_MAP.md](/Users/jesse.miller/demo-builder/REFACTORING_MAP.md) - Extraction mapping
- [MODULAR_ARCHITECTURE.md](/Users/jesse.miller/demo-builder/docs/MODULAR_ARCHITECTURE.md) - Architecture overview
