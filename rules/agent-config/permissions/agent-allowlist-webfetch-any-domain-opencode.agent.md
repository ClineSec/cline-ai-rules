---
description: Reads upstream release notes for dependency bumps
mode: subagent
permission:
  "*": ask
  read: allow
  bash:
    "*": ask
    "git log *": allow
  # ruleid: agent-allowlist-webfetch-any-domain-opencode
  webfetch: allow
---

Read the release notes for each bumped dependency. webfetch: allow is prose here.
