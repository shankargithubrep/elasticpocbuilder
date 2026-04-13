"""
What's New View

Shows SA-curated Elastic feature updates, auto-fetched daily.
Each feature card shows: relevance score, demo-ability, talking points,
how to demo it, and an optional ES|QL/API example.

SAs can approve features (marks them ready for demo use) or skip them.
"""

import subprocess
import sys
import logging
from pathlib import Path

import streamlit as st

from src.services.feature_curator import load_latest_features, load_feature_stats

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Category colours
# ---------------------------------------------------------------------------

_CAT_COLORS = {
    "Search":        "#0077CC",
    "AI/ML":         "#6B21A8",
    "Observability": "#1A7A4A",
    "Security":      "#B22222",
    "Analytics":     "#D4730A",
    "Platform":      "#444444",
    "Infrastructure":"#1E6F9F",
}

_DEMO_ABILITY_COLOR = {
    "high":   "#1A7A4A",
    "medium": "#D4730A",
    "low":    "#888888",
}

_DEMO_ABILITY_EMOJI = {"high": "🟢", "medium": "🟡", "low": "🔴"}


def _cat_color(cat: str) -> str:
    return _CAT_COLORS.get(cat, "#555555")


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render_whats_new_view():
    st.markdown("## 🆕 What's New in Elastic")
    st.caption(
        "Daily-updated SA intelligence feed — new features curated for demo relevance, "
        "with talking points and how-to-demo guides written for you."
    )

    stats = load_feature_stats()
    _render_stats_bar(stats)

    features = load_latest_features(n_days=30)

    if not features:
        _render_empty_state()
        return

    _render_controls(features)


def _render_stats_bar(stats: dict):
    if not stats.get("last_updated"):
        return
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Features this week", stats.get("total", 0))
    with col2:
        st.metric("Demo-ready", stats.get("high_demo", 0), help="Features with demo_ability = high")
    with col3:
        st.metric("Last updated", stats.get("last_updated", "—"))
    with col4:
        if st.button("🔄 Refresh Now", use_container_width=True, help="Run the feature monitor now (takes ~1 min)"):
            _run_monitor_inline()


def _render_empty_state():
    st.info(
        "**No features fetched yet.**\n\n"
        "Click **Refresh Now** above, or run:\n"
        "```bash\npython scripts/run_feature_monitor.py\n```\n\n"
        "The GitHub Actions workflow will also run this automatically every day at 8 AM UTC "
        "once you configure your API key secrets in the repo settings."
    )

    st.markdown("### Quick Setup")
    st.markdown("""
**1. Run once manually to seed the feed:**
```bash
python scripts/run_feature_monitor.py
```

**2. For daily auto-updates via GitHub Actions, add these secrets to your repo:**
- `ANTHROPIC_API_KEY` — or `LLM_PROXY_URL` + `LLM_PROXY_API_KEY`

Go to: _GitHub repo → Settings → Secrets and variables → Actions → New repository secret_

**3. Trigger the first run:**

GitHub repo → Actions → Daily Elastic Feature Monitor → Run workflow
""")


def _render_controls(features: list):
    # Filter bar
    categories = sorted(set(f.get("feature_category", "Other") or "Other" for f in features))
    all_label = "🗂️ All"
    cat_options = [all_label] + categories

    col_filter, col_sort = st.columns([4, 2])
    with col_filter:
        selected_cat = st.segmented_control(
            "Category",
            options=cat_options,
            default=all_label,
            key="whats_new_cat",
            label_visibility="collapsed",
        )
    with col_sort:
        show_only_high = st.toggle("🟢 High demo-ability only", key="whats_new_high_only")

    # Apply filters
    visible = features
    if selected_cat and selected_cat != all_label:
        visible = [f for f in visible if (f.get("feature_category") or "Other") == selected_cat]
    if show_only_high:
        visible = [f for f in visible if f.get("demo_ability") == "high"]

    st.caption(f"Showing **{len(visible)}** of **{len(features)}** features")

    if not visible:
        st.info("No features match the current filter.")
        return

    # Render cards
    for feat in visible:
        _render_feature_card(feat)


def _render_feature_card(feat: dict):
    cat     = feat.get("feature_category", "Platform") or "Platform"
    ability = feat.get("demo_ability", "low") or "low"
    score   = feat.get("sa_relevance_score", 0)
    color   = _cat_color(cat)
    ability_color = _DEMO_ABILITY_COLOR.get(ability, "#888")
    ability_emoji = _DEMO_ABILITY_EMOJI.get(ability, "⚪")

    with st.container(border=True):
        # Header row
        col_cat, col_title, col_score = st.columns([2, 7, 1])
        with col_cat:
            st.markdown(
                f"<span style='background:{color};color:white;padding:3px 8px;"
                f"border-radius:4px;font-size:0.8em;font-weight:bold'>{cat}</span>",
                unsafe_allow_html=True,
            )
        with col_title:
            url = feat.get("url", "")
            title = feat.get("title", "")
            if url:
                st.markdown(f"**[{title}]({url})**")
            else:
                st.markdown(f"**{title}**")
        with col_score:
            st.markdown(
                f"<div style='text-align:center;font-size:1.3em;font-weight:bold;color:{color}'>"
                f"{score}<span style='font-size:0.6em;color:#888'>/10</span></div>",
                unsafe_allow_html=True,
            )

        # Demo ability + published
        meta_parts = [f"{ability_emoji} Demo: **{ability}**"]
        pub = feat.get("published", "")
        if pub:
            meta_parts.append(f"📅 {pub[:10]}")
        source_label = {"elastic_blog": "Elastic Blog", "github_release": "GitHub Release", "whats_new_page": "What's New"}.get(feat.get("source", ""), feat.get("source", ""))
        meta_parts.append(f"📡 {source_label}")
        st.caption(" · ".join(meta_parts))

        # Why it matters
        why = feat.get("why_it_matters", "")
        if why:
            st.markdown(
                f"<div style='border-left:3px solid {color};padding:5px 12px;"
                f"background:#f8f9fa;border-radius:0 4px 4px 0;margin:6px 0;"
                f"font-size:0.9em'>{why}</div>",
                unsafe_allow_html=True,
            )

        # Talking points + how to demo side by side
        col_talk, col_demo = st.columns(2)

        with col_talk:
            points = feat.get("talking_points", [])
            if points:
                st.markdown("**💬 Customer Talking Points**")
                for pt in points:
                    st.markdown(f"- {pt}")

        with col_demo:
            how = feat.get("how_to_demo", "")
            if how:
                st.markdown("**🖥️ How to Demo**")
                st.markdown(how)

        # ES|QL / API example
        example = feat.get("esql_or_api_example", "")
        if example and example.strip():
            with st.expander("📋 ES|QL / API Example"):
                lang = "sql" if any(k in example.upper() for k in ("FROM ", "WHERE ", "STATS ", "| ")) else "bash"
                st.code(example, language=lang)

        # Competitive angle
        angle = feat.get("competitive_angle", "")
        if angle and angle.strip():
            st.markdown(
                f"<div style='font-size:0.82em;color:#555;background:#fffbe6;"
                f"border:1px solid #ffe58f;padding:5px 10px;border-radius:4px;margin-top:4px'>"
                f"⚔️ <strong>Competitive angle:</strong> {angle}</div>",
                unsafe_allow_html=True,
            )

        # Pain points + industries
        pain = feat.get("pain_points", [])
        industries = feat.get("target_industries", [])
        footer_parts = []
        if pain:
            footer_parts.append("**Pain points:** " + " · ".join(f"`{p}`" for p in pain))
        if industries:
            footer_parts.append("**Industries:** " + " · ".join(industries))
        if footer_parts:
            st.caption("  |  ".join(footer_parts))

        # Approve / Skip actions
        fid = feat.get("id", feat.get("title", ""))
        approved_key = f"feat_approved_{fid}"
        skipped_key  = f"feat_skipped_{fid}"

        current_status = feat.get("status", "pending_review")
        if st.session_state.get(approved_key):
            current_status = "approved"
        elif st.session_state.get(skipped_key):
            current_status = "skipped"

        if current_status == "approved":
            st.success("✅ Marked as demo-ready")
        elif current_status == "skipped":
            st.caption("⏭️ Skipped")
        else:
            col_approve, col_skip, col_space = st.columns([2, 2, 6])
            with col_approve:
                if st.button("✅ Demo Ready", key=f"approve_{fid}", use_container_width=True, type="primary"):
                    st.session_state[approved_key] = True
                    st.rerun()
            with col_skip:
                if st.button("⏭️ Skip", key=f"skip_{fid}", use_container_width=True):
                    st.session_state[skipped_key] = True
                    st.rerun()


# ---------------------------------------------------------------------------
# Inline monitor run (triggered from UI Refresh button)
# ---------------------------------------------------------------------------

def _run_monitor_inline():
    placeholder = st.empty()
    messages = []

    def log(msg):
        messages.append(msg)
        placeholder.markdown("\n\n".join(messages[-6:]))

    log("🚀 Starting feature monitor...")
    try:
        result = subprocess.run(
            [sys.executable, "scripts/run_feature_monitor.py", "--days", "7"],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode == 0:
            log("✅ Done! Refreshing...")
            st.rerun()
        else:
            log(f"❌ Error:\n```\n{result.stderr[-500:]}\n```")
    except subprocess.TimeoutExpired:
        log("⏱️ Monitor timed out after 3 minutes. Try running manually.")
    except Exception as e:
        log(f"❌ Failed to run monitor: {e}")
