from dataclasses import replace

from claude_agent_sdk import ClaudeAgentOptions, query

ALLOWED_TOOLS = [
    "Read",
    # ruleid: agent-allowlist-webfetch-any-domain-py
    "WebFetch",
    # ok: agent-allowlist-webfetch-any-domain-py
    "WebFetch(domain:docs.example.com)",
]

DISALLOWED_TOOLS = [
    # ok: agent-allowlist-webfetch-any-domain-py
    "WebFetch",
]


def research_options(cwd: str) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=cwd,
        allowed_tools=[
            "Grep",
            # ruleid: agent-allowlist-webfetch-any-domain-py
            "WebFetch(domain:*)",
            # ok: agent-allowlist-webfetch-any-domain-py
            "WebSearch",
        ],
        disallowed_tools=DISALLOWED_TOOLS,
        permission_mode="default",
    )


def with_fetch(base: ClaudeAgentOptions) -> ClaudeAgentOptions:
    # ruleid: agent-allowlist-webfetch-any-domain-py
    return replace(base, allowed_tools=["Read", "WebFetch(domain:*.io)"])


OPTIONS_DICT = {
    # ruleid: agent-allowlist-webfetch-any-domain-py
    "allowed_tools": ["Read", "WebFetch"],
    "permission_mode": "default",
}


def yolo(cwd: str) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=cwd,
        # ok: agent-allowlist-webfetch-any-domain-py
        allowed_tools=["WebFetch"],
        permission_mode="bypassPermissions",
    )


def docs_only(cwd: str) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(
        cwd=cwd,
        # ok: agent-allowlist-webfetch-any-domain-py
        allowed_tools=["Read", "WebFetch(domain:*.example.com)", "mcp__fetch__fetch"],
        # ok: agent-allowlist-webfetch-any-domain-py
        disallowed_tools=["WebFetch(domain:*)"],
    )


READ_ONLY_TOOLS = ["Read", "Grep", "Glob"]
RESEARCH_TOOLS = [
    *READ_ONLY_TOOLS,
    # ruleid: agent-allowlist-webfetch-any-domain-py
    "WebFetch",
]
BLOCKED_TOOLS = [
    # ok: agent-allowlist-webfetch-any-domain-py
    "WebFetch",
]


def denied(cwd: str) -> ClaudeAgentOptions:
    # A deny rule wins over the allow.
    return ClaudeAgentOptions(
        cwd=cwd,
        # ok: agent-allowlist-webfetch-any-domain-py
        allowed_tools=["Read", "WebFetch"],
        disallowed_tools=["WebFetch"],
    )
