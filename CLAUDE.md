# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Elastic POC Builder** is a modular platform for generating custom Elastic Agent Builder demonstrations. It uses LLM-generated Python modules to create customer-specific demos with realistic data, ES|QL queries, and demo guides.

**Architecture**: Streamlit UI + Modular Plugin Framework + LLM Code Generation

**Key Innovation**: Unlike static templates, this system generates custom Python code for each demo that can be version controlled, shared, and refined.

## Quick Start Commands

### Running the App
```bash
# Activate virtual environment
source venv/bin/activate

# Run the unified app (ONE APP for everything)
streamlit run app.py
```

The app starts at `http://localhost:8501`

### Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your API keys (see LLM Configuration section below)
```

### LLM Configuration

The system supports multiple LLM providers with automatic fallback. Configure at least one option:

**Option 1: LLM Proxy (Recommended for Team Use)**
```bash
# .env
LLM_PROXY_URL=https://your-llm-proxy.example.com
LLM_PROXY_API_KEY=your_proxy_key
```
Benefits: Centralized billing, usage tracking, model routing

**Option 2: Direct Anthropic API**
```bash
# .env
ANTHROPIC_API_KEY=sk-ant-your_key_here
```
Best for: Individual use, testing, development

**Option 3: OpenAI API (Fallback)**
```bash
# .env
OPENAI_API_KEY=sk-your_key_here
```
Note: Limited ES|QL support compared to Anthropic models

**Precedence Order**: LLM Proxy → Anthropic → OpenAI → Mock (tests only)

The system automatically detects which credentials are available and uses the highest priority option.

### Testing Commands
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/test_llm_integration.py -v       # LLM service tests (14/14 passing)
python -m pytest tests/test_data_generation.py -v      # Data generation tests (14/14 passing)
python -m pytest tests/test_integration.py -v          # Integration tests (12/14 passing, 85.7%)

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Development Commands
```bash
# Test module generation
python -c "from src.framework import create_demo; create_demo({'company_name': 'Test', 'department': 'Sales', 'industry': 'Tech', 'pain_points': ['slow'], 'use_cases': [], 'scale': '1000', 'metrics': []})"

# List generated demos
python -c "from src.framework import list_demos; print(list_demos())"

# Format code
black src/ tests/ app.py
isort src/ tests/ app.py
```

## Demo Types: Search vs Analytics

The system supports two demo types, each with specialized query strategies:

### 🔍 Search/RAG Demos (`demo_type: "search"`)
**Use For**: Document retrieval, knowledge base search, semantic search, RAG applications

**Features**:
- ES|QL Commands: `MATCH`, `MATCH_PHRASE`, `QSTR`, `RERANK`, `COMPLETION`
- `semantic_text` fields for vector-based search
- MATCH → RERANK → COMPLETION pipeline for RAG queries
- Fuzzy search, phrase matching, hybrid search

**Index Strategy**: Primarily `lookup` mode for document collections

**Query Types**: Focus on RETRIEVING specific documents (not aggregating)

**Examples**: Provider lookup, policy search, content discovery, support ticket search

### 📊 Analytics Demos (`demo_type: "analytics"`)
**Use For**: Metrics analysis, trends, aggregations, dashboards, time-series analytics

**Features**:
- ES|QL Commands: `STATS`, `INLINESTATS`, `LOOKUP JOIN`, `EVAL`, `DATE_TRUNC`
- Time-series aggregations with `@timestamp`
- Cross-dataset joins for enrichment
- Statistical calculations and trend analysis

**Index Strategy**:
- `data_stream` for time-series data
- `lookup` for reference data in JOINs

**Query Types**: Focus on AGGREGATING and analyzing patterns

**Examples**: Engagement metrics, denial trends, sales analysis, performance dashboards

### Classification
Demo type is **auto-detected** during conversation based on use case keywords:
- **Search keywords**: find, retrieve, lookup, documents, knowledge base, RAG, semantic search
- **Analytics keywords**: analyze, trend, metric, aggregate, dashboard, report, time-series

The orchestrator routes to different strategy generators based on `demo_type`:
- `SearchQueryStrategyGenerator` for search demos
- `QueryStrategyGenerator` for analytics demos

See **docs/RAG_SEARCH_ARCHITECTURE.md** for technical deep-dive.

## Key File Locations

### Main Application
- **app.py**: Unified Streamlit interface (ONE APP)
  - Create Demo mode: Conversational demo creation
  - Browse Demos mode: Module library management

### Modular Framework (`src/framework/`)
- **base.py**: Abstract base classes (DataGeneratorModule, QueryGeneratorModule, DemoGuideModule)
- **module_generator.py**: LLM-based code generation (generates Python files)
- **module_loader.py**: Dynamic module loading and execution
- **orchestrator.py**: Demo generation orchestration

### Services (`src/services/`)
- **llm_service.py**: LLM integration and context extraction
- **enhanced_data_generator.py**: Data generation utilities
- **esql_generator.py**: ES|QL query generation


### Generated Modules (`demos/`)
Each demo is a standalone Python package:
```
demos/salesforce_customer_success_20241021_143022/
├── config.json              # Customer context and metadata
├── data_generator.py        # Custom data generation code
├── query_generator.py       # Custom ES|QL queries
└── demo_guide.py           # Demo narrative and talk track
```

### Tests (`tests/`)
- **test_llm_integration.py**: LLM service tests (14/14 ✅)
- **test_data_generation.py**: Data generation tests (14/14 ✅)
- **test_integration.py**: End-to-end tests (12/14 ✅, 85.7% success rate)

### Documentation (`docs/`)
- **QUICK_START_GUIDE.md**: User guide for the unified app
- **MODULAR_ARCHITECTURE.md**: Architecture deep dive
- **DEVELOPER_GUIDE.md**: Developer documentation
- **API_REFERENCE.md**: API documentation

## Architecture Overview

### Modular Plugin Pattern

```
User Input
    │
    ▼
SmartContextExtractor
    │
    ▼
ModularDemoOrchestrator
    │
    ├─► ModuleGenerator (LLM generates Python code)
    │       │
    │       ├─► data_generator.py
    │       ├─► query_generator.py
    │       └─► demo_guide.py
    │
    └─► ModuleLoader (dynamically imports and executes)
            │
            ├─► load_data_generator()
            ├─► load_query_generator()
            └─► load_demo_guide()
```

### Key Principles

1. **LLM-Generated Code**: Each demo gets custom Python implementations
2. **Plugin Architecture**: Framework defines interfaces, LLM provides implementations
3. **Dynamic Loading**: Modules are imported and executed at runtime
4. **Version Control**: Generated modules are Git-tracked and shareable
5. **Customization**: Modules can be manually edited after generation

## Unified UI (app.py)

### Two Modes in One App

**Create Demo Mode**:
- Single comprehensive prompt submission (primary workflow)
- Sidebar generation options:
  - **LLM Model**: Select model (Fast/Balanced/Smart) - controls quality vs cost
  - **Demo Complexity**:
    - Standard: Direct processing of your prompt
    - Expanded: LLM enhances brief prompts into detailed context
  - **Demo Type**: Auto-detected (Search vs Analytics) or manually selected
- Real-time generation progress tracking
- Test prompt button for quick examples

**Browse Demos Mode**:
- List all generated demo modules with metadata cards
- Detailed tabs for each module:
  - **Config**: Customer context and settings
  - **Data**: Generated datasets with statistics
  - **Queries**: ES|QL queries with validation status
  - **Guide**: Demo narrative and talk track
  - **Tools**: Agent Builder tool definitions (if applicable)
  - **Agents**: Agent metadata and capabilities (if applicable)
- Module management (delete, inspect code)
- Export capabilities

### Session State Structure
```python
st.session_state = {
    "messages": [],              # Chat history
    "view_mode": str,           # "create" | "browse"
    "current_demo_module": str,  # Selected module name
    "selected_model": str,       # LLM model selection
    "demo_complexity": str,      # "standard" | "expanded"
    "demo_type": str,           # "auto" | "search" | "analytics"
    "generation_in_progress": bool  # Flag for active generation
}
```

## Code Style Guidelines

- **Python**: PEP 8, type hints, docstrings for all public functions
- **Naming**: snake_case for Python, descriptive variable names
- **Testing**: TDD approach, write tests first
- **Error Handling**: Use try/except with specific exceptions
- **Documentation**: Document complex logic and architectural decisions

## Critical Rules - DO NOT VIOLATE

- **MAINTAIN the unified app** - Single app.py handles everything
- **PRESERVE modular architecture** - Don't bypass module generation with static code
- **FOLLOW TDD** - Write tests before implementing features
- **RESPECT generated modules** - Don't modify them in the framework, users edit them in demos/
- **KEEP framework stable** - Updates shouldn't break existing generated modules
- **TEST module generation** - Always test with mock LLM before using real API
- **NEVER delete generated modules** without explicit permission

## Testing Strategy

### Test-Driven Development (TDD)
1. Write test defining expected behavior
2. Run test to see it fail (red)
3. Write minimal code to pass (green)
4. Refactor for quality
5. Repeat

### Current Test Status
- ✅ LLM Integration: 14/14 tests passing (100%)
- ✅ Data Generation: 14/14 tests passing (100%)
- ⚠️  Integration: 12/14 tests passing (85.7%)

### Coverage Targets
- Framework: >90%
- Services: >85%
- UI: >70%

## Module Generation Flow

### 1. Context Extraction
```python
extractor = SmartContextExtractor()
context = extractor.extract_context(user_message)
# Returns: company, department, pain_points, metrics, scale, etc.
```

### 2. LLM Code Generation
```python
generator = ModuleGenerator(llm_client)
module_path = generator.generate_demo_module(config)
# Creates: demos/company_department_timestamp/
```

### 3. Dynamic Loading
```python
loader = ModuleLoader(module_path)
data_gen = loader.load_data_generator()
datasets = data_gen.generate_datasets()
```

### 4. Execution
```python
query_gen = loader.load_query_generator(datasets)
queries = query_gen.generate_queries()
guide_gen = loader.load_demo_guide(datasets, queries)
guide = guide_gen.generate_guide()
```

## Common Workflows

### Creating a Demo
1. Start app: `streamlit run app.py`
2. Configure generation options in sidebar:
   - Select LLM Model (Fast/Balanced/Smart)
   - Choose Demo Complexity (Standard/Expanded)
   - Set Demo Type (Auto/Search/Analytics)
3. Paste comprehensive customer description or click "Use Test Prompt"
4. Click "Generate Demo" button
5. Monitor real-time progress (data → queries → guide)
6. View results or switch to Browse mode for detailed inspection

### Browsing Demos
1. Switch to "Browse Demos" mode in sidebar
2. Browse generated modules with metadata cards
3. Click "View Details" to see:
   - **Config**: Customer context and generation settings
   - **Data**: Generated datasets with field counts and statistics
   - **Queries**: ES|QL queries with validation status and results
   - **Guide**: Demo narrative, talk track, and key insights
   - **Tools**: Agent Builder tool definitions (JSON format)
   - **Agents**: Agent metadata and capabilities
4. Use "Delete" button to remove unwanted modules
5. Review query validation results and errors

### Customizing a Module
1. Navigate to `demos/module_name/`
2. Edit Python files (data_generator.py, query_generator.py, demo_guide.py)
3. Re-run demo to see changes
4. Commit to Git and share with team

### Adding Framework Features
1. Write tests in `tests/` (TDD)
2. Update base classes in `src/framework/base.py`
3. Update module generator prompts
4. Update module loader to use new methods
5. Run tests to verify

## Debugging Tips

### Module Generation Fails
- Check LLM prompts in module_generator.py
- Verify code extraction logic
- Test with mock generation
- Check file permissions in demos/

### Module Loading Fails
- Verify module directory structure
- Check for syntax errors: `python -m py_compile demos/module_name/data_generator.py`
- Ensure all imports available
- Check logs for import errors

### Context Extraction Issues
- Test patterns in SmartContextExtractor
- Add print statements to see extracted values
- Verify regex patterns match input format
- Test with known-good examples

### UI Not Responding
- Check session state initialization
- Verify needs_processing flag is set
- Look for errors in Streamlit console
- Test programmatic message flow

## Project Structure

```
vulcan/
├── app.py                          # Unified Streamlit interface
├── src/
│   ├── framework/                  # Modular architecture
│   │   ├── base.py
│   │   ├── module_generator.py
│   │   ├── module_loader.py
│   │   └── orchestrator.py
│   └── services/                   # Supporting services
│       ├── llm_service.py
│       ├── enhanced_data_generator.py
│       └── esql_generator.py
├── demos/                          # Generated modules
│   └── [customer]_[dept]_[timestamp]/
│       ├── config.json
│       ├── data_generator.py
│       ├── query_generator.py
│       └── demo_guide.py
├── tests/                          # Test suite
│   ├── test_llm_integration.py
│   ├── test_data_generation.py
│   └── test_integration.py
├── docs/                           # Documentation
│   ├── QUICK_START_GUIDE.md
│   ├── MODULAR_ARCHITECTURE.md
│   └── DEVELOPER_GUIDE.md
└── (archive/ removed - old app versions deleted)
```

## Success Metrics

- **Module Generation**: 100% success with mock LLM
- **Code Quality**: All generated modules pass syntax validation
- **Loading Success**: 100% of well-formed modules load correctly
- **Test Coverage**: >80% across all code
- **User Experience**: <20 seconds to generate complete demo

## Next Steps

1. **Improve test coverage** to >90%
2. **Implement A-ha moment** feature (currently placeholder)
3. **Add more industry patterns** to context extraction
4. **Optimize LLM prompts** for better code quality
5. **Add module templates** for common scenarios

---

**Built with ❤️ by the Elastic Solutions Architecture Team**
