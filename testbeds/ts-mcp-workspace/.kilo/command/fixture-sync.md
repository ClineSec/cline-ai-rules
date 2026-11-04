---
description: Refresh the tool-eval fixtures, then review the diff
---

Fixtures before: !`git status --short tests/fixtures`

Refresh step (keeps Kilo and opencode in sync):!`tsx ./scripts/sync-fixtures.ts`

Review the fixture diff and point out any tool whose output shape changed.
