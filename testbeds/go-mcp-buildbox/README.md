# buildbox-mcp

An MCP server that gives coding agents access to a CI build box: the checked-out repository,
the build runner, and the build-history database.

> **Intentionally vulnerable.** This is a cline-ai-rules testbed. Do not deploy it, run it,
> or copy patterns from it.

Two binaries:

| Binary | SDK | Transport | Tools |
| --- | --- | --- | --- |
| `cmd/buildbox` | [mark3labs/mcp-go](https://github.com/mark3labs/mcp-go) v1.3.0 | stdio | `git_log`, `git_diff`, `git_checkout`, `git_fetch`, `git_blame`, `build_search`, `build_stats`, `flaky_tests`, `job_report` |
| `cmd/buildbox-http` | [modelcontextprotocol/go-sdk](https://github.com/modelcontextprotocol/go-sdk) v1.8.0 | Streamable HTTP on `127.0.0.1:8931` | `run_check`, `run_pipeline`, `run_script`, `lint_script`, `tail_log`, `disk_usage`, `env_probe`, `artifact_list` |

## Layout

- `internal/gitops`: git tools over `os/exec` (mcp-go handlers on a `Repo`).
- `internal/history`: build-history queries on Postgres through pgx and sqlx (mcp-go).
- `internal/runner`: build-runner tools (go-sdk typed handlers and one raw handler).
- `internal/artifacts`: artifact listing on gorm (go-sdk).

## Configuration

| Variable | Default | Used by |
| --- | --- | --- |
| `BUILDBOX_REPO` | `/srv/buildbox/repo` | `cmd/buildbox` |
| `BUILDBOX_DATABASE_URL` | `postgres://buildbox@db.example.invalid/history` | both |
| `BUILDBOX_SHELL` | `/bin/bash` | `cmd/buildbox-http` |

## Running in a container

The `ghcr.io/example-org/buildbox-mcp` image holds both binaries.

- `deploy/compose.yaml`: the build-host layout (`buildbox-http`, Postgres, host metrics).
- `deploy/compose.dev.yaml`: the stdio server against your own checkout, for MCP Inspector.
- Client configs that start the stdio server with `docker run`: `.mcp.json` (Claude Code),
  `.continue/mcpServers/buildbox.yaml` (Continue), `.codex/config.toml` (Codex), and
  `buildbox.code-workspace` and `.vscode/mcp.json` (VS Code), `.roo/mcp.json` (Roo Code), and
  `gemini-extension.json` (Gemini CLI). `.claude/agents/container-disk-auditor.md` is a Claude
  Code subagent with its own disk-report server.
- `docs/claude_desktop_config.json`: an example to paste into Claude Desktop. Desktop doesn't
  expand `$HOME`, so the first entry mounts nothing until you put your own home folder in, as
  `buildbox-mac` does.
