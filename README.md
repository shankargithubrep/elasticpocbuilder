# Demo Builder: LLM-Powered Demo Generation Platform

An AI-powered platform for Elastic Solutions Architects that generates custom Python code modules to create customer-specific demo assets. Each demo is built through a sophisticated planning process that aligns ES|QL queries with business intent, then designs data generation to support those queries.

---

## Overview

Demo Builder uses LLM code generation to create custom Python modules for each customer. These modules generate synthetic data, ES|QL queries, and demo narratives tailored to specific business contexts. The platform emphasizes query-first planning, where business intent drives query design, which then informs data generation strategy.

### Key Approach

```
Customer Context → Query Planning → Data Generation Design → Asset Creation
```

Rather than filling templates, the system generates working Python code that implements customer-specific business logic. Each generated module is a standalone package that can be version-controlled, shared, and refined.

---

## Core Capabilities

### Intent-Driven Query Planning

The system analyzes customer pain points and business questions to plan ES|QL queries before generating any data:

1. **Intent Analysis**: Extracts business questions from customer context
2. **Query Strategy**: Plans query types (scripted, parameterized, RAG) based on use cases
3. **Data Requirements**: Designs datasets that support planned queries
4. **Implementation**: Generates Python modules that create aligned data and queries

This ensures queries answer real business questions with data structured to support those answers.

### One-Shot Build Process

The platform aims for working demos in a single generation cycle through:

- **Pre-validation**: Syntax checking with automatic error correction
- **Query Testing**: Optional Elasticsearch execution with result validation
- **Constraint Optimization**: LLM-assisted query refinement for zero-result queries
- **Interactive Editing**: Browser-based query modification and testing

### Query Development Tools

**Browse View Features**:
- Edit queries directly in the browser with syntax highlighting
- Test modified queries against indexed data
- View results inline without saving changes
- Parameter testing with sample values from data profiles
- LLM-powered constraint relaxation for failed queries

**Testing Support**:
- Execute queries against real Elasticsearch clusters
- Automatic retry with LLM-based error fixing (up to 3 attempts)
- Sample value extraction from data profiles
- Parameterized query testing interface

---

## Quick Start

### Prerequisites

- Python 3.8+
- Elasticsearch cluster (Cloud or local) with API key
- Anthropic API key (for code generation)

### Installation

```bash
# Clone repository
git clone https://github.com/elastic/demo-builder.git
cd demo-builder

# Setup environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your API keys
```

### Start Application

```bash
source venv/bin/activate
streamlit run app.py
```

Access at `http://localhost:8501`

---

## Generation Process

### 1. Context Extraction

Provide customer information in natural language:

```
Bass Pro Shops needs to analyze fishing gear sales performance
across regional stores. Product management team struggles with
slow SQL reporting on 50K daily transactions.
```

System extracts:
- Company: Bass Pro Shops
- Department: Product Management
- Pain Points: Slow reporting
- Scale: 50K transactions/day
- Industry: Retail

### 2. Query Strategy Planning

LLM analyzes business questions and plans query approach:

**Query Strategy Document** (`query_strategy.json`):
```json
{
  "business_intent": [
    "Identify top-selling products by region",
    "Track seasonal patterns in fishing categories"
  ],
  "query_types": {
    "scripted": ["regional_performance", "seasonal_trends"],
    "parameterized": ["product_lookup", "category_filter"],
    "rag": ["ask_about_sales"]
  },
  "datasets": [
    {
      "name": "product_catalog",
      "type": "reference",
      "purpose": "Support product lookups and JOINs",
      "fields": ["product_id", "category", "price"]
    },
    {
      "name": "sales_transactions",
      "type": "timeseries",
      "purpose": "Analyze temporal sales patterns",
      "fields": ["@timestamp", "product_id", "region", "revenue"]
    }
  ]
}
```

### 3. Data Generation Design

LLM generates Python code that creates data supporting the planned queries:

**Generated Module** (`data_generator.py`):
```python
class BassProShopsDataGenerator(DataGeneratorModule):
    def generate_datasets(self):
        # Reference data for JOINs
        products = pd.DataFrame({
            'product_id': range(1, 1501),
            'category': self._assign_categories(),  # fishing_rods, reels, tackle
            'price': np.random.uniform(15, 500, 1500)
        })

        # Time-series data for analytics
        sales = pd.DataFrame({
            'timestamp': pd.date_range(end=datetime.now(), periods=2000, freq='h'),
            'product_id': np.random.choice(products['product_id'], 2000),
            'region': np.random.choice(['Northeast', 'South', 'Midwest'], 2000),
            'revenue': self._calculate_revenue(...)
        })

        return {'products': products, 'sales': sales}
```

### 4. Query Implementation

LLM generates queries aligned with business intent and data structure:

**Generated Module** (`query_generator.py`):
```python
class BassProShopsQueryGenerator(QueryGeneratorModule):
    def generate_queries(self):
        return [
            {
                'name': 'Regional Sales Performance',
                'type': 'scripted',
                'esql': '''
                    FROM sales_transactions
                    | WHERE @timestamp > NOW() - 90 days
                    | STATS revenue = SUM(revenue) BY region
                    | SORT revenue DESC
                ''',
                'purpose': 'Identify highest-revenue regions'
            },
            {
                'name': 'Product Lookup',
                'type': 'parameterized',
                'esql': '''
                    FROM product_catalog
                    | WHERE product_id == ?product_id
                ''',
                'parameters': [{
                    'name': 'product_id',
                    'type': 'integer',
                    'description': 'Product identifier'
                }]
            }
        ]
```

---

## Query Testing & Refinement

### Automated Testing

After generation, optionally test queries against real Elasticsearch:

```python
# 1. Index generated data
indexer.index_dataset(products_df, 'product_catalog')
indexer.index_dataset(sales_df, 'sales_transactions')

# 2. Execute each query
for query in queries:
    result = es_client.query(query['esql'])

# 3. Auto-fix failures with LLM assistance
if error:
    fixed_query = llm.fix_query(query, error, data_profile)
    retry(fixed_query)  # Up to 3 attempts
```

Results saved to `query_testing_results.json`:
```json
{
  "total_queries": 6,
  "passed": 4,
  "fixed": 1,
  "failed": 1,
  "queries": [
    {
      "name": "Regional Performance",
      "status": "fixed",
      "attempts": 2,
      "original_error": "Unknown field: timestamp",
      "fix_applied": "Changed to @timestamp"
    }
  ]
}
```

### Interactive Query Editing

**Browse View Capabilities**:

- **Edit Mode**: Click "Edit Query" checkbox to modify any query
- **Test Execution**: Run modified queries without saving to disk
- **Result Display**: View query results inline below editor
- **Parameter Testing**: Test parameterized queries with sample values
- **Constraint Optimization**: LLM suggests relaxed constraints for zero-result queries

**Example Workflow**:
1. Navigate to Browse Demos → Queries tab
2. Check "Edit Query" on any query
3. Modify ES|QL in text editor
4. Click "Test This Query"
5. View results below editor
6. Iterate until satisfied

### Zero-Results Optimization

When queries return no results, the system can automatically suggest fixes:

```python
# Detect zero results
if len(results['values']) == 0:
    # Analyze constraints with data profile
    optimized_query, explanation = relax_query_constraints(
        query=original_query,
        data_profile=data_profile,
        llm_client=llm
    )
    # Suggests: "Relaxed date range from 7 days to 30 days"
```

---

## Architecture

### Module Structure

Each generated demo is a standalone Python package:

```
demos/bass_pro_shops_product_mgmt_20251107/
├── config.json              # Customer context + metadata
├── query_strategy.json      # Query planning document
├── data_profile.json        # Field statistics + sample values
├── data_generator.py        # Generated: Data creation logic
├── query_generator.py       # Generated: ES|QL query definitions
├── demo_guide.py            # Generated: Demo narrative
├── data/                    # Static assets
│   ├── product_catalog.csv
│   └── sales_transactions.csv
├── queries.json             # Compiled query definitions
└── query_testing_results.json  # Test execution report
```

### Key Components

| Component | Purpose | Technology |
|-----------|---------|------------|
| `app.py` | User interface and orchestration | Streamlit |
| `module_generator.py` | LLM-powered code generation | Claude (Anthropic) |
| `module_loader.py` | Dynamic Python module execution | importlib |
| `elasticsearch_indexer.py` | Data upload + query execution | Elasticsearch Python client |
| `query_optimizer.py` | Constraint relaxation for failed queries | Claude (Anthropic) |

### Generation Flow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Context Extraction                                    │
│ Natural language → Structured customer data              │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Query Strategy Planning                               │
│ Business intent → Query types + data requirements        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Code Generation                                       │
│ LLM writes Python modules implementing strategy          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Asset Creation                                        │
│ Execute modules → CSV + JSON + Markdown                  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Testing & Refinement                                  │
│ Index data → Test queries → Fix errors → Iterate         │
└─────────────────────────────────────────────────────────┘
```

---

## Design Constraints

The system enforces rules to ensure generated code produces working demos:

### Time Handling
- Data spans 0-120 days from current date
- Use `pd.date_range(end=datetime.now(), periods=N)`
- DataFrame column: `timestamp` (maps to `@timestamp` in Elasticsearch)

### Data Size
- Demos: 500-2000 rows maximum
- Fast loading and indexing (<30 seconds)
- Realistic but manageable scale

### Query Compatibility
- Reference datasets: `index.mode: lookup` for JOINs
- Time-series datasets: `index.mode: data_stream` for temporal queries
- Proper field types for JOIN compatibility

### ES|QL Best Practices
- Use `@timestamp` field name in queries
- Include time filters (`WHERE @timestamp > NOW() - N days`)
- Avoid overly restrictive constraints in initial queries

---

## Testing

### Test Suites

```bash
# Run all tests
python -m pytest tests/ -v

# Specific suites
python -m pytest tests/test_llm_integration.py -v      # LLM services
python -m pytest tests/test_data_generation.py -v      # Data generation
python -m pytest tests/test_integration.py -v          # End-to-end
```

### Test Coverage
- Framework: >90%
- Services: >85%
- UI: >70%

---

## Documentation

- [Modular Architecture](docs/MODULAR_ARCHITECTURE.md) - System design details
- [Quick Start Guide](docs/QUICK_START_GUIDE.md) - Detailed walkthrough
- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Extending the platform
- [API Reference](docs/API_REFERENCE.md) - Service documentation
- [ES|QL Strategy](docs/ESQL_SKILL_ACCURACY_STRATEGY.md) - Query generation approach

---

## Project Structure

```
demo-builder/
├── app.py                          # Main Streamlit application
├── src/
│   ├── framework/                  # Core generation framework
│   │   ├── base.py                 # Abstract base classes
│   │   ├── module_generator.py     # LLM code generation
│   │   ├── module_loader.py        # Dynamic module loading
│   │   └── orchestrator.py         # Generation orchestration
│   ├── services/                   # Supporting services
│   │   ├── llm_service.py          # LLM integration
│   │   ├── elasticsearch_indexer.py # ES operations
│   │   ├── query_optimizer.py      # Query refinement
│   │   └── esql_generator.py       # Query utilities
│   └── ui/                         # Streamlit components
│       ├── views/
│       │   ├── create_demo.py      # Demo creation interface
│       │   └── browse_demos.py     # Demo library + testing
│       ├── context_extractor.py    # NL → structured data
│       └── query_results_display.py # Query execution UI
├── demos/                          # Generated demo modules
├── tests/                          # Test suites
├── docs/                           # Documentation
└── .claude/                        # Claude Code integration
    ├── skills/                     # ES|QL expertise
    └── agents/                     # Specialized agents
```

---

## Key Features

### Query-First Design
- Business intent drives query planning
- Data generation designed to support planned queries
- Ensures queries answer real business questions

### Interactive Development
- Edit queries in browser without saving
- Test against real Elasticsearch data
- View results inline
- Parameter testing with sample values

### Automated Refinement
- Syntax validation with auto-correction
- Query execution testing
- LLM-assisted constraint optimization
- Zero-results troubleshooting

### Version Control
- Generated modules are Git-tracked
- Share modules across teams
- Build organizational query libraries
- Review changes like code

---

**Built by Jesse Miller <jesse.miller@elastic.co>**
