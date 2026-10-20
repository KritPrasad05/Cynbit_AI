# report.md — Final Project Report

The honest retrospective of what was done. Distinct from
`docs/03_Technical_Approach_Report.md` (the formal engineering deliverable):
this document is about the run itself — what worked, what didn't, and what
every number actually rests on. Every number links to its source file.

## 1. Executive summary

I analyzed Cynbit Technologies from its public site and market data, scored
13 AI opportunities, and built the top-scoring one as a working POC: the
**Discovery Copilot**, a pipeline that turns a free-text inbound inquiry into
a grounded, schema-validated discovery brief (service fit with evidence,
scope extraction, complexity band, risks, clarifying questions, next steps
mapped to Cynbit's real 6-step lifecycle). It runs live on Groq's free tier
(`openai/gpt-oss-120b`, switched from GLM on user instruction after the
original build — decision.md D-026) and keyless in a real Offline Mode; it
was evaluated against two baselines and an ablation on a held-out synthetic
split; it runs as a local Streamlit app with CI. The submission is honest
about its weakest points: synthetic validation data, gateway-dependent
historical live numbers, and a coarse complexity band.

## 2. What was asked vs. what was delivered

| Requirement | Status | Where |
|---|---|---|
| Analyze Cynbit's site/services/public info | ✅ done | 20 pages scraped with provenance (`data/raw/`), research notes with cited sources |
| Identify AI/ML opportunities | ✅ done | 13 opportunities, 4 buckets, weighted matrix (`docs/bonus/07_...`) |
| Deliverable 1: AI Opportunity Report | ✅ done | `docs/01_AI_Opportunity_Report.md` (3,105 words; Fact/Claim/Inference labels; 14 source groups) |
| Deliverable 2: functional POC | ✅ done | `app/` — Streamlit demo, offline-first, 8 one-click cases incl. injection |
| Deliverable 3: Technical Approach Report | ✅ done | `docs/03_Technical_Approach_Report.md` |
| Clean git history | ✅ done | 25+ conventional commits, one logical change each |
| Public GitHub repo + live demo | ⚠️ prepared, not pushed | no credentials in build env — `DEPLOY_STEPS.md` has exact commands; README links are placeholders to fill after push |
| GLM free tier verified | ✅ done | both endpoints probed; free models documented with sources (decision.md D-004) |
| Offline Mode for keyless reviewers | ✅ done | deterministic engine + real cached live outputs; badge enforced |
| ≥150 labeled synthetic examples | ✅ done | 170 (120/50 split), hard cases, seed-42 reproducible (CI-checked) |
| Baseline + ablation in eval | ✅ done (one caveat) | 2 baselines full-split; no-grounding ablation complete; no-fewshot **blocked** by build-gateway rate limits (5 attempts) — re-run command documented |
| Failure analysis (5 worst) | ✅ done | `evals/results/failures.md` — 6 cases, root causes, pattern summary |
| Cost + latency projections | ✅ done | `evals/results/cost_latency.json` (100/1k/10k per month) |
| Bonus artifacts | ✅ done | ROI, ethics/DPDP, competitors, roadmap, demo script, 8 sample chats, notebook, eval dashboard page |

## 3. The chosen opportunity and why

**Discovery Copilot — inbound lead qualification & scoping** (matrix score
4.80/5.00, full reasoning in `docs/bonus/07_...` §B): it automates Cynbit's
own stated first process step; their services page already promises agents
that "manage leads and coordination" without productizing intake; the
speed-to-lead economics are severe and documented; and it is the ideal shape
for a free-tier structured-output POC. Runner-ups: Revio review intelligence
(4.65 — crowded category, launch status unclear) and the SEO content engine
(4.25 — table-stakes demo). Flip conditions for both are recorded.

## 4. Results

Headline (all from `evals/results/metrics_table.json`, held-out 50):

- **Service routing:** exact-set 0.36 (rules) → 0.56 (offline engine) →
  **0.74 live** (CI95 ≈ 0.60–0.85); macro-F1 0.75 → 0.74 → **0.88**.
  [`metrics_glm.json`]
- **Out-of-scope recall 1.00** everywhere — no fake service matches were
  invented for job applications, vendor pitches, or sponsorship requests.
- **Injection pass rate 1.00** (3/3 in the live run; all offline runs too):
  flagged, stayed on task, zero compliance markers in advice.
  [`per_example_glm*.jsonl`]
- **Extraction:** timeline F1 0.64 → 0.67 → **0.84 live** (LLM beats regex on
  messy phrasing); budget F1 peaked at **0.89 offline** vs 0.75 live — the
  LLM annotates quotes in ways the normalizer mismatches; hybrid merge is
  the obvious fix. [`metrics_*.json`]
- **Complexity:** 0.67 exact / **0.96 adjacent** — same in live and offline
  by design (shared deterministic estimator; `decision.md` D-013).
- **Ablation (no grounding, n=10 matched live rows):** classification
  identical to the final system (8/8 agreement) — grounding contributes
  evidence + source URLs on 100% of matches and calibrated confidence, not
  accuracy. [`summary.json` → ablation_notes]
- **Cost/latency:** ~2.7k tokens and p50 ≈ 8.7 s per live request; $0/month
  at free tier for 100–10k requests (with rate-limit caveats).
  [`cost_latency.json`]
- **Error analysis:** the 6 worst live outputs with root causes — dominant
  pattern is multi-label over-firing on associated-but-not-requested
  services; two "failures" are actually labeling ambiguity on vague inputs.
  [`failures.md`]

## 5. Live demo notes and how to run

- Local: `bash scripts/run_local.sh` (or `pip install -r requirements.txt
  && streamlit run app/streamlit_app.py`) — boots in Offline Mode, no `.env`,
  no key (re-verified after the Groq migration with a headless Streamlit
  AppTest: keyless boot, example replay, eval dashboard render).
- Tests: `pytest tests/` (52 tests, no network).
- Eval: `python evals/run_eval.py` (offline) / `--provider groq` (with a
  GROQ_API_KEY; the historical GLM artifacts stay in evals/results/ under
  their own tags).
- No cloud hosting by design (D-027): the demo is the local Streamlit app.
  If a public URL is needed, the same repo deploys to Streamlit Community
  Cloud (free) with `app/streamlit_app.py` as the main file and
  `GROQ_API_KEY` as a secret.

> **Post-completion changes (2026-10-20, user instruction):** the live LLM
> provider was switched from GLM to **Groq** (`openai/gpt-oss-120b`, verified
> current production model — the llama-3.x models are deprecated on Groq;
> see decision.md D-026), and the demo was switched from a Hugging Face
> Space to a **local Streamlit run** (decision.md D-027). Historical GLM
> eval numbers and cached demo outputs are kept with their provenance and
> marked HISTORICAL; both refresh with one command each using a Groq key.

## 6. What worked

1. **The two-call pipeline** (classify+extract; advise) with deterministic
   sanitize/ground/estimate around it — zero schema-exhaustion failures
   across every live run, and security/pricing decisions never depend on
   model compliance.
2. **Offline Mode as a first-class mode.** The exact-match cache of real GLM
   outputs + deterministic engine made the demo reviewable with zero keys and
   doubled as the deployment's no-secret default.
3. **The local OpenAI-compatible bridge** over the build environment's GLM
   gateway exercised the repo's real client end-to-end — the live path was
   genuinely tested, not just "built against the interface."
4. **Split discipline.** The eval split never touched prompts; CI re-checks
   data determinism; every metric has per-example audit files.
5. **Red-teaming my own pick early** (matrix §C) pre-answered the skeptical
   CTO questions and shaped the range-not-quote estimate design.

## 7. What didn't work, and the fixes tried

1. **Generator labeling bug (caught mid-build):** the dataset top-up loop
   labeled ~96 extra examples as `seo_marketing` (a string-vs-tuple membership
   test always failed). Symptom: classifier predicted SEO for everything.
   Fix: family-aware top-up + regenerated data + a distribution assertion in
   the build script output. Cost: one wasted calibration cycle.
2. **Prompt v2 injection handling:** live testing showed injection-bearing
   inquiries being marked out-of-scope with all fields dropped. Fix: prompt v3
   ("injection is a security signal, NOT an intent signal"); re-tested live,
   re-cached. Documented as D-015.
3. **Complexity rules (63% train):** hand-tuned keyword rules couldn't
   recover template-embedded complexity. Fix: classical TF-IDF+LogReg model
   trained on the train split, rules kept for the user-facing rationale.
4. **Background evals killed by the sandbox:** long-running background
   processes were reaped between tool calls. Fix: chunked foreground runs
   (`--start/--end`) + a merge script.
5. **Build-gateway rate limiting (the big one):** bursts of ~25–35 live calls
   trigger 10–15+ minute cooldowns. Fixes tried: pacing sleeps, in-run
   backoff retries, chunking, resumable cache generation. Outcome: full live
   eval (50/50, 94% live coverage) + no-grounding ablation completed; the
   no-fewshot ablation and LLM-judge sample stayed blocked after 5 attempts —
   honestly marked, with one-command re-runs documented.

## 8. Limitations and known issues

- Every headline number is on **synthetic** gold; nothing here is validated
  on real Cynbit inquiries (impossible in scope — and stated everywhere it
  matters).
- Live metrics reflect **glm-4-plus** through the build gateway, not the
  repo-default **glm-4-flash**; expect drift when re-run on the true free
  tier.
- 3/50 live examples fell back to the offline engine mid-run (rate limits) —
  they are included in metrics (deployed-system semantics) and flagged via
  `live_coverage: 0.94`.
- Budget extraction in live mode underperforms the regex baseline (0.75 vs
  0.89 F1) — known, root-caused, fix designed (hybrid merge), not yet built.
- Complexity banding is coarse by design; exact-band misses are mostly
  one-band (adjacent 0.96).
- The UI's eval dashboard reads files generated at build time; regenerate
  after any eval re-run.

## 9. Cost and latency findings

- Measured: ~2.7k tokens/request live (prompt+completion), p50 8.7 s, p95
  ~19 s through the build gateway (`cost_latency.json`).
- Projections: 100 → 10k requests/month ≈ 0.27M → 27M tokens; **$0** at
  free tier (rate-cap queuing needed at the top end; paid flash tiers would
  still be under ~$1–3/month). Offline Mode: 2 ms, zero cost, no network.
- Business-side ROI (assumption-based, parameterized 50–2,000
  inquiries/month): `docs/bonus/04_ROI_and_Cost_Model.md`.

## 10. What I would do with 2 more weeks and real Cynbit data

1. **Re-validate on 100 real inquiries in shadow mode** (roadmap gate 1) and
   publish the real-data metrics next to the synthetic ones.
2. **Hybrid extraction:** merge regex (figures) with LLM (presence/semantics)
   — directly attacks the budget-F1 gap.
3. **Per-label confidence gates** to kill the over-prediction failure family
   (E0050/E0025/E0013 in `failures.md`), plus contrastive few-shot pairs for
   "marketing site (build)" vs "marketing services (ads/SEO)".
4. **Second turn:** consume the answers to the clarifying questions and
   refine the estimate — the single highest-value feature add.
5. **Finish the blocked ablations** (no-fewshot, LLM-judge sample) with a
   real key, and add grouped k-fold once the dataset passes ~500 examples.
6. **Same pipeline, second surface:** Revio review-triage demo to show the
   engine generalizes across their product lines.

## 11. Appendix

- **File index:** see `flow.md` (requirement → file map) and the repo map in
  `README.md`.
- **Commit summary:** 25+ conventional commits (`git log --oneline`), from
  `chore: scaffold repository structure` through
  `docs: opportunity scoring and selection`, `feat(core): …`, `feat(app): …`,
  `test: …`, `eval: …`, `docs: …` — no fix-fix-fix chains, no giant initial
  commit.
- **Decision log:** `decision.md` (D-001…D-027 + open risks; D-026/D-027
  record the post-completion Groq + local-run switch).
