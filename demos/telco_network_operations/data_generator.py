
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List


class TelcoDataGenerator(DataGeneratorModule):
    """Data generator for Telco - Network Operations"""

    @staticmethod
    def safe_choice(choices, size=None, weights=None, replace=True):
        use_python_random = False
        if len(choices) > 0:
            first_type = type(choices[0])
            if first_type in (list, tuple, dict):
                use_python_random = True

        if use_python_random:
            if size is None:
                if weights is not None:
                    return random.choices(choices, weights=weights, k=1)[0]
                else:
                    return random.choice(choices)
            if weights is not None:
                return random.choices(choices, weights=weights, k=size)
            else:
                return random.choices(choices, k=size)

        if weights is not None:
            weights = np.array(weights, dtype=float)
            if len(weights) > len(choices):
                weights = weights[:len(choices)]
            elif len(weights) < len(choices):
                raise ValueError(f"Not enough weights: {len(weights)} for {len(choices)} choices")
            probabilities = weights / weights.sum()
            if size is None:
                return np.random.choice(choices, p=probabilities, replace=replace)
            return np.random.choice(choices, size=size, p=probabilities, replace=replace)
        else:
            if size is None:
                return np.random.choice(choices)
            return np.random.choice(choices, size=size, replace=replace)

    @staticmethod
    def random_timedelta(start_date, end_date=None, days=None, hours=None, minutes=None, max_days=None):
        if max_days is not None:
            random_seconds = int(np.random.random() * int(max_days) * 86400)
            return start_date - timedelta(seconds=random_seconds)
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

    # ------------------------------------------------------------------
    # Shared reference pools (set once, reused across datasets)
    # ------------------------------------------------------------------
    def _build_reference_pools(self):
        self.cell_tower_ids = [f'CT-{i:04d}' for i in range(1, 81)]
        self.ran_node_ids = [f'RAN-{i:03d}' for i in range(1, 51)]
        self.mme_nodes = [f'MME-{i:02d}' for i in range(1, 9)]
        self.mme_pools = ['MME-POOL-EAST', 'MME-POOL-WEST', 'MME-POOL-CENTRAL']
        self.cluster_ids = ['CLUSTER-EAST-1', 'CLUSTER-EAST-2', 'CLUSTER-WEST-1', 'CLUSTER-WEST-2', 'CLUSTER-CENTRAL-1']
        self.network_elements = [f'NE-{i:03d}' for i in range(1, 41)]
        self.hss_nodes = [f'HSS-{i:02d}' for i in range(1, 7)]
        self.regions = ['EAST', 'WEST', 'CENTRAL', 'SOUTH', 'NORTH']
        self.sub_regions = {
            'EAST': ['EAST-1A', 'EAST-1B', 'EAST-2A'],
            'WEST': ['WEST-1A', 'WEST-1B', 'WEST-2A'],
            'CENTRAL': ['CENTRAL-1A', 'CENTRAL-1B'],
            'SOUTH': ['SOUTH-1A', 'SOUTH-1B'],
            'NORTH': ['NORTH-1A', 'NORTH-1B'],
        }
        self.imsi_pool = [f'310260{random.randint(100000000, 999999999)}' for _ in range(500)]
        self.apn_pool = ['internet', 'ims', 'enterprise.vpn', 'mms', 'wap', 'emergency']
        self.software_versions = ['v4.2.1', 'v4.2.3', 'v4.3.0', 'v4.3.1', 'v5.0.0', 'v5.0.2', 'v5.1.0']
        self.fault_codes = [
            'FC-1001', 'FC-1002', 'FC-1003', 'FC-2001', 'FC-2002',
            'FC-3001', 'FC-3002', 'FC-4001', 'FC-4002', 'FC-5001'
        ]
        self.bug_ids = [f'BUG-{i:05d}' for i in range(10001, 10025)]
        # cell_id pool shared across datasets
        self.cell_ids = [f'CELL-{i:04d}' for i in range(1, 201)]

    # ------------------------------------------------------------------
    # Dataset generators
    # ------------------------------------------------------------------

    def _gen_cell_tower_reference(self) -> pd.DataFrame:
        n = 300
        vendors = {'Ericsson': 35, 'Nokia': 30, 'Huawei': 20, 'Samsung': 10, 'ZTE': 5}
        mobility_zones = {'URBAN': 40, 'SUBURBAN': 30, 'RURAL': 20, 'HIGHWAY': 10}
        handoff_zone_types = {'INTRA-FREQ': 35, 'INTER-FREQ': 30, 'INTER-RAT': 25, 'EMERGENCY': 10}

        region_coords = {
            'EAST': (40.7, -74.0), 'WEST': (34.0, -118.2),
            'CENTRAL': (41.8, -87.6), 'SOUTH': (29.7, -95.3), 'NORTH': (44.9, -93.2)
        }

        rows = []
        for i, tid in enumerate(self.cell_tower_ids[:n]):
            region = self.safe_choice(self.regions)
            base_lat, base_lon = region_coords[region]
            lat = round(base_lat + np.random.normal(0, 0.5), 6)
            lon = round(base_lon + np.random.normal(0, 0.5), 6)
            rows.append({
                'cell_tower_id': tid,
                'mobility_zone': self.safe_choice(list(mobility_zones.keys()), weights=list(mobility_zones.values())),
                'handoff_zone_type': self.safe_choice(list(handoff_zone_types.keys()), weights=list(handoff_zone_types.values())),
                'geographic_region': region,
                'tower_vendor': self.safe_choice(list(vendors.keys()), weights=list(vendors.values())),
                'latitude': str(lat),
                'longitude': str(lon),
            })
        return pd.DataFrame(rows)

    def _gen_ran_site_reference(self) -> pd.DataFrame:
        n = 250
        vendors = {'Ericsson': 35, 'Nokia': 30, 'Huawei': 20, 'Samsung': 10, 'ZTE': 5}
        tech_gens = {'4G-LTE': 45, '5G-NR': 35, '4G/5G-DSS': 15, '3G-UMTS': 5}

        rows = []
        for i, rid in enumerate(self.ran_node_ids[:n]):
            region = self.safe_choice(self.regions)
            sub_region = self.safe_choice(self.sub_regions[region])
            rows.append({
                'ran_node_id': rid,
                'site_name': f'SITE-{region[:2]}-{i+1:03d}',
                'region': region,
                'sub_region': sub_region,
                'vendor': self.safe_choice(list(vendors.keys()), weights=list(vendors.values())),
                'technology_generation': self.safe_choice(list(tech_gens.keys()), weights=list(tech_gens.values())),
            })
        return pd.DataFrame(rows)

    def _gen_network_element_registry(self) -> pd.DataFrame:
        n = 200
        elem_types = {'MME': 8, 'HSS': 6, 'SGW': 8, 'PGW': 8, 'PCRF': 5, 'eNodeB': 35, 'gNodeB': 30}
        criticality_tiers = {'TIER-1': 20, 'TIER-2': 50, 'TIER-3': 30}
        vendors = {'Ericsson': 35, 'Nokia': 30, 'Huawei': 20, 'Cisco': 10, 'Samsung': 5}

        rows = []
        for i, neid in enumerate(self.network_elements[:n]):
            etype = self.safe_choice(list(elem_types.keys()), weights=list(elem_types.values()))
            rows.append({
                'network_element_id': neid,
                'element_name': f'{etype}-NODE-{i+1:03d}',
                'element_type': etype,
                'region': self.safe_choice(self.regions),
                'vendor': self.safe_choice(list(vendors.keys()), weights=list(vendors.values())),
                'capacity_threshold_msg_per_min': str(random.choice([5000, 10000, 15000, 20000, 25000, 50000])),
                'criticality_tier': self.safe_choice(list(criticality_tiers.keys()), weights=list(criticality_tiers.values())),
            })
        return pd.DataFrame(rows)

    def _gen_mme_bug_signature_lookup(self) -> pd.DataFrame:
        n = 200
        bug_data = [
            ('BUG-10001', 'MME process crash due to null pointer dereference in S1AP handler', 'S1AP', 'CRITICAL'),
            ('BUG-10002', 'Memory leak in NAS signaling module causing gradual resource exhaustion over 72 hours', 'NAS', 'HIGH'),
            ('BUG-10003', 'Race condition in attach procedure leading to duplicate session creation', 'SESSION-MGMT', 'HIGH'),
            ('BUG-10004', 'CPU spike triggered by malformed TAU request flooding from specific UE firmware', 'TAU-HANDLER', 'CRITICAL'),
            ('BUG-10005', 'HSS connection pool exhaustion under high concurrent authentication load', 'HSS-INTERFACE', 'HIGH'),
            ('BUG-10006', 'Incorrect handling of handover failure causing stale S1 context accumulation', 'HANDOVER', 'MEDIUM'),
            ('BUG-10007', 'Timer leak in paging procedure under heavy paging load conditions', 'PAGING', 'MEDIUM'),
            ('BUG-10008', 'Deadlock in bearer management module when SGW responds with unexpected cause code', 'BEARER-MGMT', 'HIGH'),
            ('BUG-10009', 'Incorrect IMSI validation leading to false authentication rejections', 'AUTH', 'CRITICAL'),
            ('BUG-10010', 'S6a interface timeout not properly handled causing subscriber authentication loop', 'S6A', 'HIGH'),
        ]
        rows = []
        for i in range(n):
            bd = bug_data[i % len(bug_data)]
            sv = self.safe_choice(self.software_versions)
            rows.append({
                'software_version': sv,
                'bug_id': bd[0],
                'bug_description': bd[1],
                'affected_component': bd[2],
                'patch_available': self.safe_choice(['YES', 'NO', 'IN-PROGRESS'], weights=[60, 20, 20]),
                'severity_rating': bd[3],
            })
        return pd.DataFrame(rows)

    def _gen_mme_bug_signatures(self) -> pd.DataFrame:
        n = 200
        bug_records = [
            ('FC-1001', 'BUG-10001', 'S1AP Null Pointer Dereference', 'CRITICAL', 'S1AP-PROCESSING',
             'CVE-2023-11001', 'Memory corruption in S1AP setup request handler causing process restart'),
            ('FC-1002', 'BUG-10002', 'NAS Memory Leak Under Load', 'HIGH', 'NAS-SIGNALING',
             'CVE-2023-11002', 'Gradual heap exhaustion in NAS procedure handler over extended operation'),
            ('FC-1003', 'BUG-10003', 'Attach Race Condition', 'HIGH', 'ATTACH-PROCEDURE',
             'CVE-2023-11003', 'Duplicate session entries created under concurrent attach storm conditions'),
            ('FC-2001', 'BUG-10004', 'TAU CPU Exhaustion', 'CRITICAL', 'TAU-HANDLER',
             'CVE-2023-11004', 'Malformed tracking area update request triggers unbounded CPU loop'),
            ('FC-2002', 'BUG-10005', 'HSS Connection Pool Depletion', 'HIGH', 'HSS-INTERFACE',
             'CVE-2023-11005', 'S6a diameter connections not released after timeout under burst load'),
            ('FC-3001', 'BUG-10006', 'Stale Handover Context Leak', 'MEDIUM', 'HANDOVER-MGMT',
             None, 'S1 handover contexts not cleaned up after inter-eNB handover failure events'),
            ('FC-3002', 'BUG-10007', 'Paging Timer Resource Leak', 'MEDIUM', 'PAGING',
             None, 'Timer objects not freed after paging timeout causing slow memory growth'),
            ('FC-4001', 'BUG-10008', 'Bearer Management Deadlock', 'HIGH', 'BEARER-MGMT',
             'CVE-2023-11008', 'Mutex deadlock between bearer creation and SGW modify bearer response'),
            ('FC-4002', 'BUG-10009', 'IMSI Validation False Reject', 'CRITICAL', 'AUTH-MODULE',
             'CVE-2023-11009', 'Off-by-one error in IMSI length check causes valid subscribers to be rejected'),
            ('FC-5001', 'BUG-10010', 'S6a Timeout Auth Loop', 'HIGH', 'S6A-INTERFACE',
             'CVE-2023-11010', 'Authentication retry loop not bounded when HSS S6a interface times out'),
        ]

        rows = []
        for i in range(n):
            br = bug_records[i % len(bug_records)]
            affected_versions = ', '.join(random.sample(self.software_versions, k=random.randint(2, 4)))
            patch_ver = self.safe_choice(['v5.1.1', 'v5.1.2', 'v5.2.0', 'PENDING', 'N/A'])
            rows.append({
                'fault_code': br[0],
                'bug_id': br[1],
                'bug_title': br[2],
                'bug_severity': br[3],
                'affected_software_versions': affected_versions,
                'bug_category': br[4],
                'patch_available': self.safe_choice(['YES', 'NO', 'IN-PROGRESS'], weights=[55, 20, 25]),
                'patch_version': patch_ver,
                'cve_reference': br[5] if br[5] else 'N/A',
                'workaround_available': self.safe_choice(['YES', 'NO'], weights=[65, 35]),
            })
        return pd.DataFrame(rows)

    def _gen_mme_system_logs(self, n: int = 800) -> pd.DataFrame:
        now = datetime.now()
        end = now
        start = now - timedelta(days=90)

        # Incident windows: 6 incidents with elevated failure rates
        incident_windows = []
        for _ in range(6):
            inc_start = self.random_timedelta(start, end)
            inc_end = inc_start + timedelta(hours=random.randint(1, 6))
            mme = self.safe_choice(self.mme_nodes)
            incident_windows.append((inc_start, min(inc_end, end), mme))

        fault_cat_map = {
            'FC-1001': ('S1AP', 'HARDWARE'), 'FC-1002': ('MEMORY', 'SOFTWARE'),
            'FC-1003': ('SESSION', 'SOFTWARE'), 'FC-2001': ('CPU', 'SOFTWARE'),
            'FC-2002': ('HSS', 'CONNECTIVITY'), 'FC-3001': ('HANDOVER', 'SOFTWARE'),
            'FC-3002': ('PAGING', 'SOFTWARE'), 'FC-4001': ('BEARER', 'SOFTWARE'),
            'FC-4002': ('AUTH', 'SOFTWARE'), 'FC-5001': ('S6A', 'CONNECTIVITY'),
        }

        process_names = ['mme_main', 'nas_handler', 's1ap_proc', 'hss_client', 'bearer_mgr', 'paging_mgr']
        error_codes = ['ERR-0001', 'ERR-0002', 'ERR-0100', 'ERR-0200', 'ERR-0300', 'ERR-0400', 'ERR-0500']
        log_severities = {'ERROR': 30, 'WARNING': 40, 'INFO': 25, 'CRITICAL': 5}
        log_levels = {'ERROR': 30, 'WARN': 40, 'INFO': 25, 'DEBUG': 5}

        rows = []
        # 30% baseline
        baseline_n = int(n * 0.3)
        for _ in range(baseline_n):
            ts = self.random_timedelta(start, end)
            mme = self.safe_choice(self.mme_nodes)
            pool = self.safe_choice(self.mme_pools)
            fc = self.safe_choice(self.fault_codes)
            fcat, fsev_cat = fault_cat_map.get(fc, ('GENERAL', 'SOFTWARE'))
            sv = self.safe_choice(self.software_versions)
            cpu = round(np.random.beta(2, 5) * 100, 1)
            mem = round(np.random.beta(2, 4) * 100, 1)
            rows.append(self._mme_row(ts, mme, pool, sv, cpu, mem, fc, fcat, process_names, error_codes, log_severities, log_levels))

        # 70% incident-clustered
        inc_n = n - baseline_n
        per_inc = inc_n // len(incident_windows)
        for (inc_start, inc_end, inc_mme) in incident_windows:
            for _ in range(per_inc):
                ts = self.random_timedelta(inc_start, inc_end)
                fc = self.safe_choice(self.fault_codes[:5])  # higher-severity codes
                fcat, _ = fault_cat_map.get(fc, ('GENERAL', 'SOFTWARE'))
                sv = self.safe_choice(self.software_versions[:4])  # older/buggy versions
                cpu = round(min(100, np.random.beta(5, 2) * 100), 1)
                mem = round(min(100, np.random.beta(5, 2) * 100), 1)
                pool = self.safe_choice(self.mme_pools)
                rows.append(self._mme_row(ts, inc_mme, pool, sv, cpu, mem, fc, fcat, process_names, error_codes, log_severities, log_levels))

        random.shuffle(rows)
        return pd.DataFrame(rows[:n])

    def _mme_row(self, ts, mme, pool, sv, cpu, mem, fc, fcat, process_names, error_codes, log_severities, log_levels):
        active_ue = random.randint(500, 15000)
        attach_rate = random.randint(10, 500)
        attach_fail_rate = round(np.random.beta(2, 8), 4)
        return {
            '@timestamp': ts,
            'mme_node_id': mme,
            'mme_pool_id': pool,
            'cpu_utilization_pct': str(cpu),
            'memory_utilization_pct': str(mem),
            'active_ue_sessions': str(active_ue),
            'attach_request_rate': str(attach_rate),
            'attach_failure_rate': str(round(attach_fail_rate * 100, 2)),
            'software_version': sv,
            'process_name': self.safe_choice(process_names),
            'log_severity': self.safe_choice(list(log_severities.keys()), weights=list(log_severities.values())),
            'error_code': self.safe_choice(error_codes),
            'fault_code': fc,
            'fault_category': fcat,
            'fault_severity': self.safe_choice(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'], weights=[10, 25, 40, 25]),
            'affected_subscribers': str(random.randint(0, 5000)),
            'attach_failures': str(random.randint(0, 200)),
            'detach_events': str(random.randint(0, 100)),
            's1ap_errors': str(random.randint(0, 50)),
            'nas_procedure_failures': str(random.randint(0, 80)),
            'core_dump_generated': self.safe_choice(['true', 'false'], weights=[5, 95]),
            'log_level': self.safe_choice(list(log_levels.keys()), weights=list(log_levels.values())),
            's1ap_error_count': random.randint(0, 50),
            'nas_signaling_error_count': random.randint(0, 80),
        }

    def _gen_signaling_logs(self, n: int = 600) -> pd.DataFrame:
        now = datetime.now()
        end = now
        start = now - timedelta(days=90)

        protocols = {'S1AP': 25, 'NAS': 25, 'DIAMETER': 20, 'GTP-C': 15, 'SS7': 10, 'SIP': 5}
        msg_types_by_proto = {
            'S1AP': ['InitialUEMessage', 'UEContextSetupRequest', 'UEContextReleaseCommand', 'HandoverRequest', 'PathSwitchRequest'],
            'NAS': ['AttachRequest', 'AttachAccept', 'AttachReject', 'DetachRequest', 'TAURequest', 'ServiceRequest'],
            'DIAMETER': ['Authentication-Information-Request', 'Authentication-Information-Answer', 'Update-Location-Request', 'Update-Location-Answer'],
            'GTP-C': ['CreateSessionRequest', 'CreateSessionResponse', 'DeleteSessionRequest', 'ModifyBearerRequest'],
            'SS7': ['MAP-SendAuthInfo', 'MAP-UpdateLocation', 'MAP-SendRoutingInfo', 'SCCP-UDT'],
            'SIP': ['INVITE', 'BYE', 'REGISTER', 'OPTIONS', '200 OK', '404 Not Found'],
        }
        cause_codes = {
            'SUCCESS': 40, 'TIMEOUT': 15, 'REJECT': 15, 'PROTOCOL-ERROR': 10,
            'RESOURCE-UNAVAILABLE': 8, 'AUTH-FAILURE': 7, 'UNKNOWN': 5
        }
        directions = {'REQUEST': 50, 'RESPONSE': 45, 'NOTIFICATION': 5}

        rows = []
        for _ in range(n):
            ts = self.random_timedelta(start, end)
            ne = self.safe_choice(self.network_elements)
            proto = self.safe_choice(list(protocols.keys()), weights=list(protocols.values()))
            msg = self.safe_choice(msg_types_by_proto[proto])
            src = self.safe_choice(self.network_elements)
            dst_pool = [x for x in self.network_elements if x != src]
            dst = self.safe_choice(dst_pool if dst_pool else self.network_elements)
            rows.append({
                '@timestamp': ts,
                'network_element_id': ne,
                'signaling_protocol': proto,
                'message_type': msg,
                'source_node': src,
                'destination_node': dst,
                'message_direction': self.safe_choice(list(directions.keys()), weights=list(directions.values())),
                'session_id': f'SIG-{uuid.uuid4().hex[:12].upper()}',
                'cause_code': self.safe_choice(list(cause_codes.keys()), weights=list(cause_codes.values())),
            })
        return pd.DataFrame(rows)

    def _gen_ran_performance_metrics(self, n: int = 700) -> pd.DataFrame:
        now = datetime.now()
        end = now
        start = now - timedelta(days=90)

        ho_types = {'INTRA-FREQ': 35, 'INTER-FREQ': 25, 'INTER-RAT-4G-5G': 20, 'INTER-RAT-5G-4G': 15, 'EMERGENCY': 5}
        rat_types = ['LTE', 'NR', 'UMTS']

        # Cascade failure windows: clusters of handover failures
        cascade_windows = []
        for _ in range(5):
            c_start = self.random_timedelta(start, end)
            c_end = c_start + timedelta(hours=random.randint(1, 4))
            affected_ran = random.sample(self.ran_node_ids[:30], k=random.randint(3, 8))
            cascade_windows.append((c_start, min(c_end, end), affected_ran))

        rows = []
        baseline_n = int(n * 0.35)
        for _ in range(baseline_n):
            ts = self.random_timedelta(start, end)
            ran = self.safe_choice(self.ran_node_ids)
            cell = self.safe_choice(self.cell_ids)
            ho_attempts = random.randint(10, 500)
            ho_fail_rate = np.random.beta(1, 9)
            ho_failures = int(ho_attempts * ho_fail_rate)
            src_rat = self.safe_choice(rat_types)
            tgt_pool = [r for r in rat_types if r != src_rat]
            tgt_rat = self.safe_choice(tgt_pool if tgt_pool else rat_types)
            rows.append({
                '@timestamp': ts,
                'ran_node_id': ran,
                'cell_id': cell,
                'handover_attempts': str(ho_attempts),
                'handover_failures': str(ho_failures),
                'handover_type': self.safe_choice(list(ho_types.keys()), weights=list(ho_types.values())),
                'source_rat': src_rat,
                'target_rat': tgt_rat,
                'ue_count': random.randint(5, 800),
            })

        # Cascade failure rows
        cascade_n = n - baseline_n
        per_cascade = cascade_n // len(cascade_windows)
        for (c_start, c_end, affected_ran) in cascade_windows:
            for _ in range(per_cascade):
                ts = self.random_timedelta(c_start, c_end)
                ran = self.safe_choice(affected_ran)
                cell = self.safe_choice(self.cell_ids[:50])  # same zone cells
                ho_attempts = random.randint(50, 300)
                ho_fail_rate = np.random.beta(6, 3)  # high failure rate
                ho_failures = int(ho_attempts * ho_fail_rate)
                src_rat = self.safe_choice(['LTE', 'NR'])
                tgt_rat = 'NR' if src_rat == 'LTE' else 'LTE'
                rows.append({
                    '@timestamp': ts,
                    'ran_node_id': ran,
                    'cell_id': cell,
                    'handover_attempts': str(ho_attempts),
                    'handover_failures': str(ho_failures),
                    'handover_type': self.safe_choice(['INTER-FREQ', 'INTER-RAT-4G-5G', 'INTER-RAT-5G-4G']),
                    'source_rat': src_rat,
                    'target_rat': tgt_rat,
                    'ue_count': random.randint(100, 1000),
                })

        random.shuffle(rows)
        return pd.DataFrame(rows[:n])

    def _gen_call_detail_records(self, n: int = 600) -> pd.DataFrame:
        now = datetime.now()
        end = now
        start = now - timedelta(days=90)

        network_types = {'LTE': 45, '5G-NR': 35, 'UMTS': 15, 'GSM': 5}
        # Handoff failure clusters
        failure_windows = []
        for _ in range(4):
            f_start = self.random_timedelta(start, end)
            f_end = f_start + timedelta(hours=random.randint(1, 3))
            affected_towers = random.sample(self.cell_tower_ids[:40], k=random.randint(3, 10))
            failure_windows.append((f_start, min(f_end, end), affected_towers))

        rows = []
        baseline_n = int(n * 0.4)
        for _ in range(baseline_n):
            ts = self.random_timedelta(start, end)
            tower = self.safe_choice(self.cell_tower_ids)
            sub = self.safe_choice(self.imsi_pool)
            duration = int(np.random.lognormal(4, 1))
            dropped = self.safe_choice(['true', 'false'], weights=[5, 95])
            ho_event = self.safe_choice(['INTRA-FREQ', 'INTER-FREQ', 'INTER-RAT', 'NONE'], weights=[20, 15, 10, 55])
            rows.append({
                '@timestamp': ts,
                'cell_tower_id': tower,
                'call_dropped': dropped,
                'call_attempt': self.safe_choice(['true', 'false'], weights=[90, 10]),
                'handoff_event': ho_event,
                'subscriber_id': sub,
                'call_duration_seconds': str(duration),
                'signal_strength_dbm': str(random.randint(-120, -50)),
                'network_type': self.safe_choice(list(network_types.keys()), weights=list(network_types.values())),
            })

        # Failure-clustered rows
        fail_n = n - baseline_n
        per_window = fail_n // len(failure_windows)
        for (f_start, f_end, affected_towers) in failure_windows:
            for _ in range(per_window):
                ts = self.random_timedelta(f_start, f_end)
                tower = self.safe_choice(affected_towers)
                sub = self.safe_choice(self.imsi_pool)
                duration = int(np.random.lognormal(2, 0.5))
                rows.append({
                    '@timestamp': ts,
                    'cell_tower_id': tower,
                    'call_dropped': self.safe_choice(['true', 'false'], weights=[60, 40]),
                    'call_attempt': 'true',
                    'handoff_event': self.safe_choice(['INTER-FREQ', 'INTER-RAT', 'INTRA-FREQ'], weights=[40, 35, 25]),
                    'subscriber_id': sub,
                    'call_duration_seconds': str(duration),
                    'signal_strength_dbm': str(random.randint(-120, -90)),
                    'network_type': self.safe_choice(list(network_types.keys()), weights=list(network_types.values())),
                })

        random.shuffle(rows)
        return pd.DataFrame(rows[:n])

    def _gen_data_session_logs(self, n: int = 1200) -> pd.DataFrame:
        now = datetime.now()
        timestamps = pd.date_range(end=now, periods=n, freq='h')

        rat_types = {'LTE': 45, '5G-NR': 35, 'NR-SA': 10, 'NR-NSA': 10}
        session_statuses = {'ACTIVE': 30, 'COMPLETED': 45, 'FAILED': 15, 'INTERRUPTED': 10}
        term_causes = {
            'NORMAL': 40, 'UE-DETACH': 15, 'NETWORK-RELEASE': 10,
            'AUTH-FAILURE': 10, 'TIMEOUT': 8, 'HANDOVER-FAILURE': 7,
            'RESOURCE-EXHAUSTION': 5, 'POLICY-REJECT': 5
        }

        n_arr = n
        session_ids = [f'SES-{uuid.uuid4().hex[:12].upper()}' for _ in range(n_arr)]
        statuses = self.safe_choice(list(session_statuses.keys()), size=n_arr, weights=list(session_statuses.values()))
        t_causes = self.safe_choice(list(term_causes.keys()), size=n_arr, weights=list(term_causes.values()))
        rats = self.safe_choice(list(rat_types.keys()), size=n_arr, weights=list(rat_types.values()))
        subs = self.safe_choice(self.imsi_pool, size=n_arr)
        apns = self.safe_choice(self.apn_pool, size=n_arr)
        cells = self.safe_choice(self.cell_ids, size=n_arr)
        durations = np.random.lognormal(mean=6, sigma=1.5, size=n_arr).astype(int)
        bytes_xfer = np.random.lognormal(mean=10, sigma=2, size=n_arr).astype(int)

        return pd.DataFrame({
            '@timestamp': timestamps,
            'session_id': session_ids,
            'session_status': statuses,
            'termination_cause': t_causes,
            'rat_type': rats,
            'subscriber_id': subs,
            'apn': apns,
            'cell_id': cells,
            'session_duration_seconds': [str(d) for d in durations],
            'bytes_transferred': [str(b) for b in bytes_xfer],
        })

    def _gen_core_network_events(self, n: int = 1200) -> pd.DataFrame:
        now = datetime.now()
        end = now
        start = now - timedelta(days=90)

        severities = {'CRITICAL': 8, 'HIGH': 20, 'MEDIUM': 35, 'LOW': 30, 'INFO': 7}
        event_types = {
            'SPLIT-BRAIN': 5, 'SIGNALING-STORM': 7, 'AUTH-FAILURE-BURST': 12,
            'MME-CRASH': 6, 'HSS-SYNC-FAILURE': 8, 'RESOURCE-EXHAUSTION': 10,
            'SS7-ATTACK': 5, 'ROGUE-ACCESS': 4, 'HANDOVER-CASCADE': 8,
            'BEARER-FAILURE': 10, 'PAGING-OVERLOAD': 8, 'NORMAL-OPERATION': 17
        }
        consensus_states = {'LEADER': 30, 'FOLLOWER': 40, 'CANDIDATE': 15, 'SPLIT': 10, 'UNKNOWN': 5}
        node_roles = {'MME-PRIMARY': 20, 'MME-SECONDARY': 20, 'HSS-PRIMARY': 15, 'HSS-SECONDARY': 15,
                      'SGW': 15, 'PGW': 15}

        # Incident windows for clustering
        incident_windows = []
        for _ in range(8):
            i_start = self.random_timedelta(start, end)
            i_end = i_start + timedelta(hours=random.randint(1, 8))
            cluster = self.safe_choice(self.cluster_ids)
            region = self.safe_choice(self.regions)
            etype = self.safe_choice(['SPLIT-BRAIN', 'SIGNALING-STORM', 'AUTH-FAILURE-BURST',
                                      'MME-CRASH', 'HSS-SYNC-FAILURE', 'SS7-ATTACK'])
            incident_windows.append((i_start, min(i_end, end), cluster, region, etype))

        event_templates = {
            'SPLIT-BRAIN': [
                'Core cluster {cluster} detected split-brain condition; nodes {node} and peer lost quorum consensus in region {region}. Automatic failover initiated.',
                'Split-brain event on {cluster}: node {node} in {region} cannot reach majority peers. Consensus state transitioned to CANDIDATE.',
                'Network partition detected on {cluster} in {region}. Node {node} isolated from cluster majority, triggering emergency re-election.',
            ],
            'SIGNALING-STORM': [
                'Signaling storm detected on {cluster} in {region}: node {node} receiving {rate} messages/min, exceeding capacity threshold.',
                'Node {node} on {cluster} experiencing signaling overload in {region}. NAS message queue depth exceeds safe operating limit.',
                'Abnormal signaling rate surge on {node} in {region}. Cluster {cluster} applying traffic shaping to protect core stability.',
            ],
            'AUTH-FAILURE-BURST': [
                'Mass authentication failure burst detected on {cluster} in {region}. Node {node} logging elevated HSS reject rate over past 15 minutes.',
                'HSS returning repeated authentication failures for subscribers homed on {node} in {region}. Cluster {cluster} flagged for investigation.',
                'Authentication failure spike on {cluster}: node {node} in {region} recording abnormal EAP-AKA failure rate. Possible HSS sync issue.',
            ],
            'MME-CRASH': [
                'MME node {node} in cluster {cluster} ({region}) crashed unexpectedly. Core dump captured. Subscribers migrating to standby MME.',
                'Process restart detected on {node} in {cluster}, {region}. S1AP handler terminated with SIGSEGV. Automatic recovery in progress.',
                'Node {node} on {cluster} in {region} entered fault state. MME watchdog triggered process restart after unresponsive health check.',
            ],
            'HSS-SYNC-FAILURE': [
                'HSS database synchronization failure on {cluster} in {region}. Node {node} reporting inconsistent subscriber profile data.',
                'Replication lag detected between HSS nodes on {cluster} in {region}. Node {node} diverged from primary by more than threshold.',
                'HSS sync error on {node} in {region}: cluster {cluster} reporting stale authentication vectors affecting subscriber attach.',
            ],
            'SS7-ATTACK': [
                'Suspected SS7 MAP attack detected on {node} in {region}. Cluster {cluster} logging abnormal MAP-SendRoutingInfo flood from foreign PLMN.',
                'SS7 security alert: node {node} in {cluster} ({region}) receiving unsolicited MAP location update requests from unregistered network.',
                'Rogue SS7 signaling detected targeting {node} on {cluster} in {region}. Possible subscriber tracking or interception attempt.',
            ],
            'RESOURCE-EXHAUSTION': [
                'Resource exhaustion on {node} in {cluster} ({region}): CPU at critical threshold, NAS processing queue backing up.',
                'Memory pressure on {node} in {region}. Cluster {cluster} reporting heap utilization above 90% on MME process.',
                'File descriptor exhaustion on {node} in {cluster}, {region}. S1AP connections being refused due to OS resource limits.',
            ],
            'ROGUE-ACCESS': [
                'Rogue network access attempt detected at {node} in {region}. Cluster {cluster} blocking unauthorized PLMN attach request.',
                'Unauthorized roaming attempt flagged on {cluster} in {region}. Node {node} rejecting attach from unrecognized IMSI range.',
                'Security alert on {node} in {cluster} ({region}): abnormal international roaming pattern suggests misconfig or active attack.',
            ],
            'HANDOVER-CASCADE': [
                'Handover cascade failure on {cluster} in {region}: node {node} reporting chain of X2 handover failures across multiple cells.',
                'Cell tower handoff cascade detected on {node} in {region}. Cluster {cluster} logging sequential inter-frequency handover failures.',
                'Cascading handover failure event on {cluster}: node {node} in {region} unable to complete inter-RAT transfers. UE sessions dropping.',
            ],
            'BEARER-FAILURE': [
                'Bearer setup failure spike on {node} in {cluster} ({region}). GTP-C create session response rate declining sharply.',
                'Dedicated bearer establishment failures on {cluster} in {region}. Node {node} logging SGW modify bearer timeouts.',
                'EPS bearer failure on {node} in {region}: cluster {cluster} reporting PGW policy rule application errors for IMS APN.',
            ],
            'PAGING-OVERLOAD': [
                'Paging overload on {node} in {cluster} ({region}): paging queue depth exceeding threshold, causing delayed UE reachability.',
                'MME paging storm detected on {cluster} in {region}. Node {node} processing abnormal volume of S1AP paging requests.',
                'Paging channel saturation on {node} in {region}. Cluster {cluster} applying paging rate limiting to protect RAN interface.',
            ],
            'NORMAL-OPERATION': [
                'Node {node} in {cluster} ({region}) operating within normal parameters. All health checks passing.',
                'Routine status update from {node} in {region}: cluster {cluster} nominal, no active alarms.',
                'Scheduled maintenance window completed on {node} in {cluster}, {region}. All services restored.',
            ],
        }

        alert_templates = {
            'SPLIT-BRAIN': 'ALERT: Split-brain condition on cluster {cluster} in {region} requires immediate operator intervention.',
            'SIGNALING-STORM': 'ALERT: Signaling storm threshold exceeded on {node} in {region}. Traffic throttling engaged.',
            'AUTH-FAILURE-BURST': 'ALERT: Mass auth failure detected on {cluster} in {region}. Check HSS health and S6a connectivity.',
            'MME-CRASH': 'ALERT: MME process crash on {node} in {cluster} ({region}). Subscriber failover in progress.',
            'HSS-SYNC-FAILURE': 'ALERT: HSS sync failure on {cluster} in {region}. Authentication service may be degraded.',
            'SS7-ATTACK': 'ALERT: SS7 security attack suspected on {node} in {region}. Engage security team immediately.',
            'RESOURCE-EXHAUSTION': 'ALERT: Resource exhaustion on {node} in {cluster} ({region}). Capacity intervention required.',
            'ROGUE-ACCESS': 'ALERT: Rogue access attempt on {cluster} in {region}. Review firewall and roaming policy.',
            'HANDOVER-CASCADE': 'ALERT: Handover cascade failure on {cluster} in {region}. RAN coordination required.',
            'BEARER-FAILURE': 'ALERT: Bearer failure rate elevated on {node} in {cluster} ({region}). Check SGW and PGW status.',
            'PAGING-OVERLOAD': 'ALERT: Paging overload on {node} in {region}. Reduce paging load or increase capacity.',
            'NORMAL-OPERATION': 'INFO: No active alerts for {node} in {cluster} ({region}). System nominal.',
        }

        rows = []
        baseline_n = int(n * 0.35)
        for _ in range(baseline_n):
            ts = self.random_timedelta(start, end)
            etype = self.safe_choice(list(event_types.keys()), weights=list(event_types.values()))
            cluster = self.safe_choice(self.cluster_ids)
            region = self.safe_choice(self.regions)
            node = self.safe_choice(self.mme_nodes + self.hss_nodes)
            rows.append(self._core_event_row(ts, etype, cluster, region, node, severities, consensus_states, node_roles, event_templates, alert_templates))

        inc_n = n - baseline_n
        per_inc = inc_n // len(incident_windows)
        for (i_start, i_end, cluster, region, etype) in incident_windows:
            for _ in range(per_inc):
                ts = self.random_timedelta(i_start, i_end)
                node = self.safe_choice(self.mme_nodes + self.hss_nodes)
                rows.append(self._core_event_row(ts, etype, cluster, region, node, severities, consensus_states, node_roles, event_templates, alert_templates, force_high=True))

        random.shuffle(rows)
        return pd.DataFrame(rows[:n])

    def _core_event_row(self, ts, etype, cluster, region, node, severities, consensus_states, node_roles, event_templates, alert_templates, force_high=False):
        sev_weights = {'CRITICAL': 25, 'HIGH': 35, 'MEDIUM': 25, 'LOW': 10, 'INFO': 5} if force_high else severities
        template = self.safe_choice(event_templates[etype])
        rate = random.randint(5000, 50000)
        desc = template.format(cluster=cluster, node=node, region=region, rate=rate)
        alert_tmpl = alert_templates[etype]
        alert = alert_tmpl.format(cluster=cluster, node=node, region=region)
        affected_peers = str(random.randint(0, 5))
        score = str(round(np.random.beta(3, 2) * 100 if force_high else np.random.beta(2, 5) * 100, 2))
        return {
            '@timestamp': ts,
            'event_id': f'EVT-{uuid.uuid4().hex[:10].upper()}',
            'event_title': f'{etype.replace("-", " ").title()} - {node} - {region}',
            'event_description': desc,
            'alert_message': alert,
            'node_id': node,
            'node_role': self.safe_choice(list(node_roles.keys()), weights=list(node_roles.values())),
            'cluster_id': cluster,
            'network_region': region,
            'severity': self.safe_choice(list(sev_weights.keys()), weights=list(sev_weights.values())),
            'event_type': etype,
            'consensus_state': self.safe_choice(list(consensus_states.keys()), weights=list(consensus_states.values())),
            'affected_peers': affected_peers,
            'score': score,
        }

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        self._build_reference_pools()

        datasets = {
            'cell_tower_reference': self._gen_cell_tower_reference(),
            'ran_site_reference': self._gen_ran_site_reference(),
            'network_element_registry': self._gen_network_element_registry(),
            'mme_bug_signature_lookup': self._gen_mme_bug_signature_lookup(),
            'mme_bug_signatures': self._gen_mme_bug_signatures(),
            'mme_system_logs': self._gen_mme_system_logs(n=800),
            'signaling_logs': self._gen_signaling_logs(n=600),
            'ran_performance_metrics': self._gen_ran_performance_metrics(n=700),
            'call_detail_records': self._gen_call_detail_records(n=600),
            'data_session_logs': self._gen_data_session_logs(n=1200),
            'core_network_events': self._gen_core_network_events(n=1200),
        }
        return datasets

    def get_relationships(self) -> List[tuple]:
        return [
            ('data_session_logs', 'cell_id', 'cell_tower_reference'),
            ('call_detail_records', 'cell_tower_id', 'cell_tower_reference'),
            ('ran_performance_metrics', 'ran_node_id', 'ran_site_reference'),
            ('ran_performance_metrics', 'cell_id', 'cell_tower_reference'),
            ('signaling_logs', 'network_element_id', 'network_element_registry'),
            ('mme_system_logs', 'fault_code', 'mme_bug_signatures'),
            ('mme_system_logs', 'software_version', 'mme_bug_signature_lookup'),
            ('mme_bug_signatures', 'fault_code', 'mme_system_logs'),
            ('core_network_events', 'node_id', 'network_element_registry'),
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        return {
            'data_session_logs': 'Time-series log of 4G/5G data sessions including status, RAT type, APN, cell, subscriber, and session metrics.',
            'call_detail_records': 'Per-call records including dropped call flags, handoff events, signal strength, and tower association.',
            'cell_tower_reference': 'Reference table of cell towers with geographic, vendor, and handoff zone metadata.',
            'core_network_events': 'Time-series core network events covering split-brain, signaling storms, auth failures, SS7 attacks, and more.',
            'mme_system_logs': 'MME node operational logs including CPU/memory utilization, error codes, fault codes, and subscriber impact.',
            'mme_bug_signature_lookup': 'Lookup table mapping software versions to known MME bug IDs and descriptions.',
            'signaling_logs': 'Signaling protocol messages (S1AP, NAS, DIAMETER, SS7, GTP-C) with cause codes and direction.',
            'network_element_registry': 'Registry of core and RAN network elements with type, region, vendor, and capacity thresholds.',
            'ran_performance_metrics': 'RAN node handover performance metrics including attempts, failures, and RAT types.',
            'ran_site_reference': 'Reference table of RAN sites with region, vendor, and technology generation.',
            'mme_bug_signatures': 'Lookup table mapping fault codes to known MME bug signatures, CVEs, and patch availability.',
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        return {
            'core_network_events': ['event_description', 'alert_message'],
            'mme_bug_signature_lookup': ['bug_description'],
            'mme_bug_signatures': ['bug_title'],
            'signaling_logs': ['message_type'],
        }
