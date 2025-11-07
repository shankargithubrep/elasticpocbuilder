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
            es_client: ElasticsearchClient instance (can be ElasticsearchIndexer)
        """
        self.es_client = es_client
        self.max_unique_values = 100

        # Check if es_client.execute_esql returns a tuple (ElasticsearchIndexer)
        # or a dict directly (ElasticClient)
        self._is_tuple_response = hasattr(es_client, 'index_dataset')  # ElasticsearchIndexer has index_dataset method

    def _execute_esql(self, query: str):
        """Execute ES|QL query and normalize the response

        Args:
            query: ES|QL query string

        Returns:
            Query result dict or None if failed
        """
        if self._is_tuple_response:
            # ElasticsearchIndexer returns (success, result, error_msg)
            success, result, error_msg = self.es_client.execute_esql(query)
            if success:
                return result
            else:
                raise Exception(error_msg)
        else:
            # ElasticClient returns result dict directly
            return self.es_client.execute_esql(query)

    def profile_datasets(
        self,
        datasets: Dict[str, Any],
        demo_path: Path,
        index_name_map: Optional[Dict[str, str]] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """Profile all datasets and save results

        Args:
            datasets: Dictionary of dataset_name -> DataFrame
            demo_path: Path to demo directory
            index_name_map: Optional mapping of dataset_name -> actual_index_name
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with profiling results
        """
        profile = {
            "generated_at": datetime.now().isoformat(),
            "datasets": {},
            "relationships": []
        }

        total_datasets = len(datasets)

        for i, (dataset_name, df) in enumerate(datasets.items(), 1):
            if progress_callback:
                progress_callback(f"Profiling {dataset_name}... ({i}/{total_datasets})")

            # Get the actual index name if mapped, otherwise use dataset_name
            index_name = index_name_map.get(dataset_name, dataset_name) if index_name_map else dataset_name
            logger.info(f"Profiling dataset: {dataset_name} (index: {index_name})")

            try:
                dataset_profile = self._profile_dataset(index_name, df)
                profile["datasets"][dataset_name] = dataset_profile
            except Exception as e:
                logger.error(f"Error profiling {dataset_name}: {e}")
                profile["datasets"][dataset_name] = {
                    "error": str(e),
                    "total_records": len(df)
                }

        # Detect relationships between datasets
        if progress_callback:
            progress_callback(f"Detecting relationships between datasets...")

        try:
            relationships = self._detect_relationships(datasets, profile["datasets"])
            profile["relationships"] = relationships
            logger.info(f"Detected {len(relationships)} potential relationships")
        except Exception as e:
            logger.error(f"Error detecting relationships: {e}")

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

        # Generate suggested filters (guaranteed to return results)
        try:
            suggested_filters = self._generate_suggested_filters(dataset_name, profile)
            profile["suggested_filters"] = suggested_filters
        except Exception as e:
            logger.warning(f"Could not generate suggested filters for {dataset_name}: {e}")

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
                result = self._execute_esql(query)
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
                result = self._execute_esql(query)
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
                result = self._execute_esql(query)
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

    def _detect_relationships(
        self,
        datasets: Dict[str, Any],
        dataset_profiles: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect potential relationships between datasets for LOOKUP JOINs

        Args:
            datasets: Dictionary of dataset_name -> DataFrame
            dataset_profiles: Dictionary of dataset_name -> profile data

        Returns:
            List of detected relationships with metadata
        """
        relationships = []

        # Get all dataset pairs
        dataset_names = list(datasets.keys())

        for i, left_dataset in enumerate(dataset_names):
            for right_dataset in dataset_names[i+1:]:
                # Try to find relationships between these two datasets
                left_df = datasets[left_dataset]
                right_df = datasets[right_dataset]

                left_profile = dataset_profiles.get(left_dataset, {})
                right_profile = dataset_profiles.get(right_dataset, {})

                # Look for potential foreign key relationships
                potential_rels = self._find_field_relationships(
                    left_dataset, left_df, left_profile,
                    right_dataset, right_df, right_profile
                )

                relationships.extend(potential_rels)

        return relationships

    def _find_field_relationships(
        self,
        left_dataset: str,
        left_df,
        left_profile: Dict[str, Any],
        right_dataset: str,
        right_df,
        right_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find field-level relationships between two datasets

        Args:
            left_dataset: Name of the left dataset
            left_df: DataFrame for left dataset
            left_profile: Profile data for left dataset
            right_dataset: Name of the right dataset
            right_df: DataFrame for right dataset
            right_profile: Profile data for right dataset

        Returns:
            List of detected field relationships
        """
        relationships = []

        # Get fields from both datasets
        left_fields = left_profile.get('fields', {})
        right_fields = right_profile.get('fields', {})

        for left_field, left_info in left_fields.items():
            # Skip non-categorical fields
            if 'unique_values' not in left_info:
                continue

            for right_field, right_info in right_fields.items():
                # Skip non-categorical fields
                if 'unique_values' not in right_info:
                    continue

                # Check for potential relationship
                relationship = self._analyze_field_pair(
                    left_dataset, left_field, left_df[left_field], left_info,
                    right_dataset, right_field, right_df[right_field], right_info
                )

                if relationship:
                    relationships.append(relationship)

        return relationships

    def _analyze_field_pair(
        self,
        left_dataset: str,
        left_field: str,
        left_series,
        left_info: Dict[str, Any],
        right_dataset: str,
        right_field: str,
        right_series,
        right_info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Analyze a pair of fields to determine if there's a relationship

        Args:
            left_dataset: Name of left dataset
            left_field: Name of left field
            left_series: Pandas series for left field
            left_info: Profile info for left field
            right_dataset: Name of right dataset
            right_field: Name of right field
            right_series: Pandas series for right field
            right_info: Profile info for right field

        Returns:
            Relationship metadata or None if no relationship detected
        """
        # Pattern matching for field names (e.g., product_id vs product_refs)
        is_id_pattern = self._is_id_field(left_field) or self._is_id_field(right_field)
        is_ref_pattern = self._is_ref_field(left_field) or self._is_ref_field(right_field)

        # Check for name similarity (e.g., product_id in both, or product_refs -> product_id)
        names_related = self._fields_name_related(left_field, right_field)

        # If names aren't related and no ID/ref patterns, skip
        if not (is_id_pattern or is_ref_pattern or names_related):
            return None

        # Get unique values for overlap analysis
        left_values = set(left_info.get('unique_values', []))
        right_values = set(right_info.get('unique_values', []))

        # Handle array fields (detected by comma-separated values)
        left_is_array = self._is_array_field(left_series)
        right_is_array = self._is_array_field(right_series)

        # Expand array values for overlap check
        if left_is_array:
            left_values = self._expand_csv_values(left_values)
        if right_is_array:
            right_values = self._expand_csv_values(right_values)

        # Calculate overlap
        overlap = left_values.intersection(right_values)
        if len(overlap) == 0:
            return None

        overlap_pct = len(overlap) / max(len(left_values), len(right_values)) * 100

        # Require at least 10% overlap to consider it a relationship
        if overlap_pct < 10:
            return None

        # Determine cardinality
        left_cardinality = left_info.get('cardinality', len(left_values))
        right_cardinality = right_info.get('cardinality', len(right_values))

        if left_cardinality == right_cardinality:
            cardinality = "one-to-one"
        elif left_cardinality > right_cardinality:
            cardinality = "many-to-one"
        else:
            cardinality = "one-to-many"

        # Determine which side should be the LOOKUP JOIN target
        # Typically, the smaller, reference-like dataset is the lookup target
        lookup_dataset = right_dataset if right_cardinality <= left_cardinality else left_dataset
        lookup_field = right_field if right_cardinality <= left_cardinality else left_field
        source_dataset = left_dataset if lookup_dataset == right_dataset else right_dataset
        source_field = left_field if lookup_dataset == right_dataset else right_field

        # Get sample values that would produce results
        sample_values = list(overlap)[:5]

        relationship = {
            "source_dataset": source_dataset,
            "source_field": source_field,
            "source_field_type": "array" if (left_is_array if source_field == left_field else right_is_array) else "single",
            "lookup_dataset": lookup_dataset,
            "lookup_field": lookup_field,
            "cardinality": cardinality,
            "overlap_percentage": round(overlap_pct, 2),
            "matching_values": len(overlap),
            "sample_join_values": sample_values,
            "confidence": "high" if overlap_pct > 50 else "medium" if overlap_pct > 25 else "low"
        }

        return relationship

    @staticmethod
    def _is_id_field(field_name: str) -> bool:
        """Check if a field name looks like an ID field"""
        field_lower = field_name.lower()
        return field_lower.endswith('_id') or field_lower == 'id' or 'uuid' in field_lower

    @staticmethod
    def _is_ref_field(field_name: str) -> bool:
        """Check if a field name looks like a reference field"""
        field_lower = field_name.lower()
        return 'ref' in field_lower or 'reference' in field_lower

    @staticmethod
    def _fields_name_related(field1: str, field2: str) -> bool:
        """Check if two field names are related (e.g., product_id and product_refs)"""
        # Remove common suffixes
        f1_base = field1.lower().replace('_id', '').replace('_ids', '').replace('_ref', '').replace('_refs', '')
        f2_base = field2.lower().replace('_id', '').replace('_ids', '').replace('_ref', '').replace('_refs', '')

        # Check if bases are the same
        return f1_base == f2_base or f1_base in f2_base or f2_base in f1_base

    @staticmethod
    def _is_array_field(series) -> bool:
        """Detect if a field contains array-like data (comma-separated values)"""
        # Sample a few non-null values
        sample = series.dropna().head(10)
        if len(sample) == 0:
            return False

        # Check if values contain commas (CSV pattern)
        csv_count = sum(1 for val in sample if isinstance(val, str) and ',' in val)
        return csv_count > len(sample) * 0.5  # More than 50% have commas

    @staticmethod
    def _expand_csv_values(values: set) -> set:
        """Expand comma-separated values into individual values"""
        expanded = set()
        for val in values:
            if isinstance(val, str) and ',' in val:
                # Split and strip whitespace
                expanded.update(v.strip() for v in val.split(','))
            else:
                expanded.add(val)
        return expanded

    def _generate_suggested_filters(
        self,
        dataset_name: str,
        dataset_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate suggested filter clauses guaranteed to return results

        Args:
            dataset_name: Name of the dataset
            dataset_profile: Profile data for the dataset

        Returns:
            List of suggested filters with metadata
        """
        suggested_filters = []
        total_records = dataset_profile.get('total_records', 0)

        # 1. Single-field filters from most common values
        fields = dataset_profile.get('fields', {})
        for field_name, field_info in fields.items():
            # Skip ID fields and timestamps
            if self._should_skip_field(field_name):
                continue

            # Categorical fields with unique values
            if 'unique_values' in field_info:
                values = field_info.get('unique_values', [])
                cardinality = field_info.get('cardinality', len(values))

                # For low-cardinality fields, suggest top 3-5 values
                if cardinality <= 20:
                    # Estimate records per value (rough approximation)
                    est_records_per_value = max(1, total_records // max(1, cardinality))

                    # Take top 3-5 values
                    sample_values = values[:min(5, len(values))]
                    for value in sample_values:
                        suggested_filters.append({
                            'filter_clause': f"{field_name} == '{value}'",
                            'estimated_records': est_records_per_value,
                            'filter_type': 'single-field',
                            'description': f"{field_name} equals '{value}'"
                        })

                # For medium-cardinality fields, suggest IN clause with top values
                elif 20 < cardinality <= 50:
                    top_values = values[:3]
                    values_str = ", ".join([f"'{v}'" for v in top_values])
                    est_records = max(1, total_records // max(1, cardinality // 3))

                    suggested_filters.append({
                        'filter_clause': f"{field_name} IN ({values_str})",
                        'estimated_records': est_records * len(top_values),
                        'filter_type': 'single-field',
                        'description': f"{field_name} in top values"
                    })

            # Numeric range filters
            elif 'min' in field_info and 'max' in field_info:
                min_val = field_info['min']
                max_val = field_info['max']
                avg_val = field_info.get('avg')

                # Suggest range around average
                if avg_val is not None and min_val != max_val:
                    range_size = (max_val - min_val) / 4  # Quarter of range
                    low = avg_val - range_size
                    high = avg_val + range_size

                    suggested_filters.append({
                        'filter_clause': f"{field_name} >= {low} AND {field_name} <= {high}",
                        'estimated_records': total_records // 2,
                        'filter_type': 'numeric-range',
                        'description': f"{field_name} in middle range"
                    })

            # Date range filters
            elif 'min_date' in field_info and 'max_date' in field_info:
                min_date = field_info['min_date']
                max_date = field_info['max_date']

                # Suggest recent data (last 25% of date range)
                suggested_filters.append({
                    'filter_clause': f"{field_name} >= '{min_date}' AND {field_name} <= '{max_date}'",
                    'estimated_records': total_records,
                    'filter_type': 'date-range',
                    'description': f"{field_name} full date range"
                })

        # 2. Multi-field combinations (from sample_combinations)
        combinations = dataset_profile.get('sample_combinations', [])
        for combo in combinations[:5]:  # Top 5 combinations
            combo_copy = combo.copy()
            record_count = combo_copy.pop('record_count', None)

            # Build filter clause
            filter_parts = [f"{k} == '{v}'" for k, v in combo_copy.items()]
            filter_clause = " AND ".join(filter_parts)

            # Build description
            desc_parts = [f"{k}='{v}'" for k, v in combo_copy.items()]
            description = ", ".join(desc_parts)

            suggested_filters.append({
                'filter_clause': filter_clause,
                'estimated_records': record_count if record_count else total_records // 10,
                'filter_type': 'multi-field',
                'description': description
            })

        # Sort by estimated records (descending) and limit to top 10
        suggested_filters.sort(key=lambda x: x.get('estimated_records', 0), reverse=True)
        return suggested_filters[:10]

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

        # Add relationship information first if available
        if profile.get("relationships"):
            lines.append("\n## Detected Relationships (for LOOKUP JOIN queries)")
            lines.append("\nThese relationships have been detected between datasets. Use them to construct valid LOOKUP JOIN queries:\n")

            for rel in profile["relationships"]:
                source_ds = rel["source_dataset"]
                source_field = rel["source_field"]
                source_type = rel["source_field_type"]
                lookup_ds = rel["lookup_dataset"]
                lookup_field = rel["lookup_field"]
                confidence = rel["confidence"]
                overlap = rel["overlap_percentage"]
                sample_values = rel.get("sample_join_values", [])[:3]

                lines.append(f"\n### {source_ds}.{source_field} → {lookup_ds}.{lookup_field}")
                lines.append(f"- **Confidence**: {confidence} ({overlap}% overlap)")
                lines.append(f"- **Source field type**: {source_type}")

                if source_type == "array":
                    lines.append(f"- **JOIN syntax**: `FROM {source_ds} | MV_EXPAND {source_field} | LOOKUP JOIN {lookup_ds} ON {source_field} == {lookup_field}`")
                else:
                    lines.append(f"- **JOIN syntax**: `FROM {source_ds} | LOOKUP JOIN {lookup_ds} ON {source_field} == {lookup_field}`")

                if sample_values:
                    sample_str = ", ".join([f"'{v}'" for v in sample_values])
                    lines.append(f"- **Sample matching values**: {sample_str}")

            lines.append("")  # Blank line after relationships

        for dataset_name, dataset_info in profile["datasets"].items():
            if "error" in dataset_info:
                continue

            lines.append(f"\n## {dataset_name} ({dataset_info.get('total_records', 0)} records)")

            # Suggested filters - PROMINENTLY DISPLAYED AT THE TOP
            if dataset_info.get("suggested_filters"):
                lines.append("\n### ⚡ SUGGESTED FILTERS (Guaranteed Results)")
                lines.append("\n**IMPORTANT**: Use these ready-to-use filters. DO NOT invent filter values.\n")

                suggested_filters = dataset_info["suggested_filters"]
                filter_limit = 5 if compact else 10

                for i, filter_info in enumerate(suggested_filters[:filter_limit], 1):
                    filter_clause = filter_info.get('filter_clause', '')
                    est_records = filter_info.get('estimated_records', 0)
                    filter_type = filter_info.get('filter_type', '')

                    if compact:
                        lines.append(f"{i}. `WHERE {filter_clause}` (~{est_records} records)")
                    else:
                        description = filter_info.get('description', '')
                        lines.append(f"{i}. `WHERE {filter_clause}`")
                        lines.append(f"   - Type: {filter_type}, Records: ~{est_records}, {description}")

                lines.append("")  # Blank line after suggested filters

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
    index_name_map: Optional[Dict[str, str]] = None,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """Convenience function to profile indexed data

    Args:
        es_client: ElasticsearchClient instance
        datasets: Dictionary of dataset_name -> DataFrame
        demo_path: Path to demo directory
        index_name_map: Optional mapping of dataset_name -> actual_index_name
        progress_callback: Optional callback for progress updates

    Returns:
        Profile dictionary
    """
    profiler = DataProfiler(es_client)
    return profiler.profile_datasets(datasets, demo_path, index_name_map, progress_callback)
