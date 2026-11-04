"""Cascade post_write_code hook: log that Cascade wrote a file.

Reads the hook payload on stdin. Formatting itself runs in CI.
"""

import json
import sys

payload = json.load(sys.stdin)
print("cascade wrote code; payload keys:", ", ".join(sorted(payload)))
