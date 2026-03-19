"""
TDD tests for SecurityQueryStrategyGenerator and ObservabilityStrategyGenerator.

Written BEFORE implementation. Tests define the contract each generator must fulfill.
Run with:  python -m pytest tests/test_security_strategy.py -v
"""

import unittest
from unittest.mock import Mock, patch
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.security_ecs_schema import (
    get_fields_for_subcategory, list_ip_fields,
    get_mitre_tactic, get_mitre_technique,
    get_severity_risk_score, MITRE_TACTICS, MITRE_TECHNIQUES
)
from src.framework.base import DemoConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mock_llm(response_json: dict) -> Mock:
    """Return a mock LLM client that returns a fixed JSON response."""
    mock = Mock()
    mock_response = Mock()
    mock_response.content = [Mock()]
    mock_response.content[0].text = json.dumps(response_json)
    mock.messages.create.return_value = mock_response
    return mock


def minimal_strategy(sub_category: str = "siem") -> dict:
    """Return a minimal valid strategy dict for a given sub-category."""
    return {
        "sub_category": sub_category,
        "datasets": [
            {
                "name": "auth_events",
                "type": "timeseries",
                "row_count": "5000-10000",
                "required_fields": {
                    "@timestamp": "date",
                    "event.category": "keyword",
                    "event.outcome": "keyword",
                    "user.name": "keyword",
                    "host.name": "keyword",
                    "source.ip": "ip",
                },
                "relationships": [],
                "semantic_fields": [],
            }
        ],
        "queries": [
            {
                "name": "Failed Login Spike Detection",
                "pain_point": "Detect brute-force login attempts",
                "esql_features": ["STATS", "WHERE", "SORT"],
                "required_datasets": ["auth_events"],
                "required_fields": {"auth_events": ["@timestamp", "event.outcome", "user.name", "source.ip"]},
                "description": "Identifies users with abnormal failed login counts",
                "complexity": "medium",
                "mitre_technique_id": "T1110",
                "severity": "high",
            }
        ],
        "detection_rules": [
            {
                "rule_id": "brute-force-001",
                "name": "Brute Force Login Detection",
                "description": "Detects password spraying via auth failure spikes",
                "language": "eql",
                "query": "sequence by user.name [authentication where event.outcome == 'failure'] with maxspan=5m",
                "severity": "high",
                "risk_score": 73,
                "mitre_tactic_id": "TA0006",
                "mitre_tactic_name": "Credential Access",
                "mitre_technique_id": "T1110",
                "mitre_technique_name": "Brute Force",
                "index_patterns": ["logs-*", "winlogbeat-*"],
                "tags": ["brute-force", "authentication"],
                "interval": "5m",
                "from": "now-6m",
            }
        ],
        "timeline_queries": [
            {
                "step": 1,
                "phase": "Credential Access",
                "name": "Failed Auth Events",
                "description": "Identify authentication failures",
                "esql": "FROM logs-* | WHERE event.category == \"authentication\" AND event.outcome == \"failure\" | STATS count = COUNT() BY user.name, source.ip | SORT count DESC | LIMIT 20",
                "expected_finding": "Users with >50 failures from a single IP",
                "mitre_technique_id": "T1110",
            }
        ],
        "text_fields": {},
        "index_patterns": ["logs-*", "winlogbeat-*"],
        "ilm_policy": "security_logs",
    }


# ===========================================================================
# ECS Schema Tests (no LLM needed)
# ===========================================================================

class TestECSSchema(unittest.TestCase):
    """Verify the ECS schema registry is correct and complete."""

    def test_siem_has_required_base_fields(self):
        """SIEM field set must include ECS base event fields."""
        fields = get_fields_for_subcategory("siem")
        required = ["@timestamp", "event.category", "event.outcome", "event.severity",
                    "user.name", "host.name", "source.ip", "destination.ip"]
        for f in required:
            self.assertIn(f, fields, f"Missing required SIEM field: {f}")

    def test_edr_has_process_fields(self):
        """EDR field set must include process ancestry and hash fields."""
        fields = get_fields_for_subcategory("edr")
        required = ["process.name", "process.executable", "process.pid",
                    "process.parent.pid", "process.hash.sha256", "process.command_line"]
        for f in required:
            self.assertIn(f, fields, f"Missing required EDR field: {f}")

    def test_xdr_has_all_three_domains(self):
        """XDR must combine process + network + file fields."""
        fields = get_fields_for_subcategory("xdr")
        self.assertIn("process.name", fields)         # endpoint
        self.assertIn("source.ip", fields)            # network
        self.assertIn("file.hash.sha256", fields)     # file

    def test_apm_has_trace_fields(self):
        """APM field set must include distributed tracing fields."""
        fields = get_fields_for_subcategory("apm")
        required = ["trace.id", "transaction.id", "span.id", "service.name",
                    "event.duration", "transaction.type", "span.type"]
        for f in required:
            self.assertIn(f, fields, f"Missing required APM field: {f}")

    def test_ip_fields_are_ip_type(self):
        """All IP fields must be typed as 'ip', not keyword."""
        all_fields = get_fields_for_subcategory("siem")
        ip_fields = list_ip_fields("siem")
        for f in ip_fields:
            self.assertEqual(all_fields[f], "ip", f"Field {f} should be type 'ip'")

    def test_ip_fields_not_empty_for_security(self):
        """Security sub-categories must have at least 2 IP-type fields."""
        for sc in ["siem", "xdr", "edr", "threat_hunting"]:
            ip_fields = list_ip_fields(sc)
            self.assertGreaterEqual(len(ip_fields), 2,
                f"{sc} should have >= 2 IP fields, got {len(ip_fields)}")

    def test_mitre_tactics_all_present(self):
        """All 14 MITRE enterprise tactics must be in the registry."""
        expected_tactics = [
            "TA0001", "TA0002", "TA0003", "TA0004", "TA0005",
            "TA0006", "TA0007", "TA0008", "TA0009", "TA0010",
            "TA0011", "TA0040", "TA0042", "TA0043"
        ]
        for tactic_id in expected_tactics:
            result = get_mitre_tactic(tactic_id)
            self.assertIn("name", result, f"MITRE tactic {tactic_id} missing 'name'")

    def test_mitre_technique_lookup(self):
        """Common technique IDs must resolve correctly."""
        cases = {
            "T1110": "Brute Force",
            "T1078": "Valid Accounts",
            "T1059": "Command and Scripting Interpreter",
            "T1566": "Phishing",
        }
        for technique_id, expected_name in cases.items():
            result = get_mitre_technique(technique_id)
            self.assertEqual(result.get("name"), expected_name,
                f"T{technique_id} name mismatch")

    def test_severity_risk_scores(self):
        """Risk scores must follow Kibana conventions."""
        self.assertEqual(get_severity_risk_score("low"), 21)
        self.assertEqual(get_severity_risk_score("medium"), 47)
        self.assertEqual(get_severity_risk_score("high"), 73)
        self.assertEqual(get_severity_risk_score("critical"), 99)

    def test_unknown_subcategory_returns_base_fields(self):
        """Unknown sub-category should return base fields, not crash."""
        fields = get_fields_for_subcategory("nonexistent")
        self.assertIn("@timestamp", fields)
        self.assertIn("host.name", fields)


# ===========================================================================
# DemoConfig Extension Tests
# ===========================================================================

class TestDemoConfigExtension(unittest.TestCase):
    """Verify DemoConfig backward compatibility and new pillar fields."""

    def test_existing_demos_still_construct(self):
        """Existing 7-field DemoConfig must still work without new fields."""
        config = DemoConfig(
            company_name="Acme",
            department="Sales",
            industry="Tech",
            pain_points=["slow queries"],
            use_cases=["analytics"],
            scale="1000 users",
            metrics=["revenue"],
        )
        self.assertEqual(config.pillar, "search")     # default
        self.assertEqual(config.sub_category, "")     # default
        self.assertEqual(config.compliance_frameworks, [])
        self.assertEqual(config.mitre_tactics, [])

    def test_security_config_construction(self):
        """Security DemoConfig must accept all new pillar fields."""
        config = DemoConfig(
            company_name="SecureCorp",
            department="SOC",
            industry="Financial",
            pain_points=["alert fatigue", "slow triage"],
            use_cases=["siem", "threat hunting"],
            scale="10000 endpoints",
            metrics=["MTTD", "MTTR"],
            pillar="security",
            sub_category="siem",
            compliance_frameworks=["SOC2", "PCI-DSS"],
            mitre_tactics=["TA0001", "TA0006"],
            data_sources=["windows_events", "firewall"],
            tech_stack={"cloud": "aws", "os": "windows"},
        )
        self.assertEqual(config.pillar, "security")
        self.assertEqual(config.sub_category, "siem")
        self.assertIn("SOC2", config.compliance_frameworks)
        self.assertIn("TA0001", config.mitre_tactics)

    def test_observability_config_construction(self):
        """Observability DemoConfig must accept APM fields."""
        config = DemoConfig(
            company_name="CloudCo",
            department="Platform Engineering",
            industry="Technology",
            pain_points=["high latency", "unknown errors"],
            use_cases=["apm", "slo management"],
            scale="30 microservices",
            metrics=["p99 latency", "error rate"],
            pillar="observability",
            sub_category="apm",
            tech_stack={"language": "python", "framework": "fastapi", "cloud": "gcp"},
            environment_scale={"services": 30, "requests_per_second": 5000},
        )
        self.assertEqual(config.pillar, "observability")
        self.assertEqual(config.sub_category, "apm")
        self.assertEqual(config.tech_stack["language"], "python")


# ===========================================================================
# SecurityQueryStrategyGenerator Contract Tests
# ===========================================================================

class TestSecurityStrategyGeneratorContract(unittest.TestCase):
    """
    Define the contract SecurityQueryStrategyGenerator must fulfill.
    Tests run against a mock LLM to validate output structure without API calls.
    """

    def setUp(self):
        """Set up mock LLM and import the generator (may not exist yet — that's OK for TDD)."""
        try:
            from src.services.security_strategy_generator import SecurityQueryStrategyGenerator
            self.GeneratorClass = SecurityQueryStrategyGenerator
        except ImportError:
            self.skipTest("SecurityQueryStrategyGenerator not yet implemented")

        self.mock_strategy = minimal_strategy("siem")
        self.mock_llm = make_mock_llm(self.mock_strategy)
        self.generator = self.GeneratorClass(self.mock_llm)

        self.siem_context = {
            "company_name": "FinBank",
            "department": "SOC",
            "industry": "Financial Services",
            "pain_points": ["Too many false positive alerts", "Slow threat detection"],
            "use_cases": ["SIEM", "alert triage"],
            "scale": "5000 endpoints",
            "metrics": ["MTTD", "MTTR", "false positive rate"],
            "pillar": "security",
            "sub_category": "siem",
            "compliance_frameworks": ["PCI-DSS", "SOC2"],
            "mitre_tactics": ["TA0001", "TA0006"],
            "data_sources": ["windows_events", "firewall_logs"],
        }

    def test_generate_strategy_returns_dict(self):
        """generate_strategy() must return a dict."""
        result = self.generator.generate_strategy(self.siem_context)
        self.assertIsInstance(result, dict)

    def test_strategy_has_datasets_key(self):
        """Strategy must contain 'datasets' list."""
        result = self.generator.generate_strategy(self.siem_context)
        self.assertIn("datasets", result)
        self.assertIsInstance(result["datasets"], list)
        self.assertGreater(len(result["datasets"]), 0)

    def test_strategy_has_queries_key(self):
        """Strategy must contain 'queries' list."""
        result = self.generator.generate_strategy(self.siem_context)
        self.assertIn("queries", result)
        self.assertIsInstance(result["queries"], list)
        self.assertGreater(len(result["queries"]), 0)

    def test_strategy_has_detection_rules(self):
        """Security strategy must contain 'detection_rules' list."""
        result = self.generator.generate_strategy(self.siem_context)
        self.assertIn("detection_rules", result)
        self.assertIsInstance(result["detection_rules"], list)

    def test_strategy_has_timeline_queries(self):
        """Security strategy must contain 'timeline_queries' list."""
        result = self.generator.generate_strategy(self.siem_context)
        self.assertIn("timeline_queries", result)
        self.assertIsInstance(result["timeline_queries"], list)

    def test_datasets_have_ecs_timestamp(self):
        """All security datasets must include @timestamp field."""
        result = self.generator.generate_strategy(self.siem_context)
        for dataset in result["datasets"]:
            fields = dataset.get("required_fields", {})
            self.assertIn("@timestamp", fields,
                f"Dataset '{dataset.get('name')}' missing @timestamp")

    def test_datasets_have_event_category(self):
        """All security datasets must include event.category (ECS base field)."""
        result = self.generator.generate_strategy(self.siem_context)
        for dataset in result["datasets"]:
            fields = dataset.get("required_fields", {})
            self.assertIn("event.category", fields,
                f"Dataset '{dataset.get('name')}' missing event.category")

    def test_ip_fields_typed_correctly(self):
        """Any field named *.ip or source.ip/destination.ip must be typed 'ip'."""
        result = self.generator.generate_strategy(self.siem_context)
        for dataset in result["datasets"]:
            fields = dataset.get("required_fields", {})
            for field_name, field_type in fields.items():
                if field_name.endswith(".ip") or field_name in ("source.ip", "destination.ip"):
                    self.assertEqual(field_type, "ip",
                        f"Field {field_name} in '{dataset.get('name')}' should be type 'ip', got '{field_type}'")

    def test_detection_rules_have_required_structure(self):
        """Each detection rule must have required Kibana Detection Engine fields."""
        result = self.generator.generate_strategy(self.siem_context)
        required_rule_fields = ["rule_id", "name", "language", "query", "severity",
                                 "risk_score", "mitre_tactic_id", "index_patterns"]
        for rule in result.get("detection_rules", []):
            for f in required_rule_fields:
                self.assertIn(f, rule, f"Detection rule missing field: {f}")

    def test_detection_rules_use_eql_or_esql(self):
        """Detection rules must use EQL or ES|QL, not KQL (for authenticity)."""
        result = self.generator.generate_strategy(self.siem_context)
        for rule in result.get("detection_rules", []):
            self.assertIn(rule.get("language"), ["eql", "esql"],
                f"Detection rule '{rule.get('name')}' uses unexpected language: {rule.get('language')}")

    def test_detection_rules_severity_is_valid(self):
        """Detection rule severity must be one of the valid Kibana values."""
        valid = {"low", "medium", "high", "critical"}
        result = self.generator.generate_strategy(self.siem_context)
        for rule in result.get("detection_rules", []):
            self.assertIn(rule.get("severity"), valid,
                f"Invalid severity '{rule.get('severity')}' in rule '{rule.get('name')}'")

    def test_timeline_queries_are_ordered(self):
        """Timeline queries must have sequential 'step' numbers starting at 1."""
        result = self.generator.generate_strategy(self.siem_context)
        steps = [q.get("step") for q in result.get("timeline_queries", [])]
        if steps:
            self.assertEqual(steps[0], 1, "Timeline must start at step 1")
            for i, step in enumerate(steps):
                self.assertEqual(step, i + 1, f"Timeline step out of order at position {i}")

    def test_timeline_queries_have_esql(self):
        """Timeline queries must use ES|QL (not EQL) for investigation."""
        result = self.generator.generate_strategy(self.siem_context)
        for query in result.get("timeline_queries", []):
            esql = query.get("esql", "")
            self.assertTrue(len(esql) > 0,
                f"Timeline query '{query.get('name')}' has empty ES|QL")
            # ES|QL queries use FROM keyword (not EQL sequence syntax)
            self.assertIn("FROM", esql.upper(),
                f"Timeline query '{query.get('name')}' doesn't look like ES|QL (missing FROM)")

    def test_strategy_includes_index_patterns(self):
        """Strategy must specify index patterns for the sub-category."""
        result = self.generator.generate_strategy(self.siem_context)
        self.assertIn("index_patterns", result)
        self.assertIsInstance(result["index_patterns"], list)
        self.assertGreater(len(result["index_patterns"]), 0)

    def test_strategy_includes_ilm_policy(self):
        """Security strategy must specify an ILM retention policy."""
        result = self.generator.generate_strategy(self.siem_context)
        self.assertIn("ilm_policy", result)
        self.assertIn(result["ilm_policy"],
            ["security_logs", "security_alerts", "compliance_audit"],
            "ILM policy must be a known security policy")


# ===========================================================================
# ObservabilityStrategyGenerator Contract Tests
# ===========================================================================

class TestObservabilityStrategyGeneratorContract(unittest.TestCase):
    """
    Define the contract ObservabilityStrategyGenerator must fulfill.
    """

    def setUp(self):
        try:
            from src.services.observability_strategy_generator import ObservabilityStrategyGenerator
            self.GeneratorClass = ObservabilityStrategyGenerator
        except ImportError:
            self.skipTest("ObservabilityStrategyGenerator not yet implemented")

        self.apm_strategy = {
            "sub_category": "apm",
            "datasets": [
                {
                    "name": "service_transactions",
                    "type": "timeseries",
                    "row_count": "10000-20000",
                    "required_fields": {
                        "@timestamp": "date",
                        "trace.id": "keyword",
                        "transaction.id": "keyword",
                        "service.name": "keyword",
                        "event.duration": "long",
                        "transaction.type": "keyword",
                        "transaction.result": "keyword",
                        "http.response.status_code": "long",
                    },
                    "relationships": [],
                    "semantic_fields": [],
                }
            ],
            "queries": [
                {
                    "name": "P99 Latency by Service",
                    "pain_point": "High latency in checkout service",
                    "esql_features": ["STATS", "PERCENTILE", "DATE_TRUNC"],
                    "required_datasets": ["service_transactions"],
                    "required_fields": {"service_transactions": ["event.duration", "service.name"]},
                    "description": "Shows p99 latency trend per service",
                    "complexity": "medium",
                }
            ],
            "slo_queries": [
                {
                    "slo_name": "Checkout API Availability",
                    "service": "checkout-service",
                    "sli_query": "FROM traces-apm-* | WHERE service.name == \"checkout-service\" | STATS good = COUNT(CASE WHEN http.response.status_code < 500 THEN 1 END), total = COUNT() | EVAL sli = good / total * 100",
                    "target_percentage": 99.9,
                    "window_days": 30,
                    "burn_rate_query": "FROM traces-apm-* | ...",
                    "error_budget_query": "FROM traces-apm-* | ...",
                }
            ],
            "service_map": {
                "services": [
                    {"name": "api-gateway", "language": "go", "version": "1.2.0"},
                    {"name": "checkout-service", "language": "python", "version": "2.1.0"},
                ],
                "dependencies": [["api-gateway", "checkout-service"]],
                "entry_points": ["api-gateway"],
            },
            "text_fields": {},
            "index_patterns": ["traces-apm-*", "metrics-apm.*", "logs-apm.*"],
        }

        self.mock_llm = make_mock_llm(self.apm_strategy)
        self.generator = self.GeneratorClass(self.mock_llm)

        self.apm_context = {
            "company_name": "ShopFast",
            "department": "Platform Engineering",
            "industry": "E-commerce",
            "pain_points": ["P99 latency spikes", "Unknown error sources"],
            "use_cases": ["APM", "distributed tracing", "SLO management"],
            "scale": "30 microservices, 5000 rps",
            "metrics": ["p99 latency", "error rate", "throughput"],
            "pillar": "observability",
            "sub_category": "apm",
            "tech_stack": {"language": "python", "cloud": "aws"},
        }

    def test_generate_strategy_returns_dict(self):
        result = self.generator.generate_strategy(self.apm_context)
        self.assertIsInstance(result, dict)

    def test_apm_strategy_has_trace_fields(self):
        """APM datasets must include trace.id, service.name, event.duration."""
        result = self.generator.generate_strategy(self.apm_context)
        for dataset in result.get("datasets", []):
            fields = dataset.get("required_fields", {})
            # At least one dataset must have core APM fields
            has_trace = "trace.id" in fields
            has_service = "service.name" in fields
            has_duration = "event.duration" in fields
            if has_trace or has_service or has_duration:
                # Found an APM dataset — verify all three are present
                self.assertTrue(has_trace, f"APM dataset '{dataset.get('name')}' missing trace.id")
                self.assertTrue(has_service, f"APM dataset '{dataset.get('name')}' missing service.name")
                self.assertTrue(has_duration, f"APM dataset '{dataset.get('name')}' missing event.duration")
                return
        self.fail("No dataset found with APM trace fields (trace.id, service.name, event.duration)")

    def test_apm_strategy_has_slo_queries(self):
        """Observability strategy must contain SLO queries."""
        result = self.generator.generate_strategy(self.apm_context)
        self.assertIn("slo_queries", result)
        self.assertIsInstance(result["slo_queries"], list)
        self.assertGreater(len(result["slo_queries"]), 0)

    def test_slo_queries_have_required_fields(self):
        """Each SLO query must have target_percentage and window_days."""
        result = self.generator.generate_strategy(self.apm_context)
        for slo in result.get("slo_queries", []):
            self.assertIn("slo_name", slo)
            self.assertIn("target_percentage", slo)
            self.assertIn("window_days", slo)
            self.assertIn("sli_query", slo)

    def test_apm_strategy_has_service_map(self):
        """Observability strategy must include a service dependency map."""
        result = self.generator.generate_strategy(self.apm_context)
        self.assertIn("service_map", result)
        service_map = result["service_map"]
        self.assertIn("services", service_map)
        self.assertIn("dependencies", service_map)
        self.assertIn("entry_points", service_map)

    def test_apm_index_patterns_use_apm_namespace(self):
        """APM strategies must use apm-namespaced index patterns."""
        result = self.generator.generate_strategy(self.apm_context)
        patterns = result.get("index_patterns", [])
        has_apm_pattern = any("apm" in p.lower() for p in patterns)
        self.assertTrue(has_apm_pattern,
            f"APM strategy should use apm-namespaced index patterns, got: {patterns}")


# ===========================================================================
# Integration: DemoConfig feeds SecurityStrategyGenerator correctly
# ===========================================================================

class TestSecurityConfigToStrategy(unittest.TestCase):
    """Verify DemoConfig.pillar + sub_category are correctly forwarded to the generator."""

    def setUp(self):
        try:
            from src.services.security_strategy_generator import SecurityQueryStrategyGenerator
            self.GeneratorClass = SecurityQueryStrategyGenerator
        except ImportError:
            self.skipTest("SecurityQueryStrategyGenerator not yet implemented")

    def test_config_fields_passed_to_context(self):
        """pillar, sub_category, compliance_frameworks must appear in context dict."""
        config = DemoConfig(
            company_name="MedCo",
            department="IT Security",
            industry="Healthcare",
            pain_points=["HIPAA compliance gaps"],
            use_cases=["compliance auditing"],
            scale="200 endpoints",
            metrics=["audit coverage"],
            pillar="security",
            sub_category="compliance",
            compliance_frameworks=["HIPAA", "SOC2"],
            mitre_tactics=["TA0006"],
        )

        # Simulate how the orchestrator will convert DemoConfig to context dict
        context = {
            "company_name": config.company_name,
            "department": config.department,
            "industry": config.industry,
            "pain_points": config.pain_points,
            "use_cases": config.use_cases,
            "scale": config.scale,
            "metrics": config.metrics,
            "pillar": config.pillar,
            "sub_category": config.sub_category,
            "compliance_frameworks": config.compliance_frameworks,
            "mitre_tactics": config.mitre_tactics,
            "data_sources": config.data_sources,
            "tech_stack": config.tech_stack,
        }

        self.assertEqual(context["pillar"], "security")
        self.assertEqual(context["sub_category"], "compliance")
        self.assertIn("HIPAA", context["compliance_frameworks"])
        self.assertIn("TA0006", context["mitre_tactics"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
