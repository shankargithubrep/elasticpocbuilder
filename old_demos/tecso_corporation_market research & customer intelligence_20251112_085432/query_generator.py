
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class TecsoCorporationQueryGenerator(QueryGeneratorModule):
    """Query generator for Tecso Corporation - Market Research & Customer Intelligence
    
    Addresses pain points:
    - No unified customer profile across touchpoints
    - Limited real-time customer segmentation capabilities
    - Insufficient behavioral pattern detection
    - Slow time-to-insight for business stakeholders
    - Lack of predictive customer modeling
    """

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate ALL ES|QL queries from pre-planned strategy"""
        queries = []

        # ============================================================
        # SCRIPTED QUERIES - No parameters, for exploration
        # ============================================================

        # Query 1: Unified Customer 360 Profile with Real-Time Channel Attribution
        queries.append({
            'name': 'Unified Customer 360 Profile with Real-Time Channel Attribution',
            'description': 'Creates unified real-time customer profiles consolidating online and in-store activity with predictive metrics, solving fragmented cross-channel view',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_customer_360',
                'description': 'Consolidates online and in-store customer activity into unified profiles with predictive CLV and churn metrics. Identifies high-value at-risk customers across all touchpoints for immediate retention action.',
                'tags': ['customer_360', 'cross_channel', 'predictive', 'retention', 'esql']
            },
            'query': '''FROM customer_transactions
| LOOKUP JOIN customers ON customer_id
| STATS 
    recent_transaction_count = COUNT(*),
    recent_revenue = SUM(transaction_amount),
    online_transactions = SUM(CASE(channel == "e-commerce", 1, 0)),
    instore_transactions = SUM(CASE(channel == "in-store", 1, 0)),
    avg_order_value = AVG(transaction_amount)
  BY customer_id, customer_name, customer_segment, lifetime_revenue, predicted_clv, churn_probability
| EVAL 
    channel_preference_score = TO_DOUBLE(online_transactions) / (online_transactions + instore_transactions),
    revenue_trend = (recent_revenue / 30) * 365,
    clv_realization_rate = (lifetime_revenue / predicted_clv) * 100
| WHERE customer_segment == "Champions"
| SORT churn_probability DESC, predicted_clv DESC
| LIMIT 100''',
            'query_type': 'scripted',
            'pain_point': 'No unified customer profile across touchpoints - customers appear as separate entities across systems',
            'complexity': 'high'
        })

        # Query 2: Advanced RFM Segmentation with Behavioral Anomaly Detection
        queries.append({
            'name': 'Advanced RFM Segmentation with Behavioral Anomaly Detection',
            'description': 'Real-time RFM segmentation with inline statistical comparison to detect customers deviating from segment norms, enabling immediate intervention',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_rfm_anomaly',
                'description': 'Analyzes customer RFM segments in real-time and detects behavioral anomalies. Identifies declining high-value customers and unexpected growth patterns for proactive engagement.',
                'tags': ['rfm', 'segmentation', 'anomaly_detection', 'behavioral', 'esql']
            },
            'query': '''FROM customer_transactions
| LOOKUP JOIN customers ON customer_id
| STATS 
    recent_spend = SUM(transaction_amount),
    recent_transactions = COUNT(*)
  BY customer_id, customer_name, rfm_segment, rfm_recency_score, rfm_frequency_score, rfm_monetary_score
| INLINESTATS 
    avg_spend_by_segment = AVG(recent_spend),
    avg_transactions_by_segment = AVG(recent_transactions) BY rfm_segment
| EVAL 
    spend_variance_pct = ((recent_spend - avg_spend_by_segment) / avg_spend_by_segment) * 100,
    transaction_variance_pct = ((recent_transactions - avg_transactions_by_segment) / avg_transactions_by_segment) * 100,
    rfm_composite_score = rfm_recency_score + rfm_frequency_score + rfm_monetary_score,
    behavior_anomaly_flag = CASE(
      spend_variance_pct < -30 OR transaction_variance_pct < -30, "declining_risk",
      spend_variance_pct > 50 AND transaction_variance_pct > 30, "high_growth",
      "normal"
    )
| WHERE behavior_anomaly_flag != "normal"
| SORT spend_variance_pct ASC
| LIMIT 500''',
            'query_type': 'scripted',
            'pain_point': 'Limited real-time customer segmentation capabilities - batch processing creates 24+ hour delays in segment updates',
            'complexity': 'high'
        })

        # Query 3: Product Affinity Market Basket Analysis with Cross-Channel Insights
        queries.append({
            'name': 'Product Affinity Market Basket Analysis with Cross-Channel Insights',
            'description': 'Discovers product category affinity patterns across channels with customer concentration metrics for merchandising optimization',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_product_affinity',
                'description': 'Discovers frequently purchased product combinations and category affinities across online and in-store channels. Optimizes merchandising and cross-sell strategies with customer concentration insights.',
                'tags': ['market_basket', 'product_affinity', 'merchandising', 'cross_channel', 'esql']
            },
            'query': '''FROM customer_transactions
| LOOKUP JOIN products ON product_id
| STATS 
    total_purchases = COUNT(*),
    total_revenue = SUM(transaction_amount),
    unique_customers = COUNT_DISTINCT(customer_id),
    online_purchases = SUM(CASE(channel == "e-commerce", 1, 0)),
    instore_purchases = SUM(CASE(channel == "in-store", 1, 0)),
    avg_basket_value = AVG(transaction_amount)
  BY product_category, product_subcategory
| EVAL 
    affinity_score = (TO_DOUBLE(unique_customers) / total_purchases) * 100,
    channel_preference = CASE(
      online_purchases > instore_purchases * 1.5, "online_dominant",
      instore_purchases > online_purchases * 1.5, "instore_dominant",
      "balanced"
    ),
    revenue_per_customer = total_revenue / unique_customers
| WHERE total_purchases >= 50
| SORT affinity_score DESC, total_revenue DESC
| LIMIT 50''',
            'query_type': 'scripted',
            'pain_point': 'Insufficient behavioral pattern detection - manual analysis cannot uncover complex multi-dimensional purchasing patterns',
            'complexity': 'medium'
        })

        # Query 4: Multi-Dimensional Campaign Performance with Real-Time ROI by Segment
        queries.append({
            'name': 'Multi-Dimensional Campaign Performance with Real-Time ROI by Segment',
            'description': 'Parallel multi-dimensional campaign analysis providing instant ROI, segment performance, and channel attribution without manual reconciliation',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_campaign_roi',
                'description': 'Analyzes campaign performance across multiple dimensions in real-time. Calculates ROI, segment effectiveness, and channel attribution to optimize marketing spend and targeting.',
                'tags': ['campaign', 'roi', 'attribution', 'performance', 'esql']
            },
            'query': '''FROM customer_transactions
| WHERE campaign_id IS NOT NULL
| LOOKUP JOIN customers ON customer_id
| LOOKUP JOIN campaigns ON campaign_id
| FORK
  (
    STATS 
      total_campaign_revenue = SUM(transaction_amount),
      total_transactions = COUNT(*),
      unique_customers = COUNT_DISTINCT(customer_id)
    BY campaign_id, campaign_name, campaign_budget, target_segment
    | EVAL 
        campaign_roi = ((total_campaign_revenue - campaign_budget) / campaign_budget) * 100,
        revenue_per_customer = total_campaign_revenue / unique_customers,
        conversion_rate = (TO_DOUBLE(unique_customers) / 10000) * 100
    | SORT campaign_roi DESC
  )
  (
    STATS 
      segment_revenue = SUM(transaction_amount),
      segment_customers = COUNT_DISTINCT(customer_id),
      avg_clv = AVG(predicted_clv)
    BY customer_segment, campaign_type
    | EVAL segment_performance_index = (segment_revenue / segment_customers) * (avg_clv / 1000)
    | SORT segment_performance_index DESC
  )
  (
    STATS 
      channel_revenue = SUM(transaction_amount),
      channel_transactions = COUNT(*)
    BY channel, campaign_name
    | EVAL avg_order_value = channel_revenue / channel_transactions
    | SORT channel_revenue DESC
  )''',
            'query_type': 'scripted',
            'pain_point': 'Slow time-to-insight for business stakeholders - custom analyses take 1-2 weeks to deliver',
            'complexity': 'high'
        })

        # Query 5: Customer Lifetime Value Trend Analysis
        queries.append({
            'name': 'Customer Lifetime Value Trend Analysis',
            'description': 'Analyzes customer lifetime value trends and CLV realization rates across segments to prioritize retention investments',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_clv_trends',
                'description': 'Tracks customer lifetime value realization and trends across segments. Identifies underperforming segments and high-potential customers for targeted value optimization.',
                'tags': ['clv', 'lifetime_value', 'predictive', 'segmentation', 'esql']
            },
            'query': '''FROM customers
| STATS 
    customer_count = COUNT(*),
    avg_lifetime_revenue = AVG(lifetime_revenue),
    avg_predicted_clv = AVG(predicted_clv),
    avg_churn_prob = AVG(churn_probability),
    total_revenue = SUM(lifetime_revenue)
  BY customer_segment, preferred_channel
| EVAL 
    clv_realization_rate = (avg_lifetime_revenue / avg_predicted_clv) * 100,
    revenue_per_customer = total_revenue / customer_count,
    risk_adjusted_value = avg_predicted_clv * (1 - avg_churn_prob)
| SORT risk_adjusted_value DESC
| LIMIT 50''',
            'query_type': 'scripted',
            'pain_point': 'Lack of predictive customer modeling - no forward-looking guidance on customer lifetime value or churn risk',
            'complexity': 'medium'
        })

        # Query 6: Channel Mix and Preference Analysis
        queries.append({
            'name': 'Channel Mix and Preference Analysis',
            'description': 'Analyzes customer channel preferences and cross-channel behavior to optimize omnichannel strategy',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_channel_mix',
                'description': 'Analyzes customer channel preferences and cross-channel shopping patterns. Identifies omnichannel customers and channel-specific opportunities for engagement optimization.',
                'tags': ['channel', 'omnichannel', 'cross_channel', 'customer_behavior', 'esql']
            },
            'query': '''FROM customer_transactions
| LOOKUP JOIN customers ON customer_id
| STATS 
    total_transactions = COUNT(*),
    total_revenue = SUM(transaction_amount),
    ecommerce_trans = SUM(CASE(channel == "e-commerce", 1, 0)),
    instore_trans = SUM(CASE(channel == "in-store", 1, 0)),
    avg_transaction_value = AVG(transaction_amount)
  BY customer_segment, preferred_channel
| EVAL 
    channel_diversity = CASE(
      ecommerce_trans > 0 AND instore_trans > 0, "omnichannel",
      ecommerce_trans > 0, "online_only",
      "instore_only"
    ),
    ecommerce_pct = (TO_DOUBLE(ecommerce_trans) / total_transactions) * 100,
    revenue_per_transaction = total_revenue / total_transactions
| SORT total_revenue DESC
| LIMIT 100''',
            'query_type': 'scripted',
            'pain_point': 'Disconnected purchase data across channels - online e-commerce and in-store POS data fragmented',
            'complexity': 'medium'
        })

        # Query 7: High-Value At-Risk Customer Identification
        queries.append({
            'name': 'High-Value At-Risk Customer Identification',
            'description': 'Identifies high-value customers with elevated churn risk for immediate retention intervention',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_atrisk_vip',
                'description': 'Identifies high-value customers showing elevated churn risk based on predictive models and recent activity. Prioritizes retention efforts by potential revenue loss.',
                'tags': ['churn', 'retention', 'high_value', 'atrisk', 'esql']
            },
            'query': '''FROM customers
| WHERE churn_probability > 0.6
| WHERE predicted_clv > 5000
| LOOKUP JOIN customer_transactions ON customer_id
| STATS 
    last_transaction_date = MAX(`@timestamp`),
    recent_spend = SUM(transaction_amount),
    transaction_count = COUNT(*)
  BY customer_id, customer_name, customer_segment, churn_probability, predicted_clv, lifetime_revenue
| EVAL 
    days_since_purchase = (TO_LONG(NOW()) - TO_LONG(last_transaction_date)) / 86400000,
    retention_priority_score = (predicted_clv * churn_probability) / 1000,
    revenue_at_risk = predicted_clv * churn_probability,
    recommended_action = CASE(
      days_since_purchase > 60 AND predicted_clv > 10000, "urgent_vip_outreach",
      days_since_purchase > 45 AND predicted_clv > 5000, "personalized_offer",
      days_since_purchase > 30, "re_engagement_campaign",
      "monitor"
    )
| WHERE recommended_action != "monitor"
| SORT retention_priority_score DESC
| LIMIT 100''',
            'query_type': 'scripted',
            'pain_point': 'Churn Prediction & Proactive Retention - identify at-risk customers before they lapse',
            'complexity': 'high'
        })

        # Query 8: Product Category Performance by Customer Segment
        queries.append({
            'name': 'Product Category Performance by Customer Segment',
            'description': 'Analyzes product category performance across customer segments to optimize inventory and merchandising',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_category_segment',
                'description': 'Analyzes product category performance across customer segments. Identifies segment-specific preferences and high-margin opportunities for targeted merchandising.',
                'tags': ['product', 'category', 'segmentation', 'merchandising', 'esql']
            },
            'query': '''FROM customer_transactions
| LOOKUP JOIN products ON product_id
| LOOKUP JOIN customers ON customer_id
| STATS 
    total_revenue = SUM(transaction_amount),
    transaction_count = COUNT(*),
    unique_customers = COUNT_DISTINCT(customer_id),
    avg_margin = AVG(margin_percentage),
    avg_price = AVG(unit_price)
  BY product_category, customer_segment
| EVAL 
    revenue_per_customer = total_revenue / unique_customers,
    avg_basket_value = total_revenue / transaction_count,
    margin_dollars = total_revenue * (avg_margin / 100)
| WHERE transaction_count >= 10
| SORT margin_dollars DESC
| LIMIT 100''',
            'query_type': 'scripted',
            'pain_point': 'Insufficient behavioral pattern detection - manual analysis cannot uncover complex multi-dimensional purchasing patterns',
            'complexity': 'medium'
        })

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries that accept user input"""
        queries = []

        # Query 1: Customer 360 Profile by Segment (Parameterized)
        queries.append({
            'name': 'Customer 360 Profile by Segment - Parameterized',
            'description': 'Unified customer profiles filtered by segment and time range with predictive metrics',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_customer_360_param',
                'description': 'Retrieves unified customer profiles for a specific segment and date range. Shows cross-channel activity, CLV metrics, and churn risk for targeted analysis.',
                'tags': ['customer_360', 'parameterized', 'segmentation', 'predictive', 'esql']
            },
            'query': '''FROM customer_transactions
| WHERE `@timestamp` >= ?start_date AND `@timestamp` <= ?end_date
| LOOKUP JOIN customers ON customer_id
| STATS 
    recent_transaction_count = COUNT(*),
    recent_revenue = SUM(transaction_amount),
    online_transactions = SUM(CASE(channel == "e-commerce", 1, 0)),
    instore_transactions = SUM(CASE(channel == "in-store", 1, 0)),
    avg_order_value = AVG(transaction_amount)
  BY customer_id, customer_name, customer_segment, lifetime_revenue, predicted_clv, churn_probability
| EVAL 
    channel_preference_score = TO_DOUBLE(online_transactions) / (online_transactions + instore_transactions),
    clv_realization_rate = (lifetime_revenue / predicted_clv) * 100
| WHERE customer_segment == ?segment
| SORT churn_probability DESC, predicted_clv DESC
| LIMIT ?limit''',
            'query_type': 'parameterized',
            'parameters': [
                {'name': 'start_date', 'type': 'date', 'description': 'Start date for analysis period'},
                {'name': 'end_date', 'type': 'date', 'description': 'End date for analysis period'},
                {'name': 'segment', 'type': 'keyword', 'description': 'Customer segment to analyze (e.g., Champions, Loyal Customers)'},
                {'name': 'limit', 'type': 'integer', 'description': 'Maximum number of customers to return', 'default': 100}
            ],
            'pain_point': 'No unified customer profile across touchpoints - customers appear as separate entities across systems',
            'complexity': 'high'
        })

        # Query 2: Campaign Performance Analysis (Parameterized)
        queries.append({
            'name': 'Campaign Performance Analysis - Parameterized',
            'description': 'Analyzes campaign effectiveness with ROI calculation for specific campaign type and date range',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_campaign_param',
                'description': 'Analyzes campaign performance for a specific campaign type and time period. Calculates ROI, customer acquisition, and revenue metrics for marketing optimization.',
                'tags': ['campaign', 'roi', 'parameterized', 'marketing', 'esql']
            },
            'query': '''FROM customer_transactions
| WHERE `@timestamp` >= ?start_date AND `@timestamp` <= ?end_date
| WHERE campaign_id IS NOT NULL
| LOOKUP JOIN campaigns ON campaign_id
| WHERE campaign_type == ?campaign_type
| STATS 
    total_revenue = SUM(transaction_amount),
    total_transactions = COUNT(*),
    unique_customers = COUNT_DISTINCT(customer_id),
    total_budget = SUM(campaign_budget)
  BY campaign_id, campaign_name, target_segment
| EVAL 
    campaign_roi = ((total_revenue - total_budget) / total_budget) * 100,
    revenue_per_customer = total_revenue / unique_customers,
    avg_transaction_value = total_revenue / total_transactions
| SORT campaign_roi DESC
| LIMIT ?limit''',
            'query_type': 'parameterized',
            'parameters': [
                {'name': 'start_date', 'type': 'date', 'description': 'Campaign analysis start date'},
                {'name': 'end_date', 'type': 'date', 'description': 'Campaign analysis end date'},
                {'name': 'campaign_type', 'type': 'keyword', 'description': 'Type of campaign (e.g., Email, Social Media, Direct Mail)'},
                {'name': 'limit', 'type': 'integer', 'description': 'Maximum number of campaigns to return', 'default': 50}
            ],
            'pain_point': 'Real-Time Campaign Performance & Attribution Analysis - measure marketing campaign effectiveness across customer segments',
            'complexity': 'medium'
        })

        # Query 3: Product Affinity by Category (Parameterized)
        queries.append({
            'name': 'Product Affinity by Category - Parameterized',
            'description': 'Analyzes product purchase patterns for specific category with cross-channel insights',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_affinity_param',
                'description': 'Analyzes product affinity and purchase patterns for a specific product category. Identifies cross-sell opportunities and channel preferences for merchandising.',
                'tags': ['product_affinity', 'parameterized', 'merchandising', 'cross_sell', 'esql']
            },
            'query': '''FROM customer_transactions
| WHERE `@timestamp` >= ?start_date AND `@timestamp` <= ?end_date
| LOOKUP JOIN products ON product_id
| WHERE product_category == ?category
| STATS 
    total_purchases = COUNT(*),
    total_revenue = SUM(transaction_amount),
    unique_customers = COUNT_DISTINCT(customer_id),
    online_purchases = SUM(CASE(channel == "e-commerce", 1, 0)),
    instore_purchases = SUM(CASE(channel == "in-store", 1, 0))
  BY product_subcategory, product_category
| EVAL 
    affinity_score = (TO_DOUBLE(unique_customers) / total_purchases) * 100,
    revenue_per_customer = total_revenue / unique_customers,
    online_pct = (TO_DOUBLE(online_purchases) / total_purchases) * 100
| WHERE total_purchases >= ?min_purchases
| SORT total_revenue DESC
| LIMIT ?limit''',
            'query_type': 'parameterized',
            'parameters': [
                {'name': 'start_date', 'type': 'date', 'description': 'Analysis period start date'},
                {'name': 'end_date', 'type': 'date', 'description': 'Analysis period end date'},
                {'name': 'category', 'type': 'keyword', 'description': 'Product category to analyze (e.g., Electronics, Clothing)'},
                {'name': 'min_purchases', 'type': 'integer', 'description': 'Minimum purchase count threshold', 'default': 10},
                {'name': 'limit', 'type': 'integer', 'description': 'Maximum number of subcategories to return', 'default': 50}
            ],
            'pain_point': 'Product Affinity & Market Basket Analysis - discover frequently purchased product combinations for merchandising optimization',
            'complexity': 'medium'
        })

        # Query 4: At-Risk Customer Analysis (Parameterized)
        queries.append({
            'name': 'At-Risk Customer Analysis - Parameterized',
            'description': 'Identifies at-risk customers above specified churn threshold with retention priority scoring',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_atrisk_param',
                'description': 'Identifies customers above a specified churn probability threshold. Calculates retention priority scores and recommends intervention actions based on value and risk.',
                'tags': ['churn', 'retention', 'parameterized', 'atrisk', 'esql']
            },
            'query': '''FROM customers
| WHERE churn_probability >= ?churn_threshold
| WHERE predicted_clv >= ?min_clv
| LOOKUP JOIN customer_transactions ON customer_id
| WHERE `@timestamp` >= ?start_date AND `@timestamp` <= ?end_date
| STATS 
    last_transaction_date = MAX(`@timestamp`),
    recent_spend = SUM(transaction_amount),
    transaction_count = COUNT(*)
  BY customer_id, customer_name, customer_segment, churn_probability, predicted_clv, lifetime_revenue
| EVAL 
    days_since_purchase = (TO_LONG(NOW()) - TO_LONG(last_transaction_date)) / 86400000,
    retention_priority_score = (predicted_clv * churn_probability) / 1000,
    revenue_at_risk = predicted_clv * churn_probability
| SORT retention_priority_score DESC
| LIMIT ?limit''',
            'query_type': 'parameterized',
            'parameters': [
                {'name': 'start_date', 'type': 'date', 'description': 'Start date for recent activity analysis'},
                {'name': 'end_date', 'type': 'date', 'description': 'End date for recent activity analysis'},
                {'name': 'churn_threshold', 'type': 'float', 'description': 'Minimum churn probability (0.0-1.0)', 'default': 0.6},
                {'name': 'min_clv', 'type': 'float', 'description': 'Minimum predicted CLV threshold', 'default': 5000},
                {'name': 'limit', 'type': 'integer', 'description': 'Maximum number of customers to return', 'default': 100}
            ],
            'pain_point': 'Churn Prediction & Proactive Retention - identify at-risk customers before they lapse',
            'complexity': 'high'
        })

        # Query 5: RFM Segment Performance (Parameterized)
        queries.append({
            'name': 'RFM Segment Performance - Parameterized',
            'description': 'Analyzes RFM segment performance with behavioral variance detection for specific segment',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_rfm_param',
                'description': 'Analyzes RFM segment performance and detects customers deviating from segment norms. Identifies declining customers and growth opportunities within a specific segment.',
                'tags': ['rfm', 'segmentation', 'parameterized', 'behavioral', 'esql']
            },
            'query': '''FROM customer_transactions
| WHERE `@timestamp` >= ?start_date AND `@timestamp` <= ?end_date
| LOOKUP JOIN customers ON customer_id
| WHERE rfm_segment == ?segment
| STATS 
    recent_spend = SUM(transaction_amount),
    recent_transactions = COUNT(*)
  BY customer_id, customer_name, rfm_segment, rfm_recency_score, rfm_frequency_score, rfm_monetary_score
| INLINESTATS 
    avg_spend_by_segment = AVG(recent_spend),
    avg_transactions_by_segment = AVG(recent_transactions) BY rfm_segment
| EVAL 
    spend_variance_pct = ((recent_spend - avg_spend_by_segment) / avg_spend_by_segment) * 100,
    transaction_variance_pct = ((recent_transactions - avg_transactions_by_segment) / avg_transactions_by_segment) * 100,
    rfm_composite_score = rfm_recency_score + rfm_frequency_score + rfm_monetary_score
| WHERE ABS(spend_variance_pct) >= ?variance_threshold OR ABS(transaction_variance_pct) >= ?variance_threshold
| SORT spend_variance_pct ASC
| LIMIT ?limit''',
            'query_type': 'parameterized',
            'parameters': [
                {'name': 'start_date', 'type': 'date', 'description': 'Analysis period start date'},
                {'name': 'end_date', 'type': 'date', 'description': 'Analysis period end date'},
                {'name': 'segment', 'type': 'keyword', 'description': 'RFM segment to analyze (e.g., Champions, Loyal Customers)'},
                {'name': 'variance_threshold', 'type': 'float', 'description': 'Minimum variance percentage to flag anomalies', 'default': 30},
                {'name': 'limit', 'type': 'integer', 'description': 'Maximum number of customers to return', 'default': 100}
            ],
            'pain_point': 'Advanced Customer Segmentation with RFM Analysis - automatically segment customers using Recency, Frequency, Monetary analysis',
            'complexity': 'high'
        })

        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using semantic search on customer behavior profiles"""
        queries = []

        # RAG Query 1: Semantic Customer Behavior Discovery for Retention
        queries.append({
            'name': 'Semantic Customer Behavior Discovery for Retention Targeting',
            'description': 'Uses semantic search to intelligently identify at-risk high-value customers with declining patterns, providing actionable retention priorities',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_semantic_retention',
                'description': 'Searches customer behavior profiles using natural language to find at-risk high-value customers. Provides retention priority scores and recommended actions based on semantic understanding of customer patterns.',
                'tags': ['semantic', 'rag', 'retention', 'churn', 'esql']
            },
            'query': '''FROM customers METADATA _id
| WHERE MATCH(customer_behavior_profile, ?user_question, {"fuzziness": "AUTO"})
| WHERE churn_probability > 0.6
| LOOKUP JOIN customer_transactions ON customer_id
| WHERE `@timestamp` >= NOW() - 180 days
| STATS 
    last_transaction_date = MAX(`@timestamp`),
    total_recent_spend = SUM(transaction_amount),
    transaction_frequency = COUNT(*)
  BY customer_id, customer_name, churn_probability, predicted_clv, customer_segment, customer_behavior_profile, _id
| EVAL 
    days_since_purchase = (TO_LONG(NOW()) - TO_LONG(last_transaction_date)) / 86400000,
    retention_priority_score = (predicted_clv * churn_probability) / 1000,
    recommended_action = CASE(
      days_since_purchase > 60 AND predicted_clv > 5000, "urgent_vip_outreach",
      days_since_purchase > 45 AND predicted_clv > 2000, "personalized_offer",
      days_since_purchase > 30, "re_engagement_campaign",
      "monitor"
    )
| WHERE recommended_action != "monitor"
| SORT retention_priority_score DESC
| LIMIT 5
| KEEP customer_id, customer_name, customer_segment, churn_probability, predicted_clv, days_since_purchase, retention_priority_score, recommended_action, customer_behavior_profile, _score
| EVAL prompt = CONCAT(
    "Based on the following customer behavior profiles and metrics, provide retention recommendations:\n\n",
    "Question: ", ?user_question, "\n\n",
    "Customer Data:\n",
    "- Customer: ", customer_name, " (", customer_segment, ")\n",
    "- Churn Probability: ", TO_STRING(churn_probability), "\n",
    "- Predicted CLV: $", TO_STRING(predicted_clv), "\n",
    "- Days Since Purchase: ", TO_STRING(days_since_purchase), "\n",
    "- Retention Priority Score: ", TO_STRING(retention_priority_score), "\n",
    "- Recommended Action: ", recommended_action, "\n",
    "- Behavior Profile: ", customer_behavior_profile, "\n\n",
    "Provide specific, actionable retention strategies for these at-risk customers."
  )
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP customer_name, customer_segment, churn_probability, predicted_clv, recommended_action, answer''',
            'query_type': 'rag',
            'pain_point': 'Churn Prediction & Proactive Retention - identify at-risk customers before they lapse',
            'complexity': 'high'
        })

        # RAG Query 2: Semantic Customer Segment Analysis
        queries.append({
            'name': 'Semantic Customer Segment Profile Analysis',
            'description': 'Uses semantic search to discover customer segments matching specific behavioral characteristics for persona development',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_semantic_persona',
                'description': 'Searches customer behavior profiles to identify segments matching specific characteristics. Generates detailed persona insights and engagement recommendations using AI analysis.',
                'tags': ['semantic', 'rag', 'persona', 'segmentation', 'esql']
            },
            'query': '''FROM customers METADATA _id
| WHERE MATCH(customer_behavior_profile, ?user_question, {"fuzziness": "AUTO"})
| STATS 
    customer_count = COUNT(*),
    avg_lifetime_revenue = AVG(lifetime_revenue),
    avg_predicted_clv = AVG(predicted_clv),
    avg_churn_prob = AVG(churn_probability),
    avg_purchase_count = AVG(purchase_count)
  BY customer_segment, preferred_channel, rfm_segment
| EVAL 
    clv_realization_rate = (avg_lifetime_revenue / avg_predicted_clv) * 100,
    revenue_per_customer = avg_lifetime_revenue
| SORT customer_count DESC
| LIMIT 5
| EVAL prompt = CONCAT(
    "Analyze the following customer segment profiles and provide persona insights:\n\n",
    "Question: ", ?user_question, "\n\n",
    "Segment Data:\n",
    "- Segment: ", customer_segment, " (RFM: ", rfm_segment, ")\n",
    "- Customer Count: ", TO_STRING(customer_count), "\n",
    "- Preferred Channel: ", preferred_channel, "\n",
    "- Avg Lifetime Revenue: $", TO_STRING(avg_lifetime_revenue), "\n",
    "- Avg Predicted CLV: $", TO_STRING(avg_predicted_clv), "\n",
    "- CLV Realization Rate: ", TO_STRING(clv_realization_rate), "%\n",
    "- Avg Churn Probability: ", TO_STRING(avg_churn_prob), "\n",
    "- Avg Purchase Count: ", TO_STRING(avg_purchase_count), "\n\n",
    "Provide detailed persona characteristics, behavioral patterns, and engagement strategies for this segment."
  )
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP customer_segment, rfm_segment, preferred_channel, customer_count, avg_lifetime_revenue, avg_predicted_clv, answer''',
            'query_type': 'rag',
            'pain_point': 'Customer Segment Profile & Persona Development - build detailed behavioral profiles for each customer segment',
            'complexity': 'high'
        })

        # RAG Query 3: Semantic Product Recommendation Discovery
        queries.append({
            'name': 'Semantic Product Recommendation Discovery',
            'description': 'Uses semantic search on product descriptions to find relevant products for specific customer needs or use cases',
            'tool_metadata': {
                'tool_id': 'tecso_corporati_market_res_semantic_product',
                'description': 'Searches product catalog using natural language to find relevant products. Provides AI-powered recommendations based on product features, customer segments, and purchase patterns.',
                'tags': ['semantic', 'rag', 'product', 'recommendation', 'esql']
            },
            'query': '''FROM products METADATA _id
| WHERE MATCH(product_description, ?user_question, {"fuzziness": "AUTO"})
| LOOKUP JOIN customer_transactions ON product_id
| STATS 
    total_purchases = COUNT(*),
    total_revenue = SUM(transaction_amount),
    unique_customers = COUNT_DISTINCT(customer_id),
    avg_transaction_value = AVG(transaction_amount)
  BY product_id, product_name, product_category, product_subcategory, unit_price, margin_percentage, product_description, _id
| EVAL 
    revenue_per_customer = total_revenue / unique_customers,
    customer_penetration = unique_customers
| WHERE total_purchases >= 5
| SORT total_revenue DESC
| LIMIT 5
| KEEP product_name, product_category, product_subcategory, unit_price, margin_percentage, total_purchases, total_revenue, unique_customers, product_description, _score
| EVAL prompt = CONCAT(
    "Analyze the following products and provide recommendations:\n\n",
    "Question: ", ?user_question, "\n\n",
    "Product Data:\n",
    "- Product: ", product_name, "\n",
    "- Category: ", product_category, " / ", product_subcategory, "\n",
    "- Unit Price: $", TO_STRING(unit_price), "\n",
    "- Margin: ", TO_STRING(margin_percentage), "%\n",
    "- Total Purchases: ", TO_STRING(total_purchases), "\n",
    "- Total Revenue: $", TO_STRING(total_revenue), "\n",
    "- Unique Customers: ", TO_STRING(unique_customers), "\n",
    "- Description: ", product_description, "\n\n",
    "Provide product recommendations, cross-sell opportunities, and merchandising strategies."
  )
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP product_name, product_category, unit_price, total_revenue, unique_customers, answer''',
            'query_type': 'rag',
            'pain_point': 'Product Affinity & Market Basket Analysis - discover frequently purchased product combinations for merchandising optimization',
            'complexity': 'high'
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum impact
        
        Progression strategy:
        1. Start with unified customer view (core pain point)
        2. Show real-time segmentation capabilities
        3. Demonstrate cross-channel insights
        4. Highlight predictive capabilities
        5. Show semantic/AI-powered analysis
        """
        return [
            # Core customer intelligence
            'Unified Customer 360 Profile with Real-Time Channel Attribution',
            'Customer 360 Profile by Segment - Parameterized',
            
            # Segmentation and behavioral analysis
            'Advanced RFM Segmentation with Behavioral Anomaly Detection',
            'RFM Segment Performance - Parameterized',
            'Customer Lifetime Value Trend Analysis',
            
            # Product and merchandising insights
            'Product Affinity Market Basket Analysis with Cross-Channel Insights',
            'Product Affinity by Category - Parameterized',
            'Product Category Performance by Customer Segment',
            
            # Campaign performance
            'Multi-Dimensional Campaign Performance with Real-Time ROI by Segment',
            'Campaign Performance Analysis - Parameterized',
            
            # Retention and churn
            'High-Value At-Risk Customer Identification',
            'At-Risk Customer Analysis - Parameterized',
            
            # Channel analysis
            'Channel Mix and Preference Analysis',
            
            # AI-powered semantic analysis
            'Semantic Customer Behavior Discovery for Retention Targeting',
            'Semantic Customer Segment Profile Analysis',
            'Semantic Product Recommendation Discovery'
        ]
