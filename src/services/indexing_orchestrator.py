"""
Indexing Orchestrator
Orchestrates data indexing with retry logic and error recovery
"""

from typing import Dict, List, Optional, Callable
import pandas as pd
import logging
import time
from pathlib import Path

from .elasticsearch_indexer import ElasticsearchIndexer, IndexingResult

logger = logging.getLogger(__name__)


class IndexingOrchestrator:
    """Orchestrates data indexing with retry logic and error handling"""

    def __init__(self, es_indexer: Optional[ElasticsearchIndexer] = None):
        """Initialize with optional Elasticsearch indexer

        Args:
            es_indexer: Optional ElasticsearchIndexer instance (creates new if None)
        """
        self.indexer = es_indexer or ElasticsearchIndexer()
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def index_all_datasets(
        self,
        datasets: Dict[str, pd.DataFrame],
        semantic_fields: Dict[str, List[str]],
        index_modes: Optional[Dict[str, str]] = None,
        progress_callback: Optional[Callable] = None,
        text_fields: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Dict]:
        """Index all datasets with retry logic

        Args:
            datasets: Dictionary mapping dataset names to DataFrames
            semantic_fields: Dictionary mapping dataset names to semantic field lists
            index_modes: Optional dictionary mapping dataset names to index modes ('data_stream' or 'lookup')
            progress_callback: Optional progress callback function(progress, message)
            text_fields: Optional dictionary mapping dataset names to fields needing 'text' type
                         (for full-text search with MATCH). Extracted from query strategy.

        Returns:
            Dictionary with indexing results for each dataset
        """
        results = {}
        total = len(datasets)

        logger.info(f"Starting indexing of {total} datasets")
        if text_fields:
            logger.info(f"Text fields for full-text search: {text_fields}")

        for idx, (name, df) in enumerate(datasets.items()):
            # Calculate progress (50-100% range, assuming data gen was 0-50%)
            if progress_callback:
                progress = 0.5 + (idx / total) * 0.3  # 50-80% range
                progress_callback(progress, f"🔍 Indexing {name}...")

            # Get semantic fields for this dataset
            dataset_semantic_fields = semantic_fields.get(name, [])

            # Get text fields for this dataset (for MATCH queries)
            dataset_text_fields = text_fields.get(name, []) if text_fields else []

            # Get index mode for this dataset (if provided)
            dataset_index_mode = None
            if index_modes:
                dataset_index_mode = index_modes.get(name)

            # Try indexing with retries
            result = self._index_with_retry(
                name,
                df,
                dataset_semantic_fields,
                dataset_index_mode,
                progress_callback,
                dataset_text_fields
            )

            results[name] = result

            if result['status'] == 'success':
                logger.info(f"Successfully indexed {name}: {result['doc_count']} documents")
            else:
                logger.error(f"Failed to index {name} after {result['attempts']} attempts: {result.get('error')}")

        return results

    def _index_with_retry(
        self,
        dataset_name: str,
        df: pd.DataFrame,
        semantic_fields: List[str],
        index_mode: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
        text_fields: Optional[List[str]] = None
    ) -> Dict:
        """Index a dataset with retry logic

        Args:
            dataset_name: Name of the dataset
            df: DataFrame to index
            semantic_fields: List of semantic field names
            index_mode: Optional explicit index mode ('data_stream' or 'lookup')
            progress_callback: Optional progress callback
            text_fields: Optional list of fields needing 'text' type for full-text search

        Returns:
            Result dictionary with status, index_name, doc_count, attempts, error
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Indexing {dataset_name} (attempt {attempt + 1}/{self.max_retries})")
                if text_fields:
                    logger.info(f"Text fields for {dataset_name}: {text_fields}")

                # Try to index
                result: IndexingResult = self.indexer.index_dataset(
                    df=df,
                    dataset_name=dataset_name,
                    semantic_fields=semantic_fields,
                    text_fields=text_fields,
                    index_mode=index_mode,
                    progress_callback=progress_callback
                )

                if result.success:
                    return {
                        'status': 'success',
                        'index_name': result.index_name,
                        'index_type': result.index_type,
                        'doc_count': result.documents_indexed,
                        'semantic_fields': result.semantic_fields,
                        'duration': result.duration_seconds,
                        'attempts': attempt + 1
                    }
                else:
                    # Indexing returned but wasn't successful
                    logger.warning(f"Indexing {dataset_name} failed: {result.errors}")

                    # Try to fix common issues
                    if attempt < self.max_retries - 1:
                        df = self._fix_indexing_issues(df, result.errors)
                        time.sleep(self.retry_delay)
                    else:
                        return {
                            'status': 'failed',
                            'error': '; '.join(result.errors),
                            'attempts': attempt + 1
                        }

            except Exception as e:
                logger.error(f"Error indexing {dataset_name}: {e}", exc_info=True)

                if attempt < self.max_retries - 1:
                    # Try to fix and retry
                    df = self._fix_common_errors(df, str(e))
                    time.sleep(self.retry_delay)
                else:
                    return {
                        'status': 'failed',
                        'error': str(e),
                        'attempts': attempt + 1
                    }

        # Should never reach here, but just in case
        return {
            'status': 'failed',
            'error': 'Max retries exceeded',
            'attempts': self.max_retries
        }

    def _fix_indexing_issues(self, df: pd.DataFrame, errors: List[str]) -> pd.DataFrame:
        """Attempt to fix common indexing issues

        Args:
            df: DataFrame with issues
            errors: List of error messages

        Returns:
            Fixed DataFrame
        """
        df = df.copy()

        for error in errors:
            error_lower = error.lower()

            # Fix timestamp issues
            if 'timestamp' in error_lower:
                df = self._fix_timestamp_fields(df)

            # Fix null values
            elif 'null' in error_lower or 'missing' in error_lower:
                df = self._fix_null_values(df)

            # Fix type issues
            elif 'type' in error_lower or 'mapping' in error_lower:
                df = self._fix_type_issues(df)

        return df

    def _fix_common_errors(self, df: pd.DataFrame, error: str) -> pd.DataFrame:
        """Fix common errors that cause exceptions

        Args:
            df: DataFrame with issues
            error: Error message

        Returns:
            Fixed DataFrame
        """
        df = df.copy()

        error_lower = error.lower()

        # Fix timestamp issues
        if 'timestamp' in error_lower or 'date' in error_lower:
            df = self._fix_timestamp_fields(df)

        # Fix encoding issues
        elif 'encoding' in error_lower or 'unicode' in error_lower:
            df = self._fix_encoding_issues(df)

        # Fix null/NaN issues
        elif 'nan' in error_lower or 'null' in error_lower:
            df = self._fix_null_values(df)

        return df

    def _fix_timestamp_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fix timestamp-related issues

        Args:
            df: DataFrame to fix

        Returns:
            Fixed DataFrame
        """
        df = df.copy()

        # Look for timestamp columns
        timestamp_cols = [col for col in df.columns if 'timestamp' in col.lower() or 'time' in col.lower() or 'date' in col.lower()]

        for col in timestamp_cols:
            try:
                # Ensure it's datetime
                if not pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = pd.to_datetime(df[col], errors='coerce')

                # Rename to @timestamp if it's called timestamp
                if col == 'timestamp':
                    df['@timestamp'] = df[col]
                    df = df.drop('timestamp', axis=1)
                    logger.info("Renamed 'timestamp' to '@timestamp'")

            except Exception as e:
                logger.warning(f"Could not fix timestamp column {col}: {e}")

        return df

    def _fix_null_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fix null value issues

        Args:
            df: DataFrame to fix

        Returns:
            Fixed DataFrame
        """
        df = df.copy()

        for col in df.columns:
            if df[col].dtype == 'object':
                # Replace NaN in string columns with empty string
                df[col] = df[col].fillna('')
            elif pd.api.types.is_numeric_dtype(df[col]):
                # Replace NaN in numeric columns with 0
                df[col] = df[col].fillna(0)

        return df

    def _fix_type_issues(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fix data type issues

        Args:
            df: DataFrame to fix

        Returns:
            Fixed DataFrame
        """
        df = df.copy()

        for col in df.columns:
            # Convert object columns to string
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str)

            # Ensure numeric columns are proper types
            elif pd.api.types.is_integer_dtype(df[col]):
                df[col] = df[col].astype('int64')
            elif pd.api.types.is_float_dtype(df[col]):
                df[col] = df[col].astype('float64')

        return df

    def _fix_encoding_issues(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fix encoding issues in string columns

        Args:
            df: DataFrame to fix

        Returns:
            Fixed DataFrame
        """
        df = df.copy()

        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    # Encode to ASCII, replace errors
                    df[col] = df[col].apply(
                        lambda x: str(x).encode('ascii', 'ignore').decode('ascii') if pd.notna(x) else ''
                    )
                except Exception as e:
                    logger.warning(f"Could not fix encoding for column {col}: {e}")

        return df

    def get_indexed_datasets(self) -> Dict[str, str]:
        """Get list of currently indexed datasets

        Returns:
            Dictionary mapping dataset names to index names
        """
        # This would query Elasticsearch for available indices
        # For now, return empty dict
        return {}

    def cleanup_old_indices(self, prefix: str = "demo_", keep_recent: int = 5):
        """Clean up old demo indices to save space

        Args:
            prefix: Index name prefix to target
            keep_recent: Number of recent indices to keep
        """
        # This would implement cleanup logic
        # Not implementing now to avoid accidental deletions
        logger.info(f"Cleanup requested for prefix={prefix}, keeping {keep_recent} recent")
        pass
