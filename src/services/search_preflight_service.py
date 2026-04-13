"""
Search Preflight Service

Verifies all required ML models, Kibana connectivity, and credentials
before any Search stack provisioning begins. Returns a structured report.
"""

import os
import logging
import requests
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class PreflightCheck:
    name: str
    passed: bool
    message: str
    detail: Optional[str] = None


@dataclass
class PreflightReport:
    passed: bool
    checks: Dict[str, PreflightCheck] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": {
                k: {"passed": v.passed, "message": v.message, "detail": v.detail}
                for k, v in self.checks.items()
            }
        }

    def summary(self) -> str:
        failed = [c for c in self.checks.values() if not c.passed]
        if not failed:
            return "All preflight checks passed."
        return "Failed: " + ", ".join(c.name for c in failed)


class SearchPreflightService:
    """
    Runs pre-flight checks before Search stack provisioning.
    All checks are non-destructive reads only.
    """

    ELSER_MODEL_ID = ".elser-2-elasticsearch"
    E5_MODEL_ID = ".multilingual-e5-small"
    JINA_ENDPOINT_ID = ".jina-embeddings-v5-text-small"  # EIS built-in endpoint
    JINA_RERANKER_ID = ".jina-reranker-v3"  # EIS built-in reranker (no ML nodes needed)

    def __init__(self, es_client: Optional[Elasticsearch] = None):
        self.kibana_url = os.getenv("ELASTICSEARCH_KIBANA_URL", "").rstrip("/")
        self.api_key = os.getenv("ELASTICSEARCH_API_KEY", "")
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL", "")
        self.headers = {
            "Authorization": f"ApiKey {self.api_key}",
            "Content-Type": "application/json",
            "kbn-xsrf": "true",
        }

        if es_client:
            self.es = es_client
        else:
            cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
            if cloud_id:
                self.es = Elasticsearch(cloud_id=cloud_id, api_key=self.api_key)
            else:
                endpoint = os.getenv("ELASTIC_ENDPOINT", "")
                self.es = Elasticsearch(endpoint, api_key=self.api_key)

    def run_all(self, embedding_model: str = "jina") -> PreflightReport:
        """
        Run all preflight checks and return a consolidated report.
        embedding_model: 'elser' (default) or 'e5' — determines which ML model is checked.
        """
        checks: Dict[str, PreflightCheck] = {}

        checks["elasticsearch"] = self._check_elasticsearch()
        checks["kibana"] = self._check_kibana()

        if embedding_model == "e5":
            checks["e5"] = self._check_ml_model(self.E5_MODEL_ID, "E5 Multilingual")
        elif embedding_model == "jina":
            checks["jina"] = self._check_jina_endpoint()
        else:
            checks["elser"] = self._check_ml_model(self.ELSER_MODEL_ID, "ELSER")

        checks["rerank"] = self._check_jina_reranker_endpoint()
        checks["slack"] = self._check_slack()

        all_passed = all(c.passed for c in checks.values())
        report = PreflightReport(passed=all_passed, checks=checks)
        logger.info(f"Preflight [{embedding_model}]: {report.summary()}")
        return report

    def _check_elasticsearch(self) -> PreflightCheck:
        try:
            info = self.es.info()
            version = info.get("version", {}).get("number", "unknown")
            return PreflightCheck(
                name="Elasticsearch",
                passed=True,
                message=f"Connected — version {version}",
            )
        except Exception as e:
            return PreflightCheck(
                name="Elasticsearch",
                passed=False,
                message="Connection failed",
                detail=str(e),
            )

    def _check_kibana(self) -> PreflightCheck:
        if not self.kibana_url:
            return PreflightCheck(
                name="Kibana",
                passed=False,
                message="ELASTICSEARCH_KIBANA_URL not set",
            )
        try:
            resp = requests.get(
                f"{self.kibana_url}/api/status",
                headers=self.headers,
                timeout=15,
            )
            if resp.status_code == 200:
                state = resp.json().get("status", {}).get("overall", {}).get("level", "unknown")
                return PreflightCheck(
                    name="Kibana",
                    passed=True,
                    message=f"Reachable — status: {state}",
                )
            return PreflightCheck(
                name="Kibana",
                passed=False,
                message=f"HTTP {resp.status_code}",
                detail=resp.text[:200],
            )
        except Exception as e:
            return PreflightCheck(
                name="Kibana",
                passed=False,
                message="Connection failed",
                detail=str(e),
            )

    def _check_ml_model(self, model_id: str, label: str) -> PreflightCheck:
        try:
            resp = self.es.ml.get_trained_models_stats(model_id=model_id)
            models = resp.get("trained_model_stats", [])
            if not models:
                return PreflightCheck(
                    name=label,
                    passed=False,
                    message=f"{label} model not found",
                    detail=f"Model ID: {model_id}",
                )
            deployment = models[0].get("deployment_stats", {})
            state = deployment.get("state", "not_deployed")
            if state == "started":
                nodes = len(deployment.get("nodes", []))
                return PreflightCheck(
                    name=label,
                    passed=True,
                    message=f"Started on {nodes} node(s)",
                )
            return PreflightCheck(
                name=label,
                passed=False,
                message=f"Model state: {state} (expected: started)",
                detail=f"Model ID: {model_id}",
            )
        except Exception as e:
            return PreflightCheck(
                name=label,
                passed=False,
                message=f"Could not check {label} model",
                detail=str(e),
            )

    def _check_jina_reranker_endpoint(self) -> PreflightCheck:
        """
        Check if the Jina Reranker v3 EIS endpoint is available.

        Jina Reranker v3 runs on EIS — no ML nodes needed.
        Listwise reranker that processes 64 docs simultaneously.
        """
        try:
            self.es.inference.get(inference_id=self.JINA_RERANKER_ID)
            return PreflightCheck(
                name="Jina Reranker EIS",
                passed=True,
                message=f"Jina Reranker v3 endpoint '{self.JINA_RERANKER_ID}' ready (no ML nodes needed)",
            )
        except Exception as e:
            err = str(e).lower()
            if "resource_not_found" in err or "404" in err:
                return PreflightCheck(
                    name="Jina Reranker EIS",
                    passed=False,
                    message=(
                        "Jina Reranker v3 EIS endpoint not available. "
                        "On Elastic Cloud this should be auto-available. "
                        "Self-managed: enable Cloud Connect in Kibana > Stack Management."
                    ),
                    detail=str(e),
                )
            return PreflightCheck(
                name="Jina Reranker EIS",
                passed=False,
                message="Could not check Jina Reranker v3 endpoint",
                detail=str(e),
            )

    def _check_jina_endpoint(self) -> PreflightCheck:
        """
        Check if the Jina EIS inference endpoint is available.

        Jina models run on Elastic Inference Service (EIS) — no API key or ML nodes needed.
        Available on Elastic Cloud by default. Self-managed requires ES 9.3+ Enterprise
        with Cloud Connect enabled in Kibana > Stack Management > Cloud Connect.
        """
        try:
            self.es.inference.get(inference_id=self.JINA_ENDPOINT_ID)
            return PreflightCheck(
                name="Jina EIS",
                passed=True,
                message=f"Jina EIS endpoint '{self.JINA_ENDPOINT_ID}' ready (no ML nodes needed)",
            )
        except Exception as e:
            err = str(e).lower()
            if "resource_not_found" in err or "404" in err:
                return PreflightCheck(
                    name="Jina EIS",
                    passed=False,
                    message=(
                        "Jina EIS endpoint not available. "
                        "On Elastic Cloud this should be auto-available. "
                        "Self-managed: enable Cloud Connect in Kibana > Stack Management."
                    ),
                    detail=str(e),
                )
            return PreflightCheck(
                name="Jina EIS",
                passed=False,
                message="Could not check Jina EIS endpoint",
                detail=str(e),
            )

    def _check_slack(self) -> PreflightCheck:
        if not self.slack_webhook:
            return PreflightCheck(
                name="Slack",
                passed=False,
                message="SLACK_WEBHOOK_URL not configured — Slack alerts disabled",
            )
        try:
            resp = requests.post(
                self.slack_webhook,
                json={"text": "🔍 Elastic Demo Builder preflight check — ignore this message."},
                timeout=10,
            )
            if resp.status_code == 200 and resp.text == "ok":
                return PreflightCheck(
                    name="Slack",
                    passed=True,
                    message="Webhook reachable",
                )
            return PreflightCheck(
                name="Slack",
                passed=False,
                message=f"Webhook returned HTTP {resp.status_code}",
                detail=resp.text[:200],
            )
        except Exception as e:
            return PreflightCheck(
                name="Slack",
                passed=False,
                message="Webhook unreachable",
                detail=str(e),
            )
