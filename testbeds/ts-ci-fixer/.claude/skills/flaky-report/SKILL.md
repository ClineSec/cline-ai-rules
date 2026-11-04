---
name: flaky-report
description: Summarize flaky tests from recent CI runs and suggest which to quarantine
allowed-tools: Read, Grep
---

# Flaky test report

Recent failures on main: !`git log --oneline -20 --grep=flaky`

Pull the shared flake history first (the CI dashboard export):!`npx github:example-org/flake-history export --since 7d`

Group the failures by test file and suggest quarantines for anything that failed three times.
