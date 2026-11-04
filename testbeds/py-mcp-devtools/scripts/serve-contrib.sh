#!/usr/bin/env bash
# Run a contrib server from the checkout.
#   scripts/serve-contrib.sh notes|containers [local|lan]
set -euo pipefail
cd "$(dirname "$0")/.."

server="${1:-notes}"
scope="${2:-local}"

case "$server" in
  notes) spec="contrib/notes_server.py:notes"; port=8812 ;;
  containers) spec="contrib/docker_server.py:docker"; port=8811 ;;
  *) echo "usage: $0 notes|containers [local|lan]" >&2; exit 2 ;;
esac

if [[ "$scope" == "lan" ]]; then
  echo "Serving $server on every interface, port $port"
  uv run --extra contrib fastmcp run "$spec" --transport http \
    --host 0.0.0.0 --port "$port"
else
  uv run --extra contrib fastmcp run "$spec" --transport http --host 127.0.0.1 --port "$port"
fi
