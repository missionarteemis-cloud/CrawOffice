#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHANNEL_ID="1495429637944119348"
AGENT_NAME="main"

exec "$SCRIPT_DIR/reset-discord-channel-session.sh" "$CHANNEL_ID" "$AGENT_NAME"
