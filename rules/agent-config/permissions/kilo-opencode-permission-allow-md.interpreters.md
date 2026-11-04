---
description: Runs the data notebooks
mode: subagent
permission:
  bash:
    "*": ask
    # ok: kilo-opencode-permission-allow-md
    "python -m pytest *": allow
    # ok: kilo-opencode-permission-allow-md
    "python scripts/report.py": allow
    # ruleid: kilo-opencode-permission-allow-md
    "python3 *": allow
---

Re-run the notebooks in notebooks/ and summarize what changed.
