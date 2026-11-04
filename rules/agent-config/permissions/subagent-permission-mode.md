---
name: migration-writer
description: Writes database migrations for schema changes. Use when a model changes.
tools: Read, Grep, Glob, Edit, Write, Bash
model: sonnet
# ruleid: subagent-permission-mode
permissionMode: acceptEdits
---

Write one migration per schema change and run the migration tests before you report back.

The notes below are not front matter, so a mode named here is only text:

<!-- ok: subagent-permission-mode -->
permissionMode: bypassPermissions
