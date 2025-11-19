"""
Configuration file generation for demo modules.

This module handles generation of config.json files that store
the demo context and metadata.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ConfigGenerator:
    """Generates configuration files for demo modules"""

    @staticmethod
    def generate_config_file(config: Dict[str, Any], module_path: Path) -> None:
        """Generate module configuration file (config.json).

        Creates a JSON configuration file that stores all customer context,
        metadata, and module component information. This file is used by the
        UI and module loader to understand the demo configuration.

        Args:
            config: Customer context dict containing:
                - company_name: Company name
                - department: Department
                - industry: Industry
                - pain_points: List of pain points
                - use_cases: List of use cases
                - scale: Scale/size preference
                - metrics: List of metrics
                - demo_type: 'search' or 'analytics' (optional, defaults to 'analytics')
            module_path: Path to the demo module directory

        Returns:
            None (writes to module_path/config.json)

        Example:
            >>> from pathlib import Path
            >>> config = {
            ...     'company_name': 'Acme Corp',
            ...     'department': 'Sales',
            ...     'industry': 'Technology',
            ...     'pain_points': ['slow queries'],
            ...     'use_cases': ['reporting'],
            ...     'scale': '10000',
            ...     'metrics': ['revenue'],
            ...     'demo_type': 'analytics'
            ... }
            >>> module_path = Path('demos/test_module')
            >>> module_path.mkdir(exist_ok=True)
            >>> ConfigGenerator.generate_config_file(config, module_path)
            >>> config_file = module_path / 'config.json'
            >>> config_file.exists()
            True
        """
        # Extract demo_type to top level for visibility
        demo_type = config.get('demo_type', 'analytics')

        config_data = {
            "_comment": "demo_type: 'search' (document retrieval/RAG) or 'analytics' (metrics/trends)",
            "demo_type": demo_type,
            "module_version": "1.0.0",
            "generated_at": datetime.now().isoformat(),
            "customer_context": config,
            "module_components": {
                "data_generator": "data_generator.py",
                "query_generator": "query_generator.py",
                "demo_guide": "demo_guide.py"
            }
        }

        config_file = module_path / 'config.json'
        config_file.write_text(json.dumps(config_data, indent=2))
        logger.info(f"✓ Generated config.json at {config_file}")

