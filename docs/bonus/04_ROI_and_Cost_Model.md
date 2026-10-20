# 04 — ROI and Cost Model (bonus)

Transparent model with stated assumptions. **All inputs are assumptions** —
none of Cynbit's internal numbers are public. Ranges, not point estimates.
Currency: INR. Built 2026-10-19.

## 1. Cost side (what the copilot costs)

**Infrastructure (free tier):**

| Item | Choice | Cost |
|---|---|---|
| LLM inference | Groq free tier (openai/gpt-oss-120b default; gpt-oss-20b fast path) | ₹0 within rate limits (30 RPM, 1K req/day, 8K tokens/min per model) |
| Hosting | local run (default) or Streamlit Community Cloud free tier | ₹0 |
| Repo/CI | GitHub + Actions free tier | ₹0 |
| Measured usage | ~2.8k tokens per inquiry, p50 ~9 s (build gateway; `evals/results/cost_latency.json`) | — |

**Monthly projections (assumption: 60% of volume hits live mode, 40% served by cache/offline):**

| Inquiries/month | Live LLM calls | Tokens/month | Cost at free tier | Cost if paid flash tier (~$0.06/M in, ~$0.22/M out) |
|---|---|---|---|---|
| 100 | ~120 | ~0.17 M | ₹0 | < ₹1 |
| 1,000 | ~1,200 | ~1.7 M | ₹0 | ~₹20–30 |
| 10,000 | ~12,000 | ~17 M | ₹0 (needs queueing around rate caps) | ~₹200–300 |

**Engineering time (the real cost):** POC-to-pilot ≈ 2 engineer-weeks (roadmap
phase 1, doc 08); ongoing ≈ 2–4 h/month monitoring + prompt maintenance.

## 2. Value side (what it returns)

Assumption anchors (external, cited in the Opportunity Report §9): responding
within 5 minutes makes contact ~100x more likely vs 30 minutes, and 78% of
buyers choose the first responder (MIT/HBR lead-response research — dated
2007–2011, directional). AI lead-gen benchmarks report +73% qualified leads
within six months (vendor-reported).

**Scenario model** (assumption: average deal value ₹1.5–4 lakh for a services
firm of this profile; inquiry→qualified conversion 15–25%; qualified→close
20–35% — all adjustable):

| Scenario | Inquiries/mo | Lift assumptions | Senior time saved | Incremental revenue effect |
|---|---|---|---|---|
| Conservative | 50 | first-response 24 h → 4 h; +0% extra leads | ~8 h/mo (15 min → 4 min × 50) | +0–1 deals/quarter (₹0–4 L) |
| Base | 200 | first-response → <5 min (auto-ack + brief); qualification consistency +10% | ~37 h/mo | +1–3 deals/quarter (₹1.5–12 L) |
| Aggressive | 1,000 | +15% inquiry→qualified (speed + quality); 30% of briefs convert to proposal 2 days faster | ~160 h/mo (≈1 FTE) | +5–15 deals/quarter (₹7.5–60 L) |

**Payback:** at base scenario, the 2 engineer-week pilot (~₹1.4–2.5 L loaded
cost, assumption) breaks even within one to two quarters if the incremental
close rate moves at all; the dominant term is senior-time recovery, which is
guaranteed-ish, not the revenue lift, which is not.

## 3. Sensitivity table (incremental deals per quarter, base scenario)

| Inquiry→qualified lift ↓ / deal value → | ₹1.5 L | ₹2.5 L | ₹4 L |
|---|---|---|---|
| +5% | 0.3 | 0.5 | 0.8 |
| +10% | 0.6 | 1.0 | 1.6 |
| +15% | 0.9 | 1.5 | 2.4 |

(200 inquiries/mo × 3 months × lift × 25% close-on-qualified, rounded.)

## 4. What would falsify this model

- Inbound volume < 20/month → time-saved term collapses; the tool becomes a proposal-writing aid instead.
- Cynbit's deals close through referrals with weeks-long cycles (speed-to-lead irrelevant) → the 5-minute lever is moot.
- Groq free tier caps bind at 1K requests/day per model (8K tokens/min) → developer-tier line at 10k inquiries is ~$0.57/mo on gpt-oss-120b (~₹50/mo — still marginal; gpt-oss-20b halves it).
