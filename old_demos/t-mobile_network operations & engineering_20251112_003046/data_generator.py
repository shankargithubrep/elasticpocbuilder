
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
        
        vendors = ['Ericsson', 'Nokia', 'Samsung']
        technologies = ['5G NR', 'LTE', 'LTE-A']
        regions = [f'REGION-{i:02d}' for i in range(1, 16)]
        region_names = ['Northeast', 'Mid-Atlantic', 'Southeast', 'Florida', 'Great Lakes', 
                       'Central', 'South Central', 'Mountain', 'Pacific', 'Northwest',
                       'California North', 'California South', 'Texas North', 'Texas South', 'Metro NYC']
        noc_teams = [f'NOC-{r}' for r in regions]
        sectors = ['A', 'B', 'C']
        freq_bands = ['n71', 'n41', 'n260', 'B2', 'B4', 'B12', 'B66', 'B71']
        
        procedure_types = ['ATTACH', 'DETACH', 'SERVICE_REQUEST', 'TAU', 'HANDOVER', 
                          'RRC_CONNECTION', 'BEARER_SETUP', 'BEARER_MODIFY', 'PAGING_RESPONSE']
        result_codes = ['SUCCESS', 'TIMEOUT', 'REJECT', 'FAILURE', 'RADIO_FAILURE']
        
        plan_types = ['Magenta', 'Magenta MAX', 'Essentials', 'Business Unlimited', 'Prepaid']
        tiers = ['Premium', 'Standard', 'Basic']
        device_models = ['iPhone 15 Pro', 'iPhone 14', 'Samsung S24', 'Samsung S23', 
                        'Google Pixel 8', 'OnePlus 12', 'Motorola Edge']
        device_caps = ['5G mmWave', '5G Sub-6', 'LTE Cat 16', 'LTE Cat 12']
        
        incident_severities = ['Critical', 'High', 'Medium', 'Low']
        incident_types = ['Cell Outage', 'Degraded Performance', 'Capacity Congestion', 
                         'Transport Issue', 'Core Network', 'Handover Failure']
        root_causes = ['Hardware Failure', 'Software Bug', 'Configuration Error', 
                      'Capacity Limit', 'Transport Degradation', 'Power Issue', 'Backhaul Congestion']

        # cell_site_inventory (reference)
        n_cells = 150
        cell_ids = [f'CELL-{i:05d}' for i in range(1, n_cells + 1)]
        
        cell_data = {
            'network.cell.id': cell_ids,
            'network.cell.name': [f'{random.choice(["Downtown", "Uptown", "Suburban", "Highway", "Airport", "Mall", "Campus"])} {random.choice(["North", "South", "East", "West", "Central"])} Site {i}' for i in range(1, n_cells + 1)],
            'network.vendor.name': self.safe_choice(vendors, n_cells, weights=[40, 35, 25]),
            'network.technology': self.safe_choice(technologies, n_cells, weights=[45, 35, 20]),
            'network.region.id': self.safe_choice(regions, n_cells),
            'network.region.name': [region_names[regions.index(self.safe_choice(regions))] for _ in range(n_cells)],
            'network.noc.team': self.safe_choice(noc_teams, n_cells),
            'geo.location': [f'{np.random.uniform(25, 49):.6f},{np.random.uniform(-125, -70):.6f}' for _ in range(n_cells)],
            'network.cell.capacity_subscribers': np.random.randint(500, 3000, n_cells),
            'network.cell.sector': self.safe_choice(sectors, n_cells),
            'network.cell.frequency_band': self.safe_choice(freq_bands, n_cells),
            'network.cell.deployment_date': pd.date_range(end=datetime.now(), periods=n_cells, freq='-30D')
        }
        
        cell_char_templates = [
            '{tech} cell site with {band} frequency band, {sector} sector, {vendor} equipment, capacity {capacity} subscribers',
            '{vendor} {tech} installation on {band}, sector {sector}, supporting up to {capacity} concurrent users',
            'Cell site deployed with {vendor} RAN, {tech} technology, {band} band, {sector} sector coverage'
        ]
        cell_data['cell.characteristics'] = [
            random.choice(cell_char_templates).format(
                tech=cell_data['network.technology'][i],
                band=cell_data['network.cell.frequency_band'][i],
                sector=cell_data['network.cell.sector'][i],
                vendor=cell_data['network.vendor.name'][i],
                capacity=cell_data['network.cell.capacity_subscribers'][i]
            ) for i in range(n_cells)
        ]
        
        datasets['cell_site_inventory'] = pd.DataFrame(cell_data)

        # subscriber_profiles (reference)
        n_subs = 200
        imsis = [f'310260{random.randint(100000000, 999999999)}' for _ in range(n_subs)]
        
        sub_data = {
            'subscriber.imsi': imsis,
            'subscriber.msisdn': [f'+1{random.randint(2000000000, 9999999999)}' for _ in range(n_subs)],
            'subscriber.plan_type': self.safe_choice(plan_types, n_subs),
            'subscriber.tier': self.safe_choice(tiers, n_subs, weights=[20, 50, 30]),
            'subscriber.tenure_months': np.random.randint(1, 120, n_subs),
            'subscriber.home_region': self.safe_choice(regions, n_subs),
            'subscriber.device_model': self.safe_choice(device_models, n_subs),
            'subscriber.device_capability': self.safe_choice(device_caps, n_subs),
            'subscriber.arpu': np.random.uniform(45, 120, n_subs).round(2)
        }
        
        profile_templates = [
            '{tier} tier subscriber on {plan} plan, using {device} with {capability} capability, {tenure} months tenure',
            '{plan} customer, {tier} tier, {device} device, {capability} support, ARPU ${arpu}',
            'Subscriber profile: {tier}, {plan} plan, {device}, {capability}, {tenure}mo customer'
        ]
        sub_data['subscriber.profile_description'] = [
            random.choice(profile_templates).format(
                tier=sub_data['subscriber.tier'][i],
                plan=sub_data['subscriber.plan_type'][i],
                device=sub_data['subscriber.device_model'][i],
                capability=sub_data['subscriber.device_capability'][i],
                tenure=sub_data['subscriber.tenure_months'][i],
                arpu=sub_data['subscriber.arpu'][i]
            ) for i in range(n_subs)
        ]
        
        datasets['subscriber_profiles'] = pd.DataFrame(sub_data)

        # network_procedures_reference (reference)
        proc_data = {
            'network.procedure.type': procedure_types,
            'network.procedure.name': ['Attach Procedure', 'Detach Procedure', 'Service Request', 
                                      'Tracking Area Update', 'Handover Procedure', 
                                      'RRC Connection Setup', 'Bearer Setup', 'Bearer Modification', 
                                      'Paging Response'],
            'network.procedure.category': ['Session', 'Session', 'Session', 'Mobility', 'Mobility',
                                          'Connection', 'Bearer', 'Bearer', 'Connection'],
            'network.procedure.expected_duration_ms': [1200, 800, 600, 900, 450, 350, 500, 400, 250],
            'network.procedure.success_threshold_pct': [98.5, 99.0, 98.0, 97.5, 95.0, 98.0, 97.0, 97.5, 96.0]
        }
        
        proc_templates = [
            '{name} - {category} procedure with expected duration {duration}ms, success threshold {threshold}%',
            '{category} procedure: {name}, target completion {duration}ms, KPI threshold {threshold}%',
            'Network procedure {name} ({category}), expected {duration}ms, success rate target {threshold}%'
        ]
        proc_data['network.procedure.description'] = [
            random.choice(proc_templates).format(
                name=proc_data['network.procedure.name'][i],
                category=proc_data['network.procedure.category'][i],
                duration=proc_data['network.procedure.expected_duration_ms'][i],
                threshold=proc_data['network.procedure.success_threshold_pct'][i]
            ) for i in range(len(procedure_types))
        ]
        
        datasets['network_procedures_reference'] = pd.DataFrame(proc_data)

        # network_signaling_events (timeseries)
        n_events = 3000
        timestamps = pd.date_range(end=datetime.now(), periods=n_events, freq='30S')
        
        event_data = {
            'event_id': [f'EVT-{i:010d}' for i in range(1, n_events + 1)],
            '@timestamp': timestamps,
            'network.cell.id': self.safe_choice(cell_ids, n_events),
            'network.procedure.type': self.safe_choice(procedure_types, n_events),
            'network.procedure.result_code': self.safe_choice(result_codes, n_events, weights=[85, 5, 4, 3, 3]),
            'network.procedure.success': self.safe_choice([True, False], n_events, weights=[90, 10]),
            'network.procedure.duration_ms': np.random.lognormal(6, 0.5, n_events).round(1),
            'subscriber.imsi': self.safe_choice(imsis, n_events),
            'network.radio.rsrp_dbm': np.random.uniform(-120, -70, n_events).round(1),
            'network.radio.rsrq_db': np.random.uniform(-20, -5, n_events).round(1),
            'network.radio.sinr_db': np.random.uniform(-5, 25, n_events).round(1),
            'network.handover.source_cell': [self.safe_choice(cell_ids) if random.random() < 0.3 else None for _ in range(n_events)],
            'network.handover.target_cell': [self.safe_choice(cell_ids) if random.random() < 0.3 else None for _ in range(n_events)],
            'network.handover.success': [random.choice([True, False]) if random.random() < 0.3 else None for _ in range(n_events)],
            'network.rrc.connection_result': self.safe_choice(['ESTABLISHED', 'REJECTED', 'TIMEOUT', 'SUCCESS'], n_events, weights=[70, 10, 5, 15]),
            'network.vendor.name': self.safe_choice(vendors, n_events),
            'network.technology': self.safe_choice(technologies, n_events),
            'network.region.id': self.safe_choice(regions, n_events)
        }
        
        event_desc_templates = [
            '{proc} procedure on cell {cell}, result {result}, duration {duration}ms, RSRP {rsrp}dBm',
            'Signaling event: {proc} {result} at {cell}, {duration}ms, radio quality RSRP={rsrp} SINR={sinr}',
            '{proc} {result} on {tech} cell {cell}, took {duration}ms, signal strength {rsrp}dBm'
        ]
        event_data['event.description'] = [
            random.choice(event_desc_templates).format(
                proc=event_data['network.procedure.type'][i],
                cell=event_data['network.cell.id'][i],
                result=event_data['network.procedure.result_code'][i],
                duration=event_data['network.procedure.duration_ms'][i],
                rsrp=event_data['network.radio.rsrp_dbm'][i],
                sinr=event_data['network.radio.sinr_db'][i],
                tech=event_data['network.technology'][i]
            ) for i in range(n_events)
        ]
        
        datasets['network_signaling_events'] = pd.DataFrame(event_data)

        # cell_performance_metrics (timeseries)
        n_metrics = 2000
        metric_timestamps = pd.date_range(end=datetime.now(), periods=n_metrics, freq='5min')
        
        metric_data = {
            'metric_id': [f'MET-{i:010d}' for i in range(1, n_metrics + 1)],
            '@timestamp': metric_timestamps,
            'network.cell.id': self.safe_choice(cell_ids, n_metrics),
            'network.cell.prb_utilization_dl_pct': np.random.uniform(20, 95, n_metrics).round(2),
            'network.cell.prb_utilization_ul_pct': np.random.uniform(15, 80, n_metrics).round(2),
            'kpi.call_drop_rate': np.random.uniform(0.1, 3.5, n_metrics).round(3),
            'kpi.call_success_rate': np.random.uniform(95, 99.9, n_metrics).round(2),
            'network.procedure.success_rate': np.random.uniform(94, 99.5, n_metrics).round(2),
            'network.handover.success_rate': np.random.uniform(92, 99, n_metrics).round(2),
            'network.rrc.connection_success_rate': np.random.uniform(95, 99.8, n_metrics).round(2),
            'network.cell.active_subscribers': np.random.randint(50, 800, n_metrics),
            'network.transport.latency_ms': np.random.uniform(5, 50, n_metrics).round(2),
            'network.transport.packet_loss_pct': np.random.uniform(0, 2, n_metrics).round(3),
            'capacity.busy_hour.prb_utilization_p95': np.random.uniform(60, 98, n_metrics).round(2),
            'network.cell.availability_pct': np.random.uniform(99, 100, n_metrics).round(3)
        }
        
        datasets['cell_performance_metrics'] = pd.DataFrame(metric_data)

        # network_incidents (timeseries)
        n_incidents = 80
        incident_timestamps = pd.date_range(end=datetime.now(), periods=n_incidents, freq='-8H')
        
        incident_data = {
            'incident.id': [f'INC-{i:06d}' for i in range(1, n_incidents + 1)],
            '@timestamp': incident_timestamps,
            'incident.detection_time': incident_timestamps,
            'incident.resolution_time': [incident_timestamps[i] + timedelta(minutes=int(np.random.uniform(15, 240))) for i in range(n_incidents)],
            'incident.mttr_minutes': np.random.uniform(15, 240, n_incidents).round(1),
            'incident.mttd_minutes': np.random.uniform(2, 45, n_incidents).round(1),
            'incident.severity': self.safe_choice(incident_severities, n_incidents, weights=[10, 25, 40, 25]),
            'incident.type': self.safe_choice(incident_types, n_incidents),
            'network.cell.id': self.safe_choice(cell_ids, n_incidents),
            'network.region.id': self.safe_choice(regions, n_incidents),
            'incident.root_cause': self.safe_choice(root_causes, n_incidents),
            'incident.affected_subscribers': np.random.randint(10, 2000, n_incidents)
        }
        
        incident_desc_templates = [
            '{type} incident on cell {cell}, severity {severity}, affecting {affected} subscribers, root cause: {cause}',
            '{severity} severity {type} at {cell}, {affected} users impacted, identified cause: {cause}',
            'Incident {type} detected at cell {cell}, {severity} level, {affected} subscribers affected, cause: {cause}'
        ]
        incident_data['incident.description'] = [
            random.choice(incident_desc_templates).format(
                type=incident_data['incident.type'][i],
                cell=incident_data['network.cell.id'][i],
                severity=incident_data['incident.severity'][i],
                affected=incident_data['incident.affected_subscribers'][i],
                cause=incident_data['incident.root_cause'][i]
            ) for i in range(n_incidents)
        ]
        
        resolution_templates = [
            'Resolved by {action}. MTTR: {mttr}min, MTTD: {mttd}min. Root cause: {cause}',
            '{cause} addressed through {action}. Detection time: {mttd}min, resolution time: {mttr}min',
            'Issue resolved: {action}. Cause identified as {cause}. Total resolution time {mttr} minutes'
        ]
        actions = ['equipment restart', 'configuration rollback', 'hardware replacement', 
                  'software patch', 'capacity expansion', 'transport rerouting', 'parameter optimization']
        incident_data['incident.resolution_notes'] = [
            random.choice(resolution_templates).format(
                action=random.choice(actions),
                mttr=incident_data['incident.mttr_minutes'][i],
                mttd=incident_data['incident.mttd_minutes'][i],
                cause=incident_data['incident.root_cause'][i]
            ) for i in range(n_incidents)
        ]
        
        datasets['network_incidents'] = pd.DataFrame(incident_data)

        return datasets

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships from requirements"""
        return [
            ('network_signaling_events', 'network.cell.id', 'cell_site_inventory'),
            ('network_signaling_events', 'subscriber.imsi', 'subscriber_profiles'),
            ('network_signaling_events', 'network.procedure.type', 'network_procedures_reference'),
            ('cell_performance_metrics', 'network.cell.id', 'cell_site_inventory'),
            ('network_incidents', 'network.cell.id', 'cell_site_inventory')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {
            'network_signaling_events': 'Real-time network signaling events capturing all subscriber procedures, handovers, and radio measurements across the mobile network',
            'cell_site_inventory': 'Master inventory of all cell sites with location, vendor, technology, capacity and deployment information',
            'subscriber_profiles': 'Subscriber master data including plan type, device capability, tenure, and ARPU',
            'cell_performance_metrics': 'Time-series KPI metrics for cell site performance including PRB utilization, success rates, and transport metrics',
            'network_incidents': 'Network incident tracking with detection/resolution times, root cause, severity, and subscriber impact',
            'network_procedures_reference': 'Reference data for network procedure types with expected duration and success thresholds'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        """Return fields that should use semantic_text mapping"""
        return {
            'network_signaling_events': ['event.description'],
            'cell_site_inventory': ['cell.characteristics'],
            'subscriber_profiles': ['subscriber.profile_description'],
            'network_incidents': ['incident.description', 'incident.resolution_notes'],
            'network_procedures_reference': ['network.procedure.description']
        }
