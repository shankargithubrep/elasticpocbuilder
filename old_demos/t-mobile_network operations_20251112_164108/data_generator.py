
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
        
        # Reference data first for relationships
        mme_hosts = [f'MME-{i:02d}' for i in range(1, 6)]
        datacenters = ['DC-EAST', 'DC-WEST', 'DC-CENTRAL']
        software_versions = ['v5.2.1', 'v5.2.3', 'v5.3.0', 'v5.3.1', 'v6.0.0']
        hardware_models = ['Cisco ASR5500', 'Ericsson SGSN-MME', 'Nokia FlexiNG', 'Huawei ME60']
        
        mme_data = []
        for host in mme_hosts:
            mme_data.append({
                'mme_host': host,
                'datacenter': random.choice(datacenters),
                'software_version': random.choice(software_versions),
                'hardware_model': random.choice(hardware_models),
                'memory_gb': random.choice([128, 256, 512, 1024]),
                'cpu_cores': random.choice([32, 64, 96, 128]),
                'max_capacity': random.choice([50000, 100000, 150000, 200000]),
                'deployment_date': datetime.now() - timedelta(days=random.randint(365, 1825)),
                'host_description': random.choice([
                    'Primary MME handling downtown metropolitan area with high subscriber density',
                    'Secondary MME for suburban coverage with load balancing capabilities',
                    'MME dedicated to enterprise customers and IoT device management',
                    'Backup MME for disaster recovery and peak traffic overflow',
                    'Regional MME serving rural areas with extended coverage zones'
                ])
            })
        datasets['mme_host_inventory'] = pd.DataFrame(mme_data)
        
        regions = ['Northeast', 'Southeast', 'Midwest', 'Southwest', 'West', 'Northwest']
        equipment_types = ['Ericsson RBS', 'Nokia AirScale', 'Samsung 5G RAN', 'Huawei BTS3900']
        maintenance_statuses = ['Active', 'Maintenance', 'Degraded', 'Optimal']
        
        cell_data = []
        cell_ids = [f'CELL-{i:04d}' for i in range(1, 101)]
        
        for cell_id in cell_ids:
            lat = round(random.uniform(25.0, 49.0), 6)
            lon = round(random.uniform(-125.0, -66.0), 6)
            neighbors = random.sample([c for c in cell_ids if c != cell_id], k=random.randint(3, 8))
            
            cell_data.append({
                'cell_id': cell_id,
                'cell_name': f'Tower {cell_id}',
                'tower_location': f"{lat},{lon}",
                'region': random.choice(regions),
                'equipment_type': random.choice(equipment_types),
                'capacity': random.choice([500, 1000, 2000, 3000, 5000]),
                'installation_date': datetime.now() - timedelta(days=random.randint(180, 3650)),
                'maintenance_status': random.choice(maintenance_statuses),
                'neighbor_cells': ','.join(neighbors[:5]),
                'tower_description': random.choice([
                    'Urban macro cell tower serving high-density commercial district',
                    'Suburban cell site with residential coverage and highway access',
                    'Rural tower providing extended range coverage for interstate corridor',
                    'Small cell deployment in shopping mall with indoor DAS integration',
                    'Coastal tower with marine coverage and tourist area support',
                    'Enterprise campus cell site with dedicated capacity allocation'
                ])
            })
        datasets['cell_tower_reference'] = pd.DataFrame(cell_data)
        
        n_failures = 2500
        end_time = datetime.now()
        start_time = end_time - timedelta(days=90)
        timestamps = [self.random_timedelta(start_time, end_time) for _ in range(n_failures)]
        timestamps.sort()
        
        procedure_types = ['ATTACH', 'TAU', 'HANDOVER', 'DETACH', 'SERVICE_REQUEST', 'PDN_CONNECTIVITY']
        error_codes = ['EMM_CAUSE_15', 'EMM_CAUSE_17', 'EMM_CAUSE_18', 'EMM_CAUSE_19', 'EMM_CAUSE_20',
                       'ESM_CAUSE_26', 'ESM_CAUSE_27', 'ESM_CAUSE_33', 'S1AP_TIMEOUT', 'HSS_UNREACHABLE']
        attach_types = ['INITIAL', 'EPS', 'COMBINED', 'EMERGENCY']
        country_codes = ['310', '311', '312', '313', '314', '315', '316', '001', '234', '262', '460', '505']
        
        failure_reasons = [
            'HSS authentication vector mismatch detected during subscriber validation',
            'MME memory exhaustion causing transaction timeout and session failure',
            'S1-AP connection timeout to eNodeB during handover preparation phase',
            'Tracking area update rejected due to invalid GUTI mapping',
            'Roaming partner SS7 signaling storm overwhelming MME processor',
            'Cell tower handoff failure cascade affecting neighboring cell cluster',
            'Split-brain condition detected between redundant MME pair instances',
            'Subscriber authentication failure from HSS database synchronization lag',
            'PDN connectivity rejected due to APN configuration mismatch',
            'Service request denied from resource exhaustion on MME host'
        ]
        
        imsi_base = ['310260', '310160', '311480', '312530']
        
        failure_data = []
        for i in range(n_failures):
            imsi_prefix = random.choice(imsi_base)
            imsi_suffix = f'{random.randint(100000000, 999999999)}'
            imsi = imsi_prefix + imsi_suffix
            
            current_cell = random.choice(cell_ids)
            target_cell = random.choice([c for c in cell_ids if c != current_cell])
            
            is_roaming = random.random() < 0.15
            country = random.choice([c for c in country_codes if not c.startswith('31')]) if is_roaming else random.choice(['310', '311', '312'])
            
            failure_data.append({
                'failure_id': f'FAIL-{i+1:08d}',
                '@timestamp': timestamps[i],
                'mme_host': random.choice(mme_hosts),
                'imsi': imsi,
                'current_cell_id': current_cell,
                'target_cell_id': target_cell,
                'procedure_type': random.choice(procedure_types),
                'error_code': random.choice(error_codes),
                'failure_reason': random.choice(failure_reasons),
                'attach_type': random.choice(attach_types),
                'tracking_area_code': f'TAC-{random.randint(1000, 9999)}',
                'roaming_flag': is_roaming,
                'country_code': country
            })
        datasets['mme_signaling_failures'] = pd.DataFrame(failure_data)
        
        n_auth = 3000
        auth_timestamps = [self.random_timedelta(start_time, end_time) for _ in range(n_auth)]
        auth_timestamps.sort()
        
        auth_results = ['SUCCESS', 'FAILURE', 'TIMEOUT', 'REJECTED']
        hss_codes = ['SUCCESS', 'AUTH_VECTOR_MISMATCH', 'SUBSCRIBER_UNKNOWN', 'HSS_TIMEOUT', 
                     'DATABASE_ERROR', 'SYNC_FAILURE', 'ROAMING_NOT_ALLOWED']
        auth_types = ['EPS_AKA', 'EAP_AKA', 'UMTS_AKA', '5G_AKA']
        roaming_partners = ['None', 'Vodafone', 'Orange', 'China Mobile', 'AT&T', 'Verizon', 'Telstra']
        
        auth_data = []
        for i in range(n_auth):
            imsi_prefix = random.choice(imsi_base)
            imsi_suffix = f'{random.randint(100000000, 999999999)}'
            imsi = imsi_prefix + imsi_suffix
            
            result = self.safe_choice(auth_results, weights=[70, 15, 10, 5])
            hss_code = 'SUCCESS' if result == 'SUCCESS' else random.choice(hss_codes[1:])
            
            auth_data.append({
                'event_id': f'AUTH-{i+1:08d}',
                '@timestamp': auth_timestamps[i],
                'imsi': imsi,
                'auth_result': result,
                'hss_response_code': hss_code,
                'mme_host': random.choice(mme_hosts),
                'cell_id': random.choice(cell_ids),
                'authentication_type': random.choice(auth_types),
                'roaming_partner': random.choice(roaming_partners),
                'response_time_ms': int(np.random.exponential(150) + 50) if result == 'SUCCESS' else int(np.random.exponential(800) + 200),
                'retry_count': 0 if result == 'SUCCESS' else random.randint(1, 5)
            })
        datasets['subscriber_authentication_events'] = pd.DataFrame(auth_data)
        
        return datasets

    def get_relationships(self) -> List[tuple]:
        return [
            ('mme_signaling_failures', 'mme_host', 'mme_host_inventory'),
            ('mme_signaling_failures', 'current_cell_id', 'cell_tower_reference'),
            ('subscriber_authentication_events', 'mme_host', 'mme_host_inventory'),
            ('subscriber_authentication_events', 'cell_id', 'cell_tower_reference')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        return {
            'mme_signaling_failures': 'MME signaling failures tracking attach, handover, and authentication issues across the 4G/5G core network',
            'cell_tower_reference': 'Cell tower infrastructure inventory with location, capacity, and neighbor relationships',
            'mme_host_inventory': 'MME host configuration and capacity information for core network elements',
            'subscriber_authentication_events': 'Subscriber authentication events tracking HSS interactions and security validation'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        return {
            'mme_signaling_failures': ['failure_reason'],
            'cell_tower_reference': ['tower_description'],
            'mme_host_inventory': ['host_description']
        }
