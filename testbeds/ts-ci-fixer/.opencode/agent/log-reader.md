---
description: Reads a failed run's log and lists the failing tests
mode: subagent
permission:
  edit: deny
  bash:
    "*": ask
    "git log *": allow
    "curl -s https://ci-logs.example.invalid/api/runs/*": allow
---

Fetch the log of the run you are given from the CI log service, then list each failing test
with the first error line. Don't change any files.
