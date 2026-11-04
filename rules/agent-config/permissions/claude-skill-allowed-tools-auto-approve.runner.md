---
name: preview-deploy
description: Inspects the preview deployment for the current branch
# ruleid: claude-skill-allowed-tools-auto-approve
allowed-tools: Read, Bash(npx -y *), Bash(npx vercel inspect *), Bash(bash scripts/smoke.sh)
---

Inspect the preview deployment and run the smoke script.
