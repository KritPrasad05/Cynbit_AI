# Sample chat — Very short input (edge case)

Source: **offline engine** run (deterministic, no network) on a novel synthetic input, 2026-10-19.

## Input

```text
SEO karte ho?
```

## Output (LeadBrief, abridged)

- **Mode:** `offline_rules` · model: deterministic-rules (TF-IDF/LogReg + templates) · latency: 3057 ms · tokens in/out: 0/0 · prompt vv3
- **Intent:** new_project
- **Goal:** SEO karte ho?
- **Industry:** — · **budget:** — · **timeline:** —
- **Services:** Digital Marketing & Technical SEO (primary, conf 0.95)
- **Complexity:** S · effort 2–4 weeks · confidence low · needs_human_review=True
- **Why:** 1 service line(s) requested; band from train-calibrated model (see docs)
- **Risks:** —
- **Top questions:** (must_ask) What budget range has been approved or is being planned for this engagement? | (must_ask) What is your target go-live date or hard deadline? | (must_ask) In one sentence, what should this solution do for your business once live?

## Annotation

EDGE CASE: 10-char input. The engine still routes to the right service line and the brief is honest about missing scope (low confidence, must-ask questions dominate). Expected behavior, not a failure.
