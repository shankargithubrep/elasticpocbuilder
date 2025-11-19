
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class ItaúUnibancoQueryGenerator(QueryGeneratorModule):
    """Query generator for Itaú Unibanco - Customer Experience
    
    Implements Real User Monitoring (RUM) analytics for banking applications,
    focusing on frontend-to-backend performance correlation, Core Web Vitals
    monitoring, and user journey analysis.
    """

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate ALL ES|QL queries from pre-planned strategy"""
        queries = []

        # ============================================================================
        # SCRIPTED QUERIES - Simple queries without parameters
        # ============================================================================

        # Query 1: Frontend-to-Backend Performance Correlation
        queries.append({
            "name": "Frontend-to-Backend Performance Correlation via Distributed Tracing",
            "description": """Correlates slow page loads with backend service performance using trace_id 
            to identify whether bottlenecks originate from frontend rendering, backend processing, or 
            database queries. Shows percentage contribution of each layer. This addresses the critical 
            pain point of inability to connect frontend navigation with backend requests.""",
            "query": """FROM rum_page_loads
| WHERE @timestamp > NOW() - 24 hours AND total_page_load_ms > 3000
| LOOKUP JOIN backend_services ON trace_id
| LOOKUP JOIN application_catalog ON application_id
| EVAL frontend_time_ms = total_page_load_ms - duration_ms
| EVAL backend_contribution_pct = (TO_DOUBLE(duration_ms) / total_page_load_ms) * 100
| WHERE backend_contribution_pct > 30
| STATS 
    avg_total_load = AVG(total_page_load_ms),
    avg_backend_time = AVG(duration_ms),
    avg_frontend_time = AVG(frontend_time_ms),
    avg_db_time = AVG(database_query_time_ms),
    slow_page_count = COUNT(*)
  BY application_name, service_name
| SORT avg_total_load DESC
| LIMIT 20""",
            "query_type": "scripted",
            "use_case": "Frontend-to-Backend Performance Correlation",
            "complexity": "high"
        })

        # Query 2: Navigation Timing Phase Breakdown
        queries.append({
            "name": "Navigation Timing Phase Breakdown for Performance Diagnosis",
            "description": """Breaks down page load into distinct timing phases (DNS, TCP, TTFB, response 
            download, DOM processing) and compares each phase against application-specific averages to 
            identify which phase is causing performance degradation. Highlights outliers by device and 
            connection type.""",
            "query": """FROM rum_page_loads
| WHERE @timestamp > NOW() - 7 days
| LOOKUP JOIN application_catalog ON application_id
| EVAL network_time = dns_time_ms + tcp_time_ms + ttfb_ms + response_time_ms
| EVAL processing_time = dom_processing_ms + load_event_ms
| EVAL network_pct = (TO_DOUBLE(network_time) / total_page_load_ms) * 100
| EVAL processing_pct = (TO_DOUBLE(processing_time) / total_page_load_ms) * 100
| STATS 
    avg_dns = AVG(dns_time_ms),
    avg_tcp = AVG(tcp_time_ms),
    avg_ttfb = AVG(ttfb_ms),
    avg_response = AVG(response_time_ms),
    avg_dom = AVG(dom_processing_ms),
    page_count = COUNT(*)
  BY application_name, device_type
| WHERE page_count > 10
| SORT avg_ttfb DESC, avg_dom DESC
| LIMIT 50""",
            "query_type": "scripted",
            "use_case": "Navigation Timing Breakdown Analysis",
            "complexity": "high"
        })

        # Query 3: Core Web Vitals Monitoring by Application Type
        queries.append({
            "name": "Core Web Vitals Monitoring by Application Type & Business Context",
            "description": """Measures Core Web Vitals compliance against application-specific performance 
            targets (not generic thresholds). Shows P75 metrics and compliance percentage by application 
            type, business unit, and device. Identifies which critical applications are failing to meet 
            their unique SLA targets.""",
            "query": """FROM rum_page_loads
| WHERE @timestamp > NOW() - 30 days
| LOOKUP JOIN application_catalog ON application_id
| EVAL lcp_meets_target = CASE(lcp_ms <= target_lcp_ms, 1, 0)
| EVAL inp_meets_target = CASE(inp_ms <= target_inp_ms, 1, 0)
| EVAL cls_meets_target = CASE(cls_score <= target_cls, 1, 0)
| EVAL all_targets_met = CASE(lcp_meets_target == 1 AND inp_meets_target == 1 AND cls_meets_target == 1, 1, 0)
| STATS
    p75_lcp = PERCENTILE(lcp_ms, 75),
    p75_inp = PERCENTILE(inp_ms, 75),
    p75_cls = PERCENTILE(cls_score, 75),
    lcp_compliance_pct = AVG(lcp_meets_target) * 100,
    inp_compliance_pct = AVG(inp_meets_target) * 100,
    cls_compliance_pct = AVG(cls_meets_target) * 100,
    overall_compliance_pct = AVG(all_targets_met) * 100,
    page_load_count = COUNT(*)
  BY application_name, application_type, business_unit, criticality, device_type
| WHERE page_load_count > 50
| SORT overall_compliance_pct ASC, page_load_count DESC
| LIMIT 50""",
            "query_type": "scripted",
            "use_case": "Core Web Vitals Monitoring & Alerting",
            "complexity": "high"
        })

        # Query 4: Resource Loading Optimization
        queries.append({
            "name": "Resource Loading Optimization with CDN Performance Analysis",
            "description": """Analyzes resource loading performance by type (scripts, stylesheets, images, 
            fonts) and CDN provider. Identifies optimization opportunities through high cache miss rates, 
            slow P95 load times, and excessive transfer sizes. Helps prioritize CDN configuration and 
            asset optimization efforts.""",
            "query": """FROM rum_resource_timing
| WHERE @timestamp > NOW() - 7 days AND http_status >= 200 AND http_status < 400
| LOOKUP JOIN application_catalog ON application_id
| EVAL cache_miss = CASE(is_cached == false, 1, 0)
| EVAL slow_resource = CASE(duration_ms > 1000, 1, 0)
| EVAL size_mb = TO_DOUBLE(transfer_size_bytes) / 1048576
| STATS
    total_resources = COUNT(*),
    avg_duration_ms = AVG(duration_ms),
    p95_duration_ms = PERCENTILE(duration_ms, 95),
    avg_ttfb_ms = AVG(ttfb_ms),
    avg_download_ms = AVG(download_time_ms),
    total_transfer_mb = SUM(size_mb),
    cache_miss_rate_pct = AVG(cache_miss) * 100,
    slow_resource_pct = AVG(slow_resource) * 100
  BY application_name, resource_type, cdn_provider
| WHERE total_resources > 100
| SORT p95_duration_ms DESC, cache_miss_rate_pct DESC
| LIMIT 30""",
            "query_type": "scripted",
            "use_case": "Resource Loading Optimization",
            "complexity": "medium"
        })

        # Query 5: Long Task & JavaScript Error Correlation
        queries.append({
            "name": "Long Task & JavaScript Error Correlation Analysis",
            "description": """Identifies patterns between long-running JavaScript tasks and user-reported 
            errors. Analyzes Total Blocking Time (TBT) and correlates with error occurrences to pinpoint 
            problematic JavaScript execution that impacts user experience.""",
            "query": """FROM rum_page_loads
| WHERE @timestamp > NOW() - 14 days AND long_task_count > 3
| LOOKUP JOIN application_catalog ON application_id
| EVAL severe_blocking = CASE(tbt_ms > 600, 1, 0)
| EVAL has_errors = CASE(error_count > 0, 1, 0)
| STATS
    avg_long_tasks = AVG(long_task_count),
    avg_tbt_ms = AVG(tbt_ms),
    avg_inp_ms = AVG(inp_ms),
    severe_blocking_pct = AVG(severe_blocking) * 100,
    error_rate_pct = AVG(has_errors) * 100,
    avg_error_count = AVG(error_count),
    affected_pages = COUNT_DISTINCT(page_name),
    total_loads = COUNT(*)
  BY application_name, device_type, browser
| WHERE total_loads > 20
| SORT avg_tbt_ms DESC, error_rate_pct DESC
| LIMIT 25""",
            "query_type": "scripted",
            "use_case": "Long Task & JavaScript Error Correlation",
            "complexity": "medium"
        })

        # Query 6: Device & Network Performance Comparison
        queries.append({
            "name": "Device & Network Performance Comparison",
            "description": """Compares Core Web Vitals performance across different device types and 
            network connection types. Helps identify whether performance issues are device-specific 
            or network-related, enabling targeted optimization strategies.""",
            "query": """FROM rum_page_loads
| WHERE @timestamp > NOW() - 14 days
| STATS
    p75_lcp = PERCENTILE(lcp_ms, 75),
    p75_inp = PERCENTILE(inp_ms, 75),
    p75_cls = PERCENTILE(cls_score, 75),
    p75_ttfb = PERCENTILE(ttfb_ms, 75),
    avg_total_load = AVG(total_page_load_ms),
    page_load_count = COUNT(*)
  BY device_type, connection_type, region
| WHERE page_load_count > 50
| SORT p75_lcp DESC, p75_inp DESC
| LIMIT 40""",
            "query_type": "scripted",
            "use_case": "Core Web Vitals Monitoring & Alerting",
            "complexity": "medium"
        })

        # Query 7: Page-Level Performance Hotspots
        queries.append({
            "name": "Page-Level Performance Hotspots",
            "description": """Identifies specific pages with consistently poor performance across all 
            Core Web Vitals metrics. Helps prioritize which pages need immediate optimization attention 
            based on traffic volume and performance degradation.""",
            "query": """FROM rum_page_loads
| WHERE @timestamp > NOW() - 7 days
| STATS
    p75_lcp = PERCENTILE(lcp_ms, 75),
    p75_inp = PERCENTILE(inp_ms, 75),
    p95_cls = PERCENTILE(cls_score, 95),
    avg_error_count = AVG(error_count),
    avg_failed_resources = AVG(failed_resource_count),
    page_view_count = COUNT(*)
  BY page_name, page_url
| WHERE page_view_count > 100
| EVAL performance_score = (p75_lcp / 2500) + (p75_inp / 200) + (p95_cls / 0.1)
| SORT performance_score DESC, page_view_count DESC
| LIMIT 30""",
            "query_type": "scripted",
            "use_case": "Navigation Timing Breakdown Analysis",
            "complexity": "medium"
        })

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries that accept user input"""
        queries = []

        # Query 1: Individual User Session Timeline
        queries.append({
            "name": "Individual User Session Timeline with Interaction & Error Correlation",
            "description": """Provides a chronological timeline of all page loads and user interactions 
            for a specific session. Enriched with application context, workflow progress, and error 
            details. Essential for debugging individual user issues and understanding session behavior.""",
            "query": """FROM rum_page_loads
| WHERE session_id == ?session_id
| LOOKUP JOIN user_sessions ON session_id
| LOOKUP JOIN application_catalog ON application_id
| EVAL event_type = "page_load"
| EVAL event_detail = CONCAT(page_name, " (LCP: ", TO_STRING(lcp_ms), "ms, Errors: ", TO_STRING(error_count), ")")
| KEEP @timestamp, event_type, event_detail, application_name, workflow_name, workflow_completed, lcp_ms, cls_score, error_count, long_task_count
| SORT @timestamp ASC
| LIMIT 100""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "session_id",
                    "type": "string",
                    "description": "Unique session identifier to analyze",
                    "required": True
                }
            ],
            "use_case": "Individual User Session Analysis",
            "complexity": "medium"
        })

        # Query 2: Conversion Funnel Drop-off Analysis
        queries.append({
            "name": "Conversion Funnel Drop-off Analysis with Workflow Tracking",
            "description": """Tracks user progression through banking workflows (PIX transfer, loan 
            application, card activation) step-by-step. Identifies drop-off points by calculating 
            sessions that reach each step, success rates, and error rates. Segments by customer type 
            and device to uncover friction points in critical conversion funnels.""",
            "query": """FROM rum_user_interactions
| WHERE @timestamp > NOW() - 30 days AND workflow_name == ?workflow_name
| LOOKUP JOIN user_sessions ON session_id
| LOOKUP JOIN application_catalog ON application_id
| EVAL step_completed = CASE(resulted_in_error == false, 1, 0)
| STATS
    sessions_reached = COUNT_DISTINCT(session_id),
    interactions = COUNT(*),
    success_rate_pct = AVG(step_completed) * 100,
    avg_interactions_per_session = TO_DOUBLE(COUNT(*)) / COUNT_DISTINCT(session_id),
    error_rate_pct = AVG(CASE(resulted_in_error == true, 1, 0)) * 100
  BY workflow_step, customer_segment, device_type
| SORT workflow_step ASC
| LIMIT 100""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "workflow_name",
                    "type": "string",
                    "description": "Workflow to analyze (e.g., 'PIX Transfer', 'Loan Application', 'Card Activation')",
                    "required": True,
                    "options": ["PIX Transfer", "Loan Application", "Card Activation", "Login Flow", "Investment Purchase", "Account Opening", "Profile Update", "Statement Download", "Bill Payment", "Support Request"]
                }
            ],
            "use_case": "Building Aggregated Conversion Funnels",
            "complexity": "high"
        })

        # Query 3: Application Performance Deep Dive
        queries.append({
            "name": "Application Performance Deep Dive with Target Compliance",
            "description": """Analyzes comprehensive performance metrics for a specific application, 
            comparing actual performance against application-specific targets. Shows breakdown by device, 
            region, and connection type to identify specific user segments experiencing issues.""",
            "query": """FROM rum_page_loads
| WHERE @timestamp > NOW() - 7 days AND application_id == ?application_id
| LOOKUP JOIN application_catalog ON application_id
| EVAL lcp_meets_target = CASE(lcp_ms <= target_lcp_ms, 1, 0)
| EVAL inp_meets_target = CASE(inp_ms <= target_inp_ms, 1, 0)
| EVAL cls_meets_target = CASE(cls_score <= target_cls, 1, 0)
| STATS
    p50_lcp = PERCENTILE(lcp_ms, 50),
    p75_lcp = PERCENTILE(lcp_ms, 75),
    p95_lcp = PERCENTILE(lcp_ms, 95),
    p75_inp = PERCENTILE(inp_ms, 75),
    p75_cls = PERCENTILE(cls_score, 75),
    lcp_compliance = AVG(lcp_meets_target) * 100,
    inp_compliance = AVG(inp_meets_target) * 100,
    cls_compliance = AVG(cls_meets_target) * 100,
    avg_error_count = AVG(error_count),
    page_loads = COUNT(*)
  BY application_name, device_type, region, connection_type
| WHERE page_loads > 10
| SORT lcp_compliance ASC, page_loads DESC
| LIMIT 50""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "application_id",
                    "type": "string",
                    "description": "Application ID to analyze (e.g., 'app_0001', 'app_0029')",
                    "required": True
                }
            ],
            "use_case": "Core Web Vitals Monitoring & Alerting",
            "complexity": "high"
        })

        # Query 4: Time Range Performance Comparison
        queries.append({
            "name": "Time Range Performance Comparison",
            "description": """Compares Core Web Vitals performance between two time periods to detect 
            performance regressions or improvements. Useful for validating the impact of deployments, 
            infrastructure changes, or optimization efforts.""",
            "query": """FROM rum_page_loads
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| LOOKUP JOIN application_catalog ON application_id
| STATS
    p75_lcp = PERCENTILE(lcp_ms, 75),
    p75_inp = PERCENTILE(inp_ms, 75),
    p75_cls = PERCENTILE(cls_score, 75),
    avg_total_load = AVG(total_page_load_ms),
    avg_ttfb = AVG(ttfb_ms),
    avg_dom_processing = AVG(dom_processing_ms),
    page_load_count = COUNT(*)
  BY application_name, business_unit
| WHERE page_load_count > 20
| SORT p75_lcp DESC
| LIMIT 30""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "start_date",
                    "type": "datetime",
                    "description": "Start date for analysis period",
                    "required": True
                },
                {
                    "name": "end_date",
                    "type": "datetime",
                    "description": "End date for analysis period",
                    "required": True
                }
            ],
            "use_case": "Core Web Vitals Monitoring & Alerting",
            "complexity": "medium"
        })

        # Query 5: User Interaction Performance Analysis
        queries.append({
            "name": "User Interaction Performance Analysis by Element",
            "description": """Analyzes performance of specific user interactions (clicks, form submissions) 
            to identify slow or error-prone UI elements. Helps prioritize frontend optimization efforts 
            based on actual user interaction patterns.""",
            "query": """FROM rum_user_interactions
| WHERE @timestamp > NOW() - 14 days AND interaction_type == ?interaction_type
| LOOKUP JOIN application_catalog ON application_id
| EVAL is_slow = CASE(interaction_duration_ms > 500, 1, 0)
| STATS
    interaction_count = COUNT(*),
    avg_duration = AVG(interaction_duration_ms),
    p95_duration = PERCENTILE(interaction_duration_ms, 95),
    error_rate_pct = AVG(CASE(resulted_in_error == true, 1, 0)) * 100,
    slow_interaction_pct = AVG(is_slow) * 100,
    unique_sessions = COUNT_DISTINCT(session_id)
  BY application_name, element_text, workflow_name, device_type
| WHERE interaction_count > 10
| SORT p95_duration DESC, error_rate_pct DESC
| LIMIT 40""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "interaction_type",
                    "type": "string",
                    "description": "Type of interaction to analyze",
                    "required": True,
                    "options": ["click", "submit", "focus", "blur", "input", "scroll", "hover"]
                }
            ],
            "use_case": "Individual User Session Analysis",
            "complexity": "medium"
        })

        # Query 6: Regional Performance Analysis
        queries.append({
            "name": "Regional Performance Analysis with Network Breakdown",
            "description": """Compares performance across different Brazilian regions, segmented by 
            connection type. Identifies regional infrastructure issues or CDN performance problems 
            that may require targeted optimization or infrastructure investment.""",
            "query": """FROM rum_page_loads
| WHERE @timestamp > NOW() - 30 days AND region == ?region
| LOOKUP JOIN application_catalog ON application_id
| STATS
    p75_lcp = PERCENTILE(lcp_ms, 75),
    p75_inp = PERCENTILE(inp_ms, 75),
    p75_ttfb = PERCENTILE(ttfb_ms, 75),
    avg_dns = AVG(dns_time_ms),
    avg_tcp = AVG(tcp_time_ms),
    avg_total_load = AVG(total_page_load_ms),
    page_loads = COUNT(*)
  BY application_name, connection_type, device_type
| WHERE page_loads > 50
| SORT p75_lcp DESC
| LIMIT 40""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "region",
                    "type": "string",
                    "description": "Brazilian region to analyze",
                    "required": True,
                    "options": ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Brasília", "Salvador", "Fortaleza", "Recife", "Porto Alegre", "Curitiba", "Manaus"]
                }
            ],
            "use_case": "Core Web Vitals Monitoring & Alerting",
            "complexity": "medium"
        })

        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using COMPLETION command
        
        RAG queries target semantic_text fields from application_catalog:
        - application_description: Banking application descriptions with focus areas
        - performance_sla: Performance SLA definitions and targets
        """
        queries = []

        # Query 1: Application Discovery by Description
        queries.append({
            "name": "Find Similar Applications by Description",
            "description": """Uses semantic search to find banking applications with similar 
            characteristics based on natural language descriptions. Helps identify applications 
            with comparable architecture, user experience requirements, or business focus for 
            benchmarking and best practice sharing.""",
            "query": """FROM application_catalog METADATA _id
| WHERE MATCH(application_description, ?user_question, {"fuzziness": "AUTO"})
| KEEP application_id, application_name, application_type, business_unit, criticality, application_description, performance_sla, target_lcp_ms, target_inp_ms, target_cls
| SORT _score DESC
| LIMIT 10
| EVAL prompt = CONCAT("Based on these banking applications and their descriptions, answer this question: ", ?user_question, "\\n\\nApplications found:\\n", application_name, " (", application_type, ") - ", application_description)
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "string",
                    "description": "Natural language question about application characteristics (e.g., 'applications focused on security', 'digital banking with good user experience')",
                    "required": True
                }
            ],
            "use_case": "Semantic Search for Similar Performance Issues",
            "complexity": "high"
        })

        # Query 2: Performance SLA Analysis
        queries.append({
            "name": "Performance SLA Guidance and Recommendations",
            "description": """Searches performance SLA definitions to provide guidance on appropriate 
            performance targets for different application types and business contexts. Uses LLM to 
            generate recommendations based on similar applications' SLA definitions.""",
            "query": """FROM application_catalog METADATA _id
| WHERE MATCH(performance_sla, ?user_question, {"fuzziness": "AUTO"})
| KEEP application_id, application_name, application_type, business_unit, criticality, performance_sla, target_lcp_ms, target_inp_ms, target_cls, primary_user_segment
| SORT _score DESC
| LIMIT 8
| EVAL prompt = CONCAT("Based on these performance SLAs from similar banking applications, provide guidance for this question: ", ?user_question, "\\n\\nSLA Examples:\\n", application_name, " (", criticality, " criticality, ", primary_user_segment, " segment): ", performance_sla, " - Targets: LCP=", TO_STRING(target_lcp_ms), "ms, INP=", TO_STRING(target_inp_ms), "ms, CLS=", TO_STRING(target_cls))
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "string",
                    "description": "Question about performance SLA targets or availability requirements (e.g., 'what should be the LCP target for a critical mobile banking app?', 'typical availability SLA for investment platforms')",
                    "required": True
                }
            ],
            "use_case": "Difficulty in defining 'satisfactory performance'",
            "complexity": "high"
        })

        # Query 3: Application Architecture Patterns
        queries.append({
            "name": "Discover Application Architecture Patterns",
            "description": """Combines semantic search across both application descriptions and performance 
            SLAs to identify architectural patterns and performance characteristics. Provides LLM-powered 
            insights about common patterns, anti-patterns, and optimization strategies.""",
            "query": """FROM application_catalog METADATA _id
| WHERE MATCH(application_description, ?user_question, {"fuzziness": "AUTO"}) 
    OR MATCH(performance_sla, ?user_question, {"fuzziness": "AUTO"})
| KEEP application_id, application_name, application_type, business_unit, criticality, application_description, performance_sla, workflow_names, primary_user_segment
| SORT _score DESC
| LIMIT 12
| EVAL prompt = CONCAT("Analyze these banking applications to answer: ", ?user_question, "\\n\\nApplication: ", application_name, "\\nType: ", application_type, "\\nBusiness Unit: ", business_unit, "\\nCriticality: ", criticality, "\\nUser Segment: ", primary_user_segment, "\\nDescription: ", application_description, "\\nSLA: ", performance_sla, "\\nWorkflows: ", workflow_names)
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "string",
                    "description": "Question about application patterns, architecture, or optimization strategies (e.g., 'what are common patterns in high-performance customer transaction apps?', 'how do critical applications handle accessibility?')",
                    "required": True
                }
            ],
            "use_case": "Semantic Search for Similar Performance Issues",
            "complexity": "high"
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum impact
        
        Narrative flow:
        1. Start with high-impact distributed tracing correlation
        2. Drill into navigation timing details
        3. Show Core Web Vitals compliance monitoring
        4. Demonstrate resource optimization analysis
        5. Correlate long tasks with errors
        6. Compare device/network performance
        7. Identify page-level hotspots
        8. Enable session-level debugging (parameterized)
        9. Analyze conversion funnels (parameterized)
        10. Deep dive into specific applications (parameterized)
        11. Support time-based comparisons (parameterized)
        12. Analyze user interaction performance (parameterized)
        13. Regional performance analysis (parameterized)
        14. Semantic application discovery (RAG)
        15. Performance SLA guidance (RAG)
        16. Architecture pattern discovery (RAG)
        """
        return [
            # Core scripted queries - demonstrate key capabilities
            "Frontend-to-Backend Performance Correlation via Distributed Tracing",
            "Navigation Timing Phase Breakdown for Performance Diagnosis",
            "Core Web Vitals Monitoring by Application Type & Business Context",
            "Resource Loading Optimization with CDN Performance Analysis",
            "Long Task & JavaScript Error Correlation Analysis",
            "Device & Network Performance Comparison",
            "Page-Level Performance Hotspots",
            
            # Parameterized queries - enable interactive analysis
            "Individual User Session Timeline with Interaction & Error Correlation",
            "Conversion Funnel Drop-off Analysis with Workflow Tracking",
            "Application Performance Deep Dive with Target Compliance",
            "Time Range Performance Comparison",
            "User Interaction Performance Analysis by Element",
            "Regional Performance Analysis with Network Breakdown",
            
            # RAG queries - semantic search and LLM-powered insights
            "Find Similar Applications by Description",
            "Performance SLA Guidance and Recommendations",
            "Discover Application Architecture Patterns"
        ]
