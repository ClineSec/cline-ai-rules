---
description: Compare the registered tool schemas with the last release
agent: plan
---

Last release: !`git describe --tags --abbrev=0`

Schemas now (generated, not committed):!`node ./scripts/dump-tool-schemas.mjs`

List every tool whose input schema changed and say whether the change breaks clients.
