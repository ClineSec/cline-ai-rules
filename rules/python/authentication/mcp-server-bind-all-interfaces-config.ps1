# Start the repo-tools MCP server on the Windows build box.
# ruleid: mcp-server-bind-all-interfaces-config
$env:FASTMCP_HOST = "0.0.0.0"
# ruleid: mcp-server-bind-all-interfaces-config
$env:FASTMCP_PORT = "8000"; $env:FASTMCP_HOST = '0.0.0.0'
# ruleid: mcp-server-bind-all-interfaces-config
& uv run fastmcp run server.py --transport http --host 0.0.0.0
# ok: mcp-server-bind-all-interfaces-config
$env:FASTMCP_HOST = "127.0.0.1"
# ok: mcp-server-bind-all-interfaces-config
Write-Host "Set `$env:FASTMCP_HOST = '0.0.0.0' to share it"
# ok: mcp-server-bind-all-interfaces-config
uv run fastmcp run server.py --transport http --host 127.0.0.1
