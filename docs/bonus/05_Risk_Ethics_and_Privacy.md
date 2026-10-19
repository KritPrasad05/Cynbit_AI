# 05 — Risk, Ethics, and Privacy (bonus)

Built 2026-10-19. Scope: the Discovery Copilot POC and its production path.

## 1. Risk register

| # | Risk | Likelihood | Impact | Mitigation (in POC) | Production control |
|---|------|-----------|--------|---------------------|--------------------|
| R1 | Prompt injection via inquiry text | High (demonstrated in eval set) | Brief manipulation, fake commitments | Sanitizer screening + untrusted-data delimiters + injection risk flag; eval pass rate 1.00 | Injection-rate monitoring; reviewer warning banner |
| R2 | Hallucinated Cynbit facts to prospects | Medium | Trust damage | Grounding restricted to curated catalog; "missing info → clarifying question" rule; source URL shown per match | Catalog versioning + periodic re-scrape |
| R3 | Effort estimates trusted as quotes | Medium | Mispricing losses | Deterministic banding, range + confidence, hard "needs human review" flag, "draft not a quote" label | Approval workflow before anything client-facing |
| R4 | PII leakage into logs | Medium | Privacy/compliance | Email/phone masked before model call and before any write; feedback stores no raw text | Retention policy + access control on stores |
| R5 | Bias in service routing (industry/language skew) | Medium | Systematic misrouting | Hinglish + diverse industries in train/eval; per-class F1 reported | Per-segment metrics on real data; BD correction loop |
| R6 | Free-tier dependency (rate caps, model changes) | Medium | Demo/production outage | Offline Mode fallback with visible badge; env-overridable model/base URL | Queue + paid-tier fallback flag |
| R7 | Synthetic-data overfit claims | High | Credibility | Every metric labeled synthetic; real-data gate 1 in roadmap | Re-validation before any external claim |

## 2. Bias considerations

- The synthetic generator's templates encode the author's view of how
  inquiries look; dialect, formality, and channel mix are narrower than
  reality. Per-class F1 is published (`evals/results/metrics_*.json`) so
  skew is inspectable, and the 30-day shadow phase measures real
  distribution shift before anything ships.
- Hinglish is a first-class case (5 train + eval examples, language detection,
  bilingual-response advice). Other Indian languages are untested — disclosed
  as a limitation, not claimed.
- No demographic attributes are inferred; classification targets are service
  lines only.

## 3. Hallucination posture

The system design separates "what Cynbit does" (only from the retrieved
catalog, with source URLs) from "what the inquirer said" (extraction with
null when unstated) from "what we advise" (risks/questions/next steps —
recommendations, always human-reviewed). The eval checks that no injected
instruction is complied with (pass rate 1.00 across runs) and the failure
analysis documents where extraction still misses.

## 4. Data protection (India DPDP Act — high-level posture)

- **Data minimization:** the POC processes only the inquiry text the user
  submitted to Cynbit's public channel; no additional lookups, no enrichment.
- **PII masking before processing:** emails/phones are masked prior to any
  model call or persistence (`sanitize()` runs first in every mode). Note:
  masking happens at the API boundary — production should also bind
  retention/erasure workflows to the masked identifier.
- **Purpose limitation:** data is used to answer the inquirer, nothing else;
  the feedback store records mode/metrics/thumbs, not raw text.
- **Consent/transparency:** production auto-acknowledgments should state that
  an AI assistant drafted the structured summary (the POC demo shows the
  badge to Cynbit's own team; the same honesty must extend to prospects).
- **Storage/transfer:** free-tier LLM endpoints are outside India; a DPDP
  review of cross-border transfer terms is a Phase-1 checklist item, not an
  afterthought. If unacceptable, the offline engine (fully local) is the
  fallback for sensitive inquiries — an unusual architectural dividend of
  Offline Mode.
- This section is a posture summary, not legal advice.

## 5. Human oversight

- Every output is a draft; the UI contract hard-codes "needs human review"
  flags and confidence levels.
- Nothing is auto-sent in the POC. Production Gate 3 explicitly requires 30
  incident-free days before any customer-visible output, still
  human-approved.
- The feedback thumbs (up/down per brief) give BD a one-click correction
  channel feeding the weekly eval re-run.
