# 09 — Demo Script and Pitch (bonus)

## 1. 90-second screen-recording script

| t | Action | Say |
|---|--------|-----|
| 0:00 | Open the Space (Offline Mode banner visible) | "This is the Cynbit Discovery Copilot — it turns any inbound inquiry into a structured discovery brief. No API key: it's running entirely offline right now." |
| 0:08 | Click example "AI chatbot over company docs" | "One click on a sample inquiry — the kind that lands in opportunities@ inboxes as a wall of text." |
| 0:15 | Scroll the brief slowly | "In about ten seconds: service fit with evidence from Cynbit's real catalog, scope signals, an S/M/L complexity band, risks, and the exact clarifying questions a senior architect would ask. Every service match cites its source on cynbit.in." |
| 0:30 | Point at the mode badge + latency | "The badge always tells you what produced the output — here, a precomputed live-GLM result replayed from cache. Full transparency, zero cost." |
| 0:38 | Click "Internship application" example | "Out-of-scope input — no services are invented, just a polite redirect drafted for the careers page." |
| 0:48 | Click "Prompt-injection attempt" | "And the security case: the inquiry tries to hijack the assistant. It's flagged, quarantined, the underlying request is still analyzed, and nothing — no discounts, no prompt contents — leaks into the output." |
| 1:00 | Switch sidebar to Live GLM, paste key (blurred) | "With a free GLM key, the same pipeline runs live — two schema-validated calls, with automatic fallback to offline on rate limits. If the key is bad, the demo still works." |
| 1:10 | Run the chatbot example live; show latency/tokens | "Live mode: same brief, fresh inference, token and latency shown. On synthetic eval it routes services at 0.74 exact-set / 0.88 macro-F1 versus 0.36 for pure rules — and every number is in the repo." |
| 1:20 | Open README | "Full code, three reports, the decision log, and the evaluation harness are public. This automates step one of Cynbit's own six-step lifecycle." |

## 2. Five talking points

1. **It maps to Cynbit's actual process** — "Discovery & audit" is their stated first step; the copilot compresses it from a blank-page read to a reviewable brief (evidence: their homepage).
2. **Speed-to-lead economics are brutal** — 100x contact odds inside 5 minutes, 78% of buyers pick the first responder (MIT/HBR; directional) — an instant structured acknowledgment attacks exactly that.
3. **Architecture earns its complexity** — deterministic sanitize/ground/estimate around two schema-validated LLM calls; estimates are never model-invented; rules baseline vs offline vs live are all measured.
4. **Zero-key demo works** — Offline Mode replays real cached GLM outputs and falls back gracefully on any provider failure; the badge prevents misrepresentation.
5. **Honest about limits** — synthetic data, gateway-dependent live numbers, complexity banding is coarse; the 30/60/90 plan's first gate is re-validation on real inquiries.

## 3. Outreach email to opportunities@cynbit.in

**Subject:** AI/ML Engineer Intern challenge — Discovery Copilot POC + report (repo + live demo)

> Hello Cynbit team,
>
> I completed your AI/ML intern challenge and focused it on the first step of
> your own Architectural Lifecycle: Discovery & audit.
>
> **What I built:** the *Discovery Copilot* — a pipeline that turns a raw
> inbound inquiry (form, email, WhatsApp-style text, even Hinglish) into a
> structured brief: service fit grounded in your public catalog with source
> links, scope signals, an S/M/L complexity band, risks, and the clarifying
> questions your team would ask anyway. It runs live on the free GLM tier and
> — because no reviewer should need a key — it also runs fully offline with
> cached model outputs and a deterministic engine.
>
> **Where it is:**
> - Live demo: <LIVE_DEMO_URL>
> - Code + three reports + evaluation: <GITHUB_REPO_URL>
>
> **Honest numbers (synthetic held-out set, all files in the repo):**
> service routing 0.74 exact-set / 0.88 macro-F1 live (0.36 for a rules
> baseline), out-of-scope recall 1.0, prompt-injection pass rate 1.0, ~2.8k
> tokens and ~$0 per inquiry. Limitations are documented, not hidden — the
> first gate in my 30/60/90 plan is re-validating on 100 real inquiries in
> shadow mode.
>
> Building this also meant reading your site closely — services, Studio,
> Revio, TenantEase, BitElevate — and scoring 13 candidate AI opportunities
> before committing to one. The full analysis is in the repo.
>
> Would love 20 minutes to walk you through it.
>
> Best regards,
> <YOUR NAME>
> <LINKEDIN / GITHUB>
