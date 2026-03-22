"""
Search Application Service

Creates and manages:
- Elastic Search Applications (with RRF hybrid search template)
- Query Rules (pin/boost specific results)
- Synonyms API sets (domain-specific vocabulary)
- Hybrid search weight tuning (BM25 vs semantic balance)
"""

import logging
from typing import Dict, List, Any, Optional
from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)


class SearchApplicationService:
    """
    Manages Elastic Search Applications, Query Rules, and Synonyms.
    All operations are idempotent.
    """

    def __init__(self, es_client: Elasticsearch):
        self.es = es_client

    # -------------------------------------------------------------------------
    # Search Application
    # -------------------------------------------------------------------------

    def ensure_search_application(
        self,
        demo_slug: str,
        index_names: List[str],
        semantic_fields: List[str],
        text_fields: List[str],
        rrf_rank_constant: int = 60,
        bm25_boost: float = 1.0,
        semantic_boost: float = 1.0,
        embedding_model: str = "elser",
    ) -> str:
        """
        Create an Elastic Search Application with an RRF-based hybrid search
        template that balances BM25 and ELSER semantic search.

        Returns the Search Application name.
        """
        app_name = f"{demo_slug}-search-app"

        template = self._build_search_template(
            semantic_fields=semantic_fields,
            text_fields=text_fields,
            rrf_rank_constant=rrf_rank_constant,
            bm25_boost=bm25_boost,
            semantic_boost=semantic_boost,
            embedding_model=embedding_model,
        )

        body = {
            "indices": index_names,
            "template": template,
        }

        try:
            # Check if exists first
            try:
                self.es.search_application.get(name=app_name)
                # Update existing
                self.es.search_application.put(name=app_name, body=body)
                logger.info(f"Updated Search Application: {app_name}")
            except Exception:
                # Create new
                self.es.search_application.put(name=app_name, body=body)
                logger.info(f"Created Search Application: {app_name}")
        except Exception as e:
            logger.warning(f"Could not create Search Application {app_name}: {e}")

        return app_name

    def _build_search_template(
        self,
        semantic_fields: List[str],
        text_fields: List[str],
        rrf_rank_constant: int,
        bm25_boost: float,
        semantic_boost: float,
        embedding_model: str = "elser",
    ) -> Dict[str, Any]:
        """
        Build an RRF hybrid search template that combines:
        - BM25 multi-match across text fields
        - Semantic kNN across semantic/vector fields (ELSER or E5)
        - RRF reciprocal rank fusion to merge results
        """
        # Select model config based on embedding type
        if embedding_model == "e5":
            model_id = ".multilingual-e5-small"
            knn_fields = [f"{sf}_vector" for sf in semantic_fields]
        elif embedding_model == "jina":
            model_id = "jina-embeddings-v3"
            knn_fields = [f"{sf}_vector" for sf in semantic_fields]
        else:
            # ELSER: kNN targets the semantic_text fields directly
            model_id = ".elser-2-elasticsearch"
            knn_fields = semantic_fields

        # BM25 multi-match query
        bm25_query = {
            "multi_match": {
                "query": "{{query}}",
                "fields": text_fields or ["*"],
                "boost": bm25_boost,
                "type": "best_fields",
            }
        }

        # Semantic knn queries
        knn_queries = []
        for kf in knn_fields:
            knn_queries.append({
                "field": kf,
                "query_vector_builder": {
                    "text_embedding": {
                        "model_id": model_id,
                        "model_text": "{{query}}",
                    }
                },
                "k": "{{size | default: 10}}",
                "num_candidates": 100,
                "boost": semantic_boost,
            })

        template_body = {
            "query": bm25_query,
            "size": "{{size | default: 10}}",
        }

        # Use RRF if we have both semantic and text fields
        if knn_queries and text_fields:
            template_body = {
                "retriever": {
                    "rrf": {
                        "retrievers": [
                            {"standard": {"query": bm25_query}},
                        ] + [
                            {"knn": knn} for knn in knn_queries
                        ],
                        "rank_constant": rrf_rank_constant,
                        "rank_window_size": 100,
                    }
                },
                "size": "{{size | default: 10}}",
            }
        elif knn_queries:
            template_body["knn"] = knn_queries

        return {
            "script": {
                "source": template_body,
                "params": {
                    "query": "",
                    "size": 10,
                },
            }
        }

    def update_hybrid_weights(
        self,
        demo_slug: str,
        index_names: List[str],
        semantic_fields: List[str],
        text_fields: List[str],
        bm25_boost: float,
        semantic_boost: float,
        rrf_rank_constant: int = 60,
        embedding_model: str = "elser",
    ) -> str:
        """Update the hybrid search weights for an existing Search Application."""
        return self.ensure_search_application(
            demo_slug=demo_slug,
            index_names=index_names,
            semantic_fields=semantic_fields,
            text_fields=text_fields,
            rrf_rank_constant=rrf_rank_constant,
            bm25_boost=bm25_boost,
            semantic_boost=semantic_boost,
            embedding_model=embedding_model,
        )

    # -------------------------------------------------------------------------
    # Query Rules
    # -------------------------------------------------------------------------

    def ensure_query_rules(
        self,
        demo_slug: str,
        pinned_rules: Optional[List[Dict[str, Any]]] = None,
        boost_rules: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[str]:
        """
        Create a Query Ruleset that pins/boosts specific documents for key queries.

        pinned_rules: [{"query_terms": ["refund policy"], "document_ids": ["doc-123"]}]
        boost_rules:  [{"query_terms": ["pricing"], "filter": {"term": {"category": "pricing"}}, "boost": 2.0}]

        Returns ruleset ID or None if no rules provided.
        """
        if not pinned_rules and not boost_rules:
            return None

        ruleset_id = f"{demo_slug}-query-rules"
        rules = []

        for i, pin in enumerate(pinned_rules or []):
            rules.append({
                "rule_id": f"pin-{i}",
                "type": "pinned",
                "criteria": [
                    {
                        "type": "fuzzy",
                        "metadata": "query",
                        "values": pin.get("query_terms", []),
                    }
                ],
                "actions": {
                    "ids": pin.get("document_ids", []),
                },
            })

        for i, boost in enumerate(boost_rules or []):
            rules.append({
                "rule_id": f"boost-{i}",
                "type": "exclude" if boost.get("exclude") else "pinned",
                "criteria": [
                    {
                        "type": "fuzzy",
                        "metadata": "query",
                        "values": boost.get("query_terms", []),
                    }
                ],
                "actions": {
                    "docs": [
                        {
                            "_index": boost.get("index", "_any"),
                            "_id": boost.get("doc_id", "*"),
                        }
                    ]
                },
            })

        try:
            self.es.query_rules.put_ruleset(
                ruleset_id=ruleset_id,
                body={"rules": rules},
            )
            logger.info(f"Created Query Ruleset: {ruleset_id} ({len(rules)} rules)")
        except Exception as e:
            logger.warning(f"Could not create Query Ruleset {ruleset_id}: {e}")

        return ruleset_id

    # -------------------------------------------------------------------------
    # Synonyms
    # -------------------------------------------------------------------------

    def ensure_synonyms(
        self,
        demo_slug: str,
        synonym_pairs: Optional[List[str]] = None,
        industry: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a Synonyms API set for domain-specific vocabulary.

        synonym_pairs: Solr format strings, e.g. ["heart attack, myocardial infarction",
                                                    "AI, artificial intelligence, machine learning"]
        industry: Used to add default industry synonyms if no pairs provided.

        Returns synonyms set ID or None.
        """
        pairs = synonym_pairs or self._default_synonyms_for_industry(industry)
        if not pairs:
            return None

        synonyms_id = f"{demo_slug}-synonyms"

        synonym_rules = [
            {"id": f"rule-{i}", "synonyms": pair}
            for i, pair in enumerate(pairs)
        ]

        try:
            self.es.synonyms.put_synonym(
                id=synonyms_id,
                body={"synonyms_set": synonym_rules},
            )
            logger.info(f"Created Synonyms set: {synonyms_id} ({len(synonym_rules)} rules)")
        except Exception as e:
            logger.warning(f"Could not create Synonyms set {synonyms_id}: {e}")
            return None

        return synonyms_id

    def _default_synonyms_for_industry(self, industry: Optional[str]) -> List[str]:
        """Return starter synonym pairs for common industries."""
        if not industry:
            return []

        industry_lower = industry.lower()

        if any(k in industry_lower for k in ["health", "medical", "pharma", "hospital"]):
            return [
                "heart attack, myocardial infarction, MI, cardiac arrest",
                "high blood pressure, hypertension",
                "doctor, physician, clinician, provider",
                "drug, medication, medicine, prescription",
                "patient, client, beneficiary",
            ]
        elif any(k in industry_lower for k in ["finance", "bank", "insurance", "fintech"]):
            return [
                "claim, request, application, submission",
                "policy, plan, coverage, contract",
                "premium, rate, cost, fee",
                "denial, rejection, decline, refused",
                "prior authorization, PA, pre-auth, pre-authorization",
            ]
        elif any(k in industry_lower for k in ["retail", "ecommerce", "e-commerce", "shop"]):
            return [
                "refund, return, chargeback, reversal",
                "order, purchase, transaction, buy",
                "product, item, SKU, listing",
                "shipping, delivery, dispatch, fulfillment",
                "discount, promotion, coupon, offer, deal",
            ]
        elif any(k in industry_lower for k in ["tech", "software", "saas", "cloud"]):
            return [
                "bug, issue, defect, problem, error",
                "feature request, enhancement, improvement, FR",
                "deploy, release, rollout, launch",
                "incident, outage, downtime, disruption",
                "API, endpoint, service, interface",
            ]
        return []

    # -------------------------------------------------------------------------
    # Teardown
    # -------------------------------------------------------------------------

    def teardown(self, demo_slug: str) -> None:
        """Remove all Search Application resources for this demo."""
        app_name = f"{demo_slug}-search-app"
        ruleset_id = f"{demo_slug}-query-rules"
        synonyms_id = f"{demo_slug}-synonyms"

        for name, method in [
            (app_name, lambda n: self.es.search_application.delete(name=n)),
            (ruleset_id, lambda n: self.es.query_rules.delete_ruleset(ruleset_id=n)),
            (synonyms_id, lambda n: self.es.synonyms.delete_synonym(id=n)),
        ]:
            try:
                method(name)
                logger.info(f"Deleted: {name}")
            except Exception:
                pass
