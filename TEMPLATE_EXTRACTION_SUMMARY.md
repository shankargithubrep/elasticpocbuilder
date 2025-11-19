# Template Extraction Summary

This document summarizes the template extraction from `src/framework/module_generator.py` into modular template files in `src/framework/generation/templates/`.

## Overview

The monolithic `module_generator.py` file (~3,900 lines) contained embedded template strings and prompt generation logic scattered throughout method implementations. These have been extracted into dedicated template modules for:

1. Improved maintainability
2. Easier prompt refinement
3. Better code organization
4. Reduced cognitive load

## Extracted Templates

### 1. Query Generator Templates (`src/framework/generation/templates/query_generator.py`)

Extracted the three main query generation prompt templates:

#### Functions Created:

1. **`get_scripted_queries_prompt(config, esql_docs)`**
   - Source: Lines 854-969 in module_generator.py
   - Purpose: Generates SCRIPTED (non-parameterized) ES|QL queries
   - Content:
     - Customer context and pain points
     - Tool metadata instructions (embedded)
     - Query template structure
     - Critical anti-patterns: integer division, NULL handling
   - Tokens: ~5000 for LLM

2. **`get_parameterized_queries_prompt(config, esql_docs)`**
   - Source: Lines 979-1151 in module_generator.py
   - Purpose: Generates PARAMETERIZED queries for Agent Builder tools
   - Content:
     - Smart parameter selection rules
     - Business date fields vs @timestamp (critical distinction)
     - Parameter definition structure
     - Anti-patterns: @timestamp parameterization, integer division
   - Tokens: ~4000 for LLM

3. **`get_rag_queries_prompt(config, esql_docs, rerank_endpoint, completion_endpoint)`**
   - Source: Lines 1161-1289 in module_generator.py
   - Purpose: Generates RAG queries with MATCH -> RERANK -> INLINE STATS -> COMPLETION pipeline
   - Content:
     - RAG architecture explanation
     - Relevance tuning with boost and fuzziness
     - INLINE STATS vs STATS critical distinction
     - Semantic search field identification
   - Tokens: ~6000 for LLM

4. **`_get_tool_metadata_instructions(config)`** (private helper)
   - Source: Lines 800-852 in module_generator.py
   - Purpose: Provides consistent tool metadata instructions
   - Content:
     - tool_id format and validation rules
     - Description guidelines with business focus
     - Tag categorization best practices
   - Used by all three query prompts

5. **`get_query_module_wrapper(config, scripted_code, parameterized_code, rag_code)`**
   - Source: Lines 1299-1351 in module_generator.py
   - Purpose: Combines three method implementations into complete module
   - Content:
     - Proper indentation handling
     - Class definition with docstrings
     - Method assembly logic

### 2. Agent Metadata Templates (`src/framework/generation/templates/agent_metadata.py`)

Extracted agent-related prompts and configuration generators:

#### Functions Created:

1. **`get_agent_instructions_prompt(config, query_descriptions, datasets_info)`**
   - Source: Lines 2877-2923 in module_generator.py
   - Purpose: Creates LLM prompt for professional agent instructions
   - Content:
     - Company context with pain points and use cases
     - Query capabilities list
     - Dataset information
     - Task requirements (150-250 words, professional tone)

2. **`get_agent_metadata_template(config, agent_id, avatar_symbol, avatar_color, instructions)`**
   - Source: Lines 2358-2471 in module_generator.py
   - Purpose: Creates complete agent metadata JSON structure
   - Content:
     - Agent ID and naming
     - Avatar color selection by demo type (#3B82F6 analytics, #10B981 search)
     - Labels for categorization
     - Configuration with instructions

3. **`get_fallback_agent_instructions(config)`**
   - Source: Lines 2882-2892 and 2935-2945 in module_generator.py
   - Purpose: Default instructions when LLM unavailable
   - Content:
     - Generic specialist introduction
     - Pain point-based focus areas
     - Use case capabilities
     - Friendly call to action

4. **`get_agent_avatar_color_by_type(demo_type)`**
   - Source: Lines 2384-2387 in module_generator.py
   - Purpose: Select avatar color based on demo type
   - Returns: Hex color (#3B82F6 for analytics, #10B981 for search)

5. **`generate_agent_id(company_name, department)`**
   - Source: Lines 2370-2373 in module_generator.py
   - Purpose: Create normalized agent ID
   - Format: lowercase, underscores, max 50 chars

6. **`generate_avatar_symbol(company_name)`**
   - Source: Lines 2376-2382 in module_generator.py
   - Purpose: Create 2-character avatar symbol from company initials

### 3. Guide Generator Templates (`src/framework/generation/templates/guide_generator.py`)

Extracted demo guide prompts and module templates:

#### Functions Created:

1. **`get_demo_guide_prompt(config, datasets_info, queries_info)`**
   - Source: Lines 2473-2793 in module_generator.py
   - Purpose: Creates comprehensive demo guide generation prompt
   - Content:
     - Complete demo guide template structure (shown to LLM as exemplar)
     - 4-part demo flow: teaser, query building, agent creation, Q&A
     - Progressive query examples: aggregation, EVAL, JOIN, complex
     - Talking points for ES|QL, Agent Builder, business value
     - Troubleshooting section
     - Dataset architecture and setup instructions
   - Tokens: ~16000 for LLM

2. **`get_demo_guide_module_template(config, guide_content)`**
   - Source: Lines 1392-1442 in module_generator.py
   - Purpose: Creates DemoGuideModule Python class
   - Content:
     - Class definition with docstrings
     - __init__ with config, datasets, queries, aha_moment
     - generate_guide() returning markdown content
     - get_talk_track() stub for customization
     - get_objection_handling() with standard objections

3. **`get_fallback_demo_guide(config, query_strategy, data_profile)`**
   - Source: Lines 2820-2875 in module_generator.py
   - Purpose: Basic guide when LLM fails
   - Content:
     - Minimal but functional structure
     - Uses actual dataset and query information
     - Includes demo flow and value propositions
     - Safe default when LLM unavailable

### 4. Data Generator Templates (Already Complete)

The file `src/framework/generation/templates/data_generator.py` was already extracted and contains:

- `get_analytics_data_generator_template(config)`
- `get_search_data_generator_template(config)`
- `get_simple_data_generator_template(config)`

## Key Design Patterns

### 1. Prompt Templates are Functions
- Take config and contextual parameters
- Return fully-formed f-strings with placeholders
- Include embedded instructions and examples
- Maintain exact formatting for LLM consistency

### 2. Tool Metadata Instructions
- Embedded in query generator prompts
- Ensures consistent tool_id, description, tags format
- Extracted to `_get_tool_metadata_instructions()` private helper
- Used across all three query types (scripted, parameterized, RAG)

### 3. Fallback Strategies
- Every major generation has fallback function
- Used when LLM unavailable or fails
- Provides reasonable defaults based on config
- Prevents cascading failures

### 4. Anti-Pattern Documentation
Each prompt includes critical anti-patterns with examples:

**Query Generators:**
- Integer division (wrap denominator in TO_DOUBLE())
- NULL handling with negative filters
- @timestamp parameterization (never do this)
- INLINE STATS vs STATS in RAG

## Integration with module_generator.py

The templates are used in `module_generator.py` via:

1. **Import statements** (to be added):
```python
from src.framework.generation.templates.query_generator import (
    get_scripted_queries_prompt,
    get_parameterized_queries_prompt,
    get_rag_queries_prompt,
    get_query_module_wrapper
)
from src.framework.generation.templates.agent_metadata import (
    get_agent_instructions_prompt,
    get_agent_metadata_template,
    get_fallback_agent_instructions,
    generate_agent_id,
    generate_avatar_symbol,
    get_agent_avatar_color_by_type
)
from src.framework.generation.templates.guide_generator import (
    get_demo_guide_prompt,
    get_demo_guide_module_template,
    get_fallback_demo_guide
)
```

2. **Method Refactoring** (to be done):
- `_generate_scripted_queries()` -> calls `get_scripted_queries_prompt()`
- `_generate_parameterized_queries()` -> calls `get_parameterized_queries_prompt()`
- `_generate_rag_queries()` -> calls `get_rag_queries_prompt()`
- `_generate_demo_guide_content()` -> calls `get_demo_guide_prompt()`
- `_generate_agent_instructions()` -> calls `get_agent_instructions_prompt()`
- `_generate_agent_metadata()` -> calls `get_agent_metadata_template()` and helpers

## File Statistics

### Source File
- **module_generator.py**: 3,920 lines (monolithic)
- Key sections extracted:
  - Query generation: lines 854-1390
  - Guide generation: lines 1392-2875
  - Agent metadata: lines 2358-2945

### Output Files
- **query_generator.py**: 556 lines
- **agent_metadata.py**: 175 lines
- **guide_generator.py**: 420 lines
- **Total extracted**: 1,151 lines (organized and reusable)

## Token Counts (for LLM calls)

Each template is optimized for token efficiency:

| Template | Max Tokens | Typical | Purpose |
|----------|-----------|---------|---------|
| Scripted Queries | 6,000 | 5,000 | Generate 5-7 ES|QL queries |
| Parameterized Queries | 5,000 | 4,000 | Generate 3-5 Agent tools |
| RAG Queries | 7,000 | 6,000 | Generate 1-3 semantic search pipelines |
| Demo Guide | 16,000 | 14,000 | Generate comprehensive guide |
| Agent Instructions | 2,000 | 1,500 | Generate 150-250 word instructions |

## Quality Assurance

All extracted templates have been:
- Verified to compile correctly with `py_compile`
- Tested for proper f-string formatting
- Checked for preserved exact prompting logic
- Organized with clear docstrings
- Structured with consistent parameter naming

## Next Steps

To complete the refactoring:

1. Update `module_generator.py` to import these templates
2. Replace inline prompt generation with template function calls
3. Update method signatures to use template functions
4. Run test suite to verify equivalence
5. Update documentation to reference template modules

## Maintenance Notes

When updating prompts:
1. Edit the appropriate template file
2. Test with mock LLM to verify output
3. Check that all placeholder variables are populated
4. Verify anti-pattern guidance is still accurate
5. Update docstrings if intent changes

All templates maintain the original quality standards and critical guidance from the monolithic file while improving organization and reusability.
