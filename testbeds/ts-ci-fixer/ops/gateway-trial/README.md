# Gateway trial

Two-week trial of the vendor-neutral LLM gateway for the CI fixer's nightly runs, so spend and
latency show up per team in one dashboard. Run the fixer from this folder to route it through
the gateway; Claude Code and Codex pick up the settings below automatically.

- `.claude/settings.json`: Claude Code through the gateway's Anthropic-compatible route.
- `.codex/config.toml`: Codex through the gateway's OpenAI-compatible route.

Nothing else changes: keys stay in your shell or keychain, the gateway forwards them.
