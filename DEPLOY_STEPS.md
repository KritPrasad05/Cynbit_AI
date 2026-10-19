# DEPLOY_STEPS.md — publish the repo and the live demo

The build environment had no GitHub/HuggingFace credentials, so publication is
a 10-minute manual step for you (the candidate). Exact commands below.
Everything else (Space packaging, no-secret defaults, pinned requirements) is
already prepared.

## 0. Prerequisites

- `git` (any recent version)
- A GitHub account
- A Hugging Face account
- Optional: a free GLM API key from https://open.bigmodel.cn (CN) or
  https://z.ai (international) — only needed for Live mode

## 1. Push the repository to GitHub

```bash
cd cynbit-ai-opportunity

# set your identity if this machine doesn't have one
git config user.name  "Your Name"
git config user.email "you@example.com"

# create the repo on github.com first (public, no README/license —
# this repo already has both), then:
git remote add origin git@github.com:<your-user>/cynbit-ai-opportunity.git
# or HTTPS: git remote add origin https://github.com/<your-user>/cynbit-ai-opportunity.git
git push -u origin main
```

Sanity check before/after pushing:

```bash
git log --oneline | wc -l        # expect ~30 commits
git log -p | grep -iE "api[_-]?key\s*=" | head   # expect no real secrets
test ! -f .env && echo "no .env — good"
```

## 2. Create the Hugging Face Space

1. Go to https://huggingface.co/new-space
2. Owner: your user · Space name: `cynbit-discovery-copilot`
3. SDK: **Streamlit** · License: **MIT** · Space hardware: **CPU basic** (free)
4. Visibility: **Public**
5. Create.

## 3. Deploy the app to the Space

Option A — the scripted way (stages files, writes the Space README
frontmatter, pushes):

```bash
pip install "huggingface_hub[cli]"
huggingface-cli login          # paste a write token from hf.co/settings/tokens
bash scripts/deploy_hf.sh <your-hf-user> cynbit-discovery-copilot
```

Option B — manual:

```bash
git clone https://huggingface.co/spaces/<your-hf-user>/cynbit-discovery-copilot space
cd space
# copy from the repo: app/ (streamlit_app.py, core/, assets/),
# data/synthetic/{leads_train,leads_eval,cached_outputs}.jsonl|json,
# evals/results/, requirements.txt
# add the Space README frontmatter from scripts/deploy_hf.sh (sdk: streamlit,
# sdk_version: 1.66.0, app_file: app/streamlit_app.py)
git add -A && git commit -m "deploy: discovery copilot" && git push
```

The Space boots in **Offline Mode with zero secrets** — one-click examples
replay cached live-GLM outputs; arbitrary inputs use the deterministic engine.

## 4. (Optional) enable Live GLM on the Space

Space → **Settings → Variables and secrets** → New secret:

- `GLM_API_KEY` = your key
- optional `GLM_BASE_URL` = `https://open.bigmodel.cn/api/paas/v4` (default)
  or `https://api.z.ai/api/paas/v4`
- optional `GLM_MODEL` = `glm-4-flash` (default) or `glm-4.5-flash`

Never put the key in the repo, the Space README, or commit history.

## 5. Finish the README links

In `README.md`, replace:

- `https://github.com/<your-user>/cynbit-ai-opportunity` (2 places)
- `https://huggingface.co/spaces/<your-hf-user>/cynbit-discovery-copilot`

then commit `docs: add live links` and push both the repo and, if needed,
re-run the deploy script so the Space's README link matches.

## 6. Verify (5-minute reviewer path)

1. Open the Space URL — app loads, OFFLINE badge visible, no setup.
2. Click all 8 one-click examples — every one renders a valid brief; the
   injection example shows the security banner and stays on task.
3. Add the key secret (if you enabled Live mode) and re-run one example —
   badge switches to LIVE GLM with latency/tokens.
4. GitHub: CI turns green within ~5 minutes (lint, tests, offline eval smoke,
   determinism check, secret scan).
5. `git log --oneline` reads as a clean story.
