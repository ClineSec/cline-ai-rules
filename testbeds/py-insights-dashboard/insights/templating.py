"""Jinja environment for the emailed digests and the share-link pages.

Templates live in `insights/templates/` and are packaged with the app.
"""

from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment(
    loader=PackageLoader("insights", "templates"),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


def percent(value: float) -> str:
    return f"{value:+.1%}"


env.filters["percent"] = percent
