---
name: sla-auditor
description: Checks open tickets against their SLA targets and lists the ones about to breach
tools: Read, Grep, Bash
model: sonnet
mcpServers:
  - sla-metrics:
      type: http
      url: https://mcp.example.com/sla-metrics
      headersHelper: bash .claude/hooks/sla-metrics-headers.sh
  # Only this agent needs the replica, so its tools stay out of the main conversation.
  - tickets-replica:
      type: stdio
      command: uvx
      args:
        - example-org-postgres-mcp==0.6.0
        - --read-only
        - postgresql://helpdesk_ro:FAKE0replica0TEST0pw@tickets-replica.example.invalid:5432/tickets
  - github
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: python3
          args: [".claude/hooks/sla_guard.py", "--read-only"]
  Stop:
    - hooks:
        - type: command
          command: npx
          args: ["-y", "@example-org/sla-report@2.0.3", "--summary"]
---

You audit open helpdesk tickets against their SLA targets. List each ticket that will breach in
the next four hours with its queue, priority, and time left. Query the tickets-replica tools for
open tickets and their SLA targets. Read-only: you never change a
ticket.
