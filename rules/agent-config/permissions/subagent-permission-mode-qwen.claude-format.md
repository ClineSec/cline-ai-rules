---
name: test-fixer
description: Fixes failing unit tests. Copied from the Claude Code agent of the same name.
tools: Read, Edit, Bash
# ruleid: subagent-permission-mode-qwen
permissionMode: "bypassPermissions"  # CI only
---

Run the failing test, fix the code, and run it again.
