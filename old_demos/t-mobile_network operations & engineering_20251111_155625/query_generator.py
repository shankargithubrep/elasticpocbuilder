
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class TMobileQueryGenerator(QueryGeneratorModule):
    """Query generator for T-Mobile - Network Operations & Engineering"""

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate ALL ES|QL queries from pre-planned strategy
        
        CRITICAL: Categorize each query with query_type field:
        - "scripted": Basic queries that don't take user parameters
        - "parameterized": Queries that can be customized with user input
        - "rag": RAG queries using MATCH -> RERANK -> COMPLETION pipeline
        """
        queries = []

        # SCRIPTED QUERY 1: Real-Time Cell Site Degradation Detection
        queries.append({
            "name": "Real-Time Cell Site Degradation Detection with Multi-Domain Enrichment",
            "description": """Proactively identifies cell sites experiencing performance degradation in real-time using ML anomaly scores combined with KPI thresholds.
            Enriches with site metadata and compares performance against regional baselines to prioritize NOC response, reducing MTTD from 30+ minutes to under 5 minutes.

            Business Impact: Addresses reactive troubleshooting and extended MTTD requiring manual correlation across vendor-specific EMS and OSS platforms.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_degradation_detection",
                "description": "Detects cell site performance degradation in real-time using ML anomaly scores and KPI thresholds. Compares against regional baselines to prioritize NOC response and reduce MTTD from 30+ to under 5 minutes.",
                "tags": ["network", "performance", "monitoring", "ml", "esql"]
            },
            "query": """FROM network_cell_performance
| STATS avg_connection_success = AVG(network.rrc.connection_success_rate),
        avg_prb_util = AVG(network.cell.prb_utilization_dl_pct),
        avg_call_drop = AVG(network.voice.call_drop_rate),
        latest_imsi_count = MAX(network.imsi_count) BY cell_id
| LOOKUP JOIN cell_site_inventory ON cell_id
| LOOKUP JOIN ml_anomaly_scores ON cell_id
| WHERE ml.anomaly_score > 75 OR avg_connection_success < 95 OR avg_call_drop > 2
| INLINESTATS region_avg_success = AVG(avg_connection_success) BY region
| EVAL degradation_vs_region = region_avg_success - avg_connection_success
| EVAL alert_priority = CASE(
    ml.anomaly_score > 90 AND degradation_vs_region > 5, "CRITICAL",
    ml.anomaly_score > 75 OR degradation_vs_region > 3, "HIGH",
    "MEDIUM"
  )
| WHERE alert_priority IN ("CRITICAL", "HIGH")
| KEEP cell_id, cell_name, region, vendor, noc_team, avg_connection_success, avg_call_drop, ml.anomaly_score, degradation_vs_region, alert_priority
| SORT ml.anomaly_score DESC
| LIMIT 50""",
            "query_type": "scripted",
            "esql_features": ["STATS", "LOOKUP JOIN", "INLINESTATS", "EVAL", "WHERE"],
            "complexity": "high"
        })

        # SCRIPTED QUERY 2: Proactive Capacity Saturation Detection
        queries.append({
            "name": "Proactive Capacity Saturation Detection with Forecasting Indicators",
            "description": """Identifies cells approaching capacity limits by analyzing PRB utilization and subscriber concentration trends over 24 hours.
            Compares each cell against capacity tier baselines to calculate congestion risk scores, enabling proactive traffic optimization and capacity expansion planning.

            Business Impact: Addresses insufficient real-time analytics with 15-60 minute delays in detecting emerging problems using batch processing.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_capacity_saturation",
                "description": "Identifies cells approaching capacity limits using PRB utilization and subscriber concentration analysis. Calculates congestion risk scores against capacity tier baselines for proactive traffic optimization and expansion planning.",
                "tags": ["capacity", "congestion", "planning", "network", "esql"]
            },
            "query": """FROM network_cell_performance
| EVAL hour = DATE_TRUNC(1 hour, @timestamp)
| STATS avg_prb_dl = AVG(network.cell.prb_utilization_dl_pct),
        max_prb_dl = MAX(network.cell.prb_utilization_dl_pct),
        avg_prb_ul = AVG(network.cell.prb_utilization_ul_pct),
        avg_imsi = AVG(network.imsi_count),
        max_imsi = MAX(network.imsi_count) BY cell_id, hour
| LOOKUP JOIN cell_site_inventory ON cell_id
| INLINESTATS capacity_tier_avg_prb = AVG(avg_prb_dl) BY capacity_tier
| EVAL subscriber_capacity_pct = (TO_DOUBLE(max_imsi) / max_subscribers) * 100
| EVAL prb_vs_tier_avg = avg_prb_dl - capacity_tier_avg_prb
| EVAL congestion_risk_score = (avg_prb_dl * 0.5) + (subscriber_capacity_pct * 0.3) + (prb_vs_tier_avg * 0.2)
| WHERE congestion_risk_score > 70 OR avg_prb_dl > 80 OR subscriber_capacity_pct > 85
| EVAL risk_level = CASE(
    congestion_risk_score > 85, "CRITICAL_CAPACITY",
    congestion_risk_score > 75, "HIGH_RISK",
    "MODERATE_RISK"
  )
| STATS latest_hour = MAX(hour),
        avg_congestion_score = AVG(congestion_risk_score),
        peak_prb_utilization = MAX(max_prb_dl),
        peak_subscriber_pct = MAX(subscriber_capacity_pct) BY cell_id, cell_name, region, capacity_tier, vendor, risk_level
| SORT avg_congestion_score DESC
| LIMIT 100""",
            "query_type": "scripted",
            "esql_features": ["STATS", "DATE_TRUNC", "LOOKUP JOIN", "INLINESTATS", "EVAL", "WHERE"],
            "complexity": "high"
        })

        # SCRIPTED QUERY 3: Multi-Dimensional NOC Performance Benchmarking
        queries.append({
            "name": "Multi-Dimensional NOC Performance Benchmarking Dashboard",
            "description": """Provides unified NOC performance dashboard with standardized KPIs across teams, vendors, and regions using FORK to calculate multiple metric dimensions in parallel.
            Enables executive leadership to benchmark NOC efficiency and identify improvement opportunities across 15+ regional teams.

            Business Impact: Addresses lack of standardized KPIs and metrics framework across NOC teams with inconsistent definitions and incompatible dashboards preventing enterprise-wide benchmarking.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_noc_benchmarking",
                "description": "Provides unified NOC performance dashboard with standardized KPIs across teams, vendors, and regions using FORK for parallel metric calculation. Enables executive benchmarking of NOC efficiency across 15+ regional teams.",
                "tags": ["noc", "performance", "benchmarking", "kpi", "esql"]
            },
            "query": """FROM network_incidents
| LOOKUP JOIN cell_site_inventory ON cell_id
| FORK
  (STATS total_incidents = COUNT(*),
          critical_incidents = SUM(CASE(severity == "Critical", 1, 0)),
          avg_mttd = AVG(incident.mttd_minutes),
          avg_mttr = AVG(incident.mttr_minutes),
          resolution_rate_pct = (TO_DOUBLE(SUM(CASE(resolved == true, 1, 0))) / COUNT(*)) * 100 BY noc_team
   | EVAL kpi_type = "incident_metrics"
   | SORT total_incidents DESC
   | LIMIT 20)
  (STATS incidents_by_vendor = COUNT(*),
          vendor_avg_mttr = AVG(incident.mttr_minutes) BY vendor
   | EVAL kpi_type = "vendor_performance"
   | SORT incidents_by_vendor DESC)
  (STATS regional_incidents = COUNT(*),
          regional_avg_mttd = AVG(incident.mttd_minutes) BY region
   | EVAL kpi_type = "regional_metrics"
   | SORT regional_incidents DESC
   | LIMIT 15)""",
            "query_type": "scripted",
            "esql_features": ["FORK", "STATS", "LOOKUP JOIN", "EVAL", "WHERE"],
            "complexity": "high"
        })

        # SCRIPTED QUERY 4: Vendor Equipment Performance Analysis
        queries.append({
            "name": "Vendor Equipment Performance and Known Issues Analysis",
            "description": """Analyzes network performance by vendor equipment model to identify patterns related to known issues and optimization opportunities.
            Correlates actual performance metrics with vendor baseline expectations and equipment characteristics.

            Business Impact: Enables data-driven vendor management and targeted optimization based on equipment-specific performance patterns.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_vendor_analysis",
                "description": "Analyzes network performance by vendor equipment model to identify patterns and optimization opportunities. Correlates metrics with vendor baselines and equipment characteristics for data-driven vendor management.",
                "tags": ["vendor", "equipment", "performance", "optimization", "esql"]
            },
            "query": """FROM network_cell_performance
| STATS avg_rrc_success = AVG(network.rrc.connection_success_rate),
        avg_handover_success = AVG(network.handover.success_rate),
        avg_prb_util = AVG(network.cell.prb_utilization_dl_pct),
        cell_count = COUNT_DISTINCT(cell_id) BY vendor, technology
| LOOKUP JOIN vendor_equipment ON vendor, technology
| EVAL performance_vs_baseline = avg_rrc_success - baseline_connection_success_rate
| EVAL prb_vs_baseline = avg_prb_util - baseline_prb_utilization
| EVAL performance_status = CASE(
    performance_vs_baseline < -2, "BELOW_BASELINE",
    performance_vs_baseline > 2, "ABOVE_BASELINE",
    "AT_BASELINE"
  )
| KEEP vendor, technology, equipment_model, software_version, avg_rrc_success, baseline_connection_success_rate, performance_vs_baseline, avg_prb_util, cell_count, performance_status, known_issues, optimization_recommendations
| SORT performance_vs_baseline ASC
| LIMIT 30""",
            "query_type": "scripted",
            "esql_features": ["STATS", "LOOKUP JOIN", "EVAL", "WHERE"],
            "complexity": "medium"
        })

        # SCRIPTED QUERY 5: Regional Network Health Overview
        queries.append({
            "name": "Regional Network Health Overview with Anomaly Detection",
            "description": """Provides comprehensive regional network health overview combining cell performance metrics, incident counts, and ML anomaly detection results.
            Enables regional NOC teams to quickly identify areas requiring attention.

            Business Impact: Supports Network Operations Command Center unified dashboard with real-time situational awareness across all regions.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_regional_health",
                "description": "Provides comprehensive regional network health overview combining cell metrics, incident counts, and ML anomaly detection. Enables regional NOC teams to quickly identify areas requiring attention.",
                "tags": ["regional", "health", "monitoring", "ml", "esql"]
            },
            "query": """FROM network_cell_performance
| STATS avg_connection_success = AVG(network.rrc.connection_success_rate),
        avg_handover_success = AVG(network.handover.success_rate),
        avg_call_drop = AVG(network.voice.call_drop_rate),
        avg_prb_util = AVG(network.cell.prb_utilization_dl_pct),
        total_subscribers = SUM(network.imsi_count),
        cell_count = COUNT_DISTINCT(cell_id) BY region, vendor
| LOOKUP JOIN ml_anomaly_scores ON region
| STATS region_avg_connection = AVG(avg_connection_success),
        region_avg_call_drop = AVG(avg_call_drop),
        region_cells = SUM(cell_count),
        region_subscribers = SUM(total_subscribers),
        anomaly_count = SUM(CASE(ml.anomaly_score > 75, 1, 0)),
        critical_anomalies = SUM(CASE(anomaly_severity == "Critical", 1, 0)) BY region
| EVAL health_score = (region_avg_connection * 0.6) - (region_avg_call_drop * 20 * 0.4)
| EVAL health_status = CASE(
    health_score > 95, "HEALTHY",
    health_score > 90, "FAIR",
    "ATTENTION_REQUIRED"
  )
| SORT health_score ASC
| LIMIT 15""",
            "query_type": "scripted",
            "esql_features": ["STATS", "LOOKUP JOIN", "EVAL"],
            "complexity": "medium"
        })

        # SCRIPTED QUERY 6: Incident Pattern Analysis by Root Cause
        queries.append({
            "name": "Incident Pattern Analysis by Root Cause and Vendor",
            "description": """Analyzes incident patterns to identify recurring root causes by vendor, region, and incident type.
            Helps identify systemic issues requiring vendor engagement or process improvements.

            Business Impact: Reduces extended MTTR by identifying common failure patterns and enabling proactive mitigation strategies.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_incident_patterns",
                "description": "Analyzes incident patterns to identify recurring root causes by vendor, region, and type. Identifies systemic issues requiring vendor engagement or process improvements to reduce MTTR.",
                "tags": ["incidents", "root-cause", "patterns", "vendor", "esql"]
            },
            "query": """FROM network_incidents
| WHERE resolved == true
| STATS incident_count = COUNT(*),
        avg_mttd = AVG(incident.mttd_minutes),
        avg_mttr = AVG(incident.mttr_minutes),
        total_affected = SUM(affected_subscribers),
        critical_count = SUM(CASE(severity == "Critical", 1, 0)) BY root_cause, vendor, incident_type
| EVAL avg_total_resolution = avg_mttd + avg_mttr
| EVAL criticality_ratio = TO_DOUBLE(critical_count) / incident_count
| WHERE incident_count >= 5
| SORT incident_count DESC, avg_total_resolution DESC
| LIMIT 50""",
            "query_type": "scripted",
            "esql_features": ["STATS", "EVAL", "WHERE"],
            "complexity": "medium"
        })

        # SCRIPTED QUERY 7: Subscriber Session Quality Analysis
        queries.append({
            "name": "Subscriber Session Quality and Failure Pattern Analysis",
            "description": """Analyzes subscriber session quality patterns including experience scores, procedure failures, and transport performance.
            Identifies cells and APNs with poor subscriber experience requiring attention.

            Business Impact: Enables subscriber-centric experience monitoring to reduce churn risk and improve network quality.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_session_quality",
                "description": "Analyzes subscriber session quality patterns including experience scores, procedure failures, and transport performance. Identifies cells and APNs with poor subscriber experience for churn reduction.",
                "tags": ["subscribers", "quality", "experience", "sessions", "esql"]
            },
            "query": """FROM subscriber_sessions
| WHERE network.procedure.success == false
| STATS session_count = COUNT(*),
        avg_experience = AVG(subscriber.experience.score),
        avg_latency = AVG(network.transport.latency_ms),
        avg_packet_loss = AVG(network.transport.packet_loss_pct),
        unique_subscribers = COUNT_DISTINCT(imsi),
        failure_types = COUNT_DISTINCT(network.procedure.failure_cause) BY cell_id, apn, network.procedure.type
| LOOKUP JOIN cell_site_inventory ON cell_id
| WHERE session_count >= 10
| EVAL experience_category = CASE(
    avg_experience < 2, "POOR",
    avg_experience < 3, "FAIR",
    avg_experience < 4, "GOOD",
    "EXCELLENT"
  )
| SORT session_count DESC, avg_experience ASC
| LIMIT 100""",
            "query_type": "scripted",
            "esql_features": ["STATS", "LOOKUP JOIN", "EVAL", "WHERE"],
            "complexity": "medium"
        })

        # SCRIPTED QUERY 8: Technology Performance Comparison
        queries.append({
            "name": "Technology Performance Comparison (LTE vs 5G NR vs LTE-A)",
            "description": """Compares network performance across different radio access technologies (LTE, 5G NR, LTE-A) to inform modernization priorities
            and identify technology-specific optimization opportunities.

            Business Impact: Supports data-driven network modernization strategy and technology migration planning.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_technology_comparison",
                "description": "Compares network performance across radio access technologies (LTE, 5G NR, LTE-A) to inform modernization priorities. Supports data-driven network modernization strategy and technology migration planning.",
                "tags": ["technology", "5g", "lte", "modernization", "esql"]
            },
            "query": """FROM network_cell_performance
| STATS avg_rrc_success = AVG(network.rrc.connection_success_rate),
        avg_handover_success = AVG(network.handover.success_rate),
        avg_attach_success = AVG(network.procedure.attach_success_rate),
        avg_call_drop = AVG(network.voice.call_drop_rate),
        avg_session_drop = AVG(network.data.session_drop_rate),
        avg_prb_dl = AVG(network.cell.prb_utilization_dl_pct),
        avg_rsrp = AVG(network.radio.rsrp_dbm),
        avg_sinr = AVG(network.radio.sinr_db),
        total_subscribers = SUM(network.imsi_count),
        cell_count = COUNT_DISTINCT(cell_id) BY technology, region
| EVAL overall_quality_score = (avg_rrc_success * 0.3) + (avg_handover_success * 0.3) + ((100 - avg_call_drop * 20) * 0.2) + ((avg_sinr + 5) * 2 * 0.2)
| SORT technology, region
| LIMIT 50""",
            "query_type": "scripted",
            "esql_features": ["STATS", "EVAL"],
            "complexity": "medium"
        })

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries that accept user input
        
        These are Agent Builder Tool queries that let users customize parameters.
        Include parameter definitions for each query.
        """
        queries = []

        # PARAMETERIZED QUERY 1: Subscriber-Centric IMSI Journey Analysis
        queries.append({
            "name": "Subscriber-Centric IMSI Journey Root Cause Analysis",
            "description": """Provides complete end-to-end visibility into individual subscriber network experience by correlating all session events across cells, procedures, and transport metrics.
            Parameterized by IMSI and time range to enable rapid troubleshooting with enriched subscriber profile context and failure cause analysis.

            Business Impact: Addresses fragmented subscriber experience visibility requiring manual correlation across vendor-specific platforms, reducing MTTD by 15-30 minutes.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_imsi_journey",
                "description": "Provides end-to-end subscriber network experience visibility by correlating session events across cells, procedures, and transport. Enables rapid troubleshooting reducing MTTD by 15-30 minutes.",
                "tags": ["subscribers", "troubleshooting", "sessions", "imsi", "esql"]
            },
            "query": """FROM subscriber_sessions
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE imsi == ?imsi
| LOOKUP JOIN subscriber_profiles ON imsi
| LOOKUP JOIN cell_site_inventory ON cell_id
| EVAL procedure_status = CASE(network.procedure.success == true, "SUCCESS", "FAILED")
| EVAL latency_category = CASE(
    network.transport.latency_ms < 50, "EXCELLENT",
    network.transport.latency_ms < 100, "GOOD",
    network.transport.latency_ms < 200, "FAIR",
    "POOR"
  )
| STATS session_count = COUNT(*),
        avg_experience = AVG(subscriber.experience.score),
        failed_procedures = SUM(CASE(network.procedure.success == false, 1, 0)),
        total_handovers = SUM(handover_count),
        avg_latency = AVG(network.transport.latency_ms),
        unique_cells = COUNT_DISTINCT(cell_id) BY imsi, subscriber_segment, plan_type, churn_risk_score, network.procedure.failure_cause
| EVAL failure_impact_score = failed_procedures * 10 + (100 - avg_experience)
| SORT failure_impact_score DESC
| LIMIT 100""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "imsi",
                    "type": "string",
                    "description": "Subscriber IMSI to analyze (e.g., 310260000000042)",
                    "required": True
                },
                {
                    "name": "start_date",
                    "type": "datetime",
                    "description": "Analysis start time",
                    "required": True
                },
                {
                    "name": "end_date",
                    "type": "datetime",
                    "description": "Analysis end time",
                    "required": True
                }
            ],
            "esql_features": ["WHERE", "LOOKUP JOIN", "STATS", "EVAL", "SORT"],
            "complexity": "medium"
        })

        # PARAMETERIZED QUERY 2: Regional Performance Deep Dive
        queries.append({
            "name": "Regional Performance Deep Dive with Anomaly Detection",
            "description": """Analyzes detailed network performance for a specific region with ML anomaly detection integration.
            Enables regional NOC teams to investigate performance issues and identify cells requiring attention.

            Business Impact: Supports proactive network capacity planning and congestion management for specific regions.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_regional_deepdive",
                "description": "Analyzes detailed network performance for specific regions with ML anomaly detection integration. Supports proactive capacity planning and congestion management for regional NOC teams.",
                "tags": ["regional", "performance", "ml", "capacity", "esql"]
            },
            "query": """FROM network_cell_performance
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE region == ?region
| STATS avg_connection_success = AVG(network.rrc.connection_success_rate),
        avg_handover_success = AVG(network.handover.success_rate),
        avg_call_drop = AVG(network.voice.call_drop_rate),
        avg_prb_util = AVG(network.cell.prb_utilization_dl_pct),
        max_prb_util = MAX(network.cell.prb_utilization_dl_pct),
        avg_imsi = AVG(network.imsi_count) BY cell_id, vendor, technology
| LOOKUP JOIN cell_site_inventory ON cell_id
| LOOKUP JOIN ml_anomaly_scores ON cell_id
| INLINESTATS region_avg_connection = AVG(avg_connection_success)
| EVAL performance_vs_region = region_avg_connection - avg_connection_success
| EVAL alert_level = CASE(
    ml.anomaly_score > 85 OR performance_vs_region > 5, "CRITICAL",
    ml.anomaly_score > 70 OR performance_vs_region > 3, "HIGH",
    ml.anomaly_score > 50, "MEDIUM",
    "NORMAL"
  )
| WHERE alert_level IN ("CRITICAL", "HIGH", "MEDIUM")
| SORT ml.anomaly_score DESC, performance_vs_region DESC
| LIMIT 100""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "region",
                    "type": "string",
                    "description": "Region to analyze (e.g., Pacific, South Central, Northeast)",
                    "required": True
                },
                {
                    "name": "start_date",
                    "type": "datetime",
                    "description": "Analysis start time",
                    "required": True
                },
                {
                    "name": "end_date",
                    "type": "datetime",
                    "description": "Analysis end time",
                    "required": True
                }
            ],
            "esql_features": ["WHERE", "STATS", "LOOKUP JOIN", "INLINESTATS", "EVAL"],
            "complexity": "high"
        })

        # PARAMETERIZED QUERY 3: Subscriber Churn Risk Analysis
        queries.append({
            "name": "Subscriber Churn Risk Correlation with Network Experience",
            "description": """Identifies high-value subscribers at churn risk by correlating poor network experience with subscriber behavior profiles using semantic search.
            Calculates retention priority scores based on churn risk, experience gaps vs segment peers, and failure rates to enable proactive retention interventions.

            Business Impact: Reduces subscriber churn by identifying at-risk high-value customers experiencing poor network quality.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_churn_risk",
                "description": "Identifies high-value subscribers at churn risk by correlating poor network experience with behavior profiles. Calculates retention priority scores for proactive retention interventions.",
                "tags": ["churn", "retention", "subscribers", "experience", "esql"]
            },
            "query": """FROM subscriber_sessions
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| LOOKUP JOIN subscriber_profiles ON imsi
| LOOKUP JOIN cell_site_inventory ON cell_id
| WHERE churn_risk_score > ?min_churn_risk
| STATS avg_experience = AVG(subscriber.experience.score),
        session_count = COUNT(*),
        failure_rate = (TO_DOUBLE(SUM(CASE(network.procedure.success == false, 1, 0))) / COUNT(*)) * 100,
        avg_session_duration = AVG(session_duration_sec),
        unique_cells = COUNT_DISTINCT(cell_id) BY imsi, subscriber_segment, lifetime_value, churn_risk_score
| INLINESTATS segment_avg_experience = AVG(avg_experience) BY subscriber_segment
| EVAL experience_gap = segment_avg_experience - avg_experience
| EVAL retention_priority_score = (churn_risk_score * 100 * 0.4) + (experience_gap * 0.3) + (failure_rate * 0.3)
| WHERE retention_priority_score > 50
| SORT retention_priority_score DESC
| LIMIT 100""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "min_churn_risk",
                    "type": "float",
                    "description": "Minimum churn risk score to analyze (0.0 to 1.0, e.g., 0.7 for high risk)",
                    "required": True
                },
                {
                    "name": "start_date",
                    "type": "datetime",
                    "description": "Analysis start time",
                    "required": True
                },
                {
                    "name": "end_date",
                    "type": "datetime",
                    "description": "Analysis end time",
                    "required": True
                }
            ],
            "esql_features": ["WHERE", "LOOKUP JOIN", "STATS", "INLINESTATS", "EVAL"],
            "complexity": "high"
        })

        # PARAMETERIZED QUERY 4: Vendor Performance Comparison
        queries.append({
            "name": "Vendor Performance Comparison and Issue Analysis",
            "description": """Compares network performance across vendors for a specific time period and technology.
            Identifies vendor-specific issues and optimization opportunities.

            Business Impact: Enables data-driven vendor management and supports SLA compliance monitoring.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_vendor_comparison",
                "description": "Compares network performance across vendors for specific time periods and technologies. Enables data-driven vendor management and SLA compliance monitoring.",
                "tags": ["vendor", "comparison", "performance", "sla", "esql"]
            },
            "query": """FROM network_cell_performance
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE technology == ?technology
| STATS avg_rrc_success = AVG(network.rrc.connection_success_rate),
        avg_handover_success = AVG(network.handover.success_rate),
        avg_call_drop = AVG(network.voice.call_drop_rate),
        avg_prb_util = AVG(network.cell.prb_utilization_dl_pct),
        cell_count = COUNT_DISTINCT(cell_id),
        total_subscribers = SUM(network.imsi_count) BY vendor
| LOOKUP JOIN vendor_equipment ON vendor, technology
| EVAL rrc_vs_baseline = avg_rrc_success - baseline_connection_success_rate
| EVAL prb_vs_baseline = avg_prb_util - baseline_prb_utilization
| EVAL performance_score = (avg_rrc_success * 0.4) + (avg_handover_success * 0.3) + ((100 - avg_call_drop * 20) * 0.3)
| KEEP vendor, technology, equipment_model, avg_rrc_success, baseline_connection_success_rate, rrc_vs_baseline, avg_handover_success, avg_call_drop, avg_prb_util, cell_count, performance_score, known_issues, optimization_recommendations
| SORT performance_score DESC""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "technology",
                    "type": "string",
                    "description": "Technology to analyze (LTE, 5G NR, or LTE-A)",
                    "required": True
                },
                {
                    "name": "start_date",
                    "type": "datetime",
                    "description": "Analysis start time",
                    "required": True
                },
                {
                    "name": "end_date",
                    "type": "datetime",
                    "description": "Analysis end time",
                    "required": True
                }
            ],
            "esql_features": ["WHERE", "STATS", "LOOKUP JOIN", "EVAL"],
            "complexity": "medium"
        })

        # PARAMETERIZED QUERY 5: Cell Site Performance Investigation
        queries.append({
            "name": "Cell Site Performance Investigation with Incident History",
            "description": """Deep dive analysis of specific cell site performance including historical incidents, ML anomaly patterns, and subscriber impact.
            Enables rapid root cause analysis for cell site issues.

            Business Impact: Reduces MTTR from 2-4 hours to under 30 minutes by providing comprehensive cell site context.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_cell_investigation",
                "description": "Deep dive analysis of specific cell sites including historical incidents, ML anomaly patterns, and subscriber impact. Reduces MTTR from 2-4 hours to under 30 minutes with comprehensive context.",
                "tags": ["cell-site", "investigation", "incidents", "troubleshooting", "esql"]
            },
            "query": """FROM network_cell_performance
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE cell_id == ?cell_id
| STATS avg_rrc_success = AVG(network.rrc.connection_success_rate),
        min_rrc_success = MIN(network.rrc.connection_success_rate),
        avg_handover_success = AVG(network.handover.success_rate),
        avg_call_drop = AVG(network.voice.call_drop_rate),
        max_call_drop = MAX(network.voice.call_drop_rate),
        avg_prb_dl = AVG(network.cell.prb_utilization_dl_pct),
        max_prb_dl = MAX(network.cell.prb_utilization_dl_pct),
        avg_imsi = AVG(network.imsi_count),
        max_imsi = MAX(network.imsi_count) BY cell_id
| LOOKUP JOIN cell_site_inventory ON cell_id
| LOOKUP JOIN ml_anomaly_scores ON cell_id
| EVAL capacity_utilization_pct = (TO_DOUBLE(max_imsi) / max_subscribers) * 100
| EVAL performance_variance = avg_rrc_success - min_rrc_success
| KEEP cell_id, cell_name, region, vendor, technology, capacity_tier, noc_team, avg_rrc_success, min_rrc_success, performance_variance, avg_handover_success, avg_call_drop, max_call_drop, avg_prb_dl, max_prb_dl, capacity_utilization_pct, ml.anomaly_score, anomaly_severity, cell_characteristics""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "cell_id",
                    "type": "string",
                    "description": "Cell ID to investigate (e.g., CELL-000089)",
                    "required": True
                },
                {
                    "name": "start_date",
                    "type": "datetime",
                    "description": "Analysis start time",
                    "required": True
                },
                {
                    "name": "end_date",
                    "type": "datetime",
                    "description": "Analysis end time",
                    "required": True
                }
            ],
            "esql_features": ["WHERE", "STATS", "LOOKUP JOIN", "EVAL"],
            "complexity": "medium"
        })

        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using COMPLETION command
        
        CRITICAL - RAG Pipeline Requirements:
        1. MUST use MATCH to find semantically similar documents
        2. OPTIONALLY use RERANK to improve relevance
        3. MUST use COMPLETION to generate LLM-powered answers
        4. Target semantic_text fields from the strategy
        
        Semantic fields available:
        - cell_site_inventory.cell_characteristics
        - subscriber_sessions.session_description
        - subscriber_profiles.subscriber_behavior_profile
        - network_incidents.incident_description
        - network_incidents.resolution_action
        - vendor_equipment.known_issues
        - vendor_equipment.optimization_recommendations
        """
        queries = []

        # RAG QUERY 1: Cell Site Characteristics Search
        queries.append({
            "name": "Cell Site Characteristics and Configuration Search",
            "description": """Semantic search across cell site characteristics to find cells matching specific configuration, capacity, or deployment patterns.
            Uses natural language to search cell metadata including MIMO configuration, backhaul type, capacity tier, and market characteristics.

            Example questions:
            - "Find high-capacity 5G cells with fiber backhaul in urban areas"
            - "Show cells with advanced MIMO configuration serving dense urban subscribers"
            - "Which cells have millimeter wave backhaul in suburban deployments?"

            Business Impact: Enables rapid identification of cells with specific characteristics for capacity planning and optimization initiatives.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_cell_search",
                "description": "Semantic search across cell site characteristics to find cells matching specific configurations, capacity, or deployment patterns. Enables rapid identification for capacity planning and optimization.",
                "tags": ["semantic-search", "cell-site", "configuration", "rag", "esql"]
            },
            "query": """FROM cell_site_inventory METADATA _id
| WHERE MATCH(cell_characteristics, ?user_question)
| KEEP cell_id, cell_name, region, vendor, technology, capacity_tier, backhaul_type, max_subscribers, cell_characteristics, _score
| SORT _score DESC
| LIMIT 10""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "string",
                    "description": "Natural language question about cell site characteristics",
                    "required": True
                }
            ],
            "esql_features": ["MATCH", "WHERE", "SORT"],
            "complexity": "medium"
        })

        # RAG QUERY 2: Incident Resolution Knowledge Search
        queries.append({
            "name": "Network Incident Resolution Knowledge Search",
            "description": """Semantic search across historical incident descriptions and resolution actions to find similar problems and proven solutions.
            Enables NOC teams to leverage past incident resolution experience for faster troubleshooting.

            Example questions:
            - "How were handover failures in dense urban areas resolved?"
            - "Find incidents related to capacity saturation and their solutions"
            - "Show me resolution actions for vendor equipment software bugs"

            Business Impact: Reduces MTTR by 30-90 minutes by providing instant access to proven resolution strategies from similar past incidents.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_incident_search",
                "description": "Semantic search across historical incident descriptions and resolution actions to find similar problems and proven solutions. Reduces MTTR by 30-90 minutes with instant access to resolution strategies.",
                "tags": ["semantic-search", "incidents", "resolution", "rag", "esql"]
            },
            "query": """FROM network_incidents METADATA _id
| WHERE MATCH(incident_description, ?user_question) OR MATCH(resolution_action, ?user_question)
| WHERE resolved == true
| KEEP incident_id, cell_id, severity, incident_type, root_cause, incident_description, resolution_action, incident.mttd_minutes, incident.mttr_minutes, affected_subscribers, vendor, region, _score
| SORT _score DESC
| LIMIT 10""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "string",
                    "description": "Natural language question about incident resolution",
                    "required": True
                }
            ],
            "esql_features": ["MATCH", "WHERE", "SORT"],
            "complexity": "medium"
        })

        # RAG QUERY 3: Vendor Equipment Issues and Recommendations
        queries.append({
            "name": "Vendor Equipment Known Issues and Optimization Search",
            "description": """Semantic search across vendor equipment known issues and optimization recommendations to identify equipment-specific problems and solutions.
            Helps NOC teams quickly find relevant vendor guidance and optimization strategies.

            Example questions:
            - "What are known issues with Nokia 5G NR equipment?"
            - "Find optimization recommendations for LTE carrier aggregation"
            - "Show memory leak issues affecting vendor equipment performance"

            Business Impact: Accelerates vendor-specific troubleshooting and enables proactive optimization based on vendor best practices.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_vendor_search",
                "description": "Semantic search across vendor equipment known issues and optimization recommendations to identify equipment-specific problems and solutions. Accelerates vendor-specific troubleshooting and optimization.",
                "tags": ["semantic-search", "vendor", "optimization", "rag", "esql"]
            },
            "query": """FROM vendor_equipment METADATA _id
| WHERE MATCH(known_issues, ?user_question) OR MATCH(optimization_recommendations, ?user_question)
| KEEP vendor, equipment_model, technology, software_version, baseline_prb_utilization, baseline_connection_success_rate, known_issues, optimization_recommendations, _score
| SORT _score DESC
| LIMIT 10""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "string",
                    "description": "Natural language question about vendor equipment issues or optimization",
                    "required": True
                }
            ],
            "esql_features": ["MATCH", "WHERE", "SORT"],
            "complexity": "medium"
        })

        # RAG QUERY 4: Subscriber Behavior Pattern Search
        queries.append({
            "name": "Subscriber Behavior Pattern and Segmentation Search",
            "description": """Semantic search across subscriber behavior profiles to identify subscribers with specific usage patterns, device preferences, or risk characteristics.
            Enables targeted retention strategies and personalized network optimization.

            Example questions:
            - "Find premium subscribers with high data usage and low churn risk"
            - "Show enterprise customers using iPhone devices with peak hour usage"
            - "Identify subscribers with heavy video streaming patterns"

            Business Impact: Supports subscriber-centric experience monitoring and enables proactive retention for high-value at-risk subscribers.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_subscriber_search",
                "description": "Semantic search across subscriber behavior profiles to identify subscribers with specific usage patterns, device preferences, or risk characteristics. Supports targeted retention and personalized optimization.",
                "tags": ["semantic-search", "subscribers", "behavior", "rag", "esql"]
            },
            "query": """FROM subscriber_profiles METADATA _id
| WHERE MATCH(subscriber_behavior_profile, ?user_question)
| KEEP imsi, subscriber_id, plan_type, device_model, subscriber_segment, lifetime_value, avg_monthly_usage_gb, churn_risk_score, subscriber_behavior_profile, _score
| SORT _score DESC
| LIMIT 15""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "string",
                    "description": "Natural language question about subscriber behavior patterns",
                    "required": True
                }
            ],
            "esql_features": ["MATCH", "WHERE", "SORT"],
            "complexity": "medium"
        })

        # RAG QUERY 5: Session Quality Issue Investigation
        queries.append({
            "name": "Subscriber Session Quality Issue Investigation",
            "description": """Semantic search across subscriber session descriptions to find sessions with specific quality issues, procedure failures, or performance patterns.
            Helps identify common subscriber experience problems across the network.

            Example questions:
            - "Find sessions with high latency and packet loss issues"
            - "Show failed attach procedures with authentication problems"
            - "Identify sessions with multiple handovers and poor experience scores"

            Business Impact: Enables rapid identification of subscriber experience issues and patterns requiring network optimization.""",
            "tool_metadata": {
                "tool_id": "tmobile_netops_session_search",
                "description": "Semantic search across subscriber session descriptions to find sessions with specific quality issues, procedure failures, or performance patterns. Enables rapid identification of experience problems.",
                "tags": ["semantic-search", "sessions", "quality", "rag", "esql"]
            },
            "query": """FROM subscriber_sessions METADATA _id
| WHERE MATCH(session_description, ?user_question)
| KEEP session_id, imsi, cell_id, apn, subscriber.experience.score, network.transport.latency_ms, network.transport.packet_loss_pct, network.procedure.type, network.procedure.success, handover_count, session_description, _score
| SORT _score DESC
| LIMIT 15""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "string",
                    "description": "Natural language question about session quality issues",
                    "required": True
                }
            ],
            "esql_features": ["MATCH", "WHERE", "SORT"],
            "complexity": "medium"
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum impact
        
        Progression strategy:
        1. Start with real-time alerting (immediate pain point relief)
        2. Show proactive capacity planning (strategic value)
        3. Demonstrate multi-dimensional analytics (executive visibility)
        4. Deep dive into subscriber experience (customer focus)
        5. Vendor and equipment analysis (operational efficiency)
        6. Enable self-service investigation (parameterized queries)
        7. Showcase AI-powered search (RAG capabilities)
        """
        return [
            # Phase 1: Immediate Impact - Real-time Detection
            "Real-Time Cell Site Degradation Detection with Multi-Domain Enrichment",
            "Regional Network Health Overview with Anomaly Detection",
            
            # Phase 2: Strategic Value - Proactive Planning
            "Proactive Capacity Saturation Detection with Forecasting Indicators",
            "Technology Performance Comparison (LTE vs 5G NR vs LTE-A)",
            
            # Phase 3: Executive Visibility - Unified Dashboard
            "Multi-Dimensional NOC Performance Benchmarking Dashboard",
            "Incident Pattern Analysis by Root Cause and Vendor",
            
            # Phase 4: Operational Excellence - Vendor Management
            "Vendor Equipment Performance and Known Issues Analysis",
            
            # Phase 5: Customer Focus - Subscriber Experience
            "Subscriber Session Quality and Failure Pattern Analysis",
            
            # Phase 6: Self-Service Investigation - Parameterized Queries
            "Subscriber-Centric IMSI Journey Root Cause Analysis",
            "Regional Performance Deep Dive with Anomaly Detection",
            "Cell Site Performance Investigation with Incident History",
            "Subscriber Churn Risk Correlation with Network Experience",
            "Vendor Performance Comparison and Issue Analysis",
            
            # Phase 7: AI-Powered Intelligence - RAG Queries
            "Network Incident Resolution Knowledge Search",
            "Vendor Equipment Known Issues and Optimization Search",
            "Cell Site Characteristics and Configuration Search",
            "Subscriber Behavior Pattern and Segmentation Search",
            "Subscriber Session Quality Issue Investigation"
        ]
