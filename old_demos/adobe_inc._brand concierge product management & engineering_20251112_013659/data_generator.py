
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List

class AdobeIncDataGenerator(DataGeneratorModule):
    """Data generator for Adobe Inc. - Brand Concierge Product Management & Engineering"""

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
        
        now = datetime.now()
        
        # Reference: tenants (850 rows)
        n_tenants = 150
        tiers = ['Enterprise', 'Professional', 'Standard']
        verticals = ['Retail', 'Financial Services', 'Healthcare', 'Technology', 'Manufacturing', 
                     'Media & Entertainment', 'Telecommunications', 'Travel & Hospitality']
        csm_names = ['Sarah Chen', 'Michael Rodriguez', 'Emily Watson', 'James Kim', 'Maria Garcia',
                     'David Thompson', 'Lisa Patel', 'Robert Johnson', 'Jennifer Lee', 'Chris Anderson']
        
        datasets['tenants'] = pd.DataFrame({
            'tenant_id': [f'TNT-{str(i+1000).zfill(5)}' for i in range(n_tenants)],
            'tenant_name': [f'{random.choice(["Acme", "Global", "Premier", "United", "Apex", "Summit"])} {random.choice(["Corp", "Inc", "LLC", "Group", "Industries", "Solutions"])}' for _ in range(n_tenants)],
            'account_tier': self.safe_choice(tiers, n_tenants, weights=[0.25, 0.40, 0.35]),
            'contract_arr': np.random.choice([25000, 50000, 100000, 250000, 500000, 1000000, 2500000], n_tenants, p=[0.15, 0.25, 0.25, 0.15, 0.10, 0.07, 0.03]),
            'renewal_date': [now + timedelta(days=int(np.random.randint(-30, 365))) for _ in range(n_tenants)],
            'customer_success_manager': self.safe_choice(csm_names, n_tenants),
            'sla_target_p95_ms': self.safe_choice([300, 400, 500, 750], n_tenants, weights=[0.15, 0.25, 0.45, 0.15]),
            'industry_vertical': self.safe_choice(verticals, n_tenants)
        })
        
        tenant_ids = datasets['tenants']['tenant_id'].tolist()
        
        # Reference: api_partners (40 rows)
        n_partners = 40
        partner_types = ['DAM', 'CMS', 'Analytics', 'Marketing Automation', 'Social Media', 'E-commerce', 'CDN', 'Translation']
        partner_tiers = ['Platinum', 'Gold', 'Silver', 'Bronze']
        
        datasets['api_partners'] = pd.DataFrame({
            'partner_id': [f'PTR-{str(i+100).zfill(4)}' for i in range(n_partners)],
            'partner_name': [f'{random.choice(["CloudSync", "DataFlow", "MediaHub", "ContentLink", "AssetBridge", "SyncPro", "IntegrationX", "ConnectAPI"])} {random.choice(["Platform", "Service", "Solutions", "Connect", "API"])}' for _ in range(n_partners)],
            'integration_type': self.safe_choice(partner_types, n_partners),
            'tier': self.safe_choice(partner_tiers, n_partners, weights=[0.15, 0.25, 0.35, 0.25]),
            'webhook_url': [f'https://partner{i+1}.example.com/webhooks/adobe' for i in range(n_partners)],
            'contact_email': [f'integration{i+1}@partner.example.com' for i in range(n_partners)],
            'partnership_health_score': np.random.uniform(0.65, 0.99, n_partners)
        })
        
        partner_ids = datasets['api_partners']['partner_id'].tolist()
        
        # Reference: ab_experiments (150 rows)
        n_experiments = 150
        features = ['Asset Search', 'Bulk Upload', 'Smart Tagging', 'Collaboration', 'Version Control',
                   'Analytics Dashboard', 'Export Pipeline', 'Metadata Editor', 'Collections', 'Sharing']
        metrics = ['conversion_rate', 'time_to_complete', 'feature_adoption', 'user_satisfaction', 'task_success_rate']
        
        exp_templates = [
            'Testing {variant} for improved {feature} performance',
            'Evaluating {variant} design to increase {feature} engagement',
            'Measuring impact of {variant} on {feature} workflow efficiency',
            'Comparing {variant} approach for {feature} user experience'
        ]
        
        datasets['ab_experiments'] = pd.DataFrame({
            'experiment_id': [f'EXP-{str(i+1).zfill(5)}' for i in range(n_experiments)],
            'experiment_name': [f'{random.choice(features)} - {random.choice(["Redesign", "Optimization", "Enhancement", "Simplification"])} Test' for _ in range(n_experiments)],
            'variant_id': [f'VAR-{random.choice(["A", "B", "C"])}-{str(i+1).zfill(5)}' for i in range(n_experiments)],
            'variant_name': self.safe_choice(['Control', 'Variant A', 'Variant B', 'Variant C'], n_experiments),
            'feature_name': self.safe_choice(features, n_experiments),
            'start_date': [now - timedelta(days=int(np.random.randint(1, 90))) for _ in range(n_experiments)],
            'target_metric': self.safe_choice(metrics, n_experiments),
            'control_baseline': np.random.uniform(0.15, 0.75, n_experiments),
            'experiment_hypothesis': [random.choice(exp_templates).format(
                variant=random.choice(['new UI', 'simplified workflow', 'enhanced algorithm', 'redesigned interface']),
                feature=random.choice(features)
            ) for _ in range(n_experiments)]
        })
        
        experiment_ids = datasets['ab_experiments']['experiment_id'].tolist()
        feature_names = datasets['ab_experiments']['feature_name'].unique().tolist()
        
        # Timeseries: api_requests (3000 rows)
        n_api = 3000
        endpoints = ['/api/v2/assets', '/api/v2/search', '/api/v2/upload', '/api/v2/metadata',
                    '/api/v2/collections', '/api/v2/share', '/api/v2/analytics', '/api/v2/users',
                    '/api/v2/tags', '/api/v2/versions', '/api/v2/export', '/api/v2/webhooks']
        regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']
        statuses = [200, 201, 204, 400, 401, 403, 404, 429, 500, 502, 503]
        status_weights = [0.70, 0.10, 0.05, 0.03, 0.02, 0.02, 0.02, 0.02, 0.02, 0.01, 0.01]
        
        error_msgs = [
            'Rate limit exceeded for tenant',
            'Invalid authentication token',
            'Resource not found',
            'Insufficient permissions',
            'Database connection timeout',
            'Upstream service unavailable',
            'Request payload too large',
            'Invalid query parameters'
        ]
        
        api_timestamps = pd.date_range(end=now, periods=n_api, freq='30s')
        api_statuses = self.safe_choice(statuses, n_api, weights=status_weights)
        
        datasets['api_requests'] = pd.DataFrame({
            'request_id': [f'REQ-{str(i+100000).zfill(8)}' for i in range(n_api)],
            '@timestamp': api_timestamps,
            'tenant_id': self.safe_choice(tenant_ids, n_api),
            'partner_id': self.safe_choice(partner_ids + [None]*10, n_api),
            'endpoint': self.safe_choice(endpoints, n_api),
            'http_status': api_statuses,
            'response_time_ms': np.where(
                api_statuses >= 500,
                np.random.lognormal(6.5, 0.8, n_api),
                np.where(api_statuses >= 400,
                         np.random.lognormal(4.5, 0.6, n_api),
                         np.random.lognormal(4.2, 0.7, n_api))
            ),
            'region': self.safe_choice(regions, n_api),
            'error_message': [random.choice(error_msgs) if s >= 400 else None for s in api_statuses],
            'user_id': [f'USR-{str(np.random.randint(10000, 135000)).zfill(6)}' for _ in range(n_api)]
        })
        
        user_ids = datasets['api_requests']['user_id'].unique().tolist()[:1000]
        
        # Timeseries: feature_usage_events (2500 rows)
        n_features = 2500
        categories = ['Asset Management', 'Search & Discovery', 'Collaboration', 'Analytics', 'Administration']
        
        feature_timestamps = pd.date_range(end=now, periods=n_features, freq='45s')
        
        datasets['feature_usage_events'] = pd.DataFrame({
            'event_id': [f'EVT-{str(i+500000).zfill(8)}' for i in range(n_features)],
            '@timestamp': feature_timestamps,
            'user_id': self.safe_choice(user_ids, n_features),
            'tenant_id': self.safe_choice(tenant_ids, n_features),
            'feature_name': self.safe_choice(feature_names, n_features),
            'feature_category': self.safe_choice(categories, n_features),
            'session_id': [f'SES-{str(np.random.randint(100000, 999999)).zfill(7)}' for _ in range(n_features)],
            'experiment_variant': self.safe_choice(experiment_ids + [None]*5, n_features),
            'interaction_duration_ms': np.random.lognormal(8.5, 1.2, n_features),
            'conversion_event': self.safe_choice([True, False], n_features, weights=[0.25, 0.75])
        })
        
        session_ids = datasets['feature_usage_events']['session_id'].unique().tolist()
        
        # Timeseries: user_sessions (2000 rows)
        n_sessions = 2000
        devices = ['Desktop', 'Mobile', 'Tablet']
        browsers = ['Chrome', 'Firefox', 'Safari', 'Edge']
        
        session_timestamps = pd.date_range(end=now, periods=n_sessions, freq='60s')
        
        datasets['user_sessions'] = pd.DataFrame({
            'session_id': self.safe_choice(session_ids, n_sessions, replace=False) if len(session_ids) >= n_sessions else [f'SES-{str(i+100000).zfill(7)}' for i in range(n_sessions)],
            '@timestamp': session_timestamps,
            'user_id': self.safe_choice(user_ids, n_sessions),
            'tenant_id': self.safe_choice(tenant_ids, n_sessions),
            'session_duration_ms': np.random.lognormal(12.5, 1.5, n_sessions),
            'page_views': np.random.poisson(8, n_sessions) + 1,
            'lcp_ms': np.random.lognormal(7.8, 0.6, n_sessions),
            'fid_ms': np.random.lognormal(3.5, 0.8, n_sessions),
            'bounce': self.safe_choice([True, False], n_sessions, weights=[0.15, 0.85]),
            'device_type': self.safe_choice(devices, n_sessions, weights=[0.65, 0.25, 0.10]),
            'browser': self.safe_choice(browsers, n_sessions, weights=[0.50, 0.20, 0.20, 0.10])
        })
        
        # Timeseries: webhook_deliveries (2000 rows)
        n_webhooks = 2000
        event_types = ['asset.created', 'asset.updated', 'asset.deleted', 'collection.shared',
                      'user.invited', 'metadata.changed', 'export.completed', 'tag.applied']
        
        webhook_timestamps = pd.date_range(end=now, periods=n_webhooks, freq='50s')
        webhook_statuses = self.safe_choice([200, 201, 400, 401, 404, 500, 502, 503, 504], n_webhooks, 
                                           weights=[0.75, 0.10, 0.03, 0.02, 0.02, 0.03, 0.02, 0.02, 0.01])
        
        datasets['webhook_deliveries'] = pd.DataFrame({
            'delivery_id': [f'WBH-{str(i+200000).zfill(8)}' for i in range(n_webhooks)],
            '@timestamp': webhook_timestamps,
            'partner_id': self.safe_choice(partner_ids, n_webhooks),
            'tenant_id': self.safe_choice(tenant_ids, n_webhooks),
            'event_type': self.safe_choice(event_types, n_webhooks),
            'http_status': webhook_statuses,
            'retry_count': np.where(webhook_statuses >= 500, np.random.poisson(1.5, n_webhooks), 
                                   np.where(webhook_statuses >= 400, np.random.poisson(0.3, n_webhooks), 0)),
            'delivery_latency_ms': np.where(webhook_statuses >= 500,
                                           np.random.lognormal(7.5, 1.0, n_webhooks),
                                           np.random.lognormal(5.8, 0.7, n_webhooks)),
            'success': webhook_statuses < 400
        })
        
        return datasets

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships from requirements"""
        return [
            ('api_requests', 'tenant_id', 'tenants'),
            ('api_requests', 'partner_id', 'api_partners'),
            ('feature_usage_events', 'tenant_id', 'tenants'),
            ('feature_usage_events', 'experiment_variant', 'ab_experiments'),
            ('user_sessions', 'tenant_id', 'tenants'),
            ('webhook_deliveries', 'partner_id', 'api_partners'),
            ('webhook_deliveries', 'tenant_id', 'tenants')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {
            'api_requests': 'API request logs tracking performance, errors, and usage across multi-tenant platform',
            'tenants': 'Enterprise customer accounts with SLA targets and renewal information',
            'api_partners': 'Third-party integration partners with health scores and contact details',
            'feature_usage_events': 'Granular feature interaction events for adoption analysis and A/B testing',
            'user_sessions': 'User session data with web vitals and engagement metrics',
            'ab_experiments': 'A/B test configurations with variants and target metrics',
            'webhook_deliveries': 'Webhook delivery attempts to partner systems with retry tracking'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        """Return fields that should use semantic_text mapping"""
        return {
            'api_requests': ['error_message'],
            'ab_experiments': ['experiment_hypothesis']
        }
