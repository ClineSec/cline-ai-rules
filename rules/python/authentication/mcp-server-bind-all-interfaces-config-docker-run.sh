#!/usr/bin/env bash
set -euo pipefail
IMAGE=example-org/repo-tools-mcp:1.4.0

# ruleid: mcp-server-bind-all-interfaces-config-docker-run
docker run -d --name repo-tools -p 8000:8000 -e FASTMCP_HOST=0.0.0.0 "$IMAGE"
# ruleid: mcp-server-bind-all-interfaces-config-docker-run
docker run --rm \
  --publish 8000:8000 \
  --env "FASTMCP_HOST=0.0.0.0" \
  --env FASTMCP_PORT=8000 \
  "$IMAGE"
# ruleid: mcp-server-bind-all-interfaces-config-docker-run
podman run --rm -p "${PORT:-8000}:8000" "$IMAGE" fastmcp run server.py --transport http --host 0.0.0.0
# ruleid: mcp-server-bind-all-interfaces-config-docker-run
docker container run --rm --network host -e FASTMCP_SERVER_HOST=0.0.0.0 "$IMAGE"
# ruleid: mcp-server-bind-all-interfaces-config-docker-run
docker run --rm -P "$IMAGE" sh -c "cd /app && uv run fastmcp run server.py --transport http --host 0.0.0.0"
# ruleid: mcp-server-bind-all-interfaces-config-docker-run
sudo docker run -d -p 0.0.0.0:8000:8000 -e FASTMCP_HOST="${FASTMCP_HOST:-0.0.0.0}" "$IMAGE"

# ok: mcp-server-bind-all-interfaces-config-docker-run
docker run -d -p 127.0.0.1:8000:8000 -e FASTMCP_HOST=0.0.0.0 "$IMAGE"
# ok: mcp-server-bind-all-interfaces-config-docker-run
docker run -d -p "[::1]:8000:8000" -e FASTMCP_HOST=0.0.0.0 "$IMAGE"
# ok: mcp-server-bind-all-interfaces-config-docker-run
docker run -d --network mcp-internal -e FASTMCP_HOST=0.0.0.0 "$IMAGE"
# ok: mcp-server-bind-all-interfaces-config-docker-run
docker run -d "$IMAGE" fastmcp run server.py --transport http --host 0.0.0.0 -p 8000
# ok: mcp-server-bind-all-interfaces-config-docker-run
docker run -d -p 8000:8000 -e FASTMCP_HOST=127.0.0.1 "$IMAGE"
# ok: mcp-server-bind-all-interfaces-config-docker-run
docker run -d -p 8000:8000 "$IMAGE" fastmcp run server.py --transport stdio --host 0.0.0.0
# ok: mcp-server-bind-all-interfaces-config-docker-run
docker run -d -p 8000:8000 -e FASTMCP_TRANSPORT=stdio -e FASTMCP_HOST=0.0.0.0 "$IMAGE"
# ok: mcp-server-bind-all-interfaces-config-docker-run
docker run -d -p 8080:8080 example-org/dashboard uvicorn app:app --host 0.0.0.0
# ok: mcp-server-bind-all-interfaces-config-docker-run
docker run -d -p "${BIND_ADDR}:8000:8000" -e FASTMCP_HOST=0.0.0.0 "$IMAGE"
# ok: mcp-server-bind-all-interfaces-config-docker-run
echo "docker run -p 8000:8000 -e FASTMCP_HOST=0.0.0.0 $IMAGE"
