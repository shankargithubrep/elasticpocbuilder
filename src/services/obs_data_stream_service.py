"""
Observability Data Stream Service

Creates OTLP-compatible index templates and data streams for:
  logs-<dataset>-<namespace>
  metrics-<dataset>-<namespace>
  traces-<dataset>-<namespace>

Standard tags injected on ALL documents (Genesys multi-tenant pattern):
  tenant_id   — isolates data per customer
  region      — which Elastic cluster (data residency)
  service     — APM service name
  env         — production / staging / dev

ECS + OTel field mappings included for full APM compatibility.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)

# ── Standard tag mappings (injected into every template) ─────────────────────

_STANDARD_TAGS = {
    "tenant_id": {"type": "keyword"},
    "region":    {"type": "keyword"},
    "service":   {"type": "keyword"},
    "env":       {"type": "keyword"},
}

# ── ECS base fields ──────────────────────────────────────────────────────────

_ECS_BASE = {
    "@timestamp":      {"type": "date"},
    "message":         {"type": "text", "fields": {"keyword": {"type": "keyword", "ignore_above": 1024}}},
    "log.level":       {"type": "keyword"},
    "log.logger":      {"type": "keyword"},
    "error.message":   {"type": "text"},
    "error.type":      {"type": "keyword"},
    "error.stack_trace": {"type": "text"},
    "event.action":    {"type": "keyword"},
    "event.category":  {"type": "keyword"},
    "event.outcome":   {"type": "keyword"},
    "event.duration":  {"type": "long"},
    "host.name":       {"type": "keyword"},
    "host.ip":         {"type": "ip"},
    "container.id":    {"type": "keyword"},
    "container.name":  {"type": "keyword"},
    "kubernetes.pod.name":       {"type": "keyword"},
    "kubernetes.namespace.name": {"type": "keyword"},
    "kubernetes.node.name":      {"type": "keyword"},
}

# ── APM / trace fields ────────────────────────────────────────────────────────

_APM_FIELDS = {
    "transaction.id":             {"type": "keyword"},
    "transaction.type":           {"type": "keyword"},
    "transaction.name":           {"type": "keyword"},
    "transaction.result":         {"type": "keyword"},
    "transaction.duration.us":    {"type": "long"},
    "transaction.sampled":        {"type": "boolean"},
    "span.id":                    {"type": "keyword"},
    "span.name":                  {"type": "keyword"},
    "span.type":                  {"type": "keyword"},
    "span.subtype":               {"type": "keyword"},
    "span.duration.us":           {"type": "long"},
    "span.outcome":               {"type": "keyword"},
    "span.destination.service.name": {"type": "keyword"},
    "trace.id":                   {"type": "keyword"},
    "parent.id":                  {"type": "keyword"},
    "service.name":               {"type": "keyword"},
    "service.version":            {"type": "keyword"},
    "service.environment":        {"type": "keyword"},
    "service.language.name":      {"type": "keyword"},
    "agent.name":                 {"type": "keyword"},
    "agent.version":              {"type": "keyword"},
}

# ── Metrics fields (TSDB-compatible) ─────────────────────────────────────────

_METRICS_FIELDS = {
    "service.name":               {"type": "keyword", "time_series_dimension": True},
    "metricset.name":             {"type": "keyword"},
    "system.cpu.total.norm.pct":  {"type": "float",   "time_series_metric": "gauge"},
    "system.memory.actual.used.bytes": {"type": "long", "time_series_metric": "gauge"},
    "system.memory.total":        {"type": "long"},
    "jvm.memory.heap.used":       {"type": "long",    "time_series_metric": "gauge"},
    "jvm.gc.collection.ms":       {"type": "long",    "time_series_metric": "counter"},
    "http.server.duration":       {"type": "histogram"},
    "process.cpu.pct":            {"type": "float",   "time_series_metric": "gauge"},
}


class ObsDataStreamService:

    def __init__(self, es: Elasticsearch):
        self.es = es

    # ── public API ────────────────────────────────────────────────────────────

    def create_all_templates(
        self,
        namespace: str,
        ilm_policy_prefix: str = "obs",
        services: Optional[List[str]] = None,
        progress: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Create component templates + index templates for logs, metrics, traces.
        namespace  — typically the tenant_id or customer slug
        services   — list of service names; if None, creates wildcard templates
        """
        results = {}

        # 1. Shared component template (standard tags + ECS base)
        if progress:
            progress(0.1, "Creating shared component template")
        ok, msg = self._create_component_template(namespace)
        results["component_template"] = {"success": ok, "message": msg}

        steps = [
            ("logs",    _ECS_BASE,                    f"{ilm_policy_prefix}-logs-{namespace}-ilm"),
            ("metrics", {**_METRICS_FIELDS},          f"{ilm_policy_prefix}-metrics-{namespace}-ilm"),
            ("traces",  {**_ECS_BASE, **_APM_FIELDS}, f"{ilm_policy_prefix}-traces-{namespace}-ilm"),
        ]

        for i, (data_type, extra_fields, ilm_name) in enumerate(steps):
            if progress:
                progress(0.2 + (i + 1) * 0.2, f"Creating {data_type} index template")
            ok, msg = self._create_index_template(
                namespace=namespace,
                data_type=data_type,
                extra_fields=extra_fields,
                ilm_policy=ilm_name,
            )
            results[f"{data_type}_template"] = {"success": ok, "message": msg}

        # 2. Bootstrap data streams
        if progress:
            progress(0.9, "Bootstrapping data streams")
        for data_type in ("logs", "metrics", "traces"):
            stream_name = f"{data_type}-otel-{namespace}"
            ok, msg = self._bootstrap_data_stream(stream_name)
            results[f"{data_type}_stream"] = {"success": ok, "message": msg}

        return results

    def get_data_stream_info(self, namespace: str) -> Dict[str, Any]:
        """Return stats for all data streams in this namespace."""
        info = {}
        for dt in ("logs", "metrics", "traces"):
            name = f"{dt}-otel-{namespace}"
            try:
                resp = self.es.indices.get_data_stream(name=name)
                streams = resp.get("data_streams", [])
                if streams:
                    s = streams[0]
                    info[name] = {
                        "status":       s.get("status", "?"),
                        "indices":      len(s.get("indices", [])),
                        "generation":   s.get("generation", 0),
                    }
                else:
                    info[name] = {"status": "not_found"}
            except Exception:
                info[name] = {"status": "not_found"}
        return info

    # ── private ───────────────────────────────────────────────────────────────

    def _create_component_template(self, namespace: str) -> tuple:
        """Shared component: standard tags + ECS base + data_stream routing."""
        name = f"obs-standard-tags-{namespace}"
        body = {
            "template": {
                "mappings": {
                    "dynamic":    "true",
                    "properties": {
                        **_STANDARD_TAGS,
                        "data_stream": {
                            "properties": {
                                "type":      {"type": "constant_keyword"},
                                "dataset":   {"type": "constant_keyword"},
                                "namespace": {"type": "constant_keyword"},
                            }
                        },
                    },
                }
            },
            "_meta": {
                "description": f"Standard observability tags for namespace {namespace}",
                "namespace":   namespace,
            },
        }
        try:
            self.es.cluster.put_component_template(name=name, body=body)
            return True, f"Component template '{name}' created"
        except Exception as exc:
            return False, str(exc)

    def _create_index_template(
        self,
        namespace: str,
        data_type: str,
        extra_fields: Dict,
        ilm_policy: str,
    ) -> tuple:
        """Create an index template for one data type."""
        template_name = f"obs-{data_type}-{namespace}"
        pattern = f"{data_type}-*-{namespace}"

        is_metrics = data_type == "metrics"

        body: Dict[str, Any] = {
            "index_patterns":   [pattern],
            "data_stream":      {},
            "composed_of":      [f"obs-standard-tags-{namespace}"],
            "priority":         500,
            "template": {
                "settings": {
                    "index": {
                        "lifecycle":          {"name": ilm_policy},
                        "number_of_shards":   1,
                        "number_of_replicas": 1,
                        **({"mode": "time_series", "routing_path": ["service.name", "tenant_id"]}
                           if is_metrics else {}),
                    }
                },
                "mappings": {
                    "dynamic":    "true",
                    "properties": {
                        **_STANDARD_TAGS,
                        **extra_fields,
                    },
                },
            },
            "_meta": {
                "namespace":  namespace,
                "data_type":  data_type,
                "managed_by": "vulcan-obs-provisioner",
            },
        }
        try:
            self.es.indices.put_index_template(name=template_name, body=body)
            return True, f"Index template '{template_name}' created (pattern: {pattern})"
        except Exception as exc:
            return False, str(exc)

    def _bootstrap_data_stream(self, stream_name: str) -> tuple:
        """Create the data stream if it doesn't already exist."""
        try:
            exists = self.es.indices.exists_data_stream(name=stream_name)
            if exists:
                return True, f"Data stream '{stream_name}' already exists"
            self.es.indices.create_data_stream(name=stream_name)
            return True, f"Data stream '{stream_name}' created"
        except Exception as exc:
            return False, str(exc)
