"""gen_cache.py — generate data/synthetic/cached_outputs.json via LIVE GLM.

Runs the full live pipeline (GLMClient → OpenAI-compatible endpoint) over the
8 built-in demo examples and stores the resulting LeadBriefs. Offline Mode
replays these for the one-click examples, so keyless reviewers see real
model output.

Usage:
    GLM_API_KEY=... python scripts/gen_cache.py
    # endpoint/model override:
    GLM_BASE_URL=https://api.z.ai/api/paas/v4 GLM_MODEL=glm-4.5-flash \
    GLM_API_KEY=... python scripts/gen_cache.py

If no key is present the script exits with a clear message (never fabricates
"live" outputs).
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.core.examples import DEMO_EXAMPLES  # noqa: E402
from app.core.llm_client import GLMClient, ProviderUnavailable  # noqa: E402
from app.core.pipeline import DiscoveryPipeline  # noqa: E402
from app.core.prompts import PROMPT_VERSION  # noqa: E402

CACHE_PATH = REPO_ROOT / "data" / "synthetic" / "cached_outputs.json"


def main() -> int:
    api_key = os.environ.get("GLM_API_KEY", "")
    if not api_key:
        print(
            "No GLM_API_KEY set. The cache must contain REAL live-model output — "
            "refusing to fabricate. Set a free key (open.bigmodel.cn / z.ai) and retry."
        )
        return 2
    try:
        llm = GLMClient(api_key=api_key)
    except ProviderUnavailable as exc:
        print(f"Provider unavailable: {exc}")
        return 2

    pipe = DiscoveryPipeline(provider="glm", llm=llm)
    # resume support: keep genuinely-live entries from an existing cache
    examples_out, done_ids = [], set()
    if CACHE_PATH.exists():
        try:
            prev = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            for e in prev.get("examples", []):
                if e.get("output", {}).get("provenance", {}).get("mode") == "glm_live":
                    examples_out.append(e)
                    done_ids.add(e["example_id"])
            print(f"resuming: {len(done_ids)} already-live entries kept")
        except (json.JSONDecodeError, OSError):
            pass
    for ex in DEMO_EXAMPLES:
        if ex["id"] in done_ids:
            continue
        t0 = time.perf_counter()
        brief = None
        for attempt in range(3):  # retry transient live failures before accepting
            brief = pipe.run(ex["text"])
            if brief.provenance.mode == "glm_live":
                break
            print(f"  attempt {attempt+1} not live ({brief.provenance.mode}); backing off...")
            pipe._cache.clear()
            time.sleep(3 + attempt * 4)
        wall = int((time.perf_counter() - t0) * 1000)
        d = brief.model_dump()
        d["provenance"]["latency_ms"] = wall  # wall clock incl. overhead
        d["provenance"]["notes"] = [
            "Precomputed live-GLM output for this built-in demo example "
            "(replayed verbatim in Offline Mode)."
        ]
        examples_out.append(
            {"example_id": ex["id"], "label": ex["label"], "input": ex["text"], "output": d}
        )
        print(f"  cached {ex['id']} (mode={brief.provenance.mode}, {wall}ms, "
              f"{brief.provenance.prompt_tokens + brief.provenance.completion_tokens} tokens)")
        time.sleep(1.2)

    meta = {
        "generated_on": time.strftime("%Y-%m-%d"),
        "provider": "live GLM via OpenAI-compatible endpoint",
        "model": llm.model,
        "base_url": llm.base_url,
        "prompt_version": PROMPT_VERSION,
        "note": (
            "SYNTHETIC demo inputs; REAL live-model outputs captured once for "
            "Offline Mode replay. Regenerate with scripts/gen_cache.py."
        ),
    }
    CACHE_PATH.write_text(
        json.dumps({"meta": meta, "examples": examples_out}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(f"\nwrote {CACHE_PATH} ({len(examples_out)} examples)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
