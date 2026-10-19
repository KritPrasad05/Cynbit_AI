"""scrape.py — Collect publicly accessible pages from cynbit.in into data/raw/.

Saves cleaned plain-text/markdown per page with a provenance header
(source URL, retrieval date, HTTP status). Pages that fail or look thin
are recorded in data/raw/_manifest.json — never invented.

Usage:
    python scripts/scrape.py                # scrape default page list
    python scripts/scrape.py /blog /story   # scrape specific paths

Only public marketing pages are collected. No login, no bypassing of any
access control. Collected for research/evaluation purposes with attribution.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

BASE = "https://www.cynbit.in"
OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36 cynbit-challenge-research/1.0"
)

DEFAULT_PATHS = [
    "/",
    "/services",
    "/products",
    "/case-studies",
    "/story",
    "/team",
    "/careers",
    "/impact",
    "/bitelevate",
    "/bitelevate/paths",
    "/diaries",
    "/blog",
    "/blog/ai-agents-business-operations",
    "/contact",
    "/privacy",
    "/terms",
]

SKIP_SUBSTRINGS = (
    "cookie", "advertis", "subscribe", "newsletter-modal", "sign in",
)


def clean_text(html: str) -> tuple[str, str]:
    """Return (main_text, title) with scripts/styles/nav chrome removed."""
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        title = re.sub(r"\s+", " ", soup.title.string).strip()
    else:
        title = ""
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "template"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    # collapse blank runs and strip trailing spaces
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln and not any(s in ln.lower() for s in SKIP_SUBSTRINGS)]
    return "\n".join(lines), title


def scrape(paths: list[str]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict] = {}
    fetched_on = dt.date.today().isoformat()
    with httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=25,
        follow_redirects=True,
    ) as client:
        for path in paths:
            url = BASE + path
            fname = (path.strip("/") or "home") + ".md"
            fname = fname.replace("/", "_")
            out = OUT_DIR / fname
            try:
                resp = client.get(url)
                status = resp.status_code
                text, title = clean_text(resp.text) if status == 200 else ("", "")
                chars = len(text)
                header = (
                    f"<!--\nsource_url: {url}\n"
                    f"retrieved_on: {fetched_on}\n"
                    f"http_status: {status}\n"
                    f"chars_after_cleaning: {chars}\n"
                    f"note: public marketing page, cleaned text-only snapshot for research;\n"
                    f"      dynamic content (forms, JS widgets) not captured.\n-->\n\n"
                    f"# {title or path}\n\n{text}\n"
                )
                out.write_text(header, encoding="utf-8")
                manifest[url] = {
                    "file": f"data/raw/{out.name}",
                    "status": status,
                    "chars": chars,
                    "retrieved_on": fetched_on,
                }
                print(f"{status} {path} -> {out.name} ({chars} chars)")
            except Exception as exc:  # noqa: BLE001 — record and continue
                manifest[url] = {
                    "file": None,
                    "error": f"{type(exc).__name__}: {exc}",
                    "retrieved_on": fetched_on,
                }
                print(f"ERR {path}: {exc}")
    (OUT_DIR / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nmanifest -> {OUT_DIR / '_manifest.json'}")


if __name__ == "__main__":
    paths = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_PATHS
    scrape(paths)
