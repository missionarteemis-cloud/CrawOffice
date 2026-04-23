#!/bin/zsh
set -euo pipefail

LOG_DIR="$HOME/.openclaw/logs"
mkdir -p "$LOG_DIR"
STAMP="$(date '+%Y-%m-%d %H:%M:%S %Z')"
{
  echo "[$STAMP] daily clean restart: stop"
  openclaw gateway stop || true
  sleep 3
  echo "[$STAMP] daily clean restart: start"
  openclaw gateway start
  sleep 5
  echo "[$STAMP] daily clean restart: status"
  openclaw status --all
  echo "[$STAMP] daily clean restart: done"
} >> "$LOG_DIR/daily-clean-restart.log" 2>&1
