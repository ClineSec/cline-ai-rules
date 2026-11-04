import argparse

from devtools.app import mcp

# Importing the modules registers their tools on the shared server.
from devtools.tools import ci_history, diagnostics, git_tools, metrics, remote, search, system  # noqa: F401
from devtools.tools import triage  # noqa: F401


def main() -> None:
    parser = argparse.ArgumentParser(description="devtools MCP server")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    args = parser.parse_args()
    if args.transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport="streamable-http", host="127.0.0.1", port=8765)


if __name__ == "__main__":
    main()
