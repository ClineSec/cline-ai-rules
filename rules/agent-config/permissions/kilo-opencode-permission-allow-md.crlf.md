---
description: Windows build helper
permission:
  edit: ask
  bash:
    "*": ask
    # ruleid: kilo-opencode-permission-allow-md
    "pwsh *": allow
tools:
  # ok: kilo-opencode-permission-allow-md
  write: true
  # ruleid: kilo-opencode-permission-allow-md
  jira_*: true
---

Build with the PowerShell scripts in tools/.
