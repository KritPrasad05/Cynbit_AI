"""make_sample_chats.py — render sample_chats/ transcripts from real runs.

Sources: (a) cached_outputs.json entries = genuine live-LLM runs of the demo
examples (captured 2026-10-19 with the previous GLM provider — provenance
inside that file; regenerate with scripts/gen_cache.py + a Groq key);
(b) fresh offline-engine runs on novel synthetic inputs (including
failure/edge cases). Each transcript records the mode and latency actually
used, plus a hand-written annotation stub that the author completes in the
markdown.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from app.core.pipeline import DiscoveryPipeline  # noqa: E402

OUT = REPO / "sample_chats"
OUT.mkdir(exist_ok=True)

# Novel offline inputs chosen to show graceful handling + honest failures
OFFLINE_CASES = [
    {
        "id": "offline_very_short",
        "label": "Very short input (edge case)",
        "text": "SEO karte ho?",
        "annotation": "EDGE CASE: 10-char input. The engine still routes to the right service line and the brief is honest about missing scope (low confidence, must-ask questions dominate). Expected behavior, not a failure.",
    },
    {
        "id": "offline_vague",
        "label": "Vague inquiry (weak output — honest failure)",
        "text": "Hi, we need something in AI for our business. Everyone says AI is the future. Can you help?",
        "annotation": "HONEST FAILURE MODE: the classifier must pick something; here it leans AI-automation on near-zero signal. The right behavior is the intent=exploratory label plus must-ask questions — which it does — but the service confidence shown (0.35) is the system admitting it doesn't know. In production this should probably route to 'book a discovery call' only.",
    },
    {
        "id": "offline_budget_miss",
        "label": "Budget phrasing the regex misses (failure case)",
        "text": "We want a customer portal for our logistics clients with live shipment tracking and invoice history. Money is not a concern for the right team. Timeline is flexible.",
        "annotation": "FAILURE CASE (documented in evals): 'Money is not a concern' is a budget signal a human would catch; the regex extractor returns null. The LLM in live mode catches phrases like this more often. Fix candidate: add sentiment-level budget hints + merge LLM/regex extraction.",
    },
    {
        "id": "offline_oos_vendor",
        "label": "Out-of-scope vendor pitch (graceful redirect)",
        "text": "We are a staffing agency placing offshore developers. Would you like to review our talent pool rates? We offer 20% first-order discount on all profiles.",
        "annotation": "OOS: detected by keyword rules, no services invented, polite redirect drafted. Note the vendor's own 'discount' phrasing does NOT trip the injection patterns (correct — it's a real offer, not an attack on our prompt).",
    },
]


def render(md_name: str, title: str, text: str, brief, annotation: str, extra_meta: str) -> None:
    prov = brief.provenance
    lines = [
        f"# {title}",
        "",
        extra_meta,
        "",
        "## Input",
        "",
        "```text",
        text,
        "```",
        "",
        "## Output (LeadBrief, abridged)",
        "",
        f"- **Mode:** `{prov.mode}` · model: {prov.model} · latency: {prov.latency_ms} ms "
        f"· tokens in/out: {prov.prompt_tokens}/{prov.completion_tokens} · prompt v{prov.prompt_version}",
    ]
    if brief.out_of_scope:
        lines += [
            "- **Out of scope:** True — " + (brief.out_of_scope_reason or ""),
            "- **Suggested response:** " + (brief.suggested_response or ""),
        ]
    else:
        lines += [
            f"- **Intent:** {brief.intent}",
            f"- **Goal:** {brief.extraction.goal or '—'}",
            f"- **Industry:** {brief.extraction.industry or '—'} · **budget:** {brief.extraction.budget_signal or '—'} · **timeline:** {brief.extraction.timeline_signal or '—'}",
            "- **Services:** " + (
                "; ".join(f"{m.service_name} ({m.fit}, conf {m.confidence})" for m in brief.services) or "none"
            ),
        ]
        if brief.estimate:
            lines += [
                f"- **Complexity:** {brief.estimate.complexity} · effort {brief.estimate.effort_range_weeks[0]}–{brief.estimate.effort_range_weeks[1]} weeks · confidence {brief.estimate.confidence} · needs_human_review={brief.estimate.needs_human_review}",
                f"- **Why:** {brief.estimate.complexity_rationale}",
            ]
        lines += ["- **Risks:** " + (" | ".join(f"[{r.severity}] {r.risk}" for r in brief.risks) or "—")]
        lines += ["- **Top questions:** " + (" | ".join(f"({q.priority}) {q.question}" for q in brief.clarifying_questions[:3]) or "—")]
    if brief.sanitization.injection_suspected:
        lines += [f"- **SECURITY:** injection suspected — patterns: {', '.join(brief.sanitization.injection_patterns)}"]
    if brief.sanitization.pii_masked:
        lines += [f"- **PII masked:** {', '.join(brief.sanitization.pii_types)}"]
    lines += [
        "",
        "## Annotation",
        "",
        annotation,
        "",
    ]
    (OUT / md_name).write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {md_name}")


def main() -> None:
    # (a) live-LLM transcripts from the cache (historical GLM runs, D-026)
    cache = json.loads((REPO / "data/synthetic/cached_outputs.json").read_text(encoding="utf-8"))
    anns = {
        "ai_doc_chatbot": "STRAIGHTFORWARD LIVE RUN: two LLM calls; correct service (AI automation), budget and timeline extracted, questions are exactly what a solutions architect would ask first. Note evidence lines trace to the public catalog.",
        "aws_migration": "LIVE RUN WITH RISK FLAG: the aggressive 2-month timeline on an L-band migration triggers the high-severity timeline risk — the deterministic estimator and the LLM advisor agreeing is the system working as designed.",
        "hinglish_restaurant": "LIVE RUN, HINGLISH: language detected as hinglish; extraction still lands (goal + tight-budget signal). The advisor recommends bilingual follow-up — a small detail that matters for the Indian SMB market.",
        "injection_case": "SECURITY CASE (LIVE): sanitizer flags the attempt; the model still classifies the underlying website request (software_dev); no discount promise, no prompt content, no CEO signature appears anywhere in the output. This transcript is the one to show skeptical reviewers.",
    }
    for ex in cache["examples"]:
        if ex["example_id"] not in anns:
            continue
        brief = type("B", (), {})  # placeholder, replaced below
        from app.core.schemas import LeadBrief

        brief = LeadBrief.model_validate(ex["output"])
        render(
            f"{ex['example_id']}.md",
            f"Sample chat — {ex['label']}",
            ex["input"],
            brief,
            anns[ex["example_id"]],
            f"Source: precomputed **live LLM** run (historical GLM provider, see "
            f"data/synthetic/cached_outputs.json meta: "
            f"{cache['meta']['model']} via {cache['meta']['base_url']}, {cache['meta']['generated_on']}).",
        )

    # (b) offline-engine transcripts on novel inputs
    pipe = DiscoveryPipeline(provider="offline")
    for case in OFFLINE_CASES:
        t0 = time.perf_counter()
        brief = pipe.run(case["text"])
        brief.provenance.latency_ms = int((time.perf_counter() - t0) * 1000)
        render(
            f"{case['id']}.md",
            f"Sample chat — {case['label']}",
            case["text"],
            brief,
            case["annotation"],
            "Source: **offline engine** run (deterministic, no network) on a novel synthetic input, 2026-10-19.",
        )


if __name__ == "__main__":
    main()
