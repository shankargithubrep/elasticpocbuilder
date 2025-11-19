# Template Modules Quick Reference

Fast lookup for template functions and their purposes.

## Query Generator Templates (`query_generator.py`)

### Main Prompt Functions

#### `get_scripted_queries_prompt(config, esql_docs)`
Generate fully tested, non-parameterized ES|QL queries.
- **Returns**: LLM prompt (~5K tokens)
- **Includes**: Scripted query examples, anti-patterns, tool metadata instructions
- **Use case**: Generate 5-7 queries addressing specific pain points

#### `get_parameterized_queries_prompt(config, esql_docs)`
Generate Agent Builder tool queries with ?parameter syntax.
- **Returns**: LLM prompt (~4K tokens)
- **Includes**: Smart parameter selection rules, @timestamp warnings
- **Use case**: Generate 3-5 configurable queries (NOT @timestamp filters!)

#### `get_rag_queries_prompt(config, esql_docs, rerank_endpoint, completion_endpoint)`
Generate semantic search + LLM completion queries.
- **Returns**: LLM prompt (~6K tokens)
- **Includes**: MATCH/RERANK/COMPLETION pipeline, relevance tuning
- **Use case**: Generate 1-3 RAG queries with AI answers

### Assembly Functions

#### `get_query_module_wrapper(config, scripted_code, parameterized_code, rag_code)`
Combine three method implementations into complete QueryGeneratorModule.
- **Returns**: Full Python module code
- **Handles**: Proper indentation, class definition, docstrings

### Private Helpers

#### `_get_tool_metadata_instructions(config)`
Consistent tool metadata format for all queries.
- **Returns**: Instructions string (embedded in prompts)
- **Includes**: tool_id rules, description guidelines, tag examples

## Agent Metadata Templates (`agent_metadata.py`)

### Prompt Functions

#### `get_agent_instructions_prompt(config, query_descriptions, datasets_info)`
Create professional agent role and capability instructions.
- **Returns**: LLM prompt (~1.5K tokens)
- **Output**: 150-250 words of professional instructions
- **Use case**: Define agent personality and scope

### Structure Functions

#### `get_agent_metadata_template(config, agent_id, avatar_symbol, avatar_color, instructions)`
Build complete agent metadata JSON structure.
- **Returns**: Dict ready for JSON serialization
- **Fields**: id, name, description, labels, avatar, configuration
- **Use case**: Create agent_metadata.json for Agent Builder API

### Helper Functions

#### `generate_agent_id(company_name, department)`
Create normalized unique agent identifier.
- **Format**: `{company}_{dept}_agent` (lowercase, underscores)
- **Use case**: Consistent ID generation

#### `generate_avatar_symbol(company_name)`
Generate 2-character avatar symbol from initials.
- **Returns**: `"CA"` from "Cybersecurity Analytics" (or first 2 chars)
- **Use case**: Avatar display

#### `get_agent_avatar_color_by_type(demo_type)`
Select avatar color based on demo type.
- **Returns**: `"#3B82F6"` (blue) for analytics, `"#10B981"` (green) for search
- **Use case**: Visual differentiation

### Fallback Functions

#### `get_fallback_agent_instructions(config)`
Default instructions when LLM unavailable.
- **Returns**: Generic but contextual instructions
- **Use case**: Graceful degradation when LLM fails

## Guide Generator Templates (`guide_generator.py`)

### Prompt Functions

#### `get_demo_guide_prompt(config, datasets_info, queries_info)`
Create comprehensive demo script with multiple sections.
- **Returns**: LLM prompt (~14K tokens)
- **Includes**: Complete template structure, 4-part demo flow
- **Use case**: Generate full internal demo documentation

### Module Functions

#### `get_demo_guide_module_template(config, guide_content)`
Create DemoGuideModule Python class.
- **Returns**: Full module code
- **Methods**: generate_guide(), get_talk_track(), get_objection_handling()
- **Use case**: Create demo_guide.py with markdown content

### Fallback Functions

#### `get_fallback_demo_guide(config, query_strategy, data_profile)`
Basic guide when LLM fails.
- **Returns**: Minimal markdown guide
- **Use case**: Safe default when LLM unavailable

## Data Generator Templates (`data_generator.py`)

(Already extracted, included for completeness)

#### `get_analytics_data_generator_template(config)`
Template for analytics-focused data generation.
- **Returns**: Partial Python module code
- **Includes**: Size preferences (small/medium/large)

#### `get_search_data_generator_template(config)`
Template for search/RAG data generation.
- **Returns**: Partial Python module code
- **Includes**: semantic_text field placeholders

#### `get_simple_data_generator_template(config)`
Minimal fallback template.
- **Returns**: Simple working module
- **Use case**: When LLM unavailable

## Common Usage Patterns

### 1. Query Generation (3-call approach)

```python
from src.framework.generation.templates.query_generator import (
    get_scripted_queries_prompt,
    get_parameterized_queries_prompt,
    get_rag_queries_prompt,
    get_query_module_wrapper
)

esql_docs = read_esql_docs()

# Call 1
scripted_prompt = get_scripted_queries_prompt(config, esql_docs)
scripted_code = llm_client.generate(scripted_prompt)

# Call 2
parameterized_prompt = get_parameterized_queries_prompt(config, esql_docs)
parameterized_code = llm_client.generate(parameterized_prompt)

# Call 3
rag_prompt = get_rag_queries_prompt(config, esql_docs, rerank_endpoint, completion_endpoint)
rag_code = llm_client.generate(rag_prompt)

# Combine
full_module = get_query_module_wrapper(config, scripted_code, parameterized_code, rag_code)
```

### 2. Agent Metadata Generation

```python
from src.framework.generation.templates.agent_metadata import (
    generate_agent_id,
    generate_avatar_symbol,
    get_agent_avatar_color_by_type,
    get_agent_instructions_prompt,
    get_agent_metadata_template
)

agent_id = generate_agent_id(config['company_name'], config['department'])
avatar_symbol = generate_avatar_symbol(config['company_name'])
avatar_color = get_agent_avatar_color_by_type(config.get('demo_type', 'analytics'))

instructions_prompt = get_agent_instructions_prompt(config, queries, datasets)
instructions = llm_client.generate(instructions_prompt)

metadata = get_agent_metadata_template(config, agent_id, avatar_symbol, avatar_color, instructions)
```

### 3. Demo Guide Generation

```python
from src.framework.generation.templates.guide_generator import (
    get_demo_guide_prompt,
    get_demo_guide_module_template
)

guide_prompt = get_demo_guide_prompt(config, datasets_info, queries_info)
guide_content = llm_client.generate(guide_prompt)

module_code = get_demo_guide_module_template(config, guide_content)
```

## Key Design Decisions

1. **Functions over Classes**: Templates are stateless functions for simplicity
2. **Config Dict Pattern**: All functions accept config dict for flexibility
3. **F-strings with Placeholders**: LLM prompts preserve all context dynamically
4. **Fallback Functions**: Every major path has graceful degradation
5. **Embedded Instructions**: Tool metadata rules stay in prompts (not separate docs)

## Critical Warnings

These warnings are embedded in prompts - DO NOT REMOVE:

### Query Generation
- **Integer Division**: Always use TO_DOUBLE() for decimal division
- **NULL Handling**: Add `OR field IS NULL` to negative filters
- **@timestamp**: NEVER parameterize @timestamp (agent handles it)
- **INLINE STATS**: Use in RAG, not STATS (preserves fields)

### Agent Metadata
- **tool_id Format**: Lowercase, underscores, max 50 chars
- **Avatar Colors**: Blue (#3B82F6) analytics, Green (#10B981) search

### Demo Guide
- **Lookup Mode**: All joined indices need "index.mode": "lookup"
- **Index Names**: No suffix convention - use exact names
- **Query Progression**: Start simple, add complexity gradually

## Testing Templates

```bash
# Verify syntax
python -m py_compile src/framework/generation/templates/*.py

# Test with mock config
python -c "
from src.framework.generation.templates.query_generator import get_scripted_queries_prompt
config = {'company_name': 'Test Co', 'department': 'Sales', 'pain_points': ['slow'], 'use_cases': []}
prompt = get_scripted_queries_prompt(config, 'test docs')
print(f'Prompt length: {len(prompt)}')
"
```

## Where These Are Used

In `module_generator.py`:
- `_generate_scripted_queries()` line 854
- `_generate_parameterized_queries()` line 979
- `_generate_rag_queries()` line 1161
- `_generate_demo_guide_content()` line 2473
- `_generate_agent_instructions()` line 2877
- `_generate_agent_metadata()` line 2358

## Related Files

- **module_generator.py**: Main entry point, orchestrates template usage
- **base.py**: Abstract base classes (DataGeneratorModule, QueryGeneratorModule, DemoGuideModule)
- **esql_strict_rules.py**: Centralized ES|QL rules (referenced in queries)
- **query_strategy_generator.py**: Query planning (provides context for guides)

## Version Control

All templates:
- Are checked into Git
- Can be edited and versioned independently
- Maintain backwards compatibility
- Have clear docstrings for changes

## Performance Notes

Total token usage per demo (approximate):
- Scripted queries: 5K tokens
- Parameterized queries: 4K tokens
- RAG queries: 6K tokens
- Demo guide: 14K tokens
- Agent instructions: 1.5K tokens
- **Total: ~30.5K tokens** (vs 40-50K if doing everything in one call)
