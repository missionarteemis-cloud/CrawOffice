# Discord channel session reset

## Why this exists

Sometimes Discord config is fixed, the gateway is restarted, but the active channel session still behaves with the old activation mode, such as `mention` instead of `open`.

In that case, the channel session itself may need to be recreated.

## Goal

Force OpenClaw to stop using the stale Discord channel session and create a fresh one from the current config.

## Identify the current channel session

Check session status from the active chat or inspect the session registry.

Typical session key pattern:
- `agent:main:discord:channel:<channel_id>`

Current known example:
- `agent:main:discord:channel:1495429637944119348`

The session registry is stored in:
- `~/.openclaw/agents/main/sessions/sessions.json`

The current session file path is typically something like:
- `~/.openclaw/agents/main/sessions/<session-id>.jsonl`

## Soft reset procedure

Use this first.

1. Confirm desired config is already correct in `~/.openclaw/openclaw.json`
   - `channels.discord.enabled = true`
   - `channels.discord.groupPolicy = "open"`
2. Restart the gateway:

```bash
openclaw gateway restart
```

3. Wait a few seconds.
4. Send a normal non-mention message in the target Discord channel.
5. Check whether the new behavior is open instead of mention.

If the session still reports `Activation: mention`, move to hard reset.

## Hard reset procedure

Use this when the session clearly remains stale.

### Safe idea

Back up the session registry, remove the affected channel session entry, then restart the gateway so OpenClaw creates a fresh session for the channel.

### Suggested sequence

1. Stop or restart the gateway so nothing is actively writing.
2. Back up the session registry:

```bash
cp ~/.openclaw/agents/main/sessions/sessions.json ~/.openclaw/agents/main/sessions/sessions.json.bak
```

3. Edit `sessions.json` and remove the specific key for the stale Discord channel session:
- `agent:main:discord:channel:1495429637944119348`

4. Optionally move the linked session transcript file out of the way instead of deleting it:

```bash
mv ~/.openclaw/agents/main/sessions/<session-id>.jsonl ~/.openclaw/agents/main/sessions/<session-id>.jsonl.bak
```

If a matching lock file exists and the gateway is stopped, move that too:

```bash
mv ~/.openclaw/agents/main/sessions/<session-id>.jsonl.lock ~/.openclaw/agents/main/sessions/<session-id>.jsonl.lock.bak
```

5. Start or restart the gateway.
6. Send a fresh message in the Discord channel.
7. Verify the new session picks up the correct activation behavior.

## Where you can launch this from

### 1. Terminal on the Mac
Best option for reliability.

Use when:
- you want direct control
- you need to edit `sessions.json`
- you may need to move session files safely

### 2. From chat by asking Craw to guide you
Good when you want step-by-step help.

Use when:
- you want help identifying the exact session key
- you want me to tell you the next command only after each step
- you want a safer assisted reset

### 3. Via future maintenance scripts
Good once the workflow stabilizes.

Possible future helper commands:
- `scripts/reset-discord-channel-session.sh <channel-id>`
- a small documented maintenance routine for Discord recovery

This is worth adding later if Discord session drift happens more than once.

## Recommended operating pattern

- try soft reset first
- use hard reset only when session status keeps showing the wrong activation mode
- back up session metadata before editing it manually
- move files aside instead of deleting them when possible

## Verification checklist

After reset, confirm:
- Craw reads the channel without requiring a tag
- session status no longer shows `Activation: mention`
- replies behave normally in the intended channel
