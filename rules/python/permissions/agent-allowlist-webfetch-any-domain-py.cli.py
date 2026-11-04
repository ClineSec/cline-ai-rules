import subprocess

# The list goes to the Claude Code CLI, which agent-allowlist-webfetch-any-domain-cli-py
# reports; this rule stays quiet on the constant.
RESEARCH_TOOLS = [
    "Read",
    # ok: agent-allowlist-webfetch-any-domain-py
    "WebFetch",
]


def research(prompt: str) -> str:
    return subprocess.run(
        ["claude", "-p", prompt, "--allowedTools", ",".join(RESEARCH_TOOLS)],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
