# Interview Framing

This is a portfolio-level project.

It explores how AI agents can safely interact with sports business systems through
a governed access layer. The agent does not directly access everything. Instead,
the gateway checks permissions, risk level, approval requirements, and audit
logging before executing tools.

The fictional sports organization is Northstar Athletics.

This project does not use real client data or real ticketing APIs.

The key idea is controlled agent access:

- permissioned tools
- audit trails
- human approval
- safe action boundaries

This connects to sports workflows like ticketing, fan support, content search, and
venue policies.

## What to emphasize

1. **Governance over raw model output.** The interesting engineering isn't the
   agent picking a tool — it's the gateway deciding whether that tool call is
   allowed, how risky it is, and whether a human must sign off.
2. **Fail-closed defaults.** Unknown tools are denied and treated as high risk.
3. **Everything is logged.** Even blocked calls produce an audit record, which is
   what makes the system auditable.
4. **Human-in-the-loop.** High-risk actions (like a ticket hold) become approval
   requests instead of executing silently.
5. **Clean separation of concerns.** Tools contain no policy; the gateway contains
   all policy; the API layer just wires HTTP to the gateway.

## What this project deliberately does not claim

- It is not a production client system.
- It does not use real sports team, league, or venue data.
- It does not integrate with real ticketing or CRM systems.
- It does not require Claude, OpenAI, or any paid API in version 1.

## Likely follow-up questions and answers

**How would you add a real LLM agent?** Replace the deterministic keyword router
in `route_agent_message` with an LLM tool-calling loop. The governance layer
(`execute_tool_call`) stays identical — the model proposes tool calls, the gateway
still authorizes, risk-scores, gates, and logs them.

**How would you scale the data layer?** Swap SQLite for PostgreSQL via
`DATABASE_URL`, and move the flat JSON business data behind real service clients.
The tool interfaces don't change.

**How do you prevent privilege escalation?** Roles map to tools in one registry;
there is no code path that executes a tool without first passing
`is_tool_allowed`, and unknown tools fail closed.
