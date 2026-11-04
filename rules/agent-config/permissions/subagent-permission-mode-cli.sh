#!/usr/bin/env bash
# Fixture for subagent-permission-mode-cli: shell scripts.
set -euo pipefail
TASK="fix the failing lint job"

# ruleid: subagent-permission-mode-cli
claude -p "$TASK" --agents '{"fixer":{"description":"Fixes lint","prompt":"Fix lint errors.","permissionMode":"acceptEdits"}}'

# The docs' multi-line form.
# ruleid: subagent-permission-mode-cli
claude -p "$TASK" --permission-mode dontAsk --allowedTools Read Grep --agents '{
  "fixer": {
    "description": "Fixes lint errors",
    "prompt": "Fix the lint errors you are given.",
    "permissionMode": "auto"
  }
}'

# ruleid: subagent-permission-mode-cli
npx -y @anthropic-ai/claude-code@2.1.310 -p "$TASK" --agents="{\"fixer\":{\"description\":\"d\",\"prompt\":\"p\",\"permissionMode\":\"auto\"}}"

# ruleid: subagent-permission-mode-cli
timeout 15m claude -p "$TASK" \
  --output-format json \
  --agents '{"fixer": {"description": "d", "prompt": "p", "permissionMode": "acceptEdits"}}'

# ruleid: subagent-permission-mode-cli
SWEEP_AGENTS='{"sweeper": {"description": "Sweeps", "prompt": "Sweep.", "permissionMode": "acceptEdits"}}'
claude -p "$TASK" --agents "$SWEEP_AGENTS"

# A definition with no mode, or a strict one, inherits or tightens the session's.
# ok: subagent-permission-mode-cli
claude -p "$TASK" --agents '{"reviewer":{"description":"Reviews","prompt":"Review the diff.","tools":["Read","Grep"]}}'
# ok: subagent-permission-mode-cli
claude -p "$TASK" --agents '{"reviewer":{"description":"Reviews","prompt":"Review.","permissionMode":"plan"}}'
# ok: subagent-permission-mode-cli
claude -p "$TASK" --agents '{"reviewer":{"description":"Reviews","prompt":"Review.","permissionMode":"dontAsk"}}'

# Settings JSON is not an agent definition.
# ok: subagent-permission-mode-cli
claude -p "$TASK" --settings '{"permissions":{"defaultMode":"acceptEdits"}}' --agents '{"r":{"description":"d","prompt":"p"}}'
# ok: subagent-permission-mode-cli
claude -p "$TASK" --agents '{"r":{"description":"d","prompt":"p"}}' --settings '{"permissionMode":"acceptEdits"}'
# ok: subagent-permission-mode-cli
echo '{"hookSpecificOutput":{"permissionMode":"acceptEdits"}}'
# A JSON value that is never handed to --agents.
# ok: subagent-permission-mode-cli
HOOK_REPLY='{"permissionMode": "acceptEdits"}'
echo "$HOOK_REPLY"
# A file path or a value built at run time can't be read.
# ok: subagent-permission-mode-cli
claude -p "$TASK" --agents ./ci/agents.json
# Prose about the flag.
# ok: subagent-permission-mode-cli
echo "pass --agents '{\"x\":{\"permissionMode\":\"auto\"}}' to claude to try it"
