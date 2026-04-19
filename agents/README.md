# Agents

This folder describes the office roles that Craw orchestrates.

## Operating model

- Craw is the manager and dispatcher.
- Specialized agents do focused work and report back.
- Discord users talk to Craw first; Craw decides whether to answer directly or delegate.
- Skills and plugins are shared system capabilities by default. Agent role files define who should normally use which capability.
- Heavy compute tools may later run on a separate Windows machine without changing the office structure. The execution backend can move while the responsibility stays with the same agent.

## Initial roster

- `manager.md` — intake, triage, delegation, synthesis
- `design-agent.md` — design direction, visual concepts, prompts, branding support
- `research-agent.md` — web research, sourcing, documentation gathering, comparison tables
- `coding-agent.md` — implementation, scripts, refactors, technical fixes
- `thread-agent.md` — Discord thread hygiene, summaries, task routing, archival structure
