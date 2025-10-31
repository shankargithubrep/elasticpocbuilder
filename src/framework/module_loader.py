"""
Module Loader for Demo Builder
Dynamically loads and executes demo modules
"""

import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import logging
import pandas as pd

from .base import DemoConfig

logger = logging.getLogger(__name__)


class ModuleLoader:
    """Loads and executes demo modules"""

    def __init__(self, module_path: str):
        """Initialize with path to demo module

        Args:
            module_path: Path to the demo module directory
        """
        self.module_path = Path(module_path)
        self.config = self._load_config()
        self.demo_config = self._create_demo_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load module configuration"""
        config_file = self.module_path / 'config.json'
        if config_file.exists():
            return json.loads(config_file.read_text())
        else:
            raise FileNotFoundError(f"Config file not found in {self.module_path}")

    def _create_demo_config(self) -> DemoConfig:
        """Create DemoConfig from module configuration"""
        context = self.config.get('customer_context', {})
        return DemoConfig(
            company_name=context.get('company_name', ''),
            department=context.get('department', ''),
            industry=context.get('industry', ''),
            pain_points=context.get('pain_points', []),
            use_cases=context.get('use_cases', []),
            scale=context.get('scale', ''),
            metrics=context.get('metrics', [])
        )

    def load_data_generator(self):
        """Load and instantiate the data generator module"""
        module = self._load_module('data_generator')

        # Find the DataGeneratorModule subclass
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and
                    name != 'DataGeneratorModule' and
                    'DataGenerator' in name):
                return obj(self.demo_config)

        raise ImportError("No DataGeneratorModule implementation found")

    def load_query_generator(self, datasets: Dict[str, pd.DataFrame]):
        """Load and instantiate the query generator module"""
        module = self._load_module('query_generator')

        # Find the QueryGeneratorModule subclass
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and
                    name != 'QueryGeneratorModule' and
                    'QueryGenerator' in name):
                return obj(self.demo_config, datasets)

        raise ImportError("No QueryGeneratorModule implementation found")

    def load_demo_guide(self, datasets: Dict[str, pd.DataFrame], queries: list):
        """Load and instantiate the demo guide module"""
        module = self._load_module('demo_guide')

        # Find the DemoGuideModule subclass
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, type) and
                    name != 'DemoGuideModule' and
                    'DemoGuide' in name):
                return obj(self.demo_config, datasets, queries)

        raise ImportError("No DemoGuideModule implementation found")

    def _load_module(self, module_name: str):
        """Dynamically load a Python module from file

        Args:
            module_name: Name of the module file (without .py)

        Returns:
            Loaded module object
        """
        module_file = self.module_path / f'{module_name}.py'

        if not module_file.exists():
            raise FileNotFoundError(f"Module {module_name} not found in {self.module_path}")

        # Create module spec
        spec = importlib.util.spec_from_file_location(
            f"demo_modules.{self.module_path.name}.{module_name}",
            module_file
        )

        if spec is None:
            raise ImportError(f"Could not load module from {module_file}")

        # Load the module
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        return module

    def execute_demo(self, progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """Execute the complete demo using loaded modules

        Args:
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with all demo artifacts
        """
        results = {}

        try:
            # Step 1: Generate data
            if progress_callback:
                progress_callback(0.2, "🏗️ Generating datasets...")

            data_generator = self.load_data_generator()
            datasets = data_generator.generate_datasets()
            relationships = data_generator.get_relationships()
            data_descriptions = data_generator.get_data_descriptions()

            results['datasets'] = datasets
            results['relationships'] = relationships
            results['data_descriptions'] = data_descriptions

            logger.info(f"Generated {len(datasets)} datasets")

            # Step 2: Generate queries (all three types)
            if progress_callback:
                progress_callback(0.5, "🔍 Creating ES|QL queries...")

            query_generator = self.load_query_generator(datasets)

            # Generate scripted queries (tested, non-parameterized)
            scripted_queries = query_generator.generate_queries()

            # Generate parameterized queries (Agent Builder tools)
            parameterized_queries = query_generator.generate_parameterized_queries()

            # Generate RAG queries (MATCH → RERANK → COMPLETION)
            rag_queries = query_generator.generate_rag_queries()

            query_progression = query_generator.get_query_progression()

            # Store queries organized by type
            results['queries'] = {
                'scripted': scripted_queries,
                'parameterized': parameterized_queries,
                'rag': rag_queries
            }
            results['all_queries'] = scripted_queries + parameterized_queries + rag_queries
            results['query_progression'] = query_progression

            logger.info(
                f"Generated {len(scripted_queries)} scripted, "
                f"{len(parameterized_queries)} parameterized, "
                f"{len(rag_queries)} RAG queries"
            )

            # Step 3: Generate demo guide
            if progress_callback:
                progress_callback(0.8, "📝 Creating demo guide...")

            # Pass all queries to demo guide generator
            demo_guide = self.load_demo_guide(datasets, results['all_queries'])
            guide_text = demo_guide.generate_guide()
            talk_track = demo_guide.get_talk_track()
            objections = demo_guide.get_objection_handling()

            results['demo_guide'] = guide_text
            results['talk_track'] = talk_track
            results['objection_handling'] = objections

            if progress_callback:
                progress_callback(1.0, "✅ Demo ready!")

            logger.info("Demo execution complete")

        except Exception as e:
            logger.error(f"Error executing demo: {e}")
            raise

        return results


class DemoModuleManager:
    """Manages all demo modules in the repository"""

    def __init__(self, base_path: str = "demos"):
        """Initialize with base path for demo modules"""
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

    def list_modules(self) -> List[Dict[str, Any]]:
        """List all available demo modules

        Returns:
            List of module information dictionaries
        """
        modules = []

        for module_dir in self.base_path.iterdir():
            if module_dir.is_dir():
                config_file = module_dir / 'config.json'
                if config_file.exists():
                    config = json.loads(config_file.read_text())
                    modules.append({
                        'name': module_dir.name,
                        'path': str(module_dir),
                        'created_at': config.get('generated_at'),
                        'customer': config.get('customer_context', {}).get('company_name'),
                        'department': config.get('customer_context', {}).get('department')
                    })

        return sorted(modules, key=lambda x: x.get('created_at', ''), reverse=True)

    def get_module(self, module_name: str) -> Optional[ModuleLoader]:
        """Get a specific module loader

        Args:
            module_name: Name of the module directory

        Returns:
            ModuleLoader instance or None if not found
        """
        module_path = self.base_path / module_name

        if module_path.exists():
            return ModuleLoader(str(module_path))

        return None

    def delete_module(self, module_name: str) -> bool:
        """Delete a demo module

        Args:
            module_name: Name of the module to delete

        Returns:
            True if deleted, False if not found
        """
        module_path = self.base_path / module_name

        if module_path.exists():
            import shutil
            shutil.rmtree(module_path)
            logger.info(f"Deleted module: {module_name}")
            return True

        return False