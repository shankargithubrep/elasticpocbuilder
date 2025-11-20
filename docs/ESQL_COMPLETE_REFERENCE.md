# ES|QL Complete Reference for LLM Query Generation

**Version**: 2025-01-14
**Purpose**: Comprehensive ES|QL guidance for LLM-based query generation
**Audience**: General-purpose LLMs tasked with crafting ES|QL queries
**Usage**: Stuff this entire document into your context window for production-quality ES|QL query generation

---

## Table of Contents

1. [Introduction to ES|QL](#introduction-to-esql)
2. [Critical Anti-Patterns (MUST READ FIRST)](#critical-anti-patterns-must-read-first)
3. [20 Critical Syntax Rules](#20-critical-syntax-rules)
4. [Advanced Query Patterns](#advanced-query-patterns)
5. [Safe Query Templates by Type](#safe-query-templates-by-type)
6. [Complete DO's and DON'Ts](#complete-dos-and-donts)
7. [Example-Based Learning](#example-based-learning)
8. [Common Error Patterns & Fixes](#common-error-patterns--fixes)
9. [Query Strategy Guidelines](#query-strategy-guidelines)
10. [Post-Generation Validation Checklist](#post-generation-validation-checklist)

---

## Introduction to ES|QL

**ES|QL** (Elasticsearch Query Language) is a piped query language for Elasticsearch that combines:
- **Full-text search** (MATCH, RERANK, semantic search)
- **Aggregations** (STATS, INLINESTATS)
- **Data enrichment** (LOOKUP JOIN)
- **Transformations** (EVAL, KEEP, DROP)
- **Filtering** (WHERE) and sorting (SORT)

### Key Characteristics

- **Pipe-based syntax**: Commands are chained with `|` like Unix pipes
- **Type-safe**: Strong typing with explicit type conversions (TO_DOUBLE, TO_LONG, etc.)
- **Case-sensitive**: Field names must match exactly
- **Strictly validated**: Errors fail fast, but some anti-patterns produce wrong results silently

### Common Use Cases

1. **Log analysis** and observability
2. **Security/SIEM** queries (authentication, threat detection)
3. **Business analytics** (metrics, KPIs, dashboards)
4. **RAG applications** (semantic search, document retrieval)
5. **Data enrichment** (joining reference data with events)

---

## Critical Anti-Patterns (MUST READ FIRST)

These six anti-patterns are the **most common sources of errors** in LLM-generated ES|QL queries. Read this section FIRST before writing any queries.

### 🚨 1. Integer Division (Silent Wrong Results)

**Problem**: ES|QL performs integer division when dividing two integers, truncating results to 0.

❌ **WRONG** (produces 0 or 100 only):
```esql
| EVAL success_rate = ((total - failures) / total) * 100
```
**Why it fails**: `(95 / 100) = 0` (integer division), then `0 * 100 = 0`

✅ **CORRECT** (produces accurate percentages like 95.7):
```esql
| EVAL success_rate = ((total - failures) / TO_DOUBLE(total)) * 100
```
**Why it works**: `(95 / 100.0) = 0.95`, then `0.95 * 100 = 95.0`

**RULE**: When dividing in EVAL, wrap the denominator in `TO_DOUBLE()` UNLESS:
- You already use `TO_DOUBLE()`: ✓ `field / TO_DOUBLE(total)`
- You multiply by float first: ✓ `field * 100.0 / total`
- You divide by float literal: ✓ `milliseconds / 1000.0`

**Impact**:
- No error thrown
- Produces plausible but wrong results (0 or 100 for percentages)
- Affects ALL percentage calculations, rates, ratios, and manual averages

---

### 🚨 2. NULL Handling with Negative Filters (Silent Data Loss)

**Problem**: ES|QL **excludes documents with NULL/missing fields** from negative filters (`!=`, `NOT`, `NOT LIKE`), causing silent data loss.

❌ **WRONG** (silently excludes docs where field is NULL):
```esql
| WHERE status != "success"
| WHERE NOT(error_type LIKE "*timeout*")
```

✅ **CORRECT** (includes NULL values - complete data):
```esql
| WHERE status != "success" OR status IS NULL
| WHERE NOT(error_type LIKE "*timeout*") OR error_type IS NULL
```

**RULE**: When using negative filters (`!=`, `NOT`, `NOT LIKE`, `NOT IN`), append `OR field IS NULL` UNLESS:
- Field is guaranteed to exist (e.g., `@timestamp`)
- You explicitly want to exclude nulls (rare - document this in description)

**When NULL Handling is CRITICAL**:
- ✅ **Security/SIEM queries**: `auth_result != "success"` must include NULL (missing data = missed threats)
- ✅ **Compliance queries**: `compliance_status != "passed"` should include incomplete records
- ✅ **Analytics**: "not X" typically means "unknown" should be included

**Impact**:
- No error thrown
- Documents with NULL values silently excluded
- Especially dangerous for security queries (missing logs = blind spots)

---

### 🚨 3. @timestamp Parameterization (Poor UX)

**Problem**: Parameterizing `@timestamp` with `?start_date` creates poor user experience.

❌ **WRONG** - Parameterizing system timestamp:
```esql
FROM events
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date  -- ❌ NEVER!
```

✅ **CORRECT** - Use NOW() for @timestamp:
```esql
FROM events
| WHERE @timestamp >= NOW() - 7 days  -- ✅ Relative time with NOW()
```

✅ **CORRECT** - Parameterize BUSINESS date fields instead:
```esql
FROM orders
| WHERE order_date >= ?start_date AND order_date <= ?end_date  -- ✅ Business date
```

**RULE**:
- **NEVER parameterize** `@timestamp` or system fields (`event.ingested`, etc.)
- **USE `NOW() - X days`** for recency queries on `@timestamp`
- **PARAMETERIZE business dates** (`order_date`, `created_at`, `contract_date`, etc.)

**Date Field Classification**:
- ❌ `@timestamp` → System field, use `NOW() - X days`
- ❌ `event.ingested` → System field, use `NOW()` if needed
- ✅ `order_date` → Business field, can parameterize
- ✅ `created_at` → Business field, can parameterize
- ✅ `updated_at` → Business field, can parameterize

---

### 🚨 4. Array Length Anti-Pattern (Data Generation)

**Problem**: Slicing pre-defined pools beyond their length causes index errors in data generation.

This is a **data generation** anti-pattern (not ES|QL syntax), but critical for demos.

❌ **WRONG**:
```python
providers = ["Dr. Smith", "Dr. Jones", "Dr. Brown"]  # Only 3 items
selected = providers[:50]  # ❌ Only returns 3, not 50!
```

✅ **CORRECT**:
```python
providers = ["Dr. Smith", "Dr. Jones", "Dr. Brown"]
selected = np.random.choice(providers, size=50, replace=True)  # ✅ With replacement
```

---

### 🚨 5. LOOKUP JOIN Incomplete ON Clause (Parsing Error)

**Problem**: JOIN ON clause must have complete binary expressions (`field == field`). Partial conditions cause parsing errors.

❌ **WRONG** (incomplete condition after AND):
```esql
| LOOKUP JOIN inventory_snapshots ON store_region == user_geo_region_name AND labels_product_category
```
**Error**: `parsing_exception: JOIN ON clause only supports fields or AND of Binary Expressions, found [labels_product_category]`

**Why it fails**: The condition after `AND` is incomplete - it's just a field name without a comparison operator or value.

✅ **CORRECT** (complete binary expressions):
```esql
| LOOKUP JOIN inventory_snapshots ON store_region == user_geo_region_name AND labels_product_category == product_category
```

**RULE**: Every condition in LOOKUP JOIN ON clause must be a complete binary expression:
- ✅ `field1 == field2`
- ✅ `field1 == field2 AND field3 == field4`
- ❌ `field1 == field2 AND field3` (incomplete!)
- ❌ `field1 AND field2 == field3` (field1 alone is incomplete!)

**Common mistake**: Forgetting the right-hand side of the comparison after AND.

---

### 🚨 6. LOOKUP JOIN Ambiguous Fields (Verification Error)

**Problem**: When the same field name exists in BOTH the main dataset and lookup table, you MUST qualify it in the ON clause to avoid ambiguity.

❌ **WRONG** (ambiguous field reference):
```esql
FROM search_queries
| LOOKUP JOIN inventory_snapshots ON labels_product_category == search_query_category AND store_region == client_geo_region_name
```
**Error**: `verification_exception: Found ambiguous reference to [labels_product_category]; matches any of [line 9:15 [labels_product_category], line 10:15 [labels_product_category]]`

**Why it fails**: If `labels_product_category` exists in BOTH `search_queries` AND `inventory_snapshots`, ES|QL doesn't know which one you mean in the JOIN condition.

✅ **CORRECT** - Option 1 (rename field in one dataset during data generation):
```python
# In data generator - ensure unique field names across datasets
search_queries_df['query_category'] = ...  # Different name than lookup table
inventory_df['product_category'] = ...     # Different name than main dataset
```
```esql
FROM search_queries
| LOOKUP JOIN inventory_snapshots ON query_category == product_category
```

✅ **CORRECT** - Option 2 (use different field entirely):
```esql
FROM search_queries
| LOOKUP JOIN inventory_snapshots ON category_id == category_id  -- Use ID fields instead
```

**RULE**:
- **Best practice**: Use UNIQUE field names between main dataset and lookup tables (e.g., `order_status` vs `status_name`)
- **Avoid**: Fields with identical names in both tables unless they're the JOIN key
- **JOIN keys**: Can have same name (e.g., `product_id` in both), but other fields should differ

**Impact**:
- Prevents ambiguous field errors
- Makes queries more readable
- Avoids needing field qualification (which doesn't work in LOOKUP JOIN)

---

## 20 Critical Syntax Rules

### 1. LOOKUP JOIN - NO SUFFIX, NO PREFIX ⚠️⚠️ CRITICAL

**Rule**: After LOOKUP JOIN, reference fields **DIRECTLY** without any prefix.

✅ **CORRECT**:
```esql
FROM claims
| LOOKUP JOIN providers ON provider_id
| STATS count = COUNT(*) BY specialty              -- Just "specialty", no prefix!
| KEEP claim_id, provider_name, specialty          -- Just "provider_name"
```

❌ **WRONG**:
```esql
FROM claims
| LOOKUP JOIN providers ON provider_id
| STATS count = COUNT(*) BY providers.specialty     -- ❌ ERROR: Unknown column
| KEEP claim_id, providers.provider_name            -- ❌ ERROR: Unknown column
```

**Why it fails**: Elasticsearch interprets `providers.specialty` as a dataset reference and looks for `providers_lookup.specialty`, which doesn't exist.

**Also WRONG**:
- ❌ `| LOOKUP JOIN providers_lookup ON id` - Never use `_lookup` suffix
- ❌ Using `ENRICH` instead of `LOOKUP JOIN` - LOOKUP JOIN is the modern approach

---

### 2. MATCH Syntax - ALWAYS WITHIN WHERE ⚠️

**Rule**: MATCH is a function called **within WHERE clause**, not a pipe operation.

✅ **CORRECT**:
```esql
| WHERE MATCH(field, "search term")
| WHERE MATCH(field, ?parameter)
| WHERE MATCH(field, ?query, {"boost": 2.0, "fuzziness": "AUTO"})
```

❌ **WRONG**:
```esql
| MATCH field "term"                    -- ❌ MATCH is NOT a pipe operation
| MATCH title, content WITH ?query      -- ❌ Invalid syntax
| MATCH (field) ?query                  -- ❌ Invalid syntax
```

**For multiple fields**, use OR:
```esql
| WHERE MATCH(title, ?query) OR MATCH(content, ?query)
```

---

### 3. FORK Syntax - NO NAMED BRANCHES ⚠️

**Rule**: FORK branches are **unnamed** and cannot be assigned to variables.

✅ **CORRECT**:
```esql
| FORK
  (WHERE category == "A" | STATS count = COUNT(*))
  (WHERE category == "B" | STATS count = COUNT(*))
```

❌ **WRONG**:
```esql
| FORK
  branch_a = (...)  -- ❌ NO NAMED BRANCHES!
  branch_b = (...)
```

❌ **ALSO WRONG**: Comments inside FORK branches can cause parsing errors.

---

### 4. Query Parameters - CANNOT CHECK NULL ⚠️

**Rule**: Parameters are **ALWAYS required** when used. No NULL checking or optional logic.

❌ **WRONG**:
```esql
| WHERE ?param IS NULL                        -- ❌ Cannot check if parameter is NULL
| WHERE field == ?param OR ?param IS NULL     -- ❌ Invalid pattern
| WHERE COALESCE(?param, "default") == field  -- ❌ Won't work
```

**If optional behavior is needed**:
- Create **separate scripted queries** (no parameters)
- Create **separate parameterized queries** (with required parameters)
- Do NOT attempt conditional parameter logic

---

### 5. RERANK Syntax - Pipe Operation ⚠️

✅ **CORRECT**:
```esql
| RERANK "query" ON field
| RERANK ?question ON content
```

❌ **WRONG**:
```esql
| RERANK semantic_text WITH ?query    -- ❌ Wrong syntax
| RERANK field WITH query             -- ❌ Wrong syntax
| WHERE RERANK(...)                   -- ❌ RERANK is a pipe operation, not a function
```

---

### 6. COUNT_DISTINCT Syntax ⚠️⚠️ VERY COMMON ERROR

**Rule**: ES|QL uses `COUNT_DISTINCT()` as a **single function**, NOT SQL's `COUNT(DISTINCT ...)`.

✅ **CORRECT**:
```esql
| STATS unique_users = COUNT_DISTINCT(user_id)
```

❌ **WRONG**:
```esql
| STATS unique_users = COUNT(DISTINCT user_id)  -- ❌ SQL syntax doesn't work
```

**This is a VERY COMMON mistake**. Remember: `COUNT_DISTINCT()` not `COUNT(DISTINCT ...)`.

---

### 7. INLINESTATS Syntax - Single BY Clause ⚠️⚠️ VERY COMMON ERROR

**Rule**: INLINESTATS uses **ONE BY clause at the end** (just like STATS), NOT one BY clause per aggregation.

✅ **CORRECT**:
```esql
| INLINESTATS avg_val = AVG(value), max_val = MAX(value) BY category
```

❌ **WRONG**:
```esql
| INLINESTATS avg_val = AVG(value) BY category, max_val = MAX(value) BY category
```

**Think of INLINESTATS like STATS** - the BY clause applies to ALL aggregations together.

---

### 8. STATS Conditional Aggregation ⚠️

✅ **CORRECT** (ES|QL 8.13+):
```esql
| STATS denied = COUNT(*) WHERE status == "denied"
| STATS high_risk = COUNT(*) WHERE risk > 0.8
```

✅ **CORRECT** (all versions):
```esql
| STATS denied = SUM(CASE(status == "denied", 1, 0))
```

❌ **WRONG**:
```esql
| STATS denied = COUNT_IF(status == "denied")     -- ❌ No COUNT_IF function
| STATS denied = COUNT(CASE(...))                 -- ❌ Use SUM(CASE(...))
```

---

### 9. DATE Functions - Parameter Order ⚠️

**Rule**: Interval/format **first**, field **second**.

✅ **CORRECT**:
```esql
| EVAL bucket = DATE_TRUNC(1 hour, @timestamp)
| EVAL month = DATE_EXTRACT("month", @timestamp)
```

❌ **WRONG**:
```esql
| EVAL bucket = DATE_TRUNC(@timestamp, 1 hour)       -- ❌ Wrong order
| EVAL month = DATE_EXTRACT(@timestamp, "month")     -- ❌ Wrong order
```

---

### 10. Index Modes for LOOKUP JOIN ⚠️ CRITICAL

**Rule**: Target index MUST be in **lookup mode** for LOOKUP JOIN.

**Index Mode Requirements**:
- **Data Streams** (`.ds-*` prefix) = Standard mode → **CANNOT** be used with LOOKUP JOIN
- **Lookup Indices** = Lookup mode → **REQUIRED** for LOOKUP JOIN

**Dataset Type Mapping**:
- `type: "timeseries"` → Create as data_stream (for events, logs, interactions)
- `type: "reference"` → Create as lookup index (for members, providers, products)

**Common Error**:
```
"Lookup Join requires a single lookup mode index; [members] resolves to [.ds-members-2025.11.03-000001] in [standard] mode"
```

**This means**: `members` was incorrectly created as a data stream. Reference datasets MUST be created as lookup indices, not data streams. You **CANNOT fix this in the query** - the index creation mode must be corrected.

---

### 11. Field Names - Case Sensitive ⚠️

- Use `@timestamp` for time fields (not `timestamp`)
- Field names are **CASE SENSITIVE** and must match exactly
- Never invent field names - use **only fields from the schema**
- After STATS, only **grouped fields and calculated fields** are available

---

### 12. Date Arithmetic - ALWAYS Use TO_LONG() ⚠️⚠️ CRITICAL

**Rule**: You **CANNOT subtract datetime values directly**. Always wrap both sides in `TO_LONG()` first.

✅ **CORRECT**:
```esql
| EVAL days_diff = (TO_LONG(NOW()) - TO_LONG(last_updated)) / 86400000
| EVAL hours_diff = (TO_LONG(end_time) - TO_LONG(start_time)) / 3600000
```

❌ **WRONG**:
```esql
| EVAL days_diff = (NOW() - last_updated) / 86400000        -- ❌ Type error
| EVAL hours = (end_time - start_time) / 3600000            -- ❌ Type error
```

**Common Error**: `[-] has arguments with incompatible types [datetime] and [datetime]`

**Time Constants**:
- 1 second = 1,000 milliseconds
- 1 minute = 60,000 milliseconds
- 1 hour = 3,600,000 milliseconds
- 1 day = 86,400,000 milliseconds

---

### 13. Division and Type Casting ⚠️

**See Critical Anti-Pattern #1 above** - Always use `TO_DOUBLE()` for division.

✅ **CORRECT**:
```esql
| EVAL rate = TO_DOUBLE(numerator) / denominator
| EVAL pct = numerator * 100.0 / denominator       -- Multiply by float first
| EVAL seconds = milliseconds / 1000.0             -- Divide by float literal
```

❌ **WRONG**:
```esql
| EVAL rate = numerator / denominator  -- ❌ Integer division loses precision
```

---

### 14. LOOKUP JOIN Schema Validation ⚠️⚠️⚠️ CRITICAL - CANNOT BE AUTO-FIXED

**Rule**: The join key **MUST exist in BOTH datasets**.

**Common Error**: `Unknown column [field_name] in right/left side of join`

This is the **MOST COMMON failure** that CANNOT be automatically fixed.

**Error Messages**:
- `"Unknown column [product_references] in right side of join"` → Join key missing in lookup dataset
- `"Unknown column [product_id] in left side of join"` → Join key missing in source dataset

**PREVENTION STRATEGY**:

Before writing ANY LOOKUP JOIN query, you MUST:
1. ✅ Verify the join key exists in the **source dataset schema** (FROM dataset)
2. ✅ Verify the join key exists in the **lookup dataset schema**
3. ✅ Use the **EXACT field name** (case-sensitive) from both schemas
4. ❌ NEVER invent, assume, or guess join key names

✅ **CORRECT**:
```esql
-- FIRST: Verify 'user_id' exists in BOTH events schema AND users schema
FROM events
| LOOKUP JOIN users ON user_id  -- ✅ Only works if user_id is in BOTH
| STATS count = COUNT(*) BY tier
```

❌ **WRONG** (WILL FAIL):
```esql
FROM pages
| LOOKUP JOIN products ON product_references  -- ❌ Assumes field exists - probably doesn't
```

**When You See This Error**:
- It means the schema doesn't support the join you're trying to do
- Auto-fix **CANNOT** resolve this - it requires data model changes
- You must either: use a different join key that exists in both, or abandon the join

---

### 15. COMPLETION Syntax (RAG Queries) ⚠️

✅ **CORRECT**:
```esql
| COMPLETION "prompt" WITH ?user_question
```

❌ **WRONG**:
```esql
| COMPLETION "prompt" ON field  -- ❌ Wrong syntax
```

**Note**: COMPLETION may not be available in all Elasticsearch versions.

---

### 16. Time Filtering - Different Patterns for Scripted vs Parameterized ⚠️⚠️ CRITICAL

**See Critical Anti-Pattern #3 above** for full details.

**The Problem**: Demo data is static with fixed timestamps. Using `NOW()` in scripted queries will return NO RESULTS.

**SCRIPTED QUERIES** (no parameters, for exploration):
- ❌ WRONG: `WHERE @timestamp > NOW() - 7 days` - Will return empty results
- ✅ CORRECT: **OMIT time filters entirely** - Let users control time via Kibana time picker

**PARAMETERIZED QUERIES** (user-facing tools):
- ✅ CORRECT: `WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date`
- ✅ CORRECT: Use parameters for user-controlled time filtering

**Rule**:
- Scripted queries: **NO `@timestamp` filters** (rely on Kibana time picker)
- Parameterized queries: Use `?start_date` and `?end_date` parameters

---

### 17. EVAL Variable Reuse - CANNOT Use Newly Defined Variables in Same Command ⚠️⚠️ CRITICAL

**Rule**: Variables defined in an EVAL command are **NOT available** to other expressions in the SAME EVAL.

❌ **WRONG** - Using variable defined in same EVAL:
```esql
| EVAL
    z_score = (count - avg) / stddev,
    multi_host = CASE(hosts >= 2, 1, 0),
    storm_prob = z_score * multi_host  -- ❌ ERROR: Unknown column [z_score]
```

✅ **CORRECT** - Use separate EVAL commands:
```esql
| EVAL
    z_score = (count - avg) / stddev,
    multi_host = CASE(hosts >= 2, 1, 0)
| EVAL storm_prob = z_score * multi_host  -- ✅ Now z_score is available
```

**Why This Fails**: ES|QL evaluates all expressions in an EVAL simultaneously, so variables aren't available to each other within the same command.

**Exception**: You CAN reference existing fields from previous commands:
```esql
| EVAL
    total = field_a + field_b,      -- ✅ field_a, field_b exist from source
    avg = (field_a + field_b) / 2   -- ✅ field_a, field_b exist (but NOT total!)
```

---

### 18. @timestamp Parameterization - NEVER Parameterize System Timestamp ⚠️⚠️ CRITICAL

**See Critical Anti-Pattern #3 above** for full details.

❌ **WRONG**:
```esql
FROM purchase_transactions
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date  -- ❌ NEVER!
```

✅ **CORRECT**:
```esql
FROM purchase_transactions
| WHERE @timestamp >= NOW() - 7 days  -- ✅ Relative time with NOW()
```

✅ **CORRECT** - Parameterize business dates:
```esql
FROM orders
| WHERE order_date >= ?start_date AND order_date <= ?end_date  -- ✅ Business date
```

---

### 19. Experimental Features ⚠️

These may fail depending on ES version:
- `CHANGE_POINT` - Use INLINESTATS with z-score calculation instead
- `LAG/LEAD` - Window functions may not be supported
- `SEMANTIC` - Use MATCH with semantic_text fields instead

---

### 20. NULL Handling with Negative Filters ⚠️⚠️ CRITICAL - SILENT DATA LOSS

**See Critical Anti-Pattern #2 above** for full details.

✅ **CORRECT**:
```esql
FROM logs
| WHERE status != "success" OR status IS NULL
```

❌ **WRONG**:
```esql
FROM logs
| WHERE status != "success"  -- ❌ Silently excludes docs with status=NULL
```

**Common Patterns**:
```esql
-- Security: Find non-successful authentications
| WHERE auth_result != "success" OR auth_result IS NULL

-- Analytics: Find non-active users
| WHERE user_status != "active" OR user_status IS NULL

-- Compliance: Find non-compliant records
| WHERE NOT(compliance_status == "passed") OR compliance_status IS NULL

-- Pattern matching: Find unusual errors
| WHERE NOT(error_code LIKE "E-200*") OR error_code IS NULL
```

---

### 21. Standard Deviation Function - STD_DEV not STDEV ⚠️⚠️ COMMON ERROR

**Problem**: ES|QL uses `STD_DEV()` for standard deviation, NOT `STDEV()` or `STDDEV()`.

✅ **CORRECT**:
```esql
FROM metrics
| STATS avg_value = AVG(metric), stddev_value = STD_DEV(metric) BY category
| EVAL z_score = (metric - avg_value) / COALESCE(stddev_value, 1)
```

✅ **CORRECT - In INLINESTATS**:
```esql
FROM events
| INLINESTATS avg_count = AVG(count), stddev_count = STD_DEV(count) BY region
| EVAL anomaly_score = (count - avg_count) / COALESCE(stddev_count, 1)
```

❌ **WRONG - STDEV does not exist**:
```esql
| STATS stddev_value = STDEV(metric) BY category    -- ❌ ERROR: Unknown function [STDEV]
```

❌ **WRONG - STDDEV also does not exist**:
```esql
| STATS stddev_value = STDDEV(metric) BY category   -- ❌ ERROR: Unknown function [STDDEV]
```

**The ONLY correct function name is `STD_DEV()`** with underscore.

**Common Use Cases**:
- **Z-score anomaly detection**: `(value - avg) / stddev > 3`
- **Statistical analysis** with INLINESTATS for per-group statistics
- **Outlier identification** beyond N standard deviations
- **Variability measurement** in time-series data

**Related Functions**:
- `STD_VAR()` - Standard variance (also uses underscore!)
- `AVG()` - Average/mean
- `PERCENTILE()` - For percentile-based thresholds

---

## Advanced Query Patterns

### LOOKUP JOIN - Data Enrichment

**Purpose**: Enrich streaming/event data with dimensional/reference data

**CRITICAL**: After LOOKUP JOIN, reference fields **WITHOUT any prefix**!

```esql
FROM events
| LOOKUP JOIN dimension_table ON join_key
| WHERE tier == "VIP"                              -- ✅ No prefix!
| STATS revenue = SUM(amount) BY segment            -- ✅ No prefix!
```

**Pattern**:
1. Main dataset (events, transactions, logs)
2. JOIN with reference data (users, products, providers)
3. Access enriched fields directly
4. Filter and aggregate using any field from either dataset

**Example**:
```esql
FROM purchase_transactions
| LOOKUP JOIN customers ON customer_id
| LOOKUP JOIN products ON product_id
| STATS
    total_revenue = SUM(amount),
    avg_order = AVG(amount),
    unique_customers = COUNT_DISTINCT(customer_id)
  BY product_category, customer_tier
| SORT total_revenue DESC
```

---

### INLINESTATS - Keep All Rows While Aggregating

**Purpose**: Add aggregate calculations without grouping (keeps all original rows)

**CRITICAL**: Use **ONE BY clause at the end** for all aggregations!

```esql
FROM transactions
| INLINESTATS
    avg_amount = AVG(amount),
    max_amount = MAX(amount),
    total_count = COUNT(*)
  BY category
| EVAL variance_from_avg = amount - avg_amount
| WHERE variance_from_avg > 1000
```

**Use Cases**:
- **Anomaly detection**: Compare individual values to group averages
- **Ranking within groups**: Identify top/bottom performers
- **Z-score calculation**: Statistical outlier detection
- **Percentage of total**: Individual contribution to group sum

**Example - Anomaly Detection**:
```esql
FROM metrics
| EVAL hour = DATE_TRUNC(1 hour, @timestamp)
| STATS value = AVG(metric) BY hour
| INLINESTATS
    mean_value = AVG(value),
    stddev_value = STDDEV(value)
| EVAL z_score = (value - mean_value) / stddev_value
| WHERE z_score > 3 OR z_score < -3
| SORT @timestamp DESC
```

---

### FORK - Parallel Analysis Paths

**Purpose**: Split pipeline for multiple analyses, then combine results

**CRITICAL**: No named branches, no comments inside branches!

```esql
FROM events
| FORK
  (WHERE type == "error" | STATS errors = COUNT(*))
  (WHERE type == "warning" | STATS warnings = COUNT(*))
  (STATS total = COUNT(*))
```

**Use Cases**:
- **Multi-category comparison**: Analyze different segments simultaneously
- **Before/after comparison**: Compare time periods in parallel
- **Multiple aggregation strategies**: Different groupings of same data

**Example**:
```esql
FROM sales
| FORK
  (STATS total_revenue = SUM(amount) BY region)
  (STATS avg_order_value = AVG(amount) BY product_category)
  (STATS daily_sales = SUM(amount) BY DATE_TRUNC(1 day, @timestamp))
```

---

### Multi-Field Search Pattern

**Purpose**: Search across multiple fields with different relevance boosts

```esql
FROM knowledge_base
| WHERE MATCH(title, ?query, {"boost": 2.0})
     OR MATCH(content, ?query, {"boost": 1.0})
     OR MATCH(tags, ?query, {"boost": 1.5})
| SORT _score DESC
| LIMIT 10
```

**Boosting Strategy**:
- Higher boost = more relevance
- Title: 2.0 (most important)
- Content: 1.0 (baseline)
- Tags: 1.5 (metadata)

---

### Semantic Search Pipeline (MATCH → RERANK → COMPLETION)

**Purpose**: Full RAG (Retrieval-Augmented Generation) pipeline

```esql
FROM knowledge_base
| WHERE MATCH(content, ?user_question, {"fuzziness": "AUTO"})
| WHERE category IN ["policy", "procedure", "faq"]
| RERANK ?user_question ON content
| KEEP article_id, title, content, last_updated, _score
| SORT _score DESC
| LIMIT 5
| COMPLETION "Answer the question based on these articles" WITH ?user_question
```

**Pipeline Stages**:
1. **MATCH**: Initial retrieval (cast wide net)
2. **RERANK**: Semantic re-scoring (narrow to best matches)
3. **COMPLETION**: LLM generation with context

---

### Multi-Lag Analysis for Sustained Patterns

**Purpose**: Detect patterns that persist over multiple time periods (not just transient spikes)

```esql
FROM events
| EVAL hour = DATE_TRUNC(1 hour, @timestamp)
| STATS count = COUNT(*), unique_hosts = COUNT_DISTINCT(host) BY hour
| INLINESTATS
    avg_count = AVG(count),
    stddev_count = STDDEV(count)
| EVAL
    z_score = (count - avg_count) / stddev_count,
    multi_host = CASE(unique_hosts >= 2, 1, 0)
| EVAL storm_score = z_score * multi_host
| WHERE storm_score > 2
| SORT hour DESC
```

**Why Multi-Lag Matters**:
- Filters out transient spikes (single host, single hour)
- Identifies sustained patterns (multiple hosts, multiple hours)
- Useful for DDoS detection, campaign analysis, outbreak monitoring

---

## Safe Query Templates by Type

### 1. Scripted Query (No Parameters, Testable)

**Use For**: Testing, exploration, fixed analysis

```esql
FROM transactions
| WHERE status == "pending"
| LOOKUP JOIN products ON product_id
| STATS
    total = COUNT(*),
    avg_amount = AVG(amount),
    max_amount = MAX(amount)
  BY category
| SORT total DESC
| LIMIT 20
```

**Key Characteristics**:
- No parameters (hard-coded values)
- **NO `@timestamp` filter** - users control time via Kibana time picker
- Can be tested immediately
- Type: `"scripted"`

---

### 2. Parameterized Query (Required Parameters Only)

**Use For**: User-facing tools, Agent Builder agents, API endpoints

```esql
FROM customers
| WHERE region == ?region
| WHERE segment == ?segment
| STATS
    customer_count = COUNT(*),
    avg_revenue = AVG(total_revenue)
  BY plan_type
| SORT customer_count DESC
```

**Key Characteristics**:
- All parameters are **REQUIRED** (no NULL checking)
- Use `?parameter_name` syntax
- **Parameterize business dates**, not `@timestamp`
- Type: `"parameterized"`

**With Time Filtering**:
```esql
FROM orders
| WHERE order_date >= ?start_date AND order_date <= ?end_date  -- Business date!
| WHERE region == ?region
| STATS total_orders = COUNT(*), revenue = SUM(amount) BY product_category
```

---

### 3. RAG Query (Semantic Search + LLM)

**Use For**: Document retrieval, knowledge base search, Q&A systems

```esql
FROM knowledge_base
| WHERE MATCH(content, ?user_question, {"fuzziness": "AUTO"})
| WHERE category IN ["policy", "procedure", "faq"]
| KEEP article_id, title, content, last_updated, _score
| SORT _score DESC
| LIMIT 5
```

**Full RAG Pipeline with COMPLETION**:
```esql
FROM knowledge_base
| WHERE MATCH(content, ?user_question)
| RERANK ?user_question ON content
| LIMIT 3
| COMPLETION "Answer based on these documents" WITH ?user_question
```

**Key Characteristics**:
- Uses `MATCH` for full-text search
- Optional `RERANK` for semantic re-scoring
- Optional `COMPLETION` for LLM generation
- Type: `"parameterized"` (requires `?user_question`)

---

### 4. Complex Aggregation with Enrichment (Scripted)

**Use For**: Analytics dashboards, KPI reports, multi-dimensional analysis

```esql
FROM call_events
| LOOKUP JOIN agents ON agent_id
| LOOKUP JOIN customers ON customer_id
| STATS
    call_count = COUNT(*),
    avg_duration = AVG(duration_seconds),
    resolved = COUNT(*) WHERE status == "resolved"
  BY team, tier, segment
| EVAL resolution_rate = TO_DOUBLE(resolved) * 100.0 / call_count
| WHERE call_count > 10
| SORT resolution_rate DESC
```

**Key Characteristics**:
- Multiple LOOKUP JOINs for enrichment
- Calculated fields (EVAL)
- Multi-dimensional grouping (BY team, tier, segment)
- **No `@timestamp` filter** - Kibana controls time range

---

## Complete DO's and DON'Ts

### ✅ DO's

1. **ALWAYS validate field names** against the actual schema before using them
2. **ALWAYS verify LOOKUP JOIN keys exist in BOTH** source AND lookup dataset schemas (CRITICAL!)
3. **ALWAYS use TO_LONG()** when subtracting datetime values
4. **ALWAYS use TO_DOUBLE()** when dividing aggregated fields (for percentages, rates, ratios)
5. **ALWAYS include `OR field IS NULL`** with negative filters (!=, NOT, NOT LIKE) unless explicit
6. **ALWAYS use @timestamp** for time fields (not `timestamp`)
7. **ALWAYS put MATCH inside WHERE clause** (`WHERE MATCH(field, query)`)
8. **ALWAYS check index mode compatibility** for LOOKUP JOIN (lookup mode required)
9. **ALWAYS omit `@timestamp` filters** in SCRIPTED queries (let Kibana time picker control range)
10. **ALWAYS use `?start_date` and `?end_date`** parameters for time filtering in PARAMETERIZED queries
11. **ALWAYS use `NOW() - X days`** for recency queries on `@timestamp`
12. **ALWAYS use separate EVAL commands** if you need to reference newly defined variables
13. **ALWAYS use DATE_TRUNC** for time-series bucketing (not DATE_EXTRACT)
14. **ALWAYS use COUNT_DISTINCT()** as a single function (not COUNT(DISTINCT ...))
15. **ALWAYS use ONE BY clause** at the end of INLINESTATS (applies to all aggregations)

---

### ❌ DON'Ts

1. **NEVER use table prefixes** after LOOKUP JOIN (use `specialty` not `providers.specialty`)
2. **NEVER add `_lookup` suffix** to index names
3. **NEVER invent or assume LOOKUP JOIN keys** - verify they exist in BOTH schemas first
4. **NEVER subtract datetime values directly** - always use `TO_LONG()` wrapper
5. **NEVER parameterize `@timestamp`** - use `NOW() - X days` or parameterize business dates
6. **NEVER check if parameters are NULL** - parameters are always required
7. **NEVER use named branches in FORK** - branches are unnamed
8. **NEVER put comments inside FORK branches** - can cause parsing errors
9. **NEVER use MATCH as a pipe operation** - it's a function within WHERE
10. **NEVER assume fields exist after STATS** without including in GROUP BY
11. **NEVER use COUNT_IF or other non-existent functions**
12. **NEVER use SQL syntax** like `COUNT(DISTINCT field)` - use `COUNT_DISTINCT(field)`
13. **NEVER use multiple BY clauses in INLINESTATS** - use ONE BY clause for all aggregations
14. **NEVER use `NOW()` in SCRIPTED queries** - omit time filters entirely
15. **NEVER use window functions** (LAG, LEAD, OVER, ROW_NUMBER, RANK) - use INLINESTATS instead
16. **NEVER divide integers without TO_DOUBLE()** - produces truncated results
17. **NEVER use negative filters without NULL checks** - causes silent data loss
18. **NEVER use DATE_EXTRACT for bucketing** - use DATE_TRUNC instead
19. **NEVER use ENRICH** - use LOOKUP JOIN instead (modern approach)
20. **NEVER use field names that don't exist in the schema** - always verify first

---

## Example-Based Learning

### Example 1: INLINESTATS for Anomaly Detection

**Use Case**: Detect metrics that deviate from the group average

```esql
FROM transactions
| EVAL hour = DATE_TRUNC(1 hour, @timestamp)
| STATS hourly_amount = SUM(amount) BY hour, region
| INLINESTATS
    avg_hourly = AVG(hourly_amount),
    stddev_hourly = STDDEV(hourly_amount)
  BY region
| EVAL z_score = (hourly_amount - avg_hourly) / stddev_hourly
| WHERE z_score > 3 OR z_score < -3
| KEEP hour, region, hourly_amount, z_score
| SORT z_score DESC
```

**What it does**:
- Groups transactions by hour and region
- Calculates average and standard deviation for each region
- Computes z-score for each hour
- Filters to outliers (|z| > 3)

---

### Example 2: LOOKUP JOIN Enrichment

**Use Case**: Enrich transaction data with customer and product information

```esql
FROM purchase_transactions
| LOOKUP JOIN customers ON customer_id
| LOOKUP JOIN products ON product_id
| WHERE customer_tier == "VIP" OR customer_tier IS NULL
| STATS
    total_revenue = SUM(amount),
    transaction_count = COUNT(*),
    avg_transaction = AVG(amount)
  BY product_category, customer_segment
| EVAL avg_transaction = TO_DOUBLE(total_revenue) / transaction_count
| WHERE transaction_count > 10
| SORT total_revenue DESC
| LIMIT 20
```

**What it does**:
- Enriches transactions with customer tier and product category
- Filters to VIP customers (includes NULL for missing data)
- Aggregates by category and segment
- Calculates average transaction value using TO_DOUBLE()
- Filters to statistically significant groups

---

### Example 3: Multi-Lag Sustained Pattern Detection

**Use Case**: Find events that persist across multiple hosts and time periods

```esql
FROM security_events
| EVAL hour = DATE_TRUNC(1 hour, @timestamp)
| STATS
    event_count = COUNT(*),
    unique_hosts = COUNT_DISTINCT(host),
    unique_users = COUNT_DISTINCT(user)
  BY hour, event_type
| INLINESTATS
    avg_events = AVG(event_count),
    stddev_events = STDDEV(event_count)
  BY event_type
| EVAL
    z_score = (event_count - avg_events) / stddev_events,
    multi_host = CASE(unique_hosts >= 3, 1, 0),
    multi_user = CASE(unique_users >= 2, 1, 0)
| EVAL threat_score = z_score * multi_host * multi_user
| WHERE threat_score > 2
| SORT threat_score DESC, hour DESC
| LIMIT 50
```

**What it does**:
- Detects event spikes (z-score > threshold)
- Filters to multi-host, multi-user patterns (not single-source)
- Calculates composite threat score
- Identifies sustained threats, not transient spikes

---

### Example 4: Zero Division Protection

**Use Case**: Safely calculate percentages when denominator might be zero

```esql
FROM campaigns
| STATS
    impressions = SUM(impression_count),
    clicks = SUM(click_count),
    conversions = SUM(conversion_count)
  BY campaign_id, channel
| EVAL
    ctr = CASE(impressions > 0, TO_DOUBLE(clicks) / impressions * 100, 0),
    cvr = CASE(clicks > 0, TO_DOUBLE(conversions) / clicks * 100, 0)
| WHERE impressions > 100
| SORT cvr DESC
```

**What it does**:
- Uses CASE to check denominator > 0 before division
- Uses TO_DOUBLE() for accurate percentage calculation
- Filters to statistically significant campaigns
- Returns 0 instead of error when denominator is 0

---

### Example 5: Semantic Search Pipeline (RAG)

**Use Case**: Find relevant documents and generate answers using LLM

```esql
FROM knowledge_base
| WHERE MATCH(content, ?user_question, {"fuzziness": "AUTO"})
     OR MATCH(title, ?user_question, {"boost": 2.0})
| WHERE category IN ["policy", "procedure", "faq"]
| WHERE doc_status == "published" OR doc_status IS NULL
| RERANK ?user_question ON content
| KEEP article_id, title, content, category, last_updated, _score
| SORT _score DESC
| LIMIT 5
| COMPLETION "Answer the user's question based on these knowledge base articles. Be concise and cite sources." WITH ?user_question
```

**What it does**:
- Searches across content and title (title boosted 2x)
- Filters to specific categories and published status
- Re-ranks using semantic similarity
- Returns top 5 most relevant documents
- Generates answer using LLM with retrieved context

---

### Example 6: Time Bucketing with Aggregation

**Use Case**: Analyze hourly trends with moving averages

```esql
FROM api_requests
| EVAL hour = DATE_TRUNC(1 hour, @timestamp)
| STATS
    request_count = COUNT(*),
    error_count = COUNT(*) WHERE status >= 500,
    avg_latency = AVG(latency_ms),
    p95_latency = PERCENTILE(latency_ms, 95)
  BY hour, service
| EVAL error_rate = TO_DOUBLE(error_count) * 100.0 / request_count
| WHERE request_count > 10
| SORT hour DESC
```

**What it does**:
- Groups requests into hourly buckets
- Calculates counts, errors, and latency metrics
- Computes error rate using TO_DOUBLE()
- Filters to statistically significant hours
- Sorts by time (most recent first)

---

### Example 7: Conditional Aggregation

**Use Case**: Count events matching different conditions

```esql
FROM sales
| STATS
    total_orders = COUNT(*),
    completed_orders = COUNT(*) WHERE status == "completed",
    cancelled_orders = COUNT(*) WHERE status == "cancelled",
    pending_orders = COUNT(*) WHERE status == "pending" OR status IS NULL,
    total_revenue = SUM(amount),
    completed_revenue = SUM(CASE(status == "completed", amount, 0))
  BY region, product_category
| EVAL completion_rate = TO_DOUBLE(completed_orders) * 100.0 / total_orders
| WHERE total_orders > 5
| SORT completion_rate DESC
```

**What it does**:
- Uses `COUNT(*) WHERE condition` for conditional counting
- Uses `SUM(CASE(...))` for conditional sums
- Includes NULL handling in pending orders
- Calculates completion rate with TO_DOUBLE()

---

### Example 8: Business Date Parameterization (NOT @timestamp)

**Use Case**: Filter by business dates that users understand

```esql
FROM orders
| WHERE order_date >= ?start_date AND order_date <= ?end_date
| WHERE region == ?region
| LOOKUP JOIN products ON product_id
| STATS
    order_count = COUNT(*),
    total_revenue = SUM(order_amount),
    avg_order_value = AVG(order_amount),
    unique_customers = COUNT_DISTINCT(customer_id)
  BY product_category
| EVAL avg_order_value = TO_DOUBLE(total_revenue) / order_count
| SORT total_revenue DESC
```

**What it does**:
- Filters by `order_date` (business date), NOT `@timestamp`
- Parameterizes date range for user control
- Enriches with product information
- Calculates revenue metrics

**Why NOT @timestamp**:
- `@timestamp` = when document was indexed (system field)
- `order_date` = when order was placed (business field)
- Users understand business dates, not index timestamps

---

### Example 9: Integer Division Fix

**Use Case**: Calculate accurate percentages and rates

❌ **WRONG**:
```esql
FROM auth_attempts
| STATS
    total = COUNT(*),
    failures = COUNT(*) WHERE result == "failed"
  BY service
| EVAL failure_rate = (failures / total) * 100  -- ❌ Returns 0 or 100 only!
```

✅ **CORRECT**:
```esql
FROM auth_attempts
| STATS
    total = COUNT(*),
    failures = COUNT(*) WHERE result == "failed"
  BY service
| EVAL failure_rate = (TO_DOUBLE(failures) / total) * 100  -- ✅ Returns 5.7, 12.3, etc.
| SORT failure_rate DESC
```

---

### Example 10: NULL Handling Fix

**Use Case**: Include missing data in security analysis

❌ **WRONG**:
```esql
FROM security_events
| WHERE auth_result != "success"  -- ❌ Silently excludes NULL!
| STATS failures = COUNT(*) BY user
```

✅ **CORRECT**:
```esql
FROM security_events
| WHERE auth_result != "success" OR auth_result IS NULL  -- ✅ Includes missing data
| STATS failures = COUNT(*) BY user, auth_result
| SORT failures DESC
```

**Why it matters**: Missing auth results could indicate:
- Logging failures
- System compromises
- Data collection issues
- Potential security blind spots

---

## Common Error Patterns & Fixes

| Error Pattern | Root Cause | Fix |
|--------------|------------|-----|
| **"Unknown column [field] in right/left side of join"** | Join key doesn't exist in both datasets | **CANNOT AUTO-FIX** - Verify schemas and use field that exists in BOTH |
| **"[-] has arguments with incompatible types [datetime]"** | Direct datetime subtraction | Wrap both sides in `TO_LONG()`: `(TO_LONG(NOW()) - TO_LONG(field))` |
| **"Unknown function [COUNT]" with DISTINCT** | Using SQL `COUNT(DISTINCT field)` | Use `COUNT_DISTINCT(field)` instead |
| **INLINESTATS syntax error with multiple BY** | Multiple BY clauses per aggregation | Use ONE BY clause: `INLINESTATS a = AVG(x), b = MAX(y) BY category` |
| **Query returns no results (scripted query)** | Using `NOW() - X days` with static demo data | Remove `@timestamp` filters from scripted queries - use Kibana time picker |
| **"Unknown index [x_lookup]"** | Adding `_lookup` suffix | Remove `_lookup` suffix entirely |
| **"Unknown column [providers_lookup.field]"** | Using table prefix after JOIN | Remove prefix: `providers.field` → `field` |
| **"Unknown column [table.field]" after JOIN** | Field reference with prefix | Reference fields directly without table prefix |
| **"mismatched input 'MATCH'"** | MATCH as pipe operation | Use `WHERE MATCH(field, query)` |
| **"Unknown query parameter"** | Checking param IS NULL | Remove NULL checks, use required params |
| **"token recognition error" in FORK** | Named branches or comments | Remove branch names and comments |
| **"Lookup Join requires lookup mode"** | Index not in lookup mode | Target index must be created in lookup mode |
| **"Unknown function [COUNT_IF]"** | Function doesn't exist | Use `SUM(CASE(...))` pattern |
| **"DATE_TRUNC" errors** | Wrong parameter order | Use `DATE_TRUNC(interval, field)` |
| **Division returns 0** | Integer division | Use `TO_DOUBLE()` or multiply by `1.0` |
| **"Field not found" after STATS** | Field not in GROUP BY | Only grouped/aggregated fields available |
| **"Unknown column [agents_lookup]"** | Auto-fix adding suffix | Remove the `_lookup` suffix |
| **"RERANK" errors** | Wrong syntax | Use `RERANK query ON field` |
| **"MATCH WITH" syntax error** | Invalid MATCH syntax | Use `WHERE MATCH(field, query)` |
| **Silent data loss with !=** | NULL values excluded from negative filter | Add `OR field IS NULL` |
| **Wrong percentage (0 or 100)** | Integer division in EVAL | Wrap denominator in `TO_DOUBLE()` |

**Note**: The first error (JOIN key missing) is the **MOST COMMON failure** from production testing and **CANNOT be auto-fixed**.

---

## Query Strategy Guidelines

### Pain Point Mapping

Map customer pain points to specific ES|QL capabilities:

| Pain Point | ES|QL Solution | Pattern |
|-----------|----------------|---------|
| **"Can't find information quickly"** | Full-text search | MATCH, RERANK, semantic search |
| **"No visibility into patterns"** | Aggregations & stats | STATS, time-series bucketing |
| **"Data silos across systems"** | Data enrichment | LOOKUP JOIN |
| **"Can't detect anomalies"** | Outlier detection | INLINESTATS with z-scores |
| **"Manual analysis takes too long"** | Automated queries | Parameterized queries, Agent Builder |
| **"Missing context in results"** | Reference data joins | LOOKUP JOIN with enrichment |
| **"Need proactive alerts"** | Threshold detection | WHERE with calculated fields |
| **"Complex multi-step analysis"** | Pipeline queries | Multi-stage EVAL, STATS, filtering |

---

### Parameter Identification Strategy

**Required vs Optional**:
- ES|QL does NOT support optional parameters
- Create **separate queries** for different scenarios
- All parameters in a query are **REQUIRED**

**When to Parameterize**:
- ✅ User selections (region, category, status)
- ✅ Search terms (user_question, keywords)
- ✅ Business date ranges (order_date, contract_date)
- ✅ Thresholds (minimum_amount, risk_level)
- ❌ NOT @timestamp (use NOW() instead)
- ❌ NOT system fields (event.ingested, etc.)

**Parameter Naming**:
- Use descriptive names: `?region` not `?r`
- Use snake_case: `?start_date` not `?startDate`
- Match business terminology: `?customer_tier` not `?tier_id`

---

### Semantic Text Field Detection

**When to use semantic_text**:
- Document content (articles, policies, procedures)
- Product descriptions
- Support ticket text
- Knowledge base entries
- Unstructured text requiring semantic understanding

**Pattern**:
```esql
FROM knowledge_base
| WHERE MATCH(content, ?user_question)  -- content is semantic_text field
| RERANK ?user_question ON content      -- Re-rank by semantic similarity
| LIMIT 10
```

**NOT semantic_text**:
- Structured fields (status, category, ID)
- Short text fields (names, titles)
- Numerical fields
- Date fields

---

### Index Type Selection

**data_stream** (for time-series data):
- Events, logs, interactions
- Has `@timestamp` field
- Growing over time
- Used in FROM clause
- Example: `FROM purchase_transactions`, `FROM security_events`

**lookup** (for reference data):
- Members, providers, products, customers
- Relatively static
- Used in LOOKUP JOIN
- Must be in lookup mode
- Example: `LOOKUP JOIN customers ON customer_id`

**Rule**:
- If data has `@timestamp` and grows over time → `data_stream`
- If data is reference/dimensional → `lookup` (for LOOKUP JOIN)

---

### Complexity Progression Strategy

Build queries from simple to complex:

**Level 1 - Basic Filtering & Aggregation**:
```esql
FROM events
| WHERE status == "error"
| STATS count = COUNT(*) BY service
| SORT count DESC
```

**Level 2 - Time Bucketing & Calculated Fields**:
```esql
FROM events
| EVAL hour = DATE_TRUNC(1 hour, @timestamp)
| STATS error_count = COUNT(*) WHERE status == "error", total = COUNT(*)
  BY hour, service
| EVAL error_rate = TO_DOUBLE(error_count) * 100.0 / total
| SORT hour DESC
```

**Level 3 - Data Enrichment**:
```esql
FROM events
| LOOKUP JOIN services ON service_id
| WHERE tier == "production"
| STATS count = COUNT(*) BY service_name, environment
```

**Level 4 - Anomaly Detection**:
```esql
FROM metrics
| EVAL hour = DATE_TRUNC(1 hour, @timestamp)
| STATS value = AVG(metric) BY hour, service
| INLINESTATS mean = AVG(value), stddev = STDDEV(value) BY service
| EVAL z_score = (value - mean) / stddev
| WHERE z_score > 3
```

**Level 5 - Multi-Lag Sustained Patterns**:
```esql
FROM events
| EVAL hour = DATE_TRUNC(1 hour, @timestamp)
| STATS count = COUNT(*), hosts = COUNT_DISTINCT(host) BY hour, type
| INLINESTATS avg = AVG(count), stddev = STDDEV(count) BY type
| EVAL z_score = (count - avg) / stddev, multi_host = CASE(hosts >= 2, 1, 0)
| EVAL threat = z_score * multi_host
| WHERE threat > 2
```

---

## Post-Generation Validation Checklist

After generating ES|QL queries, validate against these patterns:

### ✅ Syntax Validation

- [ ] All field names exist in the schema (verify against data profile)
- [ ] LOOKUP JOIN keys exist in BOTH source and lookup datasets
- [ ] No table prefixes after LOOKUP JOIN (`specialty` not `providers.specialty`)
- [ ] No `_lookup` suffixes on index names
- [ ] MATCH is inside WHERE clause, not as pipe operation
- [ ] COUNT_DISTINCT() is a single function, not COUNT(DISTINCT ...)
- [ ] INLINESTATS has ONE BY clause at the end
- [ ] DATE functions have correct parameter order (interval/format first, field second)
- [ ] No named branches in FORK
- [ ] No parameter NULL checks

### ✅ Anti-Pattern Detection

- [ ] **Integer Division**: All EVAL divisions use TO_DOUBLE() or multiply by float first
- [ ] **NULL Handling**: Negative filters (!=, NOT, NOT LIKE) include `OR field IS NULL`
- [ ] **@timestamp**: Not parameterized with `?start_date` (use NOW() or parameterize business dates)
- [ ] **Variable Reuse**: Newly defined EVAL variables not used in same EVAL command

### ✅ Type & Mode Validation

- [ ] Lookup indices are in lookup mode (not data streams)
- [ ] Time-series data uses data_stream mode
- [ ] Date arithmetic uses TO_LONG() wrapper
- [ ] Division operations use TO_DOUBLE() for precision

### ✅ Query Type Validation

**For Scripted Queries**:
- [ ] Type is `"scripted"`
- [ ] NO `@timestamp` filters (users control via Kibana time picker)
- [ ] Hard-coded values (no parameters)
- [ ] Can be tested immediately

**For Parameterized Queries**:
- [ ] Type is `"parameterized"`
- [ ] All parameters are required (no NULL checks)
- [ ] Parameter names are descriptive
- [ ] Business dates parameterized (NOT `@timestamp`)
- [ ] Has `parameters` field with descriptions

### ✅ Security Query Validation

For security/SIEM queries, extra checks:
- [ ] Negative filters include NULL checks (critical - missing data = missed threats)
- [ ] Fields like `auth_result`, `threat_level`, `compliance_status` have NULL handling
- [ ] Error counts and failure rates use TO_DOUBLE() for accuracy

### ✅ Logic Validation

- [ ] Fields referenced after STATS are in GROUP BY or are aggregations
- [ ] Zero division protected with CASE() checks
- [ ] Time filtering strategy matches query type (scripted vs parameterized)
- [ ] Aggregations use appropriate functions (COUNT_DISTINCT, not COUNT(DISTINCT))

---

## Summary & Best Practices

### Key Principles

1. **Verify schemas first** - Don't invent field names or JOIN keys
2. **Think about NULL** - Negative filters exclude NULL silently
3. **Use TO_DOUBLE()** - Integer division truncates to 0
4. **@timestamp is special** - Never parameterize, use NOW() for recency
5. **After LOOKUP JOIN, no prefixes** - Fields are available directly
6. **One BY clause in INLINESTATS** - Just like STATS
7. **Separate EVALs for variable reuse** - Can't use new variables in same command
8. **MATCH in WHERE** - Not a pipe operation
9. **Parameters are required** - No NULL checking or optional logic
10. **Test with scripted first** - Then convert to parameterized if needed

### Common Patterns to Remember

**Percentage Calculation**:
```esql
| EVAL percentage = TO_DOUBLE(part) * 100.0 / total
```

**NULL-Safe Negative Filter**:
```esql
| WHERE status != "success" OR status IS NULL
```

**Date Arithmetic**:
```esql
| EVAL days = (TO_LONG(NOW()) - TO_LONG(created_at)) / 86400000
```

**Zero Division Protection**:
```esql
| EVAL rate = CASE(total > 0, TO_DOUBLE(count) / total, 0)
```

**Anomaly Detection**:
```esql
| INLINESTATS avg = AVG(value), stddev = STDDEV(value) BY group
| EVAL z_score = (value - avg) / stddev
| WHERE z_score > 3
```

**Time Bucketing**:
```esql
| EVAL hour = DATE_TRUNC(1 hour, @timestamp)
| STATS count = COUNT(*) BY hour
```

---

## Version History

- **2025-01-14**: Initial comprehensive reference
  - Added all 20 critical syntax rules
  - Documented 4 critical anti-patterns (integer division, NULL handling, @timestamp, array length)
  - Included advanced patterns (LOOKUP JOIN, INLINESTATS, FORK, multi-lag)
  - Added safe query templates for all query types
  - Comprehensive DO's and DON'Ts (30+ guidelines)
  - 10+ concrete examples with explanations
  - Common error patterns with fixes
  - Query strategy guidelines
  - Post-generation validation checklist

---

## Credits

**Generated by**: Elastic Demo Builder (Vulcan)
**Based on**: Production testing, user feedback, and ES|QL documentation
**Maintained by**: Elastic Solutions Architecture Team
**Purpose**: Enable high-quality LLM-generated ES|QL queries for Agent Builder and demos

---

**This is a living document.** As new ES|QL features are released or new anti-patterns discovered, this reference will be updated. Always use the latest version when generating queries.
