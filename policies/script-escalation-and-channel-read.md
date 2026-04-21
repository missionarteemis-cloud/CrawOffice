# Script escalation and channel-read policy

## Core rule

If a task is blocked by missing native Discord tool exposure but can be solved safely through a local workaround script, prefer the workaround rather than stalling, provided the action is appropriate for the requester.

## Cross-channel read behavior

The Discord admin workaround script is an accepted path for reading messages from a specific channel when needed to retrieve information, inspect state, or carry out cleanup work.

Current accepted mechanism:
- `scripts/discord_admin.py read-messages --channel-id <ID> --limit <N>`

This should be treated as the normal fallback path when native in-session Discord reading is unavailable.

## Authority rule for powerful scripts

Only Diego, or users with Op / administrator authority, should be able to trigger creation or use of particularly powerful scripts that materially expand control over the server, host, or external systems.

Examples of higher-risk scripts:
- broad moderation or deletion tools
- powerful admin automation across many channels
- scripts that expose local host or workspace data
- scripts that send external notifications or messages broadly

## Ordinary-member rule

If an ordinary member asks for a script-backed solution:
- proceed when the script is clearly narrow, safe, and innocuous
- do not proceed blindly when the script would materially expand power or access
- when in doubt, pause and escalate rather than over-building capabilities for a non-admin requester

## Notification preference

When a non-admin request would require a more powerful or more sensitive script and there is uncertainty, prefer notifying Diego privately rather than silently granting that power.

## Design principle

Workarounds are good when they restore legitimate functionality.

They should not become a backdoor for broad privilege expansion for arbitrary users.
