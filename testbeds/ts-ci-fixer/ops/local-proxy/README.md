# Local proxy

For debugging the fixer's prompts: start the recording proxy with
`docker compose -f ../../scripts/proxy/compose.yaml up` (it listens on localhost:4000 and
forwards to Anthropic), then run Claude Code from this folder.
