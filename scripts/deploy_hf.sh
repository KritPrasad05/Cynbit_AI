#!/usr/bin/env bash
# deploy_hf.sh — package the app and push it to a Hugging Face Streamlit Space.
#
# Prerequisites (one-time):
#   pip install huggingface_hub
#   huggingface-cli login          # or: export HF_TOKEN=hf_...
#   create a Streamlit Space named e.g. cynbit-discovery-copilot at
#   https://huggingface.co/new-space (SDK: Streamlit, CPU basic, PUBLIC)
#
# Usage:
#   bash scripts/deploy_hf.sh <your-username> <space-name>
#   e.g. bash scripts/deploy_hf.sh johndoe cynbit-discovery-copilot
#
# The Space runs in Offline Mode by default (no secrets needed).
# To enable Live GLM on the Space: Settings → Variables and secrets →
# add secret GLM_API_KEY (and optionally GLM_BASE_URL / GLM_MODEL).
# NEVER commit the key to the repo.

set -euo pipefail

USER_NAME="${1:?usage: deploy_hf.sh <hf-username> <space-name>}"
SPACE_NAME="${2:?usage: deploy_hf.sh <hf-username> <space-name>}"
SPACE_URL="https://huggingface.co/spaces/${USER_NAME}/${SPACE_NAME}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$(mktemp -d)"

echo "Staging into ${STAGE}"

# --- 1. Space README with the required frontmatter -------------------------
cat > "${STAGE}/README.md" << 'EOF'
---
title: Cynbit Discovery Copilot
emoji: 🔎
colorFrom: indigo
colorTo: blue
sdk: streamlit
sdk_version: 1.66.0
app_file: app/streamlit_app.py
pinned: false
license: mit
---

# Cynbit Discovery Copilot (demo)

Turn any inbound inquiry into a structured discovery brief. Runs fully in
Offline Mode with zero keys; add your own GLM key in the sidebar for live
inference. Full project: see the GitHub repository link inside the app.
EOF

# --- 2. Copy app + data + pinned requirements -------------------------------
cd "${REPO_ROOT}"
mkdir -p "${STAGE}/app" "${STAGE}/data/synthetic" "${STAGE}/evals/results"
cp -r app/core app/assets app/streamlit_app.py "${STAGE}/app/"
rm -rf "${STAGE}/app/core/__pycache__"
cp data/synthetic/leads_train.jsonl data/synthetic/leads_eval.jsonl \
   data/synthetic/cached_outputs.json "${STAGE}/data/synthetic/"
cp -r evals/results/* "${STAGE}/evals/results/" 2>/dev/null || true
rm -rf "${STAGE}/evals/results/__pycache__"
cp requirements.txt "${STAGE}/requirements.txt"
touch "${STAGE}/.gitignore"  # keep HF-side clutter out

echo "Staged files:"
find "${STAGE}" -type f | sed "s|${STAGE}/||" | sort

# --- 3. Push to the Space ----------------------------------------------------
git -C "${STAGE}" init -q
git -C "${STAGE}" add -A
git -C "${STAGE}" -c user.name="deploy" -c user.email="deploy@local" \
  commit -qm "deploy: discovery copilot (offline-first)"
git -C "${STAGE}" branch -M main
git -C "${STAGE}" remote add space "https://huggingface.co/spaces/${USER_NAME}/${SPACE_NAME}"
git -C "${STAGE}" push -f space main

echo
echo "Deployed → ${SPACE_URL}"
echo "If you enabled a GLM_API_KEY secret, Live mode will work there too."
