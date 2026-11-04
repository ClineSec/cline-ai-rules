import os
import subprocess

READ_ONLY = '{"*": "ask", "read": "allow", "bash": "deny", "edit": "deny"}'


def summarize(prompt: str) -> None:
    env = dict(os.environ, OPENCODE_PERMISSION=READ_ONLY)
    # ok: ai-cli-default-auto-approve-py
    subprocess.run(["opencode", "run", prompt], env=env, check=True)
