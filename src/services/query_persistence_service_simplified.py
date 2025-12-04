"""
Simplified Query Persistence Service - Save edited queries back to demo modules

This refactored version removes unnecessary complexity:
- No module cache clearing (app restarts handle this)
- No Streamlit cache clearing (app restarts handle this)
- No regex fallback (astor is always available)
- Simplified AST manipulation
- Focused on the core requirement: persist edits to 3 files
"""

import json
import shutil
import ast
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging
import astor

logger = logging.getLogger(__name__)


class QueryPersistenceService:
    """Simplified service for persisting edited queries back to demo modules."""

    def __init__(self, module_path: str):
        """Initialize the query persistence service.

        Args:
            module_path: Path to the demo module directory
        """
        self.module_path = Path(module_path)
        self.query_generator_path = self.module_path / "query_generator.py"
        self.all_queries_path = self.module_path / "all_queries.json"
        self.test_results_path = self.module_path / "query_testing_results.json"
        self.backups_dir = self.module_path / "backups"

    def save_edited_query(
        self,
        query_id: str,
        query_type: str,
        edited_esql: str,
        original_query: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Save an edited query back to the module files.

        This is the main entry point that coordinates updates to:
        1. query_generator.py (Python source)
        2. all_queries.json (JSON cache)
        3. query_testing_results.json (testing results - the critical fix!)

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
                edited_esql, original_query
            )
            if not success:
                # Rollback Python changes if JSON update fails
                self._restore_from_backup(backup_path)
                return False, f"Failed to update JSON cache: {message}"

            # Update the query testing results (THE KEY FIX!)
            success, message = self._update_query_testing_results(
                edited_esql, original_query
            )
            if not success:
                logger.warning(f"Could not update query_testing_results.json: {message}")

            return True, f"Query saved successfully. Backup created at: {backup_path.name}"

        except Exception as e:
            logger.error(f"Error saving query: {e}")
            return False, f"Error saving query: {str(e)}"

    def _create_backup(self) -> Path:
        """Create a backup of the current query_generator.py file."""
        self.backups_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"query_generator_{timestamp}.py"
        backup_path = self.backups_dir / backup_name

        if self.query_generator_path.exists():
            shutil.copy2(self.query_generator_path, backup_path)

        return backup_path

    def _restore_from_backup(self, backup_path: Path):
        """Restore query_generator.py from a backup."""
        if backup_path.exists():
            shutil.copy2(backup_path, self.query_generator_path)
            logger.info(f"Restored from backup: {backup_path}")

    def _update_query_generator(
        self,
        query_type: str,
        query_index: int,
        edited_esql: str,
        original_query: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Update the query_generator.py file with the edited query.

        Simplified approach:
        - Only handles modern format (single generate_queries method)
        - Uses AST to find and update the specific query by name
        - No fallback methods needed
        """
        try:
            with open(self.query_generator_path, 'r') as f:
                module_content = f.read()

            tree = ast.parse(module_content)
            query_name = original_query.get('name')
            found_and_updated = False

            # Find the generate_queries function
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

                                # Check if this is our query by name
                                for i, key in enumerate(query_dict.keys):
                                    if (isinstance(key, ast.Constant) and
                                        key.value == 'name' and
                                        isinstance(query_dict.values[i], ast.Constant) and
                                        query_dict.values[i].value == query_name):

                                        # Found it! Update the esql_query field
                                        for j, key in enumerate(query_dict.keys):
                                            if isinstance(key, ast.Constant) and key.value in ['esql_query', 'esql', 'query']:
                                                query_dict.values[j] = ast.Constant(value=edited_esql)
                                                found_and_updated = True
                                                logger.info(f"Updated query '{query_name}' in AST")
                                                break
                                        break

                        if found_and_updated:
                            break

                    if found_and_updated:
                        break

            if not found_and_updated:
                return False, f"Could not find query '{query_name}' in module"

            # Convert AST back to source code
            updated_code = astor.to_source(tree)

            # Write the updated code
            with open(self.query_generator_path, 'w') as f:
                f.write(updated_code)

            return True, "Successfully updated query_generator.py"

        except Exception as e:
            logger.error(f"Error updating query_generator.py: {e}")
            return False, str(e)

    def _update_all_queries_json(
        self,
        edited_esql: str,
        original_query: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Update the all_queries.json cache file."""
        try:
            if not self.all_queries_path.exists():
                return True, "No all_queries.json to update"

            with open(self.all_queries_path, 'r') as f:
                data = json.load(f)

            query_name = original_query.get('name')
            updated = False

            # Update in the 'all' array
            for query in data.get('all', []):
                if query.get('name') == query_name:
                    # Update the ES|QL field (could be named differently)
                    if 'esql_query' in query:
                        query['esql_query'] = edited_esql
                    elif 'esql' in query:
                        query['esql'] = edited_esql
                    elif 'query' in query:
                        query['query'] = edited_esql
                    updated = True
                    break

            if updated:
                with open(self.all_queries_path, 'w') as f:
                    json.dump(data, f, indent=2)
                return True, "Successfully updated all_queries.json"
            else:
                return False, f"Query '{query_name}' not found in all_queries.json"

        except Exception as e:
            logger.error(f"Error updating all_queries.json: {e}")
            return False, str(e)

    def _update_query_testing_results(
        self,
        edited_esql: str,
        original_query: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Update the query_testing_results.json file - THE CRITICAL FIX!

        This was the root cause of edits not persisting. The UI was loading
        "auto-fixed" queries from this file, overriding user edits.
        """
        try:
            if not self.test_results_path.exists():
                return True, "No query_testing_results.json to update"

            with open(self.test_results_path, 'r') as f:
                data = json.load(f)

            query_name = original_query.get('name')
            updated = False

            # Update in the queries array
            for query in data.get('queries', []):
                if query.get('name') == query_name:
                    # Update the final_esql field (this was being used by UI)
                    query['final_esql'] = edited_esql
                    # Mark as manually edited
                    query['manually_edited'] = True
                    query['edited_at'] = datetime.now().isoformat()
                    updated = True
                    break

            if updated:
                with open(self.test_results_path, 'w') as f:
                    json.dump(data, f, indent=2)
                return True, "Successfully updated query_testing_results.json"
            else:
                # Query might not exist in test results, which is okay
                return True, f"Query '{query_name}' not in test results (okay)"

        except Exception as e:
            logger.error(f"Error updating query_testing_results.json: {e}")
            return False, str(e)

    def get_backup_list(self) -> List[Dict[str, Any]]:
        """Get list of available backups."""
        if not self.backups_dir.exists():
            return []

        backups = []
        for backup_file in self.backups_dir.glob("query_generator_*.py"):
            backups.append({
                'filename': backup_file.name,
                'path': str(backup_file),
                'timestamp': backup_file.stat().st_mtime,
                'size': backup_file.stat().st_size
            })

        # Sort by timestamp, newest first
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups

    def restore_backup(self, backup_filename: str) -> Tuple[bool, str]:
        """Restore a specific backup."""
        backup_path = self.backups_dir / backup_filename

        if not backup_path.exists():
            return False, f"Backup file not found: {backup_filename}"

        try:
            shutil.copy2(backup_path, self.query_generator_path)

            # Also need to regenerate the JSON files from the restored Python
            # This ensures consistency across all three files
            self._regenerate_json_from_python()

            return True, f"Successfully restored from backup: {backup_filename}"
        except Exception as e:
            return False, f"Error restoring backup: {str(e)}"

    def _regenerate_json_from_python(self):
        """Regenerate JSON files from the Python source.

        This ensures all three files stay in sync after a restore.
        """
        try:
            # Import the module and get queries
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "query_generator",
                self.query_generator_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get queries from the module
            if hasattr(module, 'generate_queries'):
                # Pass empty datasets as the function expects it
                queries = module.generate_queries({})

                # Update all_queries.json
                if self.all_queries_path.exists():
                    with open(self.all_queries_path, 'w') as f:
                        json.dump({"all": queries}, f, indent=2)

                # Update query_testing_results.json
                if self.test_results_path.exists():
                    with open(self.test_results_path, 'r') as f:
                        test_data = json.load(f)

                    # Update final_esql for each query
                    for query in queries:
                        for test_query in test_data.get('queries', []):
                            if test_query.get('name') == query.get('name'):
                                esql_field = query.get('esql_query') or query.get('esql') or query.get('query')
                                if esql_field:
                                    test_query['final_esql'] = esql_field
                                    test_query['restored_from_backup'] = True

                    with open(self.test_results_path, 'w') as f:
                        json.dump(test_data, f, indent=2)

        except Exception as e:
            logger.warning(f"Could not regenerate JSON from Python: {e}")