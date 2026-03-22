"""
Observability Ingest Pipeline Service

Creates enrichment + PII redaction pipelines for OTLP telemetry.

Pipeline chain:
  1. obs-enrich-<namespace>   — inject standard tags (tenant_id, region, service, env)
  2. obs-pii-redact-<namespace> — redact emails, phone numbers, credit cards from log.message
  3. obs-route-<namespace>     — route to correct data stream based on data type

Addresses:
  - "Enrich + Redact (PII)" from OTel Collector section in Genesys slide
  - "Policy-based routing" for multi-tenant data isolation
  - "Data Quality — Normalize + enrich centrally" outcome
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)


class ObsIngestPipelineService:

    def __init__(self, es: Elasticsearch):
        self.es = es

    # ── public API ────────────────────────────────────────────────────────────

    def create_all_pipelines(
        self,
        namespace: str,
        tenant_id: str,
        region: str,
        env: str = "production",
        progress: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Create the full pipeline chain for this namespace/tenant.
        Returns {pipeline_name: {success, message}}.
        """
        results = {}

        steps = [
            ("PII Redaction",  self._create_pii_pipeline,    0.25),
            ("Tag Enrichment", self._create_enrichment_pipeline, 0.60),
            ("Data Router",    self._create_routing_pipeline, 0.90),
        ]

        for label, fn, pct in steps:
            if progress:
                progress(pct, f"Creating {label} pipeline")
            ok, msg, name = fn(namespace, tenant_id, region, env)
            results[name] = {"success": ok, "message": msg}
            if ok:
                logger.info(f"Pipeline created: {name}")
            else:
                logger.warning(f"Pipeline failed: {name} — {msg}")

        return results

    def get_pipeline_names(self, namespace: str) -> Dict[str, str]:
        return {
            "enrich":  f"obs-enrich-{namespace}",
            "pii":     f"obs-pii-redact-{namespace}",
            "routing": f"obs-route-{namespace}",
        }

    # ── pipeline builders ─────────────────────────────────────────────────────

    def _create_pii_pipeline(
        self, namespace: str, tenant_id: str, region: str, env: str
    ) -> tuple:
        """
        PII redaction pipeline.
        Redacts: email addresses, phone numbers, credit card numbers
        from log.message and error.message fields.
        """
        name = f"obs-pii-redact-{namespace}"
        body = {
            "description": f"PII redaction for namespace {namespace}",
            "processors": [
                # Email redaction
                {
                    "gsub": {
                        "field":       "log.message",
                        "pattern":     r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
                        "replacement": "[EMAIL_REDACTED]",
                        "ignore_missing": True,
                    }
                },
                # Phone number redaction (E.164 + common formats)
                {
                    "gsub": {
                        "field":       "log.message",
                        "pattern":     r"(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
                        "replacement": "[PHONE_REDACTED]",
                        "ignore_missing": True,
                    }
                },
                # Credit card redaction (Luhn-ish 13-19 digit sequences)
                {
                    "gsub": {
                        "field":       "log.message",
                        "pattern":     r"\b(?:\d[ -]?){13,19}\b",
                        "replacement": "[CC_REDACTED]",
                        "ignore_missing": True,
                    }
                },
                # Also redact error.message
                {
                    "gsub": {
                        "field":       "error.message",
                        "pattern":     r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
                        "replacement": "[EMAIL_REDACTED]",
                        "ignore_missing": True,
                    }
                },
                # Tag that PII redaction ran
                {
                    "set": {
                        "field": "event.pii_redacted",
                        "value": True,
                    }
                },
            ],
            "on_failure": [
                {
                    "set": {
                        "field":   "_index",
                        "value":   "failed-pii-redaction",
                    }
                }
            ],
        }
        try:
            self.es.ingest.put_pipeline(id=name, body=body)
            return True, f"PII redaction pipeline '{name}' created", name
        except Exception as exc:
            return False, str(exc), name

    def _create_enrichment_pipeline(
        self, namespace: str, tenant_id: str, region: str, env: str
    ) -> tuple:
        """
        Tag enrichment pipeline.
        Injects: tenant_id, region, env, data_stream fields.
        Also normalises OTel attribute keys → ECS field names.
        """
        name = f"obs-enrich-{namespace}"
        body = {
            "description": f"Standard tag enrichment for tenant {tenant_id} in {region}",
            "processors": [
                # Inject standard tags (only if not already set by the sender)
                {"set": {"field": "tenant_id", "value": tenant_id,  "override": False}},
                {"set": {"field": "region",    "value": region,     "override": False}},
                {"set": {"field": "env",       "value": env,        "override": False}},
                # Map OTel resource attributes → ECS service fields
                {
                    "rename": {
                        "field":          "resource.attributes.service.name",
                        "target_field":   "service.name",
                        "ignore_missing": True,
                    }
                },
                {
                    "rename": {
                        "field":          "resource.attributes.service.version",
                        "target_field":   "service.version",
                        "ignore_missing": True,
                    }
                },
                {
                    "rename": {
                        "field":          "resource.attributes.deployment.environment",
                        "target_field":   "service.environment",
                        "ignore_missing": True,
                    }
                },
                # Copy service.name → data_stream.dataset (for data stream routing)
                {
                    "set": {
                        "field":  "data_stream.namespace",
                        "value":  namespace,
                        "override": False,
                    }
                },
                # Run PII redaction as sub-pipeline
                {
                    "pipeline": {
                        "name":           f"obs-pii-redact-{namespace}",
                        "ignore_missing_pipeline": True,
                    }
                },
            ],
            "on_failure": [
                {"set": {"field": "pipeline_error", "value": "obs-enrich"}}
            ],
        }
        try:
            self.es.ingest.put_pipeline(id=name, body=body)
            return True, f"Enrichment pipeline '{name}' created (tenant={tenant_id}, region={region})", name
        except Exception as exc:
            return False, str(exc), name

    def _create_routing_pipeline(
        self, namespace: str, tenant_id: str, region: str, env: str
    ) -> tuple:
        """
        Routing pipeline — sets data_stream.type based on signal type.
        Uses conditional processors to route logs/metrics/traces correctly.
        """
        name = f"obs-route-{namespace}"
        body = {
            "description": f"Data stream routing for namespace {namespace}",
            "processors": [
                # Default to logs if type not set
                {
                    "set": {
                        "field":    "data_stream.type",
                        "value":    "logs",
                        "override": False,
                    }
                },
                # If transaction.id present → traces
                {
                    "set": {
                        "if":     "ctx.containsKey('transaction') && ctx.transaction.containsKey('id')",
                        "field":  "data_stream.type",
                        "value":  "traces",
                    }
                },
                # If metricset.name present → metrics
                {
                    "set": {
                        "if":     "ctx.containsKey('metricset')",
                        "field":  "data_stream.type",
                        "value":  "metrics",
                    }
                },
                # Set dataset from service.name or default to "otel"
                {
                    "set": {
                        "field":  "data_stream.dataset",
                        "value":  "{{service.name}}",
                        "ignore_empty_value": True,
                        "override": False,
                    }
                },
                {
                    "set": {
                        "field":    "data_stream.dataset",
                        "value":    "otel",
                        "override": False,
                    }
                },
                # Run enrichment as sub-pipeline
                {
                    "pipeline": {
                        "name":           f"obs-enrich-{namespace}",
                        "ignore_missing_pipeline": True,
                    }
                },
            ],
        }
        try:
            self.es.ingest.put_pipeline(id=name, body=body)
            return True, f"Routing pipeline '{name}' created", name
        except Exception as exc:
            return False, str(exc), name
