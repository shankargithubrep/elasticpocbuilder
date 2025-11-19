#!/usr/bin/env python3
"""
Script to refactor the monolithic module_generator.py into smaller, modular components.
This is a one-time refactoring script that extracts templates and functions.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

def extract_method_ranges(file_path: Path) -> dict:
    """Extract method definitions and their line ranges from the file"""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    methods = {}
    current_method = None
    current_indent = None
    start_line = None

    for i, line in enumerate(lines):
        # Check for method definition
        if re.match(r'^    def (\w+)\(', line):
            # Save previous method
            if current_method and start_line is not None:
                methods[current_method] = (start_line, i)

            # Start new method
            match = re.match(r'^    def (\w+)\(', line)
            current_method = match.group(1)
            current_indent = len(line) - len(line.lstrip())
            start_line = i

        # Check for class definition (ends current method)
        elif re.match(r'^class \w+', line) and current_method:
            if start_line is not None:
                methods[current_method] = (start_line, i)
            current_method = None
            start_line = None

    # Save the last method
    if current_method and start_line is not None:
        methods[current_method] = (start_line, len(lines))

    return methods

def extract_lines(file_path: Path, start: int, end: int) -> str:
    """Extract lines from start to end (exclusive) from file"""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    return ''.join(lines[start:end])

def create_data_generator_templates():
    """Create the data generator templates module"""

    template = '''"""
Data generator templates for demo module generation.

This module provides templates for generating data generator modules
in both analytics and search modes.
"""

from typing import Dict, Any


def get_analytics_data_generator_template(config: Dict[str, Any]) -> str:
    """Get the data generator template for analytics mode demos

    This template creates a DataGeneratorModule that generates:
    - Time-series data with @timestamp fields
    - Lookup/reference tables for JOIN operations
    - Realistic business data patterns
    """

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

    # Template will be filled from module_generator.py lines 311-356
    return f"""# Analytics data generator template
# TODO: Extract from module_generator.py lines 311-356
"""


def get_search_data_generator_template(config: Dict[str, Any]) -> str:
    """Get the data generator template for search/RAG mode demos

    This template creates a DataGeneratorModule that generates:
    - Document collections with semantic_text fields
    - Knowledge base content for RAG pipelines
    - Text-heavy data suitable for MATCH operations
    """

    # Template will be filled from module_generator.py lines 1547-1845
    return f"""# Search data generator template
# TODO: Extract from module_generator.py lines 1547-1845
"""


def get_simple_data_generator_template(config: Dict[str, Any]) -> str:
    """Get the simple data generator template (fallback)

    This is a minimal template used when:
    - Query strategy generation fails
    - Quick prototyping is needed
    - Legacy compatibility is required
    """

    # Template will be filled from module_generator.py lines 3097-3145
    return f"""# Simple data generator template
# TODO: Extract from module_generator.py lines 3097-3145
"""
'''

    os.makedirs('src/framework/generation/templates', exist_ok=True)
    with open('src/framework/generation/templates/data_generator.py', 'w') as f:
        f.write(template)
    print("✅ Created data_generator.py template module")

def create_query_generator_templates():
    """Create the query generator templates module"""

    template = '''"""
Query generator templates for demo module generation.

This module provides templates for generating query generator modules
with scripted, parameterized, and RAG query types.
"""

from typing import Dict, Any


def get_analytics_query_generator_template() -> str:
    """Get the query generator template for analytics mode

    Generates queries focused on:
    - Aggregations with STATS
    - Time-series analysis with DATE_TRUNC
    - LOOKUP JOIN operations
    - Metrics and dashboards
    """
    # Template from lines 1329-1410
    return """# TODO: Extract analytics query generator template"""


def get_search_query_generator_template() -> str:
    """Get the query generator template for search/RAG mode

    Generates queries focused on:
    - MATCH operations for text search
    - RERANK for relevance optimization
    - COMPLETION for LLM-based answers
    - Semantic search patterns
    """
    # Template from lines 2229-?
    return """# TODO: Extract search query generator template"""


def get_simple_query_generator_template() -> str:
    """Get the simple query generator template (fallback)"""
    # Template from lines 3147-3180
    return """# TODO: Extract simple query generator template"""


def get_query_generator_with_strategy_template(query_strategy: Dict[str, Any]) -> str:
    """Get template for generating queries from a query strategy

    This is used in the two-phase generation approach where:
    1. Query strategy is generated first
    2. Data is generated and indexed
    3. Queries are generated with actual schema knowledge
    """
    # Template logic for strategy-based generation
    return """# TODO: Extract strategy-based query generator template"""
'''

    with open('src/framework/generation/templates/query_generator.py', 'w') as f:
        f.write(template)
    print("✅ Created query_generator.py template module")

def create_guide_generator_templates():
    """Create the guide generator templates module"""

    template = '''"""
Demo guide templates for module generation.

This module provides templates for generating demo guide modules
that create narrative documentation for demos.
"""

from typing import Dict, Any


def get_demo_guide_template(config: Dict[str, Any]) -> str:
    """Get the demo guide template

    Generates a comprehensive demo guide including:
    - Executive summary
    - Pain point analysis
    - Demo flow and talk track
    - Technical insights
    - Business value propositions
    """
    # Template from lines 1411-?
    return """# TODO: Extract demo guide template"""


def get_simple_demo_guide_template(config: Dict[str, Any]) -> str:
    """Get the simple demo guide template (fallback)

    A minimal guide template for quick demos
    """
    # Template from lines 3182-3215
    return """# TODO: Extract simple demo guide template"""
'''

    with open('src/framework/generation/templates/guide_generator.py', 'w') as f:
        f.write(template)
    print("✅ Created guide_generator.py template module")

def create_agent_metadata_templates():
    """Create the agent metadata templates module"""

    template = '''"""
Agent metadata templates for Elastic Agent Builder integration.

This module provides templates and prompts for generating agent metadata
that enables deployment to the Agent Builder platform.
"""

from typing import Dict, Any, List


def get_agent_instructions_prompt(config: Dict[str, Any],
                                 query_descriptions: List[str],
                                 datasets_info: List[str]) -> str:
    """Generate prompt for creating agent instructions

    Args:
        config: Demo configuration with company context
        query_descriptions: List of query descriptions to inform capabilities
        datasets_info: List of available datasets

    Returns:
        Prompt for LLM to generate comprehensive agent instructions
    """

    company = config.get('company_name', 'Unknown Company')
    department = config.get('department', 'Analytics')
    industry = config.get('industry', 'general')
    pain_points = config.get('pain_points', [])
    use_cases = config.get('use_cases', [])

    # Build the prompt for generating agent instructions
    # This will be extracted from the _generate_agent_instructions method
    return f"""# TODO: Extract agent instructions prompt generation"""
'''

    with open('src/framework/generation/templates/agent_metadata.py', 'w') as f:
        f.write(template)
    print("✅ Created agent_metadata.py template module")

def create_generators_modules():
    """Create the generator utility modules"""

    # Create __init__.py for generators
    init_content = '''"""
Generator utilities for module generation.

This package contains utility modules for generating various
components of demo modules.
"""

from .static_files import StaticFileGenerator
from .config_generator import ConfigGenerator
from .code_extractor import CodeExtractor

__all__ = [
    'StaticFileGenerator',
    'ConfigGenerator',
    'CodeExtractor'
]
'''

    os.makedirs('src/framework/generation/generators', exist_ok=True)
    with open('src/framework/generation/generators/__init__.py', 'w') as f:
        f.write(init_content)
    print("✅ Created generators/__init__.py")

    # Create static_files.py
    static_content = '''"""
Static file generation for demo modules.

This module handles generation of static JSON files that are used
for quick loading in the UI without needing to execute Python code.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class StaticFileGenerator:
    """Generates static JSON files for demo modules"""

    def generate_static_files(self, module_path: Path) -> None:
        """Generate all static files for a module

        This method will be extracted from module_generator._generate_static_files
        Lines approximately 2228-2293
        """
        # TODO: Extract implementation from module_generator.py
        pass

    def generate_all_queries_file(self, module_path: Path) -> None:
        """Generate all_queries.json combining all query types"""
        # TODO: Extract implementation
        pass
'''

    with open('src/framework/generation/generators/static_files.py', 'w') as f:
        f.write(static_content)
    print("✅ Created static_files.py")

    # Create config_generator.py
    config_content = '''"""
Configuration file generation for demo modules.

This module handles generation of config.json files that store
the demo context and metadata.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ConfigGenerator:
    """Generates configuration files for demo modules"""

    def generate_config_file(self, config: Dict[str, Any], module_path: Path) -> None:
        """Generate config.json for the module

        This will be extracted from module_generator._generate_config_file
        Lines approximately 2284-2293
        """
        # TODO: Extract implementation from module_generator.py
        pass
'''

    with open('src/framework/generation/generators/config_generator.py', 'w') as f:
        f.write(config_content)
    print("✅ Created config_generator.py")

    # Create code_extractor.py
    extractor_content = '''"""
Code extraction utilities for module generation.

This module handles extraction and validation of generated Python code
from LLM responses.
"""

import ast
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class CodeExtractor:
    """Extracts and validates Python code from LLM responses"""

    def extract_python_code(self, response: str) -> str:
        """Extract Python code from LLM response

        This will be extracted from module_generator._extract_python_code
        Lines approximately 253-295
        """
        # TODO: Extract implementation from module_generator.py
        pass

    def validate_python_syntax(self, code: str, filename: str = 'generated.py') -> bool:
        """Validate Python syntax using ast.parse"""
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            logger.error(f"Syntax error in {filename}: {e}")
            return False
'''

    with open('src/framework/generation/generators/code_extractor.py', 'w') as f:
        f.write(extractor_content)
    print("✅ Created code_extractor.py")

def create_main_init():
    """Create the main __init__.py for the generation package"""

    init_content = '''"""
Module generation framework - refactored from monolithic module_generator.py

This package provides a modular approach to generating demo modules,
breaking down the original 3,368-line file into logical components.
"""

from .module_generator import ModuleGenerator

# Maintain backward compatibility - everything imports from here
__all__ = ['ModuleGenerator']
'''

    with open('src/framework/generation/__init__.py', 'w') as f:
        f.write(init_content)
    print("✅ Created generation/__init__.py")

def main():
    """Run the refactoring process"""
    print("🚀 Starting module_generator.py refactoring...")
    print("=" * 60)

    # Create directory structure
    os.makedirs('src/framework/generation/templates', exist_ok=True)
    os.makedirs('src/framework/generation/generators', exist_ok=True)
    os.makedirs('src/framework/generation/deprecated', exist_ok=True)
    print("✅ Created directory structure")

    # Create template modules
    create_data_generator_templates()
    create_query_generator_templates()
    create_guide_generator_templates()
    create_agent_metadata_templates()

    # Create generator utility modules
    create_generators_modules()

    # Create main __init__.py
    create_main_init()

    print("=" * 60)
    print("✅ Created all template files with TODO markers")
    print("\nNext steps:")
    print("1. Extract actual template code from module_generator.py")
    print("2. Move methods to appropriate modules")
    print("3. Create slim module_generator.py that imports from submodules")
    print("4. Test the refactored structure")

if __name__ == "__main__":
    main()