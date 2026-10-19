"""retrieval.py — grounding layer over the curated public service catalog.

Every service match in the final brief must carry evidence traced to this
catalog (source: cynbit.in/services, 2026-10-19). Pure-Python TF-IDF cosine
similarity — no network, no embeddings API, deterministic.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "app" / "assets" / "services_catalog.json"

_TOKEN_RE = re.compile(r"[a-z0-9]{2,}")
_STOPWORDS = {
    "the", "and", "for", "our", "with", "that", "this", "have", "need",
    "want", "would", "could", "you", "are", "was", "but", "not", "can",
    "our", "out", "get", "has", "had", "will", "shall", "into", "from",
    "please", "thanks", "hi", "hello", "team", "regards",
}


def _tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]


@dataclass
class GroundedService:
    service_id: str
    service_name: str
    score: float
    evidence: str
    source_url: str
    related_product: str | None


class ServiceGrounder:
    """TF-IDF cosine grounder over the service catalog."""

    def __init__(self, catalog_path: Path = CATALOG_PATH) -> None:
        data = json.loads(catalog_path.read_text(encoding="utf-8"))
        self.services = data["services"]
        self.products = {p["id"]: p for p in data.get("products", [])}
        self._service_docs: dict[str, list[str]] = {}
        self._doc_ids: dict[str, list[str]] = {}
        for svc in self.services:
            blob = " ".join(
                [svc["description"]] + svc["capabilities"] + svc["match_keywords"]
            )
            self._service_docs[svc["id"]] = _tokenize(blob)
            self._doc_ids[svc["id"]] = svc["id"]
        self._idf = self._build_idf()

    def _build_idf(self) -> dict[str, float]:
        import math

        df: dict[str, int] = {}
        for tokens in self._service_docs.values():
            for tok in set(tokens):
                df[tok] = df.get(tok, 0) + 1
        n = len(self._service_docs)
        return {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}

    def _vec(self, tokens: list[str]) -> dict[str, float]:
        tf: dict[str, float] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0.0) + 1.0
        return {t: (c / len(tokens)) * self._idf.get(t, 1.0) for t, c in tf.items()}

    def _cosine(self, a: dict[str, float], b: dict[str, float]) -> float:
        import math

        if not a or not b:
            return 0.0
        common = set(a) & set(b)
        num = sum(a[t] * b[t] for t in common)
        den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(
            sum(v * v for v in b.values())
        )
        return num / den if den else 0.0

    # -- public API ----------------------------------------------------------

    def score_services(self, inquiry_text: str) -> list[GroundedService]:
        """Rank all services against the inquiry; descending score."""
        qvec = self._vec(_tokenize(inquiry_text))
        scored: list[GroundedService] = []
        for svc in self.services:
            svec = self._vec(self._service_docs[svc["id"]])
            score = self._cosine(qvec, svec)
            matched_caps = [
                cap for cap in svc["capabilities"]
                if any(tok in _tokenize(cap) for tok in qvec)
            ]
            evidence = (
                f"Catalog: {svc['name']} — "
                + (". ".join(matched_caps[:2]) if matched_caps else svc["description"][:140])
            )
            related = None
            if svc["id"] == "ai_automation" and any(
                k in inquiry_text.lower() for k in ("review", "reputation", "rating")
            ):
                related = "Revio"
            if svc["id"] == "ai_automation" and any(
                k in inquiry_text.lower() for k in ("resume", "career", "hir")
            ):
                related = "Cynbit Studio"
            if svc["id"] == "software_dev" and any(
                k in inquiry_text.lower() for k in ("property", "tenant", "rent")
            ):
                related = "TenantEase"
            scored.append(
                GroundedService(
                    service_id=svc["id"],
                    service_name=svc["name"],
                    score=round(score, 4),
                    evidence=evidence,
                    source_url=svc["source_url"],
                    related_product=related,
                )
            )
        return sorted(scored, key=lambda g: g.score, reverse=True)

    def evidence_for(self, service_id: str, inquiry_text: str) -> GroundedService | None:
        for g in self.score_services(inquiry_text):
            if g.service_id == service_id:
                return g
        return None

    def catalog_context(self) -> str:
        """Compact catalog block reused inside prompts (kept in one source)."""
        lines = []
        for svc in self.services:
            lines.append(
                f"- {svc['id']} | {svc['name']}: {svc['description'][:180]}"
            )
        return "\n".join(lines)


# module-level singleton (catalog loads once per process)
_grounder: ServiceGrounder | None = None


def get_grounder() -> ServiceGrounder:
    global _grounder
    if _grounder is None:
        _grounder = ServiceGrounder()
    return _grounder
