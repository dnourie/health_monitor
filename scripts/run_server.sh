#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

export PATH="$HOME/miniforge3/bin:$HOME/opt/anaconda3/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
export STREAMLIT_SERVER_HEADLESS=true
export STREAMLIT_SERVER_ADDRESS=127.0.0.1
export STREAMLIT_SERVER_PORT="${STREAMLIT_SERVER_PORT:-8501}"
PYTHON_BIN="${HEALTH_MONITOR_PYTHON:-python3}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "python3 was not found. Install Python, then run: pip install -r requirements.txt"
  exit 1
fi

if ! "$PYTHON_BIN" -m streamlit --version >/dev/null 2>&1; then
  echo "Streamlit is not installed for python3."
  echo "From this folder, run: pip install -r requirements.txt"
  exit 1
fi

exec "$PYTHON_BIN" -m streamlit run app.py
