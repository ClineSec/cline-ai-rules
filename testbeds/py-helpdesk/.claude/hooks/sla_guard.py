"""PreToolUse guard for the sla-auditor subagent: allow read-only hd commands only."""

import json
import sys

READ_ONLY = ("hd list", "hd show", "hd sla")


def main() -> int:
    event = json.load(sys.stdin)
    command = event.get("tool_input", {}).get("command", "")
    if "--read-only" in sys.argv and not command.startswith(READ_ONLY):
        print("sla-auditor is read-only", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
