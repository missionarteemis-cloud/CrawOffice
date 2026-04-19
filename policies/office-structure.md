# Office structure

## Core idea

Treat the Discord server as a small digital office.

- Craw is the front desk, manager, and orchestrator.
- Specialized agents handle focused work behind the scenes.
- Threads represent tasks, topics, or workstreams.
- Workspace files hold the durable operating model.

## Working model

1. A user makes a request.
2. Craw decides whether the request is:
   - simple enough to answer directly
   - better handled in a thread
   - best delegated to one specialist agent
   - best split across multiple specialist agents
3. Specialist outputs return to Craw.
4. Craw produces the final response, next steps, or summary.

## Initial specialist roles

- design
- research
- coding
- thread coordination

## Infrastructure model

Plugins and core providers should be treated as shared system infrastructure, not duplicated per agent by default.

Examples:
- Discord integration is a shared system capability.
- OpenAI or other model providers are shared system capabilities.
- A future ComfyUI skill can be shared globally but primarily routed to the design agent.

The agent files describe intended ownership and routing, not hard isolation.

## Future heavy-compute model

If GPU, CPU, or RAM intensive work moves to a Windows workstation on the same network, keep the same office roles and re-point the execution backend.

Example:
- design agent remains the owner of image-generation work
- the actual ComfyUI execution may later happen on the Windows machine
- Craw still orchestrates the job and reports the result back
