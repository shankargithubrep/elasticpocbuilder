# Demo Builder: Meta-Generative Demo Platform

## 🚀 Code That Writes Code That Creates Demos

A revolutionary platform for Elastic Solutions Architects that uses AI to generate custom Python code for each customer, which then generates tailored demo assets. Think of it as a **factory that builds factories** - each customer gets their own demo generation system.

---

## 📋 Table of Contents

- [What Makes This Different](#what-makes-this-different)
- [How It Works](#how-it-works)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Generated Modules](#generated-modules)
- [Testing & Validation](#testing--validation)
- [Documentation](#documentation)
- [Project Structure](#project-structure)

---

## What Makes This Different

### Traditional Approach (Templates)
```
Generic Template → Fill in blanks → Same-looking demo for everyone
```

### Demo Builder Approach (Code Generation)
```
Customer Context → LLM writes custom Python code → Code generates unique assets
```

**This is a meta-generative system**: The app doesn't create demos directly. Instead, it uses an LLM to write customer-specific Python modules that, when executed, generate all the demo materials.

---

## How It Works

### The Three-Level Architecture

#### Level 1: The Main App (User Interface)
**Location**: `app.py` + `src/framework/`

Takes your natural language description and extracts structured context:
- Company name, department, industry
- Pain points and use cases
- Scale and metrics
- Business challenges

**Example Input**:
```
"Bass Pro Shops, Product Management team, struggling with slow
reporting on fishing category performance across regions"
```

---

#### Level 2: Code Generation (The Factory Builder)
**Location**: `src/framework/module_generator.py`

The app uses Claude to **write three Python modules** specific to your customer:

**1. data_generator.py** - Python code that creates realistic sample data
```python
# Not static data, but the RECIPE to generate it
class BassProShopsDataGenerator(DataGeneratorModule):
    def generate_datasets(self):
        # Business logic specific to outdoor retail
        products = pd.DataFrame({
            'category': ['fishing_rods', 'reels', 'tackle', ...],
            'price': np.random.uniform(15, 500, 1500),
            'timestamp': pd.date_range(end=datetime.now(), periods=2000, freq='h')
        })
        # Returns realistic data with proper relationships
```

**2. query_generator.py** - Python code that creates ES|QL queries
```python
# Not the queries themselves, but code that produces them
class BassProShopsQueryGenerator(QueryGeneratorModule):
    def generate_queries(self):
        return [{
            'name': 'Regional Fishing Gear Performance',
            'esql': 'FROM product_sales | WHERE @timestamp > NOW() - 90 days...',
            'expected_insight': 'Top-selling fishing categories by region'
        }]
```

**3. demo_guide.py** - Python code that creates the demo narrative
```python
# Industry-specific talk tracks and objection handling
class BassProShopsDemoGuide(DemoGuideModule):
    def get_talk_track(self):
        return {
            'opening': 'I know outdoor retail has unique seasonality challenges...',
            'objections': {...}
        }
```

**Key Insight**: The LLM writes working Python code that implements these requirements, not just fills in templates.

---

#### Level 3: Asset Generation (The Small Factory)
**Location**: `demos/bass_pro_shops_product_management_20251029_214937/`

When you execute the generated modules, they produce:

1. **Datasets** (CSV files + Elasticsearch indices)
   - 1,500 fishing products with realistic prices
   - 2,000 sales transactions over 90 days
   - Proper relationships between tables
   - Timestamps that work with ES|QL queries

2. **ES|QL Queries** (JSON configuration)
   - 6-8 queries of progressive complexity
   - Answers to their specific business questions
   - Pre-tested against real Elasticsearch

3. **Demo Guide** (Markdown document)
   - Opening hook referencing their pain points
   - Industry-specific objection responses
   - Step-by-step demo flow

---

## Quick Start

### Prerequisites

- Python 3.8+
- Elasticsearch cluster (Cloud or local) with API key
- Anthropic API key (for code generation)

### Installation

```bash
# Clone and setup
git clone https://github.com/elastic/demo-builder.git
cd demo-builder

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials:
#   - ELASTIC_ENDPOINT or ELASTICSEARCH_CLOUD_ID
#   - ELASTIC_API_KEY or ELASTICSEARCH_API_KEY
#   - ANTHROPIC_API_KEY
```

### Start the App

```bash
source venv/bin/activate
streamlit run app.py
```

The app opens at `http://localhost:8501`

---

### Creating Your First Demo

**1. Provide Customer Context (Create Demo Mode)**

Paste a customer description or click "Use Test Prompt":
```
Bass Pro Shops needs to analyze fishing gear sales performance
across their regional stores. Product management team struggles
with slow SQL reporting on 50K daily transactions.
```

Watch the sidebar extract:
- Company: Bass Pro Shops
- Department: Product Management
- Pain Points: Slow reporting
- Scale: 50K daily transactions

**2. Generate the Demo Module**

When context reaches ≥50%, type: **"Generate demo"**

The system:
- Sends detailed prompts to Claude
- Gets back working Python code
- Validates syntax (auto-fixes errors)
- Saves to `demos/bass_pro_shops_product_management_20251029_214937/`

**3. Assets Are Generated**

The generated Python modules create:
- `product_catalog.csv` (1,500 products)
- `product_sales.csv` (2,000 transactions)
- `queries.json` (6 ES|QL queries)
- `demo_guide.md` (customized narrative)

**4. Index and Test (Optional)**

Click "Index in Elasticsearch" to:
- Upload data to your cluster
- Execute queries against real data
- Auto-fix any failing queries (up to 3 attempts)
- Get `query_testing_results.json` report

**5. Browse and Share**

Switch to "Browse Demos" mode to:
- View all generated modules
- Inspect datasets and queries
- Delete or customize modules
- Share with teammates (Git-tracked)

---

## Architecture

### System Flow

```
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 1: User Interface (app.py)                            │
│ ─────────────────────────────────────────────────────────── │
│ Input: "Bass Pro Shops product team needs sales analytics"  │
│ Extract: company, department, pain points, scale            │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 2: Code Generation (module_generator.py)              │
│ ─────────────────────────────────────────────────────────── │
│ LLM Prompt: "Generate Python for Bass Pro Shops..."         │
│ LLM Response: Complete Python modules (3 files)             │
│ Validation: Syntax checking + auto-fix                      │
│ Output: demos/bass_pro_*/[data|query|guide]_generator.py    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ LEVEL 3: Asset Generation (generated modules)               │
│ ─────────────────────────────────────────────────────────── │
│ Execute: data_generator.generate_datasets()                 │
│ Creates: product_catalog.csv, product_sales.csv             │
│ Execute: query_generator.generate_queries()                 │
│ Creates: queries.json (6-8 ES|QL queries)                   │
│ Execute: demo_guide.generate_guide()                        │
│ Creates: demo_guide.md (narrative + talk track)             │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Role | Technology |
|-----------|------|------------|
| `app.py` | User interface and orchestration | Streamlit |
| `module_generator.py` | LLM-powered code generation | Claude (Anthropic) |
| `module_loader.py` | Dynamic Python module execution | importlib |
| `elasticsearch_indexer.py` | Data upload and validation | Elasticsearch Python client |
| `data_generator.py` | Generated: Creates sample data | Pandas, NumPy |
| `query_generator.py` | Generated: Creates ES\|QL queries | Custom business logic |
| `demo_guide.py` | Generated: Creates demo script | Markdown generation |

---

## Generated Modules

Each customer gets a standalone Python package:

```
demos/bass_pro_shops_product_management_20251029_214937/
├── config.json              # Customer context metadata
├── data_generator.py        # Custom data generation code
├── query_generator.py       # Custom ES|QL queries
├── demo_guide.py            # Demo narrative and talk track
├── data/                    # Generated static files
│   ├── product_catalog.csv
│   └── product_sales.csv
├── queries.json             # Compiled queries
└── query_testing_results.json  # Validation report
```

### Key Features of Generated Modules

**1. Customization**
- Edit Python files to tweak behavior
- Add industry-specific patterns
- Refine queries for specific use cases

**2. Reusability**
- Share entire module folders with team
- Build a library of industry templates
- Version control in Git

**3. Reproducibility**
- Regenerate assets anytime
- Consistent results across machines
- No manual data preparation

---

## Testing & Validation

### Module Validation (Level 2)

After code generation:
```python
# Automatic syntax checking
py_compile.compile('data_generator.py')  # ✅ or auto-fix

# Up to 3 fix attempts per module
if syntax_error:
    send_to_llm("Fix this Python error: ...")
```

Results saved to `config.json`:
```json
{
  "module_validation": {
    "data_generator_valid": true,
    "query_generator_valid": true,
    "syntax_fixes_applied": 2
  }
}
```

### Query Testing (Level 3)

Optional real Elasticsearch testing:
```python
# 1. Index generated data
indexer.index_dataset(df, 'product_sales')

# 2. Execute each query
for query in queries:
    result = es_client.query(query['esql'])

# 3. Auto-fix failures
if error:
    fixed_query = llm.fix_query(query, error)
    retry(fixed_query)  # Up to 3 attempts
```

Results saved to `query_testing_results.json`:
```json
{
  "total_queries": 6,
  "successfully_fixed": 5,
  "needs_manual_fix": 1,
  "queries": [
    {
      "name": "Regional Performance",
      "was_fixed": true,
      "fix_attempts": 2,
      "original_error": "Unknown field: timestamp",
      "final_query": "... @timestamp ..."
    }
  ]
}
```

### Critical Constraints

The system enforces strict rules in generated code:

**Time Boundaries**:
- Data spans 0-120 days from today
- Never generate old dates (2023) or future dates
- Use `pd.date_range(end=datetime.now(), periods=N)`

**Field Naming**:
- Elasticsearch field: `@timestamp`
- DataFrame column: `timestamp`
- Indexer maps: `timestamp` → `@timestamp`

**Data Size**:
- Demos: 500-2000 rows max
- Fast loading (<30 seconds)
- Realistic but not overwhelming

**Relationships**:
- Lookup tables: `index.mode: lookup`
- JOIN-compatible field types
- Proper foreign key references

---

## Documentation

### Core Guides
- [Modular Architecture](docs/MODULAR_ARCHITECTURE.md) - System design
- [Quick Start Guide](docs/QUICK_START_GUIDE.md) - Detailed walkthrough
- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Extending the platform
- [API Reference](docs/API_REFERENCE.md) - Service documentation

### Technical Docs
- [Elasticsearch Indexing](docs/ELASTICSEARCH_INDEXING_IMPLEMENTATION.md) - Indexer details
- [ES|QL Skills](docs/ESQL_SKILL_ACCURACY_STRATEGY.md) - Query generation
- [Field Metadata](docs/FIELD_METADATA_IMPLEMENTATION_PLAN.md) - Mapping strategy

---

## Project Structure

```
demo-builder/
├── app.py                          # Unified Streamlit interface
├── src/
│   ├── framework/                  # Meta-generative framework
│   │   ├── base.py                 # Abstract base classes
│   │   ├── module_generator.py     # LLM code generation
│   │   ├── module_loader.py        # Dynamic execution
│   │   └── orchestrator.py         # Coordination
│   ├── services/                   # Supporting services
│   │   ├── llm_service.py          # LLM integration
│   │   ├── elasticsearch_indexer.py # Data upload
│   │   ├── enhanced_data_generator.py # Utilities
│   │   └── esql_generator.py       # Query helpers
│   └── ui_helpers.py               # Streamlit components
├── demos/                          # Generated modules
│   └── {company}_{dept}_{timestamp}/
│       ├── config.json
│       ├── data_generator.py       # GENERATED by LLM
│       ├── query_generator.py      # GENERATED by LLM
│       ├── demo_guide.py           # GENERATED by LLM
│       ├── data/*.csv              # Generated assets
│       └── queries.json            # Compiled queries
├── .claude/                        # Claude Code integration
│   ├── skills/                     # ES|QL expertise
│   │   ├── agent-builder.md
│   │   ├── esql-validator.md
│   │   └── esql-advanced-commands.md
│   └── agents/                     # Specialized agents
├── tests/                          # Test suites
│   ├── test_llm_integration.py     # 14/14 passing ✅
│   ├── test_data_generation.py     # 14/14 passing ✅
│   └── test_integration.py         # 12/14 passing ⚠️
├── docs/                           # Documentation
└── requirements.txt                # Dependencies
```

---

## Why This Architecture?

### Benefits

**1. Infinite Customization**
- Every demo written from scratch for that customer
- No "template feel" - feels bespoke

**2. Version Control**
- Generated Python modules are Git-tracked
- Share modules across team
- Review changes like code

**3. Refinable**
- Developers can edit generated Python
- Add business logic after generation
- Build on top of LLM output

**4. Transparent**
- Code explains the business logic
- No "black box" generation
- Debuggable and testable

**5. Scalable**
- Module library grows over time
- Industry patterns emerge
- Team learns from each other's demos

---

## Example Flow

### Input (30 seconds)
```
Bass Pro Shops product management team analyzing fishing gear
sales across 200 stores. Need to identify regional trends and
seasonal patterns in tackle vs. rod sales.
```

### Level 2 Output (5 minutes)
```python
# demos/bass_pro_shops_product_management_20251029_214937/data_generator.py
def generate_datasets(self):
    # 1,500 fishing products with categories
    products = pd.DataFrame({
        'product_id': [...],
        'category': ['fishing_rods', 'reels', 'tackle', 'bait', ...],
        'price': np.random.uniform(15, 500, 1500),
        'seasonality': [...] # Peak summer for certain items
    })

    # 2,000 sales over last 90 days with regional patterns
    sales = pd.DataFrame({
        'timestamp': pd.date_range(end=datetime.now(), periods=2000, freq='h'),
        'product_id': np.random.choice(products['product_id'], 2000),
        'store_region': np.random.choice(['Northeast', 'South', ...], 2000),
        'revenue': [...]
    })
    return {'products': products, 'sales': sales}
```

### Level 3 Output (instant)
- `product_catalog.csv` - 1,500 fishing products
- `product_sales.csv` - 2,000 regional sales
- `queries.json` - 6 queries analyzing trends
- `demo_guide.md` - Outdoor retail narrative

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific suites
python -m pytest tests/test_llm_integration.py      # LLM service (14/14 ✅)
python -m pytest tests/test_data_generation.py      # Data generation (14/14 ✅)
python -m pytest tests/test_integration.py          # Integration (12/14 ⚠️ 85.7%)
```

### Test Coverage
- Framework: >90%
- Services: >85%
- UI: >70%

---

## Contributing

### Development Setup

```bash
# Create branch
git checkout -b feature/your-feature

# Activate environment
source venv/bin/activate

# Make changes and test
python -m pytest tests/

# Format code
black src/ tests/
isort src/ tests/

# Commit
git commit -m "feat: add new industry template"
```

---

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: GitHub Issues
- **Email**: sa-tools@elastic.co

---

## The Magic Moment

**What users see**:
> "I described my customer's problem, and 5 minutes later I have a complete, working demo with data, queries, and a script."

**What actually happens**:
> The system used an LLM to write custom Python code that encodes domain expertise, business logic, and demo best practices - then executed that code to produce all the assets.

It's **code generating code generating content** - and that's what makes it scalable, customizable, and powerful.

---

**Built with ❤️ by the Elastic Solutions Architecture Team**
