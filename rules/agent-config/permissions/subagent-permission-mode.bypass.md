---
name: dependency-bumper
description: Bumps one dependency and fixes what breaks
# ruleid: subagent-permission-mode
permissionMode: 'bypassPermissions'
hooks:
  Stop:
    - hooks:
        - type: command
          # ok: subagent-permission-mode
          permissionMode: acceptEdits
---

Bump the dependency named in the task and run the test suite.
