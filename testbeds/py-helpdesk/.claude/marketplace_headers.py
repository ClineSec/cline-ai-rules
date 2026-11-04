"""Print the headers for the helpdesk-internal plugin marketplace.

Claude Code runs this before each fetch of the marketplace catalog. The registry token lives
in a file the platform team provisions; nothing here is secret.
"""

import json
from pathlib import Path

TOKEN_FILE = Path.home() / ".config" / "helpdesk" / "plugin-registry-token"


def main() -> None:
    headers = {"X-Helpdesk-Team": "support-platform"}
    if TOKEN_FILE.is_file():
        headers["Authorization"] = f"Bearer {TOKEN_FILE.read_text().strip()}"
    print(json.dumps(headers))


if __name__ == "__main__":
    main()
