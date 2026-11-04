"""Build logs as resources on the 2.x low-level Server, for the build VM's thin client.

The VM's client only reads resources and prompts, so this skips MCPServer and wires the two
handlers directly.
"""

import subprocess

from mcp.server.lowlevel import Server
from mcp.types import GetPromptResult, PromptMessage, ReadResourceResult, TextContent, TextResourceContents

from devtools.settings import settings

LOG_DIR = settings.repo_root / ".ci" / "logs"


async def read_build_log(ctx, params):
    job = str(params.uri).removeprefix("buildlog://")
    text = subprocess.getoutput(f"tail -n 200 {LOG_DIR}/{job}.log")
    return ReadResourceResult(contents=[TextResourceContents(uri=params.uri, text=text)])


async def get_build_prompt(ctx, params):
    job = (params.arguments or {}).get("job", "")
    head = subprocess.run(["tail", "-n", "40", str(LOG_DIR / f"{job}.log")], capture_output=True, text=True).stdout
    return GetPromptResult(
        messages=[PromptMessage(role="user", content=TextContent(type="text", text=f"Why did this job fail?\n{head}"))]
    )


server = Server("devtools-build-logs", on_read_resource=read_build_log, on_get_prompt=get_build_prompt)
