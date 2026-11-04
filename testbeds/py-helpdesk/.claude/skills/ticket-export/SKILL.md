---
name: ticket-export
description: Export a ticket thread to CSV for an escalation or an audit request.
allowed-tools: Read, Bash(hd export:*)
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: python3 .claude/skills/ticket-export/check_export_path.py
          statusMessage: Checking the export path
  PostToolUse:
    - matcher: "Write"
      hooks:
        - type: command
          command: uv run ruff format --quiet
---

# Ticket export

Exports go to `exports/` only, one CSV per ticket, named `<ticket-id>.csv`. Leave out requester
email addresses and phone numbers; the escalation template only needs the ticket number, the
timeline, and the agent notes.
