from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class BassProShopsQueryGenerator(QueryGeneratorModule):
    """Query generator for Bass Pro Shops - Product Management"""

    # DO NOT define __init__ - inherited from base class provides:
    # self.config, self.datasets

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate ES|QL queries specific to Bass Pro Shops's use cases"""

        queries = []

        # CRITICAL: Use EXACT field names from the datasets
        # The module loader provides field_info with actual column names, types, and examples

        # Access field information (injected by module loader)
        if hasattr(self, 'field_info'):
            print("=== Available Field Information ===")
            for dataset_name, info in self.field_info.items():
                print(f"\nDataset: {dataset_name}")
                print(f"  Columns: {info['columns']}")
                print(f"  Shape: {info['shape']}")
                if 'examples' in info:
                    print(f"  Sample values:")
                    for col, examples in list(info['examples'].items())[:5]:
                        print(f"    {col}: {examples[:3]}")

        # Identify dataset types based on actual fields
        timeseries_datasets = []
        lookup_datasets = []

        for dataset_name in self.datasets.keys():
            # Check actual column names
            columns = list(self.datasets[dataset_name].columns)

            # Dataset is timeseries if it has a timestamp field
            has_timestamp = any('time' in col.lower() or col == '@timestamp' for col in columns)

            if has_timestamp:
                timeseries_datasets.append(dataset_name)
            else:
                lookup_datasets.append(dataset_name)

        print(f"\nTimeseries datasets: {timeseries_datasets}")
        print(f"Lookup datasets: {lookup_datasets}")

        # For each dataset, identify key field roles by inspecting actual names
        field_roles = {}

        for dataset_name, df in self.datasets.items():
            columns = list(df.columns)
            field_roles[dataset_name] = {}

            # Find timestamp field (exact match)
            for col in columns:
                if 'timestamp' in col.lower() or col == '@timestamp':
                    field_roles[dataset_name]['timestamp'] = col
                    break

            # Find ID fields (ending with _id)
            id_fields = [col for col in columns if col.endswith('_id')]
            if id_fields:
                field_roles[dataset_name]['ids'] = id_fields

            # Find metric fields (numeric columns that aren't IDs)
            numeric_cols = []
            for col in columns:
                if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                    if not col.endswith('_id'):
                        numeric_cols.append(col)
            field_roles[dataset_name]['metrics'] = numeric_cols

            # Find dimension fields (categorical)
            categorical_cols = []
            for col in columns:
                if df[col].dtype == 'object' or col in ['region', 'category', 'type', 'genre', 'status']:
                    if not col.endswith('_id') and col not in field_roles[dataset_name].get('timestamp', []):
                        categorical_cols.append(col)
            field_roles[dataset_name]['dimensions'] = categorical_cols

        print(f"\n=== Detected Field Roles ===")
        for dataset, roles in field_roles.items():
            print(f"\n{dataset}:")
            for role, fields in roles.items():
                if fields:
                    print(f"  {role}: {fields}")

        # Extract actual field names from the datasets
        sales_ds = 'product_sales'
        catalog_ds = 'product_catalog'
        trends_ds = 'market_trends'
        segments_ds = 'customer_segments'

        # Get actual field names
        sales_fields = list(self.datasets[sales_ds].columns) if sales_ds in self.datasets else []
        catalog_fields = list(self.datasets[catalog_ds].columns) if catalog_ds in self.datasets else []
        trends_fields = list(self.datasets[trends_ds].columns) if trends_ds in self.datasets else []
        segments_fields = list(self.datasets[segments_ds].columns) if segments_ds in self.datasets else []

        print(f"\n=== Actual Field Names ===")
        print(f"product_sales: {sales_fields}")
        print(f"product_catalog: {catalog_fields}")
        print(f"market_trends: {trends_fields}")
        print(f"customer_segments: {segments_fields}")

        # Extract specific field names we need
        timestamp_field = field_roles.get(sales_ds, {}).get('timestamp', 'timestamp')
        
        # =================================================================
        # QUERY 1: Regional Fishing Category Performance Analysis (MEDIUM)
        # Pain Point: Scattered market research and sales data
        # Features: STATS, DATE_TRUNC, WHERE, EVAL, LOOKUP JOIN
        # =================================================================
        queries.append({
            "name": "Regional Fishing Category Performance Analysis",
            "description": """Compare Southeast bass fishing vs. Northwest fly fishing sales with enriched product details. 
            This query consolidates scattered sales and catalog data to show regional preferences at a glance. 
            Product managers can instantly see which fishing categories dominate in each region without manually 
            joining spreadsheets or waiting for IT reports.""",
            "esql": f"""FROM {sales_ds}
| WHERE {timestamp_field} > NOW() - 90 days
  AND region IN ("Southeast", "Northwest")
| LOOKUP JOIN {catalog_ds}_lookup ON product_id
| EVAL revenue_per_unit = revenue / GREATEST(quantity, 1)
| STATS
    total_revenue = SUM(revenue),
    units_sold = SUM(quantity),
    avg_price = AVG(revenue_per_unit),
    transaction_count = COUNT(*)
  BY region, category, subcategory
| WHERE category == "Fishing"
  AND (subcategory LIKE "*bass*" OR subcategory LIKE "*fly*")
| EVAL regional_category = CONCAT(region, " - ", subcategory)
| SORT total_revenue DESC
| LIMIT 20""",
            "expected_use_case": """Use this daily to monitor regional fishing preferences and identify 
            inventory allocation opportunities. For example, if Southeast bass fishing revenue is 3x Northwest, 
            adjust regional distribution centers accordingly.""",
            "parameters": []
        })

        # =================================================================
        # QUERY 2: Sales Spike Correlation with Market Trends (COMPLEX)
        # Pain Point: Cannot quickly correlate sales spikes with trends
        # Features: STATS, DATE_TRUNC, EVAL, WHERE, LOOKUP JOIN, SORT
        # =================================================================
        queries.append({
            "name": "Sales Spike Correlation with Market Trends",
            "description": """Identify sales spikes in specific categories and correlate with concurrent market 
            trend data to understand demand drivers. This solves the critical pain point of not being able to 
            quickly connect sales performance with market signals. When turkey hunting gear spikes in March, 
            see if search volume and sentiment also increased to distinguish real trends from one-off events.""",
            "esql": f"""FROM {sales_ds}
| WHERE {timestamp_field} > NOW() - 180 days
| EVAL week = DATE_TRUNC(1 week, {timestamp_field})
| STATS
    weekly_revenue = SUM(revenue),
    weekly_units = SUM(quantity)
  BY week, region, category
| LOOKUP JOIN {trends_ds}_lookup ON region
| WHERE trend_category == category
  AND DATE_DIFF("day", week, {timestamp_field}) <= 7
| EVAL
    revenue_spike = weekly_revenue > 1.5 * AVG(weekly_revenue),
    trend_strength = search_volume * sentiment_score,
    correlation_score = CASE(
      revenue_spike AND trend_strength > 75, "Strong Correlation",
      revenue_spike AND trend_strength > 50, "Moderate Correlation",
      revenue_spike, "Spike Without Trend Signal",
      "Normal Performance"
    )
| STATS
    avg_spike_revenue = AVG(weekly_revenue),
    spike_count = COUNT(*) WHERE revenue_spike,
    avg_trend_strength = AVG(trend_strength),
    max_sentiment = MAX(sentiment_score)
  BY region, category, correlation_score
| WHERE spike_count > 0
| SORT avg_spike_revenue DESC
| LIMIT 25""",
            "expected_use_case": """Run this weekly to identify which sales spikes are backed by genuine market 
            interest vs. random fluctuations. Use insights to prioritize inventory investments and marketing spend.""",
            "parameters": []
        })

        # =================================================================
        # QUERY 3: Seasonal Demand Prediction for Hunting Equipment (COMPLEX)
        # Pain Point: Scattered market research across systems
        # Features: STATS, DATE_TRUNC, DATE_EXTRACT, EVAL, WHERE, LOOKUP JOIN
        # =================================================================
        queries.append({
            "name": "Seasonal Demand Prediction for Hunting Equipment",
            "description": """Analyze historical spring turkey and fall deer hunting season patterns enriched 
            with product seasonality tags and market search trends. This consolidates 3 data sources 
            (sales history, product metadata, market signals) to predict upcoming seasonal demand. 
            Product managers can proactively adjust inventory 6-8 weeks before peak season.""",
            "esql": f"""FROM {sales_ds}
| WHERE {timestamp_field} > NOW() - 2 years
| EVAL
    month = DATE_EXTRACT("month", {timestamp_field}),
    year = DATE_EXTRACT("year", {timestamp_field}),
    season = CASE(
      month IN (3, 4, 5), "Spring Turkey",
      month IN (9, 10, 11), "Fall Deer",
      "Off Season"
    )
| LOOKUP JOIN {catalog_ds}_lookup ON product_id
| WHERE seasonal_tag IN ("turkey", "deer", "hunting")
  AND category == "Hunting"
| LOOKUP JOIN {trends_ds}_lookup ON region
| WHERE DATE_EXTRACT("month", {timestamp_field}) == month
| STATS
    historical_revenue = SUM(revenue),
    historical_units = SUM(quantity),
    avg_search_volume = AVG(search_volume),
    product_count = COUNT_DISTINCT(product_id)
  BY season, year, region, subcategory, seasonal_tag
| EVAL
    revenue_growth_yoy = (historical_revenue - LAG(historical_revenue, 1)) / GREATEST(LAG(historical_revenue, 1), 1) * 100,
    demand_score = (historical_units * avg_search_volume) / 1000
| WHERE season != "Off Season"
| SORT year DESC, season, demand_score DESC
| LIMIT 50""",
            "expected_use_case": """Use this in January (for spring turkey prep) and June (for fall deer prep) 
            to forecast seasonal demand by region. Combine historical patterns with current search trends to 
            predict inventory needs and avoid stockouts during peak hunting seasons.""",
            "parameters": []
        })

        # =================================================================
        # QUERY 4: Customer Segment Purchase Pattern Analysis (MEDIUM)
        # Pain Point: Cannot correlate sales with customer segments
        # Features: STATS, LOOKUP JOIN, WHERE, EVAL, SORT
        # =================================================================
        queries.append({
            "name": "Customer Segment Purchase Pattern Analysis",
            "description": """Correlate sales patterns with customer segment profiles (weekend warriors vs. 
            serious anglers vs. family campers) and product categories. This query solves the pain point of 
            not understanding which customer segments drive specific product categories. Discover that serious 
            anglers drive 70% of premium rod sales while family campers prefer starter bundles.""",
            "esql": f"""FROM {sales_ds}
| WHERE {timestamp_field} > NOW() - 90 days
| LOOKUP JOIN {segments_ds}_lookup ON customer_segment
| LOOKUP JOIN {catalog_ds}_lookup ON product_id
| STATS
    segment_revenue = SUM(revenue),
    segment_units = SUM(quantity),
    avg_transaction = AVG(revenue),
    purchase_frequency = COUNT(*),
    unique_products = COUNT_DISTINCT(product_id)
  BY segment_name, primary_interest, category, brand
| EVAL
    revenue_per_purchase = segment_revenue / GREATEST(purchase_frequency, 1),
    product_diversity = unique_products / GREATEST(purchase_frequency, 1),
    segment_category_affinity = CASE(
      segment_revenue > 50000 AND purchase_frequency > 100, "High Affinity",
      segment_revenue > 20000 AND purchase_frequency > 50, "Medium Affinity",
      "Low Affinity"
    )
| WHERE segment_category_affinity IN ("High Affinity", "Medium Affinity")
| SORT segment_revenue DESC
| LIMIT 30""",
            "expected_use_case": """Use this monthly to understand which customer segments are most valuable 
            for each product category. Tailor marketing campaigns, product bundles, and store layouts to match 
            segment preferences. For example, place premium gear near serious angler sections, family bundles 
            near camping displays.""",
            "parameters": []
        })

        # =================================================================
        # QUERY 5: Semantic Product Discovery for Trend Matching (COMPLEX)
        # Pain Point: Scattered market research data
        # Features: SEMANTIC, WHERE, STATS, LOOKUP JOIN
        # =================================================================
        queries.append({
            "name": "Semantic Product Discovery for Trend Matching",
            "description": """Use semantic search on product descriptions to match emerging market trend topics, 
            then correlate with actual sales performance. This query identifies inventory opportunities by 
            finding products semantically related to trending topics (e.g., 'kayak fishing' trend matches 
            'portable fish finder' and 'waterproof tackle box' products). Discover hidden connections between 
            market demand and existing inventory.""",
            "esql": f"""FROM {catalog_ds}
| WHERE SEMANTIC(product_description, ?trend_query) > 0.75
| EVAL semantic_match_score = SEMANTIC(product_description, ?trend_query)
| LOOKUP JOIN {sales_ds}_lookup ON product_id
| WHERE {timestamp_field} > NOW() - 60 days
| STATS
    recent_revenue = SUM(revenue),
    recent_units = SUM(quantity),
    avg_semantic_score = AVG(semantic_match_score),
    sales_velocity = SUM(quantity) / 60
  BY product_id, product_name, category, subcategory
| EVAL
    opportunity_score = semantic_match_score * sales_velocity,
    inventory_action = CASE(
      semantic_match_score > 0.85 AND sales_velocity > 10, "Increase Stock - High Demand Match",
      semantic_match_score > 0.85 AND sales_velocity < 5, "Promote - Low Awareness",
      semantic_match_score > 0.75 AND sales_velocity > 5, "Monitor - Growing Interest",
      "No Action"
    )
| WHERE inventory_action != "No Action"
| SORT opportunity_score DESC
| LIMIT 25""",
            "expected_use_case": """Run this when market research identifies emerging trends (e.g., 'ice fishing 
            electronics', 'ultralight backpacking'). The semantic search finds related products in your catalog, 
            and sales correlation shows which are already gaining traction vs. which need marketing push. 
            Discover new product category opportunities before competitors.""",
            "parameters": [
                {
                    "name": "trend_query",
                    "type": "string",
                    "description": "Emerging market trend or topic to search for",
                    "example": "kayak fishing accessories"
                }
            ]
        })

        # =================================================================
        # QUERY 6: Multi-Region Seasonal Category Comparison (COMPLEX)
        # Pain Point: Cannot correlate sales spikes with trends/segments
        # Features: STATS, DATE_TRUNC, DATE_EXTRACT, WHERE, EVAL, LOOKUP JOIN, SORT
        # =================================================================
        queries.append({
            "name": "Multi-Region Seasonal Category Comparison with Market Sentiment",
            "description": """Compare seasonal performance across multiple regions (ice fishing in North vs. 
            saltwater fishing in South) with market sentiment to optimize regional inventory allocation. 
            This query solves the pain point of scattered regional data by consolidating sales, product metadata, 
            and market sentiment into a single view. Understand that ice fishing peaks in January in Northeast 
            but saltwater gear peaks year-round in Southeast.""",
            "esql": f"""FROM {sales_ds}
| WHERE {timestamp_field} > NOW() - 1 year
| EVAL
    month = DATE_EXTRACT("month", {timestamp_field}),
    quarter = DATE_TRUNC(3 months, {timestamp_field})
| LOOKUP JOIN {catalog_ds}_lookup ON product_id
| LOOKUP JOIN {trends_ds}_lookup ON region
| WHERE category IN ("Fishing", "Hunting", "Camping")
  AND DATE_EXTRACT("month", {timestamp_field}) == month
| STATS
    quarterly_revenue = SUM(revenue),
    quarterly_units = SUM(quantity),
    avg_sentiment = AVG(sentiment_score),
    search_interest = AVG(search_volume)
  BY quarter, region, category, subcategory, seasonal_tag
| EVAL
    revenue_per_unit = quarterly_revenue / GREATEST(quarterly_units, 1),
    sentiment_adjusted_demand = quarterly_units * (avg_sentiment / 100),
    regional_seasonal_rank = RANK() OVER (PARTITION BY quarter, region ORDER BY quarterly_revenue DESC)
| WHERE regional_seasonal_rank <= 5
| SORT quarter DESC, region, quarterly_revenue DESC
| LIMIT 40""",
            "expected_use_case": """Use this quarterly to optimize regional inventory allocation and distribution 
            center stocking. Identify which categories peak in which regions during which seasons. For example, 
            allocate more ice fishing gear to Northeast stores in Q4, more saltwater tackle to Southeast year-round. 
            Market sentiment helps predict if historical patterns will hold.""",
            "parameters": []
        })

        # =================================================================
        # QUERY 7: Real-Time Product Performance with Change Point Detection (ADVANCED)
        # Pain Point: Product performance analysis takes days instead of minutes
        # Features: CHANGE_POINT, INLINESTATS, STATS, EVAL, LOOKUP JOIN, WHERE
        # =================================================================
        queries.append({
            "name": "Real-Time Product Performance Anomaly Detection",
            "description": """Detect sudden changes in product performance using change point detection combined 
            with inline statistics. This query transforms 'analysis takes days' into real-time alerts. When a 
            product's sales velocity suddenly increases or decreases, CHANGE_POINT identifies the anomaly 
            immediately. Combined with product metadata and customer segments, understand WHY the change happened. 
            Is it a viral social media post? A competitor stockout? A quality issue?""",
            "esql": f"""FROM {sales_ds}
| WHERE {timestamp_field} > NOW() - 30 days
| EVAL day = DATE_TRUNC(1 day, {timestamp_field})
| STATS
    daily_revenue = SUM(revenue),
    daily_units = SUM(quantity)
  BY day, product_id, region
| INLINESTATS
    avg_daily_revenue = AVG(daily_revenue),
    stddev_revenue = STD_DEV(daily_revenue)
  BY product_id
| EVAL
    revenue_zscore = (daily_revenue - avg_daily_revenue) / GREATEST(stddev_revenue, 1),
    performance_status = CASE(
      revenue_zscore > 2, "Significant Spike",
      revenue_zscore < -2, "Significant Drop",
      revenue_zscore > 1, "Moderate Increase",
      revenue_zscore < -1, "Moderate Decrease",
      "Normal"
    )
| CHANGE_POINT daily_revenue
| LOOKUP JOIN {catalog_ds}_lookup ON product_id
| WHERE performance_status IN ("Significant Spike", "Significant Drop")
| STATS
    total_anomaly_revenue = SUM(daily_revenue),
    days_with_anomaly = COUNT(*),
    avg_zscore = AVG(revenue_zscore),
    change_detected = MAX(CASE(change_point IS NOT NULL, 1, 0))
  BY product_id, product_name, category, subcategory, region, performance_status
| WHERE change_detected == 1
| EVAL
    urgency_score = ABS(avg_zscore) * days_with_anomaly,
    action_required = CASE(
      performance_status == "Significant Spike" AND urgency_score > 10, "Rush Restock",
      performance_status == "Significant Spike", "Monitor Inventory",
      performance_status == "Significant Drop" AND urgency_score > 10, "Investigate Quality/Pricing",
      "Review Marketing"
    )
| SORT urgency_score DESC
| LIMIT 20""",
            "expected_use_case": """Run this daily (or set up as real-time alert) to catch product performance 
            anomalies immediately. When a fishing rod suddenly spikes in sales, get alerted within hours instead 
            of discovering it days later when inventory is depleted. When sales drop, investigate before losing 
            more revenue. This transforms reactive analysis into proactive management.""",
            "parameters": []
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum impact"""
        return [
            "Regional Fishing Category Performance Analysis",
            "Customer Segment Purchase Pattern Analysis",
            "Seasonal Demand Prediction for Hunting Equipment",
            "Sales Spike Correlation with Market Trends",
            "Semantic Product Discovery for Trend Matching",
            "Multi-Region Seasonal Category Comparison with Market Sentiment",
            "Real-Time Product Performance Anomaly Detection"
        ]