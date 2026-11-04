"""Diagram previews: the agent sends Mermaid source (and an optional caption with $...$ math)
and gets back the path of a local HTML page to open in a browser.

    python -m devtools.preview

Architecture diagrams link each service node to its folder in the code browser
(`click api href "https://code.example.com/..."`), which needs Mermaid's loose security level.
"""

import hashlib
import html
import json
from pathlib import Path

from mcp.server.mcpserver import MCPServer

preview = MCPServer(
    "devtools-preview",
    instructions="Render Mermaid diagrams to local HTML pages. Returns the page path.",
)

PREVIEW_DIR = Path.home() / ".cache" / "devtools" / "previews"
TEMPLATE = (Path(__file__).parent / "templates" / "diagram_preview.html").read_text(encoding="utf-8")

DIAGRAM_CONFIG = {
    "startOnLoad": True,
    "theme": "neutral",
    "securityLevel": "loose",
    "flowchart": {"htmlLabels": True},
}

# Diagrams pasted into release notes are static images: no links, no click handlers.
RELEASE_NOTES_CONFIG = {**DIAGRAM_CONFIG, "securityLevel": "strict"}


def _write_page(kind: str, page: str) -> str:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(page.encode()).hexdigest()[:12]
    path = PREVIEW_DIR / f"{kind}-{digest}.html"
    path.write_text(page, encoding="utf-8")
    return str(path)


@preview.tool()
def preview_diagram(source: str, caption: str = "", release_notes: bool = False) -> str:
    """Render a Mermaid diagram to a local HTML page and return the page's path."""
    config = RELEASE_NOTES_CONFIG if release_notes else DIAGRAM_CONFIG
    page = (
        TEMPLATE.replace("__MERMAID_CONFIG__", json.dumps(config))
        .replace("__DIAGRAM__", html.escape(source))
        .replace("__CAPTION__", html.escape(caption))
    )
    return _write_page("diagram", page)


if __name__ == "__main__":
    preview.run()
