"""
Index Template Service

Creates production-grade Elasticsearch index templates, component templates,
and ILM policies for Search demos. Ensures proper field mappings, semantic_text
fields, and data lifecycle policies are in place before indexing.
"""

import logging
from typing import Dict, List, Any, Optional
from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)


# Default ILM policy for Search demos
# Hot: 7 days, Warm: forcemerge + shrink, Delete: 90 days
SEARCH_ILM_POLICY = {
    "policy": {
        "phases": {
            "hot": {
                "min_age": "0ms",
                "actions": {
                    "rollover": {"max_age": "7d", "max_primary_shard_size": "10gb"},
                    "set_priority": {"priority": 100},
                },
            },
            "warm": {
                "min_age": "7d",
                "actions": {
                    "forcemerge": {"max_num_segments": 1},
                    "shrink": {"number_of_shards": 1},
                    "set_priority": {"priority": 50},
                },
            },
            "cold": {
                "min_age": "30d",
                "actions": {
                    "searchable_snapshot": {"snapshot_repository": "found-snapshots"},
                    "set_priority": {"priority": 0},
                },
            },
            "delete": {
                "min_age": "90d",
                "actions": {"delete": {}},
            },
        }
    }
}


class IndexTemplateService:
    """
    Creates and manages Elasticsearch index templates for Search demos.
    All operations are idempotent (check-before-create).
    """

    def __init__(self, es_client: Elasticsearch):
        self.es = es_client

    def ensure_search_stack(
        self,
        demo_slug: str,
        index_names: List[str],
        field_mappings: Dict[str, Any],
        semantic_fields: List[str],
        pipeline_name: Optional[str] = None,
        embedding_model: str = "elser",
    ) -> Dict[str, Any]:
        """
        Create full index template stack for a Search demo.

        Returns dict of created resource names.
        """
        results = {}

        # 1. ILM policy
        ilm_name = f"{demo_slug}-search-ilm"
        results["ilm_policy"] = self._ensure_ilm_policy(ilm_name)

        # 2. Mappings component template
        mappings_template = f"{demo_slug}-mappings"
        results["mappings_template"] = self._ensure_mappings_component(
            mappings_template, field_mappings, semantic_fields, embedding_model
        )

        # 3. Settings component template
        settings_template = f"{demo_slug}-settings"
        results["settings_template"] = self._ensure_settings_component(
            settings_template, ilm_name, pipeline_name
        )

        # 4. Index template binding both components
        index_template = f"{demo_slug}-search-template"
        index_patterns = [f"{name}*" for name in index_names]
        results["index_template"] = self._ensure_index_template(
            index_template,
            index_patterns,
            [mappings_template, settings_template],
        )

        return results

    def _ensure_ilm_policy(self, policy_name: str) -> str:
        try:
            self.es.ilm.get_lifecycle(name=policy_name)
            logger.info(f"ILM policy already exists: {policy_name}")
            return policy_name
        except Exception:
            pass

        try:
            # Try with searchable snapshots (cloud); fall back without cold phase
            self.es.ilm.put_lifecycle(name=policy_name, policy=SEARCH_ILM_POLICY["policy"])
            logger.info(f"Created ILM policy: {policy_name}")
        except Exception as e:
            if "searchable_snapshot" in str(e).lower() or "snapshot" in str(e).lower():
                # Fall back to policy without cold/searchable_snapshot phase
                simple_policy = {
                    "phases": {
                        "hot": SEARCH_ILM_POLICY["policy"]["phases"]["hot"],
                        "warm": SEARCH_ILM_POLICY["policy"]["phases"]["warm"],
                        "delete": SEARCH_ILM_POLICY["policy"]["phases"]["delete"],
                    }
                }
                self.es.ilm.put_lifecycle(name=policy_name, policy=simple_policy)
                logger.info(f"Created ILM policy (no cold phase): {policy_name}")
            else:
                logger.warning(f"Could not create ILM policy {policy_name}: {e}")

        return policy_name

    def _ensure_mappings_component(
        self,
        template_name: str,
        field_mappings: Dict[str, Any],
        semantic_fields: List[str],
        embedding_model: str = "elser",
    ) -> str:
        try:
            self.es.cluster.get_component_template(name=template_name)
            logger.info(f"Mappings component template already exists: {template_name}")
            return template_name
        except Exception:
            pass

        properties = field_mappings.get("properties", {}).copy()

        if embedding_model in ("e5", "jina"):
            # Dense models: keep source fields as text, add dense_vector output fields
            dims = 384 if embedding_model == "e5" else 1024  # e5-small=384, jina-v3=1024
            for sf in semantic_fields:
                if sf not in properties:
                    properties[sf] = {"type": "text"}
                vector_field = f"{sf}_vector"
                properties[vector_field] = {
                    "type": "dense_vector",
                    "dims": dims,
                    "index": True,
                    "similarity": "cosine",
                }
        else:
            # ELSER: map semantic fields to semantic_text with ELSER inference
            for sf in semantic_fields:
                if sf in properties:
                    properties[sf] = {
                        "type": "semantic_text",
                        "inference_id": ".elser-2-elasticsearch",
                    }

        # Always include @timestamp
        if "@timestamp" not in properties:
            properties["@timestamp"] = {"type": "date"}

        body = {
            "template": {
                "mappings": {
                    "properties": properties,
                    "_source": {"enabled": True},
                }
            }
        }

        try:
            self.es.cluster.put_component_template(name=template_name, body=body)
            logger.info(f"Created mappings component template: {template_name}")
        except Exception as e:
            logger.warning(f"Could not create mappings template {template_name}: {e}")

        return template_name

    def _ensure_settings_component(
        self,
        template_name: str,
        ilm_policy_name: str,
        pipeline_name: Optional[str],
    ) -> str:
        try:
            self.es.cluster.get_component_template(name=template_name)
            logger.info(f"Settings component template already exists: {template_name}")
            return template_name
        except Exception:
            pass

        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "index.lifecycle.name": ilm_policy_name,
        }
        if pipeline_name:
            settings["index.default_pipeline"] = pipeline_name

        body = {"template": {"settings": settings}}

        try:
            self.es.cluster.put_component_template(name=template_name, body=body)
            logger.info(f"Created settings component template: {template_name}")
        except Exception as e:
            logger.warning(f"Could not create settings template {template_name}: {e}")

        return template_name

    def _ensure_index_template(
        self,
        template_name: str,
        index_patterns: List[str],
        composed_of: List[str],
    ) -> str:
        try:
            self.es.indices.get_index_template(name=template_name)
            logger.info(f"Index template already exists: {template_name}")
            return template_name
        except Exception:
            pass

        body = {
            "index_patterns": index_patterns,
            "composed_of": composed_of,
            "priority": 200,
            "template": {
                "settings": {
                    "index.lifecycle.rollover_alias": template_name,
                }
            },
        }

        try:
            self.es.indices.put_index_template(name=template_name, body=body)
            logger.info(f"Created index template: {template_name}")
        except Exception as e:
            logger.warning(f"Could not create index template {template_name}: {e}")

        return template_name

    def teardown(self, demo_slug: str) -> None:
        """Remove all templates and policies for this demo (idempotent)."""
        for resource, method in [
            (f"{demo_slug}-search-template", self.es.indices.delete_index_template),
            (f"{demo_slug}-mappings", self.es.cluster.delete_component_template),
            (f"{demo_slug}-settings", self.es.cluster.delete_component_template),
            (f"{demo_slug}-search-ilm", self.es.ilm.delete_lifecycle),
        ]:
            try:
                method(name=resource)
                logger.info(f"Deleted: {resource}")
            except Exception:
                pass
