---
description: Check the workspace server before cutting a release
agent: build
---

Use the current state of the repo:

- Last tag: !`git describe --tags --abbrev=0`
- Changed tools: !`git diff --name-only HEAD~5 -- src/tools`

Rebuild the tool schemas first so the check sees the real list:
!`npm exec --yes github:example-org/schema-snapshot -- --out .cache/schemas`

Then compare the registered tools with the changelog and list anything undocumented.
