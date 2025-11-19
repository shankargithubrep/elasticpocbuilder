
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List

class TMobileDataGenerator(DataGeneratorModule):
    """Data generator for T-Mobile - Network Operations & Engineering"""

    @staticmethod
    def safe_choice(choices, size=None, weights=None, replace=True):
        if weights is not None:
            weights = np.array(weights, dtype=float)
            probabilities = weights / weights.sum()
            return np.random.choice(choices, size=size, p=probabilities, replace=replace)
        else:
            return np.random.choice(choices, size=size, replace=replace)

    @staticmethod
    def random_timedelta(start_date, end_date=None, days=None, hours=None, minutes=None):
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
        datasets = {}
        
        vendors = ['Ericsson', 'Nokia', 'Samsung']
        regions = ['Northeast', 'Southeast', 'Midwest', 'Southwest', 'West', 'Northwest', 
                   'Central', 'Mountain', 'Pacific', 'Atlantic', 'Gulf', 'Great Lakes', 
                   'Mid-Atlantic', 'South Central', 'North Central']
        technologies = ['LTE', '5G NR', 'LTE-A']
        markets = ['Urban', 'Suburban', 'Rural', 'Dense Urban', 'Highway']
        capacity_tiers = ['Tier 1 (High)', 'Tier 2 (Medium)', 'Tier 3 (Low)', 'Tier 4 (Very High)']
        backhaul_types = ['Fiber', 'Microwave', 'Millimeter Wave', 'Hybrid']
        noc_teams = [f'NOC-{region}' for region in ['NE', 'SE', 'MW', 'SW', 'W', 'NW', 'C', 'MT', 
                                                      'PA', 'AT', 'GU', 'GL', 'MA', 'SC', 'NC']]
        
        # cell_site_inventory (reference)
        n_cells = 150
        cell_ids = [f'CELL-{i:06d}' for i in range(1, n_cells + 1)]
        enodeb_ids = [f'ENB-{i:05d}' for i in range(1, n_cells + 1)]
        
        cell_characteristics_templates = [
            "High-capacity {technology} cell serving {market} area with {vendor} equipment, {backhaul} backhaul connectivity",
            "{technology} macro cell with {capacity} capacity tier, optimized for {market} deployment using {vendor} RAN",
            "Carrier aggregation enabled {technology} site with {backhaul} transport, serving high-density {market} zone",
            "{vendor} {technology} cell with advanced MIMO configuration, {capacity} capacity serving {market} subscribers",
            "Multi-band {technology} site with {backhaul} backhaul, {capacity} tier deployment in {market} environment"
        ]
        
        datasets['cell_site_inventory'] = pd.DataFrame({
            'cell_id': cell_ids,
            'enodeb_id': enodeb_ids,
            'cell_name': [f'{random.choice(["Metro", "Tower", "Site", "Station"])} {random.choice(["Alpha", "Beta", "Gamma", "Delta", "Omega"])} {i}' 
                          for i in range(1, n_cells + 1)],
            'site_id': [f'SITE-{i:05d}' for i in range(1, n_cells + 1)],
            'latitude': np.random.uniform(25.0, 49.0, n_cells),
            'longitude': np.random.uniform(-125.0, -65.0, n_cells),
            'region': self.safe_choice(regions, n_cells),
            'market': self.safe_choice(markets, n_cells),
            'vendor': self.safe_choice(vendors, n_cells),
            'technology': self.safe_choice(technologies, n_cells, weights=[0.4, 0.4, 0.2]),
            'capacity_tier': self.safe_choice(capacity_tiers, n_cells),
            'max_subscribers': np.random.randint(500, 5000, n_cells),
            'backhaul_type': self.safe_choice(backhaul_types, n_cells, weights=[0.5, 0.2, 0.15, 0.15]),
            'noc_team': self.safe_choice(noc_teams, n_cells),
            'deployment_date': pd.date_range(end=datetime.now(), periods=n_cells, freq='-30D')
        })
        
        datasets['cell_site_inventory']['cell_characteristics'] = [
            random.choice(cell_characteristics_templates).format(
                technology=row['technology'],
                market=row['market'],
                vendor=row['vendor'],
                backhaul=row['backhaul_type'],
                capacity=row['capacity_tier']
            ) for _, row in datasets['cell_site_inventory'].iterrows()
        ]
        
        # vendor_equipment (reference)
        equipment_data = []
        for vendor in vendors:
            models = [f'{vendor}-{tech}-{i}' for tech in ['LTE', '5G', 'LTE-A'] for i in range(1, 4)]
            for model in models:
                tech = 'LTE' if 'LTE' in model and '5G' not in model else ('5G NR' if '5G' in model else 'LTE-A')
                equipment_data.append({
                    'vendor': vendor,
                    'equipment_model': model,
                    'technology': tech,
                    'software_version': f'v{np.random.randint(5, 12)}.{np.random.randint(0, 10)}.{np.random.randint(0, 20)}',
                    'baseline_prb_utilization': np.random.uniform(40, 65),
                    'baseline_connection_success_rate': np.random.uniform(97, 99.5),
                    'known_issues': random.choice([
                        f'{vendor} {tech} equipment experiencing intermittent handover failures in high-mobility scenarios',
                        f'Software version compatibility issues with legacy core network elements for {vendor} {tech}',
                        f'{tech} carrier aggregation instability during peak traffic periods on {vendor} equipment',
                        f'{vendor} {tech} RAN showing elevated signaling load during mass attach events',
                        f'Known memory leak in {vendor} {tech} software causing periodic performance degradation'
                    ]),
                    'optimization_recommendations': random.choice([
                        f'Upgrade {vendor} {tech} software to latest patch release for improved handover performance',
                        f'Adjust PRB allocation algorithm parameters for better load balancing on {vendor} {tech} cells',
                        f'Enable advanced interference mitigation features for {tech} deployments in dense areas',
                        f'Implement carrier aggregation tuning for {vendor} {tech} to optimize throughput',
                        f'Configure dynamic spectrum sharing parameters for {tech} efficiency on {vendor} equipment'
                    ])
                })
        
        datasets['vendor_equipment'] = pd.DataFrame(equipment_data[:100])
        
        # subscriber_profiles (reference)
        n_subs = 200
        imsis = [f'310260{i:09d}' for i in range(1, n_subs + 1)]
        plan_types = ['Unlimited Elite', 'Magenta Max', 'Essentials', 'Business Unlimited', 'Prepaid']
        device_models = ['iPhone 15 Pro', 'iPhone 14', 'Samsung Galaxy S24', 'Galaxy S23', 'Pixel 8', 
                         'OnePlus 11', 'Motorola Edge', 'iPhone 13', 'Galaxy A54', 'iPhone 12']
        device_capabilities = ['5G mmWave', '5G Sub-6', 'LTE Advanced', 'LTE Cat 4']
        segments = ['Premium', 'Standard', 'Value', 'Enterprise', 'MVNO']
        
        behavior_templates = [
            "{segment} subscriber with {device} on {plan} plan, average {usage}GB monthly usage, {behavior_pattern}",
            "{plan} customer using {device}, {segment} tier with {churn_status} churn risk, typical usage {usage}GB/month",
            "Long-term {segment} subscriber on {plan}, {device} user with {behavior_pattern}, {usage}GB average consumption",
            "{device} user in {segment} segment, {plan} plan with {churn_status} retention risk, {usage}GB monthly data",
            "{segment} tier customer with {device}, {plan} subscription, {behavior_pattern}, averaging {usage}GB per month"
        ]
        
        datasets['subscriber_profiles'] = pd.DataFrame({
            'imsi': imsis,
            'subscriber_id': [f'SUB-{i:08d}' for i in range(1, n_subs + 1)],
            'plan_type': self.safe_choice(plan_types, n_subs),
            'device_model': self.safe_choice(device_models, n_subs),
            'device_capability': self.safe_choice(device_capabilities, n_subs, weights=[0.25, 0.35, 0.25, 0.15]),
            'subscriber_segment': self.safe_choice(segments, n_subs),
            'lifetime_value': np.random.uniform(500, 15000, n_subs),
            'avg_monthly_usage_gb': np.random.uniform(5, 150, n_subs),
            'activation_date': pd.date_range(end=datetime.now(), periods=n_subs, freq='-15D'),
            'churn_risk_score': np.random.uniform(0.05, 0.85, n_subs)
        })
        
        datasets['subscriber_profiles']['subscriber_behavior_profile'] = [
            behavior_templates[i % len(behavior_templates)].format(
                segment=row['subscriber_segment'],
                device=row['device_model'],
                plan=row['plan_type'],
                usage=f"{row['avg_monthly_usage_gb']:.1f}",
                behavior_pattern=random.choice(['heavy video streaming', 'business data usage', 
                                               'social media focused', 'balanced usage pattern',
                                               'peak hour heavy user']),
                churn_status=('high' if row['churn_risk_score'] > 0.6 else 
                             'medium' if row['churn_risk_score'] > 0.3 else 'low')
            ) for i, (_, row) in enumerate(datasets['subscriber_profiles'].iterrows())
        ]
        
        # network_cell_performance (timeseries)
        n_perf = 3000
        timestamps = pd.date_range(end=datetime.now(), periods=n_perf, freq='15min')
        
        datasets['network_cell_performance'] = pd.DataFrame({
            '@timestamp': timestamps,
            'event_id': [f'EVT-{i:010d}' for i in range(1, n_perf + 1)],
            'cell_id': self.safe_choice(cell_ids, n_perf),
            'enodeb_id': self.safe_choice(enodeb_ids, n_perf),
            'network.radio.rsrp_dbm': np.random.uniform(-120, -70, n_perf),
            'network.radio.rsrq_db': np.random.uniform(-20, -5, n_perf),
            'network.radio.sinr_db': np.random.uniform(-5, 25, n_perf),
            'network.cell.prb_utilization_dl_pct': np.random.uniform(20, 95, n_perf),
            'network.cell.prb_utilization_ul_pct': np.random.uniform(15, 85, n_perf),
            'network.rrc.connection_success_rate': np.random.uniform(92, 99.9, n_perf),
            'network.handover.success_rate': np.random.uniform(90, 99.5, n_perf),
            'network.procedure.attach_success_rate': np.random.uniform(93, 99.8, n_perf),
            'network.voice.call_drop_rate': np.random.uniform(0.1, 5.0, n_perf),
            'network.data.session_drop_rate': np.random.uniform(0.2, 4.5, n_perf),
            'network.imsi_count': np.random.randint(50, 2000, n_perf),
            'vendor': self.safe_choice(vendors, n_perf),
            'region': self.safe_choice(regions, n_perf),
            'technology': self.safe_choice(technologies, n_perf, weights=[0.4, 0.4, 0.2])
        })
        
        # subscriber_sessions (timeseries)
        n_sessions = 2500
        session_timestamps = pd.date_range(end=datetime.now(), periods=n_sessions, freq='30s')
        apns = ['internet', 'ims', 'mms', 'vzwinternet', 'vzwims']
        procedure_types = ['Attach', 'Detach', 'TAU', 'Service Request', 'Bearer Modification', 'Handover']
        failure_causes = ['Network Failure', 'UE Not Responding', 'Congestion', 'Authentication Failure', 
                          'Resource Unavailable', 'Timeout', 'Protocol Error']
        auth_results = ['Success', 'Failed', 'Timeout']
        
        session_desc_templates = [
            "{procedure} procedure for IMSI {imsi} on cell {cell_id}, {result} with {duration}s duration, {data}MB transferred",
            "Subscriber session on {apn} APN, {procedure} {result}, experience score {score:.2f}, {handovers} handovers",
            "{procedure} for {apn} service, {result} after {duration}s, latency {latency}ms, {data}MB data volume",
            "Mobile session with {handovers} handovers, {procedure} procedure {result}, {score:.2f} experience score",
            "{apn} session: {procedure} {result}, {duration}s duration, {latency}ms latency, packet loss {loss}%"
        ]
        
        datasets['subscriber_sessions'] = pd.DataFrame({
            '@timestamp': session_timestamps,
            'session_id': [f'SESS-{i:012d}' for i in range(1, n_sessions + 1)],
            'imsi': self.safe_choice(imsis, n_sessions),
            'cell_id': self.safe_choice(cell_ids, n_sessions),
            'mme_id': self.safe_choice([f'MME-{i:02d}' for i in range(1, 81)], n_sessions),
            'apn': self.safe_choice(apns, n_sessions, weights=[0.5, 0.2, 0.1, 0.15, 0.05]),
            'subscriber.experience.score': np.random.uniform(1.0, 5.0, n_sessions),
            'network.transport.latency_ms': np.random.uniform(10, 250, n_sessions),
            'network.transport.packet_loss_pct': np.random.uniform(0, 8, n_sessions),
            'network.procedure.type': self.safe_choice(procedure_types, n_sessions),
            'network.procedure.success': self.safe_choice([True, False], n_sessions, weights=[0.92, 0.08]),
            'network.auth.result': self.safe_choice(auth_results, n_sessions, weights=[0.95, 0.03, 0.02]),
            'session_duration_sec': np.random.randint(10, 7200, n_sessions),
            'data_volume_mb': np.random.uniform(0.5, 500, n_sessions),
            'handover_count': np.random.randint(0, 15, n_sessions)
        })
        
        datasets['subscriber_sessions']['network.procedure.failure_cause'] = [
            random.choice(failure_causes) if not success else None 
            for success in datasets['subscriber_sessions']['network.procedure.success']
        ]
        
        datasets['subscriber_sessions']['session_description'] = [
            session_desc_templates[i % len(session_desc_templates)].format(
                procedure=row['network.procedure.type'],
                imsi=row['imsi'],
                cell_id=row['cell_id'],
                result='succeeded' if row['network.procedure.success'] else 'failed',
                duration=row['session_duration_sec'],
                data=f"{row['data_volume_mb']:.1f}",
                apn=row['apn'],
                score=row['subscriber.experience.score'],
                handovers=row['handover_count'],
                latency=f"{row['network.transport.latency_ms']:.1f}",
                loss=f"{row['network.transport.packet_loss_pct']:.2f}"
            ) for i, (_, row) in enumerate(datasets['subscriber_sessions'].iterrows())
        ]
        
        # network_incidents (timeseries)
        n_incidents = 1500
        incident_timestamps = pd.date_range(end=datetime.now(), periods=n_incidents, freq='45min')
        severities = ['Critical', 'High', 'Medium', 'Low']
        incident_types = ['Cell Outage', 'Degraded Performance', 'Capacity Congestion', 'Handover Failure',
                         'Transport Issue', 'Equipment Alarm', 'Configuration Error', 'Software Bug']
        root_causes = ['Hardware Failure', 'Software Bug', 'Configuration Error', 'Capacity Limit',
                      'Transport Issue', 'Power Failure', 'Environmental', 'Vendor Issue', 'Unknown']
        detection_methods = ['ML Anomaly Detection', 'Threshold Alert', 'Subscriber Complaint', 
                            'NOC Monitoring', 'Automated Health Check', 'Vendor Alarm']
        
        incident_desc_templates = [
            "{incident_type} on cell {cell_id} affecting {affected} subscribers, {severity} severity, detected via {detection}",
            "{severity} incident: {incident_type} in {region}, root cause {root_cause}, MTTD {mttd:.1f}min MTTR {mttr:.1f}min",
            "Cell site {cell_id} experiencing {incident_type}, {affected} subscribers impacted, {detection} detection method",
            "{incident_type} incident ({severity}) affecting {region} region, {root_cause} identified, {status}",
            "{vendor} equipment {incident_type} on {cell_id}, {affected} users affected, resolved via {resolution}"
        ]
        
        resolution_templates = [
            "Remote {action} performed by {noc_team}, cell service restored after {mttr:.0f} minutes",
            "On-site technician dispatched, {action} completed, {root_cause} addressed",
            "Automated recovery procedure executed, {action} applied, monitoring for recurrence",
            "{noc_team} performed {action}, root cause {root_cause} mitigated, service normalized",
            "Vendor support engaged, {action} implemented, {root_cause} resolved permanently"
        ]
        
        datasets['network_incidents'] = pd.DataFrame({
            '@timestamp': incident_timestamps,
            'incident_id': [f'INC-{i:08d}' for i in range(1, n_incidents + 1)],
            'cell_id': self.safe_choice(cell_ids, n_incidents),
            'enodeb_id': self.safe_choice(enodeb_ids, n_incidents),
            'severity': self.safe_choice(severities, n_incidents, weights=[0.1, 0.25, 0.45, 0.2]),
            'incident_type': self.safe_choice(incident_types, n_incidents),
            'affected_subscribers': np.random.randint(5, 1500, n_incidents),
            'incident.mttd_minutes': np.random.uniform(1, 45, n_incidents),
            'incident.mttr_minutes': np.random.uniform(10, 240, n_incidents),
            'root_cause': self.safe_choice(root_causes, n_incidents),
            'detection_method': self.safe_choice(detection_methods, n_incidents, weights=[0.3, 0.25, 0.15, 0.15, 0.1, 0.05]),
            'noc_team': self.safe_choice(noc_teams, n_incidents),
            'vendor': self.safe_choice(vendors, n_incidents),
            'region': self.safe_choice(regions, n_incidents),
            'resolved': self.safe_choice([True, False], n_incidents, weights=[0.85, 0.15])
        })
        
        actions = ['configuration rollback', 'software patch', 'equipment reset', 'parameter optimization',
                   'capacity upgrade', 'hardware replacement', 'traffic rerouting', 'alarm clearance']
        
        datasets['network_incidents']['resolution_action'] = [
            resolution_templates[i % len(resolution_templates)].format(
                action=random.choice(actions),
                noc_team=row['noc_team'],
                mttr=row['incident.mttr_minutes'],
                root_cause=row['root_cause']
            ) if row['resolved'] else 'Incident investigation in progress, resolution pending'
            for i, (_, row) in enumerate(datasets['network_incidents'].iterrows())
        ]
        
        datasets['network_incidents']['incident_description'] = [
            incident_desc_templates[i % len(incident_desc_templates)].format(
                incident_type=row['incident_type'],
                cell_id=row['cell_id'],
                affected=row['affected_subscribers'],
                severity=row['severity'],
                detection=row['detection_method'],
                region=row['region'],
                root_cause=row['root_cause'],
                mttd=row['incident.mttd_minutes'],
                mttr=row['incident.mttr_minutes'],
                status='resolved' if row['resolved'] else 'ongoing',
                vendor=row['vendor'],
                resolution=random.choice(actions)
            ) for i, (_, row) in enumerate(datasets['network_incidents'].iterrows())
        ]
        
        # ml_anomaly_scores (timeseries)
        n_anomalies = 2000
        anomaly_timestamps = pd.date_range(end=datetime.now(), periods=n_anomalies, freq='10min')
        metric_names = ['prb_utilization_dl', 'rrc_connection_success_rate', 'handover_success_rate',
                       'call_drop_rate', 'session_drop_rate', 'rsrp', 'sinr', 'latency']
        anomaly_severities = ['Critical', 'High', 'Medium', 'Low', 'Info']
        detection_rules = ['Population Analysis', 'Time Series Forecast', 'Multi-Metric Correlation',
                          'Threshold Deviation', 'Seasonal Pattern', 'Trend Analysis']
        
        datasets['ml_anomaly_scores'] = pd.DataFrame({
            '@timestamp': anomaly_timestamps,
            'cell_id': self.safe_choice(cell_ids, n_anomalies),
            'metric_name': self.safe_choice(metric_names, n_anomalies),
            'ml.anomaly_score': np.random.uniform(0, 100, n_anomalies),
            'actual_value': np.random.uniform(50, 150, n_anomalies),
            'typical_value': np.random.uniform(60, 120, n_anomalies),
            'deviation_pct': np.random.uniform(-50, 80, n_anomalies),
            'anomaly_severity': self.safe_choice(anomaly_severities, n_anomalies, weights=[0.05, 0.15, 0.35, 0.3, 0.15]),
            'detection_rule': self.safe_choice(detection_rules, n_anomalies),
            'region': self.safe_choice(regions, n_anomalies)
        })
        
        return datasets

    def get_relationships(self) -> List[tuple]:
        return [
            ('network_cell_performance', 'cell_id', 'cell_site_inventory'),
            ('network_cell_performance', 'vendor', 'vendor_equipment'),
            ('subscriber_sessions', 'cell_id', 'cell_site_inventory'),
            ('subscriber_sessions', 'imsi', 'subscriber_profiles'),
            ('network_incidents', 'cell_id', 'cell_site_inventory'),
            ('ml_anomaly_scores', 'cell_id', 'cell_site_inventory')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        return {
            'network_cell_performance': 'Real-time cell site performance metrics including radio quality, PRB utilization, connection success rates, and subscriber counts across nationwide network',
            'cell_site_inventory': 'Comprehensive inventory of cell sites with location, vendor, technology, capacity tier, and deployment information for 50,000+ sites',
            'subscriber_sessions': 'Individual subscriber session data with IMSI-based tracking, procedure outcomes, experience scores, and network performance metrics',
            'subscriber_profiles': 'Subscriber demographic and behavioral profiles including plan types, device capabilities, usage patterns, and churn risk scores for 100M+ subscribers',
            'network_incidents': 'Network incident tracking with MTTD/MTTR metrics, root cause analysis, affected subscribers, and resolution actions across all NOC teams',
            'ml_anomaly_scores': 'Machine learning anomaly detection results with deviation percentages, severity classifications, and detection rule identification',
            'vendor_equipment': 'Vendor equipment catalog with baseline performance metrics, known issues, and optimization recommendations for multi-vendor RAN environment'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        return {
            'cell_site_inventory': ['cell_characteristics'],
            'subscriber_sessions': ['session_description'],
            'subscriber_profiles': ['subscriber_behavior_profile'],
            'network_incidents': ['incident_description', 'resolution_action'],
            'vendor_equipment': ['known_issues', 'optimization_recommendations']
        }
