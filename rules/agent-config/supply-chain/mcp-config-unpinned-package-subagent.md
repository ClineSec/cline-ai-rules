---
name: release-notes
description: Drafts release notes. Use when: a release branch is cut and the changelog needs a summary
tools: Read, Grep, mcp__browser__*
mcpServers:
  - browser:
      type: stdio
      command: npx
      args:
        # ruleid: mcp-config-unpinned-package-subagent
        - "@example-org/playwright-mcp@latest"
  - sqlite:
      command: npx
      args:
        - -y # install without asking
        # ruleid: mcp-config-unpinned-package-subagent
        - example-org-mcp-sqlite
        - db/release.db
  # ruleid: mcp-config-unpinned-package-subagent
  - search: { command: "npx", args: ["-y", '@example-org/mcp-search@^2.1.0'] }
  - cli:
      # ruleid: mcp-config-unpinned-package-subagent
      args: [--yes, --package=@example-org/mcp-cli, example-mcp]
      command: npx
# Fetch tools for changelog links.
  - fetch:
      command: uvx
      args:
        - --python
        - "3.12"
        # ruleid: mcp-config-unpinned-package-subagent
        - example-org-mcp-fetch
  - git-tools:
      command: uvx
      args:
        - --from
        # ruleid: mcp-config-unpinned-package-subagent
        - git+https://github.com/example-org/mcp-tools@main
        - example-mcp
  - extras:
      command: uv
      # ruleid: mcp-config-unpinned-package-subagent
      args: [run, --with, example-org-fastmcp, example-fastmcp, run, server.py]
  - kb:
      command: docker
      args:
        - run
        - -i
        - --rm
        # ruleid: mcp-config-unpinned-package-subagent
        - ghcr.io/example-org/kb-mcp:latest
  - wrapped:
      command: bash
      args:
        - -lc
        # ruleid: mcp-config-unpinned-package-subagent
        - source ~/.nvm/nvm.sh && npx -y @example-org/mcp-memory

  - pinned:
      command: npx
      args:
        - -y
        # ok: mcp-config-unpinned-package-subagent
        - "@example-org/playwright-mcp@1.58.0"
  - pinned-plain:
      command: uvx
      args:
        # ok: mcp-config-unpinned-package-subagent
        - example-org-mcp-fetch==2026.4.7
  - local:
      command: uv
      args:
        - run
        # ok: mcp-config-unpinned-package-subagent
        - tools/release_mcp.py
  - docs:
      type: http
      # ok: mcp-config-unpinned-package-subagent
      url: https://mcp.example.com/mcp
  # ok: mcp-config-unpinned-package-subagent
  - github
hooks:
  Stop:
    - hooks:
        - type: command
          command: npx
          # ok: mcp-config-unpinned-package-subagent
          args: ["-y", "example-org-notify"]
---

Summarize the merged pull requests since the last tag. A server defined in this body is not
loaded:

mcpServers:
  - example:
      command: npx
      # ok: mcp-config-unpinned-package-subagent
      args: [example-org-body-only]
