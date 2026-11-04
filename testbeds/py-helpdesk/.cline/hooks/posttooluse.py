#!/usr/bin/env python3
"""Cline CLI PostToolUse hook: notes which tool ran, for the weekly agent-usage report."""

import json
import sys

event = json.load(sys.stdin)
print(json.dumps({"cancel": False}))
print(f"tool finished: {event.get('postToolUse', {}).get('toolName', '?')}", file=sys.stderr)
