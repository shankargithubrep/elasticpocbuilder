# Vulcan: AI-Powered Demo Generator for Elastic Agent Builder

Generate complete Elastic Agent Builder demos from a single prompt. Vulcan uses LLM code generation to create custom data, ES|QL queries, and demo narratives tailored to any industry or use case. Each demo is a standalone Python module you can version control, share, and refine.

---

## Quick Start

### Prerequisites

- Python 3.8+
- Anthropic API key
- Elasticsearch cluster with API key
- Kibana instance with Agent Builder enabled

### Installation

```bash
git clone https://github.com/elastic/vulcan.git
cd vulcan

python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your credentials (see below)
```

### Configure Credentials

Edit `.env` with your Anthropic API key and Elasticsearch credentials:

```bash
# LLM — Anthropic API key (required for demo generation)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Elasticsearch — for data indexing and query testing
ELASTICSEARCH_CLOUD_ID=your-deployment:base64string
ELASTICSEARCH_API_KEY=your-api-key

# Kibana — for Agent Builder deployment
ELASTICSEARCH_KIBANA_URL=https://your-deployment.kb.region.cloud.es.io:443
```

See `.env.example` for additional options (LLM Proxy, OpenAI fallback, custom models).

### Run

```bash
source venv/bin/activate
streamlit run app.py
```

Open `http://localhost:8501`.

### Sample Demos

Two pre-built demos are included in `demos/` so you can explore the Browse view immediately without generating anything:

- **creative_brand_asset_discover** — Search/RAG demo for brand asset discovery
- **telco_network_operations** — Analytics demo for network operations

---

## How It Works

### Create a Demo

1. Open the app and describe your customer scenario in the chat input:

   ```
   T-Mobile network operations team needs to monitor MME node health,
   detect authentication failures, and correlate cell site issues with
   HSS database sync problems. 500K signaling events per day.
   ```

2. The system extracts company, department, pain points, metrics, and auto-detects the demo type (Search vs Analytics).

3. If **prompt expansion** is enabled (default), the system enriches your brief description into detailed customer context before generation.

4. Type `generate` to kick off the 8-phase build process:
   - Query strategy planning
   - Data module generation
   - Dataset creation
   - Elasticsearch indexing
   - Data profiling
   - Query generation
   - Query testing & auto-fix
   - Finalization

5. Browse the result in the **Browse Demos** view.

### Browse & Refine

Select any demo to inspect and iterate across six tabs:

| Tab | What It Shows |
|-----|---------------|
| **Config** | Customer context, generation metadata |
| **Data** | Generated datasets, field statistics |
| **Queries** | Scripted, Parameterized, and Completion queries — edit, test, and validate inline |
| **Tools** | Deploy validated queries as Agent Builder tools |
| **Agents** | Create and configure AI agents with your tools |
| **Guide** | Demo narrative and talk track |

**Query editing**: Click any query to edit ES|QL in-browser, test against indexed data, and iterate without saving. Parameterized queries show suggested values and support one-click sample fill.

**Agent Builder deployment**: Deploy validated queries as tools, then create agents that use those tools — all from the Browse view.

---

## Demo Types

### Search / Completion Demos
For document retrieval, knowledge base search, semantic search, RAG applications.

- ES|QL commands: `MATCH`, `MATCH_PHRASE`, `QSTR`, `RERANK`, `COMPLETION`
- `semantic_text` fields for vector search (embeddings via ELSER)
- MATCH → RERANK → COMPLETION pipeline for question-answering
- Index strategy: `lookup` mode for document collections

### Analytics Demos
For metrics analysis, trends, aggregations, dashboards, time-series data.

- ES|QL commands: `STATS`, `INLINESTATS`, `LOOKUP JOIN`, `EVAL`, `DATE_TRUNC`
- Time-series aggregations with `@timestamp`
- Cross-dataset joins for enrichment
- Index strategy: `data_stream` for time-series, `lookup` for reference data

Demo type is **auto-detected** from your prompt (search keywords vs analytics keywords), or you can set it manually.

---

## Generated Module Structure

Each demo is a standalone Python package:

```
demos/telco_network_operations/
├── config.json              # Customer context + metadata
├── query_strategy.json      # Query planning document
├── data_profile.json        # Field statistics + sample values
├── agent_metadata.json      # Agent configuration for deployment
├── data_generator.py        # Python: data creation logic
├── query_generator.py       # Python: ES|QL query definitions
├── demo_guide.py            # Python: demo narrative
├── all_queries.json         # Compiled query definitions
├── query_testing_results.json  # Test execution report
└── data/                    # Generated CSV datasets
    ├── signaling_logs.csv
    ├── mme_system_logs.csv
    └── ...
```

Modules are self-contained — you can copy a `demos/` folder to share a complete demo with someone else.

---

## Configuration

### LLM Providers

Vulcan checks for LLM credentials in this order:

| Priority | Provider | Env Vars |
|----------|----------|----------|
| 1 | **Anthropic** (recommended) | `ANTHROPIC_API_KEY` |
| 2 | LLM Proxy | `LLM_PROXY_URL` + `LLM_PROXY_API_KEY` |
| 3 | OpenAI (limited ES|QL support) | `OPENAI_API_KEY` |
| 4 | Mock mode (testing only) | None set |

### Sidebar Settings

The app sidebar provides runtime configuration:

- **Prompt expansion** — LLM enriches brief prompts into detailed context (on by default)
- **Embedding type** — Sparse (ELSER), Dense (Jina), or Custom
- **Custom model override** — Use a specific LLM model
- **Custom endpoints** — Override rerank/completion inference endpoints
- **Connection status** — Live indicators for LLM and Elasticsearch

---

## Project Structure

```
vulcan/
├── app.py                          # Streamlit application
├── src/
│   ├── framework/                  # Core generation framework
│   │   ├── base.py                 # Abstract base classes
│   │   ├── module_generator.py     # LLM-powered code generation
│   │   ├── module_loader.py        # Dynamic module loading
│   │   └── orchestrator.py         # Generation orchestration
│   ├── services/                   # Supporting services
│   │   ├── llm_service.py          # LLM integration
│   │   ├── elasticsearch_indexer.py # Data indexing + query execution
│   │   ├── query_optimizer.py      # Constraint relaxation
│   │   ├── query_test_runner.py    # Query validation
│   │   ├── query_strategy_generator.py  # Analytics query planning
│   │   ├── search_strategy_generator.py # Search query planning
│   │   ├── agent_builder_service.py     # Agent Builder API
│   │   └── data_profiler.py        # Dataset statistics
│   └── ui/                         # Streamlit UI components
│       ├── views/
│       │   ├── create_demo.py      # Demo creation flow
│       │   ├── browse_demos.py     # Module library & testing
│       │   └── tabs/               # Browse view tabs
│       │       ├── config_tab.py
│       │       ├── data_tab.py
│       │       ├── queries_tab.py
│       │       ├── guide_tab.py
│       │       ├── tools_tab.py
│       │       └── agents_tab.py
│       ├── sidebar.py              # Settings UI
│       └── query_results_display.py # Query execution UI
├── demos/                          # Generated demo modules
├── tests/                          # Test suites
└── docs/                           # Documentation
```

---

## Testing

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

---

## Documentation

- [Modular Architecture](docs/MODULAR_ARCHITECTURE.md)
- [Quick Start Guide](docs/QUICK_START_GUIDE.md)
- [RAG/Search Architecture](docs/RAG_SEARCH_ARCHITECTURE.md)
- [ES|QL Reference](docs/ESQL_COMPLETE_REFERENCE.md)
- [Expansion Prompts](docs/EXPANSION_PROMPTS.md)

---

**Built by Jesse Miller <jesse.miller@elastic.co>**
