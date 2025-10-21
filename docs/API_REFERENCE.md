# API Reference
## Elastic Agent Builder Demo Platform

---

## 📚 Table of Contents
- [Core Services](#core-services)
- [Data Models](#data-models)
- [Utility Functions](#utility-functions)
- [Error Classes](#error-classes)

---

## Core Services

### CustomerResearcher

**Location**: `src/services/customer_researcher.py`

#### Methods

##### `research_company(company_name: str, department: str = None) -> CustomerProfile`
Analyzes a company to determine industry, pain points, and relevant use cases.

**Parameters:**
- `company_name` (str): Name of the company to research
- `department` (str, optional): Specific department to focus on

**Returns:**
- `CustomerProfile`: Object containing:
  - `company_name` (str): Input company name
  - `industry` (str): Detected or assigned industry
  - `department` (str): Target department
  - `pain_points` (List[str]): Identified business challenges
  - `use_cases` (List[str]): Recommended Agent Builder use cases

**Example:**
```python
researcher = CustomerResearcher()
profile = researcher.research_company("Adobe", "Marketing Operations")
```

##### `suggest_demo_focus(profile: CustomerProfile) -> Dict`
Suggests demonstration focus areas based on customer profile.

**Parameters:**
- `profile` (CustomerProfile): Customer profile object

**Returns:**
- `Dict`: Suggested focus areas with priorities

---

### ScenarioGenerator

**Location**: `src/services/scenario_generator.py`

#### Methods

##### `generate_scenario(customer_profile: Dict, use_case: str = None) -> Dict`
Creates a complete demo scenario with datasets and relationships.

**Parameters:**
- `customer_profile` (Dict): Customer profile from research
- `use_case` (str, optional): Specific use case to focus on

**Returns:**
- `Dict`: Scenario configuration with:
  - `name` (str): Scenario name
  - `description` (str): Detailed description
  - `datasets` (List[Dict]): Dataset definitions
  - `relationships` (List[str]): Data relationships
  - `queries` (List[str]): Suggested query patterns
  - `agent_config` (Dict): Agent configuration

**Example:**
```python
generator = ScenarioGenerator()
scenario = generator.generate_scenario(
    customer_profile=profile.__dict__,
    use_case="Customer 360 Analytics"
)
```

##### `validate_scenario(scenario: Dict) -> bool`
Validates scenario completeness and consistency.

**Parameters:**
- `scenario` (Dict): Scenario to validate

**Returns:**
- `bool`: True if valid

---

### DataGenerator

**Location**: `src/services/data_generator.py`

#### Methods

##### `generate_datasets(scenario: Dict) -> Dict[str, pd.DataFrame]`
Generates synthetic datasets based on scenario specification.

**Parameters:**
- `scenario` (Dict): Scenario with dataset definitions

**Returns:**
- `Dict[str, pd.DataFrame]`: Named DataFrames with generated data

**Dataset Types:**
- `reference`: Lookup data (products, customers, etc.)
- `events`: Timestamped event data
- `metrics`: Numerical measurements
- `time_series`: Regular time-based data

**Example:**
```python
generator = DataGenerator()
datasets = generator.generate_datasets(scenario)
# Returns: {"customers": DataFrame, "orders": DataFrame, ...}
```

##### `export_datasets(datasets: Dict, output_dir: str) -> Dict[str, str]`
Exports datasets to CSV files.

**Parameters:**
- `datasets` (Dict[str, pd.DataFrame]): Datasets to export
- `output_dir` (str): Directory for output files

**Returns:**
- `Dict[str, str]`: Mapping of dataset names to file paths

---

### ESQLGenerator

**Location**: `src/services/esql_generator.py`

#### Methods

##### `generate_queries(scenario: Dict, datasets: Dict) -> List[Dict]`
Generates ES|QL queries based on scenario and data structure.

**Parameters:**
- `scenario` (Dict): Scenario configuration
- `datasets` (Dict): Available datasets

**Returns:**
- `List[Dict]`: Query objects with:
  - `name` (str): Query name
  - `description` (str): Query purpose
  - `esql` (str): ES|QL query string
  - `complexity` (str): "simple", "intermediate", or "complex"
  - `parameters` (List[str], optional): Query parameters

**Example:**
```python
esql_gen = ESQLGenerator()
queries = esql_gen.generate_queries(scenario, datasets)
```

##### `validate_query(esql: str) -> bool`
Validates ES|QL query syntax.

**Parameters:**
- `esql` (str): Query string to validate

**Returns:**
- `bool`: True if syntactically valid

##### `optimize_query(esql: str) -> str`
Optimizes query for performance and correctness.

**Parameters:**
- `esql` (str): Query to optimize

**Returns:**
- `str`: Optimized query

---

### ElasticClient

**Location**: `src/services/elastic_client.py`

#### Methods

##### `create_index(index_name: str, mappings: Dict = None, settings: Dict = None) -> bool`
Creates an Elasticsearch index.

**Parameters:**
- `index_name` (str): Name of index
- `mappings` (Dict, optional): Field mappings
- `settings` (Dict, optional): Index settings

**Important:**
- For lookup indices, must include `{"index.mode": "lookup"}` in settings

**Returns:**
- `bool`: Success status

##### `ingest_data(index_name: str, data: pd.DataFrame, batch_size: int = 1000) -> Dict`
Bulk ingests data into Elasticsearch.

**Parameters:**
- `index_name` (str): Target index
- `data` (pd.DataFrame): Data to ingest
- `batch_size` (int): Batch size for bulk operations

**Returns:**
- `Dict`: Ingestion statistics

##### `execute_esql(query: str) -> Dict`
Executes an ES|QL query.

**Parameters:**
- `query` (str): ES|QL query string

**Returns:**
- `Dict`: Query results with columns and values

---

### ValidationService

**Location**: `src/services/validation_service.py`

#### Methods

##### `validate_data_upload(index_name: str, data_df: pd.DataFrame) -> ValidationTask`
Validates successful data upload to Elasticsearch.

**Parameters:**
- `index_name` (str): Index name
- `data_df` (pd.DataFrame): Original data

**Returns:**
- `ValidationTask`: Task object with validation results

##### `validate_esql_query(query: Dict) -> ValidationResult`
Validates and executes an ES|QL query.

**Parameters:**
- `query` (Dict): Query object with name, description, esql

**Returns:**
- `ValidationResult`: Contains:
  - `success` (bool): Execution success
  - `execution_time` (float): Query time in ms
  - `row_count` (int): Result rows
  - `sample_data` (List): Sample results
  - `error` (str, optional): Error message

##### `validate_all_queries(queries: List[Dict]) -> Tuple[List[ValidationResult], Dict]`
Validates multiple queries and generates summary.

**Parameters:**
- `queries` (List[Dict]): Queries to validate

**Returns:**
- `Tuple[List[ValidationResult], Dict]`: Results and summary statistics

---

### ElasticAgentBuilderClient

**Location**: `src/services/elastic_agent_builder_client.py`

#### Methods

##### `create_esql_tool(tool: ESQLTool) -> Dict`
Creates an ES|QL tool in Agent Builder.

**Parameters:**
- `tool` (ESQLTool): Tool configuration with:
  - `name` (str): Tool name
  - `description` (str): Tool description
  - `esql` (str): Query with parameters
  - `parameters` (List[Dict]): Parameter definitions

**Returns:**
- `Dict`: Created tool with ID

**Example:**
```python
tool = ESQLTool(
    name="Get Customer Metrics",
    description="Retrieves metrics for a customer",
    esql="FROM metrics | WHERE customer_id == ?customer_id | STATS ...",
    parameters=[{"name": "customer_id", "type": "keyword", "required": True}]
)
response = client.create_esql_tool(tool)
```

##### `create_agent(agent: Agent) -> Dict`
Creates an agent with tools.

**Parameters:**
- `agent` (Agent): Agent configuration with:
  - `name` (str): Agent name
  - `instructions` (str): Agent instructions
  - `tools` (List[str]): Tool IDs
  - `labels` (Dict[str, str]): Metadata labels

**Returns:**
- `Dict`: Created agent with ID

##### `converse(agent_id: str, message: str) -> Dict`
Sends a message to an agent.

**Parameters:**
- `agent_id` (str): Agent identifier
- `message` (str): User message

**Returns:**
- `Dict`: Agent response

##### `validate_agent_with_queries(agent_id: str, test_queries: List[str]) -> List[Dict]`
Tests agent with sample queries.

**Parameters:**
- `agent_id` (str): Agent to test
- `test_queries` (List[str]): Test messages

**Returns:**
- `List[Dict]`: Responses for each query

---

### GitHubStateManager

**Location**: `src/services/github_state_manager.py`

#### Methods

##### `save_demo_state(demo_id: str, state: Dict) -> bool`
Persists demo state to GitHub.

**Parameters:**
- `demo_id` (str): Unique demo identifier
- `state` (Dict): State to save

**Returns:**
- `bool`: Success status

##### `load_demo_state(demo_id: str) -> Dict`
Retrieves demo state from GitHub.

**Parameters:**
- `demo_id` (str): Demo identifier

**Returns:**
- `Dict`: Saved state or empty dict

##### `list_demos() -> List[str]`
Lists available demo IDs.

**Returns:**
- `List[str]`: Demo identifiers

---

## Data Models

### CustomerProfile
```python
@dataclass
class CustomerProfile:
    company_name: str
    industry: str
    department: str
    pain_points: List[str]
    use_cases: List[str]
```

### ValidationTask
```python
@dataclass
class ValidationTask:
    name: str
    status: str  # "pending", "running", "completed", "failed"
    details: str
    start_time: float
    end_time: float = None
    result: Any = None
    error: str = None
```

### ValidationResult
```python
@dataclass
class ValidationResult:
    query_name: str
    success: bool
    execution_time: float
    row_count: int
    sample_data: List[Dict]
    error: str = None
```

### ESQLTool
```python
@dataclass
class ESQLTool:
    name: str
    description: str
    esql: str
    parameters: List[Dict]
```

### Agent
```python
@dataclass
class Agent:
    name: str
    instructions: str
    tools: List[str]
    labels: Dict[str, str] = field(default_factory=dict)
```

---

## Utility Functions

### Query Refinement Utilities

**Location**: `tests/test_query_refinement.py`

#### `detect_query_issues(query: str) -> List[str]`
Detects common ES|QL query issues.

**Issues Detected:**
- `integer_division`: Division without TO_DOUBLE
- `join_after_aggregation`: JOIN after STATS
- `missing_limit`: No LIMIT on non-aggregated queries

#### `apply_query_fixes(query: str, issues: List[str]) -> str`
Applies automatic fixes to detected issues.

**Fixes Applied:**
- Wraps numerator in TO_DOUBLE() for division
- Reorders JOIN before STATS
- Adds LIMIT 1000 to unbounded queries

---

## Error Classes

### DemoBuilderError
Base exception class for all demo builder errors.

### DataGenerationError
Raised when data generation fails.

### QueryValidationError
Raised when query validation fails.

### ElasticsearchConnectionError
Raised when cannot connect to Elasticsearch.

### AgentBuilderAPIError
Raised when Agent Builder API calls fail.

---

## Environment Variables

Required environment variables for operation:

```bash
# Elasticsearch Configuration
ELASTICSEARCH_HOST=https://your-instance.elastic.cloud
ELASTICSEARCH_API_KEY=your-api-key

# LLM Configuration (one of these)
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key

# GitHub State Persistence
GITHUB_TOKEN=ghp_xxxxx
GITHUB_REPO=elastic/demo-builder

# Optional
ELASTICSEARCH_VERIFY_CERTS=true
LOG_LEVEL=INFO
ENABLE_MOCK_MODE=false  # Run without Elasticsearch
```

---

## Response Formats

### Query Execution Response
```json
{
  "columns": [
    {"name": "field1", "type": "keyword"},
    {"name": "field2", "type": "long"}
  ],
  "values": [
    ["value1", 123],
    ["value2", 456]
  ]
}
```

### Validation Summary
```json
{
  "total_queries": 10,
  "successful": 8,
  "failed": 2,
  "average_execution_time": 45.2,
  "issues_found": ["integer_division", "missing_limit"],
  "fixes_applied": ["TO_DOUBLE", "LIMIT"]
}
```

### Agent Creation Response
```json
{
  "agent_id": "agent_xxxxx",
  "name": "Adobe Analytics Agent",
  "status": "active",
  "tools": ["tool_1", "tool_2"],
  "created_at": "2024-10-21T10:00:00Z"
}
```

---

## Rate Limits

### Elasticsearch API
- Bulk indexing: 10MB per request
- Query execution: 30 second timeout
- Concurrent requests: 10 max

### Agent Builder API
- Tool creation: 100/minute
- Agent creation: 20/minute
- Conversations: 60/minute

---

## Best Practices

### Query Generation
1. Always use TO_DOUBLE() for division operations
2. Place JOIN operations before aggregations
3. Include LIMIT on non-aggregated queries
4. Use parameterized queries for tools

### Data Generation
1. Keep reference data under 10,000 records
2. Generate time series with realistic intervals
3. Maintain foreign key relationships
4. Use appropriate data types for fields

### Error Handling
1. Implement retry logic with exponential backoff
2. Log all errors with context
3. Provide meaningful error messages
4. Gracefully degrade when services unavailable

---

*Version: 1.0.0*
*Last Updated: October 21, 2024*