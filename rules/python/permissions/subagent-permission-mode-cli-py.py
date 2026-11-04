"""Fixture for subagent-permission-mode-cli-py."""
import asyncio
import json
import os
import shutil
import subprocess

CLAUDE_BIN = shutil.which("claude") or "claude"

FIXER_AGENTS = {
    "fixer": {
        "description": "Fixes lint errors",
        "prompt": "Fix the lint errors you are given.",
        "permissionMode": "acceptEdits",
    }
}

FIXER_JSON = '{"fixer": {"description": "d", "prompt": "p", "permissionMode": "acceptEdits"}}'

READER_AGENTS = {
    "reader": {
        "description": "Reads logs",
        "prompt": "Summarize the log.",
        "tools": ["Read", "Grep"],
    }
}


def fix(task: str) -> None:
    subprocess.run(
        # ruleid: subagent-permission-mode-cli-py
        ["claude", "-p", task, "--agents", '{"fixer":{"description":"d","prompt":"p","permissionMode":"auto"}}'],
        check=True,
    )
    subprocess.run(
        [
            CLAUDE_BIN,
            "-p",
            task,
            "--agents",
            # ruleid: subagent-permission-mode-cli-py
            json.dumps({"fixer": {"description": "d", "prompt": "p", "permissionMode": "acceptEdits"}}),
        ],
        check=True,
    )


def fix_with_json_constant(task: str) -> None:
    # ruleid: subagent-permission-mode-cli-py
    subprocess.run([CLAUDE_BIN, "-p", task, "--agents", FIXER_JSON], check=True)


def fix_with_constant(task: str) -> None:
    # ruleid: subagent-permission-mode-cli-py
    agents = {"fixer": {"description": "d", "prompt": "p", "permissionMode": "auto"}}
    subprocess.run(["claude", "-p", task, "--agents", json.dumps(agents)], check=True)


async def fix_async(task: str) -> None:
    proc = await asyncio.create_subprocess_exec(
        # ruleid: subagent-permission-mode-cli-py
        "claude", "-p", task, "--agents", json.dumps(dict(fixer=dict(description="d", prompt="p", permissionMode="acceptEdits")))
    )
    await proc.wait()


def fix_joined(task: str) -> None:
    # ruleid: subagent-permission-mode-cli-py
    subprocess.run(["claude", "-p", task, "--agents=" + json.dumps({"f": {"description": "d", "prompt": "p", "permissionMode": "auto"}})])


def fix_shell(task: str) -> None:
    # ruleid: subagent-permission-mode-cli-py
    os.system("claude -p 'fix lint' --agents '{\"fixer\":{\"description\":\"d\",\"prompt\":\"p\",\"permissionMode\":\"auto\"}}'")


def safe(task: str) -> None:
    # ok: subagent-permission-mode-cli-py
    subprocess.run(["claude", "-p", task, "--agents", json.dumps(READER_AGENTS)], check=True)
    # ok: subagent-permission-mode-cli-py
    subprocess.run(["claude", "-p", task, "--agents", '{"r":{"description":"d","prompt":"p","permissionMode":"plan"}}'])
    # ok: subagent-permission-mode-cli-py
    subprocess.run(["claude", "-p", task, "--agents", "ci/agents.json"])
    # Settings JSON is not an agent definition.
    # ok: subagent-permission-mode-cli-py
    subprocess.run(["claude", "-p", task, "--settings", '{"permissions":{"defaultMode":"acceptEdits"}}'])
    # ok: subagent-permission-mode-cli-py
    subprocess.run(["claude", "-p", task, "--agents", json.dumps(READER_AGENTS), "--settings", '{"permissionMode":"auto"}'])
    # ok: subagent-permission-mode-cli-py
    os.system("claude -p 'x' --agents '{\"r\":{\"description\":\"d\",\"prompt\":\"p\"}}' --settings '{\"permissionMode\":\"auto\"}'")
    # The program after a wrapper: a string anywhere in the argv, a name anywhere.
    # ruleid: subagent-permission-mode-cli-py
    subprocess.run(["timeout", "900", "claude", "-p", task, "--agents", '{"fixer":{"description":"d","prompt":"p","permissionMode":"acceptEdits"}}'])
    # ruleid: subagent-permission-mode-cli-py
    subprocess.run(["sudo", CLAUDE_BIN, "-p", task, "--agents", '{"fixer":{"description":"d","prompt":"p","permissionMode":"auto"}}'])
    # ruleid: subagent-permission-mode-cli-py
    subprocess.run(["timeout", "900", CLAUDE_BIN, "-p", task, "--agents", '{"fixer":{"description":"d","prompt":"p","permissionMode":"acceptEdits"}}'])
    # ok: subagent-permission-mode-cli-py
    subprocess.run(["timeout", "900", CLAUDE_BIN, "-p", task, "--agents", json.dumps(READER_AGENTS)])
    # Another program.
    # ok: subagent-permission-mode-cli-py
    subprocess.run(["my-runner", "--agents", '{"r":{"permissionMode":"auto"}}'])
    # A hook's reply printed for Claude Code, not a launch.
    # ok: subagent-permission-mode-cli-py
    print(json.dumps({"permissionMode": "acceptEdits"}))


def fix_as_ci_user(task: str) -> None:
    # A name-held program after a wrapper, with the definition built in a dict first.
    # ruleid: subagent-permission-mode-cli-py
    agents = {"fixer": {"description": "d", "prompt": "p", "permissionMode": "acceptEdits"}}
    subprocess.run(["sudo", "-u", "ci", CLAUDE_BIN, "-p", task, "--agents", json.dumps(agents)], check=True)
    # ok: subagent-permission-mode-cli-py
    readers = {"reader": {"description": "d", "prompt": "p", "tools": ["Read"]}}
    subprocess.run(["sudo", "-u", "ci", CLAUDE_BIN, "-p", task, "--agents", json.dumps(readers)], check=True)
