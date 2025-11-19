
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List

class TMobileUSAIncDataGenerator(DataGeneratorModule):
    """Data generator for T-Mobile USA, Inc. - Network Operations Center (NOC) - Core Network Engineering"""

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
        
        # Markets and datacenters
        markets = ['New York', 'Los Angeles', 'Chicago', 'Dallas', 'Atlanta', 'Miami', 'Seattle', 'Boston', 'Phoenix', 'Denver']
        datacenters = ['DC-EAST-1', 'DC-WEST-1', 'DC-CENTRAL-1', 'DC-SOUTH-1']
        vendors = ['Ericsson', 'Nokia', 'Huawei']
        software_versions = ['R18.2.1', 'R18.2.3', 'R18.3.0', 'R19.0.1', 'R19.1.0']
        
        # MME Infrastructure (150 rows)
        n_mme = 150
        cluster_ids = [f'CLUSTER-{i:03d}' for i in range(1, 31)]
        
        mme_hosts = []
        for i in range(n_mme):
            cluster = random.choice(cluster_ids)
            dc = random.choice(datacenters)
            host = f'MME-{dc}-{i+1:03d}'
            mme_hosts.append(host)
        
        datasets['mme_infrastructure'] = pd.DataFrame({
            'mme_host': mme_hosts,
            'cluster_id': [random.choice(cluster_ids) for _ in range(n_mme)],
            'datacenter': [random.choice(datacenters) for _ in range(n_mme)],
            'market_name': [random.choice(markets) for _ in range(n_mme)],
            'software_version': [random.choice(software_versions) for _ in range(n_mme)],
            'max_subscribers': np.random.randint(50000, 150000, n_mme),
            'current_load_pct': np.random.uniform(40, 95, n_mme),
            'cpu_cores': self.safe_choice([32, 48, 64, 96], n_mme),
            'memory_total_gb': self.safe_choice([128, 256, 384, 512], n_mme).astype(float),
            'cluster_role': self.safe_choice(['active', 'standby', 'active', 'active'], n_mme, weights=[60, 20, 10, 10]),
            'last_restart': [now - timedelta(days=int(d)) for d in np.random.uniform(0, 90, n_mme)],
            'maintenance_window': self.safe_choice(['SUN-02:00-06:00', 'SAT-01:00-05:00', 'TUE-03:00-06:00'], n_mme),
            'vendor': [random.choice(vendors) for _ in range(n_mme)],
            'host_description': [
                f'MME host {mme_hosts[i]} serving {random.choice(markets)} market with {random.choice(software_versions)} software, '
                f'configured for high-capacity LTE core network processing with {random.choice(["primary", "backup", "load-balanced"])} role'
                for i in range(n_mme)
            ]
        })
        
        # Subscriber Profiles (5000 rows)
        n_subs = 5000
        imsi_prefix = '310260'
        
        datasets['subscriber_profiles'] = pd.DataFrame({
            'imsi': [f'{imsi_prefix}{random.randint(1000000000, 9999999999)}' for _ in range(n_subs)],
            'subscriber_id': [f'SUB-{i+1:08d}' for i in range(n_subs)],
            'subscriber_tier': self.safe_choice(['Premium', 'Standard', 'Basic', 'Enterprise'], n_subs, weights=[15, 50, 25, 10]),
            'home_market': [random.choice(markets) for _ in range(n_subs)],
            'service_availability_pct': np.random.uniform(95, 100, n_subs),
            'churn_risk_score': np.random.uniform(0, 1, n_subs),
            'incident_count_30d': np.random.poisson(0.5, n_subs),
            'last_incident_date': [now - timedelta(days=int(d)) if d < 30 else None 
                                   for d in np.random.uniform(0, 60, n_subs)],
            'sla_target_pct': self.safe_choice([99.9, 99.5, 99.0, 98.5], n_subs, weights=[15, 50, 25, 10]),
            'lifetime_value': np.random.uniform(500, 15000, n_subs),
            'account_age_days': np.random.randint(30, 3650, n_subs),
            'roaming_enabled': self.safe_choice([True, False], n_subs, weights=[70, 30]),
            'subscriber_profile_text': [
                f'Subscriber on {tier} tier with {int(avail)}% availability, account age {int(age)} days, '
                f'churn risk {risk:.2f}, LTV ${ltv:.0f}, roaming {"enabled" if roam else "disabled"}'
                for tier, avail, age, risk, ltv, roam in zip(
                    datasets['subscriber_profiles']['subscriber_tier'],
                    datasets['subscriber_profiles']['service_availability_pct'],
                    datasets['subscriber_profiles']['account_age_days'],
                    datasets['subscriber_profiles']['churn_risk_score'],
                    datasets['subscriber_profiles']['lifetime_value'],
                    datasets['subscriber_profiles']['roaming_enabled']
                )
            ]
        })
        
        # Roaming Partners (200 rows)
        n_partners = 200
        countries = ['Mexico', 'Canada', 'UK', 'Germany', 'France', 'Italy', 'Spain', 'Japan', 'South Korea', 
                     'Australia', 'Brazil', 'India', 'China', 'Thailand', 'UAE', 'Singapore', 'Netherlands', 'Switzerland']
        
        plmn_ids = [f'{random.randint(200, 999)}{random.randint(10, 99)}' for _ in range(n_partners)]
        
        datasets['roaming_partners'] = pd.DataFrame({
            'plmn_id': plmn_ids,
            'partner_name': [f'{random.choice(["Telco", "Mobile", "Wireless", "Telecom"])} {random.choice(countries)} {random.choice(["Ltd", "Inc", "SA", "GmbH"])}' 
                            for _ in range(n_partners)],
            'country_code': [random.choice(countries) for _ in range(n_partners)],
            'roaming_type': self.safe_choice(['LTE', '5G', '3G', 'LTE+5G'], n_partners, weights=[40, 30, 10, 20]),
            'apn_configuration': [
                f'APN: internet.{plmn}.roam, DNS: {random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}, '
                f'QoS: {random.choice(["QCI-9", "QCI-8", "QCI-7"])}, MTU: {random.choice([1500, 1440, 1400])}'
                for plmn in plmn_ids
            ],
            'baseline_auth_success_rate': np.random.uniform(95, 99.9, n_partners),
            'baseline_daily_volume': np.random.randint(100, 50000, n_partners),
            'security_risk_level': self.safe_choice(['Low', 'Medium', 'High', 'Critical'], n_partners, weights=[50, 30, 15, 5]),
            'agreement_status': self.safe_choice(['Active', 'Pending', 'Suspended'], n_partners, weights=[85, 10, 5]),
            'last_config_change': [now - timedelta(days=int(d)) for d in np.random.uniform(0, 365, n_partners)],
            'partner_description': [
                f'Roaming partner {name} in {country} with {rtype} support, {status} agreement, '
                f'{risk} security risk, baseline {int(vol)} daily authentications at {rate:.2f}% success rate'
                for name, country, rtype, status, risk, vol, rate in zip(
                    datasets['roaming_partners']['partner_name'],
                    datasets['roaming_partners']['country_code'],
                    datasets['roaming_partners']['roaming_type'],
                    datasets['roaming_partners']['agreement_status'],
                    datasets['roaming_partners']['security_risk_level'],
                    datasets['roaming_partners']['baseline_daily_volume'],
                    datasets['roaming_partners']['baseline_auth_success_rate']
                )
            ]
        })
        
        # Cell Site Inventory (8000 rows)
        n_sites = 8000
        site_types = ['Macro', 'Micro', 'Pico', 'Small Cell']
        tracking_areas = [f'TA-{i:04d}' for i in range(1, 201)]
        
        datasets['cell_site_inventory'] = pd.DataFrame({
            'enodeb_id': [f'eNB-{i+1:06d}' for i in range(n_sites)],
            'site_name': [f'{random.choice(markets)}-{random.choice(["North", "South", "East", "West", "Central"])}-{i+1:04d}' 
                         for i in range(n_sites)],
            'tracking_area': [random.choice(tracking_areas) for _ in range(n_sites)],
            'market_name': [random.choice(markets) for _ in range(n_sites)],
            'latitude': np.random.uniform(25, 48, n_sites),
            'longitude': np.random.uniform(-125, -70, n_sites),
            'max_prb_utilization': np.random.uniform(40, 95, n_sites),
            'neighbor_sites': [','.join([f'eNB-{random.randint(1, n_sites):06d}' for _ in range(random.randint(3, 8))]) 
                              for _ in range(n_sites)],
            'coverage_radius_m': [random.choice([500, 1000, 2000, 5000]) if st == 'Macro' else random.choice([100, 200, 300])
                                 for st in self.safe_choice(site_types, n_sites, weights=[60, 20, 10, 10])],
            'site_type': self.safe_choice(site_types, n_sites, weights=[60, 20, 10, 10]),
            'operational_status': self.safe_choice(['Active', 'Degraded', 'Maintenance', 'Offline'], n_sites, weights=[85, 8, 5, 2]),
            'last_alarm': [now - timedelta(hours=int(h)) if h < 720 else None 
                          for h in np.random.exponential(100, n_sites)],
            'site_description': [
                f'{stype} cell site {name} in {market} covering {radius}m radius, tracking area {ta}, '
                f'status {status}, PRB utilization {util:.1f}%, serving approximately {random.randint(50, 1500)} subscribers'
                for stype, name, market, radius, ta, status, util in zip(
                    datasets['cell_site_inventory']['site_type'],
                    datasets['cell_site_inventory']['site_name'],
                    datasets['cell_site_inventory']['market_name'],
                    datasets['cell_site_inventory']['coverage_radius_m'],
                    datasets['cell_site_inventory']['tracking_area'],
                    datasets['cell_site_inventory']['operational_status'],
                    datasets['cell_site_inventory']['max_prb_utilization']
                )
            ]
        })
        
        # MME Signaling Events (10000 rows for MEDIUM size)
        n_events = 10000
        
        interface_types = ['S1-MME', 'S6a', 'S11', 'S10', 'Gn/Gp']
        message_types = ['Attach Request', 'Detach Request', 'TAU Request', 'Service Request', 
                        'Authentication Request', 'Update Location', 'PDN Connectivity', 'Handover Request',
                        'S1 Release', 'Bearer Modification']
        outcomes = ['Success', 'Failure', 'Timeout', 'Rejected']
        error_codes = ['0', 'EMM_CAUSE_15', 'EMM_CAUSE_18', 'ESM_CAUSE_26', 'DIAMETER_TIMEOUT', 
                      'DIAMETER_UNABLE_TO_DELIVER', 'GTP_REQUEST_REJECTED', 'S1AP_OVERLOAD']
        
        # Generate timestamps going backwards from now
        timestamps = pd.date_range(end=now, periods=n_events, freq='30S')
        
        # Sample from existing reference data
        sample_mme_hosts = np.random.choice(mme_hosts, n_events)
        sample_imsi = np.random.choice(datasets['subscriber_profiles']['imsi'].values, n_events)
        sample_plmn = np.random.choice(plmn_ids + ['310260'] * 50, n_events)  # Mostly home network
        sample_enodeb = np.random.choice(datasets['cell_site_inventory']['enodeb_id'].values, n_events)
        sample_ta = np.random.choice(tracking_areas, n_events)
        sample_tiers = np.random.choice(datasets['subscriber_profiles']['subscriber_tier'].values, n_events)
        
        # Create roaming partner names with None for home network
        roaming_partners = []
        for plmn in sample_plmn:
            if plmn == '310260':
                roaming_partners.append(None)
            else:
                partner_rows = datasets['roaming_partners'][datasets['roaming_partners']['plmn_id'] == plmn]
                if len(partner_rows) > 0:
                    roaming_partners.append(partner_rows.iloc[0]['partner_name'])
                else:
                    roaming_partners.append(None)
        
        # Generate cluster_id and datacenter from mme_infrastructure
        cluster_dc = []
        for host in sample_mme_hosts:
            mme_row = datasets['mme_infrastructure'][datasets['mme_infrastructure']['mme_host'] == host]
            if len(mme_row) > 0:
                cluster_dc.append((mme_row.iloc[0]['cluster_id'], mme_row.iloc[0]['datacenter']))
            else:
                cluster_dc.append((random.choice(cluster_ids), random.choice(datacenters)))
        
        # Inject anomalies for split-brain, signaling storms, resource exhaustion
        signaling_storm_scores = np.random.uniform(0, 0.3, n_events)
        # 2% of events are storm-related
        storm_indices = np.random.choice(n_events, int(n_events * 0.02), replace=False)
        signaling_storm_scores[storm_indices] = np.random.uniform(0.7, 1.0, len(storm_indices))
        
        # Memory usage patterns with gradual degradation
        base_memory = np.random.uniform(50e9, 100e9, n_events)
        # 5% show memory leak pattern
        leak_indices = np.random.choice(n_events, int(n_events * 0.05), replace=False)
        base_memory[leak_indices] = np.random.uniform(120e9, 200e9, len(leak_indices))
        
        datasets['mme_signaling_events'] = pd.DataFrame({
            '@timestamp': timestamps,
            'event_id': [f'EVT-{i+1:010d}' for i in range(n_events)],
            'mme_host': sample_mme_hosts,
            'cluster_id': [cd[0] for cd in cluster_dc],
            'datacenter': [cd[1] for cd in cluster_dc],
            'interface_type': self.safe_choice(interface_types, n_events, weights=[40, 25, 15, 10, 10]),
            'message_type': [random.choice(message_types) for _ in range(n_events)],
            'imsi': sample_imsi,
            'plmn_id': sample_plmn,
            'transaction_id': [f'TXN-{random.randint(1000000000, 9999999999)}' for _ in range(n_events)],
            'outcome': self.safe_choice(outcomes, n_events, weights=[85, 8, 4, 3]),
            'duration_ms': np.random.lognormal(3, 1.5, n_events).astype(int),
            'retry_count': np.random.poisson(0.3, n_events),
            'error_code': [random.choice(error_codes) if out != 'Success' else '0' 
                          for out in self.safe_choice(outcomes, n_events, weights=[85, 8, 4, 3])],
            'enodeb_id': sample_enodeb,
            'tracking_area': sample_ta,
            'subscriber_tier': sample_tiers,
            'roaming_partner': roaming_partners,
            'messages_per_second': np.random.uniform(100, 15000, n_events),
            'thread_pool_queue_depth': np.random.poisson(50, n_events),
            'memory_rss_bytes': base_memory.astype(int),
            'signaling_storm_score': signaling_storm_scores,
            'event_description': [
                f'{msg_type} on {iface} from IMSI {imsi[:10]}*** via {enb} resulted in {outcome} '
                f'(duration {dur}ms, retries {retry}), MPS {mps:.0f}, queue depth {qd}, '
                f'storm score {score:.3f}, memory {mem/1e9:.1f}GB'
                for msg_type, iface, imsi, enb, outcome, dur, retry, mps, qd, score, mem in zip(
                    datasets['mme_signaling_events']['message_type'],
                    datasets['mme_signaling_events']['interface_type'],
                    datasets['mme_signaling_events']['imsi'],
                    datasets['mme_signaling_events']['enodeb_id'],
                    datasets['mme_signaling_events']['outcome'],
                    datasets['mme_signaling_events']['duration_ms'],
                    datasets['mme_signaling_events']['retry_count'],
                    datasets['mme_signaling_events']['messages_per_second'],
                    datasets['mme_signaling_events']['thread_pool_queue_depth'],
                    datasets['mme_signaling_events']['signaling_storm_score'],
                    datasets['mme_signaling_events']['memory_rss_bytes']
                )
            ]
        })
        
        return datasets

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships from requirements"""
        return [
            ('mme_signaling_events', 'mme_host', 'mme_infrastructure'),
            ('mme_signaling_events', 'imsi', 'subscriber_profiles'),
            ('mme_signaling_events', 'plmn_id', 'roaming_partners'),
            ('mme_signaling_events', 'enodeb_id', 'cell_site_inventory')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {
            'mme_signaling_events': 'Real-time signaling events from MME hosts including authentication, handovers, and session management with anomaly detection scores',
            'mme_infrastructure': 'MME host configuration and capacity information including cluster topology and resource allocations',
            'subscriber_profiles': 'Subscriber service quality metrics, churn risk scores, and SLA targets for proactive customer retention',
            'roaming_partners': 'International roaming partner configurations with baseline performance metrics and security risk assessments',
            'cell_site_inventory': 'Cell tower infrastructure with coverage areas, neighbor relationships, and operational status'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        """Return fields that should use semantic_text mapping"""
        return {
            'mme_signaling_events': ['event_description'],
            'mme_infrastructure': ['host_description'],
            'subscriber_profiles': ['subscriber_profile_text'],
            'roaming_partners': ['partner_description', 'apn_configuration'],
            'cell_site_inventory': ['site_description']
        }
