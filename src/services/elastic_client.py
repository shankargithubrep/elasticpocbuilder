"""
Elasticsearch Client Wrapper
Basic operations for demo data management
"""

import logging
from typing import Dict, List, Optional
from elasticsearch import Elasticsearch
import pandas as pd
import os

logger = logging.getLogger(__name__)


class ElasticClient:
    """Wrapper for Elasticsearch operations"""

    def __init__(self, host: str = None, api_key: str = None, cloud_id: str = None):
        """
        Initialize Elasticsearch client

        Args:
            host: Elasticsearch host URL
            api_key: API key for authentication
            cloud_id: Elastic Cloud ID (alternative to host)
        """
        # Get from environment if not provided
        host = host or os.environ.get("ELASTICSEARCH_HOST", "localhost:9200")
        api_key = api_key or os.environ.get("ELASTICSEARCH_API_KEY")
        cloud_id = cloud_id or os.environ.get("ELASTICSEARCH_CLOUD_ID")

        try:
            if cloud_id and api_key:
                self.client = Elasticsearch(
                    cloud_id=cloud_id,
                    api_key=api_key
                )
            elif api_key:
                self.client = Elasticsearch(
                    hosts=[host],
                    api_key=api_key
                )
            else:
                # Local development without auth
                self.client = Elasticsearch(hosts=[host])

            # Test connection
            if self.client.ping():
                logger.info("Successfully connected to Elasticsearch")
            else:
                logger.warning("Elasticsearch connection could not be verified")

        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {e}")
            # Create a dummy client for testing without Elasticsearch
            self.client = None

    def create_index(self, index_name: str, mappings: Dict = None, settings: Dict = None) -> bool:
        """
        Create an Elasticsearch index

        Args:
            index_name: Name of the index
            mappings: Index mappings
            settings: Index settings

        Returns:
            True if successful
        """
        if not self.client:
            logger.warning(f"No Elasticsearch connection - skipping index creation for {index_name}")
            return False

        try:
            body = {}
            if settings:
                body["settings"] = settings
            if mappings:
                body["mappings"] = mappings

            self.client.indices.create(index=index_name, body=body if body else None)
            logger.info(f"Created index: {index_name}")
            return True

        except Exception as e:
            if "resource_already_exists_exception" in str(e):
                logger.info(f"Index {index_name} already exists")
                return True
            else:
                logger.error(f"Failed to create index {index_name}: {e}")
                return False

    def delete_index(self, index_name: str) -> bool:
        """Delete an index if it exists"""
        if not self.client:
            return False

        try:
            if self.client.indices.exists(index=index_name):
                self.client.indices.delete(index=index_name)
                logger.info(f"Deleted index: {index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {e}")
            return False

    def index_dataframe(self, df: pd.DataFrame, index_name: str, id_field: str = None) -> bool:
        """
        Index a pandas DataFrame to Elasticsearch

        Args:
            df: DataFrame to index
            index_name: Target index name
            id_field: Field to use as document ID

        Returns:
            True if successful
        """
        if not self.client:
            logger.warning(f"No Elasticsearch connection - skipping data indexing for {index_name}")
            return False

        try:
            # Convert DataFrame to records
            records = df.to_dict("records")

            # Bulk index
            actions = []
            for i, record in enumerate(records):
                action = {
                    "_index": index_name,
                    "_source": record
                }
                if id_field and id_field in record:
                    action["_id"] = record[id_field]
                else:
                    action["_id"] = str(i)

                actions.append({"index": action})
                actions.append(record)

            # Use bulk API
            from elasticsearch.helpers import bulk
            success, failed = bulk(self.client, actions, raise_on_error=False)

            logger.info(f"Indexed {success} documents to {index_name}")
            if failed:
                logger.warning(f"Failed to index {len(failed)} documents")

            return True

        except Exception as e:
            logger.error(f"Failed to index data to {index_name}: {e}")
            return False

    def execute_esql(self, query: str) -> Optional[Dict]:
        """
        Execute an ES|QL query

        Args:
            query: ES|QL query string

        Returns:
            Query results or None if failed
        """
        if not self.client:
            logger.warning("No Elasticsearch connection - cannot execute ES|QL query")
            return None

        try:
            # ES|QL endpoint (adjust based on your Elasticsearch version)
            response = self.client.perform_request(
                "POST",
                "/_query",
                body={"query": query}
            )
            return response

        except Exception as e:
            logger.error(f"Failed to execute ES|QL query: {e}")
            return None

    def search(self, index: str, query: Dict = None, size: int = 10) -> Optional[Dict]:
        """
        Perform a search query

        Args:
            index: Index to search
            query: Query DSL
            size: Number of results

        Returns:
            Search results or None if failed
        """
        if not self.client:
            return None

        try:
            body = {"size": size}
            if query:
                body["query"] = query

            response = self.client.search(index=index, body=body)
            return response

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return None

    def get_index_info(self, index_name: str) -> Optional[Dict]:
        """Get information about an index"""
        if not self.client:
            return None

        try:
            return self.client.indices.get(index=index_name)
        except Exception as e:
            logger.error(f"Failed to get index info: {e}")
            return None

    def health_check(self) -> bool:
        """Check if Elasticsearch is accessible"""
        if not self.client:
            return False

        try:
            return self.client.ping()
        except Exception:
            return False