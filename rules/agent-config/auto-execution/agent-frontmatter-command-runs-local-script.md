---
name: release-checks
description: Run the release checklist before tagging
allowed-tools: Read, Grep
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          # ruleid: agent-frontmatter-command-runs-local-script
          command: "./scripts/check-release-command.sh"
        - type: command
          # ok: agent-frontmatter-command-runs-local-script
          command: uv run ruff check --quiet
        - type: command
          # ok: agent-frontmatter-command-runs-local-script
          command: '"${CLAUDE_PLUGIN_ROOT}"/scripts/guard.sh'
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        # ruleid: agent-frontmatter-command-runs-local-script
        - { type: command, command: python3 .claude/hooks/changelog_lint.py, timeout: 30 }
        - type: command
          # ruleid: agent-frontmatter-command-runs-local-script
          command: $CLAUDE_PROJECT_DIR/tools/notify-release  # posts to the release channel
        - type: command
          # ok: agent-frontmatter-command-runs-local-script
          command: /usr/local/bin/release-audit
  Stop:
    - hooks:
        - type: command
          # ruleid: agent-frontmatter-command-runs-local-script
          command: pwsh -NoProfile -File .\scripts\stop-check.ps1
        - type: command
          # ok: agent-frontmatter-command-runs-local-script
          command: ~/.claude/hooks/notify.sh
# Session setup, added after the 2.3 release.
  SessionStart:
    - hooks:
        - type: command
          # ruleid: agent-frontmatter-command-runs-local-script
          command: bash scripts/release-env.sh
---

Run the release checklist in `docs/release.md`.

<!-- ok: agent-frontmatter-command-runs-local-script -->
command: ./scripts/not-a-hook.sh

```yaml
hooks:
  PreToolUse:
    - hooks:
        - type: command
          <!-- ok: agent-frontmatter-command-runs-local-script -->
          command: ./scripts/example-in-docs.sh
```
