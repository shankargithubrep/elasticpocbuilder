
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class TecsoQueryGenerator(QueryGeneratorModule):
    """Query generator for Tecso - Market Research
    
    Implements queries for analyzing purchase behavior, customer segmentation,
    and product performance across online and in-store channels.
    """

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate ALL ES|QL queries from pre-planned strategy
        
        Returns queries categorized as scripted, parameterized, or rag for
        customer profiling, segmentation, and purchase pattern analysis.
        """
        queries = []

        # ============================================================
        # SCRIPTED QUERIES - No parameters, ready to run
        # ============================================================

        # Query 1: Customer Segment Revenue Analysis
        queries.append({
            'name': 'Customer Segment Revenue Analysis with Purchase Behavior',
            'description': 'Analyzes revenue by customer segment and purchase channel, calculating key metrics like average transaction value and revenue per customer to identify high-value segments',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_segment_revenue',
                'description': 'Analyzes revenue by customer segment and purchase channel. Identifies high-value segments with transaction metrics and revenue per customer for targeted marketing strategies.',
                'tags': ['analytics', 'revenue', 'segmentation', 'esql', 'customer']
            },
            'query': '''FROM purchase_transactions
| LOOKUP JOIN customers ON customer_id
| STATS 
    total_revenue = SUM(purchase_amount), 
    avg_transaction = AVG(purchase_amount), 
    transaction_count = COUNT(*), 
    unique_customers = COUNT_DISTINCT(customer_id) 
  BY customer_segment, purchase_channel
| EVAL revenue_per_customer = total_revenue / unique_customers
| SORT total_revenue DESC
| LIMIT 20''',
            'query_type': 'scripted',
            'pain_point': 'Need to understand which customer segments drive the most revenue and their purchasing patterns'
        })

        # Query 2: Product Category Performance with Demographics
        queries.append({
            'name': 'Product Category Performance with Customer Demographics',
            'description': 'Identifies which product categories resonate with specific age demographics, enabling targeted marketing campaigns and inventory optimization',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_category_demographics',
                'description': 'Identifies product categories by age demographics. Shows which products resonate with specific age groups for targeted campaigns and inventory planning.',
                'tags': ['analytics', 'demographics', 'products', 'esql', 'targeting']
            },
            'query': '''FROM purchase_transactions
| LOOKUP JOIN products ON product_id
| LOOKUP JOIN customers ON customer_id
| WHERE demographic_age_group IS NOT NULL
| STATS 
    total_units = SUM(quantity), 
    total_revenue = SUM(purchase_amount), 
    avg_basket_size = AVG(quantity) 
  BY product_category, demographic_age_group
| EVAL revenue_per_unit = total_revenue / total_units
| SORT total_revenue DESC
| LIMIT 30''',
            'query_type': 'scripted',
            'pain_point': 'Understanding which products are purchased by specific demographic groups for targeted marketing'
        })

        # Query 3: High-Value Customer Purchase Pattern Comparison
        queries.append({
            'name': 'High-Value Customer Purchase Pattern Comparison',
            'description': 'Identifies high-value customers whose individual purchases significantly exceed their segment average, revealing upsell and VIP engagement opportunities',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_high_value_patterns',
                'description': 'Identifies high-value customers exceeding segment averages. Reveals upsell opportunities and VIP customers for personalized engagement strategies.',
                'tags': ['analytics', 'customer', 'upsell', 'esql', 'vip']
            },
            'query': '''FROM purchase_transactions
| LOOKUP JOIN customers ON customer_id
| WHERE lifetime_value > 1000
| INLINESTATS segment_avg_purchase = AVG(purchase_amount) BY customer_segment
| EVAL purchase_vs_segment_avg = purchase_amount - segment_avg_purchase
| EVAL performance_ratio = purchase_amount / segment_avg_purchase
| WHERE performance_ratio > 1.5
| SORT purchase_vs_segment_avg DESC
| KEEP customer_id, customer_name, customer_segment, purchase_amount, segment_avg_purchase, purchase_vs_segment_avg, performance_ratio
| LIMIT 50''',
            'query_type': 'scripted',
            'pain_point': 'Need to compare individual customer purchase behavior against their segment average to identify upsell opportunities'
        })

        # Query 4: Channel Performance Overview
        queries.append({
            'name': 'Multi-Channel Performance Overview',
            'description': 'Provides comprehensive view of purchase activity across all channels with revenue and customer metrics',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_channel_performance',
                'description': 'Analyzes purchase performance across online, mobile, and in-store channels. Compares revenue, transactions, and customer engagement by channel.',
                'tags': ['analytics', 'channel', 'performance', 'esql', 'omnichannel']
            },
            'query': '''FROM purchase_transactions
| STATS 
    total_revenue = SUM(purchase_amount),
    transaction_count = COUNT(*),
    avg_transaction = AVG(purchase_amount),
    unique_customers = COUNT_DISTINCT(customer_id)
  BY purchase_channel
| EVAL revenue_per_customer = total_revenue / unique_customers
| SORT total_revenue DESC''',
            'query_type': 'scripted',
            'pain_point': 'Need visibility into channel performance and customer engagement patterns'
        })

        # Query 5: Top Products by Revenue
        queries.append({
            'name': 'Top Selling Products by Revenue',
            'description': 'Identifies best-selling products with revenue and volume metrics for inventory and merchandising decisions',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_top_products',
                'description': 'Identifies top-selling products by revenue and volume. Provides insights for inventory management and merchandising strategies.',
                'tags': ['analytics', 'products', 'revenue', 'esql', 'merchandising']
            },
            'query': '''FROM purchase_transactions
| LOOKUP JOIN products ON product_id
| STATS 
    total_revenue = SUM(purchase_amount),
    total_units = SUM(quantity),
    transaction_count = COUNT(*),
    avg_price = AVG(purchase_amount)
  BY product_name, product_category, brand
| EVAL revenue_per_transaction = total_revenue / transaction_count
| SORT total_revenue DESC
| LIMIT 25''',
            'query_type': 'scripted',
            'pain_point': 'Need to identify best-selling products for inventory and merchandising optimization'
        })

        # Query 6: Customer Lifetime Value Distribution
        queries.append({
            'name': 'Customer Lifetime Value Distribution by Segment',
            'description': 'Analyzes lifetime value distribution across customer segments to identify most valuable cohorts',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_ltv_distribution',
                'description': 'Analyzes customer lifetime value distribution by segment. Identifies most valuable customer cohorts for retention and growth strategies.',
                'tags': ['analytics', 'customer', 'ltv', 'esql', 'segmentation']
            },
            'query': '''FROM customers
| STATS 
    customer_count = COUNT(*),
    avg_ltv = AVG(lifetime_value),
    total_ltv = SUM(lifetime_value),
    min_ltv = MIN(lifetime_value),
    max_ltv = MAX(lifetime_value)
  BY customer_segment, preferred_channel
| EVAL ltv_per_customer = total_ltv / customer_count
| SORT total_ltv DESC''',
            'query_type': 'scripted',
            'pain_point': 'Understanding customer value distribution across segments for strategic planning'
        })

        # ============================================================
        # PARAMETERIZED QUERIES - User can customize
        # ============================================================

        # Query 7: Parameterized Segment Analysis
        queries.append({
            'name': 'Customer Segment Deep Dive with Time Range',
            'description': 'Analyzes specific customer segment performance over a custom time period with channel breakdown',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_segment_deep_dive',
                'description': 'Analyzes specific customer segment performance over custom time periods. Provides detailed channel breakdown and purchase metrics for strategic segment management.',
                'tags': ['analytics', 'segmentation', 'parameterized', 'esql', 'customer']
            },
            'query': '''FROM purchase_transactions
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| LOOKUP JOIN customers ON customer_id
| WHERE customer_segment == ?segment
| STATS 
    total_revenue = SUM(purchase_amount),
    transaction_count = COUNT(*),
    avg_transaction = AVG(purchase_amount),
    unique_customers = COUNT_DISTINCT(customer_id)
  BY purchase_channel
| EVAL revenue_per_customer = total_revenue / unique_customers
| SORT total_revenue DESC''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'date',
                    'description': 'Start date for analysis period',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'date',
                    'description': 'End date for analysis period',
                    'required': True
                },
                {
                    'name': 'segment',
                    'type': 'keyword',
                    'description': 'Customer segment to analyze (e.g., Premium, Standard, Budget, VIP)',
                    'required': True
                }
            ],
            'pain_point': 'Need flexible analysis of specific customer segments over custom time periods'
        })

        # Query 8: Parameterized Product Category Analysis
        queries.append({
            'name': 'Product Category Performance by Demographics',
            'description': 'Analyzes specific product category performance across demographic groups with time filtering',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_category_analysis',
                'description': 'Analyzes product category performance by age demographics over custom periods. Identifies target demographics for category-specific marketing campaigns.',
                'tags': ['analytics', 'products', 'demographics', 'parameterized', 'esql']
            },
            'query': '''FROM purchase_transactions
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| LOOKUP JOIN products ON product_id
| LOOKUP JOIN customers ON customer_id
| WHERE product_category == ?category
| WHERE demographic_age_group IS NOT NULL
| STATS 
    total_revenue = SUM(purchase_amount),
    total_units = SUM(quantity),
    avg_basket_size = AVG(quantity),
    unique_customers = COUNT_DISTINCT(customer_id)
  BY demographic_age_group, purchase_channel
| EVAL revenue_per_customer = total_revenue / unique_customers
| SORT total_revenue DESC''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'date',
                    'description': 'Start date for analysis period',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'date',
                    'description': 'End date for analysis period',
                    'required': True
                },
                {
                    'name': 'category',
                    'type': 'keyword',
                    'description': 'Product category to analyze (e.g., Electronics, Clothing, Home & Garden)',
                    'required': True
                }
            ],
            'pain_point': 'Understanding demographic preferences for specific product categories'
        })

        # Query 9: Parameterized Channel Comparison
        queries.append({
            'name': 'Channel Performance Comparison with Filters',
            'description': 'Compares performance across purchase channels with flexible segment and time filtering',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_channel_comparison',
                'description': 'Compares online, mobile, and in-store channel performance with segment filters. Provides insights for omnichannel strategy optimization.',
                'tags': ['analytics', 'channel', 'comparison', 'parameterized', 'esql']
            },
            'query': '''FROM purchase_transactions
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| LOOKUP JOIN customers ON customer_id
| WHERE customer_segment == ?segment
| STATS 
    total_revenue = SUM(purchase_amount),
    transaction_count = COUNT(*),
    avg_transaction = AVG(purchase_amount),
    total_units = SUM(quantity),
    unique_customers = COUNT_DISTINCT(customer_id)
  BY purchase_channel
| EVAL revenue_per_customer = total_revenue / unique_customers
| EVAL units_per_transaction = TO_DOUBLE(total_units) / transaction_count
| SORT total_revenue DESC''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'date',
                    'description': 'Start date for analysis period',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'date',
                    'description': 'End date for analysis period',
                    'required': True
                },
                {
                    'name': 'segment',
                    'type': 'keyword',
                    'description': 'Customer segment to filter (e.g., Premium, Standard, Budget, VIP)',
                    'required': True
                }
            ],
            'pain_point': 'Need flexible comparison of channel performance across customer segments'
        })

        # Query 10: Parameterized Brand Performance
        queries.append({
            'name': 'Brand Performance Analysis by Customer Segment',
            'description': 'Analyzes specific brand performance across customer segments with time filtering',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_brand_performance',
                'description': 'Analyzes brand performance across customer segments over custom periods. Identifies which segments prefer specific brands for partnership strategies.',
                'tags': ['analytics', 'brand', 'segmentation', 'parameterized', 'esql']
            },
            'query': '''FROM purchase_transactions
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| LOOKUP JOIN products ON product_id
| LOOKUP JOIN customers ON customer_id
| WHERE brand == ?brand
| STATS 
    total_revenue = SUM(purchase_amount),
    total_units = SUM(quantity),
    transaction_count = COUNT(*),
    unique_customers = COUNT_DISTINCT(customer_id)
  BY customer_segment, purchase_channel
| EVAL revenue_per_customer = total_revenue / unique_customers
| EVAL avg_transaction = total_revenue / transaction_count
| SORT total_revenue DESC''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'date',
                    'description': 'Start date for analysis period',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'date',
                    'description': 'End date for analysis period',
                    'required': True
                },
                {
                    'name': 'brand',
                    'type': 'keyword',
                    'description': 'Brand to analyze (e.g., TechPro, ActiveLife, BeautyGlow)',
                    'required': True
                }
            ],
            'pain_point': 'Understanding brand performance across different customer segments'
        })

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries that accept user input
        
        These queries allow market research teams to customize analysis
        by segment, time period, category, and other dimensions.
        """
        queries = []

        # Query 1: Flexible Segment Revenue Dashboard
        queries.append({
            'name': 'Multi-Channel Customer Engagement Dashboard',
            'description': 'Provides comprehensive multi-dimensional view of customer engagement across channels with flexible time ranges and segment filtering',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_engagement_dashboard',
                'description': 'Provides multi-dimensional customer engagement view across channels. Flexible time ranges and segment filters for comprehensive market research analysis.',
                'tags': ['analytics', 'dashboard', 'engagement', 'parameterized', 'esql']
            },
            'query': '''FROM purchase_transactions
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| LOOKUP JOIN customers ON customer_id
| WHERE customer_segment == ?segment
| STATS 
    total_revenue = SUM(purchase_amount),
    transaction_count = COUNT(*),
    avg_transaction = AVG(purchase_amount),
    unique_customers = COUNT_DISTINCT(customer_id),
    total_units = SUM(quantity)
  BY purchase_channel
| EVAL revenue_per_customer = total_revenue / unique_customers
| EVAL units_per_transaction = TO_DOUBLE(total_units) / transaction_count
| SORT total_revenue DESC''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'date',
                    'description': 'Start date for analysis period',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'date',
                    'description': 'End date for analysis period',
                    'required': True
                },
                {
                    'name': 'segment',
                    'type': 'keyword',
                    'description': 'Customer segment to analyze (Premium, Standard, Budget, VIP)',
                    'required': True
                }
            ],
            'pain_point': 'Need a flexible view of customer engagement across online and in-store channels for different time periods'
        })

        # Query 2: Customer Cohort Analysis
        queries.append({
            'name': 'Customer Cohort Purchase Behavior Analysis',
            'description': 'Analyzes purchase behavior for customers acquired during a specific time period',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_cohort_analysis',
                'description': 'Analyzes purchase behavior for customer cohorts by acquisition period. Tracks cohort performance and retention for lifecycle marketing strategies.',
                'tags': ['analytics', 'cohort', 'customer', 'parameterized', 'esql']
            },
            'query': '''FROM customers
| WHERE acquisition_date >= ?cohort_start AND acquisition_date <= ?cohort_end
| LOOKUP JOIN purchase_transactions ON customer_id
| WHERE @timestamp >= ?analysis_start AND @timestamp <= ?analysis_end
| STATS 
    total_revenue = SUM(purchase_amount),
    transaction_count = COUNT(*),
    avg_transaction = AVG(purchase_amount),
    active_customers = COUNT_DISTINCT(customer_id)
  BY customer_segment, purchase_channel
| EVAL revenue_per_customer = total_revenue / active_customers
| SORT total_revenue DESC''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'cohort_start',
                    'type': 'date',
                    'description': 'Start date for customer acquisition cohort',
                    'required': True
                },
                {
                    'name': 'cohort_end',
                    'type': 'date',
                    'description': 'End date for customer acquisition cohort',
                    'required': True
                },
                {
                    'name': 'analysis_start',
                    'type': 'date',
                    'description': 'Start date for purchase analysis period',
                    'required': True
                },
                {
                    'name': 'analysis_end',
                    'type': 'date',
                    'description': 'End date for purchase analysis period',
                    'required': True
                }
            ],
            'pain_point': 'Understanding purchase behavior and retention for specific customer cohorts'
        })

        # Query 3: Product Subcategory Deep Dive
        queries.append({
            'name': 'Product Subcategory Performance with Customer Insights',
            'description': 'Analyzes specific product subcategory performance with customer demographic breakdown',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_subcategory_analysis',
                'description': 'Analyzes product subcategory performance with demographic breakdown. Identifies target audiences for subcategory-specific merchandising strategies.',
                'tags': ['analytics', 'products', 'subcategory', 'parameterized', 'esql']
            },
            'query': '''FROM purchase_transactions
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| LOOKUP JOIN products ON product_id
| LOOKUP JOIN customers ON customer_id
| WHERE product_subcategory == ?subcategory
| STATS 
    total_revenue = SUM(purchase_amount),
    total_units = SUM(quantity),
    avg_price = AVG(purchase_amount),
    unique_customers = COUNT_DISTINCT(customer_id)
  BY demographic_age_group, customer_segment
| EVAL revenue_per_customer = total_revenue / unique_customers
| SORT total_revenue DESC''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'date',
                    'description': 'Start date for analysis period',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'date',
                    'description': 'End date for analysis period',
                    'required': True
                },
                {
                    'name': 'subcategory',
                    'type': 'keyword',
                    'description': 'Product subcategory to analyze (e.g., Garden Tools, Frozen Foods)',
                    'required': True
                }
            ],
            'pain_point': 'Need detailed insights into specific product subcategory performance'
        })

        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using COMPLETION command
        
        Creates semantic search queries for natural language exploration
        of customer profiles, product descriptions, and transaction notes.
        """
        queries = []

        # RAG Query 1: Semantic Product Discovery
        queries.append({
            'name': 'Semantic Product Discovery for Customer Buying Patterns',
            'description': 'Uses semantic search to identify customers who frequently purchase specific product types described in natural language',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_semantic_product_discovery',
                'description': 'Finds customers purchasing specific product types using natural language descriptions. Enables precise customer profiling for targeted campaigns without rigid category filters.',
                'tags': ['rag', 'semantic', 'products', 'customer', 'esql']
            },
            'query': '''FROM purchase_transactions METADATA _id
| LOOKUP JOIN products ON product_id
| LOOKUP JOIN customers ON customer_id
| WHERE MATCH(product_description, ?user_question)
| STATS 
    total_spent = SUM(purchase_amount), 
    purchase_frequency = COUNT(*), 
    avg_order_value = AVG(purchase_amount) 
  BY customer_id, customer_name, customer_segment
| WHERE purchase_frequency >= 3
| SORT total_spent DESC
| LIMIT 25''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Natural language description of products to find (e.g., "premium organic health wellness products", "outdoor camping equipment")',
                    'required': True
                }
            ],
            'pain_point': 'Finding customers who buy specific product types using natural language descriptions rather than rigid category filters'
        })

        # RAG Query 2: Customer Profile Semantic Search
        queries.append({
            'name': 'Customer Profile Semantic Search and Analysis',
            'description': 'Finds customers matching specific behavioral or demographic profiles using natural language queries',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_customer_profile_search',
                'description': 'Finds customers matching behavioral or demographic profiles using natural language. Identifies target audiences for personalized marketing campaigns.',
                'tags': ['rag', 'semantic', 'customer', 'profiling', 'esql']
            },
            'query': '''FROM customers METADATA _id
| WHERE MATCH(customer_profile_description, ?user_question)
| LOOKUP JOIN purchase_transactions ON customer_id
| STATS 
    total_revenue = SUM(purchase_amount),
    transaction_count = COUNT(*),
    avg_transaction = AVG(purchase_amount)
  BY customer_id, customer_name, customer_segment, demographic_age_group, preferred_channel
| SORT total_revenue DESC
| LIMIT 20''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Natural language description of customer profile to find (e.g., "loyal customers who prefer online shopping", "high-value electronics buyers")',
                    'required': True
                }
            ],
            'pain_point': 'Identifying customers with specific behavioral patterns or preferences for targeted campaigns'
        })

        # RAG Query 3: Transaction Pattern Discovery
        queries.append({
            'name': 'Transaction Pattern Semantic Discovery',
            'description': 'Discovers purchase transactions matching specific patterns or behaviors described in natural language',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_transaction_discovery',
                'description': 'Discovers purchase transactions matching specific patterns using natural language. Identifies buying behaviors and trends for market research insights.',
                'tags': ['rag', 'semantic', 'transactions', 'patterns', 'esql']
            },
            'query': '''FROM purchase_transactions METADATA _id
| WHERE MATCH(transaction_notes, ?user_question)
| LOOKUP JOIN customers ON customer_id
| LOOKUP JOIN products ON product_id
| STATS 
    transaction_count = COUNT(*),
    total_revenue = SUM(purchase_amount),
    avg_amount = AVG(purchase_amount),
    total_units = SUM(quantity)
  BY purchase_channel, customer_segment, product_category
| SORT transaction_count DESC
| LIMIT 25''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Natural language description of transaction patterns to find (e.g., "large quantity online orders", "smooth checkout experiences")',
                    'required': True
                }
            ],
            'pain_point': 'Understanding specific transaction patterns and customer behaviors through natural language exploration'
        })

        # RAG Query 4: Product Recommendation Insights
        queries.append({
            'name': 'Product Recommendation Insights with Semantic Search',
            'description': 'Identifies products and their buyers using semantic search for recommendation engine development',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_product_recommendations',
                'description': 'Identifies products and buyer profiles using semantic search. Provides insights for recommendation engine development and cross-sell strategies.',
                'tags': ['rag', 'semantic', 'products', 'recommendations', 'esql']
            },
            'query': '''FROM products METADATA _id
| WHERE MATCH(product_description, ?user_question)
| LOOKUP JOIN purchase_transactions ON product_id
| LOOKUP JOIN customers ON customer_id
| STATS 
    total_revenue = SUM(purchase_amount),
    total_units = SUM(quantity),
    unique_customers = COUNT_DISTINCT(customer_id),
    avg_price = AVG(purchase_amount)
  BY product_name, product_category, brand, customer_segment
| EVAL revenue_per_customer = total_revenue / unique_customers
| SORT total_revenue DESC
| LIMIT 20''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Natural language description of products to find (e.g., "luxury beauty products for premium customers", "affordable tech gadgets")',
                    'required': True
                }
            ],
            'pain_point': 'Building product recommendation strategies based on semantic product understanding'
        })

        # RAG Query 5: Customer Journey Semantic Analysis
        queries.append({
            'name': 'Customer Journey Semantic Analysis',
            'description': 'Analyzes customer purchase journeys using semantic search on profiles and transaction notes',
            'tool_metadata': {
                'tool_id': 'tecso_market_res_journey_analysis',
                'description': 'Analyzes customer purchase journeys using semantic search. Identifies patterns in customer behavior for journey optimization and engagement strategies.',
                'tags': ['rag', 'semantic', 'customer', 'journey', 'esql']
            },
            'query': '''FROM customers METADATA _id
| WHERE MATCH(customer_profile_description, ?user_question)
| LOOKUP JOIN purchase_transactions ON customer_id
| STATS 
    first_purchase = MIN(@timestamp),
    latest_purchase = MAX(@timestamp),
    total_spent = SUM(purchase_amount),
    purchase_count = COUNT(*),
    channels_used = COUNT_DISTINCT(purchase_channel)
  BY customer_id, customer_name, customer_segment, demographic_age_group
| EVAL avg_purchase = total_spent / purchase_count
| SORT total_spent DESC
| LIMIT 25''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Natural language description of customer journey to analyze (e.g., "customers with consistent multi-channel engagement", "high-value loyal shoppers")',
                    'required': True
                }
            ],
            'pain_point': 'Understanding customer purchase journeys and engagement patterns over time'
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum impact
        
        Progression builds from basic analytics to advanced segmentation,
        then parameterized exploration, and finally semantic discovery.
        """
        return [
            # Start with foundational revenue analysis
            'Customer Segment Revenue Analysis with Purchase Behavior',
            
            # Show demographic insights
            'Product Category Performance with Customer Demographics',
            
            # Demonstrate advanced pattern detection
            'High-Value Customer Purchase Pattern Comparison',
            
            # Basic performance metrics
            'Multi-Channel Performance Overview',
            'Top Selling Products by Revenue',
            
            # Customer value analysis
            'Customer Lifetime Value Distribution by Segment',
            
            # Introduce parameterized flexibility
            'Customer Segment Deep Dive with Time Range',
            'Product Category Performance by Demographics',
            'Channel Performance Comparison with Filters',
            'Brand Performance Analysis by Customer Segment',
            
            # Advanced parameterized dashboards
            'Multi-Channel Customer Engagement Dashboard',
            'Customer Cohort Purchase Behavior Analysis',
            'Product Subcategory Performance with Customer Insights',
            
            # Finish with semantic/RAG capabilities
            'Semantic Product Discovery for Customer Buying Patterns',
            'Customer Profile Semantic Search and Analysis',
            'Transaction Pattern Semantic Discovery',
            'Product Recommendation Insights with Semantic Search',
            'Customer Journey Semantic Analysis'
        ]
