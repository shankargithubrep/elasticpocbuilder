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
    """Base class for query generation modules

    Generates three types of queries:
    1. Scripted queries (non-parameterized, tested)
    2. Parameterized queries (Agent Builder tools, LLM-generated)
    3. RAG queries (MATCH → RERANK → COMPLETION pipeline)
    """

    def __init__(self, config: DemoConfig, datasets: Dict[str, pd.DataFrame]):
        """Initialize with config and available datasets"""
        self.config = config
        self.datasets = datasets

    @abstractmethod
    def generate_queries(self) -> List[Dict[str, Any]]:
        """Generate scripted (non-parameterized) ES|QL queries for the demo

        These are fully tested queries with hard-coded values that address
        specific customer pain points. They serve as the foundation for
        parameterized versions.

        Returns:
            List of query definitions with:
            - query_type: "scripted"
            - name: Query name
            - description: What it demonstrates
            - esql: The ES|QL query (no parameters)
            - expected_insight: What the customer will learn
            - tested: True (indicates validation status)
        """
        pass

    def generate_parameterized_queries(self) -> List[Dict[str, Any]]:
        """Generate parameterized versions of scripted queries

        These queries use ?parameter syntax for Agent Builder ES|QL tools.
        They are LLM-generated based on validated scripted queries.

        Note: These are NOT executed in this app - they are tool definitions
        for Agent Builder integration (v2 feature).

        Returns:
            List of parameterized query definitions with:
            - query_type: "parameterized"
            - name: Query name
            - description: What it demonstrates
            - esql: ES|QL query with ?parameter syntax
            - parameters: Dict of parameter definitions with:
                - type: Parameter data type (string, date, keyword[], etc.)
                - description: What the parameter controls
                - default: Default value (from scripted query)
                - required: Boolean
            - base_query: Name of the scripted query this derives from
            - agent_builder_ready: True

        Important: Avoid LIKE and RLIKE operators - they don't support parameters!
        """
        # Default implementation: Return empty list
        # LLM-generated modules will override this with actual parameterized queries
        return []

    def generate_rag_queries(self) -> List[Dict[str, Any]]:
        """Generate RAG queries for semantic search + LLM completion

        These queries implement the MATCH → RERANK → COMPLETION pipeline
        for open-ended question answering via Agent Builder.

        Pipeline:
        1. MATCH/MATCH_PHRASE - Semantic text search (100+ docs)
        2. RERANK (optional) - ML-based relevance scoring (top 5-10 docs)
        3. INLINE STATS - Aggregate context (preserves fields!)
        4. COMPLETION - LLM generates answer from context

        Returns:
            List of RAG query definitions with:
            - query_type: "rag"
            - name: Query name
            - description: What questions it can answer
            - esql: Full MATCH → RERANK → COMPLETION query
            - parameters: Dict with at least:
                - user_question: Required string parameter
            - search_fields: List of text fields for MATCH
            - rerank_fields: List of fields for RERANK (optional)
            - context_fields: List of fields for LLM context
            - time_boundary: Time range (e.g., "120 days")
            - agent_builder_tool: Dict with tool definition metadata

        Critical: Use INLINE STATS not STATS to preserve fields before COMPLETION!
        """
        # Default implementation: Return empty list
        # LLM-generated modules will override this with actual RAG queries
        return []

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