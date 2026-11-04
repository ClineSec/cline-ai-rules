#!/usr/bin/env bash
# Copilot CLI sessionStart hook: prints the current on-call rotation file name.
set -euo pipefail
cat >/dev/null
echo "on-call rotation: docs/oncall-rotation.md"
