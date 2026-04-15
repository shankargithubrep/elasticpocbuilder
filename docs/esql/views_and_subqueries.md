# ES|QL Views and Subqueries (9.4+)

Elastic 9.4 introduces two related features that make ES|QL queries more composable
and easier to reuse: **Views** and **Subqueries**.

Use them when a demo query would otherwise:
- repeat the same `FROM ... | WHERE ... | STATS ...` prelude across many queries
- need the output of one aggregation as the input to another
- express "top-N from a filtered slice" without exporting intermediate results

---

## Views

A **view** is a saved, named ES|QL query that can be referenced in `FROM` like a regular index.
Views let you hide complex filter / enrich / normalize logic behind a clean name and reuse it
across many downstream queries.

### Creating a view

```esql
CREATE VIEW enterprise_sales_active_q4 AS
FROM sales-*
| WHERE status == "active" AND @timestamp >= "2026-10-01"
| EVAL revenue_usd = amount * fx_rate
| KEEP deal_id, account, region, revenue_usd, @timestamp
```

### Using a view

```esql
FROM enterprise_sales_active_q4
| STATS total_revenue = SUM(revenue_usd) BY region
| SORT total_revenue DESC
| LIMIT 10
```

### When to use views in a demo

- **Tenant scoping** — define a per-tenant view once, reference it everywhere:
  ```esql
  CREATE VIEW acme_kb AS
  FROM kb_content | WHERE tenant_id == "acme-support"
  ```
- **Normalized enrichment** — bake a `LOOKUP JOIN` or `EVAL` layer into a reusable named
  source so presenters don't have to type it every query.
- **Clean dashboard panels** — each panel queries `FROM <view>` instead of repeating 20 lines.

### Listing and dropping

```esql
SHOW VIEWS
DROP VIEW enterprise_sales_active_q4
```

---

## Subqueries

A **subquery** is an inline ES|QL query wrapped in parentheses that can appear anywhere a
value list is expected. The two most common forms:

### 1. `IN (subquery)` — dynamic filter

Filter one dataset by the output of another query in a single statement:

```esql
FROM support_tickets
| WHERE customer_id IN (
    FROM customers | WHERE tier == "enterprise" | KEEP customer_id
  )
| STATS ticket_count = COUNT(*) BY priority
```

### 2. Scalar subquery — inject an aggregated value

Use the result of one query as a scalar in another:

```esql
FROM orders
| WHERE amount > (
    FROM orders | STATS avg_amount = AVG(amount) | KEEP avg_amount
  )
| STATS big_orders = COUNT(*) BY region
```

### When to use subqueries in a demo

- **"Top customers by X, show all their activity"** patterns
- **Threshold filtering** where the threshold itself is computed (e.g. "above average")
- **Cohort analysis** without needing a materialized lookup table

---

## Rules and limits

- Views are **read-only** — they cannot wrap `COMPLETION`, `RERANK`, or `INLINE STATS`
  that depend on runtime parameters; treat them as pure filter / enrich / aggregate pipelines.
- Subqueries returning a **single column** are required for `IN` and scalar contexts.
- A subquery inside `IN` should end with `KEEP <one_field>` to make intent explicit.
- Views can reference other views (depth limit applies — keep composition shallow, 2–3 levels max).
- Use views for structural reuse; use subqueries for one-off dynamic filtering.

---

## Demo hook ideas

| Scenario | Feature | Benefit |
|---|---|---|
| Multi-tenant KB retrieval | View per tenant | Cleaner queries, no repeated WHERE clauses |
| "Above-average" analytics | Scalar subquery | No need for two-pass queries |
| Cohort drill-down | `IN (subquery)` | Single-query cohort filter |
| Shared dashboard panels | View | Reusable data source across panels |
| Enrichment layer | View with `LOOKUP JOIN` | Hide join complexity behind a name |
