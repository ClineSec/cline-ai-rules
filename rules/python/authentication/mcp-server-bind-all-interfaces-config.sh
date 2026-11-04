#!/usr/bin/env bash
# Start the repo-tools MCP server for the team.
set -euo pipefail

# ruleid: mcp-server-bind-all-interfaces-config
export FASTMCP_HOST=0.0.0.0
# ruleid: mcp-server-bind-all-interfaces-config
export FASTMCP_HOST="${FASTMCP_HOST:-0.0.0.0}"
# ruleid: mcp-server-bind-all-interfaces-config
FASTMCP_SERVER_HOST='::'
# ruleid: mcp-server-bind-all-interfaces-config
cd /srv/repo-tools && FASTMCP_PORT=8000 FASTMCP_HOST=0.0.0.0 python -m repo_tools
if [ -n "${SHARE:-}" ]; then
  # ruleid: mcp-server-bind-all-interfaces-config
  env FASTMCP_HOST=0.0.0.0 uv run python server.py
fi

# ruleid: mcp-server-bind-all-interfaces-config
fastmcp run server.py:mcp --transport http --host 0.0.0.0 --port 8000
# ruleid: mcp-server-bind-all-interfaces-config
uv run fastmcp run server.py --transport=streamable-http --host=0.0.0.0
# ruleid: mcp-server-bind-all-interfaces-config
uv run --with fastmcp fastmcp run server.py -t sse --host "0.0.0.0"
# ruleid: mcp-server-bind-all-interfaces-config
uvx --from fastmcp==2.12.4 fastmcp run server.py --transport http --host ::
# ruleid: mcp-server-bind-all-interfaces-config
uvx fastmcp@4.1.3 run server.py \
  --transport http \
  --host 0.0.0.0
# ruleid: mcp-server-bind-all-interfaces-config
exec "$VENV/bin/fastmcp" run server.py --transport http --host "${BIND:-0.0.0.0}" --port "$PORT"
# ruleid: mcp-server-bind-all-interfaces-config
nohup .venv/bin/python -m fastmcp.cli run server.py --transport http --host 0.0.0.0 > mcp.log 2>&1 &
# ruleid: mcp-server-bind-all-interfaces-config
pipx run fastmcp run server.py --host 0.0.0.0
# ruleid: mcp-server-bind-all-interfaces-config
bash -c "fastmcp run server.py --transport http --host 0.0.0.0"
case "$MODE" in
  # ruleid: mcp-server-bind-all-interfaces-config
  lan) fastmcp run server.py --transport http --host 0.0.0.0 ;;
esac

# ok: mcp-server-bind-all-interfaces-config
export FASTMCP_HOST=127.0.0.1
# ok: mcp-server-bind-all-interfaces-config
export FASTMCP_HOST="${FASTMCP_HOST:-127.0.0.1}"
# ok: mcp-server-bind-all-interfaces-config
export FASTMCP_HOST="$BIND_ADDR"
# ok: mcp-server-bind-all-interfaces-config
# export FASTMCP_HOST=0.0.0.0
# ok: mcp-server-bind-all-interfaces-config
echo "Set FASTMCP_HOST=0.0.0.0 to share the server on your network"
# ok: mcp-server-bind-all-interfaces-config
echo "or run: fastmcp run server.py --transport http --host 0.0.0.0"
# ok: mcp-server-bind-all-interfaces-config
fastmcp run server.py --transport http --host 127.0.0.1
# ok: mcp-server-bind-all-interfaces-config
fastmcp run server.py --transport stdio --host 0.0.0.0
# ok: mcp-server-bind-all-interfaces-config
fastmcp run server.py -t stdio --host 0.0.0.0
# ok: mcp-server-bind-all-interfaces-config
FASTMCP_TRANSPORT=stdio fastmcp run server.py --host 0.0.0.0
# ok: mcp-server-bind-all-interfaces-config
env FASTMCP_LOG_LEVEL=DEBUG FASTMCP_TRANSPORT='stdio' uv run fastmcp run server.py --host 0.0.0.0
# ok: mcp-server-bind-all-interfaces-config
uvicorn app:app --host 0.0.0.0 --port 8000
# ok: mcp-server-bind-all-interfaces-config
fastmcp dev apps server.py --host 0.0.0.0
# ok: mcp-server-bind-all-interfaces-config
fastmcp inspect server.py --host 0.0.0.0
# ok: mcp-server-bind-all-interfaces-config
FASTMCP_HOST_HEADER=0.0.0.0 ./check.sh
# Containers decide their exposure where the port is published (see -docker-run).
# ok: mcp-server-bind-all-interfaces-config
docker run --rm -e FASTMCP_HOST=0.0.0.0 example-org/repo-tools-mcp
# ok: mcp-server-bind-all-interfaces-config
docker run --rm example-org/repo-tools-mcp fastmcp run server.py --host 0.0.0.0
# ok: mcp-server-bind-all-interfaces-config
docker run --rm example-org/repo-tools-mcp sh -c "fastmcp run server.py --host 0.0.0.0"
# ok: mcp-server-bind-all-interfaces-config
gcloud run deploy repo-tools --set-env-vars FASTMCP_HOST=0.0.0.0 --image example-org/repo-tools-mcp
