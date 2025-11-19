
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List

class ItaúUnibancoDataGenerator(DataGeneratorModule):
    """Data generator for Itaú Unibanco - Customer Experience"""

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
        
        # Reference data
        app_types = ['Web Banking', 'Mobile Banking', 'Investment Portal', 'Credit Card Portal', 'Loan Application']
        business_units = ['Retail Banking', 'Corporate Banking', 'Investment', 'Credit & Cards', 'Digital Channels']
        workflows = ['Login Flow', 'PIX Transfer', 'Investment Purchase', 'Account Opening', 'Loan Application', 
                    'Card Activation', 'Bill Payment', 'Statement Download', 'Profile Update', 'Support Request']
        
        regions = ['São Paulo', 'Rio de Janeiro', 'Brasília', 'Belo Horizonte', 'Porto Alegre', 'Salvador', 
                  'Curitiba', 'Fortaleza', 'Recife', 'Manaus']
        
        devices = ['desktop', 'mobile', 'tablet']
        browsers = ['Chrome', 'Safari', 'Firefox', 'Edge', 'Samsung Internet']
        connections = ['4g', '5g', 'wifi', '3g']
        
        page_urls = [
            '/login', '/dashboard', '/pix/transfer', '/pix/confirm', '/investments/portfolio',
            '/investments/buy', '/cards/list', '/cards/activate', '/loans/apply', '/loans/status',
            '/account/open', '/account/documents', '/bills/list', '/bills/pay', '/profile/edit'
        ]
        
        # application_catalog
        n_apps = 150
        app_ids = [f'app_{i:04d}' for i in range(n_apps)]
        
        datasets['application_catalog'] = pd.DataFrame({
            'application_id': app_ids,
            'application_name': [f'{self.safe_choice(app_types)} - {self.safe_choice(["Portal", "App", "Platform", "Service"])}' for _ in range(n_apps)],
            'business_unit': self.safe_choice(business_units, n_apps),
            'application_type': self.safe_choice(app_types, n_apps),
            'criticality': self.safe_choice(['critical', 'high', 'medium', 'low'], n_apps, weights=[0.2, 0.3, 0.3, 0.2]),
            'target_lcp_ms': self.safe_choice([2500, 3000, 3500, 4000], n_apps),
            'target_fid_ms': self.safe_choice([100, 150, 200], n_apps),
            'target_inp_ms': self.safe_choice([200, 300, 400], n_apps),
            'target_cls': self.safe_choice([0.1, 0.15, 0.2, 0.25], n_apps),
            'workflow_names': [','.join(random.sample(workflows, k=random.randint(2, 5))) for _ in range(n_apps)],
            'primary_user_segment': self.safe_choice(['retail', 'premium', 'corporate', 'youth', 'senior'], n_apps),
            'application_description': [
                f'Banking application for {self.safe_choice(["customer transactions", "account management", "investment services", "credit operations", "digital banking"])} with focus on {self.safe_choice(["security", "performance", "user experience", "accessibility"])}'
                for _ in range(n_apps)
            ],
            'performance_sla': [
                f'Target {self.safe_choice(["99.9%", "99.5%", "99%"])} availability with page load under {self.safe_choice(["3s", "4s", "5s"])} for {self.safe_choice(["90%", "95%", "99%"])} of users'
                for _ in range(n_apps)
            ]
        })
        
        # user_sessions
        n_sessions = 2500
        session_ids = [f'sess_{i:08d}' for i in range(n_sessions)]
        user_ids = [f'user_{i:06d}' for i in range(15000)]
        
        session_starts = pd.date_range(end=datetime.now(), periods=n_sessions, freq='15min')
        session_durations = np.random.exponential(scale=8, size=n_sessions).clip(0.5, 60)
        
        datasets['user_sessions'] = pd.DataFrame({
            'session_id': session_ids,
            'user_id': self.safe_choice(user_ids, n_sessions),
            'session_start': session_starts,
            'session_end': [session_starts[i] + timedelta(minutes=float(session_durations[i])) for i in range(n_sessions)],
            'session_duration_minutes': session_durations,
            'page_view_count': np.random.poisson(5, n_sessions).clip(1, 30),
            'interaction_count': np.random.poisson(12, n_sessions).clip(0, 100),
            'error_count': np.random.poisson(0.3, n_sessions).clip(0, 10),
            'workflow_completed': self.safe_choice([True, False], n_sessions, weights=[0.7, 0.3]),
            'workflow_name': self.safe_choice(workflows, n_sessions),
            'final_page_url': self.safe_choice(page_urls, n_sessions),
            'device_type': self.safe_choice(devices, n_sessions, weights=[0.4, 0.5, 0.1]),
            'browser': self.safe_choice(browsers, n_sessions, weights=[0.5, 0.25, 0.1, 0.1, 0.05]),
            'region': self.safe_choice(regions, n_sessions),
            'customer_segment': self.safe_choice(['retail', 'premium', 'corporate', 'youth', 'senior'], n_sessions, weights=[0.4, 0.2, 0.15, 0.15, 0.1]),
            'conversion_occurred': self.safe_choice([True, False], n_sessions, weights=[0.6, 0.4])
        })
        
        # backend_services
        n_backend = 5000
        service_names = ['auth-service', 'account-service', 'payment-service', 'investment-service', 
                        'card-service', 'loan-service', 'notification-service', 'fraud-detection', 
                        'customer-profile', 'transaction-history']
        operations = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        
        trace_ids_backend = [f'trace_{i:012d}' for i in range(n_backend)]
        
        datasets['backend_services'] = pd.DataFrame({
            'trace_id': trace_ids_backend,
            'span_id': [f'span_{i:012d}' for i in range(n_backend)],
            'parent_span_id': [f'span_{max(0, i-random.randint(1, 3)):012d}' if random.random() > 0.3 else '' for i in range(n_backend)],
            'service_name': self.safe_choice(service_names, n_backend),
            'service_type': self.safe_choice(['http', 'grpc', 'database', 'cache', 'queue'], n_backend, weights=[0.4, 0.2, 0.2, 0.1, 0.1]),
            'operation_name': [f'{self.safe_choice(operations)}_{self.safe_choice(["user", "account", "transaction", "payment", "transfer"])}' for _ in range(n_backend)],
            'duration_ms': np.random.lognormal(4, 1, n_backend).clip(5, 5000).astype(int),
            'http_status_code': self.safe_choice([200, 201, 204, 400, 401, 404, 500, 503], n_backend, weights=[0.75, 0.1, 0.05, 0.03, 0.02, 0.02, 0.02, 0.01]),
            'database_query_time_ms': np.random.lognormal(3, 1, n_backend).clip(0, 2000).astype(int),
            'external_api_time_ms': np.random.lognormal(3.5, 1, n_backend).clip(0, 3000).astype(int),
            'error_occurred': self.safe_choice([True, False], n_backend, weights=[0.05, 0.95]),
            'error_type': [self.safe_choice(['timeout', 'connection_error', 'validation_error', 'auth_error', '']) if random.random() < 0.05 else '' for _ in range(n_backend)],
            'service_tier': self.safe_choice(['tier1', 'tier2', 'tier3'], n_backend, weights=[0.3, 0.5, 0.2]),
            'database_name': self.safe_choice(['postgres_main', 'postgres_analytics', 'redis_cache', 'mongodb_sessions', 'mysql_legacy'], n_backend)
        })
        
        # rum_page_loads
        n_pages = 3000
        timestamps = pd.date_range(end=datetime.now(), periods=n_pages, freq='5min')
        
        datasets['rum_page_loads'] = pd.DataFrame({
            '@timestamp': timestamps,
            'session_id': self.safe_choice(session_ids, n_pages),
            'trace_id': self.safe_choice(trace_ids_backend, n_pages),
            'span_id': [f'span_page_{i:012d}' for i in range(n_pages)],
            'user_id': self.safe_choice(user_ids, n_pages),
            'page_url': self.safe_choice(page_urls, n_pages),
            'page_name': [url.replace('/', '_').strip('_') or 'home' for url in self.safe_choice(page_urls, n_pages)],
            'transaction_name': self.safe_choice(workflows, n_pages),
            'application_id': self.safe_choice(app_ids, n_pages),
            'device_type': self.safe_choice(devices, n_pages, weights=[0.4, 0.5, 0.1]),
            'browser': self.safe_choice(browsers, n_pages, weights=[0.5, 0.25, 0.1, 0.1, 0.05]),
            'region': self.safe_choice(regions, n_pages),
            'connection_type': self.safe_choice(connections, n_pages, weights=[0.3, 0.4, 0.25, 0.05]),
            'lcp_ms': np.random.lognormal(7.5, 0.5, n_pages).clip(500, 10000).astype(int),
            'fid_ms': np.random.lognormal(4, 0.8, n_pages).clip(10, 500).astype(int),
            'inp_ms': np.random.lognormal(5, 0.8, n_pages).clip(50, 1000).astype(int),
            'cls_score': np.random.lognormal(-2, 0.8, n_pages).clip(0, 1),
            'fcp_ms': np.random.lognormal(7, 0.5, n_pages).clip(300, 5000).astype(int),
            'ttfb_ms': np.random.lognormal(6, 0.6, n_pages).clip(100, 3000).astype(int),
            'tbt_ms': np.random.lognormal(5.5, 0.8, n_pages).clip(0, 2000).astype(int),
            'dns_time_ms': np.random.lognormal(3, 0.5, n_pages).clip(0, 200).astype(int),
            'tcp_time_ms': np.random.lognormal(4, 0.5, n_pages).clip(10, 500).astype(int),
            'request_time_ms': np.random.lognormal(3.5, 0.6, n_pages).clip(5, 300).astype(int),
            'response_time_ms': np.random.lognormal(5, 0.7, n_pages).clip(50, 2000).astype(int),
            'dom_processing_ms': np.random.lognormal(6, 0.6, n_pages).clip(100, 3000).astype(int),
            'load_event_ms': np.random.lognormal(5, 0.5, n_pages).clip(50, 1000).astype(int),
            'total_page_load_ms': np.random.lognormal(7.8, 0.5, n_pages).clip(800, 15000).astype(int),
            'error_count': np.random.poisson(0.2, n_pages).clip(0, 10),
            'long_task_count': np.random.poisson(1.5, n_pages).clip(0, 20),
            'failed_resource_count': np.random.poisson(0.3, n_pages).clip(0, 15),
            'navigation_type': self.safe_choice(['navigate', 'reload', 'back_forward', 'prerender'], n_pages, weights=[0.7, 0.15, 0.1, 0.05])
        })
        
        # rum_user_interactions
        n_interactions = 5000
        interaction_timestamps = pd.date_range(end=datetime.now(), periods=n_interactions, freq='2min')
        
        interaction_types = ['click', 'submit', 'input', 'scroll', 'hover', 'focus', 'blur']
        element_ids = ['btn_submit', 'btn_cancel', 'input_amount', 'input_account', 'select_type', 
                      'checkbox_terms', 'link_help', 'btn_confirm', 'input_password', 'btn_login']
        
        datasets['rum_user_interactions'] = pd.DataFrame({
            '@timestamp': interaction_timestamps,
            'session_id': self.safe_choice(session_ids, n_interactions),
            'trace_id': self.safe_choice(trace_ids_backend, n_interactions),
            'span_id': [f'span_int_{i:012d}' for i in range(n_interactions)],
            'user_id': self.safe_choice(user_ids, n_interactions),
            'interaction_type': self.safe_choice(interaction_types, n_interactions, weights=[0.4, 0.2, 0.15, 0.1, 0.05, 0.05, 0.05]),
            'element_id': self.safe_choice(element_ids, n_interactions),
            'element_text': [f'{self.safe_choice(["Confirmar", "Cancelar", "Enviar", "Voltar", "Próximo", "Salvar"])}' for _ in range(n_interactions)],
            'page_url': self.safe_choice(page_urls, n_interactions),
            'application_id': self.safe_choice(app_ids, n_interactions),
            'workflow_name': self.safe_choice(workflows, n_interactions),
            'workflow_step': [f'step_{random.randint(1, 5)}' for _ in range(n_interactions)],
            'interaction_duration_ms': np.random.lognormal(5, 1, n_interactions).clip(10, 5000).astype(int),
            'resulted_in_error': self.safe_choice([True, False], n_interactions, weights=[0.05, 0.95]),
            'error_message': [self.safe_choice(['Validation failed', 'Network error', 'Timeout', 'Invalid input', '']) if random.random() < 0.05 else '' for _ in range(n_interactions)],
            'device_type': self.safe_choice(devices, n_interactions, weights=[0.4, 0.5, 0.1]),
            'region': self.safe_choice(regions, n_interactions)
        })
        
        # rum_resource_timing
        n_resources = 5000
        resource_timestamps = pd.date_range(end=datetime.now(), periods=n_resources, freq='90s')
        
        resource_types = ['script', 'stylesheet', 'image', 'font', 'fetch', 'xmlhttprequest', 'other']
        cdn_providers = ['Cloudflare', 'Akamai', 'AWS CloudFront', 'Fastly', 'origin']
        
        datasets['rum_resource_timing'] = pd.DataFrame({
            '@timestamp': resource_timestamps,
            'session_id': self.safe_choice(session_ids, n_resources),
            'trace_id': self.safe_choice(trace_ids_backend, n_resources),
            'page_url': self.safe_choice(page_urls, n_resources),
            'resource_url': [f'https://cdn.itau.com.br/{self.safe_choice(["js", "css", "img", "fonts"])}/{random.randint(1, 100)}.{self.safe_choice(["js", "css", "png", "woff2"])}' for _ in range(n_resources)],
            'resource_type': self.safe_choice(resource_types, n_resources, weights=[0.25, 0.15, 0.3, 0.1, 0.1, 0.05, 0.05]),
            'resource_name': [f'resource_{i}.{self.safe_choice(["js", "css", "png", "jpg", "woff2"])}' for i in range(n_resources)],
            'initiator_type': self.safe_choice(['script', 'link', 'img', 'css', 'fetch'], n_resources),
            'duration_ms': np.random.lognormal(5, 1, n_resources).clip(5, 5000).astype(int),
            'transfer_size_bytes': np.random.lognormal(10, 2, n_resources).clip(100, 5000000).astype(int),
            'encoded_body_size_bytes': np.random.lognormal(10, 2, n_resources).clip(100, 5000000).astype(int),
            'decoded_body_size_bytes': np.random.lognormal(10.5, 2, n_resources).clip(100, 6000000).astype(int),
            'dns_time_ms': np.random.lognormal(2, 0.5, n_resources).clip(0, 100).astype(int),
            'tcp_time_ms': np.random.lognormal(3, 0.5, n_resources).clip(0, 200).astype(int),
            'ttfb_ms': np.random.lognormal(4, 0.7, n_resources).clip(5, 1000).astype(int),
            'download_time_ms': np.random.lognormal(4.5, 0.8, n_resources).clip(5, 2000).astype(int),
            'http_status': self.safe_choice([200, 304, 404, 500], n_resources, weights=[0.85, 0.1, 0.03, 0.02]),
            'is_cached': self.safe_choice([True, False], n_resources, weights=[0.4, 0.6]),
            'cdn_provider': self.safe_choice(cdn_providers, n_resources, weights=[0.3, 0.25, 0.25, 0.1, 0.1]),
            'application_id': self.safe_choice(app_ids, n_resources)
        })
        
        return datasets

    def get_relationships(self) -> List[tuple]:
        return [
            ('rum_page_loads', 'application_id', 'application_catalog'),
            ('rum_page_loads', 'trace_id', 'backend_services'),
            ('rum_page_loads', 'session_id', 'user_sessions'),
            ('rum_user_interactions', 'application_id', 'application_catalog'),
            ('rum_user_interactions', 'session_id', 'user_sessions'),
            ('rum_user_interactions', 'trace_id', 'backend_services'),
            ('rum_resource_timing', 'application_id', 'application_catalog'),
            ('rum_resource_timing', 'session_id', 'user_sessions'),
            ('rum_resource_timing', 'trace_id', 'backend_services')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        return {
            'rum_page_loads': 'Real User Monitoring page load events with Core Web Vitals and navigation timing breakdown',
            'rum_user_interactions': 'User interactions including clicks, form submissions, and custom workflow actions',
            'rum_resource_timing': 'Resource timing data for scripts, stylesheets, images, and API calls',
            'backend_services': 'Backend service traces with distributed tracing spans and performance metrics',
            'application_catalog': 'Application metadata with performance targets and business context',
            'user_sessions': 'Aggregated user session data with conversion and workflow completion status'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        return {
            'application_catalog': ['application_description', 'performance_sla']
        }
