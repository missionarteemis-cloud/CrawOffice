# provider-watchdog

Monitors the primary AI provider before each agent run and automatically switches to OpenRouter if OpenAI is unreachable.

## What it does

- Before each agent response, tests if OpenAI is reachable with a lightweight HEAD request
- If OpenAI is down (5xx or timeout), switches `agents.defaults.model.primary` to `openrouter/auto` and notifies Diego
- When OpenAI comes back, silently restores the primary provider
- Throttled to check at most once per minute to avoid overhead

## Events

- `message:received` — triggers before the agent processes an incoming message
- `agent:start` — triggers before the agent run begins

## Messages sent to user

- `⚡ OpenAI non risponde — switchato su OpenRouter. Riprova ora.` — when switching to fallback
- `⚠️ Watchdog: switch provider fallito` — if the switch command itself fails

## Config

No additional config required. Reads provider names from hardcoded constants:
- Primary: `openai-codex/gpt-5.4`
- Fallback: `openrouter/auto`
