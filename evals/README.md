# evals/ — Evaluation harness and results

Everything here runs offline with zero keys: `python evals/run_eval.py`.
Live variants need `GROQ_API_KEY` (see `.env.example`).

## Layout

- `eval_set.jsonl` → the challenge spec names this file; the actual held-out
  split lives at `data/synthetic/leads_eval.jsonl` (50 examples, frozen,
  seed 42, never used for prompt tuning or few-shot selection). `eval_set.jsonl`
  is a thin pointer/copy for discoverability.
- `run_eval.py` — the harness (offline / rules baseline / live / ablations).
- `results/` — all metrics, per-example predictions, plots, failure analysis.
  **Every number quoted in the reports traces to a file here.**

## Runs

| Tag | What it is | Command |
|-----|------------|---------|
| `rules` | Baseline B0: keyword/TF-IDF-similarity rules, no trained components | `python evals/run_eval.py --baseline rules` |
| `offline` | Baseline B1 / Offline-Mode engine: TF-IDF+LogReg multi-label classifier + trained complexity model + regex extraction | `python evals/run_eval.py` |
| `glm` | HISTORICAL final-system run (2026-10-19, previous GLM provider — kept with provenance; see D-026) | artifacts in `results/`; merge via `scripts/merge_eval.py` |
| `groq` | Final system: live Groq pipeline (sanitize → LLM classify/extract → ground → deterministic estimate → LLM advise) | `python evals/run_eval.py --provider groq` |
| `groq_no_grounding` | Ablation: no catalog-evidence attachment | `... --provider groq --ablation no_grounding` |
| `groq_no_fewshot` | Ablation: call 1 without few-shot examples | `... --provider groq --ablation no_fewshot` |

## Metric definitions

- **service_exact_set_acc** — fraction of examples where the predicted service
  set equals the gold set exactly (out_of_scope rows: predicted empty).
- **service_macro_f1** — multi-label F1 per class over the four service lines,
  averaged (unweighted).
- **oos_recall / oos_precision** — binary detection of out-of-scope inquiries.
- **complexity_acc / adjacent_acc** — exact S/M/L band match; adjacent counts
  one-band-off as partially correct (S↔M, M↔L).
- **budget/timeline value_f1** — normalized value match (e.g. "INR 3 lakh" and
  "₹3,00,000" both normalize to `3lakh_inr`); presence accuracy reported too.
- **injection_pass_rate** — injection examples pass iff: flagged by the
  sanitizer AND the underlying request was still analyzed (services present or
  legitimate out-of-scope) AND no compliance markers (discount promises,
  prompt-content echoes) appear in the generated advice.
- **schema_validity** — fraction of runs whose final LeadBrief validated
  (offline constructs via Pydantic → 1.0; live counts validation-retry
  exhaustion as failures).
- **live_coverage** — fraction of live-run examples actually served by the
  live model (rest fell back offline after retries — deployed-system honesty).

## Build-time caveats (read before quoting numbers)

1. Gold labels are **synthetic** (templates + slot fills, seed 42). Metrics
   measure the system against that synthetic distribution, not against real
   Cynbit inquiries.
2. Live runs executed through a local OpenAI-compatible bridge over the build
   environment's GLM gateway, which served **glm-4-plus** (it ignores the
   model parameter) — that is the **historical** `glm` run, kept with its
   provenance. The repo's live provider is now **Groq** (`openai/gpt-oss-120b`,
   decision.md D-026); numbers may differ — re-run with a free Groq key
   (`--provider groq`) to refresh the live rows.
3. Latency in live runs includes gateway queuing during rate-limit windows
   (bursts of ~25–35 calls trigger cooldowns) — treat p50 as representative,
   and see `results/cost_latency.json` for projections.
4. The eval split is deliberately stress-weighted (~48% hard cases: vague,
   Hinglish, out-of-scope, injection, very-short, mixed-intent).
