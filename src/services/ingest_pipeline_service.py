"""
Ingest Pipeline Service

Creates Elasticsearch ingest pipelines with ML inference processors
for semantic search demos. Supports ELSER (sparse) and E5 multilingual (dense).
Also handles PII redaction processors.
"""

import logging
from typing import Dict, List, Any, Optional
from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)

ELSER_MODEL_ID = ".elser-2-elasticsearch"
E5_MODEL_ID = ".multilingual-e5-small"
E5_DIMS = 384  # multilingual-e5-small output dimensions
JINA_ENDPOINT_ID = "jina-embeddings-v3"
JINA_DIMS = 1024  # jina-embeddings-v3 output dimensions


def _vector_field_name(source_field: str) -> str:
    """Return the dense vector output field name for an E5-embedded source field."""
    return f"{source_field}_vector"


class IngestPipelineService:
    """
    Creates and manages ingest pipelines for Search demos.
    Idempotent — checks before creating.
    """

    def __init__(self, es_client: Elasticsearch):
        self.es = es_client

    def ensure_embedding_pipeline(
        self,
        demo_slug: str,
        semantic_fields: List[str],
        embedding_model: str = "elser",
        pii_fields: Optional[List[str]] = None,
    ) -> str:
        """
        Unified entry point — delegates to ELSER, E5, or Jina pipeline creation
        based on the embedding_model parameter ('elser', 'e5', or 'jina').
        """
        if embedding_model == "e5":
            return self.ensure_e5_pipeline(demo_slug, semantic_fields, pii_fields)
        if embedding_model == "jina":
            return self.ensure_jina_pipeline(demo_slug, semantic_fields, pii_fields)
        return self.ensure_elser_pipeline(demo_slug, semantic_fields, pii_fields)

    def ensure_jina_pipeline(
        self,
        demo_slug: str,
        semantic_fields: List[str],
        pii_fields: Optional[List[str]] = None,
    ) -> str:
        """
        Create an ingest pipeline using the Jina v3 inference endpoint.
        Outputs dense vectors (1024 dims) to {field}_vector for each semantic field.

        Returns the pipeline name.
        """
        pipeline_name = f"{demo_slug}-jina-pipeline"

        if self._pipeline_exists(pipeline_name):
            logger.info(f"Jina pipeline already exists: {pipeline_name}")
            return pipeline_name

        processors = []

        for sf in semantic_fields:
            processors.append({
                "inference": {
                    "model_id": JINA_ENDPOINT_ID,
                    "input_output": [
                        {
                            "input_field": sf,
                            "output_field": _vector_field_name(sf),
                        }
                    ],
                    "on_failure": [
                        {
                            "append": {
                                "field": "_source._ingest_errors",
                                "value": f"Jina inference failed for field: {sf}",
                                "ignore_failure": True,
                            }
                        }
                    ],
                }
            })

        if pii_fields:
            for pii_field in pii_fields:
                processors.append({
                    "redact": {
                        "field": pii_field,
                        "patterns": [
                            "%{EMAILADDRESS:email}",
                            "%{IP:ip_address}",
                            "\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b",
                            "\\b\\d{4}[- ]?\\d{4}[- ]?\\d{4}[- ]?\\d{4}\\b",
                        ],
                        "ignore_missing": True,
                        "ignore_failure": True,
                    }
                })

        processors.append({
            "set": {
                "field": "_source.ingested_at",
                "value": "{{_ingest.timestamp}}",
                "ignore_failure": True,
            }
        })

        pipeline_body = {
            "description": f"Jina v3 dense embedding pipeline for {demo_slug}",
            "processors": processors,
            "on_failure": [
                {"set": {"field": "event.kind", "value": "pipeline_error"}},
                {"append": {"field": "error.message", "value": "{{ _ingest.on_failure_message }}"}},
            ],
        }

        try:
            self.es.ingest.put_pipeline(id=pipeline_name, body=pipeline_body)
            logger.info(
                f"Created Jina pipeline: {pipeline_name} "
                f"(fields: {semantic_fields} → {[_vector_field_name(f) for f in semantic_fields]})"
            )
        except Exception as e:
            logger.warning(f"Could not create Jina pipeline {pipeline_name}: {e}")

        return pipeline_name

    def ensure_e5_pipeline(
        self,
        demo_slug: str,
        semantic_fields: List[str],
        pii_fields: Optional[List[str]] = None,
    ) -> str:
        """
        Create an ingest pipeline using the multilingual-e5-small model.
        Outputs dense vectors to {field}_vector for each semantic field.

        Returns the pipeline name.
        """
        pipeline_name = f"{demo_slug}-e5-pipeline"

        if self._pipeline_exists(pipeline_name):
            logger.info(f"E5 pipeline already exists: {pipeline_name}")
            return pipeline_name

        processors = []

        for sf in semantic_fields:
            processors.append({
                "inference": {
                    "model_id": E5_MODEL_ID,
                    "input_output": [
                        {
                            "input_field": sf,
                            "output_field": _vector_field_name(sf),
                        }
                    ],
                    "on_failure": [
                        {
                            "append": {
                                "field": "_source._ingest_errors",
                                "value": f"E5 inference failed for field: {sf}",
                                "ignore_failure": True,
                            }
                        }
                    ],
                }
            })

        if pii_fields:
            for pii_field in pii_fields:
                processors.append({
                    "redact": {
                        "field": pii_field,
                        "patterns": [
                            "%{EMAILADDRESS:email}",
                            "%{IP:ip_address}",
                            "\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b",
                            "\\b\\d{4}[- ]?\\d{4}[- ]?\\d{4}[- ]?\\d{4}\\b",
                        ],
                        "ignore_missing": True,
                        "ignore_failure": True,
                    }
                })

        processors.append({
            "set": {
                "field": "_source.ingested_at",
                "value": "{{_ingest.timestamp}}",
                "ignore_failure": True,
            }
        })

        pipeline_body = {
            "description": f"E5 multilingual dense embedding pipeline for {demo_slug}",
            "processors": processors,
            "on_failure": [
                {"set": {"field": "event.kind", "value": "pipeline_error"}},
                {"append": {"field": "error.message", "value": "{{ _ingest.on_failure_message }}"}},
            ],
        }

        try:
            self.es.ingest.put_pipeline(id=pipeline_name, body=pipeline_body)
            logger.info(
                f"Created E5 pipeline: {pipeline_name} "
                f"(fields: {semantic_fields} → {[_vector_field_name(f) for f in semantic_fields]})"
            )
        except Exception as e:
            logger.warning(f"Could not create E5 pipeline {pipeline_name}: {e}")

        return pipeline_name

    def ensure_elser_pipeline(
        self,
        demo_slug: str,
        semantic_fields: List[str],
        pii_fields: Optional[List[str]] = None,
    ) -> str:
        """
        Create an ingest pipeline with:
        - ELSER inference processor for each semantic field
        - Optional PII redaction processor
        - On-failure handler (logs error, does not drop document)

        Returns the pipeline name.
        """
        pipeline_name = f"{demo_slug}-elser-pipeline"

        if self._pipeline_exists(pipeline_name):
            logger.info(f"Ingest pipeline already exists: {pipeline_name}")
            return pipeline_name

        processors = []

        # ELSER inference processors for each semantic field
        for sf in semantic_fields:
            processors.append({
                "inference": {
                    "model_id": ELSER_MODEL_ID,
                    "input_output": [
                        {
                            "input_field": sf,
                            "output_field": f"ml.inference.{sf}_expanded_terms",
                        }
                    ],
                    "on_failure": [
                        {
                            "append": {
                                "field": "_source._ingest_errors",
                                "value": f"ELSER inference failed for field: {sf}",
                                "ignore_failure": True,
                            }
                        }
                    ],
                }
            })

        # PII redaction processor (if requested)
        if pii_fields:
            for pii_field in pii_fields:
                processors.append({
                    "redact": {
                        "field": pii_field,
                        "patterns": [
                            "%{EMAILADDRESS:email}",
                            "%{IP:ip_address}",
                            "\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b",  # phone
                            "\\b\\d{4}[- ]?\\d{4}[- ]?\\d{4}[- ]?\\d{4}\\b",  # credit card
                        ],
                        "ignore_missing": True,
                        "ignore_failure": True,
                    }
                })

        # Set ingestion timestamp
        processors.append({
            "set": {
                "field": "_source.ingested_at",
                "value": "{{_ingest.timestamp}}",
                "ignore_failure": True,
            }
        })

        pipeline_body = {
            "description": f"ELSER semantic search pipeline for {demo_slug}",
            "processors": processors,
            "on_failure": [
                {
                    "set": {
                        "field": "event.kind",
                        "value": "pipeline_error",
                    }
                },
                {
                    "append": {
                        "field": "error.message",
                        "value": "{{ _ingest.on_failure_message }}",
                    }
                },
            ],
        }

        try:
            self.es.ingest.put_pipeline(id=pipeline_name, body=pipeline_body)
            logger.info(
                f"Created ingest pipeline: {pipeline_name} "
                f"(semantic fields: {semantic_fields})"
            )
        except Exception as e:
            logger.warning(f"Could not create ingest pipeline {pipeline_name}: {e}")

        return pipeline_name

    def ensure_enrichment_pipeline(
        self,
        demo_slug: str,
        geo_ip_fields: Optional[List[str]] = None,
        user_agent_fields: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Create an optional enrichment pipeline for geo-ip and user-agent parsing.
        Returns None if no enrichment fields provided.
        """
        if not geo_ip_fields and not user_agent_fields:
            return None

        pipeline_name = f"{demo_slug}-enrichment-pipeline"

        if self._pipeline_exists(pipeline_name):
            logger.info(f"Enrichment pipeline already exists: {pipeline_name}")
            return pipeline_name

        processors = []

        if geo_ip_fields:
            for ip_field in geo_ip_fields:
                processors.append({
                    "geoip": {
                        "field": ip_field,
                        "target_field": f"geo.{ip_field.replace('.', '_')}",
                        "ignore_missing": True,
                        "ignore_failure": True,
                    }
                })

        if user_agent_fields:
            for ua_field in user_agent_fields:
                processors.append({
                    "user_agent": {
                        "field": ua_field,
                        "ignore_missing": True,
                        "ignore_failure": True,
                    }
                })

        try:
            self.es.ingest.put_pipeline(
                id=pipeline_name,
                body={
                    "description": f"Enrichment pipeline for {demo_slug}",
                    "processors": processors,
                }
            )
            logger.info(f"Created enrichment pipeline: {pipeline_name}")
        except Exception as e:
            logger.warning(f"Could not create enrichment pipeline {pipeline_name}: {e}")

        return pipeline_name

    def _pipeline_exists(self, pipeline_name: str) -> bool:
        try:
            self.es.ingest.get_pipeline(id=pipeline_name)
            return True
        except Exception:
            return False

    def teardown(self, demo_slug: str) -> None:
        """Remove all pipelines for this demo."""
        for suffix in ["-elser-pipeline", "-e5-pipeline", "-jina-pipeline", "-enrichment-pipeline"]:
            name = f"{demo_slug}{suffix}"
            try:
                self.es.ingest.delete_pipeline(id=name)
                logger.info(f"Deleted pipeline: {name}")
            except Exception:
                pass
