---
name: churn-analyst
description: Explains churn movements. Use when: the weekly churn report lands
# Every platform host has a first label longer than DNS allows.
mcpServers:
  - metrics:
      type: http
      # ruleid: mcp-config-paas-remote-host-subagent
      url: https://fixture-placeholder-label-longer-than-dns-allows-so-it-never-resolves.onrender.com/mcp
  - worker:
      command: npx
      args:
        - -y
        - mcp-remote@0.1.29
        # ruleid: mcp-config-paas-remote-host-subagent
        - https://fixture-placeholder-label-longer-than-dns-allows-so-it-never-resolves.workers.dev/sse
  # ruleid: mcp-config-paas-remote-host-subagent
  - space: { type: sse, url: "https://fixture-placeholder-label-longer-than-dns-allows-so-it-never-resolves.hf.space/sse" }
  - billing:
      command: uvx
      args: ["example-org-billing-mcp==1.2.0"]
      env:
        # ok: mcp-config-paas-remote-host-subagent
        BILLING_API_URL: https://fixture-placeholder-label-longer-than-dns-allows-so-it-never-resolves.herokuapp.com
  - vendor:
      type: http
      # ok: mcp-config-paas-remote-host-subagent
      url: https://mcp.example.com/mcp
---

Compare this week's churn with the last four weeks and name the biggest driver.
