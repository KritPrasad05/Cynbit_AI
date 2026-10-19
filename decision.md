# decision.md — Decision Log

Every non-trivial decision taken during this challenge, logged as it was made
(not reconstructed at the end). Format per the challenge spec. Times are local
build-machine time (UTC+5:30 context, dates YYYY-MM-DD).

---

### D-001 : Repository location and git identity   [Phase 0]  [2026-10-19]
- Context: The build sandbox only guarantees write access under its project root; the deliverable is a git repo with clean history.
- Options considered: A) repo inside the sandbox project root (pros: writable, versionable; cons: none material), B) repo in `/tmp` (pros: none; cons: wiped on restart, violates sandbox conventions).
- Decision: A — repo lives at the sandbox project root; pushed to GitHub as `cynbit-ai-opportunity` by the candidate (see DEPLOY_STEPS.md).
- Reason: Durability and the sandbox file-path convention; git identity set to a neutral `AI/ML Intern Candidate <candidate@cynbit-challenge.local>` so no personal data is embedded without consent.
- Trade-off accepted: Git author email is a placeholder, not the candidate's real address.
- Revisit if: The candidate pushes to GitHub and wants their own identity — run `git config user.email` + `git commit --amend` is NOT recommended after push; instead set identity before pushing.

### D-002 : Environment facts recorded   [Phase 0]  [2026-10-19]
- Context: Phase 0 requires an environment check before building.
- Options considered: n/a (fact-finding).
- Decision: Facts recorded: Python 3.12.15, git 2.47.3, node v24.21.0; outbound HTTPS works directly from Python (cynbit.in reachable, HTTP 200); `open.bigmodel.cn` and `api.z.ai` both reachable and both return OpenAI-style 401 errors on `/api/paas/v4/chat/completions` without a key — i.e. both OpenAI-compatible endpoints are live.
- Reason: These facts determine that real scraping is possible (no pre-seeded fallback needed) and that the live provider can be built and probed, just not fully exercised without a key.
- Trade-off accepted: None.
- Revisit if: Sandbox network policy changes.

### D-003 : No GLM API key in environment — build dual-mode anyway   [Phase 0]  [2026-10-19]
- Context: No `GLM_API_KEY`/`ZHIPUAI_API_KEY` env var exists in the build sandbox. The challenge pre-authorizes this path: "If no key is available in the environment, build against the OpenAI-compatible interface anyway and test using Offline Mode."
- Options considered: A) Stop and request a key (violates "do not stop to ask questions"), B) Build the OpenAI-compatible GLM client untested + fully test Offline Mode, C) Use the build environment's own GLM gateway (z-ai-web-dev-sdk, serves GLM models) for the one-time generation of cached demo outputs and a live eval sample.
- Decision: B + C combined.
- Reason: B satisfies the spec exactly; C adds genuine value — the SDK served **glm-4-plus** responses during the build (see `data/README_data.md`), so `data/synthetic/cached_outputs.json` contains real live-model outputs for the built-in demo examples, and a live-vs-offline eval sample was runnable without fabricating anything.
- Trade-off accepted: The repo's live path (`app/core/llm_client.py`) could not be end-to-end tested against the *free-tier* model itself within the sandbox; it is exercised through an OpenAI-compatible interface and covered by fallback tests. This is disclosed in `report.md` § limitations.
- Revisit if: A key is provided — set `GLM_API_KEY` and the smoke test `tests/test_llm_client.py::test_live_glm_mode` (marked, skipped without key) will run.

### D-004 : GLM free-tier model and base URL   [Phase 0]  [2026-10-19]
- Context: The challenge forbids assuming `glm-4-flash` is current; docs must be checked.
- Options considered: A) `open.bigmodel.cn/api/paas/v4` with `glm-4-flash` (CN platform; announced free in Aug 2024, still listed; supports Function Call / JSON outputs, 26 languages incl. Hindi-adjacent code-mix handling), B) `api.z.ai/api/paas/v4` with `glm-4.5-flash` / `glm-4.7-flash` (international platform; Z.ai pricing page lists Flash at $0; LiteLLM documents `zai/glm-4.5-flash` as FREE tier; third-party trackers estimate ~1 req/s and ~1,000 req/day caps — unpublished, unconfirmed), C) newer `GLM-5.3-Flash` (announced Sep 2026, free-tier status less documented at build time), D) paid GLM models (violates $0 budget).
- Decision: Default `GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4`, `GLM_MODEL=glm-4-flash`, both overridable via env vars / UI field. Verification performed 2026-10-19: both endpoints answered an OpenAI-shaped auth error on `/api/paas/v4/chat/completions` (D-002); free-tier status cross-checked via Zhipu announcement (aibase.com/news/11323), Z.ai model-API pricing pages, and LiteLLM provider docs (full citations in the Opportunity Report §9).
- Reason: `glm-4-flash` on the CN platform is the longest-standing documented no-cost entry point with published JSON/function-call support; because both platforms expose the identical OpenAI-compatible `/api/paas/v4` path, a reviewer with an international key switches to `https://api.z.ai/api/paas/v4` + `glm-4.5-flash` by changing two env vars, zero code change.
- Trade-off accepted: Free-tier rate limits (esp. unpublished caps on api.z.ai) apply in live mode; the app auto-falls-back to Offline Mode on missing key, auth failure, or repeated 429s.
- Revisit if: Zhipu/Z.ai renames or sunsets the free tier — change two env vars, no code change.

### D-005 : Dependency choices and pins   [Phase 0]  [2026-10-19]
- Context: App must run on Hugging Face Spaces (Streamlit SDK) and in CI with `pip install -r requirements.txt`.
- Options considered: A) minimal deps (streamlit, pydantic, httpx) with hand-rolled TF-IDF, B) streamlit + pydantic + scikit-learn + httpx, C) add `openai` SDK instead of raw httpx.
- Decision: B, plus `openai` SDK for the live client (C folded in): pinned in `requirements.txt` as streamlit==1.66.0, pydantic==2.12.5, scikit-learn==1.5.2, httpx==0.28.1, openai==3.35.1, pandas==2.2.3, matplotlib==3.9.2 (eval/plots only, still light for Spaces); dev extras (pytest, ruff) listed in a separate dev section comment.
- Reason: scikit-learn is the honest classical baseline AND the offline classifier engine — one dependency serves both, proving the architecture earns its complexity. `openai` SDK is the most robust OpenAI-compatible client (timeouts, retries) and reviewers expect it.
- Trade-off accepted: Heavier image than strictly minimal; acceptable for Spaces free CPU tier.
- Revisit if: Spaces free tier image size becomes a problem — drop matplotlib+pandas from runtime and pre-render all eval artifacts as markdown/JSON.

### D-006 : Opportunity selected — Discovery Copilot (inbound lead qualification & scoping)   [Phase 2]  [2026-10-19]
- Context: 13 opportunities scored across 4 buckets (full matrix: docs/bonus/07_Opportunity_Scoring_Matrix.md).
- Options considered: A) Discovery Copilot 4.80 (pros: maps to their step-1 process, compounding value; cons: inbound volume unknown), B) Revio review intelligence 4.65 (pros: best data availability; cons: crowded category, generic-sentiment trap, product launch status unclear), C) SEO/content engine 4.25 (pros: high feasibility; cons: table-stakes demo, subjective eval).
- Decision: A. B and C recorded as runner-ups with explicit flip conditions (Revio live with paying customers / inbound volume negligible).
- Reason: A automates Cynbit's own stated first lifecycle step, matches their marketed "agents that manage leads", attacks documented speed-to-lead economics (100x contact odds within 5 min, 78% first-responder wins — research notes M7), and is the optimal shape for a free-tier structured-output POC.
- Trade-off accepted: The pick rests on an unverifiable assumption (meaningful inbound volume); mitigated by a parameterized ROI model and outbound-research use case.
- Revisit if: Cynbit discloses referral-only demand or Revio customer traction.

### D-007 : Scoring weights follow the brief, ties broken by strategic fit   [Phase 2]  [2026-10-19]
- Context: Weights were fixed by the challenge (impact 30 / feasibility 25 / data 20 / demo 15 / fit 10).
- Options considered: A) use brief weights as-is, B) re-weight toward feasibility.
- Decision: A. One near-tie (4.80 vs 4.65) was broken by strategic fit and differentiation risk, documented in the matrix doc, not by silently changing weights.
- Reason: Reproducibility and honesty of the scoring process matter more to the reviewer than the specific winner.
- Trade-off accepted: None.
- Revisit if: n/a.

### D-008 : Data sourcing — synthetic only, grounded in public patterns   [Phase 4]  [2026-10-19]
- Context: The POC needs labeled inquiries; Cynbit's real inquiry logs are private and unavailable.
- Options considered: A) purely hand-written examples, B) template+slot generator with seeded RNG (deterministic), C) live-LLM generation of examples.
- Decision: B, with hand-written template bodies modeled on real public inquiry patterns (RFP-style requests, WhatsApp-style messages, LinkedIn intros) and hard-case pools (vague, Hinglish, out-of-scope, injection, very short, mixed-intent). Catalog grounding file is hand-curated from data/raw/, explicitly not synthetic.
- Reason: Determinism and reproducibility (seed 42) matter for eval credibility; templates give controlled label ground truth; C would contaminate eval with model-authored text (self-grading risk).
- Trade-off accepted: Linguistic diversity is narrower than real-world inquiries; disclosed in report.md limitations.
- Revisit if: real anonymized inquiry samples become available — regenerate labels collaboratively with BD.

### D-009 : Dataset size and composition   [Phase 4]  [2026-10-19]
- Context: Challenge requires ≥150 labeled examples with realistic diversity including hard cases.
- Options considered: 150 exactly vs 170 with wider hard-case coverage.
- Decision: 170 total (120 train / 50 eval) across all four service lines; hard cases ≈ 30% of eval (vague, Hinglish, out-of-scope, injection, very-short, mixed-intent multi-service).
- Reason: 50-example eval gives roughly ±14pp 95% CI on accuracy — acceptable for a POC; more hard cases in eval = more informative failure analysis.
- Trade-off accepted: Small eval means metrics are estimates, not guarantees; CI stated in eval results.
- Revisit if: extending to production — grow eval to ≥300.

### D-010 : Label schema   [Phase 4]  [2026-10-19]
- Context: Classification target design.
- Options considered: A) single primary service, B) multi-label services + exclusive out_of_scope + complexity S/M/L + intent, C) fine-grained 20-class taxonomy mirroring every sub-service.
- Decision: B. Multi-label matches reality ("site + SEO"), out_of_scope exclusive, complexity as 3 bands (a defensible target without historical cost data), intent coarse.
- Reason: Matches Cynbit's actual case-study taxonomy (Fact: software dev / cloud / digital marketing categories on their site) while staying learnable at N=170.
- Trade-off accepted: Complexity banding is coarser than hours-based estimation; extraction gold (budget/timeline/industry) normalized to categories, not raw strings, to keep exact-match meaningful.
- Revisit if: real pricing history enables continuous effort regression.

### D-011 : Eval split discipline   [Phase 4]  [2026-10-19]
- Context: Holdout must never leak into prompts/few-shot.
- Options considered: A) random 50-example holdout, B) stratified holdout guaranteeing hard cases, C) k-fold.
- Decision: B — data/synthetic/leads_eval.jsonl (50 examples, ~30% hard cases) generated once (seed 42) and frozen; few-shot examples in prompts are drawn only from leads_train.jsonl; the offline classifier trains only on the train split.
- Reason: Guarantees the eval measures generalization incl. adversarial inputs; frozen file prevents accidental re-splitting.
- Trade-off accepted: Single split, no variance estimate across folds; mitigated by reporting binomial CIs.
- Revisit if: dataset grows past ~500 — move to grouped k-fold by template family.
