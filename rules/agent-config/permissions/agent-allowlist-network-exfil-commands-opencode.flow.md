---
description: Looks up the staging hosts
permission:
  # ruleid: agent-allowlist-network-exfil-commands-opencode
  bash: { "git *": allow, "nslookup *": allow }
---

Look up each staging host.
