"""
Search Provisioner

Orchestrates all Search stack provisioning in the correct order.
Single entry point called by the orchestrator after demo generation.
Saves a complete elastic_assets.json manifest to the demo folder.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

from elasticsearch import Elasticsearch
from dotenv import load_dotenv

from .search_preflight_service import SearchPreflightService
from .index_template_service import IndexTemplateService
from .ingest_pipeline_service import IngestPipelineService
from .search_application_service import SearchApplicationService
from .kibana_assets_service import KibanaAssetsService

load_dotenv()
logger = logging.getLogger(__name__)


def _build_es_client() -> Elasticsearch:
    api_key = os.getenv("ELASTICSEARCH_API_KEY", "")
    cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
    if cloud_id:
        return Elasticsearch(cloud_id=cloud_id, api_key=api_key)
    endpoint = os.getenv("ELASTIC_ENDPOINT", "")
    return Elasticsearch(endpoint, api_key=api_key)


class SearchProvisioner:
    """
    Orchestrates full Elastic Search stack provisioning for a demo.

    Provisioning sequence:
      1. Preflight (models, Kibana, Slack)
      2. ILM policy + index template + ingest pipeline
      3. Search Application + Query Rules + Synonyms
      4. Kibana: Slack connector
      5. Kibana: Dashboard (P95 + volume + errors + terms)
      6. Kibana: Alerting rules
      7. Kibana: Cases connector config
      8. Kibana: Discover view
      9. Scoped read-only API key
     10. Save elastic_assets.json
    """

    def __init__(self, es_client: Optional[Elasticsearch] = None):
        self.es = es_client or _build_es_client()
        self.preflight_svc = SearchPreflightService(self.es)
        self.template_svc = IndexTemplateService(self.es)
        self.pipeline_svc = IngestPipelineService(self.es)
        self.search_app_svc = SearchApplicationService(self.es)
        self.kibana_svc = KibanaAssetsService(self.es)

    def provision_all(
        self,
        demo_slug: str,
        query_strategy: Dict[str, Any],
        datasets: Dict[str, Any],
        module_path: str,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Provision all Search stack assets. Fail-open: each step is wrapped
        independently so partial provisioning is always recorded.

        Returns the elastic_assets dict (also saved to elastic_assets.json).
        """
        def _progress(pct: float, msg: str):
            if progress_callback:
                try:
                    progress_callback(pct, f"🔧 {msg}")
                except Exception:
                    pass
            logger.info(f"[{int(pct * 100)}%] {msg}")

        assets: Dict[str, Any] = {
            "demo_name": demo_slug,
            "provisioned_at": datetime.now(timezone.utc).isoformat(),
            "indices": [],
            "ingest_pipeline": None,
            "index_template": None,
            "ilm_policy": None,
            "search_application": None,
            "query_rules_id": None,
            "synonyms_id": None,
            "kibana_dashboard_ids": [],
            "alerting_rule_ids": [],
            "slack_connector_id": None,
            "case_connector_configured": False,
            "discover_view_ids": [],
            "data_view_ids": [],
            "scoped_api_key": None,
            "preflight_results": {},
            "health_check": {},
            "provisioning_errors": [],
        }

        # Extract useful fields from the query strategy
        customer = query_strategy.get("customer_context", {})
        company_name = customer.get("company_name", demo_slug)
        industry = customer.get("industry", "")
        index_names = self._extract_index_names(query_strategy, datasets)
        semantic_fields = self._extract_semantic_fields(query_strategy)
        text_fields = self._extract_text_fields(query_strategy)
        field_mappings = self._extract_field_mappings(datasets)
        assets["indices"] = index_names

        # Resolve embedding model — from query_strategy, then session_state, then default
        embedding_model = query_strategy.get("embedding_model", "elser")
        try:
            import streamlit as st
            sidebar_type = st.session_state.get("inference_endpoints", {}).get("embedding_type", "elser")
            if sidebar_type in ("elser", "e5", "jina"):
                embedding_model = sidebar_type
            elif sidebar_type == "dense":
                embedding_model = "e5"
            elif sidebar_type == "sparse":
                embedding_model = "elser"
        except Exception:
            pass
        assets["embedding_model"] = embedding_model
        logger.info(f"Provisioning with embedding model: {embedding_model}")

        # --- Step 1: Preflight ---
        _progress(0.88, f"Running preflight checks (model: {embedding_model})...")
        try:
            report = self.preflight_svc.run_all(embedding_model=embedding_model)
            assets["preflight_results"] = report.to_dict()
            if not report.checks.get("elasticsearch", {}).passed if hasattr(report.checks.get("elasticsearch"), "passed") else not report.checks.get("elasticsearch", {}).get("passed", True):
                logger.warning("ES preflight failed — aborting provisioning")
                self._save_assets(module_path, assets)
                return assets
        except Exception as e:
            assets["provisioning_errors"].append(f"preflight: {e}")

        # --- Step 2: ILM + Index Template + Ingest Pipeline ---
        _progress(0.89, f"Creating index templates and {'E5' if embedding_model == 'e5' else 'ELSER'} pipeline...")
        try:
            pipeline_name = self.pipeline_svc.ensure_embedding_pipeline(
                demo_slug, semantic_fields, embedding_model=embedding_model
            )
            assets["ingest_pipeline"] = pipeline_name

            template_results = self.template_svc.ensure_search_stack(
                demo_slug=demo_slug,
                index_names=index_names,
                field_mappings=field_mappings,
                semantic_fields=semantic_fields,
                pipeline_name=pipeline_name,
                embedding_model=embedding_model,
            )
            assets["ilm_policy"] = template_results.get("ilm_policy")
            assets["index_template"] = template_results.get("index_template")
        except Exception as e:
            logger.warning(f"Template/pipeline provisioning error: {e}")
            assets["provisioning_errors"].append(f"templates: {e}")

        # --- Step 3: Search Application + Query Rules + Synonyms ---
        _progress(0.90, "Creating Search Application...")
        try:
            app_name = self.search_app_svc.ensure_search_application(
                demo_slug=demo_slug,
                index_names=index_names,
                semantic_fields=semantic_fields,
                text_fields=text_fields,
                embedding_model=embedding_model,
            )
            assets["search_application"] = app_name
        except Exception as e:
            logger.warning(f"Search Application error: {e}")
            assets["provisioning_errors"].append(f"search_app: {e}")

        try:
            synonyms_id = self.search_app_svc.ensure_synonyms(
                demo_slug=demo_slug,
                industry=industry,
            )
            assets["synonyms_id"] = synonyms_id
        except Exception as e:
            assets["provisioning_errors"].append(f"synonyms: {e}")

        # --- Step 4: Slack Connector ---
        _progress(0.91, "Configuring Slack connector...")
        try:
            slack_id = self.kibana_svc.ensure_slack_connector()
            assets["slack_connector_id"] = slack_id
        except Exception as e:
            logger.warning(f"Slack connector error: {e}")
            assets["provisioning_errors"].append(f"slack: {e}")

        # --- Step 5: Kibana Dashboard ---
        _progress(0.92, "Creating Kibana dashboards...")
        try:
            duration_field = self._detect_duration_field(query_strategy)
            error_field = self._detect_error_field(query_strategy)
            query_field = self._detect_query_field(query_strategy)

            dashboard_id = self.kibana_svc.create_dashboard(
                demo_slug=demo_slug,
                index_names=index_names,
                query_field=query_field,
                duration_field=duration_field,
                error_field=error_field,
                company_name=company_name,
            )
            if dashboard_id:
                assets["kibana_dashboard_ids"].append(dashboard_id)
        except Exception as e:
            logger.warning(f"Dashboard error: {e}")
            assets["provisioning_errors"].append(f"dashboard: {e}")

        # --- Step 6: Alerting Rules ---
        _progress(0.93, "Creating alerting rules...")
        try:
            rule_ids = self.kibana_svc.create_alert_rules(
                demo_slug=demo_slug,
                index_names=index_names,
                slack_connector_id=assets.get("slack_connector_id"),
                duration_field=duration_field,
                company_name=company_name,
            )
            assets["alerting_rule_ids"] = rule_ids
        except Exception as e:
            logger.warning(f"Alert rules error: {e}")
            assets["provisioning_errors"].append(f"alerting: {e}")

        # --- Step 7: Cases ---
        _progress(0.94, "Configuring case management...")
        try:
            configured = self.kibana_svc.configure_case_connector(
                slack_connector_id=assets.get("slack_connector_id")
            )
            assets["case_connector_configured"] = configured
        except Exception as e:
            assets["provisioning_errors"].append(f"cases: {e}")

        # --- Step 8: Discover View ---
        _progress(0.95, "Creating Discover saved views...")
        try:
            display_fields = (text_fields + semantic_fields)[:8] or ["@timestamp"]
            view_id = self.kibana_svc.create_discover_view(
                demo_slug=demo_slug,
                index_names=index_names,
                display_fields=display_fields,
                company_name=company_name,
            )
            if view_id:
                assets["discover_view_ids"].append(view_id)
        except Exception as e:
            logger.warning(f"Discover view error: {e}")
            assets["provisioning_errors"].append(f"discover: {e}")

        # --- Step 8b: Kibana Data Views ---
        _progress(0.955, "Creating Kibana Data Views...")
        try:
            data_view_ids = self.kibana_svc.ensure_data_views(index_names)
            assets["data_view_ids"] = data_view_ids
        except Exception as e:
            logger.warning(f"Data views error: {e}")
            assets["provisioning_errors"].append(f"data_views: {e}")

        # --- Step 9: Scoped API Key ---
        _progress(0.96, "Creating scoped API key...")
        try:
            key_info = self.kibana_svc.create_scoped_api_key(
                demo_slug=demo_slug,
                index_names=index_names,
            )
            assets["scoped_api_key"] = key_info
        except Exception as e:
            assets["provisioning_errors"].append(f"api_key: {e}")

        # --- Step 10: Save manifest ---
        _progress(0.97, "Saving provisioning manifest...")
        self._save_assets(module_path, assets)

        error_count = len(assets["provisioning_errors"])
        if error_count:
            logger.warning(f"Provisioning completed with {error_count} non-fatal errors")
        else:
            logger.info("Search stack provisioning completed successfully")

        return assets

    def teardown_all(self, module_path: str) -> None:
        """Remove all provisioned assets for a demo (reads elastic_assets.json)."""
        assets = self._load_assets(module_path)
        if not assets:
            logger.warning("No elastic_assets.json found — nothing to teardown")
            return

        demo_slug = assets.get("demo_name", "")

        self.pipeline_svc.teardown(demo_slug)
        self.template_svc.teardown(demo_slug)
        self.search_app_svc.teardown(demo_slug)
        self.kibana_svc.teardown_demo_assets(
            dashboard_ids=assets.get("kibana_dashboard_ids", []),
            alert_rule_ids=assets.get("alerting_rule_ids", []),
            discover_view_ids=assets.get("discover_view_ids", []),
            scoped_api_key_id=(assets.get("scoped_api_key") or {}).get("id"),
        )

        # Remove assets file
        assets_path = Path(module_path) / "elastic_assets.json"
        if assets_path.exists():
            assets_path.unlink()
            logger.info("Removed elastic_assets.json")

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _extract_index_names(
        self, query_strategy: Dict, datasets: Dict
    ) -> List[str]:
        names = []
        # From query strategy datasets
        for ds in query_strategy.get("datasets", []):
            name = ds.get("index_name") or ds.get("name")
            if name:
                names.append(name)
        # From datasets dict keys as fallback
        if not names:
            for key in datasets:
                names.append(key.lower().replace(" ", "-"))
        return names or ["demo-search-index"]

    def _extract_semantic_fields(self, query_strategy: Dict) -> List[str]:
        fields = []
        for ds in query_strategy.get("datasets", []):
            for f in ds.get("semantic_fields", []):
                if f not in fields:
                    fields.append(f)
        return fields or []

    def _extract_text_fields(self, query_strategy: Dict) -> List[str]:
        fields = []
        for ds in query_strategy.get("datasets", []):
            for f in ds.get("text_fields", ds.get("key_fields", [])):
                if f not in fields:
                    fields.append(f)
        return fields or []

    def _extract_field_mappings(self, datasets: Dict) -> Dict[str, Any]:
        """Build a basic properties dict from dataset column names."""
        properties: Dict[str, Any] = {}
        for _name, df in datasets.items():
            if hasattr(df, "columns"):
                for col in df.columns:
                    if col == "@timestamp":
                        properties[col] = {"type": "date"}
                    elif col not in properties:
                        properties[col] = {"type": "text", "fields": {"keyword": {"type": "keyword"}}}
        return {"properties": properties}

    def _detect_duration_field(self, query_strategy: Dict) -> str:
        candidates = ["response_time_ms", "duration_ms", "latency_ms", "event.duration", "took"]
        for ds in query_strategy.get("datasets", []):
            for f in ds.get("key_fields", []) + ds.get("numeric_fields", []):
                if any(k in f.lower() for k in ["duration", "latency", "response_time", "took"]):
                    return f
        return "response_time_ms"

    def _detect_error_field(self, query_strategy: Dict) -> str:
        candidates = ["error_code", "status_code", "http_status", "error", "outcome"]
        for ds in query_strategy.get("datasets", []):
            for f in ds.get("key_fields", []):
                if any(k in f.lower() for k in ["error", "status", "outcome"]):
                    return f
        return "status_code"

    def _detect_query_field(self, query_strategy: Dict) -> str:
        for ds in query_strategy.get("datasets", []):
            for f in ds.get("key_fields", []):
                if any(k in f.lower() for k in ["query", "search_term", "keyword", "q"]):
                    return f
        return "query"

    def _save_assets(self, module_path: str, assets: Dict) -> None:
        path = Path(module_path) / "elastic_assets.json"
        path.write_text(json.dumps(assets, indent=2, default=str))
        logger.info(f"Saved elastic_assets.json → {path}")

    def _load_assets(self, module_path: str) -> Optional[Dict]:
        path = Path(module_path) / "elastic_assets.json"
        if path.exists():
            return json.loads(path.read_text())
        return None
