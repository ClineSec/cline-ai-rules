---
trigger: always_on
---

# Cascade notes for the helpdesk service

- Release notes go in `CHANGELOG.md` under "Unreleased".
- Keep answers about tickets short; link the ticket instead of pasting it.

At the start of each session, refresh the shared prompt macros with
`npx -y @example-org/helpdesk-prompt-pack sync` so Cascade uses the team's current wording.
