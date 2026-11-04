---
name: db-reviewer
description: Reviews migrations against the staging schema
tools: Read, Grep, Bash
mcpServers:
  - staging-db:
      type: http
      url: https://mcp.example.com/staging-db
      # ruleid: agent-frontmatter-command-runs-local-script
      headersHelper: node scripts/mcp-db-headers.mjs
  - docs: { type: http, url: "https://mcp.example.com/docs", headersHelper: /opt/bin/docs-headers }
  - local-tools:
      type: stdio
      # ok: agent-frontmatter-command-runs-local-script
      command: ./mcp/tools-server.sh
# Metrics, added for the dashboard review.
  - metrics:
      type: http
      url: https://mcp.example.com/metrics
      # ruleid: agent-frontmatter-command-runs-local-script
      headersHelper: bash scripts/metrics-headers.sh
  - github
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: node
          # ruleid: agent-frontmatter-command-runs-local-script
          args: [".claude/hooks/check-migration.js", "--strict"]
        - type: command
          args:
            # ruleid: agent-frontmatter-command-runs-local-script
            - ${CLAUDE_PROJECT_DIR}/scripts/sql_guard.py
            # ok: agent-frontmatter-command-runs-local-script
            - --quiet
          timeout: 20
          command: python3
        - type: command
          command: npx
          # ok: agent-frontmatter-command-runs-local-script
          args: ["prettier@3.6.2", "--check", "migrations/0042_add_index.sql.js"]
        - type: command
          command: node
          # ok: agent-frontmatter-command-runs-local-script
          args: ["--version"]
  Stop:
    - hooks:
        - type: command
          command: bash
          args:
          # ruleid: agent-frontmatter-command-runs-local-script
          - .claude/hooks/summarize.sh
# Lock check before each session.
  SessionStart:
    - hooks:
        - type: command
          command: python3
          # ruleid: agent-frontmatter-command-runs-local-script
          args: ["scripts/lock_check.py"]
---

Review each migration for locking and rollback safety.
