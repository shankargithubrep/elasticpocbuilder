"""
TDD tests for MOTLP (Managed OTLP) observability sub-category.

Tests cover:
- MOTLP field constants in security_ecs_schema
- ObservabilityStrategyGenerator routing for motlp sub-category
- Native OTLP field conventions (not ECS-translated)
- Correct index patterns (traces-generic.otel-default etc.)
- Dataset routing via data_stream.dataset
- Prompt contains MOTLP-specific guidance
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_llm(response_json: dict):
    """Return a mock LLM client that returns the given dict as a JSON response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=f"```json\n{json.dumps(response_json)}\n```")]
    mock_client.messages.create.return_value = mock_response
    return mock_client


def _minimal_motlp_strategy(sub_category="motlp"):
    return {
        "sub_category": sub_category,
        "datasets": [
            {
                "name": "otel_traces",
                "type": "timeseries",
                "row_count": "10000-30000",
                "required_fields": {
                    "@timestamp": "date",
                    "TraceId": "keyword",
                    "SpanId": "keyword",
                    "Name": "keyword",
                    "Duration": "long",
                    "StatusCode": "keyword",
                    "resource.attributes.service.name": "keyword",
                    "resource.attributes.deployment.environment": "keyword",
                    "data_stream.dataset": "keyword",
                },
                "relationships": [],
                "semantic_fields": [],
            }
        ],
        "queries": [
            {
                "name": "P99 Latency by Service (MOTLP)",
                "pain_point": "High latency",
                "esql_features": ["STATS", "PERCENTILE", "DATE_TRUNC"],
                "required_datasets": ["otel_traces"],
                "required_fields": {"otel_traces": ["Duration", "resource.attributes.service.name"]},
                "description": "P99 latency from MOTLP traces",
                "complexity": "medium",
            }
        ],
        "slo_queries": [
            {
                "slo_name": "API Availability",
                "service": "api-service",
                "sli_query": "FROM traces-generic.otel-default | STATS good = COUNT(CASE WHEN StatusCode == \"STATUS_CODE_OK\" THEN 1 END), total = COUNT() | EVAL sli = good / total * 100",
                "target_percentage": 99.9,
                "window_days": 30,
                "burn_rate_query": "FROM traces-generic.otel-default | STATS errors = COUNT(CASE WHEN StatusCode == \"STATUS_CODE_ERROR\" THEN 1 END), total = COUNT() BY DATE_TRUNC(1 hour, @timestamp) | EVAL error_rate = errors / total",
                "error_budget_query": "FROM traces-generic.otel-default | STATS errors = COUNT(CASE WHEN StatusCode == \"STATUS_CODE_ERROR\" THEN 1 END), total = COUNT() | EVAL budget = (0.001 * total - errors) / (0.001 * total) * 100",
            }
        ],
        "service_map": {
            "services": [
                {"name": "api-gateway", "language": "go", "version": "1.0.0"},
                {"name": "order-service", "language": "python", "version": "2.0.0"},
            ],
            "dependencies": [["api-gateway", "order-service"]],
            "entry_points": ["api-gateway"],
        },
        "text_fields": {},
        "index_patterns": [
            "traces-generic.otel-default",
            "metrics-generic.otel-default",
            "logs-generic.otel-default",
        ],
        "ilm_policy": "apm_traces",
    }


# ---------------------------------------------------------------------------
# 1. Schema constants
# ---------------------------------------------------------------------------

class TestMOTLPSchema:

    def test_motlp_index_patterns_exist(self):
        from src.services.security_ecs_schema import MOTLP_INDEX_PATTERNS
        assert "traces-generic.otel-default" in MOTLP_INDEX_PATTERNS
        assert "metrics-generic.otel-default" in MOTLP_INDEX_PATTERNS
        assert "logs-generic.otel-default" in MOTLP_INDEX_PATTERNS

    def test_motlp_required_fields_exist(self):
        from src.services.security_ecs_schema import MOTLP_REQUIRED_FIELDS
        # Native OTLP span fields
        assert "TraceId" in MOTLP_REQUIRED_FIELDS
        assert "SpanId" in MOTLP_REQUIRED_FIELDS
        assert "Duration" in MOTLP_REQUIRED_FIELDS
        assert "StatusCode" in MOTLP_REQUIRED_FIELDS
        assert "Name" in MOTLP_REQUIRED_FIELDS
        # Resource attributes
        assert "resource.attributes.service.name" in MOTLP_REQUIRED_FIELDS
        assert "resource.attributes.deployment.environment" in MOTLP_REQUIRED_FIELDS
        # Dataset routing
        assert "data_stream.dataset" in MOTLP_REQUIRED_FIELDS

    def test_motlp_field_types(self):
        from src.services.security_ecs_schema import MOTLP_REQUIRED_FIELDS
        assert MOTLP_REQUIRED_FIELDS["TraceId"] == "keyword"
        assert MOTLP_REQUIRED_FIELDS["Duration"] == "long"
        assert MOTLP_REQUIRED_FIELDS["@timestamp"] == "date"

    def test_get_index_patterns_motlp(self):
        from src.services.security_ecs_schema import get_index_patterns
        patterns = get_index_patterns("motlp")
        assert "traces-generic.otel-default" in patterns
        assert "metrics-generic.otel-default" in patterns

    def test_motlp_distinct_from_apm_patterns(self):
        from src.services.security_ecs_schema import get_index_patterns
        motlp = get_index_patterns("motlp")
        apm = get_index_patterns("observability")
        # MOTLP uses generic.otel, classic APM uses apm.*
        assert not any("apm" in p for p in motlp)
        assert any("generic.otel" in p for p in motlp)


# ---------------------------------------------------------------------------
# 2. ObservabilityStrategyGenerator — MOTLP routing
# ---------------------------------------------------------------------------

class TestObservabilityMOTLPRouting:

    def _make_context(self, sub="motlp"):
        return {
            "company_name": "Acme Corp",
            "department": "Platform Engineering",
            "industry": "E-commerce",
            "pain_points": ["high latency", "no trace visibility"],
            "use_cases": ["distributed tracing", "SLO management"],
            "scale": "500 services",
            "metrics": ["p99 latency", "error rate"],
            "sub_category": sub,
            "tech_stack": {"backend": "Go, Python"},
            "environment_scale": {"services": 50},
        }

    def test_motlp_strategy_returns_generic_otel_index_patterns(self):
        from src.services.observability_strategy_generator import ObservabilityStrategyGenerator
        gen = ObservabilityStrategyGenerator(_make_llm(_minimal_motlp_strategy()))
        result = gen.generate_strategy(self._make_context("motlp"))
        assert any("generic.otel" in p for p in result["index_patterns"])

    def test_motlp_strategy_enforces_required_fields(self):
        from src.services.observability_strategy_generator import ObservabilityStrategyGenerator
        gen = ObservabilityStrategyGenerator(_make_llm(_minimal_motlp_strategy()))
        result = gen.generate_strategy(self._make_context("motlp"))
        # Every MOTLP dataset should have TraceId and resource.attributes.service.name
        for ds in result["datasets"]:
            fields = ds.get("required_fields", {})
            if "TraceId" in fields or "resource.attributes.service.name" in fields:
                assert "TraceId" in fields
                assert "resource.attributes.service.name" in fields
                assert "Duration" in fields

    def test_motlp_strategy_has_data_stream_dataset_field(self):
        from src.services.observability_strategy_generator import ObservabilityStrategyGenerator
        gen = ObservabilityStrategyGenerator(_make_llm(_minimal_motlp_strategy()))
        result = gen.generate_strategy(self._make_context("motlp"))
        for ds in result["datasets"]:
            fields = ds.get("required_fields", {})
            if "TraceId" in fields:
                assert "data_stream.dataset" in fields, "MOTLP datasets must include data_stream.dataset for routing"

    def test_motlp_strategy_sets_sub_category(self):
        from src.services.observability_strategy_generator import ObservabilityStrategyGenerator
        gen = ObservabilityStrategyGenerator(_make_llm(_minimal_motlp_strategy()))
        result = gen.generate_strategy(self._make_context("motlp"))
        assert result["sub_category"] == "motlp"

    def test_motlp_slo_queries_use_generic_otel_index(self):
        from src.services.observability_strategy_generator import ObservabilityStrategyGenerator
        gen = ObservabilityStrategyGenerator(_make_llm(_minimal_motlp_strategy()))
        result = gen.generate_strategy(self._make_context("motlp"))
        for slo in result.get("slo_queries", []):
            assert "generic.otel" in slo.get("sli_query", "") or "generic.otel" in slo.get("burn_rate_query", "")

    def test_apm_strategy_unchanged(self):
        """Existing APM sub-category should NOT be affected."""
        from src.services.observability_strategy_generator import ObservabilityStrategyGenerator
        apm_strategy = {**_minimal_motlp_strategy("apm")}
        apm_strategy["index_patterns"] = ["traces-apm-*", "metrics-apm.*", "logs-apm.*"]
        apm_strategy["datasets"][0]["required_fields"] = {
            "@timestamp": "date",
            "trace.id": "keyword",
            "transaction.id": "keyword",
            "service.name": "keyword",
            "event.duration": "long",
            "processor.event": "keyword",
            "service.version": "keyword",
            "service.environment": "keyword",
            "transaction.type": "keyword",
            "transaction.result": "keyword",
            "http.response.status_code": "long",
            "agent.name": "keyword",
        }
        gen = ObservabilityStrategyGenerator(_make_llm(apm_strategy))
        result = gen.generate_strategy(self._make_context("apm"))
        assert result["sub_category"] == "apm"
        assert any("apm" in p for p in result["index_patterns"])


# ---------------------------------------------------------------------------
# 3. Prompt content validation
# ---------------------------------------------------------------------------

class TestMOTLPPromptContent:

    def test_motlp_prompt_mentions_generic_otel_index(self):
        from src.services.observability_strategy_generator import ObservabilityStrategyGenerator
        gen = ObservabilityStrategyGenerator(MagicMock())
        prompt = gen._build_prompt(
            {"company_name": "Acme", "department": "Eng", "industry": "Tech",
             "pain_points": [], "use_cases": [], "scale": "100", "metrics": [],
             "tech_stack": {}, "environment_scale": {}, "sub_category": "motlp"},
            esql_skill="ES|QL reference",
            obs_skill="Obs reference",
            num_queries=3,
            sub_category="motlp",
        )
        assert "generic.otel" in prompt
        assert "MOTLP" in prompt or "Managed OTLP" in prompt

    def test_motlp_prompt_mentions_resource_attributes(self):
        from src.services.observability_strategy_generator import ObservabilityStrategyGenerator
        gen = ObservabilityStrategyGenerator(MagicMock())
        prompt = gen._build_prompt(
            {"company_name": "Acme", "department": "Eng", "industry": "Tech",
             "pain_points": [], "use_cases": [], "scale": "100", "metrics": [],
             "tech_stack": {}, "environment_scale": {}, "sub_category": "motlp"},
            esql_skill="",
            obs_skill="",
            num_queries=3,
            sub_category="motlp",
        )
        assert "resource.attributes" in prompt

    def test_motlp_prompt_mentions_traceid_not_trace_id(self):
        """MOTLP uses TraceId (OTLP native), not trace.id (ECS)."""
        from src.services.observability_strategy_generator import ObservabilityStrategyGenerator
        gen = ObservabilityStrategyGenerator(MagicMock())
        prompt = gen._build_prompt(
            {"company_name": "Acme", "department": "Eng", "industry": "Tech",
             "pain_points": [], "use_cases": [], "scale": "100", "metrics": [],
             "tech_stack": {}, "environment_scale": {}, "sub_category": "motlp"},
            esql_skill="",
            obs_skill="",
            num_queries=3,
            sub_category="motlp",
        )
        assert "TraceId" in prompt

    def test_motlp_prompt_includes_sdk_config_guidance(self):
        """MOTLP demos should guide users on OTEL_EXPORTER_OTLP_ENDPOINT."""
        from src.services.observability_strategy_generator import ObservabilityStrategyGenerator
        gen = ObservabilityStrategyGenerator(MagicMock())
        prompt = gen._build_prompt(
            {"company_name": "Acme", "department": "Eng", "industry": "Tech",
             "pain_points": [], "use_cases": [], "scale": "100", "metrics": [],
             "tech_stack": {}, "environment_scale": {}, "sub_category": "motlp"},
            esql_skill="",
            obs_skill="",
            num_queries=3,
            sub_category="motlp",
        )
        assert "OTEL_EXPORTER_OTLP_ENDPOINT" in prompt or "OTEL_EXPORTER" in prompt

    def test_motlp_prompt_mentions_data_stream_dataset_routing(self):
        from src.services.observability_strategy_generator import ObservabilityStrategyGenerator
        gen = ObservabilityStrategyGenerator(MagicMock())
        prompt = gen._build_prompt(
            {"company_name": "Acme", "department": "Eng", "industry": "Tech",
             "pain_points": [], "use_cases": [], "scale": "100", "metrics": [],
             "tech_stack": {}, "environment_scale": {}, "sub_category": "motlp"},
            esql_skill="",
            obs_skill="",
            num_queries=3,
            sub_category="motlp",
        )
        assert "data_stream.dataset" in prompt


# ---------------------------------------------------------------------------
# 4. Backward compat — all 3 existing sub-categories unaffected
# ---------------------------------------------------------------------------

class TestExistingSubCategoriesUnchanged:

    @pytest.mark.parametrize("sub", ["apm", "infrastructure", "slo"])
    def test_existing_sub_categories_still_work(self, sub):
        from src.services.observability_strategy_generator import ObservabilityStrategyGenerator
        strategy = _minimal_motlp_strategy(sub)
        if sub == "apm":
            strategy["index_patterns"] = ["traces-apm-*", "metrics-apm.*"]
            strategy["datasets"][0]["required_fields"] = {
                "@timestamp": "date", "trace.id": "keyword", "event.duration": "long",
                "service.name": "keyword", "transaction.id": "keyword",
                "service.version": "keyword", "service.environment": "keyword",
                "transaction.type": "keyword", "transaction.result": "keyword",
                "http.response.status_code": "long", "processor.event": "keyword",
                "agent.name": "keyword",
            }
        gen = ObservabilityStrategyGenerator(_make_llm(strategy))
        result = gen.generate_strategy({
            "company_name": "Test", "department": "Eng", "industry": "Tech",
            "pain_points": [], "use_cases": [], "scale": "100", "metrics": [],
            "sub_category": sub, "tech_stack": {}, "environment_scale": {},
        })
        assert result["sub_category"] == sub
