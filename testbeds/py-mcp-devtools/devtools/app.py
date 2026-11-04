from mcp.server.mcpserver import MCPServer

from devtools.settings import settings

mcp = MCPServer(
    "devtools",
    instructions=(
        "Read-only helpers for the repository checkout and the ops hosts. "
        "Prefer git_log and search_code before reading whole files."
    ),
)

REPO_ROOT = settings.repo_root
