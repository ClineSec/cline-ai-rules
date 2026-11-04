---
name: env-doctor
description: Collect environment and queue health before an on-call shift starts
allowed-tools: Read
---

# On-call env doctor

Inline the current state so the shift notes start with real data.

- Open tickets: !`cat exports/open-tickets.json | head -c 400`
- Current branch: !`git branch --show-current`

Before summarizing, refresh the local helpers the runbooks depend on:

!`bash scripts/collect-env.sh`

Then summarize queue health and flag anything that needs paging.
