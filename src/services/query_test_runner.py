"""
Query Test Runner
Tests ES|QL queries against indexed data and fixes failures iteratively
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import re

from .elasticsearch_indexer import ElasticsearchIndexer
from .sample_values_extractor import SampleValuesExtractor
from .query_optimizer import fix_query

logger = logging.getLogger(__name__)


@dataclass
class QueryTestResult:
    """Result of testing a single query"""
    name: str
    was_fixed: bool
    needs_manual_fix: bool
    fix_attempts: int
    original_error: Optional[str] = None
    final_error: Optional[str] = None
    fix_history: List[Dict] = None
    original_esql: Optional[str] = None
    final_esql: Optional[str] = None

    def __post_init__(self):
        if self.fix_history is None:
            self.fix_history = []


class QueryTestRunner:
    """Tests and fixes queries iteratively using LLM"""

    def __init__(self, es_indexer: ElasticsearchIndexer, llm_client, data_profile: Optional[Dict] = None):
        """Initialize with Elasticsearch indexer and LLM client

        Args:
            es_indexer: ElasticsearchIndexer instance
            llm_client: Anthropic Claude client
            data_profile: Optional data profile from profiling phase
        """
        self.indexer = es_indexer
        self.llm_client = llm_client
        self.sample_extractor = SampleValuesExtractor(es_indexer.client)
        self.data_profile = data_profile

    def test_all_queries(
        self,
        queries: List[Dict],
        indexed_datasets: Dict[str, str],
        max_attempts: int = 3
    ) -> Dict:
        """Test all queries and attempt to fix failures

        Args:
            queries: List of query dictionaries with 'name', 'esql', etc.
            indexed_datasets: Dict mapping dataset names to index names
            max_attempts: Maximum fix attempts per query

        Returns:
            Dictionary with test results summary and individual query results
        """
        logger.info(f"Testing {len(queries)} queries against indexed data")

        results = {
            'tested_at': datetime.now().isoformat(),
            'total_queries': len(queries),
            'successfully_fixed': 0,
            'needs_manual_fix': 0,
            'queries': []
        }

        for query in queries:
            test_result = self._test_single_query(
                query,
                indexed_datasets,
                max_attempts
            )

            results['queries'].append(asdict(test_result))

            if test_result.was_fixed:
                results['successfully_fixed'] += 1
            elif test_result.needs_manual_fix:
                results['needs_manual_fix'] += 1

        logger.info(f"Test complete: {results['successfully_fixed']} fixed, {results['needs_manual_fix']} need manual fix")

        return results

    def _test_single_query(
        self,
        query: Dict,
        indexed_datasets: Dict,
        max_attempts: int
    ) -> QueryTestResult:
        """Test a single query with retry logic

        Args:
            query: Query dictionary
            indexed_datasets: Dict of dataset name -> index name
            max_attempts: Maximum fix attempts

        Returns:
            QueryTestResult with test outcome
        """
        result = QueryTestResult(
            name=query['name'],
            was_fixed=False,
            needs_manual_fix=False,
            fix_attempts=0,
            original_esql=query.get('esql') or query.get('query') or query.get('esql_query', '')
        )

        # Support 'esql', 'query', and 'esql_query' field names for backwards compatibility
        current_esql = query.get('esql') or query.get('query') or query.get('esql_query', '')

        # CRITICAL: Convert parameterized queries to scripted queries for testing
        if self._is_parameterized_query(current_esql):
            logger.info(f"Query '{query['name']}' is parameterized - converting to scripted query")
            current_esql = self._convert_to_scripted_query(current_esql, indexed_datasets)
            logger.info(f"Converted query: {current_esql[:200]}...")

        # Check for JOIN queries and validate early
        if self._is_join_query(current_esql):
            logger.info(f"Query '{query['name']}' contains LOOKUP JOIN - performing validation")
            join_validation = self._validate_join_query(current_esql, indexed_datasets)
            if not join_validation['valid']:
                logger.warning(f"JOIN validation failed: {join_validation['error']}")
                result.original_error = f"JOIN validation failed: {join_validation['error']}"

        for attempt in range(max_attempts):
            result.fix_attempts = attempt + 1

            # Replace dataset names with actual index names in query
            executed_esql = self._replace_index_names(current_esql, indexed_datasets)

            # Test the query
            success, response, error = self.indexer.execute_esql(executed_esql)

            # Check for zero results even on success
            result_count = 0
            if success and response:
                # Extract result count from response
                if isinstance(response, dict):
                    values = response.get('values', [])
                    result_count = len(values) if values else 0
                elif isinstance(response, list):
                    result_count = len(response)

            # Treat zero results as needing a fix (constraint relaxation)
            if success and result_count == 0:
                logger.warning(f"Query '{query['name']}' returned 0 results on attempt {attempt + 1}")
                success = False
                error = "Query returned 0 results (constraints may be too restrictive)"

            if success:
                result.was_fixed = True
                result.final_esql = current_esql
                result.fix_history.append({
                    'attempt': attempt + 1,
                    'succeeded': True,
                    'esql': current_esql,
                    'result_count': result_count
                })
                logger.info(f"Query '{query['name']}' succeeded on attempt {attempt + 1} with {result_count} results")
                break

            # Capture first error
            if attempt == 0:
                result.original_error = error

            logger.warning(f"Query '{query['name']}' failed on attempt {attempt + 1}: {error}")

            # Try to fix with centralized query optimizer
            if attempt < max_attempts - 1:
                try:
                    # Get query dict format expected by fix_query
                    query_dict = {
                        'name': query.get('name', 'Unknown Query'),
                        'description': query.get('description', ''),
                    }

                    # Use centralized fix_query function with data profile and indexed datasets
                    fixed_esql, explanation = fix_query(
                        query=query_dict,
                        current_esql=current_esql,
                        data_profile=self.data_profile,
                        llm_client=self.llm_client,
                        error_message=error if result_count > 0 or not success else None,
                        indexed_datasets=indexed_datasets
                    )

                    logger.info(f"Fix explanation: {explanation}")

                    result.fix_history.append({
                        'attempt': attempt + 1,
                        'error': error,
                        'esql': current_esql
                    })

                    current_esql = fixed_esql

                except Exception as e:
                    logger.error(f"Failed to fix query with LLM: {e}")
                    result.needs_manual_fix = True
                    result.final_error = str(e)
                    break
            else:
                # Last attempt failed
                result.needs_manual_fix = True
                result.final_error = error
                result.fix_history.append({
                    'attempt': attempt + 1,
                    'error': error,
                    'esql': current_esql
                })

        return result

    def _is_parameterized_query(self, esql: str) -> bool:
        """Check if query contains ES|QL parameters

        Args:
            esql: ES|QL query string

        Returns:
            True if query contains parameters (?, ?name, ?1, etc.)
        """
        # Match ? followed by optional alphanumeric identifier
        param_pattern = r'\?[\w]*'
        return bool(re.search(param_pattern, esql))

    def _convert_to_scripted_query(
        self,
        esql: str,
        indexed_datasets: Dict[str, str]
    ) -> str:
        """Convert parameterized query to scripted query with real values

        Args:
            esql: Parameterized ES|QL query
            indexed_datasets: Dict mapping dataset names to index names

        Returns:
            Scripted ES|QL query with actual values
        """
        logger.info("Converting parameterized query to scripted query")

        # Find all parameters in the query
        param_pattern = r'\?(\w+)'
        parameters = re.findall(param_pattern, esql)

        if not parameters:
            logger.warning("No parameters found in query")
            return esql

        logger.info(f"Found {len(parameters)} parameters: {parameters}")

        # Extract index name from query (FROM clause)
        from_pattern = r'FROM\s+(\w+)'
        from_match = re.search(from_pattern, esql)

        if not from_match:
            logger.warning("Could not find FROM clause in query")
            return esql

        dataset_name = from_match.group(1)
        index_name = indexed_datasets.get(dataset_name)

        if not index_name:
            logger.warning(f"No index found for dataset {dataset_name}")
            return esql

        # Get sample values from Elasticsearch for each parameter
        scripted_esql = esql

        for param_name in set(parameters):  # Use set to avoid duplicates
            # Try to get a real value for this parameter
            sample_value = self.sample_extractor.get_value_for_field(
                index_name=index_name,
                field_name=param_name,
                field_type="keyword"
            )

            if sample_value:
                # Replace parameter with actual value
                # Use quotes for string values
                if isinstance(sample_value, str):
                    replacement = f'"{sample_value}"'
                else:
                    replacement = str(sample_value)

                # Replace ?param_name with actual value
                scripted_esql = re.sub(
                    rf'\?{param_name}\b',
                    replacement,
                    scripted_esql
                )

                logger.info(f"Replaced ?{param_name} with {replacement}")
            else:
                logger.warning(f"Could not find sample value for parameter: {param_name}")
                # Keep parameter as-is if we can't find a value
                # The LLM fixer will handle it later

        return scripted_esql

    def _replace_index_names(self, esql: str, indexed_datasets: Dict[str, str]) -> str:
        """Replace dataset names with actual index names in query

        Args:
            esql: Original ES|QL query
            indexed_datasets: Dict mapping dataset names to index names

        Returns:
            ES|QL query with actual index names
        """
        modified_esql = esql

        for dataset_name, index_name in indexed_datasets.items():
            # Replace dataset name with index name
            # NO _lookup suffix handling - we don't use that convention
            modified_esql = modified_esql.replace(dataset_name, index_name)

        return modified_esql

    def _is_join_query(self, esql: str) -> bool:
        """Check if query contains a LOOKUP JOIN

        Args:
            esql: ES|QL query string

        Returns:
            True if query contains LOOKUP JOIN
        """
        return bool(re.search(r'LOOKUP\s+JOIN', esql, re.IGNORECASE))

    def _validate_join_query(self, esql: str, indexed_datasets: Dict) -> Dict[str, Any]:
        """Validate LOOKUP JOIN query syntax and structure

        Args:
            esql: ES|QL query string
            indexed_datasets: Dict of dataset name -> index name

        Returns:
            Dict with 'valid' (bool) and 'error' (str) if invalid
        """
        # Pattern to match LOOKUP JOIN syntax
        # Matches: LOOKUP JOIN <index> ON <field1> [== <field2>]
        join_pattern = r'LOOKUP\s+JOIN\s+(\w+)\s+ON\s+(\w+)(?:\s*==\s*(\w+))?'

        match = re.search(join_pattern, esql, re.IGNORECASE)

        if not match:
            return {
                'valid': False,
                'error': 'Invalid LOOKUP JOIN syntax. Expected: LOOKUP JOIN <index> ON <field> or LOOKUP JOIN <index> ON <field1> == <field2>'
            }

        lookup_index = match.group(1)
        left_field = match.group(2)
        right_field = match.group(3) if match.group(3) else left_field

        # Check if both JOIN keyword is present (common error: just "LOOKUP" without "JOIN")
        if not re.search(r'LOOKUP\s+JOIN', esql, re.IGNORECASE):
            return {
                'valid': False,
                'error': 'Missing JOIN keyword. Use "LOOKUP JOIN", not just "LOOKUP"'
            }

        # Check if using single = instead of ==
        if re.search(r'ON\s+\w+\s*=\s*\w+(?!=)', esql):
            return {
                'valid': False,
                'error': 'Use "==" for field comparison in LOOKUP JOIN, not "="'
            }

        # Check if lookup index exists in indexed datasets
        if lookup_index not in indexed_datasets:
            return {
                'valid': False,
                'error': f'Lookup index "{lookup_index}" not found in indexed datasets. Available: {list(indexed_datasets.keys())}'
            }

        # Provide helpful info from data profile if available
        if self.data_profile and 'relationships' in self.data_profile:
            relationships = self.data_profile['relationships']
            # Find if this JOIN matches a detected relationship
            for rel in relationships:
                if rel['lookup_dataset'] == lookup_index:
                    # This is a detected relationship - good!
                    logger.info(f"JOIN matches detected relationship: {rel['source_dataset']}.{rel['source_field']} -> {rel['lookup_dataset']}.{rel['lookup_field']}")

                    # Check if they're using the correct field names
                    if left_field != rel['source_field'] or right_field != rel['lookup_field']:
                        return {
                            'valid': False,
                            'error': f'Field mismatch. Detected relationship suggests: {rel["source_dataset"]}.{rel["source_field"]} == {rel["lookup_dataset"]}.{rel["lookup_field"]}, but query uses {left_field} == {right_field}'
                        }

        return {'valid': True}

    def get_summary_stats(self, results: Dict) -> Dict[str, Any]:
        """Get summary statistics from test results

        Args:
            results: Test results dictionary

        Returns:
            Summary statistics
        """
        total = results['total_queries']
        fixed = results['successfully_fixed']
        manual = results['needs_manual_fix']
        success_rate = (fixed / total * 100) if total > 0 else 0

        return {
            'total_queries': total,
            'successfully_fixed': fixed,
            'needs_manual_fix': manual,
            'success_rate': round(success_rate, 1),
            'avg_attempts': self._calculate_avg_attempts(results['queries'])
        }

    def _calculate_avg_attempts(self, query_results: List[Dict]) -> float:
        """Calculate average fix attempts"""
        if not query_results:
            return 0.0

        total_attempts = sum(q.get('fix_attempts', 0) for q in query_results)
        return round(total_attempts / len(query_results), 1)
