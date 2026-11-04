import asyncio
import os
import shlex
import subprocess

import pexpect

CLAUDE_BIN = "claude"
# A tool list joined into argv in research() below.
# ruleid: agent-allowlist-webfetch-any-domain-cli-py
RESEARCH_TOOLS = ["Read", "Grep", "WebFetch"]
SAFE_TOOLS = ("Read", "Grep", "WebFetch(domain:docs.example.com)")
REFUSED_FLAGS = frozenset({"--allow-all-urls", "--yolo"})
# ok: agent-allowlist-webfetch-any-domain-cli-py
BLOCKED_FLAGS = ["--allow-all-urls", "--allow-all"]


def triage(prompt: str) -> str:
    return subprocess.run(
        [
            CLAUDE_BIN,
            "-p",
            prompt,
            "--allowedTools",
            "Read",
            # ruleid: agent-allowlist-webfetch-any-domain-cli-py
            "WebFetch(domain:*)",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def research(prompt: str) -> None:
    subprocess.run(["claude", "-p", prompt, "--allowedTools", ",".join(RESEARCH_TOOLS)], check=True)


def docs_only(prompt: str) -> None:
    # ok: agent-allowlist-webfetch-any-domain-cli-py
    subprocess.run(["claude", "-p", prompt, "--allowedTools", *SAFE_TOOLS], check=True)


def gemini_fetch(prompt: str) -> None:
    # ruleid: agent-allowlist-webfetch-any-domain-cli-py
    subprocess.run(("gemini", "-p", prompt, "--allowed-tools", "web_fetch"), check=True)


def gemini_auto_edit(prompt: str) -> None:
    # ruleid: agent-allowlist-webfetch-any-domain-cli-py
    subprocess.run(["gemini", "--approval-mode", "auto_edit", "-p", prompt], check=True)
    # ruleid: agent-allowlist-webfetch-any-domain-cli-py
    subprocess.run(["gemini", "--approval-mode=auto_edit", "-p", prompt], check=True)
    # ok: agent-allowlist-webfetch-any-domain-cli-py
    subprocess.run(["gemini", "--approval-mode", "plan", "-p", prompt], check=True)


def copilot_fetch(prompt: str) -> None:
    # ruleid: agent-allowlist-webfetch-any-domain-cli-py
    subprocess.run(["copilot", "-p", prompt, "--allow-tool", "shell(git:*), url"], check=True)
    # ruleid: agent-allowlist-webfetch-any-domain-cli-py
    subprocess.run(["copilot", "-p", prompt, "--allow-all-urls"], check=True)
    # ok: agent-allowlist-webfetch-any-domain-cli-py
    subprocess.run(["copilot", "-p", prompt, "--allow-tool", "url(docs.example.com)"], check=True)


def built_up(prompt: str) -> list[str]:
    argv = [CLAUDE_BIN, "-p", prompt]
    argv.append("--allowedTools")
    # ruleid: agent-allowlist-webfetch-any-domain-cli-py
    argv.append("WebFetch")
    return argv


async def run_async(prompt: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        # ruleid: agent-allowlist-webfetch-any-domain-cli-py
        "claude", "-p", prompt, "--allowed-tools", "Read WebFetch"
    )
    await proc.wait()


def shell_string(prompt: str) -> None:
    # ruleid: agent-allowlist-webfetch-any-domain-cli-py
    subprocess.run(f"claude -p {shlex.quote(prompt)} --allowedTools 'Read' 'WebFetch'", shell=True)


def system_string() -> None:
    # ruleid: agent-allowlist-webfetch-any-domain-cli-py
    os.system("npx -y @google/gemini-cli -p 'refresh the docs' --approval-mode auto_edit")


def spawned() -> None:
    # ruleid: agent-allowlist-webfetch-any-domain-cli-py
    pexpect.spawn("claude", ["--allowedTools=WebFetch"])


def denied(prompt: str, args: list[str]) -> None:
    # ok: agent-allowlist-webfetch-any-domain-cli-py
    subprocess.run(["claude", "--allowedTools", "Read", "--disallowedTools", "WebFetch", "-p", prompt], check=True)
    # ok: agent-allowlist-webfetch-any-domain-cli-py
    subprocess.run(["claude", "--allowedTools", "Read", "-p", "Use WebFetch on the link"], check=True)
    # ok: agent-allowlist-webfetch-any-domain-cli-py
    subprocess.run(["claude", "-p", "Explain what WebFetch allows"], check=True)
    # ok: agent-allowlist-webfetch-any-domain-cli-py
    if "--allow-all-urls" in args:
        raise ValueError("refused")
    # ok: agent-allowlist-webfetch-any-domain-cli-py
    subprocess.run("claude -p 'fix it' --allowedTools 'Read' --disallowedTools 'WebFetch'", shell=True)


# ok: agent-allowlist-webfetch-any-domain-cli-py
# subprocess.run(["claude", "--allowedTools", "WebFetch"])
