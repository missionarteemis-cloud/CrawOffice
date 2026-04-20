# Roadmap

## Phase 1 - operational memory and structure
- [x] define specialist agents and playbooks
- [x] add Discord recovery notes and reset scripts
- [x] add `discord-ops` agent
- [x] define ComfyUI as primary image backend at the workspace policy level
- [x] create office memory files: open loops, decisions, roadmap
- [ ] define the thread-escalation workflow for long topics

## Phase 2 - Discord operations stability
- [ ] decide the primary operational path for Discord admin actions
  - native tool path when available
  - delivery path when appropriate
  - `discord_admin.py` workaround when necessary
- [ ] route or operationalize `discord-ops`
- [ ] stabilize thread creation and channel-management flows
- [ ] clean up the log channel once full read/delete capability is stable

## Phase 3 - image workflow maturity
- [ ] configure a valid native OpenClaw `comfy` provider block
- [ ] set fallback image providers with explicit priority
- [ ] migrate heavy image generation to Diego's Windows workstation

## Phase 4 - repo and external coordination
- [ ] connect the workspace to GitHub
- [ ] use GitHub issues or equivalent for longer-term task tracking
- [ ] document the office workflow publicly in Discord threads/setup posts

## Phase 5 - private/advanced interaction modes
- [ ] evaluate ephemeral or private Discord reply workflows
- [ ] separate safe conversational flows from raw generation or ops flows where useful
