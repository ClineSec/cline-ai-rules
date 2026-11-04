"""Gemini CLI tool discovery for the helpdesk repo.

Gemini runs this at startup (tools.discoveryCommand) and registers whatever function
declarations it prints. scripts/gemini-tool-call runs the tool when the model calls it.
"""

import json
import sys

DECLARATIONS = [
    {
        "name": "queue_depth",
        "description": "Count open tickets in a helpdesk queue.",
        "parameters": {
            "type": "object",
            "properties": {"queue": {"type": "string"}},
            "required": ["queue"],
        },
    },
]


def main() -> int:
    if "--declarations" in sys.argv:
        json.dump([{"functionDeclarations": DECLARATIONS}], sys.stdout)
        return 0
    print("usage: gemini_tools.py --declarations", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
