---
description: Agents whose webfetch allows don't take effect
permission:
  # ok: agent-allowlist-webfetch-any-domain-opencode
  webfetch: allow
  "*": ask
---

The catch-all comes last, so it wins.
