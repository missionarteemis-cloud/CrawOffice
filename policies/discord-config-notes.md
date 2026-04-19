# Discord config notes

## Goal

Keep Discord working in an open server mode without requiring a mention for every message, while preserving the shared-channel privacy rules already defined in the workspace.

## Desired behavior

- Discord channel access should remain enabled.
- Craw should be able to read and reply in the server without requiring an explicit tag every time.
- Shared-channel privacy rules still apply even when the bot can read the channel openly.

## Current direction

The current config is using the newer `channels.discord` section rather than old plugin-specific keys.

Desired shape:

```json
"channels": {
  "discord": {
    "enabled": true,
    "token": "...",
    "groupPolicy": "open"
  }
}
```

This open policy appears to be the setting that restores non-mention behavior.

## What may break it

- running `openclaw doctor --fix`
- OpenClaw upgrades that rewrite channel config
- mixing old `plugins.entries.discord.botToken` or `plugins.entries.discord.channels` keys back into the config

## Recovery checklist

If Discord suddenly only responds when tagged, check:

1. `~/.openclaw/openclaw.json`
2. confirm `channels.discord.enabled` is `true`
3. confirm `channels.discord.groupPolicy` is `"open"`
4. confirm the Discord token is still present in `channels.discord.token`
5. restart the gateway

Recommended restart command:

```bash
openclaw gateway restart
```

## Do not rely on

Older config keys like:
- `plugins.entries.discord.botToken`
- `plugins.entries.discord.channels`

Those appear incompatible with the current OpenClaw config format and may cause validation errors.

## Operating reminder

Open Discord visibility does not mean open data disclosure. Even in open mode, Craw should avoid exposing explicit local directory details to ordinary server members.
