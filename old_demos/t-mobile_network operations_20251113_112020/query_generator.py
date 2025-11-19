
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class TMobileQueryGenerator(QueryGeneratorModule):
    """Query generator for T-Mobile - Network Operations
    
    Implements queries for detecting and analyzing mobile network failures,
    including MME failures, cell tower handoff issues, authentication problems,
    and security threats across 4G/5G infrastructure.
    """

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate ALL ES|QL queries from pre-planned strategy
        
        Returns comprehensive set of queries for network operations monitoring:
        - Mass authentication failure detection
        - Cell tower handoff cascade analysis
        - MME split-brain and signaling storm detection
        - Enterprise SLA violation risk prediction
        - Security attack detection
        """
        queries = []

        # ============================================================
        # SCRIPTED QUERIES - No parameters, for exploration
        # ============================================================

        # Query 1: Mass Subscriber Authentication Failure Detection
        queries.append({
            'name': 'Mass Subscriber Authentication Failure Detection',
            'description': 'Detect mass authentication failures using statistical z-score analysis across 5-minute intervals, enriched with subscriber context to identify enterprise customer impact and HSS database issues before help desk is overwhelmed',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_mass_auth_failure',
                'description': 'Detects mass authentication failures from HSS database corruption or sync issues. Identifies subscriber authentication patterns using z-score analysis before help desk is overwhelmed. Critical for preventing widespread service outages.',
                'tags': ['authentication', 'hss', 'failure-detection', 'esql', 'security']
            },
            'query': '''FROM mme_failure_events
| WHERE authentication_attempt == true 
  AND failure_code IN ("HSS-401", "NAS-301", "NAS-302", "EMM-001", "EMM-002", "EMM-003")
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    unique_mme = COUNT_DISTINCT(mme_host)
  BY time_bucket
| INLINESTATS 
    avg_failures = AVG(failure_count),
    stddev_failures = STD_DEV(failure_count),
    avg_imsi = AVG(unique_imsi),
    stddev_imsi = STD_DEV(unique_imsi)
| EVAL 
    z_score_failures = (failure_count - avg_failures) / COALESCE(stddev_failures, 1),
    z_score_imsi = (unique_imsi - avg_imsi) / COALESCE(stddev_imsi, 1),
    imsi_change_rate = unique_imsi - avg_imsi
| WHERE (z_score_failures > 3 OR z_score_imsi > 3) AND failure_count > 50
| EVAL severity = CASE(
    z_score_imsi > 4 AND unique_imsi > 100, "CRITICAL",
    z_score_imsi > 3 AND unique_imsi > 50, "HIGH",
    "MEDIUM"
  )
| KEEP time_bucket, severity, unique_imsi, failure_count, z_score_imsi, z_score_failures, unique_mme, imsi_change_rate
| SORT z_score_imsi DESC
| LIMIT 20''',
            'query_type': 'scripted',
            'pain_point': 'HSS database corruption or synchronization issues affecting subscriber authentication',
            'use_case': 'Alert on unusual subscriber authentication patterns before help desk is overwhelmed'
        })

        # Query 2: Cell Tower Handoff Cascade Failure Analysis
        queries.append({
            'name': 'Cell Tower Handoff Cascade Failure Analysis',
            'description': 'Identify systematic cell tower handoff failures using multi-dimensional cardinality analysis, detect infrastructure cascade failures from power or equipment issues affecting 50+ cells, enriched with tower metadata',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_handoff_cascade',
                'description': 'Identifies cell tower handoff cascade failures from infrastructure problems. Detects power failures and equipment issues affecting multiple cells using statistical analysis. Prevents dropped calls during mobility.',
                'tags': ['handoff', 'cell-tower', 'infrastructure', 'esql', 'mobility']
            },
            'query': '''FROM mme_failure_events
| WHERE handover_attempt == true 
  AND failure_code IN ("S1AP-201", "S1AP-202", "ESM-101", "ESM-102")
| LOOKUP JOIN cell_towers ON cell_id
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*),
    unique_cells = COUNT_DISTINCT(cell_id),
    unique_source_cells = COUNT_DISTINCT(source_cell_id),
    unique_target_cells = COUNT_DISTINCT(target_cell_id),
    unique_markets = COUNT_DISTINCT(market_name)
  BY time_bucket, power_source
| INLINESTATS 
    avg_cells = AVG(unique_cells),
    stddev_cells = STD_DEV(unique_cells),
    p95_cells = PERCENTILE(unique_cells, 95),
    avg_failures = AVG(failure_count)
  BY power_source
| EVAL 
    z_score_cells = (unique_cells - avg_cells) / COALESCE(stddev_cells, 1),
    cell_change_rate = unique_cells - avg_cells,
    pct_above_baseline = ((unique_cells - avg_cells) / COALESCE(avg_cells, 1)) * 100
| WHERE (z_score_cells > 2.5 OR unique_cells > 15) AND failure_count > 50
| EVAL severity = CASE(
    unique_cells > 30 AND z_score_cells > 3, "CRITICAL",
    unique_cells > 15 AND z_score_cells > 2.5, "HIGH",
    "MEDIUM"
  )
| KEEP time_bucket, severity, unique_cells, failure_count, z_score_cells, unique_markets, power_source, pct_above_baseline
| SORT z_score_cells DESC
| LIMIT 20''',
            'query_type': 'scripted',
            'pain_point': 'Radio equipment failure and cell site power failures affecting handoffs',
            'use_case': 'Identify cell tower handoff cascade failures from infrastructure problems'
        })

        # Query 3: MME Split-Brain and Signaling Storm Detection
        queries.append({
            'name': 'MME Split-Brain and Signaling Storm Detection',
            'description': 'Detect split-brain conditions and signaling storms by analyzing failure patterns across multiple MME hosts in same cluster, using statistical deviation to identify synchronized cyclical failures indicating core network issues',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_split_brain_storm',
                'description': 'Detects core network split-brain conditions and signaling storms across MME clusters. Identifies synchronized cyclical failures affecting multiple hosts. Critical for preventing cascading core network outages.',
                'tags': ['mme', 'split-brain', 'signaling-storm', 'esql', 'core-network']
            },
            'query': '''FROM mme_failure_events
| WHERE failure_code IN ("S1AP-201", "S1AP-202", "ESM-101", "ESM-102", "NAS-301", "NAS-302")
| LOOKUP JOIN mme_hosts ON mme_host
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*),
    unique_mme_hosts = COUNT_DISTINCT(mme_host),
    unique_message_types = COUNT_DISTINCT(signaling_message_type),
    affected_subscribers = COUNT_DISTINCT(imsi)
  BY time_bucket, cluster_id, datacenter
| INLINESTATS 
    avg_failures = AVG(failure_count),
    stddev_failures = STD_DEV(failure_count),
    avg_mme_hosts = AVG(unique_mme_hosts),
    p95_failures = PERCENTILE(failure_count, 95)
  BY cluster_id
| EVAL 
    z_score_failures = (failure_count - avg_failures) / COALESCE(stddev_failures, 1),
    multi_host_indicator = CASE(unique_mme_hosts >= 2, 1, 0),
    storm_probability = z_score_failures * multi_host_indicator
| WHERE z_score_failures > 2.5 AND unique_mme_hosts >= 2 AND failure_count > 50
| EVAL severity = CASE(
    unique_mme_hosts >= 3 AND z_score_failures > 4, "CRITICAL",
    unique_mme_hosts >= 2 AND z_score_failures > 3, "HIGH",
    "MEDIUM"
  )
| KEEP time_bucket, severity, unique_mme_hosts, failure_count, affected_subscribers, cluster_id, datacenter, storm_probability
| SORT storm_probability DESC
| LIMIT 20''',
            'query_type': 'scripted',
            'pain_point': 'Core network split-brain and signaling storms causing cyclical failures',
            'use_case': 'Detect core network split-brain or signaling storms across multiple hosts'
        })

        # Query 4: Enterprise SLA Violation Risk Prediction
        queries.append({
            'name': 'Enterprise SLA Violation Risk Prediction',
            'description': 'Proactively identify service degradation affecting enterprise customers by analyzing failure patterns for enterprise subscribers, calculate SLA risk scores before violations occur and help desk is overwhelmed',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_enterprise_sla_risk',
                'description': 'Predicts SLA violation risk for enterprise customers by analyzing service degradation patterns. Calculates risk scores before violations occur. Critical for maintaining enterprise customer satisfaction.',
                'tags': ['enterprise', 'sla', 'risk-prediction', 'esql', 'customer-experience']
            },
            'query': '''FROM mme_failure_events
| LOOKUP JOIN subscriber_profiles ON imsi
| WHERE enterprise_account == true
| LOOKUP JOIN mme_hosts ON mme_host
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    enterprise_failures = COUNT(*),
    unique_enterprise_imsi = COUNT_DISTINCT(imsi),
    unique_procedures = COUNT_DISTINCT(procedure_type),
    failure_rate = COUNT(*)
  BY time_bucket, region, plan_type
| INLINESTATS 
    avg_failures = AVG(enterprise_failures),
    stddev_failures = STD_DEV(enterprise_failures),
    p95_failures = PERCENTILE(enterprise_failures, 95),
    avg_imsi = AVG(unique_enterprise_imsi)
  BY region
| EVAL 
    z_score = (enterprise_failures - avg_failures) / COALESCE(stddev_failures, 1),
    imsi_deviation = unique_enterprise_imsi - avg_imsi,
    sla_risk_score = (z_score * 0.6) + ((imsi_deviation / 10) * 0.4)
| WHERE z_score > 2.0 AND enterprise_failures > 10
| EVAL severity = CASE(
    sla_risk_score > 4 AND unique_enterprise_imsi > 20, "CRITICAL",
    sla_risk_score > 3 AND unique_enterprise_imsi > 10, "HIGH",
    "MEDIUM"
  )
| KEEP time_bucket, severity, unique_enterprise_imsi, enterprise_failures, sla_risk_score, region, plan_type
| SORT sla_risk_score DESC
| LIMIT 20''',
            'query_type': 'scripted',
            'pain_point': 'SLA violations with enterprise customers',
            'use_case': 'Filter noise and only alert on serious multi-dimensional problems affecting enterprise accounts'
        })

        # Query 5: Rogue Network and SS7 Security Attack Detection
        queries.append({
            'name': 'Rogue Network and SS7 Security Attack Detection',
            'description': 'Detect security attacks and rogue network attempts by identifying unusual PLMN patterns, unauthorized roaming attempts, and suspicious failure signatures using semantic search for known attack patterns',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_security_attack',
                'description': 'Detects rogue network attempts and SS7 security attacks through PLMN pattern analysis. Identifies unauthorized roaming and suspicious authentication attempts. Critical for network security and fraud prevention.',
                'tags': ['security', 'ss7', 'fraud-detection', 'esql', 'roaming']
            },
            'query': '''FROM mme_failure_events
| WHERE failure_code IN ("HSS-401", "NAS-301", "NAS-302", "EMM-001", "EMM-002", "EMM-003")
| LOOKUP JOIN subscriber_profiles ON imsi
| EVAL 
    time_bucket = DATE_TRUNC(5 minutes, @timestamp),
    plmn_mismatch = CASE(serving_plmn != home_plmn, 1, 0)
| STATS 
    attack_events = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    unique_plmn = COUNT_DISTINCT(serving_plmn),
    unique_tracking_areas = COUNT_DISTINCT(tracking_area_code),
    plmn_mismatches = SUM(plmn_mismatch)
  BY time_bucket, serving_plmn
| INLINESTATS 
    avg_events = AVG(attack_events),
    stddev_events = STD_DEV(attack_events),
    avg_plmn = AVG(unique_plmn)
  BY serving_plmn
| EVAL 
    z_score = (attack_events - avg_events) / COALESCE(stddev_events, 1),
    attack_diversity = unique_plmn + unique_tracking_areas,
    threat_score = (z_score * 0.5) + (attack_diversity * 0.3) + (plmn_mismatches * 0.2)
| WHERE z_score > 2.5 OR (unique_imsi > 20 AND plmn_mismatches > 10)
| EVAL severity = CASE(
    threat_score > 10 AND unique_imsi > 50, "CRITICAL",
    threat_score > 7 AND unique_imsi > 20, "HIGH",
    "MEDIUM"
  )
| KEEP time_bucket, severity, unique_imsi, attack_events, threat_score, serving_plmn, unique_plmn, plmn_mismatches
| SORT threat_score DESC
| LIMIT 20''',
            'query_type': 'scripted',
            'pain_point': 'Rogue network attempts and SS7 security attacks',
            'use_case': 'Detect security attacks or roaming misconfigurations'
        })

        # Query 6: HSS Database Synchronization Health Monitor
        queries.append({
            'name': 'HSS Database Synchronization Health Monitor',
            'description': 'Monitor HSS database replication lag and sync failures across partitions to identify database corruption issues before they impact subscriber authentication at scale',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_hss_sync_health',
                'description': 'Monitors HSS database synchronization health across all nodes and partitions. Detects replication lag and sync failures before mass authentication failures occur. Essential for proactive database maintenance.',
                'tags': ['hss', 'database', 'replication', 'esql', 'health-monitoring']
            },
            'query': '''FROM hss_sync_events
| WHERE sync_status IN ("Partial Failure", "Complete Failure", "Timeout", "Lag Warning")
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    sync_failures = COUNT(*),
    total_affected_imsi = SUM(affected_imsi_count),
    avg_replication_lag = AVG(replication_lag_ms),
    max_replication_lag = MAX(replication_lag_ms),
    unique_partitions = COUNT_DISTINCT(database_partition),
    unique_nodes = COUNT_DISTINCT(hss_node)
  BY time_bucket, sync_status
| INLINESTATS 
    avg_failures = AVG(sync_failures),
    stddev_failures = STD_DEV(sync_failures),
    p95_lag = PERCENTILE(avg_replication_lag, 95)
| EVAL 
    z_score = (sync_failures - avg_failures) / COALESCE(stddev_failures, 1),
    lag_severity = CASE(
        avg_replication_lag > 30000, "CRITICAL",
        avg_replication_lag > 15000, "HIGH",
        "MEDIUM"
    )
| WHERE z_score > 2 OR avg_replication_lag > 15000 OR total_affected_imsi > 100
| EVAL severity = CASE(
    z_score > 3 AND total_affected_imsi > 500, "CRITICAL",
    z_score > 2 AND total_affected_imsi > 100, "HIGH",
    "MEDIUM"
  )
| KEEP time_bucket, severity, sync_failures, total_affected_imsi, avg_replication_lag, max_replication_lag, unique_partitions, sync_status
| SORT z_score DESC
| LIMIT 20''',
            'query_type': 'scripted',
            'pain_point': 'HSS database corruption or synchronization issues affecting subscriber authentication',
            'use_case': 'Detect mass authentication failure events from HSS database issues'
        })

        # Query 7: MME Software Version Bug Pattern Analysis
        queries.append({
            'name': 'MME Software Version Bug Pattern Analysis',
            'description': 'Identify MME software bugs or resource exhaustion patterns by correlating failure rates with software versions and capacity utilization across different MME hosts',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_mme_software_bugs',
                'description': 'Identifies MME software bugs and resource exhaustion by version. Correlates failure patterns with software versions to detect bugs before total outage. Guides software upgrade priorities.',
                'tags': ['mme', 'software-bugs', 'capacity', 'esql', 'resource-exhaustion']
            },
            'query': '''FROM mme_failure_events
| LOOKUP JOIN mme_hosts ON mme_host
| EVAL time_bucket = DATE_TRUNC(10 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*),
    unique_subscribers = COUNT_DISTINCT(imsi),
    unique_procedures = COUNT_DISTINCT(procedure_type),
    unique_hosts = COUNT_DISTINCT(mme_host)
  BY time_bucket, software_version, datacenter
| INLINESTATS 
    avg_failures = AVG(failure_count),
    stddev_failures = STD_DEV(failure_count),
    avg_subscribers = AVG(unique_subscribers)
  BY software_version
| EVAL 
    z_score = (failure_count - avg_failures) / COALESCE(stddev_failures, 1),
    subscriber_impact = unique_subscribers - avg_subscribers,
    bug_probability = z_score * (unique_hosts / 5.0)
| WHERE z_score > 2.5 AND failure_count > 30
| EVAL severity = CASE(
    z_score > 4 AND unique_hosts >= 2, "CRITICAL",
    z_score > 3 AND unique_hosts >= 1, "HIGH",
    "MEDIUM"
  )
| KEEP time_bucket, severity, software_version, failure_count, unique_subscribers, unique_hosts, datacenter, bug_probability
| SORT bug_probability DESC
| LIMIT 20''',
            'query_type': 'scripted',
            'pain_point': 'MME software bugs and resource exhaustion causing service degradation',
            'use_case': 'Identify MME software bugs or resource exhaustion before total outage'
        })

        # Query 8: Regional Network Performance Comparison
        queries.append({
            'name': 'Regional Network Performance Comparison',
            'description': 'Compare network failure rates and patterns across regions and datacenters to identify systematic infrastructure issues and guide capacity planning',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_regional_performance',
                'description': 'Compares network performance across regions and datacenters. Identifies underperforming areas and systematic infrastructure issues. Guides capacity planning and resource allocation.',
                'tags': ['regional', 'performance', 'capacity-planning', 'esql', 'infrastructure']
            },
            'query': '''FROM mme_failure_events
| LOOKUP JOIN mme_hosts ON mme_host
| EVAL time_bucket = DATE_TRUNC(15 minutes, @timestamp)
| STATS 
    total_failures = COUNT(*),
    unique_subscribers = COUNT_DISTINCT(imsi),
    unique_cells = COUNT_DISTINCT(cell_id),
    unique_mme_hosts = COUNT_DISTINCT(mme_host),
    auth_failures = SUM(CASE(authentication_attempt == true, 1, 0)),
    handover_failures = SUM(CASE(handover_attempt == true, 1, 0))
  BY time_bucket, region, datacenter
| EVAL 
    failure_rate = TO_DOUBLE(total_failures) / unique_subscribers,
    auth_failure_pct = TO_DOUBLE(auth_failures) * 100.0 / total_failures,
    handover_failure_pct = TO_DOUBLE(handover_failures) * 100.0 / total_failures
| INLINESTATS 
    avg_failure_rate = AVG(failure_rate),
    stddev_failure_rate = STD_DEV(failure_rate)
  BY region
| EVAL 
    z_score = (failure_rate - avg_failure_rate) / COALESCE(stddev_failure_rate, 0.01),
    performance_score = 100 - (failure_rate * 100)
| WHERE total_failures > 20
| EVAL health_status = CASE(
    performance_score < 85, "DEGRADED",
    performance_score < 95, "WARNING",
    "HEALTHY"
  )
| KEEP time_bucket, region, datacenter, health_status, total_failures, unique_subscribers, failure_rate, performance_score, auth_failure_pct, handover_failure_pct
| SORT performance_score ASC
| LIMIT 25''',
            'query_type': 'scripted',
            'pain_point': 'Extended outages increasing customer churn probability',
            'use_case': 'Identify systematic infrastructure failures through pattern analysis'
        })

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries that accept user input
        
        These queries allow network operations teams to customize analysis
        by region, time range, failure type, and other dimensions.
        """
        queries = []

        # Query 1: Custom Time Range Authentication Failure Analysis
        queries.append({
            'name': 'Custom Time Range Authentication Failure Analysis',
            'description': 'Analyze authentication failures for a specific time range and region with customizable severity thresholds',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_auth_custom_time',
                'description': 'Analyzes authentication failures for user-specified time ranges and regions. Customizable thresholds for failure detection. Useful for investigating specific incidents or time periods.',
                'tags': ['authentication', 'parameterized', 'time-range', 'esql', 'custom-analysis']
            },
            'query': '''FROM mme_failure_events
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE authentication_attempt == true 
  AND failure_code IN ("HSS-401", "NAS-301", "NAS-302", "EMM-001", "EMM-002", "EMM-003")
| LOOKUP JOIN mme_hosts ON mme_host
| WHERE region == ?region
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    unique_mme = COUNT_DISTINCT(mme_host)
  BY time_bucket, datacenter
| WHERE failure_count > ?min_failure_threshold
| EVAL severity = CASE(
    failure_count > ?critical_threshold, "CRITICAL",
    failure_count > ?high_threshold, "HIGH",
    "MEDIUM"
  )
| KEEP time_bucket, datacenter, severity, failure_count, unique_imsi, unique_mme
| SORT failure_count DESC
| LIMIT 50''',
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
                    'name': 'region',
                    'type': 'keyword',
                    'description': 'Region to analyze (West, Central, Southeast, Midwest, Mountain)',
                    'required': True
                },
                {
                    'name': 'min_failure_threshold',
                    'type': 'integer',
                    'description': 'Minimum failure count to include in results',
                    'required': True,
                    'default': 10
                },
                {
                    'name': 'critical_threshold',
                    'type': 'integer',
                    'description': 'Failure count threshold for CRITICAL severity',
                    'required': True,
                    'default': 100
                },
                {
                    'name': 'high_threshold',
                    'type': 'integer',
                    'description': 'Failure count threshold for HIGH severity',
                    'required': True,
                    'default': 50
                }
            ],
            'pain_point': 'HSS database corruption or synchronization issues affecting subscriber authentication',
            'use_case': 'Alert on unusual subscriber authentication patterns before help desk is overwhelmed'
        })

        # Query 2: Cell Tower Handoff Analysis by Market
        queries.append({
            'name': 'Cell Tower Handoff Analysis by Market',
            'description': 'Analyze handoff failures for specific markets and technology types with customizable thresholds',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_handoff_by_market',
                'description': 'Analyzes handoff failures for specific markets and technology types. Customizable cell count thresholds for cascade detection. Helps isolate market-specific infrastructure issues.',
                'tags': ['handoff', 'market-analysis', 'parameterized', 'esql', 'technology']
            },
            'query': '''FROM mme_failure_events
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE handover_attempt == true 
  AND failure_code IN ("S1AP-201", "S1AP-202", "ESM-101", "ESM-102")
| LOOKUP JOIN cell_towers ON cell_id
| WHERE market_name == ?market_name
| WHERE technology == ?technology
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*),
    unique_cells = COUNT_DISTINCT(cell_id),
    unique_source_cells = COUNT_DISTINCT(source_cell_id),
    unique_target_cells = COUNT_DISTINCT(target_cell_id)
  BY time_bucket, power_source, tower_type
| WHERE unique_cells > ?min_cell_threshold
| EVAL severity = CASE(
    unique_cells > ?critical_cell_threshold, "CRITICAL",
    unique_cells > ?high_cell_threshold, "HIGH",
    "MEDIUM"
  )
| KEEP time_bucket, power_source, tower_type, severity, failure_count, unique_cells, unique_source_cells, unique_target_cells
| SORT unique_cells DESC
| LIMIT 50''',
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
                    'name': 'market_name',
                    'type': 'keyword',
                    'description': 'Market to analyze (e.g., "Denver Metro", "Miami Metro")',
                    'required': True
                },
                {
                    'name': 'technology',
                    'type': 'keyword',
                    'description': 'Technology type (LTE, LTE-Advanced, 5G-NR)',
                    'required': True
                },
                {
                    'name': 'min_cell_threshold',
                    'type': 'integer',
                    'description': 'Minimum affected cells to include in results',
                    'required': True,
                    'default': 5
                },
                {
                    'name': 'critical_cell_threshold',
                    'type': 'integer',
                    'description': 'Cell count threshold for CRITICAL severity',
                    'required': True,
                    'default': 20
                },
                {
                    'name': 'high_cell_threshold',
                    'type': 'integer',
                    'description': 'Cell count threshold for HIGH severity',
                    'required': True,
                    'default': 10
                }
            ],
            'pain_point': 'Radio equipment failure and cell site power failures affecting handoffs',
            'use_case': 'Identify cell tower handoff cascade failures from infrastructure problems'
        })

        # Query 3: Enterprise Subscriber Impact Analysis
        queries.append({
            'name': 'Enterprise Subscriber Impact Analysis',
            'description': 'Analyze service impact on enterprise subscribers by plan type and region with SLA threshold monitoring',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_enterprise_impact',
                'description': 'Analyzes service impact on enterprise subscribers by plan and region. Monitors SLA compliance with customizable thresholds. Critical for enterprise customer retention.',
                'tags': ['enterprise', 'sla', 'parameterized', 'esql', 'customer-impact']
            },
            'query': '''FROM mme_failure_events
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| LOOKUP JOIN subscriber_profiles ON imsi
| WHERE enterprise_account == true
| WHERE plan_type == ?plan_type
| LOOKUP JOIN mme_hosts ON mme_host
| WHERE region == ?region
| EVAL time_bucket = DATE_TRUNC(10 minutes, @timestamp)
| STATS 
    enterprise_failures = COUNT(*),
    unique_enterprise_imsi = COUNT_DISTINCT(imsi),
    unique_procedures = COUNT_DISTINCT(procedure_type)
  BY time_bucket, datacenter
| WHERE enterprise_failures > ?min_failure_threshold
| EVAL 
    failure_rate = TO_DOUBLE(enterprise_failures) / unique_enterprise_imsi,
    sla_risk = CASE(
        failure_rate > ?sla_critical_rate, "SLA_BREACH_RISK",
        failure_rate > ?sla_warning_rate, "SLA_WARNING",
        "SLA_COMPLIANT"
    )
| KEEP time_bucket, datacenter, sla_risk, enterprise_failures, unique_enterprise_imsi, failure_rate, unique_procedures
| SORT failure_rate DESC
| LIMIT 50''',
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
                    'name': 'plan_type',
                    'type': 'keyword',
                    'description': 'Enterprise plan type (Premium, Unlimited, Essential)',
                    'required': True
                },
                {
                    'name': 'region',
                    'type': 'keyword',
                    'description': 'Region to analyze (West, Central, Southeast, Midwest, Mountain)',
                    'required': True
                },
                {
                    'name': 'min_failure_threshold',
                    'type': 'integer',
                    'description': 'Minimum failure count to include in results',
                    'required': True,
                    'default': 5
                },
                {
                    'name': 'sla_critical_rate',
                    'type': 'double',
                    'description': 'Failure rate threshold for SLA breach risk (e.g., 0.05 = 5%)',
                    'required': True,
                    'default': 0.05
                },
                {
                    'name': 'sla_warning_rate',
                    'type': 'double',
                    'description': 'Failure rate threshold for SLA warning (e.g., 0.02 = 2%)',
                    'required': True,
                    'default': 0.02
                }
            ],
            'pain_point': 'SLA violations with enterprise customers',
            'use_case': 'Filter noise and only alert on serious multi-dimensional problems affecting enterprise accounts'
        })

        # Query 4: MME Cluster Health Analysis
        queries.append({
            'name': 'MME Cluster Health Analysis',
            'description': 'Analyze MME cluster health and detect split-brain conditions for specific clusters and datacenters',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_mme_cluster_health',
                'description': 'Analyzes MME cluster health and detects split-brain conditions. Monitors signaling storm patterns across cluster hosts. Essential for core network stability.',
                'tags': ['mme', 'cluster', 'parameterized', 'esql', 'health-monitoring']
            },
            'query': '''FROM mme_failure_events
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| LOOKUP JOIN mme_hosts ON mme_host
| WHERE cluster_id == ?cluster_id
| WHERE datacenter == ?datacenter
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    failure_count = COUNT(*),
    unique_mme_hosts = COUNT_DISTINCT(mme_host),
    unique_message_types = COUNT_DISTINCT(signaling_message_type),
    affected_subscribers = COUNT_DISTINCT(imsi)
  BY time_bucket, software_version
| WHERE unique_mme_hosts >= ?min_host_count
| EVAL 
    multi_host_failure = CASE(unique_mme_hosts >= 2, "YES", "NO"),
    cluster_health = CASE(
        unique_mme_hosts >= 3 AND failure_count > ?critical_threshold, "CRITICAL",
        unique_mme_hosts >= 2 AND failure_count > ?warning_threshold, "WARNING",
        "HEALTHY"
    )
| KEEP time_bucket, software_version, cluster_health, failure_count, unique_mme_hosts, affected_subscribers, multi_host_failure
| SORT failure_count DESC
| LIMIT 50''',
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
                    'name': 'cluster_id',
                    'type': 'keyword',
                    'description': 'MME cluster ID to analyze',
                    'required': True
                },
                {
                    'name': 'datacenter',
                    'type': 'keyword',
                    'description': 'Datacenter location (DC-Seattle, DC-Dallas, DC-Atlanta, DC-Chicago, DC-Denver)',
                    'required': True
                },
                {
                    'name': 'min_host_count',
                    'type': 'integer',
                    'description': 'Minimum affected hosts to include in results',
                    'required': True,
                    'default': 1
                },
                {
                    'name': 'critical_threshold',
                    'type': 'integer',
                    'description': 'Failure count threshold for CRITICAL health status',
                    'required': True,
                    'default': 100
                },
                {
                    'name': 'warning_threshold',
                    'type': 'integer',
                    'description': 'Failure count threshold for WARNING health status',
                    'required': True,
                    'default': 50
                }
            ],
            'pain_point': 'Core network split-brain and signaling storms causing cyclical failures',
            'use_case': 'Detect core network split-brain or signaling storms across multiple hosts'
        })

        # Query 5: Security Threat Analysis by PLMN
        queries.append({
            'name': 'Security Threat Analysis by PLMN',
            'description': 'Analyze potential security threats and rogue network attempts for specific PLMN codes and time ranges',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_security_plmn',
                'description': 'Analyzes security threats and rogue network attempts by PLMN code. Detects unauthorized roaming patterns and SS7 attacks. Critical for fraud prevention and network security.',
                'tags': ['security', 'plmn', 'parameterized', 'esql', 'fraud-detection']
            },
            'query': '''FROM mme_failure_events
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| WHERE failure_code IN ("HSS-401", "NAS-301", "NAS-302", "EMM-001", "EMM-002", "EMM-003")
| WHERE serving_plmn == ?serving_plmn
| LOOKUP JOIN subscriber_profiles ON imsi
| EVAL 
    time_bucket = DATE_TRUNC(5 minutes, @timestamp),
    plmn_mismatch = CASE(serving_plmn != home_plmn, 1, 0),
    roaming_violation = CASE(roaming_enabled == false AND serving_plmn != home_plmn, 1, 0)
| STATS 
    attack_events = COUNT(*),
    unique_imsi = COUNT_DISTINCT(imsi),
    unique_tracking_areas = COUNT_DISTINCT(tracking_area_code),
    plmn_mismatches = SUM(plmn_mismatch),
    roaming_violations = SUM(roaming_violation)
  BY time_bucket, home_plmn
| WHERE attack_events > ?min_event_threshold
| EVAL 
    threat_level = CASE(
        plmn_mismatches > ?critical_mismatch_threshold, "CRITICAL",
        plmn_mismatches > ?high_mismatch_threshold, "HIGH",
        "MEDIUM"
    ),
    mismatch_rate = TO_DOUBLE(plmn_mismatches) * 100.0 / attack_events
| KEEP time_bucket, home_plmn, threat_level, attack_events, unique_imsi, plmn_mismatches, roaming_violations, mismatch_rate
| SORT plmn_mismatches DESC
| LIMIT 50''',
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
                    'name': 'serving_plmn',
                    'type': 'keyword',
                    'description': 'Serving PLMN code to analyze (310-260, 310-800, 310-490)',
                    'required': True
                },
                {
                    'name': 'min_event_threshold',
                    'type': 'integer',
                    'description': 'Minimum attack events to include in results',
                    'required': True,
                    'default': 10
                },
                {
                    'name': 'critical_mismatch_threshold',
                    'type': 'integer',
                    'description': 'PLMN mismatch count threshold for CRITICAL threat level',
                    'required': True,
                    'default': 50
                },
                {
                    'name': 'high_mismatch_threshold',
                    'type': 'integer',
                    'description': 'PLMN mismatch count threshold for HIGH threat level',
                    'required': True,
                    'default': 20
                }
            ],
            'pain_point': 'Rogue network attempts and SS7 security attacks',
            'use_case': 'Detect security attacks or roaming misconfigurations'
        })

        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using COMPLETION command
        
        RAG queries use semantic search on failure_description field to provide
        intelligent answers about network failures, their causes, and remediation steps.
        """
        queries = []

        # Query 1: Network Failure Root Cause Analysis
        queries.append({
            'name': 'Network Failure Root Cause Analysis',
            'description': 'Use semantic search and LLM completion to analyze failure descriptions and provide root cause analysis and remediation recommendations',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_failure_root_cause',
                'description': 'Analyzes network failure descriptions using AI to identify root causes and suggest remediation. Searches failure patterns semantically and generates expert-level troubleshooting guidance.',
                'tags': ['rag', 'root-cause', 'ai-analysis', 'esql', 'troubleshooting']
            },
            'query': '''FROM mme_failure_events METADATA _id
| WHERE MATCH(failure_description, ?user_question)
| LOOKUP JOIN mme_hosts ON mme_host
| LOOKUP JOIN cell_towers ON cell_id
| KEEP 
    _id,
    @timestamp,
    failure_description,
    failure_code,
    procedure_type,
    mme_host,
    datacenter,
    region,
    cell_id,
    site_name,
    market_name,
    technology,
    power_source,
    _score
| SORT _score DESC
| LIMIT 5
| EVAL context = CONCAT(
    "Timestamp: ", TO_STRING(@timestamp), "\\n",
    "Failure: ", failure_description, "\\n",
    "Code: ", failure_code, "\\n",
    "Procedure: ", procedure_type, "\\n",
    "MME Host: ", mme_host, " (", datacenter, ", ", region, ")\\n",
    "Cell: ", cell_id, " - ", site_name, " (", market_name, ", ", technology, ")\\n",
    "Power Source: ", power_source
  )
| EVAL prompt = CONCAT(
    "You are a T-Mobile network operations expert analyzing mobile network failures. ",
    "Based on these failure events, answer the question: ", ?user_question, "\\n\\n",
    "Network Failure Context:\\n", context, "\\n\\n",
    "Provide a detailed technical analysis including:\\n",
    "1. Root cause identification\\n",
    "2. Impact assessment (subscribers, services, regions affected)\\n",
    "3. Immediate remediation steps\\n",
    "4. Long-term prevention recommendations"
  )
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP @timestamp, failure_description, mme_host, datacenter, cell_id, market_name, answer
| LIMIT 1''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Question about network failures (e.g., "What is causing HSS authentication failures?")',
                    'required': True
                }
            ],
            'pain_point': 'Extended outages increasing customer churn probability',
            'use_case': 'Identify systematic infrastructure failures through pattern analysis'
        })

        # Query 2: Handoff Failure Troubleshooting Assistant
        queries.append({
            'name': 'Handoff Failure Troubleshooting Assistant',
            'description': 'Use semantic search to find similar handoff failures and generate AI-powered troubleshooting guidance with cell tower context',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_handoff_troubleshoot',
                'description': 'Provides AI-powered troubleshooting for handoff failures. Searches similar failure patterns and generates step-by-step remediation guides with cell tower infrastructure context.',
                'tags': ['rag', 'handoff', 'troubleshooting', 'esql', 'ai-assistant']
            },
            'query': '''FROM mme_failure_events METADATA _id
| WHERE handover_attempt == true
| WHERE MATCH(failure_description, ?user_question)
| LOOKUP JOIN cell_towers ON cell_id
| EVAL source_cell_info = CONCAT("Source Cell: ", source_cell_id)
| EVAL target_cell_info = CONCAT("Target Cell: ", target_cell_id)
| KEEP 
    _id,
    @timestamp,
    failure_description,
    failure_code,
    source_cell_id,
    target_cell_id,
    cell_id,
    site_name,
    market_name,
    technology,
    power_source,
    tower_type,
    frequency_band,
    _score
| SORT _score DESC
| LIMIT 5
| EVAL context = CONCAT(
    "Timestamp: ", TO_STRING(@timestamp), "\\n",
    "Failure: ", failure_description, "\\n",
    "Code: ", failure_code, "\\n",
    "Source Cell: ", source_cell_id, "\\n",
    "Target Cell: ", target_cell_id, "\\n",
    "Cell Site: ", site_name, " (", market_name, ")\\n",
    "Technology: ", technology, " - ", frequency_band, "\\n",
    "Tower Type: ", tower_type, "\\n",
    "Power Source: ", power_source
  )
| EVAL prompt = CONCAT(
    "You are a T-Mobile RF engineer troubleshooting cell tower handoff failures. ",
    "Answer this question: ", ?user_question, "\\n\\n",
    "Handoff Failure Context:\\n", context, "\\n\\n",
    "Provide specific troubleshooting guidance including:\\n",
    "1. Likely causes based on cell configuration and technology\\n",
    "2. Infrastructure issues to check (power, equipment, neighbor relations)\\n",
    "3. Step-by-step diagnostic procedures\\n",
    "4. Configuration changes or fixes to implement"
  )
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP @timestamp, failure_description, source_cell_id, target_cell_id, site_name, market_name, technology, answer
| LIMIT 1''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Question about handoff failures (e.g., "Why are handoffs failing in Miami Metro?")',
                    'required': True
                }
            ],
            'pain_point': 'Radio equipment failure and cell site power failures affecting handoffs',
            'use_case': 'Identify cell tower handoff cascade failures from infrastructure problems'
        })

        # Query 3: Security Incident Analysis Assistant
        queries.append({
            'name': 'Security Incident Analysis Assistant',
            'description': 'Use semantic search to analyze security-related failures and generate AI-powered threat assessment and response recommendations',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_security_analysis',
                'description': 'Analyzes security incidents and potential attacks using AI. Searches for attack patterns in failure descriptions and generates threat assessments with response recommendations.',
                'tags': ['rag', 'security', 'threat-analysis', 'esql', 'ai-assistant']
            },
            'query': '''FROM mme_failure_events METADATA _id
| WHERE failure_code IN ("HSS-401", "NAS-301", "NAS-302", "EMM-001", "EMM-002", "EMM-003")
| WHERE MATCH(failure_description, ?user_question)
| LOOKUP JOIN subscriber_profiles ON imsi
| KEEP 
    _id,
    @timestamp,
    failure_description,
    failure_code,
    serving_plmn,
    home_plmn,
    tracking_area_code,
    imsi,
    subscriber_type,
    roaming_enabled,
    device_type,
    _score
| SORT _score DESC
| LIMIT 5
| EVAL context = CONCAT(
    "Timestamp: ", TO_STRING(@timestamp), "\\n",
    "Failure: ", failure_description, "\\n",
    "Code: ", failure_code, "\\n",
    "Serving PLMN: ", serving_plmn, "\\n",
    "Home PLMN: ", home_plmn, "\\n",
    "Tracking Area: ", tracking_area_code, "\\n",
    "Subscriber Type: ", subscriber_type, "\\n",
    "Roaming Enabled: ", TO_STRING(roaming_enabled), "\\n",
    "Device Type: ", device_type
  )
| EVAL prompt = CONCAT(
    "You are a T-Mobile network security analyst investigating potential security threats. ",
    "Answer this question: ", ?user_question, "\\n\\n",
    "Security Event Context:\\n", context, "\\n\\n",
    "Provide a comprehensive security analysis including:\\n",
    "1. Threat assessment (attack type, severity, indicators of compromise)\\n",
    "2. Affected subscribers and potential data exposure\\n",
    "3. Immediate containment actions\\n",
    "4. Investigation steps and evidence collection\\n",
    "5. Long-term security hardening recommendations"
  )
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}
| KEEP @timestamp, failure_description, serving_plmn, home_plmn, subscriber_type, roaming_enabled, answer
| LIMIT 1''',
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'text',
                    'description': 'Question about security incidents (e.g., "Are we seeing SS7 attacks or roaming fraud?")',
                    'required': True
                }
            ],
            'pain_point': 'Rogue network attempts and SS7 security attacks',
            'use_case': 'Detect security attacks or roaming misconfigurations'
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum impact
        
        Builds a narrative from basic failure detection to advanced
        predictive analysis and AI-powered troubleshooting.
        """
        return [
            # Start with immediate threats - authentication failures
            'Mass Subscriber Authentication Failure Detection',
            
            # Infrastructure cascade failures
            'Cell Tower Handoff Cascade Failure Analysis',
            
            # Core network stability
            'MME Split-Brain and Signaling Storm Detection',
            
            # Customer impact focus
            'Enterprise SLA Violation Risk Prediction',
            
            # Security threats
            'Rogue Network and SS7 Security Attack Detection',
            
            # Proactive monitoring
            'HSS Database Synchronization Health Monitor',
            
            # Software quality
            'MME Software Version Bug Pattern Analysis',
            
            # Strategic overview
            'Regional Network Performance Comparison',
            
            # Parameterized queries for custom analysis
            'Custom Time Range Authentication Failure Analysis',
            'Cell Tower Handoff Analysis by Market',
            'Enterprise Subscriber Impact Analysis',
            'MME Cluster Health Analysis',
            'Security Threat Analysis by PLMN',
            
            # AI-powered troubleshooting
            'Network Failure Root Cause Analysis',
            'Handoff Failure Troubleshooting Assistant',
            'Security Incident Analysis Assistant'
        ]
