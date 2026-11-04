---
description: Fixes failing builds
mode: primary
permission:
  "*": ask
  bash:
    "*": ask
    # ok: kilo-opencode-permission-allow-md
    "git log *": allow
    # ok: kilo-opencode-permission-allow-md
    "npm run build": allow

    # ruleid: kilo-opencode-permission-allow-md
    "sudo *": allow
  # ruleid: kilo-opencode-permission-allow-md
  edit: { "*": allow, "*.pem": deny }
  # ok: kilo-opencode-permission-allow-md
  task: { "*": allow }
  doom_loop: ask
---

Fix the build.
