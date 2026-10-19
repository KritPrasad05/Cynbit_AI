"""Smoke check of the offline pipeline + estimator calibration on TRAIN split.

Run: python scripts/calibrate_check.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import json

from app.core.pipeline import DiscoveryPipeline, estimate_complexity, sanitize
from app.core.schemas import ClassifyExtract


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip() and not l.startswith("#")]


train = load(REPO / "data" / "synthetic" / "leads_train.jsonl")

pipe = DiscoveryPipeline(provider="offline")

# quick end-to-end runs
from app.core.examples import DEMO_EXAMPLES

for ex in DEMO_EXAMPLES[:3] + [DEMO_EXAMPLES[7]]:
    b = pipe.run(ex["text"])
    print(f"[{ex['id']}] mode={b.provenance.mode} services={[m.service_id for m in b.services]} "
          f"intent={b.intent} cx={b.estimate.complexity if b.estimate else '-'} "
          f"inj={b.sanitization.injection_suspected} q={len(b.clarifying_questions)}")

# complexity calibration on TRAIN
correct = 0
total = 0
misses = []
for r in train:
    san = sanitize(r["text"])
    ce = pipe.engine.classify_extract(san.sanitized_text, san)
    est = estimate_complexity(ce, san.sanitized_text, pipe.engine.complexity_model())
    total += 1
    if est.complexity == r["labels"]["complexity"]:
        correct += 1
    else:
        misses.append((r["id"], r["labels"]["complexity"], est.complexity, (ce.goal or "")[:60]))
print(f"\ncomplexity accuracy on TRAIN: {correct}/{total} = {correct/total:.2%}")
for m in misses[:12]:
    print("  miss:", m)

# service classification accuracy on TRAIN (in-sample)
ok = 0
tot = 0
for r in train:
    if r["labels"]["services"] == ["out_of_scope"]:
        continue
    san = sanitize(r["text"])
    ce = pipe.engine.classify_extract(san.sanitized_text, san)
    tot += 1
    if set(ce.services) == set(r["labels"]["services"]):
        ok += 1
print(f"\nservice exact-set match on TRAIN (in-sample): {ok}/{tot} = {ok/tot:.2%}")
