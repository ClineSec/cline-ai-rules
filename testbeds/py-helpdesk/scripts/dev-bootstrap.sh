#!/bin/sh
# Prints the local toolchain so a new session starts with the versions in its context.
set -eu
echo "helpdesk dev session"
python3 --version
uv --version 2>/dev/null || echo "uv not installed; see README"
