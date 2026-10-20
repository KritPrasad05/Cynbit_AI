# DEPLOY_STEPS.md — how to publish and serve this demo

Three paths, in order of effort. **Path 1 is the reviewer default** (decision.md
D-027): the demo is a local Streamlit app, no hosting account needed. Path 2
makes the repo public. Path 3 optionally adds a free public URL via Streamlit
Community Cloud if a submission requires a live link (D-027 option B).

| Path | What you get | Time | Account needed |
|---|---|---|---|
| 1. Run locally | working demo at `http://localhost:8501` | ~2 min | none |
| 2. Push to GitHub | public repo, CI runs on every push | ~5 min | GitHub |
| 3. Streamlit Community Cloud | public `*.streamlit.app` URL | ~5 min | GitHub |

---

## Path 1 — Run the demo locally (default)

```bash
bash scripts/run_local.sh
```

That single script creates a `.venv`, installs the pinned
`requirements.txt`, loads `.env` if present, and boots Streamlit in
**Offline Mode** — zero keys, zero network. Manual equivalent:

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py   # http://localhost:8501
pytest tests/                        # 52 tests, no network
```

Optional live inference (free key from
[console.groq.com/keys](https://console.groq.com/keys)):

```bash
cp .env.example .env    # then set GROQ_API_KEY=... in .env
```

…or paste the key in the app sidebar (BYOK field — never logged or
persisted). Invalid or rate-limited keys fall back to Offline Mode
automatically; the mode badge always shows which path produced a result.

---

## Path 2 — Publish the repo to GitHub

The build environment has no GitHub credentials and the git identity is a
placeholder, so set your own identity first (once, per machine):

```bash
git config user.name  "Your Name"
git config user.email "you@example.com"
```

Then create an empty repo at `github.com/new` (name it
`cynbit-ai-opportunity`, public, **no** README/license/.gitignore — this repo
has all three) and push:

```bash
git remote add origin git@github.com:<your-user>/cynbit-ai-opportunity.git
# or: git remote add origin https://github.com/<your-user>/cynbit-ai-opportunity.git
git push -u origin main
```

Notes:

- Only `main` exists — no branches to select (CI triggers on push to `main`).
- `.env` is git-ignored and CI hard-fails if it ever appears in a commit;
  the repo also greps for committed secrets. Keys belong in the Streamlit
  sidebar or local `.env` only.
- CI on GitHub runs lint + 52 tests + offline eval smoke + a data
  determinism check (~3–4 min, Python 3.12, needs no secrets).

After the push, replace the `<your-user>` placeholder in exactly two places:

1. `README.md` — the GitHub badge link (line with
   `https://github.com/<your-user>/cynbit-ai-opportunity`).
2. `notebooks/poc_walkthrough.ipynb` — the commented Colab clone cell.

Commit as `docs: point README and notebook at the published repo`.

---

## Path 3 — Public URL via Streamlit Community Cloud (optional, free)

Streamlit's own free hosting deploys straight from the GitHub repo — no
Docker, no server, no card.

1. Complete Path 2 (the app deploys from GitHub, not from your laptop).
2. Go to [share.streamlit.io](https://share.streamlit.io) → sign in with
   GitHub → **New app**.
3. Pick: Repo `<your-user>/cynbit-ai-opportunity` · Branch `main` ·
   Main file path `app/streamlit_app.py` → **Deploy**.
4. (Optional) App → **Settings → Secrets** → add:

   ```toml
   GROQ_API_KEY = "gsk_..."
   LLM_PROVIDER = "groq"
   ```

   Secrets are injected as environment variables and are **never visible in
   the repo or logs**. Without a secret the app simply serves Offline Mode —
   the keyless reviewer experience is identical to Path 1.
5. Your URL: `https://<app-name>.streamlit.app` (first deploy takes a few
   minutes; cold starts after idle are ~30–60 s).

Why this deploys cleanly:

- `requirements.txt` sits at the repo root (Streamlit Cloud reads it from
  there) and pins everything, including `streamlit==1.66.0`.
- The app is a single process with no local models and no database — the
  default 1 GB resource is ample (two JSON-mode Groq calls per inquiry).
- Nothing auto-sends to clients; feedback thumbs write to in-app state only.

After the first deploy, add the URL to the README badge row (replacing the
`run_locally` demo badge or adding beside it):

```markdown
[![Live demo](https://img.shields.io/badge/demo-streamlit.app-FF4B4B)](https://<app-name>.streamlit.app)
```

Live-mode rate limits (Groq free tier, per model): 30 req/min · 1K req/day ·
8K tokens/min · 200K tokens/day. The 2-call pipeline sustains ~3
inquiries/min in live mode; beyond that, requests degrade gracefully to
Offline Mode rather than erroring (decision.md D-026).

---

## Post-publish verification checklist

- [ ] Repo URL opens; README badges and internal links resolve.
- [ ] GitHub Actions CI is green on `main` (lint → tests → eval smoke →
      determinism → secret scan).
- [ ] Demo (local or `*.streamlit.app`) boots with **no key** and shows the
      OFFLINE MODE badge.
- [ ] A one-click example replays a cached live-LLM output (badge shows the
      provider); an arbitrary typed input uses the deterministic engine.
- [ ] The prompt-injection one-click case still fails gracefully (no
      instruction-following of the injected text).
- [ ] With a valid Groq key, the badge switches to LIVE and latency/token
      usage appear on the result card.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `localhost:8501` already in use | `streamlit run app/streamlit_app.py --server.port 8502` |
| App boots but stays OFFLINE with a key set | Check `GROQ_API_KEY` has no quotes/spaces; check `.env` is loaded (`run_local.sh` prints it); provider is auto-detected |
| Streamlit Cloud app stuck on "Installing" | Ensure `requirements.txt` stays at repo root and pins resolve on Python 3.12+; check the app's Manage app → logs |
| Live calls suddenly go offline | Groq free-tier rate limit hit (429) — expected behavior; auto-fallback is by design |
