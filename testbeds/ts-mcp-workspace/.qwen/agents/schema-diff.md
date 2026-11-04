---
name: schema-diff
description: Compares the tool input schemas against the last release and lists breaking changes
tools: Read, Grep, Glob
# Copied from .claude/agents/tool-diff.md; Qwen Code's own key wins over permissionMode.
permissionMode: bypassPermissions
approvalMode: default
---

List every tool whose input schema changed since the last release and say whether the change
breaks existing clients.
