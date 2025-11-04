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

        for attempt in range(max_attempts):
            result.fix_attempts = attempt + 1

            # Replace dataset names with actual index names in query
            executed_esql = self._replace_index_names(current_esql, indexed_datasets)

            # Test the query
            success, response, error = self.indexer.execute_esql(executed_esql)

            if success:
                result.was_fixed = True
                result.final_esql = current_esql
                result.fix_history.append({
                    'attempt': attempt + 1,
                    'succeeded': True,
                    'esql': current_esql
                })
                logger.info(f"Query '{query['name']}' succeeded on attempt {attempt + 1}")
                break

            # Capture first error
            if attempt == 0:
                result.original_error = error

            logger.warning(f"Query '{query['name']}' failed on attempt {attempt + 1}: {error}")

            # Try to fix with LLM
            if attempt < max_attempts - 1:
                try:
                    fixed_esql = self._fix_query_with_llm(
                        query=query,
                        error=error,
                        indexed_datasets=indexed_datasets,
                        attempt=attempt
                    )

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

    def _fix_query_with_llm(
        self,
        query: Dict,
        error: str,
        indexed_datasets: Dict,
        attempt: int
    ) -> str:
        """Use LLM to fix a failed query

        Args:
            query: Original query dictionary
            error: Error message from Elasticsearch
            indexed_datasets: Available indices
            attempt: Current attempt number

        Returns:
            Fixed ES|QL query string
        """
        # Import and use our strict ES|QL rules
        try:
            from src.prompts.esql_strict_rules import get_rules_for_query_fixing
            esql_rules = get_rules_for_query_fixing()
        except ImportError:
            # Fallback if import fails
            esql_rules = self._read_esql_skill()

        # Format data profile if available (using compact mode)
        data_profile_text = ""
        if self.data_profile:
            try:
                from src.services.data_profiler import DataProfiler
                data_profile_text = "\n\n" + DataProfiler.format_profile_for_llm(self.data_profile, compact=True)
            except Exception as e:
                logger.warning(f"Could not format data profile: {e}")

        prompt = f"""Fix this ES|QL query that failed with an error.

**Query Name:** {query['name']}
**Description:** {query.get('description', 'N/A')}

**Original Query:**
```esql
{query.get('esql') or query.get('query') or query.get('esql_query', '')}
```

**Error:**
```
{error}
```

**Available Indices:**
{json.dumps(indexed_datasets, indent=2)}
{data_profile_text}

**ES|QL Fix Rules:**
{esql_rules}

**Your Task:**
Analyze the error and apply the fix rules. Follow the transformations IN ORDER:
1. Remove ALL _lookup suffixes (never add them)
2. Fix MATCH syntax (must be in WHERE clause)
3. Fix FORK (no named branches)
4. Remove parameter NULL checks
5. Fix DATE function parameter order
6. Replace invalid aggregates (COUNT_IF, etc.)

Provide ONLY the corrected ES|QL query (no explanations).

**Attempt {attempt + 1} of 3.**

Corrected query:"""

        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for precise fixes
                messages=[{"role": "user", "content": prompt}]
            )

            fixed_query = response.content[0].text.strip()

            # Extract query from code blocks if present
            if "```" in fixed_query:
                # Find the code block
                parts = fixed_query.split("```")
                for i, part in enumerate(parts):
                    if i % 2 == 1:  # Odd indices are code blocks
                        # Remove language identifier if present
                        lines = part.strip().split('\n')
                        if lines[0].lower() in ['esql', 'sql']:
                            fixed_query = '\n'.join(lines[1:])
                        else:
                            fixed_query = part.strip()
                        break

            logger.info(f"LLM generated fix for '{query['name']}'")
            return fixed_query.strip()

        except Exception as e:
            logger.error(f"LLM fix failed: {e}", exc_info=True)
            raise

    def _read_esql_skill(self) -> str:
        """Read ES|QL skill documentation for reference"""
        try:
            from pathlib import Path
            skill_path = Path('.claude/skills/esql-advanced-commands.md')
            if skill_path.exists():
                content = skill_path.read_text()
                # Truncate to first 1000 chars to save tokens
                return content[:2000] + "\n...(truncated)"
            else:
                return self._get_minimal_esql_reference()
        except Exception as e:
            logger.warning(f"Could not read ES|QL skill: {e}")
            return self._get_minimal_esql_reference()

    def _get_minimal_esql_reference(self) -> str:
        """Get minimal ES|QL reference"""
        return """
ES|QL Key Commands:
- FROM: Specify index/data stream
- WHERE: Filter rows
- EVAL: Create calculated fields
- STATS: Aggregate with GROUP BY
- LOOKUP JOIN: Enrich with lookup data (requires _lookup suffix)
- INLINESTATS: Calculate aggregates keeping all rows
- DATE_TRUNC: Bucket timestamps
- DATE_EXTRACT: Extract date parts (syntax: DATE_EXTRACT("part", field))
- SORT: Order results
- LIMIT: Limit result count
- KEEP/DROP: Select/exclude columns
"""

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
