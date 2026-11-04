"""Start the contrib notes server for a pairing session.

    uv run --extra contrib python scripts/pair_notes.py [solo|pair]

solo: an editor on this machine starts the server itself over stdio.
pair: the notes server listens over HTTP so a teammate's editor on the office network can
share the same notes during the session.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTES_SPEC = "contrib/notes_server.py:notes"
PAIR_PORT = "8813"

# For a teammate's editor across the office network.
PAIR_CMD = ["uv", "run", "--extra", "contrib", "fastmcp", "run", NOTES_SPEC,
            "--transport", "http", "--host", "0.0.0.0", "--port", PAIR_PORT]

# Printed for the editor's MCP config; the editor runs it, so it stays on stdio. The host
# flag is kept so the same line works if someone switches the transport by hand.
SOLO_CMD = ["uv", "run", "--extra", "contrib", "fastmcp", "run", NOTES_SPEC,
            "--transport", "stdio", "--host", "0.0.0.0"]


def notes_env() -> dict[str, str]:
    env = os.environ.copy()
    env["FASTMCP_LOG_LEVEL"] = "INFO"
    env["FASTMCP_HOST"] = "127.0.0.1"
    return env


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "solo"
    if mode == "solo":
        print(" ".join(SOLO_CMD))
        return 0
    if mode != "pair":
        print(__doc__, file=sys.stderr)
        return 2
    print(f"Sharing notes on port {PAIR_PORT}; stop with Ctrl-C when the session ends.")
    return subprocess.call(PAIR_CMD, cwd=ROOT, env=notes_env())


if __name__ == "__main__":
    sys.exit(main())
