# Module Generator Refactoring Map

## Current State
- **File**: `src/framework/module_generator.py`
- **Size**: 3,368 lines
- **Status**: Monolithic, contains everything

## Target Structure

```
src/framework/generation/
├── __init__.py                 # Backward compatibility exports
├── module_generator.py         # Slim orchestrator (~500 lines)
├── templates/
│   ├── __init__.py
│   ├── data_generator.py       # ✅ CREATED (needs content)
│   ├── query_generator.py      # 🚧 TODO
│   ├── guide_generator.py      # 🚧 TODO
│   └── agent_metadata.py       # 🚧 TODO
├── generators/
│   ├── __init__.py             # ✅ CREATED
│   ├── static_files.py         # ✅ CREATED (needs implementation)
│   ├── config_generator.py     # ✅ CREATED (needs implementation)
│   └── code_extractor.py       # ✅ CREATED (needs implementation)
└── deprecated/
    ├── __init__.py
    └── legacy_generator.py      # 🚧 TODO
```

## Methods to Move

### From ModuleGenerator class to respective modules:

#### → templates/data_generator.py
- Lines 296-371: `_generate_data_module()` template content
- Lines 1524-1845: `_generate_data_module_with_requirements()` search mode template
- Lines 3095-3145: Simple data generator template

#### → templates/query_generator.py
- Lines 854-978: `_generate_scripted_queries()`
- Lines 979-1219: `_generate_parameterized_queries()`
- Lines 1220-1328: `_generate_rag_queries()`
- Lines 463-796: Query generation with schema methods

#### → templates/guide_generator.py
- Lines 2550-2850: Demo guide template
- Lines 3181-3215: Simple guide template

#### → templates/agent_metadata.py
- Lines 2851-3050: Agent instructions generation
- Lines 798-852: Tool metadata instructions

#### → generators/static_files.py
- Lines 3343-3428: `_generate_static_files()` ✅ EXTRACTED
- Lines 3274-3296: `_remove_timestamp_parameters()` ✅ EXTRACTED
- Related helper methods for JSON generation

#### → generators/config_generator.py
- Lines 2337-2356: `_generate_config_file()` ✅ EXTRACTED

#### → generators/code_extractor.py
- Lines 3084-3088: `_call_llm()` code extraction logic ✅ EXTRACTED as `extract_python_code()`
- Lines 3090-3106: `_validate_python_syntax()` ✅ EXTRACTED
- Lines 3108-3146: `_validate_query_module_methods()` ✅ EXTRACTED

#### → deprecated/legacy_generator.py
- Lines 65-94: `generate_demo_module()` without query_plan (DEPRECATED)
- Lines 296-371: `_generate_data_module()` (old approach)
- Lines 372-461: `_generate_query_module()` (3-call approach)
- Lines 2550-2850: `_generate_guide_module()` (old approach)

## Main ModuleGenerator (Slim Version)

The new slim `module_generator.py` will only contain:
- `__init__()` method
- Main orchestration methods:
  - `generate_demo_module_with_strategy()` (ACTIVE)
  - `generate_data_and_infrastructure_only()` (ACTIVE)
  - `generate_query_module_with_profile()` (ACTIVE)
- Helper coordination methods
- Imports from submodules

## Implementation Plan

### Phase 1: Extract Templates (In Progress)
1. ✅ Create directory structure
2. ✅ Create template module stubs
3. 🚧 Extract data generator templates
4. 🚧 Extract query generator templates
5. 🚧 Extract guide generator templates
6. 🚧 Extract agent metadata templates

### Phase 2: Extract Utilities
1. Move code extraction utilities
2. Move static file generation
3. Move config generation
4. Move validation methods

### Phase 3: Create Slim Orchestrator
1. Create new module_generator.py importing from submodules
2. Keep only orchestration logic
3. Delegate all template/utility work to submodules

### Phase 4: Move Deprecated Code
1. Move old generation methods to deprecated/
2. Mark clearly as deprecated
3. Keep for reference but not in main flow

### Phase 5: Testing & Validation
1. Test that existing imports still work
2. Generate a test demo
3. Verify all functionality preserved
4. Clean up and optimize

## Risk Mitigation

- **All imports remain the same**: External code continues to work
- **Incremental approach**: Move piece by piece, test each step
- **Backward compatibility**: Old imports redirect to new locations
- **Git history preserved**: Can always revert if issues arise

## Progress Tracking

### Phase 1: Extract Templates (In Progress)
- [x] Directory structure created
- [x] Template stubs created
- [x] Data generator templates extracted (partially)
- [ ] Query generator templates extracted
- [ ] Guide generator templates extracted
- [ ] Agent metadata templates extracted

### Phase 2: Extract Utilities (COMPLETE)
- [x] Code extraction utilities (CodeExtractor) ✅
  - `extract_python_code()` ✅
  - `validate_python_syntax()` ✅
  - `validate_query_module_methods()` ✅
- [x] Static file generation (StaticFileGenerator) ✅
  - `generate_static_files()` ✅
  - `generate_all_queries_file()` ✅
  - `_remove_timestamp_parameters()` ✅
- [x] Config generation (ConfigGenerator) ✅
  - `generate_config_file()` ✅
- [x] Comprehensive tests created (23 tests, 100% passing) ✅

### Phase 3: Create Slim Orchestrator (Pending)
- [ ] Create new module_generator.py importing from submodules
- [ ] Keep only orchestration logic
- [ ] Delegate all template/utility work to submodules

### Phase 4: Move Deprecated Code (Pending)
- [ ] Move old generation methods to deprecated/
- [ ] Mark clearly as deprecated
- [ ] Keep for reference but not in main flow

### Phase 5: Testing & Validation (Pending)
- [ ] Test that existing imports still work
- [ ] Generate a test demo
- [ ] Verify all functionality preserved
- [ ] Clean up and optimize

## Notes

- The refactoring preserves all functionality
- No breaking changes for existing code
- Improves maintainability and testability
- Makes it easier to understand and modify individual components
- Reduces cognitive load when working on specific features