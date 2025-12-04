"""
Service for managing query validation and tool metadata for Elastic Agent Builder integration.

This service handles:
- Tracking validated queries
- Storing tool metadata for deployment
- Managing deployment status
"""

import json
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime


class QueryValidationService:
    """Service for managing query validation and tool metadata."""

    def __init__(self, module_path: str):
        """
        Initialize the validation service for a specific demo module.

        Args:
            module_path: Path to the demo module directory
        """
        self.module_path = Path(module_path)
        self.validated_queries_file = self.module_path / "validated_queries.json"
        self.tool_metadata_file = self.module_path / "tool_metadata.json"

        # Ensure module directory exists
        self.module_path.mkdir(parents=True, exist_ok=True)

        # Load existing data
        self.validated_queries = self._load_validated_queries()
        self.tool_metadata = self._load_tool_metadata()

    def _load_validated_queries(self) -> Set[str]:
        """Load the set of validated query IDs."""
        if self.validated_queries_file.exists():
            try:
                with open(self.validated_queries_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('validated_queries', []))
            except Exception:
                return set()
        return set()

    def _save_validated_queries(self):
        """Save the set of validated query IDs."""
        data = {
            'validated_queries': list(self.validated_queries),
            'last_updated': datetime.now().isoformat()
        }
        with open(self.validated_queries_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_tool_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load tool metadata for queries."""
        if self.tool_metadata_file.exists():
            try:
                with open(self.tool_metadata_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_tool_metadata(self):
        """Save tool metadata."""
        with open(self.tool_metadata_file, 'w') as f:
            json.dump(self.tool_metadata, f, indent=2)

    def is_query_validated(self, query_id: str) -> bool:
        """
        Check if a query is validated.

        Args:
            query_id: The unique identifier for the query

        Returns:
            True if the query is validated, False otherwise
        """
        return query_id in self.validated_queries

    def toggle_query_validation(self, query_id: str) -> bool:
        """
        Toggle the validation status of a query.

        Args:
            query_id: The unique identifier for the query

        Returns:
            The new validation status (True if now validated, False if not)
        """
        if query_id in self.validated_queries:
            self.validated_queries.remove(query_id)
            is_validated = False
        else:
            self.validated_queries.add(query_id)
            is_validated = True

        self._save_validated_queries()
        return is_validated

    def mark_query_validated(self, query_id: str):
        """
        Mark a query as validated.

        Args:
            query_id: The unique identifier for the query
        """
        self.validated_queries.add(query_id)
        self._save_validated_queries()

    def mark_query_unvalidated(self, query_id: str):
        """
        Mark a query as not validated.

        Args:
            query_id: The unique identifier for the query
        """
        self.validated_queries.discard(query_id)
        self._save_validated_queries()

        # Also remove tool metadata if it exists
        if query_id in self.tool_metadata:
            del self.tool_metadata[query_id]
            self._save_tool_metadata()

    def get_validated_queries(self) -> List[str]:
        """
        Get the list of all validated query IDs.

        Returns:
            List of validated query IDs
        """
        return list(self.validated_queries)

    def get_tool_metadata(self, query_id: str) -> Dict[str, Any]:
        """
        Get tool metadata for a specific query.

        Args:
            query_id: The unique identifier for the query

        Returns:
            Tool metadata dictionary or empty dict if not found
        """
        return self.tool_metadata.get(query_id, {})

    def save_tool_metadata(self, query_id: str, metadata: Dict[str, Any]):
        """
        Save tool metadata for a query.

        Args:
            query_id: The unique identifier for the query
            metadata: The tool metadata to save
        """
        self.tool_metadata[query_id] = {
            **metadata,
            'last_updated': datetime.now().isoformat()
        }
        self._save_tool_metadata()

    def is_tool_ready_for_deployment(self, query_id: str) -> bool:
        """
        Check if a query has all required metadata for tool deployment.

        Args:
            query_id: The unique identifier for the query

        Returns:
            True if the query is ready for deployment, False otherwise
        """
        if query_id not in self.validated_queries:
            return False

        metadata = self.tool_metadata.get(query_id, {})

        # Check required fields for ES|QL tools
        required_fields = ['tool_id', 'description']
        return all(field in metadata and metadata[field] for field in required_fields)

    def mark_tool_deployed(self, query_id: str, tool_id: str):
        """
        Mark a tool as deployed to Agent Builder.

        Args:
            query_id: The unique identifier for the query
            tool_id: The ID of the deployed tool in Agent Builder
        """
        if query_id in self.tool_metadata:
            self.tool_metadata[query_id]['deployed'] = True
            self.tool_metadata[query_id]['deployed_tool_id'] = tool_id
            self.tool_metadata[query_id]['deployed_at'] = datetime.now().isoformat()
            self._save_tool_metadata()

    def is_tool_deployed(self, query_id: str) -> bool:
        """
        Check if a tool has been deployed to Agent Builder.

        Args:
            query_id: The unique identifier for the query

        Returns:
            True if the tool is deployed, False otherwise
        """
        metadata = self.tool_metadata.get(query_id, {})
        return metadata.get('deployed', False)

    def get_deployed_tool_id(self, query_id: str) -> Optional[str]:
        """
        Get the Agent Builder tool ID for a deployed query.

        Args:
            query_id: The unique identifier for the query

        Returns:
            The Agent Builder tool ID or None if not deployed
        """
        metadata = self.tool_metadata.get(query_id, {})
        return metadata.get('deployed_tool_id')

    def get_deployment_candidates(self) -> List[Dict[str, Any]]:
        """
        Get list of validated queries that are ready for deployment but not yet deployed.

        Returns:
            List of query metadata for deployment candidates
        """
        candidates = []
        for query_id in self.validated_queries:
            if not self.is_tool_deployed(query_id):
                metadata = self.tool_metadata.get(query_id, {})
                candidates.append({
                    'query_id': query_id,
                    'metadata': metadata,
                    'is_ready': self.is_tool_ready_for_deployment(query_id)
                })
        return candidates

    def get_deployed_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of deployed tools.

        Returns:
            List of deployed tool metadata
        """
        deployed = []
        for query_id, metadata in self.tool_metadata.items():
            if metadata.get('deployed', False):
                deployed.append({
                    'query_id': query_id,
                    'tool_id': metadata.get('deployed_tool_id'),
                    'name': metadata.get('name'),
                    'deployed_at': metadata.get('deployed_at'),
                    'metadata': metadata
                })
        return deployed

    def compute_query_hash(self, query_text: str) -> str:
        """
        Compute SHA256 hash of a query text for change detection.

        Args:
            query_text: The ES|QL query text

        Returns:
            SHA256 hash of the query
        """
        return hashlib.sha256(query_text.encode('utf-8')).hexdigest()

    def store_query_hash(self, query_id: str, query_text: str):
        """
        Store the hash of a validated query for future comparison.

        Args:
            query_id: The unique identifier for the query
            query_text: The ES|QL query text
        """
        if query_id not in self.tool_metadata:
            self.tool_metadata[query_id] = {}

        query_hash = self.compute_query_hash(query_text)
        self.tool_metadata[query_id]['query_hash'] = query_hash
        self.tool_metadata[query_id]['hash_stored_at'] = datetime.now().isoformat()
        self._save_tool_metadata()

    def is_query_changed(self, query_id: str, current_query_text: str) -> bool:
        """
        Check if a query has changed since it was validated/deployed.

        Args:
            query_id: The unique identifier for the query
            current_query_text: The current ES|QL query text

        Returns:
            True if the query has changed, False otherwise
        """
        metadata = self.tool_metadata.get(query_id, {})
        stored_hash = metadata.get('query_hash')

        if not stored_hash:
            # No hash stored, consider it changed (needs initial validation)
            return True

        current_hash = self.compute_query_hash(current_query_text)
        return current_hash != stored_hash

    def get_query_sync_status(self, query_id: str, current_query_text: str) -> Dict[str, Any]:
        """
        Get detailed synchronization status for a query.

        Args:
            query_id: The unique identifier for the query
            current_query_text: The current ES|QL query text

        Returns:
            Dictionary with sync status information
        """
        metadata = self.tool_metadata.get(query_id, {})
        is_changed = self.is_query_changed(query_id, current_query_text)
        is_deployed = self.is_tool_deployed(query_id)

        return {
            'query_id': query_id,
            'is_validated': query_id in self.validated_queries,
            'is_deployed': is_deployed,
            'is_changed': is_changed,
            'needs_revalidation': is_changed and query_id in self.validated_queries,
            'needs_redeployment': is_changed and is_deployed,
            'deployed_tool_id': metadata.get('deployed_tool_id'),
            'last_hash_update': metadata.get('hash_stored_at'),
            'deployed_at': metadata.get('deployed_at')
        }

    def mark_query_validated_with_hash(self, query_id: str, query_text: str):
        """
        Mark a query as validated and store its hash.

        Args:
            query_id: The unique identifier for the query
            query_text: The ES|QL query text that was validated
        """
        self.mark_query_validated(query_id)
        self.store_query_hash(query_id, query_text)

    def get_query_versions(self, query_id: str) -> Dict[str, Any]:
        """
        Get information about deployed vs current versions of a query.

        Args:
            query_id: The unique identifier for the query

        Returns:
            Dictionary with version information
        """
        metadata = self.tool_metadata.get(query_id, {})
        return {
            'query_id': query_id,
            'has_deployed_version': self.is_tool_deployed(query_id),
            'deployed_query': metadata.get('deployed_query_text'),
            'deployed_hash': metadata.get('query_hash'),
            'deployed_at': metadata.get('deployed_at'),
            'current_query': metadata.get('current_query'),
            'query_modified': metadata.get('query_modified', False),
            'modified_at': metadata.get('modified_at')
        }