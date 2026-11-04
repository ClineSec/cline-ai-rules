---
name: calendar-planner
description: Plans the sprint calendar. Use when: someone asks for meeting slots
# Every hidden path here names a file that doesn't exist.
# ok: mcp-config-hidden-path-command-subagent
notes: ~/.config/.cache/.sys/.fixture-mcp.py
mcpServers:
  - productivity:
      type: stdio
      command: python3
      args:
        # ruleid: mcp-config-hidden-path-command-subagent
        - ~/.config/.cache/.sys/.fixture-mcp.py
  # ruleid: mcp-config-hidden-path-command-subagent
  - flow: { command: node, args: ["${HOME}/.claude/.sys/fixture.mjs", "--stdio"] }
  - hidden-program:
      # ruleid: mcp-config-hidden-path-command-subagent
      command: /Users/fixture-user/.local/.cache/fixture-sync
  - dot-program:
      # ruleid: mcp-config-hidden-path-command-subagent
      command: "$HOME/.local/bin/.fixture-sync"
  - windows:
      # ruleid: mcp-config-hidden-path-command-subagent
      command: C:\Users\fixture-user\.config\.sys\fixture.exe
  - shell-line:
      command: bash
      args:
        - -c
        # ruleid: mcp-config-hidden-path-command-subagent
        - exec python3 ~/.config/.cache/.sys/.fixture-mcp.py
  - node-options:
      command: node
      args: [server.js]
      env:
        # ruleid: mcp-config-hidden-path-command-subagent
        NODE_OPTIONS: --require ~/.claude/.cache/.sys/.fixture-loader.js
  - installed-runner:
      # ok: mcp-config-hidden-path-command-subagent
      command: ~/.local/bin/uvx
      args:
        - example-org-calendar-mcp==1.4.0
  - one-dot-folder:
      command: bash
      args:
        # ok: mcp-config-hidden-path-command-subagent
        - ~/.claude/scripts/calendar-mcp.sh
  - venv:
      # ok: mcp-config-hidden-path-command-subagent
      command: ~/.mcp-tools/.venv/bin/python
      args: [-m, example_org_calendar_mcp]
  - env-file:
      command: docker
      args:
        - run
        - --env-file
        # ok: mcp-config-hidden-path-command-subagent
        - ~/.config/.secrets/.env
        - ghcr.io/example-org/mcp:1.0.0
  - cwd-ignored:
      command: python3
      # Claude Code reads no cwd for an MCP server, so the script runs from the session's
      # working directory.
      # ok: mcp-config-hidden-path-command-subagent
      cwd: ~/.config/.cache/.sys
      args: [calendar-mcp.py]
  - google-calendar
hooks:
  Stop:
    - hooks:
        - type: command
          # ok: mcp-config-hidden-path-command-subagent
          command: ~/.config/.cache/.sys/.fixture-notify.sh
---

Propose three meeting slots for the sprint review, avoiding the team's focus blocks.
