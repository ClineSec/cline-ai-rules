# ts-mcp-workspace (testbed)

**Intentionally vulnerable.** A small TypeScript MCP server used to test `cline-ai-rules`
against MCP server code that looks like a real project. Do not deploy it, connect a client to
it, or copy patterns from it.

`workspace` gives a coding agent tools for one project checkout: git history and branches,
code search, npm scripts and tests, package installs, fetching a URL into the workspace,
searching a local cache of the project's issues, and snippet sharing adapted from a community
server.
`src/compat/` serves the same tools to clients pinned to the 1.x SDK through its low-level
`Server`, and `src/agent/` runs a review agent with in-process tools on the Claude Agent SDK,
plus changelog, issue-triage, migration-planning, docs-tagging, and dependency-research agents
on the AI SDK, the OpenAI Agents SDK, LangGraph.js, LangChain.js, and Mastra, with step caps at,
above, and far above each framework's default.

Every payload is inert: commands are harmless, hosts use `example.com` or `.invalid`, package
names use `example-org`, and there are no real credentials. Expected findings are listed in
`expectations.yaml`.

## Layout

| Path | What it does |
| --- | --- |
| `src/index.ts` | Builds the `McpServer` (`@modelcontextprotocol/server` 2.x) and connects stdio |
| `src/http.ts` | Streamable HTTP entrypoint on `createMcpExpressApp` for the browser IDE container |
| `src/hosted.ts` | The hosted deployment behind OAuth (`requireBearerAuth`) |
| `src/config.ts` | Environment-driven settings |
| `src/review.ts`, `src/sampling.ts` | A second server for the PR review panel that drafts comments and titles with the client's model (MCP sampling) through an `askHost` helper |
| `src/tools/` | One `register*Tools(server)` module per tool group |
| `src/tools/diagnostics.ts` | Support-bundle, CI-context, and settings tools, plus the same lookups as AI SDK tools for the in-process agents |
| `src/compat/lowlevel.ts` | The 1.x low-level `Server` with a `CallToolRequestSchema` handler |
| `src/compat/http.ts` | The 1.x `McpServer` over streamable HTTP on a bare Express app, for the old desktop client |
| `src/agent/reviewer.ts` | Review agent with in-process MCP tools |
| `src/agent/changelog.ts` | Changelog and release-notes agents on the AI SDK's `ToolLoopAgent` |
| `src/agent/issue-triage.ts`, `src/agent/issue-cache.ts` | Issue router and labelers on the OpenAI Agents SDK, reading the local issue cache |
| `src/agent/migration-graph.ts` | LangGraph.js planner that plans one package upgrade per step |
| `src/agent/doc-indexer.ts` | Docs tagger on LangChain's classic `AgentExecutor` |
| `src/agent/research.ts` | Dependency upgrade researcher on Mastra |
| `test/` | Vitest tests |
| `.mcp.json`, `.vscode/mcp.json`, `.cursor/mcp.json`, `workspace-mcp.code-workspace`, `.claude/agents/tool-diff.md` | Client configs that run `workspace-mcp` next to reference filesystem servers for comparing tool output; some of them are rooted far too broadly |
| `.roo/mcp.json`, `.zed/settings.json`, `.devcontainer/devcontainer.json`, `.github/mcp.json`, `opencode.jsonc`, `.kilo/kilo.jsonc` | The same server for Roo Code, Zed, the dev container, Copilot CLI, opencode, and Kilo, with switched-off and hosted twins |
