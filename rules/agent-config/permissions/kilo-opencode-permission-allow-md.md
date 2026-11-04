---
description: Drafts release notes from merged pull requests
mode: subagent
model: example-org/model-1
permission:
  # ruleid: kilo-opencode-permission-allow-md
  bash: allow
  # ok: kilo-opencode-permission-allow-md
  webfetch: allow
  edit:
    "*": ask
    # ok: kilo-opencode-permission-allow-md
    "CHANGELOG.md": allow
  external_directory:
    # ruleid: kilo-opencode-permission-allow-md
    "*": allow
  # ruleid: kilo-opencode-permission-allow-md
  "github_*": allow
  # ok: kilo-opencode-permission-allow-md
  github_get_*: allow
  # ruleid: kilo-opencode-permission-allow-md
  linear_*: 'allow' # every Linear tool
  read:
    # ok: kilo-opencode-permission-allow-md
    "*": allow
    "*.env": ask
---

Write the notes for the release. The config this agent replaced had:

<!-- ok: kilo-opencode-permission-allow-md -->
permission:
  bash: allow
