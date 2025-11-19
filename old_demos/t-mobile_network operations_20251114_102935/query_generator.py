
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class TMobileQueryGenerator(QueryGeneratorModule):
    """Query generator for T-Mobile - Network Operations"""

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate ALL ES|QL queries from pre-planned strategy
        
        CRITICAL: Categorize each query with query_type field:
        - "scripted": Basic queries that don't take user parameters
        - "parameterized": Queries that can be customized with user input
        - "rag": RAG queries using MATCH -> RERANK -> COMPLETION pipeline
        """
        queries = []

        # Query 1: Core Network Split-Brain Detection with Multi-MME Context Conflict
        queries.append({
            'name': 'Core Network Split-Brain Detection with Multi-MME Context Conflict',
            'description': 'Detects split-brain conditions by identifying clusters where multiple MME hosts are processing signaling for the same IMSI within short time windows, indicating duplicate subscriber context ownership. Uses statistical analysis to identify abnormal multi-MME activity patterns that precede signaling storms.',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_split_brain_detection',
                'description': 'Detects core network split-brain conditions where multiple MME hosts claim ownership of same subscriber contexts. Identifies signaling storms and context conflicts before they cause widespread service disruption.',
                'tags': ['network', 'split-brain', 'mme', 'critical', 'esql']
            },
            'query': """FROM mme_signaling_events
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS 
    unique_mmes = COUNT_DISTINCT(mme_host),
    total_events = COUNT(*),
    unique_subscribers = COUNT_DISTINCT(imsi_hash)
  BY time_bucket, cluster_id, datacenter
| WHERE unique_mmes >= 2
| INLINESTATS 
    avg_mmes = AVG(unique_mmes),
    p95_mmes = PERCENTILE(unique_mmes, 95)
  BY cluster_id
| EVAL split_brain_severity = CASE(
    unique_mmes >= 4, "CRITICAL",
    unique_mmes >= 3, "HIGH",
    "MEDIUM"
  )
| KEEP cluster_id, split_brain_severity, unique_mmes, unique_subscribers, total_events, time_bucket, datacenter
| SORT unique_mmes DESC
| LIMIT 20""",
            'query_type': 'scripted',
            'pain_point': 'Split-brain conditions where multiple MMEs claim ownership of same subscriber contexts cause signaling storms and session establishment failures, overwhelming diameter routing agents and HSS capacity. Current tools cannot detect duplicate transaction IDs or abnormal signaling patterns indicating split-brain scenarios.'
        })

        # Query 2: HSS Authentication Transaction Failure Analysis with Database Node Correlation
        queries.append({
            'name': 'HSS Authentication Transaction Failure Analysis with Database Node Correlation',
            'description': 'Analyzes HSS authentication transaction success rates (AIR command code) correlated with specific HSS nodes to identify database replication issues or node-specific failures. Uses z-score analysis to detect abnormal response times indicating database query performance degradation.',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_hss_auth_analysis',
                'description': 'Analyzes HSS authentication transaction failures and correlates with specific database nodes. Identifies replication lag, corruption, and node-specific performance issues affecting subscriber authentication.',
                'tags': ['hss', 'authentication', 'database', 'performance', 'esql']
            },
            'query': """FROM diameter_transactions
| WHERE command_code == "Authentication-Information"
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS 
    auth_attempts = COUNT(*),
    auth_failures = COUNT(*) WHERE transaction_success == false,
    avg_response_ms = AVG(response_time_ms),
    p95_response_ms = PERCENTILE(response_time_ms, 95)
  BY time_bucket, hss_node
| EVAL success_rate_pct = ((auth_attempts - auth_failures) / auth_attempts) * 100
| INLINESTATS 
    avg_success = AVG(success_rate_pct),
    stddev_success = STD_DEV(success_rate_pct),
    avg_latency = AVG(avg_response_ms),
    stddev_latency = STD_DEV(avg_response_ms)
| EVAL success_z_score = (success_rate_pct - avg_success) / COALESCE(stddev_success, 1)
| EVAL latency_z_score = (avg_response_ms - avg_latency) / COALESCE(stddev_latency, 1)
| WHERE success_rate_pct < 98 OR latency_z_score > 2.5
| EVAL health_status = CASE(
    success_rate_pct < 95, "CRITICAL",
    success_rate_pct < 98, "DEGRADED",
    "WARNING"
  )
| KEEP hss_node, health_status, success_rate_pct, auth_failures, p95_response_ms, time_bucket
| SORT success_rate_pct ASC
| LIMIT 25""",
            'query_type': 'scripted',
            'pain_point': 'HSS database replication lag and corruption cause authentication failures affecting subscriber attach procedures, but current monitoring only tracks database-level metrics without correlating actual authentication transaction success rates with specific HSS node performance.'
        })

        # Query 3: Cell Handoff Cascade Failure Pattern Detection with Geographic Clustering
        queries.append({
            'name': 'Cell Handoff Cascade Failure Pattern Detection with Geographic Clustering',
            'description': 'Identifies cascade failure patterns where a single problematic cell causes handoff failures to multiple neighboring cells. Analyzes handoff success rates for cell pairs and detects when 3+ target cells sharing the same source cell show degraded handoff performance, indicating a source cell issue.',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_handoff_cascade',
                'description': 'Identifies cell handoff cascade failures where one problematic cell causes failures across multiple neighbors. Detects widespread dropped calls and data session interruptions from cascading cell tower issues.',
                'tags': ['handoff', 'cell-tower', 'cascade', 'radio', 'esql']
            },
            'query': """FROM handoff_events
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS 
    total_handoffs = COUNT(*),
    failed_handoffs = COUNT(*) WHERE handoff_result == "failure",
    unique_target_cells = COUNT_DISTINCT(target_cell_id)
  BY time_bucket, source_cell_id
| EVAL handoff_success_rate = ((total_handoffs - failed_handoffs) / total_handoffs) * 100
| WHERE handoff_success_rate < 90 AND unique_target_cells >= 3
| EVAL cascade_severity = CASE(
    handoff_success_rate < 70, "CRITICAL",
    handoff_success_rate < 85, "HIGH",
    "MEDIUM"
  )
| KEEP source_cell_id, cascade_severity, handoff_success_rate, failed_handoffs, unique_target_cells, time_bucket
| SORT failed_handoffs DESC
| LIMIT 20""",
            'query_type': 'scripted',
            'pain_point': 'Cell tower handoff failures cascade across multiple adjacent cells causing widespread dropped calls and data session interruptions, but current vendor-specific monitoring systems operate in silos making it impossible to identify cascading handoff failures across multiple cell sites.'
        })

        # Query 4: Proactive MME Attach Procedure Degradation Detection with Multi-Dimensional Analysis
        queries.append({
            'name': 'Proactive MME Attach Procedure Degradation Detection with Multi-Dimensional Analysis',
            'description': 'Detects attach procedure degradation using statistical z-score analysis across MME hosts and cells. Identifies abnormal failure patterns 10-15 minutes before customer impact by comparing current attach success rates against baseline patterns, with drill-down to specific reject causes and affected cells.',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_attach_degradation',
                'description': 'Detects MME attach procedure degradation 10-15 minutes before help desk is overwhelmed. Uses statistical analysis to identify abnormal failure patterns and prevent customer-facing outages.',
                'tags': ['mme', 'attach', 'proactive', 'degradation', 'esql']
            },
            'query': """FROM mme_signaling_events
| WHERE procedure_type == "Attach"
| EVAL time_bucket = DATE_TRUNC(15 minutes, @timestamp)
| STATS 
    attach_attempts = COUNT(*),
    attach_failures = COUNT(*) WHERE procedure_result == "failure",
    unique_cells = COUNT_DISTINCT(cell_id)
  BY time_bucket, mme_host
| EVAL success_rate_pct = ((attach_attempts - attach_failures) / attach_attempts) * 100
| INLINESTATS 
    avg_success = AVG(success_rate_pct),
    stddev_success = STD_DEV(success_rate_pct),
    p95_success = PERCENTILE(success_rate_pct, 95)
| EVAL z_score = (success_rate_pct - avg_success) / COALESCE(stddev_success, 1)
| WHERE success_rate_pct < 95 OR z_score < -2.5
| EVAL alert_severity = CASE(
    success_rate_pct < 90, "CRITICAL",
    success_rate_pct < 95, "HIGH",
    "MEDIUM"
  )
| KEEP mme_host, alert_severity, success_rate_pct, attach_failures, unique_cells, time_bucket, z_score
| SORT success_rate_pct ASC
| LIMIT 25""",
            'query_type': 'scripted',
            'pain_point': 'Network Operations Center relies on customer complaints and help desk ticket volume to identify network degradation, resulting in MTTD exceeding 15-20 minutes. Need to detect attach procedure failures 10-15 minutes before help desk is overwhelmed by identifying abnormal signaling patterns.'
        })

        # Query 5: Subscriber Service Request Failure Root Cause Analysis with Device and Cell Correlation
        queries.append({
            'name': 'Subscriber Service Request Failure Root Cause Analysis with Device and Cell Correlation',
            'description': 'Performs root cause analysis of service request failures by correlating failure patterns with cell capacity metrics and procedure latency. Identifies dominant failure causes (paging failure, RRC timeout, MME reject) and pinpoints capacity-constrained cells or technology-specific issues requiring targeted optimization.',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_service_request_rca',
                'description': 'Performs root cause analysis of UE-initiated service request failures. Identifies whether issues stem from radio problems, core network congestion, or device issues to guide optimization efforts.',
                'tags': ['service-request', 'root-cause', 'optimization', 'ue', 'esql']
            },
            'query': """FROM mme_signaling_events
| WHERE procedure_type == "Service Request"
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS 
    total_requests = COUNT(*),
    failed_requests = COUNT(*) WHERE procedure_result == "failure",
    avg_latency_ms = AVG(procedure_latency_ms),
    p95_latency_ms = PERCENTILE(procedure_latency_ms, 95)
  BY time_bucket, cell_id, reject_cause
| EVAL success_rate_pct = ((total_requests - failed_requests) / total_requests) * 100
| WHERE success_rate_pct < 95
| KEEP cell_id, success_rate_pct, failed_requests, reject_cause, p95_latency_ms, time_bucket
| SORT failed_requests DESC
| LIMIT 30""",
            'query_type': 'scripted',
            'pain_point': 'UE-initiated service request failures cause poor user experience but root cause identification is difficult - could be radio issues, core network congestion, or device problems. Need deep-dive analysis to optimize network resource allocation and identify problematic device models or congested cells.'
        })

        # Query 6: MME Software Bug and Resource Exhaustion Detection
        queries.append({
            'name': 'MME Software Bug and Resource Exhaustion Detection',
            'description': 'Identifies MME hosts experiencing abnormal procedure failure rates or latency spikes that indicate software bugs or resource exhaustion. Correlates failure patterns with specific procedure types and MME versions to pinpoint software defects requiring patches or capacity upgrades.',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_mme_health',
                'description': 'Identifies MME software bugs and resource exhaustion by analyzing procedure failure rates and latency patterns. Detects issues before they cause widespread service impact.',
                'tags': ['mme', 'software', 'capacity', 'health', 'esql']
            },
            'query': """FROM mme_signaling_events
| EVAL time_bucket = DATE_TRUNC(15 minutes, @timestamp)
| STATS 
    total_procedures = COUNT(*),
    failures = COUNT(*) WHERE procedure_result IN ("failure", "timeout"),
    avg_latency = AVG(procedure_latency_ms),
    p95_latency = PERCENTILE(procedure_latency_ms, 95)
  BY time_bucket, mme_host, procedure_type
| EVAL failure_rate_pct = (TO_DOUBLE(failures) * 100.0) / total_procedures
| INLINESTATS 
    avg_failure_rate = AVG(failure_rate_pct),
    stddev_failure_rate = STD_DEV(failure_rate_pct)
  BY mme_host
| EVAL z_score = (failure_rate_pct - avg_failure_rate) / COALESCE(stddev_failure_rate, 1)
| WHERE failure_rate_pct > 5 OR z_score > 3.0 OR p95_latency > 500
| EVAL health_status = CASE(
    failure_rate_pct > 10 OR p95_latency > 1000, "CRITICAL",
    failure_rate_pct > 5 OR p95_latency > 500, "WARNING",
    "DEGRADED"
  )
| KEEP mme_host, procedure_type, health_status, failure_rate_pct, failures, p95_latency, time_bucket
| SORT failure_rate_pct DESC
| LIMIT 25""",
            'query_type': 'scripted',
            'pain_point': 'MME software bugs and resource exhaustion cause unpredictable service degradation but are difficult to detect proactively. Need to identify abnormal failure patterns and latency spikes that indicate software defects or capacity issues before widespread customer impact.'
        })

        # Query 7: IMSI and Cell ID Cardinality Anomaly Detection
        queries.append({
            'name': 'IMSI and Cell ID Cardinality Anomaly Detection',
            'description': 'Tracks unique IMSI and cell ID cardinality changes over time to detect mass authentication failures, cell tower outages, or network partitioning. Sudden drops in unique subscriber counts or cell activity indicate systemic issues requiring immediate investigation.',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_cardinality_anomaly',
                'description': 'Tracks unique IMSI and cell ID cardinality changes over time. Detects mass authentication failures, cell tower outages, or network partitioning by identifying sudden drops in subscriber or cell activity.',
                'tags': ['cardinality', 'anomaly', 'imsi', 'cell', 'esql']
            },
            'query': """FROM mme_signaling_events
| EVAL time_bucket = DATE_TRUNC(15 minutes, @timestamp)
| STATS 
    unique_subscribers = COUNT_DISTINCT(imsi_hash),
    unique_cells = COUNT_DISTINCT(cell_id),
    total_events = COUNT(*)
  BY time_bucket, datacenter
| INLINESTATS 
    avg_subscribers = AVG(unique_subscribers),
    stddev_subscribers = STD_DEV(unique_subscribers),
    avg_cells = AVG(unique_cells),
    stddev_cells = STD_DEV(unique_cells)
  BY datacenter
| EVAL subscriber_z_score = (unique_subscribers - avg_subscribers) / COALESCE(stddev_subscribers, 1)
| EVAL cell_z_score = (unique_cells - avg_cells) / COALESCE(stddev_cells, 1)
| WHERE subscriber_z_score < -2.0 OR cell_z_score < -2.0
| EVAL anomaly_type = CASE(
    subscriber_z_score < -2.0 AND cell_z_score < -2.0, "MASS_OUTAGE",
    subscriber_z_score < -2.0, "AUTHENTICATION_FAILURE",
    "CELL_OUTAGE"
  )
| KEEP datacenter, anomaly_type, unique_subscribers, unique_cells, total_events, time_bucket, subscriber_z_score, cell_z_score
| SORT subscriber_z_score ASC
| LIMIT 20""",
            'query_type': 'scripted',
            'pain_point': 'Need to detect network issues before help desk is overwhelmed. Tracking unique IMSI and cell ID cardinality changes helps identify mass authentication failures, cell tower outages, or network partitioning early.'
        })

        # Query 8: Signaling Storm Detection Across Multiple MME Hosts
        queries.append({
            'name': 'Signaling Storm Detection Across Multiple MME Hosts',
            'description': 'Detects signaling storms by identifying sustained spikes in signaling event rates across multiple MME hosts. Uses statistical analysis to differentiate normal traffic bursts from pathological signaling storms that can overwhelm core network capacity.',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_signaling_storm',
                'description': 'Detects signaling storms by identifying sustained spikes in event rates across multiple MME hosts. Differentiates normal traffic bursts from pathological storms that overwhelm core network capacity.',
                'tags': ['signaling', 'storm', 'capacity', 'mme', 'esql']
            },
            'query': """FROM mme_signaling_events
| EVAL time_bucket = DATE_TRUNC(5 minutes, @timestamp)
| STATS 
    event_count = COUNT(*),
    unique_mmes = COUNT_DISTINCT(mme_host)
  BY time_bucket, cluster_id
| INLINESTATS 
    avg_events = AVG(event_count),
    stddev_events = STD_DEV(event_count),
    p95_events = PERCENTILE(event_count, 95)
  BY cluster_id
| EVAL z_score = (event_count - avg_events) / COALESCE(stddev_events, 1)
| WHERE z_score > 3.0 AND unique_mmes >= 2
| EVAL storm_severity = CASE(
    z_score > 5.0, "CRITICAL",
    z_score > 4.0, "HIGH",
    "MEDIUM"
  )
| KEEP cluster_id, storm_severity, event_count, unique_mmes, time_bucket, z_score, p95_events
| SORT z_score DESC
| LIMIT 20""",
            'query_type': 'scripted',
            'pain_point': 'Core network split-brain and signaling storms overwhelm diameter routing agents and HSS capacity. Need to detect sustained spike patterns across multiple lag periods before system-wide failure.'
        })

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries that accept user input
        
        These are Agent Builder Tool queries that let users customize parameters.
        Include parameter definitions for each query.
        """
        queries = []

        # Query 1: SS7 Security Attack Detection with Semantic Pattern Analysis and Subscriber Impact
        queries.append({
            'name': 'SS7 Security Attack Detection with Semantic Pattern Analysis and Subscriber Impact',
            'description': 'Detects SS7 security attacks using semantic analysis of attack descriptions to identify sophisticated exploitation patterns. Aggregates attacks by source network and type, calculates affected subscriber counts, and prioritizes based on severity and blocking success.',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_ss7_security',
                'description': 'Detects SS7 security attacks in real-time using semantic pattern analysis. Identifies location tracking, SMS interception, and fraud attempts from rogue operators with affected subscriber counts and threat levels.',
                'tags': ['ss7', 'security', 'attack', 'fraud', 'esql']
            },
            'query': """FROM security_events
| WHERE event_type == ?event_type
| WHERE MATCH(attack_description, ?search_terms)
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS 
    attack_count = COUNT(*),
    blocked_count = COUNT(*) WHERE blocked == true,
    affected_subscribers = COUNT_DISTINCT(target_imsi_hash),
    unique_sources = COUNT_DISTINCT(source_global_title)
  BY time_bucket, attack_type, source_network, severity
| EVAL block_rate_pct = (TO_DOUBLE(blocked_count) * 100.0) / attack_count
| WHERE attack_count >= 5
| EVAL threat_level = CASE(
    severity == "critical" AND block_rate_pct < 90, "ACTIVE_THREAT",
    severity == "critical", "BLOCKED_CRITICAL",
    severity == "high", "HIGH_RISK",
    "MONITORED"
  )
| KEEP attack_type, threat_level, attack_count, affected_subscribers, block_rate_pct, time_bucket, source_network, severity, unique_sources
| SORT attack_count DESC
| LIMIT 30""",
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'event_type',
                    'type': 'string',
                    'description': 'Type of security event to analyze',
                    'default': 'SS7_Attack',
                    'required': True
                },
                {
                    'name': 'search_terms',
                    'type': 'string',
                    'description': 'Search terms for semantic matching in attack descriptions',
                    'default': 'location tracking SMS interception fraud',
                    'required': True
                }
            ],
            'pain_point': 'SS7 protocol exploitation for location tracking, SMS interception, and fraud attacks from rogue operators are detected too late (24-48 hours via billing systems). Need real-time detection of SS7 attacks correlated with network performance impact and affected subscriber counts.'
        })

        # Query 2: Revenue Impact Calculation for Network Incidents with Customer Segment Analysis
        queries.append({
            'name': 'Revenue Impact Calculation for Network Incidents with Customer Segment Analysis',
            'description': 'Calculates real-time revenue impact of network incidents by analyzing failed sessions, correlating with customer segment ARPU, and computing estimated revenue loss and SLA penalty exposure. Provides executive-level business impact metrics within minutes of incident detection.',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_revenue_impact',
                'description': 'Calculates real-time revenue impact of network incidents by customer segment. Computes estimated revenue loss and SLA penalties to provide executive-level business impact metrics within minutes.',
                'tags': ['revenue', 'sla', 'business', 'impact', 'esql']
            },
            'query': """FROM subscriber_sessions
| WHERE session_result == ?session_result
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS 
    affected_subscribers = COUNT_DISTINCT(imsi_hash),
    failed_sessions = COUNT(*)
  BY time_bucket, mme_host
| EVAL avg_duration_hours = 0.5
| EVAL hourly_arpu = 50.0 / 730.0
| EVAL sla_penalty_per_hour = 100.0
| EVAL estimated_revenue_loss = affected_subscribers * hourly_arpu * avg_duration_hours
| EVAL estimated_sla_penalty = affected_subscribers * sla_penalty_per_hour * avg_duration_hours
| EVAL total_financial_impact = estimated_revenue_loss + estimated_sla_penalty
| WHERE affected_subscribers >= ?min_subscribers
| EVAL impact_severity = CASE(
    total_financial_impact > 10000, "CRITICAL",
    total_financial_impact > 5000, "HIGH",
    "MEDIUM"
  )
| KEEP mme_host, impact_severity, affected_subscribers, estimated_revenue_loss, estimated_sla_penalty, total_financial_impact, time_bucket
| SORT total_financial_impact DESC
| LIMIT 20""",
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'session_result',
                    'type': 'string',
                    'description': 'Session result to analyze (e.g., failure, timeout)',
                    'default': 'failure',
                    'required': True
                },
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
                    'name': 'min_subscribers',
                    'type': 'integer',
                    'description': 'Minimum number of affected subscribers to include',
                    'default': 100,
                    'required': True
                }
            ],
            'pain_point': 'Network outages directly impact revenue and trigger SLA penalties, but current reporting cannot quickly quantify business impact or identify which customer segments are affected. A single MME failure affecting 10,000 subscribers for 30 minutes represents $15,000-25,000 in lost revenue but takes hours to calculate manually.'
        })

        # Query 3: Handoff Failure Analysis by Cell Technology and Region
        queries.append({
            'name': 'Handoff Failure Analysis by Cell Technology and Region',
            'description': 'Analyzes handoff failures by cell technology (4G/5G) and geographic region to identify technology-specific issues or regional network problems. Helps prioritize network optimization efforts and technology migration strategies.',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_handoff_tech_analysis',
                'description': 'Analyzes handoff failures by cell technology and region. Identifies technology-specific issues (4G vs 5G) and regional network problems to guide optimization and migration strategies.',
                'tags': ['handoff', 'technology', 'regional', 'optimization', 'esql']
            },
            'query': """FROM handoff_events
| WHERE handoff_result == ?handoff_result
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS 
    total_handoffs = COUNT(*),
    avg_latency = AVG(handoff_latency_ms),
    p95_latency = PERCENTILE(handoff_latency_ms, 95),
    unique_subscribers = COUNT_DISTINCT(imsi_hash)
  BY time_bucket, source_cell_id, failure_reason
| WHERE total_handoffs >= ?min_handoffs
| KEEP source_cell_id, total_handoffs, avg_latency, p95_latency, unique_subscribers, failure_reason, time_bucket
| SORT total_handoffs DESC
| LIMIT 25""",
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'handoff_result',
                    'type': 'string',
                    'description': 'Handoff result to analyze (success, failure, timeout)',
                    'default': 'failure',
                    'required': True
                },
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
                    'name': 'min_handoffs',
                    'type': 'integer',
                    'description': 'Minimum number of handoffs to include in results',
                    'default': 10,
                    'required': True
                }
            ],
            'pain_point': 'Radio equipment failure and cell tower handoff failures cause dropped calls during mobility and interrupted data sessions. Need to analyze handoff patterns by technology and region to prioritize optimization efforts.'
        })

        # Query 4: MME Procedure Performance by Datacenter and Cluster
        queries.append({
            'name': 'MME Procedure Performance by Datacenter and Cluster',
            'description': 'Analyzes MME procedure performance across datacenters and clusters to identify geographic or infrastructure-specific issues. Compares success rates and latency metrics to guide capacity planning and failover strategies.',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_mme_datacenter_perf',
                'description': 'Analyzes MME procedure performance across datacenters and clusters. Identifies geographic or infrastructure-specific issues to guide capacity planning and failover strategies.',
                'tags': ['mme', 'datacenter', 'performance', 'capacity', 'esql']
            },
            'query': """FROM mme_signaling_events
| WHERE procedure_type == ?procedure_type
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS 
    total_procedures = COUNT(*),
    failures = COUNT(*) WHERE procedure_result IN ("failure", "timeout", "rejected"),
    avg_latency = AVG(procedure_latency_ms),
    p95_latency = PERCENTILE(procedure_latency_ms, 95)
  BY time_bucket, datacenter, cluster_id
| EVAL success_rate_pct = ((total_procedures - failures) / total_procedures) * 100
| WHERE total_procedures >= ?min_procedures
| KEEP datacenter, cluster_id, success_rate_pct, failures, avg_latency, p95_latency, time_bucket
| SORT success_rate_pct ASC
| LIMIT 25""",
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'procedure_type',
                    'type': 'string',
                    'description': 'MME procedure type to analyze (Attach, TAU, Service Request, etc.)',
                    'default': 'Attach',
                    'required': True
                },
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
                    'name': 'min_procedures',
                    'type': 'integer',
                    'description': 'Minimum number of procedures to include in results',
                    'default': 100,
                    'required': True
                }
            ],
            'pain_point': 'MME software bugs and resource exhaustion affect specific datacenters or clusters differently. Need to compare performance across infrastructure to identify capacity constraints and guide failover strategies.'
        })

        # Query 5: Diameter Transaction Performance by Command Code
        queries.append({
            'name': 'Diameter Transaction Performance by Command Code',
            'description': 'Analyzes diameter transaction performance by command code to identify HSS database performance issues for specific operations. Tracks authentication, location updates, and subscriber data operations separately.',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_diameter_cmd_perf',
                'description': 'Analyzes diameter transaction performance by command code. Identifies HSS database performance issues for specific operations like authentication, location updates, and subscriber data queries.',
                'tags': ['diameter', 'hss', 'performance', 'database', 'esql']
            },
            'query': """FROM diameter_transactions
| WHERE command_code == ?command_code
| WHERE @timestamp >= ?start_date AND @timestamp <= ?end_date
| EVAL time_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS 
    total_transactions = COUNT(*),
    failures = COUNT(*) WHERE transaction_success == false,
    avg_response_ms = AVG(response_time_ms),
    p95_response_ms = PERCENTILE(response_time_ms, 95),
    p99_response_ms = PERCENTILE(response_time_ms, 99)
  BY time_bucket, hss_node, result_code
| EVAL success_rate_pct = ((total_transactions - failures) / total_transactions) * 100
| WHERE total_transactions >= ?min_transactions
| KEEP hss_node, result_code, success_rate_pct, failures, avg_response_ms, p95_response_ms, p99_response_ms, time_bucket
| SORT success_rate_pct ASC
| LIMIT 25""",
            'query_type': 'parameterized',
            'parameters': [
                {
                    'name': 'command_code',
                    'type': 'string',
                    'description': 'Diameter command code to analyze (Authentication-Information, Update-Location, etc.)',
                    'default': 'Authentication-Information',
                    'required': True
                },
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
                    'name': 'min_transactions',
                    'type': 'integer',
                    'description': 'Minimum number of transactions to include in results',
                    'default': 50,
                    'required': True
                }
            ],
            'pain_point': 'HSS database corruption or synchronization issues affect subscriber authentication. Need to analyze diameter transaction performance by operation type to identify database-specific issues.'
        })

        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using COMPLETION command
        
        CRITICAL - RAG Pipeline Requirements:
        1. MUST use MATCH to find semantically similar documents
        2. OPTIONALLY use RERANK to improve relevance
        3. MUST use COMPLETION to generate LLM-powered answers
        4. Target semantic_text fields from the strategy
        """
        queries = []

        # Query 1: Security Attack Pattern Analysis and Remediation Guidance
        queries.append({
            'name': 'Security Attack Pattern Analysis and Remediation Guidance',
            'description': 'Provides intelligent analysis of security attack patterns using semantic search and LLM-powered recommendations. Searches attack descriptions to find similar incidents and generates actionable remediation guidance based on historical patterns.',
            'tool_metadata': {
                'tool_id': 't-mobile_network_op_security_rag',
                'description': 'Analyzes security attack patterns using AI-powered semantic search. Provides intelligent remediation guidance based on historical attack patterns and industry best practices.',
                'tags': ['security', 'rag', 'ai', 'remediation', 'esql']
            },
            'query': """FROM security_events METADATA _id
| WHERE MATCH(attack_description, ?user_question)
| LIMIT 5
| EVAL prompt = CONCAT(
    "Based on these security incidents, answer the following question: ",
    ?user_question,
    "\\n\\nIncident Details:\\n",
    "Attack Type: ", attack_type, "\\n",
    "Severity: ", severity, "\\n",
    "Source: ", source_network, "\\n",
    "Description: ", attack_description, "\\n",
    "Blocked: ", TO_STRING(blocked)
  )
| KEEP _id, attack_type, severity, source_network, blocked, attack_description, prompt""",
            'query_type': 'rag',
            'parameters': [
                {
                    'name': 'user_question',
                    'type': 'string',
                    'description': 'Question about security attacks or remediation strategies',
                    'required': True
                }
            ],
            'pain_point': 'Rogue network attempts and SS7 security attacks require rapid response, but security teams lack context on similar historical incidents and proven remediation strategies. Need AI-powered analysis to provide instant guidance.'
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum impact"""
        return [
            # Start with critical real-time detection
            'Proactive MME Attach Procedure Degradation Detection with Multi-Dimensional Analysis',
            'Core Network Split-Brain Detection with Multi-MME Context Conflict',
            
            # Show infrastructure health monitoring
            'HSS Authentication Transaction Failure Analysis with Database Node Correlation',
            'MME Software Bug and Resource Exhaustion Detection',
            
            # Demonstrate cascade failure detection
            'Cell Handoff Cascade Failure Pattern Detection with Geographic Clustering',
            'Signaling Storm Detection Across Multiple MME Hosts',
            
            # Show security and anomaly detection
            'SS7 Security Attack Detection with Semantic Pattern Analysis and Subscriber Impact',
            'IMSI and Cell ID Cardinality Anomaly Detection',
            
            # Root cause analysis
            'Subscriber Service Request Failure Root Cause Analysis with Device and Cell Correlation',
            
            # Business impact
            'Revenue Impact Calculation for Network Incidents with Customer Segment Analysis',
            
            # Parameterized queries for user customization
            'Handoff Failure Analysis by Cell Technology and Region',
            'MME Procedure Performance by Datacenter and Cluster',
            'Diameter Transaction Performance by Command Code',
            
            # AI-powered analysis
            'Security Attack Pattern Analysis and Remediation Guidance'
        ]
