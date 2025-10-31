"""
Elasticsearch Indexer Service
Handles indexing of demo datasets into Elasticsearch with support for:
- Data streams (timeseries data)
- Lookup indices (dimension tables)
- Semantic text fields with ELSER
- ELSER pre-flight checks and deployment
"""

import os
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
from elasticsearch import Elasticsearch, helpers
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class IndexingResult:
    """Result of indexing operation"""
    success: bool
    index_name: str
    index_type: str  # "data_stream" or "lookup"
    documents_indexed: int
    semantic_fields: List[str]
    duration_seconds: float
    errors: List[str]


class FieldMapper:
    """Automatic field type detection and mapping generation"""

    @staticmethod
    def analyze_dataframe(df: pd.DataFrame, semantic_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze DataFrame and generate Elasticsearch mappings

        Args:
            df: pandas DataFrame to analyze
            semantic_fields: Optional list of fields to map as semantic_text

        Returns:
            Dictionary with:
            - mappings: ES mapping configuration
            - is_timeseries: boolean
            - semantic_fields: list of semantic text fields
        """
        mappings = {"properties": {}}
        detected_semantic_fields = []

        # Override semantic fields if provided
        semantic_field_set = set(semantic_fields or [])

        for col in df.columns:
            # Skip @timestamp as it's added automatically
            if col == "@timestamp":
                continue

            # Map timestamp columns to @timestamp
            if col in ["timestamp", "time", "date"] and pd.api.types.is_datetime64_any_dtype(df[col]):
                mappings["properties"]["@timestamp"] = {"type": "date"}
                continue

            # Check if explicitly marked as semantic
            if col in semantic_field_set:
                # On EIS, semantic_text automatically uses built-in ELSER
                # No inference_id needed
                mappings["properties"][col] = {
                    "type": "semantic_text"
                }
                detected_semantic_fields.append(col)
                continue

            # Auto-detect semantic text (text fields with avg length > 50)
            if pd.api.types.is_string_dtype(df[col]):
                avg_length = df[col].astype(str).str.len().mean()
                if avg_length > 50 and col not in semantic_field_set:
                    # Long text might be semantic
                    mappings["properties"][col] = {
                        "type": "semantic_text",
                        "inference_id": ".elser-2-elasticsearch"
                    }
                    detected_semantic_fields.append(col)
                else:
                    # Short text is keyword
                    mappings["properties"][col] = {"type": "keyword"}
            else:
                # Map other types
                mappings["properties"][col] = FieldMapper._map_column(df[col])

        is_timeseries = FieldMapper.is_timeseries(df)

        return {
            "mappings": mappings,
            "is_timeseries": is_timeseries,
            "semantic_fields": detected_semantic_fields
        }

    @staticmethod
    def is_timeseries(df: pd.DataFrame) -> bool:
        """Detect if DataFrame is timeseries data"""
        # Check for timestamp columns
        timestamp_cols = ["@timestamp", "timestamp", "time", "date"]
        for col in timestamp_cols:
            if col in df.columns:
                return True

        # Check for datetime columns
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                return True

        return False

    @staticmethod
    def _map_column(series: pd.Series) -> Dict[str, str]:
        """Map pandas dtype to Elasticsearch field type"""
        dtype = series.dtype

        if pd.api.types.is_integer_dtype(dtype):
            return {"type": "long"}
        elif pd.api.types.is_float_dtype(dtype):
            return {"type": "double"}
        elif pd.api.types.is_bool_dtype(dtype):
            return {"type": "boolean"}
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return {"type": "date"}
        elif pd.api.types.is_string_dtype(dtype):
            # Check cardinality for keyword vs text
            cardinality = series.nunique()
            total = len(series)
            if cardinality / total < 0.5:  # Low cardinality
                return {"type": "keyword"}
            else:
                return {"type": "text"}
        else:
            return {"type": "keyword"}  # Default


class ElasticsearchIndexer:
    """Main indexing service"""

    def __init__(self):
        """Initialize Elasticsearch client from environment variables"""
        self.client = self._create_client()

    def _create_client(self) -> Elasticsearch:
        """Create Elasticsearch client from .env credentials"""
        # Try multiple naming conventions
        cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID") or os.getenv("ELASTIC_CLOUD_ID")
        api_key = os.getenv("ELASTICSEARCH_API_KEY") or os.getenv("ELASTIC_API_KEY")
        endpoint = os.getenv("ELASTIC_ENDPOINT") or os.getenv("ELASTIC_CLOUD_ENDPOINT")

        if cloud_id and api_key:
            # Use cloud_id
            return Elasticsearch(
                cloud_id=cloud_id,
                api_key=api_key,
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
        elif endpoint and api_key:
            # Use direct endpoint
            return Elasticsearch(
                hosts=[endpoint],
                api_key=api_key,
                request_timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
        else:
            raise ValueError(
                "Missing Elasticsearch credentials in .env\n"
                "Required: ELASTICSEARCH_CLOUD_ID + ELASTICSEARCH_API_KEY\n"
                "OR: ELASTIC_ENDPOINT + ELASTIC_API_KEY"
            )

    def verify_connection(self) -> Tuple[bool, str]:
        """Test Elasticsearch connection"""
        try:
            info = self.client.info()
            cluster_name = info.get("cluster_name", "unknown")
            version = info.get("version", {}).get("number", "unknown")
            return True, f"Connected to {cluster_name} (version {version})"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def index_dataset(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        semantic_fields: Optional[List[str]] = None,
        index_mode: Optional[str] = None,
        progress_callback: Optional[callable] = None,
        stop_callback: Optional[callable] = None
    ) -> IndexingResult:
        """
        Index a dataset into Elasticsearch

        Args:
            df: pandas DataFrame to index
            dataset_name: name for the index/data stream
            semantic_fields: optional list of fields to use semantic_text
            index_mode: optional explicit index mode ('data_stream' or 'lookup')
                       If not provided, will auto-detect based on timestamp fields
            progress_callback: optional callback(progress, message)
            stop_callback: optional callback() that returns True to stop indexing

        Returns:
            IndexingResult with details
        """
        start_time = time.time()
        errors = []

        try:
            # Update progress
            if progress_callback:
                progress_callback(0.05, "Checking ELSER deployment...")

            # Analyze DataFrame with LLM-specified semantic fields
            mapping_info = FieldMapper.analyze_dataframe(df, semantic_fields)

            # Pre-flight check: Ensure ELSER is ready if semantic fields are used
            if mapping_info["semantic_fields"]:
                elser_ready, elser_msg = self.ensure_elser_ready(progress_callback)
                if not elser_ready:
                    raise ValueError(
                        f"Cannot index with semantic_text fields: {elser_msg}\n\n"
                        f"Semantic fields specified: {', '.join(mapping_info['semantic_fields'])}\n\n"
                        f"Please deploy ELSER through Kibana > Machine Learning > Trained Models, "
                        f"or remove semantic fields from your data generator."
                    )

            if progress_callback:
                progress_callback(0.1, "Analyzed dataset structure")

            # Determine index type: use explicit index_mode if provided, otherwise auto-detect
            if index_mode:
                # Use explicit mode from strategy
                use_data_stream = (index_mode == "data_stream")
                logger.info(f"Using explicit index_mode: {index_mode}")
            else:
                # Fall back to auto-detection based on timestamp fields
                use_data_stream = mapping_info["is_timeseries"]
                logger.info(f"Auto-detected index type: {'data_stream' if use_data_stream else 'lookup'}")

            # Create index or data stream
            if use_data_stream:
                index_name = self._create_data_stream(
                    dataset_name,
                    mapping_info["mappings"],
                    progress_callback
                )
                index_type = "data_stream"
            else:
                index_name = self._create_lookup_index(
                    dataset_name,
                    mapping_info["mappings"],
                    progress_callback
                )
                index_type = "lookup"

            if progress_callback:
                progress_callback(0.3, f"Created {index_type}: {index_name}")

            # Prepare documents
            documents = self._prepare_documents(df, mapping_info["is_timeseries"])

            if progress_callback:
                progress_callback(0.4, f"Prepared {len(documents)} documents")

            # Bulk index (with stop callback support)
            # Pass semantic fields info for proper batch sizing
            has_semantic_fields = bool(mapping_info["semantic_fields"])
            indexed_count = self._bulk_index(
                index_name,
                documents,
                index_type,
                has_semantic_fields,
                progress_callback,
                stop_callback
            )

            duration = time.time() - start_time

            # Check if we stopped early
            was_stopped = indexed_count < len(documents)

            return IndexingResult(
                success=True,
                index_name=index_name,
                index_type=index_type,
                documents_indexed=indexed_count,
                semantic_fields=mapping_info["semantic_fields"],
                duration_seconds=round(duration, 2),
                errors=errors if not was_stopped else errors + [f"Stopped early: {indexed_count}/{len(documents)} indexed"]
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Indexing failed: {e}", exc_info=True)
            errors.append(str(e))

            return IndexingResult(
                success=False,
                index_name=dataset_name,
                index_type="unknown",
                documents_indexed=0,
                semantic_fields=[],
                duration_seconds=round(duration, 2),
                errors=errors
            )

    def _create_data_stream(
        self,
        stream_name: str,
        mappings: Dict,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Create data stream with index template"""
        template_name = f"{stream_name}_template"

        # Delete existing template if exists
        try:
            self.client.indices.delete_index_template(name=template_name)
        except:
            pass

        # Create index template
        # Pattern must match the data stream name exactly
        # The backing indices will be named {stream_name}-*, but the template
        # pattern needs to match the data stream name itself
        self.client.indices.put_index_template(
            name=template_name,
            index_patterns=[stream_name],
            data_stream={},
            template={
                "mappings": mappings
            }
        )

        # Delete existing data stream if exists
        try:
            self.client.indices.delete_data_stream(name=stream_name)
        except:
            pass

        # Create data stream
        self.client.indices.create_data_stream(name=stream_name)

        return stream_name

    def _create_lookup_index(
        self,
        index_name: str,
        mappings: Dict,
        progress_callback: Optional[callable] = None
    ) -> str:
        """Create lookup index with index.mode: lookup"""
        full_name = f"{index_name}_lookup"

        # Delete existing index if exists
        try:
            self.client.indices.delete(index=full_name)
        except:
            pass

        # Create lookup index
        self.client.indices.create(
            index=full_name,
            settings={
                "index": {
                    "mode": "lookup"
                }
            },
            mappings=mappings
        )

        return full_name

    def _prepare_documents(self, df: pd.DataFrame, is_timeseries: bool) -> List[Dict]:
        """Convert DataFrame to Elasticsearch documents

        Note: When a field has both 'field' and 'field_semantic' versions,
        we only include the '_semantic' version since semantic_text fields
        store both the text and embeddings automatically.
        """
        documents = []

        # Identify fields that have semantic versions
        semantic_suffixed_fields = {col for col in df.columns if col.endswith('_semantic')}
        base_fields_to_skip = {col.replace('_semantic', '') for col in semantic_suffixed_fields}

        for _, row in df.iterrows():
            doc = {}

            for col, value in row.items():
                # Skip base field if semantic version exists
                # e.g., skip "exclusions" if "exclusions_semantic" exists
                if col in base_fields_to_skip and f"{col}_semantic" in df.columns:
                    continue

                # Handle timestamp mapping
                if col in ["timestamp", "time", "date"] and is_timeseries:
                    # Map to @timestamp
                    if pd.notna(value):
                        if isinstance(value, pd.Timestamp):
                            doc["@timestamp"] = value.isoformat()
                        else:
                            doc["@timestamp"] = pd.Timestamp(value).isoformat()
                elif col == "@timestamp":
                    if pd.notna(value):
                        if isinstance(value, pd.Timestamp):
                            doc["@timestamp"] = value.isoformat()
                        else:
                            doc["@timestamp"] = pd.Timestamp(value).isoformat()
                else:
                    # Handle NaN values
                    if pd.notna(value):
                        # Convert numpy types to Python types
                        if isinstance(value, (pd.Timestamp, datetime)):
                            doc[col] = value.isoformat()
                        elif hasattr(value, 'item'):  # numpy types
                            doc[col] = value.item()
                        else:
                            doc[col] = value

            documents.append(doc)

        return documents

    def _bulk_index(
        self,
        index_name: str,
        documents: List[Dict],
        index_type: str,
        has_semantic_fields: bool = False,
        progress_callback: Optional[callable] = None,
        stop_callback: Optional[callable] = None
    ) -> int:
        """
        Bulk index documents with progress tracking

        Args:
            index_name: Name of the index/data stream
            documents: List of documents to index
            index_type: Type of index ('data_stream' or 'lookup')
            has_semantic_fields: Whether the index has semantic_text fields (limits batch to 16)
            progress_callback: Optional callback(progress, message) for progress updates
            stop_callback: Optional callback() that returns True if indexing should stop

        Returns:
            Number of documents successfully indexed
        """
        # ELSER batch size limit: max 16 documents per batch when using semantic_text
        # https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/semantic-text#using-elser-on-eis
        batch_size = 16 if has_semantic_fields else 1000
        total_docs = len(documents)
        indexed_count = 0

        # Prepare bulk actions for helpers.bulk()
        # Format: each action is a dict with _index, _op_type, and document fields at top level
        actions = []
        for doc in documents:
            # Make a copy to avoid modifying original
            doc_copy = doc.copy()

            # Use create for data streams (append-only)
            op_type = "create" if index_type == "data_stream" else "index"

            # Data streams REQUIRE @timestamp field
            if index_type == "data_stream" and "@timestamp" not in doc_copy:
                # Try to find a timestamp field to use
                timestamp_value = None
                for key in ['timestamp', 'created_at', 'created_date', 'date', 'time']:
                    if key in doc_copy:
                        timestamp_value = doc_copy[key]
                        break

                # If no timestamp field found, use current time
                if timestamp_value is None:
                    from datetime import datetime
                    timestamp_value = datetime.utcnow().isoformat()

                doc_copy["@timestamp"] = timestamp_value

            # helpers.bulk() expects: {_op_type: op, _index: name, **document_fields}
            action = {
                "_op_type": op_type,
                "_index": index_name,
                **doc_copy  # Spread document fields at top level (not in _source)
            }

            actions.append(action)

        # Bulk index in batches
        for i in range(0, len(actions), batch_size):
            # Check if stop requested
            if stop_callback and stop_callback():
                if progress_callback:
                    progress_callback(
                        0.95,
                        f"⏸️ Stopped: {indexed_count}/{total_docs} documents indexed"
                    )
                return indexed_count

            batch = actions[i:i+batch_size]

            # Execute bulk with detailed error tracking
            try:
                # Use helpers.bulk for proper formatting, but capture details
                success_count, failed_items = helpers.bulk(
                    self.client,
                    batch,
                    raise_on_error=False,
                    stats_only=False  # Get failed items for error details
                )

                indexed_count += success_count
                failed_count = len(failed_items)

                # Log failures with sample errors
                if failed_count > 0:
                    error_samples = []
                    for item in failed_items[:3]:  # First 3 errors
                        # Extract error from failed item
                        error_info = item.get('index', item.get('create', {})).get('error', {})
                        if isinstance(error_info, dict):
                            error_type = error_info.get('type', 'unknown')
                            error_reason = error_info.get('reason', 'no reason')
                            error_samples.append(f"{error_type}: {error_reason}")
                        else:
                            error_samples.append(str(error_info))

                    error_sample = "; ".join(error_samples)
                    logger.error(f"Batch {i//batch_size + 1}: {success_count} succeeded, {failed_count} failed. Sample errors: {error_sample}")

            except Exception as e:
                logger.error(f"Bulk request failed: {e}")
                failed_count = len(batch)

            # Update progress
            if progress_callback:
                progress = 0.4 + (0.55 * (i + len(batch)) / total_docs)
                progress_callback(
                    progress,
                    f"Indexing: {indexed_count}/{total_docs} documents"
                )

        if progress_callback:
            progress_callback(0.95, "Indexing complete")

        return indexed_count

    def check_elser_deployment(self) -> Tuple[bool, str]:
        """Check if ELSER model is deployed and ready"""
        try:
            # Check inference endpoint
            try:
                response = self.client.inference.get(inference_id=".elser-2-elasticsearch")
            except Exception as e:
                if "resource_not_found_exception" in str(e).lower():
                    return False, "ELSER inference endpoint not found"
                raise

            # Check model deployment status
            try:
                model_stats = self.client.ml.get_trained_models_stats(model_id=".elser_model_2*")
            except Exception as e:
                return False, f"Cannot check ELSER model status: {str(e)}"

            # Check if any model is deployed and started
            for model in model_stats.get('trained_model_stats', []):
                deployment_stats = model.get('deployment_stats', {})
                state = deployment_stats.get('state', 'not_deployed')

                if state == 'started':
                    return True, "ELSER model is deployed and ready"
                elif state == 'starting':
                    return False, "ELSER model is starting, please wait..."
                elif state == 'downloading':
                    return False, "ELSER model is downloading, please wait..."

            return False, "ELSER model is not deployed"

        except Exception as e:
            logger.error(f"ELSER check failed: {e}", exc_info=True)
            return False, f"ELSER check error: {str(e)}"

    def deploy_elser(self) -> Tuple[bool, str]:
        """Deploy ELSER model if not already deployed"""
        try:
            # Check current status first
            is_ready, status_msg = self.check_elser_deployment()
            if is_ready:
                return True, status_msg

            # If downloading or starting, don't try to deploy again
            if "downloading" in status_msg.lower() or "starting" in status_msg.lower():
                return False, status_msg

            # Try to start deployment
            try:
                self.client.ml.start_trained_model_deployment(
                    model_id=".elser_model_2_linux-x86_64",
                    wait_for="starting"
                )
                return True, "ELSER deployment started"
            except Exception as e:
                if "resource_not_found_exception" in str(e).lower():
                    return False, (
                        "ELSER model not found. Please deploy ELSER through "
                        "Kibana > Machine Learning > Trained Models first."
                    )
                raise

        except Exception as e:
            logger.error(f"ELSER deployment failed: {e}", exc_info=True)
            return False, f"ELSER deployment error: {str(e)}"

    def ensure_elser_ready(self, progress_callback: Optional[callable] = None) -> Tuple[bool, str]:
        """
        Ensure ELSER is deployed and ready, wait if necessary

        Args:
            progress_callback: optional callback(progress, message)

        Returns:
            (is_ready, message) tuple
        """
        # Check if ready
        is_ready, msg = self.check_elser_deployment()
        if is_ready:
            return True, msg

        # If downloading or starting, wait up to 5 minutes
        if "downloading" in msg.lower() or "starting" in msg.lower():
            max_wait = 300  # 5 minutes
            wait_interval = 10  # Check every 10 seconds
            elapsed = 0

            while elapsed < max_wait:
                time.sleep(wait_interval)
                elapsed += wait_interval

                # Update progress
                if progress_callback:
                    progress = 0.05 + (0.05 * elapsed / max_wait)
                    progress_callback(progress, f"Waiting for ELSER ({elapsed}s)...")

                # Check status
                is_ready, msg = self.check_elser_deployment()
                if is_ready:
                    return True, msg

            # Timeout
            return False, "Timeout waiting for ELSER model to be ready"

        # Not deployed, try to deploy it
        if progress_callback:
            progress_callback(0.1, "Deploying ELSER model...")

        success, deploy_msg = self.deploy_elser()
        if not success:
            return False, deploy_msg

        # Wait for deployment to start
        max_wait = 60  # 1 minute
        wait_interval = 5
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(wait_interval)
            elapsed += wait_interval

            if progress_callback:
                progress = 0.1 + (0.05 * elapsed / max_wait)
                progress_callback(progress, f"Waiting for ELSER deployment ({elapsed}s)...")

            is_ready, msg = self.check_elser_deployment()
            if is_ready or "starting" in msg.lower():
                return True, "ELSER deployment in progress"

        return False, "Timeout waiting for ELSER deployment to start"

    def delete_index(self, index_name: str) -> Tuple[bool, str]:
        """Delete an index or data stream"""
        try:
            # Try as data stream first
            try:
                self.client.indices.delete_data_stream(name=index_name)
                return True, f"Deleted data stream: {index_name}"
            except:
                pass

            # Try as regular index
            self.client.indices.delete(index=index_name)
            return True, f"Deleted index: {index_name}"

        except Exception as e:
            return False, f"Delete failed: {str(e)}"

    def list_indices(self) -> List[Dict[str, Any]]:
        """List all indices and data streams"""
        try:
            indices = []

            # Get data streams
            try:
                streams = self.client.indices.get_data_stream(name="*")
                for stream in streams.get('data_streams', []):
                    indices.append({
                        'name': stream['name'],
                        'type': 'data_stream',
                        'docs_count': 'N/A'  # Would need to query backing indices
                    })
            except:
                pass

            # Get regular indices
            all_indices = self.client.cat.indices(format='json')
            for idx in all_indices:
                if not idx['index'].startswith('.'):  # Skip system indices
                    indices.append({
                        'name': idx['index'],
                        'type': 'index',
                        'docs_count': idx.get('docs.count', 0)
                    })

            return indices

        except Exception as e:
            logger.error(f"Failed to list indices: {e}", exc_info=True)
            return []

    def execute_esql(self, query: str) -> Tuple[bool, Any, str]:
        """
        Execute an ES|QL query

        Args:
            query: ES|QL query string

        Returns:
            Tuple of (success, result, error_message)
        """
        try:
            # Use the ES|QL API endpoint
            response = self.client.esql.query(query=query)
            return True, response, ""

        except Exception as e:
            error_msg = str(e)
            logger.error(f"ES|QL query failed: {error_msg}", exc_info=True)
            return False, None, error_msg
