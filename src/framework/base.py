"""
Base Framework Classes for Demo Builder
Provides interfaces that demo modules must implement
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import pandas as pd
from dataclasses import dataclass


@dataclass
class DemoConfig:
    """Configuration for a demo module"""
    company_name: str
    department: str
    industry: str
    pain_points: List[str]
    use_cases: List[str]
    scale: str
    metrics: List[str]


class DataGeneratorModule(ABC):
    """Base class for data generation modules"""

    def __init__(self, config: DemoConfig):
        """Initialize with demo configuration"""
        self.config = config

    @abstractmethod
    def generate_datasets(self) -> Dict[str, pd.DataFrame]:
        """Generate all datasets for the demo

        Returns:
            Dictionary mapping dataset names to DataFrames
        """
        pass

    @abstractmethod
    def get_relationships(self) -> List[tuple]:
        """Define relationships between datasets

        Returns:
            List of tuples (source_table, foreign_key, target_table)
        """
        pass

    @abstractmethod
    def get_data_descriptions(self) -> Dict[str, str]:
        """Provide descriptions of each dataset

        Returns:
            Dictionary mapping dataset names to descriptions
        """
        pass


class QueryGeneratorModule(ABC):
    """Base class for query generation modules"""

    def __init__(self, config: DemoConfig, datasets: Dict[str, pd.DataFrame]):
        """Initialize with config and available datasets"""
        self.config = config
        self.datasets = datasets

    @abstractmethod
    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate ES|QL queries for the demo

        Returns:
            List of query definitions with:
            - name: Query name
            - description: What it demonstrates
            - esql: The ES|QL query
            - expected_insight: What the customer will learn
        """
        pass

    @abstractmethod
    def get_query_progression(self) -> List[str]:
        """Define the order to present queries

        Returns:
            List of query names in presentation order
        """
        pass


class AhaMomentModule(ABC):
    """Base class for A-ha moment generation"""

    def __init__(self, config: DemoConfig, datasets: Dict[str, pd.DataFrame], queries: List[Dict]):
        """Initialize with full context"""
        self.config = config
        self.datasets = datasets
        self.queries = queries

    @abstractmethod
    def generate_aha_moment(self) -> Dict[str, Any]:
        """Generate the A-ha moment configuration

        Returns:
            Dictionary with:
            - setup: How to set up the moment
            - reveal: The reveal moment
            - impact: Business impact statement
            - query: Specific ES|QL query to run
            - data_preparation: Any special data prep needed
        """
        pass


class DemoGuideModule(ABC):
    """Base class for demo guide generation"""

    def __init__(self, config: DemoConfig, datasets: Dict[str, pd.DataFrame],
                 queries: List[Dict], aha_moment: Optional[Dict] = None):
        """Initialize with full demo context"""
        self.config = config
        self.datasets = datasets
        self.queries = queries
        self.aha_moment = aha_moment

    @abstractmethod
    def generate_guide(self) -> str:
        """Generate the demo guide document

        Returns:
            Markdown-formatted demo guide
        """
        pass

    @abstractmethod
    def get_talk_track(self) -> Dict[str, str]:
        """Generate talk track for each query

        Returns:
            Dictionary mapping query names to talk track
        """
        pass

    @abstractmethod
    def get_objection_handling(self) -> Dict[str, str]:
        """Generate objection handling responses

        Returns:
            Dictionary mapping common objections to responses
        """
        pass