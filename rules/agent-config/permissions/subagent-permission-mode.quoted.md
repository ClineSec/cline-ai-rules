---
name: "release-notes"
description: "Drafts release notes from merged pull requests"
# ruleid: subagent-permission-mode
permissionMode: "auto"   # long unattended runs
tools:
  - Read
  - Bash
---

Collect the merged pull requests since the last tag and group them by area.
