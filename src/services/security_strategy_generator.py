"""
Security Query Strategy Generator
Generates query-first strategy for SIEM, XDR, EDR, Threat Hunting, and Compliance demos.

Key differences from the analytics QueryStrategyGenerator:
- Uses ECS (Elastic Common Schema) field naming — enforced via security_ecs_schema.py
- Generates detection_rules (EQL format) IN ADDITION to ES|QL investigative queries
- Generates timeline_queries (ES|QL) for kill-chain investigation workflows
- Includes MITRE ATT&CK tactic/technique mapping on all queries and rules
- Outputs ILM policy and index pattern recommendations
- NEVER mixes EQL (detection rules) with ES|QL (investigative queries)
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import logging
import uuid

from src.services.security_ecs_schema import (
    get_fields_for_subcategory,
    get_index_patterns,
    get_ilm_policy,
    list_ip_fields,
    get_mitre_tactic,
    get_severity_risk_score,
    MITRE_TACTICS,
    MITRE_TECHNIQUES,
    COMPLIANCE_FRAMEWORKS,
)

logger = logging.getLogger(__name__)

# Dataset sizes for security demos
SECURITY_SIZE_RANGES = {
    "siem":           {"timeseries": "5000-20000",  "reference": "200-1000"},
    "xdr":            {"timeseries": "10000-30000", "reference": "500-2000"},
    "edr":            {"timeseries": "10000-30000", "reference": "200-1000"},
    "threat_hunting": {"timeseries": "20000-50000", "reference": "1000-5000"},
    "compliance":     {"timeseries": "5000-15000",  "reference": "200-500"},
}


class SecurityQueryStrategyGenerator:
    """
    Generates a security-focused query strategy BEFORE data generation.

    Output structure:
    {
        "sub_category": "siem" | "xdr" | "edr" | "threat_hunting" | "compliance",
        "datasets": [ DatasetRequirement... ],
        "queries": [ InvestigativeQuery... ],       # ES|QL — for Kibana Discover / Agent Builder
        "detection_rules": [ DetectionRule... ],   # EQL  — for Kibana Detection Engine
        "timeline_queries": [ TimelineQuery... ],  # ES|QL — for kill-chain investigation
        "text_fields": { dataset: [fields] },
        "index_patterns": [ "logs-*", ... ],
        "ilm_policy": "security_logs" | "security_alerts" | "compliance_audit",
    }
    """

    def __init__(self, llm_client):
        self.llm_client = llm_client

    def generate_strategy(self, context: Dict) -> Dict:
        """Generate complete security strategy from customer context."""
        company = context.get("company_name", "Customer")
        sub_category = context.get("sub_category", "siem")
        logger.info(f"Generating SECURITY/{sub_category.upper()} strategy for {company}")

        esql_skill = self._read_esql_skill()
        security_skill = self._read_security_skill()

        num_queries = 5
        max_retries = 4

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"Retry {attempt}: reducing to {num_queries} queries")

                prompt = self._build_prompt(context, esql_skill, security_skill, num_queries, sub_category)

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
                    f"Security strategy: {len(strategy.get('queries', []))} queries, "
                    f"{len(strategy.get('detection_rules', []))} rules, "
                    f"{len(strategy.get('timeline_queries', []))} timeline steps"
                )
                return strategy

            except ValueError as e:
                if "Invalid JSON" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"JSON parse failed (attempt {attempt + 1}): {e}")
                    num_queries = max(1, num_queries - 2)
                    continue
                raise
            except Exception as e:
                logger.error(f"Security strategy generation failed: {e}", exc_info=True)
                raise

        raise ValueError("Failed to generate valid security strategy after all retries")

    # -------------------------------------------------------------------------
    # Prompt Construction
    # -------------------------------------------------------------------------

    def _build_prompt(
        self,
        context: Dict,
        esql_skill: str,
        security_skill: str,
        num_queries: int,
        sub_category: str,
    ) -> str:
        """Build the LLM prompt tailored to the security sub-category."""

        ecs_fields = get_fields_for_subcategory(sub_category)
        ip_fields = list_ip_fields(sub_category)
        index_patterns = get_index_patterns(sub_category)

        # Build compliance section if relevant
        compliance_section = ""
        frameworks = context.get("compliance_frameworks", [])
        if frameworks:
            controls = []
            for fw in frameworks:
                fw_data = COMPLIANCE_FRAMEWORKS.get(fw, {})
                controls.extend(fw_data.get("key_controls", []))
            compliance_section = f"""
**Compliance Frameworks In Scope:** {', '.join(frameworks)}
Key controls to address:
{chr(10).join(f'  - {c}' for c in controls[:8])}
"""

        # Build MITRE section
        mitre_tactics = context.get("mitre_tactics", [])
        mitre_section = ""
        if mitre_tactics:
            tactic_names = [
                f"{t}: {get_mitre_tactic(t).get('name', '')}"
                for t in mitre_tactics
            ]
            mitre_section = f"""
**MITRE ATT&CK Tactics In Scope:** {', '.join(tactic_names)}
"""

        # Sub-category-specific guidance
        subcategory_guidance = self._get_subcategory_guidance(sub_category)

        # Top ECS fields to highlight in prompt (avoid overwhelming with all 150+)
        key_fields = self._get_key_fields_for_prompt(sub_category, ecs_fields)

        return f"""You are an Elastic Security expert designing a SIEM/Security demo for Elastic Agent Builder.

**Customer Context:**
- Company: {context.get('company_name')}
- Department: {context.get('department')}
- Industry: {context.get('industry')}
- Pain Points: {json.dumps(context.get('pain_points', []))}
- Use Cases: {json.dumps(context.get('use_cases', []))}
- Scale: {context.get('scale', 'Unknown')}
- Key Metrics: {json.dumps(context.get('metrics', []))}
- Data Sources: {json.dumps(context.get('data_sources', ['logs']))}
- Security Sub-Category: {sub_category.upper()}
{compliance_section}{mitre_section}

**Sub-Category Guidance:**
{subcategory_guidance}

**MANDATORY ECS Field Names — Use EXACTLY These (no invented field names):**
{json.dumps(key_fields, indent=2)}

**IP-type fields — MUST be typed as "ip" not "keyword":**
{json.dumps(ip_fields[:10])}

**Recommended Index Patterns:**
{json.dumps(index_patterns)}

**ES|QL Reference:**
{esql_skill}

**Kibana Security Reference:**
{security_skill}

**⚠️ CRITICAL LANGUAGE DISTINCTION:**
- **ES|QL** (FROM ... | WHERE ... | STATS ...): Use for INVESTIGATIVE queries and timeline_queries
- **EQL** (sequence by ... [event] with maxspan=...): Use ONLY for detection_rules language="eql"
- NEVER put EQL syntax inside ES|QL queries or vice versa

**⚠️ ECS FIELD NAMING — MANDATORY:**
- ALWAYS use dot-notation ECS fields: user.name NOT username, source.ip NOT src_ip
- ALWAYS use event.category, event.outcome, event.type (not custom event fields)
- IP address fields MUST be typed "ip" (not "keyword")
- Use wildcard type for process.command_line and registry.path (for LIKE queries)

**⚠️ ES|QL ANTI-PATTERNS — NEVER USE:**
- LAG(), LEAD(), ROW_NUMBER(), RANK(), DENSE_RANK()
- OVER (PARTITION BY ...) window functions
- Referencing other rows or previous values

**✅ SECURITY-SPECIFIC ES|QL PATTERNS TO USE:**
1. Brute force / spike detection:
   ```
   FROM logs-* | WHERE event.category == "authentication" AND event.outcome == "failure"
   | STATS failures = COUNT(), unique_ips = COUNT_DISTINCT(source.ip) BY user.name
   | WHERE failures > 10 | SORT failures DESC
   ```
2. Rare process execution (living-off-the-land):
   ```
   FROM logs-* | WHERE event.category == "process"
   | STATS exec_count = COUNT() BY process.name, host.name
   | INLINESTATS global_avg = AVG(exec_count) BY process.name
   | WHERE exec_count < global_avg * 0.1 | SORT exec_count ASC
   ```
3. Network beaconing detection:
   ```
   FROM logs-* | WHERE event.category == "network"
   | STATS connection_count = COUNT(), bytes_out = SUM(destination.bytes) BY destination.ip, host.name
   | WHERE connection_count > 100 AND bytes_out < 1000 | SORT connection_count DESC
   ```
4. Compliance audit — privileged access review:
   ```
   FROM logs-* | WHERE event.category == "authentication" AND user.roles LIKE "*admin*"
   | STATS login_count = COUNT() BY user.name, host.name, DATE_TRUNC(1 day, @timestamp)
   | SORT login_count DESC
   ```

**Your Task:**
Generate EXACTLY {num_queries} investigative ES|QL queries + 3 detection rules + a 5-step attack timeline.
Each query and rule must map to a MITRE ATT&CK technique.

**Return ONLY valid JSON in this exact structure:**
```json
{{
  "sub_category": "{sub_category}",
  "datasets": [
    {{
      "name": "snake_case_name",
      "type": "timeseries",
      "row_count": "5000-20000",
      "required_fields": {{
        "@timestamp": "date",
        "event.category": "keyword",
        "event.outcome": "keyword",
        "user.name": "keyword",
        "host.name": "keyword",
        "source.ip": "ip"
      }},
      "relationships": [],
      "semantic_fields": []
    }}
  ],
  "queries": [
    {{
      "name": "Descriptive Query Name",
      "pain_point": "Which customer pain point this addresses",
      "esql_features": ["STATS", "WHERE"],
      "required_datasets": ["dataset_name"],
      "required_fields": {{"dataset_name": ["field1", "field2"]}},
      "description": "What insight this delivers",
      "complexity": "medium",
      "mitre_technique_id": "T1110",
      "mitre_technique_name": "Brute Force",
      "severity": "high"
    }}
  ],
  "detection_rules": [
    {{
      "rule_id": "unique-rule-id-001",
      "name": "Rule Name",
      "description": "What threat this detects",
      "language": "eql",
      "query": "sequence by user.name [authentication where event.outcome == \\"failure\\"] with maxspan=5m",
      "severity": "high",
      "risk_score": 73,
      "mitre_tactic_id": "TA0006",
      "mitre_tactic_name": "Credential Access",
      "mitre_technique_id": "T1110",
      "mitre_technique_name": "Brute Force",
      "index_patterns": ["logs-*"],
      "tags": ["brute-force"],
      "interval": "5m",
      "from": "now-6m"
    }}
  ],
  "timeline_queries": [
    {{
      "step": 1,
      "phase": "MITRE Tactic Name",
      "name": "Investigation Step Name",
      "description": "What this step investigates",
      "esql": "FROM logs-* | WHERE event.category == \\"authentication\\" | LIMIT 20",
      "expected_finding": "What a positive finding looks like",
      "mitre_technique_id": "T1110"
    }}
  ],
  "text_fields": {{}},
  "index_patterns": {json.dumps(index_patterns)},
  "ilm_policy": "security_logs"
}}
```

IMPORTANT:
- All dataset field names MUST use ECS dot-notation
- IP fields (*.ip) MUST have type "ip"
- detection_rules language MUST be "eql" or "esql" (not "kuery")
- timeline_queries MUST use ES|QL (FROM ... syntax), NOT EQL
- timeline_queries must be sequential steps 1, 2, 3, 4, 5
- severity must be one of: low, medium, high, critical
"""

    def _get_subcategory_guidance(self, sub_category: str) -> str:
        """Return sub-category-specific generation guidance."""
        guidance = {
            "siem": """Focus on: log aggregation, authentication events, network traffic analysis.
- Windows Event Log IDs: 4624 (logon), 4625 (failed logon), 4688 (process create), 4698 (scheduled task)
- Linux: /var/log/auth.log, syslog, auditd
- Key threat scenarios: brute force, account compromise, lateral movement via auth logs""",

            "xdr": """Focus on: cross-domain correlation — endpoint + network + cloud alerts.
- Correlate endpoint process events with outbound network connections
- Link file creation events to process ancestry
- Identify cloud resource access from compromised endpoints
- Key threat scenarios: supply chain attacks, cloud lateral movement, data exfiltration""",

            "edr": """Focus on: endpoint telemetry — process trees, file events, registry modifications.
- Generate parent-child process relationships (ppid → pid chains)
- Include process.hash.sha256 for malware detection
- Registry persistence locations: HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
- Key threat scenarios: malware persistence, credential dumping (LSASS), defense evasion""",

            "threat_hunting": """Focus on: proactive detection of low-and-slow attacks and living-off-the-land binaries (LOLBins).
- Use INLINESTATS for statistical baselining (rare processes, unusual connection counts)
- LOLBins to hunt: powershell.exe, wscript.exe, mshta.exe, regsvr32.exe, certutil.exe
- Key scenarios: domain admin abuse, scheduled task persistence, DNS tunneling""",

            "compliance": """Focus on: audit trail completeness, access reviews, and control evidence collection.
- Map each query to a specific compliance control ID
- Include privileged access monitoring, data access audit, configuration change tracking
- Generate queries that produce compliance evidence reports (not just security alerts)""",
        }
        return guidance.get(sub_category, guidance["siem"])

    def _get_key_fields_for_prompt(self, sub_category: str, all_fields: Dict) -> Dict[str, str]:
        """Return the most important fields to highlight in the prompt (max 30)."""
        priority_fields = {
            "siem": ["@timestamp", "event.category", "event.type", "event.outcome",
                     "user.name", "user.domain", "host.name", "host.os.type",
                     "source.ip", "destination.ip", "network.protocol",
                     "process.name", "message", "threat.tactic.name", "threat.technique.id"],
            "xdr": ["@timestamp", "event.category", "event.outcome",
                    "process.name", "process.executable", "process.pid", "process.parent.pid",
                    "file.path", "file.hash.sha256", "source.ip", "destination.ip",
                    "cloud.provider", "cloud.account.id", "threat.technique.id"],
            "edr": ["@timestamp", "event.category", "event.type",
                    "process.name", "process.executable", "process.command_line",
                    "process.pid", "process.parent.pid", "process.hash.sha256",
                    "file.path", "file.name", "registry.key", "registry.path",
                    "host.name", "host.os.type", "user.name"],
            "threat_hunting": ["@timestamp", "event.category",
                               "process.name", "process.command_line", "process.parent.name",
                               "dns.question.name", "network.protocol", "destination.ip",
                               "source.ip", "user.name", "host.name", "threat.technique.id"],
            "compliance": ["@timestamp", "event.category", "event.outcome",
                           "user.name", "user.roles", "host.name", "source.ip",
                           "file.path", "cloud.account.id", "cloud.service.name",
                           "message", "event.action"],
        }
        keys = priority_fields.get(sub_category, priority_fields["siem"])
        return {k: all_fields[k] for k in keys if k in all_fields}

    # -------------------------------------------------------------------------
    # Post-processing: enforce ECS, add missing fields, set defaults
    # -------------------------------------------------------------------------

    def _enrich_and_validate(self, strategy: Dict, sub_category: str) -> Dict:
        """Enforce ECS field types, set defaults, add index patterns and ILM policy."""

        strategy.setdefault("sub_category", sub_category)
        strategy.setdefault("detection_rules", [])
        strategy.setdefault("timeline_queries", [])
        strategy.setdefault("text_fields", {})
        strategy.setdefault("index_patterns", get_index_patterns(sub_category))
        strategy.setdefault("ilm_policy", "security_logs")

        # Enforce IP field types on all datasets
        for dataset in strategy.get("datasets", []):
            fields = dataset.get("required_fields", {})
            for field_name in list(fields.keys()):
                if field_name.endswith(".ip") or field_name in (
                    "source.ip", "destination.ip", "host.ip",
                    "threat.indicator.ip", "related.ip"
                ):
                    fields[field_name] = "ip"

        # Ensure detection rules have stable rule_ids
        for rule in strategy.get("detection_rules", []):
            if not rule.get("rule_id") or rule["rule_id"] == "unique-rule-id-001":
                rule["rule_id"] = str(uuid.uuid4())
            # Default risk score from severity if missing
            if "risk_score" not in rule and "severity" in rule:
                rule["risk_score"] = get_severity_risk_score(rule["severity"])

        # Ensure timeline queries are numbered sequentially from 1
        for i, query in enumerate(strategy.get("timeline_queries", [])):
            query["step"] = i + 1

        return strategy

    # -------------------------------------------------------------------------
    # Skill / JSON helpers (same pattern as QueryStrategyGenerator)
    # -------------------------------------------------------------------------

    def _read_esql_skill(self) -> str:
        """Read ES|QL skill documentation."""
        try:
            # Try installed agent-skills location
            for path in [
                Path(".agents/skills/elasticsearch-esql/SKILL.md"),
                Path(".claude/skills/elasticsearch-esql/SKILL.md"),
            ]:
                if path.exists():
                    return path.read_text()[:3000]  # cap to avoid token overflow
        except Exception as e:
            logger.warning(f"Could not read ES|QL skill: {e}")

        return """ES|QL Key Features:
- FROM <index>: Select source index
- WHERE: Filter rows (use ECS field names)
- STATS ... BY: Aggregate and group
- INLINESTATS: Aggregate while keeping all rows (anomaly detection)
- EVAL: Compute new fields
- DATE_TRUNC: Bucket timestamps
- SORT / LIMIT: Order and paginate results
- LOOKUP JOIN: Enrich with reference data (lookup index mode required)
- COUNT_DISTINCT: Count unique values
- LIKE / RLIKE: Pattern matching (no parameters!)
"""

    def _read_security_skill(self) -> str:
        """Read Kibana security skill documentation."""
        try:
            for path in [
                Path(".agents/skills/security-alert-triage/SKILL.md"),
                Path(".claude/skills/security-alert-triage/SKILL.md"),
                Path(".agents/skills/security-detection-rule-management/SKILL.md"),
            ]:
                if path.exists():
                    return path.read_text()[:2000]
        except Exception as e:
            logger.warning(f"Could not read security skill: {e}")

        return """Kibana Security Detection Engine:
- Detection rules use EQL (Event Query Language) for sequence detection
- EQL sequences: sequence by <field> [event condition] with maxspan=<time>
- Alert fields: kibana.alert.severity, kibana.alert.risk_score (0-100)
- Severity levels: low (21), medium (47), high (73), critical (99)
- MITRE ATT&CK fields: threat.tactic.id, threat.technique.id
"""

    def _is_likely_truncated(self, text: str) -> bool:
        """Check if LLM response appears truncated."""
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
        """Extract and parse JSON from LLM response."""
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
                # Remove trailing commas before } or ]
                import re
                fixed = re.sub(r",\s*([}\]])", r"\1", json_text)
                return json.loads(fixed)
            except json.JSONDecodeError as e2:
                raise ValueError(f"Invalid JSON in security strategy response: {e2}")
