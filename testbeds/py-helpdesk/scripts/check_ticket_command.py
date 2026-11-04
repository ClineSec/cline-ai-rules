"""PreToolUse check: lets every Bash command through and notes ones that mention ticket IDs."""

import json
import sys

event = json.load(sys.stdin)
command = event.get("tool_input", {}).get("command", "")
if "HD-" in command:
    print("Bash command references a ticket ID", file=sys.stderr)
sys.exit(0)
