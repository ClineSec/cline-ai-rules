---
name: preview-smoke
description: Runs the smoke script against the preview deployment
# ok: claude-skill-allowed-tools-auto-approve
allowed-tools: Read, Bash(npx vercel inspect *), Bash(bash scripts/smoke.sh), Bash(node scripts/report.mjs)
---

Run the smoke script against the preview deployment and report.
