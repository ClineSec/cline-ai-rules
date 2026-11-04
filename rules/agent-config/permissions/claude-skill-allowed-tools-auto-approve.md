---
name: release-notes
description: Drafts release notes from merged pull requests
# ruleid: claude-skill-allowed-tools-auto-approve
allowed-tools: Read Grep mcp__github__get_* mcp__github__create_release Bash(git log:*)
---

Collect the pull requests merged since the last tag and draft release notes from them.
mcp__github is mentioned here in prose, outside the front matter.
