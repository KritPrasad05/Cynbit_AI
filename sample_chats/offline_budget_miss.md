# Sample chat — Budget phrasing the regex misses (failure case)

Source: **offline engine** run (deterministic, no network) on a novel synthetic input, 2026-10-19.

## Input

```text
We want a customer portal for our logistics clients with live shipment tracking and invoice history. Money is not a concern for the right team. Timeline is flexible.
```

## Output (LeadBrief, abridged)

- **Mode:** `offline_rules` · model: deterministic-rules (TF-IDF/LogReg + templates) · latency: 2 ms · tokens in/out: 0/0 · prompt vv3
- **Intent:** new_project
- **Goal:** We want a customer portal for our logistics clients with live shipment tracking and invoice history
- **Industry:** fintech · **budget:** — · **timeline:** —
- **Services:** Custom IT Services — Software Development (secondary, conf 0.35)
- **Complexity:** M · effort 4–10 weeks · confidence low · needs_human_review=True
- **Why:** 1 service line(s) requested; band from train-calibrated model (see docs)
- **Risks:** —
- **Top questions:** (must_ask) What budget range has been approved or is being planned for this engagement? | (must_ask) What is your target go-live date or hard deadline? | (must_ask) Which platforms (web / iOS / Android) and third-party integrations are must-haves for version one?

## Annotation

FAILURE CASE (documented in evals): 'Money is not a concern' is a budget signal a human would catch; the regex extractor returns null. The LLM in live mode catches phrases like this more often. Fix candidate: add sentiment-level budget hints + merge LLM/regex extraction.
