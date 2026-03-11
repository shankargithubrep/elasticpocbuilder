
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any


class TelcoQueryGenerator(QueryGeneratorModule):
    """Query generator for Telco - Network Operations"""

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate SCRIPTED ES|QL queries with hardcoded values (no user parameters)"""
        queries = []

        # Query 1: Data Session Interruption Trending Over Time
        queries.append({
            'name': 'Data Session Interruption Trending Over Time',
            'description': (
                'Analyzes data session logs to identify and trend interrupted sessions over hourly '
                'time buckets. Filters for sessions with INTERRUPTED or FAILED status, then groups '
                'counts by hour and RAT type to reveal degradation patterns across 4G/5G/3G. '
                'Network operations teams can spot rising failure trends and correlate them with '
                'network events or infrastructure changes before they escalate.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_session_interruption_trend',
                'description': (
                    'Tracks rising frequency of interrupted data sessions by RAT type and hour. '
                    'Identifies degradation patterns early across 4G/5G/3G networks to enable '
                    'proactive intervention before widespread outages.'
                ),
                'tags': ['data_sessions', 'interruptions', 'trending', 'rat_type', 'esql']
            },
            'query': '''FROM data_session_logs
| WHERE session_status IN ("INTERRUPTED", "FAILED")
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| EVAL session_duration_sec = TO_DOUBLE(session_duration_seconds)
| EVAL is_short_session = CASE(session_duration_sec < 30, 1, 0)
| STATS
    interrupted_session_count = COUNT(session_id),
    affected_subscribers = COUNT_DISTINCT(subscriber_id),
    affected_cells = COUNT_DISTINCT(cell_id),
    short_session_count = SUM(is_short_session),
    avg_session_duration_sec = ROUND(AVG(session_duration_sec), 2)
  BY time_bucket, rat_type
| EVAL short_session_pct = ROUND(TO_DOUBLE(short_session_count) * 100.0 / TO_DOUBLE(interrupted_session_count), 1)
| SORT time_bucket DESC, interrupted_session_count DESC''',
            'query_type': 'scripted',
            'pain_point': 'Dropped calls during mobility and interrupted data sessions',
            'datasets': ['data_session_logs']
        })

        # Query 2: Dropped Call Rate by Cell Tower and Mobility Zone
        queries.append({
            'name': 'Dropped Call Rate by Cell Tower and Mobility Zone',
            'description': (
                'Analyzes call detail records to detect anomalous dropped call rates at the cell '
                'tower level, segmented by mobility zone. Aggregates dropped call counts and total '
                'call attempts per tower per 15-minute time bucket, computes a per-tower dropped '
                'call rate, and uses INLINESTATS to derive mean and standard deviation. A Z-score '
                'flags towers exhibiting statistically significant spikes. LOOKUP JOIN enriches '
                'each tower record with its mobility zone classification, handoff zone type, and '
                'geographic region.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_dropped_call_tower_analysis',
                'description': (
                    'Identifies abnormal dropped call spikes during handoff events across mobility '
                    'zones using Z-score anomaly detection. Enriches cell tower data with geographic '
                    'and zone metadata to pinpoint high-risk handoff corridors.'
                ),
                'tags': ['dropped_calls', 'cell_tower', 'mobility', 'anomaly_detection', 'esql']
            },
            'query': '''FROM call_detail_records
| WHERE handoff_event IN ("INTER-RAT", "INTER-FREQ", "INTRA-FREQ")
| EVAL time_bucket = DATE_TRUNC(15 minutes, @timestamp)
| EVAL dropped_flag = CASE(call_dropped == "true", 1, 0)
| STATS
    total_dropped = SUM(dropped_flag),
    total_attempts = COUNT(*),
    avg_signal_dbm = AVG(TO_DOUBLE(signal_strength_dbm))
  BY time_bucket, cell_tower_id
| EVAL dropped_call_rate = TO_DOUBLE(total_dropped) / TO_DOUBLE(COALESCE(total_attempts, 1))
| INLINESTATS
    avg_dropped_rate = AVG(dropped_call_rate),
    stddev_dropped_rate = STD_DEV(dropped_call_rate)
  BY cell_tower_id
| EVAL z_score = (dropped_call_rate - avg_dropped_rate) / COALESCE(stddev_dropped_rate, 1.0)
| WHERE z_score > 3 OR z_score < -3
| LOOKUP JOIN cell_tower_reference ON cell_tower_id
| KEEP
    time_bucket,
    cell_tower_id,
    mobility_zone,
    handoff_zone_type,
    geographic_region,
    tower_vendor,
    latitude,
    longitude,
    total_dropped,
    total_attempts,
    dropped_call_rate,
    avg_dropped_rate,
    stddev_dropped_rate,
    z_score,
    avg_signal_dbm
| SORT z_score DESC, time_bucket ASC''',
            'query_type': 'scripted',
            'pain_point': 'Dropped calls during mobility and interrupted data sessions',
            'datasets': ['call_detail_records', 'cell_tower_reference']
        })

        # Query 3: Core Network Split-Brain Event Detection
        queries.append({
            'name': 'Core Network Split-Brain Event Detection',
            'description': (
                'Detects split-brain conditions across core network nodes by filtering for '
                'SPLIT-BRAIN event types and partitioned consensus states. Surfaces the most '
                'critical split-brain events first, enabling NOC engineers to rapidly triage '
                'active incidents where nodes lose consensus and operate independently, causing '
                'routing inconsistencies and service degradation.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_split_brain_detection',
                'description': (
                    'Detects core network split-brain conditions where nodes lose consensus. '
                    'Surfaces critical partitioned-state events by severity for rapid NOC triage '
                    'before routing inconsistencies cascade into service outages.'
                ),
                'tags': ['split_brain', 'core_network', 'consensus', 'severity', 'esql']
            },
            'query': '''FROM core_network_events
| WHERE event_type == "SPLIT-BRAIN" OR consensus_state IN ("SPLIT", "CANDIDATE")
| EVAL relevance_score = TO_DOUBLE(score)
| KEEP
    event_id,
    event_title,
    event_description,
    alert_message,
    node_id,
    node_role,
    cluster_id,
    network_region,
    severity,
    consensus_state,
    affected_peers,
    @timestamp,
    relevance_score
| SORT relevance_score DESC, @timestamp DESC
| LIMIT 25''',
            'query_type': 'scripted',
            'pain_point': 'Core network split-brain and signaling storms',
            'datasets': ['core_network_events']
        })

        # Query 4: MME Resource Exhaustion and Error Surge Detection
        queries.append({
            'name': 'MME Resource Exhaustion and Error Surge Detection',
            'description': (
                'Analyzes MME system logs to detect resource exhaustion anomalies by computing '
                'per-node CPU and memory utilization statistics across 5-minute time buckets. '
                'Applies Z-score based anomaly detection using INLINESTATS to identify nodes '
                'with statistically significant spikes. A LOOKUP JOIN enriches each anomalous '
                'event with known software bug signatures, enabling teams to correlate exhaustion '
                'events with known defects, patch levels, or firmware issues.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_mme_resource_exhaustion',
                'description': (
                    'Detects MME memory and CPU exhaustion events using Z-score anomaly detection. '
                    'Correlates resource spikes with known software bug signatures to prioritize '
                    'patching and prevent signaling failures.'
                ),
                'tags': ['mme', 'resource_exhaustion', 'anomaly_detection', 'bug_correlation', 'esql']
            },
            'query': '''FROM mme_system_logs
| WHERE log_severity IN ("ERROR", "CRITICAL", "WARNING")
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| EVAL cpu_val = TO_DOUBLE(cpu_utilization_pct)
| EVAL mem_val = TO_DOUBLE(memory_utilization_pct)
| EVAL ue_val = TO_DOUBLE(active_ue_sessions)
| EVAL attach_fail_val = TO_DOUBLE(attach_failure_rate)
| STATS
    avg_cpu = AVG(cpu_val),
    avg_memory = AVG(mem_val),
    total_s1ap_errors = SUM(s1ap_error_count),
    total_nas_errors = SUM(nas_signaling_error_count),
    total_attach_failures = SUM(attach_fail_val),
    avg_ue_sessions = AVG(ue_val),
    event_count = COUNT()
  BY time_bucket, mme_node_id, mme_pool_id, software_version
| INLINESTATS
    baseline_cpu = AVG(avg_cpu),
    stddev_cpu = STD_DEV(avg_cpu),
    baseline_memory = AVG(avg_memory),
    stddev_memory = STD_DEV(avg_memory),
    baseline_s1ap_errors = AVG(total_s1ap_errors),
    stddev_s1ap_errors = STD_DEV(total_s1ap_errors)
  BY mme_node_id
| EVAL
    cpu_z_score = ROUND((avg_cpu - baseline_cpu) / COALESCE(stddev_cpu, 1.0), 2),
    memory_z_score = ROUND((avg_memory - baseline_memory) / COALESCE(stddev_memory, 1.0), 2),
    s1ap_error_z_score = ROUND((TO_DOUBLE(total_s1ap_errors) - baseline_s1ap_errors) / COALESCE(stddev_s1ap_errors, 1.0), 2)
| EVAL
    cpu_exhaustion_flag = CASE(avg_cpu >= 90, "CRITICAL", avg_cpu >= 75, "WARNING", "NORMAL"),
    memory_exhaustion_flag = CASE(avg_memory >= 90, "CRITICAL", avg_memory >= 75, "WARNING", "NORMAL")
| EVAL anomaly_score = ROUND((cpu_z_score + memory_z_score + s1ap_error_z_score) / 3.0, 2)
| WHERE cpu_z_score > 3 OR memory_z_score > 3 OR s1ap_error_z_score > 3
| LOOKUP JOIN mme_bug_signature_lookup ON software_version
| EVAL bug_correlated = CASE(bug_id IS NOT NULL, "YES", "NO")
| EVAL remediation_priority = CASE(
    patch_available == "YES" AND severity_rating == "CRITICAL", "IMMEDIATE",
    patch_available == "YES" AND severity_rating == "HIGH", "HIGH",
    patch_available == "NO" AND anomaly_score > 5, "ESCALATE",
    "MONITOR"
  )
| KEEP
    time_bucket,
    mme_node_id,
    mme_pool_id,
    software_version,
    avg_cpu,
    avg_memory,
    cpu_z_score,
    memory_z_score,
    s1ap_error_z_score,
    anomaly_score,
    cpu_exhaustion_flag,
    memory_exhaustion_flag,
    total_s1ap_errors,
    total_nas_errors,
    total_attach_failures,
    avg_ue_sessions,
    event_count,
    bug_id,
    bug_description,
    affected_component,
    patch_available,
    severity_rating,
    bug_correlated,
    remediation_priority
| SORT anomaly_score DESC, time_bucket DESC''',
            'query_type': 'scripted',
            'pain_point': 'MME software bugs and resource exhaustion',
            'datasets': ['mme_system_logs', 'mme_bug_signature_lookup']
        })

        # Query 5: Signaling Storm Detection Across Network Elements
        queries.append({
            'name': 'Signaling Storm Detection Across Network Elements',
            'description': (
                'Detects signaling storm conditions across core network elements by analyzing '
                'message volume per network node over rolling 1-minute time buckets. Aggregates '
                'signaling message counts by network element and protocol type, then applies '
                'Z-score statistical analysis using INLINESTATS to identify nodes experiencing '
                'abnormal burst activity. LOOKUP JOIN enriches each element with classification, '
                'region, and capacity thresholds. Nodes with Z-scores exceeding 3 standard '
                'deviations are flagged as storm candidates.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_signaling_storm_detection',
                'description': (
                    'Identifies abnormal signaling message volume bursts indicating storm conditions '
                    'in the core network. Uses Z-score analysis and capacity threshold checks to '
                    'flag at-risk nodes before cascading failures propagate.'
                ),
                'tags': ['signaling_storm', 'core_network', 'anomaly_detection', 'capacity', 'esql']
            },
            'query': '''FROM signaling_logs
| EVAL time_bucket = DATE_TRUNC(1 minute, @timestamp)
| STATS
    message_count = COUNT(*),
    unique_sources = COUNT_DISTINCT(source_node),
    unique_destinations = COUNT_DISTINCT(destination_node)
  BY time_bucket, network_element_id, signaling_protocol
| INLINESTATS
    avg_message_count = AVG(message_count),
    stddev_message_count = STD_DEV(message_count)
  BY network_element_id, signaling_protocol
| EVAL z_score = (TO_DOUBLE(message_count) - avg_message_count) / COALESCE(stddev_message_count, 1.0)
| EVAL burst_ratio = TO_DOUBLE(message_count) / COALESCE(avg_message_count, 1.0)
| WHERE z_score > 3
| LOOKUP JOIN network_element_registry ON network_element_id
| EVAL storm_severity = CASE(
    z_score >= 6, "CRITICAL",
    z_score >= 4.5, "HIGH",
    z_score >= 3, "MODERATE",
    "LOW"
  )
| EVAL capacity_breach = CASE(
    message_count > TO_LONG(capacity_threshold_msg_per_min), true,
    false
  )
| KEEP
    time_bucket,
    network_element_id,
    element_name,
    element_type,
    region,
    vendor,
    criticality_tier,
    signaling_protocol,
    message_count,
    avg_message_count,
    stddev_message_count,
    z_score,
    burst_ratio,
    unique_sources,
    unique_destinations,
    storm_severity,
    capacity_threshold_msg_per_min,
    capacity_breach
| SORT z_score DESC, time_bucket ASC''',
            'query_type': 'scripted',
            'pain_point': 'Core network split-brain and signaling storms',
            'datasets': ['signaling_logs', 'network_element_registry']
        })

        # Query 6: Handover Failure Analytics by RAN and Region
        queries.append({
            'name': 'Handover Failure Analytics by RAN and Region',
            'description': (
                'Analyzes handover failure rates across radio access nodes and geographic regions '
                'to identify mobility bottlenecks. Calculates total handover attempts, failures, '
                'and success rates per node and region, then enriches each node with site metadata '
                'via LOOKUP JOIN against the RAN site reference table. Results highlight nodes and '
                'regions with the highest failure rates, enabling teams to prioritize corrective '
                'actions such as neighbor list optimization or parameter tuning.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_handover_failure_analytics',
                'description': (
                    'Analyzes handover failure rates by radio access node and geographic region. '
                    'Identifies mobility bottlenecks and ranks regions by failure severity to '
                    'prioritize network optimization actions.'
                ),
                'tags': ['handover', 'ran', 'mobility', 'failure_rate', 'esql']
            },
            'query': '''FROM ran_performance_metrics
| WHERE TO_LONG(handover_attempts) > 0
| STATS
    total_handover_attempts = SUM(TO_LONG(handover_attempts)),
    total_handover_failures = SUM(TO_LONG(handover_failures)),
    avg_ue_count = AVG(TO_DOUBLE(ue_count)),
    sample_count = COUNT(*)
  BY ran_node_id, handover_type, source_rat, target_rat
| EVAL handover_failure_rate = ROUND(
    TO_DOUBLE(total_handover_failures) * 100.0 / TO_DOUBLE(COALESCE(total_handover_attempts, 1)),
    2
  )
| EVAL handover_success_rate = ROUND(100.0 - handover_failure_rate, 2)
| LOOKUP JOIN ran_site_reference ON ran_node_id
| STATS
    region_total_attempts = SUM(total_handover_attempts),
    region_total_failures = SUM(total_handover_failures),
    node_count = COUNT_DISTINCT(ran_node_id),
    avg_failure_rate = ROUND(AVG(handover_failure_rate), 2),
    max_failure_rate = MAX(handover_failure_rate),
    avg_ue_count = AVG(avg_ue_count)
  BY region, sub_region, handover_type, source_rat, target_rat, vendor, technology_generation
| EVAL region_failure_rate = ROUND(
    TO_DOUBLE(region_total_failures) * 100.0 / TO_DOUBLE(COALESCE(region_total_attempts, 1)),
    2
  )
| EVAL failure_severity = CASE(
    region_failure_rate >= 10, "CRITICAL",
    region_failure_rate >= 5,  "HIGH",
    region_failure_rate >= 2,  "MEDIUM",
    "LOW"
  )
| SORT region_failure_rate DESC, region_total_failures DESC''',
            'query_type': 'scripted',
            'pain_point': 'Radio equipment failure and cell tower handoff failures',
            'datasets': ['ran_performance_metrics', 'ran_site_reference']
        })

        # Query 7: MME Software Bug Enrichment and Impact Correlation
        queries.append({
            'name': 'MME Software Bug Enrichment and Impact Correlation',
            'description': (
                'Enriches MME fault and error events from system logs with known software bug '
                'signature reference data. LOOKUP JOIN annotates each fault event with bug ID, '
                'severity classification, affected software version, and recommended remediation '
                'status. Aggregates enriched events to surface which software defects cause the '
                'highest service impact, measured by affected subscriber counts and fault frequency. '
                'Enables teams to prioritize patching efforts and quantify the operational impact '
                'of unresolved bugs across the MME fleet.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_mme_bug_impact_correlation',
                'description': (
                    'Enriches MME fault events with known bug signatures to correlate software '
                    'defects with service impact. Ranks bugs by subscriber impact and patch '
                    'availability to drive prioritized remediation decisions.'
                ),
                'tags': ['mme', 'bug_correlation', 'software_defects', 'remediation', 'esql']
            },
            'query': '''FROM mme_system_logs
| WHERE log_level IN ("ERROR", "CRITICAL", "WARN")
| WHERE fault_code IS NOT NULL
| EVAL fault_hour = DATE_TRUNC(1 hour, @timestamp)
| EVAL is_critical_fault = CASE(
    fault_severity == "CRITICAL", true,
    fault_severity == "HIGH", true,
    false
  )
| EVAL has_core_dump = CASE(core_dump_generated == "true", true, false)
| LOOKUP JOIN mme_bug_signatures ON fault_code
| WHERE bug_id IS NOT NULL
| EVAL impact_score = CASE(
    bug_severity == "CRITICAL" AND patch_available == "NO", 5,
    bug_severity == "CRITICAL" AND patch_available == "YES", 4,
    bug_severity == "HIGH" AND patch_available == "NO", 3,
    bug_severity == "HIGH" AND patch_available == "YES", 2,
    1
  )
| EVAL remediation_status = CASE(
    patch_available == "YES", "Patch Available",
    workaround_available == "YES", "Workaround Available",
    "No Remediation"
  )
| STATS
    total_fault_events = COUNT(*),
    total_affected_subscribers = SUM(TO_LONG(affected_subscribers)),
    total_attach_failures = SUM(TO_LONG(attach_failures)),
    total_nas_failures = SUM(TO_LONG(nas_procedure_failures)),
    total_s1ap_errors = SUM(TO_LONG(s1ap_errors)),
    affected_nodes = COUNT_DISTINCT(mme_node_id),
    max_impact_score = MAX(impact_score),
    unique_software_versions = COUNT_DISTINCT(software_version)
  BY
    bug_id,
    bug_title,
    bug_category,
    bug_severity,
    fault_code,
    patch_available,
    patch_version,
    cve_reference,
    remediation_status
| EVAL subscriber_impact_per_node = ROUND(
    TO_DOUBLE(total_affected_subscribers) / TO_DOUBLE(COALESCE(affected_nodes, 1)),
    2
  )
| SORT max_impact_score DESC, total_affected_subscribers DESC
| LIMIT 50''',
            'query_type': 'scripted',
            'pain_point': 'MME software bugs and resource exhaustion',
            'datasets': ['mme_system_logs', 'mme_bug_signatures']
        })

        # Query 8: IMSI and Cell ID Cardinality Tracking
        queries.append({
            'name': 'IMSI and Cell ID Cardinality Changes Over Time',
            'description': (
                'Tracks unique subscriber (IMSI) and cell ID cardinality changes over hourly '
                'time buckets to detect abnormal shifts in network attachment patterns. Sudden '
                'drops in unique IMSIs can indicate HSS authentication failures or mass detach '
                'events, while spikes in cell ID cardinality may signal rogue cell activity or '
                'configuration errors. This query surfaces cardinality trends by RAT type to '
                'support proactive monitoring of 4G and 5G network health.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_imsi_cell_cardinality',
                'description': (
                    'Tracks unique IMSI and cell ID cardinality changes over time by RAT type. '
                    'Detects abnormal drops indicating HSS failures or mass detach events, and '
                    'spikes suggesting rogue cell activity or configuration issues.'
                ),
                'tags': ['imsi', 'cardinality', 'hss', 'monitoring', 'esql']
            },
            'query': '''FROM data_session_logs
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS
    unique_subscribers = COUNT_DISTINCT(subscriber_id),
    unique_cells = COUNT_DISTINCT(cell_id),
    total_sessions = COUNT(session_id),
    interrupted_sessions = SUM(CASE(session_status IN ("INTERRUPTED", "FAILED"), 1, 0)),
    auth_failures = SUM(CASE(termination_cause == "AUTH-FAILURE", 1, 0)),
    handover_failures = SUM(CASE(termination_cause == "HANDOVER-FAILURE", 1, 0))
  BY time_bucket, rat_type
| EVAL interruption_rate = ROUND(
    TO_DOUBLE(interrupted_sessions) * 100.0 / TO_DOUBLE(COALESCE(total_sessions, 1)),
    2
  )
| EVAL auth_failure_rate = ROUND(
    TO_DOUBLE(auth_failures) * 100.0 / TO_DOUBLE(COALESCE(total_sessions, 1)),
    2
  )
| SORT time_bucket DESC, unique_subscribers DESC''',
            'query_type': 'scripted',
            'pain_point': 'Need to detect network issues before help desk is overwhelmed',
            'datasets': ['data_session_logs']
        })

        # Query 9: HSS Authentication Failure Mass Event Detection
        queries.append({
            'name': 'Mass Authentication Failure Event Detection',
            'description': (
                'Detects mass authentication failure events that indicate HSS database corruption '
                'or synchronization issues. Analyzes core network events filtered to AUTH-FAILURE-BURST '
                'and HSS-SYNC-FAILURE event types, correlating with MME node data to identify the '
                'scope of subscriber authentication impact. Surfaces events by severity and affected '
                'peer count to enable rapid escalation and HSS health assessment.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_mass_auth_failure_detection',
                'description': (
                    'Detects mass authentication failure events indicating HSS issues. Correlates '
                    'AUTH-FAILURE-BURST and HSS-SYNC-FAILURE events with node and region data to '
                    'quantify subscriber impact and drive rapid HSS health response.'
                ),
                'tags': ['authentication', 'hss', 'mass_failure', 'subscriber', 'esql']
            },
            'query': '''FROM core_network_events
| WHERE event_type IN ("AUTH-FAILURE-BURST", "HSS-SYNC-FAILURE")
| EVAL affected_peer_count = TO_LONG(affected_peers)
| STATS
    total_events = COUNT(*),
    critical_events = SUM(CASE(severity == "CRITICAL", 1, 0)),
    high_events = SUM(CASE(severity == "HIGH", 1, 0)),
    affected_nodes = COUNT_DISTINCT(node_id),
    affected_clusters = COUNT_DISTINCT(cluster_id),
    max_affected_peers = MAX(affected_peer_count),
    avg_score = ROUND(AVG(TO_DOUBLE(score)), 2)
  BY network_region, event_type, node_role
| EVAL impact_level = CASE(
    critical_events > 0 AND max_affected_peers >= 3, "SEVERE",
    critical_events > 0, "HIGH",
    high_events > 0, "MEDIUM",
    "LOW"
  )
| SORT total_events DESC, critical_events DESC''',
            'query_type': 'scripted',
            'pain_point': 'HSS database corruption or synchronization issues affecting subscriber authentication',
            'datasets': ['core_network_events']
        })

        # Query 10: Security Attack and SS7 Threat Detection
        queries.append({
            'name': 'Security Attack and SS7 Threat Detection',
            'description': (
                'Identifies rogue network access attempts and SS7 security attacks by filtering '
                'core network events for SS7-ATTACK and ROGUE-ACCESS event types. Correlates '
                'signaling logs for SS7 protocol activity with AUTH-FAILURE cause codes to surface '
                'coordinated attack patterns. Results are ranked by event score and severity to '
                'enable rapid security response and isolation of compromised network elements.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_security_ss7_threat_detection',
                'description': (
                    'Identifies rogue network attempts and SS7 security attacks across core network '
                    'events. Surfaces coordinated attack patterns by severity and region to enable '
                    'rapid security response and element isolation.'
                ),
                'tags': ['security', 'ss7', 'rogue_access', 'threat_detection', 'esql']
            },
            'query': '''FROM core_network_events
| WHERE event_type IN ("SS7-ATTACK", "ROGUE-ACCESS")
| EVAL event_score = TO_DOUBLE(score)
| EVAL affected_peer_count = TO_LONG(affected_peers)
| STATS
    total_security_events = COUNT(*),
    critical_count = SUM(CASE(severity == "CRITICAL", 1, 0)),
    high_count = SUM(CASE(severity == "HIGH", 1, 0)),
    affected_nodes = COUNT_DISTINCT(node_id),
    affected_clusters = COUNT_DISTINCT(cluster_id),
    max_score = MAX(event_score),
    avg_score = ROUND(AVG(event_score), 2),
    max_affected_peers = MAX(affected_peer_count)
  BY network_region, event_type, node_role, severity
| EVAL threat_priority = CASE(
    severity == "CRITICAL" AND max_score > 80, "IMMEDIATE",
    severity == "CRITICAL", "HIGH",
    severity == "HIGH" AND max_score > 60, "HIGH",
    severity == "HIGH", "MEDIUM",
    "MONITOR"
  )
| SORT max_score DESC, critical_count DESC''',
            'query_type': 'scripted',
            'pain_point': 'Rogue network attempts and SS7 security attacks',
            'datasets': ['core_network_events']
        })

        # Query 11: Cell Tower Handoff Cascade Failure Detection
        queries.append({
            'name': 'Cell Tower Handoff Cascade Failure Detection',
            'description': (
                'Identifies cell tower handoff cascade failures by analyzing RAN performance '
                'metrics for nodes with extremely high handover failure rates across multiple '
                'handover types. Uses INLINESTATS to compute Z-score anomaly detection per '
                'source/target RAT combination, then enriches with RAN site reference data to '
                'identify geographic clusters of failure that indicate cascading mobility issues '
                'spreading across adjacent towers or coverage zones.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_handoff_cascade_detection',
                'description': (
                    'Detects cell tower handoff cascade failures using Z-score anomaly detection '
                    'across RAN nodes. Identifies geographic clusters of mobility failures that '
                    'indicate cascading issues spreading across adjacent towers.'
                ),
                'tags': ['handoff', 'cascade_failure', 'ran', 'mobility', 'esql']
            },
            'query': '''FROM ran_performance_metrics
| WHERE TO_LONG(handover_attempts) > 0
| EVAL attempt_val = TO_DOUBLE(handover_attempts)
| EVAL failure_val = TO_DOUBLE(handover_failures)
| EVAL node_failure_rate = failure_val * 100.0 / COALESCE(attempt_val, 1.0)
| STATS
    total_attempts = SUM(TO_LONG(handover_attempts)),
    total_failures = SUM(TO_LONG(handover_failures)),
    avg_failure_rate = ROUND(AVG(node_failure_rate), 2),
    max_failure_rate = MAX(node_failure_rate),
    avg_ue_count = AVG(TO_DOUBLE(ue_count)),
    sample_count = COUNT(*)
  BY ran_node_id, handover_type, source_rat, target_rat
| INLINESTATS
    mean_failure_rate = AVG(avg_failure_rate),
    stddev_failure_rate = STD_DEV(avg_failure_rate)
  BY source_rat, target_rat
| EVAL z_score = (avg_failure_rate - mean_failure_rate) / COALESCE(stddev_failure_rate, 1.0)
| WHERE z_score > 2.5
| LOOKUP JOIN ran_site_reference ON ran_node_id
| EVAL cascade_risk = CASE(
    z_score >= 4 AND max_failure_rate >= 70, "CRITICAL",
    z_score >= 3 AND max_failure_rate >= 50, "HIGH",
    z_score >= 2.5, "MEDIUM",
    "LOW"
  )
| KEEP
    ran_node_id,
    site_name,
    region,
    sub_region,
    vendor,
    technology_generation,
    handover_type,
    source_rat,
    target_rat,
    total_attempts,
    total_failures,
    avg_failure_rate,
    max_failure_rate,
    z_score,
    avg_ue_count,
    cascade_risk
| SORT z_score DESC, avg_failure_rate DESC''',
            'query_type': 'scripted',
            'pain_point': 'Radio equipment failure and cell tower handoff failures',
            'datasets': ['ran_performance_metrics', 'ran_site_reference']
        })

        # Query 12: UE Initiated Service Request Failure Analysis
        queries.append({
            'name': 'UE Initiated Service Request Procedure Failure Analysis',
            'description': (
                'Analyzes UE Initiated Service Request procedure failures by examining signaling '
                'logs for ServiceRequest messages with non-SUCCESS cause codes. Aggregates failure '
                'patterns by network element, protocol, and cause code to identify systemic issues '
                'in the attach and service request procedures. LOOKUP JOIN enriches results with '
                'network element metadata to correlate failures with specific element types, '
                'vendors, and criticality tiers.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_service_request_failures',
                'description': (
                    'Analyzes UE Initiated Service Request procedure failures by cause code and '
                    'network element. Identifies systemic attach procedure issues and correlates '
                    'with element type and vendor for targeted remediation.'
                ),
                'tags': ['service_request', 'ue_procedures', 'signaling', 'cause_code', 'esql']
            },
            'query': '''FROM signaling_logs
| WHERE message_type == "ServiceRequest"
| WHERE cause_code != "SUCCESS" OR cause_code IS NULL
| STATS
    total_failures = COUNT(*),
    unique_sessions = COUNT_DISTINCT(session_id),
    unique_sources = COUNT_DISTINCT(source_node),
    reject_count = SUM(CASE(cause_code == "REJECT", 1, 0)),
    timeout_count = SUM(CASE(cause_code == "TIMEOUT", 1, 0)),
    auth_failure_count = SUM(CASE(cause_code == "AUTH-FAILURE", 1, 0)),
    resource_unavail_count = SUM(CASE(cause_code == "RESOURCE-UNAVAILABLE", 1, 0)),
    protocol_error_count = SUM(CASE(cause_code == "PROTOCOL-ERROR", 1, 0))
  BY network_element_id, signaling_protocol, cause_code
| LOOKUP JOIN network_element_registry ON network_element_id
| EVAL failure_category = CASE(
    cause_code == "AUTH-FAILURE", "Authentication Issue",
    cause_code == "RESOURCE-UNAVAILABLE", "Resource Exhaustion",
    cause_code == "TIMEOUT", "Timeout/Latency",
    cause_code == "REJECT", "Policy Rejection",
    cause_code == "PROTOCOL-ERROR", "Protocol Defect",
    "Other"
  )
| KEEP
    network_element_id,
    element_name,
    element_type,
    region,
    vendor,
    criticality_tier,
    signaling_protocol,
    cause_code,
    failure_category,
    total_failures,
    unique_sessions,
    unique_sources,
    reject_count,
    timeout_count,
    auth_failure_count,
    resource_unavail_count,
    protocol_error_count
| SORT total_failures DESC, criticality_tier ASC''',
            'query_type': 'scripted',
            'pain_point': 'Service downtime leading to revenue loss and SLA violations',
            'datasets': ['signaling_logs', 'network_element_registry']
        })

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries with ?parameter syntax for user customization"""
        queries = []

        # Parameterized Query 1: Core Network Split-Brain Search by Region and Time
        queries.append({
            'name': 'Core Network Split-Brain Event Search',
            'description': (
                'Performs a targeted search across core network event records to rapidly identify '
                'split-brain conditions within a specified time window and network region. Matches '
                'against event descriptions and alert messages using full-text MATCH, scores results '
                'by relevance, and surfaces the most critical split-brain events first. Enables '
                'Network Operations engineers to quickly triage active split-brain incidents across '
                'distributed core nodes without manually scanning raw logs.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_split_brain_search',
                'description': (
                    'Searches core network events for split-brain conditions using full-text match. '
                    'Accepts search query and region parameters to rapidly triage active consensus '
                    'failures across distributed core nodes.'
                ),
                'tags': ['split_brain', 'core_network', 'search', 'parameterized', 'esql']
            },
            'query': '''FROM core_network_events
| WHERE MATCH(event_description, ?query) OR MATCH(alert_message, ?query) OR MATCH(event_title, ?query)
| WHERE event_type == "SPLIT-BRAIN" OR consensus_state IN ("SPLIT", "CANDIDATE")
| WHERE network_region == ?network_region
| EVAL relevance_score = TO_DOUBLE(score)
| KEEP
    event_id,
    event_title,
    event_description,
    alert_message,
    node_id,
    node_role,
    cluster_id,
    network_region,
    severity,
    consensus_state,
    affected_peers,
    @timestamp,
    relevance_score
| SORT relevance_score DESC, severity ASC, @timestamp DESC
| LIMIT 25''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'query',
                    'type': 'string',
                    'description': 'Search term to match against event descriptions, alert messages, and titles (e.g., "split brain quorum")',
                    'required': True
                },
                {
                    'name': 'network_region',
                    'type': 'string',
                    'description': 'Network region to filter events (e.g., NORTH, SOUTH, EAST, WEST, CENTRAL)',
                    'required': True
                }
            ],
            'pain_point': 'Core network split-brain and signaling storms',
            'datasets': ['core_network_events']
        })

        # Parameterized Query 2: Auth Failure Activity for Specific LAC/Region
        queries.append({
            'name': 'Authentication Failure Activity Analysis by Region',
            'description': (
                'Analyzes authentication failure activity for a specific network region or LAC, '
                'enabling targeted investigation of HSS synchronization issues or subscriber '
                'authentication problems. Filters data session logs and core network events by '
                'the specified region and failure type, aggregating failure counts, affected '
                'subscribers, and failure rates to surface the scope of authentication degradation '
                'in the targeted area.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_auth_failure_by_region',
                'description': (
                    'Analyzes auth failure activity for a specified network region. Identifies HSS '
                    'sync issues, quantifies affected subscribers, and surfaces failure rate trends '
                    'for targeted authentication troubleshooting.'
                ),
                'tags': ['authentication', 'hss', 'failure_analysis', 'parameterized', 'esql']
            },
            'query': '''FROM data_session_logs
| WHERE termination_cause == "AUTH-FAILURE"
| WHERE rat_type == ?rat_type
| STATS
    total_auth_failures = COUNT(*),
    affected_subscribers = COUNT_DISTINCT(subscriber_id),
    affected_cells = COUNT_DISTINCT(cell_id),
    total_sessions = COUNT(session_id)
  BY rat_type, session_status, apn
| EVAL auth_failure_rate = ROUND(
    TO_DOUBLE(total_auth_failures) * 100.0 / TO_DOUBLE(COALESCE(total_sessions, 1)),
    2
  )
| EVAL severity_flag = CASE(
    auth_failure_rate >= 20, "CRITICAL",
    auth_failure_rate >= 10, "HIGH",
    auth_failure_rate >= 5, "MEDIUM",
    "LOW"
  )
| SORT total_auth_failures DESC, affected_subscribers DESC''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'rat_type',
                    'type': 'string',
                    'description': 'Radio Access Technology type to filter (e.g., LTE, NR-SA, 5G-NR, NR-NSA)',
                    'required': True
                }
            ],
            'pain_point': 'HSS database corruption or synchronization issues affecting subscriber authentication',
            'datasets': ['data_session_logs']
        })

        # Parameterized Query 3: MME Node-Specific Bug and Fault Investigation
        queries.append({
            'name': 'MME Node Software Bug and Fault Investigation',
            'description': (
                'Investigates software bugs and fault events for a specific MME node and software '
                'version. Enriches fault events with bug signature metadata via LOOKUP JOIN to '
                'identify which known defects are actively manifesting on the target node. '
                'Aggregates fault frequency, affected subscriber counts, and remediation status '
                'to provide a complete picture of the node\'s software health and prioritize '
                'patching actions.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_mme_node_bug_investigation',
                'description': (
                    'Investigates software bugs and faults for a specific MME node and software '
                    'version. Correlates active fault codes with known bug signatures to identify '
                    'defects and prioritize patch deployment.'
                ),
                'tags': ['mme', 'bug_investigation', 'fault_analysis', 'parameterized', 'esql']
            },
            'query': '''FROM mme_system_logs
| WHERE mme_node_id == ?mme_node_id
| WHERE log_level IN ("ERROR", "CRITICAL", "WARN")
| WHERE fault_code IS NOT NULL
| LOOKUP JOIN mme_bug_signatures ON fault_code
| WHERE bug_id IS NOT NULL
| EVAL impact_score = CASE(
    bug_severity == "CRITICAL" AND patch_available == "NO", 5,
    bug_severity == "CRITICAL" AND patch_available == "YES", 4,
    bug_severity == "HIGH" AND patch_available == "NO", 3,
    bug_severity == "HIGH" AND patch_available == "YES", 2,
    1
  )
| EVAL remediation_status = CASE(
    patch_available == "YES", "Patch Available",
    workaround_available == "YES", "Workaround Available",
    "No Remediation"
  )
| STATS
    total_fault_events = COUNT(*),
    total_affected_subscribers = SUM(TO_LONG(affected_subscribers)),
    total_attach_failures = SUM(TO_LONG(attach_failures)),
    affected_processes = COUNT_DISTINCT(process_name),
    max_impact_score = MAX(impact_score)
  BY
    mme_node_id,
    software_version,
    bug_id,
    bug_title,
    bug_category,
    bug_severity,
    fault_code,
    patch_available,
    patch_version,
    cve_reference,
    remediation_status
| SORT max_impact_score DESC, total_affected_subscribers DESC''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'mme_node_id',
                    'type': 'string',
                    'description': 'MME node identifier to investigate (e.g., MME-01, MME-05, MME-08)',
                    'required': True
                }
            ],
            'pain_point': 'MME software bugs and resource exhaustion',
            'datasets': ['mme_system_logs', 'mme_bug_signatures']
        })

        # Parameterized Query 4: Signaling Storm by Protocol and Severity
        queries.append({
            'name': 'Signaling Storm Investigation by Protocol',
            'description': (
                'Investigates signaling storm conditions for a specific signaling protocol '
                '(e.g., SS7, DIAMETER, S1AP, GTP-C) to identify which network elements are '
                'experiencing abnormal message volume bursts. Aggregates message counts per '
                'element and applies Z-score detection, then enriches with registry metadata '
                'to surface capacity breaches and storm severity for the targeted protocol. '
                'Enables NOC engineers to quickly isolate storm sources before cascading failures.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_signaling_storm_by_protocol',
                'description': (
                    'Investigates signaling storms for a specific protocol (SS7, DIAMETER, S1AP). '
                    'Identifies which network elements have abnormal message bursts and capacity '
                    'breaches to enable rapid storm source isolation.'
                ),
                'tags': ['signaling_storm', 'protocol_analysis', 'capacity', 'parameterized', 'esql']
            },
            'query': '''FROM signaling_logs
| WHERE signaling_protocol == ?signaling_protocol
| EVAL time_bucket = DATE_TRUNC(1 minute, @timestamp)
| STATS
    message_count = COUNT(*),
    unique_sources = COUNT_DISTINCT(source_node),
    unique_destinations = COUNT_DISTINCT(destination_node),
    error_count = SUM(CASE(cause_code IN ("REJECT", "PROTOCOL-ERROR", "TIMEOUT"), 1, 0))
  BY time_bucket, network_element_id, signaling_protocol
| INLINESTATS
    avg_message_count = AVG(message_count),
    stddev_message_count = STD_DEV(message_count)
  BY network_element_id, signaling_protocol
| EVAL z_score = (TO_DOUBLE(message_count) - avg_message_count) / COALESCE(stddev_message_count, 1.0)
| EVAL burst_ratio = TO_DOUBLE(message_count) / COALESCE(avg_message_count, 1.0)
| WHERE z_score > 2
| LOOKUP JOIN network_element_registry ON network_element_id
| EVAL storm_severity = CASE(
    z_score >= 6, "CRITICAL",
    z_score >= 4.5, "HIGH",
    z_score >= 3, "MODERATE",
    "ELEVATED"
  )
| EVAL capacity_breach = CASE(
    message_count > TO_LONG(capacity_threshold_msg_per_min), true,
    false
  )
| KEEP
    time_bucket,
    network_element_id,
    element_name,
    element_type,
    region,
    vendor,
    criticality_tier,
    signaling_protocol,
    message_count,
    avg_message_count,
    z_score,
    burst_ratio,
    unique_sources,
    unique_destinations,
    error_count,
    storm_severity,
    capacity_threshold_msg_per_min,
    capacity_breach
| SORT z_score DESC, time_bucket ASC''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'signaling_protocol',
                    'type': 'string',
                    'description': 'Signaling protocol to analyze (e.g., SS7, DIAMETER, S1AP, GTP-C, NAS, SIP)',
                    'required': True
                }
            ],
            'pain_point': 'Core network split-brain and signaling storms',
            'datasets': ['signaling_logs', 'network_element_registry']
        })

        # Parameterized Query 5: Handover Failure Analysis by Technology Generation
        queries.append({
            'name': 'Handover Failure Analysis by Technology Generation',
            'description': (
                'Analyzes handover failure rates for a specific technology generation (4G-LTE, '
                '5G-NR, 4G/5G-DSS, 3G-UMTS) across all RAN nodes. Computes failure rates per '
                'node and handover type, enriches with site reference data, and uses INLINESTATS '
                'to identify statistically anomalous nodes within the selected technology. Enables '
                'targeted investigation of mobility issues affecting a specific radio generation '
                'during network upgrades or technology transitions.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_handover_by_tech_generation',
                'description': (
                    'Analyzes handover failures for a specific technology generation (4G, 5G, 3G). '
                    'Identifies anomalous RAN nodes using Z-score detection to support targeted '
                    'mobility optimization during technology transitions.'
                ),
                'tags': ['handover', 'technology_generation', 'ran', 'parameterized', 'esql']
            },
            'query': '''FROM ran_performance_metrics
| WHERE TO_LONG(handover_attempts) > 0
| STATS
    total_attempts = SUM(TO_LONG(handover_attempts)),
    total_failures = SUM(TO_LONG(handover_failures)),
    avg_ue_count = AVG(TO_DOUBLE(ue_count)),
    sample_count = COUNT(*)
  BY ran_node_id, handover_type, source_rat, target_rat
| EVAL node_failure_rate = ROUND(
    TO_DOUBLE(total_failures) * 100.0 / TO_DOUBLE(COALESCE(total_attempts, 1)),
    2
  )
| LOOKUP JOIN ran_site_reference ON ran_node_id
| WHERE technology_generation == ?technology_generation
| INLINESTATS
    mean_failure_rate = AVG(node_failure_rate),
    stddev_failure_rate = STD_DEV(node_failure_rate)
  BY handover_type, source_rat, target_rat
| EVAL z_score = (node_failure_rate - mean_failure_rate) / COALESCE(stddev_failure_rate, 1.0)
| EVAL failure_severity = CASE(
    node_failure_rate >= 10, "CRITICAL",
    node_failure_rate >= 5, "HIGH",
    node_failure_rate >= 2, "MEDIUM",
    "LOW"
  )
| KEEP
    ran_node_id,
    site_name,
    region,
    sub_region,
    vendor,
    technology_generation,
    handover_type,
    source_rat,
    target_rat,
    total_attempts,
    total_failures,
    node_failure_rate,
    z_score,
    avg_ue_count,
    failure_severity
| SORT node_failure_rate DESC, z_score DESC''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'technology_generation',
                    'type': 'string',
                    'description': 'Technology generation to analyze (e.g., 4G-LTE, 5G-NR, 4G/5G-DSS, 3G-UMTS)',
                    'required': True
                }
            ],
            'pain_point': 'Radio equipment failure and cell tower handoff failures',
            'datasets': ['ran_performance_metrics', 'ran_site_reference']
        })

        # Parameterized Query 6: Sustained Spike Pattern Detection Across Lag Periods
        queries.append({
            'name': 'Sustained Spike Pattern Detection Across Lag Periods',
            'description': (
                'Detects sustained spike patterns in MME error metrics across multiple time '
                'windows (lag periods) by comparing current error counts against rolling averages. '
                'Accepts a fault category parameter to focus analysis on specific failure domains '
                '(e.g., S1AP, AUTH, MEMORY, HSS). Uses INLINESTATS to establish per-node baselines '
                'and flags nodes where error counts remain elevated across consecutive time buckets, '
                'indicating a sustained degradation rather than a transient spike.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_sustained_spike_detection',
                'description': (
                    'Detects sustained spike patterns in MME error metrics across multiple lag '
                    'periods. Identifies nodes with persistent elevated errors for a specified fault '
                    'category to distinguish sustained degradation from transient spikes.'
                ),
                'tags': ['spike_detection', 'mme', 'sustained_errors', 'parameterized', 'esql']
            },
            'query': '''FROM mme_system_logs
| WHERE fault_category == ?fault_category
| WHERE log_severity IN ("ERROR", "CRITICAL", "WARNING")
| EVAL time_bucket = DATE_TRUNC(15 minutes, @timestamp)
| STATS
    s1ap_error_total = SUM(s1ap_error_count),
    nas_error_total = SUM(nas_signaling_error_count),
    attach_failure_total = SUM(TO_LONG(attach_failures)),
    affected_subscribers_total = SUM(TO_LONG(affected_subscribers)),
    event_count = COUNT(*)
  BY time_bucket, mme_node_id, mme_pool_id, fault_category
| INLINESTATS
    avg_s1ap_errors = AVG(s1ap_error_total),
    stddev_s1ap_errors = STD_DEV(s1ap_error_total),
    avg_nas_errors = AVG(nas_error_total),
    stddev_nas_errors = STD_DEV(nas_error_total),
    avg_attach_failures = AVG(attach_failure_total),
    stddev_attach_failures = STD_DEV(attach_failure_total)
  BY mme_node_id, fault_category
| EVAL s1ap_z_score = (TO_DOUBLE(s1ap_error_total) - avg_s1ap_errors) / COALESCE(stddev_s1ap_errors, 1.0)
| EVAL nas_z_score = (TO_DOUBLE(nas_error_total) - avg_nas_errors) / COALESCE(stddev_nas_errors, 1.0)
| EVAL attach_z_score = (TO_DOUBLE(attach_failure_total) - avg_attach_failures) / COALESCE(stddev_attach_failures, 1.0)
| EVAL composite_z_score = ROUND((s1ap_z_score + nas_z_score + attach_z_score) / 3.0, 2)
| EVAL spike_level = CASE(
    composite_z_score >= 4, "CRITICAL",
    composite_z_score >= 3, "HIGH",
    composite_z_score >= 2, "ELEVATED",
    "NORMAL"
  )
| WHERE composite_z_score >= 2
| KEEP
    time_bucket,
    mme_node_id,
    mme_pool_id,
    fault_category,
    s1ap_error_total,
    nas_error_total,
    attach_failure_total,
    affected_subscribers_total,
    s1ap_z_score,
    nas_z_score,
    attach_z_score,
    composite_z_score,
    spike_level,
    event_count
| SORT time_bucket DESC, composite_z_score DESC''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'fault_category',
                    'type': 'string',
                    'description': 'MME fault category to analyze (e.g., S1AP, AUTH, MEMORY, HSS, HANDOVER, BEARER, PAGING, SESSION, CPU, S6A)',
                    'required': True
                }
            ],
            'pain_point': 'Need to detect network issues before help desk is overwhelmed',
            'datasets': ['mme_system_logs']
        })

        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using MATCH and COMPLETION for semantic search over network events"""
        queries = []

        # RAG Query 1: Core Network Event Semantic Search and Analysis
        queries.append({
            'name': 'Core Network Event Intelligent Analysis',
            'description': (
                'Performs semantic search across core network events using full-text MATCH to '
                'find events relevant to a user\'s natural language question. Retrieves the most '
                'relevant high-severity events and uses an LLM via COMPLETION to synthesize a '
                'structured analysis of the network condition, likely root causes, and recommended '
                'actions. Enables NOC engineers to ask plain-language questions about network '
                'health and receive expert-level analysis grounded in actual event data.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_event_rag_analysis',
                'description': (
                    'Answers natural language questions about core network events using semantic '
                    'search and LLM analysis. Synthesizes event data into root cause analysis and '
                    'recommended actions for NOC engineers.'
                ),
                'tags': ['rag', 'core_network', 'semantic_search', 'llm_analysis', 'esql']
            },
            'query': '''FROM core_network_events METADATA _id
| WHERE MATCH(event_description, ?user_question) OR MATCH(alert_message, ?user_question) OR MATCH(event_title, ?user_question)
| WHERE severity IN ("CRITICAL", "HIGH")
| KEEP _id, event_id, event_title, event_description, alert_message, node_id, node_role, cluster_id, network_region, severity, event_type, consensus_state, affected_peers, @timestamp
| SORT @timestamp DESC
| LIMIT 5
| EVAL prompt = CONCAT(
    "You are a senior telecom network operations engineer. ",
    "A NOC analyst has asked: ", ?user_question, " ",
    "Based on the following network event data, provide: ",
    "1) A concise summary of what is happening, ",
    "2) The most likely root cause, ",
    "3) Immediate recommended actions. ",
    "Event: ", event_title, " | Type: ", event_type, " | Severity: ", severity, " | Region: ", network_region, " | Node: ", node_id, " | Consensus: ", consensus_state, " | Description: ", event_description)
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP event_id, event_title, event_type, severity, network_region, node_id, @timestamp, answer''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'string',
                    'description': 'Natural language question about network events (e.g., "What is causing split brain in the core network?")',
                    'required': True
                }
            ],
            'pain_point': 'Need to detect network issues before help desk is overwhelmed',
            'datasets': ['core_network_events']
        })

        # RAG Query 2: MME Bug Intelligent Remediation Advisor
        queries.append({
            'name': 'MME Bug Intelligent Remediation Advisor',
            'description': (
                'Performs semantic search across MME bug signature descriptions to find bugs '
                'relevant to a described symptom or failure pattern. Retrieves matching bug '
                'records and uses an LLM via COMPLETION to provide structured remediation '
                'guidance, including patch recommendations, workaround steps, and risk '
                'assessment. Enables network operations teams to quickly identify applicable '
                'known defects and receive actionable remediation advice without manually '
                'searching bug databases.'
            ),
            'tool_metadata': {
                'tool_id': 'telco_network_op_mme_bug_remediation_advisor',
                'description': (
                    'Provides intelligent MME bug remediation advice using semantic search and LLM. '
                    'Matches symptom descriptions to known bug signatures and synthesizes actionable '
                    'patch and workaround guidance for network operations teams.'
                ),
                'tags': ['rag', 'mme', 'bug_remediation', 'llm_advisor', 'esql']
            },
            'query': '''FROM mme_bug_signature_lookup METADATA _id
| WHERE MATCH(bug_description, ?symptom_description)
| KEEP _id, software_version, bug_id, bug_description, affected_component, patch_available, severity_rating
| SORT severity_rating ASC
| LIMIT 5
| EVAL prompt = CONCAT(
    "You are an expert MME (Mobility Management Entity) software engineer. ",
    "A network operations engineer is experiencing this issue: ", ?symptom_description, " ",
    "The following known bug may be relevant: ",
    "Bug ID: ", bug_id, " | Severity: ", severity_rating, " | Affected Component: ", affected_component, " | Software Version: ", software_version, " | Patch Available: ", patch_available, " | Description: ", bug_description, " ",
    "Please provide: 1) Whether this bug matches the described symptom, ",
    "2) Immediate mitigation steps if patch is not available, ",
    "3) Patch deployment recommendations if patch is available, ",
    "4) Risk assessment of leaving this unpatched.")
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP bug_id, software_version, affected_component, severity_rating, patch_available, answer''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'symptom_description',
                    'type': 'string',
                    'description': 'Description of the MME symptom or failure pattern being observed (e.g., "high memory usage and NAS signaling failures on MME nodes")',
                    'required': True
                }
            ],
            'pain_point': 'MME software bugs and resource exhaustion',
            'datasets': ['mme_bug_signature_lookup']
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum narrative impact"""
        return [
            # Start with subscriber-facing impact to establish urgency
            'Data Session Interruption Trending Over Time',
            'Mass Authentication Failure Event Detection',
            # Move to infrastructure failures driving the impact
            'Dropped Call Rate by Cell Tower and Mobility Zone',
            'Cell Tower Handoff Cascade Failure Detection',
            'Handover Failure Analytics by RAN and Region',
            # Core network health and stability
            'Core Network Split-Brain Event Detection',
            'Signaling Storm Detection Across Network Elements',
            # MME software and resource issues
            'MME Resource Exhaustion and Error Surge Detection',
            'MME Software Bug Enrichment and Impact Correlation',
            # Procedure-level analysis
            'UE Initiated Service Request Procedure Failure Analysis',
            'IMSI and Cell ID Cardinality Changes Over Time',
            # Security threats
            'Security Attack and SS7 Threat Detection',
            # Parameterized investigation tools
            'Core Network Split-Brain Event Search',
            'Authentication Failure Activity Analysis by Region',
            'MME Node Software Bug and Fault Investigation',
            'Signaling Storm Investigation by Protocol',
            'Handover Failure Analysis by Technology Generation',
            'Sustained Spike Pattern Detection Across Lag Periods',
            # AI-powered analysis
            'Core Network Event Intelligent Analysis',
            'MME Bug Intelligent Remediation Advisor',
        ]
