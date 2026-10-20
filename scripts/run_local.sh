#!/usr/bin/env bash
# run_local.sh — run the Cynbit Discovery Copilot demo locally (Streamlit).
#
# Offline Mode by default: zero keys, zero network. One-click examples replay
# real precomputed live-LLM outputs; every other input uses the deterministic
# engine. Nothing leaves your machine.
#
# Live mode: either paste a Groq key in the app sidebar (never persisted), or
# copy .env.example to .env and set GROQ_API_KEY (https://console.groq.com/keys).
#
# Usage:   bash scripts/run_local.sh     (from anywhere; it cds to repo root)

set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d .venv ]; then
  echo "Creating virtual environment (.venv)…"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

# Load .env if present (never committed — see .gitignore).
if [ -f .env ]; then
  set -a; source .env; set +a
  echo ".env loaded (LLM_PROVIDER=${LLM_PROVIDER:-auto})"
fi

echo ""
echo "  Demo UI  → http://localhost:8501"
echo "  Mode     → offline by default; sidebar switch enables live Groq (BYOK)"
echo ""
python -m streamlit run app/streamlit_app.py
