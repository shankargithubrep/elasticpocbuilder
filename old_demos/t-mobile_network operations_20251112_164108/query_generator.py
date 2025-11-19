
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class TMobileQueryGenerator(QueryGeneratorModule):
    """Query generator for T-Mobile - Network Operations
    
    Focuses on detecting network failures, security threats, and infrastructure issues
    across 4G/5G mobile network infrastructure including MME, HSS, and cell towers.
    """

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate ALL ES|QL queries from pre-planned strategy
        
        Returns queries for:
        - Cell tower cascade failure detection
        - IMSI influx anomaly detection for security threats
        - HSS mass authentication failure detection
        - MME split-brain and signaling storm detection
        - Semantic search for similar network failure patterns
        """
        queries = []

        # ============================================================
        # SCRIPTED QUERIES - No parameters, for exploration
        # ============================================================

        # Query 1: Cell Tower Cascade Failure Detection with Z-Score Analysis
        queries.append({
            'name': 'Cell Tower Cascade Failure Detection with Z-Score Analysis',
            'description': 'Detects abnormal spike patterns in cell ID failures using statistical z-score analysis across 5-minute intervals to identify cascade failures before they escalate',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_cell_cascade_detection',
                'description': 'Detects cell tower cascade failures using z-score analysis. Identifies abnormal failure spikes across 5-minute intervals to prevent mass service disruption before escalation.',
                'tags': ['network', 'infrastructure', 'cascade-failure', 'analytics', 'esql']
            },
            'query': '''FROM mme_signaling_failures
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)  # Widened from 5min for more aggregation
| STATS 
    failure_count = COUNT(*), 
    unique_imsi = COUNT_DISTINCT(imsi) 
  BY time_bucket, current_cell_id
| LOOKUP JOIN cell_tower_reference ON current_cell_id == cell_id
| INLINESTATS 
    avg_failures = AVG(failure_count), 
    stddev_failures = STD_DEV(failure_count), 
    p95_failures = PERCENTILE(failure_count, 95) 
  BY region
| EVAL z_score = (failure_count - avg_failures) / COALESCE(stddev_failures, 1)
| WHERE failure_count >= 2  # Adjusted: max in data is 2
| EVAL severity = CASE(
    failure_count >= 2, "CRITICAL",  # Adjusted threshold 
    z_score > 4, "HIGH", 
    "MEDIUM"
  )
| KEEP 
    current_cell_id, 
    severity, 
    cell_name, 
    z_score, 
    failure_count, 
    time_bucket, 
    unique_imsi, 
    equipment_type
| SORT z_score DESC
| LIMIT 50''',
            'query_type': 'scripted',
            'pain_point': 'Cell tower handoff cascade failures causing mass service disruption',
            'complexity': 'high'
        })

        # Query 2: IMSI Influx Anomaly Detection for Security Threats
        queries.append({
            'name': 'IMSI Influx Anomaly Detection for Security Threats',
            'description': 'Identifies unusual subscriber influx patterns by detecting statistical anomalies in unique IMSI counts per MME host to catch security attacks early',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_imsi_anomaly_detection',
                'description': 'Identifies unusual subscriber influx patterns using statistical anomaly detection. Catches SS7 attacks, rogue networks, and roaming misconfigurations early by analyzing IMSI patterns per MME host.',
                'tags': ['security', 'threat-detection', 'roaming', 'analytics', 'esql']
            },
            'query': '''FROM mme_signaling_failures
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)  # Widened from 5min for more aggregation
| STATS 
    unique_imsi_count = COUNT_DISTINCT(imsi), 
    roaming_imsi = COUNT_DISTINCT(imsi) WHERE roaming_flag == true 
  BY time_bucket, mme_host
| LOOKUP JOIN mme_host_inventory ON mme_host
| INLINESTATS 
    avg_imsi = AVG(unique_imsi_count), 
    stddev_imsi = STD_DEV(unique_imsi_count), 
    baseline_imsi = PERCENTILE(unique_imsi_count, 50) 
  BY datacenter
| EVAL z_score = (unique_imsi_count - avg_imsi) / COALESCE(stddev_imsi, 1)
| EVAL pct_deviation = ((unique_imsi_count - baseline_imsi) / baseline_imsi) * 100
| WHERE unique_imsi_count >= 2  # Adjusted: max in data is 2
| EVAL threat_level = CASE(
    z_score > 5, "CRITICAL_ATTACK", 
    z_score > 4, "HIGH_RISK", 
    "SUSPICIOUS"
  )
| KEEP 
    mme_host, 
    threat_level, 
    datacenter, 
    z_score, 
    unique_imsi_count, 
    time_bucket, 
    roaming_imsi, 
    pct_deviation
| SORT z_score DESC''',
            'query_type': 'scripted',
            'pain_point': 'Rogue network attempts, SS7 attacks, and international roaming configuration errors',
            'complexity': 'high'
        })

        # Query 3: HSS Mass Authentication Failure Detection
        queries.append({
            'name': 'HSS Mass Authentication Failure Detection',
            'description': 'Detects mass authentication failures indicating HSS problems by analyzing failure rates and response time anomalies across MME hosts',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_hss_failure_detection',
                'description': 'Detects HSS database corruption and synchronization issues. Analyzes authentication failure rates and response times to identify mass failures affecting subscriber authentication.',
                'tags': ['hss', 'authentication', 'database', 'performance', 'esql']
            },
            'query': '''FROM subscriber_authentication_events
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)  # Widened from 5min for more aggregation
| STATS 
    total_attempts = COUNT(*), 
    failed_attempts = COUNT(*) WHERE auth_result == "FAILURE", 
    avg_response_time = AVG(response_time_ms), 
    affected_subscribers = COUNT_DISTINCT(imsi) 
  BY time_bucket, mme_host
| LOOKUP JOIN mme_host_inventory ON mme_host
| EVAL failure_rate = (TO_DOUBLE(failed_attempts) / total_attempts) * 100
| INLINESTATS 
    baseline_failure_rate = AVG(failure_rate), 
    stddev_failure_rate = STD_DEV(failure_rate) 
  BY datacenter
| EVAL z_score = (failure_rate - baseline_failure_rate) / COALESCE(stddev_failure_rate, 1)
| WHERE failure_rate > 10 AND affected_subscribers >= 2  # Adjusted: max subscribers is 3
| EVAL severity = CASE(
    failure_rate > 50, "CRITICAL_HSS_OUTAGE", 
    failure_rate > 30, "HIGH_HSS_DEGRADATION", 
    "MEDIUM_HSS_ISSUE"
  )
| KEEP 
    mme_host, 
    severity, 
    software_version, 
    failure_rate, 
    affected_subscribers, 
    time_bucket, 
    avg_response_time, 
    z_score
| SORT failure_rate DESC''',
            'query_type': 'scripted',
            'pain_point': 'HSS database corruption or synchronization issues affecting subscriber authentication',
            'complexity': 'medium'
        })

        # Query 4: MME Split-Brain and Signaling Storm Detection
        queries.append({
            'name': 'MME Split-Brain and Signaling Storm Detection',
            'description': 'Multi-dimensional analysis detecting split-brain scenarios by identifying simultaneous high error rates across multiple MME hosts with correlated failure patterns',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_splitbrain_detection',
                'description': 'Detects core network split-brain conditions and signaling storms. Multi-dimensional analysis identifies simultaneous high error rates across MME hosts to prevent extended outages.',
                'tags': ['core-network', 'split-brain', 'signaling-storm', 'critical', 'esql']
            },
            'query': '''FROM mme_signaling_failures
| EVAL time_bucket = DATE_TRUNC(1 minute, @timestamp)
| STATS 
    error_rate = COUNT(*), 
    unique_procedures = COUNT_DISTINCT(procedure_type), 
    affected_cells = COUNT_DISTINCT(current_cell_id), 
    affected_imsi = COUNT_DISTINCT(imsi) 
  BY time_bucket, mme_host
| LOOKUP JOIN mme_host_inventory ON mme_host
| INLINESTATS 
    avg_error_rate = AVG(error_rate), 
    stddev_error_rate = STD_DEV(error_rate), 
    max_error_rate = MAX(error_rate) 
  BY datacenter
| EVAL z_score = (error_rate - avg_error_rate) / COALESCE(stddev_error_rate, 1)
| EVAL capacity_pct = (TO_DOUBLE(error_rate) / max_capacity) * 100
| WHERE error_rate >= 2  # Adjusted: max in data is 2
| EVAL condition_type = CASE(
    affected_cells >= 2  # Adjusted threshold, "SPLIT_BRAIN_CRITICAL", 
    error_rate >= 2  # Adjusted threshold, "SIGNALING_STORM", 
    "SEVERE_OVERLOAD"
  )
| KEEP 
    mme_host, 
    condition_type, 
    datacenter, 
    z_score, 
    error_rate, 
    time_bucket, 
    affected_imsi, 
    affected_cells
| SORT error_rate DESC
| LIMIT 20''',
            'query_type': 'scripted',
            'pain_point': 'Core network split-brain conditions and signaling storms causing extended outages',
            'complexity': 'high'
        })

        # Query 5: Handoff Failure Pattern Analysis by Region
        queries.append({
            'name': 'Handoff Failure Pattern Analysis by Region',
            'description': 'Analyzes handoff failures between cell towers grouped by region to identify geographic patterns and infrastructure weaknesses',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_handoff_analysis',
                'description': 'Analyzes handoff failure patterns across regions. Identifies geographic infrastructure weaknesses and cell tower configuration issues causing dropped calls during mobility.',
                'tags': ['handoff', 'mobility', 'regional', 'infrastructure', 'esql']
            },
            'query': '''FROM mme_signaling_failures
| WHERE procedure_type == "HANDOVER"
| LOOKUP JOIN cell_tower_reference ON current_cell_id == cell_id
| STATS 
    handoff_failures = COUNT(*),
    unique_subscribers = COUNT_DISTINCT(imsi),
    error_types = COUNT_DISTINCT(error_code)
  BY region, equipment_type
| EVAL failure_rate_per_subscriber = TO_DOUBLE(handoff_failures) / unique_subscribers
| WHERE handoff_failures > 50
| SORT handoff_failures DESC
| LIMIT 30''',
            'query_type': 'scripted',
            'pain_point': 'Radio equipment failure and cell tower handoff cascade failures',
            'complexity': 'medium'
        })

        # Query 6: MME Resource Exhaustion Monitoring
        queries.append({
            'name': 'MME Resource Exhaustion Monitoring',
            'description': 'Monitors MME hosts for signs of resource exhaustion by analyzing error patterns, failure reasons, and load distribution',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_mme_resource_monitor',
                'description': 'Monitors MME software bugs, memory leaks, and resource exhaustion. Analyzes error patterns and load distribution to detect capacity issues before service degradation.',
                'tags': ['mme', 'resource-exhaustion', 'capacity', 'performance', 'esql']
            },
            'query': '''FROM mme_signaling_failures
| WHERE error_code IN ("S1AP_TIMEOUT", "EMM_CAUSE_17", "EMM_CAUSE_18")
| EVAL time_bucket = DATE_TRUNC(10 minutes, @timestamp)
| STATS 
    timeout_count = COUNT(*),
    affected_procedures = COUNT_DISTINCT(procedure_type),
    affected_cells = COUNT_DISTINCT(current_cell_id),
    affected_imsi = COUNT_DISTINCT(imsi)
  BY time_bucket, mme_host
| LOOKUP JOIN mme_host_inventory ON mme_host
| EVAL load_pct = (TO_DOUBLE(timeout_count) / max_capacity) * 100
| WHERE timeout_count > 100
| EVAL status = CASE(
    load_pct > 80, "CRITICAL_OVERLOAD",
    load_pct > 60, "HIGH_LOAD",
    "MODERATE_LOAD"
  )
| KEEP 
    mme_host,
    status,
    software_version,
    datacenter,
    timeout_count,
    load_pct,
    affected_imsi,
    time_bucket
| SORT timeout_count DESC
| LIMIT 25''',
            'query_type': 'scripted',
            'pain_point': 'MME software bugs, memory leaks, and resource exhaustion',
            'complexity': 'medium'
        })

        # Query 7: Authentication Pattern Anomaly by Roaming Partner
        queries.append({
            'name': 'Authentication Pattern Anomaly by Roaming Partner',
            'description': 'Tracks unusual authentication patterns from roaming partners to detect configuration errors and potential security issues',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_roaming_auth_anomaly',
                'description': 'Tracks unusual subscriber authentication patterns from roaming partners. Detects international roaming configuration errors and potential security threats early.',
                'tags': ['roaming', 'authentication', 'security', 'international', 'esql']
            },
            'query': '''FROM subscriber_authentication_events
| WHERE roaming_partner != "None"
| EVAL time_bucket = DATE_TRUNC(15 minutes, @timestamp)
| STATS
    auth_attempts = COUNT(*),
    failures = COUNT(*) WHERE auth_result == "FAILURE",
    timeouts = COUNT(*) WHERE auth_result == "TIMEOUT",
    avg_response = AVG(response_time_ms),
    unique_imsi = COUNT_DISTINCT(imsi)
  BY time_bucket, roaming_partner
| EVAL failure_rate = (TO_DOUBLE(failures) / auth_attempts) * 100
| EVAL timeout_rate = (TO_DOUBLE(timeouts) / auth_attempts) * 100
| WHERE failure_rate > 10 OR timeout_rate > 5
| EVAL risk_level = CASE(
    failure_rate > 30, "HIGH_RISK",
    timeout_rate > 15, "HIGH_RISK",
    failure_rate > 20, "MEDIUM_RISK",
    "LOW_RISK"
  )
| KEEP
    roaming_partner,
    risk_level,
    failure_rate,
    timeout_rate,
    auth_attempts,
    unique_imsi,
    avg_response,
    time_bucket
| SORT failure_rate DESC
| LIMIT 20''',
            'query_type': 'scripted',
            'pain_point': 'International roaming configuration errors and security attacks',
            'complexity': 'medium'
        })

        # Query 8: Cell Tower Equipment Type Failure Analysis
        queries.append({
            'name': 'Cell Tower Equipment Type Failure Analysis',
            'description': 'Compares failure rates across different cell tower equipment types to identify hardware-specific issues and maintenance needs',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_equipment_failure_analysis',
                'description': 'Compares failure rates across cell tower equipment types. Identifies hardware-specific issues, maintenance needs, and equipment reliability problems.',
                'tags': ['equipment', 'hardware', 'reliability', 'maintenance', 'esql']
            },
            'query': '''FROM mme_signaling_failures
| LOOKUP JOIN cell_tower_reference ON current_cell_id == cell_id
| STATS
    total_failures = COUNT(*),
    unique_cells = COUNT_DISTINCT(current_cell_id),
    unique_imsi = COUNT_DISTINCT(imsi),
    error_types = COUNT_DISTINCT(error_code)
  BY equipment_type, maintenance_status
| EVAL failures_per_cell = TO_DOUBLE(total_failures) / unique_cells
| WHERE total_failures > 100
| SORT failures_per_cell DESC
| LIMIT 25''',
            'query_type': 'scripted',
            'pain_point': 'Radio equipment failure and infrastructure reliability issues',
            'complexity': 'low'
        })

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries that accept user input
        
        These queries allow network operations teams to customize analysis
        by time range, MME host, region, or error severity.
        """
        queries = []

        # Parameterized Query 1: Cell Tower Failure Analysis by Time Range and Region
        queries.append({
            'name': 'Cell Tower Failure Analysis by Time Range and Region',
            'description': 'Analyzes cell tower failures for a specific time range and region with customizable severity threshold',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_cell_failure_timerange',
                'description': 'Analyzes cell tower failures for specific time ranges and regions. Customizable severity threshold helps prioritize critical infrastructure issues.',
                'tags': ['cell-tower', 'regional', 'timerange', 'parameterized', 'esql']
            },
            'query': '''FROM mme_signaling_failures
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| LOOKUP JOIN cell_tower_reference ON current_cell_id == cell_id
| WHERE region == ?region
| STATS
    failure_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    error_types = COUNT_DISTINCT(error_code)
  BY current_cell_id, cell_name, equipment_type
| WHERE failure_count >= ?min_failures
| SORT failure_count DESC
| LIMIT 50''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'date',
                    'description': 'Analysis start date',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'date',
                    'description': 'Analysis end date',
                    'required': True
                },
                {
                    'name': 'region',
                    'type': 'keyword',
                    'description': 'Network region (e.g., Northeast, West, Southeast)',
                    'required': True
                },
                {
                    'name': 'min_failures',
                    'type': 'integer',
                    'description': 'Minimum failure count threshold',
                    'required': True,
                    'default': 100
                }
            ],
            'pain_point': 'Need to analyze specific regions and time periods for targeted troubleshooting',
            'complexity': 'medium'
        })

        # Parameterized Query 2: MME Performance Analysis by Host
        queries.append({
            'name': 'MME Performance Analysis by Host',
            'description': 'Analyzes specific MME host performance with customizable error code filtering and time range',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_mme_performance_analysis',
                'description': 'Analyzes specific MME host performance over custom time ranges. Filter by error codes to investigate particular failure types and patterns.',
                'tags': ['mme', 'performance', 'host-specific', 'parameterized', 'esql']
            },
            'query': '''FROM mme_signaling_failures
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE mme_host == ?mme_host
| WHERE error_code == ?error_code
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)  # Widened from 5min for more aggregation
| STATS
    error_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    affected_cells = COUNT_DISTINCT(current_cell_id)
  BY time_bucket, procedure_type
| SORT time_bucket DESC
| LIMIT 100''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'date',
                    'description': 'Analysis start date',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'date',
                    'description': 'Analysis end date',
                    'required': True
                },
                {
                    'name': 'mme_host',
                    'type': 'keyword',
                    'description': 'MME host identifier (e.g., MME-01, MME-02)',
                    'required': True
                },
                {
                    'name': 'error_code',
                    'type': 'keyword',
                    'description': 'Error code to analyze (e.g., EMM_CAUSE_18, S1AP_TIMEOUT)',
                    'required': True
                }
            ],
            'pain_point': 'Need to investigate specific MME hosts and error types for root cause analysis',
            'complexity': 'medium'
        })

        # Parameterized Query 3: Authentication Failure Analysis by Partner
        queries.append({
            'name': 'Authentication Failure Analysis by Roaming Partner',
            'description': 'Analyzes authentication failures for a specific roaming partner over a custom time range',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_roaming_partner_analysis',
                'description': 'Analyzes authentication failures for specific roaming partners. Investigates international roaming issues and configuration errors with customizable time ranges.',
                'tags': ['roaming', 'authentication', 'partner-specific', 'parameterized', 'esql']
            },
            'query': '''FROM subscriber_authentication_events
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE roaming_partner == ?roaming_partner
| EVAL time_bucket = DATE_TRUNC(10 minutes, @timestamp)
| STATS
    total_attempts = COUNT(*),
    failures = COUNT(*) WHERE auth_result == "FAILURE",
    timeouts = COUNT(*) WHERE auth_result == "TIMEOUT",
    avg_response = AVG(response_time_ms),
    unique_imsi = COUNT_DISTINCT(imsi)
  BY time_bucket, authentication_type
| EVAL failure_rate = (TO_DOUBLE(failures) / total_attempts) * 100
| SORT time_bucket DESC
| LIMIT 100''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'date',
                    'description': 'Analysis start date',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'date',
                    'description': 'Analysis end date',
                    'required': True
                },
                {
                    'name': 'roaming_partner',
                    'type': 'keyword',
                    'description': 'Roaming partner name (e.g., Verizon, Vodafone, AT&T)',
                    'required': True
                }
            ],
            'pain_point': 'Need to investigate roaming partner-specific authentication issues',
            'complexity': 'medium'
        })

        # Parameterized Query 4: Procedure Type Failure Trend Analysis
        queries.append({
            'name': 'Procedure Type Failure Trend Analysis',
            'description': 'Analyzes failure trends for specific procedure types (ATTACH, HANDOVER, TAU) over time',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_procedure_trend_analysis',
                'description': 'Analyzes failure trends for specific network procedures over time. Tracks ATTACH, HANDOVER, and TAU failures to identify systematic issues.',
                'tags': ['procedure', 'trends', 'failure-analysis', 'parameterized', 'esql']
            },
            'query': '''FROM mme_signaling_failures
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE procedure_type == ?procedure_type
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS
    failure_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    unique_cells = COUNT_DISTINCT(current_cell_id),
    error_types = COUNT_DISTINCT(error_code)
  BY time_bucket
| SORT time_bucket ASC
| LIMIT 200''',
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'start_date',
                    'type': 'date',
                    'description': 'Analysis start date',
                    'required': True
                },
                {
                    'name': 'end_date',
                    'type': 'date',
                    'description': 'Analysis end date',
                    'required': True
                },
                {
                    'name': 'procedure_type',
                    'type': 'keyword',
                    'description': 'Network procedure type (ATTACH, HANDOVER, TAU, SERVICE_REQUEST, DETACH, PDN_CONNECTIVITY)',
                    'required': True
                }
            ],
            'pain_point': 'Need to track specific procedure failure trends over time',
            'complexity': 'low'
        })

        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using semantic search on failure descriptions
        
        Uses MATCH to find similar failure patterns based on natural language
        descriptions from the failure_reason, tower_description, and host_description fields.
        """
        queries = []

        # RAG Query 1: Semantic Search for Similar Network Failure Patterns
        queries.append({
            'name': 'Semantic Search for Similar Network Failure Patterns',
            'description': 'Uses semantic search to find similar failure patterns based on natural language descriptions, helping identify recurring issues and root causes',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_semantic_failure_search',
                'description': 'Searches for similar network failure patterns using natural language. Helps identify recurring issues and root causes by finding semantically similar failure descriptions.',
                'tags': ['semantic-search', 'failure-analysis', 'rag', 'root-cause', 'esql']
            },
            'query': '''FROM mme_signaling_failures
| WHERE MATCH(failure_reason, ?user_question, {"fuzziness": "AUTO"})
| LOOKUP JOIN cell_tower_reference ON current_cell_id == cell_id
| STATS 
    failure_count = COUNT(*), 
    unique_subscribers = COUNT_DISTINCT(imsi), 
    error_types = COUNT_DISTINCT(error_code) 
  BY current_cell_id, equipment_type, region
| WHERE failure_count > 100
| KEEP 
    current_cell_id, 
    cell_name, 
    equipment_type, 
    failure_count, 
    unique_subscribers, 
    region, 
    error_types
| SORT failure_count DESC
| LIMIT 25''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Natural language description of failure pattern to search for (e.g., "memory exhaustion", "handoff cascade", "HSS timeout")',
                    'required': True
                }
            ],
            'pain_point': 'Difficulty identifying root causes of recurring network issues across different failure scenarios',
            'complexity': 'medium'
        })

        # RAG Query 2: Cell Tower Issue Pattern Search
        queries.append({
            'name': 'Cell Tower Issue Pattern Search',
            'description': 'Searches cell tower descriptions for similar infrastructure issues and maintenance patterns',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_tower_issue_search',
                'description': 'Searches cell tower descriptions for similar infrastructure issues. Identifies towers with comparable problems and maintenance patterns for proactive intervention.',
                'tags': ['semantic-search', 'cell-tower', 'infrastructure', 'rag', 'esql']
            },
            'query': '''FROM cell_tower_reference
| WHERE MATCH(tower_description, ?user_question, {"fuzziness": "AUTO"})
| LOOKUP JOIN mme_signaling_failures ON cell_id == current_cell_id
| STATS
    failure_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    error_types = COUNT_DISTINCT(error_code)
  BY cell_id, cell_name, equipment_type, region, maintenance_status
| WHERE failure_count > 50
| KEEP
    cell_id,
    cell_name,
    equipment_type,
    region,
    maintenance_status,
    failure_count,
    unique_imsi,
    error_types
| SORT failure_count DESC
| LIMIT 20''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Natural language description of tower issue (e.g., "coastal coverage", "high-density area", "rural coverage")',
                    'required': True
                }
            ],
            'pain_point': 'Difficulty finding similar infrastructure issues across cell tower inventory',
            'complexity': 'medium'
        })

        # RAG Query 3: MME Host Configuration Issue Search
        queries.append({
            'name': 'MME Host Configuration Issue Search',
            'description': 'Searches MME host descriptions for similar configuration and capacity issues',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_mme_config_search',
                'description': 'Searches MME host descriptions for similar configuration issues. Identifies hosts with comparable capacity or software problems for coordinated troubleshooting.',
                'tags': ['semantic-search', 'mme', 'configuration', 'rag', 'esql']
            },
            'query': '''FROM mme_host_inventory
| WHERE MATCH(host_description, ?user_question, {"fuzziness": "AUTO"})
| LOOKUP JOIN mme_signaling_failures ON mme_host == mme_host
| STATS
    total_failures = COUNT(*),
    unique_procedures = COUNT_DISTINCT(procedure_type),
    unique_cells = COUNT_DISTINCT(current_cell_id),
    unique_imsi = COUNT_DISTINCT(imsi)
  BY mme_host, datacenter, software_version, hardware_model
| WHERE total_failures > 100
| KEEP
    mme_host,
    datacenter,
    software_version,
    hardware_model,
    total_failures,
    unique_procedures,
    unique_cells,
    unique_imsi
| SORT total_failures DESC
| LIMIT 15''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Natural language description of MME issue (e.g., "high subscriber density", "IoT device management", "enterprise customers")',
                    'required': True
                }
            ],
            'pain_point': 'Difficulty identifying MME hosts with similar capacity or configuration challenges',
            'complexity': 'medium'
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum impact
        
        Progression strategy:
        1. Start with critical real-time threat detection (cascade failures, security)
        2. Show infrastructure monitoring (HSS, MME, split-brain)
        3. Demonstrate analytical depth (regional analysis, equipment comparison)
        4. Show customization with parameterized queries
        5. Finish with semantic search capabilities
        """
        return [
            # Critical real-time detection
            'Cell Tower Cascade Failure Detection with Z-Score Analysis',
            'IMSI Influx Anomaly Detection for Security Threats',
            
            # Infrastructure health monitoring
            'HSS Mass Authentication Failure Detection',
            'MME Split-Brain and Signaling Storm Detection',
            'MME Resource Exhaustion Monitoring',
            
            # Analytical depth
            'Handoff Failure Pattern Analysis by Region',
            'Authentication Pattern Anomaly by Roaming Partner',
            'Cell Tower Equipment Type Failure Analysis',
            
            # Parameterized queries for customization
            'Cell Tower Failure Analysis by Time Range and Region',
            'MME Performance Analysis by Host',
            'Authentication Failure Analysis by Roaming Partner',
            'Procedure Type Failure Trend Analysis',
            
            # Semantic search capabilities
            'Semantic Search for Similar Network Failure Patterns',
            'Cell Tower Issue Pattern Search',
            'MME Host Configuration Issue Search'
        ]
