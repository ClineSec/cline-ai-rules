import os
import subprocess
import sys

from fastmcp import Client


def start_notes_server():
    # Too late for this process's fastmcp, but the child below inherits it.
    # ruleid: mcp-server-bind-all-interfaces-config-py
    os.environ["FASTMCP_HOST"] = "0.0.0.0"
    return subprocess.Popen([sys.executable, "contrib/notes_server.py"])


def connect():
    return Client("http://127.0.0.1:8000/mcp")
