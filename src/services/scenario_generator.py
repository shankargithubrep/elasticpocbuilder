"""
Scenario Generator — LLM-generates realistic demo scenarios per pillar.

Each scenario describes:
  - What breaks (anomaly_type, affected_service, field_overrides)
  - When it starts (trigger_after_seconds)
  - How long it lasts (duration_seconds)
  - What Kibana alerts should fire (expected_alerts)

Pillar-specific scenarios:
  observability: latency_spike, error_surge, slo_breach, db_slowdown
  security:      attack (brute force, lateral movement, data exfil, privilege escalation)
  search:        query_surge, relevance_drop, index_unavailable
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Always include a "Normal Operations" baseline scenario
NORMAL_SCENARIO = {
    "name": "Normal Operations",
    "description": "Baseline traffic — all services healthy, no anomalies injected.",
    "trigger_after_seconds": 0,
    "duration_seconds": 3600,
    "anomaly_type": "normal",
    "affected_service": "all",
    "severity": "low",
    "field_overrides": {},
    "expected_alerts": [],
}


class ScenarioGenerator:
    """Generates demo scenarios via LLM for a given demo config."""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def generate(self, config: Dict) -> List[Dict]:
        """
        Generate scenarios for a demo module.

        Returns a list of scenario dicts ready to write to scenarios.json.
        Always includes a 'Normal Operations' baseline as the first entry.
        """
        pillar = config.get("pillar", "observability")
        sub_category = config.get("sub_category", "apm")
        company = config.get("company_name", "Customer")
        datasets = config.get("datasets", [])

        logger.info(f"Generating scenarios for {company} — {pillar}/{sub_category}")

        prompt = self._build_prompt(config, pillar, sub_category, datasets)

        try:
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = response.content[0].text
            scenarios = self._extract_json(raw)

            # Validate and normalise
            scenarios = self._normalise(scenarios)

            # Ensure Normal Operations is always first
            if not any(s.get("anomaly_type") == "normal" for s in scenarios):
                scenarios.insert(0, NORMAL_SCENARIO)

            logger.info(f"Generated {len(scenarios)} scenarios for {company}")
            return scenarios

        except Exception as e:
            logger.error(f"Scenario generation failed: {e}", exc_info=True)
            return self._fallback_scenarios(pillar, sub_category)

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_prompt(self, config: Dict, pillar: str, sub_category: str, datasets: List) -> str:
        company = config.get("company_name", "Customer")
        industry = config.get("industry", "Technology")
        pain_points = config.get("pain_points", [])

        # Collect field names from strategy datasets for realistic overrides
        available_fields: Dict[str, str] = {}
        for ds in datasets:
            if isinstance(ds, dict):
                available_fields.update(ds.get("required_fields", {}))

        pillar_guidance = self._pillar_guidance(pillar, sub_category, available_fields)

        return f"""You are an Elastic demo expert designing live replay scenarios for Elastic Demo Builder.

The goal is to generate scenarios that will trigger Kibana Alerts, Detection Rules, and Cases
when the demo data is streamed live into Elasticsearch. Each scenario should be dramatic enough
to fire alerts but realistic enough to be credible in a customer presentation.

**Customer Context:**
- Company: {company}
- Industry: {industry}
- Pain Points: {json.dumps(pain_points)}
- Pillar: {pillar.upper()} / {sub_category.upper()}

**Available Data Fields:**
{json.dumps(available_fields, indent=2) if available_fields else "(use standard ECS fields for this pillar)"}

{pillar_guidance}

**Return ONLY a valid JSON array of scenario objects:**
```json
[
  {{
    "name": "Normal Operations",
    "description": "Baseline — all services healthy",
    "trigger_after_seconds": 0,
    "duration_seconds": 3600,
    "anomaly_type": "normal",
    "affected_service": "all",
    "severity": "low",
    "field_overrides": {{}},
    "expected_alerts": []
  }},
  {{
    "name": "Checkout Latency Spike",
    "description": "P99 latency on checkout-service jumps to 8s — triggers SLO breach alert",
    "trigger_after_seconds": 30,
    "duration_seconds": 120,
    "anomaly_type": "latency_spike",
    "affected_service": "checkout-service",
    "severity": "high",
    "field_overrides": {{
      "event.duration": 8000000000,
      "transaction.result": "HTTP 5xx",
      "http.response.status_code": 503
    }},
    "expected_alerts": ["P99 Latency > 2s", "SLO Burn Rate Critical", "Error Rate > 5%"]
  }}
]
```

RULES:
- Always include "Normal Operations" as the first scenario (anomaly_type: "normal")
- Generate 3-5 additional anomaly scenarios specific to {company}'s pain points
- trigger_after_seconds: 20-60 (time before anomaly starts after selecting scenario)
- duration_seconds: 60-300 (how long the anomaly lasts)
- field_overrides must use the EXACT field names from the available data fields above
- expected_alerts must be realistic Kibana alert rule names for this use case
- severity: "low" | "medium" | "high" | "critical"
- anomaly_type: one of "normal" | "latency_spike" | "error_surge" | "slo_breach" | "attack" | "db_slowdown" | "cascade_failure"
"""

    def _pillar_guidance(self, pillar: str, sub_category: str, fields: Dict) -> str:
        if pillar == "observability":
            return f"""**Observability Scenario Guidance ({sub_category.upper()}):**
Generate scenarios that demonstrate APM/tracing value:
1. "Normal Operations" — healthy baseline (always first)
2. "Latency Spike" — event.duration spikes 10-50x on one service → triggers P99 alert
3. "Error Storm" — transaction.result → "HTTP 5xx", http.response.status_code → 503/500 → error rate alert
4. "SLO Breach" — sustained errors > error budget → SLO burn rate critical
5. "Database Slowdown" — span.type=="db" queries slow → cascading latency across services
6. (optional) "Cascade Failure" — one service fails, triggers downstream errors

For event.duration overrides: normal ~500000 ns (0.5ms), spike = 5000000000+ ns (5s+)
"""
        elif pillar == "security":
            return f"""**Security Scenario Guidance ({sub_category.upper()}):**
Generate scenarios that trigger Kibana Detection Engine rules:
1. "Normal Operations" — legitimate user activity baseline
2. "Brute Force Login" — event.outcome: "failure" repeated from same source.ip → brute force rule fires
3. "Privilege Escalation" — user.name gets new admin role → privilege escalation alert
4. "Lateral Movement" — process.name spawning unusual children → suspicious process tree
5. "Data Exfiltration" — large network.bytes outbound → data exfil detection rule
6. (optional) "Ransomware Indicator" — file.extension changes + process writes → endpoint alert

For security: field_overrides should target ECS fields: event.outcome, event.action,
user.name, source.ip, process.name, process.parent.name, network.bytes, file.path
"""
        else:
            return f"""**Search Scenario Guidance ({sub_category.upper()}):**
Generate scenarios that show search quality and performance:
1. "Normal Operations" — healthy search baseline
2. "Query Surge" — sudden spike in search requests
3. "Relevance Drop" — search results quality degrades
"""

    # ------------------------------------------------------------------
    # Post-processing
    # ------------------------------------------------------------------

    def _normalise(self, scenarios: List[Dict]) -> List[Dict]:
        """Ensure all required keys are present with correct types."""
        required_keys = {
            "name": "Unnamed Scenario",
            "description": "",
            "trigger_after_seconds": 30,
            "duration_seconds": 120,
            "anomaly_type": "normal",
            "affected_service": "all",
            "severity": "medium",
            "field_overrides": {},
            "expected_alerts": [],
        }
        normalised = []
        for s in scenarios:
            if not isinstance(s, dict):
                continue
            for key, default in required_keys.items():
                s.setdefault(key, default)
            # Type coercions
            s["trigger_after_seconds"] = int(s["trigger_after_seconds"])
            s["duration_seconds"] = int(s["duration_seconds"])
            if not isinstance(s["field_overrides"], dict):
                s["field_overrides"] = {}
            if not isinstance(s["expected_alerts"], list):
                s["expected_alerts"] = []
            normalised.append(s)
        return normalised

    def _fallback_scenarios(self, pillar: str, sub_category: str) -> List[Dict]:
        """Return minimal hardcoded scenarios if LLM fails."""
        scenarios = [dict(NORMAL_SCENARIO)]
        if pillar == "observability":
            scenarios.append({
                "name": "Latency Spike",
                "description": "Service latency spikes — triggers P99 alert",
                "trigger_after_seconds": 30,
                "duration_seconds": 120,
                "anomaly_type": "latency_spike",
                "affected_service": "primary-service",
                "severity": "high",
                "field_overrides": {"event.duration": 5_000_000_000},
                "expected_alerts": ["P99 Latency > 2s"],
            })
            scenarios.append({
                "name": "Error Storm",
                "description": "5xx error surge — triggers error rate alert",
                "trigger_after_seconds": 30,
                "duration_seconds": 120,
                "anomaly_type": "error_surge",
                "affected_service": "primary-service",
                "severity": "critical",
                "field_overrides": {
                    "transaction.result": "HTTP 5xx",
                    "http.response.status_code": 503,
                },
                "expected_alerts": ["Error Rate > 5%"],
            })
        elif pillar == "security":
            scenarios.append({
                "name": "Brute Force Login",
                "description": "Repeated failed logins — triggers brute force detection rule",
                "trigger_after_seconds": 30,
                "duration_seconds": 120,
                "anomaly_type": "attack",
                "affected_service": "auth-service",
                "severity": "high",
                "field_overrides": {
                    "event.outcome": "failure",
                    "event.action": "failed-login",
                },
                "expected_alerts": ["Brute Force Login Detected"],
            })
        return scenarios

    # ------------------------------------------------------------------
    # JSON extraction
    # ------------------------------------------------------------------

    def _extract_json(self, text: str) -> List[Dict]:
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
            result = json.loads(json_text)
            return result if isinstance(result, list) else []
        except json.JSONDecodeError as e:
            import re
            try:
                fixed = re.sub(r",\s*([}\]])", r"\1", json_text)
                result = json.loads(fixed)
                return result if isinstance(result, list) else []
            except json.JSONDecodeError:
                logger.warning(f"Could not parse scenario JSON: {e}")
                return []
