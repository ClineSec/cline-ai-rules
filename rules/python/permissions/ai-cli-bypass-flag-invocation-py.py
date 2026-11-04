import asyncio
import os
import shlex
import shutil
import subprocess

import pexpect

CLAUDE_BIN = shutil.which("claude") or "claude"
AGENT_BIN = "/opt/tools/claude"
PROMPT = "summarize the failing tests"


def claude_cases(prompt: str) -> None:
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["claude", "-p", prompt, "--dangerously-skip-permissions"], check=True)
    subprocess.run(
        [
            CLAUDE_BIN,
            "-p",
            prompt,
            "--permission-mode",
            # ruleid: ai-cli-bypass-flag-invocation-py
            "bypassPermissions",
        ]
    )
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.Popen(("npx", "-y", "@anthropic-ai/claude-code", "-p", prompt, "--dangerously-skip-permissions"))
    argv = [CLAUDE_BIN, "-p", prompt]
    # ruleid: ai-cli-bypass-flag-invocation-py
    argv.append("--dangerously-skip-permissions")
    subprocess.run(argv)
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(f"claude -p {shlex.quote(prompt)} --dangerously-skip-permissions", shell=True)
    # ruleid: ai-cli-bypass-flag-invocation-py
    unattended = ["--output-format", "json", "--dangerously-skip-permissions"]
    subprocess.run([CLAUDE_BIN, "-p", prompt, *unattended])
    # ruleid: ai-cli-bypass-flag-invocation-py
    review_args = ["chat", "--no-interactive", "--trust-all-tools"]
    pexpect.spawn("kiro-cli", review_args)
    # A module constant whose name doesn't say which CLI it holds.
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run([AGENT_BIN, "-p", prompt, "--dangerously-skip-permissions"])
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["claude-wrapper", "-p", prompt, "--dangerously-skip-permissions"])
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["claude", "-p", prompt, "--permission-mode", "dontAsk", "--allowedTools", "Read"])
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["claude", "--permission-mode", "plan", "--allow-dangerously-skip-permissions"])
    # A guard that refuses the flag is not an invocation.
    # ok: ai-cli-bypass-flag-invocation-py
    if "--dangerously-skip-permissions" in argv:
        raise ValueError("refusing to run claude without permission checks")
    # ok: ai-cli-bypass-flag-invocation-py
    print("never pass --dangerously-skip-permissions to claude here")
    # ok: ai-cli-bypass-flag-invocation-py
    # subprocess.run("claude -p x --dangerously-skip-permissions", shell=True)


async def codex_cases(task: str) -> None:
    # ruleid: ai-cli-bypass-flag-invocation-py
    await asyncio.create_subprocess_exec("codex", "exec", "--yolo", task)
    # ruleid: ai-cli-bypass-flag-invocation-py
    await asyncio.create_subprocess_exec(os.environ.get("CODEX_BIN", "codex"), "exec", "--yolo", task)
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["codex", "exec", "--dangerously-bypass-approvals-and-sandbox", task])
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["codex", "exec", "-s", "danger-full-access", task])
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["codex", "exec", "-c", 'sandbox_mode="danger-full-access"', task])
    # ruleid: ai-cli-bypass-flag-invocation-py
    os.system(f"codex exec --yolo {shlex.quote(task)}")
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["codex", "exec", "--sandbox", "workspace-write", task])
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["codex", "--not-so-yolo", "exec", task])


def gemini_cases(prompt: str) -> None:
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["gemini", "-p", prompt, "-y"])
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["gemini", "--approval-mode", "yolo", "-p", prompt])
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(f"gemini --yolo -p {shlex.quote(prompt)}", shell=True)
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["gemini", "--approval-mode", "auto_edit", "-p", prompt])
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["gemini", "--sandbox", "--yolo", "-p", prompt])
    # -y belongs to npx here, before the program.
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["npx", "-y", "@google/gemini-cli", "-p", prompt])
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["gemini", "-p", "yolo"])


def copilot_kiro_cursor_cases(prompt: str) -> None:
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["copilot", "-p", prompt, "--allow-all-tools"])
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["copilot", "-p", prompt], env={**os.environ, "COPILOT_ALLOW_ALL": "true"})
    # ruleid: ai-cli-bypass-flag-invocation-py
    child = pexpect.spawn("kiro-cli", ["chat", "--no-interactive", "--trust-all-tools", prompt])
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["q", "chat", "--no-interactive", "-a", prompt])
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["agent", "-p", "--force", prompt])
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["cursor-agent", "-p", prompt, "--sandbox", "disabled"])
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["copilot", "-p", prompt, "--allow-all-tools", "--sandbox"])
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["copilot", "-p", prompt, "--allow-tool", "shell(npm test)"])
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["copilot", "-p", prompt], env={**os.environ, "COPILOT_ALLOW_ALL": "false"})
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["kiro-cli", "chat", "--no-interactive", "--trust-tools=read_file", prompt])
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["agent", "deploy", "--force"])
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["git", "push", "--force"])
    return child


def newer_clis(prompt: str) -> None:
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["qwen", "-p", prompt, "--yolo"])
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["opencode", "run", "--auto", prompt])
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["goose", "run", "-t", prompt], env={**os.environ, "GOOSE_MODE": "auto"})
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["qwen", "--approval-mode", "auto-edit", "-p", prompt])
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["goose", "run", "-t", prompt], env={**os.environ, "GOOSE_MODE": "approve"})
    # aider still asks before shell commands with --yes-always.
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["aider", "--yes-always", "--message", prompt])


# Per-agent flag tables spliced into an argv template later; the program is not in view.
UNATTENDED_FLAGS = {
    # ruleid: ai-cli-bypass-flag-invocation-py
    "codex": ("--dangerously-bypass-approvals-and-sandbox",),
    # ruleid: ai-cli-bypass-flag-invocation-py
    "gemini": ["--approval-mode", "yolo"],
    # ok: ai-cli-bypass-flag-invocation-py
    "claude": ("--permission-mode", "dontAsk", "--allowedTools", "Read"),
}
# ruleid: ai-cli-bypass-flag-invocation-py
CI_AGENT_FLAGS: tuple[str, ...] = ("--output-format", "json", "--dangerously-skip-permissions")
# A block list is a guard, not an invocation.
# ok: ai-cli-bypass-flag-invocation-py
BLOCKED_AGENT_FLAGS = ["--dangerously-skip-permissions", "--yolo", "--allow-all-tools"]


def refuse_bypass(extra: list[str]) -> None:
    # ok: ai-cli-bypass-flag-invocation-py
    if any(flag in ["--dangerously-skip-permissions", "--allow-all-tools"] for flag in extra):
        raise ValueError("bypass flags are not allowed")
    # ok: ai-cli-bypass-flag-invocation-py
    if extra[:1] == ["--dangerously-skip-permissions"]:
        raise ValueError("bypass flags are not allowed")
    # A list that starts with another program is left to the program branches.
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["my-agent-wrapper", "--dangerously-skip-permissions"])
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["my-agent-wrapper", "--permission-mode", "bypassPermissions"])
    # ok: ai-cli-bypass-flag-invocation-py
    pexpect.spawn("copilot", ["-p", "summarize", "--allow-all-tools", "--sandbox"])


def cline_cases(prompt: str) -> None:
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["cline", "--yolo", prompt])
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(["cline", "--auto-approve", "true", "--json", prompt])
    # ruleid: ai-cli-bypass-flag-invocation-py
    subprocess.run(f"cline -y {shlex.quote(prompt)}", shell=True)
    # A plain run is Cline's default (ai-cli-default-auto-approve-py), not a bypass flag.
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["cline", "--auto-approve", "false", prompt])
    # ok: ai-cli-bypass-flag-invocation-py
    subprocess.run(["cline", prompt])
