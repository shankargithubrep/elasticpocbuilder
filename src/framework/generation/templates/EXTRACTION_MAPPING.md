# Template Extraction Mapping

Detailed line-by-line mapping of what was extracted from `module_generator.py` to template files.

## Query Generator Extraction (`query_generator.py`)

### 1. Scripted Queries Template
**Source**: `module_generator.py` lines 854-977
**Destination**: `query_generator.py` lines 11-129
**Function**: `get_scripted_queries_prompt(config, esql_docs)`

**Content Map**:
- Lines 860-875: Tool metadata instruction setup and customer context
- Lines 877-898: Task description and requirements
- Lines 899-922: Method template with structure example
- Lines 924-968: Critical anti-patterns (integer division, NULL handling)
- Line 969: Generation instruction

**Extracted Exactly**:
- Tool metadata prompt structure
- Template python code formatting
- Anti-pattern code examples
- Critical warnings preserved verbatim

### 2. Parameterized Queries Template
**Source**: `module_generator.py` lines 979-1159
**Destination**: `query_generator.py` lines 132-307
**Function**: `get_parameterized_queries_prompt(config, esql_docs)`

**Content Map**:
- Lines 986-1000: Tool metadata instruction setup and customer context
- Lines 1001-1040: Task, requirements, and smart parameter selection rules
- Lines 1042-1089: Method template with parameter definitions
- Lines 1091-1149: Critical anti-patterns (@timestamp, integer division, NULL handling)
- Line 1151: Generation instruction

**Extracted Exactly**:
- Parameter selection rules (CREATE vs AVOID)
- Business date field examples
- @timestamp warning (most critical!)
- Parameter definition structure
- All anti-pattern documentation

### 3. RAG Queries Template
**Source**: `module_generator.py` lines 1161-1297
**Destination**: `query_generator.py` lines 310-441
**Function**: `get_rag_queries_prompt(config, esql_docs, rerank_endpoint, completion_endpoint)`

**Content Map**:
- Lines 1167-1177: Tool metadata instruction setup, company slugs, endpoints
- Lines 1178-1209: Task description and RAG architecture
- Lines 1210-1278: Method template with complex example
- Lines 1280-1288: Important notes on field identification and aggregation
- Line 1289: Generation instruction

**Extracted Exactly**:
- RAG pipeline explanation (MATCH -> RERANK -> INLINE STATS -> COMPLETION)
- Relevance tuning with boost and fuzziness
- INLINE STATS vs STATS critical distinction
- Example query with proper escaping
- Field identification requirements

### 4. Tool Metadata Instructions (Private Helper)
**Source**: `module_generator.py` lines 800-852 (embedded in `_get_tool_metadata_instructions()`)
**Destination**: `query_generator.py` lines 444-499
**Function**: `_get_tool_metadata_instructions(config)`

**Content Map**:
- Lines 811-828: tool_id format and validation
- Lines 829-834: description guidelines with examples
- Lines 835-836: tags guidelines
- Lines 839-851: complete query example with tool_metadata

**Extracted Exactly**:
- All validation rules for tool identifiers
- Description guidelines with good/bad examples
- Tag categorization rules
- Example structure

### 5. Query Module Wrapper
**Source**: `module_generator.py` lines 1299-1351
**Destination**: `query_generator.py` lines 502-555
**Function**: `get_query_module_wrapper(config, scripted_code, parameterized_code, rag_code)`

**Content Map**:
- Lines 1311-1322: Indentation logic for method assembly
- Lines 1325-1349: Complete module structure with all three methods
- Lines 1344-1348: get_query_progression() method

**Extracted Exactly**:
- Indentation logic to convert 0-indented methods to class methods (4-space indent)
- Complete module boilerplate
- All three methods properly assembled
- Class docstring structure

## Agent Metadata Extraction (`agent_metadata.py`)

### 1. Agent Instructions Prompt
**Source**: `module_generator.py` lines 2877-2923
**Destination**: `agent_metadata.py` lines 11-55
**Function**: `get_agent_instructions_prompt(config, query_descriptions, datasets_info)`

**Content Map**:
- Lines 2895-2896: Context building from query and dataset lists
- Lines 2898-2923: Full prompt generation logic

**Extracted Exactly**:
- Query context formatting (first 10 queries)
- Dataset context formatting
- Task requirements (150-250 words, professional, specific)
- All customer context variables

### 2. Agent Metadata Structure
**Source**: `module_generator.py` lines 2370-2455
**Destination**: `agent_metadata.py` lines 58-99
**Function**: `get_agent_metadata_template(config, agent_id, avatar_symbol, avatar_color, instructions)`

**Content Map**:
- Lines 2370-2387: agent_id, avatar_symbol, avatar_color generation
- Lines 2438-2455: Complete metadata structure

**Extracted Exactly**:
- All metadata fields (id, name, description, labels, avatar_*, configuration)
- Label assembly logic
- Instructions embedding

### 3. Fallback Instructions
**Source**: `module_generator.py` lines 2882-2892 and 2935-2945
**Destination**: `agent_metadata.py` lines 102-128
**Function**: `get_fallback_agent_instructions(config)`

**Content Map**:
- Lines 2882-2892: LLM unavailable fallback
- Lines 2935-2945: Exception handling fallback

**Extracted Exactly**:
- Both fallback versions (one simpler, one more detailed)
- Pain points and use cases list building
- Generic but contextual messaging

### 4. Avatar Color by Type
**Source**: `module_generator.py` lines 2384-2387
**Destination**: `agent_metadata.py` lines 131-143
**Function**: `get_agent_avatar_color_by_type(demo_type)`

**Extracted Exactly**:
- Color selection logic
- Demo type routing (search vs analytics)

### 5. Agent ID Generation
**Source**: `module_generator.py` lines 2370-2373
**Destination**: `agent_metadata.py` lines 146-158
**Function**: `generate_agent_id(company_name, department)`

**Extracted Exactly**:
- Slug generation from company/department
- underscore joining
- Character limit enforcement

### 6. Avatar Symbol Generation
**Source**: `module_generator.py` lines 2376-2382
**Destination**: `agent_metadata.py` lines 161-174
**Function**: `generate_avatar_symbol(company_name)`

**Extracted Exactly**:
- Word splitting logic
- Initial extraction
- Single word fallback
- Case conversion

## Guide Generator Extraction (`guide_generator.py`)

### 1. Demo Guide Prompt
**Source**: `module_generator.py` lines 2473-2793
**Destination**: `guide_generator.py` lines 11-303
**Function**: `get_demo_guide_prompt(config, datasets_info, queries_info)`

**Content Map**:
- Lines 2520-2736: Complete template_guide structure (334 lines!)
- Lines 2738-2793: Prompt generation with context and task requirements

**Template Sections** (from lines 2520-2736):
- Lines 2520-2537: Title and demo overview
- Lines 2540-2552: Dataset architecture and setup
- Lines 2555-2570: Part 1 - AI Agent Teaser
- Lines 2573-2647: Part 2 - ES|QL Query Building (4 progressive queries)
- Lines 2651-2667: Part 3 - Agent & Tool Creation
- Lines 2671-2682: Part 4 - Q&A Session
- Lines 2686-2704: Talking points (ES|QL, Agent Builder, Business Value)
- Lines 2708-2721: Troubleshooting section
- Lines 2725-2736: Closing script

**Task Requirements** (from lines 2758-2791):
- Real content (not placeholders)
- Dataset architecture specifics
- Setup instructions
- Agent teaser examples
- Progressive query examples
- Tool creation summary
- Diverse Q&A questions
- Standard talking points

**Critical Rules** (from lines 2783-2788):
- No code fences around entire guide
- Proper markdown syntax
- Emoji headers preserved
- Code blocks for queries (```esql```)
- Real internal demo script feeling

**Extracted Exactly**:
- Complete 334-line template structure with all sections
- All placeholder names for LLM to fill
- All talking points
- Troubleshooting guidance
- Closing script

### 2. Demo Guide Module Template
**Source**: `module_generator.py` lines 1407-1435
**Destination**: `guide_generator.py` lines 306-349
**Function**: `get_demo_guide_module_template(config, guide_content)`

**Content Map**:
- Lines 1399-1401: Company class name sanitization
- Lines 1407-1435: Complete module boilerplate

**Extracted Exactly**:
- Import statements
- Class definition with docstring
- __init__ method signature
- generate_guide() method returning guide_content
- get_talk_track() stub
- get_objection_handling() with 3 standard objections

### 3. Fallback Demo Guide
**Source**: `module_generator.py` lines 2820-2875
**Destination**: `guide_generator.py` lines 352-419
**Function**: `get_fallback_demo_guide(config, query_strategy, data_profile)`

**Content Map**:
- Lines 2823-2829: Dataset list extraction
- Lines 2831: Query list building
- Lines 2833-2875: Fallback guide structure

**Sections** (minimal but functional):
- Overview with industry and focus areas
- Demo flow (same 4 parts as full guide)
- Dataset list (actual data)
- Key queries list (actual queries)
- Value proposition
- Closing points

**Extracted Exactly**:
- Actual data extraction from query_strategy
- Fallback section structure
- Safe defaults when LLM unavailable

## Data Generator Extraction (Already Complete)

### Functions Previously Extracted
**Source**: Various lines in module_generator.py (data module generation)
**Destination**: `data_generator.py`

**Functions**:
1. `get_analytics_data_generator_template(config)` - Analytics mode template
2. `get_search_data_generator_template(config)` - Search/RAG mode template
3. `get_simple_data_generator_template(config)` - Fallback template

These were previously extracted and are complete.

## Summary Statistics

| Source | Destination | Lines Extracted | Key Functions |
|--------|-------------|-----------------|----------------|
| module_generator.py (854-1390) | query_generator.py | 556 lines | 5 functions |
| module_generator.py (2358-2945) | agent_metadata.py | 175 lines | 6 functions |
| module_generator.py (1392-2875) | guide_generator.py | 420 lines | 3 functions |
| **Total** | | **1,151 lines** | **14 functions** |

## Verification Checklist

All extracted templates have been verified for:

- [x] Syntax correctness (`py_compile` pass)
- [x] F-string placeholder preservation
- [x] Exact prompt wording maintained
- [x] Anti-pattern guidance retained
- [x] Example code formatting preserved
- [x] Docstring quality
- [x] Type hints completeness
- [x] Parameter naming consistency

## Integration Checklist

To complete integration, update `module_generator.py`:

- [ ] Add imports from template modules
- [ ] Replace `_generate_scripted_queries()` call to use `get_scripted_queries_prompt()`
- [ ] Replace `_generate_parameterized_queries()` call to use `get_parameterized_queries_prompt()`
- [ ] Replace `_generate_rag_queries()` call to use `get_rag_queries_prompt()`
- [ ] Replace `_generate_demo_guide_content()` call to use `get_demo_guide_prompt()`
- [ ] Replace `_generate_agent_instructions()` call to use `get_agent_instructions_prompt()`
- [ ] Replace `_generate_agent_metadata()` calls to use helper functions
- [ ] Remove inline prompt definitions from methods
- [ ] Run tests to verify equivalence
- [ ] Update method docstrings to reference templates

## Hotspot Locations (Most Changed)

If updating prompts, these functions are most critical:

1. **`get_scripted_queries_prompt()`** - Changes affect all demo query quality
2. **`get_rag_queries_prompt()`** - Changes affect semantic search capabilities
3. **`get_demo_guide_prompt()`** - Changes affect demo presentation
4. **`_get_tool_metadata_instructions()`** - Changes affect Agent Builder compatibility

Test these first when making prompt modifications.
