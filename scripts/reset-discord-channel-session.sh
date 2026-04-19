#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 <channel-id> [agent-name]" >&2
  echo "Example: $0 1495429637944119348 main" >&2
  exit 1
fi

CHANNEL_ID="$1"
AGENT_NAME="${2:-main}"
BASE_DIR="$HOME/.openclaw/agents/$AGENT_NAME/sessions"
SESSIONS_JSON="$BASE_DIR/sessions.json"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$BASE_DIR/backups/discord-session-reset-$TIMESTAMP"
SESSION_KEY="agent:$AGENT_NAME:discord:channel:$CHANNEL_ID"

if [[ ! -f "$SESSIONS_JSON" ]]; then
  echo "sessions.json not found: $SESSIONS_JSON" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"
cp "$SESSIONS_JSON" "$BACKUP_DIR/sessions.json.bak"

SESSION_ID="$(python3 - "$SESSIONS_JSON" "$SESSION_KEY" <<'PY'
import json, sys
path, key = sys.argv[1], sys.argv[2]
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

found = None

def walk(obj):
    global found
    if isinstance(obj, dict):
        if obj.get('sessionKey') == key and obj.get('id'):
            found = obj['id']
            return
        for v in obj.values():
            if found:
                return
            walk(v)
    elif isinstance(obj, list):
        for item in obj:
            if found:
                return
            walk(item)

walk(data)
if found:
    print(found)
PY
)"

if [[ -z "$SESSION_ID" ]]; then
  echo "No session id found for key: $SESSION_KEY" >&2
  echo "Backup created at: $BACKUP_DIR" >&2
  exit 2
fi

SESSION_FILE="$BASE_DIR/$SESSION_ID.jsonl"
LOCK_FILE="$BASE_DIR/$SESSION_ID.jsonl.lock"

if [[ -f "$SESSION_FILE" ]]; then
  cp "$SESSION_FILE" "$BACKUP_DIR/$SESSION_ID.jsonl.bak"
fi

if [[ -f "$LOCK_FILE" ]]; then
  cp "$LOCK_FILE" "$BACKUP_DIR/$SESSION_ID.jsonl.lock.bak"
fi

python3 - "$SESSIONS_JSON" "$SESSION_KEY" <<'PY'
import json, sys
path, key = sys.argv[1], sys.argv[2]
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

def remove_key(obj):
    if isinstance(obj, dict):
        for k in list(obj.keys()):
            v = obj[k]
            if k == key:
                del obj[k]
                continue
            remove_key(v)
    elif isinstance(obj, list):
        for item in obj:
            remove_key(item)

remove_key(data)
with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
    f.write('\n')
PY

if [[ -f "$SESSION_FILE" ]]; then
  mv "$SESSION_FILE" "$SESSION_FILE.bak.$TIMESTAMP"
fi

if [[ -f "$LOCK_FILE" ]]; then
  mv "$LOCK_FILE" "$LOCK_FILE.bak.$TIMESTAMP"
fi

echo "Reset prepared for $SESSION_KEY"
echo "Session id: $SESSION_ID"
echo "Backup dir: $BACKUP_DIR"
echo
echo "Next step: restart the gateway"
echo "  openclaw gateway restart"
echo
echo "Then send a fresh non-mention message in the target Discord channel."
