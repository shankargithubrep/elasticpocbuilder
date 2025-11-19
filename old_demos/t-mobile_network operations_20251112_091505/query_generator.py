
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class TMobileQueryGenerator(QueryGeneratorModule):
    """Query generator for T-Mobile - Network Operations
    
    Implements queries for detecting network issues, authentication failures,
    security attacks, and performance degradation in 4G/5G mobile networks.
    """

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate ALL ES|QL queries from pre-planned strategy"""
        queries = []

        # ================================================================
        # SCRIPTED QUERIES - Basic exploration, no parameters
        # ================================================================

        # Query 1: IMSI and Cell ID Spike Detection with Multi-Lag Analysis
        queries.append({
            'name': 'IMSI and Cell ID Spike Detection with Multi-Lag Analysis',
            'description': 'Detect sustained spike patterns by calculating unique IMSI and cell ID counts per 5-minute interval, comparing current counts against 1-lag and 2-lag periods to identify anomalies (imsi_change_1 > 400, imsi_change_2 > 280, cell_id_change_1 > 50, cell_id_change_2 > 25) indicating network issues or mass events',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_imsi_spike_detection',
                'description': 'Detects network anomalies by tracking unique IMSI and cell ID cardinality spikes. Identifies mass events or network issues before help desk is overwhelmed using multi-lag pattern analysis.',
                'tags': ['network', 'anomaly', 'capacity', 'proactive', 'esql']
            },
            'query': '''FROM lte_s1ap_events
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    unique_imsi = COUNT_DISTINCT(imsi),
    unique_cell_id = COUNT_DISTINCT(cell_id),
    event_count = COUNT(*)
  BY time_bucket, mme_host
| SORT time_bucket ASC, mme_host ASC
| INLINESTATS 
    imsi_lag1 = LAG(unique_imsi, 1) OVER (PARTITION BY mme_host ORDER BY time_bucket),
    imsi_lag2 = LAG(unique_imsi, 2) OVER (PARTITION BY mme_host ORDER BY time_bucket),
    cell_lag1 = LAG(unique_cell_id, 1) OVER (PARTITION BY mme_host ORDER BY time_bucket),
    cell_lag2 = LAG(unique_cell_id, 2) OVER (PARTITION BY mme_host ORDER BY time_bucket)
  BY mme_host
| EVAL 
    imsi_change_1 = unique_imsi - COALESCE(imsi_lag1, unique_imsi),
    imsi_change_2 = unique_imsi - COALESCE(imsi_lag2, unique_imsi),
    cell_id_change_1 = unique_cell_id - COALESCE(cell_lag1, unique_cell_id),
    cell_id_change_2 = unique_cell_id - COALESCE(cell_lag2, unique_cell_id)
| WHERE imsi_change_1 > 400 OR imsi_change_2 > 280 OR cell_id_change_1 > 50 OR cell_id_change_2 > 25
| EVAL 
    alert_severity = CASE(
        imsi_change_1 > 800 OR cell_id_change_1 > 100, "CRITICAL",
        imsi_change_1 > 600 OR cell_id_change_1 > 75, "HIGH",
        "MEDIUM"
    )
| KEEP time_bucket, mme_host, unique_imsi, unique_cell_id, imsi_change_1, imsi_change_2, cell_id_change_1, cell_id_change_2, alert_severity, event_count
| SORT alert_severity ASC, time_bucket DESC
| LIMIT 100''',
            'query_type': 'scripted',
            'pain_point': 'Need to detect network issues before help desk is overwhelmed by tracking unique IMSI and cell ID cardinality changes over time'
        })

        # Query 2: HSS Mass Authentication Failure Detection (Scripted)
        queries.append({
            'name': 'HSS Mass Authentication Failure Detection',
            'description': 'Identify mass authentication failure events by aggregating failed authentication attempts per 5-minute interval (minimum 200 failures), enriched with HSS node details to pinpoint database corruption, synchronization issues, or replication failures',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_hss_auth_failures',
                'description': 'Identifies HSS database corruption and synchronization issues by detecting mass authentication failure events. Enriches failures with HSS cluster and replication details for rapid troubleshooting.',
                'tags': ['authentication', 'hss', 'database', 'failures', 'esql']
            },
            'query': '''FROM hss_authentication_events
| WHERE auth_result != "Success"
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    sync_failures = SUM(CASE(sync_failure == true, 1, 0)),
    sqn_failures = SUM(CASE(sqn_failure == true, 1, 0)),
    avg_response_time = AVG(response_time_ms)
  BY time_bucket, hss_node, auth_result
| WHERE failure_count >= 200
| LOOKUP JOIN hss_node_reference ON hss_node
| EVAL 
    failure_rate_per_min = TO_DOUBLE(failure_count) / 5.0,
    sync_failure_pct = TO_DOUBLE(sync_failures) * 100.0 / failure_count
| KEEP time_bucket, hss_node, hss_cluster, datacenter, database_type, replication_mode, auth_result, failure_count, unique_imsi, sync_failures, sqn_failures, sync_failure_pct, failure_rate_per_min, avg_response_time
| SORT failure_count DESC, time_bucket DESC
| LIMIT 50''',
            'query_type': 'scripted',
            'pain_point': 'HSS database corruption or synchronization issues affecting subscriber authentication leading to service downtime and revenue loss'
        })

        # Query 3: Cell Tower Handoff Cascade Failure Analysis
        queries.append({
            'name': 'Cell Tower Handoff Cascade Failure Analysis',
            'description': 'Detect cell tower handoff cascade failures by analyzing handover failure patterns across neighbor cells within 5-minute windows, enriched with cell tower geography and neighbor relationships to identify radio equipment failures',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_handoff_cascade',
                'description': 'Detects cell tower handoff cascade failures by analyzing geographic patterns. Identifies radio equipment failures and coverage gaps affecting multiple neighbor cells and subscribers.',
                'tags': ['handover', 'radio', 'coverage', 'mobility', 'esql']
            },
            'query': '''FROM lte_s1ap_events
| WHERE procedure_type == "Handover" AND handover_result == "Failure"
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    unique_cells = COUNT_DISTINCT(cell_id)
  BY time_bucket, cell_id, cause_group
| WHERE failure_count >= 50 OR unique_cells >= 50 OR unique_imsi >= 500
| LOOKUP JOIN cell_tower_reference ON cell_id
| EVAL 
    failure_rate = TO_DOUBLE(failure_count) / 5.0,
    impact_score = failure_count * unique_cells
| KEEP time_bucket, cell_id, cell_name, site_id, region, market, technology, frequency_band, neighbor_cells, cause_group, failure_count, unique_imsi, unique_cells, failure_rate, impact_score
| SORT impact_score DESC, time_bucket DESC
| LIMIT 50''',
            'query_type': 'scripted',
            'pain_point': 'Radio equipment failure and cell tower handoff failures causing dropped calls during mobility and interrupted data sessions'
        })

        # Query 4: MME Resource Exhaustion and Software Bug Detection
        queries.append({
            'name': 'MME Resource Exhaustion and Software Bug Detection',
            'description': 'Identify MME software bugs or resource exhaustion by correlating service request procedure failures (minimum 200 failures per 5-minute interval) with MME resource utilization metrics, enriched with software version and capacity tier',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_mme_exhaustion',
                'description': 'Identifies MME software bugs and resource exhaustion by correlating service request failures with resource metrics. Pinpoints specific MME hosts experiencing capacity or software issues.',
                'tags': ['mme', 'capacity', 'performance', 'software', 'esql']
            },
            'query': '''FROM lte_s1ap_events
| WHERE procedure_type == "Service Request" AND service_request_result == "Failure"
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi)
  BY time_bucket, mme_host
| WHERE failure_count >= 200
| LOOKUP JOIN mme_host_reference ON mme_host
| EVAL 
    failure_rate_per_min = TO_DOUBLE(failure_count) / 5.0,
    impact_severity = CASE(
        failure_count > 1000, "CRITICAL",
        failure_count > 500, "HIGH",
        "MEDIUM"
    )
| KEEP time_bucket, mme_host, mme_pool, datacenter, software_version, capacity_tier, max_subscribers, failure_count, unique_imsi, failure_rate_per_min, impact_severity
| SORT failure_count DESC, time_bucket DESC
| LIMIT 50''',
            'query_type': 'scripted',
            'pain_point': 'MME software bugs and resource exhaustion causing service request procedure failures and UE initiated service request failures'
        })

        # Query 5: SS7 Security Attack Detection
        queries.append({
            'name': 'SS7 Security Attack and Roaming Misconfiguration Detection',
            'description': 'Detect SS7 security attacks or roaming misconfigurations by identifying attack signature patterns per originating network, enriched with threat intelligence including threat category, description, and mitigation strategies',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_ss7_security',
                'description': 'Detects SS7 security attacks and roaming misconfigurations using threat intelligence. Identifies malicious signaling patterns and provides mitigation strategies for network protection.',
                'tags': ['security', 'ss7', 'threats', 'roaming', 'esql']
            },
            'query': '''FROM ss7_security_events
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    event_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    blocked_count = SUM(CASE(blocked == true, 1, 0)),
    critical_count = SUM(CASE(threat_level == "Critical", 1, 0)),
    high_count = SUM(CASE(threat_level == "High", 1, 0))
  BY time_bucket, originating_network, attack_signature, threat_level
| LOOKUP JOIN threat_signature_reference ON attack_signature
| EVAL 
    block_rate = TO_DOUBLE(blocked_count) * 100.0 / event_count,
    threat_score = critical_count * 10 + high_count * 5 + event_count
| KEEP time_bucket, originating_network, attack_signature, threat_name, threat_category, threat_level, threat_description, mitigation_strategy, event_count, unique_imsi, blocked_count, block_rate, threat_score
| SORT threat_score DESC, time_bucket DESC
| LIMIT 50''',
            'query_type': 'scripted',
            'pain_point': 'Rogue network attempts and SS7 security attacks threatening network security and subscriber privacy'
        })

        # Query 6: Core Network Split-Brain and Signaling Storm Detection
        queries.append({
            'name': 'Core Network Split-Brain and Signaling Storm Detection',
            'description': 'Identify core network split-brain scenarios or signaling storms by detecting abnormal message rate spikes, elevated error rates, and SCTP retransmission patterns across MME pools, enriched with primary/backup status and datacenter location',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_signaling_storm',
                'description': 'Detects core network split-brain and signaling storms by analyzing message rates and error patterns. Identifies network partitioning and overload conditions across MME pools.',
                'tags': ['signaling', 'network', 'performance', 'availability', 'esql']
            },
            'query': '''FROM signaling_link_metrics
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    avg_msg_rate = AVG(messages_per_second),
    max_msg_rate = MAX(messages_per_second),
    avg_error_rate = AVG(error_rate),
    max_error_rate = MAX(error_rate),
    total_retrans = SUM(sctp_retransmissions),
    avg_cpu = AVG(cpu_utilization),
    max_cpu = MAX(cpu_utilization),
    link_down_count = SUM(CASE(link_status == "Down", 1, 0)),
    link_degraded_count = SUM(CASE(link_status == "Degraded", 1, 0))
  BY time_bucket, mme_host, link_type
| WHERE max_msg_rate > 550 OR max_error_rate > 0.05 OR total_retrans > 20 OR link_down_count > 0
| LOOKUP JOIN mme_host_reference ON mme_host
| EVAL 
    anomaly_score = (max_msg_rate / 100.0) + (max_error_rate * 1000) + (total_retrans * 5) + (link_down_count * 50),
    alert_level = CASE(
        link_down_count > 0 OR max_error_rate > 0.1, "CRITICAL",
        max_msg_rate > 560 OR total_retrans > 30, "HIGH",
        "MEDIUM"
    )
| KEEP time_bucket, mme_host, mme_pool, datacenter, primary_backup, software_version, link_type, avg_msg_rate, max_msg_rate, avg_error_rate, max_error_rate, total_retrans, avg_cpu, max_cpu, link_down_count, link_degraded_count, anomaly_score, alert_level
| SORT anomaly_score DESC, time_bucket DESC
| LIMIT 50''',
            'query_type': 'scripted',
            'pain_point': 'Core network split-brain and signaling storms causing service downtime and SLA violations'
        })

        # Query 7: Procedure Failure Root Cause Analysis
        queries.append({
            'name': 'Procedure Failure Root Cause Analysis with Cause Code Enrichment',
            'description': 'Perform comprehensive procedure failure root cause analysis by aggregating failures per cause code, enriched with human-readable cause descriptions, severity levels, and recommended actions, correlated with cell tower geography',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_root_cause_analysis',
                'description': 'Performs root cause analysis of procedure failures with actionable recommendations. Enriches failures with cause descriptions, severity, and geographic context for rapid remediation.',
                'tags': ['failures', 'troubleshooting', 'analytics', 'remediation', 'esql']
            },
            'query': '''FROM lte_s1ap_events
| WHERE procedure_result == "Failure"
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    unique_cells = COUNT_DISTINCT(cell_id)
  BY time_bucket, procedure_type, cause_code, cause_group, mme_host
| WHERE failure_count >= 50
| LOOKUP JOIN cause_code_reference ON cause_code
| EVAL 
    failure_rate = TO_DOUBLE(failure_count) / 5.0,
    impact_score = failure_count * unique_cells
| KEEP time_bucket, procedure_type, cause_code, cause_group, cause_description, severity, recommended_action, category, mme_host, failure_count, unique_imsi, unique_cells, failure_rate, impact_score
| SORT impact_score DESC, severity ASC, time_bucket DESC
| LIMIT 100''',
            'query_type': 'scripted',
            'pain_point': 'Service downtime leading to revenue loss and SLA violations requiring rapid root cause identification'
        })

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries that accept user input"""
        queries = []

        # Query 1: Time-Range HSS Authentication Failure Analysis
        queries.append({
            'name': 'HSS Authentication Failure Analysis by Time Range',
            'description': 'Analyze HSS authentication failures within a specific time range, filtered by HSS cluster and minimum failure threshold for targeted troubleshooting',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_hss_auth_timerange',
                'description': 'Analyzes HSS authentication failures for a specific time period and cluster. Helps troubleshoot database synchronization issues and authentication problems with customizable thresholds.',
                'tags': ['authentication', 'hss', 'parameterized', 'troubleshooting', 'esql']
            },
            'query': '''FROM hss_authentication_events
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE auth_result != "Success"
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    sync_failures = SUM(CASE(sync_failure == true, 1, 0)),
    sqn_failures = SUM(CASE(sqn_failure == true, 1, 0)),
    avg_response_time = AVG(response_time_ms)
  BY time_bucket, hss_node, auth_result, diameter_result_code
| WHERE failure_count >= ?min_failure_threshold
| LOOKUP JOIN hss_node_reference ON hss_node
| WHERE hss_cluster == ?hss_cluster
| EVAL 
    failure_rate_per_min = TO_DOUBLE(failure_count) / 5.0,
    sync_failure_pct = TO_DOUBLE(sync_failures) * 100.0 / failure_count
| KEEP time_bucket, hss_node, hss_cluster, datacenter, database_type, replication_mode, auth_result, diameter_result_code, failure_count, unique_imsi, sync_failures, sqn_failures, sync_failure_pct, failure_rate_per_min, avg_response_time
| SORT failure_count DESC, time_bucket DESC
| LIMIT 100''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'date',
                    'description': 'Start of analysis time range',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'date',
                    'description': 'End of analysis time range',
                    'required': True
                },
                {
                    'name': 'hss_cluster',
                    'type': 'keyword',
                    'description': 'HSS cluster to analyze (e.g., HSS_Cluster_1)',
                    'required': True
                },
                {
                    'name': 'min_failure_threshold',
                    'type': 'integer',
                    'description': 'Minimum failure count per 5-minute interval',
                    'required': True,
                    'default': 200
                }
            ],
            'pain_point': 'HSS database corruption or synchronization issues requiring focused analysis by cluster and time period'
        })

        # Query 2: Regional Handover Failure Analysis
        queries.append({
            'name': 'Regional Cell Tower Handover Failure Analysis',
            'description': 'Analyze handover failures for a specific region and market segment to identify coverage gaps and radio equipment issues',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_regional_handover',
                'description': 'Analyzes handover failures by region and market segment. Identifies coverage gaps and radio equipment failures affecting specific geographic areas and subscriber populations.',
                'tags': ['handover', 'regional', 'coverage', 'parameterized', 'esql']
            },
            'query': '''FROM lte_s1ap_events
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE procedure_type == "Handover" AND handover_result == "Failure"
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    unique_cells = COUNT_DISTINCT(cell_id)
  BY time_bucket, cell_id, cause_group, cause_code
| LOOKUP JOIN cell_tower_reference ON cell_id
| WHERE region == ?region AND market == ?market
| EVAL 
    failure_rate = TO_DOUBLE(failure_count) / 5.0,
    impact_score = failure_count * unique_cells
| KEEP time_bucket, cell_id, cell_name, site_id, region, market, technology, frequency_band, neighbor_cells, cause_group, cause_code, failure_count, unique_imsi, unique_cells, failure_rate, impact_score
| SORT impact_score DESC, time_bucket DESC
| LIMIT 100''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'date',
                    'description': 'Start of analysis time range',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'date',
                    'description': 'End of analysis time range',
                    'required': True
                },
                {
                    'name': 'region',
                    'type': 'keyword',
                    'description': 'Geographic region (e.g., Northeast, Pacific)',
                    'required': True
                },
                {
                    'name': 'market',
                    'type': 'keyword',
                    'description': 'Market segment (e.g., Urban, Suburban, Rural)',
                    'required': True
                }
            ],
            'pain_point': 'Radio equipment failure and cell tower handoff failures requiring regional analysis for targeted remediation'
        })

        # Query 3: MME Performance Analysis by Software Version
        queries.append({
            'name': 'MME Performance Analysis by Software Version',
            'description': 'Compare service request failure rates across MME software versions to identify software bugs and guide upgrade decisions',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_mme_version_analysis',
                'description': 'Compares MME performance across software versions. Identifies software bugs and helps prioritize MME upgrades by analyzing failure patterns and impact.',
                'tags': ['mme', 'software', 'performance', 'parameterized', 'esql']
            },
            'query': '''FROM lte_s1ap_events
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE procedure_type == ?procedure_type
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    total_count = COUNT(*),
    failure_count = SUM(CASE(procedure_result == "Failure", 1, 0)),
    unique_imsi = COUNT_DISTINCT(imsi)
  BY time_bucket, mme_host
| LOOKUP JOIN mme_host_reference ON mme_host
| WHERE software_version == ?software_version
| EVAL 
    failure_rate = TO_DOUBLE(failure_count) * 100.0 / total_count,
    failures_per_min = TO_DOUBLE(failure_count) / 5.0
| KEEP time_bucket, mme_host, mme_pool, datacenter, software_version, capacity_tier, max_subscribers, total_count, failure_count, unique_imsi, failure_rate, failures_per_min
| SORT failure_rate DESC, time_bucket DESC
| LIMIT 100''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'date',
                    'description': 'Start of analysis time range',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'date',
                    'description': 'End of analysis time range',
                    'required': True
                },
                {
                    'name': 'software_version',
                    'type': 'keyword',
                    'description': 'MME software version (e.g., v5.2.3, v5.3.0)',
                    'required': True
                },
                {
                    'name': 'procedure_type',
                    'type': 'keyword',
                    'description': 'Procedure type to analyze (e.g., Service Request, Initial Attach)',
                    'required': True
                }
            ],
            'pain_point': 'MME software bugs requiring version-specific analysis for upgrade planning'
        })

        # Query 4: SS7 Threat Analysis by Originating Network
        queries.append({
            'name': 'SS7 Security Threat Analysis by Originating Network',
            'description': 'Analyze SS7 security threats from specific originating networks to identify malicious actors and configure appropriate blocking rules',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_ss7_network_threats',
                'description': 'Analyzes SS7 threats by originating network and threat category. Identifies malicious actors and provides threat intelligence for security rule configuration.',
                'tags': ['security', 'ss7', 'threats', 'parameterized', 'esql']
            },
            'query': '''FROM ss7_security_events
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE threat_level == ?threat_level
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    event_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    blocked_count = SUM(CASE(blocked == true, 1, 0)),
    unique_signatures = COUNT_DISTINCT(attack_signature)
  BY time_bucket, originating_network, attack_signature, message_type
| WHERE event_count >= ?min_event_threshold
| LOOKUP JOIN threat_signature_reference ON attack_signature
| WHERE threat_category == ?threat_category
| EVAL 
    block_rate = TO_DOUBLE(blocked_count) * 100.0 / event_count,
    events_per_min = TO_DOUBLE(event_count) / 5.0
| KEEP time_bucket, originating_network, attack_signature, threat_name, threat_category, threat_level, threat_description, mitigation_strategy, message_type, event_count, unique_imsi, blocked_count, block_rate, events_per_min
| SORT event_count DESC, time_bucket DESC
| LIMIT 100''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'date',
                    'description': 'Start of analysis time range',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'date',
                    'description': 'End of analysis time range',
                    'required': True
                },
                {
                    'name': 'threat_level',
                    'type': 'keyword',
                    'description': 'Threat level (Critical, High, Medium, Low)',
                    'required': True
                },
                {
                    'name': 'threat_category',
                    'type': 'keyword',
                    'description': 'Threat category (e.g., DoS Attack, Location Tracking, Fraud)',
                    'required': True
                },
                {
                    'name': 'min_event_threshold',
                    'type': 'integer',
                    'description': 'Minimum event count per 5-minute interval',
                    'required': True,
                    'default': 10
                }
            ],
            'pain_point': 'SS7 security attacks requiring network-specific analysis for threat mitigation'
        })

        # Query 5: Cause Code Analysis for Specific Procedure Types
        queries.append({
            'name': 'Procedure Failure Cause Code Analysis',
            'description': 'Deep dive into specific procedure failure causes with actionable remediation guidance filtered by severity and category',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_cause_code_analysis',
                'description': 'Analyzes procedure failures by cause code with actionable remediation steps. Filters by severity and category to prioritize critical issues requiring immediate attention.',
                'tags': ['failures', 'cause_codes', 'remediation', 'parameterized', 'esql']
            },
            'query': '''FROM lte_s1ap_events
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE procedure_type == ?procedure_type AND procedure_result == "Failure"
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    unique_cells = COUNT_DISTINCT(cell_id),
    unique_mme = COUNT_DISTINCT(mme_host)
  BY time_bucket, cause_code, cause_group
| LOOKUP JOIN cause_code_reference ON cause_code
| WHERE severity == ?severity
| EVAL 
    failure_rate = TO_DOUBLE(failure_count) / 5.0,
    impact_score = failure_count * unique_cells
| KEEP time_bucket, cause_code, cause_group, cause_description, severity, recommended_action, category, failure_count, unique_imsi, unique_cells, unique_mme, failure_rate, impact_score
| SORT impact_score DESC, time_bucket DESC
| LIMIT 100''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'date',
                    'description': 'Start of analysis time range',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'date',
                    'description': 'End of analysis time range',
                    'required': True
                },
                {
                    'name': 'procedure_type',
                    'type': 'keyword',
                    'description': 'Procedure type (e.g., Handover, Service Request, Initial Attach)',
                    'required': True
                },
                {
                    'name': 'severity',
                    'type': 'keyword',
                    'description': 'Failure severity level (Critical, Major, Minor, Warning)',
                    'required': True
                }
            ],
            'pain_point': 'Service downtime requiring targeted root cause analysis by procedure type and severity'
        })

        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using COMPLETION command"""
        queries = []

        # RAG Query 1: LTE S1AP Event Analysis
        queries.append({
            'name': 'LTE S1AP Event Semantic Search and Analysis',
            'description': 'Search LTE S1AP event details using natural language queries to understand network behavior, procedure outcomes, and failure patterns with AI-generated insights',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_s1ap_semantic_search',
                'description': 'Searches LTE S1AP events using natural language. Provides AI-powered insights about network procedures, failures, and subscriber impacts for rapid troubleshooting.',
                'tags': ['rag', 'semantic', 'lte', 's1ap', 'esql']
            },
            'query': '''FROM lte_s1ap_events METADATA _id
| WHERE MATCH(event_details, ?user_question, {"fuzziness": "AUTO"})
| KEEP @timestamp, event_id, imsi, cell_id, mme_host, procedure_type, procedure_result, handover_result, service_request_result, cause_group, cause_code, ue_emm_state, event_details, _score
| SORT _score DESC
| LIMIT 5
| EVAL prompt = CONCAT("Based on these LTE S1AP network events, answer this question: ", ?user_question, "\n\nContext from events:\n", event_details)
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP @timestamp, event_id, imsi, procedure_type, procedure_result, cause_code, event_details, answer, _score''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Natural language question about LTE network events',
                    'required': True
                }
            ],
            'pain_point': 'Need to quickly understand complex network event patterns and failure scenarios using natural language queries'
        })

        # RAG Query 2: HSS Authentication Error Analysis
        queries.append({
            'name': 'HSS Authentication Error Semantic Analysis',
            'description': 'Search HSS authentication error messages using natural language to understand database issues, synchronization failures, and subscriber authentication problems with AI-powered explanations',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_hss_error_semantic',
                'description': 'Searches HSS authentication errors using natural language. Provides AI-generated explanations of database issues, sync failures, and remediation guidance.',
                'tags': ['rag', 'semantic', 'hss', 'authentication', 'esql']
            },
            'query': '''FROM hss_authentication_events METADATA _id
| WHERE MATCH(error_message, ?user_question, {"fuzziness": "AUTO"})
| KEEP @timestamp, event_id, imsi, mme_host, auth_result, auth_type, hss_node, diameter_result_code, sync_failure, sqn_failure, response_time_ms, roaming_status, error_message, _score
| SORT _score DESC
| LIMIT 5
| EVAL prompt = CONCAT("Based on these HSS authentication errors, answer this question: ", ?user_question, "\n\nContext from errors:\n", error_message)
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP @timestamp, event_id, imsi, auth_result, hss_node, diameter_result_code, error_message, answer, _score''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Natural language question about HSS authentication errors',
                    'required': True
                }
            ],
            'pain_point': 'HSS database errors requiring rapid understanding of authentication failures and synchronization issues'
        })

        # RAG Query 3: SS7 Security Event Analysis
        queries.append({
            'name': 'SS7 Security Event Semantic Analysis',
            'description': 'Search SS7 security event descriptions using natural language to understand attack patterns, threat vectors, and security incidents with AI-generated threat intelligence',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_ss7_threat_semantic',
                'description': 'Searches SS7 security events using natural language. Provides AI-powered threat analysis, attack pattern insights, and security recommendations.',
                'tags': ['rag', 'semantic', 'ss7', 'security', 'esql']
            },
            'query': '''FROM ss7_security_events METADATA _id
| WHERE MATCH(event_description, ?user_question, {"fuzziness": "AUTO"})
| KEEP @timestamp, event_id, imsi, source_gt, destination_gt, message_type, attack_signature, threat_level, blocked, originating_network, map_operation, event_description, _score
| SORT _score DESC
| LIMIT 5
| EVAL prompt = CONCAT("Based on these SS7 security events, answer this question: ", ?user_question, "\n\nContext from security events:\n", event_description)
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP @timestamp, event_id, imsi, attack_signature, threat_level, originating_network, event_description, answer, _score''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Natural language question about SS7 security threats',
                    'required': True
                }
            ],
            'pain_point': 'SS7 security attacks requiring rapid threat intelligence and pattern recognition'
        })

        # RAG Query 4: Cause Code Remediation Guidance
        queries.append({
            'name': 'Cause Code Remediation Semantic Search',
            'description': 'Search cause code descriptions and recommended actions using natural language to find remediation guidance for network failures',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_cause_remediation',
                'description': 'Searches cause codes and remediation actions using natural language. Provides AI-powered troubleshooting guidance and recommended fixes for network failures.',
                'tags': ['rag', 'semantic', 'remediation', 'troubleshooting', 'esql']
            },
            'query': '''FROM cause_code_reference METADATA _id
| WHERE MATCH(cause_description, ?user_question, {"fuzziness": "AUTO"}) OR MATCH(recommended_action, ?user_question, {"fuzziness": "AUTO"})
| KEEP cause_code, cause_group, cause_description, severity, recommended_action, category, _score
| SORT _score DESC
| LIMIT 5
| EVAL prompt = CONCAT("Based on these cause codes and remediation actions, answer this question: ", ?user_question, "\n\nCause: ", cause_description, "\nRecommended Action: ", recommended_action)
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP cause_code, cause_group, severity, category, cause_description, recommended_action, answer, _score''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Natural language question about failure causes and remediation',
                    'required': True
                }
            ],
            'pain_point': 'Need rapid access to remediation guidance for network failures using natural language'
        })

        # RAG Query 5: Threat Intelligence Semantic Search
        queries.append({
            'name': 'SS7 Threat Intelligence Semantic Search',
            'description': 'Search threat descriptions and mitigation strategies using natural language to understand security vulnerabilities and protection mechanisms',
            'tool_metadata': {
                'tool_id': 't_mobile_network_op_threat_intelligence',
                'description': 'Searches threat intelligence using natural language. Provides AI-powered security insights, vulnerability analysis, and mitigation strategies for SS7 threats.',
                'tags': ['rag', 'semantic', 'threats', 'intelligence', 'esql']
            },
            'query': '''FROM threat_signature_reference METADATA _id
| WHERE MATCH(threat_description, ?user_question, {"fuzziness": "AUTO"}) OR MATCH(mitigation_strategy, ?user_question, {"fuzziness": "AUTO"})
| KEEP attack_signature, threat_name, threat_category, threat_description, mitigation_strategy, cve_references, _score
| SORT _score DESC
| LIMIT 5
| EVAL prompt = CONCAT("Based on this threat intelligence, answer this question: ", ?user_question, "\n\nThreat: ", threat_description, "\nMitigation: ", mitigation_strategy)
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP attack_signature, threat_name, threat_category, threat_description, mitigation_strategy, cve_references, answer, _score''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Natural language question about security threats and mitigation',
                    'required': True
                }
            ],
            'pain_point': 'Need rapid access to threat intelligence and mitigation strategies using natural language'
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum impact"""
        return [
            # Start with high-impact detection queries
            'IMSI and Cell ID Spike Detection with Multi-Lag Analysis',
            'HSS Mass Authentication Failure Detection',
            'Core Network Split-Brain and Signaling Storm Detection',
            
            # Follow with specific failure analysis
            'Cell Tower Handoff Cascade Failure Analysis',
            'MME Resource Exhaustion and Software Bug Detection',
            
            # Security and threat detection
            'SS7 Security Attack and Roaming Misconfiguration Detection',
            
            # Root cause analysis
            'Procedure Failure Root Cause Analysis with Cause Code Enrichment',
            
            # Parameterized queries for targeted analysis
            'HSS Authentication Failure Analysis by Time Range',
            'Regional Cell Tower Handover Failure Analysis',
            'MME Performance Analysis by Software Version',
            'SS7 Security Threat Analysis by Originating Network',
            'Procedure Failure Cause Code Analysis',
            
            # RAG queries for semantic search
            'LTE S1AP Event Semantic Search and Analysis',
            'HSS Authentication Error Semantic Analysis',
            'SS7 Security Event Semantic Analysis',
            'Cause Code Remediation Semantic Search',
            'SS7 Threat Intelligence Semantic Search'
        ]
