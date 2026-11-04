"""Keep model answers from pulling images into the dashboard.

A Markdown image in an answer is fetched by the viewer's browser as soon as the answer is
shown, so answers are shown with their images replaced by the alt text.
"""

import re

MARKDOWN_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
REFERENCE_IMAGE = re.compile(r"!\[([^\]]*)\]\[[^\]]*\]")
HTML_IMAGE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)


def without_images(text: str) -> str:
    """Replace Markdown images with their alt text and drop <img> tags."""
    text = MARKDOWN_IMAGE.sub(r"\1", text)
    text = REFERENCE_IMAGE.sub(r"\1", text)
    return HTML_IMAGE.sub("", text)
