"""
AI Endpoint Security Tab

Six detection capabilities for monitoring AI cowork tools (Claude Code,
Cursor, Copilot, etc.) across an enterprise endpoint fleet.

Sub-panels:
  🖥️  AI Process Inventory    — fleet-wide tool/user/MCP view
  🔥  Data Exposure Heatmap   — sensitive files touched by AI processes
  ⚡  Kill Chain Simulator    — scripted live attack scenario
  💉  Injection Indicators    — shells spawned by AI parent processes
  👁️  Shadow AI Discovery     — AI traffic from unregistered hosts
  🔌  MCP Connection Registry — all MCP servers, allowlist status
"""

import time
import logging
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------

_SEVERITY_COLOR = {
    "critical": "#B22222",
    "high":     "#D4730A",
    "medium":   "#D4A010",
    "low":      "#1A7A4A",
    "info":     "#1E6F9F",
}
_RISK_COLOR = {"high": "#B22222", "medium": "#D4730A", "low": "#1A7A4A"}


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

def render_ai_endpoint_security_tab(loader=None):
    st.markdown("## 🤖 AI Endpoint Security")
    st.caption(
        "Monitor AI cowork tools (Claude Code, Cursor, Copilot) across your endpoint fleet. "
        "Detect data exfiltration, prompt injection, shadow AI, and unapproved MCP servers — "
        "all from a single Elastic Agent telemetry stream."
    )

    # Load / cache data
    @st.cache_data(ttl=300, show_spinner=False)
    def _load():
        from src.services.ai_endpoint_security_service import (
            AiEndpointSecurityService, compute_fleet_summary
        )
        svc = AiEndpointSecurityService()
        datasets = svc.generate_all()
        summary = compute_fleet_summary(datasets)
        return datasets, summary

    with st.spinner("Loading AI endpoint telemetry..."):
        datasets, summary = _load()

    _render_fleet_header(summary)
    st.divider()

    panels = [
        "🖥️ AI Process Inventory",
        "🔥 Data Exposure Heatmap",
        "⚡ Kill Chain Simulator",
        "💉 Injection Indicators",
        "👁️ Shadow AI Discovery",
        "🔌 MCP Connection Registry",
    ]
    selected = st.segmented_control(
        "panel", panels, default=panels[0],
        key="ai_sec_panel", label_visibility="collapsed"
    )

    st.markdown("")

    if selected == panels[0]:
        _render_process_inventory(datasets["ai_process_inventory"])
    elif selected == panels[1]:
        _render_exposure_heatmap(datasets["ai_file_access_events"])
    elif selected == panels[2]:
        _render_kill_chain()
    elif selected == panels[3]:
        _render_injection_indicators(datasets["ai_shell_executions"])
    elif selected == panels[4]:
        _render_shadow_ai(datasets["ai_shadow_discovery"])
    elif selected == panels[5]:
        _render_mcp_registry(datasets["ai_mcp_connections"])


# ---------------------------------------------------------------------------
# Fleet header — 6 KPI tiles
# ---------------------------------------------------------------------------

def _render_fleet_header(s: dict):
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("AI Processes",    s["total_ai_processes"])
    c2.metric("Hosts Covered",   s["unique_hosts"])
    c3.metric("Users Monitored", s["unique_users"])
    c4.metric("🔴 High-Risk Flows",   s["high_risk_flows"],   delta="needs review", delta_color="inverse")
    c5.metric("👻 Shadow AI Hosts",   s["shadow_hosts"],       delta="no agent", delta_color="inverse")
    c6.metric("⚠️ Suspicious Shells", s["suspicious_shells"],  delta="investigate", delta_color="inverse")


# ---------------------------------------------------------------------------
# Panel 1 — AI Process Inventory
# ---------------------------------------------------------------------------

def _render_process_inventory(df: pd.DataFrame):
    st.markdown("### 🖥️ AI Process Inventory")
    st.caption(
        "Every AI cowork tool running across your fleet right now — tool, version, user, "
        "MCP servers connected. Most security teams have no answer to this question today."
    )

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        tools = ["All"] + sorted(df["process.name"].unique().tolist())
        sel_tool = st.selectbox("Filter by tool", tools, key="inv_tool")
    with col_f2:
        depts = ["All"] + sorted(df["user.department"].unique().tolist())
        sel_dept = st.selectbox("Filter by department", depts, key="inv_dept")
    with col_f3:
        show_unknown_mcp = st.toggle("⚠️ Unknown MCP only", key="inv_unknown_mcp")

    filtered = df.copy()
    if sel_tool != "All":
        filtered = filtered[filtered["process.name"] == sel_tool]
    if sel_dept != "All":
        filtered = filtered[filtered["user.department"] == sel_dept]
    if show_unknown_mcp:
        filtered = filtered[filtered["mcp.has_unknown"] == True]

    # Summary tiles
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Processes shown",     len(filtered))
    c2.metric("Unique tools",        filtered["process.name"].nunique())
    c3.metric("With unknown MCP",    int(filtered["mcp.has_unknown"].sum()))
    c4.metric("Unapproved tools",    int((~filtered["approved"]).sum()))

    # Tool breakdown
    st.markdown("**Tool distribution across fleet**")
    tool_counts = filtered.groupby("process.name").size().reset_index(name="count").sort_values("count", ascending=False)
    for _, row in tool_counts.iterrows():
        pct = row["count"] / len(filtered) * 100
        approved = row["process.name"] in ["claude-code", "github-copilot", "cursor"]
        badge = "✅" if approved else "⚠️ UNAPPROVED"
        st.markdown(
            f"**{row['process.name']}** {badge} — {row['count']} instances ({pct:.0f}%)"
        )
        st.progress(pct / 100)

    st.markdown("**Full inventory**")
    display_cols = ["host.name", "user.name", "user.department", "process.name",
                    "process.version", "mcp.servers_count", "mcp.has_unknown",
                    "network.connections", "approved"]
    st.dataframe(
        filtered[display_cols].rename(columns={
            "host.name": "Host", "user.name": "User", "user.department": "Dept",
            "process.name": "Tool", "process.version": "Version",
            "mcp.servers_count": "MCP#", "mcp.has_unknown": "Unknown MCP?",
            "network.connections": "Net Conns", "approved": "Approved",
        }),
        use_container_width=True, height=400,
    )


# ---------------------------------------------------------------------------
# Panel 2 — Data Exposure Heatmap
# ---------------------------------------------------------------------------

def _render_exposure_heatmap(df: pd.DataFrame):
    st.markdown("### 🔥 Data Exposure Heatmap")
    st.caption(
        "Sensitive files touched by AI processes — by user, tool, and time of day. "
        "Not alerts. Standing exposure. The conversation shifts from "
        "\"did something bad happen\" to \"here is your risk right now.\""
    )

    # Exposure by category
    st.markdown("**Exposure by file category and sensitivity**")
    cat_summary = (
        df.groupby("file.category")
        .agg(touches=("file.path", "count"), avg_sensitivity=("file.sensitivity", "mean"))
        .reset_index()
        .sort_values("avg_sensitivity", ascending=False)
    )
    for _, row in cat_summary.iterrows():
        sens = row["avg_sensitivity"]
        color = "#B22222" if sens >= 8 else "#D4730A" if sens >= 6 else "#1A7A4A"
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:12px;margin:4px 0'>"
            f"<span style='background:{color};color:white;padding:2px 8px;border-radius:4px;"
            f"font-size:0.8em;min-width:80px;text-align:center'>{row['file.category']}</span>"
            f"<span>{row['touches']} touches</span>"
            f"<span style='color:{color};font-weight:bold'>sensitivity {sens:.1f}/10</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("")

    # Top exposed users
    st.markdown("**Users with highest credential/secrets exposure**")
    high_risk = df[df["file.sensitivity"] >= 8]
    user_exposure = (
        high_risk.groupby(["user.name", "process.name"])
        .agg(high_risk_touches=("file.path", "count"))
        .reset_index()
        .sort_values("high_risk_touches", ascending=False)
        .head(10)
    )
    for _, row in user_exposure.iterrows():
        st.markdown(
            f"🔴 **{row['user.name']}** via `{row['process.name']}` — "
            f"**{row['high_risk_touches']}** high-sensitivity file touches"
        )

    # Hour of day heatmap
    st.markdown("**Access pattern by hour (all sensitivity levels)**")
    hour_data = df.groupby("event.hour").agg(count=("file.path", "count")).reset_index()
    st.bar_chart(hour_data.set_index("event.hour")["count"], height=180)

    st.markdown("**Raw exposure events (credentials & secrets only)**")
    cred_df = df[df["file.category"].isin(["credentials", "secrets"])].copy()
    st.dataframe(
        cred_df[["@timestamp", "user.name", "process.name", "file.path",
                 "file.category", "file.sensitivity", "event.action"]]
        .sort_values("file.sensitivity", ascending=False)
        .head(50),
        use_container_width=True, height=350,
    )


# ---------------------------------------------------------------------------
# Panel 3 — Kill Chain Simulator
# ---------------------------------------------------------------------------

def _render_kill_chain():
    from src.services.ai_endpoint_security_service import get_kill_chain_events

    st.markdown("### ⚡ Kill Chain Simulator")
    st.caption(
        "Scripted live scenario: a prompt injection causes Claude Code to read AWS credentials "
        "and beacon them to a C2 server. Watch Elastic detect, alert, and respond — "
        "in under 12 seconds of wall-clock time."
    )

    st.markdown(
        "<div style='background:#fff3cd;border:1px solid #ffc107;border-radius:6px;"
        "padding:10px 16px;margin-bottom:12px;font-size:0.9em'>"
        "🎬 <strong>Demo tip:</strong> Run this live in front of the customer. "
        "Each event appears with a real time delay. The moment the alert fires at t+5s "
        "is the emotional core of Phase 5 — pause there and ask "
        "<em>\"Does your current SIEM have a rule for this?\"</em>"
        "</div>",
        unsafe_allow_html=True,
    )

    events = get_kill_chain_events()

    if st.button("▶️ Run Kill Chain Simulation", type="primary", key="kc_run"):
        placeholder = st.empty()
        shown = []

        for ev in events:
            time.sleep(ev["t_offset_sec"] if ev["t_offset_sec"] == 0 else 1.5)
            shown.append(ev)
            with placeholder.container():
                for e in shown:
                    color = _SEVERITY_COLOR.get(e["severity"], "#555")
                    st.markdown(
                        f"<div style='border-left:4px solid {color};padding:8px 14px;"
                        f"margin:6px 0;border-radius:0 6px 6px 0;background:#fafafa'>"
                        f"<span style='font-size:1.2em'>{e['icon']}</span> "
                        f"<strong style='color:{color}'>t+{e['t_offset_sec']}s — {e['phase']}</strong><br>"
                        f"<span style='font-size:0.95em'>{e['event']}</span><br>"
                        f"<code style='font-size:0.78em;color:#555'>{e['detail']}</code><br>"
                        f"<span style='font-size:0.75em;color:#888'>{e['mitre']}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
        st.success("✅ Simulation complete — 6 events, 1 alert, 3 automated responses, 11 seconds.")
    else:
        # Show static preview
        for ev in events:
            color = _SEVERITY_COLOR.get(ev["severity"], "#555")
            st.markdown(
                f"<div style='border-left:3px solid {color};padding:6px 12px;"
                f"margin:4px 0;border-radius:0 4px 4px 0;opacity:0.7'>"
                f"{ev['icon']} <strong>t+{ev['t_offset_sec']}s</strong> — "
                f"{ev['phase']}: {ev['event']}"
                f"</div>",
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Panel 4 — Injection Indicators
# ---------------------------------------------------------------------------

def _render_injection_indicators(df: pd.DataFrame):
    st.markdown("### 💉 Injection Indicators")
    st.caption(
        "Shell commands spawned by AI parent processes. Unusual commands after AI ingests "
        "external content indicate prompt injection. Hardest to catch — most novel capability."
    )

    suspicious = df[df["process.is_suspicious"] == True].copy()
    benign = df[df["process.is_suspicious"] == False].copy()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total shell executions",  len(df))
    c2.metric("🔴 Suspicious",           len(suspicious))
    c3.metric("✅ Benign",               len(benign))

    if not suspicious.empty:
        st.markdown("**⚠️ Suspicious shell executions by injection pattern**")
        pattern_counts = suspicious.groupby("threat.injection_pattern").size().reset_index(name="count")
        for _, row in pattern_counts.iterrows():
            pct = row["count"] / len(suspicious) * 100
            st.markdown(f"**{row['threat.injection_pattern']}** — {row['count']} events ({pct:.0f}%)")
            st.progress(pct / 100)

        st.markdown("**Suspicious executions — full detail**")
        st.dataframe(
            suspicious[["@timestamp", "host.name", "user.name", "process.parent.name",
                         "process.name", "process.args", "threat.injection_pattern",
                         "event.risk_score"]]
            .sort_values("event.risk_score", ascending=False),
            use_container_width=True, height=350,
        )

        st.markdown("**Detection ES|QL — run this in Discover**")
        st.code("""FROM logs-endpoint.process*
| WHERE process.parent.name IN ("claude-code","cursor","github-copilot","continue")
  AND process.name IN ("bash","zsh","sh","curl","wget","python3","nc","osascript")
| EVAL is_suspicious = CASE(
    process.args LIKE "*base64*" OR
    process.args LIKE "*curl*http*" OR
    process.args LIKE "*wget*"    OR
    process.args LIKE "*chmod +x*", true, false
  )
| WHERE is_suspicious == true
| STATS events = COUNT(*), users = COUNT_DISTINCT(user.name)
    BY process.parent.name, process.name
| SORT events DESC
| LIMIT 20""", language="sql")


# ---------------------------------------------------------------------------
# Panel 5 — Shadow AI Discovery
# ---------------------------------------------------------------------------

def _render_shadow_ai(df: pd.DataFrame):
    st.markdown("### 👁️ Shadow AI Discovery")
    st.caption(
        "Hosts generating traffic to known AI vendor IPs with no registered Elastic Agent. "
        "IT has zero visibility — the threat exists but cannot be seen, let alone measured. "
        "This is the CISO-level blind spot metric."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Shadow hosts detected",   df["host.name"].nunique())
    c2.metric("Unique shadow tools",     df["shadow.tool_identified"].nunique())
    c3.metric("Total shadow egress",     f"{df['network.bytes'].sum() / 1_000_000:.1f} MB")

    st.markdown("**Shadow tools by reason**")
    reason_counts = df.groupby(["shadow.tool_identified", "shadow.reason"]).agg(
        hosts=("host.name", "nunique"),
        total_mb=("network.bytes", lambda x: round(x.sum() / 1_000_000, 1)),
    ).reset_index().sort_values("hosts", ascending=False)

    for _, row in reason_counts.iterrows():
        reason_color = {"personal_account": "#B22222", "unapproved_tool": "#D4730A", "local_llm": "#6B21A8"}.get(row["shadow.reason"], "#555")
        st.markdown(
            f"<div style='border-left:4px solid {reason_color};padding:5px 12px;margin:4px 0;border-radius:0 4px 4px 0'>"
            f"<strong>{row['shadow.tool_identified']}</strong> — "
            f"<span style='color:{reason_color}'>{row['shadow.reason']}</span> — "
            f"{row['hosts']} hosts, {row['total_mb']} MB egress"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("**Shadow AI events**")
    st.dataframe(
        df[["@timestamp", "host.name", "user.name", "user.department",
            "destination.domain", "shadow.tool_identified", "shadow.reason",
            "network.bytes", "event.risk_score"]]
        .sort_values("event.risk_score", ascending=False),
        use_container_width=True, height=350,
    )

    st.markdown("**Shadow AI detection ES|QL**")
    st.code("""FROM logs-endpoint.network*
| WHERE destination.domain IN (
    "api.anthropic.com","api.openai.com","api2.cursor.sh",
    "ollama.ai","lmstudio.ai","api.cohere.ai"
  )
| LOOKUP JOIN asset_inventory ON host.name
| WHERE asset.elastic_agent_registered == false
| STATS
    shadow_hosts = COUNT_DISTINCT(host.name),
    total_mb     = SUM(network.bytes) / 1000000,
    users        = COUNT_DISTINCT(user.name)
  BY destination.domain
| SORT shadow_hosts DESC
| LIMIT 20""", language="sql")


# ---------------------------------------------------------------------------
# Panel 6 — MCP Connection Registry
# ---------------------------------------------------------------------------

def _render_mcp_registry(df: pd.DataFrame):
    st.markdown("### 🔌 MCP Connection Registry")
    st.caption(
        "Every MCP server connected across your fleet — allowlist status, connection frequency, "
        "first seen date. Right now no enterprise has this view anywhere. "
        "A new MCP server = instant flag."
    )

    allowlisted = df[df["mcp.allowlisted"] == True]
    unknown     = df[df["mcp.allowlisted"] == False]
    new_servers = df[df["mcp.is_new"] == True]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total MCP connections",  len(df))
    c2.metric("✅ Allowlisted",         len(allowlisted))
    c3.metric("⚠️ Unknown servers",     len(unknown))
    c4.metric("🆕 New (last 3 days)",   len(new_servers))

    if not unknown.empty:
        st.markdown("**⚠️ Unknown MCP servers — requires review**")
        unknown_summary = (
            unknown.groupby("mcp.server")
            .agg(
                hosts=("host.name", "nunique"),
                users=("user.name", "nunique"),
                connections=("mcp.connection_count", "sum"),
                risk=("mcp.risk_level", "first"),
            )
            .reset_index()
            .sort_values("connections", ascending=False)
        )
        for _, row in unknown_summary.iterrows():
            color = _RISK_COLOR.get(row["risk"], "#555")
            st.markdown(
                f"<div style='border-left:4px solid {color};padding:6px 14px;"
                f"margin:5px 0;border-radius:0 6px 6px 0;background:#fff8f8'>"
                f"<strong style='color:{color}'>[{row['risk'].upper()}]</strong> "
                f"<code>{row['mcp.server']}</code> — "
                f"{row['hosts']} hosts · {row['users']} users · {row['connections']} connections"
                f"</div>",
                unsafe_allow_html=True,
            )

    if not new_servers.empty:
        st.markdown("**🆕 Newly seen MCP servers (last 3 days)**")
        st.dataframe(
            new_servers[["host.name", "user.name", "process.name", "mcp.server",
                         "mcp.allowlisted", "mcp.risk_level", "mcp.first_seen",
                         "mcp.connection_count"]]
            .sort_values("mcp.first_seen", ascending=False)
            .head(20),
            use_container_width=True,
        )

    st.markdown("**Full MCP registry**")
    st.dataframe(
        df[["host.name", "user.name", "process.name", "mcp.server", "mcp.allowlisted",
            "mcp.risk_level", "mcp.connection_count", "mcp.is_new", "mcp.first_seen"]]
        .sort_values(["mcp.allowlisted", "mcp.connection_count"], ascending=[True, False]),
        use_container_width=True, height=350,
    )

    st.markdown("**MCP registry ES|QL**")
    st.code("""FROM logs-endpoint.network*
| WHERE process.name IN ("claude-code","cursor","continue")
  AND destination.port == 443
| EVAL is_mcp = CASE(
    destination.domain LIKE "*.internal.elastic.co", false,
    true
  )
| WHERE is_mcp == true
| STATS
    connection_count = COUNT(*),
    unique_hosts     = COUNT_DISTINCT(host.name),
    first_seen       = MIN(@timestamp),
    last_seen        = MAX(@timestamp)
  BY destination.domain, process.name
| EVAL days_active = DATE_DIFF("day", first_seen, NOW())
| SORT connection_count DESC
| LIMIT 30""", language="sql")
