# Tasks

This is the primary local task board for Craw's ongoing work.

## How to use
- Add tasks when Diego asks for a new objective, fix, or follow-up.
- Move tasks between sections instead of duplicating them.
- Keep titles short and action-oriented.
- Add owner, priority, and links when useful.
- When a task changes state and it has a GitHub issue link, verify the matching issue on GitHub and update it with a comment, closure, or reopening as appropriate.
- This file stays the fast local operating board while bigger items are mirrored to GitHub.

---

## Inbox

- [ ] Define the first GitHub connection plan
  - owner: Craw
  - priority: high
  - notes: decide repo strategy, auth path, and issue workflow

- [ ] Decide the default Discord operational model
  - owner: Craw
  - priority: high
  - notes: native tool vs script workaround vs discord-ops routing

- [ ] Define the morning task recap flow on Telegram
  - owner: Craw
  - priority: medium
  - notes: use @Arteemisbot as the preferred delivery surface when the reminder/report path is stable
  - links: GitHub issue #4

---

## Todo

- [ ] Prototype a voice-first conversational interface with intelligent turn-taking
  - owner: research
  - priority: high
  - notes: first target is the main bot (Craw) joining a Discord voice channel on request and holding natural spoken conversation with VAD, STT, TTS, and better end-of-turn detection before any multi-bot expansion
  - links: GitHub issue #5

- [ ] Route or operationalize `discord-ops`
  - owner: discord-ops
  - priority: high
  - notes: Discord auth/config is now healthy, but channel runtime still shows intermittent `incomplete turn detected` failures tied to the manager-office session. Clean restart currently clears the stuck state, and a daily 04:00 clean restart is scheduled as mitigation while root cause is investigated.
  - links: `office/open-loops.md`, GitHub issue #1

- [ ] Configure a valid native ComfyUI provider block in OpenClaw
  - owner: design
  - priority: high
  - notes: requires workflow JSON + prompt node details

- [ ] Migrate ComfyUI generation workload from the Mac to Diego's Windows workstation
  - owner: design
  - priority: high
  - notes: planned future move for heavy GPU/CPU/RAM image generation; wait for Diego-side setup steps and confirmations before execution
  - links: GitHub issue #2

- [ ] Add a purpose-built task command/update routine
  - owner: coding
  - priority: medium
  - notes: allow add/update/complete task requests cleanly from chat

- [ ] Add a Discord admin helper for author-based cleanup
  - owner: coding
  - priority: medium
  - notes: allow delete-bot-messages or delete-messages-by-author without manual ID collection

- [ ] Stabilize the thread-escalation automation using the Discord workaround path
  - owner: thread-agent
  - priority: high
  - notes: after about 3 consecutive topic-related messages in the same channel, ask whether to open a dedicated thread; on approval, create the thread in that channel and recap the trigger context, usually the last ~3 relevant messages, before continuing there when appropriate

- [x] Connect the workspace to GitHub and prepare issue mirroring
  - owner: coding
  - priority: high
  - notes: workspace connected to GitHub repo `missionarteemis-cloud/CrawOffice`; auth and remote verified on 2026-04-22. Future issue-mirroring automation can be tracked separately if needed.
  - links: GitHub issue #3

- [ ] Review Discord security posture for open group policy with elevated tools
  - owner: Craw
  - priority: high
  - notes: `openclaw status` reported critical warnings; needs a safer long-term configuration

---

## Doing

- [ ] Build the local todo and roadmap workflow
  - owner: Craw
  - priority: high
  - notes: establish the file structure before linking GitHub Issues

---

## Blocked

- [ ] Stabilize native Discord structural control in chat session
  - owner: discord-ops
  - priority: medium
  - notes: current workaround scripts are effective, but native tool exposure is still inconsistent. Also track Discord channel session instability, websocket reconnects/invalid-session events, and `incomplete turn detected` failures that can require a clean restart.

- [ ] Make Telegram the reliable escalation/notification path for ambiguous higher-risk script requests
  - owner: discord-ops
  - priority: medium
  - notes: desired policy exists, but delivery flow should be stabilized before depending on it operationally

---

## Parking lot / future-facing

- [ ] Define Craw personality more explicitly in a durable way
  - owner: Craw
  - priority: low
  - notes: voice, temperament, habits, and principles should be refined after more workflow foundations are stable

- [ ] Evaluate ephemeral/private Discord response flows
  - owner: discord-ops
  - priority: low
  - notes: may require slash-command or interaction-based path

---

## Done

- [x] Create office memory files
  - owner: Craw

- [x] Add thread escalation policy
  - owner: Craw

- [x] Extend Discord workaround with thread creation
  - owner: coding

- [x] Extend Discord workaround with message read/delete and rate-limit-aware bulk delete
  - owner: coding

- [x] Add daily 04:00 clean restart mitigation for Discord/OpenClaw stability
  - owner: Craw
  - notes: script at `scripts/openclaw_daily_clean_restart.sh`, scheduled via cron. Intended as mitigation for Discord session/runtime instability until root cause is fixed.
