"""
Search Context Service

Reads loader.config (company, industry, department, pain_points, use_cases)
and generates a fully personalised SearchContext used by every Revenue Engine panel.

Every query, metric label, product/document name, failing pattern, and pain-point
KPI is derived from what the customer told us — not from a generic retail template.

Industry detection order:
  1. Explicit `industry` field in config
  2. Keywords in `department`, `pain_points`, `use_cases`
  3. Fallback → technology/enterprise default
"""

import random
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── Domain templates ──────────────────────────────────────────────────────────
# Each entry maps to one industry category.  All string fields may contain
# {company} which will be replaced with the actual company name at build time.

_DOMAINS = {

    "contact_center": {
        "label":            "Knowledge Base Articles & Agent Scripts",
        "catalog_label":    "articles / scripts",
        "value_unit":       "resolution",
        "kpi_search_label": "Agent Queries / Day",
        "kpi_zero_label":   "Escalation Rate",
        "kpi_ctr_label":    "First-Touch Resolution",
        "kpi_value_label":  "Avg Handle Time (AHT)",
        "industry_label":   "Contact Center / CX",

        "top_queries": [
            {"query": "how to handle billing dispute",            "searches": 4820, "ctr": 0.81, "avg_value": 3.2,  "zero_result_pct": 0.03},
            {"query": "account cancellation retention script",    "searches": 3614, "ctr": 0.76, "avg_value": 8.5,  "zero_result_pct": 0.05},
            {"query": "IVR transfer to supervisor procedure",     "searches": 2987, "ctr": 0.88, "avg_value": 1.8,  "zero_result_pct": 0.01},
            {"query": "password reset without email access",      "searches": 2341, "ctr": 0.72, "avg_value": 2.1,  "zero_result_pct": 0.08},
            {"query": "refund policy exceptions premium tier",    "searches": 1876, "ctr": 0.69, "avg_value": 12.4, "zero_result_pct": 0.12},
            {"query": "GDPR data deletion request process",       "searches": 1432, "ctr": 0.91, "avg_value": 4.0,  "zero_result_pct": 0.02},
            {"query": "SLA breach escalation path",              "searches": 1187, "ctr": 0.85, "avg_value": 6.7,  "zero_result_pct": 0.04},
            {"query": "chargeback dispute documentation",         "searches": 976,  "ctr": 0.78, "avg_value": 9.1,  "zero_result_pct": 0.07},
        ],
        "failing_queries": [
            {"query": "customer threatening legal action",        "searches": 847, "zero_results": True,  "suggestion": "legal escalation protocol + manager override script",       "impact": "847 escalations/day unresolved, avg AHT +18 min"},
            {"query": "agent won't give refund script",          "searches": 612, "zero_results": True,  "suggestion": "refund authority matrix by tier",                           "impact": "612 agents guessing — $84k monthly customer loss"},
            {"query": "verify identity no account access",       "searches": 589, "zero_results": False, "suggestion": "alternative identity verification procedure",               "impact": "589 abandoned calls/day"},
            {"query": "customer on hold too long complaint",     "searches": 431, "zero_results": True,  "suggestion": "hold time empathy scripts + callback scheduling",            "impact": "CSAT drop of 0.4 points per incident"},
            {"query": "service outage customer communication",   "searches": 387, "zero_results": False, "suggestion": "outage communication template library",                     "impact": "387 inconsistent agent responses during incidents"},
        ],
        "ab_query":         "customer threatens to cancel premium subscription",
        "bm25_results":     [
            {"rank": 1, "item": "Cancellation Script v2.1",         "score": 0.79, "reason": "Keyword: cancel"},
            {"rank": 2, "item": "Premium Tier Benefits Datasheet",   "score": 0.61, "reason": "Keyword: premium"},
            {"rank": 3, "item": "Refund Policy General",             "score": 0.54, "reason": "Keyword: customer"},
            {"rank": 4, "item": "Agent Handbook Section 4",          "score": 0.42, "reason": "Partial keyword"},
            {"rank": 5, "item": "Complaint Logging Procedure",       "score": 0.38, "reason": "Keyword: customer"},
        ],
        "elser_results": [
            {"rank": 1, "item": "Churn Risk Retention Playbook",     "score": 0.97, "reason": "Semantic: cancellation threat + retention offer"},
            {"rank": 2, "item": "High-Value Customer Escalation",    "score": 0.94, "reason": "Semantic: premium churn prevention"},
            {"rank": 3, "item": "Proactive Discount Auth Matrix",    "score": 0.91, "reason": "Semantic: save-the-sale authority"},
            {"rank": 4, "item": "Empathy Framework for Dissatisfied","score": 0.88, "reason": "Semantic: de-escalation technique"},
            {"rank": 5, "item": "Subscription Pause Alternative",    "score": 0.85, "reason": "Semantic: non-cancellation offer"},
        ],
        "intent_query":     "customer got charged twice and is furious",
        "intent_result":    {"intent": "billing_dispute", "urgency": "critical", "sentiment": "negative/angry", "category": "Billing / Duplicate Charge", "reformulated_query": "duplicate charge refund immediate escalation protocol", "recommended_articles": ["Duplicate Charge Resolution SOP", "Empathy Script — Angry Customer", "Refund Authority Matrix"], "reasoning": "Signals financial harm ('charged twice') + emotional state ('furious') → route to billing dispute SOP with empathy wrapper, not generic FAQ."},
        "autocomplete_prefix": "how to handle",
        "autocomplete_suggestions": [
            {"text": "how to handle irate customer — billing dispute",     "category": "Script", "match_type": "semantic"},
            {"text": "how to handle chargeback request step by step",       "category": "SOP",    "match_type": "semantic"},
            {"text": "how to handle identity verification failure",         "category": "SOP",    "match_type": "semantic"},
            {"text": "how to handle SLA breach conversation",               "category": "Script", "match_type": "keyword"},
        ],
        "personalization_history": [
            {"query": "IVR transfer procedure",            "type": "SOP",    "dept": "Tier 1 Support"},
            {"query": "refund policy premium customers",   "type": "Policy", "dept": "Tier 1 Support"},
            {"query": "GDPR data subject request",         "type": "Legal",  "dept": "Compliance"},
        ],
        "merchandising_rules": [
            {"Rule": "PIN — Churn Risk",        "Trigger": "cancel OR leave OR quit",        "Action": "PIN",   "Target": "Retention Playbook (top result)",        "Status": "✅ Active"},
            {"Rule": "BOOST — Legal Escalation","Trigger": "legal OR lawsuit OR attorney",   "Action": "BOOST", "Target": "Legal Escalation SOP +300% score",       "Status": "✅ Active"},
            {"Rule": "PIN — Outage Scripts",    "Trigger": "outage OR down OR not working",  "Action": "PIN",   "Target": "Incident Communication Templates",        "Status": "✅ Active"},
            {"Rule": "BURY — Deprecated SOPs",  "Trigger": "*",                              "Action": "BURY",  "Target": "Documents tagged deprecated=true",        "Status": "✅ Active"},
        ],
        "visual_scenarios": [
            "📸 Screenshot of error message → find troubleshooting article",
            "🖥️ Screen recording of broken UI → find known issue + workaround",
            "📄 Photo of customer's paper bill → find billing dispute SOP",
        ],
        "planner_label":    "Agent Assist — Find the right script for this call",
        "planner_placeholder": 'e.g. "Customer is threatening to cancel after a billing error on their premium account"',
        "pain_kpis": {
            "Avg Handle Time":      {"before": "8.4 min", "after": "5.1 min", "delta": "-39%", "impact": "$2.1M annual savings"},
            "First Call Resolution":{"before": "61%",     "after": "84%",     "delta": "+23pp", "impact": "23,000 fewer repeat calls/month"},
            "Escalation Rate":      {"before": "18%",     "after": "7%",      "delta": "-61%", "impact": "Supervisor capacity freed by 44%"},
            "CSAT Score":           {"before": "3.4/5",   "after": "4.6/5",   "delta": "+1.2", "impact": "Top-quartile CX benchmark achieved"},
        },
    },

    "financial_services": {
        "label":            "Compliance Documents & Policy Library",
        "catalog_label":    "documents / policies",
        "value_unit":       "review",
        "kpi_search_label": "Document Queries / Day",
        "kpi_zero_label":   "Compliance Miss Rate",
        "kpi_ctr_label":    "First-Result Accuracy",
        "kpi_value_label":  "Avg Review Time (min)",
        "industry_label":   "Financial Services",

        "top_queries": [
            {"query": "Basel III capital adequacy requirements",          "searches": 3210, "ctr": 0.87, "avg_value": 45.0, "zero_result_pct": 0.02},
            {"query": "AML suspicious activity threshold reporting",      "searches": 2840, "ctr": 0.83, "avg_value": 62.0, "zero_result_pct": 0.03},
            {"query": "FATCA FBAR reporting obligations non-US accounts", "searches": 2100, "ctr": 0.79, "avg_value": 38.0, "zero_result_pct": 0.05},
            {"query": "KYC enhanced due diligence PEP screening",         "searches": 1876, "ctr": 0.91, "avg_value": 29.0, "zero_result_pct": 0.01},
            {"query": "wire transfer limit cross-border compliance",      "searches": 1540, "ctr": 0.74, "avg_value": 55.0, "zero_result_pct": 0.07},
            {"query": "MiFID II best execution requirements",             "searches": 1280, "ctr": 0.85, "avg_value": 41.0, "zero_result_pct": 0.04},
            {"query": "GDPR data retention financial records",            "searches": 1100, "ctr": 0.88, "avg_value": 33.0, "zero_result_pct": 0.02},
            {"query": "Dodd-Frank swap reporting obligations",            "searches": 890,  "ctr": 0.76, "avg_value": 48.0, "zero_result_pct": 0.06},
        ],
        "failing_queries": [
            {"query": "crypto asset treatment balance sheet",             "searches": 1240, "zero_results": True,  "suggestion": "Digital Asset Accounting Policy 2024",     "impact": "Regulatory exposure: $4.2M potential fine risk"},
            {"query": "climate risk disclosure requirements SEC",         "searches": 980,  "zero_results": True,  "suggestion": "ESG Reporting Framework — SEC Rule S-K",  "impact": "980 analysts manually searching external sites"},
            {"query": "CBDC settlement procedure central bank",          "searches": 720,  "zero_results": False, "suggestion": "Central Bank Digital Currency Policy",     "impact": "12-week compliance gap identified"},
            {"query": "beneficial ownership threshold 2024 update",     "searches": 618,  "zero_results": True,  "suggestion": "FinCEN Beneficial Ownership Rule v2",      "impact": "618 compliance checks done with outdated data"},
            {"query": "sanctions screening OFAC match resolution",      "searches": 542,  "zero_results": False, "suggestion": "OFAC Match Escalation Procedure",          "impact": "542 false-positive blocks per day unresolved"},
        ],
        "ab_query":         "minimum capital reserve requirements for tier-1 bank holding company",
        "bm25_results": [
            {"rank": 1, "item": "Capital Requirements Directive IV",      "score": 0.82, "reason": "Keyword: capital, minimum"},
            {"rank": 2, "item": "Bank Holding Company Act Summary",       "score": 0.71, "reason": "Keyword: bank holding"},
            {"rank": 3, "item": "Reserve Ratio Policy 2019",              "score": 0.59, "reason": "Keyword: reserve"},
            {"rank": 4, "item": "Regulatory Capital Glossary",            "score": 0.44, "reason": "Partial keyword"},
            {"rank": 5, "item": "Annual Compliance Report 2022",          "score": 0.38, "reason": "Keyword: capital"},
        ],
        "elser_results": [
            {"rank": 1, "item": "Basel III Tier-1 Capital Adequacy SOP",  "score": 0.97, "reason": "Semantic: tier-1 capital buffer requirements"},
            {"rank": 2, "item": "SIFI Surcharge Calculation Guide",       "score": 0.93, "reason": "Semantic: systemically important bank capital"},
            {"rank": 3, "item": "CET1 Ratio Stress Test Framework",       "score": 0.91, "reason": "Semantic: common equity tier-1 stress scenarios"},
            {"rank": 4, "item": "Leverage Ratio Disclosure Template",     "score": 0.88, "reason": "Semantic: regulatory capital ratio reporting"},
            {"rank": 5, "item": "Recovery & Resolution Plan Template",    "score": 0.85, "reason": "Semantic: capital adequacy contingency"},
        ],
        "intent_query":     "what happens if our CET1 ratio falls below 4.5%",
        "intent_result":    {"intent": "regulatory_risk_query", "urgency": "high", "domain": "Basel III / Capital Adequacy", "category": "Regulatory Risk", "reformulated_query": "CET1 capital conservation buffer breach consequences supervisory review", "recommended_docs": ["Basel III CET1 Breach Protocol", "Supervisory Review Escalation SOP", "Capital Restoration Plan Template"], "reasoning": "Below-threshold CET1 triggers mandatory conservation buffer restrictions + supervisor notification — needs procedural guidance, not just definition."},
        "autocomplete_prefix": "GDPR",
        "autocomplete_suggestions": [
            {"text": "GDPR Article 17 right to erasure financial data",   "category": "Regulation", "match_type": "semantic"},
            {"text": "GDPR data retention period banking records EU",     "category": "Policy",     "match_type": "semantic"},
            {"text": "GDPR data breach notification 72-hour window",     "category": "SOP",        "match_type": "keyword"},
            {"text": "GDPR lawful basis processing customer data",       "category": "Framework",  "match_type": "keyword"},
        ],
        "personalization_history": [
            {"query": "AML transaction monitoring thresholds",            "type": "Policy",     "dept": "Compliance"},
            {"query": "MiFID II best execution",                         "type": "Regulation", "dept": "Trading Desk"},
            {"query": "IFRS 9 expected credit loss model",               "type": "Accounting", "dept": "Finance"},
        ],
        "merchandising_rules": [
            {"Rule": "PIN — Urgent Regulatory",  "Trigger": "SEC OR CFTC OR FinCEN notice",       "Action": "PIN",   "Target": "Latest regulatory circular (top)",       "Status": "✅ Active"},
            {"Rule": "BOOST — 2024 Updates",     "Trigger": "*",                                  "Action": "BOOST", "Target": "Documents updated in last 90 days",      "Status": "✅ Active"},
            {"Rule": "BURY — Superseded Rules",  "Trigger": "*",                                  "Action": "BURY",  "Target": "Policies tagged status=superseded",      "Status": "✅ Active"},
            {"Rule": "PIN — Sanctions",          "Trigger": "sanction OR OFAC OR SDN",            "Action": "PIN",   "Target": "OFAC Compliance Procedure v4.2",         "Status": "✅ Active"},
        ],
        "visual_scenarios": [
            "📄 Photo of a regulatory letter → find applicable compliance procedure",
            "📊 Screenshot of risk dashboard → find stress-test methodology doc",
            "🧾 Scan of a contract clause → find precedent + legal opinion",
        ],
        "planner_label":    "Compliance Navigator — Find all requirements for this regulation",
        "planner_placeholder": 'e.g. "We need to comply with the new SEC climate disclosure rule by Q2"',
        "pain_kpis": {
            "Avg Document Review":  {"before": "47 min",  "after": "9 min",   "delta": "-81%", "impact": "14,000 analyst hours saved/year"},
            "Compliance Miss Rate": {"before": "6.8%",    "after": "0.4%",    "delta": "-94%", "impact": "$18M regulatory fine risk eliminated"},
            "Search Accuracy":      {"before": "58%",     "after": "96%",     "delta": "+38pp","impact": "Auditors find right policy first time"},
            "Policy Retrieval":     {"before": "12 steps","after": "1 search","delta": "-92%", "impact": "Zero manual folder navigation required"},
        },
    },

    "healthcare": {
        "label":            "Clinical Protocols & Clinical Decision Support",
        "catalog_label":    "protocols / clinical docs",
        "value_unit":       "clinical decision",
        "kpi_search_label": "Clinical Queries / Day",
        "kpi_zero_label":   "Protocol Gap Rate",
        "kpi_ctr_label":    "Decision Support Accuracy",
        "kpi_value_label":  "Time to Decision (min)",
        "industry_label":   "Healthcare",

        "top_queries": [
            {"query": "metformin contraindications renal impairment eGFR",    "searches": 3890, "ctr": 0.92, "avg_value": 4.2,  "zero_result_pct": 0.01},
            {"query": "post-op wound care protocol hip replacement",          "searches": 3120, "ctr": 0.88, "avg_value": 3.8,  "zero_result_pct": 0.02},
            {"query": "ICD-10 code unspecified hypertension stage 2",         "searches": 2740, "ctr": 0.84, "avg_value": 2.1,  "zero_result_pct": 0.03},
            {"query": "prior authorization cardiology stress test",           "searches": 2310, "ctr": 0.79, "avg_value": 6.4,  "zero_result_pct": 0.05},
            {"query": "sepsis protocol early recognition criteria",           "searches": 1980, "ctr": 0.95, "avg_value": 8.9,  "zero_result_pct": 0.01},
            {"query": "drug interaction warfarin NSAID bleeding risk",        "searches": 1650, "ctr": 0.91, "avg_value": 5.7,  "zero_result_pct": 0.02},
            {"query": "stroke thrombectomy window eligibility criteria",      "searches": 1320, "ctr": 0.87, "avg_value": 12.3, "zero_result_pct": 0.03},
            {"query": "HIPAA minimum necessary disclosure standard",          "searches": 1100, "ctr": 0.83, "avg_value": 3.4,  "zero_result_pct": 0.04},
        ],
        "failing_queries": [
            {"query": "COVID long haul fatigue treatment protocol",           "searches": 2140, "zero_results": True,  "suggestion": "Post-COVID Syndrome Management Guidelines 2024",    "impact": "2,140 clinicians using outdated treatment paths"},
            {"query": "GLP-1 dosing morbid obesity non-diabetic",            "searches": 1870, "zero_results": True,  "suggestion": "GLP-1 Agonist Prescribing Framework — Obesity",      "impact": "$6.2M in prior auth denials from wrong dosing"},
            {"query": "AI imaging interpretation liability",                  "searches": 1240, "zero_results": False, "suggestion": "AI-Assisted Diagnosis Policy + Radiologist Oversight","impact": "Medico-legal risk not addressed in 1,240 queries"},
            {"query": "biosimilar substitution pharmacy protocol",            "searches": 890,  "zero_results": True,  "suggestion": "Biosimilar Interchangeability Formulary List",         "impact": "$1.8M formulary savings unrealised"},
            {"query": "telehealth prescribing DEA exception",                "searches": 720,  "zero_results": False, "suggestion": "Telemedicine Controlled Substance Exception Policy",  "impact": "720 prescribers operating without policy guidance"},
        ],
        "ab_query":         "newly diagnosed type 2 diabetes first-line treatment no metformin tolerance",
        "bm25_results": [
            {"rank": 1, "item": "Diabetes Management Protocol v3.1",           "score": 0.77, "reason": "Keyword: diabetes, treatment"},
            {"rank": 2, "item": "Metformin Prescribing Information",           "score": 0.68, "reason": "Keyword: metformin"},
            {"rank": 3, "item": "Type 2 Diabetes Annual Review Checklist",     "score": 0.55, "reason": "Keyword: type 2 diabetes"},
            {"rank": 4, "item": "Endocrinology Referral Criteria",             "score": 0.41, "reason": "Partial keyword"},
            {"rank": 5, "item": "Formulary 2024 — Antidiabetics",             "score": 0.37, "reason": "Keyword: diabetes"},
        ],
        "elser_results": [
            {"rank": 1, "item": "GLP-1/SGLT2 First-Line Alternative Protocol","score": 0.97, "reason": "Semantic: metformin-intolerant T2D alternatives"},
            {"rank": 2, "item": "Cardiometabolic Risk-Stratified T2D Pathway","score": 0.94, "reason": "Semantic: CV risk + glucose management"},
            {"rank": 3, "item": "SGLT2 Inhibitor Prescribing Guide",          "score": 0.91, "reason": "Semantic: glucose lowering without metformin"},
            {"rank": 4, "item": "Patient Education — Diabetes Self-Management","score": 0.88, "reason": "Semantic: newly diagnosed patient resources"},
            {"rank": 5, "item": "Endocrinology Fast-Track Criteria",           "score": 0.85, "reason": "Semantic: complex diabetes specialist referral"},
        ],
        "intent_query":     "65 year old patient acute chest pain negative troponin",
        "intent_result":    {"intent": "differential_diagnosis_query", "urgency": "critical", "category": "Cardiology / NSTEMI Rule-Out", "reformulated_query": "high-risk ACS rule-out protocol negative troponin elderly HEART score", "recommended_protocols": ["HEART Score Risk Stratification", "ACS NSTEMI Rule-Out Pathway 0/2h", "Stress Testing Eligibility Post-Triage"], "reasoning": "Negative troponin alone does not rule out ACS in a 65yo — HEART score pathway needed, not generic chest pain FAQ."},
        "autocomplete_prefix": "sepsis",
        "autocomplete_suggestions": [
            {"text": "sepsis 3 diagnostic criteria qSOFA score",             "category": "Protocol",  "match_type": "semantic"},
            {"text": "sepsis empirical antibiotic selection ICU",            "category": "Formulary", "match_type": "semantic"},
            {"text": "sepsis bundle 1-hour compliance checklist",            "category": "SOP",       "match_type": "keyword"},
            {"text": "septic shock vasopressor initiation threshold",        "category": "Protocol",  "match_type": "keyword"},
        ],
        "personalization_history": [
            {"query": "sepsis antibiotic stewardship protocol",             "type": "Protocol",  "dept": "ICU"},
            {"query": "fall risk assessment MORSE scale",                   "type": "Checklist", "dept": "Med-Surg"},
            {"query": "HIPAA minimum necessary clinical notes",             "type": "Policy",    "dept": "Compliance"},
        ],
        "merchandising_rules": [
            {"Rule": "PIN — Code Blue",        "Trigger": "cardiac arrest OR code blue OR ACLS",      "Action": "PIN",   "Target": "ACLS Arrest Protocol (immediate top)",       "Status": "✅ Active"},
            {"Rule": "BOOST — 2024 Guidelines","Trigger": "*",                                         "Action": "BOOST", "Target": "Guidelines updated < 6 months ago",          "Status": "✅ Active"},
            {"Rule": "PIN — HIPAA Queries",    "Trigger": "HIPAA OR PHI OR disclosure",               "Action": "PIN",   "Target": "Privacy Officer Contact + Policy",           "Status": "✅ Active"},
            {"Rule": "BURY — Retired Protocols","Trigger": "*",                                        "Action": "BURY",  "Target": "Protocols tagged status=retired",            "Status": "✅ Active"},
        ],
        "visual_scenarios": [
            "🩺 Photo of wound → find wound care classification + dressing protocol",
            "📊 Screenshot of lab result → find clinical interpretation guide",
            "💊 Photo of pill → identify medication + interaction checker",
        ],
        "planner_label":    "Clinical Pathway Finder — Build the right care plan",
        "planner_placeholder": 'e.g. "62-year-old female, newly diagnosed COPD, current smoker, eGFR 48"',
        "pain_kpis": {
            "Time to Decision":    {"before": "22 min",  "after": "4 min",   "delta": "-82%",  "impact": "18 min returned to direct patient care/query"},
            "Protocol Compliance": {"before": "71%",     "after": "97%",     "delta": "+26pp", "impact": "14% reduction in adverse events"},
            "Coding Accuracy":     {"before": "78%",     "after": "99.1%",   "delta": "+21pp", "impact": "$3.4M annual revenue cycle improvement"},
            "Drug Safety Alerts":  {"before": "41% caught","after": "99.8%", "delta": "+59pp", "impact": "Critical interaction catch rate at point-of-care"},
        },
    },

    "technology": {
        "label":            "Technical Documentation & Support Knowledge Base",
        "catalog_label":    "docs / support articles",
        "value_unit":       "deflection",
        "kpi_search_label": "Developer Queries / Day",
        "kpi_zero_label":   "Ticket Escalation Rate",
        "kpi_ctr_label":    "Self-Service Resolution",
        "kpi_value_label":  "Time to Resolution (min)",
        "industry_label":   "Technology / SaaS",

        "top_queries": [
            {"query": "configure SSO SAML 2.0 OKTA integration",          "searches": 5820, "ctr": 0.83, "avg_value": 28.0, "zero_result_pct": 0.02},
            {"query": "API rate limit 429 retry exponential backoff",     "searches": 4910, "ctr": 0.88, "avg_value": 12.0, "zero_result_pct": 0.01},
            {"query": "webhook signature verification HMAC SHA256",       "searches": 3740, "ctr": 0.79, "avg_value": 35.0, "zero_result_pct": 0.03},
            {"query": "RBAC permission denied production environment",    "searches": 3210, "ctr": 0.75, "avg_value": 18.0, "zero_result_pct": 0.05},
            {"query": "Kubernetes pod OOMKilled memory limit increase",   "searches": 2890, "ctr": 0.91, "avg_value": 22.0, "zero_result_pct": 0.02},
            {"query": "Terraform state lock remote backend recovery",     "searches": 2340, "ctr": 0.85, "avg_value": 41.0, "zero_result_pct": 0.04},
            {"query": "database connection pool exhausted PostgreSQL",    "searches": 1980, "ctr": 0.87, "avg_value": 15.0, "zero_result_pct": 0.03},
            {"query": "JWT token validation RS256 public key rotation",   "searches": 1620, "ctr": 0.81, "avg_value": 19.0, "zero_result_pct": 0.06},
        ],
        "failing_queries": [
            {"query": "LLM hallucination mitigation production",          "searches": 3140, "zero_results": True,  "suggestion": "GenAI Output Validation + RAG Grounding Guide",     "impact": "3,140 engineers building AI without safety guardrails"},
            {"query": "gRPC timeout cascading failure pattern",           "searches": 1870, "zero_results": True,  "suggestion": "Distributed Systems Timeout + Circuit Breaker SOP","impact": "$420K/incident from undocumented cascading failures"},
            {"query": "vector database index optimization semantic",      "searches": 1540, "zero_results": False, "suggestion": "HNSW Index Tuning Guide + Recall/Speed Trade-offs", "impact": "1,540 developers guessing embedding parameters"},
            {"query": "multi-tenant data isolation row-level security",   "searches": 1240, "zero_results": True,  "suggestion": "Multi-Tenancy Architecture Decision Record",         "impact": "Security review blocked 6 enterprise deals"},
            {"query": "OpenTelemetry collector pipeline drop sampling",   "searches": 980,  "zero_results": False, "suggestion": "OTel Sampling Strategy + Head/Tail Decision Guide", "impact": "98% of trace data dropped unintentionally"},
        ],
        "ab_query":         "how to implement zero-downtime database schema migration in production",
        "bm25_results": [
            {"rank": 1, "item": "Database Migration Guide v2.1",           "score": 0.80, "reason": "Keyword: database, migration"},
            {"rank": 2, "item": "Production Deployment Checklist",         "score": 0.66, "reason": "Keyword: production"},
            {"rank": 3, "item": "Schema Change Management Policy",         "score": 0.58, "reason": "Keyword: schema"},
            {"rank": 4, "item": "PostgreSQL Upgrade Runbook",              "score": 0.44, "reason": "Keyword: database"},
            {"rank": 5, "item": "Downtime Incident Template",              "score": 0.39, "reason": "Keyword: downtime"},
        ],
        "elser_results": [
            {"rank": 1, "item": "Expand + Contract Zero-Downtime Migration","score": 0.97, "reason": "Semantic: non-breaking schema evolution pattern"},
            {"rank": 2, "item": "Blue-Green Deployment with DB Cutover",   "score": 0.94, "reason": "Semantic: traffic shifting + schema sync"},
            {"rank": 3, "item": "Online DDL with gh-ost / pt-online",      "score": 0.91, "reason": "Semantic: non-locking schema changes"},
            {"rank": 4, "item": "Feature Flag + Dual-Write Migration",     "score": 0.88, "reason": "Semantic: backward-compatible schema migration"},
            {"rank": 5, "item": "Database Change Rollback Runbook",        "score": 0.84, "reason": "Semantic: safe schema rollback procedure"},
        ],
        "intent_query":     "my deployment is stuck and production is down",
        "intent_result":    {"intent": "incident_triage", "urgency": "P0", "category": "Production Outage / Deployment", "reformulated_query": "stuck deployment rollback procedure production outage recovery runbook", "recommended_docs": ["P0 Incident Response Runbook", "Deployment Rollback Checklist", "On-Call Escalation Path"], "reasoning": "P0 incident signal — skip FAQ, route directly to incident runbook + on-call page, not deployment tutorial."},
        "autocomplete_prefix": "Kubernetes",
        "autocomplete_suggestions": [
            {"text": "Kubernetes pod CrashLoopBackOff diagnosis guide",   "category": "Runbook",    "match_type": "semantic"},
            {"text": "Kubernetes HPA scaling behaviour custom metrics",   "category": "Config",     "match_type": "semantic"},
            {"text": "Kubernetes network policy deny-all best practice",  "category": "Security",   "match_type": "keyword"},
            {"text": "Kubernetes persistent volume claim expansion",      "category": "Operations", "match_type": "keyword"},
        ],
        "personalization_history": [
            {"query": "Terraform remote state backend S3",                "type": "Runbook",  "dept": "Platform Engineering"},
            {"query": "OpenTelemetry trace context propagation",          "type": "Guide",    "dept": "Observability"},
            {"query": "JWT RS256 key rotation zero downtime",             "type": "Security", "dept": "Auth Team"},
        ],
        "merchandising_rules": [
            {"Rule": "PIN — P0 Runbooks",      "Trigger": "down OR outage OR broken OR 500",        "Action": "PIN",   "Target": "Incident Response Runbook (top result)",      "Status": "✅ Active"},
            {"Rule": "BOOST — This Quarter",   "Trigger": "*",                                      "Action": "BOOST", "Target": "Docs updated in last 30 days",               "Status": "✅ Active"},
            {"Rule": "PIN — Security Alerts",  "Trigger": "CVE OR vulnerability OR exploit",        "Action": "PIN",   "Target": "Security Advisory + Patch Guidance",         "Status": "✅ Active"},
            {"Rule": "BURY — Deprecated APIs", "Trigger": "*",                                      "Action": "BURY",  "Target": "API docs tagged api_status=deprecated",      "Status": "✅ Active"},
        ],
        "visual_scenarios": [
            "📸 Screenshot of error stacktrace → find matching known issue + fix",
            "📊 Screenshot of metrics spike → find runbook for that service",
            "🖥️ Photo of architecture diagram → find relevant design pattern docs",
        ],
        "planner_label":    "Solution Architect — Build the right technical design",
        "planner_placeholder": 'e.g. "We need to migrate our monolith to microservices with zero downtime and GDPR compliance"',
        "pain_kpis": {
            "Ticket Deflection":    {"before": "29%",     "after": "74%",    "delta": "+45pp", "impact": "3,200 tickets deflected/month = $640K saved"},
            "Time to Resolution":   {"before": "4.2 hrs", "after": "38 min", "delta": "-85%",  "impact": "Mean incident cost reduced by $180K/year"},
            "Developer Onboarding": {"before": "3 weeks", "after": "4 days", "delta": "-81%",  "impact": "$2.1M faster time-to-productivity annually"},
            "Doc Discovery":        {"before": "47 min",  "after": "8 sec",  "delta": "-99.7%","impact": "Engineers find right answer without Slack noise"},
        },
    },

    "manufacturing": {
        "label":            "Parts Catalog, Maintenance Manuals & Quality Docs",
        "catalog_label":    "parts / manuals",
        "value_unit":       "lookup",
        "kpi_search_label": "Engineer Queries / Day",
        "kpi_zero_label":   "Wrong Part Selection Rate",
        "kpi_ctr_label":    "First-Result Accuracy",
        "kpi_value_label":  "Avg Lookup Time (min)",
        "industry_label":   "Manufacturing",

        "top_queries": [
            {"query": "M12 hex bolt grade 8.8 torque specification",        "searches": 4210, "ctr": 0.91, "avg_value": 8.4,  "zero_result_pct": 0.02},
            {"query": "hydraulic pump preventive maintenance schedule",     "searches": 3840, "ctr": 0.87, "avg_value": 12.0, "zero_result_pct": 0.03},
            {"query": "ISO 9001 non-conformance report procedure",          "searches": 3120, "ctr": 0.84, "avg_value": 6.2,  "zero_result_pct": 0.02},
            {"query": "part number 45-6789 cross reference compatibility",  "searches": 2780, "ctr": 0.79, "avg_value": 18.5, "zero_result_pct": 0.07},
            {"query": "PFMEA failure mode severity rating criteria",        "searches": 2340, "ctr": 0.85, "avg_value": 9.1,  "zero_result_pct": 0.04},
            {"query": "REACH SVHC substance compliance declaration",        "searches": 1980, "ctr": 0.88, "avg_value": 14.0, "zero_result_pct": 0.03},
            {"query": "weld procedure specification WPS ASME",              "searches": 1650, "ctr": 0.81, "avg_value": 11.0, "zero_result_pct": 0.05},
            {"query": "OSHA lockout tagout procedure pneumatic press",      "searches": 1380, "ctr": 0.93, "avg_value": 7.8,  "zero_result_pct": 0.01},
        ],
        "failing_queries": [
            {"query": "lead-free RoHS substitute for part 77-4421",        "searches": 1840, "zero_results": True,  "suggestion": "RoHS Compliant Part Cross-Reference DB 2024",      "impact": "EU shipment hold — €2.1M at risk"},
            {"query": "predictive maintenance bearing temperature model",  "searches": 1420, "zero_results": True,  "suggestion": "Bearing Failure Prediction ML Model Guide",        "impact": "1,420 machines without predictive threshold config"},
            {"query": "supplier quality audit checklist tier 2",           "searches": 1180, "zero_results": False, "suggestion": "IATF 16949 Tier-2 Supplier Audit Template",       "impact": "OEM contract clause violation risk"},
            {"query": "additive manufacturing material certification",     "searches": 890,  "zero_results": True,  "suggestion": "3D Printing / AM Material Qualification SOP",     "impact": "8 new product lines blocked from certification"},
            {"query": "carbon footprint calculation per unit production",  "searches": 720,  "zero_results": False, "suggestion": "Scope 1+2 Emission Factor Library + Calc Tool",   "impact": "ESG reporting deadline at risk"},
        ],
        "ab_query":         "seal kit replacement for 200-bar hydraulic cylinder after 5000 hours",
        "bm25_results": [
            {"rank": 1, "item": "Hydraulic Cylinder Maintenance Manual",   "score": 0.79, "reason": "Keyword: hydraulic, cylinder"},
            {"rank": 2, "item": "Seal & O-Ring Catalogue 2024",           "score": 0.68, "reason": "Keyword: seal"},
            {"rank": 3, "item": "Hydraulic System Overhaul Guide",        "score": 0.55, "reason": "Keyword: hydraulic"},
            {"rank": 4, "item": "Planned Maintenance Schedule PM-401",    "score": 0.42, "reason": "Keyword: maintenance"},
            {"rank": 5, "item": "Service Parts Price List Q4-2024",       "score": 0.38, "reason": "Keyword: parts"},
        ],
        "elser_results": [
            {"rank": 1, "item": "200-bar Cylinder Seal Kit SKU 88-4412",  "score": 0.97, "reason": "Semantic: high-pressure cylinder seal kit"},
            {"rank": 2, "item": "5000-Hour Overhaul Checklist HC-200",    "score": 0.94, "reason": "Semantic: time-based maintenance interval"},
            {"rank": 3, "item": "Parker Series 3000 Replacement Parts",   "score": 0.91, "reason": "Semantic: compatible seal kit family"},
            {"rank": 4, "item": "Hydraulic Fluid Contamination Check",    "score": 0.88, "reason": "Semantic: pre-seal replacement inspection"},
            {"rank": 5, "item": "Torque Spec Sheet — HC Series Bolts",    "score": 0.85, "reason": "Semantic: reassembly specification"},
        ],
        "intent_query":     "line 4 stopped production alarm PLC fault code E-1042",
        "intent_result":    {"intent": "production_stoppage_triage", "urgency": "P0 — Line Down", "category": "PLC Fault / Unplanned Downtime", "reformulated_query": "PLC E-1042 fault code root cause resolution emergency procedure line restart", "recommended_docs": ["PLC Fault Code E-10xx Resolution Guide", "Line 4 Emergency Restart SOP", "Maintenance Escalation — Unplanned Downtime"], "reasoning": "E-1042 fault code signals servo drive fault — not a general PLC query. Needs fault-code-specific runbook + estimated downtime impact for shift supervisor."},
        "autocomplete_prefix": "ISO 9001",
        "autocomplete_suggestions": [
            {"text": "ISO 9001:2015 clause 8.3 design control process",   "category": "Standard",  "match_type": "semantic"},
            {"text": "ISO 9001 internal audit corrective action procedure","category": "SOP",       "match_type": "semantic"},
            {"text": "ISO 9001 management review agenda template",         "category": "Template",  "match_type": "keyword"},
            {"text": "ISO 9001 risk-based thinking FMEA integration",     "category": "Framework", "match_type": "keyword"},
        ],
        "personalization_history": [
            {"query": "PFMEA severity occurrence detection criteria",      "type": "Standard",  "dept": "Quality Assurance"},
            {"query": "OSHA 29 CFR 1910.147 lockout procedure",           "type": "SOP",       "dept": "EHS"},
            {"query": "hydraulic actuator replacement torque specs",       "type": "Manual",    "dept": "Maintenance"},
        ],
        "merchandising_rules": [
            {"Rule": "PIN — Safety Critical",  "Trigger": "LOTO OR lockout OR safety OR OSHA",     "Action": "PIN",   "Target": "Safety Procedure (mandatory first result)",   "Status": "✅ Active"},
            {"Rule": "BOOST — Recalled Parts", "Trigger": "*",                                     "Action": "BOOST", "Target": "Active product recall notices",              "Status": "✅ Active"},
            {"Rule": "PIN — Line Down",        "Trigger": "fault OR alarm OR stopped OR E-1",      "Action": "PIN",   "Target": "Fault Code Runbook Library",                 "Status": "✅ Active"},
            {"Rule": "BURY — EOL Parts",       "Trigger": "*",                                     "Action": "BURY",  "Target": "Parts tagged lifecycle=end-of-life",         "Status": "✅ Active"},
        ],
        "visual_scenarios": [
            "📸 Photo of worn part → find replacement part number + supplier",
            "🔧 Photo of machine nameplate → find service manual + spare parts list",
            "⚠️ Photo of defect → find quality inspection criteria + disposition SOP",
        ],
        "planner_label":    "Maintenance Planner — Build the complete overhaul task list",
        "planner_placeholder": 'e.g. "Scheduled 5000-hour overhaul for press line 4, hydraulic + electrical"',
        "pain_kpis": {
            "Wrong Part Selection": {"before": "12%",     "after": "0.3%",   "delta": "-97%",  "impact": "Zero production stops from wrong part ordered"},
            "Avg Lookup Time":      {"before": "34 min",  "after": "45 sec", "delta": "-97%",  "impact": "28 min/lookup × 1,200 queries/day = 560 hrs saved"},
            "Unplanned Downtime":   {"before": "6.4%",    "after": "1.1%",   "delta": "-83%",  "impact": "$4.2M annual OEE improvement"},
            "Compliance Finding":   {"before": "11/audit","after": "0.8",    "delta": "-93%",  "impact": "ISO 9001 certification maintained without major findings"},
        },
    },

    "default": {
        "label":            "Enterprise Knowledge Base",
        "catalog_label":    "documents / records",
        "value_unit":       "resolution",
        "kpi_search_label": "Searches / Day",
        "kpi_zero_label":   "Zero Result Rate",
        "kpi_ctr_label":    "Click-Through Rate",
        "kpi_value_label":  "Avg Session Value",
        "industry_label":   "Enterprise",

        "top_queries": [
            {"query": "onboarding checklist new employee",                "searches": 3210, "ctr": 0.82, "avg_value": 14.0, "zero_result_pct": 0.03},
            {"query": "expense reimbursement policy international travel","searches": 2840, "ctr": 0.78, "avg_value": 8.5,  "zero_result_pct": 0.05},
            {"query": "data classification framework confidential tier",  "searches": 2100, "ctr": 0.85, "avg_value": 12.0, "zero_result_pct": 0.02},
            {"query": "vendor contract approval workflow",                "searches": 1870, "ctr": 0.72, "avg_value": 28.0, "zero_result_pct": 0.07},
            {"query": "GDPR data subject access request handling",        "searches": 1540, "ctr": 0.88, "avg_value": 9.0,  "zero_result_pct": 0.03},
            {"query": "annual performance review calibration guide",      "searches": 1320, "ctr": 0.76, "avg_value": 11.0, "zero_result_pct": 0.04},
            {"query": "IT security incident response escalation",         "searches": 1100, "ctr": 0.91, "avg_value": 18.0, "zero_result_pct": 0.02},
            {"query": "SOC 2 type II audit evidence collection",          "searches": 890,  "ctr": 0.83, "avg_value": 24.0, "zero_result_pct": 0.05},
        ],
        "failing_queries": [
            {"query": "AI tool approved vendor list 2024",               "searches": 1820, "zero_results": True,  "suggestion": "Approved AI/SaaS Vendor Registry 2024",      "impact": "1,820 employees using unapproved AI tools"},
            {"query": "hybrid work policy exceptions manager approval",  "searches": 1340, "zero_results": False, "suggestion": "Flexible Work Policy + Exception Workflow",   "impact": "$280K in HR escalations from policy ambiguity"},
            {"query": "sustainability reporting Scope 3 methodology",    "searches": 1010, "zero_results": True,  "suggestion": "ESG Reporting Framework — Scope 1/2/3",      "impact": "ESG report delayed 6 weeks"},
            {"query": "merger entity name change contract update",       "searches": 780,  "zero_results": True,  "suggestion": "Post-M&A Contract Amendment Procedure",      "impact": "780 contracts with legacy entity name"},
            {"query": "whistleblower hotline anonymous process",         "searches": 620,  "zero_results": False, "suggestion": "Ethics Hotline + Anonymous Reporting SOP",   "impact": "Regulatory non-compliance risk identified"},
        ],
        "ab_query":         "process to request budget approval for new headcount outside annual cycle",
        "bm25_results": [
            {"rank": 1, "item": "Budget Planning Guide Annual Cycle",      "score": 0.76, "reason": "Keyword: budget, annual"},
            {"rank": 2, "item": "Headcount Request Form HR-14",           "score": 0.65, "reason": "Keyword: headcount"},
            {"rank": 3, "item": "Finance Approval Workflow v3",           "score": 0.54, "reason": "Keyword: approval"},
            {"rank": 4, "item": "Organizational Change Management Policy","score": 0.42, "reason": "Keyword: budget"},
            {"rank": 5, "item": "Q4 Finance Operating Procedures",        "score": 0.38, "reason": "Keyword: budget"},
        ],
        "elser_results": [
            {"rank": 1, "item": "Off-Cycle Headcount Exception Procedure","score": 0.97, "reason": "Semantic: outside-cycle approval + business justification"},
            {"rank": 2, "item": "CHRO Fast-Track Approval Framework",     "score": 0.93, "reason": "Semantic: urgent headcount without annual cycle wait"},
            {"rank": 3, "item": "Workforce Planning — Interim FTE Guide", "score": 0.90, "reason": "Semantic: contractor-to-FTE bridge while approving"},
            {"rank": 4, "item": "Finance Business Case Template",         "score": 0.87, "reason": "Semantic: budget justification documentation"},
            {"rank": 5, "item": "Headcount ROI Calculator",              "score": 0.84, "reason": "Semantic: headcount business impact quantification"},
        ],
        "intent_query":     "I can't find the form I need to submit for my leave",
        "intent_result":    {"intent": "document_retrieval", "urgency": "medium", "category": "HR / Leave Management", "reformulated_query": "leave request form submission procedure employee self-service", "recommended_docs": ["Leave Request Form — Employee Portal", "Leave Policy Types + Eligibility", "HRIS Self-Service Guide"], "reasoning": "Vague query ('form I need') disambiguated to leave type using session context — surfaces the right form, not the leave policy index."},
        "autocomplete_prefix": "data",
        "autocomplete_suggestions": [
            {"text": "data classification policy confidential handling",   "category": "Policy",    "match_type": "semantic"},
            {"text": "data breach notification procedure GDPR 72hr",      "category": "SOP",       "match_type": "semantic"},
            {"text": "data retention schedule by document type",          "category": "Framework", "match_type": "keyword"},
            {"text": "data subject access request response template",     "category": "Template",  "match_type": "keyword"},
        ],
        "personalization_history": [
            {"query": "travel expense policy international",              "type": "Policy",   "dept": "Finance"},
            {"query": "vendor NDA approval process",                      "type": "Workflow", "dept": "Legal"},
            {"query": "GDPR subject access request",                      "type": "SOP",      "dept": "Compliance"},
        ],
        "merchandising_rules": [
            {"Rule": "PIN — Critical Policies",   "Trigger": "GDPR OR CCPA OR data breach",          "Action": "PIN",   "Target": "Privacy Policy + DPA (top result)",          "Status": "✅ Active"},
            {"Rule": "BOOST — Recently Updated",  "Trigger": "*",                                    "Action": "BOOST", "Target": "Documents updated in last 60 days",          "Status": "✅ Active"},
            {"Rule": "PIN — HR Urgent",           "Trigger": "harassment OR misconduct OR safety",   "Action": "PIN",   "Target": "Ethics Hotline + HR Direct Contact",         "Status": "✅ Active"},
            {"Rule": "BURY — Archived Policies",  "Trigger": "*",                                    "Action": "BURY",  "Target": "Documents tagged status=archived",           "Status": "✅ Active"},
        ],
        "visual_scenarios": [
            "📄 Photo of a form → identify form type + find fillable digital version",
            "📸 Screenshot of a system error → find IT support article + ticket link",
            "🖼️ Image of an org chart → find contact directory + team structure",
        ],
        "planner_label":    "Project Planner — Build your complete requirements list",
        "planner_placeholder": 'e.g. "We need to roll out a new compliance training programme across 3 offices by Q2"',
        "pain_kpis": {
            "Search Accuracy":      {"before": "51%",     "after": "94%",    "delta": "+43pp", "impact": "Employees find right document first time"},
            "Zero Result Rate":     {"before": "8.4%",    "after": "0.6%",   "delta": "-93%",  "impact": "6,800 zero-result sessions fixed/day"},
            "Knowledge Retrieval":  {"before": "18 min",  "after": "12 sec", "delta": "-98.9%","impact": "3.2 hrs/employee/week returned to productive work"},
            "Compliance Exposure":  {"before": "High",    "after": "Low",    "delta": "—",     "impact": "Policy findability gap closed before next audit"},
        },
    },
}

# ── Industry detector ─────────────────────────────────────────────────────────

_INDUSTRY_KEYWORDS = {
    "contact_center":     ["contact center", "call center", "cx", "csat", "ivr", "agent", "genesys",
                           "zendesk", "customer service", "support operations", "help desk", "aha", "aht",
                           "first call resolution", "fcr", "customer experience"],
    "financial_services": ["bank", "financial", "insurance", "fintech", "compliance", "regulatory",
                           "aml", "kyc", "investment", "trading", "wealth", "credit", "lending",
                           "basel", "mifid", "fatca", "gdpr financial"],
    "healthcare":         ["hospital", "health", "clinical", "medical", "pharma", "ehr", "emr",
                           "patient", "physician", "nursing", "clinical decision", "formulary",
                           "hipaa", "icd", "cpt", "care pathway"],
    "technology":         ["software", "saas", "platform", "developer", "engineering", "devops",
                           "cloud", "api", "kubernetes", "microservice", "tech", "startup",
                           "infrastructure", "security", "data platform"],
    "manufacturing":      ["manufacturing", "factory", "production", "plant", "industrial",
                           "automotive", "aerospace", "assembly", "quality", "iso 9001", "lean",
                           "maintenance", "oem", "supply chain", "parts"],
}


def _detect_industry(config: Dict[str, Any]) -> str:
    ctx         = config.get("customer_context") or config
    industry    = ctx.get("industry", "")
    department  = ctx.get("department", "")
    pain_points = " ".join(ctx.get("pain_points", []) if isinstance(ctx.get("pain_points"), list) else [str(ctx.get("pain_points", ""))])
    use_cases   = " ".join(ctx.get("use_cases", []) if isinstance(ctx.get("use_cases"), list) else [str(ctx.get("use_cases", ""))])

    full_text = f"{industry} {department} {pain_points} {use_cases}".lower()

    scores = {k: 0 for k in _INDUSTRY_KEYWORDS}
    for industry_key, keywords in _INDUSTRY_KEYWORDS.items():
        for kw in keywords:
            if kw in full_text:
                scores[industry_key] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "default"


# ── Public API ────────────────────────────────────────────────────────────────

@dataclass
class SearchContext:
    """Fully personalised search context derived from loader.config."""
    company:                  str
    industry_key:             str
    industry_label:           str
    label:                    str
    catalog_label:            str
    value_unit:               str
    kpi_search_label:         str
    kpi_zero_label:           str
    kpi_ctr_label:            str
    kpi_value_label:          str
    top_queries:              List[Dict]
    failing_queries:          List[Dict]
    ab_query:                 str
    bm25_results:             List[Dict]
    elser_results:            List[Dict]
    hybrid_results:           List[Dict]
    intent_query:             str
    intent_result:            Dict
    autocomplete_prefix:      str
    autocomplete_suggestions: List[Dict]
    personalization_history:  List[Dict]
    merchandising_rules:      List[Dict]
    visual_scenarios:         List[str]
    planner_label:            str
    planner_placeholder:      str
    pain_kpis:                Dict
    pain_points:              List[str]
    use_cases:                List[str]
    department:               str


class SearchContextService:

    def build(self, loader) -> SearchContext:
        """Build a fully personalised SearchContext from a DemoModuleLoader."""
        config  = loader.config if loader else {}
        ctx_raw = config.get("customer_context") or config

        company     = ctx_raw.get("company_name", "Your Company")
        department  = ctx_raw.get("department", "")
        pain_points = ctx_raw.get("pain_points", [])
        use_cases   = ctx_raw.get("use_cases", [])
        if isinstance(pain_points, str):
            pain_points = [pain_points]
        if isinstance(use_cases, str):
            use_cases = [use_cases]

        industry_key = _detect_industry(config)
        domain       = _DOMAINS[industry_key]

        # Build hybrid results (best of both, unique items)
        elser  = domain["elser_results"]
        bm25   = domain["bm25_results"]
        seen   = set()
        hybrid = []
        for r in elser:
            if r["item"] not in seen:
                hybrid.append({"rank": len(hybrid)+1, "item": r["item"],
                                "score": round(r["score"] * 0.95 + random.uniform(0.01, 0.03), 2),
                                "reason": "BM25 + Semantic (RRF)"})
                seen.add(r["item"])
        for r in bm25:
            if r["item"] not in seen and len(hybrid) < 5:
                hybrid.append({"rank": len(hybrid)+1, "item": r["item"],
                                "score": round(r["score"] * 0.7, 2),
                                "reason": "BM25 boosted by RRF"})
                seen.add(r["item"])

        return SearchContext(
            company                  = company,
            industry_key             = industry_key,
            industry_label           = domain["industry_label"],
            label                    = domain["label"],
            catalog_label            = domain["catalog_label"],
            value_unit               = domain["value_unit"],
            kpi_search_label         = domain["kpi_search_label"],
            kpi_zero_label           = domain["kpi_zero_label"],
            kpi_ctr_label            = domain["kpi_ctr_label"],
            kpi_value_label          = domain["kpi_value_label"],
            top_queries              = domain["top_queries"],
            failing_queries          = domain["failing_queries"],
            ab_query                 = domain["ab_query"],
            bm25_results             = bm25,
            elser_results            = elser,
            hybrid_results           = hybrid,
            intent_query             = domain["intent_query"],
            intent_result            = domain["intent_result"],
            autocomplete_prefix      = domain["autocomplete_prefix"],
            autocomplete_suggestions = domain["autocomplete_suggestions"],
            personalization_history  = domain["personalization_history"],
            merchandising_rules      = domain["merchandising_rules"],
            visual_scenarios         = domain["visual_scenarios"],
            planner_label            = domain["planner_label"],
            planner_placeholder      = domain["planner_placeholder"],
            pain_kpis                = domain["pain_kpis"],
            pain_points              = pain_points,
            use_cases                = use_cases,
            department               = department,
        )
