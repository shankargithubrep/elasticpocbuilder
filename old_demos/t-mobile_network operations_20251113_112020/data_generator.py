
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

        # Generate mme_hosts (2-5 hosts as per scale requirements)
        n_mme = 5
        datacenters = ['DC-Seattle', 'DC-Dallas', 'DC-Atlanta', 'DC-Chicago', 'DC-Denver']
        regions = ['West', 'Central', 'Southeast', 'Midwest', 'Mountain']
        software_versions = ['MME-5.2.1', 'MME-5.2.3', 'MME-5.3.0', 'MME-5.1.8']
        hardware_models = ['Cisco ASR5500', 'Ericsson SGSN-MME', 'Nokia Flexi NS', 'Huawei ME60']
        
        mme_hosts_data = []
        for i in range(n_mme):
            mme_hosts_data.append({
                'mme_host': f'mme-{i+1:02d}.tmobile.net',
                'datacenter': datacenters[i],
                'region': regions[i],
                'software_version': self.safe_choice(software_versions, weights=[15, 40, 30, 15]),
                'capacity_subscribers': int(np.random.normal(50000, 10000)),
                'deployment_date': datetime.now() - timedelta(days=int(np.random.uniform(180, 1800))),
                'hardware_model': self.safe_choice(hardware_models, weights=[35, 30, 20, 15]),
                'cluster_id': f'cluster-{(i % 2) + 1}'
            })
        datasets['mme_hosts'] = pd.DataFrame(mme_hosts_data)

        # Generate cell_towers (50+ cell IDs, generating 80 for variety)
        n_cells = 80
        technologies = ['LTE', '5G-NR', 'LTE-Advanced']
        frequency_bands = ['Band-2', 'Band-4', 'Band-12', 'Band-66', 'Band-71', 'n41', 'n71']
        sectors = ['A', 'B', 'C']
        tower_types = ['Macro', 'Small Cell', 'Microcell', 'DAS']
        power_sources = ['Grid', 'Grid+Battery', 'Grid+Generator', 'Solar+Battery']
        markets = ['Seattle Metro', 'Dallas-Fort Worth', 'Atlanta Metro', 'Chicago Metro', 'Denver Metro',
                   'Phoenix Metro', 'Miami Metro', 'Boston Metro', 'Los Angeles Metro', 'New York Metro']
        
        cell_towers_data = []
        for i in range(n_cells):
            cell_id = f'CELL-{i+1:04d}'
            market = random.choice(markets)
            lat_base = 30 + (i % 20) * 1.5
            lon_base = -120 + (i % 25) * 2.0
            
            neighbor_count = random.randint(3, 8)
            neighbor_ids = [f'CELL-{j:04d}' for j in random.sample(range(1, n_cells+1), neighbor_count) if j != i+1]
            
            cell_towers_data.append({
                'cell_id': cell_id,
                'site_name': f'{market} Site {i+1}',
                'latitude': lat_base + np.random.uniform(-0.5, 0.5),
                'longitude': lon_base + np.random.uniform(-0.5, 0.5),
                'technology': self.safe_choice(technologies, weights=[40, 35, 25]),
                'frequency_band': random.choice(frequency_bands),
                'sector': random.choice(sectors),
                'tower_type': self.safe_choice(tower_types, weights=[60, 20, 15, 5]),
                'power_source': self.safe_choice(power_sources, weights=[40, 35, 20, 5]),
                'market_name': market,
                'neighbor_cells': ','.join(neighbor_ids[:6])
            })
        datasets['cell_towers'] = pd.DataFrame(cell_towers_data)

        # Generate subscriber_profiles (500+ unique subscribers, generating 800)
        n_subscribers = 800
        subscriber_types = ['Consumer', 'Business', 'Enterprise', 'IoT', 'Government']
        plan_types = ['Unlimited', 'Premium', 'Essential', 'Prepaid', 'Data-Only']
        device_types = ['iPhone', 'Samsung Galaxy', 'Google Pixel', 'OnePlus', 'Motorola', 
                        'IoT Module', 'Tablet', 'Mobile Hotspot']
        plmns = ['310-260', '310-490', '310-800']
        
        subscriber_profiles_data = []
        for i in range(n_subscribers):
            sub_type = self.safe_choice(subscriber_types, weights=[60, 20, 10, 7, 3])
            is_enterprise = sub_type in ['Business', 'Enterprise', 'Government']
            
            subscriber_profiles_data.append({
                'imsi': f'310260{i+1000000000:010d}',
                'subscriber_type': sub_type,
                'plan_type': self.safe_choice(plan_types, weights=[35, 25, 20, 15, 5]),
                'enterprise_account': is_enterprise,
                'roaming_enabled': random.random() < 0.7,
                'home_plmn': self.safe_choice(plmns, weights=[70, 20, 10]),
                'registration_date': datetime.now() - timedelta(days=int(np.random.uniform(30, 1800))),
                'device_type': random.choice(device_types)
            })
        datasets['subscriber_profiles'] = pd.DataFrame(subscriber_profiles_data)

        # Generate mme_failure_events with realistic clustering
        n_failures = 8000
        mme_hosts_list = datasets['mme_hosts']['mme_host'].tolist()
        cell_ids_list = datasets['cell_towers']['cell_id'].tolist()
        imsis_list = datasets['subscriber_profiles']['imsi'].tolist()
        
        procedure_types = ['Attach', 'Detach', 'TAU', 'Service Request', 'Handover', 
                          'Authentication', 'PDN Connectivity', 'Bearer Modification']
        failure_codes = ['EMM-001', 'EMM-002', 'EMM-003', 'ESM-101', 'ESM-102', 
                        'S1AP-201', 'S1AP-202', 'NAS-301', 'NAS-302', 'HSS-401']
        signaling_types = ['Initial UE Message', 'Uplink NAS Transport', 'Downlink NAS Transport',
                          'S1 Setup Request', 'Handover Required', 'Path Switch Request',
                          'Authentication Request', 'Attach Accept', 'TAU Accept']
        
        failure_templates = [
            'Attach rejected due to {reason} on MME {mme}',
            'Authentication failure for subscriber - {reason}',
            'Handover failure from {source} to {target} - {reason}',
            'TAU rejected - {reason}',
            'Service request timeout - {reason}',
            'HSS unreachable during {procedure} - database sync issue',
            'Resource exhaustion on {mme} - {reason}',
            'Signaling storm detected - {reason}',
            'PDN connectivity failure - {reason}',
            'Bearer modification rejected - {reason}'
        ]
        
        failure_reasons = ['network congestion', 'authentication timeout', 'HSS sync failure',
                          'insufficient resources', 'invalid subscriber data', 'roaming restriction',
                          'cell overload', 'signaling timeout', 'database corruption', 
                          'software bug', 'hardware failure', 'security check failed']
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=90)
        
        mme_failure_events_data = []
        
        # Create 12 incident clusters (70% of data)
        incident_count = int(n_failures * 0.7)
        baseline_count = n_failures - incident_count
        n_incidents = 12
        
        for incident_idx in range(n_incidents):
            incident_start = self.random_timedelta(start_time, end_time)
            incident_duration = timedelta(hours=int(np.random.uniform(1, 6)))
            
            # Select affected resources for this incident
            affected_mme = random.choice(mme_hosts_list)
            affected_cells = random.sample(cell_ids_list, k=min(15, len(cell_ids_list)))
            affected_subscribers = random.sample(imsis_list, k=min(80, len(imsis_list)))
            
            # Determine incident type
            incident_types = ['HSS_SYNC', 'MME_EXHAUSTION', 'HANDOVER_CASCADE', 'SIGNALING_STORM', 'AUTH_FAILURE']
            incident_type = random.choice(incident_types)
            
            events_in_incident = incident_count // n_incidents
            
            for _ in range(events_in_incident):
                event_time = self.random_timedelta(incident_start, incident_start + incident_duration)
                
                if incident_type == 'HSS_SYNC':
                    proc_type = self.safe_choice(['Authentication', 'Attach', 'TAU'], weights=[60, 25, 15])
                    fail_code = self.safe_choice(['HSS-401', 'NAS-301', 'EMM-001'], weights=[70, 20, 10])
                    is_auth = True
                elif incident_type == 'MME_EXHAUSTION':
                    proc_type = self.safe_choice(['Service Request', 'Bearer Modification', 'PDN Connectivity'], weights=[50, 30, 20])
                    fail_code = self.safe_choice(['EMM-002', 'ESM-101', 'ESM-102'], weights=[50, 30, 20])
                    is_auth = False
                elif incident_type == 'HANDOVER_CASCADE':
                    proc_type = 'Handover'
                    fail_code = self.safe_choice(['S1AP-201', 'S1AP-202'], weights=[60, 40])
                    is_auth = False
                elif incident_type == 'SIGNALING_STORM':
                    proc_type = self.safe_choice(['TAU', 'Service Request', 'Attach'], weights=[50, 30, 20])
                    fail_code = self.safe_choice(['S1AP-201', 'NAS-302', 'EMM-003'], weights=[50, 30, 20])
                    is_auth = False
                else:  # AUTH_FAILURE
                    proc_type = self.safe_choice(['Authentication', 'Attach'], weights=[80, 20])
                    fail_code = self.safe_choice(['HSS-401', 'NAS-301'], weights=[70, 30])
                    is_auth = True
                
                cell_id = random.choice(affected_cells)
                source_cell = random.choice(affected_cells) if proc_type == 'Handover' else None
                target_cell = random.choice(affected_cells) if proc_type == 'Handover' else None
                
                reason = random.choice(failure_reasons)
                template = random.choice(failure_templates)
                description = template.format(
                    reason=reason,
                    mme=affected_mme,
                    source=source_cell or cell_id,
                    target=target_cell or cell_id,
                    procedure=proc_type
                )
                
                mme_failure_events_data.append({
                    'event_id': f'EVT-{len(mme_failure_events_data)+1:08d}',
                    '@timestamp': event_time,
                    'imsi': random.choice(affected_subscribers),
                    'mme_host': affected_mme,
                    'cell_id': cell_id,
                    'procedure_type': proc_type,
                    'failure_code': fail_code,
                    'serving_plmn': self.safe_choice(['310-260', '310-490', '310-800'], weights=[70, 20, 10]),
                    'tracking_area_code': f'TAC-{random.randint(1000, 9999)}',
                    'failure_description': description,
                    'signaling_message_type': random.choice(signaling_types),
                    'attach_attempt': proc_type == 'Attach',
                    'handover_attempt': proc_type == 'Handover',
                    'authentication_attempt': is_auth,
                    'source_cell_id': source_cell,
                    'target_cell_id': target_cell
                })
        
        # Add baseline failures (30% - random distribution)
        for _ in range(baseline_count):
            event_time = self.random_timedelta(start_time, end_time)
            proc_type = self.safe_choice(procedure_types, weights=[20, 5, 25, 15, 10, 15, 5, 5])
            fail_code = random.choice(failure_codes)
            
            cell_id = random.choice(cell_ids_list)
            is_handover = proc_type == 'Handover'
            is_attach = proc_type == 'Attach'
            is_auth = proc_type == 'Authentication' or random.random() < 0.3
            
            source_cell = random.choice(cell_ids_list) if is_handover else None
            target_cell = random.choice(cell_ids_list) if is_handover else None
            
            reason = random.choice(failure_reasons)
            template = random.choice(failure_templates)
            description = template.format(
                reason=reason,
                mme=random.choice(mme_hosts_list),
                source=source_cell or cell_id,
                target=target_cell or cell_id,
                procedure=proc_type
            )
            
            mme_failure_events_data.append({
                'event_id': f'EVT-{len(mme_failure_events_data)+1:08d}',
                '@timestamp': event_time,
                'imsi': random.choice(imsis_list),
                'mme_host': random.choice(mme_hosts_list),
                'cell_id': cell_id,
                'procedure_type': proc_type,
                'failure_code': fail_code,
                'serving_plmn': self.safe_choice(['310-260', '310-490', '310-800'], weights=[70, 20, 10]),
                'tracking_area_code': f'TAC-{random.randint(1000, 9999)}',
                'failure_description': description,
                'signaling_message_type': random.choice(signaling_types),
                'attach_attempt': is_attach,
                'handover_attempt': is_handover,
                'authentication_attempt': is_auth,
                'source_cell_id': source_cell,
                'target_cell_id': target_cell
            })
        
        datasets['mme_failure_events'] = pd.DataFrame(mme_failure_events_data)

        # Generate hss_sync_events with clustering
        n_hss_events = 3000
        hss_nodes = ['hss-primary-1', 'hss-primary-2', 'hss-secondary-1', 'hss-secondary-2']
        sync_statuses = ['Success', 'Partial Failure', 'Complete Failure', 'Timeout', 'Lag Warning']
        error_codes = ['HSS-SYNC-001', 'HSS-SYNC-002', 'HSS-SYNC-003', 'HSS-REP-101', 
                       'HSS-REP-102', 'HSS-DB-201', 'HSS-DB-202']
        db_partitions = [f'partition-{i:02d}' for i in range(1, 17)]
        
        hss_sync_events_data = []
        
        # Create 8 HSS incident clusters (60% of data)
        incident_count_hss = int(n_hss_events * 0.6)
        baseline_count_hss = n_hss_events - incident_count_hss
        n_hss_incidents = 8
        
        for incident_idx in range(n_hss_incidents):
            incident_start = self.random_timedelta(start_time, end_time)
            incident_duration = timedelta(hours=int(np.random.uniform(2, 8)))
            
            affected_node = random.choice(hss_nodes)
            affected_partitions = random.sample(db_partitions, k=random.randint(2, 6))
            
            events_in_incident = incident_count_hss // n_hss_incidents
            
            for _ in range(events_in_incident):
                event_time = self.random_timedelta(incident_start, incident_start + incident_duration)
                
                status = self.safe_choice(sync_statuses, weights=[10, 30, 40, 15, 5])
                
                if status == 'Success':
                    affected_count = int(np.random.uniform(0, 10))
                    lag = int(np.random.uniform(10, 200))
                elif status == 'Partial Failure':
                    affected_count = int(np.random.uniform(50, 500))
                    lag = int(np.random.uniform(500, 2000))
                elif status == 'Complete Failure':
                    affected_count = int(np.random.uniform(500, 5000))
                    lag = int(np.random.uniform(5000, 30000))
                elif status == 'Timeout':
                    affected_count = int(np.random.uniform(100, 1000))
                    lag = int(np.random.uniform(10000, 60000))
                else:  # Lag Warning
                    affected_count = int(np.random.uniform(0, 50))
                    lag = int(np.random.uniform(2000, 5000))
                
                hss_sync_events_data.append({
                    'event_id': f'HSS-{len(hss_sync_events_data)+1:08d}',
                    '@timestamp': event_time,
                    'hss_node': affected_node,
                    'sync_status': status,
                    'affected_imsi_count': affected_count,
                    'database_partition': random.choice(affected_partitions),
                    'error_code': random.choice(error_codes) if status != 'Success' else 'HSS-SYNC-000',
                    'replication_lag_ms': lag
                })
        
        # Add baseline HSS events (40% - normal operations)
        for _ in range(baseline_count_hss):
            event_time = self.random_timedelta(start_time, end_time)
            status = self.safe_choice(sync_statuses, weights=[85, 8, 2, 3, 2])
            
            if status == 'Success':
                affected_count = int(np.random.uniform(0, 5))
                lag = int(np.random.uniform(10, 150))
            else:
                affected_count = int(np.random.uniform(10, 100))
                lag = int(np.random.uniform(200, 2000))
            
            hss_sync_events_data.append({
                'event_id': f'HSS-{len(hss_sync_events_data)+1:08d}',
                '@timestamp': event_time,
                'hss_node': random.choice(hss_nodes),
                'sync_status': status,
                'affected_imsi_count': affected_count,
                'database_partition': random.choice(db_partitions),
                'error_code': random.choice(error_codes) if status != 'Success' else 'HSS-SYNC-000',
                'replication_lag_ms': lag
            })
        
        datasets['hss_sync_events'] = pd.DataFrame(hss_sync_events_data)

        return datasets

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships from requirements"""
        return [
            ('mme_failure_events', 'mme_host', 'mme_hosts'),
            ('mme_failure_events', 'cell_id', 'cell_towers'),
            ('mme_failure_events', 'imsi', 'subscriber_profiles')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {
            'mme_failure_events': 'MME failure events including attach, handover, and authentication failures with clustering patterns',
            'mme_hosts': 'MME host infrastructure details including capacity, software versions, and datacenter locations',
            'cell_towers': 'Cell tower infrastructure with technology types, locations, and neighbor relationships',
            'subscriber_profiles': 'Subscriber profile information including plan types, device types, and enterprise accounts',
            'hss_sync_events': 'HSS database synchronization events tracking replication lag and affected subscribers'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        """Return fields that should use semantic_text mapping"""
        return {
            'mme_failure_events': ['failure_description'],
            'cell_towers': ['site_name']
        }
