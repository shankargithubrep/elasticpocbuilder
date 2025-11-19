"""
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
