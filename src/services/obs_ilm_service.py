"""
Observability ILM Service

Creates Index Lifecycle Management policies for OTLP data streams.
Tiered retention strategy:
  Hot    →  7 days   (primary shards on fast SSD, full replicas)
  Warm   →  30 days  (reduced replicas, force-merged, searchable)
  Cold   →  90 days  (searchable snapshots, S3-backed)
  Frozen →  365 days (frozen tier, S3 searchable snapshots, min cost)
  Delete →  after 365 days

Addresses the Genesys "Lower Cost — control volume + retention tiers" outcome.
"""

import logging
from typing import Any, Callable, Dict, Optional

from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)


# Policy presets per data type
_POLICIES = {
    "logs": {
        "hot_days":    7,
        "warm_days":   30,
        "cold_days":   90,
        "frozen_days": 365,
        "priority":    100,
    },
    "metrics": {
        "hot_days":    3,   # metrics roll up faster, keep hot tier short
        "warm_days":   14,
        "cold_days":   60,
        "frozen_days": 180,
        "priority":    50,
    },
    "traces": {
        "hot_days":    2,   # traces are high-volume, expensive to keep
        "warm_days":   7,
        "cold_days":   30,
        "frozen_days": 90,
        "priority":    75,
    },
}


class ObsILMService:

    def __init__(self, es: Elasticsearch):
        self.es = es

    def create_all_policies(
        self,
        namespace: str = "default",
        progress: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Create ILM policies for logs, metrics, and traces."""
        results = {}
        total = len(_POLICIES)
        for i, (data_type, cfg) in enumerate(_POLICIES.items()):
            name = f"obs-{data_type}-{namespace}-ilm"
            if progress:
                progress((i + 1) / total, f"Creating ILM policy: {name}")
            ok, msg = self.create_policy(name, data_type, cfg)
            results[name] = {"success": ok, "message": msg}
            if ok:
                logger.info(f"ILM policy created: {name}")
            else:
                logger.warning(f"ILM policy failed: {name} — {msg}")
        return results

    def create_policy(
        self,
        policy_name: str,
        data_type: str,
        cfg: Optional[Dict] = None,
    ) -> tuple:
        """Create a single ILM policy. Returns (success, message)."""
        cfg = cfg or _POLICIES.get(data_type, _POLICIES["logs"])
        hot_d    = cfg["hot_days"]
        warm_d   = cfg["warm_days"]
        cold_d   = cfg["cold_days"]
        frozen_d = cfg["frozen_days"]

        policy = {
            "policy": {
                "phases": {
                    "hot": {
                        "min_age": "0ms",
                        "actions": {
                            "rollover": {
                                "max_age":            f"{hot_d}d",
                                "max_primary_shard_size": "50gb",
                            },
                            "set_priority": {"priority": cfg.get("priority", 100)},
                        },
                    },
                    "warm": {
                        "min_age": f"{warm_d}d",
                        "actions": {
                            "shrink":       {"number_of_shards": 1},
                            "forcemerge":   {"max_num_segments": 1},
                            "set_priority": {"priority": 50},
                            "allocate":     {"number_of_replicas": 0},
                        },
                    },
                    "cold": {
                        "min_age": f"{cold_d}d",
                        "actions": {
                            "searchable_snapshot": {
                                "snapshot_repository": "found-snapshots",
                                "force_merge_index":   True,
                            },
                            "set_priority": {"priority": 0},
                        },
                    },
                    "frozen": {
                        "min_age": f"{frozen_d}d",
                        "actions": {
                            "searchable_snapshot": {
                                "snapshot_repository": "found-snapshots",
                            }
                        },
                    },
                    "delete": {
                        "min_age": f"{frozen_d + 1}d",
                        "actions": {"delete": {}},
                    },
                }
            }
        }

        try:
            self.es.ilm.put_lifecycle(name=policy_name, policy=policy["policy"])
            return True, f"ILM policy '{policy_name}' created (hot:{hot_d}d → warm:{warm_d}d → cold:{cold_d}d → frozen:{frozen_d}d)"
        except Exception as exc:
            return False, str(exc)

    def get_policy_summary(self, namespace: str = "default") -> Dict[str, str]:
        """Return human-readable retention summary for all data types."""
        summaries = {}
        for dt, cfg in _POLICIES.items():
            summaries[dt] = (
                f"Hot {cfg['hot_days']}d → "
                f"Warm {cfg['warm_days']}d → "
                f"Cold {cfg['cold_days']}d → "
                f"Frozen {cfg['frozen_days']}d → Delete"
            )
        return summaries
