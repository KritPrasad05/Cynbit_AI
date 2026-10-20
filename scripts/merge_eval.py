"""merge_eval.py — merge chunked live runs and build the final results bundle.

Live evals can be rate-limit chunked (run_eval.py --start/--end). This script:
  1. merges per_example_{tag}[_chunk*].jsonl files for each discovered tag,
  2. recomputes full metrics (single consistent semantics),
  3. writes metrics_{tag}.json + confusion matrices,
  4. writes the cross-run summary.json, metrics_table.json, cost_latency.json.

Tags are discovered from the files present, so both the current live provider
(groq, since the D-026 migration) and the historical GLM runs (2026-10-19)
merge side by side — numbers keep their provenance.

Usage: python scripts/merge_eval.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "evals"))

RESULTS = REPO / "evals" / "results"
from run_eval import compute_metrics, confusion_matrix_png  # noqa: E402

# Priority order for discovery; only tags with per-example files are merged.
TAGS = [
    "rules",
    "offline",
    "groq",
    "groq_no_grounding",
    "groq_no_fewshot",
    "glm",  # historical live provider (pre-migration, 2026-10-19)
    "glm_no_grounding",
    "glm_no_fewshot",
]

LABELS = {
    "rules": "Baseline B0 — keyword rules (no trained components)",
    "offline": "Baseline B1 — Offline engine (TF-IDF/LogReg + templates)",
    "groq": "FINAL — live Groq pipeline (2 structured calls + grounding)",
    "groq_no_grounding": "Ablation — live Groq without catalog grounding",
    "groq_no_fewshot": "Ablation — live Groq without few-shot examples",
    "glm": "HISTORICAL — live GLM pipeline (pre-migration run, 2026-10-19)",
    "glm_no_grounding": "HISTORICAL ablation — live GLM without catalog grounding",
    "glm_no_fewshot": "HISTORICAL ablation — live GLM without few-shot examples",
}


def gather(tag: str) -> tuple[list[dict], dict] | None:
    """Return (per_example rows in order, aggregate token/live info)."""
    chunk_files = sorted(RESULTS.glob(f"per_example_{tag}_chunk*.jsonl"))
    full_file = RESULTS / f"per_example_{tag}.jsonl"
    files = ([full_file] if full_file.exists() else []) + chunk_files
    if not files:
        return None
    rows: list[dict] = []
    for f in files:
        rows += [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    # dedupe by id (a full run + stale chunks could overlap), keep first
    seen, uniq = set(), []
    for r in rows:
        if r["id"] not in seen:
            seen.add(r["id"])
            uniq.append(r)
    agg = {"tokens_in": 0, "tokens_out": 0, "llm_calls": 0, "live_served": 0}
    # aggregates come from exactly one source: chunk metrics files if the run
    # was chunked, otherwise the single full-run metrics file. Never both —
    # merging both double-counts.
    if chunk_files:
        src_files = sorted(RESULTS.glob(f"metrics_{tag}_chunk*.json"))
    else:
        src_files = [RESULTS / f"metrics_{tag}.json"]
    for mf in src_files:
        if not mf.exists():
            continue
        m = json.loads(mf.read_text(encoding="utf-8"))
        agg["tokens_in"] += m.get("tokens", {}).get("prompt_total", 0)
        agg["tokens_out"] += m.get("tokens", {}).get("completion_total", 0)
        agg["llm_calls"] += m.get("llm_calls", 0)
        agg["live_served"] += m.get("live_served", 0)
    return uniq, agg


def main() -> int:
    table = {}
    lat_cache = {}
    for tag in TAGS:
        got = gather(tag)
        if got is None:
            print(f"  skip {tag} (no per-example files)")
            continue
        rows, agg = got
        lat = [r["latency_ms"] for r in rows]
        result = {
            "per_example": rows,
            "latencies": lat,
            "tokens_in": agg["tokens_in"],
            "tokens_out": agg["tokens_out"],
            "llm_calls": agg["llm_calls"],
            "live_served": agg["live_served"],
            "n": len(rows),
        }
        m = compute_metrics(result)
        (RESULTS / f"metrics_{tag}.json").write_text(
            json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        if tag in ("offline", "groq", "glm"):
            confusion_matrix_png(
                rows,
                RESULTS / f"confusion_matrix_{tag}.png",
                f"Service routing confusion matrix — {tag} (primary service, n={len(rows)})",
            )
        table[tag] = m
        lat_cache[tag] = m
        print(
            f"  {tag:<18} n={m['n']:<3} exact={m['service_exact_set_acc']:<6} "
            f"macroF1={m['service_macro_f1']:<6} cx={m['complexity_acc']:<6} "
            f"live={m['live_coverage']}"
        )

    # --- cross-run headline summary ------------------------------------------
    def g(tag, key, default=0.0):
        return table.get(tag, {}).get(key, default)

    summary = {
        "eval_split": "data/synthetic/leads_eval.jsonl (50 held-out synthetic examples, ~48% hard cases)",
        "service_exact_set_acc": {t: g(t, "service_exact_set_acc") for t in table},
        "service_macro_f1": {t: g(t, "service_macro_f1") for t in table},
        "oos_recall": {t: g(t, "oos_recall") for t in table},
        "complexity_acc": {t: g(t, "complexity_acc") for t in table},
        "complexity_adjacent_acc": {t: g(t, "complexity_adjacent_acc") for t in table},
        "budget_value_f1": {
            t: g(t, "budget_metrics", {}).get("value_f1") for t in table
        },
        "timeline_value_f1": {
            t: g(t, "timeline_metrics", {}).get("value_f1") for t in table
        },
        "injection_pass_rate": {t: g(t, "injection_pass_rate") for t in table},
        "live_coverage": {t: g(t, "live_coverage") for t in table},
        "notes": [
            "Gold labels are synthetic; metrics measure against that distribution.",
            "The 'glm' run is HISTORICAL: captured 2026-10-19 via the build environment's "
            "GLM gateway (served glm-4-plus), before the live provider migrated to Groq "
            "(decision.md D-026). Rerun live with: python evals/run_eval.py --provider groq",
            "Complexity metrics exclude out-of-scope rows (no engagement -> no estimate).",
        ],
        # Documented analysis of the ablation runs (provenance: the 2026-10-19
        # historical GLM session; underlying per_example files remain in results/).
        "ablation_notes": {
            "no_grounding": {
                "n": 10,
                "matched_live_only_exact_set": {"main": 0.62, "ablation": 0.62},
                "run_to_run_service_agreement": 1.0,
                "interpretation": (
                    "Classification deltas on n=10 are within run-to-run variance (agreement 100%) — "
                    "grounding is not an accuracy feature by design. What grounding adds: 100% of "
                    "service matches carry catalog evidence + source URL (0% in the ablation), and "
                    "confidence is calibrated against lexical support (low-support picks flagged)."
                ),
            },
            "no_fewshot": {
                "status": "blocked",
                "reason": "build-gateway rate limits exhausted retries during the 2026-10-19 session",
                "rerun": "python evals/run_eval.py --provider groq --ablation no_fewshot",
            },
        },
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")

    # --- reviewer-facing metrics table ----------------------------------------
    rows_out = []
    for t, m in table.items():
        rows_out.append(
            {
                "run": LABELS.get(t, t),
                "tag": t,
                "n": m["n"],
                "service exact-set acc": m["service_exact_set_acc"],
                "service macro-F1": m["service_macro_f1"],
                "OOS recall": m["oos_recall"],
                "complexity acc": m["complexity_acc"],
                "complexity adj acc": m["complexity_adjacent_acc"],
                "budget value F1": m["budget_metrics"]["value_f1"],
                "timeline value F1": m["timeline_metrics"]["value_f1"],
                "injection pass": m["injection_pass_rate"],
                "latency p50 (ms)": m["latency_ms"]["p50"],
                "tokens/example": m["tokens"]["per_example_mean"],
                "live coverage": m["live_coverage"],
            }
        )
    (RESULTS / "metrics_table.json").write_text(
        json.dumps(rows_out, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    # --- cost & latency projections ---------------------------------------------
    # Prefer a current Groq run; fall back to the historical GLM run.
    live = table.get("groq") or table.get("glm")
    if live:
        tok_ex = live["tokens"]["per_example_mean"]
        p50 = live["latency_ms"]["p50"]
        p95 = live["latency_ms"]["p95"]
        is_groq = "groq" in table
        cost = {
            "measured_on": (
                "live Groq runs (openai/gpt-oss-120b; n live examples)"
                if is_groq
                else "live GLM runs (build gateway, served glm-4-plus; n live examples) — "
                "HISTORICAL, pre-migration (D-026); refresh with --provider groq"
            ),
            "tokens_per_example_mean": tok_ex,
            "latency_p50_ms": p50,
            "latency_p95_ms": p95,
            "projections": {
                v: {
                    "requests_per_month": v,
                    "tokens_per_month": int(tok_ex * v),
                    "cost_usd_per_month_free_tier": 0.0,
                    "note": (
                        "Groq free tier (verified 2026-10-20): $0 within rate limits — "
                        "30 requests/min, 1K requests/day, 8K tokens/min, 200K tokens/day "
                        "per model (console.groq.com/docs/rate-limits). At ~2.7k tokens per "
                        "inquiry the 8K TPM cap allows ~3 inquiries/min sustained. On the "
                        "Developer tier, openai/gpt-oss-20b costs $0.075/M input + $0.30/M "
                        "output -> ~$0.29/month at 1k inquiries; gpt-oss-120b ~$0.57/month "
                        "(console.groq.com/docs/models)."
                    )
                }
                for v in (100, 1000, 10000)
            },
            "offline_mode": {
                "cost_usd": 0.0,
                "latency_p50_ms": table.get("offline", {}).get("latency_ms", {}).get("p50"),
            },
        }
        (RESULTS / "cost_latency.json").write_text(
            json.dumps(cost, ensure_ascii=False, indent=1), encoding="utf-8"
        )

    print("\nwrote summary.json, metrics_table.json" + (", cost_latency.json" if live else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
