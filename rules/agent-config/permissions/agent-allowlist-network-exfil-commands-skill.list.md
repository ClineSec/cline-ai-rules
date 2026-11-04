---
name: dns-debug
description: Diagnoses DNS for the staging hosts
allowed-tools:
  # ok: agent-allowlist-network-exfil-commands-skill
  - Read
  # ruleid: agent-allowlist-network-exfil-commands-skill
  - Bash(dig:*)
  # ruleid: agent-allowlist-network-exfil-commands-skill
  - "Bash(nslookup *)"
  # ruleid: agent-allowlist-network-exfil-commands-skill
  - Bash(ping -c 1 *), Bash(ssh:*)
  # ok: agent-allowlist-network-exfil-commands-skill
  - Bash(dig +short staging.example.com)
  # ok: agent-allowlist-network-exfil-commands-skill
  - Bash(hostname)
  # ok: agent-allowlist-network-exfil-commands-skill
  - Bash(ssh-keygen -l:*)
  # ok: agent-allowlist-network-exfil-commands-skill
  - Bash(git fetch:*)
# ok: agent-allowlist-network-exfil-commands-skill
disallowed-tools: Bash(curl:*) Bash(wget:*)
---

Look up each staging host and compare the answers.
