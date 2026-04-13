"""
Prompt Builder View — guided form to generate & refine Create Demo prompts.

Workflow:
  1. User picks a starter template (or starts from scratch)
  2. User fills in a 4-section guided form
  3. "Generate Prompt" → LLM produces a rich Create Demo prompt
  4. User can refine it via natural-language instruction
  5. "Use in Create Demo" copies the prompt into the Create Demo flow
"""

import streamlit as st

from src.services import prompt_builder_service as _pbs


# ── Session state helpers ──────────────────────────────────────────────────────

def _init_state():
    defaults = {
        "pb_template":          "— Start from scratch —",
        "pb_industry":          "",
        "pb_department":        "",
        "pb_persona":           "",
        "pb_data_sources":      [],
        "pb_content_types":     [],
        "pb_doc_count":         "1K – 10K",
        "pb_languages":         "English only",
        "pb_search_type":       "Hybrid (BM25 + Semantic)",
        "pb_features":          [],
        "pb_latency":           "< 500ms",
        "pb_pain_point":        "",
        "pb_success_metric":    "",
        "pb_compliance":        [],
        "pb_generated_prompt":  "",
        "pb_refine_input":      "",
        "pb_history":           [],   # list of prompt strings
        "pb_generating":        False,
        "pb_refining":          False,
        "pb_error":             "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _apply_template(name: str):
    """Overwrite form fields with chosen template values."""
    tpl = _pbs.TEMPLATES.get(name)
    if not tpl:
        return
    st.session_state.pb_industry       = tpl.get("industry", "")
    st.session_state.pb_department     = tpl.get("department", "")
    st.session_state.pb_persona        = tpl.get("persona", "")
    st.session_state.pb_data_sources   = tpl.get("data_sources", [])
    st.session_state.pb_content_types  = tpl.get("content_types", [])
    st.session_state.pb_doc_count      = tpl.get("doc_count", "1K – 10K")
    st.session_state.pb_languages      = tpl.get("languages", "English only")
    st.session_state.pb_search_type    = tpl.get("search_type", "Hybrid (BM25 + Semantic)")
    st.session_state.pb_features       = tpl.get("features", [])
    st.session_state.pb_latency        = tpl.get("latency", "< 500ms")
    st.session_state.pb_pain_point     = tpl.get("pain_point", "")
    st.session_state.pb_success_metric = tpl.get("success_metric", "")
    st.session_state.pb_compliance     = tpl.get("compliance", [])


# ── Main render ────────────────────────────────────────────────────────────────

def render_prompt_builder_view():
    _init_state()

    st.markdown("## ✨ Prompt Builder")
    st.caption(
        "Build a rich **Create Demo** prompt without leaving the app. "
        "Fill in the guided form, generate, refine, then drop it straight into Create Demo."
    )

    # ── Template picker ────────────────────────────────────────────────────────
    template_names = list(_pbs.TEMPLATES.keys())
    chosen_tpl = st.selectbox(
        "Start from a template",
        options=template_names,
        index=template_names.index(st.session_state.pb_template),
        key="pb_template_selector",
        help="Templates pre-fill the form with realistic industry scenarios.",
    )
    if chosen_tpl != st.session_state.pb_template:
        st.session_state.pb_template = chosen_tpl
        _apply_template(chosen_tpl)
        st.rerun()

    st.divider()

    # ── Guided form: 2-column layout ──────────────────────────────────────────
    col_left, col_right = st.columns(2, gap="large")

    # ── LEFT: Customer Context + Business Context ─────────────────────────────
    with col_left:
        st.markdown("### 1 · Customer Context")

        st.session_state.pb_industry = st.selectbox(
            "Industry *",
            options=[""] + _pbs.INDUSTRIES,
            index=([""] + _pbs.INDUSTRIES).index(st.session_state.pb_industry)
                  if st.session_state.pb_industry in _pbs.INDUSTRIES else 0,
            key="pb_industry_sel",
        )

        st.session_state.pb_department = st.selectbox(
            "Department *",
            options=[""] + _pbs.DEPARTMENTS,
            index=([""] + _pbs.DEPARTMENTS).index(st.session_state.pb_department)
                  if st.session_state.pb_department in _pbs.DEPARTMENTS else 0,
            key="pb_department_sel",
        )

        st.session_state.pb_persona = st.text_input(
            "User Persona *",
            value=st.session_state.pb_persona,
            key="pb_persona_inp",
            placeholder="e.g. Call center agents handling customer queries",
        )

        st.markdown("### 4 · Business Context")

        st.session_state.pb_pain_point = st.text_area(
            "Primary Pain Point *",
            value=st.session_state.pb_pain_point,
            key="pb_pain_inp",
            placeholder="e.g. Agents spend too long searching multiple systems during live calls",
            height=80,
        )

        st.session_state.pb_success_metric = st.text_area(
            "Success Metric",
            value=st.session_state.pb_success_metric,
            key="pb_success_inp",
            placeholder="e.g. Reduce average handle time by 30%, improve first-call resolution",
            height=80,
        )

        st.session_state.pb_compliance = st.multiselect(
            "Compliance Requirements",
            options=_pbs.COMPLIANCE_OPTIONS,
            default=st.session_state.pb_compliance,
            key="pb_compliance_sel",
        )

    # ── RIGHT: Data Sources + Search Requirements ─────────────────────────────
    with col_right:
        st.markdown("### 2 · Data Sources")

        st.session_state.pb_data_sources = st.multiselect(
            "Data Sources *",
            options=_pbs.DATA_SOURCES,
            default=[s for s in st.session_state.pb_data_sources if s in _pbs.DATA_SOURCES],
            key="pb_sources_sel",
        )

        st.session_state.pb_content_types = st.multiselect(
            "Content Types *",
            options=_pbs.CONTENT_TYPES,
            default=[c for c in st.session_state.pb_content_types if c in _pbs.CONTENT_TYPES],
            key="pb_content_sel",
        )

        st.session_state.pb_doc_count = st.selectbox(
            "Document Volume",
            options=_pbs.DOC_COUNTS,
            index=_pbs.DOC_COUNTS.index(st.session_state.pb_doc_count)
                  if st.session_state.pb_doc_count in _pbs.DOC_COUNTS else 1,
            key="pb_doccount_sel",
        )

        st.session_state.pb_languages = st.selectbox(
            "Languages",
            options=_pbs.LANGUAGE_OPTIONS,
            index=_pbs.LANGUAGE_OPTIONS.index(st.session_state.pb_languages)
                  if st.session_state.pb_languages in _pbs.LANGUAGE_OPTIONS else 0,
            key="pb_lang_sel",
        )

        st.markdown("### 3 · Search Requirements")

        st.session_state.pb_search_type = st.selectbox(
            "Search Approach",
            options=_pbs.SEARCH_TYPES,
            index=_pbs.SEARCH_TYPES.index(st.session_state.pb_search_type)
                  if st.session_state.pb_search_type in _pbs.SEARCH_TYPES else 0,
            key="pb_searchtype_sel",
        )

        st.session_state.pb_features = st.multiselect(
            "Key Features",
            options=_pbs.FEATURES,
            default=[f for f in st.session_state.pb_features if f in _pbs.FEATURES],
            key="pb_features_sel",
        )

        st.session_state.pb_latency = st.selectbox(
            "Latency Target",
            options=_pbs.LATENCY_OPTIONS,
            index=_pbs.LATENCY_OPTIONS.index(st.session_state.pb_latency)
                  if st.session_state.pb_latency in _pbs.LATENCY_OPTIONS else 1,
            key="pb_latency_sel",
        )

    st.divider()

    # ── Generate button ────────────────────────────────────────────────────────
    required_ok = bool(
        st.session_state.pb_industry
        and st.session_state.pb_department
        and st.session_state.pb_persona
        and st.session_state.pb_data_sources
        and st.session_state.pb_content_types
        and st.session_state.pb_pain_point
    )

    gen_col, clear_col = st.columns([3, 1])
    with gen_col:
        if st.button(
            "✨ Generate Prompt",
            type="primary",
            use_container_width=True,
            disabled=not required_ok,
            key="pb_generate_btn",
            help="Fill in the required fields (*) to enable." if not required_ok else "Generate a Create Demo prompt.",
        ):
            with st.spinner("Generating prompt..."):
                inputs = {
                    "industry":       st.session_state.pb_industry,
                    "department":     st.session_state.pb_department,
                    "persona":        st.session_state.pb_persona,
                    "data_sources":   st.session_state.pb_data_sources,
                    "content_types":  st.session_state.pb_content_types,
                    "doc_count":      st.session_state.pb_doc_count,
                    "languages":      st.session_state.pb_languages,
                    "search_type":    st.session_state.pb_search_type,
                    "features":       st.session_state.pb_features,
                    "latency":        st.session_state.pb_latency,
                    "pain_point":     st.session_state.pb_pain_point,
                    "success_metric": st.session_state.pb_success_metric,
                    "compliance":     st.session_state.pb_compliance,
                }
                text, err = _pbs.generate_prompt(inputs)
                if err:
                    st.session_state.pb_error = err
                else:
                    st.session_state.pb_error = ""
                    if text:
                        # Save current to history before overwriting
                        if st.session_state.pb_generated_prompt:
                            st.session_state.pb_history.insert(0, st.session_state.pb_generated_prompt)
                            st.session_state.pb_history = st.session_state.pb_history[:10]
                        st.session_state.pb_generated_prompt = text
            st.rerun()

    with clear_col:
        if st.button("🗑 Clear", use_container_width=True, key="pb_clear_btn"):
            if st.session_state.pb_generated_prompt:
                st.session_state.pb_history.insert(0, st.session_state.pb_generated_prompt)
                st.session_state.pb_history = st.session_state.pb_history[:10]
            st.session_state.pb_generated_prompt = ""
            st.session_state.pb_error = ""
            st.rerun()

    if st.session_state.pb_error:
        st.error(f"⚠️ {st.session_state.pb_error}")

    # ── Generated prompt output ────────────────────────────────────────────────
    if st.session_state.pb_generated_prompt:
        st.markdown("### Generated Prompt")

        # Editable text area so user can manually tweak too
        edited = st.text_area(
            "Edit directly or use Refine below",
            value=st.session_state.pb_generated_prompt,
            height=220,
            key="pb_prompt_textarea",
            label_visibility="collapsed",
        )
        if edited != st.session_state.pb_generated_prompt:
            st.session_state.pb_generated_prompt = edited

        # Action row
        act1, act2, act3 = st.columns(3)
        with act1:
            if st.button("📋 Copy to clipboard", use_container_width=True, key="pb_copy_btn"):
                st.code(st.session_state.pb_generated_prompt, language=None)
                st.caption("Select all and copy from the box above.")
        with act2:
            if st.button("🚀 Use in Create Demo", use_container_width=True, type="primary", key="pb_use_btn"):
                # Push the prompt into the Create Demo chat messages as a new user message
                st.session_state.setdefault("messages", [])
                st.session_state.messages.append({
                    "role": "user",
                    "content": st.session_state.pb_generated_prompt,
                })
                st.session_state.needs_processing = True
                st.session_state.view_mode = "create"
                st.rerun()
        with act3:
            if st.button("💾 Save to history", use_container_width=True, key="pb_save_btn"):
                if st.session_state.pb_generated_prompt not in st.session_state.pb_history:
                    st.session_state.pb_history.insert(0, st.session_state.pb_generated_prompt)
                    st.session_state.pb_history = st.session_state.pb_history[:10]
                st.success("Saved to history.")

        st.divider()

        # ── Refine row ─────────────────────────────────────────────────────────
        st.markdown("#### Refine this prompt")
        st.caption("Describe what to change — e.g. *make it more technical*, *add emphasis on GDPR compliance*, *make it shorter*.")

        ref_col, btn_col = st.columns([4, 1])
        with ref_col:
            refine_instruction = st.text_input(
                "Refinement instruction",
                key="pb_refine_inp",
                label_visibility="collapsed",
                placeholder="e.g. Add more detail about data volume and real-time indexing requirements",
            )
        with btn_col:
            if st.button("↻ Refine", use_container_width=True, key="pb_refine_btn",
                         disabled=not refine_instruction):
                with st.spinner("Refining..."):
                    new_text, err = _pbs.refine_prompt(st.session_state.pb_generated_prompt, refine_instruction)
                    if err:
                        st.error(f"⚠️ {err}")
                    elif new_text:
                        st.session_state.pb_history.insert(0, st.session_state.pb_generated_prompt)
                        st.session_state.pb_history = st.session_state.pb_history[:10]
                        st.session_state.pb_generated_prompt = new_text
                st.rerun()

    # ── Prompt history ─────────────────────────────────────────────────────────
    if st.session_state.pb_history:
        with st.expander(f"🕘 Prompt history ({len(st.session_state.pb_history)} saved)", expanded=False):
            for i, hist_prompt in enumerate(st.session_state.pb_history):
                h_col1, h_col2 = st.columns([5, 1])
                with h_col1:
                    st.text_area(
                        f"Version {i + 1}",
                        value=hist_prompt,
                        height=100,
                        key=f"pb_hist_{i}",
                        disabled=True,
                        label_visibility="collapsed",
                    )
                with h_col2:
                    if st.button("Restore", key=f"pb_restore_{i}", use_container_width=True):
                        if st.session_state.pb_generated_prompt:
                            st.session_state.pb_history.insert(0, st.session_state.pb_generated_prompt)
                            st.session_state.pb_history = st.session_state.pb_history[:10]
                        st.session_state.pb_generated_prompt = hist_prompt
                        st.rerun()
