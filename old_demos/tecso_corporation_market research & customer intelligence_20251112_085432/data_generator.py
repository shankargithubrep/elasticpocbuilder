
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List

class TecsoCorporationDataGenerator(DataGeneratorModule):
    """Data generator for Tecso Corporation - Market Research & Customer Intelligence"""

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
        """Generate datasets with EXACT fields from requirements"""
        datasets = {}
        
        # RFM segments with realistic distribution
        rfm_segments = ['Champions', 'Loyal Customers', 'Potential Loyalists', 'New Customers', 
                        'Promising', 'Need Attention', 'About to Sleep', 'At Risk', 'Cannot Lose Them', 'Hibernating']
        rfm_weights = [0.10, 0.15, 0.12, 0.08, 0.10, 0.12, 0.08, 0.10, 0.08, 0.07]
        
        channels = ['e-commerce', 'in-store']
        payment_methods = ['credit_card', 'debit_card', 'cash', 'digital_wallet', 'buy_now_pay_later']
        
        store_locations = ['Downtown', 'Westside Mall', 'North Plaza', 'South Center', 'East Market', 
                          'Suburban Center', 'Airport', 'Riverside', 'Uptown', 'Metro Station']
        
        categories = ['Electronics', 'Clothing', 'Home & Garden', 'Beauty & Health', 'Sports & Outdoors', 
                     'Toys & Games', 'Books & Media', 'Food & Beverage', 'Automotive', 'Pet Supplies']
        
        subcategories = {
            'Electronics': ['Smartphones', 'Laptops', 'Tablets', 'Accessories', 'Audio'],
            'Clothing': ['Mens', 'Womens', 'Kids', 'Shoes', 'Accessories'],
            'Home & Garden': ['Furniture', 'Decor', 'Kitchen', 'Bedding', 'Garden Tools'],
            'Beauty & Health': ['Skincare', 'Makeup', 'Haircare', 'Supplements', 'Personal Care'],
            'Sports & Outdoors': ['Fitness', 'Camping', 'Cycling', 'Team Sports', 'Water Sports']
        }
        
        campaign_types = ['Email', 'Social Media', 'Display Ads', 'SMS', 'Direct Mail', 'In-Store Promotion']
        
        behavior_templates = [
            "High-value {channel} shopper with preference for {category}. Responds well to {campaign_type} campaigns. Average basket size ${avg_basket}.",
            "Multi-channel customer ({channel_mix}% online) focusing on {category} and {category2}. Price-sensitive with seasonal purchasing patterns.",
            "Loyal {channel} customer with consistent monthly purchases. Prefers {payment} payment. Strong brand affinity in {category} category.",
            "Emerging customer with growing purchase frequency. Primary interest in {category}. High potential for loyalty program engagement.",
            "At-risk profile showing declining engagement. Historical focus on {category}. Requires targeted retention campaigns."
        ]
        
        product_desc_templates = [
            "Premium {subcategory} product featuring advanced technology and superior quality. Ideal for discerning customers seeking reliability.",
            "Best-selling {subcategory} item with excellent customer reviews. Great value for everyday use with durable construction.",
            "Innovative {subcategory} solution designed for modern lifestyles. Combines functionality with contemporary design.",
            "Eco-friendly {subcategory} product made from sustainable materials. Perfect for environmentally conscious consumers.",
            "Professional-grade {subcategory} offering exceptional performance. Trusted by experts and enthusiasts alike."
        ]

        # Generate products (10000+ required, using 150 for SMALL)
        n_products = 150
        product_cats = self.safe_choice(categories, n_products)
        product_subcats = []
        for cat in product_cats:
            if cat in subcategories:
                product_subcats.append(self.safe_choice(subcategories[cat]))
            else:
                product_subcats.append(self.safe_choice(['Standard', 'Premium', 'Basic', 'Deluxe']))
        
        products_data = {
            'product_id': [f'PROD{str(i).zfill(6)}' for i in range(1, n_products + 1)],
            'product_name': [f'{product_subcats[i]} {product_cats[i]} Item {i}' for i in range(n_products)],
            'product_category': product_cats,
            'product_subcategory': product_subcats,
            'unit_price': np.round(np.random.lognormal(3.5, 1.0, n_products), 2),
            'margin_percentage': np.round(np.random.uniform(15, 45, n_products), 1)
        }
        products_data['product_description'] = [
            random.choice(product_desc_templates).format(subcategory=products_data['product_subcategory'][i])
            for i in range(n_products)
        ]
        datasets['products'] = pd.DataFrame(products_data)

        # Generate campaigns (500+ required, using 80 for SMALL)
        n_campaigns = 80
        now = datetime.now()
        campaign_starts = [now - timedelta(days=int(d)) for d in np.random.uniform(5, 90, n_campaigns)]
        
        datasets['campaigns'] = pd.DataFrame({
            'campaign_id': [f'CAMP{str(i).zfill(4)}' for i in range(1, n_campaigns + 1)],
            'campaign_name': [f'{self.safe_choice(campaign_types)} Campaign {i}' for i in range(1, n_campaigns + 1)],
            'campaign_type': self.safe_choice(campaign_types, n_campaigns),
            'target_segment': self.safe_choice(rfm_segments, n_campaigns),
            'campaign_budget': np.round(np.random.uniform(5000, 100000, n_campaigns), 2),
            'campaign_start_date': campaign_starts,
            'campaign_end_date': [campaign_starts[i] + timedelta(days=int(d)) for i, d in enumerate(np.random.uniform(7, 45, n_campaigns))]
        })

        # Generate customers (50000+ required, using 200 for SMALL)
        n_customers = 200
        cust_segments = self.safe_choice(rfm_segments, n_customers, weights=rfm_weights)
        
        recency_scores = []
        frequency_scores = []
        monetary_scores = []
        churn_probs = []
        
        for seg in cust_segments:
            if seg in ['Champions', 'Loyal Customers']:
                recency_scores.append(self.safe_choice([4, 5]))
                frequency_scores.append(self.safe_choice([4, 5]))
                monetary_scores.append(self.safe_choice([4, 5]))
                churn_probs.append(np.random.uniform(0.01, 0.10))
            elif seg in ['At Risk', 'Cannot Lose Them', 'Hibernating']:
                recency_scores.append(self.safe_choice([1, 2]))
                frequency_scores.append(self.safe_choice([1, 2, 3]))
                monetary_scores.append(self.safe_choice([2, 3, 4, 5]))
                churn_probs.append(np.random.uniform(0.60, 0.95))
            else:
                recency_scores.append(self.safe_choice([2, 3, 4]))
                frequency_scores.append(self.safe_choice([2, 3, 4]))
                monetary_scores.append(self.safe_choice([2, 3, 4]))
                churn_probs.append(np.random.uniform(0.20, 0.50))
        
        last_purchase_dates = [now - timedelta(days=int(d)) for d in np.random.uniform(0, 120, n_customers)]
        lifetime_revs = np.round(np.random.lognormal(7.0, 1.5, n_customers), 2)
        
        customers_data = {
            'customer_id': [f'CUST{str(i).zfill(6)}' for i in range(1, n_customers + 1)],
            'customer_name': [f'Customer {i}' for i in range(1, n_customers + 1)],
            'customer_segment': cust_segments,
            'rfm_recency_score': recency_scores,
            'rfm_frequency_score': frequency_scores,
            'rfm_monetary_score': monetary_scores,
            'rfm_segment': cust_segments,
            'lifetime_revenue': lifetime_revs,
            'predicted_clv': np.round(lifetime_revs * np.random.uniform(1.2, 2.5, n_customers), 2),
            'churn_probability': np.round(churn_probs, 3),
            'last_purchase_date': last_purchase_dates,
            'purchase_count': np.random.randint(1, 150, n_customers),
            'preferred_channel': self.safe_choice(channels, n_customers),
            'channel_mix_ratio': np.round(np.random.uniform(0.1, 0.9, n_customers), 2)
        }
        
        behavior_profiles = []
        for i in range(n_customers):
            template = random.choice(behavior_templates)
            cat1 = random.choice(categories)
            cat2 = random.choice([c for c in categories if c != cat1])
            profile = template.format(
                channel=customers_data['preferred_channel'][i],
                category=cat1,
                category2=cat2,
                campaign_type=random.choice(campaign_types),
                avg_basket=int(customers_data['lifetime_revenue'][i] / max(customers_data['purchase_count'][i], 1)),
                channel_mix=int(customers_data['channel_mix_ratio'][i] * 100),
                payment=random.choice(['credit card', 'digital wallet', 'debit card'])
            )
            behavior_profiles.append(profile)
        
        customers_data['customer_behavior_profile'] = behavior_profiles
        datasets['customers'] = pd.DataFrame(customers_data)

        # Generate transactions (500000+ required, using 2500 for SMALL)
        n_transactions = 2500
        
        transaction_timestamps = pd.date_range(end=now, periods=n_transactions, freq='15min')
        transaction_customers = self.safe_choice(customers_data['customer_id'], n_transactions)
        transaction_products = self.safe_choice(products_data['product_id'], n_transactions)
        
        product_price_map = dict(zip(products_data['product_id'], products_data['unit_price']))
        transaction_amounts = []
        for prod_id in transaction_products:
            base_price = product_price_map[prod_id]
            qty = self.safe_choice([1, 1, 1, 2, 2, 3])
            transaction_amounts.append(np.round(base_price * qty * np.random.uniform(0.9, 1.1), 2))
        
        datasets['customer_transactions'] = pd.DataFrame({
            'transaction_id': [f'TXN{str(i).zfill(8)}' for i in range(1, n_transactions + 1)],
            '@timestamp': transaction_timestamps,
            'customer_id': transaction_customers,
            'product_id': transaction_products,
            'channel': self.safe_choice(channels, n_transactions, weights=[0.55, 0.45]),
            'transaction_amount': transaction_amounts,
            'payment_method': self.safe_choice(payment_methods, n_transactions),
            'store_location': self.safe_choice(store_locations, n_transactions),
            'campaign_id': self.safe_choice(datasets['campaigns']['campaign_id'].tolist() + ['NONE'] * 20, n_transactions)
        })

        return datasets

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships from requirements"""
        return [
            ('customer_transactions', 'customer_id', 'customers'),
            ('customer_transactions', 'product_id', 'products'),
            ('customer_transactions', 'campaign_id', 'campaigns')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {
            'customer_transactions': 'Transaction records from e-commerce and in-store POS systems',
            'customers': 'Unified customer profiles with RFM segmentation and predictive analytics',
            'products': 'Product catalog with pricing and margin information',
            'campaigns': 'Marketing campaign definitions and targeting parameters'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        """Return fields that should use semantic_text mapping"""
        return {
            'customers': ['customer_behavior_profile'],
            'products': ['product_description']
        }
