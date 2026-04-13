"""
ESRally Benchmark Tab

Runs the official Elastic ESRally benchmarking tool against the configured
Elasticsearch cluster and displays p50 / p95 / p99 latency results inline.

Challenges:
  • bm25-baseline        — pure BM25, no vector inference
  • semantic-benchmark   — Jina v5 semantic retrieval, isolates inference cost
  • pdf-benchmark        — BM25 on enterprise_pdf_chunks
  • hybrid-rrf-benchmark — BM25 + Jina RRF fusion
  • full-stack           — all operations in sequence

Requires --pipeline=benchmark-only (no cluster provisioning).
"""

import os
import time
import logging
import streamlit as st
from typing import Any

from src.services import esrally_service as rally

logger = logging.getLogger(__name__)

# ── Genesys requirement thresholds (R22) ──────────────────────────────────────
LATENCY_TARGET_MS = 100   # retrieval < 100ms
P95_WARN_MS       = 200   # amber above this
P95_FAIL_MS       = 500   # red above this

_CSS = """
<style>
.rally-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #005571 100%);
    color: white; border-radius: 10px; padding: 18px 24px; margin-bottom: 14px;
}
.rally-header h3 { margin: 0; font-size: 1.25rem; }
.rally-header p  { margin: 4px 0 0; opacity: .8; font-size: .82rem; }
.challenge-card {
    border: 2px solid #e0e0e0; border-radius: 8px; padding: 12px 14px;
    cursor: pointer; transition: border-color .15s;
    background: #fafafa;
}
.challenge-card.selected { border-color: #005571; background: #f0f8fc; }
.challenge-card .ch-title  { font-weight: 700; font-size: .92rem; color: #005571; }
.challenge-card .ch-desc   { font-size: .78rem; color: #555; margin: 3px 0; }
.challenge-card .ch-dur    { font-size: .72rem; color: #999; }
.results-table { width:100%; border-collapse:collapse; font-size:.82rem; margin-top:8px; }
.results-table th { background:#f0f8fc; color:#005571; font-size:.72rem; text-transform:uppercase;
                    padding:6px 10px; border-bottom:2px solid #c8e9f0; text-align:left; }
.results-table td { padding:6px 10px; border-bottom:1px solid #eee; color:#333; }
.results-table tr:hover td { background:#f8fdfd; }
.pass  { color:#009e97; font-weight:700; }
.warn  { color:#c87600; font-weight:700; }
.fail  { color:#c03030; font-weight:700; }
.badge-pass { background:#e6faf9; color:#007a73; border-radius:10px;
              padding:2px 8px; font-size:.72rem; font-weight:700; }
.badge-warn { background:#fff8e6; color:#c87600; border-radius:10px;
              padding:2px 8px; font-size:.72rem; font-weight:700; }
.badge-fail { background:#fff0f0; color:#c03030; border-radius:10px;
              padding:2px 8px; font-size:.72rem; font-weight:700; }
.req-bar { background:#f0f8fc; border:1px solid #c8e9f0; border-radius:6px;
           padding:8px 12px; margin-bottom:10px; font-size:.78rem; }
.req-bar strong { color:#005571; }
</style>
"""

SLI_METRICS = [
    ("50th percentile latency",  "p50 Latency"),
    ("90th percentile latency",  "p90 Latency"),
    ("95th percentile latency",  "p95 Latency"),
    ("99th percentile latency",  "p99 Latency"),
    ("100th percentile latency", "p100 (max)"),
    ("95th percentile service time", "p95 Service Time"),
    ("Mean throughput",          "Mean Throughput"),
    ("error rate",               "Error Rate"),
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _latency_class(value_ms: float, metric_name: str) -> str:
    if "throughput" in metric_name.lower():
        return ""
    if "error" in metric_name.lower():
        return "fail" if value_ms > 0 else "pass"
    if value_ms <= LATENCY_TARGET_MS:
        return "pass"
    if value_ms <= P95_WARN_MS:
        return "warn"
    return "fail"


def _badge(value_ms: float) -> str:
    if value_ms <= LATENCY_TARGET_MS:
        return f'<span class="badge-pass">✓ &lt;{LATENCY_TARGET_MS}ms target</span>'
    if value_ms <= P95_WARN_MS:
        return f'<span class="badge-warn">⚠ above target</span>'
    return f'<span class="badge-fail">✗ exceeds target</span>'


def _render_results_table(by_task: dict[str, list[dict]]) -> None:
    if not by_task:
        st.warning("No metrics found in results file.")
        return

    for task, metrics in by_task.items():
        st.markdown(f"**Operation: `{task}`**")

        rows_html = ""
        for m in metrics:
            name   = m["metric"]
            val    = m["value"]
            unit   = m["unit"]
            is_lat = "latency" in name.lower() or "service time" in name.lower()
            cls    = _latency_class(val, name) if is_lat else ""
            badge  = _badge(val) if "95th" in name and is_lat else ""
            label  = next((lbl for key, lbl in SLI_METRICS if key.lower() == name.lower()), name)
            rows_html += (
                f"<tr>"
                f"  <td>{label}</td>"
                f"  <td class='{cls}'>{val:,.2f} {unit}</td>"
                f"  <td>{badge}</td>"
                f"</tr>"
            )

        st.markdown(
            f'<table class="results-table">'
            f"<tr><th>Metric</th><th>Value</th><th>vs R22 Target (&lt;100ms)</th></tr>"
            f"{rows_html}"
            f"</table>",
            unsafe_allow_html=True,
        )
        st.write("")


def _render_past_results(challenge: str) -> None:
    raw     = rally.load_results(challenge)
    by_task = rally.summarise_results(raw)
    if not by_task:
        return
    st.markdown("---")
    st.markdown("#### Previous Run Results")
    _render_results_table(by_task)


# ── Main render ────────────────────────────────────────────────────────────────

def render_esrally_tab(loader: Any = None) -> None:
    st.markdown(_CSS, unsafe_allow_html=True)

    st.markdown(
        '<div class="rally-header">'
        "<h3>⚡ ESRally Benchmark</h3>"
        "<p>Official Elastic macro-benchmarking tool · pipeline: benchmark-only · "
        "measures p50 / p95 / p99 latency against your live cluster</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Session state ────────────────────────────────────────────────────────
    for key, default in [
        ("rally_installed",      None),   # None = unchecked
        ("rally_version",        ""),
        ("rally_running",        False),
        ("rally_output_lines",   []),
        ("rally_returncode",     None),
        ("rally_challenge",      "bm25-baseline"),
        ("rally_host",           ""),
        ("rally_show_output",    False),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # ── Check installation (once per session) ────────────────────────────────
    if st.session_state.rally_installed is None:
        st.session_state.rally_installed = rally.is_installed()
        if st.session_state.rally_installed:
            st.session_state.rally_version = rally.get_version()

    if not st.session_state.get("rally_host"):
        st.session_state.rally_host = rally.get_target_host_from_env()

    # ── Install banner ───────────────────────────────────────────────────────
    if not st.session_state.rally_installed:
        st.warning(
            "**ESRally is not installed.** "
            "Click below to install it into the current Python environment via pip."
        )
        if st.button("📦 Install ESRally", key="rally_install_btn"):
            output_ph = st.empty()
            lines: list[str] = []

            def _on_line(line: str) -> None:
                lines.append(line)
                output_ph.code("".join(lines[-15:]), language=None)

            ok, msg = rally.install(on_line=_on_line)
            if ok:
                st.session_state.rally_installed = True
                st.session_state.rally_version   = rally.get_version()
                st.success("ESRally installed. Refresh to continue.")
                st.rerun()
            else:
                st.error(f"Install failed: {msg}")
        return

    # ── Installed — show version ─────────────────────────────────────────────
    ver = st.session_state.rally_version
    st.caption(f"ESRally {ver} · track: `tracks/genesys_knowledge/`")

    # ── R22 requirement reminder ─────────────────────────────────────────────
    st.markdown(
        '<div class="req-bar">🎯 <strong>Genesys R22 Target</strong>: '
        "Retrieval &lt; <strong>100ms</strong> end-to-end &nbsp;·&nbsp; "
        "200 QPS average per region &nbsp;·&nbsp; "
        "p95 results are colour-coded against this threshold</div>",
        unsafe_allow_html=True,
    )

    # ── Challenge selector ───────────────────────────────────────────────────
    st.markdown("#### Select Challenge")
    challenge_keys = list(rally.CHALLENGES.keys())
    cols = st.columns(len(challenge_keys))
    for col, key in zip(cols, challenge_keys):
        ch = rally.CHALLENGES[key]
        selected = st.session_state.rally_challenge == key
        with col:
            if st.button(
                f"{ch['icon']} {ch['label']}\n{ch['duration']}",
                key=f"ch_{key}",
                use_container_width=True,
                type="primary" if selected else "secondary",
            ):
                st.session_state.rally_challenge = key
                st.rerun()

    active = rally.CHALLENGES[st.session_state.rally_challenge]
    st.caption(f"**{active['icon']} {active['label']}** — {active['description']}")

    # ── Benchmark stats line ─────────────────────────────────────────────────
    warmup     = active.get("warmup", 0)
    iterations = active.get("iterations", 0)
    target_qps = active.get("target_qps")
    ops        = active.get("operations", 1)
    index_lbl  = active.get("index", "")
    qps_str    = f"{target_qps} QPS target" if target_qps else "mixed QPS"
    ops_str    = f"{ops} operation{'s' if ops > 1 else ''}"
    st.markdown(
        f"<div style='background:#f0f8fc;border:1px solid #c8e9f0;border-radius:6px;"
        f"padding:7px 14px;font-size:.78rem;color:#444;margin-top:4px;'>"
        f"📊 &nbsp;<b>{iterations} measurement queries</b> + {warmup} warmup &nbsp;·&nbsp; "
        f"{qps_str} &nbsp;·&nbsp; {ops_str} &nbsp;·&nbsp; "
        f"index: <code>{index_lbl}</code>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Configuration ────────────────────────────────────────────────────────
    st.markdown("#### Cluster & Options")
    cfg_c1, cfg_c2 = st.columns([3, 1])

    with cfg_c1:
        host = st.text_input(
            "Elasticsearch endpoint",
            value=st.session_state.rally_host,
            key="rally_host_input",
            placeholder="https://your-cluster.es.io:443",
            help="HTTPS endpoint of your cluster. Auto-filled from ELASTIC_ENDPOINT or ELASTICSEARCH_CLOUD_ID.",
        )
        st.session_state.rally_host = host

    with cfg_c2:
        api_key = st.text_input(
            "API Key",
            value=os.getenv("ELASTICSEARCH_API_KEY", ""),
            type="password",
            key="rally_api_key_input",
            help="Elasticsearch API key. Defaults to ELASTICSEARCH_API_KEY env var.",
        )

    adv_c1, adv_c2 = st.columns(2)
    with adv_c1:
        race_id = st.text_input(
            "Race ID (optional)",
            value=f"vulcan-{st.session_state.rally_challenge}",
            key="rally_race_id",
            help="Identifier for this run — used in ESRally's internal datastore.",
        )
    with adv_c2:
        st.info(
            "Iterations and throughput are defined in the track.json per challenge. "
            "Edit `tracks/genesys_knowledge/track.json` to customise.",
            icon="ℹ️",
        )

    # ── Run ──────────────────────────────────────────────────────────────────
    st.divider()
    run_col, clear_col = st.columns([4, 1])

    with run_col:
        can_run = bool(host and api_key) and not st.session_state.rally_running
        run_btn = st.button(
            f"▶ Run {active['icon']} {active['label']}",
            disabled=not can_run,
            type="primary",
            use_container_width=True,
            key="rally_run_btn",
            help="Requires endpoint + API key." if not can_run else f"Estimated duration: {active['duration']}",
        )

    with clear_col:
        if st.button("Clear", use_container_width=True, key="rally_clear"):
            st.session_state.rally_output_lines = []
            st.session_state.rally_returncode   = None
            st.rerun()

    if not host or not api_key:
        st.caption("⚠️ Set Elasticsearch endpoint and API key above to enable benchmarking.")

    # ── Execute ESRally ──────────────────────────────────────────────────────
    if run_btn and can_run:
        st.session_state.rally_running      = True
        st.session_state.rally_output_lines = []
        st.session_state.rally_returncode   = None

        challenge = st.session_state.rally_challenge
        cmd = rally.build_command(
            challenge=challenge,
            target_host=host,
            api_key=api_key,
            race_id=race_id,
        )

        st.info(f"Running: `{' '.join(cmd[:4])} …`")
        output_ph = st.empty()
        lines: list[str] = []

        def _on_line(line: str) -> None:
            lines.append(line)
            # Show last 25 lines of output live
            output_ph.code("".join(lines[-25:]), language=None)

        with st.spinner(f"ESRally running {active['label']} ({active['duration']})…"):
            rc, _ = rally.run_race(cmd, on_line=_on_line)

        st.session_state.rally_output_lines = lines
        st.session_state.rally_returncode   = rc
        st.session_state.rally_running      = False
        st.rerun()

    # ── Output + Results ─────────────────────────────────────────────────────
    rc = st.session_state.rally_returncode

    if st.session_state.rally_output_lines:
        with st.expander(
            "📜 ESRally Output Log",
            expanded=(rc is not None and rc != 0),
        ):
            st.code("".join(st.session_state.rally_output_lines), language=None)

    if rc is not None:
        if rc == 0:
            st.success("✅ Benchmark completed successfully.")
        else:
            st.error(f"❌ ESRally exited with code {rc}. Check the output log above.")

    # ── Results panel ────────────────────────────────────────────────────────
    challenge = st.session_state.rally_challenge
    raw       = rally.load_results(challenge)
    by_task   = rally.summarise_results(raw)

    if by_task:
        st.markdown(f"#### Results — {active['icon']} {active['label']}")
        _render_results_table(by_task)

        # Quick p95 callout
        all_p95 = [
            m["value"]
            for metrics in by_task.values()
            for m in metrics
            if "95th percentile latency" in m["metric"]
        ]
        if all_p95:
            max_p95 = max(all_p95)
            badge   = _badge(max_p95)
            st.markdown(
                f"**Worst-case p95 latency across all operations: "
                f"`{max_p95:.1f} ms`** &nbsp; {badge}",
                unsafe_allow_html=True,
            )
    elif rc == 0:
        st.info("Results file not found. ESRally may have written it to a different path — "
                "check `tracks/genesys_knowledge/results/`.")

    # ── Past results from other challenges ───────────────────────────────────
    past = [r for r in rally.list_past_results() if r["challenge"] != challenge]
    if past:
        with st.expander("📂 Previous Results (other challenges)", expanded=False):
            for entry in past:
                st.markdown(f"**{entry['label']}** — {entry['metric_count']} metrics saved")
                ch_raw     = rally.load_results(entry["challenge"])
                ch_by_task = rally.summarise_results(ch_raw)
                _render_results_table(ch_by_task)
