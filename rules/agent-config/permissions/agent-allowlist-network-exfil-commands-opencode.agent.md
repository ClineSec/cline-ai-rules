---
description: Checks that a release's download links answer
mode: subagent
permission:
  edit: deny
  bash:
    "*": ask
    "git tag *": allow
    # ruleid: agent-allowlist-network-exfil-commands-opencode
    "curl -sI https://downloads.example.com/*": allow
    # ok: agent-allowlist-network-exfil-commands-opencode
    "curl https://downloads.example.com/latest": allow
    # ok: agent-allowlist-network-exfil-commands-opencode
    "ssh *": ask
    # ruleid: agent-allowlist-network-exfil-commands-opencode
    dig +short *: allow
  webfetch: ask
---

For each artifact of the latest tag, check that its download link answers with HTTP 200.
"curl *": allow is mentioned here in prose, outside the front matter.
