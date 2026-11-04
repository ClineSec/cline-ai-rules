import asyncio
import os
import shlex
import subprocess

import pexpect

CLINE_BIN = "/usr/local/bin/cline"
AGENT = "cline"


def cline_cases(prompt: str) -> None:
    # ruleid: ai-cli-default-auto-approve-py
    subprocess.run(["cline", "--json", prompt], check=True)
    # ruleid: ai-cli-default-auto-approve-py
    subprocess.Popen([CLINE_BIN, "-m", "claude-sonnet-5-5", prompt])
    # A module constant whose name is the CLI.
    # ruleid: ai-cli-default-auto-approve-py
    subprocess.run([AGENT, prompt], input="", text=True)
    argv = [
        # ruleid: ai-cli-default-auto-approve-py
        "cline",
        "--cwd",
        "service",
        prompt,
    ]
    subprocess.run(argv, timeout=900)
    # ruleid: ai-cli-default-auto-approve-py
    subprocess.run(f"cline {shlex.quote(prompt)}", shell=True)
    # ruleid: ai-cli-default-auto-approve-py
    os.system("npx -y cline --json 'summarize pytest.log' > cline.jsonl")
    # ok: ai-cli-default-auto-approve-py
    subprocess.run(["cline", "--auto-approve", "false", prompt])
    # ok: ai-cli-default-auto-approve-py
    subprocess.run(["cline", "--auto-approve=false", prompt])
    # ok: ai-cli-default-auto-approve-py
    subprocess.run(["cline", "--plan", prompt])
    # ok: ai-cli-default-auto-approve-py
    subprocess.run(["cline", "auth", "--provider", "anthropic"])
    # ok: ai-cli-default-auto-approve-py
    subprocess.run(["cline", "--version"], capture_output=True)
    # Explicit bypass flags are ai-cli-bypass-flag-invocation-py.
    # ok: ai-cli-default-auto-approve-py
    subprocess.run(["cline", "--yolo", prompt])
    # ok: ai-cli-default-auto-approve-py
    subprocess.run(f"cline --auto-approve false {shlex.quote(prompt)}", shell=True)
    # ok: ai-cli-default-auto-approve-py
    print("cline is not installed; run npm install -g cline")
    # ok: ai-cli-default-auto-approve-py
    subprocess.run(["claude-wrapper", prompt])


async def amp_cases(prompt: str) -> None:
    # ruleid: ai-cli-default-auto-approve-py
    await asyncio.create_subprocess_exec("amp", "-x", prompt)
    # ruleid: ai-cli-default-auto-approve-py
    subprocess.run(["amp", "--execute", prompt, "--stream-json"])
    # ruleid: ai-cli-default-auto-approve-py
    subprocess.run(f"amp -x {shlex.quote(prompt)}", shell=True)
    # ok: ai-cli-default-auto-approve-py
    subprocess.run(["amp", "-ox", prompt])
    # ok: ai-cli-default-auto-approve-py
    subprocess.run(["amp", "threads", "list"])
    # ok: ai-cli-default-auto-approve-py
    pexpect.spawn("amp", [])


async def opencode_cases(prompt: str) -> None:
    # ruleid: ai-cli-default-auto-approve-py
    subprocess.run(["opencode", "run", prompt], check=True)
    # ruleid: ai-cli-default-auto-approve-py
    await asyncio.create_subprocess_exec("opencode", "run", "--model", "example/model-1", prompt)
    # ruleid: ai-cli-default-auto-approve-py
    argv = ["opencode", "run", "--format", "json", prompt]
    subprocess.run(argv, capture_output=True)
    # ruleid: ai-cli-default-auto-approve-py
    os.system(f"opencode run {shlex.quote(prompt)}")
    # Explicit bypass flags are ai-cli-bypass-flag-invocation-py.
    # ok: ai-cli-default-auto-approve-py
    subprocess.run(["opencode", "run", "--auto", prompt])
    # ok: ai-cli-default-auto-approve-py
    subprocess.run(["opencode", "models"])
    # ok: ai-cli-default-auto-approve-py
    subprocess.run(["opencode", "serve", "--port", "4096"])
