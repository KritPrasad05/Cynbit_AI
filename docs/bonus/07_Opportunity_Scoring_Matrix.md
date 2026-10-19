# 07 — Opportunity Scoring Matrix

Phase 2 deliverable. Long list of 13 AI/ML opportunities for Cynbit, grouped by
bucket, scored 1–5 per criterion and weighted. Scores are the author's calibrated
judgment (labeled **Inference** throughout), grounded in the scraped site corpus
(`data/raw/`) and the market sources in `data/raw/_research_notes.md`.

**Weights** (fixed by the challenge brief):
Business impact 30% · Feasibility on free-tier GLM with no private data 25% ·
Data availability (public or synthesizable) 20% · Demo-ability under 2 minutes
15% · Strategic fit with Cynbit's stated positioning 10%.

Scoring anchors: 5 = clearly excellent, 3 = average/uncertain, 1 = clearly poor.
Effort to build a credible POC: S (< 1 dev-week), M (1–3 dev-weeks), L (> 3 dev-weeks).

## A. Full matrix

| # | Opportunity | Bucket | Problem it solves | AI/ML approach | Data needed | Impact | Feas. | Data | Demo | Fit | **Weighted** | Effort |
|---|-------------|--------|-------------------|----------------|-------------|--------|-------|------|------|------|-----------|--------|
| 1 | **Discovery Copilot — inbound lead qualification & scoping** | Internal | Free-text inquiries arrive via form/email/WhatsApp; slow, inconsistent triage burns senior time | Pipeline: sanitize → classify service fit → extract structured brief → ground on service catalog → estimate complexity → draft clarifying questions | Synthetic inquiries + public site catalog | 5 | 5 | 4 | 5 | 5 | **4.80** | M |
| 2 | Revio review intelligence | Product | Review volumes exceed manual reading; replies are slow/uneven | Theme clustering, sentiment, escalation detection, grounded reply drafting | Public review datasets (Yelp/Amazon/Google) | 5 | 4 | 5 | 5 | 4 | **4.65** | M |
| 3 | SEO/content engine | Internal | Content and technical-SEO delivery is labor-heavy | Brief generation, cluster planning, content QA against SERP intent | Public SERPs + their blog | 4 | 5 | 4 | 4 | 4 | **4.25** | M |
| 4 | Cynbit Studio resume-to-role matching | Product | Learners can't map skills to job market | JD parsing, skill-gap extraction, evidence-grounded guidance | Public job descriptions | 4 | 4 | 4 | 4 | 4 | **4.10** | M |
| 5 | Proposal & case-study generator | Internal | Proposals take days; case studies never get written | Structured extraction from briefs + retrieval over past work | Synthetic briefs + public case studies | 4 | 5 | 3 | 4 | 4 | **4.05** | M |
| 6 | TenantEase maintenance-ticket triage | Product | Landlords/tenant managers drown in chat messages | Intent + urgency classification, routing, lease Q&A | Synthetic tickets | 4 | 4 | 4 | 4 | 3 | **3.90** | M |
| 7 | Productized "AI readiness audit" (lead magnet) | New | SMBs want AI but don't know where to start; converts Cynbit's own funnel | Guided assessment → scored report → matched service pitch | Public SMB frameworks | 4 | 4 | 3 | 4 | 5 | **3.90** | S |
| 8 | AI voice intake agent | New | Phone inquiries missed outside hours; they already market "AI voice agents" | STT → same pipeline as #1 → TTS reply draft | Synthetic call transcripts | 4 | 3 | 3 | 3 | 5 | **3.50** | L |
| 9 | Internal delivery KB assistant | Internal | Tribal knowledge locked in chats | RAG over internal docs | **Private data — unavailable** | 3 | 4 | 2 | 3 | 3 | **3.25** | M |
| 10 | BitElevate learning-path recommender | Product | Paths are generic; drop-off risk | Sequence recommendation + project feedback rubric | Synthetic learner journeys | 3 | 4 | 3 | 3 | 3 | **3.25** | M |
| 11 | Client onboarding status summarizer | Customer | Clients ask "where are we?" | Summarize project state from updates | Private data — unavailable | 3 | 4 | 2 | 3 | 3 | **3.05** | M |
| 12 | Delivery-risk early-warning | Internal | Overruns detected late | Trend/classification on project telemetry | Private data — unavailable | 4 | 3 | 2 | 3 | 4 | **3.20** | L |
| 13 | Newsletter growth engine | Internal | 25k+ subscribers (Claim) under-monetized | Topic modeling, personalization, subject-line testing | Their public blog | 3 | 4 | 3 | 2 | 3 | **3.10** | M |

Weighted score = 0.30·Impact + 0.25·Feasibility + 0.20·Data + 0.15·Demo + 0.10·Fit.

## B. Ranking and decision

| Rank | Opportunity | Weighted | Verdict |
|------|-------------|----------|---------|
| 1 | Discovery Copilot (lead qualification & scoping) | **4.80** | **SELECTED** |
| 2 | Revio review intelligence | 4.65 | Runner-up |
| 3 | SEO/content engine | 4.25 | Runner-up |

**Selected: #1, the Discovery Copilot.** Reasoning (all **Inference** unless
labeled):

1. It automates Cynbit's own stated first process step — "Discovery & audit"
   (Fact: data/raw/home.md) — so the value story needs no mental translation for
   a Cynbit reviewer.
2. Their services page already promises autonomous agents that "manage leads and
   coordination" (Fact: data/raw/services.md) and their blog sells CRM automation
   (Fact: data/raw/blog_best-crm-automation-strategies.md), yet nothing on the
   site productizes intake. The gap between preached and shipped is the wedge.
3. Speed-to-lead economics are severe: 100x contact odds responding within 5
   minutes vs 30; 78% of buyers pick the first responder; average B2B response
   is 47 hours (source M7, research notes). An instant structured brief directly
   attacks this.
4. It compounds: the structured brief is reusable downstream (proposal
   generation #5, AI-readiness audit #7, even Revio/TenantEase demo prep),
   making it the highest-leverage single build.
5. Feasibility is a perfect 5 for this challenge: text-in → structured-JSON-out
   is exactly what free-tier GLM + Pydantic does well, with zero private data
   required and a crisp 2-minute demo.

**Why the runner-ups lost:**

- *Revio review intelligence (4.65)*: strongest data story (public review
  datasets) and a real product. Loses on differentiation risk: review
  sentiment/reply drafting is the most crowded category in the market
  ($16.7B→$19.6B review software market, source M8) and a POC there reads as
  "generic sentiment analysis" — the same weak-signal trap as a site-Q&A chatbot.
  It also bets on a product Cynbit has announced but not evidenced as launched.
  Would win if: Cynbit confirms Revio is live with paying customers and mounting
  review volumes.
- *SEO/content engine (4.25)*: great feasibility, but the demo-able slice
  (brief/outline generation) is increasingly table-stakes (every CMS has an AI
  assistant), and quality evaluation is subjective without ranking data. Would
  win if: the challenge emphasized their digital-marketing revenue line over
  their AI positioning.

**What would flip the decision back:** evidence that Cynbit's inbound volume is
negligible (referral-only business) — then the ROI concentrates in Revio/Studio
product features instead; or a statement that Revio is in market with customers.

## C. Red-team pass on the pick (required by Phase 2)

- **Weakest assumption:** that inbound free-text volume is meaningful for
  Cynbit. Unknown — no public data. Mitigation: the copilot also standardizes
  *outbound* research (pasting a prospect's LinkedIn post or RFP) and its ROI
  model (bonus doc 04) is parameterized from 50 to 2,000 inquiries/month so the
  reviewer can plug in reality.
- **Skeptical CTO objection 1:** "Your effort estimates have no historical
  grounding — a junior could misprice a project and we'd eat the loss."
  Response: outputs are ranges with confidence and a mandatory human-review
  flag; the POC UI hard-codes "draft, not a quote"; the eval measures estimate
  *banding* (S/M/L), not false-precision hours.
- **Skeptical CTO objection 2:** "A structured web form solves this without AI."
  Response: real inquiries arrive unstructured regardless (email, LinkedIn,
  WhatsApp screenshots, referrals), and forcing structure on the prospect
  reduces response. The value is the reasoning layer (scoping, risks, questions),
  not field parsing — the ablation in `evals/` quantifies exactly that gap
  versus a rules baseline.
- **Production killers:** prompt injection embedded in lead text; PII leakage
  into logs; hallucinated service claims to prospects. Mitigations built into
  the POC: input sanitizer + injection eval set + PII masking + grounding
  restricted to the curated service catalog + never-auto-send posture.
- **Honest cap:** without Cynbit's real inquiry logs, headline accuracy numbers
  are measured on synthetic data and must be re-validated on a real sample
  before any production claim.
