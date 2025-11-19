
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

class UnitedHealthGroupDataGenerator(DataGeneratorModule):
    """Data generator for UnitedHealth Group - Callcenter Operations"""

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
        start_date = now - timedelta(days=120)

        # Agents (120 agents)
        agent_ids = [f"AGT{str(i).zfill(5)}" for i in range(1, 121)]
        teams = ['Claims', 'Authorization', 'Benefits', 'Provider Network', 'General Support']
        specializations = ['Prior Auth', 'Claims Denials', 'Benefits Verification', 'Provider Search', 'General Inquiry', 'ID Cards']
        
        datasets['agents'] = pd.DataFrame({
            'agent_id': agent_ids,
            'agent_name': [f"{np.random.choice(['John', 'Jane', 'Michael', 'Sarah', 'David', 'Lisa', 'Robert', 'Emily', 'James', 'Maria'])} {np.random.choice(['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez'])}" for _ in agent_ids],
            'team': self.safe_choice(teams, size=len(agent_ids)),
            'hire_date': [self.random_timedelta(now - timedelta(days=1825), now - timedelta(days=30)) for _ in agent_ids],
            'specialization': self.safe_choice(specializations, size=len(agent_ids)),
            'efficiency_rating': np.random.uniform(3.5, 5.0, len(agent_ids))
        })

        # Member Plans (500 members)
        member_ids = [f"MBR{str(i).zfill(8)}" for i in range(1, 501)]
        plan_types = ['HMO', 'PPO', 'EPO', 'POS', 'HDHP']
        plan_names = ['HealthGuard Plus', 'Premium Care', 'Essential Coverage', 'Choice Network', 'ValueHealth', 'FlexCare', 'SecureHealth']
        coverage_tiers = ['Individual', 'Individual + Spouse', 'Individual + Children', 'Family']
        eligibility_statuses = ['Active', 'Active', 'Active', 'Active', 'Active', 'Pending', 'Suspended']
        
        datasets['member_plans'] = pd.DataFrame({
            'member_id': member_ids,
            'plan_type': self.safe_choice(plan_types, size=len(member_ids)),
            'plan_name': self.safe_choice(plan_names, size=len(member_ids)),
            'coverage_tier': self.safe_choice(coverage_tiers, size=len(member_ids)),
            'eligibility_status': self.safe_choice(eligibility_statuses, size=len(member_ids)),
            'effective_date': [self.random_timedelta(now - timedelta(days=730), now - timedelta(days=1)) for _ in member_ids],
            'deductible_remaining': np.random.uniform(0, 5000, len(member_ids)),
            'out_of_pocket_max': self.safe_choice([3000, 5000, 6500, 8000, 10000], size=len(member_ids))
        })

        # Provider Network (200 providers)
        provider_ids = [f"PRV{str(i).zfill(6)}" for i in range(1, 201)]
        specialties = ['Primary Care', 'Cardiology', 'Orthopedics', 'Dermatology', 'Pediatrics', 'Internal Medicine', 'Endocrinology', 'Oncology', 'Psychiatry', 'Neurology']
        network_statuses = ['In-Network', 'In-Network', 'In-Network', 'Out-of-Network', 'Pending Verification']
        cities = ['Minneapolis', 'Chicago', 'Phoenix', 'Atlanta', 'Dallas', 'Seattle', 'Boston', 'Denver']
        
        datasets['provider_network'] = pd.DataFrame({
            'provider_id': provider_ids,
            'provider_name': [f"Dr. {np.random.choice(['James', 'Sarah', 'Michael', 'Jennifer', 'Robert', 'Linda', 'William', 'Patricia'])} {np.random.choice(['Anderson', 'Thomas', 'Jackson', 'White', 'Harris', 'Martin', 'Thompson', 'Garcia'])} MD" for _ in provider_ids],
            'specialty': self.safe_choice(specialties, size=len(provider_ids)),
            'network_status': self.safe_choice(network_statuses, size=len(provider_ids)),
            'last_verified_date': [self.random_timedelta(now - timedelta(days=180), now) for _ in provider_ids],
            'accepting_patients': self.safe_choice([True, False], size=len(provider_ids), weights=[0.7, 0.3]),
            'address': [f"{np.random.randint(100, 9999)} {np.random.choice(['Main', 'Oak', 'Maple', 'Park', 'Cedar'])} St, {np.random.choice(cities)}, MN {np.random.randint(55000, 55999)}" for _ in provider_ids],
            'phone': [f"({np.random.randint(200, 999)}) {np.random.randint(200, 999)}-{np.random.randint(1000, 9999)}" for _ in provider_ids]
        })

        # Prior Authorizations (300 prior auths)
        prior_auth_ids = [f"PA{str(i).zfill(7)}" for i in range(1, 301)]
        medications = ['Humira', 'Enbrel', 'Lyrica', 'Eliquis', 'Xarelto', 'Januvia', 'Lantus', 'Symbicort', 'Advair', 'Spiriva', 'Trulicity', 'Ozempic']
        pa_statuses = ['Approved', 'Pending', 'Pending', 'Denied', 'Under Review', 'Additional Info Required']
        
        datasets['prior_authorizations'] = pd.DataFrame({
            'prior_auth_id': prior_auth_ids,
            'member_id': self.safe_choice(member_ids, size=len(prior_auth_ids)),
            'medication_name': self.safe_choice(medications, size=len(prior_auth_ids)),
            'status': self.safe_choice(pa_statuses, size=len(prior_auth_ids)),
            'submission_date': [self.random_timedelta(now - timedelta(days=60), now) for _ in prior_auth_ids],
            'days_pending': np.random.randint(0, 45, len(prior_auth_ids)),
            'provider_id': self.safe_choice(provider_ids, size=len(prior_auth_ids)),
            'urgency_flag': self.safe_choice([True, False], size=len(prior_auth_ids), weights=[0.3, 0.7])
        })

        # Claims Denials (80 denial codes)
        denial_codes = [f"D{str(i).zfill(3)}" for i in range(1, 81)]
        categories = ['Medical Necessity', 'Coding Error', 'Non-Covered Service', 'Authorization Required', 'Timely Filing', 'Duplicate Claim']
        
        denial_reasons = [
            'Service not medically necessary per clinical guidelines',
            'Incorrect procedure code submitted',
            'Service not covered under member plan',
            'Prior authorization required but not obtained',
            'Claim submitted beyond timely filing limit',
            'Duplicate claim already processed',
            'Out-of-network provider without authorization',
            'Missing required documentation',
            'Coordination of benefits issue',
            'Plan exclusion applies'
        ]
        
        resolutions = [
            'Submit clinical documentation supporting medical necessity',
            'Resubmit with correct CPT/ICD-10 codes',
            'Appeal with policy exception request',
            'Obtain retroactive prior authorization',
            'Contact provider for corrected claim',
            'No action needed - original claim paid',
            'Submit gap exception request',
            'Provide itemized bill and medical records',
            'Update COB information with primary carrier',
            'Review plan documents with member'
        ]
        
        datasets['claims_denials'] = pd.DataFrame({
            'denial_code': denial_codes,
            'denial_reason': self.safe_choice(denial_reasons, size=len(denial_codes)),
            'common_resolution': self.safe_choice(resolutions, size=len(denial_codes)),
            'appeal_success_rate': np.random.uniform(0.15, 0.85, len(denial_codes)),
            'category': self.safe_choice(categories, size=len(denial_codes))
        })

        # Insurance Knowledge Base (150 articles)
        article_ids = [f"KB{str(i).zfill(5)}" for i in range(1, 151)]
        kb_categories = ['Benefits', 'Claims', 'Prior Authorization', 'Provider Network', 'Coverage', 'Appeals', 'Billing']
        
        titles = [
            'Understanding Your Deductible and Out-of-Pocket Maximum',
            'How to Find In-Network Providers',
            'Prior Authorization Process for Specialty Medications',
            'What to Do When a Claim is Denied',
            'Coordination of Benefits Explained',
            'HMO vs PPO: Understanding Your Plan Type',
            'How to Appeal a Denied Claim',
            'Emergency Room Coverage and Copays',
            'Preventive Care Services Covered at 100%',
            'Understanding Medical Necessity Requirements'
        ]
        
        content_templates = [
            'This article explains the key concepts of {} and how it impacts your coverage. Members should understand that {}. For questions, contact member services.',
            'Important information about {} for all plan members. Please note that {} and follow the guidelines provided.',
            'Step-by-step guide to {}. This process involves {} and typically takes 3-5 business days.',
            'Common questions about {} answered. Members frequently ask about {} and here are the details.'
        ]
        
        datasets['insurance_knowledge_base'] = pd.DataFrame({
            'article_id': article_ids,
            'title': self.safe_choice(titles, size=len(article_ids)),
            'content': [np.random.choice(content_templates).format('insurance benefits', 'coverage varies by plan') for _ in article_ids],
            'category': self.safe_choice(kb_categories, size=len(article_ids)),
            'topic_tags': self.safe_choice(['deductible', 'copay', 'authorization', 'network', 'claims', 'eligibility', 'appeals'], size=len(article_ids)),
            'last_updated': [self.random_timedelta(now - timedelta(days=365), now) for _ in article_ids],
            'view_count': np.random.randint(50, 5000, len(article_ids))
        })

        # Call Center Transactions (2500 transactions)
        n_transactions = 2500
        timestamps = pd.date_range(end=now, periods=n_transactions, freq='17min')
        
        call_types = ['Prior Authorization', 'Benefits Verification', 'Claims Inquiry', 'Provider Search', 'ID Card Request', 'Coverage Question', 'Claim Denial']
        resolution_statuses = ['Resolved', 'Resolved', 'Resolved', 'Escalated', 'Pending Follow-up', 'Transferred']
        
        call_notes_templates = [
            'Member called regarding prior authorization status for {}. Verified eligibility and confirmed {} is pending review. Expected decision in 2-3 business days.',
            'Benefits verification for upcoming procedure. Member has {} plan with ${} deductible remaining. Confirmed in-network provider.',
            'Claim inquiry for DOS {}. Claim status is {}. Explained processing timeline and next steps to member.',
            'Provider network search for {} in {} area. Provided list of 5 in-network providers accepting new patients.',
            'Member requested replacement ID card. Verified identity through security questions. Card will arrive in 7-10 business days.',
            'Coverage question regarding {}. Reviewed plan documents and explained benefit limitations and member responsibility.',
            'Claim denial code {} - {}. Explained reason for denial and appeal process. Member will submit additional documentation.'
        ]
        
        transaction_ids = [f"TXN{str(i).zfill(9)}" for i in range(1, n_transactions + 1)]
        selected_agents = self.safe_choice(agent_ids, size=n_transactions)
        selected_members = self.safe_choice(member_ids, size=n_transactions)
        selected_call_types = self.safe_choice(call_types, size=n_transactions, weights=[0.2, 0.2, 0.25, 0.15, 0.05, 0.1, 0.05])
        
        denial_codes_with_null = list(denial_codes) + [None] * 200
        prior_auth_ids_with_null = list(prior_auth_ids) + [None] * 500
        
        datasets['call_center_transactions'] = pd.DataFrame({
            'transaction_id': transaction_ids,
            '@timestamp': timestamps,
            'agent_id': selected_agents,
            'member_id': selected_members,
            'call_type': selected_call_types,
            'call_duration_seconds': np.random.randint(120, 1800, n_transactions),
            'resolution_status': self.safe_choice(resolution_statuses, size=n_transactions, weights=[0.6, 0.15, 0.1, 0.1, 0.03, 0.02]),
            'verification_steps_count': np.random.randint(2, 6, n_transactions),
            'processing_time_seconds': np.random.randint(60, 900, n_transactions),
            'transaction_cost': np.random.uniform(5.50, 45.00, n_transactions),
            'call_notes': [np.random.choice(call_notes_templates).format('Humira', 'authorization', '01/15/2024', 'processed', 'cardiology', 'Minneapolis', 'D045', 'prior authorization not obtained') for _ in range(n_transactions)],
            'denial_code': self.safe_choice(denial_codes_with_null, size=n_transactions),
            'prior_auth_id': self.safe_choice(prior_auth_ids_with_null, size=n_transactions)
        })

        return datasets

    def get_relationships(self) -> List[tuple]:
        return [
            ('call_center_transactions', 'agent_id', 'agents'),
            ('call_center_transactions', 'member_id', 'member_plans'),
            ('call_center_transactions', 'prior_auth_id', 'prior_authorizations'),
            ('call_center_transactions', 'denial_code', 'claims_denials'),
            ('prior_authorizations', 'member_id', 'member_plans'),
            ('prior_authorizations', 'provider_id', 'provider_network')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        return {
            'call_center_transactions': 'Call center transaction records including call type, duration, resolution status, and associated member/agent data',
            'agents': 'Call center agent information including team assignment, specialization, and performance ratings',
            'member_plans': 'Member insurance plan details including coverage type, eligibility, and financial information',
            'prior_authorizations': 'Prior authorization requests for medications and procedures with status tracking',
            'provider_network': 'Healthcare provider directory with network status and verification dates',
            'claims_denials': 'Denial code reference with reasons and resolution guidance',
            'insurance_knowledge_base': 'Knowledge base articles for common insurance questions and processes'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        return {
            'call_center_transactions': ['call_notes'],
            'insurance_knowledge_base': ['title', 'content'],
            'claims_denials': ['denial_reason', 'common_resolution']
        }
