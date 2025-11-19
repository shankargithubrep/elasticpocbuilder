
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
        
        # Reference data pools
        mme_hostnames = [f'mme-{dc}-{i:02d}' for dc in ['east', 'west', 'central'] for i in range(1, 6)]
        mme_pools = ['pool-core-01', 'pool-core-02', 'pool-edge-01', 'pool-edge-02']
        datacenters = ['dc-seattle', 'dc-dallas', 'dc-atlanta', 'dc-chicago']
        mme_versions = ['v5.2.1', 'v5.2.3', 'v5.3.0', 'v5.1.8']
        mme_vendors = ['Ericsson', 'Nokia', 'Cisco']
        
        hss_nodes = [f'hss-{dc}-{i:02d}' for dc in ['east', 'west'] for i in range(1, 4)]
        hss_db_instances = ['hss-db-primary-01', 'hss-db-primary-02', 'hss-db-secondary-01', 'hss-db-secondary-02']
        hss_roles = ['primary', 'secondary', 'standby']
        
        tracking_areas = [f'TAC{i:04d}' for i in range(1001, 1021)]
        enodeb_vendors = ['Ericsson', 'Nokia', 'Samsung', 'Huawei']
        freq_bands = ['Band 2 (1900MHz)', 'Band 4 (AWS)', 'Band 12 (700MHz)', 'Band 66 (AWS-3)', 'Band 71 (600MHz)']
        
        plmn_ids = ['310260', '310310', '302220', '334020', '334050', '722070', '722310']
        roaming_partners = ['AT&T', 'Telcel', 'Rogers', 'Movistar', 'Claro']
        
        # Generate mme_nodes (reference)
        n_mme = 15
        datasets['mme_nodes'] = pd.DataFrame({
            'network.mme.hostname': self.safe_choice(mme_hostnames, n_mme, replace=False),
            'network.mme.pool_id': self.safe_choice(mme_pools, n_mme),
            'network.mme.datacenter': self.safe_choice(datacenters, n_mme),
            'network.mme.software_version': self.safe_choice(mme_versions, n_mme),
            'network.mme.ue_context.max_capacity': np.random.randint(50000, 200000, n_mme),
            'network.mme.vendor': self.safe_choice(mme_vendors, n_mme),
            'cloud.availability_zone': [f'{dc}-{az}' for dc, az in zip(
                self.safe_choice(datacenters, n_mme),
                self.safe_choice(['1a', '1b', '1c'], n_mme)
            )]
        })
        
        # Generate hss_nodes (reference)
        n_hss = 10
        datasets['hss_nodes'] = pd.DataFrame({
            'network.hss.node_id': [f'hss-{dc}-{i:02d}' for dc in ['east', 'west'] for i in range(1, 6)],  # Generate 10 HSS node IDs
            'network.hss.database_instance': self.safe_choice(hss_db_instances, n_hss),
            'network.hss.datacenter': self.safe_choice(datacenters, n_hss),
            'network.hss.node_role': self.safe_choice(hss_roles, n_hss, weights=[0.4, 0.4, 0.2])
        })
        
        # Generate cell_sites (reference)
        n_cells = 800
        site_ids = [f'SITE{i:05d}' for i in range(1, n_cells + 1)]
        enodeb_ids = [f'eNB{i:06d}' for i in range(100001, 100001 + n_cells)]
        
        datasets['cell_sites'] = pd.DataFrame({
            'network.cell.ecgi': [f'{enbid}01' for enbid in enodeb_ids],
            'network.enodeb.id': enodeb_ids,
            'network.enodeb.site_id': site_ids,
            'network.enodeb.vendor': self.safe_choice(enodeb_vendors, n_cells),
            'network.tracking_area_code': self.safe_choice(tracking_areas, n_cells),
            'network.cell.frequency_band': self.safe_choice(freq_bands, n_cells),
            'geo.location': [f'{lat:.6f},{lon:.6f}' for lat, lon in zip(
                np.random.uniform(25.0, 49.0, n_cells),
                np.random.uniform(-125.0, -66.0, n_cells)
            )]
        })
        
        # Generate network_procedures (timeseries)
        n_proc = 10000
        timestamps = pd.date_range(end=datetime.now(), periods=n_proc, freq='30s')
        
        procedure_types = ['Attach', 'Service Request', 'TAU', 'Detach', 'Handover', 'Bearer Modification']
        outcomes = ['success', 'failure']
        result_codes = ['2001', '2002', '5001', '5003', '5012', '5030', '4010', '4012']
        failure_reasons = ['timeout', 'resource_unavailable', 'authentication_failed', 'hss_unreachable', 
                          'context_not_found', 'signaling_congestion', 'radio_link_failure']
        diameter_commands = ['AIR', 'ULR', 'CLR', 'IDR', 'PUR']
        handoff_causes = ['radio_link_failure', 'target_cell_congestion', 'handover_timeout', 
                         'preparation_failure', 'resource_unavailable']
        gtp_causes = ['0', '64', '65', '66', '67', '72', '73', '81']
        
        selected_mme = datasets['mme_nodes']['network.mme.hostname'].values
        selected_hss = datasets['hss_nodes']['network.hss.node_id'].values
        selected_cells = datasets['cell_sites']['network.cell.ecgi'].values
        selected_tacs = datasets['cell_sites']['network.tracking_area_code'].values
        
        imsi_prefixes = ['310260', '310310']
        imsis = [f'{np.random.choice(imsi_prefixes)}{np.random.randint(1000000000, 9999999999)}' for _ in range(600)]
        
        proc_outcomes = self.safe_choice(outcomes, n_proc, weights=[0.92, 0.08])
        proc_types = self.safe_choice(procedure_types, n_proc)
        
        datasets['network_procedures'] = pd.DataFrame({
            '@timestamp': timestamps,
            'network.procedure.type': proc_types,
            'network.procedure.outcome': proc_outcomes,
            'network.procedure.result_code': [
                self.safe_choice(['2001', '2002'], 1)[0] if out == 'success' 
                else self.safe_choice(result_codes[2:], 1)[0]
                for out in proc_outcomes
            ],
            'network.procedure.failure_reason': [
                '' if out == 'success' else self.safe_choice(failure_reasons, 1)[0]
                for out in proc_outcomes
            ],
            'network.procedure.duration_ms': [
                int(np.random.lognormal(4.5, 0.8)) if out == 'success'
                else int(np.random.lognormal(7.0, 1.2))
                for out in proc_outcomes
            ],
            'network.ue.imsi': self.safe_choice(imsis, n_proc),
            'network.ue.imsi_prefix': [imsi[:6] for imsi in self.safe_choice(imsis, n_proc)],
            'network.cell.ecgi': self.safe_choice(selected_cells, n_proc),
            'network.cell.source_ecgi': [
                self.safe_choice(selected_cells, 1)[0] if ptype == 'Handover' else ''
                for ptype in proc_types
            ],
            'network.cell.target_ecgi': [
                self.safe_choice(selected_cells, 1)[0] if ptype == 'Handover' else ''
                for ptype in proc_types
            ],
            'network.mme.hostname': self.safe_choice(selected_mme, n_proc),
            'network.mme.pool_id': self.safe_choice(mme_pools, n_proc),
            'network.hss.node_id': self.safe_choice(selected_hss, n_proc),
            'network.tracking_area_code': self.safe_choice(selected_tacs, n_proc),
            'network.diameter.result_code': [
                self.safe_choice(['2001', '2002'], 1)[0] if out == 'success'
                else self.safe_choice(['5001', '5003', '5012', '4010'], 1)[0]
                for out in proc_outcomes
            ],
            'network.diameter.command_code': self.safe_choice(diameter_commands, n_proc),
            'network.handoff.outcome': [
                out if ptype == 'Handover' else ''
                for ptype, out in zip(proc_types, proc_outcomes)
            ],
            'network.handoff.failure_cause': [
                self.safe_choice(handoff_causes, 1)[0] if ptype == 'Handover' and out == 'failure' else ''
                for ptype, out in zip(proc_types, proc_outcomes)
            ],
            'network.gtp.cause_code': self.safe_choice(gtp_causes, n_proc),
            'network.roaming_partner.plmn_id': [
                self.safe_choice(plmn_ids[2:], 1)[0] if np.random.random() < 0.15 else ''
                for _ in range(n_proc)
            ]
        })
        
        # Generate mme_metrics (timeseries)
        n_mme_metrics = 8000
        mme_timestamps = pd.date_range(end=datetime.now(), periods=n_mme_metrics, freq='1min')
        
        datasets['mme_metrics'] = pd.DataFrame({
            '@timestamp': mme_timestamps,
            'network.mme.hostname': self.safe_choice(selected_mme, n_mme_metrics),
            'system.cpu.total.pct': np.random.beta(2, 5, n_mme_metrics) * 0.95,
            'system.memory.used.pct': np.random.beta(3, 2, n_mme_metrics) * 0.90,
            'system.memory.used.bytes': np.random.randint(20000000000, 55000000000, n_mme_metrics),
            'network.mme.ue_context.active_count': np.random.randint(15000, 180000, n_mme_metrics),
            'network.mme.s1ap.connected_enodeb_count': np.random.randint(50, 250, n_mme_metrics)
        })
        
        # Generate hss_metrics (timeseries)
        n_hss_metrics = 6000
        hss_timestamps = pd.date_range(end=datetime.now(), periods=n_hss_metrics, freq='1min')
        
        datasets['hss_metrics'] = pd.DataFrame({
            '@timestamp': hss_timestamps,
            'network.hss.node_id': self.safe_choice(selected_hss, n_hss_metrics),
            'database.hss.replication_lag_seconds': np.random.exponential(0.5, n_hss_metrics),
            'network.hss.diameter.tps': np.random.normal(8500, 2000, n_hss_metrics).clip(1000, 25000)
        })
        
        # Generate cell_metrics (timeseries)
        n_cell_metrics = 12000
        cell_timestamps = pd.date_range(end=datetime.now(), periods=n_cell_metrics, freq='5min')
        
        datasets['cell_metrics'] = pd.DataFrame({
            '@timestamp': cell_timestamps,
            'network.cell.ecgi': self.safe_choice(selected_cells, n_cell_metrics),
            'network.cell.rrc_connection_success_rate': np.random.beta(20, 1, n_cell_metrics),
            'network.cell.prb_utilization_pct': np.random.beta(2, 3, n_cell_metrics) * 100,
            'network.cell.active_ue_count': np.random.poisson(45, n_cell_metrics)
        })
        
        # Generate security_events (timeseries)
        n_security = 5000
        security_timestamps = pd.date_range(end=datetime.now(), periods=n_security, freq='5min')
        
        protocols = ['SS7', 'Diameter', 'GTP']
        ss7_attacks = ['location_tracking', 'sms_interception', 'call_interception', 'fraud_bypass']
        diameter_attacks = ['subscriber_enumeration', 'location_disclosure', 'dos_attack', 'fraud_attempt']
        event_outcomes = ['blocked', 'detected', 'allowed']
        countries = ['Unknown', 'Russia', 'China', 'Nigeria', 'Romania', 'India', 'Pakistan']
        
        sec_protocols = self.safe_choice(protocols, n_security, weights=[0.3, 0.5, 0.2])
        
        datasets['security_events'] = pd.DataFrame({
            '@timestamp': security_timestamps,
            'network.protocol': sec_protocols,
            'network.ss7.attack_type': [
                self.safe_choice(ss7_attacks, 1)[0] if proto == 'SS7' else ''
                for proto in sec_protocols
            ],
            'network.ss7.source_gt': [
                f'+{np.random.randint(1, 999)}{np.random.randint(1000000000, 9999999999)}' if proto == 'SS7' else ''
                for proto in sec_protocols
            ],
            'network.diameter.attack_type': [
                self.safe_choice(diameter_attacks, 1)[0] if proto == 'Diameter' else ''
                for proto in sec_protocols
            ],
            'network.diameter.source_host': [
                f'host{np.random.randint(1, 999)}.{self.safe_choice(["attacker", "suspicious", "unknown"], 1)[0]}.com' 
                if proto == 'Diameter' else ''
                for proto in sec_protocols
            ],
            'network.diameter.source_realm': [
                f'{self.safe_choice(["attacker", "malicious", "unknown"], 1)[0]}.realm' if proto == 'Diameter' else ''
                for proto in sec_protocols
            ],
            'network.ue.imsi': [
                self.safe_choice(imsis, 1)[0] if np.random.random() < 0.7 else ''
                for _ in range(n_security)
            ],
            'event.outcome': self.safe_choice(event_outcomes, n_security, weights=[0.7, 0.25, 0.05]),
            'geo.country_name': self.safe_choice(countries, n_security, weights=[0.3, 0.15, 0.15, 0.1, 0.1, 0.1, 0.1])
        })
        
        return datasets

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships from requirements"""
        return [
            ('network_procedures', 'network.mme.hostname', 'mme_nodes'),
            ('network_procedures', 'network.hss.node_id', 'hss_nodes'),
            ('network_procedures', 'network.cell.ecgi', 'cell_sites'),
            ('mme_metrics', 'network.mme.hostname', 'mme_nodes'),
            ('hss_metrics', 'network.hss.node_id', 'hss_nodes'),
            ('cell_metrics', 'network.cell.ecgi', 'cell_sites')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {
            'network_procedures': 'Network signaling procedures (Attach, TAU, Service Request, Handover) with outcomes and diagnostic codes',
            'mme_nodes': 'MME (Mobility Management Entity) node configuration and capacity information',
            'mme_metrics': 'Real-time MME resource utilization metrics (CPU, memory, UE context counts)',
            'hss_nodes': 'HSS (Home Subscriber Server) node configuration and database instance mapping',
            'hss_metrics': 'HSS performance metrics including replication lag and Diameter TPS',
            'cell_sites': 'Cell tower and eNodeB configuration with geographic locations',
            'cell_metrics': 'Radio cell performance metrics (RRC success rate, PRB utilization, active UEs)',
            'security_events': 'SS7 and Diameter security attack detection events'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        """Return fields that should use semantic_text mapping"""
        return {}
