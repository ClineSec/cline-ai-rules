# Release smoke test

The release pipeline runs `claude -p "$(cat smoke.md)"` from this folder after each staging
deploy. Claude walks the staging helpdesk (create a ticket, reply, close it) and writes
`smoke-report.md`. The run is unattended, so `.claude/settings.json` here answers the
permission checks that would otherwise stop it.
