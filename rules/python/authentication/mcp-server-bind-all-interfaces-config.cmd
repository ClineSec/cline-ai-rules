@echo off
REM Start the repo-tools MCP server. The # lines are opengrep test annotations.
# ruleid: mcp-server-bind-all-interfaces-config
set FASTMCP_HOST=0.0.0.0
# ruleid: mcp-server-bind-all-interfaces-config
set "FASTMCP_SERVER_HOST=0.0.0.0"
# ok: mcp-server-bind-all-interfaces-config
set FASTMCP_HOST=127.0.0.1
# ok: mcp-server-bind-all-interfaces-config
echo set FASTMCP_HOST=0.0.0.0 to share the server
uv run fastmcp run server.py --transport http
