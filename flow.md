# flow.md — How the deliverables fit together

Six Mermaid diagrams, each followed by a short explanation, then a table
mapping every challenge requirement to the exact file that satisfies it.

## 1. Deliverables flow

```mermaid
flowchart TD
    R[Phase 1 research<br/>scrape cynbit.in + market sources] --> OR[01 AI Opportunity Report<br/>13 scored opportunities]
    OR --> SEL[Phase 2 selection<br/>Discovery Copilot 4.80/5]
    SEL --> D[Phase 4 data<br/>170 synthetic leads, seed 42]
    D --> POC[Phase 5 POC<br/>pipeline + offline engine + Streamlit]
    POC --> EV[Phase 6 evaluation<br/>2 baselines + live + ablations]
    EV --> TAR[03 Technical Approach Report]
    POC --> DEP[Phase 9 deployment<br/>HF Space + GitHub]
    TAR --> META[Phase 8 meta-docs<br/>README · decision.md · flow.md · report.md]
    DEP --> META
    META --> QA[Phase 10 final QA checklist]
```

Research grounds the opportunity report; the report's scoring picks the POC;
the POC is only credible because the eval harness measures it; the technical
report explains what was built and measured; meta-documents describe reality
after the fact, and QA closes the loop.

## 2. System architecture

```mermaid
flowchart LR
    U[user inquiry] --> S[Sanitizer<br/>PII mask · injection screen]
    S --> C{mode?}
    C -- groq live --> L1[LLM call 1<br/>classify+extract JSON]
    C -- offline --> O1[TF-IDF+LogReg<br/>+ regex + OOS rules]
    L1 --> G[Grounder<br/>catalog evidence + source URL]
    O1 --> G
    G --> E[Estimator<br/>deterministic S/M/L]
    E --> A{mode?}
    A -- groq live --> L2[LLM call 2<br/>risks·questions·steps JSON]
    A -- offline --> O2[template advisor]
    L2 --> V[Pydantic validator<br/>retry ≤ 2 with error feedback]
    O2 --> V
    V --> B[LeadBrief]
    B --> UI[Streamlit cards<br/>mode badge · feedback]
    L1 -. ProviderUnavailable .-> O1
    L2 -. ProviderUnavailable .-> O2
```

The dashed paths are the automatic offline fallback: missing key, auth
failure, repeated 429s, or timeout never crash the app — the badge tells the
user which path produced the result.

## 3. Data pipeline

```mermaid
flowchart LR
    A[cynbit.in public pages<br/>20 pages, provenance headers] -->|scripts/scrape.py| B[data/raw/]
    B -->|hand-curation| C[app/assets/services_catalog.json]
    T[scripts/build_data.py<br/>seed 42] -->|170 synthetic leads| S[data/synthetic/]
    S -->|120| TR[train split]
    S -->|50 frozen| EV[eval split<br/>never used for prompts]
    TR -->|fit| CL[offline classifier + complexity model]
    TR -->|4 verbatim rows| FS[few-shot in prompts.py]
    DEMO[8 demo examples] -->|scripts/gen_cache.py<br/>live LLM| CACHE[cached_outputs.json]
    CACHE --> OFF[Offline Mode replay]
```

The catalog is hand-curated public fact (not synthetic); the leads are
synthetic with banners; the eval split is frozen and never touches prompts;
the cache holds genuine live-model outputs for the demo inputs.

## 4. Request lifecycle (sequence)

```mermaid
sequenceDiagram
    participant U as User
    participant ST as Streamlit UI
    participant P as Pipeline
    participant R as Grounder (catalog)
    participant L as Groq (live) / Offline engine
    participant V as Validator (Pydantic)

    U->>ST: paste inquiry / click example
    ST->>P: run(text)
    P->>P: sanitize (PII mask, injection screen)
    P->>L: classify+extract (schema, temp 0.1)
    alt invalid JSON / validation error
        L->>L: retry ≤ 2 (error fed back)
    end
    alt ProviderUnavailable (no key / 401 / 429×2 / timeout)
        P->>L: offline engine takes over
    end
    P->>R: score services vs catalog
    R-->>P: evidence + source URLs + confidences
    P->>P: deterministic estimate (S/M/L + range)
    P->>L: advise (risks, questions, steps)
    L-->>P: JSON
    P->>V: assemble LeadBrief
    V-->>ST: valid brief (or retry / fallback note)
    ST->>U: cards + mode badge + latency/tokens
    U->>ST: thumbs up/down
    ST->>ST: append data/feedback.jsonl (masked input only)
```

## 5. Reviewer journey (first 5 minutes)

```mermaid
flowchart TD
    A[README.md<br/>60-second orientation] --> B{run the demo}
    B --> C[bash scripts/run_local.sh<br/>boots in Offline Mode, no key]
    C --> D[click one-click example<br/>e.g. Prompt-injection attempt]
    D --> E[structured brief renders<br/>badge + latency + evidence]
    E --> F{impressed?}
    F -- yes --> G[open evals/results/<br/>metrics_table.json + failures.md]
    F -- yes --> H[skim docs/01 report<br/>→ decision.md for judgment calls]
    G --> I[add own Groq key in sidebar<br/>→ live inference]
    H --> I
```

Everything a reviewer needs in 5 minutes is one README away: a 2-command
local demo, results table, the three required deliverables, and the honest
limitations. (Optional public URL: Streamlit Community Cloud — D-027.)

## 6. Git and deployment flow

```mermaid
flowchart LR
    D[dev: conventional commits<br/>one logical change each] --> GH[GitHub repo<br/>main branch]
    GH --> CI[GitHub Actions<br/>ruff + pytest + offline eval smoke<br/>+ determinism + secret scan]
    CI -->|green| LOC[reviewer clones & runs<br/>bash scripts/run_local.sh]
    LOC -->|no secrets by default| APP[app boots in Offline Mode]
    LOC -->|BYOK GROQ_API_KEY<br/>sidebar or .env| LIVE[Live Groq enabled]
    GH -. optional . SCC[Streamlit Community Cloud<br/>free public URL]
```

Since 2026-10-20 the demo ships as a local Streamlit app (D-027); a public
URL, if ever needed, comes from Streamlit Community Cloud with the same repo.

## Requirement → file mapping

| Challenge requirement | Where it is satisfied |
|---|---|
| AI Opportunity Report (industry analysis, opportunities) | `docs/01_AI_Opportunity_Report.md` (2,000–3,500 words, Fact/Claim/Inference labels, sources with dates) |
| AI/ML Proof of Concept (functional demo) | `app/` (Streamlit) + `data/` + `scripts/`; runs keyless via Offline Mode |
| Technical Approach Report (models, pipeline, prompts, plan) | `docs/03_Technical_Approach_Report.md` |
| Clean code + git history | 25+ conventional commits on `main`; CI: `.github/workflows/ci.yml` |
| Public GitHub repo / live demo | `README.md` quickstart (`bash scripts/run_local.sh`); optional public URL via Streamlit Community Cloud — D-027 |
| LLM provider verification (Groq) | `decision.md` D-026 (models, deprecations, rate limits verified 2026-10-20 with sources; GLM-era record in D-004) |
| Zero-key demo (Offline Mode) | `app/core/offline.py` + `data/synthetic/cached_outputs.json` + UI badge |
| $0 budget | free-tier LLM (Groq), local run / free Streamlit Community Cloud if hosted, no paid APIs (cost model: `docs/bonus/04_ROI_and_Cost_Model.md`) |
| ≥10 scored opportunities, weights, matrix | `docs/bonus/07_Opportunity_Scoring_Matrix.md` (13 opportunities) |
| Red-team pass on the pick | `docs/bonus/07_Opportunity_Scoring_Matrix.md` §C; summarized in report §7 |
| ≥150 labeled synthetic examples + hard cases | `data/synthetic/leads_{train,eval}.jsonl` (170; vague/Hinglish/OOS/injection/very-short/mixed) |
| Held-out split never used for tuning | frozen `leads_eval.jsonl`; few-shot = train rows only (D-011) |
| Synthetic-data banners + provenance | banner line in every synthetic file; `data/README_data.md`; provenance note per example |
| Pipeline (not mega-prompt) + structured outputs + retries | `app/core/pipeline.py`, `app/core/schemas.py`, bounded validation retries |
| Grounding over fluency | `app/core/retrieval.py` + catalog; missing info → clarifying questions |
| Human in the loop | confidence + needs_human_review flags; draft-only posture in UI |
| Cheap by default, caching | free-tier model default, in-memory request cache, cached demo outputs |
| PII masking in logs | `sanitize()` runs before any model call/write; feedback stores masked data |
| Robustness (empty/long/non-English/off-topic) | sanitizer warnings + OOS rules; tests in `tests/` |
| Rate-limit/timeout + friendly errors | `app/core/llm_client.py` (ProviderUnavailable → fallback); UI never crashes |
| Provider abstraction `generate(messages, schema=...)` | `app/core/llm_client.py::GroqClient.generate` |
| Eval: metrics, baseline, ablation, failure cases, cost | `evals/run_eval.py`, `evals/results/` (metrics, confusion matrices, `failures.md`, `cost_latency.json`) |
| 30/60/90 roadmap | `docs/bonus/08_Rollout_Roadmap_30_60_90.md` |
| Sample transcripts (8+, incl. failures + injection) | `sample_chats/` (4 live + 4 offline, annotated) |
| Colab-ready notebook | `notebooks/poc_walkthrough.ipynb` (Offline Mode default) |
| decision.md with required coverage | `decision.md` (D-001…D-025 + open risks) |
| report.md retrospective | `report.md` |
| Bonus: ROI, ethics/DPDP, competitors, demo script | `docs/bonus/04,05,06,09` |
| Eval dashboard in app | Streamlit "Eval dashboard" page |
