
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List

class TecsoDataGenerator(DataGeneratorModule):
    """Data generator for Tecso - Market Research"""

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
        num_products = 200
        num_customers = 500
        num_transactions = 2500

        # Products dataset
        categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports & Outdoors', 'Beauty & Personal Care', 
                     'Food & Beverages', 'Books & Media', 'Toys & Games', 'Health & Wellness', 'Automotive']
        
        subcategories = {
            'Electronics': ['Smartphones', 'Laptops', 'Tablets', 'Headphones', 'Smart Home'],
            'Clothing': ['Men\'s Apparel', 'Women\'s Apparel', 'Kids\' Clothing', 'Shoes', 'Accessories'],
            'Home & Garden': ['Furniture', 'Kitchen', 'Bedding', 'Decor', 'Garden Tools'],
            'Sports & Outdoors': ['Fitness Equipment', 'Camping Gear', 'Athletic Wear', 'Bikes', 'Team Sports'],
            'Beauty & Personal Care': ['Skincare', 'Makeup', 'Hair Care', 'Fragrances', 'Bath & Body'],
            'Food & Beverages': ['Snacks', 'Beverages', 'Organic', 'Frozen Foods', 'Pantry Staples'],
            'Books & Media': ['Fiction', 'Non-Fiction', 'Movies', 'Music', 'Magazines'],
            'Toys & Games': ['Action Figures', 'Board Games', 'Educational Toys', 'Dolls', 'Puzzles'],
            'Health & Wellness': ['Vitamins', 'Supplements', 'Medical Supplies', 'Fitness Trackers', 'Wellness'],
            'Automotive': ['Car Accessories', 'Tools', 'Maintenance', 'Electronics', 'Parts']
        }
        
        brands = ['TechPro', 'StyleMax', 'HomeComfort', 'ActiveLife', 'BeautyGlow', 'FreshChoice', 
                 'ReadWell', 'PlayFun', 'VitalCare', 'AutoExpert', 'PremiumSelect', 'ValueBrand']

        product_cats = self.safe_choice(categories, size=num_products)
        product_subcats = [self.safe_choice(subcategories[cat]) for cat in product_cats]
        
        product_desc_templates = [
            "High-quality {subcategory} from {brand} with excellent durability and performance",
            "Premium {subcategory} designed for everyday use, brought to you by {brand}",
            "{brand}'s bestselling {subcategory} featuring innovative design and superior quality",
            "Affordable {subcategory} from {brand} with great value and reliability",
            "Luxury {subcategory} by {brand} for discerning customers seeking excellence"
        ]

        products = pd.DataFrame({
            'product_id': [f'PROD{str(i+1).zfill(6)}' for i in range(num_products)],
            'product_name': [f'{self.safe_choice(brands)} {subcat} {self.safe_choice(["Pro", "Plus", "Elite", "Standard", "Premium"])}' 
                           for subcat in product_subcats],
            'product_category': product_cats,
            'product_subcategory': product_subcats,
            'unit_price': np.round(np.random.lognormal(3.5, 1.0, num_products), 2),
            'brand': self.safe_choice(brands, size=num_products),
            'product_description': [
                random.choice(product_desc_templates).format(
                    subcategory=product_subcats[i],
                    brand=self.safe_choice(brands)
                ) for i in range(num_products)
            ]
        })
        datasets['products'] = products

        # Customers dataset
        segments = ['Premium', 'Standard', 'Budget', 'VIP']
        age_groups = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+']
        channels = ['Online', 'In-Store', 'Mobile App', 'Hybrid']
        
        first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 
                      'William', 'Barbara', 'David', 'Elizabeth', 'Richard', 'Susan', 'Joseph', 'Jessica']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 
                     'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas']

        now = datetime.now()
        acq_dates = [now - timedelta(days=int(d)) for d in np.random.uniform(30, 1800, num_customers)]
        
        customer_segs = self.safe_choice(segments, size=num_customers, weights=[0.15, 0.50, 0.30, 0.05])
        
        profile_templates = [
            "{segment} customer in {age_group} age bracket, prefers {channel} shopping with strong interest in {category}",
            "{age_group} shopper classified as {segment} segment, primarily uses {channel} and frequently purchases {category}",
            "{segment} tier customer aged {age_group}, loyal {channel} user with high engagement in {category} products",
            "{age_group} demographic, {segment} classification, shows consistent {channel} activity and {category} preference"
        ]

        customers = pd.DataFrame({
            'customer_id': [f'CUST{str(i+1).zfill(7)}' for i in range(num_customers)],
            'customer_name': [f'{self.safe_choice(first_names)} {self.safe_choice(last_names)}' for _ in range(num_customers)],
            'customer_segment': customer_segs,
            'demographic_age_group': self.safe_choice(age_groups, size=num_customers),
            'lifetime_value': np.round(np.random.lognormal(6.5, 1.2, num_customers), 2),
            'acquisition_date': acq_dates,
            'preferred_channel': self.safe_choice(channels, size=num_customers),
            'customer_profile_description': [
                random.choice(profile_templates).format(
                    segment=customer_segs[i],
                    age_group=self.safe_choice(age_groups),
                    channel=self.safe_choice(channels),
                    category=self.safe_choice(categories)
                ) for i in range(num_customers)
            ]
        })
        datasets['customers'] = customers

        # Purchase transactions dataset
        timestamps = pd.date_range(end=now, periods=num_transactions, freq='45min')
        
        store_locations = ['New York - Manhattan', 'Los Angeles - Downtown', 'Chicago - Loop', 
                          'Houston - Galleria', 'Phoenix - Scottsdale', 'Philadelphia - Center City',
                          'San Antonio - Riverwalk', 'San Diego - Fashion Valley', 'Dallas - Uptown',
                          'Austin - Domain', 'Online Warehouse', 'Mobile Fulfillment Center']
        
        transaction_channels = ['Online', 'In-Store', 'Mobile App']
        
        notes_templates = [
            "Customer purchased {quantity} units of {product_category} via {channel}",
            "{channel} transaction for {product_category} items, total quantity {quantity}",
            "Completed {channel} purchase of {quantity} {product_category} products",
            "{quantity} item {channel} order in {product_category} category",
            "{product_category} purchase via {channel}, quantity {quantity}, smooth checkout"
        ]

        selected_customers = self.safe_choice(customers['customer_id'].values, size=num_transactions)
        selected_products = self.safe_choice(products['product_id'].values, size=num_transactions)
        quantities = np.random.choice([1, 1, 1, 2, 2, 3, 4, 5], size=num_transactions)
        
        product_prices = products.set_index('product_id')['unit_price'].to_dict()
        product_categories = products.set_index('product_id')['product_category'].to_dict()
        
        purchase_amounts = [product_prices[pid] * qty * np.random.uniform(0.95, 1.05) 
                          for pid, qty in zip(selected_products, quantities)]
        
        trans_channels = self.safe_choice(transaction_channels, size=num_transactions, weights=[0.45, 0.35, 0.20])

        transactions = pd.DataFrame({
            'transaction_id': [f'TXN{str(i+1).zfill(8)}' for i in range(num_transactions)],
            '@timestamp': timestamps,
            'customer_id': selected_customers,
            'product_id': selected_products,
            'purchase_amount': np.round(purchase_amounts, 2),
            'purchase_channel': trans_channels,
            'quantity': quantities,
            'store_location': [self.safe_choice(store_locations) if ch == 'In-Store' 
                             else self.safe_choice(['Online Warehouse', 'Mobile Fulfillment Center'])
                             for ch in trans_channels],
            'transaction_notes': [
                random.choice(notes_templates).format(
                    quantity=quantities[i],
                    product_category=product_categories[selected_products[i]],
                    channel=trans_channels[i]
                ) for i in range(num_transactions)
            ]
        })
        datasets['purchase_transactions'] = transactions

        return datasets

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships from requirements"""
        return [
            ('purchase_transactions', 'customer_id', 'customers'),
            ('purchase_transactions', 'product_id', 'products')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {
            'purchase_transactions': 'Online and in-store purchase transaction history with customer and product details',
            'customers': 'Customer profiles with segmentation, demographics, and lifetime value metrics',
            'products': 'Product catalog with categories, pricing, and brand information'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        """Return fields that should use semantic_text mapping"""
        return {
            'purchase_transactions': ['transaction_notes'],
            'customers': ['customer_profile_description'],
            'products': ['product_description']
        }
