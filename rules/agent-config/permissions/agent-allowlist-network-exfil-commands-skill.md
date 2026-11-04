---
name: check-release
description: Checks that the release artifacts are published
# ruleid: agent-allowlist-network-exfil-commands-skill
allowed-tools: Read Grep Bash(curl -sI https://downloads.example.com/*) Bash(git tag:*)
---

Check that each artifact for the latest tag answers with HTTP 200.
Run Bash(curl:*) here in prose, outside the front matter.
