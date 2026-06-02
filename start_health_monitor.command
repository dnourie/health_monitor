#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${STREAMLIT_SERVER_PORT:-8501}"
URL="http://127.0.0.1:${PORT}"

if ! lsof -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  "$APP_DIR/scripts/run_server.sh" &
  SERVER_PID=$!

  for _ in {1..40}; do
    if lsof -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
      break
    fi
    sleep 0.25
  done

  if ! lsof -iTCP:"${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "The Health Monitor server did not start. Check the terminal output above."
    wait "$SERVER_PID"
    exit 1
  fi
fi

open "$URL"
echo "Health Monitor is running at $URL"
echo "Leave this window open while you use the app, or install auto-start with scripts/install_autostart.sh."
wait
