---
name: notes-librarian
description: Files meeting notes into the team notes folder
tools: Read, Grep
mcpServers:
  - files:
      type: stdio
      command: npx
      # ruleid: mcp-filesystem-root-too-broad-subagent
      args: ["-y", "@modelcontextprotocol/server-filesystem@2.0.0", "~"]
  - archive:
      type: stdio
      command: npx
      args:
        - -y
        - "@modelcontextprotocol/server-filesystem@2.0.0"
        - ./notes
        # ruleid: mcp-filesystem-root-too-broad-subagent
        - /Users/fixture-user
  # ruleid: mcp-filesystem-root-too-broad-subagent
  - disk: { type: stdio, command: mcp-server-filesystem, args: ["/"] }
  - container:
      command: docker
      args:
        - run
        - -i
        - --rm
        - -v
        # ruleid: mcp-filesystem-root-too-broad-subagent
        - /home/fixture-user:/projects/home
        - mcp/filesystem:1.0.2
        - /projects
  - shell:
      command: bash
      args:
        - -c
        # ruleid: mcp-filesystem-root-too-broad-subagent
        - npx -y @modelcontextprotocol/server-filesystem@2.0.0 /home
  - flow-shell:
      command: sh
      # ruleid: mcp-filesystem-root-too-broad-subagent
      args: [-c, npx -y @modelcontextprotocol/server-filesystem@2.0.0 /Users]
  - unexpanded:
      command: npx
      # ok: mcp-filesystem-root-too-broad-subagent
      args: ["-y", "@modelcontextprotocol/server-filesystem@2.0.0", "${HOME}"]
  - null-home:
      command: npx
      # ok: mcp-filesystem-root-too-broad-subagent
      args: [-y, "@modelcontextprotocol/server-filesystem@2.0.0", ~]
  - project:
      command: npx
      # ok: mcp-filesystem-root-too-broad-subagent
      args: ["-y", "@modelcontextprotocol/server-filesystem@2.0.0", "./notes", "~/notes"]
  - other:
      command: npx
      # ok: mcp-filesystem-root-too-broad-subagent
      args: ["-y", "@example-org/notes-mcp@1.4.0", "/"]
  # ok: mcp-filesystem-root-too-broad-subagent
  - github
hooks:
  PostToolUse:
    - matcher: "Read"
      hooks:
        - type: command
          # ok: mcp-filesystem-root-too-broad-subagent
          command: npx -y @modelcontextprotocol/server-filesystem@2.0.0 /
---

File each new meeting note under `notes/` by date. The `files` server's `"~"` argument lives in the
frontmatter.
