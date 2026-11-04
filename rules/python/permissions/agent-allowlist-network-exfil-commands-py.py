from dataclasses import replace

from claude_agent_sdk import ClaudeAgentOptions, query

ALLOWED_TOOLS = [
    "Read",
    # ruleid: agent-allowlist-network-exfil-commands-py
    "Bash(curl:*)",
    # ok: agent-allowlist-network-exfil-commands-py
    "Bash(curl -sf https://status.example.com/healthz)",
]

DISALLOWED_TOOLS = [
    # ok: agent-allowlist-network-exfil-commands-py
    "Bash(wget *)",
]


def status_options(cwd: str) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=cwd,
        allowed_tools=[
            "Grep",
            # ruleid: agent-allowlist-network-exfil-commands-py
            "Bash(dig +short *)",
            # ok: agent-allowlist-network-exfil-commands-py
            "Bash(git log:*)",
        ],
        disallowed_tools=DISALLOWED_TOOLS,
        permission_mode="default",
    )


def with_ssh(base: ClaudeAgentOptions) -> ClaudeAgentOptions:
    # ruleid: agent-allowlist-network-exfil-commands-py
    return replace(base, allowed_tools=["Read", "Bash(ssh deploy@build.example.com *)"])


OPTIONS_DICT = {
    # ruleid: agent-allowlist-network-exfil-commands-py
    "allowed_tools": ["Read", "Bash(nslookup:*)"],
    "permission_mode": "default",
}


def yolo(cwd: str) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=cwd,
        # ok: agent-allowlist-network-exfil-commands-py
        allowed_tools=["Bash(curl:*)"],
        permission_mode="bypassPermissions",
    )


def readonly(cwd: str) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=cwd,
        # ok: agent-allowlist-network-exfil-commands-py
        allowed_tools=["Read", "Grep", "Bash(hostname)", "WebFetch(domain:docs.example.com)"],
        # ok: agent-allowlist-network-exfil-commands-py
        disallowed_tools=["Bash(curl:*)", "Bash(wget:*)"],
    )


# A shared tool list in its own module, named for the agent rather than "allowed".
READ_ONLY_TOOLS = ["Read", "Grep", "Glob"]
DEPLOY_TRIAGE_TOOLS = [
    *READ_ONLY_TOOLS,
    # ruleid: agent-allowlist-network-exfil-commands-py
    "Bash(curl:*)",
]
UNSAFE_TOOLS = [
    # ok: agent-allowlist-network-exfil-commands-py
    "Bash(curl:*)",
]
SHELL_EXAMPLES = [
    # ok: agent-allowlist-network-exfil-commands-py
    "Bash(curl:*)",
]
