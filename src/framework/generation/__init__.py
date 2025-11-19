"""
Module generation framework - refactored from monolithic module_generator.py

This package provides a modular approach to generating demo modules,
breaking down the original 3,368-line file into logical components.

Template modules are organized under templates/:
- query_generator.py: Query generation prompts and assembly
- agent_metadata.py: Agent metadata generation
- guide_generator.py: Demo guide generation
- data_generator.py: Data generation templates
"""

# Note: ModuleGenerator remains in parent module_generator.py
# Import templates as needed from src.framework.generation.templates.*

__all__ = [
    'templates',  # Template subpackage
]
