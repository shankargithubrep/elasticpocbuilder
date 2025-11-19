
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List

class AdobeIncDataGenerator(DataGeneratorModule):
    """Data generator for Adobe Inc. - Brand Concierge AI/ML & Product Engineering"""

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
        n_customers = 200
        customer_ids = [f"CUST{str(i+1).zfill(6)}" for i in range(n_customers)]
        
        companies = ["Acme Corp", "Global Brands Inc", "TechStart", "Retail Giant", "Fashion House", 
                    "MediaCo", "Finance Plus", "Healthcare Systems", "Education First", "Manufacturing Co"]
        industries = ["Retail", "Technology", "Finance", "Healthcare", "Manufacturing", "Media", "Education"]
        tiers = ["Enterprise", "Professional", "Standard"]
        
        datasets['customer_accounts'] = pd.DataFrame({
            'customer_account_id': customer_ids,
            'company_name': [f"{self.safe_choice(companies)} {i+1}" for i in range(n_customers)],
            'industry': self.safe_choice(industries, n_customers),
            'tier': self.safe_choice(tiers, n_customers, weights=[0.3, 0.5, 0.2]),
            'active_users': np.random.randint(50, 5000, n_customers),
            'total_assets': np.random.randint(1000, 200000, n_customers),
            'contract_start_date': pd.date_range(end=datetime.now(), periods=n_customers, freq='-30D')
        })

        # Brand assets
        n_assets = 3000
        asset_types = ["image", "video", "document", "logo", "template", "audio"]
        file_formats = ["jpg", "png", "mp4", "pdf", "svg", "psd", "ai", "mp3"]
        approval_statuses = ["approved", "pending", "rejected", "draft"]
        categories = ["marketing", "product", "social", "internal", "campaign", "brand_guidelines"]
        
        asset_names = ["Brand Logo", "Product Shot", "Campaign Banner", "Social Post", "Marketing Template",
                      "Video Ad", "Product Demo", "Brand Guidelines", "Event Poster", "Email Header"]
        
        asset_descriptions = [
            "High-resolution brand logo for digital and print use with transparent background",
            "Professional product photography showcasing key features and benefits",
            "Eye-catching campaign banner optimized for web and mobile platforms",
            "Engaging social media content designed for maximum audience engagement",
            "Customizable marketing template with brand colors and typography",
            "Dynamic video advertisement highlighting product value proposition",
            "Comprehensive product demonstration video with detailed feature walkthrough",
            "Complete brand identity guidelines including logos, colors, and usage rules",
            "Event promotional poster with compelling visuals and clear call-to-action",
            "Email header design optimized for various email clients and devices"
        ]
        
        now = datetime.now()
        start_date = now - timedelta(days=120)
        
        datasets['brand_assets'] = pd.DataFrame({
            'asset_id': [f"ASSET{str(i+1).zfill(8)}" for i in range(n_assets)],
            'asset_name': [f"{self.safe_choice(asset_names)} {i+1}" for i in range(n_assets)],
            'asset_description': self.safe_choice(asset_descriptions, n_assets),
            'asset_type': self.safe_choice(asset_types, n_assets),
            'brand_name': [f"Brand {self.safe_choice(['Alpha', 'Beta', 'Gamma', 'Delta', 'Omega'])}" for _ in range(n_assets)],
            'customer_account_id': self.safe_choice(customer_ids, n_assets),
            'tags': [','.join(self.safe_choice(['marketing', 'product', 'social', 'campaign', 'brand', 'digital'], 
                                               np.random.randint(1, 4), replace=False)) for _ in range(n_assets)],
            'file_format': self.safe_choice(file_formats, n_assets),
            'created_date': [self.random_timedelta(start_date, now) for _ in range(n_assets)],
            'last_modified': [self.random_timedelta(start_date, now) for _ in range(n_assets)],
            'usage_count': np.random.randint(0, 500, n_assets),
            'approval_status': self.safe_choice(approval_statuses, n_assets, weights=[0.6, 0.2, 0.1, 0.1]),
            'content_category': self.safe_choice(categories, n_assets)
        })

        # Query templates
        n_templates = 40
        use_cases = ["semantic_search", "keyword_search", "hybrid_search", "filtered_search", 
                    "multi_field_search", "fuzzy_search", "aggregation_query"]
        performance_ratings = ["excellent", "good", "fair", "poor"]
        
        datasets['query_templates'] = pd.DataFrame({
            'template_id': [f"TMPL{str(i+1).zfill(3)}" for i in range(n_templates)],
            'template_name': [f"{self.safe_choice(use_cases)} Template {i+1}" for i in range(n_templates)],
            'query_dsl': [f'{{"query": {{"match": {{"field": "value{i}"}}}}}}' for i in range(n_templates)],
            'use_case': self.safe_choice(use_cases, n_templates),
            'last_updated': pd.date_range(end=now, periods=n_templates, freq='-7D'),
            'maintenance_hours': np.random.uniform(0.5, 8.0, n_templates).round(1),
            'complexity_score': np.random.randint(1, 11, n_templates),
            'performance_rating': self.safe_choice(performance_ratings, n_templates, weights=[0.2, 0.4, 0.3, 0.1]),
            'deprecated': self.safe_choice([True, False], n_templates, weights=[0.15, 0.85])
        })

        # AI assistant conversations
        n_convos = 2500
        conversation_ids = [f"CONV{str(i+1).zfill(8)}" for i in range(n_convos)]
        user_ids = [f"USER{str(i+1).zfill(6)}" for i in range(500)]
        
        queries = [
            "Find all approved marketing assets for our spring campaign",
            "Show me recent product images with high engagement",
            "What brand guidelines exist for social media posts",
            "Search for video content related to product launches",
            "Find templates used in email campaigns last month",
            "Show approved logos in SVG format",
            "What assets are pending approval for the finance team",
            "Find high-resolution images for print materials",
            "Search for campaign assets tagged with digital",
            "Show me all assets created in the last week"
        ]
        
        strategies = ["semantic", "keyword", "hybrid", "filtered", "multi_step", "composed"]
        quality_ratings = ["excellent", "good", "fair", "poor"]
        
        datasets['ai_assistant_conversations'] = pd.DataFrame({
            'conversation_id': conversation_ids,
            'user_id': self.safe_choice(user_ids, n_convos),
            'customer_account_id': self.safe_choice(customer_ids, n_convos),
            'query_text': self.safe_choice(queries, n_convos),
            'response_text': [f"Found {np.random.randint(1, 50)} relevant assets matching your criteria" for _ in range(n_convos)],
            'retrieved_documents': [','.join([f"ASSET{str(j).zfill(8)}" for j in np.random.randint(1, 3000, np.random.randint(1, 11))]) for _ in range(n_convos)],
            'retrieval_strategy': self.safe_choice(strategies, n_convos),
            'conversation_turn': np.random.randint(1, 6, n_convos),
            'quality_rating': self.safe_choice(quality_ratings, n_convos, weights=[0.25, 0.44, 0.2, 0.11]),
            'helpful': self.safe_choice([True, False], n_convos, weights=[0.69, 0.31]),
            'clarification_needed': self.safe_choice([True, False], n_convos, weights=[0.42, 0.58]),
            'retrieval_latency_ms': np.random.randint(50, 2000, n_convos),
            'timestamp': pd.date_range(end=now, periods=n_convos, freq='15T'),
            'context_from_previous_turn': [f"Previous query context {i}" if i % 3 == 0 else "" for i in range(n_convos)]
        })

        # Retrieval experiments
        n_experiments = 1500
        embedding_models = ["text-embedding-ada-002", "all-MiniLM-L6-v2", "bge-large-en", 
                           "e5-large-v2", "instructor-xl", "gte-large"]
        
        test_queries = [
            "Find marketing assets for Q4 campaign with high engagement metrics",
            "Search for brand-compliant social media templates",
            "Locate product demonstration videos from last quarter",
            "Find approved logos suitable for digital and print use",
            "Search for campaign assets tagged with sustainability"
        ]
        
        datasets['retrieval_experiments'] = pd.DataFrame({
            'experiment_id': [f"EXP{str(i+1).zfill(6)}" for i in range(n_experiments)],
            'experiment_name': [f"Experiment {i+1} - {self.safe_choice(strategies)}" for i in range(n_experiments)],
            'retrieval_strategy': self.safe_choice(strategies, n_experiments),
            'embedding_model': self.safe_choice(embedding_models, n_experiments),
            'query_template': [f"Template {self.safe_choice(range(1, 41))}" for _ in range(n_experiments)],
            'test_query': self.safe_choice(test_queries, n_experiments),
            'precision_at_5': np.random.uniform(0.3, 0.95, n_experiments).round(3),
            'recall_at_10': np.random.uniform(0.4, 0.9, n_experiments).round(3),
            'mrr_score': np.random.uniform(0.5, 0.98, n_experiments).round(3),
            'latency_ms': np.random.randint(100, 3000, n_experiments),
            'experiment_date': pd.date_range(end=now, periods=n_experiments, freq='1H'),
            'engineer_notes': [f"Testing {self.safe_choice(['performance', 'accuracy', 'latency', 'relevance'])} improvements" for _ in range(n_experiments)],
            'deployed_to_production': self.safe_choice([True, False], n_experiments, weights=[0.25, 0.75])
        })

        # Retrieval quality incidents
        n_incidents = 1000
        failure_reasons = ["poor_relevance", "missing_context", "wrong_filter", "timeout", 
                          "empty_results", "incorrect_ranking", "embedding_mismatch"]
        
        datasets['retrieval_quality_incidents'] = pd.DataFrame({
            'incident_id': [f"INC{str(i+1).zfill(6)}" for i in range(n_incidents)],
            'conversation_id': self.safe_choice(conversation_ids, n_incidents),
            'user_query': self.safe_choice(queries, n_incidents),
            'retrieved_doc_ids': [','.join([f"ASSET{str(j).zfill(8)}" for j in np.random.randint(1, 3000, np.random.randint(1, 6))]) for _ in range(n_incidents)],
            'expected_doc_ids': [','.join([f"ASSET{str(j).zfill(8)}" for j in np.random.randint(1, 3000, np.random.randint(1, 6))]) for _ in range(n_incidents)],
            'failure_reason': self.safe_choice(failure_reasons, n_incidents),
            'debug_time_minutes': np.random.randint(15, 90, n_incidents),
            'resolution_notes': [f"Resolved by adjusting {self.safe_choice(['query', 'filters', 'embedding', 'ranking'])}" for _ in range(n_incidents)],
            'incident_date': pd.date_range(end=now, periods=n_incidents, freq='2H'),
            'resolved': self.safe_choice([True, False], n_incidents, weights=[0.8, 0.2])
        })

        return datasets

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships from requirements"""
        return [
            ('brand_assets', 'customer_account_id', 'customer_accounts'),
            ('ai_assistant_conversations', 'customer_account_id', 'customer_accounts'),
            ('retrieval_quality_incidents', 'conversation_id', 'ai_assistant_conversations')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {
            'customer_accounts': 'Enterprise customer accounts using Adobe Brand Concierge',
            'brand_assets': 'Digital brand assets including images, videos, and documents',
            'query_templates': 'Query DSL templates for different retrieval use cases',
            'ai_assistant_conversations': 'AI assistant conversation logs with retrieval metrics',
            'retrieval_experiments': 'A/B testing experiments for retrieval strategy optimization',
            'retrieval_quality_incidents': 'Incidents where retrieval quality was poor requiring debugging'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        """Return fields that should use semantic_text mapping"""
        return {
            'brand_assets': ['asset_description'],
            'ai_assistant_conversations': ['query_text'],
            'retrieval_experiments': ['test_query'],
            'retrieval_quality_incidents': ['user_query']
        }
