---
name: schema-checker
description: Checks a migration against the staging schema before review
tools: Read, Grep
mcpServers:
  - schema-tools:
      type: stdio
      # ruleid: project-mcp-server-no-prompt-subagent
      command: uv
      args: ["run", "tools/schema_mcp.py"]
      env:
        SCHEMA_DIR: db/schema
  # ruleid: project-mcp-server-no-prompt-subagent
  - fixtures: { type: stdio, command: "node", args: ["scripts/fixtures-mcp.mjs"] }
  - docs:
      type: http
      # ok: project-mcp-server-no-prompt-subagent
      url: https://mcp.example.com/docs
  # ok: project-mcp-server-no-prompt-subagent
  - github
  - scratch:
      # command: ./old-server.sh
      # ok: project-mcp-server-no-prompt-subagent
      command: ""
# Added for the release checks.
  - release-tools:
      # ruleid: project-mcp-server-no-prompt-subagent
      command: node
      args: [scripts/release-mcp.mjs]
hooks:
  PostToolUse:
    - matcher: "Read"
      hooks:
        - type: command
          # ok: project-mcp-server-no-prompt-subagent
          command: echo done
---

Compare each new migration under `db/migrations/` with the staging schema and list any column
that is dropped or renamed. The tool server's `command: uv` setting lives in the frontmatter.
