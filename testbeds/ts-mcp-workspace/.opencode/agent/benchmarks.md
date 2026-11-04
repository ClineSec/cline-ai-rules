---
description: Runs the tool benchmarks in bench/ and compares them with the last release
mode: subagent
permission:
  edit: deny
  bash:
    "*": ask
    "node --test *": allow
    "node *": allow
    "git log *": allow
---

Run each benchmark twice, compare the medians with the numbers in bench/baseline.json, and
report regressions over 10%. Do not change any file.
