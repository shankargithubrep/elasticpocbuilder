"""
Detection Rules Tab — Security Pillar

Displays Kibana Detection Engine rules generated for Security demos:
- EQL/ES|QL rule definitions with MITRE ATT&CK badges
- Severity and risk score indicators
- Export rules as Kibana-importable JSON (ndjson format)
- Attack timeline (kill-chain investigation queries)
"""

import streamlit as st
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Severity colour map (Kibana conventions)
SEVERITY_COLORS = {
    "critical": "🔴",
    "high":     "🟠",
    "medium":   "🟡",
    "low":      "🔵",
}


def _load_security_strategy(module_name: str) -> dict:
    """Load query_strategy.json for a demo module."""
    path = Path("demos") / module_name / "query_strategy.json"
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception as e:
            logger.warning(f"Could not load query_strategy.json: {e}")
    return {}


def _format_rule_ndjson(rules: list) -> str:
    """Format detection rules as Kibana ndjson import format."""
    lines = []
    for rule in rules:
        kibana_rule = {
            "id": rule.get("rule_id", ""),
            "name": rule.get("name", ""),
            "description": rule.get("description", ""),
            "risk_score": rule.get("risk_score", 47),
            "severity": rule.get("severity", "medium"),
            "type": "eql" if rule.get("language") == "eql" else "esql",
            "language": rule.get("language", "eql"),
            "query": rule.get("query", ""),
            "index": rule.get("index_patterns", ["logs-*"]),
            "interval": rule.get("interval", "5m"),
            "from": rule.get("from", "now-6m"),
            "enabled": False,
            "tags": rule.get("tags", []),
            "threat": [
                {
                    "framework": "MITRE ATT&CK",
                    "tactic": {
                        "id": rule.get("mitre_tactic_id", ""),
                        "name": rule.get("mitre_tactic_name", ""),
                        "reference": f"https://attack.mitre.org/tactics/{rule.get('mitre_tactic_id', '')}/"
                    },
                    "technique": [
                        {
                            "id": rule.get("mitre_technique_id", ""),
                            "name": rule.get("mitre_technique_name", ""),
                            "reference": f"https://attack.mitre.org/techniques/{rule.get('mitre_technique_id', '')}/"
                        }
                    ]
                }
            ] if rule.get("mitre_tactic_id") else [],
        }
        lines.append(json.dumps(kibana_rule))
    return "\n".join(lines)


def render_detection_rules_tab(loader):
    """Render the Detection Rules tab for Security demos."""

    strategy = _load_security_strategy(st.session_state.current_demo_module)
    detection_rules = strategy.get("detection_rules", [])
    timeline_queries = strategy.get("timeline_queries", [])
    sub_category = strategy.get("sub_category", loader.config.get("sub_category", "siem"))

    if not detection_rules and not timeline_queries:
        st.info(
            "No detection rules found for this demo. "
            "This tab is available for Security pillar demos (SIEM, XDR, EDR, Threat Hunting, Compliance). "
            "Generate a Security demo to see detection rules here."
        )
        return

    st.info(
        f"🛡️ **Security Demo** — {sub_category.upper()} · "
        f"{len(detection_rules)} detection rules · {len(timeline_queries)} investigation steps. "
        "Rules are ready to export and import into Kibana's Detection Engine."
    )

    # Sub-tabs: Rules | Timeline
    sub_tabs = st.tabs([
        f"🔴 Detection Rules ({len(detection_rules)})",
        f"🔍 Attack Timeline ({len(timeline_queries)} steps)",
    ])

    # -------------------------------------------------------------------------
    # TAB 1: Detection Rules
    # -------------------------------------------------------------------------
    with sub_tabs[0]:
        if not detection_rules:
            st.info("No detection rules were generated for this demo.")
        else:
            # Export all button
            ndjson_content = _format_rule_ndjson(detection_rules)
            st.download_button(
                label="📥 Export All Rules (Kibana ndjson)",
                data=ndjson_content,
                file_name=f"{st.session_state.current_demo_module}_detection_rules.ndjson",
                mime="application/x-ndjson",
                use_container_width=True,
                type="primary",
                help="Download rules in Kibana Detection Engine import format. "
                     "In Kibana: Security > Rules > Import rules"
            )

            st.caption(
                "**How to import:** Kibana → Security → Rules → Import rules → upload the .ndjson file. "
                "Rules are imported as **disabled** — review and enable each one."
            )
            st.divider()

            # Render each rule
            for i, rule in enumerate(detection_rules, 1):
                severity = rule.get("severity", "medium")
                sev_emoji = SEVERITY_COLORS.get(severity, "⚪")
                risk_score = rule.get("risk_score", 47)
                mitre_tactic = rule.get("mitre_tactic_name", "")
                mitre_technique_id = rule.get("mitre_technique_id", "")
                mitre_technique_name = rule.get("mitre_technique_name", "")
                language = rule.get("language", "eql").upper()

                with st.expander(
                    f"{sev_emoji} [{i}] {rule.get('name', 'Unnamed Rule')} "
                    f"· {severity.upper()} · Risk {risk_score}",
                    expanded=(i == 1),
                ):
                    # MITRE badge row
                    badge_cols = st.columns([2, 2, 2, 1])
                    with badge_cols[0]:
                        if mitre_tactic:
                            st.markdown(
                                f"<span style='background:#1f4e79;color:white;padding:2px 8px;"
                                f"border-radius:4px;font-size:0.75rem'>🎯 {mitre_tactic}</span>",
                                unsafe_allow_html=True
                            )
                    with badge_cols[1]:
                        if mitre_technique_id:
                            st.markdown(
                                f"<span style='background:#2e5090;color:white;padding:2px 8px;"
                                f"border-radius:4px;font-size:0.75rem'>"
                                f"{mitre_technique_id} · {mitre_technique_name}</span>",
                                unsafe_allow_html=True
                            )
                    with badge_cols[2]:
                        st.markdown(
                            f"<span style='background:#555;color:white;padding:2px 8px;"
                            f"border-radius:4px;font-size:0.75rem'>Language: {language}</span>",
                            unsafe_allow_html=True
                        )
                    with badge_cols[3]:
                        st.metric("Risk", risk_score, label_visibility="visible")

                    st.markdown(f"**Description:** {rule.get('description', '')}")

                    # Index patterns
                    index_patterns = rule.get("index_patterns", [])
                    if index_patterns:
                        st.caption(f"**Index patterns:** `{'`, `'.join(index_patterns)}`")

                    # Schedule
                    interval = rule.get("interval", "5m")
                    lookback = rule.get("from", "now-6m")
                    st.caption(f"**Schedule:** Every `{interval}` · Lookback `{lookback}`")

                    st.markdown("**Query:**")

                    if language == "EQL":
                        st.code(rule.get("query", ""), language="sql")
                        st.caption(
                            "⚠️ **EQL** (Event Query Language) — this is NOT ES|QL. "
                            "EQL sequence syntax is used by Kibana's Detection Engine for correlation rules."
                        )
                    else:
                        st.code(rule.get("query", ""), language="sql")

                    # Tags
                    tags = rule.get("tags", [])
                    if tags:
                        st.caption(f"**Tags:** {', '.join(tags)}")

                    # Single rule export
                    single_ndjson = _format_rule_ndjson([rule])
                    st.download_button(
                        "📥 Export this rule",
                        data=single_ndjson,
                        file_name=f"{rule.get('rule_id', f'rule_{i}')}.ndjson",
                        mime="application/x-ndjson",
                        key=f"export_rule_{i}_{st.session_state.current_demo_module}",
                        use_container_width=True,
                    )

    # -------------------------------------------------------------------------
    # TAB 2: Attack Timeline
    # -------------------------------------------------------------------------
    with sub_tabs[1]:
        if not timeline_queries:
            st.info("No attack timeline was generated for this demo.")
        else:
            st.markdown(
                "The attack timeline shows a step-by-step investigation path through the kill chain. "
                "Run each ES|QL query in Kibana Discover to trace an attack in sequence."
            )

            # Download all timeline queries as JSON
            timeline_json = json.dumps(timeline_queries, indent=2)
            st.download_button(
                "📥 Download Timeline Queries (JSON)",
                data=timeline_json,
                file_name=f"{st.session_state.current_demo_module}_timeline.json",
                mime="application/json",
                use_container_width=True,
            )
            st.divider()

            for step in timeline_queries:
                step_num = step.get("step", "?")
                phase = step.get("phase", "")
                name = step.get("name", f"Step {step_num}")
                description = step.get("description", "")
                esql = step.get("esql", "")
                expected = step.get("expected_finding", "")
                mitre_id = step.get("mitre_technique_id", "")

                # Connecting line between steps (not for first step)
                if step_num != 1 and step_num != "?":
                    st.markdown(
                        "<div style='text-align:center;color:#888;margin:-8px 0'>▼</div>",
                        unsafe_allow_html=True
                    )

                with st.container(border=True):
                    header_cols = st.columns([1, 6, 2])
                    with header_cols[0]:
                        st.markdown(
                            f"<div style='background:#1f4e79;color:white;border-radius:50%;"
                            f"width:32px;height:32px;display:flex;align-items:center;"
                            f"justify-content:center;font-weight:bold'>{step_num}</div>",
                            unsafe_allow_html=True
                        )
                    with header_cols[1]:
                        st.markdown(f"**{name}**")
                        if phase:
                            st.caption(f"Phase: {phase}")
                    with header_cols[2]:
                        if mitre_id:
                            st.markdown(
                                f"<span style='background:#2e5090;color:white;padding:2px 6px;"
                                f"border-radius:4px;font-size:0.7rem'>{mitre_id}</span>",
                                unsafe_allow_html=True
                            )

                    if description:
                        st.markdown(description)

                    if esql:
                        st.code(esql, language="sql")

                    if expected:
                        st.success(f"**Expected finding:** {expected}")

                    # Run in ES button (opens Discover)
                    kibana_url = _get_kibana_url()
                    if kibana_url:
                        discover_url = f"{kibana_url}/app/discover"
                        st.link_button(
                            "▶ Open Kibana Discover",
                            url=discover_url,
                            help="Opens Kibana Discover — paste the query above to run it",
                        )


def _get_kibana_url() -> str:
    """Return Kibana URL from environment if configured."""
    import os
    url = os.getenv("ELASTICSEARCH_KIBANA_URL", "")
    # Strip trailing slash
    return url.rstrip("/") if url else ""
