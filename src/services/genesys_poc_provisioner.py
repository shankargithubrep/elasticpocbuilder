"""
Genesys POC Provisioner

Provisions all assets for the Genesys Knowledge Base POC against a live
Elasticsearch cluster.  Demonstrates:

  - semantic_text field backed by Jina Embeddings v5 (EIS)
  - Document-Level Security (DLS) enforced at query-time via index roles
  - Multi-tenant ACL captured at sync time (acl.principals)
  - Hybrid retrieval: BM25 + semantic + RRF
  - Connector event tracking via kb_sync_events

Provisioning sequence:
  1. Create kb_content index with semantic_text mapping
  2. Create kb_sync_events index
  3. Create DLS roles (genesys_acme_agent, genesys_globalnet_agent, genesys_admin)
  4. Create demo users (alice_acme, bob_globalnet, admin_genesys)
  5. Index ~60 kb_content documents across sharepoint / salesforce / confluence
  6. Index ~30 kb_sync_events

Standalone usage:
    python -m src.services.genesys_poc_provisioner

Programmatic usage:
    from src.services.genesys_poc_provisioner import GenesysPOCProvisioner
    p = GenesysPOCProvisioner()
    summary = p.provision_all(progress_callback=print)
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from dotenv import load_dotenv
from elasticsearch import Elasticsearch, NotFoundError

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_es_client() -> Elasticsearch:
    api_key  = os.getenv("ELASTICSEARCH_API_KEY", "")
    cloud_id = os.getenv("ELASTICSEARCH_CLOUD_ID")
    if cloud_id:
        return Elasticsearch(cloud_id=cloud_id, api_key=api_key)
    endpoint = os.getenv("ELASTIC_ENDPOINT", "http://localhost:9200")
    return Elasticsearch(endpoint, api_key=api_key)


def _ts(days_ago: int = 0, hours_ago: int = 0) -> str:
    """Return an ISO-8601 UTC timestamp offset by the given delta."""
    t = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours_ago)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Mapping constants
# ---------------------------------------------------------------------------

KB_CONTENT_MAPPING: Dict[str, Any] = {
    "settings": {
        "index.mapping.total_fields.limit": 5000
    },
    "mappings": {
        "properties": {
            "tenant_id":      {"type": "keyword"},
            "source":         {"type": "keyword"},
            "doc_id":         {"type": "keyword"},
            "chunk_id":       {"type": "keyword"},
            "title": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}}
            },
            "content": {
                "type": "semantic_text",
                "inference_id": ".jina-embeddings-v5-text-small"
            },
            "locale":         {"type": "keyword"},
            "acl": {
                "properties": {
                    "principals": {"type": "keyword"}
                }
            },
            "source_url":     {"type": "keyword"},
            "last_synced_at": {"type": "date"},
            "@timestamp":     {"type": "date"},
            # Metadata filtering fields — drive the "narrow scope by topic/audience" demo moment
            "topic":              {"type": "keyword"},   # billing_disputes | escalation | compliance | technical | onboarding | product_faq | data_privacy | retention | sla
            "document_type":      {"type": "keyword"},   # procedure | policy | runbook | faq | how_to | reference | playbook | template
            "audience":           {"type": "keyword"},   # agents | agents_tier2 | agents+public | internal
            "product_family":     {"type": "keyword"},   # voice | digital | analytics | platform | all | enterprise
            # SharePoint custom columns — ingested via Graph API per Genesys requirement
            "sp_custom_tier":          {"type": "keyword"},   # standard | premium | enterprise
            "sp_custom_product_line":  {"type": "keyword"},   # support-ops | hr | compliance | comms | safety | enterprise | telehealth | clinical | records | kyc | fraud | porting
            "sp_custom_region":        {"type": "keyword"},   # us | eu | apac | global
        }
    }
}

KB_SYNC_EVENTS_MAPPING: Dict[str, Any] = {
    "mappings": {
        "properties": {
            "@timestamp":              {"type": "date"},
            "tenant_id":               {"type": "keyword"},
            "source":                  {"type": "keyword"},
            "event_type":              {"type": "keyword"},
            "doc_id":                  {"type": "keyword"},
            "status":                  {"type": "keyword"},
            "error_message":           {"type": "text"},
            "retry_count":             {"type": "integer"},
            "connector_id":            {"type": "keyword"},
            "region":                  {"type": "keyword"},
            # RTBF / GDPR Article 17 — audit trail fields
            "propagation_confirmed":   {"type": "boolean"},
            "propagation_timestamp":   {"type": "date"},
            "gdpr_article17":          {"type": "boolean"},
            "rtbf_request_id":         {"type": "keyword"},
        }
    }
}

CONNECTOR_REGISTRY_MAPPING: Dict[str, Any] = {
    "settings": {"index.mode": "lookup"},
    "mappings": {
        "properties": {
            "connector_id":           {"type": "keyword"},
            "tenant_id":              {"type": "keyword"},
            "source_type":            {"type": "keyword"},
            "region":                 {"type": "keyword"},
            "sync_schedule":          {"type": "keyword"},
            "last_sync_cursor":       {"type": "date"},
            "last_successful_sync":   {"type": "date"},
            "status":                 {"type": "keyword"},
            "docs_synced_total":      {"type": "long"},
            "avg_sync_duration_ms":   {"type": "integer"},
            "failure_rate_pct":       {"type": "float"},
            "last_error":             {"type": "text"},
        }
    }
}

TENANT_REGISTRY_MAPPING: Dict[str, Any] = {
    "settings": {"index.mode": "lookup"},
    "mappings": {
        "properties": {
            "tenant_id":                        {"type": "keyword"},
            "tenant_name":                      {"type": "keyword"},
            "region":                           {"type": "keyword"},
            "industry_vertical":                {"type": "keyword"},
            "subscription_tier":                {"type": "keyword"},
            "data_sensitivity_classification":  {"type": "keyword"},
            "data_residency":                   {"type": "keyword"},
            "kb_index":                         {"type": "keyword"},
            "primary_locale":                   {"type": "keyword"},
            "onboarded_at":                     {"type": "date"},
        }
    }
}

RETRIEVAL_LOGS_MAPPING: Dict[str, Any] = {
    "mappings": {
        "properties": {
            "@timestamp":            {"type": "date"},
            "tenant_id":             {"type": "keyword"},
            "region":                {"type": "keyword"},
            "query_type":            {"type": "keyword"},
            "query_latency_ms":      {"type": "integer"},
            "dls_filter_time_ms":    {"type": "integer"},
            "retrieval_only_time_ms":{"type": "integer"},
            "dls_enabled":           {"type": "boolean"},
            "result_count":          {"type": "integer"},
            "user_principal":        {"type": "keyword"},
            "locale":                {"type": "keyword"},
        }
    }
}

# ---------------------------------------------------------------------------
# Tenant definitions — single source of truth for roles + users
# Add/remove tenants here; roles, users and DLS queries are auto-generated.
# ---------------------------------------------------------------------------

DEMO_PASSWORD = "pass01"  # simple password for demo environment (ES requires min 6 chars)

# ---------------------------------------------------------------------------
# TENANTS — single source of truth.
# Each tenant gets two DLS roles:
#   support: sees standard docs (group:{id}-support + tenant:{id})
#   tier2:   sees support docs PLUS sensitive escalation docs (group:{id}-tier2)
# This powers the "same query, different result count" demo moment.
# ---------------------------------------------------------------------------

TENANTS: List[Dict[str, Any]] = [
    {"id": "acme",      "label": "ACME Telecommunications",     "industry": "Telecom"},
    {"id": "globalnet", "label": "GlobalNet Financial Services", "industry": "Financial Services"},
]


def _build_roles() -> Dict[str, Any]:
    """Generate two DLS roles per tenant (support + tier2) plus unrestricted admin."""
    roles: Dict[str, Any] = {}
    for t in TENANTS:
        tid = t["id"]
        # Support role — standard docs only
        roles[f"genesys_{tid}_support"] = {
            "indices": [{
                "names": ["kb_content"],
                "privileges": ["read", "view_index_metadata"],
                "query": json.dumps({
                    "bool": {"filter": [
                        {"term": {"tenant_id": tid}},
                        {"terms": {"acl.principals": [f"tenant:{tid}", f"group:{tid}-support", f"group:{tid}-agents"]}},
                    ]}
                })
            }]
        }
        # Tier2 role — support docs + sensitive escalation docs
        roles[f"genesys_{tid}_tier2"] = {
            "indices": [{
                "names": ["kb_content"],
                "privileges": ["read", "view_index_metadata"],
                "query": json.dumps({
                    "bool": {"filter": [
                        {"term": {"tenant_id": tid}},
                        {"terms": {"acl.principals": [
                            f"tenant:{tid}",
                            f"group:{tid}-support",
                            f"group:{tid}-agents",
                            f"group:{tid}-tier2",
                            f"group:{tid}-compliance",
                            f"group:{tid}-sre",
                        ]}},
                    ]}
                })
            }]
        }
    roles["genesys_admin"] = {
        "indices": [{"names": ["kb_content"], "privileges": ["read", "view_index_metadata"]}]
    }
    return roles


def _build_users() -> List[Dict[str, Any]]:
    """Generate two users per tenant (support + tier2) plus admin."""
    users: List[Dict[str, Any]] = []
    for t in TENANTS:
        tid = t["id"]
        users.append({
            "username": f"{tid}-support",
            "password": DEMO_PASSWORD,
            "roles": [f"genesys_{tid}_support"],
            "full_name": f"{t['label']} — Support Agent",
            "email": f"support@{tid}.com",
        })
        users.append({
            "username": f"{tid}-tier2",
            "password": DEMO_PASSWORD,
            "roles": [f"genesys_{tid}_tier2"],
            "full_name": f"{t['label']} — Tier 2 Agent",
            "email": f"tier2@{tid}.com",
        })
    users.append({
        "username": "admin",
        "password": DEMO_PASSWORD,
        "roles": ["genesys_admin"],
        "full_name": "Genesys Platform Admin",
        "email": "admin@genesys.com",
    })
    return users


ROLES: Dict[str, Any] = _build_roles()
USERS: List[Dict[str, Any]] = _build_users()

# ---------------------------------------------------------------------------
# Sample KB content
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Document metadata — topic / document_type / audience / product_family tags
# + SharePoint custom columns (sp_custom_*) for SharePoint-sourced docs.
# This drives the "metadata filtering" demo moment: same query, narrowed scope.
# ---------------------------------------------------------------------------
_DOC_META: Dict[str, Dict[str, str]] = {
    # ── SharePoint / ACME ───────────────────────────────────────────────────
    "HR-001":    {"topic": "escalation",      "document_type": "procedure", "audience": "agents",        "product_family": "all",       "sp_custom_tier": "standard",   "sp_custom_product_line": "support-ops", "sp_custom_region": "us"},
    "HR-002":    {"topic": "compliance",      "document_type": "policy",    "audience": "internal",      "product_family": "all",       "sp_custom_tier": "enterprise", "sp_custom_product_line": "hr",          "sp_custom_region": "us"},
    "HR-003":    {"topic": "compliance",      "document_type": "procedure", "audience": "agents",        "product_family": "all",       "sp_custom_tier": "standard",   "sp_custom_product_line": "safety",      "sp_custom_region": "us"},
    "HR-004":    {"topic": "data_privacy",    "document_type": "policy",    "audience": "agents_tier2",  "product_family": "all",       "sp_custom_tier": "enterprise", "sp_custom_product_line": "compliance",  "sp_custom_region": "eu"},
    "HR-005":    {"topic": "onboarding",      "document_type": "policy",    "audience": "agents",        "product_family": "all",       "sp_custom_tier": "standard",   "sp_custom_product_line": "hr",          "sp_custom_region": "us"},
    # ── SharePoint / GlobalNet ───────────────────────────────────────────────
    "HR-GN-001": {"topic": "escalation",      "document_type": "runbook",   "audience": "agents",        "product_family": "all",       "sp_custom_tier": "standard",   "sp_custom_product_line": "support-ops", "sp_custom_region": "us"},
    "HR-GN-002": {"topic": "compliance",      "document_type": "policy",    "audience": "agents",        "product_family": "all",       "sp_custom_tier": "enterprise", "sp_custom_product_line": "compliance",  "sp_custom_region": "us"},
    "HR-GN-003": {"topic": "compliance",      "document_type": "policy",    "audience": "agents_tier2",  "product_family": "all",       "sp_custom_tier": "enterprise", "sp_custom_product_line": "compliance",  "sp_custom_region": "us"},
    "HR-GN-004": {"topic": "onboarding",      "document_type": "policy",    "audience": "agents",        "product_family": "all",       "sp_custom_tier": "standard",   "sp_custom_product_line": "hr",          "sp_custom_region": "us"},
    "HR-GN-005": {"topic": "compliance",      "document_type": "policy",    "audience": "agents_tier2",  "product_family": "all",       "sp_custom_tier": "enterprise", "sp_custom_product_line": "compliance",  "sp_custom_region": "eu"},
    # ── Salesforce / ACME ───────────────────────────────────────────────────
    "SF-A-001":  {"topic": "billing_disputes","document_type": "procedure", "audience": "agents",        "product_family": "all"},
    "SF-A-002":  {"topic": "product_faq",     "document_type": "faq",       "audience": "agents+public", "product_family": "all"},
    "SF-A-003":  {"topic": "retention",       "document_type": "playbook",  "audience": "agents",        "product_family": "all"},
    "SF-A-004":  {"topic": "sla",             "document_type": "reference", "audience": "agents",        "product_family": "all"},
    "SF-A-005":  {"topic": "billing_disputes","document_type": "policy",    "audience": "agents_tier2",  "product_family": "enterprise"},
    # ── Salesforce / GlobalNet ───────────────────────────────────────────────
    "SF-GN-001": {"topic": "billing_disputes","document_type": "procedure", "audience": "agents",        "product_family": "all"},
    "SF-GN-002": {"topic": "technical",       "document_type": "procedure", "audience": "agents",        "product_family": "all"},
    "SF-GN-003": {"topic": "onboarding",      "document_type": "how_to",    "audience": "agents",        "product_family": "all"},
    "SF-GN-004": {"topic": "product_faq",     "document_type": "faq",       "audience": "agents+public", "product_family": "voice"},
    "SF-GN-005": {"topic": "escalation",      "document_type": "template",  "audience": "agents",        "product_family": "all"},
    # ── Confluence / ACME ───────────────────────────────────────────────────
    "CONF-A-001":{"topic": "technical",       "document_type": "runbook",   "audience": "internal",      "product_family": "platform"},
    "CONF-A-002":{"topic": "technical",       "document_type": "runbook",   "audience": "internal",      "product_family": "platform"},
    "CONF-A-003":{"topic": "escalation",      "document_type": "runbook",   "audience": "internal",      "product_family": "all"},
    "CONF-A-004":{"topic": "technical",       "document_type": "reference", "audience": "internal",      "product_family": "analytics"},
    "CONF-A-005":{"topic": "technical",       "document_type": "reference", "audience": "internal",      "product_family": "analytics"},
    # ── Confluence / GlobalNet ───────────────────────────────────────────────
    "CONF-GN-001":{"topic": "technical",      "document_type": "runbook",   "audience": "internal",      "product_family": "platform"},
    "CONF-GN-002":{"topic": "technical",      "document_type": "runbook",   "audience": "internal",      "product_family": "voice"},
    "CONF-GN-003":{"topic": "technical",      "document_type": "runbook",   "audience": "internal",      "product_family": "all"},
    "CONF-GN-004":{"topic": "data_privacy",   "document_type": "procedure", "audience": "agents_tier2",  "product_family": "all"},
    "CONF-GN-005":{"topic": "technical",      "document_type": "reference", "audience": "internal",      "product_family": "all"},
    # ── Additional tenants ───────────────────────────────────────────────────
    "APX-SP-001": {"topic": "product_faq",    "document_type": "policy",    "audience": "agents",        "product_family": "voice",     "sp_custom_tier": "standard",   "sp_custom_product_line": "porting",     "sp_custom_region": "us"},
    "APX-SP-002": {"topic": "escalation",     "document_type": "procedure", "audience": "agents",        "product_family": "all",       "sp_custom_tier": "standard",   "sp_custom_product_line": "comms",       "sp_custom_region": "us"},
    "APX-SP-003": {"topic": "sla",            "document_type": "runbook",   "audience": "agents_tier2",  "product_family": "enterprise","sp_custom_tier": "enterprise", "sp_custom_product_line": "enterprise",  "sp_custom_region": "us"},
    "BW-SP-001":  {"topic": "compliance",     "document_type": "procedure", "audience": "agents_tier2",  "product_family": "all",       "sp_custom_tier": "enterprise", "sp_custom_product_line": "kyc",         "sp_custom_region": "eu"},
    "BW-SP-002":  {"topic": "escalation",     "document_type": "procedure", "audience": "agents_tier2",  "product_family": "all",       "sp_custom_tier": "enterprise", "sp_custom_product_line": "fraud",       "sp_custom_region": "eu"},
    "BW-SP-003":  {"topic": "data_privacy",   "document_type": "policy",    "audience": "agents_tier2",  "product_family": "all",       "sp_custom_tier": "enterprise", "sp_custom_product_line": "compliance",  "sp_custom_region": "eu"},
    "MER-CF-001": {"topic": "compliance",     "document_type": "policy",    "audience": "agents_tier2",  "product_family": "all"},
    "MER-CF-002": {"topic": "compliance",     "document_type": "procedure", "audience": "agents_tier2",  "product_family": "all"},
    "MER-CF-003": {"topic": "compliance",     "document_type": "policy",    "audience": "agents_tier2",  "product_family": "all"},
    "FOR-SF-001": {"topic": "product_faq",    "document_type": "procedure", "audience": "agents",        "product_family": "all"},
    "FOR-SF-002": {"topic": "escalation",     "document_type": "procedure", "audience": "agents_tier2",  "product_family": "all"},
    "FOR-SF-003": {"topic": "billing_disputes","document_type": "procedure","audience": "agents",        "product_family": "all"},
    "CB-SP-001":  {"topic": "technical",      "document_type": "procedure", "audience": "agents",        "product_family": "all",       "sp_custom_tier": "standard",   "sp_custom_product_line": "telehealth",  "sp_custom_region": "us"},
    "CB-SP-002":  {"topic": "escalation",     "document_type": "procedure", "audience": "agents",        "product_family": "all",       "sp_custom_tier": "standard",   "sp_custom_product_line": "clinical",    "sp_custom_region": "us"},
    "CB-SP-003":  {"topic": "compliance",     "document_type": "procedure", "audience": "agents_tier2",  "product_family": "all",       "sp_custom_tier": "enterprise", "sp_custom_product_line": "compliance",  "sp_custom_region": "us"},
    "NXT-CF-001": {"topic": "product_faq",    "document_type": "policy",    "audience": "agents",        "product_family": "voice"},
    "NXT-CF-002": {"topic": "technical",      "document_type": "policy",    "audience": "agents",        "product_family": "all"},
    "NXT-CF-003": {"topic": "product_faq",    "document_type": "faq",       "audience": "agents+public", "product_family": "voice"},
    "PV-SF-001":  {"topic": "compliance",     "document_type": "policy",    "audience": "agents_tier2",  "product_family": "all"},
    "PV-SF-002":  {"topic": "product_faq",    "document_type": "procedure", "audience": "agents",        "product_family": "all"},
    "PV-SF-003":  {"topic": "sla",            "document_type": "policy",    "audience": "agents_tier2",  "product_family": "all"},
    "ALC-SP-001": {"topic": "escalation",     "document_type": "procedure", "audience": "agents_tier2",  "product_family": "all",       "sp_custom_tier": "enterprise", "sp_custom_product_line": "clinical",    "sp_custom_region": "us"},
    "ALC-SP-002": {"topic": "compliance",     "document_type": "policy",    "audience": "agents",        "product_family": "all",       "sp_custom_tier": "standard",   "sp_custom_product_line": "records",     "sp_custom_region": "us"},
    "ALC-SP-003": {"topic": "compliance",     "document_type": "procedure", "audience": "agents",        "product_family": "all",       "sp_custom_tier": "standard",   "sp_custom_product_line": "clinical",    "sp_custom_region": "us"},
    "VTX-SF-001": {"topic": "sla",            "document_type": "policy",    "audience": "agents_tier2",  "product_family": "all"},
    "VTX-SF-002": {"topic": "sla",            "document_type": "reference", "audience": "agents_tier2",  "product_family": "all"},
    "VTX-SF-003": {"topic": "compliance",     "document_type": "procedure", "audience": "agents_tier2",  "product_family": "all"},
    "EF-CF-001":  {"topic": "compliance",     "document_type": "procedure", "audience": "agents_tier2",  "product_family": "all"},
    "EF-CF-002":  {"topic": "data_privacy",   "document_type": "procedure", "audience": "agents_tier2",  "product_family": "all"},
    "EF-CF-003":  {"topic": "compliance",     "document_type": "reference", "audience": "agents_tier2",  "product_family": "all"},
    # ── Paraphrase demo (SF-A-006, SF-A-007) + multilingual demo (SF-GN-006) ──
    # SF-A-006: formal billing vocabulary — BM25 fails on casual queries, Jina v5 succeeds
    # SF-A-007: table-structured content — demonstrates hard chunking splitting the matrix mid-row
    # SF-GN-006: full Spanish document — demonstrates cross-lingual semantic retrieval
    "SF-A-006":  {"topic": "billing_disputes", "document_type": "reference",  "audience": "agents",       "product_family": "enterprise"},
    "SF-A-007":  {"topic": "escalation",       "document_type": "procedure",  "audience": "agents",       "product_family": "all"},
    "SF-GN-006": {"topic": "billing_disputes", "document_type": "procedure",  "audience": "agents",       "product_family": "all"},
}

def _apply_meta(doc_id: str, source: str) -> Dict[str, str]:
    """Return metadata fields for a doc_id. Falls back to sensible defaults."""
    m = _DOC_META.get(doc_id, {})
    out: Dict[str, str] = {
        "topic":          m.get("topic", "general"),
        "document_type":  m.get("document_type", "document"),
        "audience":       m.get("audience", "agents"),
        "product_family": m.get("product_family", "all"),
    }
    if source == "sharepoint" and "sp_custom_tier" in m:
        out["sp_custom_tier"]         = m["sp_custom_tier"]
        out["sp_custom_product_line"] = m.get("sp_custom_product_line", "all")
        out["sp_custom_region"]       = m.get("sp_custom_region", "global")
    return out


def _build_kb_documents() -> List[Dict[str, Any]]:  # noqa: C901
    """Return ~60 realistic kb_content documents across 3 sources and 2 tenants."""
    docs: List[Dict[str, Any]] = []

    # ── SharePoint ──────────────────────────────────────────────────────────
    sharepoint_acme = [
        ("HR-001", "Employee Escalation Policy",
         "When a customer complaint cannot be resolved at Tier 1, agents must escalate to the Tier 2 queue "
         "within 15 minutes. All escalations require a case ID and a brief summary of the issue. Tier 2 agents "
         "are empowered to offer service credits up to $250. Escalations to management require director approval.",
         ["group:acme-agents", "tenant:acme"], "en-US"),

        ("HR-002", "FMLA Leave Request Procedure",
         "Employees requesting Family and Medical Leave must submit Form HR-204 at least 30 days in advance "
         "when the leave is foreseeable. HR will respond within 5 business days with an eligibility determination. "
         "Medical certification from a licensed provider is required for all health-related FMLA requests. "
         "Intermittent leave must be tracked in the HR portal.",
         ["group:acme-hr", "group:acme-managers", "tenant:acme"], "en-US"),

        ("HR-003", "Workplace Incident Reporting",
         "All workplace incidents including near-misses must be reported within 24 hours using the Safety Portal. "
         "Supervisors must complete a root-cause analysis within 72 hours of any recordable injury. OSHA 300 logs "
         "are updated monthly and reviewed by the Safety Committee. Serious incidents trigger an immediate "
         "cross-functional review.",
         ["group:acme-agents", "group:acme-safety", "tenant:acme"], "en-US"),

        ("HR-004", "Data Retention and Privacy Compliance",
         "Customer PII must be retained for no longer than 36 months unless subject to a legal hold. Upon "
         "receiving a RTBF (Right to be Forgotten) request, the data team has 30 days to confirm deletion across "
         "all systems including backups. All access to PII fields is logged in the audit trail. Annual GDPR "
         "training is mandatory for all agents handling EU customer data.",
         ["group:acme-compliance", "tenant:acme"], "en-US"),

        ("HR-005", "Remote Work Equipment Policy",
         "Acme provides a one-time equipment stipend of $1,200 for home-office setup. Approved items include "
         "monitors, ergonomic chairs, and headsets. Equipment must be returned upon offboarding. Laptops are "
         "company property and must have full-disk encryption enabled at all times. VPN is required for any "
         "access to internal systems from outside the corporate network.",
         ["group:acme-agents", "tenant:acme"], "en-US"),
    ]

    sharepoint_globalnet = [
        ("HR-GN-001", "Agent Escalation Runbook — GlobalNet",
         "GlobalNet agents follow a three-tier escalation model. Tier 1 handles routine inquiries. Tier 2 handles "
         "billing disputes and technical issues requiring system access. Tier 3 is reserved for executive "
         "escalations and regulatory complaints. All escalations must be logged in Salesforce with a disposition "
         "code within 2 hours of resolution.",
         ["group:globalnet-agents", "tenant:globalnet"], "en-US"),

        ("HR-GN-002", "Compliance Training Requirements",
         "All GlobalNet agents must complete PCI-DSS Level 1 training annually before March 31st. New hires "
         "have 30 days to complete the onboarding compliance module. Training completion is tracked in the LMS "
         "and tied to performance reviews. Failure to complete required training results in system access "
         "suspension until compliance is restored.",
         ["group:globalnet-compliance", "group:globalnet-agents", "tenant:globalnet"], "en-US"),

        ("HR-GN-003", "Customer Consent Management",
         "GlobalNet is required to capture explicit opt-in consent before enrolling customers in any marketing "
         "communications. Consent records are stored in the CRM with a timestamp and agent ID. Customers may "
         "withdraw consent at any time via self-service portal or by calling support. Withdrawal must be "
         "processed within 48 hours across all downstream systems.",
         ["group:globalnet-compliance", "tenant:globalnet"], "es-419"),

        ("HR-GN-004", "Shift Scheduling and Overtime Policy",
         "GlobalNet contact center operates 24/7 across three shifts. Overtime requests must be submitted "
         "72 hours in advance and approved by the shift supervisor. Premium pay of 1.5x applies to all hours "
         "beyond 40 in a workweek. Emergency overtime may be assigned with 4-hour notice during high-volume "
         "events such as outages or billing cycles.",
         ["group:globalnet-agents", "tenant:globalnet"], "en-US"),

        ("HR-GN-005", "Whistleblower Protection Policy",
         "GlobalNet prohibits retaliation against any employee who reports suspected fraud, waste, or regulatory "
         "violation in good faith. Reports can be submitted anonymously via the Ethics Hotline at 1-800-555-0199. "
         "The Compliance team investigates all reports within 15 business days. Substantiated reports are "
         "escalated to the Board Audit Committee.",
         ["group:globalnet-compliance", "group:globalnet-managers", "tenant:globalnet"], "fr-FR"),
    ]

    for doc_id, title, content, principals, locale in sharepoint_acme + sharepoint_globalnet:
        tenant = "acme" if doc_id.startswith("HR-0") else "globalnet"
        for chunk_num in range(2):
            chunk_id = f"{doc_id}-chunk-{chunk_num}"
            docs.append({
                "tenant_id": tenant,
                "source": "sharepoint",
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "title": title,
                "content": content if chunk_num == 0 else content[len(content)//2:],
                "locale": locale,
                "acl": {"principals": principals},
                "source_url": f"https://sharepoint.{tenant}.internal/sites/HR/{doc_id}",
                "last_synced_at": _ts(days_ago=1),
                "@timestamp": _ts(days_ago=1),
                **_apply_meta(doc_id, "sharepoint"),
            })

    # ── Salesforce ──────────────────────────────────────────────────────────
    sf_acme = [
        ("SF-A-001", "Billing Dispute Resolution — Acme",
         "To resolve a billing dispute, verify the customer's last three invoices in Salesforce. If an overcharge "
         "is confirmed, issue a credit memo within one billing cycle. Disputes involving recurring charges require "
         "supervisor sign-off before any credit exceeding $500 is applied. Document the root cause and resolution "
         "steps in the case notes.",
         ["group:acme-billing", "tenant:acme"], "en-US"),

        ("SF-A-002", "Product Upgrade FAQ",
         "Customers can upgrade their plan at any time through self-service or by calling support. Downgrades "
         "take effect at the start of the next billing cycle. There is no fee for upgrades but a $25 processing "
         "fee applies to downgrades requested less than 5 days before renewal. Grandfathered pricing is not "
         "preserved after a voluntary downgrade.",
         ["group:acme-agents", "group:acme-billing", "tenant:acme"], "en-US"),

        ("SF-A-003", "Churn Prevention Playbook",
         "Agents who identify a customer at churn risk should immediately flag the account in Salesforce using "
         "the 'Retention' tag. The retention team will reach out within 24 hours with a tailored offer. Common "
         "retention levers include a 20% discount for 3 months, a service credit, or a plan downgrade with "
         "feature preservation. All retention actions must be logged with outcome codes.",
         ["group:acme-retention", "tenant:acme"], "en-US"),

        ("SF-A-004", "SLA Response Time Standards",
         "Acme's SLA commitments: P1 issues are acknowledged within 15 minutes and resolved within 4 hours. "
         "P2 issues are acknowledged within 1 hour and resolved within 8 hours. P3 and P4 issues are handled "
         "within standard business hours. SLA breaches trigger automatic notifications to the account manager "
         "and are tracked in the monthly executive dashboard.",
         ["group:acme-support", "group:acme-agents", "tenant:acme"], "en-US"),

        ("SF-A-005", "Refund Policy for Acme Enterprise",
         "Enterprise customers with active annual contracts are eligible for pro-rated refunds within 90 days "
         "of activation. Refund requests must be submitted via the enterprise support portal with a signed "
         "cancellation form. Processing takes 10-15 business days. Customers who received a discount at "
         "activation may have the discount amount deducted from the refund.",
         ["group:acme-billing", "group:acme-enterprise", "tenant:acme"], "en-US"),

        # PARAPHRASE DEMO — uses ONLY formal billing vocabulary.
        # BM25 returns 0 results for "billing dispute", "refund", "wrong charge", "customer complaint".
        # Jina v5 semantic query for those same terms surfaces this doc because the embedding space
        # understands: "fee adjudication" ≈ dispute, "credit offset" ≈ refund, "rate differential" ≈ overcharge.
        # Also contains INV-2026-84732 for the exact-reference hybrid demo.
        ("SF-A-006", "Billing Adjustment Fee Schedule — Acme",
         "The following fee adjudication schedule governs pro-rata billing reconciliation for all ACME "
         "subscription tiers. Reference invoice INV-2026-84732 applies the following contractual rate "
         "adjustments: Standard tier contracts are subject to a 5% variance tolerance before recalibration "
         "is triggered. When the invoiced amount exceeds the contracted rate differential by more than 10%, "
         "a credit offset is processed within the subsequent billing cycle. Tier 2 and Enterprise accounts "
         "receive priority recalibration processing, with credit issuance confirmed within 3 business days. "
         "All fee schedule amendments must be logged by the billing controller with case ID and effective date.",
         ["group:acme-billing", "group:acme-enterprise", "tenant:acme"], "en-US"),

        # CHUNKING DEMO — table-structured content with numbered steps.
        # Hard chunking (midpoint character split) cuts the matrix mid-row:
        #   chunk-0: full content (steps 1-2 + first half of table rows)
        #   chunk-1: second half of table rows with no header + steps 3-4
        # chunk-1 is returned when agent queries a lower-tier row — no header context, unusable.
        # Jina semantic auto-chunking keeps tables together; procedures are never split mid-step.
        ("SF-A-007", "Customer Tier Resolution Matrix — Escalation Decision Procedure",
         "Agent Decision Matrix: this procedure governs how agents route escalation decisions mid-call. "
         "Step 1 — Identify the customer tier from the account profile. "
         "Step 2 — Locate the applicable resolution pathway in the matrix below: "
         "| Tier | Issue Type | Resolution Authority | Credit Limit | SLA | "
         "| Standard | Billing | Billing Team | $100 | 48h | "
         "| Premium | Billing | Senior Agent | $500 | 24h | "
         "| Enterprise | Billing | Billing Director | Unlimited | 4h | "
         "| Standard | Technical | L1 Support | None | 72h | "
         "| Premium | Technical | L2 Support | None | 24h | "
         "| Enterprise | Technical | Engineering | None | 2h | "
         "Step 3 — Apply the resolution authority and credit limits from the matched matrix row. "
         "Step 4 — Document the tier-routing decision in Salesforce with the matrix row reference and agent ID.",
         ["group:acme-support", "group:acme-billing", "tenant:acme"], "en-US"),
    ]

    sf_globalnet = [
        ("SF-GN-001", "Billing Dispute Resolution — GlobalNet",
         "GlobalNet agents must verify the customer's payment history before initiating a dispute investigation. "
         "Disputes involving amounts over $1,000 are automatically escalated to the Revenue Assurance team. "
         "All credits must be approved by the billing supervisor and reflected in the next statement. Customers "
         "must be notified of the outcome within 5 business days.",
         ["group:globalnet-billing", "tenant:globalnet"], "en-US"),

        ("SF-GN-002", "Service Restoration Procedure",
         "When a GlobalNet service outage is detected, the NOC team opens a P1 incident and notifies account "
         "managers within 30 minutes. Customer-facing status updates are posted to the status page every "
         "60 minutes until resolution. Upon restoration, a root-cause analysis is delivered to affected "
         "enterprise accounts within 5 business days.",
         ["group:globalnet-noc", "group:globalnet-agents", "tenant:globalnet"], "en-US"),

        ("SF-GN-003", "Customer Onboarding Knowledge Article",
         "New GlobalNet customers receive a dedicated onboarding specialist for the first 90 days. "
         "Onboarding includes a kickoff call, configuration review, and two training sessions. Success "
         "milestones are tracked in the customer health scorecard. At day 60, the CSM reviews usage metrics "
         "and identifies expansion opportunities.",
         ["group:globalnet-csm", "tenant:globalnet"], "es-419"),

        ("SF-GN-004", "Carrier Number Portability FAQ",
         "Customers requesting number porting must submit a signed LOA (Letter of Authorization) and a recent "
         "phone bill. Porting typically completes in 5-10 business days for US numbers and 15-20 days for "
         "international numbers. During the porting window, both old and new services remain active. Customers "
         "are notified via SMS when the port is confirmed.",
         ["group:globalnet-porting", "group:globalnet-agents", "tenant:globalnet"], "en-US"),

        ("SF-GN-005", "Proactive Outage Communication Template",
         "When GlobalNet declares a major outage, the following communication template must be used for all "
         "customer-facing channels: Subject: [ACTION REQUIRED] Service Disruption — GlobalNet. Body must "
         "include: incident ID, services affected, estimated resolution time, and a direct support contact. "
         "All outgoing communications must be approved by the Communications Director before release.",
         ["group:globalnet-comms", "group:globalnet-managers", "tenant:globalnet"], "fr-FR"),

        # MULTILINGUAL DEMO — full Spanish KB article for GlobalNet.
        # Demo moment: agent types Spanish query → BM25 finds this doc (exact Spanish match).
        # Second query: English semantic query → also finds this doc cross-lingually via Jina v5.
        # Florian confirmed Jina v5 supports 119 languages in the same embedding space —
        # no separate Spanish index, no translation layer, one model handles both directions.
        ("SF-GN-006", "Política de Resolución de Disputas de Cargo — GlobalNet",
         "Cuando un cliente reporta una discrepancia en su factura, el agente debe verificar el historial "
         "de pagos de los últimos tres meses en el sistema de gestión de clientes. Las disputas que "
         "involucren montos superiores a $1,000 se escalan automáticamente al equipo de Aseguramiento de "
         "Ingresos. Todos los créditos deben ser aprobados por el supervisor de facturación y reflejarse "
         "en el siguiente estado de cuenta. El cliente debe ser notificado del resultado dentro de 5 días "
         "hábiles. Para disputas en mercados de habla hispana, el agente debe documentar la interacción "
         "en español en el sistema CRM y asegurarse de que el número de caso se vincule al perfil del cliente.",
         ["group:globalnet-billing", "tenant:globalnet"], "es-419"),
    ]

    for doc_id, title, content, principals, locale in sf_acme + sf_globalnet:
        tenant = "acme" if "-A-" in doc_id else "globalnet"
        for chunk_num in range(2):
            chunk_id = f"{doc_id}-chunk-{chunk_num}"
            docs.append({
                "tenant_id": tenant,
                "source": "salesforce",
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "title": title,
                "content": content if chunk_num == 0 else content[len(content)//2:],
                "locale": locale,
                "acl": {"principals": principals},
                "source_url": f"https://salesforce.com/articles/{doc_id.lower().replace('-', '_')}",
                "last_synced_at": _ts(hours_ago=6),
                "@timestamp": _ts(hours_ago=6),
                **_apply_meta(doc_id, "salesforce"),
            })

    # ── Confluence ──────────────────────────────────────────────────────────
    conf_acme = [
        ("CONF-A-001", "API Authentication Guide — Acme Platform",
         "Acme's public API uses OAuth 2.0 with PKCE for all client applications. Access tokens expire after "
         "3600 seconds and must be refreshed using the refresh_token grant. API keys are available for "
         "server-to-server integrations and are scoped to specific endpoints. Rate limits are enforced at "
         "1,000 requests per minute per tenant with burst allowance of 200 requests.",
         ["group:acme-engineering", "group:acme-platform", "tenant:acme"], "en-US"),

        ("CONF-A-002", "Deployment Runbook — Production",
         "All production deployments must follow the change management process: submit a CR ticket at least "
         "48 hours before the deployment window. Deployments are scheduled for Tuesday and Thursday between "
         "02:00-04:00 UTC. A rollback plan must be documented and tested in staging before approval. "
         "Post-deployment smoke tests are mandatory and must pass within 30 minutes of go-live.",
         ["group:acme-sre", "group:acme-engineering", "tenant:acme"], "en-US"),

        ("CONF-A-003", "Incident Management Runbook",
         "Incident severity is classified P1 through P4 based on customer impact. P1 requires immediate "
         "paging of the on-call SRE and a war-room Slack channel within 5 minutes. The incident commander "
         "is responsible for communication, remediation coordination, and timeline documentation. A "
         "post-mortem must be completed within 5 business days of P1 and P2 incidents.",
         ["group:acme-sre", "tenant:acme"], "en-US"),

        ("CONF-A-004", "Elasticsearch Index Strategy",
         "Acme uses Elastic Cloud for all search and observability workloads. Index lifecycle policies "
         "are configured with a 30-day hot phase, 90-day warm phase, and 365-day cold phase. ELSER is "
         "enabled on all customer-facing knowledge base indices. Aliases are used for zero-downtime "
         "reindexing. All indices follow the naming convention: {team}-{domain}-{YYYY.MM}.",
         ["group:acme-platform", "group:acme-engineering", "tenant:acme"], "en-US"),

        ("CONF-A-005", "Data Pipeline Architecture",
         "Acme's event streaming platform is built on Apache Kafka with 14-day retention. All events "
         "are schema-validated using Confluent Schema Registry before ingestion. Downstream consumers "
         "include Elasticsearch (via Logstash), the data warehouse (via Kafka Connect), and the ML "
         "feature store. Failed events are routed to a dead-letter topic and retried three times before "
         "alerting the on-call engineer.",
         ["group:acme-data", "group:acme-engineering", "tenant:acme"], "en-US"),
    ]

    conf_globalnet = [
        ("CONF-GN-001", "API Authentication — GlobalNet Developer Portal",
         "GlobalNet external APIs are secured with mutual TLS for partner integrations and API key "
         "authentication for third-party developers. API keys are provisioned through the developer portal "
         "and must be rotated every 90 days. Webhooks use HMAC-SHA256 signatures with a shared secret. "
         "All API calls are rate-limited to 500 requests per minute per key.",
         ["group:globalnet-engineering", "tenant:globalnet"], "en-US"),

        ("CONF-GN-002", "Network Provisioning Runbook",
         "New customer circuits are provisioned in the GlobalNet OSS within 2 hours of order confirmation. "
         "The provisioning engineer must validate BGP peering, QoS policies, and redundancy paths before "
         "marking the order complete. High-availability customers require dual-path verification. "
         "All provisioning actions are logged in the change management system with circuit ID and timestamp.",
         ["group:globalnet-noc", "group:globalnet-engineering", "tenant:globalnet"], "en-US"),

        ("CONF-GN-003", "Disaster Recovery Runbook",
         "GlobalNet's RTO is 4 hours and RPO is 1 hour for all Tier 1 services. DR failover is triggered "
         "by the NOC director after a confirmed site failure. The failover checklist includes: DNS cutover, "
         "database replica promotion, BGP route advertisement, and customer notification. Monthly DR drills "
         "are mandatory and results are reported to the CTO.",
         ["group:globalnet-sre", "group:globalnet-noc", "tenant:globalnet"], "en-US"),

        ("CONF-GN-004", "RTBF Compliance Procedure",
         "Upon receiving a Right to be Forgotten request, the Privacy team opens a JIRA ticket with a 30-day "
         "SLA. Data must be deleted from all primary stores, search indices, backup snapshots (at next rotation), "
         "and third-party processors within the SLA. Elasticsearch deletion is handled via the Delete-by-Query "
         "API targeting the customer's tenant_id. Confirmation is sent to the customer with a signed deletion "
         "certificate.",
         ["group:globalnet-privacy", "group:globalnet-compliance", "tenant:globalnet"], "fr-FR"),

        ("CONF-GN-005", "Monitoring and Alerting Standards",
         "All GlobalNet production services must emit RED metrics (Rate, Errors, Duration) to the central "
         "Elastic Observability cluster. Alerting thresholds: error rate > 1% for 5 minutes triggers P2, "
         "> 5% triggers P1. Latency alerts fire when p99 exceeds 500ms for 10 consecutive minutes. "
         "Runbooks must be linked in every alert definition and reviewed quarterly.",
         ["group:globalnet-sre", "group:globalnet-engineering", "tenant:globalnet"], "en-US"),
    ]

    for doc_id, title, content, principals, locale in conf_acme + conf_globalnet:
        tenant = "acme" if "-A-" in doc_id else "globalnet"
        for chunk_num in range(2):
            chunk_id = f"{doc_id}-chunk-{chunk_num}"
            docs.append({
                "tenant_id": tenant,
                "source": "confluence",
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "title": title,
                "content": content if chunk_num == 0 else content[len(content)//2:],
                "locale": locale,
                "acl": {"principals": principals},
                "source_url": f"https://confluence.{tenant}.internal/display/KB/{doc_id}",
                "last_synced_at": _ts(hours_ago=2),
                "@timestamp": _ts(hours_ago=2),
                **_apply_meta(doc_id, "confluence"),
            })

    return docs


# ---------------------------------------------------------------------------
# Additional tenant content (closes Gap 1 — 10 tenants had no kb_content)
# ---------------------------------------------------------------------------

def _build_additional_tenant_docs() -> List[Dict[str, Any]]:
    """Return 3 kb_content docs per additional tenant so all 12 tenants have content."""
    docs: List[Dict[str, Any]] = []

    # (tenant_id, source, locale, [(doc_id, title, content, principals)])
    tenant_content = [
        ("apextel", "sharepoint", "en-US", [
            ("APX-SP-001", "Number Porting SLA Policy",
             "ApexTel commits to number porting completion within 2 business days for standard residential requests and 5 business days for enterprise multi-line requests. Failed ports must be re-submitted within 24 hours with a corrected NPI/NXX code. Agents must log every porting event in the CRM with the carrier rejection code.",
             ["group:apextel-support", "tenant:apextel"]),
            ("APX-SP-002", "Outage Communication Procedure",
             "When a network outage affects more than 100 customers, ApexTel's Communications team must send proactive SMS alerts within 15 minutes of incident declaration. Email follow-up is mandatory within 1 hour. Customer-facing status page must be updated every 30 minutes until resolution.",
             ["group:apextel-support", "group:apextel-noc", "tenant:apextel"]),
            ("APX-SP-003", "Enterprise SLA Escalation Runbook",
             "Enterprise customers with SLA-GOLD or SLA-PLATINUM contracts are entitled to a dedicated Technical Account Manager. TAMs must be notified within 10 minutes of a P1 incident affecting the customer. Compensation credits are automatically calculated at 10% of monthly fee per hour of downtime beyond the SLA threshold.",
             ["group:apextel-tier2", "tenant:apextel"]),
        ]),
        ("bluewave", "sharepoint", "fr-FR", [
            ("BW-SP-001", "KYC Verification Procedure — Bluewave Capital",
             "All new client onboarding at Bluewave Capital requires completion of Know Your Customer verification within 3 business days. Required documents: government-issued ID, proof of address (less than 3 months old), and source of funds declaration for accounts over €100,000. AML screening is mandatory for all clients regardless of account size.",
             ["group:bluewave-compliance", "tenant:bluewave"]),
            ("BW-SP-002", "Fraud Alert Response Protocol",
             "When a fraud alert is triggered by the transaction monitoring system, the assigned analyst has 2 hours to review and classify the alert. Confirmed fraud events require immediate account freeze and notification to the client via secure message. Regulatory reporting to the FCA must be completed within 24 hours of fraud confirmation.",
             ["group:bluewave-fraud", "group:bluewave-compliance", "tenant:bluewave"]),
            ("BW-SP-003", "Client Data Retention Policy",
             "Bluewave Capital retains client transaction records for 7 years in compliance with FCA regulations. Personal data of closed accounts is anonymised after the mandatory retention period. GDPR Article 17 deletion requests are processed within 30 days, with exceptions for legally mandated retention obligations.",
             ["group:bluewave-compliance", "group:bluewave-privacy", "tenant:bluewave"]),
        ]),
        ("meridian", "confluence", "en-US", [
            ("MER-CF-001", "Clinical Data Access Policy",
             "Access to patient clinical records in Meridian Health's Knowledge Base is restricted to licensed clinicians with active patient relationships. All access events are logged to the HIPAA audit trail. Agents supporting clinical queries must complete annual HIPAA training and sign the confidentiality agreement before being granted access.",
             ["group:meridian-clinical", "tenant:meridian"]),
            ("MER-CF-002", "HIPAA Breach Notification Procedure",
             "If a breach of unsecured PHI is discovered, Meridian Health must notify affected patients within 60 days. Breaches affecting more than 500 individuals in a state require media notice. HHS must be notified immediately for breaches over 500 individuals. The Privacy Officer must be engaged within 1 hour of breach discovery.",
             ["group:meridian-compliance", "group:meridian-privacy", "tenant:meridian"]),
            ("MER-CF-003", "Patient Consent Management",
             "Meridian Health obtains explicit written consent before sharing patient records with third-party providers. Consent records are stored in the Patient Consent Management System with a 10-year retention period. Patients may withdraw consent at any time, triggering a 72-hour data access review and update cycle.",
             ["group:meridian-clinical", "group:meridian-compliance", "tenant:meridian"]),
        ]),
        ("fortis", "salesforce", "de-DE", [
            ("FOR-SF-001", "Credit Application Processing Guide",
             "Fortis Bank processes retail credit applications within 48 hours and business credit applications within 5 business days. Applications exceeding €500,000 require review by the Credit Committee. Agents must document all application decisions with the risk classification code and the primary rejection reason where applicable.",
             ["group:fortis-credit", "tenant:fortis"]),
            ("FOR-SF-002", "Anti-Money Laundering Escalation",
             "Suspicious transaction alerts generated by Fortis's AML monitoring system must be reviewed within 4 hours. Confirmed suspicious activity reports (SARs) must be filed with BaFin within 24 hours. Customer must not be informed of the SAR filing. Account freeze can be applied by the AML team without management approval for confirmed high-risk transactions.",
             ["group:fortis-compliance", "group:fortis-aml", "tenant:fortis"]),
            ("FOR-SF-003", "SEPA Payment Dispute Resolution",
             "SEPA direct debit disputes must be resolved within 8 weeks of the disputed transaction date. Agents verify the mandate reference and transaction history before initiating a chargeback. Refunds are processed within 3 business days of dispute confirmation. Recurring SEPA dispute patterns trigger an account review.",
             ["group:fortis-support", "tenant:fortis"]),
        ]),
        ("carebridge", "sharepoint", "en-US", [
            ("CB-SP-001", "Telehealth Session Support Guide",
             "CareBridge agents supporting telehealth sessions must verify patient identity using two-factor authentication before granting session access. Technical issues during active clinical sessions are P1 incidents requiring immediate escalation to the platform engineering team. All session disruptions must be logged with duration and patient impact.",
             ["group:carebridge-support", "tenant:carebridge"]),
            ("CB-SP-002", "Prescription Refill Escalation Procedure",
             "Prescription refill requests requiring physician review are escalated to the clinical queue within 4 hours. Controlled substance refill requests require direct physician approval and cannot be auto-approved. Agents must verify insurance coverage before confirming refill eligibility.",
             ["group:carebridge-clinical", "tenant:carebridge"]),
            ("CB-SP-003", "Patient Privacy Complaint Handling",
             "All patient privacy complaints are logged in the HIPAA incident tracking system within 2 hours of receipt. The Privacy Officer must be notified of any complaint alleging unauthorised disclosure of PHI. Resolution must be communicated to the patient within 30 days. Repeat complaints from the same patient trigger a formal investigation.",
             ["group:carebridge-compliance", "tenant:carebridge"]),
        ]),
        ("nexustel", "confluence", "de-DE", [
            ("NXT-CF-001", "Roaming Agreement Policy — EU Markets",
             "NexusTel customers roaming within the EU are covered by the EU Roaming Regulation at domestic rates. Roaming outside the EU is charged at published international rates. Agents must advise customers of applicable rates before international travel. Daily roaming caps of €50 apply unless the customer has opted out in writing.",
             ["group:nexustel-support", "tenant:nexustel"]),
            ("NXT-CF-002", "Network Maintenance Window Policy",
             "NexusTel schedules maintenance windows between 02:00 and 05:00 CET on Tuesdays and Thursdays. Emergency maintenance can be triggered at any time with a minimum 30-minute customer notification. Enterprise customers with SLA commitments receive 72-hour advance notice for planned maintenance.",
             ["group:nexustel-noc", "group:nexustel-support", "tenant:nexustel"]),
            ("NXT-CF-003", "5G Rollout Customer FAQ",
             "NexusTel's 5G network covers 85% of urban areas across Germany, Austria, and Switzerland. Customers must have a 5G-compatible device and a 5G-enabled plan to access the network. Speed guarantees under 5G: minimum 100 Mbps downlink in covered areas. Coverage maps are updated monthly on the NexusTel website.",
             ["group:nexustel-support", "tenant:nexustel"]),
        ]),
        ("primevest", "salesforce", "en-SG", [
            ("PV-SF-001", "MAS Regulatory Compliance Policy",
             "PrimeVest Asset Management operates under the Monetary Authority of Singapore's licensing framework. All investment advice must be provided by MAS-licensed representatives. Client suitability assessments are mandatory before recommending investment products. Documentation must be retained for a minimum of 5 years.",
             ["group:primevest-compliance", "tenant:primevest"]),
            ("PV-SF-002", "Client Portfolio Review Procedure",
             "Annual portfolio reviews are mandatory for all PrimeVest clients. Reviews must document current asset allocation, performance against benchmark, and any recommended changes. Reviews for clients with assets over SGD 1M require sign-off by the Chief Investment Officer before distribution.",
             ["group:primevest-advisors", "tenant:primevest"]),
            ("PV-SF-003", "Trade Execution and Best Execution Policy",
             "PrimeVest is required to take all sufficient steps to obtain the best possible result for client orders. Best execution factors include price, costs, speed, and likelihood of execution. All trades are logged with timestamps and execution venue. Quarterly best execution reports are reviewed by the Compliance Committee.",
             ["group:primevest-trading", "group:primevest-compliance", "tenant:primevest"]),
        ]),
        ("alphacare", "sharepoint", "en-US", [
            ("ALC-SP-001", "Emergency Department Triage Protocol",
             "AlphaCare Medical Group emergency departments follow the Emergency Severity Index (ESI) 5-level triage system. ESI Level 1 (immediate life threat) requires physician response within 0 minutes. Level 2 (high risk) within 10 minutes. Level 3 within 30 minutes. Triage nurses must document ESI level, chief complaint, and vital signs in the EMR.",
             ["group:alphacare-clinical", "tenant:alphacare"]),
            ("ALC-SP-002", "Medical Records Release Policy",
             "AlphaCare releases medical records within 30 days of a valid written request. HIPAA-authorised disclosures can be processed within 24 hours. Records for legal proceedings require review by the Legal team before release. Digital records are provided via the patient portal; physical copies are provided at cost per page.",
             ["group:alphacare-records", "group:alphacare-compliance", "tenant:alphacare"]),
            ("ALC-SP-003", "Informed Consent Procedure",
             "All AlphaCare patients must provide informed consent before surgical procedures, invasive diagnostics, and research participation. Consent forms must be signed at least 24 hours before elective procedures. Emergency exceptions are documented by two attending physicians. Translators are provided at no cost for non-English-speaking patients.",
             ["group:alphacare-clinical", "tenant:alphacare"]),
        ]),
        ("vortextel", "salesforce", "en-SG", [
            ("VTX-SF-001", "APAC Roaming Interconnect Policy",
             "VortexTel maintains bilateral roaming agreements with 42 operators across the APAC region. Preferred roaming partners are listed in the operator portal and receive preferential routing. Disputed roaming charges between operators are resolved within 60 days through the GSMA dispute resolution process.",
             ["group:vortextel-wholesale", "tenant:vortextel"]),
            ("VTX-SF-002", "Enterprise IoT Connectivity SLA",
             "VortexTel's enterprise IoT contracts guarantee 99.95% uptime for mission-critical device connectivity. SLA breaches trigger automatic credit calculation at 10% of monthly connectivity fee per hour of downtime. IoT platform incidents are classified separately from consumer network incidents for SLA tracking purposes.",
             ["group:vortextel-enterprise", "group:vortextel-support", "tenant:vortextel"]),
            ("VTX-SF-003", "Spectrum Licence Compliance Procedure",
             "VortexTel holds spectrum licences in Singapore, Malaysia, Thailand, and the Philippines. Annual spectrum usage reports must be submitted to each national regulator. Out-of-band emissions must be monitored monthly and reported quarterly. Licence renewal applications must be submitted 12 months before expiry.",
             ["group:vortextel-regulatory", "tenant:vortextel"]),
        ]),
        ("eurofinance", "confluence", "fr-FR", [
            ("EF-CF-001", "MiFID II Trade Reporting Procedure",
             "EuroFinance Holdings is required to report all eligible transactions to an Approved Reporting Mechanism (ARM) within the transaction reporting deadline. Reports must include LEI codes for all counterparties, ISIN codes for all instruments, and UTC timestamps. Failed reports must be corrected and resubmitted within 24 hours of failure notification.",
             ["group:eurofinance-compliance", "group:eurofinance-reporting", "tenant:eurofinance"]),
            ("EF-CF-002", "GDPR Data Subject Rights Procedure",
             "EuroFinance processes GDPR data subject access requests within 30 days. Identity verification is mandatory before releasing personal data. Right to erasure requests are reviewed by the Legal and Compliance teams. Data portability requests are fulfilled in machine-readable format (JSON or CSV) within 30 days.",
             ["group:eurofinance-privacy", "group:eurofinance-compliance", "tenant:eurofinance"]),
            ("EF-CF-003", "Liquidity Risk Management Policy",
             "EuroFinance maintains a Liquidity Coverage Ratio (LCR) of at least 110% in compliance with CRR requirements. Daily liquidity reports are submitted to the risk management committee. Stress testing scenarios are run monthly to validate the liquidity buffer under adverse market conditions. ILAAP documentation is updated annually.",
             ["group:eurofinance-risk", "tenant:eurofinance"]),
        ]),
    ]

    for tenant_id, source, locale, articles in tenant_content:
        for doc_id, title, content, principals in articles:
            docs.append({
                "tenant_id":      tenant_id,
                "source":         source,
                "doc_id":         doc_id,
                "chunk_id":       f"{doc_id}-chunk-0",
                "title":          title,
                "content":        content,
                "locale":         locale,
                "acl":            {"principals": principals},
                "source_url":     f"https://{source}.{tenant_id}.internal/KB/{doc_id}",
                "last_synced_at": _ts(hours_ago=1),
                "@timestamp":     _ts(hours_ago=1),
                **_apply_meta(doc_id, source),
            })

    return docs


# ---------------------------------------------------------------------------
# Sync event generator
# ---------------------------------------------------------------------------

def _build_sync_events() -> List[Dict[str, Any]]:
    """Return ~30 kb_sync_events covering all event_type values."""
    events: List[Dict[str, Any]] = []

    # Upsert events (most common)
    upserts = [
        ("sharepoint", "acme",      "HR-001",      "conn-sp-acme-01",  "us-east-1"),
        ("sharepoint", "acme",      "HR-002",      "conn-sp-acme-01",  "us-east-1"),
        ("sharepoint", "acme",      "HR-003",      "conn-sp-acme-01",  "us-east-1"),
        ("sharepoint", "globalnet", "HR-GN-001",   "conn-sp-gn-01",    "eu-west-1"),
        ("sharepoint", "globalnet", "HR-GN-002",   "conn-sp-gn-01",    "eu-west-1"),
        ("salesforce", "acme",      "SF-A-001",    "conn-sf-acme-01",  "us-east-1"),
        ("salesforce", "acme",      "SF-A-002",    "conn-sf-acme-01",  "us-east-1"),
        ("salesforce", "acme",      "SF-A-003",    "conn-sf-acme-01",  "us-east-1"),
        ("salesforce", "globalnet", "SF-GN-001",   "conn-sf-gn-01",    "eu-west-1"),
        ("salesforce", "globalnet", "SF-GN-002",   "conn-sf-gn-01",    "eu-west-1"),
        ("confluence", "acme",      "CONF-A-001",  "conn-cf-acme-01",  "us-east-1"),
        ("confluence", "acme",      "CONF-A-002",  "conn-cf-acme-01",  "us-east-1"),
        ("confluence", "globalnet", "CONF-GN-001", "conn-cf-gn-01",    "eu-west-1"),
        ("confluence", "globalnet", "CONF-GN-002", "conn-cf-gn-01",    "eu-west-1"),
        ("confluence", "globalnet", "CONF-GN-004", "conn-cf-gn-01",    "eu-west-1"),
    ]
    for idx, (source, tenant, doc_id, connector_id, region) in enumerate(upserts):
        events.append({
            "@timestamp":   _ts(hours_ago=idx),
            "tenant_id":    tenant,
            "source":       source,
            "event_type":   "upsert",
            "doc_id":       doc_id,
            "status":       "success",
            "error_message": None,
            "retry_count":  0,
            "connector_id": connector_id,
            "region":       region,
        })

    # Delete events — with RTBF propagation_confirmed audit trail
    # Three states demonstrated: confirmed (True), pending (False), in-progress (False + timestamp)
    rtbf_deletes = [
        # (source, tenant, doc_id, connector_id, region, propagation_confirmed, rtbf_request_id, days_ago)
        ("sharepoint", "acme",      "HR-OLD-001",   "conn-sp-acme-01", "us-east-1",  True,  "RTBF-2026-001", 3),
        ("salesforce", "globalnet", "SF-GN-OLD-99", "conn-sf-gn-01",   "eu-west-1",  True,  "RTBF-2026-002", 2),
        ("confluence", "acme",      "CONF-A-OLD-3", "conn-cf-acme-01", "us-east-1",  True,  "RTBF-2026-003", 1),
        ("sharepoint", "globalnet", "HR-GN-OLD-07", "conn-sp-gn-01",   "eu-west-1",  False, "RTBF-2026-004", 0),  # pending
        ("salesforce", "acme",      "SF-A-OLD-12",  "conn-sf-acme-01", "us-east-1",  False, "RTBF-2026-005", 0),  # in-progress
    ]
    for source, tenant, doc_id, connector_id, region, confirmed, rtbf_id, days_ago in rtbf_deletes:
        event: Dict[str, Any] = {
            "@timestamp":            _ts(days_ago=days_ago, hours_ago=1),
            "tenant_id":             tenant,
            "source":                source,
            "event_type":            "delete",
            "doc_id":                doc_id,
            "status":                "success" if confirmed else "pending",
            "error_message":         None,
            "retry_count":           0,
            "connector_id":          connector_id,
            "region":                region,
            "propagation_confirmed": confirmed,
            "gdpr_article17":        True,
            "rtbf_request_id":       rtbf_id,
        }
        if confirmed:
            event["propagation_timestamp"] = _ts(days_ago=days_ago)
        events.append(event)

    # Retry events
    events.append({
        "@timestamp":    _ts(hours_ago=3),
        "tenant_id":     "acme",
        "source":        "sharepoint",
        "event_type":    "retry",
        "doc_id":        "HR-005",
        "status":        "success",
        "error_message": "Connection timeout on first attempt",
        "retry_count":   1,
        "connector_id":  "conn-sp-acme-01",
        "region":        "us-east-1",
    })
    events.append({
        "@timestamp":    _ts(hours_ago=5),
        "tenant_id":     "globalnet",
        "source":        "confluence",
        "event_type":    "retry",
        "doc_id":        "CONF-GN-003",
        "status":        "success",
        "error_message": "503 Service Unavailable — Confluence Cloud",
        "retry_count":   2,
        "connector_id":  "conn-cf-gn-01",
        "region":        "eu-west-1",
    })

    # Rate-limit event
    events.append({
        "@timestamp":    _ts(hours_ago=7),
        "tenant_id":     "acme",
        "source":        "salesforce",
        "event_type":    "rate_limit",
        "doc_id":        "SF-A-004",
        "status":        "deferred",
        "error_message": "Salesforce API rate limit exceeded — backoff 60s",
        "retry_count":   0,
        "connector_id":  "conn-sf-acme-01",
        "region":        "us-east-1",
    })

    # ── sync_failed events (closes Gap 3 — shows connector failure story) ──
    # Scenario: GlobalNet Salesforce connector (already marked degraded in connector_registry)
    # had a multi-hour failure window with 3 failed attempts before recovery.
    sync_failures = [
        # (source, tenant, doc_id, connector_id, region, retry_count, error_message, hours_ago, status)
        ("salesforce", "globalnet", "SF-GN-003", "conn-sf-gn-01", "eu-west-1", 3,
         "OAuth token refresh failed: 401 Unauthorized — service account password expired",
         8, "failed"),
        ("salesforce", "globalnet", "SF-GN-004", "conn-sf-gn-01", "eu-west-1", 3,
         "OAuth token refresh failed: 401 Unauthorized — service account password expired",
         7, "failed"),
        ("salesforce", "globalnet", "SF-GN-005", "conn-sf-gn-01", "eu-west-1", 3,
         "OAuth token refresh failed: 401 Unauthorized — service account password expired",
         6, "failed"),
        ("salesforce", "acme",      "SF-A-003",  "conn-sf-acme-01", "us-east-1", 2,
         "Connection timeout after 30s — Salesforce endpoint unreachable",
         12, "failed"),
        ("sharepoint", "globalnet", "HR-GN-004", "conn-sp-gn-01", "eu-west-1", 1,
         "HTTP 503 Service Unavailable — SharePoint Cloud maintenance window",
         18, "failed"),
    ]
    for source, tenant, doc_id, connector_id, region, retries, error_msg, hours_ago, status in sync_failures:
        events.append({
            "@timestamp":    _ts(hours_ago=hours_ago),
            "tenant_id":     tenant,
            "source":        source,
            "event_type":    "sync_failed",
            "doc_id":        doc_id,
            "status":        status,
            "error_message": error_msg,
            "retry_count":   retries,
            "connector_id":  connector_id,
            "region":        region,
        })

    # Recovery events — show that the GlobalNet Salesforce connector recovered after token rotation
    events.append({
        "@timestamp":    _ts(hours_ago=5),
        "tenant_id":     "globalnet",
        "source":        "salesforce",
        "event_type":    "upsert",
        "doc_id":        "SF-GN-003",
        "status":        "success",
        "error_message": None,
        "retry_count":   0,
        "connector_id":  "conn-sf-gn-01",
        "region":        "eu-west-1",
    })
    events.append({
        "@timestamp":    _ts(hours_ago=4),
        "tenant_id":     "globalnet",
        "source":        "salesforce",
        "event_type":    "upsert",
        "doc_id":        "SF-GN-004",
        "status":        "success",
        "error_message": None,
        "retry_count":   0,
        "connector_id":  "conn-sf-gn-01",
        "region":        "eu-west-1",
    })

    # Audit events
    audits = [
        ("sharepoint", "acme",      "HR-001",      "conn-sp-acme-01",  "us-east-1"),
        ("salesforce", "globalnet", "SF-GN-001",   "conn-sf-gn-01",    "eu-west-1"),
        ("confluence", "acme",      "CONF-A-001",  "conn-cf-acme-01",  "us-east-1"),
        ("sharepoint", "globalnet", "HR-GN-003",   "conn-sp-gn-01",    "eu-west-1"),
        ("confluence", "globalnet", "CONF-GN-004", "conn-cf-gn-01",    "eu-west-1"),
        ("salesforce", "acme",      "SF-A-005",    "conn-sf-acme-01",  "us-east-1"),
    ]
    for source, tenant, doc_id, connector_id, region in audits:
        events.append({
            "@timestamp":    _ts(days_ago=2),
            "tenant_id":     tenant,
            "source":        source,
            "event_type":    "audit",
            "doc_id":        doc_id,
            "status":        "logged",
            "error_message": None,
            "retry_count":   0,
            "connector_id":  connector_id,
            "region":        region,
        })

    return events


# ---------------------------------------------------------------------------
# Connector registry data
# ---------------------------------------------------------------------------

def _build_connector_registry() -> List[Dict[str, Any]]:
    """Return connector_registry documents — one per connector per tenant, 3 source types + ServiceNow."""
    return [
        # ACME — us-east-1
        {"connector_id": "conn-sp-acme-01",  "tenant_id": "acme",      "source_type": "SharePoint",  "region": "us-east-1", "sync_schedule": "*/15 * * * *", "last_sync_cursor": _ts(hours_ago=1),  "last_successful_sync": _ts(hours_ago=1),  "status": "active",   "docs_synced_total": 1840, "avg_sync_duration_ms": 4200,  "failure_rate_pct": 0.01, "last_error": None},
        {"connector_id": "conn-sf-acme-01",  "tenant_id": "acme",      "source_type": "Salesforce",  "region": "us-east-1", "sync_schedule": "*/15 * * * *", "last_sync_cursor": _ts(hours_ago=2),  "last_successful_sync": _ts(hours_ago=2),  "status": "active",   "docs_synced_total": 3210, "avg_sync_duration_ms": 3800,  "failure_rate_pct": 0.02, "last_error": None},
        {"connector_id": "conn-sn-acme-01",  "tenant_id": "acme",      "source_type": "ServiceNow",  "region": "us-east-1", "sync_schedule": "*/30 * * * *", "last_sync_cursor": _ts(hours_ago=1),  "last_successful_sync": _ts(hours_ago=1),  "status": "active",   "docs_synced_total": 712,  "avg_sync_duration_ms": 6100,  "failure_rate_pct": 0.00, "last_error": None},
        # GlobalNet — eu-west-1
        {"connector_id": "conn-sp-gn-01",    "tenant_id": "globalnet", "source_type": "SharePoint",  "region": "eu-west-1", "sync_schedule": "*/15 * * * *", "last_sync_cursor": _ts(hours_ago=1),  "last_successful_sync": _ts(hours_ago=1),  "status": "active",   "docs_synced_total": 2100, "avg_sync_duration_ms": 4500,  "failure_rate_pct": 0.01, "last_error": None},
        {"connector_id": "conn-sf-gn-01",    "tenant_id": "globalnet", "source_type": "Salesforce",  "region": "eu-west-1", "sync_schedule": "*/15 * * * *", "last_sync_cursor": _ts(hours_ago=4),  "last_successful_sync": _ts(hours_ago=5),  "status": "degraded", "docs_synced_total": 890,  "avg_sync_duration_ms": 8900,  "failure_rate_pct": 0.12, "last_error": "Salesforce API rate limit exceeded — backoff 60s"},
        {"connector_id": "conn-cf-gn-01",    "tenant_id": "globalnet", "source_type": "Confluence",  "region": "eu-west-1", "sync_schedule": "0 * * * *",    "last_sync_cursor": _ts(hours_ago=2),  "last_successful_sync": _ts(hours_ago=2),  "status": "active",   "docs_synced_total": 421,  "avg_sync_duration_ms": 5300,  "failure_rate_pct": 0.03, "last_error": None},
        {"connector_id": "conn-sn-gn-01",    "tenant_id": "globalnet", "source_type": "ServiceNow",  "region": "eu-west-1", "sync_schedule": "*/30 * * * *", "last_sync_cursor": _ts(hours_ago=3),  "last_successful_sync": _ts(hours_ago=3),  "status": "active",   "docs_synced_total": 344,  "avg_sync_duration_ms": 5700,  "failure_rate_pct": 0.00, "last_error": None},
    ]


def _build_tenant_registry() -> List[Dict[str, Any]]:
    """Return 12 tenant_registry documents across 3 verticals and 3 regions."""
    import random as _rnd
    _rnd.seed(42)
    tenants = [
        # (tenant_id, tenant_name, region, vertical, tier, sensitivity, locale)
        ("acme",          "ACME Telecommunications",        "us-east-1",    "Telecom",            "Enterprise",            "standard",  "en-US"),
        ("globalnet",     "GlobalNet Financial Services",   "eu-west-1",    "Financial Services", "Enterprise",            "regulated", "en-GB"),
        ("apextel",       "ApexTel Inc.",                   "us-west-2",    "Telecom",            "Professional",          "standard",  "en-US"),
        ("bluewave",      "Bluewave Capital Group",         "eu-west-1",    "Financial Services", "Enterprise",            "regulated", "fr-FR"),
        ("meridian",      "Meridian Health Systems",        "us-east-1",    "Healthcare",         "Healthcare-Regulated",  "hipaa",     "en-US"),
        ("fortis",        "Fortis Banking Corporation",     "eu-central-1", "Financial Services", "Enterprise",            "regulated", "de-DE"),
        ("carebridge",    "CareBridge Networks",            "us-west-2",    "Healthcare",         "Healthcare-Regulated",  "hipaa",     "en-US"),
        ("nexustel",      "NexusTel Europe",                "eu-west-1",    "Telecom",            "Professional",          "standard",  "de-DE"),
        ("primevest",     "PrimeVest Asset Management",     "ap-southeast-1","Financial Services","Enterprise",            "regulated", "en-SG"),
        ("alphacare",     "AlphaCare Medical Group",        "ap-northeast-1","Healthcare",        "Healthcare-Regulated",  "hipaa",     "ja-JP"),
        ("vortextel",     "VortexTel APAC",                 "ap-southeast-1","Telecom",           "Professional",          "standard",  "en-SG"),
        ("eurofinance",   "EuroFinance Holdings",           "eu-central-1", "Financial Services", "Enterprise",            "regulated", "fr-FR"),
    ]
    docs = []
    for tid, name, region, vertical, tier, sensitivity, locale in tenants:
        docs.append({
            "tenant_id":                       tid,
            "tenant_name":                     name,
            "region":                          region,
            "industry_vertical":               vertical,
            "subscription_tier":               tier,
            "data_sensitivity_classification": sensitivity,
            "data_residency":                  region.split("-")[0].upper(),
            "kb_index":                        f"kb-{tid}-prod",
            "primary_locale":                  locale,
            "onboarded_at":                    _ts(days_ago=_rnd.randint(30, 365)),
        })
    return docs


def _build_retrieval_logs() -> List[Dict[str, Any]]:
    """Return ~100 retrieval_log entries showing latency with DLS (75) and without DLS baseline (25).

    The dls_enabled field allows direct comparison:
      - dls_enabled=True  → includes dls_filter_time_ms overhead (~6–12ms)
      - dls_enabled=False → baseline retrieval with no ACL filter (lower latency)
    This powers the 'DLS overhead is only 8ms at p95' demo moment.
    """
    import random as _rnd
    _rnd.seed(7)
    logs = []
    tenants_regions = [
        ("acme",      "us-east-1", ["acme-support", "acme-tier2"]),
        ("globalnet", "eu-west-1", ["globalnet-support", "globalnet-tier2"]),
    ]
    query_types = [
        ("hybrid",   35, 8),   # (type, base_latency_ms, dls_overhead_ms)
        ("semantic", 42, 8),
        ("bm25",     18, 5),
    ]

    # 75 DLS-enabled entries (production traffic with tenant isolation)
    for i in range(75):
        tid, region, users = _rnd.choice(tenants_regions)
        q_type, base, dls = _rnd.choice(query_types)
        jitter = _rnd.choice([1, 1, 1, 1, 2, 3, 8])  # rare spikes
        latency = base * jitter + _rnd.randint(-5, 10)
        latency = max(latency, 5)
        dls_t = dls + _rnd.randint(0, 4)
        logs.append({
            "@timestamp":             _ts(hours_ago=i // 3),
            "tenant_id":              tid,
            "region":                 region,
            "query_type":             q_type,
            "query_latency_ms":       latency,
            "dls_filter_time_ms":     dls_t,
            "retrieval_only_time_ms": max(latency - dls_t, 3),
            "dls_enabled":            True,
            "result_count":           _rnd.choice([5, 8, 10, 10, 12]),
            "user_principal":         f"user:{_rnd.choice(users)}@{tid}.com",
            "locale":                 "en-US" if tid == "acme" else _rnd.choice(["en-GB", "fr-FR", "de-DE"]),
        })

    # 25 baseline entries (no DLS — simulates pre-migration OpenSearch behaviour)
    # Shows that retrieval latency is the same; the 8ms delta is entirely DLS overhead.
    baseline_query_types = [
        ("hybrid",   34, 0),
        ("semantic", 41, 0),
        ("bm25",     17, 0),
    ]
    for i in range(25):
        tid, region, _ = _rnd.choice(tenants_regions)
        q_type, base, _ = _rnd.choice(baseline_query_types)
        jitter = _rnd.choice([1, 1, 1, 1, 2, 3, 8])
        latency = base * jitter + _rnd.randint(-5, 10)
        latency = max(latency, 5)
        logs.append({
            "@timestamp":             _ts(hours_ago=30 + i // 2),  # older timestamps (pre-DLS era)
            "tenant_id":              tid,
            "region":                 region,
            "query_type":             q_type,
            "query_latency_ms":       latency,
            "dls_filter_time_ms":     0,
            "retrieval_only_time_ms": latency,
            "dls_enabled":            False,
            "result_count":           _rnd.choice([10, 15, 20, 25]),  # no ACL filtering = more results
            "user_principal":         "user:api-service@genesys.internal",
            "locale":                 "en-US",
        })

    return logs


# ---------------------------------------------------------------------------
# Multilingual kb_content supplement
# ---------------------------------------------------------------------------

def _build_multilingual_docs() -> List[Dict[str, Any]]:
    """Return additional kb_content docs in non-English locales to demonstrate multilingual retrieval."""
    docs: List[Dict[str, Any]] = []

    multilingual = [
        # (doc_id, title, content, locale, tenant, source, principals)
        ("ML-GN-ES-001", "Procedimiento de Escalación de Disputas de Facturación",
         "Cuando un cliente presenta una disputa de facturación que no puede resolverse en el primer nivel, "
         "el agente debe escalar al equipo de Facturación dentro de los 15 minutos. Se requiere el número de "
         "contrato y una descripción del cargo disputado. Los créditos de servicio de hasta €500 pueden ser "
         "aprobados por el equipo de facturación sin aprobación adicional. Las disputas relacionadas con "
         "transferencias internacionales requieren revisión del equipo de cumplimiento.",
         "es-419", "globalnet", "sharepoint",
         ["group:globalnet-agents", "group:globalnet-billing", "tenant:globalnet"]),

        ("ML-GN-FR-001", "Procédure de Suppression des Données RGPD Article 17",
         "Conformément au Règlement Général sur la Protection des Données (RGPD), article 17, tout client "
         "peut demander la suppression de ses données personnelles. GlobalNet s'engage à traiter ces demandes "
         "dans un délai de 30 jours. La suppression doit être confirmée dans tous les systèmes primaires, "
         "les index de recherche et les sauvegardes. Un certificat de suppression signé est envoyé au client. "
         "Les agents doivent ouvrir un ticket JIRA avec la priorité P1 dès réception de la demande.",
         "fr-FR", "globalnet", "confluence",
         ["group:globalnet-compliance", "group:globalnet-privacy", "tenant:globalnet"]),

        ("ML-GN-DE-001", "Netzwerkausfall-Eskalationshandbuch",
         "Bei einem Netzwerkausfall müssen Agenten den Fehlercode NF-{code} protokollieren und das NOC-Team "
         "innerhalb von 15 Minuten benachrichtigen. Die Eskalationsstufen sind: L1-Agent → NOC-Ingenieur → "
         "Regionaler Netzwerkmanager. Für P1-Fehler gilt eine SLA-Schwelle von 1 Stunde. Alle Aktionen müssen "
         "mit Zeitstempel in das Incident-Log eingetragen werden. Kunden sind proaktiv über den Status zu "
         "informieren, wenn die Ausfallzeit 30 Minuten überschreitet.",
         "de-DE", "globalnet", "sharepoint",
         ["group:globalnet-agents", "group:globalnet-sre", "tenant:globalnet"]),

        ("ML-ACME-ES-001", "Guía de Portabilidad de Número para Agentes",
         "La portabilidad numérica permite a los clientes conservar su número de teléfono al cambiar de "
         "operador. El proceso toma entre 1 y 5 días hábiles. El agente debe solicitar al cliente el código "
         "de autorización (CAF) del operador actual. Se debe verificar que la cuenta no tenga deudas "
         "pendientes antes de iniciar la solicitud. El estado de la portabilidad puede consultarse en el "
         "sistema CRM usando el identificador de solicitud PORT-{id}.",
         "es-419", "acme", "salesforce",
         ["group:acme-agents", "group:acme-support", "tenant:acme"]),
    ]

    for doc_id, title, content, locale, tenant, source, principals in multilingual:
        docs.append({
            "tenant_id":    tenant,
            "source":       source,
            "doc_id":       doc_id,
            "chunk_id":     f"{doc_id}-chunk-0",
            "title":        title,
            "content":      content,
            "locale":       locale,
            "acl":          {"principals": principals},
            "source_url":   f"https://{source}.{tenant}.internal/KB/{doc_id}",
            "last_synced_at": _ts(hours_ago=1),
            "@timestamp":   _ts(hours_ago=1),
        })

    return docs


# ---------------------------------------------------------------------------
# Main provisioner class
# ---------------------------------------------------------------------------

class GenesysPOCProvisioner:
    """
    Provisions all assets for the Genesys Knowledge Base POC.

    Args:
        es_client: Optional pre-built Elasticsearch client.  If not supplied,
                   credentials are read from environment variables:
                   ELASTICSEARCH_API_KEY, ELASTIC_ENDPOINT, ELASTICSEARCH_CLOUD_ID
    """

    def __init__(self, es_client: Optional[Elasticsearch] = None):
        self.es = es_client or _build_es_client()

    # ── Public API ────────────────────────────────────────────────────────

    def provision_all(
        self,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Run the full provisioning sequence.

        Returns a summary dict with counts of created resources.
        """
        cb = progress_callback or (lambda msg: logger.info(msg))
        summary: Dict[str, Any] = {}

        cb("Creating index: kb_content ...")
        summary["kb_content"] = self._create_index("kb_content", KB_CONTENT_MAPPING)

        cb("Creating index: kb_sync_events ...")
        summary["kb_sync_events"] = self._create_index("kb_sync_events", KB_SYNC_EVENTS_MAPPING)

        cb("Creating index: connector_registry ...")
        summary["connector_registry"] = self._create_index("connector_registry", CONNECTOR_REGISTRY_MAPPING)

        cb("Creating index: tenant_registry ...")
        summary["tenant_registry"] = self._create_index("tenant_registry", TENANT_REGISTRY_MAPPING)

        cb("Creating index: retrieval_logs ...")
        summary["retrieval_logs"] = self._create_index("retrieval_logs", RETRIEVAL_LOGS_MAPPING)

        cb("Creating DLS roles ...")
        summary["roles"] = self._create_roles()

        cb("Creating demo users ...")
        summary["users"] = self._create_users()

        cb("Indexing kb_content documents ...")
        summary["kb_content_docs"] = self._index_kb_content()

        cb("Indexing kb_sync_events ...")
        summary["kb_sync_events_docs"] = self._index_sync_events()

        cb("Indexing multilingual kb_content docs ...")
        summary["multilingual_docs"] = self._index_multilingual_docs()

        cb("Indexing kb_content for all 12 tenants ...")
        summary["additional_tenant_docs"] = self._index_bulk("kb_content", _build_additional_tenant_docs(), id_field="chunk_id")

        cb("Indexing connector_registry ...")
        summary["connector_registry_docs"] = self._index_connector_registry()

        cb("Indexing tenant_registry ...")
        summary["tenant_registry_docs"] = self._index_bulk("tenant_registry", _build_tenant_registry(), id_field="tenant_id")

        cb("Indexing retrieval_logs ...")
        summary["retrieval_logs_docs"] = self._index_bulk("retrieval_logs", _build_retrieval_logs())

        cb("Provisioning complete.")
        return summary

    def teardown_all(self) -> None:
        """Delete all provisioned indices, roles, and users."""
        for index in ("kb_content", "kb_sync_events", "connector_registry", "tenant_registry", "retrieval_logs"):
            try:
                self.es.indices.delete(index=index, ignore_unavailable=True)
                logger.info("Deleted index: %s", index)
            except Exception as exc:
                logger.warning("Could not delete index %s: %s", index, exc)

        for role_name in ROLES:
            try:
                self.es.security.delete_role(name=role_name)
                logger.info("Deleted role: %s", role_name)
            except NotFoundError:
                pass
            except Exception as exc:
                logger.warning("Could not delete role %s: %s", role_name, exc)

        for user in USERS:
            try:
                self.es.security.delete_user(username=user["username"])
                logger.info("Deleted user: %s", user["username"])
            except NotFoundError:
                pass
            except Exception as exc:
                logger.warning("Could not delete user %s: %s", user["username"], exc)

    # ── Private helpers ───────────────────────────────────────────────────

    def _create_index(self, name: str, mapping: Dict[str, Any]) -> str:
        """Create or update an index with the given mapping. Returns status string."""
        if self.es.indices.exists(index=name):
            logger.info("Index %s already exists — skipping create.", name)
            return "already_exists"
        self.es.indices.create(index=name, body=mapping)
        logger.info("Created index: %s", name)
        return "created"

    def _create_roles(self) -> Dict[str, str]:
        """Create the three DLS roles. Returns {role_name: status}."""
        results: Dict[str, str] = {}
        for role_name, role_body in ROLES.items():
            try:
                self.es.security.put_role(name=role_name, body=role_body)
                logger.info("Created/updated role: %s", role_name)
                results[role_name] = "ok"
            except Exception as exc:
                logger.error("Failed to create role %s: %s", role_name, exc)
                results[role_name] = f"error: {exc}"
        return results

    def _create_users(self) -> Dict[str, str]:
        """Create the three demo users. Returns {username: status}."""
        results: Dict[str, str] = {}
        for user in USERS:
            try:
                self.es.security.put_user(
                    username=user["username"],
                    body={
                        "password": user["password"],
                        "roles":    user["roles"],
                        "full_name": user.get("full_name", ""),
                        "email":    user.get("email", ""),
                        "enabled":  True,
                    },
                )
                logger.info("Created/updated user: %s", user["username"])
                results[user["username"]] = "ok"
            except Exception as exc:
                logger.error("Failed to create user %s: %s", user["username"], exc)
                results[user["username"]] = f"error: {exc}"
        return results

    def _index_kb_content(self) -> int:
        """Bulk-index all kb_content documents. Returns count indexed."""
        docs = _build_kb_documents()
        bulk_body: List[Any] = []
        for doc in docs:
            bulk_body.append({"index": {"_index": "kb_content", "_id": doc["chunk_id"]}})
            bulk_body.append(doc)

        resp = self.es.bulk(body=bulk_body, refresh="wait_for")
        errors = [item for item in resp["items"] if "error" in item.get("index", {})]
        if errors:
            logger.warning("%d bulk index errors for kb_content", len(errors))
            for err in errors[:5]:
                logger.warning("  %s", err)
        indexed = len(docs) - len(errors)
        logger.info("Indexed %d kb_content documents (%d errors)", indexed, len(errors))
        return indexed

    def _index_sync_events(self) -> int:
        """Bulk-index all kb_sync_events. Returns count indexed."""
        events = _build_sync_events()
        bulk_body: List[Any] = []
        for idx, event in enumerate(events):
            bulk_body.append({"index": {"_index": "kb_sync_events"}})
            # Strip None values so ES doesn't complain about null fields
            clean = {k: v for k, v in event.items() if v is not None}
            bulk_body.append(clean)

        resp = self.es.bulk(body=bulk_body, refresh="wait_for")
        errors = [item for item in resp["items"] if "error" in item.get("index", {})]
        if errors:
            logger.warning("%d bulk index errors for kb_sync_events", len(errors))
        indexed = len(events) - len(errors)
        logger.info("Indexed %d kb_sync_events (%d errors)", indexed, len(errors))
        return indexed

    def _index_bulk(self, index: str, docs: List[Dict[str, Any]], id_field: Optional[str] = None) -> int:
        """Generic bulk indexer. Optionally uses id_field as document _id."""
        bulk_body: List[Any] = []
        for doc in docs:
            meta: Dict[str, Any] = {"_index": index}
            if id_field and id_field in doc:
                meta["_id"] = doc[id_field]
            bulk_body.append({"index": meta})
            bulk_body.append({k: v for k, v in doc.items() if v is not None})
        resp = self.es.bulk(body=bulk_body, refresh="wait_for")
        errors = [item for item in resp["items"] if "error" in item.get("index", {})]
        indexed = len(docs) - len(errors)
        if errors:
            logger.warning("%d bulk errors for %s: %s", len(errors), index, errors[0])
        logger.info("Indexed %d docs into %s (%d errors)", indexed, index, len(errors))
        return indexed

    def _index_multilingual_docs(self) -> int:
        """Index multilingual supplement docs into kb_content."""
        docs = _build_multilingual_docs()
        bulk_body: List[Any] = []
        for doc in docs:
            bulk_body.append({"index": {"_index": "kb_content", "_id": doc["chunk_id"]}})
            bulk_body.append(doc)
        resp = self.es.bulk(body=bulk_body, refresh="wait_for")
        errors = [item for item in resp["items"] if "error" in item.get("index", {})]
        indexed = len(docs) - len(errors)
        logger.info("Indexed %d multilingual kb_content docs (%d errors)", indexed, len(errors))
        return indexed

    def _index_connector_registry(self) -> int:
        """Bulk-index connector_registry documents."""
        connectors = _build_connector_registry()
        bulk_body: List[Any] = []
        for c in connectors:
            bulk_body.append({"index": {"_index": "connector_registry", "_id": c["connector_id"]}})
            clean = {k: v for k, v in c.items() if v is not None}
            bulk_body.append(clean)
        resp = self.es.bulk(body=bulk_body, refresh="wait_for")
        errors = [item for item in resp["items"] if "error" in item.get("index", {})]
        indexed = len(connectors) - len(errors)
        logger.info("Indexed %d connector_registry docs (%d errors)", indexed, len(errors))
        return indexed

    # ── Optional: user-scoped query demo (used for smoke-testing DLS) ────

    def verify_dls(self, query: str = "escalation procedure") -> Dict[str, Any]:
        """
        Run the same free-text search as each demo user and return hit counts.
        Demonstrates that DLS enforces tenant isolation at query time.
        """
        results: Dict[str, Any] = {}
        search_body = {"query": {"match": {"content": query}}, "size": 5}

        for user in USERS:
            scoped_es = self.es.options(
                basic_auth=(user["username"], user["password"])
            )
            try:
                resp = scoped_es.search(index="kb_content", body=search_body)
                hits = resp["hits"]["hits"]
                tenants_seen = list({h["_source"]["tenant_id"] for h in hits})
                results[user["username"]] = {
                    "total": resp["hits"]["total"]["value"],
                    "returned": len(hits),
                    "tenants": tenants_seen,
                }
            except Exception as exc:
                results[user["username"]] = {"error": str(exc)}

        return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    )

    import argparse

    parser = argparse.ArgumentParser(description="Genesys POC Provisioner")
    parser.add_argument(
        "--teardown",
        action="store_true",
        help="Delete all provisioned assets instead of creating them",
    )
    parser.add_argument(
        "--verify-dls",
        action="store_true",
        help="Run a DLS smoke-test after provisioning (requires users to exist)",
    )
    args = parser.parse_args()

    provisioner = GenesysPOCProvisioner()

    if args.teardown:
        print("Tearing down all Genesys POC assets...")
        provisioner.teardown_all()
        print("Done.")
        return

    print("Provisioning Genesys POC assets...")
    summary = provisioner.provision_all(progress_callback=print)
    print("\nProvisioning summary:")
    print(json.dumps(summary, indent=2))

    if args.verify_dls:
        print("\nVerifying DLS (query: 'escalation procedure')...")
        dls_results = provisioner.verify_dls()
        print(json.dumps(dls_results, indent=2))


if __name__ == "__main__":
    main()
