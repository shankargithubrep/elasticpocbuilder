# Elastic Agent Builder Demo Platform
## Comprehensive Internal Documentation

---

## 🏗️ System Architecture

### Overview
The Demo Builder is a Streamlit-based application that automates the creation of Elastic Agent Builder demonstrations. It implements an iterative refinement loop that generates data, creates ES|QL queries, validates them, fixes issues automatically, and deploys agents with tools.

### Core Components

```
demo-builder/
├── app.py                    # Basic Streamlit interface
├── app_enhanced.py          # Enhanced version with validation UI
├── src/
│   ├── services/           # Core business logic
│   │   ├── customer_researcher.py      # Company/industry analysis
│   │   ├── scenario_generator.py       # Demo scenario creation
│   │   ├── data_generator.py          # Synthetic data generation
│   │   ├── esql_generator.py          # ES|QL query generation
│   │   ├── elastic_client.py          # Elasticsearch operations
│   │   ├── validation_service.py      # Query/data validation
│   │   ├── github_state_manager.py    # State persistence
│   │   └── elastic_agent_builder_client.py  # Agent Builder API
│   └── utils/
│       └── session_state.py           # Streamlit state management
├── tests/                   # Integration and unit tests
├── examples/               # Demo examples (Adobe)
└── docs/                   # Documentation
```

---

## 🔄 The Iterative Refinement Loop

### 1. Customer Research Phase
```python
# customer_researcher.py
CustomerResearcher.research_company(company_name, department)
```
- **Input**: Company name, department
- **Process**:
  - Detects industry from company name (heuristic)
  - Matches to industry templates
  - Customizes pain points for department
- **Output**: CustomerProfile with use cases, pain points

**Industry Templates Available**:
- retail, financial, healthcare, technology, marketing

### 2. Scenario Generation Phase
```python
# scenario_generator.py
ScenarioGenerator.generate_scenario(customer_profile, use_case)
```
- **Input**: Customer profile
- **Process**:
  - Selects appropriate template
  - Customizes for company size
  - Defines datasets and relationships
- **Output**: Scenario with datasets, relationships, agent config

**Scenario Templates**:
- performance_analytics, customer_360, fraud_detection, operational_intelligence

### 3. Data Generation Phase
```python
# data_generator.py
DataGenerator.generate_datasets(scenario)
```
- **Dataset Types**:
  - `reference`: Lookup data with IDs (products, customers)
  - `events`: Time-stamped events (transactions, logs)
  - `metrics`: Numerical measurements
  - `time_series`: Regular time-based data

- **Relationship Creation**:
  - Foreign keys added automatically
  - Maintains referential integrity
  - Supports multi-level relationships

### 4. Index Creation Phase
```python
# elastic_client.py
ElasticClient.create_index(index_name, mappings, settings)
```
- **Critical**: Lookup indices need `"index.mode": "lookup"`
- **Auto-mapping**: Infers from DataFrame dtypes
- **Bulk indexing**: Handles large datasets efficiently

### 5. Query Generation Phase
```python
# esql_generator.py
ESQLGenerator.generate_queries(scenario, datasets)
```
- **Query Templates**:
  - simple_aggregation
  - time_series_aggregation
  - top_entities
  - filtering_with_calc
  - join_pattern
  - trend_analysis
  - percentile_analysis

- **Automatic Adaptations**:
  - Detects timestamp fields for time-based queries
  - Identifies grouping fields
  - Creates JOINs based on relationships

### 6. Query Validation & Refinement
```python
# The critical iterative loop
issues = detect_query_issues(query)
if issues:
    fixed_query = apply_query_fixes(query, issues)
    validate_query(fixed_query)
```

**Common Issues Auto-Fixed**:

| Issue | Detection | Fix |
|-------|-----------|-----|
| Integer Division | `/ without TO_DOUBLE` | Wrap numerator in `TO_DOUBLE()` |
| JOIN After STATS | JOIN appears after aggregation | Reorder JOIN before STATS |
| Missing LIMIT | No LIMIT on non-aggregated query | Add `LIMIT 1000` |
| Lost Fields | Field used after STATS without being in BY | Add to BY clause |

### 7. Agent & Tool Creation
```python
# elastic_agent_builder_client.py
client.create_esql_tool(tool_config)
client.create_agent(agent_config)
```

**Tool Types**:
- **ES|QL Tools**: Parameterized queries with `?param` syntax
- **Index Search Tools**: Natural language search on indices

**Agent Configuration**:
- Custom instructions based on industry/company
- Tool assignment
- Labels for organization

### 8. Validation Loop
```python
# validation_service.py
ValidationService.validate_all_queries(queries)
```
- Tests each query execution
- Captures execution time
- Validates result counts
- Generates validation report

---

## 📋 Critical Implementation Details

### 1. Lookup Index Configuration
**MUST SET** for JOIN operations to work:
```python
settings = {"index.mode": "lookup"}  # Critical!
```

### 2. Integer Division Fix Pattern
```python
# Bad: clicks / impressions
# Good: TO_DOUBLE(clicks) / impressions

# Regex pattern for auto-fix:
pattern = r'(\w+)\s*/\s*(\w+)'
replacement = r'TO_DOUBLE(\1) / \2'
```

### 3. JOIN Ordering Rules
```esql
# CORRECT ORDER:
FROM main_table
| LOOKUP JOIN lookup_table ON key  # JOIN FIRST
| STATS ... BY fields              # THEN AGGREGATE
| WHERE conditions                 # THEN FILTER

# WRONG ORDER (will fail):
FROM main_table
| STATS ... BY fields
| LOOKUP JOIN lookup_table ON key  # Can't JOIN after STATS!
```

### 4. State Persistence Pattern
```python
# GitHub state management for demo continuity
state = {
    "demo_id": demo_id,
    "tasks": task_list,
    "config": demo_config,
    "validation_results": results
}
github_manager.save_demo_state(demo_id, state)
```

### 5. Error Recovery Pattern
```python
for attempt in range(3):
    try:
        result = execute_query(query)
        break
    except QueryError as e:
        query = apply_fixes(query, detect_issues(e))
        if attempt == 2:
            flag_for_manual_review(query)
```

---

## 🛠️ Service Reference

### CustomerResearcher
```python
research_company(company_name: str, department: str) -> CustomerProfile
suggest_demo_focus(profile: CustomerProfile) -> Dict
```

### ScenarioGenerator
```python
generate_scenario(customer_profile: Dict, use_case: str) -> Dict
validate_scenario(scenario: Dict) -> bool
```

### DataGenerator
```python
generate_datasets(scenario: Dict) -> Dict[str, pd.DataFrame]
export_datasets(datasets: Dict, output_dir: str) -> Dict[str, str]
```

### ESQLGenerator
```python
generate_queries(scenario: Dict, datasets: Dict) -> List[Dict]
validate_query(esql: str) -> bool
optimize_query(esql: str) -> str
```

### ValidationService
```python
validate_data_upload(index_name: str, data_df: pd.DataFrame) -> ValidationTask
validate_esql_query(query: Dict) -> ValidationResult
validate_all_queries(queries: List[Dict]) -> Tuple[List[ValidationResult], Dict]
```

### ElasticAgentBuilderClient
```python
create_esql_tool(tool: ESQLTool) -> Dict
create_agent(agent: Agent) -> Dict
converse(agent_id: str, message: str) -> Dict
validate_agent_with_queries(agent_id: str, test_queries: List[str]) -> List[Dict]
```

---

## 🔍 Known Issues & Solutions

### Issue 1: Complex Expression Division
**Problem**: `(revenue - cost) / cost` not fully detected
**Solution**:
```python
# Manual pattern for complex expressions
if "(" in line and "/" in line:
    # Extract expression and apply TO_DOUBLE to entire numerator
    expr = re.search(r'\(([^)]+)\)\s*/\s*(\w+)', line)
    if expr:
        fixed = f"TO_DOUBLE({expr.group(1)}) / {expr.group(2)}"
```

### Issue 2: Multi-Level JOINs
**Problem**: Multiple JOINs need careful ordering
**Solution**:
```esql
FROM main_table
| LOOKUP JOIN table1 ON key1  # All JOINs first
| LOOKUP JOIN table2 ON key2
| WHERE conditions            # Then filters
| STATS ... BY fields         # Then aggregations
```

### Issue 3: Field Loss After Aggregation
**Problem**: Fields disappear after STATS unless in BY clause
**Solution**: Include all needed fields in BY clause or use MAX/MIN to preserve

### Issue 4: Elasticsearch Connection Issues
**Problem**: Local dev without Elasticsearch
**Solution**: Mock mode - generates all artifacts without validation

---

## 🚀 Extension Points

### Adding New Industry Templates
1. Add to `CustomerResearcher.industry_templates`
2. Create scenario in `ScenarioGenerator.scenario_templates`
3. Add data generation pattern in `DataGenerator`
4. Create ES|QL query templates

### Adding New Query Patterns
1. Add template to `ESQLGenerator.query_templates`
2. Add detection logic in `detect_query_issues`
3. Add fix logic in `apply_query_fixes`

### Adding New Data Types
1. Create generator method in `DataGenerator`
2. Add mapping inference logic
3. Update relationship creation logic

---

## 📝 Testing Strategy

### Unit Tests Needed
- [ ] Test each service independently
- [ ] Mock Elasticsearch for offline testing
- [ ] Test query fix patterns

### Integration Tests (Implemented)
- [x] End-to-end demo generation
- [x] Query refinement loop
- [x] Data relationship validation
- [x] Agent configuration generation

### Performance Benchmarks
- Data generation: ~400K records/second
- Query generation: <0.01s per query
- Query validation: <0.1s per query
- Total demo generation: <15 seconds with Elasticsearch

---

## 🔐 Security Considerations

### API Keys
- Never commit to git (use .env file)
- Use environment variables
- Rotate regularly

### GitHub PAT
- Use fine-grained tokens
- Limit to specific repository
- Set expiration dates

### Elasticsearch
- Use API keys, not passwords
- Limit permissions to required indices
- Use HTTPS always

---

## 📊 Metrics & Monitoring

### Success Metrics
- Query first-attempt success rate: Target 90%
- Query post-fix success rate: Target 100%
- Demo generation time: Target <60s
- Data relationship integrity: Must be 100%

### Logging
- All services use Python logging
- Levels: DEBUG, INFO, WARNING, ERROR
- Critical operations logged with timing

---

## 🆘 Troubleshooting Guide

### "Integer division returning 0"
Add `TO_DOUBLE()` to numerator

### "JOIN fails - column not found"
1. Check JOIN is before STATS
2. Verify index has lookup mode
3. Confirm field names match exactly

### "Query timeout"
1. Add LIMIT clause
2. Reduce time range
3. Add WHERE filters early

### "Agent doesn't respond correctly"
1. Check tool descriptions are clear
2. Verify agent instructions are specific
3. Test individual tools first

---

## 🎯 Best Practices

### Data Generation
- Keep reference data under 10K records
- Use realistic value distributions
- Always maintain referential integrity

### Query Generation
- Start simple, add complexity
- Always use TO_DOUBLE for division
- Test with small datasets first

### Agent Creation
- Write clear, specific instructions
- Use descriptive tool names
- Include example questions

### Validation
- Validate early and often
- Log all issues for learning
- Build library of working patterns

---

## 🚦 Production Readiness Checklist

- [x] Core services implemented
- [x] Integration tests passing
- [x] Query auto-fix working
- [x] State persistence implemented
- [x] Error handling in place
- [ ] Full Elasticsearch integration tested
- [ ] Agent Builder API integration tested
- [ ] Performance optimization completed
- [ ] Security review completed
- [ ] Documentation complete

---

## 📚 References

### Elastic Documentation
- [ES|QL Syntax](https://www.elastic.co/docs/reference/query-languages/esql/esql-syntax)
- [Agent Builder APIs](https://www.elastic.co/docs/solutions/search/agent-builder/kibana-api)
- [MCP Server](https://www.elastic.co/docs/solutions/search/agent-builder/mcp-server)

### Internal Documents
- [Self-Improving Architecture](SELF_IMPROVING_ARCHITECTURE.md)
- [Elastic Integration Guide](ELASTIC_AGENT_BUILDER_INTEGRATION.md)
- [Test Strategy](../tests/TEST_STRATEGY.md)
- [Test Results](../tests/TEST_RESULTS.md)

---

*Last Updated: October 21, 2024*
*Version: 1.0.0*