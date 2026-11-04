import asyncio
import os
import subprocess
import sys

import docker

SHARED_HOST = "0.0.0.0"
SERVER = "contrib/notes_server.py:notes"


def share_on_lan():
    # ruleid: mcp-server-bind-all-interfaces-config-py
    os.environ["FASTMCP_HOST"] = "0.0.0.0"
    # ruleid: mcp-server-bind-all-interfaces-config-py
    os.environ.setdefault("FASTMCP_SERVER_HOST", SHARED_HOST)
    # ruleid: mcp-server-bind-all-interfaces-config-py
    os.putenv("FASTMCP_HOST", "::")
    # ruleid: mcp-server-bind-all-interfaces-config-py
    os.environ.update(FASTMCP_PORT="8000", FASTMCP_HOST="0.0.0.0")


def child_env():
    env = os.environ.copy()
    # ruleid: mcp-server-bind-all-interfaces-config-py
    env["FASTMCP_HOST"] = "0.0.0.0"
    subprocess.Popen([sys.executable, "notes_server.py"], env=env)
    # ruleid: mcp-server-bind-all-interfaces-config-py
    subprocess.Popen([sys.executable, "notes_server.py"], env={**os.environ, "FASTMCP_TRANSPORT": "http", "FASTMCP_HOST": "0.0.0.0"})
    # ruleid: mcp-server-bind-all-interfaces-config-py
    return dict(os.environ, FASTMCP_HOST="0.0.0.0")


def launch():
    # ruleid: mcp-server-bind-all-interfaces-config-py
    subprocess.Popen(["fastmcp", "run", SERVER, "--transport", "http", "--host", "0.0.0.0"])
    # ruleid: mcp-server-bind-all-interfaces-config-py
    subprocess.run(["uv", "run", "fastmcp", "run", SERVER, "--transport=http", "--host=0.0.0.0"], check=True)
    # ruleid: mcp-server-bind-all-interfaces-config-py
    subprocess.run("uvx fastmcp run server.py --transport http --host 0.0.0.0", shell=True)
    # ruleid: mcp-server-bind-all-interfaces-config-py
    os.system("fastmcp run server.py -t sse --host :: &")


async def launch_async():
    # ruleid: mcp-server-bind-all-interfaces-config-py
    return await asyncio.create_subprocess_exec("fastmcp", "run", SERVER, "--transport", "http", "--host", "0.0.0.0")


# ruleid: mcp-server-bind-all-interfaces-config-py
TEAM_CMD = (sys.executable, "-m", "fastmcp.cli", "run", SERVER, "--transport", "http", "--host", "0.0.0.0")


def local_only():
    # ok: mcp-server-bind-all-interfaces-config-py
    os.environ["FASTMCP_HOST"] = "127.0.0.1"
    # ok: mcp-server-bind-all-interfaces-config-py
    os.environ["FASTMCP_HOST"] = os.environ.get("BIND_ADDR", "127.0.0.1")
    # ok: mcp-server-bind-all-interfaces-config-py
    os.environ["UVICORN_HOST"] = "0.0.0.0"
    # ok: mcp-server-bind-all-interfaces-config-py
    host = os.environ.get("FASTMCP_HOST", "0.0.0.0")
    # ok: mcp-server-bind-all-interfaces-config-py
    if os.environ.get("FASTMCP_HOST") == "0.0.0.0":
        print("serving on every interface")
    # ok: mcp-server-bind-all-interfaces-config-py
    subprocess.Popen(["fastmcp", "run", SERVER, "--transport", "http", "--host", "127.0.0.1"])
    # ok: mcp-server-bind-all-interfaces-config-py
    subprocess.Popen(["fastmcp", "run", SERVER, "--transport", "stdio", "--host", "0.0.0.0"])
    # ok: mcp-server-bind-all-interfaces-config-py
    subprocess.Popen(["uvicorn", "app:app", "--host", "0.0.0.0"])
    # ok: mcp-server-bind-all-interfaces-config-py
    subprocess.Popen([sys.executable, "notes_server.py"], env={**os.environ, "FASTMCP_TRANSPORT": "stdio", "FASTMCP_HOST": "0.0.0.0"})
    # Container environment: the bind is inside the container.
    # ok: mcp-server-bind-all-interfaces-config-py
    docker.from_env().containers.run("example-org/notes-mcp", environment={"FASTMCP_HOST": "0.0.0.0"}, ports={"8000/tcp": ("127.0.0.1", 8000)})
    # ok: mcp-server-bind-all-interfaces-config-py
    print("run: fastmcp run server.py --transport http --host 0.0.0.0")
    return host
