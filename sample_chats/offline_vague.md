# Sample chat — Vague inquiry (weak output — honest failure)

Source: **offline engine** run (deterministic, no network) on a novel synthetic input, 2026-10-19.

## Input

```text
Hi, we need something in AI for our business. Everyone says AI is the future. Can you help?
```

## Output (LeadBrief, abridged)

- **Mode:** `offline_rules` · model: deterministic-rules (TF-IDF/LogReg + templates) · latency: 2 ms · tokens in/out: 0/0 · prompt vv3
- **Intent:** new_project
- **Goal:** we need something in AI for our business
- **Industry:** — · **budget:** — · **timeline:** —
- **Services:** AI Automation Suite (primary, conf 0.95)
- **Complexity:** M · effort 4–10 weeks · confidence low · needs_human_review=True
- **Why:** 1 service line(s) requested; band from train-calibrated model (see docs)
- **Risks:** —
- **Top questions:** (must_ask) What budget range has been approved or is being planned for this engagement? | (must_ask) What is your target go-live date or hard deadline? | (must_ask) What content/documents should the AI ground its answers in, and when should it hand off to a human?

## Annotation

HONEST FAILURE MODE: the classifier must pick something; here it leans AI-automation on near-zero signal. The right behavior is the intent=exploratory label plus must-ask questions — which it does — but the service confidence shown (0.35) is the system admitting it doesn't know. In production this should probably route to 'book a discovery call' only.
