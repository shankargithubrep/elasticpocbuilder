"""
Query Refinement Service
Refines search queries using profiled data to ensure they return results
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class QueryRefiner:
    """Refines search queries by replacing placeholder values with actual profiled values"""

    def __init__(self, data_profile: Dict[str, Any]):
        """Initialize with data profile

        Args:
            data_profile: Profile dictionary from DataProfiler
        """
        self.data_profile = data_profile
        self.datasets = data_profile.get('datasets', {})

    def refine_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Refine a single query using profiled data

        Args:
            query: Query dictionary with 'query' (ES|QL string) and metadata

        Returns:
            Refined query dictionary
        """
        esql = query.get('query', '')
        query_name = query.get('name', 'Unnamed')
        required_datasets = query.get('required_datasets', [])

        if not esql or not required_datasets:
            logger.warning(f"Query '{query_name}' missing query or required_datasets, skipping refinement")
            return query

        # Check if query needs refinement (has hardcoded/placeholder values)
        if not self._needs_refinement(esql):
            logger.debug(f"Query '{query_name}' appears to have valid values, skipping refinement")
            return query

        logger.info(f"Refining query: {query_name}")

        # Extract the primary dataset (first in required_datasets)
        primary_dataset = required_datasets[0]

        if primary_dataset not in self.datasets:
            logger.warning(f"Dataset '{primary_dataset}' not found in profile, cannot refine query")
            return query

        dataset_profile = self.datasets[primary_dataset]

        # Refine the query based on query type
        refined_esql = esql

        # 1. Refine exact match filters (field == "placeholder_value")
        refined_esql = self._refine_exact_matches(refined_esql, dataset_profile, primary_dataset)

        # 2. Refine MATCH queries (for semantic search)
        refined_esql = self._refine_match_queries(refined_esql, dataset_profile, primary_dataset)

        # 3. Refine multi-field WHERE clauses using sample combinations
        refined_esql = self._refine_multi_field_filters(refined_esql, dataset_profile, primary_dataset)

        # Update query
        if refined_esql != esql:
            logger.info(f"Refined query '{query_name}':")
            logger.info(f"  BEFORE: {esql[:150]}...")
            logger.info(f"  AFTER:  {refined_esql[:150]}...")

            refined_query = query.copy()
            refined_query['query'] = refined_esql
            refined_query['refinement_applied'] = True
            return refined_query
        else:
            logger.debug(f"No changes made to query '{query_name}'")
            return query

    def _needs_refinement(self, esql: str) -> bool:
        """Check if query contains placeholder/suspect values that need refinement

        Args:
            esql: ES|QL query string

        Returns:
            True if refinement needed
        """
        # Common placeholder patterns
        placeholder_patterns = [
            r'== "?\d{10}"?',  # 10-digit placeholder (like NPI 1234567890)
            r'== "?(XXXX|TEST|PLACEHOLDER)',  # Obvious placeholders
            r'== "?123',  # Generic test values starting with 123
        ]

        for pattern in placeholder_patterns:
            if re.search(pattern, esql, re.IGNORECASE):
                logger.debug(f"Found placeholder pattern: {pattern}")
                return True

        # Check for WHERE clauses with multiple conditions (might be invalid combinations)
        # Pattern: WHERE field1 == "X" AND field2 == "Y" AND field3 == "Z" (3+ filters)
        and_count = esql.count(' AND ')
        if and_count >= 3:
            logger.debug(f"Found {and_count} AND conditions, may need combination refinement")
            return True

        return False

    def _refine_exact_matches(self, esql: str, dataset_profile: Dict, dataset_name: str) -> str:
        """Refine exact match filters like: field == "placeholder_value"

        Args:
            esql: ES|QL query string
            dataset_profile: Profile for the dataset
            dataset_name: Name of the dataset

        Returns:
            Refined ES|QL string
        """
        fields = dataset_profile.get('fields', {})

        # Pattern: field_name == "value" or field_name == 'value'
        # Use lookahead to avoid matching inside strings
        pattern = r'(\w+)\s*==\s*["\']([^"\']+)["\']'

        def replace_value(match):
            field_name = match.group(1)
            current_value = match.group(2)

            # Check if this field exists in the profile
            if field_name not in fields:
                logger.debug(f"Field '{field_name}' not in profile, keeping current value")
                return match.group(0)

            field_info = fields[field_name]

            # Get actual values from profile
            unique_values = field_info.get('unique_values', [])

            if not unique_values:
                logger.debug(f"No unique values for field '{field_name}', keeping current value")
                return match.group(0)

            # Check if current value exists in the data
            if current_value in unique_values:
                logger.debug(f"Field '{field_name}' value '{current_value}' exists, keeping")
                return match.group(0)

            # Replace with first actual value
            actual_value = unique_values[0]
            logger.info(f"Replacing {field_name} == '{current_value}' with '{actual_value}'")
            return f'{field_name} == "{actual_value}"'

        refined = re.sub(pattern, replace_value, esql)
        return refined

    def _refine_match_queries(self, esql: str, dataset_profile: Dict, dataset_name: str) -> str:
        """Refine MATCH queries using actual field content

        For semantic_text fields, we want to ensure MATCH terms are relevant to actual data.

        Args:
            esql: ES|QL query string
            dataset_profile: Profile for the dataset
            dataset_name: Name of the dataset

        Returns:
            Refined ES|QL string
        """
        # For now, we won't auto-replace MATCH query terms since they're meant to be
        # flexible natural language queries. The strategy generator should create
        # appropriate search terms based on the use case.

        # Future enhancement: Could use semantic_fields content to suggest better terms

        return esql

    def _refine_multi_field_filters(self, esql: str, dataset_profile: Dict, dataset_name: str) -> str:
        """Refine multi-field WHERE clauses using sample combinations from profiling

        ENHANCED APPROACH: Parse individual filter conditions and intelligently replace
        only the exact-match filters with invalid values, while preserving:
        - MATCH() queries (semantic search)
        - LIKE patterns (wildcards)
        - Boolean filters
        - Valid exact matches

        Args:
            esql: ES|QL query string
            dataset_profile: Profile for the dataset
            dataset_name: Name of the dataset

        Returns:
            Refined ES|QL string
        """
        # Get sample combinations from profile
        sample_combinations = dataset_profile.get('sample_combinations', [])

        if not sample_combinations:
            logger.debug(f"No sample combinations available for {dataset_name}")
            return esql

        # Count AND conditions in WHERE clause
        and_count = esql.count(' AND ')

        if and_count < 2:
            logger.debug("Fewer than 2 AND conditions, no multi-field refinement needed")
            return esql

        logger.info(f"Query has {and_count} AND conditions, analyzing for smart refinement")

        # Extract WHERE clause
        where_match = re.search(r'WHERE\s+(.+?)(?:\s+\||$)', esql, re.IGNORECASE | re.DOTALL)
        if not where_match:
            logger.debug("No WHERE clause found")
            return esql

        where_clause = where_match.group(1).strip()

        # Parse individual conditions from WHERE clause
        parsed_filters = self._parse_where_conditions(where_clause)

        if not parsed_filters:
            logger.debug("Could not parse WHERE conditions")
            return esql

        logger.info(f"Parsed {len(parsed_filters)} filter conditions")

        # Find best-matching combination based on parsed filters
        best_combo = self._find_best_combination(parsed_filters, sample_combinations, dataset_profile)

        if not best_combo:
            logger.debug("No suitable combination found matching query filters")
            return esql

        logger.info(f"Selected best matching combination: {best_combo}")

        # Intelligently merge: use combo values only for fields that need fixing
        refined_filters = self._merge_filters_with_combination(parsed_filters, best_combo, dataset_profile)

        # Rebuild WHERE clause
        new_where = " AND ".join(refined_filters)

        # Replace WHERE clause
        refined = re.sub(
            r'WHERE\s+.+?(?=\s+\||$)',
            f'WHERE {new_where}',
            esql,
            flags=re.IGNORECASE | re.DOTALL
        )

        logger.info(f"Refined multi-field WHERE clause:")
        logger.info(f"  OLD: WHERE {where_clause[:150]}...")
        logger.info(f"  NEW: WHERE {new_where[:150]}...")

        return refined

    def _parse_where_conditions(self, where_clause: str) -> List[Dict[str, Any]]:
        """Parse WHERE clause into individual filter conditions

        Args:
            where_clause: WHERE clause string (without the WHERE keyword)

        Returns:
            List of parsed filter dictionaries with type, field, operator, value
        """
        filters = []

        # Split on AND (case-insensitive), but be careful with AND inside MATCH()
        # Simple approach: split on ' AND ' not inside parentheses
        conditions = self._split_and_conditions(where_clause)

        for condition in conditions:
            condition = condition.strip()

            # Detect filter type and parse accordingly
            if 'MATCH(' in condition.upper():
                # MATCH filter - preserve as-is
                filters.append({
                    'type': 'match',
                    'original': condition,
                    'preserve': True
                })
            elif ' LIKE ' in condition.upper():
                # LIKE pattern - preserve as-is
                filters.append({
                    'type': 'like',
                    'original': condition,
                    'preserve': True
                })
            elif '==' in condition:
                # Exact match filter - may need refinement
                match = re.match(r'(\w+)\s*==\s*(["\']?)([^"\']+)\2', condition)
                if match:
                    field = match.group(1)
                    value = match.group(3)
                    filters.append({
                        'type': 'exact',
                        'field': field,
                        'value': value,
                        'original': condition,
                        'preserve': False  # May be refined
                    })
            elif ' IN ' in condition.upper():
                # IN filter - preserve as-is for now
                filters.append({
                    'type': 'in',
                    'original': condition,
                    'preserve': True
                })
            else:
                # Unknown/complex filter - preserve as-is
                filters.append({
                    'type': 'unknown',
                    'original': condition,
                    'preserve': True
                })

        return filters

    def _split_and_conditions(self, where_clause: str) -> List[str]:
        """Split WHERE clause on AND, respecting parentheses

        Args:
            where_clause: WHERE clause string

        Returns:
            List of individual conditions
        """
        conditions = []
        current = []
        paren_depth = 0

        # Split by words to handle AND properly
        parts = re.split(r'\s+', where_clause)

        for part in parts:
            # Track parentheses
            paren_depth += part.count('(') - part.count(')')

            if part.upper() == 'AND' and paren_depth == 0:
                # Found AND at top level - save current condition
                if current:
                    conditions.append(' '.join(current))
                    current = []
            else:
                current.append(part)

        # Don't forget last condition
        if current:
            conditions.append(' '.join(current))

        return conditions

    def _find_best_combination(
        self,
        parsed_filters: List[Dict[str, Any]],
        sample_combinations: List[Dict[str, Any]],
        dataset_profile: Dict
    ) -> Optional[Dict[str, Any]]:
        """Find best-matching combination based on query filters

        Scoring: Combination with most matching field names wins

        Args:
            parsed_filters: Parsed filter conditions
            sample_combinations: Available combinations from profiling
            dataset_profile: Dataset profile for validation

        Returns:
            Best matching combination or None
        """
        # Extract field names from exact-match filters
        query_fields = set()
        for f in parsed_filters:
            if f['type'] == 'exact' and 'field' in f:
                query_fields.add(f['field'])

        if not query_fields:
            # No exact-match filters to optimize
            return None

        # Score each combination by field overlap
        scored_combos = []
        for combo in sample_combinations:
            combo_fields = {k for k in combo.keys() if k != 'record_count'}
            overlap = len(query_fields.intersection(combo_fields))

            if overlap > 0:
                scored_combos.append((overlap, combo))

        if not scored_combos:
            # Fallback: use first combination with multiple fields
            for combo in sample_combinations:
                combo_fields = {k: v for k, v in combo.items() if k != 'record_count'}
                if len(combo_fields) >= 2:
                    return combo_fields
            return None

        # Return combination with highest overlap
        scored_combos.sort(key=lambda x: x[0], reverse=True)
        best_combo = scored_combos[0][1]

        # Remove record_count
        return {k: v for k, v in best_combo.items() if k != 'record_count'}

    def _merge_filters_with_combination(
        self,
        parsed_filters: List[Dict[str, Any]],
        combination: Dict[str, Any],
        dataset_profile: Dict
    ) -> List[str]:
        """Merge parsed filters with combination values intelligently

        Strategy:
        - MATCH/LIKE/IN filters: Keep original (preserve)
        - Exact match with VALID value: Keep original
        - Exact match with INVALID value + field in combination: Use combo value
        - Exact match with INVALID value + field NOT in combination: Keep original

        Args:
            parsed_filters: Parsed filter conditions
            combination: Best matching combination
            dataset_profile: Dataset profile

        Returns:
            List of filter condition strings
        """
        refined = []
        fields_in_dataset = dataset_profile.get('fields', {})

        for f in parsed_filters:
            if f.get('preserve', False):
                # MATCH, LIKE, IN - always preserve
                refined.append(f['original'])
            elif f['type'] == 'exact':
                field = f['field']
                value = f['value']

                # Check if value is valid
                if field in fields_in_dataset:
                    field_info = fields_in_dataset[field]
                    valid_values = field_info.get('unique_values', [])

                    if valid_values and value in valid_values:
                        # Value is valid - keep original
                        logger.debug(f"Field {field}={value} is valid, keeping")
                        refined.append(f['original'])
                    elif field in combination:
                        # Value is invalid but we have a combo value - replace
                        new_value = combination[field]
                        logger.info(f"Replacing {field}={value} with {field}={new_value} from combination")
                        # Format value based on type
                        if isinstance(new_value, bool):
                            formatted_value = str(new_value).lower()  # true/false
                        elif isinstance(new_value, (int, float)):
                            formatted_value = str(new_value)  # No quotes for numbers
                        else:
                            formatted_value = f'"{new_value}"'  # Quotes for strings
                        refined.append(f'{field} == {formatted_value}')
                    else:
                        # Value is invalid but no combo value - keep original
                        logger.debug(f"Field {field}={value} invalid but no combo value, keeping")
                        refined.append(f['original'])
                else:
                    # Field not in profile - keep original
                    refined.append(f['original'])
            else:
                # Unknown type - preserve
                refined.append(f['original'])

        return refined

    def refine_all_queries(self, queries: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Refine all queries in a list

        Args:
            queries: List of query dictionaries

        Returns:
            Tuple of (refined_queries, refinement_stats)
        """
        refined_queries = []
        stats = {
            'total_queries': len(queries),
            'refined': 0,
            'skipped': 0,
            'failed': 0
        }

        for query in queries:
            try:
                refined_query = self.refine_query(query)
                refined_queries.append(refined_query)

                if refined_query.get('refinement_applied'):
                    stats['refined'] += 1
                else:
                    stats['skipped'] += 1
            except Exception as e:
                logger.error(f"Failed to refine query '{query.get('name')}': {e}", exc_info=True)
                # Keep original query on failure
                refined_queries.append(query)
                stats['failed'] += 1

        logger.info(f"Query refinement complete: {stats['refined']} refined, {stats['skipped']} skipped, {stats['failed']} failed")

        return refined_queries, stats


def refine_queries_with_profile(
    queries: List[Dict[str, Any]],
    data_profile: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Convenience function to refine queries using data profile

    Args:
        queries: List of query dictionaries
        data_profile: Profile dictionary from DataProfiler

    Returns:
        Tuple of (refined_queries, refinement_stats)
    """
    refiner = QueryRefiner(data_profile)
    return refiner.refine_all_queries(queries)
