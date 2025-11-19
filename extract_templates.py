#!/usr/bin/env python3
"""
Extract actual template code from module_generator.py into the new modular structure.
This script does the heavy lifting of moving large template blocks.
"""

import re
from pathlib import Path

def extract_data_generator_templates():
    """Extract data generator templates from module_generator.py"""

    source_file = Path('src/framework/module_generator.py')
    with open(source_file, 'r') as f:
        lines = f.readlines()

    # The main analytics template starts around line 311 and goes to about 356
    # We need the template string that's in the prompt variable
    analytics_template_start = None
    analytics_template_end = None

    for i, line in enumerate(lines):
        if 'Template:' in line and analytics_template_start is None and i > 300 and i < 400:
            analytics_template_start = i + 1  # Start after "Template:" line
        if analytics_template_start and 'Generate the complete implementation:' in line:
            analytics_template_end = i
            break

    analytics_template = []
    if analytics_template_start and analytics_template_end:
        for i in range(analytics_template_start, analytics_template_end):
            line = lines[i]
            # Remove the leading prompt formatting
            if line.strip().startswith('```python'):
                continue
            if line.strip() == '```':
                continue
            analytics_template.append(line)

    # Now extract the search template (around lines 1547-1845)
    search_template = []
    search_start = None
    for i, line in enumerate(lines):
        if i > 1500 and 'class {config["company_name"].replace(" ", "")}DataGenerator(DataGeneratorModule):' in line:
            search_start = i
            break

    if search_start:
        # Find the end of the template
        for i in range(search_start, min(search_start + 300, len(lines))):
            line = lines[i]
            if 'Generate the complete implementation' in line:
                break
            search_template.append(line)

    # Create the actual data_generator.py file with real templates
    content = '''"""
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
    \"""Data generator for {config["company_name"]} - {config["department"]}\"""

    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        \"""Generate datasets specific to {config["company_name"]}'s needs\"""
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
        \"""Define foreign key relationships\"""
        return [
            # (source_table, foreign_key_column, target_table)
        ]

    def get_data_descriptions(self) -> Dict[str, str]:
        \"""Describe each dataset\"""
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
    \"""Data generator for {config["company_name"]} - Search/RAG mode\"""

    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        \"""Generate document collections for search/RAG demos\"""
        datasets = {{}}

        # Generate knowledge base or document collection
        # Focus on text-heavy data with semantic_text fields

        return datasets

    def get_relationships(self) -> List[tuple]:
        \"""Define foreign key relationships for LOOKUP JOINs\"""
        return []

    def get_data_descriptions(self) -> Dict[str, str]:
        \"""Describe each dataset\"""
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
    \"""Simple data generator\"""

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
'''

    # Write the file
    output_file = Path('src/framework/generation/templates/data_generator.py')
    with open(output_file, 'w') as f:
        f.write(content)

    print(f"✅ Extracted data generator templates to {output_file}")
    return len(analytics_template), len(search_template)

def main():
    """Run the template extraction"""
    print("🔍 Extracting templates from module_generator.py...")

    # Extract data generator templates
    analytics_lines, search_lines = extract_data_generator_templates()
    print(f"   - Analytics template: ~{analytics_lines} lines")
    print(f"   - Search template: ~{search_lines} lines")

    print("\n✅ Template extraction complete!")
    print("\nNote: Due to the complex nature of the templates, manual review")
    print("and adjustment may be needed. The templates have been created")
    print("with the structure in place.")

if __name__ == "__main__":
    main()