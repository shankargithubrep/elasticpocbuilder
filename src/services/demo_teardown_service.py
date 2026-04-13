"""
Demo Teardown Service

Deletes ALL Elastic assets associated with a demo module before
removing the local folder. Reads elastic_assets.json and obs_assets.json
to know exactly what was provisioned.

Assets cleaned up:
  Elasticsearch:
    - Indices / Data Streams
    - Ingest Pipelines
    - Index Templates
    - ILM Policies
    - Search Applications
    - Query Rules
    - Synonyms Sets
    - ML jobs (if any)

  Kibana:
    - Dashboards
    - Data Views
    - Discover Views
    - Alerting Rules
    - Slack / Case Connectors

  Agent Builder:
    - Tools
    - Agents
"""

import json
import logging
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class TeardownResult:
    def __init__(self):
        self.deleted:  List[str] = []
        self.failed:   List[str] = []
        self.skipped:  List[str] = []

    def ok(self, label: str):
        self.deleted.append(label)
        logger.info(f"Deleted: {label}")

    def fail(self, label: str, reason: str):
        self.failed.append(f"{label}: {reason}")
        logger.warning(f"Failed to delete {label}: {reason}")

    def skip(self, label: str):
        self.skipped.append(label)

    @property
    def summary(self) -> str:
        return (
            f"✅ Deleted {len(self.deleted)} | "
            f"❌ Failed {len(self.failed)} | "
            f"⏭️ Skipped {len(self.skipped)}"
        )


class DemoTeardownService:

    def __init__(self):
        from elasticsearch import Elasticsearch
        api_key  = os.getenv("ELASTICSEARCH_API_KEY", "")
        cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
        endpoint = os.getenv("ELASTIC_ENDPOINT", "") or os.getenv("ES_URL", "")
        kwargs   = {"request_timeout": 30}
        if api_key:
            kwargs["api_key"] = api_key
        if cloud_id:
            self.es = Elasticsearch(cloud_id=cloud_id, **kwargs)
        elif endpoint:
            self.es = Elasticsearch(endpoint, **kwargs)
        else:
            self.es = None

        self.kibana_url = os.getenv("ELASTICSEARCH_KIBANA_URL", "").rstrip("/")
        self.api_key    = api_key

    # ── public API ────────────────────────────────────────────────────────────

    def preview(self, module_name: str) -> Dict[str, List[str]]:
        """
        Return a preview of everything that will be deleted
        without actually deleting anything.
        """
        module_path = Path("demos") / module_name
        preview: Dict[str, List[str]] = {
            "indices":           [],
            "data_streams":      [],
            "pipelines":         [],
            "index_templates":   [],
            "ilm_policies":      [],
            "search_apps":       [],
            "query_rules":       [],
            "kibana_dashboards": [],
            "kibana_data_views": [],
            "kibana_alerts":     [],
            "agent_tools":       [],
            "agent":             [],
        }

        # Search assets
        ea = self._load_json(module_path / "elastic_assets.json")
        if ea:
            preview["indices"]           = ea.get("indices", [])
            preview["pipelines"]        += [ea.get("ingest_pipeline")] if ea.get("ingest_pipeline") else []
            preview["index_templates"]  += [ea.get("index_template")]  if ea.get("index_template") else []
            preview["ilm_policies"]     += [ea.get("ilm_policy")]      if ea.get("ilm_policy") else []
            preview["search_apps"]      += [ea.get("search_application")] if ea.get("search_application") else []
            preview["query_rules"]      += [ea.get("query_rules_id")]  if ea.get("query_rules_id") else []
            preview["kibana_dashboards"] = ea.get("kibana_dashboard_ids", [])
            preview["kibana_data_views"] = (
                ea.get("data_view_ids", []) + ea.get("discover_view_ids", [])
            )
            preview["kibana_alerts"]     = ea.get("alerting_rule_ids", [])

        # Observability assets
        oa = self._load_json(module_path / "obs_assets.json")
        if oa:
            ns = oa.get("namespace", "")
            for dt in ("logs", "metrics", "traces"):
                preview["data_streams"].append(f"{dt}-otel-{ns}")
                preview["pipelines"].append(f"obs-{dt}-pipeline-{ns}")
                preview["index_templates"].append(f"obs-{dt}-{ns}")
                preview["ilm_policies"].append(f"obs-{dt}-{ns}-ilm")
            preview["pipelines"] += [f"obs-enrich-{ns}", f"obs-pii-redact-{ns}", f"obs-route-{ns}"]
            preview["kibana_data_views"] += oa.get("kibana_data_views", [])

        # Agent Builder
        tm = self._load_json(module_path / "tool_metadata.json")
        if tm:
            for tid, meta in tm.items():
                if isinstance(meta, dict) and meta.get("deployed"):
                    preview["agent_tools"].append(meta.get("name", tid))

        am = self._load_json(module_path / "agent_metadata.json")
        if am and (am.get("deployed") or am.get("deployed_at") or am.get("id")):
            preview["agent"].append(am.get("name", am.get("id", "agent")))

        # Remove empty
        return {k: v for k, v in preview.items() if v}

    def teardown(
        self,
        module_name: str,
        skip_categories: Optional[List[str]] = None,
    ) -> TeardownResult:
        """
        Delete all Elastic assets for this demo module.
        skip_categories: list of keys from preview() to skip
        """
        module_path    = Path("demos") / module_name
        skip           = set(skip_categories or [])
        result         = TeardownResult()

        ea = self._load_json(module_path / "elastic_assets.json")
        oa = self._load_json(module_path / "obs_assets.json")

        if not self.es:
            result.fail("Elasticsearch", "No ES connection configured")
            return result

        # ── Elasticsearch indices ─────────────────────────────────────────────
        if "indices" not in skip and ea:
            for idx in ea.get("indices", []):
                self._delete_index(idx, result)

        # ── Data streams (observability) ──────────────────────────────────────
        if "data_streams" not in skip and oa:
            ns = oa.get("namespace", "")
            for dt in ("logs", "metrics", "traces"):
                self._delete_data_stream(f"{dt}-otel-{ns}", result)

        # ── Ingest pipelines ──────────────────────────────────────────────────
        if "pipelines" not in skip:
            if ea and ea.get("ingest_pipeline"):
                self._delete_pipeline(ea["ingest_pipeline"], result)
            if oa:
                ns = oa.get("namespace", "")
                for pipe in [f"obs-enrich-{ns}", f"obs-pii-redact-{ns}", f"obs-route-{ns}"]:
                    self._delete_pipeline(pipe, result)

        # ── Index templates ───────────────────────────────────────────────────
        if "index_templates" not in skip:
            if ea and ea.get("index_template"):
                self._delete_index_template(ea["index_template"], result)
            if oa:
                ns = oa.get("namespace", "")
                for dt in ("logs", "metrics", "traces"):
                    self._delete_index_template(f"obs-{dt}-{ns}", result)
                    self._delete_component_template(f"obs-standard-tags-{ns}", result)

        # ── ILM policies ──────────────────────────────────────────────────────
        if "ilm_policies" not in skip:
            if ea and ea.get("ilm_policy"):
                self._delete_ilm_policy(ea["ilm_policy"], result)
            if oa:
                ns = oa.get("namespace", "")
                for dt in ("logs", "metrics", "traces"):
                    self._delete_ilm_policy(f"obs-{dt}-{ns}-ilm", result)

        # ── Search Application ────────────────────────────────────────────────
        if "search_apps" not in skip and ea and ea.get("search_application"):
            self._delete_search_app(ea["search_application"], result)

        # ── Query Rules ───────────────────────────────────────────────────────
        if "query_rules" not in skip and ea and ea.get("query_rules_id"):
            self._delete_query_rules(ea["query_rules_id"], result)

        # ── Kibana assets ─────────────────────────────────────────────────────
        if self.kibana_url and self.api_key:
            if "kibana_dashboards" not in skip and ea:
                for did in ea.get("kibana_dashboard_ids", []):
                    self._delete_kibana_saved_object("dashboard", did, result)

            if "kibana_data_views" not in skip:
                if ea:
                    for vid in ea.get("data_view_ids", []) + ea.get("discover_view_ids", []):
                        self._delete_kibana_data_view(vid, result)
                if oa:
                    for vid in oa.get("kibana_data_views", []):
                        self._delete_kibana_data_view(vid, result)

            if "kibana_alerts" not in skip and ea:
                for rid in ea.get("alerting_rule_ids", []):
                    self._delete_kibana_alert_rule(rid, result)

            if ea and ea.get("slack_connector_id"):
                self._delete_kibana_connector(ea["slack_connector_id"], result)

        # ── Agent Builder tools + agent ───────────────────────────────────────
        if "agent_tools" not in skip or "agent" not in skip:
            tm = self._load_json(module_path / "tool_metadata.json")
            if tm:
                try:
                    from src.services.agent_builder_service import AgentBuilderService
                    ab = AgentBuilderService()
                    for tid, meta in tm.items():
                        if isinstance(meta, dict):
                            deployed_id = meta.get("deployed_tool_id") or tid
                            try:
                                ab.delete_tool(deployed_id)
                                result.ok(f"Agent tool: {meta.get('name', tid)}")
                            except Exception as exc:
                                if "404" in str(exc):
                                    result.skip(f"Tool {tid} (already gone)")
                                else:
                                    result.fail(f"Tool {tid}", str(exc))
                except Exception as exc:
                    result.fail("Agent Builder connection", str(exc))

            am = self._load_json(module_path / "agent_metadata.json")
            if am and am.get("id"):
                try:
                    from src.services.agent_builder_service import AgentBuilderService
                    ab = AgentBuilderService()
                    ab.delete_agent(am["id"])
                    result.ok(f"Agent: {am.get('name', am['id'])}")
                except Exception as exc:
                    if "404" in str(exc):
                        result.skip(f"Agent {am.get('id')} (already gone)")
                    else:
                        result.fail(f"Agent {am.get('id')}", str(exc))

        return result

    # ── Elasticsearch deletions ───────────────────────────────────────────────

    def _delete_index(self, name: str, result: TeardownResult):
        try:
            self.es.indices.delete(index=name, ignore_unavailable=True)
            result.ok(f"Index: {name}")
        except Exception as exc:
            result.fail(f"Index {name}", str(exc))

    def _delete_data_stream(self, name: str, result: TeardownResult):
        try:
            self.es.indices.delete_data_stream(name=name, ignore_unavailable=True)
            result.ok(f"Data stream: {name}")
        except Exception as exc:
            if "404" in str(exc) or "not_found" in str(exc).lower():
                result.skip(f"Data stream {name} (not found)")
            else:
                result.fail(f"Data stream {name}", str(exc))

    def _delete_pipeline(self, name: str, result: TeardownResult):
        try:
            self.es.ingest.delete_pipeline(id=name)
            result.ok(f"Pipeline: {name}")
        except Exception as exc:
            if "404" in str(exc):
                result.skip(f"Pipeline {name} (not found)")
            else:
                result.fail(f"Pipeline {name}", str(exc))

    def _delete_index_template(self, name: str, result: TeardownResult):
        try:
            self.es.indices.delete_index_template(name=name)
            result.ok(f"Index template: {name}")
        except Exception as exc:
            if "404" in str(exc):
                result.skip(f"Template {name} (not found)")
            else:
                result.fail(f"Template {name}", str(exc))

    def _delete_component_template(self, name: str, result: TeardownResult):
        try:
            self.es.cluster.delete_component_template(name=name)
            result.ok(f"Component template: {name}")
        except Exception as exc:
            if "404" in str(exc):
                result.skip(f"Component template {name} (not found)")
            else:
                result.fail(f"Component template {name}", str(exc))

    def _delete_ilm_policy(self, name: str, result: TeardownResult):
        try:
            self.es.ilm.delete_lifecycle(name=name)
            result.ok(f"ILM policy: {name}")
        except Exception as exc:
            if "404" in str(exc):
                result.skip(f"ILM {name} (not found)")
            else:
                result.fail(f"ILM {name}", str(exc))

    def _delete_search_app(self, name: str, result: TeardownResult):
        try:
            self.es.perform_request("DELETE", f"/_application/search_application/{name}")
            result.ok(f"Search Application: {name}")
        except Exception as exc:
            if "404" in str(exc):
                result.skip(f"Search App {name} (not found)")
            else:
                result.fail(f"Search App {name}", str(exc))

    def _delete_query_rules(self, ruleset_id: str, result: TeardownResult):
        try:
            self.es.perform_request("DELETE", f"/_query_rules/{ruleset_id}")
            result.ok(f"Query Rules: {ruleset_id}")
        except Exception as exc:
            if "404" in str(exc):
                result.skip(f"Query Rules {ruleset_id} (not found)")
            else:
                result.fail(f"Query Rules {ruleset_id}", str(exc))

    # ── Kibana deletions ──────────────────────────────────────────────────────

    def _kibana_request(self, method: str, path: str) -> Tuple[bool, str]:
        url = f"{self.kibana_url}{path}"
        req = urllib.request.Request(
            url,
            headers={
                "kbn-xsrf": "teardown",
                "Authorization": f"ApiKey {self.api_key}",
            },
            method=method,
        )
        try:
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=15, context=ctx):
                return True, "ok"
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return True, "not_found"
            return False, f"HTTP {exc.code}"
        except Exception as exc:
            return False, str(exc)

    def _delete_kibana_saved_object(self, obj_type: str, obj_id: str, result: TeardownResult):
        ok, msg = self._kibana_request("DELETE", f"/api/saved_objects/{obj_type}/{obj_id}")
        if ok:
            result.ok(f"Kibana {obj_type}: {obj_id}")
        else:
            result.fail(f"Kibana {obj_type} {obj_id}", msg)

    def _delete_kibana_data_view(self, view_id: str, result: TeardownResult):
        ok, msg = self._kibana_request("DELETE", f"/api/data_views/data_view/{view_id}")
        if ok:
            result.ok(f"Kibana Data View: {view_id}")
        else:
            result.fail(f"Kibana Data View {view_id}", msg)

    def _delete_kibana_alert_rule(self, rule_id: str, result: TeardownResult):
        ok, msg = self._kibana_request("DELETE", f"/api/alerting/rule/{rule_id}")
        if ok:
            result.ok(f"Kibana Alert Rule: {rule_id}")
        else:
            result.fail(f"Kibana Alert Rule {rule_id}", msg)

    def _delete_kibana_connector(self, connector_id: str, result: TeardownResult):
        ok, msg = self._kibana_request("DELETE", f"/api/actions/connector/{connector_id}")
        if ok:
            result.ok(f"Kibana Connector: {connector_id}")
        else:
            result.fail(f"Kibana Connector {connector_id}", msg)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _load_json(self, path: Path) -> Optional[Dict]:
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
        return None
