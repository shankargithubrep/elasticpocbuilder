
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class AdobeIncQueryGenerator(QueryGeneratorModule):
    """Query generator for Adobe Inc. - Brand Concierge Product Management & Engineering
    
    Addresses critical pain points:
    - Multi-tenant performance isolation (noisy neighbor detection)
    - Slow feedback loops on product releases (4-6 weeks → 3-7 days)
    - Fragmented product usage visibility across disparate sources
    - Disconnected UX and technical performance correlation
    - No early warning system for customer health ($8-12M annual churn)
    """

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate ALL ES|QL queries from pre-planned strategy"""
        queries = []

        # ==================== SCRIPTED QUERIES ====================
        # These queries don't take parameters and are immediately testable
        
        # Query 1: Noisy Neighbor Detection with Tenant Context
        queries.append({
            "name": "Noisy Neighbor Detection with Tenant Context",
            "description": "Identifies tenants consuming disproportionate resources by comparing their P95 latency and request volume against the average, calculating a noisy neighbor score, and flagging SLA breaches with revenue impact",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_noisy_neighbor_detection",
                "description": "Identifies noisy neighbor tenants causing performance issues. Detects resource-hogging accounts affecting multi-tenant SLA compliance with revenue impact scoring for prioritization.",
                "tags": ["performance", "multi-tenant", "sla", "monitoring", "esql"]
            },
            "query": """FROM api_requests
| STATS p95_latency = PERCENTILE(response_time_ms, 95), request_volume = COUNT(*) BY tenant_id
| LOOKUP JOIN tenants ON tenant_id
| INLINESTATS avg_p95 = AVG(p95_latency), avg_volume = AVG(request_volume)
| EVAL latency_vs_avg_pct = ((p95_latency - avg_p95) / avg_p95) * 100
| EVAL volume_vs_avg_pct = ((request_volume - avg_volume) / avg_volume) * 100
| EVAL noisy_neighbor_score = (latency_vs_avg_pct * 0.4) + (volume_vs_avg_pct * 0.6)
| EVAL sla_breach = CASE(p95_latency > sla_target_p95_ms, true, false)
| WHERE noisy_neighbor_score > 50 OR sla_breach == true
| EVAL revenue_impact = contract_arr / 12 / 30
| SORT noisy_neighbor_score DESC
| KEEP tenant_id, tenant_name, account_tier, p95_latency, sla_target_p95_ms, noisy_neighbor_score, sla_breach, revenue_impact
| LIMIT 20""",
            "query_type": "scripted",
            "pain_point": "Multi-tenant performance isolation challenges - noisy neighbor problems require manual log analysis to identify",
            "complexity": "high"
        })

        # Query 2: At-Risk Customer Early Warning System
        queries.append({
            "name": "At-Risk Customer Early Warning System",
            "description": "Calculates customer health scores based on feature usage and engagement patterns, identifies at-risk accounts 60-90 days before renewal with churn probability, and quantifies potential revenue loss for prioritization",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_churn_early_warning",
                "description": "Identifies at-risk customers 60-90 days before renewal using health scoring. Predicts churn probability and revenue impact to prevent $8-12M annual losses through proactive intervention.",
                "tags": ["churn", "customer-health", "revenue", "analytics", "esql"]
            },
            "query": """FROM feature_usage_events
| STATS feature_dau = COUNT_DISTINCT(user_id), feature_events = COUNT(*) BY tenant_id
| LOOKUP JOIN tenants ON tenant_id
| EVAL days_to_renewal = (TO_LONG(renewal_date) - TO_LONG(NOW())) / 86400000
| EVAL usage_trend_score = CASE(
    feature_dau < 5, 20,
    feature_dau < 15, 50,
    feature_dau < 50, 70,
    85
  )
| EVAL engagement_score = CASE(
    feature_events < 100, 25,
    feature_events < 500, 55,
    feature_events < 2000, 75,
    90
  )
| EVAL health_score = (usage_trend_score * 0.6) + (engagement_score * 0.4)
| EVAL churn_risk_probability = CASE(
    health_score < 40, 0.85,
    health_score < 55, 0.65,
    health_score < 70, 0.35,
    0.15
  )
| WHERE days_to_renewal <= 90 AND days_to_renewal > 0 AND churn_risk_probability >= 0.35
| EVAL potential_revenue_loss = contract_arr * churn_risk_probability
| SORT churn_risk_probability DESC, potential_revenue_loss DESC
| KEEP tenant_id, tenant_name, health_score, churn_risk_probability, days_to_renewal, contract_arr, potential_revenue_loss, customer_success_manager, feature_dau
| LIMIT 50""",
            "query_type": "scripted",
            "pain_point": "No early warning system for customer health - at-risk accounts identified only 30-60 days before renewal, costing $8-12M annually in preventable churn",
            "complexity": "high"
        })

        # Query 3: API Partner Integration Health Monitoring
        queries.append({
            "name": "API Partner Integration Health Monitoring",
            "description": "Monitors API partner integration health by tracking success rates over time, detecting degradation events, and prioritizing issues by partner tier and severity",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_partner_health",
                "description": "Monitors third-party API integration health across 40+ partners. Detects degradation patterns and prioritizes critical issues by partner tier to prevent escalation and churn.",
                "tags": ["partners", "integrations", "api", "monitoring", "esql"]
            },
            "query": """FROM api_requests
| WHERE partner_id IS NOT NULL
| EVAL success = CASE(http_status >= 200 AND http_status < 300, 1, 0)
| STATS 
    avg_success_rate = (SUM(success) / COUNT(*)) * 100,
    min_success_rate = MIN(CASE(success == 1, 100, 0)),
    total_requests_7d = COUNT(*)
  BY partner_id
| LOOKUP JOIN api_partners ON partner_id
| EVAL health_status = CASE(
    avg_success_rate >= 99.5, "healthy",
    avg_success_rate >= 98, "monitoring",
    avg_success_rate >= 95, "at_risk",
    "critical"
  )
| WHERE health_status IN ("at_risk", "critical")
| EVAL priority = CASE(
    tier == "Platinum" AND health_status == "critical", 1,
    tier == "Platinum" AND health_status == "at_risk", 2,
    health_status == "critical", 3,
    4
  )
| SORT priority ASC, avg_success_rate ASC
| KEEP partner_id, partner_name, tier, avg_success_rate, min_success_rate, health_status, total_requests_7d, priority
| LIMIT 30""",
            "query_type": "scripted",
            "pain_point": "API Partner Ecosystem Health Monitoring - ensure third-party integrations operate reliably, maintain partner satisfaction, identify issues before they escalate to partner churn",
            "complexity": "high"
        })

        # Query 4: Multi-Tenant SLA Compliance Dashboard
        queries.append({
            "name": "Multi-Tenant SLA Compliance Dashboard",
            "description": "Real-time SLA compliance monitoring across all tenants with P95 latency tracking, breach detection, and uptime calculation",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_sla_compliance",
                "description": "Tracks SLA compliance across 850+ tenants in real-time. Monitors P95 latency targets and uptime guarantees to ensure fair resource allocation and prevent SLA violations.",
                "tags": ["sla", "compliance", "performance", "monitoring", "esql"]
            },
            "query": """FROM api_requests
| STATS 
    p95_latency = PERCENTILE(response_time_ms, 95),
    total_requests = COUNT(*),
    error_count = SUM(CASE(http_status >= 500, 1, 0))
  BY tenant_id, region
| LOOKUP JOIN tenants ON tenant_id
| EVAL uptime_pct = ((total_requests - error_count) / total_requests) * 100
| EVAL sla_breach = CASE(p95_latency > sla_target_p95_ms OR uptime_pct < 99.9, true, false)
| EVAL latency_margin = sla_target_p95_ms - p95_latency
| WHERE sla_breach == true OR latency_margin < 50
| SORT latency_margin ASC
| KEEP tenant_id, tenant_name, account_tier, region, p95_latency, sla_target_p95_ms, uptime_pct, sla_breach, contract_arr
| LIMIT 50""",
            "query_type": "scripted",
            "pain_point": "Multi-Tenant Performance Monitoring & SLA Management - ensure fair resource allocation across 850+ tenants, detect noisy neighbor situations, guarantee SLA compliance",
            "complexity": "medium"
        })

        # Query 5: Feature Adoption Velocity Analysis
        queries.append({
            "name": "Feature Adoption Velocity Analysis",
            "description": "Tracks feature adoption rates and engagement velocity across account tiers to identify successful features and lagging adoption",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_feature_adoption",
                "description": "Analyzes feature adoption velocity across customer segments. Identifies high-performing features and lagging adoption patterns to optimize product strategy and reduce feedback loops from 4-6 weeks to days.",
                "tags": ["features", "adoption", "analytics", "product", "esql"]
            },
            "query": """FROM feature_usage_events
| STATS 
    unique_users = COUNT_DISTINCT(user_id),
    total_interactions = COUNT(*),
    avg_duration_ms = AVG(interaction_duration_ms),
    conversion_count = SUM(CASE(conversion_event == true, 1, 0))
  BY feature_name, feature_category
| EVAL conversion_rate = (conversion_count / total_interactions) * 100
| EVAL engagement_score = CASE(
    unique_users >= 1000 AND conversion_rate >= 50, 90,
    unique_users >= 500 AND conversion_rate >= 40, 75,
    unique_users >= 200 AND conversion_rate >= 30, 60,
    unique_users >= 100, 45,
    30
  )
| SORT engagement_score DESC, unique_users DESC
| KEEP feature_name, feature_category, unique_users, total_interactions, conversion_rate, avg_duration_ms, engagement_score
| LIMIT 20""",
            "query_type": "scripted",
            "pain_point": "Real-Time Feature Adoption Analysis & Funnel Optimization - track granular feature usage patterns and workflow conversion rates, reducing feedback loops from 4-6 weeks to 3-7 days",
            "complexity": "medium"
        })

        # Query 6: Webhook Delivery Reliability Monitor
        queries.append({
            "name": "Webhook Delivery Reliability Monitor",
            "description": "Monitors webhook delivery success rates, retry patterns, and latency to ensure reliable partner event notifications",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_webhook_reliability",
                "description": "Monitors webhook delivery reliability across partner integrations. Tracks success rates, retry patterns, and latency to ensure event notifications reach partners reliably.",
                "tags": ["webhooks", "partners", "reliability", "monitoring", "esql"]
            },
            "query": """FROM webhook_deliveries
| STATS 
    total_deliveries = COUNT(*),
    successful = SUM(CASE(success == true, 1, 0)),
    failed = SUM(CASE(success == false, 1, 0)),
    avg_retries = AVG(retry_count),
    avg_latency_ms = AVG(delivery_latency_ms),
    p95_latency = PERCENTILE(delivery_latency_ms, 95)
  BY partner_id, event_type
| LOOKUP JOIN api_partners ON partner_id
| EVAL success_rate = (successful / total_deliveries) * 100
| EVAL reliability_score = CASE(
    success_rate >= 99 AND avg_retries < 0.5, 95,
    success_rate >= 97 AND avg_retries < 1, 80,
    success_rate >= 95 AND avg_retries < 2, 65,
    success_rate >= 90, 50,
    30
  )
| WHERE success_rate < 98 OR avg_retries > 1
| SORT reliability_score ASC, success_rate ASC
| KEEP partner_id, partner_name, tier, event_type, total_deliveries, success_rate, avg_retries, avg_latency_ms, p95_latency, reliability_score
| LIMIT 30""",
            "query_type": "scripted",
            "pain_point": "API Partner Ecosystem Health Monitoring - ensure third-party integrations operate reliably",
            "complexity": "medium"
        })

        # Query 7: User Session Quality Metrics
        queries.append({
            "name": "User Session Quality Metrics",
            "description": "Analyzes user session quality through Core Web Vitals (LCP, FID), bounce rates, and engagement patterns across devices and browsers",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_session_quality",
                "description": "Analyzes user session quality through Core Web Vitals and engagement metrics. Correlates technical performance with user experience across devices to identify UX bottlenecks.",
                "tags": ["ux", "performance", "sessions", "analytics", "esql"]
            },
            "query": """FROM user_sessions
| STATS 
    total_sessions = COUNT(*),
    avg_duration_ms = AVG(session_duration_ms),
    avg_page_views = AVG(page_views),
    avg_lcp_ms = AVG(lcp_ms),
    avg_fid_ms = AVG(fid_ms),
    bounce_rate = (SUM(CASE(bounce == true, 1, 0)) / COUNT(*)) * 100
  BY device_type, browser
| EVAL quality_score = CASE(
    avg_lcp_ms < 2500 AND avg_fid_ms < 100 AND bounce_rate < 30, 90,
    avg_lcp_ms < 4000 AND avg_fid_ms < 300 AND bounce_rate < 50, 70,
    avg_lcp_ms < 6000 AND bounce_rate < 70, 50,
    30
  )
| EVAL session_health = CASE(
    quality_score >= 80, "excellent",
    quality_score >= 60, "good",
    quality_score >= 40, "needs_improvement",
    "poor"
  )
| SORT quality_score DESC
| KEEP device_type, browser, total_sessions, avg_duration_ms, avg_page_views, avg_lcp_ms, avg_fid_ms, bounce_rate, quality_score, session_health
| LIMIT 20""",
            "query_type": "scripted",
            "pain_point": "Disconnected user experience and technical performance - cannot correlate customer complaints with actual performance data",
            "complexity": "medium"
        })

        # Query 8: Regional Performance Comparison
        queries.append({
            "name": "Regional Performance Comparison",
            "description": "Compares API performance metrics across regions to identify geographic performance disparities and routing issues",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_regional_performance",
                "description": "Compares API performance across geographic regions. Identifies regional disparities in latency and error rates to optimize routing and infrastructure allocation.",
                "tags": ["performance", "regional", "api", "infrastructure", "esql"]
            },
            "query": """FROM api_requests
| STATS 
    request_count = COUNT(*),
    avg_latency = AVG(response_time_ms),
    p50_latency = PERCENTILE(response_time_ms, 50),
    p95_latency = PERCENTILE(response_time_ms, 95),
    p99_latency = PERCENTILE(response_time_ms, 99),
    error_rate = (SUM(CASE(http_status >= 500, 1, 0)) / COUNT(*)) * 100
  BY region
| INLINESTATS 
    global_avg = AVG(avg_latency),
    global_p95 = AVG(p95_latency)
| EVAL latency_vs_global = ((avg_latency - global_avg) / global_avg) * 100
| EVAL p95_vs_global = ((p95_latency - global_p95) / global_p95) * 100
| EVAL performance_grade = CASE(
    p95_latency < 500 AND error_rate < 1, "A",
    p95_latency < 750 AND error_rate < 2, "B",
    p95_latency < 1000 AND error_rate < 5, "C",
    "D"
  )
| SORT p95_latency DESC
| KEEP region, request_count, avg_latency, p50_latency, p95_latency, p99_latency, error_rate, latency_vs_global, p95_vs_global, performance_grade""",
            "query_type": "scripted",
            "pain_point": "Multi-Tenant Performance Monitoring & SLA Management - ensure fair resource allocation",
            "complexity": "medium"
        })

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries that accept user input"""
        queries = []

        # Query 1: A/B Experiment Performance Analysis (Parameterized)
        queries.append({
            "name": "A/B Experiment Performance Analysis",
            "description": "Analyzes A/B experiment performance by calculating conversion rates and uplift vs control baseline, provides go/no-go decisions based on statistical significance",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_ab_experiment_analysis",
                "description": "Analyzes A/B experiment results with statistical significance testing. Calculates conversion uplift and provides go/no-go decisions within 7 days to accelerate product iteration.",
                "tags": ["ab-testing", "experiments", "conversion", "analytics", "esql"]
            },
            "query": """FROM feature_usage_events
| WHERE experiment_variant IS NOT NULL
| WHERE feature_name == ?feature_name
| STATS 
    conversion_rate = (SUM(CASE(conversion_event == true, 1, 0)) / COUNT(*)) * 100,
    avg_interaction_ms = AVG(interaction_duration_ms),
    unique_users = COUNT_DISTINCT(user_id),
    total_interactions = COUNT(*)
  BY experiment_variant
| LOOKUP JOIN ab_experiments ON experiment_variant == experiment_id
| EVAL uplift_pct = ((conversion_rate - control_baseline) / control_baseline) * 100
| EVAL statistical_significance = CASE(
    unique_users >= 1000 AND ABS(uplift_pct) >= 5, "significant",
    unique_users >= 500 AND ABS(uplift_pct) >= 10, "significant",
    unique_users >= 100, "insufficient_sample",
    "too_early"
  )
| EVAL decision = CASE(
    statistical_significance == "significant" AND uplift_pct > 5, "ship_variant",
    statistical_significance == "significant" AND uplift_pct < -5, "kill_variant",
    statistical_significance == "insufficient_sample", "continue_test",
    "wait_for_data"
  )
| EVAL engagement_improvement_pct = ((avg_interaction_ms - 5000) / 5000) * 100
| SORT uplift_pct DESC
| KEEP experiment_variant, experiment_name, variant_name, conversion_rate, control_baseline, uplift_pct, unique_users, statistical_significance, decision, engagement_improvement_pct
| LIMIT 20""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "feature_name",
                    "type": "string",
                    "description": "Feature name to analyze (e.g., 'Smart Tagging', 'Bulk Upload', 'Collections')",
                    "required": True
                }
            ],
            "pain_point": "Slow feedback loops on product releases - 4-6 weeks to understand feature impact prevents rapid iteration",
            "complexity": "high"
        })

        # Query 2: Real-Time Feature Adoption Funnel Analysis (Parameterized)
        queries.append({
            "name": "Real-Time Feature Adoption Funnel Analysis",
            "description": "Provides multi-dimensional feature adoption analysis: adoption rates by account tier, feature stickiness (DAU/MAU ratio), and funnel conversion rates by industry vertical",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_feature_funnel",
                "description": "Analyzes feature adoption funnels across dimensions (tier, industry). Calculates stickiness metrics and conversion rates to optimize onboarding flows and reduce time-to-value.",
                "tags": ["features", "funnel", "adoption", "conversion", "esql"]
            },
            "query": """FROM feature_usage_events
| WHERE feature_name == ?target_feature
| LOOKUP JOIN tenants ON tenant_id
| FORK
  (
    STATS total_users = COUNT_DISTINCT(user_id), total_interactions = COUNT(*) BY account_tier
    | EVAL metric_type = "adoption_by_tier"
  )
  (
    STATS 
      dau = COUNT_DISTINCT(user_id),
      mau = COUNT_DISTINCT(user_id)
    | EVAL stickiness = (dau / mau) * 100
    | EVAL metric_type = "feature_stickiness"
  )
  (
    STATS 
      funnel_step1 = COUNT_DISTINCT(user_id),
      funnel_step2 = COUNT_DISTINCT(CASE(conversion_event == true, user_id, null))
    BY industry_vertical
    | EVAL conversion_rate = (funnel_step2 / funnel_step1) * 100
    | EVAL metric_type = "funnel_conversion_by_industry"
    | SORT conversion_rate DESC
  )""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "target_feature",
                    "type": "string",
                    "description": "Feature to analyze (e.g., 'Smart Tagging', 'Analytics Dashboard', 'Export Pipeline')",
                    "required": True
                }
            ],
            "pain_point": "Real-Time Feature Adoption Analysis & Funnel Optimization - track granular feature usage patterns and workflow conversion rates",
            "complexity": "high"
        })

        # Query 3: Tenant Health Score with Time Range
        queries.append({
            "name": "Tenant Health Score with Time Range",
            "description": "Calculates comprehensive tenant health scores based on usage, engagement, and performance metrics over a specified time window",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_tenant_health_score",
                "description": "Calculates comprehensive tenant health scores combining usage, engagement, and performance. Enables flexible time-window analysis for trend detection and health monitoring.",
                "tags": ["health-score", "tenants", "analytics", "churn", "esql"]
            },
            "query": """FROM feature_usage_events
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| STATS 
    unique_users = COUNT_DISTINCT(user_id),
    total_events = COUNT(*),
    avg_interaction_ms = AVG(interaction_duration_ms),
    conversion_count = SUM(CASE(conversion_event == true, 1, 0))
  BY tenant_id
| LOOKUP JOIN tenants ON tenant_id
| EVAL usage_score = CASE(
    unique_users >= 50, 90,
    unique_users >= 20, 70,
    unique_users >= 10, 50,
    30
  )
| EVAL engagement_score = CASE(
    total_events >= 2000, 90,
    total_events >= 1000, 70,
    total_events >= 500, 50,
    30
  )
| EVAL conversion_score = CASE(
    conversion_count >= 100, 90,
    conversion_count >= 50, 70,
    conversion_count >= 20, 50,
    30
  )
| EVAL health_score = (usage_score * 0.4) + (engagement_score * 0.3) + (conversion_score * 0.3)
| EVAL health_status = CASE(
    health_score >= 80, "healthy",
    health_score >= 60, "stable",
    health_score >= 40, "at_risk",
    "critical"
  )
| SORT health_score ASC
| KEEP tenant_id, tenant_name, account_tier, contract_arr, unique_users, total_events, conversion_count, health_score, health_status, customer_success_manager
| LIMIT 50""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "start_date",
                    "type": "date",
                    "description": "Start date for health score calculation",
                    "required": True
                },
                {
                    "name": "end_date",
                    "type": "date",
                    "description": "End date for health score calculation",
                    "required": True
                }
            ],
            "pain_point": "No early warning system for customer health - at-risk accounts identified only 30-60 days before renewal",
            "complexity": "high"
        })

        # Query 4: API Endpoint Performance Analysis
        queries.append({
            "name": "API Endpoint Performance Analysis",
            "description": "Analyzes performance metrics for specific API endpoints with customizable time window and region filtering",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_api_endpoint_performance",
                "description": "Analyzes API endpoint performance with flexible filtering. Tracks latency percentiles, error rates, and throughput to identify performance bottlenecks and optimize resource allocation.",
                "tags": ["api", "performance", "endpoints", "monitoring", "esql"]
            },
            "query": """FROM api_requests
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE endpoint == ?endpoint_path
| WHERE region == ?region
| STATS 
    request_count = COUNT(*),
    avg_latency = AVG(response_time_ms),
    p50_latency = PERCENTILE(response_time_ms, 50),
    p95_latency = PERCENTILE(response_time_ms, 95),
    p99_latency = PERCENTILE(response_time_ms, 99),
    error_count = SUM(CASE(http_status >= 500, 1, 0)),
    success_count = SUM(CASE(http_status >= 200 AND http_status < 300, 1, 0))
  BY endpoint, region
| EVAL error_rate = (error_count / request_count) * 100
| EVAL success_rate = (success_count / request_count) * 100
| EVAL performance_grade = CASE(
    p95_latency < 500 AND error_rate < 1, "excellent",
    p95_latency < 1000 AND error_rate < 2, "good",
    p95_latency < 2000 AND error_rate < 5, "acceptable",
    "poor"
  )
| KEEP endpoint, region, request_count, avg_latency, p50_latency, p95_latency, p99_latency, error_rate, success_rate, performance_grade""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "start_date",
                    "type": "date",
                    "description": "Start date for analysis window",
                    "required": True
                },
                {
                    "name": "end_date",
                    "type": "date",
                    "description": "End date for analysis window",
                    "required": True
                },
                {
                    "name": "endpoint_path",
                    "type": "string",
                    "description": "API endpoint path (e.g., '/api/v2/assets', '/api/v2/search')",
                    "required": True
                },
                {
                    "name": "region",
                    "type": "string",
                    "description": "AWS region (e.g., 'us-west-2', 'eu-west-1', 'us-east-1', 'ap-southeast-1')",
                    "required": True
                }
            ],
            "pain_point": "Multi-Tenant Performance Monitoring & SLA Management - ensure fair resource allocation",
            "complexity": "medium"
        })

        # Query 5: Partner Integration Performance by Tier
        queries.append({
            "name": "Partner Integration Performance by Tier",
            "description": "Analyzes partner integration performance filtered by partner tier with time-based comparison",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_partner_tier_performance",
                "description": "Analyzes partner integration performance by tier (Platinum, Gold, Silver, Bronze). Compares success rates and volumes to ensure tier-appropriate service levels and identify at-risk partnerships.",
                "tags": ["partners", "integrations", "tier", "analytics", "esql"]
            },
            "query": """FROM api_requests
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE partner_id IS NOT NULL
| EVAL success = CASE(http_status >= 200 AND http_status < 300, 1, 0)
| STATS 
    request_count = COUNT(*),
    success_rate = (SUM(success) / COUNT(*)) * 100,
    avg_latency = AVG(response_time_ms),
    p95_latency = PERCENTILE(response_time_ms, 95)
  BY partner_id
| LOOKUP JOIN api_partners ON partner_id
| WHERE tier == ?partner_tier
| EVAL tier_performance = CASE(
    success_rate >= 99 AND p95_latency < 1000, "exceeds_expectations",
    success_rate >= 97 AND p95_latency < 2000, "meets_expectations",
    success_rate >= 95, "below_expectations",
    "critical"
  )
| SORT success_rate ASC
| KEEP partner_id, partner_name, tier, integration_type, request_count, success_rate, avg_latency, p95_latency, tier_performance, partnership_health_score
| LIMIT 30""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "start_date",
                    "type": "date",
                    "description": "Start date for analysis",
                    "required": True
                },
                {
                    "name": "end_date",
                    "type": "date",
                    "description": "End date for analysis",
                    "required": True
                },
                {
                    "name": "partner_tier",
                    "type": "string",
                    "description": "Partner tier to analyze ('Platinum', 'Gold', 'Silver', 'Bronze')",
                    "required": True
                }
            ],
            "pain_point": "API Partner Ecosystem Health Monitoring - ensure third-party integrations operate reliably",
            "complexity": "medium"
        })

        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using COMPLETION command
        
        Semantic fields from strategy:
        - api_requests.error_message (text)
        - ab_experiments.experiment_hypothesis (text)
        """
        queries = []

        # RAG Query 1: API Error Analysis and Troubleshooting
        queries.append({
            "name": "API Error Analysis and Troubleshooting",
            "description": "Semantic search across API error messages to find similar issues and generate troubleshooting recommendations using LLM",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_api_error_troubleshooting",
                "description": "Searches API error messages semantically to find similar issues. Uses LLM to generate troubleshooting recommendations and root cause analysis for faster incident resolution.",
                "tags": ["rag", "errors", "troubleshooting", "api", "esql"]
            },
            "query": """FROM api_requests METADATA _id
| WHERE MATCH(error_message, ?user_question)
| WHERE http_status >= 400
| STATS 
    error_count = COUNT(*),
    affected_tenants = COUNT_DISTINCT(tenant_id),
    affected_partners = COUNT_DISTINCT(partner_id),
    sample_error = VALUES(error_message)
  BY error_message, endpoint, region
| SORT error_count DESC
| LIMIT 5
| EVAL context = CONCAT(
    "Error: ", error_message, 
    " | Endpoint: ", endpoint,
    " | Region: ", region,
    " | Occurrences: ", TO_STRING(error_count),
    " | Affected tenants: ", TO_STRING(affected_tenants)
  )
| EVAL prompt = CONCAT(
    "Based on this API error pattern, provide troubleshooting steps and potential root causes: ",
    context,
    " User question: ",
    ?user_question
  )
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP error_message, endpoint, region, error_count, affected_tenants, affected_partners, answer""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "string",
                    "description": "Question about API errors (e.g., 'Why are we seeing rate limit errors?', 'What causes database timeouts?')",
                    "required": True
                }
            ],
            "pain_point": "Fragmented product usage visibility across disparate data sources requiring 2-3 days of manual data extraction",
            "complexity": "high"
        })

        # RAG Query 2: Experiment Hypothesis Analysis
        queries.append({
            "name": "Experiment Hypothesis Analysis",
            "description": "Semantic search across A/B experiment hypotheses to find related experiments and generate insights about experiment strategy",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_experiment_insights",
                "description": "Searches experiment hypotheses semantically to find related tests. Uses LLM to analyze experiment strategy, identify patterns, and recommend future experiments based on historical results.",
                "tags": ["rag", "experiments", "ab-testing", "insights", "esql"]
            },
            "query": """FROM ab_experiments METADATA _id
| WHERE MATCH(experiment_hypothesis, ?user_question)
| KEEP experiment_id, experiment_name, variant_name, feature_name, target_metric, control_baseline, experiment_hypothesis, start_date
| SORT start_date DESC
| LIMIT 5
| EVAL context = CONCAT(
    "Experiment: ", experiment_name,
    " | Feature: ", feature_name,
    " | Hypothesis: ", experiment_hypothesis,
    " | Target metric: ", target_metric,
    " | Baseline: ", TO_STRING(control_baseline)
  )
| EVAL prompt = CONCAT(
    "Analyze these experiment hypotheses and provide strategic insights: ",
    context,
    " User question: ",
    ?user_question
  )
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP experiment_name, feature_name, target_metric, experiment_hypothesis, control_baseline, answer""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "string",
                    "description": "Question about experiments (e.g., 'What experiments improved conversion?', 'Which features have been tested for engagement?')",
                    "required": True
                }
            ],
            "pain_point": "Slow feedback loops on product releases - 4-6 weeks to understand feature impact prevents rapid iteration",
            "complexity": "high"
        })

        # RAG Query 3: Error Pattern Recognition and Prevention
        queries.append({
            "name": "Error Pattern Recognition and Prevention",
            "description": "Combines error message semantic search with tenant context to identify systemic issues and generate prevention strategies",
            "tool_metadata": {
                "tool_id": "adobe_inc.brand_conc_error_prevention",
                "description": "Identifies error patterns across tenants using semantic search. Generates prevention strategies and proactive monitoring recommendations to reduce incident frequency.",
                "tags": ["rag", "errors", "prevention", "monitoring", "esql"]
            },
            "query": """FROM api_requests METADATA _id
| WHERE MATCH(error_message, ?user_question)
| WHERE http_status >= 500
| LOOKUP JOIN tenants ON tenant_id
| STATS 
    total_errors = COUNT(*),
    unique_tenants = COUNT_DISTINCT(tenant_id),
    enterprise_affected = SUM(CASE(account_tier == "Enterprise", 1, 0)),
    avg_tenant_arr = AVG(contract_arr),
    error_sample = VALUES(error_message)
  BY error_message, http_status
| SORT total_errors DESC
| LIMIT 3
| EVAL revenue_at_risk = avg_tenant_arr * unique_tenants
| EVAL context = CONCAT(
    "Error pattern: ", error_message,
    " | HTTP status: ", TO_STRING(http_status),
    " | Total occurrences: ", TO_STRING(total_errors),
    " | Affected tenants: ", TO_STRING(unique_tenants),
    " | Enterprise customers impacted: ", TO_STRING(enterprise_affected),
    " | Revenue at risk: $", TO_STRING(revenue_at_risk)
  )
| EVAL prompt = CONCAT(
    "Analyze this error pattern and suggest prevention strategies: ",
    context,
    " User question: ",
    ?user_question
  )
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP error_message, http_status, total_errors, unique_tenants, enterprise_affected, revenue_at_risk, answer""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "string",
                    "description": "Question about error prevention (e.g., 'How can we prevent database timeouts?', 'What monitoring should we add?')",
                    "required": True
                }
            ],
            "pain_point": "Disconnected user experience and technical performance - cannot correlate customer complaints with actual performance data",
            "complexity": "high"
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum impact"""
        return [
            # Start with business-critical pain points
            "Noisy Neighbor Detection with Tenant Context",
            "At-Risk Customer Early Warning System",
            "Multi-Tenant SLA Compliance Dashboard",
            
            # Partner ecosystem health
            "API Partner Integration Health Monitoring",
            "Webhook Delivery Reliability Monitor",
            "Partner Integration Performance by Tier",
            
            # Product iteration and experimentation
            "A/B Experiment Performance Analysis",
            "Feature Adoption Velocity Analysis",
            "Real-Time Feature Adoption Funnel Analysis",
            
            # Performance and UX correlation
            "User Session Quality Metrics",
            "Regional Performance Comparison",
            "API Endpoint Performance Analysis",
            
            # Tenant health and analytics
            "Tenant Health Score with Time Range",
            
            # RAG-powered insights
            "API Error Analysis and Troubleshooting",
            "Experiment Hypothesis Analysis",
            "Error Pattern Recognition and Prevention"
        ]
