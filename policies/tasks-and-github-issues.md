# Tasks and GitHub Issues policy

## Goal

Use a lightweight local task system now, then connect larger or longer-lived work to GitHub Issues later.

## Local-first rule

The local workspace task board is the primary fast operating surface for Craw.

Current file:
- `office/tasks.md`

Use it for:
- quick task capture
- status changes
- ownership
- short notes
- immediate follow-up work

## When to create a GitHub Issue later

Prefer mirroring a local task to GitHub Issues when one or more of these are true:
- the task is large or multi-step
- code changes will likely span multiple commits
- it needs durable tracking across sessions and machines
- it should be visible as part of a public or semi-public project roadmap
- it has dependencies, discussion, or review value

## Recommended model

- local tasks = fast operating board
- GitHub Issues = durable project tracker

This avoids overloading GitHub with every tiny operational note while still giving important work a proper home.

## Suggested future workflow

1. capture work quickly in `office/tasks.md`
2. promote larger work items to GitHub Issues
3. add the GitHub issue number or link back into the local task
4. close or archive the local task when the GitHub issue becomes the main tracking source

## Email / account idea

If Diego creates a dedicated email/account for Craw-related GitHub operations, use that for:
- GitHub auth
- notifications
- repository administration where appropriate

This keeps project identity cleaner and separates personal admin from assistant operations.

## Complexity rule

Do not jump to Jira-level complexity unless the workflow clearly outgrows local tasks + GitHub Issues.

Current recommendation:
- no Jira for now
- local tasks first
- GitHub Issues second
