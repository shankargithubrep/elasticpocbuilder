"""
Sample Values Extractor
Extracts real values from indexed Elasticsearch data for use in query testing
"""

from typing import Dict, List, Any, Optional
import logging
import json
from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)


class SampleValuesExtractor:
    """Extracts sample values from indexed data for query testing"""

    def __init__(self, es_client: Elasticsearch):
        """Initialize with Elasticsearch client

        Args:
            es_client: Elasticsearch client instance
        """
        self.client = es_client

    def extract_sample_values(
        self,
        indexed_datasets: Dict[str, str],
        fields_of_interest: Optional[Dict[str, List[str]]] = None,
        sample_size: int = 5
    ) -> Dict[str, Dict[str, List[Any]]]:
        """Extract sample values from indexed datasets

        Args:
            indexed_datasets: Dict mapping dataset names to index names
            fields_of_interest: Optional dict mapping dataset -> [field_names] to extract
            sample_size: Number of sample values to extract per field

        Returns:
            Dict mapping dataset -> field -> [sample_values]
        """
        logger.info(f"Extracting sample values from {len(indexed_datasets)} datasets")

        sample_values = {}

        for dataset_name, index_name in indexed_datasets.items():
            logger.info(f"Extracting samples from {dataset_name} ({index_name})")

            try:
                # Get a sample document to understand field structure
                sample_query = {
                    "size": sample_size,
                    "query": {"match_all": {}},
                    "_source": True
                }

                response = self.client.search(index=index_name, body=sample_query)

                if not response['hits']['hits']:
                    logger.warning(f"No documents found in {index_name}")
                    continue

                # Extract field values from sample documents
                dataset_samples = {}

                for hit in response['hits']['hits']:
                    doc = hit['_source']

                    # If specific fields requested, only extract those
                    if fields_of_interest and dataset_name in fields_of_interest:
                        target_fields = fields_of_interest[dataset_name]
                    else:
                        # Extract all fields from document
                        target_fields = doc.keys()

                    for field_name in target_fields:
                        if field_name in doc:
                            value = doc[field_name]

                            # Initialize field list if needed
                            if field_name not in dataset_samples:
                                dataset_samples[field_name] = []

                            # Add unique values only
                            if value not in dataset_samples[field_name]:
                                dataset_samples[field_name].append(value)

                sample_values[dataset_name] = dataset_samples
                logger.info(f"Extracted {len(dataset_samples)} fields from {dataset_name}")

            except Exception as e:
                logger.error(f"Failed to extract samples from {index_name}: {e}", exc_info=True)
                continue

        return sample_values

    def get_value_for_field(
        self,
        index_name: str,
        field_name: str,
        field_type: str = "keyword"
    ) -> Optional[Any]:
        """Get a single sample value for a specific field

        Args:
            index_name: Elasticsearch index name
            field_name: Field to get value for
            field_type: Field data type (keyword, text, etc.)

        Returns:
            Sample value or None if not found
        """
        try:
            # Query for a document with this field populated
            query = {
                "size": 1,
                "query": {
                    "exists": {
                        "field": field_name
                    }
                },
                "_source": [field_name]
            }

            response = self.client.search(index=index_name, body=query)

            if response['hits']['hits']:
                doc = response['hits']['hits'][0]['_source']
                return doc.get(field_name)

            return None

        except Exception as e:
            logger.error(f"Failed to get value for {field_name} in {index_name}: {e}")
            return None

    def save_sample_values(self, sample_values: Dict, output_path: str):
        """Save sample values to JSON file

        Args:
            sample_values: Extracted sample values
            output_path: Path to save JSON file
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(sample_values, f, indent=2, default=str)
            logger.info(f"Saved sample values to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save sample values: {e}", exc_info=True)

    def load_sample_values(self, input_path: str) -> Dict:
        """Load sample values from JSON file

        Args:
            input_path: Path to JSON file

        Returns:
            Sample values dictionary
        """
        try:
            with open(input_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load sample values: {e}", exc_info=True)
            return {}
