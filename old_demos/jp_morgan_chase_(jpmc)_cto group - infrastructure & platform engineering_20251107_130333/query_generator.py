
from src.framework.base import QueryGeneratorModule, DemoConfig
from typing import Dict, List, Any
import pandas as pd

class JPMorganChaseQueryGenerator(QueryGeneratorModule):
    """Query generator for JP Morgan Chase (JPMC) - CTO Group - Infrastructure & Platform Engineering
    
    Focus: Intel to AMD migration analysis, performance benchmarking, cost optimization,
    and unified observability across infrastructure platforms.
    """

    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate ALL ES|QL queries from pre-planned strategy"""
        queries = []

        # ============================================================================
        # SCRIPTED QUERIES - No parameters, ready to run
        # ============================================================================

        # Query 1: Intel vs AMD Performance Baseline Comparison
        queries.append({
            "name": "Intel vs AMD Performance Baseline Comparison with Cost Analysis",
            "description": """Establish performance baselines across identical workloads on Intel Xeon vs AMD EPYC architectures.
            Calculate performance-per-dollar and cost-per-transaction metrics to quantify TCO differences.
            Addresses pain point: Lack of visibility into workload characteristics by hardware platform.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_cpu_performance_baseline",
                "description": "Compares Intel vs AMD server performance metrics. Analyzes performance-per-dollar and cost-per-transaction across workloads for TCO optimization and infrastructure planning decisions.",
                "tags": ["infrastructure", "performance", "cost", "cpu", "esql"]
            },
            "query": """FROM infrastructure_metrics
| WHERE test_phase == "Baseline"
| LOOKUP JOIN compute_hosts ON host_id
| LOOKUP JOIN applications ON application_id
| LOOKUP JOIN benchmark_definitions ON benchmark_id
| STATS 
    avg_transaction_duration_ms = AVG(transaction.duration.us) / 1000,
    p95_transaction_duration_ms = PERCENTILE(transaction.duration.us, 95) / 1000,
    avg_tps = AVG(transactions_per_second),
    avg_cpu_pct = AVG(system.cpu.total.pct),
    avg_cost_per_hour = AVG(hourly_compute_cost_usd),
    avg_power_watts = AVG(power_consumption_tdp_watts),
    test_count = COUNT(*)
  BY cpu_vendor, workload_category, benchmark_type
| EVAL 
    performance_per_dollar = avg_tps / avg_cost_per_hour,
    cost_per_million_transactions = (avg_cost_per_hour / avg_tps) * 1000000,
    power_efficiency = avg_tps / avg_power_watts
| SORT cpu_vendor, workload_category, performance_per_dollar DESC""",
            "query_type": "scripted",
            "use_case": "Baseline Performance Comparison: Intel vs AMD",
            "complexity": "high"
        })

        # Query 2: Application Migration Prioritization
        queries.append({
            "name": "Application-Specific Migration Prioritization with ROI Calculation",
            "description": """Compare each application's performance on Intel vs AMD to identify best migration candidates.
            Calculate performance gains and cost savings to rank applications by migration value.
            Focus on applications not yet migrated to AMD.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_migration_prioritization",
                "description": "Identifies top migration candidates to AMD. Calculates performance gains and annual savings to prioritize applications for hardware migration with highest ROI potential.",
                "tags": ["migration", "cost", "optimization", "planning", "esql"]
            },
            "query": """FROM infrastructure_metrics
| WHERE test_phase == "Baseline"
| LOOKUP JOIN compute_hosts ON host_id
| LOOKUP JOIN applications ON application_id
| WHERE migration_status != "Completed"
| STATS 
    intel_avg_tps = AVG(CASE(cpu_vendor == "Intel", transactions_per_second, null)),
    amd_avg_tps = AVG(CASE(cpu_vendor == "AMD", transactions_per_second, null)),
    intel_avg_cost = AVG(CASE(cpu_vendor == "Intel", cost_per_hour_usd, null)),
    amd_avg_cost = AVG(CASE(cpu_vendor == "AMD", cost_per_hour_usd, null))
  BY application_id, application_name, business_unit, criticality_tier
| WHERE intel_avg_tps IS NOT NULL AND amd_avg_tps IS NOT NULL
| EVAL 
    performance_gain_pct = ((amd_avg_tps - intel_avg_tps) / intel_avg_tps) * 100,
    cost_reduction_pct = ((intel_avg_cost - amd_avg_cost) / intel_avg_cost) * 100,
    annual_savings_usd = (intel_avg_cost - amd_avg_cost) * 24 * 365,
    migration_score = (performance_gain_pct * 0.6) + (cost_reduction_pct * 0.4)
| WHERE performance_gain_pct > 0 AND cost_reduction_pct > 0
| SORT migration_score DESC
| LIMIT 50""",
            "query_type": "scripted",
            "use_case": "Application-Specific Migration Prioritization",
            "complexity": "high"
        })

        # Query 3: Real-Time Performance Regression Detection
        queries.append({
            "name": "Real-Time Performance Regression Detection with SLA Monitoring",
            "description": """Detect performance regressions in real-time by aggregating transaction duration by hour.
            Identify SLA violations and flag severity levels. Essential for catching issues during migration windows.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_sla_monitoring",
                "description": "Monitors SLA violations and performance regressions. Detects critical issues in real-time across applications and assigns severity levels for immediate incident response.",
                "tags": ["monitoring", "sla", "performance", "alerts", "esql"]
            },
            "query": """FROM infrastructure_metrics
| LOOKUP JOIN compute_hosts ON host_id
| LOOKUP JOIN applications ON application_id
| EVAL hour_bucket = DATE_TRUNC(1 hour, @timestamp)
| STATS 
    avg_duration_ms = AVG(transaction.duration.us) / 1000,
    p95_duration_ms = PERCENTILE(transaction.duration.us, 95) / 1000,
    p99_duration_ms = PERCENTILE(transaction.duration.us, 99) / 1000,
    error_rate_pct = (COUNT(CASE(event.outcome == "failure", 1, null)) / COUNT(*)) * 100,
    avg_cpu_pct = AVG(system.cpu.total.pct)
  BY hour_bucket, application_id, application_name, sla_target_ms, hostname, cpu_vendor
| WHERE p95_duration_ms > sla_target_ms
| EVAL 
    sla_violation = CASE(p95_duration_ms > sla_target_ms, "YES", "NO"),
    severity = CASE(
      p99_duration_ms > sla_target_ms * 2, "CRITICAL",
      p95_duration_ms > sla_target_ms * 1.5, "HIGH",
      "MEDIUM"
    )
| SORT hour_bucket DESC
| LIMIT 100""",
            "query_type": "scripted",
            "use_case": "Continuous Performance Regression Detection",
            "complexity": "high"
        })

        # Query 4: Unified Kafka and Infrastructure Correlation
        queries.append({
            "name": "Unified Kafka and Infrastructure Performance Correlation",
            "description": """Correlate Kafka consumer lag and throughput with underlying infrastructure metrics to identify bottlenecks.
            Addresses pain point: Data scattered across disparate systems with no unified view.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_kafka_correlation",
                "description": "Correlates Kafka performance with infrastructure metrics. Identifies consumer lag issues and throughput bottlenecks across Intel and AMD platforms for streaming optimization.",
                "tags": ["kafka", "streaming", "infrastructure", "correlation", "esql"]
            },
            "query": """FROM kafka_metrics
| LOOKUP JOIN compute_hosts ON host_id
| STATS 
    avg_consumer_lag = AVG(consumer_lag),
    max_consumer_lag = MAX(consumer_lag),
    avg_throughput = AVG(message_throughput_per_sec),
    avg_broker_cpu = AVG(broker_cpu_pct),
    avg_network_in = AVG(broker_network_in_mb),
    avg_network_out = AVG(broker_network_out_mb)
  BY hostname, cpu_vendor, topic_name, consumer_group
| EVAL 
    lag_severity = CASE(
      max_consumer_lag > 50000, "CRITICAL",
      max_consumer_lag > 25000, "HIGH",
      "NORMAL"
    ),
    throughput_health = CASE(
      avg_throughput < 1000, "LOW",
      avg_throughput < 10000, "MEDIUM",
      "HIGH"
    )
| WHERE max_consumer_lag > 10000
| SORT max_consumer_lag DESC
| LIMIT 50""",
            "query_type": "scripted",
            "use_case": "Consolidate Kafka & Hive Metrics into Unified Observability",
            "complexity": "medium"
        })

        # Query 5: Cost-Performance TCO Analysis
        queries.append({
            "name": "Cost-Performance TCO Analysis by Business Unit",
            "description": """Calculate comprehensive TCO including compute costs, licensing, and power consumption.
            Compare Intel vs AMD across business units to quantify migration ROI.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_tco_analysis",
                "description": "Analyzes total cost of ownership by business unit. Calculates comprehensive TCO including compute, power, and licensing costs for Intel vs AMD infrastructure investment decisions.",
                "tags": ["cost", "tco", "business", "financial", "esql"]
            },
            "query": """FROM infrastructure_metrics
| LOOKUP JOIN compute_hosts ON host_id
| LOOKUP JOIN applications ON application_id
| LOOKUP JOIN cost_allocation ON cost_center
| STATS 
    total_compute_hours = COUNT(*),
    avg_tps = AVG(transactions_per_second),
    total_compute_cost = SUM(cost_per_hour_usd),
    avg_power_consumption = AVG(power_consumption_watts)
  BY business_unit, cost_center, cpu_vendor
| EVAL 
    annual_compute_cost = total_compute_cost * 12,
    annual_power_cost = (avg_power_consumption * 24 * 365 * 0.12) / 1000,
    licensing_cost = 50000,
    total_tco_annual = annual_compute_cost + annual_power_cost + licensing_cost,
    cost_per_million_transactions = (total_tco_annual / (avg_tps * 86400 * 365)) * 1000000
| SORT total_tco_annual DESC""",
            "query_type": "scripted",
            "use_case": "Cost-Performance Analysis & TCO Modeling",
            "complexity": "high"
        })

        # Query 6: Multi-Dimensional Stress Test Analysis
        queries.append({
            "name": "Multi-Dimensional Stress Test Analysis with FORK",
            "description": """Simultaneously analyze multiple dimensions of stress test results: peak performance,
            error rates under load, and resource saturation points. Identifies maximum sustainable capacity.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_stress_analysis",
                "description": "Analyzes stress test results across dimensions. Identifies peak performance, error thresholds, and resource saturation points for capacity planning and resilience testing.",
                "tags": ["stress", "capacity", "testing", "performance", "esql"]
            },
            "query": """FROM infrastructure_metrics
| WHERE test_phase == "Stress-Test"
| LOOKUP JOIN compute_hosts ON host_id
| LOOKUP JOIN applications ON application_id
| LOOKUP JOIN benchmark_definitions ON benchmark_id
| FORK
  (
    STATS 
      peak_tps = MAX(transactions_per_second),
      avg_tps = AVG(transactions_per_second),
      test_duration_hours = (MAX(TO_LONG(@timestamp)) - MIN(TO_LONG(@timestamp))) / 3600000
    BY cpu_vendor, application_name, target_load_level
    | EVAL analysis_type = "peak_performance"
  ),
  (
    STATS 
      error_rate_pct = (COUNT(CASE(event.outcome == "failure", 1, null)) / COUNT(*)) * 100,
      total_errors = COUNT(CASE(event.outcome == "failure", 1, null))
    BY cpu_vendor, application_name, target_load_level
    | WHERE error_rate_pct > 0.1
    | EVAL analysis_type = "error_analysis"
  ),
  (
    STATS 
      max_cpu_pct = MAX(system.cpu.total.pct),
      max_memory_pct = MAX(system.memory.used.pct),
      saturation_point = AVG(CASE(system.cpu.total.pct > 80, transactions_per_second, null))
    BY cpu_vendor, application_name
    | WHERE max_cpu_pct > 80 OR max_memory_pct > 85
    | EVAL analysis_type = "resource_saturation"
  )""",
            "query_type": "scripted",
            "use_case": "Stress Test & Capacity Planning",
            "complexity": "high"
        })

        # Query 7: Hive Query Performance Analysis
        queries.append({
            "name": "Hive Query Performance Analysis by Architecture",
            "description": """Analyze Hive query execution times across Intel and AMD architectures.
            Identify slow queries and compare performance characteristics by hardware platform.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_hive_performance",
                "description": "Analyzes Hive query performance metrics. Compares execution times between Intel and AMD platforms to identify optimization opportunities for big data workloads.",
                "tags": ["hive", "bigdata", "performance", "analytics", "esql"]
            },
            "query": """FROM hive_query_logs
| LOOKUP JOIN compute_hosts ON host_id
| LOOKUP JOIN applications ON application_id
| STATS 
    avg_execution_ms = AVG(query_execution_time_ms),
    p95_execution_ms = PERCENTILE(query_execution_time_ms, 95),
    avg_data_scanned_gb = AVG(data_scanned_gb),
    total_queries = COUNT(*)
  BY cpu_vendor, database_name, query_type
| EVAL 
    performance_rating = CASE(
      p95_execution_ms < 10000, "EXCELLENT",
      p95_execution_ms < 60000, "GOOD",
      p95_execution_ms < 180000, "FAIR",
      "POOR"
    )
| SORT p95_execution_ms DESC
| LIMIT 50""",
            "query_type": "scripted",
            "use_case": "Consolidate Kafka & Hive Metrics into Unified Observability",
            "complexity": "medium"
        })

        # Query 8: Migration Budget vs Actual Spend
        queries.append({
            "name": "Migration Budget Analysis and Cost Center Performance",
            "description": """Track migration progress and budget utilization by cost center.
            Compare current spend against budget and target cost reduction goals.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_budget_tracking",
                "description": "Tracks migration budget and progress metrics. Monitors cost center performance against targets and AMD adoption rates for financial governance and planning.",
                "tags": ["budget", "migration", "financial", "tracking", "esql"]
            },
            "query": """FROM cost_allocation
| EVAL 
    budget_utilization_pct = (current_spend_usd / budget_annual_usd) * 100,
    total_hosts = intel_host_count + amd_host_count,
    amd_adoption_pct = (TO_DOUBLE(amd_host_count) / total_hosts) * 100,
    projected_annual_savings = current_spend_usd * (target_cost_reduction_pct / 100)
| SORT budget_utilization_pct DESC
| LIMIT 25""",
            "query_type": "scripted",
            "use_case": "Cost-Performance Analysis & TCO Modeling",
            "complexity": "low"
        })

        return queries

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized queries that accept user input"""
        queries = []

        # Query 1: Architecture-Specific Performance Analysis (Parameterized)
        queries.append({
            "name": "Architecture-Specific Performance Deep Dive",
            "description": """Analyze performance metrics for a specific CPU architecture and workload type.
            Filter by architecture (Intel/AMD) and workload category to compare results.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_architecture_analysis",
                "description": "Analyzes performance metrics by CPU architecture and workload type. Compares Intel vs AMD performance for specific workload categories with detailed latency and resource metrics.",
                "tags": ["infrastructure", "performance", "architecture", "workload", "esql"]
            },
            "query": """FROM infrastructure_metrics
| WHERE test_phase == "Baseline"
| LOOKUP JOIN compute_hosts ON host_id
| LOOKUP JOIN applications ON application_id
| WHERE cpu_vendor == ?architecture
| WHERE workload_category == ?workload_type
| STATS 
    avg_tps = AVG(transactions_per_second),
    p50_latency_ms = PERCENTILE(transaction.duration.us, 50) / 1000,
    p95_latency_ms = PERCENTILE(transaction.duration.us, 95) / 1000,
    p99_latency_ms = PERCENTILE(transaction.duration.us, 99) / 1000,
    avg_cpu = AVG(system.cpu.total.pct),
    avg_memory = AVG(system.memory.used.pct),
    success_rate_pct = (COUNT(CASE(event.outcome == "success", 1, null)) / COUNT(*)) * 100
  BY application_name, criticality_tier
| SORT avg_tps DESC
| LIMIT 50""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "architecture",
                    "type": "string",
                    "description": "CPU architecture to analyze",
                    "default": "AMD",
                    "allowed_values": ["Intel", "AMD"]
                },
                {
                    "name": "workload_type",
                    "type": "string",
                    "description": "Workload category to filter",
                    "default": "Trading Platform",
                    "allowed_values": ["Batch Processing", "Real-time Streaming", "Payment Processing", 
                                      "Risk Analytics", "Trading Platform", "Data Warehouse"]
                }
            ],
            "use_case": "Baseline Performance Comparison: Intel vs AMD",
            "complexity": "medium"
        })

        # Query 2: Business Unit Migration Progress (Parameterized)
        queries.append({
            "name": "Business Unit Migration Progress Tracker",
            "description": """Track migration progress for a specific business unit.
            Show application counts by migration status and calculate completion percentage.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_migration_tracker",
                "description": "Tracks migration progress by business unit. Shows application counts by migration status and criticality for project management and executive reporting.",
                "tags": ["migration", "tracking", "business", "progress", "esql"]
            },
            "query": """FROM applications
| WHERE business_unit == ?business_unit
| LOOKUP JOIN infrastructure_metrics ON application_id
| LOOKUP JOIN compute_hosts ON host_id
| STATS 
    app_count = COUNT_DISTINCT(application_id),
    avg_tps = AVG(transactions_per_second),
    total_tests = COUNT(*)
  BY migration_status, criticality_tier
| SORT migration_status, criticality_tier""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "business_unit",
                    "type": "string",
                    "description": "Business unit to analyze",
                    "default": "Trading",
                    "allowed_values": ["Treasury", "Investment Banking", "Risk Management", 
                                      "Retail Banking", "Trading", "Asset Management"]
                }
            ],
            "use_case": "Application-Specific Migration Prioritization",
            "complexity": "medium"
        })

        # Query 3: Kafka Topic Performance Analysis (Parameterized)
        queries.append({
            "name": "Kafka Topic Performance Deep Dive",
            "description": """Analyze Kafka metrics for a specific topic across different architectures.
            Compare consumer lag, throughput, and broker resource utilization.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_kafka_topic_analysis",
                "description": "Analyzes Kafka topic performance metrics. Monitors consumer lag, throughput, and broker resources by CPU architecture for streaming platform optimization.",
                "tags": ["kafka", "streaming", "topic", "performance", "esql"]
            },
            "query": """FROM kafka_metrics
| WHERE topic_name == ?topic_name
| LOOKUP JOIN compute_hosts ON host_id
| STATS 
    avg_lag = AVG(consumer_lag),
    max_lag = MAX(consumer_lag),
    p95_lag = PERCENTILE(consumer_lag, 95),
    avg_throughput = AVG(message_throughput_per_sec),
    avg_broker_cpu = AVG(broker_cpu_pct),
    avg_network_in = AVG(broker_network_in_mb)
  BY cpu_vendor, consumer_group
| EVAL 
    lag_health = CASE(
      max_lag < 10000, "HEALTHY",
      max_lag < 50000, "WARNING",
      "CRITICAL"
    )
| SORT max_lag DESC""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "topic_name",
                    "type": "string",
                    "description": "Kafka topic to analyze",
                    "default": "trades",
                    "allowed_values": ["payments", "trades", "risk-events", "market-data", 
                                      "customer-events", "audit-logs"]
                }
            ],
            "use_case": "Consolidate Kafka & Hive Metrics into Unified Observability",
            "complexity": "medium"
        })

        # Query 4: Benchmark Type Performance Comparison (Parameterized)
        queries.append({
            "name": "Benchmark Type Performance Comparison",
            "description": """Compare performance across Intel and AMD for a specific benchmark type.
            Useful for evaluating migration candidates for specific workload patterns.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_benchmark_comparison",
                "description": "Compares benchmark performance between Intel and AMD platforms. Evaluates specific workload patterns to identify migration candidates with performance metrics.",
                "tags": ["benchmark", "performance", "comparison", "testing", "esql"]
            },
            "query": """FROM infrastructure_metrics
| WHERE test_phase == "Baseline"
| LOOKUP JOIN benchmark_definitions ON benchmark_id
| LOOKUP JOIN compute_hosts ON host_id
| WHERE benchmark_type == ?benchmark_type
| STATS 
    avg_tps = AVG(transactions_per_second),
    p95_latency_ms = PERCENTILE(transaction.duration.us, 95) / 1000,
    avg_cpu = AVG(system.cpu.total.pct),
    avg_cost_per_hour = AVG(cost_per_hour_usd),
    test_count = COUNT(*)
  BY cpu_vendor, target_load_level
| EVAL 
    performance_per_dollar = avg_tps / avg_cost_per_hour
| SORT cpu_vendor, target_load_level""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "benchmark_type",
                    "type": "string",
                    "description": "Type of benchmark to analyze",
                    "default": "CPU-Intensive",
                    "allowed_values": ["Network-Intensive", "I/O-Intensive", "Mixed-Workload", 
                                      "Memory-Intensive", "CPU-Intensive"]
                }
            ],
            "use_case": "Baseline Performance Comparison: Intel vs AMD",
            "complexity": "medium"
        })

        # Query 5: Datacenter Performance Analysis (Parameterized)
        queries.append({
            "name": "Datacenter-Level Performance and Cost Analysis",
            "description": """Analyze infrastructure performance and costs for a specific datacenter.
            Compare Intel vs AMD deployment and identify optimization opportunities.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_datacenter_analysis",
                "description": "Analyzes datacenter-level performance and costs. Compares Intel vs AMD deployments by location for capacity planning and cost optimization decisions.",
                "tags": ["datacenter", "cost", "performance", "infrastructure", "esql"]
            },
            "query": """FROM infrastructure_metrics
| LOOKUP JOIN compute_hosts ON host_id
| WHERE datacenter == ?datacenter
| STATS 
    host_count = COUNT_DISTINCT(host_id),
    avg_tps = AVG(transactions_per_second),
    avg_cpu = AVG(system.cpu.total.pct),
    avg_memory = AVG(system.memory.used.pct),
    total_cost = SUM(cost_per_hour_usd),
    avg_power_watts = AVG(power_consumption_watts)
  BY cpu_vendor, hardware_generation
| EVAL 
    estimated_annual_cost = total_cost * 24 * 365,
    power_efficiency = avg_tps / avg_power_watts
| SORT cpu_vendor, hardware_generation""",
            "query_type": "parameterized",
            "parameters": [
                {
                    "name": "datacenter",
                    "type": "string",
                    "description": "Datacenter location to analyze",
                    "default": "NYC-DC1",
                    "allowed_values": ["CHI-DC1", "DFW-DC1", "SJC-DC1", "NYC-DC1", "NYC-DC2"]
                }
            ],
            "use_case": "Cost-Performance Analysis & TCO Modeling",
            "complexity": "medium"
        })

        return queries

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries using COMPLETION command
        
        Targets semantic_text fields:
        - compute_hosts.host_profile_description
        - applications.application_characteristics
        - benchmark_definitions.benchmark_description
        - infrastructure_metrics.anomaly_notes
        """
        queries = []

        # Query 1: Semantic Search for High-Risk Migration Candidates
        queries.append({
            "name": "Semantic Search for High-Risk Migration Candidates",
            "description": """Use semantic search to identify applications with characteristics that make them
            high-risk for migration (e.g., 'latency-sensitive real-time trading applications').
            Enrich with current performance metrics to prioritize testing.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_migration_risk_search",
                "description": "Uses semantic search to find high-risk migration candidates. Identifies applications by characteristics and provides AI-powered risk assessments for migration planning.",
                "tags": ["migration", "risk", "semantic", "ai", "esql"]
            },
            "query": """FROM applications METADATA _id
| WHERE MATCH(application_characteristics, ?user_question)
| WHERE migration_status == "Not Started" OR migration_status == "Planning"
| LOOKUP JOIN infrastructure_metrics ON application_id
| LOOKUP JOIN compute_hosts ON host_id
| STATS 
    avg_tps = AVG(transactions_per_second),
    avg_cpu = AVG(system.cpu.total.pct),
    current_arch = VALUES(cpu_vendor)
  BY application_id, application_name, criticality_tier, application_characteristics
| SORT avg_cpu DESC
| LIMIT 5
| EVAL prompt = CONCAT("Based on these application characteristics and performance metrics, provide a migration risk assessment and recommendations: ", application_characteristics, " Current performance: ", TO_STRING(avg_tps), " TPS, ", TO_STRING(avg_cpu), "% CPU on ", current_arch, " architecture.")
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "string",
                    "description": "Describe the application characteristics to search for",
                    "default": "compute-intensive batch processing applications with high CPU utilization"
                }
            ],
            "use_case": "Application-Specific Migration Prioritization",
            "complexity": "medium"
        })

        # Query 2: Infrastructure Anomaly Investigation
        queries.append({
            "name": "Infrastructure Anomaly Investigation with AI Analysis",
            "description": """Search through anomaly notes to find similar infrastructure issues.
            Use AI to provide root cause analysis and remediation recommendations.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_anomaly_investigation",
                "description": "Investigates infrastructure anomalies using semantic search. Provides AI-powered root cause analysis and remediation recommendations for operational incidents.",
                "tags": ["anomaly", "investigation", "ai", "operations", "esql"]
            },
            "query": """FROM infrastructure_metrics METADATA _id
| WHERE MATCH(anomaly_notes, ?user_question)
| LOOKUP JOIN compute_hosts ON host_id
| LOOKUP JOIN applications ON application_id
| STATS 
    occurrence_count = COUNT(*),
    avg_cpu = AVG(system.cpu.total.pct),
    avg_memory = AVG(system.memory.used.pct),
    affected_apps = COUNT_DISTINCT(application_id)
  BY anomaly_notes, cpu_vendor, test_phase
| SORT occurrence_count DESC
| LIMIT 5
| EVAL prompt = CONCAT("Analyze this infrastructure anomaly and provide root cause analysis and recommendations: ", anomaly_notes, " Occurred ", TO_STRING(occurrence_count), " times on ", cpu_vendor, " during ", test_phase, " phase. Average CPU: ", TO_STRING(avg_cpu), "%, Memory: ", TO_STRING(avg_memory), "%")
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "string",
                    "description": "Describe the anomaly or issue to investigate",
                    "default": "memory pressure and high utilization"
                }
            ],
            "use_case": "Continuous Performance Regression Detection",
            "complexity": "medium"
        })

        # Query 3: Benchmark Selection Assistant
        queries.append({
            "name": "Benchmark Selection Assistant with AI Recommendations",
            "description": """Find appropriate benchmarks based on workload description using semantic search.
            Get AI-powered recommendations on which benchmarks to use for migration validation.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_benchmark_assistant",
                "description": "Assists with benchmark selection using semantic search. Provides AI recommendations for choosing appropriate benchmarks for migration validation and testing.",
                "tags": ["benchmark", "testing", "ai", "recommendations", "esql"]
            },
            "query": """FROM benchmark_definitions METADATA _id
| WHERE MATCH(benchmark_description, ?user_question)
| LIMIT 5
| EVAL prompt = CONCAT("Based on this benchmark: ", benchmark_name, " (", benchmark_type, ") - ", benchmark_description, " Target load: ", target_load_level, ", Success criteria: ", success_criteria, " - provide recommendations on when to use this benchmark and what to look for in results.")
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "string",
                    "description": "Describe the workload or testing scenario",
                    "default": "high-throughput streaming workload with network-intensive operations"
                }
            ],
            "use_case": "Baseline Performance Comparison: Intel vs AMD",
            "complexity": "low"
        })

        # Query 4: Host Configuration Optimization
        queries.append({
            "name": "Host Configuration Optimization Recommendations",
            "description": """Search for hosts with specific characteristics and get AI-powered optimization recommendations
            for migration planning.""",
            "tool_metadata": {
                "tool_id": "jpmc_infra_host_optimization",
                "description": "Provides host configuration optimization recommendations. Uses semantic search to find hosts and offers AI-powered suggestions for migration and capacity planning.",
                "tags": ["host", "optimization", "ai", "capacity", "esql"]
            },
            "query": """FROM compute_hosts METADATA _id
| WHERE MATCH(host_profile_description, ?user_question)
| LIMIT 5
| EVAL prompt = CONCAT("Analyze this host configuration: ", hostname, " - ", host_profile_description, " CPU: ", cpu_cores, " cores, Memory: ", TO_STRING(memory_gb), "GB, Cost: $", TO_STRING(hourly_compute_cost_usd), "/hr, Power: ", TO_STRING(power_consumption_tdp_watts), "W. Provide optimization and migration recommendations.")
| COMPLETION answer = prompt WITH {"inference_id": "completion-vulcan"}""",
            "query_type": "rag",
            "parameters": [
                {
                    "name": "user_question",
                    "type": "string",
                    "description": "Describe the host characteristics to search for",
                    "default": "legacy Intel hardware scheduled for AMD migration"
                }
            ],
            "use_case": "Cost-Performance Analysis & TCO Modeling",
            "complexity": "low"
        })

        return queries

    def get_query_progression(self) -> List[str]:
        """Define the order to present queries for maximum impact
        
        Progression strategy:
        1. Start with high-level comparison (Intel vs AMD baseline)
        2. Drill into migration prioritization
        3. Show operational monitoring (regression detection)
        4. Demonstrate unified observability (Kafka integration)
        5. Present cost analysis and ROI
        6. Show advanced analytics (stress testing with FORK)
        7. Include Hive query analysis
        8. End with budget tracking
        """
        return [
            # Phase 1: Establish Baseline Understanding
            "Intel vs AMD Performance Baseline Comparison with Cost Analysis",
            "Architecture-Specific Performance Deep Dive",
            
            # Phase 2: Migration Planning and Prioritization
            "Application-Specific Migration Prioritization with ROI Calculation",
            "Semantic Search for High-Risk Migration Candidates",
            "Business Unit Migration Progress Tracker",
            
            # Phase 3: Operational Monitoring
            "Real-Time Performance Regression Detection with SLA Monitoring",
            "Infrastructure Anomaly Investigation with AI Analysis",
            
            # Phase 4: Unified Observability
            "Unified Kafka and Infrastructure Performance Correlation",
            "Kafka Topic Performance Deep Dive",
            "Hive Query Performance Analysis by Architecture",
            
            # Phase 5: Cost and Performance Analysis
            "Cost-Performance TCO Analysis by Business Unit",
            "Datacenter-Level Performance and Cost Analysis",
            "Migration Budget Analysis and Cost Center Performance",
            
            # Phase 6: Advanced Testing and Validation
            "Multi-Dimensional Stress Test Analysis with FORK",
            "Benchmark Type Performance Comparison",
            "Benchmark Selection Assistant with AI Recommendations",
            "Host Configuration Optimization Recommendations"
        ]
