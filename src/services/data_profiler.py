"""
Data Profiler Service
Profiles indexed data using ES|QL queries to extract field values, statistics, and cardinalities.
This information is used to guide query generation and ensure queries return results.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DataProfiler:
    """Profile indexed data to understand field values and distributions"""

    def __init__(self, es_client):
        """Initialize the profiler with an Elasticsearch client

        Args:
            es_client: ElasticsearchClient instance
        """
        self.es_client = es_client
        self.max_unique_values = 100

    def profile_datasets(
        self,
        datasets: Dict[str, Any],
        demo_path: Path,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Profile all datasets and save results

        Args:
            datasets: Dictionary of dataset_name -> DataFrame
            demo_path: Path to demo directory
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with profiling results
        """
        profile = {
            "generated_at": datetime.now().isoformat(),
            "datasets": {}
        }

        total_datasets = len(datasets)

        for i, (dataset_name, df) in enumerate(datasets.items(), 1):
            if progress_callback:
                progress_callback(f"Profiling {dataset_name}... ({i}/{total_datasets})")

            logger.info(f"Profiling dataset: {dataset_name}")

            try:
                dataset_profile = self._profile_dataset(dataset_name, df)
                profile["datasets"][dataset_name] = dataset_profile
            except Exception as e:
                logger.error(f"Error profiling {dataset_name}: {e}")
                profile["datasets"][dataset_name] = {
                    "error": str(e),
                    "total_records": len(df)
                }

        # Save profile to file
        profile_path = demo_path / "data_profile.json"
        with open(profile_path, 'w') as f:
            json.dump(profile, f, indent=2)

        logger.info(f"Data profile saved to {profile_path}")

        if progress_callback:
            progress_callback(f"✅ Profiling complete - {total_datasets} datasets profiled")

        return profile

    def _profile_dataset(self, dataset_name: str, df) -> Dict[str, Any]:
        """Profile a single dataset

        Args:
            dataset_name: Name of the dataset/index
            df: DataFrame with the data (used for field type detection)

        Returns:
            Dictionary with profiling information
        """
        profile = {
            "total_records": len(df),
            "fields": {},
            "sample_combinations": []
        }

        # Get field types from DataFrame
        field_types = {
            col: str(df[col].dtype)
            for col in df.columns
        }

        # Profile each field
        for field_name, field_type in field_types.items():
            try:
                field_profile = self._profile_field(dataset_name, field_name, field_type)
                if field_profile:
                    profile["fields"][field_name] = field_profile
            except Exception as e:
                logger.warning(f"Could not profile {dataset_name}.{field_name}: {e}")

        # Get sample combinations for multi-field queries
        try:
            combinations = self._get_sample_combinations(dataset_name, df)
            profile["sample_combinations"] = combinations
        except Exception as e:
            logger.warning(f"Could not get combinations for {dataset_name}: {e}")

        return profile

    def _profile_field(
        self,
        dataset_name: str,
        field_name: str,
        field_type: str
    ) -> Optional[Dict[str, Any]]:
        """Profile a single field using ES|QL

        Args:
            dataset_name: Name of the index
            field_name: Name of the field
            field_type: Data type of the field

        Returns:
            Dictionary with field profiling info or None if error
        """
        field_profile = {
            "type": field_type
        }

        # For text/keyword fields, get unique values
        if 'object' in field_type or 'str' in field_type or 'category' in field_type:
            query = f"""
FROM {dataset_name}
| STATS unique_values = VALUES({field_name})
| LIMIT 1
"""
            try:
                result = self.es_client.execute_esql(query)
                if result and 'values' in result and result['values']:
                    values = result['values'][0][0] if result['values'] else []
                    # Limit to max_unique_values
                    if len(values) > self.max_unique_values:
                        values = values[:self.max_unique_values]
                        field_profile["truncated"] = True
                    field_profile["unique_values"] = values
                    field_profile["cardinality"] = len(values)
            except Exception as e:
                logger.debug(f"Could not get unique values for {field_name}: {e}")

        # For numeric fields, get min/max/avg
        elif 'int' in field_type or 'float' in field_type:
            query = f"""
FROM {dataset_name}
| STATS
    min_val = MIN({field_name}),
    max_val = MAX({field_name}),
    avg_val = AVG({field_name})
"""
            try:
                result = self.es_client.execute_esql(query)
                if result and 'values' in result and result['values']:
                    min_val, max_val, avg_val = result['values'][0]
                    field_profile["min"] = min_val
                    field_profile["max"] = max_val
                    field_profile["avg"] = avg_val
            except Exception as e:
                logger.debug(f"Could not get stats for {field_name}: {e}")

        # For datetime fields, get min/max
        elif 'datetime' in field_type:
            query = f"""
FROM {dataset_name}
| STATS
    min_date = MIN({field_name}),
    max_date = MAX({field_name})
"""
            try:
                result = self.es_client.execute_esql(query)
                if result and 'values' in result and result['values']:
                    min_date, max_date = result['values'][0]
                    field_profile["min_date"] = str(min_date)
                    field_profile["max_date"] = str(max_date)
            except Exception as e:
                logger.debug(f"Could not get date range for {field_name}: {e}")

        return field_profile if len(field_profile) > 1 else None

    def _get_sample_combinations(
        self,
        dataset_name: str,
        df,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get sample field value combinations for multi-criteria queries

        This helps identify realistic multi-field filter combinations.
        For example, for providers: (specialty=Cardiology, state=CA, network_status=In-Network)

        Args:
            dataset_name: Name of the index
            df: DataFrame to analyze
            limit: Maximum number of combinations to return

        Returns:
            List of sample field combinations
        """
        combinations = []

        # Identify categorical fields (strings with low cardinality)
        categorical_fields = []
        for col in df.columns:
            if df[col].dtype == 'object' or str(df[col].dtype) == 'category':
                unique_count = df[col].nunique()
                if 2 <= unique_count <= 50:  # Sweet spot for categorical
                    categorical_fields.append(col)

        # Limit to 3-4 most interesting fields
        categorical_fields = categorical_fields[:4]

        if not categorical_fields:
            return combinations

        # Build ES|QL query to get combinations
        stats_fields = ", ".join(categorical_fields)
        by_clause = ", ".join(categorical_fields)

        query = f"""
FROM {dataset_name}
| STATS record_count = COUNT(*) BY {by_clause}
| SORT record_count DESC
| LIMIT {limit}
| KEEP {stats_fields}, record_count
"""

        try:
            result = self.es_client.execute_esql(query)
            if result and 'values' in result and result['columns']:
                # Parse column names
                column_names = [col['name'] for col in result['columns']]

                # Convert to list of dicts
                for row in result['values']:
                    combination = {}
                    for i, col_name in enumerate(column_names):
                        combination[col_name] = row[i]
                    combinations.append(combination)

        except Exception as e:
            logger.debug(f"Could not get combinations for {dataset_name}: {e}")

        return combinations

    @staticmethod
    def load_profile(demo_path: Path) -> Optional[Dict[str, Any]]:
        """Load data profile from file

        Args:
            demo_path: Path to demo directory

        Returns:
            Profile dictionary or None if not found
        """
        profile_path = demo_path / "data_profile.json"

        if not profile_path.exists():
            return None

        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading profile from {profile_path}: {e}")
            return None

    @staticmethod
    def format_profile_for_llm(profile: Dict[str, Any], compact: bool = True) -> str:
        """Format profile data for LLM consumption with smart sampling

        Args:
            profile: Profile dictionary
            compact: If True, use smart sampling to minimize tokens (default: True)

        Returns:
            Formatted string for LLM prompt (200-500 tokens when compact=True)
        """
        if not profile or "datasets" not in profile:
            return ""

        lines = ["# Data Profile - Actual Field Values\n"]
        lines.append("Use these ACTUAL values from the indexed data when generating queries.\n")

        for dataset_name, dataset_info in profile["datasets"].items():
            if "error" in dataset_info:
                continue

            lines.append(f"\n## {dataset_name} ({dataset_info.get('total_records', 0)} records)")

            # Field values with smart sampling
            if "fields" in dataset_info:
                lines.append("### Fields:")

                for field_name, field_info in dataset_info["fields"].items():
                    # Skip ID fields and timestamps when in compact mode
                    if compact and DataProfiler._should_skip_field(field_name):
                        continue

                    if "unique_values" in field_info:
                        values = field_info["unique_values"]
                        cardinality = field_info.get("cardinality", len(values))

                        # Smart sampling: <20 values = full list, >20 = sample
                        if cardinality <= 20:
                            # Full list for low cardinality fields
                            values_str = ", ".join([f"'{v}'" for v in values])
                            lines.append(f"- **{field_name}**: {values_str}")
                        elif compact:
                            # Compact mode: show first 10 + count
                            sample = values[:10]
                            values_str = ", ".join([f"'{v}'" for v in sample])
                            lines.append(f"- **{field_name}**: {values_str} ... ({cardinality} total)")
                        else:
                            # Non-compact: show more values
                            sample = values[:10]
                            values_str = ", ".join([f"'{v}'" for v in sample])
                            lines.append(f"- **{field_name}**: {values_str}, ... ({cardinality} total)")

                    elif "min" in field_info and "max" in field_info:
                        # Numeric ranges - always compact
                        lines.append(f"- **{field_name}**: {field_info['min']}-{field_info['max']}")

                    elif "min_date" in field_info:
                        # Date ranges - always compact
                        min_date = str(field_info['min_date']).split('T')[0]  # Just date part
                        max_date = str(field_info['max_date']).split('T')[0]
                        lines.append(f"- **{field_name}**: {min_date} to {max_date}")

            # Sample combinations - limit to 3 in compact mode
            if dataset_info.get("sample_combinations"):
                combo_limit = 3 if compact else 5
                lines.append(f"\n### Sample Combinations (guaranteed results):")
                for i, combo in enumerate(dataset_info["sample_combinations"][:combo_limit], 1):
                    # Don't modify original combo
                    combo_copy = combo.copy()
                    record_count = combo_copy.pop('record_count', None)
                    combo_str = " AND ".join([f"{k}='{v}'" for k, v in combo_copy.items()])
                    if record_count and not compact:
                        lines.append(f"{i}. {combo_str} ({record_count} records)")
                    else:
                        lines.append(f"{i}. {combo_str}")

        return "\n".join(lines)

    @staticmethod
    def _should_skip_field(field_name: str) -> bool:
        """Determine if a field should be skipped in compact mode

        Args:
            field_name: Name of the field

        Returns:
            True if field should be skipped
        """
        skip_patterns = [
            '_id', 'id', 'uuid', 'guid',  # ID fields
            'created_at', 'updated_at', 'timestamp', 'date_created', 'date_modified',  # Timestamps
            'created_date', 'modified_date', 'last_updated'
        ]

        field_lower = field_name.lower()
        return any(pattern in field_lower for pattern in skip_patterns)


def profile_indexed_data(
    es_client,
    datasets: Dict[str, Any],
    demo_path: Path,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """Convenience function to profile indexed data

    Args:
        es_client: ElasticsearchClient instance
        datasets: Dictionary of dataset_name -> DataFrame
        demo_path: Path to demo directory
        progress_callback: Optional callback for progress updates

    Returns:
        Profile dictionary
    """
    profiler = DataProfiler(es_client)
    return profiler.profile_datasets(datasets, demo_path, progress_callback)
