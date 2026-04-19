# Plugins and skills

## Short answer

Plugins are usually shared infrastructure for the whole OpenClaw system. Skills are task instructions or local capabilities that can be routed to specific agent roles by policy.

## Practical meaning

- A plugin such as Discord is not normally "inside" one agent folder.
- A provider such as OpenAI is also normally system-level.
- A skill such as a future ComfyUI integration can live in a generic skills location and still be treated as mainly owned by the design agent.

Craw uses routing rules to decide who should use what.

## Role-based ownership without hard duplication

Recommended pattern:
- system-level integrations live in generic OpenClaw config or shared skill locations
- workspace policy files state which role should normally invoke them
- Craw orchestrates and delegates accordingly

## Skills from Discord vs terminal

In principle, yes, skills can be created or edited from chat if Craw has file access, because skills are files and folders.

In practice:
- creating or editing a workspace skill can be done from this chat by writing files in the repo
- installing or wiring external dependencies may still require terminal-side setup
- testing some skills may also require terminal access, service restarts, or config changes

So the answer is: not terminal-only, but terminal is sometimes needed for activation and infrastructure wiring.

## Current recommendation

- define the agent roles and routing policy in the repo first
- add skills in the workspace when needed
- keep plugins and provider config centralized
- let Craw route shared capabilities to the most appropriate agent
