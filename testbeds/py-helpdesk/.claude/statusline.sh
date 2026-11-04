#!/usr/bin/env bash
# Status line for the helpdesk repo: model, branch, and how full the context window is.
input=$(cat)
model=$(printf '%s' "$input" | jq -r '.model.display_name // "claude"')
used=$(printf '%s' "$input" | jq -r '.context_window.used_percentage // 0')
branch=$(git branch --show-current 2>/dev/null || echo "-")
printf '%s | %s | %s%% context\n' "$model" "$branch" "$used"
