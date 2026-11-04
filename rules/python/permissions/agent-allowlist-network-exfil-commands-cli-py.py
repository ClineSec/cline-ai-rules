import asyncio
import os
import shlex
import subprocess

import pexpect

CLAUDE_BIN = "claude"
# A tool list joined into argv in lookup() below.
# ruleid: agent-allowlist-network-exfil-commands-cli-py
LOOKUP_TOOLS = ["Read", "Grep", "Bash(dig +short *)"]
SAFE_TOOLS = ("Read", "Grep", "Bash(npm test:*)")


def triage(prompt: str) -> str:
    return subprocess.run(
        [
            CLAUDE_BIN,
            "-p",
            prompt,
            "--allowedTools",
            "Read",
            # ruleid: agent-allowlist-network-exfil-commands-cli-py
            "Bash(curl:*)",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def lookup(prompt: str) -> None:
    subprocess.run(["claude", "-p", prompt, "--allowedTools", ",".join(LOOKUP_TOOLS)], check=True)


def tests_only(prompt: str) -> None:
    # ok: agent-allowlist-network-exfil-commands-cli-py
    subprocess.run(["claude", "-p", prompt, "--allowedTools", *SAFE_TOOLS], check=True)


def gemini_status(prompt: str) -> None:
    # ruleid: agent-allowlist-network-exfil-commands-cli-py
    subprocess.run(("gemini", "-p", prompt, "--allowed-tools", "run_shell_command(nslookup)"), check=True)


def copilot_fetch(prompt: str) -> None:
    # ruleid: agent-allowlist-network-exfil-commands-cli-py
    subprocess.run(["copilot", "-p", prompt, "--allow-tool", "shell(git:*), shell(curl:*)"], check=True)


def copilot_flag_value(prompt: str) -> None:
    # ruleid: agent-allowlist-network-exfil-commands-cli-py
    subprocess.run(["copilot", "-p", prompt, "--allow-tool=shell(wget)"], check=True)


def built_up(prompt: str) -> list[str]:
    argv = [CLAUDE_BIN, "-p", prompt]
    argv.append("--allowedTools")
    # ruleid: agent-allowlist-network-exfil-commands-cli-py
    argv.append("Bash(ssh deploy@build.example.com *)")
    return argv


def extended(argv: list[str]) -> None:
    # ruleid: agent-allowlist-network-exfil-commands-cli-py
    argv.extend(["--allowedTools", "Read", "PowerShell(Invoke-WebRequest *)"])


async def run_async(prompt: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        # ruleid: agent-allowlist-network-exfil-commands-cli-py
        "claude", "-p", prompt, "--allowed-tools", "Read Bash(wget -qO- *)"
    )
    await proc.wait()


def shell_string(prompt: str) -> None:
    # ruleid: agent-allowlist-network-exfil-commands-cli-py
    subprocess.run(f"claude -p {shlex.quote(prompt)} --allowedTools 'Read' 'Bash(curl -s https://status.example.com/*)'", shell=True)


def system_string() -> None:
    # ruleid: agent-allowlist-network-exfil-commands-cli-py
    os.system("npx -y @github/copilot -p 'check the hosts' --allow-tool 'shell(ping:*)'")


def spawned() -> None:
    # ruleid: agent-allowlist-network-exfil-commands-cli-py
    pexpect.spawn("claude", ["--allowedTools=Bash(nc:*)"])


def denied(prompt: str) -> None:
    # ok: agent-allowlist-network-exfil-commands-cli-py
    subprocess.run(["claude", "-p", prompt, "--allowedTools", "Read", "--disallowedTools", "Bash(curl:*)"], check=True)
    # ok: agent-allowlist-network-exfil-commands-cli-py
    subprocess.run(["copilot", "-p", prompt, "--allow-tool", "shell(git:*)", "--deny-tool", "shell(curl)"], check=True)
    # ok: agent-allowlist-network-exfil-commands-cli-py
    subprocess.run("claude -p 'fix it' --allowedTools 'Read' --disallowedTools 'Bash(curl:*)'", shell=True)


def exact_and_other(prompt: str) -> None:
    # ok: agent-allowlist-network-exfil-commands-cli-py
    subprocess.run(["claude", "-p", prompt, "--allowedTools", "Bash(curl https://status.example.com/healthz)"], check=True)
    # ok: agent-allowlist-network-exfil-commands-cli-py
    subprocess.run(["claude", "-p", prompt, "--allowedTools", "Bash(git pull:*)", "Bash(curl:*status.example.com*)"], check=True)
    # ok: agent-allowlist-network-exfil-commands-cli-py
    subprocess.run(["claude", "-p", "Explain what Bash(curl:*) allows"], check=True)
    # ok: agent-allowlist-network-exfil-commands-cli-py
    subprocess.run(["copilot", "-p", prompt, "--allow-tool", "url(docs.example.com)"], check=True)


# ok: agent-allowlist-network-exfil-commands-cli-py
# subprocess.run(["claude", "--allowedTools", "Bash(curl:*)"])
