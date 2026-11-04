import subprocess

# The list goes to the Claude Code CLI, which agent-allowlist-network-exfil-commands-cli-py
# reports; this rule stays quiet on the constant.
STATUS_TOOLS = [
    "Read",
    # ok: agent-allowlist-network-exfil-commands-py
    "Bash(curl:*)",
]


def check(prompt: str) -> str:
    return subprocess.run(
        ["claude", "-p", prompt, "--allowedTools", ",".join(STATUS_TOOLS)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
