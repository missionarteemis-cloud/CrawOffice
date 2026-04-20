# Open loops

Track active problems, unresolved tasks, and follow-ups that should not live only in chat.

## Current

### Discord operations / capability gap
- Problem: the current conversational Discord session can talk, but does not expose full structural Discord control directly.
- Known status:
  - cross-channel log delivery works through `openclaw agent --deliver`
  - direct structural actions from the chat session are still limited
  - workaround script `scripts/discord_admin.py` can perform direct Discord admin actions via API
  - `discord-ops` agent exists but is not yet fully routed into the normal workflow
- Next steps:
  - decide whether to formalize `discord_admin.py` as the default Discord admin path
  - decide whether `discord-ops` should wrap that script or become a true routed agent for Discord operations

### ComfyUI as primary image backend
- Problem: workspace policy now says ComfyUI is the primary image backend, but OpenClaw provider config is not yet fully wired as a valid native `comfy` provider block.
- Known status:
  - workspace policy updated
  - invalid partial config was reverted to keep OpenClaw healthy
- Next steps:
  - identify the exact workflow JSON and prompt node for the default ComfyUI image path
  - write a valid `models.providers.comfy` config when the workflow details are known

### Thread-based long-topic handling
- Problem: long conversations should move into a Discord thread instead of bloating the parent channel context.
- Goal:
  - when a topic reaches roughly the third consecutive message and is clearly continuing, create a thread under the current text channel
  - title it with a generic problem/topic label
  - seed it with a short recap or the latest relevant exchanged context
- Next steps:
  - use the Discord admin workaround path until native in-session thread control is stable
  - define naming conventions for new threads
