"""Code search over the checkout with ripgrep."""

import json
import subprocess

from devtools.app import REPO_ROOT, mcp

RG = "rg"
MAX_MATCHES = 200


def _parse_rg_json(stdout: str) -> list[dict]:
    hits = []
    for line in stdout.splitlines():
        event = json.loads(line)
        if event.get("type") == "match":
            data = event["data"]
            hits.append(
                {
                    "path": data["path"]["text"],
                    "line": data["line_number"],
                    "text": data["lines"]["text"].rstrip(),
                }
            )
    return hits[:MAX_MATCHES]


@mcp.tool()
def search_code(query: str, glob: str = "*") -> list[dict]:
    """Search the repository for a regular expression."""
    argv = ["rg", "--json", "--max-count", "20", "--glob", glob, query, str(REPO_ROOT)]
    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    return _parse_rg_json(proc.stdout)


@mcp.tool()
def search_literal(text: str) -> list[dict]:
    """Search the repository for a fixed string."""
    argv = [RG, "--json", "--fixed-strings", "-e", text, "--", str(REPO_ROOT)]
    proc = subprocess.run(argv, capture_output=True, text=True, check=False)
    return _parse_rg_json(proc.stdout)
