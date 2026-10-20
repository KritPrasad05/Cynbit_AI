# decision.md — Decision Log

Every non-trivial decision taken during this challenge, logged as it was made
(not reconstructed at the end). Format per the challenge spec. Times are local
build-machine time (UTC+5:30 context, dates YYYY-MM-DD).

---

### D-001 : Repository location and git identity   [Phase 0]  [2026-10-19]
- Context: The build sandbox only guarantees write access under its project root; the deliverable is a git repo with clean history.
- Options considered: A) repo inside the sandbox project root (pros: writable, versionable; cons: none material), B) repo in `/tmp` (pros: none; cons: wiped on restart, violates sandbox conventions).
- Decision: A — repo lives at the sandbox project root; pushed to GitHub as `cynbit-ai-opportunity` by the candidate (push commands: README + `git remote add origin …`).
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

### D-012 : Architecture — six-step pipeline, two LLM calls, deterministic estimate   [Phase 5]  [2026-10-19]
- Context: Challenge rule 6.1 requires a pipeline, not a mega-prompt.
- Options considered: A) single mega-prompt producing the whole brief, B) five micro-calls (one per field), C) two structured calls (classify+extract; advise) with pure-Python sanitize/ground/estimate steps around them.
- Decision: C, realized in app/core/pipeline.py.
- Reason: Sanitization and grounding must be deterministic for security/verifiability; estimation must never be LLM-invented (pricing risk); two calls keep live latency ~6–15s and tokens ~3k/example instead of ~3x that with retries on one big JSON. Each step is unit-tested.
- Trade-off accepted: Two round-trips add latency vs a mega-prompt; acceptable for a triage tool, and identical requests are cached.
- Revisit if: GLM supports parallel tool calls cheaply — could overlap calls.

### D-013 : Complexity estimator — train-calibrated classical model, rules provide rationale   [Phase 5]  [2026-10-19]
- Context: Initial pure-keyword rules hit only 63% on TRAIN (template-embedded complexity is subtle).
- Options considered: A) keep tuning rules by hand, B) LLM estimates (rejected: estimates must be deterministic and never hallucinated), C) char n-gram TF-IDF + logistic regression trained on the TRAIN split, with keyword rules retained for the user-facing rationale.
- Decision: C (app/core/offline.py ComplexityModel; pipeline.estimate_complexity). Same estimator object used in live and offline modes.
- Reason: Deterministic, no LLM, in-sample 100% / held-out 60% exact + 86% adjacent — honest numbers reported with the caveat that gold bands are template-derived.
- Trade-off accepted: The band is less interpretable than pure rules; mitigated by showing keyword-rule rationale strings in the UI.
- Revisit if: real historical project data arrives — replace with effort regression on real features.

### D-014 : Offline Mode design — exact-match cache + deterministic engine   [Phase 5]  [2026-10-19]
- Context: Challenge 6.4 mandates a useful keyless demo.
- Options considered: A) stub returning "add a key", B) rules-only, C) precomputed live-GLM outputs for built-in examples + deterministic engine for arbitrary input.
- Decision: C. data/synthetic/cached_outputs.json (8 examples, generated via live GLM through the repo's own GLMClient — build-time provenance in the file's meta) + TF-IDF/LogReg classifier + regex extraction + template advice. UI shows an unmissable OFFLINE badge distinguishing offline_cached vs offline_rules.
- Reason: Reviewer clicks an example → sees REAL model output with zero keys; arbitrary inputs still get useful deterministic output; nothing is misrepresented as live inference.
- Trade-off accepted: Cached outputs are frozen to prompt v3; regenerating requires a key (scripts/gen_cache.py).
- Revisit if: prompts change — regenerate cache in the same commit.

### D-015 : Prompt v2 → v3 — injection cases must still be analyzed   [Phase 5]  [2026-10-19]
- Context: Live testing of v2 showed the model marking injection-bearing inquiries out_of_scope and dropping the underlying request (services=[], no estimate) — a weak security story and a classification failure.
- Options considered: A) accept and document, B) clarify in the system prompt that injection is a security signal, never an intent signal, C) hard-filter injection text before the model.
- Decision: B (prompts.py v3). Re-tested live: injection example now classifies software_dev with the injection surfaced as a sanitizer flag + risk.
- Reason: Smallest change that fixes observed behavior; C would hide the security signal the eval needs to measure.
- Trade-off accepted: Prompt-version bump invalidates earlier cached outputs — cache regenerated in the same session.
- Revisit if: future live testing regresses.

### D-016 : Build-time GLM access — local OpenAI-compatible bridge over the sandbox GLM gateway   [Phase 5]  [2026-10-19]
- Context: No GLM_API_KEY in the build sandbox, but the sandbox exposes a GLM gateway via z-ai-web-dev-sdk (Node; served model glm-4-plus). The repo's live path is Python/openai-SDK.
- Options considered: A) leave live path untested (challenge allows offline testing), B) reimplement pipeline calls in Node for cache generation (duplication, prompts drift), C) run a localhost OpenAI-compatible proxy (scripts/glm_proxy.mjs, sandbox-only, NOT in the repo) in front of the gateway and point GLMClient at it.
- Decision: C. Consequences honestly recorded: live-path tests + cached outputs + live evals all ran through this bridge; the bridge serves glm-4-plus (gateway ignores the model param), NOT the free-tier glm-4-flash the repo defaults to. Latencies measured through the bridge include local HTTP overhead (negligible vs model time) and gateway queuing (material — see results README).
- Reason: Exercises the exact production code path end-to-end without duplicating logic; gateway 429 rate limits were handled with pacing and retries (observed: bursts of ~25–35 calls trigger ~10–15 min cooldowns).
- Trade-off accepted: Live numbers come from glm-4-plus, a stronger model than free-tier glm-4-flash; results are labeled accordingly and the reviewer can re-run with any key against the true free tier.
- Revisit if: A real key becomes available — re-run `evals/run_eval.py --provider glm` and `scripts/gen_cache.py`.

### D-017 : Evaluation design — stress-weighted holdout, task-appropriate metrics   [Phase 6]  [2026-10-19]
- Context: Mixed task (multi-label classification + extraction + generation advice) needs an eval that a reviewer can audit.
- Options considered: A) accuracy only, B) full multi-metric suite with per-example audit files, C) LLM-as-judge for everything.
- Decision: B (+ bounded C): exact-set accuracy with Wilson CI, macro-F1 per class, OOS recall/precision, complexity exact+adjacent, budget/timeline presence+value F1 with normalizers, injection pass-rate (flagged ∧ on-task ∧ no-compliance), schema validity, latency/tokens, live coverage. Judge limited to an optional 10-example question-usefulness sample (blocked by rate limits, documented).
- Reason: Every claim in the reports traces to a file; adversarial inputs get their own metric; the eval README defines everything.
- Trade-off accepted: 50 examples → wide CIs (±14pp); stated wherever quoted.
- Revisit if: dataset ≥ 300 — add grouped k-fold by template family.

### D-018 : Baselines — rules-only and the offline engine   [Phase 6]  [2026-10-19]
- Options considered: A) majority class, B) keyword/TF-IDF-similarity rules, C) TF-IDF+LogReg (the offline engine), D) no-grounding LLM.
- Decision: B (B0) and C (B1) as the two baselines; D as ablation. A rejected as uninformative (class balance too even).
- Reason: B0 shows what free rules buy (0.36 exact-set), B1 shows the classical ceiling (0.56), the live pipeline shows what GLM adds (0.74) — the reviewer sees each layer's marginal value.
- Trade-off accepted: B1 doubles as the offline engine (dual role) — disclosed to avoid double-counting novelty.
- Revisit if: a transformer fine-tune becomes feasible.

### D-019 : Ablations — grounding and few-shot; one blocked honestly   [Phase 6]  [2026-10-19]
- Context: Challenge requires ≥1 ablation; build-gateway rate limits constrained live budget.
- Options considered: A) skip ablations, B) no-grounding only, C) no-grounding + no-fewshot on subsamples.
- Decision: C attempted; no-grounding completed (n=10, matched live-only comparison — classification identical 8/8, evidence coverage 0%→100%); no-fewshot attempted 5× across spread-out windows, all blocked by gateway 429 cooldowns. Documented as blocked with the exact re-run command in evals/results/summary.json; NOT fabricated.
- Reason: An honest "blocked, here's the one-liner to finish it" beats a fabricated or silently missing ablation.
- Trade-off accepted: The few-shot contribution is argued (hard-case F1 deltas between offline/live) but not directly measured.
- Revisit if: any GLM key is available — run the documented command.

### D-020 : UI choices — cards over JSON, badges over silence, feedback loop   [Phase 5]  [2026-10-19]
- Context: The reviewer spends ~5 minutes; the challenge specifies card rendering, mode badge, latency/tokens, thumbs feedback, collapsible how-it-works.
- Options considered: raw JSON with copy button vs structured cards; single-page vs nav (demo + eval dashboard).
- Decision: Cards for every brief section (services with evidence + source URLs, complexity with rationale, prioritized questions, owner-tagged next steps), mode badge colored per provenance, latency/tokens/calls metrics row, thumbs→data/feedback.jsonl (gitignored), "How it works" expander with pipeline steps + prompt version, second page rendering evals/results.
- Reason: The demo must communicate the architecture's care in one glance; JSON stays available in a collapsed expander for engineers.
- Trade-off accepted: Slightly heavier UI file (~430 lines) — logic stays in core/ with zero Streamlit imports.
- Revisit if: multi-turn follow-ups arrive — needs a session model.

### D-021 : Hosting — Hugging Face Spaces (Streamlit SDK, CPU basic, offline-first)   [Phase 9]  [2026-10-19]  [SUPERSEDED by D-027, 2026-10-20]
- Options considered: A) HF Spaces, B) Render free tier (cold starts, sleeps), C) Streamlit Community Cloud (auth coupling), D) localhost-only.
- Decision: A per the challenge's fixed constraint; deploy packaged by scripts/deploy_hf.sh (Space README frontmatter with app_file: app/streamlit_app.py, pinned sdk_version 1.66.0); GLM key only as a Space secret; boots keyless.
- Reason: Fixed by the brief; also the best free fit (no cold-start sleep, public URL, secret management).
- Trade-off accepted: Space image includes pandas/matplotlib for the eval dashboard (~heavier build, still fine on free CPU).
- Revisit if: traffic or build size becomes an issue — split eval dashboard into a static page.

### D-022 : Repo structure follows the challenge spec, with two small extensions   [Phase 0→8]  [2026-10-19]
- Context: Spec's tree is mandatory; real build needed three extra pieces.
- Options considered: strict-only vs extensions.
- Decision: Extensions: (1) app/core/examples.py — the 8 demo inputs shared by UI and cache generation (spec's tree has no home for them); (2) evals/README.md + data/README_data.md as spec-implied provenance docs; (3) scripts/ gained merge_eval.py, make_charts.py, make_sample_chats.py, make_failures.py, gen_cache.py, calibrate_check.py for reproducible artifacts. All additive; no spec file omitted.
- Reason: Single source of truth for demo inputs; every artifact regenerable.
- Trade-off accepted: none material.
- Revisit if: n/a.

### D-023 : Scrapes — all 20 pages returned 200; nothing failed, nothing invented   [Phase 1]  [2026-10-19]
- Context: Spec requires recording failed/thin scrapes.
- Decision/record: all 20 targets returned HTTP 200 on 2026-10-19; thin pages (<3.0k cleaned chars) are /team (2.5k — role titles only), /diaries, /terms, /privacy; manifest at data/raw/_manifest.json records sizes. Dynamic widgets (forms, sliders) not captured — noted in every file's header.
- Trade-off accepted: team composition inferred from page structure, labeled Inference.
- Revisit if: site changes — re-run scripts/scrape.py.

### D-024 : Deviations from the challenge prompt (all minor, all disclosed)   [All]  [2026-10-19]
1. Cached outputs were generated through the build environment's GLM gateway (served glm-4-plus) rather than a personal free-tier key — no key existed in the environment; the challenge pre-authorized building against the interface with offline testing, and the gateway bridge tested MORE, not less (D-016).
2. The no-fewshot ablation and LLM-judge sample could not complete due to gateway rate limits — marked blocked with re-run commands (D-019); the required minimum (baseline + ablation) is satisfied.
3. eval_set.jsonl is a labeled pointer-copy of the frozen data/synthetic/leads_eval.jsonl (the spec named the file; the data lives under data/ with the rest of the dataset and its provenance).
4. Live eval ran in resumable chunks due to sandbox process reaping + rate limits; scripts/merge_eval.py recomputes all metrics under one consistent semantics.
5. Git identity is a placeholder (candidate@cynbit-challenge.local) — set your own (`git config user.name/user.email`) before pushing to GitHub.

### D-026 : Live LLM provider switched from GLM to Groq (user instruction)   [2026-10-20]
- Context: After the original build completed on GLM (Zhipu/Z.ai), the user asked to switch the code to the Groq API key. Both providers expose OpenAI-compatible chat/completions, so this was a configuration + verification change, not an architecture change — the provider abstraction (D-004) paid off exactly as designed.
- Options considered (verified against console.groq.com/docs/models, /docs/deprecations, /docs/rate-limits on 2026-10-20): A) `openai/gpt-oss-120b`; B) `openai/gpt-oss-20b`; C) `qwen/qwen3.8-27b` (rejected: preview tier, not production); D) `llama-3.1-8b-instant` / `llama-3.3-70b-versatile` (REJECTED: deprecated on Groq since 2026-08-16).
- Decision: `GroqClient` → `https://api.groq.com/openai/v1`, default model `openai/gpt-oss-120b` with `openai/gpt-oss-20b` selectable in the UI (fast path, 1000 t/s); env vars `GROQ_API_KEY` / `GROQ_BASE_URL` / `GROQ_MODEL`; JSON mode (`response_format: json_object`) requested whenever a schema is passed; `reasoning_effort=low` for gpt-oss models to keep the 2-call pipeline snappy; if the endpoint rejects an optional param (400), one plain retry without optional params; `LLM_PROVIDER=glm` accepted as a deprecated alias for `groq` (env + pipeline), so stale configs keep live behavior instead of silently degrading; legacy `glm_*` provenance literals retained in the schema so the precomputed cache (2026-10-19) still validates.
- Reason: gpt-oss-120b/20b are Groq's current production text models (131k context); free tier is 30 RPM / 1K RPD / 8K TPM / 200K TPD per model — enough for a demo, and the eval harness's new default `--sleep 20` respects the 8K TPM cap. Historical GLM eval artifacts are kept under their own tags with provenance intact rather than relabeled — every number continues to trace to its file.
- Trade-off accepted: live metrics in evals/results/ and the cached demo outputs remain the genuine 2026-10-19 GLM capture (marked HISTORICAL) until someone reruns `evals/run_eval.py --provider groq` or `scripts/gen_cache.py` with a key. Docs mark this everywhere numbers are quoted.
- Revisit if: Groq deprecates the gpt-oss models; free-tier limits change; or a Groq rerun shows metric drift beyond run-to-run noise.

### D-027 : Demo delivery — local Streamlit app instead of Hugging Face Spaces (user instruction)   [2026-10-20]
- Context: D-021 chose HF Spaces hosting per the original challenge constraint. The user then asked to "use streamlit instead of hugging face": the Streamlit app itself, run locally, is the demo; no third-party hosting.
- Options considered: A) local run only (`scripts/run_local.sh`); B) Streamlit Community Cloud (free, Streamlit-native public URL); C) keep the HF Space (rejected — user instruction).
- Decision: A as the default. `scripts/deploy_hf.sh` and `DEPLOY_STEPS.md` removed; `scripts/run_local.sh` added (venv, pinned requirements, optional `.env` load, keyless Offline-Mode boot); README quickstart leads with `bash scripts/run_local.sh`. B documented in the README as the natural upgrade if a public URL is ever needed (same repo, main file `app/streamlit_app.py`, `GROQ_API_KEY` as a secret).
- Reason: user instruction; also maximizes reviewer trust — no external account needed to see the demo, and the zero-key Offline Mode story stays intact (nothing leaves the reviewer's machine).
- Trade-off accepted: no public URL out of the box (the original challenge text asked for a live demo link); mitigated by the 2-command local run and the documented 5-minute Streamlit Community Cloud path.
- Revisit if: a submission requirement forces a hosted URL — deploy to Streamlit Community Cloud.

### D-025 : Open risks (living list)   [updated 2026-10-20]
1. **Synthetic-data overfit** — all metrics vs generated gold; unvalidated on real inquiries. Mitigation path: roadmap gate 1.
2. **Provider/model drift** — live numbers are the historical glm-4-plus gateway run (2026-10-19); the live provider is now Groq `openai/gpt-oss-120b` (D-026); direction of drift unknown until rerun with a key (`python evals/run_eval.py --provider groq`).
3. **Budget extraction regression in live mode** (0.75 vs 0.89 offline) — hybrid merge designed, not built.
4. **Multi-label over-firing** on associated services (dominant failure family) — per-label gates designed, not built.
5. **Rate-limit fragility** — Groq free tier is published and verified (30 RPM / 1K RPD / 8K TPM / 200K TPD per model): the 2-call pipeline sustains ~3 inquiries/min free; production needs the queue + fallback design already specified.
6. **Single-maintainer bus factor** — prompts/catalog/models need owners at Cynbit to survive contact with reality.
7. **No hosted demo URL by default** (D-027) — local Streamlit run instead; Streamlit Community Cloud path documented in the README if the submission needs a public link.
