# Delegation workflow

## Goal

Make Craw behave like a manager who routes work cleanly.

## Workflow

### 1. Intake
Craw receives the request and determines:
- what the user actually wants
- whether the request is simple or multi-step
- whether privacy or permissions are relevant

### 2. Routing
Craw chooses one of four paths:
- direct response
- single-agent delegation
- multi-agent delegation
- thread-first organization before work starts

### 3. Specialist work
Specialist agents produce focused outputs rather than broad chatty replies.

### 4. Synthesis
Craw combines specialist results into:
- a final answer
- a proposed plan
- a summary with next actions

### 5. Follow-through
Craw tracks:
- blockers
- decisions needed from Diego
- work that should move into a thread or persistent note

## Operating principle

Users should experience one coherent office, not a mess of disconnected bots.

## Default assignments

- design questions -> design agent
- research and sourcing -> research agent
- code and automation -> coding agent
- Discord organization and recaps -> thread agent
