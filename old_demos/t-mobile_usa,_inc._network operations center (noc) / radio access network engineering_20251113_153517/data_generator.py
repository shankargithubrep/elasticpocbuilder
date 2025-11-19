
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List

class TMobileUSAIncDataGenerator(DataGeneratorModule):
    """Data generator for T-Mobile USA, Inc. - Network Operations Center (NOC) / Radio Access Network Engineering"""

    @staticmethod
    def safe_choice(choices, size=None, weights=None, replace=True):
        """Safer alternative to np.random.choice with automatic probability normalization.

        WARNING: Do NOT use this for lists of lists with varying lengths!
        For example, if you have networks = [['HMO', 'PPO'], ['PPO', 'EPO'], ['HMO']],
        use Python's random.choice() instead:
            import random
            'networks': [','.join(random.choice(networks)) for _ in range(n)]
        """
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

        # Reference data
        regions = ['us-east', 'us-west', 'us-central', 'us-south']
        datacenters = ['DC-ATL-01', 'DC-NYC-02', 'DC-LAX-01', 'DC-CHI-01', 'DC-DFW-01', 'DC-SEA-01']
        clusters = ['CLU-EAST-A', 'CLU-EAST-B', 'CLU-WEST-A', 'CLU-WEST-B', 'CLU-CENTRAL-A', 'CLU-SOUTH-A']
        
        # Generate mme_hosts (reference)
        n_hosts = 50
        mme_hosts_data = {
            'mme_host': [f'mme-{region}-{i:02d}.tmobile.net' for region in regions for i in range(1, 14)],
            'cluster_id': [self.safe_choice(clusters) for _ in range(n_hosts)],
            'datacenter': [self.safe_choice(datacenters) for _ in range(n_hosts)],
            'region': [self.safe_choice(regions) for _ in range(n_hosts)],
            'cpu_utilization_pct': np.random.uniform(20, 95, n_hosts),
            'memory_utilization_pct': np.random.uniform(40, 98, n_hosts),
            'heap_used_mb': np.random.uniform(2048, 12288, n_hosts),
            'heap_max_mb': np.repeat([16384, 32768, 65536], [20, 20, 10]),
            'thread_pool_active': np.random.randint(50, 500, n_hosts),
            'thread_pool_max': np.repeat([512, 1024, 2048], [20, 20, 10]),
            'sctp_association_count': np.random.randint(50, 500, n_hosts),
            'software_version': self.safe_choice(['MME-v4.2.1', 'MME-v4.3.0', 'MME-v4.3.2', 'MME-v5.0.1'], n_hosts, weights=[10, 30, 40, 20]),
            'operational_status': self.safe_choice(['active', 'standby', 'degraded'], n_hosts, weights=[70, 20, 10])
        }
        mme_hosts_data['last_restart_time'] = [
            self.random_timedelta(datetime.now() - timedelta(days=90), datetime.now()) 
            for _ in range(n_hosts)
        ]
        mme_hosts_data['host_description'] = [
            f"MME host {host} in {dc} serving {region} region with {int(assoc)} SCTP associations running software version {ver}"
            for host, dc, region, assoc, ver in zip(
                mme_hosts_data['mme_host'], 
                mme_hosts_data['datacenter'], 
                mme_hosts_data['region'],
                mme_hosts_data['sctp_association_count'],
                mme_hosts_data['software_version']
            )
        ]
        datasets['mme_hosts'] = pd.DataFrame(mme_hosts_data)

        # Generate cell_sites (reference)
        n_cells = 500
        technologies = ['LTE', '5G-NR', '5G-NSA']
        freq_bands = ['Band-2-1900MHz', 'Band-4-AWS', 'Band-12-700MHz', 'Band-66-AWS-3', 'Band-71-600MHz', 'n41-2.5GHz', 'n71-600MHz']
        
        cell_sites_data = {
            'cell_id': [f'CELL-{i:06d}' for i in range(1, n_cells + 1)],
            'enodeb_id': [f'eNB-{i:04d}' for i in np.random.randint(1, 150, n_cells)],
            'cell_name': [f'{city}-{sector}-{tech}' for city, sector, tech in zip(
                self.safe_choice(['NYC', 'LAX', 'CHI', 'ATL', 'DFW', 'SEA', 'BOS', 'MIA'], n_cells),
                self.safe_choice(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'], n_cells),
                self.safe_choice(technologies, n_cells)
            )],
            'cluster_id': [self.safe_choice(clusters) for _ in range(n_cells)],
            'datacenter': [self.safe_choice(datacenters) for _ in range(n_cells)],
            'region': [self.safe_choice(regions) for _ in range(n_cells)],
            'technology': self.safe_choice(technologies, n_cells, weights=[40, 35, 25]),
            'frequency_band': [self.safe_choice(freq_bands) for _ in range(n_cells)],
            'prb_utilization_dl_pct': np.random.uniform(15, 95, n_cells),
            'prb_utilization_ul_pct': np.random.uniform(10, 85, n_cells),
            'operational_status': self.safe_choice(['active', 'degraded', 'maintenance'], n_cells, weights=[85, 10, 5]),
            'latitude': np.random.uniform(25.0, 48.0, n_cells),
            'longitude': np.random.uniform(-125.0, -70.0, n_cells)
        }
        all_cell_ids = cell_sites_data['cell_id']
        cell_sites_data['neighbor_cell_ids'] = [
            ','.join(random.sample([c for c in all_cell_ids if c != cell], min(6, len(all_cell_ids)-1)))
            for cell in all_cell_ids
        ]
        cell_sites_data['cell_description'] = [
            f"{tech} cell site {name} on {band} with {dl:.1f}% DL and {ul:.1f}% UL PRB utilization in {region}"
            for tech, name, band, dl, ul, region in zip(
                cell_sites_data['technology'],
                cell_sites_data['cell_name'],
                cell_sites_data['frequency_band'],
                cell_sites_data['prb_utilization_dl_pct'],
                cell_sites_data['prb_utilization_ul_pct'],
                cell_sites_data['region']
            )
        ]
        datasets['cell_sites'] = pd.DataFrame(cell_sites_data)

        # Generate subscriber_profiles (reference)
        n_subs = 1000
        device_types = ['iPhone-14', 'iPhone-15', 'Samsung-S23', 'Samsung-S24', 'Google-Pixel-8', 'OnePlus-11', 'Motorola-Edge']
        
        subscriber_profiles_data = {
            'imsi': [f'310260{random.randint(1000000000, 9999999999)}' for _ in range(n_subs)],
            'subscriber_tier': self.safe_choice(['premium', 'standard', 'basic'], n_subs, weights=[20, 60, 20]),
            'roaming_status': self.safe_choice(['home', 'domestic-roaming', 'international-roaming'], n_subs, weights=[85, 10, 5]),
            'home_network': self.safe_choice(['T-Mobile', 'Sprint-Legacy', 'Metro-MVNO'], n_subs, weights=[70, 20, 10]),
            'device_type': [self.safe_choice(device_types) for _ in range(n_subs)],
            'fraud_risk_score': np.random.uniform(0, 100, n_subs),
            'lifetime_value_usd': np.random.uniform(500, 15000, n_subs),
            'account_status': self.safe_choice(['active', 'suspended', 'grace-period'], n_subs, weights=[90, 5, 5]),
            'last_known_location': [self.safe_choice(['NYC', 'LAX', 'CHI', 'ATL', 'DFW', 'SEA', 'BOS', 'MIA']) for _ in range(n_subs)]
        }
        subscriber_profiles_data['subscriber_behavior_profile'] = [
            f"{tier} tier subscriber with {device} device, {status} roaming status, fraud risk score {score:.1f}, lifetime value ${ltv:.0f}"
            for tier, device, status, score, ltv in zip(
                subscriber_profiles_data['subscriber_tier'],
                subscriber_profiles_data['device_type'],
                subscriber_profiles_data['roaming_status'],
                subscriber_profiles_data['fraud_risk_score'],
                subscriber_profiles_data['lifetime_value_usd']
            )
        ]
        datasets['subscriber_profiles'] = pd.DataFrame(subscriber_profiles_data)

        # Generate mme_signaling_events (timeseries)
        n_events = 10000
        mme_host_list = mme_hosts_data['mme_host']
        cell_id_list = cell_sites_data['cell_id']
        enodeb_id_list = list(set(cell_sites_data['enodeb_id']))
        imsi_list = subscriber_profiles_data['imsi']
        
        event_types = ['attach', 'detach', 'tau', 'handoff', 'service-request', 'pdn-connection', 'authentication']
        nas_msg_types = ['ATTACH_REQUEST', 'ATTACH_ACCEPT', 'TAU_REQUEST', 'TAU_ACCEPT', 'SERVICE_REQUEST', 
                         'DETACH_REQUEST', 'PDN_CONNECTIVITY_REQUEST', 'AUTHENTICATION_REQUEST']
        handoff_types = ['X2', 'S1', 'inter-MME', 'intra-MME', 'N/A']
        
        mme_signaling_data = {
            'event_id': [f'EVT-{i:010d}' for i in range(1, n_events + 1)],
            '@timestamp': pd.date_range(end=datetime.now(), periods=n_events, freq='30s'),
            'mme_host': [self.safe_choice(mme_host_list) for _ in range(n_events)],
            'cluster_id': [self.safe_choice(clusters) for _ in range(n_events)],
            'datacenter': [self.safe_choice(datacenters) for _ in range(n_events)],
            'event_type': self.safe_choice(event_types, n_events, weights=[25, 5, 20, 30, 10, 5, 5]),
            'imsi': [self.safe_choice(imsi_list) for _ in range(n_events)],
            'imei': [f'{random.randint(100000000000000, 999999999999999)}' for _ in range(n_events)],
            'nas_message_type': [self.safe_choice(nas_msg_types) for _ in range(n_events)],
            'nas_processing_latency_ms': np.random.uniform(5, 500, n_events),
            'authentication_result': self.safe_choice(['success', 'failure', 'timeout', 'N/A'], n_events, weights=[85, 8, 2, 5]),
            'handoff_type': [self.safe_choice(handoff_types) for _ in range(n_events)],
            'handoff_result': self.safe_choice(['success', 'failure', 'N/A'], n_events, weights=[75, 10, 15]),
            'handoff_failure_cause': self.safe_choice(['timeout', 'resource-unavailable', 'signaling-error', 'radio-link-failure', 'N/A'], 
                                                      n_events, weights=[5, 3, 2, 5, 85]),
            'source_enodeb_id': [self.safe_choice(enodeb_id_list) for _ in range(n_events)],
            'target_enodeb_id': [self.safe_choice(enodeb_id_list) for _ in range(n_events)],
            'source_cell_id': [self.safe_choice(cell_id_list) for _ in range(n_events)],
            'target_cell_id': [self.safe_choice(cell_id_list) for _ in range(n_events)],
            'attach_result': self.safe_choice(['success', 'failure', 'N/A'], n_events, weights=[80, 5, 15]),
            'tau_result': self.safe_choice(['success', 'failure', 'N/A'], n_events, weights=[85, 3, 12]),
            'pdn_connection_time_ms': np.random.uniform(50, 2000, n_events),
            'gtp_tunnel_result': self.safe_choice(['established', 'failed', 'N/A'], n_events, weights=[85, 5, 10]),
            'diameter_transaction_result': self.safe_choice(['success', 'timeout', 'error', 'N/A'], n_events, weights=[85, 5, 3, 7]),
            's6a_interface_result': self.safe_choice(['success', 'failure', 'N/A'], n_events, weights=[90, 3, 7]),
            'sctp_association_id': [f'SCTP-{random.randint(10000, 99999)}' for _ in range(n_events)],
            'sctp_state': self.safe_choice(['ESTABLISHED', 'SHUTDOWN_PENDING', 'CLOSED'], n_events, weights=[92, 5, 3]),
            'revenue_impacting': self.safe_choice([True, False], n_events, weights=[12, 88])
        }
        mme_signaling_data['event_description'] = [
            f"{evt_type} event on {mme} from cell {src_cell} to {tgt_cell} with {ho_result} handoff result, NAS latency {lat:.1f}ms, authentication {auth}"
            for evt_type, mme, src_cell, tgt_cell, ho_result, lat, auth in zip(
                mme_signaling_data['event_type'],
                mme_signaling_data['mme_host'],
                mme_signaling_data['source_cell_id'],
                mme_signaling_data['target_cell_id'],
                mme_signaling_data['handoff_result'],
                mme_signaling_data['nas_processing_latency_ms'],
                mme_signaling_data['authentication_result']
            )
        ]
        datasets['mme_signaling_events'] = pd.DataFrame(mme_signaling_data)

        # Generate ss7_diameter_events (timeseries)
        n_ss7 = 8000
        protocols = ['SS7-MAP', 'Diameter-S6a', 'Diameter-S6d', 'Diameter-Gx', 'SS7-CAMEL']
        msg_types = ['UPDATE_LOCATION', 'INSERT_SUBSCRIBER_DATA', 'SEND_ROUTING_INFO', 'PROVIDE_SUBSCRIBER_INFO', 
                     'AUTHENTICATION_INFO_REQUEST', 'CANCEL_LOCATION', 'PURGE_UE']
        networks = ['T-Mobile-US', 'Vodafone-UK', 'Orange-FR', 'Telefonica-ES', 'Rogers-CA', 'Telstra-AU', 'Unknown-Network']
        attack_categories = ['location-tracking', 'sms-interception', 'fraud-roaming', 'dos-attack', 'none']
        
        ss7_diameter_data = {
            'event_id': [f'SS7-{i:010d}' for i in range(1, n_ss7 + 1)],
            '@timestamp': pd.date_range(end=datetime.now(), periods=n_ss7, freq='45s'),
            'protocol': [self.safe_choice(protocols) for _ in range(n_ss7)],
            'message_type': [self.safe_choice(msg_types) for _ in range(n_ss7)],
            'source_network': [self.safe_choice(networks) for _ in range(n_ss7)],
            'destination_network': [self.safe_choice(networks) for _ in range(n_ss7)],
            'imsi': [self.safe_choice(imsi_list) for _ in range(n_ss7)],
            'msisdn': [f'+1{random.randint(2000000000, 9999999999)}' for _ in range(n_ss7)],
            'originating_address': [f'{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}' 
                                   for _ in range(n_ss7)],
            'transaction_result': self.safe_choice(['success', 'failure', 'timeout', 'rejected'], n_ss7, weights=[80, 8, 7, 5]),
            'anomaly_score': np.random.uniform(0, 100, n_ss7),
            'is_suspicious': self.safe_choice([True, False], n_ss7, weights=[15, 85]),
            'attack_category': self.safe_choice(attack_categories, n_ss7, weights=[3, 2, 4, 3, 88]),
            'cluster_id': [self.safe_choice(clusters) for _ in range(n_ss7)],
            'datacenter': [self.safe_choice(datacenters) for _ in range(n_ss7)]
        }
        ss7_diameter_data['event_pattern_description'] = [
            f"{protocol} {msg_type} from {src_net} to {dst_net} with {result} result, anomaly score {score:.1f}, suspicious flag {susp}, attack category {attack}"
            for protocol, msg_type, src_net, dst_net, result, score, susp, attack in zip(
                ss7_diameter_data['protocol'],
                ss7_diameter_data['message_type'],
                ss7_diameter_data['source_network'],
                ss7_diameter_data['destination_network'],
                ss7_diameter_data['transaction_result'],
                ss7_diameter_data['anomaly_score'],
                ss7_diameter_data['is_suspicious'],
                ss7_diameter_data['attack_category']
            )
        ]
        datasets['ss7_diameter_events'] = pd.DataFrame(ss7_diameter_data)

        return datasets

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships from requirements"""
        return [
            ('mme_signaling_events', 'mme_host', 'mme_hosts'),
            ('mme_signaling_events', 'source_cell_id', 'cell_sites'),
            ('mme_signaling_events', 'target_cell_id', 'cell_sites'),
            ('mme_signaling_events', 'imsi', 'subscriber_profiles'),
            ('ss7_diameter_events', 'imsi', 'subscriber_profiles')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {
            'mme_signaling_events': 'MME signaling events including attach, detach, TAU, handoff, and authentication events across 4G LTE and 5G networks',
            'mme_hosts': 'MME host infrastructure with resource utilization, software versions, and operational status',
            'cell_sites': 'Cell site inventory with technology type, frequency bands, PRB utilization, and neighbor relationships',
            'subscriber_profiles': 'Subscriber profiles with tier, roaming status, device type, fraud risk, and lifetime value',
            'ss7_diameter_events': 'SS7 and Diameter signaling events with anomaly detection for security attack prevention'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        """Return fields that should use semantic_text mapping"""
        return {
            'mme_signaling_events': ['event_description'],
            'mme_hosts': ['host_description'],
            'cell_sites': ['cell_description'],
            'subscriber_profiles': ['subscriber_behavior_profile'],
            'ss7_diameter_events': ['event_pattern_description']
        }
