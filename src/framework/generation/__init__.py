"""
Module generation framework - refactored from monolithic module_generator.py

This package provides a modular approach to generating demo modules,
breaking down the original 3,368-line file into logical components.
"""

from .module_generator import ModuleGenerator

# Maintain backward compatibility - everything imports from here
__all__ = ['ModuleGenerator']
