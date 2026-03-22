"""
Region Config Service

Manages multi-region Elastic cluster configurations for data residency scenarios.
Supports loading from:
  1. regions.json  — UI-configured regions (persisted across sessions)
  2. Environment variables — ES_URL_<REGION>, ES_API_KEY_<REGION>
  3. Legacy single-region — ELASTIC_ENDPOINT / ELASTICSEARCH_API_KEY (always included)

Storage: regions.json in project root (git-ignored, like .env)
"""

import json
import logging
import os
import re
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_REGIONS_FILE = Path("regions.json")

# Well-known region display metadata
REGION_META = {
    "us-east-1":      {"label": "US East (N. Virginia)",    "cloud": "AWS", "flag": "🇺🇸"},
    "us-west-2":      {"label": "US West (Oregon)",          "cloud": "AWS", "flag": "🇺🇸"},
    "eu-west-1":      {"label": "EU West (Ireland)",         "cloud": "AWS", "flag": "🇪🇺"},
    "eu-central-1":   {"label": "EU Central (Frankfurt)",    "cloud": "AWS", "flag": "🇩🇪"},
    "ap-southeast-1": {"label": "Asia Pacific (Singapore)",  "cloud": "AWS", "flag": "🇸🇬"},
    "ap-northeast-1": {"label": "Asia Pacific (Tokyo)",      "cloud": "AWS", "flag": "🇯🇵"},
    "ap-southeast-2": {"label": "Asia Pacific (Sydney)",     "cloud": "AWS", "flag": "🇦🇺"},
    "me-south-1":     {"label": "Middle East (Bahrain)",     "cloud": "AWS", "flag": "🇧🇭"},
    "sa-east-1":      {"label": "South America (São Paulo)", "cloud": "AWS", "flag": "🇧🇷"},
    "us-central1":    {"label": "US Central (Iowa)",         "cloud": "GCP", "flag": "🇺🇸"},
    "europe-west1":   {"label": "EU West (Belgium)",         "cloud": "GCP", "flag": "🇧🇪"},
    "eastus":         {"label": "East US (Virginia)",        "cloud": "Azure","flag": "🇺🇸"},
    "westeurope":     {"label": "West Europe (Netherlands)", "cloud": "Azure","flag": "🇳🇱"},
}


@dataclass
class RegionConfig:
    """Single Elastic cluster configuration for one region."""
    name: str                    # e.g. "US-East-1"
    region_code: str             # e.g. "us-east-1"
    es_url: str                  # https://xxx.es.io:9243
    api_key: str                 # Elastic API key
    kibana_url: str = ""         # https://xxx.kb.io:5601
    is_primary: bool = False     # primary region for single-region queries
    tenant_id: str = ""          # default tenant_id tag for generated data
    notes: str = ""              # free-text notes

    @property
    def flag(self) -> str:
        return REGION_META.get(self.region_code, {}).get("flag", "🌐")

    @property
    def cloud_label(self) -> str:
        meta = REGION_META.get(self.region_code, {})
        cloud = meta.get("cloud", "")
        label = meta.get("label", self.region_code)
        return f"{cloud} · {label}" if cloud else label

    @property
    def display_name(self) -> str:
        return f"{self.flag} {self.name}"

    def is_configured(self) -> bool:
        return bool(self.es_url and self.api_key)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d.pop("api_key", None)   # never serialise secrets to disk
        return d


class RegionConfigService:
    """Load, save, and manage multi-region Elastic configurations."""

    # ── public API ────────────────────────────────────────────────────────────

    def load_all(self) -> List[RegionConfig]:
        """
        Return all configured regions, merging:
          1. regions.json (UI-saved, no secrets)
          2. Env vars for secrets + any env-only regions
          3. Legacy single-region env vars as a fallback primary
        """
        file_regions = self._load_from_file()
        env_regions  = self._load_from_env()

        # Merge: file entries are the source of truth for metadata;
        # env vars supply / override secrets
        merged: Dict[str, RegionConfig] = {}

        for r in file_regions:
            merged[r.name.upper()] = r

        for r in env_regions:
            key = r.name.upper()
            if key in merged:
                # Patch secrets from env into file entry
                existing = merged[key]
                if r.api_key:
                    existing.api_key = r.api_key
                if r.es_url and not existing.es_url:
                    existing.es_url = r.es_url
                if r.kibana_url and not existing.kibana_url:
                    existing.kibana_url = r.kibana_url
            else:
                merged[key] = r

        # Ensure at least the legacy primary is present
        legacy = self._legacy_primary()
        if legacy and "PRIMARY" not in merged and not merged:
            merged["PRIMARY"] = legacy

        result = list(merged.values())

        # Sort: primary first, then alphabetical
        result.sort(key=lambda r: (not r.is_primary, r.name))
        return result

    def save(self, regions: List[RegionConfig]):
        """Persist region metadata (no secrets) to regions.json."""
        data = [r.to_dict() for r in regions]
        try:
            _REGIONS_FILE.write_text(
                json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            logger.info(f"Saved {len(data)} region(s) to {_REGIONS_FILE}")
        except Exception as e:
            logger.error(f"Could not save regions: {e}")

    def upsert(self, region: RegionConfig):
        """Add or update a single region and persist."""
        regions = self.load_all()
        idx = next((i for i, r in enumerate(regions) if r.name.upper() == region.name.upper()), None)
        if idx is not None:
            regions[idx] = region
        else:
            regions.append(region)
        self.save(regions)

    def delete(self, name: str):
        """Remove a region by name and persist."""
        regions = [r for r in self.load_all() if r.name.upper() != name.upper()]
        self.save(regions)

    def get_primary(self) -> Optional[RegionConfig]:
        regions = self.load_all()
        primary = next((r for r in regions if r.is_primary), None)
        return primary or (regions[0] if regions else None)

    def get_env_template(self, regions: List[RegionConfig]) -> str:
        """Generate .env snippet for all configured regions."""
        lines = ["# Multi-Region Elastic Configuration", "# Add to your .env file\n"]
        for r in regions:
            tag = re.sub(r"[^A-Z0-9]", "_", r.name.upper())
            lines.append(f"# {r.display_name} — {r.cloud_label}")
            lines.append(f"ES_URL_{tag}={r.es_url}")
            lines.append(f"ES_API_KEY_{tag}=<your-api-key>")
            if r.kibana_url:
                lines.append(f"KIBANA_URL_{tag}={r.kibana_url}")
            lines.append("")
        return "\n".join(lines)

    # ── private ───────────────────────────────────────────────────────────────

    def _load_from_file(self) -> List[RegionConfig]:
        if not _REGIONS_FILE.exists():
            return []
        try:
            data = json.loads(_REGIONS_FILE.read_text(encoding="utf-8"))
            return [RegionConfig(**{k: v for k, v in d.items() if k in RegionConfig.__dataclass_fields__})
                    for d in data]
        except Exception as e:
            logger.warning(f"Could not load regions.json: {e}")
            return []

    def _load_from_env(self) -> List[RegionConfig]:
        """
        Detect env vars matching:
          ES_URL_<TAG>       → es_url
          ES_API_KEY_<TAG>   → api_key
          KIBANA_URL_<TAG>   → kibana_url (optional)
        """
        pattern = re.compile(r"^ES_URL_(.+)$")
        regions = []
        for key, val in os.environ.items():
            m = pattern.match(key)
            if not m:
                continue
            tag = m.group(1)                              # e.g. "US_EAST_1"
            name = tag.replace("_", "-").title()          # "Us-East-1" → cleaned below
            region_code = tag.lower().replace("_", "-")  # "us-east-1"
            api_key = os.getenv(f"ES_API_KEY_{tag}", "")
            kibana  = os.getenv(f"KIBANA_URL_{tag}", "")
            regions.append(RegionConfig(
                name=name,
                region_code=region_code,
                es_url=val,
                api_key=api_key,
                kibana_url=kibana,
                is_primary=(len(regions) == 0),
            ))
        return regions

    def _legacy_primary(self) -> Optional[RegionConfig]:
        """Build a RegionConfig from the original single-region env vars."""
        es_url  = os.getenv("ELASTIC_ENDPOINT") or os.getenv("ES_URL", "")
        api_key = os.getenv("ELASTICSEARCH_API_KEY") or os.getenv("ES_API_KEY", "")
        kibana  = os.getenv("ELASTICSEARCH_KIBANA_URL", "")
        cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID", "")

        if not (es_url or cloud_id) or not api_key:
            return None

        return RegionConfig(
            name="Primary",
            region_code="us-east-1",
            es_url=es_url or f"cloud_id:{cloud_id}",
            api_key=api_key,
            kibana_url=kibana,
            is_primary=True,
        )
