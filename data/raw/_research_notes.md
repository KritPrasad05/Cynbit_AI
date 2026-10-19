# Research Notes — Cynbit Challenge (Phase 1)

Collected 2026-10-19. Every external claim below carries its source URL; company
statements are labeled **Claim** (their marketing) vs **Fact** (verified on their
public site on the date shown) vs **Inference** (author's reasoning).

## A. Cynbit site corpus (data/raw/)

20 public pages scraped successfully (HTTP 200) on 2026-10-19 — see `_manifest.json`
for the authoritative list. All pages resolved; none failed. Thin pages (under
~3.0k cleaned chars): `/team` (2.5k — role titles only, no named individuals),
`/diaries` (2.9k), `/terms` (2.7k), `/privacy` (2.7k). The team page shows a
"Board of Architects" (Founder & CEO, Co-Founder & CTO) without personal names —
**Inference**: a small leadership team, consistent with an early-stage services
firm where senior time is the scarcest resource.

Key extracted facts (all **Fact**, from data/raw/ on 2026-10-19):

- Positioning: "AI automation and software solutions company in Jaipur"; "autonomous
  AI agents, custom software development, and scalable business platforms".
- 6-step Architectural Lifecycle: Discovery & audit → Strategy & blueprinting →
  High-fidelity design → Technical implementation → Quality & integrity check →
  Deployment & evolution.
- Services (3 suites): AI automation (autonomous agents "manage leads and
  coordination", LLM automation of data entry/document handling, AI voice agents,
  AI stack integration); Custom IT services (full-stack web/mobile, backend,
  AWS/Azure cloud, legacy migration); Digital marketing (Google/Meta ads,
  technical SEO, CRM automation, funnel optimization).
- Products: Cynbit Studio (edtech "career intelligence", AI-evaluated coding
  missions, mock interviews, resume engine, job matcher); Revio ("AI-first
  reputation engine", cross-platform review sync, AI response engine, sentiment,
  crisis detection, multi-location); TenantEase (property/tenant management,
  rent tracking, automated reminders).
- BitElevate: training + certification, claims 1000+ certified architects.
- Manav Seva Trust partnership: IT teaching for rural areas and government schools.
- Case studies listed (12): WizHealth (AI diagnostic triage), Pragya Healths (IoT
  patient monitoring), Wild Basil (blockchain-lite food traceability), Sofiasa
  (legacy ERP modernization), EContentPrep (adaptive learning), Cloudy Tales
  (real-time collaboration), Urban Wardrobe (AR try-on), Evento (real-time
  ticketing), Marketing Addict (AI campaign optimization), EliteVogue (headless
  commerce), TrendMart (hyper-local SEO), CarePlus Health (cloud migration),
  GlobalPay (cross-border payments).
- Careers page lists open internships including **Business Development Intern**
  and "HR & Talent Acquisition Intern" — **Inference**: BD capacity is being
  actively recruited, supporting the hypothesis that inbound lead handling is a
  real pain point.
- Contact surfaces: "Start discovery" CTA (multiple), opportunities@cynbit.in,
  3 phone numbers, HQ 32/115 Pratap Nagar, Jaipur 302033.
- Blog (12 posts across 2 index pages): includes "How AI Agents Are Transforming
  Business Operations in 2026" (published 2025-10-13, scraped in full), "Best CRM
  Automation Strategies…", "How Small Businesses Can Automate Operations Using
  AI", "How AI is Revolutionizing Digital Marketing in 2026", etc.
- Marketing metrics on site (**Claim**, unverified): 98% retention, 3x ROI
  uplift, 25k+ newsletter subscribers, 50k+ users handled, 99.9% uptime,
  1000+ certified, "+40% organic leads" (Marketing Addict testimonial),
  "99.99% uptime / +140% growth" (case-studies page).

## B. Market context (external sources)

| # | Statement | Value | Source (accessed 2026-10-19) |
|---|-----------|-------|------------------------------|
| M1 | SMB generative-AI use (operational range) | 55–58% (up from 40% in 2024) | presenc.ai/research/smb-ai-adoption-statistics-2026 (May 2026), citing US Chamber of Commerce / Thryv |
| M2 | Growing vs declining SMBs using AI | 83% vs 55% | presenc.ai (May 2026) |
| M3 | OECD firm-level AI adoption | 8.7% (2023) → 20.2% (2025) | omago.ai/blog/sme-ai-adoption-2026-data citing OECD; oecd.org SME AI adoption brief (Dec 2025) |
| M4 | Traditional vs AI lead-scoring accuracy | 15–25% → 40–60% | warmly.ai/p/blog/ai-lead-scoring (Mar 2026) |
| M5 | ML lead scoring vs traditional conversion | +75% higher conversion | landbase.com/blog/lead-scoring-statistics (Jan 2026) |
| M6 | AI lead-gen: qualified leads within 6 months | +73% | thestarrconspiracy.com AI lead-gen benchmarks (Sep 2026) |
| M7 | 5-minute rule: contact odds vs 30-min delay | 100x; 21x qualification; 78% buy from first responder; avg B2B response 47h | MIT/InsideSales (Oldroyd) Lead Response Management Study; HBR "The Short Life of Online Sales Leads" (2011); Drift/InsideSales — compiled at caseyresponse.com/blog/lead-response-time-statistics (2026) |
| M8 | Review/feedback management software market | $16.73B (2025) → $19.56B (2026) | thebusinessresearchcompany.com report summary |
| M9 | Online reputation management market | $6.88B (2025) → $7.75B (2026) | mordorintelligence.com (Jan 2026) |
| M10 | India proptech market | $1.31B (2025) → $1.47B (2026), 12.26% CAGR to $3.82B by 2034 | imarcgroup.com/india-proptech-market (Sep 2026); Grand View: $1.56B (2025) |
| M11 | India edtech market | $12.1B (2025) → $50B (2035), 15.24% CAGR | marketresearchfuture.com India edtech report (Sep 2026) |
| M12 | Global edtech market | $279.8B (2025) → $320.7B (2026), 11.39% CAGR | imarcgroup.com/edtech-market (Oct 2026) |
| M13 | India MSME AI adoption (manufacturing) | ~15% | D&B "Business Enterprises of Tomorrow" MSME report (via public summaries) |
| M14 | GLM free tier | glm-4-flash free on open.bigmodel.cn (announced Aug 2024, still listed); GLM-4.5-Flash $0 on api.z.ai; LiteLLM documents zai/glm-4.5-flash FREE | aibase.com/news/11323; z.ai pricing pages; docs.litellm.ai/docs/providers/zai |

Caveats recorded honestly: market-size figures differ across research vendors
(e.g., proptech India $1.3B–$2.9B depending on scope); the MIT/HBR 5-minute-rule
studies date from 2007–2011 and are repeatedly cited but hard to reproduce; SMB
AI-adoption figures vary by measurement frame (8.8%–76%) — we quote the
conservative operational range 55–58% and label vendor-published benchmarks as
vendor-reported.

## C. Reading notes for opportunity framing

1. Cynbit's own services page says their autonomous agents "manage leads and
   coordination" — a lead-qualification copilot is consistent with what they
   already sell, not a new departure. (Fact + Inference)
2. Their blog actively markets CRM automation and AI-agent content, but the
   public site shows no productized version of it — the gap between what they
   preach and what they productize is the opportunity. (Inference)
3. The 6-step lifecycle starts with "Discovery & audit" — the POC can compress
   step 1 for inbound inquiries. (Fact + Inference)
4. All case studies are tagged Software Dev / Cloud / Digital Marketing — the
   service-classification taxonomy for the POC should mirror these real
   categories. (Fact)
