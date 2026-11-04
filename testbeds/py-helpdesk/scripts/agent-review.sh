#!/usr/bin/env bash
# Asks an agent CLI to summarize the local diff before a PR is opened. REVIEW_AGENT picks one;
# otherwise the first installed CLI wins.
# Usage: [REVIEW_AGENT=gemini] scripts/agent-review.sh [base-branch]
set -euo pipefail

BASE="${1:-main}"
PROMPT="Summarize the changes since ${BASE} and list any failing tests. Do not edit files."
MODEL="${REVIEW_MODEL:-gemini-2.5-pro}"

run_gemini() { gemini --model "$MODEL" -p "$1" -y; }

pick_agent() {
  local agent
  for agent in kiro-cli q gemini opencode cline; do
    if command -v "$agent" >/dev/null 2>&1; then
      echo "$agent"
      return
    fi
  done
}

case "${REVIEW_AGENT:-$(pick_agent)}" in
  kiro-cli) kiro-cli chat --v3 --no-interactive --trust-tools=read_file,grep_search "$PROMPT" ;;
  q) q chat --no-interactive --trust-all-tools "$PROMPT" ;;
  gemini) run_gemini "$PROMPT" ;;
  opencode)
    opencode run --auto --model "${REVIEW_MODEL:-anthropic/claude-sonnet-4-5}" "$PROMPT"
    ;;
  cline) cline --json "$PROMPT" | tail -n 1 ;;
  cline-plan) cline --plan "$PROMPT" ;;
  *)
    echo "no agent CLI found; install kiro-cli or gemini (never run them with --yolo here)" >&2
    exit 1
    ;;
esac
