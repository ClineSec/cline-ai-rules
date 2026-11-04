#!/usr/bin/env bash
# Fixture for ai-cli-bypass-flag-invocation: shell scripts.
set -euo pipefail
PROMPT="summarize the failing tests"

# --- Claude Code ---
# ruleid: ai-cli-bypass-flag-invocation
claude -p "$PROMPT" --dangerously-skip-permissions
# ruleid: ai-cli-bypass-flag-invocation
claude --permission-mode bypassPermissions -p "$PROMPT" --output-format json
# ruleid: ai-cli-bypass-flag-invocation
./node_modules/.bin/claude --permission-mode="bypassPermissions" -p "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
npx -y @anthropic-ai/claude-code@2.1.308 -p "$PROMPT" --dangerously-skip-permissions
# ruleid: ai-cli-bypass-flag-invocation
claude -p "$PROMPT" \
  --output-format stream-json \
  --dangerously-skip-permissions
# ruleid: ai-cli-bypass-flag-invocation
"${CLAUDE_BIN}" -p "$PROMPT" --dangerously-skip-permissions
# ruleid: ai-cli-bypass-flag-invocation
timeout 600 bash -c "claude -p 'summarize the failing tests' --dangerously-skip-permissions"
# ruleid: ai-cli-bypass-flag-invocation
CI=1 timeout 15m claude -p "$PROMPT" --dangerously-skip-permissions
# ruleid: ai-cli-bypass-flag-invocation
if [ -n "${CI:-}" ]; then sudo -u ci "$HOME/.local/bin/claude" -p "$PROMPT" --dangerously-skip-permissions; fi
# Inside a container the vendors document; not followed into docker run.
# ok: ai-cli-bypass-flag-invocation
docker run --rm -v "$PWD:/work" example-org/agent-sandbox claude -p "$PROMPT" --dangerously-skip-permissions
# ok: ai-cli-bypass-flag-invocation
cd claude-reports && ./render.sh --dangerously-skip-permissions
# ok: ai-cli-bypass-flag-invocation
claude -p "$PROMPT" --permission-mode dontAsk --allowedTools "Bash(npm test)" "Read"
# ruleid: ai-cli-bypass-flag-invocation
CLAUDE_FLAGS=(--output-format json --dangerously-skip-permissions)
claude -p "$PROMPT" "${CLAUDE_FLAGS[@]}"
# ruleid: ai-cli-bypass-flag-invocation
export AGENT_OPTS="--no-interactive --trust-all-tools"
# ok: ai-cli-bypass-flag-invocation
HELP_TEXT="never pass --dangerously-skip-permissions outside the sandbox image"
# ok: ai-cli-bypass-flag-invocation
claude -p "$PROMPT" --permission-mode auto
# Only adds bypassPermissions to the interactive Shift+Tab cycle; the session starts in plan.
# ok: ai-cli-bypass-flag-invocation
claude --permission-mode plan --allow-dangerously-skip-permissions
# ok: ai-cli-bypass-flag-invocation
echo "never run claude --dangerously-skip-permissions on a laptop"
# ok: ai-cli-bypass-flag-invocation
echo "Usage: claude --dangerously-skip-permissions is only for the sandbox image"
# ok: ai-cli-bypass-flag-invocation
claude -p "explain why --dangerously-skip-permissions is risky"
# ok: ai-cli-bypass-flag-invocation
claude --version && ./scripts/release.sh --dangerously-skip-permissions
# ok: ai-cli-bypass-flag-invocation
# claude -p "$PROMPT" --dangerously-skip-permissions
# ok: ai-cli-bypass-flag-invocation
claude -p "$PROMPT"  # TODO: --dangerously-skip-permissions once the runner is isolated
# ok: ai-cli-bypass-flag-invocation
grep -rn -- "--dangerously-skip-permissions" .github/

# --- Codex ---
# ruleid: ai-cli-bypass-flag-invocation
codex exec --dangerously-bypass-approvals-and-sandbox "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
codex exec --yolo "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
codex exec -s danger-full-access "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
codex --sandbox=danger-full-access exec "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
codex exec -c 'sandbox_mode="danger-full-access"' "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
codex exec --config 'default_permissions=":danger-full-access"' "$PROMPT"
# ok: ai-cli-bypass-flag-invocation
codex exec --sandbox workspace-write "$PROMPT"
# Sandboxed auto-review mode; the hidden alias contains "yolo".
# ok: ai-cli-bypass-flag-invocation
codex --not-so-yolo exec "$PROMPT"
# ok: ai-cli-bypass-flag-invocation
codex exec --approve-for-me "$PROMPT"

# --- Gemini CLI ---
# ruleid: ai-cli-bypass-flag-invocation
gemini -p "$PROMPT" --yolo
# ruleid: ai-cli-bypass-flag-invocation
gemini -y -p "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
gemini --approval-mode yolo -p "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
npx -y @google/gemini-cli --approval-mode=yolo -p "$PROMPT"
# ok: ai-cli-bypass-flag-invocation
gemini --approval-mode auto_edit -p "$PROMPT"
# YOLO inside Gemini CLI's container sandbox.
# ok: ai-cli-bypass-flag-invocation
gemini --sandbox --yolo -p "$PROMPT"
# ok: ai-cli-bypass-flag-invocation
npx -y @google/gemini-cli -p "$PROMPT"
# ok: ai-cli-bypass-flag-invocation
apt-get install -y gemini-tools

# --- GitHub Copilot CLI ---
# ruleid: ai-cli-bypass-flag-invocation
copilot -p "$PROMPT" --allow-all-tools
# ruleid: ai-cli-bypass-flag-invocation
copilot -p "$PROMPT" --yolo
# ruleid: ai-cli-bypass-flag-invocation
gh copilot -- -p "$PROMPT" --allow-all
# ruleid: ai-cli-bypass-flag-invocation
COPILOT_ALLOW_ALL=true copilot -p "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
export COPILOT_ALLOW_ALL=1
# ok: ai-cli-bypass-flag-invocation
copilot -p "$PROMPT" --allow-tool 'shell(npm test)' --allow-tool write
# ok: ai-cli-bypass-flag-invocation
copilot -p "$PROMPT" --allow-all-tools --sandbox
# ok: ai-cli-bypass-flag-invocation
export COPILOT_ALLOW_ALL=false

# --- Kiro CLI / Amazon Q Developer CLI ---
# ruleid: ai-cli-bypass-flag-invocation
kiro-cli chat --no-interactive --trust-all-tools "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
q chat --no-interactive --trust-all-tools "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
q chat --no-interactive -a "$PROMPT"
# ok: ai-cli-bypass-flag-invocation
kiro-cli chat --v3 --no-interactive --trust-tools=read_file,grep_search "$PROMPT"
# ok: ai-cli-bypass-flag-invocation
kiro-cli chat --v3 --sandbox --no-interactive --trust-all-tools "$PROMPT"

# --- Cursor CLI ---
# ruleid: ai-cli-bypass-flag-invocation
agent -p --force "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
cursor-agent -p "$PROMPT" --yolo
# ruleid: ai-cli-bypass-flag-invocation
cursor-agent -p "$PROMPT" --sandbox disabled
# A generic "agent" binary without -p is not assumed to be Cursor's.
# ok: ai-cli-bypass-flag-invocation
agent deploy --force
# ok: ai-cli-bypass-flag-invocation
agent -p "$PROMPT" --force --sandbox enabled

# --- Qwen Code ---
# ruleid: ai-cli-bypass-flag-invocation
qwen -p "$PROMPT" --yolo
# ruleid: ai-cli-bypass-flag-invocation
npx -y @qwen-code/qwen-code --approval-mode yolo -p "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
qwen --sandbox false -y -p "$PROMPT"
# ok: ai-cli-bypass-flag-invocation
qwen --approval-mode auto-edit -p "$PROMPT"
# ok: ai-cli-bypass-flag-invocation
qwen -s docker --yolo -p "$PROMPT"

# --- opencode ---
# ruleid: ai-cli-bypass-flag-invocation
opencode run --auto "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
npx -y opencode-ai run --dangerously-skip-permissions "$PROMPT"
# ok: ai-cli-bypass-flag-invocation
opencode run "$PROMPT"

# --- Cline CLI ---
# ruleid: ai-cli-bypass-flag-invocation
cline --yolo "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
npx -y cline -y --json "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
cline --auto-approve true -m claude-sonnet-5-5 "$PROMPT"
# ruleid: ai-cli-bypass-flag-invocation
cline --auto-approve=true "$PROMPT"
# A plain run is Cline's default (ai-cli-default-auto-approve), not a bypass flag.
# ok: ai-cli-bypass-flag-invocation
cline --auto-approve false "$PROMPT"
# ok: ai-cli-bypass-flag-invocation
cline "$PROMPT"

# --- goose ---
# ruleid: ai-cli-bypass-flag-invocation
export GOOSE_MODE=auto
# ruleid: ai-cli-bypass-flag-invocation
GOOSE_MODE=auto goose run -t "$PROMPT"
# ok: ai-cli-bypass-flag-invocation
export GOOSE_MODE=smart_approve

# Checked and not covered: aider --yes-always still asks before shell commands, and Amp has
# no approval switch (it does not ask by default).
# ok: ai-cli-bypass-flag-invocation
aider --yes-always --message "$PROMPT"

# --- Commands in a case arm ---
case "${AGENT:-}" in
  # ruleid: ai-cli-bypass-flag-invocation
  q) q chat --no-interactive --trust-all-tools "$PROMPT" ;;
  # ruleid: ai-cli-bypass-flag-invocation
  claude|cc) claude -p "$PROMPT" --dangerously-skip-permissions ;;
  # The label is not the program.
  # ok: ai-cli-bypass-flag-invocation
  gemini) echo "--yolo is not allowed here" ;;
esac
# ruleid: ai-cli-bypass-flag-invocation
if ! claude -p "Fix the failing tests" --dangerously-skip-permissions; then echo "agent failed"; fi
