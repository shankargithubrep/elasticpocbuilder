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
    warnings: List[Dict] = None  # Pattern warnings (e.g., integer division)

    def __post_init__(self):
        if self.fix_history is None:
            self.fix_history = []
        if self.warnings is None:
            self.warnings = []


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
            'early_exit': False,
            'queries': []
        }

        consecutive_failures = 0
        EARLY_EXIT_THRESHOLD = 3

        for query in queries:
            test_result = self._test_single_query(
                query,
                indexed_datasets,
                max_attempts
            )

            results['queries'].append(asdict(test_result))

            if test_result.was_fixed:
                results['successfully_fixed'] += 1
                consecutive_failures = 0
            elif test_result.needs_manual_fix:
                results['needs_manual_fix'] += 1
                consecutive_failures += 1

            # Early exit: if first N queries all fail, something is systemically wrong
            # (e.g., no data indexed, refresh not working). Don't burn LLM calls fixing the rest.
            if consecutive_failures >= EARLY_EXIT_THRESHOLD and results['successfully_fixed'] == 0:
                remaining = len(queries) - len(results['queries'])
                logger.warning(
                    f"Early exit: first {EARLY_EXIT_THRESHOLD} queries all failed with 0 successes. "
                    f"Skipping {remaining} remaining queries — likely a systemic issue."
                )
                results['early_exit'] = True
                results['early_exit_reason'] = (
                    f"First {EARLY_EXIT_THRESHOLD} queries failed consecutively. "
                    f"This usually indicates a data indexing or refresh issue."
                )
                # Mark remaining queries as needing manual fix without testing
                for remaining_query in queries[len(results['queries']):]:
                    results['queries'].append(asdict(QueryTestResult(
                        name=remaining_query['name'],
                        was_fixed=False,
                        needs_manual_fix=True,
                        fix_attempts=0,
                        original_error="Skipped due to early exit (systemic failure detected)",
                    )))
                    results['needs_manual_fix'] += 1
                break

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
                # Note: Elasticsearch client returns ObjectApiResponse which supports dict-like access
                # but isinstance(response, dict) returns False. Use duck typing instead.
                if isinstance(response, list):
                    result_count = len(response)
                elif hasattr(response, 'get'):
                    # ObjectApiResponse and dict both have 'get' method
                    values = response.get('values', [])
                    result_count = len(values) if values else 0

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

                # Detect potential integer division patterns (no error, but may produce wrong results)
                division_warnings = self._detect_integer_division_patterns(current_esql)
                if division_warnings:
                    result.warnings.extend(division_warnings)
                    for warning in division_warnings:
                        logger.warning(f"⚠️ Query '{query['name']}': {warning['message']}")

                # Detect missing NULL handling in negative filters (silent data loss)
                null_warnings = self._detect_null_handling_issues(current_esql, query.get('name', ''), query.get('description', ''))
                if null_warnings:
                    result.warnings.extend(null_warnings)
                    for warning in null_warnings:
                        logger.warning(f"⚠️ Query '{query['name']}': {warning['message']}")

                # Detect incorrect STDEV function (should be STD_DEV)
                stdev_warnings = self._detect_stdev_errors(current_esql)
                if stdev_warnings:
                    result.warnings.extend(stdev_warnings)
                    for warning in stdev_warnings:
                        logger.warning(f"⚠️ Query '{query['name']}': {warning['message']}")

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

    def _detect_integer_division_patterns(self, esql: str) -> List[Dict]:
        """Detect potential integer division patterns that may produce incorrect results

        Integer division in ES|QL truncates results:
        - (5 - 1) / 5 = 0 (wrong - integer division)
        - (5 - 1) / TO_DOUBLE(5) = 0.8 (correct - float division)

        This is particularly problematic for percentage calculations where results
        appear plausible (0 or 100) but are actually truncated.

        Args:
            esql: ES|QL query string

        Returns:
            List of warning dictionaries with message, pattern, and suggested_fix
        """
        warnings = []

        # Pattern: EVAL statements with division
        # Match: | EVAL field = expression / expression
        eval_division_pattern = r'\|\s*EVAL\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)'

        for match in re.finditer(eval_division_pattern, esql, re.IGNORECASE):
            field_name = match.group(1)
            expression = match.group(2).strip()

            # Check if expression contains division
            if '/' not in expression:
                continue

            # Skip if already using TO_DOUBLE() or TO_LONG()
            if 'TO_DOUBLE(' in expression.upper() or 'TO_LONG(' in expression.upper():
                continue

            # Skip if using float literals (100.0, 1.0, etc.)
            if re.search(r'/\s*\d+\.\d+', expression):
                continue

            # Skip if multiplying by float first (field * 100.0 / ...)
            if re.search(r'\*\s*\d+\.\d+\s*/', expression):
                continue

            # Detect common integer division patterns
            # Pattern 1: (expr) / field
            # Pattern 2: field / field
            # Pattern 3: agg_result / agg_result (e.g., failures / attempts)
            division_match = re.search(r'(.+?)\s*/\s*([a-zA-Z_][a-zA-Z0-9_]*|\([^)]+\))', expression)

            if division_match:
                numerator = division_match.group(1).strip()
                denominator = division_match.group(2).strip()

                # Extract the exact division operation
                original_pattern = f"{numerator} / {denominator}"

                # Generate suggested fix
                # If denominator is a simple field, wrap it in TO_DOUBLE()
                if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', denominator):
                    suggested_fix = f"{numerator} / TO_DOUBLE({denominator})"
                else:
                    # For complex expressions, suggest wrapping whole division or numerator
                    suggested_fix = f"TO_DOUBLE({numerator}) / {denominator}"

                # Check if this looks like a percentage calculation (common pattern)
                is_percentage = '*' in expression and ('100' in expression or 'pct' in field_name.lower() or 'rate' in field_name.lower())

                warning_msg = f"Potential integer division in EVAL {field_name}: '{original_pattern}'"
                if is_percentage:
                    warning_msg += " (percentage calculation - integer division will truncate to 0 or 100)"

                warnings.append({
                    'type': 'integer_division',
                    'field': field_name,
                    'message': warning_msg,
                    'pattern': original_pattern,
                    'suggested_fix': f"| EVAL {field_name} = {suggested_fix}",
                    'full_expression': expression,
                    'is_percentage': is_percentage
                })

        return warnings

    def _detect_null_handling_issues(self, esql: str, query_name: str = '', query_description: str = '') -> List[Dict]:
        """Detect negative filters missing NULL checks (silent data loss)

        ES|QL excludes documents with NULL/missing fields from negative filters:
        - WHERE field != "value" excludes docs where field is NULL
        - WHERE NOT(field LIKE "pattern") excludes docs where field is NULL

        This causes silent data loss, especially critical in security/SIEM queries
        where missing data could mean missed threats.

        Args:
            esql: ES|QL query string
            query_name: Query name for context
            query_description: Query description for security classification

        Returns:
            List of warning dictionaries with message, pattern, and suggested_fix
        """
        warnings = []

        # Check if this is a security/SIEM query (extra critical)
        security_keywords = ['security', 'auth', 'threat', 'compliance', 'audit',
                           'siem', 'detection', 'alert', 'incident', 'vulnerability']
        is_security_query = any(keyword in query_name.lower() or keyword in query_description.lower()
                               for keyword in security_keywords)

        # Pattern 1: field != "value" (most common)
        # Matches: | WHERE field != "value"
        inequality_pattern = r'\|\s*WHERE\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*!=\s*([^\s|]+)'

        for match in re.finditer(inequality_pattern, esql, re.IGNORECASE):
            field_name = match.group(1).strip()
            value = match.group(2).strip()

            # Skip guaranteed fields
            if field_name == '@timestamp':
                continue

            # Check if this field already has NULL handling
            null_check_pattern = rf'OR\s+{re.escape(field_name)}\s+IS\s+NULL'
            if re.search(null_check_pattern, esql, re.IGNORECASE):
                continue  # Already has NULL handling

            warning_msg = f"Negative filter on '{field_name}' missing NULL check (silently excludes docs where field is NULL)"
            if is_security_query:
                warning_msg += " - CRITICAL for security queries (missing data = missed threats)"

            warnings.append({
                'type': 'missing_null_check',
                'field': field_name,
                'message': warning_msg,
                'pattern': f"{field_name} != {value}",
                'suggested_fix': f"| WHERE {field_name} != {value} OR {field_name} IS NULL",
                'is_security_query': is_security_query
            })

        # Pattern 2: NOT(field LIKE "pattern")
        # Matches: | WHERE NOT(field LIKE "pattern")
        not_like_pattern = r'\|\s*WHERE\s+NOT\s*\(\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s+LIKE\s+([^\)]+)\)'

        for match in re.finditer(not_like_pattern, esql, re.IGNORECASE):
            field_name = match.group(1).strip()
            pattern_value = match.group(2).strip()

            # Skip guaranteed fields
            if field_name == '@timestamp':
                continue

            # Check if this field already has NULL handling
            null_check_pattern = rf'OR\s+{re.escape(field_name)}\s+IS\s+NULL'
            if re.search(null_check_pattern, esql, re.IGNORECASE):
                continue

            warning_msg = f"NOT LIKE filter on '{field_name}' missing NULL check (silently excludes docs where field is NULL)"
            if is_security_query:
                warning_msg += " - CRITICAL for security queries"

            warnings.append({
                'type': 'missing_null_check',
                'field': field_name,
                'message': warning_msg,
                'pattern': f"NOT({field_name} LIKE {pattern_value})",
                'suggested_fix': f"| WHERE NOT({field_name} LIKE {pattern_value}) OR {field_name} IS NULL",
                'is_security_query': is_security_query
            })

        # Pattern 3: NOT(field == "value")
        # Matches: | WHERE NOT(field == "value")
        not_equals_pattern = r'\|\s*WHERE\s+NOT\s*\(\s*([a-zA-Z_][a-zA-Z0-9_.]*)\s*==\s*([^\)]+)\)'

        for match in re.finditer(not_equals_pattern, esql, re.IGNORECASE):
            field_name = match.group(1).strip()
            value = match.group(2).strip()

            # Skip guaranteed fields
            if field_name == '@timestamp':
                continue

            # Check if this field already has NULL handling
            null_check_pattern = rf'OR\s+{re.escape(field_name)}\s+IS\s+NULL'
            if re.search(null_check_pattern, esql, re.IGNORECASE):
                continue

            warning_msg = f"NOT filter on '{field_name}' missing NULL check (silently excludes docs where field is NULL)"
            if is_security_query:
                warning_msg += " - CRITICAL for security queries"

            warnings.append({
                'type': 'missing_null_check',
                'field': field_name,
                'message': warning_msg,
                'pattern': f"NOT({field_name} == {value})",
                'suggested_fix': f"| WHERE NOT({field_name} == {value}) OR {field_name} IS NULL",
                'is_security_query': is_security_query
            })

        return warnings

    def _detect_stdev_errors(self, esql: str) -> List[Dict]:
        """Detect incorrect STDEV function usage (should be STD_DEV)

        ES|QL uses STD_DEV() not STDEV() or STDDEV(). This is a syntax error that will
        cause query execution to fail with "Unknown function [STDEV]".

        Returns:
            List of warning dictionaries with type, message, and suggested fix
        """
        warnings = []

        # Check for STDEV( - case insensitive
        import re
        stdev_pattern = re.compile(r'\bSTDEV\s*\(', re.IGNORECASE)
        matches = stdev_pattern.findall(esql)

        if matches:
            warnings.append({
                'type': 'incorrect_function_name',
                'function': 'STDEV',
                'message': f"Query uses STDEV() which does not exist. Use STD_DEV() instead. Found {len(matches)} occurrence(s).",
                'suggested_fix': "Replace STDEV( with STD_DEV( in all aggregations",
                'severity': 'error'  # This will cause query execution to fail
            })

        return warnings
