#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/com.local.health-monitor.plist"
LOG_DIR="$APP_DIR/logs"
PYTHON_BIN="$(command -v python3)"

mkdir -p "$PLIST_DIR" "$LOG_DIR"

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.local.health-monitor</string>
  <key>ProgramArguments</key>
  <array>
    <string>$APP_DIR/scripts/run_server.sh</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>WorkingDirectory</key>
  <string>$APP_DIR</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>HEALTH_MONITOR_PYTHON</key>
    <string>$PYTHON_BIN</string>
    <key>STREAMLIT_SERVER_PORT</key>
    <string>8501</string>
  </dict>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/health-monitor.out.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/health-monitor.err.log</string>
</dict>
</plist>
EOF

launchctl unload "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl load "$PLIST_PATH"

echo "Health Monitor auto-start is installed."
echo "It will start at login and stay available at http://127.0.0.1:8501"
echo "Logs are in: $LOG_DIR"
