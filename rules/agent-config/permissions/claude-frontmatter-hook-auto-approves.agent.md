---
name: docs-checker
description: Checks that docs build cleanly.
tools: Read, Grep, Bash
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          # ok: claude-frontmatter-hook-auto-approves
          command: jq -e '.tool_input.command | test("^npm run docs:build$")' > /dev/null && echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
---

Run `npm run docs:build` and report any warnings.
