"""
Data generator templates for demo module generation.

This module provides templates for generating data generator modules
in both analytics and search modes.
"""

from typing import Dict, Any


def get_analytics_data_generator_template(config: Dict[str, Any]) -> str:
    """Get the data generator template for analytics mode demos"""

    # Extract size preferences
    size_preference = config.get('size_preference', 'medium').lower()
    ranges = {
        'small': {'timeseries_typical': '100-500', 'timeseries_max': 1000,
                  'reference_typical': '10-50', 'reference_max': 100},
        'medium': {'timeseries_typical': '500-5000', 'timeseries_max': 10000,
                   'reference_typical': '50-500', 'reference_max': 1000},
        'large': {'timeseries_typical': '5000-50000', 'timeseries_max': 100000,
                  'reference_typical': '500-5000', 'reference_max': 10000}
    }.get(size_preference, {'timeseries_typical': '500-5000', 'timeseries_max': 10000,
                             'reference_typical': '50-500', 'reference_max': 1000})

    return f"""from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List

class {config["company_name"].replace(" ", "")}DataGenerator(DataGeneratorModule):
    """Data generator for {config["company_name"]} - {config["department"]}"""

    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        """Generate datasets specific to {config["company_name"]}'s needs"""
        datasets = {{}}

        # Generate main dataset with columns specific to their business
        # Include patterns that demonstrate their pain points

        # EXAMPLE: Generate timestamps ending at NOW (critical for ES|QL queries)
        # Max 120 days of data - this example shows ~42 days (1000 hours)
        # events_df = pd.DataFrame({{
        #     'timestamp': pd.date_range(end=datetime.now(), periods=1000, freq='h'),
        #     'event_type': np.random.choice(['click', 'purchase'], 1000),
        #     'amount': np.random.uniform(10, 1000, 1000)
        # }})
        # datasets['events'] = events_df

        # IMPORTANT: Size preference is {size_preference.upper()}
        # - Primary datasets: {ranges['timeseries_typical']} rows (MAX {ranges['timeseries_max']:,})
        # - Reference/lookup tables: {ranges['reference_typical']} rows (MAX {ranges['reference_max']:,})
        # Scale mentioned: {config["scale"]} (for context only, don't generate that many rows!)

        return datasets

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships"""
        return [
            # (source_table, foreign_key_column, target_table)
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {{
            # 'dataset_name': 'Description of what this data represents'
        }}
"""


def get_search_data_generator_template(config: Dict[str, Any]) -> str:
    """Get the data generator template for search/RAG mode demos"""

    return f"""from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from typing import Dict, List
from faker import Faker

fake = Faker()

class {config["company_name"].replace(" ", "")}DataGenerator(DataGeneratorModule):
    """Data generator for {config["company_name"]} - Search/RAG mode"""

    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        """Generate document collections for search/RAG demos"""
        datasets = {{}}

        # Generate knowledge base or document collection
        # Focus on text-heavy data with semantic_text fields

        return datasets

    def get_relationships(self) -> List[tuple]:
        """Define foreign key relationships for LOOKUP JOINs"""
        return []

    def get_data_descriptions(self) -> Dict[str, str]:
        """Describe each dataset"""
        return {{}}
"""


def get_simple_data_generator_template(config: Dict[str, Any]) -> str:
    """Get the simple data generator template (fallback)"""

    company = config.get("company_name", "Company").replace(" ", "")

    return f"""from src.framework.base import DataGeneratorModule, DemoConfig
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

class {company}DataGenerator(DataGeneratorModule):
    """Simple data generator"""

    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        return {{
            'events': pd.DataFrame({{
                'timestamp': pd.date_range(end=datetime.now(), periods=100, freq='h'),
                'value': np.random.randn(100)
            }})
        }}

    def get_relationships(self) -> List[tuple]:
        return []

    def get_data_descriptions(self) -> Dict[str, str]:
        return {{'events': 'Event data'}}
"""
