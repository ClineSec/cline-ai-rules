import json
import os
import subprocess

from agents import function_tool
from crewai.tools import BaseTool
from langchain_core.tools import StructuredTool, tool
from pydantic_ai import Agent, RunContext

agent = Agent("openai:gpt-5")


@tool
def runtime_environment() -> str:
    """Show the environment the agent runs in."""
    # ruleid: agent-tool-returns-environment
    return json.dumps(dict(os.environ), indent=2)


@function_tool
def shell_environment() -> str:
    out = subprocess.check_output(["env"], text=True)
    # ruleid: agent-tool-returns-environment
    return out


@agent.tool
def deploy_context(ctx: RunContext[str]) -> dict:
    # ruleid: agent-tool-returns-environment
    return {"user": ctx.deps, "env": {**os.environ}}


@agent.tool_plain
def get_setting(name: str) -> str:
    # ruleid: agent-tool-returns-environment
    return os.getenv(name, "")


class EnvTool(BaseTool):
    name: str = "environment"
    description: str = "List environment variables."

    def _run(self) -> str:
        # ruleid: agent-tool-returns-environment
        return "\n".join(f"{k}={v}" for k, v in os.environ.items())


def cloud_credentials() -> dict:
    # ruleid: agent-tool-returns-environment
    return {"aws_key": os.environ["AWS_SECRET_ACCESS_KEY"], "region": os.environ["AWS_REGION"]}


credentials_tool = StructuredTool.from_function(cloud_credentials)


@tool
def ci_context() -> dict:
    """CI variables for the release notes."""
    # ruleid: agent-tool-returns-environment
    return {k: v for k, v in os.environ.items() if k.startswith(("CI_", "GITHUB_"))}


CI_VARIABLE_RULES = {"CI_DEPLOY_KEY": {"redact": True}}


@tool
def ci_context_by_policy() -> dict:
    """CI variables for the release notes, minus the ones the policy redacts."""
    # Only the listed variables are dropped. The condition starts with a parenthesized
    # expression (OpenGrep 1.30.2 dropped every finding in this file on one before the filter
    # sanitizers skipped it).
    # ruleid: agent-tool-returns-environment
    return {k: v for k, v in os.environ.items() if not (CI_VARIABLE_RULES.get(k) or {}).get("redact")}


# Near misses.

@tool
def ci_branch() -> dict:
    # ok: agent-tool-returns-environment
    return {k: v for k, v in os.environ.items() if k in ("CI_COMMIT_BRANCH", "CI_PIPELINE_ID")}


@tool
def locale() -> dict:
    # ok: agent-tool-returns-environment
    return {"lang": os.environ.get("LANG", "C"), "tz": os.environ.get("TZ", "UTC")}


@function_tool
def configured_providers() -> dict:
    # ok: agent-tool-returns-environment
    return {name: name in os.environ for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY")}


@agent.tool_plain
def run_tests() -> str:
    proc = subprocess.run(["pytest", "-q"], env={**os.environ, "CI": "1"}, capture_output=True, text=True)
    # ok: agent-tool-returns-environment
    return proc.stdout[-4000:]


def environment_for_cli() -> dict:
    """A CLI helper, not a tool."""
    # ok: agent-tool-returns-environment
    return dict(os.environ)
