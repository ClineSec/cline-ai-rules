# py-helpdesk (testbed)

**Intentionally vulnerable.** A small FastAPI helpdesk assistant used to test `cline-ai-rules`
against code that looks like a real project. Do not deploy it or copy patterns from it.

Every payload is inert: commands are harmless, model and package names use the `example-org`
placeholder, the instruction text targets folders that do not exist, and the model-written
reporting SQL is SELECT-only against a made-up, read-only ticket warehouse. Expected findings are
listed in `expectations.yaml`.

Agent loops on several frameworks sit next to each other, with step caps at, above, and far
above each framework's default: a CrewAI trend-digest crew (`helpdesk/trend_crew.py` and its
`helpdesk/config/agents.yaml`), a LangChain knowledge-base gap finder (`kb_gap_agent.py`), an
OpenAI Agents SDK routing desk (`handoff_desk.py`), an AutoGen reply-review team
(`review_team.py`), an AG2 incident war room (`war_room.py`), a LangGraph backlog sweeper
(`backlog_graph.py`), and a smolagents log digger (`log_digger.py`).

Approval hooks in other clients' formats: a Codex `[[hooks.PermissionRequest]]` table in
`.codex/config.toml` that approves every helpdesk MCP call, a Devin CLI `PermissionRequest`
approve in `.devin/config.json`, and a Claude-format Copilot hook file
(`.github/hooks/ticket-tools.json`) whose read-only matcher VS Code ignores.
