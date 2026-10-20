# Sample chat — Zero-downtime AWS migration

Source: precomputed **live LLM** run — HISTORICAL GLM provider, captured 2026-10-19 (see data/synthetic/cached_outputs.json meta: glm-4-plus via the build-gateway bridge; the live provider is now Groq, decision.md D-026).

## Input

```text
Hi Cynbit team,

We need to migrate our on-prem servers to AWS with zero downtime — about 15 services and two databases, currently falling over at peak load. Enterprise requirement, so compliance documentation matters. We'd like this within 2 months.

Could you share an approach and rough cost? Thanks!

Regards,
Vikram
PayNest Fintech
```

## Output (LeadBrief, abridged)

- **Mode:** `glm_live` (historical GLM run) · model: glm-4-plus (gateway-served) · latency: 10125 ms · tokens in/out: 2280/792 · prompt vv3
- **Intent:** new_project
- **Goal:** Migrate on-prem servers to AWS with zero downtime
- **Industry:** fintech · **budget:** — · **timeline:** within 2 months
- **Services:** Custom IT Services — Cloud & Infrastructure (primary, conf 0.95)
- **Complexity:** L · effort 10–24 weeks · confidence medium · needs_human_review=True
- **Why:** 1 service line(s) requested; complexity keywords: enterpris, zero[- ]downtime, compliance; band from train-calibrated model (see docs)
- **Risks:** [high] Unrealistic timeline for zero-downtime migration of 15 services and 2 databases in a fintech environment | [high] Missing compliance requirements specification for fintech industry | [medium] No budget information provided | [medium] Potential technical dependencies between services not identified
- **Top questions:** (must_ask) What specific compliance frameworks (PCI DSS, SOC 2, etc.) must be met post-migration? | (must_ask) What is the approximate budget range for this migration project? | (should_ask) What are the dependencies between the 15 services being migrated?

## Annotation

LIVE RUN WITH RISK FLAG: the aggressive 2-month timeline on an L-band migration triggers the high-severity timeline risk — the deterministic estimator and the LLM advisor agreeing is the system working as designed.
