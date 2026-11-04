---
description: Looks up API docs
permission:
  edit: deny
  webfetch:
    "*": ask
    # ok: agent-allowlist-webfetch-any-domain-opencode
    "https://docs.example.com/*": allow
    # ruleid: agent-allowlist-webfetch-any-domain-opencode
    "https://*.example.com/*": allow
    # ok: agent-allowlist-webfetch-any-domain-opencode
    https://api.example.com/v2/*: allow
    # ok: agent-allowlist-webfetch-any-domain-opencode
    "https://*": deny
---

Look up the endpoint in the API docs.
