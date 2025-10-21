"""
Modular Demo Orchestrator
Orchestrates demo generation using the modular framework
"""

from typing import Dict, Any, Optional
from pathlib import Path
import logging

from .module_generator import ModuleGenerator
from .module_loader import ModuleLoader, DemoModuleManager
from .base import DemoConfig

logger = logging.getLogger(__name__)


class ModularDemoOrchestrator:
    """Orchestrates demo generation using modular architecture"""

    def __init__(self, llm_client=None):
        """Initialize orchestrator

        Args:
            llm_client: Optional LLM client for module generation
        """
        self.module_generator = ModuleGenerator(llm_client)
        self.module_manager = DemoModuleManager()

    def generate_new_demo(
        self,
        config: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Generate a new demo module and execute it

        Args:
            config: Demo configuration
            progress_callback: Optional progress callback

        Returns:
            Demo results including module path
        """
        # Step 1: Generate the module
        if progress_callback:
            progress_callback(0.1, "🤖 Generating custom demo module...")

        module_path = self.module_generator.generate_demo_module(config)

        # Step 2: Load and execute the module
        if progress_callback:
            progress_callback(0.3, "📦 Loading demo module...")

        loader = ModuleLoader(module_path)
        results = loader.execute_demo(progress_callback)

        # Add module information to results
        results['module_path'] = module_path
        results['module_name'] = Path(module_path).name

        logger.info(f"Demo generated and executed: {module_path}")

        return results

    def execute_existing_demo(
        self,
        module_name: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Execute an existing demo module

        Args:
            module_name: Name of the module to execute
            progress_callback: Optional progress callback

        Returns:
            Demo results
        """
        loader = self.module_manager.get_module(module_name)

        if loader is None:
            raise ValueError(f"Module '{module_name}' not found")

        results = loader.execute_demo(progress_callback)
        results['module_name'] = module_name

        return results

    def list_available_demos(self) -> list:
        """List all available demo modules

        Returns:
            List of available demos
        """
        return self.module_manager.list_modules()

    def regenerate_module_component(
        self,
        module_name: str,
        component: str,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Regenerate a specific component of an existing module

        Args:
            module_name: Name of the module
            component: Component to regenerate ('data', 'queries', 'guide')
            config: Optional updated configuration

        Returns:
            True if successful
        """
        loader = self.module_manager.get_module(module_name)

        if loader is None:
            raise ValueError(f"Module '{module_name}' not found")

        # Load existing config if not provided
        if config is None:
            config = loader.config.get('customer_context', {})

        module_path = Path(loader.module_path)

        # Regenerate the specific component
        if component == 'data':
            self.module_generator._generate_data_module(config, module_path)
        elif component == 'queries':
            self.module_generator._generate_query_module(config, module_path)
        elif component == 'guide':
            self.module_generator._generate_guide_module(config, module_path)
        else:
            raise ValueError(f"Unknown component: {component}")

        logger.info(f"Regenerated {component} for module {module_name}")
        return True

    def export_module(self, module_name: str, export_path: str) -> str:
        """Export a demo module as a standalone package

        Args:
            module_name: Name of the module to export
            export_path: Path where to export

        Returns:
            Path to exported package
        """
        import shutil
        import json

        loader = self.module_manager.get_module(module_name)

        if loader is None:
            raise ValueError(f"Module '{module_name}' not found")

        # Create export directory
        export_dir = Path(export_path) / module_name
        export_dir.mkdir(parents=True, exist_ok=True)

        # Copy module files
        shutil.copytree(loader.module_path, export_dir, dirs_exist_ok=True)

        # Add README
        readme_content = f"""# Demo Module: {module_name}

## Customer Context
{json.dumps(loader.config.get('customer_context', {}), indent=2)}

## Components
- `data_generator.py`: Generates demo datasets
- `query_generator.py`: Creates ES|QL queries
- `demo_guide.py`: Produces demo guide and talk track
- `config.json`: Module configuration

## Usage
```python
from src.framework.module_loader import ModuleLoader

loader = ModuleLoader('{module_name}')
results = loader.execute_demo()
```

## Customization
Each component can be edited independently to refine the demo.
"""

        (export_dir / 'README.md').write_text(readme_content)

        logger.info(f"Exported module to {export_dir}")
        return str(export_dir)


# Convenience functions for common operations

def create_demo(config: Dict[str, Any], llm_client=None) -> Dict[str, Any]:
    """Create a new demo module

    Args:
        config: Demo configuration
        llm_client: Optional LLM client

    Returns:
        Demo results
    """
    orchestrator = ModularDemoOrchestrator(llm_client)
    return orchestrator.generate_new_demo(config)


def run_demo(module_name: str) -> Dict[str, Any]:
    """Run an existing demo module

    Args:
        module_name: Name of the demo module

    Returns:
        Demo results
    """
    orchestrator = ModularDemoOrchestrator()
    return orchestrator.execute_existing_demo(module_name)


def list_demos() -> list:
    """List all available demos

    Returns:
        List of demo modules
    """
    orchestrator = ModularDemoOrchestrator()
    return orchestrator.list_available_demos()