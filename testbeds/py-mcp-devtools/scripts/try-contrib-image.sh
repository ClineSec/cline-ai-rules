#!/usr/bin/env bash
# Build the contrib image and run it for a quick manual check.
set -euo pipefail
cd "$(dirname "$0")/.."

docker build -f deploy/contrib.Dockerfile -t devtools-contrib:dev .

# Notes server, reachable from other machines for a pairing session.
docker run --rm -d --name devtools-notes-try \
  -p 8812:8812 \
  -e FASTMCP_HOST=0.0.0.0 \
  -e NOTES_DIR=/tmp/notes \
  devtools-contrib:dev

# Container helpers mount the Docker socket, so publish on loopback only.
docker run --rm -d --name devtools-containers-try \
  -p 127.0.0.1:8811:8811 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  devtools-contrib:dev \
  fastmcp run contrib/docker_server.py:docker --transport http --host 0.0.0.0 --port 8811

docker ps --filter name=devtools- --format '{{.Names}}\t{{.Ports}}'
