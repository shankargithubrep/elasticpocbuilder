# ES|QL Unsupported Functions - Common SQL Patterns to Avoid

## Overview

ES|QL is NOT standard SQL. Many common SQL functions and patterns don't exist in ES|QL and will cause query failures. This document catalogs unsupported functions found in generated queries and provides ES|QL alternatives.

## Window Functions (NOT SUPPORTED)

### LAG() and LEAD() - Row Access Functions

**SQL Pattern**:
```sql
SELECT
    year,
    revenue,
    revenue - LAG(revenue, 1) OVER (ORDER BY year) AS revenue_change
FROM sales
```

**ES|QL Reality**: ❌ **LAG() does NOT exist**

**Found in**: `demos/bass_pro_shops_product_management_20251029_214937/query_generator.py` line 222:
```esql
revenue_growth_yoy = (historical_revenue - LAG(historical_revenue, 1)) / GREATEST(LAG(historical_revenue, 1), 1) * 100
```

**Intent**: Calculate year-over-year revenue growth by comparing current year to previous year.

**ES|QL Alternatives**:

#### Option 1: Pre-Calculate in Data Generation
```python
# In data_generator.py
df['previous_year_revenue'] = df.groupby(['region', 'category'])['revenue'].shift(1)
df['yoy_growth'] = ((df['revenue'] - df['previous_year_revenue']) / df['previous_year_revenue']) * 100
```

Then query directly:
```esql
FROM sales
| WHERE year > 2022
| STATS
    current_revenue = SUM(revenue),
    avg_yoy_growth = AVG(yoy_growth)
  BY region, category, year
| SORT year DESC
```

#### Option 2: Use Separate Aggregations
```esql
// Get current year metrics
FROM sales
| WHERE timestamp > NOW() - 1 year AND timestamp < NOW()
| STATS current_revenue = SUM(revenue) BY region, category
| EVAL period = "current"

// Then separately query previous year and manually compare
FROM sales
| WHERE timestamp > NOW() - 2 years AND timestamp < NOW() - 1 year
| STATS previous_revenue = SUM(revenue) BY region, category
| EVAL period = "previous"

// Manual comparison in application layer
```

#### Option 3: Avoid Year-Over-Year Calculations in Queries
Instead of:
```esql
| EVAL yoy_growth = (current - LAG(current, 1)) / LAG(current, 1) * 100  // ❌ Won't work
```

Do:
```esql
// Show absolute trends without YoY comparison
FROM sales
| EVAL month = DATE_TRUNC(1 month, timestamp)
| STATS monthly_revenue = SUM(revenue) BY month, category
| SORT month DESC
| LIMIT 24  // Last 24 months - viewer can visually see trends
```

### RANK() and ROW_NUMBER() - Ranking Functions

**SQL Pattern**:
```sql
SELECT
    product_name,
    revenue,
    RANK() OVER (PARTITION BY category ORDER BY revenue DESC) AS rank
FROM products
```

**ES|QL Reality**: ❌ **RANK() does NOT exist**

**Found in**: `demos/bass_pro_shops_product_management_20251029_214937/query_generator.py` line 351:
```esql
regional_seasonal_rank = RANK() OVER (PARTITION BY quarter, region ORDER BY quarterly_revenue DESC)
```

**Intent**: Rank products within each category by revenue.

**ES|QL Alternative**: Use SORT and LIMIT

```esql
// Instead of RANK() to get top 5 per category
FROM products
| STATS total_revenue = SUM(revenue) BY product_name, category
| SORT category, total_revenue DESC
| LIMIT 100  // Get enough for all categories

// Then filter in application layer or use multiple queries
```

**Better Pattern**: Get top N without explicit rank
```esql
// Get top 5 products by revenue
FROM products
| STATS revenue = SUM(revenue) BY product_name
| SORT revenue DESC
| LIMIT 5
```

**For Partitioned Ranking**: Run separate queries per partition
```esql
// Top 5 products in "Fishing" category
FROM products
| WHERE category == "Fishing"
| STATS revenue = SUM(revenue) BY product_name
| SORT revenue DESC
| LIMIT 5

// Repeat for each category (or parameterize)
```

## Semantic Search Functions (NOT SUPPORTED)

### SEMANTIC() - Similarity Search

**Found in**: `demos/bass_pro_shops_product_management_20251029_214937/query_generator.py` line 286:
```esql
| WHERE SEMANTIC(product_description, ?trend_query) > 0.75
```

**ES|QL Reality**: ❌ **SEMANTIC() does NOT exist**

**Intent**: Find products semantically similar to a search term.

**ES|QL Alternative**: Use text matching or semantic_text field queries

```esql
// Option 1: Simple text matching
FROM products
| WHERE product_description LIKE "*kayak fishing*"

// Option 2: If using semantic_text field type (requires ELSER)
// This is not SEMANTIC() but rather a different query approach
FROM products
| WHERE MATCH(product_description_semantic, "kayak fishing")
```

**Better Approach**: Pre-calculate semantic matches during indexing
```python
# In data generator - add semantic match scores during data generation
# Use sentence transformers or similar to calculate similarity scores
df['trend_match_score'] = calculate_similarity(df['description'], trend_query)
```

Then query:
```esql
FROM products
| WHERE trend_match_score > 0.75
| STATS ... BY category
```

## Advanced Analytics Functions

### CHANGE_POINT - Anomaly Detection

**Found in**: `demos/bass_pro_shops_product_management_20251029_214937/query_generator.py` line 394:
```esql
| CHANGE_POINT daily_revenue
```

**ES|QL Reality**: ⚠️  **Unclear if CHANGE_POINT exists**

**Status**: Needs verification - not in standard ES|QL docs

**Intent**: Detect anomalous changes in time series data.

**ES|QL Alternative**: Use statistical thresholds

```esql
FROM sales
| EVAL day = DATE_TRUNC(1 day, timestamp)
| STATS daily_revenue = SUM(revenue) BY day, product_id
| INLINESTATS
    avg_revenue = AVG(daily_revenue),
    stddev_revenue = STD_DEV(daily_revenue)
  BY product_id
| EVAL
    zscore = (daily_revenue - avg_revenue) / GREATEST(stddev_revenue, 1),
    is_anomaly = ABS(zscore) > 2  // 2 standard deviations
| WHERE is_anomaly == true
| SORT zscore DESC
```

## Summary of Unsupported Functions

| Function | SQL Use Case | ES|QL Status | Alternative |
|----------|-------------|--------------|-------------|
| `LAG()` | Access previous row | ❌ Not supported | Pre-calculate or separate queries |
| `LEAD()` | Access next row | ❌ Not supported | Pre-calculate or separate queries |
| `RANK()` | Ranking within partition | ❌ Not supported | Use SORT + LIMIT |
| `ROW_NUMBER()` | Sequential numbering | ❌ Not supported | Use SORT + LIMIT |
| `DENSE_RANK()` | Dense ranking | ❌ Not supported | Use SORT + LIMIT |
| `NTILE()` | Percentile bucketing | ❌ Not supported | Calculate in application |
| `PERCENT_RANK()` | Percentage ranking | ❌ Not supported | Calculate in application |
| `FIRST_VALUE()` | First in window | ❌ Not supported | Use SORT + LIMIT 1 |
| `LAST_VALUE()` | Last in window | ❌ Not supported | Use SORT DESC + LIMIT 1 |
| `SEMANTIC()` | Semantic similarity | ❌ Not supported | Use text matching or pre-calculate |
| `COSINE_SIMILARITY()` | Vector similarity | ❌ Not supported | Pre-calculate scores |
| `CHANGE_POINT()` | Anomaly detection | ⚠️  Unverified | Use z-score with INLINESTATS |

## Best Practices for ES|QL Query Generation

### 1. Avoid Window Functions Entirely

**❌ Don't generate**:
```esql
| EVAL growth = (revenue - LAG(revenue)) / LAG(revenue) * 100
| EVAL rank = RANK() OVER (PARTITION BY category ORDER BY revenue DESC)
```

**✅ Instead use**:
```esql
// Show trends without explicit YoY comparison
| STATS monthly_revenue = SUM(revenue) BY month, category
| SORT month DESC

// Get top N without ranking
| STATS revenue = SUM(revenue) BY product
| SORT revenue DESC
| LIMIT 10
```

### 2. Pre-Calculate Complex Metrics

If queries need:
- Year-over-year growth
- Ranking within groups
- Semantic similarity scores
- Anomaly indicators

**Calculate during data generation** and include as fields:

```python
# In data_generator.py
df['yoy_growth_pct'] = calculate_yoy_growth(df)
df['category_rank'] = df.groupby('category')['revenue'].rank(ascending=False)
df['is_trending'] = df['revenue_zscore'] > 2

# Then query simply:
```
```esql
FROM sales
| WHERE is_trending == true
| STATS total_revenue = SUM(revenue) BY product, category_rank
| WHERE category_rank <= 5
```

### 3. Use ES|QL Strengths

Focus on what ES|QL does well:
- ✅ Fast aggregations (STATS)
- ✅ Time-based bucketing (DATE_TRUNC)
- ✅ LOOKUP JOIN for enrichment
- ✅ Statistical functions (AVG, SUM, COUNT, STD_DEV)
- ✅ INLINESTATS for within-query aggregations
- ✅ Text matching (LIKE, ==)
- ✅ Filtering (WHERE)
- ✅ Sorting and limiting (SORT, LIMIT)

Avoid SQL-style window functions and complex analytics that ES|QL doesn't support.

### 4. Update LLM Generation Prompts

Add to module generator prompts:

```python
prompt += """
CRITICAL - ES|QL DOES NOT SUPPORT:
- ❌ Window functions: LAG(), LEAD(), RANK(), ROW_NUMBER(), FIRST_VALUE(), LAST_VALUE()
- ❌ Semantic functions: SEMANTIC(), COSINE_SIMILARITY()
- ❌ OVER (PARTITION BY ...) clauses
- ❌ Unverified functions: CHANGE_POINT()

For year-over-year comparisons:
✅ Pre-calculate during data generation
✅ Use separate queries with date filters
✅ Show absolute trends without explicit YoY calculations

For ranking:
✅ Use SORT + LIMIT to get top N
✅ Run separate queries per category if needed
✅ Avoid RANK() OVER (PARTITION BY ...)

For semantic search:
✅ Pre-calculate similarity scores during data generation
✅ Use simple text matching with LIKE
✅ Index with semantic_text field type (requires ELSER)
"""
```

## Verification Checklist

Before considering a query valid, check:

- [ ] No LAG() or LEAD() functions
- [ ] No RANK(), ROW_NUMBER(), DENSE_RANK(), NTILE()
- [ ] No OVER (PARTITION BY ...) clauses
- [ ] No SEMANTIC() or COSINE_SIMILARITY() calls
- [ ] No FIRST_VALUE() or LAST_VALUE()
- [ ] No CHANGE_POINT() (until verified in ES|QL docs)
- [ ] All window-style calculations use pre-calculated fields or separate queries
- [ ] All ranking uses SORT + LIMIT patterns

## Impact on Bass Pro Shops Demo

The Bass Pro Shops demo (`demos/bass_pro_shops_product_management_20251029_214937/`) has **3 unsupported functions**:

1. **Line 222**: `LAG(historical_revenue, 1)` - YoY growth calculation
2. **Line 286**: `SEMANTIC(product_description, ?trend_query)` - Semantic search
3. **Line 351**: `RANK() OVER (PARTITION BY ...)` - Regional ranking
4. **Line 394**: `CHANGE_POINT daily_revenue` - Anomaly detection

**These queries will all fail** when executed against Elasticsearch.

**Fix Required**: Regenerate queries without these functions, using the alternatives documented above.

---

**Document Version**: 1.0
**Date**: October 29, 2025
**Related Files**:
- `.claude/skills/agent-builder.md` (needs update)
- `src/framework/module_generator.py` (prompts need update)
- `demos/bass_pro_shops_product_management_20251029_214937/query_generator.py` (needs regeneration)
