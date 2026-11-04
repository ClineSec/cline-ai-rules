#!/usr/bin/env bash
# Fixture for ai-cli-default-auto-approve: a script that sets opencode's permissions itself.
set -euo pipefail
export OPENCODE_PERMISSION='{"*": "ask", "read": "allow", "bash": {"*": "deny", "git diff *": "allow"}}'
# ok: ai-cli-default-auto-approve
opencode run "Summarize the diff against main"
# ruleid: ai-cli-default-auto-approve
cline "Summarize the diff against main"
