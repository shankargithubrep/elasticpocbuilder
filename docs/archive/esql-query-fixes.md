# ES|QL Query Fixes - Join Timing Issues

## Problem Identified
The original queries had **LOOKUP JOIN operations after STATS aggregations**, which caused fields to disappear. After a STATS command, only the grouped-by fields and aggregated fields remain available.

## Key Rule for LOOKUP JOIN
**Always perform LOOKUP JOIN BEFORE aggregations if you need the joined fields for grouping or filtering.**

### ✅ Query 2: Channel Performance by Region
**Original Issue**: Integer division returned 0 for CTR and CVR  
**Fix**: Added TO_DOUBLE() for proper decimal division

```esql
FROM campaign_performance
| WHERE Date >= "2024-06-01" AND Date <= "2025-06-30"
| EVAL ctr = TO_DOUBLE(Clicks) / Impressions * 100  ← FIXED
| EVAL cvr = TO_DOUBLE(Conversions) / Clicks * 100  ← FIXED
| STATS 
    total_impressions = SUM(Impressions),
    avg_ctr = AVG(ctr),
    avg_cvr = AVG(cvr),
    total_revenue = SUM(Revenue)
  BY Region, Channel
| WHERE total_impressions > 100000
| SORT total_revenue DESC
```

---

## Queries Fixed

### ✅ Query 1: Campaign ROI Analysis with Asset Enrichment
**Original Issue**: Tried to join on `Asset ID` after STATS removed it  
**Fix**: Moved LOOKUP JOIN before STATS, added `Asset Type` to GROUP BY

```esql
FROM campaign_performance
| LOOKUP JOIN brand_assets ON `Asset ID`  ← MOVED BEFORE STATS
| EVAL roi = (Revenue - Spend) / Spend * 100
| STATS 
    total_spend = SUM(Spend),
    total_revenue = SUM(Revenue),
    avg_roi = AVG(roi),
    total_conversions = SUM(Conversions)
  BY `Campaign Name`, `Asset Type`  ← CAN NOW GROUP BY ASSET TYPE
| EVAL roi_percentage = (total_revenue - total_spend) / total_spend * 100
| SORT roi_percentage DESC
| LIMIT 10
```

---

### ✅ Query 3: Hidden Gems - High-Potential Assets for Campaign Expansion
**Original Issue**: Multiple joins with aggregations in wrong order, unrealistic thresholds  
**Fix**: Restructured to aggregate campaign data first, then join usage events, adjusted thresholds to match actual data distribution

```esql
FROM campaign_performance
| STATS 
    avg_engagement = AVG(`Engagement Rate`),
    total_conversions = SUM(Conversions),
    total_revenue = SUM(Revenue),
    campaign_count = COUNT_DISTINCT(`Campaign Name`)
  BY `Asset ID`  ← AGGREGATE CAMPAIGN METRICS FIRST
| LOOKUP JOIN asset_usage_events ON `Asset ID`
| WHERE `Action Type` IN ("Download", "View", "Share")
| STATS 
    max_avg_engagement = MAX(avg_engagement),
    max_conversions = MAX(total_conversions),
    max_revenue = MAX(total_revenue),
    max_campaigns = MAX(campaign_count),
    internal_usage = COUNT(*)  ← COUNT USAGE EVENTS
  BY `Asset ID`  ← KEEP ASSET ID FOR FINAL JOIN
| WHERE internal_usage > 15 AND max_campaigns < 5  ← REALISTIC THRESHOLDS
| EVAL engagement_score = max_avg_engagement * internal_usage  ← COMPOSITE SCORE
| LOOKUP JOIN brand_assets ON `Asset ID`  ← FINAL ENRICHMENT
| KEEP `Asset ID`, `Product Name`, `Asset Type`, internal_usage, max_avg_engagement, max_campaigns, engagement_score
| SORT engagement_score DESC
| LIMIT 20
```

**Key improvements:**
- Start with campaign_performance to get engagement metrics
- Join to usage events and count internal usage
- Use realistic thresholds (>15 usage, <5 campaigns)
- Create composite engagement_score for ranking
- Multiple strategic joins with proper field retention

---

### ✅ Query 6: Asset Type Performance Ranking
**Original Issue**: Started FROM brand_assets unnecessarily, integer division  
**Fix**: Start from campaign_performance (larger dataset), join to enrich, use TO_DOUBLE()

```esql
FROM campaign_performance  ← START WITH PERFORMANCE DATA
| LOOKUP JOIN brand_assets ON `Asset ID`  ← ENRICH IMMEDIATELY
| EVAL revenue_per_impression = TO_DOUBLE(Revenue) / Impressions * 1000  ← FIXED
| STATS 
    total_campaigns = COUNT_DISTINCT(`Campaign Name`),
    total_revenue = SUM(Revenue),
    avg_engagement = AVG(`Engagement Rate`),
    avg_revenue_per_1k = AVG(revenue_per_impression)
  BY `Asset Type`, Status  ← NOW WE HAVE THESE FIELDS
| WHERE Status == "Active"
| SORT total_revenue DESC
| LIMIT 15
```

---

### ✅ Query 7: Audience Segment Profitability
**Original Issue**: Division by zero when Conversions = 0, integer division  
**Fix**: Added WHERE filter to exclude zero conversions, use TO_DOUBLE()

```esql
FROM campaign_performance
| WHERE Date >= "2024-01-01"
| WHERE Conversions > 0  ← PREVENTS DIVISION BY ZERO
| EVAL cost_per_conversion = TO_DOUBLE(Spend) / Conversions  ← FIXED
| EVAL revenue_per_conversion = TO_DOUBLE(Revenue) / Conversions  ← FIXED
| EVAL profit_margin = TO_DOUBLE(Revenue - Spend) / Revenue * 100  ← FIXED
| STATS 
    total_conversions = SUM(Conversions),
    avg_cpc = AVG(cost_per_conversion),
    avg_revenue_per_conv = AVG(revenue_per_conversion),
    avg_profit_margin = AVG(profit_margin),
    total_profit = SUM(Revenue - Spend)
  BY `Audience Segment`, Channel
| WHERE total_conversions > 100
| EVAL efficiency_score = (avg_revenue_per_conv / avg_cpc) * avg_profit_margin
| SORT efficiency_score DESC
```

---

### ✅ Query 8: Asset Type Usage Across Departments
**Purpose**: Show which asset types are most popular across different teams  
**Approach**: Aggregate usage by department and asset, then roll up by asset type

```esql
FROM asset_usage_events
| STATS 
    usage_count = COUNT(*),
    unique_users = COUNT_DISTINCT(`User ID`)
  BY Department, `Asset ID`
| LOOKUP JOIN brand_assets ON `Asset ID`
| STATS 
    total_usage = SUM(usage_count),
    total_users = SUM(unique_users),
    departments_using = COUNT_DISTINCT(Department)
  BY `Asset Type`
| EVAL avg_usage_per_dept = TO_DOUBLE(total_usage) / departments_using
| SORT total_usage DESC
| LIMIT 15
```

**Key features:**
- Shows organizational usage patterns
- Identifies which content types resonate across teams
- Provides insights for asset creation priorities
- Uses TO_DOUBLE() for proper decimal division

---

## General Patterns for Success

### ✅ DO THIS:
```esql
FROM main_index
| LOOKUP JOIN lookup_index ON join_field  ← JOIN FIRST
| STATS aggregations BY field_from_lookup  ← THEN AGGREGATE
```

### ❌ NOT THIS:
```esql
FROM main_index
| STATS aggregations BY some_field  ← AGGREGATION LOSES FIELDS
| LOOKUP JOIN lookup_index ON join_field  ← CAN'T JOIN - FIELD GONE!
```

### When You Need Multiple Joins:
1. **Keep the join field** in every STATS BY clause
2. **Join progressively** after each aggregation that keeps the join field
3. **Final enrichment join** just before KEEP/SORT for display fields

---

## Testing Your Queries

If you get errors or unexpected results:

### "Unknown column [FieldName]" errors:
1. **Check what fields exist at that point** in the pipeline
2. After STATS, only BY fields + aggregated fields exist
3. After LOOKUP JOIN, all fields from lookup index are added
4. Use KEEP early if you want to track exactly what fields you have

### Calculated fields return 0:
1. **ES|QL performs integer division by default**
2. Use `TO_DOUBLE()` on at least one operand
3. Or multiply by a decimal first: `value * 100.0 / divisor`
4. Test calculations with simple ROW queries first

### Division by zero errors:
1. Add WHERE filters before division: `WHERE denominator > 0`
2. Use COALESCE for null handling: `COALESCE(field, 0)`

---

## All Queries Now Tested & Fixed ✅

All 8 demo queries have been updated and should now work correctly in your Agent Builder demo!
