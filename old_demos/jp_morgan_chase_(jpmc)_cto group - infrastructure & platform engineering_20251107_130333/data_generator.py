
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List

class JPMorganChaseDataGenerator(DataGeneratorModule):
    """Data generator for JP Morgan Chase (JPMC) - CTO Group - Infrastructure & Platform Engineering"""

    @staticmethod
    def safe_choice(choices, size=None, weights=None, replace=True):
        """Safer alternative to np.random.choice with automatic probability normalization."""
        if weights is not None:
            weights = np.array(weights, dtype=float)
            probabilities = weights / weights.sum()
            return np.random.choice(choices, size=size, p=probabilities, replace=replace)
        else:
            return np.random.choice(choices, size=size, replace=replace)

    @staticmethod
    def random_timedelta(start_date, end_date=None, days=None, hours=None, minutes=None):
        """Generate random timedelta-adjusted datetime, handling numpy int64 conversion."""
        if end_date is not None:
            delta = end_date - start_date
            random_seconds = int(np.random.random() * delta.total_seconds())
            return start_date + timedelta(seconds=random_seconds)

        delta_kwargs = {}
        if days is not None:
            delta_kwargs['days'] = int(days)
        if hours is not None:
            delta_kwargs['hours'] = int(hours)
        if minutes is not None:
            delta_kwargs['minutes'] = int(minutes)

        return start_date + timedelta(**delta_kwargs)

    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        """Generate datasets with EXACT fields from requirements"""
        datasets = {}
        
        now = datetime.now()
        
        # Reference data
        cpu_models_intel = ['Intel Xeon Gold 6248', 'Intel Xeon Platinum 8280', 'Intel Xeon E5-2690', 'Intel Xeon Gold 5220']
        cpu_models_amd = ['AMD EPYC 7763', 'AMD EPYC 7713', 'AMD EPYC 7543', 'AMD EPYC 7443']
        datacenters = ['NYC-DC1', 'NYC-DC2', 'CHI-DC1', 'DFW-DC1', 'SJC-DC1']
        business_units = ['Investment Banking', 'Retail Banking', 'Asset Management', 'Treasury', 'Risk Management', 'Trading']
        workload_categories = ['Trading Platform', 'Risk Analytics', 'Payment Processing', 'Data Warehouse', 'Real-time Streaming', 'Batch Processing']
        criticality_tiers = ['Tier1-Critical', 'Tier2-High', 'Tier3-Medium', 'Tier4-Low']
        
        # compute_hosts
        n_hosts = 200
        host_ids = [f'host-{i:05d}' for i in range(1, n_hosts + 1)]
        cpu_vendors = self.safe_choice(['Intel', 'AMD'], n_hosts, weights=[0.7, 0.3])
        
        hosts_data = []
        for i, host_id in enumerate(host_ids):
            vendor = cpu_vendors[i]
            if vendor == 'Intel':
                cpu_model = random.choice(cpu_models_intel)
                cores = random.choice([16, 24, 32, 48])
                tdp = random.randint(150, 250)
                hourly_cost = round(random.uniform(0.8, 1.5), 3)
                licensing = random.randint(8000, 15000)
                hw_gen = random.choice(['Gen3', 'Gen4', 'Gen5'])
            else:
                cpu_model = random.choice(cpu_models_amd)
                cores = random.choice([32, 48, 64, 96])
                tdp = random.randint(180, 280)
                hourly_cost = round(random.uniform(0.5, 1.0), 3)
                licensing = random.randint(3000, 8000)
                hw_gen = random.choice(['Gen3', 'Gen4'])
            
            memory_gb = cores * random.choice([4, 8, 16])
            purchase_date = now - timedelta(days=random.randint(90, 1800))
            migration_candidate = vendor == 'Intel' and hw_gen in ['Gen3', 'Gen4']
            
            profile_templates = [
                "High-performance {vendor} server optimized for {workload} workloads with {cores} cores",
                "{vendor} compute node in {dc} providing {memory}GB RAM for enterprise applications",
                "Legacy {vendor} hardware scheduled for AMD migration assessment, currently running {workload}",
                "Modern {vendor} platform with enhanced security features for financial services compliance"
            ]
            
            hosts_data.append({
                'host_id': host_id,
                'hostname': f'{host_id}.jpmc.internal',
                'host.cpu.model.name': cpu_model,
                'cpu_architecture': 'x86_64',
                'cpu_vendor': vendor,
                'cpu_cores': cores,
                'memory_gb': memory_gb,
                'datacenter': random.choice(datacenters),
                'rack_location': f'R{random.randint(1,40):02d}-U{random.randint(1,42):02d}',
                'hardware_generation': hw_gen,
                'purchase_date': purchase_date,
                'hourly_compute_cost_usd': hourly_cost,
                'licensing_cost_annual_usd': float(licensing),
                'power_consumption_tdp_watts': float(tdp),
                'migration_candidate': migration_candidate,
                'host_profile_description': random.choice(profile_templates).format(
                    vendor=vendor, cores=cores, memory=memory_gb,
                    dc=datacenters[i % len(datacenters)],
                    workload=random.choice(['compute-intensive', 'memory-intensive', 'I/O-intensive'])
                )
            })
        
        datasets['compute_hosts'] = pd.DataFrame(hosts_data)
        
        # applications
        n_apps = 150
        app_ids = [f'app-{i:04d}' for i in range(1, n_apps + 1)]
        
        apps_data = []
        for app_id in app_ids:
            bu = random.choice(business_units)
            wl_cat = random.choice(workload_categories)
            crit = self.safe_choice(criticality_tiers, weights=[0.2, 0.3, 0.3, 0.2])
            
            sla_map = {'Tier1-Critical': (5, 20), 'Tier2-High': (20, 50), 'Tier3-Medium': (50, 200), 'Tier4-Low': (200, 1000)}
            sla_target = round(random.uniform(*sla_map[crit]), 2)
            
            min_tps = round(random.uniform(10, 5000), 2)
            
            migration_priority = self.safe_choice(['P0-Immediate', 'P1-High', 'P2-Medium', 'P3-Low'], 
                                                   weights=[0.15, 0.25, 0.35, 0.25])
            migration_status = self.safe_choice(['Not Started', 'Planning', 'In Progress', 'Completed'], 
                                                 weights=[0.5, 0.2, 0.2, 0.1])
            
            char_templates = [
                "{workload} application for {bu} requiring {crit} availability and sub-{sla}ms latency",
                "Mission-critical {workload} system processing {tps} TPS with strict regulatory compliance requirements",
                "Enterprise {workload} platform serving {bu} with {status} migration to AMD infrastructure",
                "High-throughput {workload} application optimized for real-time processing and low-latency execution"
            ]
            
            apps_data.append({
                'application_id': app_id,
                'application_name': f'{bu.replace(" ", "")}-{wl_cat.replace(" ", "")}-{app_id}',
                'business_unit': bu,
                'criticality_tier': crit,
                'workload_category': wl_cat,
                'sla_target_ms': sla_target,
                'min_tps_required': min_tps,
                'cost_center': f'CC-{random.randint(1000, 9999)}',
                'migration_priority': migration_priority,
                'migration_status': migration_status,
                'owner_team': f'{bu.split()[0]}-Engineering',
                'application_characteristics': random.choice(char_templates).format(
                    workload=wl_cat, bu=bu, crit=crit, sla=int(sla_target), 
                    tps=int(min_tps), status=migration_status
                )
            })
        
        datasets['applications'] = pd.DataFrame(apps_data)
        
        # benchmark_definitions
        n_benchmarks = 80
        benchmark_ids = [f'bench-{i:03d}' for i in range(1, n_benchmarks + 1)]
        benchmark_types = ['CPU-Intensive', 'Memory-Intensive', 'I/O-Intensive', 'Network-Intensive', 'Mixed-Workload']
        
        bench_data = []
        for bench_id in benchmark_ids:
            b_type = random.choice(benchmark_types)
            duration = random.choice([5, 10, 15, 30, 60])
            load_level = random.choice(['Light', 'Medium', 'Heavy', 'Peak', 'Stress'])
            
            desc_templates = [
                "{type} benchmark testing {load} load conditions over {duration} minutes with {metric} metrics",
                "Standardized {type} performance test measuring throughput and latency under {load} scenarios",
                "Custom {type} benchmark simulating production workload patterns for migration validation",
                "Industry-standard {type} test suite evaluating hardware performance across {load} load profiles"
            ]
            
            bench_data.append({
                'benchmark_id': bench_id,
                'benchmark_name': f'{b_type}-{load_level}-{bench_id}',
                'benchmark_type': b_type,
                'test_duration_minutes': duration,
                'target_load_level': load_level,
                'success_criteria': f'P95 latency < {random.randint(10, 100)}ms AND throughput > {random.randint(100, 10000)} TPS',
                'spec_cpu_2017_score': round(random.uniform(200, 600), 2) if b_type == 'CPU-Intensive' else None,
                'tpc_h_qphh': round(random.uniform(50000, 200000), 2) if 'I/O' in b_type else None,
                'sysbench_events_per_sec': round(random.uniform(5000, 50000), 2) if b_type == 'CPU-Intensive' else None,
                'kafka_mb_per_sec': round(random.uniform(100, 2000), 2) if 'Network' in b_type else None,
                'custom_trade_settlement_tps': round(random.uniform(500, 5000), 2) if random.random() > 0.7 else None,
                'custom_risk_calc_throughput': round(random.uniform(1000, 10000), 2) if random.random() > 0.7 else None,
                'custom_payment_validation_p95_ms': round(random.uniform(5, 50), 2) if random.random() > 0.7 else None,
                'benchmark_description': random.choice(desc_templates).format(
                    type=b_type, load=load_level, duration=duration,
                    metric=random.choice(['performance', 'throughput', 'latency', 'resource utilization'])
                )
            })
        
        datasets['benchmark_definitions'] = pd.DataFrame(bench_data)
        
        # infrastructure_metrics (timeseries)
        n_metrics = 3000
        timestamps = pd.date_range(end=now, periods=n_metrics, freq='5min')
        
        workload_types = ['OLTP', 'OLAP', 'Streaming', 'Batch', 'API', 'ML-Training']
        test_phases = ['Baseline', 'Load-Test', 'Stress-Test', 'Soak-Test', 'Migration-Validation', 'Production']
        outcomes = ['success', 'failure']
        
        metrics_data = []
        for i, ts in enumerate(timestamps):
            host = random.choice(host_ids)
            app = random.choice(app_ids)
            bench = random.choice(benchmark_ids)
            wl_type = random.choice(workload_types)
            phase = random.choice(test_phases)
            outcome = self.safe_choice(outcomes, weights=[0.95, 0.05])
            
            host_info = datasets['compute_hosts'][datasets['compute_hosts']['host_id'] == host].iloc[0]
            cpu_base = 40 if host_info['cpu_vendor'] == 'Intel' else 35
            cpu_pct = round(random.uniform(cpu_base, 95), 2)
            mem_pct = round(random.uniform(30, 85), 2)
            
            duration_us = int(random.uniform(1000, 100000)) if outcome == 'success' else int(random.uniform(50000, 500000))
            tps = round(random.uniform(50, 5000), 2) if outcome == 'success' else round(random.uniform(10, 100), 2)
            
            anomaly_notes_list = [
                None, None, None, None, None,
                f"CPU spike detected on {host} during {phase} phase",
                f"Memory pressure observed - {mem_pct}% utilization exceeds threshold",
                f"Elevated transaction latency correlates with disk I/O contention",
                f"Network throughput degradation during peak load testing"
            ]
            
            metrics_data.append({
                'metric_id': f'metric-{i:07d}',
                '@timestamp': ts,
                'host_id': host,
                'application_id': app,
                'benchmark_id': bench,
                'system.cpu.total.pct': cpu_pct,
                'system.memory.used.pct': mem_pct,
                'system.diskio.read.bytes': int(random.uniform(1e6, 1e9)),
                'system.diskio.write.bytes': int(random.uniform(1e6, 1e9)),
                'system.diskio.io.time': int(random.uniform(100, 10000)),
                'system.network.in.bytes': int(random.uniform(1e6, 1e8)),
                'system.network.out.bytes': int(random.uniform(1e6, 1e8)),
                'transaction.duration.us': duration_us,
                'event.outcome': outcome,
                'transactions_per_second': tps,
                'cost_per_hour_usd': host_info['hourly_compute_cost_usd'],
                'power_consumption_watts': round(host_info['power_consumption_tdp_watts'] * (cpu_pct / 100) * random.uniform(0.8, 1.2), 2),
                'workload_type': wl_type,
                'test_phase': phase,
                'anomaly_notes': random.choice(anomaly_notes_list)
            })
        
        datasets['infrastructure_metrics'] = pd.DataFrame(metrics_data)
        
        # kafka_metrics (timeseries)
        n_kafka = 1500
        kafka_timestamps = pd.date_range(end=now, periods=n_kafka, freq='10min')
        topics = ['trades', 'payments', 'risk-events', 'market-data', 'audit-logs', 'customer-events']
        consumer_groups = ['trading-app', 'risk-engine', 'analytics', 'reporting', 'audit-processor']
        
        kafka_data = []
        for i, ts in enumerate(kafka_timestamps):
            host = random.choice(host_ids)
            topic = random.choice(topics)
            
            kafka_data.append({
                'kafka_metric_id': f'kafka-{i:07d}',
                '@timestamp': ts,
                'host_id': host,
                'topic_name': topic,
                'consumer_group': random.choice(consumer_groups),
                'consumer_lag': int(random.uniform(0, 100000)),
                'message_throughput_per_sec': round(random.uniform(100, 50000), 2),
                'topic_size_bytes': int(random.uniform(1e9, 1e12)),
                'partition_count': random.choice([8, 16, 32, 64]),
                'broker_cpu_pct': round(random.uniform(20, 80), 2),
                'broker_network_in_mb': round(random.uniform(10, 1000), 2),
                'broker_network_out_mb': round(random.uniform(10, 1000), 2)
            })
        
        datasets['kafka_metrics'] = pd.DataFrame(kafka_data)
        
        # hive_query_logs (timeseries)
        n_hive = 1200
        hive_timestamps = pd.date_range(end=now, periods=n_hive, freq='15min')
        query_types = ['SELECT', 'INSERT', 'CREATE', 'ALTER', 'JOIN', 'AGGREGATE']
        databases = ['trading_db', 'risk_db', 'customer_db', 'analytics_db', 'reporting_db']
        users = ['etl_user', 'analyst_user', 'app_service', 'data_scientist', 'reporting_svc']
        
        hive_data = []
        for i, ts in enumerate(hive_timestamps):
            host = random.choice(host_ids)
            app = random.choice(app_ids)
            q_type = random.choice(query_types)
            db = random.choice(databases)
            
            query_templates = [
                "SELECT * FROM {db}.transactions WHERE trade_date > '2024-01-01' AND amount > 1000000",
                "INSERT INTO {db}.daily_summary SELECT account_id, SUM(amount) FROM {db}.transactions GROUP BY account_id",
                "CREATE TABLE {db}.temp_results AS SELECT * FROM {db}.source_table WHERE status = 'active'",
                "SELECT t1.*, t2.risk_score FROM {db}.trades t1 JOIN {db}.risk_metrics t2 ON t1.trade_id = t2.trade_id"
            ]
            
            hive_data.append({
                'query_id': f'query-{i:07d}',
                '@timestamp': ts,
                'host_id': host,
                'application_id': app,
                'query_execution_time_ms': int(random.uniform(1000, 300000)),
                'data_scanned_gb': round(random.uniform(0.1, 500), 2),
                'rows_returned': int(random.uniform(100, 10000000)),
                'query_type': q_type,
                'database_name': db,
                'user_name': random.choice(users),
                'query_text': random.choice(query_templates).format(db=db)
            })
        
        datasets['hive_query_logs'] = pd.DataFrame(hive_data)
        
        # cost_allocation (reference)
        n_cost = 50
        cost_centers = list(set([app['cost_center'] for app in apps_data]))[:n_cost]
        
        cost_data = []
        for cc in cost_centers:
            bu = random.choice(business_units)
            dept = random.choice(['Infrastructure', 'Application Development', 'Data Engineering', 'Platform Engineering'])
            budget = round(random.uniform(500000, 10000000), 2)
            spend = round(budget * random.uniform(0.5, 0.95), 2)
            
            cost_data.append({
                'cost_center': cc,
                'business_unit': bu,
                'department': dept,
                'budget_annual_usd': budget,
                'current_spend_usd': spend,
                'intel_host_count': random.randint(10, 100),
                'amd_host_count': random.randint(0, 50),
                'target_cost_reduction_pct': round(random.uniform(15, 35), 2),
                'migration_budget_usd': round(random.uniform(50000, 500000), 2)
            })
        
        datasets['cost_allocation'] = pd.DataFrame(cost_data)
        
        return datasets

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships from requirements"""
        return [
            ('infrastructure_metrics', 'host_id', 'compute_hosts'),
            ('infrastructure_metrics', 'application_id', 'applications'),
            ('infrastructure_metrics', 'benchmark_id', 'benchmark_definitions'),
            ('kafka_metrics', 'host_id', 'compute_hosts'),
            ('hive_query_logs', 'host_id', 'compute_hosts'),
            ('hive_query_logs', 'application_id', 'applications'),
            ('cost_allocation', 'cost_center', 'applications')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {
            'infrastructure_metrics': 'Time-series performance metrics from compute infrastructure across Intel and AMD platforms',
            'compute_hosts': 'Physical and virtual compute hosts with hardware specifications and cost data',
            'applications': 'Application catalog with business criticality, SLAs, and migration status',
            'benchmark_definitions': 'Standardized performance benchmark definitions and success criteria',
            'kafka_metrics': 'Real-time streaming metrics from Kafka brokers and topics',
            'hive_query_logs': 'Historical query execution logs from Hive data warehouse',
            'cost_allocation': 'Cost center budget allocation and infrastructure spend tracking'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        """Return fields that should use semantic_text mapping"""
        return {
            'infrastructure_metrics': ['anomaly_notes'],
            'compute_hosts': ['host_profile_description'],
            'applications': ['application_characteristics'],
            'benchmark_definitions': ['benchmark_description'],
            'hive_query_logs': ['query_text']
        }
