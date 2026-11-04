---
name: changelog-bot
description: Writes the changelog section for a release
tools:
  - read_file
  - run_shell_command
# ruleid: subagent-permission-mode-qwen
approvalMode: yolo
---

Read the merged pull requests since the last tag and write the changelog section.
