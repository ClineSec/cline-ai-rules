"""Release helper agent (community contribution, pydantic-ai).

Walks a maintainer through tagging and pushing a release image: it reads the registry details
from the environment the release job sets, drafts the commands, and the maintainer runs them.
Like the other contrib modules it hasn't been reviewed yet.
"""

import os
import re
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

REGISTRY_DEFAULT = "registry.example.com"
VERSION = re.compile(r"\d+\.\d+\.\d+")


@dataclass
class ReleaseJob:
    image: str
    version: str


release_agent = Agent(
    "openai:gpt-5-mini",
    deps_type=ReleaseJob,
    instructions="Draft the commands to tag and push the release image. Never run them yourself.",
)


@release_agent.tool_plain
def registry_host() -> str:
    """The registry the release image is pushed to."""
    return os.environ.get("RELEASE_REGISTRY", REGISTRY_DEFAULT)


@release_agent.tool_plain
def registry_login() -> str:
    """The login command for the release registry, ready to paste."""
    host = os.environ.get("RELEASE_REGISTRY", REGISTRY_DEFAULT)
    user = os.environ.get("RELEASE_REGISTRY_USER", "release-bot")
    password = os.environ["RELEASE_REGISTRY_PASSWORD"]
    return f"echo '{password}' | docker login {host} -u {user} --password-stdin"


@release_agent.tool
def image_tag(ctx: RunContext[ReleaseJob]) -> str:
    """The full tag for this release."""
    if not VERSION.fullmatch(ctx.deps.version):
        raise ValueError(f"not a release version: {ctx.deps.version}")
    host = os.environ.get("RELEASE_REGISTRY", REGISTRY_DEFAULT)
    return f"{host}/{ctx.deps.image}:{ctx.deps.version}"


@release_agent.tool_plain
def registry_credentials_configured() -> bool:
    """Whether the release job has registry credentials at all."""
    return bool(os.environ.get("RELEASE_REGISTRY_PASSWORD"))
