"""gen_cache.py — generate data/synthetic/cached_outputs.json via LIVE Groq.

Runs the full live pipeline (GroqClient → api.groq.com OpenAI-compatible
endpoint) over the 8 built-in demo examples and stores the resulting
LeadBriefs. Offline Mode replays these for the one-click examples, so keyless
reviewers see real model output.

Usage:
    GROQ_API_KEY=... python scripts/gen_cache.py
    # model override (Groq production models, verified 2026-10-20):
    GROQ_MODEL=openai/gpt-oss-20b GROQ_API_KEY=... python scripts/gen_cache.py

If no key is present the script exits with a clear message (never fabricates
"live" outputs). The current cache was captured with the previous GLM
provider on 2026-10-19 — regenerating with a Groq key refreshes it.
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
from app.core.llm_client import GroqClient, ProviderUnavailable  # noqa: E402
from app.core.pipeline import DiscoveryPipeline  # noqa: E402
from app.core.prompts import PROMPT_VERSION  # noqa: E402

CACHE_PATH = REPO_ROOT / "data" / "synthetic" / "cached_outputs.json"


def main() -> int:
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print(
            "No GROQ_API_KEY set. The cache must contain REAL live-model output — "
            "refusing to fabricate. Get a free key at https://console.groq.com/keys "
            "and retry."
        )
        return 2
    try:
        llm = GroqClient(api_key=api_key)
    except ProviderUnavailable as exc:
        print(f"Provider unavailable: {exc}")
        return 2

    pipe = DiscoveryPipeline(provider="groq", llm=llm)
    # resume support: keep genuinely-live entries from an existing cache
    examples_out, done_ids = [], set()
    if CACHE_PATH.exists():
        try:
            prev = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            for e in prev.get("examples", []):
                if e.get("output", {}).get("provenance", {}).get("mode") in (
                    "groq_live",
                    "glm_live",  # legacy entries captured pre-migration (D-026)
                ):
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
            if brief.provenance.mode == "groq_live":
                break
            print(f"  attempt {attempt+1} not live ({brief.provenance.mode}); backing off...")
            pipe._cache.clear()
            time.sleep(3 + attempt * 4)
        wall = int((time.perf_counter() - t0) * 1000)
        d = brief.model_dump()
        d["provenance"]["latency_ms"] = wall  # wall clock incl. overhead
        d["provenance"]["notes"] = [
            "Precomputed live-LLM output for this built-in demo example "
            "(replayed verbatim in Offline Mode)."
        ]
        examples_out.append(
            {"example_id": ex["id"], "label": ex["label"], "input": ex["text"], "output": d}
        )
        print(f"  cached {ex['id']} (mode={brief.provenance.mode}, {wall}ms, "
              f"{brief.provenance.prompt_tokens + brief.provenance.completion_tokens} tokens)")
        time.sleep(2.5)  # Groq free tier: stay under 30 RPM / 8K TPM

    meta = {
        "generated_on": time.strftime("%Y-%m-%d"),
        "provider": "live Groq via OpenAI-compatible endpoint",
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
