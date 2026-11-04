import asyncio
import os
import subprocess

import anyio

import anthropic
import litellm
from google import genai
from openai import OpenAI

openai_client = OpenAI()
claude = anthropic.Anthropic()


def run_openai_suggestion(task):
    resp = openai_client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": task}]
    )
    code = resp.choices[0].message.content
    # ruleid: llm-output-to-code-execution
    exec(code)


def run_claude_command(task):
    msg = claude.messages.create(
        model="claude-sonnet-5-5", max_tokens=512, messages=[{"role": "user", "content": task}]
    )
    command = msg.content[0].text.strip()
    # ruleid: llm-output-to-code-execution
    subprocess.run(command, shell=True)


def run_litellm_expression(task):
    out = litellm.completion(model="gpt-5", messages=[{"role": "user", "content": task}])
    expr = out.choices[0].message.content
    # ruleid: llm-output-to-code-execution
    return eval(expr)


def run_responses_api(task):
    resp = openai_client.responses.create(model="gpt-5", input=task)
    # ruleid: llm-output-to-code-execution
    os.system(resp.output_text)


async def run_claude_command_async(task):
    msg = claude.messages.create(
        model="claude-sonnet-5-5", max_tokens=512, messages=[{"role": "user", "content": task}]
    )
    command = msg.content[0].text.strip()
    # ruleid: llm-output-to-code-execution
    proc = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE)
    return await proc.communicate()


def run_litellm_status(task):
    out = litellm.completion(model="gpt-5", messages=[{"role": "user", "content": task}])
    # ruleid: llm-output-to-code-execution
    code, text = subprocess.getstatusoutput(out.choices[0].message.content)
    return code, text


async def word_count_summary(task):
    resp = openai_client.responses.create(model="gpt-5", input=task)
    # The model's text is data in the environment; the shell command itself is fixed.
    # ok: llm-output-to-code-execution
    proc = await asyncio.create_subprocess_shell("wc -w", env={"SUMMARY": resp.output_text})
    return await proc.communicate()


async def run_allowlisted_async(task):
    resp = openai_client.responses.create(model="gpt-5", input=task)
    action = resp.output_text.strip()
    argv = {"status": ["git", "status"], "log": ["git", "log", "-n", "5"]}[action]
    # ok: llm-output-to-code-execution
    proc = await asyncio.create_subprocess_exec(*argv)
    return await proc.communicate()


def dispatch_allowlisted(task):
    resp = openai_client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": task}]
    )
    action = resp.choices[0].message.content.strip()
    allowed = {"status": ["git", "status"], "log": ["git", "log", "-n", "5"]}
    # ok: llm-output-to-code-execution
    subprocess.run(allowed[action], shell=False)


def count_words_in_sandbox(task):
    out = litellm.completion(model="gpt-5", messages=[{"role": "user", "content": task}])
    text = out.choices[0].message.content
    # Fixed code; the model's text is only a value in the namespace.
    # ok: llm-output-to-code-execution
    return eval("len(summary.split())", {"__builtins__": {"len": len}}, {"summary": text})


def static_shell():
    # ok: llm-output-to-code-execution
    subprocess.run("ls -la", shell=True)


def eval_user_config(path):
    with open(path) as f:
        # ok: llm-output-to-code-execution
        return compile(f.read(), path, "exec")


def run_claude_in_login_shell(task):
    msg = claude.messages.create(
        model="claude-sonnet-5-5", max_tokens=512, messages=[{"role": "user", "content": task}]
    )
    # ruleid: llm-output-to-code-execution
    return subprocess.run(["bash", "-lc", msg.content[0].text], capture_output=True).stdout


async def run_openai_with_anyio(task):
    resp = openai_client.responses.create(model="gpt-5", input=task)
    cmd = f"timeout 10 {resp.output_text}"
    # ruleid: llm-output-to-code-execution
    return (await anyio.run_process(cmd)).stdout


async def grep_with_anyio_argv(task):
    resp = openai_client.responses.create(model="gpt-5", input=task)
    # The model's text is one argv item to grep, not a shell command.
    # ok: llm-output-to-code-execution
    return (await anyio.run_process(["grep", "-rn", "--", resp.output_text, "docs/"])).stdout


def greet_in_bash(task):
    resp = openai_client.responses.create(model="gpt-5", input=task)
    # The model's text is $1 of a fixed script.
    # ok: llm-output-to-code-execution
    return subprocess.run(["bash", "-c", 'echo "hello, $1"', "greet", resp.output_text]).stdout


def interpreter_argv(client, task):
    import sys
    code = client.chat.completions.create(model="gpt-4.1-mini", messages=[{"role": "user", "content": task}]).choices[0].message.content
    # ruleid: llm-output-to-code-execution
    subprocess.run([sys.executable, "-c", code], check=True)
    # ruleid: llm-output-to-code-execution
    subprocess.run(["node", "--eval", code])
    # ok: llm-output-to-code-execution
    subprocess.run([sys.executable, "-m", "json.tool", "report.json"], input=code, text=True)
    # ok: llm-output-to-code-execution
    subprocess.run(["node", "--check", "build.mjs"])
    # ruleid: llm-output-to-code-execution
    subprocess.run([sys.executable, "-I", "-c", code])
    # ok: llm-output-to-code-execution
    subprocess.run([sys.executable, "tools/report.py", "-c", code])


def write_then_run(client, task, workdir):
    import runpy
    import sys
    import tempfile
    from pathlib import Path

    code = client.chat.completions.create(model="gpt-4.1-mini", messages=[{"role": "user", "content": task}]).choices[0].message.content
    script = Path(workdir) / "solution.py"
    # ruleid: llm-output-to-code-execution
    script.write_text(code, encoding="utf-8")
    try:
        subprocess.run([sys.executable, str(script)], check=True, timeout=30)
    finally:
        # ok: llm-output-to-code-execution
        print(script, len(code), code)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as handle:
        # ruleid: llm-output-to-code-execution
        handle.write(code)
    runpy.run_path(handle.name)

    with open(workdir + "/step.sh", "w") as out:
        # ruleid: llm-output-to-code-execution
        out.write(code)
    subprocess.run(["bash", workdir + "/step.sh"])

    notes = Path(workdir) / "NOTES.md"
    # ok: llm-output-to-code-execution
    notes.write_text(code)
    subprocess.run(["git", "add", str(notes)], check=True)


async def agent_sdks(repo):
    from agents import Agent, Runner
    from claude_agent_sdk import ClaudeSDKClient, ResultMessage, query

    async for message in query(prompt=f"Reply with one command that runs the tests in {repo}"):
        if isinstance(message, ResultMessage):
            # ruleid: llm-output-to-code-execution
            os.system(message.result)
            # ok: llm-output-to-code-execution
            subprocess.run(["git", "notes", "add", "-m", message.result], check=True)

    async with ClaudeSDKClient() as sdk:
        await sdk.query("Reply with a Python expression for the build number")
        async for message in sdk.receive_response():
            if isinstance(message, ResultMessage):
                # ruleid: llm-output-to-code-execution
                eval(message.result)

    calc = Agent(name="calc", instructions="Answer with a Python expression.")
    result = Runner.run_sync(calc, "Sum of the first ten squares")
    # ruleid: llm-output-to-code-execution
    return eval(result.final_output)


def run_gemini_snippet(task):
    gemini = genai.Client()
    resp = gemini.models.generate_content(model="gemini-3-pro", contents=task)
    # ruleid: llm-output-to-code-execution
    exec(resp.text)


def run_streamed_command(task, chain):
    command = ""
    for chunk in chain.stream({"task": task}):
        command += chunk
    # ruleid: llm-output-to-code-execution
    os.system(command)


def replay_build_log(feed):
    lines = ""
    for line in feed.stream():
        lines += line
    # ok: llm-output-to-code-execution
    os.system(lines)


def run_by_keyword(task, ssh):
    resp = openai_client.responses.create(model="gpt-5", input=task)
    command = resp.output_text.strip()
    # ruleid: llm-output-to-code-execution
    subprocess.run(args=command, shell=True, check=True)
    # ruleid: llm-output-to-code-execution
    subprocess.Popen(shell=True, args=command).wait()
    # ruleid: llm-output-to-code-execution
    _, out, _ = ssh.exec_command(command=command, timeout=30)
    # ruleid: llm-output-to-code-execution
    compile(source=command, filename="<model>", mode="exec")
    # The command is fixed; the model's text is only an environment value.
    # ok: llm-output-to-code-execution
    subprocess.run(args="printenv SUMMARY", shell=True, env={"SUMMARY": command})
    # An argv by keyword with no shell: the model's text is one argument to git.
    # ok: llm-output-to-code-execution
    subprocess.run(args=["git", "notes", "add", "-m", command], check=True)
    # ok: llm-output-to-code-execution
    _, out, _ = ssh.exec_command(command="uptime", environment={"NOTE": command})
    return out.read()


async def run_by_keyword_async(task, loop, factory):
    msg = claude.messages.create(
        model="claude-sonnet-5-5", max_tokens=512, messages=[{"role": "user", "content": task}]
    )
    command = msg.content[0].text.strip()
    # ruleid: llm-output-to-code-execution
    proc = await asyncio.create_subprocess_shell(cmd=command, stdout=asyncio.subprocess.PIPE)
    # ruleid: llm-output-to-code-execution
    await loop.subprocess_shell(factory, cmd=command)
    # ruleid: llm-output-to-code-execution
    await anyio.run_process(command=f"timeout 10 {command}")
    # ok: llm-output-to-code-execution
    await anyio.run_process(command=["grep", "-rn", "--", command, "docs/"])
    # ok: llm-output-to-code-execution
    await asyncio.create_subprocess_shell(cmd="wc -w", env={"SUMMARY": command})
    return await proc.communicate()


def write_then_run_by_keyword(client, task, workdir):
    import sys
    from pathlib import Path

    code = client.chat.completions.create(model="gpt-4.1-mini", messages=[{"role": "user", "content": task}]).choices[0].message.content
    script = Path(workdir) / "fix.py"
    # ruleid: llm-output-to-code-execution
    script.write_text(code)
    subprocess.run(args=[sys.executable, str(script)], check=True, timeout=30)

    changes = Path(workdir) / "CHANGES.md"
    # ok: llm-output-to-code-execution
    changes.write_text(code)
    subprocess.run(args=["git", "add", str(changes)], check=True)
