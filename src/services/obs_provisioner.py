"""
Observability Provisioner

Orchestrates the full Elastic Observability stack setup in the correct order.
Single entry point called by the demo framework after observability demo generation.

Provisioning sequence:
  1. Preflight  — check ES connection, verify cluster capabilities
  2. ILM        — create hot/warm/cold/frozen retention policies (logs/metrics/traces)
  3. Templates  — create OTLP-compatible data stream index templates
  4. Pipelines  — create PII redaction + tag enrichment + routing pipelines
  5. Data       — index sample telemetry data with standard tags
  6. Kibana     — create data views for all data streams
  7. Manifest   — save obs_assets.json to demo folder

Supports multi-region: pass a MultiRegionElasticClient to provision across regions.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from elasticsearch import Elasticsearch
from dotenv import load_dotenv

from .obs_ilm_service import ObsILMService
from .obs_data_stream_service import ObsDataStreamService
from .obs_ingest_pipeline_service import ObsIngestPipelineService

load_dotenv()
logger = logging.getLogger(__name__)


def _build_es_client() -> Elasticsearch:
    api_key  = os.getenv("ELASTICSEARCH_API_KEY", "")
    cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
    if cloud_id:
        return Elasticsearch(cloud_id=cloud_id, api_key=api_key)
    endpoint = os.getenv("ELASTIC_ENDPOINT", "")
    return Elasticsearch(endpoint, api_key=api_key)


class ObsProvisioner:
    """
    Orchestrates full Elastic Observability stack provisioning.

    Single-region usage:
        provisioner = ObsProvisioner()
        assets = provisioner.provision_all(config, module_path, progress_callback)

    Multi-region usage:
        from src.services.multi_region_elastic_client import MultiRegionElasticClient
        mr_client = MultiRegionElasticClient.from_config()
        for region_name in ["US East", "EU West"]:
            es = mr_client.get_es(region_name)
            prov = ObsProvisioner(es_client=es)
            prov.provision_all(config, module_path, progress_callback, region=region_name)
    """

    def __init__(self, es_client: Optional[Elasticsearch] = None):
        self.es       = es_client or _build_es_client()
        self.ilm_svc  = ObsILMService(self.es)
        self.ds_svc   = ObsDataStreamService(self.es)
        self.pipe_svc = ObsIngestPipelineService(self.es)

    def provision_all(
        self,
        config: Dict[str, Any],
        module_path: str,
        progress_callback: Optional[Callable] = None,
        region: str = "primary",
    ) -> Dict[str, Any]:
        """
        Provision all Observability stack assets for a demo.
        Fail-open: each step is wrapped independently.

        Returns the obs_assets dict (also saved to obs_assets.json).
        """
        def _p(pct: float, msg: str):
            if progress_callback:
                try:
                    progress_callback(pct, f"🔭 {msg}")
                except Exception:
                    pass

        # Derive namespace + tenant from config
        ctx       = config.get("customer_context") or config
        company   = ctx.get("company_name", "demo")
        namespace = company.lower().replace(" ", "-")[:20]
        tenant_id = config.get("tenant_id", namespace)
        env       = config.get("env", "production")
        sub_cat   = config.get("sub_category", "apm")

        assets: Dict[str, Any] = {
            "demo_name":       config.get("module_name", namespace),
            "provisioned_at":  datetime.now(timezone.utc).isoformat(),
            "region":          region,
            "namespace":       namespace,
            "tenant_id":       tenant_id,
            "env":             env,
            "sub_category":    sub_cat,
            "ilm_policies":    {},
            "index_templates": {},
            "data_streams":    {},
            "pipelines":       {},
            "kibana_data_views": [],
            "provisioning_errors": [],
        }

        errors = assets["provisioning_errors"]

        # ── Step 1: Preflight ─────────────────────────────────────────────────
        _p(0.05, "Running preflight checks")
        try:
            info = self.es.info()
            assets["cluster_version"] = info.get("version", {}).get("number", "?")
            assets["cluster_name"]    = info.get("cluster_name", "?")
            logger.info(f"Connected to ES {assets['cluster_version']} (cluster: {assets['cluster_name']})")
        except Exception as exc:
            errors.append(f"Preflight failed: {exc}")
            logger.error(f"Preflight failed: {exc}")
            self._save_assets(assets, module_path)
            return assets

        # ── Step 2: ILM Policies ──────────────────────────────────────────────
        _p(0.15, "Creating ILM retention policies (hot→warm→cold→frozen)")
        try:
            ilm_results = self.ilm_svc.create_all_policies(namespace=namespace)
            assets["ilm_policies"] = ilm_results
            failed_ilm = [k for k, v in ilm_results.items() if not v["success"]]
            if failed_ilm:
                errors.append(f"ILM failures: {failed_ilm}")
        except Exception as exc:
            errors.append(f"ILM step failed: {exc}")
            logger.warning(f"ILM step failed: {exc}")

        # ── Step 3: Index Templates + Data Streams ────────────────────────────
        _p(0.35, "Creating OTLP-compatible data stream templates")
        try:
            template_results = self.ds_svc.create_all_templates(
                namespace=namespace,
                ilm_policy_prefix="obs",
            )
            assets["index_templates"] = template_results

            # Get data stream info after creation
            assets["data_streams"] = self.ds_svc.get_data_stream_info(namespace)
        except Exception as exc:
            errors.append(f"Template step failed: {exc}")
            logger.warning(f"Template step failed: {exc}")

        # ── Step 4: Ingest Pipelines ──────────────────────────────────────────
        _p(0.55, "Creating enrichment + PII redaction + routing pipelines")
        try:
            pipeline_results = self.pipe_svc.create_all_pipelines(
                namespace=namespace,
                tenant_id=tenant_id,
                region=region,
                env=env,
            )
            assets["pipelines"] = pipeline_results
        except Exception as exc:
            errors.append(f"Pipeline step failed: {exc}")
            logger.warning(f"Pipeline step failed: {exc}")

        # ── Step 5: Index sample telemetry ────────────────────────────────────
        _p(0.70, "Indexing sample telemetry data")
        try:
            indexed = self._index_sample_data(namespace, tenant_id, region, env, sub_cat)
            assets["sample_docs_indexed"] = indexed
        except Exception as exc:
            errors.append(f"Sample data indexing failed: {exc}")
            logger.warning(f"Sample data failed: {exc}")

        # ── Step 6: Kibana Data Views ─────────────────────────────────────────
        _p(0.85, "Creating Kibana Data Views")
        try:
            kibana_url = os.getenv("ELASTICSEARCH_KIBANA_URL", "")
            api_key    = os.getenv("ELASTICSEARCH_API_KEY", "")
            if kibana_url and api_key:
                views = self._create_kibana_data_views(namespace, kibana_url, api_key)
                assets["kibana_data_views"] = views
            else:
                assets["kibana_data_views"] = []
                logger.info("Skipping Kibana Data Views — KIBANA_URL not configured")
        except Exception as exc:
            errors.append(f"Kibana Data Views failed: {exc}")
            logger.warning(f"Kibana step failed: {exc}")

        # ── Step 7: Save manifest ─────────────────────────────────────────────
        _p(0.98, "Saving obs_assets.json")
        self._save_assets(assets, module_path)

        _p(1.0, f"Observability stack ready — {len(errors)} error(s)")
        logger.info(
            f"Observability provisioning complete for {namespace} "
            f"({len(errors)} errors)"
        )
        return assets

    # ── multi-region convenience ──────────────────────────────────────────────

    def provision_all_regions(
        self,
        config: Dict[str, Any],
        module_path: str,
        region_configs: List[Dict],   # [{name, es_url, api_key, ...}]
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Provision the observability stack across multiple regions.
        Each region gets its own ILM/templates/pipelines but shares the same config.
        Returns {region_name: assets_dict}.
        """
        from .multi_region_elastic_client import RegionClient
        from .region_config_service import RegionConfig

        all_assets: Dict[str, Any] = {}
        total = len(region_configs)

        for i, rc_dict in enumerate(region_configs):
            region_name = rc_dict.get("name", f"region-{i}")

            def _region_progress(pct: float, msg: str, rn=region_name):
                if progress_callback:
                    overall = (i / total) + (pct / total)
                    progress_callback(overall, f"[{rn}] {msg}")

            try:
                cfg = RegionConfig(**{k: v for k, v in rc_dict.items()
                                      if k in RegionConfig.__dataclass_fields__})
                rc = RegionClient(cfg)
                provisioner = ObsProvisioner(es_client=rc.es)
                assets = provisioner.provision_all(
                    config=config,
                    module_path=module_path,
                    progress_callback=_region_progress,
                    region=region_name,
                )
                all_assets[region_name] = assets
            except Exception as exc:
                logger.error(f"Region {region_name} provisioning failed: {exc}")
                all_assets[region_name] = {"error": str(exc)}

        # Save combined manifest
        combined_path = Path(module_path) / "obs_assets_all_regions.json"
        try:
            combined_path.write_text(
                json.dumps(all_assets, indent=2, default=str), encoding="utf-8"
            )
        except Exception as exc:
            logger.warning(f"Could not save combined assets: {exc}")

        return all_assets

    # ── private helpers ───────────────────────────────────────────────────────

    def _index_sample_data(
        self, namespace: str, tenant_id: str, region: str, env: str, sub_cat: str
    ) -> int:
        """Index a small set of sample telemetry docs to bootstrap the data streams."""
        from elasticsearch.helpers import bulk
        from datetime import timedelta
        import random

        services = ["api-gateway", "auth-service", "contact-routing", "voice-transcription"]
        docs = []
        now = datetime.now(timezone.utc)

        for i in range(50):
            svc = random.choice(services)
            ts  = (now - timedelta(minutes=random.randint(0, 60))).isoformat()

            # Log document
            docs.append({
                "_index":     f"logs-otel-{namespace}",
                "_source": {
                    "@timestamp": ts,
                    "tenant_id":  tenant_id,
                    "region":     region,
                    "env":        env,
                    "service":    svc,
                    "service.name": svc,
                    "log.level":  random.choice(["INFO", "INFO", "WARN", "ERROR"]),
                    "log.message": f"Sample log from {svc} for tenant {tenant_id}",
                    "data_stream.type":      "logs",
                    "data_stream.dataset":   svc,
                    "data_stream.namespace": namespace,
                },
            })

            # Trace/transaction document
            docs.append({
                "_index":     f"traces-otel-{namespace}",
                "_source": {
                    "@timestamp":              ts,
                    "tenant_id":               tenant_id,
                    "region":                  region,
                    "env":                     env,
                    "service":                 svc,
                    "service.name":            svc,
                    "transaction.id":          f"tx-{i:04d}",
                    "transaction.type":        "request",
                    "transaction.name":        f"GET /api/{svc}/health",
                    "transaction.duration.us": random.randint(1000, 500000),
                    "transaction.result":      random.choice(["HTTP 2xx", "HTTP 2xx", "HTTP 5xx"]),
                    "trace.id":                f"trace-{i:04d}",
                    "data_stream.type":        "traces",
                    "data_stream.dataset":     svc,
                    "data_stream.namespace":   namespace,
                },
            })

        success, failed = bulk(self.es, docs, raise_on_error=False, request_timeout=60)
        logger.info(f"Indexed {success} sample telemetry docs ({len(failed)} failed)")
        return success

    def _create_kibana_data_views(
        self, namespace: str, kibana_url: str, api_key: str
    ) -> List[str]:
        import urllib.request

        created = []
        headers = {
            "kbn-xsrf": "obs-provisioner",
            "Content-Type": "application/json",
            "Authorization": f"ApiKey {api_key}",
        }
        data_views = [
            {"title": f"logs-*-{namespace}*",    "name": f"Logs — {namespace}"},
            {"title": f"metrics-*-{namespace}*", "name": f"Metrics — {namespace}"},
            {"title": f"traces-*-{namespace}*",  "name": f"Traces — {namespace}"},
        ]
        for dv in data_views:
            payload = json.dumps({"data_view": {**dv, "timeFieldName": "@timestamp"}}).encode()
            req = urllib.request.Request(
                f"{kibana_url.rstrip('/')}/api/data_views/data_view",
                data=payload, headers=headers, method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    body = json.loads(resp.read())
                    created.append(body.get("data_view", {}).get("id", dv["name"]))
                    logger.info(f"Kibana Data View created: {dv['name']}")
            except urllib.error.HTTPError as exc:
                if exc.code == 409:
                    created.append(f"{dv['name']} (already exists)")
                else:
                    logger.warning(f"Data View {dv['name']}: HTTP {exc.code}")
            except Exception as exc:
                logger.warning(f"Data View {dv['name']}: {exc}")
        return created

    def _save_assets(self, assets: Dict[str, Any], module_path: str):
        try:
            path = Path(module_path) / "obs_assets.json"
            path.write_text(json.dumps(assets, indent=2, default=str), encoding="utf-8")
            logger.info(f"obs_assets.json saved to {path}")
        except Exception as exc:
            logger.warning(f"Could not save obs_assets.json: {exc}")
