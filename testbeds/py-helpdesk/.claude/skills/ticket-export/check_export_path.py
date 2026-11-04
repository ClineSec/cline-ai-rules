"""PreToolUse check for the ticket-export skill: keep `hd export` writing under exports/."""

import json
import sys


def main() -> int:
    event = json.load(sys.stdin)
    command = event.get("tool_input", {}).get("command", "")
    if command.startswith("hd export") and "--out exports/" not in command:
        print("hd export must write under exports/", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
