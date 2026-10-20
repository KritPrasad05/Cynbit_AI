"""make_failures.py — build evals/results/failures.md from per-example data.

Selects the 5 worst live-run failures (ranked: service-set mismatch >
complexity mismatch > extraction misses) and renders them for manual
root-cause annotation (annotations are written by the author in the
generated file — the script only assembles evidence).
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "evals" / "results"

rows = []
for f in sorted(
    set(RES.glob("per_example_glm*.jsonl")) | set(RES.glob("per_example_groq*.jsonl"))
):
    rows += [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
seen, uniq = set(), []
for r in rows:
    if r["id"] not in seen:
        seen.add(r["id"])
        uniq.append(r)

eval_texts = {}
for l in (REPO / "data/synthetic/leads_eval.jsonl").read_text(encoding="utf-8").splitlines():
    if l.strip() and not l.startswith("#"):
        d = json.loads(l)
        eval_texts[d["id"]] = d


def score(e: dict) -> int:
    s = 0
    if e["pred_oos"] != e["gold_oos"]:
        return 10  # worst: misjudged the engagement itself
    if e["gold_oos"]:
        return 0  # correctly rejected -> compare only extraction side notes
    if set(e["pred_services"]) != set(e["gold_services"]):
        s += 4
    if e["pred_complexity"] != e["gold_complexity"]:
        s += 2
    if e["gold_budget"] and e["pred_budget"] != e["gold_budget"]:
        s += 1
    if e["gold_timeline"] and e["pred_timeline"] != e["gold_timeline"]:
        s += 1
    return s


ranked = sorted(uniq, key=score, reverse=True)
worst = [e for e in ranked if score(e) >= 3][:6]

out = [
    "# Failure analysis — worst live-run outputs",
    "",
    "Selected from `per_example_glm*.jsonl` / `per_example_groq*.jsonl` (live",
    "LLM runs — historical GLM and/or current Groq — on the 50-example held-out",
    "split) by composite severity: OOS mismatch (3) > service-set mismatch (4)",
    "> complexity mismatch (2) > extraction miss (1 each). Root causes are the",
    "author's analysis of each case — see the pattern summary at the end.",
    "",
]
for e in worst:
    src = eval_texts.get(e["id"], {})
    out += [
        f"## {e['id']} (hard case: {e['hard_case'] or 'standard'}) — severity {score(e)}",
        "",
        f"- **Input (abridged):** {src.get('text', '')[:220]}…",
        f"- **Gold services:** {e['gold_services']} → **predicted:** {e['pred_services']}",
        f"- **Gold complexity:** {e['gold_complexity']} → **predicted:** {e['pred_complexity']}",
        f"- **Gold budget:** {e['gold_budget']} → **predicted:** {e['pred_budget']}",
        f"- **Gold timeline:** {e['gold_timeline']} → **predicted:** {e['pred_timeline']}",
        f"- **Mode:** {e['mode']}",
        "",
        "_Root cause (author):_ PENDING",
        "",
    ]

out += [
    "## Pattern summary",
    "",
    "_PENDING — filled after review._",
    "",
]

(RES / "failures.md").write_text("\n".join(out), encoding="utf-8")
print(f"wrote failures.md with {len(worst)} cases; severity ranking:")
for e in worst:
    print(f"  {e['id']} sev={score(e)} hard={e['hard_case']} gold={e['gold_services']} pred={e['pred_services']}")
