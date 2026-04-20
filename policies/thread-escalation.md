# Thread escalation policy

## Goal

Move long-running topics out of the main channel before they bloat context and become hard to resume.

## Trigger rule

When Diego sends roughly a third consecutive message about the same topic, treat that as a strong signal that the topic should move into a thread, especially when:
- the subject is clearly ongoing
- multiple troubleshooting steps are involved
- decisions, logs, or follow-up actions are accumulating
- the discussion would be easier to resume later if isolated

## Desired behavior

1. identify the topic succinctly
2. create a thread under the current text channel
3. use a short generic title based on the problem or task
4. seed the thread with a compact recap of the recent relevant exchange
5. continue the deeper work in the thread when operationally possible

## Example thread title patterns
- Discord capability debug
- ComfyUI backend setup
- Dishwasher error E-18
- GitHub integration setup
- Office workflow planning

## Implementation note

Until native in-session Discord thread management is fully stable, use the most reliable available operational path:
- native Discord tool when exposed
- delivery flow when suitable
- `scripts/discord_admin.py` or a future wrapper when required

## Context handling rule

When the thread is created, treat it as the preferred container for:
- recap of the problem
- current hypotheses
- pending steps
- results and decisions

The parent channel should keep only the lighter, high-level traffic where possible.
