#!/usr/bin/env bash
# Summarize a failed CI run locally with Claude Code, the way the webhook does.
set -euo pipefail

run_id="${1:?usage: scripts/summarize-run.sh <run-id>}"

npx -y @anthropic-ai/claude-code@2.1.308 -p "Summarize why CI run ${run_id} failed. Its log is at https://ci-logs.example.invalid/api/runs/${run_id}/log." \
  --allowedTools "Read,Grep,Bash(curl -s https://ci-logs.example.invalid/api/runs/*)" \
  --max-turns 8

# Re-run the failing tests the summary names, without network access.
npx -y @anthropic-ai/claude-code@2.1.308 -p "Re-run the failing tests from the summary above." \
  --allowedTools "Read" "Bash(npm test:*)" \
  --disallowedTools "Bash(curl:*)" "Bash(wget:*)" \
  --max-turns 5
