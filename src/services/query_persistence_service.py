"""
Query Persistence Service - Save edited queries back to demo modules

This service handles:
- Saving edited queries to query_generator.py files
- Creating backups before modifying module files
- Updating the all_queries.json cache
- Preserving module structure and Python syntax
"""

import os
import json
import shutil
import ast
import re
import sys
import importlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging

# Import streamlit for cache clearing
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False
    # Streamlit not available - cache clearing will be skipped

logger = logging.getLogger(__name__)


class QueryPersistenceService:
    """Service for persisting edited queries back to demo modules."""

    def __init__(self, module_path: str):
        """Initialize the query persistence service.

        Args:
            module_path: Path to the demo module directory
        """
        self.module_path = Path(module_path)
        self.query_generator_path = self.module_path / "query_generator.py"
        self.all_queries_path = self.module_path / "all_queries.json"
        self.backups_dir = self.module_path / "backups"

    def save_edited_query(
        self,
        query_id: str,
        query_type: str,
        edited_esql: str,
        original_query: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Save an edited query back to the module files.

        Args:
            query_id: Query identifier (e.g., "scripted_query_1")
            query_type: Type of query (scripted, parameterized, rag)
            edited_esql: The edited ES|QL query text
            original_query: The original query dictionary

        Returns:
            Tuple of (success, message)
        """
        try:
            # Extract query index from ID
            match = re.match(r"(\w+)_query_(\d+)", query_id)
            if not match:
                return False, f"Invalid query ID format: {query_id}"

            query_index = int(match.group(2)) - 1  # Convert to 0-based index

            # Create backup before modifying
            backup_path = self._create_backup()
            logger.info(f"Created backup at: {backup_path}")

            # Update the Python module
            success, message = self._update_query_generator(
                query_type, query_index, edited_esql, original_query
            )
            if not success:
                return False, message

            # Update the JSON cache
            success, message = self._update_all_queries_json(
                query_type, query_index, edited_esql, original_query
            )
            if not success:
                # Rollback Python changes if JSON update fails
                self._restore_from_backup(backup_path)
                return False, f"Failed to update JSON cache: {message}"

            # Update the query testing results if it exists
            success, message = self._update_query_testing_results(
                edited_esql, original_query
            )
            # Log but don't fail if testing results can't be updated
            if not success:
                logger.warning(f"Could not update query_testing_results.json: {message}")

            # Clear Python module cache to ensure fresh imports
            self._clear_module_cache()

            # Clear Streamlit cache to force UI to reload queries
            self._clear_streamlit_cache()

            return True, f"Query saved successfully. Backup created at: {backup_path.name}"

        except Exception as e:
            logger.error(f"Error saving query: {e}")
            return False, f"Error saving query: {str(e)}"

    def _create_backup(self) -> Path:
        """Create a backup of the current query_generator.py file.

        Returns:
            Path to the backup file
        """
        # Create backups directory if it doesn't exist
        self.backups_dir.mkdir(exist_ok=True)

        # Create timestamped backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"query_generator_{timestamp}.py"
        backup_path = self.backups_dir / backup_name

        # Copy the current file
        if self.query_generator_path.exists():
            shutil.copy2(self.query_generator_path, backup_path)

        return backup_path

    def _restore_from_backup(self, backup_path: Path):
        """Restore query_generator.py from a backup.

        Args:
            backup_path: Path to the backup file
        """
        if backup_path.exists():
            shutil.copy2(backup_path, self.query_generator_path)
            logger.info(f"Restored from backup: {backup_path}")

    def _clear_module_cache(self):
        """Clear the Python module cache for the demo module.

        This ensures that subsequent imports of the module will read
        the updated file from disk rather than using the cached version.
        """
        try:
            # Get the module name from the path
            module_name = self.module_path.name

            # Build the module paths that might be cached
            module_patterns = [
                f"demos.{module_name}.query_generator",
                f"demos.{module_name}.data_generator",
                f"demos.{module_name}",
            ]

            # Remove matching modules from cache
            modules_to_remove = []
            for key in sys.modules:
                for pattern in module_patterns:
                    if key == pattern or key.startswith(pattern + "."):
                        modules_to_remove.append(key)

            for module_key in modules_to_remove:
                del sys.modules[module_key]
                logger.debug(f"Cleared module from cache: {module_key}")

            if modules_to_remove:
                logger.info(f"Cleared {len(modules_to_remove)} module(s) from Python cache")

        except Exception as e:
            # Log but don't fail - cache clearing is a best effort
            logger.warning(f"Could not clear module cache: {e}")

    def _clear_streamlit_cache(self):
        """Clear Streamlit's data cache to ensure fresh query loads.

        This forces the UI to reload queries from disk rather than
        serving cached data from memory.
        """
        if HAS_STREAMLIT:
            try:
                # Clear all cached data
                st.cache_data.clear()
                logger.info("Cleared Streamlit cache for fresh query loading")
            except Exception as e:
                # Log but don't fail - cache clearing is a best effort
                logger.warning(f"Could not clear Streamlit cache: {e}")
        else:
            logger.debug("Streamlit not available, skipping cache clear")

    def _update_query_generator(
        self,
        query_type: str,
        query_index: int,
        edited_esql: str,
        original_query: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Update the query_generator.py file with the edited query.

        Args:
            query_type: Type of query (scripted, parameterized, rag)
            query_index: 0-based index of the query in its list
            edited_esql: The edited ES|QL query text
            original_query: The original query dictionary

        Returns:
            Tuple of (success, message)
        """
        try:
            # Read the current module
            with open(self.query_generator_path, 'r') as f:
                module_content = f.read()

            # Parse the AST to find the method
            tree = ast.parse(module_content)

            # First check if this is a newer format with single generate_queries method
            has_single_method = False
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == 'generate_queries':
                    has_single_method = True
                    break

            if has_single_method:
                # Newer format - all queries in one method
                query_name = original_query.get('name')
                found_and_updated = False

                # Log for debugging
                logger.info(f"Looking for query: {query_name}")

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == 'generate_queries':
                        # Look through all statements in the method
                        for stmt in node.body:
                            # Check if it's an append to queries list
                            if (isinstance(stmt, ast.Expr) and
                                isinstance(stmt.value, ast.Call) and
                                isinstance(stmt.value.func, ast.Attribute) and
                                stmt.value.func.attr == 'append'):

                                # Get the dict being appended
                                if len(stmt.value.args) > 0 and isinstance(stmt.value.args[0], ast.Dict):
                                    query_dict = stmt.value.args[0]

                                    # Check if this is the right query by name
                                    name_found = False
                                    name_value = None
                                    for i, key in enumerate(query_dict.keys):
                                        # Handle both ast.Constant (Python 3.8+) and ast.Str (older versions)
                                        key_value = None
                                        if isinstance(key, ast.Constant):
                                            key_value = key.value
                                        elif hasattr(ast, 'Str') and isinstance(key, ast.Str):
                                            key_value = key.s

                                        if key_value == 'name':
                                            # Get the name value
                                            if isinstance(query_dict.values[i], ast.Constant):
                                                name_value = query_dict.values[i].value
                                            elif hasattr(ast, 'Str') and isinstance(query_dict.values[i], ast.Str):
                                                name_value = query_dict.values[i].s

                                            if name_value == query_name:
                                                name_found = True
                                                logger.info(f"Found query by name: {query_name}")
                                                break

                                    if name_found:
                                        # Found the right query, now update its query field
                                        for j, key2 in enumerate(query_dict.keys):
                                            key_value = None
                                            if isinstance(key2, ast.Constant):
                                                key_value = key2.value
                                            elif hasattr(ast, 'Str') and isinstance(key2, ast.Str):
                                                key_value = key2.s

                                            if key_value in ['query', 'esql', 'esql_query']:
                                                # Update the query text
                                                logger.info(f"Updating query field '{key_value}' with new ES|QL")
                                                query_dict.values[j] = ast.Constant(value=edited_esql)
                                                found_and_updated = True
                                                break
                                    if found_and_updated:
                                        break
                            if found_and_updated:
                                break

                if not found_and_updated:
                    # Try fallback with counting queries of the same type
                    type_count = 0
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and node.name == 'generate_queries':
                            for stmt in node.body:
                                if (isinstance(stmt, ast.Expr) and
                                    isinstance(stmt.value, ast.Call) and
                                    isinstance(stmt.value.func, ast.Attribute) and
                                    stmt.value.func.attr == 'append'):

                                    if len(stmt.value.args) > 0 and isinstance(stmt.value.args[0], ast.Dict):
                                        query_dict = stmt.value.args[0]

                                        # Check query type
                                        for i, key in enumerate(query_dict.keys):
                                            if isinstance(key, ast.Constant) and key.value == 'query_type':
                                                if isinstance(query_dict.values[i], ast.Constant) and query_dict.values[i].value == query_type:
                                                    if type_count == query_index:
                                                        # Found the right query by index
                                                        for j, key2 in enumerate(query_dict.keys):
                                                            if isinstance(key2, ast.Constant) and key2.value in ['query', 'esql', 'esql_query']:
                                                                # Update the query text
                                                                query_dict.values[j] = ast.Constant(value=edited_esql)
                                                                found_and_updated = True
                                                                break
                                                    type_count += 1
                                                    break
                                        if found_and_updated:
                                            break
                                if found_and_updated:
                                    break

            else:
                # Older format - separate methods for each query type
                method_map = {
                    'scripted': 'generate_scripted_queries',
                    'parameterized': 'generate_parameterized_queries',
                    'rag': 'generate_rag_queries'
                }

                target_method = method_map.get(query_type)
                if not target_method:
                    return False, f"Unknown query type: {query_type}"

                # Find and update the method
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == target_method:
                        # Find the return statement
                        for stmt in node.body:
                            if isinstance(stmt, ast.Return) and isinstance(stmt.value, ast.List):
                                # Update the specific query in the list
                                if query_index < len(stmt.value.elts):
                                    query_dict_node = stmt.value.elts[query_index]

                                    # Update the esql field in the dictionary
                                    if isinstance(query_dict_node, ast.Dict):
                                        for i, key in enumerate(query_dict_node.keys):
                                            if isinstance(key, ast.Constant) and key.value in ['esql', 'query', 'esql_query']:
                                                # Create new string node with edited query
                                                query_dict_node.values[i] = ast.Constant(value=edited_esql)
                                                break

            # Check if we actually found and updated the query
            if not found_and_updated and has_single_method:
                logger.warning(f"Query '{query_name}' not found in module")
                return False, f"Query '{query_name}' not found in module"

            # Convert AST back to Python code
            import astor
            updated_code = astor.to_source(tree)

            # Write the updated code
            with open(self.query_generator_path, 'w') as f:
                f.write(updated_code)

            logger.info(f"Successfully updated query generator with new ES|QL for '{query_name}'")
            return True, "Query generator updated successfully"

        except ImportError:
            # Fallback to regex-based replacement if astor is not available
            return self._update_query_generator_regex(
                query_type, query_index, edited_esql, original_query, module_content
            )
        except Exception as e:
            logger.error(f"Error updating query generator: {e}")
            return False, str(e)

    def _update_query_generator_regex(
        self,
        query_type: str,
        query_index: int,
        edited_esql: str,
        original_query: Dict[str, Any],
        module_content: str
    ) -> Tuple[bool, str]:
        """Update query_generator.py using regex (fallback method).

        Args:
            query_type: Type of query
            query_index: 0-based index of the query
            edited_esql: The edited ES|QL query text
            original_query: The original query dictionary
            module_content: Current content of the module

        Returns:
            Tuple of (success, message)
        """
        try:
            # Try different field names that might contain the query
            original_esql = None
            for field_name in ['esql', 'esql_query', 'query']:
                if field_name in original_query:
                    original_esql = original_query[field_name]
                    break

            if not original_esql:
                return False, "Original query text not found in any expected field (esql, esql_query, query)"

            # Escape special regex characters
            escaped_original = re.escape(original_esql)

            # Try to find and replace with different field names and quote styles
            patterns_to_try = []

            # For newer modules using 'query' field with triple quotes
            patterns_to_try.append(
                (r"(\s*['\"]query['\"]\s*:\s*''')" + escaped_original + r"(''')",
                 lambda m: m.group(1) + edited_esql + m.group(2))
            )
            patterns_to_try.append(
                (r'(\s*["\']query["\']\s*:\s*""")' + escaped_original + r'(""")',
                 lambda m: m.group(1) + edited_esql + m.group(2))
            )

            # For older modules using 'esql' field
            patterns_to_try.append(
                (r"(\s*['\"]esql['\"]\s*:\s*['\"])" + escaped_original + r"(['\"])",
                 lambda m: m.group(1) + edited_esql + m.group(2))
            )
            patterns_to_try.append(
                (r"(\s*['\"]esql['\"]\s*:\s*''')" + escaped_original + r"(''')",
                 lambda m: m.group(1) + edited_esql + m.group(2))
            )
            patterns_to_try.append(
                (r'(\s*["\']esql["\']\s*:\s*""")' + escaped_original + r'(""")',
                 lambda m: m.group(1) + edited_esql + m.group(2))
            )

            # Try each pattern
            updated_content = module_content
            for pattern_str, replacement_func in patterns_to_try:
                pattern = re.compile(pattern_str, re.MULTILINE | re.DOTALL)
                if pattern.search(updated_content):
                    updated_content = pattern.sub(replacement_func, updated_content, count=1)
                    break

            # Verify the replacement was made
            if updated_content == module_content:
                return False, "Could not find query to replace in module. The query structure may have changed."

            # Write the updated content
            with open(self.query_generator_path, 'w') as f:
                f.write(updated_content)

            return True, "Query generator updated successfully"

        except Exception as e:
            logger.error(f"Error in regex update: {e}")
            return False, str(e)

    def _update_all_queries_json(
        self,
        query_type: str,
        query_index: int,
        edited_esql: str,
        original_query: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Update the all_queries.json cache file.

        Args:
            query_type: Type of query (scripted, parameterized, rag)
            query_index: 0-based index of the query in its list
            edited_esql: The edited ES|QL query text
            original_query: The original query dictionary

        Returns:
            Tuple of (success, message)
        """
        try:
            # Read current JSON
            if self.all_queries_path.exists():
                with open(self.all_queries_path, 'r') as f:
                    all_queries = json.load(f)
            else:
                all_queries = {
                    'scripted': [],
                    'parameterized': [],
                    'rag': []
                }

            # Check if this is a newer format with "all" array
            if 'all' in all_queries and isinstance(all_queries['all'], list):
                # Newer format - all queries in "all" array
                # We need to find the right query to update
                # Try to match by name or other unique identifier
                query_name = original_query.get('name')

                updated = False
                for i, q in enumerate(all_queries['all']):
                    if q.get('name') == query_name:
                        # Update the query - check which field contains the query text
                        if 'esql_query' in q:
                            q['esql_query'] = edited_esql
                        elif 'esql' in q:
                            q['esql'] = edited_esql
                        elif 'query' in q:
                            q['query'] = edited_esql

                        # Add metadata about the edit
                        q['last_edited'] = datetime.now().isoformat()
                        q['edited'] = True
                        updated = True
                        break

                if not updated:
                    # If we can't find by name, try by index in the full list
                    # Count queries of the requested type up to our index
                    type_count = 0
                    for i, q in enumerate(all_queries['all']):
                        if q.get('query_type', 'scripted') == query_type:
                            if type_count == query_index:
                                # This is our query
                                if 'esql_query' in q:
                                    q['esql_query'] = edited_esql
                                elif 'esql' in q:
                                    q['esql'] = edited_esql
                                elif 'query' in q:
                                    q['query'] = edited_esql

                                # Add metadata about the edit
                                q['last_edited'] = datetime.now().isoformat()
                                q['edited'] = True
                                updated = True
                                break
                            type_count += 1

                if updated:
                    # Write back the updated JSON
                    with open(self.all_queries_path, 'w') as f:
                        json.dump(all_queries, f, indent=2)
                    return True, "JSON cache updated successfully"
                else:
                    return False, f"Could not find query to update in JSON cache"

            else:
                # Older format - separate arrays for each query type
                # Update the specific query
                if query_type in all_queries and query_index < len(all_queries[query_type]):
                    all_queries[query_type][query_index]['esql'] = edited_esql

                    # Add metadata about the edit
                    all_queries[query_type][query_index]['last_edited'] = datetime.now().isoformat()
                    all_queries[query_type][query_index]['edited'] = True

                    # Write back the updated JSON
                    with open(self.all_queries_path, 'w') as f:
                        json.dump(all_queries, f, indent=2)

                    return True, "JSON cache updated successfully"
                else:
                    return False, f"Query not found at index {query_index} in {query_type} queries"

        except Exception as e:
            logger.error(f"Error updating JSON cache: {e}")
            return False, str(e)

    def _update_query_testing_results(
        self,
        edited_esql: str,
        original_query: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Update the query_testing_results.json file with the edited query.

        This prevents auto-fixed queries from overriding user edits.

        Args:
            edited_esql: The edited ES|QL query text
            original_query: The original query dictionary

        Returns:
            Tuple of (success, message)
        """
        try:
            test_results_path = self.module_path / 'query_testing_results.json'
            if not test_results_path.exists():
                # No testing results to update
                return True, "No query testing results file to update"

            with open(test_results_path, 'r') as f:
                test_results = json.load(f)

            query_name = original_query.get('name')
            if not query_name:
                return False, "Query has no name field"

            # Find the query in the test results
            updated = False
            for query_result in test_results.get('queries', []):
                if query_result.get('name') == query_name:
                    # Update the final_esql field with the user's edit
                    query_result['final_esql'] = edited_esql
                    query_result['manually_edited'] = True
                    query_result['edited_at'] = datetime.now().isoformat()

                    # Also update the fix history if it exists
                    if query_result.get('fix_history'):
                        # Add a new entry to fix history showing manual edit
                        query_result['fix_history'].append({
                            'attempt': len(query_result['fix_history']) + 1,
                            'succeeded': True,
                            'esql': edited_esql,
                            'manual_edit': True,
                            'edited_at': datetime.now().isoformat()
                        })

                    updated = True
                    break

            if updated:
                # Write back the updated test results
                with open(test_results_path, 'w') as f:
                    json.dump(test_results, f, indent=2)
                logger.info(f"Updated query testing results for '{query_name}'")
                return True, "Query testing results updated successfully"
            else:
                # Query not found in test results - this is OK
                return True, f"Query '{query_name}' not found in test results (may not have been tested)"

        except Exception as e:
            logger.error(f"Error updating query testing results: {e}")
            return False, str(e)

    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Get a list of available backups.

        Returns:
            List of backup information dictionaries
        """
        backups = []
        if self.backups_dir.exists():
            for backup_file in self.backups_dir.glob("query_generator_*.py"):
                # Parse timestamp from filename
                match = re.match(r"query_generator_(\d{8}_\d{6})\.py", backup_file.name)
                if match:
                    timestamp_str = match.group(1)
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                    backups.append({
                        'filename': backup_file.name,
                        'path': str(backup_file),
                        'timestamp': timestamp.isoformat(),
                        'size': backup_file.stat().st_size,
                        'age_hours': (datetime.now() - timestamp).total_seconds() / 3600
                    })

        # Sort by timestamp, newest first
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups

    def restore_backup(self, backup_filename: str) -> Tuple[bool, str]:
        """Restore a specific backup.

        Args:
            backup_filename: Name of the backup file to restore

        Returns:
            Tuple of (success, message)
        """
        try:
            backup_path = self.backups_dir / backup_filename
            if not backup_path.exists():
                return False, f"Backup file not found: {backup_filename}"

            # Create a backup of current before restoring
            current_backup = self._create_backup()

            # Restore the selected backup
            self._restore_from_backup(backup_path)

            return True, f"Restored from {backup_filename}. Current version backed up as {current_backup.name}"

        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False, str(e)