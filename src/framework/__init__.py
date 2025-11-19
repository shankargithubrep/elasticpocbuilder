"""
Demo Builder Framework
Modular architecture for generating customer-specific demos
"""

from .base import (
    DemoConfig,
    DataGeneratorModule,
    QueryGeneratorModule,
    AhaMomentModule,
    DemoGuideModule
)

from .generation.module_generator import ModuleGenerator
from .module_loader import ModuleLoader, DemoModuleManager
from .orchestrator import (
    ModularDemoOrchestrator,
    create_demo,
    run_demo,
    list_demos
)

__all__ = [
    # Base classes
    'DemoConfig',
    'DataGeneratorModule',
    'QueryGeneratorModule',
    'AhaMomentModule',
    'DemoGuideModule',

    # Module management
    'ModuleGenerator',
    'ModuleLoader',
    'DemoModuleManager',

    # Orchestration
    'ModularDemoOrchestrator',
    'create_demo',
    'run_demo',
    'list_demos'
]