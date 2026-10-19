# 08 — Rollout Roadmap: 30 / 60 / 90 days (bonus)

Pilot-to-production plan for the Discovery Copilot with success gates.
Owners are roles. Effort assumes one engineer plus part-time BD/founder.

## Phase 0 — this submission (done)

- POC + reports + offline-capable demo + eval harness on synthetic data.
- Gate to start Phase 1: reviewer sign-off that the brief format matches how
  Cynbit actually qualifies leads (adjust fields accordingly).

## Days 1–30 — Shadow mode

| Step | Owner | Output |
|---|---|---|
| Instrument the real contact form + opportunities@ inbox (masked logging) | Engineer | 100+ real inquiries captured consentfully |
| Run the copilot in parallel (never user-facing) | Engineer | Side-by-side briefs |
| BD rates every generated brief (services, complexity, questions) | BD | 100 labeled real examples |
| Re-run eval harness on the real labeled sample | Engineer | Real-data metrics vs synthetic metrics |
| Privacy review: PII masking, retention, consent language | Founder | Signed-off data note (DPDP-aligned posture) |

**Gate 1 (exit criteria):** ≥ 80% routing agreement with BD on real inquiries;
≥ 60% of clarifying questions rated "ask-worthy"; zero PII incidents.
If missed → tune on real data, extend 2 weeks, re-gate once.

## Days 31–60 — Assist mode

| Step | Owner | Output |
|---|---|---|
| Brief-first workflow: BD opens the brief before reading raw email | BD + Engineer | Adoption ≥ 80% of inbound |
| Feedback loop (thumbs + corrections) wired to a server-side store | Engineer | Weekly label stream |
| Retrain offline classifier on real labels; refresh few-shot set | Engineer | Offline engine v2 |
| Live GLM key as platform secret + monitoring (fallback rate, latency, injection rate) | Engineer | Dashboard + alerts |
| Polish suggested_response templates for out-of-scope (careers, partnerships) | BD | Standard redirects |

**Gate 2:** first-response time < 5 minutes for auto-acknowledgment path;
qualification time per lead < 5 minutes of senior time; fallback rate < 20%.

## Days 61–90 — Integrated mode

| Step | Owner | Output |
|---|---|---|
| Form + email ingestion via queue (Redis) with worker | Engineer | End-to-end automation of steps 1–2 |
| Review UI (or CRM embed) with approve/edit/dismiss | Engineer | Human-in-the-loop contract |
| Proposal skeleton generator from approved briefs (opportunity A2) | Engineer | Proposal draft in < 10 min |
| Weekly eval re-run + drift report | Engineer | Reliability track record |
| Decide: extend to Revio triage / AI-readiness audit surfaces | Founder | Phase-4 scope |

**Gate 3 (production):** 30 consecutive days with zero PII/incident reports,
≥ 90% schema-valid briefs, measured senior-time-per-lead reduction ≥ 50%,
and BD satisfaction ≥ 4/5. Only then does any output become customer-visible
(still human-approved).

## Success metrics recap

| KPI | Baseline (unknown/measured in shadow) | 90-day target |
|---|---|---|
| First-response time | measure day 1–30 | < 5 min |
| Senior time per qualification | measure day 1–30 | −50% vs shadow baseline |
| Routing agreement with BD | gate 1 ≥ 80% | ≥ 90% |
| Ask-worthy question rate | gate 1 ≥ 60% | ≥ 70% |
| PII / injection incidents | 0 tolerated | 0 |
