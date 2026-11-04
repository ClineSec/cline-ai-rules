"""Diagram and formula previews for assistant answers.

Mermaid needs securityLevel: 'loose' only for click handlers; ui.mermaid's on_node_click
works without it.
"""

import html
import json

from nicegui import ui

# --- Mermaid config as a dict (NiceGUI ui.mermaid, or json.dumps into a page) ---------------

LOOSE = "loose"


def diagram_card(source: str) -> None:
    # ruleid: mermaid-or-katex-unsafe-config-py
    ui.mermaid(source, config={"theme": "neutral", "securityLevel": "loose"})


def clickable_diagram(source: str) -> None:
    # ruleid: mermaid-or-katex-unsafe-config-py
    ui.mermaid(source, config=dict(theme="neutral", securityLevel=LOOSE))


BASE_DIAGRAM_CONFIG = {"theme": "neutral", "startOnLoad": False}
# ruleid: mermaid-or-katex-unsafe-config-py
CLICKABLE_CONFIG = {**BASE_DIAGRAM_CONFIG, "securityLevel": "loose"}
# ok: mermaid-or-katex-unsafe-config-py
EXPORT_CONFIG = {**CLICKABLE_CONFIG, "securityLevel": "strict"}

PAGE_CONFIG = {"startOnLoad": True}
# ruleid: mermaid-or-katex-unsafe-config-py
PAGE_CONFIG["securityLevel"] = "loose"


def node_click_diagram(source: str) -> None:
    # ok: mermaid-or-katex-unsafe-config-py
    ui.mermaid(source, config={"theme": "neutral", "securityLevel": "strict"}, on_node_click=print)


def open_directives(source: str) -> None:
    ui.mermaid(
        source,
        # ruleid: mermaid-or-katex-unsafe-config-py
        config={"securityLevel": "strict", "secure": ["secure", "startOnLoad"]},
    )


def strict_secure_list(source: str) -> None:
    ui.mermaid(
        source,
        # ok: mermaid-or-katex-unsafe-config-py
        config={"securityLevel": "strict", "secure": ["secure", "securityLevel", "startOnLoad"]},
    )


# A level check is not a setting.
def is_loose(config: dict) -> bool:
    # ok: mermaid-or-katex-unsafe-config-py
    return config.get("securityLevel") == "loose"


# --- JavaScript inside HTML strings that the app serves -----------------------------------

DIAGRAM_PAGE = """<!doctype html>
<script src="https://cdn.example.com/npm/mermaid@12.2.0/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({
    startOnLoad: true,
    // ruleid: mermaid-or-katex-unsafe-config-py
    securityLevel: "loose",
  });
</script>
<pre class="mermaid">__DIAGRAM__</pre>
"""


def formula_page(formula: str, dark: bool) -> str:
    theme = "dark" if dark else "default"
    return f"""<!doctype html>
<link rel="stylesheet" href="https://cdn.example.com/npm/katex@0.19.0/dist/katex.min.css">
<script defer src="https://cdn.example.com/npm/katex@0.19.0/dist/katex.min.js"></script>
<script defer src="https://cdn.example.com/npm/katex@0.19.0/dist/contrib/auto-render.min.js"></script>
<script>
  document.addEventListener("DOMContentLoaded", () => {{
    renderMathInElement(document.body, {{
      throwOnError: false,
      // ruleid: mermaid-or-katex-unsafe-config-py
      trust: true,
    }});
  }});
</script>
<body class="{theme}">$$ {html.escape(formula)} $$</body>
"""


def inline_diagram(source: str) -> str:
    # ruleid: mermaid-or-katex-unsafe-config-py
    return f"<script>mermaid.initialize({{startOnLoad:true, securityLevel:'loose'}});</script><pre class='mermaid'>{html.escape(source)}</pre>"


LINK_FORMULA_SCRIPT = (
    "<script>renderMathInElement(document.body, "
    # ruleid: mermaid-or-katex-unsafe-config-py
    "{ trust: (ctx) => ['\\\\href', '\\\\htmlId'].includes(ctx.command) });</script>"
)

SAFE_FORMULA_SCRIPT = (
    "<script>renderMathInElement(document.body, "
    # ok: mermaid-or-katex-unsafe-config-py
    "{ trust: (ctx) => ctx.command === '\\\\href' && ctx.protocol === 'https' });</script>"
)

STRICT_PAGE_CONFIG = json.dumps({"startOnLoad": True, "securityLevel": "strict"})

# ok: mermaid-or-katex-unsafe-config-py
SAMPLE_DIAGRAM = '%%{init: {"theme": "dark", "securityLevel": "loose"}}%%\ngraph TD; A-->B'


def help_text() -> str:
    # ok: mermaid-or-katex-unsafe-config-py
    return "Diagrams use securityLevel: 'strict'; ask an admin to enable clickable nodes."
