from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

class BassProShopsDataGenerator(DataGeneratorModule):
    """Data generator for Bass Pro Shops - Product Management"""

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
        """Generate datasets specific to Bass Pro Shops's needs"""
        datasets = {}

        # Generate product catalog first (needed for FK relationships)
        datasets['product_catalog'] = self._generate_product_catalog()
        
        # Generate customer segments
        datasets['customer_segments'] = self._generate_customer_segments()
        
        # Generate market trends
        datasets['market_trends'] = self._generate_market_trends()
        
        # Generate product sales (main timeseries)
        datasets['product_sales'] = self._generate_product_sales(
            datasets['product_catalog'],
            datasets['customer_segments']
        )

        return datasets

    def _generate_product_catalog(self) -> pd.DataFrame:
        """Generate product catalog with 50,000+ products"""
        
        categories = {
            'Fishing': ['Rods', 'Reels', 'Lures', 'Tackle', 'Electronics', 'Apparel'],
            'Hunting': ['Firearms', 'Ammunition', 'Optics', 'Tree Stands', 'Blinds', 'Apparel'],
            'Camping': ['Tents', 'Sleeping Bags', 'Coolers', 'Stoves', 'Backpacks', 'Furniture'],
            'Boating': ['Motors', 'Trolling Motors', 'Marine Electronics', 'Safety', 'Accessories'],
            'Outdoor Lifestyle': ['Footwear', 'Clothing', 'Accessories', 'Home Decor', 'Gifts']
        }
        
        brands = {
            'Fishing': ['Bass Pro Shops', 'Shimano', 'Abu Garcia', 'Rapala', 'Berkley', 'Humminbird'],
            'Hunting': ['Bass Pro Shops', 'Browning', 'Mossy Oak', 'Bushnell', 'Leupold', 'Sitka'],
            'Camping': ['Bass Pro Shops', 'Coleman', 'Yeti', 'MSR', 'REI', 'Big Agnes'],
            'Boating': ['Minn Kota', 'Lowrance', 'Garmin', 'Mercury', 'Yamaha'],
            'Outdoor Lifestyle': ['Bass Pro Shops', 'RedHead', 'Carhartt', 'Columbia', 'Merrell']
        }
        
        seasonal_tags = ['Year-Round', 'Spring', 'Summer', 'Fall', 'Winter', 'Spring-Turkey', 
                        'Fall-Deer', 'Summer-Bass', 'Ice-Fishing', 'Holiday']
        
        products = []
        product_id = 1
        
        for category, subcategories in categories.items():
            category_brands = brands.get(category, ['Bass Pro Shops', 'Generic'])
            products_per_subcat = 10000 // len(subcategories)
            
            for subcategory in subcategories:
                for i in range(products_per_subcat):
                    brand = self.safe_choice(category_brands)
                    seasonal_tag = self.safe_choice(seasonal_tags, weights=[40, 10, 10, 15, 10, 5, 5, 3, 1, 1])
                    
                    price_ranges = {
                        'Rods': (29.99, 499.99), 'Reels': (19.99, 699.99), 'Lures': (3.99, 29.99),
                        'Firearms': (299.99, 2999.99), 'Optics': (49.99, 1999.99), 'Tents': (49.99, 899.99),
                        'Motors': (999.99, 9999.99), 'Footwear': (39.99, 299.99)
                    }
                    price_range = price_ranges.get(subcategory, (19.99, 299.99))
                    price = round(np.random.uniform(price_range[0], price_range[1]), 2)
                    
                    product_name = f"{brand} {subcategory} {self.safe_choice(['Pro', 'Elite', 'Classic', 'Sport', 'Adventure', 'Extreme'])}"
                    
                    descriptions = [
                        f"Premium {subcategory.lower()} designed for serious outdoor enthusiasts. Features advanced materials and ergonomic design for all-day comfort.",
                        f"Professional-grade {subcategory.lower()} with innovative technology. Perfect for {seasonal_tag.lower()} conditions and demanding use.",
                        f"High-performance {subcategory.lower()} built to last. Combines durability with precision engineering for optimal results.",
                        f"Versatile {subcategory.lower()} suitable for beginners and experts alike. Trusted by guides and professionals across North America.",
                        f"Tournament-tested {subcategory.lower()} with proven track record. Delivers consistent performance in challenging environments."
                    ]
                    
                    products.append({
                        'product_id': f'PRD{product_id:08d}',
                        'product_name': product_name,
                        'brand': brand,
                        'category': category,
                        'subcategory': subcategory,
                        'seasonal_tag': seasonal_tag,
                        'price': price,
                        'product_description': self.safe_choice(descriptions)
                    })
                    product_id += 1
        
        return pd.DataFrame(products)

    def _generate_customer_segments(self) -> pd.DataFrame:
        """Generate customer segments with regional preferences"""
        
        regions = ['Southeast', 'Northeast', 'Midwest', 'Southwest', 'Northwest', 'Mountain West']
        
        segment_profiles = [
            ('weekend-warrior', 'Weekend Warriors', ['Fishing', 'Camping'], 2.5, 850),
            ('serious-angler', 'Serious Anglers', ['Fishing', 'Boating'], 8.5, 3200),
            ('trophy-hunter', 'Trophy Hunters', ['Hunting', 'Optics'], 6.2, 4500),
            ('family-camper', 'Family Campers', ['Camping', 'Outdoor Lifestyle'], 3.1, 1200),
            ('outdoor-enthusiast', 'Outdoor Enthusiasts', ['Fishing', 'Hunting', 'Camping'], 5.8, 2800),
            ('competitive-angler', 'Competitive Anglers', ['Fishing', 'Boating'], 12.3, 6500),
            ('bow-hunter', 'Bow Hunters', ['Hunting', 'Apparel'], 7.1, 3800),
            ('fly-fishing', 'Fly Fishing Specialists', ['Fishing'], 9.2, 4200),
            ('waterfowl-hunter', 'Waterfowl Hunters', ['Hunting', 'Boating'], 5.5, 3100),
            ('backpacker', 'Backpackers', ['Camping', 'Footwear'], 4.2, 1800)
        ]
        
        segments = []
        segment_id = 1
        
        for region in regions:
            for seg_key, seg_name, interests, freq_base, ltv_base in segment_profiles:
                regional_multiplier = np.random.uniform(0.8, 1.3)
                
                primary_interest = self.safe_choice(interests)
                interest_keywords = ', '.join(interests + [
                    self.safe_choice(['trophy', 'recreational', 'professional', 'beginner', 'expert'])
                ])
                
                segments.append({
                    'segment_id': f'{seg_key}-{region.lower().replace(" ", "-")}',
                    'segment_name': seg_name,
                    'region': region,
                    'primary_interest': primary_interest,
                    'avg_purchase_frequency': round(freq_base * regional_multiplier, 1),
                    'lifetime_value': round(ltv_base * regional_multiplier, 2),
                    'segment_description': f"{seg_name} in {region} region with focus on {primary_interest.lower()}. Active {int(freq_base * regional_multiplier)} times per year.",
                    'interest_keywords': interest_keywords
                })
                segment_id += 1
        
        return pd.DataFrame(segments)

    def _generate_market_trends(self) -> pd.DataFrame:
        """Generate market trends data"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)  # 2 years
        
        regions = ['Southeast', 'Northeast', 'Midwest', 'Southwest', 'Northwest', 'Mountain West']
        
        trend_topics = {
            'Fishing': [
                'bass fishing tournaments', 'kayak fishing growth', 'forward-facing sonar adoption',
                'sustainable fishing practices', 'ice fishing popularity', 'fly fishing resurgence'
            ],
            'Hunting': [
                'crossbow hunting expansion', 'thermal optics demand', 'public land access concerns',
                'turkey hunting decline', 'deer population trends', 'predator hunting interest'
            ],
            'Camping': [
                'overlanding trend', 'glamping popularity', 'solar camping gear', 
                'ultralight backpacking', 'family camping resurgence', 'van life movement'
            ],
            'Boating': [
                'electric trolling motors', 'lithium battery adoption', 'shallow water anchors',
                'pontoon boat popularity', 'kayak fishing growth', 'boat shortage impact'
            ],
            'Conservation': [
                'habitat restoration', 'wildlife population studies', 'fishing license trends',
                'youth outdoor participation', 'public land funding', 'invasive species concerns'
            ]
        }
        
        trends = []
        trend_id = 1
        
        current_date = start_date
        while current_date <= end_date:
            for region in regions:
                num_trends = np.random.randint(3, 8)
                
                for _ in range(num_trends):
                    category = self.safe_choice(list(trend_topics.keys()))
                    topic = self.safe_choice(trend_topics[category])
                    
                    # Seasonal patterns
                    month = current_date.month
                    seasonal_multiplier = 1.0
                    if 'spring' in topic.lower() or 'turkey' in topic.lower():
                        seasonal_multiplier = 2.0 if month in [3, 4, 5] else 0.5
                    elif 'fall' in topic.lower() or 'deer' in topic.lower():
                        seasonal_multiplier = 2.5 if month in [9, 10, 11] else 0.4
                    elif 'ice' in topic.lower():
                        seasonal_multiplier = 3.0 if month in [12, 1, 2] else 0.1
                    
                    base_search = np.random.randint(500, 5000)
                    search_volume = int(base_search * seasonal_multiplier * np.random.uniform(0.8, 1.2))
                    
                    social_mentions = int(search_volume * np.random.uniform(0.3, 0.8))
                    sentiment_score = np.random.uniform(0.4, 0.9)
                    
                    trend_desc = f"Market trend analysis for {topic} in {region}. Search volume indicates {['declining', 'stable', 'growing', 'surging'][int(sentiment_score * 3)]} interest among outdoor enthusiasts."
                    
                    trends.append({
                        'trend_id': f'TRD{trend_id:08d}',
                        'timestamp': current_date,
                        'region': region,
                        'trend_category': category,
                        'trend_topic': topic,
                        'sentiment_score': round(sentiment_score, 3),
                        'search_volume': search_volume,
                        'social_mentions': social_mentions,
                        'trend_description': trend_desc
                    })
                    trend_id += 1
            
            current_date += timedelta(days=7)  # Weekly trends
        
        return pd.DataFrame(trends)

    def _generate_product_sales(self, product_catalog: pd.DataFrame, 
                                customer_segments: pd.DataFrame) -> pd.DataFrame:
        """Generate product sales transactions"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=730)  # 2 years
        
        regions = ['Southeast', 'Northeast', 'Midwest', 'Southwest', 'Northwest', 'Mountain West']
        stores_per_region = 15
        
        sales = []
        sale_id = 1
        
        # Sample products for performance
        sampled_products = product_catalog.sample(n=min(5000, len(product_catalog)))
        segment_list = customer_segments['segment_id'].tolist()
        
        current_date = start_date
        while current_date <= end_date:
            daily_transactions = np.random.randint(1500, 3500)
            
            for _ in range(daily_transactions):
                product = sampled_products.sample(n=1).iloc[0]
                
                # Seasonal sales patterns
                month = current_date.month
                seasonal_boost = 1.0
                if product['seasonal_tag'] in ['Spring', 'Spring-Turkey'] and month in [3, 4, 5]:
                    seasonal_boost = 2.5
                elif product['seasonal_tag'] in ['Fall', 'Fall-Deer'] and month in [9, 10, 11]:
                    seasonal_boost = 3.0
                elif product['seasonal_tag'] == 'Summer-Bass' and month in [6, 7, 8]:
                    seasonal_boost = 2.2
                elif product['seasonal_tag'] == 'Holiday' and month in [11, 12]:
                    seasonal_boost = 2.8
                
                if np.random.random() > (0.3 / seasonal_boost):
                    continue
                
                # Regional preferences
                region_weights = [1] * len(regions)
                if product['category'] == 'Fishing':
                    region_weights = [3, 1, 2, 2, 2, 1]  # Southeast bass fishing
                elif product['category'] == 'Hunting':
                    region_weights = [2, 1, 3, 2, 1, 2]  # Midwest hunting
                
                region = self.safe_choice(regions, weights=region_weights)
                store_id = f'STORE-{region[:3].upper()}-{np.random.randint(1, stores_per_region + 1):03d}'
                
                # Match customer segment to region and category
                region_segments = customer_segments[customer_segments['region'] == region]
                matching_segments = region_segments[
                    region_segments['primary_interest'] == product['category']
                ]
                
                if len(matching_segments) > 0:
                    segment = matching_segments.sample(n=1).iloc[0]['segment_id']
                else:
                    segment = region_segments.sample(n=1).iloc[0]['segment_id']
                
                quantity = self.safe_choice([1, 2, 3, 4], weights=[70, 20, 7, 3])
                revenue = round(product['price'] * quantity * np.random.uniform(0.95, 1.0), 2)
                
                timestamp = self.random_timedelta(
                    current_date, 
                    hours=self.safe_choice(range(24), weights=[1,1,1,1,1,2,3,5,8,10,12,14,15,14,12,10,8,6,4,3,2,1,1,1])
                )
                
                feedback_options = [
                    f"Great {product['subcategory'].lower()} for the price. Used it during {product['seasonal_tag'].lower()} season and performed excellently.",
                    f"Purchased for {region} fishing/hunting conditions. Quality matches the {product['brand']} reputation.",
                    f"Excellent product for serious outdoor use. The {product['subcategory'].lower()} exceeded expectations.",
                    f"Perfect for weekend trips. Good value in the {product['category'].lower()} category.",
                    f"Professional-grade performance. Highly recommend for {product['seasonal_tag'].lower()} activities."
                ]
                
                sales.append({
                    'sale_id': f'SALE{sale_id:010d}',
                    'timestamp': timestamp,
                    'product_id': product['product_id'],
                    'category': product['category'],
                    'subcategory': product['subcategory'],
                    'region': region,
                    'store_id': store_id,
                    'quantity': quantity,
                    'revenue': revenue,
                    'customer_segment': segment,
                    'product_description': product['product_description'],
                    'customer_feedback': self.safe_choice(feedback_options)
                })
                sale_id += 1
                
                if sale_id > 500000:  # Cap at 500k for performance
                    return pd.DataFrame(sales)
            
            current_date += timedelta(days=1)
        
        return pd.DataFrame(sales)

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships"""
        return [
            ('product_sales', 'product_id', 'product_catalog'),
            ('product_sales', 'customer_segment', 'customer_segments'),
            ('product_sales', 'region', 'market_trends')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {
            'product_sales': 'Transaction-level sales data across all Bass Pro Shops locations with customer segments and regional patterns',
            'product_catalog': 'Complete product catalog with categories, brands, pricing, and seasonal tags for hunting, fishing, camping, and outdoor lifestyle',
            'market_trends': 'Regional market trends, search volumes, social mentions, and sentiment analysis for outdoor recreation topics',
            'customer_segments': 'Customer segmentation profiles with regional preferences, purchase frequency, and lifetime value metrics'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        """Specify fields that should use semantic_text for vector search"""
        return {
            'product_sales': ['product_description', 'customer_feedback'],
            'product_catalog': ['product_description', 'product_name'],
            'market_trends': ['trend_topic', 'trend_description'],
            'customer_segments': ['segment_description', 'interest_keywords']
        }