# Sample chat — Hinglish restaurant inquiry

Source: precomputed **live LLM** run — HISTORICAL GLM provider, captured 2026-10-19 (see data/synthetic/cached_outputs.json meta: glm-4-plus via the build-gateway bridge; the live provider is now Groq, decision.md D-026).

## Input

```text
Namaste, humein apne restaurant ke liye online ordering system chahiye. Budget thoda tight hai but quality kaam chahiye. Kitna time lagega?
```

## Output (LeadBrief, abridged)

- **Mode:** `glm_live` (historical GLM run) · model: glm-4-plus (gateway-served) · latency: 8243 ms · tokens in/out: 2204/686 · prompt vv3
- **Intent:** new_project
- **Goal:** Online ordering system for a restaurant
- **Industry:** food · **budget:** budget thoda tight hai (tight budget, no figure) · **timeline:** —
- **Services:** Custom IT Services — Software Development (secondary, conf 0.35)
- **Complexity:** S · effort 2–4 weeks · confidence medium · needs_human_review=True
- **Why:** 1 service line(s) requested; band from train-calibrated model (see docs)
- **Risks:** [medium] Scope vagueness - 'online ordering system' could mean anything from a simple menu display to a full restaurant management platform | [high] Budget constraints may limit functionality or quality | [medium] Missing timeline information makes planning difficult | [medium] No integration requirements mentioned (POS, inventory, payment gateways)
- **Top questions:** (must_ask) What specific features are required in the online ordering system? | (must_ask) What is your approximate budget range? | (should_ask) What is your target launch timeline?

## Annotation

LIVE RUN, HINGLISH: language detected as hinglish; extraction still lands (goal + tight-budget signal). The advisor recommends bilingual follow-up — a small detail that matters for the Indian SMB market.
