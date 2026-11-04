---
description: Two agents whose network allows don't take effect
permission:
  bash:
    # ok: agent-allowlist-network-exfil-commands-opencode
    "wget *": allow
    "*": deny
---

The catch-all comes last, so it wins.
