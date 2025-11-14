# Troubleshooting Guide
## Elastic Agent Builder Demo Platform

---

## 🚨 Common Issues and Solutions

### Installation Issues

#### Problem: ModuleNotFoundError when running the app
```
ModuleNotFoundError: No module named 'streamlit'
```

**Solution:**
1. Ensure you're in the virtual environment:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
2. Reinstall dependencies:
```bash
pip install -r requirements.txt
```

#### Problem: GitHub token permission denied
```
Error: Resource not accessible by personal access token
```

**Solution:**
1. Create a new GitHub PAT with correct permissions:
   - Go to GitHub Settings → Developer Settings → Personal Access Tokens
   - Select "Fine-grained personal access tokens"
   - Set repository access to `elastic/demo-builder`
   - Grant permissions:
     - Contents: Read & Write
     - Metadata: Read
2. Update `.env` file with new token

---

### Elasticsearch Connection Issues

#### Problem: Unable to connect to Elasticsearch
```
elasticsearch.exceptions.ConnectionError: Connection refused
```

**Solution:**
1. Verify Elasticsearch is running and accessible
2. Check `.env` configuration:
```env
ELASTICSEARCH_HOST=https://your-instance.elastic.cloud:443
ELASTICSEARCH_API_KEY=your-actual-api-key
```
3. Test connection manually:
```python
from elasticsearch import Elasticsearch
es = Elasticsearch(
    hosts=[os.getenv("ELASTICSEARCH_HOST")],
    api_key=os.getenv("ELASTICSEARCH_API_KEY"),
    verify_certs=True
)
print(es.info())
```

#### Problem: SSL certificate verification failed
```
ssl.SSLError: certificate verify failed
```

**Solution for development only:**
```env
ELASTICSEARCH_VERIFY_CERTS=false
```
**Note:** Never disable certificate verification in production!

---

### ES|QL Query Issues

#### Problem: Integer division returns 0
```esql
-- This returns 0 when clicks < impressions
EVAL ctr = clicks / impressions * 100
```

**Solution:**
Use TO_DOUBLE() on the numerator:
```esql
EVAL ctr = TO_DOUBLE(clicks) / impressions * 100
```

#### Problem: "Unknown column" error on JOIN
```
Error: Unknown column [product_name]
```

**Solutions:**
1. **Check JOIN order** - JOIN must come before aggregation:
```esql
-- Correct:
FROM orders
| LOOKUP JOIN products ON product_id
| STATS total = SUM(amount) BY product_name

-- Wrong:
FROM orders
| STATS total = SUM(amount) BY product_id
| LOOKUP JOIN products ON product_id  -- Too late!
```

2. **Verify lookup index configuration:**
```python
settings = {"index.mode": "lookup"}  # Required for JOIN!
```

#### Problem: Query timeout
```
Error: Query exceeded timeout of 30s
```

**Solutions:**
1. Add LIMIT clause:
```esql
FROM large_dataset
| WHERE condition
| LIMIT 1000
```

2. Add time range filter:
```esql
FROM events
| WHERE timestamp >= NOW() - 7 days
| LIMIT 1000
```

3. Optimize aggregations:
```esql
-- Instead of processing all data:
FROM events
| EVAL calculated_field = complex_calculation

-- Filter first:
FROM events
| WHERE relevant_condition
| EVAL calculated_field = complex_calculation
```

#### Problem: Fields lost after STATS
```esql
FROM data
| STATS count = COUNT(*) BY category
| WHERE product_name == "X"  -- Error: product_name not available
```

**Solution:**
Include needed fields in BY clause:
```esql
FROM data
| STATS count = COUNT(*) BY category, product_name
| WHERE product_name == "X"
```

---

### Data Generation Issues

#### Problem: Foreign key constraint violations
```
Error: Referenced ID 'CUST-999' does not exist
```

**Solution:**
Ensure reference data is generated first:
```python
# Correct order:
customers_df = generate_customers()  # Generate reference data first
orders_df = generate_orders(customers_df)  # Then dependent data
```

#### Problem: Memory error with large datasets
```
MemoryError: Unable to allocate array
```

**Solutions:**
1. Reduce dataset size in scenario:
```python
"datasets": [
    {"name": "events", "records": 10000}  # Instead of 1000000
]
```

2. Generate data in chunks:
```python
chunk_size = 50000
for i in range(0, total_records, chunk_size):
    chunk = generate_chunk(i, min(i + chunk_size, total_records))
    process_chunk(chunk)
```

---

### Agent Builder API Issues

#### Problem: Tool creation fails
```
Error: Invalid ES|QL in tool definition
```

**Solution:**
Validate query before creating tool:
```python
# Test query first
es_client.execute_esql(query)

# Use proper parameter syntax
tool_query = "FROM index | WHERE field == ?param_name"  # Use ? for parameters
```

#### Problem: Agent not responding correctly
```
Agent response: "I don't understand the question"
```

**Solutions:**
1. **Check tool descriptions are clear:**
```python
tool = ESQLTool(
    name="get_customer_metrics",
    description="Returns sales metrics for a specific customer ID",  # Be specific!
    esql="..."
)
```

2. **Provide specific agent instructions:**
```python
agent = Agent(
    name="Sales Analytics Agent",
    instructions="""You help analyze sales data. When asked about:
    - Revenue: Use the 'get_revenue_metrics' tool
    - Customers: Use the 'get_customer_metrics' tool
    - Products: Use the 'get_product_performance' tool
    Always provide specific numbers and trends."""
)
```

---

### Streamlit App Issues

#### Problem: Session state lost on refresh
```
Error: 'st.session_state' has no attribute 'demo_state'
```

**Solution:**
Initialize session state properly:
```python
# In app.py
if 'demo_state' not in st.session_state:
    st.session_state.demo_state = DemoState()
```

#### Problem: UI not updating after action
```
Changes not reflected in UI
```

**Solution:**
Use st.rerun() after state changes:
```python
st.session_state.demo_state.phase = "data_generation"
st.rerun()
```

---

### Performance Issues

#### Problem: Demo generation takes too long
```
Generating demo... (5+ minutes)
```

**Solutions:**
1. **Profile the bottleneck:**
```python
import time
start = time.time()
generate_data()
print(f"Data generation: {time.time() - start}s")
```

2. **Common bottlenecks and fixes:**
   - Data generation: Reduce record counts
   - Elasticsearch indexing: Increase batch size
   - Query validation: Run in parallel

3. **Enable mock mode for testing:**
```env
ENABLE_MOCK_MODE=true
```

---

## 🔍 Debugging Techniques

### Enable Debug Logging
```python
# In your code
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in .env
LOG_LEVEL=DEBUG
```

### Test Individual Components
```python
# Test data generation alone
from src.services.data_generator import DataGenerator
gen = DataGenerator()
datasets = gen.generate_datasets(scenario)
print(f"Generated {len(datasets)} datasets")

# Test query generation
from src.services.esql_generator import ESQLGenerator
esql = ESQLGenerator()
queries = esql.generate_queries(scenario, datasets)
for q in queries:
    print(f"{q['name']}: {esql.validate_query(q['esql'])}")
```

### Validate ES|QL Syntax Locally
```python
def validate_esql_syntax(query):
    """Basic syntax validation without Elasticsearch"""
    required_start = ["FROM", "from"]
    if not any(query.strip().startswith(s) for s in required_start):
        return False, "Query must start with FROM"

    # Check pipe structure
    if query.count("|") != query.count("\n|"):
        return False, "Each pipe should be on a new line"

    return True, "Syntax appears valid"
```

### Monitor Elasticsearch Performance
```bash
# Check cluster health
curl -X GET "${ELASTICSEARCH_HOST}/_cluster/health" \
  -H "Authorization: ApiKey ${ELASTICSEARCH_API_KEY}"

# Check index stats
curl -X GET "${ELASTICSEARCH_HOST}/_stats" \
  -H "Authorization: ApiKey ${ELASTICSEARCH_API_KEY}"
```

---

## 📊 Performance Benchmarks

Expected performance for different operations:

| Operation | Expected Time | If Slower, Check |
|-----------|--------------|------------------|
| Data Generation (100K records) | <1 second | Memory, CPU |
| Index Creation | <2 seconds | Network, ES cluster |
| Data Ingestion (100K) | <10 seconds | Batch size, network |
| Query Generation (10 queries) | <0.1 second | Template complexity |
| Query Execution (simple) | <100ms | Index size, query complexity |
| Query Execution (complex JOIN) | <500ms | Lookup index config |
| Agent Creation | <2 seconds | API rate limits |

---

## 🚦 Health Checks

### Quick System Health Check
```python
def health_check():
    checks = {
        "elasticsearch": False,
        "agent_builder": False,
        "github": False,
        "data_generation": False
    }

    # Check Elasticsearch
    try:
        es_client.info()
        checks["elasticsearch"] = True
    except:
        pass

    # Check Agent Builder
    try:
        agent_client.list_agents()
        checks["agent_builder"] = True
    except:
        pass

    # Check GitHub
    try:
        github_manager.list_demos()
        checks["github"] = True
    except:
        pass

    # Check data generation
    try:
        DataGenerator().generate_datasets({"datasets": [{"name": "test", "records": 10}]})
        checks["data_generation"] = True
    except:
        pass

    return checks
```

---

## 🆘 Getting Help

### Check Logs
1. Application logs: `logs/app.log`
2. Elasticsearch logs: Check Kibana or cloud console
3. Streamlit logs: Terminal where `streamlit run` is running

### Run Integration Tests
```bash
# Test the complete flow
python tests/test_integration.py

# Test query refinement
python tests/test_query_refinement.py
```

### Enable Mock Mode
For testing without external services:
```env
ENABLE_MOCK_MODE=true
```

### Common Commands

#### Reset Demo State
```python
# In Python console
from src.services.github_state_manager import GitHubStateManager
manager = GitHubStateManager()
manager.delete_demo_state("demo_id")
```

#### Clear Elasticsearch Index
```bash
curl -X DELETE "${ELASTICSEARCH_HOST}/index_name" \
  -H "Authorization: ApiKey ${ELASTICSEARCH_API_KEY}"
```

#### Validate Environment
```python
import os
required = ["ELASTICSEARCH_HOST", "ELASTICSEARCH_API_KEY", "GITHUB_TOKEN"]
for var in required:
    value = os.getenv(var)
    print(f"{var}: {'✓' if value else '✗'}")
```

---

## 📝 Reporting Issues

When reporting issues, please include:

1. **Error message and full stack trace**
2. **Environment details:**
   ```bash
   python --version
   pip list | grep -E "streamlit|elasticsearch|pandas"
   ```
3. **Configuration (with secrets redacted):**
   ```bash
   cat .env | sed 's/=.*/=REDACTED/'
   ```
4. **Steps to reproduce**
5. **Expected vs actual behavior**

Report issues at: https://github.com/elastic/demo-builder/issues

---

## 🔮 Prevention Tips

### Before Running Demos
1. Run health check
2. Verify Elasticsearch cluster has space
3. Test with small dataset first
4. Validate all queries locally

### Best Practices
1. Always use virtual environments
2. Keep dependencies up to date
3. Use mock mode for development
4. Test iteratively with small data
5. Monitor Elasticsearch cluster health
6. Set up proper logging
7. Use version control for demo states

### Regular Maintenance
1. Clean up old indices
2. Rotate logs
3. Update API keys before expiry
4. Review and optimize slow queries
5. Archive old demo states

---

*Version: 1.0.0*
*Last Updated: October 21, 2024*