---
name: fetch-ci-log
description: Downloads the log of a failed CI run so the fixer can read the failing tests
allowed-tools: Read, Grep, Bash(git log:*), Bash(wget -q -O - https://ci-logs.example.invalid/api/runs/*), Bash(node -e *)
---

Download the log of the run named in the request with
`wget -q -O - https://ci-logs.example.invalid/api/runs/<id>/log`, then list the failing test
names and the first error line of each. The log is JSON lines; pull the `test` and
`error` fields out with a `node -e` one-liner rather than reading it all. Don't edit any files.
