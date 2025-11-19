
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List

class TMobileDataGenerator(DataGeneratorModule):
    """Data generator for T-Mobile - Network Operations"""

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

        # Reference data: mme_hosts (50 rows)
        n_mme = 50
        clusters = ['cluster-east-1', 'cluster-east-2', 'cluster-west-1', 'cluster-west-2', 'cluster-central']
        datacenters = ['dc-newyork', 'dc-atlanta', 'dc-dallas', 'dc-seattle', 'dc-chicago']
        regions = ['northeast', 'southeast', 'southwest', 'northwest', 'central']
        vendors = ['Ericsson', 'Nokia', 'Cisco', 'Huawei']
        versions = ['R15.2', 'R15.3', 'R16.1', 'R16.2', 'R17.0']
        roles = ['active', 'standby', 'backup']
        
        datasets['mme_hosts'] = pd.DataFrame({
            'mme_host': [f'mme-{region[:2]}-{i:02d}' for i, region in enumerate(np.random.choice(regions, n_mme), 1)],
            'cluster_id': np.random.choice(clusters, n_mme),
            'datacenter': np.random.choice(datacenters, n_mme),
            'region': np.random.choice(regions, n_mme),
            'vendor': np.random.choice(vendors, n_mme),
            'software_version': np.random.choice(versions, n_mme),
            'max_subscriber_capacity': np.random.choice([50000, 100000, 150000, 200000], n_mme),
            'role': self.safe_choice(roles, n_mme, weights=[0.6, 0.3, 0.1]),
            'deployment_date': pd.date_range(end=datetime.now() - timedelta(days=180), periods=n_mme, freq='7D')
        })

        # Reference data: cells (500 rows)
        n_cells = 500
        technologies = ['4G-LTE', '5G-NSA', '5G-SA']
        cell_vendors = ['Ericsson', 'Nokia', 'Samsung']
        
        datasets['cells'] = pd.DataFrame({
            'cell_id': [f'cell-{i:05d}' for i in range(1, n_cells + 1)],
            'cell_name': [f'Tower {reg.upper()}-{i:04d}' for i, reg in enumerate(np.random.choice(regions, n_cells), 1)],
            'technology': self.safe_choice(technologies, n_cells, weights=[0.5, 0.3, 0.2]),
            'region': np.random.choice(regions, n_cells),
            'latitude': np.random.uniform(25.0, 49.0, n_cells),
            'longitude': np.random.uniform(-125.0, -65.0, n_cells),
            'max_prb_capacity': np.random.choice([50, 100, 150, 200], n_cells),
            'vendor': np.random.choice(cell_vendors, n_cells),
            'deployment_date': pd.date_range(end=datetime.now() - timedelta(days=365), periods=n_cells, freq='D'),
            'neighbor_cell_list': [','.join([f'cell-{np.random.randint(1, n_cells):05d}' for _ in range(np.random.randint(3, 8))]) for _ in range(n_cells)]
        })

        # Reference data: hss_nodes (20 rows)
        n_hss = 20
        node_roles = ['primary', 'secondary', 'backup']
        db_types = ['Oracle RAC', 'PostgreSQL', 'MySQL Cluster']
        
        datasets['hss_nodes'] = pd.DataFrame({
            'hss_node': [f'hss-{dc[:2]}-{i:02d}' for i, dc in enumerate(np.random.choice(datacenters, n_hss), 1)],
            'node_role': self.safe_choice(node_roles, n_hss, weights=[0.5, 0.3, 0.2]),
            'datacenter': np.random.choice(datacenters, n_hss),
            'region': np.random.choice(regions, n_hss),
            'database_type': np.random.choice(db_types, n_hss),
            'replication_master': [f'hss-{dc[:2]}-{np.random.randint(1, 10):02d}' for dc in np.random.choice(datacenters, n_hss)],
            'max_tps_capacity': np.random.choice([5000, 10000, 15000, 20000], n_hss),
            'deployment_date': pd.date_range(end=datetime.now() - timedelta(days=730), periods=n_hss, freq='30D')
        })

        # Reference data: customer_segments (10 rows)
        n_segments = 10
        datasets['customer_segments'] = pd.DataFrame({
            'segment_id': [f'seg-{i:02d}' for i in range(1, n_segments + 1)],
            'segment_name': ['Enterprise Premium', 'Enterprise Standard', 'Government', 'Small Business', 
                           'Consumer Premium', 'Consumer Standard', 'Consumer Basic', 'IoT', 'MVNO', 'Wholesale'],
            'segment_type': ['enterprise', 'enterprise', 'government', 'business', 
                           'consumer', 'consumer', 'consumer', 'iot', 'wholesale', 'wholesale'],
            'monthly_arpu_usd': [250.0, 150.0, 180.0, 80.0, 120.0, 75.0, 45.0, 5.0, 30.0, 20.0],
            'sla_availability_pct': [99.99, 99.9, 99.95, 99.5, 99.0, 98.5, 98.0, 99.0, 98.0, 97.5],
            'sla_penalty_per_hour_usd': [10000.0, 5000.0, 7500.0, 1000.0, 500.0, 250.0, 100.0, 200.0, 300.0, 150.0],
            'business_priority': [1, 2, 1, 3, 2, 3, 4, 3, 4, 5]
        })

        # Get reference keys
        mme_hosts = datasets['mme_hosts']['mme_host'].tolist()
        cell_ids = datasets['cells']['cell_id'].tolist()
        hss_nodes = datasets['hss_nodes']['hss_node'].tolist()
        segment_ids = datasets['customer_segments']['segment_id'].tolist()
        cluster_ids = datasets['mme_hosts']['cluster_id'].unique().tolist()
        tac_list = [f'tac-{i:04d}' for i in range(1, 101)]

        # Timeseries: mme_signaling_events (10000 rows)
        n_sig = 10000
        proc_types = ['Attach', 'Detach', 'TAU', 'Service Request', 'PDN Connectivity', 'Bearer Modification']
        proc_results = ['success', 'failure', 'timeout', 'rejected']
        reject_causes = ['no_reject', 'network_failure', 'congestion', 'auth_failure', 'roaming_not_allowed', 'unknown_subscriber']
        s1ap_types = ['InitialUEMessage', 'UplinkNASTransport', 'DownlinkNASTransport', 'InitialContextSetup', 'UEContextRelease']
        sig_interfaces = ['S1-MME', 'S6a', 'S11', 'S10']
        msg_directions = ['uplink', 'downlink']
        
        datasets['mme_signaling_events'] = pd.DataFrame({
            '@timestamp': pd.date_range(end=datetime.now(), periods=n_sig, freq='30S'),
            'event_id': [f'evt-{i:08d}' for i in range(1, n_sig + 1)],
            'mme_host': np.random.choice(mme_hosts, n_sig),
            'cluster_id': np.random.choice(cluster_ids, n_sig),
            'datacenter': np.random.choice(datacenters, n_sig),
            'procedure_type': self.safe_choice(proc_types, n_sig, weights=[0.3, 0.1, 0.25, 0.2, 0.1, 0.05]),
            'procedure_result': self.safe_choice(proc_results, n_sig, weights=[0.85, 0.08, 0.04, 0.03]),
            'procedure_latency_ms': np.random.lognormal(4.5, 0.8, n_sig).astype(int),
            'cell_id': np.random.choice(cell_ids, n_sig),
            'tracking_area_code': np.random.choice(tac_list, n_sig),
            'imsi_hash': [f'imsi-{np.random.randint(100000, 999999):06d}' for _ in range(n_sig)],
            'reject_cause': self.safe_choice(reject_causes, n_sig, weights=[0.85, 0.05, 0.04, 0.03, 0.02, 0.01]),
            's1ap_message_type': np.random.choice(s1ap_types, n_sig),
            'signaling_interface': self.safe_choice(sig_interfaces, n_sig, weights=[0.5, 0.25, 0.15, 0.1]),
            'message_direction': np.random.choice(msg_directions, n_sig)
        })

        # Timeseries: diameter_transactions (12000 rows)
        n_diam = 12000
        cmd_codes = ['Authentication-Information', 'Update-Location', 'Cancel-Location', 'Insert-Subscriber-Data', 'Purge-UE']
        app_ids = ['16777251', '16777238', '16777216']
        result_codes = ['2001', '3002', '5001', '5003', '5004', '5012']
        
        datasets['diameter_transactions'] = pd.DataFrame({
            '@timestamp': pd.date_range(end=datetime.now(), periods=n_diam, freq='25S'),
            'transaction_id': [f'txn-{i:010d}' for i in range(1, n_diam + 1)],
            'command_code': self.safe_choice(cmd_codes, n_diam, weights=[0.4, 0.3, 0.1, 0.1, 0.1]),
            'application_id': np.random.choice(app_ids, n_diam),
            'result_code': self.safe_choice(result_codes, n_diam, weights=[0.92, 0.03, 0.02, 0.01, 0.01, 0.01]),
            'origin_host': np.random.choice(mme_hosts, n_diam),
            'destination_host': np.random.choice(hss_nodes, n_diam),
            'response_time_ms': np.random.lognormal(3.5, 0.9, n_diam).astype(int),
            'imsi_hash': [f'imsi-{np.random.randint(100000, 999999):06d}' for _ in range(n_diam)],
            'hss_node': np.random.choice(hss_nodes, n_diam),
            'mme_host': np.random.choice(mme_hosts, n_diam),
            'transaction_success': self.safe_choice([True, False], n_diam, weights=[0.95, 0.05])
        })

        # Timeseries: handoff_events (8000 rows)
        n_handoff = 8000
        handoff_types = ['X2', 'S1', 'intra-cell', 'inter-freq']
        handoff_results = ['success', 'failure', 'timeout']
        failure_reasons = ['none', 'target_cell_congestion', 'weak_signal', 'handoff_timeout', 'resource_unavailable']
        
        datasets['handoff_events'] = pd.DataFrame({
            '@timestamp': pd.date_range(end=datetime.now(), periods=n_handoff, freq='40S'),
            'handoff_id': [f'ho-{i:08d}' for i in range(1, n_handoff + 1)],
            'handoff_type': self.safe_choice(handoff_types, n_handoff, weights=[0.5, 0.3, 0.15, 0.05]),
            'source_cell_id': np.random.choice(cell_ids, n_handoff),
            'target_cell_id': np.random.choice(cell_ids, n_handoff),
            'handoff_result': self.safe_choice(handoff_results, n_handoff, weights=[0.88, 0.08, 0.04]),
            'failure_reason': self.safe_choice(failure_reasons, n_handoff, weights=[0.88, 0.04, 0.03, 0.03, 0.02]),
            'handoff_latency_ms': np.random.lognormal(4.0, 0.7, n_handoff).astype(int),
            'imsi_hash': [f'imsi-{np.random.randint(100000, 999999):06d}' for _ in range(n_handoff)],
            'mme_host': np.random.choice(mme_hosts, n_handoff),
            'ue_signal_strength_dbm': np.random.randint(-120, -60, n_handoff)
        })

        # Timeseries: security_events (2000 rows)
        n_sec = 2000
        event_types = ['SS7_Attack', 'Diameter_Attack', 'Rogue_Network', 'Malformed_Message', 'Rate_Limit_Exceeded']
        attack_types = ['IMSI_Catching', 'Location_Tracking', 'SMS_Interception', 'Fraud_Attempt', 'DoS_Attack', 'Scanning']
        src_networks = ['roaming-partner-01', 'roaming-partner-02', 'unknown-network', 'domestic-mvno', 'international-roam']
        severities = ['critical', 'high', 'medium', 'low']
        interfaces = ['SS7', 'Diameter', 'S1-MME', 'S6a']
        attack_descs = [
            'Suspicious IMSI probing detected from foreign network attempting to track subscriber location',
            'Multiple authentication requests from unknown global title indicating potential fraud',
            'Abnormal message rate detected suggesting coordinated attack or misconfiguration',
            'Malformed Diameter message received with invalid AVP structure from roaming partner',
            'SS7 MAP message with suspicious routing detected attempting subscriber interception',
            'Rate limit exceeded for location update requests from single source network',
            'Unauthorized access attempt blocked at network perimeter firewall',
            'Potential SMS interception attack detected based on message pattern analysis'
        ]
        
        datasets['security_events'] = pd.DataFrame({
            '@timestamp': pd.date_range(end=datetime.now(), periods=n_sec, freq='3min'),
            'event_id': [f'sec-{i:07d}' for i in range(1, n_sec + 1)],
            'event_type': self.safe_choice(event_types, n_sec, weights=[0.3, 0.25, 0.2, 0.15, 0.1]),
            'attack_type': self.safe_choice(attack_types, n_sec, weights=[0.25, 0.2, 0.15, 0.15, 0.15, 0.1]),
            'source_network': np.random.choice(src_networks, n_sec),
            'source_ip': [f'{np.random.randint(10, 200)}.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}' for _ in range(n_sec)],
            'source_global_title': [f'+{np.random.randint(1, 999)}{np.random.randint(1000000000, 9999999999)}' for _ in range(n_sec)],
            'target_imsi_hash': [f'imsi-{np.random.randint(100000, 999999):06d}' for _ in range(n_sec)],
            'blocked': self.safe_choice([True, False], n_sec, weights=[0.85, 0.15]),
            'severity': self.safe_choice(severities, n_sec, weights=[0.1, 0.25, 0.45, 0.2]),
            'interface': self.safe_choice(interfaces, n_sec, weights=[0.35, 0.35, 0.2, 0.1]),
            'attack_description': np.random.choice(attack_descs, n_sec)
        })

        # Timeseries: subscriber_sessions (9000 rows)
        n_sess = 9000
        session_types = ['data', 'voice', 'sms', 'mms', 'ims']
        apns = ['internet', 'ims', 'mms', 'wap', 'enterprise.apn']
        qci_values = [5, 6, 7, 8, 9]
        session_results = ['normal_release', 'abnormal_release', 'timeout', 'handoff_drop']
        
        datasets['subscriber_sessions'] = pd.DataFrame({
            '@timestamp': pd.date_range(end=datetime.now(), periods=n_sess, freq='35S'),
            'session_id': [f'sess-{i:010d}' for i in range(1, n_sess + 1)],
            'imsi_hash': [f'imsi-{np.random.randint(100000, 999999):06d}' for _ in range(n_sess)],
            'mme_host': np.random.choice(mme_hosts, n_sess),
            'cell_id': np.random.choice(cell_ids, n_sess),
            'tracking_area_code': np.random.choice(tac_list, n_sess),
            'session_type': self.safe_choice(session_types, n_sess, weights=[0.6, 0.2, 0.1, 0.05, 0.05]),
            'apn': self.safe_choice(apns, n_sess, weights=[0.5, 0.2, 0.1, 0.1, 0.1]),
            'qci': np.random.choice(qci_values, n_sess),
            'session_duration_seconds': np.random.lognormal(6.0, 1.5, n_sess).astype(int),
            'data_volume_mb': np.random.lognormal(2.5, 2.0, n_sess),
            'session_result': self.safe_choice(session_results, n_sess, weights=[0.90, 0.05, 0.03, 0.02]),
            'customer_segment': np.random.choice(segment_ids, n_sess)
        })

        return datasets

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships from requirements"""
        return [
            ('mme_signaling_events', 'mme_host', 'mme_hosts'),
            ('mme_signaling_events', 'cell_id', 'cells'),
            ('diameter_transactions', 'hss_node', 'hss_nodes'),
            ('diameter_transactions', 'mme_host', 'mme_hosts'),
            ('handoff_events', 'source_cell_id', 'cells'),
            ('handoff_events', 'target_cell_id', 'cells'),
            ('subscriber_sessions', 'mme_host', 'mme_hosts'),
            ('subscriber_sessions', 'cell_id', 'cells'),
            ('subscriber_sessions', 'customer_segment', 'customer_segments')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {
            'mme_signaling_events': 'MME signaling events tracking subscriber procedures and authentication',
            'diameter_transactions': 'Diameter protocol transactions between MME and HSS nodes',
            'handoff_events': 'Cell tower handoff events tracking mobility and failures',
            'security_events': 'Security events including SS7 attacks and rogue network attempts',
            'subscriber_sessions': 'Subscriber data sessions with QoS and customer segment info',
            'mme_hosts': 'MME host configuration and capacity information',
            'cells': 'Cell tower configuration and location data',
            'hss_nodes': 'HSS node configuration and database information',
            'customer_segments': 'Customer segments with SLA and business priority'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        """Return fields that should use semantic_text mapping"""
        return {
            'security_events': ['attack_description']
        }
