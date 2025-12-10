"""
Progress Tracking Service for Vulcan demo modules.

Handles:
- Progress persistence (progress.json in each module)
- Syncing with existing validation files
- Progress calculation
- Reset functionality
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

logger = logging.getLogger(__name__)

# Global cache for auto-sync results to avoid repeated API calls
_auto_sync_cache: Dict[str, float] = {}  # module_name -> last_sync_timestamp
AUTO_SYNC_COOLDOWN_SECONDS = 300  # Only auto-sync once every 5 minutes per module


class ProgressTrackingService:
    """
    Service for tracking demo module completion progress.

    Progress is stored in progress.json within each module directory
    and syncs with existing validation files (validated_queries.json, tool_metadata.json).
    """

    def __init__(self, module_path: str):
        """
        Initialize progress tracking for a specific module.

        Args:
            module_path: Path to the demo module directory
        """
        self.module_path = Path(module_path)
        self.progress_file = self.module_path / "progress.json"
        self.validated_queries_file = self.module_path / "validated_queries.json"
        self.tool_metadata_file = self.module_path / "tool_metadata.json"

        # Load or create progress data
        self.progress_data = self._load_progress()

    def _load_progress(self) -> Dict[str, Any]:
        """Load progress data from file or create default structure."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    # Ensure all required keys exist
                    return self._ensure_structure(data)
            except Exception as e:
                logger.warning(f"Error loading progress file: {e}")

        # Return default structure
        return self._get_default_structure()

    def _get_default_structure(self) -> Dict[str, Any]:
        """Get default progress data structure."""
        return {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "data_indexed": False,
            "data_indexed_at": None,
            "agent_deployed": False,
            "agent_deployed_at": None,
        }

    def _ensure_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all required keys exist in progress data."""
        default = self._get_default_structure()
        for key, value in default.items():
            if key not in data:
                data[key] = value
        return data

    def _save_progress(self):
        """Save progress data to file."""
        self.progress_data["last_updated"] = datetime.now().isoformat()
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving progress file: {e}")

    # ========== Data Indexing ==========

    def is_data_indexed(self) -> bool:
        """Check if data has been indexed."""
        return self.progress_data.get("data_indexed", False)

    def mark_data_indexed(self):
        """Mark data as indexed."""
        self.progress_data["data_indexed"] = True
        self.progress_data["data_indexed_at"] = datetime.now().isoformat()
        self._save_progress()

    def mark_data_not_indexed(self):
        """Mark data as not indexed."""
        self.progress_data["data_indexed"] = False
        self.progress_data["data_indexed_at"] = None
        self._save_progress()

    # ========== Query Validation ==========

    def get_validated_queries(self) -> List[str]:
        """Get list of validated query IDs from validated_queries.json."""
        if not self.validated_queries_file.exists():
            return []

        try:
            with open(self.validated_queries_file, 'r') as f:
                data = json.load(f)
                return data.get('validated_queries', [])
        except Exception as e:
            logger.warning(f"Error reading validated queries: {e}")
            return []

    def get_query_validation_count(self, total_queries: int) -> Tuple[int, int]:
        """
        Get query validation progress.

        Args:
            total_queries: Total number of queries in the module

        Returns:
            Tuple of (validated_count, total_count)
        """
        validated = len(self.get_validated_queries())
        return (validated, total_queries)

    # ========== Tool Deployment ==========

    def get_deployed_tools(self) -> List[str]:
        """Get list of deployed tool IDs from tool_metadata.json."""
        if not self.tool_metadata_file.exists():
            return []

        try:
            with open(self.tool_metadata_file, 'r') as f:
                data = json.load(f)
                deployed = []
                for tool_id, metadata in data.items():
                    if metadata.get('deployed', False):
                        deployed.append(tool_id)
                return deployed
        except Exception as e:
            logger.warning(f"Error reading tool metadata: {e}")
            return []

    def get_tool_deployment_count(self, total_tools: int) -> Tuple[int, int]:
        """
        Get tool deployment progress.

        Args:
            total_tools: Total number of tools in the module

        Returns:
            Tuple of (deployed_count, total_count)
        """
        deployed = len(self.get_deployed_tools())
        return (deployed, total_tools)

    # ========== Agent Deployment ==========

    def is_agent_deployed(self) -> bool:
        """Check if agent has been deployed."""
        return self.progress_data.get("agent_deployed", False)

    def mark_agent_deployed(self):
        """Mark agent as deployed."""
        self.progress_data["agent_deployed"] = True
        self.progress_data["agent_deployed_at"] = datetime.now().isoformat()
        self._save_progress()

    def mark_agent_not_deployed(self):
        """Mark agent as not deployed."""
        self.progress_data["agent_deployed"] = False
        self.progress_data["agent_deployed_at"] = None
        self._save_progress()

    # ========== Overall Progress ==========

    def calculate_progress(
        self,
        total_queries: int = 0,
        total_tools: int = 0
    ) -> Dict[str, Any]:
        """
        Calculate overall progress across all categories.

        Args:
            total_queries: Total number of queries in module
            total_tools: Total number of tools in module

        Returns:
            Dictionary with progress breakdown and overall percentage
        """
        # Data indexing (1 item)
        data_done = 1 if self.is_data_indexed() else 0
        data_total = 1

        # Query validation
        validated_queries = self.get_validated_queries()
        queries_validated = len(validated_queries)
        # Use the higher of passed total or actual validated count
        queries_total = max(total_queries, queries_validated) if total_queries > 0 else queries_validated

        # Tool deployment
        deployed_tools = self.get_deployed_tools()
        tools_deployed = len(deployed_tools)
        # Use the higher of passed total or actual deployed count
        tools_total = max(total_tools, tools_deployed) if total_tools > 0 else tools_deployed

        # Agent deployment (1 item)
        agent_done = 1 if self.is_agent_deployed() else 0
        agent_total = 1

        # Calculate totals - only count categories that have items
        total_done = data_done + agent_done
        total_items = data_total + agent_total

        # Add queries if there are any
        if queries_total > 0:
            total_done += min(queries_validated, queries_total)  # Cap at total
            total_items += queries_total

        # Add tools if there are any
        if tools_total > 0:
            total_done += min(tools_deployed, tools_total)  # Cap at total
            total_items += tools_total

        # Calculate percentage (avoid division by zero, cap at 100%)
        percentage = min((total_done / total_items * 100), 100) if total_items > 0 else 0

        return {
            "percentage": round(percentage),
            "data": {
                "done": data_done == 1,
                "indexed_at": self.progress_data.get("data_indexed_at"),
            },
            "queries": {
                "validated": queries_validated,
                "total": queries_total,
            },
            "tools": {
                "deployed": tools_deployed,
                "total": tools_total,
            },
            "agent": {
                "done": agent_done == 1,
                "deployed_at": self.progress_data.get("agent_deployed_at"),
            },
            "total_done": total_done,
            "total_items": total_items,
        }

    # ========== Reset ==========

    def reset_progress(self):
        """
        Reset all progress tracking for this module.

        This clears:
        - progress.json (data_indexed, agent_deployed)
        - validated_queries.json (query validations)
        - Deployment markers in tool_metadata.json

        Does NOT delete indexed data from ES or un-deploy from Agent Builder.
        """
        # Reset progress.json
        self.progress_data = self._get_default_structure()
        self._save_progress()

        # Clear validated_queries.json
        if self.validated_queries_file.exists():
            try:
                with open(self.validated_queries_file, 'w') as f:
                    json.dump({
                        "validated_queries": [],
                        "last_updated": datetime.now().isoformat(),
                        "reset_at": datetime.now().isoformat()
                    }, f, indent=2)
            except Exception as e:
                logger.error(f"Error clearing validated queries: {e}")

        # Clear deployment markers in tool_metadata.json (keep other metadata)
        if self.tool_metadata_file.exists():
            try:
                with open(self.tool_metadata_file, 'r') as f:
                    data = json.load(f)

                for tool_id in data:
                    if isinstance(data[tool_id], dict):
                        data[tool_id]['deployed'] = False
                        data[tool_id]['deployed_at'] = None
                        data[tool_id]['deployed_tool_id'] = None

                data['_reset_at'] = datetime.now().isoformat()

                with open(self.tool_metadata_file, 'w') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                logger.error(f"Error clearing tool metadata: {e}")

        logger.info(f"Progress reset for module: {self.module_path}")

    # ========== Auto-Sync with External Services ==========

    def auto_sync_progress(self, dataset_names: List[str] = None, timeout_seconds: float = 3.0) -> bool:
        """
        Auto-detect and sync progress from external services (ES indices, Agent Builder).

        This is called on module load to detect if data was indexed or agents deployed
        before progress tracking was implemented.

        Uses cooldown to prevent repeated API calls.

        Args:
            dataset_names: List of dataset names to check for indices
            timeout_seconds: Max time to wait for each API call

        Returns:
            True if any progress was updated, False otherwise
        """
        import time
        global _auto_sync_cache

        module_key = str(self.module_path)
        now = time.time()

        # Check cooldown
        if module_key in _auto_sync_cache:
            elapsed = now - _auto_sync_cache[module_key]
            if elapsed < AUTO_SYNC_COOLDOWN_SECONDS:
                logger.debug(f"Auto-sync skipped (cooldown): {module_key}")
                return False

        updated = False

        # Only sync if not already marked as done
        if not self.is_data_indexed() and dataset_names:
            try:
                data_indexed = self._check_indices_exist(dataset_names, timeout_seconds)
                if data_indexed:
                    self.mark_data_indexed()
                    updated = True
                    logger.info(f"Auto-synced data_indexed=True for {module_key}")
            except Exception as e:
                logger.warning(f"Auto-sync data check failed: {e}")

        if not self.is_agent_deployed():
            try:
                agent_deployed = self._check_agent_deployed(timeout_seconds)
                if agent_deployed:
                    self.mark_agent_deployed()
                    updated = True
                    logger.info(f"Auto-synced agent_deployed=True for {module_key}")
            except Exception as e:
                logger.warning(f"Auto-sync agent check failed: {e}")

        # Update cooldown timestamp
        _auto_sync_cache[module_key] = now

        return updated

    def _check_indices_exist(self, dataset_names: List[str], timeout_seconds: float) -> bool:
        """
        Check if at least one dataset index exists in Elasticsearch.

        Uses the existing ElasticsearchIndexer which properly handles env loading.
        Returns True if ANY index exists (partial indexing still counts as data indexed).
        """
        try:
            from src.services.elasticsearch_indexer import ElasticsearchIndexer

            # ElasticsearchIndexer handles dotenv loading and ES client creation
            indexer = ElasticsearchIndexer()

            if not indexer.client:
                logger.debug("No ES connection available, skipping index check")
                return False

            # Check if ANY of the dataset indices exist (first match wins)
            for name in dataset_names[:3]:  # Only check first 3 to keep it fast
                try:
                    if indexer.client.indices.exists(index=name):
                        logger.debug(f"Found index: {name}")
                        return True
                except Exception:
                    continue

            return False

        except ImportError:
            logger.debug("ElasticsearchIndexer not available")
            return False
        except ValueError as e:
            # Missing credentials - this is expected if ES not configured
            logger.debug(f"ES not configured: {e}")
            return False
        except Exception as e:
            logger.warning(f"Index check error: {e}")
            return False

    def _check_agent_deployed(self, timeout_seconds: float) -> bool:
        """
        Check if agent is deployed by verifying with Agent Builder API.

        API is the source of truth - users may have deleted resources manually
        even if local metadata says "deployed". Always check API when credentials
        are available.
        """
        agent_metadata_file = self.module_path / "agent_metadata.json"

        if not agent_metadata_file.exists():
            return False

        try:
            with open(agent_metadata_file, 'r') as f:
                data = json.load(f)

            agent_id = data.get('id', '')
            if not agent_id:
                return False

            # Always check API - it's the source of truth
            try:
                from dotenv import load_dotenv
                import os
                load_dotenv()

                kibana_url = os.getenv('ELASTICSEARCH_KIBANA_URL') or os.getenv('KIBANA_URL')
                api_key = os.getenv('ELASTICSEARCH_API_KEY') or os.getenv('ELASTIC_API_KEY')

                if kibana_url and api_key:
                    from src.services.elastic_agent_builder_client import ElasticAgentBuilderClient
                    client = ElasticAgentBuilderClient(kibana_url, api_key)

                    # Try to get the agent - if it exists, it's deployed
                    agent = client.get_agent(agent_id)
                    if agent:
                        logger.debug(f"Found agent in Agent Builder: {agent_id}")
                        return True
                    else:
                        # Agent not found in API - it's not deployed
                        # (even if local metadata says it is)
                        logger.debug(f"Agent not found in Agent Builder: {agent_id}")
                        return False
                else:
                    # No API credentials - fall back to local metadata
                    if data.get('deployed', False) or data.get('deployed_at'):
                        return True
                    return False
            except Exception as e:
                # API error - fall back to local metadata
                logger.debug(f"Agent API check failed, using local metadata: {e}")
                if data.get('deployed', False) or data.get('deployed_at'):
                    return True
                return False

        except Exception as e:
            logger.debug(f"Agent metadata check error: {e}")
            return False


# Cache for service instances
_service_cache: Dict[str, ProgressTrackingService] = {}


def get_progress_service(module_name: str) -> ProgressTrackingService:
    """
    Get or create a progress tracking service for a module.

    Args:
        module_name: Name of the demo module

    Returns:
        ProgressTrackingService instance
    """
    if module_name not in _service_cache:
        module_path = Path("demos") / module_name
        _service_cache[module_name] = ProgressTrackingService(str(module_path))

    return _service_cache[module_name]


def clear_service_cache():
    """Clear the service cache (useful for testing)."""
    global _service_cache
    _service_cache = {}
