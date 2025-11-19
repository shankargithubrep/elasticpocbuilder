
from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List

class VerizonFIOSDataGenerator(DataGeneratorModule):
    """Data generator for Verizon FIOS - Consumer TV Product & Personalization Engineering"""

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
        
        # Content themes (reference data)
        n_themes = 500
        
        parent_themes = ['Drama', 'Comedy', 'Action', 'Romance', 'Thriller', 'SciFi', 'Fantasy', 
                        'Mystery', 'Horror', 'Documentary', 'Family', 'Adventure']
        
        emotional_tones = ['Uplifting', 'Dark', 'Bittersweet', 'Intense', 'Light', 'Melancholic', 
                          'Suspenseful', 'Whimsical', 'Gritty', 'Inspirational']
        
        narrative_elements = ['Character-driven', 'Plot-driven', 'Ensemble cast', 'Single protagonist', 
                             'Non-linear', 'Linear', 'Episodic', 'Serialized', 'Anthology']
        
        theme_names = [
            'Coming of age', 'Redemption arc', 'Family dynamics', 'Corporate intrigue', 'Political power',
            'Love triangle', 'Revenge quest', 'Identity crisis', 'Moral ambiguity', 'Survival',
            'Friendship bonds', 'Betrayal', 'Good vs evil', 'Time travel', 'Parallel universes',
            'Artificial intelligence', 'Post-apocalyptic', 'Historical drama', 'Social justice',
            'Mental health', 'Addiction recovery', 'Generational conflict', 'Class struggle'
        ] * 25
        
        datasets['content_themes'] = pd.DataFrame({
            'theme_id': [f'THEME-{i:05d}' for i in range(n_themes)],
            'theme_name': [theme_names[i % len(theme_names)] for i in range(n_themes)],
            'theme_description': [
                f"A narrative exploration of {theme_names[i % len(theme_names)].lower()} with emphasis on character development and emotional depth"
                for i in range(n_themes)
            ],
            'parent_theme': self.safe_choice(parent_themes, n_themes),
            'related_themes': [
                ','.join(self.safe_choice(theme_names[:23], size=np.random.randint(2, 5), replace=False))
                for _ in range(n_themes)
            ],
            'emotional_tone': self.safe_choice(emotional_tones, n_themes),
            'narrative_elements': [
                ','.join(self.safe_choice(narrative_elements, size=np.random.randint(1, 3), replace=False))
                for _ in range(n_themes)
            ]
        })
        
        # Content catalog
        n_content = 2000
        
        content_types = ['Movie', 'Series', 'Documentary', 'Special', 'Sports']
        genres = ['Drama', 'Comedy', 'Action', 'Thriller', 'SciFi', 'Romance', 'Horror', 'Mystery', 
                 'Fantasy', 'Documentary', 'Family', 'Crime', 'Adventure', 'Animation']
        
        subgenres_map = {
            'Drama': ['Legal', 'Medical', 'Political', 'Historical', 'Psychological'],
            'Comedy': ['Sitcom', 'Romantic', 'Dark', 'Slapstick', 'Satire'],
            'Action': ['Spy', 'Military', 'Superhero', 'Martial arts', 'Heist'],
            'Thriller': ['Psychological', 'Crime', 'Legal', 'Political', 'Conspiracy'],
            'SciFi': ['Space opera', 'Cyberpunk', 'Time travel', 'Dystopian', 'Hard sci-fi']
        }
        
        complexity_levels = ['Simple', 'Moderate', 'Complex', 'Very Complex']
        tones = ['Light', 'Serious', 'Dark', 'Uplifting', 'Intense', 'Whimsical', 'Gritty']
        ratings = ['G', 'PG', 'PG-13', 'TV-14', 'TV-MA', 'R']
        availability = ['On-demand', 'Live', 'Premium', 'Basic']
        
        studios = ['Warner Bros', 'Universal', 'Paramount', 'Sony', 'Disney', 'Netflix Studios', 
                  'HBO Max', 'Amazon Studios', 'Apple TV+', 'NBC Universal']
        
        first_names = ['James', 'Sarah', 'Michael', 'Jennifer', 'David', 'Emily', 'Robert', 'Lisa']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
        
        content_genres = self.safe_choice(genres, n_content)
        
        datasets['content_catalog'] = pd.DataFrame({
            'content_id': [f'CONTENT-{i:06d}' for i in range(n_content)],
            'title': [f"{self.safe_choice(['The', 'A', 'An', ''])} {self.safe_choice(['Dark', 'Lost', 'Hidden', 'Last', 'First', 'Final', 'Rising', 'Fallen'])} {self.safe_choice(['Kingdom', 'City', 'Empire', 'Legacy', 'Chronicles', 'Saga', 'Journey', 'Destiny'])}" for _ in range(n_content)],
            'description': [
                f"A compelling {content_genres[i].lower()} that explores themes of {self.safe_choice(theme_names[:23]).lower()} with {self.safe_choice(['intense', 'nuanced', 'gripping', 'heartfelt', 'powerful'])} storytelling and {self.safe_choice(['complex', 'memorable', 'dynamic', 'layered'])} characters"
                for i in range(n_content)
            ],
            'content_type': self.safe_choice(content_types, n_content, weights=[40, 35, 10, 10, 5]),
            'genre': content_genres,
            'subgenres': [
                ','.join(self.safe_choice(subgenres_map.get(content_genres[i], ['General', 'Contemporary']), 
                        size=min(2, len(subgenres_map.get(content_genres[i], ['General']))), replace=False))
                for i in range(n_content)
            ],
            'themes': [
                ','.join(self.safe_choice(theme_names[:23], size=np.random.randint(2, 5), replace=False))
                for _ in range(n_content)
            ],
            'narrative_complexity': self.safe_choice(complexity_levels, n_content, weights=[20, 40, 30, 10]),
            'tone': self.safe_choice(tones, n_content),
            'release_year': np.random.randint(2015, 2025, n_content),
            'runtime_minutes': np.random.choice([45, 60, 90, 120, 150], n_content, p=[0.3, 0.25, 0.2, 0.15, 0.1]),
            'rating': self.safe_choice(ratings, n_content),
            'cast': [
                ','.join([f"{self.safe_choice(first_names)} {self.safe_choice(last_names)}" 
                         for _ in range(np.random.randint(3, 6))])
                for _ in range(n_content)
            ],
            'director': [f"{self.safe_choice(first_names)} {self.safe_choice(last_names)}" for _ in range(n_content)],
            'studio': self.safe_choice(studios, n_content),
            'availability': self.safe_choice(availability, n_content, weights=[50, 20, 20, 10])
        })
        
        # User preferences
        n_users = 5000
        
        profile_maturity_levels = ['Cold Start', 'Developing', 'Established', 'Mature']
        interaction_contexts = ['Browse', 'Search', 'Recommendation', 'Watchlist', 'Continue watching']
        
        datasets['user_preferences'] = pd.DataFrame({
            'user_id': [f'USER-{i:07d}' for i in range(n_users)],
            'subscriber_id': [f'SUB-{i:07d}' for i in range(n_users)],
            'preference_vector': [
                ','.join([f'{np.random.random():.4f}' for _ in range(20)])
                for _ in range(n_users)
            ],
            'liked_themes': [
                ','.join(self.safe_choice(theme_names[:23], size=np.random.randint(3, 7), replace=False))
                for _ in range(n_users)
            ],
            'disliked_themes': [
                ','.join(self.safe_choice(theme_names[:23], size=np.random.randint(1, 4), replace=False))
                for _ in range(n_users)
            ],
            'preferred_genres': [
                ','.join(self.safe_choice(genres, size=np.random.randint(2, 5), replace=False))
                for _ in range(n_users)
            ],
            'avoided_genres': [
                ','.join(self.safe_choice(genres, size=np.random.randint(0, 3), replace=False))
                for _ in range(n_users)
            ],
            'preferred_tone': self.safe_choice(tones, n_users),
            'complexity_preference': self.safe_choice(complexity_levels, n_users),
            'session_count': np.random.choice([2, 5, 15, 35, 75], n_users, p=[0.15, 0.20, 0.30, 0.25, 0.10]),
            'profile_maturity': self.safe_choice(profile_maturity_levels, n_users, weights=[15, 25, 35, 25]),
            'last_updated': pd.date_range(end=datetime.now(), periods=n_users, freq='15min'),
            'cold_start_phase': np.random.choice([True, False], n_users, p=[0.18, 0.82])
        })
        
        # Viewing history (events)
        n_events = 12000
        
        event_types = ['play', 'pause', 'stop', 'skip', 'complete', 'dismiss', 'rate']
        
        user_ids = datasets['user_preferences']['user_id'].tolist()
        content_ids = datasets['content_catalog']['content_id'].tolist()
        
        timestamps = pd.date_range(end=datetime.now(), periods=n_events, freq='7s')
        selected_users = self.safe_choice(user_ids, n_events)
        selected_content = self.safe_choice(content_ids, n_events)
        selected_events = self.safe_choice(event_types, n_events, weights=[30, 15, 20, 10, 15, 5, 5])
        
        datasets['viewing_history'] = pd.DataFrame({
            'event_id': [f'EVT-{i:010d}' for i in range(n_events)],
            'user_id': selected_users,
            'content_id': selected_content,
            'event_type': selected_events,
            'watch_duration_seconds': [
                np.random.randint(30, 7200) if selected_events[i] in ['play', 'pause', 'stop', 'complete'] 
                else np.random.randint(5, 300)
                for i in range(n_events)
            ],
            'completion_percentage': [
                np.random.uniform(0.7, 1.0) if selected_events[i] == 'complete'
                else np.random.uniform(0.0, 0.3) if selected_events[i] == 'skip'
                else np.random.uniform(0.1, 0.9)
                for i in range(n_events)
            ],
            'skipped': [selected_events[i] == 'skip' for i in range(n_events)],
            'dismissed': [selected_events[i] == 'dismiss' for i in range(n_events)],
            'rating_given': [
                np.random.randint(1, 6) if selected_events[i] == 'rate' else 0
                for i in range(n_events)
            ],
            'interaction_context': self.safe_choice(interaction_contexts, n_events, weights=[30, 20, 35, 10, 5]),
            '@timestamp': timestamps
        })
        
        # Recommendation explanations
        n_recs = 1000
        
        reasoning_factors_list = [
            'Theme similarity', 'Genre match', 'Tone preference', 'Narrative complexity',
            'Cast preference', 'Director preference', 'Similar viewing history', 'Popular with similar users',
            'Trending content', 'New release', 'Highly rated', 'Completion rate'
        ]
        
        explanation_templates = [
            "Recommended because you enjoyed similar {theme} themes in {genre} content",
            "Based on your preference for {tone} tone and {complexity} narrative complexity",
            "Similar to content you've watched with {theme} themes",
            "Popular among viewers who share your interest in {genre} and {theme}",
            "Matches your preference for {tone} storytelling with {complexity} plots"
        ]
        
        rec_user_ids = self.safe_choice(user_ids, n_recs)
        rec_content_ids = self.safe_choice(content_ids, n_recs)
        
        datasets['recommendation_explanations'] = pd.DataFrame({
            'recommendation_id': [f'REC-{i:08d}' for i in range(n_recs)],
            'user_id': rec_user_ids,
            'content_id': rec_content_ids,
            'explanation_text': [
                random.choice(explanation_templates).format(
                    theme=self.safe_choice(theme_names[:23]),
                    genre=self.safe_choice(genres),
                    tone=self.safe_choice(tones),
                    complexity=self.safe_choice(complexity_levels)
                )
                for _ in range(n_recs)
            ],
            'reasoning_factors': [
                ','.join(self.safe_choice(reasoning_factors_list, size=np.random.randint(2, 5), replace=False))
                for _ in range(n_recs)
            ],
            'similarity_score': np.random.uniform(0.65, 0.98, n_recs),
            'preference_match_themes': [
                ','.join(self.safe_choice(theme_names[:23], size=np.random.randint(2, 4), replace=False))
                for _ in range(n_recs)
            ],
            'created_at': pd.date_range(end=datetime.now(), periods=n_recs, freq='5min')
        })
        
        return datasets

    def get_relationships(self) -> List[tuple]:
        return [
            ('user_preferences', 'user_id', 'viewing_history'),
            ('content_catalog', 'content_id', 'viewing_history'),
            ('content_catalog', 'content_id', 'recommendation_explanations'),
            ('user_preferences', 'user_id', 'recommendation_explanations'),
            ('content_themes', 'theme_id', 'content_catalog')
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        return {
            'content_catalog': 'On-demand titles and live channel content with rich metadata including themes, narrative complexity, and tone',
            'user_preferences': 'Multi-dimensional user preference profiles with theme preferences, genre affinities, and cold start indicators',
            'viewing_history': 'Granular viewing events capturing play, skip, dismiss, and completion behaviors with context',
            'recommendation_explanations': 'Transparent recommendation reasoning with similarity scores and matched preference factors',
            'content_themes': 'Hierarchical theme taxonomy with emotional tones and narrative elements for semantic content understanding'
        }

    def get_semantic_fields(self) -> Dict[str, List[str]]:
        return {
            'content_catalog': ['description'],
            'recommendation_explanations': ['explanation_text'],
            'content_themes': ['theme_description']
        }
