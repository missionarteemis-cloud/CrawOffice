# Decisions

Record durable decisions so repeated chats do not have to rediscover them.

## 2026-04-20

### Discord shared-channel privacy
- Explicit local directory paths from Diego's Mac should not be disclosed to ordinary members in shared channels.
- Only Op or administrator users may receive explicit path details.
- Ordinary members may still receive innocuous environment details such as machine name, OS, architecture, and non-sensitive tool versions.

### Craw office structure
- Craw is the visible manager and orchestrator.
- Initial specialist roles:
  - design
  - research
  - coding
  - thread agent
  - discord-ops

### Commit log format
- Every workspace commit should also be sent to the Discord log channel.
- Format:
  - `hash` - brief description

### Primary image-generation backend
- ComfyUI is the primary image-generation backend for this workspace.
- Cloud image providers are future fallbacks, not the default path.

### Discord operational reality
- Direct structural Discord actions are not reliably available from the conversational channel session.
- Cross-channel posting works more reliably through delivery flows and, when needed, the `discord_admin.py` workaround script.
