# Fixture for ai-cli-bypass-flag-invocation: a Makefile.
CLAUDE ?= npx -y @anthropic-ai/claude-code
PROMPT := summarize the failing tests
# ruleid: ai-cli-bypass-flag-invocation
CODEX_FLAGS := --model gpt-5.5 --dangerously-bypass-approvals-and-sandbox
# ok: ai-cli-bypass-flag-invocation
CLAUDE_FLAGS := --permission-mode dontAsk --allowedTools "Read"

triage:
	# ruleid: ai-cli-bypass-flag-invocation
	@$(CLAUDE) -p "$(PROMPT)" \
		--dangerously-skip-permissions

fix:
	# ruleid: ai-cli-bypass-flag-invocation
	-codex exec --yolo "$(PROMPT)"

help:
	# ok: ai-cli-bypass-flag-invocation
	@echo "make triage runs claude --dangerously-skip-permissions"
	# ok: ai-cli-bypass-flag-invocation
	@$(CLAUDE) -p "$(PROMPT)" --permission-mode dontAsk --allowedTools "Read"
