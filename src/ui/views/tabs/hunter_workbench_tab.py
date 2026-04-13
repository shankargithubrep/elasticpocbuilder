"""
Hunter WorkBench Tab

JupyterLab integration for deep observability investigation:
  - Notebook template gallery (6 templates across SRE / DevOps / Leadership)
  - One-click download of .ipynb with pre-wired ES|QL + tenant config
  - Cell preview before download
  - JupyterLab quick-start setup guide
  - Requirements snippet for pip install
"""

import json
import urllib.parse
import streamlit as st
import streamlit.components.v1 as _st_components

from src.services.hunter_notebook_service import HunterNotebookService, TEMPLATES

# ── CSS ───────────────────────────────────────────────────────────────────────

_CSS = """
<style>
.hw-header {
  background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 50%, #2d1b69 100%);
  color: white; padding: 20px 24px; border-radius: 10px; margin-bottom: 16px;
}
.hw-header h2 { margin: 0; font-size: 1.5rem; }
.hw-header p  { margin: 4px 0 0; opacity: .75; font-size: .85rem; }

.nb-card {
  border: 1px solid #e0e0e0; border-radius: 10px; padding: 16px;
  background: white; transition: box-shadow .15s;
  margin-bottom: 4px;
}
.nb-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.1); }
.nb-card .nb-icon { font-size: 2rem; }
.nb-card .nb-title { font-weight: 700; font-size: 1rem; margin: 4px 0; }
.nb-card .nb-desc  { font-size: .82rem; color: #555; }
.nb-card .nb-persona { font-size: .75rem; color: #1565c0;
  background: #e8f4f8; border-radius: 4px; padding: 2px 6px; }

.cell-preview {
  background: #1e1e1e; color: #d4d4d4; border-radius: 6px;
  padding: 12px 16px; font-family: monospace; font-size: .8rem;
  white-space: pre-wrap; overflow-x: auto; max-height: 320px;
}
.md-preview {
  background: #f8f9fa; border-left: 3px solid #6c757d;
  padding: 8px 12px; border-radius: 0 4px 4px 0; margin-bottom: 4px;
  font-size: .85rem;
}

.setup-step {
  background: #f0f7ff; border-left: 4px solid #1565c0;
  padding: 10px 14px; border-radius: 0 6px 6px 0; margin-bottom: 8px;
  font-size: .85rem;
}
</style>
"""


def _copy_button(content: str, key: str, label: str = "📋 Copy"):
    encoded = urllib.parse.quote(content, safe="")
    _st_components.html(
        f"""<button
          style="background:#1f4e79;color:white;border:none;border-radius:4px;
                 padding:5px 12px;cursor:pointer;font-size:12px;font-family:monospace;"
          onclick="navigator.clipboard.writeText(decodeURIComponent('{encoded}'))
                   .then(()=>{{this.innerHTML='✅ Copied!';setTimeout(()=>this.innerHTML='{label}',2000)}})
                   .catch(()=>this.innerHTML='❌ Failed')">{label}</button>""",
        height=40,
    )


def _tenant_bar() -> tuple:
    c1, c2 = st.columns(2)
    with c1:
        tenant = st.text_input("Tenant ID", value="default", key="hw_tenant")
    with c2:
        region = st.selectbox("Region", ["us-east-1", "eu-west-1", "ap-southeast-1", "us-central1"], key="hw_region")
    return tenant, region


# ── Notebook gallery ──────────────────────────────────────────────────────────

def _render_gallery(tenant: str, region: str):
    svc       = HunterNotebookService()
    templates = svc.list_templates()

    # Group by persona
    groups = {}
    for t in templates:
        for persona in t["persona"].split(" / "):
            persona = persona.strip()
            groups.setdefault(persona, []).append(t)

    persona_filter = st.segmented_control(
        "Filter by persona",
        options=["All"] + sorted(groups.keys()),
        default="All",
        key="hw_persona_filter",
    )

    shown = templates if persona_filter == "All" else [
        t for t in templates if persona_filter in t["persona"]
    ]

    cols = st.columns(3)
    for i, tpl in enumerate(shown):
        with cols[i % 3]:
            st.markdown(f"""
<div class="nb-card">
  <div class="nb-icon">{tpl['icon']}</div>
  <div class="nb-title">{tpl['title']}</div>
  <div class="nb-desc">{tpl['description']}</div>
  <br/>
  <span class="nb-persona">👤 {tpl['persona']}</span>
</div>
""", unsafe_allow_html=True)

            col_dl, col_prev = st.columns(2)

            with col_dl:
                nb_bytes = svc.generate_bytes(tpl["key"], tenant_id=tenant, region=region)
                fname    = f"{tpl['key']}_{tenant}.ipynb"
                st.download_button(
                    label="⬇️ Download",
                    data=nb_bytes,
                    file_name=fname,
                    mime="application/json",
                    key=f"dl_{tpl['key']}",
                    use_container_width=True,
                )

            with col_prev:
                if st.button("👁️ Preview", key=f"prev_{tpl['key']}", use_container_width=True):
                    st.session_state["hw_preview"] = tpl["key"]


# ── Cell preview ──────────────────────────────────────────────────────────────

def _render_preview(tenant: str, region: str):
    key = st.session_state.get("hw_preview")
    if not key or key not in TEMPLATES:
        return

    tpl = TEMPLATES[key]
    svc = HunterNotebookService()
    nb_json = json.loads(svc.generate_bytes(key, tenant_id=tenant, region=region))

    st.markdown(f"### 👁️ Preview — {tpl['icon']} {tpl['title']}")
    st.caption(f"Showing all cells · tenant: `{tenant}` · region: `{region}`")

    for cell in nb_json["cells"]:
        src = "".join(cell["source"])
        if cell["cell_type"] == "markdown":
            st.markdown(f'<div class="md-preview">{src}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="cell-preview">{src}</div>', unsafe_allow_html=True)

    if st.button("✖ Close preview", key="hw_close_preview"):
        st.session_state.pop("hw_preview", None)
        st.rerun()


# ── JupyterLab setup guide ────────────────────────────────────────────────────

def _render_setup():
    st.markdown("### ⚙️ JupyterLab Quick-Start")

    st.markdown("""
<div class="setup-step">
<strong>Step 1 — Install dependencies</strong>
</div>
""", unsafe_allow_html=True)

    pip_cmd = "pip install jupyterlab elasticsearch pandas plotly numpy"
    st.code(pip_cmd, language="bash")
    _copy_button(pip_cmd, "copy_pip")

    st.markdown("""
<div class="setup-step">
<strong>Step 2 — Set environment variables</strong>
</div>
""", unsafe_allow_html=True)

    env_snippet = """export ELASTIC_ENDPOINT="https://your-cluster.es.io:9243"
export ELASTICSEARCH_API_KEY="your-api-key-here"

# Then launch JupyterLab
jupyter lab"""
    st.code(env_snippet, language="bash")
    _copy_button(env_snippet, "copy_env")

    st.markdown("""
<div class="setup-step">
<strong>Step 3 — Open your downloaded .ipynb and run all cells</strong><br/>
<code>Kernel → Restart Kernel and Run All Cells</code>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="setup-step">
<strong>Optional — Use a .env file (recommended)</strong>
</div>
""", unsafe_allow_html=True)

    env_file = """# .env (add to .gitignore)
ELASTIC_ENDPOINT=https://your-cluster.es.io:9243
ELASTICSEARCH_API_KEY=your-api-key-here"""
    st.code(env_file, language="bash")
    _copy_button(env_file, "copy_dotenv")

    st.markdown("""
<div class="setup-step">
<strong>requirements.txt for sharing notebooks</strong>
</div>
""", unsafe_allow_html=True)

    reqs = "elasticsearch>=8.10.0\npandas>=2.0.0\nplotly>=5.18.0\nnumpy>=1.24.0\npython-dotenv>=1.0.0"
    st.code(reqs, language="text")
    _copy_button(reqs, "copy_reqs")

    with st.expander("🔐 Security note — protecting API keys", expanded=False):
        st.markdown("""
- **Never commit API keys** to Git. Use `.env` and add it to `.gitignore`.
- Use a **scoped API key** with read-only access to the relevant indices.
- For shared notebooks, use **Elastic role-based API keys** that expire.
- Strip cell outputs before sharing: `jupyter nbconvert --ClearOutputPreprocessor.enabled=True`.
""")


# ── All notebooks bundle ──────────────────────────────────────────────────────

def _render_bundle(tenant: str, region: str):
    st.markdown("### 📦 Download All Notebooks")
    st.caption("Get all 6 notebooks in a single zip archive, pre-configured for your tenant and region.")

    if st.button("⬇️ Generate & Download All (ZIP)", type="primary", key="hw_bundle"):
        import io, zipfile
        svc = HunterNotebookService()
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for key in TEMPLATES:
                nb_bytes = svc.generate_bytes(key, tenant_id=tenant, region=region)
                zf.writestr(f"{key}_{tenant}.ipynb", nb_bytes)
        buf.seek(0)
        st.download_button(
            label="📥 Download ZIP",
            data=buf,
            file_name=f"hunter_workbench_{tenant}.zip",
            mime="application/zip",
            key="hw_bundle_dl",
        )


# ── Main entry point ──────────────────────────────────────────────────────────

def render_hunter_workbench_tab(loader):
    """Render the Hunter WorkBench tab for observability demos."""
    st.markdown(_CSS, unsafe_allow_html=True)

    st.markdown("""
<div class="hw-header">
  <h2>🔬 Hunter WorkBench</h2>
  <p>JupyterLab notebooks with pre-built ES|QL · tenant-scoped · download and run against your live cluster</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
> Download any notebook, open it in JupyterLab, and run all cells against your live Elastic cluster.
> Every query is pre-scoped to your **tenant** and **region** — no editing needed.
""")

    tenant, region = _tenant_bar()

    tab1, tab2, tab3 = st.tabs(["📓 Notebook Gallery", "⚙️ JupyterLab Setup", "📦 Download All"])

    with tab1:
        _render_gallery(tenant, region)
        _render_preview(tenant, region)

    with tab2:
        _render_setup()

    with tab3:
        _render_bundle(tenant, region)
