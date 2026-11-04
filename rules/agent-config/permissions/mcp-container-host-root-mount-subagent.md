---
name: disk-auditor
description: Reports large folders on the build host
tools: Read, Grep
mcpServers:
  - tree:
      type: stdio
      command: docker
      # ruleid: mcp-container-host-root-mount-subagent
      args: ["run", "-i", "--rm", "-v", "/:/host:ro", "example-org/tree-mcp:1.4.0"]
  - notes:
      type: stdio
      command: podman
      args:
        - run
        - -i
        - --mount
        # ruleid: mcp-container-host-root-mount-subagent
        - type=bind,source=/home/fixture-user,target=/home/user,readonly
        - example-org/notes-mcp:3.1.0
  - shell:
      command: bash
      args:
        - -c
        # ruleid: mcp-container-host-root-mount-subagent
        - exec docker run -i --rm -v "$HOME:/home/user" example-org/notes-mcp:3.1.0
  - repo:
      command: docker
      # ok: mcp-container-host-root-mount-subagent
      args: ["run", "-i", "--rm", "-v", "/home/fixture-user/src/fixture-app:/repo:ro", "example-org/notes-mcp:3.1.0"]
  - files:
      command: docker
      # ok: mcp-container-host-root-mount-subagent
      args: ["run", "-i", "--rm", "-v", "/:/projects/host:ro", "mcp/filesystem:1.0.2", "/projects"]
---

Report the ten largest folders under /host. Mount `/:/host` only on throwaway build hosts.
