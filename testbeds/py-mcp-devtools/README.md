# py-mcp-devtools (testbed)

**Intentionally vulnerable.** A small Python MCP server used to test `cline-ai-rules` against
MCP server code that looks like a real project. Do not deploy it, connect a client to it, or
copy patterns from it.

`devtools` gives a coding agent read access to a repository checkout and a few operations
helpers: git history and diffs, code search, CI run history, service status, disk usage,
metrics math, and remote host checks over SSH. Build targets run through a second, low-level server. The
`legacy/` server is the pre-2.0 SDK version some teams still run, and `contrib/` holds
community Docker and notes servers built on standalone fastmcp. `deploy/`, `scripts/`, the
`Makefile`, the `Procfile`, and a CI workflow run those contrib servers on the team's shared
build VM.

Every payload is inert: commands are harmless (`git log`, `du -sh`, `uptime`), hosts use
`example.com` or `.invalid`, and there are no real credentials. Expected findings are listed in
`expectations.yaml`.

## Layout

| Path | What it does |
| --- | --- |
| `devtools/app.py` | The shared `MCPServer` instance (MCP Python SDK 2.x) |
| `devtools/server.py` | Entry point: imports the tool modules and runs stdio or HTTP |
| `devtools/tools/` | One module per tool group; `triage.py` drafts CI triage notes with the client's model through `Sample` resolver dependencies |
| `devtools/tools/diagnostics.py` | Support-bundle and runtime tools for debugging a stuck deployment: settings by name, CI context, environment names |
| `devtools/build_server.py` | Low-level `Server` for build targets |
| `devtools/build_http.py` | The build server over streamable HTTP in the toolchain container (SDK session manager) |
| `devtools/dashboard.py` | Read-only status `MCPServer` mounted in a Starlette app for the ops dashboard |
| `devtools/hosted.py` | The shared-cluster deployment behind OAuth (`token_verifier`) |
| `legacy/ops_server.py` | Same ops tools on `mcp.server.fastmcp.FastMCP` (SDK 1.x) |
| `legacy/release_notes.py` | Release-note drafting on 1.x `FastMCP`, asking the client's model through `ctx.session.create_message` (sampling) |
| `legacy/http_server.py` | Read-only status tools on 1.x `FastMCP` over SSE, for the dashboard VM |
| `contrib/docker_server.py` | Docker helpers on standalone `fastmcp` (stdio, or HTTP with `DOCKER_MCP_HTTP=1`) |
| `contrib/notes_server.py` | Team notes copied from a community snippet, on standalone `fastmcp` (not yet reviewed) |
| `contrib/release_agent.py` | Release helper agent on pydantic-ai that drafts the registry login, tag, and push commands (not yet reviewed) |
| `contrib/fastmcp.json`, `contrib/team.fastmcp.json` | `fastmcp run` configs for the notes server: stdio for local clients, HTTP for the team |
| `deploy/` | Contrib image (`contrib.Dockerfile`), compose file, systemd units, and the build VM's environment file |
| `scripts/`, `Makefile`, `Procfile`, `.env.example` | Ways to run the contrib servers locally, for the team, and on a PaaS preview; `scripts/pair_notes.py` starts the notes server for a pairing session |
| `.github/workflows/contrib-smoke.yml` | Builds the contrib image and starts the notes server in CI and on the build VM runner |
| `devtools/preview.py`, `devtools/templates/` | Diagram-preview server: Mermaid source and KaTeX captions rendered to local HTML pages |
| `tests/` | pytest tests that call the tool functions directly |
| `.aider.conf.yml`, `.aider.model.settings.yml` | Aider defaults for the repo: models through the build team's caching gateway, and a local Ollama model for offline work |
