# Developer Guide
## How to Extend and Customize the Demo Builder

---

## 🚀 Quick Start for Developers

### Setup Development Environment

```bash
# Clone repo
git clone https://github.com/elastic/demo-builder.git
cd demo-builder

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install pytest black ruff mypy

# Setup pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your credentials
nano .env
```

Required variables:
```env
ELASTICSEARCH_HOST=https://your-instance.elastic.cloud
ELASTICSEARCH_API_KEY=your-api-key
ANTHROPIC_API_KEY=your-anthropic-key  # or OPENAI_API_KEY
GITHUB_TOKEN=ghp_xxxxx  # For state persistence
```

---

## 🏗️ Architecture Overview

### Service Layer Pattern

Each service is independent and mockable:

```python
# Pattern for all services
class ServiceName:
    def __init__(self, config=None):
        self.config = config or self.default_config()

    def primary_method(self, input_data):
        # Validate input
        # Process
        # Return structured output
        pass
```

### Data Flow

```
User Input → CustomerResearcher → ScenarioGenerator → DataGenerator
                                                           ↓
ValidationService ← ESQLGenerator ← [Datasets]
        ↓
ElasticAgentBuilderClient → [Deployed Agent]
```

---

## 🔧 Adding New Features

### 1. Adding a New Industry Template

**Step 1**: Add to `customer_researcher.py`

```python
# In CustomerResearcher.industry_templates
"manufacturing": {
    "pain_points": [
        "Supply chain optimization",
        "Quality control",
        "Equipment maintenance",
        "Production efficiency"
    ],
    "use_cases": [
        "Predictive maintenance",
        "Quality analytics",
        "Supply chain visibility",
        "Production monitoring"
    ],
    "key_metrics": ["oee", "defect_rate", "downtime"]
}
```

**Step 2**: Add scenario template in `scenario_generator.py`

```python
# In ScenarioGenerator.scenario_templates
"manufacturing_ops": {
    "name": "Manufacturing Operations",
    "description": "Production line monitoring and optimization",
    "datasets": [
        {"name": "equipment", "records": 500, "type": "reference"},
        {"name": "sensor_data", "records": 100000, "type": "metrics"},
        {"name": "production_events", "records": 50000, "type": "events"}
    ],
    "relationships": ["equipment->sensor_data", "equipment->production_events"]
}
```

**Step 3**: Add data patterns in `data_generator.py`

```python
def _generate_manufacturing_data(self, name: str, num_records: int):
    """Generate manufacturing-specific data"""
    # Custom generation logic
    pass
```

### 2. Adding a New Query Pattern

**Step 1**: Add template to `esql_generator.py`

```python
# In ESQLGenerator.query_templates
"anomaly_detection": """FROM {index}
| EVAL zscore = (value - AVG(value)) / STDDEV(value)
| WHERE ABS(zscore) > 3
| SORT zscore DESC
| LIMIT 100"""
```

**Step 2**: Add to query generation logic

```python
# In generate_queries method
if "sensor" in dataset_name or "metric" in dataset_name:
    queries.append(self._create_query(
        name="Anomaly Detection",
        description="Find statistical outliers",
        esql=self._fill_template("anomaly_detection", {"index": dataset_name}),
        complexity="complex"
    ))
```

### 3. Adding a New Validation Rule

**Step 1**: Add detection in `test_query_refinement.py`

```python
def detect_issues(self, query: str) -> List[str]:
    issues = []

    # New rule: Check for EVAL before WHERE
    if "EVAL" in query and "WHERE" in query:
        eval_pos = query.index("EVAL")
        where_pos = query.index("WHERE")
        if eval_pos > where_pos:
            issues.append("eval_after_where")

    return issues
```

**Step 2**: Add fix logic

```python
def apply_fixes(self, query: str, issues: List[str]) -> str:
    if "eval_after_where" in issues:
        # Reorder EVAL before WHERE
        # Implementation here
        pass
    return query
```

---

## 📊 Working with Data Generation

### Creating Custom Data Generators

```python
from src.services.data_generator import DataGenerator

class CustomDataGenerator(DataGenerator):
    def generate_custom_dataset(self, config):
        """Generate domain-specific data"""

        # Use Faker for realistic data
        from faker import Faker
        fake = Faker()

        # Generate base data
        data = {
            "id": [f"ID-{i:06d}" for i in range(config["records"])],
            "timestamp": pd.date_range(
                end=datetime.now(),
                periods=config["records"],
                freq=config.get("frequency", "1H")
            ),
            "value": np.random.normal(
                loc=config.get("mean", 100),
                scale=config.get("std", 20),
                size=config["records"]
            )
        }

        return pd.DataFrame(data)
```

### Adding Relationships

```python
def add_foreign_keys(self, source_df, target_df, key_field="id"):
    """Add foreign key relationship"""

    # Get source IDs
    source_ids = source_df[key_field].values

    # Add to target with realistic distribution
    # 80% of records reference 20% of sources (Pareto)
    popular_ids = np.random.choice(
        source_ids[:int(len(source_ids)*0.2)],
        size=int(len(target_df)*0.8)
    )
    regular_ids = np.random.choice(
        source_ids,
        size=len(target_df) - len(popular_ids)
    )

    target_df[f"{source_df.name}_id"] = np.concatenate([
        popular_ids, regular_ids
    ])

    return target_df
```

---

## 🔍 Working with ES|QL Queries

### Query Building Best Practices

```python
class QueryBuilder:
    @staticmethod
    def build_aggregation_query(index: str, metric: str, group_by: str):
        """Build a properly formatted aggregation query"""

        query = f"""FROM {index}
| STATS
    total = SUM({metric}),
    average = AVG({metric}),
    count = COUNT(*)
  BY {group_by}
| SORT total DESC
| LIMIT 10"""

        # Validate
        if "/" in query and "TO_DOUBLE" not in query:
            # Apply fix
            query = QueryBuilder.fix_division(query)

        return query

    @staticmethod
    def fix_division(query: str):
        """Fix integer division issues"""
        import re
        pattern = r'(\w+)\s*/\s*(\w+)'
        return re.sub(pattern, r'TO_DOUBLE(\1) / \2', query)
```

### Testing Queries

```python
def test_query_locally(query: str, sample_data: pd.DataFrame):
    """Test query logic without Elasticsearch"""

    # Parse query components
    # This is simplified - real implementation would need full parser

    if "STATS" in query and "BY" in query:
        # Simulate aggregation
        group_field = query.split("BY")[1].strip().split()[0]
        result = sample_data.groupby(group_field).agg({
            'value': ['sum', 'mean', 'count']
        })
        return result

    return sample_data
```

---

## 🤖 Extending the LLM Integration

### Adding Custom LLM Providers

```python
# In src/services/llm_service.py (to be created)

from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)

    def generate(self, prompt: str) -> str:
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
```

### Prompt Templates

```python
# In src/prompts/templates.py

CUSTOMER_RESEARCH_PROMPT = """
Analyze this company: {company_name}
Department: {department}

Provide:
1. Industry classification
2. Top 3 pain points for this department
3. Relevant use cases for Agent Builder
4. Key metrics they would track

Format as JSON.
"""

QUERY_GENERATION_PROMPT = """
Generate ES|QL queries for this scenario:
Datasets: {datasets}
Use cases: {use_cases}

Requirements:
- Use TO_DOUBLE for division
- JOIN before aggregation
- Include LIMIT where appropriate

Generate 5 queries with progressive complexity.
"""
```

---

## 🧪 Testing Your Changes

### Unit Testing Pattern

```python
# In tests/test_services.py

import pytest
from src.services.data_generator import DataGenerator

class TestDataGenerator:
    def setup_method(self):
        self.generator = DataGenerator()

    def test_generates_correct_record_count(self):
        scenario = {
            "datasets": [
                {"name": "test", "records": 1000, "type": "reference"}
            ]
        }

        datasets = self.generator.generate_datasets(scenario)

        assert "test" in datasets
        assert len(datasets["test"]) == 1000

    def test_maintains_relationships(self):
        # Test foreign key integrity
        pass

# Run tests
# pytest tests/test_services.py -v
```

### Integration Testing

```python
# In tests/test_integration_custom.py

def test_custom_industry_flow():
    """Test complete flow for custom industry"""

    # 1. Research
    researcher = CustomerResearcher()
    profile = researcher.research_company("Manufacturing Co", "Operations")

    # 2. Generate scenario
    generator = ScenarioGenerator()
    scenario = generator.generate_scenario(profile.__dict__)

    # 3. Create data
    data_gen = DataGenerator()
    datasets = data_gen.generate_datasets(scenario)

    # 4. Generate queries
    esql_gen = ESQLGenerator()
    queries = esql_gen.generate_queries(scenario, datasets)

    # Validate
    assert len(datasets) > 0
    assert len(queries) > 0
    assert all(esql_gen.validate_query(q["esql"]) for q in queries)
```

---

## 🚢 Deployment Considerations

### Environment-Specific Configs

```python
# In src/config.py

import os
from enum import Enum

class Environment(Enum):
    DEV = "development"
    STAGING = "staging"
    PROD = "production"

class Config:
    def __init__(self):
        self.env = Environment(os.getenv("ENVIRONMENT", "development"))

        # Environment-specific settings
        self.settings = {
            Environment.DEV: {
                "max_records": 10000,
                "enable_mock": True,
                "log_level": "DEBUG"
            },
            Environment.PROD: {
                "max_records": 1000000,
                "enable_mock": False,
                "log_level": "INFO"
            }
        }

    def get(self, key):
        return self.settings[self.env].get(key)
```

### Error Handling

```python
# In src/utils/error_handler.py

class DemoBuilderError(Exception):
    """Base exception for Demo Builder"""
    pass

class DataGenerationError(DemoBuilderError):
    """Raised when data generation fails"""
    pass

class QueryValidationError(DemoBuilderError):
    """Raised when query validation fails"""
    pass

def handle_error(func):
    """Decorator for consistent error handling"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DemoBuilderError as e:
            logger.error(f"Demo Builder Error: {e}")
            # Return safe default or raise based on context
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            # Log full traceback in debug mode
            if Config().get("log_level") == "DEBUG":
                logger.exception(e)
            raise DemoBuilderError(f"Operation failed: {e}")
    return wrapper
```

---

## 📝 Code Style Guide

### Python Standards
- Use Black for formatting
- Use Ruff for linting
- Type hints for all public methods
- Docstrings for all classes and methods

### Naming Conventions
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### ES|QL Query Formatting
```esql
FROM index_name
| WHERE condition
| EVAL new_field = expression
| STATS
    metric1 = AGG1(field1),
    metric2 = AGG2(field2)
  BY group_field
| SORT sort_field DESC
| LIMIT 10
```

---

## 🐛 Debugging Tips

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set in .env
LOG_LEVEL=DEBUG
```

### Inspect Intermediate State

```python
# Add debug points in services
def generate_queries(self, scenario, datasets):
    logger.debug(f"Scenario: {json.dumps(scenario, indent=2)}")
    logger.debug(f"Dataset keys: {datasets.keys()}")

    # Generate queries
    queries = []

    logger.debug(f"Generated {len(queries)} queries")
    for q in queries:
        logger.debug(f"  - {q['name']}: {q['complexity']}")

    return queries
```

### Test Without Elasticsearch

```python
# Set in .env
ENABLE_MOCK_MODE=true

# Or in code
if not self.elastic_client:
    logger.info("Running in mock mode")
    return self.mock_response()
```

---

## 📚 Additional Resources

### Internal Docs
- [Internal Documentation](INTERNAL_DOCUMENTATION.md)
- [API Reference](API_REFERENCE.md)
- [Test Strategy](../tests/TEST_STRATEGY.md)

### External Resources
- [ES|QL Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/esql.html)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)

---

*Version: 1.0.0*
*Last Updated: October 21, 2024*