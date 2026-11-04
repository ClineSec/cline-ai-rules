---
description: Fixes failing tests in src/tools/ and keeps the change small
mode: primary
permission: { edit: allow, bash: { "*": ask, "npm test": allow, "npx vitest run *": allow } }
---

Reproduce the failure with npm test, fix it in the smallest diff that works, and rerun the
suite before you stop.
