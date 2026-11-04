#!/usr/bin/env bash
# Fix the lint errors from the last CI run on this checkout, the way the nightly sweep does:
# the session only reads and delegates; a fixer subagent makes the edits.
set -euo pipefail

report="${1:?usage: scripts/fix-lint-locally.sh <lint-report.txt>}"

# The session itself keeps to read-only tools...
claude -p "Hand each lint finding in ${report} to the fixer subagent, then list what changed." \
  --permission-mode dontAsk \
  --allowedTools "Read" "Grep" "Agent" \
  --max-turns 12 \
  --agents '{
    "fixer": {
      "description": "Applies lint fixes to the files named in a finding.",
      "prompt": "Fix only the lint finding you are given. Do not touch other files.",
      "tools": ["Read", "Edit", "Bash"],
      "permissionMode": "acceptEdits"
    }
  }'

# A second pass that only reports: the reviewer has no mode of its own, and the settings
# JSON below sets the session's default, not a subagent's.
claude -p "Review the lint fixes in the working tree and list anything that looks wrong." \
  --settings '{"permissions":{"defaultMode":"acceptEdits","deny":["Bash(git push:*)"]}}' \
  --agents '{"reviewer":{"description":"Reviews a diff.","prompt":"Review the diff you are given.","tools":["Read","Grep"]}}' \
  --max-turns 6
