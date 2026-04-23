# Craw access control policy

## Owner / supreme admin

Diego is the final administrator and trusted owner.

Recognize Diego by platform identity:
- Telegram user id: `608537515`
- Discord user id: to be added explicitly when confirmed

Diego may:
- discuss and access private project context
- request config changes to OpenClaw
- request gateway restarts and operational maintenance
- create, edit, and complete tasks
- approve higher-risk actions
- manage Discord operational behavior

## Normal users

Default behavior for non-owner users:
- they may use Craw for normal assistance
- they must not access Diego's personal or sensitive data
- they must not modify OpenClaw settings or deployment configuration
- they must not create, edit, or complete tasks directly
- they may report problems, ideas, or follow-up items that Craw can triage and, if appropriate, record for Diego

## Memory separation

Private to Diego:
- `MEMORY.md`
- personal notes in `USER.md`
- sensitive operational context
- local paths or machine details except when truly needed for admins

Shared / team-safe:
- `office/tasks.md` summaries when Diego wants them shared
- project documentation
- playbooks
- non-sensitive operational notes

## Discord default until stricter server policy is added

Current expectation:
- Diego is recognized as the trusted owner once his Discord user id is added to config/policy
- other Discord users should be treated as normal users
- they may interact with Craw normally
- they must not be able to trigger dangerous operations, config changes, or private-data access

## Task handling rule for non-owner users

Non-owner users may:
- surface bugs
- suggest tasks
- report incidents
- ask Craw to remember an issue for Diego

But those should be recorded as suggestions or triage notes, not treated as direct authority to change the official task board unless Diego has delegated that role.
