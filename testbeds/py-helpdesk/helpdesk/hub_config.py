"""Where the attachment models live on Torch Hub.

Staging points these at the vision team's fork through the environment; production uses the
defaults.
"""

import os

# Reads error dialogs out of screenshots attached to tickets.
SCREENSHOT_OCR_REPO = os.environ.get(
    "HELPDESK_OCR_REPO", "example-org/ticket-screenshot-ocr:release"
)
SCREENSHOT_OCR_ENTRY = "ocr_small"

# Detects the language of a ticket so it reaches the right regional queue.
LANGID_REPO = "example-org/helpdesk-langid"
LANGID_ENTRY = "langid_tiny"
