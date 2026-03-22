"""
Multi-Region Elastic Client

Single interface for querying one or many Elastic clusters across regions.
Supports:
  - Single-region queries (route by region name)
  - Fan-out queries (all regions, results merged with region tag)
  - Tenant-aware routing (tenant_id → region(s))
  - Connection testing per region

Used by:
  - Observability provisioner
  - MCP experience layer
  - POC script generator
  - Revenue Engine / Incident Command Center
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from elasticsearch import Elasticsearch, NotFoundError

from .region_config_service import RegionConfig, RegionConfigService

logger = logging.getLogger(__name__)


class RegionClient:
    """Wraps a single Elasticsearch client with its RegionConfig."""

    def __init__(self, config: RegionConfig):
        self.config = config
        self._es: Optional[Elasticsearch] = None

    @property
    def es(self) -> Elasticsearch:
        if self._es is None:
            self._es = self._build()
        return self._es

    def _build(self) -> Elasticsearch:
        url = self.config.es_url
        key = self.config.api_key
        kwargs: Dict[str, Any] = {
            "request_timeout": 30,
            "max_retries": 2,
            "retry_on_timeout": True,
        }
        if key:
            kwargs["api_key"] = key
        if url.startswith("cloud_id:"):
            return Elasticsearch(cloud_id=url.split("cloud_id:", 1)[1], **kwargs)
        return Elasticsearch(url, **kwargs)

    def ping(self) -> Tuple[bool, str]:
        """Test connection. Returns (success, message)."""
        try:
            info = self.es.info()
            version = info.get("version", {}).get("number", "?")
            return True, f"✅ Connected · ES {version} · {self.config.es_url}"
        except Exception as exc:
            return False, f"❌ {exc}"

    def esql(self, query: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Run an ES|QL query and return the raw response."""
        body: Dict[str, Any] = {"query": query}
        if params:
            body["params"] = params
        return self.es.perform_request(
            "POST",
            "/_query",
            body=body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        ).body

    def index_exists(self, index: str) -> bool:
        try:
            return self.es.indices.exists(index=index).body
        except Exception:
            return False


class MultiRegionElasticClient:
    """
    Facade over multiple RegionClient instances.

    Typical usage
    -------------
    client = MultiRegionElasticClient.from_config()

    # Query one region
    result = client.esql("us-east-1", "FROM logs-* | LIMIT 10")

    # Fan-out to all regions
    results = client.fan_out_esql("FROM logs-* | STATS count = COUNT(*)")
    # → {"us-east-1": {...}, "eu-west-1": {...}}

    # Direct ES client for a region
    es = client.get_es("eu-west-1")
    """

    def __init__(self, region_clients: List[RegionClient]):
        self._clients: Dict[str, RegionClient] = {
            rc.config.name.lower(): rc for rc in region_clients
        }
        # also index by region_code for convenience
        for rc in region_clients:
            self._clients[rc.config.region_code.lower()] = rc

    # ── factory ───────────────────────────────────────────────────────────────

    @classmethod
    def from_config(cls, service: Optional[RegionConfigService] = None) -> "MultiRegionElasticClient":
        """Build from RegionConfigService (loads regions.json + env vars)."""
        svc = service or RegionConfigService()
        configs = svc.load_all()
        if not configs:
            raise RuntimeError(
                "No Elastic regions configured. "
                "Add regions via Settings → Multi-Region, or set ES_URL / ES_API_KEY in .env"
            )
        clients = [RegionClient(cfg) for cfg in configs if cfg.is_configured()]
        if not clients:
            raise RuntimeError("No fully-configured regions found (need es_url + api_key).")
        return cls(clients)

    @classmethod
    def from_configs(cls, configs: List[RegionConfig]) -> "MultiRegionElasticClient":
        """Build directly from a list of RegionConfig objects."""
        clients = [RegionClient(cfg) for cfg in configs if cfg.is_configured()]
        return cls(clients)

    # ── region resolution ─────────────────────────────────────────────────────

    def regions(self) -> List[RegionConfig]:
        """Return unique RegionConfig objects (deduplicated)."""
        seen, out = set(), []
        for rc in self._clients.values():
            if rc.config.name not in seen:
                seen.add(rc.config.name)
                out.append(rc.config)
        return out

    def get_client(self, region: str) -> RegionClient:
        """Get a RegionClient by name or region_code (case-insensitive)."""
        key = region.lower()
        if key not in self._clients:
            available = list({rc.config.name for rc in self._clients.values()})
            raise KeyError(f"Region '{region}' not found. Available: {available}")
        return self._clients[key]

    def get_es(self, region: str) -> Elasticsearch:
        """Get the raw Elasticsearch client for a region."""
        return self.get_client(region).es

    def primary(self) -> RegionClient:
        """Return the primary region client."""
        for rc in self._clients.values():
            if rc.config.is_primary:
                return rc
        return next(iter(self._clients.values()))

    # ── query methods ─────────────────────────────────────────────────────────

    def esql(self, region: str, query: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Run ES|QL against a specific region."""
        return self.get_client(region).esql(query, params)

    def fan_out_esql(
        self,
        query: str,
        regions: Optional[List[str]] = None,
        params: Optional[Dict] = None,
        max_workers: int = 4,
    ) -> Dict[str, Any]:
        """
        Execute ES|QL across all (or specified) regions in parallel.

        Returns:
            {
                "us-east-1": {"columns": [...], "values": [...], "error": None},
                "eu-west-1": {"columns": [...], "values": [...], "error": None},
            }
        """
        target_regions = regions or list({rc.config.name for rc in self._clients.values()})
        results: Dict[str, Any] = {}

        def _query_one(name: str) -> Tuple[str, Any]:
            try:
                rc = self.get_client(name)
                return rc.config.name, rc.esql(query, params)
            except Exception as exc:
                return name, {"error": str(exc), "columns": [], "values": []}

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(_query_one, name): name for name in target_regions}
            for future in as_completed(futures):
                name, result = future.result()
                results[name] = result

        return results

    def fan_out_search(
        self,
        index: str,
        body: Dict[str, Any],
        regions: Optional[List[str]] = None,
        max_workers: int = 4,
    ) -> Dict[str, Any]:
        """
        Execute a DSL search across all (or specified) regions in parallel.
        Returns {region_name: search_response}.
        """
        target_regions = regions or list({rc.config.name for rc in self._clients.values()})
        results: Dict[str, Any] = {}

        def _search_one(name: str) -> Tuple[str, Any]:
            try:
                rc = self.get_client(name)
                resp = rc.es.search(index=index, body=body)
                return rc.config.name, resp.body
            except Exception as exc:
                return name, {"error": str(exc), "hits": {"hits": [], "total": {"value": 0}}}

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(_search_one, name): name for name in target_regions}
            for future in as_completed(futures):
                name, result = future.result()
                results[name] = result

        return results

    # ── health & testing ──────────────────────────────────────────────────────

    def ping_all(self) -> Dict[str, Tuple[bool, str]]:
        """
        Test all region connections in parallel.
        Returns {region_name: (success, message)}.
        """
        results: Dict[str, Tuple[bool, str]] = {}

        def _ping(rc: RegionClient) -> Tuple[str, bool, str]:
            ok, msg = rc.ping()
            return rc.config.name, ok, msg

        seen_names = set()
        unique_clients = []
        for rc in self._clients.values():
            if rc.config.name not in seen_names:
                seen_names.add(rc.config.name)
                unique_clients.append(rc)

        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [pool.submit(_ping, rc) for rc in unique_clients]
            for f in as_completed(futures):
                name, ok, msg = f.result()
                results[name] = (ok, msg)

        return results

    def index_exists(self, region: str, index: str) -> bool:
        return self.get_client(region).index_exists(index)
