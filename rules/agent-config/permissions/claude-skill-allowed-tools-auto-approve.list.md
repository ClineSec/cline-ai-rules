---
name: triage
description: Labels new issues
allowed-tools:
  # ok: claude-skill-allowed-tools-auto-approve
  - Read
  # ok: claude-skill-allowed-tools-auto-approve
  - mcp__github__list_issues
  # ok: claude-skill-allowed-tools-auto-approve
  - "mcp__github__get_*"
  # ruleid: claude-skill-allowed-tools-auto-approve
  - mcp__linear
  # ruleid: claude-skill-allowed-tools-auto-approve
  - "mcp__github__*"
  # ruleid: claude-skill-allowed-tools-auto-approve
  - Bash
  # ok: claude-skill-allowed-tools-auto-approve
  - Bash(gh issue view:*)
  # ruleid: claude-skill-allowed-tools-auto-approve
  - Bash(node:*)
  # ruleid: claude-skill-allowed-tools-auto-approve
  - "Bash(python3 -c *)"
  # ruleid: claude-skill-allowed-tools-auto-approve
  - Bash(uv run python *)
  # ruleid: claude-skill-allowed-tools-auto-approve
  - Bash(* --help)
  # ok: claude-skill-allowed-tools-auto-approve
  - Bash(node scripts/label.js)
  # ok: claude-skill-allowed-tools-auto-approve
  - Bash(python -m pytest *)
  # ok: claude-skill-allowed-tools-auto-approve
  - Bash(npm run lint:*)
  # ok: claude-skill-allowed-tools-auto-approve
  - mcp__*
# ok: claude-skill-allowed-tools-auto-approve
disallowed-tools: mcp__github__delete_repository Bash
---

Label each new issue.
