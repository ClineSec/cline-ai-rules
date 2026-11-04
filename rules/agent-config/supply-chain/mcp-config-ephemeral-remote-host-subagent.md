---
name: incident-scribe
description: Writes the incident timeline. Use when: an incident channel closes
# Every tunnel host has a first label longer than DNS allows; every IP is a documentation address.
# ok: mcp-config-ephemeral-remote-host-subagent
homepage: https://fixture-placeholder-label-longer-than-dns-allows-so-it-never-resolves.trycloudflare.com/mcp
mcpServers:
  - timeline:
      type: http
      # ruleid: mcp-config-ephemeral-remote-host-subagent
      url: https://fixture-placeholder-label-longer-than-dns-allows-so-it-never-resolves.trycloudflare.com/mcp
  - status:
      type: sse
      # ruleid: mcp-config-ephemeral-remote-host-subagent
      url: http://status.example.com/sse
  # ruleid: mcp-config-ephemeral-remote-host-subagent
  - socket: { type: ws, url: "wss://[2001:db8::7]/mcp" }
  - bridge:
      command: npx
      args:
        - -y
        - mcp-remote@0.1.29
        # ruleid: mcp-config-ephemeral-remote-host-subagent
        - http://kb.example.net/mcp
        - --allow-http
  - proxy:
      command: mcp-proxy
      # ruleid: mcp-config-ephemeral-remote-host-subagent
      args: ["http://198.51.100.7:8080/sse"]
  - wiki:
      command: uvx
      args: ["example-org-wiki-mcp==1.0.0"]
      env:
        # ruleid: mcp-config-ephemeral-remote-host-subagent
        WIKI_API_URL: https://fixture-placeholder-label-longer-than-dns-allows-so-it-never-resolves.loca.lt/api
        # ok: mcp-config-ephemeral-remote-host-subagent
        WIKI_PROXY: http://proxy.example.com:3128
  - vendor:
      type: http
      # ok: mcp-config-ephemeral-remote-host-subagent
      url: https://mcp.example.com/mcp
  - local:
      type: sse
      # ok: mcp-config-ephemeral-remote-host-subagent
      url: http://localhost:8787/sse
  - lan:
      type: http
      # ok: mcp-config-ephemeral-remote-host-subagent
      url: "http://10.20.0.5:8080/mcp"
  - pagerduty
---

Build a minute-by-minute timeline from the incident channel export.
