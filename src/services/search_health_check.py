"""
Search Health Check Service

Pre-demo checklist that verifies all provisioned assets are live and healthy.
Runs lightweight read-only checks — safe to run at any time.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class HealthItem:
    name: str
    status: str          # "ok" | "warning" | "error" | "skipped"
    message: str
    detail: Optional[str] = None

    @property
    def icon(self) -> str:
        return {"ok": "✅", "warning": "⚠️", "error": "❌", "skipped": "⏭️"}.get(self.status, "❓")


@dataclass
class HealthReport:
    overall: str         # "ok" | "warning" | "error"
    checked_at: str
    items: List[HealthItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": self.overall,
            "checked_at": self.checked_at,
            "items": [
                {"name": i.name, "status": i.status, "message": i.message, "detail": i.detail}
                for i in self.items
            ],
        }

    def summary_lines(self) -> List[str]:
        return [f"{i.icon} **{i.name}**: {i.message}" for i in self.items]


class SearchHealthCheckService:
    """
    Runs a pre-demo health check against all provisioned Search assets.
    Reads elastic_assets.json for the list of resources to verify.
    """

    def __init__(self, es_client: Optional[Elasticsearch] = None):
        self.kibana_url = os.getenv("ELASTICSEARCH_KIBANA_URL", "").rstrip("/")
        self.api_key = os.getenv("ELASTICSEARCH_API_KEY", "")
        self.headers = {
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json",
        }

        if es_client:
            self.es = es_client
        else:
            cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
            if cloud_id:
                self.es = Elasticsearch(cloud_id=cloud_id, api_key=self.api_key)
            else:
                endpoint = os.getenv("ELASTIC_ENDPOINT", "")
                self.es = Elasticsearch(endpoint, api_key=api_key) if endpoint else None

    def run(self, module_path: str) -> HealthReport:
        """
        Load elastic_assets.json from module_path and run all health checks.
        Returns a HealthReport.
        """
        assets_path = Path(module_path) / "elastic_assets.json"
        if not assets_path.exists():
            return HealthReport(
                overall="error",
                checked_at=datetime.now(timezone.utc).isoformat(),
                items=[HealthItem("Assets manifest", "error", "elastic_assets.json not found — run provisioning first")],
            )

        assets = json.loads(assets_path.read_text())
        items: List[HealthItem] = []

        # 1. Indices
        for index_name in assets.get("indices", []):
            items.append(self._check_index(index_name))

        # 2. Ingest pipeline
        if pipeline := assets.get("ingest_pipeline"):
            items.append(self._check_pipeline(pipeline))

        # 3. ELSER model
        items.append(self._check_ml_model(".elser-2-elasticsearch", "ELSER model"))

        # 4. Search Application
        if app_name := assets.get("search_application"):
            items.append(self._check_search_application(app_name))

        # 5. Kibana dashboard
        for dash_id in assets.get("kibana_dashboard_ids", []):
            items.append(self._check_kibana_saved_object("dashboard", dash_id, "Dashboard"))

        # 6. Alert rules
        for rule_id in assets.get("alerting_rule_ids", []):
            items.append(self._check_alert_rule(rule_id))

        # 7. Slack connector
        if connector_id := assets.get("slack_connector_id"):
            items.append(self._check_slack_connector(connector_id))

        # 8. Scoped API key
        if key_info := assets.get("scoped_api_key"):
            items.append(self._check_api_key(key_info.get("id", "") if isinstance(key_info, dict) else ""))

        # Determine overall status
        statuses = [i.status for i in items]
        if "error" in statuses:
            overall = "error"
        elif "warning" in statuses:
            overall = "warning"
        else:
            overall = "ok"

        report = HealthReport(
            overall=overall,
            checked_at=datetime.now(timezone.utc).isoformat(),
            items=items,
        )

        # Persist result into assets file
        try:
            assets["health_check"] = report.to_dict()
            assets_path.write_text(json.dumps(assets, indent=2, default=str))
        except Exception:
            pass

        return report

    # -------------------------------------------------------------------------
    # Individual checks
    # -------------------------------------------------------------------------

    def _check_index(self, index_name: str) -> HealthItem:
        try:
            stats = self.es.indices.stats(index=index_name, metric="docs")
            count = stats["indices"][index_name]["primaries"]["docs"]["count"]
            if count == 0:
                return HealthItem(index_name, "warning", f"Index exists but has 0 documents")
            return HealthItem(index_name, "ok", f"{count:,} documents indexed")
        except Exception as e:
            return HealthItem(index_name, "error", "Index not found or inaccessible", str(e))

    def _check_pipeline(self, pipeline_name: str) -> HealthItem:
        try:
            self.es.ingest.get_pipeline(id=pipeline_name)
            return HealthItem(f"Pipeline: {pipeline_name}", "ok", "Pipeline exists")
        except Exception as e:
            return HealthItem(f"Pipeline: {pipeline_name}", "error", "Pipeline not found", str(e))

    def _check_ml_model(self, model_id: str, label: str) -> HealthItem:
        try:
            resp = self.es.ml.get_trained_models_stats(model_id=model_id)
            models = resp.get("trained_model_stats", [])
            if not models:
                return HealthItem(label, "error", f"Model {model_id} not found")
            state = models[0].get("deployment_stats", {}).get("state", "unknown")
            if state == "started":
                return HealthItem(label, "ok", f"Model deployed and started")
            return HealthItem(label, "warning", f"Model state: {state} (expected: started)")
        except Exception as e:
            return HealthItem(label, "error", "Could not check model", str(e))

    def _check_search_application(self, app_name: str) -> HealthItem:
        try:
            self.es.search_application.get(name=app_name)
            return HealthItem(f"Search App: {app_name}", "ok", "Search Application exists")
        except Exception as e:
            return HealthItem(f"Search App: {app_name}", "error", "Search Application not found", str(e))

    def _check_kibana_saved_object(self, so_type: str, so_id: str, label: str) -> HealthItem:
        if not self.kibana_url:
            return HealthItem(label, "skipped", "Kibana URL not configured")
        try:
            resp = requests.get(
                f"{self.kibana_url}/api/saved_objects/{so_type}/{so_id}",
                headers=self.headers,
                timeout=10,
            )
            if resp.status_code == 200:
                title = resp.json().get("attributes", {}).get("title", so_id)
                return HealthItem(f"{label}: {title}", "ok", "Exists in Kibana")
            return HealthItem(label, "warning", f"HTTP {resp.status_code}", resp.text[:100])
        except Exception as e:
            return HealthItem(label, "error", "Kibana unreachable", str(e))

    def _check_alert_rule(self, rule_id: str) -> HealthItem:
        if not self.kibana_url:
            return HealthItem("Alert rule", "skipped", "Kibana URL not configured")
        try:
            resp = requests.get(
                f"{self.kibana_url}/api/alerting/rule/{rule_id}",
                headers=self.headers,
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                name = data.get("name", rule_id)
                enabled = data.get("enabled", False)
                status = "ok" if enabled else "warning"
                msg = "Active" if enabled else "Disabled — enable in Kibana Alerts"
                return HealthItem(f"Alert: {name}", status, msg)
            return HealthItem("Alert rule", "warning", f"HTTP {resp.status_code}")
        except Exception as e:
            return HealthItem("Alert rule", "error", "Could not check rule", str(e))

    def _check_slack_connector(self, connector_id: str) -> HealthItem:
        if not self.kibana_url:
            return HealthItem("Slack connector", "skipped", "Kibana URL not configured")
        try:
            resp = requests.get(
                f"{self.kibana_url}/api/actions/connector/{connector_id}",
                headers=self.headers,
                timeout=10,
            )
            if resp.status_code == 200:
                return HealthItem("Slack connector", "ok", "Connector configured")
            return HealthItem("Slack connector", "warning", f"HTTP {resp.status_code}")
        except Exception as e:
            return HealthItem("Slack connector", "error", "Could not check connector", str(e))

    def _check_api_key(self, key_id: str) -> HealthItem:
        if not key_id:
            return HealthItem("Scoped API key", "skipped", "No key ID recorded")
        try:
            resp = self.es.security.get_api_key(id=key_id)
            keys = resp.get("api_keys", [])
            if keys and not keys[0].get("invalidated"):
                expiry = keys[0].get("expiration", "never")
                return HealthItem("Scoped API key", "ok", f"Valid — expires: {expiry}")
            return HealthItem("Scoped API key", "warning", "Key invalidated or expired")
        except Exception as e:
            return HealthItem("Scoped API key", "error", "Could not verify key", str(e))
