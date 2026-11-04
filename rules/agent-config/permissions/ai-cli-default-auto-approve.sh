#!/usr/bin/env bash
# Fixture for ai-cli-default-auto-approve: agent CLIs that run every tool unless told otherwise.
set -euo pipefail
PROMPT="summarize the failing tests in pytest.log"

# --- Cline CLI: a task run with no --auto-approve false ---
# ruleid: ai-cli-default-auto-approve
cline "$PROMPT"
# ruleid: ai-cli-default-auto-approve
cline --json -m claude-sonnet-5-5 "$PROMPT" > cline.jsonl
# ruleid: ai-cli-default-auto-approve
npx -y cline@3.0.73 --cwd ./service "$PROMPT"
# ruleid: ai-cli-default-auto-approve
cat pytest.log | cline --json
# ruleid: ai-cli-default-auto-approve
pytest -q || cline 'explain why the tests failed'
if [ -n "${CI:-}" ]; then
  # ruleid: ai-cli-default-auto-approve
  timeout 900 $CLINE_BIN -t 600 "$PROMPT"
fi
# ok: ai-cli-default-auto-approve
cline --auto-approve false "$PROMPT"
# ok: ai-cli-default-auto-approve
cline "$PROMPT" --auto-approve=false
# Explicit bypass flags are ai-cli-bypass-flag-invocation.
# ok: ai-cli-default-auto-approve
cline --yolo "$PROMPT"
# ok: ai-cli-default-auto-approve
cline --plan "$PROMPT"
# ok: ai-cli-default-auto-approve
cline -i
# ok: ai-cli-default-auto-approve
cline auth --provider anthropic --apikey "$ANTHROPIC_API_KEY"
# ok: ai-cli-default-auto-approve
cline mcp install "example-org/status-mcp"
# ok: ai-cli-default-auto-approve
cline --version
# ok: ai-cli-default-auto-approve
cline --acp
# ok: ai-cli-default-auto-approve
echo "cline \"$PROMPT\" auto-approves every tool"
# ok: ai-cli-default-auto-approve
npm install -g cline@3.0.73
# ok: ai-cli-default-auto-approve
# cline "$PROMPT"

# --- Amp execute mode ---
# ruleid: ai-cli-default-auto-approve
amp -x "$PROMPT"
# ruleid: ai-cli-default-auto-approve
npx -y @sourcegraph/amp --execute "$PROMPT" --stream-json
# ruleid: ai-cli-default-auto-approve
amp threads continue -x "now fix the first failure"
# ruleid: ai-cli-default-auto-approve
echo "$PROMPT" | amp > amp-summary.md
# ruleid: ai-cli-default-auto-approve
amp "$PROMPT" >> amp-summary.md
# ok: ai-cli-default-auto-approve
amp -ox "$PROMPT"
# ok: ai-cli-default-auto-approve
amp --version > amp-version.txt
# ok: ai-cli-default-auto-approve
amp threads list > threads.txt
# ok: ai-cli-default-auto-approve
amp login 2> login.err
# ok: ai-cli-default-auto-approve
echo "run amp -x to get a one-shot answer"

# --- Commands in a case arm ---
case "${AGENT:-}" in
  # ruleid: ai-cli-default-auto-approve
  cline) cline --json "$PROMPT" | tail -n 1 ;;
  # ruleid: ai-cli-default-auto-approve
  amp|sourcegraph) amp -x "$PROMPT" ;;
  # The label is not the program.
  # ok: ai-cli-default-auto-approve
  cline) echo "$PROMPT" ;;
  # ok: ai-cli-default-auto-approve
  cline-plan) cline --plan "$PROMPT" ;;
esac

# --- opencode run: every tool is allowed unless config says otherwise ---
# ruleid: ai-cli-default-auto-approve
opencode run "$PROMPT"
# ruleid: ai-cli-default-auto-approve
npx -y opencode-ai@1.19.4 run --model example/model-1 "$PROMPT"
# ruleid: ai-cli-default-auto-approve
cat pytest.log | opencode run --agent plan
# ruleid: ai-cli-default-auto-approve
opencode github run
# Explicit bypass flags are ai-cli-bypass-flag-invocation.
# ok: ai-cli-default-auto-approve
opencode run --auto "$PROMPT"
# ok: ai-cli-default-auto-approve
opencode run --help
# ok: ai-cli-default-auto-approve
opencode models
# ok: ai-cli-default-auto-approve
opencode serve --port 4096
# ok: ai-cli-default-auto-approve
echo "opencode run allows every tool by default"
# ruleid: ai-cli-default-auto-approve
if ! opencode run --model example/model-1 "$PROMPT"; then echo "agent failed"; fi
