"""
Schema Contract Validation

Lightweight validation module (no LLM, no I/O) that verifies field name consistency
across the search demo pipeline: strategy -> data specs -> data profile -> queries.

Only used for search demos. Analytics demos never call this module.
"""

import re
import logging
from typing import Dict, List, Any, Set

logger = logging.getLogger(__name__)


class SchemaContract:
    """Validates field name consistency across search demo pipeline stages"""

    @staticmethod
    def extract_canonical_fields(query_strategy: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """Extract the canonical field schema from query strategy.

        The query strategy is the source of truth for field names and types.

        Args:
            query_strategy: Strategy dict with 'datasets' containing 'required_fields'

        Returns:
            {dataset_name: {field_name: field_type}}
        """
        canonical = {}
        for dataset in query_strategy.get('datasets', []):
            name = dataset.get('name', '')
            fields = dataset.get('required_fields', dataset.get('fields', {}))
            if isinstance(fields, dict):
                canonical[name] = fields
            elif isinstance(fields, list):
                # List format: convert to dict with 'unknown' types
                canonical[name] = {f: 'unknown' for f in fields}
            else:
                canonical[name] = {}
        return canonical

    @staticmethod
    def validate_data_specifications(
        canonical: Dict[str, Dict[str, str]],
        data_specs: Dict[str, Any]
    ) -> List[str]:
        """Validate data specifications against canonical schema.

        Checks that expanded data specs reference the same field names
        as the query strategy.

        Args:
            canonical: {dataset_name: {field_name: field_type}} from strategy
            data_specs: Data specifications dict with 'datasets' key

        Returns:
            List of warning messages (empty = all good)
        """
        warnings = []
        spec_datasets = data_specs.get('datasets', {})

        for dataset_name, canonical_fields in canonical.items():
            if dataset_name not in spec_datasets:
                warnings.append(
                    f"Dataset '{dataset_name}' in strategy but missing from data specifications"
                )
                continue

            spec_fields = set(spec_datasets[dataset_name].get('fields', {}).keys())
            canonical_field_names = set(canonical_fields.keys())

            # Fields in strategy but missing from specs
            missing = canonical_field_names - spec_fields
            if missing:
                warnings.append(
                    f"Dataset '{dataset_name}': fields in strategy but missing from specs: {sorted(missing)}"
                )

            # Fields in specs but not in strategy (invented by LLM)
            extra = spec_fields - canonical_field_names
            if extra:
                warnings.append(
                    f"Dataset '{dataset_name}': fields in specs but not in strategy: {sorted(extra)}"
                )

        # Datasets in specs but not in strategy
        for ds_name in spec_datasets:
            if ds_name not in canonical:
                warnings.append(
                    f"Dataset '{ds_name}' in specs but not in strategy"
                )

        return warnings

    @staticmethod
    def validate_data_profile(
        canonical: Dict[str, Dict[str, str]],
        data_profile: Dict[str, Any]
    ) -> List[str]:
        """Validate profiled data against canonical schema.

        Checks that indexed data field names match strategy expectations.

        Args:
            canonical: {dataset_name: {field_name: field_type}} from strategy
            data_profile: Profile dict with 'datasets' containing field info

        Returns:
            List of warning messages (empty = all good)
        """
        warnings = []
        profile_datasets = data_profile.get('datasets', {})

        for dataset_name, canonical_fields in canonical.items():
            if dataset_name not in profile_datasets:
                warnings.append(
                    f"Dataset '{dataset_name}' in strategy but not in data profile"
                )
                continue

            # Extract field names from profile (various formats)
            profile_ds = profile_datasets[dataset_name]
            profile_fields: Set[str] = set()

            # Format 1: 'fields' dict
            if 'fields' in profile_ds:
                profile_fields.update(profile_ds['fields'].keys())
            # Format 2: 'field_names' list
            if 'field_names' in profile_ds:
                profile_fields.update(profile_ds['field_names'])

            if not profile_fields:
                continue

            canonical_field_names = set(canonical_fields.keys())

            # Fields expected but missing from indexed data
            missing = canonical_field_names - profile_fields
            # Filter out meta-fields that may not be profiled
            missing = {f for f in missing if not f.startswith('_')}
            if missing:
                warnings.append(
                    f"Dataset '{dataset_name}': strategy fields missing from indexed data: {sorted(missing)}"
                )

        return warnings

    @staticmethod
    def validate_query_fields(
        canonical: Dict[str, Dict[str, str]],
        queries: List[Dict[str, Any]]
    ) -> List[str]:
        """Validate that queries reference fields that exist in the canonical schema.

        Parses ES|QL queries to extract field references and checks them
        against the strategy's field definitions.

        Args:
            canonical: {dataset_name: {field_name: field_type}} from strategy
            queries: List of query dicts with 'esql' or 'example_esql' keys

        Returns:
            List of warning messages (empty = all good)
        """
        warnings = []

        # Build a flat set of all known field names across all datasets
        all_known_fields: Set[str] = set()
        for fields in canonical.values():
            all_known_fields.update(fields.keys())

        # Also add common meta-fields that are always valid
        all_known_fields.update(['@timestamp', '_id', '_index', '_score'])

        for i, query in enumerate(queries):
            esql = (
                query.get('example_esql') or
                query.get('esql') or
                query.get('esql_query') or
                query.get('query') or
                ''
            )

            if not esql:
                continue

            query_name = query.get('name', query.get('title', f'query_{i}'))

            # Extract field references from MATCH(), WHERE, STATS BY, etc.
            referenced_fields = SchemaContract._extract_field_references(esql)

            # Check each referenced field
            unknown_fields = referenced_fields - all_known_fields
            if unknown_fields:
                warnings.append(
                    f"Query '{query_name}': references unknown fields: {sorted(unknown_fields)}"
                )

        return warnings

    @staticmethod
    def _extract_field_references(esql: str) -> Set[str]:
        """Extract field name references from an ES|QL query string.

        Heuristic extraction - not a full parser. Catches most common patterns:
        - MATCH(field_name, ...)
        - WHERE field_name == ...
        - STATS ... BY field_name
        - SORT field_name
        - KEEP field_name, ...

        Args:
            esql: ES|QL query string

        Returns:
            Set of field names referenced in the query
        """
        fields: Set[str] = set()

        # MATCH(field_name, ...) and MATCH_PHRASE(field_name, ...)
        for match in re.finditer(r'MATCH(?:_PHRASE)?\s*\(\s*([a-zA-Z_][a-zA-Z0-9_]*)', esql):
            fields.add(match.group(1))

        # KEEP field1, field2, ...
        keep_match = re.search(r'KEEP\s+(.+?)(?:\||$)', esql, re.IGNORECASE)
        if keep_match:
            for f in re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)', keep_match.group(1)):
                if f.upper() not in ('KEEP', 'AS', 'NULL', 'TRUE', 'FALSE'):
                    fields.add(f)

        # WHERE field == / != / > / < ...
        for match in re.finditer(r'WHERE\s+([a-zA-Z_@][a-zA-Z0-9_]*)', esql, re.IGNORECASE):
            fields.add(match.group(1))

        # SORT field_name
        for match in re.finditer(r'SORT\s+([a-zA-Z_@][a-zA-Z0-9_]*)', esql, re.IGNORECASE):
            fields.add(match.group(1))

        # STATS ... BY field_name
        by_match = re.search(r'\bBY\s+(.+?)(?:\||$)', esql, re.IGNORECASE)
        if by_match:
            for f in re.findall(r'([a-zA-Z_@][a-zA-Z0-9_]*)', by_match.group(1)):
                if f.upper() not in ('BY', 'AS', 'AND', 'OR', 'NOT', 'NULL', 'TRUE', 'FALSE'):
                    fields.add(f)

        # Filter out ES|QL keywords that look like field names
        esql_keywords = {
            'FROM', 'WHERE', 'EVAL', 'STATS', 'SORT', 'LIMIT', 'KEEP', 'DROP',
            'RENAME', 'MATCH', 'MATCH_PHRASE', 'QSTR', 'RERANK', 'COMPLETION',
            'FORK', 'FUSE', 'INLINESTATS', 'LOOKUP', 'JOIN', 'ON', 'ASC', 'DESC',
            'NULLS', 'FIRST', 'LAST', 'COUNT', 'AVG', 'SUM', 'MIN', 'MAX',
            'MEDIAN', 'VALUES', 'MV_EXPAND', 'DISSECT', 'GROK', 'ENRICH',
            'DATE_TRUNC', 'TO_STRING', 'TO_INTEGER', 'TO_DOUBLE', 'CASE',
            'LIKE', 'RLIKE', 'IN', 'IS', 'NOT', 'AND', 'OR', 'WITH', 'ROW',
            'SHOW', 'META', 'MV_COUNT', 'COALESCE', 'ROUND', 'LENGTH',
            'CONCAT', 'SUBSTRING', 'TRIM', 'TO_LOWER', 'TO_UPPER',
        }

        fields = {f for f in fields if f.upper() not in esql_keywords}

        return fields
