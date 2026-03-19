"""
Observability Strategy Generator
Generates query-first strategy for APM/Tracing, Infrastructure, and SLO demos.

Extends the analytics QueryStrategyGenerator with:
- OpenTelemetry / EDOT field requirements (trace.id, span.id, service.name, event.duration)
- SLO/SLI query generation (availability, latency, error rate)
- Service dependency map for topology visualization
- APM-namespaced index patterns (traces-apm-*, metrics-apm.*, logs-apm.*)
- Cross-service trace correlation (shared trace.id across parent-child spans)
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import logging

from src.services.security_ecs_schema import (
    ECS_APM_FIELDS,
    ECS_HOST_FIELDS,
    ECS_CLOUD_FIELDS,
    ECS_HTTP_FIELDS,
    get_index_patterns,
    get_ilm_policy,
)

logger = logging.getLogger(__name__)

# Dataset sizes for observability demos
OBS_SIZE_RANGES = {
    "apm":            {"timeseries": "10000-30000", "reference": "50-200"},
    "infrastructure": {"timeseries": "5000-20000",  "reference": "100-500"},
    "slo":            {"timeseries": "10000-20000",  "reference": "50-100"},
}

# Core APM fields every APM dataset must have
APM_REQUIRED_FIELDS = {
    "@timestamp": "date",
    "trace.id": "keyword",
    "transaction.id": "keyword",
    "service.name": "keyword",
    "service.version": "keyword",
    "service.environment": "keyword",
    "event.duration": "long",
    "transaction.type": "keyword",
    "transaction.result": "keyword",
    "http.response.status_code": "long",
    "processor.event": "keyword",
    "agent.name": "keyword",
}


class ObservabilityStrategyGenerator:
    """
    Generates observability-focused query strategy BEFORE data generation.

    Output structure:
    {
        "sub_category": "apm" | "infrastructure" | "slo",
        "datasets": [ DatasetRequirement... ],
        "queries": [ Query... ],            # ES|QL — latency, error rate, throughput
        "slo_queries": [ SLOQuery... ],     # SLI calculation + burn rate + error budget
        "service_map": {                    # Service topology
            "services": [...],
            "dependencies": [...],
            "entry_points": [...]
        },
        "text_fields": {},
        "index_patterns": ["traces-apm-*", ...],
        "ilm_policy": "apm_traces" | "observability_metrics"
    }
    """

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def generate_strategy(self, context: Dict) -> Dict:
        """Generate complete observability strategy from customer context."""
        company = context.get("company_name", "Customer")
        sub_category = context.get("sub_category", "apm")
        logger.info(f"Generating OBSERVABILITY/{sub_category.upper()} strategy for {company}")

        esql_skill = self._read_esql_skill()
        obs_skill = self._read_observability_skill()

        num_queries = 5
        max_retries = 4

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"Retry {attempt}: reducing to {num_queries} queries")

                prompt = self._build_prompt(context, esql_skill, obs_skill, num_queries, sub_category)

                response = self.llm_client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=10000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )

                strategy_text = response.content[0].text

                if self._is_likely_truncated(strategy_text):
                    logger.warning(f"Response truncated (attempt {attempt + 1}/{max_retries})")
                    num_queries = max(1, num_queries - 2)
                    if attempt < max_retries - 1:
                        continue

                strategy = self._extract_json(strategy_text)
                strategy = self._enrich_and_validate(strategy, sub_category)

                logger.info(
                    f"Observability strategy: {len(strategy.get('queries', []))} queries, "
                    f"{len(strategy.get('slo_queries', []))} SLOs, "
                    f"{len(strategy.get('service_map', {}).get('services', []))} services"
                )
                return strategy

            except ValueError as e:
                if "Invalid JSON" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"JSON parse failed (attempt {attempt + 1}): {e}")
                    num_queries = max(1, num_queries - 2)
                    continue
                raise
            except Exception as e:
                logger.error(f"Observability strategy generation failed: {e}", exc_info=True)
                raise

        raise ValueError("Failed to generate valid observability strategy after all retries")

    # -------------------------------------------------------------------------
    # Prompt Construction
    # -------------------------------------------------------------------------

    def _build_prompt(
        self,
        context: Dict,
        esql_skill: str,
        obs_skill: str,
        num_queries: int,
        sub_category: str,
    ) -> str:
        """Build the LLM prompt for observability strategy generation."""

        tech_stack = context.get("tech_stack", {})
        env_scale = context.get("environment_scale", {})
        index_patterns = get_index_patterns("observability")
        subcategory_guidance = self._get_subcategory_guidance(sub_category)

        return f"""You are an Elastic Observability expert designing an APM/Tracing demo for Elastic Agent Builder.

**Customer Context:**
- Company: {context.get('company_name')}
- Department: {context.get('department')}
- Industry: {context.get('industry')}
- Pain Points: {json.dumps(context.get('pain_points', []))}
- Use Cases: {json.dumps(context.get('use_cases', []))}
- Scale: {context.get('scale', 'Unknown')}
- Key Metrics: {json.dumps(context.get('metrics', []))}
- Tech Stack: {json.dumps(tech_stack)}
- Environment Scale: {json.dumps(env_scale)}
- Sub-Category: {sub_category.upper()}

**Sub-Category Guidance:**
{subcategory_guidance}

**MANDATORY APM ECS Field Names — Use EXACTLY These:**
{json.dumps(APM_REQUIRED_FIELDS, indent=2)}

**Additional OTEL / APM Fields Available:**
- span.id, span.name, span.type, span.subtype, span.action
- parent.id (links child spans to parent span)
- service.language.name, service.runtime.name, service.framework.name
- service.node.name (for horizontal scaling scenarios)
- labels.<custom_key> (for custom business tags)
- numeric_labels.<custom_key> (for custom numeric metrics)
- metricset.name, metricset.period (for metric documents)

**Recommended Index Patterns:**
- traces-apm-* (transaction and span documents, processor.event = transaction|span)
- metrics-apm.* (aggregated metrics, processor.event = metric)
- logs-apm.* (application logs correlated with traces)
- metrics-* (infrastructure metrics from EDOT/metricbeat)

**ES|QL Reference:**
{esql_skill}

**Observability Reference:**
{obs_skill}

**⚠️ APM DATA GENERATION RULES:**
1. trace.id must be SHARED across related span documents (same request = same trace.id)
2. Each transaction has one transaction.id; child spans have unique span.id but same trace.id
3. event.duration is in NANOSECONDS (1ms = 1,000,000 ns; 100ms = 100,000,000 ns)
4. processor.event values: "transaction" | "span" | "metric" | "error"
5. transaction.type values: "request" | "scheduled" | "message"
6. transaction.result values: "HTTP 2xx" | "HTTP 4xx" | "HTTP 5xx" | "success" | "failure"

**✅ APM ES|QL PATTERNS TO USE:**
1. P99 latency trend per service:
   ```
   FROM traces-apm-* | WHERE processor.event == "transaction"
   | STATS p99 = PERCENTILE(event.duration, 99), req_count = COUNT()
     BY service.name, DATE_TRUNC(1 hour, @timestamp)
   | EVAL p99_ms = p99 / 1000000 | SORT @timestamp ASC
   ```
2. Error rate by service:
   ```
   FROM traces-apm-* | WHERE processor.event == "transaction"
   | STATS total = COUNT(), errors = COUNT(CASE WHEN transaction.result LIKE "HTTP 5*" THEN 1 END)
     BY service.name
   | EVAL error_rate = errors / total * 100 | SORT error_rate DESC
   ```
3. Slow database queries:
   ```
   FROM traces-apm-* | WHERE span.type == "db" AND event.duration > 100000000
   | STATS avg_duration = AVG(event.duration), count = COUNT()
     BY span.db.statement, service.name
   | EVAL avg_ms = avg_duration / 1000000 | SORT avg_ms DESC | LIMIT 10
   ```
4. Service dependency latency:
   ```
   FROM traces-apm-* | WHERE span.type == "external"
   | STATS avg_lat = AVG(event.duration), p95 = PERCENTILE(event.duration, 95)
     BY service.name, service.target.name
   | EVAL avg_ms = avg_lat / 1000000 | SORT avg_ms DESC
   ```

**Your Task:**
Generate EXACTLY {num_queries} ES|QL queries + 2-3 SLO definitions + a service dependency map.

**Return ONLY valid JSON in this exact structure:**
```json
{{
  "sub_category": "{sub_category}",
  "datasets": [
    {{
      "name": "service_transactions",
      "type": "timeseries",
      "row_count": "10000-30000",
      "required_fields": {{
        "@timestamp": "date",
        "trace.id": "keyword",
        "transaction.id": "keyword",
        "service.name": "keyword",
        "service.version": "keyword",
        "service.environment": "keyword",
        "event.duration": "long",
        "transaction.type": "keyword",
        "transaction.result": "keyword",
        "http.response.status_code": "long",
        "processor.event": "keyword",
        "agent.name": "keyword"
      }},
      "relationships": [],
      "semantic_fields": []
    }}
  ],
  "queries": [
    {{
      "name": "P99 Latency by Service",
      "pain_point": "High latency impacting user experience",
      "esql_features": ["STATS", "PERCENTILE", "DATE_TRUNC", "EVAL"],
      "required_datasets": ["service_transactions"],
      "required_fields": {{"service_transactions": ["event.duration", "service.name", "@timestamp"]}},
      "description": "Shows p99 latency trend to identify service degradation",
      "complexity": "medium"
    }}
  ],
  "slo_queries": [
    {{
      "slo_name": "API Availability SLO",
      "service": "api-gateway",
      "sli_query": "FROM traces-apm-* | WHERE processor.event == \\"transaction\\" AND service.name == \\"api-gateway\\" | STATS good = COUNT(CASE WHEN transaction.result LIKE \\"HTTP 2*\\" THEN 1 END), total = COUNT() | EVAL sli = ROUND(good / total * 100, 3)",
      "target_percentage": 99.9,
      "window_days": 30,
      "burn_rate_query": "FROM traces-apm-* | WHERE processor.event == \\"transaction\\" AND service.name == \\"api-gateway\\" | STATS errors = COUNT(CASE WHEN transaction.result LIKE \\"HTTP 5*\\" THEN 1 END), total = COUNT() BY DATE_TRUNC(1 hour, @timestamp) | EVAL error_rate = errors / total",
      "error_budget_query": "FROM traces-apm-* | WHERE processor.event == \\"transaction\\" | STATS errors = COUNT(CASE WHEN transaction.result LIKE \\"HTTP 5*\\" THEN 1 END), total = COUNT() | EVAL error_budget_remaining = (0.001 * total - errors) / (0.001 * total) * 100"
    }}
  ],
  "service_map": {{
    "services": [
      {{"name": "api-gateway", "language": "go", "version": "1.0.0"}},
      {{"name": "checkout-service", "language": "python", "version": "2.0.0"}}
    ],
    "dependencies": [["api-gateway", "checkout-service"]],
    "entry_points": ["api-gateway"]
  }},
  "text_fields": {{}},
  "index_patterns": {json.dumps(index_patterns)},
  "ilm_policy": "apm_traces"
}}
```

IMPORTANT:
- event.duration values in datasets must be in NANOSECONDS (realistic: 1ms-5000ms range)
- trace.id must be consistent across related transactions and spans
- service.environment should be one of: production, staging, development
- All datasets should have @timestamp with realistic distribution over the last 30 days
"""

    def _get_subcategory_guidance(self, sub_category: str) -> str:
        guidance = {
            "apm": """Focus on: distributed tracing, latency analysis, error rate tracking.
- Generate realistic microservice architectures (3-8 services)
- Include service dependencies (API gateway → backend services → databases)
- Key pain points: high p99 latency, unknown error sources, slow DB queries
- Transaction types: HTTP requests, background jobs, message consumers""",

            "infrastructure": """Focus on: host metrics, container health, resource utilization.
- CPU, memory, disk, and network metrics per host
- Container/pod metrics if Kubernetes environment
- Key pain points: capacity planning, resource contention, infrastructure cost
- Use metrics-* and logs-* index patterns""",

            "slo": """Focus on: service reliability, error budget management, burn rate alerting.
- Define SLOs for availability (e.g. 99.9%) and latency (p99 < 500ms)
- Generate burn rate queries to detect SLO violations early
- Key metrics: error budget remaining, burn rate, SLI trend
- Compliance with SLA commitments""",
        }
        return guidance.get(sub_category, guidance["apm"])

    # -------------------------------------------------------------------------
    # Post-processing
    # -------------------------------------------------------------------------

    def _enrich_and_validate(self, strategy: Dict, sub_category: str) -> Dict:
        """Enforce APM fields, set defaults for missing keys."""

        strategy.setdefault("sub_category", sub_category)
        strategy.setdefault("slo_queries", [])
        strategy.setdefault("service_map", {"services": [], "dependencies": [], "entry_points": []})
        strategy.setdefault("text_fields", {})
        strategy.setdefault("index_patterns", get_index_patterns("observability"))
        strategy.setdefault("ilm_policy", "apm_traces")

        # Ensure every APM dataset has the core trace fields
        for dataset in strategy.get("datasets", []):
            fields = dataset.get("required_fields", {})
            if "trace.id" in fields or "event.duration" in fields:
                # This is an APM dataset — enforce required APM fields
                for field, ftype in APM_REQUIRED_FIELDS.items():
                    if field not in fields:
                        fields[field] = ftype

        return strategy

    # -------------------------------------------------------------------------
    # Skill / JSON helpers
    # -------------------------------------------------------------------------

    def _read_esql_skill(self) -> str:
        try:
            for path in [
                Path(".agents/skills/elasticsearch-esql/SKILL.md"),
                Path(".claude/skills/elasticsearch-esql/SKILL.md"),
            ]:
                if path.exists():
                    return path.read_text()[:3000]
        except Exception as e:
            logger.warning(f"Could not read ES|QL skill: {e}")
        return """ES|QL: FROM <index> | WHERE | STATS ... BY | INLINESTATS | EVAL | DATE_TRUNC | PERCENTILE | SORT | LIMIT"""

    def _read_observability_skill(self) -> str:
        try:
            for path in [
                Path(".agents/skills/observability-service-health/SKILL.md"),
                Path(".agents/skills/observability-manage-slos/SKILL.md"),
                Path(".claude/skills/observability-service-health/SKILL.md"),
            ]:
                if path.exists():
                    return path.read_text()[:2000]
        except Exception as e:
            logger.warning(f"Could not read observability skill: {e}")
        return """Kibana Observability: APM traces indexed in traces-apm-*, metrics in metrics-apm.*, logs in logs-apm.*.
SLOs defined via Kibana SLO API. Service maps built from span parent.id relationships."""

    def _is_likely_truncated(self, text: str) -> bool:
        text = text.rstrip()
        if not (text.endswith("}") or text.endswith("]") or text.endswith("```")):
            return True
        if "```json" in text and not text.endswith("```"):
            return True
        if abs(text.count("{") - text.count("}")) > 2:
            return True
        if abs(text.count("[") - text.count("]")) > 2:
            return True
        return False

    def _extract_json(self, text: str) -> Dict:
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            json_text = text[start:end].strip()
        else:
            json_text = text.strip()

        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed: {e} — attempting fix")
            try:
                import re
                fixed = re.sub(r",\s*([}\]])", r"\1", json_text)
                return json.loads(fixed)
            except json.JSONDecodeError as e2:
                raise ValueError(f"Invalid JSON in observability strategy response: {e2}")
