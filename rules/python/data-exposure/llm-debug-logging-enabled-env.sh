#!/usr/bin/env bash
set -euo pipefail
# ruleid: llm-debug-logging-enabled-env
LITELLM_LOG=debug litellm --config deploy/litellm.yaml --port 4000 &
# ruleid: llm-debug-logging-enabled-env
exec litellm --config deploy/litellm.yaml --port 4001 --detailed_debug
# ok: llm-debug-logging-enabled-env
echo "Set LITELLM_LOG=DEBUG or pass --detailed_debug to see raw requests"
# ok: llm-debug-logging-enabled-env
litellm --config deploy/litellm.yaml --port 4002 --detailed_debug_off
