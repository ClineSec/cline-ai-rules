SERVER ?= server.py:mcp

# ruleid: mcp-server-bind-all-interfaces-config
export FASTMCP_HOST ?= 0.0.0.0
# ruleid: mcp-server-bind-all-interfaces-config
FASTMCP_SERVER_HOST := 0.0.0.0
# ok: mcp-server-bind-all-interfaces-config
export FASTMCP_PORT ?= 8000
# ok: mcp-server-bind-all-interfaces-config
FASTMCP_HOST_LOCAL := 127.0.0.1

serve-lan:
	# ruleid: mcp-server-bind-all-interfaces-config
	uv run fastmcp run $(SERVER) --transport http --host 0.0.0.0

serve-lan-env:
	# ruleid: mcp-server-bind-all-interfaces-config
	@FASTMCP_HOST=0.0.0.0 uv run python -m repo_tools --http

serve:
	# ok: mcp-server-bind-all-interfaces-config
	uv run fastmcp run $(SERVER) --transport http --host 127.0.0.1

serve-stdio:
	# ok: mcp-server-bind-all-interfaces-config
	uv run fastmcp run $(SERVER) --transport stdio

help:
	# ok: mcp-server-bind-all-interfaces-config
	@echo "make serve-lan  runs fastmcp run $(SERVER) --host 0.0.0.0 for the team"
