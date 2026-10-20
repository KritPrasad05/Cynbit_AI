# Sample chat — AI chatbot over company docs

Source: precomputed **live LLM** run — HISTORICAL GLM provider, captured 2026-10-19 (see data/synthetic/cached_outputs.json meta: glm-4-plus via the build-gateway bridge; the live provider is now Groq, decision.md D-026).

## Input

```text
Hi Cynbit team,

We are a 40-person insurance brokerage in Jaipur. Our support staff answers the same policy questions all day. We want a chatbot on our website that answers from our own policy documents, escalates to a human when unsure, and logs everything. Our budget is around Rs 4 lakh. We'd like this within 3 months.

Could you share an approach and rough cost? Thanks!

Regards,
Rohit
Brightlane Retail
```

## Output (LeadBrief, abridged)

- **Mode:** `glm_live` (historical GLM run) · model: glm-4-plus (gateway-served) · latency: 12530 ms · tokens in/out: 2285/754 · prompt vv3
- **Intent:** new_project
- **Goal:** Create a chatbot for insurance policy questions that can escalate to humans
- **Industry:** insurance · **budget:** around Rs 4 lakh · **timeline:** within 3 months
- **Services:** AI Automation Suite (secondary, conf 0.35)
- **Complexity:** M · effort 4–10 weeks · confidence high · needs_human_review=False
- **Why:** 1 service line(s) requested; scope drivers: escalat; band from train-calibrated model (see docs)
- **Risks:** [medium] Scope vagueness in policy document integration | [high] Unrealistic timeline for complex AI implementation | [medium] Insufficient budget for enterprise-grade insurance chatbot | [high] Compliance and security requirements not specified
- **Top questions:** (must_ask) What specific insurance policies need to be covered by the chatbot? | (must_ask) What existing systems does the chatbot need to integrate with (CRM, policy databases, etc.)? | (should_ask) What are the specific compliance and security requirements for handling customer insurance data?

## Annotation

STRAIGHTFORWARD LIVE RUN: two LLM calls; correct service (AI automation), budget and timeline extracted, questions are exactly what a solutions architect would ask first. Note evidence lines trace to the public catalog.
