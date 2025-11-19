
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
        now = datetime.now()
        
        # Reference data first for relationships
        n_cells = 1500
        enb_ids = [f"eNB_{i:04d}" for i in range(1, 201)]
        regions = ['Northeast', 'Southeast', 'Midwest', 'Southwest', 'West', 'Pacific']
        markets = ['Urban', 'Suburban', 'Rural', 'Dense Urban', 'Highway']
        techs = ['LTE', '5G NSA', '5G SA']
        bands = ['Band 2 (1900MHz)', 'Band 4 (AWS)', 'Band 12 (700MHz)', 'Band 66 (AWS-3)', 
                 'Band 71 (600MHz)', 'n41 (2.5GHz)', 'n71 (600MHz)']
        
        datasets['cell_tower_reference'] = pd.DataFrame({
            'cell_id': [f"CELL_{i:05d}" for i in range(1, n_cells + 1)],
            'enb_id': self.safe_choice(enb_ids, n_cells),
            'cell_name': [f"Site_{random.randint(1000, 9999)}_Sector_{random.randint(1, 3)}" for _ in range(n_cells)],
            'site_id': [f"SITE_{i:04d}" for i in np.random.randint(1, 600, n_cells)],
            'latitude': np.random.uniform(25.0, 49.0, n_cells),
            'longitude': np.random.uniform(-125.0, -65.0, n_cells),
            'region': self.safe_choice(regions, n_cells),
            'market': self.safe_choice(markets, n_cells),
            'technology': self.safe_choice(techs, n_cells, weights=[0.5, 0.3, 0.2]),
            'frequency_band': self.safe_choice(bands, n_cells),
            'capacity_rating': self.safe_choice(['Low', 'Medium', 'High', 'Very High'], n_cells, weights=[0.15, 0.35, 0.35, 0.15]),
            'neighbor_cells': [','.join(self.safe_choice([f"CELL_{j:05d}" for j in range(1, n_cells + 1)], 
                                                         random.randint(3, 8), replace=False)) for _ in range(n_cells)],
            'tower_status': self.safe_choice(['Active', 'Degraded', 'Maintenance'], n_cells, weights=[0.92, 0.05, 0.03])
        })
        
        n_mme = 5
        datasets['mme_host_reference'] = pd.DataFrame({
            'mme_host': [f"mme-{i:02d}.tmobile.net" for i in range(1, n_mme + 1)],
            'mme_pool': [f"POOL_{(i-1)//2 + 1}" for i in range(1, n_mme + 1)],
            'datacenter': self.safe_choice(['DC-East', 'DC-West', 'DC-Central'], n_mme),
            'region': self.safe_choice(regions, n_mme),
            'software_version': self.safe_choice(['v5.2.1', 'v5.2.3', 'v5.3.0'], n_mme, weights=[0.2, 0.5, 0.3]),
            'capacity_tier': self.safe_choice(['Tier1', 'Tier2', 'Tier3'], n_mme, weights=[0.4, 0.4, 0.2]),
            'primary_backup': self.safe_choice(['Primary', 'Backup'], n_mme, weights=[0.6, 0.4]),
            'max_subscribers': self.safe_choice([500000, 750000, 1000000], n_mme)
        })
        
        n_causes = 800
        cause_groups = ['Radio Network', 'Transport', 'NAS', 'Protocol', 'Miscellaneous']
        severities = ['Critical', 'Major', 'Minor', 'Warning']
        categories = ['Handover', 'Authentication', 'Resource', 'Configuration', 'Hardware']
        
        datasets['cause_code_reference'] = pd.DataFrame({
            'cause_code': [f"CC_{i:04d}" for i in range(1, n_causes + 1)],
            'cause_group': self.safe_choice(cause_groups, n_causes),
            'cause_description': [f"Cause code {i}: {random.choice(['Radio link failure', 'Resource unavailable', 'Authentication rejected', 'Protocol error', 'Timeout occurred', 'Configuration mismatch', 'Hardware failure', 'Congestion detected'])}" 
                                 for i in range(1, n_causes + 1)],
            'severity': self.safe_choice(severities, n_causes, weights=[0.1, 0.2, 0.4, 0.3]),
            'recommended_action': [random.choice(['Check radio conditions and interference', 'Verify MME capacity and resources', 
                                                 'Review subscriber authentication settings', 'Inspect transport network connectivity',
                                                 'Restart affected network element', 'Escalate to vendor support',
                                                 'Monitor for pattern recurrence', 'Update software to latest version']) 
                                  for _ in range(n_causes)],
            'category': self.safe_choice(categories, n_causes)
        })
        
        n_hss = 8
        datasets['hss_node_reference'] = pd.DataFrame({
            'hss_node': [f"hss-{i:02d}.tmobile.net" for i in range(1, n_hss + 1)],
            'hss_cluster': [f"HSS_Cluster_{(i-1)//2 + 1}" for i in range(1, n_hss + 1)],
            'datacenter': self.safe_choice(['DC-East', 'DC-West', 'DC-Central'], n_hss),
            'database_type': self.safe_choice(['Oracle RAC', 'MySQL Cluster', 'Cassandra'], n_hss, weights=[0.5, 0.3, 0.2]),
            'replication_mode': self.safe_choice(['Master-Master', 'Master-Slave', 'Multi-Master'], n_hss, weights=[0.4, 0.4, 0.2]),
            'capacity_subscribers': self.safe_choice([2000000, 3000000, 5000000], n_hss, weights=[0.3, 0.5, 0.2])
        })
        
        n_threats = 1200
        threat_cats = ['Location Tracking', 'SMS Interception', 'Fraud', 'DoS Attack', 'Spoofing', 'Unauthorized Access']
        
        datasets['threat_signature_reference'] = pd.DataFrame({
            'attack_signature': [f"SIG_{i:05d}" for i in range(1, n_threats + 1)],
            'threat_name': [f"{random.choice(['MAP', 'CAP', 'INAP', 'TCAP'])} {random.choice(['Send Routing Info', 'Provide Subscriber Info', 'Insert Subscriber Data', 'Update Location', 'Any Time Interrogation', 'Send Authentication Info'])} Attack" 
                           for _ in range(n_threats)],
            'threat_category': self.safe_choice(threat_cats, n_threats),
            'threat_description': [f"Detected {random.choice(['anomalous', 'suspicious', 'malicious', 'unauthorized'])} SS7 signaling pattern indicating potential {random.choice(['subscriber tracking', 'interception attempt', 'fraud activity', 'network probing'])}" 
                                  for _ in range(n_threats)],
            'mitigation_strategy': [random.choice(['Block source GT immediately', 'Rate limit signaling from source network', 
                                                  'Alert security operations center', 'Enable enhanced filtering rules',
                                                  'Coordinate with roaming partner', 'Implement geo-fencing restrictions']) 
                                   for _ in range(n_threats)],
            'cve_references': [f"CVE-{random.randint(2018, 2024)}-{random.randint(1000, 9999)}" if random.random() > 0.7 else '' 
                              for _ in range(n_threats)]
        })
        
        # Timeseries data
        n_s1ap = 25000
        timestamps_s1ap = pd.date_range(end=now, periods=n_s1ap, freq='15s')
        
        mme_hosts = datasets['mme_host_reference']['mme_host'].tolist()
        cell_ids = datasets['cell_tower_reference']['cell_id'].tolist()
        cause_codes = datasets['cause_code_reference']['cause_code'].tolist()
        
        imsis = [f"310260{random.randint(100000000, 999999999)}" for _ in range(600)]
        procedures = ['Initial Attach', 'Service Request', 'Handover', 'TAU', 'Detach', 'PDN Connectivity']
        results = ['Success', 'Failure', 'Partial Success']
        attach_results = ['Success', 'Failure', 'Rejected', 'Timeout']
        emm_states = ['EMM-REGISTERED', 'EMM-DEREGISTERED', 'EMM-REGISTERED-INITIATED', 'EMM-TRACKING-AREA-UPDATING-INITIATED']
        apns = ['internet', 'ims', 'mms', 'vzwinternet', 'vzwims']
        
        datasets['lte_s1ap_events'] = pd.DataFrame({
            '@timestamp': timestamps_s1ap,
            'event_id': [f"EVT_{i:010d}" for i in range(1, n_s1ap + 1)],
            'imsi': self.safe_choice(imsis, n_s1ap),
            'cell_id': self.safe_choice(cell_ids, n_s1ap),
            'mme_host': self.safe_choice(mme_hosts, n_s1ap),
            'procedure_type': self.safe_choice(procedures, n_s1ap, weights=[0.15, 0.35, 0.20, 0.15, 0.05, 0.10]),
            'procedure_result': self.safe_choice(results, n_s1ap, weights=[0.88, 0.10, 0.02]),
            'attach_result': self.safe_choice(attach_results, n_s1ap, weights=[0.85, 0.08, 0.05, 0.02]),
            'service_request_result': self.safe_choice(results, n_s1ap, weights=[0.90, 0.08, 0.02]),
            'handover_result': self.safe_choice(results, n_s1ap, weights=[0.92, 0.06, 0.02]),
            'tau_result': self.safe_choice(results, n_s1ap, weights=[0.93, 0.05, 0.02]),
            'enb_id': self.safe_choice(enb_ids, n_s1ap),
            'mme_ue_s1ap_id': np.random.randint(1000000, 9999999, n_s1ap),
            'enb_ue_s1ap_id': np.random.randint(100000, 999999, n_s1ap),
            'cause_group': self.safe_choice(cause_groups, n_s1ap),
            'cause_code': self.safe_choice(cause_codes, n_s1ap),
            'ue_emm_state': self.safe_choice(emm_states, n_s1ap, weights=[0.70, 0.15, 0.10, 0.05]),
            'session_duration_ms': np.random.exponential(30000, n_s1ap).astype(int),
            'bearer_id': [f"Bearer_{random.randint(5, 15)}" for _ in range(n_s1ap)],
            'apn': self.safe_choice(apns, n_s1ap, weights=[0.50, 0.25, 0.10, 0.10, 0.05]),
            'serving_network_mcc': self.safe_choice(['310', '311', '312'], n_s1ap, weights=[0.85, 0.10, 0.05]),
            'serving_network_mnc': self.safe_choice(['260', '490', '480'], n_s1ap, weights=[0.80, 0.15, 0.05]),
            'event_details': [f"Procedure {random.choice(procedures)} for IMSI {random.choice(imsis)} at cell {random.choice(cell_ids[:50])} resulted in {random.choice(results)}. {random.choice(['Normal operation', 'Radio conditions degraded', 'High load detected', 'Handover attempt', 'Resource allocation successful', 'Authentication completed'])}" 
                             for _ in range(n_s1ap)]
        })
        
        n_hss = 12000
        timestamps_hss = pd.date_range(end=now, periods=n_hss, freq='30s')
        
        hss_nodes = datasets['hss_node_reference']['hss_node'].tolist()
        auth_results = ['Success', 'Failure', 'Sync Failure', 'Unknown Subscriber']
        auth_types = ['EPS-AKA', 'AKA', 'SIM']
        diameter_codes = ['2001', '5001', '5004', '5012', '5030', '5065', '3002']
        roaming_statuses = ['Home', 'Roaming', 'International Roaming']
        
        datasets['hss_authentication_events'] = pd.DataFrame({
            '@timestamp': timestamps_hss,
            'event_id': [f"HSS_EVT_{i:010d}" for i in range(1, n_hss + 1)],
            'imsi': self.safe_choice(imsis, n_hss),
            'mme_host': self.safe_choice(mme_hosts, n_hss),
            'auth_result': self.safe_choice(auth_results, n_hss, weights=[0.92, 0.04, 0.03, 0.01]),
            'auth_type': self.safe_choice(auth_types, n_hss, weights=[0.80, 0.15, 0.05]),
            'hss_node': self.safe_choice(hss_nodes, n_hss),
            'diameter_result_code': self.safe_choice(diameter_codes, n_hss, weights=[0.92, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01]),
            'sync_failure': np.random.random(n_hss) < 0.02,
            'sqn_failure': np.random.random(n_hss) < 0.015,
            'response_time_ms': np.random.gamma(2, 15, n_hss).astype(int),
            'subscriber_profile_id': [f"PROF_{random.randint(1, 50):03d}" for _ in range(n_hss)],
            'roaming_status': self.safe_choice(roaming_statuses, n_hss, weights=[0.85, 0.12, 0.03]),
            'visited_plmn': [f"{random.choice(['310260', '310490', '234', '262', '440'])}" for _ in range(n_hss)],
            'error_message': [f"{random.choice(['Authentication successful', 'Subscriber profile retrieved', 'SQN out of range - resync required', 'Unknown subscriber in HSS', 'Database query timeout', 'Replication lag detected', 'Invalid authentication vector', 'HSS overload condition'])}" 
                             for _ in range(n_hss)]
        })
        
        n_signaling = 8000
        timestamps_sig = pd.date_range(end=now, periods=n_signaling, freq='90s')
        
        link_types = ['S1-MME', 'S6a', 'S11', 'S10', 'SGs']
        peer_nodes = [f"peer-{i:02d}.tmobile.net" for i in range(1, 21)]
        congestion_levels = ['None', 'Low', 'Medium', 'High', 'Critical']
        link_statuses = ['Up', 'Degraded', 'Down']
        
        datasets['signaling_link_metrics'] = pd.DataFrame({
            '@timestamp': timestamps_sig,
            'metric_id': [f"METRIC_{i:010d}" for i in range(1, n_signaling + 1)],
            'mme_host': self.safe_choice(mme_hosts, n_signaling),
            'link_type': self.safe_choice(link_types, n_signaling, weights=[0.40, 0.25, 0.15, 0.10, 0.10]),
            'peer_node': self.safe_choice(peer_nodes, n_signaling),
            'messages_per_second': np.random.poisson(500, n_signaling),
            'error_rate': np.random.beta(1, 100, n_signaling),
            'congestion_level': self.safe_choice(congestion_levels, n_signaling, weights=[0.70, 0.15, 0.10, 0.04, 0.01]),
            'sctp_associations': np.random.randint(5, 50, n_signaling),
            'sctp_retransmissions': np.random.poisson(2, n_signaling),
            'link_status': self.safe_choice(link_statuses, n_signaling, weights=[0.95, 0.04, 0.01]),
            'cpu_utilization': np.random.beta(5, 3, n_signaling) * 100,
            'memory_utilization': np.random.beta(6, 2, n_signaling) * 100,
            'active_subscribers': np.random.randint(10000, 500000, n_signaling)
        })
        
        n_ss7 = 3000
        timestamps_ss7 = pd.date_range(end=now, periods=n_ss7, freq='5min')
        
        attack_sigs = datasets['threat_signature_reference']['attack_signature'].tolist()
        msg_types = ['MAP_SRI_SM', 'MAP_PSI', 'MAP_ATI', 'MAP_SAI', 'MAP_UL', 'CAP_IDP', 'MAP_ISD']
        threat_levels = ['Low', 'Medium', 'High', 'Critical']
        gt_prefixes = ['1234567', '9876543', '5551234', '4445678', '3332211']
        map_ops = ['sendRoutingInfoForSM', 'provideSubscriberInfo', 'anyTimeInterrogation', 'sendAuthenticationInfo', 'updateLocation', 'insertSubscriberData']
        
        datasets['ss7_security_events'] = pd.DataFrame({
            '@timestamp': timestamps_ss7,
            'event_id': [f"SS7_EVT_{i:010d}" for i in range(1, n_ss7 + 1)],
            'imsi': self.safe_choice(imsis, n_ss7),
            'source_gt': [f"{random.choice(gt_prefixes)}{random.randint(1000000, 9999999)}" for _ in range(n_ss7)],
            'destination_gt': [f"{random.choice(gt_prefixes)}{random.randint(1000000, 9999999)}" for _ in range(n_ss7)],
            'message_type': self.safe_choice(msg_types, n_ss7),
            'attack_signature': self.safe_choice(attack_sigs, n_ss7),
            'threat_level': self.safe_choice(threat_levels, n_ss7, weights=[0.60, 0.25, 0.12, 0.03]),
            'blocked': np.random.random(n_ss7) < 0.35,
            'originating_network': [f"MCC{random.choice(['310', '234', '262', '440', '208'])}_MNC{random.randint(10, 99):02d}" for _ in range(n_ss7)],
            'sccp_called_party': [f"{random.choice(gt_prefixes)}{random.randint(1000000, 9999999)}" for _ in range(n_ss7)],
            'sccp_calling_party': [f"{random.choice(gt_prefixes)}{random.randint(1000000, 9999999)}" for _ in range(n_ss7)],
            'map_operation': self.safe_choice(map_ops, n_ss7),
            'event_description': [f"SS7 {random.choice(msg_types)} message from {random.choice(['unknown network', 'suspicious GT', 'blacklisted source', 'untrusted partner'])} attempting {random.choice(['location tracking', 'subscriber information query', 'SMS interception', 'authentication vector request'])}. {random.choice(['Blocked by firewall', 'Allowed with monitoring', 'Rate limited', 'Flagged for investigation'])}" 
                                 for _ in range(n_ss7)]
        })
        
        return datasets

    def get_relationships(self) -> List[tuple]:
        return [
            ('lte_s1ap_events', 'cell_id', 'cell_tower_reference'),
            ('lte_s1ap_events', 'mme_host', 'mme_host_reference'),
            ('lte_s1ap_events', 'cause_code', 'cause_code_reference'),
            ('hss_authentication_events', 'mme_host', 'mme_host_reference'),
            ('hss_authentication_events', 'hss_node', 'hss_node_reference'),
            ('signaling_link_metrics', 'mme_host', 'mme_host_reference'),
            ('ss7_security_events', 'attack_signature', 'threat_signature_reference')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        return {
            'lte_s1ap_events': 'S1-AP signaling events between eNodeBs and MME including attach, handover, TAU, and service request procedures',
            'hss_authentication_events': 'HSS authentication and subscriber profile events via Diameter S6a interface',
            'signaling_link_metrics': 'Signaling link performance metrics for MME interfaces including SCTP and message rates',
            'ss7_security_events': 'SS7 security events detecting potential attacks and unauthorized signaling',
            'cell_tower_reference': 'Cell tower and eNodeB reference data with location and configuration',
            'mme_host_reference': 'MME host configuration and capacity information',
            'cause_code_reference': 'S1-AP cause code definitions with severity and recommended actions',
            'hss_node_reference': 'HSS node configuration and database information',
            'threat_signature_reference': 'SS7 threat signatures and attack patterns with mitigation strategies'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        return {
            'lte_s1ap_events': ['event_details'],
            'hss_authentication_events': ['error_message'],
            'cause_code_reference': ['cause_description', 'recommended_action'],
            'threat_signature_reference': ['threat_description', 'mitigation_strategy'],
            'ss7_security_events': ['event_description']
        }
