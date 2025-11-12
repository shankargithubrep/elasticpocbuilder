# Parameter Design Patterns for ES|QL Tools

## Overview

This document explains the sophisticated parameter strategy used in Demo Builder for generating Agent Builder ES|QL tools. Understanding when to create parameters vs. when to rely on agent intelligence is critical for building flexible, user-friendly tools.

## The Core Principle

**Custom tools should focus on BUSINESS-SPECIFIC logic. Cross-cutting concerns like temporal filtering should be handled by agents via `platform.core.execute_esql`.**

---

## The Nuanced Strategy

### ✅ CREATE Parameters For:

#### 1. **Business Date Fields**
Date fields that are part of your domain model (NOT @timestamp):

```sql
-- GOOD: Business date parameters
WHERE deployment_date >= ?deploy_start
WHERE hire_date BETWEEN ?hired_from AND ?hired_to
WHERE expiration_date < ?expiry_cutoff
WHERE renewal_date >= ?renewal_after
WHERE launch_date == ?target_launch
```

**Why?** These fields require domain knowledge. Agents can't infer which business date field is relevant without schema understanding.

#### 2. **Domain-Specific Filters**
Fields unique to your business logic:

```sql
-- GOOD: Domain parameters
WHERE category == ?category
WHERE provider_specialty == ?specialty
WHERE network_status == ?status
WHERE priority_level >= ?min_priority
WHERE customer_segment == ?segment
```

**Why?** These values require knowledge of your data schema and business rules.

#### 3. **Schema-Specific Identifiers**
Fields that reference specific entities:

```sql
-- GOOD: Schema parameters
WHERE provider_id == ?provider
WHERE department_id == ?dept
WHERE application_id == ?app
WHERE transaction_type == ?type
```

**Why?** Agents need explicit user input for these values.

---

### ❌ AVOID Parameters For:

#### 1. **@timestamp Filtering** (CRITICAL)
Event timestamps that agents can handle dynamically:

```sql
-- BAD: @timestamp parameters (anti-pattern!)
WHERE @timestamp >= ?start_date  -- ❌ Agent handles this
WHERE @timestamp <= ?end_date    -- ❌ Cross-cutting concern
```

**Why?** Agents have access to `platform.core.execute_esql` which can:
- Add temporal filtering dynamically based on user questions
- Handle natural language time references ("last month", "Q3 2024")
- Modify time ranges without redeploying tools

**Example Agent Behavior:**
```
User: "Show me provider searches for October"

Agent Decision:
1. Uses custom tool: provider_search (business params only)
2. OR uses platform.core.execute_esql to add @timestamp filter:
   WHERE @timestamp >= "2024-10-01" AND @timestamp <= "2024-10-31"
```

#### 2. **Event Timestamp Fields**
Audit fields managed by the system:

```sql
-- BAD: Event timestamp parameters
WHERE created_at >= ?created_start  -- ❌ System timestamp
WHERE updated_at <= ?updated_end     -- ❌ Audit field
WHERE indexed_at >= ?index_start     -- ❌ System metadata
```

**Why?** These behave like @timestamp - universal across all queries.

#### 3. **Generic Operations**
Operations that apply to all queries:

```sql
-- BAD: Generic operation parameters
LIMIT ?limit      -- ❌ Agents can adjust dynamically
SORT ?direction   -- ❌ Not business logic
```

**Why?** Agents can modify these in queries without rigid parameters.

---

## Detection Logic

The system uses sophisticated detection to classify parameters:

### How It Works

```python
# Step 1: Extract field name from query
WHERE deployment_date >= ?deploy_start
# → Field: "deployment_date"

# Step 2: Check if @timestamp
if field_name == "@timestamp":
    return "Skip parameter"  # ❌ Don't create

# Step 3: Check data profile
if field_name in data_profile['fields']:
    if field_type == "datetime64[ns]":
        return "Business date parameter"  # ✅ Create

# Step 4: Check naming patterns
business_patterns = ['deployment', 'hire', 'expiration', 'launch', ...]
if any(pattern in field_name):
    return "Business date parameter"  # ✅ Create
```

### Data Profile Example

```json
{
  "datasets": {
    "infrastructure": {
      "fields": {
        "deployment_date": {
          "type": "datetime64[ns]",  // ← Detects as business date
          "min_date": "2023-01-01",
          "max_date": "2025-01-15"
        },
        "@timestamp": {
          "type": "datetime64[ns]",  // ← Detected as event timestamp
          "min_date": "2024-01-01",
          "max_date": "2025-01-15"
        }
      }
    }
  }
}
```

---

## Real-World Examples

### Example 1: Provider Network Search (Healthcare)

**❌ Anti-Pattern (Over-Parameterized):**
```python
{
    "esql": """
        FROM provider_network
        | WHERE specialty == ?specialty
        | WHERE @timestamp >= ?start_date  // ❌ Bad!
        | WHERE @timestamp <= ?end_date    // ❌ Bad!
        | WHERE network_status == ?status
    """,
    "parameters": {
        "specialty": {"type": "keyword", ...},
        "start_date": {"type": "date", ...},  // ❌ Rigid
        "end_date": {"type": "date", ...},    // ❌ Rigid
        "status": {"type": "keyword", ...}
    }
}
```

**✅ Good Pattern (Business-Focused):**
```python
{
    "esql": """
        FROM provider_network
        | WHERE specialty == ?specialty
        | WHERE network_status == ?status
        | WHERE credential_expiration_date >= ?expires_after  // ✅ Business date!
    """,
    "parameters": {
        "specialty": {"type": "keyword", "description": "Provider specialty"},
        "status": {"type": "keyword", "description": "Network status"},
        "expires_after": {"type": "date", "description": "Credential expiration filter"}
    }
}
```

**Why It's Better:**
- Agents can add `@timestamp` filtering when user asks "show me recent updates"
- Tool focuses on business logic (specialty, network status)
- Business date field (credential_expiration_date) is parameterized because it's domain-specific

---

### Example 2: Infrastructure Cost Analysis

**❌ Anti-Pattern:**
```python
{
    "esql": """
        FROM infrastructure_costs
        | WHERE @timestamp >= ?start_date  // ❌ Bad!
        | WHERE @timestamp <= ?end_date    // ❌ Bad!
        | WHERE environment == ?env
        | STATS total_cost = SUM(cost_usd) BY service
    """,
    "parameters": {
        "start_date": {"type": "date", ...},  // ❌ Unnecessary
        "end_date": {"type": "date", ...},    // ❌ Unnecessary
        "env": {"type": "keyword", ...}
    }
}
```

**✅ Good Pattern:**
```python
{
    "esql": """
        FROM infrastructure_costs
        | WHERE environment == ?env
        | WHERE deployment_type == ?deployment
        | STATS total_cost = SUM(cost_usd) BY service
    """,
    "parameters": {
        "env": {"type": "keyword", "description": "Environment (prod, staging, dev)"},
        "deployment": {"type": "keyword", "description": "Deployment type"}
    }
}
```

**Agent Behavior:**
```
User: "Show me infrastructure costs for production in the last 30 days"

Agent uses:
platform.core.execute_esql("""
    FROM infrastructure_costs
    | WHERE environment == "prod"
    | WHERE @timestamp >= NOW() - 30 days  // ← Agent adds this!
    | STATS total_cost = SUM(cost_usd) BY service
""")
```

---

### Example 3: Employee Management (Business Dates)

**✅ Good Pattern (Business Date Parameters):**
```python
{
    "esql": """
        FROM employees
        | WHERE department == ?dept
        | WHERE hire_date >= ?hired_after      // ✅ Business date
        | WHERE hire_date <= ?hired_before     // ✅ Business date
        | WHERE status == ?status
        | STATS employee_count = COUNT(*) BY role
    """,
    "parameters": {
        "dept": {"type": "keyword", "description": "Department name"},
        "hired_after": {"type": "date", "description": "Hired on or after this date"},
        "hired_before": {"type": "date", "description": "Hired on or before this date"},
        "status": {"type": "keyword", "description": "Employment status"}
    }
}
```

**Why This Is Correct:**
- `hire_date` is a business date field (NOT @timestamp)
- Filtering by hire date is a common business requirement
- Agents can't infer hire date ranges without user input
- User might ask: "Show me employees hired in Q4 2023"

---

## When Date Parameters ARE Appropriate

### Legitimate Use Cases

#### 1. **Semantic Temporal Comparisons**
```sql
-- Comparing specific time periods
WHERE hire_date >= ?q3_2023_start AND hire_date <= ?q3_2023_end
-- vs
WHERE hire_date >= ?q4_2023_start AND hire_date <= ?q4_2023_end
```

The date parameters have **semantic meaning** (Q3 vs Q4), not just filtering.

#### 2. **Complex Date Logic**
```sql
-- Seasonality analysis
WHERE DATE_EXTRACT("month", hire_date) == ?target_month
AND DATE_EXTRACT("year", hire_date) IN ?comparison_years
```

Date parameters are **part of the analytical logic**, not simple filters.

#### 3. **Multi-Temporal Queries**
```sql
-- Current vs prior period comparison
WHERE (deployment_date >= ?current_start AND deployment_date <= ?current_end)
   OR (deployment_date >= ?prior_start AND deployment_date <= ?prior_end)
```

Multiple date ranges with **relationship logic** between them.

---

## Implementation Details

### Files Modified

**1. `src/services/agent_builder_service.py`**
- `_extract_field_from_parameter()`: Extracts field name from query
- `_is_timestamp_parameter()`: Detects @timestamp parameters (skip)
- `_is_business_date_parameter()`: Detects business date fields (create)
- `extract_esql_parameters()`: Orchestrates sophisticated detection

**2. `src/framework/module_generator.py`**
- Updated parameterized query generation prompts
- Removed @timestamp parameter examples
- Added business date field guidance

**3. `src/ui/views/tabs/tools_tab.py`**
- Loads data profile during tool deployment
- Passes data profile to parameter extraction

---

## Migration Guide

### For Existing Demos

**Existing demos with @timestamp parameters will continue to work**, but:
- They represent the anti-pattern
- Future demos will use the nuanced approach
- Consider documenting which demos use old pattern

### For New Demos

**Query generation will now:**
1. Focus on business-specific parameters
2. Avoid @timestamp filtering parameters
3. Create parameters for business date fields only
4. Rely on agents for temporal filtering

---

## FAQs

### Q: Won't users be confused if they can't specify date ranges?
**A:** No! Agents can handle date ranges dynamically when users ask temporal questions. This makes tools MORE flexible, not less.

### Q: What if my query NEEDS a specific time range?
**A:** If it's **business logic** (e.g., "compare Q3 vs Q4"), use parameters. If it's **filtering** (e.g., "last 30 days"), let agents handle it.

### Q: How do I know if a date field is "business" vs "event"?
**A:** Ask: "Is this date part of my domain model?"
- `deployment_date`, `hire_date`, `expiration_date` → Business ✅
- `@timestamp`, `created_at`, `updated_at` → Event ❌

### Q: What about LIMIT parameters?
**A:** Generally avoid. Agents can modify LIMIT dynamically. Exception: If limit is business logic (e.g., "top 10 performers").

---

## Summary

### The Golden Rule

**Create parameters for business-specific logic. Let agents handle cross-cutting concerns.**

### Quick Reference

| Field Type | Example | Parameter? | Why |
|------------|---------|------------|-----|
| @timestamp | `WHERE @timestamp >= ?start` | ❌ NO | Agent handles via execute_esql |
| Event timestamps | `WHERE created_at >= ?start` | ❌ NO | System audit field |
| Business dates | `WHERE hire_date >= ?hired_after` | ✅ YES | Domain-specific logic |
| Domain fields | `WHERE category == ?category` | ✅ YES | Schema knowledge required |
| Generic ops | `LIMIT ?limit` | ❌ NO | Agent can adjust |

### Key Benefits

1. **Flexibility**: Agents can add temporal filtering dynamically
2. **Simplicity**: Tools focus on business logic, not infrastructure
3. **User Experience**: Natural language time references work seamlessly
4. **Maintainability**: Fewer parameters = simpler tool definitions

---

**Last Updated**: 2025-01-12
**Version**: 1.0
**Related Docs**: See `docs/RAG_SEARCH_ARCHITECTURE.md` for query type patterns
