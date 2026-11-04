# ts-ci-fixer (testbed)

**Intentionally vulnerable.** A small Node service used to test `cline-ai-rules` against
TypeScript that looks like a real project. Do not deploy it or copy patterns from it.

When CI fails on a pull request, a webhook starts a Claude Agent SDK session in a checkout of
the branch to propose a fix. Other agents review pull requests, keep the docs in step after a
merge, and answer `/bot` comments with a plan-then-apply session.

Every payload is inert: prompts point at folders that do not exist, hosts use `example.com`,
and there are no real credentials. Expected findings are listed in `expectations.yaml`.

## Layout

| Path | What it does |
| --- | --- |
| `src/index.ts` | Webhook server that routes events to the agents |
| `src/config.ts` | Environment-driven settings |
| `src/integrations.ts` | Registry and Sentry endpoints and the tokens the agents use for them |
| `src/runnerLogs.ts` | Starts the team's Python fastmcp CI log server on a self-hosted runner for a fix run, or as a stdio child locally |
| `src/agentOptions.ts` | Shared `Options` builder |
| `src/toolsets.ts` | Tool lists the agents share (read-only, deploy triage) |
| `src/permissions.ts` | Tool gate and mode checks |
| `src/tools/` | AI SDK tools for the triage agent that reads a failed run (test filter, log search, git history, flake tracker, past runs from the CI history database) |
| `src/agents/` | One module per agent: CI fixer, PR reviewer, docs sync, plan-then-apply session, changelog, release publisher (`release.ts`), deploy triage (`triage.ts`), a failure reproducer that runs a model-written script (`repro.ts`), a verify step that runs the command a session suggests (`verify.ts`), and a flaky-test classifier that runs model-written matchers in vm2 (`flaky.ts`) |
| `src/agents/quarantine.ts` | Nightly flaky-test quarantine agent with pre-approved MCP tools |
| `src/agents/incident.ts` | Deploy incident responder on the OpenAI Agents SDK with hosted MCP servers (runbooks, deploy history, incidents, release train, feature flags), run-context instructions, and a health-check tool |
| `src/agents/postmortem.ts` | Postmortem drafter on the OpenAI Agents SDK whose instructions function reads the incident's status-page updates, with a deploy-log tool, and a customer status digest that builds one agent per open incident |
| `src/agents/statusNotes.ts` | Status-page notes for CI outages posted through the Responses API's hosted MCP tool |
| `src/agents/foundryTriage.ts` | Build-failure triage agent on Azure AI Foundry Agent Service (`@azure/ai-agents`) with pipeline and artifact MCP servers |
| `src/agents/backlog.ts` | Flaky-test backlog groomer on LangChain.js with human-in-the-loop review |
| `test/` | Vitest tests |
| `.github/workflows/` | The fixer as a `workflow_run` job, `/bot` comment commands, and agent reviews of fork pull requests in Actions |
| `.vscode/mcp.json`, `.windsurf/mcp_config.json`, `.zed/settings.json` | MCP servers the team's editors connect to (CI log search, flake history, a runner debug endpoint; Zed calls them context servers); the Windsurf file is a shared copy of `~/.codeium/windsurf/mcp_config.json` |
| `.kiro/settings/mcp.json`, `.cursor/permissions.json` | Kiro's MCP servers with auto-approved tools, and Cursor's repository MCP allowlist |
| `.claude/agents/flake-hunter.md` | Claude Code subagent that reruns a failing test, with its own MCP servers (CI history, a browser, the runner debug endpoint, Sentry) |
| `.claude/settings.json`, `.claude/skills/fetch-ci-log/`, `.cursor/cli.json`, `.gemini/settings.json`, `.codex/rules/`, `opencode.json`, `.opencode/agent/`, `.vscode/settings.json`, `scripts/summarize-run.sh`, `src/agents/cliFallback.ts` | Each agent client's command allow list for the fix loop (tests, git, and pulling a failed run's log) |
| `.github/hooks/ci-fixer.json`, `.codex/hooks.json` | Approval hooks for the fix loop: a Copilot `preToolUse` hook that allows every shell command and a `permissionRequest` hook that allows edits (read-only and HTTP policy hooks beside them), and a Codex `PermissionRequest` hook that allows shell commands and patches (plus a `PreToolUse` allow ported from Claude Code, which Codex ignores) |
| `ci-fixer.code-workspace` | VS Code workspace for the service and the docs preview, with the team's terminal auto-approve rules (and VS Code's built-in ones switched off) |
| `ops/flake-bisect/` | Editor settings contributed with the flake bisect helper |
| `.github/workflows/deep-review.yml` | Claude Code ultrareview of labeled pull requests, of the built tree, and on a maintainer's `/ultrareview` comment |
| `src/a2a/` | The fixer as an A2A agent for other agents in the org (`server.ts`), and the runner-facing release server that checks a runner token (`releaseServer.ts`, `runnerTokens.ts`) |
