
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class TMobileQueryGenerator(QueryGeneratorModule):
    """Query generator for T-Mobile - Network Operations & Engineering
    
    Addresses critical pain points:
    - Extended MTTR (2-4 hours) due to manual root cause analysis
    - Reactive troubleshooting with 15-30 minute MTTD delays
    - Fragmented subscriber experience visibility across vendor systems
    - Insufficient real-time analytics with 15-60 minute batch delays
    - Lack of standardized KPIs preventing enterprise-wide benchmarking
    """

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate ALL ES|QL queries from pre-planned strategy"""
        queries = []

        # ============================================================
        # SCRIPTED QUERIES - Basic exploration without parameters
        # ============================================================

        # Query 1: Real-Time Cell Site Performance Degradation Detection
        queries.append({
            'name': 'Real-Time Cell Site Performance Degradation Detection',
            'description': 'Detects cell sites experiencing performance degradation in last 15 minutes by comparing against regional averages, enabling sub-5 minute MTTD vs current 30+ minutes',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_cell_degradation',
                'description': 'Identifies cell sites with performance degradation in real-time. Compares cell metrics against regional baselines to detect anomalies before subscriber impact, reducing MTTD from 30+ minutes to under 5 minutes.',
                'tags': ['performance', 'proactive', 'cell-site', 'esql', 'alerts']
            },
            'query': '''FROM cell_performance_metrics
| STATS 
    avg_call_drop_rate = AVG(kpi.call_drop_rate), 
    avg_prb_util = AVG(network.cell.prb_utilization_dl_pct), 
    avg_ho_success = AVG(network.handover.success_rate) 
  BY network.cell.id
| LOOKUP JOIN cell_site_inventory ON network.cell.id
| INLINESTATS 
    regional_avg_drop_rate = AVG(avg_call_drop_rate), 
    regional_avg_prb = AVG(avg_prb_util) 
  BY network.region.name
| EVAL degradation_score = (avg_call_drop_rate / regional_avg_drop_rate) + (avg_prb_util / regional_avg_prb) - (avg_ho_success / 100)
| WHERE degradation_score > 2.5 OR avg_prb_util > 85
| EVAL alert_priority = CASE(
    degradation_score > 4, "CRITICAL", 
    degradation_score > 3, "HIGH", 
    "MEDIUM"
  )
| SORT degradation_score DESC
| KEEP 
    network.cell.id, 
    network.cell.name, 
    network.region.name, 
    network.noc.team, 
    avg_call_drop_rate, 
    avg_prb_util, 
    degradation_score, 
    alert_priority
| LIMIT 50''',
            'query_type': 'scripted',
            'pain_point': 'Reactive troubleshooting driven by subscriber complaints rather than proactive detection, with 15-30 minute MTTD delays'
        })

        # Query 2: Multi-Vendor Network Performance Benchmarking
        queries.append({
            'name': 'Multi-Vendor Network Performance Benchmarking',
            'description': 'Enables objective standardized KPI comparison across vendors, regions, and technologies simultaneously using parallel analysis paths for enterprise-wide benchmarking',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_vendor_benchmark',
                'description': 'Compares network performance KPIs across vendors, regions, and technologies. Provides standardized benchmarking framework to identify best-performing segments and optimization opportunities.',
                'tags': ['benchmarking', 'kpi', 'vendor', 'esql', 'analytics']
            },
            'query': '''FROM cell_performance_metrics
| LOOKUP JOIN cell_site_inventory ON network.cell.id
| FORK
  (STATS 
    avg_call_success = AVG(kpi.call_success_rate), 
    avg_ho_success = AVG(network.handover.success_rate), 
    avg_rrc_success = AVG(network.rrc.connection_success_rate), 
    p95_prb_util = PERCENTILE(capacity.busy_hour.prb_utilization_p95, 95) 
   BY network.vendor.name 
   | EVAL dimension = "vendor" 
   | RENAME network.vendor.name AS segment_name)
  (STATS 
    avg_call_success = AVG(kpi.call_success_rate), 
    avg_ho_success = AVG(network.handover.success_rate), 
    avg_rrc_success = AVG(network.rrc.connection_success_rate), 
    p95_prb_util = PERCENTILE(capacity.busy_hour.prb_utilization_p95, 95) 
   BY network.region.name 
   | EVAL dimension = "region" 
   | RENAME network.region.name AS segment_name)
  (STATS 
    avg_call_success = AVG(kpi.call_success_rate), 
    avg_ho_success = AVG(network.handover.success_rate), 
    avg_rrc_success = AVG(network.rrc.connection_success_rate), 
    p95_prb_util = PERCENTILE(capacity.busy_hour.prb_utilization_p95, 95) 
   BY network.technology 
   | EVAL dimension = "technology" 
   | RENAME network.technology AS segment_name)''',
            'query_type': 'scripted',
            'pain_point': 'Lack of standardized KPIs and metrics framework across NOC teams preventing enterprise-wide benchmarking'
        })

        # Query 3: Automated Root Cause Analysis with Event Correlation
        queries.append({
            'name': 'Automated Root Cause Analysis with Event Correlation',
            'description': 'Automatically correlates failure events and suggests probable root causes using statistical anomaly detection, reducing MTTR from 2-4 hours to under 30 minutes',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_root_cause',
                'description': 'Analyzes network signaling failures to identify root causes automatically. Correlates failure patterns across procedures and cells using anomaly detection, reducing manual MTTR from 2-4 hours to under 30 minutes.',
                'tags': ['root-cause', 'automation', 'mttr', 'esql', 'troubleshooting']
            },
            'query': '''FROM network_signaling_events
| WHERE network.procedure.success == false
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*), 
    failure_codes = MV_DEDUPE(VALUES(network.procedure.result_code)) 
  BY time_bucket, network.cell.id, network.procedure.type
| LOOKUP JOIN cell_site_inventory ON network.cell.id
| LOOKUP JOIN network_procedures_reference ON network.procedure.type
| INLINESTATS 
    avg_failures = AVG(failure_count), 
    stddev_failures = STDDEV(failure_count) 
  BY network.procedure.type
| EVAL anomaly_score = (failure_count - avg_failures) / stddev_failures
| WHERE anomaly_score > 2 OR failure_count > 100
| EVAL root_cause_indicator = CASE(
    network.procedure.category == "RRC" AND anomaly_score > 3, "Capacity_Overload",
    network.procedure.category == "Handover" AND anomaly_score > 3, "Inter_Cell_Interference",
    "Configuration_Issue"
  )
| SORT anomaly_score DESC
| KEEP 
    time_bucket, 
    network.cell.id, 
    network.cell.name, 
    network.procedure.type, 
    failure_count, 
    anomaly_score, 
    root_cause_indicator, 
    failure_codes
| LIMIT 100''',
            'query_type': 'scripted',
            'pain_point': 'Extended MTTR (2-4 hours) due to manual root cause analysis workflows across multiple systems'
        })

        # Query 4: Network Anomaly Detection with Subscriber Activity Changes
        queries.append({
            'name': 'Network Anomaly Detection with Subscriber Activity Changes',
            'description': 'Detects statistically significant changes in subscriber activity patterns per cell site, enabling proactive detection before complaints arrive and reducing MTTD to under 5 minutes',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_subscriber_anomaly',
                'description': 'Identifies sudden changes in subscriber activity patterns at cell sites. Detects subscriber churn spikes or connection drops proactively using statistical analysis, enabling intervention before mass complaints.',
                'tags': ['anomaly', 'subscribers', 'proactive', 'esql', 'detection']
            },
            'query': '''FROM network_signaling_events
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS unique_subscribers = COUNT_DISTINCT(subscriber.imsi) BY time_bucket, network.cell.id
| INLINESTATS 
    avg_subs = AVG(unique_subscribers), 
    stddev_subs = STDDEV(unique_subscribers) 
  BY network.cell.id
| EVAL z_score = (unique_subscribers - avg_subs) / stddev_subs
| WHERE z_score < -2 OR z_score > 2
| LOOKUP JOIN cell_site_inventory ON network.cell.id
| EVAL alert_type = CASE(
    z_score < -2, "Subscriber_Churn_Spike",
    "Subscriber_Surge"
  )
| SORT time_bucket DESC
| KEEP 
    time_bucket, 
    network.cell.id, 
    network.cell.name, 
    network.region.name, 
    network.noc.team, 
    unique_subscribers, 
    z_score, 
    alert_type
| LIMIT 50''',
            'query_type': 'scripted',
            'pain_point': 'Reactive troubleshooting driven by subscriber complaints rather than proactive detection, with 15-30 minute MTTD delays'
        })

        # Query 5: Unified NOC Dashboard Multi-Dimensional View
        queries.append({
            'name': 'Unified NOC Dashboard Multi-Dimensional View',
            'description': 'Provides real-time unified executive dashboard combining performance KPIs, signaling health, incidents, and capacity alerts with sub-minute latency vs 15-60 minute batch delays',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_noc_dashboard',
                'description': 'Provides comprehensive real-time network operations view. Combines performance KPIs, signaling health, active incidents, and capacity alerts in unified dashboard with sub-minute latency instead of 15-60 minute batch delays.',
                'tags': ['dashboard', 'realtime', 'executive', 'esql', 'operations']
            },
            'query': '''FROM cell_performance_metrics
| STATS 
    avg_call_drop = AVG(kpi.call_drop_rate), 
    avg_prb_util = AVG(network.cell.prb_utilization_dl_pct),
    total_active_subs = SUM(network.cell.active_subscribers),
    avg_transport_latency = AVG(network.transport.latency_ms),
    cells_over_80_util = COUNT_IF(network.cell.prb_utilization_dl_pct > 80)
| EVAL metric_category = "performance_kpis"''',
            'query_type': 'scripted',
            'pain_point': 'Insufficient real-time analytics for high-cardinality network data with 15-60 minute batch processing delays'
        })

        # Query 6: Capacity Planning - Cells Approaching Congestion
        queries.append({
            'name': 'Capacity Planning - Cells Approaching Congestion',
            'description': 'Identifies cell sites approaching capacity limits using historical trending and current utilization patterns for proactive capacity planning',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_capacity_planning',
                'description': 'Identifies cells approaching capacity limits for proactive planning. Analyzes PRB utilization trends and busy hour patterns to predict congestion before subscriber impact occurs.',
                'tags': ['capacity', 'planning', 'proactive', 'esql', 'congestion']
            },
            'query': '''FROM cell_performance_metrics
| STATS 
    avg_prb_dl = AVG(network.cell.prb_utilization_dl_pct),
    avg_prb_ul = AVG(network.cell.prb_utilization_ul_pct),
    p95_busy_hour = AVG(capacity.busy_hour.prb_utilization_p95),
    avg_active_subs = AVG(network.cell.active_subscribers)
  BY network.cell.id
| LOOKUP JOIN cell_site_inventory ON network.cell.id
| EVAL capacity_risk_score = (avg_prb_dl * 0.4) + (p95_busy_hour * 0.4) + ((avg_active_subs / network.cell.capacity_subscribers) * 100 * 0.2)
| WHERE capacity_risk_score > 70
| EVAL risk_level = CASE(
    capacity_risk_score > 85, "CRITICAL",
    capacity_risk_score > 75, "HIGH",
    "MEDIUM"
  )
| SORT capacity_risk_score DESC
| KEEP 
    network.cell.id,
    network.cell.name,
    network.region.name,
    network.vendor.name,
    network.technology,
    avg_prb_dl,
    p95_busy_hour,
    avg_active_subs,
    network.cell.capacity_subscribers,
    capacity_risk_score,
    risk_level
| LIMIT 50''',
            'query_type': 'scripted',
            'pain_point': 'Proactive Network Capacity Planning & Congestion Management - Use historical trending and predictive analytics to identify cells approaching capacity limits'
        })

        # Query 7: Handover Performance Analysis by Vendor
        queries.append({
            'name': 'Handover Performance Analysis by Vendor',
            'description': 'Analyzes handover success rates and identifies inter-vendor handover issues that may indicate configuration problems or interference',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_handover_analysis',
                'description': 'Analyzes handover performance across vendors and cell pairs. Identifies problematic handover paths and inter-vendor issues to optimize mobility experience and reduce call drops.',
                'tags': ['handover', 'mobility', 'vendor', 'esql', 'optimization']
            },
            'query': '''FROM network_signaling_events
| WHERE network.procedure.type == "HANDOVER"
| STATS 
    total_handovers = COUNT(*),
    successful_handovers = COUNT_IF(network.handover.success == true),
    failed_handovers = COUNT_IF(network.handover.success == false),
    avg_signal_rsrp = AVG(network.radio.rsrp_dbm)
  BY network.handover.source_cell, network.handover.target_cell
| EVAL success_rate_pct = (TO_DOUBLE(successful_handovers) * 100.0) / total_handovers
| WHERE total_handovers > 10 AND success_rate_pct < 95
| LOOKUP JOIN cell_site_inventory ON network.handover.source_cell == network.cell.id
| RENAME 
    network.vendor.name AS source_vendor,
    network.region.name AS source_region
| SORT success_rate_pct ASC
| KEEP 
    network.handover.source_cell,
    network.handover.target_cell,
    source_vendor,
    source_region,
    total_handovers,
    success_rate_pct,
    avg_signal_rsrp
| LIMIT 100''',
            'query_type': 'scripted',
            'pain_point': 'Fragmented subscriber experience visibility across network domains requiring manual correlation across vendor-specific Element Management Systems'
        })

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries that accept user input"""
        queries = []

        # Query 1: Subscriber-Centric Experience Troubleshooting
        queries.append({
            'name': 'Subscriber-Centric Experience Troubleshooting with Network Context',
            'description': 'Provides complete unified view of individual subscriber network experience across all vendors and domains for rapid complaint resolution, eliminating manual correlation',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_subscriber_experience',
                'description': 'Analyzes complete subscriber network experience for troubleshooting. Provides unified view across vendors, procedures, and cells to resolve complaints rapidly without manual correlation across systems.',
                'tags': ['subscriber', 'troubleshooting', 'experience', 'esql', 'support']
            },
            'query': '''FROM network_signaling_events
| WHERE subscriber.imsi == ?subscriber_imsi
| LOOKUP JOIN subscriber_profiles ON subscriber.imsi
| LOOKUP JOIN cell_site_inventory ON network.cell.id
| STATS 
    procedure_count = COUNT(*), 
    success_count = COUNT_IF(network.procedure.success == true), 
    avg_rsrp = AVG(network.radio.rsrp_dbm), 
    avg_sinr = AVG(network.radio.sinr_db), 
    cell_count = COUNT_DISTINCT(network.cell.id) 
  BY network.procedure.type, network.vendor.name
| EVAL success_rate_pct = (TO_DOUBLE(success_count) * 100.0) / procedure_count
| EVAL signal_quality = CASE(
    avg_rsrp > -80 AND avg_sinr > 10, "EXCELLENT", 
    avg_rsrp > -95 AND avg_sinr > 5, "GOOD", 
    avg_rsrp > -105, "FAIR", 
    "POOR"
  )
| SORT procedure_count DESC
| KEEP 
    network.procedure.type, 
    network.vendor.name, 
    procedure_count, 
    success_rate_pct, 
    avg_rsrp, 
    avg_sinr, 
    signal_quality, 
    cell_count''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'subscriber_imsi',
                    'type': 'string',
                    'description': 'Subscriber IMSI to analyze (e.g., 310260380691721)',
                    'required': True
                }
            ],
            'pain_point': 'Fragmented subscriber experience visibility across network domains requiring manual correlation across vendor-specific Element Management Systems'
        })

        # Query 2: Regional Performance Analysis with Time Range
        queries.append({
            'name': 'Regional Performance Analysis with Time Range',
            'description': 'Compares network performance across regions for a specified time period to identify underperforming areas',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_regional_performance',
                'description': 'Compares network KPIs across regions for custom time periods. Identifies underperforming regions and trends to guide resource allocation and optimization efforts.',
                'tags': ['regional', 'performance', 'comparison', 'esql', 'analytics']
            },
            'query': '''FROM cell_performance_metrics
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| LOOKUP JOIN cell_site_inventory ON network.cell.id
| STATS 
    avg_call_success = AVG(kpi.call_success_rate),
    avg_call_drop = AVG(kpi.call_drop_rate),
    avg_ho_success = AVG(network.handover.success_rate),
    avg_prb_util = AVG(network.cell.prb_utilization_dl_pct),
    cell_count = COUNT_DISTINCT(network.cell.id)
  BY network.region.name
| EVAL performance_score = (avg_call_success + avg_ho_success) / 2 - (avg_call_drop * 10)
| SORT performance_score DESC
| KEEP 
    network.region.name,
    avg_call_success,
    avg_call_drop,
    avg_ho_success,
    avg_prb_util,
    cell_count,
    performance_score''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'datetime',
                    'description': 'Start date for analysis period',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'datetime',
                    'description': 'End date for analysis period',
                    'required': True
                }
            ],
            'pain_point': 'Lack of standardized KPIs and metrics framework across NOC teams preventing enterprise-wide benchmarking'
        })

        # Query 3: Cell Site Performance Deep Dive
        queries.append({
            'name': 'Cell Site Performance Deep Dive',
            'description': 'Provides detailed performance analysis for a specific cell site including all KPIs, procedures, and trending',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_cell_deep_dive',
                'description': 'Analyzes detailed performance metrics for specific cell site. Provides comprehensive KPI view including procedures, capacity, and signal quality for targeted troubleshooting.',
                'tags': ['cell-site', 'deep-dive', 'troubleshooting', 'esql', 'detailed']
            },
            'query': '''FROM cell_performance_metrics
| WHERE network.cell.id == ?cell_id
| LOOKUP JOIN cell_site_inventory ON network.cell.id
| STATS 
    avg_call_success = AVG(kpi.call_success_rate),
    avg_call_drop = AVG(kpi.call_drop_rate),
    avg_ho_success = AVG(network.handover.success_rate),
    avg_rrc_success = AVG(network.rrc.connection_success_rate),
    avg_prb_dl = AVG(network.cell.prb_utilization_dl_pct),
    avg_prb_ul = AVG(network.cell.prb_utilization_ul_pct),
    p95_busy_hour = AVG(capacity.busy_hour.prb_utilization_p95),
    avg_active_subs = AVG(network.cell.active_subscribers),
    avg_latency = AVG(network.transport.latency_ms),
    avg_packet_loss = AVG(network.transport.packet_loss_pct)
| EVAL health_score = (avg_call_success + avg_ho_success + avg_rrc_success) / 3
| KEEP 
    network.cell.id,
    network.cell.name,
    network.vendor.name,
    network.technology,
    network.region.name,
    avg_call_success,
    avg_call_drop,
    avg_ho_success,
    avg_rrc_success,
    avg_prb_dl,
    avg_prb_ul,
    p95_busy_hour,
    avg_active_subs,
    avg_latency,
    avg_packet_loss,
    health_score''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'cell_id',
                    'type': 'string',
                    'description': 'Cell ID to analyze (e.g., CELL-00001)',
                    'required': True
                }
            ],
            'pain_point': 'Extended MTTR (2-4 hours) due to manual root cause analysis workflows across multiple systems'
        })

        # Query 4: Vendor Performance Comparison for Technology
        queries.append({
            'name': 'Vendor Performance Comparison for Technology',
            'description': 'Compares vendor performance for a specific technology (LTE, LTE-A, 5G NR) to identify best practices and issues',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_vendor_tech_compare',
                'description': 'Compares vendor performance within specific technology. Identifies which vendors deliver best KPIs for LTE, LTE-A, or 5G NR to guide procurement and optimization decisions.',
                'tags': ['vendor', 'technology', 'comparison', 'esql', 'benchmarking']
            },
            'query': '''FROM cell_performance_metrics
| LOOKUP JOIN cell_site_inventory ON network.cell.id
| WHERE network.technology == ?technology
| STATS 
    avg_call_success = AVG(kpi.call_success_rate),
    avg_call_drop = AVG(kpi.call_drop_rate),
    avg_ho_success = AVG(network.handover.success_rate),
    avg_rrc_success = AVG(network.rrc.connection_success_rate),
    avg_prb_util = AVG(network.cell.prb_utilization_dl_pct),
    cell_count = COUNT_DISTINCT(network.cell.id)
  BY network.vendor.name
| EVAL vendor_score = (avg_call_success + avg_ho_success + avg_rrc_success) / 3 - (avg_call_drop * 10)
| SORT vendor_score DESC
| KEEP 
    network.vendor.name,
    avg_call_success,
    avg_call_drop,
    avg_ho_success,
    avg_rrc_success,
    avg_prb_util,
    cell_count,
    vendor_score''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'technology',
                    'type': 'string',
                    'description': 'Technology type to analyze (LTE, LTE-A, or 5G NR)',
                    'required': True
                }
            ],
            'pain_point': 'Lack of standardized KPIs and metrics framework across NOC teams preventing enterprise-wide benchmarking'
        })

        # Query 5: Incident Pattern Analysis by Severity
        queries.append({
            'name': 'Incident Pattern Analysis by Severity',
            'description': 'Analyzes incident patterns for a specific severity level to identify common root causes and affected areas',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_incident_patterns',
                'description': 'Analyzes incident patterns by severity level. Identifies common root causes, affected regions, and MTTR trends to improve incident response and prevention strategies.',
                'tags': ['incidents', 'patterns', 'severity', 'esql', 'analysis']
            },
            'query': '''FROM network_incidents
| WHERE incident.severity == ?severity
| LOOKUP JOIN cell_site_inventory ON network.cell.id
| STATS 
    incident_count = COUNT(*),
    avg_mttr = AVG(incident.mttr_minutes),
    avg_mttd = AVG(incident.mttd_minutes),
    total_affected_subs = SUM(incident.affected_subscribers),
    unique_cells = COUNT_DISTINCT(network.cell.id)
  BY incident.root_cause, network.region.name
| EVAL mttr_category = CASE(
    avg_mttr < 30, "Fast",
    avg_mttr < 120, "Moderate",
    "Slow"
  )
| WHERE incident_count > 3
| SORT incident_count DESC
| KEEP 
    incident.root_cause,
    network.region.name,
    incident_count,
    avg_mttr,
    avg_mttd,
    mttr_category,
    total_affected_subs,
    unique_cells
| LIMIT 50''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'severity',
                    'type': 'string',
                    'description': 'Incident severity level (CRITICAL, HIGH, MEDIUM, LOW)',
                    'required': True
                }
            ],
            'pain_point': 'Extended MTTR (2-4 hours) due to manual root cause analysis workflows across multiple systems'
        })

        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using COMPLETION command"""
        queries = []

        # Query 1: Incident Resolution Knowledge Search
        queries.append({
            'name': 'Incident Resolution Knowledge Search',
            'description': 'Searches historical incident resolutions using semantic search to find similar past incidents and their solutions',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_incident_knowledge',
                'description': 'Finds similar past incidents and resolutions using semantic search. Helps NOC engineers quickly identify proven solutions based on incident descriptions and resolution notes.',
                'tags': ['rag', 'incidents', 'knowledge', 'esql', 'semantic']
            },
            'query': '''FROM network_incidents METADATA _id
| WHERE MATCH(incident.description, ?user_question, {"fuzziness": "AUTO"})
| LOOKUP JOIN cell_site_inventory ON network.cell.id
| EVAL context = CONCAT(
    "Incident: ", incident.description, 
    " | Root Cause: ", incident.root_cause,
    " | Resolution: ", incident.resolution_notes,
    " | Cell: ", network.cell.name,
    " | Vendor: ", network.vendor.name,
    " | Region: ", network.region.name,
    " | MTTR: ", TO_STRING(incident.mttr_minutes), " minutes"
  )
| KEEP incident.id, incident.description, incident.root_cause, incident.resolution_notes, network.cell.name, network.vendor.name, network.region.name, incident.mttr_minutes, context, _score
| SORT _score DESC
| LIMIT 5''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'string',
                    'description': 'Describe the incident or issue you are troubleshooting',
                    'required': True
                }
            ],
            'pain_point': 'Extended MTTR (2-4 hours) due to manual root cause analysis workflows across multiple systems'
        })

        # Query 2: Cell Site Characteristics Search
        queries.append({
            'name': 'Cell Site Characteristics Search',
            'description': 'Searches cell site inventory using semantic understanding of site characteristics and deployment details',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_cell_search',
                'description': 'Finds cell sites matching specific characteristics using semantic search. Helps identify cells with similar configurations, equipment, or deployment patterns for analysis.',
                'tags': ['rag', 'cell-site', 'inventory', 'esql', 'semantic']
            },
            'query': '''FROM cell_site_inventory METADATA _id
| WHERE MATCH(cell.characteristics, ?user_question, {"fuzziness": "AUTO"})
| EVAL context = CONCAT(
    "Cell: ", network.cell.name,
    " | ID: ", network.cell.id,
    " | Vendor: ", network.vendor.name,
    " | Technology: ", network.technology,
    " | Region: ", network.region.name,
    " | Characteristics: ", cell.characteristics,
    " | Capacity: ", TO_STRING(network.cell.capacity_subscribers), " subscribers"
  )
| KEEP network.cell.id, network.cell.name, network.vendor.name, network.technology, network.region.name, cell.characteristics, network.cell.capacity_subscribers, context, _score
| SORT _score DESC
| LIMIT 10''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'string',
                    'description': 'Describe the cell site characteristics you are looking for',
                    'required': True
                }
            ],
            'pain_point': 'Fragmented subscriber experience visibility across network domains requiring manual correlation across vendor-specific Element Management Systems'
        })

        # Query 3: Network Procedure Documentation Search
        queries.append({
            'name': 'Network Procedure Documentation Search',
            'description': 'Searches network procedure reference documentation to understand expected behavior and thresholds',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_procedure_docs',
                'description': 'Finds network procedure documentation using semantic search. Helps engineers understand expected procedure behavior, duration targets, and success thresholds for troubleshooting.',
                'tags': ['rag', 'procedures', 'documentation', 'esql', 'semantic']
            },
            'query': '''FROM network_procedures_reference METADATA _id
| WHERE MATCH(network.procedure.description, ?user_question, {"fuzziness": "AUTO"})
| EVAL context = CONCAT(
    "Procedure: ", network.procedure.name,
    " | Type: ", network.procedure.type,
    " | Category: ", network.procedure.category,
    " | Expected Duration: ", TO_STRING(network.procedure.expected_duration_ms), "ms",
    " | Success Threshold: ", TO_STRING(network.procedure.success_threshold_pct), "%",
    " | Description: ", network.procedure.description
  )
| KEEP network.procedure.type, network.procedure.name, network.procedure.category, network.procedure.expected_duration_ms, network.procedure.success_threshold_pct, network.procedure.description, context, _score
| SORT _score DESC
| LIMIT 5''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'string',
                    'description': 'Ask about network procedures or signaling behavior',
                    'required': True
                }
            ],
            'pain_point': 'Extended MTTR (2-4 hours) due to manual root cause analysis workflows across multiple systems'
        })

        # Query 4: Subscriber Profile Search
        queries.append({
            'name': 'Subscriber Profile Search',
            'description': 'Searches subscriber profiles using semantic understanding of customer characteristics and device capabilities',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_subscriber_search',
                'description': 'Finds subscribers matching specific profile characteristics. Helps identify customer segments with similar plans, devices, or usage patterns for targeted analysis.',
                'tags': ['rag', 'subscriber', 'profiles', 'esql', 'semantic']
            },
            'query': '''FROM subscriber_profiles METADATA _id
| WHERE MATCH(subscriber.profile_description, ?user_question, {"fuzziness": "AUTO"})
| EVAL context = CONCAT(
    "IMSI: ", subscriber.imsi,
    " | Plan: ", subscriber.plan_type,
    " | Tier: ", subscriber.tier,
    " | Device: ", subscriber.device_model,
    " | Capability: ", subscriber.device_capability,
    " | Tenure: ", TO_STRING(subscriber.tenure_months), " months",
    " | ARPU: $", TO_STRING(subscriber.arpu),
    " | Profile: ", subscriber.profile_description
  )
| KEEP subscriber.imsi, subscriber.msisdn, subscriber.plan_type, subscriber.tier, subscriber.device_model, subscriber.device_capability, subscriber.tenure_months, subscriber.arpu, subscriber.profile_description, context, _score
| SORT _score DESC
| LIMIT 10''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'string',
                    'description': 'Describe the subscriber characteristics you are looking for',
                    'required': True
                }
            ],
            'pain_point': 'Fragmented subscriber experience visibility across network domains requiring manual correlation across vendor-specific Element Management Systems'
        })

        # Query 5: Network Event Description Search
        queries.append({
            'name': 'Network Event Description Search',
            'description': 'Searches network signaling events using semantic understanding of event descriptions and failure patterns',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_event_search',
                'description': 'Finds network signaling events matching specific patterns. Uses semantic search on event descriptions to identify similar failures, procedures, or signal quality issues.',
                'tags': ['rag', 'events', 'signaling', 'esql', 'semantic']
            },
            'query': '''FROM network_signaling_events METADATA _id
| WHERE MATCH(event.description, ?user_question, {"fuzziness": "AUTO"})
| LOOKUP JOIN cell_site_inventory ON network.cell.id
| EVAL context = CONCAT(
    "Event: ", event.description,
    " | Procedure: ", network.procedure.type,
    " | Result: ", network.procedure.result_code,
    " | Cell: ", network.cell.name,
    " | Vendor: ", network.vendor.name,
    " | Technology: ", network.technology,
    " | Signal RSRP: ", TO_STRING(network.radio.rsrp_dbm), "dBm",
    " | SINR: ", TO_STRING(network.radio.sinr_db), "dB"
  )
| KEEP event.description, network.procedure.type, network.procedure.result_code, network.cell.name, network.vendor.name, network.technology, network.radio.rsrp_dbm, network.radio.sinr_db, context, _score
| SORT _score DESC
| LIMIT 10''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'string',
                    'description': 'Describe the network event or issue you are investigating',
                    'required': True
                }
            ],
            'pain_point': 'Inability to correlate network events with subscriber behavior patterns across disparate systems'
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum impact"""
        return [
            # Start with immediate impact - proactive detection
            'Real-Time Cell Site Performance Degradation Detection',
            'Network Anomaly Detection with Subscriber Activity Changes',
            
            # Show troubleshooting efficiency gains
            'Automated Root Cause Analysis with Event Correlation',
            'Subscriber-Centric Experience Troubleshooting with Network Context',
            
            # Demonstrate strategic insights
            'Multi-Vendor Network Performance Benchmarking',
            'Capacity Planning - Cells Approaching Congestion',
            
            # Show operational excellence
            'Unified NOC Dashboard Multi-Dimensional View',
            'Handover Performance Analysis by Vendor',
            
            # Deep dive capabilities
            'Cell Site Performance Deep Dive',
            'Regional Performance Analysis with Time Range',
            'Vendor Performance Comparison for Technology',
            'Incident Pattern Analysis by Severity',
            
            # Knowledge management with RAG
            'Incident Resolution Knowledge Search',
            'Network Event Description Search',
            'Cell Site Characteristics Search',
            'Network Procedure Documentation Search',
            'Subscriber Profile Search'
        ]
