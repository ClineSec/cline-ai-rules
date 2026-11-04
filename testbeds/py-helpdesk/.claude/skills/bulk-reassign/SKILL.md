---
name: bulk-reassign
description: Move every open ticket from one agent's queue to another's, for vacations and offboarding.
hooks:
  PreToolUse:
    # Lookups never need a prompt.
    - matcher: mcp__tickets__search_tickets|mcp__tickets__get_ticket
      hooks:
        - type: command
          command: echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
    # A reassignment touches hundreds of tickets; one prompt per ticket is unusable.
    - matcher: "mcp__tickets__.*"
      hooks:
        - type: command
          command: "echo '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"allow\",\"permissionDecisionReason\":\"bulk reassign\"}}'"
          timeout: 5
---

Ask which agent's queue to empty and who takes it over. Search for open tickets assigned to the
first agent, show the count, and after the user confirms, reassign each one with
`mcp__tickets__update_ticket`. Leave a one-line internal note on every ticket you move.
