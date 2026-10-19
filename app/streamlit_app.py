"""streamlit_app.py — Cynbit Discovery Copilot demo UI.

Runs with NO API key (Offline Mode) out of the box. Optional bring-your-own
GLM key (held in session state only — never logged, never persisted).

Pages: Demo | Eval dashboard.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.core.examples import DEMO_EXAMPLES  # noqa: E402
from app.core.llm_client import GLMClient, ProviderUnavailable  # noqa: E402
from app.core.pipeline import DiscoveryPipeline  # noqa: E402
from app.core.prompts import PROMPT_VERSION  # noqa: E402

st.set_page_config(
    page_title="Cynbit Discovery Copilot",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

FEEDBACK_PATH = REPO_ROOT / "data" / "feedback.jsonl"
RESULTS_DIR = REPO_ROOT / "evals" / "results"


# ---------------------------------------------------------------------------
# Cached resources
# ---------------------------------------------------------------------------


@st.cache_resource(show_spinner=False)
def get_offline_pipeline() -> DiscoveryPipeline:
    return DiscoveryPipeline(provider="offline")


@st.cache_resource(show_spinner=False)
def get_live_pipeline(api_key: str, base_url: str, model: str) -> DiscoveryPipeline:
    llm = GLMClient(api_key=api_key, base_url=base_url or None, model=model or None)
    return DiscoveryPipeline(provider="glm", llm=llm)


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------


def mode_badge(mode: str) -> None:
    labels = {
        "glm_live": ("🟢 LIVE GLM", "green"),
        "glm_live_fallback_offline": ("🟠 LIVE→OFFLINE FALLBACK", "orange"),
        "offline_cached": ("🔵 OFFLINE MODE: precomputed GLM output", "blue"),
        "offline_rules": ("⚪ OFFLINE MODE: rule-based output", "gray"),
    }
    text, color = labels.get(mode, (mode, "gray"))
    st.markdown(
        f'<span style="background-color:{color};color:white;padding:2px 10px;'
        f'border-radius:12px;font-size:0.8em;font-weight:600">{text}</span>',
        unsafe_allow_html=True,
    )


def render_brief(brief) -> None:  # brief: LeadBrief
    prov = brief.provenance
    c1, c2, c3, c4, c5 = st.columns([2, 1.2, 1.2, 1.2, 1.4])
    c1.markdown(f"**Mode:** {prov.mode}")
    mode_badge(prov.mode)
    c2.metric("Latency", f"{prov.latency_ms} ms")
    c3.metric("Tokens (in/out)", f"{prov.prompt_tokens}/{prov.completion_tokens}")
    c4.metric("LLM calls", prov.llm_calls)
    c5.metric("Prompt / schema", f"{prov.prompt_version} / {prov.schema_version}")
    for n in prov.notes:
        st.caption(f"ℹ️ {n}")

    if prov.mode in ("offline_cached", "offline_rules"):
        st.info(
            "OFFLINE MODE: precomputed or rule-based output — this is NOT live "
            "inference. Add a GLM key in the sidebar for live results.",
            icon="🔵",
        )

    if brief.sanitization.injection_suspected:
        st.warning(
            "🛡️ Input contained prompt-injection-style text "
            f"({', '.join(brief.sanitization.injection_patterns)}). "
            "It was treated as untrusted data; instructions were NOT followed.",
            icon="🛡️",
        )
    if brief.sanitization.pii_masked:
        st.caption(
            f"🔒 PII masked before processing: {', '.join(brief.sanitization.pii_types)} "
            "(masked in logs and model input)."
        )

    if brief.out_of_scope:
        st.success(
            "**Out of scope — graceful redirect (no services invented).**\n\n"
            f"{brief.out_of_scope_reason or ''}\n\n"
            f"**Suggested response:** {brief.suggested_response}",
            icon="🧭",
        )
        st.markdown("#### Suggested next steps")
        for s in brief.next_steps:
            st.markdown(f"- **{s.step}** — _{s.owner}_, {s.when}")
        return

    st.markdown("#### 📋 Extracted brief")
    ex = brief.extraction
    left, right = st.columns(2)
    with left:
        st.markdown(f"**Goal:** {ex.goal or '—'}")
        st.markdown(f"**Industry:** {ex.industry or '—'}")
        st.markdown(f"**Budget signal:** {ex.budget_signal or '—'}")
        st.markdown(f"**Timeline signal:** {ex.timeline_signal or '—'}")
    with right:
        st.markdown(f"**Deliverables:** {', '.join(ex.deliverables) or '—'}")
        st.markdown(f"**Tech constraints:** {', '.join(ex.tech_constraints) or '—'}")
        st.markdown(f"**Language:** {ex.communication_language}")
    st.caption(f"Intent: `{brief.intent}` · input summary: {brief.input_summary[:120]}…")

    st.markdown("#### 🎯 Cynbit service fit (grounded in the public catalog)")
    if not brief.services:
        st.warning("No service match reached the confidence floor — ask clarifying questions first.")
    for m in brief.services:
        with st.container(border=True):
            mc1, mc2 = st.columns([3, 1])
            mc1.markdown(f"**{m.service_name}** · `{m.service_id}` · {m.fit}")
            conf = m.confidence
            mc2.progress(min(conf, 1.0), text=f"conf {conf:.2f}")
            st.caption(f"Evidence — {m.evidence}")
            st.caption(f"Source: {m.source_url} (retrieved 2026-10-19)")
    for ev in brief.grounding_evidence:
        st.caption(f"💡 {ev}")

    est = brief.estimate
    if est:
        st.markdown("#### 📊 Complexity & effort (deterministic — same rules in every mode)")
        ec1, ec2, ec3 = st.columns(3)
        ec1.metric("Complexity band", est.complexity)
        ec2.metric("Effort range (indicative)", f"{est.effort_range_weeks[0]}–{est.effort_range_weeks[1]} weeks")
        ec3.metric("Estimate confidence", est.confidence)
        st.caption(f"Why: {est.complexity_rationale}")
        if est.needs_human_review:
            st.warning("⚠️ **Needs human review** — this is a draft for triage, " + est.disclaimer, icon="✋")
        else:
            st.caption(est.disclaimer)

    if brief.risks:
        st.markdown("#### ⚠️ Risks")
        for r in brief.risks:
            sev_icon = {"high": "🔴", "medium": "🟠", "low": "🟢"}[r.severity]
            st.markdown(f"- {sev_icon} **{r.risk}** _({r.severity})_ — mitigation: {r.mitigation}")

    if brief.clarifying_questions:
        st.markdown("#### ❓ Clarifying questions (priority order)")
        for q in brief.clarifying_questions:
            tag = {"must_ask": "MUST", "should_ask": "SHOULD", "nice_to_have": "NICE"}[q.priority]
            st.markdown(f"- **[{tag}]** {q.question} _— {q.why}_")

    if brief.next_steps:
        st.markdown("#### ➡️ Next steps (mapped to Cynbit's real process)")
        for s in brief.next_steps:
            st.markdown(f"- **{s.step}** — _{s.owner}_, {s.when}")

    if brief.process_alignment:
        st.caption("Accelerates Cynbit lifecycle steps: " + " → ".join(brief.process_alignment[:2]))


def save_feedback(ok: bool, brief, text: str) -> None:
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": time.time(),
        "thumbs": "up" if ok else "down",
        "mode": brief.provenance.mode,
        "prompt_version": brief.provenance.prompt_version,
        "input_sha_head": (text[:80]),
        "services": [m.service_id for m in brief.services],
        "complexity": brief.estimate.complexity if brief.estimate else None,
    }
    with FEEDBACK_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🔎 Discovery Copilot")
    st.caption("for Cynbit Technologies — AI/ML intern challenge POC")
    page = st.radio("Go to", ["Demo", "Eval dashboard"], label_visibility="collapsed")

    st.divider()
    st.markdown("**Mode**")
    mode = st.radio(
        "Mode",
        ["Offline (no key)", "Live GLM"],
        label_visibility="collapsed",
    )

    api_key = ""
    base_url, model = "", ""
    if mode == "Live GLM":
        api_key = st.text_input(
            "GLM API key (bring your own)",
            type="password",
            help="Held in browser session only. Never logged, never written to disk. "
            "Free key: open.bigmodel.cn (CN) or z.ai (international).",
        )
        with st.expander("Advanced"):
            base_url = st.text_input(
                "Base URL", value="https://open.bigmodel.cn/api/paas/v4"
            )
            model = st.text_input("Model", value="glm-4-flash")
        if not api_key:
            st.info("No key yet? The app runs fully in Offline Mode.")
    else:
        st.success("Offline Mode active — zero keys, zero network. One-click demo "
                   "examples replay real precomputed GLM outputs; other inputs use "
                   "the deterministic engine.")

    st.divider()
    st.caption(
        "All demo inputs are SYNTHETIC. This tool drafts briefs for humans — "
        "it never sends anything to a client automatically."
    )

# ---------------------------------------------------------------------------
# Demo page
# ---------------------------------------------------------------------------

if page == "Demo":
    st.markdown(
        "# Turn any inbound inquiry into a structured discovery brief — in seconds"
    )
    st.caption(
        "Paste a lead (form, email, WhatsApp, LinkedIn). The copilot sanitizes it, "
        "classifies service fit against Cynbit's public catalog, extracts scope "
        "signals, estimates complexity, and drafts the clarifying questions a "
        "senior architect would ask. Draft output for human review — not a quote."
    )

    with st.expander("🧪 One-click examples (synthetic inputs)"):
        cols = st.columns(4)
        for i, ex in enumerate(DEMO_EXAMPLES):
            with cols[i % 4]:
                if st.button(ex["label"], key=f"ex_{ex['id']}", use_container_width=True):
                    st.session_state["input_text"] = ex["text"]
                    st.session_state["example_note"] = ex["note"]
        if "example_note" in st.session_state:
            st.caption(f"Selected example: {st.session_state['example_note']}")

    text = st.text_area(
        "Inbound inquiry (untrusted input)",
        value=st.session_state.get("input_text", ""),
        height=180,
        placeholder="e.g. 'Hi, we need an AI chatbot for our clinic website…'",
    )

    col_run, col_clear = st.columns([1, 4])
    run = col_run.button("⚡ Analyze inquiry", type="primary", use_container_width=True)
    if col_clear.button("Clear"):
        st.session_state["input_text"] = ""
        st.rerun()

    if run and text.strip():
        try:
            if mode == "Live GLM" and api_key:
                try:
                    pipe = get_live_pipeline(api_key.strip(), base_url, model)
                except ProviderUnavailable as exc:
                    st.error(f"Could not initialize live GLM: {exc}")
                    st.stop()
            else:
                pipe = get_offline_pipeline()
            with st.spinner("Running pipeline…" if mode == "Live GLM" else "Running offline pipeline…"):
                brief = pipe.run(text)
            render_brief(brief)

            st.divider()
            fb1, fb2, _ = st.columns([1, 1, 5])
            if fb1.button("👍 Useful", key="fb_up"):
                save_feedback(True, brief, text)
                st.toast("Feedback saved to local feedback.jsonl")
            if fb2.button("👎 Needs work", key="fb_down"):
                save_feedback(False, brief, text)
                st.toast("Feedback saved to local feedback.jsonl")

            with st.expander("🔍 Raw structured output (LeadBrief JSON)"):
                st.json(brief.model_dump())
        except Exception as exc:  # noqa: BLE001 — demo must never crash
            st.error(f"Something went wrong producing the brief: {type(exc).__name__}. "
                     "This is a demo limitation — try another input or Offline Mode.")
            st.exception(exc)
    elif run:
        st.warning("Paste an inquiry first (or pick a one-click example above).")

    with st.expander("❓ How it works"):
        st.markdown(
            f"""
**Pipeline (prompt version {PROMPT_VERSION}):**

1. **Sanitize** — PII masked (email/phone), prompt-injection screening,
   language & length checks. Input is wrapped in untrusted-data delimiters.
2. **Classify + extract** — service multi-label classification and structured
   field extraction (goal, deliverables, budget/timeline signals). Live mode:
   one schema-validated GLM call (max 2 validation retries). Offline mode:
   TF-IDF/LogReg classifier + regex extraction.
3. **Ground** — every service match is evidenced against the curated public
   catalog (`app/assets/services_catalog.json`, source cynbit.in/services).
   No catalog support → low confidence, flagged.
4. **Estimate** — deterministic complexity banding (S/M/L + effort range).
   Identical rules in live and offline modes; estimates are never LLM-invented.
5. **Advise** — risks, prioritized clarifying questions, next steps mapped to
   Cynbit's 6-step lifecycle. Live: second schema-validated GLM call. Offline:
   feature-keyed templates.
6. **Validate & assemble** — LeadBrief (Pydantic). Confidence and
   needs-human-review flags are explicit.

**Offline Mode is real**: one-click examples replay precomputed live-GLM
outputs (`data/synthetic/cached_outputs.json`); any other input uses the
deterministic engine. The badge always tells you which path produced the result.

**Grounding policy**: the system only states facts about Cynbit that exist in
the retrieved catalog; anything missing becomes a clarifying question.
"""
        )

# ---------------------------------------------------------------------------
# Eval dashboard page
# ---------------------------------------------------------------------------

else:
    st.markdown("# 📊 Evaluation dashboard")
    st.caption("Held-out split (50 synthetic examples, never used for prompt tuning). "
               "Full methodology: evals/run_eval.py")
    summary_path = RESULTS_DIR / "summary.json"
    if not summary_path.exists():
        st.info(
            "No eval results found yet. Run `python evals/run_eval.py` (offline, "
            "no key needed) to generate them."
        )
    else:
        s = json.loads(summary_path.read_text(encoding="utf-8"))
        st.markdown("### Headline numbers")
        cards = st.columns(4)
        cards[0].metric("Service routing (macro-F1)", f"{s.get('service_macro_f1', 0):.2f}")
        cards[1].metric("Exact-set accuracy", f"{s.get('service_exact_set_acc', 0):.2f}")
        cards[2].metric("Out-of-scope recall", f"{s.get('oos_recall', 0):.2f}")
        cards[3].metric("Injection pass rate", f"{s.get('injection_pass_rate', 0):.2f}")
        cards2 = st.columns(4)
        cards2[0].metric("Complexity accuracy", f"{s.get('complexity_acc', 0):.2f}")
        cards2[1].metric("Budget field F1", f"{s.get('budget_f1', 0):.2f}")
        cards2[2].metric("Timeline field F1", f"{s.get('timeline_f1', 0):.2f}")
        cards2[3].metric("Schema validity", f"{s.get('schema_validity', 0):.2f}")

        st.markdown("### Confusion matrix — service routing (offline engine)")
        cm_path = RESULTS_DIR / "confusion_matrix_offline.png"
        if cm_path.exists():
            st.image(str(cm_path), use_container_width=True)

        st.markdown("### Per-metric table (all runs)")
        table_path = RESULTS_DIR / "metrics_table.json"
        if table_path.exists():
            st.dataframe(json.loads(table_path.read_text(encoding="utf-8")))
        st.caption("Sources: evals/results/*.json — see evals/README.md for definitions.")
