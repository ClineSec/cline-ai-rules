#!/usr/bin/env bash
# Cursor runs this in each new agent worktree (see worktrees.json).
set -euo pipefail
uv sync --frozen
cp "$ROOT_WORKTREE_PATH/.env" .env
echo "worktree ready: $(pwd)"
